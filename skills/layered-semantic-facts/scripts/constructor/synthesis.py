"""合成分析（任务 2.1/2.2/2.3）：以 fact-catalog 为封闭边界，派生「事实类型 → 信息需求」分解。

确定性：同一契约（事实类型集）两次运行产出相同清单；清单覆盖 fact-catalog 全部
事实类型字段，无法映射到下层项目信息的字段记入差距段（unmappable），不静默丢弃。

信息需求清单是本变更的确定性交付物（design 决策 4），落盘后作为后续调研的封闭输入。
"""
import json
from pathlib import Path

from catalog import FIELDS, LAYER_OF

# 清单落盘位置（构造器变更目录内，作为确定性交付物随仓库提交）
from layout import SKILL_ROOT

_REPO_ROOT = SKILL_ROOT.parents[1]
_CONSTRUCTOR_DIR = _REPO_ROOT / "openspec" / "changes" / "add-semantic-fact-constructor"
INFO_NEEDS_FILE = _CONSTRUCTOR_DIR / "info-needs.md"

# 事实类型字段 → 信息需求（确定性派生表；依据调研报告第 1 节「信息需求派生」的对应关系）
# 语义归纳类字段（无确定算法）映射到「归纳」信息需求，由生产阶梯的兜底层承担。
FIELD_INFO_NEEDS = {
    "项目用途/领域": {
        "name": "crate 名称与元数据（cargo metadata description/readme 字段）",
        "domain": "领域描述归纳（description 字段直出 + 归纳）",
        "doc": "README 入口位置（cargo metadata readme 字段）",
    },
    "模块划分": {
        "modules": "workspace 成员/顶层 mod 清单（cargo metadata members + 源码 mod 声明）",
    },
    "入口": {
        "entries": "bin target 清单与 src_path（cargo metadata targets）",
    },
    "构建与运行形态": {
        "build": "构建系统与产物形态（cargo metadata edition/crate_types）",
        "run": "运行/测试/验证命令（cargo 惯例命令）",
        "deployment": "部署形态归纳（CLI/库/服务）",
    },
    "配置项": {
        "configs": "配置文件/环境变量调用点（源码 env::var/config 模式检索）",
    },
    "外部依赖": {
        "dependencies": "依赖清单（cargo metadata dependencies：name/req/kind/optional）",
    },
    "模块职责": {
        "path": "模块路径（mod 声明与文件结构）",
        "responsibility": "职责描述归纳",
        "capabilities": "暴露能力归纳（pub 项清单 + 归纳）",
    },
    "模块间依赖": {
        "direction": "依赖方向（crate 级依赖 + 源码 use/mod 结构）",
        "type": "依赖类型判定归纳（调用/数据/配置）",
    },
    "对外接口": {
        "public_entries": "模块 pub 入口清单（pub fn/struct 声明检索）",
    },
    "公共接口": {
        "signature": "函数/方法签名文本（ctags signature / rustdoc JSON）",
        "visibility": "可见性（pub 声明检索）",
        "module": "符号-模块归属（文件路径映射）",
    },
    "类型定义": {
        "kind": "结构体/枚举/trait 分类（符号清单 kind）",
        "description": "类型语义描述归纳",
        "fields": "字段/variant 清单（ctags field/variant kinds）",
    },
    "符号关系": {
        "relation": "继承/实现/组合关系（impl/trait 模式匹配）",
        "target": "目标符号（impl T for U 的 T/U）",
        "module": "符号-模块归属（文件路径映射）",
    },
    "意图声明": {
        "intent": "doc 注释原文（///、//! 文本抽取，与符号绑定）",
    },
    "调用关系": {
        "caller": "调用方符号（调用链工具输出）",
        "callee": "被调方符号（调用链工具输出）",
        "condition": "调用条件线索归纳（分支上下文）",
    },
    "数据流": {
        "source": "数据产生点归纳（变量级数据流分析）",
        "sink": "数据消费点归纳（变量级数据流分析）",
    },
    "生命周期/状态": {
        "resource": "资源创建/释放点（Drop impl/new 模式检索）",
        "transitions": "状态迁移语义归纳",
    },
    "错误处理": {
        "error_type": "错误类型（Result/自定义错误类型检索）",
        "propagation": "传播方式（?/match Err 模式检索）",
        "recovery": "恢复策略归纳",
    },
    "行为约定": {
        "invariant": "不变量归纳",
        "side_effect": "副作用归纳",
        "timing": "并发/时序约束归纳",
    },
    "使用契约": {
        "preconditions": "前置条件归纳（doc panics/Errors 段 + 上下文）",
        "parameter_constraints": "参数约束（签名类型约束直出 + 归纳）",
        "guarantees": "返回保证归纳（签名 + doc）",
    },
    "元素实现语义": {
        "summary": "行为摘要/算法意图归纳",
        "control_flow": "分支/循环结构（AST 模式直出）",
        "data_flow": "变量级数据流归纳",
    },
}

