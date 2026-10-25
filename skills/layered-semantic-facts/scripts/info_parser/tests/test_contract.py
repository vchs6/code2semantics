"""信息契约落实 spec「输出符合信息契约」场景测试（任务 2.1、2.2）。"""
from info_parser import contract
from info_parser.framework import ParseResult, check_contract


def _valid_package():
    return {
        "info_type": "cargo_package",
        "content": {
            "name": "indicatif", "version": "0.18.6", "edition": "2021",
            "rust_version": "1.85", "description": "进度条库",
            "readme": "README.md", "repository": "https://github.com/console-rs/indicatif",
        },
        "evidence": {"file": "Cargo.toml", "range": "2-8"},
        "source_tool": "X-cargo_metadata",
    }


def test_符合样例通过契约校验():
    assert contract.is_valid(_valid_package())


def test_违例样例校验失败():
    bad = _valid_package()
    bad["content"].pop("version")  # 缺必填字段
    assert contract.validate_item(bad)


def test_缺证据校验失败():
    bad = _valid_package()
    bad.pop("evidence")
    assert contract.validate_item(bad)


def test_check_contract_全部符合_返回成功():
    result = check_contract([_valid_package()], tool_id="X-cargo_metadata")
    assert result.ok and result.items


def test_check_contract_违例被拦截转失败():
    bad = _valid_package()
    bad["content"].pop("name")
    result = check_contract([bad], tool_id="X-cargo_metadata")
    assert not result.ok
    assert result.items == []
    assert result.failure.unparsed == [bad]


def test_check_contract_部分符合_可解析部分保留():
    good = _valid_package()
    bad = _valid_package()
    bad["content"].pop("name")
    result = check_contract([good, bad], tool_id="X-cargo_metadata")
    assert result.items == [good]  # 可解析部分保留
    assert result.failure is not None
    assert result.failure.unparsed == [bad]
