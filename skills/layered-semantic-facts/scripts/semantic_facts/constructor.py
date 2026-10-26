"""Constructor runtime boundary: fixed needs -> accepted parser profiles -> FactBatch.

This component never persists facts or assembles the final query response.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .constructor_plan import plan_constructor_request
from .capability_matrix import CapabilityMatrix
from .info_parser import ParserRegistry
from .producer_dispatch import dispatch_registered_producer
from .repository.contract import ContractCodec
from .source_scanner import build_fact_batch_with_gaps
from .tool_executor import SubprocessToolExecutor


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
    *,
    external_executor: SubprocessToolExecutor | None = None,
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
                scan_result = build_fact_batch_with_gaps(root, codec, external_executor=external_executor)
                produced = scan_result["batch"]
                for scan_gap in scan_result["gaps"]:
                    gaps.append({
                        "fact_type": "F2",
                        "fields": sorted(set().union(*requested_fields.values())) if requested_fields else [],
                        "target": request["query"]["target"],
                        "reason": scan_gap["reason"],
                        "detail": scan_gap["path"] + ": " + scan_gap["detail"],
                        "context": context,
                        "coverage": {**coverage, "completeness": "partial", "checked": [scan_gap["path"]]},
                    })
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

            # Consume accepted subprocess producers selected by the fixed plan.
            if external_executor is not None and any(
                profile["environment"] == "subprocess"
                for item in plan_result["plan"]
                for profile in item.get("producer_profiles", [])
            ):
                matrix = CapabilityMatrix(assets / "capability-matrix.json")
                parser_registry = ParserRegistry(assets)
                for item in plan_result["plan"]:
                    for profile in item.get("producer_profiles", []):
                        if profile["environment"] != "subprocess":
                            continue
                        tool_id = profile["tool_id"]
                        if tool_id != "rust.cargo-metadata":
                            continue
                        manifest = root / "Cargo.toml"
                        if not manifest.is_file():
                            gaps.append({
                                "fact_type": item["fact_type"],
                                "fields": item["fields"],
                                "target": request["query"]["target"],
                                "reason": "unavailable_tool",
                                "detail": f"Cargo manifest not found: {manifest}",
                                "context": context,
                                "coverage": coverage,
                            })
                            continue
                        entry = next(entry for entry in matrix.load()["entries"] if entry["tool_id"] == tool_id)
                        parse_request = {
                            "kind": "parse_request",
                            "tool_native_output": {"encoding": "utf-8", "text": ""},
                            "invocation_profile": {
                                "tool_id": tool_id,
                                "tool_version": "observed-by-execution",
                                "command": list(profile["invocation"]),
                                "environment": {"language": "Rust", "platform": sys.platform},
                                "sources": [actual_source],
                                "coverage": {
                                    "domain": "Cargo workspace/package metadata for the explicit project root",
                                    "checked": ["Cargo.toml"],
                                    "excluded": list(actual_source.get("excludes", [])),
                                    "completeness": "complete",
                                    "method": "cargo metadata --no-deps --format-version 1",
                                },
                                "evidence": [],
                            },
                        }
                        parsed = dispatch_registered_producer(
                            entry, parse_request, parser_registry,
                            external_executor=external_executor, cwd=root,
                            args=["--manifest-path", str(manifest)], timeout_seconds=20.0,
                        )
                        if parsed.get("gaps"):
                            for parser_gap in parsed["gaps"]:
                                gaps.append({**parser_gap, "target": request["query"]["target"]})
                            continue
                        for observation in parsed["observations"]:
                            need_id = observation["information_need_id"]
                            mapping = {
                                "source.f4.kind": ("F4", "kind"),
                                "source.f6.kind": ("F6", "kind"),
                                "source.f3.entries": ("F3", "entries"),
                            }
                            mapped = mapping.get(need_id)
                            if mapped is None:
                                gaps.append({
                                    "fact_type": item["fact_type"], "fields": item["fields"],
                                    "target": request["query"]["target"], "reason": "uncovered_need",
                                    "detail": f"No FactBatch mapping is accepted for observation need {need_id}.",
                                    "context": observation["context"], "coverage": observation["coverage"],
                                })
                                continue
                            fact_type, field_name = mapped
                            if field_name not in requested_fields.get(fact_type, set()):
                                continue
                            assertion = {
                                "origin": "observed", "knowledge": "supported",
                                "context": observation["context"], "coverage": observation["coverage"],
                                "basis": {
                                    "evidence": observation["evidence"], "premises": [],
                                    "method": f"native {tool_id} output parser",
                                    "limitations": [
                                        "Manifest declaration only; does not prove runtime behavior.",
                                        "Workspace membership and package dependency are distinct relation kinds.",
                                    ],
                                },
                                "value": observation["payload"],
                                "validity": {"state": "current", "sources": [{
                                    "source_id": actual_source["source_id"],
                                    "content_state": actual_source["content_state"],
                                }]},
                            }
                            produced["facts"].append({
                                "fact_id": "fact-" + hashlib.sha256(
                                    (observation["observation_id"] + ":" + fact_type + ":" + field_name).encode("utf-8")
                                ).hexdigest()[:24],
                                "node": observation["subject"], "fact_type": fact_type,
                                "granularities": ["L2"], "fields": {field_name: assertion},
                            })

            query_target = request["query"]["target"]
            for inventory in produced["direct_nodes"]:
                if query_target["kind"] == "scope":
                    direct_nodes.append(inventory)
                elif inventory["target"]["kind"] == "scope":
                    # Establish the current project-to-file path before accepting
                    # a node-target inventory.
                    direct_nodes.append(inventory)
                elif inventory["target"]["kind"] == "node" and inventory["target"]["node"] == query_target["node"]:
                    direct_nodes.append(inventory)
            for fact in produced["facts"]:
                if request["query"]["target"]["kind"] == "node" and fact["node"] != request["query"]["target"]["node"]:
                    continue
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
