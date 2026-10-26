# Runtime acceptance results

Date: 2026-10-26

## Verified path

The following bounded path is covered by `tests/test_acceptance.py`:

- Real Python source fixture under `tests/fixtures/scenarios/python_project/`
- Python AST syntax inventory
- Schema-validated F2 FactBatch with source evidence and content digests
- SQLite write, close/reopen, and query
- Repeating an identical scan preserves the number of stored fact rows

The dedicated CI run is the source of truth for the pass/fail result.

## Scope limitation

This is a partial runtime integration check, not full system acceptance. It does not yet verify tool capability selection, external tool execution, registered parser dispatch from native tool output, induction batching, multi-layer construction, source-change invalidation, the complete public query response, or the required cross-component scenarios S1–S12.

FULL_END_TO_END_ACCEPTANCE: NOT_YET_PASSED
