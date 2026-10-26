import json
from pathlib import Path

from semantic_facts.info_parser import parse_python_request, parse_rust_request


def request(text, *, tool_id="python.ast-source"):
    return {
        "kind": "parse_request",
        "tool_native_output": {"encoding": "utf-8", "text": text},
        "invocation_profile": {
            "tool_id": tool_id,
            "tool_version": "3.12",
            "command": ["python", "ast", "src/example.py"],
            "environment": {"platform": "linux"},
            "sources": [{
                "source_id": "source-example",
                "root": "example-project",
                "content_state": "sha256:source-state",
                "status": "available",
                "dirty": False,
                "has_untracked": False,
                "excludes": [],
            }],
            "coverage": {
                "domain": "supplied Python source text",
                "checked": ["src/example.py"],
                "excluded": [],
                "completeness": "complete",
                "method": "Python ast.parse",
            },
            "evidence": [],
        },
    }


def test_parser_emits_schema_valid_observations_with_traceable_evidence():
    result = parse_python_request(request(
        "import os\nfrom pathlib import Path\n\nclass Worker:\n    def run(self, value):\n        return value\n"
    ))

    assert result["kind"] == "parse_result"
    assert result["gaps"] == []
    texts = {item["payload"]["text"] for item in result["observations"]}
    assert {"import os", "from pathlib import Path", "class Worker", "function run"} <= texts
    for item in result["observations"]:
        assert item["evidence"][0]["source_id"] == "source-example"
        assert item["evidence"][0]["content_digest"].startswith("sha256:")
        assert ":L" in item["evidence"][0]["locator"]


def test_parser_is_deterministic_for_identical_input():
    value = request("def greet(name):\n    return name\n")
    assert parse_python_request(value) == parse_python_request(value)


def test_parser_returns_explicit_gap_for_syntax_error():
    result = parse_python_request(request("def broken(:\n    pass\n"))

    assert result["observations"] == []
    assert result["gaps"][0]["reason"] == "unparseable"
    assert "syntax error" in result["gaps"][0]["detail"]


def test_parser_returns_explicit_gap_for_unsupported_tool_profile():
    result = parse_python_request(request("not parsed", tool_id="unknown.tool"))

    assert result["observations"] == []
    assert result["gaps"][0]["reason"] == "unsupported_profile"


def test_registry_discovers_builtin_parser_and_reports_unknown_profiles():
    from semantic_facts.info_parser import ParserRegistry

    registry = ParserRegistry()
    assert registry.supported_tools() == ("python.ast-source", "python.compileall", "python.pyproject-toml", "rust.cargo-metadata", "rust.syntax-source")
    unsupported = request("raw output", tool_id="not.registered")
    result = registry.parse(unsupported)
    assert result["gaps"][0]["reason"] == "unsupported_profile"


def test_registry_rejects_duplicate_registration():
    import pytest
    from semantic_facts.info_parser import ParserRegistry

    registry = ParserRegistry()
    with pytest.raises(ValueError, match="already registered"):
        registry.register("python.ast-source", lambda value: value)

def test_rust_parser_emits_struct_trait_function_and_use_observations():
    result = parse_rust_request(request(
        "use std::path::Path;\n\npub struct Config { value: String }\n\npub trait Readable {\n    fn read(&self);\n}\n\nimpl Config {\n    pub fn load() {}\n}\n",
        tool_id="rust.syntax-source",
    ))

    texts = {item["payload"]["text"] for item in result["observations"]}
    assert "struct Config" in texts
    assert "trait Readable" in texts
    assert "fn read" in texts
    assert "fn load" in texts
    assert "use std::path::Path" in texts
    assert all(item["evidence"][0]["locator"].startswith("src/example.py:L") for item in result["observations"])


def test_rust_parser_returns_gap_for_unclosed_delimiter():
    result = parse_rust_request(request("pub struct Config { value: String", tool_id="rust.syntax-source"))
    assert result["observations"] == []
    assert result["gaps"][0]["reason"] == "unparseable"


def test_registry_registers_python_and_rust_parsers():
    from semantic_facts.info_parser import ParserRegistry

    registry = ParserRegistry()
    assert registry.supported_tools() == ("python.ast-source", "python.compileall", "python.pyproject-toml", "rust.cargo-metadata", "rust.syntax-source")
    result = registry.parse(request("pub enum State { Ready, Busy }", tool_id="rust.syntax-source"))
    assert any(item["payload"]["text"] == "enum State" for item in result["observations"])

