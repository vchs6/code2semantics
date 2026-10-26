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
