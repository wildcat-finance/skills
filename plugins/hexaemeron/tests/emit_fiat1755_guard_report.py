#!/usr/bin/env python3
"""Run the Fiat 1755 public-quotation guard and emit a fresh unittest report."""

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
    "kf-1755-s2-r1b-01": (
        "plugins.hexaemeron.tests.test_checkpoint_marker_scan."
        "PublicAuditQuotationTests."
        "test_preserved_public_audit_source_is_not_key_material",
        "plugins.hexaemeron.tests.test_checkpoint_marker_scan."
        "PublicAuditQuotationTests."
        "test_preserved_public_audit_synopsis_is_not_key_material",
    ),
}


def arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(argv)


def main(argv=None):
    options = arguments(sys.argv[1:] if argv is None else argv)
    target = report_target([options.report])
    suite = unittest.defaultTestLoader.loadTestsFromNames(CASES[options.case])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("emit_fiat1755_guard_report.py: report write failed", file=sys.stderr)
        return 2
    rejected = sum(
        len(getattr(result, field))
        for field in (
            "failures",
            "errors",
            "skipped",
            "expectedFailures",
            "unexpectedSuccesses",
        )
    )
    print(f"{max(result.testsRun - rejected, 0)}/{result.testsRun} tests passed")
    return 0 if result.testsRun == len(CASES[options.case]) and rejected == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
