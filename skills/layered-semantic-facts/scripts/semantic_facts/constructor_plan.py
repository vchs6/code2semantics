"""Deterministic constructor request planning over the fixed information-needs catalogue."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .information_needs import load_information_needs


def _supported_current_assertion(assertion: Any, current_states: dict[str, str]) -> bool:
    if not isinstance(assertion, dict) or assertion.get("knowledge") != "supported":
        return False
    basis = assertion.get("basis", {})
    if not basis.get("evidence"):
        return False
    coverage = assertion.get("coverage", {})
    if coverage.get("completeness") != "complete":
        return False
    validity = assertion.get("validity", {})
    if validity.get("state") != "current":
        return False
    states = validity.get("sources", [])
    return bool(states) and all(
        item.get("source_id") in current_states
        and item.get("content_state") == current_states[item.get("source_id")]
        for item in states
    )


def plan_constructor_request(
    request: dict[str, Any],
    asset_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return a stable need plan and explicit gaps; never mutate assets or matrix."""
    catalogue = load_information_needs(asset_root)
    query = request["query"]
    existing = request["existing_valid_facts"]
    current = request["current_source_context"]
    current_states = {source["source_id"]: source["content_state"] for source in current["sources"]}
    facts_by_type: dict[str, list[dict[str, Any]]] = {}
    for fact in existing.get("facts", []):
        facts_by_type.setdefault(fact["fact_type"], []).append(fact)

    needs_index = {
        (need["fact_type"], field): need
        for need in catalogue["needs"]
        for field in need["fields"]
    }
    planned: dict[str, dict[str, Any]] = {}
    gaps: list[dict[str, Any]] = []

    for selection in query["selections"]:
        fact_type = selection["fact_type"]
        for field in selection["fields"]:
            matching_facts = facts_by_type.get(fact_type, [])
            already_satisfied = any(
                field in fact.get("fields", {})
                and _supported_current_assertion(fact["fields"][field], current_states)
                for fact in matching_facts
                if fact.get("node", {}).get("source_id") in current_states
            )
            if already_satisfied:
                continue

            need = needs_index.get((fact_type, field))
            if need is None:
                gaps.append({
                    "fact_type": fact_type,
                    "fields": [field],
                    "target": query["target"],
                    "reason": "uncovered_need",
                    "detail": f"No fixed development-time information need covers {fact_type}.{field}.",
                    "need_id": None,
                })
                continue

            key = need["need_id"]
            item = planned.setdefault(key, {
                "need_id": key,
                "fact_type": need["fact_type"],
                "fields": [],
                "languages": list(need["languages"]),
                "production_mode": need["production_mode"],
                "evidence_kinds": list(need["evidence_kinds"]),
                "acceptance_fixture": need["acceptance_fixture"],
            })
            if field not in item["fields"]:
                item["fields"].append(field)

    for item in planned.values():
        item["fields"].sort()
    ordered_plan = [planned[key] for key in sorted(planned)]
    gaps.sort(key=lambda gap: (gap["fact_type"], tuple(gap["fields"]), gap["reason"]))
    return {
        "plan": ordered_plan,
        "gaps": gaps,
        "catalogue_version": catalogue["contract_version"],
        "catalogue_mutated": False,
        "matrix_mutated": False,
    }
