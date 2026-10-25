# Tasks

> 调研产物 `research/semantic-fact-requirements.md` 尚未落盘（research/ 目录为空），本清单为**执行型**：执行调研、产出清单、逐项自查。

- [x] 1. 执行语义事实集需求调研：归纳软件项目语言无关的语义表达所需事实，经分析汇总确定分层结构（层级数量与名称是调研结论，不预设），逐层列出事实类型、语言无关语义词汇与字段描述。验证：分层论证成文
- [x] 2. 将清单写入 `research/semantic-fact-requirements.md`（中文，含基准日期 2026-10-21；含"语义表达中的作用"论证节）。验证：文件存在且含全部事实类型
- [x] 3. 自查清单与 proposal/design 边界一致：无生产能力判定、无契约结构定义等越界内容。验证：越界检查结论有记录
- [x] 4. 运行 `openspec validate` 确认本变更产物有效。验证：validate 通过（或 --strict 下无 error 级问题）
- [x] 5. （重入 2026-10-22，proposal 修改构成强制要求）依据 proposal 新增的表达要求补充"使用契约"事实类型（调用前置条件、参数约束、返回保证）至清单事实层，并同步下游 fact-catalog。验证：清单与 fact-catalog 均含使用契约类型，validate 通过

- [x] 6. （重入 2026-10-22，用户明确指示全面重研）从零重新执行语义事实集需求调研：重新归纳事实需求与分析分层（可推翻现有四层结论），更新基准日期为 2026-10-22，重写清单正文并记录越界自查结论；若清单相对旧版有实质变化，同步下游 `skills/layered-semantic-facts/references/fact-catalog.md`。验证：清单落盘且分层论证成文，validate 通过，fact-catalog 同步结论有记录
  - 执行结论（2026-10-22）：重研独立再推导，四层收敛一致；实质变化为项目层新增"构建与运行形态"、符号层新增"意图声明"、事实层重组为 A/B 两组。fact-catalog 已同步上述三项；越界自查结论记录于清单末节；openspec validate --strict 通过（4 passed, 0 failed）。

## Workflow follow-up

- 本变更为 epic `epic-layered-semantic-fact-skill` 的前置输入（config 规则：epic 开始前需先完成本调研），随 epic 评审要求一并归档。
