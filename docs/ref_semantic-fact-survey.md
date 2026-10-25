# 上游项目语义事实获取调研报告

版本：1.0.0\
调研日期：2026-10-19\
关联任务：UPA00\
基线提交：cfbc0c7f8419a7e69d7224cc0909d572744bbcd0\
适用范围：首期纯 Rust 第三方库向仓颉迁移；Rust 1.85.1、仓颉 SDK 1.0.5。本文不更换工具链基线，不宣称产品实现或迁移验证完成。

## 1. 调研结论及选型原则

**通用选型原则（适用于所有语言）**：通用工具优先、小工具组合获取优先，适用于所有源语言及混合语言项目。通用工具包括已有编译器、构建系统、包管理器、标准格式处理器和成熟通用分析工具，不要求一个工具支持所有语言。在满足事实字段、精度和覆盖要求的前提下，优先复用现有能力并组合小工具；组合已能满足需求时不引入大型工具，也不重复自研已有能力。确有缺口才评估大型或专用工具，并记录缺口、增量收益及运行和维护成本。各语言仅绑定具体工具、解析器和配置；Rust是首期验证实例，不能据此宣称其他语言已验证。

以下工具清单和实测结果是该原则在Rust首期范围内的应用，不限定上游分析Skill的语言适用范围。

首期应以 **Cargo + rustc + 文件/清单解析 + 按需语法解析 + 小型观察驱动** 组成事实获取链。优先复用迁移本就需要的编译器能力：工程信息、有效配置、编译诊断、实际输入依赖、MIR和真实测试输出。不要因为需要语义事实就默认部署大型代码分析平台。

选型顺序为：先复用有效事实；再在免费工具中依次考虑现有工具链、成熟小工具及其组合；只有明确列出这些组合仍不能满足的字段、精度或覆盖要求后，才考虑大型工具。随后才是辅助 Skill 和 AI 兜底。大小不能只按二进制体积判断，应比较安装服务、运行资源、输出体积、解析维护成本、版本耦合和额外 Token。自研一个依赖 rustc 内部 API 的小程序，也可能比成熟工具更难维护。

本次交付包含事实目录、21项候选能力矩阵、37项一手资料、固定版本实测原始输出及复现说明。实测使用自编无外部依赖的双库工作空间；它是调研夹具，不是已选 GitHub 迁移样本，也不是完整端到端验证。外部辅助 Skill 仅核查固定提交源码，没有运行模型或测得 Token 节省率。

最重要的选型修正：

1. Cargo负责工程和依赖元信息，rustc补充配置、诊断、依赖文件和局部编译后语义。不能把Cargo的JSON当成全部源语义。
2. stable Rust 1.85.1支持 `--emit=mir`；本次真实输出包含类型、基本块和宏生成函数。但MIR文本没有稳定格式承诺，采用它必须限定版本和解析子集。
3. Tree-sitter适合语法定位和声明补全；不提供真实类型解析、宏展开或完整调用图。已有rustc结果足够的事实不重复获取。
4. rust-analyzer/SCIP与rustdoc JSON是特定缺口的候选；不作为所有项目默认依赖。rustdoc JSON在本次stable基线上失败。
5. 五类出口行为需要源码、类型、局部控制关系、文档及有界执行组合，单个静态工具不保证完整获取。

## 2. 研究方法、证据等级与原报告补缺

研究以消费请求为起点，而不是从工具排行榜倒推需求。逐项核对官方接口，再检查辅助Skill的实际指令和底层代码，最后对最小工具链做隔离取样。机器矩阵位于[能力矩阵](../capability-matrix.json)，事实目录位于[事实目录](fact-catalog.json)，来源清单位于[来源](sources.json)。

证据等级独立于选型结论：

| 等级 | 含义 | 可以支持的结论 |
|---|---|---|
| docs_only | 已读一手文档 | 文档声称具备能力；尚不能编写依赖臆测格式的解析器 |
| source_inspected | 固定提交源码已检查 | 实际方法和依赖可分析；不等于环境可运行 |
| probe_passed | 固定版本及限定样本运行成功 | 对已测试输入和字段提供样例依据 |
| probe_partial | 输出可得但覆盖或解析仍有限 | 可设计限定方案；不能声称全部能力通过 |
| probe_negative | 预期能力在指定条件下失败 | 排除该条件下的使用，保留失败证据 |

此前“语法—类型—数据流—控制流—运行时—架构—领域—演化”的分层可作为导航，但需补上工程拓扑、构建条件、出口协议、配置化覆盖与来源信封。团队协作、冲刺、人员风险、估算成本不属于首期语义事实主线。质量指标与安全扫描结果也不能代替API行为契约。

本报告补足：工作空间/包/target层次，声明与解析依赖，feature/cfg/build.rs，重导出和公开可达性，五类行为及前置条件，表示和资源差异，测试预言，部分失败、冲突与缓存失效。所有工具结论均绑定来源；没有继续使用无法解析的引用编号。

