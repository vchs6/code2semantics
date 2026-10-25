"""语义实体记录模型测试（任务 2.1/2.2/2.3；design 决策 3/7）。

- 分解：读写单位（语义事实集）→ 实体/属性记录（物理粒度）
- 重组：实体/属性 → 语义事实集（对读写契约透明：取回与提交一致）
- 操作语义常量：提交原子生效、幂等、版本冲突、失效（实现见 4.x）
"""
from sfrs.model import FACT_SET_SUBMIT, OPS_SEMANTICS, decompose, reassemble

FACT_SET = {
    "project": "indicatif",
    "version": "a65379f",
    "facts": {
        "项目层": [
            {"type": "项目用途/领域",
             "children": [{"name": "name", "is_subtree": False, "value": "indicatif"},
                          {"name": "domain", "is_subtree": False, "value": "进度条库"}],
             "evidence": {"file": "Cargo.toml", "range": "1-14"}},
        ]
    },
}


def test_事实集分解为实体与属性():
    entities = decompose(FACT_SET)
    assert len(entities) == 1
    e = entities[0]
    assert e["entity_id"] == "项目用途/领域:Cargo.toml:1-14"
    assert e["fact_type"] == "项目用途/领域"
    assert e["layer"] == "项目层"  # 层级归属元数据（参与索引，不参与布局）
    assert e["fields"] == {"name": "indicatif", "domain": "进度条库"}
    assert e["evidence"] == {"file": "Cargo.toml", "range": "1-14"}


def test_分解确定性_同输入同输出():
    assert decompose(FACT_SET) == decompose(dict(FACT_SET))


def test_重组还原事实集_取回与提交一致():
    entities = decompose(FACT_SET)
    rebuilt = reassemble(entities, project="indicatif", version="a65379f")
    assert rebuilt["facts"] == FACT_SET["facts"]
    assert rebuilt["project"] == "indicatif" and rebuilt["version"] == "a65379f"


def test_提交形态schema常量锚定读写单位():
    assert FACT_SET_SUBMIT == ("project", "version", "facts")


def test_操作语义常量齐备():
    for key in ("submit_atomic", "idempotent_same_content",
                "conflict_same_id_diff_content", "invalidate_explicit",
                "version_by_caller"):
        assert key in OPS_SEMANTICS
