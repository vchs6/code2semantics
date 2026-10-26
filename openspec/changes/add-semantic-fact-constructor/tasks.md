# Tasks

Implementation is TDD: write a failing behavior test (RED), implement the smallest component change, then run focused tests and regression (GREEN). Only this component's code is owned here; public contracts and cross-component response orchestration remain with the main/query changes.

## 1. Information-needs catalogue (first-stage deliverable)

- [x] 1.1 Create `skills/layered-semantic-facts/assets/information-needs.json` from the current F2 fact-catalogue fields and the fixed Python/Rust first-phase scope; every entry must name required evidence kinds, current-source and coverage requirements, production mode, fixture, and research basis.
- [x] 1.2 Add positive and negative catalogue validation tests against `assets/information-needs.schema.json`, including duplicate need IDs, empty fields, missing evidence kinds and unsupported fact fields; run `python -m pytest tests/test_information_needs.py -q`.
- [x] 1.3 Add a deterministic catalogue loader that rejects invalid JSON/schema and duplicate need IDs without mutating the catalogue; run `python -m pytest tests/test_information_needs.py -q`.
- [x] 1.4 Record the initial catalogue's explicit unsupported scope and evidence provenance in `references/information-needs.md`; do not claim semantic fields not produced by current parsers.

## 2. Deterministic request-to-plan matching

- [x] 2.1 Add RED tests for partially satisfied F2 requests, unknown needs, empty source scope, stale content state, and repeated identical requests; run `python -m pytest tests/test_constructor_plan.py -q`.
- [x] 2.2 Implement `plan_constructor_request` to map requested fact types/fields and unmet items to the fixed catalogue; produce stable, sorted plan items and explicit `uncovered_need` gaps.
- [x] 2.3 Verify non-empty but insufficient values are not considered satisfied unless evidence, validity and coverage meet the request; never mutate the catalogue or matrix at runtime.
- [x] 2.4 Add matrix selection tests: disabled tools, tools without parser-development acceptance, environment mismatch and partial coverage must not be selected; multi-tool coverage may be combined. Run `python -m pytest tests/test_constructor_plan.py tests/capability_matrix -q`.

## 3. Tool executor boundary and parser integration

- [x] 3.1 Define an injected executor protocol with bounded timeout, argv-only invocation, captured stdout/stderr/exit code and explicit invocation profile; test that no shell string execution is used.
- [x] 3.2 Implement a registry-driven execution loop that selects only enabled matching matrix entries, invokes the registered executor, passes output to `ParserRegistry`, and converts unsupported profiles/failures into explicit gaps.
- [x] 3.3 Add Python and Rust source fixtures for module/symbol inventories and malformed input; verify deterministic evidence locators and content digests.
- [x] 3.4 Ensure one failed producer does not discard independent valid observations; reject malformed parser results before construction.

## 4. FactBatch construction and evidence discipline

- [x] 4.1 Reuse the current constructor implementation through a stable interface and add tests for F2 reference identity, names, boundary, locators, evidence, content state, coverage and limitations.
- [x] 4.2 Add conflict and request-binding checks: do not silently replace existing facts; do not accept observations for another source, subject, content state or out-of-scope target.
- [x] 4.3 Validate the complete FactBatch against public schemas before returning; on failure return a structured error and no partial batch.
- [x] 4.4 Verify no repository import/write occurs in the constructor package and no final output-schema response is assembled here.

## 5. Constructor component acceptance

- [x] 5.1 Add `tests/test_constructor.py` for catalogue → plan → enabled producer → parser → FactBatch, using real Python/Rust source fixtures and no mocked successful parser output.
- [x] 5.2 Run `PYTHONPATH=skills/layered-semantic-facts/scripts python -m pytest tests/test_information_needs.py tests/test_constructor_plan.py tests/test_constructor.py -q`.
- [x] 5.3 Run the relevant repository, matrix, parser, scanner and acceptance regression suites; strict-validate this change.
- [x] 5.4 Update this task list only from observed test evidence and record limitations; no source facts may be deleted by implementation or test.



## Evidence update (2026-10-26)

