# Validation

## 当前结论与范围

2026-10-25 按 `openspec instructions apply --change epic-layered-semantic-fact-skill --json` 执行主任务 1.2、2.1–2.2、3.1–3.3、4.1–4.2。公共机读资产、四份接口说明、全部相应样例与设计资产校验器已直接替换。旧契约定义、旧正例、历史/用户快照/revision/refresh 入口、旧 parser(scope, needs) 签名及重复生产状态均不保留；仅以非法字段反例防止旧协议重新被接受。

研究原文、主 proposal/specs/design 的行为权威及八子规划保持不变。本次只交付公共数据契约和设计资产验证；没有实施解析器、矩阵、归纳器、构造器、仓库或查询运行时，没有运行真实工具、SQLite 事务/重开重读、安装包或端到端生产。主任务 5–8 保持 pending，不归档。

## 实际执行记录

1. 项目定位：`openspec list --json` 返回有效 root；`status --change epic-layered-semantic-fact-skill --json` 确认四项规划已具备；apply 返回 ready，原进度 1/23。本次仅按已有任务实施，记录状态前取得 `openspec instructions tasks --change epic-layered-semantic-fact-skill --json`。
2. 目录 RED：独立断言因旧 fact-catalog 仍含 production_status 以退出码 1 失败。替换目录/schema 后，18 类型、字段研究依据、L1–L4/O1–O5、研究 UTF-8/LF SHA-256 检查通过，退出码 0。
3. 查询 RED：当前 query.json 被旧 contract-format 拒绝（包括缺 snapshot 的要求）；退出码 1。替换公共查询和中间类型后，阶段性的 34 个非响应 shape 正反例通过。
4. 响应 RED：当前 response.json 被旧 output-schema 拒绝，8 项错误，退出码 1。响应 shape 替换后，跨字段校验尚未实现时，nonempty-insufficient-not-satisfied 被错误接受，整套检查按预期失败。
5. 独立审查：六类 Important（七个可复现反例）分别涉及构造当前来源交叉核对、完整性断言前提、自证循环、执行证据引用、上下文来源及仅有反证的充分断言；逐项 RED 均确认错误接受。已用对应 review-* 回归案例修复，并重跑整套为 GREEN。Minor 是目录包络缺 validity，已与公共 assertion.required 同步并加同源断言。没有遗留审查阻断。
6. 额外覆盖 RED→GREEN：scope-member-cannot-borrow-another-coverage 先错误接受，修复为按完整 node 身份独立验证请求覆盖；缺研究依据的矩阵条目先错误接受，补 required research_basis 后拒绝。独立项目同名身份、语言特有差异和冲突候选保留的合法样例也已通过。

## 可复现验证命令与结果

依赖：`python -m pip install -r openspec/changes/epic-layered-semantic-fact-skill/validation/requirements.txt`。

主契约命令：

```text
python openspec/changes/epic-layered-semantic-fact-skill/validation/validate_contracts.py
```

实际结果：退出码 0，输出：

```json
{"schemas": 7, "shape_cases": 64, "semantic_cases": 30, "catalog_facts": 18, "status": "design_assets_pass", "runtime_verified": false}
```

本机使用已有 Python 运行时和已安装 jsonschema/referencing；通过 PYTHONPATH 指定现有依赖目录。读取依赖需提升本地执行权限，未新增网络安装。脚本按自身绝对位置定位开发仓库，可在不同当前目录运行，不访问被分析源码或使用网络解析 Schema。

其他实际检查：

- `openspec validate --all --strict --json`：10/10 通过、0 失败；无 ERROR/WARN。保留 3 条上游能力尚未发布导致目前不能归档的 INFO，以及 2 条调研 skip_specs INFO，不为清除提示改写规范。
- `git diff --check`：退出码 0。
- 引用检查：7 个 Schema 的全部 $ref 必须在本地权威资产中解析到存在的 JSON Pointer；目录逐字段 value_shape 与公共 fact_node 条件分支一致。
- 契约反例检查：拒绝旧用户版本字段、旧解析输入、构造直接响应、以 Response 作为 StoredRecord.batch、丢失必要依据、递归 child、未授权来源引用、重复身份、失效来源和不满足却标为 satisfied。
- 本仓库尚无产品测试入口；本轮可执行验证为上述设计资产全量检查和 OpenSpec 校验，不把没有产品测试解释为组件通过。

## 交付与剩余门槛

| 交付 | 当前状态 |
| --- | --- |
| 目录、查询、公共中间、响应 Schema 及说明/样例/设计资产校验 | 已交付，通过上述检查 |
| 构造器开发期实际信息需求清单 | pending；validation/information-needs.json 是合成结构样例，不是实际需求清单 |
| 矩阵、工具研究、解析开发接入验收与点亮 | pending；空矩阵及点亮案例只验证契约，不是真实验收 |
| 归纳、构造、SQLite 仓库、查询、包装 | pending；repository 仅已有 design/tasks，其余缺失工件由各自子流程处理 |
| 同源运行时接口一致性（主8.4）、真实 S1–S12/补充场景集成（主8.1–8.3） | pending；不能用本次样例和校验器代替 |

主设计资产验证只验证提供的数据形状、离线引用和代表性跨字段一致性。实际授权边界、当前源码内容真实性、工具执行纯度/受控权限、覆盖充分性、前提失效传播及预算/无进展循环，必须由各子组件及主集成用真实入口验证。机器数据中的声明和证据定位本身不构成软件语义正确性的证明。
