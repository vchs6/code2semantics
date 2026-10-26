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
    duplicate = copy.deepcopy(original)
    duplicate["edge_id"] = "member-a-duplicate"
    parent_edge = copy.deepcopy(original)
    parent_edge["edge_id"] = "member-b"
    parent_edge["source"] = {"source_id": "src-a", "subject_id": "project-a", "node_id": "parent-b"}
    cycle_edge = copy.deepcopy(original)
    cycle_edge["edge_id"] = "cycle-a"
    cycle_edge["source"], cycle_edge["target"] = original["target"], original["source"]
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
    assert any(edge["source"]["node_id"] == "child-a" and edge["target"]["node_id"] == "unit-a" for edge in result["navigation"])
    assert any(edge["target"].get("kind") == "external" for edge in result["navigation"])
    repository.close()