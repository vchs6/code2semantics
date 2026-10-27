# Runtime acceptance results

Date: 2026-10-26

## Verified path

The following bounded path is covered by `tests/test_acceptance.py` and CI run https://github.com/vchs6/code2semantics/actions/runs/40258363539:

- Real Python source fixture under `tests/fixtures/scenarios/python_project/`
- Python AST syntax inventory through the registered `ParserRegistry`
- Deterministic constructor maps parser observations to a Schema-validated F2 FactBatch with source evidence and content digests
- SQLite write, close/reopen, and query
- Repeating an identical scan preserves the number of stored fact rows\n- A changed Python source snapshot is appended under a new source identity; older fact rows remain stored, while current-scope queries select only the latest source snapshot for that exact project root

Observed CI results: repository 35 passed; capability matrix 14 passed; parser registry 6 passed; source scanner 4 passed; runtime acceptance 2 passed; strict OpenSpec passed. The product delivery gate intentionally remains blocked because the full end-to-end pipeline (capability-matrix tool selection/execution, induction, multi-layer construction, and full source-change dependency invalidation) is not yet implemented and verified.

## Scope limitation

This is a partial runtime integration check, not full system acceptance. It does not yet verify tool capability selection, external tool execution, registered parser dispatch from native tool output, induction batching, multi-layer construction, source-change invalidation, the complete public query response, or the required cross-component scenarios S1–S12.

FULL_END_TO_END_ACCEPTANCE: NOT_YET_PASSED

## First-phase language scope: Python + Rust

The first phase supports Python and Rust source inventories. Python is parsed with the standard-library AST. Rust currently uses a deterministic declaration inventory and delimiter-balance checks; it is not a replacement for rustc/rust-analyzer and does not claim type checking, macro expansion, borrow checking, or runtime semantics.

The Rust parser/registry/scanner tests and mixed-language source-to-FactBatch tests are required CI checks. Full product acceptance remains blocked until tool orchestration, induction, full semantic construction, and dependency-aware incremental invalidation are implemented and verified.
## Python + Rust CI update (2026-10-26)

Latest CI run: https://github.com/vchs6/code2semantics/actions/runs/40259119661

- Repository tests: 35 passed.
- Capability matrix tests: 14 passed.
- Parser tests (Python + Rust registry/declarations): 9 passed.
- Source scanner tests (including mixed Python/Rust project): 5 passed.
- Runtime acceptance tests (Python and Rust scan → FactBatch → SQLite → query): 3 passed.
- Strict OpenSpec validation: passed.
- Product delivery gate: BLOCKED by design; full orchestration, induction, higher-layer semantic construction, and dependency-aware incremental invalidation are still missing.

Rust parsing is intentionally a lightweight deterministic declaration inventory with delimiter checks, not rustc/rust-analyzer type checking. Do not describe this as full Rust semantic analysis.

## Expanded component and packaging regression (2026-10-26)

Latest completed CI: https://github.com/vchs6/code2semantics/actions/runs/40268487627

- Repository: 39 passed.
- Capability matrix: 15 passed.
- Parser registry / Python / Rust: 9 passed.
- Mixed-language source scanner: 5 passed.
- Runtime source-to-query acceptance: 4 passed.
- Copied Skill packaging: 2 passed; copied-install test uses only the installed Skill directory for runtime code and assets.
- Bounded tool executor: 3 passed.
- Information-needs + constructor planning + constructor + induction + query orchestration: 30 passed.
- Public contract validation and strict OpenSpec: passed.
- Product delivery gate: BLOCKED by design because full S1–S12 acceptance, direct-node completeness/ancestor obligations, full dependency-aware invalidation, and configured induction-provider/tool orchestration are still incomplete.

This is strong evidence for the implemented component boundaries, not a claim that the full semantic-facts product is complete.


## Direct-node completeness and query scoping (2026-10-26)

CI run: https://github.com/vchs6/code2semantics/actions/runs/40269286038

- Repository: 39 passed; capability matrix: 15; parser: 9; source scanner/inventory: 6; source acceptance: 4; copied packaging: 2; bounded executor: 3; combined planning/constructor/induction/query: 37.
- Strict OpenSpec and public contract validation passed.
- The constructor now persists complete scope and per-file direct-node inventories for supported Python/Rust syntax; query refuses to claim completeness without a current evidence-backed inventory. Tests verify inventory repair and target-node scoping without deleting prior facts.
- Product delivery gate remains BLOCKED because necessary ancestor-path planning, dependency-aware invalidation, multi-project/overlapping-root and graph-cycle cases, tool orchestration/induction provider, and full S1–S12 acceptance remain pending.


## Node-target ancestor path acceptance (2026-10-26)

