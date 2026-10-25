# 调研验收记录

验收对象：同目录 `semantic-fact-requirements.md`。依据：当前 `../proposal.md` 与 `../design.md`。日期：2026-10-25。

结论：报告内容自审与机械验证通过，交接方继续独立验收。通过仅指需求研究交付，不代表产品实现、生产工具能力或算法普遍正确性已获证明。

## 需求与语义对照

| proposal / What Changes 要求 | 报告证据 | 任务 | 结果 |
| --- | --- | --- | --- |
| 事实类型、词汇、字段与分层报告 | §2–7；Q/R/F/L/O 全链 | 2.1、2.3、3.1–3.3 | 通过 |
| 范围、软件单元、混合/嵌套/重叠 | R1/R2、F1/F2；S1/S2/S4/S6/S7/S8 | 2.1、4.1 | 通过；范围不是项目身份 |
| 物理包含、成员、从属、组成区别 | R4/F4/O2；S3/S7/S8 | 2.1、2.3、3.2、4.1 | 通过；不强加唯一父节点 |
| 构建/代码/运行时/数据/部署依赖与交互 | R6/R7、F6/F7/O3；S3/S5/S6/S9/S10 | 2.1–2.3、4.1 | 通过；方向/条件/范围/证据保留 |
| 用途、架构、接口、类型、调用、数据、状态、错误、约束、控制及算法 | R3/R5/R8–R14；F3/F5/F8–F16；S11 | 2.1、2.3、3.1、4.1 | 通过；整体可追到局部计算依据 |
| 证据与不确定性 | R15/F17/O4；S12；U1–U5 | 2.2、2.3、3.2、4.1 | 通过；来源性质和知识/适用状态可组合 |
| 问题→需求→主体/粒度/聚合/细化→分层 | §2、§3、§5 | 2.1、3.1 | 通过；未以层数作为输入 |
| 层次与其它维度职责辨析 | L1–L4、O1–O5 | 3.2 | 通过；层顺序不是父树/导航深度 |
| 分层结论、单列/合并/细分与追踪 | §5 各层及备选表、§7 双向追踪 | 3.1–3.3 | 通过；每层有独立问题与边界理由 |
| 典型场景与边界检验 | S1–S12 的输入、预期、证据与结果 | 4.1、4.2 | 通过 |
| 有界核查、来源性质与局限 | E1–E6、U1–U5 | 2.2、4.2 | 通过；每事实最多两源，失败止损 |
| 指定报告路径实际交付 | 九节有内容、报告实存 | 1.1、4.2、5.2 | 通过；不以规划齐备代替交付 |
| 下游事实目录/查询/响应设计输入 | §1、§6、§7、§9 | 4.2、5.1 | 通过；语义字段不是协议字段 |

关键边界自审：L1/L2 保留整体角色与内部职责；L2/L3 保留职责与多对多实现；L3/L4 保留契约与计算依据。F15/F16 分开操作与解释而不强制增加层。O1–O5 均有需求去向，不单列层不等于删减信息。S9/S10 分开结构环、条件可满足环、实际循环。F17 明确来源性质与知识/适用状态可组合，不可合为互斥枚举。外部材料只支持 §4 的窄陈述，不决定层数。

## 场景验收摘要

| 场景 | 关键反例 | 结果 |
| --- | --- | --- |
| S1 | 简单程序可 L1→L3→L4，不造空组件 | 通过 |
| S2 | 共目录不产生共同产品/依赖；缺失内部保持未知 | 通过 |
| S3 | 成员、协作、接口及算法链分开 | 通过 |
| S4 | 多工作空间及独立项目不被根目录吞并 | 通过 |
| S5 | 跨工作空间不阻断追踪；超时不等于未执行 | 通过 |
| S6 | 范围外占位不扩大分析；只展开调用方算法 | 通过 |
| S7 | 物理嵌套不证明逻辑从属 | 通过 |
| S8 | 同一身份、多成员、多职责实现 | 通过 |
| S9 | 保留回边和守卫，静态环不证明无限执行 | 通过 |
| S10 | 互斥条件不能拼成实际循环 | 通过 |
| S11 | [b,a,b]→[b,a]、空输入、空标识错误路径 | 通过 |
| S12 | 未知、限定否定和来源性质独立 | 通过 |

