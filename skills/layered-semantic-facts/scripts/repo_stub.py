"""内存版语义事实仓库桩（SFRS 接口桩，测试用）。

模拟 SFRS 的按（项目、版本）存取接口；真实 SFRS 落地后仅替换适配层（design Q2）。

接口（编排器只依赖以下方法）：
- accessible() -> bool
- read(project, version) -> {事实类型: [实体]} 或 None（该版本无事实）
- write(project, version, facts) -> int（新入库实体数，幂等：已存在实体不重复计）
"""
from coverage import entity_id


class InMemoryRepo:
    def __init__(self, seed=None, accessible=True):
        # storage: {(project, version): {事实类型: [实体]}}
        self._storage = {}
        self._accessible = accessible
        if seed:
            for (project, version), facts in seed.items():
                self.write(project, version, facts)

    def accessible(self):
        return self._accessible

    def read(self, project, version):
        return self._storage.get((project, version))

    def write(self, project, version, facts):
        """幂等写入，返回新入库实体数。"""
        key = (project, version)
        slot = self._storage.setdefault(key, {})
        new_count = 0
        for fact_type, entities in facts.items():
            existing = slot.setdefault(fact_type, [])
            seen_ids = {entity_id(e) for e in existing}
            for e in entities:
                if entity_id(e) not in seen_ids:
                    existing.append(e)
                    seen_ids.add(entity_id(e))
                    new_count += 1
        return new_count
