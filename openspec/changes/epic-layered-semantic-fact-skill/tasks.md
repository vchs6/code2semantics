# Tasks

本清单由定稿 [proposal.md](proposal.md)、[specs](specs/) 与 [design.md](design.md) 的 D1–D8 派生。主变更只拥有总设计、公共契约定义、依赖编排与集成验收；八子变更拥有组件实现和局部测试。本轮只修订规划文档，不执行以下 pending 实施任务。

现有 assets、references 与 validation/ 中包含旧协议，因此旧清单中“资产已生成/校验通过”的勾选不能沿用为最新契约完成。本清单明确将这些义务设为 pending。旧协议无需兼容，后续统一替换定义、样例、接口说明及所有消费者，不建立双轨、兼容入口或旧数据迁移工具；不以清库绕过校验。

## 1. 既有研究依据与主规划基线

- [x] 1.1 核实既有 `../survey-semantic-fact-requirements/research/semantic-fact-requirements.md` 的四层、O1–O5、F1–F18、R1–R16、S1–S12 依据存在；完成依据为该报告及其 `../survey-semantic-fact-requirements/research/validation.md`，不重做研究。
- [x] 1.2 在后续 apply 开始前复核本次主规划和八子 proposal/specs 的同源边界，记录 `traceability.md` 的 requirement→D→子变更→验收映射；核验无历史/用户快照/revision/refresh 功能、无旧协议兼容义务、无重复组件实现，缺失子 design/tasks 保持未交付并转入对应子流程。

## 2. 公共事实目录定义（D1，先于查询契约）

- [x] 2.1 按报告第 3/5/6/7 节直接重写 `skills/layered-semantic-facts/assets/fact-catalog.json` 与 `fact-catalog.schema.json`，保持四层观察与组织职责分离及 F1–F18 依据；同步 `references/fact-catalog.md` 和 `traceability.md`，逐字段核对来源、直接节点完整性与目录内/外边界，不把工具可用性当事实覆盖，删除既有 production_status 等重复生产状态字段。
- [x] 2.2 更新本变更 `validation/schema-cases.json` 与 `semantic-cases.json` 的目录相关正反样例，主变更同步替换本变更 `validation/validate_contracts.py` 中设计资产的 shape/引用/样例检查，先展示旧目录不符合新要求的失败，再验证新目录通过；该校验仅验设计资产，不实现组件运行时校验；记录运行命令和输出到 `validation.md`；不等待查询组件实现，不用旧验证脚本通过替代。

## 3. 公共查询与中间契约定义（D1–D5，依赖第2组）

- [x] 3.1 直接重写 `assets/contract-format.schema.json`、`common.schema.json`、`information-needs.schema.json` 与 `references/contract-format.md`：当前项目集合、固定目标/粒度、主体证据、未满足项、合法边界及必要上级路径；移除用户历史/快照/revision/refresh 字段与分支，逐项核对主 specs 的入口/范围/变化/完整性需求并记录定义差异。
- [x] 3.2 直接重写 `assets/pipeline.schema.json`、`capability-matrix.schema.json` 与 `references/runtime-contracts.md` 的公共边界：原生输出+invocation-profile→ParseResult；ConstructRequest 消费请求/已有有效事实/未满足项/当前上下文，ConstructResult 只返回事实、证据和缺口；归纳按类型+主体+当前内容状态+上下文分组；矩阵初始空且仅解析开发流程完成接入验收可点亮，点亮即可供构造器使用，不设 production_status/actual_production/execution_validation 等重复维度，调用状态由执行器管理。核验旧 `parser(scope, needs)` 和直接构造持久化/response 均无残留。
- [x] 3.3 更新 `validation/query.json`、`parse-result.json`、`construct-request.json`、`construct-result.json`、`induction-request.json`、`stored-record.json`、`read-result.json`、`assertion.json`、`external-reference.json` 及相关正反样例，覆盖未知/非空不足、来源变化/删除、前提失效、未授权外部引用、直接节点完整性与纯解析。同步替换主 `validation/validate_contracts.py` 的设计资产检查并运行，验证 shape、引用及正反样例，不等待子组件运行时接口，保存命令与预期拒绝/接受结果到 `validation.md`；不要求旧数据可读或旧协议适配。

## 4. 公共响应契约定义（D1/D3/D8，依赖第3组）

