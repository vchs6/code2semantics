"""H-ast_grep 解析器：ast-grep JSON 输出（--json，JSON 数组或每行一个匹配对象）
→ 信息数据项（确定性转换）。

按调用剖面的 facet（profile["facet"]）分面抽取，语言无关结构部分。模式变量使用
规范捕获名（SOURCE/TARGET/CALLEE/CONDITION/ERROR_EXPR/RESOURCE/SYMBOL 等），
缺失的枚举字段（relation/op/control_flow_kind）由 profile 补充缺省值：
- symbol_relation：捕获 SOURCE、TARGET；relation = meta RELATION 或 profile["relation"]（缺省 implement）
- call_condition：捕获 CALLEE、CONDITION；caller = meta CALLER（可为 null）
- error_handling：捕获 ERROR_EXPR；op = meta OP 或 profile["op"]（缺省 throw）
- lifecycle_event：捕获 RESOURCE；op = meta OP 或 profile["op"]（缺省 create）
- element_structure：捕获 SYMBOL；control_flow_kind = meta KIND 或 profile["kind"]（缺省 branch）
每条附 file:range 证据（ast-grep range.start.line 为 0 基，解析时 +1）。
"""
import json

from .framework import ParseFailure, ParseResult

_REQUIRED = {
    "symbol_relation": ("SOURCE", "TARGET"),
    "call_condition": ("CALLEE", "CONDITION"),
    "error_handling": ("ERROR_EXPR",),
    "lifecycle_event": ("RESOURCE",),
    "element_structure": ("SYMBOL",),
}
_DEFAULTS = {
    "symbol_relation": ("relation", "implement"),
    "error_handling": ("op", "throw"),
    "lifecycle_event": ("op", "create"),
    "element_structure": ("kind", "branch"),
}


def _single_match(line):
    """解析一行/一个 ast-grep JSON 匹配，返回 (file, start_line, end_line, meta) 或 None。"""
    try:
        obj = json.loads(line)
    except ValueError:
        return None
    try:
        file = obj["file"]
        start_line = obj["range"]["start"]["line"] + 1
        end_line = obj["range"]["end"]["line"] + 1
    except (KeyError, TypeError):
        return None
    single = (obj.get("metaVariables") or {}).get("single") or {}
    meta = {k: v.get("text") for k, v in single.items() if isinstance(v, dict)}
    # 捕获名别名归一：trait 模式常用 $TRAIT 命名关系目标
    if "TARGET" not in meta and "TRAIT" in meta:
        meta["TARGET"] = meta["TRAIT"]
    return file, start_line, end_line, meta


def _build_item(facet, profile, file, start_line, end_line, meta):
    missing = [k for k in _REQUIRED[facet] if not meta.get(k)]
    if missing:
        return None
    if facet == "symbol_relation":
        content = {"relation": meta.get("RELATION") or profile.get("relation") or "implement",
                   "source": meta["SOURCE"], "target": meta["TARGET"]}
    elif facet == "call_condition":
        content = {"caller": meta.get("CALLER"), "callee": meta["CALLEE"],
                   "condition_kind": "branch", "condition_pattern": meta["CONDITION"]}
    elif facet == "error_handling":
        content = {"op": meta.get("OP") or profile.get("op") or "throw",
                   "error_expr": meta["ERROR_EXPR"]}
    elif facet == "lifecycle_event":
        content = {"resource": meta["RESOURCE"],
                   "op": meta.get("OP") or profile.get("op") or "create"}
    else:
        content = {"symbol": meta["SYMBOL"],
                   "control_flow_kind": meta.get("KIND") or profile.get("kind") or "branch"}
    return {
        "info_type": facet,
        "content": content,
        "evidence": {"file": file, "range": f"{start_line}-{end_line}"},
        "source_tool": "H-ast_grep",
    }


def parse_ast_grep(raw_output, profile=None):
    """ast-grep JSON 输出 → ParseResult。profile["facet"] 指明事实分面（必需）。"""
    profile = profile or {}
    facet = profile.get("facet")
    if facet not in _REQUIRED:
        return ParseResult(failure=ParseFailure(
            tool_id="H-ast_grep", reason=f"未知或缺失的 facet：{facet!r}"))

    if isinstance(raw_output, (bytes, str)):
        try:
            data = json.loads(raw_output)
            records = data if isinstance(data, list) else [data]
        except ValueError:
            records = [ln for ln in raw_output.splitlines() if ln.strip()]
    elif isinstance(raw_output, dict):
        records = [raw_output]
    else:
        records = list(raw_output)

    items, unparsed = [], []
    for rec in records:
        parsed = _single_match(rec if isinstance(rec, str) else json.dumps(rec))
        if parsed is None:
            unparsed.append(rec if isinstance(rec, str) else json.dumps(rec))
            continue
        file, start_line, end_line, meta = parsed
        item = _build_item(facet, profile, file, start_line, end_line, meta)
        if item is None:
            unparsed.append(rec if isinstance(rec, str) else json.dumps(rec))
            continue
        items.append(item)

    result = ParseResult(items=items)
    if unparsed:
        result.failure = ParseFailure(
            tool_id="H-ast_grep", reason=f"{len(unparsed)} 个匹配缺必需捕获组", unparsed=unparsed)
    return result
