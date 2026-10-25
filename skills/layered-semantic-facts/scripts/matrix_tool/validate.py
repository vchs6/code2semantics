"""一致性校验：schema 合规、无孤儿条目、证据可回链、判定与状态自洽、无重复条目。

校验不通过返回可定位的失败原因列表（exit code 1）。
"""
import sys

from .common import (
    ENTRIES_FILE,
    INFO_NEEDS_FILE,
    PRODUCERS_FILE,
    REPO_ROOT,
    load_yaml,
    schema_validate,
)


def _evidence_link_errors(evidence, where):
    """证据回链检查：source 文件存在、行号范围在文件内"""
    errors = []
    source = REPO_ROOT / evidence["source"]
    if not source.is_file():
        return [f"证据无法回链 {where}: 文件不存在 {evidence['source']}"]
    n_lines = len(source.read_text("utf-8").splitlines())
    lo, hi = evidence["line_start"], evidence["line_end"]
    if lo > hi:
        errors.append(f"证据无法回链 {where}: 行号范围倒置 {lo}-{hi}")
    elif lo < 1 or hi > n_lines:
        errors.append(
            f"证据无法回链 {where}: 行号 {lo}-{hi} 超出文件实际行数 {n_lines}（{evidence['source']}）"
        )
    return errors


def validate_matrix(root=None):
    """校验整个矩阵目录，返回错误信息列表；空列表 = 通过"""
    if root is None:
        entries_f, producers_f, needs_f = ENTRIES_FILE, PRODUCERS_FILE, INFO_NEEDS_FILE
    else:
        entries_f = root / "entries.yaml"
        producers_f = root / "producers.yaml"
        needs_f = root / "info-needs.yaml"

    errors = []
    entries_doc = load_yaml(entries_f)
    producers_doc = load_yaml(producers_f)
    needs_doc = load_yaml(needs_f)

    for doc, name in [
        (entries_doc, "entries"),
        (producers_doc, "producers"),
        (needs_doc, "info-needs"),
    ]:
        errors.extend(schema_validate(doc, name))

    producer_ids = {p["id"] for p in producers_doc["producers"]}
    need_ids = {n["id"] for n in needs_doc["needs"]}

    seen = set()
    for i, e in enumerate(entries_doc["entries"]):
        where = f"条目[{i}] ({e.get('need_id')}×{e.get('producer_id')})"
        # 孤儿条目：引用的生产者/信息需求无定义
        if e["need_id"] not in need_ids:
            errors.append(f"孤儿条目 {where}: 信息需求 {e['need_id']} 未在 info-needs.yaml 定义")
        if e["producer_id"] not in producer_ids:
            errors.append(f"孤儿条目 {where}: 生产者 {e['producer_id']} 未在 producers.yaml 定义")
        # 重复条目
        key = (e["need_id"], e["producer_id"])
        if key in seen:
            errors.append(f"重复条目 {where}: 同一信息需求×生产者出现多次")
        seen.add(key)
        # 证据回链
        errors.extend(_evidence_link_errors(e["evidence"], where))
        # 判定与状态自洽
        if e["status"] == "已点亮" and e["verdict"] == "不可完成":
            errors.append(f"判定与状态不自洽 {where}: 判定为不可完成却已点亮")
        # 工具直出条目点亮须有可执行命令；智能体兜底/分析 Skill 层无命令（生产工具即代理自身）
        if (e["status"] == "已点亮" and e["production_tier"] == "工具直出"
                and not e["invocation_profile"].get("command")):
            errors.append(f"判定与状态不自洽 {where}: 已点亮但调用剖面缺少 command")

    for j, p in enumerate(producers_doc["producers"]):
        errors.extend(
            _evidence_link_errors(p["evidence"], f"生产者[{j}] ({p.get('id')})")
        )
    for k, n in enumerate(needs_doc["needs"]):
        errors.extend(_evidence_link_errors(n["evidence"], f"信息需求[{k}] ({n.get('id')})"))

    return errors


def main():
    errors = validate_matrix()
    if errors:
        for msg in errors:
            print(f"[matrix-validate] {msg}", file=sys.stderr)
        print(f"校验不通过：{len(errors)} 处问题", file=sys.stderr)
        return 1
    print("矩阵一致性校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
