import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "skills" / "layered-semantic-facts" / "assets"


def validator() -> Draft202012Validator:
    schema = json.loads((ASSETS / "capability-matrix.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def load_fixture() -> dict:
    return json.loads((ASSETS / "capability-matrix.json").read_text(encoding="utf-8"))


def valid_entry(**overrides: object) -> dict:
    entry = {
        "tool_id": "cargo.metadata",
        "description": "��ȡ Cargo workspace Ԫ����",
        "information_need_ids": ["project.targets"],
        "output_kinds": ["metadata"],
        "languages": ["rust"],
        "platforms": ["linux"],
        "environment": "cargo-1.85",
        "invocation": ["cargo metadata --format-version 1"],
        "combinations": [],
        "limitations": [],
        "enabled": False,
        "research_basis": ["survey-info-acquisition-tools/research/semantic-tooling-survey.md#3"],
    }
    entry.update(overrides)
    return entry


def test_cold_start_empty_matrix_matches_public_schema() -> None:
    document = {"contract_version": "1.0.0", "entries": []}
    validator().validate(document)


def test_current_matrix_separates_accepted_profiles_from_disabled_research_candidates() -> None:
    document = load_fixture()
    validator().validate(document)
    entries = {entry["tool_id"]: entry for entry in document["entries"]}
    assert {"python.ast-source", "rust.syntax-source"} <= set(entries)
    for tool_id in ("python.ast-source", "rust.syntax-source"):
        entry = entries[tool_id]
        assert entry["enabled"] is True
        assert entry["acceptance"]["actor"] == "parser_development"
        assert entry["acceptance"]["evidence"]
        assert set(entry["information_need_ids"]) == {
            "syntax.f2.identity", "syntax.f2.names", "syntax.f2.boundary", "syntax.f2.locators"
        }

    cargo = entries["rust.cargo-metadata"]
    assert cargo["enabled"] is True
    assert cargo["acceptance"]["actor"] == "parser_development"
    assert set(cargo["information_need_ids"]) == {"source.f4.kind", "source.f6.kind"}
    assert any("test_runtime_producer_acceptance.py" in item for item in cargo["acceptance"]["evidence"])
    assert not any("DISABLED" in limit for limit in cargo["limitations"])

    python_manifest = entries["python.pyproject-toml"]
    assert python_manifest["enabled"] is True
    assert python_manifest["acceptance"]["actor"] == "parser_development"
    assert set(python_manifest["information_need_ids"]) == {"source.f3.runtime", "source.f6.kind"}
    assert any("test_runtime_producer_acceptance.py" in item for item in python_manifest["acceptance"]["evidence"])
    assert not any("DISABLED" in limit for limit in python_manifest["limitations"])

    research_candidates = set(entries) - {
        "python.ast-source", "rust.syntax-source", "rust.cargo-metadata", "python.pyproject-toml"
    }
    assert research_candidates == {
        "python.compileall", "rust.cargo-check", "rust.rust-analyzer", "multi.ctags", "multi.ast-grep",
    }
    for tool_id in research_candidates:
        entry = entries[tool_id]
        assert entry["enabled"] is False
        assert "acceptance" not in entry
        assert entry["information_need_ids"]
        assert any("DISABLED" in limit for limit in entry["limitations"])


def test_schema_rejects_invalid_entries() -> None:
    invalid_documents = [
        {"contract_version": "1.0.0", "entries": [{"tool_id": "bad id"}]},
        {"contract_version": "1.0.0", "entries": [valid_entry(tool_id="bad id")]},
        {"contract_version": "1.0.0", "entries": [valid_entry(information_need_ids=["a", "a"]) ]},
        {"contract_version": "1.0.0", "entries": [valid_entry(enabled=True)]},
        {
            "contract_version": "1.0.0",
            "entries": [valid_entry(acceptance={"actor": "parser_development", "evidence": ["ok"]})],
        },
        {"contract_version": "1.0.0", "entries": [valid_entry(extra="forbidden")]},
    ]
    for document in invalid_documents:
        errors = list(validator().iter_errors(document))
        assert errors, document


def test_fixture_can_represent_multiple_needs_and_candidates() -> None:
    first = valid_entry(tool_id="tool.a", information_need_ids=["need.a", "need.b"])
    second = valid_entry(tool_id="tool.b", information_need_ids=["need.b"])
    document = {"contract_version": "1.0.0", "entries": [first, second]}
    validator().validate(document)
    assert {entry["tool_id"] for entry in document["entries"]} == {"tool.a", "tool.b"}

