# Tasks

## 1. Metadata and self-contained layout

- [x] 1.1 Add SKILL.md frontmatter with name, description and compatibility; name matches the skill directory.
- [x] 1.2 Place runtime code under scripts/, data and schemas under assets/, and human-readable references under references/.
- [x] 1.3 Resolve assets relative to installed module paths; do not require the development repository root.
- [ ] 1.4 Run the official skills-ref validator if available; otherwise record a reproducible line-by-line specification checklist.

## 2. Independent install validation

- [ ] 2.1 Add a packaging test that copies only skills/layered-semantic-facts to a temporary directory.
- [ ] 2.2 From the copied directory, run scan-source on a mixed Python/Rust fixture and verify a FactBatch is stored.
- [ ] 2.3 From the copied directory, run query against the copied SQLite repository and validate the output-schema response.
- [ ] 2.4 Verify the package does not access repository-relative tests, OpenSpec files or other development-only paths.

## 3. Evidence and boundaries

- [x] 3.1 Document the supported Python/Rust syntax-only boundary and the non-claims about runtime/type semantics.
- [x] 3.2 Document append-only source snapshots and prohibit deleting facts to simulate restore.
- [ ] 3.3 Record copied-install test output separately from full S1–S12 system acceptance.
- [ ] 3.4 Strict-validate this change and run packaging, parser, constructor, repository and query regression tests.

## Evidence (2026-10-26)

- Existing package entrypoint: skills/layered-semantic-facts/SKILL.md.
- Runtime CLI: semantic_facts.cli with scan-source and query.
- Existing tests prove repository-local Python/Rust scan/query. Independent copied-install validation is not yet implemented.
- Full-system acceptance remains pending in the main change.
