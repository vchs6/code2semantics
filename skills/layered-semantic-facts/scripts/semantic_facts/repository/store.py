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
from typing import Any, Sequence

from .contract import ContractCodec
from .types import CommitReceipt, SourceRow, StoredRecord, WriteConflict


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

    def backup(self, destination: str | Path) -> None:
        """Create a consistent SQLite backup of the current repository."""
        destination_path = Path(destination)
        if destination_path.resolve() == Path(self.path).resolve():
            raise ValueError("backup destination must differ from the repository path")
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(destination_path)) as target:
            self.connection.backup(target)

    def restore(self, source: str | Path) -> None:
        """Restore a validated SQLite backup without touching state on validation failure."""
        source_path = Path(source)
        if not source_path.is_file():
            raise ValueError("backup file does not exist")
        if source_path.resolve() == Path(self.path).resolve():
            raise ValueError("restore source must differ from the repository path")

        try:
            uri = "file:" + source_path.resolve().as_posix() + "?mode=ro"
            with sqlite3.connect(uri, uri=True) as backup:
                integrity = backup.execute("PRAGMA integrity_check").fetchone()
                if not integrity or integrity[0] != "ok":
                    raise ValueError("backup failed SQLite integrity check")
                tables = {row[0] for row in backup.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
                expected = {"sources", "entities", "facts", "attributes", "relations", "submissions", "source_heads"}
                if tables and not expected.issubset(tables):
                    raise ValueError("backup does not contain the repository schema")
                backup.backup(self.connection)
        except sqlite3.DatabaseError as error:
            raise ValueError("invalid SQLite backup: " + str(error)) from error

        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialized = False

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
            CREATE TABLE IF NOT EXISTS source_heads (
                root TEXT PRIMARY KEY, source_id TEXT NOT NULL
            );
            """
        )
        # Bootstrap current pointers for older databases; never remove historical facts.
        for _, payload in self.connection.execute(
            "SELECT source_id, payload FROM sources ORDER BY rowid DESC"
        ).fetchall():
            source = json.loads(payload)
            self.connection.execute(
                "INSERT OR IGNORE INTO source_heads(root, source_id) VALUES (?, ?)",
                (str(Path(source["root"]).resolve()), source["source_id"]),
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
            # Re-observing an old snapshot can make it current again; fact history stays.
            with self.connection:
                self._mark_current_sources(records[0].sources)
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

    def _mark_current_sources(self, sources: Sequence[SourceRow]) -> None:
        for row in sources:
            value = row.value
            self.connection.execute(
                "INSERT INTO source_heads(root, source_id) VALUES (?, ?) "
                "ON CONFLICT(root) DO UPDATE SET source_id = excluded.source_id",
                (str(Path(value["root"]).resolve()), value["source_id"]),
            )

    def _insert_record(self, record: StoredRecord) -> None:
        for row in record.sources:
            value = row.value
            self.connection.execute(
                "INSERT OR IGNORE INTO sources(source_id, payload) VALUES (?, ?)",
                (value["source_id"], row.payload),
            )
        self._mark_current_sources(record.sources)
        for row in record.entities:
            value = row.value
            self.connection.execute(
                "INSERT OR IGNORE INTO entities(entity_key, source_id, subject_id, node_id, payload) VALUES (?, ?, ?, ?, ?)",
                (row.key, value["source_id"], value["subject_id"], value.get("node_id"), row.payload),
            )
        for row in record.facts:
            value = row.value
            node = value["node"]
            self.connection.execute(
                "INSERT INTO facts(fact_key, source_id, subject_id, node_id, fact_id, fact_type, payload) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (row.key, node["source_id"], node["subject_id"], node["node_id"], value["fact_id"], value["fact_type"], row.payload),
            )
        for row in record.attributes:
            self.connection.execute(
                "INSERT INTO attributes(attribute_key, fact_key, field_name, payload) VALUES (?, ?, ?, ?)",
                (row.key, row.fact_key, row.field_path.removeprefix("/fields/"), row.payload),
            )
        for row in record.relations:
            self.connection.execute(
                "INSERT INTO relations(relation_key, owner_key, payload) VALUES (?, ?, ?)",
                (row.key, row.owner_key, row.payload),
            )

    def read(self, query: dict[str, Any]) -> dict[str, Any]:
        self._validate_query(query)
        self._ensure_schema()
        target = query["target"].get("node")
        selections = query["selections"]

        if target:
            source_row = self.connection.execute(
                "SELECT payload FROM sources WHERE source_id = ?", (target["source_id"],)
            ).fetchone()
            if source_row:
                source = json.loads(source_row[0])
                head = self.connection.execute(
                    "SELECT source_id FROM source_heads WHERE root = ?",
                    (str(Path(source["root"]).resolve()),),
                ).fetchone()
                current_source_ids = {head[0]} if head else set()
            else:
                current_source_ids = set()
        else:
            directories = {
                str(Path(directory).resolve())
                for directory in query["scope"].get("directories", [])
            }
            current_source_ids = {
                source_id for root, source_id in self.connection.execute("SELECT root, source_id FROM source_heads")
                if root in directories
            }

        params: list[Any] = []
        sql = "SELECT fact_key, source_id, subject_id, node_id, fact_id, fact_type, payload FROM facts WHERE 1=1"
        if target:
            if current_source_ids:
                sql += " AND source_id = ? AND subject_id = ? AND node_id = ?"
                params.extend((next(iter(current_source_ids)), target["subject_id"], target["node_id"]))
            else:
                sql += " AND 1=0"
        elif current_source_ids:
            placeholders = ",".join("?" for _ in current_source_ids)
            sql += f" AND source_id IN ({placeholders})"
            params.extend(sorted(current_source_ids))
        else:
            sql += " AND 1=0"

        types = tuple(selection["fact_type"] for selection in selections)
        sql += " AND fact_type IN (" + ",".join("?" for _ in types) + ")"
        params.extend(types)
        rows = self.connection.execute(sql, params).fetchall()
        selected: list[dict[str, Any]] = []
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

        sources = []
        if current_source_ids:
            placeholders = ",".join("?" for _ in current_source_ids)
            sources = [
                json.loads(payload)
                for _, payload in self.connection.execute(
                    f"SELECT source_id, payload FROM sources WHERE source_id IN ({placeholders})",
                    tuple(sorted(current_source_ids)),
                )
            ]
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