- [x] 4.1 直接重写 `assets/output-schema.schema.json` 与 `references/output-schema.md`，限定请求节点所需事实及其直接节点的最小投影，保留必要 context/coverage/basis、证据、节点引用、冲突、目录外与目录内缺口和终止原因；以逐条规格对照确认不自动后代展开、不输出全部上级事实。
- [x] 4.2 更新 `validation/response.json` 及响应正反样例，先展示丢失否定限定、混同来源与知识、缺完整性仍充分命中、泄漏非请求字段的失败，再同步替换并运行主 `validation/validate_contracts.py` 的响应设计资产检查，验证正确响应，不等待查询组件；在 `validation.md` 记录可执行命令、结果与尚未覆盖项。现有旧校验代码不得算作此项完成证据。

## 5. 推进工具研究、矩阵与解析子交付（D4/D7）

- [x] 5.0 仅在后续开发期公共目录/契约语义就绪后，先推进 `../add-semantic-fact-constructor/` 子规划及首阶段 apply，由该子产出面向本次未满足事实需求的可检查信息获取需求清单（具体路径、字段与生成/验证命令先在该子 tasks 落盘）；该阶段属于开发期子提案/设计/任务与 apply 交付，不是查询运行步骤，不等待工具、矩阵、解析器或完整构造器实现；交付固定清单，后续新增需求须通过开发期提案启动研究与解析器开发验收。主验收需求与事实目录/字段的映射、来源上下文和覆盖条件，再把此清单作为5.1输入；不得由主代写组件实现。
- [x] 5.1 以5.0构造器首阶段交付的信息获取需求清单为输入，推进 `../survey-info-acquisition-tools/` 的规划补齐与 apply，基于既有 `research/semantic-tooling-survey.md` 增量复核未点亮工具说明，接收输出种类/覆盖/限制/语言/环境/调用/组合证据；验收先覆盖与环境、再轻量简洁多语言偏好，研究不点亮。交付路径与执行命令须先写入其自身 tasks，再推进；主不实施工具研究组件。
- [x] 5.2 触发并推进 `../add-semantic-capability-matrix/` 的规划补齐与 apply，接收空矩阵初始化、工具说明读取和受控点亮状态接口及局部测试记录；验收初始为空、矩阵不生产/调度、研究与构造不可点亮。具体实现和测试路径以该子 tasks 交付为准，在 `traceability.md` 记录接收证据。
- [x] 5.3 在说明与矩阵接口就绪后推进 `../add-info-parser/` 的规划补齐与 apply，接收原生输出+调用描述纯转换及证据保留的实现、正反测试与解析开发完成后的受控点亮记录；验收不执行工具、不读取源项目/事实仓库、不选工具/归纳/维护矩阵，所有证据来自输入，缺失返回 gap，点亮即工具通过接入验收可供构造器使用，集成实证另记但不增加矩阵状态。

## 6. 推进归纳、构造与仓库子交付（D2/D3/D5/D7）

- [x] 6.1 按第3组归纳契约推进 `../add-induction-batch-trigger/` 的规划补齐与 apply，接收未满足触发和字段分组的实现、非空不足/unknown/证据不足/冲突保留测试及接口说明；验收按事实类型+主体+当前来源内容状态+上下文分组，不直接持久化或组装 response。子 tasks 先固定交付路径和命令，主接收证据。
- [x] 6.2 在5.0首阶段需求清单、5.3与6.1完成后推进 `../add-semantic-fact-constructor/` 的规划补齐与 apply，接收仅消费开发期既定清单、匹配请求/未满足项形成当前获取计划、读取已点亮说明并运行时选择组合执行、纯解析接入和归纳返回的实现及局部证据；核验合法观察边界内必要上级路径与完整直接节点识别、不递归构造所有 child 完整事实、不读写事实仓库、不组装最终响应。未点亮/环境不符/清单未覆盖必须 gap，不擅自扩权；核验运行构造器不生成/扩展清单、不触发工具研究/解析器开发/点亮，待开发期变更处理。
- [x] 6.3 按公共事实契约推进 `../add-semantic-fact-repository/` 的规划补齐与 apply，接收 SQLite 结构化事实/证据关联/当前有效性、事务回滚和关闭重开读取实现及测试；核验修改/删除/前提失效不当当前命中、冲突保留、非法数据拒绝且原数据未因测试删除，存储接口不使用最终 response，不要求旧历史或用户版本协议。

## 7. 推进查询与包装子交付（D6/D7）

