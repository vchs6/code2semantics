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

    assert [fact["fact_id"] for fact in result["facts"]] == ["fact-a", "fact-b", "fact-old"]
    assert all(list(fact["fields"]) == ["strategy"] for fact in result["facts"])
    assert result["sources"] == batch["sources"]
    assert result["navigation"] == []
    assert result["direct_nodes"] == []
    assert result["conflicts"] == []
    repository.close()


def test_read_with_no_match_returns_an_empty_fact_set(batch, db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    repository.write(batch, "submission-1")
    result = repository.read(make_query(subject_id="missing"))

    assert result["facts"] == []
    assert result["sources"] == []
    assert result["navigation"] == []
    repository.close()


def test_write_rejects_non_fact_batch_without_changing_database(db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    with pytest.raises(ValueError):
        repository.write({"response": True}, "submission-1")
    assert repository.connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []
    repository.close()

