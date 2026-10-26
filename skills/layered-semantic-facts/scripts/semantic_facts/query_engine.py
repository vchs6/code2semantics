"""Deterministic query response projection for the currently supported syntax facts."""
from __future__ import annotations

import json
import hashlib
import sqlite3
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .repository.store import Repository
from .source_scanner import inspect_source
from .constructor import execute_constructor_request
from .tool_executor import SubprocessToolExecutor


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
    needs_document = json.loads((Path(asset_root) / "information-needs.json").read_text(encoding="utf-8"))
    in_catalog = {
        (need["fact_type"], field)
        for need in needs_document["needs"]
        for field in need["fields"]
    }
    out_of_catalog: list[dict[str, Any]] = []
    for selection in query["selections"]:
        unsupported = sorted(
            field for field in selection["fields"]
            if (selection["fact_type"], field) not in in_catalog
        )
        if unsupported:
            out_of_catalog.append({
                "fact_type": selection["fact_type"],
                "fields": unsupported,
                "reason": "No fixed first-phase information need covers these fields.",
            })
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
    inventory_gap_reason = "coverage_incomplete"
    inventory_gap_detail = "Direct-node completeness for the requested observation boundary is not established by current evidence."
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
        scope_inventories = [
            inventory for inventory in stored["direct_nodes"]
            if inventory.get("target", {}).get("kind") == "scope"
            and set(inventory.get("assertion", {}).get("context", {}).get("source_ids", [])).intersection(current_states)
        ]
        target_node = target["node"]
        scope_is_current = any(inventory_is_current(item) for item in scope_inventories)
        target_is_in_scope = any(
            inventory_is_current(item) and target_node in item.get("children", [])
            for item in scope_inventories
        )
        matching_direct_nodes = [
            inventory for inventory in stored["direct_nodes"]
            if inventory.get("target", {}).get("kind") == "node"
            and inventory["target"].get("node") == target_node
        ]
        target_inventory_complete = any(inventory_is_current(inventory) for inventory in matching_direct_nodes)
        inventory_complete = scope_is_current and target_is_in_scope and target_inventory_complete
        if scope_is_current and not target_is_in_scope:
            inventory_gap_reason = "invalid_reference"
            inventory_gap_detail = "The requested node is not present in the current direct-node inventory for the specified project scope."

    if not inventory_complete:
        gaps.append({
            "fact_type": "F2",
            "fields": ["direct_nodes"],
            "target": target,
            "reason": inventory_gap_reason,
            "detail": inventory_gap_detail,
            "context": context,
            "coverage": coverage,
        })

    for selection in query["selections"]:
        requested_fields = [
            field for field in selection["fields"]
            if (selection["fact_type"], field) in in_catalog
        ]
        if not requested_fields:
            continue
        matching = [fact for fact in results if fact["fact_type"] == selection["fact_type"]]
        if not matching:
            gaps.append({
                "fact_type": selection["fact_type"],
                "fields": requested_fields,
                "target": query["target"],
                "reason": "missing",
                "detail": "No stored fact of the requested type matched this query.",
                "context": context,
                "coverage": coverage,
            })
            continue
        present = {field for fact in matching for field in fact.get("fields", {})}
        missing = sorted(set(requested_fields) - present)
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
        "out_of_catalog": out_of_catalog,
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


def _repository_unavailable_response(
    query: dict[str, Any],
    sources: list[dict[str, Any]],
    detail: str,
    response_validator: Draft202012Validator,
) -> dict[str, Any]:
    """Return a validated, explicit gap response when the fact store cannot be read."""
    context = {
        "source_ids": sorted(source["source_id"] for source in sources if source.get("status") == "available"),
        "conditions": [],
        "environment": {},
        "language_semantics": ["Repository unavailable; no alternate store was selected"],
    }
    coverage = {
        "domain": "explicitly requested project roots",
        "checked": list(query["scope"]["directories"]),
        "excluded": list(query["scope"]["excludes"]),
        "completeness": "unknown",
        "method": "repository access check",
    }
    gaps = [{
        "fact_type": selection["fact_type"],
        "fields": list(selection["fields"]),
        "target": query["target"],
        "reason": "repository_unavailable",
        "detail": detail,
        "context": context,
        "coverage": coverage,
    } for selection in query["selections"]]
    gaps.append({
        "fact_type": "F2",
        "fields": ["direct_nodes"],
        "target": query["target"],
        "reason": "repository_unavailable",
        "detail": detail,
        "context": context,
        "coverage": coverage,
    })
    response = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "query": query,
        "sources": sources,
        "results": [],
        "direct_nodes": [],
        "premise_checks": [],
        "conflicts": [],
        "gaps": gaps,
        "out_of_catalog": [],
        "termination": "unavailable",
    }
    validation_error = next(response_validator.iter_errors(response), None)
    if validation_error:
        raise QueryContractError(
            f"response {list(validation_error.absolute_path)}: {validation_error.message}"
        )
    return response


