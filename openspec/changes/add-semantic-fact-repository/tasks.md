# Tasks

语义事实仓库 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: 后续实施使用 superpowers:subagent-driven-development 或 superpowers:executing-plans，逐项执行；本轮仅规划，所有步骤保持 pending，不自动开始 apply。

**Goal:** 为唯一 Skill 客户端交付按实体组织、可增量维护、原子一致且保真存取的当前事实仓库。

**Architecture:** 同源公共契约经边界 codec 拆为 SQLite 实体、事实、字段、显式边及证据/状态行；显式操作与内部比较令牌控制更新。有效读取检查必要前提；图遍历受深度/边数限制，截断只作内部元数据。

**Tech Stack:** Python、标准库 sqlite3、jsonschema、pytest；不新增网络服务或语言专属 schema。

**Spec:** [specs/semantic-fact-repository/spec.md](specs/semantic-fact-repository/spec.md)、[design.md](design.md)、[proposal.md](proposal.md)。先读这三份再执行。design 没有影响范围/结构的未决 Open Questions；公共 wire 绑定是明确外部准入，当前尚未满足，不能用旧资产替代。

### Global Constraints

- `sources/` 或用户项目源码只读；仓库不读取来源补证据，不触发工具/研究/解析器，不判断语义正确性，不组装 Response。
- 主变更拥有公共契约；本组件只消费最新同源定义。无历史、用户 snapshot/revision/refresh、旧兼容或迁移工具；不清库绕测试。
- 使用真实临时 SQLite 与合规公共 fixture；fixture 只证明仓库存取，不冒充真实事实生产或端到端证据。原 `verification.md` 不修改、不作为当前通过证据。
- 未来文件均为待创建；测试前先确认实际文件状态。每组全部对应行为测试必须在该组实现前写入并运行 RED；实现与 GREEN 步骤不得新补未运行 RED 的行为测试。每组 RED 必须是该行为缺失导致的失败，不能把依赖/fixture错误当 RED。通过后再执行该组提交；本轮不提交产品代码。
- 所有命令从仓库根执行。先设置 PowerShell `$env:PYTHONPATH=(Join-Path (Get-Location) 'skills/layered-semantic-facts/scripts')`；`python` 指所选 Python 解释器，需可导入 pytest/jsonschema。依赖配置随任务 1 创建，不假定现有 runtime 已就绪。

### Review Focus

- 同名主体、重叠目录与共享多工作空间成员不能串域或复制身份：任务 2、6 的身份/图测试。
- 同 ID 不同内容、合法 CAS 更新、提交键重用及跨连接陈旧写必须分别判定：任务 3、4。
- 证据/冲突/局部字段变更不能被旧整事实写覆盖，依赖循环内失效不能漏出：任务 4、5。
- 不完整 child 识别与限定否定的域/依据不能在读取或截断时升级完整性：任务 1、5、6。
- 导入分配新本地 token 后前提仍可验证，原 invalid 保持 invalid；恢复不得覆盖现有目标：任务 7。

### File Structure

| 未来路径 | 职责/首次创建任务 |
| --- | --- |
| `skills/layered-semantic-facts/scripts/semantic_facts/__init__.py` | 自包含包，任务 1 |
| `skills/layered-semantic-facts/scripts/semantic_facts/repository/types.py` | design D3 的内部类型/错误与类型化 StoredRecord 行，任务 1 |
| `skills/layered-semantic-facts/scripts/semantic_facts/repository/contract.py` | 同源 codec、字段绑定，任务 1 |
| `skills/layered-semantic-facts/scripts/semantic_facts/repository/store.py` | 连接/DDL、事务、读取和遍历，任务 2–6 |
| `skills/layered-semantic-facts/scripts/semantic_facts/repository/transfer.py` | 保真导出导入、备份恢复，任务 7 |
| `skills/layered-semantic-facts/scripts/semantic_facts/repository/__init__.py` | 统一 API/path 选择，任务 2、7 |
| `skills/layered-semantic-facts/scripts/requirements.txt` | jsonschema；开发测试依赖 pytest，任务 1 |
| `skills/layered-semantic-facts/references/repository.md` | 本组件用法与内部绑定说明，不另定义公共协议，各组随交付更新 |
| `tests/repository/conftest.py`、`tests/repository/fixtures/` | 最新公共事实 fixture 与临时库，任务 1 |
| `tests/repository/test_contract.py`、`test_store.py`、`test_transactions.py`、`test_mutations.py`、`test_validity.py`、`test_graph.py`、`test_transfer.py`、`test_acceptance.py` | 各模块相应行为测试，任务 1–8 |
| `openspec/changes/add-semantic-fact-repository/implementation-validation.md` | 后续 apply 的真实准入/组件结果，不改旧记录，任务 1、8 |

