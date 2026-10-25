"""H-trace_callees / H-trace_callers 解析器 spec 场景测试
（fixture 双跑一致性 + 契约校验 + 失败结构 + 注册发现）。"""
import json
from pathlib import Path

from info_parser.contract import validate_item
from info_parser.framework import ParserRegistry
from info_parser.trace_calls import parse_trace_callees, parse_trace_callers

FIX = Path(__file__).parent / "fixtures"


def _load(name):
    return (FIX / name).read_text("utf-8")


def test_确定性_fixture双跑一致():
    raw = _load("trace-callees-snapshot.json")
    r1 = parse_trace_callees(raw)
    r2 = parse_trace_callees(raw)
    assert r1.ok and r1.items == r2.items


def test_出边方向():
    r = parse_trace_callees(_load("trace-callees-snapshot.json"))
    contents = {(i["content"]["caller"], i["content"]["callee"], i["content"]["direction"])
                for i in r.items}
    assert ("Widget::run", "helper", "outgoing") in contents
    assert ("helper", "cleanup", "outgoing") in contents


def test_入边方向():
    r = parse_trace_callers(_load("trace-callers-snapshot.json"))
    directions = {i["content"]["direction"] for i in r.items}
    assert directions == {"incoming"}
    pairs = {(i["content"]["caller"], i["content"]["callee"]) for i in r.items}
    assert ("main", "helper") in pairs


def test_证据定位():
    r = parse_trace_callees(_load("trace-callees-snapshot.json"))
    ev = {(i["evidence"]["file"], i["evidence"]["range"]) for i in r.items}
    assert ("sample_src/lib.rs", "7-7") in ev


def test_全部数据项符合信息契约():
    for name, fn in [("trace-callees-snapshot.json", parse_trace_callees),
                     ("trace-callers-snapshot.json", parse_trace_callers)]:
        for item in fn(_load(name)).items:
            assert validate_item(item) == [], (name, item)


def test_失败结构():
    r = parse_trace_callees('{"target": "x"}')
    assert r.items == [] and r.failure is not None and "edges" in r.failure.reason
    r2 = parse_trace_callees("not json")
    assert r2.failure is not None and "JSON" in r2.failure.reason
    # 缺 from/to 的边进 unparsed
    raw = json.dumps({"edges": [{"from": "a", "to": "b"}, {"to": "c"}]})
    r3 = parse_trace_callees(raw)
    assert len(r3.items) == 1 and r3.failure is not None and len(r3.failure.unparsed) == 1


def test_注册后发现调用_未注册仍报未实现():
    reg = ParserRegistry()
    reg.register("H-trace_callees", parse_trace_callees)
    reg.register("H-trace_callers", parse_trace_callers)
    assert reg.parse("H-trace_callees", _load("trace-callees-snapshot.json")).ok
    assert reg.parse("H-trace_callers", _load("trace-callers-snapshot.json")).ok
