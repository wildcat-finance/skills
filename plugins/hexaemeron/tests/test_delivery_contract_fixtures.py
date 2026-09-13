"""Check inert scaffold fixtures; these tests establish no runtime admission."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import prove_issue_508

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures" / "issue508"
DOCS = ROOT / "docs" / "fiat-508-residual"


def fixture_matches(value, schema):
    """Check only the closed JSON Schema subset used by these inert fixtures."""
    allowed = {"$schema", "type", "const", "enum", "properties", "required",
               "additionalProperties", "items", "minItems", "minimum"}
    if set(schema) - allowed:
        raise ValueError("unsupported fixture schema keyword")
    if "const" in schema and (type(value) is not type(schema["const"])
                              or value != schema["const"]):
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    kind = schema.get("type")
    types = {"object": dict, "array": list, "integer": int, "string": str}
    if kind is not None and (kind not in types or type(value) is not types[kind]):
        return False
    if kind == "object":
        if schema.get("additionalProperties") is not False:
            raise ValueError("fixture objects must be closed")
        props = schema["properties"]
        if set(value) - set(props) or set(schema["required"]) - set(value):
            return False
        return all(fixture_matches(item, props[key]) for key, item in value.items())
    if kind == "array":
        return len(value) >= schema.get("minItems", 0) and all(
            fixture_matches(item, schema["items"]) for item in value)
    if kind == "integer":
        return value >= schema.get("minimum", value)
    return True


class Issue508Contracts(unittest.TestCase):
    def test_each_module_has_positive_and_malformed_shape_fixtures(self):
        for module in ("launch", "carryover", "command"):
            schema = json.loads((FIXTURES / (module + ".schema.json")).read_text())
            cases = json.loads((FIXTURES / (module + ".cases.json")).read_text())
            self.assertEqual({case["valid"] for case in cases}, {True, False})
            self.assertEqual(len({case["id"] for case in cases}), len(cases))
            for case in cases:
                with self.subTest(module=module, case=case["id"]):
                    self.assertIs(fixture_matches(case["value"], schema), case["valid"])

    def test_nested_payload_and_schema_unknowns_refuse(self):
        schema = json.loads((FIXTURES / "carryover.schema.json").read_text())
        value = json.loads((FIXTURES / "carryover.cases.json").read_text())[0]["value"]
        value["files"][0]["execute"] = "anything"
        self.assertFalse(fixture_matches(value, schema))
        altered = deepcopy(schema)
        altered["ignored"] = True
        with self.assertRaisesRegex(ValueError, "unsupported"):
            fixture_matches(value, altered)

    def test_frozen_criteria_and_transition_inventory(self):
        design = json.loads((DOCS / "design-evidence.json").read_text())
        declared = {c["id"]: c["blocks"] for c in design["criteria"]
                    if c["stage"] == "conformance"}
        manifest = json.loads((FIXTURES / "criteria.json").read_text())
        self.assertEqual(manifest["candidate"], "whole-worker-sandbox")
        self.assertEqual(len(manifest["criteria"]), len(declared))
        self.assertEqual({c["id"]: c["blocks"] for c in manifest["criteria"]}, declared)
        self.assertEqual(set(prove_issue_508.CRITERIA), set(declared))
        for criterion in manifest["criteria"]:
            self.assertTrue(criterion["specimens"])
            self.assertEqual(len(set(criterion["specimens"])), len(criterion["specimens"]))

    def test_all_unimplemented_calls_refuse_without_report_write(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "report.json"
            for candidate in prove_issue_508.CANDIDATES:
                for criterion in prove_issue_508.CRITERIA:
                    with self.subTest(candidate=candidate, criterion=criterion):
                        result = subprocess.run(
                            [sys.executable, str(Path(prove_issue_508.__file__).resolve()),
                             "--candidate", candidate, "--criterion", criterion,
                             "--report", str(report)],
                            capture_output=True, text=True, timeout=10, check=False)
                        self.assertEqual(result.returncode, 1)
                        refusal = json.loads(result.stdout)
                        self.assertEqual(refusal["code"], "executor-unimplemented")
                        self.assertEqual(refusal["criterion"], criterion)
                        self.assertNotIn("value", refusal)
                        self.assertFalse(report.exists())
            report.write_text("existing evidence\n")
            result = subprocess.run(
                [sys.executable, str(Path(prove_issue_508.__file__).resolve()),
                 "--candidate", "whole-worker-sandbox", "--criterion", "worker-deadline",
                 "--report", str(report)], capture_output=True, timeout=10, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(report.read_text(), "existing evidence\n")

    def test_preserved_source_digests(self):
        inventory = json.loads((DOCS / "source-inventory.json").read_text())
        self.assertGreaterEqual(len(inventory["files"]), 13)
        for item in inventory["files"]:
            self.assertEqual(hashlib.sha256((DOCS / item["preserved"]).read_bytes()).hexdigest(),
                             item["sha256"])

    def test_study_reading_copy_has_only_declared_transform(self):
        source = (DOCS / "study.source.txt").read_text()
        bridge = ("\n```design-bridge\nschema | hypomnema-design-bridge/v1\n"
                  "decision | whole-worker-sandbox\nrecord | docs/decisions/drafts/"
                  "confine-the-worker-before-admitting-its-output.md\n```\n")
        self.assertEqual((DOCS / "study.md").read_text(),
                         source.replace("(../plugins/", "(../../plugins/") + bridge)

    def test_preserved_four_draft_parser_failure(self):
        specimen = json.loads((FIXTURES / "four-draft-command.json").read_text())
        result = subprocess.run([sys.executable, *specimen["argv"][1:]], cwd=ROOT,
                                capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(result.returncode, specimen["observed_exit"])
        for operand in specimen["rejected_operands"]:
            self.assertIn(operand, result.stderr)


if __name__ == "__main__":
    unittest.main()
