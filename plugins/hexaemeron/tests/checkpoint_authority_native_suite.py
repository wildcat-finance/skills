#!/usr/bin/env python3
"""Mandatory actual native admission, original hostile cases and adapter tests."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import test_checkpoint_authority_native as local_cases
import test_checkpoint_authority_native_conformance as conformance_cases
from checkpoint_authority_native_fixture import FIXTURES, approval, pin, request
from checkpoint_authority_native_probe import run
from checkpoint_authority import native_io
from checkpoint_authority.canonical import Refusal, canonical
from checkpoint_authority.native import verify_native

NATIVE = None
SOURCE = os.environ.get("CHECKPOINT_AUTHORITY_NATIVE_SOURCE")
CAPABILITY = FIXTURES.parent / "native-capabilities.json"


class Integration(unittest.TestCase):
    def id(self): return "native_integration." + self._testMethodName

    def test_actual_sequence_covers_four_commits_from_public_only_trust(self):
        global NATIVE
        self.assertIsNotNone(SOURCE, "CHECKPOINT_AUTHORITY_NATIVE_SOURCE is required")
        # The launcher chooses where the completed private logs are copied.
        parent = os.environ.get("CHECKPOINT_AUTHORITY_NATIVE_EVIDENCE")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            result = run(SOURCE, directory)
            NATIVE = {"result_sha256": hashlib.sha256(canonical(result)).hexdigest(),
                "source_profile_sha256": result["source_profile_sha256"], "source_commit": result["source_commit"],
                "native_results": result["native_results"], "required": result["coverage"]["required"],
                "historical_required": result["coverage"]["historical_required"],
                "verified_count": len(result["coverage"]["verified"]),
                "capability_sha256": hashlib.sha256(CAPABILITY.read_bytes()).hexdigest()}
            if parent:
                # Explicit fixture evidence export; it carries no controller authority.
                import shutil
                shutil.copytree(directory / "native-positive", Path(parent) / "native-positive")

    def test_latest_step_key_approval_cannot_authorize_older_signed_commits(self):
        self.assertIsNotNone(SOURCE, "CHECKPOINT_AUTHORITY_NATIVE_SOURCE is required")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            with self.assertRaises(Refusal) as caught:
                verify_native(FIXTURES / "checkpoint.zip", job_root=directory,
                    pin=pin(SOURCE), request=request("native-history-refusal"), approval=approval(first_step=2))
            self.assertEqual(caught.exception.code, "native-signer-unapproved")
            attempt = directory / "native-history-refusal"
            self.assertTrue(all((attempt / (stage + ".stdout")).exists() for stage in ("inspect", "restore", "verify", "identity")))
            self.assertFalse((attempt / "result.json").exists())


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


class PrivateLog(io.StringIO):
    def __init__(self):
        super().__init__()
        self.bytes = 0
        parent = os.environ.get("CHECKPOINT_AUTHORITY_NATIVE_EVIDENCE")
        self.file = (Path(parent) / "suite.txt").open("x", encoding="utf-8") if parent else None
    def write(self, text):
        self.bytes += len(text.encode())
        if self.bytes > 65536: raise RuntimeError("native private test log limit")
        if self.file: self.file.write(text); self.file.flush()
        return super().write(text)
    def close(self):
        if self.file: self.file.close()
        super().close()


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(local_cases)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(conformance_cases))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Integration))
    if SOURCE:
        profile = json.loads(CAPABILITY.read_bytes())
        for row in profile["native_tests"]:
            if native_io.hash_file(Path(SOURCE) / row["path"])[0] != row["sha256"]:
                raise RuntimeError("native hostile source pin mismatch")
        path = Path(SOURCE) / "plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py"
        spec = importlib.util.spec_from_file_location("test_hexctl_checkpoint_archive", path)
        module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromNames(
            ["test_hexctl_checkpoint_archive." + row["test"] for row in profile["fixtures"]]))
    output = PrivateLog()
    result = unittest.TextTestRunner(stream=output, verbosity=2, resultclass=Result).run(suite)
    complete = len(result.started) == len(result.completed) == len(set(result.started)) == result.testsRun > 0
    passed = complete and result.wasSuccessful() and not (result.skipped or result.expectedFailures or result.unexpectedSuccesses) and NATIVE is not None
    report = {"schema": "checkpoint-authority-native-execution/v1", "complete": complete, "passed": bool(passed),
        "tests_run": result.testsRun, "subtests_run": result.subtests, "started": result.started, "completed": result.completed,
        "failure_cases": sorted(result.failure_cases), "error_cases": sorted(result.error_cases),
        "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
        "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses),
        "output_sha256": hashlib.sha256(output.getvalue().encode()).hexdigest(), "native": NATIVE, "python": sys.version.split()[0]}
    output.close()
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__": raise SystemExit(main())
