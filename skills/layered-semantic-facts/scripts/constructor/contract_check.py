"""契约校验程序（任务 1.2）：以契约机读 schema 为唯一结构依据 + fact-catalog 封闭世界校验。

返回 (errors, out_of_scope)：
- errors: 不合规结构（schema 校验失败项，可定位）；
- out_of_scope: 契约引用目录外的事实类型（不编造，MUST NOT 产生对应事实）。
"""
import json
from pathlib import Path

import jsonschema

from catalog import FIELDS
from layout import SKILL_ROOT, resolve_asset

_CONTRACT_SCHEMA = resolve_asset(SKILL_ROOT, "schema") / "contract.schema.json"


def load_contract_schema():
    return json.loads(_CONTRACT_SCHEMA.read_text("utf-8"))


def validate_contract(contract, schema=None):
    """校验查询契约。返回 (errors, out_of_scope)。"""
    schema = schema or load_contract_schema()
    errors = []
    for err in jsonschema.Draft7Validator(schema).iter_errors(contract or {}):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"契约结构不符 [{loc}]: {err.message}")

    out_of_scope = []
    facts = (contract or {}).get("facts")
    if isinstance(facts, dict):
        for fact_types in facts.values():
            if isinstance(fact_types, list):
                for t in fact_types:
                    if isinstance(t, str) and t not in FIELDS and t not in out_of_scope:
                        out_of_scope.append(t)
    return errors, out_of_scope
