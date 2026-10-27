#!/usr/bin/env python3
"""Measure CodeGraph Explorer on a disposable mixed-language fixture.

The fixture is synthetic and generated in a temporary directory. The candidate
builder is pinned by the workflow; its graph is untrusted structural evidence.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def write_fixture(root: Path, module_count: int = 50) -> None:
    py = root / "python_app"
    rust = root / "rust_worker" / "src"
    shared = root / "shared"
    py.mkdir(parents=True)
    rust.mkdir(parents=True)
    shared.mkdir(parents=True)
    (py / "pyproject.toml").write_text(
        '[project]\nname = "python-app"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (py / "app.py").write_text(
        "from client import call_worker\n"
        "import module_000  # declared import only; transform_000 is not called\n\n"
        "def handle_request(payload):\n"
        "    return call_worker(payload)\n\n"
        "def transform_000(value):\n"
        "    return value\n\n"
        "def main():\n"
        "    return handle_request({'value': 'demo'})\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )
    (py / "client.py").write_text(
        "def call_worker(payload):\n"
        "    return payload\n",
        encoding="utf-8",
    )
    for i in range(module_count):
        (py / f"module_{i:03}.py").write_text(
            f"def transform_{i}(value):\n    return value\n",
            encoding="utf-8",
        )
    (root / "rust_worker" / "Cargo.toml").write_text(
        '[package]\nname = "rust-worker"\nversion = "0.1.0"\nedition = "2021"\n',
        encoding="utf-8",
    )
    declarations = [f"pub mod module_{i:03};" for i in range(module_count)]
    (rust / "lib.rs").write_text("\n".join(declarations) + "\n", encoding="utf-8")
    for i in range(module_count):
        (rust / f"module_{i:03}.rs").write_text(
            f"pub fn transform_{i}(value: &str) -> String {{ value.to_owned() }}\n",
            encoding="utf-8",
        )
    (shared / "worker.proto").write_text(
        'syntax = "proto3";\n'
        'package demo;\n'
        'service Worker { rpc Handle (Request) returns (Reply); }\n'
        'message Request { string value = 1; }\n'
        'message Reply { string value = 1; }\n',
        encoding="utf-8",
    )


def run(command: list[str], cwd: Path, timeout: int = 180) -> dict:
    started = time.perf_counter()
    proc = subprocess.run(
        command, cwd=cwd, text=True, capture_output=True, timeout=timeout,
        check=False, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return {
        "returncode": proc.returncode,
        "seconds": round(time.perf_counter() - started, 4),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--builder", type=Path, required=True)
    parser.add_argument("--modules-per-language", type=int, default=50)
    parser.add_argument("--query-repeats", type=int, default=10)
    args = parser.parse_args()
    builder = args.builder.resolve()
    if not builder.is_file():
        raise SystemExit(f"builder does not exist: {builder}")

    with tempfile.TemporaryDirectory(prefix="codegraph-eval-") as td:
        root = Path(td) / "mixed-project"
        root.mkdir()
        write_fixture(root, args.modules_per_language)
        fixture_files = sum(1 for p in root.rglob("*") if p.is_file())
        build = run(["python", str(builder), str(root)], root)
        graph_path = root / ".codegraph" / "graph.json"
        if build["returncode"] != 0 or not graph_path.is_file():
            print(json.dumps({
                "status": "build_failed", "candidate_revision": "6a95e4f0ae643fad7354ac388ceaa2dc2c2f3f74",
                "fixture_files": fixture_files, "build": {k: v for k, v in build.items() if k != "stdout"},
                "stdout_tail": build["stdout"][-3000:],
            }, ensure_ascii=False, indent=2))
            return 1

        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        nodes, edges = graph.get("nodes", []), graph.get("edges", [])
        paths = {str(n.get("path", "")) for n in nodes}
        types = {str(n.get("type", "")) for n in nodes}
        edge_types = {str(e.get("type", "")) for e in edges}
        required = {
            "python_app/app.py": any(p.endswith("python_app/app.py") for p in paths),
            "python_app/client.py": any(p.endswith("python_app/client.py") for p in paths),
            "rust_worker/src/lib.rs": any(p.endswith("rust_worker/src/lib.rs") for p in paths),
            "rust_worker/src/module_000.rs": any(p.endswith("rust_worker/src/module_000.rs") for p in paths),
        }

        query_runs = [run(["python", str(builder), str(root), "--callers", "handle_request", "--json"], root) for _ in range(args.query_repeats)]
        query = query_runs[0] if query_runs else {"returncode": 1, "seconds": 0.0, "stdout": "", "stderr": "no query runs"}
        expected_call = run(["python", str(builder), str(root), "--callers", "call_worker", "--json"], root)
        decoy_call = run(["python", str(builder), str(root), "--callers", "transform_000", "--json"], root)
        try:
            expected_call_rows = json.loads(expected_call["stdout"])
            decoy_call_rows = json.loads(decoy_call["stdout"])
        except json.JSONDecodeError:
            expected_call_rows, decoy_call_rows = [], []
        expected_edge_present = (
            expected_call["returncode"] == 0
            and '"node": "handle_request"' in expected_call["stdout"]
            and '"type": "calls"' in expected_call["stdout"]
        )
        decoy_edge_absent = (
            decoy_call["returncode"] == 0
            and "No callers found" in decoy_call["stdout"]
        )
        update = None
        if query["returncode"] == 0:
            (py_file := root / "python_app" / "module_000.py").write_text(
                "def transform_000(value):\n    return value + 1\n", encoding="utf-8"
            )
            update = run(["python", str(builder), "--update", str(root)], root)

        output = {
            "status": "passed" if all(required.values()) and query_runs and all(q["returncode"] == 0 for q in query_runs) and expected_edge_present and decoy_edge_absent else "partial",
            "candidate": "CodeGraph Explorer",
            "candidate_revision": "6a95e4f0ae643fad7354ac388ceaa2dc2c2f3f74",
            "fixture": "Python app + Rust library + shared proto schema + generated modules",
            "modules_per_language": args.modules_per_language,
            "fixture_file_count": fixture_files,
            "full_build_seconds": build["seconds"],
            "graph_bytes": graph_path.stat().st_size,
            "total_nodes_reported": graph.get("total_nodes"),
            "actual_node_count": len(nodes),
            "total_edges_reported": graph.get("total_edges"),
            "actual_edge_count": len(edges),
            "node_types": sorted(types),
            "edge_types": sorted(edge_types),
            "required_source_paths_present": required,
            "relation_quality_checks": {
                "handle_request_calls_call_worker": expected_edge_present,
                "import_only_does_not_create_call_to_transform_000": decoy_edge_absent,
                "expected_call_query_returncode": expected_call["returncode"],
                "decoy_call_query_returncode": decoy_call["returncode"],
                "expected_call_output": expected_call["stdout"][-1200:],
                "decoy_call_output": decoy_call["stdout"][-1200:],
            },
            "query": {
                "command": "--callers handle_request --json",
                "repeat_count": len(query_runs),
                "all_returncodes_zero": all(q["returncode"] == 0 for q in query_runs),
                "seconds_each": [q["seconds"] for q in query_runs],
                "seconds_total": round(sum(q["seconds"] for q in query_runs), 4),
                "seconds_mean": round(sum(q["seconds"] for q in query_runs) / max(1, len(query_runs)), 4),
                "output_bytes_each": [len(q["stdout"].encode("utf-8")) for q in query_runs],
                "stderr_tail": query["stderr"][-1000:],
                "stdout_tail": query["stdout"][-1200:],
            },
            "incremental_update": None if update is None else {
                "returncode": update["returncode"],
                "seconds": update["seconds"],
                "stderr_tail": update["stderr"][-1000:],
                "stdout_tail": update["stdout"][-1200:],
            },
            "token_usage": {
                "candidate_code_graph_build_llm_tokens": 0,
                "basis": "Direct local Python builder and query CLI only; no model/API calls. This is not a measurement of Skill-host instruction/orchestration tokens."
            },
            "python_to_rust_semantic_link_proven": False,
            "limitations": [
                "Synthetic CI benchmark, not a production repository benchmark.",
                "Graph build includes all fixture files; no partial-build capability was assumed.",
                "Cross-language calls through the shared proto schema are not asserted as resolved.",
                "The graph is untrusted candidate evidence, not a validated semantic FactBatch."
            ],
            "builder_stdout_tail": build["stdout"][-1200:],
            "builder_stderr_tail": build["stderr"][-1200:],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if output["status"] == "passed" and (update is None or update["returncode"] == 0) and expected_edge_present and decoy_edge_absent else 2


if __name__ == "__main__":
    raise SystemExit(main())
