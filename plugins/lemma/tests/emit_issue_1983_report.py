#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Run event membership tests and report observed counters or conformance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import sys
import unittest

# Elenchus removes implicit script-directory imports with PYTHONSAFEPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emit_issue_1366_report import result_payload, write_report


REPORTER = "plugins/lemma/tests/emit_issue_1983_report.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case", required=True,
        choices=("kf-1983-legacy-membership", "event-tests", "production-conformance"),
    )
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(arguments)
    loader = unittest.TestLoader()
    names = (
        ["test_legacy_events.LegacyMembershipGuardTests"]
        if args.case == "kf-1983-legacy-membership"
        else ["test_events", "test_legacy_events"]
    )
    suite = loader.loadTestsFromNames(names)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    counters = result_payload(result)
    passed = (
        result.testsRun > 0 and result.wasSuccessful()
        and not result.skipped and not result.expectedFailures
    )
    status = 0 if passed else 1
    if args.case == "production-conformance":
        payload = {
            "schema": "protasis-design-report/v1",
            "candidate": "pinned-inheritance",
            "criterion": "production-conformance",
            "value": passed,
            "unit": "boolean",
            "command": shlex.join(["python3", REPORTER, *arguments]),
            "exit": status,
        }
        print(json.dumps(counters, sort_keys=True), file=sys.stderr)
    else:
        payload = counters
    try:
        write_report(args.report, payload)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"report refused: {exc}\n")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