Latest CI: https://github.com/vchs6/code2semantics/actions/runs/40269644416

The query test suite now proves that a node-target request requires a current scope inventory containing that file plus a current per-file direct-declaration inventory. The constructor appends both inventories, the query loop counts the scope-to-file prerequisite as progress, and the final response returns only the requested node inventory. All component suites and strict OpenSpec passed; the full product gate remains blocked for the remaining general semantic requirements.

## Constructor/query dependency-order update (2026-10-26)

Latest complete component CI: https://github.com/vchs6/code2semantics/actions/runs/40276135137

- Repository: 45 passed; capability matrix: 15 passed; parser: 9 passed; scanner: 7 passed; runtime source acceptance: 4 passed; packaging: 2 passed; bounded executor: 3 passed; producer dispatch: 3 passed; combined information-needs/constructor/binding/induction/query: 51 passed.
- Strict OpenSpec validation passed.
- Constructor dispatch now selects only enabled/accepted matrix entries, supports in-process registry parsers and an injected allowlisted subprocess executor, validates parsed output, and converts failures to explicit gaps. A failed file producer no longer discards independent valid source facts; project inventory becomes partial.
- Constructor request-binding rejects mismatched source, subject, content state and out-of-scope evidence locators. Same-source immutable fact identities reject conflicting field rewrites; new source snapshots append separate rows.
- Query tests cover multiple disjoint roots, nested roots, same-named nodes with distinct identities, unavailable sources, out-of-scope node references rejected before repository reads, mixed supported/out-of-catalog fields, and projection of external references/conflict evidence.
- Product delivery gate intentionally remains BLOCKED. Multi-parent/dependency-cycle semantics, full dependency-aware invalidation, configured cognitive induction provider, full higher-layer semantic construction, and all S1–S12 acceptance remain incomplete.
## Repository validity and premise-closure update (2026-10-26)

CI run: https://github.com/vchs6/code2semantics/actions/runs/40277063506

- Repository suite: 49 passed; capability matrix 15; parser 9; scanner 7; source acceptance 4; packaging 2; bounded executor 3; producer dispatch 3; combined planning/constructor/binding/induction/query 51 passed. Strict OpenSpec passed.
- Source snapshot changes now append `source` and dependent fact/field/evidence/relation/premise/conflict/inventory validity events. Older rows remain stored; returning to an exact prior snapshot can reactivate its retained records with new `current` events.
- `Repository.read()` and `Repository.export_current()` now validate transitive premise closure. Invalid targets, stale content states, explicitly invalidated premise links, and premise cycles do not qualify as current results; they are excluded from current projections without deleting rows.
- Added explicit `invalidate_premise()` and `invalidate_inventory()` APIs. Tests verify premise-target invalidation, cycle rejection, inventory projection filtering, export/read consistency and unchanged row counts.
- Full product delivery gate remains blocked for full system acceptance: higher-layer behavior semantics, graph-specific multi-parent/cycle interpretation, complete dependency-aware reconstruction, and all S1–S12 scenarios remain incomplete.
## Graph storage/projection regression update (2026-10-26)

CI run: https://github.com/vchs6/code2semantics/actions/runs/40277417171

- Repository suite: 51 passed; matrix 15; parser 9; scanner 7; source acceptance 4; packaging 2; bounded executor 3; producer dispatch 3; combined planning/constructor/binding/induction/query 51 passed. Strict OpenSpec passed.
- Navigation projection deduplicates semantically identical edges by source, target, relation and shared conditions while retaining distinct parent edges, reverse/cycle edges, external endpoints, and edges whose conditions contradict each other. It does not recursively walk the graph or claim a contradictory conditional cycle is executable.
- Added regression coverage for multi-parent shape, duplicate edges, cycle edges, external references and mutually contradictory conditions. Historical relation rows remain stored.
- Full product delivery gate remains blocked because higher-layer semantic graph inference, dependency-aware reconstruction and full S1–S12 acceptance are not complete.
## Integrated repository acceptance update (2026-10-26)

CI run: https://github.com/vchs6/code2semantics/actions/runs/40277635793

- Repository suite: 52 passed; capability matrix 15; parser 9; scanner 7; source acceptance 4; packaging 2; bounded executor 3; producer dispatch 3; combined planning/constructor/binding/induction/query 51 passed.
- Strict OpenSpec and public contract validation passed. The only failed step is the product delivery gate, which remains intentionally blocked for full-system S1–S12 acceptance.
- Added integrated repository acceptance covering write/reopen, local field invalidation, transitive premise filtering, explicit revalidation, current export and import into a fresh database. It asserts that fact rows remain unchanged throughout invalidation/revalidation and import/export.
- This verifies the repository lifecycle more completely; it does not close the full product gate for tool orchestration, higher-layer semantic inference, or dependency-aware construction.

