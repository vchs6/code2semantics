import json


def _query():
    return {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "repository-acceptance",
        "scope": {
            "scope_id": "scope-a",
            "directories": ["/workspace/a"],
            "excludes": [],
            "defaulted": False,
        },
        "target": {
            "kind": "node",
            "node": {"source_id": "src-a", "subject_id": "project-a", "node_id": "unit-a"},
        },
        "granularity": "L4",
        "selections": [{"fact_type": "F16", "fields": ["strategy"]}],
        "budget": {"max_rounds": 1, "max_new_assertions": 10},
    }


def test_repository_acceptance_write_reopen_query_backup_restore_preserves_history(batch, db_path, tmp_path):
    from semantic_facts.repository.store import Repository

    backup = tmp_path / "facts-backup.db"
    restored_path = tmp_path / "restored.db"
    repository = Repository(db_path)
    repository.write(batch, "acceptance-submission")
    before = {
        table: repository.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("sources", "entities", "facts", "attributes", "relations", "submissions")
    }
    assert before["facts"] == len(batch["facts"])
    assert before["submissions"] == 1

    repository.backup(backup)
    repository.close()

    reopened = Repository(db_path)
    current = reopened.read(_query())
    assert current["facts"]
    assert all(set(fact["fields"]) == {"strategy"} for fact in current["facts"])
    reopened.close()

    restored = Repository(restored_path)
    restored.restore(backup)
    after = {
        table: restored.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in before
    }
    assert after == before
    assert restored.read(_query()) == current
    restored.close()


def test_repository_acceptance_conflict_rolls_back_without_deleting_facts(batch, db_path):
    from semantic_facts.repository.store import Repository
    from semantic_facts.repository.types import WriteConflict

    repository = Repository(db_path)
    repository.write(batch, "acceptance-submission")
    before_facts = repository.connection.execute("SELECT fact_key, payload FROM facts ORDER BY fact_key").fetchall()
    before_attributes = repository.connection.execute(
        "SELECT attribute_key, payload FROM attributes ORDER BY attribute_key"
    ).fetchall()
    before_submissions = repository.connection.execute(
        "SELECT submission_key, digest FROM submissions ORDER BY submission_key"
    ).fetchall()

    conflicting = json.loads(json.dumps(batch))
    conflicting["facts"][0]["granularities"] = ["L2"]
    try:
        repository.write(conflicting, "conflicting-submission")
    except (WriteConflict, ValueError):
        pass
    else:
        raise AssertionError("conflicting fact identity must be rejected")

    assert repository.connection.execute("SELECT fact_key, payload FROM facts ORDER BY fact_key").fetchall() == before_facts
    assert repository.connection.execute(
        "SELECT attribute_key, payload FROM attributes ORDER BY attribute_key"
    ).fetchall() == before_attributes
    assert repository.connection.execute(
        "SELECT submission_key, digest FROM submissions ORDER BY submission_key"
    ).fetchall() == before_submissions
    repository.close()

def test_repository_acceptance_invalidation_revalidation_and_export_import_roundtrip(batch, db_path, tmp_path):
    from semantic_facts.repository.store import Repository

    query = _query()
    imported_path = tmp_path / "imported-current.db"
    repository = Repository(db_path)
    repository.write(batch, "acceptance-validity")
    before_fact_rows = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    fact_key = repository.connection.execute("SELECT fact_key FROM facts WHERE fact_id = ?", ("fact-a",)).fetchone()[0]
    field_key = repository.connection.execute(
        "SELECT attribute_key FROM attributes WHERE fact_key = ? AND field_name = ?",
        (fact_key, "strategy"),
    ).fetchone()[0]

    repository.invalidate_field("fact-a", "strategy", "acceptance source changed")
    invalidated = repository.read(query)
    assert invalidated["facts"] == []
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == before_fact_rows

    repository.record_validity_event("field", field_key, "current", "revalidated against current source evidence")
    current = repository.read(query)
    assert {fact["fact_id"] for fact in current["facts"]} == {"fact-a", "fact-b"}

    exported = repository.export_current()
    imported = Repository(imported_path)
    receipt = imported.import_current(exported, "acceptance-import")
    assert receipt.submission_key == "acceptance-import"
    imported_result = imported.read(query)
    assert {fact["fact_id"] for fact in imported_result["facts"]} == {"fact-a", "fact-b"}
    assert imported.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 2
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == before_fact_rows
    imported.close()
    repository.close()