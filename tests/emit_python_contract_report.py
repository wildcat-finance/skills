#!/usr/bin/env python3
"""Run Python contract tests and write one fresh Elenchus report."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.emit_run_observation_report import report_target, result_payload, write_report


def main():
    target = report_target(sys.argv[1:])
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_python_contract")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("emit_python_contract_report.py: report write failed", file=sys.stderr)
        return 2
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
