"""工具生产信息解析器框架：按工具标识注册解析器，经统一调用约定被构造器调用。

框架不含任何具体工具的转换逻辑；每个工具的解析器为独立实现，按工具标识注册。
统一调用约定：registry.parse(tool_id, raw_output, profile) -> ParseResult。
"""
from dataclasses import dataclass, field

from .contract import validate_item


@dataclass
class ParseFailure:
    """结构化失败结果（与数据项同型回传，交构造器归并进 gaps）。"""
    tool_id: str
    reason: str
    unparsed: list = field(default_factory=list)


@dataclass
class ParseResult:
    """统一回传：成功 → items 非空、failure 为 None；失败 → failure 非 None。"""
    items: list = field(default_factory=list)
    failure: ParseFailure = None

    @property
    def ok(self):
        return self.failure is None


class ParserRegistry:
    """解析器注册与发现。"""

    def __init__(self):
        self._parsers = {}

    def register(self, tool_id, parser):
        self._parsers[tool_id] = parser

    def get(self, tool_id):
        return self._parsers.get(tool_id)

    def parse(self, tool_id, raw_output, profile=None):
        """统一调用约定：按工具标识发现并调用解析器，返回 ParseResult。"""
        profile = profile or {}
        parser = self.get(tool_id)
        if parser is None:
            return ParseResult(failure=ParseFailure(
                tool_id=tool_id, reason=f"解析器未实现：{tool_id} 未注册"))
        try:
            result = parser(raw_output, profile)
            if not isinstance(result, ParseResult):
                return ParseResult(items=result if isinstance(result, list) else [])
            return result
        except Exception as exc:
            return ParseResult(failure=ParseFailure(
                tool_id=tool_id, reason=f"解析异常：{type(exc).__name__}: {exc}"))


def check_contract(items, tool_id):
    """对信息数据项列表做契约校验：不符契约的项被拦截，转为结构化失败。"""
    valid, invalid = [], []
    for item in items:
        if validate_item(item):
            invalid.append(item)
        else:
            valid.append(item)
    if not invalid:
        return ParseResult(items=valid)
    return ParseResult(
        items=valid,
        failure=ParseFailure(
            tool_id=tool_id,
            reason=f"契约校验失败：{len(invalid)} 项不符合信息契约",
            unparsed=invalid,
        ),
    )


def parse_with_profile(profile, raw_output):
    """按调用剖面（output_type → 解析器映射）驱动框架调用。

    profile 的 parser_id（工具标识）指明解析器，缺省回退 output_type；
    这是构造器「输出解析」环节的最小驱动入口（任务 4.1 冒烟）。
    """
    profile = profile or {}
    tool_id = profile.get("parser_id") or profile.get("output_type")
    return registry.parse(tool_id, raw_output, profile)


# 全局注册表（构造器经此调用）
registry = ParserRegistry()
