import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "layered-semantic-facts"


def _run_installed(skill_root: Path, args: list[str], cwd: Path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(skill_root / "scripts")
    return subprocess.run(
        [sys.executable, "-m", "semantic_facts.cli", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )


def test_copied_skill_scans_python_and_rust_then_queries_without_repo_paths(tmp_path):
    installed = tmp_path / "installed-skill"
    shutil.copytree(SKILL_ROOT, installed)

    project = tmp_path / "external-project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.py").write_text(
        "class PythonEngine:\n    def run(self):\n        return True\n",
        encoding="utf-8",
    )
    (project / "src" / "lib.rs").write_text(
        "pub struct RustEngine;\npub enum Mode { Fast, Safe }\n",
        encoding="utf-8",
    )

    database = tmp_path / "installed-facts.db"
    batch_file = tmp_path / "fact-batch.json"
    scan = _run_installed(
        installed,
        ["scan-source", "--root", str(project), "--db", str(database), "--output", str(batch_file)],
        tmp_path,
    )
    scan_report = json.loads(scan.stdout)
    batch = json.loads(batch_file.read_text(encoding="utf-8"))
    assert scan_report["status"] == "stored"
    assert len(batch["facts"]) == 2
    assert {fact["fields"]["names"]["context"]["environment"]["language"] for fact in batch["facts"]} == {"Python", "Rust"}

    query = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "copied-skill-query",
        "scope": {
            "scope_id": "copied-skill-scope",
            "directories": [str(project.resolve())],
            "excludes": [],
            "defaulted": False,
        },
        "target": {"kind": "scope"},
        "granularity": "L3",
        "selections": [{"fact_type": "F2", "fields": ["identity", "names"]}],
        "budget": {"max_rounds": 2, "max_new_assertions": 20},
    }
    query_file = tmp_path / "query.json"
    query_file.write_text(json.dumps(query), encoding="utf-8")
    result = _run_installed(
        installed,
        ["query", "--db", str(database), "--query-file", str(query_file)],
        tmp_path,
    )
    response = json.loads(result.stdout)
    assert response["termination"] == "satisfied"
    assert len(response["results"]) == 2
    assert any("class PythonEngine" in fact["fields"]["names"]["value"]["text"] for fact in response["results"])
    assert any("struct RustEngine" in fact["fields"]["names"]["value"]["text"] for fact in response["results"])
