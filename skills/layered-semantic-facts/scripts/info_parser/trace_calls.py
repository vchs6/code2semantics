"""H-trace_callees / H-trace_callers 解析器：调用链工具 JSON 输出
→ 调用关系信息数据项（确定性转换）。

输入契约（trace 工具捕获输出）：
  {"target": "<符号>", "edges": [{"from": "...", "to": "...", "file": "...", "lines": "12-15"}, ...]}
H-trace_callees 产出 direction=outgoing（target=from 的出边），H-trace_callers 产出
direction=incoming（target=to 的入边）。condition 缺省为 null（条件语义属归纳层）。
"""
import json

from .framework import ParseFailure, ParseResult


def _parse_trace(raw_output, tool_id, direction, key_index):
    if isinstance(raw_output, (bytes, str)):
        try:
            data = json.loads(raw_output)
        except ValueError as exc:
            return ParseResult(failure=ParseFailure(
                tool_id=tool_id, reason=f"无法解析 JSON：{exc}"))
    else:
        data = raw_output

    edges = (data or {}).get("edges")
    if not isinstance(data, dict) or edges is None:
        return ParseResult(failure=ParseFailure(
            tool_id=tool_id, reason="输出缺少 edges 字段（trace 工具捕获契约）"))

    items, unparsed = [], []
    for edge in edges:
        if not isinstance(edge, dict) or not edge.get("from") or not edge.get("to"):
            unparsed.append(edge)
            continue
        file = edge.get("file")
        lines = edge.get("lines") or "1-1"
        evidence = {"file": file, "range": lines} if file else {"file": "<unknown>", "range": lines}
        items.append({
            "info_type": "call_relation",
            "content": {
                "caller": edge["from"],
                "callee": edge["to"],
                "direction": direction,
                "condition": edge.get("condition"),
            },
            "evidence": evidence,
            "source_tool": tool_id,
        })

    result = ParseResult(items=items)
    if unparsed:
        result.failure = ParseFailure(
            tool_id=tool_id, reason=f"{len(unparsed)} 条边缺少 from/to", unparsed=unparsed)
    return result


def parse_trace_callees(raw_output, profile=None):
    """trace_callees 输出 → 调用关系（caller→callee，direction=outgoing）。"""
    return _parse_trace(raw_output, "H-trace_callees", "outgoing", 0)


def parse_trace_callers(raw_output, profile=None):
    """trace_callers 输出 → 调用关系（caller←callee，direction=incoming）。"""
    return _parse_trace(raw_output, "H-trace_callers", "incoming", 1)
