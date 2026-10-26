# Runtime acceptance results

Date: 2026-10-26

## Verified path

The following bounded path is covered by `tests/test_acceptance.py` and CI run https://github.com/vchs6/code2semantics/actions/runs/40257745511:

- Real Python source fixture under `tests/fixtures/scenarios/python_project/`
- Python AST syntax inventory through the registered `ParserRegistry`
- Deterministic constructor maps parser observations to a Schema-validated F2 FactBatch with source evidence and content digests
- SQLite write, close/reopen, and query
- Repeating an identical scan preserves the number of stored fact rows

Observed CI results: repository 35 passed; capability matrix 14 passed; parser registry 6 passed; source scanner 4 passed; real-source acceptance 1 passed; strict OpenSpec passed. The product delivery gate intentionally remains blocked because the full end-to-end pipeline (tool selection/execution, induction, multi-layer construction, source-change invalidation, and full query response) is not yet implemented and verified.

## Scope limitation

This is a partial runtime integration check, not full system acceptance. It does not yet verify tool capability selection, external tool execution, registered parser dispatch from native tool output, induction batching, multi-layer construction, source-change invalidation, the complete public query response, or the required cross-component scenarios S1–S12.

FULL_END_TO_END_ACCEPTANCE: NOT_YET_PASSED
