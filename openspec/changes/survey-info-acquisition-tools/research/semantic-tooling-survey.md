# 项目信息生产工具调研报告（Linux 平台 · 纯 Rust 项目）

- **基准日期**：2026-10-22
- **输入边界（封闭）**：语义事实集清单 `../../survey-semantic-fact-requirements/research/semantic-fact-requirements.md` 的 20 项事实类型（项目层 6 / 模块层 3 / 符号层 4 / 事实层 A 组 6 / B 组 1）。2026-10-22 用户决策偏离原定"构造器信息需求清单"输入，见该变更 tasks.md 偏离记录。
- **调研对象**：Linux 宿主环境下，可生产上述事实所需项目信息的**纯 Rust 项目**生产者——宿主工具、项目分析类 Skill/智能体、外部工具生态。
- **判定等级**：可完成 / 部分可完成 / 不可完成。生产策略阶梯：工具直出 → 项目分析 Skill → 智能体兜底。
- **证据规则**：宿主工具为**一手实测**（2026-10-22 于本机对 Rust 夹具执行）；外部工具每事实 ≤2 个来源并标注出处；语义归纳类判定不做工具验证（无确定算法），按性质归智能体。

## 1. 信息需求派生

信息需求 = 语义事实集清单各事实类型的字段要求，逐层列出（事实类型 → 需生产的信息）：

| 层 | 事实类型 | 需生产的信息 |
|---|---|---|
| 项目层 | 项目用途/领域 | Cargo.toml description/readme、README 入口；领域描述归纳 |
| 项目层 | 模块划分 | workspace 成员/顶层 mod 清单；职责一句话归纳 |
| 项目层 | 入口 | bin target 清单、src/main.rs 位置、启动命令 |
| 项目层 | 构建与运行形态 | 构建/测试/运行命令、crate_type（lib/bin）、部署形态归纳 |
| 项目层 | 配置项 | 配置文件/环境变量清单、用途、缺省值 |
| 项目层 | 外部依赖 | 依赖清单（normal/dev/build）、用途归类 |
| 模块层 | 模块职责 | 模块路径、职责描述、暴露能力 |
| 模块层 | 模块间依赖 | 依赖方向、依赖类型（调用/数据/配置） |
| 模块层 | 对外接口 | 模块 pub 入口清单（指向符号层） |
| 符号层 | 公共接口 | 签名、可见性、所属模块 |
| 符号层 | 类型定义 | struct/enum/trait 及字段/variant |
| 符号层 | 符号关系 | trait 实现（impl T for U）、supertrait、符号-模块归属 |
| 符号层 | 意图声明 | doc 注释（`///`/`//!`）原文，与符号绑定 |
| 事实层 A | 调用关系 | caller→callee、调用条件线索 |
| 事实层 A | 数据流 | 关键数据产生→传递→消费路径 |
| 事实层 A | 生命周期/状态 | 资源创建/释放（RAII/Drop）、状态迁移 |
| 事实层 A | 错误处理 | 错误类型、传播方式（`?`/match）、恢复策略 |
| 事实层 A | 行为约定 | 不变量、副作用、并发/时序约束 |
| 事实层 A | 使用契约 | 前置条件、参数约束、返回保证 |
| 事实层 B | 元素实现语义 | 行为摘要、控制流结构（分支/循环）、变量级数据流 |

## 2. 宿主工具生产能力（一手实测）

实测环境：Linux，本机 AtomCode 宿主工具集，对 Rust 夹具（struct/impl/trait/generic-free 惯用代码，含错误传播与分支）逐一执行。**本机 Rust 工具链（rustc/cargo/rust-analyzer 等）安装盘点命令未获批准执行，其本机可用性未实测**，涉及时按"生态存在、本机待验"记入差距。

| 工具 | 实测结果 | 对 Rust 的能力结论 |
|---|---|---|
| `list_symbols` | 夹具 10 个符号全部抽出，带行号范围与 kind（struct_item/impl_item/function_item/trait_item） | 符号清单可用；impl 条目与 trait/方法区分清楚；不直接给可见性与签名文本 |
| `ast_grep`（lang=rust） | 模式 `$OBJ.$METHOD($$$ARGS)` 命中全部 9 处方法/函数调用，含 trait 方法动态分发调用点 | 方法调用点定位可用；可编写 `impl $T for $U`、`trait $T: $S`、`?`、`match $E { ... }` 等结构模式 |
| `find_references` | `flush` 命中定义处 + 2 处调用（含 match 分支内），文件级 | 同名引用过滤可用，跨文件为文本级匹配，语义精度低于 LSP |
| `trace_callers` / `trace_callees` | `emit` 反向链 run→main、`run` 正向链 emit→write，均带行号与深度 | 调用链抽取可用（单文件内验证通过）；深度默认 3、上限 5 |
| `grep` | （结构性能力，通用）正则/字面量检索，gitignore 感知 | doc 注释、配置项、环境变量等文本类信息的兜底检索 |

**宿主工具共性限制**：输出为符号/引用/调用链的结构化清单，不含语义归纳；跨 crate 类型解析、可见性判定、宏展开后的真实调用面等语义级信息超出其能力。

## 3. 外部工具生态（Linux，二手来源 ≤2/事实）

| 工具 | 能力要点（Rust 相关） | 来源 |
|---|---|---|
| rust-analyzer（LSP） | documentSymbol/workspaceSymbol（符号+位置）；call hierarchy（prepare/incoming/outgoing，含调用区间）；references/implementation/typeDefinition；诊断（跨文件依赖）。为符号层与调用关系的语义级最优来源 | rust-analyzer capabilities.rs 源码（rust-lang.github.io/rust-analyzer/src/rust_analyzer/lsp/capabilities.rs.html）；handlers/request.rs（github.com/rust-lang/rust-analyzer） |
| universal-ctags（Rust 解析器） | kinds：module/struct/trait/impl/fn/enum/type/static/macro/field/variant/method/const，带行号与 signature 扩展字段、scope 父子 | parsers/rust.c（github.com/universal-ctags/ctags） |
| cargo metadata | 机读 JSON：workspace 成员、targets（bin/lib/test/bench/custom-build）、crate_types、依赖（name/req/kind(normal/dev/build)/optional/features）、edition、rust_version | The Cargo Book: cargo-metadata、External Tools（doc.rust-lang.org/cargo） |
| rustdoc JSON | crate 公开 API 面：逐条目签名、doc 字符串、source span； nightly `-Z unstable-options --output-format json` | The Cargo Book: cargo-rustdoc；rustdocs-mcp 对 docs.rs rustdoc JSON 的消费描述（github.com/JLFN/rustdocs-mcp） |
| crates.io Registry Web API | 依赖包元数据（版本、许可、描述），用于外部依赖用途归类佐证 | The Cargo Book: Registry Web API（doc.rust-lang.org/cargo） |
| tree-sitter-rust | 增量解析 AST（错误容忍），支撑自定义控制流/数据流模式抽取；生态内被 rust-analyzer 之外的多数扫描器采用 | tree-sitter 官方 grammar 仓库（github.com/tree-sitter/tree-sitter-rust） |

### 3.1 工具画像（规模分级 × 支持语言，2026-10-22 依提案画像要求补记）

分级定义见本变更 proposal：小型＝单一职责、轻量、输出结构简单；大型＝重基建平台、输出庞杂、需多解析器分流；介于两者为中型。

