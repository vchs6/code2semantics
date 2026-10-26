# 实施核验台账（2026-10-25）

基线：`main` 的 `fdb281326451dc97c5e1869fbaf85f543e930f9f`；验证分支 `chore/verify-implementation-20261025`。本报告只记录证据，不把代码存在视为完整验收，也不改动既有 OpenSpec 勾选。

## 自动化测试（GitHub Actions）

首轮运行（CI 目录遍历错误）：https://github.com/vchs6/code2semantics/actions/runs/40207357369

**修正后成功运行**：https://github.com/vchs6/code2semantics/actions/runs/40207444540（python-tests 与 openspec 两个作业均成功）

| 检查 | 通过 | 失败 | 跳过 | 证据边界 |
| --- | ---: | ---: | ---: | --- |
| `python -m pytest tests/repository -q -ra -p no:cacheprovider` | 31 | 0 | 0 | 仅现有 repository tests |
| `python -m pytest tests/capability_matrix -q -ra -p no:cacheprovider` | 14 | 0 | 0 | 仅现有 matrix tests |
| `validation/validate_contracts.py` | 7 schema, 64 shape, 30 semantic | 0 | - | 输出为 `design_assets_pass`，`runtime_verified=false` |
| 全活动 OpenSpec strict | 前 6 个变更通过 | 1 个 CI 枚举错误 | - | 错把 `openspec/changes/archive` 当作活动变更；已修正脚本，复验见 Actions |

首次 OpenSpec 作业失败属于 CI 遍历范围错误，不是已经完成校验的六个变更不合法。修正后的严格 OpenSpec 验证作业已成功完成；CI 中没有运行真实工具→解析→归纳的端到端验收。

## 事实仓库 tasks.md 对照

- 1.1–1.5：已标记完成；ContractCodec 的测试、实现和验证记录存在。
- 2.1–2.5：任务仍未勾选；`store.py`、`test_store.py` 已存在并在 31 项仓库测试内通过，但没有逐项审核“精确行级存储、不同来源、重开、最小返回”等所有验收要求；不得自动勾选。
- 3.1–3.5：任务仍未勾选；`test_transactions.py` 已存在，当前测试集通过；局部字段/关系/证据/冲突失效更新覆盖不完整，尚不得宣称全组完成。
- 4.1–4.5：任务仍未勾选；`tests/repository/test_validity.py` 尚未出现在检查基线，当前有效性、前提、导航去重、环和 external 的完整验收缺证。
- 5.1–5.4：任务仍未勾选；`tests/repository/test_transfer.py` 尚未出现在检查基线，导入/导出、备份/恢复的验收缺证。
- 6.1–6.4：任务仍未勾选；`tests/repository/test_acceptance.py` 尚未出现在检查基线，尚无端到端仓库验收证据。

## 主变更与依赖

主变更任务清单 2–4 组公共设计/契约已勾选；其 5–8 组关于工具研究、解析器、构造器、归纳、查询及端到端的任务仍需逐项完成和验收。能力矩阵任务清单已全部勾选，现有 14 项测试通过；与主变更集成验收是不同门槛。

**仍未完成的验证**：真实工具调用→解析→归纳→FactBatch→SQLite 持久化→重开→最小查询/响应；多来源状态变化、备份恢复、并发/事务等未覆盖任务的新增测试。CI 通过不应被解释为这些环节已完成。

## 后续执行顺序

1. 接受当前 CI 的全部严格 OpenSpec 校验结果，若失败按具体 change 定位并修复。
2. 按 TDD 为仓库任务 3–5 组先补 RED 用例，再实现 GREEN；运行整组 pytest 回归。
3. 补仓库验收测试，再与构造器/查询/解析器/归纳接口集成。
4. 按实际测试、审查和提交证据逐项勾选 tasks.md，并回填 `implementation-validation.md`，不得以计划代替验收。
5. 完成真实端到端执行、严格校验及独立评审后才将主变更标记为可验收。

本台账的 CI 与静态审计不代表已执行新增产品实现。


## 2026-10-26 补充：运行时事实保留约束

用户明确要求：系统运行时生成的语义事实记录不得删除。