## 实际验证

- `python .git/replan-20261025/test_verify_research.py`：缺陷反例初始失败（8 项，退出码 1）；实现后 9/9 测试通过（退出码 0）。
- `python .git/replan-20261025/verify_research.py openspec/changes/survey-semantic-fact-requirements/research/semantic-fact-requirements.md --trace-only`：退出码 0。
- 同校验器去掉 `--trace-only`，加 `--tasks openspec/changes/survey-semantic-fact-requirements/tasks.md`：完整检查退出码 0。
- `openspec validate survey-semantic-fact-requirements --strict --no-interactive`：退出码 0，skip_specs 的零 delta 被接受。本次使用安装路径下的 `node .../openspec/bin/openspec.js` 执行该命令。
- 从本文件提取代码重新执行：portable_replay=PASS，9/9 测试通过，完整报告退出码 0。
- OpenSpec apply 最终状态：all_done；12/12 项完成；strict 校验退出码 0。

报告 UTF-8、LF 规范化文本 SHA-256：825143510a29e9ca9e34a2b50a40bdcfc776a657da963c13d174087054c906b8

在仓库根目录复算（Python 3）：

```powershell
python -c "from pathlib import Path; import hashlib; print(hashlib.sha256(Path('openspec/changes/survey-semantic-fact-requirements/research/semantic-fact-requirements.md').read_text(encoding='utf-8').replace('\r\n', '\n').encode('utf-8')).hexdigest())"
```

实际 JSON 摘要（计数描述产物，不是预设通过条件）：

```json
{
  "errors": [],
  "entity_counts": {
    "R": 16,
    "Q": 12,
    "F": 18,
    "L": 4,
    "S": 12,
    "U": 5,
    "E": 6,
    "O": 5
  },
  "trace_rows": 18,
  "source_counts": {
    "F1": 0,
    "F10": 1,
    "F11": 1,
    "F12": 1,
    "F13": 1,
    "F14": 1,
    "F15": 1,
    "F16": 0,
    "F17": 2,
    "F18": 0,
    "F2": 1,
    "F3": 0,
    "F4": 2,
    "F5": 0,
    "F6": 1,
    "F7": 1,
    "F8": 1,
    "F9": 1
  },
  "scenario_categories": [
    "单项目",
    "同目录互不依赖多项目",
    "工作空间多项目及依赖",
    "多工作空间与独立项目混合",
    "跨工作空间",
    "范围外依赖",
    "嵌套",
    "重叠与多成员",
    "循环",
    "条件依赖",
    "内部算法",
    "未知与已证实不存在"
  ],
  "mode": "full",
  "task_counts": {
    "total": 12,
    "complete": 12
  }
}
```

机械检查只验证章节、唯一标识、引用、追踪覆盖、两源上限、场景结构与任务统计；不自动判定来源陈述真实性、论证正确性或工具能力。

## 可复现代码

本机 .git 文件只是执行日志。以下完整代码与测试随本记录保存，不依赖已有本机脚本。可把前两个 Python 块分别保存为同目录的 `verify_research.py`、`test_verify_research.py`，用 Python 3 标准库执行；也可从仓库根运行第三块，它会提取本文件前两个块到临时目录并复核。

