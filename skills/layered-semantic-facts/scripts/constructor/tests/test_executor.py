"""执行器测试（任务 3.1/3.2，spec「执行器调度与异常报告」）。"""
from constructor.executor import execute, merge_exception_into_gaps  # noqa: E402


def test_正常退出产生输出():
    result = execute({"command": "echo hello", "timeout_seconds": 10})
    assert result.exception is None
    assert result.output.strip() == "hello"


def test_超时转结构化异常():
    result = execute({"command": "sleep 5", "timeout_seconds": 1})
    assert result.output is None
    assert result.exception["kind"] == "timeout"


def test_空输出判异常():
    result = execute({"command": "true", "timeout_seconds": 10})
    assert result.output is None
    assert result.exception["kind"] == "empty_output"


def test_非零退出转结构化异常():
    result = execute({"command": "false", "timeout_seconds": 10})
    assert result.output is None
    assert result.exception["kind"] == "nonzero_exit"


def test_工具失败不中断_归并gaps标注原因():
    exception = {"tool_id": "X-cargo_metadata", "kind": "timeout", "reason": "超时"}
    gaps = []
    merge_exception_into_gaps(exception, ["入口"], gaps)
    assert any(g["type"] == "入口" and "超时" in g["reason"] for g in gaps)
