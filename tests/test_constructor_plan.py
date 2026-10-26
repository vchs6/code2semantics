from pathlib import Path

from semantic_facts.constructor_plan import plan_constructor_request
from test_information_needs import ASSETS, request


def test_partially_satisfied_request_only_plans_missing_fields(tmp_path):
    from semantic_facts.repository.contract import ContractCodec
    from semantic_facts.source_scanner import build_fact_batch

    project = tmp_path / "project"
    project.mkdir()
    (project / "service.py").write_text("class Example:\n    pass\n", encoding="utf-8")
    batch = build_fact_batch(project, ContractCodec(ASSETS))
    source = batch["sources"][0]
    fact = dict(batch["facts"][0])
    fact["fields"] = {"identity": fact["fields"]["identity"]}

    value = request(("identity", "names"))
    value["query"]["scope"]["directories"] = [str(project.resolve())]
    value["existing_valid_facts"]["sources"] = [source]
    value["existing_valid_facts"]["facts"] = [fact]
    value["current_source_context"]["sources"] = [source]

    result = plan_constructor_request(value, ASSETS)
    assert [item["need_id"] for item in result["plan"]] == ["syntax.f2.names"]


def test_multiple_fields_are_grouped_by_need_and_sorted():
    result = plan_constructor_request(request(("locators", "names", "identity")), ASSETS)
    assert [item["need_id"] for item in result["plan"]] == [
        "syntax.f2.identity", "syntax.f2.locators", "syntax.f2.names"
    ]
    assert all(item["fields"] == sorted(item["fields"]) for item in result["plan"])


def test_producer_selection_filters_disabled_and_combines_partial_coverage(tmp_path):
    from semantic_facts.capability_matrix import CapabilityMatrix
    from semantic_facts.constructor_plan import select_enabled_producers

    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    base = {
        "description": "accepted source parser",
        "output_kinds": ["source-observation"],
        "languages": ["python"],
        "platforms": ["linux"],
        "environment": "python-3.12",
        "invocation": ["in-process-parser"],
        "combinations": [],
        "limitations": ["syntax inventory only"],
        "enabled": True,
        "acceptance": {"actor": "parser_development", "evidence": ["tests/test_info_parser.py::test_registry_discovers_builtin_parser_and_reports_unknown_profiles"]},
        "research_basis": ["built-in Python AST parser and first-phase acceptance fixture"],
    }
    disabled = dict(base, tool_id="tool.disabled", information_need_ids=["syntax.f2.boundary"], enabled=False)
    disabled.pop("acceptance")
    matrix.replace([
        dict(base, tool_id="tool.identity", information_need_ids=["syntax.f2.identity"]),
        dict(base, tool_id="tool.names", information_need_ids=["syntax.f2.names"]),
        disabled,
    ])
    selected = select_enabled_producers(
        matrix,
        ["syntax.f2.identity", "syntax.f2.names", "syntax.f2.boundary"],
        "Python",
        "Linux",
        "python-3.12",
    )
    assert [item["tool_id"] for item in selected["syntax.f2.identity"]] == ["tool.identity"]
    assert [item["tool_id"] for item in selected["syntax.f2.names"]] == ["tool.names"]
    assert selected["syntax.f2.boundary"] == []


def test_producer_selection_rejects_environment_mismatch(tmp_path):
    from semantic_facts.capability_matrix import CapabilityMatrix
    from semantic_facts.constructor_plan import select_enabled_producers

    matrix = CapabilityMatrix(tmp_path / "matrix.json")
    matrix.replace([{
        "tool_id": "tool.rust",
        "description": "Rust source producer",
        "information_need_ids": ["syntax.f2.names"],
        "output_kinds": ["source-observation"],
        "languages": ["rust"],
        "platforms": ["linux"],
        "environment": "rust-toolchain-stable",
        "invocation": ["in-process-parser"],
        "combinations": [],
        "limitations": ["syntax inventory only"],
        "enabled": True,
        "acceptance": {"actor": "parser_development", "evidence": ["tests/test_info_parser.py::test_registry_registers_python_and_rust_parsers"]},
        "research_basis": ["Rust declaration parser fixture"],
    }])
    selected = select_enabled_producers(matrix, ["syntax.f2.names"], "Rust", "Linux", "missing-rust-toolchain")
    assert selected["syntax.f2.names"] == []

