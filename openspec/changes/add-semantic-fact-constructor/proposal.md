# Proposal（语义事实构造器）

## Why

语义事实生产需要可测试的确定性载体，把既定需求匹配、工具执行、外部解析器调用、事实合成与受约束归纳衔接起来。主变更 `epic-layered-semantic-fact-skill` 已明确当前项目查询的总设计方向，构造器与其他组件仍待实施，不能以规划文件或旧公共资产代替交付。

## What Changes

- 构造器消费构造请求、既有有效事实、未满足项及当前来源上下文，复用有效事实，仅补本次请求及必要关联；返回结构化事实、证据、归纳请求、冲突与缺口，不直接持久化，不组装最终 query response，构造输出不等同于 output-schema 响应。
- 信息需求清单是开发期交付物：由本构造器变更后续在 design/tasks 中依据事实目录和事实需求完成分解、固化及追溯，不在运行时生成或扩展。开发期新增需求通过提案推动 `survey-info-acquisition-tools` 研究及 `add-info-parser` 开发，完成接入验收后点亮，再完成构造器工具链接入；公共信息、查询与响应契约仍由主变更拥有。
- 运行期按请求、既有有效事实和未满足项，从既定信息需求清单匹配及聚合所需子集，生成确定性获取计划并组合已点亮工具；相同请求、既定清单和有效性上下文得到一致计划。运行期不调研、不开发解析器、不改清单或矩阵；清单未覆盖的需求返回明确 gap，由后续开发期提案处理。
- 只读初始为空的能力矩阵，根据当前环境、信息覆盖、限制及调用说明选择已点亮工具；一个需求允许多个工具组合，部分覆盖后仍结合其他工具判断剩余缺口。调研补未点亮条目，只有解析器开发流程完成接入验收后才能点亮，构造器不修改或点亮矩阵，点亮表示已验收可用，构造器可直接选用。
- 执行工具并监控生命周期、超时、输出完整性、重试与降级；相同当前来源内容状态和调用剖面的结果可复用，避免按事实类型重复调用。同一工具在多项目或不同调用剖面下允许必要的多次调用，不规定每工具全轮只能一次。
- 将 `tool-native-output + invocation-profile` 交给外部解析器转为统一来源信息，再合成事实；不在构造器中实现解析器。证据可来自源码、清单、配置、文档和观察，保留定位、来源状态及依据链，不局限于 file:line，不伪造证据。
- 按未满足需求触发受约束归纳：缺事实、unknown、证据不足、非空但不满足请求均可触发；已有充分证据可归纳，不强制所有认知能力先由解析器点亮。按事实类型、主体、当前来源内容状态及上下文分组，同组字段整组交接；返回后校验请求绑定、证据和状态，冲突不得静默覆盖，未满足项保留 gap。具体批组机制由 `add-induction-batch-trigger` 承担，本组件声明母需求及接口边界。
- 任一被构造节点都完整识别观察边界内直接节点，即使请求只匹配其中一部分；不能确认完整性时显式 gap。识别 child 不递归构造每个 child 的完整事实集；只补定位所需上级路径，允许多父组织关系，依赖循环不得递归组织成树。
- 确定性校验、分解、选工具、执行编排与合成固化为程序并配判定验证；无确定算法的认知归纳通过独立接口在证据约束下完成。不可用工具、解析失败、归纳不足分别报告，不能以猜测或占位填充。

## Capabilities

### New Capabilities

- `semantic-fact-constructor`：按当前来源上下文及未满足需求执行信息分析、工具组合、外部解析、事实合成和受约束归纳，保留证据、完整性及缺口。

### Modified Capabilities

无。

## Impact

- 最新公共契约直接替换旧协议并统一消费者；不保留兼容入口、双轨协议或回退适配，不要求旧数据迁移工具或历史可读承诺。本轮仍只改规划文档。

- 本子变更拥有构造器实现及信息需求清单；矩阵、解析器、批组归纳、仓库、查询编排分别由对应子变更实施，主变更拥有总设计、公共契约、依赖编排及集成验收。
- 公共契约与字段结构应引用主设计的更新产物；当前 Skill 的 assets/references 含旧协议，本轮不修改，不声称已与新契约一致。
- 本轮仅修订现有 proposal/specs，不创建缺失 design/tasks，不实施或归档；设计阶段继续明确接口形态与来源追溯，不预设组件已存在。

## S1–S12 来源项目信息需求补充（先于工具调研）

现有四项 F2/L3 语法清单仅是已实现的第一阶段切片，不是完整生产链的信息需求。后续 apply 必须先在本提案、design 和 tasks 中分解 S1–S12 所需的来源项目信息，再更新固定信息需求清单；不得先选工具再倒推需求。需求至少覆盖：

