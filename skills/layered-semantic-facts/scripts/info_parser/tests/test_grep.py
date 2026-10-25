"""H-grep 解析器 spec 场景测试（fixture 双跑一致性 + 契约校验 + 部分可解析）。"""
from pathlib import Path

from info_parser.contract import validate_item
from info_parser.framework import ParserRegistry
from info_parser.grep import parse_grep

FIXTURE = Path(__file__).parent / "fixtures" / "grep-snapshot.txt"


def _fixture_text():
    return FIXTURE.read_text("utf-8")


def test_确定性_fixture双跑一致():
    raw = _fixture_text()
    r1 = parse_grep(raw)
    r2 = parse_grep(raw)
    assert r1.items == r2.items and r1.ok


def test_意图声明与符号绑定():
    items = parse_grep(_fixture_text()).items
    intents = [i for i in items if i["info_type"] == "symbol_intent"]
    pairs = {(i["content"]["symbol"], i["content"]["intent"]) for i in intents}
    assert ("helper", "helper normalizes n before use") in pairs
    # 注释行绑定紧邻其后的定义行，证据覆盖两行
    it = [i for i in intents if i["content"]["symbol"] == "helper"][0]
    assert it["evidence"] == {"file": "sample_src/lib.rs", "range": "9-10"}


def test_使用契约线索分类():
    items = parse_grep(_fixture_text()).items
    clues = {(i["content"]["symbol"], i["content"]["clue_kind"]) for i in items
             if i["info_type"] == "usage_contract_clue"}
    assert ("Widget", "precondition") in clues
    assert ("Runner", "guarantee") in clues


def test_全部数据项符合信息契约():
    for item in parse_grep(_fixture_text()).items:
        assert validate_item(item) == [], item


def test_部分可解析_非grep行进失败清单():
    raw = _fixture_text() + "\n这一行不是 grep 输出\n"
    r = parse_grep(raw)
    assert r.items and r.failure is not None
    assert r.failure.unparsed == ["这一行不是 grep 输出"]


def test_注册后发现调用():
    reg = ParserRegistry()
    reg.register("H-grep", parse_grep)
    assert reg.parse("H-grep", _fixture_text()).ok


# ---- module_decl（模块声明，5.6 扩展） ----

MODULES_FIXTURE = Path(__file__).parent / "fixtures" / "grep-modules.txt"


def _modules_text():
    return MODULES_FIXTURE.read_text("utf-8")


def test_模块声明双跑一致且映射():
    raw = _modules_text()
    r1 = parse_grep(raw)
    r2 = parse_grep(raw)
    assert r1.items == r2.items
    decls = {i["content"]["name"]: i["content"]["visibility"] for i in r1.items
             if i["info_type"] == "module_decl"}
    assert decls == {"draw_target": "private", "format": "private", "in_memory": "private",
                     "style": "public", "term_like": "private"}


def test_模块声明证据定位():
    for item in parse_grep(_modules_text()).items:
        if item["info_type"] == "module_decl" and item["content"]["name"] == "style":
            assert item["evidence"] == {"file": "sample_src/lib.rs", "range": "260-260"}


def test_模块声明符合信息契约():
    for item in parse_grep(_modules_text()).items:
        assert validate_item(item) == [], item


def test_注释掉的mod声明不误报():
    raw = "sample_src/lib.rs:9:// mod fake;\nsample_src/lib.rs:10:fn helper(n: u32) {\n"
    items = parse_grep(raw).items
    assert not [i for i in items if i["info_type"] == "module_decl"]


def test_上下文分隔符行不进失败清单():
    raw = ("sample_src/lib.rs:9:/// helper doc\n"
           "sample_src/lib.rs-10-fn helper(n: u32) {\n"
           "--\n"
           "sample_src/lib.rs:20:/// other doc\n"
           "sample_src/lib.rs-21-fn other() {\n")
    r = parse_grep(raw)
    assert r.ok
    assert [i["content"]["intent"] for i in r.items if i["info_type"] == "symbol_intent"] == \
        ["helper doc", "other doc"]


# ---- public_entry / use_decl（模块层，5.8 扩展） ----

def test_公共入口_映射与证据():
    raw = ("src/lib.rs:250:pub fn draw(&self) {\n"
           "src/lib.rs:255:pub struct Widget {\n"
           "src/lib.rs:260:pub trait TermLike {\n"
           "src/lib.rs:261:fn hidden() {\n")
    r1, r2 = parse_grep(raw), parse_grep(raw)
    assert r1.items == r2.items  # 双跑一致
    entries = {(i["content"]["name"], i["content"]["kind"]) for i in r1.items
               if i["info_type"] == "public_entry"}
    assert entries == {("draw", "function"), ("Widget", "struct"), ("TermLike", "trait")}
    # 非 pub 声明不产出
    assert not [i for i in r1.items if i["info_type"] == "public_entry"
                and i["content"]["name"] == "hidden"]
    for i in r1.items:
        if i["info_type"] == "public_entry":
            assert validate_item(i) == [], i
            assert i["evidence"]["file"] == "src/lib.rs"


def test_use声明_路径与方向根():
    raw = ("src/state.rs:3:use crate::draw_target::DrawState;\n"
           "src/state.rs:4:use std::io::Write;\n"
           "src/state.rs:5:use super::style;\n"
           "src/state.rs:6:use a::b::{c, d};\n")
    r1, r2 = parse_grep(raw), parse_grep(raw)
    assert r1.items == r2.items  # 双跑一致
    decls = {(i["content"]["path"], i["content"]["root"]) for i in r1.items
             if i["info_type"] == "use_decl"}
    assert decls == {("crate::draw_target::DrawState", "crate"),
                     ("std::io::Write", "external"),
                     ("super::style", "super"),
                     ("a::b::{c, d}", "other")}
    for i in r1.items:
        if i["info_type"] == "use_decl":
            assert validate_item(i) == [], i


def test_pub行中的use注释不误报入口():
    raw = "src/lib.rs:1:// pub fn documented_only();\n"
    items = parse_grep(raw).items
    assert not [i for i in items if i["info_type"] in ("public_entry",)]
