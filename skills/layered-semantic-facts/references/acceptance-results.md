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
