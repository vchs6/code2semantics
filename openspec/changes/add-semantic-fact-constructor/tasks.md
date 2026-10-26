# Tasks

Implementation is TDD: write a failing behavior test (RED), implement the smallest component change, then run focused tests and regression (GREEN). Only this component's code is owned here; public contracts and cross-component response orchestration remain with the main/query changes.

## 1. Information-needs catalogue (first-stage deliverable)

- [ ] 1.1 Create `skills/layered-semantic-facts/assets/information-needs.json` from the current F2 fact-catalogue fields and the fixed Python/Rust first-phase scope; every entry must name required evidence kinds, current-source and coverage requirements, production mode, fixture, and research basis.
- [ ] 1.2 Add positive and negative catalogue validation tests against `assets/information-needs.schema.json`, including duplicate need IDs, empty fields, missing evidence kinds and unsupported fact fields; run `python -m pytest tests/test_information_needs.py -q`.
- [ ] 1.3 Add a deterministic catalogue loader that rejects invalid JSON/schema and duplicate need IDs without mutating the catalogue; run `python -m pytest tests/test_information_needs.py -q`.
- [ ] 1.4 Record the initial catalogue's explicit unsupported scope and evidence provenance in `references/information-needs.md`; do not claim semantic fields not produced by current parsers.

## 2. Deterministic request-to-plan matching

- [ ] 2.1 Add RED tests for partially satisfied F2 requests, unknown needs, empty source scope, stale content state, and repeated identical requests; run `python -m pytest tests/test_constructor_plan.py -q`.
- [ ] 2.2 Implement `plan_constructor_request` to map requested fact types/fields and unmet items to the fixed catalogue; produce stable, sorted plan items and explicit `uncovered_need` gaps.
- [ ] 2.3 Verify non-empty but insufficient values are not considered satisfied unless evidence, validity and coverage meet the request; never mutate the catalogue or matrix at runtime.
- [ ] 2.4 Add matrix selection tests: disabled tools, tools without parser-development acceptance, environment mismatch and partial coverage must not be selected; multi-tool coverage may be combined. Run `python -m pytest tests/test_constructor_plan.py tests/capability_matrix -q`.

## 3. Tool executor boundary and parser integration

- [ ] 3.1 Define an injected executor protocol with bounded timeout, argv-only invocation, captured stdout/stderr/exit code and explicit invocation profile; test that no shell string execution is used.
- [ ] 3.2 Implement a registry-driven execution loop that selects only enabled matching matrix entries, invokes the registered executor, passes output to `ParserRegistry`, and converts unsupported profiles/failures into explicit gaps.
- [ ] 3.3 Add Python and Rust source fixtures for module/symbol inventories and malformed input; verify deterministic evidence locators and content digests.
- [ ] 3.4 Ensure one failed producer does not discard independent valid observations; reject malformed parser results before construction.

## 4. FactBatch construction and evidence discipline

- [ ] 4.1 Reuse the current constructor implementation through a stable interface and add tests for F2 reference identity, names, boundary, locators, evidence, content state, coverage and limitations.
- [ ] 4.2 Add conflict and request-binding checks: do not silently replace existing facts; do not accept observations for another source, subject, content state or out-of-scope target.
- [ ] 4.3 Validate the complete FactBatch against public schemas before returning; on failure return a structured error and no partial batch.
- [ ] 4.4 Verify no repository import/write occurs in the constructor package and no final output-schema response is assembled here.

## 5. Constructor component acceptance

- [ ] 5.1 Add `tests/test_constructor.py` for catalogue → plan → enabled producer → parser → FactBatch, using real Python/Rust source fixtures and no mocked successful parser output.
- [ ] 5.2 Run `PYTHONPATH=skills/layered-semantic-facts/scripts python -m pytest tests/test_information_needs.py tests/test_constructor_plan.py tests/test_constructor.py -q`.
- [ ] 5.3 Run the relevant repository, matrix, parser, scanner and acceptance regression suites; strict-validate this change.
- [ ] 5.4 Update this task list only from observed test evidence and record limitations; no source facts may be deleted by implementation or test.

