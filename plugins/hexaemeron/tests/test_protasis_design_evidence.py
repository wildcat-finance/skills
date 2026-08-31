"""Closed candidate evidence, not prose or predicted grades, locks a design."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "protasis" / "scripts" / "design_evidence.py"

spec = importlib.util.spec_from_file_location("protasis_design_evidence", SCRIPT)
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


class DesignEvidenceCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.reports = self.root / "reports"
        self.reports.mkdir()
        self.record_path = self.root / "design-evidence.json"

    def tearDown(self):
        self.temporary.cleanup()

    def report(self, candidate, criterion, value, unit, *, name=None):
        name = name or f"{candidate}-{criterion}.json"
        path = self.reports / name
        payload = {
            "schema": design.REPORT_SCHEMA,
            "candidate": candidate,
            "criterion": criterion,
            "value": value,
            "unit": unit,
            "command": f"measure {candidate} {criterion}",
            "exit": 0,
        }
        data = (json.dumps(payload, sort_keys=True) + "\n").encode()
        path.write_bytes(data)
        return {
            "path": f"reports/{name}",
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    def base_record(self):
        criteria = [
            {
                "id": "prototype-works",
                "concern": "correctness",
                "kind": "gate",
                "stage": "selection",
                "owner": "protasis",
                "unit": "boolean",
                "comparator": "equals",
                "threshold": True,
                "blocks": "design-lock",
            },
            {
                "id": "warm-time",
                "concern": "time",
                "kind": "metric",
                "stage": "selection",
                "owner": "metron",
                "unit": "milliseconds",
                "comparator": "minimise",
                "threshold": None,
                "blocks": "design-lock",
            },
            {
                "id": "peak-rss",
                "concern": "space",
                "kind": "metric",
                "stage": "selection",
                "owner": "metron",
                "unit": "bytes",
                "comparator": "minimise",
                "threshold": None,
                "blocks": "design-lock",
            },
            {
                "id": "plugin-compatible",
                "concern": "compatibility",
                "kind": "gate",
                "stage": "selection",
                "owner": "phylax",
                "unit": "boolean",
                "comparator": "equals",
                "threshold": True,
                "blocks": "design-lock",
            },
            {
                "id": "restart-safe",
                "concern": "recovery",
                "kind": "gate",
                "stage": "conformance",
                "owner": "elenchus",
                "unit": "boolean",
                "comparator": "equals",
                "threshold": True,
                "blocks": "step:2",
            },
        ]
        values = {
            "streaming": {
                "prototype-works": (True, "boolean"),
                "warm-time": (100, "milliseconds"),
                "peak-rss": (100, "bytes"),
                "plugin-compatible": (True, "boolean"),
            },
            "buffered": {
                "prototype-works": (True, "boolean"),
                "warm-time": (200, "milliseconds"),
                "peak-rss": (200, "bytes"),
                "plugin-compatible": (True, "boolean"),
                "restart-safe": (True, "boolean"),
            },
        }
        results = []
        for candidate, observed in values.items():
            for criterion, (value, unit) in observed.items():
                results.append({
                    "candidate": candidate,
                    "criterion": criterion,
                    "state": "pass",
                    "report": self.report(candidate, criterion, value, unit),
                })
        results.append({
            "candidate": "streaming",
            "criterion": "restart-safe",
            "state": "pending",
            "resolver": "python3 tests/prove_restart.py",
            "report": "reports/streaming-restart-safe.json",
            "blocks": "step:2",
        })
        return {
            "schema": design.SCHEMA,
            "candidates": [
                {"id": "streaming", "summary": "Process one bounded window."},
                {"id": "buffered", "summary": "Hold the whole interval in memory."},
            ],
            "criteria": criteria,
            "results": results,
            "selection": {
                "candidate": "streaming",
                "rule": "unique-frontier",
                "policy_ref": None,
            },
        }

    def write_record(self, record=None):
        record = record or self.base_record()
        self.record_path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return record

    def codes(self, transition="draft"):
        return [finding.code for finding in design.check(self.record_path, transition)]

    def test_draft_design_lock_and_progressive_step_gate(self):
        self.write_record()
        self.assertEqual(self.codes(), [])
        self.assertEqual(self.codes("design-lock"), [])
        self.assertEqual(self.codes("step:1"), [])
        self.assertEqual(self.codes("step:2"), ["D008"])

        self.report(
            "streaming", "restart-safe", True, "boolean",
            name="streaming-restart-safe.json",
        )
        findings, _, consumed = design.evaluate(self.record_path, "step:2")
        self.assertEqual(findings, [])
        self.assertEqual(
            [(item["candidate"], item["criterion"]) for item in consumed],
            [("streaming", "restart-safe")],
        )

    def test_selection_pending_names_recovery_and_blocks_design_lock(self):
        record = self.base_record()
        result = next(
            item for item in record["results"]
            if item["candidate"] == "streaming" and item["criterion"] == "peak-rss"
        )
        result.clear()
        result.update({
            "candidate": "streaming",
            "criterion": "peak-rss",
            "state": "pending",
            "resolver": "python3 measure.py",
            "report": "reports/streaming-peak-rss-later.json",
            "blocks": "design-lock",
        })
        self.write_record(record)
        self.assertEqual(self.codes(), [])
        found = design.check(self.record_path, "design-lock")
        self.assertEqual([item.code for item in found], ["D007"])
        self.assertIn("streaming/peak-rss", found[0].message)
        self.assertIn("python3 measure.py", found[0].message)

    def test_integration_evidence_is_not_due_at_a_step_boundary(self):
        record = self.base_record()
        criterion = next(
            item for item in record["criteria"] if item["id"] == "restart-safe"
        )
        criterion["blocks"] = "integration"
        pending = next(item for item in record["results"] if item["state"] == "pending")
        pending["blocks"] = "integration"
        self.write_record(record)
        self.assertEqual(self.codes("step:4"), [])
        self.assertEqual(self.codes("integration"), ["D008"])

    def test_pending_requires_resolver_report_and_matching_stop_point(self):
        record = self.base_record()
        pending = next(item for item in record["results"] if item["state"] == "pending")
        for field, replacement in (
            ("resolver", ""),
            ("report", "../outside.json"),
            ("blocks", "step:3"),
        ):
            with self.subTest(field=field):
                candidate = json.loads(json.dumps(record))
                item = next(value for value in candidate["results"] if value["state"] == "pending")
                item[field] = replacement
                self.write_record(candidate)
                self.assertIn("D004", self.codes())
        self.assertEqual(pending["blocks"], "step:2")

    def test_report_digest_identity_unit_exit_and_state_are_checked(self):
        mutations = (
            ("digest", lambda path, payload: path.write_text(path.read_text() + " ")),
            ("candidate", lambda: payload.__setitem__("candidate", "buffered")),
            ("unit", lambda: payload.__setitem__("unit", "bytes")),
            ("exit", lambda: payload.__setitem__("exit", 1)),
        )
        for name, mutation in mutations:
            with self.subTest(name=name):
                record = self.base_record()
                self.write_record(record)
                first = next(
                    item for item in record["results"] if item["state"] == "pass"
                )
                report_path = self.root / first["report"]["path"]
                payload = json.loads(report_path.read_text())
                if name == "digest":
                    mutation(report_path, payload)
                else:
                    mutation()
                if name != "digest":
                    report_path.write_text(json.dumps(payload) + "\n")
                self.assertIn("D005", self.codes())

        record = self.base_record()
        first = next(item for item in record["results"] if item["state"] == "pass")
        self.write_record(record)
        first["state"] = "fail"
        self.write_record(record)
        self.assertIn("D006", self.codes())

    def test_unknown_fields_duplicate_ids_missing_cells_and_concerns_refuse(self):
        record = self.base_record()
        cases = []
        unknown = json.loads(json.dumps(record))
        unknown["private"] = True
        cases.append((unknown, "D001"))
        duplicate = json.loads(json.dumps(record))
        duplicate["candidates"][1]["id"] = "streaming"
        cases.append((duplicate, "D002"))
        missing = json.loads(json.dumps(record))
        missing["results"].pop()
        cases.append((missing, "D003"))
        concern = json.loads(json.dumps(record))
        concern["criteria"] = [
            item for item in concern["criteria"] if item["concern"] != "compatibility"
        ]
        concern["results"] = [
            item for item in concern["results"] if item["criterion"] != "plugin-compatible"
        ]
        cases.append((concern, "D002"))
        for candidate, code in cases:
            with self.subTest(code=code):
                self.write_record(candidate)
                self.assertIn(code, self.codes())

        duplicate_path = self.base_record()
        duplicate_path["results"][1]["report"]["path"] = (
            duplicate_path["results"][0]["report"]["path"]
        )
        self.write_record(duplicate_path)
        self.assertIn("D003", self.codes())

    def test_selection_rules_are_mechanical(self):
        dominated = self.base_record()
        dominated["selection"]["candidate"] = "buffered"
        self.write_record(dominated)
        self.assertIn("D007", self.codes("design-lock"))

        tied = self.base_record()
        for result in tied["results"]:
            if result["candidate"] != "buffered" or result["criterion"] not in {
                "warm-time", "peak-rss",
            }:
                continue
            path = self.root / result["report"]["path"]
            payload = json.loads(path.read_text())
            payload["value"] = 100
            data = (json.dumps(payload, sort_keys=True) + "\n").encode()
            path.write_bytes(data)
            result["report"]["sha256"] = hashlib.sha256(data).hexdigest()
        tied["selection"] = {
            "candidate": "streaming",
            "rule": "exact-tie-simplicity",
            "policy_ref": None,
        }
        self.write_record(tied)
        self.assertEqual(self.codes("design-lock"), [])

        policy = json.loads(json.dumps(tied))
        policy["selection"] = {
            "candidate": "buffered",
            "rule": "user-policy",
            "policy_ref": "decision:issue-1000-user-choice",
        }
        self.write_record(policy)
        self.assertEqual(self.codes("design-lock"), [])
        policy["selection"]["policy_ref"] = ""
        self.write_record(policy)
        self.assertIn("D007", self.codes("design-lock"))

    def test_a_known_conformance_failure_cannot_be_selected(self):
        record = self.base_record()
        pending = next(item for item in record["results"] if item["state"] == "pending")
        pending.clear()
        pending.update({
            "candidate": "streaming",
            "criterion": "restart-safe",
            "state": "fail",
            "report": self.report("streaming", "restart-safe", False, "boolean"),
        })
        self.write_record(record)
        self.assertIn("D007", self.codes("design-lock"))

    def test_strict_json_rejects_duplicate_keys_and_non_finite_numbers(self):
        self.record_path.write_text('{"schema":"x","schema":"y"}\n')
        self.assertEqual(self.codes(), ["D000"])
        self.record_path.write_text('{"value":NaN}\n')
        self.assertEqual(self.codes(), ["D000"])
        self.record_path.write_text("[" * 65 + "]" * 65 + "\n")
        self.assertEqual(self.codes(), ["D000"])

    def test_report_symlink_is_refused_even_when_its_target_is_inside(self):
        record = self.base_record()
        self.write_record(record)
        first = next(item for item in record["results"] if item["state"] == "pass")
        report_path = self.root / first["report"]["path"]
        target = self.root / "inside.json"
        report_path.replace(target)
        report_path.symlink_to(target)
        self.assertIn("D005", self.codes())

    def test_receipt_output_is_closed_and_sorted(self):
        self.write_record()
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(self.record_path),
                "--transition", "design-lock",
                "--format", "receipt",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(
            set(receipt),
            {"schema", "transition", "selected", "consumed", "findings"},
        )
        self.assertEqual(receipt["findings"], [])
        identities = [
            (item["candidate"], item["criterion"])
            for item in receipt["consumed"]
        ]
        self.assertEqual(identities, sorted(identities))


if __name__ == "__main__":
    unittest.main()