- [ ] 7.1 在公共契约与6.2/6.3就绪后推进 `../add-semantic-fact-query/` 的规划补齐与 apply，接收公共契约加载/校验、覆盖比对、构造调用、校验入库重读、最小响应与 CLI 实现及测试；验收需求满足/无有效覆盖进展/预算终止，进展包含有界必要上级与直接节点完整性前置义务，不把重复候选、非空或无关事实算进展。以该子 tasks 定义的命令核验，不在主变更重复实现。
- [x] 7.2 在查询入口就绪后推进 `../define-skill-packaging/` 的规划补齐与 apply，接收 `skills/layered-semantic-facts/SKILL.md`、安装说明、依赖、仓库外安装入口、对话与可选报告交付及局部测试；核验 Agent Skills Specification frontmatter/目录/渐进披露、默认机器响应、同一当前契约和明确请求才生成报告。执行 `skills-ref validate` 或规范逐项检查表并记录实际采用方式。

## 8. 主集成验收（D8，依赖全部公共定义与八子交付）

- [ ] 8.1 在 `tests/test_acceptance.py` 与 `tests/fixtures/scenarios/` 建立跨组件集成断言并同步 `traceability.md`，覆盖报告 S1–S12 以及多项目/多工作空间/混合目录/同名嵌套重叠、成员与依赖分离、跨范围不扩权、有效环/互斥候选环、内部算法与语言差异、限定否定、origin/knowledge 独立；先运行 `python -m pytest tests/test_acceptance.py -q` 记录真实失败，再联调已交付子组件并运行通过，不用 mock 或 gap-only 代替真实生产。
- [ ] 8.2 补充运行期仅消费既定清单生成当前计划、未覆盖需求gap且不触发研究/开发/点亮，以及当前来源修改/删除后按需重构、无关事实保持有效、必要上级进展、直接节点完整识别但最小字段投影、多父/循环不递归、未知/非空不足、工具组合及无进展/预算终止的跨组件断言；以同一集成入口运行并在 `validation.md` 记录实际结果和未满足项，未经验证保持 pending。
- [ ] 8.3 从干净临时事实仓库和仓库外安装目录运行真实工具→解析→归纳→非空 FactBatch→SQLite 入库→关闭重开→重读→最小查询；保存真实来源、工具环境/调用、证据关联、当前有效性及最小字段结果到 `skills/layered-semantic-facts/references/acceptance-results.md`，分别记录工具接入验收与真实集成证据，不在矩阵另设生产状态。
- [ ] 8.4 在第2–4组已逐阶段替换并运行的设计资产校验基础上，扩展本变更 `validation/validate_contracts.py` 以验证与子组件最新同源运行时接口的一致性并运行 `python openspec/changes/epic-layered-semantic-fact-skill/validation/validate_contracts.py`；此时接入已交付组件公共校验能力核对设计资产检查与运行时结果，核验全部最新正反样例及引用一致性，失败保留并纠偏，不兼容旧协议。同步 `validation.md` 区分规划校验、契约校验和端到端证据。
- [ ] 8.5 运行 `openspec validate epic-layered-semantic-fact-skill --strict`、八子相应严格校验及各子已约定测试命令，按 `traceability.md` 逐条接收 requirement→公共定义→组件→集成证据；仅全部实证和规范验收通过后标记交付完成，任何缺项保留 pending 并报告，不缩减范围或由规划状态代替实现。

## Workflow follow-up

- 本轮仅修订文档并执行 OpenSpec 文档校验；后续实施由 apply 推进，先测试后实现。
- 缺失子 design/tasks 应进入对应子规划流程创建；本次更新不创建这些缺失工件。
- 本轮不归档；归档和发布应在实际交付及用户授权条件满足后处理。

## First-phase Python + Rust progress evidence (2026-10-26)

- 5.0 fixed needs catalogue and constructor child planning delivered: `skills/layered-semantic-facts/assets/information-needs.json`, `add-semantic-fact-constructor/design.md`, `tasks.md`.
- 5.1 survey expanded for Python and Rust with exact current parser boundaries and unverified external toolchain availability: `survey-info-acquisition-tools/research/semantic-tooling-survey.md`.
- 5.2 capability matrix now has only two accepted in-process parser profiles, each backed by parser/scanner/acceptance tests; cold-start empty matrix behavior remains schema-tested. No external cargo/rustc/rust-analyzer tool is claimed installed.
- 5.3 parser has design/tasks, registry and deterministic Python/Rust parsing with explicit syntax-only limitations. Evidence is in `tests/test_info_parser.py`, `tests/test_source_scanner.py`, and the checked-in matrix acceptance evidence.
- Constructor planning/execution and induction grouping/validation are being implemented; main full-system acceptance remains pending.


## Query and packaging child planning artifacts (2026-10-26)

