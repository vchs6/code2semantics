# semantic-fact-induction-provider Specification

## ADDED Requirements

### Requirement: Host-owned bounded provider invocation

The system SHALL invoke an induction provider only through an explicitly host-registered provider identity with a fixed command, bounded timeout, and output limits. Request data and capability-matrix records SHALL NOT select or override executable commands.

#### Scenario: Unknown provider fails closed

- **WHEN** a request names a provider that is not registered by the host
- **THEN** the adapter rejects the provider identity and accepts no proposed facts

#### Scenario: Provider timeout or malformed output fails closed

- **WHEN** the registered provider times out, exits unsuccessfully, exceeds the configured output limit, or returns malformed protocol data
- **THEN** the adapter returns an explicit gap and an empty accepted fact batch

### Requirement: Validate provider output against the exact induction request

The system SHALL pass every provider proposal through the existing induction-result validator and SHALL accept only requested fields for the exact subject and current source states with evidence identities present in the request observations.

#### Scenario: Ungrounded proposal is rejected

- **WHEN** provider output contains a field whose evidence is absent from the request observations, whose source state is stale, or whose subject/field is not requested
- **THEN** the proposal is rejected or narrowed to valid additions and the unsupported field remains a gap

#### Scenario: Conflicting proposal does not overwrite current facts

- **WHEN** provider output conflicts with an existing current assertion
- **THEN** the existing assertion remains unchanged and the conflict is reported explicitly

### Requirement: Provider protocol success does not imply semantic satisfaction

The system SHALL distinguish successful process execution from successful induction. A valid protocol envelope with no accepted facts SHALL leave unmet fields unresolved and SHALL NOT mark a query satisfied.

#### Scenario: Provider returns no supported additions

- **WHEN** the provider returns a valid empty FactBatch while the request still has unmet fields
- **THEN** the result retains explicit unmet gaps and does not fabricate an assertion