## Bounded graph/query integration (2026-10-26)

- CI run: https://github.com/vchs6/code2semantics/actions/runs/40297691458
- Repository suite: 53 passed; capability matrix: 15; parser: 9; source scanner: 7; runtime source acceptance: 4; copied Skill packaging: 2; bounded executor: 3; producer dispatch: 3; combined information-needs/constructor/induction/query suite: 52 passed; strict OpenSpec passed.
- Added repository graph traversal coverage for multiple parents, cycle termination, equivalent-edge deduplication, external terminal references, depth/edge budget truncation and no fact-row deletion.
- Added query-orchestration coverage proving that a multi-parent cyclic graph with an external reference does not cause recursive expansion or leak graph-edge assertions into the minimal response.
- Full S1–S12 acceptance is still NOT passed. The product gate remains blocked until the complete runtime acquisition → parse → constructor/induction → FactBatch → repository re-read → final response workflow and all root scenarios are verified.


## Cross-project Python/Rust acceptance (2026-10-26)

- CI run: https://github.com/vchs6/code2semantics/actions/runs/40297921776
- Runtime acceptance suite: 5 passed. The new case runs the real query/construction pipeline across two explicitly authorized roots (Python and Rust), where both define a same-named `Engine`; it verifies source/subject identity separation, minimal requested-field projection, and explicit out-of-catalog fields.
- Full S1–S12 system acceptance remains NOT_YET_PASSED. The delivery gate is still intentionally blocked because the full provider-backed semantic construction/induction workflow and complete scenario matrix have not been demonstrated.


## Deleted-source retention and import-conflict regression (2026-10-26)

- Added a real-source acceptance case that deletes one Python file, rescans the project, and verifies: the deleted file's prior fact rows remain in SQLite; the current source head points to the new snapshot; current query output excludes the deleted file's facts; unaffected file facts remain available.
- Added a transfer test that rejects importing a different payload under an existing immutable fact identity and verifies all normalized row counts and submission receipts remain unchanged.
- CI run: https://github.com/vchs6/code2semantics/actions/runs/40298718500 — repository 56 passed; transaction 6; transfer 7; repository acceptance 3; matrix 15; parser 9; scanner 7; runtime acceptance 6; packaging 2; executor 3; producer dispatch 3; combined planning/constructor/induction/query 52 passed; strict OpenSpec passed.
- Full S1–S12 acceptance remains NOT_YET_PASSED. The delivery gate remains blocked until the full runtime acquisition/parse/constructor/induction/repository/query-response path and all root scenarios are demonstrated.


## Full acceptance boundary expansion (2026-10-26)

- Added root acceptance for unavailable sources: the query returns `termination=unavailable`, an explicit `source_unavailable` gap, and does not fall back to another project or write facts.
- Added root acceptance for out-of-scope node targets: the request is rejected before querying foreign facts; only explicitly authorized source roots are returned and the foreign repository rows remain untouched.
- Restore hardening now validates both the required normalized table names and required columns before copying a backup. Regressions cover empty SQLite files and malformed databases that reuse expected table names with wrong columns.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40299401934 — repository 57 passed; transaction 6; transfer 8; repository acceptance 3; matrix 15; parser 9; scanner 7; runtime acceptance 8; packaging 2; executor 3; producer dispatch 3; combined planning/constructor/induction/query 52 passed; strict OpenSpec passed.
- Full S1–S12 acceptance remains NOT_YET_PASSED. The product gate is intentionally blocked until the complete provider/tool acquisition → parsing → construction/induction → repository re-read → final response workflow and the entire scenario matrix are verified.

## Query acceptance update (2026-10-26)

CI run: https://github.com/vchs6/code2semantics/actions/runs/40311963317

- Repository: 59 passed.
- Transactions: 6 passed.
- Transfer: 8 passed.
- Repository acceptance: 5 passed.
- Capability matrix: 15 passed.
- Parser: 9 passed.
- Source scanner: 7 passed.
- Runtime acceptance: 9 passed.
- Packaging: 2 passed.
- Bounded executor: 3 passed.
- Producer dispatch: 3 passed.
- Combined information-needs/constructor/binding/induction/query orchestration: 55 passed.
- Strict OpenSpec validation: passed.
- Product delivery gate: BLOCKED as intended; full S1–S12 acceptance has not passed.

New query checks cover a closed repository returning explicit `repository_unavailable` gaps without fallback or fabricated results, and preservation of `budget_exhausted` when the final allowed construction round makes partial progress but still has gaps. Source-deletion acceptance also verifies that old fact rows remain stored while current queries exclude deleted-file facts and retain unaffected current facts.

## Query current-source regression verification (2026-10-26)

