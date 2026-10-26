"""Scan current Python source and orchestrate parser plus deterministic constructor."""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .fact_constructor import construct_fact_batch
from .constructor_plan import select_enabled_producers
from .capability_matrix import CapabilityMatrix
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


def inspect_source(root: str | Path) -> dict[str, Any]:
    """Compute current source identity/state without parsing or constructing facts."""
    project_root = Path(root).resolve()
    if not project_root.is_dir():
        raise ValueError(f"source root is not a directory: {project_root}")
    files = sorted(
        path for path in project_root.rglob("*")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(project_root).parts)
        and path.is_file() and path.suffix in {".py", ".rs"}
    )
    snapshot_digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(project_root).as_posix()
        content = path.read_bytes()
        snapshot_digest.update(relative.encode("utf-8"))
        snapshot_digest.update(b"\\0")
        snapshot_digest.update(hashlib.sha256(content).digest())
    snapshot_hash = snapshot_digest.hexdigest()
    root_hash = hashlib.sha256(str(project_root).encode("utf-8")).hexdigest()[:20]
    dirty, has_untracked = _git_state(project_root)
    return {
        "source_id": "src-" + root_hash + "-" + snapshot_hash[:20],
        "root": str(project_root),
        "content_state": "sha256:" + snapshot_hash,
        "status": "available",
        "dirty": dirty,
        "has_untracked": has_untracked,
        "excludes": sorted(EXCLUDED_DIRS),
    }


def build_fact_batch(root: str | Path, codec: ContractCodec) -> dict[str, Any]:
    """Read current Python source, parse it, and construct a validated FactBatch."""
    project_root = Path(root).resolve()
    if not project_root.is_dir():
        raise ValueError(f"source root is not a directory: {project_root}")

    files = sorted(
        path for path in project_root.rglob("*")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(project_root).parts)
        and path.is_file() and path.suffix in {".py", ".rs"}
    )
    if not files:
        raise ValueError(f"no Python or Rust source files found under {project_root}")

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
    snapshot_hash = snapshot_digest.hexdigest()
    content_state = "sha256:" + snapshot_hash
    root_hash = hashlib.sha256(str(project_root).encode("utf-8")).hexdigest()[:20]
    # Version source identity by content so re-scans append a new fact set rather
    # than replacing or deleting facts from an earlier source state.
    source_id = "src-" + root_hash + "-" + snapshot_hash[:20]
    subject_id = re.sub(r"[^A-Za-z0-9._:-]+", "-", str(project_root)).strip("-") or "unnamed"
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
    matrix = CapabilityMatrix(Path(__file__).resolve().parents[2] / "assets" / "capability-matrix.json")
    platform = "windows" if sys.platform.startswith("win") else "darwin" if sys.platform == "darwin" else "linux"
    required_need_ids = ["syntax.f2.identity", "syntax.f2.names", "syntax.f2.boundary", "syntax.f2.locators"]
    for relative, source_text in raw:
        language = "Rust" if Path(relative).suffix == ".rs" else "Python"
        selected_by_need = select_enabled_producers(matrix, required_need_ids, language, platform, "in-process")
        common_tool_ids = set.intersection(*(
            {entry["tool_id"] for entry in entries} for entries in selected_by_need.values()
        )) if selected_by_need else set()
        if not common_tool_ids:
            raise ValueError(f"no accepted enabled parser covers all required F2 needs for {language} in {platform}")
        tool_id = sorted(common_tool_ids)[0]
        coverage = {
            "domain": language + " syntax in " + relative,
            "checked": [relative],
            "excluded": [],
            "completeness": "complete",
            "method": "deterministic declaration parser",
        }
        request = {
            "kind": "parse_request",
            "tool_native_output": {"encoding": "utf-8", "text": source_text},
            "invocation_profile": {
                "tool_id": tool_id,
                "tool_version": "rust-source-parser-1" if language == "Rust" else "3.12+",
                "command": ["source-parser", relative],
                "environment": {"language": language},
                "sources": [source_record],
                "coverage": coverage,
                "evidence": [],
            },
        }
        parsed_files.append((relative, parser_registry.parse(request)))

    return construct_fact_batch(source_record, subject_id, parsed_files, codec)
