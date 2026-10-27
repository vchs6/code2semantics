#!/usr/bin/env python3
"""Measure CodeGraph Explorer on a disposable mixed-language fixture.

This is a research harness only: it never writes into the checked-out repository,
never installs optional dependencies, and treats the candidate graph as untrusted
structural evidence rather than accepted semantic facts.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def write_fixture(root: Path) -> None:
    (root / "python_app").mkdir(parents=True)
    (root / "rust_worker" / "src").mkdir(parents=True)
    (root / "python_app" / "pyproject.toml").write_text(
        '[project]\nname = "python-app"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (root / "python_app" / "app.py").write_text(
        "from client import call_worker\n\n"
        "def handle_request(payload):\n"
        "    return call_worker(payload)\n\n"
        "def main():\n"
        "    return handle_request({'value': 'demo'})\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )
    (root / "python_app" / "client.py").write_text(
        "def call_worker(payload):\n"
        "    return payload\n",
        encoding="utf-8",
    )
    (root / "rust_worker" / "Cargo.toml").write_text(
        '[package]\nname = "rust-worker"\nversion = "0.1.0"\nedition = "2021"\n',
        encoding="utf-8",
    )
    (root / "rust_worker" / "src" / "lib.rs").write_text(
        "pub fn worker(payload: &str) -> String {\n"
        "    payload.to_owned()\n"
        "}\n",
        encoding="utf-8",
    )
    (root / "shared" ).mkdir()
    (root / "shared" / "worker.proto").write_text(
        'syntax = "proto3";\n'
        'package demo;\n'
        'service Worker { rpc Handle (Request) returns (Reply); }\n'
        'message Request { string value = 1; }\n'
        'message Reply { string value = 1; }\n',
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--builder", type=Path, required=True)
    args = parser.parse_args()
    builder = args.builder.resolve()
    if not builder.is_file():
        raise SystemExit(f"builder does not exist: {builder}")

    with tempfile.TemporaryDirectory(prefix="codegraph-eval-") as td:
        root = Path(td) / "mixed-project"
        root.mkdir()
        write_fixture(root)
        started = time.perf_counter()
        build = subprocess.run(
            ["python", str(builder), str(root)],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        build_seconds = time.perf_counter() - started
        graph_path = root / ".codegraph" / "graph.json"
        if build.returncode != 0 or not graph_path.is_file():
            print(json.dumps({
                "status": "build_failed",
                "returncode": build.returncode,
                "stderr_tail": build.stderr[-4000:],
                "stdout_tail": build.stdout[-4000:],
                "build_seconds": round(build_seconds, 4),
            }, ensure_ascii=False, indent=2))
            return 1

        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        paths = {str(n.get("path", "")) for n in nodes}
        types = {str(n.get("type", "")) for n in nodes}
        edge_types = {str(e.get("type", "")) for e in edges}
        required = {
            "python_app/app.py": any(p.endswith("python_app/app.py") for p in paths),
            "python_app/client.py": any(p.endswith("python_app/client.py") for p in paths),
            "rust_worker/src/lib.rs": any(p.endswith("rust_worker/src/lib.rs") for p in paths),
        }
        output = {
            "status": "passed" if all(required.values()) else "partial",
            "candidate": "CodeGraph Explorer",
            "candidate_revision": "6a95e4f0ae643fad7354ac388ceaa2dc2c2f3f74",
            "fixture": "Python app + Rust library + shared proto schema",
            "build_returncode": build.returncode,
            "build_seconds": round(build_seconds, 4),
            "graph_bytes": graph_path.stat().st_size,
            "total_nodes_reported": graph.get("total_nodes"),
            "actual_node_count": len(nodes),
            "total_edges_reported": graph.get("total_edges"),
            "actual_edge_count": len(edges),
            "node_types": sorted(types),
            "edge_types": sorted(edge_types),
            "required_source_paths_present": required,
            "python_to_rust_semantic_link_proven": False,
            "token_usage": {
                "candidate_code_graph_build_llm_tokens": 0,
                "basis": "The harness invokes the local Python builder directly and makes no model/API calls; this is not a measurement of tokens spent by a Skill host."
            },
            "limitations": [
                "This harness measures a local full graph build and structural inventory only.",
                "It does not prove cross-language call resolution from Python to Rust.",
                "The proto file is included to test project discovery, not to claim RPC wiring is understood.",
                "The graph is untrusted candidate evidence, not a validated semantic FactBatch."
            ],
            "builder_stdout_tail": build.stdout[-1500:],
            "builder_stderr_tail": build.stderr[-1500:],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if all(required.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
