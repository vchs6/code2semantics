# Design

## Context

现状（已核实落盘）：Skill 运行链路的组件分散两处——`skills/layered-semantic-facts/`（SKILL.md、references/ 契约文档与机读 schema、src/ 查询流程程序）与 `capabilities/`（schema/ 矩阵与信息契约机读 schema、matrix/ 能力矩阵数据、tools/ 下 matrix_tool、info_parser、constructor、e2e.py）。跨目录 import 靠测试文件与 `constructor_adapter.py` 中的 `sys.path.insert` 硬编码拼凑；查询契约 schema 在 `skills/.../references/contract.schema.json` 与 `capabilities/schema/` 各存一份。用户裁决（2026-10-23）：能力组件生成时就应落在 Skill 目录内、随包一并安装；程序代码目录命名 `scripts/`；最终制品须符合业界 Agent Skills 规范（proposal「Why」声明对齐基准）。

## Goals / Non-Goals

**Goals:**

- 定义 Skill 目录内的固定布局（`scripts/` 代码、`references/` 文档、`assets/` 数据工件），使 Skill 目录自包含、整体即安装包，且符合业界 Agent Skills 规范。
- 定义统一加载入口，消除 sys.path 拼凑；迁移既有组件落位并保持全量测试通过。
- 保证契约权威单一、数据工件随更新同步生效；规范符合性可判定验收。

**Non-Goals:**

- 不改构造器、解析器、矩阵的组件行为逻辑（各自提案已定稿，本变更只迁移落位）。
- 不设计多 Skill 共享组件库或版本化分发机制（无需求支撑，见 Open Questions）。
- 不改查询契约与输出契约语义。

## Decisions

1. **Skill 目录固定布局（按 Agent Skills 规范三分）**：`scripts/` 承载全部程序代码（现有 `src/` 查询流程更名迁入；`matrix_tool/`、`info_parser/`、`constructor/` 自 `capabilities/tools/` 迁入同置于 `scripts/` 下）；`references/` 仅保留人读契约/输出文档；`assets/matrix/` 承载能力矩阵数据文件、`assets/schema/` 承载矩阵与信息契约机读 schema（自 `capabilities/{matrix,schema}` 迁入）——`assets/` 为规范对静态资源与数据文件（含 schema）的推荐目录。`capabilities/tools/e2e.py` 为跨变更演示脚本，不属于 Skill 运行组件，不迁入（验证职责转安装仿真测试，随 `capabilities/` 移除）。SKILL.md frontmatter 增 `compatibility` 字段（运行依赖标准声明位），执行流程描述与文件引用随迁移同步更新。备选（保留 `capabilities/` 子树整体搬移）被否——顶层目录语义与 Skill 结构无关联；备选（数据目录命名 `data/`）被否——偏离规范推荐命名，经用户裁决 2026-10-23 改齐；备选（e2e.py 随迁并标注演示用途）被否——混入运行时组件目录违反规范「scripts 自包含或声明依赖」精神。依据：proposal「What Changes」1/2/3/4、Agent Skills 规范（Directory structure、`compatibility`、scripts 约定）、用户裁决 2026-10-23。
2. **统一加载入口锚定 Skill 根**：`scripts/` 下新增 `layout.py`，以本文件位置锚定 Skill 根，提供组件模块路径注册与数据工件路径解析（`resolve_asset("matrix")` 等）；全部跨组件 import 与数据加载经它进行，各组件与测试 MUST NOT 自行 `sys.path` 拼凑；布局缺件时报可定位错误（缺哪个、期望何处）。备选（依赖调用方注入路径）被否——现状即注入拼凑，是缺陷来源。依据：spec「组件与数据工件固定布局可寻址」、proposal「What Changes」6。
3. **契约权威单一在 `assets/schema/`**：查询契约与输出契约机读 schema 仅保留 `assets/schema/` 一份权威，Skill 编排层与构造器同源加载；`references/contract.schema.json` 等机读副本删除，references 文档中指向权威路径。备选（保留 references 副本加一致性校验）被否——两副本靠校验维持一致仍可能漂移。依据：spec「契约权威单一」、proposal「What Changes」5。
4. **安装形态即目录复制**：安装 = 复制 Skill 目录整体；仓库内 Skill 目录为数据工件权威，调研播种/点亮更新后重新分发即同步生效。验证：安装仿真测试（tmp 独立环境复制安装 → 端到端查询 → 矩阵更新后重装生效）。依据：spec「Skill 目录自包含且可独立运行」「数据工件随更新同步生效」。
5. **迁移以全量回归 + 规范校验为准出**：目录迁移完成后，既有全部 pytest 经布局适配 MUST 全绿；Skill 目录 MUST 通过 Agent Skills 规范校验（`skills-ref validate`，不可用时以对照检查表逐项判定：frontmatter 字段与约束、推荐目录结构、渐进披露）。TDD 驱动迁移步骤与加载入口。依据：AGENTS.md 原则 7/8、proposal「What Changes」8、spec「目录布局与元数据符合业界规范」。

## Risks / Trade-offs

- [迁移触及大量测试文件的路径注入] → 统一加载入口先行（tests conftest 收敛为一处注入），迁移分步：入口 → 迁移 → 收敛 → 回归，每步全量可跑。
- [外部引用 capabilities/ 路径的文档与工件（已完成变更的 design/tasks、memory 记录）失效] → 已完成变更工件为时点记录不追改；以本变更 proposal「Impact」声明路径变更，memory 以新路径覆盖更新。
- [`skills-ref validate` 工具在当前环境不可用] → 验收降级为对照检查表逐项判定（spec 已声明"校验工具或对照检查表"两种手段）；工具可用性在实施首日核实。
- [安装环境缺 Python 依赖（yaml/jsonschema）] → 运行依赖写入 SKILL.md `compatibility` 字段（决策 1）；打包机制不引入额外打包工具（无需求支撑，不预设）。

## Migration Plan

纯迁移 + 新增加载入口：`capabilities/` 整体迁入 Skill 目录后删除；`src/` 更名 `scripts/`；`e2e.py` 移除。回滚 = git 恢复目录布局。迁移后旧路径不存在，无双轨期。

## Open Questions

1. **多 Skill 共享能力组件**：若未来出现第二个 Skill 消费构造器/解析器，组件是否抽为共享库（脱离单 Skill 安装单元）。当前无需求支撑，出现时另立变更评估。
