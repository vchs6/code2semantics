import json
from pathlib import Path

import pytest

from semantic_facts.capability_matrix import CapabilityMatrix, MatrixValidationError


def entry(tool_id: str = "cargo.metadata", **overrides: object) -> dict:
    value = {
        "tool_id": tool_id,
        "description": "��ȡ Cargo workspace Ԫ����",
        "information_need_ids": ["project.targets"],
        "output_kinds": ["metadata"],
        "languages": ["rust"],
        "platforms": ["linux"],
        "environment": "cargo-1.85",
        "invocation": ["cargo metadata --format-version 1"],
        "combinations": [],
        "limitations": [],
        "enabled": False,
        "research_basis": ["survey-info-acquisition-tools/research/semantic-tooling-survey.md#3"],
    }
    value.update(overrides)
    return value


def test_validation_errors(tmp_path: Path) -> None:
    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    with pytest.raises(MatrixValidationError) as error:
        matrix.validate({"contract_version": "1.0.0", "entries": [entry(tool_id="bad id")]})
    assert error.value.location == "/entries/0/tool_id"


def test_load(tmp_path: Path) -> None:
    path = tmp_path / "matrix.json"
    path.write_text("{", encoding="utf-8")
    matrix = CapabilityMatrix(path)
    with pytest.raises(MatrixValidationError):
        matrix.load()

    path.write_text(
        json.dumps({"contract_version": "1.0.0", "entries": [entry(), entry()]}),
        encoding="utf-8",
    )
    with pytest.raises(MatrixValidationError) as error:
        matrix.load()
    assert error.value.location == "/entries/1/tool_id"


def test_atomic_replace_and_upsert(tmp_path: Path) -> None:
    path = tmp_path / "matrix.json"
    matrix = CapabilityMatrix(path)
    matrix.replace([entry()])
    original = path.read_bytes()
    with pytest.raises(MatrixValidationError):
        matrix.replace([entry(tool_id="bad id")])
    assert path.read_bytes() == original

    assert matrix.upsert(entry(description="updated")) is True
    assert matrix.load()["entries"][0]["description"] == "updated"
    assert matrix.upsert(entry(description="updated")) is False


def test_idempotent_update_preserves_file_bytes(tmp_path: Path) -> None:
    path = tmp_path / "matrix.json"
    matrix = CapabilityMatrix(path)
    matrix.replace([entry()])
    original = path.read_bytes()
    assert matrix.upsert(entry()) is False
    assert path.read_bytes() == original

