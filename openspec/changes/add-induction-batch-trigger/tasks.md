# Tasks

## 1. Deterministic grouping

- [x] 1.1 Add RED tests for missing/unknown/insufficient-evidence/nonempty-insufficient gaps, multiple subjects, multiple content states, and context isolation; run `python -m pytest tests/test_induction.py -q`.
- [x] 1.2 Implement `build_induction_requests(observations, existing_valid_facts, unmet, asset_root)` using the public pipeline schema; group fields by fact type + subject + content state + context and sort deterministically.
- [x] 1.3 Preserve complete grouped fields; reject or gap unbound scope targets, unsupported fact types, and unmet fields with no current observation evidence.
- [x] 1.4 Verify repeated identical inputs produce byte-for-byte equal requests and do not mutate matrix, needs catalogue or repository.

## 2. Result validation and merge

- [x] 2.1 Add RED tests for valid result, wrong subject, wrong source state, unrequested field, evidence not in observations, malformed FactBatch, and conflict with existing current facts.
- [x] 2.2 Implement `validate_induction_result(request, proposed_batch, asset_root)`; accept only facts bound to the exact request and current evidence.
- [x] 2.3 Reject conflicting proposals with explicit gap; preserve existing facts and return only accepted additions. Never delete or replace an existing fact/attribute.
- [x] 2.4 When no provider result is supplied, return `constructor_unavailable` gap rather than inventing an assertion.

## 3. Acceptance

- [x] 3.1 Add real observation fixtures from Python and Rust parser tests and verify grouping across both languages.
- [x] 3.2 Run `PYTHONPATH=skills/layered-semantic-facts/scripts python -m pytest tests/test_induction.py -q`.
- [x] 3.3 Run parser, constructor, repository and full CI regression; strict-validate this change.
- [x] 3.4 Record the boundary: batch trigger/validation is implemented, but no cognitive inference provider is claimed unless a configured provider has its own integration evidence.


## Verified implementation evidence (2026-10-26)

- Implementation: `skills/layered-semantic-facts/scripts/semantic_facts/induction.py`.
- Tests: `tests/test_induction.py` (10 cases covering grouping, determinism, no-evidence gaps, no-provider behavior, evidence-bound acceptance, conflict rejection, source-state/context isolation, subject/source/evidence mismatch, eligible gap states, and malformed/unrequested proposals).
- Regression/strict validation: CI run https://github.com/vchs6/code2semantics/actions/runs/40268078346; the combined constructor/induction/query suite is part of the CI gate. The latest complete prior run passed 30 tests in that combined step and strict OpenSpec. The product delivery gate remains intentionally blocked for missing full-system acceptance.
- Scope boundary: deterministic grouping and result validation are implemented; no AI induction provider is claimed. If no provider result is supplied, the component returns `constructor_unavailable` and does not invent facts.
