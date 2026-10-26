# First-phase information-needs catalogue

This is a fixed development-time catalogue. Runtime constructor planning may read it but MUST NOT add or edit needs.

## Supported fields

| Need ID | Fact/field | Producer | Acceptance |
|---|---|---|---|
| `syntax.f2.identity` | F2.identity | Python AST / Rust declaration parser | Stable source-file node reference |
| `syntax.f2.names` | F2.names | Python AST / Rust declaration parser | Supported module/type/function/import declarations with source evidence |
| `syntax.f2.boundary` | F2.boundary | Deterministic constructor | Explicit syntax-only boundary and language limitations |
| `syntax.f2.locators` | F2.locators | Python AST / Rust declaration parser | Source-relative line locator, source ID and content digest |

Each need declares its languages, evidence kind, current-source requirement, coverage requirement, acceptance fixture, production mode, and research basis in `assets/information-needs.json`.

## Deliberate limits

- Python: module, class, function/async-function, and import declarations.
- Rust: module, function, struct, enum, trait, impl, type, const/static, and use declarations, with delimiter diagnostics.
- Neither parser proves runtime behavior. The Rust parser does not perform type checking, macro expansion, borrow checking, or compiler diagnostics.
- F1/F3–F18 fields, control/data flow, call graph semantics, dependency-aware invalidation and cognitive summaries are not in this initial catalogue. They must remain explicit gaps until a development-time OpenSpec change expands the catalogue and supplies tool/parser research and acceptance tests.
- The catalogue is schema-validated and cross-checked against `fact-catalog.json`; duplicate IDs and fields not declared for their fact type are rejected.
