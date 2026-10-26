"""Safe CI probe for optional semantic-fact acquisition tool candidates.

This script only probes tool presence/version and runs read-only/sample commands
against temporary fixtures. It never executes project source or enables matrix
entries. Missing optional tools are reported as unverified/unavailable, not fatal.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(argv: list[str], *, cwd: Path | None = None, timeout: int = 10) -> dict:
    try:
        completed = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return {
            "argv": argv,
            "exit_code": completed.returncode,
            "stdout": completed.stdout[:4000],
            "stderr": completed.stderr[:2000],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "argv": argv,
            "exit_code": None,
            "stdout": (error.stdout or "")[:1000] if isinstance(error.stdout, str) else "",
            "stderr": (error.stderr or "")[:1000] if isinstance(error.stderr, str) else "",
            "timed_out": True,
        }
    except OSError as error:
        return {"argv": argv, "exit_code": None, "stdout": "", "stderr": str(error), "timed_out": False}


def main() -> int:
    tools = {
        "python": (sys.executable, ["--version"]),
        "cargo": ("cargo", ["--version"]),
        "rustc": ("rustc", ["--version"]),
        "rust-analyzer": ("rust-analyzer", ["--version"]),
        "ctags": ("ctags", ["--version"]),
        "ast-grep": ("ast-grep", ["--version"]),
        "tree-sitter": ("tree-sitter", ["--version"]),
    }
    report = {
        "platform": platform.platform(),
        "python": sys.version,
        "tools": {},
        "sample_probes": {},
        "policy": "probe-only; no candidate is enabled by this script",
    }
    for name, (executable, args) in tools.items():
        path = shutil.which(executable)
        report["tools"][name] = {
            "path": path,
            "status": "present" if path else "not_installed_in_this_ci_environment",
            "version_probe": run([path, *args]) if path else None,
        }

    with tempfile.TemporaryDirectory(prefix="semantic-fact-tool-probe-") as temp:
        root = Path(temp)
        py_file = root / "probe.py"
        py_file.write_text("class Probe:\n    def run(self):\n        return 1\n", encoding="utf-8")
        if report["tools"]["python"]["path"]:
            report["sample_probes"]["python_compileall"] = run(
                [sys.executable, "-m", "compileall", "-q", str(py_file)], cwd=root
            )
        ctags = report["tools"]["ctags"]["path"]
        if ctags:
            report["sample_probes"]["ctags_json"] = run(
                [ctags, "--output-format=json", "--fields=+S", str(py_file)], cwd=root
            )
        ast_grep = report["tools"]["ast-grep"]["path"]
        if ast_grep:
            report["sample_probes"]["ast_grep_json"] = run(
                [ast_grep, "run", "--json=stream", "class $NAME", str(py_file)], cwd=root
            )
        cargo = report["tools"]["cargo"]["path"]
        if cargo:
            project = root / "cargo-project"
            (project / "src").mkdir(parents=True)
            (project / "Cargo.toml").write_text(
                '[package]\nname = "probe-project"\nversion = "0.1.0"\nedition = "2021"\n',
                encoding="utf-8",
            )
            (project / "src" / "lib.rs").write_text("pub fn probe() {}\n", encoding="utf-8")
            report["sample_probes"]["cargo_metadata"] = run(
                [cargo, "metadata", "--no-deps", "--format-version", "1", "--manifest-path", str(project / "Cargo.toml")],
                cwd=project,
                timeout=20,
            )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
