"""SFRS 适配层测试（任务 4.6 衔接 / InMemoryRepo 替换）。

编排器对仓库的调用面为 accessible()/read(project, version)/write(project, version, produced)
（与内存桩同构）；本适配层把编排器实体形态桥接为 SFRS 语义事实集（经 model 分解/重组）。
"""
import sys
from pathlib import Path

from layout import SKILL_ROOT

from catalog import LAYER_OF  # noqa: E402
from sfrs.adapter import SFRSRepo  # noqa: E402

PRODUCED = {
    "项目用途/领域": [
        {"_id": "项目用途/领域:Cargo.toml:1-14", "name": "indicatif",
         "domain": "A progress bar library", "evidence": {"file": "Cargo.toml", "range": "1-14"}},
    ],
}


def test_write_read_roundtrip_编排器形态(tmp_path):
    adapter = SFRSRepo(db_path=tmp_path / "facts.db")
    n = adapter.write("indicatif", "a65379f", PRODUCED)
    assert n == 1  # 新入库实体数（终止判据语义）
    out = adapter.read("indicatif", "a65379f")
    assert out == PRODUCED  # 取回与提交一致（编排器形态不变）


def test_重复写入幂等_返回0(tmp_path):
    adapter = SFRSRepo(db_path=tmp_path / "facts.db")
    adapter.write("indicatif", "a65379f", PRODUCED)
    assert adapter.write("indicatif", "a65379f", PRODUCED) == 0


def test_跨实例持久化_新实例读到已存事实(tmp_path):
    db = tmp_path / "facts.db"
    SFRSRepo(db_path=db).write("indicatif", "a65379f", PRODUCED)
    adapter2 = SFRSRepo(db_path=db)
    assert adapter2.read("indicatif", "a65379f") == PRODUCED  # 跨会话语义


def test_层归组经fact_catalog(tmp_path):
    adapter = SFRSRepo(db_path=tmp_path / "facts.db")
    adapter.write("indicatif", "v1", PRODUCED)
    fact_set = adapter._sfrs.read("indicatif", "v1")
    layer = LAYER_OF["项目用途/领域"]
    assert layer in fact_set["facts"]  # 逻辑分层视图由元数据重建
