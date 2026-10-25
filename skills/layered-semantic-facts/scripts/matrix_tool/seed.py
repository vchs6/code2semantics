"""播种脚本：调研报告 → 矩阵条目的忠实转换（确定性，可重复执行）。

输入：生产能力调研报告（markdown，结构固化为 survey tasks 第 5 条）。
输出：info-needs.yaml / producers.yaml / entries.yaml。

规则（spec「播种为报告的忠实转换」）：
- 同一报告两次播种结果完全一致；
- 报告增量只刷新对应条目（派生字段以报告为准；status/invocation_profile/runtime_guidance
  为本地状态，播种保留不重置）；
- 不编造报告中不存在的条目；识别不了的单元格报错停下，不做猜测性扩展。
"""
import re
import sys

from .common import (
    MATRIX_DIR,
    dump_yaml,
    load_yaml,
    SURVEY_REPORT,
    report_source_rel,
)

# ---------------------------------------------------------------------------
# 规范化映射表（标识符规范化，非内容编造；内容均取自报告原文）
# ---------------------------------------------------------------------------

# 信息需求显示名 → need id（slug 为标识符规范化；layer/fact_type 用报告原文）
NEED_SLUGS = {
    "项目用途/领域": ("project", "domain"),
    "模块划分": ("project", "modules"),
    "入口": ("project", "entries"),
    "构建与运行形态": ("project", "build_run"),
    "配置项": ("project", "configs"),
    "外部依赖": ("project", "dependencies"),
    "模块职责": ("module", "responsibility"),
    "模块间依赖": ("module", "dependencies"),
    "对外接口": ("module", "public_interface"),
    "公共接口": ("symbol", "public_api"),
    "类型定义": ("symbol", "types"),
    "符号关系": ("symbol", "relations"),
    "意图声明": ("symbol", "intent"),
    "调用关系": ("fact_a", "call_relation"),
    "数据流": ("fact_a", "dataflow"),
    "生命周期/状态": ("fact_a", "lifecycle"),
    "错误处理": ("fact_a", "error_handling"),
    "行为约定": ("fact_a", "behavior_contract"),
    "使用契约": ("fact_a", "usage_contract"),
    "元素实现语义": ("fact_b", "element_semantics"),
    # 第 4 节派生行（第 1 节"调用关系"行内声明的调用条件线索，归事实层 A）
    "调用条件线索": ("fact_a", "call_condition"),
}

# slug 段 → 层级名（供派生行补登记用）
SEG_LAYER = {
    "project": "项目层",
    "module": "模块层",
    "symbol": "符号层",
    "fact_a": "事实层A",
    "fact_b": "事实层B",
}

# 生产者单元格 → 生产者 id 列表（报告记法规范化；规模/语言取自 3.1 节）
PRODUCER_ALIASES = {
    "H-list_symbols": ["H-list_symbols"],
    "H-ast_grep": ["H-ast_grep"],
    "H-find_references": ["H-find_references"],
    "H-grep": ["H-grep"],
    "H-trace_callers": ["H-trace_callers"],
    "H-trace_callees": ["H-trace_callees"],
    "H-trace_callers/callees": ["H-trace_callers", "H-trace_callees"],
    "H-trace/ast_grep": ["H-trace_callers", "H-ast_grep"],
    "H-grep/ast_grep": ["H-grep", "H-ast_grep"],
    "H-ast_grep/tree-sitter": ["H-ast_grep", "X-tree_sitter"],
    "X-rustdoc JSON/ctags": ["X-rustdoc_json", "X-ctags"],
    "X-rust-analyzer call hierarchy": ["X-rust_analyzer"],
    "tree-sitter": ["X-tree_sitter"],
    "X-cargo metadata": ["X-cargo_metadata"],
    "X-ctags": ["X-ctags"],
    "X-rustdoc JSON": ["X-rustdoc_json"],
    "X-rust-analyzer": ["X-rust_analyzer"],
    "X-crates.io API": ["X-crates_io_api"],
}

# 3.1 节工具画像：producer id → (画像行匹配关键字, 规模, 支持语言)
PROFILE_ROWS = {
    "H-list_symbols": ("list_symbols", "小型", "多语言"),
    "H-trace_callers": ("list_symbols", "小型", "多语言"),
    "H-trace_callees": ("list_symbols", "小型", "多语言"),
    "H-ast_grep": ("ast_grep", "小型", "多语言"),
    "H-find_references": ("find_references", "小型", "语言无关"),
    "H-grep": ("grep", "小型", "语言无关"),
    "X-ctags": ("ctags", "小型", "多语言"),
    "X-cargo_metadata": ("cargo metadata", "小型", "Rust 专属"),
    "X-crates_io_api": ("crates.io Registry Web API", "小型", "语言无关"),
    "X-tree_sitter": ("tree-sitter", "中型", "多语言"),
    "X-rustdoc_json": ("rustdoc JSON", "中型", "Rust 专属"),
    "X-rust_analyzer": ("rust-analyzer", "大型", "Rust 专属"),
}