| 工具 | 规模 | 支持的编程语言 |
|---|---|---|
| list_symbols / trace_callers / trace_callees / blast_radius / file_dependencies（宿主） | 小型（单一职责，符号/调用图单类输出） | 多语言：Rust、Python、JS/TS、Go、Java、C/C++、C#、PHP 等（宿主 LSP 符号能力所及范围；Rust 一手实测） |
| ast_grep（宿主） | 小型（单模式 AST 匹配） | 多语言：Rust、Python、JS/TS/TSX、Go、Java、C/C++、C#、HTML、PHP 等（Rust 一手实测） |
| find_references（宿主） | 小型（符号文本级引用查找） | 语言无关（文本级，语义精度随语言符号规则） |
| grep（宿主） | 小型（正则检索） | 语言无关 |
| ctags | 小型（单命令生成 tags 文本） | 多语言：50+（C/C++、Java、Python、Rust、Go、JS 等，`--list-languages` 可枚举；Rust kinds 见 parsers/rust.c） |
| cargo metadata | 小型（单命令 JSON 输出） | Rust 专属（Cargo 生态） |
| crates.io Registry Web API | 小型（HTTP 元数据查询） | 语言无关（包元数据，非代码解析） |
| tree-sitter | 中型（解析库 + grammar 生态，需宿主集成与模式开发） | 多语言：40+ 官方/社区 grammar（Rust、Python、JS/TS、Go、Java、C 系、Ruby 等） |
| rustdoc JSON | 中型（nightly 编译器附属输出，API 面完整但获取链路重） | Rust 专属 |
| rust-analyzer | 大型（重基建 IDE 平台：增量索引、诊断、补全等全量服务，输出面庞杂） | Rust 专属 |

画像与选型策略的对应：多语言小型工具（ctags、ast_grep、宿主符号/调用图工具）可跨语言复用同一解析器，优先；Rust 专属工具中仅 rust-analyzer 为大型——按"多语言工具不可判定或语义不足才引入"准则，仅在宏展开后语义（G5）等场景按需引入。

## 4. 覆盖矩阵（信息需求 × 生产者）

判定记法：**可完成**（判定可完成且有明确生产者）/ **部分可完成**（仅覆盖部分字段或需多源合并）/ **不可完成**（当前无生产者）。生产者记法：H-*＝宿主工具，X-*＝外部工具，A-*＝智能体/Skill 归纳。每格一行证据；来源见第 2/3 节编号。

| 信息需求 | 判定 | 生产者（阶梯） | 证据（一行） |
|---|---|---|---|
| 项目用途/领域 | 部分可完成 | X-cargo metadata（description/readme 字段）＋ H-grep ＋ A-归纳 | metadata 有 description/homepage/repository 字段；"领域描述"为自由文本，工具直出字段后仍需归纳 |
| 模块划分 | 部分可完成 | X-cargo metadata（workspace_members）＋ H-list_symbols（mod 结构）＋ A-归纳 | 成员与 mod 清单可直出；"职责一句话"无工具可产出 |
| 入口 | 可完成 | X-cargo metadata（targets kind=bin + src_path） | metadata targets 数组逐 target 给出 kind 与 src_path，启动点直接可查 |
| 构建与运行形态 | 部分可完成 | X-cargo metadata（crate_types/edition）＋ X-rustdoc JSON ＋ A-归纳（部署形态） | crate_type/edition/命令可直出；"容器化服务/库/CLI"的部署归类需归纳 |
| 配置项 | 部分可完成 | H-grep（`env::var`/config 模式）＋ H-ast_grep ＋ A-归纳（用途/缺省） | 调用点可检索定位，但 Rust 无声明式配置 schema，清单化与缺省值推导属归纳 |
| 外部依赖 | 可完成 | X-cargo metadata（dependencies：name/req/kind/optional/features）＋ X-crates.io API（用途佐证） | metadata JSON 逐依赖含 kind（normal/dev/build），结构完整 |
| 模块职责 | 不可完成（工具直出）→ 智能体兜底 | A-项目分析 Skill/子代理 | 职责为语义归纳，无确定算法；工具仅供 H-list_symbols 出模块清单作边界 |
| 模块间依赖 | 部分可完成 | X-cargo metadata（crate 级依赖方向）＋ H-grep/ast_grep（crate 内 `mod`/`use`）＋ A-归纳（依赖类型） | 依赖方向可直出；"调用/数据/配置"类型判定需读代码归纳 |
| 对外接口 | 可完成 | H-list_symbols ＋ H-ast_grep（`pub fn`/`pub struct` 模式）＋ X-rustdoc JSON（公开 API 面） | 符号清单带位置；rustdoc JSON 直接给出 pub API 逐条目 |
| 公共接口（签名/可见性） | 可完成 | X-ctags（signature 扩展字段）＋ H-list_symbols ＋ X-rustdoc JSON | ctags Rust kind=f/P 带 signature；rustdoc JSON 含完整签名 |
| 类型定义 | 可完成 | H-list_symbols（struct/enum/trait）＋ X-ctags（field/variant/const kinds） | 实测 10 符号含 struct/trait 及行号；ctags 字段/variant 逐条带行号 |
| 符号关系 | 可完成 | H-ast_grep（`impl $T for $U`、`trait $T: $S` 模式）＋ X-rust-analyzer（implementation/参考 provider） | trait 实现/supertrait 结构可模式匹配；LSP 语义级确认实现关系 |
| 意图声明 | 可完成 | H-grep（`///`/`//!`）＋ X-rustdoc JSON（doc 字段与 source span） | doc 注释为文本抽取，原文保留即可，无需归纳；rustdoc JSON doc 字段直接机读 |
| 调用关系 | 可完成 | H-trace_callers/callees（一手实测）＋ X-rust-analyzer call hierarchy | 双向链实测通过；LSP incoming/outgoing 含调用区间（宏展开后语义更准） |
| 调用条件线索 | 部分可完成 | H-ast_grep（match/if 包裹模式）＋ A-归纳 | 分支结构可定位，条件语义需读上下文归纳 |
| 数据流 | 不可完成（工具直出）→ 智能体兜底 | A-项目分析 Skill（H-trace/ast_grep 供证据） | "产生→传递→消费"路径无现成工具；变量级数据流需程序分析基建（如数据流分析框架），当前生态未接入 |
| 生命周期/状态 | 部分可完成 | H-ast_grep（Drop impl/`new`/析构模式）＋ X-rust-analyzer ＋ A-归纳（迁移语义） | RAII 资源创建/释放点可模式定位；状态机迁移语义需归纳 |
| 错误处理 | 部分可完成 | H-ast_grep（`Result`/`?`/`match Err` 模式）＋ A-归纳（恢复策略） | 错误类型与传播点可结构抽取；恢复策略语义需归纳 |
| 行为约定 | 不可完成（工具直出）→ 智能体兜底 | A-项目分析 Skill/代理 | 不变量/副作用/时序为深层语义，无确定算法；doc 中显式声明部分可由 H-grep 辅助 |
| 使用契约 | 部分可完成 | X-rustdoc JSON/ctags（签名类型约束）＋ H-grep（doc 中 panics/Errors 段）＋ A-归纳 | 签名约束（参数/返回类型）工具直出；前置条件散布于 doc 与实现，需归纳 |
| 元素实现语义 | 部分可完成 | H-ast_grep/tree-sitter 模式（控制流结构）＋ A-归纳（算法意图/行为摘要） | 分支/循环结构可 AST 级直出；意图与摘要为归纳，无确定算法 |

矩阵小结：**可完成 8 / 部分可完成 10 / 不可完成（纯归纳兜底）2**；20 项信息需求全部有至少一个生产者路径（含智能体兜底），无"零生产者"格子。

## 5. 差距清单与处理判定

| # | 差距 | 弱覆盖内容 | 处理判定 |
|---|---|---|---|
| G1 | 数据流无工具直出 | 变量级"产生→传递→消费"路径 | **弱绑定标注**：由智能体兜底归纳，证据用 H-trace/ast_grep 输出回链；缓加入程序分析基建（如数据流框架），不在本轮解析器范围 |
| G2 | 行为约定无工具直出 | 不变量、副作用、并发/时序约束 | **弱绑定标注**：智能体兜底；doc 中显式声明部分由 H-grep 辅助定位 |
| G3 | 模块职责/领域描述为纯归纳 | 职责一句话、领域描述 | **弱绑定标注**：智能体兜底，工具直出的清单字段（description/mod 清单）作结构锚点 |
| G4 | 配置项无结构化 schema | 配置清单、用途、缺省值 | **弱绑定标注**：调用点检索 + 归纳；Rust 生态无声明式配置源，建议解析器按 `env::var`/config 模式实现部分直出 |
| G5 | 宏展开后语义失真 | 宏内调用/实现关系（宿主工具按源码文本/未展开 AST 匹配） | **弱绑定标注**：涉宏事实标注"宏前语义"；语义级确认缓接 rust-analyzer（LSP 具备展开后视角） |
| G6 | 本机 Rust 工具链可用性未实测 | rustc/cargo/rust-analyzer/ctags 本机安装与版本 | **缓加入**：本机盘点命令未获批准执行；解析器实现前须实测登记（影响"解析器已实现"的矩阵点亮） |
| G7 | 使用契约前置条件散布 | panics/Errors 段落之外的前置条件 | **弱绑定标注**：签名约束直出 + doc 段落抽取 + 归纳兜底 |

