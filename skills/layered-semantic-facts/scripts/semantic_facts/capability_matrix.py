"""Deterministic maintenance and candidate queries for the capability matrix."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class MatrixValidationError(ValueError):
    """A matrix document failed schema or repository-level validation."""

    def __init__(self, location: str, message: str):
        self.location = location or "/"
        self.message = message
        super().__init__(f"{self.location}: {message}")


class CapabilityMatrix:
    """Load, validate, atomically maintain, and query one matrix document."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        schema_path = Path(__file__).resolve().parents[2] / "assets" / "capability-matrix.schema.json"
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise MatrixValidationError("/", f"cannot load capability matrix schema: {error}") from error
        self._validator = Draft202012Validator(schema)

    def validate(self, document: Any) -> None:
        error = next(self._validator.iter_errors(document), None)
        if error is not None:
            location = "".join(f"/{str(part).replace('~', '~0').replace('/', '~1')}" for part in error.absolute_path)
            raise MatrixValidationError(location or "/", error.message)
        seen: dict[str, int] = {}
        for index, entry in enumerate(document["entries"]):
            tool_id = entry["tool_id"]
            if tool_id in seen:
                raise MatrixValidationError(f"/entries/{index}/tool_id", f"duplicate tool_id; first entry is {seen[tool_id]}")
            seen[tool_id] = index

    def load(self) -> dict[str, Any]:
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise MatrixValidationError("/", f"cannot read matrix: {error}") from error
        self.validate(document)
        return document

    def replace(self, entries: list[dict[str, Any]]) -> bool:
        document = {"contract_version": "1.0.0", "entries": entries}
        self.validate(document)
        if self.path.exists() and self.load() == document:
            return False
        self._atomic_write(document)
        return True

    def upsert(self, entry: dict[str, Any]) -> bool:
        current = self.load() if self.path.exists() else {"contract_version": "1.0.0", "entries": []}
        entries = list(current["entries"])
        for index, existing in enumerate(entries):
            if existing["tool_id"] == entry.get("tool_id"):
                if existing == entry:
                    return False
                entries[index] = entry
                return self.replace(entries)
        entries.append(entry)
        return self.replace(entries)

    def query(
        self,
        information_need_ids: list[str],
        language: str,
        platform: str,
        environment: str,
    ) -> list[dict[str, Any]]:
        document = self.load()
        requested = set(information_need_ids)
        known_needs = {need for entry in document["entries"] for need in entry["information_need_ids"]}
        unknown = sorted(requested - known_needs)
        if unknown:
            raise MatrixValidationError("/information_need_ids", f"unknown information need: {unknown[0]}")
        results = [
            entry
            for entry in document["entries"]
            if requested.issubset(entry["information_need_ids"])
            and language in entry["languages"]
            and platform in entry["platforms"]
            and environment == entry["environment"]
        ]
        return sorted(results, key=lambda entry: entry["tool_id"])

    def _atomic_write(self, document: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self.path.parent, prefix=f".{self.path.name}.", delete=False
        )
        temporary = Path(handle.name)
        try:
            with handle:
                json.dump(document, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