## 1. 公共准入、同源边界与类型

**Files:** 新建上表 types.py、contract.py、包文件、requirements.txt、conftest.py、fixtures、test_contract.py、repository.md 和 implementation-validation.md；不修改公共 assets/references 的协议定义。

**Interfaces:** 消费主 D1 最新 schema/正反例与主校验器。产出 design D3 的 `JsonObject`、`RecordKey`、`Mutation`、`ChangeSet`、`CommitReceipt`、`FactFilter`、`ReadResult`、`RecordReadResult`、`TraversalResult`、错误类及 `StoredRecord`；类型字段与 design 一致。`ContractCodec(schema_root: Path)` 的 `validate_batch(batch: JsonObject) -> None`、`decode(batch: JsonObject) -> tuple[StoredRecord, ...]`、`encode(records: Sequence[StoredRecord]) -> JsonObject` 为后续消费接口。

- [ ] 1.1 核验 design D1 三项外部准入：逐一检查主迁移资产、公共 FactBatch/Response 分离和必需状态的实际 JSON Pointer；按主任务记录的实际命令运行 `openspec/changes/epic-layered-semantic-fact-skill/validation/validate_contracts.py`；将命令、退出码、资产引用写入 implementation-validation.md。旧协议残留或公共前提/失效表示缺失时停止实施并保留该项未完成，不新造公共字段；验收为逐项准入通过记录。
- [ ] 1.2 写 test_contract.py 失败测试与同源 fixture：`test_roundtrip_preserves_every_field` 对源码/清单/配置/文档/观察证据、origin 与 knowledge、每字段 context/coverage/basis、冲突、有效性、限定否定和 child 完整性逐值比较；`test_rejects_report_response_and_old_protocol` 参数化人读报告/最终 Response/旧版本入口，断言 ContractError 且 location 非空；`test_same_shape_across_languages` 保留不同语言原始语义值。明确断言 `assert codec.encode(codec.decode(batch)) == batch`，不以缺字段或强制默认值通过。
- [ ] 1.3 RED：执行 `python -m pytest tests/repository/test_contract.py -q`，预期缺少 ContractCodec/类型实现导致失败；准入与 fixture 本身必须已通过同源 schema，保存对应行为失败输出。
- [ ] 1.4 最小实现上述类型和 codec，StoredRecord 为 design D2 各行的不可变类型集合；在 repository.md 列实际公共 JSON Pointer → 行/字段及重建绑定，包含所有公共字段/扩展。实现缺映射时定位拒绝；创建依赖清单与本地测试加载设置。GREEN：同一命令全通过且 fixture 用主 schema 复验通过，绑定表无遗漏。
- [ ] 1.5 提交该组精确文件并核对 `git diff --cached --stat` 仅本组交付，提交说明 `feat: add shared-contract repository codec`；验证提交包含失败后通过的测试与绑定文档，不包含公共 schema 改写。

## 2. 实体布局、单取与持久重读

**Files:** 新建 store.py、repository/__init__.py、test_store.py；更新 repository.md。

**Interfaces:** 消费任务 1 codec/StoredRecord。产出 `Repository(path: Path, codec: ContractCodec)`、`apply(changes: ChangeSet) -> CommitReceipt` 的 create 子集、`read(filters: FactFilter) -> ReadResult`、`read_record(target: RecordKey, project_keys: tuple[str, ...], validity: Literal['valid','all'] = 'valid') -> RecordReadResult | None`、`close() -> None`、`open_repository(path: Path | None, codec: ContractCodec) -> Repository`；后续任务扩同一接口，不另建测试入口。