差距共性：全部弱覆盖项集中在**语义归纳类信息**（对应构造器阶梯的智能体兜底层），工具直出层（结构/签名/依赖/调用链/文档）无不可满足的信息需求——该结论支持"解析器实现聚焦结构抽取，归纳走智能体"的生产策略。

## 6. 调研边界自查

本报告不含事实需求定义（归语义事实集清单）、不含契约/schema 结构决策（归 epic 设计阶段 fact-catalog → contract-format → output-schema）；信息需求由清单事实类型逐项派生，未新增、未扩张事实范围。

## 5. First-phase Python + Rust catalogue alignment (2026-10-26)

The active first-phase scope is now the fixed development-time catalogue at `skills/layered-semantic-facts/assets/information-needs.json`, derived from `add-semantic-fact-constructor/design.md`. It currently covers four F2/L3 fields: identity, names, boundary and locators. The earlier Rust-only survey above is retained as historical research context; it is not the complete first-phase language scope.

### 5.1 Python candidates

| Candidate | Current use/coverage | Limitations / gate |
|---|---|---|
| Python standard-library `ast` | Parses supplied Python text; emits module, class, function/async-function and import observations with line ranges | Does not execute source or prove runtime behavior; parser component tests must pass for the exact profile |
| `python -m compileall` | Candidate syntax/bytecode compilation signal for later validation | Not used by the current F2 inventory path; can create `__pycache__`; not semantic evidence |
| `pyproject.toml`, `setup.cfg`, requirements files | Candidate manifest/config evidence for later F1/F3/F5 needs | Not part of the current fixed F2-only catalogue |

### 5.2 Rust candidates

| Candidate | Current use/coverage | Limitations / gate |
|---|---|---|
| Built-in deterministic Rust declaration parser | Parses supplied text; emits module/function/struct/enum/trait/impl/type/const/static/use declarations and delimiter diagnostics | Not rustc/rust-analyzer; no type checking, macro expansion, borrow checking or runtime behavior |
| `cargo metadata --no-deps --format-version 1` | Candidate workspace/target/dependency inventory for a future catalogue extension | Not invoked by current F2 scanner; requires Cargo and an explicit execution policy |
| `cargo check` / `rustc` | Candidate compile/type-check evidence | Toolchain availability not verified in this CI run; project code must never be executed implicitly as a side effect of a syntax query |
| `rust-analyzer` | Candidate semantic symbols, references and call hierarchy | Installation/version and project readiness are environment-specific and unverified; no matrix entry enabled from ecosystem presence alone |
| `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml` | Candidate manifest/toolchain evidence for later F1/F3/F5 needs | Not part of the current fixed F2-only catalogue |

### 5.3 Current acceptance evidence and matrix state

- Parser registry and declaration tests: `tests/test_info_parser.py`.
- Mixed-language scanner tests: `tests/test_source_scanner.py`.
- Real-source integration: `tests/test_acceptance.py` exercises Python and Rust source → parser → FactBatch → SQLite → reopen → query.
- CI: https://github.com/vchs6/code2semantics/actions/runs/40261330788 (component suites and strict OpenSpec pass; product delivery gate remains intentionally blocked because full constructor orchestration is incomplete).
- No external tool such as cargo/rustc/rust-analyzer is claimed as installed or accepted. The capability matrix remains empty; this survey does not enable entries.
- Future needs outside F2 identity/names/boundary/locators must enter via a development-time OpenSpec change, tool research, parser acceptance and a separate matrix enablement action. Runtime code must not extend the catalogue or matrix.

## 7. Expanded S1–S12 needs coverage and producer shortlist (2026-10-26)

This section supersedes the earlier statement that the survey input is only the four F2 syntax needs. The authoritative input is now `skills/layered-semantic-facts/assets/information-needs.json`: 127 field-level needs across F1–F18, mapped to scenarios S1–S12. These are requirements, not 127 separate tools. Candidate selection is grouped by native output and complementary coverage.

### 7.1 Candidate coverage matrix

| Need group | Information needs / fact fields | Primary candidate families | Complementary sources | Gaps / acceptance status |
|---|---|---|---|---|
| Scope and project identity | F1 all fields; F2.roles; F3 entry/runtime/environment fields | Project/workspace manifest readers; Python/Rust source parsers | Configuration and documentation readers; caller-declared scope | Custom deterministic readers/parsers still need implementation and tests. Nested paths do not establish ownership. |
| Workspace and organization | F4 all fields; F5 responsibility/implementation links | Cargo workspace metadata; Python project/workspace manifests | Source references and documentation; constrained induction for responsibility | Manifest membership does not establish dependency or responsibility. Candidate only. |
| Dependencies and interactions | F6 all fields; F7 all fields; F8 all fields | Package manifests; import/reference/call analyzers; API/schema readers | Compiler semantic indexes and opt-in runtime traces | Static edges are candidates unless resolution/conditions are proven. External endpoints remain references only. |
| Declarations, types, bindings and dispatch | F9 all fields; F10 all fields; F11 all fields | Existing AST parsers; ctags; ast-grep structural matches | Compiler/type-checker output; rust-analyzer LSP | Existing AST profiles only cover syntax inventory. Tag/pattern hits do not prove semantic binding. |
| Data/control flow, state and errors | F12–F15 all fields | AST/control-flow analyzers; compiler IR/diagnostic output | Runtime traces when explicitly authorized; source/doc evidence | No accepted general data-flow or state-transition producer yet. Do not infer runtime behavior from syntax alone. |
| Algorithm and evidence reasoning | F16 all fields; F17 all fields; F18 all fields | Accepted source/control-flow evidence; coverage/provenance validator | Constrained cognitive inference with premises and counterevidence | No automatic proof of intent, invariants, termination or complexity. Unsupported claims remain open items/gaps. |

### 7.2 Small candidate shortlist (not a one-tool-per-field plan)

| Candidate profile | Intended coverage | Native output to parse | Current decision |
|---|---|---|---|
| Python `compileall` | Additional Python syntax/compile diagnostics | Compiler/compileall diagnostics | Candidate; safe fixture probe in CI, disabled pending parser acceptance |
| Python `pyproject.toml` via stdlib `tomllib` | Declared project metadata, build backend, scripts and dependency declarations | TOML manifest records | Candidate; no dedicated parser/acceptance yet, disabled |
| `cargo metadata --no-deps --format-version 1` | Rust workspace members, targets and declared dependencies | Cargo metadata JSON | Candidate; availability and output probe in CI, disabled pending parser acceptance |
| `cargo check` | Rust type/compiler diagnostics for explicitly opted-in projects | Compiler diagnostics | Candidate; disabled pending environment, sandbox and parser acceptance |
| `rust-analyzer` | Rust semantic symbols, references, implementations and call hierarchy | LSP responses/diagnostics | Candidate; server lifecycle/project readiness and adapter acceptance pending |
| universal-ctags JSON | Cross-language declarations, tags, some signatures/scopes | JSON-lines tag records | Candidate; version/output probe pending |
| ast-grep JSON | Cross-language structural matches for declarations/call/control-flow candidates | JSON stream | Candidate; version/rule/output probe pending |

Existing `python.ast-source` and `rust.syntax-source` remain the only enabled profiles. The six candidate profiles are represented in the capability matrix as disabled entries solely to make the research/coverage hand-off explicit; disabled entries are not executable production capabilities and carry no parser-development acceptance.

### 7.3 Environment probe evidence

CI now runs `scripts/research/probe_candidate_tools.py` on the Ubuntu runner. The script records platform, executable paths, version output and safe sample output where the candidate is installed. It uses temporary fixtures only, never executes project source, and never enables matrix entries. The run linked from this report must be inspected before marking tool availability or native output as observed. A missing binary means unavailable in that CI environment only; it does not prove unavailable on every supported developer platform.

