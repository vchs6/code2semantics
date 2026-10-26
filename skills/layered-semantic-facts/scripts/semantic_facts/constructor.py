"""Constructor runtime boundary: fixed needs -> accepted parser profiles -> FactBatch.

This component never persists facts or assembles the final query response.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .constructor_plan import plan_constructor_request
from .repository.contract import ContractCodec
from .source_scanner import build_fact_batch


def _validate_result(result: dict[str, Any], asset_root: Path) -> None:
    schemas = [json.loads(path.read_text(encoding="utf-8")) for path in asset_root.glob("*.schema.json")]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    pipeline_id = next(
        schema["$id"] for schema in schemas if schema["$id"].endswith("/pipeline.schema.json")
    )
    validator = Draft202012Validator(
        {"$ref": pipeline_id + "#/$defs/construct_result"}, registry=registry
    )
    error = next(validator.iter_errors(result), None)
    if error:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise ValueError(f"invalid ConstructResult {pointer}: {error.message}")


def execute_constructor_request(
    request: dict[str, Any],
    asset_root: str | Path | None = None,
) -> dict[str, Any]:
    """Execute the currently supported deterministic Python/Rust F2 constructor.

    The constructor reads current source roots and accepted parser profiles, returns
    a contract-valid FactBatch plus explicit gaps, and never touches SQLite.
    """
    assets = Path(asset_root) if asset_root else Path(__file__).resolve().parents[2] / "assets"
    plan_result = plan_constructor_request(request, assets)
    codec = ContractCodec(assets)
    requested_fields: dict[str, set[str]] = {}
    for item in plan_result["plan"]:
        requested_fields.setdefault(item["fact_type"], set()).update(item["fields"])

    gaps: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    direct_nodes: list[dict[str, Any]] = []
    current_sources = request["current_source_context"]["sources"]
    needs_inventory = any(gap.get("reason") == "coverage_incomplete" for gap in request["unmet"])
    if not current_sources:
        raise ValueError("ConstructRequest requires at least one current source")

    context = {
        "source_ids": [source["source_id"] for source in current_sources],
        "conditions": [],
        "environment": {},
        "language_semantics": ["First-phase Python/Rust syntax inventory only"],
    }
    coverage = {
        "domain": "requested current project scope",
        "checked": list(request["query"]["scope"]["directories"]),
        "excluded": list(request["query"]["scope"]["excludes"]),
        "completeness": "partial",
        "method": "fixed information-needs plan and accepted parser profiles",
    }

    for gap in plan_result["gaps"]:
        gaps.append({
            "fact_type": gap["fact_type"],
            "fields": gap["fields"],
            "target": gap["target"],
            "reason": gap["reason"],
            "detail": gap["detail"],
            "context": context,
            "coverage": coverage,
        })

    if requested_fields or needs_inventory:
        for current_source in current_sources:
            root = Path(current_source["root"])
            try:
                produced = build_fact_batch(root, codec)
            except (OSError, ValueError) as error:
                gaps.append({
                    "fact_type": "F2",
                    "fields": sorted(set().union(*requested_fields.values())),
                    "target": request["query"]["target"],
                    "reason": "construction_failed",
                    "detail": f"Cannot construct facts from {root}: {error}",
                    "context": context,
                    "coverage": coverage,
                })
                continue

            actual_source = produced["sources"][0]
            if actual_source["content_state"] != current_source["content_state"]:
                gaps.append({
                    "fact_type": "F2",
                    "fields": sorted(set().union(*requested_fields.values())),
                    "target": request["query"]["target"],
                    "reason": "source_modified",
                    "detail": f"Source changed during construction: {root}",
                    "context": context,
                    "coverage": coverage,
                })
                continue

            sources.append(actual_source)
            query_target = request["query"]["target"]
            for inventory in produced["direct_nodes"]:
                if query_target["kind"] == "scope":
                    direct_nodes.append(inventory)
                elif inventory["target"]["kind"] == "node" and inventory["target"]["node"] == query_target["node"]:
                    direct_nodes.append(inventory)
            for fact in produced["facts"]:
                fields = requested_fields.get(fact["fact_type"], set())
                projected = dict(fact)
                projected["fields"] = {
                    name: assertion
                    for name, assertion in fact["fields"].items()
                    if name in fields
                }
                if projected["fields"]:
                    facts.append(projected)
    else:
        sources.extend(current_sources)

    if not sources:
        # Keep the request's source context in the FactBatch even when every
        # producer failed or the source changed during construction.
        sources.extend(current_sources)

    batch = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "sources": sources,
        "facts": facts,
        "navigation": [],
        "direct_nodes": direct_nodes,
        "conflicts": [],
    }
    codec.validate_batch(batch)
    result = {"kind": "construct_result", "batch": batch, "gaps": gaps}
    _validate_result(result, assets)
    return result
