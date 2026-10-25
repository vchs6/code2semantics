"""SFRS 仓库行为测试（任务 4.1–4.5；spec 8 个 Requirement 的场景对照）。

固定样例：sfrs/tests/fixtures/（任务 1.3 资产）。
"""
import json
from pathlib import Path

import pytest

from sfrs.model import decompose, reassemble
from sfrs.repository import SFRS

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _fact_set(name="fact_set_valid.json"):
    return json.loads((FIXTURES / name).read_text("utf-8"))


@pytest.fixture()
def repo(tmp_path):
    return SFRS(db_path=tmp_path / "facts.db")


def test_建库幂等_重复初始化不破坏数据(tmp_path):
    db = tmp_path / "facts.db"
    fs = _fact_set()
    r1 = SFRS(db_path=db)
    r1.submit(fs)
    r2 = SFRS(db_path=db)  # 重复建库（CREATE IF NOT EXISTS）
    out = r2.read(fs["project"], fs["version"])
    assert out is not None  # 数据完好


def test_合规事实集提交与取回一致(repo):
    fs = _fact_set()
    repo.submit(fs)
    out = repo.read(fs["project"], fs["version"])
    assert out == fs  # 取回与提交一致（重组透明）


def test_语义报告被拒绝_仓库状态不变(repo):
    report = json.loads((FIXTURES / "semantic_report.json").read_text("utf-8"))
    result = repo.submit(report)
    assert "error" in result and "读写单位" in result["error"]
    assert repo.read("indicatif", "v1") is None  # 状态不变


def test_不合规结构被拒_原因可定位(repo):
    bad = _fact_set("fact_set_invalid_structure.json")
    result = repo.submit(bad)
    assert "error" in result
    assert "children" in result["error"] or "name" in result["error"]


def test_重复提交幂等_不产生重复事实(repo):
    fs = _fact_set()
    r1 = repo.submit(fs)
    r2 = repo.submit(fs)
    assert r2["accepted"] == 0  # 幂等：无新入库
    assert repo.read(fs["project"], fs["version"]) == fs


def test_单实体更新不影响其余事实(repo):
    fs = _fact_set()
    repo.submit(fs)
    # 构造单实体增量更新（新内容的同名实体 → 版本冲突拒绝；不同实体更新不影响他者）
    updated = json.loads(json.dumps(fs))
    updated["facts"]["项目层"][0]["children"][0]["value"] = "indicatif2"
    result = repo.submit(updated)  # 同 (项目,版本) 同 ID 不同内容 → 版本冲突
    assert "error" in result and "版本冲突" in result["error"]
    assert repo.read(fs["project"], fs["version"]) == fs  # 已存事实保持不变


def test_新版本提交不影响旧版本_历史可追溯(repo):
    fs_v1 = _fact_set()
    repo.submit(fs_v1)
    fs_v2 = json.loads(json.dumps(fs_v1))
    fs_v2["version"] = "b22222"
    fs_v2["facts"]["项目层"][0]["children"][1]["value"] = "进度条与 CLI 报告库"
    repo.submit(fs_v2)
    v1 = repo.read("indicatif", fs_v1["version"])  # 旧版本状态可追溯
    v2 = repo.read("indicatif", "b22222")
    assert v1["facts"]["项目层"][0]["children"][1]["value"] == "A progress bar and cli reporting library for Rust"
    assert v2["facts"]["项目层"][0]["children"][1]["value"] == "进度条与 CLI 报告库"


def test_同版本同ID不同内容判版本冲突(repo):
    fs = _fact_set()
    repo.submit(fs)
    conflicting = json.loads(json.dumps(fs))
    conflicting["facts"]["项目层"][0]["children"][0]["value"] = "tampered"
    result = repo.submit(conflicting)
    assert "error" in result and "版本冲突" in result["error"]


def test_按条件精确查询_只返回匹配事实(repo):
    fs = _fact_set()
    repo.submit(fs)
    rows = repo.query(project=fs["project"], version=fs["version"], fact_type="项目用途/领域")
    assert rows and all(r["fact_type"] == "项目用途/领域" for r in rows)
    assert repo.query(project=fs["project"], version=fs["version"], fact_type="配置项") == []


def test_关系遍历_只返回显式关系(repo):
    payload = json.loads((FIXTURES / "relation_invalid_ref.json").read_text("utf-8"))
    entities = payload["entities"]
    repo.submit_entities("p", "v1", entities)
    # 无效引用被拒：v2 内无任何实体，关系两端引用均不存在（报出首个缺失端）
    result = repo.submit_relations("p", "v2", payload["relations"])
    assert "error" in result and "引用无效" in result["error"] and "不存在" in result["error"]
    # v1 内 to_entity 也缺失 → 夹具关系同样被拒（无效引用样例的语义）
    assert "error" in repo.submit_relations("p", "v1", payload["relations"])
    # 有效关系提交后遍历：只返回显式关系边，不推导新事实
    rel_valid = {"relation_id": "r2", "from_entity": "ent_exists",
                 "to_entity": "ent_exists", "relation_type": "调用"}
    assert "error" not in repo.submit_relations("p", "v1", [rel_valid])
    edges = repo.relations_from("p", "v1", "ent_exists")
    assert edges == [rel_valid]
    assert repo.relations_from("p", "v1", "ent_missing") == []


def test_未指明版本即参数错误_保守语义(repo):
    with pytest.raises(ValueError):
        repo.read("indicatif", None)
