"""代理归纳路径测试（构造器增量 7.3，TDD 先行）：

- 无工具直出数据项、但有已点亮 A-*（智能体兜底/项目分析Skill）生产者的事实类型
  → construct 产出结构化 induction_requests（不编造、不中断）；
- 提供 inducer 钩子时，归纳结果按契约并入 facts（仅目录内类型、证据透传）；
- 未被 inducer 覆盖的请求保持为「待代理归纳」缺口，随输出暴露。
"""
import json
import jsonschema

from constructor.constructor import construct
from constructor.fact_synthesis import assemble_output
from constructor_adapter import default_parser_registry
from layout import SKILL_ROOT, resolve_asset


def _output_schema():
    return json.loads(
        (resolve_asset(SKILL_ROOT, "schema") / "output.schema.json").read_text("utf-8"))


def _construct(contract, tmp_path, **kw):
    return construct(contract, parser_registry=default_parser_registry(),
                     skip_exec=True, **kw)


def _no_tool_contract(tmp_path):
    """临时项目（无源码工具可产出目标事实）+ 查询配置项（仅 A-* 生产者可满足语义部分）。"""
    proj = tmp_path / "proj"
    proj.mkdir()
    return {"project": str(proj), "facts": {"项目层": [{"fact_type": "配置项"}]}}


def test_无inducer时产出归纳请求与待归纳缺口(tmp_path):
    out = _construct(_no_tool_contract(tmp_path), tmp_path)
    assert "error" not in out
    assert out.get("induction_requests"), "配置项应有归纳请求"
    req = out["induction_requests"][0]
    assert req["type"] == "配置项"
    assert set(req["fields"]) >= {"configs"}  # fact-catalog 字段随请求下发
    assert req["guidance"]  # 信息需求 guidance（required_info）随请求下发
    assert any(g["type"] == "配置项" and "待代理归纳" in g["reason"] for g in out["gaps"])
    jsonschema.Draft7Validator(_output_schema()).validate(out)


def test_inducer归纳结果并入facts(tmp_path):
    def inducer(requests):
        assert [r["type"] for r in requests] == ["配置项"]
        return {"配置项": [{"fields": {"configs": [{"name": "RUST_LOG", "purpose": "日志级别"}]},
                        "evidence": None}]}

    out = _construct(_no_tool_contract(tmp_path), tmp_path, inducer=inducer)
    assert "error" not in out
    assert out["facts"]["项目层"], "归纳事实应并入输出"
    conf = [i for i in out["facts"]["项目层"] if i["type"] == "配置项"]
    assert conf and conf[0]["fields"]["configs"] == \
        [{"name": "RUST_LOG", "purpose": "日志级别"}]
    # construct 层事实条目为 {type, fields, evidence} 中间形态；响应的 children
    # 形态由编排器合成（最终响应 schema 校验在 e2e 覆盖），此处断言中间形态完整。
    assert set(conf[0]) == {"type", "fields", "evidence"}
    assert out.get("induction_requests") == []  # 已被覆盖的请求不再暴露


def test_inducer返回目录外类型被拒(tmp_path):
    def inducer(requests):
        return {"不存在的事实": [{"fields": {"x": 1}}]}

    out = _construct(_no_tool_contract(tmp_path), tmp_path, inducer=inducer)
    assert "error" not in out
    assert not (out.get("facts") or {}).get("项目层")
    assert out.get("induction_requests")  # 请求保留（不被非法归纳顶替）


def test_无A生产者的缺失类型仍是普通缺口(tmp_path):
    contract = {"project": str(tmp_path / "proj"), "facts": {"事实层": [{"fact_type": "数据流"}]}}
    (tmp_path / "proj").mkdir()
    out = construct(contract, skip_exec=True)
    assert "error" not in out
    assert not out.get("induction_requests")  # 数据流 A-* 判不可完成 → 无归纳请求
    assert any(g["type"] == "数据流" for g in out["gaps"])


# ---- 混合形态：类型有工具直出产出、归纳字段空缺 → 待取值整组触发 ----

