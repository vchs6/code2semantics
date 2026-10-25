"""X-ctags 解析器：universal-ctags JSON 输出（--output-format=json，每行一个 JSON 对象）
→ 符号层信息数据项（确定性转换）。

产出 symbol_def 信息数据项：公共接口（signature/visibility）与类型定义（kind/fields）。
fields 按 ctags scope 归组：field/ member 标签归入其所属类型的 fields。
每条附源码证据定位（file:range），证据自 line/end 可回溯。
"""
import json

from .framework import ParseFailure, ParseResult

_TYPE_KINDS = {"struct", "class", "enum", "interface", "union", "record"}
_FIELD_KINDS = {"field", "member", "enumConstant"}


def _item(tag, fields):
    content = {
        "name": tag["name"],
        "kind": tag.get("kind"),
        "signature": tag.get("signature"),
        "visibility": tag.get("access"),
    }
    if content["kind"] in _TYPE_KINDS:
        content["fields"] = fields.get(tag["name"], [])
    return {
        "info_type": "symbol_def",
        "content": content,
        "evidence": {"file": tag["path"], "range": f"{tag['line']}-{tag.get('end') or tag['line']}"},
        "source_tool": "X-ctags",
    }


def parse_ctags(raw_output, profile=None):
    """ctags JSON 输出（str：JSON Lines；list/dict：已解析标签列表）→ ParseResult。"""
    if isinstance(raw_output, (bytes, str)):
        tags = []
        for ln in raw_output.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                tags.append(json.loads(ln))
            except ValueError as exc:
                return ParseResult(failure=ParseFailure(
                    tool_id="X-ctags", reason=f"无法解析 JSON Lines：{exc}"))
    else:
        tags = raw_output

    if not isinstance(tags, list):
        tags = [tags]

    items, unparsed = [], []
    fields_by_type, type_tags = {}, []
    for tag in tags:
        if not isinstance(tag, dict) or not tag.get("name") or not tag.get("path") or "line" not in tag:
            unparsed.append(tag)
            continue
        scope = tag.get("scope")
        if tag.get("kind") in _FIELD_KINDS and scope:
            fields_by_type.setdefault(scope.split("::")[-1], []).append(
                {"name": tag["name"], "type": tag.get("typeref", "").replace("typename:", "") or None})
        else:
            type_tags.append(tag)

    for tag in type_tags:
        kind = tag.get("kind")
        if kind in _TYPE_KINDS or kind in {"function", "method", "macro", "constant"}:
            items.append(_item(tag, fields_by_type))
        else:
            unparsed.append(tag)

    result = ParseResult(items=items)
    if unparsed:
        result.failure = ParseFailure(
            tool_id="X-ctags", reason=f"{len(unparsed)} 项无法解析", unparsed=unparsed)
    return result
