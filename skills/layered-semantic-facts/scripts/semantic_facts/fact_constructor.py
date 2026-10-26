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
    direct_nodes: list[dict[str, Any]] = []
    project_children: list[dict[str, Any]] = []
    project_evidence: dict[str, dict[str, Any]] = {}

    for relative, parsed in parsed_files:
        if parsed.get("kind") != "parse_result":
            raise ValueError(f"invalid parser result for {relative}: kind must be parse_result")
        if parsed.get("gaps"):
            raise ValueError(f"cannot construct facts for {relative}: {parsed['gaps'][0]['detail']}")
        observations = parsed.get("observations", [])
        if not observations:
            raise ValueError(f"parser produced no file-level observation for {relative}")

        # Bind every observation to this exact source snapshot, project subject,
        # and file scope before any assertion is constructed.
        seen_observation_ids: set[str] = set()
        for observation in observations:
            observation_id = observation.get("observation_id")
            if not observation_id or observation_id in seen_observation_ids:
                raise ValueError(f"duplicate or missing observation_id in {relative}")
            seen_observation_ids.add(observation_id)
            subject = observation.get("subject", {})
            if subject.get("source_id") != source_id:
                raise ValueError(f"observation source mismatch in {relative}: {observation_id}")
            if subject.get("subject_id") != subject_id:
                raise ValueError(f"observation subject mismatch in {relative}: {observation_id}")
            evidence = observation.get("evidence", [])
            if not evidence:
                raise ValueError(f"observation has no evidence in {relative}: {observation_id}")
            for item in evidence:
                if item.get("source_id") != source_id:
                    raise ValueError(f"evidence source mismatch in {relative}: {item.get('evidence_id')}")
                if item.get("content_state") != content_state:
                    raise ValueError(f"evidence content state mismatch in {relative}: {item.get('evidence_id')}")
                locator = item.get("locator", "")
                locator_path = locator.split(":L", 1)[0]
                if locator_path != relative:
                    raise ValueError(f"evidence locator outside requested file {relative}: {locator}")

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
        language = "Rust" if relative.endswith(".rs") else "Python"
        context = {
            "source_ids": [source_id],
            "conditions": [],
            "environment": {"language": language},
            "language_semantics": [language + " syntax inventory; runtime behavior not inferred"],
        }
        coverage = {
            "domain": language + " syntax in " + relative,
            "checked": [relative],
            "excluded": [],
            "completeness": "complete",
            "method": "deterministic declaration parser via info_parser",
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
                    "limitations": ["Does not infer runtime behavior or intent", "Rust syntax inventory does not include type checking or macro expansion"] if language == "Rust" else ["Does not infer runtime behavior or intent"],
                },
                "value": value,
                "validity": {"state": "current", "sources": [{"source_id": source_id, "content_state": content_state}]},
            }

        file_node = {"source_id": source_id, "subject_id": subject_id, "node_id": node_id}
        project_children.append(file_node)
        for item in evidence_items:
            project_evidence[item["evidence_id"]] = item

        facts.append({
            "fact_id": fact_id,
            "node": file_node,
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

        declaration_children = []
        for observation in observations:
            child = observation["subject"]
            if child not in declaration_children:
                declaration_children.append(child)
        declaration_children.sort(key=lambda item: (item["source_id"], item["subject_id"], item["node_id"]))
        direct_nodes.append({
            "target": {"kind": "node", "node": file_node},
            "granularity": "L3",
            "boundary": f"Direct supported declarations in {relative}; syntax only, no descendant expansion.",
            "children": declaration_children,
            "assertion": assertion({
                "kind": "text",
                "text": f"Enumerated {len(declaration_children)} direct syntax declarations in {relative}.",
            }),
        })

    project_context = {
        "source_ids": [source_id],
        "conditions": [],
        "environment": {"languages": ",".join(sorted({"Rust" if path.endswith(".rs") else "Python" for path, _ in parsed_files}))},
        "language_semantics": ["Direct source-file inventory is limited to supported Python/Rust syntax files."],
    }
    project_coverage = {
        "domain": "direct supported source files in the exact requested root",
        "checked": sorted(relative for relative, _ in parsed_files),
        "excluded": list(source.get("excludes", [])),
        "completeness": "complete",
        "method": "deterministic Python/Rust source scan",
    }
    project_assertion = {
        "origin": "observed",
        "knowledge": "supported",
        "context": project_context,
        "coverage": project_coverage,
        "basis": {
            "evidence": [project_evidence[key] for key in sorted(project_evidence)],
            "premises": [],
            "method": "deterministic direct-source inventory",
            "limitations": ["Completeness applies only to supported Python/Rust source files under this exact root."],
        },
        "value": {"kind": "text", "text": f"Enumerated {len(project_children)} supported direct source files."},
        "validity": {"state": "current", "sources": [{"source_id": source_id, "content_state": content_state}]},
    }
    direct_nodes.append({
        "target": {"kind": "scope"},
        "granularity": "L3",
        "boundary": "Direct supported Python/Rust source files under the exact requested root; excluded directories are not scanned.",
        "children": sorted(project_children, key=lambda item: (item["source_id"], item["subject_id"], item["node_id"])),
        "assertion": project_assertion,
    })

    batch = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "sources": [source],
        "facts": facts,
        "navigation": [],
        "direct_nodes": direct_nodes,
        "conflicts": [],
    }
    codec.validate_batch(batch)
    return batch
