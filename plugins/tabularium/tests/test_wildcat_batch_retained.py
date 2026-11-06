"""Hold the retained-conformance resolver to constructed controls and named custody refusals.

Ordinary discovery needs no retained capture: the controls are built from the
constructed batch transactions, and the custody cases point the two staging
variables at absent, unreadable, linked or manifest-failing trees.
"""

from __future__ import annotations

import ast
from contextlib import contextmanager, redirect_stderr
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "scripts"))

import prove_wildcat_batches as proof
import wildcat_batch_reports as reports
import wildcat_batch_retained as retained
from tabularium_lib.core import canonical_json
from test_wildcat_v3_release import constructed_release
from wildcat_batch_fixtures import HOSTILE_SPECIMENS, raws_for
from wildcat_batch_public_fixtures import SOURCE_ORDER, TRANSACTIONS, VENUES
from wildcat_v3_fixtures import ACCOUNT, MARKET

REPORT = ".hexaemeron/design-reports/adjacent-burn-retained-conformance.json"
SIDECAR = ".hexaemeron/design-reports/adjacent-burn-retained-conformance.observations.json"
ARGUMENTS = ["--candidate", "adjacent-burn", "--criterion", "retained-conformance", "--report", REPORT]
DESIGN_REPORT_KEYS = {"schema", "candidate", "criterion", "value", "unit", "command", "exit"}
INPUT_KEYS = {"generation", "raw_release_id", "canonical_sha256", "coverage_sha256"}
STAGING_VARIABLES = tuple(spec.variable for spec in retained.GENERATIONS)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


@contextmanager
def temporary_cwd():
    old = Path.cwd()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary).resolve()
        os.chdir(root)
        try:
            yield root
        finally:
            os.chdir(old)


@contextmanager
def staging_environment(**values):
    """The process environment with only the two staging variables changed."""
    environ = {key: value for key, value in os.environ.items() if key not in STAGING_VARIABLES}
    environ.update(values)
    with mock.patch.dict(os.environ, environ, clear=True):
        yield


class ConstructedGeneration(retained.RetainedGeneration):
    """A control built from constructed transactions; it needs no staging tree."""

    def __init__(self, generation, transactions):
        super().__init__(generation, "CONSTRUCTED_CONTROL_" + generation.upper().replace("-", "_"), None)
        self.transactions = transactions

    def custody(self, environ):
        return Path(tempfile.gettempdir()).resolve()

    def rebuild(self, root, output):
        output.mkdir()
        raws = raws_for(self.transactions)

        def replace_logs(document, journal, plan):
            response = json.loads(journal["records"][0]["response"])
            response["result"] = raws
            journal["records"][0]["response"] = canonical_json(response).decode()
            plan["release"]["name"] = self.generation + "-constructed-control"

        return constructed_release(output, self.generation, replace_logs)


class RefusingGeneration(retained.RetainedGeneration):
    """Custody passes; the rebuild refuses the way a failing staging tree does."""

    def __init__(self, generation):
        super().__init__(generation, "CONSTRUCTED_REFUSAL_" + generation.upper().replace("-", "_"), None)

    def custody(self, environ):
        return Path(tempfile.gettempdir()).resolve()

    def rebuild(self, root, output):
        raise ValueError("the staging tree lacks files the manifest lists")


def source_order(venue, *extra):
    return [TRANSACTIONS[name] for name in SOURCE_ORDER[venue]] + [HOSTILE_SPECIMENS[name] for name in extra]


def controls(*extra):
    return tuple(ConstructedGeneration(venue, source_order(venue, *extra)) for venue in VENUES)


def run_proof(resolver):
    """Run the registered proof interface against one resolver in a fresh worktree."""
    with temporary_cwd() as root, mock.patch.dict(reports.CONFORMANCE, {
            ("adjacent-burn", "retained-conformance"): resolver}), redirect_stderr(io.StringIO()) as error:
        try:
            status = proof.main(ARGUMENTS)
        except SystemExit as raised:
            status = raised.code
        files = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
        report = json.loads((root / REPORT).read_bytes()) if (root / REPORT).is_file() else None
        sidecar = json.loads((root / SIDECAR).read_bytes()) if (root / SIDECAR).is_file() else None
    return status, report, sidecar, files, error.getvalue()


def walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)
    else:
        yield value


