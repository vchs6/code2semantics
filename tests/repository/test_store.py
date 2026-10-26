import json

import pytest


def make_query(*, subject_id="project-a", fact_type="F16", fields=("strategy",)):
    return {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "request-store-1",
        "scope": {
            "scope_id": "scope-a",
            "directories": ["/workspace/a"],
            "excludes": [],
            "defaulted": False,
        },
        "target": {
            "kind": "node",
            "node": {
                "source_id": "src-a",
                "subject_id": subject_id,
                "node_id": "unit-a",
            },
        },
        "granularity": "L4",
        "selections": [{"fact_type": fact_type, "fields": list(fields)}],
        "budget": {"max_rounds": 1, "max_new_assertions": 10},
    }


def test_write_reopens_and_stores_normalized_rows(batch, db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    receipt = repository.write(batch, "submission-1")
    assert receipt.submission_key == "submission-1"
    assert receipt.affected == ()
    repository.close()

    reopened = Repository(db_path)
    tables = {row[0] for row in reopened.connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )}
    assert {"sources", "facts", "attributes", "relations"} <= tables
    assert reopened.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == len(batch["facts"])
    assert reopened.connection.execute("SELECT COUNT(*) FROM attributes").fetchone()[0] >= 1
    assert reopened.connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 1
    reopened.close()


