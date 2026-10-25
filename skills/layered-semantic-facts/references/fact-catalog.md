# 可提供事实目录（fact catalog）

本目录是消费方可查询语义事实的**封闭边界**：查询契约所引用的事实 MUST 属于本目录，目录外引用判为"超出范围"（见 `contract-format.md` 与 spec `semantic-fact-query`「可提供事实目录前置确定」）。

- **层级**：采用语义事实集需求清单（`survey-semantic-fact-requirements/research/semantic-fact-requirements.md`）的分析结论——项目 → 模块 → 符号 → 事实（2026-10-22 全面重研再收敛确认）。
- **语言无关性**：语义词汇为语言无关描述，执行者将各语言的结构映射到这些词汇。
- **证据定位格式**：统一为 `文件:行号范围`。

## 项目层

| 事实类型 | 可查询字段 |
|---|---|
| 项目用途/领域 | `name`（名称）、`domain`（领域描述）、`doc`（文档入口） |
| 模块划分 | `modules`（顶层模块清单：路径 + 职责一句话） |
| 入口 | `entries`（可执行入口、启动命令、main/初始化位置） |
| 构建与运行形态 | `build`（构建系统与产物）、`run`（运行/测试/验证命令）、`deployment`（部署形态：容器化服务/库/CLI 等语言无关描述） |
| 配置项 | `configs`（配置文件/环境变量：用途、缺省值） |
| 外部依赖 | `dependencies`（运行时/构建依赖：名称、用途归类） |

## 模块层

| 事实类型 | 可查询字段 |
|---|---|
| 模块职责 | `path`（模块路径）、`responsibility`（职责描述）、`capabilities`（对外暴露能力） |
| 模块间依赖 | `direction`（依赖方向）、`type`（调用/数据/配置） |
| 对外接口 | `public_entries`（模块对外公共入口清单，指向符号层） |

## 符号层

| 事实类型 | 可查询字段 |
|---|---|
| 公共接口 | `signature`（函数/方法签名）、`visibility`（可见性）、`module`（所属模块） |
| 类型定义 | `kind`（结构体/类/接口/枚举）、`description`（语义描述）、`fields`（字段） |
| 符号关系 | `relation`（继承/实现/组合）、`target`（目标符号）、`module`（符号-模块归属） |
| 意图声明 | `intent`（文档注释承载的意图/用法说明，与符号绑定） |

## 事实层（关系与行为，含元素内部语义）

| 事实类型 | 可查询字段 |
|---|---|
| 调用关系 | `caller` → `callee`、`condition`（调用条件线索） |
| 数据流 | `source` → `sink`（关键数据的产生→传递→消费路径） |
| 生命周期/状态 | `resource`（资源）、`transitions`（创建/释放、状态迁移） |
| 错误处理 | `error_type`（错误类型）、`propagation`（传播方式）、`recovery`（恢复策略） |
| 行为约定 | `invariant`（不变量）、`side_effect`（副作用）、`timing`（并发/时序约束） |
| 使用契约 | `preconditions`（调用前置条件）、`parameter_constraints`（参数约束）、`guarantees`（返回保证） |
| 元素实现语义 | `summary`（行为摘要/算法意图）、`control_flow`（分支/循环结构）、`data_flow`（变量级数据流）——仅语言无关部分，排除语句写法、临时变量命名等语言相关细节 |

## 待回填项

本目录暂不声明各类事实的**生产方式**（工具直出 / 编排 / 智能体归纳）与弱覆盖事实的处理（弱绑定标注或缓加入）——此类结论需要生产能力调研支撑，见 epic design「Open Questions」，待相关调研完成后回填本目录。