```python
import argparse, json, re
from collections import Counter
from pathlib import Path

CATS=['单项目','同目录互不依赖多项目','工作空间多项目及依赖','多工作空间与独立项目混合','跨工作空间','范围外依赖','嵌套','重叠与多成员','循环','条件依赖','内部算法','未知与已证实不存在']
HEADINGS=['目标、范围与方法','原始消费者问题与遗漏后果','事实需求与关系分析','外部佐证及支持边界','分层推导与边界论证','事实类型、语义词汇与字段描述','追踪关系','典型场景检验','局限、不确定性与待设计问题']
ID=r'\b[QRF ELOSU]\d+\b'.replace(' ','')
def ids(text): return set(re.findall(ID,text))
def validate(text,trace_only=False):
    errors=[]
    if not text: return {'errors':['missing_report']}
    defined=re.findall(r'^### ([QRF ELOSU]\d+) '.replace(' ', ' ',1),text,re.M)
    counts=Counter(defined); all_ids=set(counts)
    errors += ['duplicate:'+i for i,n in counts.items() if n>1]
    errors += ['dangling:'+i for i in sorted(ids(text)-all_ids)]
    sections={int(m.group(1)):m.group(2) for m in re.finditer(r'^## (\d+)\. ([^\n]+)',text,re.M)}
    if not trace_only:
        for n,title in enumerate(HEADINGS,1):
            if sections.get(n)!=title: errors.append('missing_section:'+str(n))
        for m in re.finditer(r'^## (\d+)\. [^\n]+\n(.*?)(?=^## |\Z)',text,re.M|re.S):
            if not m.group(2).strip(): errors.append('empty_section:'+m.group(1))
    rows=[]
    for line in text.splitlines():
        if re.match(r'^\| Q\d',line):
            cells=[c.strip() for c in line.strip('|').split('|')]
            if len(cells)!=5:
                errors.append('invalid_trace_row'); continue
            groups=[ids(c) for c in cells]
            for idx,prefix in [(0,'Q'),(1,'R'),(2,'F')]:
                if not groups[idx] or any(i[0]!=prefix for i in groups[idx]): errors.append('trace_missing_'+prefix)
            if not groups[3] or any(i[0] not in 'LO' for i in groups[3]): errors.append('trace_missing_destination')
            if any(i[0]!='E' for i in groups[4]): errors.append('invalid_source')
            rows.append(groups)
    traced=set().union(*(set().union(*r[:4]) for r in rows)) if rows else set()
    errors += ['untraced:'+i for i in sorted(all_ids) if i[0] in 'QRFLO' and i not in traced]
    for prefix in 'QRFL':
        if not any(i.startswith(prefix) for i in all_ids): errors.append('missing_entities:'+prefix)
    source_counts={}
    for f in sorted(i for i in all_ids if i.startswith('F')):
        sources=set().union(*(r[4] for r in rows if f in r[2])) if rows else set()
        source_counts[f]=len(sources)
        if len(sources)>2: errors.append('too_many_sources:'+f)
    scenario_categories=[]
    if not trace_only:
        for m in re.finditer(r'^### (S\d+) [^\n]+\n(.*?)(?=^### |^## |\Z)',text,re.M|re.S):
            body=m.group(2)
            cat=re.search(r'^- 场景类别: (.+)$',body,re.M)
            if cat: scenario_categories.append(cat.group(1).strip())
            for field in ['输入','问题','预期','引用','证据','结果','遗漏影响']:
                if not re.search(r'^- '+field+r': \S',body,re.M): errors.append('scenario_field:'+m.group(1)+':'+field)
            if not all(any(i.startswith(p) for i in ids(body)) for p in 'QRF'): errors.append('scenario_trace:'+m.group(1))
            if not any(i[0] in 'LO' for i in ids(body)): errors.append('scenario_organization:'+m.group(1))
        errors += ['missing_scenario:'+cat for cat in CATS if cat not in scenario_categories]
    return {'errors':sorted(set(errors)),'entity_counts':dict(Counter(i[0] for i in all_ids)),'trace_rows':len(rows),'source_counts':source_counts,'scenario_categories':scenario_categories,'mode':'trace' if trace_only else 'full'}
def main():
    p=argparse.ArgumentParser(); p.add_argument('report'); p.add_argument('--tasks'); p.add_argument('--trace-only',action='store_true'); p.add_argument('--output')
    a=p.parse_args(); report=Path(a.report)
    result=validate(report.read_text(encoding='utf-8') if report.exists() else None,a.trace_only)
    if a.tasks:
        tasktext=Path(a.tasks).read_text(encoding='utf-8')
        result['task_counts']={'total':len(re.findall(r'^- \[[ x]\] ',tasktext,re.M)),'complete':len(re.findall(r'^- \[x\] ',tasktext,re.M))}
    output=json.dumps(result,ensure_ascii=False,indent=2)
    if a.output: Path(a.output).write_text(output+'\n',encoding='utf-8')
    print(output)
    return bool(result['errors'])
if __name__=='__main__': raise SystemExit(main())
```

