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
        "plugins.hexaemeron.tests.test_known_failure_inventory."
        "KnownFailureInventoryTests."
        "test_kf_453_01_closed_inventory_is_source_bound"
    ),
    "kf-453-02": (
        "plugins.hexaemeron.tests.test_inoculation_lifecycle."
        "InoculationLifecycleTests."
        "test_kf_453_02_inoculation_precedes_implementation"
    ),
}
REQUIRED_SURFACE = (
    Path("plugins/hexaemeron/tests/test_known_failure_inventory.py"),
    Path("plugins/hexaemeron/tests/test_inoculation_lifecycle.py"),
    Path("plugins/hexaemeron/tests/emit_issue_453_guard_report.py"),
    Path("plugins/hexaemeron/tests/fixtures/issue-453/inventory.json"),
    Path("plugins/hexaemeron/tests/fixtures/issue-453/no-known-findings.json"),
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


def repository_cwd() -> Path | None:
    """Return the physical guard repository only when cwd is that repository."""
    try:
        root = Path.cwd().resolve(strict=True)
        repository = REPOSITORY_ROOT.resolve(strict=True)
        root_stat = root.stat()
        repository_stat = repository.stat()
    except OSError:
        return None
    if (root_stat.st_dev, root_stat.st_ino) != (
        repository_stat.st_dev,
        repository_stat.st_ino,
    ):
        return None
    return root


def result_is_clean(result) -> bool:
    """Accept only a positive, ordinary, assertion-free unittest run."""
    required = (
        "failures",
        "errors",
        "skipped",
        "expectedFailures",
        "unexpectedSuccesses",
    )
    tests_run = getattr(result, "testsRun", None)
    if isinstance(tests_run, bool) or not isinstance(tests_run, int) or tests_run <= 0:
        return False
    try:
        return all(not getattr(result, field) for field in required)
    except (AttributeError, TypeError):
        return False


def main(argv=None):
    options = arguments(sys.argv[1:] if argv is None else argv)
    root = repository_cwd()
    if root is None:
        print(
            "emit_issue_453_guard_report.py: cwd is not the reporter repository",
            file=sys.stderr,
        )
        return 2
    target = report_target([options.report])
    suite = missing_surface_suite(root)
    if suite is None:
        suite = unittest.defaultTestLoader.loadTestsFromName(CASES[options.case])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("emit_issue_453_guard_report.py: report write failed", file=sys.stderr)
        return 2
    rejected = sum(
        len(getattr(result, field, ()))
        for field in (
            "failures",
            "errors",
            "skipped",
            "expectedFailures",
            "unexpectedSuccesses",
        )
    )
    print(f"{max(result.testsRun - rejected, 0)}/{result.testsRun} tests passed")
    return 0 if result_is_clean(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
