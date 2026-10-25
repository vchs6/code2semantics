# Design

## Context

动机与授权范围见 [proposal.md](proposal.md)，行为权威为 [specs/semantic-fact-repository/spec.md](specs/semantic-fact-repository/spec.md) 的七项 Requirement。本轮只新增规划工件；仓库产品入口、脚本、测试尚不存在，旧 `verification.md` 不是当前实现或本轮验收证据。

主 [design.md](../epic-layered-semantic-fact-skill/design.md) D1/D2/D5/D6/D7/D8 拥有公共事实、证据、来源上下文、有效性与冲突契约，以及跨组件集成。现有 `skills/layered-semantic-facts/assets/`、`references/` 仍含旧协议，不能作为仓库实现输入。开始产品实施前 MUST 通过下述公共契约准入；设计完成不代表该准入满足。

已有依据：[storage-survey.md](research/storage-survey.md) OQ1 支持实体/属性/显式关系分离与定向索引，OQ4 支持本地 SQLite 文件；OQ2 的路径行号占位身份、OQ3 的长期历史与显式版本参数与最新 proposal 冲突，不采用。本设计采用既定 Python + SQLite，并把内部布局与一致性策略明确作为当前工程取舍，不声称研究证明其性能最优。

[事实需求报告](../survey-semantic-fact-requirements/research/semantic-fact-requirements.md) R1/R2、O1/O2、S1–S8 要求身份和范围独立；R15/F17/O4/S12 要求证据、知识状态和限定否定保真；R16/F18、S8–S10 支持多父、跳层及环。不重新调研层次。

## Goals / Non-Goals

**Goals:** 通过确定性 Python 程序提供可单取、更新、失效及删除的实体属性与显式关系；跨实体批次使用真实 SQLite 事务；保真存取公共事实及其证据/状态，按范围过滤并有限遍历；用 pytest 验证重开重读、原子性、依赖失效和恢复。

**Non-Goals:** 不构造事实、不判断软件语义正确性、不核实当前源码、不计算查询覆盖充分性、不投影 Response；不实现工具、解析器、矩阵或研究调度；不建设 HTTP 服务、多客户端框架、历史查询、用户 snapshot/revision/refresh、旧协议兼容或数据迁移工具；不管理整源副本。本轮不实施、发布或归档。

## Decisions

### D1 公共契约准入与单客户端边界

依据 proposal 的公共契约归属、主 D1/D5–D8：仓库只接受最新公共 FactBatch 所含结构化事实、证据、来源上下文、有效性及冲突，通过同源 schema 校验并重建同源记录。实现前，主变更 MUST 已完成以下交付并有真实通过证据：

1. `assets/fact-catalog.json` / `fact-catalog.schema.json`，`contract-format.schema.json`，`output-schema.schema.json` 及 D1 指定共享 schema、references 同步迁移；FactBatch 与 Response 分离，主体/来源域、范围外引用、每字段 context/coverage/basis、必要前提、origin/knowledge、完整性、冲突和有效性的机读表示可定位。
2. 主 `validation/validate_contracts.py` 对上述资产及正反例通过，包含拒绝旧 revision/snapshot/refresh/response 存储外壳的反例；主工件记录与校验器实际命令一致。
3. 本子变更任务 1 记录实际 schema JSON Pointer → 内部列/边的绑定与 fixture 来源，并验证重建结果仍满足同一公共 schema。任何语义未定义、字段丢失或资产仍旧时停止该任务，报告主变更缺口；不得自行发明公共字段补齐。

内部 Python 参数、列名与错误类型不属于公共 wire 协议。边界模块仅映射最新同源结构，不提供旧协议适配。唯一调用者是 Skill 的查询流程；通过 Python 导入统一接口，不新增服务端或命令行产品入口。

被否备选：沿用旧 output-schema 会把响应与历史协议带入存储；复制公共 schema 到仓库会形成第二权威；等待查询/构造器实现才测仓库会失去组件独立验收。依据主 D7，合规 fixture 足以验证仓库，不证明生产链路。

### D2 内部实体布局、身份与保真

依据 spec“语义事实集为读写单位”“按范围精确查询”、报告 R1/R2/R15/F17/F18 和 storage-survey OQ1：采用以下内部关系布局。所有 `*_key` 是提交方公共身份经无损域组合得到的键，不从名称、路径、行号或唯一父推导；相同主体可有多个类型/上下文的事实。工作空间成员关系单独存边，不把同一主体按父复制。不同来源域、项目或权威身份不同的同名主体不合并。

