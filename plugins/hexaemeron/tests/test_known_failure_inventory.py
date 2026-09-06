"""Guards for the source-bound Protasis known-failure inventory."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]
SCRIPT = PLUGIN_ROOT / "skills/protasis/scripts/known_failure_inventory.py"
EMITTER = PLUGIN_ROOT / "tests/emit_issue_453_guard_report.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures/issue-453/inventory.json"
COMMITTED_STUDY = REPOSITORY_ROOT / "docs/known-failure-inoculation-study.md"
COMMITTED_RUNBOOK = PLUGIN_ROOT / "docs/known-failure-inoculation/runbook.md"
EXPECTED_IDS = frozenset(
    {
        "kf-453-01",
        "kf-453-02",
        "kf-453-03",
        "kf-453-04",
        "kf-453-05",
        "kf-453-06",
        "kf-453-07",
    }
)

RUNBOOK = """# Known-failure inoculation runbook

## Step 1: Define the inventory

Known-failure assignment: `kf-453-01` -> Step 1

## Step 2: Open the inoculation phase

Known-failure assignment: `kf-453-02` -> Step 2

## Step 3: Retain the guard evidence

Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3

## Step 4: Prove recovery and final green

Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4
"""

NO_FINDINGS_RUNBOOK = """# No-known-findings runbook

## Step 1: Record the explicit claim
"""

STEP_ONLY_RUNBOOK = """# Known-failure inoculation runbook

## Step 1: Define the inventory

## Step 2: Open the inoculation phase

## Step 3: Retain the guard evidence

