"""构造器入口与端到端串联测试（任务 2.3/6.1）。

端到端：契约 + 矩阵桩 + 解析器桩（任务 6.1 用桩；真实矩阵+解析器链路由 Skill 侧验证）。
"""
import yaml

from constructor.constructor import construct  # noqa: E402
from info_parser.framework import ParseResult, ParserRegistry  # noqa: E402


def _matrix_stub(tmp_path):
    """最小矩阵桩：入口 有一个已点亮工具（X-stub_tool）。"""
    import yaml
    m = tmp_path / "matrix"
    m.mkdir()
    yaml.safe_dump({
        "schema_version": 1, "revision": 1,
        "entries": [
            {"need_id": "need.project.domain", "producer_id": "X-stub_tool",
             "verdict": "可完成", "production_tier": "工具直出", "platforms": ["linux"],
             "runtime_guidance": "", "status": "已点亮",
             "invocation_profile": {"command": "echo stub-output", "timeout_seconds": 10,
                                    "retries": 0, "output_type": "text", "parser_id": None},
             "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
            {"need_id": "need.project.entries", "producer_id": "X-stub_tool",
             "verdict": "可完成", "production_tier": "工具直出", "platforms": ["linux"],
             "runtime_guidance": "", "status": "已点亮",
             "invocation_profile": {"command": "echo stub-output", "timeout_seconds": 10,
                                    "retries": 0, "output_type": "text", "parser_id": None},
             "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
        ],
    }, open(m / "entries.yaml", "w", encoding="utf-8"))
    yaml.safe_dump({"schema_version": 1, "producers": [
        {"id": "X-stub_tool", "name": "stub", "kind": "external_tool", "scale": "小型",
         "languages": [], "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
    ]}, open(m / "producers.yaml", "w", encoding="utf-8"))
    yaml.safe_dump({"schema_version": 1, "identifier_note": "占位", "needs": [
        {"id": "need.project.entries", "layer": "项目层", "fact_type": "入口",
         "required_info": "bin target 清单",
         "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
        {"id": "need.project.domain", "layer": "项目层", "fact_type": "项目用途/领域",
         "required_info": "crate 名称与元数据",
         "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
    ]}, open(m / "info-needs.yaml", "w", encoding="utf-8"))
    return m


def _registry_with_stub():
    reg = ParserRegistry()
    def stub_parser(raw, profile):
        return ParseResult(items=[
            {"info_type": "cargo_package",
             "content": {"name": "stub", "version": "0.1.0", "edition": "2021",
                         "description": "stub crate", "readme": "README.md", "repository": None},
             "evidence": {"file": "Cargo.toml", "range": "1-5"},
             "source_tool": "X-stub_tool"},
        ])
    reg.register("X-stub_tool", stub_parser)
    return reg


def test_端到端_桩链路产出符合契约的事实集(tmp_path):
    m = _matrix_stub(tmp_path)
    contract = {"project": str(tmp_path), "facts": {"项目层": ["项目用途/领域", "不存在的事实"]}}
    out = construct(contract, project_root=str(tmp_path),
                    matrix_dir=m, parser_registry=_registry_with_stub(),
                    skip_exec=True)  # 桩解析器直接注入数据项，跳过真实工具执行
    # 契约要求的事实被构造（stub 产出 cargo_package → 合成项目用途/领域）
    assert out["facts"]["项目层"][0]["type"] == "项目用途/领域"
    # 目录外引用分列
    assert out["out_of_scope"] == ["不存在的事实"]
    # 已构造的事实不出现在 gaps；目录外引用也不进 gaps（分列）
    assert all(g["type"] != "项目用途/领域" for g in out["gaps"])
    assert all(g["type"] != "不存在的事实" for g in out["gaps"])


def test_同一生产者服务多个事实类型_信息数据项不重复(tmp_path):
    """复现缺陷：多个事实类型共用同一生产者时，解析器重复产出同一数据项，
    合成后字段内容不得重复。"""
    m = _matrix_stub(tmp_path)
    reg = ParserRegistry()
    def stub_parser(raw, profile):
        # 每次调用都返回 package + target 两类数据项（与真实 cargo metadata 解析器同构）
        return ParseResult(items=[
            {"info_type": "cargo_package",
             "content": {"name": "stub", "version": "0.1.0", "edition": "2021",
                         "description": "stub crate", "readme": "README.md", "repository": None},
             "evidence": {"file": "Cargo.toml", "range": "1-5"},
             "source_tool": "X-stub_tool"},
            {"info_type": "cargo_target",
             "content": {"name": "stub", "kind": ["lib"], "crate_types": ["lib"],
                         "src_path": "src/lib.rs"},
             "evidence": {"file": "src/lib.rs", "range": "1-1"},
             "source_tool": "X-stub_tool"},
        ])
    reg.register("X-stub_tool", stub_parser)
    contract = {"project": str(tmp_path), "facts": {"项目层": ["项目用途/领域", "入口"]}}
    out = construct(contract, project_root=str(tmp_path), matrix_dir=m,
                    parser_registry=reg, skip_exec=True)
    entries_fact = next(i for i in out["facts"]["项目层"] if i["type"] == "入口")
    assert len(entries_fact["fields"]["entries"]) == 1  # 不因两个事实类型各跑一次而重复


def test_同一轮构造内每工具仅执行一次_数据项服务多事实(tmp_path):
    """tasks 4.3：同一轮构造内同一工具仅执行一次，其数据项路由服务多个事实类型。"""
    import constructor.constructor as ctor_mod

    m = _matrix_stub(tmp_path)  # 项目用途/领域 与 入口 两条已点亮条目，共用 X-stub_tool
    reg = ParserRegistry()

    def stub_parser(raw, profile):
        # 一次执行返回 package + target 两类数据项（与真实 cargo metadata 解析器同构）
        return ParseResult(items=[
            {"info_type": "cargo_package",
             "content": {"name": "stub", "version": "0.1.0", "edition": "2021",
                         "description": "stub crate", "readme": "README.md", "repository": None},
             "evidence": {"file": "Cargo.toml", "range": "1-5"},
             "source_tool": "X-stub_tool"},
            {"info_type": "cargo_target",
             "content": {"name": "stub", "kind": ["lib"], "crate_types": ["lib"],
                         "src_path": "src/lib.rs"},
             "evidence": {"file": "src/lib.rs", "range": "1-1"},
             "source_tool": "X-stub_tool"},
        ])

    reg.register("X-stub_tool", stub_parser)
    contract = {"project": str(tmp_path), "facts": {"项目层": ["项目用途/领域", "入口"]}}

    calls = {"n": 0}
    real_execute = ctor_mod.execute

    def counting(profile, tool_id="unknown-tool", cwd=None):
        calls["n"] += 1
        return real_execute(profile, tool_id=tool_id, cwd=cwd)

    ctor_mod.execute = counting
    try:
        out = construct(contract, project_root=str(tmp_path), matrix_dir=m,
                        parser_registry=reg)
    finally:
        ctor_mod.execute = real_execute

    assert calls["n"] == 1  # 工具执行次数=1（不按事实类型重复调用）
    types = {i["type"] for i in out["facts"]["项目层"]}
    assert types == {"项目用途/领域", "入口"}  # 一次执行的数据项路由合成两类事实


def test_构造入口暴露信息需求清单(tmp_path):
    m = _matrix_stub(tmp_path)
    contract = {"project": str(tmp_path), "facts": {"项目层": ["项目用途/领域"]}}
    out = construct(contract, project_root=str(tmp_path), matrix_dir=m,
                    parser_registry=_registry_with_stub(), skip_exec=True)
    assert out["info_needs"]["needs"]  # 清单可从输出中取回（任务 2.3）
    assert out["info_needs"]["unmappable"] is not None


def test_不可访问项目直接报告(tmp_path):
    m = _matrix_stub(tmp_path)
    out = construct({"project": str(tmp_path / "nope"), "facts": {"项目层": ["入口"]}},
                    project_root=str(tmp_path / "nope"), matrix_dir=m,
                    parser_registry=_registry_with_stub())
    assert "error" in out