| 表 | 内部主键和职责 | 主要索引/约束 |
| --- | --- | --- |
| `entities` | `entity_key`，保存公共主体身份及其来源域，`deleted` 墓碑和内部 `token` | 域与公共主体身份唯一；域/项目索引 |
| `facts` | `fact_key`，`entity_key`、`fact_type`、来源上下文及断言级状态，`token`、`deleted` | 主体/事实类型、来源域、有效性索引；不以 `(entity,type)` 唯一化 |
| `attributes` | `(fact_key, field_path)`，每个可独立寻址字段一行，保存值及该字段公共元信息 | `(fact_key,field_path)`；字段路径索引，不预设任意 JSON 值性能保证 |
| `relations` | `relation_key`、所属事实/字段、类型、方向、内部端点键或外部引用值及公共元信息 | 起点/类型与终点/类型索引；内部端点延迟外键，外部引用不伪造实体 |
| `evidence` / `evidence_links` | 公共证据身份或批内无损局部键、证据值；断言/字段与证据关联 | 证据键、关联拥有者索引；支持/反驳关系保真 |
| `premises` | 依赖断言/字段到必要前提断言/字段的边及所依赖内部 token | 前提反向索引；非语义关系，不自动当事实边 |
| `conflicts` / `conflict_links` | 公共冲突记录与参与事实/字段；冲突不被新候选覆盖 | 拥有者与参与者索引 |
| `submissions` | 内部提交键、规范化操作摘要及提交确认 | 提交键唯一；仅用于幂等确认，无用户历史查询 |

所有可维护主记录（实体、事实、属性、关系、证据、冲突）都有内部 `token` 与 `deleted`；关联表随拥有者事务维护。字段、关系、共享证据及冲突变更同时推进所有受影响所属事实 token，防止旧整事实更新覆盖局部变更。身份和字段值中的 JSON 可逐值保存；字段数组、复杂语言表达、原始语义引用及公共扩展保留其顺序和结构。公共记录中的全部字段必须被边界映射覆盖，未映射字段拒绝，而非静默投影丢失。不能把整个 FactBatch/Response 存成一行 blob；每个事实和字段可以独立读取及维护。断言级与字段级 context/coverage/basis、origin/knowledge、完整性、限定否定域、证据和有效性保留原层级，不能挪成全局摘要。父节点的存在或 child 引用不能生成完整覆盖声明。

被否备选：整响应 blob 不支持单取；单实体单事实会覆盖多类型和冲突候选；树形 parent 列丢多父及环；通用语言专属表增加第二套语义。OQ1 是布局参考，不沿用其中未经基准验证的“每表单索引”或优化必然结论。

### D3 确定性接口与模块职责

依据主 D6、AGENTS 原则 7 及上述边界，未来文件均位于 `skills/layered-semantic-facts/scripts/semantic_facts/`，测试位于 `tests/repository/`。包内使用相对导入，不依赖工作目录。

| 文件 | 单一职责 |
| --- | --- |
| `repository/types.py` | 内部不可变操作、键、过滤器、结果和错误类型 |
| `repository/contract.py` | 加载主同源 schema，公共记录结构校验、无损拆解/重建；记录实际字段绑定 |
| `repository/store.py` | SQLite 连接、DDL、事务写入、精确读取、必要前提检查和显式边有限遍历 |
| `repository/transfer.py` | 当前合规事实集导出/导入和 SQLite 一致备份/恢复校验 |
| `repository/__init__.py` | 仅导出 Skill 使用的统一 Python API |
| `tests/repository/conftest.py` | 最新公共契约合规 fixture 与临时 SQLite 路径，非全链路 mock |

`JsonObject = dict[str, object]` 只表示尚未校验的 JSON 对象；公共结构精确类型/字段由主定义消费，不能以此别名绕过 schema。内部具体接口：

