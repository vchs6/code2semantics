# Design: Skill Packaging

## Ownership

This component owns the installable Skill layout, metadata, relative asset discovery, dependency declaration, and validation from a copied Skill directory. Query, parser, constructor, matrix and repository behavior remain owned by their component modules.

## Package layout

The single install unit is skills/layered-semantic-facts:
- SKILL.md: frontmatter, usage, supported scope, safety/retention constraints and command examples.
- scripts/semantic_facts/: executable components and CLI.
- assets/: the single authoritative schemas, fixed information-needs catalogue and capability matrix.
- references/: human-readable contracts, information-needs and acceptance evidence.
- scripts/requirements.txt: runtime Python dependencies.

All schema and data paths are derived from the installed module's location, not the development repository root. A copied Skill must run without any other repository files.

## Runtime and compatibility

First phase supports Python and Rust syntax inventory only. Python parsing uses the standard-library AST. Rust parsing is a deterministic declaration inventory, not a substitute for rustc/rust-analyzer type checking, macro expansion, borrow checking or runtime semantics. The package does not execute project code. External tool execution, if added later, must use the allowlisted bounded executor and explicit compatibility requirements.

The CLI has two supported operations:
- scan-source: scan Python/Rust files, create a schema-validated FactBatch, and append it to SQLite.
- query: accept the public Query JSON and return the validated minimal response after repository-backed query orchestration.

Old semantic fact rows are immutable. A changed source snapshot is appended under a new source identity; current queries use current source heads. Packaging must not clear databases or silently migrate facts.

## Validation

Validation has separate gates:
1. Metadata/layout check: required frontmatter fields, name matches directory, scripts/assets/references exist, runtime requirements are declared.
2. Copy-install test: copy only the Skill directory into a temporary location, set PYTHONPATH to that copy's scripts, and run scan/query there.
3. Runtime evidence: record source→parse→FactBatch→SQLite→reopen→query. A passing layout check is not full system acceptance.
4. Full-system acceptance remains owned by the main change and requires S1–S12; packaging cannot declare it complete based only on a successful copied CLI smoke test.
