"""5.5 增量接入回归：第 5 阶段新解析器注册后，既有解析器（X-cargo_metadata）
行为与调用结果不变；default_parser_registry 全量注册可用（spec「解析器可增量接入」）。"""
import sys
from pathlib import Path

from constructor_adapter import default_parser_registry
from info_parser.contract import validate_item
from info_parser.ctags import parse_ctags
from info_parser.framework import ParserRegistry

FIXTURES = Path(__file__).parent / "fixtures"


def _ctags_raw():
    return (FIXTURES / "ctags-snapshot.jsonl").read_text("utf-8")


def test_新解析器注册不改既有解析器行为(tmp_path):
    # 基线：空注册表 + X-cargo_metadata
    proj = tmp_path / "demo"
    (proj / "src").mkdir(parents=True)
    (proj / "Cargo.toml").write_text(
        '[package]\nname = "demo"\nversion = "0.1.0"\nedition = "2021"\n',
        encoding="utf-8")
    (proj / "src" / "lib.rs").write_text("pub fn hello() {}\n", encoding="utf-8")
    metadata = {"packages": [{
        "name": "demo", "version": "0.1.0", "edition": "2021",
        "description": None, "readme": None, "repository": None, "rust_version": None,
        "manifest_path": str(proj / "Cargo.toml"),
        "targets": [{"name": "demo", "kind": ["lib"], "crate_types": ["lib"],
                     "src_path": str(proj / "src" / "lib.rs")}],
        "dependencies": [],
    }]}

    base = ParserRegistry()
    from info_parser.cargo_metadata import parse_cargo_metadata
    base.register("X-cargo_metadata", parse_cargo_metadata)
    baseline = base.parse("X-cargo_metadata", metadata, {"project_root": str(proj)})

    # 注册全部新解析器后，既有解析器结果逐项不变
    from constructor_adapter import default_parser_registry
    full = default_parser_registry()
    after = full.parse("X-cargo_metadata", metadata, {"project_root": str(proj)})
    assert after.ok and baseline.ok
    assert after.items == baseline.items


def test_第5阶段解析器全部已注册且契约合规():
    reg = default_parser_registry()
    for tool_id in ["X-cargo_metadata", "X-ctags", "H-grep", "H-ast_grep",
                    "H-trace_callees", "H-trace_callers"]:
        assert reg.get(tool_id) is not None, tool_id
    # 符号层解析器在真实采集 fixture 上通过契约校验
    result = reg.parse("X-ctags", _ctags_raw())
    assert result.ok
    for item in result.items:
        assert validate_item(item) == [], item
