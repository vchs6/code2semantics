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
