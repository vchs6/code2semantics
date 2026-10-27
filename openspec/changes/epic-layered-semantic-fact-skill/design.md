# Design

## Context

动机与本次授权边界见 [proposal.md](proposal.md)。行为权威为 [semantic-fact-query](specs/semantic-fact-query/spec.md) 与 [query-contract-derivation](specs/query-contract-derivation/spec.md)。既有[事实需求研究报告](../survey-semantic-fact-requirements/research/semantic-fact-requirements.md)第 3 节 R1–R16、第 5 节四层观察与 O1–O5、第 6 节 F1–F18、第 7 节追踪、第 8 节 S1–S12 已存在；本轮不重做研究，不替换其目录依据。

`skills/layered-semantic-facts/assets/`、`references/` 及本变更 `validation/` 现有文件包含旧的历史、用户快照、refresh、`parser(scope, needs)` 协议。它们是待迁移资产，不能当作本设计已实现的接口或生产证据。八子变更的 proposal/specs 是组件规划入口；缺失的 design/tasks 不在本轮补建，不假定实现和验收证据存在。已有[工具研究报告](../survey-info-acquisition-tools/research/semantic-tooling-survey.md)仅作后续需求驱动增量复核的材料。

## Goals / Non-Goals

**Goals:** 主变更固化跨组件边界、公共契约迁移顺序、依赖和集成验收；组件子变更承担实现、局部测试及交付。确定性控制流程由程序执行，认知归纳通过独立输入输出接口调用。

**Non-Goals:** 本轮不实施、迁移 schema、运行产品验收或归档；不将规划完成等同于契约可用、解析点亮或端到端生产完成。

## Decisions

### D1 研究依据与契约迁移顺序

依据 proposal 的研究保留约束、spec 的“研究驱动的目录与观察粒度”，及报告第 3/5/6/7 节，沿用四层观察 L1–L4 与组织职责 O1–O5 的分离、F1–F18 事实目录。主变更后续先迁移 `assets/fact-catalog.json` / `fact-catalog.schema.json`，再迁移 `contract-format.schema.json`，最后迁移 `output-schema.schema.json`；公共 `common.schema.json`、`pipeline.schema.json`、`information-needs.schema.json`、`capability-matrix.schema.json` 及 `references/fact-catalog.md`、`contract-format.md`、`output-schema.md`、`runtime-contracts.md` 必须同批对齐。

公共契约包含 Query、主体/节点引用、来源上下文、有效性、FactBatch、Evidence、Gap、工具说明/点亮状态、ParseRequest/Result、ConstructRequest/Result 与 InductionRequest/Result 的语义边界。名称在此标识概念，不声明旧 JSON 字段已符合新设计。主 `validation/validate_contracts.py` 随目录、查询、中间与响应定义逐阶段替换，承担设计资产 shape、引用与正反样例校验，不等待组件 runtime，也不重复实现组件运行时 validator；查询交付后再核对设计资产校验与同源运行时接口一致性。请求限定当前项目集合、固定目标和观察粒度；FactBatch 与 Response 分离，Response 只由查询投影。旧契约无需兼容，后续直接重写统一定义、样例、接口说明和消费者，不建设旧协议适配或旧数据迁移工具。契约迁移必须删除用户历史、快照、revision、refresh 入口和旧解析签名，并迁移对应正反样例与确定性校验后才能供子组件使用。

被否备选：重新调研分层会丢弃已交付依据；直接认定已有 schema 符合新语义会把旧协议带入组件。目录支持不等于实际生产覆盖。

### D2 当前主体身份、来源有效性与增量更新

依据 proposal 当前项目与边界约束、spec 的范围分离/当前来源变化/推导前提闭包，及报告 R1/R2/R15、S1/S4/S8/S12，主体身份由来源与边界证据确定，与用户目录、工作空间成员关系及显示路径分离；同名、移动或多父不能直接判同一或不同。跨项目/工作空间交互必须有独立证据，成员关系不能替代依赖关系；范围外端点只留引用。

用户查询时核对当前来源状态，先排除删除、失效及前提不成立事实，再把本次需求、既有有效事实和变化交给构造流程。只重构受影响请求及必要关联，不主动全量重构。来源内容指纹可选，用于内部失效判定，不暴露为用户版本协议；有效性必须包括修改、删除、未提交/未跟踪内容及相关排除边界。内部保留审计数据不产生历史查询能力。

被否备选：只用提交标识会漏掉当前修改；要求用户 refresh 或 revision 违背当前查询入口；每次清库全量重建损害增量需求并掩盖有效性错误。

