"""Conformance never accepts stale, incomplete or unrelated replay evidence."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_authority import conformance as owner, native_io, replay_conformance as subject

ROOT = Path(__file__).resolve().parents[3]


class ReplayConformanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        for path in (*subject.SOURCES, *subject.FILES, subject.MANIFEST):
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        self.cases = subject.inputs(self.root)["cases"]
        self.expected, self.hostile_count = subject.expected_history(self.root)

    def value(self):
        ariadne = [case for case in self.cases if case.startswith(subject.ARIADNE_MODULE + ".")]
        return {"schema": "checkpoint-authority-replay-execution/v1", "complete": True, "passed": True,
            "tests_run": len(self.cases), "subtests_run": 0, "started": self.cases[:], "completed": self.cases[:],
            "failure_cases": [], "error_cases": [], "failures": 0, "errors": 0, "skips": 0,
            "expected_failures": 0, "unexpected_successes": 0, "output_sha256": "c" * 64,
            "python": sys.version.split()[0], "replay": {
                "history_sha256": hashlib.sha256((self.root / subject.HISTORY).read_bytes()).hexdigest(),
                **{key: self.expected[key] for key in ("records", "bytes", "head_sha256", "policy_history", "decisions", "accepted", "historical_permits")},
                "hostile_refused": self.hostile_count, "current_eligibility": ["eligible"] * len(self.expected["accepted"]),
                "ariadne_cases": len(ariadne)}}

    def execute(self, value):
        result = native_io.Execution(subject.CRITERION, "replay-conformance", "a" * 64, 0, json.dumps(value).encode(), b"", 1)
        with patch.object(native_io, "execute", return_value=result): return subject.execute(self.root)

    def test_manifest_is_owned_and_covers_replay_and_ariadne_cases(self):
        from checkpoint_authority_replay_corpus import value
        self.assertEqual(json.loads((ROOT / subject.MANIFEST).read_bytes()), value(ROOT))
        self.assertGreaterEqual(sum(case.startswith(subject.ARIADNE_MODULE + ".") for case in self.cases), 7)
        self.assertGreaterEqual(sum(case.startswith("test_checkpoint_authority_replay.") for case in self.cases), 20)
        self.assertGreaterEqual(self.hostile_count, 14)

    def test_valid_execution_shape_preserves_replay_bindings(self):
        self.assertEqual(self.execute(self.value())[0], self.value())

    def test_replay_evidence_must_match_the_committed_history(self):
        for mutate in (lambda v: v["replay"].update(history_sha256="f" * 64),
                lambda v: v["replay"].update(records=v["replay"]["records"] + 1),
                lambda v: v["replay"].update(head_sha256="f" * 64),
                lambda v: v["replay"].update(accepted=[]),
                lambda v: v["replay"].update(hostile_refused=0),
                lambda v: v["replay"].update(current_eligibility=["unknown"] * len(v["replay"]["accepted"])),
                lambda v: v["replay"].update(ariadne_cases=0),
                lambda v: v["replay"].update(decisions={"count": 0, "tail": None}),
                lambda v: v["replay"].pop("bytes"),
                lambda v: v.update(python="3.13.0")):
            value = self.value(); mutate(value)
            with self.subTest(replay=value["replay"]), self.assertRaises(owner.Refusal): self.execute(value)

    def test_partial_duplicate_and_skipped_execution_never_passes_criterion(self):
        for mutate in (lambda v: v.update(complete=False), lambda v: v.update(replay=None),
                lambda v: v.update(tests_run=0), lambda v: v.update(skips=1), lambda v: v.update(expected_failures=1),
                lambda v: v.update(completed=v["completed"][:-1]),
                lambda v: v.update(started=v["started"][:-1] + v["started"][:1])):
            value = self.value(); mutate(value); report = {"value": False, "exit": 3}
            with patch.object(subject, "execute", return_value=(value, 0, "a" * 64, "b" * 64)):
                event = subject.run(self.root, report)
            self.assertFalse(report["value"]); self.assertFalse(event["complete"])
            self.assertEqual(event["status"], "failed")

    def test_fixture_drift_and_source_change_refuse(self):
        target = self.root / subject.FILES[0]; target.write_bytes(target.read_bytes() + b"x")
        with self.assertRaisesRegex(owner.Refusal, "replay-fixture-drift"): subject.inputs(self.root)
        target.write_bytes((ROOT / subject.FILES[0]).read_bytes())
        target = self.root / subject.FILES[3]; target.write_bytes(target.read_bytes() + b"\n")
        with self.assertRaisesRegex(owner.Refusal, "replay-fixture-drift"): subject.inputs(self.root)
        target.write_bytes((ROOT / subject.FILES[3]).read_bytes())
        def change(root):
            path = root / subject.SOURCES[0]; path.write_bytes(path.read_bytes() + b"\n")
            return self.value(), 0, "a" * 64, "b" * 64
        with patch.object(subject, "execute", side_effect=change), self.assertRaisesRegex(owner.Refusal, "source-changed"):
            subject.run(self.root, {"value": False, "exit": 3})

    def test_manifest_without_ariadne_cases_or_with_foreign_cases_refuses(self):
        path = self.root / subject.MANIFEST; original = json.loads(path.read_bytes())
        for change in (lambda m: m.update(cases=[c for c in m["cases"] if not c.startswith(subject.ARIADNE_MODULE + ".")]),
                lambda m: m.update(cases=m["cases"] + ["test_hexctl.HexctlTests.test_other"]),
                lambda m: m.update(criterion="native-boundary-coverage"),
                lambda m: m["files"].pop()):
            manifest = json.loads(json.dumps(original)); change(manifest)
            path.write_bytes(json.dumps(manifest).encode())
            with self.subTest(manifest=sorted(manifest)), self.assertRaises(owner.Refusal): subject.inputs(self.root)
        path.write_bytes(json.dumps(original).encode())

    def test_budget_record_meets_the_declared_study_budget(self):
        record = json.loads((ROOT / subject.BUDGET).read_bytes())
        self.assertEqual(record["schema"], "checkpoint-authority-replay-budget/v1")
        self.assertEqual(record["budget"]["records_minimum"], 1280)
        self.assertEqual(record["budget"]["peak_rss_bytes_maximum"], 512 * 1024 * 1024)
        measured = record["measured"]
        self.assertGreaterEqual(measured["records"], 1280)
        self.assertEqual(measured["signed_body_decodes"], measured["records"])
        self.assertEqual(measured["carrier_decodes"], measured["records"])
        self.assertEqual(measured["retained_body_nodes"], 0)
        self.assertLess(measured["peak_rss_bytes"]["max"], 512 * 1024 * 1024)
        self.assertEqual(len(measured["wall_ms"]["samples"]), 3)
        self.assertTrue(record["passed"]); self.assertTrue(all(record["verdict"].values()))
        self.assertEqual(record["study_comparison"]["decode_work"], 1280)
        self.assertIn("No production latency", record["limits"])


if __name__ == "__main__": unittest.main()