## 3. 首期需要获取的事实

P0表示首期按请求覆盖；conditional表示特性存在即必需；demand表示实际消费请求触发。它们不要求启动时全仓扫描。P1由性能要求触发；P2可后续扩展。所有事实均带F23信封。

| ID | 事实组及优先级 | 必须保留的字段 | 消费与主要限制 |
|---|---|---|---|
| F01 | 源快照与来源（P0） | commit、dirty文件摘要、文件清单、清单/锁文件哈希、源根、子模块、许可证定位 | LMO03、UPA04；未提交变更不能只用commit代表快照 |
| F02 | 工作目录结构（P0） | 单库/工作空间/混合集合、workspace成员/排除/default_members、package归属、附属target | LMO03；目录名不等于包名；examples/benches不是独立迁移库 |
| F03 | 依赖图（P0） | declared/resolved边、normal/build/dev、optional、rename、path/git/registry、版本、target条件、外部边界 | LMO03、LMO04；no-deps缺解析图；不同边类型不能混成迁移排序 |
| F04 | 构建配置（P0） | rustc/Cargo版本、edition/MSRV、target/host、profile、feature启用集、cfg、env白名单、panic/overflow设置 | LMO04、UPA04、SAR01；每配置独立覆盖；不能以全features替代互斥配置 |
| F05 | 生成与扩展边界（P0-conditional） | build.rs、proc-macro、include、生成文件、链接参数、native/FFI、宏展开覆盖 | LMO04、SAR01；纯Rust也可能有build.rs；宏输入不等于展开结果 |
| F06 | 模块与出口身份（P0） | 模块树、visibility、reexport别名、公开可达路径、实体身份、cfg、源位置 | LMO04、LMO11、SAR01；pub语法不等于从crate根公开可达 |
| F07 | 类型及接口契约（P0） | 参数/返回、泛型、trait bounds、关联类型/常量、impl、枚举变体、trait方法、安全性/ABI | LMO04、SAR01；语法只保留声明；推导/解析与目标映射分开 |
| F08 | 符号关系（P0） | definition/reference/import/implementation、may_call、调用点、动态分派未解集合 | LMO04；reference不能升级为call；method/trait/dyn需分级 |
| F09 | 局部控制与数据关系（P0-demand） | 分支/循环/提前返回、读写点、传播链、状态字段和源位置 | LMO04、SAR01；不要求全仓SSA/PDG；未知路径不等于不可达 |
| F10 | 前置条件和不变量（P0） | 输入域、状态约束、合法序列、环境假设、声明/推断/观测区分 | LMO04、SAR01；观察不到非法输入不能推出前置条件 |
| F11 | 返回结果语义（P0） | 正常值、空/边界值、精度、顺序、编码、确定性、比较观察点 | LMO11、SAR01；仅在已覆盖输入和配置下观测 |
| F12 | 错误与终止语义（P0） | Result/Option/panic/abort、错误类别/载荷、触发条件、错误优先级、失败后状态 | LMO11、SAR01；崩溃与返回错误不能统一为失败布尔值 |
| F13 | 状态变化（P0） | 初始状态、写集、前后状态、失败原子性、重置/复用、共享状态 | LMO11、SAR01；内部字段只作为定位证据；比较可观察状态 |
| F14 | 副作用（P0） | 文件/流/日志/环境/回调/资源操作、顺序和次数、允许观察范围 | LMO11、SAR01；未记录副作用不等于无副作用；插桩效果需说明 |
| F15 | 调用序列协议（P0） | 构造/操作/终结合法序列、前次失败影响、迭代消费、重复调用、回调协议 | LMO11、SAR01；单调用测试无法覆盖历史依赖 |
| F16 | 表示与跨语言风险（P0） | 整数宽度/溢出、浮点NaN/-0、Unicode/字节索引、序列/映射顺序、相等/哈希、序列化 | LMO04、MKB01、SAR01；UPA记录源事实；MKB提供通用映射，LMO决定允许差异 |
| F17 | 所有权和资源生命周期（P0-conditional） | 借用/别名、可变性、所有权转移、Drop、资源释放顺序、unsafe前提 | LMO04、SAR01；语法生命周期参数不等于借用检查完整结论 |
| F18 | 并发、异步和环境（P0-conditional） | Send/Sync、锁/原子、async取消/重入、线程时序、时钟/随机/OS/路径 | LMO04、SAR01；样本没有这些特性可not_applicable；不能因此删除事实类别 |
| F19 | 测试和行为预言（P0） | 单元/集成/doctest/example/bench、断言、输入、预期、跳过原因、执行条件、结果/证据引用 | LMO04、LMO07、SAR01；编译成功不等于测试通过；测试通过不等于语义等价 |
| F20 | 性能和复杂度（P1-demand） | 输入规模、基准环境、算法复杂度依据、时间/内存/分配测量、容差 | LMO04、LMO07；仅用户要求或迁移风险触发；不凭单次耗时推导复杂度 |
| F21 | 文档与领域意图（P0-demand） | 公开承诺、术语、使用模式、限制、未决歧义、原文引用 | LMO04、SAR01；作者声明与实际行为冲突均保留 |
| F22 | 架构边界和迁移单元输入（P0-demand） | 模块依赖、强连通集合候选、共享类型/状态、公开边界、测试关联 | LMO04；不由UPA直接决定Cluster/MU或迁移调度 |
| F23 | 证据、覆盖和缺口（P0） | 事实来源级别、逐字段定位、配置/快照、解析版本、覆盖分母、未知/不适用/冲突/失败 | UPA01、UPA04、所有消费者；空数组只能在覆盖范围已知时说明零结果 |
| F24 | 演化与治理补充（P2） | 版本差异、弃用/兼容、许可证；团队/活跃度/维护风险按需 | LMO04、报告；许可证基础定位归F01首期；团队画像、冲刺和成本估计不作语义主线 |