- [ ] 2.1 写 `test_individual_records_survive_reopen`：同主体两种事实和同类型不同上下文事实均存在，关闭后新连接按主体/类型读取等于期望公共子批；直接用 sqlite3 核验 attributes/relations 为独立行，非 FactBatch blob。`test_source_domains_do_not_merge_names` 输入两个项目同名 helper 与一个共享两工作空间的主体，断言两同名键不同、共享主体只有一实体且两成员边保留。`test_filter_intersection_and_empty_projects` 断言组合条件只得预期事实、空项目集合为空。`test_exact_fact_field_and_relation_read_without_other_contexts` 对同主体同类型两个上下文按 RecordKey 单取事实/字段/关系，断言 result.target 是指定键、value/metadata 仅为指定目标及必要证据，不含另一个上下文；片段是 RecordReadResult，公共 read 批仍通过 schema，原 coverage 不变；越域或空项目精确读返回 None。`test_path_precedence_and_non_cwd_import` 参数化路径优先级/从临时工作目录导入，断言确切路径与同一公共事实。
- [ ] 2.2 RED：`python -m pytest tests/repository/test_store.py -q`，预期 Repository 不存在/读写或路径行为未实现失败；确认测试对真实临时文件执行。
- [ ] 2.3 最小实现 design D2 全部表、唯一性/外键/索引及 create/read/read_record/close；每连接开启并核实 foreign_keys。read 使用数据库条件选择与一致读事务，不全库 encode 后裁剪；tokens 与公共 batch 分开。open_repository 按显式参数 → SFRS_DB_PATH → `~/.atomcode/sfrs/facts.db` 选址，测试环境全部临时化，不写真实默认库。
- [ ] 2.4 GREEN：运行任务 2 RED 命令和 `python -m pytest tests/repository/test_contract.py -q`，预期全通过；repository.md 记录路径与单取示例。
- [ ] 2.5 提交 store.py、__init__.py、test_store.py 与本组文档，说明 `feat: persist entity-oriented semantic facts`；核对提交范围与前序 fixture 未损坏。

## 3. 原子批次、引用与幂等确认

**Files:** 更新 store.py，创建 test_transactions.py，更新 repository.md。

**Interfaces:** 消费任务 2 真实 SQLite 与 create/read，完成 `apply(changes: ChangeSet) -> CommitReceipt` 的全批校验/幂等。ContractError/ReferenceError/WriteConflict/StorageError 沿用任务 1。

- [ ] 3.1 写 `test_batch_failure_rolls_back_facts_evidence_conflicts_and_receipt`，首项合法、后项非法/提交阶段外键失败，断言新连接读回等于提交前且 submissions 无确认；`test_external_reference_is_not_dangling_internal` 对同一目标分别用合法 external 和非法 internal，前者保留原值且不建伪实体，后者 ReferenceError.target 定位目标；`test_same_batch_cycle_is_legal` 同批 A/B 相互引用成功。`test_repeated_submission_returns_same_receipt` 断言 `assert repo.apply(changes) == repo.apply(changes)` 且行数/token不增；同键改内容及同事实 ID 不同 create 内容分别 WriteConflict，矛盾候选不同 ID 与公共冲突记录一起保留。 `test_locked_writer_leaves_no_partial_state`，用第二真实连接持写锁，断言 StorageError 与完整原状态，释放后相同操作可提交。`test_structural_validity_does_not_assert_semantic_truth` 保存一条结构合规但知识不足的事实并逐值重读相等。
- [ ] 3.2 RED：`python -m pytest tests/repository/test_transactions.py -q`，预期原子/引用/幂等/锁忙及知识状态保真断言失败，不能接受因 fixture 无效而失败。
- [ ] 3.3 最小实现 BEGIN IMMEDIATE、最终批后引用视图、延迟内部外键、全事务回滚及提交确认；规范摘要涵盖操作与 token，排序对象键而保留数组序，非有限数拒绝。重复同键同摘要先取原确认，同键异摘要拒绝；同内容 create 幂等、不同内容拒绝。
- [ ] 3.4 GREEN：运行任务 3 RED 命令及 `python -m pytest tests/repository/test_store.py -q` 全通过；记录批次/引用/冲突错误示例，不声称软件语义已证实。
- [ ] 3.5 提交本组 store.py、test_transactions.py、repository.md，说明 `feat: apply atomic idempotent fact batches`，检查无隐式覆盖/旧版本入口。

## 4. 显式局部更新、删除与陈旧写保护

**Files:** 更新 store.py，创建 test_mutations.py，更新 repository.md。

