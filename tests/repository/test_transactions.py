import copy
import json

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


def test_partial_field_update_appends_assertion_version_and_preserves_old_version(batch, db_path):
    from semantic_facts.repository.store import Repository
    from test_store import make_query

    repository = Repository(db_path)
    repository.write(batch, "field-version-1")
    fact = next(item for item in batch["facts"] if item["fact_id"] == "fact-a")
    old_value = fact["fields"]["strategy"]["value"]["text"]
    old_versions = repository.connection.execute(
        "SELECT COUNT(*) FROM attribute_versions"
    ).fetchone()[0]
    old_fact_rows = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

    updated = copy.deepcopy(batch)
    changed_fact = next(item for item in updated["facts"] if item["fact_id"] == "fact-a")
    changed_fact["fields"]["strategy"]["value"]["text"] = "new observed strategy"
    repository.write(updated, "field-version-2")

    result = repository.read(make_query())
    current = next(item for item in result["facts"] if item["fact_id"] == "fact-a")
    assert current["fields"]["strategy"]["value"]["text"] == "new observed strategy"
    assert repository.connection.execute("SELECT COUNT(*) FROM attribute_versions").fetchone()[0] == old_versions + 1
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == old_fact_rows
    history = [
        row[0] for row in repository.connection.execute(
            "SELECT payload FROM attribute_versions WHERE field_name = 'strategy'"
        )
    ]
    assert any(json.loads(payload)["value"]["text"] == old_value for payload in history)
    repository.close()
