import copy
from pathlib import Path

from semantic_facts.constructor import execute_constructor_request
from semantic_facts.repository.contract import ContractCodec
from semantic_facts.source_scanner import build_fact_batch
from test_information_needs import ASSETS, request


def _request_for_project(project: Path, fields=("identity", "names")):
    codec = ContractCodec(ASSETS)
    source_batch = build_fact_batch(project, codec)
    value = request(fields)
    value["query"]["scope"]["directories"] = [str(project.resolve())]
    value["existing_valid_facts"]["sources"] = source_batch["sources"]
    value["current_source_context"]["sources"] = source_batch["sources"]
    return value


def test_constructor_runs_current_source_to_schema_valid_fact_batch_without_persistence(tmp_path):
    project = tmp_path / "constructor-project"
    project.mkdir()
    (project / "service.py").write_text(
        "class Engine:\n    def run(self):\n        return 1\n",
        encoding="utf-8",
    )
    value = _request_for_project(project)

    result = execute_constructor_request(value, ASSETS)

    assert result["kind"] == "construct_result"
    assert result["gaps"] == []
    assert result["batch"]["facts"]
    assert set(result["batch"]["facts"][0]["fields"]) == {"identity", "names"}
    assert result["batch"]["facts"][0]["fields"]["names"]["basis"]["evidence"]
    assert not (tmp_path / "facts.db").exists()


def test_constructor_returns_explicit_gap_for_need_outside_fixed_catalogue(tmp_path):
    project = tmp_path / "constructor-project"
    project.mkdir()
    (project / "service.py").write_text("class Engine:\n    pass\n", encoding="utf-8")
    value = _request_for_project(project, ("purpose",))

    result = execute_constructor_request(value, ASSETS)

    assert result["batch"]["facts"] == []
    assert result["gaps"][0]["reason"] == "uncovered_need"
    assert result["gaps"][0]["fields"] == ["purpose"]


def test_constructor_detects_source_changed_during_construction(tmp_path):
    project = tmp_path / "constructor-project"
    project.mkdir()
    source = project / "service.py"
    source.write_text("class Engine:\n    pass\n", encoding="utf-8")
    value = _request_for_project(project)
    source.write_text("class ChangedEngine:\n    pass\n", encoding="utf-8")

    result = execute_constructor_request(value, ASSETS)

    assert result["batch"]["facts"] == []
    assert any(gap["reason"] == "source_modified" for gap in result["gaps"])

def test_constructor_supports_rust_source_with_syntax_only_evidence(tmp_path):
    project = tmp_path / "rust-constructor-project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "lib.rs").write_text(
        "pub struct Engine;\npub enum Mode { Fast, Safe }\n\nimpl Engine {\n    pub fn run() {}\n}\n",
        encoding="utf-8",
    )
    value = _request_for_project(project)

    result = execute_constructor_request(value, ASSETS)

    assert result["gaps"] == []
    assert result["batch"]["facts"]
    names = result["batch"]["facts"][0]["fields"]["names"]["value"]["text"]
    assert "struct Engine" in names
    assert "enum Mode" in names
    assertion = result["batch"]["facts"][0]["fields"]["names"]
    assert assertion["context"]["environment"]["language"] == "Rust"
    assert any("No type checking" in limitation or "type checking" in limitation for limitation in assertion["basis"]["limitations"])
