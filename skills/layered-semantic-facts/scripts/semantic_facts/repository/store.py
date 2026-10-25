"""SQLite fact-set storage boundary.

The repository accepts a validated FactBatch and a caller-complete query.  It
does not inspect sources, authorize requests, infer missing query conditions,
or manufacture a response envelope.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .contract import ContractCodec
from .types import CommitReceipt, StoredRecord, WriteConflict


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class Repository:
    def __init__(self, path: str | Path, schema_root: str | Path | None = None):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        if schema_root is None:
            schema_root = Path(__file__).resolve().parents[3] / "assets"
        self.codec = ContractCodec(Path(schema_root))
        self._initialized = False

    def close(self) -> None:
        self.connection.close()

    def _ensure_schema(self) -> None:
        if self._initialized:
            return
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS entities (
                entity_key TEXT PRIMARY KEY, source_id TEXT NOT NULL,
                subject_id TEXT NOT NULL, node_id TEXT, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS facts (
                fact_key TEXT PRIMARY KEY, source_id TEXT NOT NULL,
                subject_id TEXT NOT NULL, node_id TEXT NOT NULL,
                fact_id TEXT NOT NULL, fact_type TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attributes (
                attribute_key TEXT PRIMARY KEY, fact_key TEXT NOT NULL,
                field_name TEXT NOT NULL, payload TEXT NOT NULL,
                FOREIGN KEY(fact_key) REFERENCES facts(fact_key)
            );
            CREATE TABLE IF NOT EXISTS relations (
                relation_key TEXT PRIMARY KEY, owner_key TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS submissions (
                submission_key TEXT PRIMARY KEY, digest TEXT NOT NULL,
                receipt TEXT NOT NULL
            );
            """
        )
        self.connection.commit()
        self._initialized = True

    @staticmethod
    def _digest(batch: dict[str, Any]) -> str:
        return hashlib.sha256(_canonical(batch).encode("utf-8")).hexdigest()

    def write(self, batch: dict[str, Any], submission_key: str) -> CommitReceipt:
        # Validate before creating schema or opening a write transaction.
        records = self.codec.decode(batch)
        digest = self._digest(batch)
        self._ensure_schema()
        existing = self.connection.execute(
            "SELECT digest, receipt FROM submissions WHERE submission_key = ?",
            (submission_key,),
        ).fetchone()
        if existing:
            if existing[0] != digest:
                raise WriteConflict(None, "submission key already has different content")
            payload = json.loads(existing[1])
            return CommitReceipt(submission_key, payload["digest"], tuple())

        record = records[0]
        affected = tuple()
        try:
            with self.connection:
                self._insert_record(record)
                receipt = {"submission_key": submission_key, "digest": digest}
                self.connection.execute(
                    "INSERT INTO submissions(submission_key, digest, receipt) VALUES (?, ?, ?)",
                    (submission_key, digest, _canonical(receipt)),
                )
        except sqlite3.IntegrityError as error:
            raise WriteConflict(None, str(error)) from error
        return CommitReceipt(submission_key, digest, affected)

    def _insert_record(self, record: StoredRecord) -> None:
        for row in record.sources:
            value = row.value
            self.connection.execute(
                "INSERT OR REPLACE INTO sources(source_id, payload) VALUES (?, ?)",
                (value["source_id"], row.payload),
            )
        for row in record.entities:
            value = row.value
            self.connection.execute(
                "INSERT OR REPLACE INTO entities(entity_key, source_id, subject_id, node_id, payload) VALUES (?, ?, ?, ?, ?)",
                (row.key, value["source_id"], value["subject_id"], value.get("node_id"), row.payload),
            )
        for row in record.facts:
            value = row.value
            node = value["node"]
            self.connection.execute(
                "INSERT OR REPLACE INTO facts(fact_key, source_id, subject_id, node_id, fact_id, fact_type, payload) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (row.key, node["source_id"], node["subject_id"], node["node_id"], value["fact_id"], value["fact_type"], row.payload),
            )
        for row in record.attributes:
            self.connection.execute(
                "INSERT OR REPLACE INTO attributes(attribute_key, fact_key, field_name, payload) VALUES (?, ?, ?, ?)",
                (row.key, row.fact_key, row.field_path.removeprefix("/fields/"), row.payload),
            )
        for row in record.relations:
            self.connection.execute(
                "INSERT OR REPLACE INTO relations(relation_key, owner_key, payload) VALUES (?, ?, ?)",
                (row.key, row.owner_key, row.payload),
            )

    def read(self, query: dict[str, Any]) -> dict[str, Any]:
        self._validate_query(query)
        self._ensure_schema()
        target = query["target"].get("node")
        selections = query["selections"]
        params: list[Any] = []
        sql = "SELECT fact_key, source_id, subject_id, node_id, fact_id, fact_type, payload FROM facts WHERE 1=1"
        if target:
            sql += " AND source_id = ? AND subject_id = ? AND node_id = ?"
            params.extend((target["source_id"], target["subject_id"], target["node_id"]))
        types = tuple(selection["fact_type"] for selection in selections)
        sql += " AND fact_type IN (" + ",".join("?" for _ in types) + ")"
        params.extend(types)
        rows = self.connection.execute(sql, params).fetchall()
        selected: list[dict[str, Any]] = []
        source_ids: set[str] = set()
        for row in rows:
            value = json.loads(row[6])
            selection = next(item for item in selections if item["fact_type"] == row[5])
            wanted = set(selection["fields"])
            fields = {}
            for name, payload in self.connection.execute(
                "SELECT field_name, payload FROM attributes WHERE fact_key = ?", (row[0],)
            ):
                if name in wanted:
                    fields[name] = json.loads(payload)
            if fields:
                value["fields"] = fields
                selected.append(value)
                source_ids.add(row[1])
        sources = [json.loads(payload) for source_id, payload in self.connection.execute(
            "SELECT source_id, payload FROM sources WHERE source_id IN ({})".format(",".join("?" for _ in source_ids)), tuple(source_ids)
        )] if source_ids else []
        return {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "sources": sources,
            "facts": selected,
            "navigation": [],
            "direct_nodes": [],
            "conflicts": [],
        }

    @staticmethod
    def _validate_query(query: dict[str, Any]) -> None:
        required = {"contract_version", "catalog_id", "request_id", "scope", "target", "granularity", "selections", "budget"}
        if not isinstance(query, dict) or not required <= query.keys():
            raise ValueError("query is incomplete")

