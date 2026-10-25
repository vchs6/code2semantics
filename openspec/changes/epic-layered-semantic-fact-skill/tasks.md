# Tasks

> **For agentic workers:** REQUIRED SUB-SKILL: 使用 superpowers:executing-plans 或经用户选择的 superpowers:subagent-driven-development 逐任务实施。任务勾选遵循 OpenSpec apply；本轮仅交付研究消费后的设计资产，产品实现保持 pending。

**Goal:** 交付可安装、按统一契约真实生产与查询最小分层事实的 Skill。

**Architecture:** 目录→查询契约→响应契约；确定性范围/解析/校验/仓库/查询流水线调用受约束认知接口。构造器接收已读事实而不访问仓库。

**Tech Stack:** Python、jsonschema、标准库 ast/hashlib/sqlite3、pytest；认知由宿主适配器提供。引擎选择依据design D6，工具能力以任务3/5/12实测为准。

**Spec:** 本目录 design.md、specs/semantic-fact-query/spec.md、specs/query-contract-derivation/spec.md；公共签名与类型权威为 skills/layered-semantic-facts/references/runtime-contracts.md，数据权威为 assets/。以下路径相对于仓库根。

## Global Constraints

- 先完成 survey-semantic-fact-requirements；只有报告缺失或强制要求才重入研究。本轮已经核实其 all_done 与报告摘要。
- 设计顺序：fact-catalog → contract-format → output-schema；既有设计资产的勾选不表示实现完成。
- 来源性质与知识状态独立；最小字段投影保留 context/coverage/basis；历史续查不得改绑当前。
- 不删除仓库或源项目绕过验证；不修改其它变更的proposal/specs，不按旧实现回填结构。
- 每个产品单元先写失败测试、实际观察失败，再实现和复跑；单元测试与说明随所属任务交付。命令从仓库根运行，先由任务2建立 tests/conftest.py 的 scripts 路径装载；`python`表示当前环境已配置Python与jsonschema/pytest的解释器。
- 尚未创建产品 scripts/、tests/ 或 SKILL.md；所有这些任务必须执行→产出→验证，不能只核对假想产物。

## Review Focus

- 修改与未跟踪文件改变当前快照；历史文件删除仍从保存内容复核（任务4、8）。
- 多来源同名/同行号与重叠工作空间不得合并身份（任务4、12）。
- 字段投影不得泄漏前提内容，间接前提失效须阻止充分命中（任务7、9）。
- 相同快照的新知识不能覆盖旧修订，冲突记录不能最后写入胜出（任务8）。
- 互斥条件的结构环不能宣称可运行无限循环，范围外引用不能自动读源码（任务5、7、12）。

## 1. 已落盘的设计资产

- [x] 1.1 消费已验收研究§2–§9生成 assets/fact-catalog.json 及schema、references/fact-catalog.md；验证18项F逐项有R/章节来源、L/O职责区分、研究摘要一致，所有生产状态unverified。
- [x] 1.2 从目录派生 assets/contract-format.schema.json 与common.schema.json、references/contract-format.md；验证当前/历史目标、来源绑定与非法目标正反例。
- [x] 1.3 从查询契约派生 output-schema.schema.json、pipeline.schema.json、information-needs.schema.json、capability-matrix.schema.json及接口说明；运行 `python openspec/changes/epic-layered-semantic-fact-skill/validation/validate_contracts.py`，预期7 schemas、32 positive、20 negative和8个明确尚未运行的语义案例结构通过。

## 2. 统一契约加载与错误接口

**Files:** 创建 scripts/semantic_facts/__init__.py、contracts.py、tests/conftest.py、tests/test_contracts.py；更新 references/runtime-contracts.md 的运行命令。
**Interfaces:** 产出 load_contracts(asset_dir: Path) -> ContractSet、validate_shape(kind: str, value: dict, contracts: ContractSet) -> None、ContractError(code, path, message)；全部后续模块消费同一ContractSet。

