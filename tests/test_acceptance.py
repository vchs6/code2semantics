import json
from pathlib import Path

from semantic_facts.cli import main
from semantic_facts.repository.store import Repository
from semantic_facts.query_engine import execute_query, execute_query_with_construction


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "tests" / "fixtures" / "scenarios" / "python_project"


def test_real_source_scan_store_reopen_and_query(tmp_path, capsys):
    database = tmp_path / "facts.db"
    batch_path = tmp_path / "fact-batch.json"

    assert main([
        "scan-python",
        "--root", str(SCENARIO),
        "--db", str(database),
        "--output", str(batch_path),
    ]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "stored"
    assert report["fact_count"] >= 1

    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    assert batch["facts"]
    assert batch["facts"][0]["fields"]["names"]["basis"]["evidence"]

    query = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "acceptance-query-1",
        "scope": {
            "scope_id": "acceptance-scope",
            "directories": [str(SCENARIO)],
            "excludes": [],
            "defaulted": False,
        },
        "target": {"kind": "scope"},
        "granularity": "L3",
        "selections": [{"fact_type": "F2", "fields": ["identity", "names"]}],
        "budget": {"max_rounds": 1, "max_new_assertions": 20},
    }

    repository = Repository(database)
    repository.close()
    reopened = Repository(database)
    result = execute_query(query, reopened, ROOT / "skills" / "layered-semantic-facts" / "assets")
    assert result["termination"] == "satisfied"
    assert result["results"]
    assert any("class RepositoryReader" in fact["fields"]["names"]["value"]["text"] for fact in result["results"])
    assert all(fact["fields"]["names"]["basis"]["evidence"] for fact in result["results"])

    query_path = tmp_path / "query.json"
    query_path.write_text(json.dumps(query, ensure_ascii=False), encoding="utf-8")
    assert main(["query", "--db", str(database), "--query-file", str(query_path)]) == 0
    cli_response = json.loads(capsys.readouterr().out)
    assert cli_response["termination"] == "satisfied"
    assert cli_response["results"]

    query_with_missing_field = dict(query)
    query_with_missing_field["selections"] = [{"fact_type": "F2", "fields": ["purpose"]}]
    incomplete = execute_query(query_with_missing_field, reopened, ROOT / "skills" / "layered-semantic-facts" / "assets")
    assert incomplete["termination"] == "satisfied"
    assert incomplete["gaps"] == []
    assert incomplete["out_of_catalog"][0]["fields"] == ["purpose"]
    counts_before = reopened.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    reopened.close()

    # Re-running the exact same scan is idempotent and never deletes fact rows.
    assert main(["scan-python", "--root", str(SCENARIO), "--db", str(database)]) == 0
    capsys.readouterr()
    final = Repository(database)
    counts_after = final.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    assert counts_after == counts_before
    final.close()


