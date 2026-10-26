import copy

import pytest


def test_same_submission_replays_without_duplicate_rows(batch, db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    first = repository.write(batch, "submission-1")
    before = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    second = repository.write(copy.deepcopy(batch), "submission-1")
    after = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

    assert second.digest == first.digest
    assert before == after
    assert repository.connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 1
    repository.close()


def test_same_submission_with_different_content_is_rejected(batch, db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    repository.write(batch, "submission-1")
    changed = copy.deepcopy(batch)
    changed["facts"][0]["fields"]["strategy"]["context"]["environment"]["profile"] = "release"

    with pytest.raises(ValueError):
        repository.write(changed, "submission-1")
    assert repository.connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 1
    repository.close()


def test_invalid_reference_does_not_change_existing_state(batch, db_path):
    from semantic_facts.repository.store import Repository

    repository = Repository(db_path)
    repository.write(batch, "submission-1")
    invalid = copy.deepcopy(batch)
    invalid["facts"][0]["node"]["node_id"] = ""

    with pytest.raises(ValueError):
        repository.write(invalid, "submission-2")
    assert repository.connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 1
    repository.close()



def test_new_submission_cannot_replace_existing_fact_history(batch, db_path):
    from semantic_facts.repository.store import Repository
    from semantic_facts.repository.types import WriteConflict

    repository = Repository(db_path)
    repository.write(batch, "submission-1")
    before_facts = repository.connection.execute(
        "SELECT fact_key, payload FROM facts ORDER BY fact_key"
    ).fetchall()
    before_submissions = repository.connection.execute(
        "SELECT submission_key, digest FROM submissions ORDER BY submission_key"
    ).fetchall()

    changed = copy.deepcopy(batch)
    changed["facts"][0]["granularities"] = ["L2"]

    with pytest.raises(WriteConflict):
        repository.write(changed, "submission-2")

    after_facts = repository.connection.execute(
        "SELECT fact_key, payload FROM facts ORDER BY fact_key"
    ).fetchall()
    after_submissions = repository.connection.execute(
        "SELECT submission_key, digest FROM submissions ORDER BY submission_key"
    ).fetchall()
    assert after_facts == before_facts
    assert after_submissions == before_submissions
    repository.close()