- [ ] 2.1 在 tests/test_contracts.py 写失败测试 `test_local_registry_and_contract_version`，断言所有本地$ref可解析、版本2.0.0触发code='contract_mismatch'；`test_projection_envelope_shape` 删除basis必须invalid_shape，并装载validation/schema-cases.json的全部schema案例；验证测试文件和准确断言落盘。
- [ ] 2.2 运行 `python -m pytest tests/test_contracts.py -q`，确认失败来自缺少contracts实现或预期断言失败，记录实际RED输出。
- [ ] 2.3 实现本组签名与只读目录注册、错误映射、共享schema加载；不得复制枚举或访问远程schema；说明公开错误字段与加载路径，验证代码/文档均落盘。
- [ ] 2.4 运行 `python -m pytest tests/test_contracts.py -q` 和设计资产验证脚本，全部PASS且未知版本不会读取仓库才勾选。

## 3. 生产信息需求与能力调查

**Files:** 创建 scripts/semantic_facts/requirements.py、tests/test_requirements.py、assets/information-needs.json、assets/capability-matrix.json、references/production-evidence.md。
**Interfaces:** 消费目录与两份对应schema；产出 derive_needs(catalog: dict) -> InformationNeeds、record_capability(matrix: CapabilityMatrix, result: dict) -> CapabilityMatrix；parser消费InformationNeeds。

- [ ] 3.1 写 `test_every_catalog_field_has_information_need`，断言需求的(F,field)集合等于目录全集且need_id=F.field全局唯一、Observation引用能解析；写 `test_no_verified_capability_without_nonempty_evidence`，断言空产出或缺少运行证据不能令actual_production='validated'；验证测试代码落盘。
- [ ] 3.2 运行 `python -m pytest tests/test_requirements.py -q` 并记录预期RED，不用空矩阵绕过全集断言。
- [ ] 3.3 实现两签名，逐字段产出主体/证据/环境/快照/覆盖/确定性或认知需求；以这些需求为先执行一次有界工具调查与实际可用性探测，记录Python ast、文本/配置读取及宿主归纳适配的可用证据/限制；每事实二手≤2源，缺口止损。生成需求与未验证矩阵，不预先点亮生产能力；验证schema及调查记录落盘。
- [ ] 3.4 运行 `python -m pytest tests/test_requirements.py -q`，确认全集覆盖、矩阵三个维度分开并通过schema；production-evidence.md逐项列出实测命令与限制，未验证需求仍保持待实施。

## 4. 范围、快照与主体寻址

**Files:** 创建 scripts/semantic_facts/scope.py、identity.py、tests/test_scope_identity.py；补references/contract-format.md运行说明。
**Interfaces:** 消费Query/NodeRef/SnapshotRecord；产出 capture_scope(query, cwd, source_registry) -> ScopeContext、load_historical_scope(query, repository) -> ScopeContext、identify(namespace, snapshot, boundary_evidence, role, locator) -> NodeRef，准确类型见runtime-contracts。

- [ ] 4.1 写 `test_dirty_untracked_and_multisource_snapshot`（修改未跟踪文件后snapshot改变；两个namespace同名subject不合并），`test_nested_overlap_without_unique_parent`（共享主体有两个成员关联），`test_default_scope_is_not_project`（defaulted=True且不虚造项目），`test_current_continuation_rejects_changed_snapshot`（stale_snapshot）；验证断言落盘。
- [ ] 4.2 运行 `python -m pytest tests/test_scope_identity.py -q`，记录准确RED原因。
- [ ] 4.3 实现来源注册、授权内容清单、内容哈希和身份锚点；检查捕获中变化并有界退出，历史只读保存内容；文档说明目录集合和namespace来源；验证未写分析源码。
- [ ] 4.4 运行 `python -m pytest tests/test_scope_identity.py -q` 全PASS；核对多来源分别绑定且dirty/untracked变化实际改变摘要。

## 5. 解析器与直接观察生产

