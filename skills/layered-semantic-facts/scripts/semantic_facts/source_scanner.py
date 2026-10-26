"""Deterministic source inventory for Python projects.

This component observes Python syntax only. It does not infer runtime behavior,
execute source code, or delete/replace previously stored fact rows.
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path
from typing import Any

from .repository.contract import ContractCodec


EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._:-]+", "-", value).strip("-") or "unnamed"


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _symbol_names(source: str, filename: str) -> list[str]:
    tree = ast.parse(source, filename=filename)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(f"function:{node.name}")
        elif isinstance(node, ast.ClassDef):
            names.append(f"class:{node.name}")
        elif isinstance(node, ast.Import):
            names.extend(f"import:{alias.name}" for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names.extend(f"import:{module}.{alias.name}".strip(".") for alias in node.names)
    return sorted(set(names))


def build_fact_batch(root: str | Path, codec: ContractCodec) -> dict[str, Any]:
    """Scan Python files and build a schema-validated F2 syntax-inventory batch."""
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

    raw: list[tuple[Path, str, bytes, list[str]]] = []
    for path in files:
        content = path.read_bytes()
        try:
            source = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"Python source is not UTF-8: {path.relative_to(project_root)}") from error
        relative = path.relative_to(project_root).as_posix()
        try:
            names = _symbol_names(source, relative)
        except SyntaxError as error:
            raise ValueError(f"cannot parse {relative}:{error.lineno}: {error.msg}") from error
        raw.append((path, relative, content, names))

    snapshot_digest = hashlib.sha256()
    for _, relative, content, _ in raw:
        snapshot_digest.update(relative.encode("utf-8"))
        snapshot_digest.update(b"\0")
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
    for _, relative, content, names in raw:
        file_digest = _digest(content)
        node_id = "file-" + hashlib.sha256(relative.encode("utf-8")).hexdigest()[:20]
        fact_id = "fact-" + hashlib.sha256((relative + "\0F2").encode("utf-8")).hexdigest()[:20]
        evidence_id = "ev-" + hashlib.sha256((relative + "\0" + file_digest).encode("utf-8")).hexdigest()[:20]
        context = {
            "source_ids": [source_id],
            "conditions": [],
            "environment": {"language": "Python"},
            "language_semantics": ["Python syntax inventory; runtime behavior not inferred"],
        }
        coverage = {
            "domain": f"Python syntax in {relative}",
            "checked": [relative],
            "excluded": [],
            "completeness": "complete",
            "method": "Python ast.parse",
        }
        evidence = {
            "evidence_id": evidence_id,
            "source_id": source_id,
            "content_state": content_state,
            "kind": "source",
            "locator": f"{relative}:file",
            "content_digest": file_digest,
            "relation": "supports",
        }
        def assertion(text: str) -> dict[str, Any]:
            return {
                "origin": "observed",
                "knowledge": "supported",
                "context": context,
                "coverage": coverage,
                "basis": {
                    "evidence": [evidence],
                    "premises": [],
                    "method": "deterministic Python AST syntax inventory",
                    "limitations": ["Does not infer runtime behavior or intent"],
                },
                "value": {"kind": "text", "text": text},
                "validity": {"state": "current", "sources": [{"source_id": source_id, "content_state": content_state}]},
            }

        facts.append({
            "fact_id": fact_id,
            "node": {"source_id": source_id, "subject_id": subject_id, "node_id": node_id},
            "fact_type": "F2",
            "granularities": ["L3"],
            "fields": {
                "identity": assertion(f"Python source file: {relative}"),
                "names": assertion("; ".join(names) if names else f"No class/function/import declarations in {relative}"),
                "boundary": assertion("Observed syntax is limited to this file; runtime behavior is not inferred."),
                "locators": assertion(f"{relative}:file"),
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