class BatchRetainedTests(unittest.TestCase):
    """Constructed controls, custody refusals, report shape and scratch removal."""

    def test_absent_staging_variable_refuses_by_name_with_exit_2_and_no_report(self):
        for present in ((), ("ALEXANDRIA_WILDCAT_V1_STAGING",)):
            with self.subTest(present=present), tempfile.TemporaryDirectory() as temporary, \
                    staging_environment(**{name: str(Path(temporary).resolve()) for name in present}):
                absent = next(name for name in STAGING_VARIABLES if name not in present)
                status, report, sidecar, files, error = run_proof(reports.CONFORMANCE[
                    ("adjacent-burn", "retained-conformance")])
                self.assertEqual((status, report, sidecar, files), (2, None, None, []))
                self.assertIn("EvidenceUnavailable", error)
                self.assertIn(absent + " is not set", error)
                self.assertNotIn(temporary, error)

    def test_unreadable_linked_or_non_directory_staging_path_refuses_by_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            (base / "file").write_bytes(b"not a tree")
            (base / "tree").mkdir()
            (base / "link").symlink_to(base / "tree", target_is_directory=True)
            (base / "closed").mkdir()
            os.chmod(base / "closed", 0)
            try:
                for name, reason in (("missing", "names an unreadable path"), ("file", "names no directory"),
                                     ("link", "names a symlink"), ("closed", "names an unreadable directory"),
                                     ("relative", "must name an absolute path")):
                    value = "tree/relative" if name == "relative" else str(base / name)
                    with self.subTest(name=name), staging_environment(
                            ALEXANDRIA_WILDCAT_V1_STAGING=str(base / "tree"), ALEXANDRIA_WILDCAT_V2_STAGING=value):
                        made = []
                        with self.assertRaises(retained.EvidenceUnavailable) as raised:
                            retained.retained_conformance(witness=made.append)
                        self.assertEqual(str(raised.exception), "ALEXANDRIA_WILDCAT_V2_STAGING " + reason)
                        self.assertEqual(made, [])
            finally:
                os.chmod(base / "closed", 0o700)

    def test_staging_tree_failing_its_manifest_refuses_and_removes_the_scratch(self):
        with tempfile.TemporaryDirectory() as temporary:
            tree = Path(temporary).resolve() / "staging"
            tree.mkdir()
            (tree / "checkpoint.json").write_bytes(b"{}")
            made = []
            with staging_environment(ALEXANDRIA_WILDCAT_V1_STAGING=str(tree), ALEXANDRIA_WILDCAT_V2_STAGING=str(tree)):
                status, report, sidecar, files, error = run_proof(retained.retained_resolver(witness=made.append))
            self.assertEqual((status, report, sidecar, files), (2, None, None, []))
            self.assertIn("conformance unavailable: AlexandriaError", error)
            self.assertNotIn(str(tree), error)
            self.assertEqual(len(made), 1)
            self.assertFalse(made[0].exists())

    def test_source_order_controls_pass_on_both_generations(self):
        made = []
        status, report, sidecar, files, error = run_proof(retained.retained_resolver(controls(), made.append))
        self.assertEqual(status, 0)
        self.assertIs(report["value"], True)
        self.assertEqual(sidecar["observations"]["passed_generations"], list(VENUES))
        self.assertEqual(files, [REPORT, SIDECAR])
        self.assertEqual(json.loads(error.strip().splitlines()[-1]), {"exit": 0, "value": True})
        self.assertEqual(len(made), 1)
        self.assertFalse(made[0].exists())

    def test_report_is_a_boolean_and_the_sidecar_carries_identifiers_and_digests_only(self):
        status, report, sidecar, _, _ = run_proof(retained.retained_resolver(controls()))
        self.assertEqual(status, 0)
        self.assertEqual(set(report), DESIGN_REPORT_KEYS)
        self.assertEqual((report["schema"], report["candidate"], report["criterion"], report["unit"], report["exit"]),
                         ("protasis-design-report/v1", "adjacent-burn", "retained-conformance", "boolean", 0))
        self.assertIs(report["value"], True)
        self.assertEqual(report["command"], "python3 " + reports.PROOF_REPORTER + " " + " ".join(ARGUMENTS))
        self.assertEqual(set(sidecar), {"schema", "candidate", "criterion", "observations"})
        self.assertEqual(sidecar["schema"], reports.OBSERVATIONS_SCHEMA)
        self.assertEqual(set(sidecar["observations"]), {"inputs", "passed_generations"})
        inputs = sidecar["observations"]["inputs"]
        self.assertEqual([item["generation"] for item in inputs], list(VENUES))
        for item in inputs:
            self.assertEqual(set(item), INPUT_KEYS)
            self.assertRegex(item["raw_release_id"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(item["canonical_sha256"], HEX64)
            self.assertRegex(item["coverage_sha256"], HEX64)
        for value in walk(sidecar["observations"]):
            self.assertIsInstance(value, str)
            self.assertNotIn("/", value)
            self.assertNotRegex(value, r"0x[0-9a-fA-F]{40}")
            self.assertFalse(value.isdigit())

    def test_unclaimed_market_burn_control_yields_false_and_no_passing_report(self):
        made = []
        status, report, sidecar, files, _ = run_proof(
            retained.retained_resolver(controls("burn-without-payment"), made.append))
        self.assertEqual(status, 1)
        self.assertIs(report["value"], False)
        self.assertEqual(report["exit"], 1)
        self.assertEqual(sidecar["observations"]["passed_generations"], [])
        self.assertEqual(files, [REPORT, SIDECAR])
        self.assertFalse(made[0].exists())

    def test_payment_without_its_burn_control_yields_false_and_no_passing_report(self):
        status, report, sidecar, _, _ = run_proof(retained.retained_resolver(controls("payment-without-burn")))
        self.assertEqual((status, report["value"], report["exit"]), (1, False, 1))
        self.assertEqual(sidecar["observations"]["passed_generations"], [])

    def test_every_hostile_shape_fails_and_a_single_failing_generation_names_the_other_as_passed(self):
        for name in HOSTILE_SPECIMENS:
            with self.subTest(hostile=name):
                generations = (ConstructedGeneration("wildcat-v1", source_order("wildcat-v1")),
                               ConstructedGeneration("wildcat-v2", source_order("wildcat-v2", name)))
                value, observations = retained.retained_conformance(generations, environ={})
                self.assertIs(value, False)
                self.assertEqual(observations["passed_generations"], ["wildcat-v1"])
                self.assertEqual([item["generation"] for item in observations["inputs"]], list(VENUES))

    def test_generation_mapping_no_payment_refuses_by_name_rather_than_passing(self):
        # Without a payment row every join condition holds over an empty set,
        # so the resolver refuses the generation by name and writes nothing.
        for name, transactions in (("no-transactions", []), ("repaid-only", [[("repaid", 80)]]),
                                   ("queue-without-batch", [[("transfer", ACCOUNT, MARKET, 70),
                                                             ("queued", 100, 70, 70)]])):
            with self.subTest(control=name):
                made = []
                generations = (ConstructedGeneration("wildcat-v1", transactions),
                               ConstructedGeneration("wildcat-v2", source_order("wildcat-v2")))
                status, report, sidecar, files, error = run_proof(
                    retained.retained_resolver(generations, made.append))
                self.assertEqual((status, report, sidecar, files), (2, None, None, []))
                self.assertIn("conformance unavailable: EvidenceUnavailable: "
                              "wildcat-v1 maps no withdrawal-batch payment", error)
                self.assertEqual(len(made), 1)
                self.assertFalse(made[0].exists())

    def test_release_conforms_refuses_edited_joins_gaps_and_unsupported_signatures(self):
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary).resolve()
            control = ConstructedGeneration("wildcat-v2", source_order("wildcat-v2"))
            raw = control.rebuild(scratch, scratch / "raw-output")
            canonical = scratch / "canonical"
            retained.build_wildcat_canonical(raw, canonical, "wildcat-v2-control")
            source = retained.document(canonical / "source.json")
            coverage = retained.document(canonical / "coverage.json")
        self.assertTrue(retained.release_conforms(source, coverage))
        payment = next(record for record in source["mapping_records"] if record["signature"] == retained.PAYMENT)
        burn = next(record for record in source["mapping_records"]
                    if record["source_selector"] == payment["join"]["companion_selector"])
        other = next(record for record in source["mapping_records"]
                     if record["signature"] == retained.PAYMENT and record is not payment)

        def edited(change):
            edited_source = json.loads(json.dumps(source))
            edited_coverage = json.loads(json.dumps(coverage))
            records = {record["source_selector"]: record for record in edited_source["mapping_records"]}
            if change == "join-removed":
                records[payment["source_selector"]]["join"] = None
            elif change == "join-rule":
                records[payment["source_selector"]]["join"]["rule"] = "unique-value-burn"
            elif change == "burn-record-differs":
                records[burn["source_selector"]]["join"]["conditions"]["value"] = "0"
            elif change == "burn-claimed-twice":
                records[other["source_selector"]]["join"] = dict(payment["join"], primary_selector=other["source_selector"])
            elif change == "burn-gap":
                edited_coverage["coverage"]["unsupported_events"][retained.BURN_GAP] = 1
            elif change == "unclaimed-gap-on-disposition":
                for item in edited_source["dispositions"]:
                    if item["source_selector"] == burn["source_selector"]:
                        item["gaps"].append(retained.UNCLAIMED_GAP)
            elif change == "unsupported-signature":
                edited_coverage["coverage"]["unsupported_events"]["canonical:market:" + retained.PAYMENT] = 1
            elif change == "unsupported-topic":
                edited_coverage["coverage"]["unsupported_events"]["decode:market:" + sorted(retained.BATCH_TOPICS)[0]] = 1
            return edited_source, edited_coverage

        for change in ("join-removed", "join-rule", "burn-record-differs", "burn-claimed-twice", "burn-gap",
                       "unclaimed-gap-on-disposition", "unsupported-signature", "unsupported-topic"):
            with self.subTest(change=change):
                self.assertFalse(retained.release_conforms(*edited(change)))

    def test_rebuild_refusal_leaves_no_report_and_no_scratch(self):
        made = []
        generations = (ConstructedGeneration("wildcat-v1", source_order("wildcat-v1")), RefusingGeneration("wildcat-v2"))
        status, report, sidecar, files, error = run_proof(retained.retained_resolver(generations, made.append))
        self.assertEqual((status, report, sidecar, files), (2, None, None, []))
        self.assertIn("conformance unavailable: ValueError", error)
        self.assertNotIn("manifest lists", error)
        self.assertEqual(len(made), 1)
        self.assertFalse(made[0].exists())

    def test_scratch_inside_the_repository_refuses_before_anything_is_created(self):
        with mock.patch.object(retained.tempfile, "gettempdir", return_value=str(retained.REPO)):
            with self.assertRaises(retained.EvidenceUnavailable):
                retained.retained_conformance(controls(), environ={})
        self.assertEqual([path for path in retained.REPO.iterdir() if path.name.startswith(retained.SCRATCH_PREFIX)], [])

    def test_public_examples_bind_the_declared_variables_and_verify_their_pins_without_custody(self):
        self.assertEqual(STAGING_VARIABLES, ("ALEXANDRIA_WILDCAT_V1_STAGING", "ALEXANDRIA_WILDCAT_V2_STAGING"))
        for spec in retained.GENERATIONS:
            with self.subTest(generation=spec.generation):
                module = retained.example_module(spec.example)
                self.assertEqual(module.STAGING_ENV_VAR, spec.variable)
                preserved = module.verify_preserved()
                self.assertEqual(preserved["manifest"]["format"], module.MANIFEST_FORMAT)
                self.assertTrue(preserved["record"]["checked"]["release_id"].startswith("sha256:"))
        for spec in (retained.RetainedGeneration("wildcat-v1", "OTHER_VARIABLE", "wildcat-v1-interval-v0"),):
            with self.assertRaises(retained.EvidenceUnavailable), tempfile.TemporaryDirectory() as temporary:
                spec.rebuild(Path(temporary), Path(temporary) / "out")

    def test_step_four_declares_this_class_and_the_resolver_launches_no_subprocess(self):
        self.assertEqual(reports.STEP_CASES[4], (("test_wildcat_batch_retained", "BatchRetainedTests"),))
        self.assertEqual(reports.RETAINED_CASES, reports.STEP_CASES[4])
        self.assertIn(("adjacent-burn", "retained-conformance"), reports.CONFORMANCE)
        tree = ast.parse((HERE / "wildcat_batch_retained.py").read_bytes())
        imported = {(getattr(node, "module", None) or alias.name).split(".")[0]
                    for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names}
        self.assertNotIn("subprocess", imported)
        calls = {node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {"system", "popen", "fork", "spawn", "spawnv", "execv", "execve", "run", "Popen"})
        self.assertNotIn("discover", calls)


if __name__ == "__main__":
    unittest.main()
