from pathlib import Path

from semantic_facts.constructor_plan import plan_constructor_request
from test_information_needs import ASSETS, request


def test_partially_satisfied_request_only_plans_missing_fields():
    value = request(("identity", "names"))
    value["existing_valid_facts"]["facts"] = [{
        "fact_id": "fact-current",
        "node": {"source_id": "source-current", "subject_id": "project", "node_id": "file-a"},
        "fact_type": "F2",
        "granularities": ["L3"],
        "fields": {
            "identity": {
                "origin": "observed",
                "knowledge": "supported",
                "basis": {"evidence": [{"evidence_id": "ev-identity"}]},
                "coverage": {"completeness": "complete"},
                "validity": {"state": "current", "sources": [
                    {"source_id": "source-current", "content_state": "sha256:current"}
                ]},
            }
        },
    }]

    result = plan_constructor_request(value, ASSETS)
    assert [item["need_id"] for item in result["plan"]] == ["syntax.f2.names"]


def test_multiple_fields_are_grouped_by_need_and_sorted():
    result = plan_constructor_request(request(("locators", "names", "identity")), ASSETS)
    assert [item["need_id"] for item in result["plan"]] == [
        "syntax.f2.identity", "syntax.f2.locators", "syntax.f2.names"
    ]
    assert all(item["fields"] == sorted(item["fields"]) for item in result["plan"])


def test_producer_selection_filters_disabled_and_combines_partial_coverage(tmp_path):
    from semantic_facts.capability_matrix import CapabilityMatrix
    from semantic_facts.constructor_plan import select_enabled_producers

    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    base = {
        "description": "accepted source parser",
        "output_kinds": ["source-observation"],
        "languages": ["python"],
        "platforms": ["linux"],
        "environment": "python-3.12",
        "invocation": ["in-process-parser"],
        "combinations": [],
        "limitations": ["syntax inventory only"],
        "enabled": True,
        "acceptance": {"actor": "parser_development", "evidence": ["tests/test_info_parser.py::test_registry_discovers_builtin_parser_and_reports_unknown_profiles"]},
        "research_basis": ["built-in Python AST parser and first-phase acceptance fixture"],
    }
    matrix.replace([
        dict(base, tool_id="tool.identity", information_need_ids=["syntax.f2.identity"]),
        dict(base, tool_id="tool.names", information_need_ids=["syntax.f2.names"]),
        dict(base, tool_id="tool.disabled", information_need_ids=["syntax.f2.boundary"], enabled=False, acceptance=None),
    ])
    selected = select_enabled_producers(
        matrix,
        ["syntax.f2.identity", "syntax.f2.names", "syntax.f2.boundary"],
        "Python",
        "Linux",
        "python-3.12",
    )
    assert [item["tool_id"] for item in selected["syntax.f2.identity"]] == ["tool.identity"]
    assert [item["tool_id"] for item in selected["syntax.f2.names"]] == ["tool.names"]
    assert selected["syntax.f2.boundary"] == []


def test_producer_selection_rejects_environment_mismatch(tmp_path):
    from semantic_facts.capability_matrix import CapabilityMatrix
    from semantic_facts.constructor_plan import select_enabled_producers

    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    matrix.replace([{
        "tool_id": "tool.rust",
        "description": "Rust source producer",
        "information_need_ids": ["syntax.f2.names"],
        "output_kinds": ["source-observation"],
        "languages": ["rust"],
        "platforms": ["linux"],
        "environment": "rust-toolchain-stable",
        "invocation": ["in-process-parser"],
        "combinations": [],
        "limitations": ["syntax inventory only"],
        "enabled": True,
        "acceptance": {"actor": "parser_development", "evidence": ["tests/test_info_parser.py::test_registry_registers_python_and_rust_parsers"]},
        "research_basis": ["Rust declaration parser fixture"],
    }])
    selected = select_enabled_producers(matrix, ["syntax.f2.names"], "Rust", "Linux", "missing-rust-toolchain")
    assert selected["syntax.f2.names"] == []
