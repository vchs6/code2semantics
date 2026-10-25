"""覆盖比对（coverage）：契约要求集 vs 仓库返回集 → 实体级缺口清单。

确定性集合运算（spec「实体级未命中判定」+「透读编排循环」的覆盖比对步骤）。

词汇来源：fact-catalog 的事实类型与字段（catalog.FIELDS）。
实体 = facts 中某事实类型的一个条目；实体稳定标识优先取条目 `_id`，
缺省回退到 evidence 的 file:range（待 SFRS 实体稳定标识方案回填后固化）。

两种缺口：
- 值属性缺失：实体的标量字段缺失/为空。
- 子树缺失：实体的子树字段（在 subtree_map 中声明）缺失时，递归分解到
  子事实类型的子实体逐个判定，仅真正缺失的子实体进缺口，不把整棵子树记为一个缺口。

subtree_map 形如 {事实类型: {字段: 子事实类型}}，默认空（子树映射待信息契约
OQ2 回填后由编排器注入）；空映射时所有字段按值属性处理。
"""
from catalog import FIELDS


def entity_id(entity):
    """实体稳定标识：优先 _id，回退 evidence 定位。"""
    if isinstance(entity, dict):
        if entity.get("_id"):
            return entity["_id"]
        ev = entity.get("evidence") or {}
        if ev.get("file"):
            return f"{ev['file']}:{ev.get('range', '?')}"
    return repr(entity)


def _missing(container, key):
    """字段缺失判定：键不存在，或值为 None/空串/空列表。"""
    if isinstance(container, dict):
        if key not in container:
            return True
        v = container[key]
    else:
        return True
    return v is None or v == "" or v == []


def compare(required, returned, subtree_map=None, requested_paths=None):
    """覆盖比对。

    required: {事实类型: [字段列表]}（字段列表为空表示该类型只要有实体即可）。
    returned: {事实类型: [实体 dict 列表]}。
    subtree_map: {事实类型: {字段: 子事实类型}}，可选。
    requested_paths: {(事实类型, 字段)}——消费方已请求的子树节点内容集（节点续查）；
        命中者即使字段有值也递归判缺子实体，未命中者保持既有行为（字段缺失才递归），
        且不把未请求的孙辈字段纳入判缺。

    返回 gaps: [{type, entity, field, kind, reason}]，kind ∈ 类型缺失/值属性缺失/子树缺失。
    """
    requested_paths = requested_paths or set()
    subtree_map = subtree_map or {}
    gaps = []
    _checked = set()  # (type, field) 防子树递归成环

    for fact_type, req_fields in required.items():
        entities = returned.get(fact_type, [])
        if not entities:
            gaps.append({
                "type": fact_type, "entity": None, "field": None,
                "kind": "类型缺失",
                "reason": f"仓库中无任何 {fact_type} 实体",
            })
            continue
        _compare_entities(fact_type, entities, req_fields, returned,
                          subtree_map, gaps, _checked, requested_paths)
    return gaps


def _compare_entities(fact_type, entities, req_fields, returned,
                      subtree_map, gaps, checked, requested):
    for entity in entities:
        fields = entity if isinstance(entity, dict) else {}
        for field in req_fields or FIELDS.get(fact_type, []):
            child_type = (subtree_map.get(fact_type) or {}).get(field)
            requested_child = (fact_type, field) in requested
            if child_type and not _missing(fields, field) and not requested_child:
                continue  # 子树字段有值且未请求其内容 → 该子树节点不参与判缺
            if not _missing(fields, field) and not child_type:
                continue
            if child_type:
                # 子树字段：递归分解到子事实类型的子实体（既有语义；
                # 已请求路径即使有值也下钻，spec「子树属性递归分解」以请求路径为界）
                key = (child_type, field)
                if key in checked:
                    continue
                checked.add(key)
                child_entities = returned.get(child_type, [])
                if not child_entities:
                    gaps.append({
                        "type": child_type, "entity": entity_id(entity),
                        "field": field, "kind": "子树缺失",
                        "reason": f"{fact_type} 的子树字段 {field} 指向的子实体整体缺失",
                    })
                else:
                    child_req = list(FIELDS.get(child_type, []))
                    _compare_entities(child_type, child_entities, child_req,
                                      returned, subtree_map, gaps, checked, requested)
            else:
                gaps.append({
                    "type": fact_type, "entity": entity_id(entity),
                    "field": field, "kind": "值属性缺失",
                    "reason": f"实体缺值属性 {field}",
                })