def test_constructor_preserves_valid_file_when_another_producer_fails(tmp_path):
    from semantic_facts.source_scanner import inspect_source

    project = tmp_path / "mixed-validity-project"
    project.mkdir()
    (project / "valid.py").write_text("class ValidEngine:\n    pass\n", encoding="utf-8")
    (project / "broken.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
    value = request()
    value["query"]["scope"]["directories"] = [str(project.resolve())]
    source = inspect_source(project)
    value["existing_valid_facts"]["sources"] = [source]
    value["current_source_context"]["sources"] = [source]

    result = execute_constructor_request(value, ASSETS)

    assert any("class ValidEngine" in fact["fields"]["names"]["value"]["text"] for fact in result["batch"]["facts"])
    assert any(gap["reason"] == "unparseable" and "broken.py" in gap["detail"] for gap in result["gaps"])
    scope_inventory = next(item for item in result["batch"]["direct_nodes"] if item["target"]["kind"] == "scope")
    assert scope_inventory["assertion"]["coverage"]["completeness"] == "partial"

def test_constructor_runs_accepted_manifest_profile_and_preserves_manifest_observations(tmp_path):
    import json
    import shutil
    import sys

    from semantic_facts.tool_executor import SubprocessToolExecutor

    project = tmp_path / "manifest-project"
    (project / "src").mkdir(parents=True)
    (project / "Cargo.toml").write_text(
        '[package]\nname = "manifest-app"\nversion = "0.1.0"\nedition = "2021"\n'
        '[dependencies]\nserde = "1"\n',
        encoding="utf-8",
    )
    (project / "src" / "lib.rs").write_text("pub fn run() {}\n", encoding="utf-8")

    assets = tmp_path / "assets"
    shutil.copytree(ASSETS, assets)
    matrix_path = assets / "capability-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    candidate = next(entry for entry in matrix["entries"] if entry["tool_id"] == "rust.cargo-metadata")
    candidate["enabled"] = True
    candidate["acceptance"] = {
        "actor": "parser_development",
        "evidence": ["tests/test_info_parser.py::test_cargo_metadata_parser_emits_workspace_and_dependency_observations_separately"],
    }
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    request_value = _request_for_project(project, fields=("identity", "names"))
    request_value["query"]["selections"] = [
        {"fact_type": "F2", "fields": ["identity", "names"]},
        {"fact_type": "F4", "fields": ["kind"]},
        {"fact_type": "F6", "fields": ["kind"]},
    ]
    class CountingExecutor:
        def __init__(self):
            self.delegate = SubprocessToolExecutor({
                "rust.cargo-metadata": ["cargo", "metadata", "--no-deps", "--format-version", "1"],
            })
            self.calls = []

        def execute(self, tool_id, args, *, cwd, timeout_seconds):
            self.calls.append((tool_id, tuple(args), str(cwd)))
            return self.delegate.execute(
                tool_id, args, cwd=cwd, timeout_seconds=timeout_seconds
            )

    executor = CountingExecutor()
    result = execute_constructor_request(request_value, assets, external_executor=executor)

    # The same producer covers F4.kind and F6.kind in this single request;
    # it must execute once and its output must fan out to both needs.
    assert len(executor.calls) == 1, executor.calls
    assert executor.calls[0][0] == "rust.cargo-metadata"

    assert any(fact["fact_type"] == "F2" for fact in result["batch"]["facts"])
    assert any(fact["fact_type"] == "F4" for fact in result["batch"]["facts"])
    assert any(fact["fact_type"] == "F6" for fact in result["batch"]["facts"])
    assert any(
        "workspace member" in assertion["value"].get("text", "")
        for fact in result["batch"]["facts"]
        for assertion in fact["fields"].values()
    )
    assert any(
        "dependency" in assertion["value"].get("text", "")
        for fact in result["batch"]["facts"]
        for assertion in fact["fields"].values()
    )
    assert all(assertion["basis"]["evidence"] for fact in result["batch"]["facts"] for assertion in fact["fields"].values())

def test_constructor_manifest_facts_survive_repository_reopen_and_minimal_query(tmp_path):
    import json
    import shutil

    from semantic_facts.query_engine import execute_query
    from semantic_facts.repository.store import Repository
    from semantic_facts.tool_executor import SubprocessToolExecutor

    project = tmp_path / "manifest-persist-project"
    (project / "src").mkdir(parents=True)
    (project / "Cargo.toml").write_text(
        '[package]\nname = "manifest-persist"\nversion = "0.1.0"\nedition = "2021"\n',
        encoding="utf-8",
    )
    (project / "src" / "lib.rs").write_text("pub fn run() {}\n", encoding="utf-8")
    assets = tmp_path / "assets"
    shutil.copytree(ASSETS, assets)
    matrix_path = assets / "capability-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    candidate = next(entry for entry in matrix["entries"] if entry["tool_id"] == "rust.cargo-metadata")
    candidate["enabled"] = True
    candidate["acceptance"] = {
        "actor": "parser_development",
        "evidence": ["tests/test_info_parser.py::test_cargo_metadata_parser_emits_workspace_and_dependency_observations_separately"],
    }
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    request_value = _request_for_project(project)
    request_value["query"]["selections"] = [
        {"fact_type": "F2", "fields": ["identity", "names"]},
        {"fact_type": "F4", "fields": ["kind"]},
    ]
    executor = SubprocessToolExecutor({
        "rust.cargo-metadata": ["cargo", "metadata", "--no-deps", "--format-version", "1"],
    })
    constructed = execute_constructor_request(request_value, assets, external_executor=executor)
    assert any(fact["fact_type"] == "F4" for fact in constructed["batch"]["facts"])

    database = tmp_path / "manifest-facts.db"
    repository = Repository(database, assets)
    repository.write(constructed["batch"], "manifest-integration-write")
    repository.close()

    reopened = Repository(database, assets)
    try:
        query = {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "request_id": "manifest-reopen-minimal-query",
            "scope": {
                "scope_id": "manifest-reopen-scope",
                "directories": [str(project.resolve())],
                "excludes": [],
                "defaulted": False,
            },
            "target": {"kind": "scope"},
            "granularity": "L2",
            "selections": [{"fact_type": "F4", "fields": ["kind"]}],
            "budget": {"max_rounds": 1, "max_new_assertions": 10},
        }
        response = execute_query(query, reopened, assets)
        assert response["termination"] == "satisfied", response
        assert response["results"]
        assert all(set(fact["fields"]) == {"kind"} for fact in response["results"])
        assert all(fact["fact_type"] == "F4" for fact in response["results"])
        assert all(fact["fields"]["kind"]["basis"]["evidence"] for fact in response["results"])
    finally:
        reopened.close()

def test_constructor_discards_manifest_observations_if_source_changes_during_tool_execution(tmp_path):
    import json
    import shutil

    from semantic_facts.tool_executor import SubprocessToolExecutor

    project = tmp_path / "manifest-mutates-during-tool"
    (project / "src").mkdir(parents=True)
    manifest = project / "Cargo.toml"
    manifest.write_text('[package]\nname = "before"\nversion = "0.1.0"\nedition = "2021"\n', encoding="utf-8")
    (project / "src" / "lib.rs").write_text("pub fn run() {}\n", encoding="utf-8")
    assets = tmp_path / "assets"
    shutil.copytree(ASSETS, assets)
    matrix_path = assets / "capability-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    candidate = next(entry for entry in matrix["entries"] if entry["tool_id"] == "rust.cargo-metadata")
    candidate["enabled"] = True
    candidate["acceptance"] = {
        "actor": "parser_development",
        "evidence": ["tests/test_info_parser.py::test_cargo_metadata_parser_emits_workspace_and_dependency_observations_separately"],
    }
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    request_value = _request_for_project(project)
    request_value["query"]["selections"] = [
        {"fact_type": "F2", "fields": ["identity", "names"]},
        {"fact_type": "F4", "fields": ["kind"]},
    ]

    class MutatingExecutor:
        def __init__(self):
            self.delegate = SubprocessToolExecutor({
                "rust.cargo-metadata": ["cargo", "metadata", "--no-deps", "--format-version", "1"],
            })

        def execute(self, tool_id, args, *, cwd, timeout_seconds):
            result = self.delegate.execute(tool_id, args, cwd=cwd, timeout_seconds=timeout_seconds)
            manifest.write_text(
                '[package]\nname = "after"\nversion = "0.1.0"\nedition = "2021"\n',
                encoding="utf-8",
            )
            return result

    result = execute_constructor_request(request_value, assets, external_executor=MutatingExecutor())

    assert not any(fact["fact_type"] == "F4" for fact in result["batch"]["facts"])
    assert any(gap["reason"] == "source_modified" for gap in result["gaps"])

def test_constructor_reports_gap_when_subprocess_profile_is_accepted_but_executor_missing(tmp_path):
    import json
    import shutil

    project = tmp_path / "manifest-no-executor"
    (project / "src").mkdir(parents=True)
    (project / "Cargo.toml").write_text(
        '[package]\nname = "manifest-no-executor"\nversion = "0.1.0"\nedition = "2021"\n',
        encoding="utf-8",
    )
    (project / "src" / "lib.rs").write_text("pub fn run() {}\n", encoding="utf-8")
    assets = tmp_path / "assets"
    shutil.copytree(ASSETS, assets)
    matrix_path = assets / "capability-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    candidate = next(entry for entry in matrix["entries"] if entry["tool_id"] == "rust.cargo-metadata")
    candidate["enabled"] = True
    candidate["acceptance"] = {
        "actor": "parser_development",
        "evidence": ["tests/test_info_parser.py::test_cargo_metadata_parser_emits_workspace_and_dependency_observations_separately"],
    }
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    value = _request_for_project(project)
    value["query"]["selections"] = [
        {"fact_type": "F2", "fields": ["identity", "names"]},
        {"fact_type": "F4", "fields": ["kind"]},
    ]

    result = execute_constructor_request(value, assets)

    assert not any(fact["fact_type"] == "F4" for fact in result["batch"]["facts"])
    assert any(gap["reason"] == "unavailable_tool" and "executor" in gap["detail"].lower() for gap in result["gaps"])

def test_constructor_consumes_accepted_pyproject_profile_into_runtime_and_dependency_facts(tmp_path):
    import json
    import shutil

    project = tmp_path / "pyproject-consumer"
    project.mkdir()
    (project / "app.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        '[project]\nname = "pyproject-consumer"\nversion = "1.0"\n'
        'dependencies = ["requests>=2"]\n',
        encoding="utf-8",
    )
    assets = tmp_path / "assets"
    shutil.copytree(ASSETS, assets)
    matrix_path = assets / "capability-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    candidate = next(entry for entry in matrix["entries"] if entry["tool_id"] == "python.pyproject-toml")
    candidate["enabled"] = True
    candidate["acceptance"] = {
        "actor": "parser_development",
        "evidence": ["tests/test_info_parser.py::test_pyproject_toml_parser_emits_manifest_and_script_observations"],
    }
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    value = _request_for_project(project)
    value["query"]["selections"] = [
        {"fact_type": "F2", "fields": ["identity", "names"]},
        {"fact_type": "F3", "fields": ["runtime"]},
        {"fact_type": "F6", "fields": ["kind"]},
    ]

    result = execute_constructor_request(value, assets)

    assert any(fact["fact_type"] == "F3" for fact in result["batch"]["facts"])
    assert any(fact["fact_type"] == "F6" for fact in result["batch"]["facts"])
    assert any(
        "pyproject-consumer" in assertion["value"].get("text", "")
        for fact in result["batch"]["facts"] if fact["fact_type"] == "F3"
        for assertion in fact["fields"].values()
    )
    assert any(
        "requests>=2" in assertion["value"].get("text", "")
        for fact in result["batch"]["facts"] if fact["fact_type"] == "F6"
        for assertion in fact["fields"].values()
    )