### 7.4 Selection rules

1. Prefer existing accepted producers when their output meets the need and completeness criterion.
2. Add no new external tool merely to cover a field name; add it only when a specific need lacks adequate evidence.
3. Combine producers where manifests, source references, compiler output and documentation supply complementary evidence.
4. Preserve separate evidence and knowledge status for direct observations, interpretations and inferences.
5. Keep every candidate disabled until the parser accepts the exact tool/version/output/invocation profile with positive, negative and missing-tool tests.
6. After parser acceptance, test constructor selection and multi-producer composition. Only then may the matrix entry be enabled.

### 7.5 Observed CI probe results (Ubuntu 24.04, Python 3.12.15)

Probe run: https://github.com/vchs6/code2semantics/actions/runs/40319334019

The probe used temporary fixtures only and did not execute project source.

| Candidate | Observed result | Evidence / decision |
|---|---|---|
| Python | Python 3.12.15 present | `python --version` exit 0 |
| `python -m compileall` | Sample Python fixture compiled successfully, exit 0 | Output is a syntax/bytecode diagnostic only; profile remains disabled until parser and no-generated-artifact acceptance is added |
| Cargo | Cargo 1.99.0 present | `cargo --version` exit 0 |
| `cargo metadata --no-deps --format-version 1` | Temporary minimal Cargo project returned valid JSON, exit 0; output contained package, target, workspace member and manifest paths | Strong candidate for workspace/target/dependency-manifest needs; profile remains disabled pending parser tests and policy acceptance |
| rustc | rustc 1.99.0 present | `rustc --version` exit 0; no compile/type-check sample was run in this probe |
| rust-analyzer | A shim/path exists, but `rust-analyzer --version` failed with “Unknown binary … in official toolchain” (exit 1) | Not usable in this CI environment; do not treat as installed |
| universal-ctags | No executable found | Not installed in this CI environment; no output fixture observed |
| ast-grep | No executable found | Not installed in this CI environment; no output fixture observed |
| tree-sitter CLI | No executable found | Not installed in this CI environment; no output fixture observed |

The first probe run exposed invalid newline escaping in the temporary fixtures; that run is retained as RED evidence and is not used as a positive tool result. The corrected probe run above is the accepted evidence. These results are specific to this GitHub-hosted Ubuntu runner and do not claim availability on developer workstations or other platforms.

### 7.6 Matrix hand-off

The capability matrix now contains the two previously accepted syntax profiles plus six disabled candidate profiles. No candidate was enabled by research. The matrix unit test was updated to assert the distinction between enabled/accepted profiles and disabled/research-only candidates. CI: https://github.com/vchs6/code2semantics/actions/runs/40319334019 — component tests and strict OpenSpec passed; overall CI remains blocked only by the expected product delivery gate.

## 8. 独立项目分析类 Skill 调研（2026-10-27）

### 8.1 调研边界

本节只研究具有独立项目分析任务与可调用入口的 Skill。通用 AI 代理、模型、代理宿主/运行平台不属于候选对象；当工具与所选项目分析 Skill 都无法满足剩余需求时，AI 兜底使用该 Skill 的既定宿主，宿主只作为运行前提记录。

Python/Rust 是当前解析器与生产链的第一阶段实现范围，不是 Skill 候选的语言准入限制，也不是最终产品语言边界。最终目标是分析语言无关的项目模型，尤其是混合语言项目中的边界、依赖、接口、交互和证据关系。分别通过单语言样例不等于混合语言验收通过。

### 8.2 候选发现与文档证据

本轮通过公开 Skill 仓库定位候选，并直接检查其 `SKILL.md`。以下结论仅为文档审查结果，不代表已在目标宿主安装、授权或执行；可执行性、真实输出和混合语言能力仍待实测。

