# Tasks

## 1. Contract and adapter
- [x] 1.1 Add RED tests for provider registration, protocol version, JSON stdin/stdout, invalid configuration and provider identity mismatch.
- [x] 1.2 Implement a host-owned provider registry with fixed argv prefixes, timeout and output-size bounds; never read executable commands from requests or the capability matrix.
- [x] 1.3 Implement invocation result types for accepted proposal, timeout, process failure, malformed output and source-state change.
- [x] 1.4 Route candidate batches exclusively through `validate_induction_result`; no direct repository writes from the provider adapter.

## 2. Failure and evidence validation
- [x] 2.1 Test absent provider, timeout, nonzero exit, malformed JSON and output-size overflow; assert empty accepted facts and explicit gaps.
- [x] 2.2 Test a valid but ungrounded proposal, wrong subject, stale source state, unrequested field and evidence not present in request observations; assert rejection.
- [x] 2.3 Test existing-fact conflict and verify existing facts remain unchanged.
- [x] 2.4 Test source mutation during provider execution; discard all proposal output from the stale snapshot.

## 3. Runtime integration
- [x] 3.1 Add provider injection to constructor/query orchestration without changing pure query projection or repository responsibilities.
- [x] 3.2 Add an executable protocol fixture to test real process boundaries and bounded output.
- [x] 3.3 Run all component suites and strict OpenSpec; record protocol-only evidence separately from real inference acceptance.
- [ ] 3.4 Configure an actual inference provider and execute S1–S12 real-source scenarios. Keep provider and product gates blocked until this passes.

## Implementation evidence (2026-10-26)

- Added `semantic_facts.induction_provider.InductionProviderRegistry` and `invoke_induction_provider`. The registry accepts only host-supplied fixed argv prefixes, positive timeout and stdout/stderr byte limits. Requests are schema-validated before process invocation; provider JSON identity/protocol are checked; proposals pass through `validate_induction_result`; failures return empty accepted facts and preserve unmet-field gaps.
- Added `tests/test_induction_provider.py` and wired it into the CI constructor/induction/query suite. GREEN: https://github.com/vchs6/code2semantics/actions/runs/40351619888 — 81 tests passed in the combined suite; strict OpenSpec passed. Full workflow remains blocked only by the root S1–S12 product delivery gate.
- Completed protocol tests cover unknown registration, invalid configuration, valid versioned envelope, timeout, nonzero exit, malformed JSON, output-limit breach, provider identity mismatch, and rejection of untrusted command fields before invocation.
- Remaining: explicit missing-executable and source-mutation acceptance, real provider wiring through constructor/query runtime, evidence-bound nonempty accepted proposal integration, and actual provider-backed S1–S12 acceptance. No real inference provider is configured or claimed.

### Failure-mode and source-state RED/GREEN evidence (2026-10-26)

- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40352261343 — induction provider/constructor/query combined suite 83 passed; repository 63; transaction 6; transfer 8; repository acceptance 5; matrix 15; parser 14; scanner 9; runtime acceptance 20; executor 3; producer dispatch 3; strict OpenSpec passed. Full workflow remains blocked only by the root S1–S12 product delivery gate.
- Added explicit missing-executable coverage and a provider fixture that mutates the source after receiving an induction request. The adapter re-inspects each source after process completion and after timeout; any changed/unavailable source changes status to `source_modified`, discards provider output and returns an empty accepted batch with explicit source_modified gaps.
- Task 2.2–2.3 are enforced through the existing `validate_induction_result` path and its existing evidence/source/subject/field/conflict tests; task 2.4 now has a direct provider process-boundary regression.
- Remaining tasks 2.2/2.3 provider-specific nonempty candidate cases and 3.1–3.4 runtime/provider integration remain pending. No actual cognitive inference provider is configured, so this adapter's protocol tests do not constitute provider-backed S1–S12 acceptance.

### Constructor/query injection and evidence validation (2026-10-26)

- `execute_constructor_request` now accepts an optional `InductionProviderRegistry` plus provider ID. It groups only eligible unmet fields with current observations, invokes the configured provider through `run_induction_requests`, and merges only the `validate_induction_result`-accepted additions. If no provider is configured, eligible grouped requests are passed through the existing no-provider validation path and remain explicit `constructor_unavailable` gaps. No repository writes occur in the provider adapter.
- `execute_query_with_construction` now exposes the same optional provider registry/ID and passes them through to the constructor; the default CLI does not configure a provider, so no arbitrary provider is selected and current behavior remains fail-closed.
- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40352903470 — induction provider/constructor/query suite 84 passed; runtime acceptance 20; repository 63; transaction 6; transfer 8; repository acceptance 5; capability matrix 15; parser 14; scanner 9; executor 3; producer dispatch 3; strict OpenSpec passed. Overall workflow remains blocked only by the full S1–S12 product delivery gate.
- Tasks 3.1–3.3 are complete for the generic adapter/injection boundary. Task 3.4 remains pending: no actual cognitive inference provider is configured, and no provider-backed S1–S12 acceptance is claimed.

## Host configuration and true output-bound evidence (2026-10-26)

- Added `load_induction_provider_from_environment()` for host-owned `SEMANTIC_FACTS_INDUCTION_PROVIDER_ID` and `SEMANTIC_FACTS_INDUCTION_PROVIDER_ARGV_JSON`, with optional timeout/stdout/stderr byte limits. The CLI `query` and `construct` entrypoints load this configuration and pass it to query/constructor orchestration. When unset, no provider is selected and induction remains fail-closed. Partial or malformed configuration is rejected.
- Replaced `subprocess.run(capture_output=True)` with a process boundary that writes output to temporary files, monitors stdout/stderr sizes while the process runs, terminates on byte-limit or timeout breach, and reads at most the configured output limit plus one byte. Request input is also capped at 2 MB. Commands remain fixed host configuration with `shell=False`.
- GREEN CI: https://github.com/vchs6/code2semantics/actions/runs/40354134398 — induction provider/constructor/query suite 86 passed; root/runtime acceptance 21; repository 63; transactions 6; transfer 8; repository acceptance 5; matrix 15; parser 14; scanner 9; executor 3; producer dispatch 3; strict OpenSpec passed. Overall workflow remains blocked only by the full S1–S12 product delivery gate.
- Provider protocol, host config, process bounds, evidence validation and fail-closed behavior are now implemented and tested. Task 3.4 remains pending because no actual cognitive inference provider is configured in the repository/CI environment; no provider-backed S1–S12 acceptance is claimed.
