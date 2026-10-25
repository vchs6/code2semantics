"""H-ast_grep 解析器 spec 场景测试（真实采集 fixture 双跑一致性 + 契约校验 + 分面）。"""
import json
from pathlib import Path

from info_parser.ast_grep import parse_ast_grep
from info_parser.contract import validate_item

FIX = Path(__file__).parent / "fixtures"


def _load(name):
    lines = (FIX / name).read_text("utf-8").splitlines()
    return "\n".join(ln for ln in lines if ln.strip())


def test_确定性_fixture双跑一致():
    raw = _load("ag-snapshot-relation.jsonl")
    r1 = parse_ast_grep(raw, {"facet": "symbol_relation"})
    r2 = parse_ast_grep(raw, {"facet": "symbol_relation"})
    assert r1.ok and r1.items == r2.items


def test_符号关系分面():
    r = parse_ast_grep(_load("ag-snapshot-relation.jsonl"), {"facet": "symbol_relation"})
    item = r.items[0]
    assert item["content"] == {"relation": "implement", "source": "Widget", "target": "Runner"}
    assert item["evidence"] == {"file": "sample_src/lib.rs", "range": "5-11"}  # 0 基行号 +1


def test_调用条件分面():
    r = parse_ast_grep(_load("ag-snapshot-condition.jsonl"), {"facet": "call_condition"})
    item = r.items[0]
    assert item["content"]["callee"] == "helper"
    assert item["content"]["condition_kind"] == "branch"
    assert item["content"]["condition_pattern"] == "self.w > 0"
    assert item["content"]["caller"] is None


def test_错误处理与生命周期分面():
    r = parse_ast_grep(_load("ag-snapshot-error.jsonl"), {"facet": "error_handling"})
    assert r.items[0]["content"] == {"op": "throw", "error_expr": '"bad state"'}
    r2 = parse_ast_grep(_load("ag-snapshot-lifecycle.jsonl"), {"facet": "lifecycle_event"})
    assert r2.items[0]["content"] == {"resource": "conn", "op": "create"}
    # profile 缺省值可覆盖
    r3 = parse_ast_grep(_load("ag-snapshot-lifecycle.jsonl"),
                        {"facet": "lifecycle_event", "op": "acquire"})
    assert r3.items[0]["content"]["op"] == "acquire"


def test_元素结构分面():
    r = parse_ast_grep(_load("ag-snapshot-element.jsonl"),
                       {"facet": "element_structure", "kind": "match"})
    assert r.items[0]["content"] == {"symbol": "n", "control_flow_kind": "match"}


def test_缺facet报结构化失败():
    r = parse_ast_grep(_load("ag-snapshot-error.jsonl"))
    assert r.items == [] and r.failure is not None
    assert "facet" in r.failure.reason


def test_缺捕获组进部分失败清单():
    raw = _load("ag-snapshot-error.jsonl") + "\n" + json.dumps(
        {"file": "a.rs", "range": {"start": {"line": 0}}, "metaVariables": {"single": {}}})
    r = parse_ast_grep(raw, {"facet": "error_handling"})
    assert len(r.items) == 1 and r.failure is not None and len(r.failure.unparsed) == 1


def test_全部数据项符合信息契约():
    cases = [
        ("ag-snapshot-relation.jsonl", {"facet": "symbol_relation"}),
        ("ag-snapshot-condition.jsonl", {"facet": "call_condition"}),
        ("ag-snapshot-error.jsonl", {"facet": "error_handling"}),
        ("ag-snapshot-lifecycle.jsonl", {"facet": "lifecycle_event"}),
        ("ag-snapshot-element.jsonl", {"facet": "element_structure"}),
    ]
    for name, profile in cases:
        for item in parse_ast_grep(_load(name), profile).items:
            assert validate_item(item) == [], (name, item)
