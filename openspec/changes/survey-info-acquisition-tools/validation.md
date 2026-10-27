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