TOOL_NAMES = {
    "H-list_symbols": "list_symbols（宿主）",
    "H-trace_callers": "trace_callers（宿主）",
    "H-trace_callees": "trace_callees（宿主）",
    "H-ast_grep": "ast_grep（宿主）",
    "H-find_references": "find_references（宿主）",
    "H-grep": "grep（宿主）",
    "X-ctags": "universal-ctags（Rust 解析器）",
    "X-cargo_metadata": "cargo metadata",
    "X-crates_io_api": "crates.io Registry Web API",
    "X-tree_sitter": "tree-sitter-rust",
    "X-rustdoc_json": "rustdoc JSON",
    "X-rust_analyzer": "rust-analyzer（LSP）",
    "A-analysis_skill": "项目分析 Skill/子代理",
    "A-agent_fallback": "智能体归纳（A-归纳）",
}

PLATFORMS = ["linux"]  # 报告调研平台（标题与第 2 节实测环境）


def _norm_cell(cell):
    """去掉单元格中的括注与尾部修饰（括注内容为说明，不参与标识）。"""
    cell = re.sub(r"（[^）]*）", "", cell)
    return cell.strip().removesuffix(" 模式").removesuffix(" call hierarchy").strip()


def _producer_ids(cell):
    """生产者单元格 → id 列表（单元格可含多个生产者，以 ＋ 分隔）。
    识别不了报错，不编造。"""
    ids = []
    for part in re.split("＋", cell):
        part = part.strip()
        if not part:
            continue
        token = _norm_cell(part)
        if token.startswith("A-项目分析"):
            ids.append("A-analysis_skill")
        elif token.startswith("A-归纳"):
            ids.append("A-agent_fallback")
        elif token in PRODUCER_ALIASES:
            ids.extend(PRODUCER_ALIASES[token])
        else:
            raise ValueError(f"播种失败：生产者记法无法识别（不做猜测性扩展）：{part!r}")
    return ids


def _tier(producer_id):
    if producer_id.startswith("A-analysis"):
        return "项目分析Skill"
    if producer_id.startswith("A-"):
        return "智能体兜底"
    return "工具直出"


def _verdict(cell):
    for v in ("部分可完成", "不可完成", "可完成"):
        if v in cell:
            return v
    raise ValueError(f"播种失败：判定等级无法识别：{cell!r}")


def _split_rows(lines, start):
    """从 start 行起定位第一个 markdown 表格，收集其数据行（跳过表头与分隔行）。

    返回 (cells, 行号)；start 处先跳过非表格行（标题、空行、引言），进入表格后
    遇到首个非表格行即结束。
    """
    i = start - 1
    n = len(lines)
    while i < n and not lines[i].startswith("|"):
        i += 1
    rows = []
    while i < n and lines[i].startswith("|"):
        cells = [c.strip() for c in lines[i].rstrip("\n").strip("|").split("|")]
        if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            rows.append((cells, i + 1))  # 1-based
        i += 1
    return rows


def _section(lines, heading_prefix):
    for i, l in enumerate(lines):
        if l.startswith(heading_prefix):
            return i + 1
    raise ValueError(f"播种失败：报告中缺少小节 {heading_prefix!r}")


