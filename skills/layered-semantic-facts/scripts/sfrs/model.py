"""语义实体记录模型（任务 2.1/2.2/2.3；design 决策 3/7）。

- 分解 decompose：读写单位（语义事实集）→ 实体记录（物理粒度：实体+属性+证据）
- 重组 reassemble：实体记录 → 语义事实集（对读写契约透明：取回与提交一致）
- 操作语义常量 OPS_SEMANTICS：spec「增量维护与幂等写入」的规则锚点（实现见 4.x）

实体稳定标识红线（design Open Question 2）：身份判定责任由 Skill 提取流程承担，
仓库只校验同 ID 结构一致性；回填前本模块以 (事实类型:文件:行号范围) 作确定性
占位标识（保守方案，与查询侧 entity_id 同构），显式标注待 OQ2 回填后固化。
"""


# 读写单位（提交形态）的字段锚点：事实集提交 MUST 含此三元组
FACT_SET_SUBMIT = ("project", "version", "facts")

# 操作语义（spec「增量维护与幂等写入」「版本由调用方给定」「事实不可变与按版本追溯」）
OPS_SEMANTICS = {
    "submit_atomic": "提交（含批量）为原子生效单元：任一变更不合规则整体不生效",
    "idempotent_same_content": "同（项目、版本）内同 ID 同内容重复提交幂等，不产生重复事实",
    "conflict_same_id_diff_content": "同（项目、版本）内同 ID 不同内容判版本冲突，拒绝提交",
    "invalidate_explicit": "事实失效为显式操作（随新项目版本表达新状态），仓库不隐式失效",
    "version_by_caller": "版本由调用方给定；仓库不创建、不推进版本，无固化操作",
}


def _entity_id(fact_type, evidence):
    """占位实体标识（保守方案，待 OQ2 回填固化）：与查询侧 entity_id 同构。"""
    ev = evidence or {}
    return f"{fact_type}:{ev.get('file', '?')}:{ev.get('range', '?')}"


def decompose(fact_set):
    """把语义事实集分解为实体记录列表（确定性：同输入同输出）。

    fact_set: {project, version, facts}（读写单位形态）。
    每个事实条目（{type, children, evidence}）分解为一个实体：
    - entity_id：占位标识（见模块注释）；
    - fact_type / layer（层级归属元数据，参与索引不参与布局）；
    - fields = children 中的值属性（name → value）；子树节点（is_subtree=true）
      不进入属性——其内容由子实体承担；
    - evidence 原样保留。
    """
    entities = []
    for layer, items in (fact_set.get("facts") or {}).items():
        for item in items:
            fields = {}
            for child in item.get("children") or []:
                if child.get("is_subtree"):
                    continue
                fields[child["name"]] = child.get("value")
            evidence = item.get("evidence") or {}
            entities.append({
                "entity_id": _entity_id(item["type"], evidence),
                "fact_type": item["type"],
                "layer": layer,
                "fields": fields,
                "evidence": evidence,
            })
    return entities


def reassemble(entities, project=None, version=None):
    """把实体记录重组为语义事实集（取回与提交一致：facts 与提交时一致）。

    entities: decompose 的输出列表。重组按 (fact_type) 归组、children 按
    fields 顺序重建（值属性 → is_subtree=false）。
    """
    facts = {}
    for e in entities:
        layer = e.get("layer", "事实层")
        children = [{"name": k, "is_subtree": False, "value": v}
                    for k, v in (e.get("fields") or {}).items()]
        item = {"type": e["fact_type"], "children": children}
        if e.get("evidence"):
            item["evidence"] = e["evidence"]
        facts.setdefault(layer, []).append(item)
    out = {"facts": facts}
    if project is not None:
        out["project"] = project
    if version is not None:
        out["version"] = version
    return out
