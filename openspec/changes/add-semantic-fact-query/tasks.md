# Tasks

TDD rule: each behavior task starts with a failing test, then the smallest implementation, then focused and regression runs. Product completion requires runtime evidence, not just passing repository tests.

## 1. Query validation and current-source handling

- [x] 1.1 Validate Query and response against the main public schemas; reject malformed query before repository writes.
- [x] 1.2 Inspect explicitly requested Python/Rust source roots and bind the current content snapshot, including dirty/untracked state.
- [x] 1.3 Read only current source-head facts and filter assertions whose validity/evidence state is stale; retain historical fact rows.
- [ ] 1.4 Add tests for multiple roots, nested/overlapping roots, unavailable repository, and out-of-scope references without expanding read authorization.

## 2. Bounded construction loop

- [x] 2.1 Add tests for missing fields causing construction, write followed by re-read, unknown needs returning gaps, no progress stopping, and source changes appending new fact versions.
- [x] 2.2 Implement deterministic read → coverage → ConstructRequest → append write → re-read loop with bounded rounds.
- [x] 2.3 Stop when satisfied, no coverage progress, source unavailable, or budget exhausted; preserve explicit gaps and never infer facts.
- [ ] 2.4 Count necessary ancestor-path and direct-node-completeness obligations as bounded progress; unrelated facts must not extend the loop.

## 3. Public response projection

- [x] 3.1 Validate the final response against output-schema and include requested fields, evidence, context, coverage, gaps and termination.
- [x] 3.2 Ensure constructor plans and raw repository envelopes are not returned as final responses.
- [ ] 3.3 Project only the requested target and required direct nodes; verify completeness before treating a partial direct-node result as sufficient.
- [ ] 3.4 Add tests for multiple projects, same-name subjects, multi-parent relations, dependency cycles, external references, conflicts and out-of-catalog items.

## 4. CLI and integration

- [x] 4.1 Provide the query CLI using the public Query JSON and schema-validated response.
- [x] 4.2 Exercise Python and Rust source → FactBatch → SQLite → close/reopen → query in real-source tests.
- [ ] 4.3 Run all query tests and strict OpenSpec validation after each implementation change; record actual output in acceptance-results.md.
- [ ] 4.4 Complete full S1–S12 integration acceptance before declaring this component fully complete.

## Evidence (2026-10-26)

- Implementation: semantic_facts/query_engine.py, semantic_facts/cli.py, semantic_facts/repository/store.py.
- Tests: tests/test_query_orchestration.py, tests/test_acceptance.py, repository tests.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40268078346 — query/constructor/induction suite and strict OpenSpec passed; product delivery gate intentionally blocks full-system completion.
- Full dependency-aware invalidation, direct-node completeness, multi-project/cycle acceptance and S1–S12 remain pending.
