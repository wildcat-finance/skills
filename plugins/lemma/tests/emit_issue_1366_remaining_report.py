#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Run remaining venue guards, tests and checked conformance resolvers."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import shlex
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emit_issue_1366_report import result_payload, write_report


REPORTER = "plugins/lemma/tests/emit_issue_1366_remaining_report.py"
TEST_CASES = {
    "kf-1366-remaining-legacy-membership": (
        "test_remaining_events.RemainingLegacyMembershipGuardTests",),
    "kf-1366-distinct-event-owners": (
        "test_remaining_events.DistinctEventOwnersGuardTests",),
    "kf-1366-target-source-closure": (
        "test_remaining_events.TargetSourceClosureGuardTests",),
    "kf-1366-metadata-compilation-target": (
        "test_remaining_events.MetadataCompilationTargetGuardTests",),
    "kf-1366-canonical-citation-map": (
        "test_remaining_events.CanonicalCitationMapGuardTests",),
    "event-tests": ("test_events", "test_legacy_events", "test_remaining_events"),
    "preparation-tests": ("test_preparation",),
}
DESIGN_CASES = ("production-conformance", "complete-input-custody", "venue-conformance")
CANDIDATES = ("current-pins", "exact-pins", "prepared-events")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=(*TEST_CASES, *DESIGN_CASES))
    parser.add_argument("--candidate", choices=CANDIDATES)
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(arguments)
    if args.case in DESIGN_CASES:
        if args.candidate is None:
            parser.error("design conformance requires --candidate")
        # Later steps supply this source-owned evidence checker. An absent
        # checker refuses; neither a future case nor missing evidence passes.
        try:
            checker = importlib.import_module("remaining_conformance")
            passed = checker.evaluate(args.case, args.candidate)
        except (ImportError, OSError, ValueError) as exc:
            parser.exit(2, f"conformance unavailable: {exc}\n")
        if type(passed) is not bool:
            parser.exit(2, "conformance checker did not return a boolean\n")
        status = 0 if passed else 1
        payload = {
            "schema": "protasis-design-report/v1",
            "candidate": args.candidate,
            "criterion": args.case,
            "value": passed,
            "unit": "boolean",
            "command": shlex.join(["python3", REPORTER, *arguments]),
            "exit": status,
        }
    else:
        if args.candidate is not None:
            parser.error("--candidate is only valid for design conformance")
        suite = unittest.TestLoader().loadTestsFromNames(TEST_CASES[args.case])
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        payload = result_payload(result)
        passed = (result.testsRun > 0 and result.wasSuccessful()
                  and not result.skipped and not result.expectedFailures)
        status = 0 if passed else 1
    try:
        write_report(args.report, payload)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"report refused: {exc}\n")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