- Catalogue and loader: `skills/layered-semantic-facts/assets/information-needs.json`, `skills/layered-semantic-facts/scripts/semantic_facts/information_needs.py`, `references/information-needs.md`.
- Request planning: `semantic_facts/constructor_plan.py`; tests: `tests/test_information_needs.py`, `tests/test_constructor_plan.py`.
- CI run `https://github.com/vchs6/code2semantics/actions/runs/40261330788`: information-needs and constructor-plan tests passed; strict OpenSpec passed. Product delivery gate remains blocked because full tool orchestration and semantic construction are not yet complete.


## Verified implementation evidence (2026-10-26)

- Fixed information-needs catalogue and loader: `assets/information-needs.json`, `semantic_facts/information_needs.py`.
- Deterministic planning and matrix selection: `semantic_facts/constructor_plan.py`; tests include partial satisfaction, unknown needs, stale assertions, empty scope, deterministic plans, disabled profiles, partial coverage and environment mismatch.
- Parser and FactBatch construction: `semantic_facts/info_parser.py`, `semantic_facts/fact_constructor.py`, `semantic_facts/source_scanner.py`, `semantic_facts/constructor.py`; Python and Rust are supported for syntax-only F2/L3 facts.
- Bounded external executor boundary: `semantic_facts/tool_executor.py`; tests cover allowlisted argv execution, stdout/stderr/exit code capture, timeout and rejected profiles. It is not yet wired as an external producer in the runtime loop because the accepted first-phase matrix contains in-process parser profiles only.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40268078346. Prior completed regression run passed repository 39, matrix 15, parser 9, scanner 5, source acceptance 3 and the combined information-needs/plan/constructor/induction/query suite 30; strict OpenSpec passed. Product delivery gate remains blocked for missing full-system acceptance.
- Still pending: 3.2 registry-driven external tool execution loop; 3.4 independent producer failure preservation; 4.2 complete request-binding/conflict checks at constructor boundary; full multi-layer semantic construction and configured induction-provider integration. Do not mark these complete based on syntax inventory tests.

## Focused completion evidence (2026-10-26)

- Failure isolation: `source_scanner.build_fact_batch_with_gaps` preserves valid per-file observations and returns explicit parse/producer gaps for failures; project direct-node inventory is marked partial when any file fails. `execute_constructor_request` carries these gaps into `ConstructResult` without discarding successful files.
- Request binding: `construct_fact_batch` rejects mismatched source IDs, subject IDs, content states, missing/duplicate observation IDs, missing evidence, and evidence locators outside the requested file before building any FactBatch.
- Tests: `tests/test_source_scanner.py` partial-scan test; `tests/test_constructor.py` mixed-validity constructor test; `tests/test_constructor_binding.py` source/subject/state/locator binding tests.
- CI run `https://github.com/vchs6/code2semantics/actions/runs/40275399143`: repository 45, matrix 15, parser 9, scanner 7, source acceptance 4, packaging 2, executor 3, combined information-needs/plan/constructor/binding/induction/query 47 passed; strict OpenSpec passed. Product delivery gate remains blocked by full-system acceptance gaps.
- Still pending: 3.2 external producer executor integration. Current accepted Python/Rust producers are in-process ParserRegistry profiles; do not mark external subprocess producer dispatch complete until an accepted matrix profile and runtime tests exercise that path.
## Producer dispatch completion evidence (2026-10-26)

- `semantic_facts/producer_dispatch.py` now dispatches accepted enabled matrix profiles. In-process entries go through `ParserRegistry`; subprocess entries require the injected allowlisted `SubprocessToolExecutor`, then stdout is passed through `ParserRegistry` and the result is schema-validated. Disabled/unaccepted profiles, missing executors, timeout/nonzero exit and parser errors become explicit gaps.
- `source_scanner.build_fact_batch_with_gaps` uses matrix-selected entries and the dispatcher; one producer failure does not discard independent valid file observations. Partial source inventories are explicitly marked partial.
- Tests: `tests/test_producer_dispatch.py` covers successful subprocess→parser conversion, subprocess failure gaps, and disabled producer rejection. `tests/test_source_scanner.py` and `tests/test_constructor.py` cover independent file failure preservation. `tests/test_constructor_binding.py` covers source/subject/content/locator binding.
- CI `https://github.com/vchs6/code2semantics/actions/runs/40276135137`: repository 45, matrix 15, parser 9, scanner 7, source acceptance 4, packaging 2, bounded executor 3, producer dispatch 3, combined planning/constructor/binding/induction/query 51 passed; strict OpenSpec passed. The product delivery gate remains blocked for full S1–S12 system acceptance.
- Boundary: subprocess dispatch is implemented and tested as an injected, allowlisted path. The first-phase checked-in Python/Rust matrix continues to use in-process parsers; no external tool is marked enabled without parser-development acceptance.

