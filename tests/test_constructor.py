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

def test_constructor_wires_allowlisted_external_producer_through_parser(tmp_path):
    import json
    import shutil
    import sys

    from semantic_facts.tool_executor import SubprocessToolExecutor

    project = tmp_path / "external-producer-project"
    project.mkdir()
    (project / "service.py").write_text(
        "class ExternalService:\\n    def run(self):\\n        return True\\n",
        encoding="utf-8",
    )
    assets = tmp_path / "assets"
    shutil.copytree(ASSETS, assets)
    matrix_path = assets / "capability-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    python_entry = next(entry for entry in matrix["entries"] if entry["tool_id"] == "python.ast-source")
    python_entry["environment"] = "subprocess"
    python_entry["invocation"] = ["subprocess", "ParserRegistry.parse(ParseRequest)"]
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\\n", encoding="utf-8")

    executor = SubprocessToolExecutor({
        "python.ast-source": [
            sys.executable, "-c",
            "import pathlib,sys; sys.stdout.write(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))",
        ],
    })
    request_value = _request_for_project(project)
    result = execute_constructor_request(request_value, assets, external_executor=executor)

    assert result["gaps"] == []
    assert any(
        "class ExternalService" in fact["fields"]["names"]["value"]["text"]
        for fact in result["batch"]["facts"]
    )
    assert result["batch"]["facts"][0]["fields"]["names"]["basis"]["evidence"]
