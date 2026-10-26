# Tasks

## 1. Align research with the fixed Python/Rust needs catalogue

- [x] 1.1 Read `add-semantic-fact-constructor/design.md` and `assets/information-needs.json`; use only the four fixed F2 syntax-inventory needs as the current survey input.
- [x] 1.2 Record Python AST, Python compileall, Rust declaration parser, cargo metadata, rustc/cargo check and rust-analyzer candidates with exact coverage boundaries and limitations in `research/semantic-tooling-survey.md`.
- [x] 1.3 Separate built-in parser capabilities from executable acquisition tools; do not claim the parser itself reads project files or do matrix writes from this research change.
- [x] 1.4 Record environment availability as unverified unless a CI or runtime probe actually ran; do not infer installed rustc/cargo/rust-analyzer from ecosystem documentation.

## 2. Acceptance evidence for current first-phase parser profiles

- [x] 2.1 Add or reference deterministic Python and Rust parser fixtures with source evidence and content digests.
- [x] 2.2 Record focused test commands and successful CI links for the parser and mixed-language scanner; explicitly state that syntax inventory is not semantic/type analysis.
- [x] 2.3 Confirm no capability-matrix entry is enabled solely from survey findings; enabling requires a separate parser-development acceptance action.
- [x] 2.4 Strict-validate `survey-info-acquisition-tools` and update the main traceability record with the survey artifact path and limitations.


## Evidence update (2026-10-26)

- Survey updated at `research/semantic-tooling-survey.md`; external toolchain availability remains explicitly unverified and no matrix entries were enabled.
- Parser/scanner/acceptance tests passed in CI run `https://github.com/vchs6/code2semantics/actions/runs/40261330788`; strict OpenSpec passed.
- Scope is F2/L3 syntax inventory only. Semantic/type analysis and external tool execution are pending later component tasks.