- 备份恢复测试已改为恢复到独立临时数据库，原始测试库不再通过 DELETE 模拟数据丢失。
- `Repository._insert_record` 不再对事实/属性/关系使用 SQLite `INSERT OR REPLACE`，避免 SQLite REPLACE 隐式删除并重插已有记录；来源和实体使用 `INSERT OR IGNORE` 保留已存在行。遇到重复事实键的不同提交应由事务冲突拒绝，不能覆盖既有事实。
- 新增测试验证新提交不能替换已存事实，失败后原事实与提交记录不变。
- 当前 main CI：https://github.com/vchs6/code2semantics/actions/runs/40255196104
- 本次结果：repository 35 passed；capability matrix 14 passed；严格 OpenSpec 通过；公共设计契约输出仍为 `runtime_verified=false`。

边界：这落实了当前 SQLite 写入路径的防覆盖/保留约束，不等于已实现所有历史版本、失效传播、局部更新或端到端语义生命周期；这些仍需按任务契约继续实现和验证。


## 2026-10-26 治理与产品交付门禁修正

用户要求：先修正 AI 治理和质量门禁缺陷；后续直接提交 main，不创建分支。

- `AGENTS.md` 新增第 12 节“产品交付与质量门禁”：区分组件测试、契约校验与真实产品行为验收；明确真实输入、运行入口、可观察输出、集成断言和复现命令为完成证据。
- `openspec/config.yaml` 的 tasks 规则新增要求：产品完成状态必须有真实运行入口、真实输入场景、可观察输出和集成验收证据。
- 新增 `scripts/quality_gates/check_product_delivery.py`，以 fail-closed 方式检查 Skill 运行入口、跨组件验收测试、真实源码场景 fixture 和运行验收记录。
- `.github/workflows/verify-semantic-facts.yml` 在组件测试与契约检查后执行该门禁。
- 最新验证：https://github.com/vchs6/code2semantics/actions/runs/40256001405 。现有 35 个 repository 测试、14 个 matrix 测试、设计契约检查和严格 OpenSpec 均通过；产品交付门禁按预期失败，明确指出缺少 `skills/layered-semantic-facts/SKILL.md`、`tests/test_acceptance.py`、`tests/fixtures/scenarios`、`skills/layered-semantic-facts/references/acceptance-results.md`。
- 该 CI 失败是有意的 fail-closed 结果，表明项目当前不能宣称产品端到端验收完成。门禁通过后仍须执行真实源码集成测试，不能只依靠文件存在性。

以上均直接提交 main。下一步应先按现有 OpenSpec 流程补齐真实运行入口和集成产物，再运行门禁；不得通过降低门禁要求恢复绿色。


## 2026-10-26 组件实现增量

直接提交至 `main`，未创建分支：

- `skills/layered-semantic-facts/scripts/semantic_facts/info_parser.py`：确定性 Python AST 解析器、来源证据和行范围、语法错误显式 gap、ParserRegistry 注册/发现。
- `skills/layered-semantic-facts/scripts/semantic_facts/fact_constructor.py`：将解析 observations 转换为符合公共 FactBatch Schema 的 F2/L3 源码语法清单事实；不把语法观察冒充运行时行为。
- `skills/layered-semantic-facts/scripts/semantic_facts/source_scanner.py`：扫描 Python 源文件，计算内容状态，保守记录 Git dirty/untracked 状态，并串接 ParserRegistry 与 FactBatch 构造器。
- `skills/layered-semantic-facts/scripts/semantic_facts/cli.py`：`scan-python` 持久化与 `query` 查询命令。
- `skills/layered-semantic-facts/SKILL.md`：记录当前可执行入口和支持边界。
- 新增 `tests/test_info_parser.py`、`tests/test_source_scanner.py`、`tests/test_acceptance.py` 和真实源码 fixture；端到端测试覆盖真实 Python 源码→解析→FactBatch→SQLite→关闭重开→查询，并验证重复扫描不减少事实行。
- CI 运行：https://github.com/vchs6/code2semantics/actions/runs/40257745511 。结果：repository 35 passed，capability matrix 14 passed，parser 6 passed，source scanner 4 passed，runtime acceptance 1 passed；严格 OpenSpec 通过。
- 产品交付门禁按预期仍 BLOCKED：当前链路只覆盖 Python F2/L3 语法清单，不包括工具矩阵调度与外部工具执行、受约束归纳、完整多层构造、源码变更后的受影响事实失效/重构，以及完整公共查询响应。未将该局部链路标记为完整系统验收。


## 2026-10-26 查询投影与事实版本保留

