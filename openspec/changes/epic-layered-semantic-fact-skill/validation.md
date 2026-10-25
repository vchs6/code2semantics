# 设计工件验证记录

验证日期：2026-10-25。本轮仅研究消费、主spec/design/tasks和必要契约；未创建产品scripts、tests、SKILL.md，未执行产品实现、安装或真实生产。其它变更的proposal/specs及openspec/config.yaml未修改。

## 已执行

环境：Python解释器 `C:/Users/vchs6/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`；`PYTHONUTF8=1`；`PYTHONPATH=C:/Users/vchs6/.codex/tmp/code2semantics-python-deps`。

```powershell
python openspec/changes/epic-layered-semantic-fact-skill/validation/validate_contracts.py
```

结果：7份JSONSchema自身校验及本地引用解析通过；32正例接受、20反例拒绝；目录18项F，4种粒度与5种组织职责；研究UTF-8/LF规范化摘要一致。来源性质×知识状态18种组合均有正例，覆盖字段投影信封、否定必要条件、多来源快照、关键候选配对、带目标缺口及精确/refresh请求形状。

```powershell
node C:/Users/vchs6/.codex/tmp/survey-openspec-runtime/node_modules/@fission-ai/openspec/bin/openspec.js validate epic-layered-semantic-fact-skill --strict --json
```

结果：valid=true，issues=[]，1 passed / 0 failed。

## 可复现数据与边界

validation/schema-cases.json列出fixture和确定性patch，每个案例有明确接受/拒绝预期；validate_contracts.py只验证设计资产，不包含运行期产品实现。

validation/semantic-cases.json含8项结构合法但应被运行语义校验拒绝的案例：不存在主体、跨来源版本、前提修订缺失、未请求字段、否定域错误、否定证据缺失、前提内容泄漏、快照集合摘要错误。本轮仅确认这些例子结构合法，未宣称其语义程序已经实现。任务7负责真实拒绝验证。

初次独立审查的3项Important已在当前工件内最小纠正：关键引用字段采用共享shape，selector/gap携带目标，精确revision只读而显式refresh允许同快照新知识；对应spec、D2/D3/D6、任务6/7/10、schema正反例均同步。信息需求need_id固定F.field，Observation信息需求引用由语义校验核对。

OpenSpec apply当前记录3/46完成，43项产品任务待执行；完成的是已落盘并验证的目录、查询、响应/公共契约资产。仅“planning complete”不代表产品完成。表达结构验证、生产能力与运行验证分开报告；生产状态全部unverified。主提案逐项追踪见traceability.md。

安装及Agent Skills符合性验证仍在任务11：当前assets/references符合约定目录分工，但尚无可安装Skill入口，不宣称官方skills-ref已运行。