def test_changed_source_appends_new_facts_without_deleting_old_versions(tmp_path, capsys):
    project = tmp_path / "versioned-project"
    project.mkdir()
    source_file = project / "service.py"
    source_file.write_text("def version_one():\n    return 1\n", encoding="utf-8")
    database = tmp_path / "versioned.db"

    assert main(["scan-python", "--root", str(project), "--db", str(database)]) == 0
    capsys.readouterr()

    def query():
        return {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "request_id": "versioned-query",
            "scope": {
                "scope_id": "versioned-scope",
                "directories": [str(project.resolve())],
                "excludes": [],
                "defaulted": False,
            },
            "target": {"kind": "scope"},
            "granularity": "L3",
            "selections": [{"fact_type": "F2", "fields": ["names"]}],
            "budget": {"max_rounds": 1, "max_new_assertions": 20},
        }

    repository = Repository(database)
    first = execute_query(query(), repository, ROOT / "skills" / "layered-semantic-facts" / "assets")
    assert any("function version_one" in fact["fields"]["names"]["value"]["text"] for fact in first["results"])
    old_source_ids = {source["source_id"] for source in first["sources"]}
    old_fact_keys = {
        row[0] for row in repository.connection.execute(
            "SELECT fact_key FROM facts WHERE source_id IN ({})".format(",".join("?" for _ in old_source_ids)),
            tuple(sorted(old_source_ids)),
        )
    }
    old_count = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    repository.close()

    source_file.write_text("def version_two():\n    return 2\n", encoding="utf-8")
    assert main(["scan-python", "--root", str(project), "--db", str(database)]) == 0
    capsys.readouterr()

    repository = Repository(database)
    total_count = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    total_sources = repository.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    assert total_count > old_count
    assert total_sources == 2
    assert old_source_ids.issubset({
        row[0] for row in repository.connection.execute("SELECT source_id FROM sources")
    })
    invalidated = {
        key: state for key, state in repository.connection.execute(
            "SELECT target_key, state FROM validity_events WHERE target_kind = 'fact' ORDER BY event_id"
        ) if key in old_fact_keys
    }
    assert set(invalidated) == old_fact_keys
    assert set(invalidated.values()) == {"modified"}

    current = execute_query(query(), repository, ROOT / "skills" / "layered-semantic-facts" / "assets")
    assert any("function version_two" in fact["fields"]["names"]["value"]["text"] for fact in current["results"])
    assert all("function version_one" not in fact["fields"]["names"]["value"]["text"] for fact in current["results"])
    assert len(current["sources"]) == 1
    count_after_second_version = total_count
    repository.close()

    # Reverting to an already-seen snapshot makes it current again without
    # deleting the newer version or creating duplicate fact rows.
    source_file.write_text("def version_one():\n    return 1\n", encoding="utf-8")
    assert main(["scan-python", "--root", str(project), "--db", str(database)]) == 0
    capsys.readouterr()
    repository = Repository(database)
    reverted = execute_query(query(), repository, ROOT / "skills" / "layered-semantic-facts" / "assets")
    assert any("function version_one" in fact["fields"]["names"]["value"]["text"] for fact in reverted["results"])
    assert all("function version_two" not in fact["fields"]["names"]["value"]["text"] for fact in reverted["results"])
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == count_after_second_version
    assert repository.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 2
    restored_states = {
        key: state for key, state in repository.connection.execute(
            "SELECT target_key, state FROM validity_events WHERE target_kind = 'fact' ORDER BY event_id"
        ) if key in old_fact_keys
    }
    assert set(restored_states.values()) == {"current"}
    repository.close()

