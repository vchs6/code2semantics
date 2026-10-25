# AI Agent <!--领域驱动设计 (DDD)--> 执行工程纪律

本文件对所有 AI 代理会话自动生效。原则条目按"规范"对待：与任何即兴判断冲突时，以本文件为准。

<!--
## 1. 限界上下文与物理沙盒隔离
- 严禁跨越限界上下文修改代码。若处理 `Order` 领域变更，你唯一的合法动作是修改 `openspec/changes/<current>/specs/order/`，严禁在同一个变更中私自触碰 `Payment` 或 `User` 目录。

## 2. 领域纯洁性红线 (Domain Invariants Guard)
- 当你在撰写或更新行为规范 (`spec.md`) 时，`Scenario`（GIVEN/WHEN/THEN）内禁止出现任何物理实现术语（如 `SQL`、`Redis`、`AxumRouter`、`HTTP 200`）。
- 你必须且只能使用 `openspec/project.md` 中定义的通用语言（Ubiquitous Language）来断言聚合根的状态变化。

## 3. 战术实现自动化规范
- 实施任务划分时，你必须优先在 `design.md` 中声明实体（Entities）、值对象（Value Objects）的不可变边界。
- 必须确保所有的持久化操作都通过 Repository 接口隔离，严禁在领域服务（Domain Service）内直接编写硬编码的数据库查询逻辑。
-->

## 4. 配置驱动优先于手工编排（2026-10-21 定）

凡属可重复的多阶段工作（如"调研 → 建模 → 定契约 → 实现"流水线），AI 不得在对话中即兴设计或手工串联流程，而必须：

1. **先把流程固化为配置**——写入 OpenSpec 配置（`openspec/config.yaml` 的 `rules` 与 `operations.*.guidance`）、变更任务清单（`tasks.md`）或项目技能（`.atomcode/skills/`），让加载机制与工作流自身驱动执行；
2. **再由配置运转**——执行时通过既有工作流（如 `/opsx-apply`）推进，AI 只处理配置未覆盖的阻塞与决策，不重排、不跳过验证。

**强制机制**（这些配置是该原则的落地载体，修改前先对照本条）：

- `openspec/config.yaml`：工件撰写规则（proposal/design/tasks 的顺序与内容约束）与 apply/archive guidance——顺序约束、准入条件与职责表述以配置当前内容为准，不在此处复述；
- 变更任务清单（`tasks.md`）：阶段顺序与验证准入条件的权威来源；
- 调研有度规则（清单一次成稿、二手每事实≤2 源、止损记差距）同属配置内容，不得在会话中临时放宽。

**何时允许偏离**：仅当配置与现实冲突（配置自身有错或任务超出其覆盖范围）时，先修订配置/本文件，再继续执行；禁止绕过配置直接手工编排。

## 5. 交付以产物落盘为准，禁止假设产物存在（2026-10-21 定）

规划完成不等于交付完成。变更工件（proposal/specs/design/tasks）齐备只代表计划就绪；真实交付物只有被显式执行（如 `/opsx-apply`）并验证落盘后才存在。此类问题的一般形态是：**交付物不在追踪/校验工具的视野内，或任务被写成对假想产物的核对，于是"规划齐备"掩盖了"交付缺失"**。治理规则：

1. **先核实、后引用**：引用任何上游/其他变更的产物前，必须先在磁盘上核实其存在与内容；缺失时触发上游执行并停下，禁止静默继续或凭记忆、凭对话历史假定其存在。
2. **执行型任务不可降级为验证型**：撰写 tasks 前必须先查盘——产物已存在方可写"核对/验证"型任务；产物不存在时，任务必须是"执行 → 产出 → 验证"型。禁止把执行动作从任务清单中抹掉、只留对假想产物的核对。
3. **交付物必须可检查**：每项交付物必须落在明确路径，并在任务验证项中写明可判定的检查方式（存在性/内容要点）；仅存在于对话中、未落盘的内容视为不存在。
4. **工具盲区由 AI 主动弥补**：追踪与校验工具（如 OpenSpec 的 status/validate）只检查其工件集内的存在性；工件集之外的交付物（如调研报告、生成文件）缺失时工具不会报警。不得以"工具没报错/校验通过"作为产物存在的依据，工件集之外的交付物一律按本条 1–3 主动核查。

