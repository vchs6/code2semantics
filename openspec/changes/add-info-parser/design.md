# Design: Python + Rust information parser

## Public boundary

The parser consumes only a public `ParseRequest` (`tool_native_output.text` plus an `invocation_profile`) and returns a public `ParseResult`. It does not open project files, execute tools, access SQLite, construct FactBatch records, select tools, or mutate the capability matrix.

## First-phase profiles

- `python.ast-source`: Python standard-library AST. Emits a module/file subject and observations for class, function/async-function and import declarations. Syntax errors return an explicit `unparseable` gap.
- `rust.syntax-source`: deterministic Rust declaration inventory. Emits module, function, struct, enum, trait, impl, type, const/static and use declarations. Delimiter mismatches return explicit `unparseable` gaps.
- Both profiles bind observations to a stable file subject node, retain line-range/source locators, source content state and SHA-256 digest, and sort output deterministically.
- Both are intentionally syntax inventory only. Rust parsing is not rustc/rust-analyzer, type checking, macro expansion, borrow checking or runtime analysis.

## Registration and acceptance

`ParserRegistry` is the only registration/discovery/call boundary. Unsupported tool IDs return a public `unsupported_profile` gap. The accepted parser profiles are recorded in `assets/capability-matrix.json` only after tests cover the exact output profile and evidence behavior.

## Validation

Input and output are validated against the current `pipeline.schema.json` and shared schema registry. Missing required source context, malformed output and unsupported profiles fail explicitly. The registry has no runtime write access to the matrix or repository.
