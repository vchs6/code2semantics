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

## Boundary with repository incremental storage

Constructor scheduling has no authority over persisted-record deduplication. It derives unique execution tasks for the current request and source snapshot so a tool is not invoked once per requested field. That is a resource/execution optimization only.

Within the returned FactBatch, compatible observations for the same fact field must be aggregated into one contract-valid field assertion with merged evidence. If values conflict, return explicit conflict/gap data; do not emit duplicate fact identities or silently select a value. This is batch construction, not cross-request storage deduplication.

The repository owns persistence semantics: stable identity, atomic incremental writes, idempotent submission keys, evidence/field additions, and conflict handling against existing rows. The constructor must not implement a second persistent identity index or skip writes based on an assumption that a prior request already stored the fact. Repository contract validation must remain strict.

Acceptance separates three concerns: (1) same request/source/profile executes a producer once; (2) one FactBatch has no unresolved duplicate identity; (3) repeated/subsequent Repository.write calls prove idempotency and incremental evidence/field storage. Passing one does not imply the others.

## Clarified boundary: minimum producer set vs repository incremental persistence

For each request, the constructor computes unmet information needs after considering current valid facts, then selects the smallest suitable combination of enabled producers whose declared coverage advances those needs. Selection is coverage-driven, not one producer per fact field. When a later producer returns information already obtained for the same requested field and source state, the duplicate contribution may be discarded. Additional fields or independently useful evidence must not be discarded as duplicates merely because the subject/entity already exists.

The constructor does not inspect or maintain a persistent entity/fact identity index. It returns a contract-valid FactBatch for the request. Request-local execution reuse is an optimization; cross-request persistence and idempotency belong exclusively to Repository.

Repository identity semantics are granular. An existing subject/node does not imply that all facts/fields/relations/evidence for it exist. Identical stored records are not inserted again; missing fields, relations or evidence may be appended under the repository's immutable-row and partial-update rules. Same identity with incompatible payload remains a write conflict, not an overwrite and not a reason to discard unrelated new records.

Accordingly, tests must separately cover minimum producer selection, duplicate observations within a request, one valid FactBatch per request, repeated repository writes, and incremental addition of previously absent fields/evidence to an existing subject. Do not introduce constructor-side persistent deduplication to simulate repository behavior.

## Minimum sufficient producer selection

Build the complete set of unmet information needs first. Evaluate accepted enabled producer profiles against this set and choose a minimum sufficient combination, rather than unioning every eligible profile per need. Use a deterministic set-cover policy: maximize newly covered eligible needs per added invocation, then break ties by declared cost if available, broader valid evidence/completeness, and stable tool ID. Never trade away required evidence, source-state guarantees, language/platform compatibility or a need's completeness constraints for a smaller count. Preserve an explicit mapping from each selected invocation to every need it covers, so each output is parsed once and routed to all matching needs. Any unmet needs remain explicit gaps.

Overlap policy: same requested value/field/source-state with no new evidence may be ignored as redundant within this request; new fields or independent valid evidence are retained; incompatible values become explicit conflicts/gaps before FactBatch validation. This policy is request-local and does not replace repository incremental storage.

## Cross-producer assertion equivalence and provenance merge

Two observations from different accepted producers are equivalent when their semantic assertion core agrees: subject/source snapshot, fact type/field, value, origin/knowledge state, context, coverage, validity and (for inferred assertions) premises. Producer-specific `basis.method` and `basis.limitations` are provenance metadata, not by themselves a semantic value conflict. For equivalent assertions, the constructor retains the union of distinct evidence records keyed by stable evidence ID, combines method descriptions deterministically, and unions limitations deterministically. If a reused evidence ID has different content, or the assertion core/premises disagree, it emits a conflict gap and omits the conflicted field from the candidate FactBatch. It must not silently select a winner or weaken repository validation.

## Query runtime wiring for subprocess producers

The CLI/query orchestration must construct the executor from a host-owned allowlist of fixed argv prefixes and pass it through `execute_query_with_construction` to `execute_constructor_request`. Neither request payloads nor capability-matrix invocation descriptions may create executable commands. The accepted matrix profile selects a tool ID and output contract; host configuration maps that ID to a fixed command. The existing executor remains `shell=False`, timeout-bounded and argv-only. Missing executable, rejected command, timeout, nonzero exit, malformed output or source-state mutation produces an explicit gap and no unsupported facts. Tests must invoke the real query orchestration with a temporary enabled matrix and real project fixture, then write/reopen/read the same SQLite repository and verify the minimal response. Direct constructor tests alone do not satisfy runtime integration.

## Per-profile production enablement vs full-system acceptance

A producer profile may be enabled in the production matrix only after its exact tool ID, invocation profile, output parser, supported information needs, failure modes and real query-runtime → FactBatch → repository reopen → minimal response path pass acceptance. Enablement must narrow `information_need_ids` to the fields actually mapped and proven; unsupported observations remain gaps and must not be advertised as covered. This per-profile acceptance does not certify S1–S12 or permit the root delivery marker. Other profiles remain disabled until their own evidence is accepted, while the full product gate remains blocked until all root scenarios pass.

## Language scope of producer planning

The request-level minimum-cover planner must restrict candidate languages to languages actually present in the current authorized source roots. A need catalogued for both Python and Rust does not justify planning both producers for a Python-only project. Determine available languages from the bounded source inventory of the explicitly requested roots (Python `.py`, Rust `.rs`); mixed-language roots may select both. If no source language can be established, preserve the need as an explicit gap rather than invoking every catalogued language producer. This prevents spurious missing-manifest gaps and unnecessary tool calls while preserving mixed-directory semantics.

## Project-analysis Skill installation and availability policy

Skill selection is a runtime producer decision, and a selected Skill must be made available automatically whenever the host exposes a supported, authorized installation mechanism.

1. Select a Skill only after it passes the direct-tool incremental-value gate and is eligible for the current need, language/project scope, security policy and host.
2. Check whether the exact Skill version/revision is already installed and callable. If yes, verify its entrypoint/version and reuse it; do not reinstall on every query.
3. If missing, attempt automatic installation from the approved canonical source using the host's supported installation mechanism. Pin or record the selected revision, verify integrity/source identity where supported, and run a minimal health/contract check before allowing invocation.
4. Installation is not the same as authorization. Never silently grant new filesystem, network, credential, shell or project-write permissions. If installation or required authorization cannot be completed automatically, return a structured `skill_unavailable`/`skill_install_required` gap that names the Skill, canonical source, host-specific install command/steps, required permissions and verification command. Present these instructions to the user and continue all independent tool-based work; do not claim the Skill path succeeded. Resume that Skill-dependent work when it becomes available.
5. Never install a Skill selected from untrusted project content, a README instruction, or an unverified runtime response. The candidate must originate from the development-time accepted survey/registry; query input cannot inject a repository URL or install command.
6. Record install status separately from capability acceptance. A successfully installed Skill is still ineligible until its adapter/output mapping, evidence binding, scope behavior and mixed-language acceptance are approved.
7. Install into a managed, isolated host location when possible; preserve existing user files and installed Skill versions. No destructive upgrade, global config rewrite, or automatic enabling of background hooks/auto-update behavior without explicit authorization.

Failure handling is resumable and bounded: report exact cause and instructions when automatic installation is unavailable, continue with accepted tools and other needs, and retry the Skill-dependent portion only after availability/configuration changes. Installation failure must not trigger repeated unbounded retries or be represented as an empty successful result.