**Interfaces:** 扩充同一 `apply` 支持 Mutation 的 update/invalidate/delete；消费维护读 `ReadResult.tokens` 与 RecordKey，无新增用户版本参数。

- [ ] 4.1 写 `test_attribute_update_preserves_unrelated_records`，匹配 token 更新单字段并同步证据，断言新字段/证据正确、无关事实的 batch 与 token 均未改变；`test_stale_whole_fact_write_after_field_evidence_or_conflict_update` 参数化局部字段/关系/共享证据/冲突更新，第二连接旧整事实 token 均 WriteConflict；`test_duplicate_and_overlapping_mutations_rejected` 对同目标重复及整事实+字段重叠，断言全批原状态；`test_delete_requires_incoming_reference_maintenance` 缺影响声明拒绝，补同批入边失效/删除后成功，当前查询无被删事实/有效悬空边，维护读保留失效标志、未转 external。 `test_evidence_delete_and_entity_delete_keep_references_consistent` 检查仍被使用的证据不能直接删除、实体删除维护所有有效引用； `test_replay_update_receipt_after_token_advanced`，断言原提交重放返回原确认、不同提交旧 token 拒绝。
- [ ] 4.2 RED：`python -m pytest tests/repository/test_mutations.py -q`，预期操作/CAS/删除引用维护/重放确认断言失败；读取预置结果应与任务 2–3 已通过行为一致。
- [ ] 4.3 最小实现逐目标 CAS、不可复用新 token、全批重叠拒绝与墓碑删除；字段/关系/共享证据/冲突变更推进所有所属事实 token。校验被引用证据删除及实体所属记录、入边影响，缺失声明整体拒绝；只改受影响行，不能清库重建。文档给出一次合法显式更新和一次冲突的区别。
- [ ] 4.4 GREEN：运行任务 4 RED 命令及 `python -m pytest tests/repository/test_transactions.py -q` 全通过。
- [ ] 4.5 提交本组精确文件，说明 `feat: maintain fact records with explicit updates`，核验未增用户 revision/snapshot 参数。

## 5. 当前有效性与必要前提闭包

**Files:** 更新 store.py，创建 test_validity.py，更新 repository.md。

**Interfaces:** 消费任务 4 mutation 与内部 token，完成 `read(FactFilter(..., validity='valid'|'all')) -> ReadResult` 和 apply 的 premises 影响约束；不添加来源扫描器。

- [ ] 5.1 写 `test_missing_transitive_invalidation_rejects_batch`：A→B→C 必要前提链分三种情形：更新 C 为新有效内容时，遗漏 A/B 失效或重建声明整批拒绝；齐全且 A/B 标失效时，当前读排除旧依赖 A/B、保留新有效 C 及无关 U。删除 C 或将 C 标失效时，齐全维护后当前读排除 A/B/C、保留 U，维护读仍保留相应失效边界；`test_valid_read_checks_premise_token_and_cycle` 检查多级前提、前提墓碑/失效/绑定陈旧及环内失效均不能泄漏有效命中，合法全有效闭包有限返回。`test_maintenance_read_keeps_invalid_context` 断言维护读逐值保留旧定位、来源状态和失效原因，valid 读不返回该断言。 `test_non_source_evidence_and_partial_children_not_upgraded`：五种来源证据均可重读，给父/部分 child 引用及“不完整”状态，断言公共 coverage/完整性原样不变；限定否定域/basis 保持。来源路径指向不存在文件仍不访问来源，按已提交 invalid 状态过滤。
- [ ] 5.2 RED：`python -m pytest tests/repository/test_validity.py -q`，预期前提闭包/失效过滤/证据和覆盖保真断言失败；使用真实 SQLite fixture，局部异常状态仅在专门的安全读取测试中用 sqlite3 注入，不能作为正常写入入口。
- [ ] 5.3 最小实现显式 premises 反向闭包校验、批后重新绑定和有效读前提 token 检查；已访问集合处理环，只核查提交的必要前提，不推导软件依赖。
- [ ] 5.4 GREEN：运行任务 5 RED 命令及 `python -m pytest tests/repository/test_mutations.py -q` 全通过；文档明确查询负责当前来源核实与语义影响，仓库只维护提交并校验必要前提，不因旧定位可取回重新有效。
- [ ] 5.5 提交本组 store.py、test_validity.py、repository.md，说明 `feat: enforce current fact premise validity`，核验无自动源读取或事实生产。