```python
import unittest
from verify_research import validate
CATS=['单项目','同目录互不依赖多项目','工作空间多项目及依赖','多工作空间与独立项目混合','跨工作空间','范围外依赖','嵌套','重叠与多成员','循环','条件依赖','内部算法','未知与已证实不存在']
def fixture():
    sections=['目标、范围与方法','原始消费者问题与遗漏后果','事实需求与关系分析','外部佐证及支持边界','分层推导与边界论证','事实类型、语义词汇与字段描述','追踪关系','典型场景检验','局限、不确定性与待设计问题']
    bodies=['方法','### Q1 问题\n说明','### R1 需求\nQ1','### E1 源\n材料\n### E2 源\n材料\n### E3 源\n材料','### L1 层\nR1\n### O1 组织\nR1','### F1 类型\nR1','| Q | R | F | 组织 | E |\n| --- | --- | --- | --- | --- |\n| Q1 | R1 | F1 | L1, O1 | E1 |','\n'.join('### S'+str(i+1)+' 场景\n- 场景类别: '+c+'\n- 输入: 输入\n- 问题: Q1\n- 预期: 表达\n- 引用: R1 F1 L1\n- 证据: 假设\n- 结果: 通过\n- 遗漏影响: 区别丢失' for i,c in enumerate(CATS)),'未决边界说明']
    return '\n\n'.join('## '+str(i+1)+'. '+h+'\n\n'+b for i,(h,b) in enumerate(zip(sections,bodies)))
class Checks(unittest.TestCase):
    def test_valid_fixture(self): self.assertEqual(validate(fixture())['errors'],[])
    def test_missing_report(self): self.assertIn('missing_report',validate(None)['errors'])
    def test_dangling_id(self): self.assertIn('dangling:Q99',validate(fixture()+'\nQ99')['errors'])
    def test_unsupported_layer(self): self.assertIn('untraced:L2',validate(fixture()+'\n### L2 无需求层\n说明')['errors'])
    def test_requirement_no_destination(self): self.assertIn('trace_missing_destination',validate(fixture().replace('| L1, O1 |','| - |'))['errors'])
    def test_more_than_two_sources(self): self.assertIn('too_many_sources:F1',validate(fixture().replace('| E1 |','| E1, E2, E3 |'))['errors'])
    def test_missing_scenario(self): self.assertIn('missing_scenario:条件依赖',validate(fixture().replace('- 场景类别: 条件依赖','- 场景类别: 别类'))['errors'])
    def test_empty_section(self): self.assertIn('empty_section:1',validate(fixture().replace('方法\n\n## 2','\n\n## 2'))['errors'])
    def test_duplicate_id(self): self.assertIn('duplicate:Q1',validate(fixture()+'\n### Q1 重复\n说明')['errors'])
if __name__=='__main__': unittest.main()
```

```python
from pathlib import Path
import re, subprocess, sys, tempfile
root = Path.cwd()
doc = root / "openspec/changes/survey-semantic-fact-requirements/research/validation.md"
blocks = re.findall(r"^```python\n(.*?)^```", doc.read_text(encoding="utf-8"), re.M | re.S)
assert len(blocks) >= 2
work = Path(tempfile.mkdtemp(prefix="semantic-research-validation-"))
for name, code in zip(["verify_research.py", "test_verify_research.py"], blocks[:2]):
    (work / name).write_text(code, encoding="utf-8")
subprocess.run([sys.executable, str(work / "test_verify_research.py")], check=True)
subprocess.run([sys.executable, str(work / "verify_research.py"),
    str(root / "openspec/changes/survey-semantic-fact-requirements/research/semantic-fact-requirements.md"),
    "--tasks", str(root / "openspec/changes/survey-semantic-fact-requirements/tasks.md")], check=True)
print("portable_replay=PASS")
```

## 不足与交接约束

U1：职责与程序元素边界可重叠，需多角色及分类理由。U2：高级语言/动态行为的无损表达仍需下游扩展，保留残留语义。U3：条件与否定依赖配置、版本和覆盖。U4：架构说明网页超时，未作为证据或标准符合性声明。U5：算法意图、复杂度和终止性并非自动证明。

场景是构造样例，未声称真实代码库采集或工具评测已完成。主变更继续设计事实目录、查询与响应契约时，不能把已登记未知静默转为空关系或已证明结论。
