"""SFRS 适配层（编排器仓库接口 → SQLite 持久化）。

编排器对仓库的调用面为三个方法（与内存桩同构，design 决策：SFRS 落地后仅替换适配层）：
- accessible() -> bool
- read(project, version) -> {事实类型: [实体]} 或 None
- write(project, version, produced) -> int（新入库实体数，幂等）

桥接方式：编排器实体形态（拍平 dict：_id/evidence/字段）经 sfrs.model 分解/重组
为语义事实集（读写单位），由 SFRS 以（项目、版本）持久化。
"""
from catalog import LAYER_OF
from sfrs.model import decompose, reassemble
from sfrs.repository import SFRS


class SFRSRepo:
    def __init__(self, db_path=None):
        self._sfrs = SFRS(db_path=db_path)

    def accessible(self):
        return self._sfrs.accessible()

    def _to_fact_set(self, project, version, produced):
        """编排器形态 {事实类型: [拍平实体]} → 语义事实集（读写单位形态）。"""
        facts = {}
        for fact_type, entities in (produced or {}).items():
            layer = LAYER_OF.get(fact_type, "事实层")
            items = facts.setdefault(layer, [])
            for entity in entities or []:
                evidence = entity.get("evidence") or {}
                children = [{"name": k, "is_subtree": False, "value": v}
                            for k, v in entity.items()
                            if k not in ("_id", "evidence")]
                items.append({"type": fact_type, "children": children,
                              "evidence": evidence})
        return {"project": project, "version": version, "facts": facts}

    def _from_fact_set(self, fact_set):
        """语义事实集 → 编排器形态 {事实类型: [拍平实体]}。"""
        out = {}
        for entity in decompose(fact_set):
            flat = {"_id": entity["entity_id"], "evidence": entity["evidence"]}
            flat.update(entity["fields"])
            out.setdefault(entity["fact_type"], []).append(flat)
        return out or None

    def read(self, project, version):
        fact_set = self._sfrs.read(project, version)
        if fact_set is None:
            return None
        return self._from_fact_set(fact_set)

    def write(self, project, version, produced):
        """提交编排器产出（幂等），返回新入库实体数（编排循环终止判据语义）。"""
        result = self._sfrs.submit(self._to_fact_set(project, version, produced))
        if "error" in result:
            raise ValueError(f"SFRS 提交被拒：{result['error']}")
        return result["accepted"]

    # 直通能力（Skill 按需取回：精确查询/关系遍历/事实集级读取）
    def read_fact_set(self, project, version):
        return self._sfrs.read(project, version)

    def query(self, project, version, fact_type=None, entity_id=None):
        return self._sfrs.query(project, version, fact_type=fact_type, entity_id=entity_id)

    def relations_from(self, project, version, entity_id):
        return self._sfrs.relations_from(project, version, entity_id)
