---
name: layered-semantic-facts
description: 按查询契约从项目源码提取最小、分层、语言无关的语义事实集（机器可读 JSON 或人可读报告）。支持契约查询模式与对话派生模式。触发词：语义事实、语义分析、项目有哪些模块/入口/接口/依赖、按契约取事实、fact-catalog、查询契约。
compatibility: Requires Python 3.10+, PyYAML, jsonschema; cargo on PATH for Rust project analysis
---

# layered-semantic-facts

跨代理环境通用的语义事实提取 Skill。职责：语义事实的提取与呈现，交付机器可读语义事实集与人可读语义事实汇总报告两种输出（见主提案「职责边界」）。事实的下游工作流（迁移规划、语言映射、代码生成）不在本 Skill 职责内。

## 模式路由

1. 输入为结构化查询契约 → **契约查询模式**。
2. 输入为自然语言对话（未形成契约）→ **对话派生模式**：先从对话提取契约，再进入契约查询模式，最后渲染人可读报告。

## 硬性规则（两种模式共同遵守）

- 项目位置缺省：契约未含 `project` 时，以宿主当前工作目录补齐并在输出标注。
- 封闭世界：契约引用的事实类型 MUST 属于可提供事实目录（`references/fact-catalog.md`）；目录外引用判"超出范围"，MUST NOT 编造。
- 最小化：输出仅含契约要求的层与字段；未要求的层与字段 MUST NOT 出现。
- 缺口显式：目录内但项目中缺失的事实进 gaps，MUST NOT 编造填充。
- 证据绑定：每条事实附源码证据定位（文件:行号范围），指向真实存在的源码位置。
- 意图不明先澄清：对话不足以构成可执行契约时，先澄清，不猜测产出。

## 契约查询模式执行流程

查询由确定性程序 `scripts/orchestrator.py` 编排（仓库透读模式，见 `add-semantic-fact-query`）：

1. **契约校验**：按 `references/contract-format.md` 与机读 schema（`assets/schema/contract.schema.json`）校验；目录外引用 → out_of_scope，不编造。
2. **仓库透读**：按（项目、版本）读事实仓库；命中即返回，未命中才触发事实构造（构造器在 `scripts/constructor/`）。
3. **构造定向**：构造任务仅含缺口对应的事实节点，按层自顶向下（父节点缺失先构造父节点）；构造器声明的缺口不再重触发。
4. **循环终止**：差集为空，或本轮构造未产生新入库事实，MUST NOT 无限重试。
5. **下一级返回**：输出仅含已请求节点的下一级——值属性直出（value），子树节点仅标注（is_subtree=true），内容由消费方续查（契约 `facts` 对象形态的 `path`）。
6. **输出**：机器可读 JSON，按 `references/output-schema.md`（机读权威 `assets/schema/output.schema.json`）；gaps（含字段级精确原因）与超出范围分列，标注真实版本。

构造器缺席时降级只读：命中项正常返回，未命中项进 gaps 并标注原因，MUST NOT 退化回现场即兴提取。

**代理归纳协作**：构造器对"无工具直出数据项、但有已点亮智能体兜底/分析Skill 生产者"的缺失事实类型，在输出 `induction_requests` 中给出结构化归纳请求（事实类型 + fact-catalog 字段 + 信息需求指导），并在 gaps 标注"待代理归纳"。此时由运行本 Skill 的代理按请求做语义归纳（认知型任务，不经解析器），以 `inducer` 钩子传回：`construct(..., inducer=fn)`，归纳结果经契约校验后并入 facts；目录外类型被拒收，未被覆盖的请求保持暴露。MUST NOT 在无归纳请求时自行编造归纳类事实填充。

## 对话派生模式执行流程

1. **意图识别**：从用户对话识别想了解的事实。
2. **契约提取**：整理为与契约查询模式同结构的契约（项目位置缺省补全）。
3. **澄清时机**：意图不足以构成契约时（如只说"帮我看看这个项目"），按 fact-catalog 列出可选事实类型与典型契约示例，请用户明确后再执行。
4. **调用契约查询模式**执行提取。
5. **渲染报告**：从事实集按 `references/report-template.md` 渲染人可读 Markdown（单一事实源，不平行提取）。

## 参考文件

- `references/fact-catalog.md`：可提供事实目录（封闭边界、层级、字段）
- `references/contract-format.md`：查询契约格式与校验规则
- `references/output-schema.md`：机器可读事实集 schema
- `references/report-template.md`：人可读报告模板

程序代码位于 `scripts/`（查询流程编排层与构造器、解析器、矩阵工具能力组件，经 `scripts/layout.py` 统一加载）；机读 schema 权威位于 `assets/schema/`，能力矩阵数据位于 `assets/matrix/`。安装方式：复制本 Skill 目录整体到目标环境。
