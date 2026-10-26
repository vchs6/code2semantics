# Design: Induction Provider Adapter

## Boundary

`build_induction_requests` remains deterministic. A new provider adapter accepts one validated request and returns a candidate batch payload plus execution metadata. The adapter is not trusted: all candidate output passes through `validate_induction_result` before any addition can be persisted.

## Host configuration

- Provider registration is supplied by application configuration, not by a request, repository record or capability-matrix command string.
- Each registration has a stable provider ID, fixed argv prefix, timeout, maximum stdout bytes, maximum stderr bytes, and protocol version.
- Invoke with `shell=False`, explicit working directory, UTF-8 JSON on stdin, no shell interpolation, and a bounded timeout.
- Credentials may only be inherited from explicitly configured host environment; never log credential values.
- Reject unknown provider IDs, empty commands, NUL arguments, invalid timeout/output limits and unexpected protocol versions.

## Response protocol

Input: one JSON `InductionRequest` on stdin.

Output: one JSON object containing `provider_id`, `protocol_version`, and `proposed_batch`. Stderr is diagnostic only. The output is untrusted and is validated against the public batch schema and then against the exact induction request, source states, requested fields, and evidence inventory.

## Failure behavior

Missing registration, executable-not-found, timeout, nonzero exit, invalid UTF-8/JSON, output-limit breach, provider ID mismatch or source mutation returns a structured gap and empty accepted batch. Never fall back to a guessed assertion or mark the query satisfied.

## Testing and acceptance

1. RED tests for absent registration, valid protocol, timeout, nonzero exit, malformed/oversized output, provider identity mismatch and stale source state.
2. Verify valid but ungrounded proposals are rejected by `validate_induction_result`; only request-bound evidence-supported fields survive.
3. Verify conflicts preserve existing facts and are reported.
4. Run actual configured provider against real S1–S12 fixtures before enabling any provider profile. A fake executable is protocol coverage, not product acceptance.