- Created `openspec/changes/add-semantic-fact-query/design.md` and `tasks.md` from the existing proposal/specs and current implementation. Query execution and basic response projection tests exist; direct-node completeness, necessary ancestor progress, multi-project/cycle cases and full S1–S12 remain pending.
- Created `openspec/changes/define-skill-packaging/design.md` and `tasks.md`. Added a copied-install integration test in `tests/test_packaging.py`, which copies only the Skill directory and runs Python/Rust scan plus query without using repository-relative runtime paths. Current CI run: https://github.com/vchs6/code2semantics/actions/runs/40268487627.
- Induction batching/validation is accepted as a deterministic component boundary (no provider inference claimed): `tests/test_induction.py` covers grouping, evidence binding, conflicts, content-state/context separation and explicit no-provider gaps. Child task evidence is recorded in `add-induction-batch-trigger/tasks.md`.
- Main integration tasks 8.1–8.5 remain pending until the actual tool → parser → constructor/induction → FactBatch → repository re-read → complete minimal response path satisfies S1–S12. The fail-closed product gate must remain blocked until that evidence exists.


## Repository graph traversal increment (2026-10-26)

- Followed the pending repository graph-validation work before claiming overall completion. Added bounded `Repository.traverse_navigation` with cycle protection, multi-parent support, equivalent-edge deduplication, external/cross-source terminal references, and explicit max-depth/max-edge termination.
- Test-first evidence: initial CI run https://github.com/vchs6/code2semantics/actions/runs/40297171108 failed because the API was missing; after implementation, a second run exposed a disconnected multi-parent test fixture. The fixture was corrected to represent a reachable graph, not to relax the assertion.
- Latest completed CI for this increment: https://github.com/vchs6/code2semantics/actions/runs/40297475469. Repository 53 passed; matrix 15; parser 9; scanner 7; source acceptance 4; packaging 2; bounded executor 3; producer dispatch 3; combined information-needs/constructor/induction/query 51 passed; strict OpenSpec passed.
- Root tasks 8.1–8.5 remain pending. The fail-closed product gate still blocks because the full S1–S12 integration and tool → parser → constructor/induction → FactBatch → repository → complete response acceptance has not been demonstrated. No overall completion claim is made.


## Query graph-boundary acceptance increment (2026-10-26)

- Added a query-orchestration test using a schema-valid FactBatch with multi-parent navigation, a dependency cycle, and an external terminal reference. It asserts bounded graph traversal terminates and final query response contains only requested identity/name fields, not graph-edge assertions or out-of-scope external contents.
- The query subtask 3.4 test set now covers multi-project same-name identities, nested/disjoint roots, external references, conflict evidence, out-of-catalog fields, plus the new multi-parent/cycle scenario.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40297691458 — repository 53 passed; matrix 15; parser 9; scanner 7; source acceptance 4; packaging 2; executor 3; producer dispatch 3; combined planning/constructor/induction/query suite 52 passed; strict OpenSpec passed.
- Root task 8.1 remains pending because these tests are distributed across component suites and do not yet establish all S1–S12 scenarios in the single root acceptance harness. The full runtime tool/induction path remains unverified; product delivery gate correctly remains blocked.


## Dependency-ordered component acceptance update (2026-10-26)

- Marked 5.1 complete from the survey child tasks/evidence; toolchain availability remains explicitly unverified and survey findings do not enable matrix profiles.
- Marked 6.1 complete for deterministic induction grouping/result validation. No cognitive provider is claimed; no-provider behavior remains an explicit gap.
- Marked 6.2 complete for the current fixed Python/Rust F2/L3 scope: constructor catalogue/plan, accepted parser dispatch, evidence-bound FactBatch construction and partial-failure gaps have focused tests. This does not claim all F1–F18 semantic layers or a provider-backed induction workflow.
- Marked 7.2 complete for self-contained Skill packaging and copied-install Python/Rust scan/query validation; official skills-ref validation was not run and is not claimed.
- Latest completed full CI after concurrency and graph work: https://github.com/vchs6/code2semantics/actions/runs/40298151751. Repository 54 passed; matrix 15; parser 9; scanner 7; runtime acceptance 5; packaging 2; executor 3; producer dispatch 3; combined planning/constructor/induction/query 52 passed; strict OpenSpec passed. Product delivery gate remains BLOCKED.
- Still pending in the dependency plan: 6.3 full repository acceptance (including a separate RED-first transfer run and remaining import/local mutation policy), 7.1 full S1–S12 query acceptance, and 8.1–8.5 root integration. These remain unchecked; the implementation is not declared globally complete.


## Repository transfer safety and focused gates (2026-10-26)

