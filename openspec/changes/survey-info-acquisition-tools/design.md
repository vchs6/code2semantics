# Design: Information-acquisition producers and independent project-analysis Skills

## Scope and authority

This change researches producers against the fixed development-time catalogue at `skills/layered-semantic-facts/assets/information-needs.json`. The catalogue is the information-demand authority; the existing parser/tool matrix and the languages currently implemented by the product must not constrain discovery of independent project-analysis Skills.

The current product implementation has a first-phase Python/Rust syntax-inventory scope. This is not the Skill survey's admission rule or the final product's language boundary. The final goal includes mixed-language projects, their independent project boundaries, build ecosystems, cross-language interfaces/interactions, and source-qualified evidence.

This change is a development-time research and acceptance artifact. It does not run at query time, install/authorize a Skill, update production facts, or enable capability-matrix entries.

## Producer categories

### A. Deterministic tools and parsers

Continue evaluating tools by concrete need coverage, invocation profile, native output, language/environment, evidence locators, limitations and reproducible probes. Current Python/Rust parser profiles remain limited to their accepted syntax/manifest scope. A tool is not credited with semantic behavior merely because it emits syntax, a manifest, or a graph.

### B. Independent project-analysis Skills

Only evaluate a Skill as a candidate when it has an independent project-analysis task, a real invocation entrypoint, and outputs that can be inspected. Candidate discovery may include public Skill directories and repositories without restricting language support to Python/Rust.

For each Skill record:
- canonical name, repository/source URL, revision/version and license/availability when verifiable;
- actual invocation entrypoint, input/output protocol, required dependencies and host prerequisites;
- declared languages separately from languages actually exercised;
- project-boundary detection, entrypoint/build ecosystem, module responsibility, dependency, interface/call, data/control flow, lifecycle/error, algorithm and evidence capabilities;
- source locators and whether claims preserve current content state, scope, coverage, direct observation versus inference, conflicts and unknown;
- security and execution behavior: project code execution, network/data egress, credentials, filesystem writes, allowed scope, timeout/output behavior and failure handling;
- per-need coverage, unique contribution over underlying tools, dependencies on other Skills, and unsupported cases.

Exclude general-purpose agent hosts/model services, prompt-only role descriptions, formatting-only Skills, and thin wrappers without an independently verifiable analysis contribution. If a candidate orchestrates tools, record both the underlying tool outputs and its additional analysis; do not double-count the same coverage.

### C. AI fallback boundary (not a survey target)

The AI fallback uses the selected project-analysis Skill's existing host. This survey does not compare or select agent hosts, models, or agent platforms. Host availability is recorded only as a prerequisite to an executable Skill test. When tool and Skill results do not satisfy a need, the AI fallback may reason only from the evidence already available and must label inference, assumptions and unresolved gaps; it must not fabricate source evidence or claim unseen runtime behavior.

## Mixed-language evaluation

Single-language tests do not establish mixed-language support. A candidate's mixed-language claim requires one authorized project fixture containing at least two languages and a real cross-language boundary (for example FFI, RPC, generated binding or shared schema), plus separate project/build metadata and a decoy declared dependency that has no demonstrated runtime call.

Check whether the Skill:
1. recognizes the languages and build ecosystems actually present;
2. preserves distinct project/source identities across nested or overlapping roots;
3. connects cross-language endpoints only when evidence supports the relationship;
4. distinguishes declared dependencies from source-level/observed interaction;
5. returns traceable evidence per language and per relationship;
6. keeps unsupported constructs, missing evidence and out-of-scope targets explicitly unknown;
7. avoids modifying source files or executing project code without explicit authorization.

For each test, retain the candidate revision, invocation details, exact authorized root/exclusions, raw output, intermediate artifacts where available, source locators, errors and a need-by-need evaluation. Mark document-only claims as unverified. If no approved host is available to run a Skill, record the execution blocker and leave runtime acceptance pending.

## Selection and hand-off

The research report may recommend candidates and combinations but does not make runtime selections. The constructor remains responsible for choosing eligible producers against the fixed needs catalogue; parsers own deterministic conversion to the public observation contract; induction validates evidence-bound semantic proposals. A Skill's knowledge graph or prose summary is not a FactBatch until an explicit adapter validates identity, scope, evidence, content state, coverage and conflict semantics.

No research result alone enables a capability-matrix entry. Any runtime Skill adapter/dispatch requires a separate implementation and acceptance task after this survey identifies a candidate with sufficient evidence.

## Current candidate status

- `understand` from Understand Anything: priority test candidate based on documented knowledge-graph output, multi-language structural adapters and explicit unknown handling. Mixed-language runtime behavior is not yet tested in this project.
- `codebase-analysis`: broad repository walkthrough candidate; machine-readable evidence contract and cross-language edges are not documented.
- `codebase-summary`: evidence-led architecture summary candidate; its prose/HTML output must be checked for field-level traceability and machine conversion.
- `explaining-codebases`: conditional candidate because it explicitly depends on another Skill for artifact production.
- `improve-codebase-architecture`: lower-priority candidate for responsibility/architecture interpretation, not a complete semantic inventory.

These are research candidates only, not installed, authorized, accepted or enabled runtime producers.

## Token-efficient candidate selection

The survey prioritizes Skills that execute deterministic local tools/scripts to produce structured, queryable artifacts, then ask the model to inspect only small relevant subgraphs/results. Do not prioritize a Skill merely because it generates a rich graph: its build path and query path must be examined separately.

Measure token cost by phase:
- graph/index construction: model input/output tokens, including any semantic pass;
- Skill instruction and orchestration overhead;
- per-question query: tokens needed to retrieve/interpret a scoped result;
- fallback: additional tokens spent reading source files or reasoning because the graph is incomplete.

Prefer code-analysis paths with zero or near-zero LLM token use where verified, but also evaluate accuracy, cross-language coverage, evidence traceability and missing/unknown behavior. A zero-token regex graph with weak edges must not outrank a more accurate candidate solely on cost. Token claims must be supported by run logs or explicit instrumentation; vendor/project claims alone remain unverified.

Initial priority order for experiments:
1. **CodeGraph Explorer** (`GoldDHacker/codegraph-explorer-skill`): local Python script builds `.codegraph/graph.json`; its Skill instructions explicitly direct the model to query the graph instead of parsing source with LLM tokens. The inspected document describes small structured queries and zero-token graph construction. Important caveat: much of C/C++/Go/Rust/Ruby/PHP/Swift/Kotlin extraction is regex-based; tree-sitter support is documented for JS/TS/Java and selected extended languages. Cross-language completeness is not established.
2. **Understand Anything** (`Egonex-AI/Understand-Anything`): structured `.ua/knowledge-graph.json`, typed nodes/edges, broad multi-language adapter claims and explicit unknown handling. The skill can invoke an LLM graph review and includes multi-phase graph generation; actual token cost must be measured and the deterministic/LLM phases separated.
3. **Graphify** (`Graphify-Labs/graphify` / `darce07/graphify-claude-skill`): structured graph JSON and broad tree-sitter language coverage; code-only extraction is documented as local/LLM-free, while semantic extraction for docs/media can use an LLM. Evaluate only code analysis first, disable optional semantic passes where possible, and measure actual model usage.
4. **codebase-summary** and **codebase-analysis**: retain as lower-priority comparison candidates because their principal outputs are prose-oriented or their machine-readable evidence contract is less explicit.

These ranks are experiment order only. Do not enable or integrate a candidate until mixed-language fixtures, source evidence, security and token measurements pass.