CI run: https://github.com/vchs6/code2semantics/actions/runs/40312675115

- Repository suite: 59 passed.
- Transaction suite: 6 passed.
- Transfer suite: 8 passed.
- Repository acceptance suite: 5 passed.
- Capability matrix: 15 passed.
- Parser: 9 passed.
- Source scanner: 7 passed.
- Runtime acceptance: 9 passed.
- Copied Skill packaging: 2 passed.
- Bounded tool executor: 3 passed.
- Producer dispatch: 3 passed.
- Combined information-needs/constructor/binding/induction/query orchestration: 55 passed.
- Public contract validation and strict OpenSpec: passed.
- Product delivery gate: BLOCKED as intended; the acceptance record does not contain `FULL_END_TO_END_ACCEPTANCE: PASS`.

The latest CI run verifies query responses for a closed repository, budget exhaustion after partial progress, current-source modification, and source-file deletion. Current query results exclude superseded/deleted source facts while the database retains prior fact rows. This evidence closes the focused query source-validity regressions only; it does not complete full S1–S12 runtime acceptance.

## Query CLI source-deletion acceptance and quality-gate regression (2026-10-26)

- Query CLI acceptance CI: https://github.com/vchs6/code2semantics/actions/runs/40314761586 — runtime acceptance tests passed, including a real CLI query after source-file deletion. The query rebuilt the current source snapshot, excluded deleted-file facts from current results, preserved prior fact rows, and appended a `modified` validity event for the superseded source.
- Quality-gate RED: https://github.com/vchs6/code2semantics/actions/runs/40314914337 — new unit test failed because prose mentioning the success marker incorrectly made the gate return 0.
- Gate fix: `scripts/quality_gates/check_product_delivery.py` now requires the marker as a standalone line, not as a substring. The unit test suite passes in https://github.com/vchs6/code2semantics/actions/runs/40315019218.
- Latest full CI on `main`: repository 59 passed; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 9; scanner 7; runtime acceptance 10; packaging 2; bounded executor 3; producer dispatch 3; combined planning/constructor/binding/induction/query 55 passed; quality-gate unit tests 2 passed; strict OpenSpec passed.
- Product delivery gate remains BLOCKED because full S1–S12 runtime acceptance has not been demonstrated. This is the expected result, not a component test failure.

## Integrated parser/constructor/induction-boundary acceptance (2026-10-26)

- CI: https://github.com/vchs6/code2semantics/actions/runs/40316268213
- Runtime acceptance: 11 passed. The new integrated case uses a real Python source tree and the enabled producer registry/ParserRegistry path to build an evidence-backed FactBatch; invokes the real induction request/result validator for an unmet higher-level field; verifies that the unconfigured cognitive provider yields an explicit `constructor_unavailable` gap and no inferred fact; persists the deterministic FactBatch to SQLite; closes/reopens the repository; and executes a schema-validated query that returns only requested F2 identity/name fields.
- Full CI component counts: repository 59; transactions 6; transfer 8; repository acceptance 5; capability matrix 15; parser 9; scanner 7; runtime acceptance 11; packaging 2; bounded executor 3; producer dispatch 3; combined information-needs/constructor/binding/induction/query 55; quality-gate unit tests 2; strict OpenSpec passed.
- Product delivery gate: BLOCKED as intended because full S1–S12 production semantics are not yet verified. This integrated case verifies the deterministic syntax-only path and safe induction-unavailable behavior; it does not claim provider-backed induction, external-tool acquisition, F1/F3–F18 semantic production, or full S1–S12 completion.

## Integrated pipeline boundary regression — latest main CI (2026-10-26)

- CI run: https://github.com/vchs6/code2semantics/actions/runs/40316361028
- Runtime acceptance: 11 passed, including the integrated parser/constructor/induction-boundary/repository-reopen/minimal-query case.
- Combined planning/constructor/binding/induction/query orchestration: 55 passed. Repository 59; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 9; scanner 7; packaging 2; executor 3; producer dispatch 3; quality-gate unit tests 2; strict OpenSpec passed.
- The new integrated test verifies real Python source through the enabled producer registry and parser into an evidence-backed FactBatch; invokes the induction grouping/result-validation boundary; confirms the absent cognitive provider yields an explicit gap without fabricating or persisting inferred facts; then writes the deterministic batch, closes/reopens SQLite, and returns a schema-validated minimal query response.
- The CI workflow's overall conclusion remains failure only because the product delivery gate correctly returns BLOCKED: full S1–S12 production semantics have not been demonstrated. This test does not claim external toolchain execution or provider-backed induction. The constructor task record explicitly says the external executor is not yet wired into the runtime loop and the enabled matrix currently contains only in-process parser profiles.

