import json
import sqlite3

import pytest


def _snapshot(repository):
    return {
        table: repository.connection.execute(
            f"SELECT * FROM {table} ORDER BY 1"
        ).fetchall()
        for table in ("sources", "entities", "facts", "attributes", "relations", "submissions")
    }


def test_backup_and_restore_preserve_current_fact_set(batch, db_path, tmp_path):
    from semantic_facts.repository.store import Repository

    backup_path = tmp_path / "facts-backup.db"
    restored_path = tmp_path / "restored-facts.db"

    original = Repository(db_path)
    original.write(batch, "submission-1")
    expected = _snapshot(original)
    original.backup(backup_path)

    # Restore into a separate database. The source database and its fact history
    # are never destructively modified by this test.
    restored = Repository(restored_path)
    restored.restore(backup_path)
    assert _snapshot(restored) == expected
    assert restored.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    original.close()
    restored.close()


def test_restore_rejects_invalid_backup_without_changing_database(batch, db_path, tmp_path):
    from semantic_facts.repository.store import Repository

    invalid_backup = tmp_path / "invalid.db"
    invalid_backup.write_text("not a sqlite database", encoding="utf-8")

    repository = Repository(db_path)
    repository.write(batch, "submission-1")
    before = _snapshot(repository)

    with pytest.raises((ValueError, sqlite3.DatabaseError)):
        repository.restore(invalid_backup)

    assert _snapshot(repository) == before
    repository.close()


def test_backup_requires_initialized_repository(db_path, tmp_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    backup_path = tmp_path / "empty-backup.db"
    repository.backup(backup_path)
    assert backup_path.exists()
    repository.close()

def test_export_current_and_import_current_roundtrip_only_current_facts(batch, db_path, tmp_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    repository.write(batch, "export-source")
    total_rows_before = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

    exported = repository.export_current()
    assert exported["sources"]
    assert exported["facts"]
    assert "fact-old" not in {fact["fact_id"] for fact in exported["facts"]}
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == total_rows_before
    repository.close()

    imported = Repository(tmp_path / "imported-current.db")
    receipt = imported.import_current(exported, "import-current-1")
    roundtrip = imported.export_current()
    assert receipt.submission_key == "import-current-1"
    assert {fact["fact_id"] for fact in roundtrip["facts"]} == {fact["fact_id"] for fact in exported["facts"]}
    assert roundtrip["sources"] == exported["sources"]
    assert len(roundtrip["direct_nodes"]) == len(exported["direct_nodes"])
    imported.close()


def test_import_current_rejects_invalid_batch_without_mutating_repository(batch, db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    repository.write(batch, "existing")
    before = {
        table: repository.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("sources", "facts", "attributes", "submissions", "inventories")
    }
    invalid = json.loads(json.dumps(batch))
    invalid["facts"][0]["node"]["node_id"] = ""
    try:
        repository.import_current(invalid, "invalid-import")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid import must be rejected")
    after = {
        table: repository.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in before
    }
    assert after == before
    repository.close()

def test_restore_rejects_empty_sqlite_file_without_changing_fact_history(batch, db_path, tmp_path):
    import sqlite3
    import pytest
    from semantic_facts.repository.store import Repository

    empty_backup = tmp_path / "empty-valid-sqlite.db"
    with sqlite3.connect(empty_backup):
        pass

    repository = Repository(db_path)
    repository.write(batch, "restore-empty-backup-protection")
    before_facts = repository.connection.execute("SELECT fact_key, payload FROM facts ORDER BY fact_key").fetchall()
    before_sources = repository.connection.execute("SELECT source_id, payload FROM sources ORDER BY source_id").fetchall()

    with pytest.raises(ValueError, match="repository schema"):
        repository.restore(empty_backup)

    assert repository.connection.execute("SELECT fact_key, payload FROM facts ORDER BY fact_key").fetchall() == before_facts
    assert repository.connection.execute("SELECT source_id, payload FROM sources ORDER BY source_id").fetchall() == before_sources
    repository.close()

def test_import_current_conflicting_identity_preserves_existing_fact_history(batch, db_path):
    import copy
    import pytest
    from semantic_facts.repository.store import Repository
    from semantic_facts.repository.types import WriteConflict

    repository = Repository(db_path)
    repository.write(batch, "import-conflict-base")
    before = {
        table: repository.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("sources", "facts", "attributes", "relations", "evidence", "submissions")
    }
    conflicting = copy.deepcopy(batch)
    conflicting["facts"][0]["granularities"] = ["L2"]

    with pytest.raises(WriteConflict):
        repository.import_current(conflicting, "import-conflicting-fact")

    after = {
        table: repository.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in before
    }
    assert after == before
    assert repository.connection.execute(
        "SELECT submission_key FROM submissions WHERE submission_key = ?",
        ("import-conflicting-fact",),
    ).fetchone() is None
    repository.close()

def test_restore_rejects_wrong_repository_schema_without_changing_fact_history(batch, db_path, tmp_path):
    import sqlite3
    import pytest
    from semantic_facts.repository.store import Repository

    malformed = tmp_path / "malformed-repository-schema.db"
    with sqlite3.connect(malformed) as connection:
        for table in ("sources", "entities", "facts", "attributes", "relations", "submissions"):
            connection.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")

    repository = Repository(db_path)
    repository.write(batch, "restore-malformed-schema-protection")
    before_facts = repository.connection.execute("SELECT fact_key, payload FROM facts ORDER BY fact_key").fetchall()
    before_sources = repository.connection.execute("SELECT source_id, payload FROM sources ORDER BY source_id").fetchall()

    with pytest.raises(ValueError, match="repository schema"):
        repository.restore(malformed)

    assert repository.connection.execute("SELECT fact_key, payload FROM facts ORDER BY fact_key").fetchall() == before_facts
    assert repository.connection.execute("SELECT source_id, payload FROM sources ORDER BY source_id").fetchall() == before_sources
    repository.close()
