"""矩阵更新脚本 spec「更新点亮条目且版本化」场景测试。"""
from pathlib import Path

import yaml

from matrix_tool import common, seed, update


def _seeded_matrix(tmp_path):
    m = tmp_path / "m"
    m.mkdir()
    seed.seed(common.SURVEY_REPORT, m)
    return m


def _entries(m):
    return yaml.safe_load((m / "entries.yaml").read_text("utf-8"))["entries"]


def test_解析器落地点亮条目_可被查询到(tmp_path):
    m = _seeded_matrix(tmp_path)
    n = update.light_up(layer="项目层", matrix_dir=m)
    assert n > 0
    entries = _entries(m)
    # 项目层工具直出条目已点亮
    lit = [e for e in entries if e["need_id"] == "need.project.entries" and e["producer_id"] == "X-cargo_metadata"]
    assert lit and lit[0]["status"] == "已点亮"
    assert lit[0]["invocation_profile"]["command"]


def test_仅点亮项目级工具_兜底与其它层不点亮(tmp_path):
    m = _seeded_matrix(tmp_path)
    update.light_up(layer="项目层", matrix_dir=m)
    entries = _entries(m)
    for e in entries:
        need_is_project = e["need_id"].startswith("need.project.")
        is_tool = e["production_tier"] == "工具直出"
        if need_is_project and is_tool:
            assert e["status"] == "已点亮", (e["need_id"], e["producer_id"])
        else:
            assert e["status"] == "未点亮", (e["need_id"], e["producer_id"], e["production_tier"])


def test_更新保留变更痕迹(tmp_path):
    m = _seeded_matrix(tmp_path)
    update.light_up(layer="项目层", matrix_dir=m)
    history_dir = m / "history"
    revs = sorted(history_dir.glob("rev-*.yaml"))
    assert revs
    hist = yaml.safe_load(revs[0].read_text("utf-8"))
    assert "changed" in hist and hist["changed"]
    # 修改前后内容可追溯
    for c in hist["changed"]:
        assert c["before"]["status"] == "未点亮"
        assert c["after"]["status"] == "已点亮"


def test_空矩阵更新拒绝(tmp_path):
    m = tmp_path / "m"
    m.mkdir()
    # 空矩阵（无 entries.yaml 或 entries 空）→ 点亮无目标，不生成条目
    import yaml as _y
    _y.safe_dump({"schema_version": 1, "revision": 0, "identifier_note": "", "entries": []},
                 open(m / "entries.yaml", "w", encoding="utf-8"))
    _y.safe_dump({"schema_version": 1, "producers": []},
                 open(m / "producers.yaml", "w", encoding="utf-8"))
    _y.safe_dump({"schema_version": 1, "identifier_note": "占位标识：need.<事实类型slug>，待 add-semantic-fact-constructor 信息需求清单对齐后统一替换", "needs": []},
                 open(m / "info-needs.yaml", "w", encoding="utf-8"))
    n = update.light_up(layer="项目层", matrix_dir=m)
    assert n == 0
    assert _entries(m) == []
