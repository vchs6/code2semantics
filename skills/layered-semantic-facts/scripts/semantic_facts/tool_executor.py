"""Allowlisted, bounded subprocess execution boundary for future external producers.

Current first-phase Python/Rust profiles are in-process ParserRegistry handlers.
This executor is intentionally opt-in: callers must register a fixed argv prefix
for a tool ID; user input is appended as individual argv elements and never
interpreted by a shell.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from typing import Mapping, Protocol, Sequence


@dataclass(frozen=True)
class ExecutionResult:
    tool_id: str
    argv: tuple[str, ...]
    cwd: str
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool


class ToolExecutionError(ValueError):
    """A requested tool profile or execution parameter is not permitted."""


class ToolExecutor(Protocol):
    def execute(
        self,
        tool_id: str,
        args: Sequence[str],
        *,
        cwd: str | Path,
        timeout_seconds: float,
    ) -> ExecutionResult: ...


class SubprocessToolExecutor:
    """Execute only explicitly registered argv prefixes with bounded timeouts."""

    def __init__(
        self,
        registered_commands: Mapping[str, Sequence[str]],
        *,
        max_timeout_seconds: float = 30.0,
    ) -> None:
        if max_timeout_seconds <= 0:
            raise ValueError("max_timeout_seconds must be positive")
        self._commands = {
            tool_id: tuple(prefix)
            for tool_id, prefix in registered_commands.items()
        }
        for tool_id, prefix in self._commands.items():
            if not tool_id or not prefix or any(not part or "\\0" in part for part in prefix):
                raise ValueError(f"invalid registered command for {tool_id!r}")
        self.max_timeout_seconds = max_timeout_seconds

    def execute(
        self,
        tool_id: str,
        args: Sequence[str],
        *,
        cwd: str | Path,
        timeout_seconds: float,
    ) -> ExecutionResult:
        if tool_id not in self._commands:
            raise ToolExecutionError(f"tool is not registered: {tool_id}")
        if timeout_seconds <= 0 or timeout_seconds > self.max_timeout_seconds:
            raise ToolExecutionError(
                f"timeout must be in (0, {self.max_timeout_seconds}] seconds"
            )
        if any(not isinstance(arg, str) or "\\0" in arg for arg in args):
            raise ToolExecutionError("argv arguments must be strings without NUL bytes")
        working_directory = Path(cwd).resolve()
        if not working_directory.is_dir():
            raise ToolExecutionError(f"working directory is not accessible: {working_directory}")

        argv = self._commands[tool_id] + tuple(args)
        try:
            completed = subprocess.run(
                argv,
                cwd=str(working_directory),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
                shell=False,
                env=os.environ.copy(),
            )
            return ExecutionResult(
                tool_id=tool_id,
                argv=argv,
                cwd=str(working_directory),
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout.decode("utf-8", "replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
            stderr = error.stderr.decode("utf-8", "replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
            return ExecutionResult(
                tool_id=tool_id,
                argv=argv,
                cwd=str(working_directory),
                returncode=None,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
            )