def _mixed_contract(tmp_path):
    """临时 Rust 项目：src/lib.rs 含 use 声明（H-grep 直出依赖方向，type 归纳字段留空）。"""
    proj = tmp_path / "proj"
    (proj / "src").mkdir(parents=True)
    (proj / "src" / "lib.rs").write_text(
        "use std::io::Write;\nuse crate::term_like::TermLike;\n", encoding="utf-8")
    return {"project": str(proj), "facts": {"模块层": [{"fact_type": "模块间依赖"}]}}


def test_混合形态空归纳字段触发整组归纳请求(tmp_path):
    out = construct(_mixed_contract(tmp_path), parser_registry=default_parser_registry())
    assert "error" not in out
    deps = [i for i in out["facts"]["模块层"] if i["type"] == "模块间依赖"]
    assert deps and all(d["fields"]["direction"] for d in deps)  # 工具直出方向
    assert all(d["fields"]["type"] is None for d in deps)  # 归纳字段空缺
    reqs = out.get("induction_requests") or []
    assert len(reqs) == 1, f"应恰有一条整组归纳请求：{reqs}"
    req = reqs[0]
    assert req["type"] == "模块间依赖"
    assert req["fields"] == ["type"]  # 待取值字段集合，非全字段、不逐字段拆分
    assert req["guidance"]  # 依据信息随请求下发


def test_混合形态归纳请求确定性(tmp_path):
    contract = _mixed_contract(tmp_path)  # 同一项目构造两次，请求应一致
    a = construct(contract, parser_registry=default_parser_registry())
    b = construct(contract, parser_registry=default_parser_registry())
    assert a["induction_requests"] == b["induction_requests"]


def test_混合形态inducer整组返回回填实体空字段(tmp_path):
    def inducer(requests):
        assert [r["type"] for r in requests] == ["模块间依赖"]
        assert requests[0]["fields"] == ["type"]
        return {"模块间依赖": [{"fields": {"type": "调用"}}]}

    out = construct(_mixed_contract(tmp_path), parser_registry=default_parser_registry(),
                    inducer=inducer)
    assert "error" not in out
    deps = [i for i in out["facts"]["模块层"] if i["type"] == "模块间依赖"]
    assert deps and all(d["fields"]["type"] == "调用" for d in deps)  # 回填到既有实体
    assert out.get("induction_requests") == []  # 已覆盖的请求不再暴露
    assert not any(g["type"] == "模块间依赖" for g in out["gaps"])  # 不再报该类型缺口


def test_混合形态归纳未回填时请求保持暴露(tmp_path):
    def inducer(requests):
        # 归纳方确认了类型但未给出任何可回填值（字段值为 None）
        return {"模块间依赖": [{"fields": {"type": None}}]}

    out = construct(_mixed_contract(tmp_path), parser_registry=default_parser_registry(),
                    inducer=inducer)
    assert "error" not in out
    deps = [i for i in out["facts"]["模块层"] if i["type"] == "模块间依赖"]
    assert all(d["fields"]["type"] is None for d in deps)  # 未回填，不编造
    reqs = out.get("induction_requests") or []  # 未覆盖的请求保持暴露
    assert reqs and reqs[0]["type"] == "模块间依赖" and reqs[0]["fields"] == ["type"]


def test_混合形态归纳无效返回被拒收请求保留(tmp_path):
    def inducer(requests):
        # 目录外类型与未被请求类型的返回均应拒收；未被顶替的请求保留
        return {"模块间依赖": [{"fields": {"type": "调用"}}],
                "不存在的事实": [{"fields": {"x": 1}}]}

    out = construct(_mixed_contract(tmp_path), parser_registry=default_parser_registry(),
                    inducer=inducer)
    assert "error" not in out
    deps = [i for i in out["facts"]["模块层"] if i["type"] == "模块间依赖"]
    assert all(d["fields"]["type"] == "调用" for d in deps)  # 合法回填生效
    assert not (out.get("facts") or {}).get("不存在的事实")  # 目录外拒收
    assert out.get("induction_requests") == []  # 合法类型的请求已被覆盖
