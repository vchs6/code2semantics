"""事实合成器 spec「事实合成按契约结构装配输出」场景测试。"""
from synthesizer import synthesize


def _contract(**over):
    base = {
        "project": "/proj",
        "facts": {
            "项目层": ["项目用途/领域"],
            "符号层": ["公共接口"],
        },
    }
    base.update(over)
    return base


def test_命中与构造事实合并装配_不区分来源_不重复():
    merged = {
        "项目用途/领域": [
            {"_id": "e1", "name": "indicatif", "domain": "进度条库", "doc": "README.md"},
            {"_id": "e2", "name": "indicatif", "domain": "进度条库", "doc": "README.md"},
        ],
        "公共接口": [
            {"_id": "s1", "signature": "fn draw()", "visibility": "pub", "module": "draw_target"},
        ],
    }
    out = synthesize(_contract(), merged, version="abc123")
    assert len(out["facts"]["项目层"]) == 2
    assert len(out["facts"]["符号层"]) == 1
    assert out["version"] == "abc123"
    assert out["version_fallback"] is False


def test_超出契约的层与事实类型被裁剪():
    merged = {
        "项目用途/领域": [{"_id": "e1", "name": "x", "domain": "d", "doc": "r"}],
        "模块职责": [{"_id": "m1", "path": "src/lib.rs", "responsibility": "r"}],  # 契约未要求
    }
    out = synthesize(_contract(), merged, version="v1")
    assert "模块层" not in out["facts"]
    assert "模块职责" not in str(out["facts"])


def test_超出字段被裁剪():
    merged = {
        "项目用途/领域": [
            {"_id": "e1", "name": "x", "domain": "d", "doc": "r", "extra_field": "不该出现"},
        ],
    }
    out = synthesize(_contract(), merged, version="v1")
    item = out["facts"]["项目层"][0]
    names = {c["name"] for c in item["children"]}
    assert "extra_field" not in names


def test_gaps与out_of_scope分列():
    out = synthesize(_contract(), merged={}, version="v1",
                     gaps=[{"type": "入口", "reason": "构造器不可用只读降级"}],
                     out_of_scope=["某目录外事实"])
    assert out["gaps"] == [{"type": "入口", "reason": "构造器不可用只读降级"}]
    assert out["out_of_scope"] == ["某目录外事实"]


def test_版本回退标注():
    out = synthesize(_contract(), merged={}, version="cur123", version_fallback=True)
    assert out["version_fallback"] is True
    assert out["version"] == "cur123"


def test_缺省标注():
    out = synthesize(_contract(), merged={}, version="v",
                     project_defaulted=True, repository_defaulted=True)
    assert out["project_defaulted"] is True
    assert out["repository_defaulted"] is True
