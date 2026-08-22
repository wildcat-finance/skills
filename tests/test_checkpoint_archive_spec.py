"""Scaffold checks for the portable checkpoint design package."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "docs" / "hexaemeron-checkpoint-archive-study.md"
RUNBOOK = ROOT / "docs" / "hexaemeron-checkpoint-archive-runbook.md"
LICENSE = ROOT / "LICENSE"


class CheckpointArchiveSpecTests(unittest.TestCase):
    def test_tracked_design_paths_are_present(self):
        for path in (STUDY, RUNBOOK):
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(path.is_file())
                self.assertTrue(path.read_text(encoding="utf-8").strip())

    def test_root_licence_and_unittest_context_remain_available(self):
        self.assertIn("Apache License", LICENSE.read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "tests").is_dir())
        self.assertTrue((ROOT / "tests" / "test_promise_machine_contract.py").is_file())


if __name__ == "__main__":
    unittest.main()
