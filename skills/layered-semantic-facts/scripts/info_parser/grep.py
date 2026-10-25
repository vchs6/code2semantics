"""H-grep 解析器：grep 行输出（grep -n，格式 file:line:text，每行一条）
→ 意图声明与使用契约线索信息数据项（确定性转换）。

意图声明：注释行（//、#、--、/*、*、/// 等）紧邻其后的是符号定义行时，注释绑定该符号，
产出 symbol_intent。使用契约线索：注释文本含契约关键词（Pre/Requires/Returns/Panics/
Example/Error 等）时按 clue_kind 分类产出 usage_contract_clue。
符号名取自定义行的首个标识符（语言无关启发：fn/def/function/struct/class/interface/func 后的名字）。
"""
import re

from .framework import ParseFailure, ParseResult

_COMMENT_RE = re.compile(r"^\s*(//+|#+|--+|/\*+|\*+|;)")
_DEF_RE = re.compile(
    r"^\s*(?:pub\s+|export\s+|public\s+|private\s+|fn\s+|def\s+|function\s+|func\s+|"
    r"struct\s+|class\s+|interface\s+|enum\s+|trait\s+|type\s+)*"
    r"(?:fn|def|function|func|struct|class|interface|enum|trait)\s+([A-Za-z_][A-Za-z0-9_]*)")
_MOD_RE = re.compile(r"^\s*(pub\s+)?mod\s+([A-Za-z_][A-Za-z0-9_]*)")
_PUB_RE = re.compile(r"^\s*pub\s+(fn|struct|enum|trait|type|const)\s+([A-Za-z_][A-Za-z0-9_]*)")
_PUB_KIND = {"fn": "function", "struct": "struct", "enum": "enum",
             "trait": "trait", "type": "type", "const": "constant"}
_USE_RE = re.compile(r"^\s*use\s+(.+?);")
_USE_ROOTS = {"crate": "crate", "super": "super", "self": "self",
              "std": "external", "core": "external", "alloc": "external"}


def _use_root(path):
    first = path.split("::", 1)[0].strip()
    return _USE_ROOTS.get(first, "other")
_CONTRACT_RULES = [
    ("panics", re.compile(r"panics?\b|panic!", re.I)),
    ("precondition", re.compile(r"\bpre\b|precondition|requires?\b|must\b", re.I)),
    ("parameter_constraint", re.compile(r"parameter constraint|参数|argument|constraint", re.I)),
    ("guarantee", re.compile(r"returns?\b|guarantee|ensures?\b|保证", re.I)),
]


def _parse_line(ln):
    # 匹配行：path:line:text（路径在 grep 输出中不含冒号，故首个冒号前即路径）；
    # 上下文行（-A/-B/-C）：path-line-text（分隔符为连字符，路径同样不含冒号）。
    m = re.match(r"^([^:]+):(\d+):(.*)$", ln)
    if not m:
        m = re.match(r"^([^:]+)-(\d+)-(.*)$", ln)
    if not m:
        return None
    return {"file": m.group(1), "line": int(m.group(2)), "text": m.group(3)}


def _first_contract_kind(text):
    for kind, rx in _CONTRACT_RULES:
        if rx.search(text):
            return kind
    return None


def parse_grep(raw_output, profile=None):
    """grep -n 输出（str）→ symbol_intent / usage_contract_clue 信息数据项。"""
    if raw_output is None:
        lines = []
    elif isinstance(raw_output, (bytes, str)):
        lines = raw_output.splitlines()
    else:
        lines = [str(x) for x in raw_output]

    parsed = []
    unparsed = []
    for ln in lines:
        if not ln.strip():
            continue
        if ln.strip() == "--":
            continue  # grep 上下文分隔符（-A/-B/-C），非数据行
        rec = _parse_line(ln)
        if rec is None:
            unparsed.append(ln)
            continue
        parsed.append(rec)

    items = []
    for i, rec in enumerate(parsed):
        # 模块声明：^mod <name> / ^pub mod <name>（注释行不命中，注释前缀已排除）
        m_mod = _MOD_RE.match(rec["text"])
        if m_mod:
            items.append({
                "info_type": "module_decl",
                "content": {"name": m_mod.group(2),
                            "visibility": "public" if m_mod.group(1) else "private"},
                "evidence": {"file": rec["file"], "range": f"{rec['line']}-{rec['line']}"},
                "source_tool": "H-grep",
            })
            continue
        if _COMMENT_RE.match(rec["text"]):
            pass  # 注释行 → 走意图/契约绑定
        else:
            # 公共入口：pub fn/struct/enum/trait/type/const
            m_pub = _PUB_RE.match(rec["text"])
            if m_pub:
                items.append({
                    "info_type": "public_entry",
                    "content": {"name": m_pub.group(2), "kind": _PUB_KIND[m_pub.group(1)],
                                "signature": rec["text"].strip()},
                    "evidence": {"file": rec["file"], "range": f"{rec['line']}-{rec['line']}"},
                    "source_tool": "H-grep",
                })
                continue
            # use 声明：模块间依赖方向线索
            m_use = _USE_RE.match(rec["text"])
            if m_use:
                items.append({
                    "info_type": "use_decl",
                    "content": {"path": m_use.group(1).strip(),
                                "root": _use_root(m_use.group(1).strip())},
                    "evidence": {"file": rec["file"], "range": f"{rec['line']}-{rec['line']}"},
                    "source_tool": "H-grep",
                })
                continue
            continue
        text = rec["text"].strip().lstrip("/#-*;").strip()
        if not text:
            continue
        # 绑定：向后找紧邻的定义行（中间不得再有其他行）
        j = i + 1
        if j < len(parsed) and parsed[j]["line"] == rec["line"] + 1:
            m = _DEF_RE.match(parsed[j]["text"])
            if m:
                kind = _first_contract_kind(text)
                if kind:
                    items.append({
                        "info_type": "usage_contract_clue",
                        "content": {"symbol": m.group(1), "clue_kind": kind, "text": text},
                        "evidence": {"file": rec["file"], "range": f"{rec['line']}-{parsed[j]['line']}"},
                        "source_tool": "H-grep",
                    })
                else:
                    items.append({
                        "info_type": "symbol_intent",
                        "content": {"symbol": m.group(1), "intent": text},
                        "evidence": {"file": rec["file"], "range": f"{rec['line']}-{parsed[j]['line']}"},
                        "source_tool": "H-grep",
                    })

    result = ParseResult(items=items)
    if unparsed:
        result.failure = ParseFailure(
            tool_id="H-grep", reason=f"{len(unparsed)} 行不符合 grep -n 输出格式", unparsed=unparsed)
    return result
