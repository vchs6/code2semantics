import sys
from pathlib import Path

from semantic_facts.info_parser import ParserRegistry
from semantic_facts.producer_dispatch import dispatch_registered_producer
from semantic_facts.tool_executor import SubprocessToolExecutor

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "skills" / "layered-semantic-facts" / "assets"


def request():
    return {
        "kind": "parse_request",
        "tool_native_output": {"encoding": "utf-8", "text": "class Original: pass"},
        "invocation_profile": {
            "tool_id": "python.ast-source",
            "tool_version": "3.12",
            "command": ["source-parser", "src/example.py"],
            "environment": {"language": "Python"},
            "sources": [{
                "source_id": "src-test",
                "root": "/project",
                "content_state": "sha256:" + "a" * 64,
                "status": "available",
                "dirty": False,
                "has_untracked": False,
                "excludes": [],
            }],
            "coverage": {
                "domain": "Python syntax",
                "checked": ["src/example.py"],
                "excluded": [],
                "completeness": "complete",
                "method": "test",
            },
            "evidence": [],
        },
    }


def entry(environment="subprocess", enabled=True):
    value = {
        "tool_id": "python.ast-source",
        "environment": environment,
        "enabled": enabled,
        "invocation": [environment],
    }
    if enabled:
        value["acceptance"] = {"actor": "parser_development", "evidence": ["tests/test_producer_dispatch.py"]}
    return value


def test_dispatch_invokes_registered_subprocess_then_parser(tmp_path):
    executor = SubprocessToolExecutor({
        "python.ast-source": [sys.executable, "-c", "print('class FromProducer:')"],
    })
    result = dispatch_registered_producer(
        entry(), request(), ParserRegistry(ASSETS),
        external_executor=executor, cwd=tmp_path, timeout_seconds=2,
    )
    assert result["gaps"] == []
    assert any(item["payload"]["text"] == "class FromProducer" for item in result["observations"])


def test_dispatch_returns_explicit_gap_when_subprocess_producer_fails(tmp_path):
    executor = SubprocessToolExecutor({
        "python.ast-source": [sys.executable, "-c", "import sys; print('failed', file=sys.stderr); sys.exit(3)"],
    })
    result = dispatch_registered_producer(
        entry(), request(), ParserRegistry(ASSETS),
        external_executor=executor, cwd=tmp_path, timeout_seconds=2,
    )
    assert result["observations"] == []
    assert result["gaps"][0]["reason"] == "unavailable_tool"
    assert "failed" in result["gaps"][0]["detail"]


def test_dispatch_does_not_run_disabled_or_unaccepted_producer(tmp_path):
    executor = SubprocessToolExecutor({"python.ast-source": [sys.executable, "-c", "raise SystemExit(99)"]})
    result = dispatch_registered_producer(
        entry(enabled=False), request(), ParserRegistry(ASSETS),
        external_executor=executor, cwd=tmp_path, timeout_seconds=2,
    )
    assert result["gaps"][0]["reason"] == "unavailable_tool"
    assert "not enabled and accepted" in result["gaps"][0]["detail"]