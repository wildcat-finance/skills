"""Step 4: the committed design record says what the run decided, and its
reports are the bytes the record was scored from."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
ADMISSION = PLUGIN_ROOT / "docs/synkrisis-admission"
RECORD = ADMISSION / "design-evidence.json"
REPORTS = ADMISSION / "reports"

CONCERNS = {"correctness", "time", "space", "compatibility", "recovery"}
RUNNER = PLUGIN_ROOT / "tests/elenchus.py"
WORKTREE = PLUGIN_ROOT.parents[1]


def scratch_directory(prefix: str = "anamnesis-step-runner-"):
    """Transient space the runner can reach and `git status` never sees.

    The runner binds its report path to this checkout, so scratch has to stay
    inside it; the ignored top-level tmp/ is confined and invisible to status.
    """
    scratch = WORKTREE / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


class CommittedDesignRecord(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(RECORD.read_text(encoding="utf-8"))

    def test_record_declares_the_protasis_schema(self) -> None:
        self.assertEqual(self.record["schema"], "protasis-design-evidence/v1")

    def test_three_candidates_and_every_concern_is_covered(self) -> None:
        self.assertEqual(len(self.record["candidates"]), 3)
        self.assertEqual(
            {criterion["concern"] for criterion in self.record["criteria"]}, CONCERNS
        )

    def test_selection_is_boundary_record_on_a_unique_frontier(self) -> None:
        selection = self.record["selection"]
        self.assertEqual(selection["candidate"], "boundary-record")
        self.assertEqual(selection["rule"], "unique-frontier")
        surviving = {
            result["candidate"]
            for result in self.record["results"]
            if result["state"] == "fail"
        }
        self.assertEqual(surviving, {"widen-const", "sibling-contract"})

    def test_every_cell_names_a_report_whose_bytes_match_its_digest(self) -> None:
        self.assertEqual(len(self.record["results"]), 18)
        for result in self.record["results"]:
            report = result["report"]
            path = ADMISSION / report["path"]
            with self.subTest(report=report["path"]):
                self.assertTrue(path.is_file(), f"missing report {report['path']}")
                body = path.read_bytes()
                self.assertEqual(hashlib.sha256(body).hexdigest(), report["sha256"])
                document = json.loads(body)
                self.assertEqual(document["schema"], "protasis-design-report/v1")
                self.assertEqual(document["exit"], 0)


class StepRunnerRefusesAnEmptySuite(unittest.TestCase):
    """Steps 5 and 6 are admitted before their test files exist, so an empty
    suite must refuse rather than report a clean run of nothing."""

    def setUp(self) -> None:
        holder = scratch_directory()
        self.addCleanup(holder.cleanup)
        self.scratch = Path(holder.name)

    def run_step(self, step: int):
        report = self.scratch / f"step-{step}.json"
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--step", str(step), str(report)],
            capture_output=True,
            text=True,
        )
        return completed, report

    def test_a_step_with_no_tests_is_refused_and_writes_no_report(self) -> None:
        completed, report = self.run_step(5)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("discovered no tests", completed.stderr)
        self.assertFalse(report.exists())

    def test_a_step_that_has_tests_still_passes_and_writes_its_report(self) -> None:
        completed, report = self.run_step(1)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(report.is_file())
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertTrue(payload["complete"])
        self.assertGreater(payload["testsRun"], 0)


if __name__ == "__main__":
    unittest.main()
