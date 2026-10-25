from pathlib import Path

import pytest

from semantic_facts.capability_matrix import CapabilityMatrix, MatrixValidationError


def entry(tool_id: str, needs: list[str], **overrides: object) -> dict:
    value = {
        "tool_id": tool_id,
        "description": tool_id,
        "information_need_ids": needs,
        "output_kinds": ["metadata"],
        "languages": ["rust"],
        "platforms": ["linux"],
        "environment": "cargo-1.85",
        "invocation": [tool_id],
        "combinations": [],
        "limitations": [],
        "enabled": False,
        "research_basis": ["survey-info-acquisition-tools/research/semantic-tooling-survey.md#4"],
    }
    value.update(overrides)
    return value


def test_query_requires_all_information_needs_and_returns_all_candidates(tmp_path: Path) -> None:
    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    matrix.replace(
        [
            entry("tool.a", ["need.a", "need.b"]),
            entry("tool.b", ["need.b"]),
            entry("tool.d", ["need.a", "need.b"]),
            entry("tool.c", ["need.a", "need.b"], languages=["python"]),
        ]
    )
    result = matrix.query(["need.a", "need.b"], "rust", "linux", "cargo-1.85")
    assert [item["tool_id"] for item in result] == ["tool.a", "tool.d"]


def test_query_returns_empty_for_no_match_and_rejects_unknown_need(tmp_path: Path) -> None:
    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    matrix.replace([entry("tool.a", ["need.a"])])
    assert matrix.query(["need.a"], "rust", "windows", "cargo-1.85") == []
    with pytest.raises(MatrixValidationError) as error:
        matrix.query(["need.unknown"], "rust", "linux", "cargo-1.85")
    assert error.value.location == "/information_need_ids"


def test_empty_matrix_query_without_needs_returns_empty(tmp_path: Path) -> None:
    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    matrix.replace([])
    assert matrix.query([], "rust", "linux", "cargo-1.85") == []