- **范围与项目身份（F1–F3）**：用户明确的根目录/排除范围、项目与入口身份、语言/运行时/部署/配置线索及其来源；目录嵌套不等于项目归属。
- **工作空间与组织（F4–F5）**：工作空间清单、成员关系、嵌套/重叠项目根、职责与实现关联；物理包含、工作空间成员、逻辑从属和依赖必须分开表达。
- **依赖、交互与接口（F6–F8）**：清单声明的构建/包依赖、源码引用/导入/调用候选、接口归属、请求响应、触发、顺序、效果与结果；保留条件、解析状态和范围外端点。
- **类型、绑定与分派（F9–F11）**：声明、类型关系、引用解析、目标集合、动态分派、参数映射及未解析/条件目标；语法名称不得冒充类型或动态调用证据。
- **内部行为（F12–F16）**：数据流候选、状态生命周期、守卫、错误传播、控制流/回边、算法步骤与解释前提；直接观察和归纳结论必须分开，终止性/复杂度未证明时保持开放项。
- **证据与细化（F17–F18）**：反证、知识状态、检查/排除区域、枚举完整性、未满足需求，以及高层职责到低层实现的追踪。

每项需求都必须定义所需输出、证据类型、当前来源绑定、覆盖/完整性判据、语言/平台/环境约束、盲区、验收夹具和研究依据。一个需求可以由多个生产工具组合覆盖。超出已验收能力的字段继续返回明确 gap。

### 强制依赖顺序

1. 本构造器提案、设计和任务先完成来源项目信息需求分解与追溯，并更新 `information-needs.json` 及其验证测试。
2. `survey-info-acquisition-tools` 只以该清单为输入，逐需求补充候选工具、真实环境探测、输出样例、覆盖和限制；未验证环境不得写成可用。
3. `add-info-parser` 再针对已研究且选定的原生输出格式补充解析器设计、实现与正反测试。
4. 只有解析器对相应工具/输出/调用剖面通过接入验收后，才可启用对应矩阵条目。
5. 构造器运行调度最后消费既定需求与已验收矩阵；再进入归纳、仓库重读及主变更 S1–S12 集成验收。

本提案不宣称这些新增信息已被当前工具或解析器覆盖，也不允许在同一次 apply 中跳过研究与解析验收直接点亮矩阵。

## 修复：请求级生产者选择与单次执行语义

当前构造器集成暴露出同一事实获取请求可能重复执行同一生产者、重复消费观察并产生冲突 FactBatch 身份的问题。本变更必须先修正本提案、设计与任务，再应用实现；不能只删除一段重复代码而不建立请求级调度契约。

- 工具选择以本次事实获取请求的未满足信息需求为输入。先按语言、平台、环境、覆盖、限制和成本选出合适生产者，再按 `(source_id, content_state, tool_id, invocation_profile, normalized_arguments)` 分组执行。
- 同一来源快照下，同一工具调用剖面只执行一次；其解析结果必须分发给本次请求中所有由该剖面覆盖的信息需求。不同来源快照、不同必需参数/调用剖面允许分别执行。
- 计划应明确区分“需求到生产者的覆盖映射”和“唯一执行任务列表”。执行层只遍历唯一任务列表，不得遍历每个需求条目再次调用工具。
- 观察到事实的映射必须使用稳定的事实身份规则。相同事实身份的重复贡献应聚合证据；身份相同但字段值冲突时保留冲突记录并产生明确 gap，不得静默覆盖或通过放宽仓库契约掩盖。
- 对每个请求增加可观测的调用计数/执行记录，并以回归测试证明一个工具覆盖多个需求时只执行一次、结果覆盖所有请求字段；两个不同工具提供重叠证据时不得产生重复事实身份。
- 在工具执行前后校验同一来源快照；来源发生变化时，丢弃该快照下的全部工具输出与派生事实，并返回 `source_modified` gap。

验收标准：重复消费循环不存在；相同请求和快照下生产者调用次数确定；输出按需求扇出但事实按身份聚合；冲突可观察；来源变化失败关闭；FactBatch 契约验证、SQLite 重读与最小响应回归通过。此修复不授权启用任何尚未完成接入验收的矩阵条目。

## 组件边界澄清：请求调度与仓库增量存储

本变更中的“避免重复执行”仅指构造器的请求级调度优化，不是对仓库增量写入、幂等提交或已存事实复用的替代实现。

- 构造器只依据本次请求的未满足信息需求选择工具；对相同来源快照、相同调用剖面及相同参数的任务执行一次，并把输出分发给相关需求。它不查询持久化身份表、不决定跨请求是否应写入，也不负责跨提交的去重。
- 构造器返回的单个 FactBatch 必须符合公共契约。若多个观察贡献同一事实字段，应在事实合成时合并可兼容的证据；无法调和的值冲突须显式表示并报告，不能以重复事实记录绕过契约。
- 仓库负责增量持久化与幂等提交：按稳定事实/字段/证据身份识别已有记录，只写入实际变化，安全补充证据并按存储契约处理冲突。重复提交相同 submission key 与相同摘要应幂等；相同 key 对应不同内容必须拒绝。
- 仓库的重复身份校验是数据完整性保护，不应放宽为静默接受重复行；同样，构造器的单次工具调用保护也不能被当作仓库幂等性的实现。
- 验收必须分别证明：一次请求内同一调用剖面不会重复执行；FactBatch 不包含未解决的重复身份；重复提交不会重复写入；新增证据或字段能按需增量保存；真实冲突被保留或拒绝且不静默覆盖。

