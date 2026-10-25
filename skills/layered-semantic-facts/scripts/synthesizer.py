"""事实合成器（synthesizer）：确定性装配最终语义事实集。

输入：仓库命中事实与构造入库事实的合并集合（单一事实源）、查询契约、真实版本标识。
输出：符合 output-schema 的最终事实集——按契约结构装配、最小化裁剪（仅契约要求的层与字段）、
gaps 与 out_of_scope 分列、真实版本标注。

MUST NOT 将仓库原始返回直接透传（spec「事实合成按契约结构装配输出」）。
"""
from catalog import FIELDS


def _flatten_facts(merged):
    """把 {事实类型: [实体]} 展平为 {层级: [{type, fields, evidence}]}。

    merged: {事实类型: [实体 dict]}；实体的 `_id` 不进入输出（内部标识）。
    """
    by_layer = {}
    for fact_type, entities in merged.items():
        from catalog import LAYER_OF
        layer = LAYER_OF.get(fact_type, "事实层")
        by_layer.setdefault(layer, [])
        for e in entities:
            if not isinstance(e, dict):
                continue
            item = {"type": fact_type, "fields": {k: v for k, v in e.items() if k != "_id"}}
            if e.get("evidence"):
                item["evidence"] = e["evidence"]
            by_layer[layer].append(item)
    return by_layer


def synthesize(contract, merged, version, version_fallback=False,
               gaps=None, out_of_scope=None,
               project=None, project_defaulted=False, repository_defaulted=False,
               subtree_map=None, induction_requests=None):
    """合成最终事实集（按查询节点下一级返回）。

    contract: 查询契约（facts 节点定位；project/repository 可缺省）。
    merged: {事实类型: [实体]}（命中 + 构造，单一事实源，已按 fact-catalog 词汇归组）。
    version: 真实版本标识；version_fallback: 是否回退当前版本。
    gaps: [{type, reason}]（缺口语义）。
    out_of_scope: [目录外事实类型]。
    subtree_map: {事实类型: {字段: 子事实类型}}——声明子树字段的下一级标注；
        子树字段输出为引用（is_subtree=true，内容不返回，由消费方续查）。

    返回符合 output-schema 的 dict。最小化：仅契约要求的层与类型；
    每实体 children = 该节点的下一级节点集（值属性直出、子树节点仅标注）。
    """
    subtree_map = subtree_map or {}
    # 契约要求的 (层级 → 事实类型) 视图
    required_by_layer = {}
    for layer, items in (contract.get("facts") or {}).items():
        types = set()
        for it in items:
            types.add(it if isinstance(it, str) else it.get("fact_type"))
        required_by_layer[layer] = types

    facts = {}
    for fact_type, entities in merged.items():
        from catalog import LAYER_OF
        layer = LAYER_OF.get(fact_type, "事实层")
        if layer not in required_by_layer:
            continue  # 超出契约的层：裁剪
        if fact_type not in required_by_layer[layer]:
            continue  # 超出契约的事实类型：裁剪
        facts.setdefault(layer, [])
        # 下一级装配：仅保留 fact-catalog 该类型声明的字段；子树字段只标注不展开
        catalog_fields = [f for f in FIELDS.get(fact_type, [])]
        subtree_fields = subtree_map.get(fact_type) or {}
        for e in entities:
            if not isinstance(e, dict):
                continue
            children = []
            for field in catalog_fields:
                if field not in e:
                    continue  # 未产出的字段不冒充（缺口由 gaps 显式表达）
                if field in subtree_fields:
                    children.append({"name": field, "is_subtree": True})
                else:
                    children.append({"name": field, "is_subtree": False, "value": e[field]})
            item = {"type": fact_type, "children": children}
            if e.get("evidence"):
                item["evidence"] = e["evidence"]
            facts[layer].append(item)

    out = {
        "project": project if project is not None else contract.get("project"),
        "project_defaulted": project_defaulted,
        "repository_defaulted": repository_defaulted,
        "version": version,
        "version_fallback": version_fallback,
        "facts": facts,
        "gaps": gaps or [],
        "out_of_scope": out_of_scope or [],
    }
    if induction_requests:
        out["induction_requests"] = list(induction_requests)  # 未覆盖请求随输出暴露
    return out
