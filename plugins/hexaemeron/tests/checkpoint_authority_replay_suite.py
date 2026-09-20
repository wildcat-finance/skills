#!/usr/bin/env python3
"""Emit complete unittest execution for the authority-replay criterion.

The suite runs the replay, wire and conformance cases, replays the committed
positive history and every recorded hostile mutation, and executes the exact
Ariadne checkpoint predicate cases through the ordinary discovery adapter.
"""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_checkpoint_authority_replay as replay_cases
import test_checkpoint_authority_replay_conformance as conformance_cases
import test_checkpoint_authority_ariadne as ariadne_adapter


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
            (self.failure_cases if issubclass(error[0], test.failureException) else self.error_cases).add(test.id())
        super().addSubTest(test, subtest, error)


def main():
    loader = unittest.defaultTestLoader
    suite = loader.loadTestsFromModule(replay_cases)
    suite.addTests(loader.loadTestsFromModule(conformance_cases))
    suite.addTests(loader.loadTestsFromModule(ariadne_adapter))
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2, resultclass=Result).run(suite)
    complete = len(result.started) == len(result.completed) == len(set(result.started)) == result.testsRun > 0
    replayed = replay_cases.REPLAYED
    if replayed is not None:
        replayed = dict(replayed, ariadne_cases=sum(
            case.startswith(ariadne_adapter.MODULE_NAME + ".") for case in result.completed))
    passed = complete and result.wasSuccessful() and not (result.skipped or result.expectedFailures or result.unexpectedSuccesses) and replayed is not None
    report = {"schema": "checkpoint-authority-replay-execution/v1", "complete": complete, "passed": bool(passed),
        "tests_run": result.testsRun, "subtests_run": result.subtests, "started": result.started, "completed": result.completed,
        "failure_cases": sorted(result.failure_cases), "error_cases": sorted(result.error_cases),
        "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
        "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses),
        "output_sha256": hashlib.sha256(output.getvalue().encode()).hexdigest(), "replay": replayed,
        "python": sys.version.split()[0]}
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    if not passed:
        # Only test ids and fixed summary counts reach the conformance interface.
        print("authority-replay execution failed", file=sys.stderr)
        for category in ("failure_cases", "error_cases"):
            for case in report[category]: print(category + ": " + case, file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__": raise SystemExit(main())
