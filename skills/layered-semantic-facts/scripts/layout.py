"""Skill 布局统一加载入口（design 决策 2）：锚定 Skill 根的布局解析。

- 组件模块路径注册：scripts/ 下的组件（查询流程、构造器、解析器、矩阵工具）
- 数据工件解析：assets/matrix（能力矩阵）、assets/schema（契约机读 schema）
- 缺件报可定位错误：缺失对象与其期望布局位置

全部跨组件 import 与数据加载 MUST 经本模块；各组件与测试 MUST NOT 自行 sys.path 拼凑。
"""
import sys
from pathlib import Path


class LayoutError(Exception):
    """布局缺件：缺失对象与其期望布局位置可定位。"""


# Skill 根（scripts/ 的父目录）
SKILL_ROOT = Path(__file__).resolve().parents[1]

# 数据工件种类 → 期望布局位置（相对 Skill 根）
ASSET_KINDS = {"matrix": "assets/matrix", "schema": "assets/schema"}


def resolve_asset(root, kind):
    """解析数据工件目录。root 为 Skill 根；缺件报 LayoutError（含期望位置）。"""
    rel = ASSET_KINDS.get(kind)
    if rel is None:
        raise LayoutError(f"未知数据工件种类：{kind}（期望布局位置：assets/<{'|'.join(ASSET_KINDS)}>）")
    path = Path(root) / rel
    if not path.is_dir():
        raise LayoutError(f"数据工件缺失：{rel}（期望布局位置：{path}）")
    return path


def component_paths(root):
    """返回组件模块搜索路径（scripts/ 下各组件目录 + scripts/ 本身）。缺件报 LayoutError。"""
    root = Path(root)
    scripts = root / "scripts"
    if not scripts.is_dir():
        raise LayoutError(f"程序代码目录缺失：scripts/（期望布局位置：{scripts}）")
    return [scripts]


def register_skill_paths(root=None):
    """把 Skill 组件路径注入 sys.path（一处注入，tests conftest 与入口程序共用）。"""
    root = Path(root) if root else SKILL_ROOT
    for p in component_paths(root):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    return root
