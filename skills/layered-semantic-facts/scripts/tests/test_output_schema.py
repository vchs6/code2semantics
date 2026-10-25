"""output.schema.json 演进测试（任务 2.2）：合成器输出通过新响应 schema 校验。"""
import json

import jsonschema

from layout import SKILL_ROOT, resolve_asset
from synthesizer import synthesize

_SCHEMA = json.loads(
    (resolve_asset(SKILL_ROOT, "schema") / "output.schema.json").read_text("utf-8"))


def _validate(out):
    return list(jsonschema.Draft7Validator(_SCHEMA).iter_errors(out))


def test_合成器输出通过响应schema():
    merged = {
        "项目用途/领域": [
            {"_id": "e1", "name": "indicatif", "domain": "进度条库", "doc": "README.md",
             "evidence": {"file": "Cargo.toml", "range": "1-14"}},
        ],
        "模块划分": [{"_id": "m0", "modules": ["a"]}],
    }
    out = synthesize(
        {"project": "/p", "facts": {"项目层": ["项目用途/领域", "模块划分"]}},
        merged, version="v1",
        subtree_map={"模块划分": {"modules": "模块职责"}})
    assert _validate(out) == []


def test_gaps字段级缺口通过响应schema():
    out = synthesize({"project": "/p", "facts": {}}, merged={}, version="v1",
                     gaps=[{"type": "构建与运行形态", "field": "run",
                            "reason": "信息需求差距段：无对应生产者"}])
    assert _validate(out) == []
