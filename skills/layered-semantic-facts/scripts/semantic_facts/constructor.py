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
from .induction import ELIGIBLE_REASONS, build_induction_requests, validate_induction_result
from .induction_provider import InductionProviderRegistry, run_induction_requests



def _merge_request_fact_contributions(
    facts: list[dict[str, Any]],
    *,
    gaps: list[dict[str, Any]],
    target: dict[str, Any],
    context: dict[str, Any],
    coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    """Merge same request-local semantic fact contributions before FactBatch validation.

    The repository still owns cross-request incremental persistence. This helper
    only prevents duplicate contributions inside the current FactBatch and keeps
    independent evidence when assertion bodies agree.
    """
    grouped: dict[tuple[str, str, str, str, tuple[str, ...]], dict[str, Any]] = {}
    conflicted: set[tuple[tuple[str, str, str, str, tuple[str, ...]], str]] = set()
    for fact in facts:
        node = fact["node"]
        key = (
            node["source_id"], node["subject_id"], node["node_id"],
            fact["fact_type"], tuple(sorted(fact.get("granularities", []))),
        )
        current = grouped.get(key)
        if current is None:
            grouped[key] = json.loads(json.dumps(fact))
            continue
        for field_name, assertion in fact.get("fields", {}).items():
            previous = current["fields"].get(field_name)
            if previous is None:
                current["fields"][field_name] = json.loads(json.dumps(assertion))
                continue
            field_key = (key, field_name)
            if field_key in conflicted:
                continue
            left = json.loads(json.dumps(previous))
            right = json.loads(json.dumps(assertion))
            left_basis = left.pop("basis", {})
            right_basis = right.pop("basis", {})
            left_evidence = left_basis.get("evidence", [])
            right_evidence = right_basis.get("evidence", [])
            # Producer-specific method/limitations may differ while both
            # observations support the same semantic assertion. Core assertion
            # context/value/validity/coverage and inference premises must agree;
            # methods and limitations are retained as merged provenance.
            if left != right or left_basis.get("premises", []) != right_basis.get("premises", []):
                conflicted.add(field_key)
                current["fields"].pop(field_name, None)
                gaps.append({
                    "fact_type": fact["fact_type"],
                    "fields": [field_name],
                    "target": target,
                    "reason": "conflict",
                    "detail": "Multiple producers returned incompatible assertions for the same semantic entity field in one request.",
                    "context": context,
                    "coverage": {**coverage, "completeness": "partial"},
                })
                continue
            by_id: dict[str, dict[str, Any]] = {}
            for item in [*left_evidence, *right_evidence]:
                evidence_id = item.get("evidence_id")
                if not isinstance(evidence_id, str):
                    continue
                existing = by_id.get(evidence_id)
                if existing is not None and existing != item:
                    conflicted.add(field_key)
                    current["fields"].pop(field_name, None)
                    gaps.append({
                        "fact_type": fact["fact_type"],
                        "fields": [field_name],
                        "target": target,
                        "reason": "conflict",
                        "detail": f"Producers reused evidence identity {evidence_id!r} with different content.",
                        "context": context,
                        "coverage": {**coverage, "completeness": "partial"},
                    })
                    break
                by_id.setdefault(evidence_id, item)
            if field_key not in conflicted:
                merged = json.loads(json.dumps(previous))
                basis = merged.setdefault("basis", {})
                basis["evidence"] = list(by_id.values())
                methods = {
                    value for value in (left_basis.get("method"), right_basis.get("method"))
                    if isinstance(value, str) and value
                }
                if methods:
                    basis["method"] = " | ".join(sorted(methods))
                limitations = {
                    value
                    for value in [
                        *left_basis.get("limitations", []),
                        *right_basis.get("limitations", []),
                    ]
                    if isinstance(value, str) and value
                }
                basis["limitations"] = sorted(limitations)
                current["fields"][field_name] = merged
    result: list[dict[str, Any]] = []
    for key in sorted(grouped):
        fact = grouped[key]
        if not fact["fields"]:
            continue
        stable = json.dumps(key, ensure_ascii=False, separators=(",", ":"))
        fact["fact_id"] = "fact-" + hashlib.sha256(stable.encode("utf-8")).hexdigest()[:24]
        result.append(fact)
    return result


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
    induction_provider_registry: InductionProviderRegistry | None = None,
    induction_provider_id: str | None = None,
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
    induction_observations: list[dict[str, Any]] = []
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

            # Consume only selected, enabled, accepted producer profiles.
            if any(
                profile["environment"] == "subprocess" or profile["tool_id"] == "python.pyproject-toml"
                for item in plan_result["plan"]
                for profile in item.get("producer_profiles", [])
            ):
                matrix = CapabilityMatrix(assets / "capability-matrix.json")
                parser_registry = ParserRegistry(assets)
                executed_profiles: set[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = set()
                root_languages = {
                    "python" if path.suffix == ".py" else "rust"
                    for path in root.rglob("*")
                    if path.is_file()
                    and path.suffix in {".py", ".rs"}
                    and not any(part in {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"} for part in path.relative_to(root).parts)
                }
                for item in plan_result["plan"]:
                    for profile in item.get("producer_profiles", []):
                        profile_languages = {str(language).lower() for language in profile.get("languages", [])}
                        if profile_languages and not (profile_languages & root_languages):
                            # A request may span multiple projects/languages. A
                            # producer selected for one source must not be run
                            # against another source that lacks that language.
                            continue
                        tool_id = profile["tool_id"]
                        if tool_id == "rust.cargo-metadata" and profile["environment"] == "subprocess":
                            manifest = root / "Cargo.toml"
                            if not manifest.is_file():
                                gaps.append({
                                    "fact_type": item["fact_type"], "fields": item["fields"],
                                    "target": request["query"]["target"], "reason": "unavailable_tool",
                                    "detail": f"Cargo manifest not found: {manifest}",
                                    "context": context, "coverage": coverage,
                                })
                                continue
                            native_output = ""
                            command_args = ["--manifest-path", str(manifest)]
                            language = "Rust"
                            checked = ["Cargo.toml"]
                        elif tool_id == "python.pyproject-toml" and profile["environment"] == "in-process":
                            manifest = root / "pyproject.toml"
                            if not manifest.is_file():
                                gaps.append({
                                    "fact_type": item["fact_type"], "fields": item["fields"],
                                    "target": request["query"]["target"], "reason": "unavailable_tool",
                                    "detail": f"Python project manifest not found: {manifest}",
                                    "context": context, "coverage": coverage,
                                })
                                continue
                            try:
                                native_output = manifest.read_text(encoding="utf-8")
                            except (OSError, UnicodeDecodeError) as error:
                                gaps.append({
                                    "fact_type": item["fact_type"], "fields": item["fields"],
                                    "target": request["query"]["target"], "reason": "unparseable",
                                    "detail": f"Cannot read pyproject.toml: {error}",
                                    "context": context, "coverage": coverage,
                                })
                                continue
                            command_args = []
                            language = "Python"
                            checked = ["pyproject.toml"]
                        else:
                            continue

                        task_key = (
                            tool_id,
                            profile["environment"],
                            tuple(profile["invocation"]),
                            tuple(command_args),
                        )
                        if task_key in executed_profiles:
                            continue
                        executed_profiles.add(task_key)
                        entry = next(entry for entry in matrix.load()["entries"] if entry["tool_id"] == tool_id)
                        parse_request = {
                            "kind": "parse_request",
                            "tool_native_output": {"encoding": "utf-8", "text": native_output},
                            "invocation_profile": {
                                "tool_id": tool_id,
                                "tool_version": "observed-by-execution",
                                "command": list(profile["invocation"]),
                                "environment": {"language": language, "platform": sys.platform},
                                "sources": [actual_source],
                                "coverage": {
                                    "domain": f"{manifest.name} metadata for the explicit project root",
                                    "checked": checked,
                                    "excluded": list(actual_source.get("excludes", [])),
                                    "completeness": "complete",
                                    "method": "read-only manifest parser",
                                },
                                "evidence": [],
                            },
                        }
                        parsed = dispatch_registered_producer(
                            entry, parse_request, parser_registry,
                            external_executor=external_executor if profile["environment"] == "subprocess" else None,
                            cwd=root if profile["environment"] == "subprocess" else None,
                            args=command_args, timeout_seconds=20.0,
                        )
                        if parsed.get("gaps"):
                            for parser_gap in parsed["gaps"]:
                                gaps.append({**parser_gap, "target": request["query"]["target"]})
                            continue
                        induction_observations.extend(parsed["observations"])
                        mapping = {
                            "source.f3.runtime": ("F3", "runtime"),
                            "source.f3.environment": ("F3", "environment"),
                            "source.f4.kind": ("F4", "kind"),
                            "source.f6.kind": ("F6", "kind"),
                        }
                        for observation in parsed["observations"]:
                            need_id = observation["information_need_id"]
                            mapped = mapping.get(need_id)
                            if mapped is None:
                                if any(
                                    need_id == need["need_id"] and need["fact_type"] in requested_fields
                                    and any(field in requested_fields[need["fact_type"]] for field in need["fields"])
                                    for need in __import__("semantic_facts.information_needs", fromlist=["load_information_needs"]).load_information_needs(assets)["needs"]
                                ):
                                    gaps.append({
                                        "fact_type": item["fact_type"], "fields": item["fields"],
                                        "target": request["query"]["target"], "reason": "uncovered_need",
                                        "detail": f"No accepted FactBatch mapping for observation need {need_id}.",
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
                                    "method": f"native {tool_id} parser",
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

            if any(
                profile["environment"] == "subprocess" or profile["tool_id"] == "python.pyproject-toml"
                for item in plan_result["plan"]
                for profile in item.get("producer_profiles", [])
            ):
                try:
                    refreshed = build_fact_batch_with_gaps(root, codec)
                    refreshed_source = refreshed["batch"]["sources"][0]
                except (OSError, ValueError, IndexError) as error:
                    refreshed_source = None
                    refresh_detail = str(error)
                else:
                    refresh_detail = ""
                if refreshed_source is None or refreshed_source["content_state"] != actual_source["content_state"]:
                    sources.pop()
                    gaps.append({
                        "fact_type": "F2",
                        "fields": sorted(set().union(*requested_fields.values())) if requested_fields else [],
                        "target": request["query"]["target"],
                        "reason": "source_modified",
                        "detail": (
                            f"Source changed during external producer execution: {root}"
                            if refreshed_source is not None
                            else f"Cannot revalidate source after external producer execution: {root}: {refresh_detail}"
                        ),
                        "context": context,
                        "coverage": {**coverage, "completeness": "partial"},
                    })
                    continue

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

    facts = _merge_request_fact_contributions(
        facts,
        gaps=gaps,
        target=request["query"]["target"],
        context=context,
        coverage=coverage,
    )
    batch = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "sources": sources,
        "facts": facts,
        "navigation": [],
        "direct_nodes": direct_nodes,
        "conflicts": [],
    }
    eligible_gaps = [gap for gap in gaps if gap.get("reason") in ELIGIBLE_REASONS]
    if eligible_gaps and induction_observations:
        if induction_provider_registry is not None and induction_provider_id:
            provider_result = run_induction_requests(
                induction_observations,
                batch,
                eligible_gaps,
                induction_provider_id,
                induction_provider_registry,
                assets,
            )
            batch["facts"].extend(
                fact
                for item in provider_result["results"]
                for fact in item["induction_result"]["batch"]["facts"]
            )
            gaps = [gap for gap in gaps if gap not in eligible_gaps]
            gaps.extend(provider_result["gaps"])
        else:
            induction_plan = build_induction_requests(
                induction_observations, batch, eligible_gaps, assets
            )
            gaps = [gap for gap in gaps if gap not in eligible_gaps]
            gaps.extend(induction_plan["gaps"])
            for induction_request in induction_plan["requests"]:
                unresolved = validate_induction_result(induction_request, None, assets)
                gaps.extend(unresolved["gaps"])

    codec.validate_batch(batch)
    result = {"kind": "construct_result", "batch": batch, "gaps": gaps}
    _validate_result(result, assets)
    return result
