# 运行接口与语义校验职责

这些是待实现的公共接口，不表示已有产品程序。统一数据权威为 assets/ 下的目录和 JSONSchema；Python TypedDict/dataclass 可以生成或加载这些结构，但不得另写不一致的字段枚举。路径以 `skills/layered-semantic-facts/scripts/semantic_facts/` 为模块根，测试放 `tests/`。

## 公共类型和所有权

| 名称 | 唯一数据定义 | 所有者与作用 |
| --- | --- | --- |
| Query / Response | contract-format.schema.json / output-schema.schema.json | 查询入口与所有调用方 |
| NodeRef / Assertion / Evidence / Context / Coverage | common.schema.json $defs | 全部消费者共享 |
| Fact / SnapshotRecord | output-schema $defs.fact_node / common $defs.snapshot_record | 存储、查询、构造共同采用 |
| FactBatch / NavigationEdge | pipeline.schema.json $defs.fact_batch / navigation_edge | 事实与导航分开存储；导航允许多父、跳层和回边 |
| ParseResult / Observation | pipeline $defs.parse_result / observation | 解析器只产生可定位观察及明确未满足项 |
| ConstructRequest / ConstructResult | pipeline $defs.construct_request / construct_result | 构造消费 known、missing、parsed 并返回增量；不访问仓库 |
| InductionRequest | pipeline $defs.induction_request | 显式主体、字段组、观察、证据、快照和上下文；结果采用 ConstructResult |
| InformationNeeds / CapabilityMatrix | information-needs.schema.json / capability-matrix.schema.json | 需求与能力验证，不伪造已验证记录 |
| ScopeContext | 下面定义的运行值 | 宿主授权与捕获上下文，不作为新的事实契约 |

ScopeContext 的准确字段：scope_id: str、directories: tuple[str,...]、excludes: tuple[str,...]、defaulted: bool、source_roots: dict[str,str]、snapshot_set_id: str、snapshots: list[SnapshotRecord]、mode: Literal['current','historical']。source_roots 仅定位已授权来源，不以根目录决定软件主体身份。

以下是函数签名契约；dict 型数据均指表中对应 JSONSchema，禁止定义平行 JSON 变体。repo_path/config 可由宿主显式传入，不将源项目写作仓库目录。

| 模块 | 公共签名 | 必需行为 |
| --- | --- | --- |
| contracts.py | load_contracts(asset_dir: Path) -> ContractSet; validate_shape(kind: str, value: dict, contracts: ContractSet) -> None | 本地 $ref registry，版本与目录一致；结构失败抛 ContractError(code, path, message) |
| scope.py | capture_scope(query: Query, cwd: Path, source_registry: Path) -> ScopeContext; load_historical_scope(query: Query, repository: Repository) -> ScopeContext | 捕获内容清单、dirty/untracked/排除/配置并分别绑定来源；历史只能读保存快照 |
| identity.py | identify(namespace: str, snapshot: str, boundary_evidence: list[Evidence], role: str, locator: str) -> NodeRef | 标识含来源/版本/边界锚点，不能只散列名称与行；跨版本身份对应以有证据的F18表达 |
| requirements.py | derive_needs(catalog: dict) -> InformationNeeds; record_capability(matrix: CapabilityMatrix, result: dict) -> CapabilityMatrix | 逐字段信息需求/判定记录；validated 必须引用实测非空事实及测试证据 |
| parser.py | parse(scope: ScopeContext, needs: InformationNeeds) -> ParseResult | 只读授权材料，产出证据化观察；直接分析边保留；不写仓库 |
| induction.py | prepare_induction(subject: NodeRef, requested: list[dict], parsed: ParseResult, known: FactBatch) -> InductionRequest; validate_induction(request: InductionRequest, result: ConstructResult) -> ConstructResult | 宿主承接认知调用；确定性校验主体/字段/证据/快照/上下文与未满足项；不得扩权 |
| constructor.py | construct(request: ConstructRequest, induce: Callable[[InductionRequest], ConstructResult]) -> ConstructResult | 接收已读 known，保留已知断言及直接分析边，只构造缺口；无 Repository 参数，也无仓库导入或写入 |
| semantic_validation.py | validate_batch(batch: FactBatch, scope: ScopeContext, contracts: ContractSet, premise_lookup: Callable[[dict], Fact]) -> None | 下面 V1–V9 入库校验，闭包迭代访问并检测循环，拒绝自证前提 |
| repository.py | Repository(path: Path, contracts: ContractSet); put(batch: FactBatch, scope: ScopeContext) -> str; read(query: Query, scope: ScopeContext) -> ReadResult; read_revision(premise: dict) -> Fact; save_scope(scope: ScopeContext, content: dict[str,bytes]) -> None | SQLite 事务写入；read 调用闭包验证；版本不兼容显式错误，原记录不删；保存内容与不可变修订 |
| coverage.py | compare(query: Query, known: FactBatch) -> list[dict] | 按target+F+field比较有效适用断言；空/未知不算满足；返回带selection_target的missing selectors |
| projection.py | project(query: Query, scope: ScopeContext, valid: FactBatch, missing: list[dict], termination: str) -> Response | 对直接下一级和字段白名单投影；信封不裁剪；前提内容不外泄 |
| query.py | execute(query: Query, cwd: Path, repository: Repository, induce: Callable[[InductionRequest], ConstructResult]) -> Response | scope当前或显式refresh采用read→compare→construct→validate→put→read→compare；精确node及historical只读/比较/投影，不构造；进展签名按新增有效字段覆盖及有效修订，不按调用次数冒充进展 |
| cli.py | main(argv: list[str] | None = None) -> int | query --request PATH --repository PATH；stdout 仅 JSON；错误 stderr 结构化并非零退出；无效契约不查询仓库 |

