import json
from pathlib import Path

from semantic_facts.query_engine import execute_query_with_construction
from semantic_facts.repository.store import Repository

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "skills" / "layered-semantic-facts" / "assets"


def make_query(project: Path, fields=("identity", "names")):
    return {
        "contract_version": "1.0.0",
        "catalog_id": "semantic-facts-20261025",
        "request_id": "query-orchestration",
        "scope": {
            "scope_id": "scope-query",
            "directories": [str(project.resolve())],
            "excludes": [],
            "defaulted": False,
        },
        "target": {"kind": "scope"},
        "granularity": "L3",
        "selections": [{"fact_type": "F2", "fields": list(fields)}],
        "budget": {"max_rounds": 2, "max_new_assertions": 20},
    }


def test_query_constructs_missing_current_facts_then_re_reads_them(tmp_path):
    project = tmp_path / "query-project"
    project.mkdir()
    (project / "engine.py").write_text(
        "class Engine:\n    def run(self):\n        return True\n",
        encoding="utf-8",
    )
    database = tmp_path / "query.db"
    repository = Repository(database, ASSETS)
    try:
        response = execute_query_with_construction(make_query(project), repository, ASSETS)
        assert response["termination"] == "satisfied"
        assert response["gaps"] == []
        assert response["results"]
        assert any("class Engine" in fact["fields"]["names"]["value"]["text"] for fact in response["results"])
        assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] >= 1
    finally:
        repository.close()


def test_query_reports_fixed_catalogue_gap_without_inventing_or_deleting_facts(tmp_path):
    project = tmp_path / "query-project"
    project.mkdir()
    (project / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")
    database = tmp_path / "query.db"
    repository = Repository(database, ASSETS)
    try:
        response = execute_query_with_construction(make_query(project, ("purpose",)), repository, ASSETS)
        assert response["termination"] == "no_progress"
        assert response["gaps"][0]["reason"] == "uncovered_need"
        assert response["gaps"][0]["fields"] == ["purpose"]
        assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 0
    finally:
        repository.close()


def test_query_uses_current_source_snapshot_and_keeps_old_fact_rows(tmp_path):
    project = tmp_path / "query-project"
    project.mkdir()
    source = project / "engine.py"
    source.write_text("class FirstEngine:\n    pass\n", encoding="utf-8")
    database = tmp_path / "query.db"
    repository = Repository(database, ASSETS)
    try:
        first = execute_query_with_construction(make_query(project), repository, ASSETS)
        assert any("class FirstEngine" in fact["fields"]["names"]["value"]["text"] for fact in first["results"])
        first_count = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

        source.write_text("class SecondEngine:\n    pass\n", encoding="utf-8")
        second = execute_query_with_construction(make_query(project), repository, ASSETS)
        assert any("class SecondEngine" in fact["fields"]["names"]["value"]["text"] for fact in second["results"])
        assert all("class FirstEngine" not in fact["fields"]["names"]["value"]["text"] for fact in second["results"])
        assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] > first_count
    finally:
        repository.close()
