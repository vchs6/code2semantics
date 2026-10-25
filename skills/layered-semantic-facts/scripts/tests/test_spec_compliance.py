"""Agent Skills 规范符合性对照检查表（任务 3.1；skills-ref 不可用时的可判定验收）。

检查项依据 AGENTS.md 原则 9 引用的 Agent Skills Specification
（agentskills/agentskills，docs/specification.mdx）：
frontmatter 字段与约束、推荐目录结构、渐进披露（SKILL.md <500 行）。
"""
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = SKILL_ROOT / "SKILL.md"

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def _frontmatter():
    text = SKILL_MD.read_text("utf-8")
    m = _FRONTMATTER_RE.match(text)
    assert m, "SKILL.md MUST 以 YAML frontmatter 开头"
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip()
    return fields, text[m.end():]


def test_目录结构符合规范():
    assert (SKILL_ROOT / "SKILL.md").is_file()  # SKILL.md 必需
    assert (SKILL_ROOT / "scripts").is_dir()    # 程序代码
    assert (SKILL_ROOT / "references").is_dir() # 按需加载文档
    assert (SKILL_ROOT / "assets").is_dir()     # 静态资源与数据文件（含 schema）


def test_frontmatter_name约束():
    fields, _ = _frontmatter()
    name = fields["name"]
    assert name == SKILL_ROOT.name  # 必须匹配父目录名
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name)  # 小写字母-数字-连字符，无连续/首尾连字符
    assert len(name) <= 64


def test_frontmatter_description约束():
    fields, _ = _frontmatter()
    desc = fields["description"]
    assert 0 < len(desc) <= 1024  # 非空且 ≤1024


def test_frontmatter_compatibility约束():
    fields, _ = _frontmatter()
    compat = fields.get("compatibility")
    assert compat and len(compat) <= 500  # 存在时 ≤500（运行环境要求声明位）


def test_渐进披露_SKILL正文小于500行():
    _, body = _frontmatter()
    assert len(body.splitlines()) < 500


def test_文件引用相对路径存在():
    for rel in ("references/fact-catalog.md", "references/contract-format.md",
                "references/output-schema.md", "references/report-template.md",
                "scripts/layout.py", "assets/schema/contract.schema.json",
                "assets/schema/output.schema.json", "assets/matrix/entries.yaml"):
        assert (SKILL_ROOT / rel).exists(), f"SKILL.md/文档引用的路径不存在：{rel}"
