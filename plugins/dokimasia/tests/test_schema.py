"""Closed means closed, and a half-checked schema is worse than none."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from dokimasia_lib import reconcile  # noqa: E402
from dokimasia_lib import schema  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "disposition_build", PLUGIN / "tests" / "fixtures" / "dispositions" / "build.py"
)
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

EVIDENCE = PLUGIN / "docs" / "evidence"


class SchemaCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.made = build.build_all(Path(self.tmp.name))
        self.inventory = reconcile.read_json(self.made["inventory.json"])
        self.workbook = reconcile.read_json(self.made["workbook.json"])
        self.coverage = reconcile.reconcile(
            self.inventory, self.workbook,
            reconcile.read_json(self.made["closed.json"]),
        )

    def mutated(self, apply) -> dict:
        copy = json.loads(json.dumps(self.coverage))
        apply(copy)
        return copy


class EveryEmittedRecordHoldsItsSchema(SchemaCase):
    def test_the_inventory_record_holds_its_schema(self):
        self.assertEqual(schema.check(self.inventory), [])

    def test_the_workbook_record_holds_its_schema(self):
        self.assertEqual(schema.check(self.workbook), [])

    def test_the_coverage_record_holds_its_schema(self):
        self.assertEqual(schema.check(self.coverage), [])

    def test_the_committed_evidence_holds_its_schemas(self):
        for name in ("wildcat-app-v2.coverage.json", "wildcat-app-v2.scrutiny.json"):
            with self.subTest(name=name):
                record = json.loads((EVIDENCE / name).read_text(encoding="utf-8"))
                self.assertEqual(schema.check(record), [])


class BreachesAreCaught(SchemaCase):
    """Each of these passed silently before the checker existed."""

    def test_an_unknown_key_is_a_refusal(self):
        findings = schema.check(self.mutated(lambda r: r.update({"surprise": 1})))
        self.assertTrue(findings)
        self.assertIn("unknown key 'surprise'", findings[0])

    def test_a_missing_required_key_is_caught(self):
        findings = schema.check(self.mutated(lambda r: r.pop("gaps")))
        self.assertTrue(any("required key 'gaps' is absent" in line for line in findings))

    def test_a_value_over_its_maximum_is_caught(self):
        findings = schema.check(
            self.mutated(lambda r: r["closure_ratio"].update({"value": 2.5}))
        )
        self.assertTrue(any("over the maximum" in line for line in findings))

    def test_a_value_failing_its_pattern_is_caught(self):
        findings = schema.check(
            self.mutated(lambda r: r["subject"].update({"inventory_sha256": "nope"}))
        )
        self.assertTrue(any("does not match" in line for line in findings))

    def test_a_wrong_type_is_caught(self):
        findings = schema.check(
            self.mutated(lambda r: r["counts"].update({"scoped": "many"}))
        )
        self.assertTrue(any("expected type" in line for line in findings))

    def test_a_wrong_const_is_caught(self):
        findings = schema.check(self.mutated(lambda r: r.update({"closure": "other"})))
        self.assertTrue(findings)

    def test_a_value_outside_an_enum_is_caught(self):
        findings = schema.check(
            self.mutated(
                lambda r: r["dispositions"][0].update({"disposition": "partial"})
            )
        )
        self.assertTrue(any("is not one of" in line for line in findings))

    def test_a_string_over_its_maximum_length_is_caught(self):
        findings = schema.check(
            self.mutated(lambda r: r["gaps"][0].update({"reason": "x" * 4096}))
        )
        self.assertTrue(any("over the" in line for line in findings))

    def test_a_boolean_is_not_an_integer(self):
        """Python says a bool is an int. JSON Schema does not."""
        findings = schema.check(
            self.mutated(lambda r: r["counts"].update({"scoped": True}))
        )
        self.assertTrue(any("expected type" in line for line in findings))

    def test_a_reference_through_definitions_is_followed(self):
        findings = schema.check(
            self.mutated(lambda r: r["dispositions"][0].update({"stray": 1}))
        )
        self.assertTrue(
            any("unknown key 'stray'" in line for line in findings),
            "a $ref target was not checked, so its closure was not enforced",
        )


class UnsupportedKeywordsRefuse(unittest.TestCase):
    """A schema quietly half-checked is worse than one not checked at all."""

    def test_an_unsupported_keyword_refuses_rather_than_being_ignored(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "odd.json"
            target.write_text(json.dumps({
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "oneOf": [{"required": ["a"]}],
            }))
            with self.assertRaises(schema.SchemaError) as caught:
                schema.check_record({"a": "x"}, target)
            self.assertIn("unsupported keyword", str(caught.exception))
            self.assertIn("oneOf", str(caught.exception))

    def test_an_unknown_type_refuses(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "odd.json"
            target.write_text(json.dumps({"type": "tuple"}))
            with self.assertRaises(schema.SchemaError) as caught:
                schema.check_record({}, target)
            self.assertIn("unknown type", str(caught.exception))

    def test_a_missing_definition_refuses(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "odd.json"
            target.write_text(json.dumps({
                "type": "array", "items": {"$ref": "#/definitions/absent"},
            }))
            with self.assertRaises(schema.SchemaError) as caught:
                schema.check_record([{}], target)
            self.assertIn("missing definition", str(caught.exception))

    def test_a_record_declaring_no_schema_refuses(self):
        with self.assertRaises(schema.SchemaError) as caught:
            schema.check({"not": "a record"})
        self.assertIn("declares no schema", str(caught.exception))

    def test_a_record_declaring_an_unpublished_schema_refuses(self):
        with self.assertRaises(schema.SchemaError) as caught:
            schema.check({"schema": "dokimasia-imaginary/v1"})
        self.assertIn("no committed schema publishes", str(caught.exception))

    def test_a_symlinked_schema_refuses(self):
        with tempfile.TemporaryDirectory() as raw:
            real = Path(raw) / "real.json"
            real.write_text(json.dumps({"type": "object"}))
            link = Path(raw) / "link.json"
            link.symlink_to(real)
            with self.assertRaises(schema.SchemaError) as caught:
                schema.check_record({}, link)
            self.assertIn("not a regular file", str(caught.exception))


class EverySchemaIsCheckable(unittest.TestCase):
    def test_no_committed_schema_uses_an_unsupported_keyword(self):
        """The checker covers exactly what this plugin's schemas use."""
        for path in sorted((PLUGIN / "schemas").glob("*.json")):
            with self.subTest(schema=path.name):
                published = json.loads(path.read_text(encoding="utf-8"))
                used: set[str] = set()

                def walk(node):
                    if isinstance(node, dict):
                        for key, value in node.items():
                            if key in ("properties", "definitions"):
                                for entry in value.values():
                                    walk(entry)
                                used.add(key)
                                continue
                            used.add(key)
                            walk(value)
                    elif isinstance(node, list):
                        for entry in node:
                            walk(entry)

                walk(published)
                unsupported = used - schema.SUPPORTED
                self.assertEqual(
                    unsupported, set(),
                    f"{path.name} uses keywords the checker would refuse",
                )


if __name__ == "__main__":
    unittest.main()
