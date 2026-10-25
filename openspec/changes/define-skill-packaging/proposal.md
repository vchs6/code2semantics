# Proposal（Skill 打包边界与能力组件寻址）

## Why

`layered-semantic-facts` Skill 的运行时依赖（查询流程编排层 → 构造器 → 解析器 → 能力矩阵与契约 schema）分布在 `skills/layered-semantic-facts/` 与 `capabilities/` 两个目录树中，Skill 目录被单独安装/复制到其他机器或项目时无法运行；跨目录 import 依赖硬编码相对路径拼凑，契约存在两处副本仅靠路径巧合保持一致。能力组件**本应随 Skill 一并安装分发**——归属边界从未按"安装单元"定义，构成分发缺口。本变更以业界 **Agent Skills 规范**（agentskills/agentskills：SKILL.md 元数据、`scripts/`/`references/`/`assets/` 目录约定、`compatibility` 字段、渐进披露）为对齐基准，使最终制品既自包含又符合业界标准。

## What Changes

- **能力组件迁入 Skill 目录**：`capabilities/tools`（构造器、解析器、矩阵工具）与 `capabilities/schema`、`capabilities/matrix`（契约机读 schema、能力矩阵数据工件）收编至 `skills/layered-semantic-facts/` 之下；`capabilities/` 顶层目录随之移除。Skill 目录自此**自包含**——整体即安装包，安装后可独立运行，MUST NOT 依赖仓库其他目录。
- **随包内容按规范三分**：程序代码（含 `src/` 更名与迁入组件）一律位于 **`scripts/`**；人读契约/输出文档留 **`references/`**；数据工件（能力矩阵、契约机读 schema）按业界规范落 **`assets/`**（规范对静态资源与数据文件含 schema 的推荐目录）。SKILL.md frontmatter 增 `compatibility` 字段声明运行依赖（规范规定的环境要求标准声明位）。
- **SKILL.md 同步更新**：`src/`→`scripts/` 更名与机读 schema 移出 `references/` 后，SKILL.md 内执行流程描述与文件引用同步更新（渐进披露第二级的行为载体）。
- **辅助演示脚本不随迁**：`capabilities/tools/e2e.py`（跨变更演示脚本）不属于 Skill 运行组件，不迁入 `scripts/`；其验证职责由安装仿真测试承接，原文件随 `capabilities/` 移除。
- **契约权威单一**：查询契约与输出契约机读 schema 在 Skill 内仅一份权威副本（`assets/schema/`），Skill 编排层与构造器同源加载，MUST NOT 出现分叉副本。
- **统一加载入口**：跨组件加载收敛为单一寻址入口（锚定 Skill 根的确定布局），消除散落在各组件与测试中的路径拼凑。
- **数据工件同步生效**：能力矩阵等数据工件的权威即仓库内 Skill 目录，调研播种/点亮更新后随安装（重新分发）对安装环境生效。
- **规范符合性可判定验收**：以 Agent Skills 规范校验（`skills-ref validate` 或对照检查表：frontmatter 字段与约束、推荐目录结构、渐进披露）作为验收手段之一。

## Capabilities

### New Capabilities

- `skill-packaging`：Skill 自包含安装形态——安装后的 Skill 在独立环境中可完成端到端语义事实查询（程序代码位于 `scripts/`，数据工件位于 `assets/`，契约同源，数据工件随更新同步生效），且目录布局与元数据符合业界 Agent Skills 规范。

### Modified Capabilities

（无。既有变更的能力需求不受影响；目录归属迁移由本变更执行，已完成变更的工件为其时点记录，不追改。）

## Impact

- 迁移：`capabilities/tools/{matrix_tool,info_parser,constructor}` → `skills/layered-semantic-facts/scripts/`；`capabilities/{schema,matrix}` → `skills/layered-semantic-facts/assets/{schema,matrix}`；`skills/layered-semantic-facts/src/` → `scripts/`；`capabilities/tools/e2e.py` 随 `capabilities/` 移除（验证职责转安装仿真测试）。
- 修改：SKILL.md（`compatibility` 字段、执行流程引用与文件引用同步）；`constructor_adapter.py` 与各测试文件的路径注入收敛到统一加载入口。
- 关联但不在本变更修改：构造器、解析器、矩阵的组件行为逻辑（各自提案已定稿，本变更只迁移落位不改行为）；`add-semantic-fact-repository`（SFRS）的存储语义。
- 影响范围：此后新增能力组件（新解析器等）一律生成于 Skill 目录 `scripts/` 内并经统一加载入口注册；Skill 分发对外符合业界 Agent Skills 规范。
