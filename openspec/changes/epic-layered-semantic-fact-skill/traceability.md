# Traceability

本表追踪当前权威 [proposal.md](proposal.md)、两个 [spec delta](specs/) 与 [design.md](design.md)；既有[研究报告](../survey-semantic-fact-requirements/research/semantic-fact-requirements.md)保持依据，不重做研究。映射是规划和验收义务，不是组件或测试已经存在的声明。本次 apply 已直接替换公共 `assets/`、四份 `references/` 和设计资产校验/样例；任务 2–4 的证据见下表及 validation.md。组件与真实集成仍未交付，不能据契约校验勾选组件任务。

| 需求与保留依据 | 主设计 / 公共任务 | 组件实施归属 | 主集成验收与可检查输出 |
| --- | --- | --- | --- |
| 四层观察、O1–O5 与 F1–F18；报告第3/5/6/7节 | D1；tasks 2–4 | 所有子组件消费同源定义 | 主设计资产校验逐阶段替换，不等待子query运行时；新目录/查询/响应及中间契约正反样例；所有定义与消费者直接统一替换，无旧协议兼容 |
| 契约驱动查询、当前项目集合；R1/R2/S1/S4/S8 | D2/D6；3.1、7.1 | add-semantic-fact-query、repository | 当前查询、修改/删除/未提交内容不旧命中；仅请求及必要关联重构，无历史/快照/revision/refresh |
| 主体边界：多独立项目/多工作空间/混合目录/同名/嵌套重叠；成员≠依赖；R1–R6/S1/S8/S9 | D2/D3/D8；8.1–8.2 | constructor、repository、query | 独立主体和关系证据，范围外仅引用不扩读取授权，多父不强制唯一树 |
| 最小直接下级、必要上级与完整直接节点；R2/R3/R4/R16/第5节 | D3/D6；3.1、4.1、6.2、7.1 | constructor、query | 合法边界全部直接节点识别；未确认完整性→gap；必要上级推进算进展；请求节点及直接节点最小字段，不预建全部child完整事实或递归后代 |
| 组织组成与有类型交互；R3/R5/R6/F4/F6/F7 | D2/D8；8.1 | constructor、induction、query | 跨项目/工作空间与范围外关系分开；关系方向/角色/条件/上下文和证据齐全 |
| 有效环与互斥候选环；R6/报告第5节/S9 | D3/D8；8.1–8.2 | constructor、induction、query | 回边保留；共同条件成立且有执行证据才称实际循环，互斥候选不误判，不递归组织为树 |
| 整体用途到内部算法、语言行为保真；R4/R6–R14/F1–F16/F18/S6/S10/S11 | D5/D8；8.1 | parser、induction、constructor | 真实证据支撑控制、数据更新、边界与异常、论证和未证实项；统一结构保留语言语义差异 |
| origin/knowledge 正交、限定否定、context/coverage/basis；R15/R16/F17/S11/S12 | D5/D8；3–4、8.1 | induction、repository、query | 缺少/unknown/证据不足/非空不足分辨，冲突保留；空值≠不存在，最小响应保留限定证据和前提引用 |
| 工具需求驱动研究与组合选择 | D4/D7；5.0–5.1 | survey-info-acquisition-tools | 开发期构造器子提案/设计/任务首阶段先交付固定信息需求清单，不等待工具；新增需求通过开发期提案启动研究与解析器验收，非查询运行步骤；既有 semantic-tooling-survey.md 按该清单新增需求增量复核；输出种类/覆盖/限制/语言/平台环境/调用/组合齐全，先覆盖环境后轻量简洁多语言 |
| 空矩阵与经接入验收点亮 | D4；3.2、5.2–5.3 | capability-matrix、info-parser 开发流程 | 初始空，研究补说明不点亮；解析开发验收完成受控点亮→工具可供构造器使用，不设 production_status/actual_production/execution_validation，执行器管理调用状态 |
| 解析纯转换边界 | D4；3.2、5.3 | add-info-parser | 仅 tool-native-output+invocation-profile→统一来源信息；证据从输入携带，不执行/读源项目/读事实仓库/选工具/归纳/维护矩阵 |
| 归纳未满足触发与分组 | D5；3.2、6.1 | add-induction-batch-trigger | 缺少/unknown/证据不足/非空不足触发；事实类型+主体+当前来源内容状态+上下文分组，保留证据冲突缺口 |
| 构造职责 | D3/D4/D5；6.2 | add-semantic-fact-constructor | 请求/既有有效事实/未满足项/当前来源上下文输入；运行期仅消费开发期既定清单匹配请求/未满足项并聚合当前计划，组合已点亮工具执行解析归纳，返回事实；不生成/扩展清单，不启动研究/开发/点亮，未覆盖gap待开发变更，不持久化/组装Response |
| 结构化事实仓库、有效性、前提闭包 | D2/D5；6.3 | add-semantic-fact-repository | 非空事实/证据关联/有效性持久化，SQLite重开重读、事务拒绝/回滚；不存最终Response，不承诺旧历史可读 |
| 查询循环、无进展和预算 | D6；7.1、8.2–8.3 | add-semantic-fact-query | 比对→构造→校验入库→重读→最小响应；目标与必要前置义务有界进展，无关/重复不算；三终止条件均保留有效事实和gap |
| 对话同契约、默认机器结果、明确请求报告与规范包装 | D7/D8；7.2 | define-skill-packaging | 默认范围标注、模糊意图澄清、同源Response报告；仓库外安装及 skills-ref validate 或规范逐项检查 |
| 真实集成与子交付非重复拥有 | D7/D8；5–8 | 八子变更局部实施，主编排接收 | 触发/推进子apply→交付→接收；S1–S12+新边界真实工具非空事实→入库重读→最小响应；接入验收与集成证据分别记录，不变成矩阵两套状态 |