精确node引用是只读知识修订；缺字段返回带该node的gap，不在原revision上构造。refresh仅限当前同源码快照，允许读取latest并构造，put后read latest再在resolved_target返回新revision；旧引用仍可读旧revision。historical不构造。Repository.read按Query.target.kind选择exact/latest，不能在内部静默切换；scope当前查询可构造。

ContractSet = 持有目录、JSONSchema registry 和版本的只读对象。ContractError 是统一异常，code 限定为 invalid_shape、contract_mismatch、invalid_reference、stale_snapshot、invalid_evidence、invalid_premise、invalid_coverage、out_of_scope；代码与失败路径测试固定。read_revision 对找不到的确切修订抛 invalid_premise，不读最新替代。ReadResult = pipeline.schema.json $defs.read_result，含 known: FactBatch 与 rejected: list[Gap]；无效闭包字段由 compare(query, result.known) 形成缺口，query将rejected的精确原因交给project，不把 invalid_premise 降为普通未发现。

## 必须由运行程序检查的规则

- V1 目录闭合与配对：每字段value_shape须解析到common共享定义；candidate_set的target/conditions配对不得分离，F10.targets与target_conditions若同时存在，按同一目标和条件对应；binding_set保留parameter/argument配对，edge_set保留端点/条件。need_id为单字段F.field并全局唯一，Observation.information_need_id必须存在且匹配生产字段。selector和gap均按target+F+field寻址，禁止跨主体借用命中。
- V1 目录闭合：输出/入库字段只属对应 F；源/目标/主体字段必须含结构化引用，方向与种类适用，不能用任意文本逃逸引用校验。F4 的 kind 只允许 physical_contains/workspace_member/logical_belongs/internal_composition；F6 的 kind 只允许 build/code_interface/runtime/data/deployment；F18 的 kind 只允许 implements/refines/summarizes/corresponds。语义值编码为 text；这些值由目录字段说明和实现校验锁定。其它研究词汇允许保留说明与原始语义，不擅自收缩需求。
- V2 身份与范围：所有已解析主体在命名域和快照内存在，引用匹配源注册表；引用文本并非身份。outside_scope 未解析引用可保留 observed_in，但不得据此打开外部源码。重复 node ID 不可合并不同边界。导航索引的父子是查询视图，不能删除回边或限制唯一父。
- V3 快照集合：context、evidence、premises、node 与集合逐项一致；集合摘要以规范化排序后的 namespace/snapshot 对计算。多来源同名不能互换；当前捕获期间变化则重试有限次后 stale_snapshot，历史不访问当前源码。
- V4 证据：content_digest 与不可变保存内容一致，定位在该内容内；支持/反驳不能乱标。直接观察只支持实际读到的声明/事件。来源不存在、不可定位、版本错配不入库。
- V5 否定：negative.domain 等于 coverage.domain；check_evidence_ids 全部指向该断言支持证据；检查方法确实覆盖声明对象域/条件，excluded 不与否定域交叠；“扫描未发现”不足以证明运行/反射域无引用。
- V6 前提闭包：精确按 node+revision+field 读取所有传递前提；验证快照、有效知识与环境/条件适用，禁止自证环，冲突或证据不足的前提不能被隐式升级为充分结论。解释不足可保存，但不作为“满足充分事实需求”的命中。
- V7 最小投影：query→results 的类型/字段/目标/直接下级一致；subtree 不带后代字段；所有叶子信封完整；前提只以引用出现；out_of_catalog 与目录内 gaps 互斥归类。
- V8 条件与循环：逐边保留条件作用域；初版只确定处理显式同域布尔文字的联合矛盾与实际观测路径，其它条件表达保持 unknown 并列出未决项，不宣称任意逻辑可判定。结构环与执行无限性分开。
- V9 生产真实性：每个 validated 能力记录指向可运行样本、非空输出、持久化重读与投影检查；伪造字段/缺口-only/仅 JSONSchema通过都不能点亮能力。目录表达能力与实际工具能力分别列出。

JSONSchema提供这些规则的必要结构条件，不能完成上述跨记录语义判断。本轮 validation 的 semantic-cases.json 是未来实现的拒绝/保留预期，不记作已通过生产验证。

## 确定性实现与认知边界

Python（jsonschema + 标准库 pathlib/hashlib/ast/sqlite3）是当前实现选择：报告R1/R15/R16要求精确范围、证据和追踪，AGENTS原则7要求可程序化职责确定实现；这些约束支持程序/事务/不可变版本职责，研究没有比较语言或数据库，不能声称研究证明Python/SQLite最优。SQLite 先承载 source_snapshots、subjects、facts、navigation、evidence、premises、scopes 与 knowledge_revisions 逻辑记录；具体物理索引依实测，不将表数当语义层数。所有写入经 Repository，构造器不碰存储。

解析先以授权文本/配置/清单的定位观察和 Python ast 的直接元素/调用/控制观察建立可测基线；其它语言通过同一证据化观察和受约束归纳接口表达，不能靠后缀虚称支持。实际工具选择须在任务3用需求矩阵逐项实测，任何不足保留任务与缺口。接口契约不因此只支持Python；跨语言行为差异必须在真实材料场景验证。认知输出可归纳职责/意图，但必须经同一入库校验，不能直接写最终响应。首次生产验收必须使用真实宿主归纳输出及来源；回放输出只作回归，不能代替一次真实生产。
