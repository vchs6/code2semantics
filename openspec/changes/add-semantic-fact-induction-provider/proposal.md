# Proposal: Configured Evidence-Bound Induction Provider

## Why

The existing induction component deterministically groups requests and validates proposed FactBatch additions, but deliberately returns `constructor_unavailable` when no provider result is supplied. That is correct fail-closed behavior, but it leaves the production chain without a runtime induction provider and prevents full S1–S12 acceptance.

## What Changes

- Add a provider adapter boundary that consumes an already-validated `InductionRequest` and returns a candidate FactBatch proposal; it does not write to SQLite or construct a public query response.
- Provider commands/configuration are host-owned and explicitly registered. Query data and capability-matrix entries cannot select arbitrary executables, arguments, endpoints or credentials.
- Bound execution by timeout and output size; preserve stdout/stderr status, exit code and provider identity for diagnostics without treating provider claims as evidence.
- Route every proposed result through the existing `validate_induction_result`; accept only requested fields for the exact subject and current source states with evidence IDs present in the induction observations. Conflicts and unproven claims remain explicit gaps.
- Missing configuration, timeout, nonzero exit, malformed JSON, oversized output or stale source state fail closed and produce no inferred facts.
- The provider profile stays disabled until real runtime integration is accepted. Mock/fake-provider tests verify protocol and failure handling only; they do not satisfy S1–S12 product delivery.

## Capabilities

### New Capabilities
- `semantic-fact-induction-provider`: invoke a host-configured inference provider under bounded execution and validate its result through the existing induction contract.

### Modified Capabilities
- `semantic-fact-constructor`: call the provider only after deterministic grouping; never bypass request/evidence validation.

## Dependencies

This change depends on `add-induction-batch-trigger` and the public FactBatch/InductionRequest schemas. The main epic remains blocked until a real configured provider has source-to-store acceptance for S1–S12. No provider brand or endpoint is assumed by this proposal.
