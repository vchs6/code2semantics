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