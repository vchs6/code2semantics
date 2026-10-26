#!/usr/bin/env python3
"""Fail closed when the repository claims runtime acceptance without its evidence.

This gate intentionally distinguishes component tests and design-contract checks
from a real source-to-facts integration run. It does not infer success from
prebuilt repository fixtures.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DELIVERABLES = {
    "Skill runtime entrypoint": ROOT / "skills/layered-semantic-facts/SKILL.md",
    "Cross-component acceptance tests": ROOT / "tests/test_acceptance.py",
    "Real-source scenario fixtures": ROOT / "tests/fixtures/scenarios",
    "Recorded real runtime acceptance": ROOT / "skills/layered-semantic-facts/references/acceptance-results.md",
}

def main() -> int:
    missing = [
        (label, path.relative_to(ROOT).as_posix())
        for label, path in REQUIRED_DELIVERABLES.items()
        if not path.exists()
    ]
    if missing:
        print("PRODUCT DELIVERY GATE: BLOCKED")
        print("Component tests and schema validation are not runtime acceptance.")
        print("Missing required deliverables:")
        for label, path in missing:
            print(f"- {label}: {path}")
        print("Do not mark the main semantic-facts change complete until these exist and the real-source integration test passes.")
        return 1

    acceptance_record = REQUIRED_DELIVERABLES["Recorded real runtime acceptance"]
    record_text = acceptance_record.read_text(encoding="utf-8")
    if not re.search(r"(?m)^FULL_END_TO_END_ACCEPTANCE: PASS\s*$", record_text):
        print("PRODUCT DELIVERY GATE: BLOCKED")
        print("The acceptance record does not contain the full acceptance success marker on a standalone line.")
        print("A partial source-to-store smoke test cannot certify full component integration.")
        return 1

    print("Required runtime acceptance artifacts and full acceptance marker exist.")
    print("The CI integration test must still pass; the marker is not a substitute for execution.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
