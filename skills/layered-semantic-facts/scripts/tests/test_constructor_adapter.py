"""构造器适配器测试：把真实构造器接入查询流程编排器的 available()/build(needs) 接口。"""
from constructor_adapter import RealConstructorAdapter  # noqa: E402
from info_parser.framework import ParseResult, ParserRegistry  # noqa: E402


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


def _matrix_stub(tmp_path):
    import yaml
    m = tmp_path / "matrix"
    m.mkdir()
    yaml.safe_dump({
        "schema_version": 1, "revision": 1,
        "entries": [
            {"need_id": "need.project.domain", "producer_id": "X-stub_tool",
             "verdict": "可完成", "production_tier": "工具直出", "platforms": ["linux"],
             "runtime_guidance": "", "status": "已点亮",
             "invocation_profile": {"command": "echo x", "timeout_seconds": 10,
                                    "retries": 0, "output_type": "text", "parser_id": None},
             "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
        ],
    }, open(m / "entries.yaml", "w", encoding="utf-8"))
    yaml.safe_dump({"schema_version": 1, "producers": [
        {"id": "X-stub_tool", "name": "stub", "kind": "external_tool", "scale": "小型",
         "languages": [], "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
    ]}, open(m / "producers.yaml", "w", encoding="utf-8"))
    yaml.safe_dump({"schema_version": 1, "identifier_note": "占位", "needs": [
        {"id": "need.project.domain", "layer": "项目层", "fact_type": "项目用途/领域",
         "required_info": "crate 名称与元数据",
         "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
    ]}, open(m / "info-needs.yaml", "w", encoding="utf-8"))
    return m


def test_适配器available为真(tmp_path):
    adapter = RealConstructorAdapter(project_root=str(tmp_path), matrix_dir=_matrix_stub(tmp_path),
                                     parser_registry=_registry_with_stub())
    assert adapter.available() is True


def test_适配器build返回仓库形态事实(tmp_path):
    adapter = RealConstructorAdapter(project_root=str(tmp_path), matrix_dir=_matrix_stub(tmp_path),
                                     parser_registry=_registry_with_stub())
    produced = adapter.build({"项目用途/领域"})
    assert "项目用途/领域" in produced
    entity = produced["项目用途/领域"][0]
    assert entity["evidence"] == {"file": "Cargo.toml", "range": "1-5"}
    assert entity.get("name") == "stub"  # 实体为拍平形态（字段直接在实体上）


def test_适配器build无生产者返回空(tmp_path):
    adapter = RealConstructorAdapter(project_root=str(tmp_path), matrix_dir=_matrix_stub(tmp_path),
                                     parser_registry=_registry_with_stub())
    assert adapter.build({"配置项"}) == {}


def test_适配器暴露构造器声明缺口(tmp_path):
    """任务 3.1：适配层向编排器透出结构化缺口声明（类型级 + 字段级原因）。"""
    adapter = RealConstructorAdapter(project_root=str(tmp_path), matrix_dir=_matrix_stub(tmp_path),
                                     parser_registry=_registry_with_stub())
    adapter.build({"配置项"})  # 矩阵桩无配置项条目 → 类型级缺口
    gaps = adapter.declared_gaps()
    assert any(g["type"] == "配置项" and "reason" in g for g in gaps)
