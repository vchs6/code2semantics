"""矩阵更新脚本：解析器落地/新工具接入时点亮条目，版本化保留变更痕迹。

spec「更新点亮条目且版本化」：
- 点亮：某信息需求对应的生产者及其解析器登记完成 → 条目 status 变为已点亮，可被构造器查询到；
- 版本化：每次更新 revision 递增，变更前后内容写入 history/ 供追溯。

本变更聚焦「仅点亮项目级信息的生产工具」：只对项目层（layer=项目层）中
production_tier=工具直出 的条目执行点亮，A-* 智能体兜底及其它层级先不点亮。

点亮需提供 command（调用剖面），command 表 PROJECT_TOOL_COMMANDS 取自调研报告第 2/3 节
的项目级工具命令（确定性）。parser_id 待 add-info-parser 注册协议定稿后回填（design OQ3），
当前置 None 占位。
"""
import datetime
from pathlib import Path

from .common import (
    MATRIX_DIR,
    dump_yaml,
    load_yaml,
)
from .validate import validate_matrix

# 项目级工具直出生产者的命令表（来源：调研报告第 2/3 节）
PROJECT_TOOL_COMMANDS = {
    "H-list_symbols": {"command": "list_symbols", "output_type": "symbols"},
    "H-ast_grep": {"command": "ast_grep", "output_type": "ast-matches"},
    "H-grep": {"command": "grep", "output_type": "lines"},
    "X-cargo_metadata": {"command": "cargo metadata --format-version 1 --no-deps", "output_type": "json"},
    "X-crates_io_api": {"command": "GET https://crates.io/api/v1/crates/{crate}", "output_type": "json"},
    "X-rustdoc_json": {"command": "cargo rustdoc --lib -- -Z unstable-options --output-format json", "output_type": "json"},
}


def _resolve_need_ids(needs_doc, need_ids, layer):
    """筛出目标 need id 集合。need_ids 与 layer 至少一个非 None。"""
    if need_ids is None and layer is None:
        raise ValueError("light_up 需提供 need_ids 或 layer")
    target = set()
    for n in needs_doc["needs"]:
        if need_ids is not None and n["id"] in set(need_ids):
            target.add(n["id"])
        elif layer is not None and n["layer"] == layer:
            target.add(n["id"])
    return target


def light_up(need_ids=None, layer=None, production_tier="工具直出",
             commands=None, matrix_dir=None):
    """点亮符合条件的条目，返回点亮条目数。

    - need_ids / layer 二选一筛信息需求（layer 通常取"项目层"）；
    - production_tier 筛生产者层级（默认"工具直出"，A-* 兜底不点亮）；
    - commands: {producer_id: {command, timeout_seconds?, retries?, output_type?, parser_id?}}，
      缺省用 PROJECT_TOOL_COMMANDS；无 command 的生产者不点亮（解析器未登记）。
    """
    matrix_dir = Path(matrix_dir) if matrix_dir else MATRIX_DIR
    commands = commands if commands is not None else PROJECT_TOOL_COMMANDS

    entries_doc = load_yaml(matrix_dir / "entries.yaml")
    needs_doc = load_yaml(matrix_dir / "info-needs.yaml")
    target = _resolve_need_ids(needs_doc, need_ids, layer)

    changed = []
    for e in entries_doc["entries"]:
        if e["need_id"] not in target:
            continue
        if e["production_tier"] != production_tier:
            continue
        pid = e["producer_id"]
        cmd = commands.get(pid)
        if not cmd or not cmd.get("command"):
            continue  # 无命令（解析器未登记）→ 不点亮
        before = {"status": e["status"], "command": e["invocation_profile"].get("command")}
        prof = dict(e["invocation_profile"])
        prof.pop("structure_placeholder", None)  # 点亮即回填，移除占位标记
        prof["command"] = cmd["command"]
        prof["timeout_seconds"] = cmd.get("timeout_seconds")
        prof["retries"] = cmd.get("retries")
        prof["output_type"] = cmd.get("output_type")
        prof["parser_id"] = cmd.get("parser_id")
        e["invocation_profile"] = prof
        e["status"] = "已点亮"
        after = {"status": e["status"], "command": e["invocation_profile"].get("command")}
        changed.append({
            "need_id": e["need_id"], "producer_id": pid,
            "before": before, "after": after,
        })

    if changed:
        entries_doc["revision"] = entries_doc.get("revision", 0) + 1
        dump_yaml(entries_doc, matrix_dir / "entries.yaml")
        history_dir = matrix_dir / "history"
        history_dir.mkdir(exist_ok=True)
        dump_yaml({
            "revision": entries_doc["revision"],
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "changed": changed,
        }, history_dir / f"rev-{entries_doc['revision']}.yaml")

    # 校验接入更新出口
    errors = validate_matrix(matrix_dir)
    if errors:
        raise ValueError("点亮后一致性校验失败：\n" + "\n".join(errors))
    return len(changed)