## Native tool-output parser acceptance (2026-10-26)

- Added pure ParseRequest adapters for Cargo metadata JSON (`rust.cargo-metadata`) and Python compileall diagnostics (`python.compileall`); neither adapter executes a tool or reads a project. Both preserve current source/content-state binding, digest, output locator, coverage and explicit language-semantics limits.
- Test-first evidence: RED https://github.com/vchs6/code2semantics/actions/runs/40320249864 (new parser entry points absent); subsequent GREEN component verification https://github.com/vchs6/code2semantics/actions/runs/40320586364 — parser 12 passed, capability matrix 15 passed, combined constructor/query suite 57 passed, strict OpenSpec passed. Overall workflow remains BLOCKED only by the intended product delivery gate.
- CI probe evidence: https://github.com/vchs6/code2semantics/actions/runs/40319334019 — Cargo 1.99.0 returned valid metadata JSON for a temporary fixture; Python 3.12.15 compileall succeeded on a temporary fixture. This is environment probe evidence, separate from parser acceptance.
- **Not yet production-enabled:** current constructor planning selects only `environment="in-process"`; the source scanner/fact constructor currently constructs F2 syntax inventory only and does not yet map Cargo manifest observations into F1/F3/F4/F6 FactBatch assertions. The new profiles therefore remain disabled. Next OpenSpec dependency is constructor producer planning/execution and multi-fact mapping; only after that path has tests and accepted runtime invocation may the matrix entries be enabled.

## Constructor native manifest producer integration increment (2026-10-26)

- RED for constructor consumption: https://github.com/vchs6/code2semantics/actions/runs/40323258026 — once the missing test import was fixed, the test failed because the constructor did not produce F4/F6 facts from Cargo metadata.
- RED for source mutation: https://github.com/vchs6/code2semantics/actions/runs/40324281385 — the constructor initially accepted stale manifest output after the manifest changed during external execution.
- GREEN component verification: https://github.com/vchs6/code2semantics/actions/runs/40324323776 — runtime acceptance 11 passed; information-needs/constructor-plan/constructor/query combined tests 61 passed; repository 59; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 12; scanner 8; executor 3; producer dispatch 3; quality-gate tests 2; strict OpenSpec passed. Overall CI remains blocked only by the intended product delivery gate.
- Implemented the first real consumer slice: constructor invokes an accepted Cargo metadata subprocess profile through the bounded argv-only executor, parses native JSON via ParserRegistry, maps observed manifest records into F4.kind/F6.kind (and F3.entries when requested), preserves source/evidence/content-state metadata, and deduplicates execution by tool per source.
- Project source identity now includes recognized manifest/configuration files such as Cargo.toml, Cargo.lock and pyproject.toml. This prevents manifest-derived facts from remaining current when only the manifest changes.
- After external execution, constructor rescans the source state and discards the batch if the source changed during execution. The new test mutates Cargo.toml inside the executor boundary and verifies no stale F4 fact is returned.
- Added a real Cargo manifest integration test that writes the FactBatch to SQLite, closes/reopens the repository, and verifies a minimal F4.kind query response with evidence.
- Scope limitation: this is a narrow F4/F6 manifest consumer path, not full F1/F3/F4/F6 field coverage, not Python pyproject parsing, and not full S1–S12. The production matrix still keeps all research candidates disabled; the test uses a temporary copied matrix with explicit parser-development acceptance to exercise the path. Do not enable production profiles until supported field mapping, missing-tool/timeout cases, source-state binding and matrix acceptance are complete.

## Request-wide producer coverage and overlap aggregation (2026-10-26)

- Proposal/design/tasks were updated before implementation: https://github.com/vchs6/code2semantics/commit/930ac0eca09cd215ebd3e918ffc2a3375e620a32, https://github.com/vchs6/code2semantics/commit/4787fac6f4c58095a393a33164c96e245fb520fd, https://github.com/vchs6/code2semantics/commit/ebdb195d43fe08a05dbeb331ad45df8dc00d41be.
- The planner now collects all unmet needs across the request per compatible language/environment group and chooses a deterministic greedy minimum sufficient producer cover. It prefers the candidate covering the largest number of remaining needs and breaks ties by stable tool ID. Hard constraints for enabled status, language, platform and environment remain mandatory.
- Request-local FactBatch contributions are aggregated by source/subject/node/fact type/granularity. Equivalent assertion bodies merge evidence by stable evidence ID; incompatible values or reuse of an evidence ID with different content produce an explicit conflict gap and remove the conflicted field from the candidate batch. Repository identity validation remains strict; this is not a persistent constructor-side deduplication index.
- Regression tests: one producer covers multiple requested needs; complementary profiles are selected when no single profile covers all needs; disabled and language/platform/environment-incompatible profiles are excluded; independent evidence is merged; conflicting assertions produce a gap rather than an arbitrary winner.
- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40340224549 — repository 63 passed; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; scanner 8; runtime acceptance 11; packaging 2; executor 3; producer dispatch 3; information-needs/constructor-plan/constructor/contribution/binding/induction/query group 70 passed; quality-gate unit tests 2; strict OpenSpec passed.
- Product delivery gate remains BLOCKED. CI says the acceptance record lacks the standalone `FULL_END_TO_END_ACCEPTANCE: PASS` marker and explicitly rejects a partial source-to-store smoke test as full component integration. Do not add that marker until real S1–S12 acceptance is actually demonstrated.
- Remaining production-chain gaps include complete F1/F3–F18 producers, accepted enabled profiles for manifest producers, complete scenario-specific positive/negative evidence and provider-backed induction. The current integrated Python syntax path and narrow test-only Cargo manifest path do not prove full S1–S12.

