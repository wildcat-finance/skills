"""The Wave Delta reinstatement holds, and the demo notices when it does not.

Five of these run one demo condition each against the real tree. The sixth runs
the whole demo against a deliberately broken copy in a temporary directory, so
the demo cannot quietly become a script that passes on anything.
"""

import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEMO = ROOT / "docs" / "wave-delta-reinstatement-demo.py"


def load_demo():
    spec = importlib.util.spec_from_file_location("wave_delta_reinstatement_demo", DEMO)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReinstatementConditionTests(unittest.TestCase):
    """One test per condition, against the tree as it stands."""

    @classmethod
    def setUpClass(cls):
        cls.demo = load_demo()

    def test_every_retired_decision_has_one_standing_successor(self):
        result = self.demo.condition_successors(ROOT)
        self.assertTrue(result.ok, result.failures)
        self.assertEqual(len(result.evidence), 4, result.evidence)

    def test_adr_028_stays_accepted_with_its_handoff_amendment(self):
        result = self.demo.condition_adr_028(ROOT)
        self.assertTrue(result.ok, result.failures)

    def test_no_governing_document_disclaims_itself(self):
        result = self.demo.condition_banners(ROOT)
        self.assertTrue(result.ok, result.failures)

    def test_the_estate_record_names_the_reinstatement(self):
        result = self.demo.condition_estate(ROOT)
        self.assertTrue(result.ok, result.failures)

    def test_the_pinned_decision_record_tests_pass(self):
        result = self.demo.condition_pinned_tests(ROOT)
        self.assertTrue(result.ok, result.failures)


class BrokenTreeTests(unittest.TestCase):
    """The guard: a tree with the reinstatement undone must fail the demo.

    Without the demo script this test cannot pass, and without the checks inside
    it the broken copy would look the same as the real tree.
    """

    def test_a_tree_missing_a_successor_fails_the_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            broken = pathlib.Path(tmp) / "repo"
            (broken / "docs" / "decisions").mkdir(parents=True)
            for name in ("ADR-028", "ADR-029", "ADR-030", "ADR-031", "ADR-032",
                         "ADR-070", "ADR-071", "ADR-072", "ADR-073"):
                for path in (ROOT / "docs" / "decisions").glob(f"{name}-*.md"):
                    shutil.copy2(path, broken / "docs" / "decisions" / path.name)
            for name in ("wave-delta-issue-estate-2026-09-02.md",
                         "hexaemeron-checkpoint-programme-study.md",
                         "hexaemeron-checkpoint-programme-runbook.md"):
                shutil.copy2(ROOT / "docs" / name, broken / "docs" / name)
            shutil.copy2(DEMO, broken / "docs" / DEMO.name)
            # Undo one thing the reinstatement did: the lineage record loses its
            # successor, so a retired decision ends with nowhere to go again.
            for path in (broken / "docs" / "decisions").glob("ADR-073-*.md"):
                path.unlink()

            completed = subprocess.run(
                [sys.executable, str(broken / "docs" / DEMO.name), "--repo", str(broken)],
                capture_output=True, text=True, shell=False, timeout=600,
            )
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
            self.assertIn("ADR-032 is named by 0 standing successor(s)", completed.stdout)


if __name__ == "__main__":
    unittest.main()
