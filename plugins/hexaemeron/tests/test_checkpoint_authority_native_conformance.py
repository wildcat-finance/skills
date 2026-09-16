"""Conformance never accepts stale, incomplete or unrelated native evidence."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from checkpoint_authority_native_fixture import fixture
from checkpoint_authority import conformance as owner, native_conformance as subject, native_io
from checkpoint_authority.native import LAYOUT_SHA256
from checkpoint_authority.native_records import NATIVE_COMMIT

ROOT = Path(__file__).resolve().parents[3]


class NativeConformanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        for path in (*subject.SOURCES, *subject.FILES, subject.MANIFEST):
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        self.cases = subject.inputs(self.root)["cases"]

    def value(self):
        expected = fixture()
        stages = [{"stage": name, "attempt_id": "native-positive", "input_sha256": expected["outer_sha256"],
            "exit": 0, "output_sha256": "a" * 64, "log_sha256": "b" * 64,
            "output_bytes": 1, "log_bytes": 0, "duration_ms": 1} for name in ("inspect", "restore", "verify", "identity")]
        return {"schema": "checkpoint-authority-native-execution/v1", "complete": True, "passed": True,
            "tests_run": len(self.cases), "subtests_run": 0, "started": self.cases[:], "completed": self.cases[:],
            "failure_cases": [], "error_cases": [], "failures": 0, "errors": 0, "skips": 0,
            "expected_failures": 0, "unexpected_successes": 0, "output_sha256": "c" * 64,
            "python": sys.version.split()[0], "native": {"result_sha256": "d" * 64,
            "source_profile_sha256": LAYOUT_SHA256, "source_commit": NATIVE_COMMIT, "native_results": stages,
            "required": sorted(expected["required"]), "historical_required": sorted(expected["historical_required"]),
            "verified_count": 4, "capability_sha256": hashlib.sha256((self.root / subject.FILES[0]).read_bytes()).hexdigest()}}

    def execute(self, value):
        result = native_io.Execution(subject.CRITERION, "native-conformance", "a" * 64, 0,
            json.dumps(value).encode(), b"", 1)
        with patch.object(native_io, "execute", return_value=result): return subject.execute(self.root)

    def test_manifest_is_owned_and_has_all_thirty_five_hostile_cases(self):
        from checkpoint_authority_native_corpus import value
        self.assertEqual(json.loads((ROOT / subject.MANIFEST).read_bytes()), value(ROOT))
        self.assertEqual(sum(case.startswith("test_hexctl_checkpoint_archive.") for case in self.cases), 35)

    def test_capability_maps_twenty_four_names_to_real_stages(self):
        capability = json.loads((ROOT / subject.FILES[0]).read_bytes())
        self.assertEqual(len(capability["fixtures"]), 35)
        self.assertEqual(len({row["id"] for row in capability["fixtures"]}), 35)
        self.assertEqual(len(capability["refusals"]), 24)
        mapping = {row["name"]:row for row in capability["refusals"]}
        self.assertEqual(mapping["destination-occupied"]["stages"], ["restore"])
        for name in ("boundary-occupied", "boundary-unaccepted", "worktree-dirty", "signature-format-unsupported", "identity-unavailable"):
            self.assertEqual(mapping[name]["stages"], ["producer"])
        self.assertEqual(mapping["bundle-oversized"]["stages"], ["producer", "inspect"])
        self.assertFalse(capability["coverage"]["all_refusals_from_inspect"])
        self.assertEqual({row["issue"] for row in capability["open_native_obligations"]}, {1647,1648,1649})
        for row in capability["fixtures"]:
            self.assertEqual(row["native_stage"], "inspect")
            self.assertIn(row["id"], mapping[row["asserted_refusal"]]["hostile_fixture_ids"])

    def test_valid_execution_shape_preserves_all_stage_bindings(self):
        self.assertEqual(self.execute(self.value())[0], self.value())

    def test_multiple_native_attempts_share_the_declared_check_budget(self):
        report = native_io.Execution(subject.CRITERION, "native-conformance", "a" * 64, 0,
            json.dumps(self.value()).encode(), b"", 1)
        def run(*args, **kwargs):
            # One criterion includes two native attempts plus the hostile corpus.
            if kwargs["deadline"] < 1800:
                from checkpoint_authority.canonical import Refusal
                raise Refusal("native-deadline", subject.CRITERION)
            return report
        with patch.object(subject.time, "monotonic", return_value=0), patch.object(native_io, "execute", side_effect=run):
            self.assertEqual(subject.execute(self.root)[1], 0)

    def test_malformed_native_shapes_and_swapped_stage_inputs_refuse(self):
        for mutate in (lambda v: v["native"]["native_results"][0].update(attempt_id="stale"),
                lambda v: v["native"]["native_results"][0].update(input_sha256="f"*64),
                lambda v: v["native"]["native_results"][1].update(stage="verify"),
                lambda v: v["native"]["native_results"][1].update(exit=True),
                lambda v: v["native"]["native_results"][1].update(output_sha256="bad"),
                lambda v: v["native"].update(verified_count=True),
                lambda v: v["native"].update(source_profile_sha256="f"*64),
                lambda v: v["native"].update(required=v["native"]["required"][:-1])):
            value = self.value(); mutate(value)
            with self.subTest(value=value["native"]), self.assertRaises(owner.Refusal): self.execute(value)

    def test_partial_duplicate_and_skipped_execution_never_passes_criterion(self):
        for mutate in (lambda v:v.update(complete=False), lambda v:v.update(native=None),
                lambda v:v.update(tests_run=0), lambda v:v.update(skips=1),
                lambda v:v.update(completed=v["completed"][:-1]),
                lambda v:v.update(started=v["started"][:-1]+v["started"][:1])):
            value=self.value(); mutate(value); report={"value":False,"exit":3}
            with patch.object(subject,"execute",return_value=(value,0,"a"*64,"b"*64)):
                event=subject.run(self.root,report)
            self.assertFalse(report["value"]); self.assertFalse(event["complete"])

    def test_fixture_drift_and_source_change_refuse(self):
        target = self.root / subject.FILES[1]; target.write_bytes(target.read_bytes()+b"x")
        with self.assertRaises(owner.Refusal): subject.inputs(self.root)
        target.write_bytes((ROOT / subject.FILES[1]).read_bytes())
        def change(root):
            path=root/subject.SOURCES[0]; path.write_bytes(path.read_bytes()+b"\n")
            return self.value(),0,"a"*64,"b"*64
        with patch.object(subject,"execute",side_effect=change), self.assertRaises(owner.Refusal):
            subject.run(self.root,{"value":False,"exit":3})


if __name__ == "__main__": unittest.main()
