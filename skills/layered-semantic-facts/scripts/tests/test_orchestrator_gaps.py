"""编排器缺口透传测试（任务 3.1，design 决策 5；spec「构造无法补齐时终止」）。

构造器声明的结构化缺口（字段/类型级原因）为权威：已声明缺口不参与后续轮次
判缺与构造触发（含差距段字段的节点不再触发重复构造）；最终 gaps 使用精确原因。
"""
from constructor_stub import ConstructorStub
from orchestrator import orchestrate
from repo_stub import InMemoryRepo


def _contract(facts, project):
    return {"project": project, "facts": {"项目层": facts}}


def test_类型级缺口透传_原因精确且只构造一次(tmp_path):
    calls = {"n": 0}
    declared = [{"type": "配置项", "reason": "矩阵中无可用生产者条目"}]

    def produce(needs):
        calls["n"] += 1
        return {"入口": [{"_id": "e1", "entries": [{"name": "x"}]}]}

    ctor = ConstructorStub(available=True, produce=produce,
                           declared_gaps=declared)
    out = orchestrate(_contract(["配置项", "入口"], str(tmp_path)), InMemoryRepo(), ctor)
    assert calls["n"] == 1  # 配置项无产出 → 终止，不重试
    gap = next(g for g in out["gaps"] if g["type"] == "配置项")
    assert gap["reason"] == "矩阵中无可用生产者条目"  # 精确原因，非"构造后仍缺失"


def test_字段级缺口不重触发构造(tmp_path):
    calls = {"n": 0}
    declared = [{"type": "构建与运行形态", "field": "run",
                 "reason": "构造后仍缺失（无对应信息数据项产出）"}]

    def produce(needs):
        calls["n"] += 1
        return {"构建与运行形态": [{"_id": "b1", "build": "cargo build",
                                  "deployment": "库"}]}

    ctor = ConstructorStub(available=True, produce=produce,
                           declared_gaps=declared)
    out = orchestrate(_contract(["构建与运行形态"], str(tmp_path)), InMemoryRepo(), ctor)
    assert calls["n"] == 1  # run 字段已声明缺口 → 第二轮不再触发构造
    assert out["gaps"] == [{"type": "构建与运行形态", "field": "run",
                            "reason": "构造后仍缺失（无对应信息数据项产出）"}]
    item = out["facts"]["项目层"][0]
    names = {c["name"] for c in item["children"]}
    assert {"build", "deployment"} <= names  # 已产出字段正常返回


def test_节点寻址契约的判缺范围(tmp_path):
    """path 请求的子树节点内容参与递归判缺；构造按自顶向下补齐后缺口消失。"""
    def produce(needs):
        return {"模块划分": [{"_id": "m0", "modules": ["a"]}],
                "模块职责": [{"_id": "mod_a", "path": "x", "responsibility": "r",
                              "capabilities": ["c"]}]}

    ctor = ConstructorStub(available=True, produce=produce)
    contract = {"project": str(tmp_path),
                "facts": {"项目层": [{"fact_type": "模块划分", "path": ["modules"]}]}}
    out = orchestrate(contract, InMemoryRepo(), ctor,
                      subtree_map={"模块划分": {"modules": "模块职责"}})
    assert out["gaps"] == []  # 已请求路径上的字段均已产出
    assert out["facts"]["项目层"]
