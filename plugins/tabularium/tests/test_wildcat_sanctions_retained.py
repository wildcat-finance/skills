"""Conditional finite-input coverage, hostile custody and interruption cleanup."""

from copy import deepcopy
from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wildcat_sanctions_retained as retained
from wildcat_sanctions_fixtures import raws
from test_wildcat_v3_release import constructed_release
from tabularium_lib.core import canonical_json


class ConstructedGeneration(retained.owner.RetainedGeneration):
    """Build real raw and canonical releases from a labelled control."""

    def __init__(self, generation, control="positive"):
        super().__init__(generation, "CONSTRUCTED_" + generation.replace("-", "_"), None)
        self.control = control

    def custody(self, environ):
        return Path(tempfile.gettempdir()).resolve()

    def rebuild(self, root, output):
        output.mkdir()
        logs = raws(self.generation)
        if self.control == "absent":
            logs = [logs[0]]
        elif self.control == "missing-primary":
            logs.pop(0)
        elif self.control in ("duplicate-primary", "duplicate-companion"):
            logs.append(deepcopy(logs[0 if self.control == "duplicate-primary" else 1]))
            logs[-1]["logIndex"] = "0x20"
        elif self.control == "refusal":
            raise ValueError("private payload must never reach public diagnostics")
        elif self.control == "cancel":
            raise KeyboardInterrupt

        def replace(document, journal, plan):
            response = json.loads(journal["records"][0]["response"])
            response["result"] = logs
            journal["records"][0]["response"] = canonical_json(response).decode()
        return constructed_release(output, self.generation, replace)


def controls(control="positive"):
    return tuple(ConstructedGeneration(venue, control) for venue in ("wildcat-v1", "wildcat-v2"))