主公开定义交付路径与阶段见 tasks 2–4；八子入口、前置门槛和预期局部输出见 design D7 与 tasks 5–7。此前缺失的 add-semantic-fact-query 与 define-skill-packaging 子 design/tasks 已于 2026-10-26 创建；两者实施与局部验收仍按各自 tasks 保持 pending。主未来集成入口和证据见 tasks 8；任何尚无可执行命令/实物的交付保持 pending。

## 公共机读契约交付（2026-10-25）

| 主任务 / 决定 | 本次实际公共定义与证据 | 下游归属 / 状态 |
| --- | --- | --- |
| 1.2 / D7 | 已复核八子现有 proposal/specs：公共权威只在主 assets，运行期不扩展开发需求清单、研究或点亮；无重复组件实现 | repository 已有 design/tasks，另七子尚缺其 design/tasks；本次不创建或实施 |
| 2.1–2.2 / D1 | fact-catalog.json/schema：F1–F18、L1–L4、O1–O5、逐字段研究 basis、含 validity 的完整 assertion_envelope；研究 LF 指纹一致；无生产状态 | 目录公共交付完成；事实实际生产覆盖待子组件 |
| 3.1 / D2/D3 | common 的 source/subject/node/外部引用、current validity、必要前提、直接节点清单；contract-format 固定当前 scope/target/granularity/selections | constructor/repository/query 按同源定义实施；不接受旧用户版本协议 |
| 3.2 / D4/D5 | pipeline 中 ParseRequest/Result、ConstructRequest/Result、InductionRequest/Result、FactBatch、StoredRecord、ReadResult；needs/matrix Schema | 仅公共数据契约完成；没有实现解析/构造/归纳/仓库组件 |
| 3.3 / D2/D5 | 当前来源修改/删除、非空不足、未知、前提失效、外部引用、纯解析边界的正反样例；来源上下文交叉核对和必要闭包代表性检查 | 实际源码核验、接入权限、数据库事务/重开均待子组件 |
| 4.1–4.2 / D3/D8 | output-schema：最小字段、完整直接身份清单、必要 context/coverage/basis/validity、最小 premise_checks、冲突、内外缺口、终止原因；64 shape + 30 semantic cases | 公共响应资产完成；查询运行时与主集成 tasks 8 保持 pending |

所有 JSON Pointer、字段语义和验证命令见 `skills/layered-semantic-facts/references/runtime-contracts.md`。验证入口为本变更 `validation/validate_contracts.py`，本轮未调用组件运行时。旧定义、旧说明、旧正例和旧校验已直接替换，不留双轨或适配入口；测试只保留旧字段必须拒绝的反例。


## Python + Rust first-phase implementation update (2026-10-26)

