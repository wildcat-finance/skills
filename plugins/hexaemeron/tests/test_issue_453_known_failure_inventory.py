"""Guards for the source-bound Protasis known-failure inventory."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]
SCRIPT = PLUGIN_ROOT / "skills/protasis/scripts/known_failure_inventory.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures/issue-453/inventory.json"

RUNBOOK = """# Known-failure inoculation runbook

## Step 1: Define the inventory

## Step 2: Open the inoculation phase

## Step 3: Retain the guard evidence

## Step 4: Prove recovery and final green
"""


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

    def _findings(
        self,
        value: dict | None = None,
        *,
        body: str | None = None,
        study: str | None = None,
        runbook: str = RUNBOOK,
        repository: Path = REPOSITORY_ROOT,
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
            return self.checker.check(study_path, runbook_path, repository)

    def _codes(self, *args, **kwargs):
        return [finding.code for finding in self._findings(*args, **kwargs)]

    def test_kf_453_01_closed_inventory_is_source_bound(self):
        found = self._findings()
        self.assertEqual([finding.as_dict() for finding in found], [])

    def test_exactly_one_closed_inventory_fence_is_required(self):
        body = encoded(inventory_object())
        cases = (
            "# Study without an inventory\n",
            study_text(body) + "\n" + study_text(body),
            "# Study\n\n```known-failure-inventory\n" + body,
            "# Study\n\n~~~known-failure-inventory\n" + body + "\n```\n",
        )
        for source in cases:
            with self.subTest(source=source[:40]):
                self.assertIn("K001", self._codes(study=source))

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
        for body in (duplicate, malformed, deep):
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
                self.assertIn("K005", self._codes(value))

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
        for source_ref in ("missing-colon", "unknown-source: detail", "issue-327-root:"):
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

    def test_guard_paths_are_nonempty_unique_portable_and_confined(self):
        for path in (
            "/tmp/test.py",
            "../test.py",
            "tests/../test.py",
            "tests\\test.py",
            "tests//test.py",
            "./tests/test.py",
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

    def test_test_command_has_one_exact_report_argument(self):
        cases = (
            "python3 runner.py",
            "python3 runner.py --report={report}",
            "python3 runner.py --report {report} {report}",
            "python3 runner.py --report '{report",
            "",
        )
        for command in cases:
            value = inventory_object()
            value["findings"][0]["test_command"] = command
            with self.subTest(command=command):
                self.assertIn("K008", self._codes(value))

    def test_report_contract_and_green_command_are_closed(self):
        value = inventory_object()
        value["findings"][0]["report_format"] = "tap-v1"
        self.assertIn("K009", self._codes(value))
        value = inventory_object()
        value["findings"][0]["expected_guard_verdict"] = "passed"
        self.assertIn("K009", self._codes(value))
        for path in ("/tmp/report.json", "../report.json", ".elenchus\\report.json"):
            value = inventory_object()
            value["findings"][0]["report_file"] = path
            with self.subTest(path=path):
                self.assertIn("K009", self._codes(value))
        value = inventory_object()
        value["findings"][0]["green_command"] = ""
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
        self.assertIn("K011", self._codes(value))

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
        self.assertEqual(self._codes(value), [])

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
                self.assertIn("K011", self._codes(mutation))

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


if __name__ == "__main__":
    unittest.main()
