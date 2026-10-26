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