### 3.1 五类行为必须共享比较前提

对每个出口实体，准备源侧输入域、初始状态、环境/配置、允许调用序列，以及五类观察的可用性、证据和缺口。不能只返回一个“行为摘要”字符串。建议字段按以下语义拆分：

- 返回：值/结构、空值、排序、精度和编码；记录具体输入。
- 错误：Result、Option、panic或进程终止的类别与载荷，触发条件和错误优先级。
- 状态：前后状态、可观察写集、失败后是否保留原状态。
- 副作用：文件、输出、回调、资源等观察点；次数和顺序不能丢失。
- 序列：每一步的输入、输出和状态关联；记录重复调用、失败后继续、终结后操作。

UPA只提供源侧事实及证据。编排器负责目标事实、两端API映射、比较上下文和允许差异，SAR负责在约定前提内找反例并出具报告。没有发现反例不得表述为完全等价；不将SAR改造成工作流审批者。

### 3.2 轻量拓扑投影与项目深度投影分离

顶层规划仅查询F01—F05所需的工程投影和F23；不预取完整F06—F22。多个独立工作空间需要分别运行Cargo，再以目录归属关联。排除已识别的migration过程目录、目标结果和构建输出；记录排除依据，不能仅凭同名目录删除或忽略用户源码。

UPA返回源根、工作空间/包身份和依赖边。默认目标路径、工作序列、Cluster/MU是编排器产物，不能由分析器偷偷生成。示例/基准是包的target；存在独立Cargo.toml时仍须判断其真实归属，不能仅由文件夹名决定。

## 4. 通用原则在Rust首期的工具组合实例

### 4.1 基础能力及边界

| 工具/接口 | 首期用途 | 输出与解析 | 证据及限制 |
|---|---|---|---|
| Cargo metadata | workspace/package/target、声明/解析依赖和feature | JSON；按package ID关联，不拆解其内部字符串 | CAP01，实测；no-deps的resolve为null |
| Cargo build/check/test消息 | 编译产物、构建脚本信息、实际profile/features、构建结果 | JSONL事件，stdout/stderr分流 | CAP02；test尾部仍有文本 |
| rustc -Vv、--print cfg | 编译器身份、目标条件、显式cfg、panic等 | 固定键值行，小解析器 | CAP18；裸命令不自动包含Cargo/build.rs参数 |
| rustc --print target-features | 可支持的目标特性清单 | 小范围文本解析或保留证据 | CAP18；支持不等于启用 |
| rustc --error-format=json | 编译器错误、警告、代码和位置 | stderr JSONL；独立于Cargo外层消息解析 | CAP19；不是完整类型查询接口 |
| rustc --emit=dep-info | 编译器实际读取的源依赖 | Makefile依赖语法；处理转义/续行 | CAP20；不是包依赖图，也不是构建脚本所有运行输入 |
| cargo rustc -- --emit=mir | 局部类型、基本块、调用、赋值、分支/错误传播线索 | 固定版本MIR文本；保留原始引用 | CAP20；解析器尚未实现，格式会变 |
| 源文件/清单/锁文件解析 | 身份、声明、文档定位、输入摘要 | 标准TOML/JSON/字节读取 | 不用正则替代语法/清单解析；路径规范化不丢原始身份 |
| Tree-sitter Rust | 补足声明、属性、use和调用语法定位 | AST节点、byte range | CAP03；cfg未筛选、宏未展开 |
| 小型源侧观察驱动 | 请求指定输入下的行为记录 | 固定JSONL契约 | CAP06；本次仅单个两步序列 |

Cargo、rustc命令及格式的官方依据见S01—S03、S33—S35；本表的具体输出由本次实测支持，不将最新版文档中的新增选项默认视为1.85.1已支持。特别是 `--print target-spec-json` 虽出现于help，实测仍需不稳定选项，不能仅按help列名判断可用。

