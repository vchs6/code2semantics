# Design: Semantic Fact Query

## Scope and dependency order

This component owns deterministic query orchestration and the public minimal response. It consumes the main change's query/response schemas, the repository API, the fixed information-needs catalogue, and the constructor's public ConstructRequest/ConstructResult. It does not own those contracts, the parser registry, the capability matrix, or repository persistence internals.

First-phase supported source languages are Python and Rust. The current constructor can produce syntax inventory F2/L3 only; unsupported fields remain explicit gaps.

## Runtime sequence

1. Validate the caller's current Query against the public contract. Historical snapshots/revisions/refresh are not supported.
2. Inspect each explicitly requested root's current Python/Rust source content, including dirty/untracked files. Do not broaden the requested roots.
3. Read the repository for the current source heads and requested fact fields. The repository filters stale assertion validity/evidence and keeps old fact rows stored.
4. Project current facts and compute missing requested fields.
5. If satisfied, return the minimal output-schema response without construction.
6. If gaps remain and budget permits, create ConstructRequest with the exact query, existing valid FactBatch, unmet gaps, and current source context. Call the constructor; do not perform research, modify the information-needs catalogue, or enable matrix entries at query time.
7. Validate and append the returned FactBatch using the repository's atomic write API. Never delete or replace previous fact rows.
8. Re-read the repository and recompute coverage. A round counts as progress only if requested coverage or an explicitly required prerequisite obligation is satisfied. New unrelated facts do not count.
9. Stop on satisfied, no progress, unavailable source/repository, or budget exhaustion. Return the valid current facts and explicit gaps, not a fabricated answer.
10. Assemble one public response with requested fields, source evidence/context/coverage/basis, relevant direct-node inventory, conflicts, out-of-catalog items, gaps and termination reason. Do not return internal constructor plans or all ancestor facts.

## Current implementation boundary

The query engine already implements the bounded read → constructor → write → re-read loop and checks current source snapshots. The response projection validates the Query and output schema and reports missing fields. The repository now persists and reads normalized evidence, premise, inventory, conflict and navigation rows; current reads exclude invalid assertions while retaining them in storage.

The remaining design work is not to rewrite this loop, but to close acceptance gaps: direct-node completeness obligations, necessary ancestor navigation, multi-project/overlapping-root scoping, dependency-aware invalidation, robust handling of unavailable repositories, and full output projection across all public response fields. The query component must never delete stored facts when sources change.

## Failure and stop behavior

- Invalid Query/response: fail with a contract error before any write.
- Source root unavailable: return termination=unavailable and explicit source-unavailable gaps; never switch source.
- Unsupported information need: return uncovered_need.
- No accepted producer or constructor failure: retain existing valid facts and return the appropriate gap.
- Constructor output is not user response. Only a validated write followed by re-read may satisfy the query.
- No coverage progress: stop, even if unrelated facts were appended.
- Budget exhausted with gaps: stop and return remaining gaps.
