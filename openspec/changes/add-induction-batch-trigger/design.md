# Design

## Context

构造器阶段三（`scripts/constructor/constructor.py:121-155`）的归纳触发判定为事实类型级：`if fact_type in facts: continue`——类型已产出任何事实即整类型跳过。归纳字段标记机制已存在：`synthesis.py` 的 `FIELD_INFO_NEEDS` 将纯归纳字段标注为"归纳"信息需求并纳入 unmappable 差距段（`synthesis.py:153-164`）。实测（indicatif，版本 a65379f）：模块间依赖类型由 grep 解析器直出 `direction`（102 条 use 声明），`type` 字段全部为空，未触发归纳，产生 102 条重复字段级 gap。动机与行为语义见 proposal.md，需求见 `specs/semantic-fact-constructor/spec.md` delta。

## Goals / Non-Goals

**Goals:**

- 归纳触发判定从"事实类型整体缺失"扩展为"事实类型存在待取值集合"，覆盖混合形态（类型有产出但归纳字段空缺）。
- 待取值集合以事实类型为单位整组触发、整组返回、整组回填；不逐字段拆分。
- 既有"整类型缺失"归纳路径行为不变（回归保障）。

**Non-Goals:**

- 不改变 `induction_requests` 输出结构（`type` + `fields` + `guidance`）与 output-schema。
- 不为 `type` 这类归纳字段新增工具直出生产者，不修改能力矩阵（矩阵生产者列与生产者选型策略不变）。
- 不处理字段级 gap 的呈现去重/聚合（那是输出呈现优化，属另一潜在变更）。

## Decisions

### 决策 1：待取值盘点的数据来源用既有 `FIELD_INFO_NEEDS` 归纳标记，不新增标记机制

待取值字段集合 = 该事实类型在 `FIELD_INFO_NEEDS` 中标记为归纳（info_need 命中 unmappable 前缀表）的字段中，本轮构造产出实体里值为空的字段的并集。确定性：`derive_info_needs` 与 unmappable 派生均为纯函数（`synthesis.py:122-166`），同一构造输入产出相同待取值集合，满足原则 7（实现形态：Python 脚本，pytest 场景覆盖验证）。

被否备选：在 fact-catalog 或矩阵中新增"归纳字段"标注——需要同步修改两份配置并引入第二真相源，与 `FIELD_INFO_NEEDS` 已有标记重复；否。

（依据：proposal「What Changes」第 1 条；在盘事实 `synthesis.py:22-52`）

### 决策 2：触发判定改造为两分支共用同一整组通道，混合形态在类型已有事实时补充盘点

阶段三逻辑改为：对每个请求类型，(a) 类型不在 facts 中 → 既有路径（生产者盘点 + 整类型请求）；(b) 类型在 facts 中且存在已点亮归纳类生产者 → 盘点决策 1 的待取值字段集合，非空则追加一条该类型的归纳请求。两分支产出的请求统一进入既有 inducer 调用与契约校验通道。

被否备选 A：逐字段触发（每空字段一条请求）——用户裁决否决（2026-10-25）：不做字段级逐字段触发，应以一组待取值整体触发；否。
被否备选 B：合成阶段把纯归纳字段为空的实体判为"部分缺失"重新走整类型构造——会把已直出的 direction 数据项一并重跑，违反"仅构造缺失部分"（proposal What Changes 与设计原则"先查库、仅构造缺失"）；否。

（依据：proposal「What Changes」第 1、2 条；用户裁决记忆 2026-10-25）

### 决策 3：归纳返回按（事实类型 → 字段值组）回填到既有实体空字段

inducer 返回中该类型的条目经既有目录校验（`constructor.py:144-146` 的拒收逻辑不变）后，将字段值回填到该类型已产出实体中对应空字段；回填按实体证据归属（归纳返回若带实体级条目则匹配，仅字段组则填充全部同名字段空位）。回填成功的字段不再进 coverage 判缺（字段已有值，`coverage.py:82` 跳过逻辑自然生效）；未回填字段维持既有字段级 gap。

被否备选：把归纳返回作为新实体追加（既有 `facts.setdefault(...).append` 路径）——会为同一批实体产生重复事实条目，破坏"每条依赖一条实体、证据绑定"的粒度；否。

（依据：proposal「What Changes」第 3 条；spec delta Scenario「整组返回回填实体空字段」）

### 决策 4：`guidance` 取该类型既有 `required_info`，不按字段拼接新文本

`need_by_fact_type.get(fact_type)` 的 required_info 已覆盖该类型全部字段的信息需求描述（`synthesis.py` 派生表），整组请求沿用，保持请求结构与既有消费方（运行 Skill 的代理）兼容。

被否备选：按待取值字段子集动态拼接 guidance——引入新的文本组装逻辑且无调研支撑其必要性；否，列为实现时如发现 guidance 粒度不足再回填 Open Questions。

（依据：proposal「Impact」output 契约不变承诺）

## Risks / Trade-offs

- [混合形态盘点引入额外遍历成本] → 待取值盘点仅在类型被请求且已有事实时执行一次，字段集来自常量表，成本 O(类型数 × 字段数)，可忽略。
- [归纳返回实体级条目与既有实体匹配失败] → 匹配不到的返回值不静默丢弃，未回填字段保持字段级 gap 显式暴露（spec delta Scenario「未覆盖请求与未回填字段保持显式」）。
- [与 add-semantic-fact-constructor 未归档 delta 的归档顺序] → 本变更 delta 基于其"语义归纳的请求与并入"需求块整块修改；若上游 delta 在本变更归档前有实质修订，须按原则 8 一致性回溯核对后重放本 delta。

## Open Questions

- 无阻塞性未知项；决策 4 的 guidance 粒度若实测不足，回填后再议，不影响 spec 与任务分解。