def test_real_rust_source_scan_store_reopen_and_query(tmp_path, capsys):
    rust_project = tmp_path / "rust-project"
    (rust_project / "src").mkdir(parents=True)
    (rust_project / "src" / "lib.rs").write_text(
        "use std::fmt::Debug;\npub struct Engine;\npub enum Mode { Fast, Safe }\n\nimpl Engine {\n    pub fn run() {}\n}\n",
        encoding="utf-8",
    )
    database = tmp_path / "rust-facts.db"
    batch_path = tmp_path / "rust-fact-batch.json"

    assert main(["scan-python", "--root", str(rust_project), "--db", str(database), "--output", str(batch_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "stored"
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    names = batch["facts"][0]["fields"]["names"]["value"]["text"]
    assert "struct Engine" in names
    assert "enum Mode" in names
    assert "fn run" in names
    assert batch["facts"][0]["fields"]["names"]["context"]["environment"]["language"] == "Rust"

    query = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "rust-acceptance-query",
        "scope": {"scope_id": "rust-scope", "directories": [str(rust_project)], "excludes": [], "defaulted": False},
        "target": {"kind": "scope"},
        "granularity": "L3",
        "selections": [{"fact_type": "F2", "fields": ["identity", "names"]}],
        "budget": {"max_rounds": 1, "max_new_assertions": 20},
    }
    query_path = tmp_path / "rust-query.json"
    query_path.write_text(json.dumps(query), encoding="utf-8")
    assert main(["query", "--db", str(database), "--query-file", str(query_path)]) == 0
    response = json.loads(capsys.readouterr().out)
    assert response["termination"] == "satisfied"
    assert any("struct Engine" in fact["fields"]["names"]["value"]["text"] for fact in response["results"])
def test_partial_fact_updates_append_missing_attributes_and_reject_conflicts(tmp_path):
    import copy
    import pytest
    from semantic_facts.repository.types import WriteConflict
    from semantic_facts.repository.contract import ContractCodec
    from semantic_facts.source_scanner import build_fact_batch

    project = tmp_path / "partial-project"
    project.mkdir()
    (project / "service.py").write_text("class Example:\n    def run(self):\n        return 1\n", encoding="utf-8")
    batch = build_fact_batch(project, ContractCodec(ROOT / "skills" / "layered-semantic-facts" / "assets"))
    identity_batch = copy.deepcopy(batch)
    identity_batch["facts"][0]["fields"] = {"identity": batch["facts"][0]["fields"]["identity"]}
    names_batch = copy.deepcopy(batch)
    names_batch["facts"][0]["fields"] = {"names": batch["facts"][0]["fields"]["names"]}

    repository = Repository(tmp_path / "partial.db")
    repository.write(identity_batch, "identity-only")
    repository.write(names_batch, "names-only")
    fact_count = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    attribute_names = {
        row[0] for row in repository.connection.execute("SELECT field_name FROM attributes")
    }
    assert fact_count == 1
    assert {"identity", "names"} <= attribute_names

    conflicting = copy.deepcopy(names_batch)
    conflicting["facts"][0]["fields"]["names"]["value"]["text"] += "; conflicting rewrite"
    before = repository.connection.execute(
        "SELECT attribute_key, payload FROM attributes ORDER BY attribute_key"
    ).fetchall()
    with pytest.raises(WriteConflict):
        repository.write(conflicting, "conflicting-names")
    after = repository.connection.execute(
        "SELECT attribute_key, payload FROM attributes ORDER BY attribute_key"
    ).fetchall()
    assert after == before
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == fact_count
    repository.close()

def test_first_phase_acceptance_combines_python_and_rust_projects_without_identity_collision(tmp_path):
    python_project = tmp_path / "python-project"
    rust_project = tmp_path / "rust-project"
    python_project.mkdir()
    (rust_project / "src").mkdir(parents=True)
    (python_project / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")
    (rust_project / "src" / "lib.rs").write_text("pub struct Engine;\n", encoding="utf-8")

    query = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "multi-project-first-phase",
        "scope": {
            "scope_id": "python-rust-scope",
            "directories": [str(python_project.resolve()), str(rust_project.resolve())],
            "excludes": [],
            "defaulted": False,
        },
        "target": {"kind": "scope"},
        "granularity": "L3",
        "selections": [{"fact_type": "F2", "fields": ["identity", "names", "purpose"]}],
        "budget": {"max_rounds": 2, "max_new_assertions": 30},
    }
    database = tmp_path / "multi-project.db"
    repository = Repository(database, ROOT / "skills" / "layered-semantic-facts" / "assets")
    try:
        response = execute_query_with_construction(
            query, repository, ROOT / "skills" / "layered-semantic-facts" / "assets"
        )
        assert response["termination"] == "satisfied", response
        assert len(response["sources"]) == 2
        same_named = [
            fact for fact in response["results"]
            if "Engine" in fact["fields"]["names"]["value"]["text"]
        ]
        assert len(same_named) == 2
        assert len({fact["node"]["source_id"] for fact in same_named}) == 2
        assert len({fact["node"]["subject_id"] for fact in same_named}) == 2
        assert response["out_of_catalog"] == [{
            "fact_type": "F2",
            "fields": ["purpose"],
            "reason": "No fixed first-phase information need covers these fields.",
        }]
        assert response["gaps"] == []
        assert all(set(fact["fields"]) <= {"identity", "names"} for fact in response["results"])
        assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] >= 2
    finally:
        repository.close()

def test_deleted_source_file_is_excluded_from_current_query_but_history_is_retained(tmp_path):
    project = tmp_path / "deleted-file-project"
    project.mkdir()
    first_file = project / "first.py"
    deleted_file = project / "to_delete.py"
    first_file.write_text("class First:\n    pass\n", encoding="utf-8")
    deleted_file.write_text("class ToDelete:\n    pass\n", encoding="utf-8")
    database = tmp_path / "deleted-file.db"
    codec = __import__("semantic_facts.repository.contract", fromlist=["ContractCodec"]).ContractCodec(
        ROOT / "skills" / "layered-semantic-facts" / "assets"
    )
    from semantic_facts.source_scanner import build_fact_batch

    initial_batch = build_fact_batch(project, codec)
    repository = Repository(database, ROOT / "skills" / "layered-semantic-facts" / "assets")
    repository.write(initial_batch, "initial-snapshot")
    old_source_id = initial_batch["sources"][0]["source_id"]
    old_fact_count = repository.connection.execute(
        "SELECT COUNT(*) FROM facts WHERE source_id = ?", (old_source_id,)
    ).fetchone()[0]
    assert any("class ToDelete" in fact["fields"]["names"]["value"]["text"] for fact in initial_batch["facts"])

    deleted_file.unlink()
    new_batch = build_fact_batch(project, codec)
    repository.write(new_batch, "after-file-deletion")
    assert new_batch["sources"][0]["source_id"] != old_source_id
    assert repository.connection.execute(
        "SELECT COUNT(*) FROM facts WHERE source_id = ?", (old_source_id,)
    ).fetchone()[0] == old_fact_count

    query = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "after-source-file-deletion",
        "scope": {
            "scope_id": "deleted-file-scope",
            "directories": [str(project.resolve())],
            "excludes": [],
            "defaulted": False,
        },
        "target": {"kind": "scope"},
        "granularity": "L3",
        "selections": [{"fact_type": "F2", "fields": ["identity", "names"]}],
        "budget": {"max_rounds": 1, "max_new_assertions": 20},
    }
    current = execute_query(query, repository, ROOT / "skills" / "layered-semantic-facts" / "assets")
    assert len(current["sources"]) == 1
    assert current["sources"][0]["source_id"] == new_batch["sources"][0]["source_id"]
    assert all("class ToDelete" not in fact["fields"]["names"]["value"]["text"] for fact in current["results"])
    assert any("class First" in fact["fields"]["names"]["value"]["text"] for fact in current["results"])
    assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] > old_fact_count
    repository.close()

