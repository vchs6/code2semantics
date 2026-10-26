# Repository Component Acceptance Evidence — 2026-10-26

CI evidence: https://github.com/vchs6/code2semantics/actions/runs/40277635793

## Verified behavior
- Repository suite: 52 passed, 0 failed, 0 skipped.
- Strict OpenSpec validation and public contract validation passed.
- Atomic immutable writes reject conflicting identities and preserve facts/attributes/submissions on rollback.
- Source-head changes append validity events for source-owned records and dependent artifacts. Old rows remain stored; current reads use the latest source snapshot. Reverting to a retained source snapshot appends current events rather than rewriting history.
- Current reads and exports check source state, evidence freshness and recursive premise closure. Invalid targets and premise cycles are excluded from current projections without deleting records.
- Explicit APIs exist for field, fact, relation, evidence, conflict, premise and inventory invalidation. Navigation projection deduplicates identical edges while preserving multi-parent edges, reverse/cycle edges, external endpoints and contradictory conditions.
- Integrated repository acceptance covers write/reopen, query, local invalidation, premise closure, revalidation, current export/import, backup/restore and conflict rollback.

## Still pending
- Do not mark full repository/product acceptance complete until graph-dependent reconstruction, precise source-change dependency invalidation across all semantic layers, full multi-parent/cycle inference and all S1–S12 end-to-end scenarios are verified.
- The product delivery gate remains intentionally blocked for those system-level gaps.
