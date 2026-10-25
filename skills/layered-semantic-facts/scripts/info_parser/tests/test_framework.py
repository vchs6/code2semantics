"""解析器框架 spec「解析器注册与发现」「解析失败显式表达」场景测试（桩解析器，不依赖真实工具）。"""
from info_parser.framework import (
    ParseFailure,
    ParseResult,
    ParserRegistry,
)


def _stub_parser(raw_output, profile):
    """桩解析器：把 raw_output 包成一条数据项。"""
    return ParseResult(items=[{"info_type": "stub", "raw": raw_output}])


def _failing_parser(raw_output, profile):
    return ParseResult(failure=ParseFailure(
        tool_id="stub-fail", reason="无法解析：输出为空", unparsed=[raw_output]))


def _partial_parser(raw_output, profile):
    return ParseResult(
        items=[{"info_type": "stub", "raw": raw_output["ok"]}],
        failure=ParseFailure(
            tool_id="stub-partial", reason="部分不可解析",
            unparsed=raw_output["bad"]))


def test_注册后发现调用结果回传():
    reg = ParserRegistry()
    reg.register("stub", _stub_parser)
    result = reg.parse("stub", "hello", profile={})
    assert result.ok
    assert result.items == [{"info_type": "stub", "raw": "hello"}]


def test_按工具标识取解析器():
    reg = ParserRegistry()
    reg.register("stub", _stub_parser)
    assert reg.get("stub") is _stub_parser


def test_请求未注册解析器_明确未实现():
    reg = ParserRegistry()
    result = reg.parse("no-such-tool", "x")
    assert not result.ok
    assert result.failure.reason == "解析器未实现：no-such-tool 未注册"
    assert result.items == []


def test_无法解析_返回结构化失败_不产数据项():
    reg = ParserRegistry()
    reg.register("stub-fail", _failing_parser)
    result = reg.parse("stub-fail", "")
    assert not result.ok
    assert result.failure.tool_id == "stub-fail"
    assert result.failure.reason
    assert result.items == []


def test_部分可解析_可解析部分产数据项_不可解析部分进清单():
    reg = ParserRegistry()
    reg.register("stub-partial", _partial_parser)
    result = reg.parse("stub-partial", {"ok": "good", "bad": ["junk"]})
    assert result.items  # 可解析部分产出
    assert result.failure is not None  # 不可解析部分结构化报告
    assert result.failure.unparsed == ["junk"]


def test_解析器异常转为结构化失败():
    def boom(raw, profile):
        raise ValueError("bad output")
    reg = ParserRegistry()
    reg.register("boom", boom)
    result = reg.parse("boom", "x")
    assert not result.ok
    assert "解析异常" in result.failure.reason
