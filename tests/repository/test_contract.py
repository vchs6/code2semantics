"""���ǰ��ȱ codec����Щ����Լ���ֶα��桢ӳ�串�Ǽ���ȷ�ܾ���"""
import copy
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import pytest


def test_fixture_passes_public_schema(batch, public_validator):
    public_validator.validate(batch)


def test_roundtrip_preserves_every_field(codec, batch, public_validator):
    public_validator.validate(batch)
    records = codec.decode(batch)
    rebuilt = codec.encode(records)
    assert rebuilt == batch
    public_validator.validate(rebuilt)
    assertion = rebuilt["facts"][0]["fields"]["strategy"]
    assert {e["kind"] for e in assertion["basis"]["evidence"]} == {"source", "manifest", "configuration", "documentation", "observation"}
    for name in ("origin", "knowledge", "context", "coverage", "basis", "validity"):
        assert assertion[name] == batch["facts"][0]["fields"]["strategy"][name]
    assert rebuilt["facts"][1]["fields"]["open_items"]["negative"] == batch["facts"][1]["fields"]["open_items"]["negative"]
    assert rebuilt["facts"][2]["fields"]["strategy"]["validity"]["state"] == "modified"
    assert rebuilt["conflicts"] == batch["conflicts"]
    assert rebuilt["direct_nodes"] == batch["direct_nodes"]
    assert rebuilt["direct_nodes"][0]["assertion"]["coverage"]["completeness"] == "partial"
    assert rebuilt["facts"][1]["fields"]["strategy"]["basis"]["evidence"][0]["relation"] == "refutes"


@pytest.mark.parametrize("bad", ["report", "response", "revision", "snapshot", "refresh", "version", "stored"])
def test_rejects_report_response_and_old_protocol(codec, batch, bad):
    from semantic_facts.repository.types import ContractError
    value = copy.deepcopy(batch)
    if bad == "report":
        value = {"report": "human readable semantics"}
    elif bad == "response":
        value = json.loads((Path(__file__).parent / "fixtures/response.json").read_text(encoding="utf-8"))
    elif bad == "version":
        value["contract_version"] = "0.1.0"
    elif bad == "stored":
        value = {"kind": "stored_record", "batch": value, "transaction_id": "tx-a"}
    else:
        value[bad] = "old"
    with pytest.raises(ContractError) as error:
        codec.decode(value)
    assert error.value.location
    assert error.value.reason


@pytest.mark.parametrize("language,value", [("Python", "x is None"), ("Rust", "match x { Some(v) => v, None => return }"), ("���", "let ֵ = Some(1)")])
def test_same_shape_across_languages(codec, batch, language, value):
    batch["facts"][0]["fields"]["strategy"]["context"]["language_semantics"] = [language]
    batch["facts"][0]["fields"]["strategy"]["value"] = {"kind": "text", "text": value}
    assert codec.encode(codec.decode(batch)) == batch


def test_immutable_rows_and_independent_fields(codec, batch):
    records = codec.decode(batch)
    record = records[0]
    assert len(record.facts) == 3
    assert len(record.attributes) == 4
    assert record.entities
    assert record.relations and record.evidence and record.evidence_links and record.premises
    assert record.conflicts and record.conflict_links
    with pytest.raises(FrozenInstanceError):
        record.facts = ()
    batch["facts"][0]["fields"]["strategy"]["value"]["text"] = "mutated caller input"
    assert codec.encode(records)["facts"][0]["fields"]["strategy"]["value"]["text"] == "stable deduplication"


def test_mapping_covers_every_public_leaf_and_rejects_missing_binding(codec, batch):
    from semantic_facts.repository.types import ContractError
    record = codec.decode(batch)[0]
    def leaves(value, path=""):
        if isinstance(value, dict) and value:
            return {p for key, child in value.items() for p in leaves(child, path + "/" + key.replace("~", "~0").replace("/", "~1"))}
        if isinstance(value, list) and value:
            return {p for index, child in enumerate(value) for p in leaves(child, path + "/" + str(index))}
        return {path}
    assert {b.pointer for b in record.bindings} == leaves(batch)
    with pytest.raises(ContractError) as error:
        codec.encode((replace(record, bindings=record.bindings[:-1]),))
    assert error.value.location


def test_source_envelope_preserved_without_facts(codec, batch):
    from semantic_facts.repository.types import ContractError
    for name in ("facts", "navigation", "direct_nodes", "conflicts"):
        batch[name] = []
    assert codec.encode(codec.decode(batch)) == batch
    with pytest.raises(ContractError) as error:
        codec.encode(())
    assert error.value.location


