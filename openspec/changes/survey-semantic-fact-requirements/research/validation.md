# 本轮执行与验收记录

- 日期：2026-10-25；变更：survey-semantic-fact-requirements。
- 仓库基线：`dd0b368f4f70859e523a2f5b0c4ffbfa79635e50`。
- 范围：design.md、tasks.md、research/semantic-fact-requirements.md 与本记录；proposal、config、skip_specs 和产品代码不变。
- 用户已确认本轮 design/tasks 修订草案并授权继续报告、验证及 GitHub 提交；没有归档授权。
- 本记录最后由实际最终命令输出复核；任务进度须以末次 apply 输出为准。

## 1. 工作流证据

1. 读取仓库 AGENTS.md、OpenSpec config、project（正文为注释）、该变更所有工件与旧研究；核查另外两份 research 报告、docs 参考研究及下游 catalog/epic。
2. 读取仓库 OpenSpec apply/update 技能。OpenSpec 1.14.3 的 list/status/instructions 确认 root、spec-driven、specs skipped。基线 apply 为旧任务 6/6 all_done，基线 strict 亦通过，说明二者不能代替新需求的内容验收。
3. 按仓库 update 技能及 AGENTS 8.3 展示修订草案，收到用户确认。先取得 design 指令并定稿，再刷新 tasks 指令生成本轮七项任务；apply 进度变为 6/13。
4. 使用 Superpowers 官方 [using-superpowers](https://github.com/obra/superpowers/blob/main/skills/using-superpowers/SKILL.md)、[verification-before-completion](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md) 的技能先读、证据先行原则，并参考 [executing-plans](https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md) 的按任务执行及独立整体复核。本轮为既有 proposal 的纯调研执行，计划由仓库 OpenSpec tasks 承载，不新建产品代码或另一套实施计划。
5. 七项新任务逐项按照 apply 的 sourcePath/line 更新；每次完成后刷新进度，前六项完成后为 12/13。末项待本记录和集成验收完成才勾选。
6. 独立只读审查覆盖 proposal、设计、报告、任务及边界；发现一项 P2：S10 将版本声明与解析内容差异一律视为冲突。已改为先核对快照/配置/显式替换规则，合法替换保留两者，仅同上下文约束矛盾才标冲突。审查未发现其他实质需求遗漏；审查时本验收记录尚未生成，其验证主张由末次命令核实。

官方技能并未安装进仓库或修改用户配置。技能参考不覆盖仓库对工件指令、确认和任务派生的强制规则。

## 2. 实际校验结果

环境：Windows，Node.js 24.22.1，OpenSpec 1.14.3，Python 3。OpenSpec 安装在独立临时工具目录，实际以 `node <工具目录>/bin/openspec.js` 调用；下列 `openspec` 是相同 CLI 的简写，不是模拟结果。

| 检查 | 结果与范围 |
|---|---|
| `openspec validate survey-semantic-fact-requirements --strict --json` | 1 passed、0 failed；无 ERROR/WARNING。保留 1 条 INFO：skip_specs 允许零 delta |
| `openspec validate --all --strict --json` | 10 passed、0 failed；扫描 10 个 active change、0 个主 spec。不等于十个变更已完成内容验收或可归档 |
| 报告确定性检查（本记录 §3） | 13 项原始需求、32 类事实、7 个来源、5 个视图、10 个场景；50 个场景维度非空；报告与 design 的 11 条局部文件链接存在；本轮与历史共 13 个任务标记 |
| `git diff --check` | 通过；无补丁空白错误。Git 的 LF/CRLF 自动转换提示不属于内容错误 |
| proposal 逐条一致性 | 报告 §11 的九行回溯，独立复核无其他实质遗漏；层级推导可回到 §3/§4，关系与证据不受唯一父子链限制 |
| 范围检查 | 仅上述四份文档；报告 §9 显式列出下游未适配，不修改契约或运行代码；未执行 archive |

中间失败与修复没有省略：旧报告缺少 R 编号的检查先失败；临时检查器曾把 V1—V5 误按两位编号匹配，已纠正；局部链接检查发现 design 的参考路径多退一级，已修正；strict 发现本轮 7.x 编号处于第 2 组，已规范为 2.1—2.7；补丁检查发现末尾多余空行，已修正并重跑。最终结果不能由中间失败推断，以上表格以修复后的实际输出为据。

全库校验还保留既有 INFO：add-induction-batch-trigger 及 add-semantic-fact-query 的部分 delta 在归档时会因目标主 spec 不存在而被拒绝。这些属于既有归档上下文提示，本轮没有修改或归档这些变更。

## 3. 可复现的确定性内容检查

在仓库根目录，将下列 Python 检查保存到临时文件，运行 `python <临时文件> --final`。它检查存在性、编号集合、非空维度、引用和局部文件链接；不证明自然语言语义正确、外部来源支持力度或实际提取能力。语义判断的依据是报告 §11 和独立审查。

```python
from pathlib import Path
import re, json, sys
root = Path.cwd()
base = root / "openspec/changes/survey-semantic-fact-requirements"
report = (base / "research/semantic-fact-requirements.md").read_text(encoding="utf-8-sig")
checks = {}
def table_ids(prefix, n):
    rows = re.findall(r"^\| ("+prefix+r"\d{2})\b.*$", report, re.M)
    assert len(rows)==n and len(set(rows))==n, (prefix, len(rows), rows)
    assert set(rows)=={prefix+str(i).zfill(2) for i in range(1,n+1)}, prefix
    return rows
checks["requirements"] = len(table_ids("R",13))
checks["facts"] = len(table_ids("F",32))
checks["scenarios"] = len(table_ids("S",10))
views=re.findall(r"^\| (V[1-5])\b.*$", report, re.M)
assert len(views)==5 and len(set(views))==5, views
checks["views"] = len(views)
checks["sources"] = len(table_ids("E",7))
assert "2026-10-25" in report
for i in range(1,12):
    assert re.search(r"^## "+str(i)+r"\.",report,re.M), i
for line in report.splitlines():
    if re.match(r"^\| (R|F|S)\d{2}\b",line):
        cells=[x.strip() for x in line.strip("|").split("|")]
        assert all(cells), line
        if re.match(r"^\| S\d{2}\b",line):
            assert len(cells)==6, (len(cells), line)
            assert all(len(c)>10 for c in cells[1:]), line
for prefix,n in [("R",13),("F",32),("S",10),("V",5),("E",7)]:
    seen=set(re.findall(r"\b"+prefix+r"\d{2}\b",report))
    assert seen <= {prefix+str(i).zfill(2) for i in range(1,n+1)}, (prefix, seen)
links=[]
for rel in ["design.md","research/semantic-fact-requirements.md"]:
    path=base/rel
    text=path.read_text(encoding="utf-8-sig")
    for target in re.findall(r"\]\(([^)]+)\)",text):
        if "://" not in target and not target.startswith("#"):
            dest=(path.parent / target.split("#")[0]).resolve()
            if dest.name=="validation.md" and "--final" not in sys.argv: continue
            assert dest.is_file(), (path.name,target)
            links.append(str(dest.relative_to(root)))
checks["local_links"] = len(links)
assert "未运行源码提取器" in report and "不是对实际提取工具的运行测试" in report
assert "已证实不存在" in report and "互斥" in report
checks["nonempty_scenario_dimensions"] = 50
tasks=(base/"tasks.md").read_text(encoding="utf-8-sig")
boxes=re.findall(r"^- \[([ xX])\] ",tasks,re.M)
assert len(boxes)==13, len(boxes)
checks["tasks_complete"]=sum(x.lower()=="x" for x in boxes)
if "--final" in sys.argv:
    assert checks["tasks_complete"]==13
    assert (base/"research/validation.md").is_file()
checks["result"] = "PASS"
print(json.dumps(checks,ensure_ascii=False,indent=2))
```

预期核心输出：requirements=13、facts=32、scenarios=10、views=5、sources=7、local_links=11、nonempty_scenario_dimensions=50、tasks_complete=13、result=PASS。旧稿没有 R/F/S 编号集合，因此该检查不会把旧稿误判为本轮交付。

## 4. 局限与交接

- 十类场景是概念表达见证，不是实际源码、工具提取、性能或端到端测试。纯文档变更没有新增或修改生产代码，因此没有伪报运行时测试通过。
- 官方文档与论文的核实位置、日期、链接及下载失败替代记录在报告 §2；每个需求的外部佐证有界，不声称已验证所有生态。
- 报告完成不等于现有 Skill 已提供 32 类事实；fact-catalog、查询/输出契约及生产能力报告仍需按 epic 顺序适配，详见报告 §9/§10。
- 没有新增事实存储、自动发现或 ID 生成实现；也没有因概念关系可表达而指定数据库。
- 保持本变更未归档，交付文档提交供审阅；未合并主分支。
