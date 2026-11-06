#!/usr/bin/env python3
"""Run the #1963 V1 bundle tests and emit one fresh Elenchus report.

An absent or unimportable test module is counted as an error, never as an
assertion failure. The confined single-target write path is the hardened one
in tests/emit_run_observation_report.py.
"""

import argparse
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

MODULES = ("tests.test_kickoff_xray_1963",)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, metavar="REPORT")
    return parser


def main(argv=None, modules=MODULES):
    arguments = build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    target = report_target([arguments.report])
    suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("emit_kickoff_xray_1963_report.py: report write failed", file=sys.stderr)
        return 2
    failed = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failed}/{result.testsRun} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
