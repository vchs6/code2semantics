# Validation

## 当前结论与边界

本次修订主变更及相关八个子变更的现有 proposal/specs，加主变更现有 design/tasks 与 traceability/validation 文档。遵循 `openspec instructions` 各工件模板按上游顺序生成，再由 OpenSpec 严格校验和独立语义核查验收文档；此处不宣称公共契约资产已替换、组件已实现或真实集成已通过。

既有 `skills/layered-semantic-facts/assets/`、`references/`、本目录 `validation/validate_contracts.py` 和 fixtures 含旧协议，本轮保持原状。其曾有格式校验结果不能证明本次新契约符合性，也不能作为 tasks 2–8 的完成依据。旧协议无需兼容，后续按最新设计直接重写统一定义、样例、接口说明和全部消费者；不建设双轨、兼容入口或旧数据迁移工具，不要求旧记录历史可读。正常拒绝不匹配数据并保护原始数据，禁止以清库绕过校验。

## 本轮文档验证流程

1. 已取得 `openspec list --json` 确认项目 root，并取得 `status --change epic-layered-semantic-fact-skill --json` 确认四项现有工件和具体输出路径。
2. 依次取得 `instructions proposal`、`instructions specs`、`instructions design`、`instructions tasks`，使用对应模板并读取定稿上游生成下游；无缺失工件新增。
3. 执行 `openspec validate epic-layered-semantic-fact-skill --strict` 检查结构、spec 格式与工件约束。实际运行结果：退出码 0，输出 `Change 'epic-layered-semantic-fact-skill' is valid`；仅证明本次主文档结构校验通过。
4. 独立逐条核对 [traceability.md](traceability.md) 与用户已定稿边界；OpenSpec 通过只证明其覆盖的文档结构，不能替代资产、组件及跨变更语义核查。

## 后续实施验收门槛

| 门槛 | 责任与交付 | 必须验证的要点 | 当前状态 |
| --- | --- | --- | --- |
| 公共目录→查询→响应定义及主设计资产校验 | 主 tasks 2–4，含 common/pipeline/needs/matrix 共享定义、接口说明及样例 | 主 validation/validate_contracts.py 随定义逐阶段替换，验shape/引用/样例，不等待子query运行时；全部直接替换为当前协议；无用户历史/快照/revision/refresh/旧parser签名；origin与knowledge独立、context/coverage/basis及完整性缺口保留 | pending，本轮未改资产 |
| 工具说明与矩阵 | survey-info-acquisition-tools、capability-matrix | 开发期构造器子提案/设计/任务首阶段先交付固定信息需求清单，不等待工具；新增需求经开发期提案处理；研究按该清单增量开展；初始空；点亮表示工具通过接入验收可使用，无单独生产状态；运行/超时/重试/成功失败由执行器管理 | pending，已有工具报告待按新需求复核 |
| 纯解析与接入验收点亮 | add-info-parser 开发流程 | 原生输出+invocation-profile→统一来源信息；不执行、不读项目/事实仓库、不选工具、不归纳/维护矩阵；输入缺证据返gap | pending，不把规划或旧样例当验收 |
| 归纳与构造 | induction-batch-trigger、constructor | 未满足需求触发，非空不足不算满足；分组保持当前内容与上下文；已点亮工具组合执行；合法边界完整直接节点识别、必要上级路径；不持久化/不组装Response | pending |
| 仓库 | repository | 结构化事实/证据/有效性，SQLite重开重读、事务拒绝/回滚、变化/删除/前提失效不当前命中，不存最终Response | pending |
| 查询 | query | 覆盖→构造→校验入库→重读→最小响应；当前按需增量，目标及必要上级/完整性前置义务推进算进展；满足/无进展/预算终止 | pending |
| 包装与对话 | define-skill-packaging | 同一当前契约、默认范围标注、意图澄清、明确要求报告、仓库外运行、Agent Skills Specification检查 | pending |
| 主集成 | tasks 8，acceptance-results.md | 真实工具→非空事实→入库重开重读→最小查询；报告S1–S12及新边界；接入验收和集成实证分开记录但不增加矩阵状态 | pending |

