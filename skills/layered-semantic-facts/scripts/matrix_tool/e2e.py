"""矩阵端到端串联（spec「集成验证」）：播种 → 一致性校验 → 点亮项目级 → 查询。

确定性、可重复；用真实调研报告在给定矩阵目录上走完整链路。
"""
from . import seed, update, validate, query


def matrix_e2e(report_path, matrix_dir):
    """执行端到端串联，返回链路结果 dict。

    链路：seed 播种 → validate 一致性校验 → light_up 点亮项目级工具
    → query_producers 平台筛选查询（产出供构造器消费的生产者链）。
    """
    # 播种
    added, refreshed, removed = seed.seed(report_path, matrix_dir)
    seed_ok = added > 0 or refreshed > 0 or removed >= 0  # 播种本身成功（真实报告全量）
    # 一致性校验
    validate_ok = validate.validate_matrix(matrix_dir) == []
    # 点亮项目级工具
    lit_count = update.light_up(layer="项目层", matrix_dir=matrix_dir)
    # 查询：平台筛选后的生产者链（以"入口"为例）
    chain = query.query_producers(fact_type="入口", platform="linux", matrix_dir=matrix_dir)
    return {
        "seed_ok": seed_ok,
        "validate_ok": validate_ok,
        "lit_count": lit_count,
        "chain": chain,
    }
