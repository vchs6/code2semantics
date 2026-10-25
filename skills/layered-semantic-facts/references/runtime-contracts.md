# 公共组件边界与机读类型

本文定义组件共同消费的公共类型和职责；组件的 Python 方法、文件路径及执行命令由各子 design/tasks 确定。主变更只交付设计资产校验器，没有实现组件运行时。依据：研究 R1–R16/F1–F18，主设计 D1–D8。

| 类型 | 唯一 Schema JSON Pointer | 约束 |
| --- | --- | --- |
| Query | contract-format.schema.json 根 | 当前授权入口、固定 target/granularity/selections |
| NodeRef / SubjectRef / ExternalRef | common.schema.json#/$defs/node_ref / subject_ref / external_ref | 来源域限定身份；外部只引用不扩权 |
| Source / Validity | common.schema.json#/$defs/source / validity | 当前内容状态、修改/删除、未提交及未跟踪、失效原因 |
| Evidence / Assertion / Premise | common.schema.json#/$defs/evidence / assertion / premise | 正交来源和知识、context/coverage/basis、当前有效性 |
| Fact / Navigation / DirectInventory | common.schema.json#/$defs/fact_node / navigation_edge / direct_inventory | 事实字段、显式关系、直接身份完整清单分离 |
| Conflict / Gap | common.schema.json#/$defs/conflict / gap | 保留冲突双方与目录内未满足原因 |
| FactBatch | pipeline.schema.json#/$defs/fact_batch | facts/navigation/direct_nodes/conflicts/sources；没有最终响应 |
| ParseRequest / ParseResult | pipeline.schema.json#/$defs/parse_request / parse_result | 原生输出与调用描述 → observations/gaps |
| ConstructRequest / ConstructResult | pipeline.schema.json#/$defs/construct_request / construct_result | 请求/有效事实/未满足项/当前上下文 → batch/gaps |
| InductionRequest / InductionResult | pipeline.schema.json#/$defs/induction_request / induction_result | 类型+主体+当前内容状态+上下文分组；候选事实与gap返回 |
| StoredRecord / ReadResult | pipeline.schema.json#/$defs/stored_record / read_result | 存储事实批与事务关联；有效 known 与 rejected 缺口 |
| InformationNeeds | information-needs.schema.json 根 | 构造器开发期固定清单，不是运行时生成协议 |
| CapabilityMatrix | capability-matrix.schema.json 根 | 初始 entries=[]，工具说明与单一 enabled 状态 |
| Response | output-schema.schema.json 根 | 查询校验入库并重读后组装最小响应 |

## 身份、事实与有效性

node_ref 为 source_id/subject_id/node_id 三元身份。fact_id 在此完整节点身份内定位一个候选事实，允许同主体、同类型的不同上下文和冲突候选共存；字段前提使用完整 node+fact_id+field，附所依赖当前 content_state，不包含用户历史或知识修订参数。

fact.fields 依目录生成封闭字段集合，断言的值受 value_shape 约束。公共字段统一存于 common，pipeline 和 response 通过 $ref 消费同一定义。直接节点清单可以只有身份引用，不要求这些节点已经存在完整事实。navigation 的类型区分物理包含、工作空间成员、逻辑从属、组成、实现、细化、摘要以及调用/接口/运行/数据/部署/依赖，保留多父和回边，不强制递归树。

validity.state 为 current/modified/deleted/premise_invalid/unknown，sources 记录依赖来源和内容状态，非 current 必须有 reason。存储维护可保留失效记录；current read/已有有效事实/Response 中不得把它们当当前事实。来源变化和必要前提失效由查询/仓库组件按既定职责处理，设计校验器不访问源树、不实现失效传播或覆盖计算。

## 获取、解析、归纳与矩阵

ParseRequest 只含 tool_native_output（UTF-8 text）与 invocation_profile（工具身份/版本、命令、环境、输入来源、覆盖与证据）。parse(tool_native_output, invocation_profile) -> ParseResult 只作结构转换；输出 observation 必须保留 information_need_id、主体、原始语义信息、证据、context、coverage。证据和定位缺失则返回 gap，不能读文件补齐；不执行工具、不读取源项目/事实仓库、不选工具、不归纳或更新矩阵。具体原生格式解析和纯转换测试由解析器子变更实现。

ConstructRequest 的 existing_valid_facts 由查询流程提供，构造器不读取仓库。current_source_context 保留 sources、changes、必要上级与本次完整性义务。构造器仅消费开发期既定 InformationNeeds，聚合当前获取计划，按需求覆盖与环境筛选已 enabled 的工具组合，再偏好轻量、简单、多语言。构造器调用工具和解析器，再按 unmet 触发归纳，返回候选 batch/gaps，不持久化、不生成 Response。

InductionRequest.group 固定 fact_type、subject、content_states、context 和待补字段；不得把不同主体、内容状态或上下文混作同组。observations 可为空（无证据时允许显式 gap），unmet 非空；已有有效事实用于复用和背景，unknown、非空不足与冲突不因存在文本而被略过。InductionResult 返回候选事实与 gap，不能修改矩阵/仓库。

矩阵 entries 初始为空。每项工具说明包括 information_need_ids、output_kinds、languages、platforms、environment、invocation、combinations、limitations 和非空 research_basis 回链。研究只新增 enabled=false 的说明；仅解析器开发接入验收完成后 enabled=true，必须提供 acceptance.actor=parser_development 与非空测试证据；已点亮即可由构造器选用。调用的运行、超时、重试和成功失败属于执行器，不写矩阵。Schema 只能验证验收记录结构，接口权限与真正验收过程由矩阵/解析器组件实现。

## 设计资产验证及运行期义务

安装验证依赖：`python -m pip install -r openspec/changes/epic-layered-semantic-fact-skill/validation/requirements.txt`。

执行：`python openspec/changes/epic-layered-semantic-fact-skill/validation/validate_contracts.py`。全部引用仅从同目录 Schema 离线解析；检查研究指纹、四层/组织/十八事实、目录字段与 Schema 同源、正反样例以及代表性的来源/投影/前提/完整性一致性。需要时可从任意工作目录使用绝对脚本路径执行。

运行期仍须由子组件实现并测试：实际授权范围判断、当前内容核验、工具接入门禁、纯解析、信息需求匹配、未满足触发、必要上级和直接节点完整识别、覆盖充分性、SQLite 事务与重开、前提传递失效、预算/无进展控制、最小投影。主验证器没有这些组件的可执行入口，不能以样例通过替代它们；后续主任务 8.4 核对同源运行时行为，8.1–8.3 执行真实集成。本次没有旧协议定义、兼容入口、历史可读或迁移工具。
