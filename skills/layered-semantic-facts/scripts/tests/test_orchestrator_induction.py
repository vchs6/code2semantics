"""编排器归纳请求透传测试（tasks 7.4 / spec「语义归纳的请求与并入」）。

桩构造器模拟真实构造器行为：无工具直出数据项 → 产出结构化归纳请求；
预置归纳结果 → 代理归纳后并入事实集。断言：
  1. 未覆盖请求随最终响应暴露（induction_requests）；
  2. 已归纳事实并入输出、不再暴露请求；
  3. 待归纳类型 gap 原因标"待归纳"（与"构造后仍缺失"语义分层）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import orchestrate
from repo_stub import InMemoryRepo
from versioning import current_version

REQUESTS = [
    {"type": "配置项", "fields": ["name", "purpose", "default"],
     "guidance": "配置项清单、用途与缺省值归纳"},
    {"type": "数据流", "fields": ["source", "sink"],
     "guidance": "变量级数据流路径归纳"},
]


class _InductionConstructor:
    """桩构造器：build 返回预置归纳结果并清除对应请求，其余请求保留暴露。"""

    def __init__(self, requests, induced=None):
        self._requests = list(requests)
        self._induced = dict(induced or {})

    def available(self):
        return True

    def declared_gaps(self):
        return []

    def induction_requests(self):
        return [dict(r) for r in self._requests]

    def build(self, needs):
        produced = {}
        for t in sorted(needs):
            if t in self._induced:
                produced[t] = self._induced.pop(t)
                self._requests = [r for r in self._requests if r["type"] != t]
        return produced


def _run(constructor):
    contract = {"project": os.getcwd(),
                "facts": {"项目层": [{"fact_type": "配置项"},
                                     {"fact_type": "数据流"}]}}
    return orchestrate(contract, InMemoryRepo(), constructor,
                       version_fn=lambda p: "v-test")


def _fact_types(out):
    return {it["type"] for items in (out.get("facts") or {}).values()
            for it in items}


def _gap_by_type(out, t):
    return next((g for g in out.get("gaps", []) if g["type"] == t), None)


def test_未覆盖归纳请求随响应暴露且gap标注待归纳():
    out = _run(_InductionConstructor(REQUESTS))
    reqs = out.get("induction_requests")
    assert reqs and {r["type"] for r in reqs} == {"配置项", "数据流"}
    req = next(r for r in reqs if r["type"] == "配置项")
    assert req["fields"] == ["name", "purpose", "default"]
    assert "缺省值" in req["guidance"]
    for t in ("配置项", "数据流"):
        g = _gap_by_type(out, t)
        assert g and g["reason"] == "待归纳", f"{t} 缺口应标待归纳：{g}"
    assert not (_fact_types(out) & {"配置项", "数据流"})  # 未归纳不编造


def test_代理归纳后并入事实集且已覆盖请求不再暴露():
    induced = {"配置项": [{"configs": [{"name": "SM_BINDING", "purpose": "端口绑定配置",
                                        "default": "127.0.0.1:0"}],
                           "evidence": {"file": "src/lib.rs", "range": "10-12"}}]}
    out = _run(_InductionConstructor(REQUESTS, induced=induced))
    assert "配置项" in _fact_types(out)  # 归纳结果并入事实集
    reqs = out.get("induction_requests") or []
    assert {r["type"] for r in reqs} == {"数据流"}  # 已覆盖请求不再暴露
    assert _gap_by_type(out, "配置项") is None  # 已并入不再报缺口
    g = _gap_by_type(out, "数据流")
    assert g and g["reason"] == "待归纳"
