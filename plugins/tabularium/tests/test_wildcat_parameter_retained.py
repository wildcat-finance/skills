"""Constructed retained controls, custody refusals and bounded public reports."""

from contextlib import redirect_stderr
from copy import deepcopy
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
sys.path.insert(0, str(HERE.parent / "scripts"))
import prove_wildcat_parameters as proof
import wildcat_parameter_reports as reports
import wildcat_parameter_retained as retained
from test_wildcat_parameter_scaffold import temporary_cwd
from wildcat_parameter_fixtures import inputs, raw_release
from wildcat_v3_fixtures import record
from tabularium_lib.core import canonical_json
from tabularium_lib.wildcat_rows import map_records

VENUES = ("wildcat-v1", "wildcat-v2")
REPORT = ".hexaemeron/retained.json"
SIDECAR = ".hexaemeron/retained.observations.json"
ARGS = ["--candidate", "native-fields", "--criterion", "retained-conformance", "--report", REPORT]


class ConstructedGeneration(retained.RetainedGeneration):
    def __init__(self, generation, group="required"):
        super().__init__(generation, "CONSTRUCTED_CONTROL", None)
        self.group = group

    def custody(self, environ):
        return Path(tempfile.gettempdir()).resolve()

    def rebuild(self, root, output):
        output.mkdir()
        if self.group == "required":
            return raw_release(output, self.generation)
        from test_wildcat_v3_release import constructed_release
        contexts, records, _ = inputs(self.generation, self.group)

        def replace(document, journal, plan):
            document["contexts"] = [{"address": address, **{k: context[k] for k in
                                    ("role", "asset", "market", "abi_variant", "concrete_contract")}}
                                   for address, context in sorted(contexts.items())]
            response = json.loads(journal["records"][0]["response"])
            response["result"] = [raw for raw, _ in records]
            request = json.loads(journal["records"][0]["request"])
            request["params"][0]["address"] = sorted(contexts)
            journal["records"][0].update(request=canonical_json(request).decode(), response=canonical_json(response).decode())
            for capture in plan["captures"]:
                capture["scope"]["subjects"] = ["eip155:1:" + address for address in sorted(contexts)]
            plan["release"]["name"] = self.generation + "-constructed-final"
        return constructed_release(output, self.generation, replace)


def controls():
    return tuple(ConstructedGeneration(venue) for venue in VENUES)


def run_proof(resolver):
    with temporary_cwd() as root, redirect_stderr(io.StringIO()) as error, \
            mock.patch.dict(reports.CONFORMANCE, {("native-fields", "retained-conformance"): resolver}):
        try:
            status = proof.main(ARGS)
        except SystemExit as raised:
            status = raised.code
        files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
        payload = json.loads((root / REPORT).read_bytes()) if (root / REPORT).is_file() else None
        sidecar = json.loads((root / SIDECAR).read_bytes()) if (root / SIDECAR).is_file() else None
    return status, payload, sidecar, files, error.getvalue()


