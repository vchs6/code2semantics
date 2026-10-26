"""Deterministic induction batching and evidence-bound result validation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .repository.contract import ContractCodec


ELIGIBLE_REASONS = {"missing", "unknown", "insufficient_evidence", "nonempty_insufficient"}


def _validators(asset_root: Path) -> tuple[Draft202012Validator, Draft202012Validator, Draft202012Validator]:
    schemas = [json.loads(path.read_text(encoding="utf-8")) for path in asset_root.glob("*.schema.json")]
    registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas)
    pipeline_id = next(schema["$id"] for schema in schemas if schema["$id"].endswith("/pipeline.schema.json"))
    return tuple(
        Draft202012Validator({"$ref": pipeline_id + "#/$defs/" + definition}, registry=registry)
        for definition in ("induction_request", "induction_result", "fact_batch")
    )


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _validate(validator: Draft202012Validator, value: dict[str, Any], label: str) -> None:
    error = next(validator.iter_errors(value), None)
    if error:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise ValueError(f"invalid {label} {pointer}: {error.message}")


def build_induction_requests(
    observations: list[dict[str, Any]],
    existing_valid_facts: dict[str, Any],
    unmet: list[dict[str, Any]],
    asset_root: str | Path | None = None,
) -> dict[str, Any]:
    """Group eligible unmet fields by type, subject, source content state and context."""
    assets = Path(asset_root) if asset_root else Path(__file__).resolve().parents[2] / "assets"
    request_validator, _, batch_validator = _validators(assets)
    _validate(batch_validator, existing_valid_facts, "FactBatch")
    groups: dict[str, dict[str, Any]] = {}
    rejected: list[dict[str, Any]] = []

    for gap in unmet:
        if gap["reason"] not in ELIGIBLE_REASONS:
            rejected.append(gap)
            continue
        allowed_sources = set(gap["context"]["source_ids"])
        target = gap["target"]
        candidates = []
        for observation in observations:
            source_id = observation["subject"]["source_id"]
            if source_id not in allowed_sources:
                continue
            if target["kind"] == "node" and observation["subject"] != target["node"]:
                continue
            evidence = observation["evidence"]
            if not evidence:
                continue
            candidates.append(observation)

        if not candidates:
            rejected.append({
                **gap,
                "reason": "insufficient_evidence",
                "detail": gap["detail"] + " No matching current observation evidence was available for induction.",
            })
            continue

        for observation in candidates:
            subject = observation["subject"]
            source_states = sorted({
                (item["source_id"], item["content_state"])
                for item in observation["evidence"]
            })
            content_states = [
                {"source_id": source_id, "content_state": state}
                for source_id, state in source_states
            ]
            group_key = _canonical({
                "fact_type": gap["fact_type"],
                "subject": subject,
                "content_states": content_states,
                "context": observation["context"],
            })
            group = groups.setdefault(group_key, {
                "fact_type": gap["fact_type"],
                "subject": subject,
                "content_states": content_states,
                "context": observation["context"],
                "fields": set(),
                "observations": {},
                "unmet": {},
            })
            group["fields"].update(gap["fields"])
            group["observations"][observation["observation_id"]] = observation
            gap_key = _canonical(gap)
            group["unmet"][gap_key] = gap

    requests = []
    for key in sorted(groups):
        group = groups[key]
        fields = sorted(group["fields"])
        request_id = "induction-" + hashlib.sha256((key + _canonical(fields)).encode("utf-8")).hexdigest()[:24]
        request = {
            "kind": "induction_request",
            "request_id": request_id,
            "group": {
                "fact_type": group["fact_type"],
                "subject": group["subject"],
                "content_states": group["content_states"],
                "context": group["context"],
                "fields": fields,
            },
            "observations": [group["observations"][item] for item in sorted(group["observations"])],
            "existing_valid_facts": existing_valid_facts,
            "unmet": [group["unmet"][item] for item in sorted(group["unmet"])],
        }
        _validate(request_validator, request, "InductionRequest")
        requests.append(request)

    rejected.sort(key=lambda gap: (gap["fact_type"], tuple(gap["fields"]), gap["reason"], gap["detail"]))
    return {"requests": requests, "gaps": rejected}


def validate_induction_result(
    request: dict[str, Any],
    proposed_batch: dict[str, Any] | None,
    asset_root: str | Path | None = None,
) -> dict[str, Any]:
    """Validate and accept only request-bound, evidence-backed, non-conflicting additions."""
    assets = Path(asset_root) if asset_root else Path(__file__).resolve().parents[2] / "assets"
    request_validator, result_validator, batch_validator = _validators(assets)
    _validate(request_validator, request, "InductionRequest")
    codec = ContractCodec(assets)
    group = request["group"]
    base = request["existing_valid_facts"]
    observations = request["observations"]
    current_states = {
        item["source_id"]: item["content_state"] for item in group["content_states"]
    }
    allowed_evidence = {
        evidence["evidence_id"]: evidence
        for observation in observations
        for evidence in observation["evidence"]
    }
    gaps: list[dict[str, Any]] = []

    if proposed_batch is None:
        for gap in request["unmet"]:
            gaps.append({
                **gap,
                "target": {"kind": "node", "node": group["subject"]},
                "reason": "constructor_unavailable",
                "detail": "No induction provider result was supplied; no facts were inferred.",
            })
        result = {
            "kind": "induction_result",
            "batch": {
                "contract_version": base["contract_version"],
                "catalog_id": base["catalog_id"],
                "sources": base["sources"],
                "facts": [],
                "navigation": [],
                "direct_nodes": [],
                "conflicts": [],
            },
            "gaps": gaps,
        }
        _validate(result_validator, result, "InductionResult")
        return result

    _validate(batch_validator, proposed_batch, "proposed FactBatch")
    existing_assertions: dict[tuple[str, str], dict[str, Any]] = {}
    for fact in base["facts"]:
        if fact["node"] == group["subject"] and fact["fact_type"] == group["fact_type"]:
            for field, assertion in fact["fields"].items():
                existing_assertions[(fact["fact_type"], field)] = assertion

    accepted_facts: list[dict[str, Any]] = []
    accepted_fields: set[str] = set()
    conflicts: list[dict[str, Any]] = []
    for fact in proposed_batch["facts"]:
        if fact["fact_type"] != group["fact_type"] or fact["node"] != group["subject"]:
            continue
        accepted_fields_for_fact = {}
        for field, assertion in fact["fields"].items():
            if field not in group["fields"]:
                continue
            validity = assertion.get("validity", {})
            if validity.get("state") != "current":
                continue
            if not validity.get("sources") or any(
                state.get("source_id") not in current_states
                or state.get("content_state") != current_states[state["source_id"]]
                for state in validity["sources"]
            ):
                continue
            evidence = assertion.get("basis", {}).get("evidence", [])
            if not evidence or any(
                item.get("evidence_id") not in allowed_evidence
                or allowed_evidence[item["evidence_id"]] != item
                for item in evidence
            ):
                continue
            existing = existing_assertions.get((fact["fact_type"], field))
            if existing is not None:
                if existing == assertion:
                    accepted_fields.add(field)
                else:
                    conflicts.append({
                        "fact_type": fact["fact_type"],
                        "fields": [field],
                        "target": {"kind": "node", "node": group["subject"]},
                        "reason": "conflict",
                        "detail": f"Induction proposal conflicts with existing assertion for {field}; existing fact was preserved.",
                        "context": group["context"],
                        "coverage": assertion["coverage"],
                    })
                continue
            accepted_fields_for_fact[field] = assertion
            accepted_fields.add(field)
        if accepted_fields_for_fact:
            accepted = dict(fact)
            accepted["fields"] = accepted_fields_for_fact
            accepted_facts.append(accepted)

    remaining_gaps = []
    for gap in request["unmet"]:
        remaining = sorted(set(gap["fields"]) - accepted_fields)
        conflict_fields = {
            field for conflict in conflicts if conflict["fact_type"] == gap["fact_type"]
            for field in conflict["fields"]
        }
        remaining = sorted(set(remaining) | (set(gap["fields"]) & conflict_fields))
        if remaining:
            remaining_gaps.append({
                **gap,
                "fields": remaining,
                "target": {"kind": "node", "node": group["subject"]},
            })
    gaps.extend(remaining_gaps)
    gaps.extend(conflicts)

    sources_by_id = {source["source_id"]: source for source in base["sources"]}
    for source in proposed_batch["sources"]:
        existing = sources_by_id.get(source["source_id"])
        if existing is not None and existing != source:
            raise ValueError(f"source identity conflict in induction result: {source['source_id']}")
        sources_by_id[source["source_id"]] = source

    result_batch = {
        "contract_version": base["contract_version"],
        "catalog_id": base["catalog_id"],
        "sources": [sources_by_id[key] for key in sorted(sources_by_id)],
        "facts": accepted_facts,
        "navigation": [],
        "direct_nodes": [],
        "conflicts": [],
    }
    codec.validate_batch(result_batch)
    result = {"kind": "induction_result", "batch": result_batch, "gaps": gaps}
    _validate(result_validator, result, "InductionResult")
    return result