def test_root_acceptance_unavailable_source_never_falls_back(tmp_path):
    missing = tmp_path / "not-created-project"
    query = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "unavailable-root-acceptance",
        "scope": {"scope_id": "unavailable-scope", "directories": [str(missing)], "excludes": [], "defaulted": False},
        "target": {"kind": "scope"},
        "granularity": "L3",
        "selections": [{"fact_type": "F2", "fields": ["identity", "names"]}],
        "budget": {"max_rounds": 1, "max_new_assertions": 10},
    }
    repository = Repository(tmp_path / "unavailable-root.db", ROOT / "skills" / "layered-semantic-facts" / "assets")
    try:
        response = execute_query_with_construction(
            query, repository, ROOT / "skills" / "layered-semantic-facts" / "assets"
        )
        assert response["termination"] == "unavailable"
        assert response["sources"][0]["status"] == "unavailable"
        assert any(gap["reason"] == "source_unavailable" for gap in response["gaps"])
        assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 0
    finally:
        repository.close()


def test_root_acceptance_rejects_out_of_scope_target_before_repository_read(tmp_path):
    from semantic_facts.repository.contract import ContractCodec
    from semantic_facts.source_scanner import build_fact_batch

    allowed = tmp_path / "allowed-project"
    foreign = tmp_path / "foreign-project"
    allowed.mkdir()
    foreign.mkdir()
    (allowed / "allowed.py").write_text("class Allowed:\n    pass\n", encoding="utf-8")
    (foreign / "foreign.py").write_text("class SecretOutsideScope:\n    pass\n", encoding="utf-8")
    assets = ROOT / "skills" / "layered-semantic-facts" / "assets"
    codec = ContractCodec(assets)
    foreign_batch = build_fact_batch(foreign, codec)

    repository = Repository(tmp_path / "scope-boundary.db", assets)
    try:
        repository.write(foreign_batch, "foreign-seed")
        foreign_node = foreign_batch["facts"][0]["node"]
        query = {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "request_id": "out-of-scope-target-acceptance",
            "scope": {"scope_id": "allowed-only", "directories": [str(allowed.resolve())], "excludes": [], "defaulted": False},
            "target": {"kind": "node", "node": foreign_node},
            "granularity": "L3",
            "selections": [{"fact_type": "F2", "fields": ["identity", "names"]}],
            "budget": {"max_rounds": 1, "max_new_assertions": 10},
        }
        response = execute_query_with_construction(query, repository, assets)
        assert response["termination"] == "no_progress"
        assert any(gap["reason"] == "invalid_reference" for gap in response["gaps"])
        assert all(source["root"] == str(allowed.resolve()) for source in response["sources"])
        assert all(fact["node"]["source_id"] != foreign_node["source_id"] for fact in response["results"])
        assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == len(foreign_batch["facts"])
    finally:
        repository.close()

