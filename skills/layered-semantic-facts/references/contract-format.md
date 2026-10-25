# 当前查询契约

唯一入口结构为 `../assets/contract-format.schema.json`；公共类型定义在 `common.schema.json`。依据：研究 R1/R2/R14–R16、L1–L4/O1/O4/O5，以及主设计 D1–D6。

| Query 字段 | 语义 |
| --- | --- |
| contract_version / catalog_id | 当前公共定义标识，精确匹配；不匹配须拒绝 |
| request_id | 本次调用关联标识 |
| scope | scope_id、非空 directories、excludes、defaulted；是授权观察入口，不是项目身份 |
| target | scope 或 node；node 使用 source_id + subject_id + node_id，不包含路径、父身份或用户版本 |
| granularity | 固定本次 L1/L2/L3/L4 观察粒度 |
| selections | 非空 fact_type/fields 请求；目录外字段结构合法，但响应必须分列 out_of_catalog |
| budget | 正整数 max_rounds/max_new_assertions，达到预算时返回有效已有事实和剩余缺口 |

结构化输入必须显式携带 scope。对话适配层在意图已足够、位置缺省时，把调用时工作目录补入 directories 并标记 defaulted=true；不能将混合目录认作共同项目。目标、粒度或字段不明时应先澄清。接口只分析当前来源；历史、用户快照、revision、refresh 字段及旧入口一律拒绝，不提供兼容转换。

source_id 是独立来源域，subject_id 是域内有边界证据的软件主体，node_id 定位该主体内的语义节点。同名、同路径、多成员、多父或移动不能直接证明身份相同/不同；身份由构造侧基于边界证据识别，Schema 不替代语义判断。外部依赖使用 external_ref，包含 observed_in 和未授权边界，只能保留引用，不能据此增加源码授权。成员关系不推出依赖。

当前来源由公共 source 记录：root、content_state、status、dirty、has_untracked、excludes。content_state 是内部当前内容判定标记，涵盖相关修改、未跟踪内容、配置及排除边界；不成为用户版本参数。来源删除、内容不匹配或必要前提失效时，相关断言不作为当前命中；保留无关有效事实，按本次需求增量构造，不自动全量重建。

构造输入使用 `pipeline#/$defs/construct_request`：query、existing_valid_facts、unmet、current_source_context；后者保留 sources/changes、necessary_ancestors 和 obligations。必要上级路径及直接节点完整性属于本次有界覆盖义务，推进这些义务也算有效进展；字段非空、重复候选、调用次数或无关事实不算进展。此处定义输入语义，不实现查询控制循环。

请求内节点允许补齐必要上级，但输出只投影目标和直接节点，不输出全部上级或后代。已有不充分、unknown、冲突与限定否定必须保留 context/coverage/basis。主验证样例位于 `openspec/changes/epic-layered-semantic-fact-skill/validation/query.json` 和 `schema-cases.json`；运行命令见 runtime-contracts.md。
