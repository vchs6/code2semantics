"""Host-configured, bounded subprocess adapter for evidence-bound induction providers."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from .induction import validate_induction_result


class ProviderConfigurationError(ValueError):
    """The host's provider allowlist or execution limits are invalid."""


@dataclass(frozen=True)
class ProviderRegistration:
    argv: tuple[str, ...]
    timeout_seconds: float
    max_stdout_bytes: int
    max_stderr_bytes: int


class InductionProviderRegistry:
    """Immutable-in-practice allowlist owned by the host application."""

    def __init__(self, registrations: Mapping[str, Mapping[str, Any]]) -> None:
        parsed: dict[str, ProviderRegistration] = {}
        for provider_id, value in registrations.items():
            argv = value.get("argv")
            timeout = value.get("timeout_seconds")
            max_stdout = value.get("max_stdout_bytes")
            max_stderr = value.get("max_stderr_bytes")
            if (
                not isinstance(provider_id, str) or not provider_id
                or not isinstance(argv, Sequence) or isinstance(argv, (str, bytes))
                or not argv or any(not isinstance(part, str) or not part or "\\0" in part for part in argv)
                or not isinstance(timeout, (int, float)) or timeout <= 0
                or not isinstance(max_stdout, int) or max_stdout <= 0
                or not isinstance(max_stderr, int) or max_stderr <= 0
            ):
                raise ProviderConfigurationError(f"invalid induction provider registration: {provider_id!r}")
            parsed[provider_id] = ProviderRegistration(tuple(argv), float(timeout), max_stdout, max_stderr)
        self._registrations = parsed

    def get(self, provider_id: str) -> ProviderRegistration:
        try:
            return self._registrations[provider_id]
        except KeyError as error:
            raise ProviderConfigurationError(f"induction provider is not registered: {provider_id}") from error


def _empty_failed_result(request: dict[str, Any], asset_root: str | Path | None) -> dict[str, Any]:
    return validate_induction_result(request, None, asset_root)


def invoke_induction_provider(
    provider_id: str,
    request: dict[str, Any],
    registry: InductionProviderRegistry,
    asset_root: str | Path | None = None,
    *,
    cwd: str | Path | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Invoke a fixed host-registered command and validate all returned assertions.

    The provider's output is untrusted. Execution metadata is diagnostic only;
    candidate facts are returned only after the public induction validator
    binds them to this request, its source states, and observed evidence.
    """
    registration = registry.get(provider_id)
    timeout = registration.timeout_seconds if timeout_seconds is None else timeout_seconds
    if timeout <= 0 or timeout > registration.timeout_seconds:
        raise ProviderConfigurationError(
            f"timeout must be in (0, {registration.timeout_seconds}] seconds"
        )
    payload = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    try:
        completed = subprocess.run(
            registration.argv,
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            cwd=str(Path(cwd).resolve()) if cwd is not None else None,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        return {
            "provider_id": provider_id,
            "execution_status": "timeout",
            "detail": f"Induction provider exceeded {timeout} seconds.",
            "induction_result": _empty_failed_result(request, asset_root),
        }
    except subprocess.TimeoutExpired:
        return {
            "provider_id": provider_id,
            "execution_status": "timeout",
            "detail": f"Induction provider exceeded {timeout} seconds.",
            "induction_result": _empty_failed_result(request, asset_root),
        }
    except (OSError, UnicodeError) as error:
        return {
            "provider_id": provider_id,
            "execution_status": "unavailable_tool",
            "detail": f"Induction provider could not execute or decode output: {error}",
            "induction_result": _empty_failed_result(request, asset_root),
        }

    stdout_bytes = completed.stdout.encode("utf-8")
    stderr_bytes = completed.stderr.encode("utf-8")
    if len(stdout_bytes) > registration.max_stdout_bytes or len(stderr_bytes) > registration.max_stderr_bytes:
        return {
            "provider_id": provider_id,
            "execution_status": "output_limit",
            "detail": "Induction provider output exceeded the registered byte limit.",
            "induction_result": _empty_failed_result(request, asset_root),
        }
    if completed.returncode != 0:
        return {
            "provider_id": provider_id,
            "execution_status": "nonzero_exit",
            "detail": f"Induction provider exited with status {completed.returncode}.",
            "induction_result": _empty_failed_result(request, asset_root),
        }
    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return {
            "provider_id": provider_id,
            "execution_status": "malformed_output",
            "detail": f"Induction provider returned invalid JSON at line {error.lineno}.",
            "induction_result": _empty_failed_result(request, asset_root),
        }
    if (
        not isinstance(document, dict)
        or document.get("provider_id") != provider_id
        or document.get("protocol_version") != "1.0.0"
        or not isinstance(document.get("proposed_batch"), dict)
    ):
        return {
            "provider_id": provider_id,
            "execution_status": "provider_identity_mismatch",
            "detail": "Provider response identity, protocol version, or proposed_batch is invalid.",
            "induction_result": _empty_failed_result(request, asset_root),
        }
    try:
        induction_result = validate_induction_result(request, document["proposed_batch"], asset_root)
    except (OSError, ValueError, TypeError, KeyError) as error:
        return {
            "provider_id": provider_id,
            "execution_status": "invalid_proposal",
            "detail": f"Induction proposal failed contract validation: {error}",
            "induction_result": _empty_failed_result(request, asset_root),
        }
    return {
        "provider_id": provider_id,
        "execution_status": "completed",
        "detail": "",
        "induction_result": induction_result,
    }