### D3 直接节点完整识别与最小投影分开

依据 proposal 节点边界、spec 的最小直接下级结果/构造边界内直接节点完整性，以及报告第 5 节、R2/R3/R4/R16、S1/S8/S9，构造前确定本次节点的观察边界和粒度。请求节点缺必要上级时，先沿有证据的必要上级路径构造；不强制唯一父。任一被构造节点都必须完整识别边界内直接节点并记录识别覆盖，不能只发现匹配选择器的部分。完整性不能证实时记录 Gap，不作充分覆盖。

直接节点清单与其完整事实集是不同交付：识别边界内所有直接节点，不递归构造每个 child 的完整事实；循环边保留为关系，以访问边界防止递归成树。查询只返回请求节点所需事实及其直接节点最小投影，保留身份、必要 context/coverage/basis 和证据。上级构造所得不全部输出，后续更深分析使用节点引用发起新查询。

被否备选：只构造匹配部分不能证明完整性；预建整棵树或所有 child 事实会无界扩展；强制唯一父会丢失重叠组织与共享实现。

### D4 工具研究、矩阵与解析器的责任边界

依据 proposal 工具可用性/解析职责与 spec 同名约束，结合报告第 3 节事实需求和第 9 节支持边界，矩阵部署初始为空。工具研究仅在开发期按构造器子变更设计/任务交付的固定信息需求清单，以及经提案确认的新增需求，增量补充未点亮条目，记录输出信息种类、需求覆盖、限制、支持语言、平台环境、调用说明和组合方式；一项需求可由多工具组合覆盖。选择先满足覆盖和环境，再偏好轻量、简洁、多语言，不用“单工具优胜者”代替需求覆盖。

矩阵只存工具说明与已验收点亮状态，不执行工具、不生产事实、不调度构造。只有 `add-info-parser` 的解析器开发流程完成、满足纯转换契约且测试通过后，由该开发流程通过矩阵受控接口点亮；研究与构造器不得点亮。运行时构造器只消费开发期既定信息需求清单，匹配请求与未满足项并聚合当前获取计划，再读取已点亮且环境适用条目，选择组合执行。运行过程不得生成或扩展清单、触发工具研究、解析器开发或点亮；未覆盖需求返回 Gap，待开发期变更处理。

解析公共契约为 `parse(tool_native_output, invocation_profile) -> ParseResult`：调用描述与原生输出携带工具身份、调用环境、覆盖、来源定位与必要证据；解析器只做结构转换与格式校验，不执行工具，不读源项目或事实仓库，不选择工具，不归纳语义事实，不维护矩阵。所需定位或证据未包含时返回解析缺口，不偷偷读文件补齐。点亮表示工具已通过接入验收、可被构造器使用，不设置另一套生产状态。执行器管理每次调用的运行、超时、重试和成功失败，不写矩阵；集成验收证据独立记录，不能变成矩阵的新状态。

被否备选：矩阵承担调度会与构造器重叠；研究直接点亮跳过解析验证；解析器接受 scope/needs 并主动取源混淆工具执行和纯转换。

### D5 构造、归纳与事实仓库分离

依据 proposal 构造与归纳约束、spec 构造与查询职责分离，以及报告 R8–R16/F4/F6/F7/F11–F18：`construct(request, existing_valid_facts, unmet, current_source_context) -> ConstructResult` 由运行构造器消费既定清单、匹配聚合为当前获取计划，再选择组合已点亮工具并执行，将原生输出交解析器转换为统一来源信息，再向归纳接口提供请求所需来源、已有事实与缺口，返回 FactBatch/证据/冲突/剩余缺口。构造器不读写持久仓库、不组装 Response；已有事实由查询流程提供，调用方负责入库。

归纳触发以未满足需求为准，包含缺少、unknown、证据不足、非空但不满足。按事实类型、主体、当前来源内容状态和上下文分组字段；已有有效字段作为背景和复用输入，不能无依据覆盖冲突或丢失证据。归纳器只返回候选事实和缺口，不自行更改矩阵或写仓库。所有直接节点识别完整性也进入归纳与覆盖判断，不把局部结果冒充边界穷尽。

`add-semantic-fact-repository` 持有结构化事实、证据关联、上下文与当前有效性，支持校验后的批量写入、事务回滚、关闭重开读取和失效关联；不以最终 response 存取。推导前提闭包必须在有效读取时校验，限定否定保留检查边界与依据。

被否备选：以 response 为存储对象把请求投影和事实生命周期绑定；构造直接入库绕过查询校验；仅以 null 触发归纳遗漏 unknown 和非空不足。

