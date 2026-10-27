# CodeGraph Explorer：真实项目评测与分析报告

**评测时间：** 2026-10-27  
**评测状态：** 结构化信息获取候选；**未获得生产接入验收**  
**Skill/构建脚本来源：** [GoldDHacker/codegraph-explorer-skill](https://github.com/GoldDHacker/codegraph-explorer-skill)  
**固定代码版本：** `6a95e4f0ae643fad7354ac388ceaa2dc2c2f3f74`  
**机器可读结果：** [codegraph-explorer.results.json](codegraph-explorer.results.json)

## 1. 目标与被测对象

检验其脚本式代码解析能否在**真实 Rust / Python 项目**中较低成本生成可查询的结构化项目信息，以及关系类型、源码位置、图谱规模、增量更新和来源有效性方面的限制。评测**不是**检验 Skill 直接生成语言无关语义事实，因为 F1–F18 事实由项目的统一构造器与证据验证流程负责。Skill 原始图谱只作为候选来源信息。

固定真实项目：
- [Rust Dashu（cmpute/dashu）](https://github.com/cmpute/dashu/tree/a0fc5358a3335e9fce155c5ddf8ae7ca83f24a33) — 提交 `a0fc5358a3335e9fce155c5ddf8ae7ca83f24a33`。
- [Python Click（pallets/click）](https://github.com/pallets/click/tree/2247b35ea1c47c727d7a06e51fa280e12a863ff6) — 提交 `2247b35ea1c47c727d7a06e51fa280e12a863ff6`。

执行条件：GitHub Actions `ubuntu-latest` / Python 3.12，临时独立 Git 检出，直接运行固定版本 `scripts/codegraph_builder.py` 及 `--callers ... --json`；**未启动 Skill 宿主、未执行被分析项目的编译/测试，不安装其可选 Tree-sitter 语法包**。这意味着结果可能与启用 Tree-sitter 的候选输出不同。

## 2. 实测结果

| 项目 | Dashu（Rust 为主） | Click（Python） |
|---|---:|---:|
| 检出文件总数（不含 .git） | 564 | 178 |
| Rust / Python 文件数 | 393 / 20 | 0 / 91 |
| 候选脚本发现文件数 | 521 | 141 |
| 完整建图墙钟时间 | **3.4667 秒** | **1.5793 秒** |
| `graph.json` 字节数 | 43,946,741（约 43.9 MB） | 21,004,684（约 21.0 MB） |
| 节点数 | 7,771 | 2,924 |
| 边数 | 155,397 | 73,733 |
| `contains` / `calls` 边 | 7,250 / 148,147 | 2,783 / 70,868 |
| `inherits` 边 | 未出现 | 82 |
| `INFERRED` 标记 | 145,714（约 93.8%） | 70,147（约 95.1%） |
| `RESOLVED` / `EXTRACTED` 标记 | 2,457 / 7,226 | 721 / 2,865 |
| 带源码位置的节点数 | 7,250 | 2,783 |
| 悬空图边 | 0 | 0 |
| `--callers` 结构化 JSON 查询 | 10 次成功 | 10 次成功 |
| 平均查询耗时 | 0.3832 秒 | 0.2195 秒 |
| 单次源码编辑后 `--update` 耗时 | 3.0438 秒 | 1.2194 秒 |

**证据：** [真实仓库 CI Run 40443798396](https://github.com/vchs6/code2semantics/actions/runs/40443798396)，Artifacts 名称 `codegraph-real-project-results`。上述汇总固化在仓库，即使 Artifact 过期仍可使用历史结论。完整图谱未提交：它们体积较大、版本和工作目录相关、还未通过事实质量验收。

## 3. 真实项目中的专项缺陷：mtime 不变但源码改变

在上述两项目的临时检出中，先让图缓存与源文件状态同步，再为一个 Python 源文件新增可识别函数，使用 `os.utime` 恢复文件先前的修改时间，并运行 `--update`。

| 项目 | 更新命令状态 | 重新解析的文件 | 新函数是否进入图 |
|---|---|---:|---|
| Dashu（仓库内 Python 辅助脚本） | 退出码 0 | 0 | **否** |
| Click（`docs/conf.py`） | 退出码 0 | 0 | **否** |

**证据：** [专项 CI Run 40444104829](https://github.com/vchs6/code2semantics/actions/runs/40444104829)；相关脚本 `scripts/research/evaluate_codegraph_real_projects.py`。

**结论：** 现有候选的增量更新成功状态不足以保证来源新鲜度；仅凭 mtime 或已有 `graph.json` 不能把关系当成当前有效信息。后续如接入，必须基于授权源码内容指纹检查新鲜度，必要时重建或拒绝陈旧缓存。该问题在两个真实项目中复现，而不是单纯的理论风险。

## 4. 质量与成本分析

- **结构化获取能力：初步证实。** 一次扫描能返回文件、函数、导入、类型、调用候选等结构和关系，后续可以返回局部 JSON 查询结果。
- **时间开销：这两份真实仓库中较低。** 但单次 CI 时间不能推导大型复杂仓库 SLA；首次图构建与增量更新均不是零成本。
- **模型 Token：直接本地脚本步骤为零模型调用。** 并不代表 Skill 宿主说明加载、编排、后续推理或全部生产链成本为零。
- **推断边：关键风险。** 两个真实图谱的关系边大部分是 `INFERRED` 标签；**这不等于它们全是错误边**，但在缺乏逐边证据核验、跨语言关系准确率和独立工具对照前，不能将边数当作语义信息的有效覆盖率。
- **与普通工具的比较：未完成。** 尚未以同一固定信息需求、相同质量标准对比已验收工具组合的覆盖、调用次数和总成本；不能据此认定 Skill 优于或不劣于普通工具。
- **多语言能力：仅证明同一仓库可出现多语言节点。** 尚未证明 Python↔Rust FFI/RPC 等跨语言真实交互。
- **事实转换：未通过生产验收。** 暂无已验收适配将图谱结果转成带充分证据、来源指纹、冲突与未知标记的统一信息，再由构造器构建 F1–F18。

## 5. 结论与选择规则

**当前保留 CodeGraph Explorer 为候选结构化信息获取手段，不点亮生产能力矩阵。**

对于一次性需要多类项目信息的请求，可以将其一次建图、多次局部查询的效率纳入选择器成本估计；与普通工具处于同层候选，不要求 Skill 自身产出 FactBatch。但必须先验证输出的信息质量，修正或屏蔽 mtime 缓存过期的风险，并按请求/项目信息需求与普通工具进行等价质量对照。

这是**带版本和证据的历史评测结论**：以后若被测的工具、项目提交与验收口径不变，查本报告即可，不必每次重跑。若源码/工具变了，只需补测受影响点，原历史记录保留。

## 6. 可复现入口

- 实仓测试：`scripts/research/evaluate_codegraph_real_projects.py` 与 `.github/workflows/evaluate-codegraph-real-projects.yml`。
- 合成规模、重复查询、关系正反例、增量删除：`scripts/research/evaluate_codegraph_skill.py` 与 `.github/workflows/evaluate-codegraph-skill.yml`。
- 合成测试成功日志：[CI Run 40443411991](https://github.com/vchs6/code2semantics/actions/runs/40443411991)。
- 机器可读历史结果：[JSON 摘要](codegraph-explorer.results.json)。
