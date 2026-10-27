# Validation: Independent project-analysis Skill survey

## Scope

This change researches independent project-analysis Skills only. Generic AI agents, models, hosts and agent platforms are excluded from candidate research. The selected Skill's host is a runtime prerequisite for fallback, not a separately evaluated candidate.

The survey is language-neutral. Python/Rust describe the current product implementation phase, not candidate admission or the final mixed-language goal.

## Document review evidence (2026-10-27)

Directly inspected public Skill definitions:
- `codebase-analysis`: https://github.com/JakubMikolajek/codex-skills-collection/blob/main/skills/codebase-analysis/SKILL.md
- `codebase-summary`: https://github.com/smyrick/skills/blob/main/skills/codebase-summary/SKILL.md
- `explaining-codebases`: https://github.com/analyticalmonk/explain-this/blob/main/skills/explaining-codebases/SKILL.md
- `improve-codebase-architecture`: https://github.com/jae-labs/skills/blob/main/skills/improve-codebase-architecture/SKILL.md
- `understand` from Understand Anything: https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/SKILL.md

Candidate mapping, documented language support, known dependencies and limitations are in `research/semantic-tooling-survey.md` §8.

## Current result

- Candidate discovery and source-document review: complete.
- Initial per-need coverage mapping: complete as a document-only hypothesis, not an acceptance result.
- Priority candidate: Understand Anything `understand`, because the Skill document specifies a structured `.ua/knowledge-graph.json`, typed nodes/edges, multiple language adapters and explicit unknown handling for unsupported parsing/deletion cases.
- Comparison candidates: `codebase-analysis`, `codebase-summary`; conditional candidate `explaining-codebases` depends on `creating-explainers`; specialized architecture candidate `improve-codebase-architecture`.
- Runtime installation/invocation, mixed-language fixture, security/execution review, source evidence validation and conversion to this project's FactBatch contract: NOT RUN / PENDING.

## Runtime blocker and acceptance plan

The current session has repository read/write and GitHub CI access, but no authorized invocation of the candidate Skill's host. Therefore no claim is made that a Skill was installed, executed or validated. Do not infer runtime support from a public `SKILL.md`.

When an approved host is available, execute the candidate against a temporary authorized mixed-language project containing at least two languages, separate build manifests, one evidenced cross-language interface (FFI/RPC/schema), one declared dependency without demonstrated runtime interaction, and one unresolved behavior. Capture candidate revision, invocation, exact root/exclusions, raw output and intermediate graph; verify source locators, source identity, content state, relationship type, direct observation versus inference, unknown handling, scope boundaries, filesystem writes, network/data egress and project-code execution. Compare each result with the fixed `information-needs.json` catalogue. Keep tasks 4.4–4.6 and 5.3–5.4 pending until these tests actually run.

No capability-matrix entry was enabled. Research is not runtime integration. The product delivery gate remains blocked by the separate full S1–S12 acceptance requirement.

## CI validation evidence

- Strict OpenSpec validation passed in CI run https://github.com/vchs6/code2semantics/actions/runs/40438471133 for commit `5275a54ae3c37ae611976f37f8362c5b48931deb`.
- The product-delivery job remains intentionally blocked: the full S1–S12 acceptance success marker is absent. This is not a Skill survey failure and must not be bypassed by adding a marker.
- Component regressions in this run passed: repository 63, transaction 6, transfer 8, repository acceptance 5, capability matrix 15, parser 14, scanner 9, runtime acceptance 27, packaging 2, tool executor 3, producer dispatch 3, constructor/induction/provider/query 86, quality-gate unit tests 2.
- This CI validates repository contracts and regression suites; it does not install or execute an independent project-analysis Skill. Candidate runtime/mixed-language tests remain pending.
## Token-efficiency priority update (2026-10-27)

- User direction: prefer tool-driven independent project-analysis Skills with structured/queryable output to minimize token use.
- Experiment order is now CodeGraph Explorer → Understand Anything → Graphify → prose-oriented comparison candidates. This is an evaluation order, not an approved production selection.
- Measurement protocol records one-time build cost, per-query cost, amortized build + 1/10/50 queries, source fallback overhead and output quality. Public zero-token claims remain unverified until measured in an approved host.
- CodeGraph Explorer's Skill document says local script builds `.codegraph/graph.json` and directs the model to query scoped graph commands rather than parse source with LLM tokens. It also documents uneven language extraction, with several languages remaining regex-based. This makes it a high-priority candidate but not a presumed winner.
- Understand Anything and Graphify also provide structured graph artifacts; Graphify's code-only local AST path should be measured separately from optional semantic extraction over docs/media. Graph structure/token economy never overrides source evidence and false-edge validation.
- No candidate has been executed in an approved host in this session. Runtime token/quality results remain pending.