# Traceability

本表追踪当前权威 [proposal.md](proposal.md)、两个 [spec delta](specs/) 与 [design.md](design.md)；既有[研究报告](../survey-semantic-fact-requirements/research/semantic-fact-requirements.md)保持依据，不重做研究。映射是规划和验收义务，不是组件或测试已经存在的声明。旧 `assets/`、`references/` 和 `validation/` 尚未按本设计替换，不能据既有校验通过勾选完成。

| 需求与保留依据 | 主设计 / 公共任务 | 组件实施归属 | 主集成验收与可检查输出 |
| --- | --- | --- | --- |
| 四层观察、O1–O5 与 F1–F18；报告第3/5/6/7节 | D1；tasks 2–4 | 所有子组件消费同源定义 | 主设计资产校验逐阶段替换，不等待子query运行时；新目录/查询/响应及中间契约正反样例；所有定义与消费者直接统一替换，无旧协议兼容 |
| 契约驱动查询、当前项目集合；R1/R2/S1/S4/S8 | D2/D6；3.1、7.1 | add-semantic-fact-query、repository | 当前查询、修改/删除/未提交内容不旧命中；仅请求及必要关联重构，无历史/快照/revision/refresh |
| 主体边界：多独立项目/多工作空间/混合目录/同名/嵌套重叠；成员≠依赖；R1–R6/S1/S8/S9 | D2/D3/D8；8.1–8.2 | constructor、repository、query | 独立主体和关系证据，范围外仅引用不扩读取授权，多父不强制唯一树 |
| 最小直接下级、必要上级与完整直接节点；R2/R3/R4/R16/第5节 | D3/D6；3.1、4.1、6.2、7.1 | constructor、query | 合法边界全部直接节点识别；未确认完整性→gap；必要上级推进算进展；请求节点及直接节点最小字段，不预建全部child完整事实或递归后代 |
| 组织组成与有类型交互；R3/R5/R6/F4/F6/F7 | D2/D8；8.1 | constructor、induction、query | 跨项目/工作空间与范围外关系分开；关系方向/角色/条件/上下文和证据齐全 |
| 有效环与互斥候选环；R6/报告第5节/S9 | D3/D8；8.1–8.2 | constructor、induction、query | 回边保留；共同条件成立且有执行证据才称实际循环，互斥候选不误判，不递归组织为树 |
| 整体用途到内部算法、语言行为保真；R4/R6–R14/F1–F16/F18/S6/S10/S11 | D5/D8；8.1 | parser、induction、constructor | 真实证据支撑控制、数据更新、边界与异常、论证和未证实项；统一结构保留语言语义差异 |
| origin/knowledge 正交、限定否定、context/coverage/basis；R15/R16/F17/S11/S12 | D5/D8；3–4、8.1 | induction、repository、query | 缺少/unknown/证据不足/非空不足分辨，冲突保留；空值≠不存在，最小响应保留限定证据和前提引用 |
| 工具需求驱动研究与组合选择 | D4/D7；5.0–5.1 | survey-info-acquisition-tools | 开发期构造器子提案/设计/任务首阶段先交付固定信息需求清单，不等待工具；新增需求通过开发期提案启动研究与解析器验收，非查询运行步骤；既有 semantic-tooling-survey.md 按该清单新增需求增量复核；输出种类/覆盖/限制/语言/平台环境/调用/组合齐全，先覆盖环境后轻量简洁多语言 |
| 空矩阵与经接入验收点亮 | D4；3.2、5.2–5.3 | capability-matrix、info-parser 开发流程 | 初始空，研究补说明不点亮；解析开发验收完成受控点亮→工具可供构造器使用，不设 production_status/actual_production/execution_validation，执行器管理调用状态 |
| 解析纯转换边界 | D4；3.2、5.3 | add-info-parser | 仅 tool-native-output+invocation-profile→统一来源信息；证据从输入携带，不执行/读源项目/读事实仓库/选工具/归纳/维护矩阵 |
| 归纳未满足触发与分组 | D5；3.2、6.1 | add-induction-batch-trigger | 缺少/unknown/证据不足/非空不足触发；事实类型+主体+当前来源内容状态+上下文分组，保留证据冲突缺口 |
| 构造职责 | D3/D4/D5；6.2 | add-semantic-fact-constructor | 请求/既有有效事实/未满足项/当前来源上下文输入；运行期仅消费开发期既定清单匹配请求/未满足项并聚合当前计划，组合已点亮工具执行解析归纳，返回事实；不生成/扩展清单，不启动研究/开发/点亮，未覆盖gap待开发变更，不持久化/组装Response |
| 结构化事实仓库、有效性、前提闭包 | D2/D5；6.3 | add-semantic-fact-repository | 非空事实/证据关联/有效性持久化，SQLite重开重读、事务拒绝/回滚；不存最终Response，不承诺旧历史可读 |
| 查询循环、无进展和预算 | D6；7.1、8.2–8.3 | add-semantic-fact-query | 比对→构造→校验入库→重读→最小响应；目标与必要前置义务有界进展，无关/重复不算；三终止条件均保留有效事实和gap |
| 对话同契约、默认机器结果、明确请求报告与规范包装 | D7/D8；7.2 | define-skill-packaging | 默认范围标注、模糊意图澄清、同源Response报告；仓库外安装及 skills-ref validate 或规范逐项检查 |
| 真实集成与子交付非重复拥有 | D7/D8；5–8 | 八子变更局部实施，主编排接收 | 触发/推进子apply→交付→接收；S1–S12+新边界真实工具非空事实→入库重读→最小响应；接入验收与集成证据分别记录，不变成矩阵两套状态 |

主公开定义交付路径与阶段见 tasks 2–4；八子入口、前置门槛和预期局部输出见 design D7 与 tasks 5–7。子 design/tasks 缺失时先进入子规划流程，不假定交付存在；本轮不新建缺失子工件。主未来集成入口和证据见 tasks 8；任何尚无可执行命令/实物的交付保持 pending。