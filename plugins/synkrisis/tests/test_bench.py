"""The work budget: a deterministic scale fixture and a refusal that can fire."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import support

SPEC = support.PLUGIN_ROOT / "tests" / "fixtures" / "scale" / "100-runs" / "spec.json"


class ScaleFixtureTests(unittest.TestCase):
    def test_peak_rss_uses_the_macos_byte_unit(self):
        bench = support.bench()
        normalise = getattr(
            bench,
            "peak_rss_mib",
            lambda raw_peak, _platform_name: raw_peak // 1024,
        )
        self.assertEqual(normalise(29 * 1024 * 1024, "darwin"), 29)

    def test_peak_rss_uses_the_posix_kib_unit(self):
        bench = support.bench()
        self.assertEqual(bench.peak_rss_mib(29 * 1024, "linux"), 29)

    def test_committed_spec_pins_the_studied_scale(self):
        document = support.read_json(SPEC)
        self.assertEqual(
            document,
            {
                "schema": "synkrisis-scale-fixture/v1",
                "runs": 100,
                "events_per_run": 1000,
                "seed": 449,
            },
        )

    def test_synthetic_records_are_deterministic(self):
        bench = support.bench()
        first = bench.synthetic_run("run-007", 7, 60)
        second = bench.synthetic_run("run-007", 7, 60)
        self.assertEqual(first, second)

    def test_synthetic_records_pass_the_admission_checks(self):
        bench = support.bench()
        synkrisis = support.synkrisis()
        payload = bench.synthetic_run("run-003", 3, 60)
        record = synkrisis.RunRecord(
            run_id="run-003",
            record="records/run-003.jsonl",
            sha256=support.sha256(payload),
            bytes=len(payload),
            validation={"tool": "constructed", "status": "accepted"},
            redaction={
                "profile": "promise-machine-run-observation-capture/v1",
                "status": "accepted",
            },
            binding={"status": "unavailable", "reason": "constructed fixture"},
        )
        features = synkrisis.parse_record_events(
            payload, record, "records/run-003.jsonl", synkrisis.EventBudget()
        )
        self.assertEqual(features["events"], payload.count(b"\n"))
        self.assertEqual(features["context"]["selected_skill"], "mason")


class BudgetCommandTests(unittest.TestCase):
    def run_bench(self, fixture, *arguments):
        return subprocess.run(  # phylax: allow subprocess: fixed argv local script, no shell
            [
                sys.executable,
                str(support.SCRIPTS / "bench_synkrisis.py"),
                "--fixture",
                str(fixture),
                *arguments,
            ],
            capture_output=True,
            text=True,
            cwd=support.REPO_ROOT,
        )

    def small_fixture(self, scratch):
        fixture = Path(scratch) / "small"
        fixture.mkdir()
        (fixture / "spec.json").write_text(
            json.dumps(
                {
                    "schema": "synkrisis-scale-fixture/v1",
                    "runs": 4,
                    "events_per_run": 40,
                    "seed": 449,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return fixture

    def test_small_budget_run_passes_and_records_its_method(self):
        with tempfile.TemporaryDirectory() as scratch:
            completed = self.run_bench(
                self.small_fixture(scratch), "--max-seconds", "30", "--max-rss-mib", "512"
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            result = json.loads(completed.stdout.splitlines()[0])
            for key in (
                "fixture_spec_sha256",
                "python",
                "platform",
                "repetitions",
                "max_seconds_observed",
                "peak_rss_mib",
            ):
                self.assertIn(key, result)

    def test_exceeded_budget_is_a_visible_refusal(self):
        with tempfile.TemporaryDirectory() as scratch:
            completed = self.run_bench(
                self.small_fixture(scratch),
                "--max-seconds",
                "0.000001",
                "--max-rss-mib",
                "512",
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("refused", completed.stdout)

    def test_unsupported_spec_is_refused(self):
        with tempfile.TemporaryDirectory() as scratch:
            fixture = Path(scratch) / "bad"
            fixture.mkdir()
            (fixture / "spec.json").write_text('{"schema": "other/v1"}\n', encoding="utf-8")
            completed = self.run_bench(
                fixture, "--max-seconds", "30", "--max-rss-mib", "512"
            )
            self.assertEqual(completed.returncode, 1)


class DemoPathTests(unittest.TestCase):
    def test_demo_path_exits_zero_twice_with_identical_bytes(self):
        synkrisis = support.synkrisis()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch).resolve()
            support.copy_example_into(root)
            first = support.run_full_path(root)
            self.assertEqual(first["status"], "verified")
            report = (root / "out/report.md").read_bytes()
            second = support.run_full_path(root)
            self.assertEqual(second["status"], "verified")
            self.assertEqual((root / "out/report.md").read_bytes(), report)
            self.assertIsNotNone(synkrisis)

    def run_cli(self, *arguments, cwd):
        return subprocess.run(  # phylax: allow subprocess: fixed argv local script, no shell
            [sys.executable, str(support.SCRIPTS / "synkrisis.py"), *arguments],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

    def test_incompatible_cohort_demonstration_exits_non_zero(self):
        """The first negative demonstration, at the command surface.

        `tests/test_cohort.py` holds the same refusal as a unit case. What is
        demonstrated here is that a person following the documented commands
        sees a non-zero exit and one stable code rather than an empty or
        partial cohort, which is the claim the runbook's exit gate makes.
        """
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch).resolve()
            support.copy_example_into(root)
            policy = support.read_json(root / "policy.json")
            # No run in the declared universe carries this skill, so the
            # policy leaves nothing eligible to compare.
            policy["dimensions"]["context.selected_skill"]["value"] = "surveyor"
            support.write(root, "policy.json", support.canonical(policy))
            completed = self.run_cli(
                "cohort", "--manifest", "manifest.json", "--policy", "policy.json",
                "--out", "out/cohort.json", "--json", cwd=str(root),
            )
            self.assertEqual(completed.returncode, 1, completed.stdout)
            document = json.loads(completed.stdout)
            self.assertTrue(document["code"].startswith("SK"))
            self.assertTrue(document["recovery"])
            self.assertFalse((root / "out" / "cohort.json").exists())

    def test_causal_strengthening_demonstration_exits_non_zero(self):
        """The second negative demonstration, at the command surface.

        A catalogue whose prose asserts a cause is refused before any rule
        runs, so no findings document exists to be read as a causal claim.
        """
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch).resolve()
            support.copy_example_into(root)
            support.run_cohort(root)
            rules = support.read_json(support.RULES)
            rules["rules"][0]["title"] = "Late boundary reads caused the higher token use"
            support.write(root, "rules.json", support.canonical(rules))
            completed = self.run_cli(
                "diagnose", "--cohort", "out/cohort.json", "--rules", "rules.json",
                "--out", "out/findings.json", "--json", cwd=str(root),
            )
            self.assertEqual(completed.returncode, 1, completed.stdout)
            document = json.loads(completed.stdout)
            self.assertTrue(document["code"].startswith("SK"))
            self.assertTrue(document["recovery"])
            self.assertFalse((root / "out" / "findings.json").exists())


if __name__ == "__main__":
    unittest.main()
