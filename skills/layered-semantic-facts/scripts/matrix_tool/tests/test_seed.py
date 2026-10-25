"""矩阵播种 spec「播种为报告的忠实转换」「矩阵只记现状且内容外源」场景测试。"""
import shutil
from pathlib import Path

import pytest
import yaml

from matrix_tool import common, seed

SURVEY = common.SURVEY_REPORT


def _entries(matrix_dir):
    return yaml.safe_load((matrix_dir / "entries.yaml").read_text("utf-8"))["entries"]


# ---- 播种为报告的忠实转换 ----

def test_同一报告两次播种结果一致(tmp_path):
    m1 = tmp_path / "m1"
    m2 = tmp_path / "m2"
    m1.mkdir(); m2.mkdir()
    seed.seed(SURVEY, m1)
    seed.seed(SURVEY, m2)
    assert (m1 / "entries.yaml").read_text() == (m2 / "entries.yaml").read_text()
    assert (m1 / "producers.yaml").read_text() == (m2 / "producers.yaml").read_text()
    assert (m1 / "info-needs.yaml").read_text() == (m2 / "info-needs.yaml").read_text()


def test_报告增量刷新对应条目_未变化条目保持原状(tmp_path):
    report = tmp_path / "report.md"
    shutil.copy(SURVEY, report)
    m = tmp_path / "m"
    m.mkdir()
    seed.seed(report, m)
    # 修改报告：入口 判定 可完成 → 部分可完成
    text = report.read_text("utf-8")
    assert "| 入口 | 可完成 |" in text
    report.write_text(text.replace("| 入口 | 可完成 |", "| 入口 | 部分可完成 |"), "utf-8")
    added, refreshed, removed = seed.seed(report, m)
    assert added == 0 and removed == 0
    assert refreshed >= 1
    # 入口条目 verdict 已刷新
    entries = _entries(m)
    entry = next(e for e in entries if e["need_id"] == "need.project.entries")
    assert entry["verdict"] == "部分可完成"
    # 未变化条目保持原状：外部依赖仍是"可完成"
    dep = next(e for e in entries if e["need_id"] == "need.project.dependencies")
    assert dep["verdict"] == "可完成"


def test_播种不编造不立项(tmp_path):
    m = tmp_path / "m"
    m.mkdir()
    seed.seed(SURVEY, m)
    entries = _entries(m)
    # 差距清单标记不可完成的需求（数据流/行为约定/模块职责）如实记录，无工具直出生产者
    for need_id in ("need.fact_a.dataflow", "need.fact_a.behavior_contract", "need.module.responsibility"):
        ents = [e for e in entries if e["need_id"] == need_id]
        assert ents, need_id
        assert all(e["verdict"] == "不可完成" for e in ents)
        assert all(e["production_tier"] == "项目分析Skill" for e in ents)
        assert all(e["status"] == "未点亮" for e in ents)


# ---- 矩阵只记现状且内容外源 ----

def test_未点亮条目仅为现状记录_不产生待办(tmp_path):
    m = tmp_path / "m"
    m.mkdir()
    seed.seed(SURVEY, m)
    entries = _entries(m)
    # 未点亮条目只承载现状，schema 无待办/构建指令字段
    for e in entries:
        assert e["status"] == "未点亮"
        assert "todo" not in e and "待办" not in str(e)


def test_空矩阵且无报告_拒绝生成条目(tmp_path):
    m = tmp_path / "m"
    m.mkdir()
    missing = tmp_path / "no-such-report.md"
    with pytest.raises(FileNotFoundError):
        seed.seed(missing, m)
    # 矩阵保持空：不生成 entries.yaml（播种在写盘前即拒绝）
    assert not (m / "entries.yaml").exists()
