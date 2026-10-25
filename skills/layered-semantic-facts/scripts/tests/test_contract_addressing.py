"""契约节点寻址测试（任务 1.1，design 决策 3；既有扁平契约向后兼容）。"""
import json

import jsonschema

from layout import SKILL_ROOT, resolve_asset

SCHEMA = json.loads(
    (resolve_asset(SKILL_ROOT, "schema") / "contract.schema.json").read_text("utf-8"))


def _errors(contract):
    return list(jsonschema.Draft7Validator(SCHEMA).iter_errors(contract))


def test_既有扁平契约向后兼容():
    contract = {"project": "/p", "facts": {"项目层": ["项目用途/领域", "入口"]}}
    assert _errors(contract) == []


def test_节点定位契约通过校验():
    contract = {"facts": {"项目层": [{"fact_type": "入口"}]}}
    assert _errors(contract) == []


def test_续查契约通过校验():
    contract = {"facts": {"项目层": [{"fact_type": "模块划分", "path": ["modules"]}]}}
    assert _errors(contract) == []


def test_混合形态契约通过校验():
    contract = {"facts": {"项目层": ["入口", {"fact_type": "项目用途/领域"}]}}
    assert _errors(contract) == []


def test_非法寻址形态被拒绝():
    assert _errors({"facts": {"项目层": [{"fact_type": 123}]}})  # fact_type 须为字符串
    assert _errors({"facts": {"项目层": [{"path": "not-a-list"}]}})  # path 须为字符串列表
    assert _errors({"facts": {"项目层": [{"unknown": 1}]}})  # 未知字段拒绝