class ParameterRetainedTests(unittest.TestCase):
    def test_constructed_controls_build_verify_and_clean_both_generations(self):
        made, private = [], []
        value, observed = retained.retained_conformance(controls(), {}, made.append, private.append)
        self.assertTrue(value)
        self.assertEqual(len(made), 1)
        self.assertFalse(made[0].exists())
        self.assertEqual([row["generation"] for row in observed["inputs"]], list(VENUES))
        self.assertTrue(all(row["passed"] for row in observed["inputs"]))
        self.assertEqual(len(private), 2)
        for inventory in private:
            self.assertEqual(inventory["qualification"], "absence from these retained inputs only")
            self.assertTrue(all(row["present"] for row in inventory["declarations"] if row["required"]))
            self.assertTrue(all(not row["present"] for row in inventory["declarations"] if not row["required"]))

    def test_public_sidecar_contains_only_release_id_digests_and_booleans(self):
        status, payload, sidecar, files, _ = run_proof(retained.retained_resolver(controls()))
        self.assertEqual((status, payload["value"], payload["exit"]), (0, True, 0))
        self.assertEqual(files, [REPORT, SIDECAR])
        self.assertEqual(set(sidecar["observations"]), {"inputs"})
        for row in sidecar["observations"]["inputs"]:
            self.assertEqual(set(row), {"generation", "raw_release_id", "canonical_sha256",
                                        "coverage_sha256", "inventory_sha256", "passed"})
            self.assertIn(row["generation"], VENUES)
            self.assertIs(row["passed"], True)
            self.assertRegex(row["raw_release_id"], r"^sha256:[0-9a-f]{64}$")
            for key in ("canonical_sha256", "coverage_sha256", "inventory_sha256"):
                self.assertRegex(row[key], r"^[0-9a-f]{64}$")
        encoded = json.dumps(sidecar)
        self.assertNotIn("/private/", encoded)
        self.assertNotIn("signature", encoded)
        self.assertNotRegex(encoded, r"0x[0-9a-fA-F]{40}")

    def test_published_retained_observations_have_the_closed_private_safe_shape(self):
        bundle = HERE.parents[2] / "docs/kickoff/2090"
        sidecar = json.loads((bundle / "retained-observations.json").read_bytes())
        self.assertEqual(set(sidecar), {"schema", "candidate", "criterion", "observations"})
        self.assertEqual((sidecar["schema"], sidecar["candidate"], sidecar["criterion"]),
                         (reports.OBSERVATIONS_SCHEMA, "native-fields", "retained-conformance"))
        self.assertEqual(set(sidecar["observations"]), {"inputs"})
        self.assertEqual([item["generation"] for item in sidecar["observations"]["inputs"]], list(VENUES))
        for row in sidecar["observations"]["inputs"]:
            self.assertEqual(set(row), {"generation", "raw_release_id", "canonical_sha256",
                                        "coverage_sha256", "inventory_sha256", "passed"})
            self.assertRegex(row["raw_release_id"], r"^sha256:[0-9a-f]{64}$")
            for field in ("canonical_sha256", "coverage_sha256", "inventory_sha256"):
                self.assertRegex(row[field], r"^[0-9a-f]{64}$")
            self.assertIs(type(row["passed"]), bool)

    def test_missing_custody_refuses_before_scratch_and_writes_no_report(self):
        variables = {spec.variable for spec in retained.GENERATIONS}
        with mock.patch.dict(os.environ, {k: v for k, v in os.environ.items() if k not in variables}, clear=True):
            made = []
            status, payload, sidecar, files, error = run_proof(retained.retained_resolver(witness=made.append))
        self.assertEqual((status, payload, sidecar, files, made), (2, None, None, [], []))
        self.assertIn("ALEXANDRIA_WILDCAT_V1_STAGING is not set", error)

    def test_linked_staging_ancestor_is_refused_without_revealing_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); (base / "tree/child").mkdir(parents=True)
            (base / "link").symlink_to(base / "tree", target_is_directory=True)
            spec = retained.GENERATIONS[0]
            with self.assertRaises(retained.EvidenceUnavailable) as raised:
                spec.custody({spec.variable: str(base / "link/child")})
            self.assertEqual(str(raised.exception), spec.variable + " names a linked ancestor")

    def test_staging_leaf_shape_and_permissions_refuse_by_variable(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            (base / "file").write_bytes(b"preserved")
            (base / "tree").mkdir()
            (base / "link").symlink_to(base / "tree", target_is_directory=True)
            (base / "closed").mkdir(); os.chmod(base / "closed", 0)
            spec = retained.GENERATIONS[1]
            try:
                for value, reason in (("relative", "must name an absolute path"),
                                      (str(base / "absent"), "names an unreadable path"),
                                      (str(base / "file"), "names no directory"),
                                      (str(base / "link"), "names a symlink"),
                                      (str(base / "closed"), "names an unreadable directory")):
                    with self.subTest(reason=reason), self.assertRaises(retained.EvidenceUnavailable) as raised:
                        spec.custody({spec.variable: value})
                    self.assertEqual(str(raised.exception), spec.variable + " " + reason)
            finally:
                os.chmod(base / "closed", 0o700)

    def test_changed_staging_manifest_refuses_and_removes_scratch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); (root / "checkpoint.json").write_bytes(b"{}")
            environ = {spec.variable: str(root) for spec in retained.GENERATIONS}
            made = []
            with self.assertRaises(Exception):
                retained.retained_conformance(environ=environ, witness=made.append)
            self.assertEqual(len(made), 1)
            self.assertFalse(made[0].exists())

    def test_generation_without_required_target_refuses_and_cleans(self):
        for venue in VENUES:
            made = []
            specs = tuple(ConstructedGeneration(item, "last_group" if item == venue else "required")
                          for item in VENUES)
            status, payload, sidecar, files, error = run_proof(retained.retained_resolver(specs, made.append))
            self.assertEqual((status, payload, sidecar, files), (2, None, None, []))
            self.assertIn(venue + " maps no required parameter target", error)
            self.assertFalse(made[0].exists())
        with self.assertRaises(retained.EvidenceUnavailable):
            retained.retained_conformance((), {})

    def test_rebuild_interruption_and_callback_failure_remove_scratch(self):
        for interruption in (RuntimeError("private detail"), KeyboardInterrupt()):
            made = []
            with self.subTest(kind=type(interruption).__name__), \
                    mock.patch.object(ConstructedGeneration, "rebuild", side_effect=interruption):
                with self.assertRaises(type(interruption)):
                    retained.retained_conformance(controls(), {}, made.append)
            self.assertEqual(len(made), 1)
            self.assertFalse(made[0].exists())
        made = []
        with self.assertRaises(RuntimeError):
            retained.retained_conformance(controls(), {}, made.append,
                                         lambda inventory: (_ for _ in ()).throw(RuntimeError("private detail")))
        self.assertFalse(made[0].exists())

    def test_hostile_or_occupied_outputs_refuse_before_retained_work(self):
        for kind in ("occupied", "sidecar", "linked"):
            resolver = mock.Mock()
            with self.subTest(kind=kind), temporary_cwd() as root, redirect_stderr(io.StringIO()), \
                    mock.patch.dict(reports.CONFORMANCE, {("native-fields", "retained-conformance"): resolver}):
                (root / ".hexaemeron").mkdir()
                target = root / (SIDECAR if kind == "sidecar" else REPORT)
                if kind == "linked": target.symlink_to(root / "absent")
                else: target.write_bytes(b"preserved")
                with self.assertRaises(SystemExit) as raised: proof.main(ARGS)
                self.assertEqual(raised.exception.code, 2)
                resolver.assert_not_called()
                if kind != "linked": self.assertEqual(target.read_bytes(), b"preserved")

    def test_private_scratch_and_witness_refusals_leave_no_release(self):
        from wildcat_batch_retained import REPO
        with mock.patch("wildcat_batch_retained.tempfile.gettempdir", return_value=str(REPO)):
            with self.assertRaises(retained.EvidenceUnavailable):
                retained.retained_conformance(controls(), {})
        made = []
        def refusing_witness(path):
            made.append(path)
            raise RuntimeError("private witness detail")
        with self.assertRaises(RuntimeError):
            retained.retained_conformance(controls(), {}, refusing_witness)
        self.assertFalse(made[0].exists())

    def test_failed_verification_returns_false_and_cleans(self):
        made = []
        with mock.patch.object(retained, "verified", return_value=False):
            status, payload, sidecar, _, _ = run_proof(retained.retained_resolver(controls(), made.append))
        self.assertEqual((status, payload["value"], payload["exit"]), (1, False, 1))
        self.assertTrue(all(not row["passed"] for row in sidecar["observations"]["inputs"]))
        self.assertFalse(made[0].exists())

    def test_required_mapping_and_final_group_predicate_reject_changed_dispositions(self):
        for venue in VENUES:
            contexts, raws, _ = inputs(venue)
            mapped = map_records(venue, contexts, raws, "1.2.0")
            source = {"mapping_records": list(mapped["mapping_records"])}
            events = list(mapped["events"])
            self.assertTrue(retained.release_conforms(venue, source, events))
            for change in ("missing-row", "wrong-action", "amount", "wrong-rule", "wrong-version", "decoded", "disposition"):
                altered, rows = deepcopy(source), deepcopy(events)
                if change == "missing-row": rows.pop()
                elif change == "wrong-action": rows[0]["action"] = venue + ".borrow"
                elif change == "amount": rows[0]["amounts"] = [{}]
                elif change == "wrong-rule": rows[0]["provenance"]["mapping_rule"] = "unknown"
                elif change == "wrong-version": rows[0]["provenance"]["adapter_version"] = "1.0.0"
                elif change == "decoded": altered["mapping_records"][0]["decoded"]["invented"] = "7"
                else: altered["mapping_records"][0]["disposition"] = "supporting"
                with self.subTest(venue=venue, change=change):
                    self.assertFalse(retained.release_conforms(venue, altered, rows))
            contexts, raws, _ = inputs(venue, "last_group")
            mapped = map_records(venue, contexts, raws, "1.2.0")
            source = {"mapping_records": list(mapped["mapping_records"])}
            self.assertTrue(retained.release_conforms(venue, source, []))
            for field, value in (("limitations", ["generic"]), ("disposition", "primary")):
                altered = deepcopy(source); altered["mapping_records"][0][field] = value
                self.assertFalse(retained.release_conforms(venue, altered, []))

    def test_bound_entrypoint_registration_and_no_child_execution(self):
        self.assertEqual(reports.STEP_CASES[3][0], ("test_wildcat_parameter_retained", "ParameterRetainedTests"))
        with mock.patch("subprocess.Popen", side_effect=AssertionError("child creation")) as child:
            result, _ = retained.retained_conformance(controls(), {})
        self.assertTrue(result)
        child.assert_not_called()


if __name__ == "__main__":
    unittest.main()
