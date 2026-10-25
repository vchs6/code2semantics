# Proposal

## Why

构造器阶段三的归纳触发判定为事实类型级：只要该类型已产出任何事实即整类型跳过（`fact_type in facts` 即 continue）。对"部分字段工具直出、部分字段纯归纳"的混合形态事实类型（如 模块间依赖：`direction` 由 use 声明直出、`type` 为纯归纳字段），纯归纳字段永远不触发归纳请求，只能以 null 落盘并进字段级 gap——实测 indicatif 项目一次查询产生 102 条重复的 `模块间依赖.type` 字段级 gap。用户裁决（2026-10-25）：不做字段级逐字段触发，应以"一组待取值"为整体触发。

## What Changes

- 构造器归纳触发判定从"事实类型整体缺失"扩展为"事实类型存在待取值集合"：类型已产出事实时，仍盘点其归因字段中值为空的待取值字段集合，非空即触发归纳。
- 归纳请求以事实类型为单位、以待取值字段集合为一组整体下发（`fields` 为整组待归纳字段），MUST NOT 逐字段拆分为多条请求。
- 归纳方整组返回后，构造器整组校验并回填到对应实体的空字段；回填成功的字段不再进 gaps，未回填的字段保持既有字段级 gap 语义。
- 既有"整类型无工具直出数据项"的归纳触发路径保持不变；本变更为其覆盖不足的混合形态补齐同一批量归纳通道。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `semantic-fact-constructor`: 修改"语义归纳的请求与并入"需求——归纳触发条件从"无工具直出数据项的缺失事实类型"扩展为"存在待取值集合的事实类型（含类型有产出但归纳字段空缺的混合形态）"，并新增"待取值整组触发、整组返回回填"的行为要求。

## Impact

- 代码：`.atomcode/skills/layered-semantic-facts/scripts/constructor/constructor.py`（阶段三触发判定与归纳回填）、`synthesis.py`（待取值字段盘点所依赖的归纳字段标记，已有 `FIELD_INFO_NEEDS`/unmappable 机制）。
- 输出契约：`induction_requests` 结构不变（`type` + `fields` 列表 + `guidance`），语义扩展为"待取值组"；output-schema 无结构变更，validate 应继续通过。
- 测试：`scripts/constructor/tests/`、`scripts/tests/test_orchestrator_induction.py` 新增混合形态用例；既有整类型缺失用例行为不变。
- 依赖：无新增外部依赖；不涉及 Skill 目录布局与 frontmatter（不触发原则 9 对齐验收）。
