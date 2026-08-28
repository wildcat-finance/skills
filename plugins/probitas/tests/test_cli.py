"""The CLI, exercised the way an operator would run it."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from . import support

from probitas_lib import registry  # noqa: E402

PROBITAS = os.path.join(support.SCRIPTS, "probitas.py")
FIXTURES = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures")


def run(*args):
    return subprocess.run(
        [sys.executable, PROBITAS, *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestVenuesCommand(unittest.TestCase):
    def test_it_lists_every_venue(self):
        result = run("venues", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        venues = json.loads(result.stdout)
        self.assertEqual(len(venues), len(registry.all_venues()))
        self.assertIn("wildcat", [v["id"] for v in venues])

    def test_the_plain_listing_says_which_are_implemented(self):
        result = run("venues")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not implemented", result.stdout)


class TestCollectCommand(unittest.TestCase):
    address = "0x" + "a1" * 20

    def collect(self, *extra, case="empty"):
        """Always against a fixture.

        The suite must never reach the network. A test that quietly makes a
        live request passes on a laptop, fails in CI behind a proxy, and tells
        you nothing either way.
        """
        result = run(
            "collect",
            "--entity",
            "Acme Trading Ltd",
            "--address",
            self.address,
            "--fixtures",
            os.path.join(FIXTURES, case),
            "--out",
            "-",
            *extra,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_the_evidence_file_has_the_five_top_level_blocks(self):
        payload = self.collect()
        for key in ("run", "subject", "records", "coverage", "gaps"):
            self.assertIn(key, payload)

    def test_every_registry_venue_appears_in_coverage(self):
        payload = self.collect()
        self.assertEqual(len(payload["coverage"]), len(registry.all_venues()))

    def test_an_unchecked_venue_becomes_a_named_gap(self):
        payload = self.collect()
        subjects = [gap["subject"] for gap in payload["gaps"]]
        self.assertIn("maple borrowing history", subjects)
        # Venues with no adapter remain named gaps. A venue that was checked
        # and came back empty is a finding rather than a hole.
        self.assertNotIn("wildcat borrowing history", subjects)
        self.assertNotIn("morpho-blue borrowing history", subjects)
        self.assertNotIn("euler borrowing history", subjects)
        self.assertEqual(len(payload["gaps"]), len(registry.unimplemented()))

    def test_midnight_empty_is_checked_without_a_gap_and_keeps_schema_one(self):
        payload = self.collect()
        coverage = next(
            row for row in payload["coverage"] if row["venue"] == "morpho-midnight"
        )
        self.assertEqual(payload["schema"], 1)
        self.assertEqual(coverage["status"], "empty")
        self.assertIn("cursor walk(s) exhausted", coverage["note"])
        self.assertNotIn(
            "morpho-midnight borrowing history",
            {gap["subject"] for gap in payload["gaps"]},
        )

    def test_midnight_refusal_becomes_error_coverage_and_a_named_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(FIXTURES, "empty")
            for name in os.listdir(source):
                if name != "morpho-midnight.json":
                    shutil.copyfile(
                        os.path.join(source, name), os.path.join(directory, name)
                    )
            payload = self.collect(case=directory)

        coverage = next(
            row for row in payload["coverage"] if row["venue"] == "morpho-midnight"
        )
        gap = next(
            gap
            for gap in payload["gaps"]
            if gap["subject"] == "morpho-midnight borrowing history"
        )
        self.assertEqual(coverage["status"], "error")
        self.assertEqual(gap["reason"], coverage["note"])
        self.assertIn("no records emitted", coverage["note"])
        self.assertNotIn(directory, coverage["note"])

    def test_inferred_addresses_stay_in_their_own_tier(self):
        payload = self.collect("--inferred", "0x" + "b2" * 20)
        tiers = {a["address"]: a["provenance"] for a in payload["subject"]["addresses"]}
        self.assertEqual(tiers[self.address], "declared")
        self.assertEqual(tiers["0x" + "b2" * 20], "inferred")

    def test_a_bad_address_is_refused_with_exit_two(self):
        result = run(
            "collect",
            "--entity",
            "Acme",
            "--address",
            "not-an-address",
            "--fixtures",
            os.path.join(FIXTURES, "empty"),
            "--out",
            "-",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a 20-byte hex address", result.stderr)

    def test_writing_to_a_file_reports_what_it_wrote(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "evidence.json")
            result = run(
                "collect",
                "--entity",
                "Acme",
                "--address",
                self.address,
                "--fixtures",
                os.path.join(FIXTURES, "empty"),
                "--out",
                path,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                f"{len(registry.implemented())} of "
                f"{len(registry.all_venues())} venue(s) checked",
                result.stderr,
            )
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["schema"], 1)

    def test_two_runs_produce_identical_bytes(self):
        arguments = (
            "collect",
            "--entity",
            "Acme",
            "--address",
            self.address,
            "--fixtures",
            os.path.join(FIXTURES, "defaulted"),
            "--out",
            "-",
            "--run-id",
            "fixed",
        )
        self.assertEqual(run(*arguments).stdout, run(*arguments).stdout)

    def test_every_aggregate_fixture_has_deterministic_midnight_bytes(self):
        for case in (
            "clean",
            "cured",
            "defaulted",
            "demo",
            "empty",
            "euler-borrower",
            "euler-empty",
            "morpho-bad-debt",
            "morpho-clean",
            "morpho-empty",
            "morpho-liquidated",
        ):
            with self.subTest(case=case):
                first = self.collect(case=case)
                second = self.collect(case=case)
                self.assertEqual(first, second)
                coverage = next(
                    row
                    for row in first["coverage"]
                    if row["venue"] == "morpho-midnight"
                )
                expected = "checked" if case == "demo" else "empty"
                self.assertEqual(coverage["status"], expected)


class TestTheWholeSequence(unittest.TestCase):
    """collect, render, verify, the way an operator runs it."""

    address = "0x" + "a1" * 20

    def pipeline(self, case="defaulted"):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        evidence = os.path.join(directory.name, "evidence.json")
        dossier = os.path.join(directory.name, "dossier.md")

        collected = run(
            "collect",
            "--entity",
            "Acme Trading Ltd",
            "--address",
            self.address,
            "--fixtures",
            os.path.join(FIXTURES, case),
            "--run-id",
            "demo",
            "--out",
            evidence,
        )
        self.assertEqual(collected.returncode, 0, collected.stderr)

        rendered = run("render", evidence, "--out", dossier)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)

        return evidence, dossier, run("verify", dossier, evidence)

    def test_the_demo_path_ends_with_every_gate_passing(self):
        _, _, verified = self.pipeline()
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertEqual(len(verified.stdout.strip().splitlines()), 5)
        self.assertNotIn("FAIL", verified.stdout)

    def test_a_breached_gate_exits_one_and_says_which(self):
        _, dossier, _ = self.pipeline()
        with open(dossier, encoding="utf-8") as handle:
            document = handle.read()
        with open(dossier, "w", encoding="utf-8") as handle:
            handle.write(document.replace("## What could not be established", "## Notes"))
        evidence = os.path.join(os.path.dirname(dossier), "evidence.json")
        result = run("verify", dossier, evidence)
        self.assertEqual(result.returncode, 1)
        self.assertIn("gate 4", result.stdout)
        self.assertIn("does not ship", result.stderr)

    def test_rendering_twice_gives_identical_bytes(self):
        evidence, _, _ = self.pipeline()
        self.assertEqual(
            run("render", evidence, "--out", "-").stdout,
            run("render", evidence, "--out", "-").stdout,
        )

    def test_rendering_something_that_is_not_evidence_exits_two(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = os.path.join(directory.name, "not-evidence.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('{"hello": "world"}')
        result = run("render", path, "--out", "-")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a probitas evidence file", result.stderr)

    def test_the_dossier_puts_the_gaps_before_the_summary(self):
        _, dossier, _ = self.pipeline()
        with open(dossier, encoding="utf-8") as handle:
            document = handle.read()
        self.assertLess(
            document.index("## What could not be established"),
            document.index("## Summary"),
        )


if __name__ == "__main__":
    unittest.main()
