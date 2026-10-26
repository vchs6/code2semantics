"""Registry-driven producer dispatch for accepted parser profiles.

In-process profiles invoke ParserRegistry directly. Subprocess profiles require an
explicitly configured argv-only executor; tool output is always passed back through
the registered parser and validated before construction.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Sequence

from .info_parser import ParserRegistry
from .tool_executor import SubprocessToolExecutor


def _gap(request: dict[str, Any], reason: str, detail: str, registry: ParserRegistry) -> dict[str, Any]:
    profile = request["invocation_profile"]
    result = {
        "kind": "parse_result",
        "observations": [],
        "gaps": [{
            "fact_type": "F2",
            "fields": ["syntax_inventory"],
            "target": {"kind": "scope"},
            "reason": reason,
            "detail": detail,
            "context": {
                "source_ids": [source["source_id"] for source in profile["sources"]],
                "conditions": [],
                "environment": profile["environment"],
                "language_semantics": ["Producer failure; no facts inferred from missing output"],
            },
            "coverage": profile["coverage"],
        }],
    }
    return registry.validate_result(result)


def dispatch_registered_producer(
    entry: dict[str, Any],
    request: dict[str, Any],
    parser_registry: ParserRegistry,
    *,
    external_executor: SubprocessToolExecutor | None = None,
    cwd: str | Path | None = None,
    args: Sequence[str] = (),
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """Invoke only an accepted enabled matrix entry, then validate its ParseResult."""
    tool_id = entry.get("tool_id")
    profile = request.get("invocation_profile", {})
    if not entry.get("enabled") or not entry.get("acceptance"):
        return _gap(request, "unavailable_tool", f"Producer is not enabled and accepted: {tool_id}", parser_registry)
    if tool_id != profile.get("tool_id"):
        return _gap(request, "unsupported_profile", "Selected producer and ParseRequest profile do not match.", parser_registry)

    environment = entry.get("environment")
    if environment == "in-process":
        try:
            return parser_registry.parse(request)
        except (ValueError, TypeError, KeyError) as error:
            return _gap(request, "unparseable", f"Registered in-process producer failed: {error}", parser_registry)

    if environment != "subprocess":
        return _gap(request, "unavailable_tool", f"Unsupported producer environment: {environment}", parser_registry)
    if external_executor is None or cwd is None:
        return _gap(request, "unavailable_tool", f"No bounded executor configured for subprocess producer {tool_id}", parser_registry)

    try:
        execution = external_executor.execute(
            tool_id,
            args,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
        )
    except (OSError, ValueError) as error:
        return _gap(request, "unavailable_tool", f"Producer execution rejected: {error}", parser_registry)
    if execution.timed_out:
        return _gap(request, "unavailable_tool", f"Producer timed out after {timeout_seconds} seconds: {tool_id}", parser_registry)
    if execution.returncode != 0:
        detail = execution.stderr.strip() or f"exit code {execution.returncode}"
        return _gap(request, "unavailable_tool", f"Producer failed ({tool_id}): {detail}", parser_registry)

    parsed_request = deepcopy(request)
    parsed_request["tool_native_output"] = {"encoding": "utf-8", "text": execution.stdout}
    parsed_request["invocation_profile"]["command"] = list(execution.argv)
    try:
        return parser_registry.parse(parsed_request)
    except (ValueError, TypeError, KeyError) as error:
        return _gap(request, "unparseable", f"Producer output could not be parsed: {error}", parser_registry)
