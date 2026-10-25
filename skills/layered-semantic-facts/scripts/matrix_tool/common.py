"""生产能力矩阵：公共 IO 与路径约定。"""
from pathlib import Path
import json
import yaml

import jsonschema

from layout import SKILL_ROOT, resolve_asset

REPO_ROOT = SKILL_ROOT.parents[1]
MATRIX_DIR = resolve_asset(SKILL_ROOT, "matrix")
SCHEMA_DIR = resolve_asset(SKILL_ROOT, "schema")

ENTRIES_FILE = MATRIX_DIR / "entries.yaml"
PRODUCERS_FILE = MATRIX_DIR / "producers.yaml"
INFO_NEEDS_FILE = MATRIX_DIR / "info-needs.yaml"
HISTORY_DIR = MATRIX_DIR / "history"

SURVEY_REPORT = (
    REPO_ROOT
    / "openspec/changes/survey-info-acquisition-tools/research/semantic-tooling-survey.md"
)


def report_source_rel():
    """调研报告相对仓库根的路径（证据 source 字段用）"""
    return str(SURVEY_REPORT.relative_to(REPO_ROOT))


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(data, path):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def schema_validate(data, schema_name):
    """按 schema 校验，返回错误信息列表（可定位）"""
    schema = json.loads((SCHEMA_DIR / f"{schema_name}.schema.json").read_text("utf-8"))
    errors = []
    for err in jsonschema.Draft7Validator(schema).iter_errors(data):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"schema 校验失败 [{loc}]: {err.message}")
    return errors
