import json
from pathlib import Path

from semantic_facts.cli import main
from semantic_facts.repository.store import Repository
from semantic_facts.query_engine import execute_query


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
    assert incomplete["termination"] == "no_progress"
    assert incomplete["gaps"][0]["fields"] == ["purpose"]
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

    current = execute_query(query(), repository, ROOT / "skills" / "layered-semantic-facts" / "assets")
    assert any("function version_two" in fact["fields"]["names"]["value"]["text"] for fact in current["results"])
    assert all("function version_one" not in fact["fields"]["names"]["value"]["text"] for fact in current["results"])
    assert len(current["sources"]) == 1
    repository.close()
