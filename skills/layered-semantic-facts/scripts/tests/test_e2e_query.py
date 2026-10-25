"""端到端联通测试（任务 4.2）：真实矩阵 + 真实构造器适配层 + 内存仓库桩。

节点定位契约查询项目层 → 下一级返回（含子树标注）→ 以子树节点续查（命中仓库，
不重复构造）→ gaps 精确原因（含差距段字段级）；输出通过 output.schema.json 校验。
"""
import json

import jsonschema
import pytest

from layout import SKILL_ROOT, resolve_asset

REPO_ROOT = SKILL_ROOT.parents[1]
INDICATIF = REPO_ROOT.parent / "sm-test" / "source" / "indicatif"

pytestmark = pytest.mark.skipif(
    not INDICATIF.exists(), reason="本地无 indicatif 测试项目")

_SCHEMA = json.loads(
    (resolve_asset(SKILL_ROOT, "schema") / "output.schema.json").read_text("utf-8"))


class _HybridConstructor:
    """真实构造器适配层为主，模块层子树以桩补齐（演示续查流程；真实数据仍来自适配层）。"""

    def __init__(self, real):
        self._real = real

    def available(self):
        return True

    def declared_gaps(self):
        return [g for g in self._real.declared_gaps() if g["type"] not in ("模块划分",)]

    def build(self, needs):
        produced = self._real.build(needs)
        if "模块划分" in needs:
            produced.setdefault("模块划分", [{
                "_id": "m0", "modules": ["lib", "utils"],
                "evidence": {"file": "src/lib.rs", "range": "1-10"}}])
        if "模块职责" in needs:
            produced.setdefault("模块职责", [
                {"_id": "mod_lib", "path": "src/lib.rs", "responsibility": "公共入口",
                 "capabilities": ["draw"], "evidence": {"file": "src/lib.rs", "range": "1-10"}},
                {"_id": "mod_utils", "path": "src/utils.rs", "responsibility": "工具函数",
                 "capabilities": ["u1"], "evidence": {"file": "src/utils.rs", "range": "1-5"}}])
        return produced


def test_模块层混合形态归纳回填端到端_字段级gap收敛(tmp_path):
    """任务 4.1：真实构造器 + inducer 桩整组返回 → 回填既有实体，
    编排器覆盖比对的字段级 gap（模块间依赖.type）收敛为 0；inducer 缺席时显式暴露。"""
    from constructor_adapter import RealConstructorAdapter
    from orchestrator import orchestrate
    from repo_stub import InMemoryRepo
    from versioning import current_version

    contract = {"project": str(INDICATIF),
                "facts": {"模块层": [{"fact_type": "模块间依赖"}]}}
    repo = InMemoryRepo()

    def inducer(requests):
        assert [r["type"] for r in requests] == ["模块间依赖"]
        assert requests[0]["fields"] == ["type"]
        return {"模块间依赖": [{"fields": {"type": "调用"}}]}  # 桩值，验证回填管线

    out = orchestrate(contract, repo, RealConstructorAdapter(INDICATIF, inducer=inducer),
                      version_fn=current_version)
    assert "error" not in out
    jsonschema.Draft7Validator(_SCHEMA).validate(out)
    dep = next(i for i in out["facts"]["模块层"] if i["type"] == "模块间依赖")
    type_child = next(c for c in dep["children"] if c["name"] == "type")
    assert type_child.get("value") == "调用"  # 归纳值已回填
    field_gaps = [g for g in out["gaps"]
                  if g["type"] == "模块间依赖" and g.get("field") == "type"]
    assert field_gaps == []  # 字段级 gap 收敛为 0

    # inducer 缺席：type 字段无值 → 字段级 gap 显式暴露（缺口不隐藏）
    out2 = orchestrate(contract, InMemoryRepo(),
                       RealConstructorAdapter(INDICATIF), version_fn=current_version)
    assert "error" not in out2
    gap = next(g for g in out2["gaps"]
               if g["type"] == "模块间依赖" and g.get("field") == "type")
    assert gap["reason"]  # 显式原因
    reqs = out2.get("induction_requests") or []
    assert reqs and reqs[0]["type"] == "模块间依赖"  # 整组归纳请求随响应暴露


