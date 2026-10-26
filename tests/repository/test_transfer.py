import json
import sqlite3

import pytest


def test_backup_and_restore_preserve_current_fact_set(batch, db_path, tmp_path):
    from semantic_facts.repository.store import Repository

    backup_path = tmp_path / "facts-backup.db"
    repository = Repository(db_path)
    repository.write(batch, "submission-1")
    original_count = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

    repository.backup(backup_path)
    repository.connection.execute("DELETE FROM attributes")
    repository.connection.execute("DELETE FROM facts")
    repository.connection.execute("DELETE FROM entities")
    repository.connection.execute("DELETE FROM sources")
    repository.connection.execute("DELETE FROM relations")
    repository.connection.execute("DELETE FROM submissions")
    repository.connection.commit()
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 0

    repository.restore(backup_path)
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == original_count
    assert repository.connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 1
    repository.close()


def test_restore_rejects_invalid_backup_without_changing_database(batch, db_path, tmp_path):
    from semantic_facts.repository.store import Repository

    invalid_backup = tmp_path / "invalid.db"
    invalid_backup.write_text("not a sqlite database", encoding="utf-8")

    repository = Repository(db_path)
    repository.write(batch, "submission-1")
    before = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

    with pytest.raises((ValueError, sqlite3.DatabaseError)):
        repository.restore(invalid_backup)

    after = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    assert after == before
    assert repository.connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 1
    repository.close()


def test_backup_requires_initialized_repository(db_path, tmp_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    backup_path = tmp_path / "empty-backup.db"
    repository.backup(backup_path)
    assert backup_path.exists()
    repository.close()
