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