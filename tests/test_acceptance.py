import json
from pathlib import Path

from semantic_facts.cli import main
from semantic_facts.repository.store import Repository


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
    result = reopened.read(query)
    assert result["facts"]
    assert any("class RepositoryReader" in fact["fields"]["names"]["value"]["text"] for fact in result["facts"])
    assert all(fact["fields"]["names"]["basis"]["evidence"] for fact in result["facts"])
    counts_before = reopened.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    reopened.close()

    # Re-running the exact same scan is idempotent and never deletes fact rows.
    assert main(["scan-python", "--root", str(SCENARIO), "--db", str(database)]) == 0
    capsys.readouterr()
    final = Repository(database)
    counts_after = final.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    assert counts_after == counts_before
    final.close()
