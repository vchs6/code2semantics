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

    def _validity_event_states(self) -> dict[tuple[str, str], str]:
        self._ensure_schema()
        states: dict[tuple[str, str], str] = {}
        for kind, key, state in self.connection.execute(
            "SELECT target_kind, target_key, state FROM validity_events ORDER BY event_id"
        ):
            states[(kind, key)] = state
        return states

    def record_validity_event(
        self,
        target_kind: str,
        target_key: str,
        state: str,
        reason: str | None = None,
    ) -> int:
        """Append an explicit validity event; never delete the target record."""
        tables = {
            "fact": ("facts", "fact_key"),
            "field": ("attributes", "attribute_key"),
            "relation": ("relations", "relation_key"),
            "evidence": ("evidence", "evidence_key"),
            "premise": ("premises", "premise_key"),
            "conflict": ("conflicts", "conflict_key"),
            "inventory": ("inventories", "inventory_key"),
        }
        allowed_states = {"current", "modified", "deleted", "premise_invalid", "unknown"}
        if target_kind not in tables:
            raise ValueError(f"unsupported validity target kind: {target_kind}")
        if state not in allowed_states:
            raise ValueError(f"unsupported validity state: {state}")
        if not target_key:
            raise ValueError("target_key must not be empty")
        if state != "current" and not reason:
            raise ValueError("a non-current validity state requires a reason")
        self._ensure_schema()
        table, key_column = tables[target_kind]
        exists = self.connection.execute(
            f"SELECT 1 FROM {table} WHERE {key_column} = ?", (target_key,)
        ).fetchone()
        if not exists:
            raise ValueError(f"{target_kind} target does not exist: {target_key}")
        with self.connection:
            cursor = self.connection.execute(
                "INSERT INTO validity_events(target_kind, target_key, state, reason) VALUES (?, ?, ?, ?)",
                (target_kind, target_key, state, reason),
            )
        return int(cursor.lastrowid)

    def invalidate_fact(self, fact_id: str, reason: str, state: str = "modified") -> int:
        self._ensure_schema()
        row = self.connection.execute("SELECT fact_key FROM facts WHERE fact_id = ?", (fact_id,)).fetchone()
        if not row:
            raise ValueError(f"fact does not exist: {fact_id}")
        return self.record_validity_event("fact", row[0], state, reason)

    def invalidate_field(self, fact_id: str, field_name: str, reason: str, state: str = "modified") -> int:
        self._ensure_schema()
        row = self.connection.execute(
            "SELECT a.attribute_key FROM attributes a JOIN facts f ON f.fact_key = a.fact_key "
            "WHERE f.fact_id = ? AND a.field_name = ?",
            (fact_id, field_name),
        ).fetchone()
        if not row:
            raise ValueError(f"field does not exist: {fact_id}.{field_name}")
        return self.record_validity_event("field", row[0], state, reason)

    def invalidate_relation(self, relation_key: str, reason: str, state: str = "modified") -> int:
        return self.record_validity_event("relation", relation_key, state, reason)

    def invalidate_evidence(self, source_id: str, evidence_id: str, reason: str, state: str = "modified") -> int:
        self._ensure_schema()
        evidence_key = None
        for key, payload in self.connection.execute("SELECT evidence_key, payload FROM evidence"):
            item = json.loads(payload)
            if item.get("source_id") == source_id and item.get("evidence_id") == evidence_id:
                evidence_key = key
                break
        if evidence_key is None:
            raise ValueError(f"evidence does not exist: {source_id}.{evidence_id}")
        return self.record_validity_event("evidence", evidence_key, state, reason)

    def invalidate_conflict(self, conflict_id: str, reason: str, state: str = "modified") -> int:
        self._ensure_schema()
        conflict_key = None
        for key, payload in self.connection.execute("SELECT conflict_key, payload FROM conflicts"):
            if json.loads(payload).get("conflict_id") == conflict_id:
                conflict_key = key
                break
        if conflict_key is None:
            raise ValueError(f"conflict does not exist: {conflict_id}")
        return self.record_validity_event("conflict", conflict_key, state, reason)

    def export_current(self) -> dict[str, Any]:
        """Export only current source-head facts; historical rows remain stored locally."""
        self._ensure_schema()
        heads = {
            source_id: root
            for root, source_id in self.connection.execute("SELECT root, source_id FROM source_heads")
        }
        if not heads:
            raise ValueError("repository has no current source snapshot to export")

        current_sources = [
            json.loads(payload)
            for source_id, payload in self.connection.execute(
                "SELECT source_id, payload FROM sources"
            )
            if source_id in heads
        ]
        current_states = {source["source_id"]: source["content_state"] for source in current_sources}
        event_states = self._validity_event_states()
        evidence_key_by_identity = {
            (item["source_id"], item["evidence_id"]): key
            for key, payload in self.connection.execute("SELECT evidence_key, payload FROM evidence")
            for item in [json.loads(payload)]
        }

        def active(kind: str, key: str) -> bool:
            return event_states.get((kind, key), "current") == "current"

        def is_current(assertion: dict[str, Any]) -> bool:
            validity = assertion.get("validity", {})
            if validity.get("state") != "current":
                return False
            validity_sources = validity.get("sources", [])
            if not validity_sources or any(
                item.get("source_id") not in current_states
                or item.get("content_state") != current_states[item.get("source_id")]
                for item in validity_sources
            ):
                return False
            return all(
                item.get("source_id") in current_states
                and item.get("content_state") == current_states[item.get("source_id")]
                and active("evidence", evidence_key_by_identity.get((item.get("source_id"), item.get("evidence_id")), ""))
                for item in assertion.get("basis", {}).get("evidence", [])
            )

        facts: list[dict[str, Any]] = []
        for fact_key, source_id, payload in self.connection.execute(
            "SELECT fact_key, source_id, payload FROM facts"
        ):
            if source_id not in current_states or not active("fact", fact_key):
                continue
            fact = json.loads(payload)
            fields: dict[str, Any] = {}
            for attribute_key, name, field_payload in self.connection.execute(
                "SELECT attribute_key, field_name, payload FROM attributes WHERE fact_key = ?", (fact_key,)
            ):
                assertion = json.loads(field_payload)
                if active("field", attribute_key) and is_current(assertion):
                    fields[name] = assertion
            if fields:
                fact["fields"] = fields
                facts.append(fact)

        navigation = []
        for relation_key, payload in self.connection.execute(
            "SELECT relation_key, payload FROM relations WHERE navigation = 1"
        ):
            if not active("relation", relation_key):
                continue
            edge = json.loads(payload)
            if edge.get("source", {}).get("source_id") in current_states:
                navigation.append(edge)

        direct_nodes = []
        for inventory_key, payload in self.connection.execute("SELECT inventory_key, payload FROM inventories"):
            if not active("inventory", inventory_key):
                continue
            inventory = json.loads(payload)
            assertion = inventory.get("assertion", {})
            source_ids = set(assertion.get("context", {}).get("source_ids", []))
            if source_ids.intersection(current_states) and is_current(assertion):
                direct_nodes.append(inventory)

        conflicts = []
        for conflict_key, payload in self.connection.execute("SELECT conflict_key, payload FROM conflicts"):
            if not active("conflict", conflict_key):
                continue
            conflict = json.loads(payload)
            source_ids = set(conflict.get("context", {}).get("source_ids", []))
            if source_ids.intersection(current_states):
                conflicts.append(conflict)

        batch = {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "sources": sorted(current_sources, key=lambda item: (item["root"], item["source_id"])),
            "facts": sorted(facts, key=lambda item: (item["fact_type"], item["fact_id"])),
            "navigation": sorted(navigation, key=_canonical),
            "direct_nodes": sorted(direct_nodes, key=_canonical),
            "conflicts": sorted(conflicts, key=lambda item: item["conflict_id"]),
        }
        self.codec.validate_batch(batch)
        return batch

    def import_current(self, batch: dict[str, Any], submission_key: str) -> CommitReceipt:
        """Append a validated current FactBatch; never clear or replace existing rows."""
        self.codec.validate_batch(batch)
        return self.write(batch, submission_key)

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
            CREATE TABLE IF NOT EXISTS attribute_versions (
                version_key TEXT PRIMARY KEY, attribute_key TEXT NOT NULL,
                fact_key TEXT NOT NULL, field_name TEXT NOT NULL, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS validity_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_kind TEXT NOT NULL, target_key TEXT NOT NULL,
                state TEXT NOT NULL, reason TEXT
            );
            CREATE TABLE IF NOT EXISTS relations (
                relation_key TEXT PRIMARY KEY, owner_key TEXT NOT NULL,
                payload TEXT NOT NULL, navigation INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS submissions (
                submission_key TEXT PRIMARY KEY, digest TEXT NOT NULL,
                receipt TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS source_heads (
                root TEXT PRIMARY KEY, source_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_key TEXT PRIMARY KEY, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence_links (
                link_key TEXT PRIMARY KEY, owner_key TEXT NOT NULL,
                evidence_key TEXT NOT NULL, pointer TEXT NOT NULL,
                relation TEXT NOT NULL, ordinal INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS premises (
                premise_key TEXT PRIMARY KEY, owner_key TEXT NOT NULL,
                target_kind TEXT NOT NULL, target_key TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inventories (
                inventory_key TEXT PRIMARY KEY, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conflicts (
                conflict_key TEXT PRIMARY KEY, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conflict_links (
                link_key TEXT PRIMARY KEY, conflict_key TEXT NOT NULL,
                target_kind TEXT NOT NULL, target_key TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            """
        )
        relation_columns = {
            row[1] for row in self.connection.execute("PRAGMA table_info(relations)")
        }
        if "navigation" not in relation_columns:
            self.connection.execute(
                "ALTER TABLE relations ADD COLUMN navigation INTEGER NOT NULL DEFAULT 0"
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
        # Every persisted row is immutable. Repeated observations may append missing
        # attributes, but a conflicting identity/payload is rejected, never replaced.
        for row in record.sources:
            value = row.value
            self.connection.execute(
                "INSERT OR IGNORE INTO sources(source_id, payload) VALUES (?, ?)",
                (value["source_id"], row.payload),
            )
            existing = self.connection.execute(
                "SELECT payload FROM sources WHERE source_id = ?", (value["source_id"],)
            ).fetchone()
            if not existing or existing[0] != row.payload:
                raise WriteConflict(None, f"source identity conflict: {value['source_id']}")

        self._mark_current_sources(record.sources)

        for row in record.entities:
            value = row.value
            values = (row.key, value["source_id"], value["subject_id"], value.get("node_id"), row.payload)
            self.connection.execute(
                "INSERT OR IGNORE INTO entities(entity_key, source_id, subject_id, node_id, payload) VALUES (?, ?, ?, ?, ?)",
                values,
            )
            existing = self.connection.execute(
                "SELECT entity_key, source_id, subject_id, node_id, payload FROM entities WHERE entity_key = ?",
                (row.key,),
            ).fetchone()
            if not existing or tuple(existing) != values:
                raise WriteConflict(None, f"entity identity conflict: {row.key}")

        for row in record.facts:
            value = row.value
            node = value["node"]
            values = (
                row.key, node["source_id"], node["subject_id"], node["node_id"],
                value["fact_id"], value["fact_type"], row.payload,
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO facts(fact_key, source_id, subject_id, node_id, fact_id, fact_type, payload) VALUES (?, ?, ?, ?, ?, ?, ?)",
                values,
            )
            existing = self.connection.execute(
                "SELECT fact_key, source_id, subject_id, node_id, fact_id, fact_type, payload FROM facts WHERE fact_key = ?",
                (row.key,),
            ).fetchone()
            if not existing or tuple(existing) != values:
                raise WriteConflict(None, f"fact identity conflict: {row.key}")

        for row in record.attributes:
            field_name = row.field_path.removeprefix("/fields/")
            values = (row.key, row.fact_key, field_name, row.payload)
            version_key = hashlib.sha256(_canonical((row.key, row.payload)).encode("utf-8")).hexdigest()
            self.connection.execute(
                "INSERT OR IGNORE INTO attribute_versions(version_key, attribute_key, fact_key, field_name, payload) "
                "VALUES (?, ?, ?, ?, ?)",
                (version_key, *values),
            )
            existing = self.connection.execute(
                "SELECT attribute_key, fact_key, field_name, payload FROM attributes WHERE attribute_key = ?",
                (row.key,),
            ).fetchone()
            if existing is None:
                self.connection.execute(
                    "INSERT INTO attributes(attribute_key, fact_key, field_name, payload) VALUES (?, ?, ?, ?)",
                    values,
                )
            elif tuple(existing[:3]) != values[:3]:
                raise WriteConflict(None, f"attribute identity conflict: {row.key}")
            elif existing[3] != row.payload:
                # Keep the logical field key stable while retaining every prior
                # assertion version in attribute_versions.
                self.connection.execute(
                    "UPDATE attributes SET payload = ? WHERE attribute_key = ?",
                    (row.payload, row.key),
                )
                assertion = json.loads(row.payload)
                if assertion.get("validity", {}).get("state") == "current":
                    self.connection.execute(
                        "INSERT INTO validity_events(target_kind, target_key, state, reason) VALUES (?, ?, ?, ?)",
                        ("field", row.key, "current", "new validated assertion version appended"),
                    )

        for row in record.relations:
            values = (row.key, row.owner_key, row.payload, int(row.navigation))
            self.connection.execute(
                "INSERT OR IGNORE INTO relations(relation_key, owner_key, payload, navigation) VALUES (?, ?, ?, ?)",
                values,
            )
            existing = self.connection.execute(
                "SELECT relation_key, owner_key, payload, navigation FROM relations WHERE relation_key = ?",
                (row.key,),
            ).fetchone()
            if not existing or tuple(existing) != values:
                raise WriteConflict(None, f"relation conflict: {row.key}")

        for row in record.evidence:
            values = (row.key, row.payload)
            self.connection.execute(
                "INSERT OR IGNORE INTO evidence(evidence_key, payload) VALUES (?, ?)", values
            )
            existing = self.connection.execute(
                "SELECT evidence_key, payload FROM evidence WHERE evidence_key = ?", (row.key,)
            ).fetchone()
            if not existing or tuple(existing) != values:
                raise WriteConflict(None, f"evidence conflict: {row.key}")

        for row in record.evidence_links:
            link_key = _canonical((row.owner_key, row.evidence_key, row.pointer, row.relation))
            values = (link_key, row.owner_key, row.evidence_key, row.pointer, row.relation, row.ordinal)
            self.connection.execute(
                "INSERT OR IGNORE INTO evidence_links(link_key, owner_key, evidence_key, pointer, relation, ordinal) "
                "VALUES (?, ?, ?, ?, ?, ?)", values
            )
            existing = self.connection.execute(
                "SELECT link_key, owner_key, evidence_key, pointer, relation, ordinal "
                "FROM evidence_links WHERE link_key = ?", (link_key,)
            ).fetchone()
            if not existing or tuple(existing) != values:
                raise WriteConflict(None, f"evidence link conflict: {link_key}")

        for row in record.premises:
            values = (row.key, row.owner_key, row.target.kind, row.target.key, row.payload)
            self.connection.execute(
                "INSERT OR IGNORE INTO premises(premise_key, owner_key, target_kind, target_key, payload) "
                "VALUES (?, ?, ?, ?, ?)", values
            )
            existing = self.connection.execute(
                "SELECT premise_key, owner_key, target_kind, target_key, payload FROM premises WHERE premise_key = ?",
                (row.key,),
            ).fetchone()
            if not existing or tuple(existing) != values:
                raise WriteConflict(None, f"premise conflict: {row.key}")

        for row in record.inventories:
            values = (row.key, row.payload)
            self.connection.execute(
                "INSERT OR IGNORE INTO inventories(inventory_key, payload) VALUES (?, ?)", values
            )
            existing = self.connection.execute(
                "SELECT inventory_key, payload FROM inventories WHERE inventory_key = ?", (row.key,)
            ).fetchone()
            if not existing or tuple(existing) != values:
                raise WriteConflict(None, f"inventory conflict: {row.key}")

        for row in record.conflicts:
            values = (row.key, row.payload)
            self.connection.execute(
                "INSERT OR IGNORE INTO conflicts(conflict_key, payload) VALUES (?, ?)", values
            )
            existing = self.connection.execute(
                "SELECT conflict_key, payload FROM conflicts WHERE conflict_key = ?", (row.key,)
            ).fetchone()
            if not existing or tuple(existing) != values:
                raise WriteConflict(None, f"conflict identity: {row.key}")

        for row in record.conflict_links:
            values = (row.key, row.conflict_key, row.target.kind, row.target.key, row.payload)
            self.connection.execute(
                "INSERT OR IGNORE INTO conflict_links(link_key, conflict_key, target_kind, target_key, payload) "
                "VALUES (?, ?, ?, ?, ?)", values
            )
            existing = self.connection.execute(
                "SELECT link_key, conflict_key, target_kind, target_key, payload "
                "FROM conflict_links WHERE link_key = ?", (row.key,)
            ).fetchone()
            if not existing or tuple(existing) != values:
                raise WriteConflict(None, f"conflict link: {row.key}")

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

        current_states = {
            source_id: json.loads(payload)["content_state"]
            for source_id, payload in self.connection.execute("SELECT source_id, payload FROM sources")
            if source_id in current_source_ids
        }
        event_states = self._validity_event_states()
        evidence_key_by_identity = {
            (item["source_id"], item["evidence_id"]): key
            for key, payload in self.connection.execute("SELECT evidence_key, payload FROM evidence")
            for item in [json.loads(payload)]
        }

        def active(kind: str, key: str) -> bool:
            return event_states.get((kind, key), "current") == "current"

        def assertion_is_current(assertion: dict[str, Any]) -> bool:
            validity = assertion.get("validity")
            if not isinstance(validity, dict) or validity.get("state") != "current":
                return False
            validity_sources = validity.get("sources", [])
            if not validity_sources or any(
                item.get("source_id") not in current_states
                or item.get("content_state") != current_states[item.get("source_id")]
                for item in validity_sources
            ):
                return False
            evidence = assertion.get("basis", {}).get("evidence", [])
            return all(
                item.get("source_id") in current_states
                and item.get("content_state") == current_states[item.get("source_id")]
                and active("evidence", evidence_key_by_identity.get((item.get("source_id"), item.get("evidence_id")), ""))
                for item in evidence
            )

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
            if not active("fact", row[0]):
                continue
            value = json.loads(row[6])
            selection = next(item for item in selections if item["fact_type"] == row[5])
            wanted = set(selection["fields"])
            fields = {}
            for attribute_key, name, payload in self.connection.execute(
                "SELECT attribute_key, field_name, payload FROM attributes WHERE fact_key = ?", (row[0],)
            ):
                if name in wanted and active("field", attribute_key):
                    assertion = json.loads(payload)
                    if assertion_is_current(assertion):
                        fields[name] = assertion
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
        navigation = []
        for payload, is_navigation in self.connection.execute(
            "SELECT payload, navigation FROM relations WHERE navigation = 1"
        ):
            edge = json.loads(payload)
            source_ref = edge.get("source", {})
            if source_ref.get("source_id") not in current_source_ids:
                continue
            if target and source_ref != target:
                continue
            navigation.append(edge)

        direct_nodes = []
        for (payload,) in self.connection.execute("SELECT payload FROM inventories"):
            inventory = json.loads(payload)
            inventory_target = inventory.get("target", {})
            node_ref = inventory_target.get("node", {}) if inventory_target.get("kind") == "node" else {}
            inventory_sources = set(inventory.get("assertion", {}).get("context", {}).get("source_ids", []))
            if not inventory_sources.intersection(current_source_ids):
                continue
            if target and inventory_target.get("kind") == "node" and node_ref != target:
                continue
            direct_nodes.append(inventory)

        conflicts = []
        for (payload,) in self.connection.execute("SELECT payload FROM conflicts"):
            conflict = json.loads(payload)
            conflict_sources = set(conflict.get("context", {}).get("source_ids", []))
            if conflict_sources.intersection(current_source_ids):
                conflicts.append(conflict)

        return {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "sources": sources,
            "facts": selected,
            "navigation": navigation,
            "direct_nodes": direct_nodes,
            "conflicts": conflicts,
        }

    @staticmethod
    def _validate_query(query: dict[str, Any]) -> None:
        required = {"contract_version", "catalog_id", "request_id", "scope", "target", "granularity", "selections", "budget"}
        if not isinstance(query, dict) or not required <= query.keys():
            raise ValueError("query is incomplete")

