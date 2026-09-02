"""The reference release: verified, graded, drift-held and rebuildable."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.support import PLUGIN_ROOT, REPO_ROOT, SCRIPTS  # noqa: F401

from berean_lib import evals, jsonio, promote, release
from tests.test_corpus import failures

EXAMPLE = PLUGIN_ROOT / "examples" / "goldfinch-demo-v0"
RELEASE_DIR = EXAMPLE / "release"
LAZARUS_RPC = (
    REPO_ROOT
    / "plugins"
    / "lazarus"
    / "examples"
    / "goldfinch-v0-release"
    / "fixture"
    / "rpc.jsonl"
)


class ReferenceReleaseTests(unittest.TestCase):
    def test_the_shipped_release_verifies_clean_and_is_active(self):
        checks = release.verify(str(RELEASE_DIR))
        self.assertEqual(failures(checks), [])
        promotions = [check for check in checks if check.name == "release-promotions"]
        self.assertEqual(promotions[0].detail, "active")

    def test_the_shipped_corpus_grades_clean_and_reproduces_its_report(self):
        report, results = evals.run(str(RELEASE_DIR))
        self.assertEqual(report["failed"], 0)
        self.assertTrue(all(passed for _, passed, _ in results))
        committed = jsonio.load(str(RELEASE_DIR / "evals" / "report.json"), "report")
        self.assertEqual(report, committed)

    def test_every_adversarial_class_appears(self):
        cases = jsonio.load(str(RELEASE_DIR / "evals" / "cases.json"), "cases")
        classes = {case["adversarial"] for case in cases["cases"]} - {None}
        self.assertEqual(classes, set(evals.ADVERSARIAL_CLASSES))

    def test_the_reads_are_recorded_rpc_and_never_upgraded(self):
        document = release.load(str(RELEASE_DIR))
        self.assertEqual(document["retention"], "none")
        from berean_lib import reads as reads_lib

        records = reads_lib.load(str(RELEASE_DIR / "reads.jsonl"))
        self.assertEqual(
            {record["evidence"] for record in records.values()}, {"recorded-rpc"}
        )


class DriftTests(unittest.TestCase):
    def test_the_copied_reads_match_the_lazarus_fixture_byte_for_byte(self):
        if not LAZARUS_RPC.is_file():
            self.skipTest("the Lazarus fixture is not in this tree")
        with open(LAZARUS_RPC, "rb") as handle:
            source = handle.read()
        with open(RELEASE_DIR / "reads.jsonl", "rb") as handle:
            copy = handle.read()
        self.assertEqual(copy, source)


class RebuildTests(unittest.TestCase):
    def test_rebuild_reproduces_the_committed_bytes(self):
        with tempfile.TemporaryDirectory() as holder:
            working = os.path.join(holder, "release")
            shutil.copytree(RELEASE_DIR, working)
            for current, _, files in os.walk(working):
                for name in files:
                    if name != "reads.jsonl":
                        os.remove(os.path.join(current, name))
            completed = subprocess.run(
                [sys.executable, str(EXAMPLE / "rebuild.py"), "--release", working],
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            for current, _, files in os.walk(RELEASE_DIR):
                for name in sorted(files):
                    committed_path = os.path.join(current, name)
                    relative = os.path.relpath(committed_path, RELEASE_DIR)
                    rebuilt_path = os.path.join(working, relative)
                    with self.subTest(file=relative):
                        with open(committed_path, "rb") as handle:
                            committed = handle.read()
                        with open(rebuilt_path, "rb") as handle:
                            self.assertEqual(handle.read(), committed)


class DemoTests(unittest.TestCase):
    def test_the_demo_walks_every_stage_clean(self):
        completed = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("every stage held", completed.stdout)
        for gate in ("release-corpus", "release-reads", "release-promotions"):
            self.assertIn(gate, completed.stdout)


if __name__ == "__main__":
    unittest.main()
