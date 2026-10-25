"""编排核心的生产者选择与解析器调用（任务 4.1/4.2）。

- select_producers：依信息需求只读查询能力矩阵，取「判定可完成 且 解析器已实现」
  的工具直出条目；解析器未实现的条目不选用并标注原因；矩阵外无条目返回空。
  MUST NOT 编造矩阵中不存在的生产者（spec「按能力矩阵选择生产者」）。
- call_parser：经统一注册接口调用外部解析器取信息数据项；解析器缺失返回
  结构化失败，由调用方归并进 gaps（spec「输出解析经外部解析器」）。
"""
from matrix_tool.query import query_producers


def select_producers(fact_type, matrix_dir, parser_registry):
    """查矩阵选生产者。返回 (usable, unavailable)。

    usable: [{"tool_id", "invocation_profile"}]——已点亮、判定非"不可完成"、
            工具直出、且解析器已注册。
    unavailable: [{"tool_id", "reason"}]——解析器未实现的已点亮条目。
    """
    chain = query_producers(fact_type=fact_type, matrix_dir=matrix_dir)
    usable, unavailable = [], []
    for item in chain:
        if item["production_tier"] != "工具直出" or item["verdict"] == "不可完成":
            continue
        if item["status"] != "已点亮":
            continue
        tool_id = item["producer_id"]
        if parser_registry.get(tool_id) is None:
            unavailable.append({
                "tool_id": tool_id,
                "reason": f"解析器未实现：{tool_id}",
            })
            continue
        usable.append({
            "tool_id": tool_id,
            "invocation_profile": item["invocation_profile"],
        })
    return usable, unavailable


def call_parser(tool_id, raw_output, profile, parser_registry):
    """经统一注册接口调用解析器；解析器缺失返回「解析器未实现」失败结果。"""
    parser = parser_registry.get(tool_id)
    if parser is None:
        from info_parser.framework import ParseFailure, ParseResult
        return ParseResult(failure=ParseFailure(
            tool_id=tool_id, reason=f"解析器未实现：{tool_id}"))
    return parser_registry.parse(tool_id, raw_output, profile)
