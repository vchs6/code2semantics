# Tasks

> 阶段顺序遵循配置驱动与 design 决策 5：统一加载入口先行 → 目录迁移 → SKILL.md 更新与规范校验 → 安装仿真与文档。每阶段以全量回归为验证，迁移后 `capabilities/` 不再存在。

## 1. 统一加载入口（现布局可先行落地）

- [x] 1.1 实现 `scripts/layout.py`（锚定 Skill 根的布局解析：组件模块路径注册、`assets/matrix`/`assets/schema` 工件解析、缺件报可定位错误）。验证：pytest 覆盖 spec「组件与数据工件固定布局可寻址」两个 scenario（寻址成功、缺件可定位）
- [x] 1.2 tests conftest 收敛为经 `layout.py` 注入路径（一处注入）。验证：全量 pytest 通过，仓内测试文件不再各自 `sys.path.insert` 拼凑

## 2. 目录迁移（src→scripts 更名 + 组件迁入 + 数据工件归 assets）

- [x] 2.1 `skills/layered-semantic-facts/src/` 更名 `scripts/`，`capabilities/tools/{matrix_tool,info_parser,constructor}` 迁入 `scripts/` 下，import 与包路径随迁适配。验证：全量 pytest（矩阵+解析器+构造器+查询侧）全绿
- [x] 2.2 `capabilities/{matrix,schema}` 迁入 `assets/{matrix,schema}`，数据加载点（矩阵工具 common、构造器契约校验、加载入口）改经 `layout.py`；`references/` 机读 schema 副本删除并在文档中指向权威路径。验证：全量 pytest 全绿；矩阵播种/点亮/查询在 `assets/matrix` 上可运行；仓内仅存一份契约 schema
- [x] 2.3 SKILL.md 同步更新：frontmatter 增 `compatibility` 字段（运行依赖：Python 3.10+、PyYAML、jsonschema、cargo），执行流程描述与文件引用随迁移同步（`scripts/`、`assets/schema/` 路径）。验证：SKILL.md 引用路径全部存在；正文 <500 行
- [x] 2.4 移除 `capabilities/` 顶层目录（含 `tools/e2e.py`，其验证职责由 3.2 安装仿真承接）。验证：`capabilities/` 不存在；全量 pytest 全绿

## 3. 规范校验、安装仿真与文档

- [x] 3.1 Agent Skills 规范符合性校验：优先 `skills-ref validate`（实施首日核实工具可用性），不可用时按规范对照检查表逐项判定（frontmatter 字段与约束、`scripts/`/`references/`/`assets/` 目录结构、渐进披露）。验证：校验通过或检查表逐项通过（spec「目录布局与元数据符合业界规范」scenario）
- [x] 3.2 安装仿真测试：tmp 独立环境仅复制 Skill 目录 → 以契约发起 indicatif 项目级查询 → 产出符合 output-schema 的事实集；矩阵播种更新后重装 → 查询按新矩阵选择生产者。验证：pytest 覆盖 spec「Skill 目录自包含且可独立运行」「数据工件随更新同步生效」scenario
- [x] 3.3 Skill 文档补安装/部署约定（安装=目录整体复制、运行依赖已由 `compatibility` 字段声明、`scripts/`/`references/`/`assets/` 布局说明、新组件一律生成于 `scripts/` 并经 `layout.py` 注册）。验证：文档落盘且与布局一致
