"""The versioned JSON Schema documents carry the intended envelope."""

import json
import unittest

from . import support
from tabularium_lib.release_v2 import KNOWN_GAPS


class SchemaDocumentTests(unittest.TestCase):
    def load(self, name):
        return json.loads((support.PLUGIN_ROOT / "schemas" / name).read_text())

    def test_event_schema_is_draft_2020_12_and_requires_every_dimension(self):
        schema = self.load("canonical-event-v2.json")
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        for key in ("event_family", "action", "chain", "transaction", "parties", "instrument", "amounts", "provenance", "native_record"):
            self.assertIn(key, schema["required"])
        provenance = schema["properties"]["provenance"]
        self.assertIn("source_contract", provenance["required"])
        self.assertEqual(
            provenance["properties"]["source_contract"]["pattern"],
            "^0x[0-9a-f]{40}$",
        )

    def test_coverage_schema_binds_all_three_artifacts_and_unsupported_kinds(self):
        schema = self.load("coverage-manifest-v2.json")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        self.assertIn("capture_manifest", schema["required"])
        coverage = schema["properties"]["coverage"]
        self.assertEqual(
            set(coverage["required"]), {"included_events", "unsupported_events"}
        )
        self.assertFalse(coverage["additionalProperties"])
        for key in ("included_events", "unsupported_events"):
            counts = coverage["properties"][key]["additionalProperties"]
            self.assertEqual(counts["type"], "integer")
            self.assertEqual(counts["minimum"], 0)
        gaps = schema["properties"]["known_gaps"]
        self.assertGreaterEqual(gaps["minItems"], 4)
        self.assertTrue(gaps["uniqueItems"])
        self.assertIn(
            "the release is unsigned; offline verification proves internal consistency, not publisher identity or authenticity",
            KNOWN_GAPS["aave-v4"],
        )

    def test_event_schema_v2_separates_protocol_and_source_api(self):
        schema = self.load("canonical-event-v2.json")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        provenance = schema["properties"]["provenance"]
        self.assertIn("protocol_generation", provenance["required"])
        self.assertIn("source_api", provenance["required"])
        self.assertIn("amounts", schema["required"])
        self.assertIn("debt-transfer", schema["properties"]["event_family"]["enum"])
        self.assertIn("interest-accrual", schema["properties"]["event_family"]["enum"])

    def test_coverage_schema_v2_binds_capture_scope_and_versions(self):
        schema = self.load("coverage-manifest-v2.json")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        self.assertIn("scope", schema["properties"]["source"]["required"])
        self.assertIn("included_events", schema["properties"]["coverage"]["required"])
        self.assertEqual(schema["properties"]["versions"]["properties"]["event_schema"]["const"], 2)

    def test_compound_phase0_schemas_are_noncanonical_and_closed(self):
        facts = self.load("compound-v3-execution-fact-v1.json")
        self.assertEqual(len(facts["oneOf"]), 3)
        for name in ("call", "storageWrite", "principalTransition"):
            contract = facts["$defs"][name]["allOf"][1]
            self.assertFalse(contract["additionalProperties"])
        manifest = self.load("compound-v3-witness-manifest-v1.json")
        self.assertFalse(manifest["additionalProperties"])
        self.assertIn("scope", manifest["required"])
        self.assertIn("facts_bytes", manifest["required"])
        self.assertEqual(
            manifest["properties"]["registry_commit"]["const"],
            "f766f51583c23acc33b2a7824654ef2029a96804",
        )
