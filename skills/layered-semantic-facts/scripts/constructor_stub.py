"""构造器接口桩（测试用）。

模拟构造器的「查询契约 + 项目位置 → 事实集」接口（design 决策 4）。
编排器只依赖：
- available() -> bool（构造器是否可用）
- build(needs) -> {事实类型: [实体]}（按构造任务清单产出事实）
- declared_gaps() -> [{type, field?, reason}]（可选；结构化缺口声明，design 决策 5）

真实构造器落地后仅替换适配层；本桩用于编排循环与覆盖比对联调。
"""


class ConstructorStub:
    def __init__(self, available=True, produce=None, declared_gaps=None):
        """produce: callable(needs: set[事实类型]) -> {事实类型: [实体]}。
        缺省为每次返回空（模拟构造器无法补齐 → 触发终止判据）。
        declared_gaps: 构造器声明的结构化缺口（字段/类型级原因）。"""
        self._available = available
        self._produce = produce or (lambda needs: {})
        self._declared = list(declared_gaps or [])

    def available(self):
        return self._available

    def build(self, needs):
        return self._produce(needs)

    def declared_gaps(self):
        return list(self._declared)
