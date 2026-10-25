"""构造器入口（任务 2.3/6.1）：契约 → 合成分析 → 生产者选择 → 执行器 → 解析器 → 事实合成。

透传流程（spec「按契约构造语义事实集」）：
1. 契约校验（结构 + fact-catalog 封闭世界 → out_of_scope）；
2. 合成分析：派生信息需求清单（确定性交付物，随输出暴露，任务 2.3）；
3. 逐事实类型查矩阵选生产者（只读，解析器已实现且已点亮的工具直出条目）；
4. 执行器按调用剖面跑工具 → 解析器转信息数据项（缺失/失败进 gaps，不中断）；
5. 事实合成（证据自数据项传递）+ 按 output-schema 组装（gaps/out_of_scope 分列）。
"""
import json
import os

from catalog import FIELDS
from .contract_check import validate_contract
from .executor import execute, merge_exception_into_gaps
from .fact_synthesis import assemble_output, synthesize_facts
from .producer import call_parser, select_producers
from .synthesis import build_info_needs, FIELD_INFO_NEEDS, _is_inductive


def _match_entities_by_evidence(entities, evidence):
    """归纳条目证据与实体的匹配（design 决策 3）：带证据且命中则仅返回命中实体，
    否则返回全部实体（仅字段组形态，填充所有同名字段空位）。"""
    if not evidence:
        return list(entities)
    ev = json.dumps(evidence, sort_keys=True, ensure_ascii=False)
    matched = [e for e in entities
               if json.dumps(e.get("evidence"), sort_keys=True, ensure_ascii=False) == ev]
    return matched or list(entities)


def _apply_induced_entries(facts, fact_type, entries):
    """把归纳返回条目并入/回填（design 决策 3）。返回是否有任何字段值实际写入：
    类型已有实体 → 回填实体空字段（条目带证据命中则仅回填该实体）；
    类型无实体 → 追加新实体（既有路径）。无效条目（无字段/值全为 None）不计覆盖。"""
    applied = False
    for entry in entries or []:
        fields = (entry.get("fields") if isinstance(entry, dict) and "fields" in entry
                  else entry)
        if not isinstance(fields, dict) or not fields:
            continue
        evidence = entry.get("evidence") if isinstance(entry, dict) else None
        existing = facts.get(fact_type)
        if existing:
            # 混合形态：整组返回回填既有实体空字段；不覆盖已有值，不编造
            matched = _match_entities_by_evidence(existing, evidence)
            for e in matched:
                for k, v in fields.items():
                    if v is not None and (e.get("fields") or {}).get(k) is None:
                        e.setdefault("fields", {})[k] = v
                        applied = True
        else:
            facts.setdefault(fact_type, []).append({
                "type": fact_type, "fields": fields, "evidence": evidence})
            applied = True
    return applied


def collect_induction_requests(required_types, facts, matrix_dir):
    """收集代理归纳请求（design 决策 2：两分支共用同一整组通道，确定性）。

    (a) 类型无产出 → 既有整类型请求（fields = 全目录字段）；
    (b) 类型有产出但归纳字段空缺（混合形态）→ 以待取值字段集合为一组整体请求，
        MUST NOT 逐字段拆分（add-induction-batch-trigger）；待取值集合为空（归纳
        字段全部有值）→ 不请求。
    仅对有已点亮 A-*（智能体兜底/项目分析Skill）生产者的类型产出请求。
    """
    from matrix_tool.query import load_matrix, query_producers
    _entries, _producers, need_by_fact_type = load_matrix(matrix_dir)
    requests = []
    for fact_type in dict.fromkeys(required_types):
        agents = [e for e in query_producers(fact_type=fact_type, matrix_dir=matrix_dir)
                  if e["production_tier"] in ("智能体兜底", "项目分析Skill")
                  and e["status"] == "已点亮" and e["verdict"] != "不可完成"]
        if not agents:
            continue
        entities = facts.get(fact_type)
        if entities:
            fields = pending_inductive_fields(fact_type, entities)
            if not fields:
                continue  # 待取值集合为空（归纳字段全部有值）→ 不请求
        else:
            fields = list(FIELDS.get(fact_type, []))  # 既有整类型路径
        need = need_by_fact_type.get(fact_type) or {}
        requests.append({
            "type": fact_type,
            "fields": fields,
            "guidance": need.get("required_info", ""),
        })
    return requests


