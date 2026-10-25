<!--
# 📜 语义事实提取Skill最高技术宪法

本文件是整个项目的单一事实来源（Source of Truth）与最高控制基线。所有 AI Agent（如规划、编码、测试智能体）以及人类开发团队，在发起提案、设计架构、生成代码、或进行运行时静态校验时，**必须 100% 严格遵守本宪法中的通用语言、技术栈边界与架构硬红线。**

---

## 📂 1. 项目全局物理拓扑规范 (Repository Directory Map)

系统采用严格的 **Monorepo（单体仓库）** 与 **Hexagonal Architecture（六边形/端口与适配器架构）** 进行物理隔离，确保领域层逻辑与底层基础设施/外部工具链的绝对解耦。

```text
my-project/
├── openspec/                          # OpenSpec 规范驱动开发控制中心
│   ├── project.md                    # 本文件：最高技术宪法与技术基线
│   ├── AGENTS.md                     # AI Agent 行为准则与工程执行纪律
│   └── specs/                        # 全局长寿主规格库 (Global Specs)
│       └── facts_extraction/         # 语义事实提取限界上下文
│           ├── schema.json           # 核心中立事实的强 JSON Schema
│           └── spec.md               # 聚合根行为不变量与断言
├── skills/                            # 智能体编排层 (Orchestration Layer)
│   └── facts_pipeline.json           # Dify / LangGraph 工作流配置文件
├── src/                               # 物理系统源码目录 (Core Implementation)
│   ├── domain/                       # 纯洁领域层 (Domain Core)
│   │   └── facts/                    # 事实提取域聚合根、实体、值对象及统一异常
│   ├── port/                         # 端口层 (Inbound Ports 接口定义)
│   └── infrastructure/               # 基础设施层 (Adapters & External Tools)
│       └── parsers/                  # 外部语言 AST 软解析物理适配器脚本
└── tests/                             # 自动化验收与领域集成测试桩 (Test Fixtures)
```

---

## 📖 2. 语义事实提取限界上下文通用语言 (Ubiquitous Language)

本上下文（`PureFactsExtractionContext`）专注于**源系统意图的客观还原**，拒绝任何面向目标的逻辑外溢。

### 2.1 全局核心名词与术语基线
*   **Source Language（源语言）**：待分析的原始项目所属的编程语言（如 `JAVA`、`CPP`）。
*   **Semantic Fact（语义事实）**：彻底脱离具体源语言语法结构、纯粹描述系统底层业务、类型与控制流拓扑的中立、机器可读的事实集合。

### 2.2 核心战术领域模型定义 (Tactical Domain Models)

#### 🛡️ 聚合根：`SemanticFactRepository` (语义事实仓库)
*   **物理职责**：整个限界上下文的控制核心，负责接收外部源语言适配器输入的原始快照，并**强制将其淬取并断言为符合中立 Schema 规范的语义事实集**。
*   **核心物理属性**：
    *   `repositoryId`: `UUID` (全局唯一标识)
    *   `sourceLanguage`: `SourceLanguageEnum`
    *   `extractionStatus`: `Enum (PENDING | EXTRACTED | FAILED)`
*   **核心领域方法 (Commands)**：
    *   `initialize(sourceLanguage)`: 初始化事实仓库快照状态。
    *   `ingestSourceAst(SourceAstSnapshot)`: 接收外部适配器软解析出的中立 AST 快照。
    *   `extractNeutralFacts()`: 驱动领域服务与 AI 节点，将快照彻底脱敏、解耦，转化为不带语法特征的中立事实。
    *   `validateSchemaCompliance()`: 强制触发物理数据格式与核心实体存在性断言，不符则抛出 `InvalidSemanticFactException`。

#### 📦 核心值对象 (Value Objects - 不可变性)
*   **`SourceAstSnapshot` (源语言 AST 摘要快照)**：
    由外部特定语言适配器吐出的、包含项目基本调用拓扑与隐式运行时特征的标准化元数据快照。

#### 👤 核心实体 (Domain Entities - 生命周期标识)
*   **`TypeBoundaryFact` (类型系统边界事实 - `FACT-TYPE-[UUID]`)**：
    客观描述原系统的类型特征，包含：`nullabilityModel`（空安全性特征）、`genericsPhilosophy`（泛型行为特征）、`memoryLayout`（引用或值类型布局特征）。
*   **`ControlFlowFact` (控制流与异常哲学事实 - `FACT-FLOW-[UUID]`)**：
    客观描述原系统的运行特征，包含：`concurrencyModel`（并发与线程模型事实）、`errorPropagation`（错误与异常流转事实）、`closureCaptureModel`（闭包与变量捕获事实）。

---

## 🚨 3. 领域核心防御红线：统一异常控制 (Domain Exceptions)

1.  **`InvalidSemanticFactException` (非法语义事实异常)**：
    *   *触发边界*：AI 提取节点输出的数据未能成功脱敏，或者生成的数据结构破坏了中立 `schema.json` 的硬性约束。
2.  **`InvalidAstSnapshotException` (非法 AST 快照异常)**：
    *   *触发边界*：上游解析适配器传入的数据结构损坏，或缺失核心调用依赖拓扑。

---

## ⚙️ 4. 全局工程技术栈与核心编码规则 (Global Coding Guidelines)

1.  **纯粹中立原则**：淬取产出的中立事实（`schema.json`）中，**严禁包含任何特定目标语言（如无 Rust 的 lifetime 概念、无 Go 的 channel 概念）的物理痕迹**。它只对源系统做客观的意图还原。
2.  **领域纯洁性原则**：`src/domain/` 目录下的所有核心文件，严禁引入任何第三方编排或大模型框架依赖，必须保持绝对的纯 Python 原生强类型逻辑。
3.  **不可变代码生成原则**：任何根据主规格 `schema.json` 自动生成的强类型桩代码，其目录权限在 CI 中为只读，严禁在业务开发中手动修改。
-->