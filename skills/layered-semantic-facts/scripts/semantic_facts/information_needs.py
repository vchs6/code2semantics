"""Load and validate the fixed development-time information-needs catalogue."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class InformationNeedsError(ValueError):
    """The fixed information-needs catalogue is missing or invalid."""


def load_information_needs(asset_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(asset_root) if asset_root else Path(__file__).resolve().parents[2] / "assets"
    schema_path = root / "information-needs.schema.json"
    catalogue_path = root / "information-needs.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
        fact_catalogue = json.loads((root / "fact-catalog.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InformationNeedsError(f"cannot load information-needs assets: {error}") from error

    error = next(Draft202012Validator(schema).iter_errors(catalogue), None)
    if error:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise InformationNeedsError(f"catalogue {pointer}: {error.message}")

    ids: set[str] = set()
    fields_by_type = {
        fact["id"]: set(fact["fields"])
        for fact in fact_catalogue["fact_types"]
    }
    for index, need in enumerate(catalogue["needs"]):
        need_id = need["need_id"]
        if need_id in ids:
            raise InformationNeedsError(f"/needs/{index}/need_id: duplicate need_id {need_id}")
        ids.add(need_id)
        unknown_fields = set(need["fields"]) - fields_by_type.get(need["fact_type"], set())
        if unknown_fields:
            raise InformationNeedsError(
                f"/needs/{index}/fields: fields not defined for {need['fact_type']}: {sorted(unknown_fields)}"
            )
    return catalogue
