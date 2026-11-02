"""Hold the accrual retained-conformance resolver to constructed controls and named custody refusals.

Ordinary discovery needs no retained capture. Each control is built from the
constructed accrual specimen's transactions through the real raw-release path,
and the custody cases point the two staging variables at absent, unreadable,
linked or manifest-failing trees.
"""

from __future__ import annotations

import ast
from contextlib import contextmanager, redirect_stderr
from copy import deepcopy
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

import prove_wildcat_accrual as proof
import wildcat_accrual_reports as reports
import wildcat_accrual_retained as retained
import wildcat_batch_retained as custody
from tabularium_lib.keccak import keccak256
from test_wildcat_v3_release import constructed_release
from wildcat_accrual_public_fixtures import VENUES, declare_second_market, specimen_raws
from wildcat_batch_fixtures import SECOND_MARKET
from wildcat_v3_fixtures import ACCRUAL, ASSET, MARKET, STATE

REPORT = ".hexaemeron/design/reports/abi-named-amounts-retained-conformance.json"
SIDECAR = ".hexaemeron/design/reports/abi-named-amounts-retained-conformance.observations.json"
ARGUMENTS = ["--candidate", "abi-named-amounts", "--criterion", "retained-conformance", "--report", REPORT]
DESIGN_REPORT_KEYS = {"schema", "candidate", "criterion", "value", "unit", "command", "exit"}
INPUT_KEYS = {"generation", "raw_release_id", "canonical_sha256", "coverage_sha256"}
STAGING_VARIABLES = tuple(spec.variable for spec in custody.GENERATIONS)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ACCRUAL_TOPIC, STATE_TOPIC = ("0x" + keccak256(signature.encode()).hex() for signature in (ACCRUAL, STATE))


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


class ConstructedGeneration(custody.RetainedGeneration):
    """A control built from constructed transactions; it needs no staging tree.

    `undecoded` re-declares the second emitter as a context with no concrete
    ABI, so its accrual and state-update logs stay `unsupported-decode` gaps.
    """

    def __init__(self, generation, raws, undecoded=False):
        super().__init__(generation, "CONSTRUCTED_CONTROL_" + generation.upper().replace("-", "_"), None)
        self.raws = raws
        self.undecoded = undecoded

    def custody(self, environ):
        return Path(tempfile.gettempdir()).resolve()

    def rebuild(self, root, output):
        output.mkdir()
        declare = declare_second_market(self.raws, self.generation + "-constructed-control")

        def mutate(document, journal, plan):
            declare(document, journal, plan)
            if self.undecoded:
                for context in document["contexts"]:
                    if context["address"] == SECOND_MARKET:
                        context.update(role="factory", abi_variant=None, concrete_contract=None)

        return constructed_release(output, self.generation, mutate)


class RefusingGeneration(custody.RetainedGeneration):
    """Custody passes; the rebuild refuses the way a failing staging tree does."""

    def __init__(self, generation):
        super().__init__(generation, "CONSTRUCTED_REFUSAL_" + generation.upper().replace("-", "_"), None)

    def custody(self, environ):
        return Path(tempfile.gettempdir()).resolve()

    def rebuild(self, root, output):
        raise ValueError("the staging tree lacks files the manifest lists")


def controls(**overrides):
    """One source-order specimen control per generation, with any generation replaced."""
    return tuple(overrides.get(venue) or ConstructedGeneration(venue, specimen_raws(venue)) for venue in VENUES)


def only(venue, *topics):
    """The specimen's logs whose first topic is one of `topics`, in their original order."""
    return [raw for raw in specimen_raws(venue) if raw["topics"][0] in topics]


def run_proof(resolver):
    """Run the registered proof interface against one resolver in a fresh worktree."""
    with temporary_cwd() as root, mock.patch.dict(reports.CONFORMANCE, {
            ("abi-named-amounts", "retained-conformance"): resolver}), redirect_stderr(io.StringIO()) as error:
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


