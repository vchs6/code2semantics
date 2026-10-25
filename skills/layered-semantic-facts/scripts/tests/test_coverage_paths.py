"""覆盖比对节点粒度适配测试（任务 1.2，design 决策 2；spec「实体级未命中判定」）。"""
from coverage import compare


def test_值属性缺失按实体级输出():
    required = {"项目用途/领域": ["name", "domain"]}
    returned = {"项目用途/领域": [{"_id": "p1", "name": "x", "domain": ""}]}
    gaps = compare(required, returned)
    kinds = {(g["entity"], g["field"], g["kind"]) for g in gaps}
    assert ("p1", "domain", "值属性缺失") in kinds


def test_未请求的子树节点不参与判缺():
    """请求仅定位 模块划分 节点本身（无 path 请求 模块职责）时，
    模块职责 子树不判缺、不触发构造（spec：未被消费方请求的子树节点不参与判缺）。"""
    required = {"模块划分": ["modules"]}
    returned = {"模块划分": [{"_id": "m0", "modules": ["a", "b"]}]}
    gaps = compare(required, returned)
    assert gaps == []  # modules 有值即命中；模块职责未请求 → 不判缺


def test_已请求路径的子树递归判缺():
    """请求以 path 定位到子树节点时，递归分解按实体级判定（既有语义保留）。"""
    required = {"模块划分": ["modules"]}
    subtree_map = {"模块划分": {"modules": "模块职责"}}
    requested_paths = {("模块划分", "modules")}
    returned = {
        "模块划分": [{"_id": "m0", "modules": ["a"]}],
        "模块职责": [{"_id": "mod_a", "path": "x", "responsibility": "", "capabilities": []}],
    }
    gaps = compare(required, returned, subtree_map=subtree_map,
                   requested_paths=requested_paths)
    kinds = {(g["type"], g["field"], g["kind"]) for g in gaps}
    assert ("模块职责", "responsibility", "值属性缺失") in kinds  # 已请求 → 递归判缺


def test_子树缺省不递归_向后兼容():
    """未传 requested_paths 时保持既有行为（子树字段缺失即递归判缺）。"""
    required = {"模块划分": ["modules"]}
    subtree_map = {"模块划分": {"modules": "模块职责"}}
    returned = {"模块划分": [{"_id": "m0", "modules": []}]}
    gaps = compare(required, returned, subtree_map=subtree_map)
    assert gaps  # 既有行为：子树字段缺失即递归判缺
    assert any(g["kind"] == "子树缺失" for g in gaps)