def execute_query_with_construction(
    query: dict[str, Any],
    repository: Repository,
    asset_root: str | Path | None = None,
    *,
    external_executor: SubprocessToolExecutor | None = None,
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
    if query["target"]["kind"] == "node" and query["target"]["node"]["source_id"] not in current_ids:
        # Do not query the repository for a node outside the explicitly authorized
        # source roots. Return an explicit gap without probing the foreign identity.
        context = {
            "source_ids": sorted(current_ids),
            "conditions": [],
            "environment": {},
            "language_semantics": ["Out-of-scope target rejected before repository read"],
        }
        coverage = {
            "domain": "explicitly requested project roots",
            "checked": list(query["scope"]["directories"]),
            "excluded": list(query["scope"]["excludes"]),
            "completeness": "unknown",
            "method": "source-boundary authorization check",
        }
        gaps = [{
            "fact_type": selection["fact_type"],
            "fields": list(selection["fields"]),
            "target": query["target"],
            "reason": "invalid_reference",
            "detail": "The requested node source is outside the explicitly authorized project roots.",
            "context": context,
            "coverage": coverage,
        } for selection in query["selections"]]
        gaps.append({
            "fact_type": "F2",
            "fields": ["direct_nodes"],
            "target": query["target"],
            "reason": "invalid_reference",
            "detail": "The requested node source is outside the explicitly authorized project roots.",
            "context": context,
            "coverage": coverage,
        })
        response = {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "query": query,
            "sources": current_sources,
            "results": [],
            "direct_nodes": [],
            "premise_checks": [],
            "conflicts": [],
            "gaps": gaps,
            "out_of_catalog": [],
            "termination": "no_progress",
        }
        error = next(response_validator.iter_errors(response), None)
        if error:
            raise QueryContractError(f"response {list(error.absolute_path)}: {error.message}")
        return response

    try:
        stored = repository.read(query)
    except (OSError, sqlite3.Error) as error:
        return _repository_unavailable_response(
            query, current_sources, f"Fact repository is unavailable: {error}", response_validator
        )

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

    def complete_inventory_keys(result: dict[str, Any]) -> set[str]:
        current_states = {source["source_id"]: source["content_state"] for source in current_sources}
        keys: set[str] = set()
        for inventory in result["direct_nodes"]:
            target = inventory.get("target", {})
            assertion = inventory.get("assertion", {})
            if assertion.get("knowledge") != "supported" or assertion.get("coverage", {}).get("completeness") != "complete":
                continue
            validity = assertion.get("validity", {})
            if validity.get("state") != "current":
                continue
            validity_sources = validity.get("sources", [])
            if not validity_sources or any(
                item.get("source_id") not in current_states
                or item.get("content_state") != current_states[item.get("source_id")]
                for item in validity_sources
            ):
                continue
            evidence = assertion.get("basis", {}).get("evidence", [])
            if not all(
                item.get("source_id") in current_states
                and item.get("content_state") == current_states[item.get("source_id")]
                for item in evidence
            ):
                continue

            is_requested_target = target == query["target"]
            is_required_ancestor = (
                query["target"]["kind"] == "node"
                and target.get("kind") == "scope"
                and query["target"]["node"] in inventory.get("children", [])
            )
            if not is_requested_target and not is_required_ancestor:
                continue
            keys.add(json.dumps({
                "target": target,
                "sources": sorted(assertion["context"]["source_ids"]),
                "checked": assertion["coverage"]["checked"],
                "role": "ancestor" if is_required_ancestor else "target",
            }, sort_keys=True, ensure_ascii=False))
        return keys

    last_constructor_gaps: list[dict[str, Any]] = []
    budget_exhausted = False
    max_rounds = max(1, query["budget"]["max_rounds"])
    for round_index in range(max_rounds):
        stored = repository.read(query)
        stored = {**stored, "facts": [fact for fact in stored["facts"] if fact["node"]["source_id"] in current_ids]}
        before_coverage = {
            (fact["fact_type"], field)
            for fact in stored["facts"] for field in fact.get("fields", {})
        }
        before_inventory = complete_inventory_keys(stored)
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
            constructed = execute_constructor_request(construct_request, assets, external_executor=external_executor)
        except (OSError, ValueError) as error:
            last_constructor_gaps = [{
                **gap,
                "reason": "construction_failed",
                "detail": f"Constructor failed: {error}",
            } for gap in response["gaps"]]
            break

        last_constructor_gaps = [gap for gap in constructed["gaps"] if gap["reason"] != "uncovered_need"]
        if any(gap["reason"] == "source_modified" for gap in last_constructor_gaps):
            break

        batch = constructed["batch"]
        digest = hashlib.sha256(
            json.dumps(batch, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        try:
            repository.write(batch, "query-construct-" + digest)
            refreshed = repository.read(query)
        except (OSError, sqlite3.Error) as error:
            return _repository_unavailable_response(
                query, current_sources, f"Fact repository is unavailable: {error}", response_validator
            )
        refreshed = {**refreshed, "facts": [fact for fact in refreshed["facts"] if fact["node"]["source_id"] in current_ids]}
        after_coverage = {
            (fact["fact_type"], field)
            for fact in refreshed["facts"] for field in fact.get("fields", {})
        }
        after_inventory = complete_inventory_keys(refreshed)
        response = execute_query(query, repository, assets, stored_result=refreshed, source_override=current_sources)
        if not response["gaps"]:
            return response
        if not (after_coverage - before_coverage) and not (after_inventory - before_inventory):
            break
        if round_index == max_rounds - 1:
            budget_exhausted = True
            response["termination"] = "budget_exhausted"

    try:
        stored = repository.read(query)
    except (sqlite3.Error, OSError, ValueError) as error:
        return _repository_unavailable_response(
            query, current_sources, f"Fact repository is unavailable: {error}", response_validator
        )
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
            if gap["reason"] == "uncovered_need":
                continue
            key = (gap["fact_type"], tuple(gap["fields"]), gap["reason"], gap["detail"])
            if key not in existing_keys:
                merged_gaps.append(gap)
                existing_keys.add(key)
        response["gaps"] = merged_gaps
    if not response["gaps"]:
        response["termination"] = "satisfied"
    elif budget_exhausted:
        response["termination"] = "budget_exhausted"
    else:
        response["termination"] = "no_progress"
    error = next(response_validator.iter_errors(response), None)
    if error:
        raise QueryContractError(f"response {list(error.absolute_path)}: {error.message}")
    return response
