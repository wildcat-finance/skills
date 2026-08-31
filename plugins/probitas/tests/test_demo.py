"""The demo path, run the way the README tells someone to run it.

The last step of the runbook demonstrates. This runs the three commands as
subprocesses against a fixture, so it exercises the CLI a reader is told to
use rather than the functions underneath it, and it keeps the committed
example dossier honest by regenerating it and comparing.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from . import support

PROBITAS = os.path.join(support.SCRIPTS, "probitas.py")
DEMO_FIXTURE = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures", "demo")
EXAMPLE = os.path.join(support.PLUGIN_ROOT, "docs", "example-dossier.md")

ENTITY = "Acme Trading Ltd"
ADDRESS = "0x" + "a1" * 20


def run(*args):
    return subprocess.run(
        [sys.executable, PROBITAS, *args], capture_output=True, text=True, check=False
    )


class TestTheDemoPath(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.evidence = os.path.join(directory.name, "evidence.json")
        self.dossier = os.path.join(directory.name, "dossier.md")

        collected = run(
            "collect",
            "--entity",
            ENTITY,
            "--address",
            ADDRESS,
            "--fixtures",
            DEMO_FIXTURE,
            "--run-id",
            "demo",
            "--out",
            self.evidence,
        )
        self.assertEqual(collected.returncode, 0, collected.stderr)

        rendered = run("render", self.evidence, "--out", self.dossier)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)

        self.verified = run("verify", self.dossier, self.evidence)

    def test_it_exits_zero(self):
        self.assertEqual(
            self.verified.returncode, 0, self.verified.stdout + self.verified.stderr
        )

    def test_every_gate_line_reads_pass(self):
        lines = self.verified.stdout.strip().splitlines()
        self.assertEqual(len(lines), 5)
        for line in lines:
            self.assertIn(": pass --", line)
        self.assertNotIn("FAIL", self.verified.stdout)

    def test_it_gathered_from_all_three_record_bearing_venues(self):
        with open(self.evidence, encoding="utf-8") as handle:
            payload = json.load(handle)
        venues = {record["venue"] for record in payload["records"]}
        self.assertEqual(venues, {"wildcat", "morpho-blue", "morpho-midnight"})

    def test_the_venues_with_no_adapter_are_named_gaps(self):
        with open(self.evidence, encoding="utf-8") as handle:
            payload = json.load(handle)
        subjects = {gap["subject"] for gap in payload["gaps"]}
        for venue in ("maple", "aave-v3", "metamorpho"):
            with self.subTest(venue=venue):
                self.assertIn(f"{venue} borrowing history", subjects)
        self.assertNotIn("morpho-midnight borrowing history", subjects)

    def test_midnight_coverage_and_late_outcome_are_visible(self):
        with open(self.evidence, encoding="utf-8") as handle:
            payload = json.load(handle)
        coverage = next(
            row for row in payload["coverage"] if row["venue"] == "morpho-midnight"
        )
        outcome = next(
            record
            for record in payload["records"]
            if record["venue"] == "morpho-midnight"
            and record["claim"] == "maturity_outcome"
        )
        self.assertEqual(coverage["status"], "checked")
        self.assertIn("cursor walk(s) exhausted", coverage["note"])
        self.assertEqual(outcome["values"]["obligation_state"], "outstanding_at_maturity")
        self.assertEqual(outcome["values"]["observation_state"], "settled_late")

        with open(self.dossier, encoding="utf-8") as handle:
            document = handle.read()
        self.assertIn("Outstanding at maturity", document)
        self.assertIn("Settled late through liquidation", document)

    def test_a_wildcat_default_and_a_morpho_liquidation_read_differently(self):
        """The distinction the two adapters exist to hold."""
        with open(self.dossier, encoding="utf-8") as handle:
            document = handle.read()
        self.assertIn("Withdrawal expired unpaid", document)
        self.assertIn("past the grace period now", document)
        self.assertIn("price moving rather than a borrower walking away", document)

    def test_the_committed_example_matches_what_the_demo_produces(self):
        """A stale example is a lie about what the tool does."""
        with open(self.dossier, encoding="utf-8") as fresh:
            produced = fresh.read()
        with open(EXAMPLE, encoding="utf-8") as committed:
            self.assertEqual(
                committed.read(),
                produced,
                "docs/example-dossier.md is stale; regenerate it from the demo path",
            )

    def test_the_committed_example_passes_the_gates_too(self):
        result = run("verify", EXAMPLE, self.evidence)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
