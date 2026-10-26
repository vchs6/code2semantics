---
name: layered-semantic-facts
description: Scan Python source files into a schema-validated semantic fact batch, store it in SQLite, and query stored facts. Use when a user asks for a bounded Python syntax inventory; this implementation does not claim full cross-language semantic inference.
compatibility: Requires Python 3.12+, jsonschema, pytest for tests, and a local writable filesystem for SQLite.
---

# Layered Semantic Facts

## Current executable entrypoint

Install the dependencies from `scripts/requirements.txt`, then set `PYTHONPATH=skills/layered-semantic-facts/scripts`.

Scan Python and Rust source into a FactBatch and persist it:

```bash
python -m semantic_facts.cli scan-source --root /path/to/project --db /path/to/facts.db --output /tmp/fact-batch.json
```

Run a query using a JSON file that follows the public Query contract:

```bash
python -m semantic_facts.cli query --db /path/to/facts.db --query-file /path/to/query.json
```

## What the current scanner observes

- Python: module, class, function/async function, and import declarations.
- Rust: module, function, struct, enum, trait, impl, type, const/static, and use declarations.
- Both languages: file identity and source evidence locators.
- File identity and evidence locators.
- Source-content digests and current-source context.

The Python parser uses Python AST. The Rust parser is a deterministic declaration inventory with delimiter-balance diagnostics; it is not rustc, rust-analyzer, a type checker, or a macro expander. Both parsers are limited to syntax inventory (F2, L3); they do not infer runtime behavior. Other languages are not supported by this first-phase scanner. External tool orchestration, induction, and the full multi-layer constructor/query workflow remain incomplete.

## Evidence and retention

Each emitted field carries source evidence and a content digest. Invalid Python input produces an explicit error rather than guessed facts. Existing fact rows are not replaced by a later write. A changed Python source snapshot receives a new source identity and is appended as a new fact set; current-scope queries select the latest snapshot for that exact root, while older fact rows remain stored. Conflicting fact identities are rejected. Do not delete stored semantic facts to simulate a restore test. Restore tests must use a separate temporary database.

## Validation

Run:

```bash
PYTHONPATH=skills/layered-semantic-facts/scripts python -m pytest tests/test_info_parser.py tests/test_source_scanner.py tests/test_acceptance.py -q
```

A passing component test does not prove full system acceptance. Full acceptance requires the real source → parser/tool orchestration → constructor/induction → FactBatch → SQLite reopen/read → query response flow, with evidence recorded in `references/acceptance-results.md`.
