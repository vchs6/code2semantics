"""待取值盘点测试（add-induction-batch-trigger 任务 1.1/1.2，TDD 先行）：

盘点函数按 design 决策 1：待取值字段集合 = 该事实类型在 FIELD_INFO_NEEDS 中
标记为归纳的字段中，本轮构造产出实体里值为空（缺失或 None）的字段；类型完全
无产出时返回该类型全部归纳字段（与既有整类型归纳路径等价）。
"""
from constructor.constructor import collect_induction_requests, pending_inductive_fields
from constructor.synthesis import FIELD_INFO_NEEDS, _is_inductive
from catalog import FIELDS


def _entity(direction, dep_type):
    return {"type": "模块间依赖", "fields": {"direction": direction, "type": dep_type},
            "evidence": {"file": "src/lib.rs", "range": "1-1"}}


def test_归纳标记表_模块间依赖type为归纳():
    # 依据 synthesis.py FIELD_INFO_NEEDS：type 字段为「依赖类型判定归纳」
    assert _is_inductive(FIELD_INFO_NEEDS["模块间依赖"]["type"])
    assert not _is_inductive(FIELD_INFO_NEEDS["模块间依赖"]["direction"])


def test_混合形态_空归纳字段进待取值集合():
    # direction 工具直出有值、type 全空 → 待取值集合恰为 ["type"]
    entities = [_entity("std::io::Write", None), _entity("crate::TermLike", None)]
    assert pending_inductive_fields("模块间依赖", entities) == ["type"]


def test_归纳字段已有值不进集合():
    entities = [_entity("std::io::Write", "调用"), _entity("crate::TermLike", None)]
    # 部分实体 type 已回填、部分为空 → 空位仍待取值；全部有值时为空集合
    assert pending_inductive_fields("模块间依赖", entities) == ["type"]
    assert pending_inductive_fields(
        "模块间依赖", [_entity("std::io::Write", "调用")]) == []


def test_非归纳字段缺失不进集合():
    # direction 非归纳字段即使为空也不属于待取值（其缺失走既有工具/合成缺口语义）
    entities = [{"type": "模块间依赖", "fields": {"direction": None, "type": None},
                 "evidence": None}]
    assert pending_inductive_fields("模块间依赖", entities) == ["type"]


def test_类型完全无产出_返回全部归纳字段():
    # 与既有整类型归纳路径等价：无实体时全部归纳字段待取值
    assert pending_inductive_fields("模块间依赖", []) == ["type"]
    all_ind = ["数据流"]
    assert pending_inductive_fields("数据流", []) == \
        ["source", "sink"]  # FIELD_INFO_NEEDS["数据流"] 两字段均归纳


def test_目录外或无字段表类型_空集合():
    assert pending_inductive_fields("不存在的事实", []) == []


# ---- 归纳请求收集（design 决策 2：两分支共用同一整组通道）----

def test_待取值集合为空不产生归纳请求():
    # 混合形态但归纳字段全部有值 → 不产出该类型的归纳请求
    facts = {"模块间依赖": [{"type": "模块间依赖",
                             "fields": {"direction": "std::io", "type": "调用"},
                             "evidence": None}]}
    assert collect_induction_requests(["模块间依赖"], facts, None) == []


def test_类型完全无产出_整类型路径fields为全目录字段():
    # 既有整类型归纳路径不变：fields = fact-catalog 全字段（非仅归纳字段）
    reqs = collect_induction_requests(["配置项"], {}, None)
    assert len(reqs) == 1
    assert reqs[0]["type"] == "配置项"
    assert reqs[0]["fields"] == list(FIELDS["配置项"])
    assert reqs[0]["guidance"]  # required_info 随请求下发


def test_混合形态空归纳字段_整组fields恰为待取值集合():
    facts = {"模块间依赖": [{"type": "模块间依赖",
                             "fields": {"direction": "std::io", "type": None},
                             "evidence": None}]}
    reqs = collect_induction_requests(["模块间依赖"], facts, None)
    assert len(reqs) == 1  # 一次整组请求，不逐字段拆分
    assert reqs[0]["fields"] == ["type"]
