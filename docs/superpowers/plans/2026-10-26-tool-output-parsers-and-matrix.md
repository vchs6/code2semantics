# Tool Output Parsers and Capability Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Apply the accepted tool-survey and parser proposals in dependency order, adding evidence-backed native-output parsers and enabling only profiles that pass parser-development acceptance.

**Architecture:** Keep parser code as pure `tool-native-output + invocation-profile → ParseResult`. Research records candidate versions/output and environment observations; parser tests consume deterministic fixtures; the capability matrix records enabled profiles only after focused acceptance. Constructor dispatch and end-to-end S1–S12 remain downstream gates.

**Tech Stack:** Python 3.12, pytest, JSON Schema Draft 2020-12, GitHub Actions, OpenSpec.

**Spec:** `openspec/changes/add-semantic-fact-constructor/design.md`, `openspec/changes/survey-info-acquisition-tools/design.md`, `openspec/changes/add-info-parser/proposal.md`, `openspec/changes/add-info-parser/tasks.md`, `openspec/changes/add-semantic-capability-matrix/tasks.md`.

## Global Constraints

- Work only on remote `main`; do not create or modify other branches.
- A research candidate is not an accepted producer; keep it disabled until exact parser/invocation acceptance exists.
- Parsers do not execute tools, read project files, write the matrix, construct facts, or access the repository.
- Preserve source identity, content state, output digest, evidence locator, coverage, and explicit limitations.
- Unknown, malformed, partial, unsupported, or missing tool output must produce explicit gaps and never fabricated facts.
- Keep the product delivery gate blocked until actual S1–S12 end-to-end acceptance passes.

## Review Focus

1. Cargo metadata with multiple workspace members, no dependencies, and dependency records must preserve membership and dependency as different relation kinds.
2. Invalid JSON, missing required Cargo metadata keys, and unsupported output versions must return gaps rather than throw or invent values.
3. compileall output is diagnostic evidence only; a successful compile does not prove runtime correctness.
4. Tool paths that exist but cannot execute (rust-analyzer shim) must be recorded as unusable in that CI environment.
5. Disabled matrix entries must never be selected by constructor dispatch, and enabling requires parser-development acceptance evidence.

---

### Task 1: Native Cargo metadata parser

**Files:**
- Modify: `skills/layered-semantic-facts/scripts/semantic_facts/info_parser.py`
- Test: `tests/test_info_parser.py`
- Fixtures: `tests/fixtures/tool-output/cargo-metadata/`

**Interfaces:**
- Consumes: public `ParseRequest`, `invocation_profile.tool_id = rust.cargo-metadata`, UTF-8 JSON stdout.
- Produces: schema-valid `ParseResult` observations with manifest evidence, exact source/content-state binding, stable IDs and explicit unsupported/malformed gaps.

- [x] Add tests for a captured-shape Cargo metadata fixture: package/target/workspace-member records and dependency edges use separate information need IDs.
- [x] Add tests for malformed JSON, missing keys, unsupported metadata version, deterministic output, and evidence digest/locator.
- [x] Run parser tests and observe expected RED.
- [x] Implement a pure JSON-to-observation converter; it must not invoke Cargo or read the manifest.
- [x] Run parser tests to GREEN, then run the full CI suite.

### Task 2: Python compileall diagnostics parser

**Files:**
- Modify: `skills/layered-semantic-facts/scripts/semantic_facts/info_parser.py`
- Test: `tests/test_info_parser.py`
- Fixtures: `tests/fixtures/tool-output/python-compileall/`

**Interfaces:**
- Consumes: public `ParseRequest`, `tool_id = python.compileall`, native diagnostic text and invocation profile.
- Produces: evidence-backed compile diagnostics and explicit success/coverage limitations; no semantic assertions inferred from success.

- [x] Add positive/negative fixtures for compile success, syntax error, missing path and malformed diagnostic output.
- [x] Run parser tests and observe expected RED.
- [x] Implement pure diagnostic conversion preserving source and output digest; do not execute compileall in parser.
- [x] Run focused and full CI tests.

### Task 3: Parser-development acceptance and matrix enablement

**Files:**
- Modify: `skills/layered-semantic-facts/assets/capability-matrix.json`
- Modify: `tests/capability_matrix/test_contract.py`
- Modify: `openspec/changes/add-info-parser/tasks.md`
- Modify: `openspec/changes/add-semantic-capability-matrix/tasks.md`

- [x] Record exact fixture, invocation profile, tested CI run and parser evidence for each accepted profile.
- [ ] Enable only `rust.cargo-metadata` and/or `python.compileall` if all parser acceptance tests pass.
- [ ] Keep cargo-check, rust-analyzer, ctags and ast-grep disabled until their own output adapters and invocation acceptance exist.
- [ ] Verify constructor dispatch rejects every disabled/unaccepted candidate.
- [ ] Run strict OpenSpec and full CI; record the product gate as blocked if S1–S12 remain incomplete.

### Task 4: Survey and traceability hand-off

**Files:**
- Modify: `openspec/changes/survey-info-acquisition-tools/research/semantic-tooling-survey.md`
- Modify: `skills/layered-semantic-facts/references/acceptance-results.md`
- Modify: `openspec/changes/epic-layered-semantic-fact-skill/traceability.md`

- [ ] Record observed native output and exact environment facts from CI, distinguishing a successful probe from parser acceptance.
- [ ] Map enabled profiles to information needs, parser tests, fixture, and coverage limitations.
- [ ] Record remaining gaps and leave root S1–S12 tasks pending.

## Verification

- `PYTHONPATH=skills/layered-semantic-facts/scripts python -m pytest tests/test_info_parser.py tests/test_producer_dispatch.py tests/capability_matrix -q -ra -p no:cacheprovider`
- `python openspec/changes/epic-layered-semantic-fact-skill/validation/validate_contracts.py`
- `openspec validate add-info-parser --strict --no-interactive`
- `openspec validate survey-info-acquisition-tools --strict --no-interactive`
- `openspec validate add-semantic-capability-matrix --strict --no-interactive`
- Full CI must be inspected after every push; the product delivery gate is not expected to pass until root tasks 8.1–8.5 are complete.


## Execution ledger note (2026-10-26)

- Parser adapters were test-first: RED run https://github.com/vchs6/code2semantics/actions/runs/40320249864 failed because the parser functions were absent; GREEN run https://github.com/vchs6/code2semantics/actions/runs/40320586364 reports 12 parser tests passed, 15 capability-matrix tests passed, 57 combined constructor/query tests passed, and strict OpenSpec success.
- Product gate remained BLOCKED, which is expected. No candidate was enabled because constructor planning currently hard-codes `environment="in-process"`; subprocess dispatch/configuration is a downstream dependency and must be completed before matrix enablement.
- No subagent tool is available in this harness; final review must be recorded as self-review if no independent reviewer becomes available.
