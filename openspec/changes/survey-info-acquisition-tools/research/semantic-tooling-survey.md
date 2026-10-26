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
