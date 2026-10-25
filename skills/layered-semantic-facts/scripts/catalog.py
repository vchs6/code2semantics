"""fact-catalog 的程序化词汇（封闭世界的单一事实源 = references/fact-catalog.md）。

本模块从 fact-catalog.md 确定性解析出「事实类型 → 字段」与「事实类型 → 层级」映射，
供覆盖比对与合成器消费；不修改 fact-catalog.md（单一事实源约束）。

子树字段映射（subtree_map：字段 → 子事实类型）不在 fact-catalog 中显式标注，
由调用方作为显式参数注入（见 coverage.compare 的 subtree_map 形参），
待 SFRS 实体稳定标识方案回填后固化。
"""
import re
from pathlib import Path

FACT_CATALOG = Path(__file__).resolve().parents[1] / "references" / "fact-catalog.md"

_LAYER_RE = re.compile(r"^##\s+(.+?)(?:（.*)?$")
_FIELD_RE = re.compile(r"`([^`]+)`")


def parse_catalog(path=FACT_CATALOG):
    """解析 fact-catalog.md，返回 (fields, layer_of)。

    fields: {事实类型: [字段, ...]}
    layer_of: {事实类型: 层级名}
    """
    fields = {}
    layer_of = {}
    current_layer = None
    for line in path.read_text("utf-8").splitlines():
        m = _LAYER_RE.match(line)
        if m:
            current_layer = m.group(1).strip()
            continue
        if not line.startswith("|") or "可查询字段" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        fact_type, field_cell = cells[0], cells[1]
        if fact_type.startswith("---") or not fact_type:
            continue
        fact_fields = _FIELD_RE.findall(field_cell)
        if fact_fields:
            fields[fact_type] = fact_fields
            layer_of[fact_type] = current_layer
    return fields, layer_of


FIELDS, LAYER_OF = parse_catalog()
