"""Skill 布局统一加载入口测试（spec「组件与数据工件固定布局可寻址」两 scenario）。"""
import pytest  # noqa: E402

from layout import SKILL_ROOT, LayoutError, component_paths, resolve_asset  # noqa: E402


def _target_layout(tmp_path):
    """构造目标布局桩：scripts/ 与 assets/{matrix,schema} 齐备的 Skill 目录。"""
    (tmp_path / "scripts").mkdir()
    for kind in ("matrix", "schema"):
        (tmp_path / "assets" / kind).mkdir(parents=True)
    return tmp_path


def test_组件与工件寻址成功(tmp_path):
    root = _target_layout(tmp_path)
    assert (root / "scripts").is_dir()
    assert resolve_asset(root, "matrix") == root / "assets" / "matrix"
    assert resolve_asset(root, "schema") == root / "assets" / "schema"
    paths = component_paths(root)
    assert root / "scripts" in paths


def test_组件缺失可定位(tmp_path):
    root = tmp_path  # 无 scripts/、无 assets/
    with pytest.raises(LayoutError) as ei:
        resolve_asset(root, "matrix")
    msg = str(ei.value)
    assert "assets/matrix" in msg  # 缺失对象与期望布局位置可定位


def test_真实Skill根解析_迁移前不要求assets存在():
    # 真实 Skill 根锚定正确即可；assets 在迁移（任务 2.2）后才存在
    assert SKILL_ROOT.name == "layered-semantic-facts"
    assert (SKILL_ROOT / "SKILL.md").exists()