class AccrualRetainedTests(unittest.TestCase):
    """Constructed controls, custody refusals, report shape and scratch removal."""

    @classmethod
    def setUpClass(cls):
        # One built control for the predicate cases: V2's specimen, whose first
        # market declares its asset and whose second declares none.
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary).resolve()
            raw = ConstructedGeneration("wildcat-v2", specimen_raws("wildcat-v2")).rebuild(scratch, scratch / "raw")
            canonical = scratch / "canonical"
            retained.build_wildcat_canonical(raw, canonical, "wildcat-v2-control")
            cls.source = retained.document(canonical / "source.json")
            cls.coverage = retained.document(canonical / "coverage.json")
            cls.rows = retained.event_rows(canonical / "events.jsonl")

    def test_absent_staging_variable_refuses_by_name_with_exit_2_and_no_report(self):
        for present in ((), ("ALEXANDRIA_WILDCAT_V1_STAGING",)):
            with self.subTest(present=present), tempfile.TemporaryDirectory() as temporary, \
                    staging_environment(**{name: str(Path(temporary).resolve()) for name in present}):
                absent = next(name for name in STAGING_VARIABLES if name not in present)
                status, report, sidecar, files, error = run_proof(reports.CONFORMANCE[
                    ("abi-named-amounts", "retained-conformance")])
                self.assertEqual((status, report, sidecar, files), (2, None, None, []))
                self.assertIn("conformance unavailable: EvidenceUnavailable: " + absent + " is not set", error)
                self.assertNotIn(temporary, error)

    def test_unreadable_linked_or_non_directory_staging_path_refuses_by_name_before_any_scratch(self):
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

    def test_source_order_controls_pass_on_both_generations_and_remove_the_scratch(self):
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
                         ("protasis-design-report/v1", "abi-named-amounts", "retained-conformance", "boolean", 0))
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

    def test_generation_mapping_no_row_of_either_event_refuses_by_name_rather_than_passing(self):
        # With either event absent its conditions hold over an empty set, so the
        # resolver refuses the generation by name and writes nothing.
        for name, raws, missing in (
                ("no-logs", [], "interest-and-fees-accrued"),
                ("batch-only", [raw for raw in specimen_raws("wildcat-v1")
                                if raw["topics"][0] not in (ACCRUAL_TOPIC, STATE_TOPIC)], "interest-and-fees-accrued"),
                ("state-only", only("wildcat-v1", STATE_TOPIC), "interest-and-fees-accrued"),
                ("accrual-only", only("wildcat-v1", ACCRUAL_TOPIC), "state-updated")):
            with self.subTest(control=name):
                made = []
                generations = controls(**{"wildcat-v1": ConstructedGeneration("wildcat-v1", raws)})
                status, report, sidecar, files, error = run_proof(retained.retained_resolver(generations, made.append))
                self.assertEqual((status, report, sidecar, files), (2, None, None, []))
                self.assertIn("conformance unavailable: EvidenceUnavailable: wildcat-v1 maps no " + missing + " row",
                              error)
                self.assertEqual(len(made), 1)
                self.assertFalse(made[0].exists())

    def test_undecoded_emitter_control_yields_false_and_names_the_other_generation_as_passed(self):
        for venue in VENUES:
            with self.subTest(failing=venue):
                made = []
                generations = controls(**{venue: ConstructedGeneration(venue, specimen_raws(venue), undecoded=True)})
                status, report, sidecar, files, _ = run_proof(retained.retained_resolver(generations, made.append))
                self.assertEqual((status, report["value"], report["exit"]), (1, False, 1))
                self.assertEqual(sidecar["observations"]["passed_generations"], [other for other in VENUES if other != venue])
                self.assertEqual([item["generation"] for item in sidecar["observations"]["inputs"]], list(VENUES))
                self.assertEqual(files, [REPORT, SIDECAR])
                self.assertFalse(made[0].exists())

    def test_release_failing_verify_yields_false(self):
        built = retained.build_wildcat_canonical

        def build_then_edit(raw, canonical, name):
            result = built(raw, canonical, name)
            if name.startswith("wildcat-v2"):
                capture = canonical / "capture.json"
                capture.write_bytes(capture.read_bytes() + b"\n")
            return result

        with mock.patch.object(retained, "build_wildcat_canonical", build_then_edit):
            value, observations = retained.retained_conformance(controls(), environ={})
        self.assertIs(value, False)
        self.assertEqual(observations["passed_generations"], ["wildcat-v1"])

    def test_release_conforms_accepts_the_control_and_refuses_each_edited_meaning(self):
        source, rows, coverage = self.source, self.rows, self.coverage
        self.assertTrue(retained.release_conforms("wildcat-v2", source, rows, coverage))
        self.assertFalse(retained.release_conforms("wildcat-v1", source, rows, coverage))
        accruals = [row for row in rows if row["action"] == "wildcat-v2.interest-and-fees-accrued"]
        known = next(row for row in accruals if row["amounts"][3]["asset"] == ASSET)
        unknown = next(row for row in accruals if row["amounts"][3]["asset"] is None)
        state = next(row for row in rows if row["action"] == "wildcat-v2.state-updated")
        other = next(row for row in rows if row["action"].split(".", 1)[1] not in retained.MEANING)

        def edited(change):
            source_, rows_, coverage_ = deepcopy(source), deepcopy(rows), deepcopy(coverage)
            by_selector = {row["provenance"]["source_selector"]: row for row in rows_}
            records = {item["source_selector"]: item for item in source_["mapping_records"]}
            gaps = {item["source_selector"]: item["gaps"] for item in source_["dispositions"]}
            known_, unknown_, state_ = (by_selector[row["provenance"]["source_selector"]]
                                        for row in (known, unknown, state))
            record = records[state["provenance"]["source_selector"]]
            if change == "party-role":
                known_["parties"][0]["role"] = "borrower"
            elif change == "extra-party":
                state_["parties"].append({"role": "actor", "address": MARKET})
            elif change == "amount-kind":
                state_["amounts"][0]["kind"] = "ray"
            elif change == "amount-order":
                known_["amounts"][1], known_["amounts"][2] = known_["amounts"][2], known_["amounts"][1]
            elif change == "amount-converted":
                known_["amounts"][3]["base_units"] = str(int(known_["amounts"][3]["base_units"]) + 1)
            elif change == "ray-asset":
                known_["amounts"][0]["asset"] = ASSET
            elif change == "fee-asset-differs":
                known_["amounts"][3]["asset"] = SECOND_MARKET
            elif change == "timestamp-amount":
                decoded = records[known["provenance"]["source_selector"]]["decoded"]
                known_["amounts"].append({"kind": "from-timestamp", "base_units": decoded["fromTimestamp"], "asset": None})
            elif change == "flag-row-field":
                state_["is_delinquent"] = True
            elif change == "flag-missing":
                del record["decoded"]["isDelinquent"]
            elif change == "flag-not-boolean":
                record["decoded"]["isDelinquent"] = "1"
            elif change == "native-record":
                data = state_["native_record"]["data"]
                state_["native_record"]["data"] = data[:-1] + ("e" if data[-1] == "f" else "f")
            elif change == "joined":
                record["join"] = {"rule": "same-transaction", "primary_selector": state["provenance"]["source_selector"]}
            elif change == "supported-by-event":
                record["supporting_selectors"].append(other["provenance"]["source_selector"])
                state_["provenance"]["supporting_selectors"].append(other["provenance"]["source_selector"])
            elif change == "not-primary":
                record["disposition"] = "unsupported-canonical-meaning"
            elif change == "asset-gap-missing":
                gaps[unknown["provenance"]["source_selector"]].remove("attribution:interest-and-fees-accrued:asset")
            elif change == "asset-gap-extra":
                gaps[known["provenance"]["source_selector"]].append("attribution:interest-and-fees-accrued:asset")
            elif change == "family":
                state_["event_family"] = "interest-accrual"
            elif change == "rule":
                state_["provenance"]["mapping_rule"] = "wildcat-v2.state-updated.v2"
            elif change == "generation":
                state_["action"] = "wildcat-v1.state-updated"
            elif change == "row-dropped":
                rows_.remove(state_)
            elif change == "row-repeated":
                rows_.append(deepcopy(state_))
            elif change == "included-count":
                coverage_["coverage"]["included_events"]["state-updated"] += 1
            elif change == "unsupported-signature":
                coverage_["coverage"]["unsupported_events"]["canonical:market:" + ACCRUAL] = 1
            elif change == "unsupported-topic":
                coverage_["coverage"]["unsupported_events"]["decode:market:" + STATE_TOPIC] = 1
            return source_, rows_, coverage_

        for change in ("party-role", "extra-party", "amount-kind", "amount-order", "amount-converted", "ray-asset",
                       "fee-asset-differs", "timestamp-amount", "flag-row-field", "flag-missing", "flag-not-boolean",
                       "native-record", "joined", "supported-by-event", "not-primary", "asset-gap-missing",
                       "asset-gap-extra", "family", "rule", "generation", "row-dropped", "row-repeated",
                       "included-count", "unsupported-signature", "unsupported-topic"):
            with self.subTest(change=change):
                edited_source, edited_rows, edited_coverage = edited(change)
                self.assertFalse(retained.release_conforms("wildcat-v2", edited_source, edited_rows, edited_coverage))

    def test_rebuild_refusal_leaves_no_report_and_no_scratch(self):
        made = []
        generations = controls(**{"wildcat-v2": RefusingGeneration("wildcat-v2")})
        status, report, sidecar, files, error = run_proof(retained.retained_resolver(generations, made.append))
        self.assertEqual((status, report, sidecar, files), (2, None, None, []))
        self.assertIn("conformance unavailable: ValueError", error)
        self.assertNotIn("manifest lists", error)
        self.assertEqual(len(made), 1)
        self.assertFalse(made[0].exists())

    def test_scratch_inside_the_repository_refuses_before_anything_is_created(self):
        with mock.patch.object(custody.tempfile, "gettempdir", return_value=str(custody.REPO)):
            with self.assertRaises(retained.EvidenceUnavailable):
                retained.retained_conformance(controls(), environ={})
        self.assertEqual([path for path in custody.REPO.iterdir() if path.name.startswith(custody.SCRATCH_PREFIX)], [])

    def test_step_four_declares_this_class_and_the_resolver_reuses_the_custody_helpers(self):
        self.assertEqual(reports.STEP_CASES[4], (("test_wildcat_accrual_retained", "AccrualRetainedTests"),))
        self.assertEqual(reports.RETAINED_CASES, reports.STEP_CASES[4])
        self.assertIn(("abi-named-amounts", "retained-conformance"), reports.CONFORMANCE)
        for helper in ("GENERATIONS", "private_scratch", "document", "sha256_file", "verified"):
            self.assertIs(getattr(retained, helper), getattr(custody, helper), helper)
        tree = ast.parse((HERE / "wildcat_accrual_retained.py").read_bytes())
        defined = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        self.assertFalse(defined & {"RetainedGeneration", "example_module", "private_scratch", "document", "verified"})
        imported = {(getattr(node, "module", None) or alias.name).split(".")[0]
                    for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names}
        # Each forbidden name is split so this module's own bytes stay free of it.
        launcher, validator = "sub" + "process", "json" + "schema"
        self.assertFalse(imported & {launcher, validator})
        calls = {node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {"system", "popen", "fork", "spawn", "spawnv", "execv", "execve", "run", "Popen"})
        self.assertNotIn("discover", calls)
        for name in ("wildcat_accrual_retained.py", "test_wildcat_accrual_retained.py"):
            source = (HERE / name).read_bytes()
            for word in (launcher, validator):
                self.assertNotIn(word.encode(), source, name)


if __name__ == "__main__":
    unittest.main()
