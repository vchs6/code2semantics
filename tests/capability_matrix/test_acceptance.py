from pathlib import Path

import pytest

from semantic_facts.capability_matrix import CapabilityMatrix, MatrixValidationError


def entry(**overrides: object) -> dict:
    value = {
        "tool_id": "tool.accepted",
        "description": "����ɿ������յĹ���",
        "information_need_ids": ["need.a"],
        "output_kinds": ["metadata"],
        "languages": ["rust"],
        "platforms": ["linux"],
        "environment": "cargo-1.85",
        "invocation": ["tool.accepted"],
        "combinations": [],
        "limitations": [],
        "enabled": True,
        "acceptance": {"actor": "parser_development", "evidence": ["tests/acceptance.log"]},
        "research_basis": ["survey-info-acquisition-tools/research/semantic-tooling-survey.md#5"],
    }
    value.update(overrides)
    return value


def test_enabled_requires_parser_development_acceptance(tmp_path: Path) -> None:
    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    matrix.replace([entry()])
    assert matrix.load()["entries"][0]["enabled"] is True

    with pytest.raises(MatrixValidationError):
        matrix.replace([entry(acceptance={"actor": "runtime", "evidence": ["run.log"]})])
    with pytest.raises(MatrixValidationError):
        matrix.replace([entry(acceptance={"actor": "parser_development", "evidence": []})])
    with pytest.raises(MatrixValidationError):
        matrix.replace([entry(enabled=False)])


def test_runtime_state_is_rejected_and_does_not_change_matrix(tmp_path: Path) -> None:
    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    matrix.replace([entry()])
    before = matrix.load()
    with pytest.raises(MatrixValidationError):
        matrix.replace([entry(execution_status="success")])
    assert matrix.load() == before

