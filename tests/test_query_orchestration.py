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
        assert response["termination"] == "satisfied"
        assert response["gaps"] == []
        assert response["out_of_catalog"] == [{
            "fact_type": "F2",
            "fields": ["purpose"],
            "reason": "No fixed first-phase information need covers these fields.",
        }]
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


def test_query_requires_and_returns_current_scope_direct_node_completeness(tmp_path):
    project = tmp_path / "inventory-query-project"
    project.mkdir()
    (project / "engine.py").write_text(
        """class Engine:
    def run(self):
        return True
""",
        encoding="utf-8",
    )
    repository = Repository(tmp_path / "inventory.db", ASSETS)
    try:
        response = execute_query_with_construction(make_query(project), repository, ASSETS)
        assert response["termination"] == "satisfied"
        assert response["gaps"] == []
        assert len(response["direct_nodes"]) == 1
        inventory = response["direct_nodes"][0]
        assert inventory["target"]["kind"] == "scope"
        assert inventory["assertion"]["coverage"]["completeness"] == "complete"
        assert len(inventory["children"]) == 1
    finally:
        repository.close()


def test_query_rebuilds_missing_inventory_without_deleting_existing_facts(tmp_path):
    from semantic_facts.repository.contract import ContractCodec
    from semantic_facts.source_scanner import build_fact_batch

    project = tmp_path / "missing-inventory-project"
    project.mkdir()
    (project / "engine.py").write_text("""class Engine:
    pass
""", encoding="utf-8")
    batch = build_fact_batch(project, ContractCodec(ASSETS))
    batch["direct_nodes"] = []
    repository = Repository(tmp_path / "missing-inventory.db", ASSETS)
    try:
        repository.write(batch, "seed-without-inventory")
        fact_count_before = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        response = execute_query_with_construction(make_query(project), repository, ASSETS)
        fact_count_after = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        assert response["termination"] == "satisfied"
        assert response["gaps"] == []
        assert any(item["target"]["kind"] == "scope" for item in response["direct_nodes"])
        assert fact_count_after == fact_count_before
        assert repository.connection.execute("SELECT COUNT(*) FROM inventories").fetchone()[0] >= 1
    finally:
        repository.close()


def test_node_query_returns_only_target_fact_and_its_direct_inventory(tmp_path):
    from semantic_facts.repository.contract import ContractCodec
    from semantic_facts.source_scanner import build_fact_batch

    project = tmp_path / "node-query-project"
    project.mkdir()
    (project / "first.py").write_text("""class FirstEngine:
    pass
""", encoding="utf-8")
    (project / "second.py").write_text("""class SecondEngine:
    pass
""", encoding="utf-8")
    batch = build_fact_batch(project, ContractCodec(ASSETS))
    target_fact = next(fact for fact in batch["facts"] if "first.py" in fact["fields"]["identity"]["value"]["ref"]["node_id"] or fact["fields"]["locators"]["value"]["text"].startswith("first.py"))
    query = make_query(project)
    query["target"] = {"kind": "node", "node": target_fact["node"]}

    repository = Repository(tmp_path / "node-query.db", ASSETS)
    try:
        response = execute_query_with_construction(query, repository, ASSETS)
        assert response["termination"] == "satisfied", response
        assert len(response["results"]) == 1
        assert response["results"][0]["node"] == target_fact["node"]
        assert len(response["direct_nodes"]) == 1
        assert response["direct_nodes"][0]["target"]["node"] == target_fact["node"]
    finally:
        repository.close()

def test_query_multiple_disjoint_roots_keeps_project_sources_separate(tmp_path):
    first = tmp_path / "first-project"
    second = tmp_path / "second-project"
    first.mkdir()
    second.mkdir()
    (first / "engine.py").write_text("class FirstEngine:\n    pass\n", encoding="utf-8")
    (second / "engine.py").write_text("class SecondEngine:\n    pass\n", encoding="utf-8")
    query = make_query(first)
    query["scope"]["directories"] = [str(first.resolve()), str(second.resolve())]
    repository = Repository(tmp_path / "multi-root.db", ASSETS)
    try:
        response = execute_query_with_construction(query, repository, ASSETS)
        assert response["termination"] == "satisfied", response
        names = [fact["fields"]["names"]["value"]["text"] for fact in response["results"]]
        assert any("class FirstEngine" in value for value in names)
        assert any("class SecondEngine" in value for value in names)
        assert {source["root"] for source in response["sources"]} == {str(first.resolve()), str(second.resolve())}
        assert all(fact["node"]["source_id"] in {source["source_id"] for source in response["sources"]} for fact in response["results"])
    finally:
        repository.close()


def test_query_explicit_nested_roots_preserves_both_root_identities(tmp_path):
    parent = tmp_path / "parent-project"
    nested = parent / "nested-project"
    nested.mkdir(parents=True)
    (parent / "parent.py").write_text("class ParentEngine:\n    pass\n", encoding="utf-8")
    (nested / "nested.py").write_text("class NestedEngine:\n    pass\n", encoding="utf-8")
    query = make_query(parent)
    query["scope"]["directories"] = [str(parent.resolve()), str(nested.resolve())]
    repository = Repository(tmp_path / "nested-roots.db", ASSETS)
    try:
        response = execute_query_with_construction(query, repository, ASSETS)
        assert response["termination"] == "satisfied", response
        roots = {source["root"] for source in response["sources"]}
        assert roots == {str(parent.resolve()), str(nested.resolve())}
        assert len({source["source_id"] for source in response["sources"]}) == 2
    finally:
        repository.close()


