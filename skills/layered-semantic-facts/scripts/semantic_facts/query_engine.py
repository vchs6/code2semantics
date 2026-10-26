"""Deterministic query response projection for the currently supported syntax facts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .repository.store import Repository


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


def execute_query(query: dict[str, Any], repository: Repository, asset_root: str | Path | None = None) -> dict[str, Any]:
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

    stored = repository.read(query)
    sources = stored["sources"]
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
        "direct_nodes": stored["direct_nodes"],
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