## 6. AI “不带着历史记忆”阅读和讨论当前提案

## 1. 无状态讨论红线 (Stateless Discussion Only)
- 在对任何 `proposal.md` 或 `spec.md` 进行评审、讨论和断言时，AI 助手**必须自动清除前序会话的非结构化聊天缓存（Clear Memory Window）**。
- 你必须且仅能以“当前工作区中物理文件（As-is File Status）”的最终渲染文本为判定依据，严禁参考任何未写入文件的历史聊天痕迹。

## 2. 爆炸半径限制 (Context Token Limit)
- 严禁将无关的源语言大文件、历史运行日志全量作为对话上下文注入。
- 进行提案讨论时，合法的上下文 Token 范围仅限于：`project.md` (Read-only) + 当前变更文件夹下的 Specs 目录。

## 7. 确定性实现优先（2026-10-22 定）

凡可用确定性脚本/程序完成的处理流程（校验、转换、存储、查询、批处理等），AI MUST 优先实现为可测试的脚本或程序代码，并配套可判定的验证手段；MUST NOT 将此类流程交由 AI 代理在运行时按文档描述即兴执行。代理按文档执行不具备"精确、可重复、一致"所需的可确定性，仅适用于无确定算法可依的认知型任务（如语义归纳、报告渲染）。

强制机制：

- `openspec/config.yaml` 的 `rules.design`：设计涉及可脚本化流程时，MUST 固化为脚本/程序实现形态并声明验证方式；
- 消费方提案按契约消费约定声明实现形态（如 Python + SQLite），实现语言/引擎仅为当前选择，不构成对契约语言无关性的限定。

## 8. 工件派生纪律（2026-10-23 定）

变更工件（proposal → design → tasks → spec delta）是**派生关系**，不是并列文档。AI 修订任何工件时 MUST：

1. **指令驱动生成**：修订前 MUST 先运行 `openspec instructions <artifact> --change <name> --json` 取得该工件的撰写规则与模板，并按其生成修订；MUST NOT 凭对话记忆或即兴草案直接编辑工件文件。（起因事件：构造器变更 design 决策曾凭对话草案起草、未先取工件指令，被用户纠正后才补齐流程——本条即为杜绝复发。）
2. **上游定稿再动下游**：下游工件（design/tasks/spec delta）的实质修订 MUST 在上游工件定稿后进行，且 MUST 逐条引用上游为据；MUST NOT 在提案未修订时先改设计与任务分解来引入新行为语义。
3. **草案确认后落盘**：修订草案先在对话中展示、经用户确认后再写入（openspec-update-change 流程）。
4. **一致性回溯**：上游工件修订后，MUST 逐个核对下游工件与 spec delta 是否需联动修订，不允许"提案已改、设计与任务停留在旧语义"。

强制机制：

- `openspec/config.yaml` 的 `rules.proposal` / `rules.design` / `rules.tasks`：各含"指令驱动修订"规则条目，工件指令生成时自动携带本纪律；
- 工件修订后的实现落地 MUST 经 `/opsx-apply` + TDD（原则 7），MUST NOT 绕过 apply 流程直接改生产代码。

## 9. Skill 工件业界规范对齐（2026-10-23 定）

凡产出或修订 Skill 类工件（SKILL.md、目录布局、frontmatter 元数据），MUST 对齐 **Agent Skills Specification**（业界开放规范；仓库 `agentskills/agentskills`，规范文档 `docs/specification.mdx`，https://github.com/agentskills/agentskills ）：