def test_checked_in_matrix_exposes_only_accepted_first_phase_profiles():
    from semantic_facts.capability_matrix import CapabilityMatrix
    from semantic_facts.constructor_plan import select_enabled_producers

    matrix = CapabilityMatrix(ASSETS / "capability-matrix.json")
    for language, expected_tool in [
        ("Python", "python.ast-source"),
        ("Rust", "rust.syntax-source"),
    ]:
        selected = select_enabled_producers(
            matrix,
            ["syntax.f2.identity", "syntax.f2.names", "syntax.f2.boundary", "syntax.f2.locators"],
            language,
            "linux",
            "in-process",
        )
        for need_id, entries in selected.items():
            assert [entry["tool_id"] for entry in entries] == [expected_tool], need_id

def test_unknown_need_returns_explicit_uncovered_gap():
    result = plan_constructor_request(request(("purpose",)), ASSETS)
    assert result["plan"] == []
    assert result["gaps"][0]["reason"] == "uncovered_need"
    assert result["gaps"][0]["fields"] == ["purpose"]


def test_stale_existing_assertion_does_not_satisfy_current_request(tmp_path):
    from semantic_facts.repository.contract import ContractCodec
    from semantic_facts.source_scanner import build_fact_batch

    project = tmp_path / "stale-project"
    project.mkdir()
    (project / "service.py").write_text("class Example:\n    pass\n", encoding="utf-8")
    batch = build_fact_batch(project, ContractCodec(ASSETS))
    source = batch["sources"][0]
    stale_fact = dict(batch["facts"][0])
    stale_identity = dict(stale_fact["fields"]["identity"])
    stale_identity["validity"] = {"state": "modified", "sources": [{"source_id": source["source_id"], "content_state": source["content_state"]}], "reason": "stale"}
    stale_fact["fields"] = {"identity": stale_identity}

    value = request(("identity",))
    value["query"]["scope"]["directories"] = [str(project.resolve())]
    value["existing_valid_facts"]["sources"] = [source]
    value["existing_valid_facts"]["facts"] = [stale_fact]
    value["current_source_context"]["sources"] = [source]

    result = plan_constructor_request(value, ASSETS)
    assert [item["need_id"] for item in result["plan"]] == ["syntax.f2.identity"]


def test_empty_query_scope_is_rejected():
    value = request(("identity",))
    value["query"]["scope"]["directories"] = []
    try:
        plan_constructor_request(value, ASSETS)
    except ValueError as error:
        assert "invalid ConstructRequest" in str(error)
    else:
        raise AssertionError("empty source scope must be rejected")


def test_constructor_plan_is_deterministic_for_identical_requests():
    value = request(("locators", "names", "identity"))
    assert plan_constructor_request(value, ASSETS) == plan_constructor_request(value, ASSETS)

def test_constructor_plan_selects_accepted_subprocess_producer_for_manifest_need(tmp_path):
    import json
    import shutil

    for source in ASSETS.iterdir():
        if source.is_file():
            shutil.copy(source, tmp_path / source.name)
    matrix_path = tmp_path / "capability-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    entry = next(item for item in matrix["entries"] if item["tool_id"] == "rust.cargo-metadata")
    entry["enabled"] = True
    entry["acceptance"] = {
        "actor": "parser_development",
        "evidence": ["tests/test_info_parser.py::test_cargo_metadata_parser_emits_workspace_and_dependency_observations_separately"],
    }
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    value = request()
    value["query"]["selections"] = [{"fact_type": "F4", "fields": ["kind"]}]
    value["query"]["granularity"] = "L2"
    result = plan_constructor_request(value, tmp_path)

    assert result["gaps"] == []
    assert len(result["plan"]) == 1
    assert result["plan"][0]["need_id"] == "source.f4.kind"
    assert result["plan"][0]["producer_ids"] == ["rust.cargo-metadata"]
    assert result["plan"][0]["producer_profiles"][0]["environment"] == "subprocess"
