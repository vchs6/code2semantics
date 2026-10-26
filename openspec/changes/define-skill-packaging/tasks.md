# Tasks

## 1. Metadata and self-contained layout

- [x] 1.1 Add SKILL.md frontmatter with name, description and compatibility; name matches the skill directory.
- [x] 1.2 Place runtime code under scripts/, data and schemas under assets/, and human-readable references under references/.
- [x] 1.3 Resolve assets relative to installed module paths; do not require the development repository root.
- [x] 1.4 Run the official skills-ref validator if available; otherwise record a reproducible line-by-line specification checklist.

## 2. Independent install validation

- [x] 2.1 Add a packaging test that copies only skills/layered-semantic-facts to a temporary directory.
- [x] 2.2 From the copied directory, run scan-source on a mixed Python/Rust fixture and verify a FactBatch is stored.
- [x] 2.3 From the copied directory, run query against the copied SQLite repository and validate the output-schema response.
- [x] 2.4 Verify the package does not access repository-relative tests, OpenSpec files or other development-only paths.

## 3. Evidence and boundaries

- [x] 3.1 Document the supported Python/Rust syntax-only boundary and the non-claims about runtime/type semantics.
- [x] 3.2 Document append-only source snapshots and prohibit deleting facts to simulate restore.
- [x] 3.3 Record copied-install test output separately from full S1–S12 system acceptance.
- [x] 3.4 Strict-validate this change and run packaging, parser, constructor, repository and query regression tests.

## Evidence (2026-10-26)

- Existing package entrypoint: skills/layered-semantic-facts/SKILL.md.
- Runtime CLI: semantic_facts.cli with scan-source and query.
- Existing tests prove repository-local Python/Rust scan/query. Independent copied-install validation is not yet implemented.
- Full-system acceptance remains pending in the main change.


## Verified packaging evidence (2026-10-26)

- Independent copied-install test: `tests/test_packaging.py` copies only the Skill directory, runs Python/Rust scan-source and query from that copy, and validates the public response.
- Metadata/layout fallback checklist: `skills/layered-semantic-facts/references/skill-packaging-validation.md`. The official `skills-ref validate` was not invoked; no official-validator pass is claimed.
- CI run https://github.com/vchs6/code2semantics/actions/runs/40268487627: repository, matrix, parser, scanner, source acceptance, copied packaging, bounded executor, information-needs/constructor/induction/query tests and strict OpenSpec all passed. The fail-closed product gate remains blocked because full S1–S12 acceptance is not yet complete.
