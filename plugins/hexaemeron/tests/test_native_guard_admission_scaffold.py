"""Check published scaffold custody and refusals without claiming conformance."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs/native-guard-admission"
DECISION = "docs/decisions/drafts/route-audit-obligations-to-their-evidence.md"
DECISION_SLUG = "route-audit-obligations-to-their-evidence"
PROOF = DOCS / "proof.py"
EXPECTED_DIGESTS = {
    "study.md": "45e864d1acdd4a66e1a8034dd1662235d811229d2c7ab87cc62115c0e6dada2f",
    "runbook.md": "62982d5f7cf3a4fec1dbdc7a20f255a814c58e2c4aa71c0b16ba03973f6e81b2",
    "design-evidence.json": "4f5aba14c308c63b3d1ea62aa682f380b996f68230601bd9a8fe7fb3e3c014ab",
}


def load(path):
    return json.loads(path.read_text())


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


HYPOMNEMA = load_module(
    ROOT / "plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py",
    "native_admission_scaffold_hypomnema",
)
ASSIGNMENTS = load_module(
    ROOT / "plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py",
    "native_admission_scaffold_assignments",
)


def decision_source_bytes(root):
    data, path, error = HYPOMNEMA._read_stable_adr(root, "adr/" + DECISION_SLUG)
    if data is None:
        raise AssertionError(error)
    if path.as_posix() != DECISION:
        prefix = ("# " + path.name[:7] + ": ").encode("ascii")
        if not data.startswith(prefix):
            raise AssertionError("assigned decision heading does not match its path")
        data = b"# Decision: " + data[len(prefix):]
    return data


class NativeGuardAdmissionScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def invoke(self, report=".hexaemeron/reports/proof.json", **overrides):
        candidate = overrides.get("candidate", "typed-applicability")
        criterion = overrides.get("criterion", "native-execution")
        result = subprocess.run(
            [sys.executable, str(PROOF), "--candidate", candidate,
             "--criterion", criterion, "--report", report],
            cwd=self.root, capture_output=True, text=True, timeout=10,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertLess(len(result.stdout.encode()), 1024)
        record = json.loads(result.stdout)
        self.assertEqual(set(record), {
            "schema", "candidate", "criterion", "available_step", "report_written", "code",
        })
        self.assertEqual(record["schema"], "native-guard-admission-refusal/v1")
        self.assertIs(record["report_written"], False)
        return record

    def test_accepted_source_bytes_remain_exact(self):
        for path, expected in EXPECTED_DIGESTS.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((DOCS / path).read_bytes()).hexdigest(), expected)

    def test_selected_design_has_one_canonical_decision(self):
        design = load(DOCS / "design-evidence.json")
        study = (DOCS / "study.md").read_text()
        blocks = re.findall(r"^```design-bridge\n(.*?)^```", study, re.M | re.S)
        self.assertEqual(blocks, [
            "schema | hypomnema-design-bridge/v1\n"
            "decision | typed-applicability\n"
            f"record | {DECISION}\n",
        ])
        self.assertEqual(design["selection"]["candidate"], "typed-applicability")
        decision = decision_source_bytes(ROOT).decode("utf-8")
        self.assertTrue(decision.startswith("# Decision: Route audit obligations to their evidence\n"))
        for heading in ("Status", "Context", "Decision", "Alternatives", "Consequences"):
            self.assertEqual(decision.count("\n## " + heading + "\n"), 1)
        self.assertIn("Implementation and conformance remain pending.", decision)

    def test_selection_reports_keep_their_digests_and_pending_cells(self):
        results = load(DOCS / "design-evidence.json")["results"]
        selected = [row for row in results if row["state"] != "pending"]
        self.assertEqual(len(selected), 15)
        self.assertEqual(sum(row["state"] == "pending" for row in results), 18)
        for row in selected:
            report = row["report"]
            raw = (DOCS / report["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), report["sha256"])
            decoded = json.loads(raw)
            self.assertEqual(decoded["candidate"], row["candidate"])
            self.assertEqual(decoded["criterion"], row["criterion"])
            self.assertEqual(decoded["exit"], 0)

    def test_original_synthetic_probe_reproduces_all_fifteen_reports(self):
        research = self.root / ".hexaemeron/research"
        research.mkdir(parents=True)
        for name in ("design_probe.py", "candidate-models.json"):
            shutil.copyfile(DOCS / "research" / name, research / name)
        for path in sorted((DOCS / "reports/design").glob("*.json")):
            report = load(path)
            argv = shlex.split(report["command"])
            self.assertEqual(argv[:2], ["python3", ".hexaemeron/research/design_probe.py"])
            self.assertEqual(argv[-2], "--report")
            expected_path = ".hexaemeron/reports/design/" + path.name
            self.assertEqual(argv[-1], expected_path)
            result = subprocess.run(
                [sys.executable, *argv[1:]], cwd=self.root,
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((self.root / expected_path).read_bytes(), path.read_bytes())

    def test_examples_preserve_four_dispositions_and_exact_source_status(self):
        fixture = load(DOCS / "fixtures/applicability.json")
        self.assertEqual(set(fixture), {"schema", "source_views", "entries"})
        self.assertEqual(fixture["schema"], "protasis-audit-applicability/v1")
        self.assertEqual(len(fixture["source_views"]), 1)
        source = (DOCS / "fixtures/source.md").read_bytes()
        view = fixture["source_views"][0]
        self.assertEqual(set(view), {"id", "path", "source_sha256", "view_sha256"})
        self.assertEqual(view["source_sha256"], hashlib.sha256(source).hexdigest())
        self.assertEqual(view["view_sha256"], hashlib.sha256((ROOT / view["path"]).read_bytes()).hexdigest())
        expected_statuses = {
            "local-regression": "open", "integration-requirement": "not checked",
            "historical": "fixed in the recorded source", "out-of-scope": "open upstream",
        }
        self.assertEqual({row["disposition"] for row in fixture["entries"]}, set(expected_statuses))
        self.assertEqual(len(fixture["entries"]), 4)
        targets = load(DOCS / "fixtures/targets.json")
        self.assertEqual(targets["evidence_status"], "not-executed")
        for row in fixture["entries"]:
            self.assertEqual(set(row), {
                "id", "source_ref", "source_span", "source_status", "disposition",
                "rationale", "finding_id", "criterion_id", "tracking",
            })
            self.assertRegex(row["id"], r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
            self.assertEqual(row["source_ref"].split(":", 1), [view["id"], row["id"]])
            span = row["source_span"]
            self.assertEqual(set(span), {"start_byte", "end_byte", "sha256"})
            self.assertIs(type(span["start_byte"]), int)
            self.assertIs(type(span["end_byte"]), int)
            self.assertLess(span["start_byte"], span["end_byte"])
            self.assertLessEqual(span["end_byte"], len(source))
            witness = source[span["start_byte"]:span["end_byte"]]
            self.assertEqual(hashlib.sha256(witness).hexdigest(), span["sha256"])
            self.assertEqual(row["source_status"], expected_statuses[row["disposition"]])
            self.assertIn("Status: " + row["source_status"], witness.decode())
            self.assertEqual(row["tracking"], [])
            if row["disposition"] == "local-regression":
                self.assertIn(row["finding_id"], targets["regressions"])
                self.assertIsNone(row["criterion_id"])
            elif row["disposition"] == "integration-requirement":
                self.assertIn(row["criterion_id"], targets["criteria"])
                self.assertIsNone(row["finding_id"])
            else:
                self.assertIsNone(row["finding_id"])
                self.assertIsNone(row["criterion_id"])

    def test_provenance_covers_only_declared_public_files(self):
        manifest = load(DOCS / "fixtures/provenance.json")
        self.assertEqual(set(manifest), {"schema", "artifacts"})
        self.assertEqual(manifest["schema"], "native-guard-admission-provenance/v1")
        paths = [row["path"] for row in manifest["artifacts"]]
        self.assertEqual(paths, sorted(set(paths)))
        expected = {
            str(path.relative_to(ROOT)) for path in DOCS.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
            and path.name != "provenance.json"
        } | {DECISION}
        self.assertEqual(set(paths), expected)
        allowed_origins = {
            "accepted-study", "accepted-runbook", "accepted-design-evidence",
            "authored-synthetic-selection-source", "executed-synthetic-selection",
            "authored-synthetic-fixture", "reviewed-decision", "scaffold-source",
            "executed-parser-conformance",
        }
        for row in manifest["artifacts"]:
            self.assertEqual(set(row), {"path", "sha256", "origin"})
            self.assertIn(row["origin"], allowed_origins)
            self.assertTrue(row["path"].startswith("docs/native-guard-admission/") or row["path"] == DECISION)
            self.assertNotIn("..", Path(row["path"]).parts)
            self.assertIn(Path(row["path"]).suffix, (".md", ".py", ".json"))
            raw = decision_source_bytes(ROOT) if row["path"] == DECISION else (ROOT / row["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
        self.assertEqual(sum(row["origin"] == "executed-synthetic-selection" for row in manifest["artifacts"]), 15)
        self.assertEqual(sum(row["origin"] == "authored-synthetic-selection-source" for row in manifest["artifacts"]), 2)

    def assigned_fixture(self):
        docs = self.root / "docs/native-guard-admission"
        shutil.copytree(DOCS, docs)
        decision = self.root / "docs/decisions" / ("ADR-999-" + DECISION_SLUG + ".md")
        decision.parent.mkdir(parents=True, exist_ok=True)
        decision.write_bytes(ASSIGNMENTS.transformed(decision_source_bytes(ROOT), "999"))
        return docs, decision

    def test_required_assignment_preserves_scaffold_checks(self):
        docs, _ = self.assigned_fixture()
        with mock.patch.object(sys.modules[__name__], "ROOT", self.root), \
                mock.patch.object(sys.modules[__name__], "DOCS", docs):
            self.test_selected_design_has_one_canonical_decision()
            self.test_provenance_covers_only_declared_public_files()

    def test_assignment_still_refuses_changed_decision_body(self):
        docs, decision = self.assigned_fixture()
        decision.write_bytes(decision.read_bytes() + b"\nChanged decision content.\n")
        with mock.patch.object(sys.modules[__name__], "ROOT", self.root), \
                mock.patch.object(sys.modules[__name__], "DOCS", docs):
            with self.assertRaises(AssertionError):
                self.test_provenance_covers_only_declared_public_files()

    def test_assignment_still_refuses_duplicate_decision_homes(self):
        _, decision = self.assigned_fixture()
        draft = self.root / DECISION
        draft.parent.mkdir()
        draft.write_bytes(decision_source_bytes(ROOT))
        with self.assertRaisesRegex(AssertionError, "more than one canonical"):
            decision_source_bytes(self.root)

    def test_assignment_still_refuses_heading_number_mismatch(self):
        _, decision = self.assigned_fixture()
        decision.write_bytes(decision.read_bytes().replace(b"# ADR-999: ", b"# ADR-998: ", 1))
        with self.assertRaisesRegex(AssertionError, "heading does not match"):
            decision_source_bytes(self.root)

    def test_unimplemented_operations_refuse_without_creating_files(self):
        design = load(DOCS / "design-evidence.json")
        count = 0
        for row in design["results"]:
            if row["state"] != "pending":
                continue
            if row["candidate"] == "typed-applicability" and row["criterion"] in {"applicability-parser", "bounded-reader"}:
                continue
            count += 1
            with self.subTest(candidate=row["candidate"], criterion=row["criterion"]):
                result = self.invoke(candidate=row["candidate"], criterion=row["criterion"])
                self.assertEqual(result["code"], "operation-unavailable")
                expected_step = {"applicability-parser": 2, "bounded-reader": 2, "frozen-controller-join": 3}.get(row["criterion"], 4)
                self.assertEqual(result["available_step"], expected_step)
                self.assertEqual(result["candidate"], row["candidate"])
                self.assertEqual(result["criterion"], row["criterion"])
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertEqual(count, 16)

    def test_parser_proof_executes_tests_and_preserves_exact_evidence(self):
        report = ".hexaemeron/reports/parser.json"
        result = subprocess.run(
            [sys.executable, str(PROOF), "--candidate", "typed-applicability",
             "--criterion", "applicability-parser", "--report", report],
            cwd=self.root, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        record = load(self.root / report)
        evidence = load(self.root / ".hexaemeron/reports/parser.evidence.json")
        self.assertIs(record["value"], True)
        self.assertIs(evidence["operation_ran"], True)
        self.assertGreater(evidence["tests"], 0)
        self.assertEqual([evidence[k] for k in ("failures", "errors", "skips", "declared_command_launches")], [0, 0, 0, 0])
        self.assertEqual(evidence["design_report_sha256"], hashlib.sha256((self.root / report).read_bytes()).hexdigest())
        for row in evidence["sources"]:
            self.assertEqual(row["sha256"], hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest())
        before = (self.root / report).read_bytes()
        self.assertEqual(self.invoke(report, criterion="applicability-parser")["code"], "report-exists")
        self.assertEqual((self.root / report).read_bytes(), before)

    def test_existing_evidence_companion_refuses_before_report_creation(self):
        evidence = self.root / ".hexaemeron/reports/parser.evidence.json"
        evidence.parent.mkdir(parents=True)
        evidence.write_bytes(b"retained")
        self.assertEqual(self.invoke(".hexaemeron/reports/parser.json", criterion="applicability-parser")["code"], "report-exists")
        self.assertEqual(evidence.read_bytes(), b"retained")
        self.assertFalse((self.root / ".hexaemeron/reports/parser.json").exists())

    def test_existing_report_is_never_replaced(self):
        path = self.root / ".hexaemeron/reports/proof.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(b'{"preserve":"original report"}\n')
        original = path.read_bytes()
        self.assertEqual(self.invoke()["code"], "report-exists")
        self.assertEqual(path.read_bytes(), original)

    def test_report_leaf_links_and_directories_refuse_without_following(self):
        path = self.root / ".hexaemeron/reports/proof.json"
        path.parent.mkdir(parents=True)
        target = self.root / "unrelated"
        target.write_bytes(b"independent bytes")
        path.symlink_to(target)
        self.assertEqual(self.invoke()["code"], "report-exists")
        self.assertEqual(target.read_bytes(), b"independent bytes")
        path.unlink()
        path.mkdir()
        self.assertEqual(self.invoke()["code"], "report-exists")

    def test_linked_report_ancestor_refuses(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / ".hexaemeron").symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.invoke()["code"], "report-path-invalid")
        self.assertEqual(list(outside.iterdir()), [])

    def test_unsafe_report_spellings_refuse(self):
        for operand in ("", "outside.json", "/tmp/outside.json", ".hexaemeron/reports/../outside.json",
                        ".hexaemeron/reports/./x.json", ".hexaemeron/reports/x.txt",
                        ".hexaemeron/reports/a\\b.json", ".hexaemeron/reports/\nx.json",
                        ".hexaemeron/reports/" + "x" * 1024 + ".json"):
            with self.subTest(operand=operand):
                self.assertEqual(self.invoke(operand)["code"], "report-path-invalid")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_absolute_report_inside_current_worktree_still_has_no_write(self):
        result = self.invoke(str(self.root / ".hexaemeron/reports/proof.json"))
        self.assertEqual(result["code"], "operation-unavailable")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_unknown_arguments_have_bounded_value_free_refusal(self):
        marker = "caller-material-" * 1000
        for override in ({"candidate": marker}, {"criterion": marker}):
            result = self.invoke(**override)
            self.assertEqual(result["code"], "invalid-arguments")
            self.assertIsNone(result["candidate"])
            self.assertIsNone(result["criterion"])

    def test_new_documentation_has_a_hex_runner_owner(self):
        owners = load(ROOT / "tests/check-map-v1.json")["owners"]
        self.assertIn({"path": "docs/native-guard-admission", "scope": "hexaemeron"}, owners)


if __name__ == "__main__":
    unittest.main()