**Files:** 创建 scripts/semantic_facts/parser.py、tests/test_parser.py、tests/fixtures/unique_ids.py、tests/fixtures/project_manifest.json；补references/production-evidence.md。
**Interfaces:** 消费ScopeContext/InformationNeeds；产出 parse(scope: ScopeContext, needs: InformationNeeds) -> ParseResult；Observation/evidence/context严格复用pipeline/common。

- [ ] 5.1 先创建真实可执行的有限序列去重样本（空id报错、重复跳过、首次追加）及独立边界清单；写 `test_nonempty_direct_observations`（observations非空、定位/摘要复核、循环和调用观察可见），`test_external_reference_never_reads_outside`（外部源码读取次数为0），`test_manifest_missing_is_insufficient_not_absent`；验证源样本可执行且测试落盘。
- [ ] 5.2 运行 `python -m pytest tests/test_parser.py -q`，记录缺少解析器的RED；不能用预制FactBatch满足非空生产断言。
- [ ] 5.3 实现授权文本/清单/配置证据读取和Python ast直接观察，保留主体、字段需求、位置、快照和直接分析关系；其它语言保留可定位观察及受约束认知需求而不虚称确定性支持；验证ParseResult通过schema。
- [ ] 5.4 运行 `python -m pytest tests/test_parser.py -q` 全PASS，production-evidence记录真实观察数量/位置与实际未覆盖项，只有该路径真实验证的能力才能更新矩阵。

## 6. 构造与受约束归纳

**Files:** 创建 scripts/semantic_facts/constructor.py、induction.py、tests/test_constructor_induction.py；补references/runtime-contracts.md宿主调用说明。
**Interfaces:** 消费ConstructRequest(query,known,missing,parsed)；产出 construct(request, induce) -> ConstructResult、prepare_induction(subject, requested, parsed, known) -> InductionRequest、validate_induction(request, result) -> ConstructResult。induce回调签名为 Callable[[InductionRequest],ConstructResult]。

- [ ] 6.1 写 `test_known_and_direct_edges_preserved`（已知事实及直接分析边不丢），`test_constructor_has_no_repository_access`（仓库不可传入且访问哨兵从未触发），`test_missing_selectors_are_target_specific`（A同字段命中不能抵消B的missing；selector与gap目标快照一致），`test_induction_rejects_subject_snapshot_field_drift`（错误主体/快照/字段均拒绝），`test_interpreted_insufficient_is_not_supported`；验证失败测试落盘。
- [ ] 6.2 运行 `python -m pytest tests/test_constructor_induction.py -q`，记录RED。
- [ ] 6.3 实现三个接口，认知请求必须包含明确主体/字段组/证据/上下文/快照；只针对missing调用，保留known而不擅自改修订，归纳结果通过统一契约再交调用者入库；验证无Repository参数或导入。
- [ ] 6.4 运行 `python -m pytest tests/test_constructor_induction.py -q` 全PASS；区分测试回放与真实宿主归纳，真实生产留任务12验收，不能用mock结果标生产完成。

## 7. 跨引用、证据与知识语义验证

**Files:** 创建 scripts/semantic_facts/semantic_validation.py、tests/test_semantic_validation.py；完善references/runtime-contracts.md V1–V9。
**Interfaces:** 消费FactBatch、ScopeContext、ContractSet与 premise_lookup: Callable[[dict],Fact]；产出 validate_batch(batch, scope, contracts, premise_lookup) -> None，失败为统一ContractError。

- [ ] 7.1 写测试驱动 validation/semantic-cases.json 的8个案例，并断言候选target/conditions和参数parameter/argument配对按共享shape一致，逐项断言expected拒绝理由；补 `test_transitive_premise_closure_and_self_cycle`、`test_condition_conjunction_not_edgewise_possibility`、`test_absence_requires_domain_and_checked_evidence`；前提版本失效返回invalid_premise，f与not-f不能判可运行环；验证断言落盘。
- [ ] 7.2 运行 `python -m pytest tests/test_semantic_validation.py -q`，确认所有非法语义尚未被缺失实现拒绝的RED，不以schema通过跳过。
- [ ] 7.3 实现V1–V9相关入库规则：引用/类型/域/证据摘要/前提闭包/条件及范围；未知一般条件保留unknown；说明结构校验与语义校验边界，验证实际执行到证据与传递前提。
- [ ] 7.4 运行 `python -m pytest tests/test_semantic_validation.py -q` 全PASS，8语义反例此时才可记为运行验证通过。

