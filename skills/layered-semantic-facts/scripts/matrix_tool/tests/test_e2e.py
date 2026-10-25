"""矩阵端到端串联 spec「集成验证」场景测试（任务 4.1）。

链路：真实报告播种 → 一致性校验 → 点亮项目级工具 → 只读查询（平台筛选），
产出可供构造器消费的矩阵。全程在 tmp 目录，确定性、可重复。
"""
from pathlib import Path

from matrix_tool import common
from matrix_tool.e2e import matrix_e2e


def test_端到端串联_播种校验点亮查询(tmp_path):
    m = tmp_path / "matrix"
    m.mkdir()
    out = matrix_e2e(common.SURVEY_REPORT, m)
    # 播种 + 校验 + 点亮 + 查询 全程无异常
    assert out["seed_ok"] and out["validate_ok"]
    assert out["lit_count"] > 0
    # 查询结果含平台筛选后的生产者链
    chain = out["chain"]
    assert chain
    assert all("producer_id" in c and "production_tier" in c for c in chain)
    # 产出矩阵文件落盘
    assert (m / "entries.yaml").exists()
    assert (m / "producers.yaml").exists()
    assert (m / "info-needs.yaml").exists()