def test_local_invalidation_targets_current_source_head_without_deleting_history(tmp_path, capsys):
    import hashlib

    project = tmp_path / "invalidation-project"
    project.mkdir()
    source_file = project / "module.py"
    source_file.write_text("def first():\n    return 1\n", encoding="utf-8")
    database = tmp_path / "invalidation.db"
    assert main(["scan-source", "--root", str(project), "--db", str(database)]) == 0
    capsys.readouterr()

    source_file.write_text("def second():\n    return 2\n", encoding="utf-8")
    assert main(["scan-source", "--root", str(project), "--db", str(database)]) == 0
    capsys.readouterr()

    fact_id = "fact-" + hashlib.sha256(("module.py" + "\\0F2").encode("utf-8")).hexdigest()[:20]
    repository = Repository(database)
    rows = repository.connection.execute(
        "SELECT f.fact_key, f.source_id, a.attribute_key FROM facts f "
        "JOIN attributes a ON a.fact_key = f.fact_key "
        "WHERE f.fact_id = ? AND a.field_name = ? ORDER BY f.source_id",
        (fact_id, "names"),
    ).fetchall()
    assert len(rows) == 2
    current_source_id = repository.connection.execute(
        "SELECT source_id FROM source_heads WHERE root = ?", (str(project.resolve()),)
    ).fetchone()[0]
    current_row = next(row for row in rows if row[1] == current_source_id)
    old_row = next(row for row in rows if row[1] != current_source_id)

    repository.invalidate_field(fact_id, "names", "explicit local invalidation test")
    event = repository.connection.execute(
        "SELECT target_key FROM validity_events WHERE target_kind = 'field' ORDER BY event_id DESC LIMIT 1"
    ).fetchone()[0]
    assert event == current_row[2]
    assert event != old_row[2]
    assert repository.connection.execute("SELECT COUNT(*) FROM facts WHERE fact_id = ?", (fact_id,)).fetchone()[0] == 2
    repository.close()

def test_query_cli_rebuilds_current_snapshot_after_source_file_deletion(tmp_path, capsys):
    project = tmp_path / "query-cli-deleted-source"
    project.mkdir()
    stable = project / "stable.py"
    removed = project / "removed.py"
    stable.write_text("""class Stable:
    pass
""", encoding="utf-8")
    removed.write_text("""class Removed:
    pass
""", encoding="utf-8")
    database = tmp_path / "query-cli-deleted-source.db"

    assert main(["scan-source", "--root", str(project), "--db", str(database)]) == 0
    capsys.readouterr()
    repository = Repository(database)
    old_source_id = repository.connection.execute(
        "SELECT source_id FROM source_heads WHERE root = ?", (str(project.resolve()),)
    ).fetchone()[0]
    old_fact_count = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    old_fact_keys = {
        row[0] for row in repository.connection.execute("SELECT fact_key FROM facts")
    }
    repository.close()

    removed.unlink()
    query = {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "query-cli-after-source-deletion",
        "scope": {
            "scope_id": "query-cli-deleted-scope",
            "directories": [str(project.resolve())],
            "excludes": [],
            "defaulted": False,
        },
        "target": {"kind": "scope"},
        "granularity": "L3",
        "selections": [{"fact_type": "F2", "fields": ["identity", "names"]}],
        "budget": {"max_rounds": 2, "max_new_assertions": 20},
    }
    query_path = tmp_path / "query.json"
    query_path.write_text(json.dumps(query, ensure_ascii=False), encoding="utf-8")

    assert main(["query", "--db", str(database), "--query-file", str(query_path)]) == 0
    response = json.loads(capsys.readouterr().out)

    assert response["termination"] == "satisfied", response
    assert any("class Stable" in fact["fields"]["names"]["value"]["text"] for fact in response["results"])
    assert all("class Removed" not in fact["fields"]["names"]["value"]["text"] for fact in response["results"])
    current_source_ids = {source["source_id"] for source in response["sources"]}
    assert old_source_id not in current_source_ids
    assert {fact["node"]["source_id"] for fact in response["results"]} <= current_source_ids

    repository = Repository(database)
    try:
        current_source_id = repository.connection.execute(
            "SELECT source_id FROM source_heads WHERE root = ?", (str(project.resolve()),)
        ).fetchone()[0]
        assert current_source_id in current_source_ids
        assert current_source_id != old_source_id
        assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] > old_fact_count
        assert old_fact_keys <= {
            row[0] for row in repository.connection.execute("SELECT fact_key FROM facts")
        }
        assert repository.connection.execute(
            "SELECT 1 FROM validity_events WHERE target_kind = 'source' AND target_key = ? AND state = 'modified'",
            (old_source_id,),
        ).fetchone() is not None
    finally:
        repository.close()
