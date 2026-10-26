from pathlib import Path

import pytest

from semantic_facts.fact_constructor import construct_fact_batch
from semantic_facts.info_parser import ParserRegistry
from semantic_facts.repository.contract import ContractCodec


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "skills" / "layered-semantic-facts" / "assets"


def parsed_file():
    codec = ContractCodec(ASSETS)
    source = {
        "source_id": "src-a",
        "root": "/project",
        "content_state": "sha256:" + "a" * 64,
        "status": "available",
        "dirty": False,
        "has_untracked": False,
        "excludes": [],
    }
    request = {
        "kind": "parse_request",
        "tool_native_output": {
            "encoding": "utf-8",
            "text": "class Engine:\n    def run(self):\n        return 1\n",
        },
        "invocation_profile": {
            "tool_id": "python.ast-source",
            "tool_version": "3.12",
            "command": ["source-parser", "src/engine.py"],
            "environment": {"language": "Python"},
            "sources": [source],
            "coverage": {
                "domain": "Python syntax",
                "checked": ["src/engine.py"],
                "excluded": [],
                "completeness": "complete",
                "method": "AST",
            },
            "evidence": [],
        },
    }
    parsed = ParserRegistry(ASSETS).parse(request)
    return codec, source, parsed


def test_constructor_accepts_only_observations_bound_to_requested_source():
    codec, source, parsed = parsed_file()
    batch = construct_fact_batch(source, "project", [("src/engine.py", parsed)], codec)
    assert batch["facts"]
    assert all(
        evidence["source_id"] == source["source_id"]
        and evidence["content_state"] == source["content_state"]
        for fact in batch["facts"]
        for assertion in fact["fields"].values()
        for evidence in assertion["basis"]["evidence"]
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda observation: observation["subject"].update(source_id="src-other"), "observation source mismatch"),
        (lambda observation: observation["subject"].update(subject_id="other-project"), "observation subject mismatch"),
        (lambda observation: observation["evidence"][0].update(content_state="sha256:" + "b" * 64), "evidence content state mismatch"),
        (lambda observation: observation["evidence"][0].update(locator="other.py:L1-L2"), "evidence locator outside requested file"),
        (lambda observation: observation["evidence"][0].update(source_id="src-other"), "evidence source mismatch"),
    ],
)
def test_constructor_rejects_unbound_observation_or_evidence(mutation, message):
    import copy

    codec, source, parsed = parsed_file()
    tampered = copy.deepcopy(parsed)
    mutation(tampered["observations"][0])
    with pytest.raises(ValueError, match=message):
        construct_fact_batch(source, "project", [("src/engine.py", tampered)], codec)