## Python manifest source-to-store acceptance follow-up (2026-10-26)

- Initial RED exposed that the new test used the generic request fixture's `/workspace/project` source context instead of binding the request to the temporary project under test. The constructor correctly returned `source_unavailable`; this was an acceptance-fixture defect, not evidence that the parser had failed. The test now creates the real source snapshot with `build_fact_batch` and binds both `existing_valid_facts.sources` and `current_source_context.sources` to that snapshot.
- GREEN component evidence: https://github.com/vchs6/code2semantics/actions/runs/40344057998 — repository 63 passed; transactions 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; scanner 8; runtime acceptance 12; packaging 2; executor 3; producer dispatch 3; constructor/query group 70 passed; quality gate unit tests 2 passed. Strict OpenSpec validation is still running at time of this record. Overall Python job is blocked only by the intended product delivery gate.
- The new runtime acceptance proves Python `pyproject.toml` observations are converted into F3.runtime and F6.kind assertions, persisted to SQLite, survive close/reopen, and are returned by a minimal F3.runtime query with evidence.
- This is one accepted integration slice, not full S1–S12. The production matrix still keeps research candidates disabled; the test enables the Python manifest profile only in a copied temporary matrix. Do not write `FULL_END_TO_END_ACCEPTANCE: PASS` until the complete root scenarios and real production tool profiles are accepted.

## Cross-producer provenance and Rust workspace/dependency acceptance (2026-10-26)

- RED/GREEN for provenance merge: https://github.com/vchs6/code2semantics/actions/runs/40344487255 exposed that request-local aggregation incorrectly treated differing producer method/limitations metadata as conflicting values. The implementation now compares semantic assertion core and premises separately from producer-specific method/limitations, unions evidence by stable ID, deterministically combines methods and limitations, and still gaps on value/context/validity/premise conflicts or conflicting reuse of an evidence ID. Design clarification: https://github.com/vchs6/code2semantics/commit/23ba7acda709fda91181e97153cf0cb101d84740.
- Rust workspace acceptance: https://github.com/vchs6/code2semantics/actions/runs/40344964325. A real temporary Cargo workspace with `manifest-app` and `manifest-core` runs Cargo metadata through the bounded executor, builds FactBatch F4/F6 assertions, writes SQLite, closes/reopens, and queries only `kind`. Assertions verify both workspace members appear as F4 and the `manifest-app -> manifest-core` dependency appears as F6; membership and dependency are not conflated.
- GREEN component counts in that run: repository 63; transaction 6; transfer 8; repository acceptance 5; matrix 15; parser 14; scanner 8; runtime acceptance 12; packaging 2; executor 3; producer dispatch 3; constructor/query/contribution group 70; quality gate tests 2; strict OpenSpec passed. Overall failure is the intentional product delivery gate.
- Python manifest acceptance is also GREEN in the same run: real `pyproject.toml` observations produce F3.runtime/F6.kind, persist to SQLite, survive close/reopen, and return a minimal F3.runtime response with evidence.
- These are accepted narrow Python/Rust source-to-store slices. Full S1–S12 remains unproven; the production matrix still keeps research candidates disabled. Do not add `FULL_END_TO_END_ACCEPTANCE: PASS` yet.

## Query-runtime subprocess wiring and source-state parity (2026-10-26)