- Fixed development-time needs catalogue: `skills/layered-semantic-facts/assets/information-needs.json`; schema adds explicit `languages: [Python, Rust]`; loader validates schema, duplicate IDs and fact-catalogue field membership.
- Constructor planning: `semantic_facts/constructor_plan.py` maps requested F2 fields to the fixed catalogue deterministically, reuses only supported/current/evidence-backed/complete assertions, and reports uncovered fields as gaps. Tests: `tests/test_information_needs.py`, `tests/test_constructor_plan.py`.
- Survey update: `openspec/changes/survey-info-acquisition-tools/research/semantic-tooling-survey.md` now includes Python and Rust candidates, invocation/coverage boundaries and explicit unverified environment assumptions. Existing matrix remains empty; research does not enable tools.
- Constructor child `design.md` and `tasks.md` now exist; catalogue/loader/planning initial tasks are checked based on CI evidence. Survey child `design.md` and `tasks.md` now exist; its external-tool probes and matrix acceptance remain pending.
- CI evidence: https://github.com/vchs6/code2semantics/actions/runs/40261330788 — existing suites and the new information-needs/constructor-plan tests pass, strict OpenSpec passes. The fail-closed product delivery gate remains blocked for the unimplemented full constructor orchestration.
- Current supported behavior remains syntax inventory F2/L3 only. Do not infer F1/F3–F18, type semantics, call/data flow or runtime behavior from this scope.


## Query and packaging planning follow-up (2026-10-26)

- Query child design/tasks: `openspec/changes/add-semantic-fact-query/design.md`, `tasks.md`. Existing query loop and tests are recorded as partial implementation; direct-node completeness, ancestor obligations, multi-project/cycle acceptance and S1–S12 remain pending.
- Packaging child design/tasks: `openspec/changes/define-skill-packaging/design.md`, `tasks.md`. Independent copied-install test `tests/test_packaging.py` is now in CI; it is not a substitute for full main-change acceptance.
- The induction child tasks are checked only for the deterministic batching/validation boundary, not for a cognitive provider. The main full-system tasks remain pending.


## Direct-node completeness and current query boundary (2026-10-26)

- Scope and file direct inventories are now constructed from current Python/Rust source: scope inventory lists supported source-file nodes; file inventory lists parser declaration nodes. Inventory records include current validity, coverage and evidence and are append-only across source versions.
- Query verifies a current complete scope inventory and, for node targets, verifies the target file belongs to the current scope and has its own complete direct inventory. The scope-to-file prerequisite counts as bounded progress; response projection returns only the requested target inventory.
- Evidence: `tests/test_source_scanner.py`, `tests/test_query_orchestration.py`; CI https://github.com/vchs6/code2semantics/actions/runs/40269644416. Component suites and strict OpenSpec pass; product delivery gate remains blocked.
- Boundary: this only implements the first-phase project-scope→source-file→syntax-declaration path. General semantic ancestor chains, multi-project/overlapping roots, dependency graph cycles and S1–S12 remain pending.


## Cross-project Python/Rust acceptance increment (2026-10-26)

- Added a test to `tests/test_acceptance.py` that executes the actual query/construction pipeline over two explicitly requested roots: one Python project and one Rust project, each defining a same-named `Engine`. It verifies distinct source/subject identities, schema-validated current-source facts, requested-field-only projection, and explicit out-of-catalog classification.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40297921776 — repository 53, matrix 15, parser 9, scanner 7, runtime acceptance 5, packaging 2, executor 3, producer dispatch 3, combined information-needs/constructor/induction/query 52 passed; strict OpenSpec passed.
- This is additional root acceptance evidence, not completion of 8.1–8.5. The full S1–S12 matrix and runtime provider/induction path are still not fully covered, so the product delivery gate remains blocked.

## Expanded source-information needs traceability (2026-10-26)

The constructor information-needs catalogue now has one stable need per field in the authoritative F1–F18 fact catalogue: 127 fields across 18 fact types. Each record includes scenario IDs, expected output kind, candidate producer families, evidence kinds, language/platform/environment constraints, current-source and coverage requirements, limitations, fixture, research basis and acceptance status. This is a needs specification, not a claim that the producer exists.

