#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Run in-process event tests and emit their actual counters or conformance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import sys
import unittest


HERE = Path(__file__).resolve().parent
REPORTER = "plugins/lemma/tests/emit_issue_1366_report.py"
CONFORMANCE_TESTS = (
    "test_membership_multisets_and_overloads",
    "test_inherited_and_qualified_events",
    "test_event_only_owner_kinds",
    "test_primitive_and_compound_wire_types",
    "test_abi_order_types_and_flags",
    "test_excluded_dependency_evidence",
    "test_missing_and_malformed_evidence",
    "test_cyclic_and_excessive_type_expansion",
    "test_late_unit_failure_writes_nothing",
    "test_refusal_preserves_existing_outputs",
    "test_pinned_compiler_shapes",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case", required=True,
        choices=("kf-1366-indexed-bit", "event-tests", "event-conformance"),
    )
    parser.add_argument("--report", required=True)
    return parser


def result_payload(result: unittest.TestResult) -> dict:
    return {
        "schema": "elenchus.unittest.v1",
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }


def write_report(raw_path: str, payload: dict) -> None:
    """Create one fresh report under the current worktree without symlinks."""
    root = Path.cwd()
    path = Path(raw_path)
    if ".." in path.parts:
        raise ValueError("report must name a file inside the current worktree")
    if path.is_absolute():
        # macOS exposes the same temporary root through /var and /private/var.
        # Accept an alias of that root, then keep every descendant no-follow.
        for ancestor in path.parents:
            try:
                matches_root = ancestor.samefile(root)
            except OSError:
                matches_root = False
            if matches_root:
                path = path.relative_to(ancestor)
                break
        else:
            raise ValueError("report must name a file inside the current worktree")
    if not path.parts or any(part in (".", "..") for part in path.parts):
        raise ValueError("report must name a file inside the current worktree")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent_fd = os.open(root, directory_flags)
    try:
        for part in path.parts[:-1]:
            try:
                os.mkdir(part, 0o700, dir_fd=parent_fd)
            except FileExistsError:
                pass
            next_fd = os.open(part, directory_flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = next_fd
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        descriptor = os.open(path.name, flags, 0o600, dir_fd=parent_fd)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    finally:
        os.close(parent_fd)


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(arguments)
    sys.path.insert(0, str(HERE))
    loader = unittest.TestLoader()
    if args.case == "kf-1366-indexed-bit":
        suite = loader.loadTestsFromName("test_events.IndexedBitGuardTests")
    elif args.case == "event-tests":
        suite = loader.discover(str(HERE), pattern="test_events.py")
    else:
        names = ["test_events.IndexedBitGuardTests"] + [
            f"test_events.EventConformanceTests.{name}" for name in CONFORMANCE_TESTS
        ]
        suite = loader.loadTestsFromNames(names)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    counters = result_payload(result)
    passed = (
        result.testsRun > 0 and result.wasSuccessful()
        and not result.skipped and not result.expectedFailures
    )
    status = 0 if passed else 1
    if args.case == "event-conformance":
        payload = {
            "schema": "protasis-design-report/v1",
            "candidate": "compiler-membership",
            "criterion": "full-type-and-refusal-conformance",
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
