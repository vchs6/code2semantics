"""透读编排器 spec「透读编排循环」「按来源项目版本判定命中」「构造器缺席时只读降级」
「不可访问时直接报告」场景测试。"""
import pytest

from orchestrator import orchestrate
from repo_stub import InMemoryRepo
from constructor_stub import ConstructorStub


@pytest.fixture
def proj(tmp_path):
    """真实存在的项目目录（编排器按 spec 检查 isdir）。"""
    return str(tmp_path)


def _contract(project, **over):
    base = {"project": project, "facts": {"项目层": ["项目用途/领域", "入口"]}}
    base.update(over)
    return base


def _full_facts():
    return {
        "项目用途/领域": [{"_id": "e1", "name": "indicatif", "domain": "进度条库", "doc": "README.md"}],
        "入口": [{"_id": "e2", "entries": ["src/main.rs"]}],
    }


def _version_fn(v):
    return lambda project: v


# ---- 透读编排循环 ----

def test_缺口触发构造后满足契约(proj):
    repo = InMemoryRepo(seed={(proj, "v1"): {
        "项目用途/领域": [_full_facts()["项目用途/领域"][0]],
    }})
    def produce(needs):
        return {"入口": _full_facts()["入口"]} if "入口" in needs else {}
    ctor = ConstructorStub(produce=produce)
    out = orchestrate(_contract(proj, version="v1"), repo, ctor, version_fn=_version_fn("v1"))
    assert "error" not in out
    assert out["version"] == "v1"
    assert len(out["facts"]["项目层"]) == 2  # 命中 + 构造入库，统一装配


def test_构造产出入库并返回循环_不绕过仓库(proj):
    repo = InMemoryRepo()
    def produce(needs):
        return _full_facts()
    ctor = ConstructorStub(produce=produce)
    out = orchestrate(_contract(proj, version="v1"), repo, ctor, version_fn=_version_fn("v1"))
    # 产出经仓库写入；最终事实从仓库重读取得（不直接并入构造返回值）
    assert out["facts"]["项目层"]
    assert repo.read(proj, "v1") is not None


def test_构造无法补齐时终止不无限重试(proj):
    repo = InMemoryRepo()
    n_calls = {"n": 0}
    def produce(needs):
        n_calls["n"] += 1
        return {}  # 永不产出
    ctor = ConstructorStub(produce=produce)
    out = orchestrate(_contract(proj, version="v1"), repo, ctor, version_fn=_version_fn("v1"))
    assert n_calls["n"] == 1  # 只构造一轮即终止
    assert all(g["reason"] == "构造后仍缺失" for g in out["gaps"])


def test_每轮构造定向执行_仅含缺口(proj):
    repo = InMemoryRepo(seed={(proj, "v1"): {
        "项目用途/领域": [_full_facts()["项目用途/领域"][0]],
    }})
    seen = []
    def produce(needs):
        seen.append(set(needs))
        return {"入口": _full_facts()["入口"]}
    ctor = ConstructorStub(produce=produce)
    orchestrate(_contract(proj, version="v1"), repo, ctor, version_fn=_version_fn("v1"))
    assert seen == [{"入口"}]  # 构造任务仅含缺口类型，不含已满足的"项目用途/领域"


def test_构造器缺席只读降级(proj):
    repo = InMemoryRepo(seed={(proj, "v1"): {
        "项目用途/领域": [_full_facts()["项目用途/领域"][0]],
    }})
    ctor = ConstructorStub(available=False)
    out = orchestrate(_contract(proj, version="v1"), repo, ctor, version_fn=_version_fn("v1"))
    assert out["facts"]["项目层"]  # 命中项正常返回
    assert any(g["type"] == "入口" and "只读降级" in g["reason"] for g in out["gaps"])


# ---- 不可访问直接报告 ----

def test_项目不可访问直接报告(tmp_path):
    repo = InMemoryRepo()
    missing = str(tmp_path / "nonexistent")
    out = orchestrate(_contract(missing), repo, ConstructorStub(),
                      version_fn=_version_fn("v1"))
    assert "error" in out and "项目不可访问" in out["error"]


def test_仓库不可访问直接报告(proj):
    repo = InMemoryRepo(accessible=False)
    out = orchestrate(_contract(proj), repo, ConstructorStub(), version_fn=_version_fn("v1"))
    assert "error" in out and "仓库不可访问" in out["error"]


# ---- 版本语义 ----

def test_请求版本命中(proj):
    repo = InMemoryRepo(seed={(proj, "v1"): _full_facts()})
    out = orchestrate(_contract(proj, version="v1"), repo, ConstructorStub(available=False),
                      version_fn=_version_fn("v1"))
    assert out["version"] == "v1"
    assert out["version_fallback"] is False


def test_请求版本缺失回退当前版本并标注(proj):
    repo = InMemoryRepo(seed={(proj, "cur"): _full_facts()})
    out = orchestrate(_contract(proj, version="old"), repo, ConstructorStub(available=False),
                      version_fn=_version_fn("cur"))
    assert out["version"] == "cur"
    assert out["version_fallback"] is True


def test_本地文件夹按当前版本判定(proj):
    repo = InMemoryRepo()
    out = orchestrate(_contract(proj), repo, ConstructorStub(available=False),
                      project_root=proj, version_fn=_version_fn("cur"))
    assert out["version"] == "cur"
    assert out["version_fallback"] is False