## 8. 事务仓库、重读与不可变知识修订

**Files:** 创建 scripts/semantic_facts/repository.py、tests/test_repository.py；补references/runtime-contracts.md持久化说明。
**Interfaces:** 消费所有共享数据契约和validate_batch；产出 Repository(path, contracts)、put(batch, scope) -> str、read(query, scope) -> ReadResult、read_revision(premise) -> Fact、save_scope(scope, content) -> None。

- [ ] 8.1 写 `test_commit_close_reopen_read_nonempty`（关闭连接再开后事实非空且身份/证据/快照相同），`test_same_snapshot_revision_and_conflicts_preserved`（revision1仍可读、revision2并存），`test_historical_evidence_after_source_deletion`（仅删除测试临时源文件后历史仍可读），`test_invalid_data_rolls_back_without_deleting_database`（事务回滚且原库仍在）；验证用独立临时目录。
- [ ] 8.2 运行 `python -m pytest tests/test_repository.py -q`，记录RED，不允许内存dict替代跨连接持久化检查。
- [ ] 8.3 实现SQLite事务及不可变修订，存scope与内容快照；读时验证前提闭包，ReadResult.rejected保留确切原因；不兼容数据显式错误不删除，记录可验证转换流程；验证模块落盘。
- [ ] 8.4 运行 `python -m pytest tests/test_repository.py -q` 全PASS，检查实际SQLite重开、内容重读及回滚证据。

## 9. 覆盖比较与最小投影

**Files:** 创建 scripts/semantic_facts/coverage.py、projection.py、tests/test_coverage_projection.py；补references/output-schema.md。
**Interfaces:** 消费有效FactBatch/Query/ScopeContext；产出 compare(query, known) -> list[dict]、project(query, scope, valid, missing, termination) -> Response。

- [ ] 9.1 写 `test_requested_goal_only_with_complete_envelope`（goal存在，complexity与未请求前提内容不在结果，context/coverage/basis仍在），`test_direct_next_level_only`（subtree无后代值，跳层和同层递归均可导航），`test_out_of_catalog_separate_from_missing`，`test_unknown_empty_is_not_covered`；验证断言落盘。
- [ ] 9.2 运行 `python -m pytest tests/test_coverage_projection.py -q`，记录RED。
- [ ] 9.3 实现字段白名单、目标直接下一级验证和带信封投影；未知/不足/冲突不冒充已满足，合法未解析外部引用仍可呈现；验证Response通过同一schema并记录运行示例。
- [ ] 9.4 运行 `python -m pytest tests/test_coverage_projection.py -q` 全PASS，检查投影前后否定成立域与证据完全相同。

## 10. 有界查询编排与命令入口

**Files:** 创建 scripts/semantic_facts/query.py、cli.py、__main__.py、tests/test_query.py；补references/runtime-contracts.md可运行命令。
**Interfaces:** 消费Repository、construct、compare、project；产出 execute(query, cwd, repository, induce) -> Response、main(argv: list[str] | None = None) -> int。

