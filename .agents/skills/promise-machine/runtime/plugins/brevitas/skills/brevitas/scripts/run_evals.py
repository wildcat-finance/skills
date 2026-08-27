#!/usr/bin/env python3
"""Run Brevitas provenance, compression, structure, and evidence evals."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

from brevitas import lint_text


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"


def run_case(case_dir: Path) -> list[str]:
    manifest = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    original = (case_dir / "original.md").read_text(encoding="utf-8")
    target = (case_dir / "target.md").read_text(encoding="utf-8")
    failures: list[str] = []

    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
    if digest != manifest["origin_sha256"]:
        failures.append("fixture no longer matches its pinned origin digest")

    issues = lint_text(
        target,
        mode=manifest.get("mode", "report"),
        source_text=original,
        source_name="original.md",
    )
    failures.extend(f"lint {issue.code} at {issue.source}:{issue.line}: {issue.message}" for issue in issues)

    expectation = manifest["expectation"]
    if expectation == "compress":
        if len(target.splitlines()) >= len(original.splitlines()):
            failures.append("target is not physically shorter than original")
    elif expectation == "retain-evidence":
        lines = target.splitlines()
        if not lines or "brevitas: evidence-exception" not in lines[0]:
            failures.append("retention case lacks an evidence exception")
        retained = "\n".join(lines[1:]).rstrip() + "\n"
        if retained != original:
            failures.append("retention case changed irreducible evidence")
    else:
        failures.append(f"unknown expectation: {expectation}")
    return failures


def main() -> int:
    failures = 0
    for case_dir in sorted(path for path in CASES.iterdir() if path.is_dir()):
        case_failures = run_case(case_dir)
        if case_failures:
            failures += len(case_failures)
            for failure in case_failures:
                print(f"FAIL {case_dir.name}: {failure}")
        else:
            print(f"PASS {case_dir.name}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