实际Cargo项目优先通过Cargo维持正确的依赖、extern、cfg和build.rs环境；直接调用rustc适合独立可控样本或已准确捕获参数的场景。不得通过猜测 `--extern`、手工拼不完整flags来制造“成功”输出。后续若需要捕获真实编译调用，先研究包装器契约和失败行为，再实现一个受控适配器；不要为每次查询临时生成编译脚本。

### 4.2 MIR、LLVM IR与内部接口如何取舍

实测MIR中，`checked_step` 显示u8参数、Result返回、checked_add、ok_or和基本块；Cargo编译api后，MIR出现宏生成的 `generated` 函数及Counter状态写入。它比纯语法树更接近已编译的局部语义，但不能取代模块公开性、完整trait声明、文档意图和动态执行证据。

MIR文件首部明确标注面向人、格式可随时变化。因此首期可将其用作局部证据；如果选择机器解析，必须固定rustc提交/版本，先定义可识别构造及不支持构造，验证完整消费、错误拒绝和覆盖标记，再输出小型FactFragment。禁止“几个正则匹配成功”就宣称完整CFG/调用图。格式失配先报告解析缺口，不能自动把全部MIR交AI当确定事实。

`--emit=llvm-ir` 和 `--emit=metadata` 也是rustc能力，但本次未实测其解析。LLVM IR适合明确的低层操作/ABI问题，源语义恢复成本通常更高；二进制rmeta不是公开通用事实Schema。它们不进入首期默认采集包。[S33]

宏展开、HIR/THIR调试输出及rustc_driver回调可进一步取数据，但受不稳定接口和版本耦合影响。THIR侧重带类型的可执行体，并不表示整个项目所有声明；内部driver API无稳定承诺。[S36、S37] 本次stable的-Z探测失败。不得启用RUSTC_BOOTSTRAP绕过基线，也不因“程序很小”就默认开发编译器插件。只有具体缺口与长期维护收益成立时另立任务验证。

### 4.3 其他工具的处理结论

| 候选 | 调研结论 | 当前决策 |
|---|---|---|
| rust-analyzer / SCIP | 定义/引用/实现等导航能力；SCIP是协议，不是独立分析器 [S04、S05、S13、S14] | 小工具组合不足时再按请求验证；不默认常驻语言服务器 |
| rustdoc JSON | 文档/API条目有专门数据模型；实验格式且有format_version [S06、S07] | stable负向探测；单独固定分析工具链后才可接入 |
| cargo-llvm-cov | 可提供执行覆盖数据 [S09] | 只有覆盖消费请求时启用；覆盖率不证明等价 |
| Miri | 可发现执行路径上的部分未定义行为，有平台/操作限制 [S08] | unsafe等具体风险触发，不替换正常工具链 |
| Kani | harness驱动的性质验证，需要明确假设和边界 [S10] | 后续特定难点候选，不作普遍采集前提 |
| CodeQL | Rust已有正式支持；免费CLI使用范围有许可条件 [S19、S20] | 不能笼统排除Rust，也不能默认无限制免费；首期不引入 |
| Semgrep CE | 适于规则匹配；CE和付费跨文件分析能力不同 [S21、S22] | 按需小规则扫描，结果只是finding |
| Joern | 已核查官方前端列表未列Rust；通用CPG不代表任意语言支持 [S17、S18] | 不作为Rust首期工具 |
| Clang | compilation DB和AST可支撑C/C++；不能自动解析Rust或建立FFI语义 [S15、S16] | 混合语言以后按需调研/验证 |
| Sonar / PMD / Sourcetrail | Sonar Rust可接Clippy与覆盖；PMD与CPD支持范围不能混淆；Sourcetrail仓库已归档 [S23—S25] | 不部署质量平台补充基础语义；不选归档工具作为新主依赖 |

这些结论是候选筛选，不是拒绝将来所有高级分析。矩阵中未固定运行版本、许可证需再核对或没有真实输出样例的项，均不具备解析器编码准入证据。

## 5. 辅助Skill调研与适配

| Skill及固定版本 | 核查结果 | 可借鉴部分 | 限制与当前结论 |
|---|---|---|---|
| wikify-ingest-repo，964470a | CLI索引与LLM合成分离；SCIP边推断代码明确基于引用作用域 [S26、S27] | 定位、引用和选择性上下文 | 不是精确调用图；默认安装/写wiki行为需适配；仅可选 |
| code-review-graph explore-codebase，9c26c62，包2.3.6 | 检查了Skill、Python依赖和Rust AST处理 [S28—S30] | 结构导航和按需上下文 | 语法/启发式边不能保证真实分派；未测其Token宣传目标；不默认引入MCP服务 |
| audit-context-building，5c99c03 | 按函数追踪假设、不变量及依赖 [S31] | 对工具剩余缺口做局部调查 | 不执行默认全仓/多代理展开；模型结论须保留来源和推断标签 |
| sarif-parsing，5c99c03 | 使用结构化格式和确定性过滤方式 [S32] | 格式处理方法 | 无需让模型重读机器JSON；不独立获取项目语义 |

