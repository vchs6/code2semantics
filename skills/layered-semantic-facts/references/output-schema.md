# 最小事实响应

响应使用 `../assets/output-schema.schema.json`，事实本体唯一位于 `common#/$defs/fact_node`，与 FactBatch 共用；响应不作为仓库存储接口。依据：研究 R1/R2/R15/R16、S8–S12，主设计 D2/D3/D5/D8。

响应回显已固定的 query，并携带 sources、results、direct_nodes、premise_checks、conflicts、gaps、out_of_catalog、termination。termination 为 satisfied、no_progress、budget_exhausted、invalid_reference 或 unavailable。目录外类型/字段在 out_of_catalog；目录内 missing/unknown/非空不足/冲突/来源变化/前提失效/完整性不足在 gaps，二者不能合并。

results 仅携带请求节点及直接节点的请求字段；fact_id、node 和 granularities 提供身份与观察信息，fields 中每个值保留完整 assertion。direct_nodes 是请求边界的完整直接身份清单和该清单的 assertion；children 只有 node_ref，无递归 children，不能由清单生成每个 child 的完整事实集。必要上级不会因构造过而全部输出。后续深入使用 node_ref 发起新的当前查询。

origin 的 observed/derived/interpreted 与 knowledge 的 supported/insufficient/unknown/conflicting/not_applicable/absent 是正交维度，解释可以同时证据不足。unknown、不适用及限定不存在无 value；不足/未知/冲突/不适用须有 reason。basis 保存有定位和当前内容标记的支持/反驳证据、必要前提、方法与限制。最小投影不能丢弃必要的 context、coverage、basis、validity。

absent 必须有 negative.domain、claim、check_evidence_ids；检查域与 coverage.domain 一致，coverage 完整且 checked 非空，检查证据解析到 basis 中的支持证据。未发现、空值或工具不可用均不构成不存在。冲突保留不同 fact_id 的候选及 conflict.members，不以最后写入覆盖。

premise_checks 只投影必要前提的引用、knowledge、validity、context、basis，不含 value。引用包括 node、fact_id、field 与内部 content_state；查询运行时必须在仓库校验完整传递闭包。当前结果不能引用缺失、失效、删除、冲突、证据不足或上下文不兼容的前提。主设计资产校验只检查提供的样例闭包，不替代真实仓库重读或源码有效性核验。

satisfied 要求本次目标的全部目录内请求字段有当前充分事实、直接节点清单已证实完整，且没有剩余 gap 或目录外项；不能因存在非空结果就成功。预算/无进展终止保留有效已有结果及精确剩余 gap。部分直接清单必须携带 coverage_incomplete。每个主体和上下文独立比较覆盖，不能借其它主体命中抵消缺口。

样例：`openspec/changes/epic-layered-semantic-fact-skill/validation/response.json`。shape 反例验证字段保真与非法字段拒绝，semantic 反例验证投影、来源一致性、完整性和前提等跨字段条件。`validate_contracts.py` 的通过仅表示这些设计资产通过，真实工具、SQLite 重开重读和跨组件生产仍由后续任务验收。