def test_节点定位契约_端到端_下一级返回与单次构造(tmp_path, monkeypatch):
    sys_path_setup = __import__("constructor_adapter")  # 确保 scripts 在 path（conftest 已注入）
    import constructor.constructor as ctor_mod
    from constructor_adapter import RealConstructorAdapter
    from orchestrator import orchestrate
    from repo_stub import InMemoryRepo
    from versioning import current_version

    calls = {"n": 0}
    real_execute = ctor_mod.execute

    def counting(profile, tool_id="unknown-tool", cwd=None):
        if "cargo metadata" in (profile or {}).get("command", ""):
            calls["n"] += 1
        return real_execute(profile, tool_id=tool_id, cwd=cwd)

    monkeypatch.setattr(ctor_mod, "execute", counting)

    contract = {"project": str(INDICATIF), "facts": {"项目层": [
        {"fact_type": "项目用途/领域"}, {"fact_type": "入口"},
        {"fact_type": "外部依赖"}, {"fact_type": "构建与运行形态"},
        {"fact_type": "模块划分"}, {"fact_type": "配置项"},
    ]}}
    subtree_map = {"模块划分": {"modules": "模块职责"}}
    repo = InMemoryRepo()
    ctor = _HybridConstructor(RealConstructorAdapter(project_root=str(INDICATIF)))
    out = orchestrate(contract, repo, ctor,
                      version_fn=current_version, subtree_map=subtree_map)

    assert "error" not in out
    jsonschema.Draft7Validator(_SCHEMA).validate(out)  # 输出通过 output-schema 校验

    types = {i["type"] for i in out["facts"]["项目层"]}
    assert {"项目用途/领域", "入口", "外部依赖", "构建与运行形态", "模块划分"} <= types
    # 下一级形态：children 标注；模块划分的 modules 为子树节点（内容不返回）
    module_item = next(i for i in out["facts"]["项目层"] if i["type"] == "模块划分")
    children = {c["name"]: c for c in module_item["children"]}
    assert children["modules"]["is_subtree"] is True and "value" not in children["modules"]
    entry_item = next(i for i in out["facts"]["项目层"] if i["type"] == "入口")
    assert all(c["is_subtree"] is False and "value" in c for c in entry_item["children"])

    # gaps 精确原因：H-ast_grep 解析器注册后（add-info-parser 第 5 阶段），配置项
    # 缺口下移到工具执行环节，为结构化工具失败（类型级）；构建与运行形态为字段级
    gap_by_type = {g["type"]: g for g in out["gaps"]}
    assert "工具失败" in gap_by_type["配置项"]["reason"]
    assert gap_by_type["构建与运行形态"].get("field") == "run"

    # 差距段字段不再触发重复构造：cargo metadata 全程仅执行 1 次
    assert calls["n"] == 1

    # 以子树节点续查：命中仓库（构造计数不增），输出子树节点的下一级（模块职责）
    contract2 = {"project": str(INDICATIF), "facts": {"项目层": [
        {"fact_type": "模块划分", "path": ["modules"]}]}}
    out2 = orchestrate(contract2, repo, ctor,
                       version_fn=current_version, subtree_map=subtree_map)
    assert calls["n"] == 1  # 续查命中仓库，不触发构造
    assert "error" not in out2
    jsonschema.Draft7Validator(_SCHEMA).validate(out2)
    types2 = {i["type"] for items in out2["facts"].values() for i in items}
    assert "模块职责" in types2  # 子树节点续查返回其下一级（按 catalog 层归组）
    assert out2["gaps"] == []
