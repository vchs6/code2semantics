"""合成分析与信息需求清单测试（任务 2.1/2.2/2.3）。"""
from constructor.synthesis import build_info_needs, derive_info_needs  # noqa: E402


def test_同一契约分解结果确定():
    a = derive_info_needs(["项目用途/领域", "入口"])
    b = derive_info_needs(["项目用途/领域", "入口"])
    assert a == b


def test_契约要求的事实均有信息需求条目():
    needs = derive_info_needs(["项目用途/领域", "模块划分", "入口", "构建与运行形态", "配置项", "外部依赖"])
    covered = {n["fact_type"] for n in needs}
    assert covered == {"项目用途/领域", "模块划分", "入口", "构建与运行形态", "配置项", "外部依赖"}


def test_全量清单覆盖fact_catalog全部事实类型():
    full = build_info_needs()
    types = {n["fact_type"] for n in full["needs"]}
    assert len(types) == 20  # fact-catalog 封闭边界内全部事实类型
    assert "项目用途/领域" in types and "元素实现语义" in types


def test_无法映射的字段进差距段():
    full = build_info_needs()
    assert full.get("unmappable")  # 差距段存在且非空（如需要归纳的字段）


def test_信息需求清单文件落盘():
    from constructor.synthesis import INFO_NEEDS_FILE, write_info_needs_file
    write_info_needs_file()
    assert INFO_NEEDS_FILE.exists()
    text = INFO_NEEDS_FILE.read_text("utf-8")
    assert "项目用途/领域" in text and "差距段" in text