- Added an explicit regression for an empty-but-valid SQLite file used as a restore source. RED: https://github.com/vchs6/code2semantics/actions/runs/40298339861. It exposed that a schema check guarded by `if tables` allowed an empty database to replace the target repository.
- Fixed restore to reject any backup lacking the full repository schema before copying. The restore target's fact/source rows remain unchanged on rejection.
- CI GREEN: https://github.com/vchs6/code2semantics/actions/runs/40298437864 — repository 55 passed; focused transaction 6; transfer 6; repository acceptance 3; matrix 15; parser 9; scanner 7; source acceptance 5; packaging 2; executor 3; producer dispatch 3; combined planning/constructor/induction/query 52; strict OpenSpec passed.
- The workflow now runs dedicated transaction, transfer and repository acceptance suites in addition to the complete repository suite. This improves gate granularity but does not substitute for the pending root S1–S12 acceptance.
- Root task 6.3 remains pending until the remaining repository acceptance and import/local-mutation policy are complete; root 7.1 and 8.1–8.5 also remain pending.


## Source deletion and import conflict safety (2026-10-26)

- Added real-source acceptance coverage for deleting a Python source file: rescan appends a new source snapshot; historical fact rows remain stored; current queries exclude facts from the deleted file and preserve unaffected current facts.
- Added transfer coverage for importing a conflicting immutable fact identity; the import is rejected and normalized rows/submission receipts remain unchanged.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40298718500 — repository 56 passed; transaction 6; transfer 7; repository acceptance 3; matrix 15; parser 9; scanner 7; runtime acceptance 6; packaging 2; executor 3; producer dispatch 3; combined planning/constructor/induction/query 52 passed; strict OpenSpec passed.
- These checks strengthen the append-only/current-head boundary, but root 6.3, 7.1 and 8.1–8.5 remain pending until child acceptance gaps and full S1–S12 are closed. The product delivery gate remains blocked by design.


## Restore schema validation hardening (2026-10-26)

- Added a RED regression for a malformed SQLite backup that contains every expected table name but lacks the required columns. The previous name-only check accepted it and could overwrite the live database.
- `Repository.restore` now verifies required columns across all normalized tables before calling SQLite backup/restore. Both empty and malformed backup tests assert fact/source history remains unchanged after rejection.
- CI GREEN: https://github.com/vchs6/code2semantics/actions/runs/40299139228 — repository 57 passed; transaction 6; transfer 8; repository acceptance 3; matrix 15; parser 9; scanner 7; runtime acceptance 6; packaging 2; executor 3; producer dispatch 3; combined planning/constructor/induction/query 52; strict OpenSpec passed.
- Full S1–S12 acceptance and the final product delivery gate remain pending. This repository safety improvement does not imply complete system acceptance.


## Root acceptance: unavailable and out-of-scope boundaries (2026-10-26)

- `tests/test_acceptance.py` now exercises the real query/construction path for unavailable roots and out-of-scope node targets. It verifies explicit failure gaps, no fallback to another project, no foreign-source result leakage, and no mutation of the foreign repository's fact rows.
- Backup restore rejects empty SQLite files and malformed databases with expected table names but incorrect columns. The target's fact/source history remains unchanged on rejection.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40299401934 — repository 57 passed; transaction 6; transfer 8; repository acceptance 3; matrix 15; parser 9; scanner 7; runtime acceptance 8; packaging 2; executor 3; producer dispatch 3; combined planning/constructor/induction/query 52 passed; strict OpenSpec passed.
- Root tasks 8.1–8.5 remain pending: this is expanded but not complete S1–S12 coverage; the full external tool/provider → parse → constructor/induction → FactBatch → repository → minimal response path is not yet fully demonstrated. Product gate remains BLOCKED.


## Repository dependency closure (2026-10-26)

- Root dependency 6.3 is now satisfied by the repository component's immutable normalized writes, source-head validity, append-only validity events, atomic transactions, backup/restore and current export/import tests.
- RED/GREEN for a current-head local mutation bug: RED run https://github.com/vchs6/code2semantics/actions/runs/40310626084; GREEN run https://github.com/vchs6/code2semantics/actions/runs/40310872678.
- GREEN evidence: repository 59 passed; transaction 6; transfer 8; repository acceptance 5; matrix 15; parser 9; scanner 7; runtime acceptance 9; packaging 2; executor 3; producer dispatch 3; combined planning/constructor/binding/induction/query 52 passed; strict OpenSpec passed.
- Next dependency is query acceptance 7.1 / child task 4.4, then root integration tasks 8.1–8.5. Product delivery gate remains blocked until full S1–S12 acceptance passes.
