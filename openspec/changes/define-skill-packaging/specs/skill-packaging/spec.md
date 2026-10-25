# Spec Delta

## Purpose

定义 `layered-semantic-facts` Skill 的自包含安装形态：程序代码位于 Skill 目录 `scripts/`，能力组件与数据工件随包分发、固定布局可寻址，契约同源，数据工件随更新同步生效。安装后的 Skill 在独立环境中可完成端到端语义事实查询。

## ADDED Requirements

### Requirement: Skill 目录自包含且可独立运行
Skill 目录 SHALL 为自包含安装单元：程序代码全部位于 Skill 目录的 `scripts/` 目录内（含查询流程编排层与构造器、解析器等能力组件）；安装（复制 Skill 目录整体）到独立环境后，端到端语义事实查询（契约 → 构造 → 事实集）SHALL 可运行，MUST NOT 依赖安装环境中的其他仓库目录。

#### Scenario: 安装到独立环境后端到端查询可运行
- **WHEN** Skill 目录整体被安装到不含开发仓库其余部分的环境，并以查询契约发起项目级语义事实查询
- **THEN** 查询产出符合输出契约的语义事实集，全过程不因组件定位失败而中断

#### Scenario: 程序代码位于 scripts 目录
- **WHEN** 查看 Skill 安装包内容
- **THEN** 全部可执行程序代码位于 `scripts/` 目录内，安装包内无 `scripts/` 之外的程序代码目录

### Requirement: 组件与数据工件固定布局可寻址
能力组件（构造器、解析器、矩阵工具）与数据工件（能力矩阵、契约机读 schema）在 Skill 目录内 SHALL 有固定布局；Skill 经**统一加载入口**按该布局定位组件与工件，寻址 SHALL 给出确定结果或可定位的失败原因（缺哪个组件/工件、在何处期望）。MUST NOT 出现散落在各组件与测试中的路径拼凑加载。

#### Scenario: 组件与工件寻址成功
- **WHEN** 安装后的 Skill 按统一加载入口请求构造器、解析器、矩阵工件与契约 schema
- **THEN** 各依赖以确定路径返回，端到端链路可建立

#### Scenario: 组件缺失可定位
- **WHEN** 安装包内容不完整（某组件或数据工件缺失）
- **THEN** 统一加载入口报出缺失对象及其期望布局位置，MUST NOT 以静默降级或错误路径继续

### Requirement: 契约权威单一
查询契约与输出契约的机读 schema 在 Skill 目录内 SHALL 仅有一份权威副本；Skill 编排层与构造器 SHALL 同源加载该副本，MUST NOT 存在因迁移或复制产生的分叉副本。

#### Scenario: 编排层与构造器契约同源
- **WHEN** Skill 编排层与其调用的构造器分别校验同一查询契约
- **THEN** 双方依据的契约机读 schema 为同一份权威副本（同源加载），校验结果一致

### Requirement: 数据工件随更新同步生效
能力矩阵等数据工件的权威即仓库内 Skill 目录本身；仓库内经调研播种/点亮更新后，重新安装（分发）的 Skill SHALL 携带更新后的数据工件，安装环境无需额外迁移步骤。

#### Scenario: 矩阵更新随重新安装生效
- **WHEN** 仓库内 Skill 目录中的能力矩阵经播种/点亮更新，且安装环境重新安装该 Skill
- **THEN** 安装后的 Skill 查询即按更新后的矩阵选择生产者，无需手工同步数据文件

### Requirement: 目录布局与元数据符合业界规范
Skill 目录布局与 SKILL.md 元数据 SHALL 符合业界 Agent Skills 规范：SKILL.md frontmatter 含 `name`（与父目录名一致、命名约束合规）与 `description`（含做什么与何时使用），以及声明运行环境要求的 `compatibility` 字段；程序代码位于 `scripts/`、人读文档位于 `references/`、数据工件位于 `assets/`。符合性 SHALL 经规范校验工具或对照检查表判定。

#### Scenario: 规范校验通过
- **WHEN** 以 Agent Skills 规范校验（如 `skills-ref validate`）检查 Skill 目录
- **THEN** frontmatter 字段与命名约束、推荐目录结构均通过校验，无违规项