def parse_report(path):
    text = path.read_text("utf-8")
    lines = text.splitlines()

    # 第 1 节信息需求
    s1 = _split_rows(lines, _section(lines, "## 1."))
    needs = []
    src_rel = report_source_rel()
    for cells, lineno in s1:
        layer, fact_type, required_info = cells[0], cells[1], cells[2]
        if layer == "层":  # 表头
            continue
        layer = re.sub(r"\s+", "", layer)  # "事实层 A" → "事实层A"
        seg, slug = NEED_SLUGS[fact_type]
        needs.append({
            "id": f"need.{seg}.{slug}",
            "layer": layer,
            "fact_type": fact_type,
            "required_info": required_info,
            "evidence": {
                "source": src_rel,
                "line_start": lineno,
                "line_end": lineno,
            },
        })
    need_layer = {n["fact_type"]: n["layer"] for n in needs}
    need_id_by_fact = {n["fact_type"]: n["id"] for n in needs}

    # 3.1 节工具画像行号（供生产者证据回链）
    p31_start = _section(lines, "### 3.1")
    profile_lineno = {}
    for cells, lineno in _split_rows(lines, p31_start):
        for pid, (key, _, _) in PROFILE_ROWS.items():
            if key in cells[0]:
                profile_lineno[pid] = lineno

    # 第 4 节覆盖矩阵
    s4 = _split_rows(lines, _section(lines, "## 4."))
    src_rel = report_source_rel()
    derived = {}
    for cells, lineno in s4:
        if cells[0] == "信息需求":
            continue
        name, verdict_cell, producer_cell, evidence_cell = cells[0], cells[1], cells[2], cells[3]
        fact_name = name.split("（")[0].strip()
        if fact_name in need_id_by_fact:
            need_id = need_id_by_fact[fact_name]
            layer = need_layer[fact_name]
        elif name in NEED_SLUGS:
            seg, slug = NEED_SLUGS[name]
            need_id = f"need.{seg}.{slug}"
            layer = SEG_LAYER[seg]
            # 派生行（第 1 节事实类型表无此行）补登记进 needs，避免孤儿条目
            if not any(n["id"] == need_id for n in needs):
                needs.append({
                    "id": need_id,
                    "layer": layer,
                    "fact_type": name,
                    "required_info": "调用条件线索（caller→callee 的调用条件）",
                    "evidence": {"source": src_rel, "line_start": lineno, "line_end": lineno},
                })
                need_id_by_fact[name] = need_id
                need_layer[name] = layer
        else:
            raise ValueError(f"播种失败：第 4 节信息需求无法对应第 1 节事实类型：{name!r}")
        verdict = _verdict(verdict_cell)
        for pid in _producer_ids(producer_cell):
            derived[(need_id, pid)] = {
                "need_id": need_id,
                "producer_id": pid,
                "verdict": verdict,
                "production_tier": _tier(pid),
                "platforms": list(PLATFORMS),
                "runtime_guidance": "",
                "invocation_profile": {
                    "structure_placeholder": "待 add-info-parser 注册接口协议定稿回填（design OQ3）",
                    "command": None,
                    "timeout_seconds": None,
                    "retries": None,
                    "output_type": None,
                    "parser_id": None,
                },
                "evidence": {
                    "source": src_rel,
                    "line_start": lineno,
                    "line_end": lineno,
                    "note": evidence_cell,
                },
                "status": "未点亮",
            }

    # 生产者定义（来自矩阵实际引用；画像取 3.1）
    producer_ids = sorted({pid for _, pid in derived})
    producers = []
    for pid in producer_ids:
        if pid in PROFILE_ROWS and pid in profile_lineno:
            _, scale, langs = PROFILE_ROWS[pid]
            lineno = profile_lineno[pid]
        else:
            scale, langs, lineno = None, [], None
            # A-* 生产者证据回链到第 4 节生产者记法说明行
            for i, l in enumerate(lines, 1):
                if "生产者记法" in l:
                    lineno = i
                    break
            if lineno is None:
                raise ValueError(f"播种失败：生产者 {pid} 找不到证据行")
        producers.append({
            "id": pid,
            "name": TOOL_NAMES[pid],
            "kind": "agent" if pid.startswith("A-")
            else ("host_tool" if pid.startswith("H-") else "external_tool"),
            "scale": scale,
            "languages": [langs] if langs else [],
            "evidence": {
                "source": src_rel,
                "line_start": lineno,
                "line_end": lineno,
            },
        })

    return needs, producers, derived


def seed(report_path, matrix_dir):
    """播种。返回 (added, refreshed, removed) 统计。"""
    if not report_path.is_file():
        raise FileNotFoundError(f"播种失败：调研报告不存在：{report_path}（矩阵保持原状，不生成条目）")
    needs, producers, derived = parse_report(report_path)

    entries_f = matrix_dir / "entries.yaml"
    existing_doc = load_yaml(entries_f) if entries_f.is_file() else {"schema_version": 1, "revision": 0, "identifier_note": "", "entries": []}
    old = {(e["need_id"], e["producer_id"]): e for e in existing_doc.get("entries", [])}

    added = refreshed = removed = 0
    new_entries = []
    for key in sorted(derived):
        src = derived[key]
        if key in old:
            e = old[key]
            # 派生字段以报告为准；本地状态字段保留
            changed = any(e[f] != src[f] for f in ("verdict", "production_tier", "platforms", "evidence"))
            if changed:
                refreshed += 1
            merged = dict(src)
            for f in ("status", "invocation_profile", "runtime_guidance"):
                merged[f] = e[f]
            new_entries.append(merged)
        else:
            added += 1
            new_entries.append(src)
    removed = len(old) - len(set(old) & set(derived))

    doc = {
        "schema_version": 1,
        "revision": existing_doc.get("revision", 0) + (1 if (added or refreshed or removed) else 0),
        "identifier_note": "行维度标识 need.<事实类型slug> 为占位格式，待构造器信息需求清单（add-semantic-fact-constructor design OQ1）对齐后统一替换。",
        "entries": new_entries,
    }
    dump_yaml(doc, entries_f)
    dump_yaml({"schema_version": 1, "producers": producers}, matrix_dir / "producers.yaml")
    dump_yaml({
        "schema_version": 1,
        "identifier_note": "占位标识：need.<事实类型slug>，待 add-semantic-fact-constructor 信息需求清单对齐后统一替换",
        "needs": needs,
    }, matrix_dir / "info-needs.yaml")
    return added, refreshed, removed


def main():
    matrix_dir = MATRIX_DIR
    try:
        added, refreshed, removed = seed(SURVEY_REPORT, matrix_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[matrix-seed] {exc}", file=sys.stderr)
        return 1
    print(f"播种完成：新增 {added}，刷新 {refreshed}，移除 {removed}（矩阵目录：{matrix_dir}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
