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
