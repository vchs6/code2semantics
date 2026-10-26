from pathlib import Path

import pytest

from semantic_facts.source_scanner import build_fact_batch
from semantic_facts.repository.contract import ContractCodec


@pytest.fixture
def codec():
    root = Path(__file__).resolve().parents[1] / "skills" / "layered-semantic-facts" / "assets"
    return ContractCodec(root)


def test_scans_real_python_source_into_valid_fact_batch(tmp_path, codec):
    project = tmp_path / "sample-project"
    project.mkdir()
    (project / "service.py").write_text(
        "import json\n\nclass Service:\n    def execute(self, value):\n        return json.dumps(value)\n",
        encoding="utf-8",
    )
    (project / "broken.txt").write_text("ignored", encoding="utf-8")

    batch = build_fact_batch(project, codec)

    assert len(batch["sources"]) == 1
    assert batch["sources"][0]["dirty"] is True
    assert batch["sources"][0]["has_untracked"] is True
    assert len(batch["facts"]) == 1
    fact = batch["facts"][0]
    assert fact["fact_type"] == "F2"
    assert "class Service" in fact["fields"]["names"]["value"]["text"]
    assert "function execute" in fact["fields"]["names"]["value"]["text"]
    assert fact["fields"]["names"]["basis"]["evidence"][0]["locator"].startswith("service.py:L")
    codec.validate_batch(batch)


def test_scan_excludes_generated_directories_and_is_deterministic(tmp_path, codec):
    project = tmp_path / "sample-project"
    project.mkdir()
    (project / "app.py").write_text("def run():\n    return True\n", encoding="utf-8")
    generated = project / "__pycache__"
    generated.mkdir()
    (generated / "ignored.py").write_text("def ignored():\n    pass\n", encoding="utf-8")

    first = build_fact_batch(project, codec)
    second = build_fact_batch(project, codec)

    assert first == second
    assert len(first["facts"]) == 1


def test_scan_rejects_invalid_python_instead_of_inventing_facts(tmp_path, codec):
    project = tmp_path / "sample-project"
    project.mkdir()
    (project / "bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    try:
        build_fact_batch(project, codec)
    except ValueError as error:
        assert "cannot construct facts for bad.py" in str(error)
    else:
        raise AssertionError("invalid Python must not produce facts")


def test_scan_fails_when_no_supported_language_sources_exist(tmp_path, codec):
    project = tmp_path / "empty-project"
    project.mkdir()
    (project / "readme.md").write_text("No Python files", encoding="utf-8")

    try:
        build_fact_batch(project, codec)
    except ValueError as error:
        assert "no Python or Rust source files" in str(error)
    else:
        raise AssertionError("empty source scope must not silently produce an empty fact batch")

def test_scans_mixed_python_and_rust_project(tmp_path, codec):
    project = tmp_path / "mixed-project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "lib.rs").write_text(
        "pub struct Engine;\npub enum Mode { Fast, Safe }\nimpl Engine { pub fn run() {} }\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text(
        "class Runner:\n    def start(self):\n        return True\n",
        encoding="utf-8",
    )

    batch = build_fact_batch(project, codec)
    assert len(batch["facts"]) == 2
    by_file = {fact["fields"]["identity"]["value"]["ref"]["node_id"]: fact for fact in batch["facts"]}
    names = [fact["fields"]["names"]["value"]["text"] for fact in batch["facts"]]
    assert any("struct Engine" in value and "enum Mode" in value for value in names)
    assert any("class Runner" in value and "function start" in value for value in names)
    assert all(fact["fields"]["names"]["basis"]["evidence"] for fact in batch["facts"])
    assert all(fact["fields"]["names"]["context"]["environment"]["language"] in {"Python", "Rust"} for fact in batch["facts"])

def test_scanner_records_scope_and_file_direct_node_completeness(tmp_path, codec):
    project = tmp_path / "inventory-project"
    project.mkdir()
    (project / "app.py").write_text(
        """class Engine:
    def run(self):
        return True
""",
        encoding="utf-8",
    )

    batch = build_fact_batch(project, codec)
    assert len(batch["direct_nodes"]) == 2
    scope_inventory = next(item for item in batch["direct_nodes"] if item["target"]["kind"] == "scope")
    file_inventory = next(item for item in batch["direct_nodes"] if item["target"]["kind"] == "node")
    assert scope_inventory["assertion"]["coverage"]["completeness"] == "complete"
    assert scope_inventory["children"] == [batch["facts"][0]["node"]]
    assert file_inventory["target"]["node"] == batch["facts"][0]["node"]
    assert len(file_inventory["children"]) >= 3

def test_partial_scan_preserves_valid_files_when_another_file_is_unparseable(tmp_path, codec):
    from semantic_facts.source_scanner import build_fact_batch_with_gaps

    project = tmp_path / "partial-scan-project"
    project.mkdir()
    (project / "valid.py").write_text("class Valid:\n    pass\n", encoding="utf-8")
    (project / "broken.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    result = build_fact_batch_with_gaps(project, codec)
    assert len(result["batch"]["facts"]) == 1
    assert "valid.py" in result["batch"]["facts"][0]["fields"]["locators"]["value"]["text"]
    assert len(result["gaps"]) == 1
    assert result["gaps"][0]["path"] == "broken.py"
    assert result["gaps"][0]["reason"] == "unparseable"
    assert next(item for item in result["batch"]["direct_nodes"] if item["target"]["kind"] == "scope")["assertion"]["coverage"]["completeness"] == "partial"

def test_source_state_changes_when_project_manifest_changes(tmp_path, codec):
    project = tmp_path / "manifest-bound-project"
    project.mkdir()
    (project / "app.py").write_text("def run():\n    return True\n", encoding="utf-8")
    manifest = project / "pyproject.toml"
    manifest.write_text('[project]\nname = "first-name"\nversion = "0.1.0"\n', encoding="utf-8")

    first = build_fact_batch(project, codec)
    manifest.write_text('[project]\nname = "changed-name"\nversion = "0.1.0"\n', encoding="utf-8")
    second = build_fact_batch(project, codec)

    assert first["sources"][0]["content_state"] != second["sources"][0]["content_state"]
    assert first["sources"][0]["source_id"] != second["sources"][0]["source_id"]