### D6 确定性查询控制与实现形态

依据 proposal 查询循环、spec 中介补全/非法数据拒绝，以及 AGENTS 原则 7，确定性部分采用 Python 程序、JSON Schema 校验及 SQLite 持久化，使用 pytest 场景验证。此为既定最小实现形态，不是研究报告推导出的技术唯一性；子变更须在自身 design/tasks 细化并先测试后实现，不能让运行代理按自然语言手工执行控制流程。

查询顺序：校验 Query → 核定当前来源与有效事实 → 比对覆盖 → 必要上级及缺口构造 → 校验 FactBatch/证据/前提 → 仓库事务入库 → 重读 → 再比对 → 最小 Response。若满足请求、无有效覆盖进展或预算耗尽则终止，始终保留有效已有事实及未满足项。进展依据本次有界覆盖集合的推进，包含目标有效覆盖以及必要上级路径、直接节点完整性前置义务；无关新事实不算进展。目标字段尚未增加但必要前置义务推进时继续，不能误判无进展。进展还可依据可用充分性，重复候选、调用次数、字段非空和已点亮状态不算进展。目录外请求与目录内 missing 分列；预算及执行边界显式返回，禁止无限重试或 gap-only 冒充成功。

被否备选：构造输出直达响应绕过持久化重读；AI 临场组织循环不可重复验证；空值填满覆盖会误报成功。

### D7 八子变更依赖与交付门槛

依据 proposal 主/子职责与 spec 可验证交付，主变更仅拥有公共契约、依赖编排与集成验收。以下路径表示已存在组件变更和预期义务，不证明设计、实现或证据已完成。

| 子变更入口 | 前置依赖 | 子变更预期交付与局部验收 |
| --- | --- | --- |
| [survey-info-acquisition-tools](../survey-info-acquisition-tools/proposal.md) | 公共目录与构造器首阶段信息获取需求清单 | 在既有 `research/semantic-tooling-survey.md` 基础增量复核说明，输出种类/覆盖/限制/平台/调用/组合齐全，保持未点亮 |
| [add-semantic-capability-matrix](../add-semantic-capability-matrix/proposal.md) | 公共工具说明与点亮状态契约 | 空矩阵初始化、说明读取和受控状态更新；研究/构造不得点亮，矩阵不调度 |
| [add-info-parser](../add-info-parser/proposal.md) | 公共解析契约、工具说明与矩阵状态接口 | 原生输出+调用描述纯转换；不读项目/仓库，不执行；开发完成后受控点亮及证据 |
| [add-induction-batch-trigger](../add-induction-batch-trigger/proposal.md) | 公共归纳输入输出与未满足项契约 | 非空不足等触发、分组、候选事实和证据/冲突/缺口保留，不持久化 |
| [add-semantic-fact-constructor](../add-semantic-fact-constructor/proposal.md) | 首阶段仅需公共目录/构造契约；后阶段依赖已点亮工具、归纳接口 | 开发期首阶段先产出固定信息获取需求清单（不等待工具）；后阶段运行时工具组合执行、来源解析、必要路径与直接节点完整识别；仅返回 FactBatch |
| [add-semantic-fact-repository](../add-semantic-fact-repository/proposal.md) | 公共结构化事实/证据/有效性契约 | SQLite 事务、重开重读、当前失效和前提验证、不存最终 response |
| [add-semantic-fact-query](../add-semantic-fact-query/proposal.md) | 公共契约、构造器、仓库 | 覆盖比对循环、校验入库重读、预算/无进展终止、最小投影和 CLI |
| [define-skill-packaging](../define-skill-packaging/proposal.md) | 查询入口与公共契约；最终验收需全部组件 | Skill、安装、对话同契约、明确请求报告、规范符合性和仓库外运行 |

开发期先推进构造器子提案、设计/任务与首阶段 apply，交付固定信息需求清单，不等待工具、矩阵、解析器或完整构造器；工具研究在开发期据此启动；这不是每次查询运行中的步骤。新增清单需求必须通过开发期提案推进研究与解析器验收，运行期只返回未覆盖缺口。矩阵可围绕公共契约准备，解析与归纳分别实现；构造组合前须有实际已点亮工具和归纳接口；仓库可独立依公共契约实现；查询依赖构造与仓库，包装和集成最后核验。任何缺失依赖保留 pending，不能由主 tasks 重复实施来隐去子交付空缺。

被否备选：主变更重写所有组件测试/实现会形成双重任务权威；仅引用子变更名而无验收输出不能建立集成门槛。

### D8 保真证据与真实集成验收