## 6. S1–S12 source-project information needs (next apply; prerequisite to tool survey)

These tasks are deliberately pending. The existing checked tasks validate only the initial F2/L3 slice and must not be interpreted as delivery of the full source-information model.

- [x] 6.1 Derive a requirement-to-information-needs table from research scenarios S1–S12 and fact catalogue F1–F18. Include scope/project identity, workspace membership, physical/logical organization, dependencies/interactions/interfaces, types/bindings/dispatch, data/control flow, state/error/algorithm evidence, knowledge/completeness and higher-to-lower refinement. Preserve the distinction between direct evidence and cognitive inference.
- [x] 6.2 Expand `assets/information-needs.json` and its schema/tests with stable need IDs, fact fields, evidence kinds, expected native output, source/current-state binding, completeness criteria, language/platform/environment constraints, limitations, fixture and research basis. A need may list multiple candidate producer families; do not claim any candidate is installed or accepted here.
- [x] 6.3 Add RED tests proving unknown, unsupported, incomplete-coverage and missing-evidence needs are not silently marked covered; run focused information-needs and constructor-plan tests.
- [x] 6.4 Update `references/information-needs.md`, this task list and `traceability.md` to map S1–S12 → fact fields → information needs → required evidence. Strict-validate the constructor change and record the actual CI result before handing the catalogue to tool research.
- [ ] 6.5 Only after 6.1–6.4 pass, hand the immutable needs catalogue to `survey-info-acquisition-tools`; do not expand the tool survey before the needs catalogue is reviewed and validated.

## Stage 1 acceptance evidence (2026-10-26)

- Expanded `assets/information-needs.json` to 127 stable per-field needs covering every field in F1–F18 and referencing all scenarios S1–S12.
- Each need records expected output kind, candidate producer family (research hypothesis only), evidence kinds, current-source and coverage rules, languages, platforms, environments, limitations, fixture, research basis and acceptance status.
- Only the four existing F2/L3 syntax needs are marked `accepted_initial_slice`; the remaining 123 needs are `research_required` and are not enabled in the capability matrix.
- Added tests asserting exact catalogue-to-fact-field coverage, all S1–S12 IDs, required metadata, rejection of missing metadata, duplicate IDs, omitted needs and that research-required candidates are not marked enabled.
- Updated the validation fixture and traceability table so the public design-asset validator uses the current catalogue.
- CI GREEN for the focused information-needs/constructor-plan/constructor/binding/induction/query suite: https://github.com/vchs6/code2semantics/actions/runs/40318346289 — 57 passed in the combined step; strict OpenSpec passed. The overall workflow remains BLOCKED only at the product delivery gate, which is expected until S1–S12 end-to-end acceptance.
- Stage 1 is complete as a needs specification and validation deliverable only. No tool has been researched or enabled as a result of these candidate-family entries. Task 6.5 remains pending until this catalogue is handed to the survey change through its ordered workflow.

## 7. Constructor integration for researched native-output producers (next apply)

These tasks follow accepted pure parser adapters. They are prerequisites to enabling `rust.cargo-metadata` or `python.compileall`; do not treat parser registration as production capability.

