# Tasks

## 1. Align research with the fixed Python/Rust needs catalogue

- [x] 1.1 Read `add-semantic-fact-constructor/design.md` and `assets/information-needs.json`; use only the four fixed F2 syntax-inventory needs as the current survey input.
- [x] 1.2 Record Python AST, Python compileall, Rust declaration parser, cargo metadata, rustc/cargo check and rust-analyzer candidates with exact coverage boundaries and limitations in `research/semantic-tooling-survey.md`.
- [x] 1.3 Separate built-in parser capabilities from executable acquisition tools; do not claim the parser itself reads project files or do matrix writes from this research change.
- [x] 1.4 Record environment availability as unverified unless a CI or runtime probe actually ran; do not infer installed rustc/cargo/rust-analyzer from ecosystem documentation.

## 2. Acceptance evidence for current first-phase parser profiles

- [x] 2.1 Add or reference deterministic Python and Rust parser fixtures with source evidence and content digests.
- [x] 2.2 Record focused test commands and successful CI links for the parser and mixed-language scanner; explicitly state that syntax inventory is not semantic/type analysis.
- [x] 2.3 Confirm no capability-matrix entry is enabled solely from survey findings; enabling requires a separate parser-development acceptance action.
- [x] 2.4 Strict-validate `survey-info-acquisition-tools` and update the main traceability record with the survey artifact path and limitations.


## Evidence update (2026-10-26)

- Survey updated at `research/semantic-tooling-survey.md`; external toolchain availability remains explicitly unverified and no matrix entries were enabled.
- Parser/scanner/acceptance tests passed in CI run `https://github.com/vchs6/code2semantics/actions/runs/40261330788`; strict OpenSpec passed.
- Scope is F2/L3 syntax inventory only. Semantic/type analysis and external tool execution are pending later component tasks.

## 3. Dependency gate for expanded S1–S12 information needs

The existing survey acceptance covers the initial F2/L3 catalogue only. It is not sufficient for the expanded source/project information requirements. These tasks must remain pending until constructor tasks 6.1–6.4 are accepted.

- [x] 3.1 Read the expanded, validated constructor needs catalogue and map every need to one or more candidate producer families, required native output, supported language/environment and evidence coverage. Do not infer the needed tools from the existing matrix.
- [x] 3.2 For candidates that can be safely probed in the approved CI/runtime environment, execute version/help/fixture probes and record exact command, exit code, version and representative output. Mark unavailable or untested environments as unverified; never infer availability from documentation alone.
- [x] 3.3 Record per-need coverage, blind spots, output format, invocation profile, composition strategy and unsupported cases. Explicitly distinguish manifest-only, syntax-only, compiler/type-checking, reference/call-graph and cognitive-inference needs.
- [x] 3.4 Produce a coverage matrix (need → candidate tools → native output → parser work → gaps) and identify needs requiring tool combinations. Research must not edit/enable capability-matrix entries.
- [x] 3.5 Add or update research tests/validation where applicable, strict-validate this change, and hand the accepted candidate/output coverage to `add-info-parser`. No parser implementation or matrix enablement is implied by survey completion.

## Expanded needs survey and probe evidence (2026-10-26)

- The authoritative input is the 127-record `assets/information-needs.json` covering all F1–F18 fields and S1–S12 scenarios. Candidate tools are grouped by capability/output family; this is not a 127-tool plan.
- Coverage matrix and shortlist are in `research/semantic-tooling-survey.md` §7. Seven research-only candidates were added to the capability matrix as disabled entries; no survey action enabled them.
- Corrected CI probe evidence: https://github.com/vchs6/code2semantics/actions/runs/40319334019. Python 3.12.15 `compileall` fixture and Cargo 1.99.0 `cargo metadata --no-deps --format-version 1` fixture succeeded. rustc 1.99.0 is present, but `cargo check` was not probed. rust-analyzer path resolved but was not runnable; ctags, ast-grep and tree-sitter CLI were absent in this runner.
- The first probe run is retained as RED evidence because fixture newline escaping caused sample failures; only the corrected run above is treated as positive evidence.
- Candidate entries remain disabled until exact native-output parser fixtures and parser-development acceptance pass.


## Parser handoff evidence (2026-10-26)

- Cargo metadata and compileall native-output formats now have pure parser adapters and focused tests; the adapter tests passed in CI run https://github.com/vchs6/code2semantics/actions/runs/40320586364.
- Probe evidence is still runner-specific: cargo metadata and compileall samples passed on Ubuntu 24.04; rust-analyzer was not runnable; ctags and ast-grep were absent.
- Survey work is complete, but candidates remain disabled because constructor planning does not yet select subprocess profiles. The next dependency is constructor runtime selection and bounded executor wiring; matrix enablement follows that acceptance, not the survey alone.

## 4. 独立项目分析类 Skill 调研（新增范围，宿主不在调研范围）

- [ ] 4.1 以当前有效的 `skills/layered-semantic-facts/assets/information-needs.json` 为唯一需求输入，定义“独立项目分析类 Skill”的纳入/排除标准；不调研通用 AI 代理、模型、代理宿主或运行平台。AI 兜底使用所选 Skill 的既定宿主，该宿主仅作为调用前提记录。
- [ ] 4.2 从 Skill 目录、公开仓库和官方文档发现候选，逐个记录名称、来源、版本/提交、许可/可用性、真实调用入口、输入输出协议、支持语言、分析范围、依赖工具及运行前提。只将具有独立项目分析任务和可验证输出的 Skill 纳入候选；排除普通 prompt、纯措辞包装及无独立增量的薄封装。
- [ ] 4.3 建立逐项需求覆盖矩阵：需求 ID/事实字段 → Skill 能力 → 直接输入材料/工具依赖 → 输出事实类型 → 源码定位/证据质量 → 覆盖完整性 → 限制与未知。明确区分 Skill 自身产出的分析与其调用底层工具的产出，防止重复计算覆盖。
- [ ] 4.4 对可在获准环境安全执行的候选进行真实试验，优先使用临时 Python/Rust 夹具或可授权项目；记录版本、调用入口、输入、输出、退出/失败结果、证据定位和可复现步骤。未实际运行的能力标为“未验证”，不得由 README 或营销描述推断为已完成。
- [ ] 4.5 评估来源访问权限、范围约束、网络/凭据要求、是否执行项目代码、外部数据发送、超时/输出限制和失败模式；不得为了调研自动执行未知项目脚本或授予超出项目授权范围的访问权限。
- [ ] 4.6 将候选 Skill 与已有工具生产者并列比较，标明它具体补足哪些工具缺口、哪些能力仍需 AI 推导、哪些内容即使经 Skill 分析仍不能证实。AI 兜底宿主不做独立市场调研，也不作为第二套候选评分对象。
- [ ] 4.7 更新 `research/semantic-tooling-survey.md` 的独立 Skill 章节、覆盖矩阵和未解决差距；保持调研与运行时集成分离，不修改/点亮能力矩阵，不宣称已接入构造器；运行本变更严格 OpenSpec 校验，并记录真实试验结果和未验证项。

### 本组边界

本组仅研究独立项目分析类 Skill 的候选能力与证据。调研完成不等于 Skill 已安装、已授权、已注册或可在生产构造器中调用；后续须另行设计并验收 Skill 适配/调度接口。AI 代理兜底直接使用该 Skill 的宿主，不在本调研中比较或选择宿主。