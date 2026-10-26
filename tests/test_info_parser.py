from pathlib import Path

from semantic_facts.info_parser import parse_python_request


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
    assert registry.supported_tools() == ("python.ast-source",)
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
        "use std::path::Path;\n\npub struct Config { value: String }\n\npub trait Readable { fn read(&self); }\n\nimpl Config {\n    pub fn load() {}\n}\n",
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
    assert registry.supported_tools() == ("python.ast-source", "rust.syntax-source")
    result = registry.parse(request("pub enum State { Ready, Busy }", tool_id="rust.syntax-source"))
    assert any(item["payload"]["text"] == "enum State" for item in result["observations"])