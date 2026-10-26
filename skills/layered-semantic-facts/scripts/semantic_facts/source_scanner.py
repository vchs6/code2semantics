"""Scan current Python source and orchestrate parser plus deterministic constructor."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

from .fact_constructor import construct_fact_batch
from .info_parser import ParserRegistry
from .repository.contract import ContractCodec


EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}



def _git_state(root: Path) -> tuple[bool, bool]:
    """Return (dirty, has_untracked); unknown VCS state is conservatively not clean."""
    try:
        subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True, capture_output=True, text=True,
        )
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "--", "."],
            check=True, capture_output=True, text=True,
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        return True, True
    dirty = any(not line.startswith("??") for line in status)
    untracked = any(line.startswith("??") for line in status)
    return dirty, untracked

def build_fact_batch(root: str | Path, codec: ContractCodec) -> dict[str, Any]:
    """Read current Python source, parse it, and construct a validated FactBatch."""
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

    raw: list[tuple[str, str]] = []
    for path in files:
        try:
            source_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"Python source is not UTF-8: {path.relative_to(project_root)}") from error
        raw.append((path.relative_to(project_root).as_posix(), source_text))

    snapshot_digest = hashlib.sha256()
    for relative, source_text in raw:
        snapshot_digest.update(relative.encode("utf-8"))
        snapshot_digest.update(b"\\0")
        snapshot_digest.update(hashlib.sha256(source_text.encode("utf-8")).digest())
    content_state = "sha256:" + snapshot_digest.hexdigest()
    root_hash = hashlib.sha256(str(project_root).encode("utf-8")).hexdigest()[:20]
    source_id = "src-" + root_hash
    subject_id = "project-" + root_hash
    dirty, has_untracked = _git_state(project_root)
    source_record = {
        "source_id": source_id,
        "root": str(project_root),
        "content_state": content_state,
        "status": "available",
        "dirty": dirty,
        "has_untracked": has_untracked,
        "excludes": sorted(EXCLUDED_DIRS),
    }

    parsed_files: list[tuple[str, dict[str, Any]]] = []
    parser_registry = ParserRegistry(codec.schema_root)
    for relative, source_text in raw:
        coverage = {
            "domain": f"Python syntax in {relative}",
            "checked": [relative],
            "excluded": [],
            "completeness": "complete",
            "method": "Python ast.parse",
        }
        request = {
            "kind": "parse_request",
            "tool_native_output": {"encoding": "utf-8", "text": source_text},
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
        parsed_files.append((relative, parser_registry.parse(request)))

    return construct_fact_batch(source_record, subject_id, parsed_files, codec)
