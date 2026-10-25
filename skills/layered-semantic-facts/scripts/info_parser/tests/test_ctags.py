"""X-ctags 解析器 spec「工具输出到信息数据项的确定性转换」「输出符合信息契约」
「解析失败显式表达」场景测试（fixture 双跑一致性 + 契约校验 + 失败结构）。"""
import json
from pathlib import Path

from info_parser.contract import validate_item
from info_parser.ctags import parse_ctags
from info_parser.framework import ParserRegistry

FIXTURE = Path(__file__).parent / "fixtures" / "ctags-snapshot.jsonl"


def _fixture_text():
    return FIXTURE.read_text("utf-8")


def test_确定性_fixture双跑一致():
    raw = _fixture_text()
    r1 = parse_ctags(raw)
    r2 = parse_ctags(raw)
    assert r1.ok and r2.ok
    assert r1.items == r2.items


def test_公共接口与类型定义映射():
    items = {i["content"]["name"]: i for i in parse_ctags(_fixture_text()).items}
    # 公共接口：signature/visibility
    assert items["helper"]["content"] == {
        "name": "helper", "kind": "function", "signature": "fn helper(n: u32)", "visibility": None}
    assert items["run"]["content"]["signature"] == "fn run(&self)"
    assert items["run"]["content"]["visibility"] is None
    # 类型定义：kind + fields（按 scope 归组）
    assert items["Widget"]["content"]["kind"] == "struct"
    assert items["Widget"]["content"]["fields"] == [{"name": "w", "type": "u32"}]
    assert items["Runner"]["content"]["kind"] == "interface"


def test_证据定位可在项目定位():
    for item in parse_ctags(_fixture_text()).items:
        ev = item["evidence"]
        assert ev["file"] == "sample_src/lib.rs"
        start, end = ev["range"].split("-")
        assert 1 <= int(start) <= int(end)


def test_全部数据项符合信息契约():
    for item in parse_ctags(_fixture_text()).items:
        assert validate_item(item) == [], item


def test_失败与部分可解析():
    # 全失败：非 JSON 行
    r = parse_ctags("not json\n")
    assert r.items == [] and r.failure is not None
    assert r.failure.tool_id == "X-ctags"
    # 部分可解析：缺 name 的标签进 unparsed
    good = json.dumps({"_type": "tag", "name": "f", "path": "a.rs", "kind": "function", "line": 1})
    r2 = parse_ctags(good + "\n" + json.dumps({"_type": "tag", "path": "a.rs", "line": 2}) + "\n")
    assert len(r2.items) == 1 and r2.failure is not None and len(r2.failure.unparsed) == 1


def test_注册后发现调用():
    reg = ParserRegistry()
    reg.register("X-ctags", parse_ctags)
    result = reg.parse("X-ctags", _fixture_text())
    assert result.ok
    # 未注册工具保持「解析器未实现」
    miss = reg.parse("X-其他", _fixture_text())
    assert miss.items == [] and "未注册" in miss.failure.reason
