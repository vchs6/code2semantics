"""Deterministic Python source parser for the public ParseRequest contract.

The parser consumes source text already supplied as tool-native output. It never
opens project files, executes tools, writes the capability matrix, or persists
facts. It emits observations with source evidence and explicit syntax gaps.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


class ParserContractError(ValueError):
    """Input does not conform to the public parse request contract."""


def _slug(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9._:-]+", "-", value).strip("-")
    return result or "unnamed"


def _validators(asset_root: Path) -> tuple[Draft202012Validator, Draft202012Validator]:
    schemas = [json.loads(path.read_text(encoding="utf-8")) for path in asset_root.glob("*.schema.json")]
    registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas)
    pipeline_id = next(schema["$id"] for schema in schemas if schema["$id"].endswith("/pipeline.schema.json"))
    request = Draft202012Validator({"$ref": pipeline_id + "#/$defs/parse_request"}, registry=registry)
    result = Draft202012Validator({"$ref": pipeline_id + "#/$defs/parse_result"}, registry=registry)
    return request, result


def parse_python_request(request: dict[str, Any], asset_root: str | Path | None = None) -> dict[str, Any]:
    """Parse supplied Python source text into contract-shaped observations."""
    if asset_root is None:
        asset_root = Path(__file__).resolve().parents[2] / "assets"
    request_validator, result_validator = _validators(Path(asset_root))
    error = next(request_validator.iter_errors(request), None)
    if error:
        raise ParserContractError(f"parse request {list(error.absolute_path)}: {error.message}")

    profile = request["invocation_profile"]
    if profile["tool_id"] != "python.ast-source":
        return _unsupported(profile, result_validator)

    sources = profile["sources"]
    if len(sources) != 1:
        return _gap_result(profile, "unsupported_profile", "python.ast-source requires exactly one source", result_validator)
    source = sources[0]
    source_id = source["source_id"]
    content_state = source["content_state"]
    root = source["root"]
    command = profile["command"]
    source_path = command[-1] if command else root
    source_text = request["tool_native_output"]["text"]
    digest = "sha256:" + hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    context = {
        "source_ids": [source_id],
        "conditions": [],
        "environment": profile["environment"],
        "language_semantics": ["Python AST syntax; no runtime behavior inferred"],
    }
    coverage = profile["coverage"]

    try:
        tree = ast.parse(source_text, filename=source_path)
    except SyntaxError as error:
        return _gap_result(
            profile,
            "unparseable",
            f"Python syntax error at line {error.lineno or 0}: {error.msg}",
            result_validator,
        )

    observations: list[dict[str, Any]] = []

    def add(kind: str, name: str, lineno: int, end_lineno: int | None, detail: str) -> None:
        node_id = _slug(f"{source_path}:{kind}:{name}:{lineno}")
        evidence_id = _slug(f"ev-{source_id}-{node_id}")
        end = end_lineno or lineno
        observations.append({
            "observation_id": _slug("obs-" + node_id),
            "subject": {"source_id": source_id, "subject_id": _slug(root), "node_id": node_id},
            "information_need_id": "python.syntax_inventory",
            "payload": {"kind": "text", "text": detail},
            "evidence": [{
                "evidence_id": evidence_id,
                "source_id": source_id,
                "content_state": content_state,
                "kind": "source",
                "locator": f"{source_path}:L{lineno}-L{end}",
                "content_digest": digest,
                "relation": "supports",
            }],
            "context": context,
            "coverage": coverage,
        })

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            add("function", node.name, node.lineno, getattr(node, "end_lineno", None),
                f"{'async function' if isinstance(node, ast.AsyncFunctionDef) else 'function'} {node.name}")
        elif isinstance(node, ast.ClassDef):
            add("class", node.name, node.lineno, getattr(node, "end_lineno", None), f"class {node.name}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                add("import", alias.name, node.lineno, node.lineno, f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                add("import", f"{module}.{alias.name}".strip("."), node.lineno, node.lineno,
                    f"from {module} import {alias.name}")

    observations.sort(key=lambda item: (
        item["evidence"][0]["locator"], item["observation_id"]
    ))
    result = {"kind": "parse_result", "observations": observations, "gaps": []}
    error = next(result_validator.iter_errors(result), None)
    if error:
        raise ParserContractError(f"parser produced invalid result {list(error.absolute_path)}: {error.message}")
    return result


def _unsupported(profile: dict[str, Any], validator: Draft202012Validator) -> dict[str, Any]:
    return _gap_result(profile, "unsupported_profile", f"unsupported tool profile: {profile['tool_id']}", validator)


def _gap_result(
    profile: dict[str, Any],
    reason: str,
    detail: str,
    validator: Draft202012Validator,
) -> dict[str, Any]:
    source = profile["sources"][0]
    result = {
        "kind": "parse_result",
        "observations": [],
        "gaps": [{
            "fact_type": "F2",
            "fields": ["syntax_inventory"],
            "target": {"kind": "scope"},
            "reason": reason,
            "detail": detail,
            "context": {
                "source_ids": [item["source_id"] for item in profile["sources"]],
                "conditions": [],
                "environment": profile["environment"],
                "language_semantics": ["Python AST syntax; no runtime behavior inferred"],
            },
            "coverage": profile["coverage"],
        }],
    }
    error = next(validator.iter_errors(result), None)
    if error:
        raise ParserContractError(f"parser produced invalid gap {list(error.absolute_path)}: {error.message}")
    return result
