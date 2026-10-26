import sys
from pathlib import Path

import pytest

from semantic_facts.tool_executor import SubprocessToolExecutor, ToolExecutionError


def test_executor_uses_registered_argv_and_captures_output(tmp_path):
    executor = SubprocessToolExecutor({"python-test": [sys.executable]}, max_timeout_seconds=3)
    result = executor.execute(
        "python-test",
        ["-c", "import sys; print('ok'); print('warning', file=sys.stderr)"],
        cwd=tmp_path,
        timeout_seconds=1,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "ok"
    assert result.stderr.strip() == "warning"
    assert result.timed_out is False
    assert result.argv[0] == sys.executable


def test_executor_rejects_unregistered_tool_and_excessive_timeout(tmp_path):
    executor = SubprocessToolExecutor({"python-test": [sys.executable]}, max_timeout_seconds=1)

    with pytest.raises(ToolExecutionError, match="not registered"):
        executor.execute("unknown", [], cwd=tmp_path, timeout_seconds=0.1)
    with pytest.raises(ToolExecutionError, match="timeout"):
        executor.execute("python-test", ["-c", "pass"], cwd=tmp_path, timeout_seconds=2)


def test_executor_times_out_without_shell_execution(tmp_path):
    executor = SubprocessToolExecutor({"python-test": [sys.executable]}, max_timeout_seconds=2)
    result = executor.execute(
        "python-test",
        ["-c", "import time; print('started', flush=True); time.sleep(2)"],
        cwd=tmp_path,
        timeout_seconds=0.1,
    )
    assert result.timed_out is True
    assert result.returncode is None
    assert "started" in result.stdout
