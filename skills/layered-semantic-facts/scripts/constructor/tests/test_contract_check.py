"""契约校验程序测试（任务 1.2，spec「按契约构造语义事实集」）。"""
from constructor.contract_check import validate_contract  # noqa: E402


def _contract(**over):
    base = {"project": "/proj", "facts": {"项目层": ["项目用途/领域", "入口"]}}
    base.update(over)
    return base


def test_合规契约通过():
    errors, out_of_scope = validate_contract(_contract())
    assert errors == []
    assert out_of_scope == []


def test_目录外事实类型记超出范围():
    errors, out_of_scope = validate_contract(_contract(facts={"项目层": ["不存在的事实"]}))
    assert out_of_scope == ["不存在的事实"]


def test_不合规结构被拒绝():
    errors, _ = validate_contract({"facts": "not-an-object"})
    assert errors  # 结构不符 contract.schema.json
