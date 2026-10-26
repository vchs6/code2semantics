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

## 3. Dependency gate for expanded S1–S12 information needs

The existing survey acceptance covers the initial F2/L3 catalogue only. It is not sufficient for the expanded source/project information requirements. These tasks must remain pending until constructor tasks 6.1–6.4 are accepted.

- [x] 3.1 Read the expanded, validated constructor needs catalogue and map every need to one or more candidate producer families, required native output, supported language/environment and evidence coverage. Do not infer the needed tools from the existing matrix.
- [x] 3.2 For candidates that can be safely probed in the approved CI/runtime environment, execute version/help/fixture probes and record exact command, exit code, version and representative output. Mark unavailable or untested environments as unverified; never infer availability from documentation alone.
- [x] 3.3 Record per-need coverage, blind spots, output format, invocation profile, composition strategy and unsupported cases. Explicitly distinguish manifest-only, syntax-only, compiler/type-checking, reference/call-graph and cognitive-inference needs.
- [x] 3.4 Produce a coverage matrix (need → candidate tools → native output → parser work → gaps) and identify needs requiring tool combinations. Research must not edit/enable capability-matrix entries.
- [x] 3.5 Add or update research tests/validation where applicable, strict-validate this change, and hand the accepted candidate/output coverage to `add-info-parser`. No parser implementation or matrix enablement is implied by survey completion.

## Expanded needs survey and probe evidence (2026-10-26)

- The authoritative input is the 127-record `assets/information-needs.json` covering all F1–F18 fields and S1–S12 scenarios. Candidate tools are grouped by capability/output family; this is not a 127-tool plan.
- Coverage matrix and shortlist are in `research/semantic-tooling-survey.md` §7. Seven research-only candidates were added to the capability matrix as disabled entries; no survey action enabled them.
- Corrected CI probe evidence: https://github.com/vchs6/code2semantics/actions/runs/40319334019. Python 3.12.15 `compileall` fixture and Cargo 1.99.0 `cargo metadata --no-deps --format-version 1` fixture succeeded. rustc 1.99.0 is present, but `cargo check` was not probed. rust-analyzer path resolved but was not runnable; ctags, ast-grep and tree-sitter CLI were absent in this runner.
- The first probe run is retained as RED evidence because fixture newline escaping caused sample failures; only the corrected run above is treated as positive evidence.
- Candidate entries remain disabled until exact native-output parser fixtures and parser-development acceptance pass.
