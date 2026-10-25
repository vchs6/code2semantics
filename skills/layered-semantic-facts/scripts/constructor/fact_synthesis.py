"""事实合成与输出组装（任务 5.1/5.2）。

- synthesize_facts：由项目信息数据项合成语义事实（确定性映射），证据自数据项传递，
  不新增不伪造；契约未要求的事实类型不合成；无信息数据项支撑的事实不产出。
- assemble_output：按 output-schema 组装事实集，gaps 与 out_of_scope 分列、最小化裁剪
  （仅契约要求的层）。
"""
from catalog import LAYER_OF


def _synthesize_domain(items):
    pkg = next((i for i in items if i["info_type"] == "cargo_package"), None)
    if pkg is None:
        return None
    fields = {}
    for fact_field, info_field in (("name", "name"), ("domain", "description"), ("doc", "readme")):
        v = pkg["content"].get(info_field)
        if v:
            fields[fact_field] = v
    if not fields:
        return None
    return {"type": "项目用途/领域", "fields": fields, "evidence": pkg["evidence"]}


def _synthesize_entries(items):
    targets = [i for i in items if i["info_type"] == "cargo_target"]
    if not targets:
        return None
    entries = [{"name": t["content"]["name"], "kind": t["content"]["kind"],
                "src_path": t["content"]["src_path"]} for t in targets]
    primary = next((t for t in targets if "lib" in t["content"]["kind"]
                    or "bin" in t["content"]["kind"]), targets[0])
    return {"type": "入口", "fields": {"entries": entries}, "evidence": primary["evidence"]}


def _synthesize_build_run(items):
    pkg = next((i for i in items if i["info_type"] == "cargo_package"), None)
    targets = [i for i in items if i["info_type"] == "cargo_target"]
    crate_types = sorted({ct for t in targets for ct in t["content"].get("crate_types", [])})
    if pkg is None and not crate_types:
        return None
    fields = {}
    if pkg and pkg["content"].get("edition"):
        fields["build"] = f"cargo build（edition {pkg['content']['edition']}）"
    if "lib" in crate_types:
        fields["deployment"] = "库（library crate）"
    elif "bin" in crate_types:
        fields["deployment"] = "CLI（bin crate）"
    if not fields:
        return None
    evidence = (pkg or targets[0])["evidence"]
    return {"type": "构建与运行形态", "fields": fields, "evidence": evidence}


def _synthesize_dependencies(items):
    deps = [i for i in items if i["info_type"] == "cargo_dependency"]
    if not deps:
        return None
    dependencies = [{"name": d["content"]["name"], "req": d["content"].get("req"),
                     "kind": d["content"]["kind"], "optional": d["content"]["optional"]}
                    for d in deps]
    return {"type": "外部依赖", "fields": {"dependencies": dependencies},
            "evidence": deps[0]["evidence"]}


def _synthesize_modules(items):
    decls = [i for i in items if i["info_type"] == "module_decl"]
    if not decls:
        return None
    modules = [{"name": d["content"]["name"], "visibility": d["content"]["visibility"],
                "declared_in": d["evidence"]["file"]} for d in decls]
    return {"type": "模块划分", "fields": {"modules": modules}, "evidence": decls[0]["evidence"]}


# ---- 符号层 ----

_FUNCS = {"function", "method", "macro", "constant"}
_TYPES = {"struct", "class", "enum", "interface", "union", "record"}


def _synthesize_public_api(items):
    defs = [i for i in items if i["info_type"] == "symbol_def"
            and i["content"].get("kind") in _FUNCS]
    if not defs:
        return None
    return [{"type": "公共接口",
             "fields": {"signature": d["content"].get("signature"),
                        "visibility": d["content"].get("visibility"),
                        "module": d["evidence"]["file"]},
             "evidence": d["evidence"]} for d in defs]


def _synthesize_type_defs(items):
    defs = [i for i in items if i["info_type"] == "symbol_def"
            and i["content"].get("kind") in _TYPES]
    if not defs:
        return None
    return [{"type": "类型定义",
             "fields": {"kind": d["content"].get("kind"),
                        "description": None,
                        "fields": d["content"].get("fields", [])},
             "evidence": d["evidence"]} for d in defs]


def _synthesize_symbol_relations(items):
    rels = [i for i in items if i["info_type"] == "symbol_relation"]
    if not rels:
        return None
    return [{"type": "符号关系",
             "fields": {"relation": r["content"]["relation"],
                        "target": r["content"]["target"],
                        "module": r["evidence"]["file"]},
             "evidence": r["evidence"]} for r in rels]


def _synthesize_intents(items):
    intents = [i for i in items if i["info_type"] == "symbol_intent"]
    if not intents:
        return None
    return [{"type": "意图声明",
             "fields": {"intent": i["content"]["intent"]},
             "evidence": i["evidence"]} for i in intents]


# ---- 事实层 ----

def _synthesize_call_relations(items):
    facts = []
    for i in items:
        if i["info_type"] == "call_relation":
            facts.append({"caller": i["content"]["caller"],
                          "callee": i["content"]["callee"],
                          "condition": i["content"].get("condition")})
        elif i["info_type"] == "call_condition":
            facts.append({"caller": i["content"].get("caller"),
                          "callee": i["content"]["callee"],
                          "condition": i["content"]["condition_pattern"]})
    if not facts:
        return None
    return [{"type": "调用关系", "fields": f, "evidence": items[0]["evidence"]} for f in facts]


