import shutil
from pathlib import Path

import pytest

from matrix_tool import common, validate



def entry(**over):
    base = {
        "need_id": "need.project.entries",
        "producer_id": "X-cargo_metadata",
        "verdict": "可完成",
        "production_tier": "工具直出",
        "platforms": ["linux"],
        "runtime_guidance": "",
        "invocation_profile": {
            "structure_placeholder": "待 add-info-parser 注册接口协议定稿回填（design OQ3）",
            "command": None,
            "timeout_seconds": None,
            "retries": None,
            "output_type": None,
            "parser_id": None,
        },
        "evidence": {"source": "AGENTS.md", "line_start": 1, "line_end": 2},
        "status": "未点亮",
    }
    base.update(over)
    return base


def write_matrix(root, entries, producers=None, needs=None):
    common.dump_yaml(
        {
            "schema_version": 1,
            "revision": 0,
            "identifier_note": "占位",
            "entries": entries,
        },
        root / "entries.yaml",
    )
    common.dump_yaml(
        {
            "schema_version": 1,
            "producers": producers
            or [
                {
                    "id": "X-cargo_metadata",
                    "name": "cargo metadata",
                    "kind": "external_tool",
                    "scale": "小型",
                    "languages": ["Rust 专属"],
                    "evidence": {
                        "source": "AGENTS.md",
                        "line_start": 1,
                        "line_end": 2,
                    },
                }
            ],
        },
        root / "producers.yaml",
    )
    common.dump_yaml(
        {
            "schema_version": 1,
            "identifier_note": "占位标识：need.<事实类型slug>，待 add-semantic-fact-constructor 信息需求清单对齐后统一替换",
            "needs": needs
            or [
                {
                    "id": "need.project.entries",
                    "layer": "项目层",
                    "fact_type": "入口",
                    "required_info": "bin target 清单",
                    "evidence": {
                        "source": "AGENTS.md",
                        "line_start": 1,
                        "line_end": 2,
                    },
                }
            ],
        },
        root / "info-needs.yaml",
    )


@pytest.fixture
def matrix_root(tmp_path):
    root = tmp_path / "matrix"
    root.mkdir()
    write_matrix(root, [entry()])
    return root


def test_valid_matrix_passes(matrix_root):
    assert validate.validate_matrix(matrix_root) == []


def test_orphan_entry_detected(matrix_root):
    write_matrix(matrix_root, [entry(producer_id="X-undefined_tool")])
    errors = validate.validate_matrix(matrix_root)
    assert any("孤儿条目" in e and "X-undefined_tool" in e for e in errors)


def test_orphan_need_detected(matrix_root):
    write_matrix(matrix_root, [entry(need_id="need.undefined.thing")])
    errors = validate.validate_matrix(matrix_root)
    assert any("孤儿条目" in e and "need.undefined.thing" in e for e in errors)


def test_evidence_file_missing_detected(matrix_root):
    write_matrix(
        matrix_root,
        [entry(evidence={"source": "no/such/file.md", "line_start": 1, "line_end": 1})],
    )
    errors = validate.validate_matrix(matrix_root)
    assert any("证据无法回链" in e and "no/such/file.md" in e for e in errors)


def test_evidence_line_out_of_range_detected(matrix_root):
    write_matrix(matrix_root, [entry(evidence={"source": "AGENTS.md", "line_start": 1, "line_end": 99999})])
    errors = validate.validate_matrix(matrix_root)
    assert any("证据无法回链" in e and "超出" in e for e in errors)


def test_schema_violation_rejected(matrix_root):
    write_matrix(matrix_root, [entry(verdict="超强")])
    errors = validate.validate_matrix(matrix_root)
    assert any("schema 校验失败" in e and "verdict" in e for e in errors)


def test_lit_without_command_detected(matrix_root):
    write_matrix(matrix_root, [entry(status="已点亮")])
    errors = validate.validate_matrix(matrix_root)
    assert any("不自洽" in e and "command" in e for e in errors)


def test_uncompletable_cannot_be_lit(matrix_root):
    write_matrix(matrix_root, [entry(verdict="不可完成", status="已点亮",
                                   invocation_profile={"command": "x", "timeout_seconds": 5,
                                                       "retries": 0, "output_type": "json", "parser_id": "p"})])
    errors = validate.validate_matrix(matrix_root)
    assert any("不可完成却已点亮" in e for e in errors)


def test_duplicate_entry_detected(matrix_root):
    write_matrix(matrix_root, [entry(), entry()])
    errors = validate.validate_matrix(matrix_root)
    assert any("重复条目" in e for e in errors)


def test_real_repo_matrix_self_evidence(tmp_path):
    """AGENTS.md 作证据在真实仓库根可回链"""
    root = tmp_path / "matrix"
    root.mkdir()
    write_matrix(root, [entry()])
    assert validate.validate_matrix(root) == []
