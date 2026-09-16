"""Focused contract tests for the pre-persistence capture profile."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def scratch_directory(prefix="run-observation-capture-"):
    """A transient in-repository directory that `git status` never sees.

    The validator and writers confine paths under the repository root, so
    scratch space must stay inside it -- but a temporary directory under the
    tracked fixture tree (or the repository top level) makes the repository
    non-quiescent while a case runs, and the disposable-signing guard's
    outer-stability assertion races against it under parallel shards.  The
    ignored top-level tmp/ satisfies both: confined, and invisible to status.
    """
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)

STARTING_BASE = "411d5131ecc8f4e50f3db57deee881a56605cd38"
PRODUCT_HEAD = "1979372032828f4ed82fdc258187910163a67cb7"
SCRIPT = ROOT / "scripts" / "run_observation_capture.py"
FIXTURES = ROOT / "tests" / "fixtures" / "run-observation-capture"
REPORTER_SCRIPT = ROOT / "tests" / "emit_run_observation_capture_report.py"
STUDY = ROOT / "docs" / "promise-machine" / "run-observation-capture-study.md"
RUNBOOK = ROOT / "docs" / "promise-machine" / "run-observation-capture-runbook.md"
# Recorded from issue 435's receipted Fiat sources at delivery. Those sources
# lived in the Fiat state directory of a run worktree that no longer exists, so
# these digests and the tracked copies above are both halves of the byte-identity
# claim that survive. Bind assertions to them, never to a state path a live run
# owns: that path belongs to whichever run holds the worktree, so reading it
# checks somebody else's study and fails every run but 435's. See issue 574.
RECEIPTED_DIGESTS = {
    STUDY: "6858aaeadb12f204538b9120e51390b9c940fa995c8edb1471815d89aaa7f404",
    RUNBOOK: "56df27b7faae2af8f7ba16ec89526413038def6a0bbf86ff0274dc566f8bf9c5",
}
PROMISE_COPIES = tuple(Path("plugins") / name / "PROMISE_MACHINE.md" for name in (
    "alexandria", "ariadne", "berean", "brevitas", "hermes", "hexaemeron",
    "horos", "janus", "lazarus", "lemma", "pandects", "probitas", "sapheneia", "tabularium",
))
CARRYOVER_GUARDS = {
    "C1-01": "test_coverage_command_is_supported_and_obsolete_spelling_is_rejected",
    "C1-02": "test_reporter_has_exact_modules_and_nonzero_error_exit",
    "C1-03": "test_capture_adr_has_the_repository_form",
    "C1-04": "test_receipted_copies_are_byte_identical_and_relocatable",
    "R1-01": "test_negative_counter_descriptor_is_refused",
    "R1-02": "test_redaction_object_order_is_not_part_of_its_contract",
    "R1-03": "test_claimed_entropy_does_not_make_repeated_bytes_eligible",
    "R1-04": "test_writer_refuses_bypass_and_never_writes_a_gap",
    "R1-05": "test_reporter_writer_refuses_a_symlinked_parent",
    "R1-06": "test_schema_and_runtime_document_the_same_closed_vocabulary",
    "R1-07": "test_promise_coverage_binds_the_reporter_bytes",
    "R1-08": "test_elenchus_command_uses_report_format",
    "R2-01": "test_complete_union_manifest_covers_paths_and_carryover_guards",
    "R3-01": "test_receipted_copies_have_exactly_one_terminal_newline",
    "R4-01": "test_receipted_sources_and_copies_are_digest_equal",
    "R5-01": "test_receipted_copies_have_no_literal_newline_escape",
    "R6-01": "test_adr_allocation_preserves_017_and_uses_022",
    "R7-01": "test_current_promise_coverage_rows_are_present",
    "R8-01": "test_literal_escape_detector_targets_5c6e",
    "R9-01": "test_receipt_assertions_never_read_a_live_run_path",
    "R9-02": "test_literal_escape_detector_targets_5c6e",
    "R9-03": "test_receipted_sources_are_never_modified",
    "R10-01": "test_base_identity_is_bound_across_receipts_and_branch",
}
PRODUCT_PATHS = (
    Path("PROMISE_MACHINE.md"), *PROMISE_COPIES,
    Path("schemas/promise-machine-run-observation-capture-v1.schema.json"),
    Path("scripts/run_observation_capture.py"),
    Path("docs/decisions/ADR-022-define-the-run-observation-capture-profile.md"),
    Path("docs/promise-machine/run-observation-capture-v1.md"), STUDY.relative_to(ROOT), RUNBOOK.relative_to(ROOT),
    Path("tests/fixtures/run-observation-capture/valid/accepted.json"),
    Path("tests/fixtures/run-observation-capture/valid/gap.json"),
    Path("tests/fixtures/run-observation-capture/valid/fingerprinted.json"),
    Path("tests/fixtures/run-observation-capture/invalid/raw-payload.json"),
    Path("tests/fixtures/run-observation-capture/invalid/unsafe-path.json"),
    Path("tests/test_run_observation_capture.py"), Path("tests/test_run_observation_capture_inoculation.py"),
    Path("tests/emit_run_observation_capture_report.py"), Path("tests/promise_machine_coverage.json"),
    Path("tests/test_promise_machine_contract.py"),
)


LITERAL_NEWLINE_ESCAPE = b"\\n"
capture = None
if SCRIPT.is_file():
    SPEC = importlib.util.spec_from_file_location("capture", SCRIPT)
    capture = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = capture
    assert SPEC.loader is not None
    SPEC.loader.exec_module(capture)


class CaptureSurfaceGuardTests(unittest.TestCase):
    """Make a detached parent record a missing capture surface as a failure."""

    def test_capture_surface_exists_before_the_profile_suite_runs(self):
        required = (
            SCRIPT,
            ROOT / "schemas" / "promise-machine-run-observation-capture-v1.schema.json",
            ROOT / "docs" / "promise-machine" / "run-observation-capture-v1.md",
        )
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        self.assertFalse(missing, f"capture surface is absent: {', '.join(missing)}")


class CaptureProfileTests(unittest.TestCase):
    def setUp(self):
        if capture is None:
            self.skipTest("capture runtime is absent in the detached parent worktree")

    def candidate(self):
        return json.loads((FIXTURES / "valid" / "accepted.json").read_text(encoding="utf-8"))

    def test_accepted_candidate_has_only_allowed_descriptors(self):
        result = capture.capture_candidate(self.candidate(), ROOT)
        self.assertEqual(result.outcome, "accepted")
        self.assertEqual(result.code, "accepted")
        self.assertEqual(result.event["descriptors"]["repository_path"], "docs")
        self.assertEqual(result.redactions[0], {"field_class": "content", "reason_code": "forbidden_content", "method": "omitted"})

    def test_forbidden_payload_becomes_a_safe_gap_without_echo(self):
        candidate = self.candidate()
        sentinel = "HOSTILE-RAW-SENTINEL-435"
        candidate["headers"] = {"Authorization": sentinel}
        result = capture.capture_candidate(candidate, ROOT)
        public = json.dumps(result.public())
        self.assertEqual(result.outcome, "gap")
        self.assertNotIn(sentinel, public)
        self.assertNotIn("headers", public)

    def test_unknown_shape_and_limits_fail_closed(self):
        result = capture.capture_candidate(["not", "an", "object"], ROOT)
        self.assertEqual((result.outcome, result.code), ("refused", "unsafe_shape"))
        candidate = self.candidate()
        candidate["event"]["name"] = "x" * (capture.MAX_STRING_BYTES + 1)
        result = capture.capture_candidate(candidate, ROOT)
        self.assertEqual((result.outcome, result.code), ("refused", "unsafe_shape"))

    def test_negative_counter_descriptor_is_refused(self):
        candidate = self.candidate()
        candidate["event"]["count"] = -1
        result = capture.capture_candidate(candidate, ROOT)
        self.assertEqual((result.outcome, result.code), ("refused", "unsafe_shape"))
        candidate["event"]["count"] = capture.MAX_COUNTER + 1
        result = capture.capture_candidate(candidate, ROOT)
        self.assertEqual((result.outcome, result.code), ("refused", "unsafe_shape"))

    def test_redaction_object_order_is_not_part_of_its_contract(self):
        candidate = self.candidate()
        candidate["redactions"] = [{
            "method": "omitted",
            "reason_code": "forbidden_content",
            "field_class": "content",
        }]
        result = capture.capture_candidate(candidate, ROOT)
        self.assertEqual(result.outcome, "accepted")
        self.assertEqual(result.redactions[0], {
            "field_class": "content",
            "reason_code": "forbidden_content",
            "method": "omitted",
        })

    def test_path_is_dehosted_and_escape_is_a_gap(self):
        result = capture.capture_candidate(self.candidate(), ROOT)
        self.assertEqual(result.event["descriptors"]["repository_path"], "docs")
        candidate = self.candidate()
        candidate["repository_path"] = "/private/var/db"
        result = capture.capture_candidate(candidate, ROOT)
        self.assertEqual((result.outcome, result.code), ("gap", "invalid_path"))
        self.assertNotIn("private", json.dumps(result.public()))

    def test_high_entropy_fingerprint_is_scoped_and_source_is_absent(self):
        candidate = json.loads((FIXTURES / "valid" / "fingerprinted.json").read_text(encoding="utf-8"))
        raw = candidate["fingerprint"]["value_b64"]
        result = capture.capture_candidate(candidate, ROOT)
        output = json.dumps(result.public())
        self.assertEqual(result.outcome, "accepted")
        self.assertEqual(result.event["descriptors"]["correlation"]["algorithm"], "sha256")
        self.assertNotIn(raw, output)
        candidate["fingerprint"]["entropy_bits"] = 64
        gap = capture.capture_candidate(candidate, ROOT)
        self.assertEqual((gap.outcome, gap.code), ("gap", "ineligible_fingerprint"))

    def test_claimed_entropy_does_not_make_repeated_bytes_eligible(self):
        candidate = self.candidate()
        candidate["fingerprint"] = {
            "scope": "capture",
            "value_b64": "eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eA==",
            "entropy_bits": 512,
        }
        result = capture.capture_candidate(candidate, ROOT)
        self.assertEqual((result.outcome, result.code), ("gap", "ineligible_fingerprint"))

    def test_writer_refuses_bypass_and_never_writes_a_gap(self):
        result = capture.capture_candidate(self.candidate(), ROOT)
        gap = capture.capture_candidate({"prompt": "HOSTILE"}, ROOT)
        with scratch_directory() as directory, tempfile.TemporaryDirectory() as outside:
            destination = Path(directory) / "capture" / "record.json"
            with self.assertRaises(ValueError):
                capture.write_accepted(destination, {"outcome": "accepted"})
            with self.assertRaises(ValueError):
                capture.write_accepted(destination, gap)
            forged = capture.CaptureResult(
                "accepted",
                "accepted",
                event={"schema_id": capture.CONTRACT_ID, "descriptors": {"raw": "HOSTILE-WRITER-BYPASS-435"}},
            )
            with self.assertRaises(ValueError):
                capture.write_accepted(destination, forged)
            result.event["descriptors"]["raw"] = "HOSTILE-MUTATED-435"
            with self.assertRaises(ValueError):
                capture.write_accepted(destination, result)
            result = capture.capture_candidate(self.candidate(), ROOT)
            redirected = Path(directory) / "redirected"
            redirected.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                capture.write_accepted(redirected / "escaped.json", result)
            self.assertFalse((Path(outside) / "escaped.json").exists())
            capture.write_accepted(destination, result)
            written = destination.read_text(encoding="utf-8")
        self.assertNotIn("HOSTILE", written)
        self.assertIn('"outcome":"accepted"', written)

    def test_cli_never_echoes_hostile_fixture_bytes(self):
        fixture = FIXTURES / "invalid" / "raw-payload.json"
        completed = subprocess.run([sys.executable, str(SCRIPT), "check", str(fixture)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("HOSTILE-HEADER-SENTINEL-435", completed.stdout + completed.stderr)
        self.assertIn('"outcome":"gap"', completed.stdout)

    def test_schema_and_runtime_document_the_same_closed_vocabulary(self):
        schema = json.loads((ROOT / "schemas" / "promise-machine-run-observation-capture-v1.schema.json").read_text(encoding="utf-8"))
        redaction = schema["$defs"]["redaction"]["properties"]
        self.assertEqual(set(redaction["field_class"]["enum"]), capture.REDACTION_FIELD_CLASSES)
        self.assertEqual(set(redaction["reason_code"]["enum"]), capture.REDACTION_REASON_CODES)
        self.assertEqual(set(redaction["method"]["enum"]), capture.REDACTION_METHODS)
        descriptors = schema["properties"]["event"]["properties"]["descriptors"]
        self.assertFalse(descriptors["additionalProperties"])
        self.assertEqual(descriptors["properties"]["count"]["minimum"], 0)
        self.assertEqual(descriptors["properties"]["count"]["maximum"], capture.MAX_COUNTER)
        self.assertFalse(schema["properties"]["event"]["additionalProperties"])
        document = (ROOT / "docs" / "promise-machine" / "run-observation-capture-v1.md").read_text(encoding="utf-8")
        for value in capture.REDACTION_METHODS | capture.REDACTION_REASON_CODES:
            self.assertIn(value, document)

    def test_complete_union_manifest_covers_paths_and_carryover_guards(self):
        self.assertEqual(
            set(CARRYOVER_GUARDS),
            {"C1-01", "C1-02", "C1-03", "C1-04", "R1-01", "R1-02", "R1-03", "R1-04", "R1-05", "R1-06", "R1-07", "R1-08", "R2-01", "R3-01", "R4-01", "R5-01", "R6-01", "R7-01", "R8-01", "R9-01", "R9-02", "R9-03", "R10-01"},
        )
        source = Path(__file__).read_text(encoding="utf-8")
        for path in PRODUCT_PATHS:
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())
        for finding, guard in CARRYOVER_GUARDS.items():
            with self.subTest(finding=finding):
                self.assertIn(finding, source)
                self.assertIn(f"def {guard}(", source)

    def test_promise_coverage_binds_the_reporter_bytes(self):
        coverage = json.loads((ROOT / "tests" / "promise_machine_coverage.json").read_text(encoding="utf-8"))["run_observation_capture"]
        reporter = coverage["reporter"]
        self.assertEqual(reporter["path"], "tests/emit_run_observation_capture_report.py")
        self.assertEqual(reporter["sha256"], __import__("hashlib").sha256(REPORTER_SCRIPT.read_bytes()).hexdigest())

    def test_elenchus_command_uses_report_format(self):
        runbook = RUNBOOK.read_text(encoding="utf-8")
        study = STUDY.read_text(encoding="utf-8")
        self.assertIn("--report-file .elenchus/run-observation-capture.json", runbook)
        self.assertIn("--report-format unittest-json-v1", runbook)
        self.assertNotIn("--format unittest-json-v1", runbook)
        self.assertNotIn("elenchus.py compare", runbook)
        self.assertNotIn("elenchus.py compare", study)
        completed = subprocess.run([sys.executable, "plugins/hexaemeron/skills/elenchus/scripts/elenchus.py", "--help"], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--report-format", completed.stdout)
        self.assertIn("--format {text,json}", completed.stdout)

    def test_coverage_command_is_supported_and_obsolete_spelling_is_rejected(self):
        supported = subprocess.run([sys.executable, "scripts/promise_machine.py", "coverage", "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
        obsolete = subprocess.run([sys.executable, "scripts/promise_machine.py", "check-coverage"], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(supported.returncode, 0, supported.stdout + supported.stderr)
        self.assertEqual(obsolete.returncode, 2)
        self.assertIn("invalid choice", obsolete.stderr)

    def test_reporter_has_exact_modules_and_nonzero_error_exit(self):
        reporter_spec = importlib.util.spec_from_file_location("capture_reporter", REPORTER_SCRIPT)
        reporter = importlib.util.module_from_spec(reporter_spec)
        assert reporter_spec.loader is not None
        reporter_spec.loader.exec_module(reporter)
        self.assertEqual(reporter.MODULES, (
            "tests.test_run_observation_capture",
            "tests.test_run_observation_capture_inoculation",
            "tests.test_promise_machine_contract",
        ))
        with scratch_directory() as directory:
            output = Path(directory) / "report.json"
            class FailingCaptureTest(unittest.TestCase):
                def test_failure(self):
                    self.fail("synthetic reporter failure")

            with mock.patch.object(reporter, "build_suite", return_value=unittest.TestSuite([FailingCaptureTest("test_failure")])):
                self.assertEqual(reporter.main([str(output)]), 1)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["schema"], "elenchus.unittest.v1")
        self.assertEqual(report["testsRun"], 1)
        self.assertEqual(report["failures"], 1)

    def test_reporter_writer_refuses_a_symlinked_parent(self):
        reporter_spec = importlib.util.spec_from_file_location("capture_reporter_symlink", REPORTER_SCRIPT)
        reporter = importlib.util.module_from_spec(reporter_spec)
        assert reporter_spec.loader is not None
        reporter_spec.loader.exec_module(reporter)
        with scratch_directory() as directory, tempfile.TemporaryDirectory() as outside:
            redirected = Path(directory) / "redirected"
            redirected.symlink_to(outside, target_is_directory=True)
            target = redirected / "report.json"
            with self.assertRaises(ValueError):
                reporter.write_new(target, b"{}\n")
            self.assertFalse((Path(outside) / "report.json").exists())

    def test_capture_adr_has_the_repository_form(self):
        document = (ROOT / "docs" / "decisions" / "ADR-022-define-the-run-observation-capture-profile.md").read_text(encoding="utf-8")
        self.assertRegex(document, r"Accepted, 2026-08-24\.")
        for section in ("## Context", "## Decision", "## Alternatives", "## Consequences"):
            self.assertIn(section, document)
        self.assertIn("https://github.com/wildcat-finance/skills/issues/435", document)

    def test_receipted_copies_are_byte_identical_and_relocatable(self):
        for copy in (STUDY, RUNBOOK):
            with self.subTest(path=copy):
                self.assertEqual(hashlib.sha256(copy.read_bytes()).hexdigest(), RECEIPTED_DIGESTS[copy])
        for original in (STUDY, RUNBOOK):
            with tempfile.TemporaryDirectory() as directory:
                moved = Path(directory) / original.name
                shutil.copyfile(original, moved)
                text = moved.read_text(encoding="utf-8")
                for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
                    self.assertTrue(target.startswith("https://"), target)

    def test_receipted_copies_have_exactly_one_terminal_newline(self):
        for copy in (STUDY, RUNBOOK):
            with self.subTest(path=copy):
                self.assertEqual(copy.read_bytes()[-1:], b"\n")
                self.assertNotEqual(copy.read_bytes()[-2:], b"\n\n")

    def test_receipted_sources_and_copies_are_digest_equal(self):
        for copy in (STUDY, RUNBOOK):
            with self.subTest(path=copy):
                self.assertEqual(hashlib.sha256(copy.read_bytes()).digest(), bytes.fromhex(RECEIPTED_DIGESTS[copy]))

    def test_receipted_copies_have_no_literal_newline_escape(self):
        recorded = subprocess.run(
            ["git", "show", "HEAD:tests/test_run_observation_capture.py"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        expected_detector = b'LITERAL_NEWLINE_ESCAPE = b"' + bytes((0x5C, 0x5C, 0x6E, 0x22))
        if recorded.returncode == 0:
            self.assertIn(expected_detector, recorded.stdout)
        self.assertEqual(LITERAL_NEWLINE_ESCAPE, bytes((0x5C, 0x6E)))
        self.assertIn(LITERAL_NEWLINE_ESCAPE, b"first" + LITERAL_NEWLINE_ESCAPE + b"second")
        for path in (STUDY, RUNBOOK):
            with self.subTest(path=path):
                self.assertNotIn(LITERAL_NEWLINE_ESCAPE, path.read_bytes())

    def test_literal_escape_detector_targets_5c6e(self):
        self.assertEqual(LITERAL_NEWLINE_ESCAPE, bytes((0x5C, 0x6E)))
        self.assertNotEqual(LITERAL_NEWLINE_ESCAPE, bytes((0x5C, 0x5C, 0x6E)))

    def test_receipt_assertions_never_read_a_live_run_path(self):
        # Built rather than spelled, so this assertion is not its own counterexample.
        live_run_state = "." + "hexaemeron"
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotIn(live_run_state, source)
        self.assertTrue(STUDY.is_file())
        self.assertTrue(RUNBOOK.is_file())

    def test_receipted_sources_are_never_modified(self):
        self.assertEqual(set(RECEIPTED_DIGESTS), {STUDY, RUNBOOK})
        for copy, digest in RECEIPTED_DIGESTS.items():
            with self.subTest(path=copy):
                self.assertEqual(hashlib.sha256(copy.read_bytes()).hexdigest(), digest)

    def test_base_identity_is_bound_across_receipts_and_branch(self):
        self.assertIn(STARTING_BASE, STUDY.read_text(encoding="utf-8"))
        self.assertIn(STARTING_BASE, RUNBOOK.read_text(encoding="utf-8"))
        adr = (
            ROOT
            / "docs"
            / "decisions"
            / "ADR-022-define-the-run-observation-capture-profile.md"
        ).read_text(encoding="utf-8")
        self.assertIn(STARTING_BASE, adr)
        self.assertIn(PRODUCT_HEAD, adr)
        available = subprocess.run(
            ["git", "cat-file", "-e", f"{PRODUCT_HEAD}^{{commit}}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if available.returncode != 0:
            return
        product_parent = subprocess.run(
            ["git", "rev-parse", f"{PRODUCT_HEAD}^1"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(product_parent.stdout.strip(), STARTING_BASE)
        composed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", PRODUCT_HEAD, "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(composed.returncode, 0, composed.stderr)

    def test_c12_runbook_names_the_aggregate(self):
        self.assertTrue(RUNBOOK.read_text(encoding="utf-8").startswith("# Fiat #435 CARRYOVER-12 runbook:"))

    def test_adr_allocation_preserves_017_and_uses_022(self):
        preserved = ROOT / "docs" / "decisions" / "ADR-017-gate-durable-agent-prose.md"
        base = subprocess.run(["git", "show", "HEAD:docs/decisions/ADR-017-gate-durable-agent-prose.md"], cwd=ROOT, capture_output=True, check=True).stdout
        self.assertEqual(preserved.read_bytes(), base)
        self.assertTrue((ROOT / "docs" / "decisions" / "ADR-018-bind-merged-authorship-to-the-integration-receipt.md").is_file())
        capture_adr = ROOT / "docs" / "decisions" / "ADR-022-define-the-run-observation-capture-profile.md"
        self.assertTrue(capture_adr.is_file())
        self.assertTrue(capture_adr.read_text(encoding="utf-8").startswith("# ADR-022:"))

    def test_current_promise_coverage_rows_are_present(self):
        coverage = json.loads((ROOT / "tests" / "promise_machine_coverage.json").read_text(encoding="utf-8"))
        rows = {row["promise_id"]: row for row in coverage["rows"]}
        self.assertIn("sapheneia-durable-record-shape", rows)
        for key in ("fiat-final-integration", "fiat-receipted-delivery", "fiat-study-amendment"):
            positive = coverage["evidence"][rows[key]["cases"]["P"]]
            runtime = coverage["runtime"][key]
            self.assertEqual(runtime["source"], positive["path"])
            self.assertEqual(runtime["selector"], positive["selector"])
            expected = hashlib.sha256((ROOT / positive["path"]).read_bytes()).hexdigest()
            self.assertEqual(runtime["sha256"], expected)
