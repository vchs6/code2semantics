"""矩阵只读查询接口 spec「只读查询接口」场景测试。

测试隔离：用 tmp 矩阵目录（seed 生成），不依赖全局真实矩阵状态。
"""
from matrix_tool import common, seed
from matrix_tool.query import query_producers


def _seeded_matrix(tmp_path):
    m = tmp_path / "m"
    m.mkdir()
    seed.seed(common.SURVEY_REPORT, m)
    return m


def test_按信息需求取生产者链_含层级调用方式平台指导(tmp_path):
    m = _seeded_matrix(tmp_path)
    chain = query_producers(need_id="need.project.entries", matrix_dir=m)
    assert chain
    for item in chain:
        assert "producer_id" in item
        assert "production_tier" in item
        assert "platforms" in item
        assert "runtime_guidance" in item
        assert "invocation_profile" in item
        assert "verdict" in item
        assert "status" in item
        assert item["producer"] is not None  # 生产者定义可解析


def test_按事实类型取生产者链(tmp_path):
    m = _seeded_matrix(tmp_path)
    chain = query_producers(fact_type="入口", matrix_dir=m)
    assert chain
    assert all(item["need_id"] == "need.project.entries" for item in chain)


def test_按运行平台筛选(tmp_path):
    m = _seeded_matrix(tmp_path)
    full = query_producers(need_id="need.project.entries", matrix_dir=m)
    linux = query_producers(need_id="need.project.entries", platform="linux", matrix_dir=m)
    darwin = query_producers(need_id="need.project.entries", platform="darwin", matrix_dir=m)
    assert len(linux) == len(full)  # 播种报告为 Linux 平台，全部条目含 linux
    assert darwin == []  # 无 darwin 平台条目


def test_按状态筛选(tmp_path):
    m = _seeded_matrix(tmp_path)
    unlit = query_producers(need_id="need.project.entries", status="未点亮", matrix_dir=m)
    lit = query_producers(need_id="need.project.entries", status="已点亮", matrix_dir=m)
    assert unlit  # 播种后未点亮
    assert lit == []  # 尚未点亮


def test_查询不修改矩阵(tmp_path):
    m = _seeded_matrix(tmp_path)
    before = {
        "entries": (m / "entries.yaml").read_text("utf-8"),
        "producers": (m / "producers.yaml").read_text("utf-8"),
        "needs": (m / "info-needs.yaml").read_text("utf-8"),
    }
    query_producers(need_id="need.project.entries", platform="linux", matrix_dir=m)
    query_producers(fact_type="入口", matrix_dir=m)
    after = {
        "entries": (m / "entries.yaml").read_text("utf-8"),
        "producers": (m / "producers.yaml").read_text("utf-8"),
        "needs": (m / "info-needs.yaml").read_text("utf-8"),
    }
    assert before == after


def test_目录外事实类型返回空(tmp_path):
    m = _seeded_matrix(tmp_path)
    assert query_producers(fact_type="不存在的事实", matrix_dir=m) == []