- 目录布局：`SKILL.md`（必需）+ `scripts/`（程序代码，agent 运行而非加载）+ `references/`（按需加载的文档）+ `assets/`（静态资源与数据文件，含 schema）；
- frontmatter 字段按规范约束：`name`（与父目录名一致、小写字母-数字-连字符、≤64 字符）、`description`（≤1024 字符，含做什么与何时使用）、`compatibility`（运行环境要求的标准声明位）等；
- 渐进披露：SKILL.md 正文 <500 行，细节下沉 references/scripts；
- 符合性 MUST 经可判定手段验证（规范官方校验工具 `skills-ref validate`，不可用时按规范逐项对照检查表）并作为相关变更的验收项。

强制机制：

- `openspec/config.yaml` 的 `rules.proposal`：涉及 Skill 工件的提案 MUST 声明对齐 Agent Skills Specification 并声明符合性验收手段；
- 涉及 Skill 布局/元数据的设计决策 MUST 引用规范条款或用户对偏离的明确裁决为据。

## 10. 代码实现纪律（2026-10-24 定）

凡实现或修改代码，AI 代理 MUST 遵循：

1. **先读任务，绝不瞎猜**：动手前 MUST 先阅读任务清单（tasks.md 的对应条目）与上游工件（design/spec 契约），以功能说明为唯一实现依据；任务、契约、规范未覆盖的行为不得凭猜测补齐，实现与功能说明冲突时以说明为准，歧义 MUST 停下澄清而非擅自取舍；
2. **简洁优先**：实现以覆盖任务要求为界，MUST NOT 添加任务未要求的功能、重构、防御分支或"顺手改进"；代码量与抽象层级取能通过验证的最小形态；
3. **先写测试，再写代码**（TDD）：为每个实现单元先写可判定的失败测试（覆盖任务验证项），再写实现使其通过；重构与修复同样先有暴露缺陷/锁定的测试；
4. **禁止随意收缩和简化**：MUST NOT 为降低实现难度而删减、降级或部分跳过功能说明要求的行为（含"部分实现+注释说明"的变体）；做不到、不适用或发现说明本身有误时，MUST 停下向用户报告，经确认后修订上游工件再继续——MUST NOT 静默缩小范围。

强制机制：

- `openspec/config.yaml` 的 `rules.design`/`rules.apply`：实现类任务 MUST 声明"先写测试"的验证路径，apply 阶段按任务验证项先行测试；
- 本条与原则 7（确定性实现优先）叠加适用：可脚本化流程以脚本实现 + 测试锁定，认知型任务产出物仍须有可判定的验收检查。

## 11. OpenSpec 工件生成与验证分离（2026-10-25 定）

凡修订 OpenSpec 变更工件（proposal → specs → design → tasks 派生链），AI MUST NOT 自行手工改写 design / tasks 等内容；工件应由 OpenSpec 工具驱动生成（`openspec instructions <artifact>` 的规则与模板），AI 的职责是**验证**生成的设计与任务分解是否符合既定要求（spec 需求、design 决策、proposal 行为语义），并以 `openspec validate` 与逐条对照判定符合性；发现不符时报偏差，MUST NOT 绕过 OpenSpec 流程手工编排或即兴起草工件内容。

强制机制：

- 与原则 8（指令驱动生成）叠加：修订前 MUST 先取 `openspec instructions <artifact>`，按其模板生成，再经 `openspec validate` 验证；
- 验证结论（符合 / 偏差清单）随交付一并呈现，作为工件修订的验收依据。

参考文档（采用规范的权威来源，链接为 2026-10-23 采纳入库时点状态；变更工件引用本清单，不另行散落链接）：

- 规范正文（采用权威）：Agent Skills Specification — https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx
- 规范仓库（含 `skills-ref` 校验工具）：https://github.com/agentskills/agentskills
- 实现参考（Agent Skills 工作机制与渐进披露）：https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- 实现参考（编写最佳实践，目录组织与渐进披露模式）：https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- 设计背景（Anthropic 工程博文）：https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