- [ ] 7.1 Add RED tests proving `plan_constructor_request` can plan an enabled/accepted producer by environment for an unmet non-F2 information need, while disabled/unaccepted entries and platform/language mismatches remain gaps. The plan must preserve multiple complementary producer IDs for a need.
- [ ] 7.2 Implement environment-aware planning across `in-process` and `subprocess`, preserving fixed catalogue semantics and no mutation of needs/matrix. Keep producer invocation commands out of user-controlled query input.
- [ ] 7.3 Add RED tests for constructor execution of accepted manifest profiles through `SubprocessToolExecutor` using a temporary Cargo workspace and a Python `pyproject.toml`; verify bounded argv-only execution, explicit missing-tool/timeout/failed-command gaps, and source-state recheck after execution.
- [ ] 7.4 Implement manifest-output orchestration from selected matrix profile through native command → parser registry → observations. Parsers remain pure; executor owns invocation; constructor owns producer selection and aggregation.
- [ ] 7.5 Extend fact construction only for public-contract-supported F1/F3/F4/F6 fields, preserving manifest evidence and distinct membership/dependency relation kinds. Unsupported fields must remain explicit gaps; do not fabricate F5/F16 inference.
- [ ] 7.6 Add end-to-end acceptance from real temporary Python/Rust project manifests through nonempty FactBatch, SQLite write/reopen/read and minimal query projection. Run focused tests and strict OpenSpec; only then enable each matching matrix profile with parser-development acceptance evidence.


### Task 7.1–7.2 evidence (2026-10-26)

- RED: https://github.com/vchs6/code2semantics/actions/runs/40321016282 — an enabled/accepted Cargo metadata profile was not selected because constructor planning hard-coded the in-process environment.
- GREEN: https://github.com/vchs6/code2semantics/actions/runs/40321130067 — the planner now searches the information need's declared environments and retains selected producer profile metadata (tool ID, environment, invocation, output kinds). The focused constructor/plan combination passed 58 tests; strict OpenSpec passed. Product delivery gate remains blocked as expected.
- Remaining 7.3–7.6: actual subprocess execution, native observation to F1/F3/F4/F6 FactBatch mapping, persistence/reopen/query acceptance, and only then matrix enablement. These remain unchecked.

### Task 7 progress evidence (2026-10-26)

- 7.1–7.2: environment-aware producer planning has RED/GREEN evidence in https://github.com/vchs6/code2semantics/actions/runs/40321130067.
- 7.3–7.5: first accepted Cargo metadata subprocess is now executed and parsed, with F4.kind/F6.kind observations mapped into a schema-valid FactBatch. Source/manifest state is included in source identity, and a post-execution rescan rejects stale output. RED/GREEN evidence: https://github.com/vchs6/code2semantics/actions/runs/40324281385 and https://github.com/vchs6/code2semantics/actions/runs/40324323776.
- 7.6: narrow Cargo F4 persistence/reopen/minimal-query test passes in the same GREEN run. The task remains unchecked because the full requested contract includes broader F1/F3/F4/F6 mapping, missing-tool/timeout coverage and Python/Rust project manifest acceptance.
- Matrix decision: keep all research candidates disabled in the checked-in production matrix. Parser and constructor acceptance has been exercised against a temporary test matrix, not yet sufficient for enabling the profile globally.

## 8. Request-level producer deduplication

- [x] 8.1 Add a RED test proving one selected producer covering multiple requested needs is invoked once and its observations satisfy all matching fields.
- [ ] 8.2 Add a RED test proving matching values from multiple producers become one fact with merged evidence.
- [ ] 8.3 Add a RED test proving disagreeing values become an explicit conflict and do not silently overwrite one another.
- [ ] 8.4 Build a canonical execution-task list keyed by source snapshot, tool ID, invocation profile and arguments; execute each unique task once and fan its observations out to matching needs.
- [ ] 8.5 Aggregate by repository fact identity before FactBatch validation. Keep repository duplicate-identity validation strict.
- [ ] 8.6 Test source changes during execution and verify outputs from the stale snapshot are discarded.
- [ ] 8.7 Run focused tests, repository/query regressions, strict OpenSpec and full CI. Keep new profiles disabled until accepted.

### Request-level deduplication evidence

- Proposal/design/tasks were updated before applying the fix: https://github.com/vchs6/code2semantics/commit/3308646ae7694008e1840f1840d06a6fa1cac1c9 and https://github.com/vchs6/code2semantics/commit/ee514155192597eb59b186b82897f8307274a932.
- The regression test selects Cargo metadata for both F4.kind and F6.kind and asserts the executor call count is exactly one. CI run https://github.com/vchs6/code2semantics/actions/runs/40333047820 passed all component test steps; overall failure was only the expected product delivery gate.
- A further fix keys the execution guard by tool ID, environment, invocation profile and normalized arguments rather than tool ID alone: https://github.com/vchs6/code2semantics/commit/fc95c520a8f8ba4d0d9c5d42e89f2762a5cb8a0d. Its CI run is pending at https://github.com/vchs6/code2semantics/actions/runs/40333512425; do not mark task 8.4 or the whole issue complete until that run is inspected.

