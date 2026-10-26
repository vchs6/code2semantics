# Tasks

## 1. Deterministic grouping

- [ ] 1.1 Add RED tests for missing/unknown/insufficient-evidence/nonempty-insufficient gaps, multiple subjects, multiple content states, and context isolation; run `python -m pytest tests/test_induction.py -q`.
- [ ] 1.2 Implement `build_induction_requests(observations, existing_valid_facts, unmet, asset_root)` using the public pipeline schema; group fields by fact type + subject + content state + context and sort deterministically.
- [ ] 1.3 Preserve complete grouped fields; reject or gap unbound scope targets, unsupported fact types, and unmet fields with no current observation evidence.
- [ ] 1.4 Verify repeated identical inputs produce byte-for-byte equal requests and do not mutate matrix, needs catalogue or repository.

## 2. Result validation and merge

- [ ] 2.1 Add RED tests for valid result, wrong subject, wrong source state, unrequested field, evidence not in observations, malformed FactBatch, and conflict with existing current facts.
- [ ] 2.2 Implement `validate_induction_result(request, proposed_batch, asset_root)`; accept only facts bound to the exact request and current evidence.
- [ ] 2.3 Reject conflicting proposals with explicit gap; preserve existing facts and return only accepted additions. Never delete or replace an existing fact/attribute.
- [ ] 2.4 When no provider result is supplied, return `constructor_unavailable` gap rather than inventing an assertion.

## 3. Acceptance

- [ ] 3.1 Add real observation fixtures from Python and Rust parser tests and verify grouping across both languages.
- [ ] 3.2 Run `PYTHONPATH=skills/layered-semantic-facts/scripts python -m pytest tests/test_induction.py -q`.
- [ ] 3.3 Run parser, constructor, repository and full CI regression; strict-validate this change.
- [ ] 3.4 Record the boundary: batch trigger/validation is implemented, but no cognitive inference provider is claimed unless a configured provider has its own integration evidence.
