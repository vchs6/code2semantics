# Tasks

## 1. Align research with the fixed Python/Rust needs catalogue

- [ ] 1.1 Read `add-semantic-fact-constructor/design.md` and `assets/information-needs.json`; use only the four fixed F2 syntax-inventory needs as the current survey input.
- [ ] 1.2 Record Python AST, Python compileall, Rust declaration parser, cargo metadata, rustc/cargo check and rust-analyzer candidates with exact coverage boundaries and limitations in `research/semantic-tooling-survey.md`.
- [ ] 1.3 Separate built-in parser capabilities from executable acquisition tools; do not claim the parser itself reads project files or do matrix writes from this research change.
- [ ] 1.4 Record environment availability as unverified unless a CI or runtime probe actually ran; do not infer installed rustc/cargo/rust-analyzer from ecosystem documentation.

## 2. Acceptance evidence for current first-phase parser profiles

- [ ] 2.1 Add or reference deterministic Python and Rust parser fixtures with source evidence and content digests.
- [ ] 2.2 Record focused test commands and successful CI links for the parser and mixed-language scanner; explicitly state that syntax inventory is not semantic/type analysis.
- [ ] 2.3 Confirm no capability-matrix entry is enabled solely from survey findings; enabling requires a separate parser-development acceptance action.
- [ ] 2.4 Strict-validate `survey-info-acquisition-tools` and update the main traceability record with the survey artifact path and limitations.
