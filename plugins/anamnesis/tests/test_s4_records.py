"""Step 4: the committed design record says what the run decided, and its
reports are the bytes the record was scored from."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
ADMISSION = PLUGIN_ROOT / "docs/synkrisis-admission"
RECORD = ADMISSION / "design-evidence.json"
REPORTS = ADMISSION / "reports"

CONCERNS = {"correctness", "time", "space", "compatibility", "recovery"}
RUNNER = PLUGIN_ROOT / "tests/elenchus.py"
WORKTREE = PLUGIN_ROOT.parents[1]


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
    """A step whose pattern matches no test file must refuse rather than report a
    clean run of nothing. The condition is forced here rather than borrowed from
    whichever step currently lacks tests, because that fact changes as the run
    builds its later steps."""

    def setUp(self) -> None:
        self.scratch = Path(tempfile.mkdtemp(dir=WORKTREE))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        spec = importlib.util.spec_from_file_location("anamnesis_runner", RUNNER)
        self.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runner)

    def test_an_empty_suite_is_refused_and_writes_no_report(self) -> None:
        report = self.scratch / "empty.json"
        with unittest.mock.patch.object(
            unittest.defaultTestLoader, "discover", return_value=unittest.TestSuite()
        ):
            code = self.runner.main(["--step", "4", str(report)])
        self.assertEqual(code, 3)
        self.assertFalse(report.exists())

    def test_a_step_that_has_tests_still_passes_and_writes_its_report(self) -> None:
        report = self.scratch / "step-1.json"
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--step", "1", str(report)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(report.is_file())
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertTrue(payload["complete"])
        self.assertGreater(payload["testsRun"], 0)


if __name__ == "__main__":
    unittest.main()