## 职责边界澄清：最少工具获取与重复信息处理

构造器的目标不是实现持久化去重，而是依据本次事实获取请求、已有当前有效事实和未满足信息项，选择能满足需求的最小合适工具组合。工具选择优先复用已获取且仍有效的信息；后续工具输出与本次请求已获得的信息重复时，不重复构造相同事实贡献。若额外输出提供了新的请求字段或必要的独立证据，则按请求与证据策略保留，不得将有价值的增量信息误判为重复。

构造器只负责本次请求内的需求满足、工具选择、输出到事实的合成和合法 FactBatch 形成；它不维护跨请求的持久化身份索引，也不自行判断数据库中某主体是否已经存储。构造器可为本次请求的等价工具调用复用执行结果，但这只是最少调用优化，不是仓库幂等写入。

仓库负责跨提交的增量存储和幂等性。仓库按公共契约中的稳定身份检查主体/节点、事实、字段、关系和证据：完全相同的已有记录不重复插入；已存在主体下新增的事实字段、关系或证据按仓库局部更新契约补充；相同身份但不可兼容的内容按契约拒绝或记录冲突，不能静默覆盖。不能仅因主体存在就丢弃其所有新字段或证据。

验收应分别验证：工具组合覆盖需求且尽量减少调用；同一请求的重复输出不会形成重复事实身份；仓库重复提交幂等；已有主体可增量补充缺失字段/证据；冲突不静默覆盖。这些验收属于不同层次，不得以某一层的去重替代另一层的职责。

## Clarification: choose a minimum sufficient producer set for the request

The constructor SHALL select tools against the set of unmet information needs for the whole request, not independently select every eligible producer for every field. It SHALL prefer the smallest suitable set of enabled, accepted producers whose combined declared coverage satisfies the requested needs, subject to language/platform/environment, evidence, completeness and limitation constraints. A producer covering several unmet needs should be preferred over several redundant producers when both options are equally valid. If no complete coverage set exists, select only producers that advance the request and report the remaining needs as explicit gaps.

The constructor may discard a later producer's duplicate contribution only when it represents the same requested semantic information for the same source snapshot and adds no distinct field, value or useful independent evidence. It must preserve novel fields/evidence and report incompatible values as conflicts. Repository storage remains producer-agnostic and owns cross-request idempotency and incremental entity enrichment.

## Runtime integration requirement for accepted subprocess producers

An accepted subprocess producer is not production-integrated merely because a direct constructor test can inject an executor. The query orchestration/CLI path MUST pass a host-configured, fixed-argv, bounded executor into constructor execution. The executor allowlist is application configuration, never derived from query input or matrix-supplied arbitrary commands. If the tool is unavailable, disabled, unaccepted, times out, fails, or returns malformed output, the request receives an explicit gap and no facts are fabricated. The production matrix remains disabled until the real query path proves tool invocation → parser → FactBatch → repository write/reopen → minimal response on a real fixture.

## 项目分析类 Skill 的选择、自动安装与恢复执行

- 工具覆盖不足时，只有通过直接工具对照证明具有增量价值的独立项目分析类 Skill 才能被选中；若选中的 Skill 尚未安装，构造器应通过宿主支持且已获准的机制自动安装固定来源/版本，并验证其入口和基本输出契约后再调用。
- 自动安装必须使用开发期验收并登记的规范来源，记录/固定版本，优先使用隔离的受管安装目录；不得从 Query、项目 README、源码或 Skill 输出中读取任意安装命令，不得静默授予新权限、改写全局配置、启用 hooks/后台更新或执行未经授权的项目代码。
- 安装状态、运行健康状态和生产能力验收状态必须分开。安装成功不代表输出已满足语义需求；返回内容仍须通过来源身份、授权范围、当前内容状态、证据、覆盖完整性、冲突及混合语言关系验证。
- 若宿主不支持自动安装、安装失败或需要额外授权，则返回显式 `skill_install_required`/`skill_unavailable` gap，向用户说明 Skill 名称、规范来源、准确的宿主安装步骤、所需权限及验证命令；同时继续其他可独立完成的工具获取和查询工作。待 Skill 可用后恢复被阻塞的需求，不将其标记为已满足。
- 本组件负责运行时选择与可恢复安装流程；调研组件只记录候选的安装方法、安全要求和验证步骤，不安装、不授权、不点亮能力矩阵。