| 候选 Skill | 文档可确认的分析范围 | 与本项目需求的潜在对应 | 主要缺口/风险 | 初步结论 |
|---|---|---|---|---|
| [codebase-analysis](https://github.com/JakubMikolajek/codex-skills-collection/blob/main/skills/codebase-analysis/SKILL.md) | 按步骤检查仓库结构、依赖、脚本、架构、后端/前端、基础设施、第三方集成、测试、安全、重复代码与死代码 | F1/F2/F3/F4/F5/F6；可作为项目级初始盘点与模块/依赖分析候选 | 文档没有规定统一机器可读 FactBatch、逐字段源码定位、当前来源指纹或混合语言交互验收；文档未证明实际执行覆盖 | **优先试验候选**：项目级覆盖面较广，仍需核实证据精度与跨语言能力 |
| [codebase-summary](https://github.com/smyrick/skills/blob/main/skills/codebase-summary/SKILL.md) | 基于仓库证据解释架构；检查边界、语言、manifest/build systems、入口、接口、主要执行路径、测试与部署；支持小/中/大分析深度 | F1/F2/F3/F4/F5/F6/F7/F8/F18；对架构摘要、入口与代表性请求路径较相关 | 默认产出面向人的说明；需验证每项断言能否保留机器可消费的源码证据，是否能处理多语言构建生态与跨语言调用；真实运行未验证 | **优先试验候选**：证据导向的分析流程与需求相关，尚未证明可直接转换成语义事实 |
| [explaining-codebases](https://github.com/analyticalmonk/explain-this/blob/main/skills/explaining-codebases/SKILL.md) | 对真实仓库进行架构概览、数据流/执行路径说明和单机制深挖；要求按路径与行号校验声明 | F5/F7/F8/F11/F12/F15/F16/F18；对执行路径解释与引用校验可能有补充价值 | 明确依赖 `creating-explainers` 的产物流程，不能视为完全独立的单 Skill；主要目标是生成解释器产物，不是机器事实采集；未验证混合语言分析 | **条件候选**：只有在依赖 Skill 的可用性与其独立分析增量明确后再试验 |
| [improve-codebase-architecture](https://github.com/jae-labs/skills/blob/main/skills/improve-codebase-architecture/SKILL.md) | 识别架构摩擦、模块耦合、测试性和 AI 可导航性问题，并给出架构改进候选 | F5/F18 的职责/架构关系可能有帮助 | 主要优化目标是重构建议，不是完整语义库存；依赖项目词汇/ADR和探索子代理流程；不应把重构建议当作已观察的软件事实 | **低优先级/特定需求候选**：仅在职责/架构解释需求明确且能提供源码证据时纳入 |

### 8.3 需求覆盖初评（仅文档映射，未验证）

| 信息需求类别 | 独立 Skill 可能补充的能力 | 必须实测的判定条件 |
|---|---|---|
| 项目边界、入口、构建生态（F1/F2/F3/F4） | 识别仓库/子项目、入口、manifest、构建与运行单元 | 混合语言仓库中是否识别多个构建系统、嵌套/重叠项目与独立 Library，且不按目录推断身份 |
| 模块职责与架构映射（F5/F18） | 根据模块实现、公开接口和调用关系归纳职责 | 每个职责结论是否引用具体源码；是否区分观察事实与解释；共享实现是否保留多对多关系 |
| 依赖、调用、接口与数据交互（F6/F7/F8/F10/F11/F12） | 汇总静态引用、接口与代表性执行路径 | 是否区分声明依赖、调用点、实际执行；能否追踪跨语言接口与调用，并保留未解析目标 |
| 状态、错误与内部算法（F13/F14/F15/F16） | 对控制路径、异常、资源生命周期和算法步骤进行解释 | 是否有具体源码位置与反例；是否将推断的意图、终止性或复杂度错误标成已证实 |
| 证据、知识状态和限定否定（F17） | 在解释中引用来源和标注不确定性 | 能否保留源文件/行区间/内容状态、支持与反证、检查覆盖；缺失证据不能被写成不存在 |

本表是候选能力映射，不是覆盖通过声明。任何需求只有在实际运行输出通过逐项核验后，才可标记为已验证覆盖。Skill 的自然语言总结若缺少可追溯证据，不能直接作为受支持语义事实持久化。

### 8.4 混合语言实测设计

候选的核心试验使用同一临时授权根下的混合语言项目，而非分别运行两份独立单语言样例。建议夹具包含：

1. 一个语言 A 的应用入口与声明依赖；
2. 一个语言 B 的库/模块，通过 FFI、生成绑定、RPC/HTTP、共享 schema 或明确接口与语言 A 交互；
3. 两种语言各自的构建/依赖清单，以及一处嵌套或独立子项目；
4. 至少一条有源码依据的跨语言调用/数据契约，和一条只有声明依赖、并未证明实际调用的关系；
5. 一个无法从现有材料确定的行为，检验 Skill 是否保留 unknown，而非补写假事实。

验收记录需保存候选版本/提交、安装和调用前提、精确输入根与排除项、执行命令/宿主入口、原始输出、源码位置、失败情况和逐字段评审结果。至少验证：两种语言均被识别；项目身份与工作空间/目录包含分离；跨语言实体映射可追踪；声明依赖不冒充运行时调用；事实各自绑定到正确语言的源码证据；未知与范围外内容不被编造。若没有可安全运行的宿主或候选无法执行，记录为“未验证/阻塞”，不推断为通过。

### 8.5 本轮结论与后续工作

- 已完成候选发现与公开 `SKILL.md` 文档初审；候选均尚未在本项目的获准环境中实际执行。
- 当前优先实测 `codebase-analysis` 与 `codebase-summary`；`explaining-codebases` 因依赖 `creating-explainers` 暂列条件候选；`improve-codebase-architecture` 仅适用于特定架构职责需求。
- 当前没有证据证明上述任一候选能完整覆盖 S1–S12，或已验证混合语言项目分析。不能将文档描述计入生产覆盖率。
- 下一步按任务 4.4/4.5 执行安全可复现的混合语言夹具试验，并更新本表。研究完成本身不安装/授权 Skill，不修改能力矩阵，也不表示运行时构造器已经能调用 Skill。

### 8.6 新增候选：Understand Anything 的独立项目分析 Skill

候选：[Egonex-AI/Understand-Anything — `understand` Skill](https://github.com/Egonex-AI/Understand-Anything/tree/main/understand-anything-plugin/skills/understand)。本轮直接读取其 `SKILL.md`，不是只依据市场摘要。

文档中明确的输入输出与流程：以项目根路径为输入；运行项目自带的扫描/合并脚本，按阶段进行文件分析、架构层识别、知识图谱生成/审查与验证；输出 `.ua/knowledge-graph.json`，包含节点和边类型，并支持排除规则、全量/增量更新及可选图审查。图节点覆盖代码文件、函数/类/模块、配置、文档、服务、数据库表、端点、流水线、schema 与基础设施资源；边包括 contains/imports/implements/calls、数据读写与转换、depends_on、tested_by、配置/部署等。该输出形式比纯自然语言总结更接近可映射为语义实体和关系的中间表示。

语言能力的文档证据比此前候选更具体：SKILL 声明的确定性结构适配器覆盖 JavaScript/JSX、TypeScript/TSX、Ruby、Python、Go、Rust 和 C++；对其它语法即使能够解析，也会保守处理。文档还明确写出 Rust trait impl 身份可能保持 unknown、无确定性结构解析器的语言不能仅凭 LLM/正则猜测确认符号删除。由此可见它有跨语言项目分析的潜在价值，但**这仍是候选文档证据，不是本项目已实测的混合语言能力**。

| 评估项 | 当前文档审查结论 | 待验证事项 |
|---|---|---|
| 独立 Skill 属性 | 有明确 `understand` 入口、项目路径参数、独立分析流程及结构化图产物 | 需要在获准宿主实际安装/调用，确认依赖和运行边界 |
| 语言范围 | 文档列出 JS/TS、Ruby、Python、Go、Rust、C++ 的确定性结构适配器 | 需要检查实际版本的 parser adapter、fixture 与构建流程；不得把所有图边都视为各语言均有同等精度 |
| 混合语言价值 | 统一知识图谱可容纳多种代码/配置/基础设施节点和关系 | 尚无本项目的同一混合语言夹具执行结果；跨语言调用/FFI/RPC 是否被正确关联尚未证明 |
| 证据可追溯性 | 设计包含节点来源范围、结构指纹、符号身份校验、验证阶段与 unknown 保留 | 需核实最终每条语义边是否携带可回链的精确源码位置、证据和当前内容状态，能否转换为本项目 Evidence/FactBatch 契约 |
| 安全与副作用 | 文档要求把 README/manifest 视为不可信项目数据；分析会写入 `.ua/` 产物并可能运行 Node/Python 脚本及内部子代理 | 必须在临时副本/隔离目录执行，核实依赖安装、脚本执行、联网/外发、权限和输出写入行为 |
| 事实可靠性 | 对部分删除判断采用确定性 parser + declaration-coverage adapter，并对不支持情况保留 unknown | 需验证其 LLM 图边的推断标签、证据强度和冲突处理是否足以支撑本项目语义事实契约 |

初步排序调整：`understand` 提升为**优先实测候选**；`codebase-analysis` 与 `codebase-summary` 保留为轻量对照候选。它的图输出、语言适配范围和 unknown 保留策略更接近本项目需求，但不能因图节点/边数量丰富就判定语义正确或完整。当前仍未安装、未运行、未验收，能力矩阵不因此启用任何条目。

### 8.7 独立 Skill 的真实试验门槛

在获准宿主可用后，优先对 `understand` 运行一个临时混合语言夹具：至少包含两种语言的可执行/库边界、显式跨语言接口（如 FFI 或 RPC/schema）、独立子项目及一条只有声明依赖但没有调用证据的边。保留原始 `knowledge-graph.json` 和中间扫描输出，并对每条候选关系检查节点身份、来源位置、当前内容状态、关系种类与置信/unknown 语义。对照构造器的 F1–F18 需求逐项判定；不符合 FactBatch 契约的图输出只能作为候选证据，不能直接入库。

本轮执行环境只具备仓库读取/写入与 CI 核验入口，未获得安装并运行该 Skill 的已授权宿主会话，因此不能伪称完成动态试验。下一步应在批准的宿主上执行上述可复现试验；若当前会话无法调用该宿主，4.4/4.5 保持 pending，继续完成文档审查与契约设计，但不将阻塞隐藏为通过。

### 8.8 Token-efficient structured-output candidates (2026-10-27)

User priority: prefer project-analysis Skills that execute tools/scripts and return structured, queryable data, minimizing model token use. This changes the experiment order; it does not waive semantic accuracy, evidence, security or mixed-language acceptance.

| Priority | Candidate | Directly inspected behavior/documentation | Token-cost interpretation | Main caveat to test |
|---|---|---|---|---|
| 1 | [CodeGraph Explorer](https://github.com/GoldDHacker/codegraph-explorer-skill) | Skill says a local Python script builds `.codegraph/graph.json`; subsequent questions use bounded commands such as `--callers`, `--find-path`, `--impact`, `--file-deps`, `--subgraph` and `--wiring`. It explicitly instructs the model not to parse source with LLM tokens. | Strongest first candidate for low-token, tool-driven code analysis. The zero-token claim is documented, not yet measured in our host. | Language support is uneven: inspected text documents tree-sitter for JS/TS/Java and selected extended grammars, while several languages including Rust/Go/C++/Ruby/PHP/Swift/Kotlin remain regex-based in the noted version. Need mixed-language precision tests and per-language edge-quality review. |
| 2 | [Understand Anything](https://github.com/Egonex-AI/Understand-Anything/tree/main/understand-anything-plugin/skills/understand) | Multi-phase local project scan creates `.ua/knowledge-graph.json`, with typed nodes/edges, incremental support, deterministic validation and optional LLM graph review. | Structured reusable output is promising, but the LLM review option and multi-phase analysis may incur token cost; separate and measure each phase. | Need establish actual token accounting, mixed-language edge correctness, evidence locators/content state, and conversion from graph records to FactBatch. |
| 3 | [Graphify](https://github.com/Graphify-Labs/graphify) and [Graphify Skill](https://github.com/darce07/graphify-claude-skill) | Local tree-sitter AST extraction produces `graph.json`; queries include graph query/path/explain. Documentation says code-only extraction can skip semantic LLM extraction, while docs/media may invoke an LLM pass. | Potentially very low token cost for code-only projects if semantic passes are disabled/skipped; token usage varies by corpus and invocation mode. | Verify actual invocation's code-only fast path, supported grammars, relation precision and whether query/explain invokes a model. Measure actual run rather than relying on the stated 0 LLM credits. |
| 4 | [codebase-summary](https://github.com/smyrick/skills/tree/main/skills/codebase-summary) and [codebase-analysis](https://github.com/JakubMikolajek/codex-skills-collection/tree/main/skills/codebase-analysis) | Repository exploration/checklist and evidence-led architecture prose. | Useful baselines, but likely more model-context use when repeated questions require re-reading prose/source. Must measure rather than assume. | No equally explicit local graph-query contract in the inspected Skill document; verify if structured outputs and evidence are stable enough for reuse. |

#### Token measurement protocol

Public documents make claims about zero-token extraction, but this session has not run any candidate Skill in an approved host and cannot claim measured savings. For each candidate, collect the following during the same mixed-language fixture:

1. **One-time build cost:** model input/output tokens used by Skill instructions, orchestration, optional LLM semantic extraction and graph review; report local deterministic CPU work separately from model tokens.
2. **Per-query cost:** input/output tokens for a representative relation query (e.g. cross-language interface, callers, dependency path) and any graph records/source snippets loaded.
3. **Amortized cost:** total build + N queries, reported for N=1, 10 and 50, compared with a baseline that reads the relevant source files directly.
4. **Quality:** correct nodes/edges, false positives, missed edges, source-locator accuracy, current source-state binding, unknown handling and authorization boundary. Token savings count only when the quality bar is met.
5. **Fallback overhead:** whether the agent must reopen source files or invoke an LLM because the graph is incomplete; include this in token totals rather than hiding it.

Never load an entire graph JSON into model context if the Skill provides bounded query commands. Prefer query output size and relevant subgraph size. A structured graph is a reusable intermediate artifact, not automatically a trustworthy semantic fact batch.

#### Current status

- Candidate documents were inspected directly; this is source-document evidence only.
- CodeGraph Explorer is the first candidate to test due to script-first graph construction, scoped query commands and an explicit zero-token code-analysis design. Understand Anything and Graphify are next because they also produce structured graphs and document multi-language support.
- No candidate was installed or executed in this session. No token savings are yet measured. Mixed-language runtime testing, security review and FactBatch evidence mapping remain pending; no capability-matrix entries were enabled.

### 8.9 Tool-overlap gate: Skill must prove incremental value (2026-10-27)

The earlier candidate ordering by structured output and low token use is now subordinate to a more important first gate: compare the Skill with direct use of the same underlying tools. Tool-driven implementation alone is not sufficient reason to add the Skill as a second runtime producer.

| Candidate | Documented overlap pattern | Increment to prove before integration | Current decision |
|---|---|---|---|
| CodeGraph Explorer | Local script creates `.codegraph/graph.json`; query commands expose callers, paths, impact, file dependencies and subgraphs. Likely overlaps with direct symbol/reference/call-graph tools where those are available. | Does it resolve useful cross-file/cross-language edges, identify project wiring, or provide better scoped evidence than invoking available tools directly? Compare false edges, missing edges, source reads and total tokens. | Keep as first experiment candidate only; no integration decision until direct-tool baseline is measured. |
| Understand Anything | Local scan and multi-phase graph construction with typed nodes/edges and optional graph review. Overlaps with project scanning, symbol extraction, dependency analysis and graph assembly. | Determine whether its additional nodes/edges and review catch real gaps beyond the direct tools; measure token cost of review separately. | Second experiment candidate; no assumed increment. |
| Graphify | Local AST/tree-sitter graph construction and query/path commands; optional LLM semantic pass for non-code material. | Separate deterministic code graph from semantic/document pass; compare graph relation precision and project-level edges against direct tools. | Third experiment candidate; no assumed increment. |
| Prose-oriented analysis Skills | Explore files and produce architecture summaries or explanations. | Show verified facts or cross-component relations unavailable from direct tools, with source-level evidence; presentation alone is not increment. | Lower priority unless a specific need is uncovered. |

#### Required experiment shape

Run the same authorized mixed-language fixture in two modes:

1. **Direct mode:** invoke available accepted tools for the fixed need subset and retain each native output.
2. **Skill mode:** invoke the candidate on the same source snapshot, retain the Skill's raw graph/report and enumerate every underlying tool/script and model-driven step.

Normalize both outputs to comparable candidate nodes/edges/claims without pretending either is already a FactBatch. Measure (a) newly covered needs with valid evidence, (b) precision and missed relations against fixture ground truth, (c) source locator accuracy, (d) unknown/scope behavior, (e) model tokens and wall-clock time including build and queries, and (f) additional source reads required to validate claims. Deduplicate facts that simply repeat underlying tool outputs.

Acceptance decision:
- If Skill and direct mode provide equivalent validated information and evidence, prefer direct tool reuse and retain the Skill only as documentation/workflow inspiration.
- If Skill shows a measurable quality/coverage benefit or equivalent-quality total-cost reduction, consider it for runtime integration after security and adapter validation.
- If the only benefit is nicer presentation, do not count it as semantic coverage.
- If the Skill result is richer but its new edges cannot be verified or it turns unknown into guessed facts, reject that increment.

Token efficiency is therefore a secondary optimization after measurable increment/quality equivalence, not the first and only selection criterion.
### 8.10 CodeGraph Explorer installation readiness and security notes

Direct README inspection confirms a manual archive installation path for Claude Code at `~/.claude/skills/codegraph` (README's `🚀 Installation` section); the Skill expects `SKILL.md`, `scripts/codegraph_builder.py` and language extraction references to be colocated. Its core builder uses Python standard library only; `watchdog`, tree-sitter grammars, `ladybug`, and `python-igraph`/`leidenalg` are optional dependencies for additional features. Optional tree-sitter packages should be pinned together to the documented compatible `tree-sitter>=0.25,<0.26` line. The exact archive URL/version and supported installation mechanism must be pinned before production use; a mutable `main`/branch download is not a reproducible install identity.

Automatic-install candidate procedure (not yet executed):

1. Use a development-time approved registry entry with canonical repository, pinned commit/tag and verified archive/source digest; never derive the install URL or command from project files or query input.
2. Prefer an isolated managed install directory. For a Claude Code-compatible host, the documented target is `~/.claude/skills/codegraph`; other hosts require their own supported Skill directory/installation adapter. Do not overwrite an existing installation with a different revision without explicit upgrade policy.
3. Before install, inspect and validate the archive/file list and license; install the minimum required files and only install optional parser grammars that are required by the accepted language coverage. No need to install optional `watchdog`, `ladybug`, or clustering packages unless the selected profile requires them.
4. Run a static compile/health check (`python -m py_compile` for the builder, then `python codegraph_builder.py --doctor` after installation where supported), followed by a tiny disposable mixed-language fixture. Capture dependency versions, stdout/stderr, generated graph, source locators and any writes.
5. The Skill documentation describes a `SessionStart` hook option and auto-update configuration. These must remain disabled unless explicitly approved; installing the Skill must not silently enable hooks, watchers, auto-update, external graph databases or project-write behavior.
6. The builder writes `.codegraph/` artifacts into the target project, so run evaluation on a temporary copy or explicit writable output root. Verify exclusion rules, no source modification, no unexpected network access and no data egress. Read-only behavior cannot be assumed solely from the Skill's description.

Installability assessment: **documented manual installation exists; automatic installation has not been performed or verified in this session**. This session has no authorized target Skill-host filesystem/installation API. Therefore the candidate remains not installed/not accepted. If runtime auto-install is unavailable, the constructor must return exact host-specific instructions and continue independent work as defined in the proposal.

### 8.11 Decision: CodeGraph Explorer is a structural evidence producer, not a complete language-neutral semantic fact producer

Current evidence does **not** support claiming that CodeGraph Explorer directly produces the complete language-neutral semantic facts required by F1–F18/S1–S12. It emits a structured graph with heuristic/AST-derived nodes and edges; this is a candidate intermediate evidence source that must be mapped to the authoritative fact catalogue and validated.

| Fact/need family | Potential direct contribution | Not established / must not infer |
|---|---|---|
| Project/file identity and containment (F1/F2/F4) | File nodes, paths, containment and discovered project structure | Full logical project identity, nested/overlapping project ownership, workspace semantics or authorized scope completeness without additional checks |
| Imports/dependencies and declared wiring (F6) | Import/file-dependency/wiring relations where implemented | A declared import or dependency is not proof of runtime interaction, required dependency, or complete dependency resolution |
| Calls/inheritance/implements (F9/F10/F11) | Candidate call/inheritance edges from AST or regex and local resolution | Language-independent semantic binding, dynamic dispatch, cross-language calls, macro/generated-code behavior or exact resolution for every supported language |
| Data flow/effects/state/lifecycle/errors (F12/F13/F14) | Some syntactic call/reference clues may help targeted follow-up | Complete variable-level def-use, aliasing, state transitions, resource lifetimes, exception propagation/recovery or side-effect semantics |
| Control flow and algorithm explanation (F15/F16) | Structural candidates from declarations and call graph | Guard semantics, invariants, termination, complexity, algorithm correctness or proof of behavior |
| Evidence/knowledge/completeness (F17/F18) | Graph records may carry source/file/symbol metadata and confidence labels | Conformance to this project's evidence schema, current source content-state binding, coverage proof, counterevidence, independent evidence and bounded-negative claims without an explicit adapter and validation |

Language-neutral here means the **public semantic fact contract and identity/relation model** are language-independent, not that every language parser has equal precision or that a generic graph edge has the same semantics in every language. CodeGraph Explorer documents uneven extraction paths (tree-sitter for selected languages and regex fallback/heuristics for others); therefore language-specific blind spots must remain explicit.

Decision: retain CodeGraph Explorer as a **low-token structural graph candidate**. Do not use its graph as a ready-to-persist FactBatch, and do not count graph nodes/edges as accepted semantic coverage without per-need mapping, source/content-state validation, relation-specific checks, and mixed-language tests. Prefer it only where direct comparison proves incremental value over existing accepted tools. Remaining semantic needs should go to other accepted producers/Skills and then evidence-constrained AI induction; unresolved needs remain gaps.

### 8.12 Cost risk: do not require a full graph build before every request

CodeGraph Explorer's graph-first workflow can amortize cost across repeated queries, but an unconditional full-project build can be wasteful for a one-off or narrow information need. The production policy must therefore be demand-driven and must not require a complete graph as a precondition for every query.

Proposed evaluation cases:

- **Narrow/one-shot need:** compare direct accepted tool calls with building the entire graph. If direct tools satisfy the need, do not build the graph or install the Skill.
- **Broad/repeated need:** measure one-time full graph construction, incremental update cost, graph size, per-query cost and quality over 1/10/50 queries. Reuse the graph only while its source fingerprint and scope match.
- **Partial graph path:** test whether the candidate can build only the relevant files/subgraph or whether its query commands require a full repository graph. Record limitations instead of assuming incremental or partial construction exists.
- **Changed source:** verify whether incremental mode detects content changes reliably, updates affected nodes/edges, and invalidates stale evidence. Do not use mtime-only or stale graph state as proof of current content unless the implementation validates it.
- **Mixed-language project:** measure graph construction and relation precision per language and across language boundaries. A fast incomplete graph is not a successful producer.

Runtime selection implication: first estimate the remaining need set and compare it with accepted direct-tool coverage. Invoke a graph Skill only when its expected incremental coverage/quality or amortized total cost justifies the build. A graph build may be reused for subsequent compatible requests, but its reuse key must include authorized scope, source content state, candidate version and extraction profile. If the full build is too expensive for the current request, continue with direct tools and leave uncovered needs for later stages rather than forcing a full scan.

Cost acceptance must report first-build latency, incremental-update latency, query latency, graph bytes/nodes/edges, model tokens used by build/review/query, source fallback reads, and quality on the same fixture. This is currently a required measurement, not an observed benchmark; no timing claim is made in this report.

### 8.13 First isolated CodeGraph benchmark result (2026-10-27)

CI run: https://github.com/vchs6/code2semantics/actions/runs/40442745658. The candidate was fetched at pinned commit `6a95e4f0ae643fad7354ac388ceaa2dc2c2f3f74`; the harness generated a temporary synthetic mixed-language project and executed only the local builder/query CLI, without installing optional packages or calling any model API.

| Metric | Observed result | Interpretation |
|---|---:|---|
| Fixture size | 106 files | Python app/modules, Rust library/modules, pyproject/Cargo manifests and a shared proto schema |
| Full graph build | 0.133 s wall-clock | Fast on this small synthetic fixture; not a production-repository benchmark |
| Graph artifact | 147,258 bytes | 260 nodes and 158 edges; node types file/function/import/symbol/entrypoint; edge types calls/contains |
| Targeted `--callers handle_request --json` query | 0.0934 s; 119 output bytes | Scoped output is small; result showed a caller edge from `main` to `handle_request` |
| Incremental update after modifying one Python file | 0.112 s wall-clock; builder reported 1 file reparsed, 104 served from cache, 0 removed | Incremental extraction works on this fixture; process startup dominates measured wall time |
| Local builder/query model-token use | 0 model/API tokens by construction | The harness directly invoked Python; this is not the Skill-host prompt/orchestration token count |
| Cross-language Python→Rust link | Not proven | Graph includes both language source paths, but does not demonstrate a semantic link across the shared schema |

Result: the concern that a small graph build necessarily takes a long time is not supported by this smoke test; 106 fixture files built in about 0.13 seconds on the GitHub-hosted runner. This cannot be extrapolated linearly to large real repositories or equal semantic completeness. The result only shows that local structural graph construction and scoped queries can be inexpensive on a modest fixture.

Workflow note: the first smoke run had a path-escaping issue only in artifact upload; the benchmark itself passed. The workflow path was corrected and the subsequent run uploaded the result successfully.

Still pending: test a representative larger repository; run N=1/10/50 repeated queries; compare against direct accepted tools at equivalent quality; validate real cross-language relations, false positives/negatives, current-source evidence and security/write behavior. No candidate is enabled or accepted for production by this benchmark.

### 8.14 Scaled benchmark: 106 and 1,006 files, repeated queries

Successful run: https://github.com/vchs6/code2semantics/actions/runs/40443027810. Candidate revision remains pinned to `6a95e4f0ae643fad7354ac388ceaa2dc2c2f3f74`. Both fixtures are generated in temporary directories; the benchmark invokes the local Python builder and query CLI directly.

| Metric | 106-file fixture | 1,006-file fixture |
|---|---:|---:|
| Full graph build wall time | 0.1166 s | 0.3782 s |
| Graph size | 147,258 bytes | 1,412,941 bytes |
| Nodes / edges | 260 / 158 | 2,510 / 1,508 |
| Repeated `--callers handle_request --json` queries | 10 | 50 |
| Total query wall time | 0.7911 s | 4.3413 s |
| Mean query wall time | 0.0791 s | 0.0868 s |
| Incremental update after changing one Python file | 0.096 s | 0.2556 s |

Interpretation: for these synthetic fixtures, full graph construction scales acceptably from roughly 100 to roughly 1,000 source/config files, and the query command returns small scoped output. Query timing includes a fresh Python process and graph load per invocation, so it is not just in-memory graph traversal time. The build/update/query measurements are wall-clock times from one hosted CI run, not repeated-run distributions or production SLA evidence.

Token accounting: graph build and query invoked the local script directly and made no model/API calls, so candidate code-analysis model-token use is zero by construction. Skill-host instruction tokens and downstream reasoning tokens were not measured. Repeated queries also do not yet compare total cost with direct tools at equivalent semantic quality.

Cross-language semantics remain unproven: both Python and Rust files appear in the graph, but the fixture does not establish a Python→Rust call through the proto contract. These results support further evaluation of graph build cost only; they do not justify treating the graph as language-neutral semantic facts or enabling the Skill in production.

### 8.15 Extended scale: 10,006-file synthetic mixed-language fixture

Successful CI run: https://github.com/vchs6/code2semantics/actions/runs/40443086780. This run executes the same pinned candidate and harness at three fixture sizes, with repeated query loops and a one-file incremental update.

| Metric | 106 files | 1,006 files | 10,006 files |
|---|---:|---:|---:|
| Full graph build | 0.1512 s | 0.5017 s | 3.9842 s |
| Graph size | 147,258 B | 1,412,941 B | 14,237,979 B (~14.2 MB) |
| Nodes / edges | 260 / 158 | 2,510 / 1,508 | 25,010 / 15,008 |
| Query repetitions | 10 | 50 | 10 |
| Query total / mean | 1.0284 s / 0.1028 s | 5.7135 s / 0.1143 s | 2.2401 s / 0.2240 s |
| Incremental update after one Python file edit | 0.1287 s | 0.3330 s | 2.4100 s |

Interpretation: a 10,006-file synthetic project built in about 4 seconds on the hosted runner, yielding a ~14.2 MB graph. This makes full local graph construction plausible for a broad project scan, but not free: at this scale each query process took about 0.22 seconds on average, and a one-file update still took about 2.4 seconds because global graph resolution/metrics are recomputed. The current `--update` path re-parses one changed file but does not mean total update cost is proportional only to that file.

All timing values are single-run wall-clock observations, not statistical benchmarks. CI runner, filesystem cache, Python startup and graph resolution affect the numbers. No real production repository or direct-tool equivalent-quality baseline was measured.

Model token accounting remains 0 for the local builder/query subprocesses because the harness invokes no model/API. This excludes Skill-host instruction/orchestration and later semantic induction. Graph completeness remains structural only: the test does not prove Python-to-Rust semantic linking through the shared proto schema. Therefore this result supports further cost evaluation but does not establish language-neutral semantic-fact coverage or production acceptance.

### 8.16 Relation-quality smoke test against fixture ground truth

Successful run: https://github.com/vchs6/code2semantics/actions/runs/40443319461. The harness now asserts two relation-level behaviors in addition to inventory and performance:

- **Expected call edge present:** Python `handle_request` calls `call_worker`; `--callers call_worker --json` returned a `calls` edge whose source node is `handle_request`.
- **Import-only decoy does not create a call edge:** the fixture imports `module_000` but does not call its `transform_000` function; `--callers transform_000 --json` returned an empty JSON list. This checks one false-positive boundary, not overall precision.
- All three fixture sizes passed these assertions: 106, 1,006 and 10,006 files. The graph contains Python and Rust paths, but the expected call edge is within Python; the harness explicitly keeps `python_to_rust_semantic_link_proven=false`.

Latest observed metrics from this run (single CI sample):

| Fixture files | Full build | Graph | Nodes / edges | Query loop | Mean query | One-file update |
|---:|---:|---:|---:|---:|---:|---:|
| 106 | 0.1017 s | 147,258 B | 262 / 160 | 10 queries / 0.7129 s | 0.0713 s | 0.1287 s |
| 1,006 | 0.3189 s | 1,412,941 B | 2,512 / 1,510 | 50 queries / 3.8721 s | 0.0774 s | 0.3330 s |
| 10,006 | 2.3530 s | 14,237,979 B | 25,012 / 15,010 | 10 queries / 1.4489 s | 0.1449 s | 2.4100 s |

Observed output confirms a cheap local structural graph on this fixture, but the benchmark is still not a comparison against the project's accepted direct tools. It does not validate cross-language FFI/RPC resolution, semantic behavior fields, or complete false-positive/false-negative rates. The import-only check covers one deliberately absent call edge; it must not be generalized into a precision score.

CI harness status: `Evaluate CodeGraph Skill` succeeded at pinned revision `6a95e4f0ae643fad7354ac388ceaa2dc2c2f3f74`. The benchmark runs the builder/query CLI directly, so local graph operations consume no model/API tokens; Skill-host overhead remains unmeasured.

### 8.17 Incremental cache correctness: edit and deletion checks

Successful CI run: https://github.com/vchs6/code2semantics/actions/runs/40443411991. The harness now checks a known positive call edge (`handle_request` calls `call_worker`) and a known negative edge (the import-only `module_000` must not create a call to `transform_000`), then edits one file and deletes another before running incremental updates.

- All three scales (106, 1,006, 10,006 files) passed both relation assertions.
- After editing one Python file, the builder reported one re-parsed file and the rest served from cache; return code was successful.
- After deleting `python_app/module_001.py`, the builder reported one removed file and the deleted path was absent from the resulting graph at all three scales.
- On the 10,006-file fixture, full build was 2.5012 s; the edit update was 2.4100 s in this run; the deletion update was about 1.49 s. The update cost includes full reference resolution and graph metrics, not just per-file parsing.

These are useful cache lifecycle and local relation checks, but the false-positive check is limited to one deliberately absent call and the positive call is intra-language Python. Cross-language Python→Rust relation resolution, actual RPC/FFI behavior, broad precision/recall, source-line evidence validity and direct-tool baseline remain untested. Candidate output is still not accepted as a semantic FactBatch.

### 8.18 Real open-source Rust and Python repository evaluation (2026-10-27)

Successful CI: https://github.com/vchs6/code2semantics/actions/runs/40443798396. This is a **real project** evaluation, not generated Python/Rust fixture data. The workflow fetched and checked out immutable revisions of [cmpute/dashu](https://github.com/cmpute/dashu) (`a0fc5358a3335e9fce155c5ddf8ae7ca83f24a33`) and [pallets/click](https://github.com/pallets/click) (`2247b35ea1c47c727d7a06e51fa280e12a863ff6`) alongside pinned CodeGraph Explorer (`6a95e4f0ae643fad7354ac388ceaa2dc2c2f3f74`). The graph was generated with its local script in isolated CI checkouts; application project code, Cargo builds and Python project test suites were not executed.

| Metric | Rust Dashu | Python Click |
|---|---:|---:|
| Repository files (excluding .git) | 564, including 393 Rust and 20 Python | 178, including 91 Python |
| Full graph build wall time | **3.4667 s** | **1.5793 s** |
| Graph artifact size | 43,946,741 bytes | 21,004,684 bytes |
| Graph nodes | 7,771 | 2,924 |
| Graph edges | 155,397 (148,147 calls; 7,250 contains) | 73,733 (70,868 calls; 2,783 contains; 82 inherits) |
| Edge tag INFERRED | **145,714** (~93.8%) | **70,147** (~95.1%) |
| Edge tag RESOLVED / EXTRACTED | 2,457 / 7,226 | 721 / 2,865 |
| Callers queries | 10, all successful, structured JSON | 10, all successful, structured JSON |
| Mean callers-query wall time | 0.3832 s | 0.2195 s |
| One-file edit then incremental update | 3.0438 s | 1.2194 s |
| Dangling graph edges | 0 | 0 |

**Important quality observation:** the real repositories produce very dense candidate call graphs dominated by `INFERRED` edges, unlike the sparse synthetic fixture. This does not prove the inferred edges are false, but it is a major evidence/precision risk: graph edge counts must not be credited as verified call-fact coverage. The next direct-tool comparison must sample inferred edges and verify the source/target and language-specific resolution. Large graph output should be consumed through bounded queries rather than whole-file model context.

**Important freshness observation:** Dashu's edit attempt in the first real run reported `0 file(s) (re)parsed` despite the benchmark appending a comment before `--update`, while Click reported `1 file(s) (re)parsed`. The Dashu test did not yet prove whether the comment change was recognized because the edit was made in a very short time window and the candidate caches per-file modification times. This must be investigated with an explicit same-mtime semantic-content mutation test; source content digest must be authoritative for current semantic-fact validity.

The local builder/query subprocesses made no model calls, but this is not a measurement of the eventual Skill-host orchestration token cost. Only the two isolated project builds and sampled query/incremental command execution succeeded; F1–F18 language-neutral semantic fact coverage, cross-language calls, conditional behavior, negative knowledge and FactBatch acceptance remain pending.

The benchmark source and CI runner are in `scripts/research/evaluate_codegraph_real_projects.py` and `.github/workflows/evaluate-codegraph-real-projects.yml`; the CI artifact `codegraph-real-project-results` contains JSON result files. No capability-matrix entries were enabled.
