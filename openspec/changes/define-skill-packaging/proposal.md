# Proposal（Skill 打包边界与能力组件寻址）

## Why

目标产物需要以单一 `layered-semantic-facts` Skill 完整安装和分发，使查询、构造、解析、矩阵及仓库接口在独立安装环境中可寻址。当前规划不能假定不存在的组件目录或 adapter 已交付，本变更定义目标安装与加载边界，对齐 AGENTS.md 采纳的 Agent Skills Specification。

## What Changes

- 定义自包含单 Skill 安装单元：SKILL.md 为入口，程序位于 scripts/，按需加载文档位于 references/，矩阵及机读 schema 等数据位于 assets/。不依赖开发仓库其他目录；外部工具和运行环境要求通过 compatibility 明确声明。
- 统一以 Skill 根目录为基准进行相对加载，按确定布局发现组件、文档及数据；缺失对象给出可定位原因。查询、构造器、解析器、矩阵及仓库的业务行为由各自子变更实现，包装负责安装与加载，不重复组件逻辑。
- 机读契约每种只保留一个权威资产，各组件同源消费主变更公共契约；不在包装层重新定义字段或保留分叉 schema。现有 assets/references 含旧协议，须由主变更完成公共契约更新后按统一布局分发，当前不能声称已一致可用。
- 开发期固化的信息需求清单及数据工件更新随重新安装或重新分发同步生效，运行期只读使用，不生成或扩展清单、不启动研究开发；开发期研究仅补未点亮条目，只有解析器开发流程完成接入验收后才可点亮，包分发不改变点亮状态；已点亮即验收可用，不另设生产状态。
- SKILL.md frontmatter 按规范约束 name、description、compatibility；name 与目录一致，description 说明做什么与何时使用；正文保持渐进披露，细节下沉 references/scripts。按 `skills-ref validate` 或不可用时逐项规范检查表验收。
- 在不包含开发仓库其余内容的安装环境验证入口、组件、公共契约和数据加载，按主变更用例检查完整查询链与真实缺口。安装/加载检查与真实端到端验收证据分别报告，且不增设矩阵生产状态，不能以找到路径代替生产能力交付。

## Capabilities

### New Capabilities

- `skill-packaging`：单 Skill 自包含分发、统一相对加载、公共契约单一权威、数据同步及 Agent Skills 规范符合性。

### Modified Capabilities

无。

## Impact

- 最新公共契约直接替换旧协议并统一消费者；不保留兼容入口、双轨协议或回退适配，不要求旧数据迁移工具或历史可读承诺。本轮仍只改规划文档。

- 本变更拥有目标包布局、SKILL.md 元数据/引用、安装与加载验证；不声明迁移或删除 capabilities/src/adapter 等不存在产物，不修改各组件业务语义。
- 主变更拥有总设计、公共契约、依赖编排和集成验收；各组件在各自子变更中实施，包装按这些交付进行集成安装。
- 本轮只修订现有 proposal/specs，不创建 design/tasks，不更改现有 Skill 资产或源码，不归档。后续布局决策引用 AGENTS.md 采纳的规范条款并纳入可判定验收。
