# Proposal（语义事实集需求调研）

## Why

项目 `code2semantics` 在进入设计前，必须先回答"软件项目语言无关的语义表达需要哪些事实"。这是独立于工具能力的一个调研问题：事实需求由语义表达目标决定，不因现有工具能做什么而改变。只有先形成事实集清单，epic 的三份设计（fact-catalog / contract-format / output-schema）才有封闭边界。顺序不可颠倒，避免"契约无事实可依"。

## What Changes

- 产出**语义事实集需求清单**（文档工件，非代码变更）：归纳软件项目语言无关的语义表达所需事实，给出事实类型、语言无关语义词汇与字段描述；**分层结构不预设**，由调研经分析与汇总后按照语义描述的对象、粒度和抽象程度划分（层级数量与名称是调研结论，非输入假定），但至少需要表达出从软件项目整体逐步深入到具体实现算法（代码级）的语义事实。
- 清单一次成稿、有界不扩张（见 design 调研有度规则）。
- 清单落盘至变更目录 `research/semantic-fact-requirements.md`，作为 `epic-layered-semantic-fact-skill` 的直接输入：fact-catalog 以本清单为蓝本；epic 亦依据本清单提出对生产能力调研（`survey-info-acquisition-tools`）的调研要求。

## Capabilities

### New Capabilities

（无——本变更为纯调研/文档工件，不引入系统行为，已设 `skip_specs: true`。）

### Modified Capabilities

（无。）

## Impact

- 不影响任何代码、API 或依赖。
- 影响：为 `epic-layered-semantic-fact-skill` 的 fact-catalog 提供蓝本；epic 以本清单为依据拟定 `survey-info-acquisition-tools` 的调研要求。产出物仅存在于 openspec 变更目录内。
