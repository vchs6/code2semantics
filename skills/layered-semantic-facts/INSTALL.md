# 安装与部署（layered-semantic-facts）

## 安装方式

安装 = **复制本 Skill 目录整体**到目标环境（含 `SKILL.md`、`scripts/`、`references/`、`assets/`）。目录自包含，不依赖仓库其他部分。

## 运行依赖

- Python 3.10+（含标准库）
- PyYAML、jsonschema（pip 安装）
- cargo 在 PATH 上（Rust 项目分析时需要；其他语言随对应工具链扩展）

运行依赖的规范声明位为 `SKILL.md` frontmatter 的 `compatibility` 字段。

## 目录布局

| 目录 | 内容 |
|---|---|
| `SKILL.md` | 技能元数据与执行流程（渐进披露第二级） |
| `scripts/` | 全部程序代码：查询流程编排层（orchestrator/coverage/synthesizer/repo_stub/versioning）、能力组件（constructor/、info_parser/、matrix_tool/）、统一加载入口 `layout.py` |
| `references/` | 按需加载的人读文档（fact-catalog、contract-format、output-schema、report-template） |
| `assets/schema/` | 机读 schema **单一权威**（contract/output/info-contract/矩阵三 schema） |
| `assets/matrix/` | 能力矩阵数据工件（entries/producers/info-needs + history） |

## 数据工件更新

`assets/matrix/` 的权威即仓库内本目录：调研播种/点亮更新后，**重新分发（再复制）**即对安装环境同步生效，无需迁移步骤。

## 新增能力组件约定

- 新组件（如新解析器）一律生成于 `scripts/` 之下；
- 经 `scripts/layout.py` 的 `register_skill_paths()` 注册加载路径，数据工件经 `resolve_asset()` 定位；
- MUST NOT 在组件或测试内自行 `sys.path` 拼凑（布局缺件由 `LayoutError` 报出可定位错误）。