所有子组件先在自身 design/tasks 明确交付路径与执行命令，再推进 apply 并接收局部验收。主变更不重复其实现，主集成不得用 mock、gap-only、示例 JSON 或旧校验器通过冒充真实生产。任何缺失、失败或环境不支持均保留 pending 和明确缺口，不缩减目录需求。

## 后续集成场景断言

- 多项目、多工作空间、混合目录、同名身份、嵌套重叠与多父边界；成员不是依赖证据，跨范围引用不扩大授权。
- 固定目标与观察粒度，请求节点所需事实及其直接节点最小投影；必要上级先构造但不全部输出；完整识别边界内全部直接节点，未确认完整性不得充分命中，不预建每个 child 完整事实，不沿循环递归成树。
- 来源修改、删除及未提交/未跟踪变化后的按需重构；无关有效事实保持，受失效前提影响不当前命中；无用户历史、快照、revision、refresh 协议或自动全量重建。
- 缺少、unknown、证据不足和非空不足触发归纳，按事实类型/主体/当前内容状态/上下文分组；证据、冲突、限定否定和必要context/coverage/basis不丢失。
- 联合条件成立且有执行观察的实际循环与互斥候选环分别表达；内部算法的控制、数据更新、边界与异常证据，跨语言差异保真。
- 开发期固定清单交付→研究→解析器开发接入验收，与运行期查询严格分开；运行构造器只消费清单匹配请求/未满足项并聚合当前获取计划，不生成/扩展清单，不触发研究/开发/点亮，未覆盖需求gap待开发期变更处理。
- 初始矩阵空；未点亮说明不执行，解析开发接入验收后点亮即可使用，无另设生产状态；调用运行状态在执行器内。工具组合选择先覆盖/环境，再轻量简洁多语言。
- 无进展基于本次有界覆盖集合，必要上级路径与直接节点完整性义务的推进也算进展，无关事实、重复数据、调用次数不算；预算终止保留有效已有事实和gap。

## 本轮偏差与未执行项

当前没有把旧协议资产视作新接口；这些资产与验证程序需要后续直接统一替换，是明确未执行义务而非已通过。八子缺失 design/tasks 本轮不新建，子实现、工具接入验收、公共契约校验和真实集成结果全部 pending。本轮不执行 apply、发布或归档。
## 本轮实际汇总验收记录

以下为 root 独立执行的本轮结果，不代表产品实现或新公共契约资产已通过验收。

- `openspec validate --all --strict --json`：退出码 0，10 项通过、0 失败，无 ERROR/WARN。`add-induction-batch-trigger` 有 1 项 INFO，`add-semantic-fact-query` 有 2 项 INFO：上游能力尚未发布，相关 MODIFIED 目前不能归档；两项 survey 变更各有 skip_specs INFO。本轮不归档，不为消除这些提示把 MODIFIED 改为 ADDED。
- 文档范围与本地链接检查：23 份现有 Markdown、9 个变更、29 个本地链接；0 新文件、0 越界、0 损坏链接。八个子变更缺失的 design/tasks 均未创建。
- `git diff --check`：退出码 0，无空白错误。
- 本轮无产品改动，未执行产品测试；未使用旧契约校验结果证明新契约通过。
- fresh reviewer 已完整审读 23 份文档：无 Critical、无 Minor；唯一 Important 是构造器运行期生成开发清单。root 已亲读最新 constructor spec 20–33 行、主 tasks 5.0/6.2 与 tooling 两份 spec 的开发期场景，确认现为开发期固化清单，runtime 仅匹配并生成当前获取计划、未覆盖返回 gap，不启动研究、开发或点亮；该 Important 已关闭，无未解决阻断。
本轮补充开发期/运行期分离修订后，重新运行 `openspec validate epic-layered-semantic-fact-skill --strict`，退出码 0，输出 `Change 'epic-layered-semantic-fact-skill' is valid`。root 已在全部修订完成后独立重跑 `openspec validate --all --strict --json`：退出码 0，仍为 10/10 通过、0 失败，无 ERROR/WARN；同样保留 3 条上游能力未发布 INFO 与 2 条 skip_specs INFO。最终范围与链接检查仍为 23 份现有 Markdown、9 个变更、29 个有效本地链接、0 新文件、无越界；八子缺失 design/tasks 未创建。最终 `git diff --check` 退出码 0。这些结果不替代产品或集成验收，本轮未执行产品测试。
