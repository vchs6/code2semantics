# Implementation Progress — 2026-10-26

Baseline: `main`, direct commits only. This record separates verified behavior from work still pending.

## Completed and verified in this continuation

### Constructor / producer execution
- `semantic_facts/producer_dispatch.py` routes accepted, enabled capability-matrix entries through `ParserRegistry`.
- In-process parser profiles are supported directly. Subprocess profiles require the allowlisted `SubprocessToolExecutor`; stdout is parsed and validated. Disabled/unaccepted profiles, missing executors, timeouts, nonzero exits and malformed outputs return explicit gaps.
- `source_scanner.build_fact_batch_with_gaps` preserves independent valid files when another file fails and marks project inventory partial.
- `fact_constructor.construct_fact_batch` rejects source/subject/content-state/evidence-locator mismatches and duplicate/missing observation IDs.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40276135137 — repository 45, matrix 15, parser 9, scanner 7, source acceptance 4, packaging 2, executor 3, producer dispatch 3, combined planning/constructor/binding/induction/query 51 passed; strict OpenSpec passed.

### Query scope and projection
- Multiple disjoint roots, explicit nested roots, same-named nodes with separate identities, unavailable roots and out-of-scope node references are tested.
- Out-of-scope node references are rejected before repository reads.
- Fields outside the fixed first-phase information-needs catalogue are returned in `out_of_catalog`, separate from in-scope gaps.
- External-reference boundaries and conflict evidence are retained by query projection.

### Repository validity and immutable history
- Conflicting field payloads under the same source snapshot and logical identity raise `WriteConflict`; they are not silently replaced.
- Source snapshot changes append validity events for old source-owned rows and dependent artifacts. Exact prior snapshots can be reactivated with new current events. Historical rows are never deleted.
- `Repository.read()` and `Repository.export_current()` validate premise closure recursively. Invalid premise targets, stale content states and premise cycles are excluded from current projections.
- Added `invalidate_premise()` and `invalidate_inventory()` APIs.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40277063506 — repository 49, matrix 15, parser 9, scanner 7, source acceptance 4, packaging 2, executor 3, producer dispatch 3, combined planning/constructor/binding/induction/query 51 passed; strict OpenSpec passed.

## Still pending

- Full higher-layer semantic construction beyond Python/Rust F2/L3 syntax inventory.
- Configured cognitive induction provider and evidence-grounded inference for behavior semantics.
- Graph semantics for multi-parent relations, dependency cycles and conditional/contradictory cycles beyond safe finite storage/projection.
- Full dependency-aware incremental reconstruction and all S1–S12 end-to-end acceptance scenarios.
- Product delivery gate intentionally remains blocked until these behaviors have executable acceptance evidence. Do not turn it green by weakening its checks.

## Graph and premise-closure follow-up

- Repository `read()` and `export_current()` now share transitive premise-closure behavior: a target field with stale/invalid premise or a premise cycle is excluded from current projection; no rows are deleted. `invalidate_premise()` and `invalidate_inventory()` are explicit append-only APIs.
- Navigation projection deduplicates exact semantic duplicates but retains separate parent edges, reverse/cycle edges, external references, and edges under contradictory conditions. It stores/projects graph shape without claiming that a conditional cycle is executable.
- Tests added in `tests/repository/test_validity.py` and `tests/repository/test_store.py`; latest CI `https://github.com/vchs6/code2semantics/actions/runs/40277417171` passed all component suites and strict OpenSpec. Product gate remains blocked as designed.