- `ContractCodec(schema_root: Path)`；`validate_batch(batch: JsonObject) -> None`，`decode(batch: JsonObject) -> tuple[StoredRecord, ...]`，`encode(records: Sequence[StoredRecord]) -> JsonObject`。`StoredRecord` 包含上表各行的类型化集合，并保存全字段绑定；仅供仓库内部。
- `RecordKey(kind: Literal['entity','fact','attribute','relation','evidence','conflict'], key: str, field_path: str | None = None)`；键来自公共身份和域，字段键引用所属事实及路径。
- `Mutation(action: Literal['create','update','invalidate','delete'], target: RecordKey, payload: JsonObject | None, expected_token: str | None)`；payload 是目标对应的完整公共记录/字段值与元信息；create 无 expected_token，其余必须提交维护读得到的 token。失效 payload 保留公共失效原因和来源上下文；删除不要求整模型。
- `ChangeSet(submission_key: str, mutations: tuple[Mutation, ...])`；`CommitReceipt(submission_key: str, digest: str, affected: tuple[RecordKey, ...])`。
- `FactFilter(project_keys: tuple[str, ...], subjects: tuple[str, ...] = (), fact_types: tuple[str, ...] = (), validity: Literal['valid','all'] = 'valid')`。项目键和主体键均为公共域限定身份；空项目集合返回空，不表示全库；所有非空过滤条件取交集。
- `RecordReadResult(target: RecordKey, value: object, metadata: JsonObject, token: str, valid: bool, deleted: bool)` 是内部精确记录结果：value 为目标公共记录或字段值，metadata 保留其所属身份、字段状态与必要证据/上下文；删除墓碑的 value 为 None。它不声明是可独立提交的公共 FactBatch。
- `ReadResult(batch: JsonObject, tokens: dict[RecordKey, str])`；batch 保持公共事实格式，内部 token 与公共结构分开，不要求用户 revision。
- `Repository(path: Path, codec: ContractCodec)`：`apply(changes: ChangeSet) -> CommitReceipt`；`read(filters: FactFilter) -> ReadResult`；`read_record(target: RecordKey, project_keys: tuple[str, ...], validity: Literal['valid','all'] = 'valid') -> RecordReadResult | None`；`walk(start: str, filters: FactFilter, relation_types: tuple[str, ...], max_depth: int, max_edges: int) -> TraversalResult`；`close() -> None`。
- `TraversalResult(records: ReadResult, truncated: bool, reason: Literal['depth','edges'] | None)` 将遍历截断与公共事实自身的 coverage 分开；`open_repository(path: Path | None, codec: ContractCodec) -> Repository` 负责 D6 路径解析。
- `export_current(repo: Repository, destination: Path) -> None`；`import_current(repo: Repository, source: Path, submission_key: str, project_keys: tuple[str, ...]) -> CommitReceipt`；`backup(repo: Repository, destination: Path) -> None`；`restore(backup_path: Path, destination: Path, codec: ContractCodec) -> None`。

`ContractError(location, reason)` 定位公共字段，`ReferenceError(target)` 定位非法引用，`WriteConflict(target, reason)` 区分创建冲突、陈旧写和提交键重用，`StorageError(reason)` 表示不可完成存储操作。错误均不返回成功确认。公共业务冲突与本地写冲突分开：不同事实 ID 的矛盾候选与公共冲突记录可一起保存，同一 ID create 不同内容必须拒绝。

被否备选：将接口交给运行代理按文档手工执行不确定；大框架/HTTP 不符合单客户端范围；将内部比较令牌写成公共版本协议违背 proposal。

### D4 原子变更、幂等、显式更新与删除

