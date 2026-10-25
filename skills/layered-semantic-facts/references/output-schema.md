# 响应契约

依据报告§3 R15/R16、§5 O4/O5、§6 F1–F18，响应在查询契约之后派生。机读权威是 output-schema.schema.json；其中每个事实的 fields 与目录同步封闭。value 节点是直接属性叶子（按所属事实合并元数据），subtree 节点仅含可续查引用与必要可靠性元数据，不带后代值；运行时以导航索引核验其确是请求目标直接下一级。粒度标签不用于推算导航步数。

每个被投影字段都是 assertion，必须保留 origin、knowledge、context、coverage、basis。origin 的 observed/derived/interpreted 回答如何得到，knowledge 的 supported/insufficient/unknown/conflicting/not_applicable/absent 回答支持程度与适用性；两个轴独立，解释可以证据不足，观察可以冲突。supported 必须带 value 与证据/前提；unknown/not_applicable/absent 不携带虚构值；insufficient/conflicting 可携带明确未证实/冲突候选值且必须给 reason。

absent 必须有限定 negative.domain、claim、检查证据 IDs，coverage.complete 和非空 checked，basis.evidence 非空，不能仅由空数组/null/未发现生成。结构条件仅为必要条件；检查证据的真实性、否定域等于声明域、覆盖穷尽性、联合条件和检查方法适用性必须由生产/入库验证器验证。无法证明时保留 unknown/insufficient 或 gap。

语义值使用显式 kind（text/scalar/reference/list/record）。关键引用字段由目录value_shape映射到common共享定义：reference_value/reference_list、candidate_set（target+conditions+mode）、participant_set（participant+role）、binding_set（parameter+argument+conditions）、edge_set（source+target+kind+conditions）。schema逐字段强制形状；record只用于其余描述性字段细化，不能替代关键引用结构。引用必须使用reference，禁止把应解析引用藏在text。来源/客体的解析和字段所要求的语义值类型由目录语义校验器进一步核验；任意文本并不证明关系表达合格。语言特有行为通过 context.language_semantics 和 F9.language_semantics 保留。

basis.premises 仅返回确切字段引用及修订，不返回未请求前提内容。查询读取 derived/interpreted 时在仓库内验证完整前提闭包的身份、快照、修订、支持状态和上下文适用性；不可获取/失效的闭包使该断言失效并形成 gap。最终投影仅发布请求字段与必要信封，不能顺带泄漏前提事实。冲突分支并存且显式标注；不采用最后写入覆盖作为消解规则。

gaps每项的target是精确node引用或明确scope_id；同F/field在多个主体上分别比较覆盖，A命中不能掩盖B缺口。pipeline.selector使用同一selection_target，归纳与构造不得跨目标借用覆盖。resolved_target返回实际采用的scope或节点continuation，精确node保持原revision，refresh显式返回新revision。

同快照知识修订是新 fact_revision，旧 revision 不变；snapshots 是所有响应断言/证据/前提依赖来源的绑定集合，分别携带 dirty/has_untracked 与内容清单摘要。跨来源事实不得只绑定一个源码版本。外部未解析引用含 observed_in，表示名称来自哪个已观察快照，不伪造目标身份或目标源码快照。

JSONSchema验证局部形状；跨记录等值、ID唯一、引用闭合、当前/历史匹配、目录语义、字段投影最小性、条件可满足性和证据真实性另由确定性运行校验承担。测试资产中将结构反例与这些语义拒绝要求分别登记。
