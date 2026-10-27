# 结构化信息获取工具与 Skill 评测存档

本目录存放**已执行的测试结果与分析报告**，不依赖聊天记录或 GitHub Actions 临时 Artifacts，供后续选型、OpenSpec 设计与实现引用。报告属于特定版本、环境、数据集与信息需求下的**历史证据快照**，不代表当前环境必然可用，也不会自动点亮能力矩阵。

| 候选 | 类型 | 本地持久化报告 | 机器可读快照 | 已验证阶段 |
|---|---|---|---|---|
| CodeGraph Explorer | 独立项目分析 Skill 的确定性脚本 | [codegraph-explorer.md](codegraph-explorer.md) | [codegraph-explorer.results.json](codegraph-explorer.results.json) | 真实 Rust Dashu、Python Click，建图/结构化查询/来源缓存反例 |
| Python / Cargo / rustc / rust-analyzer / universal-ctags / ast-grep / tree-sitter CLI | 普通分析工具及环境候选 | [candidate-tools.md](candidate-tools.md) | [candidate-tools.results.json](candidate-tools.results.json)（观测摘要） | CI 环境探测及有限临时夹具 |
| Understand Anything、Graphify 等其他候选 | Skill / 工具 | [skill-candidate-status.md](skill-candidate-status.md) | 暂无 | 文档审核，**未在本项目批准的宿主实测** |

## 查阅与复用规则

1. 先查本目录的报告和 JSON 快照；对于**相同候选固定提交、相同测试仓库固定提交、相同采集方式及相同验收需求**，可重用既有历史性能与结论，**不要求每次重新运行测试**。
2. 报告记录测试日期、代码/工具提交、操作系统或 CI 环境、运行命令、具体源码、原始运行链接、通过/失败/未验证、可复用边界与风险。多个版本或条件须分别记录，不能覆盖旧证据或将新结果伪装为旧结果。
3. 需要判断**当前源码状态/当前工具可用性**时，历史报告只能用于候选选择和成本估计，不能替代实时来源指纹与权限检查；真实项目源码或工具版本变化时按影响范围补测，不强制无条件全量重测。
4. 当公共信息需求清单、解析契约、语言覆盖、候选行为、Skill 固定版本或验证门禁发生实质变化时，仅重测受影响信息需求，并另存新报告或新版本条目。已验证且不受影响的结论继续可复用。
5. **性能证据不等于结构化信息质量验收**，更不等于语言无关语义事实已经构造、入库或通过 S1–S12；禁止仅根据图谱节点数/边数宣称语义需求覆盖。
6. GitHub Actions Artifacts 用来保留运行时原始 JSON；它可能过期，因此须把关键测试结果、异常现象与证据链接写入本目录，不能只给 Artifact URL。敏感源码/秘密不可写入报告。

## 入口

- 扩展研究依据：[总调研](../semantic-tooling-survey.md)
- 测试与验证说明：[../../validation.md](../../validation.md)
- CodeGraph 真实项目测试脚本：`scripts/research/evaluate_codegraph_real_projects.py`
- CodeGraph 合成规模测试脚本：`scripts/research/evaluate_codegraph_skill.py`
- 候选工具探测脚本：`scripts/research/probe_candidate_tools.py`

> 状态基线：2026-10-27。该目录是持久化研究记录，不是生产运行时缓存或验证通过证书。