def test_cargo_metadata_parser_emits_workspace_and_dependency_observations_separately():
    from semantic_facts.info_parser import parse_cargo_metadata_request

    native = {
        "version": 1,
        "workspace_root": "/fixture/workspace",
        "workspace_members": ["path+file:///fixture/workspace/app#app@0.1.0"],
        "packages": [{
            "name": "app",
            "version": "0.1.0",
            "id": "path+file:///fixture/workspace/app#app@0.1.0",
            "manifest_path": "/fixture/workspace/app/Cargo.toml",
            "targets": [{"name": "app", "kind": ["bin"], "crate_types": ["bin"], "src_path": "/fixture/workspace/app/src/main.rs"}],
            "dependencies": [{
                "name": "serde",
                "req": "^1",
                "kind": None,
                "optional": False,
                "uses_default_features": True,
                "features": [],
                "target": None,
                "rename": None,
                "registry": None,
                "path": None,
            }],
        }],
    }
    value = request(json.dumps(native), tool_id="rust.cargo-metadata")
    value["invocation_profile"]["command"] = ["cargo", "metadata", "--no-deps", "--format-version", "1"]
    result = parse_cargo_metadata_request(value)

    assert result["gaps"] == []
    need_ids = {item["information_need_id"] for item in result["observations"]}
    assert "source.f4.kind" in need_ids
    assert "source.f6.kind" in need_ids
    assert any("workspace member" in item["payload"]["text"] for item in result["observations"])
    assert any("dependency" in item["payload"]["text"] for item in result["observations"])
    assert all(item["evidence"][0]["kind"] == "manifest" for item in result["observations"])
    assert all(item["evidence"][0]["content_digest"].startswith("sha256:") for item in result["observations"])


def test_cargo_metadata_parser_returns_gap_for_malformed_or_unsupported_output():
    from semantic_facts.info_parser import parse_cargo_metadata_request

    malformed = parse_cargo_metadata_request(request("{bad json", tool_id="rust.cargo-metadata"))
    assert malformed["observations"] == []
    assert malformed["gaps"][0]["reason"] == "unparseable"

    unsupported = parse_cargo_metadata_request(request('{"version":99,"packages":[]}', tool_id="rust.cargo-metadata"))
    assert unsupported["observations"] == []
    assert unsupported["gaps"][0]["reason"] in {"unparseable", "unsupported_profile"}


def test_compileall_parser_preserves_diagnostic_evidence_without_inferring_semantics():
    from semantic_facts.info_parser import parse_compileall_request

    native = """*** Error compiling '/fixture/project/broken.py'...
  File "/fixture/project/broken.py", line 1
    def broken(:
                 ^
SyntaxError: invalid syntax
"""
    value = request(native, tool_id="python.compileall")
    result = parse_compileall_request(value)

    assert result["gaps"] == []
    assert result["observations"]
    assert any("SyntaxError" in item["payload"]["text"] for item in result["observations"])
    assert all(item["evidence"][0]["kind"] == "observation" for item in result["observations"])
    assert all("no runtime behavior inferred" in item["context"]["language_semantics"][0] for item in result["observations"])

def test_pyproject_toml_parser_emits_manifest_and_script_observations():
    from semantic_facts.info_parser import parse_pyproject_toml_request

    native = """[project]
name = "sample-app"
version = "1.2.3"
dependencies = ["requests>=2"]

[project.scripts]
sample-cli = "sample_app.cli:main"
"""
    value = request(native, tool_id="python.pyproject-toml")
    value["invocation_profile"]["command"] = ["tomllib.loads", "pyproject.toml"]
    result = parse_pyproject_toml_request(value)

    assert result["gaps"] == []
    needs = {item["information_need_id"] for item in result["observations"]}
    assert "source.f3.entries" in needs
    assert "source.f6.kind" in needs
    assert any("sample-cli" in item["payload"]["text"] for item in result["observations"])
    assert any("requests>=2" in item["payload"]["text"] for item in result["observations"])
    assert all(item["evidence"][0]["kind"] == "manifest" for item in result["observations"])
    assert all(item["evidence"][0]["content_digest"].startswith("sha256:") for item in result["observations"])


def test_pyproject_toml_parser_returns_gap_for_malformed_toml():
    from semantic_facts.info_parser import parse_pyproject_toml_request

    result = parse_pyproject_toml_request(request('[project\nname = "broken"', tool_id="python.pyproject-toml"))
    assert result["observations"] == []
    assert result["gaps"][0]["reason"] == "unparseable"
