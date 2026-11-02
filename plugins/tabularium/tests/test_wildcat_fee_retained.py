"""Constructed fee controls exercise retained custody, vacuity and cleanup."""

from __future__ import annotations

import ast
from contextlib import redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

import prove_wildcat_fees as proof
import wildcat_fee_reports as reports
import wildcat_fee_retained as retained
from tabularium_lib.core import canonical_json
from test_wildcat_batch_retained import temporary_cwd, staging_environment, walk
from test_wildcat_v3_release import constructed_release
from wildcat_fee_fixtures import BIPS, FEES, VENUES, fee_raws
from wildcat_v3_fixtures import MARKET, log

REPORT = ".hexaemeron/design-reports/versioned-native-retained-conformance.json"
SIDECAR = REPORT.replace(".json", ".observations.json")
ARGUMENTS = ["--candidate", "versioned-native", "--criterion", "retained-conformance", "--report", REPORT]


class ConstructedGeneration(retained.RetainedGeneration):
    """Use constructed raw logs while retaining the actual canonical owners."""

    def __init__(self, generation, raws):
        super().__init__(generation, "CONSTRUCTED_FEE_CONTROL", None)
        self.raws = raws

    def custody(self, environ):
        return Path(tempfile.gettempdir()).resolve()

    def rebuild(self, root, output):
        output.mkdir()

        def mutate(document, journal, plan):
            response = json.loads(journal["records"][0]["response"])
            response["result"] = self.raws
            journal["records"][0]["response"] = canonical_json(response).decode()
            plan["release"]["name"] = self.generation + "-constructed-fee-control"

        return constructed_release(output, self.generation, mutate)


def controls(v1=None, v2=None):
    return (ConstructedGeneration(VENUES[0], fee_raws(VENUES[0]) if v1 is None else v1),
            ConstructedGeneration(VENUES[1], fee_raws(VENUES[1]) if v2 is None else v2))


def run_proof(resolver):
    with temporary_cwd() as root, mock.patch.dict(reports.CONFORMANCE, {
            ("versioned-native", "retained-conformance"): resolver}), redirect_stderr(io.StringIO()) as error:
        try:
            status = proof.main(ARGUMENTS)
        except SystemExit as raised:
            status = raised.code
        files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
        report = json.loads((root / REPORT).read_bytes()) if (root / REPORT).is_file() else None
        sidecar = json.loads((root / SIDECAR).read_bytes()) if (root / SIDECAR).is_file() else None
    return status, report, sidecar, files, error.getvalue()


