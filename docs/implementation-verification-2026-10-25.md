# 实施核验台账（2026-10-25）

基线：`main` 的 `fdb281326451dc97c5e1869fbaf85f543e930f9f`；验证分支 `chore/verify-implementation-20261025`。本报告只记录证据，不把代码存在视为完整验收，也不改动既有 OpenSpec 勾选。

## 自动化测试（GitHub Actions）

首轮运行：https://github.com/vchs6/code2semantics/actions/runs/40207357369

| 检查 | 通过 | 失败 | 跳过 | 证据边界 |
| --- | ---: | ---: | ---: | --- |
| `python -m pytest tests/repository -q -ra -p no:cacheprovider` | 31 | 0 | 0 | 仅现有 repository tests |
| `python -m pytest tests/capability_matrix -q -ra -p no:cacheprovider` | 14 | 0 | 0 | 仅现有 matrix tests |
| `validation/validate_contracts.py` | 7 schema, 64 shape, 30 semantic | 0 | - | 输出为 `design_assets_pass`，`runtime_verified=false` |
| 全活动 OpenSpec strict | 前 6 个变更通过 | 1 个 CI 枚举错误 | - | 错把 `openspec/changes/archive` 当作活动变更；已修正脚本，复验见 Actions |

首次 OpenSpec 作业失败属于 CI 遍历范围错误，不是已经完成校验的六个变更不合法。修正后结果需要以本分支最新 CI 运行为准。

## 事实仓库 tasks.md 对照

- 1.1–1.5：已标记完成；ContractCodec 的测试、实现和验证记录存在。
- 2.1–2.5：任务仍未勾选；`store.py`、`test_store.py` 已存在并在 31 项仓库测试内通过，但没有逐项审核“精确行级存储、不同来源、重开、最小返回”等所有验收要求；不得自动勾选。
- 3.1–3.5：任务仍未勾选；`test_transactions.py` 已存在，当前测试集通过；局部字段/关系/证据/冲突失效更新覆盖不完整，尚不得宣称全组完成。
- 4.1–4.5：任务仍未勾选；`tests/repository/test_validity.py` 尚未出现在检查基线，当前有效性、前提、导航去重、环和 external 的完整验收缺证。
- 5.1–5.4：任务仍未勾选；`tests/repository/test_transfer.py` 尚未出现在检查基线，导入/导出、备份/恢复的验收缺证。
- 6.1–6.4：任务仍未勾选；`tests/repository/test_acceptance.py` 尚未出现在检查基线，尚无端到端仓库验收证据。

## 主变更与依赖

主变更任务清单 2–4 组公共设计/契约已勾选；其 5–8 组关于工具研究、解析器、构造器、归纳、查询及端到端的任务仍需逐项完成和验收。能力矩阵任务清单已全部勾选，现有 14 项测试通过；与主变更集成验收是不同门槛。

**仍未完成的验证**：真实工具调用→解析→归纳→FactBatch→SQLite 持久化→重开→最小查询/响应；多来源状态变化、备份恢复、并发/事务等未覆盖任务的新增测试。CI 通过不应被解释为这些环节已完成。

## 后续执行顺序

1. 接受当前 CI 的全部严格 OpenSpec 校验结果，若失败按具体 change 定位并修复。
2. 按 TDD 为仓库任务 3–5 组先补 RED 用例，再实现 GREEN；运行整组 pytest 回归。
3. 补仓库验收测试，再与构造器/查询/解析器/归纳接口集成。
4. 按实际测试、审查和提交证据逐项勾选 tasks.md，并回填 `implementation-validation.md`，不得以计划代替验收。
5. 完成真实端到端执行、严格校验及独立评审后才将主变更标记为可验收。

本台账的 CI 与静态审计不代表已执行新增产品实现。
