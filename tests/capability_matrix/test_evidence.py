from pathlib import Path

import pytest

from semantic_facts.capability_matrix import CapabilityMatrix, MatrixValidationError


def test_research_basis_must_be_non_empty_traceable_strings(tmp_path: Path) -> None:
    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    entry = {
        "tool_id": "tool.evidence",
        "description": "evidence",
        "information_need_ids": ["need.a"],
        "output_kinds": ["metadata"],
        "languages": ["rust"],
        "platforms": ["linux"],
        "environment": "cargo-1.85",
        "invocation": ["tool.evidence"],
        "combinations": [],
        "limitations": [],
        "enabled": False,
        "research_basis": ["survey-info-acquisition-tools/research/semantic-tooling-survey.md#4"],
    }
    matrix.replace([entry])
    for invalid in ([], [""], [1]):
        bad = dict(entry, research_basis=invalid)
        with pytest.raises(MatrixValidationError):
            matrix.replace([bad])

