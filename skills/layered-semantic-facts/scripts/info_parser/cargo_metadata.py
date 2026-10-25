"""X-cargo_metadata 解析器：cargo metadata 原生输出 → 项目信息数据项（确定性转换）。

产出 cargo_package / cargo_target / cargo_dependency 三类信息数据项，
每条附源码证据定位（file:range），证据自 manifest_path/src_path 可回溯。
"""
import json
from pathlib import Path

from .framework import ParseFailure, ParseResult


def _rel(path_str, project_root):
    if not path_str:
        return path_str
    try:
        return Path(path_str).resolve().relative_to(Path(project_root).resolve()).as_posix()
    except (ValueError, TypeError, OSError):
        return path_str


def _toml_lines(manifest_path):
    with open(manifest_path, encoding="utf-8") as f:
        return f.read().splitlines()


def _section_range(lines, section):
    n = len(lines)
    for i, l in enumerate(lines):
        if l.strip() == f"[{section}]":
            start = i + 1
            for j in range(i + 1, n):
                if lines[j].startswith("["):
                    return (start, j)
            return (start, n)
    return None


def _dep_line(lines, section, name):
    rng = _section_range(lines, section)
    if rng is None:
        return None
    start, end = rng
    for i in range(start, end):
        if lines[i].strip().startswith(name + " ") or lines[i].strip().startswith(name + "="):
            return i + 1
    return None


def _package_item(pkg, manifest_lines, project_root):
    manifest_rel = _rel(pkg.get("manifest_path"), project_root)
    rng = _section_range(manifest_lines, "package") or (1, 1)
    return {
        "info_type": "cargo_package",
        "content": {
            "name": pkg["name"],
            "version": pkg.get("version"),
            "edition": pkg.get("edition"),
            "rust_version": pkg.get("rust_version"),
            "description": pkg.get("description"),
            "readme": pkg.get("readme"),
            "repository": pkg.get("repository"),
        },
        "evidence": {"file": manifest_rel, "range": f"{rng[0]}-{rng[1]}"},
        "source_tool": "X-cargo_metadata",
    }


def _target_item(t, project_root):
    src_rel = _rel(t.get("src_path"), project_root)
    return {
        "info_type": "cargo_target",
        "content": {
            "name": t["name"],
            "kind": t.get("kind") or [],
            "crate_types": t.get("crate_types") or [],
            "src_path": src_rel,
        },
        "evidence": {"file": src_rel, "range": "1-1"},
        "source_tool": "X-cargo_metadata",
    }


def _dependency_item(d, manifest_lines, project_root):
    manifest_rel = _rel(d.get("_manifest_path"), project_root)
    kind = d.get("kind") or "normal"
    section = {"normal": "dependencies", "dev": "dev-dependencies", "build": "build-dependencies"}[kind]
    line = _dep_line(manifest_lines, section, d["name"]) or 1
    return {
        "info_type": "cargo_dependency",
        "content": {
            "name": d["name"],
            "req": d.get("req"),
            "kind": kind,
            "optional": bool(d.get("optional")),
        },
        "evidence": {"file": manifest_rel, "range": f"{line}-{line}"},
        "source_tool": "X-cargo_metadata",
    }


def parse_cargo_metadata(raw_output, profile=None):
    """cargo metadata 输出 → ParseResult（信息数据项 / 结构化失败）。"""
    profile = profile or {}
    project_root = profile.get("project_root")
    if isinstance(raw_output, (bytes, str)):
        try:
            data = json.loads(raw_output)
        except (ValueError, TypeError) as exc:
            return ParseResult(failure=ParseFailure(
                tool_id="X-cargo_metadata", reason=f"无法解析 JSON：{exc}"))
    else:
        data = raw_output

    packages = data.get("packages") or []
    if not packages:
        return ParseResult(failure=ParseFailure(
            tool_id="X-cargo_metadata", reason="cargo metadata 无 packages"))

    pkg = packages[0]
    manifest_path = pkg.get("manifest_path")
    manifest_lines = _toml_lines(manifest_path) if manifest_path else []

    items = [_package_item(pkg, manifest_lines, project_root)]
    unparsed = []

    for t in pkg.get("targets") or []:
        if not t.get("name") or not t.get("src_path"):
            unparsed.append({"target": t})
            continue
        items.append(_target_item(t, project_root))

    for d in pkg.get("dependencies") or []:
        if not d.get("name"):
            unparsed.append({"dependency": d})
            continue
        dd = dict(d)
        dd["_manifest_path"] = manifest_path
        items.append(_dependency_item(dd, manifest_lines, project_root))

    result = ParseResult(items=items)
    if unparsed:
        result.failure = ParseFailure(
            tool_id="X-cargo_metadata", reason=f"{len(unparsed)} 项无法解析", unparsed=unparsed)
    return result