依据 spec 增量维护及跨连接重读，storage-survey OQ1 的实体访问建议，并采用 [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html) 的事务全或无机制与 [foreign keys](https://www.sqlite.org/foreignkeys.html) 的每连接启用及延迟约束：每连接启用并核实外键，使用单库 `BEGIN IMMEDIATE` 写事务。先校验整批和批后引用视图，再在同一事务写入事实、属性、边、证据、有效性、冲突、前提及提交确认；提交失败回滚全部。允许同批新增相互引用主体及环，不允许最终状态留下非法内部引用。锁忙返回可定位 StorageError，不自动重跑认知工作。

提交键由 Skill 内部调用者提供；摘要覆盖规范化操作、目标、内容和 expected_token，JSON 对象键排序、数组保序、拒绝非 JSON/非有限数。相同提交键同摘要先返回原确认，即使 token 已变化；同键不同摘要拒绝。相同目标 create 同内容为无变更幂等，不生成重复；同 ID create 不同内容是冲突。合法 update 必须显式 action 和匹配 token，只替换指定字段/事实，维护同批证据和状态；不以 last-write-wins 静默覆盖。每次真实修改产生新的内部不可复用 token；跨连接读旧 token 的写被拒绝。事务内重复修改同一目标拒绝；父事实整体更新与其字段操作重叠也拒绝，消除顺序歧义。

删除采用当前记录墓碑，不提供历史值。删除事实后不再出现在事实读取；删除实体使其所属事实/属性/关系一起删除或失效；调用方必须在同批删除/失效所有受影响入边与必要前提依赖，缺少必要影响声明整批拒绝。关系的失效引用可指向墓碑用于内部维护，不能成为有效边；墓碑是已知被删除内部身份，不能转换为范围外引用。保留被引用证据，未引用证据允许显式删除；删除被有效事实使用的证据同样要求事务内维护影响。完全物理清除及历史回收不是当前任务。

变更/失效一个事实或字段时，所有显式必要前提的传递依赖须在同事务失效/重建，否则拒绝；循环用已访问集合收敛。只处理已提交的必要依赖，不猜测语义影响。查询流程负责来源变化的影响范围；本仓库不能发现未声明的语义依赖。无关实体、事实及 token 保持原样。

被否备选：逐行自动提交会留下半批；仅 append 无法更新/删除；无条件 UPSERT 隐藏冲突；立即外键拒绝合法同批循环；自动把缺目标变成 external 会扩权。原子机制的官方依据不代替本仓库的冲突策略选择。

### D5 当前有效读取与有界显式图访问

依据 spec 当前有效性、来源边界和关系遍历，主 D2/D5/D8，报告 R1/R15/F17/S12：读取在同一 SQLite 读事务中选择匹配事实并组装必要证据/冲突/来源上下文。默认只返回未删除且公共有效性有效的事实/字段/关系，并检查每条必要前提的当前有效状态、所引用 token 和传递闭包；缺前提、前提墓碑、失效或 token 不符则排除依赖断言。必要前提循环不会无限递归，循环内任一前提无效导致该依赖闭包无效；结构环本身不视作语义错误。维护读 `validity='all'` 可读失效记录并保留公共失效标志及内部 token；墓碑仅用于引用检查，不作为有效事实返回。

`read_record` 按完整域限定键精确单取实体/事实/字段/关系/证据/冲突，不带回同主体同类型的其它上下文事实；空授权项目集合或域不符返回 None，有效模式应用相同前提检查，维护模式可获得失效记录及墓碑标记。字段片段不删减后伪装合法公共批，公共 `read` 仍返回合法完整事实批及必要支持记录，二者都不改写 coverage/完整性。

read 不读源文件，不据旧定位存在推断有效，不自行恢复有效性。源码、清单、配置、文档、观察证据按公共契约保留定位和内容状态；不复制整个项目，不要求保留历史整源。公共完整性/覆盖声明即使不充分也原样保留，仓库不把“存在父及部分 child”升级为 covered，不抹掉限定否定的检查域和依据。

walk 只沿已提交显式边，对域限定主体与关系身份分别去重，保留多父及回边。`max_depth >= 0`、`max_edges > 0` 为必填边界；深度 0 只读起点，出界参数报错。按稳定边键排序，每条边最多返回一次；达到深度/边预算且仍有未走匹配边时设置内部 TraversalResult 截断信息；不更改已存事实的公共 coverage/完整性声明，不生成“完整”声明。只返回授权项目集合中的实体，合法 external 端点原样保留且不扩展、不读取来源；空关系类型集合不走边。图访问以已访问集合和有限队列实现，必要时逐层 SQL 查询；[SQLite WITH 文档](https://www.sqlite.org/lang_with.html) 第 3 节图查询的循环控制说明此边界必要，不要求使用递归 CTE。

被否备选：只过滤本事实有效位会泄漏过期推导；读取全模型再裁剪损害精确访问；将图展开成树丢关系身份；递归源读取或推导缺边越过仓库职责。

### D6 当前数据导入、导出、备份与交付

依据 spec 语言无关统一接口、proposal breaking 边界、主 D6/D7 和 storage-survey OQ4：路径优先由调用参数指定，未给定时采用 `SFRS_DB_PATH`，再默认 `~/.atomcode/sfrs/facts.db`，不进入 Skill 安装包或版本库。不同项目共库以公共来源域/项目身份隔离，不以工作目录隔离冒充语义身份。

导出读取同一一致视图中的全部当前记录（包括失效记录）、证据、公共冲突和必要前提，使用最小私有维护容器 `RepositoryTransfer(format_version: Literal[1], batch: JsonObject, tombstones: tuple[DeletedIdentity, ...], bindings: tuple[PremiseIdentityBinding, ...])`。batch 仍由最新公共契约编码；`DeletedIdentity(target: RecordKey, project_keys: tuple[str, ...])` 仅保存被引用的已删除身份/所属域，不带旧值；`PremiseIdentityBinding(dependent: RecordKey, premise: RecordKey)` 仅保存本地必要前提端点身份，不带 token。这是本组件导入导出的维护封套，不是事实语义协议、Response、历史协议或第二公共 schema；结构由 transfer.py 精确校验，公共 batch 部分仍由同源 codec 校验。封套仅携带重建批后引用视图必需的墓碑与绑定，不可将任意缺失身份伪装为已删除目标；每个墓碑必须在导出视图中真实存在、被批内失效记录引用且属于对应域。合法跨项目/来源域必要前提在双方均属于授权项目集合、完整身份一致时允许保存与导入，不按“跨域”一律拒绝；导入的授权项目集合由调用方显式传入 `import_current` 的 `project_keys` 参数；空集合直接拒绝，不从待导入文件、工作目录、默认库路径或隐含上下文推断，也不由文件扩权。这是内部范围参数，不新增公共协议字段或鉴权服务。导入时任何有效记录引用墓碑、未声明悬空内部端点、绑定端点与公共前提完整域限定身份不一致、伪造域或越过授权项目集合均整批拒绝。

导入整批同源校验、引用检查及原子 create；对既有不同内容身份拒绝，不能覆盖真实当前记录；相同内容幂等。先按完整域限定公共身份和必要墓碑建立批后引用视图，再为新记录分配本地 token、为 premises 绑定同批/库内当前 token。原 invalid 状态、原因、失效关系和冲突原样保留，不因重绑恢复 valid；原 valid 记录只有在全部必要前提合规、存在且有效时才能保持 valid，否则整体拒绝并定位缺口。内部 token/提交确认不写入导出封套，不沿用导出库 token。墓碑不因导入成为有效实体或 external 端点，不向用户暴露历史查询。

备份采用 sqlite3 的一致备份能力，依据 [SQLite Online Backup API](https://www.sqlite.org/backup.html) 保存当前数据库（含内部状态与墓碑）；恢复只创建不存在的目标路径，先在临时库执行完整性/外键检查、schema 兼容和保真重读，全部通过后发布目标。失败删除仅限本次临时产物，原库/已有目标保持不变。

独立验收使用真实临时 SQLite 和公共合规 fixture，不依赖构造器/查询实现。当前代码不兼容时拒绝打开并报告，保留原数据库；不删库通过测试，不提供旧记录迁移器。产品测试及验收证据由后续 apply 产生，本轮只校验规划。

被否备选：只导公共 batch 会使失效关系指向的删除身份悬空；要求主公共契约新加本地墓碑/token字段会越过归属；丢弃这些记录会破坏保真。JSON 响应导出会丢失无效/冲突/证据状态；直接覆盖恢复目标有数据损失风险；写入项目源目录污染使用者项目；历史包和兼容迁移超出范围。

## Risks / Trade-offs

- [公共 wire 契约仍未更新] → D1 与任务 1 是可判定外部实施准入，不能使用旧资产或仓库私有字段绕过；规划工件可先完成。
- [字段级布局及无损重建复杂度] → 同源 schema 正反例、每字段断言及 round-trip 测试；不作无基准性能承诺。
- [依赖声明不完整] → 查询流程负责当前来源与语义受影响范围；仓库严格检查显式前提，不能宣称检测所有软件变化。
- [墓碑及幂等确认占空间] → 当前仅维护当前值及必要一致性元数据，不提供历史检索；规模测量后再提案清理，不在本轮增加策略。
- [SQLite 本地写锁与存储失败] → 单客户端仍测试双连接陈旧写、锁忙及回滚；不把进程内缓存当持久化证据。

## Migration Plan

1. 本轮依 OpenSpec 指令创建 design/tasks，经独立 builder check、覆盖自审和严格规划校验，不运行产品实施。
2. 后续收到新的实施请求，再按 apply 核验 D1，创建同源绑定、fixture、失败测试，逐任务最小实现并验证。
3. 完成独立组件验收后交付主变更引用；不代做主查询/构造/端到端集成，不将本仓库测试声明为系统交付。
4. 替换与回退保持成套契约及匹配实现；遇到不兼容库只报告并保留，不清库、不自动迁移、不自动归档。