## 6. 多父、环与有限显式遍历

**Files:** 更新 store.py，创建 test_graph.py，更新 repository.md。

**Interfaces:** 消费任务 5 有效 read，产出 `walk(start: str, filters: FactFilter, relation_types: tuple[str, ...], max_depth: int, max_edges: int) -> TraversalResult`；TraversalResult 仅仓库内部元数据，公共 batch 不变。

- [ ] 6.1 写 `test_multi_parent_cycle_retains_each_explicit_edge_once`，两个父共享主体且存在回边，断言边键集合与输入一致、每边一次、不补传递边；`test_traversal_limits_do_not_rewrite_fact_coverage` 比较深度 0/1 和边预算 1，断言深度0仅起点、预算1仅一条稳定排序边、存在未走匹配边时 `assert result.truncated is True` 且 reason 为 depth/edges，已有公共 coverage 逐值未变；`test_external_endpoint_never_expands_scope` 保留 external 引用、无范围外实体。空项目/空类型不走边，负深度或非正边预算拒绝。
- [ ] 6.2 RED：`python -m pytest tests/repository/test_graph.py -q`，预期缺少 walk/有界行为失败，准备数据必须通过正常 apply。
- [ ] 6.3 最小实现逐层定向 SQL + 有限队列、主体访问集和关系身份去重；只走匹配类型与授权项目，稳定按边键排序，保留多父/回边；不把遍历截断写回事实，不读取整库再遍历，不自动读取 external 来源。
- [ ] 6.4 GREEN：运行任务 6 RED 命令及 `python -m pytest tests/repository/test_validity.py -q` 全通过；在 repository.md 写一个有环图调用与确切边集合/截断结果，明确结构环不等于运行循环，遍历不判断条件可满足性。
- [ ] 6.5 提交本组精确文件，说明 `feat: traverse bounded explicit fact relations`，核验 fixture 同名/重叠边界仍成立。

## 7. 保真导入导出与安全备份恢复

**Files:** 新建 transfer.py、test_transfer.py；更新 types.py、统一 __init__.py 与 repository.md。

**Interfaces:** 消费 Repository/codec/current records。types.py 同组新增 design D6 的 RepositoryTransfer、DeletedIdentity、PremiseIdentityBinding；私有维护容器严格验证，不成为新公共事实协议。产出 `export_current(repo: Repository, destination: Path) -> None`、`import_current(repo: Repository, source: Path, submission_key: str, project_keys: tuple[str, ...]) -> CommitReceipt`、`backup(repo: Repository, destination: Path) -> None`、`restore(backup_path: Path, destination: Path, codec: ContractCodec) -> None`，参数与 design D3 一致。

- [ ] 7.1 写 `test_export_import_preserves_invalid_conflicts_and_rebinds_premises`：库含有效/失效事实、证据、冲突与前提，导出后导入全新库，断言公共 batch 完全相等、有效/维护读集合一致、本地 token 不复用而 valid 前提仍可验证、invalid 不升级；导出无内部 token/提交确认。`test_transfer_roundtrip_deleted_internal_endpoint` 以正常 apply 删除主体并保留失效入边/冲突/前提，导出容器含必要真实墓碑身份；导入新库后精确维护读墓碑 deleted 为 True、失效关系/冲突逐值一致、默认有效读无该端点；移除墓碑、伪造未引用墓碑、绑定端点不匹配公共前提完整域限定身份、伪造域或越授权项目集合均整体拒绝，不将引用改成 external。`test_authorized_cross_project_premise_transfer_roundtrip` 对授权集合内两项目/来源域的合法必要前提导出导入，断言两个端点完整身份和公共前提均不变、valid 读取仍命中，显式传入包含双方的 project_keys 时不能因跨域拒绝；只传一方项目、传空集合、伪造完整身份或越调用方显式项目集合则整体拒绝且库不变。测试必须直接设置该参数，不依赖隐含上下文。`test_import_rejects_missing_premise_or_different_existing_content` 整批拒绝且原库不变。`test_backup_restore_preserves_current_state_and_tombstones` 恢复后新连接重读相等、删除引用维护仍有效。 `test_restore_failure_never_overwrites_existing_database` 对已有目标、损坏备份、不兼容格式断言 StorageError、目标/原库字节不变、不创建成功目标。
- [ ] 7.2 RED：`python -m pytest tests/repository/test_transfer.py -q`，预期缺 transfer API/保真绑定或失败恢复保护行为失败，原库在失败后仍可 read。
- [ ] 7.3 最小实现一致当前视图导出为 design D6 私有维护容器、精确封套校验、同源公共batch验证及批后引用视图校验；import_current 必须消费调用方显式 project_keys，空集合拒绝，不能从文件/工作目录推断授权；仅恢复真实被失效记录引用的必要墓碑，不恢复旧值，按完整前提身份同事务重绑新 token；原invalid原因不变，valid缺有效前提则拒绝，封套只为本组件当前维护，不引入公共字段或历史查询。采用 sqlite3 一致备份，恢复在临时库检查完整性/外键、schema与重读后只发布到不存在目标；不能删库或迁移旧记录。
- [ ] 7.4 GREEN：运行任务 7 RED 命令及 `python -m pytest tests/repository/test_contract.py tests/repository/test_validity.py -q` 全通过；文档写正常备份/恢复、失效保真和遇不兼容库的拒绝边界。
- [ ] 7.5 提交本组 transfer.py、types.py、统一导出、test_transfer.py 与文档，说明 `feat: preserve fact state across transfer and backup`，核验未新增历史兼容协议。

