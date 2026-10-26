"""Deterministic constructor from validated parser observations to FactBatch."""
from __future__ import annotations

import hashlib
from typing import Any

from .repository.contract import ContractCodec


def construct_fact_batch(
    source: dict[str, Any],
    subject_id: str,
    parsed_files: list[tuple[str, dict[str, Any]]],
    codec: ContractCodec,
) -> dict[str, Any]:
    """Convert parser observations into observed F2 facts without inventing semantics."""
    source_id = source["source_id"]
    content_state = source["content_state"]
    facts: list[dict[str, Any]] = []

    for relative, parsed in parsed_files:
        if parsed.get("kind") != "parse_result":
            raise ValueError(f"invalid parser result for {relative}: kind must be parse_result")
        if parsed.get("gaps"):
            raise ValueError(f"cannot construct facts for {relative}: {parsed['gaps'][0]['detail']}")
        observations = parsed.get("observations", [])
        if not observations:
            raise ValueError(f"parser produced no file-level observation for {relative}")

        names = [item["payload"]["text"] for item in observations]
        evidence_by_id = {
            item["evidence_id"]: item
            for observation in observations
            for item in observation["evidence"]
        }
        evidence_items = [evidence_by_id[key] for key in sorted(evidence_by_id)]
        if not evidence_items:
            raise ValueError(f"parser produced no source evidence for {relative}")

        node_id = "file-" + hashlib.sha256(relative.encode("utf-8")).hexdigest()[:20]
        fact_id = "fact-" + hashlib.sha256((relative + "\\0F2").encode("utf-8")).hexdigest()[:20]
        context = {
            "source_ids": [source_id],
            "conditions": [],
            "environment": {"language": "Python"},
            "language_semantics": ["Python syntax inventory; runtime behavior not inferred"],
        }
        coverage = {
            "domain": f"Python syntax in {relative}",
            "checked": [relative],
            "excluded": [],
            "completeness": "complete",
            "method": "Python ast.parse via info_parser",
        }

        def assertion(value: dict[str, Any]) -> dict[str, Any]:
            return {
                "origin": "observed",
                "knowledge": "supported",
                "context": context,
                "coverage": coverage,
                "basis": {
                    "evidence": evidence_items,
                    "premises": [],
                    "method": "deterministic Python AST parser",
                    "limitations": ["Does not infer runtime behavior or intent"],
                },
                "value": value,
                "validity": {"state": "current", "sources": [{"source_id": source_id, "content_state": content_state}]},
            }

        facts.append({
            "fact_id": fact_id,
            "node": {"source_id": source_id, "subject_id": subject_id, "node_id": node_id},
            "fact_type": "F2",
            "granularities": ["L3"],
            "fields": {
                "identity": assertion({"kind": "reference", "ref": {
                    "source_id": source_id, "subject_id": subject_id, "node_id": node_id,
                }}),
                "names": assertion({"kind": "text", "text": "; ".join(names)}),
                "boundary": assertion({"kind": "text", "text": "Observed syntax is limited to this file; runtime behavior is not inferred."}),
                "locators": assertion({"kind": "text", "text": "; ".join(item["locator"] for item in evidence_items)}),
            },
        })

    batch = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "sources": [source],
        "facts": facts,
        "navigation": [],
        "direct_nodes": [],
        "conflicts": [],
    }
    codec.validate_batch(batch)
    return batch