class SanctionsRetainedTests(unittest.TestCase):
    def test_real_manifest_failure_is_sanitized_and_publishes_no_report(self):
        import prove_wildcat_sanctions as proof
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            staging = base / "private-staging"
            staging.mkdir()
            (staging / "checkpoint.json").write_bytes(b"{}")
            environ = {spec.variable: str(staging) for spec in retained.GENERATIONS}
            error = io.StringIO()
            os.chdir(base)
            try:
                with mock.patch.dict(os.environ, environ), redirect_stderr(error):
                    with self.assertRaises(SystemExit) as raised:
                        proof.main(["--candidate", "unique-key", "--criterion", "retained-coverage",
                                    "--report", ".hexaemeron/refused.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("AlexandriaError", error.getvalue())
                self.assertNotIn(str(staging), error.getvalue())
                self.assertFalse((base / ".hexaemeron/refused.json").exists())
                self.assertFalse((base / ".hexaemeron/refused.observations.json").exists())
                self.assertEqual((staging / "checkpoint.json").read_bytes(), b"{}")
            finally:
                os.chdir(previous)

    def test_positive_controls_execute_each_admitted_join(self):
        made = []
        value, observed = retained.retained_conformance(controls(), environ={}, witness=made.append)
        self.assertIs(value, True)
        self.assertEqual([row["generation"] for row in observed["inputs"]], ["wildcat-v1", "wildcat-v2"])
        self.assertEqual({row["routing_coverage"] for row in observed["inputs"]}, {"joined-present-targets"})
        self.assertEqual(len(made), 1)
        self.assertFalse(made[0].exists())

    def test_verified_absence_is_distinct_from_positive_exercise(self):
        value, observed = retained.retained_conformance(controls("absent"), environ={})
        self.assertIs(value, True)
        self.assertEqual({row["routing_coverage"] for row in observed["inputs"]}, {"checked-absence"})

    def test_present_missing_and_ambiguous_targets_refuse_and_clean_up(self):
        for control in ("missing-primary", "duplicate-primary", "duplicate-companion"):
            with self.subTest(control=control):
                made = []
                with self.assertRaises(retained.EvidenceUnavailable):
                    retained.retained_conformance(controls(control), environ={}, witness=made.append)
                self.assertEqual(len(made), 1)
                self.assertFalse(made[0].exists())

    def test_every_missing_custody_variable_refuses_before_scratch(self):
        for spec in retained.GENERATIONS:
            with self.subTest(generation=spec.generation), self.assertRaisesRegex(
                    retained.EvidenceUnavailable, spec.variable + " is not set"):
                spec.custody({})
        with mock.patch.object(retained.owner, "private_scratch", side_effect=AssertionError("must not allocate")):
            with self.assertRaises(retained.EvidenceUnavailable):
                retained.retained_conformance(environ={})

    def test_link_relative_missing_and_non_directory_custody_refuse(self):
        spec = retained.GENERATIONS[0]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            (base / "file").write_bytes(b"{}")
            (base / "tree").mkdir()
            (base / "link").symlink_to(base / "tree", target_is_directory=True)
            for value in ("relative", str(base / "missing"), str(base / "file"), str(base / "link")):
                with self.subTest(value=Path(value).name), self.assertRaises(retained.EvidenceUnavailable):
                    spec.custody({spec.variable: value})

    def test_both_inventories_validate_before_any_raw_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            environ = {spec.variable: str(base) for spec in retained.GENERATIONS}
            module = mock.Mock()
            module.verify_preserved.return_value = {"manifest": {}}
            module.verify_staging_tree.side_effect = [None, ValueError("changed inventory")]
            with mock.patch.object(retained.owner, "example_module", return_value=module), \
                    mock.patch.object(retained.owner, "private_scratch", side_effect=AssertionError("must not allocate")):
                with self.assertRaises(ValueError):
                    retained.retained_conformance(environ=environ)
            module.build.assert_not_called()

    def test_refusal_interruption_and_witness_exception_remove_owned_scratch(self):
        for control, exception in (("refusal", ValueError), ("cancel", KeyboardInterrupt)):
            made = []
            with self.subTest(control=control), self.assertRaises(exception):
                retained.retained_conformance(controls(control), environ={}, witness=made.append)
            self.assertEqual(len(made), 1)
            self.assertFalse(made[0].exists())
        made = []
        def interrupt(path):
            made.append(path)
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            retained.retained_conformance(controls(), environ={}, witness=interrupt)
        self.assertFalse(made[0].exists())

    def test_public_observations_have_only_bounded_identity_outcome_fields(self):
        _, observed = retained.retained_conformance(controls(), environ={})
        for row in observed["inputs"]:
            self.assertEqual(set(row), {"generation", "raw_release_id", "raw_manifest_sha256",
                                       "canonical_sha256", "coverage_sha256", "adapter_version",
                                       "verified", "routing_coverage"})
            self.assertRegex(row["raw_release_id"], r"^sha256:[0-9a-f]{64}$")
            for key in ("raw_manifest_sha256", "canonical_sha256", "coverage_sha256"):
                self.assertRegex(row[key], r"^[0-9a-f]{64}$")
            self.assertNotIn("/", json.dumps(row))
        self.assertNotIn("0x", json.dumps(observed))

    def test_incomplete_output_and_verifier_refusal_remove_scratch(self):
        made = []
        with mock.patch.object(retained.owner, "build_wildcat_canonical", return_value=None):
            with self.assertRaises(Exception):
                retained.retained_conformance(controls(), environ={}, witness=made.append)
        self.assertFalse(made[0].exists())
        made = []
        with mock.patch.object(retained.owner.verifier, "verify", side_effect=ValueError("changed output")):
            with self.assertRaises(ValueError):
                retained.retained_conformance(controls(), environ={}, witness=made.append)
        self.assertFalse(made[0].exists())

    def test_no_reporter_subprocess_is_needed_for_real_constructed_builds(self):
        import subprocess
        with mock.patch.object(subprocess, "Popen", side_effect=AssertionError("instrumented process boundary")):
            value, _ = retained.retained_conformance(controls(), environ={})
        self.assertIs(value, True)

    def test_owned_staging_is_rechecked_after_canonical_build(self):
        class Bound(ConstructedGeneration):
            def __init__(self, generation):
                super().__init__(generation)
                self.example = "fixed-constructed-owner"
        module = mock.Mock()
        module.verify_preserved.return_value = {"manifest": {}}
        module.verify_staging_tree.side_effect = [None, None, ValueError("post-build drift")]
        made = []
        with mock.patch.object(retained.owner, "example_module", return_value=module):
            with self.assertRaisesRegex(ValueError, "post-build drift"):
                retained.retained_conformance(tuple(Bound(v) for v in ("wildcat-v1", "wildcat-v2")),
                                              environ={}, witness=made.append)
        self.assertFalse(made[0].exists())
