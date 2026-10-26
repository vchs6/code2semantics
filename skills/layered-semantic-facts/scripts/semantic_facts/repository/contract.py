"""ֻ����ͬԴ FactBatch schema��������������/�ؽ���"""
from dataclasses import replace
import json
import math
from pathlib import Path
from typing import Sequence
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from .types import (
    AttributeRow, ConflictLink, ConflictRow, ContractError, EntityRow,
    EvidenceLink, EvidenceRow, FactRow, FieldBinding, InventoryRow, JsonObject,
    PremiseRow, RecordKey, RelationRow, SourceRow, StoredRecord,
    entity_key, fact_key, identity_key, project_key,
)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _escape(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _walk(value: object, pointer: str = ""):
    yield pointer, value
    if isinstance(value, dict):
        for name, child in value.items():
            yield from _walk(child, pointer + "/" + _escape(name))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, pointer + "/" + str(index))


def _leaves(value: object):
    return (p for p, v in _walk(value) if not isinstance(v, (dict, list)) or not v)


def _put(batch: JsonObject, pointer: str, value: object):
    parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer.lstrip("/").split("/")]
    target = batch
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    if isinstance(target, list):
        target[int(parts[-1])] = value
    else:
        target[parts[-1]] = value


def _premise_target(value: JsonObject) -> RecordKey:
    node = value["node"]
    return RecordKey("attribute", identity_key(node["source_id"], node["subject_id"], node["node_id"], value["fact_id"]), "/fields/" + _escape(value["field"]))


