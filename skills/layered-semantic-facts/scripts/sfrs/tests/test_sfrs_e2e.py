"""SFRS 集成验证（任务 4.6 文档冒烟 + 5.1 端到端演练）。

5.1：契约查询模式在真实项目上产出事实集 → 以（项目、版本）提交入库 →
新版本提交增量变化 → 历史版本与最新版本分别查询、沿关系遍历。
"""
import json
from pathlib import Path

import pytest

from layout import SKILL_ROOT, resolve_asset

REPO_ROOT = SKILL_ROOT.parents[1]
INDICATIF = REPO_ROOT.parent / "sm-test" / "source" / "indicatif"

pytestmark = pytest.mark.skipif(
    not INDICATIF.exists(), reason="本地无 indicatif 测试项目")

_SCHEMA = json.loads(
    (resolve_asset(SKILL_ROOT, "schema") / "output.schema.json").read_text("utf-8"))


def test_文档所载用法可实际执行(tmp_path):
    """任务 4.6 冒烟：README 使用文档的示例片段按文档原样可执行。"""
    from sfrs.repository import SFRS
    repo = SFRS(db_path=tmp_path / "facts.db")
    assert repo.accessible() is True
    result = repo.submit({"project": "demo", "version": "v1", "facts": {}})
    assert "accepted" in result
    assert repo.read("demo", "v1") is None  # 空事实集不入库实体：该版本无事实（spec 语义）
    with pytest.raises(ValueError):
        repo.read("demo", None)  # 显式版本语义（OQ3）


def test_端到端演练_提交增量与历史追溯(tmp_path):
    import jsonschema
    from constructor_adapter import RealConstructorAdapter
    from orchestrator import orchestrate
    from repo_stub import InMemoryRepo
    from sfrs.repository import SFRS
    from versioning import current_version

    # 1) 契约查询模式在真实项目上产出事实集
    out = orchestrate(
        {"project": str(INDICATIF), "facts": {"项目层": [{"fact_type": "项目用途/领域"}]}},
        InMemoryRepo(), RealConstructorAdapter(project_root=str(INDICATIF)),
        version_fn=current_version)
    assert "error" not in out
    jsonschema.Draft7Validator(_SCHEMA).validate(out)
    version = out["version"]

    # 2) 以（项目、版本）提交入库
    repo = SFRS(db_path=tmp_path / "facts.db")
    fact_set = {"project": "indicatif", "version": version, "facts": out["facts"]}
    result = repo.submit(fact_set)
    assert "error" not in result and result["accepted"] > 0

    # 3) 新版本提交增量变化（仅变更一个字段的值）
    fs_v2 = json.loads(json.dumps(fact_set))
    fs_v2["version"] = version + "-new"
    fs_v2["facts"]["项目层"][0]["children"][1]["value"] = "进度条与 CLI 报告库"
    result2 = repo.submit(fs_v2)
    # 新版本是独立的（项目、版本）键：实体在新版本首次入库 accepted=1；
    # 旧版本内容不受影响（历史可追溯，见下）
    assert "error" not in result2 and result2["accepted"] == 1

    # 同 ID 同（项目、版本）内不同内容会判冲突；新版本是独立的（项目、版本）键，
    # 因此 accepted 计入新版本的实体。核对历史与最新两个版本的内容。
    v1 = repo.read("indicatif", version)
    v2 = repo.read("indicatif", version + "-new")
    v1_val = next(c for c in v1["facts"]["项目层"][0]["children"] if c["name"] == "domain")["value"]
    v2_val = next(c for c in v2["facts"]["项目层"][0]["children"] if c["name"] == "domain")["value"]
    assert v1_val == "A progress bar and cli reporting library for Rust"  # 历史可追溯
    assert v2_val == "进度条与 CLI 报告库"  # 新版本增量生效

    # 4) 查询结果与提交内容一致
    rows = repo.query(project="indicatif", version=version, fact_type="项目用途/领域")
    assert rows and rows[0]["entity_id"].startswith("项目用途/领域:")
