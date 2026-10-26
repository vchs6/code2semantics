import copy
from pathlib import Path

from semantic_facts.induction import build_induction_requests, validate_induction_result
from semantic_facts.repository.contract import ContractCodec
from semantic_facts.source_scanner import build_fact_batch

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "skills" / "layered-semantic-facts" / "assets"


def fixture(tmp_path):
    project = tmp_path / "induction-project"
    project.mkdir()
    (project / "service.py").write_text("class Engine:\n    def run(self):\n        return 1\n", encoding="utf-8")
    batch = build_fact_batch(project, ContractCodec(ASSETS))
    fact = batch["facts"][0]
    assertion = fact["fields"]["names"]
    evidence = assertion["basis"]["evidence"][0]
    observation = {
        "observation_id": "observation-current",
        "subject": fact["node"],
        "information_need_id": "python.syntax_inventory",
        "payload": {"kind": "text", "text": assertion["value"]["text"]},
        "evidence": [evidence],
        "context": assertion["context"],
        "coverage": assertion["coverage"],
    }
    gap = {
        "fact_type": "F2",
        "fields": ["roles"],
        "target": {"kind": "scope"},
        "reason": "insufficient_evidence",
        "detail": "Role classification needs constrained induction.",
        "context": assertion["context"],
        "coverage": assertion["coverage"],
    }
    return batch, observation, gap


def test_induction_groups_fields_by_subject_source_state_and_context(tmp_path):
    batch, observation, gap = fixture(tmp_path)
    second_gap = dict(gap, fields=["boundary"], detail="Boundary needs constrained induction.")
    first = build_induction_requests([observation], batch, [gap, second_gap], ASSETS)
    second = build_induction_requests([observation], batch, [gap, second_gap], ASSETS)

    assert first == second
    assert len(first["requests"]) == 1
    request = first["requests"][0]
    assert request["group"]["fields"] == ["boundary", "roles"]
    assert request["group"]["subject"] == observation["subject"]
    assert request["group"]["content_states"] == [{
        "source_id": observation["evidence"][0]["source_id"],
        "content_state": observation["evidence"][0]["content_state"],
    }]


def test_induction_does_not_create_request_without_current_observation_evidence(tmp_path):
    batch, observation, gap = fixture(tmp_path)
    result = build_induction_requests([], batch, [gap], ASSETS)
    assert result["requests"] == []
    assert result["gaps"][0]["reason"] == "insufficient_evidence"


def test_no_provider_result_returns_explicit_gap_without_inventing_facts(tmp_path):
    batch, observation, gap = fixture(tmp_path)
    request = build_induction_requests([observation], batch, [gap], ASSETS)["requests"][0]
    result = validate_induction_result(request, None, ASSETS)
    assert result["kind"] == "induction_result"
    assert result["batch"]["facts"] == []
    assert result["gaps"][0]["reason"] == "constructor_unavailable"


def test_induction_accepts_only_request_bound_observed_evidence(tmp_path):
    batch, observation, gap = fixture(tmp_path)
    request = build_induction_requests([observation], batch, [gap], ASSETS)["requests"][0]
    proposed = copy.deepcopy(batch)
    fact = proposed["facts"][0]
    names = fact["fields"]["names"]
    fact["fields"] = {
        "roles": {
            "origin": "derived",
            "knowledge": "supported",
            "context": names["context"],
            "coverage": names["coverage"],
            "basis": {
                "evidence": [observation["evidence"][0]],
                "premises": [],
                "method": "constrained induction from current syntax evidence",
                "limitations": ["Role is an interpretation, not a parser observation."],
            },
            "value": {"kind": "text", "text": "Python class exposing a run method"},
            "validity": {
                "state": "current",
                "sources": [{
                    "source_id": observation["evidence"][0]["source_id"],
                    "content_state": observation["evidence"][0]["content_state"],
                }],
            },
        }
    }

    result = validate_induction_result(request, proposed, ASSETS)
    assert result["batch"]["facts"][0]["fields"]["roles"]["value"]["text"] == "Python class exposing a run method"
    assert result["gaps"] == []


def test_conflicting_induction_cannot_replace_existing_fact(tmp_path):
    batch, observation, gap = fixture(tmp_path)
    conflict_gap = dict(gap, fields=["names"], detail="Existing names field is insufficient.")
    request = build_induction_requests([observation], batch, [conflict_gap], ASSETS)["requests"][0]
    proposed = copy.deepcopy(batch)
    fact = proposed["facts"][0]
    assertion = copy.deepcopy(fact["fields"]["names"])
    assertion["value"] = {"kind": "text", "text": "conflicting invented name"}
    fact["fields"] = {"names": assertion}

    result = validate_induction_result(request, proposed, ASSETS)
    assert result["batch"]["facts"] == []
    assert any(gap["reason"] == "conflict" for gap in result["gaps"])
    assert batch["facts"][0]["fields"]["names"]["value"]["text"] != "conflicting invented name"
