"""合成器下一级装配测试（任务 2.1，spec「事实合成按契约结构装配输出」+ 下一级裁剪）。"""
from synthesizer import synthesize


def _contract(**over):
    base = {"project": "/proj", "facts": {"项目层": ["项目用途/领域", "模块划分"]}}
    base.update(over)
    return base


def test_下一级装配_值属性直出():
    merged = {"项目用途/领域": [
        {"_id": "e1", "name": "indicatif", "domain": "进度条库", "doc": "README.md"},
    ]}
    out = synthesize(_contract(), merged, version="v1")
    item = out["facts"]["项目层"][0]
    assert item["type"] == "项目用途/领域"
    children = {c["name"]: c for c in item["children"]}
    assert children["name"] == {"name": "name", "is_subtree": False, "value": "indicatif"}
    assert children["domain"]["is_subtree"] is False
    assert children["domain"]["value"] == "进度条库"


def test_子树节点标注且内容不出现():
    merged = {"模块划分": [{"_id": "m0", "modules": ["a", "b"]}]}
    out = synthesize(_contract(), merged, version="v1",
                     subtree_map={"模块划分": {"modules": "模块职责"}})
    item = out["facts"]["项目层"][0]
    children = {c["name"]: c for c in item["children"]}
    assert children["modules"] == {"name": "modules", "is_subtree": True}  # 子树内容不返回


def test_无子树映射时按值属性处理():
    merged = {"模块划分": [{"_id": "m0", "modules": ["a", "b"]}]}
    out = synthesize(_contract(), merged, version="v1")  # 未传 subtree_map
    children = {c["name"]: c for c in out["facts"]["项目层"][0]["children"]}
    assert children["modules"]["is_subtree"] is False
    assert children["modules"]["value"] == ["a", "b"]


def test_下一级裁剪_契约外内容不出现():
    merged = {
        "项目用途/领域": [{"_id": "e1", "name": "x", "domain": "d", "doc": "r", "extra": 1}],
        "外部依赖": [{"_id": "d1", "dependencies": []}],  # 契约未要求
    }
    out = synthesize(_contract(facts={"项目层": ["项目用途/领域"]}), merged, version="v1")
    types = {i["type"] for i in out["facts"]["项目层"]}
    assert types == {"项目用途/领域"}
    names = {c["name"] for i in out["facts"]["项目层"] for c in i["children"]}
    assert "extra" not in names


def test_分列与版本标注保留():
    out = synthesize(_contract(), merged={}, version="cur", version_fallback=True,
                     gaps=[{"type": "入口", "reason": "构造后仍缺失"}],
                     out_of_scope=["目录外事实"])
    assert out["gaps"] == [{"type": "入口", "reason": "构造后仍缺失"}]
    assert out["out_of_scope"] == ["目录外事实"]
    assert out["version"] == "cur" and out["version_fallback"] is True
