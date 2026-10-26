from pathlib import Path

from scripts.quality_gates import check_product_delivery


def test_product_gate_does_not_accept_success_marker_embedded_in_prose(tmp_path, monkeypatch, capsys):
    entrypoint = tmp_path / "SKILL.md"
    tests = tmp_path / "test_acceptance.py"
    scenarios = tmp_path / "scenarios"
    record = tmp_path / "acceptance-results.md"
    entrypoint.write_text("runtime entrypoint", encoding="utf-8")
    tests.write_text("integration test", encoding="utf-8")
    scenarios.mkdir()
    record.write_text(
        "The acceptance record does not contain FULL_END_TO_END_ACCEPTANCE: PASS.\n"
        "FULL_END_TO_END_ACCEPTANCE: NOT_YET_PASSED\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check_product_delivery, "REQUIRED_DELIVERABLES", {
        "Skill runtime entrypoint": entrypoint,
        "Cross-component acceptance tests": tests,
        "Real-source scenario fixtures": scenarios,
        "Recorded real runtime acceptance": record,
    })

    assert check_product_delivery.main() == 1
    assert "does not contain the full acceptance success marker" in capsys.readouterr().out


def test_product_gate_accepts_only_a_standalone_success_marker(tmp_path, monkeypatch):
    entrypoint = tmp_path / "SKILL.md"
    tests = tmp_path / "test_acceptance.py"
    scenarios = tmp_path / "scenarios"
    record = tmp_path / "acceptance-results.md"
    entrypoint.write_text("runtime entrypoint", encoding="utf-8")
    tests.write_text("integration test", encoding="utf-8")
    scenarios.mkdir()
    record.write_text("FULL_END_TO_END_ACCEPTANCE: PASS\n", encoding="utf-8")
    monkeypatch.setattr(check_product_delivery, "REQUIRED_DELIVERABLES", {
        "Skill runtime entrypoint": entrypoint,
        "Cross-component acceptance tests": tests,
        "Real-source scenario fixtures": scenarios,
        "Recorded real runtime acceptance": record,
    })

    assert check_product_delivery.main() == 0
