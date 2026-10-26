import json
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
    assert "fact-b" not in {fact["fact_id"] for fact in result["facts"]}
    assert "fact-old" not in {fact["fact_id"] for fact in result["facts"]}
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == len(batch["facts"])
    assert repository.connection.execute("SELECT COUNT(*) FROM attributes").fetchone()[0] >= len(batch["facts"])
    repository.close()


def test_current_read_excludes_assertion_whose_evidence_state_is_stale(batch, db_path):
    from semantic_facts.repository.store import Repository

    stale_fact = next(fact for fact in batch["facts"] if fact["fact_id"] == "fact-a")
    evidence = stale_fact["fields"]["strategy"]["basis"]["evidence"][0]
    evidence["evidence_id"] = "ev-stale-test"
    evidence["content_state"] = "sha256:" + "0" * 64

    repository = Repository(db_path)
    repository.write(batch, "submission-stale-evidence")
    result = repository.read(make_query())

    assert "fact-a" not in {fact["fact_id"] for fact in result["facts"]}
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == len(batch["facts"])
    repository.close()


def test_field_invalidation_is_append_only_and_can_be_explicitly_revalidated(batch, db_path):
    from semantic_facts.repository.store import Repository
    from test_store import make_query

    repository = Repository(db_path)
    repository.write(batch, "validity-field")
    fact_key = repository.connection.execute("SELECT fact_key FROM facts WHERE fact_id = 'fact-a'").fetchone()[0]
    attribute_key = repository.connection.execute(
        "SELECT attribute_key FROM attributes WHERE fact_key = ? AND field_name = 'strategy'",
        (fact_key,),
    ).fetchone()[0]
    fact_rows_before = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    repository.invalidate_field("fact-a", "strategy", "manual evidence review required")

    result = repository.read(make_query())
    assert "fact-a" not in {fact["fact_id"] for fact in result["facts"]}
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == fact_rows_before
    assert repository.connection.execute(
        "SELECT COUNT(*) FROM attributes WHERE attribute_key = ?", (attribute_key,)
    ).fetchone()[0] == 1

    repository.record_validity_event("field", attribute_key, "current", "revalidated against current evidence")
    result = repository.read(make_query())
    assert "fact-a" in {fact["fact_id"] for fact in result["facts"]}
    assert repository.connection.execute("SELECT COUNT(*) FROM validity_events").fetchone()[0] == 2
    repository.close()


def test_evidence_invalidation_hides_dependent_assertions_without_deleting_evidence(batch, db_path):
    from semantic_facts.repository.store import Repository
    from test_store import make_query

    repository = Repository(db_path)
    repository.write(batch, "validity-evidence")
    fact = next(item for item in batch["facts"] if item["fact_id"] == "fact-a")
    evidence = fact["fields"]["strategy"]["basis"]["evidence"][0]
    evidence_rows_before = repository.connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    fact_rows_before = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

    repository.invalidate_evidence(evidence["source_id"], evidence["evidence_id"], "source evidence withdrawn")
    result = repository.read(make_query())
    assert "fact-a" not in {item["fact_id"] for item in result["facts"]}
    assert repository.connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == evidence_rows_before
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == fact_rows_before
    repository.close()


def test_relation_and_conflict_invalidation_filters_projection_only(batch, db_path):
    from semantic_facts.repository.store import Repository
    from test_store import make_query

    repository = Repository(db_path)
    repository.write(batch, "validity-relations")
    query = make_query()
    target_node = query["target"]["node"]
    relation = next(
        (
            (key, payload)
            for key, payload in repository.connection.execute(
                "SELECT relation_key, payload FROM relations WHERE navigation = 1"
            )
            if json.loads(payload).get("source") == target_node
        ),
        None,
    )
    assert relation is not None
    conflict_id = batch["conflicts"][0]["conflict_id"]
    relation_rows_before = repository.connection.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    conflict_rows_before = repository.connection.execute("SELECT COUNT(*) FROM conflicts").fetchone()[0]

    repository.invalidate_relation(relation[0], "navigation evidence changed")
    repository.invalidate_conflict(conflict_id, "conflict resolution superseded")
    result = repository.read(make_query())

    assert all(edge["edge_id"] != json.loads(relation[1])["edge_id"] for edge in result["navigation"])
    assert conflict_id not in {item["conflict_id"] for item in result["conflicts"]}
    assert repository.connection.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == relation_rows_before
    assert repository.connection.execute("SELECT COUNT(*) FROM conflicts").fetchone()[0] == conflict_rows_before
    repository.close()

def test_invalidated_premise_target_hides_dependent_assertion_without_deleting_rows(batch, db_path):
    from semantic_facts.repository.store import Repository
    from test_store import make_query

    repository = Repository(db_path)
    repository.write(batch, "premise-closure")
    fact_rows_before = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    dependent = next(item for item in batch["facts"] if item["fact_id"] == "fact-b")
    assert dependent["fields"]["strategy"]["basis"]["premises"]

    repository.invalidate_field("fact-a", "strategy", "premise target changed")
    query = make_query()
    query["selections"] = [{"fact_type": "F16", "fields": ["strategy"]}]
    result = repository.read(query)

    returned_ids = {fact["fact_id"] for fact in result["facts"]}
    assert "fact-a" not in returned_ids
    assert "fact-b" not in returned_ids
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == fact_rows_before
    assert repository.connection.execute("SELECT COUNT(*) FROM premises").fetchone()[0] >= 1
    repository.close()


def test_cyclic_premise_closure_is_rejected_without_recursion_or_deletion(batch, db_path):
    import copy
    from semantic_facts.repository.store import Repository
    from test_store import make_query

    cyclic = copy.deepcopy(batch)
    fact_a = next(item for item in cyclic["facts"] if item["fact_id"] == "fact-a")
    fact_b = next(item for item in cyclic["facts"] if item["fact_id"] == "fact-b")
    fact_a["fields"]["strategy"]["basis"]["premises"].append({
        "node": fact_b["node"],
        "fact_id": "fact-b",
        "field": "strategy",
        "content_state": "content-a",
    })
    repository = Repository(db_path)
    repository.write(cyclic, "cyclic-premise-closure")
    fact_rows_before = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    query = make_query()
    query["selections"] = [{"fact_type": "F16", "fields": ["strategy"]}]

    result = repository.read(query)
    returned_ids = {fact["fact_id"] for fact in result["facts"]}
    assert "fact-a" not in returned_ids
    assert "fact-b" not in returned_ids
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == fact_rows_before
    repository.close()