## 9. Component-boundary acceptance for duplicate contributions

- [ ] 9.1 Verify the constructor execution plan groups only equivalent tool tasks for the same source snapshot, invocation profile and normalized arguments; do not add persistent deduplication state to the constructor.
- [ ] 9.2 Verify compatible observations contributing to the same fact field produce one FactBatch fact with merged evidence, and conflicting values produce an explicit conflict/gap before batch validation.
- [ ] 9.3 Keep cross-request incremental writes, submission-key idempotency, existing-record reuse and evidence/field additions owned by the repository; add no duplicate persistent identity cache in the constructor.
- [ ] 9.4 Add/retain repository acceptance tests proving repeated identical submissions do not duplicate rows, changed submissions with the same key are rejected, and new evidence/fields are incrementally stored without deleting unrelated facts.
- [ ] 9.5 Run constructor and repository suites independently, then the integrated write/reopen/minimal-query acceptance. Report execution reuse, FactBatch validity and repository idempotency as separate results.

## 10. Minimum sufficient producer selection for a request

- [x] 10.1 Add RED tests where one accepted producer covers two unmet needs while two separate producers cover one each; assert the planner selects the single producer when its profile meets every constraint.
- [x] 10.2 Add RED tests where no single producer covers all needs; assert a deterministic minimum combination is selected and uncovered needs remain explicit gaps.
- [x] 10.3 Add tests proving language/platform/environment, evidence-kind, completeness and limitations constraints cannot be traded away for fewer invocations.
- [x] 10.4 Implement request-level deterministic minimum sufficient producer selection over all unmet needs; keep a separate demand-to-selected-producer mapping and execute each selected invocation once.
- [x] 10.5 Test overlap handling: redundant same-value contribution is not duplicated; new fields/evidence survive; incompatible values create an explicit conflict/gap before FactBatch validation.
- [ ] 10.6 Run constructor planning/execution, repository incremental enrichment, SQLite reopen/minimal query, strict OpenSpec and full CI. Only mark complete from observed evidence.

### Minimum producer selection progress (2026-10-26)

- Proposal/design/tasks were updated before implementation: proposal https://github.com/vchs6/code2semantics/commit/930ac0eca09cd215ebd3e918ffc2a3375e620a32; design https://github.com/vchs6/code2semantics/commit/4787fac6f4c58095a393a33164c96e245fb520fd; tasks https://github.com/vchs6/code2semantics/commit/ebdb195d43fe08a05dbeb331ad45df8dc00d41be.
- Added helper-level and planner-level tests proving one accepted profile covering identity+names is preferred over two narrow profiles across the full request. Implementation now gathers all unmet need IDs per compatible language/environment group before selecting producers, then applies deterministic greedy set cover by maximum newly covered needs and stable tool-ID tie-break.
- GREEN component evidence: https://github.com/vchs6/code2semantics/actions/runs/40338995823 — information-needs/constructor-plan group 65 passed; repository 63; transaction 6; transfer 8; repository acceptance 5; matrix 15; parser 14; scanner 8; runtime acceptance 11; executor 3; producer dispatch 3; constructor/query combined 65; quality gate 2; strict OpenSpec passed. Overall run remains blocked only by the full S1–S12 product gate.
- Task 10.1 is complete. Tasks 10.2–10.6 remain pending: complementary minimum coverage, hard constraint tests, overlap conflict aggregation, and full integration acceptance are not yet proven.

### Request-wide selection and overlap handling evidence (2026-10-26)