def _synthesize_lifecycle(items):
    events = [i for i in items if i["info_type"] == "lifecycle_event"]
    if not events:
        return None
    return [{"type": "生命周期/状态",
             "fields": {"resource": e["content"]["resource"],
                        "transitions": [e["content"]["op"]]},
             "evidence": e["evidence"]} for e in events]


def _synthesize_error_handling(items):
    errs = [i for i in items if i["info_type"] == "error_handling"]
    if not errs:
        return None
    return [{"type": "错误处理",
             "fields": {"error_type": e["content"]["error_expr"],
                        "propagation": e["content"]["op"],
                        "recovery": None},
             "evidence": e["evidence"]} for e in errs]


_CLUE_FIELD = {"precondition": "preconditions", "panics": "preconditions",
               "parameter_constraint": "parameter_constraints", "guarantee": "guarantees"}


def _synthesize_usage_contract(items):
    clues = [i for i in items if i["info_type"] == "usage_contract_clue"]
    if not clues:
        return None
    grouped = {}
    order = []
    for c in clues:
        sym = c["content"]["symbol"]
        if sym not in grouped:
            grouped[sym] = {"preconditions": [], "parameter_constraints": [], "guarantees": []}
            order.append(sym)
        grouped[sym][_CLUE_FIELD[c["content"]["clue_kind"]]].append(c["content"]["text"])
    # 组的证据：该符号全部线索中最早一条
    ev_by_sym = {}
    for c in clues:
        ev_by_sym.setdefault(c["content"]["symbol"], c["evidence"])
    return [{"type": "使用契约", "fields": grouped[sym], "evidence": ev_by_sym[sym]}
            for sym in order]


def _synthesize_element_semantics(items):
    structs = [i for i in items if i["info_type"] == "element_structure"]
    if not structs:
        return None
    return [{"type": "元素实现语义",
             "fields": {"summary": None,
                        "control_flow": s["content"]["control_flow_kind"],
                        "data_flow": None},
             "evidence": s["evidence"]} for s in structs]


def _synthesize_public_entries(items):
    entries_items = [i for i in items if i["info_type"] == "public_entry"]
    if not entries_items:
        return None
    public_entries = [{"name": e["content"]["name"], "kind": e["content"]["kind"],
                       "module": e["evidence"]["file"]} for e in entries_items]
    return {"type": "对外接口", "fields": {"public_entries": public_entries},
            "evidence": entries_items[0]["evidence"]}


def _synthesize_module_dependencies(items):
    uses = [i for i in items if i["info_type"] == "use_decl"]
    if not uses:
        return None
    return [{"type": "模块间依赖",
             "fields": {"direction": u["content"]["path"], "type": None},
             "evidence": u["evidence"]} for u in uses]


SYNTHESIZERS = {
    "项目用途/领域": _synthesize_domain,
    "入口": _synthesize_entries,
    "构建与运行形态": _synthesize_build_run,
    "外部依赖": _synthesize_dependencies,
    "模块划分": _synthesize_modules,
    "对外接口": _synthesize_public_entries,
    "模块间依赖": _synthesize_module_dependencies,
    "公共接口": _synthesize_public_api,
    "类型定义": _synthesize_type_defs,
    "符号关系": _synthesize_symbol_relations,
    "意图声明": _synthesize_intents,
    "调用关系": _synthesize_call_relations,
    "生命周期/状态": _synthesize_lifecycle,
    "错误处理": _synthesize_error_handling,
    "使用契约": _synthesize_usage_contract,
    "元素实现语义": _synthesize_element_semantics,
    # 配置项 / 模块层（职责、间依赖、对外接口）与数据流、行为约定：无工具直出
    # 数据项（矩阵判定部分/不可完成），无合成规则 → 由编排层进 gaps。
}


def synthesize_facts(fact_types, info_items):
    """由信息数据项合成语义事实。返回 {事实类型: [{type, fields, evidence}]}。

    仅合成 fact_types 中列出的事实类型；每条事实证据来自其信息数据项。
    合成器可返回单条事实（dict）或事实列表（list，一数据项一事实）。
    """
    facts = {}
    for fact_type in fact_types:
        synth = SYNTHESIZERS.get(fact_type)
        if synth is None:
            continue
        fact = synth(info_items)
        if fact is None:
            continue
        bucket = facts.setdefault(fact_type, [])
        if isinstance(fact, list):
            bucket.extend(fact)
        else:
            bucket.append(fact)
    return facts


def assemble_output(contract, facts, gaps, out_of_scope,
                    project, project_defaulted=False, repository_defaulted=False,
                    induction_requests=None):
    """按 output-schema 组装最终事实集：最小化裁剪（仅契约要求的层）、gaps 与 out_of_scope 分列。

    facts 以事实类型为键；此处按 fact-catalog 层级映射归组到层（LAYER_OF），
    仅保留契约要求的层（最小化）。induction_requests 非 None 时随输出暴露
    （未被代理归纳覆盖的请求；未被调用时不含该键，保持既有输出形态）。
    """
    required_layers = set((contract.get("facts") or {}).keys())
    trimmed = {}
    for fact_type, items in facts.items():
        layer = LAYER_OF.get(fact_type, "事实层")
        if layer in required_layers:
            trimmed.setdefault(layer, []).extend(items)
    output = {
        "project": project,
        "project_defaulted": project_defaulted,
        "repository_defaulted": repository_defaulted,
        "facts": trimmed,
        "gaps": gaps or [],
        "out_of_scope": out_of_scope or [],
    }
    if induction_requests is not None:
        output["induction_requests"] = induction_requests
    return output
