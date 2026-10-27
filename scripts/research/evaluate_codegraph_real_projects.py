#!/usr/bin/env python3
"""Run a pinned CodeGraph builder on a real, separately checked-out source repository.

Research-only: do not execute the analyzed project's build/tests; no API/model use.
Graphs and timings are not evidence of complete semantic fact coverage.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def run(argv: list[str], cwd: Path, timeout: int = 240) -> dict:
    begin = time.perf_counter()
    try:
        p = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, errors="replace",
            check=False, timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return {
            "returncode": p.returncode,
            "seconds": round(time.perf_counter() - begin, 4),
            "stdout": p.stdout[-2400:],
            "stderr": p.stderr[-2400:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": None,
            "seconds": round(time.perf_counter() - begin, 4),
            "stdout": str(exc.stdout or "")[-2400:],
            "stderr": str(exc.stderr or "")[-2400:],
            "timeout": True,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--builder", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--query-repeats", type=int, default=10)
    args = parser.parse_args()

    root = args.root.resolve()
    builder = args.builder.resolve()
    if not root.is_dir() or not builder.is_file():
        raise SystemExit("missing pinned project checkout or candidate builder")
    assert args.query_repeats > 0
    checkout = run(["git", "rev-parse", "HEAD"], root)
    actual_revision = checkout["stdout"].strip()
    if checkout["returncode"] != 0 or actual_revision != args.revision:
        raise SystemExit(f"revision mismatch: {actual_revision} != {args.revision}")

    initial_files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
        and ".codegraph" not in p.relative_to(root).parts
    )
    lang_counts = dict(Counter(
        ".rs" if p.suffix == ".rs" else ".py" if p.suffix == ".py" else "other"
        for p in initial_files
    ))
    baseline = run(["git", "status", "--porcelain"], root)

    build = run([sys.executable, str(builder), str(root)], root, timeout=240)
    graph_path = root / ".codegraph" / "graph.json"
    result = {
        "project": args.name,
        "project_revision": args.revision,
        "candidate_revision": "6a95e4f0ae643fad7354ac388ceaa2dc2c2f3f74",
        "file_count": len(initial_files),
        "file_types": lang_counts,
        "initial_worktree_clean": baseline["stdout"] == "",
        "build": build,
        "project_code_executed": False,
        "model_calls_in_harness": 0,
    }
    if build["returncode"] != 0 or not graph_path.is_file():
        result["status"] = "build_failed"
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    relative_paths = [str(n.get("path", "")) for n in nodes]
    indexed = {n.get("id"): n for n in nodes}
    names = Counter(str(n.get("name", "")) for n in nodes)
    targets = [
        n for n in nodes
        if n.get("type") == "function"
        and names[str(n.get("name"))] == 1
        and any(e.get("target") == n.get("id") and e.get("type") == "calls" for e in edges)
    ]
    target = targets[0] if targets else next(
        (n for n in nodes if n.get("type") == "function" and names[str(n.get("name"))] == 1),
        None,
    )
    query_results = []
    for _ in range(args.query_repeats):
        if target is None:
            break
        query_results.append(
            run([sys.executable, str(builder), str(root), "--callers", str(target["name"]), "--json"], root, timeout=120)
        )
    structured_query = False
    result_shape = "unavailable"
    if query_results:
        try:
            value = json.loads(query_results[0]["stdout"])
            structured_query = isinstance(value, list)
            result_shape = type(value).__name__
        except (json.JSONDecodeError, TypeError):
            result_shape = "non_json"
    result["graph"] = {
        "bytes": graph_path.stat().st_size,
        "nodes": len(nodes),
        "edges": len(edges),
        "node_types": dict(Counter(str(n.get("type")) for n in nodes)),
        "edge_types": dict(Counter(str(e.get("type")) for e in edges)),
        "tag_counts": dict(Counter(str(e.get("tag")) for e in edges)),
        "source_path_sample": sorted(set(relative_paths))[:8],
        "source_locator_present": sum(
            1 for n in nodes if n.get("path") and n.get("line_start") is not None
        ),
        "dangling_edges": sum(
            1 for e in edges if e.get("source") not in indexed or e.get("target") not in indexed
        ),
    }
    result["query"] = {
        "target": str(target.get("name")) if target else None,
        "repeat_count": len(query_results),
        "mean_seconds": round(sum(q["seconds"] for q in query_results) / max(1, len(query_results)), 4),
        "all_success": bool(query_results) and all(q["returncode"] == 0 for q in query_results),
        "structured_json_list": structured_query,
        "result_shape": result_shape,
        "output_bytes": len(query_results[0]["stdout"].encode("utf-8")) if query_results else None,
        "output_sample": query_results[0]["stdout"][-800:] if query_results else None,
    }

    # Only edit the separate CI checkout, not the user's source repository.
    target_file = next(
        (p for p in initial_files if p.suffix in {".py", ".rs"} and p.is_file()),
        None,
    )
    if target_file:
        original = target_file.read_bytes()
        try:
            target_file.write_bytes(original + b"\n// codegraph temporary benchmark comment\n"
                                    if target_file.suffix == ".rs"
                                    else original + b"\n# codegraph temporary benchmark comment\n")
            update = run([sys.executable, str(builder), "--update", str(root)], root, timeout=240)
        finally:
            target_file.write_bytes(original)
        result["incremental"] = {
            "changed_file": str(target_file.relative_to(root)),
            "returncode": update["returncode"],
            "seconds": update["seconds"],
            "output": update["stdout"][-1300:],
        }
    # Adversarial current-source validity check: change content without changing mtime.
    # A cache keyed only on mtime may incorrectly keep the old graph.
    if target_file:
        original = target_file.read_bytes()
        stat_before = target_file.stat()
        marker = "__codegraph_same_mtime_source_change_probe"
        declaration = (
            b"\npub fn __codegraph_same_mtime_source_change_probe() {}\n"
            if target_file.suffix == ".rs"
            else b"\ndef __codegraph_same_mtime_source_change_probe():\n    return None\n"
        )
        try:
            target_file.write_bytes(original + declaration)
            os.utime(target_file, ns=(stat_before.st_atime_ns, stat_before.st_mtime_ns))
            same_mtime = run([sys.executable, str(builder), "--update", str(root)], root, timeout=240)
            updated_graph = json.loads(graph_path.read_text(encoding="utf-8"))
            marker_found = any(n.get("name") == marker for n in updated_graph.get("nodes", []))
        finally:
            target_file.write_bytes(original)
        result["unchanged_mtime_content_change"] = {
            "file": str(target_file.relative_to(root)),
            "returncode": same_mtime["returncode"],
            "seconds": same_mtime["seconds"],
            "new_declaration_detected": marker_found,
            "cache_staleness_observed": not marker_found,
            "output": same_mtime["stdout"][-1100:],
            "note": "Adversarial test of graph validity, not a project semantic analysis claim.",
        }
    # Worktree status may show only the managed .codegraph artifacts.
    after = run(["git", "status", "--porcelain"], root)
    result["source_checkout_status_after"] = after["stdout"][-900:]
    result["limitations"] = [
        "Real repository and candidate script, but one single CI-run timing sample.",
        "No project application code or build/test hooks were executed.",
        "A structured graph cannot directly establish full F1-F18 semantic facts.",
        "A discovered call edge is not by itself evidence of dynamic dispatch or runtime execution.",
        "No cross-language semantic links are assumed or claimed.",
        "Skill-host orchestration tokens and direct-tool comparison are not measured.",
    ]
    result["status"] = (
        "passed"
        if build["returncode"] == 0 and result["graph"]["dangling_edges"] == 0
        and result["query"]["all_success"] and structured_query
        and result.get("incremental", {}).get("returncode") == 0
        else "partial"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
