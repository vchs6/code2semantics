import json
from pathlib import Path

import pytest

from semantic_facts.constructor_plan import plan_constructor_request
from semantic_facts.information_needs import InformationNeedsError, load_information_needs


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "skills" / "layered-semantic-facts" / "assets"


def request(fields=("identity", "names", "boundary", "locators")):
    return {
        "kind": "construct_request",
        "query": {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "request_id": "plan-test",
            "scope": {
                "scope_id": "scope-a",
                "directories": ["/workspace/project"],
                "excludes": [],
                "defaulted": False,
            },
            "target": {"kind": "scope"},
            "granularity": "L3",
            "selections": [{"fact_type": "F2", "fields": list(fields)}],
            "budget": {"max_rounds": 2, "max_new_assertions": 10},
        },
        "existing_valid_facts": {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "sources": [{
                "source_id": "source-current",
                "root": "/workspace/project",
                "content_state": "sha256:current",
                "status": "available",
                "dirty": True,
                "has_untracked": True,
                "excludes": [],
            }],
            "facts": [],
            "navigation": [],
            "direct_nodes": [],
            "conflicts": [],
        },
        "unmet": [],
        "current_source_context": {
            "sources": [{
                "source_id": "source-current",
                "root": "/workspace/project",
                "content_state": "sha256:current",
                "status": "available",
                "dirty": True,
                "has_untracked": True,
                "excludes": [],
            }],
            "changes": [],
            "necessary_ancestors": [],
            "obligations": [],
        },
    }


def test_information_needs_catalogue_is_valid_and_fixed():
    catalogue = load_information_needs(ASSETS)
    assert {need["need_id"] for need in catalogue["needs"]} == {
        "syntax.f2.identity", "syntax.f2.names", "syntax.f2.boundary", "syntax.f2.locators"
    }
    assert all(set(need["languages"]) == {"Python", "Rust"} for need in catalogue["needs"])


def test_plan_is_deterministic_and_covers_supported_f2_fields():
    value = request()
    first = plan_constructor_request(value, ASSETS)
    second = plan_constructor_request(value, ASSETS)
    assert first == second
    assert first["gaps"] == []
    assert [item["need_id"] for item in first["plan"]] == [
        "syntax.f2.boundary", "syntax.f2.identity", "syntax.f2.locators", "syntax.f2.names"
    ]
    assert first["catalogue_mutated"] is False
    assert first["matrix_mutated"] is False


def test_unknown_field_is_an_explicit_gap_not_added_to_catalogue():
    value = request(("purpose",))
    result = plan_constructor_request(value, ASSETS)
    assert result["plan"] == []
    assert result["gaps"][0]["reason"] == "uncovered_need"
    assert result["gaps"][0]["fields"] == ["purpose"]


def test_current_evidence_satisfies_field_but_stale_evidence_does_not():
    value = request(("names",))
    fact = {
        "fact_id": "fact-old",
        "node": {"source_id": "source-current", "subject_id": "project", "node_id": "file-a"},
        "fact_type": "F2",
        "granularities": ["L3"],
        "fields": {
            "names": {
                "origin": "observed",
                "knowledge": "supported",
                "context": {
                    "source_ids": ["source-current"],
                    "conditions": [],
                    "environment": {"language": "Python"},
                    "language_semantics": ["syntax inventory"],
                },
                "coverage": {
                    "domain": "Python syntax in service.py",
                    "checked": ["service.py"],
                    "excluded": [],
                    "completeness": "complete",
                    "method": "Python AST",
                },
                "basis": {
                    "evidence": [{
                        "evidence_id": "ev-a",
                        "source_id": "source-current",
                        "content_state": "sha256:current",
                        "kind": "source",
                        "locator": "service.py:L1-L2",
                        "content_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                        "relation": "supports",
                    }],
                    "premises": [],
                    "method": "Python AST",
                    "limitations": [],
                },
                "value": {"kind": "text", "text": "class Example"},
                "validity": {"state": "current", "sources": [
                    {"source_id": "source-current", "content_state": "sha256:current"}
                ]},
            }
        },
    }
    value["existing_valid_facts"]["facts"] = [fact]
    assert plan_constructor_request(value, ASSETS)["plan"] == []

    fact["fields"]["names"]["validity"]["sources"][0]["content_state"] = "sha256:old"
    stale = plan_constructor_request(value, ASSETS)
    assert stale["plan"][0]["need_id"] == "syntax.f2.names"


def test_loader_rejects_duplicate_need_ids(tmp_path):
    import shutil

    for filename in ("information-needs.schema.json", "information-needs.json", "fact-catalog.json"):
        shutil.copy(ASSETS / filename, tmp_path / filename)
    path = tmp_path / "information-needs.json"
    catalogue = json.loads(path.read_text(encoding="utf-8"))
    catalogue["needs"].append(dict(catalogue["needs"][0]))
    path.write_text(json.dumps(catalogue), encoding="utf-8")
    with pytest.raises(InformationNeedsError, match="duplicate need_id"):
        load_information_needs(tmp_path)
