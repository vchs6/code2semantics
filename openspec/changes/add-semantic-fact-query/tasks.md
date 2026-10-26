# Tasks

TDD rule: each behavior task starts with a failing test, then the smallest implementation, then focused and regression runs. Product completion requires runtime evidence, not just passing repository tests.

## 1. Query validation and current-source handling

- [x] 1.1 Validate Query and response against the main public schemas; reject malformed query before repository writes.
- [x] 1.2 Inspect explicitly requested Python/Rust source roots and bind the current content snapshot, including dirty/untracked state.
- [x] 1.3 Read only current source-head facts and filter assertions whose validity/evidence state is stale; retain historical fact rows.
- [x] 1.4 Add tests for multiple roots, nested/overlapping roots, unavailable source roots, and out-of-scope references without expanding read authorization.

## 2. Bounded construction loop

- [x] 2.1 Add tests for missing fields causing construction, write followed by re-read, unknown needs returning gaps, no progress stopping, and source changes appending new fact versions.
- [x] 2.2 Implement deterministic read → coverage → ConstructRequest → append write → re-read loop with bounded rounds.
- [x] 2.3 Stop when satisfied, no coverage progress, source unavailable, or budget exhausted; preserve explicit gaps and never infer facts.
- [x] 2.4 Count necessary ancestor-path and direct-node-completeness obligations as bounded progress; unrelated facts must not extend the loop.

## 3. Public response projection

- [x] 3.1 Validate the final response against output-schema and include requested fields, evidence, context, coverage, gaps and termination.
- [x] 3.2 Ensure constructor plans and raw repository envelopes are not returned as final responses.
- [x] 3.3 Project only the requested target and required direct nodes; verify completeness before treating a partial direct-node result as sufficient.
- [x] 3.4 Add tests for multiple projects, same-name subjects, multi-parent relations, dependency cycles, external references, conflicts and out-of-catalog items.

## 4. CLI and integration

- [x] 4.1 Provide the query CLI using the public Query JSON and schema-validated response.
- [x] 4.2 Exercise Python and Rust source → FactBatch → SQLite → close/reopen → query in real-source tests.
- [x] 4.3 Run all query tests and strict OpenSpec validation after each implementation change; record actual output in acceptance-results.md.
- [ ] 4.4 Complete full S1–S12 integration acceptance before declaring this component fully complete.

## Evidence (2026-10-26)

- Implementation: semantic_facts/query_engine.py, semantic_facts/cli.py, semantic_facts/repository/store.py.
- Tests: tests/test_query_orchestration.py, tests/test_acceptance.py, repository tests.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40269644416 — query/constructor/induction suite and strict OpenSpec passed; product delivery gate intentionally blocks full-system completion.
- Full dependency-aware invalidation, direct-node completeness, multi-project/cycle acceptance and S1–S12 remain pending.


## Direct-node completeness implementation update (2026-10-26)

- FactBatch construction now emits two bounded inventory levels: the exact project scope lists supported Python/Rust source-file nodes; each file node lists its direct parser declaration nodes. Inventory assertions carry current source state, coverage and evidence.
- Query projection requires a current, evidence-backed, complete inventory for the requested scope/node before it can report the boundary as satisfied. Missing inventory is an explicit coverage_incomplete gap and triggers construction.
- Constructor output is restricted to the requested node for node-target queries. Direct inventory is appended to the repository; old inventory/fact rows are retained. Inventory identity includes validity/source state so a changed source snapshot appends a new inventory instead of conflicting with or replacing old history.
- Tests: source scanner inventory test; query tests for scope inventory, missing inventory repair without deleting facts, and node-target scoping. Latest CI run https://github.com/vchs6/code2semantics/actions/runs/40269286038: repository 39, matrix 15, parser 9, scanner 6, source acceptance 4, packaging 2, executor 3, combined planning/constructor/induction/query 37 passed; strict OpenSpec passed.
- Still pending: necessary ancestor-path progress, dependency-aware invalidation, multi-project/overlapping-root and graph-cycle acceptance, and full S1–S12. Product delivery gate remains blocked.


### Ancestor-path progress (first-phase boundary)

For the supported F2/L3 model, a node-target query now verifies both (a) the current project-scope inventory contains the requested file node and (b) that file has a current direct-declaration inventory. Scope-to-file prerequisite completion is included in the bounded progress set; final response projection returns only the requested node inventory. Tests cover node-target scoping and direct inventory persistence. This does not yet implement arbitrary semantic ancestor chains for higher-layer fact types; those remain outside the current syntax-only support boundary and require later component work.

## Scope authorization regression evidence (2026-10-26)

- Tests in `tests/test_query_orchestration.py` cover disjoint roots, explicitly requested nested roots with distinct source identities, unavailable roots (no fallback and no writes), and out-of-scope node source IDs rejected before repository read.
- CI run `https://github.com/vchs6/code2semantics/actions/runs/40275462491`: repository 45, matrix 15, parser 9, scanner 7, source acceptance 4, packaging 2, executor 3, combined planning/constructor/binding/induction/query 48 passed; strict OpenSpec passed.
- Still pending under 3.4: graph-specific multi-parent/dependency-cycle cases, explicit external-reference projection, conflict projection, and out-of-catalog response tests. Full S1–S12 acceptance remains pending.
## Additional projection and boundary evidence (2026-10-26)

- Query now classifies fields outside the fixed first-phase information-needs catalogue into `out_of_catalog` instead of mixing them into in-scope gaps; supported fields in the same request continue through normal coverage and construction.
- Tests cover mixed supported/out-of-catalog selections, same-named nodes in distinct roots, nested roots, unavailable sources without fallback, out-of-scope node references rejected before repository reads, and projection of external references plus conflict evidence.
- CI run `https://github.com/vchs6/code2semantics/actions/runs/40276135137`: all component suites and strict OpenSpec passed; combined planning/constructor/binding/induction/query suite 51 passed. Product delivery gate still blocks full acceptance.
- Task 3.4 remains pending for graph semantics beyond the current syntax-only F2/L3 boundary: multi-parent relation and dependency-cycle semantics, plus complete S1–S12 coverage. The added tests do not claim those semantics are implemented.

## Graph-boundary query acceptance evidence (2026-10-26)

- Added `test_query_handles_multi_parent_cycle_and_external_edges_without_recursive_expansion` to `tests/test_query_orchestration.py`. It stores a real-schema-validated mixed Python source FactBatch with multi-parent navigation, a dependency cycle and an external terminal reference, then verifies bounded traversal terminates and query output remains limited to requested identity/name fields.
- Repository graph traversal has separate coverage in `tests/repository/test_store.py` for duplicate edge deduplication, multi-parent edges, cycles, external terminal references, depth/edge budget truncation, and immutable fact-row counts.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40297691458 — repository 53 passed; matrix 15; parser 9; scanner 7; source acceptance 4; packaging 2; executor 3; producer dispatch 3; combined information-needs/constructor/induction/query suite 52 passed; strict OpenSpec passed.
- Task 4.4 remains pending: complete S1–S12 integration across the full runtime tool→parser→constructor/induction→FactBatch→repository→response path is not yet demonstrated. Product delivery gate remains blocked.