前两仓库MIT；Trail of Bits所核查仓库采用CC-BY-SA-4.0，若复制或改编其内容需核对归属和共享义务。本文仅引用与评价，没有复制外部Skill为产品实现。许可证确认必须覆盖所用具体文件及第三方依赖，不能把仓库许可证当成所有依赖许可。

辅助Skill的接口适配仍由编排器宿主机制承担；UPA只请求所需内容并接受经验证的事实。OpenSpec、Superpowers用于规划/实施方法，不提供源语义事实；目标仓颉Skill能力通过规划中的skill_usage_plan使用，不能拿目标语言建议补造源行为。

## 6. 实际探测结果

完整命令、退出码、逐文件SHA256见[manifest](evidence/manifest.json)，操作步骤见[复现说明](evidence/README.md)。所有输出均为真实工具执行，未修改输出中的临时绝对路径。

| 探测 | 观察 | 得出的限定结论 |
|---|---|---|
| Cargo metadata --no-deps / full | 两包、两example、一bench和custom-build均出现；no-deps resolve为null；full有path依赖边 | 拓扑和target字段可取；不能从no-deps假造解析图 |
| feature配置 | extra运行的resolve node增加extra | 构建配置必须进入事实和缓存身份 |
| cargo check/test JSON | check有build-script-executed/compiler-artifact/build-finished；test后有普通测试文本 | 事件解析需分流；build-finished成功不是测试完成信号 |
| Tree-sitter | 无语法错误；看到cfg属性、use及宏调用 | 语法事实可得；不能据此筛除未启用项或确认宏生成实体 |
| rustc cfg | 基线有目标宽度/字节序/panic；显式extra/abort参数改变输出 | 可小工具获取配置，但必须传真实配置 |
| rustc JSON错误 | 故意返回错误类型，退出1并产生结构化诊断 | 非零退出不等于没有可用诊断；诊断仍不是全部类型事实 |
| rustc MIR/dep-info | 输出实际依赖文件和MIR；api MIR包含宏生成函数、状态操作 | 可复用编译器局部证据；解析和跨配置关联仍需实现 |
| 行为观察 | 254→255返回255；第二次返回overflow且状态保持255 | 覆盖该两步序列的返回/错误/状态；没有覆盖所有输入和副作用 |
| rustdoc JSON / expanded / target-spec | stable返回1，提示需nightly或不稳定选项 | 不能作为1.85.1默认能力；负向结果有效 |

本次没有跨平台、互斥feature、proc-macro、动态trait分派、复杂unsafe/并发、真实GitHub库、仓颉比较、数据库事务或模型调用验证。不以这些未执行项标记失败或通过；它们按具体后续任务需要补证。已探测数据足以支持部分解析器的样例设计，不足以宣称UPA全功能可用。

## 7. 多工具组合、解析与汇总方案

以下为研究得出的参考实现方案，不是已编码模块。每个Recipe采用同一个调用—解析—汇总—校验—落库流程，只替换执行者。工具调用DAG不等同于迁移工作流状态机。

| Recipe | 输入与步骤 | 解析器/汇总器 | 输出及失败边界 |
|---|---|---|---|
| R01 拓扑 | 文件发现→每workspace metadata→必要时完整resolve→清单/锁摘要 | P01、清单解析；按workspace/package/target身份合并 | F01—F03及target投影；解析失败保留已知声明和缺口 |
| R02 配置 | metadata→实际构建事件→rustc cfg/版本→dep-info/生成输出 | P02/P15/P17；按crate与配置关联 | F04/F05；不把裸cfg当完整Cargo配置 |
| R03 出口/关系 | 源声明定位→有效配置→需要时MIR局部信息→尚缺字段才选LSP/SCIP或rustdoc | P03/P17；候选P04/P05；公开可达性独立验证 | F06—F09；语法、引用、may-call、解析调用分开 |
| R04 行为 | R02/R03定位→读取相关断言/文档→运行限定测试/观察驱动→必要局部AI提取 | P02/P06/P16/P17；按case/sequence/step汇总 | F10—F19；区分声明/推断/观测，未观测副作用标缺口 |
| R05 专题 | 请求明确风险→选择一个增量工具→解析finding/证据 | SARIF/coverage等独立小解析器 | 不把安全finding当完整语义；非首期默认 |
| R06 意图 | 定位少量非结构化文档→有预算的辅助Skill/AI→Schema验证 | 引文定位器、结构化提取接受器 | F10/F21；不接受无引用断言，冲突不覆盖 |

### 7.1 解析映射和关联键

