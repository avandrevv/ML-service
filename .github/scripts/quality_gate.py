#!/usr/bin/env python3
"""Quality Gate: собирает отчёты и применяет пороговую политику."""
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

POLICY = {
    "coverage_min": 80.0,
    "bandit_high_max": 0,
    "bandit_medium_max": 5,
    "ruff_errors_max": 0,
}

ARTIFACTS = Path("artifacts")


def parse_coverage(path: Path) -> float | None:
    if not path.exists():
        return None
    root = ET.parse(path).getroot()
    return float(root.attrib.get("line-rate", 0)) * 100


def parse_bandit(path: Path) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    totals = data.get("metrics", {}).get("_totals", {})
    return {
        "high":   totals.get("SEVERITY.HIGH", 0),
        "medium": totals.get("SEVERITY.MEDIUM", 0),
        "low":    totals.get("SEVERITY.LOW", 0),
    }


def parse_ruff(path: Path) -> int | None:
    if not path.exists():
        return None
    return len(json.loads(path.read_text()))


def check_jobs() -> list[str]:
    needs = json.loads(os.environ.get("NEEDS_JSON", "{}"))
    violations = []
    for name, info in needs.items():
        result = info.get("result")
        if result not in ("success", "skipped"):
            violations.append(f"Job '{name}' finished with '{result}'")
    return violations


def main() -> int:
    bandit = parse_bandit(ARTIFACTS / "static-reports" / "bandit-report.json")
    ruff = parse_ruff(ARTIFACTS / "static-reports" / "ruff-report.json")
    coverage = parse_coverage(ARTIFACTS / "coverage" / "coverage.xml")

    violations = check_jobs()

    if coverage is None:
        violations.append("Coverage report missing")
    elif coverage < POLICY["coverage_min"]:
        violations.append(
            f"Coverage {coverage:.1f}% < {POLICY['coverage_min']}%"
        )

    if bandit is not None:
        if bandit["high"] > POLICY["bandit_high_max"]:
            violations.append(
                f"Bandit HIGH {bandit['high']} > {POLICY['bandit_high_max']}"
            )
        if bandit["medium"] > POLICY["bandit_medium_max"]:
            violations.append(
                f"Bandit MEDIUM {bandit['medium']} > {POLICY['bandit_medium_max']}"
            )

    if ruff is not None and ruff > POLICY["ruff_errors_max"]:
        violations.append(f"Ruff errors {ruff} > {POLICY['ruff_errors_max']}")

    print("QUALITY GATE REPORT")
    print(f"Coverage:         {coverage}")
    print(f"Bandit:           {bandit}")
    print(f"Ruff errors:      {ruff}")
    print("-" * 60)

    if violations:
        print("FAILED")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())