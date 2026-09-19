"""Conformance never accepts stale, incomplete or unrelated released-interoperability evidence."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/fiat/scripts"))
from checkpoint_authority import conformance as owner, demo, native_io, network, release
from checkpoint_authority.canonical import digest
from checkpoint_authority import release_conformance as subject

ROOT = Path(__file__).resolve().parents[3]


class ReleaseConformanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        listed = [row["path"] for row in json.loads((ROOT / subject.MANIFEST).read_bytes())["files"]]
        for path in (*subject.SOURCES, *listed, subject.MANIFEST, release.MANIFEST):
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        self.cases = subject.inputs(self.root)["cases"]
        self.expected = json.loads((self.root / demo.EXPECTED).read_bytes())

    def value(self):
        metadata = json.loads((self.root / subject.WORKLOAD_METADATA).read_bytes())
        measured = {key: value for key, value in metadata.items() if key != "schema"}
        measured.update(schema="checkpoint-authority-release-workload-measurement/v1",
                        decodes={"carrier": measured["records"], "signed_statement": measured["records"],
                                 "additional_record_body": 0,
                                 "native_result": 256, "producer_ledger_line": 512, "other": 0},
                        journal_body_decodes=measured["records"], json_decodes_total=2 * measured["records"] + 768,
                        retained_body_nodes=0, repetitions=3, warmup_repetitions=0,
                        percentile_method="nearest-rank", wall_ms_median=2.0, wall_ms_p95=3.0,
                        samples=[{"wall_ms": time, "tracemalloc_peak_bytes": 300000,
                                  "peak_rss_bytes": 60000000} for time in (1.0, 2.0, 3.0)],
                        environment={"python": sys.version.split()[0], "platform": "test platform",
                                     "machine": "test", "processor": "test", "logical_cpus": 1,
                                     "measurement": "fresh-process-per-repetition", "contention": "test fixture"})
        return {"schema": "checkpoint-authority-release-execution/v1", "complete": True, "passed": True,
                "tests_run": len(self.cases), "subtests_run": 0, "started": self.cases[:],
                "completed": self.cases[:], "failure_cases": [], "error_cases": [], "failures": 0,
                "errors": 0, "skips": 0, "expected_failures": 0, "unexpected_successes": 0,
                "output_sha256": "c" * 64, "python": sys.version.split()[0], "workload": measured,
                "demonstration": {
                    "manifest_sha256": subject._hash(self.root, release.MANIFEST),
                    "reproducible_rebuilds": 2, "history_sha256": self.expected["history_sha256"],
                    "head_sha256": self.expected["head_sha256"], "records": self.expected["records"],
                    "accepted": self.expected["accepted"], "eligible": self.expected["eligible"],
                    "hostile_refused": 18, "interoperability_cases": 5,
                    "network_boundary": {"mechanism": "macos-sandbox-exec-deny-network",
                                         "launcher_sha256": network.prepare().launcher_sha256,
                                         "policy_sha256": digest(network.POLICY.encode()),
                                         "probe_sha256": digest(network.PROBE.encode()),
                                         "probe_exit": 0, "probe_operations": 4},
                    "current_eligibility_withheld": True, "wall_ms": 1234.5, "json_decodes": 200,
                    "tracemalloc_peak_bytes": 300000, "peak_rss_bytes": 60000000}}

    def execute(self, value):
        result = native_io.Execution(subject.CRITERION, "release-conformance", "a" * 64, 0,
                                     json.dumps(value).encode(), b"", 1)
        with patch.object(native_io, "execute", return_value=result):
            return subject.execute(self.root)

    def test_manifest_is_owned_and_covers_both_release_case_modules(self):
        from checkpoint_authority_release_corpus import manifest
        self.assertEqual(json.loads((ROOT / subject.MANIFEST).read_bytes()), manifest())
        for module in subject.MODULES:
            with self.subTest(module=module):
                self.assertGreaterEqual(sum(case.startswith(module + ".") for case in self.cases), 4)
        self.assertGreaterEqual(len(self.cases), 20)

    def test_valid_execution_shape_preserves_the_demonstration_bindings(self):
        self.assertEqual(self.execute(self.value())[0], self.value())

    def test_missing_study_workload_evidence_refuses(self):
        value = self.value(); value.pop("workload")
        with self.assertRaisesRegex(owner.Refusal, "release-execution-report"):
            self.execute(value)

    def test_workload_measurements_require_exact_corpus_counts_decodes_and_resources(self):
        mutations = (lambda v: v.update(workload_sha256="f" * 64),
                     lambda v: v.update(study_corpus_sha256="f" * 64),
                     lambda v: v.update(projection_sha256="f" * 64),
                     lambda v: v.update(model_events=1279), lambda v: v.update(model_decisions=511),
                     lambda v: v.update(cancelled=0), lambda v: v.update(denied=0),
                     lambda v: v.update(records=True), lambda v: v.update(repetitions=1),
                     lambda v: v.update(warmup_repetitions=1),
                     lambda v: v.update(wall_ms_median=1.0), lambda v: v.update(wall_ms_p95=2.0),
                     lambda v: v.update(retained_body_nodes=1), lambda v: v.update(samples=v["samples"][:1]),
                     lambda v: v["decodes"].update(carrier=0),
                     lambda v: v["decodes"].update(signed_statement=v["records"] + 1),
                     lambda v: v["decodes"].update(additional_record_body=1),
                     lambda v: v.update(journal_body_decodes=0), lambda v: v.update(json_decodes_total=0),
                     lambda v: v["decodes"].update(other=-1),
                     lambda v: v["samples"][0].update(wall_ms=float("nan")),
                     lambda v: v["samples"][0].update(peak_rss_bytes=536870912),
                     lambda v: v["samples"][0].pop("tracemalloc_peak_bytes"),
                     lambda v: v["environment"].update(python="3.13.0"),
                     lambda v: v["environment"].update(machine=""),
                     lambda v: v["environment"].update(logical_cpus=False),
                     lambda v: v["environment"].update(measurement="same-process"))
        for index, mutate in enumerate(mutations):
            value = self.value(); mutate(value["workload"])
            with self.subTest(index=index), self.assertRaisesRegex(owner.Refusal, "release-execution-report"):
                self.execute(value)

    def test_workload_metadata_has_closed_typed_fields(self):
        path = self.root / subject.WORKLOAD_METADATA
        original = json.loads(path.read_bytes())
        for mutated in ([], {**original, "records": True}, {**original, "extra": 1},
                        {key: val for key, val in original.items() if key != "records"}):
            value = self.value()
            path.write_text(json.dumps(mutated))
            with self.subTest(metadata=mutated), self.assertRaisesRegex(owner.Refusal, "release-execution-report"):
                self.execute(value)
            path.write_text(json.dumps(original))

    def test_original_study_bytes_reproduce_without_changing_the_research_evidence(self):
        import hashlib
        from checkpoint_authority_release_workload import study_rows
        rows = study_rows()
        self.assertEqual(len(rows), 1280)
        self.assertEqual(len({row["decision"] for row, _ in rows}), 512)
        self.assertEqual(hashlib.sha256(b"\n".join(raw for _, raw in rows) + b"\n").hexdigest(),
                         subject.STUDY_SHA)

    def test_demonstration_evidence_must_match_the_committed_release_and_history(self):
        for mutate in (lambda v: v["demonstration"].update(manifest_sha256="f" * 64),
                       lambda v: v["demonstration"].update(history_sha256="f" * 64),
                       lambda v: v["demonstration"].update(head_sha256="f" * 64),
                       lambda v: v["demonstration"].update(records=v["demonstration"]["records"] + 1),
                       lambda v: v["demonstration"].update(reproducible_rebuilds=1),
                       lambda v: v["demonstration"].update(hostile_refused=0),
                       lambda v: v["demonstration"].update(interoperability_cases=0),
                       lambda v: v["demonstration"].update(current_eligibility_withheld=False),
                       lambda v: v["demonstration"]["network_boundary"].update(probe_exit=1),
                       lambda v: v["demonstration"]["network_boundary"].update(probe_operations=0),
                       lambda v: v["demonstration"]["network_boundary"].update(policy_sha256="f" * 64),
                       lambda v: v["demonstration"]["network_boundary"].update(launcher_sha256="f" * 64),
                       lambda v: v["demonstration"].pop("network_boundary"),
                       lambda v: v["demonstration"].update(eligible=0),
                       lambda v: v["demonstration"].pop("peak_rss_bytes"),
                       lambda v: v.update(python="3.13.0")):
            value = self.value(); mutate(value)
            with self.subTest(demonstration=value["demonstration"]), self.assertRaises(owner.Refusal):
                self.execute(value)

    def test_a_peak_above_the_declared_ceiling_refuses(self):
        value = self.value()
        value["demonstration"]["peak_rss_bytes"] = release.RESOURCE_LIMITS["declared_peak_rss_ceiling_bytes"]
        with self.assertRaises(owner.Refusal):
            self.execute(value)

    def test_partial_duplicate_and_skipped_execution_never_passes_criterion(self):
        for mutate in (lambda v: v.update(complete=False), lambda v: v.update(demonstration=None),
                       lambda v: v.update(workload=None),
                       lambda v: v.update(tests_run=0), lambda v: v.update(skips=1),
                       lambda v: v.update(expected_failures=1),
                       lambda v: v.update(completed=v["completed"][:-1]),
                       lambda v: v.update(started=v["started"][:-1] + v["started"][:1])):
            value = self.value(); mutate(value); report = {"value": False, "exit": 3}
            with patch.object(subject, "execute", return_value=(value, 0, "a" * 64, "b" * 64)):
                event = subject.run(self.root, report)
            self.assertFalse(report["value"]); self.assertFalse(event["complete"])
            self.assertEqual(event["status"], "failed")

    def test_fixture_drift_and_source_change_refuse(self):
        listed = json.loads((self.root / subject.MANIFEST).read_bytes())["files"][0]["path"]
        target = self.root / listed; original = target.read_bytes()
        target.write_bytes(original + b"\n")
        with self.assertRaisesRegex(owner.Refusal, "release-fixture-drift"):
            subject.inputs(self.root)
        target.write_bytes(original)

        def change(root):
            path = root / subject.SOURCES[0]; path.write_bytes(path.read_bytes() + b"\n")
            return self.value(), 0, "a" * 64, "b" * 64

        with patch.object(subject, "execute", side_effect=change), \
                self.assertRaisesRegex(owner.Refusal, "source-changed"):
            subject.run(self.root, {"value": False, "exit": 3})

    def test_a_foreign_criterion_case_or_missing_file_row_refuses(self):
        path = self.root / subject.MANIFEST; original = json.loads(path.read_bytes())
        for change in (lambda m: m.update(criterion="authority-replay"),
                       lambda m: m.update(cases=m["cases"] + ["test_hexctl.HexctlTests.test_other"]),
                       lambda m: m.update(cases=[c for c in m["cases"]
                                                 if not c.startswith(subject.MODULES[1] + ".")]),
                       lambda m: m["files"].pop(),
                       lambda m: m.update(schema="checkpoint-authority-replay-corpus/v1")):
            manifest = json.loads(json.dumps(original)); change(manifest)
            path.write_bytes(json.dumps(manifest).encode())
            with self.subTest(manifest=sorted(manifest)), self.assertRaises(owner.Refusal):
                subject.inputs(self.root)
        path.write_bytes(json.dumps(original).encode())

    def test_the_criterion_binds_the_release_manifest_it_measured(self):
        inputs = subject.inputs(self.root)
        self.assertEqual(inputs["release_manifest"]["path"], release.MANIFEST)
        self.assertEqual(inputs["release_manifest"]["sha256"],
                         subject._hash(ROOT, release.MANIFEST))
        report = {"value": False, "exit": 3}
        with patch.object(subject, "execute", return_value=(self.value(), 0, "a" * 64, "b" * 64)):
            event = subject.run(self.root, report)
        self.assertTrue(event["complete"])
        self.assertEqual(event["criterion"], "released-interoperability")
        self.assertEqual(report["exit"], 0)
        self.assertIn("No production issuer root", event["boundary"])

    def test_the_conformance_report_and_evidence_stay_within_their_cap(self):
        report = {"value": False, "exit": 3}
        with patch.object(subject, "execute", return_value=(self.value(), 0, "a" * 64, "b" * 64)):
            event = subject.run(self.root, report)
        self.assertLessEqual(len(owner._json_bytes(event)), owner.MAX_REPORT_BYTES)
        self.assertLessEqual(len(owner._json_bytes(report)), owner.MAX_REPORT_BYTES)

    def test_an_unimplemented_criterion_never_reports_this_one_as_resolved(self):
        self.assertIn("released-interoperability", owner.CRITERIA)
        self.assertEqual(subject.CRITERION, "released-interoperability")
        self.assertEqual(demo.BUNDLE + "interoperability-manifest.json", subject.MANIFEST)


if __name__ == "__main__":
    unittest.main()
