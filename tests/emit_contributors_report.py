#!/usr/bin/env python3
"""Run the contributor surface and emit one fresh Elenchus report.

The confined single-target write path is not reimplemented here. It is the
hardened one in tests/emit_run_observation_report.py, which several audit rounds
shaped, and a second copy would be a second thing to harden. Only the required
surface and the module list differ.
"""

import sys
from pathlib import Path
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tests.emit_run_observation_report import (  # noqa: E402
    report_target,
    result_payload,
    write_report,
)

REQUIRED_SURFACE = (
    Path("scripts/contributors.py"),
    Path("tests/test_contributors.py"),
    Path("plugins/hexaemeron/skills/fiat/scripts/hexctl.py"),
)
MODULES = ("tests.test_contributors",)


def missing_surface_suite(root):
    missing = [path.as_posix() for path in REQUIRED_SURFACE if not (root / path).is_file()]
    if not missing:
        return None

    def required_surface_is_present():
        raise AssertionError("required contributor test surface absent: " + ", ".join(missing))

    return unittest.TestSuite([unittest.FunctionTestCase(required_surface_is_present)])


def main(argv=None):
    target = report_target(sys.argv[1:] if argv is None else argv)
    root = Path.cwd().resolve(strict=True)
    suite = missing_surface_suite(root)
    if suite is None:
        suite = unittest.defaultTestLoader.loadTestsFromNames(MODULES)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("emit_contributors_report.py: report write failed", file=sys.stderr)
        return 2
    failed = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failed}/{result.testsRun} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
