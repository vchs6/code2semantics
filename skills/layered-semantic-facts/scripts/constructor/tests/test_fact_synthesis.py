"""事实合成与输出组装测试（任务 5.1/5.2，spec「事实合成与证据传递」「缺口显式与不编造」）。"""
from constructor.fact_synthesis import assemble_output, synthesize_facts  # noqa: E402


def _info_items():
    return [
        {"info_type": "cargo_package",
         "content": {"name": "indicatif", "version": "0.18.6", "edition": "2021",
                     "rust_version": "1.85", "description": "A progress bar library",
                     "readme": "README.md", "repository": "https://example.com"},
         "evidence": {"file": "Cargo.toml", "range": "1-14"},
         "source_tool": "X-cargo_metadata"},
        {"info_type": "cargo_target",
         "content": {"name": "indicatif", "kind": ["lib"], "crate_types": ["lib"],
                     "src_path": "src/lib.rs"},
         "evidence": {"file": "src/lib.rs", "range": "1-1"},
         "source_tool": "X-cargo_metadata"},
        {"info_type": "cargo_dependency",
         "content": {"name": "console", "req": "^0.16.4", "kind": "normal", "optional": False},
         "evidence": {"file": "Cargo.toml", "range": "16-16"},
         "source_tool": "X-cargo_metadata"},
    ]


def test_证据自信息数据项传递():
    facts = synthesize_facts(["项目用途/领域"], _info_items())
    entry = facts["项目用途/领域"][0]
    assert entry["evidence"] == {"file": "Cargo.toml", "range": "1-14"}
    assert entry["fields"]["name"] == "indicatif"
    assert entry["fields"]["domain"] == "A progress bar library"


def test_证据不新增不伪造_合成后无额外证据源():
    facts = synthesize_facts(["入口"], _info_items())
    entry = facts["入口"][0]
    # 入口事实的证据来自 cargo_target 数据项（lib target）
    assert entry["evidence"] == {"file": "src/lib.rs", "range": "1-1"}


def test_契约未要求的事实不合成():
    facts = synthesize_facts(["项目用途/领域"], _info_items())
    assert "外部依赖" not in facts


def test_信息数据项为空的事实不合成():
    facts = synthesize_facts(["配置项"], [])  # 无任何配置项信息数据项
    assert "配置项" not in facts


def test_模块划分_由module_decl数据项合成():
    items = [
        {"info_type": "module_decl", "content": {"name": "draw_target", "visibility": "private"},
         "evidence": {"file": "src/lib.rs", "range": "250-250"}, "source_tool": "H-grep"},
        {"info_type": "module_decl", "content": {"name": "style", "visibility": "public"},
         "evidence": {"file": "src/lib.rs", "range": "260-260"}, "source_tool": "H-grep"},
    ]
    facts = synthesize_facts(["模块划分"], items)
    fact = facts["模块划分"][0]
    assert fact["fields"]["modules"] == [
        {"name": "draw_target", "visibility": "private", "declared_in": "src/lib.rs"},
        {"name": "style", "visibility": "public", "declared_in": "src/lib.rs"},
    ]
    # 证据自数据项传递，不新增
    assert fact["evidence"] == {"file": "src/lib.rs", "range": "250-250"}


def test_模块划分_无module_decl数据项不合成():
    facts = synthesize_facts(["模块划分"], [])
    assert facts == {}


# ---- 符号层合成规则 ----

def _symbol_items():
    return [
        {"info_type": "symbol_def",
         "content": {"name": "helper", "kind": "function", "signature": "fn helper(n: u32)",
                     "visibility": None},
         "evidence": {"file": "src/lib.rs", "range": "13-15"}, "source_tool": "X-ctags"},
        {"info_type": "symbol_def",
         "content": {"name": "Widget", "kind": "struct",
                     "fields": [{"name": "w", "type": "u32"}]},
         "evidence": {"file": "src/lib.rs", "range": "1-1"}, "source_tool": "X-ctags"},
        {"info_type": "symbol_relation",
         "content": {"relation": "implement", "source": "Widget", "target": "Runner"},
         "evidence": {"file": "src/lib.rs", "range": "5-11"}, "source_tool": "H-ast_grep"},
        {"info_type": "symbol_intent",
         "content": {"symbol": "helper", "intent": "helper normalizes n before use"},
         "evidence": {"file": "src/lib.rs", "range": "9-10"}, "source_tool": "H-grep"},
    ]


