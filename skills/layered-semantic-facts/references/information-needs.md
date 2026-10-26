# Source-project information-needs catalogue

This is a fixed development-time catalogue. Runtime constructor planning may read it but MUST NOT add or edit needs. The catalogue enumerates all 127 fields in F1–F18 and maps each need to relevant scenarios S1–S12. Catalogue coverage means a need has been specified; it does not mean a producer is implemented or accepted.

## Acceptance status

- Four F2/L3 syntax needs are the only initially accepted production slice: identity, names, boundary and locators.
- All other needs are marked `research_required`. They must not be selected as accepted production until the tool survey records evidence, the relevant parser is implemented and tested, and parser-development acceptance enables a matching matrix profile.
- Candidate producer families are research hypotheses, not assertions that a named tool is installed, available or accepted.
- A need may require multiple producers. Membership, physical containment, logical organization and dependency are distinct relation kinds.
- Every assertion must preserve current source state, evidence provenance, coverage/completeness and explicit limitations. Unknown or incomplete coverage is a gap, not a negative fact.

## Information groups

| Fact types | Required information | Example candidate producer families | Scenarios |
|---|---|---|---|
| F1–F3 | Requested scope, roots/exclusions, project identity, role, entrypoints, runtime/deployment and configuration hints | Manifest/config readers, source parsers, documentation extractors | S1, S2, S4, S6, S12 |
| F4–F5 | Workspace membership, physical/logical organization, responsibility and implementation links | Workspace manifest readers, project-boundary detectors, documentation/reference extractors | S2–S5, S7, S8 |
| F6–F8 | Package/build dependencies, import/reference/call edges, interactions and interface contracts | Manifest readers, reference/call analyzers, API/schema readers, runtime trace readers | S2–S7, S9, S10 |
| F9–F11 | Declarations, types, binding resolution, call targets and dispatch | AST parsers, compiler/type-checker outputs, semantic indexes | S1, S6, S7, S9–S12 |
| F12–F16 | Data/control flow, state transitions, guards, error paths, algorithm steps and proof limitations | Control/data-flow analyzers, compiler IR exporters, documentation extractors, constrained inference provider | S1, S5, S9–S11 |
| F17–F18 | Counterevidence, knowledge status, completeness, checked/excluded regions and refinement links | Provenance/coverage validator, accepted producers, constrained inference provider | S3, S6, S7, S8, S10–S12 |

## Per-field contract

Each record in `assets/information-needs.json` includes:

- stable need ID, fact type and field;
- subject/boundary requirement and required evidence kinds;
- context, current-source and coverage/completeness requirements;
- production mode (deterministic, hybrid or cognitive);
- acceptance fixture and research basis;
- expected output kind and candidate producer families;
- supported language set, platform and execution-environment constraints;
- relevant scenario IDs, explicit limitations and acceptance status.

The candidate families identify research directions only. The survey must record actual tool candidates, version/output evidence and environment results before a parser is selected. The parser change must then define pure native-output conversion and pass positive/negative tests. Only after that acceptance may a matching matrix entry be enabled.

## Current production boundary

The only accepted initial slice is F2/L3 syntax inventory from the in-process Python AST and Rust declaration parsers. The current matrix does not prove type checking, dependency resolution, semantic call graphs, data/control flow, state machines, algorithm correctness, or higher-level responsibility inference. The 123 research-required field needs remain explicit gaps until their dependency chain is completed.

## Validation

Run:

```bash
PYTHONPATH=skills/layered-semantic-facts/scripts python -m pytest tests/test_information_needs.py tests/test_constructor_plan.py -q
```

The loader checks the catalogue against `information-needs.schema.json` and `fact-catalog.json`, rejects duplicate need IDs and unsupported fields, and the tests assert that all F1–F18 fields and all S1–S12 scenario identifiers are represented. This validation proves catalogue structure and traceability, not producer availability or semantic production.