def pending_inductive_fields(fact_type, entities):
    """盘点事实类型本轮构造后的待取值字段集合（design 决策 1，确定性）。

    待取值 = FIELD_INFO_NEEDS 中标记为归纳的字段中，产出实体里值为空
    （缺失或 None）的字段；类型完全无产出时返回全部归纳字段（与既有
    整类型归纳路径等价）。非归纳字段的空缺走既有工具/合成缺口语义。
    """
    field_map = FIELD_INFO_NEEDS.get(fact_type) or {}
    inductive = [f for f, need in field_map.items() if _is_inductive(need)]
    if not entities:
        return inductive
    return [f for f in inductive
            if any((e.get("fields") or {}).get(f) is None for e in entities)]


def construct(contract, project_root=None, matrix_dir=None,
              parser_registry=None, cwd=None, skip_exec=False, inducer=None):
    """构造语义事实集。返回 dict：顶层结构对齐 output-schema（含 info_needs、
    induction_requests）；facts 条目为 {type, fields, evidence} 中间形态，
    最终响应的 children（下一级返回）形态由编排器合成。

    - matrix_dir：能力矩阵目录（缺省为全局矩阵）；parser_registry：解析器注册表；
    - skip_exec：测试桩模式——跳过工具执行，直接用桩解析器产出（profile 无 command 时也跳过）；
    - inducer：代理归纳钩子（callable）。无工具直出产出、但有已点亮智能体兜底/分析Skill
      生产者的缺失事实类型，产出结构化 induction_requests 并交 inducer 归纳；归纳结果
      按契约并入 facts（目录外类型拒收，不编造）。未覆盖的请求随输出暴露为「待代理归纳」。
    - 项目/仓库不可访问 → {"error": 原因}（spec「不可访问时直接报告」语义沿用）。
    """
    errors, out_of_scope = validate_contract(contract)
    if errors:
        return {"error": "；".join(errors)}

    project = contract.get("project") or project_root or os.getcwd()
    project_defaulted = not contract.get("project")
    if project_root is None:
        project_root = project
    if not os.path.isdir(project_root):
        return {"error": f"来源项目不可访问：{project_root}"}

    # 合成分析：信息需求清单（确定性交付物，随输出暴露）
    # 契约 facts 双形态（design 决策 3）：字符串定位类型节点本身；对象 {fact_type, path?}
    # 为节点定位 + 可选续查路径——两者最终都定位到事实类型。
    required_types = []
    for fact_types in (contract.get("facts") or {}).values():
        if not isinstance(fact_types, list):
            continue
        for item in fact_types:
            t = item.get("fact_type") if isinstance(item, dict) else item
            if isinstance(t, str) and t in FIELDS:
                required_types.append(t)
    info_needs = build_info_needs(required_types)

    gaps = []
    # 阶段一：逐事实查矩阵（只读），聚合生产者计划（design 决策 9：同一轮内每工具仅执行一次）
    producer_plan = {}  # tool_id -> {"profile": 调用剖面, "fact_types": 服务的事实类型}
    for fact_type in dict.fromkeys(required_types):  # 去重保序
        usable, unavailable = select_producers(fact_type, matrix_dir, parser_registry)
        for u in unavailable:  # 解析器未实现 → gaps
            gaps.append({"type": fact_type, "reason": u["reason"]})
        if not usable:
            if not unavailable:
                gaps.append({"type": fact_type, "reason": "矩阵中无可用生产者条目"})
            continue
        for producer in usable:
            # 聚合键 =（工具标识 + 命令）：同一命令只执行一次（design 决策 9），
            # 数据项路由给共享该剖面的全部事实类型；不同命令各自执行（同工具
            # 服务多个事实类型时剖面可不同，MUST NOT 互相覆盖）。
            plan_key = (producer["tool_id"], (producer["invocation_profile"] or {}).get("command"))
            plan = producer_plan.setdefault(plan_key, {
                "profile": producer["invocation_profile"],
                "tool_id": producer["tool_id"],
                "fact_types": [],
            })
            if fact_type not in plan["fact_types"]:
                plan["fact_types"].append(fact_type)

    # 阶段二：按生产者聚合执行——同一命令一次，数据项路由给其服务的全部事实类型
    all_items = []
    for _key, plan in producer_plan.items():
        tool_id = plan["tool_id"]
        profile = plan["profile"]
        fact_types = plan["fact_types"]
        if skip_exec or not (profile or {}).get("command"):
            result = call_parser(tool_id, None,  # 桩模式：解析器直接产出
                                 dict(profile or {}, project_root=project_root),
                                 parser_registry)
        else:
            exec_result = execute(profile, tool_id=tool_id, cwd=cwd or project_root)
            if exec_result.exception is not None:
                merge_exception_into_gaps(exec_result.exception, fact_types, gaps)
                continue
            result = call_parser(tool_id, exec_result.output,
                                 dict(profile or {}, project_root=project_root),
                                 parser_registry)
        if result.items:
            all_items.extend(result.items)
        if result.failure is not None:
            for fact_type in fact_types:
                gaps.append({"type": fact_type,
                             "reason": f"{result.failure.reason}（{tool_id}）"})

    # 去重：同一生产者被多个事实类型触发时，解析器会重复产出同一数据项；
    # 按（信息类型 + 内容 + 证据）稳定键去重，保证合成不重复（确定性）。
    seen_items = set()
    unique_items = []
    for item in all_items:
        key = (item.get("info_type"),
               json.dumps(item.get("content"), sort_keys=True, ensure_ascii=False),
               json.dumps(item.get("evidence"), sort_keys=True, ensure_ascii=False))
        if key not in seen_items:
            seen_items.add(key)
            unique_items.append(item)

    facts = synthesize_facts(required_types, unique_items)

    # 阶段三：代理归纳——存在待取值集合、且有已点亮 A-*（智能体兜底/分析Skill）生产者的
    # 事实类型 → 结构化归纳请求（两分支共用同一整组通道，见 collect_induction_requests）。
    induction_requests = collect_induction_requests(required_types, facts, matrix_dir)
    requested_types = {r["type"] for r in induction_requests}

    if inducer is not None and induction_requests:
        induced = inducer([dict(r) for r in induction_requests]) or {}
        covered = set()
        for fact_type, entries in induced.items():
            if fact_type not in requested_types or fact_type not in FIELDS:
                continue  # 目录外 / 未被请求的归纳结果拒收（不编造）
            if _apply_induced_entries(facts, fact_type, entries):
                covered.add(fact_type)  # 有字段值实际写入才计覆盖
        # 未实际覆盖（未返回值 / 返回值全为 None）的请求保持暴露（不编造）
        induction_requests = [r for r in induction_requests if r["type"] not in covered]

    # 缺口兜底：缺失类型若有归纳请求 → 标注待代理归纳（与工具失败 gap 并存，语义分层）；
    # 否则仅在无任何该类型 gap 时补「构造后仍缺失」（工具失败已解释缺失时不重复）。
    for fact_type in required_types:
        if fact_type in facts:
            continue
        if fact_type in requested_types:
            gaps.append({"type": fact_type,
                         "reason": "待代理归纳：无工具直出数据项，已产出归纳请求"})
        elif not any(g["type"] == fact_type for g in gaps):
            gaps.append({"type": fact_type,
                         "reason": "构造后仍缺失：无对应合成规则或信息数据项"})

    output = assemble_output(contract, facts, gaps, out_of_scope,
                             project=project, project_defaulted=project_defaulted,
                             induction_requests=induction_requests)
    output["info_needs"] = info_needs  # 任务 2.3：清单可从输出取回
    return output