def test_unknown_field_and_non_json_value_rejected(codec, batch):
    from semantic_facts.repository.types import ContractError
    batch["facts"][0]["fields"]["strategy"]["future"] = {"secret": True}
    with pytest.raises(ContractError) as error:
        codec.decode(batch)
    assert error.value.location.startswith("/")
    del batch["facts"][0]["fields"]["strategy"]["future"]
    batch["facts"][0]["fields"]["strategy"]["value"] = {"kind": "scalar", "value": float("nan")}
    with pytest.raises(ContractError):
        codec.decode(batch)


def test_identity_is_domain_qualified_and_object_order_independent(codec, batch):
    original = codec.decode(batch)[0]
    reordered = copy.deepcopy(batch)
    reordered["navigation"][0]["source"] = dict(reversed(list(reordered["navigation"][0]["source"].items())))
    assert codec.decode(reordered)[0].relations[0].key == original.relations[0].key
    other = copy.deepcopy(batch)
    # Rename the public source domain everywhere, without changing local IDs.
    def rename(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "source_id":
                    value[key] = "src-other"
                elif key == "source_ids":
                    value[key] = ["src-other"]
                else:
                    rename(child)
        elif isinstance(value, list):
            for child in value:
                rename(child)
    rename(other)
    changed = codec.decode(other)[0]
    for name in ("entities", "facts", "relations", "evidence", "conflicts"):
        assert {r.key for r in getattr(original, name)}.isdisjoint({r.key for r in getattr(changed, name)})


def test_internal_references_do_not_declare_missing_entities(codec, batch):
    from semantic_facts.repository.types import entity_key
    missing = {"source_id":"src-a", "subject_id":"project-a", "node_id":"not-declared"}
    batch["navigation"][0]["target"] = missing
    batch["facts"][1]["fields"]["strategy"]["basis"]["premises"][0]["node"] = missing
    record = codec.decode(batch)[0]
    assert entity_key(missing) not in {r.key for r in record.entities}
    child = batch["direct_nodes"][0]["children"][0]
    assert entity_key(child) in {r.key for r in record.entities}
    assert codec.encode((record,)) == batch


@pytest.mark.parametrize("duplicate_kind", ["identical", "different_value", "disjoint_fields"])
def test_duplicate_fact_identity_rejected_without_silent_rewrite(codec, batch, public_validator, duplicate_kind):
    from semantic_facts.repository.types import ContractError
    duplicate = copy.deepcopy(batch["facts"][0])
    if duplicate_kind == "different_value":
        duplicate["fields"]["strategy"]["value"]["text"] = "must never replace earlier assertion"
    elif duplicate_kind == "disjoint_fields":
        duplicate["fields"] = {"goal": duplicate["fields"]["strategy"]}
    batch["facts"].append(duplicate)
    public_validator.validate(batch)  # Shared schema intentionally cannot enforce identity uniqueness.
    before = copy.deepcopy(batch)
    with pytest.raises(ContractError) as error:
        codec.decode(batch)
    assert error.value.location == "/facts/3"
    assert "duplicate" in error.value.reason.lower()
    assert batch == before


@pytest.mark.parametrize("location", ["field", "navigation", "inventory"])
def test_explicit_edge_projection_in_every_assertion_location(codec, batch, public_validator, location):
    edge = {
        "source": copy.deepcopy(batch["facts"][0]["node"]),
        "target": copy.deepcopy(batch["direct_nodes"][0]["children"][0]),
        "kind": "call",
        "conditions": [{"expression":"enabled", "scope":"fixture", "state":"unknown"}],
    }
    if location == "field":
        assertion = batch["facts"][0]["fields"]["strategy"]
        pointer = "/facts/0/fields/strategy"
    elif location == "navigation":
        assertion = batch["navigation"][0]["assertion"]
        pointer = "/navigation/0/assertion"
    else:
        assertion = batch["direct_nodes"][0]["assertion"]
        pointer = "/direct_nodes/0/assertion"
    # The same recursive semantic_value shape is legal at all three locations.
    assertion["value"] = {"kind":"list", "items":[{"kind":"edges", "edges":[edge]}]}
    public_validator.validate(batch)
    record = codec.decode(batch)[0]
    rows = [r for r in record.relations if not r.navigation]
    assert len(rows) == 1
    row = rows[0]
    assert row.pointer == pointer + "/value/items/0/edges/0"
    assert row.value == edge
    if location == "field":
        owner = record.facts[0].key
    elif location == "navigation":
        owner = next(r.key for r in record.relations if r.navigation)
    else:
        owner = record.inventories[0].key
    assert row.owner_key == owner
    assert row.relation == "call"
    assert row.source_key == record.facts[0].entity_key
    assert row.target_key in {r.key for r in record.entities}
    assert codec.encode((record,)) == batch

