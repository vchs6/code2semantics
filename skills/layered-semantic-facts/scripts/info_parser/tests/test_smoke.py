"""集成验证（任务 4.1）：构造器桩端到端冒烟——调用剖面驱动框架调用，数据项/失败结果按约定回传。"""
from pathlib import Path

from info_parser.framework import registry, parse_with_profile
from info_parser.cargo_metadata import parse_cargo_metadata

FIXTURE = Path(__file__).parent / "fixtures" / "cargo-metadata-indicatif.json"


def test_冒烟_调用剖面驱动框架调用_数据项回传():
    registry.register("X-cargo_metadata", parse_cargo_metadata)
    raw = FIXTURE.read_text(encoding="utf-8")
    profile = {
        "project_root": "/home/vchs6/sm-test/source/indicatif",
        "output_type": "json",
        "parser_id": "X-cargo_metadata",
    }
    result = parse_with_profile(profile, raw)
    assert result.ok
    assert result.items
    assert all(item["source_tool"] == "X-cargo_metadata" for item in result.items)


def test_冒烟_未注册解析器按约定返回失败():
    profile = {"output_type": "json", "parser_id": "no-such-tool"}
    result = parse_with_profile(profile, "{}")
    assert not result.ok
    assert result.failure.reason == "解析器未实现：no-such-tool 未注册"
    assert result.items == []
