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