# 无法由工具直出的纯归纳字段（差距段：生产阶梯的兜底层承担，非工具信息需求）
_UNMAPPABLE_NOTE = (
    "以下字段为语义归纳类信息，无确定算法可依，不映射为工具信息需求；"
    "其生产按生产阶梯由项目分析 Skill / 智能体兜底承担（见调研报告第 4/5 节）。"
)


def _is_inductive(field_need):
    """字段信息需求是否为归纳类（含「归纳」标注）。"""
    return "归纳" in field_need


def derive_info_needs(fact_types):
    """对给定事实类型集派生信息需求清单（确定性）。

    返回 [{"fact_type", "layer", "field", "info_need", "inductive"}]。
    """
    needs = []
    for fact_type in sorted(fact_types):
        field_map = FIELD_INFO_NEEDS.get(fact_type)
        if field_map is None:
            continue
        for field, info_need in field_map.items():
            needs.append({
                "fact_type": fact_type,
                "layer": LAYER_OF.get(fact_type, "事实层"),
                "field": field,
                "info_need": info_need,
                "inductive": _is_inductive(info_need),
            })
    return needs


def build_info_needs(fact_types=None):
    """构建信息需求清单（全量或指定事实类型），含差距段。

    fact_types 缺省为 fact-catalog 全部事实类型（封闭边界）。
    返回 {"needs": [...], "unmappable": [...], "note": str}。
    """
    if fact_types is None:
        fact_types = sorted(FIELDS)
    needs = derive_info_needs(fact_types)

    # 差距段：纯归纳字段（无工具直出部分）记入 unmappable，不静默丢弃
    unmappable = []
    for fact_type in fact_types:
        field_map = FIELD_INFO_NEEDS.get(fact_type) or {}
        for field, info_need in field_map.items():
            if info_need.startswith(("职责描述归纳", "部署形态归纳", "依赖类型判定归纳",
                                     "类型语义描述归纳", "调用条件线索归纳", "恢复策略归纳",
                                     "不变量归纳", "副作用归纳", "并发/时序约束归纳",
                                     "前置条件归纳", "返回保证归纳", "行为摘要", "变量级数据流归纳",
                                     "数据产生点归纳", "数据消费点归纳", "状态迁移语义归纳",
                                     "领域描述归纳", "暴露能力归纳")):
                unmappable.append({"fact_type": fact_type, "field": field, "info_need": info_need})

    return {"needs": needs, "unmappable": unmappable, "note": _UNMAPPABLE_NOTE}


def write_info_needs_file():
    """把信息需求清单落盘为 Markdown（确定性交付物，任务 2.2）。"""
    full = build_info_needs()
    lines = ["# 信息需求清单（构造器合成分析产出）", "",
             f"> {_UNMAPPABLE_NOTE}", "",
             "## 信息需求条目", "",
             "| 事实类型 | 层 | 字段 | 信息需求 | 归纳类 |",
             "|---|---|---|---|---|"]
    for n in full["needs"]:
        lines.append(f"| {n['fact_type']} | {n['layer']} | {n['field']} | {n['info_need']} | {'是' if n['inductive'] else '否'} |")
    lines += ["", "## 差距段（无法映射为工具信息需求的字段）", ""]
    for u in full["unmappable"]:
        lines.append(f"- {u['fact_type']}.{u['field']}：{u['info_need']}")
    INFO_NEEDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    INFO_NEEDS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return INFO_NEEDS_FILE
