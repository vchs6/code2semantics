# Design

## Context

动机与行为上游为 [proposal.md](proposal.md)；本设计消费当前验收的[研究报告](../survey-semantic-fact-requirements/research/semantic-fact-requirements.md)，按 UTF-8/LF 规范化 SHA256 `825143510a29e9ca9e34a2b50a40bdcfc776a657da963c13d174087054c906b8` 锁定。研究 apply 已为 all_done；主 apply 发现 design/tasks 缺失，遂按 instructions design/specs/tasks 模板生成本工件链。不是从旧报告或历史实现迁回设计。

查盘时 skills/ 不存在，因此解析、构造、存储、查询和安装程序均为待实现；本轮仅落盘目录、协议、接口及计划。研究§8是构造场景表达检查，不是产品生产验证。规范依据为本变更两个 specs，已消除唯一项目根、源码唯一证据、强制Markdown及历史证据必须指向当前文件等偏差。

## Goals / Non-Goals

**Goals:** 用单一机读契约连接所有消费者；使最小查询保留可信度和快照语义；给后续执行者可测试的接口及任务。依配置严格先 fact-catalog、再 contract-format、最后 output-schema。

**Non-Goals:** 本轮不实施产品程序、不把目录表达支持声明为生产支持、不归档。最终实现的全部提案行为仍保留在 pending tasks，不以本轮边界删减最终交付。

## Decisions

### D1 观察粒度与组织职责分离

采用研究§5 L1–L4四种粒度及O1–O5组织职责，F1–F18逐项映射§3/§6/§7；以 [fact-catalog.json](../../../skills/layered-semantic-facts/assets/fact-catalog.json) 为目录权威。对应 proposal 的“从需求派生目录与分层”和“整体语义至内部算法”。粒度标签不是唯一父树；F4/F6/F18分别承载组织、依赖、实现/细化。报告S1/S8/S9要求跳层、多父和回边。

被否备选：按目录→工作空间→项目→类型固定深度会复制重叠身份、制造空层；把证据当末层会让摘要缺失可靠性。报告§5已明确合并/细分损失，故不采用。

### D2 目录封闭与共享协议

按D1目录生成 [contract-format.schema.json](../../../skills/layered-semantic-facts/assets/contract-format.schema.json)，再生成 [output-schema.schema.json](../../../skills/layered-semantic-facts/assets/output-schema.schema.json)。common.schema.json共享引用/证据/断言，pipeline.schema.json共享所有中间记录；information-needs与capability-matrix各有契约。各消费者不得另建字段枚举。版本1.0.0与目录semantic-facts-20261025同时匹配才可命中。对应 proposal“目录封闭”“统一契约”，依据§6全目录与§7追踪。

字段内使用有标签的语义值；关系端点、候选条件、参与角色、参数绑定和控制边分别采用common共享typed定义，由目录value_shape映射并逐字段强制；描述性字段可用record/list细化。selector与gap显式带node或scope目标，避免跨主体覆盖相互抵消；InformationNeed的need_id=F.field，对应观察中的information_need_id。目录只列有限字段，schema和运行语义验证共同拒绝逃逸。该编码是设计选择，研究给出要保留的信息而未规定字段拼写。被否备选：自由JSON无法检查字段/引用；全扁平字符串无法稳定保留参与者与语义关系；按语言复制schema导致消费者分叉。

### D3 身份、来源快照与知识修订

NodeRef由namespace、snapshot、subject_id、node_id构成，fact_revision独立表示同快照知识增量；snapshot_set_id绑定所有来源。命名域由来源注册表标识真实来源，不从同名/行号或共同目录推得。边界证据决定主体；跨快照同一性以有证据对应关系处理，不承诺重命名后的自动稳定识别。当前内容捕获含dirty/untracked/排除与配置，历史从保存内容读取。精确node续查只读原revision，current仍核对来源快照、historical固定历史内容，缺字段返回gap不构造。显式refresh仅限当前同快照，读取latest并可构造新revision，在resolved_target返回新continuation；旧引用不变。历史scope请求也只读，按开始时已存知识返回实际修订。依据报告R1/R2/R15、F1/F2/F17、S4/S8/S12及proposal“证据、知识状态与覆盖”。

被否备选：commit SHA忽略未提交/未跟踪变化；只用路径/行号会跨来源碰撞；以最新知识覆盖旧记录会改变历史引用。具体规范见contract-format.md。

### D4 字段级可靠性与最小投影

每字段强制origin、knowledge、context、coverage、basis；来源性质与知识状态独立，解释不足、观察冲突均可表达。否定必须有域、充分检查和证据。派生读取检查传递前提闭包，最终只返回请求字段与必要前提引用；子树只有续查头，不含后代。依据研究R15/R16、F17、O4/O5、S11/S12及proposal“最小查询/覆盖”。