| Fact type | Fields represented | Need ID prefix / existing IDs | S1–S12 scenarios mapped | Status |
|---|---|---|---|---|
| F1 scope | selection, included, excluded, observation, external, limitations | source.f1.* | S1, S2, S4, S6, S12 | research_required |
| F2 identity/boundary | identity, roles, names, boundary, locators | syntax.f2.* for four accepted syntax fields; source.f2.roles | S1, S2, S4, S7, S8, S12 | four initial fields accepted; roles research_required |
| F3 purpose/runtime | purpose, capabilities, entries, runtime, deployment, environment, actors | source.f3.* | S1, S4, S5 | research_required |
| F4 organization | source, target, kind, direction, member_scope, enumeration | source.f4.* | S2, S3, S4, S5, S7, S8 | research_required |
| F5 responsibility | responsibility, bearers, collaboration, boundary, implementations, premises | source.f5.* | S3, S4, S8 | research_required |
| F6 dependency | source, target, kind, direction, scope, necessity, resolution, cycle | source.f6.* | S2, S3, S5, S6, S7, S9, S10, S12 | research_required |
| F7 interaction | participants, kind, payload, trigger, ordering, paths, mode | source.f7.* | S3, S5 | research_required |
| F8 interface contract | owner, capability, inputs, outputs, constraints, visibility, effects, outcomes | source.f8.* | S3, S5, S6 | research_required |
| F9 program elements/types | identity, name, declaration, scope, type, type_relations, visibility, language_semantics | source.f9.* | S1, S7, S11 | research_required |
| F10 binding | site, targets, scope, resolution, target_conditions, completeness | source.f10.* | S7, S9, S10, S12 | research_required |
| F11 call/dispatch | site, source, targets, arguments, dispatch, continuations, mode | source.f11.* | S6, S7, S9, S10 | research_required |
| F12 data flow/effects | source, target, data, operation, path, transformation, aliasing, effects, precision | source.f12.* | S11 | research_required |
| F13 state/lifecycle | owner, before, after, trigger, guard, action, lifetime, composition, cleanup | source.f13.* | S9, S10, S11 | research_required |
| F14 constraints/errors | constraint, scope, error_kind, origin, propagation, handling, after | source.f14.* | S5, S9, S11 | research_required |
| F15 control/computation | owner, operation, inputs, outputs, successors, guards, back_edges, effects | source.f15.* | S1, S9, S11 | research_required |
| F16 algorithm explanation | steps, goal, strategy, invariants, termination, complexity, argument, open_items | source.f16.* | S1, S11 | research_required |
| F17 evidence/knowledge | assertion, counterevidence, process, gaps | source.f17.* | S6, S10, S12 | research_required |
| F18 refinement trace | source, target, kind, direction, participants, covered, uncovered, limitations | source.f18.* | S3, S7, S8, S11 | research_required |

The full per-field mapping is authoritative in `skills/layered-semantic-facts/assets/information-needs.json`. The test `test_information_needs_cover_every_fact_catalogue_field_and_s1_s12` asserts exact F1–F18 field coverage and the presence of all S1–S12 IDs. Candidate producer families are research hypotheses, not enabled matrix entries. Only four F2 syntax needs are marked `accepted_initial_slice`; the remaining 123 needs remain `research_required`.

After focused tests and strict OpenSpec pass, `survey-info-acquisition-tools` must use this catalogue as input and record actual candidate/version/output/environment evidence per need. Parser implementation and matrix enablement follow that research; no stage may be skipped.

## Tool survey and capability-matrix supplementation (2026-10-26)

- Survey input: the expanded 127-field F1–F18 catalogue mapped to S1–S12, not one tool per field. See `survey-info-acquisition-tools/research/semantic-tooling-survey.md` §7.
- Candidate families are grouped into project/workspace metadata, syntax/compile diagnostics, semantic references/call graph, data/control flow, and evidence-bound inference. Six matrix candidate entries were added for `python.compileall`, `rust.cargo-metadata`, `rust.cargo-check`, `rust.rust-analyzer`, `multi.ctags`, and `multi.ast-grep`; all remain `enabled=false` with no acceptance object. The two existing Python/Rust syntax profiles remain the only enabled profiles.
- CI probe run https://github.com/vchs6/code2semantics/actions/runs/40319334019: Ubuntu 24.04 / Python 3.12.15; compileall fixture passed; Cargo 1.99.0 metadata fixture returned valid JSON; rustc 1.99.0 present; rust-analyzer path existed but binary was not runnable; ctags, ast-grep and tree-sitter CLI were absent. These results are specific to the CI runner, not all developer environments.
- Parser development remains the next dependency: capture accepted native output fixtures, implement pure output adapters, test malformed/partial/missing-evidence cases, and enable each profile only after parser-development acceptance. Full S1–S12 and product gate remain pending.
