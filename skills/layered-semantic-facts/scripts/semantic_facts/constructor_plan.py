"""Deterministic constructor request planning over the fixed information-needs catalogue."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .information_needs import load_information_needs
from .capability_matrix import CapabilityMatrix


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


def _validate_construct_request(request: dict[str, Any], asset_root: Path) -> None:
    schemas = [json.loads(path.read_text(encoding="utf-8")) for path in asset_root.glob("*.schema.json")]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    pipeline_id = next(
        schema["$id"] for schema in schemas
        if schema["$id"].endswith("/pipeline.schema.json")
    )
    validator = Draft202012Validator(
        {"$ref": pipeline_id + "#/$defs/construct_request"}, registry=registry
    )
    error = next(validator.iter_errors(request), None)
    if error:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise ValueError(f"invalid ConstructRequest {pointer}: {error.message}")



def _available_source_languages(request: dict[str, Any]) -> set[str] | None:
    """Return languages found in existing authorized roots; None means roots unavailable."""
    from fnmatch import fnmatch

    roots = request.get("current_source_context", {}).get("sources", [])
    excludes = request.get("query", {}).get("scope", {}).get("excludes", [])
    excluded_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}
    existing_root = False
    languages: set[str] = set()
    for source in roots:
        root = Path(source.get("root", ""))
        if not root.is_dir():
            continue
        existing_root = True
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if any(part in excluded_dirs for part in path.relative_to(root).parts):
                continue
            if any(fnmatch(relative, pattern) or relative == pattern for pattern in excludes):
                continue
            if path.suffix == ".py":
                languages.add("python")
            elif path.suffix == ".rs":
                languages.add("rust")
    return languages if existing_root else None


def plan_constructor_request(
    request: dict[str, Any],
    asset_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return a stable need plan and explicit gaps; never mutate assets or matrix."""
    root = Path(asset_root) if asset_root else Path(__file__).resolve().parents[2] / "assets"
    _validate_construct_request(request, root)
    catalogue = load_information_needs(root)
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

    # Collect the whole request's unmet needs before choosing any producer.
    # This lets one accepted profile cover several requested needs instead of
    # independently selecting a narrow producer for every field.
    platform = "windows" if sys.platform.startswith("win") else "darwin" if sys.platform == "darwin" else "linux"
    matrix = CapabilityMatrix(root / "capability-matrix.json")
    need_ids_by_profile: dict[tuple[str, str], set[str]] = {}
    for selection in query["selections"]:
        fact_type = selection["fact_type"]
        for field in selection["fields"]:
            matching_facts = facts_by_type.get(fact_type, [])
            satisfied = any(
                field in fact.get("fields", {})
                and _supported_current_assertion(fact["fields"][field], current_states)
                for fact in matching_facts
                if fact.get("node", {}).get("source_id") in current_states
            )
            if satisfied:
                continue
            need = needs_index.get((fact_type, field))
            if need is None:
                continue
            for language in need["languages"]:
                for environment in need["environments"]:
                    need_ids_by_profile.setdefault((language, environment), set()).add(need["need_id"])

    selected_by_profile: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = {}
    available_languages = _available_source_languages(request)
    for (language, environment), ids in sorted(need_ids_by_profile.items()):
        if available_languages is not None and language.lower() not in available_languages:
            continue
        selected_by_profile[(language, environment)] = select_enabled_producers(
            matrix, sorted(ids), language, platform, environment
        )

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
            producers_by_id: dict[str, dict[str, Any]] = {}
            for language in need["languages"]:
                for environment in need["environments"]:
                    selected = selected_by_profile.get((language, environment), {})
                    for entry in selected.get(key, []):
                        producers_by_id[entry["tool_id"]] = entry
            if not producers_by_id:
                gaps.append({
                    "fact_type": fact_type,
                    "fields": [field],
                    "target": query["target"],
                    "reason": "unavailable_tool",
                    "detail": f"No accepted enabled producer is available for {need['need_id']}.",
                    "need_id": need["need_id"],
                })
                continue

            item = planned.setdefault(key, {
                "need_id": key,
                "fact_type": need["fact_type"],
                "fields": [],
                "languages": list(need["languages"]),
                "production_mode": need["production_mode"],
                "evidence_kinds": list(need["evidence_kinds"]),
                "acceptance_fixture": need["acceptance_fixture"],
                "producer_ids": sorted(producers_by_id),
                "producer_profiles": [
                    {
                        "tool_id": producers_by_id[tool_id]["tool_id"],
                        "environment": producers_by_id[tool_id]["environment"],
                        "invocation": list(producers_by_id[tool_id]["invocation"]),
                        "output_kinds": list(producers_by_id[tool_id]["output_kinds"]),
                    }
                    for tool_id in sorted(producers_by_id)
                ],
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


def select_enabled_producers(
    matrix: Any,
    need_ids: list[str],
    language: str,
    platform: str,
    environment: str,
) -> dict[str, list[dict[str, Any]]]:
    """Select only accepted, enabled producers; union partial producers by need.

    Matrix candidate discovery is read-only. Disabled or unaccepted entries are
    never eligible, even if the generic matrix query returns them as candidates.
    """
    requested = set(need_ids)
    selected: dict[str, list[dict[str, Any]]] = {need_id: [] for need_id in sorted(requested)}
    candidates_by_id: dict[str, dict[str, Any]] = {}
    for need_id in sorted(requested):
        candidates = matrix.query([need_id], language.lower(), platform.lower(), environment)
        for item in candidates:
            if (
                item.get("enabled") is True
                and item.get("acceptance", {}).get("actor") == "parser_development"
                and item.get("acceptance", {}).get("evidence")
            ):
                candidates_by_id[item["tool_id"]] = item

    # Deterministic greedy set cover over this request's unmet needs. Prefer
    # the profile covering the most still-uncovered needs; ties use stable ID.
    # This avoids selecting one narrow tool per field when one accepted profile
    # safely covers several requested needs.
    uncovered = set(requested)
    while uncovered:
        ranked: list[tuple[int, str, dict[str, Any], set[str]]] = []
        for tool_id, item in candidates_by_id.items():
            covered = set(item.get("information_need_ids", [])) & uncovered
            if covered:
                ranked.append((-len(covered), tool_id, item, covered))
        if not ranked:
            break
        ranked.sort(key=lambda entry: (entry[0], entry[1]))
        _, _, chosen, covered = ranked[0]
        for need_id in covered:
            selected[need_id].append(chosen)
        uncovered.difference_update(covered)
        candidates_by_id.pop(chosen["tool_id"], None)

    for need_id in selected:
        selected[need_id].sort(key=lambda item: item["tool_id"])
    return selected
