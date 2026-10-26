from __future__ import annotations

import json
import sys

import pytest

from semantic_facts.induction_provider import (
    InductionProviderRegistry,
    ProviderConfigurationError,
    invoke_induction_provider,
)


def _request():
    return {
        "kind": "induction_request",
        "request_id": "induction-fixture",
        "group": {
            "fact_type": "F16",
            "subject": {
                "source_id": "src-fixture",
                "subject_id": "subject-fixture",
                "node_id": "node-fixture",
            },
            "content_states": [{"source_id": "src-fixture", "content_state": "sha256:" + "a" * 64}],
            "context": {
                "source_ids": ["src-fixture"],
                "conditions": [],
                "environment": {},
                "language_semantics": ["fixture"],
            },
            "fields": ["strategy"],
        },
        "observations": [],
        "existing_valid_facts": {
            "contract_version": "1.0.0",
            "catalog_id": "semantic-facts-20261025",
            "sources": [{
                "source_id": "src-fixture",
                "root": "/fixture",
                "content_state": "sha256:" + "a" * 64,
                "status": "available",
                "dirty": False,
                "has_untracked": False,
                "excludes": [],
            }],
            "facts": [],
            "navigation": [],
            "direct_nodes": [],
            "conflicts": [],
        },
        "unmet": [{
            "fact_type": "F16",
            "fields": ["strategy"],
            "target": {"kind": "node", "node": {
                "source_id": "src-fixture",
                "subject_id": "subject-fixture",
                "node_id": "node-fixture",
            }},
            "reason": "unknown",
            "detail": "fixture need is not yet satisfied",
            "context": {
                "source_ids": ["src-fixture"],
                "conditions": [],
                "environment": {},
                "language_semantics": ["fixture"],
            },
            "coverage": {
                "domain": "fixture",
                "checked": ["fixture"],
                "excluded": [],
                "completeness": "partial",
                "method": "fixture",
            },
        }],
    }


def test_provider_requires_host_registered_fixed_command():
    registry = InductionProviderRegistry({})
    with pytest.raises(ProviderConfigurationError, match="not registered"):
        invoke_induction_provider("unregistered", _request(), registry)


def test_provider_validates_registration_limits():
    with pytest.raises(ProviderConfigurationError):
        InductionProviderRegistry({
            "provider": {"argv": [], "timeout_seconds": 1, "max_stdout_bytes": 100, "max_stderr_bytes": 100}
        })
    with pytest.raises(ProviderConfigurationError):
        InductionProviderRegistry({
            "provider": {"argv": [sys.executable, "-c", "pass"], "timeout_seconds": 0, "max_stdout_bytes": 100, "max_stderr_bytes": 100}
        })


def test_provider_accepts_versioned_json_protocol_and_routes_result_through_induction_validator(tmp_path):
    script = tmp_path / "provider.py"
    script.write_text(
        "import json,sys\n"
        "request=json.load(sys.stdin)\n"
        "json.dump({'provider_id':'fixture-provider','protocol_version':'1.0.0','proposed_batch':"
        "{'contract_version':'1.0.0','catalog_id':'semantic-facts-20261025','sources':[],"
        "'facts':[],'navigation':[],'direct_nodes':[],'conflicts':[]}},sys.stdout)\n",
        encoding="utf-8",
    )
    registry = InductionProviderRegistry({
        "fixture-provider": {
            "argv": [sys.executable, str(script)],
            "timeout_seconds": 2,
            "max_stdout_bytes": 8192,
            "max_stderr_bytes": 1024,
        }
    })

    result = invoke_induction_provider("fixture-provider", _request(), registry)

    assert result["execution_status"] == "completed"
    assert result["provider_id"] == "fixture-provider"
    assert result["induction_result"]["batch"]["facts"] == []
    assert result["induction_result"]["gaps"][0]["reason"] == "unknown"


@pytest.mark.parametrize(
    ("program", "timeout", "stdout_limit", "expected_status"),
    [
        ("import time; time.sleep(2)", 0.05, 1024, "timeout"),
        ("import sys; sys.exit(7)", 1, 1024, "nonzero_exit"),
        ("print('{ malformed')", 1, 1024, "malformed_output"),
        ("print('x' * 4096)", 1, 128, "output_limit"),
        ("print('{}')", 1, 1024, "provider_identity_mismatch"),
    ],
)
def test_provider_failure_modes_fail_closed(tmp_path, program, timeout, stdout_limit, expected_status):
    registry = InductionProviderRegistry({
        "fixture-provider": {
            "argv": [sys.executable, "-c", program],
            "timeout_seconds": max(timeout, 0.1),
            "max_stdout_bytes": stdout_limit,
            "max_stderr_bytes": 1024,
        }
    })

    result = invoke_induction_provider(
        "fixture-provider", _request(), registry, timeout_seconds=timeout
    )

    assert result["execution_status"] == expected_status
    assert result["induction_result"]["batch"]["facts"] == []
    assert result["induction_result"]["gaps"]


def test_provider_rejects_untrusted_commands_from_request_payload():
    request = _request()
    request["provider_command"] = [sys.executable, "-c", "print('injected')"]
    registry = InductionProviderRegistry({
        "fixture-provider": {
            "argv": [sys.executable, "-c", "import json,sys; json.load(sys.stdin); print('{}')"],
            "timeout_seconds": 1,
            "max_stdout_bytes": 1024,
            "max_stderr_bytes": 1024,
        }
    })

    result = invoke_induction_provider("fixture-provider", request, registry)

    assert result["execution_status"] == "provider_identity_mismatch"
    assert result["induction_result"]["batch"]["facts"] == []
