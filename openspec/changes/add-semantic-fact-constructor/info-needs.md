# 信息需求清单（构造器合成分析产出）

> 以下字段为语义归纳类信息，无确定算法可依，不映射为工具信息需求；其生产按生产阶梯由项目分析 Skill / 智能体兜底承担（见调研报告第 4/5 节）。

## 信息需求条目

| 事实类型 | 层 | 字段 | 信息需求 | 归纳类 |
|---|---|---|---|---|
| 使用契约 | 事实层 | preconditions | 前置条件归纳（doc panics/Errors 段 + 上下文） | 是 |
| 使用契约 | 事实层 | parameter_constraints | 参数约束（签名类型约束直出 + 归纳） | 是 |
| 使用契约 | 事实层 | guarantees | 返回保证归纳（签名 + doc） | 是 |
| 元素实现语义 | 事实层 | summary | 行为摘要/算法意图归纳 | 是 |
| 元素实现语义 | 事实层 | control_flow | 分支/循环结构（AST 模式直出） | 否 |
| 元素实现语义 | 事实层 | data_flow | 变量级数据流归纳 | 是 |
| 入口 | 项目层 | entries | bin target 清单与 src_path（cargo metadata targets） | 否 |
| 公共接口 | 符号层 | signature | 函数/方法签名文本（ctags signature / rustdoc JSON） | 否 |
| 公共接口 | 符号层 | visibility | 可见性（pub 声明检索） | 否 |
| 公共接口 | 符号层 | module | 符号-模块归属（文件路径映射） | 否 |
| 外部依赖 | 项目层 | dependencies | 依赖清单（cargo metadata dependencies：name/req/kind/optional） | 否 |
| 对外接口 | 模块层 | public_entries | 模块 pub 入口清单（pub fn/struct 声明检索） | 否 |
| 意图声明 | 符号层 | intent | doc 注释原文（///、//! 文本抽取，与符号绑定） | 否 |
| 数据流 | 事实层 | source | 数据产生点归纳（变量级数据流分析） | 是 |
| 数据流 | 事实层 | sink | 数据消费点归纳（变量级数据流分析） | 是 |
| 构建与运行形态 | 项目层 | build | 构建系统与产物形态（cargo metadata edition/crate_types） | 否 |
| 构建与运行形态 | 项目层 | run | 运行/测试/验证命令（cargo 惯例命令） | 否 |
| 构建与运行形态 | 项目层 | deployment | 部署形态归纳（CLI/库/服务） | 是 |
| 模块划分 | 项目层 | modules | workspace 成员/顶层 mod 清单（cargo metadata members + 源码 mod 声明） | 否 |
| 模块职责 | 模块层 | path | 模块路径（mod 声明与文件结构） | 否 |
| 模块职责 | 模块层 | responsibility | 职责描述归纳 | 是 |
| 模块职责 | 模块层 | capabilities | 暴露能力归纳（pub 项清单 + 归纳） | 是 |
| 模块间依赖 | 模块层 | direction | 依赖方向（crate 级依赖 + 源码 use/mod 结构） | 否 |
| 模块间依赖 | 模块层 | type | 依赖类型判定归纳（调用/数据/配置） | 是 |
| 生命周期/状态 | 事实层 | resource | 资源创建/释放点（Drop impl/new 模式检索） | 否 |
| 生命周期/状态 | 事实层 | transitions | 状态迁移语义归纳 | 是 |
| 符号关系 | 符号层 | relation | 继承/实现/组合关系（impl/trait 模式匹配） | 否 |
| 符号关系 | 符号层 | target | 目标符号（impl T for U 的 T/U） | 否 |
| 符号关系 | 符号层 | module | 符号-模块归属（文件路径映射） | 否 |
| 类型定义 | 符号层 | kind | 结构体/枚举/trait 分类（符号清单 kind） | 否 |
| 类型定义 | 符号层 | description | 类型语义描述归纳 | 是 |
| 类型定义 | 符号层 | fields | 字段/variant 清单（ctags field/variant kinds） | 否 |
| 行为约定 | 事实层 | invariant | 不变量归纳 | 是 |
| 行为约定 | 事实层 | side_effect | 副作用归纳 | 是 |
| 行为约定 | 事实层 | timing | 并发/时序约束归纳 | 是 |
| 调用关系 | 事实层 | caller | 调用方符号（调用链工具输出） | 否 |
| 调用关系 | 事实层 | callee | 被调方符号（调用链工具输出） | 否 |
| 调用关系 | 事实层 | condition | 调用条件线索归纳（分支上下文） | 是 |
| 配置项 | 项目层 | configs | 配置文件/环境变量调用点（源码 env::var/config 模式检索） | 否 |
| 错误处理 | 事实层 | error_type | 错误类型（Result/自定义错误类型检索） | 否 |
| 错误处理 | 事实层 | propagation | 传播方式（?/match Err 模式检索） | 否 |
| 错误处理 | 事实层 | recovery | 恢复策略归纳 | 是 |
| 项目用途/领域 | 项目层 | name | crate 名称与元数据（cargo metadata description/readme 字段） | 否 |
| 项目用途/领域 | 项目层 | domain | 领域描述归纳（description 字段直出 + 归纳） | 是 |
| 项目用途/领域 | 项目层 | doc | README 入口位置（cargo metadata readme 字段） | 否 |

## 差距段（无法映射为工具信息需求的字段）

- 使用契约.preconditions：前置条件归纳（doc panics/Errors 段 + 上下文）
- 使用契约.guarantees：返回保证归纳（签名 + doc）
- 元素实现语义.summary：行为摘要/算法意图归纳
- 元素实现语义.data_flow：变量级数据流归纳
- 数据流.source：数据产生点归纳（变量级数据流分析）
- 数据流.sink：数据消费点归纳（变量级数据流分析）
- 构建与运行形态.deployment：部署形态归纳（CLI/库/服务）
- 模块职责.responsibility：职责描述归纳
- 模块职责.capabilities：暴露能力归纳（pub 项清单 + 归纳）
- 模块间依赖.type：依赖类型判定归纳（调用/数据/配置）
- 生命周期/状态.transitions：状态迁移语义归纳
- 类型定义.description：类型语义描述归纳
- 行为约定.invariant：不变量归纳
- 行为约定.side_effect：副作用归纳
- 行为约定.timing：并发/时序约束归纳
- 调用关系.condition：调用条件线索归纳（分支上下文）
- 错误处理.recovery：恢复策略归纳
- 项目用途/领域.domain：领域描述归纳（description 字段直出 + 归纳）
