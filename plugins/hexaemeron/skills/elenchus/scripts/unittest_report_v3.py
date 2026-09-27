#!/usr/bin/env python3
"""Run named unittest modules and retain native events grouped by test method.

The v3 report preserves TestResult's counters, including repeated subtest
failures and skips. Each method also has a row whose counters reconcile with
those totals. Elenchus classifies method outcomes; any error in a method takes
precedence over its assertion failures. Fixture errors outside a started
method cannot reconcile and remain inconclusive.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("elenchus_unittest_v2", SCRIPTS / "unittest_report_v2.py")
support = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(support)
COUNTERS = ("failures", "errors", "skipped", "expectedFailures", "unexpectedSuccesses")


class CaseResult(unittest.TextTestResult):
    """Retain every native outcome and one disjoint classification per method."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []
        self.active = []

    def startTest(self, test):
        super().startTest(test)
        row = {"test": test.id(), "outcome": "running", **dict.fromkeys(COUNTERS, 0)}
        self.cases.append(row)
        self.active.append((test, row))

    def stopTest(self, test):
        if self.active and self.active[-1][0] is test:
            # Skipped subtests suppress addSuccess even though the method ran.
            if self.active[-1][1]["outcome"] == "running":
                self.active[-1][1]["outcome"] = "passed"
            self.active.pop()
        super().stopTest(test)

    def record(self, test, counter, outcome):
        if not self.active or self.active[-1][0] is not test:
            return
        row = self.active[-1][1]
        if counter is not None:
            row[counter] += 1
        priority = {"running": 0, "passed": 1, "skipped": 2,
                    "expected-failure": 3, "failed": 4,
                    "unexpected-success": 5, "error": 6}
        if outcome is not None and priority[outcome] >= priority[row["outcome"]]:
            row["outcome"] = outcome

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, None, "passed")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, "failures", "failed")

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, "errors", "error")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        parent = getattr(test, "test_case", None)
        if parent is not None:
            self.record(parent, "skipped", None)
        else:
            self.record(test, "skipped", "skipped")

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.record(test, "expectedFailures", "expected-failure")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.record(test, "unexpectedSuccesses", "unexpected-success")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            assertion = issubclass(err[0], test.failureException)
            self.record(test, "failures" if assertion else "errors", "failed" if assertion else "error")


def payload(result):
    """Keep the runner's native counters beside their per-method witness."""
    return {
        "schema": "elenchus.unittest.v3", "complete": True,
        "testsRun": result.testsRun,
        **{name: len(getattr(result, name)) for name in COUNTERS},
        "cases": result.cases,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", required=True)
    parser.add_argument("tests", nargs="+")
    args = parser.parse_args(argv)
    result = unittest.TextTestRunner(
        stream=sys.stderr, resultclass=CaseResult, verbosity=1,
    ).run(support.load(args.tests))
    support.write_report(Path(args.report), payload(result))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