- [ ] 10.1 写 `test_exact_revision_readonly_and_explicit_refresh`（精确rev1缺字段时构造次数0；refresh同快照产生rev2、resolved_target指rev2且原rev1仍可读），`test_read_construct_put_reread_project_order`（允许构造时实际仓库重读后才合成），`test_no_progress_terminates_preserving_known`（无进展终止且已知字段仍在），`test_budget_exhaustion_explicit`（max_rounds=1不重复调用），`test_contract_mismatch_before_repository_read`（错误请求读仓库次数0）；验证断言落盘。
- [ ] 10.2 运行 `python -m pytest tests/test_query.py -q`，记录RED。
- [ ] 10.3 实现签名及有界循环、缺口原因传递、stdout JSON/stderr错误协议；精确node与historical不构造；refresh同快照显式选择latest并返回新continuation，源码变化仍stale_snapshot。同快照有效覆盖增量才算进展，禁止用调用次数或重复事实假造进展；验证CLI运行示例落盘。
- [ ] 10.4 运行 `python -m pytest tests/test_query.py -q` 全PASS，并执行 `python -m semantic_facts query --request tests/fixtures/request.json --repository <临时库路径>` 得到合法机器响应。

## 11. Skill安装、对话派生与可选报告

**Files:** 创建 skills/layered-semantic-facts/SKILL.md、INSTALL.md、requirements.txt、references/dialogue.md、references/report-template.md、scripts/install.py、tests/test_packaging_dialogue.py。
**Interfaces:** 安装入口 main(argv: list[str] | None = None) -> int（install.py），接受 --destination PATH；复制完整单Skill包和自包含相对资源。宿主从dialogue.md产生Query，再调用CLI，显式报告请求才采用report-template.md消费Response。

- [ ] 11.1 写 `test_install_outside_repository_uses_packaged_assets`（仓库外拷贝可运行且不读取原repo），`test_dialogue_defaults_scope_and_clarifies_intent`，`test_report_only_on_explicit_request_and_same_facts`（缺口/解释/否定状态不升级）；编写规范对照断言name、description、compatibility及正文<500行，验证测试落盘。
- [ ] 11.2 运行 `python -m pytest tests/test_packaging_dialogue.py -q`，记录缺少包/入口的RED。
- [ ] 11.3 生成并实现上述文件与安装程序，按Agent Skills布局和渐进披露；宿主对话只派生同一契约，不引入第二事实源；记录安装/运行/报告真实操作说明，验证资产相对定位可用。
- [ ] 11.4 运行 `python -m pytest tests/test_packaging_dialogue.py -q` 全PASS，运行 `skills-ref validate skills/layered-semantic-facts`；不可用则按AGENTS采用的规范逐项写入规范对照记录并判定通过，不能假称已运行官方工具。

## 12. 真实非空生产与全部场景验收

**Files:** 创建 tests/test_acceptance.py、tests/fixtures/scenarios/、tests/fixtures/cross_language/、references/acceptance-results.md；更新assets/capability-matrix.json和production-evidence.md。
**Interfaces:** 只通过已交付CLI/Repository/宿主归纳接口运行，不直写最终响应；验收场景映射见traceability.md。

- [ ] 12.1 先为研究S1–S12建立可执行真实材料与预期断言，并写跨语言溢出/异常差异测试及端到端测试；去重必须实际验证 [b,a,b]→[b,a]、[]→[]、空id错误；运行 `python -m pytest tests/test_acceptance.py -q` 并记录首次RED或仍未覆盖的真实生产缺口，未真实产出不能通过。
- [ ] 12.2 从干净临时仓库和仓库外安装目录执行真实解析及一次真实宿主归纳，验证非空生产→校验入库→关闭重开→重读→最小字段查询；覆盖多来源身份、组织/依赖分离、外部边、嵌套/重叠、环联合条件、内部算法与限定否定。按字段登记原始输出、证据、命令、环境及未覆盖项，不能用mock或gap-only完成。
- [ ] 12.3 运行 `python -m pytest tests/test_acceptance.py -q` 及全部产品测试，逐项核对主两spec/traceability.md；表达能力、实际生产能力、运行验证分别报告。所有提案所要求能力与场景有真实证据且安装验收通过才勾选；任何未满足项保持pending并报告，不静默缩小范围。

## Workflow follow-up

- 本轮只交付规划与契约，不执行第2–12组产品任务；后续按主变更 apply逐项推进。
- 运行OpenSpec strict validate和独立审查；归档需要用户确认，归档不计入上述实施进度。
