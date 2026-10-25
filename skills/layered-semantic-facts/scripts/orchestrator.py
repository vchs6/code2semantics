"""透读编排器（orchestrator）：契约 → 仓库透读 → 缺口触发构造 → 输出。

spec「透读编排循环」：确定性循环
  读仓库 → 覆盖比对 → 构造任务清单（仅缺口）→ 构造器调用 → 产出入库 → 返回循环重读。
  继续条件：差集非空且构造器可用；终止条件：差集为空，或本轮构造未产生任何新入库事实。
  最终经事实合成按契约装配输出；剩余缺口以 gaps 显式输出。

构造器不可用（未实施/不可调用）时降级只读：命中项正常返回，未命中项进 gaps 并标注原因，
MUST NOT 退化回现场即兴提取（design 决策 5）。

仓库与构造器以接口桩编程（SFRS / 构造器落地后仅替换适配层）。
"""
import os

from catalog import FIELDS
from coverage import compare
from synthesizer import synthesize
from versioning import current_version

MAX_ROUNDS = 100  # 防御上限；正常终止见 spec 的两个终止条件


def _parse_facts(contract):
    """契约 facts 双形态解析（design 决策 3）：字符串（定位类型节点本身）
    或 {fact_type, path}（节点定位 + 续查路径）。

    返回 (located, out_of_scope)：located = [(事实类型, path 列表)]；
    out_of_scope = 目录外事实类型列表（不编造、不产生事实）。
    """
    located = []
    out_of_scope = []
    for layer, items in (contract.get("facts") or {}).items():
        for it in items:
            if isinstance(it, str):
                t, path = it, []
            else:
                t, path = it.get("fact_type"), list(it.get("path") or [])
            if t in FIELDS:
                located.append((t, path))
            else:
                out_of_scope.append(t)
    return located, out_of_scope


def _requested_subtree_paths(located, subtree_map):
    """续查路径声明的子树节点内容集 {(事实类型, 字段)}（沿 subtree_map 链下钻）。"""
    requested = set()
    for t, path in located:
        cur = t
        for seg in path:
            m = subtree_map.get(cur) or {}
            if seg in m:
                requested.add((cur, seg))
                cur = m[seg]
            else:
                break  # 非子树字段或未知段：停止下钻
    return requested


def orchestrate(contract, repo, constructor, project_root=None,
                version_fn=current_version, subtree_map=None):
    """执行透读查询，返回符合 output-schema 的 dict。

    不可访问（项目/仓库任一）时返回 {"error": 原因}（spec「不可访问时直接报告」）。
    """
    # 项目位置：缺省补全
    project = contract.get("project")
    project_defaulted = False
    if not project:
        project = project_root or os.getcwd()
        project_defaulted = True
    repository_defaulted = "repository" not in contract

    # 不可访问直接报告
    if not repo.accessible():
        return {"error": f"事实仓库不可访问：{contract.get('repository') or '(缺省来源)'}"}
    if not os.path.isdir(project):
        return {"error": f"来源项目不可访问：{project}"}

    # 版本语义：请求版本缺失 → 回退当前版本并标注
    req_version = contract.get("version")
    version_fallback = False
    if req_version:
        if repo.read(project, req_version) is None:
            version = version_fn(project)
            version_fallback = True
        else:
            version = req_version
    else:
        version = version_fn(project)

    located, out_of_scope = _parse_facts(contract)
    # path 续查：path 段沿 subtree_map 定位的子事实类型节点，同样作为请求目标
    # （spec「子树节点由消费方续查」：以子树节点为目标再查询 → 输出其下一级）
    expanded = list(located)
    for t, path in located:
        cur = t
        for seg in path:
            child = (subtree_map.get(cur) or {}).get(seg)
            if child is None:
                break
            if not any(tt == child for tt, _ in expanded):
                expanded.append((child, []))
            cur = child
    required = {t: FIELDS[t] for t, _ in expanded}
    requested = _requested_subtree_paths(located, subtree_map)
    constructor_available = constructor.available()

    returned = repo.read(project, version) or {}
    declared = {}  # (类型, 字段|None) -> 精确原因（构造器声明，design 决策 5）
    induction_requests = []  # 未覆盖归纳请求（design 决策 11，随输出暴露）
    for _ in range(MAX_ROUNDS):
        gaps = compare(required, returned, subtree_map=subtree_map,
                       requested_paths=requested)
        applicable = [g for g in gaps
                      if (g["type"], g.get("field")) not in declared]
        needs = {g["type"] for g in applicable}  # 构造任务仅含未豁免的缺口
        if not needs:
            break  # 差集为空（或全部已被声明缺口豁免）→ 终止
        if not constructor_available:
            break  # 只读降级
        produced = constructor.build(needs)
        get_requests = getattr(constructor, "induction_requests", None)
        if callable(get_requests):
            induction_requests = [dict(r) for r in (get_requests() or [])]
        if not produced:
            break  # 构造无产出 → 终止
        get_declared = getattr(constructor, "declared_gaps", None)
        if callable(get_declared):
            for g in get_declared():
                declared.setdefault((g["type"], g.get("field")), g["reason"])
        if repo.write(project, version, produced) == 0:
            break  # 本轮无新入库事实 → 终止（MUST NOT 无限重试）
        returned = repo.read(project, version) or {}  # 返回循环重读

    # 剩余缺口 → gaps：已声明缺口用其精确原因；有归纳请求的类型标"待归纳"（语义分层）；
    # 其余区分只读降级 / 构造后仍缺失
    inducting_types = {r["type"] for r in induction_requests}
    final_gaps = []
    for g in compare(required, returned, subtree_map=subtree_map,
                     requested_paths=requested):
        if not constructor_available:
            reason = "构造器不可用，只读降级"
        elif g["type"] in inducting_types:
            reason = "待归纳"
        else:
            reason = declared.get((g["type"], g.get("field")), "构造后仍缺失")
        item = {"type": g["type"], "reason": reason}
        if g.get("field"):
            item["field"] = g["field"]
        final_gaps.append(item)

    # 合成裁剪依据 = 扩展后的请求集（含 path 续查定位的子类型），按 catalog 层归组
    from catalog import LAYER_OF
    synth_facts = {}
    for t, _ in expanded:
        synth_facts.setdefault(LAYER_OF.get(t, "事实层"), []).append(t)
    synth_contract = dict(contract)
    synth_contract["facts"] = synth_facts

    return synthesize(
        synth_contract, merged=returned, version=version, version_fallback=version_fallback,
        gaps=final_gaps, out_of_scope=out_of_scope,
        project=project, project_defaulted=project_defaulted,
        repository_defaulted=repository_defaulted,
        subtree_map=subtree_map, induction_requests=induction_requests,
    )