def test_query_out_of_scope_node_reference_is_reported_without_reading_other_project(tmp_path):
    project = tmp_path / "authorized-project"
    project.mkdir()
    (project / "engine.py").write_text("class AuthorizedEngine:\n    pass\n", encoding="utf-8")
    query = make_query(project)
    query["target"] = {"kind": "node", "node": {"source_id": "src-outside", "subject_id": "outside", "node_id": "secret-node"}}
    repository = Repository(tmp_path / "out-of-scope.db", ASSETS)
    try:
        response = execute_query_with_construction(query, repository, ASSETS)
        assert response["termination"] == "no_progress"
        assert any(gap["reason"] == "invalid_reference" for gap in response["gaps"])
        assert all(source["root"] == str(project.resolve()) for source in response["sources"])
        assert all(fact["node"]["source_id"] != "src-outside" for fact in response["results"])
    finally:
        repository.close()
def test_query_unavailable_source_returns_gap_without_fallback(tmp_path):
    missing = tmp_path / "missing-project"
    query = make_query(missing)
    repository = Repository(tmp_path / "unavailable-source.db", ASSETS)
    try:
        response = execute_query_with_construction(query, repository, ASSETS)
        assert response["termination"] == "unavailable"
        assert response["sources"][0]["status"] == "unavailable"
        assert any(gap["reason"] == "source_unavailable" for gap in response["gaps"])
        assert repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 0
    finally:
        repository.close()
