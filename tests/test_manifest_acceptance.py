from __future__ import annotations

import json
import shutil

from semantic_facts.constructor import execute_constructor_request
from semantic_facts.query_engine import execute_query
from semantic_facts.repository.store import Repository
from test_information_needs import ASSETS, request


def test_python_manifest_to_factbatch_sqlite_reopen_and_minimal_query(tmp_path):
    project = tmp_path / "python-manifest-project"
    project.mkdir()
    (project / "app.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        '[project]\nname = "manifest-acceptance"\nversion = "1.0.0"\n'
        'dependencies = ["requests>=2"]\n',
        encoding="utf-8",
    )

    assets = tmp_path / "assets"
    shutil.copytree(ASSETS, assets)
    matrix_path = assets / "capability-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    profile = next(item for item in matrix["entries"] if item["tool_id"] == "python.pyproject-toml")
    profile["enabled"] = True
    profile["acceptance"] = {
        "actor": "parser_development",
        "evidence": ["tests/test_info_parser.py::test_pyproject_toml_parser_emits_manifest_and_script_observations"],
    }
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    value = request(("identity", "names"))
    value["query"]["scope"]["directories"] = [str(project.resolve())]
    value["query"]["selections"] = [
        {"fact_type": "F2", "fields": ["identity", "names"]},
        {"fact_type": "F3", "fields": ["runtime"]},
        {"fact_type": "F6", "fields": ["kind"]},
    ]
    result = execute_constructor_request(value, assets)
    assert not any(gap["reason"] == "source_modified" for gap in result["gaps"])
    assert any(fact["fact_type"] == "F3" for fact in result["batch"]["facts"]), result["gaps"]
    assert any(fact["fact_type"] == "F6" for fact in result["batch"]["facts"]), result["gaps"]

    database = tmp_path / "manifest-acceptance.sqlite"
    repository = Repository(database, assets)
    repository.write(result["batch"], "python-manifest-acceptance")
    repository.close()

    reopened = Repository(database, assets)
    try:
        query = {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "request_id": "python-manifest-minimal",
            "scope": {
                "scope_id": "python-manifest-scope",
                "directories": [str(project.resolve())],
                "excludes": [],
                "defaulted": False,
            },
            "target": {"kind": "scope"},
            "granularity": "L2",
            "selections": [{"fact_type": "F3", "fields": ["runtime"]}],
            "budget": {"max_rounds": 1, "max_new_assertions": 10},
        }
        response = execute_query(query, reopened, assets)
        assert response["termination"] == "satisfied", response
        assert response["results"]
        assert all(item["fact_type"] == "F3" for item in response["results"])
        assert all(set(item["fields"]) == {"runtime"} for item in response["results"])
        assert all(item["fields"]["runtime"]["basis"]["evidence"] for item in response["results"])
        assert any(
            "manifest-acceptance" in item["fields"]["runtime"]["value"].get("text", "")
            for item in response["results"]
        )
    finally:
        reopened.close()
