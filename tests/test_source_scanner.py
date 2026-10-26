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
    assert len(batch["facts"]) == 1
    fact = batch["facts"][0]
    assert fact["fact_type"] == "F2"
    assert "class:Service" in fact["fields"]["names"]["value"]["text"]
    assert "function:execute" in fact["fields"]["names"]["value"]["text"]
    assert fact["fields"]["names"]["basis"]["evidence"][0]["locator"] == "service.py:file"
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
        assert "cannot parse bad.py" in str(error)
    else:
        raise AssertionError("invalid Python must not produce facts")


def test_scan_fails_when_no_python_sources_exist(tmp_path, codec):
    project = tmp_path / "empty-project"
    project.mkdir()
    (project / "readme.md").write_text("No Python files", encoding="utf-8")

    try:
        build_fact_batch(project, codec)
    except ValueError as error:
        assert "no Python source files" in str(error)
    else:
        raise AssertionError("empty source scope must not silently produce an empty fact batch")
