from __future__ import annotations

import json
import shutil

import pytest

from semantic_facts.constructor import execute_constructor_request
from semantic_facts.repository.contract import ContractCodec
from semantic_facts.source_scanner import build_fact_batch
from semantic_facts.tool_executor import ExecutionResult, SubprocessToolExecutor
from test_information_needs import ASSETS, request


def _case(tmp_path):
    project = tmp_path / "rust-project"
    (project / "src").mkdir(parents=True)
    manifest = project / "Cargo.toml"
    manifest.write_text(
        '[package]\nname = "failure-fixture"\nversion = "0.1.0"\nedition = "2021"\n'
        '[dependencies]\nserde = "1"\n',
        encoding="utf-8",
    )
    (project / "src" / "lib.rs").write_text("pub fn run() {}\n", encoding="utf-8")
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

    source = build_fact_batch(project, ContractCodec(ASSETS))["sources"][0]
    value = request(("identity", "names"))
    value["query"]["scope"]["directories"] = [str(project.resolve())]
    value["query"]["selections"] = [
        {"fact_type": "F4", "fields": ["kind"]},
        {"fact_type": "F6", "fields": ["kind"]},
    ]
    value["existing_valid_facts"]["sources"] = [source]
    value["current_source_context"]["sources"] = [source]
    return project, manifest, assets, value


@pytest.mark.parametrize(
    ("failure_mode", "expected_reason"),
    [
        ("missing", "unavailable_tool"),
        ("timeout", "unavailable_tool"),
        ("nonzero", "unavailable_tool"),
        ("malformed", "unparseable"),
    ],
)
def test_subprocess_failure_modes_return_explicit_gaps_without_fabricated_facts(
    tmp_path, failure_mode, expected_reason
):
    project, manifest, assets, value = _case(tmp_path)

    if failure_mode == "missing":
        executor = SubprocessToolExecutor({
            "rust.cargo-metadata": [str(tmp_path / "missing-cargo"), "metadata", "--no-deps", "--format-version", "1"],
        })
    else:
        class StubExecutor:
            def execute(self, tool_id, args, *, cwd, timeout_seconds):
                if failure_mode == "timeout":
                    return ExecutionResult(tool_id, tuple(args), str(cwd), None, "", "timeout", True)
                if failure_mode == "nonzero":
                    return ExecutionResult(tool_id, tuple(args), str(cwd), 2, "", "fixture failure", False)
                return ExecutionResult(tool_id, tuple(args), str(cwd), 0, "{ malformed", "", False)
        executor = StubExecutor()

    result = execute_constructor_request(value, assets, external_executor=executor)
    assert not any(fact["fact_type"] in {"F4", "F6"} for fact in result["batch"]["facts"])
    assert any(gap["reason"] == expected_reason for gap in result["gaps"])


def test_source_mutation_during_cargo_execution_discards_manifest_facts(tmp_path):
    project, manifest, assets, value = _case(tmp_path)
    delegate = SubprocessToolExecutor({
        "rust.cargo-metadata": ["cargo", "metadata", "--no-deps", "--format-version", "1"],
    })

    class MutatingExecutor:
        def execute(self, tool_id, args, *, cwd, timeout_seconds):
            result = delegate.execute(tool_id, args, cwd=cwd, timeout_seconds=timeout_seconds)
            manifest.write_text(
                '[package]\nname = "changed-after-run"\nversion = "0.1.0"\nedition = "2021"\n',
                encoding="utf-8",
            )
            return result

    result = execute_constructor_request(value, assets, external_executor=MutatingExecutor())
    assert not any(fact["fact_type"] in {"F4", "F6"} for fact in result["batch"]["facts"])
    assert any(gap["reason"] == "source_modified" for gap in result["gaps"])
