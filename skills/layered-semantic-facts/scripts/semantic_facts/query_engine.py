"""Deterministic query response projection for the currently supported syntax facts."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .repository.store import Repository
from .source_scanner import inspect_source
from .constructor import execute_constructor_request


class QueryContractError(ValueError):
    """The query or projected response violates the public contract."""


def _validators(asset_root: Path) -> tuple[Draft202012Validator, Draft202012Validator]:
    schemas = [json.loads(path.read_text(encoding="utf-8")) for path in asset_root.glob("*.schema.json")]
    registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas)
    query_id = next(schema["$id"] for schema in schemas if schema["$id"].endswith("/contract-format.schema.json"))
    response_id = next(schema["$id"] for schema in schemas if schema["$id"].endswith("/output-schema.schema.json"))
    return (
        Draft202012Validator({"$ref": query_id}, registry=registry),
        Draft202012Validator({"$ref": response_id}, registry=registry),
    )


def execute_query(query: dict[str, Any], repository: Repository, asset_root: str | Path | None = None, *, stored_result: dict[str, Any] | None = None, source_override: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Read stored facts and project a minimal contract-shaped response.

    This initial deterministic path supports repository-backed field coverage.
    It does not invoke a constructor, tool, or induction model.
    """
    if asset_root is None:
        asset_root = Path(__file__).resolve().parents[2] / "assets"
    query_validator, response_validator = _validators(Path(asset_root))
    error = next(query_validator.iter_errors(query), None)
    if error:
        raise QueryContractError(f"query {list(error.absolute_path)}: {error.message}")

    stored = stored_result if stored_result is not None else repository.read(query)
    sources = source_override if source_override is not None else stored["sources"]
    if source_override is not None:
        stored = {**stored, "sources": source_override}
    if not sources:
        raise QueryContractError("no stored source record is available for the requested scope")

    gaps: list[dict[str, Any]] = []
    results = stored["facts"]
    source_ids = sorted({source["source_id"] for source in sources})
    context = {
        "source_ids": source_ids,
        "conditions": [],
        "environment": {},
        "language_semantics": ["Repository-backed deterministic field coverage"],
    }
    coverage = {
        "domain": "caller-supplied query scope",
        "checked": list(query["scope"]["directories"]),
        "excluded": list(query["scope"]["excludes"]),
        "completeness": "partial",
        "method": "stored fact field coverage comparison",
    }

    current_states = {source["source_id"]: source["content_state"] for source in sources}

    def inventory_is_current(inventory: dict[str, Any]) -> bool:
        assertion = inventory.get("assertion", {})
        if assertion.get("knowledge") != "supported" or assertion.get("coverage", {}).get("completeness") != "complete":
            return False
        validity = assertion.get("validity", {})
        if validity.get("state") != "current":
            return False
        validity_sources = validity.get("sources", [])
        if not validity_sources or any(
            item.get("source_id") not in current_states
            or item.get("content_state") != current_states[item.get("source_id")]
            for item in validity_sources
        ):
            return False
        return all(
            item.get("source_id") in current_states
            and item.get("content_state") == current_states[item.get("source_id")]
            for item in assertion.get("basis", {}).get("evidence", [])
        )

    target = query["target"]
    if target["kind"] == "scope":
        matching_direct_nodes = [
            inventory for inventory in stored["direct_nodes"]
            if inventory.get("target", {}).get("kind") == "scope"
            and set(inventory.get("assertion", {}).get("context", {}).get("source_ids", [])).intersection(current_states)
        ]
        covered_sources = {
            source_id
            for inventory in matching_direct_nodes
            if inventory_is_current(inventory)
            for source_id in inventory["assertion"]["context"]["source_ids"]
            if source_id in current_states
        }
        inventory_complete = set(current_states).issubset(covered_sources)
    else:
        matching_direct_nodes = [
            inventory for inventory in stored["direct_nodes"]
            if inventory.get("target", {}).get("kind") == "node"
            and inventory["target"].get("node") == target.get("node")
        ]
        inventory_complete = any(inventory_is_current(inventory) for inventory in matching_direct_nodes)

    if not inventory_complete:
        gaps.append({
            "fact_type": "F2",
            "fields": ["direct_nodes"],
            "target": target,
            "reason": "coverage_incomplete",
            "detail": "Direct-node completeness for the requested observation boundary is not established by current evidence.",
            "context": context,
            "coverage": coverage,
        })

    for selection in query["selections"]:
        matching = [fact for fact in results if fact["fact_type"] == selection["fact_type"]]
        if not matching:
            gaps.append({
                "fact_type": selection["fact_type"],
                "fields": list(selection["fields"]),
                "target": query["target"],
                "reason": "missing",
                "detail": "No stored fact of the requested type matched this query.",
                "context": context,
                "coverage": coverage,
            })
            continue
        present = {field for fact in matching for field in fact.get("fields", {})}
        missing = sorted(set(selection["fields"]) - present)
        if missing:
            gaps.append({
                "fact_type": selection["fact_type"],
                "fields": missing,
                "target": query["target"],
                "reason": "missing",
                "detail": "Requested fields are absent from the selected stored facts.",
                "context": context,
                "coverage": coverage,
            })

    response = {
        "contract_version": stored["contract_version"],
        "catalog_id": stored["catalog_id"],
        "query": query,
        "sources": sources,
        "results": results,
        "direct_nodes": matching_direct_nodes,
        "premise_checks": [],
        "conflicts": stored["conflicts"],
        "gaps": gaps,
        "out_of_catalog": [],
        "termination": "no_progress" if gaps else "satisfied",
    }
    error = next(response_validator.iter_errors(response), None)
    if error:
        raise QueryContractError(f"response {list(error.absolute_path)}: {error.message}")
    return response