- 新增 `semantic_facts/query_engine.py`：校验公共 Query、从仓库读取当前范围事实、比较所选字段覆盖、生成符合 output-schema 的最小响应，并对缺失字段返回显式 gap。当前只覆盖已存事实的确定性投影，不会伪称能触发构造/归纳。
- CLI `query` 已改为返回 Schema 校验后的响应，不再直接透传仓库原始结果。
- 源码扫描以 root + Python 快照内容生成 source_id；新快照使用新的 source ID，旧事实行不删除。仓库按精确 scope root 选择最新来源快照用于当前查询，避免把旧快照事实与当前结果混合。
- 新增运行测试：源码由 `version_one` 改为 `version_two` 后，事实总行数和来源版本数增加，旧版本仍保留在 SQLite 中，当前查询只返回最新版本；相同扫描保持幂等。
- 最新已完成 CI：https://github.com/vchs6/code2semantics/actions/runs/40258363539 。repository 35 passed、matrix 14 passed、parser 6 passed、scanner 4 passed、runtime acceptance 2 passed；严格 OpenSpec 通过。
- 质量门禁仍 BLOCKED 是正确结果：尚未完成能力矩阵驱动的工具执行、归纳批组、完整多层事实构造，以及对依赖影响/部分源码变化的精确失效传播。不能把当前 Python 语法清单路径等同于完整 Code2Semantics。

## 2026-10-26 OpenSpec dependency-order continuation

- Constructor 3.2 implemented: `semantic_facts/producer_dispatch.py` routes matrix-selected accepted profiles through ParserRegistry; in-process profiles run directly, subprocess profiles require an injected allowlisted executor, and timeout/nonzero/unsupported/malformed outcomes return explicit gaps. `source_scanner.py` now uses this dispatcher.
- Constructor 3.4 and 4.2 implemented and tested: per-file failures preserve independent valid facts and make project inventory partial; constructed observations are checked against exact source ID, subject ID, content state and file locator before FactBatch creation.
- Repository immutable-write regression fixed: same-source same-identity conflicting assertion writes now raise `WriteConflict` and leave facts, attributes, versions and submissions unchanged. Valid source changes are represented by appended source snapshot identities; older facts remain stored.
- Query scope/response work: multiple disjoint and nested roots, same-name subjects, unavailable roots, and out-of-scope node references are tested. Out-of-scope references are rejected before repository reads. Fields absent from the fixed first-phase information-needs catalogue are returned in `out_of_catalog`, separate from in-scope gaps. External references and conflict evidence are retained by response projection.
- CI run `https://github.com/vchs6/code2semantics/actions/runs/40276135137`: repository 45, matrix 15, parser 9, scanner 7, source acceptance 4, packaging 2, executor 3, producer dispatch 3, combined information-needs/constructor/binding/induction/query 51 passed; strict OpenSpec passed.
- Still pending by OpenSpec: query graph cases for multi-parent/dependency cycles and full S1–S12; full dependency-aware invalidation; configured cognitive induction provider; full higher-layer semantics beyond Python/Rust F2/L3 syntax inventory. Product delivery gate remains intentionally blocked.

## 2026-10-26：按 OpenSpec 依赖顺序推进 6.3 事实仓库验收

基线：主变更的 5.0–5.3、6.1–6.2 已标记完成；6.3 是第一个尚未完成的主集成依赖项。本轮不重写已定稿的设计或任务、不绕过 OpenSpec 工件生成纪律，也不提前标记主集成通过。

新增 `tests/repository/test_acceptance.py::test_repository_acceptance_graph_and_invalidation_survive_backup_without_deleting_facts`，在一个独立临时 SQLite 场景内验证：当前来源图导航、字段失效后查询过滤、事实/证据/关系/前提/直接节点行数不减少、备份到独立数据库及恢复后的失效/图结构一致性。

实际 CI：https://github.com/vchs6/code2semantics/actions/runs/40300593977

- Repository 58 passed（包含新增组合验收场景）。
- 其他已启用测试组均通过，严格 OpenSpec 校验成功。
- Product delivery gate 仍按预期 BLOCKED，因为全系统 `FULL_END_TO_END_ACCEPTANCE: PASS` 未取得真实 S1–S12 运行证据；不能以此轮仓库级验收替代整体交付。

下一步仍需核对事实仓库 6.4 的独立评审与交付证据，再按 7.1 查询编排子变更的现有 design/tasks 推进。未经 OpenSpec 指令驱动的任务更新及评审，不在本轮直接勾选 6.2/6.4。
