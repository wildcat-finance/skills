#!/usr/bin/env python3
"""Run the Python, repository-graph and Solidity dead-code surface.

The confined report writer lives in `tests/emit_run_observation_report.py` and
is imported rather than copied. That writer is the product of the issue #434
audit rounds, including the C5 round 5 finding about absolute report targets; a
second copy of three hundred hardened lines would drift away from it silently
and would be exactly the duplication this command exists to surface.
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
    Path("schemas/dead-code-report-v1.schema.json"),
    Path("scripts/dead_code.py"),
    Path("scripts/dead_code_monitoring/sitecustomize.py"),
    Path("tests/test_dead_code.py"),
)
REQUIRED_ANALYSER_DECLARATIONS = (
    "def analyse_python(",
    "def analyse_repository(",
    "def analyse_solidity(",
)
MODULES = ("tests.test_dead_code",)


def missing_surface_suite(root):
    """A suite that fails by name when the surface under test is not there."""
    missing = [path.as_posix() for path in REQUIRED_SURFACE if not (root / path).is_file()]
    script = root / "scripts" / "dead_code.py"
    if not missing:
        source = script.read_text(encoding="utf-8")
        missing.extend(
            declaration
            for declaration in REQUIRED_ANALYSER_DECLARATIONS
            if declaration not in source
        )
    if not missing:
        return None

    def required_surface_is_present():
        raise AssertionError("required dead-code test surface absent: " + ", ".join(missing))

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
        print("emit_dead_code_report.py: report write failed", file=sys.stderr)
        return 2
    failed = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failed}/{result.testsRun} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