## 8. 仓库独立组件验收与交付

**Files:** 创建 test_acceptance.py，更新本子变更 implementation-validation.md；不实施主集成或其它组件。

**Interfaces:** 只通过最终统一 Python API 消费任务 1–7；测试用真实 SQLite、同源公共合规 fixture，不等待查询/构造器，不 mock 全链路。

- [ ] 8.1 写跨模块 `test_repository_component_lifecycle`：多项目/多语言事实及共享主体→含证据冲突原子提交→关闭重开→局部更新和前提失效→有限关系读取→导出导入/备份恢复；每步断言精确期望公共 batch、有效/失效集合、无关 U 不变。RED：`python -m pytest tests/repository/test_acceptance.py -q`；若暴露边界缺陷保存行为失败，回相应组先补失败测试再修最小实现；若已有组合正确则保留通过证据，不伪造 RED。
- [ ] 8.2 GREEN：`python -m pytest tests/repository -q` 全通过，并从第二进程打开生命周期产物核验公共事实/证据/冲突/有效性与首进程一致；记录实际命令、退出码、测试数、七需求映射及准入资产状态到 implementation-validation.md，不沿用旧 verification 的数字。
- [ ] 8.3 将最终接口/交付路径、局部真实 SQLite 证据和剩余主集成依赖交给主变更引用；提交本组验收文件，说明 `test: verify semantic fact repository lifecycle`，核验主端到端尚未执行不被写为完成，不自动发布/归档。

### Self-Review：七项需求覆盖

| spec Requirement | design | 实施/验证组 |
| --- | --- | --- |
| 语义事实集为读写单位 | D1/D2/D3 | 1 同源保真/拒绝报告，2 精确fact/字段/关系单取，8 组合 |
| 增量维护与幂等写入 | D4 | 3 原子/重复，4 局部更新删除，5 依赖，8 |
| 结构校验及其边界 | D1/D4 | 1 结构，3 内外引用/冲突/不判语义，4 CAS |
| 当前事实有效性与一致重读 | D4/D5 | 2 重开，4 stale，5 前提/失效，8 第二进程 |
| 来源标注与源码不入库 | D2/D5 | 1 全字段，5 五类证据/不读源，7 保真 |
| 按范围精确查询与关系遍历 | D2/D5 | 2 身份/交集，6 多父环/预算/不扩权 |
| 语言无关的统一访问接口 | D3/D6 | 1 跨语言同源，2 路径/导入，7 传输，8 |

接口自审：任务 2–7 仅扩 design D3 同一 Repository/codec/types，walk 返回 TraversalResult；read_record 仅返回内部 RecordReadResult，公共批不被片段冒充；transfer封套含必要墓碑/前提身份但不含旧值/token；提交键/token始终内部；公共JSON字段由任务1绑定，不写第二协议。测试/文档随各模块落地，最终组只补跨模块验收。所有checkbox未执行；规划校验通过不表示本表产品测试通过。
