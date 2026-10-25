"""按需构造语义验证（TDD）：事实按契约请求按需构造并入库，非一次性全量获取；
同一事实的重复查询命中仓库不重复构造；仅缺失部分触发构造。"""
from catalog import FIELDS
from orchestrator import orchestrate
from sfrs.adapter import SFRSRepo


class CountingConstructor:
    """计数桩构造器：记录每次构造任务的类型集；为请求类型产出覆盖全部字段的实体。"""

    def __init__(self):
        self.calls = []

    def available(self):
        return True

    def build(self, needs):
        needs = set(needs)
        self.calls.append(needs)
        out = {}
        for t in needs:
            ent = {"_id": f"{t}:stub:1-1",
                   "evidence": {"file": "stub.md", "range": "1-1"}}
            for f in FIELDS.get(t, []):
                ent[f] = f"{t}.{f} 值"
            out[t] = [ent]
        return out


def _run(tmp_path, repo, constructor, types):
    contract = {"project": str(tmp_path),
                "facts": {"项目层": [{"fact_type": t} for t in types]}}
    return orchestrate(contract, repo, constructor, project_root=str(tmp_path),
                       version_fn=lambda p: "v-stub")


def test_按需构造_仅构造契约请求的类型(tmp_path):
    repo = SFRSRepo(db_path=tmp_path / "facts.db")
    ctor = CountingConstructor()
    out = _run(tmp_path, repo, ctor, ["项目用途/领域"])
    assert "error" not in out
    # 只构造了契约请求的一个类型，未全量获取其他类型
    assert ctor.calls == [{"项目用途/领域"}]
    types_in_output = {item["type"] for item in out["facts"]["项目层"]}
    assert types_in_output == {"项目用途/领域"}


def test_重复查询命中仓库_不重复构造(tmp_path):
    repo = SFRSRepo(db_path=tmp_path / "facts.db")
    ctor1 = CountingConstructor()
    out1 = _run(tmp_path, repo, ctor1, ["项目用途/领域"])
    assert ctor1.calls == [{"项目用途/领域"}]

    ctor2 = CountingConstructor()  # 全新构造器实例：同事实查询不得再触发构造
    out2 = _run(tmp_path, repo, ctor2, ["项目用途/领域"])
    assert ctor2.calls == []  # 命中仓库，零构造
    assert out2["facts"] == out1["facts"]  # 结果一致


def test_增量构造_只构造缺失的部分(tmp_path):
    repo = SFRSRepo(db_path=tmp_path / "facts.db")
    _run(tmp_path, repo, CountingConstructor(), ["项目用途/领域"])  # 已存类型 A

    ctor = CountingConstructor()
    out = _run(tmp_path, repo, ctor, ["项目用途/领域", "入口"])  # A 已存 + 入口 缺失
    # 仅缺失的 入口 触发构造；已存的 项目用途/领域 不重复构造
    assert ctor.calls == [{"入口"}]
    types_in_output = {item["type"] for item in out["facts"]["项目层"]}
    assert types_in_output == {"项目用途/领域", "入口"}
