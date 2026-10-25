# 公共事实目录

本说明与 `../assets/fact-catalog.json`、`fact-catalog.schema.json` 同源。目录只定义事实表达能力；可用工具和实际事实覆盖分别由矩阵和查询判断。

依据：`openspec/changes/survey-semantic-fact-requirements/research/semantic-fact-requirements.md` 第 3 节 R1–R16、第 5 节 L1–L4/O1–O5、第 6 节 F1–F18、第 7 节追踪关系。JSON 的 `research.sha256` 按 UTF-8/LF 校验研究原文。每个事实类型保留 requirement、organizations、basis；每个字段的 basis 指回对应 F/R 章节与主设计决定，字段名是本次工程编码，不是外部标准。

四个观察粒度分别为软件系统与协作全景、职责组件与协作、程序元素与契约、内部行为与算法。O1 范围、O2 组织、O3 交互行为、O4 证据状态、O5 细化导航与粒度分离；没有唯一父树或必经中间层。

事实目录完整保留 F1 覆盖、F2 身份边界、F3 用途形态、F4 组织、F5 职责、F6 依赖、F7 交互、F8 接口、F9 元素类型、F10 绑定、F11 调用、F12 数据效应、F13 生命周期、F14 错误、F15 内部计算、F16 算法解释、F17 证据状态、F18 实现细化。`fields` 是该类型允许的字段，单条事实不必填满所有字段；缺失或不足仍须明确缺口，不能填空冒充覆盖。

所有字段使用 `common#/$defs/assertion`：origin、knowledge、context、coverage、basis、validity；有值时使用目录 value_shape。reference_value/reference_list/candidate_set/participant_set/binding_set/edge_set 分别保留引用、集合、候选条件、参与者角色、参数绑定和控制/数据边，不能压成无类型文本。F6.cycle 使用 cycle_value，区分结构环、条件环和具有联合条件及执行观察的实际循环。F15 控制计算与 F16 算法解释分列；语言差异保留在 context.language_semantics 和 F9.language_semantics 中。

直接节点清单在 `common#/$defs/direct_inventory`，组织关系在 navigation_edge，依赖为 F6；清单完整不代表每个 child 的事实已完整构造。只发现匹配部分时必须保留 coverage_incomplete，不能宣称充分命中。

信息需求清单结构由 `information-needs.schema.json` 定义，实际清单由构造器子变更开发期交付。每项可聚合一个类型的多个字段，need_id 是清单内稳定且唯一的标识；运行时仅匹配既定清单，未覆盖需求返回 uncovered_need。主变更没有产出或扩展实际开发需求清单。矩阵的工具接入验收与事实覆盖均不写入本目录。

验证：`python openspec/changes/epic-layered-semantic-fact-skill/validation/validate_contracts.py`。这是设计资产验证，不能证明解析、构造、持久化或真实集成已实现。
