from test_store import make_query


def test_current_read_excludes_invalid_assertion_without_deleting_it(batch, db_path):
    from semantic_facts.repository.store import Repository

    invalid_fact = next(fact for fact in batch["facts"] if fact["fact_id"] == "fact-a")
    assertion = invalid_fact["fields"]["strategy"]
    assertion["validity"]["state"] = "modified"
    assertion["validity"]["reason"] = "source changed"

    repository = Repository(db_path)
    repository.write(batch, "submission-invalid-state")
    result = repository.read(make_query())

    assert "fact-a" not in {fact["fact_id"] for fact in result["facts"]}
    assert "fact-b" in {fact["fact_id"] for fact in result["facts"]}
    assert "fact-old" not in {fact["fact_id"] for fact in result["facts"]}
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == len(batch["facts"])
    assert repository.connection.execute("SELECT COUNT(*) FROM attributes").fetchone()[0] >= len(batch["facts"])
    repository.close()


def test_current_read_excludes_assertion_whose_evidence_state_is_stale(batch, db_path):
    from semantic_facts.repository.store import Repository

    stale_fact = next(fact for fact in batch["facts"] if fact["fact_id"] == "fact-a")
    evidence_id = stale_fact["fields"]["strategy"]["basis"]["evidence"][0]["evidence_id"]
    def update_evidence(value):
        if isinstance(value, dict):
            if value.get("evidence_id") == evidence_id:
                value["content_state"] = "sha256:" + "0" * 64
            for child in value.values():
                update_evidence(child)
        elif isinstance(value, list):
            for child in value:
                update_evidence(child)

    update_evidence(batch)

    repository = Repository(db_path)
    repository.write(batch, "submission-stale-evidence")
    result = repository.read(make_query())

    assert "fact-a" not in {fact["fact_id"] for fact in result["facts"]}
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == len(batch["facts"])
    repository.close()