- RED: https://github.com/vchs6/code2semantics/actions/runs/40345588518 first showed the query runtime did not accept/pass an external executor. After adding injection, https://github.com/vchs6/code2semantics/actions/runs/40345950065 showed zero tool calls because the constructor returned a `source_modified`/construction gap.
- Root cause: `inspect_source()` hashed only `.py/.rs`, while `build_fact_batch_with_gaps()` also hashed recognized project manifests. The query's current source state and constructor's source state therefore differed for any Cargo/pyproject project. `inspect_source()` now uses the same manifest-aware snapshot inputs, stable sorting and digest algorithm as FactBatch construction. Regression test asserts both APIs return identical source ID/content state and that changing only Cargo.toml changes both.
- GREEN: https://github.com/vchs6/code2semantics/actions/runs/40346459330 — source scanner 9 passed; runtime acceptance 13 passed; constructor/planning/contribution/query group 70 passed; repository 63; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; packaging 2; executor 3; producer dispatch 3; quality gate tests 2; strict OpenSpec passed. Overall failure remains only the intentional full S1–S12 product delivery gate.
- Query orchestration now accepts an optional bounded executor and forwards it to the constructor. A host-owned factory registers only fixed argv `cargo metadata --no-deps --format-version 1`; CLI `query`, `construct` and `scan-source` use this allowlist. Matrix/request data never becomes executable argv.
- The real runtime integration test uses a temporary accepted Cargo profile and two-member workspace, verifies F4 workspace members remain distinct from F6 dependency, persists and reopens SQLite, returns only requested `kind` fields with evidence, and asserts exactly one Cargo invocation across both needs. A follow-up test now exercises this through the actual CLI entrypoint; its CI is pending.
- Production Cargo/Python manifest profiles remain disabled in the checked-in matrix until CLI-level runtime acceptance, failure-mode tests and remaining S1–S12 scenarios pass.

## CLI-level default-executor and subprocess failure acceptance (2026-10-26)

- The runtime integration test now invokes the actual `semantic-facts query` CLI with the host-owned `build_default_tool_executor()` rather than substituting an executor factory. It traces the real `SubprocessToolExecutor.execute` calls, proves Cargo runs exactly once for F4 workspace membership + F6 dependency, verifies both facts survive SQLite close/reopen, and verifies a replayed satisfied query does not invoke Cargo again.
- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40347148315 — runtime acceptance 18 passed (including CLI producer integration and failure cases); source scanner 9; constructor/query group 70; repository 63; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; packaging 2; executor 3; producer dispatch 3; quality gate tests 2; strict OpenSpec passed. Overall failure remains only the expected full S1–S12 product delivery gate.
- Failure-mode tests cover missing executable, timeout, nonzero exit, malformed output and source mutation during execution. Each case returns an explicit gap and no F4/F6 facts from failed/stale output.
- This closes constructor child task 11.1–11.5 for the current Cargo manifest profile. Task 11.6 and main root tasks 8.1–8.5 remain pending until the complete S1–S12 real-source scenario set and all required producer profiles are accepted. Production manifest profiles remain disabled.

## Narrow production profile enablement and language-aware planning (2026-10-26)

- Following real CLI runtime acceptance, the checked-in capability matrix now enables only two narrowly scoped profiles: `rust.cargo-metadata` for `source.f4.kind` and `source.f6.kind`; `python.pyproject-toml` for `source.f3.runtime` and `source.f6.kind`. Each entry's acceptance evidence references parser tests, runtime integration tests and CI. All other research candidates remain disabled. Matrix tests were updated to assert this exact accepted subset.
- Python-only CLI acceptance: https://github.com/vchs6/code2semantics/actions/runs/40348620288 — `pyproject.toml` yields F3.runtime/F6.kind, writes to SQLite, survives close/reopen, returns a minimal response with evidence, and invokes no subprocess. Rust CLI acceptance in the same run proves workspace-member F4 and package-dependency F6 are distinct and Cargo is invoked once.
- A follow-up planner defect was found and corrected: needs such as F6 may list both Python and Rust, but a Python-only root must not schedule Cargo and report a spurious missing Cargo.toml gap. The planner now filters by languages actually found in authorized source roots; mixed-language roots remain eligible for both. Regression: `tests/test_constructor_plan.py::test_request_plan_does_not_select_producers_for_languages_absent_from_source_roots`.
- Latest accepted component evidence: https://github.com/vchs6/code2semantics/actions/runs/40348620288 — repository 63; transactions 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; scanner 9; runtime acceptance 19; packaging 2; executor 3; producer dispatch 3; constructor/planning/query group 71; quality-gate tests 2; strict OpenSpec passed. Full S1–S12 remains pending; do not add the full acceptance marker.

## Root mixed-language source-to-store acceptance (2026-10-26)

