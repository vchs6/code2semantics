"""构造器适配器：把真实构造器（scripts/constructor）接入查询流程编排器。

编排器对构造器的调用面为 available() / build(needs)（design 决策 4 的黑盒接口）。
本适配器绑定项目位置与能力矩阵目录，构造产出转成仓库实体形态（{事实类型: [实体]}），
实体含字段、_id（事实类型+证据定位）与 evidence——证据自信息数据项传递，不新增。

解析器登记占位（构造器任务 4.2）：默认注册已实现的 X-cargo_metadata 解析器；
新增解析器随 add-info-parser 增量登记，不改本适配器结构。
"""
from constructor.constructor import construct  # noqa: E402
from info_parser.framework import ParserRegistry  # noqa: E402


def default_parser_registry():
    """注册已实现的解析器：项目级 X-cargo_metadata + 符号层/事实层解析器（增量登记）。"""
    from info_parser.ast_grep import parse_ast_grep
    from info_parser.cargo_metadata import parse_cargo_metadata
    from info_parser.ctags import parse_ctags
    from info_parser.grep import parse_grep
    from info_parser.trace_calls import parse_trace_callers, parse_trace_callees
    reg = ParserRegistry()
    reg.register("X-cargo_metadata", parse_cargo_metadata)
    reg.register("X-ctags", parse_ctags)
    reg.register("H-grep", parse_grep)
    reg.register("H-ast_grep", parse_ast_grep)
    reg.register("H-trace_callees", parse_trace_callees)
    reg.register("H-trace_callers", parse_trace_callers)
    return reg


class RealConstructorAdapter:
    """构造器适配器：available() / build(needs) 黑盒接口。"""

    def __init__(self, project_root, matrix_dir=None, parser_registry=None, inducer=None):
        self._project_root = str(project_root)
        self._matrix_dir = matrix_dir
        self._registry = parser_registry if parser_registry is not None else default_parser_registry()
        self._inducer = inducer  # 代理归纳钩子（design 决策 11）：调用方按暴露的归纳请求注入
        self._declared = []  # 构造器声明的结构化缺口（design 决策 5）
        self._induction_requests = []  # 未覆盖归纳请求（design 决策 11）

    def available(self):
        return True

    def declared_gaps(self):
        """构造器声明的结构化缺口（类型级 + 字段级原因），供编排器豁免与精确归因。"""
        return list(self._declared)

    def induction_requests(self):
        """构造器产出的未覆盖归纳请求，供编排器透传至最终响应（design 决策 11）。"""
        return list(self._induction_requests)

    def build(self, needs):
        """按缺口事实类型构造，返回 {事实类型: [实体]}（仓库形态）。"""
        needs = sorted(needs)
        if not needs:
            return {}
        # 按 fact-catalog 层级归组（符号层/事实层事实同样最小化保留，MUST NOT 全塞项目层
        # ——assemble_output 仅输出契约声明的层，层级丢失会导致产出被裁剪为空）。
        from catalog import LAYER_OF
        layered = {}
        for fact_type in needs:
            layered.setdefault(LAYER_OF.get(fact_type, "事实层"), []).append(fact_type)
        contract = {"project": self._project_root, "facts": layered}
        out = construct(contract, project_root=self._project_root,
                        matrix_dir=self._matrix_dir, parser_registry=self._registry,
                        inducer=self._inducer)
        self._declared = []
        self._induction_requests = []
        if "error" in out:
            return {}
        self._declared = [dict(g) for g in (out.get("gaps") or [])]
        self._induction_requests = [dict(r) for r in (out.get("induction_requests") or [])]
        produced = {}
        for items in (out.get("facts") or {}).values():
            for item in items:
                fact_type = item["type"]
                ev = item.get("evidence") or {}
                entity = dict(item.get("fields") or {})
                entity["_id"] = f"{fact_type}:{ev.get('file', '?')}:{ev.get('range', '?')}"
                if ev:
                    entity["evidence"] = ev
                produced.setdefault(fact_type, []).append(entity)
        # 字段级缺口派生：已产出实体中仍缺失的 fact-catalog 字段（差距段归因）
        from catalog import FIELDS
        for entities in produced.values():
            for entity in entities:
                fact_type = entity["_id"].split(":", 1)[0]
                for field in FIELDS.get(fact_type, []):
                    v = entity.get(field)
                    if v is None or v == "" or v == []:
                        if not any(d.get("type") == fact_type and d.get("field") == field
                                   for d in self._declared):
                            self._declared.append({
                                "type": fact_type, "field": field,
                                "reason": "构造后仍缺失（无对应信息数据项产出）",
                            })
        return produced