class FeeRetainedTests(unittest.TestCase):
    def test_constructed_targets_pass_and_remove_scratch(self):
        made = []
        status, report, sidecar, files, _ = run_proof(retained.retained_resolver(controls(), made.append))
        self.assertEqual((status, report["value"], report["exit"]), (0, True, 0))
        self.assertEqual(sidecar["observations"]["passed_generations"], list(VENUES))
        self.assertEqual(files, [REPORT, SIDECAR])
        self.assertEqual(len(made), 1)
        self.assertFalse(made[0].exists())

    def test_absent_v1_collection_and_v2_update_do_not_require_invented_positives(self):
        value, observations = retained.retained_conformance(
            controls(v1=[], v2=[log(FEES, (), (73,), MARKET, 0)]), environ={})
        self.assertIs(value, True)
        self.assertEqual(observations["passed_generations"], list(VENUES))

    def test_all_empty_or_only_state_update_refuses_without_report_or_scratch(self):
        for v2 in ([], [log(BIPS, (), (125,), MARKET, 0)]):
            made = []
            status, report, sidecar, files, error = run_proof(
                retained.retained_resolver(controls(v1=[], v2=v2), made.append))
            self.assertEqual((status, report, sidecar, files), (2, None, None, []))
            self.assertIn("wildcat-v2 maps no fee collection", error)
            self.assertFalse(made[0].exists())

    def test_v1_collection_alone_cannot_replace_actual_v2_collection(self):
        with self.assertRaisesRegex(retained.EvidenceUnavailable, "wildcat-v2 maps no fee collection"):
            retained.retained_conformance(controls(v2=[]), environ={})

    def test_public_observations_have_only_release_identifiers_digests_and_outcomes(self):
        status, report, sidecar, _, _ = run_proof(retained.retained_resolver(controls()))
        self.assertEqual(status, 0)
        self.assertEqual(set(report), {"schema", "candidate", "criterion", "value", "unit", "command", "exit"})
        observations = sidecar["observations"]
        self.assertEqual(set(observations), {"inputs", "passed_generations"})
        self.assertEqual([item["generation"] for item in observations["inputs"]], list(VENUES))
        for item in observations["inputs"]:
            self.assertEqual(set(item), {"generation", "raw_release_id", "canonical_sha256", "coverage_sha256"})
            self.assertRegex(item["raw_release_id"], r"^sha256:[0-9a-f]{64}$")
            for key in ("canonical_sha256", "coverage_sha256"):
                self.assertRegex(item[key], r"^[0-9a-f]{64}$")
        for value in walk(observations):
            self.assertIsInstance(value, str)
            self.assertNotIn("/", value)
            self.assertNotRegex(value, r"0x[0-9a-fA-F]{40}")
            self.assertNotIn(value, (FEES, BIPS))
            self.assertFalse(value.isdigit())

    def test_missing_custody_refuses_before_scratch_and_never_prints_a_path(self):
        made = []
        with staging_environment():
            status, report, sidecar, files, error = run_proof(retained.retained_resolver(witness=made.append))
        self.assertEqual((status, report, sidecar, files, made), (2, None, None, [], []))
        self.assertIn("ALEXANDRIA_WILDCAT_V1_STAGING is not set", error)

    def test_unreadable_linked_relative_and_non_directory_custody_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "tree").mkdir(); (root / "file").write_bytes(b"file")
            (root / "link").symlink_to(root / "tree", target_is_directory=True)
            for value, reason in ((str(root / "absent"), "names an unreadable path"),
                                  (str(root / "file"), "names no directory"),
                                  (str(root / "link"), "names a symlink"),
                                  ("relative", "must name an absolute path")):
                with self.subTest(reason=reason), self.assertRaisesRegex(retained.EvidenceUnavailable, reason):
                    retained.retained_conformance(environ={"ALEXANDRIA_WILDCAT_V1_STAGING": value})
            with mock.patch("wildcat_batch_retained.os.access", return_value=False):
                with self.assertRaisesRegex(retained.EvidenceUnavailable, "names an unreadable directory"):
                    retained.retained_conformance(environ={"ALEXANDRIA_WILDCAT_V1_STAGING": str(root / "tree")})

    def test_changed_staging_inventory_refuses_and_cleans_scratch(self):
        with tempfile.TemporaryDirectory() as temporary:
            tree = Path(temporary).resolve()
            (tree / "checkpoint.json").write_bytes(b"{}")
            made = []
            with staging_environment(ALEXANDRIA_WILDCAT_V1_STAGING=str(tree), ALEXANDRIA_WILDCAT_V2_STAGING=str(tree)):
                status, report, sidecar, files, error = run_proof(retained.retained_resolver(witness=made.append))
            self.assertEqual((status, report, sidecar, files), (2, None, None, []))
            self.assertNotIn(str(tree), error)
            self.assertFalse(made[0].exists())

    def test_interrupted_rebuild_and_witness_remove_scratch(self):
        for boundary in ("rebuild", "witness"):
            made = []

            def interrupted(path):
                made.append(path)
                if boundary == "witness":
                    raise KeyboardInterrupt

            with self.subTest(boundary=boundary), mock.patch.object(
                    ConstructedGeneration, "rebuild", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
                retained.retained_conformance(controls(), environ={}, witness=interrupted)
            self.assertEqual(len(made), 1)
            self.assertFalse(made[0].exists())

    def test_unknown_adapter_version_refuses_and_cleans_scratch(self):
        made = []
        with mock.patch.object(retained, "ADAPTER_VERSION", "unknown"):
            status, report, sidecar, files, _ = run_proof(retained.retained_resolver(controls(), made.append))
        self.assertEqual((status, report, sidecar, files), (2, None, None, []))
        self.assertFalse(made[0].exists())

    def test_interrupted_build_removes_its_partial_output(self):
        made = []

        def interrupted(raw, target, release, version):
            target.mkdir()
            (target / "coverage.json").write_bytes(b"partial")
            raise KeyboardInterrupt

        with mock.patch.object(retained, "build_wildcat_canonical", side_effect=interrupted), \
                self.assertRaises(KeyboardInterrupt):
            retained.retained_conformance(controls(), environ={}, witness=made.append)
        self.assertEqual(len(made), 1)
        self.assertFalse(made[0].exists())

    def test_altered_generated_output_yields_false_and_cleans_scratch(self):
        build = retained.build_wildcat_canonical

        def altered(raw, target, release, version):
            build(raw, target, release, version)
            (target / "events.jsonl").write_bytes(b"{}\n")

        made = []
        with mock.patch.object(retained, "build_wildcat_canonical", side_effect=altered):
            status, report, sidecar, _, _ = run_proof(retained.retained_resolver(controls(), made.append))
        self.assertEqual((status, report["value"], report["exit"]), (1, False, 1))
        self.assertEqual(sidecar["observations"]["passed_generations"], [])
        self.assertFalse(made[0].exists())

    def test_present_targets_require_exact_fee_rows_and_supported_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            raw = controls()[1].rebuild(root, root / "raw")
            target = root / "canonical"
            retained.build_wildcat_canonical(raw, target, "constructed-fee-check", "1.1.0")
            source = retained.document(target / "source.json")
            coverage = retained.document(target / "coverage.json")
            events = retained.event_rows(target / "events.jsonl")
        self.assertTrue(retained.release_conforms("wildcat-v2", source, coverage, events))
        for change in ("version", "unsupported-signature", "unsupported-topic", "disposition", "rule", "party",
                       "amount", "family", "join", "duplicate-row", "missing-row"):
            s, c, rows = deepcopy(source), deepcopy(coverage), deepcopy(events)
            record = next(r for r in s["mapping_records"] if r["signature"] == FEES)
            row = next(r for r in rows if r["action"].endswith(".fees-collected"))
            if change == "version": c["versions"]["adapter"]["version"] = "1.0.0"
            elif change == "unsupported-signature": c["coverage"]["unsupported_events"]["canonical:market:" + FEES] = 1
            elif change == "unsupported-topic": c["coverage"]["unsupported_events"]["decode:market:" + sorted(retained.TARGET_TOPICS)[0]] = 1
            elif change == "disposition": record["disposition"] = "unsupported-canonical-meaning"
            elif change == "rule": row["provenance"]["mapping_rule"] = "wildcat-v2.debt-repaid.v1"
            elif change == "party": row["parties"][0]["role"] = "recipient"
            elif change == "amount": row["amounts"][0]["base_units"] = "74"
            elif change == "family": row["event_family"] = "repayment"
            elif change == "join": record["join"] = {}
            elif change == "duplicate-row": rows.append(deepcopy(row))
            elif change == "missing-row": rows.remove(row)
            with self.subTest(change=change):
                self.assertFalse(retained.release_conforms("wildcat-v2", s, c, rows))

    def test_a_single_failing_generation_does_not_claim_both_passed(self):
        check = retained.release_conforms
        with mock.patch.object(retained, "release_conforms", side_effect=lambda generation, *args:
                               generation != "wildcat-v2" and check(generation, *args)):
            value, observations = retained.retained_conformance(controls(), environ={})
        self.assertIs(value, False)
        self.assertEqual(observations["passed_generations"], ["wildcat-v1"])

    def test_incomplete_or_reordered_generation_set_refuses(self):
        for generations in ((), controls()[:1], tuple(reversed(controls()))):
            with self.assertRaisesRegex(retained.EvidenceUnavailable, "both ordered Wildcat generations are required"):
                retained.retained_conformance(generations, environ={})

    def test_scratch_inside_repository_refuses_before_creation(self):
        with mock.patch("wildcat_batch_retained.tempfile.gettempdir", return_value=str(HERE.parents[2])):
            with self.assertRaisesRegex(retained.EvidenceUnavailable, "temporary directory lies inside the repository"):
                retained.retained_conformance(controls(), environ={})

    def test_dispatch_is_exact_and_retained_execution_launches_no_child(self):
        self.assertEqual(reports.STEP_CASES[3], (("test_wildcat_fee_retained", "FeeRetainedTests"),
                         ("test_wildcat_fees", "FeeLegacyTests"), ("test_wildcat_fees", "FeePublicTests")))
        self.assertIn(("versioned-native", "retained-conformance"), reports.CONFORMANCE)
        tree = ast.parse((HERE / "wildcat_fee_retained.py").read_bytes())
        imports = {(getattr(node, "module", None) or alias.name).split(".")[0]
                   for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
        self.assertNotIn("subprocess", imports)
        calls = {node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {"system", "popen", "fork", "spawn", "execv", "execve", "run", "Popen", "discover"})


if __name__ == "__main__":
    unittest.main()