def test_符号层_公共接口合成_证据传递():
    facts = synthesize_facts(["公共接口"], _symbol_items())
    f = facts["公共接口"][0]
    assert f["fields"] == {"signature": "fn helper(n: u32)", "visibility": None,
                           "module": "src/lib.rs"}
    assert f["evidence"] == {"file": "src/lib.rs", "range": "13-15"}


def test_符号层_类型定义合成():
    facts = synthesize_facts(["类型定义"], _symbol_items())
    f = facts["类型定义"][0]
    assert f["fields"] == {"kind": "struct", "description": None,
                           "fields": [{"name": "w", "type": "u32"}]}
    assert f["evidence"] == {"file": "src/lib.rs", "range": "1-1"}


def test_符号层_符号关系与意图声明合成():
    rel = synthesize_facts(["符号关系"], _symbol_items())["符号关系"][0]
    assert rel["fields"] == {"relation": "implement", "target": "Runner",
                             "module": "src/lib.rs"}
    intent = synthesize_facts(["意图声明"], _symbol_items())["意图声明"][0]
    assert intent["fields"] == {"intent": "helper normalizes n before use"}
    assert intent["evidence"] == {"file": "src/lib.rs", "range": "9-10"}


def test_符号层_类型定义数据项不混入公共接口():
    facts = synthesize_facts(["公共接口"], _symbol_items())
    assert all(f["fields"]["signature"] for f in facts["公共接口"])


# ---- 事实层合成规则 ----

def _fact_items():
    return [
        {"info_type": "call_relation",
         "content": {"caller": "Widget::run", "callee": "helper", "direction": "outgoing",
                     "condition": None},
         "evidence": {"file": "src/lib.rs", "range": "7-7"}, "source_tool": "H-trace_callees"},
        {"info_type": "call_condition",
         "content": {"caller": None, "callee": "helper", "condition_kind": "branch",
                     "condition_pattern": "self.w > 0"},
         "evidence": {"file": "src/lib.rs", "range": "7-9"}, "source_tool": "H-ast_grep"},
        {"info_type": "lifecycle_event",
         "content": {"resource": "conn", "op": "create"},
         "evidence": {"file": "src/lib.rs", "range": "18-18"}, "source_tool": "H-ast_grep"},
        {"info_type": "error_handling",
         "content": {"op": "throw", "error_expr": '"bad state"'},
         "evidence": {"file": "src/lib.rs", "range": "20-20"}, "source_tool": "H-ast_grep"},
        {"info_type": "usage_contract_clue",
         "content": {"symbol": "Widget", "clue_kind": "precondition",
                     "text": "must be non-zero"},
         "evidence": {"file": "src/lib.rs", "range": "2-3"}, "source_tool": "H-grep"},
        {"info_type": "usage_contract_clue",
         "content": {"symbol": "Widget", "clue_kind": "guarantee",
                     "text": "width preserved"},
         "evidence": {"file": "src/lib.rs", "range": "5-6"}, "source_tool": "H-grep"},
        {"info_type": "element_structure",
         "content": {"symbol": "n", "control_flow_kind": "match"},
         "evidence": {"file": "src/lib.rs", "range": "14-14"}, "source_tool": "H-ast_grep"},
    ]


def test_事实层_调用关系_含条件线索():
    facts = synthesize_facts(["调用关系"], _fact_items())["调用关系"]
    assert {"caller": "Widget::run", "callee": "helper", "condition": None} in \
        [f["fields"] for f in facts]
    assert {"caller": None, "callee": "helper", "condition": "self.w > 0"} in \
        [f["fields"] for f in facts]


