"""Deterministic Python source inventory that uses the registered parser component."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .info_parser import parse_python_request
from .repository.contract import ContractCodec


EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._:-]+", "-", value).strip("-") or "unnamed"


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def build_fact_batch(root: str | Path, codec: ContractCodec) -> dict[str, Any]:
    """Scan Python files, parse them through info_parser, and build a validated F2 batch."""
    project_root = Path(root).resolve()
    if not project_root.is_dir():
        raise ValueError(f"source root is not a directory: {project_root}")

    files = sorted(
        path for path in project_root.rglob("*.py")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(project_root).parts)
        and path.is_file()
    )
    if not files:
        raise ValueError(f"no Python source files found under {project_root}")

    raw: list[tuple[Path, str, bytes]] = []
    for path in files:
        content = path.read_bytes()
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"Python source is not UTF-8: {path.relative_to(project_root)}") from error
        raw.append((path, path.relative_to(project_root).as_posix(), content))

    snapshot_digest = hashlib.sha256()
    for _, relative, content in raw:
        snapshot_digest.update(relative.encode("utf-8"))
        snapshot_digest.update(b"\\0")
        snapshot_digest.update(hashlib.sha256(content).digest())
    content_state = "sha256:" + snapshot_digest.hexdigest()
    source_id = "src-" + hashlib.sha256(str(project_root).encode("utf-8")).hexdigest()[:20]
    subject_id = "project-" + hashlib.sha256(str(project_root).encode("utf-8")).hexdigest()[:20]

    source_record = {
        "source_id": source_id,
        "root": str(project_root),
        "content_state": content_state,
        "status": "available",
        "dirty": False,
        "has_untracked": False,
        "excludes": sorted(EXCLUDED_DIRS),
    }
    facts: list[dict[str, Any]] = []
    for _, relative, content in raw:
        coverage = {
            "domain": f"Python syntax in {relative}",
            "checked": [relative],
            "excluded": [],
            "completeness": "complete",
            "method": "Python ast.parse via info_parser",
        }
        request = {
            "kind": "parse_request",
            "tool_native_output": {"encoding": "utf-8", "text": content.decode("utf-8")},
            "invocation_profile": {
                "tool_id": "python.ast-source",
                "tool_version": "3.12+",
                "command": ["python", "-m", "ast", relative],
                "environment": {"language": "Python"},
                "sources": [source_record],
                "coverage": coverage,
                "evidence": [],
            },
        }
        parsed = parse_python_request(request, codec.schema_root)
        if parsed["gaps"]:
            raise ValueError(f"cannot parse {relative}: {parsed['gaps'][0]['detail']}")
        observations = parsed["observations"]
        names = [item["payload"]["text"] for item in observations]
        evidence_by_id = {
            item["evidence"]["evidence_id"]: item["evidence"]
            for observation in observations
            for item in observation["evidence"]
        }
        evidence_items = [evidence_by_id[key] for key in sorted(evidence_by_id)]
        if not evidence_items:
            raise ValueError(f"parser produced no file-level evidence for {relative}")

        node_id = "file-" + hashlib.sha256(relative.encode("utf-8")).hexdigest()[:20]
        fact_id = "fact-" + hashlib.sha256((relative + "\\0F2").encode("utf-8")).hexdigest()[:20]
        context = {
            "source_ids": [source_id],
            "conditions": [],
            "environment": {"language": "Python"},
            "language_semantics": ["Python syntax inventory; runtime behavior not inferred"],
        }

        def assertion(value: dict[str, Any]) -> dict[str, Any]:
            return {
                "origin": "observed",
                "knowledge": "supported",
                "context": context,
                "coverage": coverage,
                "basis": {
                    "evidence": evidence_items,
                    "premises": [],
                    "method": "deterministic Python AST parser",
                    "limitations": ["Does not infer runtime behavior or intent"],
                },
                "value": value,
                "validity": {"state": "current", "sources": [{"source_id": source_id, "content_state": content_state}]},
            }

        identity = assertion({"kind": "reference", "ref": {
            "source_id": source_id, "subject_id": subject_id, "node_id": node_id,
        }})
        facts.append({
            "fact_id": fact_id,
            "node": {"source_id": source_id, "subject_id": subject_id, "node_id": node_id},
            "fact_type": "F2",
            "granularities": ["L3"],
            "fields": {
                "identity": identity,
                "names": assertion({"kind": "text", "text": "; ".join(names)}),
                "boundary": assertion({"kind": "text", "text": "Observed syntax is limited to this file; runtime behavior is not inferred."}),
                "locators": assertion({"kind": "text", "text": "; ".join(item["locator"] for item in evidence_items)}),
            },
        })

    batch = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "sources": [source_record],
        "facts": facts,
        "navigation": [],
        "direct_nodes": [],
        "conflicts": [],
    }
    codec.validate_batch(batch)
    return batch