def test_same_named_nodes_in_different_projects_keep_distinct_identity(tmp_path):
    first = tmp_path / "project-a"
    second = tmp_path / "project-b"
    first.mkdir()
    second.mkdir()
    (first / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")
    (second / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")
    query = make_query(first)
    query["scope"]["directories"] = [str(first.resolve()), str(second.resolve())]
    repository = Repository(tmp_path / "same-name.db", ASSETS)
    try:
        response = execute_query_with_construction(query, repository, ASSETS)
        assert response["termination"] == "satisfied", response
        same_named = [fact for fact in response["results"] if "class Engine" in fact["fields"]["names"]["value"]["text"]]
        assert len(same_named) == 2
        assert len({fact["node"]["source_id"] for fact in same_named}) == 2
        assert len({fact["node"]["subject_id"] for fact in same_named}) == 2
    finally:
        repository.close()
def test_query_splits_out_of_catalog_fields_from_supported_fields(tmp_path):
    project = tmp_path / "mixed-catalog-project"
    project.mkdir()
    (project / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")
    query = make_query(project, ("names", "purpose"))
    repository = Repository(tmp_path / "mixed-catalog.db", ASSETS)
    try:
        response = execute_query_with_construction(query, repository, ASSETS)
        assert response["termination"] == "satisfied", response
        assert any("class Engine" in fact["fields"]["names"]["value"]["text"] for fact in response["results"])
        assert response["out_of_catalog"] == [{
            "fact_type": "F2",
            "fields": ["purpose"],
            "reason": "No fixed first-phase information need covers these fields.",
        }]
        assert response["gaps"] == []
    finally:
        repository.close()
def test_query_projection_preserves_external_reference_and_conflict_evidence(tmp_path):
    from semantic_facts.query_engine import execute_query

    project = tmp_path / "external-conflict-project"
    project.mkdir()
    (project / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")
    query = make_query(project)
    repository = Repository(tmp_path / "external-conflict.db", ASSETS)
    try:
        seeded = execute_query_with_construction(query, repository, ASSETS)
        assert seeded["termination"] == "satisfied"
        stored = repository.read(query)
        fact = stored["facts"][0]
        source = stored["sources"][0]
        subject = fact["node"]
        fact["fields"]["identity"]["value"] = {
            "kind": "reference",
            "ref": {
                "kind": "external",
                "reference_id": "external-rust-crate",
                "label": "unscanned external crate",
                "reason": "outside_authorized_scope",
                "boundary": "Only the explicitly requested project roots were scanned.",
                "observed_in": {
                    "kind": "subject",
                    "source_id": subject["source_id"],
                    "subject_id": subject["subject_id"],
                },
            },
        }
        evidence = fact["fields"]["names"]["basis"]["evidence"][0]
        context = fact["fields"]["names"]["context"]
        stored["conflicts"] = [{
            "conflict_id": "conflict-engine-names",
            "members": [
                {"node": subject, "fact_id": fact["fact_id"], "field": "names", "content_state": source["content_state"]},
                {"node": subject, "fact_id": fact["fact_id"], "field": "identity", "content_state": source["content_state"]},
            ],
            "reason": "fixture conflict used to verify projection preserves conflict evidence",
            "context": context,
            "evidence": [evidence],
        }]
        response = execute_query(query, repository, ASSETS, stored_result=stored)
        assert response["results"][0]["fields"]["identity"]["value"]["ref"]["reason"] == "outside_authorized_scope"
        assert response["conflicts"][0]["conflict_id"] == "conflict-engine-names"
        assert response["conflicts"][0]["evidence"][0]["evidence_id"] == evidence["evidence_id"]
    finally:
        repository.close()
def test_query_handles_multi_parent_cycle_and_external_edges_without_recursive_expansion(tmp_path):
    import copy
    from semantic_facts.repository.contract import ContractCodec
    from semantic_facts.source_scanner import build_fact_batch

    project = tmp_path / "graph-query-project"
    project.mkdir()
    (project / "a.py").write_text("class Alpha:\n    pass\n", encoding="utf-8")
    (project / "b.py").write_text("class Beta:\n    pass\n", encoding="utf-8")
    (project / "c.py").write_text("class Gamma:\n    pass\n", encoding="utf-8")
    codec = ContractCodec(ASSETS)
    batch = build_fact_batch(project, codec)
    by_file = {fact["fields"]["identity"]["value"]["ref"]["node_id"]: fact for fact in batch["facts"]}
    nodes = list(by_file.values())
    root_node, child_node, second_parent = (fact["node"] for fact in nodes[:3])
    template = nodes[0]["fields"]["names"]
    context = copy.deepcopy(template["context"])
    coverage = copy.deepcopy(template["coverage"])
    assertion = copy.deepcopy(template)
    assertion["basis"]["method"] = "test graph edge; not an inferred code fact"
    assertion["basis"]["limitations"] = ["Only validates bounded graph projection"]
    assertion["value"] = {"kind": "text", "text": "fixture graph edge"}
    def edge(edge_id, source, target):
        return {
            "edge_id": edge_id,
            "source": source,
            "target": target,
            "relation": "dependency",
            "assertion": copy.deepcopy(assertion),
        }

    external = {
        "kind": "external",
        "reference_id": "outside-package",
        "label": "package outside authorized scope",
        "reason": "outside_authorized_scope",
        "boundary": "Only the explicitly requested project root is scanned.",
        "observed_in": {
            "kind": "subject",
            "source_id": batch["sources"][0]["source_id"],
            "subject_id": root_node["subject_id"],
        },
    }
    batch["navigation"] = [
        edge("root-to-child", root_node, child_node),
        edge("root-to-parent-b", root_node, second_parent),
        edge("parent-b-to-child", second_parent, child_node),
        edge("child-cycle-to-root", child_node, root_node),
        edge("child-to-external", child_node, external),
    ]
    codec.validate_batch(batch)

    database = tmp_path / "graph-query.db"
    repository = Repository(database, ASSETS)
    try:
        repository.write(batch, "graph-query-seed")
        graph = repository.traverse_navigation(root_node, max_depth=8, max_edges=20)
        assert len(graph["nodes"]) == 3
        assert len(graph["edges"]) == 5
        assert len(graph["terminal_references"]) == 1
        assert graph["truncated"] is False

        response = execute_query_with_construction(make_query(project), repository, ASSETS)
        assert response["termination"] == "satisfied", response
        assert len(response["results"]) == 3
        assert all(set(fact["fields"]) <= {"identity", "names"} for fact in response["results"])
        assert all("outside-package" not in json.dumps(fact) for fact in response["results"])
        assert all("fixture graph edge" not in json.dumps(fact) for fact in response["results"])
    finally:
        repository.close()

def test_query_reports_repository_unavailable_without_fabricating_results(tmp_path):
    project = tmp_path / "unavailable-repository-project"
    project.mkdir()
    (project / "engine.py").write_text("class Engine:\\n    pass\\n", encoding="utf-8")
    repository = Repository(tmp_path / "closed.db", ASSETS)
    repository._ensure_schema()
    before = repository.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    repository.close()

    response = execute_query_with_construction(make_query(project), repository, ASSETS)

    assert response["termination"] == "unavailable"
    assert response["results"] == []
    assert response["gaps"]
    assert all(gap["reason"] == "repository_unavailable" for gap in response["gaps"])
    assert before == 0


def test_query_reports_repository_unavailable_without_falling_back_or_writing(tmp_path):
    project = tmp_path / "repository-unavailable-project"
    project.mkdir()
    (project / "engine.py").write_text("class Engine:\\n    pass\\n", encoding="utf-8")
    database = tmp_path / "repository-unavailable.db"
    repository = Repository(database, ASSETS)
    repository.close()

    try:
        response = execute_query_with_construction(make_query(project), repository, ASSETS)
    except Exception as error:
        raise AssertionError("unavailable repository must return a contract-shaped gap response") from error

    assert response["termination"] == "unavailable"
    assert any(gap["reason"] == "repository_unavailable" for gap in response["gaps"])
    assert response["results"] == []
    assert response["sources"][0]["root"] == str(project.resolve())

    reopened = Repository(database, ASSETS)
    try:
        assert reopened.connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 0
    finally:
        reopened.close()
