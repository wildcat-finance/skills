#!/usr/bin/env python3
"""Run Brevitas provenance, compression, structure, and evidence evals."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

from brevitas import lint_text
from held_corpus import CorpusError, failure_line, result_lines, validate_corpus


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"
CORPUS = ROOT / "evals"


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-corpus-only",
        action="store_true",
        help="validate and report the held corpus without running legacy evaluations",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        corpus = validate_corpus(CORPUS)
    except CorpusError as error:
        print(failure_line(error))
        return 1
    for line in result_lines(corpus):
        print(line)
    if args.validate_corpus_only:
        return 0

    failures = 0
    for case_dir in sorted(
        path for path in CASES.iterdir() if path.is_dir() and (path / "case.json").is_file()
    ):
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
