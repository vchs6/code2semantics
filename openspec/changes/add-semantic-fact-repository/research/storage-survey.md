# SFRS 存储设计调研纪要（任务 3.1，有限调研一次成稿）

调研时间：2026-10-24。范围：design Open Questions 1–4。每项二手源 ≤2（调研有度规则）；未决项按最保守可选方案固化并标注。

## OQ1 存储布局与索引结构

**源**：GraphQLite 数据库 schema 参考（https://colliery-io.github.io/graphqlite/latest/reference/database-schema.html ）；SQLite EAV 查询与索引实践（https://sqlite.work/optimizing-fts-indexes-b-tree-depth-and-eav-model-queries-in-sqlite/ ）。

**结论**：三表实体粒度布局（entities / attributes / relations），属性为 EAV 行（entity_id, name, value）；覆盖索引 `(key, value, entity_id)` 模式支撑按属性过滤与按实体取回；建库用 `CREATE TABLE IF NOT EXISTS`（幂等）；关系表建 `(from_entity)` 与 `(to_entity, relation_type)` 双向索引支撑遍历。多属性 AND 过滤用 INTERSECT 而非自连接（SQLite 每表单索引限制）。

## OQ2 实体稳定标识机制

**源**：OmniGraph stable-schema-identity RFC（https://bitfreedom.net/code/apunkt/omnigraph/raw/branch/main/docs/rfcs/0028-stable-schema-identity.md ）；OrpheusDB 版本化论文（https://ar5iv.labs.arxiv.org/html/1703.02475 ）。

**结论**：业界共识与既有红线一致——**实体身份由权威提交方给定，存储层不自行从名称/路径推导身份**。OrpheusDB 的记录不可变 + 记录-版本多对多模型确认"事实不可变、随版本演进"可行。固化：Skill 提交流程承担身份判定（红线不放宽）；回填前仓库以 `(事实类型:文件:行号范围)` 作确定性占位标识（与查询侧 entity_id 同构），显式标注为保守方案；仓库仅校验同 ID 结构一致性（同 ID 同内容幂等、不同内容判版本冲突）。

## OQ3 版本保留策略与未指明版本语义

**源**：OrpheusDB（版本长期保留、版本图元数据）；Schema Versioning 综述（https://www.worldscientific.com/doi/10.1142/S2972370124300024 ，保留全部版本防信息丢失）。

**结论**（保守固化）：历史版本**长期保留、不清理**——单写者本地场景数据量小，清理策略无当前需求支撑；检索接口要求**显式版本参数**，不设"未指明版本"缺省语义（缺版本即参数校验错误，最保守——查询侧编排器总是先解析出真实版本再调用，不依赖仓库缺省）。

## OQ4 仓库数据落盘位置

**源**：GraphQLite（SQLite 嵌入单文件形态）；SQLite 官方文档（单文件数据库）。

**结论**（保守固化）：单文件 SQLite 数据库，位置经环境变量 `SFRS_DB_PATH` 指定；缺省 `~/.atomcode/sfrs/facts.db`（用户配置目录下，独立于项目代码、不进 Skill 安装包、不入 git 管理）。缺省位置为保守可选方案，显式标注待真实使用反馈后回顾。

## 调研差距（止损记录）

- 多属性复合过滤的性能优化（INTERSECT vs 物化视图）：当前单写者小数据量无压力，未做基准测试，记为后续按需项。
- 实体稳定标识的 Skill 侧生成机制（如符号签名哈希）：属 Skill 提取流程职责，超出本变更边界，待 Skill 侧提案处理。