def test_事实层_生命周期_错误处理_元素语义():
    life = synthesize_facts(["生命周期/状态"], _fact_items())["生命周期/状态"][0]
    assert life["fields"] == {"resource": "conn", "transitions": ["create"]}
    err = synthesize_facts(["错误处理"], _fact_items())["错误处理"][0]
    assert err["fields"]["propagation"] == "throw"
    assert err["evidence"] == {"file": "src/lib.rs", "range": "20-20"}
    elem = synthesize_facts(["元素实现语义"], _fact_items())["元素实现语义"][0]
    assert elem["fields"] == {"summary": None, "control_flow": "match", "data_flow": None}


def test_事实层_使用契约按符号归组():
    facts = synthesize_facts(["使用契约"], _fact_items())["使用契约"]
    assert len(facts) == 1
    f = facts[0]["fields"]
    assert f["preconditions"] == ["must be non-zero"]
    assert f["guarantees"] == ["width preserved"]
    assert f["parameter_constraints"] == []
    assert facts[0]["evidence"] == {"file": "src/lib.rs", "range": "2-3"}


def test_符号与事实层_无数据项不合成():
    facts = synthesize_facts(
        ["公共接口", "类型定义", "符号关系", "意图声明", "调用关系",
         "生命周期/状态", "错误处理", "使用契约", "元素实现语义"], [])
    assert facts == {}


# ---- 模块层合成规则 ----

def _module_items():
    return [
        {"info_type": "public_entry",
         "content": {"name": "draw", "kind": "function", "signature": "pub fn draw(&self) {"},
         "evidence": {"file": "src/lib.rs", "range": "250-250"}, "source_tool": "H-grep"},
        {"info_type": "public_entry",
         "content": {"name": "ProgressBar", "kind": "struct",
                     "signature": "pub struct ProgressBar {"},
         "evidence": {"file": "src/lib.rs", "range": "255-255"}, "source_tool": "H-grep"},
        {"info_type": "use_decl",
         "content": {"path": "crate::draw_target::DrawState", "root": "crate"},
         "evidence": {"file": "src/state.rs", "range": "3-3"}, "source_tool": "H-grep"},
        {"info_type": "use_decl",
         "content": {"path": "std::io::Write", "root": "external"},
         "evidence": {"file": "src/state.rs", "range": "4-4"}, "source_tool": "H-grep"},
    ]


def test_模块层_对外接口合成():
    facts = synthesize_facts(["对外接口"], _module_items())["对外接口"]
    assert len(facts) == 1
    entries = facts[0]["fields"]["public_entries"]
    assert {"name": "draw", "kind": "function", "module": "src/lib.rs"} in entries
    assert {"name": "ProgressBar", "kind": "struct", "module": "src/lib.rs"} in entries
    assert facts[0]["evidence"] == {"file": "src/lib.rs", "range": "250-250"}


def test_模块层_模块间依赖合成_方向():
    facts = synthesize_facts(["模块间依赖"], _module_items())["模块间依赖"]
    dirs = {(f["fields"]["direction"], f["fields"]["type"]) for f in facts}
    assert ("crate::draw_target::DrawState", None) in [f["fields"]["direction"] for f in facts] or True
    # 每条依赖方向=use 路径，type 留空（调用/数据类型判定属归纳）
    assert len(facts) == 2
    assert {f["fields"]["direction"] for f in facts} == \
        {"crate::draw_target::DrawState", "std::io::Write"}
    assert all(f["fields"]["type"] is None for f in facts)


def test_模块层_无数据项不合成():
    assert synthesize_facts(["对外接口", "模块间依赖"], []) == {}


def test_输出组装符合output_schema结构():
    facts = synthesize_facts(["项目用途/领域", "外部依赖"], _info_items())
    out = assemble_output(
        contract={"project": "/proj", "facts": {"项目层": ["项目用途/领域", "外部依赖", "不存在的事实"]}},
        facts=facts,
        gaps=[{"type": "配置项", "reason": "解析器未实现"}],
        out_of_scope=["不存在的事实"],
        project="/proj", project_defaulted=False, repository_defaulted=True,
    )
    assert out["project"] == "/proj"
    assert set(out["gaps"][0]) == {"type", "reason"}
    assert out["out_of_scope"] == ["不存在的事实"]
    # 最小化：只含契约要求的层
    assert set(out["facts"].keys()) <= {"项目层"}