| 输入字段/构造 | 输出候选 | 必须处理 |
|---|---|---|
| metadata packages[].id / targets[].kind | 包身份/target种类 | ID不透明；kind为集合，保留多值 |
| dependencies[].kind、resolve.nodes[].deps | 声明边/解析边 | Cargo的kind=null代表普通依赖；按该外部契约显式映射，不能推及任意null |
| features定义与resolve.features | 可选feature/已解析启用集 | 定义和生效分别存储；配置不可合并成一个全集 |
| compiler-artifact profile/features | 构建条件证据 | 比较声明与实际配置，不用最后写入消解冲突 |
| rustc cfg行 | flag或key/value集合 | 重复key可合法，如target_feature；空字符串值可能合法 |
| rustc JSON spans | 定位、诊断代码/级别/建议 | byte与字符列单位不同；外部源路径可能不可访问 |
| dep-info | 实际源输入边 | Makefile转义/续行/多target；不等于全部运行输入 |
| MIR block/call/assign | 局部关系及来源 | 版本专属子集；未知构造降覆盖或拒绝，禁止静默忽略 |
| observation step/before/return/error/after | 特定序列观测 | 初始状态、输入、观察器版本、退出码和输出摘要 |
| 文档自由文本 | 声明/AI推断事实 | 引文、实体定位、条件、矛盾和模型配置 |

主体关联至少包含source_snapshot、workspace/package、target、configuration、entity和source range。语法实体与MIR/LSP身份关联不唯一时返回候选及ambiguous状态，不能凭同名函数强行连接。补充字段合并；矛盾字段并存，保存每个来源和派生规则，不做隐式“最后一个赢”。

### 7.2 接受与存储契约

建议FactFragment包含：fact_id、requirement_id、subject、value、source_snapshot、configuration_ref、provenance、evidence_refs、coverage、gaps、derivation_refs。provenance区分tool_observed、source_declared、rule_derived、execution_observed、ai_inferred；这是参考枚举，正式Schema仍由C01/UPA01按消费者确认，不在本文冒充已落地接口。

coverage须描述请求范围、已检查对象、遗漏对象及原因；若分母未知，则明确unknown，不返回虚假百分比。只有类型、枚举、引用、配置、快照及必需覆盖都满足时接受批次。某步骤失败可返回部分事实，但不能把空结果缓存为完整。

数据库接受采用事务与幂等键；步骤尝试、原始输出和事实分开保存。缓存键包含源文件/锁文件、配置、工具、解析器、汇总规则、查询投影和必要模型配置的版本摘要；未提交源变动也会失效。过程数据、SQLite及其WAL/SHM、日志、模型片段均在本次migration内，最终迁移结果仍按既定独立目标布局。

### 7.3 枚举和假值反证

| 输入情形 | 正确处理 |
|---|---|
| 数值枚举包含0，实际值0 | 接受；不因假值丢弃 |
| 布尔字段允许false | 接受且保留；不等于字段缺失 |
| 字符串枚举明确允许空串 | 接受；未声明则拒绝 |
| 非空但不在允许集的字符串 | 拒绝或记录unsupported，不能当有效 |
| 以false代替整数0 | 严格类型检查失败，不依赖宿主语言相等判断 |
| 缺失/null/unknown/none | 按各字段Schema分别处理，不统一填默认值 |
| 工具新增枚举值 | 原始值保留，映射标unsupported并登记格式缺口；不削弱规范枚举 |
| 空数组 | 可以是合法值；是否证明“没有”取决于范围和覆盖证据 |

此要求同时约束解析器和汇总器。外部格式允许扩展，与内部事实必须合法并不矛盾：通过显式映射层隔离。

## 8. Token与运行成本控制

机器可读包括JSON、TOML、协议消息以及有明确解析规则的文本，不只包括JSON。优先确定性解析、字段投影和关联，不把全量Cargo输出、源树、MIR或数据库转成提示词。非机器可读的文档和工具无法覆盖的语义问题才进入局部AI提取；输出为JSON也不改变其AI来源。

每次查询先给事实摘要、coverage/gaps和按需取证引用，支持字段选择、分页、实体/文件范围和增量。模型请求附尚缺字段、有限源片段、提取Schema与预算；禁止为一个函数展开整个仓库或全量知识库。缓存事实与AI提取结果都检查版本及适用范围。

记录工具耗时、输出字节、缓存命中、模型输入/输出Token、重试、恢复及审查成本；无法取得Token时标unknown或明确估算方法，不用字节冒充实测Token。本次没有Token节省百分比，未运行context-mode、billion-context或新增此类依赖。借鉴离线处理和按需加载即可。

## 9. 编码前准入、优先任务与剩余缺口

调研是开发AI编写事实获取器、解析器、汇总器和组合流程前的必要工作。它按事实范围有效，不是每次运行时重新研究，也不是UPA00一次完成便永久有效。每个编码任务引用research_refs、capability_refs、sample_refs；有证据的范围可推进，缺口只阻塞依赖它的范围。

