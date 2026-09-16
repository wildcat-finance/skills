"""Causal checks for controller-owned success-criteria execution custody."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest


HERE = pathlib.Path(__file__).resolve()
SOURCE = HERE.parents[1] / "skills" / "fiat" / "scripts" / "criteria_execution.py"
SPEC = importlib.util.spec_from_file_location("criteria_execution_under_test", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CriteriaExecutionTests(unittest.TestCase):
    def test_successful_child_is_observed_and_settled(self):
        result = MODULE.execute_argv(
            [sys.executable, "-c", "import sys; sys.stdout.write('ok')"],
            pathlib.Path.cwd(),
            timeout=2,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["reason"], "zero-exit")
        self.assertEqual(result["stdout"]["bytes"], 2)
        self.assertFalse(result["stdout"]["truncated"])

    def test_nonzero_exit_is_unmet_and_keeps_exit_status(self):
        result = MODULE.execute_argv(
            [sys.executable, "-c", "import sys; sys.stderr.write('bad'); sys.exit(7)"],
            pathlib.Path.cwd(),
            timeout=2,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["returncode"], 7)
        self.assertEqual(result["reason"], "nonzero-exit")
        self.assertEqual(result["failure"], "exit")

    def test_launch_failure_is_distinct_from_child_failure(self):
        result = MODULE.execute_argv(
            ["/path/that/does/not/exist"], pathlib.Path.cwd(), timeout=2
        )
        self.assertEqual(result["status"], "launch-failed")
        self.assertEqual(result["failure"], "launch")
        self.assertIsNone(result["returncode"])

    def test_timeout_terminates_process_group_and_is_unmet(self):
        result = MODULE.execute_argv(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            pathlib.Path.cwd(),
            timeout=0.05,
        )
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["reason"], "attempt-deadline")
        self.assertFalse(result["returncode"] == 0)

    def test_incremental_stream_cap_marks_prefix_as_truncated(self):
        result = MODULE.execute_argv(
            [sys.executable, "-c", "import sys; sys.stdout.write('x' * 32)"],
            pathlib.Path.cwd(),
            timeout=2,
            stream_cap=16,
        )
        self.assertEqual(result["status"], "stream-overflow")
        self.assertEqual(result["stdout"]["bytes"], 16)
        self.assertTrue(result["stdout"]["truncated"])

    def test_caller_cannot_claim_success_without_observed_operation(self):
        join = {
            "schema": "protasis-success-criteria-join/v1",
            "criteria": [{
                "id": "c", "claim": "ran", "step": 1,
                "command": "python3 x.py",
            }],
        }
        forged = {
            "schema": MODULE.RESULT_SCHEMA,
            "operation_ran": False,
            "observed": False,
            "criterion_ids": ["c"],
            "step": 1,
            "command": "python3 x.py",
            "settled": True,
        }
        with self.assertRaises(MODULE.Refusal):
            MODULE.validate_result(forged, join, criterion_id="c")

    def test_shared_descriptor_group_is_one_observation(self):
        join = {
            "schema": "protasis-success-criteria-join/v1",
            "criteria": [
                {"id": "a", "claim": "a", "step": 2, "command": "python3 x.py"},
                {"id": "b", "claim": "b", "step": 2, "command": "python3 x.py"},
            ],
        }
        self.assertEqual([row["id"] for row in MODULE.descriptor_group(join, "a")], ["a", "b"])

    def test_result_data_cap_is_checked(self):
        join = {
            "schema": "protasis-success-criteria-join/v1",
            "criteria": [{"id": "c", "claim": "ran", "step": 1, "command": "python3 x.py"}],
        }
        result = {
            "schema": MODULE.RESULT_SCHEMA,
            "operation_ran": True,
            "observed": True,
            "run_id": "run",
            "criterion_ids": ["c"],
            "step": 1,
            "command": "python3 x.py",
            "command_sha256": MODULE.digest(b"python3 x.py"),
            "settled": True,
            "outcomes": [{"status": "completed", "returncode": 0}],
            "padding": "x" * (MODULE.MAX_RESULT_BYTES + 1),
        }
        with self.assertRaises(MODULE.Refusal):
            MODULE.validate_result(result, join, run_id="run", criterion_id="c")


if __name__ == "__main__":
    unittest.main()
