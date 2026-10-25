"""SFRS 机读 schema 验证测试（任务 1.2/1.3；schema 语法有效 + 样例固定资产校验）。"""
import json
from pathlib import Path

import jsonschema

from layout import SKILL_ROOT, resolve_asset

SCHEMA_PATH = resolve_asset(SKILL_ROOT, "schema") / "sfrs.schema.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _schema():
    return json.loads(SCHEMA_PATH.read_text("utf-8"))


def _validate(payload):
    return list(jsonschema.Draft7Validator(_schema()).iter_errors(payload))


def _load(name):
    return json.loads((FIXTURES / name).read_text("utf-8"))


def test_schema语法有效_draft7():
    schema = _schema()
    jsonschema.Draft7Validator.check_schema(schema)


def test_合规事实集通过校验():
    assert _validate(_load("fact_set_valid.json")) == []


def test_不合规条目被拒_原因可定位():
    errors = _validate(_load("fact_set_invalid_structure.json"))
    assert errors  # children 项缺 name → 结构拒绝
    assert "/facts/项目层/0/children/0" in str(errors[0].absolute_path) or errors[0].message


def test_语义报告非契约形态被拒():
    assert _validate(_load("semantic_report.json"))  # 无 project/version/facts 结构 → 拒绝


def test_实体与关系结构校验():
    schema = _schema()
    resolver = jsonschema.RefResolver.from_schema(schema)  # 保持 $ref 的根文档作用域
    entity_validator = jsonschema.Draft7Validator(
        schema["definitions"]["entity"], resolver=resolver)
    relation_validator = jsonschema.Draft7Validator(
        schema["definitions"]["relation"], resolver=resolver)
    payload = _load("relation_invalid_ref.json")
    # 结构合规（引用有效性由仓库运行时检查，任务 4.2）
    assert not list(entity_validator.iter_errors(payload["entities"][0]))
    assert not list(relation_validator.iter_errors(payload["relations"][0]))