def test_read_returns_only_selected_fact_and_fields(batch, db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    repository.write(batch, "submission-1")
    result = repository.read(make_query())

    assert [fact["fact_id"] for fact in result["facts"]] == ["fact-a", "fact-b"]
    assert all(list(fact["fields"]) == ["strategy"] for fact in result["facts"])
    assert result["sources"] == batch["sources"]
    assert result["navigation"] == batch["navigation"]
    assert result["direct_nodes"] == [item for item in batch["direct_nodes"] if item["target"].get("node", {}).get("node_id") == "unit-a"]
    assert result["conflicts"] == batch["conflicts"]
    repository.close()


def test_read_with_no_match_returns_an_empty_fact_set(batch, db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    repository.write(batch, "submission-1")
    result = repository.read(make_query(subject_id="missing"))

    assert result["facts"] == []
    assert [source["source_id"] for source in result["sources"]] == ["src-a"]
    assert result["navigation"] == []
    repository.close()


def test_write_rejects_non_fact_batch_without_changing_database(db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    with pytest.raises(ValueError):
        repository.write({"response": True}, "submission-1")
    assert repository.connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []
    repository.close()


def test_navigation_deduplicates_edges_and_preserves_cycles_multi_parent_and_external_refs(batch, db_path):
    import copy
    from semantic_facts.repository.store import Repository

    value = copy.deepcopy(batch)
    original = value["navigation"][0]
    original["assertion"]["context"]["conditions"] = [
        {"expression": "feature_enabled", "scope": "build", "state": "true"}
    ]
    duplicate = copy.deepcopy(original)
    duplicate["edge_id"] = "member-a-duplicate"
    parent_edge = copy.deepcopy(original)
    parent_edge["edge_id"] = "member-b"
    parent_edge["source"] = {"source_id": "src-a", "subject_id": "project-a", "node_id": "parent-b"}
    cycle_edge = copy.deepcopy(original)
    cycle_edge["edge_id"] = "cycle-a"
    cycle_edge["source"], cycle_edge["target"] = original["target"], original["source"]
    cycle_edge["assertion"]["context"]["conditions"] = [
        {"expression": "feature_enabled", "scope": "build", "state": "false"}
    ]
    external_edge = copy.deepcopy(original)
    external_edge["edge_id"] = "external-a"
    external_edge["target"] = {
        "kind": "external",
        "reference_id": "external-service",
        "label": "service outside requested scope",
        "reason": "outside_authorized_scope",
        "boundary": "not scanned",
        "observed_in": {"kind": "subject", "source_id": "src-a", "subject_id": "project-a"},
    }
    value["navigation"] = [original, duplicate, parent_edge, cycle_edge, external_edge]

    repository = Repository(db_path)
    repository.write(value, "graph-shape-test")
    query = make_query()
    query["target"] = {"kind": "scope"}
    result = repository.read(query)
    signatures = [
        (edge["source"], edge["target"], edge["relation"], edge["assertion"]["context"]["conditions"])
        for edge in result["navigation"]
    ]
    assert len(signatures) == 4
    assert len(set(map(repr, signatures))) == 4
    assert any(edge["source"]["node_id"] == "parent-b" and edge["target"]["node_id"] == "child-a" for edge in result["navigation"])
    assert any(
        edge["source"]["node_id"] == "child-a"
        and edge["target"]["node_id"] == "unit-a"
        and edge["assertion"]["context"]["conditions"][0]["state"] == "false"
        for edge in result["navigation"]
    )
    assert any(
        edge["source"]["node_id"] == "unit-a"
        and edge["target"]["node_id"] == "child-a"
        and edge["assertion"]["context"]["conditions"][0]["state"] == "true"
        for edge in result["navigation"]
    )
    assert any(edge["target"].get("kind") == "external" for edge in result["navigation"])
    repository.close()
def test_bounded_navigation_traversal_handles_cycles_multi_parent_and_external_refs(batch, db_path):
    import copy
    from semantic_facts.repository.store import Repository

    value = copy.deepcopy(batch)
    first = copy.deepcopy(value["navigation"][0])
    duplicate_first = copy.deepcopy(first)
    duplicate_first["edge_id"] = "duplicate-member-a"
    second_parent = copy.deepcopy(first)
    second_parent["edge_id"] = "parent-b-to-child"
    second_parent["source"] = {
        "source_id": "src-a", "subject_id": "project-a", "node_id": "parent-b"
    }
    second_parent_root = copy.deepcopy(first)
    second_parent_root["edge_id"] = "root-to-parent-b"
    second_parent_root["target"] = {
        "source_id": "src-a", "subject_id": "project-a", "node_id": "parent-b"
    }
    cycle = copy.deepcopy(first)
    cycle["edge_id"] = "child-to-root-cycle"
    cycle["source"], cycle["target"] = first["target"], first["source"]
    external = copy.deepcopy(first)
    external["edge_id"] = "child-to-external"
    external["source"] = first["target"]
    external["target"] = {
        "kind": "external",
        "reference_id": "external-crate",
        "label": "outside crate",
        "reason": "outside_authorized_scope",
        "boundary": "not scanned",
        "observed_in": {
            "kind": "subject", "source_id": "src-a", "subject_id": "project-a"
        },
    }
    value["navigation"] = [first, duplicate_first, second_parent_root, second_parent, cycle, external]
    repository = Repository(db_path)
    repository.write(value, "bounded-graph-traversal")

    result = repository.traverse_navigation(
        {"source_id": "src-a", "subject_id": "project-a", "node_id": "unit-a"},
        max_depth=8,
        max_edges=20,
    )
    edge_ids = {edge["edge_id"] for edge in result["edges"]}
    assert {"member-a", "root-to-parent-b", "parent-b-to-child", "child-to-root-cycle", "child-to-external"} <= edge_ids
    assert "duplicate-member-a" not in edge_ids
    assert sum(edge["source"] == first["source"] and edge["target"] == first["target"] for edge in result["edges"]) == 1
    assert len(result["nodes"]) == len({repr(node) for node in result["nodes"]})
    assert any(node.get("node_id") == "parent-b" for node in result["nodes"])
    assert any(node.get("kind") == "external" for node in result["terminal_references"])
    assert result["truncated"] is False
    assert result["reason"] is None

    bounded = repository.traverse_navigation(
        {"source_id": "src-a", "subject_id": "project-a", "node_id": "unit-a"},
        max_depth=1,
        max_edges=1,
    )
    assert bounded["truncated"] is True
    assert bounded["reason"] in {"depth", "edges"}
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == len(value["facts"])
    repository.close()

def test_existing_semantic_entity_is_incrementally_enriched_with_new_fact_field(batch, db_path):
    import copy
    from semantic_facts.repository.store import Repository

    first = copy.deepcopy(batch)
    first["facts"] = [fact for fact in first["facts"] if fact["fact_id"] == "fact-a"]
    first["facts"][0]["fields"] = {"strategy": first["facts"][0]["fields"]["strategy"]}
    first["navigation"] = []
    first["direct_nodes"] = []
    first["conflicts"] = []

    second = copy.deepcopy(first)
    second["facts"][0]["fields"] = {
        "open_items": copy.deepcopy(first["facts"][0]["fields"]["strategy"])
    }

    repository = Repository(db_path)
    repository.write(first, "entity-enrichment-first")
    repository.write(second, "entity-enrichment-second")

    query = make_query(fields=("strategy", "open_items"))
    result = repository.read(query)
    matching = [fact for fact in result["facts"] if fact["fact_id"] == "fact-a"]
    assert len(matching) == 1
    assert set(matching[0]["fields"]) == {"strategy", "open_items"}
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 1
    assert repository.connection.execute("SELECT COUNT(*) FROM attributes").fetchone()[0] == 2
    repository.close()


def test_identical_incremental_fact_field_replay_is_idempotent(batch, db_path):
    import copy
    from semantic_facts.repository.store import Repository

    value = copy.deepcopy(batch)
    value["facts"] = [fact for fact in value["facts"] if fact["fact_id"] == "fact-a"]
    value["facts"][0]["fields"] = {"strategy": value["facts"][0]["fields"]["strategy"]}
    value["navigation"] = []
    value["direct_nodes"] = []
    value["conflicts"] = []

    repository = Repository(db_path)
    repository.write(value, "entity-field-replay-a")
    repository.write(value, "entity-field-replay-b")

    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 1
    assert repository.connection.execute("SELECT COUNT(*) FROM attributes").fetchone()[0] == 1
    assert repository.connection.execute("SELECT COUNT(*) FROM evidence_links").fetchone()[0] == 1
    repository.close()

def test_existing_field_can_be_enriched_with_new_evidence_without_replacing_old_evidence(batch, db_path):
    import copy
    from semantic_facts.repository.store import Repository

    first = copy.deepcopy(batch)
    first["facts"] = [fact for fact in first["facts"] if fact["fact_id"] == "fact-a"]
    first["facts"][0]["fields"] = {"strategy": first["facts"][0]["fields"]["strategy"]}
    first["navigation"] = []
    first["direct_nodes"] = []
    first["conflicts"] = []

    second = copy.deepcopy(first)
    assertion = second["facts"][0]["fields"]["strategy"]
    new_evidence = copy.deepcopy(assertion["basis"]["evidence"][0])
    new_evidence.update({
        "evidence_id": "ev-new-tool",
        "kind": "observation",
        "locator": "tool-output:cargo-metadata",
        "content_digest": "sha256:" + "b" * 64,
        "relation": "supports",
    })
    assertion["basis"]["evidence"].append(new_evidence)

    repository = Repository(db_path)
    repository.write(first, "entity-evidence-first")
    repository.write(second, "entity-evidence-second")

    query = make_query(fields=("strategy",))
    result = repository.read(query)
    fact = next(item for item in result["facts"] if item["fact_id"] == "fact-a")
    evidence_ids = {item["evidence_id"] for item in fact["fields"]["strategy"]["basis"]["evidence"]}
    assert "ev-0" in evidence_ids
    assert "ev-new-tool" in evidence_ids
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 1
    repository.close()