建议实施顺序：

1. UPA05先做CAP01、CAP02、CAP18、CAP19的小解析器；用本次真实输出设计正常、缺字段、未知枚举、合法假值和混合输出用例。还需补真实库及适用失败样例后满足其完整准入。
2. UPA02/UPA06接通R01/R02，验证单/混合集合、事务、重复提交、错快照及部分失败；不能把已有研究夹具当成通用流水线已实现。
3. 根据LMO04真实查询，选择CAP03语法和CAP20局部MIR解析范围。先补MIR条件分支、资源释放、trait/泛型及位置关联样本，再决定可机器接受的构造集合。
4. 为R04明确观察驱动契约及预言，覆盖五类行为；先有源侧轨迹，再由LMO11和SAR做两端比较。没有副作用探测证据时不得声明该维度已覆盖。
5. 只有第3—4步暴露具体缺口，才验证rust-analyzer、rustdoc或其他高级候选。记录小工具组合为何不够、增量精度与成本，不按工具名单全部安装。

需后续补充的明确证据：真实三库/多库样本；构建失败与离线缺依赖；dev/build/optional及平台条件；重导出、proc-macro、泛型trait、资源/异步按需样本；MIR解析稳定性；数据库与Schema验证；辅助Skill实际宿主调用和预算。上述不影响本报告作为调研交付，但不能把UPA00全范围实现准入或UPA01—UPA06标完成。

## 10. 本轮反证检查与交付边界

| Finding | 修正 | 证据/裁定 |
|---|---|---|
| 将no-deps当完整依赖图 | 区分声明与resolve | metadata两份输出 |
| 将语法/引用图当真实调用图 | 关系类型和精度分层 | Tree-sitter输出、S27源码 |
| 忽略rustc已有能力而优先大工具 | 增加CAP18—21、小工具优先门槛 | cfg/诊断/MIR/dep-info实测 |
| stable选项与内部输出混为稳定协议 | 区分可执行、格式稳定、可解析三个条件 | MIR警告及三项负向输出 |
| test构建成功冒充测试通过 | 处理JSON与测试文本边界 | tests.stdout |
| 只描述正常返回 | 增加错误/状态/副作用/序列及前提 | F10—F19；两步源侧轨迹是部分证据 |
| 模板/源码审查冒充实际能力 | 独立证据等级、production_ready=false | 能力矩阵及manifest |
| 事实分析器决定目标布局 | 明确只产源侧事实 | 职责边界文档检查通过 |

本轮仅新增调研文档、机读研究数据和隔离取样证据，并更新索引及任务证据。没有提交事实获取业务代码、CI实现、编译器二进制或模型生成目标代码；没有完成真实迁移或独立外部审查。所有工程任务的完成状态仍以docs/shared/tasks.json为准。

## 11. 一手资料

以下链接用于核查工具声明；运行时必须另外固定版本。S26—S32为已检查的固定提交文件，完整SHA见链接。研究原始输出及文件摘要是本次版本化证据。

