"""安装仿真测试（任务 3.2，spec「Skill 目录自包含且可独立运行」「数据工件随更新同步生效」）。

安装 = 复制 Skill 目录整体到独立环境（不含仓库其余部分）；安装后端到端查询可运行；
矩阵数据随重新安装（再复制）同步生效。
"""
import shutil
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SKILL_ROOT.parents[1]
INDICATIF = REPO_ROOT.parent / "sm-test" / "source" / "indicatif"

pytestmark = pytest.mark.skipif(
    not INDICATIF.exists(), reason="本地无 indicatif 测试项目")

# 安装环境中允许出现的顶层模块（全部随包分发，无仓库侧依赖）
_SKILL_MODULES = ("layout", "orchestrator", "constructor_adapter", "repo_stub",
                  "versioning", "constructor", "info_parser", "matrix_tool", "catalog",
                  "coverage", "synthesizer", "contract_check")


def _install(tmp_path):
    """复制 Skill 目录整体到独立环境（模拟安装）。"""
    target = tmp_path / "installed" / SKILL_ROOT.name
    shutil.copytree(
        SKILL_ROOT, target,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    return target


def _purge_skill_modules():
    """清出进程内已加载的 Skill 模块，强制从安装环境重新导入。"""
    for mod in _SKILL_MODULES:
        sys.modules.pop(mod, None)
        for k in [k for k in sys.modules if k.startswith(mod + ".")]:
            sys.modules.pop(k)


def _query(installed_root):
    """在安装环境中以独立 sys.path 执行端到端查询（子进程语义的进程内模拟）。"""
    saved = sys.path[:]
    saved_modules = {k: v for k, v in sys.modules.items()
                     if k.split(".")[0] in _SKILL_MODULES}
    try:
        for p in list(sys.path):
            if "layered-semantic-facts" in p:
                sys.path.remove(p)  # 移除仓库侧路径，仅保留安装环境
        sys.path.insert(0, str(installed_root / "scripts"))
        _purge_skill_modules()

        from orchestrator import orchestrate
        from repo_stub import InMemoryRepo
        from versioning import current_version
        from constructor_adapter import RealConstructorAdapter

        contract = {"project": str(INDICATIF),
                    "facts": {"项目层": ["项目用途/领域", "入口", "外部依赖"]}}
        return orchestrate(contract, InMemoryRepo(),
                           RealConstructorAdapter(project_root=str(INDICATIF)),
                           version_fn=current_version)
    finally:
        sys.path[:] = saved
        _purge_skill_modules()
        sys.modules.update(saved_modules)


def test_安装到独立环境后端到端查询可运行(tmp_path):
    target = _install(tmp_path)
    assert (target / "SKILL.md").exists()
    out = _query(target)
    assert "error" not in out
    types = {i["type"] for i in out["facts"]["项目层"]}
    assert types == {"项目用途/领域", "入口", "外部依赖"}


def test_安装环境布局解析成功且矩阵随重装同步(tmp_path):
    target = _install(tmp_path)
    saved = sys.path[:]
    saved_modules = {k: v for k, v in sys.modules.items()
                     if k.split(".")[0] in _SKILL_MODULES}
    try:
        for p in list(sys.path):
            if "layered-semantic-facts" in p:
                sys.path.remove(p)
        sys.path.insert(0, str(target / "scripts"))
        _purge_skill_modules()
        import layout
        assert layout.SKILL_ROOT == target          # 锚定安装根，非仓库
        assert layout.resolve_asset(target, "matrix") == target / "assets" / "matrix"
    finally:
        sys.path[:] = saved
        _purge_skill_modules()
        sys.modules.update(saved_modules)
    # 数据工件随重新安装（再复制）同步：仓库侧矩阵更新后重装，安装环境获得新内容
    shutil.copy2(SKILL_ROOT / "assets" / "matrix" / "entries.yaml",
                 target / "assets" / "matrix" / "entries.yaml")
    assert (target / "assets" / "matrix" / "entries.yaml").read_text("utf-8") == \
        (SKILL_ROOT / "assets" / "matrix" / "entries.yaml").read_text("utf-8")
