from __future__ import annotations

import json
import shutil

from semantic_facts.query_engine import execute_query_with_construction
from semantic_facts import cli
from semantic_facts.repository.store import Repository
from semantic_facts.tool_executor import SubprocessToolExecutor
from test_information_needs import ASSETS


def test_cli_query_invokes_cargo_once_and_returns_distinct_membership_and_dependency(tmp_path, monkeypatch, capsys):
    project = tmp_path / "runtime-workspace"
    (project / "crates" / "app" / "src").mkdir(parents=True)
    (project / "crates" / "core" / "src").mkdir(parents=True)
    (project / "Cargo.toml").write_text(
        '[workspace]\nmembers = ["crates/app", "crates/core"]\nresolver = "2"\n',
        encoding="utf-8",
    )
    (project / "crates" / "app" / "Cargo.toml").write_text(
        '[package]\nname = "runtime-app"\nversion = "0.1.0"\nedition = "2021"\n'
        '[dependencies]\nruntime-core = { path = "../core" }\n',
        encoding="utf-8",
    )
    (project / "crates" / "core" / "Cargo.toml").write_text(
        '[package]\nname = "runtime-core"\nversion = "0.1.0"\nedition = "2021"\n',
        encoding="utf-8",
    )
    (project / "crates" / "app" / "src" / "lib.rs").write_text("pub fn run() {}\n", encoding="utf-8")
    (project / "crates" / "core" / "src" / "lib.rs").write_text("pub fn core() {}\n", encoding="utf-8")

    assets = tmp_path / "assets"
    shutil.copytree(ASSETS, assets)
    matrix_path = assets / "capability-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    profile = next(item for item in matrix["entries"] if item["tool_id"] == "rust.cargo-metadata")
    profile["enabled"] = True
    profile["acceptance"] = {
        "actor": "parser_development",
        "evidence": ["tests/test_info_parser.py::test_cargo_metadata_parser_emits_workspace_and_dependency_observations_separately"],
    }
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    query = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "runtime-workspace-members-and-dependencies",
        "scope": {
            "scope_id": "runtime-workspace-scope",
            "directories": [str(project.resolve())],
            "excludes": [],
            "defaulted": False,
        },
        "target": {"kind": "scope"},
        "granularity": "L2",
        "selections": [
            {"fact_type": "F4", "fields": ["kind"]},
            {"fact_type": "F6", "fields": ["kind"]},
        ],
        "budget": {"max_rounds": 2, "max_new_assertions": 20},
    }

    calls = []
    original_execute = SubprocessToolExecutor.execute

    def traced_execute(self, tool_id, args, *, cwd, timeout_seconds):
        calls.append((tool_id, tuple(args), str(cwd)))
        return original_execute(self, tool_id, args, cwd=cwd, timeout_seconds=timeout_seconds)

    monkeypatch.setattr(SubprocessToolExecutor, "execute", traced_execute)
    database = tmp_path / "runtime-workspace.sqlite"
    query_path = tmp_path / "runtime-query.json"
    query_path.write_text(json.dumps(query), encoding="utf-8")
    monkeypatch.setattr(cli, "_assets", lambda: assets)

    assert cli.main(["query", "--db", str(database), "--query-file", str(query_path)]) == 0
    response = json.loads(capsys.readouterr().out)
    assert response["termination"] == "satisfied", {"gaps": [(gap["reason"], gap["detail"]) for gap in response["gaps"]], "calls": calls}
    assert {fact["fact_type"] for fact in response["results"]} == {"F4", "F6"}
    assert all(set(fact["fields"]) == {"kind"} for fact in response["results"])
    values = [fact["fields"]["kind"]["value"].get("text", "") for fact in response["results"]]
    assert any("workspace member: runtime-app" in value for value in values)
    assert any("workspace member: runtime-core" in value for value in values)
    assert any("runtime-app -> runtime-core" in value for value in values)
    assert all(fact["fields"]["kind"]["basis"]["evidence"] for fact in response["results"])
    assert len(calls) == 1, calls

    reopened = Repository(database, assets)
    try:
        replay = execute_query_with_construction(query, reopened, assets, external_executor=cli.build_default_tool_executor())
        assert replay["termination"] == "satisfied", replay
        assert all(set(fact["fields"]) == {"kind"} for fact in replay["results"])
        assert len(executor.calls) == 1, executor.calls
    finally:
        reopened.close()
