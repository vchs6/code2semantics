# Design: Induction batch trigger and merge

## Ownership and dependencies

This component implements only the induction request grouping and result validation/merge boundary declared by `add-induction-batch-trigger/specs/semantic-fact-constructor/spec.md`. It does not implement a cognitive model/provider, tool execution, constructor planning, repository persistence, or final response projection.

## Group key

Group unmet fields by the complete tuple:
- fact_type;
- subject node identity (source_id, subject_id, node_id);
- current source content states (source_id, content_state);
- full public context (source_ids, conditions, environment, language_semantics).

Fields within a group are sorted and handed off together. Missing, unknown, insufficient-evidence and nonempty-insufficient gaps can trigger induction only when current observations provide evidence for the subject. Conflicting knowledge is surfaced and never silently overwritten.

## Request creation

Inputs are parser observations, the existing valid FactBatch, and public unmet gaps. The component matches gaps to observations by source/subject and creates public `induction_request` documents from the pipeline schema. It emits a structured gap when no current evidence exists, the target cannot be bound to a node, or the request is outside the public fact catalogue.

Request IDs are deterministic hashes of the group key and fields. Requests and gaps are stably sorted.

## Result validation

A proposed FactBatch is validated against the public FactBatch schema before field-level checks. Accepted facts must:
- match the exact requested fact type and subject;
- contain only requested fields;
- refer only to source IDs/content states in the request;
- use evidence IDs supplied by the grouped observations;
- preserve the public origin/knowledge/context/coverage/basis/validity envelope.

A proposal conflicting with an existing valid assertion is rejected with an explicit conflict gap. Existing fact rows are never deleted or overwritten. The component returns an `induction_result` with accepted additions and gaps; persistence remains the repository/query orchestrator's responsibility.

## No-model boundary

This implementation defines deterministic grouping and validation only. It does not pretend to perform cognitive inference. A caller must supply a proposed FactBatch from an explicitly configured induction provider; when no proposal is supplied, the result is a structured `constructor_unavailable` gap.
