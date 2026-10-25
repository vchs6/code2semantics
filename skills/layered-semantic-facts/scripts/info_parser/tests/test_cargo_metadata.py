"""cargo_metadata 解析器 spec「工具输出到信息数据项的确定性转换」「输出符合信息契约」
「解析失败显式表达」「解析器可增量接入」场景测试。

测试自包含：用 tmp_path 构造最小 Rust 项目 + 对应 cargo metadata 结构，
证据定位据此在项目内可回链；确定性场景另以真实采集 fixture 双跑验证。
"""
import json
import shutil
from pathlib import Path

from info_parser.cargo_metadata import parse_cargo_metadata
from info_parser.contract import validate_item
from info_parser.framework import ParserRegistry

FIXTURE = Path(__file__).parent / "fixtures" / "cargo-metadata-indicatif.json"


def _make_project(tmp_path):
    """构造最小 Rust 项目：Cargo.toml + src/lib.rs + examples/demo.rs。"""
    proj = tmp_path / "demo"
    (proj / "src").mkdir(parents=True)
    (proj / "examples").mkdir()
    (proj / "Cargo.toml").write_text(
        '[package]\nname = "demo"\nversion = "0.1.0"\nedition = "2021"\n'
        'description = "demo crate"\nreadme = "README.md"\n\n'
        "[dependencies]\nserde = \"1.0\"\n\n[dev-dependencies]\npretty_assertions = \"1.4\"\n",
        encoding="utf-8",
    )
    (proj / "src" / "lib.rs").write_text("pub fn hello() {}\n", encoding="utf-8")
    (proj / "examples" / "demo.rs").write_text("fn main() {}\n", encoding="utf-8")
    return proj


def _metadata(proj):
    return {
        "packages": [{
            "name": "demo", "version": "0.1.0", "edition": "2021",
            "description": "demo crate", "readme": "README.md",
            "repository": None, "rust_version": None,
            "manifest_path": str(proj / "Cargo.toml"),
            "targets": [
                {"name": "demo", "kind": ["lib"], "crate_types": ["lib"],
                 "src_path": str(proj / "src" / "lib.rs")},
                {"name": "demo", "kind": ["example"], "crate_types": ["bin"],
                 "src_path": str(proj / "examples" / "demo.rs")},
            ],
            "dependencies": [
                {"name": "serde", "req": "^1.0", "kind": None, "optional": False},
                {"name": "pretty_assertions", "req": "^1.4", "kind": "dev", "optional": False},
            ],
        }],
    }


def test_确定性_相同输入恒得相同输出(tmp_path):
    proj = _make_project(tmp_path)
    md = _metadata(proj)
    r1 = parse_cargo_metadata(md, {"project_root": str(proj)})
    r2 = parse_cargo_metadata(md, {"project_root": str(proj)})
    assert r1.items == r2.items


def test_真实fixture双跑一致性():
    raw = FIXTURE.read_text(encoding="utf-8")
    proj = "/home/vchs6/sm-test/source/indicatif"
    r1 = parse_cargo_metadata(raw, {"project_root": proj})
    r2 = parse_cargo_metadata(raw, {"project_root": proj})
    assert r1.items == r2.items
    assert r1.ok


def test_输出通过契约校验_证据可定位(tmp_path):
    proj = _make_project(tmp_path)
    md = _metadata(proj)
    result = parse_cargo_metadata(md, {"project_root": str(proj)})
    assert result.ok
    for item in result.items:
        assert validate_item(item) == []
        # 证据可在项目中定位
        ev = item["evidence"]
        assert (proj / ev["file"]).exists(), ev["file"]


def test_无法解析JSON_返回结构化失败():
    result = parse_cargo_metadata("not-json{{", {"project_root": "/tmp"})
    assert not result.ok
    assert result.failure.tool_id == "X-cargo_metadata"
    assert result.items == []


def test_部分可解析_缺name依赖进失败清单(tmp_path):
    proj = _make_project(tmp_path)
    md = _metadata(proj)
    md["packages"][0]["dependencies"].append({"req": "^1", "kind": None, "optional": False})  # 缺 name
    result = parse_cargo_metadata(md, {"project_root": str(proj)})
    assert result.items  # 可解析部分产出
    assert result.failure is not None  # 不可解析部分结构化报告
    assert any("name" not in u["dependency"] for u in result.failure.unparsed)


def test_增量接入_既有解析器行为不变(tmp_path):
    proj = _make_project(tmp_path)
    md = _metadata(proj)
    before = parse_cargo_metadata(md, {"project_root": str(proj)})

    # 新增一个桩解析器注册
    reg = ParserRegistry()
    reg.register("X-cargo_metadata", parse_cargo_metadata)
    reg.register("new-tool", lambda raw, profile: None)

    after = parse_cargo_metadata(md, {"project_root": str(proj)})
    assert after.items == before.items
    assert reg.get("X-cargo_metadata") is parse_cargo_metadata
