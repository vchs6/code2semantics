# Design: Python + Rust information-acquisition tool survey

## Scope

This change extends the prior Rust-focused survey to the first-phase Python + Rust source-inventory catalogue delivered by `add-semantic-fact-constructor`. It is a development-time research and acceptance artifact; it does not execute tools at runtime or enable capability-matrix entries by itself.

## Candidate producers

### Python
- Python standard-library `ast`: deterministic syntax tree over supplied Python source text; no external process required for parsing.
- `python -m compileall`: syntax/bytecode compilation signal only; must be run with explicit root and excluded generated paths; does not prove runtime behavior.
- `pyproject.toml`, `setup.cfg`, `requirements*.txt`, package metadata: manifest/configuration evidence; not part of the initial F2-only catalogue unless a later OpenSpec change expands needs.

### Rust
- Deterministic declaration parser in `semantic_facts.info_parser`: parses source text already acquired by the caller; declaration inventory plus delimiter diagnostics only.
- `cargo metadata --no-deps --format-version 1`: candidate for workspace/member/target/dependency needs, but those needs are not in the initial F2 catalogue.
- `cargo check` / `rustc`: compiler/type-check signals, only when installed and when a project explicitly opts into tool execution; not required for the current syntax-only need.
- `rust-analyzer`: candidate for semantic symbols/references/call hierarchy; availability and version must be probed, never assumed.
- `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`: manifest/configuration evidence for future needs.

## Environment policy

Tool availability is environment-specific. A producer is eligible only after the exact invocation profile and native output are tested on supported platforms. No research result alone enables a matrix entry. Matrix entries remain disabled or absent until parser-development acceptance evidence exists.

## Acceptance protocol

For each producer/profile record:
- tool ID/version and exact argv;
- supported language/platform/environment;
- native output fixture and digest;
- covered need IDs and known limitations;
- parser result schema validation and evidence traceability;
- malformed output and missing-tool behavior;
- test command and CI run.

The initial built-in Python and Rust parsers are deterministic in-process converters, not external command executors. The current scanner reads files directly; the constructor's matrix-driven external-tool execution remains a separate implementation task.
