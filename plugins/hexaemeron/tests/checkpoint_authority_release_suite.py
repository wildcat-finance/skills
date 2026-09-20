#!/usr/bin/env python3
"""Emit complete unittest execution for the released-interoperability criterion.

The suite runs the release inventory, consumer lock, bounded command line and
demonstration cases, and reports the one demonstration outcome those cases
produced. Only test ids, fixed counters and digests reach the conformance
interface; a raw failure message stays inside the runner.
"""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/fiat/scripts"))
import test_checkpoint_authority_release as release_cases
import test_checkpoint_authority_release_conformance as conformance_cases
import test_checkpoint_network as network_cases
import checkpoint_authority_release_workload as workload


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = []; self.completed = []; self.subtests = 0
        self.failure_cases = set(); self.error_cases = set()

    def startTest(self, test): self.started.append(test.id()); super().startTest(test)

    def stopTest(self, test): self.completed.append(test.id()); super().stopTest(test)

    def addFailure(self, test, error): self.failure_cases.add(test.id()); super().addFailure(test, error)

    def addError(self, test, error): self.error_cases.add(test.id()); super().addError(test, error)

    def addSubTest(self, test, subtest, error):
        self.subtests += 1
        if error:
            (self.failure_cases if issubclass(error[0], test.failureException)
             else self.error_cases).add(test.id())
        super().addSubTest(test, subtest, error)


def main():
    loader = unittest.defaultTestLoader
    suite = loader.loadTestsFromModule(release_cases)
    suite.addTests(loader.loadTestsFromModule(conformance_cases))
    suite.addTests(loader.loadTestsFromModule(network_cases))
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2, resultclass=Result).run(suite)
    complete = len(result.started) == len(result.completed) == len(set(result.started)) == result.testsRun > 0
    demonstrated = release_cases.DEMONSTRATED
    measured = workload.benchmark() if result.wasSuccessful() else None
    passed = (complete and result.wasSuccessful() and demonstrated is not None and measured is not None
              and not (result.skipped or result.expectedFailures or result.unexpectedSuccesses))
    report = {"schema": "checkpoint-authority-release-execution/v1", "complete": complete,
              "passed": bool(passed), "tests_run": result.testsRun, "subtests_run": result.subtests,
              "started": result.started, "completed": result.completed,
              "failure_cases": sorted(result.failure_cases), "error_cases": sorted(result.error_cases),
              "failures": len(result.failures), "errors": len(result.errors),
              "skips": len(result.skipped), "expected_failures": len(result.expectedFailures),
              "unexpected_successes": len(result.unexpectedSuccesses),
              "output_sha256": hashlib.sha256(output.getvalue().encode()).hexdigest(),
              "demonstration": demonstrated, "workload": measured, "python": sys.version.split()[0]}
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    if not passed:
        print("released-interoperability execution failed", file=sys.stderr)
        for category in ("failure_cases", "error_cases"):
            for case in report[category]:
                print(category + ": " + case, file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
