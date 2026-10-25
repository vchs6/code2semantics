"""执行器（任务 3.1/3.2）：按矩阵调用剖面调度工具，管理进程生命周期与输出捕获。

- 正常退出且输出非空 → ExecResult(output=...)
- 超时 / 非零退出 / 空输出 → ExecResult(exception=结构化异常记录)
- 工具失败不中断构造流程：结构化异常经 merge_exception_into_gaps 归并进 gaps
  （spec「执行器调度与异常报告」：工具失败转为缺口而非中断）。
"""
import subprocess
from dataclasses import dataclass


@dataclass
class ExecResult:
    output: str = None
    exception: dict = None  # {tool_id, kind, reason, unparsed?}


def execute(profile, tool_id="unknown-tool", cwd=None):
    """按调用剖面执行工具命令。profile: {command, timeout_seconds, retries, output_type}。"""
    command = (profile or {}).get("command")
    timeout = (profile or {}).get("timeout_seconds") or 60
    if not command:
        return ExecResult(exception={
            "tool_id": tool_id, "kind": "no_command", "reason": "调用剖面缺少 command"})

    try:
        proc = subprocess.run(
            command, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ExecResult(exception={
            "tool_id": tool_id, "kind": "timeout", "reason": f"工具超时（>{timeout}s）：{command}"})
    except OSError as exc:
        return ExecResult(exception={
            "tool_id": tool_id, "kind": "spawn_error", "reason": f"工具无法启动：{exc}"})

    if proc.returncode != 0:
        return ExecResult(exception={
            "tool_id": tool_id, "kind": "nonzero_exit",
            "reason": f"工具非零退出（{proc.returncode}）：{proc.stderr.strip()[:200]}"})
    if not (proc.stdout or "").strip():
        return ExecResult(exception={
            "tool_id": tool_id, "kind": "empty_output", "reason": "工具正常退出但输出为空"})
    return ExecResult(output=proc.stdout)


def merge_exception_into_gaps(exception, fact_types, gaps):
    """结构化异常归并进 gaps：对应信息需求进 gaps 并标注失败原因，不中断。"""
    reason = f"工具失败（{exception['kind']}）：{exception['reason']}"
    for fact_type in fact_types:
        gaps.append({"type": fact_type, "reason": reason})