class ContractCodec:
    def __init__(self, schema_root: Path):
        self.schema_root = Path(schema_root).resolve()
        try:
            schemas = [json.loads(p.read_text(encoding="utf-8")) for p in self.schema_root.glob("*.schema.json")]
            registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
            schema_id = next(s["$id"] for s in schemas if s["$id"].endswith("/pipeline.schema.json"))
            self._validator = Draft202012Validator({"$ref": schema_id + "#/$defs/fact_batch"}, registry=registry)
        except (OSError, ValueError, KeyError, StopIteration) as error:
            raise ContractError("/", f"Cannot load public FactBatch schema: {error}") from error

    def validate_batch(self, batch: JsonObject) -> None:
        for pointer, value in _walk(batch):
            if isinstance(value, float) and not math.isfinite(value):
                raise ContractError(pointer or "/", "Non-finite JSON number")
            if not (value is None or type(value) in (dict, list, str, int, float, bool)):
                raise ContractError(pointer or "/", "Not a JSON value")
            if isinstance(value, dict) and any(not isinstance(k, str) for k in value):
                raise ContractError(pointer or "/", "JSON object keys must be strings")
        error = next(self._validator.iter_errors(batch), None)
        if error is not None:
            pointer = "/" + "/".join(_escape(p) for p in error.absolute_path)
            raise ContractError(pointer, error.message)
        seen = {}
        for index, fact in enumerate(batch["facts"]):
            key = fact_key(fact)
            if key in seen:
                previous = seen[key]
                detail = "identical repetition" if previous == fact else "conflicting content"
                raise ContractError(
                    f"/facts/{index}",
                    f"Duplicate fact identity ({detail}); fact_id={fact.get('fact_id')}; "
                    f"previous_fact_id={previous.get('fact_id')}; fact_type={fact.get('fact_type')}; "
                    f"previous_fact_type={previous.get('fact_type')}; node_id={fact.get('node', {}).get('node_id')}",
                )
            seen[key] = fact

    def decode(self, batch: JsonObject) -> tuple[StoredRecord, ...]:
        self.validate_batch(batch)
        # JSON copy severs every mutable caller-owned reference.
        batch = json.loads(_json(batch))
        sources = tuple(SourceRow(s["source_id"], f"/sources/{i}", _json(s), i) for i, s in enumerate(batch["sources"]))
        entities = {}
        declared = [(f"/facts/{i}/node", f["node"]) for i, f in enumerate(batch["facts"])]
        for i, inventory in enumerate(batch["direct_nodes"]):
            if inventory["target"]["kind"] == "node":
                declared.append((f"/direct_nodes/{i}/target/node", inventory["target"]["node"]))
            declared.extend((f"/direct_nodes/{i}/children/{j}", node) for j, node in enumerate(inventory["children"]))
        for pointer, node in declared:
            key = entity_key(node)
            entities.setdefault(key, EntityRow(key, pointer, _json(node), len(entities), project_key(node)))
        facts, attributes, relations = [], [], []
        for index, fact in enumerate(batch["facts"]):
            key = fact_key(fact)
            pointer = f"/facts/{index}"
            facts.append(FactRow(key, pointer, _json({k:v for k,v in fact.items() if k != "fields"}), index, entity_key(fact["node"]), fact["fact_type"]))
            for field, assertion in fact["fields"].items():
                field_path = "/fields/" + _escape(field)
                attributes.append(AttributeRow(identity_key(key, field_path), pointer + field_path, _json(assertion), len(attributes), key, field_path))
                self._project_edges(assertion, pointer + field_path, key, field_path, relations)
        for i, edge in enumerate(batch["navigation"]):
            key = identity_key(_json(edge["source"]), edge["edge_id"])
            relations.append(RelationRow(key, f"/navigation/{i}", _json(edge), i, key, self._endpoint(edge["source"]), self._endpoint(edge["target"]), edge["relation"], True))
            self._project_edges(edge["assertion"], f"/navigation/{i}/assertion", key, "/assertion", relations)
        inventories = tuple(
            InventoryRow(
                identity_key("direct", str(i), _json(inv["target"]), inv["granularity"], inv["boundary"], _json(inv["assertion"]["validity"])),
                f"/direct_nodes/{i}",
                _json(inv),
                i,
            )
            for i, inv in enumerate(batch["direct_nodes"])
        )
        for inventory in inventories:
            self._project_edges(inventory.value["assertion"], inventory.pointer + "/assertion", inventory.key, "/assertion", relations)
        conflicts = tuple(ConflictRow(identity_key(*sorted(c["context"]["source_ids"]), c["conflict_id"]), f"/conflicts/{i}", _json(c), i) for i, c in enumerate(batch["conflicts"]))
        conflict_links = tuple(ConflictLink(identity_key(c.key, str(i)), c.pointer + f"/members/{i}", _json(member), i, c.key, _premise_target(member)) for c in conflicts for i, member in enumerate(c.value["members"]))
        owners = [(r.pointer, r.key) for rows in (attributes, relations, inventories, conflicts) for r in rows]
        evidence, evidence_links, premises = {}, [], []
        for pointer, value in _walk(batch):
            if not isinstance(value, dict):
                continue
            owner = max(((p,k) for p,k in owners if pointer.startswith(p + "/")), key=lambda item:len(item[0]), default=("", "envelope"))[1]
            if {"evidence_id", "content_digest", "relation"} <= value.keys():
                key = identity_key(value["source_id"], value["evidence_id"])
                body = {k:v for k,v in value.items() if k != "relation"}
                if key in evidence and evidence[key].value != body:
                    raise ContractError(pointer, "Same evidence identity has different content")
                evidence.setdefault(key, EvidenceRow(key, pointer, _json(body), len(evidence)))
                evidence_links.append(EvidenceLink(owner, key, pointer, value["relation"], len(evidence_links)))
            if {"node", "fact_id", "field", "content_state"} <= value.keys() and "/basis/premises/" in pointer:
                premises.append(PremiseRow(identity_key(owner, pointer), pointer, _json(value), len(premises), owner, _premise_target(value)))
        record = StoredRecord(batch["contract_version"], batch["catalog_id"], sources, tuple(entities.values()), tuple(facts), tuple(attributes), tuple(relations), inventories, tuple(evidence.values()), tuple(evidence_links), tuple(premises), conflicts, conflict_links, ())
        return (replace(record, bindings=self._bindings(batch, record)),)

    def _project_edges(self, assertion: JsonObject, pointer: str, owner_key: str, local_path: str, relations: list[RelationRow]) -> None:
        # All three public assertion positions share recursive semantic_value.
        # References, candidate targets and conditions do not imply graph edges.
        for subpath, value in _walk(assertion):
            if isinstance(value, dict) and {"source", "target", "kind", "conditions"} <= value.keys():
                relations.append(RelationRow(identity_key(owner_key, local_path, subpath), pointer + subpath, _json(value), len(relations), owner_key, self._endpoint(value["source"]), self._endpoint(value["target"]), value["kind"], False))

    @staticmethod
    def _endpoint(reference: JsonObject) -> str | None:
        return None if reference.get("kind") == "external" else entity_key(reference)

    @staticmethod
    def _bindings(batch: JsonObject, record: StoredRecord) -> tuple[FieldBinding, ...]:
        owners = [(r.pointer, collection, r.key) for collection in ("sources", "facts", "attributes", "relations", "inventories", "premises", "conflicts", "conflict_links") for r in getattr(record, collection)]
        bindings = []
        for pointer in _leaves(batch):
            link = next((link for link in record.evidence_links if pointer.startswith(link.pointer + "/")), None)
            if link:
                polarity = pointer == link.pointer + "/relation"
                bindings.append(FieldBinding(pointer, "evidence_links" if polarity else "evidence", link.pointer if polarity else link.evidence_key, "relation" if polarity else "payload" + pointer[len(link.pointer):]))
                continue
            prefix, collection, key = max((o for o in owners if pointer == o[0] or pointer.startswith(o[0] + "/")), key=lambda o:len(o[0]), default=("", "envelope", ""))
            bindings.append(FieldBinding(pointer, collection, key, "payload" + pointer[len(prefix):]))
        return tuple(sorted(bindings, key=lambda b: b.pointer))

    def encode(self, records: Sequence[StoredRecord]) -> JsonObject:
        if len(records) != 1:
            raise ContractError("/sources", "Encode requires one retained source envelope; merge rows before encoding")
        record = records[0]
        batch = {"contract_version":record.contract_version, "catalog_id":record.catalog_id, "sources":[r.value for r in sorted(record.sources, key=lambda r:r.ordinal)], "facts":[], "navigation":[], "direct_nodes":[r.value for r in sorted(record.inventories, key=lambda r:r.ordinal)], "conflicts":[r.value for r in sorted(record.conflicts, key=lambda r:r.ordinal)]}
        for fact in sorted(record.facts, key=lambda r:r.ordinal):
            value = fact.value
            value["fields"] = {r.field_path.removeprefix("/fields/").replace("~1", "/").replace("~0", "~"):r.value for r in record.attributes if r.fact_key == fact.key}
            batch["facts"].append(value)
        for relation in sorted((r for r in record.relations if r.navigation), key=lambda r:r.ordinal):
            batch["navigation"].append(relation.value)
        try:
            for relation in record.relations:
                if not relation.navigation:
                    _put(batch, relation.pointer, relation.value)
            for premise in record.premises:
                _put(batch, premise.pointer, premise.value)
            for link in record.conflict_links:
                _put(batch, link.pointer, link.value)
            evidence = {r.key:r.value for r in record.evidence}
            for link in record.evidence_links:
                _put(batch, link.pointer, {**evidence[link.evidence_key], "relation":link.relation})
        except (KeyError, IndexError, TypeError) as error:
            raise ContractError("/", f"Missing row binding: {error}") from error
        self.validate_batch(batch)
        expected = self._bindings(batch, record)
        if expected != record.bindings:
            actual = {b.pointer:b for b in record.bindings}
            missing = next((b.pointer for b in expected if actual.get(b.pointer) != b), "/")
            raise ContractError(missing, "Missing or changed public field binding")
        return batch

