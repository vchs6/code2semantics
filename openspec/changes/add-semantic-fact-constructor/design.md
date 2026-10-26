# Design: Semantic Fact Constructor

## Scope and dependency order

This component consumes the main change's public contracts and the fixed information-needs catalogue. It does not own public schemas, the capability matrix, parser implementations, induction batching, SQLite persistence, or the final response projection.

First-phase language scope is Python and Rust. Current deterministic extraction is limited to syntax inventory (F2/L3); the design must report unsupported needs as gaps rather than infer runtime behavior.

Dependency sequence:
1. Fixed information-needs catalogue (this design's first-stage deliverable).
2. Tool research for each need and environment, without enabling tools.
3. Capability matrix and parser implementations with independent acceptance evidence.
4. Constructor plan generation and executor orchestration over enabled tools.
5. Parser-result validation and FactBatch construction.
6. Induction batch trigger and result validation.
7. Repository write/re-read is performed by the query orchestrator, never by this constructor.

## First-stage information-needs catalogue

Path: `skills/layered-semantic-facts/assets/information-needs.json`.

The initial catalogue covers only evidence-backed Python/Rust syntax inventory:
- F2 identity, names, boundary, and locators at L3.
- Source evidence and content-state traceability are mandatory.
- Python AST parser supports module/class/function/async-function/import declarations.
- Rust parser supports module/function/struct/enum/trait/impl/type/const/static/use declarations with delimiter-balance diagnostics; it does not claim type checking, macro expansion, borrow checking, or runtime behavior.
- Each need declares an acceptance fixture and research basis. The catalogue is validated against `information-needs.schema.json`.
- Requests for fields outside this initial coverage remain explicit gaps; the runtime cannot modify this file.

## Runtime interfaces

- Input: public `construct_request` from `pipeline.schema.json`, including query, existing valid facts, unmet items, and current source context.
- Plan: deterministic subset of catalogue needs keyed by fact type/field and bounded source scope.
- Tool candidates: read-only `CapabilityMatrix.query`; only entries with `enabled=true`, parser-development acceptance evidence, matching language/platform/environment and need coverage are eligible.
- Execution: an injected executor interface returns tool-native output and an invocation profile. The constructor does not shell-expand arbitrary strings or execute user-supplied commands without an explicit registered executor policy.
- Parse: registered `ParserRegistry` transforms native output plus invocation profile to `parse_result`.
- Construct: `construct_fact_batch` converts validated observations into public FactBatch records, preserving evidence, source content state, coverage and explicit limitations.
- Output: public `construct_result` containing a FactBatch and explicit gaps. No database writes and no final response projection.

## Failure behavior

- Unknown need: gap `uncovered_need`.
- No enabled matching producer: gap `unavailable_tool`.
- Tool execution error/timeout/non-zero exit: structured gap; continue independent needs where safe.
- Parser unsupported or invalid output: structured gap; do not infer or fabricate facts.
- Invalid FactBatch: fail the constructor call and report contract error; do not persist partial output.
- Existing facts with current evidence are reused; a field is not considered satisfied solely because it is non-empty. Current-source state and evidence coverage must match the request.
- No deletes or replacement of previously stored semantic facts. Source changes create new source-state records; repository/query components determine current projection and dependency-aware invalidation.

## Determinism

For fixed query, information-needs catalogue, existing valid facts, source state, matrix contents, and executor outputs, the plan and normalized constructor result must be deterministic. Sort needs, candidates, observations and gaps by stable identifiers before returning.

## Expanded source-project information needs for S1–S12

The four syntax-inventory needs are only the initial executable slice, not the complete constructor input model. Before the survey change adds or recommends tools, this design expands the development-time catalogue to enumerate the source/project evidence required by the accepted S1–S12 scenarios. The catalogue describes needs and evidence requirements; it does not claim that current producers satisfy them.

Required acquisition groups:

1. **Scope and project identity (F1/F2/F3):** explicit roots and exclusions, project boundary/identity, entry points, language/runtime/deployment/configuration hints, and the evidence supporting each boundary. Directory nesting alone must not establish ownership.
2. **Workspace and organization (F4/F5):** workspace manifests, member lists, nested/overlapping project roots, logical responsibility and implementation links. Membership, physical containment and dependency must remain separate relation kinds.
3. **Dependencies and interactions (F6/F7/F8):** declared build/package dependencies, source-level imports/references/calls, interface ownership, request/response shape, triggers, ordering, effects and outcomes. Every edge must retain its source, resolution status, conditions and in-scope/out-of-scope endpoint status.
4. **Language semantics and binding (F9/F10/F11):** declarations, type relations where a real language tool can establish them, binding targets, dispatch/overrides, argument mapping and unresolved/conditional targets. Syntax names alone do not prove type identity or dynamic dispatch.
5. **Internal behavior and algorithm evidence (F12/F13/F14/F15/F16):** data-flow candidates, state transitions, guards, error paths, control-flow successors/back-edges, algorithm steps and explicit proof limitations. Directly observed syntax must be separated from inferred intent, invariants, termination and complexity claims.
6. **Evidence completeness and refinement (F17/F18):** counterevidence, knowledge state, checked/excluded regions, completeness of enumerations, unresolved needs and links from higher-level responsibilities to lower-level implementations.

For each need, the catalogue must state the expected output kind, evidence source, language/platform/environment constraints, current-source binding, coverage/completeness rule, known blind spots, fixture, and research basis. A need may require several producers; tool selection must optimize for combined coverage and compatible environments, not one-tool-per-fact assumptions.

### Ordered hand-off

1. Update this constructor design and information-needs.json first; add negative tests for unknown, unsupported and incomplete evidence needs.
2. Pass the expanded catalogue to survey-info-acquisition-tools. The survey must investigate candidates against each explicit need, execute approved environment probes where available, and record observed versions/output/limitations. Unverified toolchain availability remains unverified.
3. Only after research evidence is recorded, update parser design and implement parsers for the accepted native output formats. Parser tests must use captured or generated native-output fixtures and preserve provenance; parsers do not execute tools or read the project themselves.
4. Only after parser acceptance may the capability matrix enable the corresponding producer profile. Then connect the selected profiles to the constructor runtime and run cross-component acceptance.

The currently enabled in-process Python/Rust syntax parsers remain valid for F2/L3 only. No external profile is enabled merely because a candidate appears in the survey.

## Native-output producer integration (required before enabling new matrix profiles)

The new pure adapters for `rust.cargo-metadata` and `python.compileall` are parser-development components only. The current constructor plan selects `environment="in-process"`, and the current scanner/fact-constructor maps only F2 syntax observations. Therefore these adapters must remain disabled in the capability matrix until the constructor runtime consumes their need IDs and produces validated facts for the corresponding fact types.

The next implementation increment must:

- Plan producer profiles per unmet need, language, platform and environment, retaining multiple complementary producer IDs rather than requiring one tool to cover all needs.
- Execute only enabled/accepted profiles through the existing bounded argv-only executor; command prefixes are fixed by the host configuration, and manifest paths/arguments are passed as individual argv items. Never invoke a shell or execute project source as part of metadata discovery.
- Build invocation profiles from the exact current source snapshot and manifest/configuration content state. Recheck source state after external execution; stale or failed output becomes an explicit gap.
- Convert manifest observations into only the matching F1/F3/F4/F6 fact fields for which the public fact schema and evidence contract can be satisfied. Keep workspace membership, physical containment and dependency edges as distinct relation kinds. Unsupported fields remain gaps.
- Add integration tests using a real temporary Cargo workspace and a Python `pyproject.toml`, run the actual approved command, parse its native output, build a nonempty FactBatch, write/read SQLite, and assert the minimal query response does not leak unrequested fields.

A parser being registered is not enough to enable a matrix entry. Matrix enablement follows constructor-consumer acceptance for the exact invocation profile; it must not be used to claim the entire S1–S12 chain is complete.

## Request-level producer execution and fact identity

The constructor plan is demand-oriented, but execution is task-oriented. A query may have several unmet fields or needs covered by the same producer. Build a demand-to-producer mapping first, then derive canonical execution tasks keyed by source ID, source content state, tool ID, invocation profile and normalized arguments. Execute each unique task once, parse once, and fan observations out to every matching requested need. A local executed-profile set is only a defensive guard; it is not the source of truth for scheduling and must not collapse genuinely different invocations.

Aggregate FactBatch contributions by repository fact identity, not by observation ID alone. If several producers support the same field and values agree, merge evidence deterministically into one fact. If values disagree, preserve both contributions in a conflict record and emit a structured gap; do not append duplicate facts or silently choose a winner. Repository duplicate-identity validation remains strict.

Execution records must make the selected source snapshot, tool profile, normalized arguments, invocation count and output digest observable in tests. If source content changes while a producer is running, discard all outputs and facts derived from that snapshot. An execution error is represented once per unique task and fanned out to affected needs without rerunning the same command per need.
