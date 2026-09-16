"""Guard Step 1's refusal boundary and the exact governing document copies."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "plugins/hexaemeron/skills/fiat/scripts"
sys.path.insert(0, str(SCRIPTS))
from checkpoint_authority import conformance as subject


class ConformanceScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        for relative in (*subject.SOURCE_PATHS, subject.MANIFEST_PATH):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def invoke(self, *, criterion="records-and-signatures", candidate="ordered-replay",
               report=None, extra=()):
        if report is None:
            report = f".hexaemeron/reports/{candidate}-{criterion}.json"
        args = ["--candidate", candidate, "--criterion", criterion, "--report", report]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = subject.main([*args, *extra], root=self.root)
        return code, json.loads(output.getvalue())

    def paths(self, criterion="records-and-signatures"):
        path = self.root / ".hexaemeron/reports" / f"ordered-replay-{criterion}.json"
        return path, path.with_suffix(".evidence.json")

    def test_all_declared_gates_refuse_without_executing_cases(self):
        for criterion in subject.CRITERIA:
            with self.subTest(criterion=criterion):
                code, event = self.invoke(criterion=criterion)
                self.assertEqual(code, 3)
                self.assertEqual(event["exit"], code)
                self.assertFalse(event["complete"])
                self.assertEqual(event["status"], "unresolved")
                self.assertEqual(event["code"], "criterion-not-implemented")
                self.assertEqual(event["executed_cases"], [])
                path, evidence_path = self.paths(criterion)
                report = json.loads(path.read_bytes())
                self.assertEqual(set(report), {
                    "schema", "candidate", "criterion", "value", "unit", "command", "exit",
                })
                self.assertEqual(report["schema"], "protasis-design-report/v1")
                self.assertFalse(report["value"])
                self.assertEqual(report["exit"], 3)
                self.assertEqual(json.loads(evidence_path.read_bytes()), event)
                self.assertEqual(event["design_report_sha256"],
                                 hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertLess(path.stat().st_size, subject.MAX_REPORT_BYTES)
                self.assertLess(evidence_path.stat().st_size, subject.MAX_REPORT_BYTES)

    def test_report_binds_actual_source_and_fixture_bytes(self):
        _, event = self.invoke()
        for row in (*event["source"], event["fixture_manifest"]):
            self.assertEqual(row["sha256"], hashlib.sha256(
                (self.root / row["path"]).read_bytes()).hexdigest())

    def test_nonselected_and_unknown_candidates_refuse_without_writes(self):
        for candidate in ("eager-index", "unknown", "ordered-replay ", "sensitive-input"):
            with self.subTest(candidate=candidate):
                code, event = self.invoke(candidate=candidate)
                self.assertEqual(code, 2)
                self.assertEqual(event["code"], "unsupported-candidate")
                self.assertNotIn(candidate, json.dumps(event))
                self.assertFalse((self.root / ".hexaemeron").exists())

    def test_unknown_and_selection_criteria_refuse_without_writes(self):
        for criterion in ("unknown", "model-correctness", "resident-memory", "authority-replay "):
            with self.subTest(criterion=criterion):
                code, event = self.invoke(criterion=criterion)
                self.assertEqual(code, 2)
                self.assertEqual(event["code"], "unknown-criterion")
                self.assertFalse((self.root / ".hexaemeron").exists())

    def test_report_path_is_exact_and_cannot_escape(self):
        for path in (
            "/tmp/forbidden.json", "../forbidden.json", ".hexaemeron/reports/../x.json",
            ".hexaemeron/reports/x.json", ".hexaemeron//reports/ordered-replay-records-and-signatures.json",
            ".hexaemeron/reports/ordered-replay-authority-replay.json", "NUL\x00.json",
            ".hexaemeron\\reports\\ordered-replay-records-and-signatures.json",
        ):
            with self.subTest(path=path):
                code, event = self.invoke(report=path)
                self.assertEqual((code, event["code"]), (2, "unsafe-report-path"))
                self.assertFalse((self.root / ".hexaemeron").exists())

    def test_unknown_option_is_fixed_refusal(self):
        code, event = self.invoke(extra=("--unsafe-option", "private-input"))
        self.assertEqual((code, event["code"]), (2, "invalid-invocation"))
        self.assertNotIn("private-input", json.dumps(event))

    def test_abbreviated_option_refuses(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = subject.main(["--cand", "ordered-replay"], root=self.root)
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["code"], "invalid-invocation")

    def test_existing_report_preserved_and_no_sidecar_added(self):
        report, evidence = self.paths()
        report.parent.mkdir(parents=True)
        report.write_bytes(b"existing-result")
        code, event = self.invoke()
        self.assertEqual((code, event["code"]), (2, "report-exists"))
        self.assertEqual(report.read_bytes(), b"existing-result")
        self.assertFalse(evidence.exists())

    def test_existing_evidence_preserved_and_no_report_added(self):
        report, evidence = self.paths()
        evidence.parent.mkdir(parents=True)
        evidence.write_bytes(b"previous-attempt")
        code, event = self.invoke()
        self.assertEqual((code, event["code"]), (2, "report-exists"))
        self.assertEqual(evidence.read_bytes(), b"previous-attempt")
        self.assertFalse(report.exists())

    def test_retry_preserves_both_exact_files(self):
        self.invoke()
        before = [path.read_bytes() for path in self.paths()]
        code, event = self.invoke()
        self.assertEqual((code, event["code"]), (2, "report-exists"))
        self.assertEqual(before, [path.read_bytes() for path in self.paths()])

    def test_symlink_output_never_modifies_its_target(self):
        report, _ = self.paths()
        report.parent.mkdir(parents=True)
        outside = self.root.parent / "outside"
        outside.write_bytes(b"untouched")
        report.symlink_to(outside)
        self.assertEqual(self.invoke()[0], 2)
        self.assertEqual(outside.read_bytes(), b"untouched")

    def test_hardlink_output_never_modifies_its_target(self):
        report, _ = self.paths()
        report.parent.mkdir(parents=True)
        outside = self.root.parent / "outside"
        outside.write_bytes(b"untouched")
        os.link(outside, report)
        self.assertEqual(self.invoke()[0], 2)
        self.assertEqual(outside.read_bytes(), b"untouched")

    def test_fifo_output_refuses_without_waiting(self):
        report, _ = self.paths()
        report.parent.mkdir(parents=True)
        os.mkfifo(report)
        self.assertEqual(self.invoke()[0], 2)

    def test_symlink_report_directory_cannot_redirect_write(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (self.root / ".hexaemeron").mkdir()
        (self.root / ".hexaemeron/reports").symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.invoke()[0], 2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_state_directory_cannot_redirect_write(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (self.root / ".hexaemeron").symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.invoke()[0], 2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_root_refuses(self):
        alias = self.root.parent / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        self.root = alias
        self.assertEqual(self.invoke()[0], 2)

    def test_symlink_source_refuses(self):
        source = self.root / subject.SOURCE_PATHS[0]
        source.unlink()
        source.symlink_to(ROOT / subject.SOURCE_PATHS[0])
        self.assertEqual(self.invoke()[0], 2)

    def test_hardlink_source_refuses(self):
        source = self.root / subject.SOURCE_PATHS[0]
        outside = self.root.parent / "outside-source"
        outside.write_bytes(source.read_bytes())
        source.unlink()
        os.link(outside, source)
        self.assertEqual(self.invoke()[0], 2)

    def test_fifo_source_refuses_without_waiting(self):
        source = self.root / subject.SOURCE_PATHS[0]
        source.unlink()
        os.mkfifo(source)
        self.assertEqual(self.invoke()[0], 2)

    def test_oversized_source_refuses(self):
        (self.root / subject.SOURCE_PATHS[0]).write_bytes(b"x" * (subject.MAX_INPUT_BYTES + 1))
        self.assertEqual(self.invoke()[0], 2)

    def test_changed_source_is_observed_in_identity(self):
        source = self.root / subject.SOURCE_PATHS[0]
        source.write_bytes(source.read_bytes() + b"\n")
        _, event = self.invoke()
        self.assertEqual(event["source"][0]["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())

    def test_malformed_manifest_refuses(self):
        manifest = self.root / subject.MANIFEST_PATH
        for data in (b"{", b"\xff", b"[]", b'{"cases":[],"cases":[]}'):
            with self.subTest(data=data):
                manifest.write_bytes(data)
                self.assertEqual(self.invoke()[0], 2)
                self.assertFalse((self.root / ".hexaemeron").exists())

    def test_manifest_cannot_invent_implemented_cases(self):
        manifest = self.root / subject.MANIFEST_PATH
        body = json.loads(manifest.read_bytes())
        body["implemented_criteria"] = ["records-and-signatures"]
        manifest.write_text(json.dumps(body))
        code, event = self.invoke()
        self.assertEqual((code, event["code"]), (2, "unsupported-manifest"))

    def test_partial_write_is_preserved_and_never_passes(self):
        original = subject._create
        def fail_report(parent, name, data):
            if not name.endswith(".evidence.json"):
                raise OSError("private-path-must-not-leak")
            original(parent, name, data)
        with mock.patch.object(subject, "_create", side_effect=fail_report):
            code, event = self.invoke()
        self.assertEqual(code, 2)
        self.assertNotIn("private-path", json.dumps(event))
        report, evidence = self.paths()
        self.assertFalse(report.exists())
        self.assertFalse(json.loads(evidence.read_bytes())["complete"])
        self.assertEqual(self.invoke()[0], 2)

    def test_directory_swap_leaves_replacement_untouched_and_refuses(self):
        original = subject._create
        retired = self.root / "retired-reports"
        def swap_after_evidence(parent, name, data):
            original(parent, name, data)
            directory = self.root / ".hexaemeron/reports"
            directory.rename(retired)
            directory.mkdir()
        with mock.patch.object(subject, "_create", side_effect=swap_after_evidence):
            code, event = self.invoke()
        self.assertEqual((code, event["code"]), (2, "directory-changed"))
        self.assertEqual(list((self.root / ".hexaemeron/reports").iterdir()), [])
        self.assertEqual(len(list(retired.iterdir())), 1)

    def test_real_cli_returns_nonzero_and_uses_source_root(self):
        result = subprocess.run(
            [sys.executable, str(self.root / subject.SOURCE_PATHS[2]),
             "--candidate", "ordered-replay", "--criterion", "records-and-signatures",
             "--report", ".hexaemeron/reports/ordered-replay-records-and-signatures.json"],
            cwd=self.root.parent, capture_output=True, timeout=10, check=False,
        )
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertFalse(json.loads(result.stdout)["complete"])
        self.assertTrue(self.paths()[0].is_file())
        self.assertFalse((self.root.parent / ".hexaemeron").exists())

    def test_refusal_report_cannot_open_protasis_transition(self):
        state = self.root / ".hexaemeron"
        state.mkdir()
        shutil.copyfile(ROOT / "docs/checkpoint-authority/design-evidence.json",
                        state / "design-evidence.json")
        shutil.copytree(ROOT / "docs/checkpoint-authority/reports", state / "reports")
        self.invoke()
        path = ROOT / "plugins/hexaemeron/skills/protasis/scripts/design_evidence.py"
        spec = importlib.util.spec_from_file_location("p862_design_check", path)
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        findings = checker.check(state / "design-evidence.json", transition="step:3")
        self.assertTrue(findings)
        self.assertTrue(any(item.code in {"D005", "D008"} for item in findings))


class GoverningSourcesTests(unittest.TestCase):
    def test_exact_public_study_runbook_and_design_identities(self):
        pins = {
            "study.md": "1efc7bb7710f75cab7f824b8952ee08b668e2c3722dee6b834bccbe8bba36a62",
            "runbook.md": "e16fb947a1fa9f6d495e43bd7cf677f42fb33a93ab89d7f0085f56e85f5f243e",
            "design-evidence.json": "a34e662db37cdfed1d3c82520402ffb41790b94c977ca99813a12ea25e3785b1",
            "specimens/adopted-specification.md": "8ee755c1f9e5c29703af30bd08caffb6fad80c8a0990ee0acecebef09b02f541",
        }
        for name, expected in pins.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((ROOT / "docs/checkpoint-authority" / name).read_bytes()).hexdigest(), expected)

    def test_selection_reports_keep_their_original_bytes(self):
        public = ROOT / "docs/checkpoint-authority"
        design = json.loads((public / "design-evidence.json").read_bytes())
        resolved = [row for row in design["results"] if row["state"] != "pending"]
        self.assertEqual(len(resolved), 10)
        for row in resolved:
            self.assertEqual(hashlib.sha256((public / row["report"]["path"]).read_bytes()).hexdigest(), row["report"]["sha256"])
        self.assertEqual(design["selection"]["candidate"], subject.CANDIDATE)
        criteria = [row["criterion"] for row in design["results"]
                    if row["candidate"] == subject.CANDIDATE and row["state"] == "pending"]
        self.assertEqual(criteria, list(subject.CRITERIA))

    def test_original_governance_bytes_remain_exact_prefixes(self):
        pins = (
            ("docs/decisions/ADR-070-separate-the-checkpoint-protocol-from-its-authority-service.md", 7829, "00a8034de4c257d735c351bd0ed340e30717616f78c7887354078562e8f67b40"),
            ("docs/decisions/ADR-071-hold-checkpoint-authority-in-locked-storage-behind-replaceable-compute.md", 8147, "3afcec068d32cafeef2c437448ec1504558b329eb475a20f68f5bd841716f42c"),
            ("docs/wave-delta-checkpoint-programme-study.md", 14790, "cdba6c02e086449ca1490d40488cc62b0d0b98f0adc42e33c7ad65ab8732fb0d"),
            ("docs/wave-delta-checkpoint-programme-runbook.md", 10893, "465ba56a38fff421fb13696cad5818efefd936d3aa3b4b7f23e00f23e5deb113"),
        )
        for path, size, digest in pins:
            with self.subTest(path=path):
                data = (ROOT / path).read_bytes()
                self.assertEqual(hashlib.sha256(data[:size]).hexdigest(), digest)
                self.assertTrue(data[size:].startswith(b"\n## Amendment, 2026-09-16:"))

    def test_governing_source_inventory_matches_exact_copies(self):
        inventory = json.loads((ROOT / "docs/checkpoint-authority/governing-sources.json").read_bytes())
        for row in inventory["exact_copies"]:
            path = ROOT / row["path"]
            if not path.exists() and "/drafts/" in row["path"]:
                # Integration assigns only the draft's path and first heading.
                slug = path.stem
                matches = list((ROOT / "docs/decisions").glob("ADR-???-" + slug + ".md"))
                self.assertEqual(len(matches), 1)
                lines = matches[0].read_bytes().split(b"\n", 1)
                data = b"# Decision:" + lines[0].split(b":", 1)[1] + b"\n" + lines[1]
            else:
                data = path.read_bytes()
            self.assertEqual(len(data), row["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])

    def test_protocol_documents_select_protocol_checks(self):
        graph = json.loads((ROOT / "tests/check-map-v1.json").read_bytes())
        for path in ("docs/checkpoint-authority/study.md", *subject.SOURCE_PATHS, subject.MANIFEST_PATH):
            owners = [row for row in graph["owners"]
                      if path == row["path"] or path.startswith(row["path"] + "/")]
            owner = max(owners, key=lambda row: len(row["path"]))
            self.assertEqual(owner["scope"], "hexaemeron")


if __name__ == "__main__":
    unittest.main()
