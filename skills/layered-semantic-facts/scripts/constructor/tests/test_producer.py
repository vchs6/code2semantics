"""生产者选择与解析器调用测试（任务 4.1/4.2，矩阵桩 + 解析器桩）。"""
import yaml

from constructor.producer import call_parser, select_producers  # noqa: E402
from info_parser.framework import ParseResult, ParserRegistry  # noqa: E402


def _matrix_stub(tmp_path):
    """最小矩阵桩：入口 有一个已点亮工具（X-stub_tool）+ 一个兜底（A-stub）。"""
    m = tmp_path / "matrix"
    m.mkdir()
    yaml.safe_dump({
        "schema_version": 1, "revision": 1,
        "entries": [
            {"need_id": "need.project.entries", "producer_id": "X-stub_tool",
             "verdict": "可完成", "production_tier": "工具直出", "platforms": ["linux"],
             "runtime_guidance": "", "status": "已点亮",
             "invocation_profile": {"command": "echo stub-output", "timeout_seconds": 10,
                                    "retries": 0, "output_type": "text", "parser_id": None},
             "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
            {"need_id": "need.project.entries", "producer_id": "A-stub",
             "verdict": "不可完成", "production_tier": "智能体兜底", "platforms": ["linux"],
             "runtime_guidance": "", "status": "未点亮",
             "invocation_profile": {"command": None, "timeout_seconds": None, "retries": None,
                                    "output_type": None, "parser_id": None},
             "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
        ],
    }, open(m / "entries.yaml", "w", encoding="utf-8"))
    yaml.safe_dump({"schema_version": 1, "producers": [
        {"id": "X-stub_tool", "name": "stub", "kind": "external_tool", "scale": "小型",
         "languages": [], "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
        {"id": "A-stub", "name": "stub agent", "kind": "agent", "scale": None,
         "languages": [], "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
    ]}, open(m / "producers.yaml", "w", encoding="utf-8"))
    yaml.safe_dump({"schema_version": 1, "identifier_note": "占位", "needs": [
        {"id": "need.project.entries", "layer": "项目层", "fact_type": "入口",
         "required_info": "bin target 清单",
         "evidence": {"source": "README.md", "line_start": 1, "line_end": 2}},
    ]}, open(m / "info-needs.yaml", "w", encoding="utf-8"))
    return m


def test_已点亮且解析器已实现的条目可用(tmp_path):
    m = _matrix_stub(tmp_path)
    reg = ParserRegistry()
    reg.register("X-stub_tool", lambda raw, profile: ParseResult(items=[]))
    usable, unavailable = select_producers("入口", m, reg)
    assert [u["tool_id"] for u in usable] == ["X-stub_tool"]
    assert unavailable == []


def test_解析器未实现的条目不可用(tmp_path):
    m = _matrix_stub(tmp_path)
    usable, unavailable = select_producers("入口", m, ParserRegistry())  # 空 registry
    assert usable == []
    assert any(u["tool_id"] == "X-stub_tool" and "解析器未实现" in u["reason"] for u in unavailable)


def test_矩阵外无生产者进gaps(tmp_path):
    m = _matrix_stub(tmp_path)
    usable, unavailable = select_producers("配置项", m, ParserRegistry())
    assert usable == []
    assert unavailable == []  # 矩阵中该需求无条目 → 调用方按"矩阵外"进 gaps


def test_兜底层不可完成条目不被选用(tmp_path):
    m = _matrix_stub(tmp_path)
    reg = ParserRegistry()
    usable, _ = select_producers("入口", m, reg)
    assert all(u["tool_id"] != "A-stub" for u in usable)


def test_只读矩阵(tmp_path):
    m = _matrix_stub(tmp_path)
    before = (m / "entries.yaml").read_text("utf-8")
    reg = ParserRegistry()
    reg.register("X-stub_tool", lambda raw, profile: ParseResult(items=[]))
    select_producers("入口", m, reg)
    assert (m / "entries.yaml").read_text("utf-8") == before


def test_解析器调用返回数据项(tmp_path):
    reg = ParserRegistry()
    reg.register("X-stub_tool", lambda raw, profile: ParseResult(items=[{"k": "v"}]))
    result = call_parser("X-stub_tool", "raw", {}, reg)
    assert result.items == [{"k": "v"}]


def test_解析器缺失_调用返回未实现失败(tmp_path):
    result = call_parser("no-such", "raw", {}, ParserRegistry())
    assert not result.ok
    assert "解析器未实现" in result.failure.reason
