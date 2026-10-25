# Tasks

> 设计阶段顺序仅有：fact-catalog → 查询契约 → 响应契约（config 规则）；随后 Skill 骨架与两种模式实现。事实集需求调研为独立变更（epic 开始前已完成），本清单只消费其产物，不重复执行调研；调研重入取决于报告不存在或有强制要求。

## 1. 消费事实集需求清单（不重新调研）

- [x] 1.1 复核 `../../survey-semantic-fact-requirements/research/semantic-fact-requirements.md` 与本变更 spec 的一致性（封闭世界目录、gaps 与"超出范围"分列、最小化裁剪），差异与取舍记录在 epic 变更目录。验证：核对结论有记录，未发现未处理的冲突

## 2. 分层语义事实模型（fact-catalog）

- [x] 2.1 以事实集需求清单为蓝本，编写 `skills/layered-semantic-facts/references/fact-catalog.md`：分层事实模型（层级采用清单论证的四层：项目→模块→符号→事实）、可查询事实类型与字段清单、语言无关语义词汇表初版、证据定位格式（文件:行号范围）。验证：目录层级与清单一致，覆盖契约查询模式规范引用的全部语义层

## 3. 查询契约（contract-format）

- [x] 3.1 基于 fact-catalog 编写 `references/contract-format.md`：查询契约 JSON 结构（`project`、`facts` 各层与字段描述）、校验规则（含"契约引用事实 MUST 属于可提供事实目录，目录外引用判为超出范围"）、项目位置缺省处理示例。验证：契约可引用集与 fact-catalog 完全一致，含一个可模仿的完整契约示例

## 4. 最小事实集响应契约（output-schema）

- [x] 4.1 基于 fact-catalog 编写 `references/output-schema.md`：机器可读 JSON 事实集 schema（分层结构、字段、gaps 声明格式、"超出范围"声明格式、证据定位字段）。验证：schema 能表达规范中"最小化""显式缺口"与"可提供事实目录"三个 Requirement 的全部场景，与阶段 6 的 report-template 可互相对照

## 5. Skill 骨架与契约查询执行流程

- [x] 5.1 创建 `skills/layered-semantic-facts/SKILL.md`：frontmatter（name、description 触发词覆盖两种模式）+ 模式路由（对话派生 → 契约查询）+ 硬性规则（项目位置缺省为宿主当前工作目录、输出前最小化裁剪、gaps 不编造、目录外引用判超出范围、意图不明先澄清）。验证：文件存在，frontmatter 可被宿主解析
- [x] 5.2 按当前开发宿主（AtomCode）接入本地测试：符号链接 `skills/layered-semantic-facts/` 到 `.atomcode/skills/layered-semantic-facts`（目标内容不重复提交；其他代理环境按各自技能安装机制接入，Skill 本体不变）。验证：宿主重新加载技能目录后技能可被发现
- [x] 5.3 在 SKILL.md 写契约查询模式的执行流程：契约校验（含目录外引用判"超出范围"）→ 分层渐进提取（先项目层，按契约决定是否下钻）→ 按需子代理并行 → 输出前统一裁剪。验证：流程覆盖 `semantic-fact-query` 规范 5 个 Requirement 的每条路径，提取依据为 fact-catalog 的事实类型与字段定义
- [x] 5.4 在本仓库（语言无关的 markdown 项目）上手工执行一次契约查询：契约只要求项目层事实。验证：输出仅含项目层，每条事实带真实证据定位，未要求的层不出现

## 6. 对话派生模式（query-contract-derivation）

- [x] 6.1 在 SKILL.md 写对话派生模式流程：意图识别 → 契约提取（含项目位置缺省补全）→ 意图不足时按 fact-catalog 列出可选事实类型与澄清问题清单 → 调用契约查询模式 → 从事实集渲染人可读 Markdown 报告。验证：流程含澄清时机的明确判定条件，报告被明确要求从事实集生成（单一事实源）
- [x] 6.2 编写参考文件 `references/report-template.md`：人可读报告的分层结构模板与证据标注格式。验证：模板能呈现 output-schema 中每一字段，两种输出可互相对照

## 7. 集成验证

- [x] 7.1 端到端演练对话派生模式：在只说模糊意图（不指明所需事实）的对话中触发技能，确认其先按 fact-catalog 澄清而非直接产出；再给出完整意图（不含项目位置），确认缺省补全与报告生成。验证：两次演练行为分别符合 `query-contract-derivation` 规范的"意图不明时的澄清"与"项目位置缺省补全"场景
- [x] 7.2 运行 `openspec validate` 确认全部产物有效；对照两个 spec 逐条核对 SKILL.md 与参考文件无冲突表述。验证：validate 通过（或 --strict 下无 error 级问题），核对结论记录在变更目录

## 8. 重入（2026-10-22 上游事实清单全面重研）

- [x] 8.1 （重入 2026-10-22，上游事实清单全面重研构成强制要求）按重研后清单（基准日期 2026-10-22）重新完成阶段 1–2 与任务 5.4：重做一致性复核、同步 fact-catalog、重跑手工契约查询。验证：核对结论与查询输出落盘 `recheck-2026-10-22.md`，fact-catalog 与清单一致，validate 通过
  - 执行结论：fact-catalog 同步"构建与运行形态""意图声明"两类新事实类型；contract-format/output-schema/report-template/SKILL.md/两 spec 经逐项核对均无需修订（层级与字段以 fact-catalog 为准）；5.4 手工契约查询重跑通过；任务 7.1 涉及运行时交互行为且 SKILL/spec 未变，原结论继续有效。

## Workflow follow-up

- 全部任务完成后，按项目评审要求归档本变更（`/opsx-archive`）。
- 归档后确认主规范（openspec/specs/）生成正确。
