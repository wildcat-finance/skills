"""One collect run over both routes, end to end and offline.

The union is the capability issue 391 asked for, and nothing proves it except
running it: an adapter route and an archive route into one evidence file, one
dossier, five gates. The index comes from Alexandria's checked-in
demonstration rather than a fixture of our own, because a second copy of that
build would drift from the one Alexandria maintains, and Probitas already
imports `alexandria_lib` at run time on this path.

The build is the slow part of this module, so it happens once for the class.
Nothing here reaches the network.
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from . import support

PROBITAS = os.path.join(support.SCRIPTS, "probitas.py")
REPO_ROOT = os.path.dirname(os.path.dirname(support.PLUGIN_ROOT))
ALEXANDRIA = os.path.join(REPO_ROOT, "plugins", "alexandria")
DEMO = os.path.join(ALEXANDRIA, "examples", "credit-history-v0", "demo.py")
FIXTURES = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures", "demo")

ENTITY = "Acme Trading Ltd"
FIXTURE_ADDRESS = "0x" + "a1" * 20


def load_demo():
    """Import Alexandria's demonstration, or say why the union cannot be shown.

    Absent Alexandria is a real deployment: Probitas ships on its own and the
    union simply cannot be demonstrated there, so the class skips. Alexandria
    present with its demonstration missing is a defect, and skipping on it
    would turn the only end-to-end proof of this run's capability into a
    silence that reads as a pass.
    """
    if not os.path.isdir(ALEXANDRIA):
        return None
    if not os.path.isfile(DEMO):
        raise AssertionError(
            f"{DEMO} is missing while Alexandria sits beside Probitas; the "
            "union has no end-to-end proof and this would otherwise skip"
        )
    spec = importlib.util.spec_from_file_location("alexandria_demo", DEMO)
    module = importlib.util.module_from_spec(spec)
    sys.modules["alexandria_demo"] = module
    spec.loader.exec_module(module)
    return module


def run(*args):
    return subprocess.run(
        [sys.executable, PROBITAS, *args], capture_output=True, text=True, check=False
    )


class TestTheDemonstrationIsReachable(unittest.TestCase):
    """A skip must not stand in for the proof this run exists to give."""

    def test_alexandria_beside_probitas_means_the_demonstration_is_there(self):
        if not os.path.isdir(ALEXANDRIA):
            self.skipTest("Probitas is installed standalone")
        self.assertTrue(os.path.isfile(DEMO), DEMO)


class TestTheUnion(unittest.TestCase):
    """Both routes in one run, against a real index built offline."""

    @classmethod
    def setUpClass(cls):
        cls.demo = load_demo()
        if cls.demo is None:
            raise unittest.SkipTest("Alexandria is not installed beside Probitas")
        cls.directory = tempfile.mkdtemp(prefix="probitas-union-")
        output = os.path.join(cls.directory, "credit-history-v0")
        cls.demo.build_demo(output, check_expected=False)
        cls.index = os.path.join(output, "alexandria.sqlite")
        plan = cls.demo.load_bytes(cls.demo.PLAN.read_bytes(), "demo plan")
        cls.archive_address = plan["query"]["addresses"][0]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.directory, ignore_errors=True)

    def collect(self, *addresses):
        arguments = ["collect", "--entity", ENTITY]
        for address in addresses:
            arguments.extend(("--address", address))
        arguments.extend(
            [
                "--fixtures",
                FIXTURES,
                "--alexandria-index",
                self.index,
                "--run-id",
                "union",
                "--out",
                "-",
            ]
        )
        result = run(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout), result.stderr

    def test_one_file_carries_adapter_records_and_archive_records(self):
        payload, _ = self.collect(FIXTURE_ADDRESS, self.archive_address)
        venues = {record["venue"] for record in payload["records"]}
        self.assertIn("wildcat", venues)
        self.assertIn("morpho-blue", venues)
        self.assertIn("clearpool", venues)

    def test_both_source_classes_appear_in_the_coverage_table(self):
        payload, _ = self.collect(FIXTURE_ADDRESS, self.archive_address)
        sources = {}
        for row in payload["coverage"]:
            sources.setdefault(row["source"], set()).add(row["venue"])
        self.assertIn("wildcat", sources["fixtures"])
        self.assertIn("clearpool", sources["archive"])
        self.assertIn("none", sources)

    def test_an_archive_row_names_its_releases(self):
        payload, _ = self.collect(FIXTURE_ADDRESS, self.archive_address)
        for row in payload["coverage"]:
            if row["source"] != "archive":
                continue
            with self.subTest(venue=row["venue"]):
                self.assertTrue(row["releases"])
                self.assertTrue(row["releases"].startswith("sha256:"))

    def test_an_adapter_row_names_no_release(self):
        payload, _ = self.collect(FIXTURE_ADDRESS, self.archive_address)
        for row in payload["coverage"]:
            if row["source"] in ("fixtures", "live"):
                with self.subTest(venue=row["venue"]):
                    self.assertIsNone(row["releases"])

    def test_the_summary_names_both_routes(self):
        directory = tempfile.mkdtemp(prefix="probitas-union-out-")
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "evidence.json")
        result = run(
            "collect", "--entity", ENTITY,
            "--address", FIXTURE_ADDRESS, "--address", self.archive_address,
            "--fixtures", FIXTURES, "--alexandria-index", self.index,
            "--run-id", "union", "--out", path,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("routes: fixtures (", result.stderr)
        self.assertIn("archive (", result.stderr)

    def test_an_archive_only_address_still_comes_back_checked(self):
        """Conservative coverage: adding an unharvested address is what errors."""
        payload, _ = self.collect(self.archive_address)
        clearpool = next(
            row for row in payload["coverage"] if row["venue"] == "clearpool"
        )
        self.assertEqual(clearpool["status"], "checked")
        self.assertEqual(clearpool["source"], "archive")

    def test_a_venue_the_adapters_answered_is_not_reported_as_a_gap(self):
        payload, _ = self.collect(FIXTURE_ADDRESS, self.archive_address)
        subjects = {gap["subject"] for gap in payload["gaps"]}
        self.assertNotIn("wildcat borrowing history", subjects)
        self.assertNotIn("morpho-blue borrowing history", subjects)
        self.assertIn("maple borrowing history", subjects)

    def test_the_union_dossier_passes_all_five_gates(self):
        directory = tempfile.mkdtemp(prefix="probitas-union-gate-")
        self.addCleanup(shutil.rmtree, directory, True)
        evidence = os.path.join(directory, "evidence.json")
        dossier = os.path.join(directory, "dossier.md")
        collected = run(
            "collect", "--entity", ENTITY,
            "--address", FIXTURE_ADDRESS, "--address", self.archive_address,
            "--fixtures", FIXTURES, "--alexandria-index", self.index,
            "--run-id", "union", "--out", evidence,
        )
        self.assertEqual(collected.returncode, 0, collected.stderr)
        rendered = run("render", evidence, "--out", dossier)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        verified = run("verify", dossier, evidence)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        lines = verified.stdout.strip().splitlines()
        self.assertEqual(len(lines), 5)
        for line in lines:
            self.assertIn(": pass --", line)
        with open(dossier, encoding="utf-8") as handle:
            document = handle.read()
        self.assertIn("| Venue | Status | Source | Range | Records | Note |", document)
        self.assertIn("| archive |", document)
        self.assertIn("| fixtures |", document)


if __name__ == "__main__":
    unittest.main()
