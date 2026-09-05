#!/usr/bin/env python3
"""Run one issue-453 guard and emit a fresh closed unittest report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tests.emit_run_observation_report import (  # noqa: E402
    report_target,
    result_payload,
    write_report,
)


CASES = {
    "kf-453-01": (
        "plugins.hexaemeron.tests.test_issue_453_known_failure_inventory."
        "KnownFailureInventoryTests."
        "test_kf_453_01_closed_inventory_is_source_bound"
    ),
}
REQUIRED_SURFACE = (
    Path("plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py"),
    Path("plugins/hexaemeron/tests/emit_issue_453_guard_report.py"),
    Path("plugins/hexaemeron/tests/fixtures/issue-453/inventory.json"),
)


def arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(argv)


def missing_surface_suite(root: Path):
    missing = [path.as_posix() for path in REQUIRED_SURFACE if not (root / path).is_file()]
    if not missing:
        return None

    def required_surface_is_present():
        raise AssertionError("required issue-453 guard surface absent: " + ", ".join(missing))

    return unittest.TestSuite([unittest.FunctionTestCase(required_surface_is_present)])


def main(argv=None):
    options = arguments(sys.argv[1:] if argv is None else argv)
    target = report_target([options.report])
    root = Path.cwd().resolve(strict=True)
    suite = missing_surface_suite(root)
    if suite is None:
        suite = unittest.defaultTestLoader.loadTestsFromName(CASES[options.case])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("emit_issue_453_guard_report.py: report write failed", file=sys.stderr)
        return 2
    failed = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failed}/{result.testsRun} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