- CI GREEN: https://github.com/vchs6/code2semantics/actions/runs/40340224549. OpenSpec validation passed. Component results: repository 63; transactions 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; scanner 8; runtime acceptance 11; packaging 2; executor 3; producer dispatch 3; information-needs/constructor-plan/constructor/contribution merge/binding/induction/query group 70 passed; quality-gate tests 2 passed.
- Minimum producer selection now evaluates the full set of unmet needs per compatible language/environment group and uses deterministic greedy set cover. A single accepted profile covering multiple needs is preferred; complementary profiles are selected only when needed. Hard language/platform/environment/disabled-profile constraints are tested.
- Request-local fact contributions are grouped by source/subject/node/fact type/granularity. Equal assertion bodies merge independent evidence by evidence ID. Incompatible assertions or reused evidence IDs with different content produce an explicit conflict gap and the conflicted field is omitted from the batch; repository duplicate identity validation remains strict.
- Product delivery gate remains BLOCKED because `references/acceptance-results.md` lacks the full acceptance success marker on a standalone line; the gate explicitly rejects a partial source-to-store smoke test as proof of full component integration. Do not alter the gate marker without completing full S1–S12 acceptance.
- Task 10.6 remains pending. Full producer→FactBatch→repository→reopen→minimal response coverage across S1–S12 is not yet demonstrated.

## 11. Query-runtime subprocess integration

- [x] 11.1 Add a RED integration test calling `execute_query_with_construction` with a temporary accepted Cargo profile and a real multi-member workspace; assert current runtime does not invoke the executor or return F4/F6 facts yet.
- [x] 11.2 Add optional executor injection to query orchestration and pass it to `execute_constructor_request` without changing the pure `execute_query` read/projection path.
- [x] 11.3 Add a host-owned default executor factory with fixed argv prefixes for specifically accepted tool IDs; never build commands from query or matrix input. Wire CLI `query` and `construct` entrypoints to this factory.
- [x] 11.4 Verify real Cargo metadata invocation through query runtime produces distinct workspace-membership F4 and dependency F6 facts, writes SQLite, survives close/reopen and returns only requested fields/evidence.
- [ ] 11.5 Verify missing Cargo, timeout, non-zero exit, malformed output and source mutation all fail closed with explicit gaps and no fabricated facts.
- [x] 11.6 Enable only the exact Cargo/Python manifest profiles after their runtime path/failure-mode evidence passes, narrowed to supported information needs; keep all other research profiles disabled. Keep the root S1–S12 product gate blocked.

### Query-runtime producer wiring evidence (2026-10-26)

- RED: https://github.com/vchs6/code2semantics/actions/runs/40345588518 — query runtime rejected executor injection; after signature change, https://github.com/vchs6/code2semantics/actions/runs/40345950065 exposed source-state mismatch and zero producer calls.
- Root fix: `inspect_source` now includes the same recognized project manifests as FactBatch construction, so source IDs/content states match when only Cargo.toml/pyproject.toml contributes to state. Regression test compares both APIs and checks manifest-only changes alter identity.
- Implementation: `execute_query_with_construction` accepts and forwards an optional bounded executor. `build_default_tool_executor()` owns a fixed argv allowlist for Cargo metadata; CLI query/construct/scan-source use this host-owned executor. Query payloads and matrix invocation descriptions cannot provide command prefixes.
- GREEN CLI-level runtime acceptance: https://github.com/vchs6/code2semantics/actions/runs/40346686809 — runtime acceptance 13 passed, including a real two-member Cargo workspace; F4 workspace membership and F6 dependency are separately returned; SQLite write/close/reopen and minimal `kind` projection with evidence passed; Cargo was invoked once for both needs and not rerun on an already-satisfied replay. Source scanner 9 passed; constructor/query group 70 passed; repository 63; transactions 6; transfer 8; repository acceptance 5; matrix 15; parser 14; packaging 2; executor 3; producer dispatch 3; quality gate unit tests 2; strict OpenSpec passed.
- Task 11.5 remains pending: constructor/runtime-specific tests for missing Cargo, timeout, nonzero exit, malformed output and source mutation must be demonstrated as one explicit failure-mode acceptance set. Task 11.6 remains pending until those tests pass; production manifest profiles remain disabled.
- Full S1–S12 tasks 10.6 and root 8.1–8.5 remain pending. The full product gate correctly remains blocked; do not add the full acceptance marker yet.

### Subprocess failure-mode acceptance evidence (2026-10-26)