- [S01] [Cargo metadata](https://doc.rust-lang.org/cargo/commands/cargo-metadata.html)（访问：2026-10-19）
- [S02] [Cargo external tools / build JSON](https://doc.rust-lang.org/cargo/reference/external-tools.html)（访问：2026-10-19）
- [S03] [Cargo build scripts](https://doc.rust-lang.org/cargo/reference/build-scripts.html)（访问：2026-10-19）
- [S04] [rust-analyzer](https://rust-analyzer.github.io/book/)（访问：2026-10-19）
- [S05] [rust-analyzer features](https://rust-analyzer.github.io/book/features.html)（访问：2026-10-19）
- [S06] [rustdoc experimental output formats](https://doc.rust-lang.org/nightly/rustdoc/unstable-features.html#-w--output-format-output-format)（访问：2026-10-19）
- [S07] [rustdoc JSON Crate schema](https://doc.rust-lang.org/stable/nightly-rustc/rustdoc_json_types/struct.Crate.html)（访问：2026-10-19）
- [S08] [Miri](https://github.com/rust-lang/miri)（访问：2026-10-19）
- [S09] [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov/blob/main/README.md)（访问：2026-10-19）
- [S10] [Kani getting started](https://github.com/model-checking/kani/blob/main/docs/src/getting-started.md)（访问：2026-10-19）
- [S11] [Tree-sitter query syntax](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/1-syntax.html)（访问：2026-10-19）
- [S12] [Tree-sitter grammar](https://tree-sitter.github.io/tree-sitter/creating-parsers/3-writing-the-grammar.html)（访问：2026-10-19）
- [S13] [SCIP protocol](https://github.com/scip-code/scip)（访问：2026-10-19）
- [S14] [SCIP indexers](https://7.1.sourcegraph.com/code-navigation/writing-an-indexer)（访问：2026-10-19）
- [S15] [Clang compilation database](https://clang.llvm.org/docs/JSONCompilationDatabase.html)（访问：2026-10-19）
- [S16] [Clang JSON AST](https://clang.llvm.org/doxygen/JSONNodeDumper_8h_source.html)（访问：2026-10-19）
- [S17] [Joern frontends](https://docs.joern.io/frontends/)（访问：2026-10-19）
- [S18] [Joern CPG](https://docs.joern.io/)（访问：2026-10-19）
- [S19] [CodeQL CLI support and license scope](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-cli)（访问：2026-10-19）
- [S20] [CodeQL Rust GA](https://github.blog/changelog/2025-10-14-codeql-scanning-rust-and-c-c-without-builds-is-now-generally-available/)（访问：2026-10-19）
- [S21] [Semgrep analysis scope](https://semgrep.dev/docs/writing-rules/glossary)（访问：2026-10-19）
- [S22] [Semgrep CE](https://semgrep.dev/products/community-edition)（访问：2026-10-19）
- [S23] [PMD and CPD](https://pmd.github.io/pmd/)（访问：2026-10-19）
- [S24] [Sonar Rust](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/languages/rust)（访问：2026-10-19）
- [S25] [Sourcetrail archive](https://github.com/CoatiSoftware/Sourcetrail)（访问：2026-10-19）
- [S26] [wikify ingest Skill](https://github.com/vlasenkoalexey/wikify-repo/blob/964470a62406cfa81c7419f1d930bd7960606b75/wikify/skills/wikify-ingest-repo/SKILL.md)（访问：2026-10-19）
- [S27] [wikify SCIP edge inference](https://github.com/vlasenkoalexey/wikify-repo/blob/964470a62406cfa81c7419f1d930bd7960606b75/wikify/scip_index.py)（访问：2026-10-19）
- [S28] [code-review-graph explore Skill](https://github.com/bop-dap-dev/code-review-graph/blob/9c26c62948fd1e7e1129806a92232e06ec29ccbb/skills/explore-codebase/SKILL.md)（访问：2026-10-19）
- [S29] [code-review-graph parser](https://github.com/bop-dap-dev/code-review-graph/blob/9c26c62948fd1e7e1129806a92232e06ec29ccbb/code_review_graph/parser.py)（访问：2026-10-19）
- [S30] [code-review-graph version and dependencies](https://github.com/bop-dap-dev/code-review-graph/blob/9c26c62948fd1e7e1129806a92232e06ec29ccbb/pyproject.toml)（访问：2026-10-19）
- [S31] [Trail of Bits audit context Skill](https://github.com/trailofbits/skills/blob/5c99c03fb8a9ea568432ecbcba5d86e9f4ac2bf0/plugins/audit-context-building/skills/audit-context-building/SKILL.md)（访问：2026-10-19）
- [S32] [Trail of Bits SARIF parsing Skill](https://github.com/trailofbits/skills/blob/5c99c03fb8a9ea568432ecbcba5d86e9f4ac2bf0/plugins/static-analysis/skills/sarif-parsing/SKILL.md)（访问：2026-10-19）
- [S33] [rustc CLI outputs](https://doc.rust-lang.org/stable/rustc/command-line-arguments.html)（访问：2026-10-19）
- [S34] [rustc print options](https://doc.rust-lang.org/rustc/command-line-arguments/print-options.html)（访问：2026-10-19）
- [S35] [rustc JSON diagnostics](https://doc.rust-lang.org/beta/rustc/json.html)（访问：2026-10-19）
- [S36] [THIR](https://rustc-dev-guide.rust-lang.org/thir.html)（访问：2026-10-19）
- [S37] [rustc driver stability](https://rustc-dev-guide.rust-lang.org/rustc-driver/intro.html)（访问：2026-10-19）

## 12. 按需完整及增量获取的规范衔接

补充要求的规范来源为[UPA-R09—R12](../../../../openspec/changes/migration-skills-suite/specs/upstream-project-analysis/spec.md)，实现参考见[design.md](../design.md)，验收见[acceptance.md](../acceptance.md)。适用于所有语言：按需确定事实类型、对象及配置，在最小完整单元内取得全部不可缺省数据，按依赖增量更新；不可随意扩大语义范围。

本报告事实目录是分类与选型依据，不自动等同于逐项字段Schema。后续具体获取任务应补充对应单元的必需/条件必需字段、必要关联、最小调用粒度、扩展理由及成本。能力矩阵中的probe_passed只支持已探测字段，不能推导整个事实单元完整。当前原始实测证据保持不变，未新增完整性流程或增量数据库验证。

当次无法取得必需数据时明确缺口；预算耗尽保存继续点，不省字段伪成功。机器输出附带更多信息不触发额外语义分析；projection仅限制交付展示，不改变底层接受标准。增量可复用已证明对新快照有效的片段，但重新校验单元并保留复用依据。
