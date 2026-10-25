"""矩阵只读查询接口（spec「只读查询接口」）。

供构造器按信息需求/事实类型取生产者链（含生产层级、调用方式、运行平台与运行指导），
支持按运行平台筛选；无写入路径，查询 MUST NOT 修改矩阵（design 决策 5：同进程库调用）。

接口：query_producers(need_id=… | fact_type=…, platform=…, status=…, matrix_dir=…)
"""
from pathlib import Path

from .common import (
    MATRIX_DIR,
    load_yaml,
)


def load_matrix(matrix_dir=None):
    """读矩阵三文件（只读）。matrix_dir 缺省为全局矩阵目录。"""
    matrix_dir = Path(matrix_dir) if matrix_dir else MATRIX_DIR
    entries = load_yaml(matrix_dir / "entries.yaml")["entries"]
    producers = {p["id"]: p for p in load_yaml(matrix_dir / "producers.yaml")["producers"]}
    needs = load_yaml(matrix_dir / "info-needs.yaml")["needs"]
    need_by_fact_type = {n["fact_type"]: n for n in needs}
    return entries, producers, need_by_fact_type


def _resolve_need_id(need_id, fact_type, need_by_fact_type):
    if need_id is not None:
        return need_id
    if fact_type is not None:
        need = need_by_fact_type.get(fact_type)
        if need is None:
            return None
        return need["id"]
    raise ValueError("query_producers 需提供 need_id 或 fact_type")


def query_producers(need_id=None, fact_type=None, platform=None, status=None, matrix_dir=None):
    """按信息需求取生产者链。

    返回该需求的生产者条目列表，每条含：
      producer_id、verdict（判定等级）、production_tier（生产层级）、platforms（运行平台）、
      runtime_guidance（运行指导）、invocation_profile（调用方式）、status、producer（生产者定义）。

    platform 非空时仅返回该平台可运行的条目；status 非空时按点亮状态过滤。
    matrix_dir 非空时从指定矩阵目录读取（缺省为全局矩阵目录）。
    只读：不写任何矩阵文件。
    """
    entries, producers, need_by_fact_type = load_matrix(matrix_dir)
    need_id = _resolve_need_id(need_id, fact_type, need_by_fact_type)

    result = []
    for e in entries:
        if e["need_id"] != need_id:
            continue
        if platform is not None and platform not in e["platforms"]:
            continue
        if status is not None and e["status"] != status:
            continue
        item = {
            "need_id": e["need_id"],
            "producer_id": e["producer_id"],
            "verdict": e["verdict"],
            "production_tier": e["production_tier"],
            "platforms": e["platforms"],
            "runtime_guidance": e["runtime_guidance"],
            "invocation_profile": e["invocation_profile"],
            "status": e["status"],
            "producer": producers.get(e["producer_id"]),
        }
        result.append(item)
    return result
