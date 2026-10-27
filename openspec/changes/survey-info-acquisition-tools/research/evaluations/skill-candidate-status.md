# 独立项目分析类 Skill 候选：证据等级与复测状态

**存档日期：** 2026-10-27。本文件为独立 Skill 候选的**已知证据索引**，优先参考已经保存的研究，不因新会话而重新检索或运行相同测试。完整论据在 [总调研报告](../semantic-tooling-survey.md) 第 8 节。

| 候选 | 现有证据 | 当前可复用结论 | 尚未验证 |
|---|---|---|---|
| [CodeGraph Explorer](https://github.com/GoldDHacker/codegraph-explorer-skill) | **真实执行**；固定版本、本地 Python 构建脚本、Dashu 和 Click | 能生成结构化图谱并执行局部查询；有实际耗时记录；大量 INFERRED 关系；同 mtime 内容变化可导致增量缓存过期 | 与普通工具同质量对照、跨语言语义关系、最终规范化适配；宿主内 Skill 调用 |
| [Understand Anything](https://github.com/Egonex-AI/Understand-Anything/tree/main/understand-anything-plugin/skills/understand) | **公开 Skill 文档检查** | 声称可构建 `.ua/knowledge-graph.json`，带节点和边；设计包含多语言/确定性扫描和可选 LLM 审查 | 未在本项目授权宿主安装/运行；真实图谱、耗时、Token、证据覆盖和混合语言质量 |
| [Graphify](https://github.com/Graphify-Labs/graphify) / [Graphify Skill](https://github.com/darce07/graphify-claude-skill) | **公开代码及 Skill 文档检查** | 文档描述本地 AST 结构提取生成图 JSON、定向图查询；代码与文档语义步骤的模型成本需分开 | 未在本项目固定版本实测；各语言准确率、真实项目成本与来源证据 |
| [codebase-analysis](https://github.com/JakubMikolajek/codex-skills-collection/tree/main/skills/codebase-analysis) | **公开 Skill 文档检查** | 项目结构、依赖和架构盘点流程可作为对照 | 未验证是否有稳定机器输出、实际证据定位、Token 及混合语言能力 |
| [codebase-summary](https://github.com/smyrick/skills/tree/main/skills/codebase-summary) | **公开 Skill 文档检查** | 侧重证据导向的架构摘要，可作为模型阅读型对照 | 未运行宿主，也未验证结构化输出/源指纹与成本 |
| [explaining-codebases](https://github.com/analyticalmonk/explain-this/tree/main/skills/explaining-codebases) | **公开 Skill 文档检查** | 解释程序机制与架构路径的流程候选 | 依赖 `creating-explainers`；未证明可独立运行或稳定结构化结果 |
| [improve-codebase-architecture](https://github.com/jae-labs/skills/tree/main/skills/improve-codebase-architecture) | **既有总报告中的候选条目** | 偏向架构重构建议，而不是事实获取；**原始 Skill 文件与存在性仍应复核** | 不能认定已经运行或独立验证，不授予任何生产覆盖 |

## 准入与缓存规则

- **已验证输出**指独立可重跑命令或宿主执行所产生的明确机器数据、来源/版本以及已核查的样例；仅阅读 SKILL.md 不能升级为已验证。
- **历史报告可复用**，用于候选筛选、成本预估、已知风险和设计论证；当固定版本、测试数据、验收口径与权限要求均未改变时，不需要每次从零调查。
- **新需求可以增量评测**：只补未知语言、未覆盖信息需求、未验证输出或版本差异。不同候选的结果不可因输出同名 `graph.json` 就认为等价。
- 调研对象是**结构化项目信息获取者**。不能以尚未生成 F1–F18 语言无关事实作为淘汰理由；事实构造、信息有效性和语义归纳由统一构造器处理。
- 宿主安装和权限可能随时间变化；历史状态不能证明新环境可调用。未通过数据质量与解析验收的候选始终不点亮生产能力矩阵。

## 优先链接

- [CodeGraph Explorer 真实执行报告](codegraph-explorer.md) / [机器摘要](codegraph-explorer.results.json)。
- [普通工具已执行探测报告](candidate-tools.md) / [机器摘要](candidate-tools.results.json)。
- [总调研报告](../semantic-tooling-survey.md)。

**本文件不是新实测结果，也不宣称已经完成不同候选之间的质量/成本对照。**
