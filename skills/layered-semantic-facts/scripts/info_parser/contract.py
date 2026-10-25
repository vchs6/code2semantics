"""信息契约（项目信息数据项）数据结构绑定与契约校验。"""
import json
from pathlib import Path

import jsonschema

from layout import SKILL_ROOT, resolve_asset

_SCHEMA_PATH = resolve_asset(SKILL_ROOT, "schema") / "info-contract.schema.json"


def load_schema():
    return json.loads(_SCHEMA_PATH.read_text("utf-8"))


def validate_item(item, schema=None):
    """校验单条信息数据项，返回错误消息列表（空列表 = 通过）。"""
    schema = schema or load_schema()
    errors = []
    for err in jsonschema.Draft7Validator(schema).iter_errors(item):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{loc}: {err.message}")
    return errors


def is_valid(item, schema=None):
    return not validate_item(item, schema)