def _unavailable_source(root: str, detail: str) -> dict[str, Any]:
    digest = hashlib.sha256((root + "\\0" + detail).encode("utf-8")).hexdigest()
    return {
        "source_id": "src-unavailable-" + digest[:20],
        "root": str(Path(root).resolve()),
        "content_state": "sha256:" + digest,
        "status": "unavailable",
        "dirty": True,
        "has_untracked": True,
        "excludes": [],
    }


def execute_query_with_construction(
    query: dict[str, Any],
    repository: Repository,
    asset_root: str | Path | None = None,
) -> dict[str, Any]:
    """Read current facts, construct gaps, append without replacement, re-read, and project."""
    assets = Path(asset_root) if asset_root else Path(__file__).resolve().parents[2] / "assets"
    query_validator, response_validator = _validators(assets)
    error = next(query_validator.iter_errors(query), None)
    if error:
        raise QueryContractError(f"query {list(error.absolute_path)}: {error.message}")

    current_sources: list[dict[str, Any]] = []
    for root in query["scope"]["directories"]:
        try:
            current_sources.append(inspect_source(root))
        except (OSError, ValueError) as error:
            current_sources.append(_unavailable_source(root, str(error)))
    if not current_sources:
        current_sources.append(_unavailable_source(".", "query scope contains no source roots"))

    current_ids = {source["source_id"] for source in current_sources if source["status"] == "available"}
    stored = repository.read(query)
    stored = {**stored, "facts": [fact for fact in stored["facts"] if fact["node"]["source_id"] in current_ids]}
    if any(source["status"] != "available" for source in current_sources):
        response = execute_query(query, repository, assets, stored_result=stored, source_override=current_sources)
        context = {
            "source_ids": [source["source_id"] for source in current_sources],
            "conditions": [],
            "environment": {},
            "language_semantics": [],
        }
        coverage = {
            "domain": "requested current project scope",
            "checked": list(query["scope"]["directories"]),
            "excluded": list(query["scope"]["excludes"]),
            "completeness": "unknown",
            "method": "source access check",
        }
        response["gaps"] = [{
            "fact_type": selection["fact_type"],
            "fields": list(selection["fields"]),
            "target": query["target"],
            "reason": "source_unavailable",
            "detail": "One or more requested source roots are unavailable; no alternate source was selected.",
            "context": context,
            "coverage": coverage,
        } for selection in query["selections"]]
        response["termination"] = "unavailable"
        error = next(response_validator.iter_errors(response), None)
        if error:
            raise QueryContractError(f"response {list(error.absolute_path)}: {error.message}")
        return response

    last_constructor_gaps: list[dict[str, Any]] = []
    max_rounds = max(1, query["budget"]["max_rounds"])
    for round_index in range(max_rounds):
        stored = repository.read(query)
        stored = {**stored, "facts": [fact for fact in stored["facts"] if fact["node"]["source_id"] in current_ids]}
        before_coverage = {
            (fact["fact_type"], field)
            for fact in stored["facts"] for field in fact.get("fields", {})
        }
        response = execute_query(query, repository, assets, stored_result=stored, source_override=current_sources)
        if not response["gaps"]:
            return response

        construct_request = {
            "kind": "construct_request",
            "query": query,
            "existing_valid_facts": {
                "contract_version": stored["contract_version"],
                "catalog_id": stored["catalog_id"],
                "sources": current_sources,
                "facts": stored["facts"],
                "navigation": stored["navigation"],
                "direct_nodes": stored["direct_nodes"],
                "conflicts": stored["conflicts"],
            },
            "unmet": response["gaps"],
            "current_source_context": {
                "sources": current_sources,
                "changes": [],
                "necessary_ancestors": [],
                "obligations": [],
            },
        }
        try:
            constructed = execute_constructor_request(construct_request, assets)
        except (OSError, ValueError) as error:
            last_constructor_gaps = [{
                **gap,
                "reason": "construction_failed",
                "detail": f"Constructor failed: {error}",
            } for gap in response["gaps"]]
            break

        last_constructor_gaps = constructed["gaps"]
        if any(gap["reason"] == "source_modified" for gap in last_constructor_gaps):
            break

        batch = constructed["batch"]
        digest = hashlib.sha256(
            json.dumps(batch, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        repository.write(batch, "query-construct-" + digest)

        refreshed = repository.read(query)
        refreshed = {**refreshed, "facts": [fact for fact in refreshed["facts"] if fact["node"]["source_id"] in current_ids]}
        after_coverage = {
            (fact["fact_type"], field)
            for fact in refreshed["facts"] for field in fact.get("fields", {})
        }
        response = execute_query(query, repository, assets, stored_result=refreshed, source_override=current_sources)
        if not response["gaps"]:
            return response
        if not (after_coverage - before_coverage):
            break
        if round_index == max_rounds - 1:
            response["termination"] = "budget_exhausted"

    stored = repository.read(query)
    stored = {**stored, "facts": [fact for fact in stored["facts"] if fact["node"]["source_id"] in current_ids]}
    response = execute_query(query, repository, assets, stored_result=stored, source_override=current_sources)
    if last_constructor_gaps:
        replaced_fields = {
            (gap["fact_type"], field)
            for gap in last_constructor_gaps for field in gap["fields"]
        }
        merged_gaps = []
        for gap in response["gaps"]:
            remaining = [field for field in gap["fields"] if (gap["fact_type"], field) not in replaced_fields]
            if remaining:
                merged_gaps.append({**gap, "fields": remaining})
        existing_keys = {
            (gap["fact_type"], tuple(gap["fields"]), gap["reason"], gap["detail"])
            for gap in merged_gaps
        }
        for gap in last_constructor_gaps:
            key = (gap["fact_type"], tuple(gap["fields"]), gap["reason"], gap["detail"])
            if key not in existing_keys:
                merged_gaps.append(gap)
                existing_keys.add(key)
        response["gaps"] = merged_gaps
    if not response["gaps"]:
        response["termination"] = "satisfied"
    elif response["termination"] != "budget_exhausted":
        response["termination"] = "no_progress"
    error = next(response_validator.iter_errors(response), None)
    if error:
        raise QueryContractError(f"response {list(error.absolute_path)}: {error.message}")
    return response
