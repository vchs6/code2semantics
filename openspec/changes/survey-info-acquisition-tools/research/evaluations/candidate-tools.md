# 普通项目分析工具：环境探测与结构化信息能力报告

**评测日期：** 2026-10-26（已执行 CI 环境探测）；归档日期 2026-10-27。  
**结果来源：** [CI Run 40319334019](https://github.com/vchs6/code2semantics/actions/runs/40319334019)。  
**测试脚本：** `scripts/research/probe_candidate_tools.py`。  
**环境：** GitHub Actions Ubuntu 24.04，Python 3.12.15；结果**只代表当次 CI 环境**，不是用户电脑或生产宿主的实时安装状态。

## 1. 已执行的可用性与样例探测

| 候选普通工具 | 当次环境及样例执行结果 | 结构化信息价值 | 本次验证边界 |
|---|---|---|---|
| Python / 标准库解析能力 | Python 3.12.15，版本探测成功 | Python AST/符号清单可以作为源码信息获取基线 | 版本存在 ≠ 完整项目语义关系 |
| `python -m compileall` | 临时 Python 文件成功编译，退出码 0 | 语法、编译诊断 | 并非节点、调用关系或 FactBatch 输出；不单独视为结构化语义获取者 |
| `cargo` | Cargo 1.99.0；`cargo metadata --no-deps --format-version 1` 在最小临时项目成功，输出有效 JSON，含 package/target/workspace/member/manifest 信息 | Rust 构建单元、项目边界、工作空间与包元数据 | 不证明代码执行、跨 crate 动态交互；仅临时 Cargo 项目样例 |
| `rustc` | rustc 1.99.0，版本探测成功 | 后续可供编译/类型检查方案研究 | 本次**未执行编译/类型检查样例** |
| `rust-analyzer` | 存在 shim/路径，但 `--version` 失败，提示官方工具链中没有对应可执行二进制，退出码 1 | Rust 语义/符号解析的潜在候选 | **本次环境不可用**，不得仅凭命令路径计为可用 |
| `universal-ctags` | 未发现可执行文件 | 多语言符号索引的潜在候选 | 未实测输出 |
| `ast-grep` | 未发现可执行文件 | 结构化模式/语法树检索的潜在候选 | 未实测输出 |
| `tree-sitter` CLI | 未发现可执行文件 | 多语言增量结构解析的潜在候选 | 未实测 CLI 输出；不代表其他程序内嵌 Tree-sitter 不存在 |

本报告是**已经观察到的测试结果**。其中“未安装”特指该 GitHub CI 环境，并非对候选工具本身的否定。普通工具的逐信息项映射和环境限制见 [总调研报告](../semantic-tooling-survey.md) 第 7 节。

## 2. 可复用分析结论

工具与独立项目分析类 Skill 应当作为同级结构化信息获取候选，根据固定信息需求选型。普通工具具有细粒度、按需执行的优势；Skill 在一次分析返回多类项目信息与可复用图谱方面可能有优势。当前没有完成两者在**相同需求与相同证据质量**下的总成本对照，因此本探测不得被视为“普通工具一定更优”或“Skill 一定更优”。

`cargo metadata` 的 JSON 结构在当前夹具已验证，适合 Rust package/workspace/target 声明类信息；它的 package 声明、逻辑依赖与真实运行调用应区分。后续源信息仍须携带来源内容状态、项目授权范围和证据定位，才能进入统一规范化和语义事实构造器。

当工具版本、平台、配置、测试项或信息需求没有变化时，**优先读取本报告作为已有测试记录，不需要无条件重新执行环境探测**。判断当前机器是否安装某工具、目前版本是否兼容，仍需要当前环境检查；对于新增需求/升级版本，只补测受影响项。

## 3. 可复现与后续补测

- 探测脚本：`scripts/research/probe_candidate_tools.py`。
- 运行命令：`python scripts/research/probe_candidate_tools.py`。
- 历史成功 CI：[40319334019](https://github.com/vchs6/code2semantics/actions/runs/40319334019)。
- 原始环境的详细输出以该 CI 日志为准；本目录另存可复用的观测摘要：[candidate-tools.results.json](candidate-tools.results.json)。
- 本轮缺少真实 Rust/Python 项目的**直接工具与 Skill 同需求对照**；应以固定项目提交和固定信息需求进行增量补测，而不是重复已经验证的环境存在性。