- Added runtime failure acceptance for missing executable, timeout, nonzero exit, malformed Cargo metadata output, and source mutation during execution. Each case asserts no F4/F6 manifest facts are fabricated and an explicit gap is returned.
- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40347002211 — runtime acceptance group 18 passed, including all new failure cases; source scanner 9 passed; repository 63; transactions 6; transfer 8; repository acceptance 5; matrix 15; parser 14; constructor/query group 70; quality gate tests 2; strict OpenSpec passed. Overall failure was only the expected product delivery gate.
- Task 11.6 remains pending until the actual CLI entrypoint acceptance against the host-owned default executor and full S1–S12 scenario matrix are green. The production manifest matrix entries remain disabled meanwhile.


Per-profile enablement rule: a profile's own accepted real-runtime evidence can authorize that narrow profile; it does not authorize any unrelated profile or the full S1–S12 success marker.

## 12. Restrict producer selection to actual source languages

- [x] 12.1 Add a RED test for a Python-only project whose F6 need is catalogued for both Python and Rust; assert the plan does not select the Rust Cargo producer or report a missing Cargo.toml gap.
- [x] 12.2 Implement bounded language discovery from authorized source roots and intersect each need's declared languages with languages actually present before request-wide set cover.
- [x] 12.3 Add mixed Python/Rust scope coverage proving both language producers remain eligible only when both languages are present, while language/platform/environment constraints stay hard constraints.
- [x] 12.4 Run planner, CLI Python/Rust manifest acceptance, failure modes, strict OpenSpec and all component suites; only then enable the exact Python manifest profile.

### Source-language-aware planning evidence (2026-10-26)

- RED: https://github.com/vchs6/code2semantics/actions/runs/40348349667 exposed that a Python-only request still planned the Rust Cargo profile for a cross-language F6 need. The same run also showed a malformed TOML test fixture; the fixture was rewritten with literal multiline TOML, not by weakening parser checks.
- Implementation: planner discovers `.py`/`.rs` languages only under current authorized source roots, respects excluded directories and scope excludes, and filters each language/environment candidate group to languages actually present. If a concrete root exists but contains no supported language sources, it does not plan arbitrary language producers; abstract plans with unavailable roots retain prior catalogue planning behavior and runtime will return source-unavailable gaps.
- GREEN: https://github.com/vchs6/code2semantics/actions/runs/40348620288 — runtime acceptance 19 passed (including CLI Python manifest + Rust workspace/dependency paths); source scanner 9; constructor/planning/query group 71; repository 63; transaction 6; transfer 8; repository acceptance 5; matrix 15; parser 14; packaging 2; executor 3; producer dispatch 3; quality gate tests 2; strict OpenSpec passed. Product gate remains blocked for full S1–S12.
- Both exact manifest profiles are now enabled narrowly: Cargo only `source.f4.kind`/`source.f6.kind`; Python only `source.f3.runtime`/`source.f6.kind`. Other research candidates remain disabled. Task 12.3 remains pending until mixed Python/Rust scope regression passes.

### Per-root producer language acceptance evidence (2026-10-26)

- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40349969959 — runtime acceptance 20 passed, including Python-only source scope, Rust workspace, and mixed Python/Rust scope; constructor/planning/contribution/query group 72 passed; repository 63; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; scanner 9; executor 3; producer dispatch 3; strict OpenSpec passed. Overall workflow remains blocked only by the full S1–S12 product delivery gate.
- Planner discovers languages from explicitly authorized source roots and excludes producer profiles for languages absent from those roots. Constructor execution independently checks each root's actual source languages before invoking a selected producer, preventing Cargo from running against a Python-only root or Python manifest parsing against a Rust-only root. Mixed roots still invoke the appropriate profiles per root; the Cargo invocation count remains one for the Rust root.
- Task 12.4 is complete on CI run https://github.com/vchs6/code2semantics/actions/runs/40350126847. Full root tasks 8.1–8.5 remain pending.

Per-profile enablement evidence: checked-in matrix enables only `rust.cargo-metadata` for `source.f4.kind`/`source.f6.kind` and `python.pyproject-toml` for `source.f3.runtime`/`source.f6.kind`, each with parser and CLI-level source-to-store acceptance references. All remaining research candidates stay disabled. This is profile-level acceptance only, not S1–S12 completion.
