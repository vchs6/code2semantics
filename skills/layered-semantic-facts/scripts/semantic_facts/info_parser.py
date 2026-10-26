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

    add("module", Path(source_path).stem, 1, max(1, len(source_text.splitlines())),
        f"module {Path(source_path).stem}")
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



def parse_rust_request(request: dict[str, Any], asset_root: str | Path | None = None) -> dict[str, Any]:
    """Parse supplied Rust source text into deterministic declaration observations.

    This lightweight parser inventories declarations/imports only. It does not
    claim type checking, macro expansion, borrow checking, or runtime semantics.
    """
    if asset_root is None:
        asset_root = Path(__file__).resolve().parents[2] / "assets"
    request_validator, result_validator = _validators(Path(asset_root))
    error = next(request_validator.iter_errors(request), None)
    if error:
        raise ParserContractError(f"parse request {list(error.absolute_path)}: {error.message}")

    profile = request["invocation_profile"]
    if profile["tool_id"] != "rust.syntax-source":
        return _unsupported(profile, result_validator)
    if len(profile["sources"]) != 1:
        return _gap_result(profile, "unsupported_profile", "rust.syntax-source requires exactly one source", result_validator)

    source = profile["sources"][0]
    source_id = source["source_id"]
    content_state = source["content_state"]
    source_path = profile["command"][-1] if profile["command"] else source["root"]
    text = request["tool_native_output"]["text"]
    file_node_id = "file-" + hashlib.sha256(source_path.encode("utf-8")).hexdigest()[:20]
    digest = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    context = {
        "source_ids": [source_id],
        "conditions": [],
        "environment": profile["environment"],
        "language_semantics": ["Rust declaration inventory; no type checking, macro expansion, or runtime behavior inferred"],
    }
    coverage = profile["coverage"]

    # Remove comments and string contents for delimiter-balance diagnostics only.
    scrubbed = re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"', " ", text, flags=re.S)
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for offset, char in enumerate(scrubbed):
        if char in "([{":
            stack.append((char, offset))
        elif char in ")]}":
            if not stack or stack[-1][0] != pairs[char]:
                line = scrubbed.count("\n", 0, offset) + 1
                return _gap_result(profile, "unparseable", f"Rust delimiter mismatch at line {line}", result_validator)
            stack.pop()
    if stack:
        line = scrubbed.count("\n", 0, stack[-1][1]) + 1
        return _gap_result(profile, "unparseable", f"Rust unclosed delimiter at line {line}", result_validator)

    observations: list[dict[str, Any]] = []

    def add(kind: str, name: str, line_no: int, detail: str) -> None:
        node_id = _slug(f"{source_path}:{kind}:{name}:{line_no}")
        observations.append({
            "observation_id": _slug("obs-" + node_id),
            "subject": {"source_id": source_id, "subject_id": _slug(source["root"]), "node_id": file_node_id},
            "information_need_id": "rust.syntax_inventory",
            "payload": {"kind": "text", "text": detail},
            "evidence": [{
                "evidence_id": _slug(f"ev-{source_id}-{node_id}"),
                "source_id": source_id,
                "content_state": content_state,
                "kind": "source",
                "locator": f"{source_path}:L{line_no}",
                "content_digest": digest,
                "relation": "supports",
            }],
            "context": context,
            "coverage": coverage,
        })

    add("module", Path(source_path).stem, 1, f"module {Path(source_path).stem}")
    patterns = [
        ("function", re.compile(r"^\s*(?:(?:pub(?:\([^)]*\))?|async|unsafe|const|extern(?:\s+\"[^\"]+\")?)\s+)*fn\s+([A-Za-z_][A-Za-z0-9_]*)"), "fn"),
        ("struct", re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)"), "struct"),
        ("enum", re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?enum\s+([A-Za-z_][A-Za-z0-9_]*)"), "enum"),
        ("trait", re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?trait\s+([A-Za-z_][A-Za-z0-9_]*)"), "trait"),
        ("type", re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?type\s+([A-Za-z_][A-Za-z0-9_]*)"), "type"),
        ("module", re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+([A-Za-z_][A-Za-z0-9_]*)"), "mod"),
        ("import", re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?use\s+(.+?);\s*$"), "use"),
        ("impl", re.compile(r"^\s*impl(?:<[^>]+>)?\s+(.+?)\s*\{?\s*$"), "impl"),
        ("constant", re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:const|static)\s+([A-Za-z_][A-Za-z0-9_]*)"), "const/static"),
    ]
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        for kind, pattern, label in patterns:
            match = pattern.match(line)
            if match:
                name = match.group(1).strip()
                add(kind, name, line_no, f"{label} {name}")
                break

    observations.sort(key=lambda item: (item["evidence"][0]["locator"], item["observation_id"]))
    result = {"kind": "parse_result", "observations": observations, "gaps": []}
    error = next(result_validator.iter_errors(result), None)
    if error:
        raise ParserContractError(f"Rust parser produced invalid result {list(error.absolute_path)}: {error.message}")
    return result



def _native_observation(
    *,
    profile: dict[str, Any],
    need_id: str,
    locator: str,
    text: str,
    kind: str,
    digest: str,
    ordinal: str,
) -> dict[str, Any]:
    source = profile["sources"][0]
    source_id = source["source_id"]
    source_path = _slug(locator)
    return {
        "observation_id": _slug(f"obs-{source_id}-{need_id}-{ordinal}"),
        "subject": {
            "source_id": source_id,
            "subject_id": _slug(source["root"]),
            "node_id": _slug(f"{source_path}:{need_id}:{ordinal}"),
        },
        "information_need_id": need_id,
        "payload": {"kind": "text", "text": text},
        "evidence": [{
            "evidence_id": _slug(f"ev-{source_id}-{need_id}-{ordinal}"),
            "source_id": source_id,
            "content_state": source["content_state"],
            "kind": kind,
            "locator": locator,
            "content_digest": digest,
            "relation": "supports",
        }],
        "context": {
            "source_ids": [source_id],
            "conditions": [],
            "environment": profile["environment"],
            "language_semantics": [("Python compileall diagnostic only; no runtime behavior inferred" if profile["tool_id"] == "python.compileall" else "Cargo manifest metadata only; membership is not dependency and no runtime semantics inferred" if profile["tool_id"] == "rust.cargo-metadata" else "Native tool output only; no unsupported semantics inferred")],
        },
        "coverage": profile["coverage"],
    }


def _native_gap(
    profile: dict[str, Any],
    validator: Draft202012Validator,
    *,
    fact_type: str,
    fields: list[str],
    reason: str,
    detail: str,
) -> dict[str, Any]:
    result = {
        "kind": "parse_result",
        "observations": [],
        "gaps": [{
            "fact_type": fact_type,
            "fields": fields,
            "target": {"kind": "scope"},
            "reason": reason,
            "detail": detail,
            "context": {
                "source_ids": [source["source_id"] for source in profile["sources"]],
                "conditions": [],
                "environment": profile["environment"],
                "language_semantics": ["Native output could not support a stronger claim"],
            },
            "coverage": profile["coverage"],
        }],
    }
    error = next(validator.iter_errors(result), None)
    if error:
        raise ParserContractError(f"native parser produced invalid gap {list(error.absolute_path)}: {error.message}")
    return result


def parse_cargo_metadata_request(
    request: dict[str, Any], asset_root: str | Path | None = None
) -> dict[str, Any]:
    """Convert supplied Cargo metadata JSON into evidence-backed manifest observations."""
    if asset_root is None:
        asset_root = Path(__file__).resolve().parents[2] / "assets"
    request_validator, result_validator = _validators(Path(asset_root))
    error = next(request_validator.iter_errors(request), None)
    if error:
        raise ParserContractError(f"parse request {list(error.absolute_path)}: {error.message}")
    profile = request["invocation_profile"]
    if profile["tool_id"] != "rust.cargo-metadata":
        return _unsupported(profile, result_validator)
    if len(profile["sources"]) != 1:
        return _native_gap(profile, result_validator, fact_type="F4", fields=["enumeration"],
                           reason="unsupported_profile", detail="cargo metadata requires exactly one source")
    raw = request["tool_native_output"]["text"]
    digest = "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        return _native_gap(profile, result_validator, fact_type="F4", fields=["enumeration"],
                           reason="unparseable", detail=f"Cargo metadata JSON parse error at line {error.lineno}: {error.msg}")
    if not isinstance(document, dict) or document.get("version") != 1:
        return _native_gap(profile, result_validator, fact_type="F4", fields=["enumeration"],
                           reason="unsupported_profile", detail="Unsupported Cargo metadata JSON version; expected version 1")
    packages = document.get("packages")
    members = document.get("workspace_members")
    if not isinstance(packages, list) or not isinstance(members, list):
        return _native_gap(profile, result_validator, fact_type="F4", fields=["enumeration"],
                           reason="unparseable", detail="Cargo metadata requires packages and workspace_members arrays")
    observations: list[dict[str, Any]] = []
    package_ids = {p.get("id") for p in packages if isinstance(p, dict) and isinstance(p.get("id"), str)}
    for index, member in enumerate(members):
        if not isinstance(member, str):
            return _native_gap(profile, result_validator, fact_type="F4", fields=["enumeration"],
                               reason="unparseable", detail=f"workspace_members[{index}] must be a string")
        if member not in package_ids:
            return _native_gap(profile, result_validator, fact_type="F4", fields=["enumeration"],
                               reason="unparseable", detail=f"workspace member {member!r} has no package record")
        package = next(p for p in packages if isinstance(p, dict) and p.get("id") == member)
        name = package.get("name", member)
        observations.append(_native_observation(
            profile=profile, need_id="source.f4.kind",
            locator=f"cargo-metadata:/workspace_members/{index}",
            text=f"workspace member: {name} ({member})",
            kind="manifest", digest=digest, ordinal=f"member-{index}",
        ))
    for package_index, package in enumerate(packages):
        if not isinstance(package, dict) or not isinstance(package.get("name"), str) or not isinstance(package.get("id"), str):
            return _native_gap(profile, result_validator, fact_type="F3", fields=["entries"],
                               reason="unparseable", detail=f"packages[{package_index}] is missing required name/id")
        manifest_path = package.get("manifest_path")
        if isinstance(manifest_path, str):
            observations.append(_native_observation(
                profile=profile, need_id="source.f3.entries",
                locator=f"cargo-metadata:/packages/{package_index}/manifest_path",
                text=f"Cargo package manifest: {manifest_path}; package: {package['name']}",
                kind="manifest", digest=digest, ordinal=f"manifest-{package_index}",
            ))
        targets = package.get("targets", [])
        dependencies = package.get("dependencies", [])
        if not isinstance(targets, list) or not isinstance(dependencies, list):
            return _native_gap(profile, result_validator, fact_type="F6", fields=["enumeration"],
                               reason="unparseable", detail=f"packages[{package_index}] targets/dependencies must be arrays")
        for target_index, target in enumerate(targets):
            if not isinstance(target, dict) or not isinstance(target.get("name"), str):
                return _native_gap(profile, result_validator, fact_type="F3", fields=["entries"],
                                   reason="unparseable", detail=f"packages[{package_index}].targets[{target_index}] is malformed")
            observations.append(_native_observation(
                profile=profile, need_id="source.f3.entries",
                locator=f"cargo-metadata:/packages/{package_index}/targets/{target_index}",
                text=f"Cargo target: {package['name']}::{target['name']} kind={target.get('kind', [])} src={target.get('src_path', 'unknown')}",
                kind="manifest", digest=digest, ordinal=f"target-{package_index}-{target_index}",
            ))
        for dependency_index, dependency in enumerate(dependencies):
            if not isinstance(dependency, dict) or not isinstance(dependency.get("name"), str):
                return _native_gap(profile, result_validator, fact_type="F6", fields=["enumeration"],
                                   reason="unparseable", detail=f"packages[{package_index}].dependencies[{dependency_index}] is malformed")
            observations.append(_native_observation(
                profile=profile, need_id="source.f6.kind",
                locator=f"cargo-metadata:/packages/{package_index}/dependencies/{dependency_index}",
                text=f"declared package dependency: {package['name']} -> {dependency['name']} kind={dependency.get('kind') or 'normal'} optional={dependency.get('optional', False)}",
                kind="manifest", digest=digest, ordinal=f"dependency-{package_index}-{dependency_index}",
            ))
    observations.sort(key=lambda item: (item["evidence"][0]["locator"], item["observation_id"]))
    result = {"kind": "parse_result", "observations": observations, "gaps": []}
    error = next(result_validator.iter_errors(result), None)
    if error:
        raise ParserContractError(f"Cargo metadata parser produced invalid result {list(error.absolute_path)}: {error.message}")
    return result


def parse_compileall_request(
    request: dict[str, Any], asset_root: str | Path | None = None
) -> dict[str, Any]:
    """Convert supplied compileall diagnostics; success is only a syntax signal."""
    if asset_root is None:
        asset_root = Path(__file__).resolve().parents[2] / "assets"
    request_validator, result_validator = _validators(Path(asset_root))
    error = next(request_validator.iter_errors(request), None)
    if error:
        raise ParserContractError(f"parse request {list(error.absolute_path)}: {error.message}")
    profile = request["invocation_profile"]
    if profile["tool_id"] != "python.compileall":
        return _unsupported(profile, result_validator)
    if len(profile["sources"]) != 1:
        return _native_gap(profile, result_validator, fact_type="F9", fields=["language_semantics"],
                           reason="unsupported_profile", detail="compileall requires exactly one source")
    raw = request["tool_native_output"]["text"]
    digest = "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
    if not raw.strip():
        observations = [_native_observation(
            profile=profile, need_id="source.f9.language-semantics",
            locator="compileall:stdout",
            text="compileall completed without diagnostics for the invoked scope; syntax/bytecode signal only, no runtime behavior inferred",
            kind="observation", digest=digest, ordinal="no-diagnostics",
        )]
    else:
        if "Error compiling" not in raw and "SyntaxError" not in raw and "Traceback" not in raw:
            return _native_gap(profile, result_validator, fact_type="F9", fields=["language_semantics"],
                               reason="unparseable", detail="Unrecognized compileall diagnostic format")
        observations = [_native_observation(
            profile=profile, need_id="source.f9.language-semantics",
            locator="compileall:stdout",
            text="compileall diagnostic (not a runtime claim): " + raw.strip(),
            kind="observation", digest=digest, ordinal="diagnostic",
        )]
    result = {"kind": "parse_result", "observations": observations, "gaps": []}
    error = next(result_validator.iter_errors(result), None)
    if error:
        raise ParserContractError(f"compileall parser produced invalid result {list(error.absolute_path)}: {error.message}")
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


class ParserRegistry:
    """Explicit registry for deterministic native-output parsers."""

    def __init__(self, asset_root: str | Path | None = None):
        self.asset_root = Path(asset_root) if asset_root else Path(__file__).resolve().parents[2] / "assets"
        self._request_validator, self._result_validator = _validators(self.asset_root)
        self._parsers: dict[str, Any] = {}
        self.register("python.ast-source", lambda request: parse_python_request(request, self.asset_root))
        self.register("rust.syntax-source", lambda request: parse_rust_request(request, self.asset_root))
        self.register("rust.cargo-metadata", lambda request: parse_cargo_metadata_request(request, self.asset_root))
        self.register("python.compileall", lambda request: parse_compileall_request(request, self.asset_root))

    def register(self, tool_id: str, parser: Any) -> None:
        if not isinstance(tool_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", tool_id):
            raise ValueError("tool_id must match the public identifier pattern")
        if not callable(parser):
            raise TypeError("parser must be callable")
        if tool_id in self._parsers:
            raise ValueError(f"parser already registered: {tool_id}")
        self._parsers[tool_id] = parser

    def supported_tools(self) -> tuple[str, ...]:
        return tuple(sorted(self._parsers))

    def parse(self, request: dict[str, Any]) -> dict[str, Any]:
        error = next(self._request_validator.iter_errors(request), None)
        if error:
            raise ParserContractError(f"parse request {list(error.absolute_path)}: {error.message}")
        tool_id = request["invocation_profile"]["tool_id"]
        parser = self._parsers.get(tool_id)
        if parser is None:
            result = _unsupported(request["invocation_profile"], self._result_validator)
        else:
            result = parser(request)
        return self.validate_result(result)

    def validate_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Validate a ParseResult returned by any registered producer adapter."""
        error = next(self._result_validator.iter_errors(result), None)
        if error:
            raise ParserContractError(f"parser result {list(error.absolute_path)}: {error.message}")
        return result