被否备选：仅事实节点一个可信度会在字段投影后丢成立条件；单一 observed/unknown/absent枚举混淆来源与支持程度；返回整个前提闭包泄漏未请求事实；仅schema通过不证明语义有效。局部结构在schema验证，跨记录职责V1–V9明确由运行程序执行。

### D5 关系、内部行为和语言差异

F4/F6/F7/F11–F15/F18保留不同边种类、方向、条件、参与者和范围外未解析占位。循环检测先保留结构，再检查同域条件合取；初版对显式布尔文字可确定拒绝互斥，其它表达保留unknown，不伪称通用可判定。F15操作与F16解释分别保留，原语言行为通过F9及context保留。依据研究R4/R6–R14、S6/S9/S10/S11、U2/U3/U5；对应proposal“组织依赖与交互”“整体到内部”。

被否备选：成员推出依赖、无条件合并边、按展示树删除回边都损失证据；统一术语后抹去溢出/分派/并发差异会产生假等价；算法名称代替步骤不能解释边界和错误。

### D6 确定性流水线与认知接口

当前scope或显式refresh执行 read→compare→construct→validate→put→read latest→project；精确node与historical只读→compare→project，缺字段返回gap，不进入构造循环；构造显式接收known与parsed，保留已有字段及直接分析边，禁止访问Repository。认知接口只接主体、请求字段、证据、上下文和快照；返回统一ConstructResult并再验证。停止条件是覆盖无进展或预算耗尽，保留缺口。依据研究R8–R16及proposal“确定性处理与认知归纳”“实际生产交付”，并遵AGENTS原则7。准确签名与所有权见[runtime-contracts.md](../../../skills/layered-semantic-facts/references/runtime-contracts.md)。

采用Python/jsonschema与SQLite事务存储作为当前最小实现选择；研究支持范围/证据/版本/追踪职责，不声称比较过引擎。标准库可实现内容哈希、只读解析与事务修订；pytest锁定确定性行为。被否备选：由代理按文档即兴校验不可重复；构造器直接存储会混淆责任；纯内存不能完成持久化重读；引入远程数据库在当前本地Skill需求下增加未要求依赖。

### D7 能力矩阵与真实生产验收

每F/字段派生信息需求和证据/上下文/否定覆盖需求，按语言环境与生产模式实测后记录矩阵。全部当前production_status为unverified。解析基线拟采用授权文本定位观察及Python ast直接结构观察，认知路径通过宿主适配器生成解释；工具能力必须先研究/实测才点亮，不把研究的表达目录当工具支持清单。须在真实材料上走非空生产→入库→重读→最小查询；跨语言场景保留实际差异，S1–S12均有对应验收。依据报告§1/§8/§9与proposal“各项事实需求派生生产信息需求”。

被否备选：空gap响应、仅模拟归纳、只有schema通过都不能证明产出；按文件后缀宣布语言支持没有实测依据。工具实测未知不会缩小需求，未覆盖仍pending。

### D8 Skill布局与宿主报告

最终包使用SKILL.md、scripts/、references/、assets/；入口短说明加载同一目录/协议，运行环境放compatibility，遵AGENTS引用Agent Skills Specification（name与目录一致、≤64字符；description≤1024字符；正文<500行）。当前只交付assets/references，SKILL.md与可运行包需后续任务完成，不能宣称已可安装。报告模板由宿主在明确请求时使用，内容必须来自同一Response。

被否备选：把schema藏在scripts或把全部协议塞进SKILL.md不符合渐进披露；强制Markdown混淆两种模式。依据proposal“单一Skill与两种模式”“规范与可验证交付”，行业布局权威沿用AGENTS引用。

## Risks / Trade-offs

- 无损跨语言词汇未完备（U2）→保留原语义、上下文与unknown；真实跨语言测试失败时保持生产任务未完成。
- 算法解释不是证明（U5）→单独知识状态与前提链，不能以可追踪升级充分性。
- 否定/条件判断依赖覆盖（U3）→结构schema只作必要门槛，V5/V8运行检查和反例锁定。
- 工具生产能力尚未实测→任务3执行调研与真实样本，能力矩阵不预先标validated。
- 快照保存成本与同快照修订增长→初版保留全部引用依赖；清理不在当前范围，不能删除数据解决验证失败。

## Migration Plan

本轮只有设计资产，无旧运行数据迁移。未来按tasks执行并以独立临时仓库演练：验证schema和来源，创建版本化SQLite记录，真实生产入库重读，再在仓库之外安装包复跑；失败时保留原仓库和源项目，停止替换。现有不兼容数据只能通过显式、可验证转换生成新库，不就地擦除。归档单独等待用户确认。

## Open Questions

没有阻塞本轮契约和任务边界的问题。研究U1的职责分类理由、U2的语言特有语义、U3的一般条件可满足性、U5的证明强度保留为每次分析的显式未知，而不是预设结构结论；后续新增词汇须带新的研究/实测依据更新目录版本。性能索引和批大小可在不改变接口/行为的前提下通过基准确定，本轮不虚构结论。
