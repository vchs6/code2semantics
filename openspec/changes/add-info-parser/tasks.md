# Tasks

## 1. Public contract and registry

- [x] 1.1 Consume the main change's ParseRequest/ParseResult schemas without duplicating public structures.
- [x] 1.2 Implement ParserRegistry registration, discovery and unsupported-profile gap behavior.
- [x] 1.3 Validate requests and results against the public schema registry; reject malformed requests.

## 2. Python and Rust deterministic conversion

- [x] 2.1 Implement Python AST declaration inventory with stable file subject identity, line locators and content digest.
- [x] 2.2 Implement Rust declaration inventory with delimiter diagnostics and explicit syntax-only limitations.
- [x] 2.3 Preserve source evidence from the supplied output; no file reads, tool execution, matrix writes or persistence inside parser.
- [x] 2.4 Keep deterministic ordering and explicit parse gaps; do not infer runtime behavior.

## 3. Tests and acceptance

- [x] 3.1 Test Python and Rust declaration output, determinism, malformed syntax and unsupported profiles.
- [x] 3.2 Test registry discovery, duplicate registration rejection and mixed-language source scanner integration.
- [x] 3.3 Record accepted parser profiles and evidence in the capability matrix only after focused acceptance tests.
- [x] 3.4 Strict-validate the change and run the parser, scanner, constructor and repository regression suites.

## Evidence (2026-10-26)

- Parser tests: `tests/test_info_parser.py` (9 passed in the last confirmed parser suite).
- Mixed language scanner: `tests/test_source_scanner.py` (5 passed).
- Real source acceptance: `tests/test_acceptance.py` (3 passed before induction tests were added).
- Accepted profiles: `assets/capability-matrix.json` entries `python.ast-source` and `rust.syntax-source`, each with `parser_development` acceptance evidence.
- Current CI runs parser, scanner, acceptance, constructor planning and induction tests; full product delivery remains blocked until the entire multi-layer pipeline is complete.

## 4. Dependency gate for researched native tool outputs

The current parser tasks cover only supplied Python/Rust syntax text. Additional parsers must be planned after the constructor's expanded information-needs catalogue and tool survey have been accepted.

- [ ] 4.1 For each researched candidate selected for parser development, record the exact native output format/version and the corresponding information-needs IDs before implementing a parser.
- [ ] 4.2 Add captured or deterministic native-output fixtures for successful, partial, malformed, unsupported-version and missing-evidence cases. Fixtures must retain invocation/source provenance and must not pretend to be runtime output when generated synthetically.
- [ ] 4.3 Implement pure `tool-native-output + invocation-profile → ParseResult` transformations only for accepted formats; do not execute tools, read project files, select producers, write the matrix or infer facts in the parser.
- [ ] 4.4 Run focused parser tests and constructor/producer-dispatch regression. Enable a matrix entry only after parser-development acceptance for the exact tool, output format and invocation profile; record the evidence in the matrix acceptance field.
- [ ] 4.5 Strict-validate this change and record supported needs plus explicit unimplemented gaps. Survey completion alone does not satisfy parser acceptance.