依据 proposal 保留原要求、spec 各事实保真条款，以及报告 R1–R16、S1–S12，公共契约区分 origin 与 knowledge，保留每字段的 context/coverage/basis、证据、限定否定和前提引用。组织组成与交互关系分开，结构回边、互斥候选环、共同条件下实际循环分别验证；内部算法保留控制、数据更新、异常、边界和未证实项，跨语言统一结构不得抹去语言语义差异。

主集成验收调用子组件真实入口，用研究 S1–S12 和补充新边界场景检查从真实工具输出到非空事实、SQLite 重开重读及最小响应。场景必须覆盖多独立项目、多工作空间、混合目录、同名/嵌套/重叠身份、跨范围引用不扩权、变化和删除后的按需重构、必要上级、直接节点完整性、非空不足、冲突、限定否定、组合工具与无进展/预算终止；逐项对应 [traceability.md](traceability.md) 和 [validation.md](validation.md)。工具接入验收与每类事实真实集成证据分别记录，矩阵不增设生产状态，未支持项保留缺口，不能缩减验收范围。

被否备选：示例 JSON、mock 或旧校验器通过只证明局部格式，不证明真实生产；将所有结果强制 Markdown 会改变机器接口。

## Risks / Trade-offs

- [旧资产看似齐备但协议不符] → 公共契约迁移前所有相关任务 pending；严格区分规划、契约校验、组件和端到端证据。
- [直接节点完整识别成本] → 固定观察边界、完整性缺口与预算；只识别直接节点，不预构造后代完整事实集。
- [失效传播过宽或过窄] → 以当前来源、必要前提及本次请求验证受影响集合，保留不相关有效事实，测试删除和未提交变化。
- [工具覆盖不足或环境不符] → 增量补研究说明、候选组合和未满足需求；未点亮工具不参与执行，不通过自动点亮掩盖缺口。
- [结构转换与认知归纳混用] → 用纯输入输出解析器和独立归纳候选接口分别验证，不让解析器读源补证据。

## Migration Plan

1. 本轮只落盘现有主/子规划文档；保留研究与旧契约资产，明确其待迁移状态。
2. 后续经 apply 执行主公共契约迁移：先目录、再查询、再响应及共享中间契约，更新对应验证程序、样例与引用，主设计资产校验随定义逐阶段替换，不等待查询运行时；先写暴露旧协议的失败检查，再直接替换并运行通过证据。更新前不得宣称新接口可用。
3. 各子变更按 D7 补齐自身设计/任务，依同源新契约先测试后实施；交付路径和测试命令必须在各子 tasks 落盘后才作为可执行门槛。
4. 主变更收集八子交付证据并运行集成，更新追溯与验收结果。契约不匹配时拒绝使用原数据并报告，替换时保护原始数据和证据，不承诺旧记录历史可读、不建设兼容工具；失败回退成套资产与其匹配实现，禁止删除仓库掩盖问题。
5. 文档、公共契约、组件、集成与 Skill 规范各自通过后才可宣称交付；本轮不执行发布或归档。
### D9 Project-analysis Skill selection, installation and resumable fallback

Producer selection first evaluates whether accepted direct tools can satisfy the current unmet information needs. A project-analysis Skill is considered only if it offers validated incremental value over direct tool use. If selected, it should be automatically installed through the approved host mechanism when absent, then verified before invocation.

Installation and authorization are distinct. No automatic install may silently grant new filesystem, network, credential, shell, project-write, hook or background permissions. Only development-time accepted canonical Skill registry entries may be installed; query/source content cannot supply installation commands. Pin/record the revision, use an isolated managed location where possible, and do not reinstall an unchanged accepted version on every query.

If the host cannot install automatically, user approval/permissions are needed, or installation fails, return an explicit `skill_install_required`/`skill_unavailable` gap with the Skill name/source, exact host-specific installation instructions, required permissions and verification command. Continue independent tool acquisition and other satisfiable needs; do not claim the blocked Skill need is covered. Resume the dependent work once the Skill becomes available rather than blocking the entire query.

Successful installation does not mean capability acceptance. The selected Skill's output must pass a dedicated adapter and checks for requested need IDs, source/project identity, authorized scope, current content state, evidence locators, completeness, conflicts and mixed-language relationship quality before any proposed facts are accepted. Install status, health status and producer acceptance are separate states.

The integration tests must cover: direct tools sufficient (Skill not installed/called); Skill provides verified increment (automatic install and use); automatic installation unavailable (actionable instructions and independent work continues); permission denied or installation failure (no fabricated facts, no infinite retries); and installed Skill with invalid/unsupported output (explicit gaps).