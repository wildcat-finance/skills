"""Scaffold checks for harness-classification/v1.

The roster schema is the contract three generated wording surfaces will be
rendered from, so these cases hold the two things that are expensive to reverse
once prose exists: the four classification names, and the observation fields
every harness entry has to carry.

``jsonschema`` is a Lazarus dependency rather than a root one, so no case here
may depend on it being installed. Each case asserts against the schema document
itself, which always runs, and then asserts the same rule behaviourally when the
library happens to be importable. A host without the library still checks the
declared rule; it does not quietly skip.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/harness-classification-v1.json"
SCHEMA_ID = "harness-classification/v1"

CLASSIFICATIONS = (
    "Atlas launcher",
    "tested local route",
    "manual route",
    "unsupported",
)

OBSERVATION_FIELDS = (
    "client_present",
    "client_version",
    "auth_configured",
    "launcher_contract",
    "blocker",
)

# The six harnesses issue #856 asks about. Named here so a missing-field case
# removes a field from a realistic record rather than from a stub.
HARNESSES = (
    "GitHub Copilot",
    "Cursor",
    "Gemini CLI",
    "Windsurf",
    "Cline",
    "Roo Code",
)


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validator():
    """A Draft 2020-12 validator, or None where the library is absent."""
    try:
        import jsonschema
    except ImportError:
        return None
    schema = load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def entry(name, **overrides):
    record = {
        "name": name,
        "classification": "manual route",
        "client_present": False,
        "client_version": None,
        "auth_configured": False,
        "launcher_contract": "documented deep link, not exercised here",
        "blocker": "absent from this host and unauthenticated",
    }
    record.update(overrides)
    return record


def manifest(*entries):
    return {
        "schema": SCHEMA_ID,
        "recorded": {
            "host": "darwin-arm64",
            "date": "2026-09-04",
            "base_ref": "8dc3aca54adeca49387a2bdfc174cf6e72d02a11",
        },
        "harnesses": list(entries) or [entry(name) for name in HARNESSES],
    }


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema()
        self.validator = validator()
        self.harness = self.schema["$defs"]["harness"]

    def assert_valid(self, document):
        if self.validator is None:
            return
        self.assertEqual([e.message for e in self.validator.iter_errors(document)], [])

    def assert_refused(self, document):
        if self.validator is None:
            return
        self.assertNotEqual(list(self.validator.iter_errors(document)), [])

    def test_the_schema_is_the_published_roster_contract(self):
        self.assertEqual(self.schema["properties"]["schema"]["const"], SCHEMA_ID)
        self.assertEqual(
            self.schema["$id"],
            "https://wildcat.finance/schemas/harness-classification-v1.json",
        )
        self.assert_valid(manifest())

    def test_the_four_classification_names_are_exactly_these_four(self):
        declared = self.schema["$defs"]["classification"]["enum"]
        self.assertEqual(tuple(declared), CLASSIFICATIONS)

    def test_each_classification_name_is_admitted(self):
        for name in CLASSIFICATIONS:
            with self.subTest(classification=name):
                self.assert_valid(manifest(entry("Cursor", classification=name)))

    def test_an_unknown_classification_name_is_refused(self):
        declared = self.schema["$defs"]["classification"]
        # A closed enum is what refuses the unknown name. A type keyword beside
        # it would admit any string the enum forgot.
        self.assertEqual(set(declared), {"enum", "description"})
        for unknown in ("tested", "Atlas Launcher", "supported", ""):
            with self.subTest(classification=unknown):
                self.assertNotIn(unknown, declared["enum"])
                self.assert_refused(
                    manifest(entry("Cursor", classification=unknown))
                )

    def test_every_harness_entry_requires_the_five_observation_fields(self):
        required = self.harness["required"]
        for field in OBSERVATION_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, required)
        self.assertFalse(self.harness["additionalProperties"])
        document = manifest()
        self.assertEqual(len(document["harnesses"]), len(HARNESSES))
        self.assert_valid(document)

    def test_a_harness_entry_missing_any_observation_field_is_refused(self):
        for field in OBSERVATION_FIELDS:
            with self.subTest(field=field):
                record = entry("Cline")
                del record[field]
                self.assert_refused(manifest(record))

    def test_a_null_client_version_is_admitted_when_the_client_is_absent(self):
        self.assert_valid(
            manifest(entry("Gemini CLI", client_present=False, client_version=None))
        )

    def test_a_null_client_version_is_refused_when_the_client_is_present(self):
        conditional = self.harness["allOf"][0]
        self.assertEqual(conditional["if"]["properties"]["client_present"]["const"], True)
        self.assertIn("client_version", conditional["then"]["properties"])
        self.assert_refused(
            manifest(entry("Cursor", client_present=True, client_version=None))
        )
        self.assert_valid(
            manifest(
                entry(
                    "Cursor",
                    client_present=True,
                    client_version="2026.8.1",
                    classification="manual route",
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
