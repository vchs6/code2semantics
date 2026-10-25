"""覆盖比对 spec「实体级未命中判定」场景测试。"""
from coverage import compare  # noqa: E402


def test_值属性缺失_仅该实体进缺口():
    required = {"项目用途/领域": ["name", "domain", "doc"]}
    returned = {
        "项目用途/领域": [
            {"_id": "e1", "name": "indicatif", "domain": "进度条库"},
        ]
    }
    gaps = compare(required, returned)
    # doc 缺失
    assert [g["kind"] for g in gaps] == ["值属性缺失"]
    assert gaps[0]["field"] == "doc"
    assert gaps[0]["entity"] == "e1"


def test_值属性缺失_其余契约要求均在_不误报():
    required = {"项目用途/领域": ["name", "domain", "doc"]}
    returned = {
        "项目用途/领域": [
            {"_id": "e1", "name": "indicatif", "domain": "进度条库", "doc": "README.md"},
        ]
    }
    assert compare(required, returned) == []


def test_类型整体缺失():
    required = {"入口": ["entries"]}
    returned = {}
    gaps = compare(required, returned)
    assert gaps[0]["kind"] == "类型缺失"


def test_子树递归分解_子实体缺失才进缺口():
    # 模块划分.modules → 模块职责；子树字段缺失时不整记，下钻到子实体
    subtree_map = {"模块划分": {"modules": "模块职责"}}
    required = {"模块划分": ["modules"]}
    returned = {
        "模块划分": [
            {"_id": "m0", "modules": []},  # 子树字段缺失
        ],
        "模块职责": [
            {"_id": "mod_a", "path": "src/lib.rs", "responsibility": "", "capabilities": []},
            {"_id": "mod_b", "path": "src/iter.rs", "responsibility": "迭代器", "capabilities": ["iter"]},
        ],
    }
    gaps = compare(required, returned, subtree_map=subtree_map)
    # mod_a 的 responsibility/capabilities 缺失，mod_b 完整
    kinds = {(g["entity"], g["field"]) for g in gaps}
    assert ("mod_a", "responsibility") in kinds
    assert ("mod_a", "capabilities") in kinds
    assert all(g["kind"] in ("值属性缺失", "子树缺失") for g in gaps)
    # 不整记"模块划分"本身
    assert all(g["type"] != "模块划分" for g in gaps)


def test_子树整体缺失():
    subtree_map = {"模块划分": {"modules": "模块职责"}}
    required = {"模块划分": ["modules"]}
    returned = {"模块划分": [{"_id": "m0", "modules": []}]}  # 子类型无实体
    gaps = compare(required, returned, subtree_map=subtree_map)
    assert gaps[0]["kind"] == "子树缺失"
    assert gaps[0]["type"] == "模块职责"


def test_混合缺口_分列():
    subtree_map = {"模块划分": {"modules": "模块职责"}}
    required = {"项目用途/领域": ["name", "domain"], "模块划分": ["modules"]}
    returned = {
        "项目用途/领域": [{"_id": "e1", "name": "indicatif"}],  # domain 缺失
        "模块划分": [{"_id": "m0", "modules": []}],  # 子树缺失
    }
    gaps = compare(required, returned, subtree_map=subtree_map)
    kinds = [g["kind"] for g in gaps]
    assert "值属性缺失" in kinds
    assert "子树缺失" in kinds


def test_子树递归不无限循环():
    subtree_map = {"模块划分": {"modules": "模块职责"}, "模块职责": {"capabilities": "模块划分"}}
    required = {"模块划分": ["modules"]}
    returned = {
        "模块划分": [{"_id": "m0", "modules": []}],
        "模块职责": [{"_id": "a", "path": "x", "responsibility": "r", "capabilities": []}],
    }
    gaps = compare(required, returned, subtree_map=subtree_map)
    assert isinstance(gaps, list)  # 终止即可，不深究内容
