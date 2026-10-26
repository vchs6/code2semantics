# Tasks

## 1. Contract and adapter
- [ ] 1.1 Add RED tests for provider registration, protocol version, JSON stdin/stdout, invalid configuration and provider identity mismatch.
- [ ] 1.2 Implement a host-owned provider registry with fixed argv prefixes, timeout and output-size bounds; never read executable commands from requests or the capability matrix.
- [ ] 1.3 Implement invocation result types for accepted proposal, timeout, process failure, malformed output and source-state change.
- [ ] 1.4 Route candidate batches exclusively through `validate_induction_result`; no direct repository writes from the provider adapter.

## 2. Failure and evidence validation
- [ ] 2.1 Test absent provider, missing executable, timeout, nonzero exit, malformed JSON and output-size overflow; assert empty accepted facts and explicit gaps.
- [ ] 2.2 Test a valid but ungrounded proposal, wrong subject, stale source state, unrequested field and evidence not present in request observations; assert rejection.
- [ ] 2.3 Test existing-fact conflict and verify existing facts remain unchanged.
- [ ] 2.4 Test source mutation during provider execution; discard all proposal output from the stale snapshot.

## 3. Runtime integration
- [ ] 3.1 Add provider injection to constructor/query orchestration without changing pure query projection or repository responsibilities.
- [ ] 3.2 Add an executable protocol fixture to test real process boundaries and bounded output.
- [ ] 3.3 Run all component suites and strict OpenSpec; record protocol-only evidence separately from real inference acceptance.
- [ ] 3.4 Configure an actual inference provider and execute S1–S12 real-source scenarios. Keep provider and product gates blocked until this passes.
