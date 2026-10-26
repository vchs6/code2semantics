from __future__ import annotations
import copy
from semantic_facts.constructor import _merge_request_fact_contributions
from semantic_facts.repository.contract import ContractCodec
from semantic_facts.source_scanner import build_fact_batch
from test_information_needs import ASSETS

def _sample_fact(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("class Engine:\n    pass\n", encoding="utf-8")
    batch = build_fact_batch(project, ContractCodec(ASSETS))
    return copy.deepcopy(batch["facts"][0])

def test_same_assertion_merges_distinct_evidence(tmp_path):
    fact = _sample_fact(tmp_path)
    field = next(iter(fact["fields"]))
    assertion = fact["fields"][field]
    duplicate = copy.deepcopy(fact)
    extra = copy.deepcopy(assertion["basis"]["evidence"][0])
    extra.update({"evidence_id":"independent-tool-evidence","locator":"tool-output:independent","content_digest":"sha256:" + "c"*64})
    duplicate["fields"][field]["basis"]["evidence"] = [extra]
    gaps = []
    merged = _merge_request_fact_contributions([fact, duplicate], gaps=gaps, target={"kind":"scope"}, context=assertion["context"], coverage=assertion["coverage"])
    assert not gaps and len(merged) == 1
    ids = {item["evidence_id"] for item in merged[0]["fields"][field]["basis"]["evidence"]}
    assert assertion["basis"]["evidence"][0]["evidence_id"] in ids
    assert "independent-tool-evidence" in ids

def test_conflicting_assertion_is_gap_not_arbitrary_winner(tmp_path):
    fact = _sample_fact(tmp_path)
    field = next(iter(fact["fields"]))
    assertion = fact["fields"][field]
    conflicting = copy.deepcopy(fact)
    conflicting["fields"][field]["value"] = {"kind":"text","text":"conflicting producer value"}
    gaps = []
    merged = _merge_request_fact_contributions([fact, conflicting], gaps=gaps, target={"kind":"scope"}, context=assertion["context"], coverage=assertion["coverage"])
    assert len(merged) == 1 and field not in merged[0]["fields"]
    assert len(gaps) == 1 and gaps[0]["reason"] == "conflict"