## Step 4: Prove recovery and final green
"""

ASSIGNMENT_BLOCK = """Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4"""


def runbook_amendment(what_changed: str) -> str:
    return (
        "\n### Amendment -- 2026-09-05\n\n"
        f"**What changed.** {what_changed.rstrip()}\n\n"
        "**Why.** The checked source changed.\n\n"
        "**Steps touched.** Step 1's Exit.\n\n"
        "**Still holding.** Steps 2 through 4 still hold.\n"
    )


def exit_replacement(assignments: str = ASSIGNMENT_BLOCK) -> str:
    return (
        "Complete replacement Exit: The effective assignment set follows.\n\n"
        f"{assignments}\n\n"
        "The remaining exit checks still apply."
    )


def load_checker(test: unittest.TestCase):
    """Load after asserting so the unfixed parent is a guard, not an error."""
    test.assertTrue(
        SCRIPT.is_file(),
        "known-failure inventory checker is absent on the unfixed parent",
    )
    spec = importlib.util.spec_from_file_location("known_failure_inventory", SCRIPT)
    test.assertIsNotNone(spec)
    test.assertIsNotNone(spec.loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_emitter(test: unittest.TestCase):
    test.assertTrue(EMITTER.is_file())
    spec = importlib.util.spec_from_file_location("issue_453_guard_report", EMITTER)
    test.assertIsNotNone(spec)
    test.assertIsNotNone(spec.loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory_object() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def study_text(body: str) -> str:
    return (
        "# Study\n\n"
        "```known-failure-inventory\n"
        f"{body.rstrip()}\n"
        "```\n"
    )


def encoded(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=False)


class KnownFailureInventoryTests(unittest.TestCase):
    def setUp(self):
        self.checker = load_checker(self)
        self.emitter = load_emitter(self)

    def _copy_source_repository(self, root: Path) -> str:
        """Copy only the source/view pairs named by the fixed inventory."""
        first_source = ""
        for view in inventory_object()["source_views"]:
            view_source = REPOSITORY_ROOT / view["path"]
            view_target = root / view["path"]
            view_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(view_source, view_target)
            first_line = next(
                self.checker._markdown_physical_lines(
                    view_source.read_text(encoding="utf-8")
                )
            ).rstrip("\r\n")
            header = self.checker.SYNOPSIS_HEADER.fullmatch(first_line)
            self.assertIsNotNone(header)
            source_path = header.group("source")
            if not first_source:
                first_source = source_path
            source_target = root / source_path
            source_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY_ROOT / source_path, source_target)
        return first_source

    def _load(
        self,
        value: dict | None = None,
        *,
        body: str | None = None,
        study: str | None = None,
        runbook: str = RUNBOOK,
        repository: Path = REPOSITORY_ROOT,
        expected_ids=EXPECTED_IDS,
    ):
        if study is None:
            if body is None:
                body = encoded(inventory_object() if value is None else value)
            study = study_text(body)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            study_path = root / "study.md"
            runbook_path = root / "runbook.md"
            study_path.write_text(study, encoding="utf-8")
            runbook_path.write_text(runbook, encoding="utf-8")
            return self.checker.load_checked_inventory(
                study_path,
                runbook_path,
                repository,
                expected_ids=expected_ids,
            )

    def _findings(self, *args, **kwargs):
        return list(self._load(*args, **kwargs).findings)

    def _codes(self, *args, **kwargs):
        return [finding.code for finding in self._findings(*args, **kwargs)]

    def test_kf_453_01_closed_inventory_is_source_bound(self):
        found = self._findings()
        self.assertEqual([finding.as_dict() for finding in found], [])

    def test_loader_distinguishes_absence_refusal_and_clean_capture(self):
        absent = self._load(
            study="# Study without an inventory\n",
            runbook=NO_FINDINGS_RUNBOOK,
            expected_ids=None,
        )
        self.assertEqual("absent", absent.status)
        self.assertIsNone(absent.capture)
        self.assertEqual((), absent.findings)

        expected_but_absent = self._load(
            study="# Study without an inventory\n",
            runbook=NO_FINDINGS_RUNBOOK,
            expected_ids=sorted(EXPECTED_IDS),
        )
        self.assertEqual("refused", expected_but_absent.status)
        self.assertIsNone(expected_but_absent.capture)
        self.assertEqual(
            ["K006"],
            [finding.code for finding in expected_but_absent.findings],
        )

        attempted = (
            "# Study\n\n```known-failure-inventory\n"
            '{"schema":"protasis-known-failure-inventory/v1"}\n'
        )
        refused = self._load(
            study=attempted,
            runbook=NO_FINDINGS_RUNBOOK,
            expected_ids=None,
        )
        self.assertEqual("refused", refused.status)
        self.assertIsNone(refused.capture)
        self.assertTrue(refused.findings)
        self.assertIn(
            refused.findings[0].code,
            {f"K{index:03d}" for index in range(13)},
        )

        partial_assignment = self._load(
            study="# Study without an inventory\n",
            runbook=NO_FINDINGS_RUNBOOK + "\nKnown-failure assignment: malformed\n",
            expected_ids=None,
        )
        self.assertEqual("refused", partial_assignment.status)
        self.assertTrue(partial_assignment.findings)

        inventory_in_runbook = self._load(
            study="# Study without an inventory\n",
            runbook=NO_FINDINGS_RUNBOOK + "\n```known-failure-inventory\n{}\n```\n",
            expected_ids=None,
        )
        self.assertEqual("refused", inventory_in_runbook.status)
        self.assertTrue(inventory_in_runbook.findings)

        assignment_in_study = self._load(
            study="# Study\n\nKnown-failure assignment: `kf-misplaced` -> Step 1\n",
            runbook=NO_FINDINGS_RUNBOOK,
            expected_ids=None,
        )
        self.assertEqual("refused", assignment_in_study.status)
        self.assertTrue(assignment_in_study.findings)

        clean = self._load()
        self.assertEqual("clean", clean.status)
        self.assertIsNotNone(clean.capture)
        self.assertEqual((), clean.findings)

    def test_cli_refuses_absent_surfaces_with_nonempty_expected_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            study_path = root / "study.md"
            runbook_path = root / "runbook.md"
            study_path.write_text("# Study without an inventory\n", encoding="utf-8")
            runbook_path.write_text(NO_FINDINGS_RUNBOOK, encoding="utf-8")
            command = [
                "python3",
                str(SCRIPT),
                str(study_path),
                str(runbook_path),
                "--repository",
                str(REPOSITORY_ROOT),
                "--format",
                "json",
            ]
            for finding_id in sorted(EXPECTED_IDS):
                command.extend(("--expected-id", finding_id))

            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(1, completed.returncode, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual("refused", report["status"])
        self.assertFalse(report["clean"])
        self.assertEqual(1, report["finding_count"])
        self.assertEqual(["K006"], [finding["code"] for finding in report["findings"]])

    def test_clean_capture_is_closed_canonical_and_assignment_ordered(self):
        value = inventory_object()
        value["findings"][0]["failure"] += " — café"
        runbook = RUNBOOK.replace(
            "Known-failure assignment: `kf-453-03` -> Step 3\n"
            "Known-failure assignment: `kf-453-04` -> Step 3\n"
            "Known-failure assignment: `kf-453-05` -> Step 3",
            "Known-failure assignment: `kf-453-05` -> Step 3\n"
            "Known-failure assignment: `kf-453-04` -> Step 3\n"
            "Known-failure assignment: `kf-453-03` -> Step 3",
        ).replace(
            "Known-failure assignment: `kf-453-06` -> Step 4\n"
            "Known-failure assignment: `kf-453-07` -> Step 4",
            "Known-failure assignment: `kf-453-07` -> Step 4\n"
            "Known-failure assignment: `kf-453-06` -> Step 4",
        )
        study = study_text(encoded(value))
        result = self._load(value, study=study, runbook=runbook)

        self.assertEqual("clean", result.status)
        capture = result.capture
        self.assertIsNotNone(capture)
        self.assertEqual(
            {
                "schema",
                "study_sha256",
                "runbook_sha256",
                "inventory_sha256",
                "source_views",
                "findings",
                "no_known_findings",
                "assignments",
            },
            set(capture),
        )
        self.assertEqual(
            "protasis-known-failure-inventory-capture/v1", capture["schema"]
        )
        self.assertEqual(
            hashlib.sha256(study.encode("utf-8")).hexdigest(),
            capture["study_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(runbook.encode("utf-8")).hexdigest(),
            capture["runbook_sha256"],
        )
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
        self.assertEqual(
            hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            capture["inventory_sha256"],
        )
        self.assertEqual(value["source_views"], capture["source_views"])
        self.assertEqual(value["findings"], capture["findings"])
        self.assertEqual(value["no_known_findings"], capture["no_known_findings"])
        self.assertEqual(
            [
                {"finding_id": finding_id, "step": step}
                for step, finding_ids in (
                    (1, ["kf-453-01"]),
                    (2, ["kf-453-02"]),
                    (3, ["kf-453-03", "kf-453-04", "kf-453-05"]),
                    (4, ["kf-453-06", "kf-453-07"]),
                )
                for finding_id in finding_ids
            ],
            capture["assignments"],
        )

    def test_committed_study_fixture_and_exact_checker_command_have_parity(self):
        study = COMMITTED_STUDY.read_text(encoding="utf-8")
        body, _line, error = self.checker._inventory_block(study)
        self.assertIsNone(error)
        self.assertIsNotNone(body)
        self.assertEqual(inventory_object(), self.checker._json(body))

        command = [
            "python3",
            SCRIPT.relative_to(REPOSITORY_ROOT).as_posix(),
            COMMITTED_STUDY.relative_to(REPOSITORY_ROOT).as_posix(),
            COMMITTED_RUNBOOK.relative_to(REPOSITORY_ROOT).as_posix(),
            "--repository",
            ".",
        ]
        for finding_id in sorted(EXPECTED_IDS):
            command.extend(("--expected-id", finding_id))
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

        projected = subprocess.run(
            [*command, "--format", "json"],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(0, projected.returncode, projected.stdout + projected.stderr)
        report = json.loads(projected.stdout)
        self.assertEqual("protasis-known-failure-inventory-check/v1", report["schema"])
        self.assertEqual("clean", report["status"])
        self.assertTrue(report["clean"])
        self.assertEqual(0, report["finding_count"])
        self.assertEqual([], report["findings"])
        self.assertEqual(
            self.checker.load_checked_inventory(
                COMMITTED_STUDY,
                COMMITTED_RUNBOOK,
                REPOSITORY_ROOT,
                expected_ids=sorted(EXPECTED_IDS),
            ).capture,
            report["capture"],
        )

    def test_exactly_one_closed_inventory_fence_is_required(self):
        body = encoded(inventory_object())
        cases = (
            "# Study without an inventory\n",
            study_text(body) + "\n" + study_text(body),
            "# Study\n\n```known-failure-inventory\n" + body,
            "# Study\n\n~~~known-failure-inventory\n" + body + "\n```\n",
            study_text(body).replace("\n", "\u2028"),
            "# Study\n\n```known-failure-inventory\u00a0\n"
            + body
            + "\n```\n",
            "# Study\n\n```known-failure-inventory\n"
            + body
            + "\n```\u00a0\n",
            study_text(body)
            + "\n- item\n\n"
            + "  ```known-failure-inventory\n"
            + body
            + "\n  ```\n",
        )
        for source in cases:
            with self.subTest(source=source[:40]):
                self.assertIn("K001", self._codes(study=source))

        for tag in ("pre", "div", "guard-record"):
            hidden = f"<{tag}>\n{study_text(body)}</{tag}>\n\n"
            with self.subTest(raw_html=tag):
                self.assertIn("K001", self._codes(study=hidden))

        duplicate_wrappers = (
            "    <!--",
            "paragraph\n<guard-record>",
            "<guard-record ???>",
            "<x a=?>",
            "<pre/foo",
            "paragraph <pre>",
            "<![cdata[",
            "<!foo",
            "![",
        )
        for wrapper in duplicate_wrappers:
            hostile = study_text(body) + "\n" + wrapper + "\n" + study_text(body)
            with self.subTest(raw_html_duplicate=wrapper):
                self.assertIn("K001", self._codes(study=hostile))

        visible_html_examples = study_text(body) + (
            "\n```text\n<!-- visible example -->\n<guard-record>\n```\n"
        )
        self.assertEqual([], self._codes(study=visible_html_examples))

        inventory_fence = "```known-failure-inventory\n" + body + "\n```"
        hidden_inventory_cases = (
            "[foo](https://example.invalid \"\n" + inventory_fence + "\n\")",
            "[foo]: /url \"\n" + inventory_fence + "\n\"",
            "[\n" + inventory_fence + "\n]: /url",
        )
        for hidden in hidden_inventory_cases:
            with self.subTest(hidden_inventory=hidden[:30]):
                self.assertIn("K001", self._codes(study=hidden))

        bad_backtick_info = (
            "# Study\n\n```bad`info\n" + study_text(body) + "\n"
        )
        self.assertIn("K001", self._codes(study=bad_backtick_info))

    def test_study_prose_tick_tolerance_never_masks_inventory_structure(self):
        body = encoded(inventory_object())
        inventory_fence = "```known-failure-inventory\n" + body + "\n```\n"
        prose = "# Study\n\nA `Complete replacement\nExit:` value.\n\n"
        for ending in ("\n", "\r\n", "\r"):
            source = (prose + inventory_fence).replace("\n", ending)
            with self.subTest(ending=repr(ending)):
                self.assertEqual([], self._codes(study=source))

        adjacent = "# Study\n\nAn open `tick\n" + inventory_fence
        self.assertIn("K001", self._codes(study=adjacent))

        separated = "# Study\n\nAn open `tick\n\n" + inventory_fence
        self.assertEqual([], self._codes(study=separated))
        self.assertIn(
            "K001",
            self._codes(study=separated + "\n" + inventory_fence),
        )

        malformed_info = (
            "# Study\n\n```known-failure-inventory`bad\n"
            + body
            + "\n```\n"
        )
        self.assertIn("K001", self._codes(study=malformed_info))

        strict, strict_error = self.checker._markdown_surface(
            "A `Complete replacement\nExit:` value."
        )
        self.assertIsNone(strict)
        self.assertIsNotNone(strict_error)

    def test_duplicate_keys_malformed_json_and_excessive_depth_refuse(self):
        valid = encoded(inventory_object())
        duplicate = valid.replace(
            '  "schema": "protasis-known-failure-inventory/v1",',
            '  "schema": "protasis-known-failure-inventory/v1",\n'
            '  "schema": "protasis-known-failure-inventory/v1",',
            1,
        )
        malformed = valid[:-1]
        deep = '{"schema":"protasis-known-failure-inventory/v1","x":' + (
            "[" * 40 + "0" + "]" * 40
        ) + ',"source_views":[],"findings":[],"no_known_findings":null}'
        nonfinite = valid.replace('"consuming_step": 1', '"consuming_step": NaN', 1)
        for body in (duplicate, malformed, deep, nonfinite):
            with self.subTest(body=body[:60]):
                self.assertIn("K002", self._codes(body=body))

    def test_top_level_shape_and_schema_are_closed(self):
        for field in ("schema", "source_views", "findings", "no_known_findings"):
            value = inventory_object()
            del value[field]
            with self.subTest(missing=field):
                self.assertIn("K003", self._codes(value))
        value = inventory_object()
        value["extra"] = True
        self.assertIn("K003", self._codes(value))
        value = inventory_object()
        value["schema"] = "protasis-known-failure-inventory/v2"
        self.assertIn("K003", self._codes(value))

    def test_source_view_shape_ids_paths_and_digests_are_closed(self):
        fields = ("id", "path", "source_sha256", "view_sha256")
        for field in fields:
            value = inventory_object()
            del value["source_views"][0][field]
            with self.subTest(missing=field):
                self.assertIn("K004", self._codes(value))
        value = inventory_object()
        value["source_views"][0]["extra"] = "no"
        self.assertIn("K004", self._codes(value))
        for bad_id in ("", "Issue Root", "issue_root"):
            value = inventory_object()
            value["source_views"][0]["id"] = bad_id
            with self.subTest(source_id=bad_id):
                self.assertIn("K004", self._codes(value))
        value = inventory_object()
        value["source_views"][1]["id"] = value["source_views"][0]["id"]
        self.assertIn("K004", self._codes(value))
        value = inventory_object()
        value["source_views"][1]["path"] = value["source_views"][0]["path"]
        self.assertIn("K004", self._codes(value))
        value = inventory_object()
        value["source_views"][1]["path"] = value["source_views"][0]["path"].upper()
        self.assertIn("K004", self._codes(value))
        for field in ("source_sha256", "view_sha256"):
            value = inventory_object()
            value["source_views"][0][field] = "0" * 63
            with self.subTest(digest=field):
                self.assertIn("K004", self._codes(value))

    def test_source_and_view_digest_drift_refuse_separately(self):
        for field in ("source_sha256", "view_sha256"):
            value = inventory_object()
            value["source_views"][0][field] = "0" * 64
            with self.subTest(drift=field):
                found = self._findings(value)
                self.assertEqual(["K005"], [finding.code for finding in found])
                self.assertEqual(
                    REPOSITORY_ROOT / value["source_views"][0]["path"],
                    found[0].path,
                )
                self.assertIn(field, found[0].message)

    def test_source_view_paths_are_portable_and_confined(self):
        for path in (
            "/tmp/view.md",
            "../view.md",
            "audit/../view.md",
            "audit\\view.md",
            "audit//view.md",
            "./audit/view.md",
        ):
            value = inventory_object()
            value["source_views"][0]["path"] = path
            with self.subTest(path=path):
                self.assertIn("K004", self._codes(value))

    def test_source_ref_and_finding_shape_are_closed(self):
        fields = (
            "id",
            "source_ref",
            "failure",
            "guard_paths",
            "test_command",
            "report_format",
            "report_file",
            "expected_guard_verdict",
            "green_command",
            "consuming_step",
        )
        for field in fields:
            value = inventory_object()
            del value["findings"][0][field]
            with self.subTest(missing=field):
                self.assertIn("K006", self._codes(value))
        value = inventory_object()
        value["findings"][0]["extra"] = "no"
        self.assertIn("K006", self._codes(value))
        for source_ref in (
            "missing-colon",
            "unknown-source: detail",
            "issue-327-root:",
            "issue-327-root: line one\nline two",
            "issue-327-root: line one\u2028line two",
            "issue-327-root: " + "x" * 4096,
        ):
            value = inventory_object()
            value["findings"][0]["source_ref"] = source_ref
            with self.subTest(source_ref=source_ref):
                self.assertIn("K006", self._codes(value))

    def test_finding_ids_are_well_formed_and_unique(self):
        for finding_id in ("", "KF-453-01", "kf_453_01"):
            value = inventory_object()
            value["findings"][0]["id"] = finding_id
            with self.subTest(finding_id=finding_id):
                self.assertIn("K006", self._codes(value))
        value = inventory_object()
        value["findings"][1]["id"] = value["findings"][0]["id"]
        self.assertIn("K006", self._codes(value))

    def test_the_whole_finding_id_set_is_independent_and_exact(self):
        missing = inventory_object()
        missing["findings"].pop()
        self.assertIn("K006", self._codes(missing))

        extra = inventory_object()
        finding = copy.deepcopy(extra["findings"][-1])
        finding["id"] = "kf-453-08"
        for field in ("test_command", "report_file", "green_command"):
            finding[field] = finding[field].replace("kf-453-07", "kf-453-08")
        extra["findings"].append(finding)
        extra_runbook = RUNBOOK.replace(
            "Known-failure assignment: `kf-453-07` -> Step 4",
            "Known-failure assignment: `kf-453-07` -> Step 4\n"
            "Known-failure assignment: `kf-453-08` -> Step 4",
        )
        self.assertIn("K006", self._codes(extra, runbook=extra_runbook))

        self.assertIn("K006", self._codes(expected_ids=()))
        self.assertIn("K006", self._codes(expected_ids=["kf-453-01", []]))
        self.assertIn(
            "K006",
            self._codes(expected_ids=["kf-453-01", "kf-453-01"]),
        )

        def unbounded_ids():
            index = 0
            while True:
                yield f"kf-unbounded-{index}"
                index += 1

        self.assertIn("K006", self._codes(expected_ids=unbounded_ids()))

    def test_guard_paths_are_nonempty_unique_portable_and_confined(self):
        for path in (
            "/tmp/test.py",
            "../test.py",
            "tests/../test.py",
            "tests\\test.py",
            "tests//test.py",
            "./tests/test.py",
            "tests/$(touch-pwn).py",
            "tests/`touch-pwn`.py",
            "tests/guard\u2028other.py",
            "",
        ):
            value = inventory_object()
            value["findings"][0]["guard_paths"] = [path]
            with self.subTest(path=path):
                self.assertIn("K007", self._codes(value))
        value = inventory_object()
        path = value["findings"][0]["guard_paths"][0]
        value["findings"][0]["guard_paths"] = [path, path]
        self.assertIn("K007", self._codes(value))
        value = inventory_object()
        path = value["findings"][0]["guard_paths"][0]
        value["findings"][0]["guard_paths"] = [path, path.upper()]
        self.assertIn("K007", self._codes(value))
        value = inventory_object()
        value["findings"][0]["guard_paths"] = [
            "tests/cafe\u0301.py",
            "tests/caf\u00e9.py",
        ]
        self.assertIn("K007", self._codes(value))

    def test_command_substitution_is_not_a_portable_runner_path(self):
        for runner in (
            "plugins/hexaemeron/tests/$(touch-pwn).py",
            "plugins/hexaemeron/tests/`touch-pwn`.py",
        ):
            value = inventory_object()
            finding = value["findings"][0]
            reporter = "plugins/hexaemeron/tests/emit_issue_453_guard_report.py"
            finding["guard_paths"] = [
                runner if path == reporter else path for path in finding["guard_paths"]
            ]
            finding["test_command"] = (
                f"python3 {runner} --case kf-453-01 --report {{report}}"
            )
            finding["green_command"] = (
                f"python3 {runner} --case kf-453-01 --report "
                ".elenchus/issue-453-kf-453-01-green.json"
            )
            with self.subTest(runner=runner):
                self.assertIn("K007", self._codes(value))

    def test_test_command_has_one_exact_report_argument(self):
        cases = (
            "python3 runner.py",
            "python3 runner.py --report={report}",
            "python3 runner.py --report {report} {report}",
            "python3 runner.py --report '{report",
            "env python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report {report}",
            "bash -c 'python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report {report}'",
            "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --report {report} --case kf-453-01",
            "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report {report} --verbose",
            "python3 " + "x" * 4096,
            "python3 " + " ".join(f"arg-{index}" for index in range(17)),
            "python3\u2028plugins/hexaemeron/tests/emit_issue_453_guard_report.py "
            "--case kf-453-01 --report {report}",
            "",
        )
        for command in cases:
            value = inventory_object()
            value["findings"][0]["test_command"] = command
            with self.subTest(command=command):
                self.assertIn("K008", self._codes(value))

    def test_commands_bind_the_reporter_case_and_declared_green_path(self):
        mutations = (
            ("test_command", "python3 other.py --case kf-453-01 --report {report}"),
            ("test_command", "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report {report}"),
            ("test_command", "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --case kf-453-01 --report {report}"),
            ("green_command", "python3 other.py --case kf-453-01 --report .elenchus/issue-453-kf-453-01-green.json"),
            ("green_command", "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report .elenchus/issue-453-kf-453-01-green.json"),
            ("green_command", "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report .elenchus/wrong.json"),
        )
        for field, command in mutations:
            value = inventory_object()
            value["findings"][0][field] = command
            with self.subTest(field=field, command=command):
                self.assertIn("K008" if field == "test_command" else "K009", self._codes(value))

    def test_report_contract_and_green_command_are_closed(self):
        value = inventory_object()
        value["findings"][0]["report_format"] = "tap-v1"
        self.assertIn("K009", self._codes(value))
        value = inventory_object()
        value["findings"][0]["report_format"] = []
        self.assertIn("K009", self._codes(value))
        value = inventory_object()
        value["findings"][0]["expected_guard_verdict"] = "passed"
        self.assertIn("K009", self._codes(value))
        for path in (
            "/tmp/report.json",
            "../report.json",
            ".elenchus\\report.json",
            "reports/report.json",
            ".elenchus",
        ):
            value = inventory_object()
            value["findings"][0]["report_file"] = path
            with self.subTest(path=path):
                self.assertIn("K009", self._codes(value))
        value = inventory_object()
        value["findings"][0]["green_command"] = ""
        self.assertIn("K009", self._codes(value))

    def test_report_and_green_paths_are_unique_across_the_inventory(self):
        value = inventory_object()
        value["findings"][1]["report_file"] = value["findings"][0]["report_file"]
        self.assertIn("K009", self._codes(value))

        value = inventory_object()
        value["findings"][1]["report_file"] = (
            ".elenchus/issue-453-kf-453-01-green.json"
        )
        value["findings"][1]["green_command"] = (
            "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py "
            "--case kf-453-02 --report "
            ".elenchus/issue-453-kf-453-01-green-green.json"
        )
        self.assertIn("K009", self._codes(value))

        value = inventory_object()
        report = value["findings"][0]["report_file"].upper()
        value["findings"][1]["report_file"] = report
        green = self.checker._expected_green_report(report)
        value["findings"][1]["green_command"] = (
            "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py "
            f"--case kf-453-02 --report {green}"
        )
        self.assertIn("K009", self._codes(value))

        value = inventory_object()
        for finding, report in zip(
            value["findings"][:2],
            (".elenchus/cafe\u0301.json", ".elenchus/caf\u00e9.json"),
        ):
            finding["report_file"] = report
            green = self.checker._expected_green_report(report)
            finding["green_command"] = (
                "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py "
                f"--case {finding['id']} --report {green}"
            )
        self.assertIn("K009", self._codes(value))

    def test_each_finding_is_assigned_to_one_real_runbook_step(self):
        for step in (0, 5, -1, True, "1"):
            value = inventory_object()
            value["findings"][0]["consuming_step"] = step
            with self.subTest(step=step):
                self.assertIn("K010", self._codes(value))
        duplicate_step = RUNBOOK + "\n## Step 1: Duplicate\n"
        self.assertIn("K010", self._codes(runbook=duplicate_step))
        self.assertIn("K010", self._codes(runbook="# No steps\n"))

        value = inventory_object()
        value["findings"][0]["consuming_step"] = 2
        self.assertIn("K010", self._codes(value))

        fenced = RUNBOOK + (
            "\n```markdown\n"
            "## Step 99: Not a real step\n"
            "Known-failure assignment: `kf-not-real` -> Step 99\n"
            "```\n"
        )
        self.assertEqual([], self._codes(runbook=fenced))

        misplaced = RUNBOOK.replace(
            "Known-failure assignment: `kf-453-01` -> Step 1\n",
            "```markdown\n"
            "Known-failure assignment: `kf-453-01` -> Step 1\n"
            "```\n",
        )
        self.assertIn("K010", self._codes(runbook=misplaced))

        repeated = RUNBOOK.replace(
            "Known-failure assignment: `kf-453-02` -> Step 2",
            "Known-failure assignment: `kf-453-02` -> Step 2\n"
            "Known-failure assignment: `kf-453-01` -> Step 2",
        )
        self.assertIn("K010", self._codes(runbook=repeated))

        wrong_declared_step = RUNBOOK.replace(
            "Known-failure assignment: `kf-453-01` -> Step 1",
            "Known-failure assignment: `kf-453-01` -> Step 2",
        )
        self.assertIn("K010", self._codes(runbook=wrong_declared_step))

    def test_only_the_final_complete_exit_generation_is_active(self):
        first = runbook_amendment(exit_replacement())
        files_only = runbook_amendment(
            "Complete replacement Files: Preserve the declared product paths."
        )
        final = runbook_amendment(exit_replacement())
        runbook = STEP_ONLY_RUNBOOK + first + files_only + final
        for ending in ("\n", "\r\n", "\r"):
            candidate = runbook.replace("\n", ending)
            with self.subTest(ending=repr(ending)):
                steps, assigned, error = self.checker._runbook_contract(candidate)
                self.assertIsNone(error)
                self.assertEqual(EXPECTED_IDS, assigned)
                self.assertEqual(
                    {
                        1: {"kf-453-01"},
                        2: {"kf-453-02"},
                        3: {"kf-453-03", "kf-453-04", "kf-453-05"},
                        4: {"kf-453-06", "kf-453-07"},
                    },
                    steps,
                )
                self.assertEqual([], self._codes(runbook=candidate))

        compact_files_amendment = (
            "\n### Amendment -- 2026-09-05\n"
            "**What changed.** Complete replacement Files: Keep them.\n"
            "**Why.** The file set changed.\n"
            "**Steps touched.** Step 1's Files.\n"
            "**Still holding.** Steps 2 through 4 still hold.\n"
        )
        self.assertEqual(
            [], self._codes(runbook=RUNBOOK + compact_files_amendment)
        )

    def test_receipted_empty_then_locked_exit_generation_history_is_clean(self):
        runbook = COMMITTED_RUNBOOK.read_text(encoding="utf-8")

        lines = [
            physical.rstrip("\r\n")
            for physical in self.checker._markdown_physical_lines(runbook)
        ]
        fenced, fence_error = self.checker._runbook_fence_mask(lines)
        self.assertIsNone(fence_error)
        self.assertIsNotNone(fenced)
        _baseline, generations, final_generation, amendment_error = (
            self.checker._amendment_exit_scopes(lines, fenced)
        )
        self.assertIsNone(amendment_error)
        self.assertEqual(12, final_generation)
        self.assertEqual(
            [0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
            [
                sum(
                    self.checker.KNOWN_FAILURE_ASSIGNMENT.fullmatch(lines[index])
                    is not None
                    for index, scoped_generation in generations.items()
                    if scoped_generation == generation
                )
                for generation in range(1, 13)
            ],
        )
        steps, assigned, error = self.checker._runbook_contract(runbook)
        self.assertIsNone(error)
        self.assertEqual(EXPECTED_IDS, assigned)
        self.assertEqual(
            {
                1: {"kf-453-01"},
                2: {"kf-453-02"},
                3: {"kf-453-03", "kf-453-04", "kf-453-05"},
                4: {"kf-453-06", "kf-453-07"},
                5: set(),
            },
            steps,
        )
        self.assertEqual([], self._codes(runbook=runbook))

    def test_final_exit_generation_never_falls_back(self):
        complete = runbook_amendment(exit_replacement())
        empty = runbook_amendment(
            "Complete replacement Exit: No assignment records are carried."
        )
        _steps, assigned, error = self.checker._runbook_contract(
            STEP_ONLY_RUNBOOK + complete + empty
        )
        self.assertIsNotNone(error)
        self.assertEqual(set(), assigned)
        self.assertIn(
            "K010",
            self._codes(runbook=STEP_ONLY_RUNBOOK + complete + empty),
        )

        incomplete_block = "\n".join(ASSIGNMENT_BLOCK.splitlines()[:-1])
        incomplete = runbook_amendment(exit_replacement(incomplete_block))
        _steps, assigned, error = self.checker._runbook_contract(
            STEP_ONLY_RUNBOOK + complete + incomplete
        )
        self.assertIsNotNone(error)
        self.assertEqual(set(), assigned)
        self.assertIn(
            "K010",
            self._codes(runbook=STEP_ONLY_RUNBOOK + complete + incomplete),
        )

    def test_locked_exit_generation_map_refuses_drift_but_not_reordering(self):
        complete = runbook_amendment(exit_replacement())
        partial = "\n".join(ASSIGNMENT_BLOCK.splitlines()[:-1])
        extra = (
            ASSIGNMENT_BLOCK
            + "\nKnown-failure assignment: `kf-extra` -> Step 1"
        )
        reassigned = ASSIGNMENT_BLOCK.replace(
            "Known-failure assignment: `kf-453-01` -> Step 1",
            "Known-failure assignment: `kf-453-01` -> Step 2",
        )
        hostile_successors = (
            "",
            partial,
            extra,
            reassigned,
        )
        for successor in hostile_successors:
            if successor:
                replacement = exit_replacement(successor)
            else:
                replacement = "Complete replacement Exit: No assignments."
            candidate = (
                STEP_ONLY_RUNBOOK
                + complete
                + runbook_amendment(replacement)
            )
            with self.subTest(successor=successor[-80:]):
                _steps, assigned, error = self.checker._runbook_contract(candidate)
                self.assertIsNotNone(error)
                self.assertEqual(set(), assigned)
                self.assertIn("K010", self._codes(runbook=candidate))

        reordered = "\n".join(reversed(ASSIGNMENT_BLOCK.splitlines()))
        candidate = (
            STEP_ONLY_RUNBOOK
            + complete
            + runbook_amendment(exit_replacement(reordered))
        )
        steps, assigned, error = self.checker._runbook_contract(candidate)
        self.assertIsNone(error)
        self.assertEqual(EXPECTED_IDS, assigned)
        self.assertEqual(
            {
                1: {"kf-453-01"},
                2: {"kf-453-02"},
                3: {"kf-453-03", "kf-453-04", "kf-453-05"},
                4: {"kf-453-06", "kf-453-07"},
            },
            steps,
        )
        self.assertEqual([], self._codes(runbook=candidate))

    def test_records_outside_exit_generations_remain_active_and_fail_closed(self):
        final = runbook_amendment(exit_replacement())
        ordinary_extra = (
            STEP_ONLY_RUNBOOK
            + "\nKnown-failure assignment: `kf-extra` -> Step 1\n"
            + final
        )
        _steps, assigned, error = self.checker._runbook_contract(ordinary_extra)
        self.assertIsNone(error)
        self.assertEqual(EXPECTED_IDS | {"kf-extra"}, assigned)
        self.assertIn("K006", self._codes(runbook=ordinary_extra))

        files_record = runbook_amendment(
            "Complete replacement Files: Keep these files.\n\n"
            "Known-failure assignment: `kf-extra` -> Step 1\n\n"
            "No other file changes apply."
        )
        self.assertIn(
            "K006",
            self._codes(runbook=STEP_ONLY_RUNBOOK + final + files_record),
        )

        fenced_exit_decoy = runbook_amendment(
            "Complete replacement Files: Keep these files.\n\n"
            "```text\n"
            "Complete replacement Exit: This is only an example.\n"
            "```\n\n"
            "Known-failure assignment: `kf-extra` -> Step 1\n\n"
            "No other file changes apply."
        )
        _steps, assigned, error = self.checker._runbook_contract(
            STEP_ONLY_RUNBOOK + fenced_exit_decoy + final
        )
        self.assertIsNone(error)
        self.assertEqual(EXPECTED_IDS | {"kf-extra"}, assigned)
        self.assertIn(
            "K006",
            self._codes(
                runbook=STEP_ONLY_RUNBOOK + fenced_exit_decoy + final
            ),
        )

        split_fenced_marker = runbook_amendment(
            "Complete replacement Files: Keep these files.\n\n"
            "Complete replacement\n"
            "```text\n"
            "This fence breaks structural continuity.\n"
            "```\n"
            "Exit: This is not one contiguous clause.\n\n"
            "Known-failure assignment: `kf-extra` -> Step 1\n\n"
            "No other file changes apply."
        )
        self.assertIn(
            "K010",
            self._codes(
                runbook=STEP_ONLY_RUNBOOK + split_fenced_marker + final
            ),
        )

        inline_exit_decoy = runbook_amendment(
            "Complete replacement Files: Keep these files.\n\n"
            "`Complete replacement Exit: This is only an example.`\n\n"
            "Known-failure assignment: `kf-extra` -> Step 1\n\n"
            "No other file changes apply."
        )
        _steps, assigned, error = self.checker._runbook_contract(
            STEP_ONLY_RUNBOOK + inline_exit_decoy + final
        )
        self.assertIsNone(error)
        self.assertEqual(EXPECTED_IDS | {"kf-extra"}, assigned)
        self.assertIn(
            "K006",
            self._codes(
                runbook=STEP_ONLY_RUNBOOK + inline_exit_decoy + final
            ),
        )

        link_title_exit_decoy = runbook_amendment(
            "Complete replacement Files: Keep these files.\n\n"
            "[example](https://example.invalid \"\n"
            "Complete replacement Exit: This title is not authority.\n"
            "\")\n\n"
            "Known-failure assignment: `kf-extra` -> Step 1\n\n"
            "No other file changes apply."
        )
        self.assertIn(
            "K010",
            self._codes(
                runbook=STEP_ONLY_RUNBOOK + link_title_exit_decoy + final
            ),
        )

        exit_then_files = runbook_amendment(
            exit_replacement()
            + "\n\nComplete replacement Files: Keep these files.\n\n"
            "Known-failure assignment: `kf-453-01` -> Step 1\n\n"
            "No other file changes apply."
        )
        _steps, _assigned, error = self.checker._runbook_contract(
            STEP_ONLY_RUNBOOK + exit_then_files
        )
        self.assertIsNotNone(error)

        hidden_what_field = (
            "\n### Amendment -- 2026-09-05\n\n"
            "[example](https://example.invalid \"\n"
            "**What changed.** Complete replacement Exit: Historical.\n"
            "\")\n\n"
            "Known-failure assignment: `kf-extra` -> Step 1\n\n"
            "**Why.** This field is visible.\n"
            "**Steps touched.** Step 1's Exit.\n"
            "**Still holding.** Steps 2 through 4 still hold.\n"
        )
        hidden_tail_fields = (
            "\n### Amendment -- 2026-09-05\n\n"
            "**What changed.** Complete replacement Exit: Historical.\n\n"
            "Known-failure assignment: `kf-extra` -> Step 1\n\n"
            "[example](https://example.invalid \"\n"
            "**Why.** This field is hidden in a link title.\n"
            "**Steps touched.** Step 1's Exit.\n"
            "**Still holding.** Steps 2 through 4 still hold.\n"
            "\")\n"
        )
        malformed_amendments = (
            runbook_amendment(
                "Complete replacement Exit: First. "
                "Complete replacement Exit: Second."
            ),
            runbook_amendment("Complete replacement Exit : malformed"),
            runbook_amendment("An additive runbook claim."),
            "\n### Amendment -- 2026-09-05\n\n"
            "**What changed.** Complete replacement Exit: incomplete\n",
            runbook_amendment(exit_replacement()) + "\n## Step 5: Too late\n",
            hidden_what_field,
            hidden_tail_fields,
        )
        for amendment in malformed_amendments:
            with self.subTest(amendment=amendment[:70]):
                _steps, _assigned, error = self.checker._runbook_contract(
                    STEP_ONLY_RUNBOOK + amendment
                )
                self.assertIsNotNone(error)

        fenced_decoy = RUNBOOK + (
            "\n```markdown\n"
            + runbook_amendment(exit_replacement()).lstrip("\n")
            + "```\n"
        )
        self.assertEqual([], self._codes(runbook=fenced_decoy))

        superseded_hostile = (
            "Known-failure assignment: kf-malformed -> Step 1",
            "<!-- hidden assignment -->",
            "`unmatched inline code",
        )
        for hostile in superseded_hostile:
            first = runbook_amendment(exit_replacement(hostile))
            with self.subTest(hostile=hostile):
                self.assertIn(
                    "K010",
                    self._codes(runbook=STEP_ONLY_RUNBOOK + first + final),
                )

    def test_only_exact_visible_assignment_lines_are_authoritative(self):
        assignment = "Known-failure assignment: `kf-453-01` -> Step 1"
        hostile_replacements = (
            "<!--\n" + assignment + "\n-->",
            "This step does not consume kf-453-01.",
            "See [kf-453-01](https://example.invalid/kf-453-01).",
        )
        for replacement in hostile_replacements:
            hostile = RUNBOOK.replace(assignment, replacement)
            with self.subTest(replacement=replacement):
                self.assertIn("K010", self._codes(runbook=hostile))

        unclosed_comment = RUNBOOK.replace(assignment, "<!--\n" + assignment)
        self.assertIn("K010", self._codes(runbook=unclosed_comment))

        second_comment = RUNBOOK.replace(
            assignment,
            "<!-- closed --> <!--\n" + assignment + "\n-->",
        )
        self.assertIn("K010", self._codes(runbook=second_comment))

        overlapping_code_spans = RUNBOOK.replace(
            assignment,
            "`x``y`<!--``\n" + assignment + "\n-->",
        )
        self.assertEqual(
            [(0, 6)],
            self.checker._inline_code_spans("`x``y`<!--``"),
        )
        self.assertIn("K010", self._codes(runbook=overlapping_code_spans))

        escaped_inside_code = RUNBOOK.replace(
            assignment,
            "`x\\`<!--`\n" + assignment + "\n-->",
        )
        self.assertEqual(
            [(0, 4)],
            self.checker._inline_code_spans("`x\\`<!--`"),
        )
        self.assertIn("K010", self._codes(runbook=escaped_inside_code))

        multiline_code_span = RUNBOOK.replace(
            assignment,
            "`x\n`<!--`\n" + assignment + "\n-->",
        )
        self.assertIn("K010", self._codes(runbook=multiline_code_span))

        for delimiter in ("`", "``"):
            hidden_assignment = RUNBOOK.replace(
                assignment,
                f"{delimiter}\n{assignment}\n{delimiter}",
            )
            with self.subTest(multiline_delimiter=delimiter):
                self.assertIn("K010", self._codes(runbook=hidden_assignment))

        image_alt_assignment = RUNBOOK.replace(
            assignment,
            "![\n" + assignment + "\n](https://example.invalid/x)",
        )
        self.assertIn("K010", self._codes(runbook=image_alt_assignment))

        hidden_link_cases = (
            "[foo](https://example.invalid \"\n" + assignment + "\n\")",
            "[foo]: /url \"\n" + assignment + "\n\"",
            "[\n" + assignment + "\n]: /url",
        )
        for hidden in hidden_link_cases:
            hostile = RUNBOOK.replace(assignment, hidden)
            with self.subTest(hidden_link=hidden[:30]):
                self.assertIn("K010", self._codes(runbook=hostile))

        for visible_bracket in (
            "[foo](https://example.invalid)",
            "[foo]: https://example.invalid",
        ):
            with self.subTest(visible_bracket=visible_bracket):
                self.assertIn(
                    "K010",
                    self._codes(runbook=RUNBOOK + "\n" + visible_bracket + "\n"),
                )

        for admitted_example in (
            RUNBOOK + "\n`[one-line code]`\n",
            RUNBOOK + "\n```text\n[fenced example]\n```\n",
        ):
            with self.subTest(admitted_example=admitted_example[-40:]):
                self.assertEqual([], self._codes(runbook=admitted_example))

        study_with_brackets = study_text(encoded(inventory_object())).replace(
            "# Study\n\n",
            "# Study\n\n[ordinary study link](https://example.invalid)\n\n",
        )
        self.assertEqual([], self._codes(study=study_with_brackets))

        list_scoped_fence = RUNBOOK + (
            "\n- item\n\n"
            "  ```\n"
            "Known-failure assignment: `kf-extra` -> Step 1\n"
            "  ```\n"
        )
        self.assertIn("K010", self._codes(runbook=list_scoped_fence))

        list_scoped_step = RUNBOOK + (
            "\n- item\n\n"
            "  ## Step 99: nested\n"
            "Known-failure assignment: `kf-extra` -> Step 99\n"
        )
        self.assertIn("K010", self._codes(runbook=list_scoped_step))

        many_visible_spans = "`<`" * 50_000
        surface, surface_error = self.checker._markdown_surface(many_visible_spans)
        self.assertEqual(many_visible_spans, surface)
        self.assertIsNone(surface_error)
        surface, surface_error = self.checker._markdown_surface("`![visible]`")
        self.assertEqual("`![visible]`", surface)
        self.assertIsNone(surface_error)

        step_block = (
            "## Step 1: Define the inventory\n\n"
            "Known-failure assignment: `kf-453-01` -> Step 1"
        )
        for tag in ("pre", "div", "guard-record"):
            hidden_step = RUNBOOK.replace(
                step_block,
                f"<{tag}>\n{step_block}\n</{tag}>\n",
            )
            with self.subTest(raw_html=tag):
                self.assertIn("K010", self._codes(runbook=hidden_step))

        phantom = (
            "# One physical line\u2028## Step 1: Phantom\u2028"
            "Known-failure assignment: `kf-453-01` -> Step 1"
        )
        self.assertIn("K010", self._codes(runbook=phantom))

        malformed_extra = RUNBOOK + (
            "\nKnown-failure assignment: kf-extra -> Step 1\n"
        )
        self.assertIn("K010", self._codes(runbook=malformed_extra))

        extra_assignment = "Known-failure assignment: `kf-extra` -> Step 1"
        hostile_openers = (
            "    <!--",
            "paragraph\n<guard-record>",
            "<guard-record ???>",
            "<x a=?>",
            "<pre/foo",
            "paragraph <pre>",
            "<![cdata[",
            "<!foo",
        )
        for opener in hostile_openers:
            hostile = RUNBOOK + "\n" + opener + "\n" + extra_assignment + "\n"
            with self.subTest(raw_html_extra=opener):
                self.assertIn("K010", self._codes(runbook=hostile))

        first_assignment = "Known-failure assignment: `kf-453-01` -> Step 1"
        through_eof_fence = RUNBOOK.replace(
            first_assignment,
            "```text\n```\u00a0\n" + first_assignment,
        )
        self.assertIn("K010", self._codes(runbook=through_eof_fence))

        visible_after_bad_info = RUNBOOK + (
            "\n```bad`info\n"
            "Known-failure assignment: `kf-extra` -> Step 1\n"
        )
        self.assertIn("K010", self._codes(runbook=visible_after_bad_info))

        for token in ("0", "01", "9" * 5000):
            hostile = RUNBOOK.replace("## Step 1:", f"## Step {token}:")
            with self.subTest(step_token=token[:20]):
                self.assertIn("K010", self._codes(runbook=hostile))

    def test_nonempty_findings_require_a_null_no_findings_claim(self):
        value = inventory_object()
        value["no_known_findings"] = {
            "source_views": [],
            "consuming_step": 1,
            "surveyor_assertion": "no-known-findings",
        }
        self.assertIn("K011", self._codes(value))

    def test_empty_inventory_requires_the_closed_digest_bound_claim(self):
        value = inventory_object()
        value["findings"] = []
        self.assertIn(
            "K011",
            self._codes(value, expected_ids=(), runbook=NO_FINDINGS_RUNBOOK),
        )

        bound_views = [
            {
                "id": view["id"],
                "source_sha256": view["source_sha256"],
                "view_sha256": view["view_sha256"],
            }
            for view in value["source_views"]
        ]
        claim = {
            "source_views": bound_views,
            "consuming_step": 1,
            "surveyor_assertion": "no-known-findings",
        }
        value["no_known_findings"] = claim
        self.assertEqual(
            self._codes(value, expected_ids=(), runbook=NO_FINDINGS_RUNBOOK),
            [],
        )

        mutations = []
        missing_view = copy.deepcopy(value)
        missing_view["no_known_findings"]["source_views"].pop()
        mutations.append(missing_view)
        stale_digest = copy.deepcopy(value)
        stale_digest["no_known_findings"]["source_views"][0]["view_sha256"] = "0" * 64
        mutations.append(stale_digest)
        bad_step = copy.deepcopy(value)
        bad_step["no_known_findings"]["consuming_step"] = 5
        mutations.append(bad_step)
        extra = copy.deepcopy(value)
        extra["no_known_findings"]["extra"] = True
        mutations.append(extra)
        for mutation in mutations:
            with self.subTest(mutation=mutation["no_known_findings"]):
                self.assertIn(
                    "K011",
                    self._codes(
                        mutation,
                        expected_ids=(),
                        runbook=NO_FINDINGS_RUNBOOK,
                    ),
                )

    def test_finding_and_guard_path_caps_refuse_the_unchecked_tail(self):
        value = inventory_object()
        template = value["findings"][0]
        value["findings"] = []
        for index in range(129):
            finding = copy.deepcopy(template)
            finding["id"] = f"kf-cap-{index:03d}"
            value["findings"].append(finding)
        self.assertIn("K012", self._codes(value))

        value = inventory_object()
        value["findings"][0]["guard_paths"] = [
            f"tests/guard-{index:04d}.py" for index in range(4097)
        ]
        self.assertIn("K012", self._codes(value))

    def test_unreadable_or_oversized_inputs_refuse(self):
        oversized = "# Study\n" + ("x" * (2 * 1024 * 1024 + 1))
        self.assertIn("K000", self._codes(study=oversized))
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.md"
            found = self.checker.check(missing, missing, REPOSITORY_ROOT)
        self.assertTrue(found)
        self.assertTrue(all(finding.code == "K000" for finding in found))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            study_path = root / "study.md"
            runbook_path = root / "missing-runbook.md"
            study_path.write_text(
                study_text(encoded(inventory_object())), encoding="utf-8"
            )
            found = self.checker.check(
                study_path,
                runbook_path,
                REPOSITORY_ROOT,
                expected_ids=EXPECTED_IDS,
            )
            self.assertEqual(["K000"], [finding.code for finding in found])
            self.assertEqual(runbook_path, found[0].path)
            self.assertIn("runbook", found[0].message)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            study_path = root / "study.md"
            runbook_path = root / "runbook.md"
            study_path.write_text(oversized, encoding="utf-8")
            runbook_path.write_text(RUNBOOK, encoding="utf-8")
            found = self.checker.check(
                study_path,
                runbook_path,
                REPOSITORY_ROOT,
                expected_ids=EXPECTED_IDS,
            )
            self.assertEqual(["K000"], [finding.code for finding in found])
            study_path.write_text(
                study_text(encoded(inventory_object())), encoding="utf-8"
            )
            self.assertEqual(
                [],
                self.checker.check(
                    study_path,
                    runbook_path,
                    REPOSITORY_ROOT,
                    expected_ids=EXPECTED_IDS,
                ),
            )

    def test_synopsis_header_uses_commonmark_physical_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            self._copy_source_repository(repository)
            value = inventory_object()
            view = value["source_views"][0]
            view_path = repository / view["path"]
            text = view_path.read_text(encoding="utf-8")
            text = text.replace("\n", "\u2028", 1)
            view_path.write_text(text, encoding="utf-8")
            view["view_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            found = self._findings(value, repository=repository)
        self.assertEqual(["K005"], [finding.code for finding in found])
        self.assertEqual(view_path, found[0].path)
        self.assertIn("source_sha256", found[0].message)

    def test_secure_read_primitives_are_required(self):
        with mock.patch.object(self.checker, "_secure_read_primitives", return_value=False):
            self.assertEqual(["K000"], self._codes())

    def test_input_and_source_symlinks_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular = root / "regular-study.md"
            regular.write_text(study_text(encoded(inventory_object())), encoding="utf-8")
            linked = root / "study.md"
            linked.symlink_to(regular.name)
            runbook = root / "runbook.md"
            runbook.write_text(RUNBOOK, encoding="utf-8")
            found = self.checker.check(
                linked,
                runbook,
                REPOSITORY_ROOT,
                expected_ids=EXPECTED_IDS,
            )
            self.assertEqual(["K000"], [finding.code for finding in found])

        for alias_kind in ("leaf", "directory"):
            with self.subTest(alias_kind=alias_kind), tempfile.TemporaryDirectory() as directory:
                repository = Path(directory)
                self._copy_source_repository(repository)
                if alias_kind == "leaf":
                    relative = inventory_object()["source_views"][0]["path"]
                    target = repository / relative
                    saved = target.with_name(target.name + ".saved")
                    target.rename(saved)
                    target.symlink_to(saved.name)
                else:
                    target = repository / "audit"
                    saved = repository / "audit-real"
                    target.rename(saved)
                    target.symlink_to(saved.name, target_is_directory=True)
                self.assertIn("K005", self._codes(repository=repository))

    def test_a_fifo_swapped_in_at_leaf_open_refuses_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            study = root / "study.md"
            runbook = root / "runbook.md"
            study.write_text(study_text(encoded(inventory_object())), encoding="utf-8")
            runbook.write_text(RUNBOOK, encoding="utf-8")
            original_open = self.checker.os.open
            swapped = False

            def racing_open(path, flags, *args, **kwargs):
                nonlocal swapped
                if not swapped and Path(path) == study and "dir_fd" not in kwargs:
                    swapped = True
                    study.unlink()
                    os.mkfifo(study)
                return original_open(path, flags, *args, **kwargs)

            with (
                mock.patch.object(self.checker, "_secure_read_primitives", return_value=True),
                mock.patch.object(self.checker.os, "open", side_effect=racing_open),
            ):
                found = self.checker.check(
                    study,
                    runbook,
                    REPOSITORY_ROOT,
                    expected_ids=EXPECTED_IDS,
                )
            self.assertTrue(swapped)
            self.assertEqual(["K000"], [finding.code for finding in found])

    def test_study_and_runbook_replacement_at_the_final_boundary_refuse(self):
        for target_name in ("study.md", "runbook.md"):
            with self.subTest(target=target_name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                study = root / "study.md"
                runbook = root / "runbook.md"
                study.write_text(study_text(encoded(inventory_object())), encoding="utf-8")
                runbook.write_text(RUNBOOK, encoding="utf-8")
                target = root / target_name
                original_read = self.checker._stable_file
                target_reads = 0

                def replacing_read(path, limit=self.checker.MAX_BYTES):
                    nonlocal target_reads
                    path = Path(path)
                    if path == target:
                        target_reads += 1
                        if target_reads == 2:
                            replacement = target.with_name(target.name + ".replacement")
                            replacement.write_bytes(target.read_bytes() + b"\n")
                            os.replace(replacement, target)
                    return original_read(path, limit)

                with mock.patch.object(self.checker, "_stable_file", side_effect=replacing_read):
                    found = self.checker.check(
                        study,
                        runbook,
                        REPOSITORY_ROOT,
                        expected_ids=EXPECTED_IDS,
                    )
                self.assertEqual(2, target_reads)
                self.assertEqual(["K000"], [finding.code for finding in found])
                self.assertEqual(target, found[0].path)
                self.assertIn(target_name.removesuffix(".md"), found[0].message)

    def test_source_and_view_replacement_at_the_final_boundary_refuse(self):
        for target_kind in ("source", "view"):
            with self.subTest(target_kind=target_kind), tempfile.TemporaryDirectory() as directory:
                repository = Path(directory)
                source_path = self._copy_source_repository(repository)
                view = inventory_object()["source_views"][0]
                relative = source_path if target_kind == "source" else view["path"]
                target = repository / relative
                replace_at = 2 if target_kind == "source" else 3
                original_read = self.checker._confined_file
                target_reads = 0

                def replacing_read(root, candidate, limit=self.checker.MAX_BYTES):
                    nonlocal target_reads
                    if candidate == relative:
                        target_reads += 1
                        if target_reads == replace_at:
                            replacement = target.with_name(target.name + ".replacement")
                            replacement.write_bytes(target.read_bytes() + b"\n")
                            os.replace(replacement, target)
                    return original_read(root, candidate, limit)

                with mock.patch.object(
                    self.checker,
                    "_confined_file",
                    side_effect=replacing_read,
                ):
                    found = self._findings(repository=repository)
                self.assertEqual(replace_at, target_reads)
                self.assertEqual(["K005"], [finding.code for finding in found])
                self.assertEqual(target, found[0].path)
                self.assertIn(view["id"], found[0].message)
                self.assertIn(f"{target_kind}_sha256", found[0].message)

    def test_reporter_refuses_nonpositive_or_nonordinary_results(self):
        def result(**counts):
            candidate = unittest.TestResult()
            candidate.testsRun = counts.pop("testsRun", 1)
            for field in (
                "failures",
                "errors",
                "skipped",
                "expectedFailures",
                "unexpectedSuccesses",
            ):
                setattr(candidate, field, [object()] * counts.pop(field, 0))
            self.assertEqual({}, counts)
            return candidate

        clean = result()
        self.assertTrue(self.emitter.result_is_clean(clean))
        dirty_results = (
            result(testsRun=0),
            result(failures=1),
            result(errors=1),
            result(skipped=1),
            result(expectedFailures=1),
            result(unexpectedSuccesses=1),
        )
        for dirty in dirty_results:
            with self.subTest(payload=self.emitter.result_payload(dirty)):
                self.assertFalse(self.emitter.result_is_clean(dirty))
                fake_unittest = mock.Mock()
                fake_unittest.defaultTestLoader.loadTestsFromName.return_value = object()
                fake_unittest.TextTestRunner.return_value.run.return_value = dirty
                with (
                    mock.patch.object(self.emitter, "repository_cwd", return_value=REPOSITORY_ROOT),
                    mock.patch.object(self.emitter, "report_target", return_value=object()),
                    mock.patch.object(self.emitter, "missing_surface_suite", return_value=None),
                    mock.patch.object(self.emitter, "write_report"),
                    mock.patch.object(self.emitter, "unittest", fake_unittest),
                    redirect_stdout(io.StringIO()),
                ):
                    status = self.emitter.main(
                        [
                            "--case",
                            "kf-453-01",
                            "--report",
                            ".elenchus/hostile-result.json",
                        ]
                    )
                self.assertEqual(1, status)

    def test_reporter_refuses_a_different_cwd_even_with_copied_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory)
            for relative in self.emitter.REQUIRED_SURFACE:
                target = other / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("copied\n", encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(other)
                with redirect_stderr(io.StringIO()):
                    status = self.emitter.main(
                        [
                            "--case",
                            "kf-453-01",
                            "--report",
                            ".elenchus/copied-surface.json",
                        ]
                    )
            finally:
                os.chdir(previous)
        self.assertEqual(2, status)


if __name__ == "__main__":
    unittest.main()