- Added `tests/test_acceptance.py::test_mixed_python_rust_manifest_chain_through_cli_store_reopen_and_minimal_projection` as a root acceptance-harness case, not only a child component test.
- It runs the real CLI query on two explicitly authorized roots: Python `app.py` + `pyproject.toml`, and a two-member Cargo workspace with a declared path dependency. It verifies F2 names, F3 runtime, F4 workspace membership and F6 dependency facts, source evidence on every returned field, SQLite persistence, and a minimal post-reopen F6.kind projection.
- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40353437920 — root/runtime acceptance 21 passed; constructor/planning/induction/provider/query group 84 passed; repository 63; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; scanner 9; executor 3; producer dispatch 3; strict OpenSpec passed. Overall workflow remains blocked only by the intentionally fail-closed full S1–S12 product delivery gate.
- This root case closes one real mixed-language source-to-store slice. It does not certify all S1–S12, full direct-child/ancestor semantics across every fact type, or provider-backed cognitive induction. The full acceptance marker remains absent.

## Multi-project validity isolation acceptance (2026-10-26)

- Added `tests/test_acceptance.py::test_multi_project_source_change_does_not_invalidate_unrelated_project_facts`. It creates two real Python project roots, stores both, changes only one root, re-scans it, and verifies the current query returns the changed project's new declaration plus the unchanged project's declaration. It also checks validity events for the unaffected project's fact keys remain `current`.
- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40354905438 — root/runtime acceptance 22 passed; induction provider/constructor/query group 86 passed; repository 63; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; scanner 9; executor 3; producer dispatch 3; strict OpenSpec passed. Overall workflow remains blocked only by the full S1–S12 product delivery gate.
- This verifies current-source invalidation isolation across multiple authorized project roots. Root tasks 8.1–8.5 remain pending for the unimplemented S1–S12 semantic cases and real provider-backed induction.

## Root direct-child completeness and minimal projection acceptance (2026-10-26)

- Added `tests/test_acceptance.py::test_root_acceptance_enumerates_all_direct_children_but_projects_only_requested_fields`. The real CLI query asks only for F2.names, while the response must contain a current, evidence-backed complete scope inventory identifying both `alpha.py` and `beta.py` by stable node IDs. Returned fact projections are constrained to the requested `names` field.
- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40355303673 — root/runtime acceptance 23 passed; provider/constructor/query group 86 passed; repository 63; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; scanner 9; executor 3; producer dispatch 3; strict OpenSpec passed. Overall workflow remains blocked only by full S1–S12 acceptance.
- This directly verifies the rule that complete direct-child identification is independent of the requested field projection and does not require recursive construction of grandchildren. It is one root acceptance scenario, not full S1–S12 completion.

## Multiple Rust workspace isolation root acceptance (2026-10-27)

- Added `tests/test_acceptance.py::test_multiple_rust_workspaces_keep_membership_and_dependencies_scoped` as a real CLI query acceptance case over two separately authorized Cargo workspace roots.
- Each workspace contains an app package and a core package. The test verifies both members and the app-to-core dependency are returned under the owning source root, that facts from the other workspace do not leak across roots, that returned fields are limited to requested F4.kind/F6.kind, and that evidence and source-root identity survive repository re-read.
- Initial RED exposed a test-fixture escaping defect: TOML/source files were written with literal backslash-n sequences, so Cargo could not produce the expected observations and the query terminated `no_progress`. The fixture was corrected to write actual newlines; no production expectation or gate was weakened.
- GREEN component evidence: https://github.com/vchs6/code2semantics/actions/runs/40426615823 — root/runtime acceptance 24 passed; repository 63; transactions 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; source scanner 9; packaging 2; tool executor 3; producer dispatch 3; constructor/induction/provider/query suite 86 passed; quality-gate unit tests 2 passed; strict OpenSpec passed.
- Product delivery gate remains BLOCKED because the full S1–S12 acceptance marker is intentionally absent. This closes one additional multi-workspace acceptance slice only; root tasks 8.1–8.5 remain pending for the remaining semantic scenarios and actual provider-backed induction.

## Overlapping nested Python roots root acceptance (2026-10-27)

- Added `tests/test_acceptance.py::test_overlapping_nested_python_roots_keep_distinct_source_identities` to the real CLI root acceptance suite. The query explicitly authorizes both an outer Python root and its nested root, each containing an `engine.py` declaration with the same symbol name.
- The test verifies both source roots remain represented, same-named declarations retain distinct `(source_id, node_id)` identities, returned fields stay within the requested identity/names projection, evidence remains attached, and repository re-read preserves the same root boundary.
- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40426833999 — root/runtime acceptance 25 passed; repository 63; transactions 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; source scanner 9; packaging 2; tool executor 3; producer dispatch 3; constructor/induction/provider/query suite 86 passed; quality-gate unit tests 2 passed; strict OpenSpec passed.
- Product delivery gate remains BLOCKED for full S1–S12 acceptance. This is a validated nested/overlapping-root slice only; root tasks 8.1–8.5 remain pending for remaining semantic requirements and actual provider-backed induction.
