"""The versioned JSON Schema documents carry the intended envelope.

The admitted vocabulary of the v3 documents is the closed adapter tuple table.
That table is derived here at test time from `release_v2.ADAPTERS`, the
registry a new adapter is registered in, never copied, so a schema that
disagrees with what a registered adapter emits fails with the schema file, the
field and the disagreeing value named. Reading the registry rather than a
fixed module list is what makes registering a fourth adapter visible here: a
list would leave its values unchecked against the schema documents.
"""

import contextlib
import copy
import errno
import io
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile
import unittest
from unittest import mock

from . import prove_schema_v3
from . import support
from tabularium_lib import SUPPORTED_EVENT_SCHEMAS, release_v2
from tabularium_lib.adapters import aave_v4, euler_v1, euler_v2
from tabularium_lib.release_v2 import KNOWN_GAPS

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised only where the package is absent
    jsonschema = None


SCHEMA_DIRECTORY = support.PLUGIN_ROOT / "schemas"
ADAPTER_MODULES = tuple(release_v2.ADAPTERS[name] for name in sorted(release_v2.ADAPTERS))
DRAFT = "https://json-schema.org/draft/2020-12/schema"
EVENT_V2 = "canonical-event-v2.json"
COVERAGE_V2 = "coverage-manifest-v2.json"
EVENT_V3 = "canonical-event-v3.json"
COVERAGE_V3 = "coverage-manifest-v3.json"
ALL_SCHEMAS = (EVENT_V2, COVERAGE_V2, EVENT_V3, COVERAGE_V3)
DEPRECATED = {EVENT_V2: EVENT_V3, COVERAGE_V2: COVERAGE_V3}
REQUIRES_JSONSCHEMA = unittest.skipIf(jsonschema is None, support.JSONSCHEMA_ABSENT)


def scratch_directory(prefix: str = "tabularium-schema-v3-"):
    """Transient space with no symlinked component and no status entry.

    The reporter refuses a symlinked path component, and on macOS the platform
    temporary directory is reached through one, so scratch is anchored at the
    ignored top-level tmp/ of this checkout instead.  That directory is
    confined and `git status` never sees it.
    """
    scratch = support.REPO_ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def tuple_table():
    """One row per registered adapter, read from the module constants."""
    rows = []
    for module in ADAPTER_MODULES:
        rows.append(
            {
                "venue": module.ADAPTER,
                "adapter": module.ADAPTER,
                "adapter_version": module.ADAPTER_VERSION,
                "protocol_generation": module.PROTOCOL_GENERATION,
                "source_api": module.SOURCE_API,
                "evidence_class": release_v2.EVIDENCE_CLASSES[module.ADAPTER],
                "mapping_rules": sorted(rule for _, _, rule in module.MAPPINGS.values()),
            }
        )
    return rows


def column(rows, key):
    return sorted({row[key] for row in rows})


def load_schema(name):
    return json.loads((SCHEMA_DIRECTORY / name).read_text(encoding="utf-8"))


def walk(schema, pointer):
    """Follow a slash-separated pointer through nested dictionaries."""
    node = schema
    for part in pointer.split("/"):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(pointer)
        node = node[part]
    return node


def admits(subschema, value):
    """Whether one property schema accepts one literal value."""
    if "const" in subschema:
        return subschema["const"] == value
    if "enum" in subschema:
        return value in subschema["enum"]
    if subschema.get("type") == "string":
        return isinstance(value, str) and len(value) >= subschema.get("minLength", 0)
    return False


class SchemaDocumentTests(unittest.TestCase):
    maxDiff = None

    def load(self, name):
        return load_schema(name)

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


class SchemaDocumentValidityTests(unittest.TestCase):
    """Every versioned document parses and is itself a valid draft 2020-12 schema."""

    def test_the_declared_document_sets_match_the_schemas_directory(self):
        """Emptied, the two lists below would assert nothing and still pass.

        `ALL_SCHEMAS` and `DEPRECATED` drive loops whose bodies carry every
        assertion in this class and in the supersession case, so an empty one
        is a test that checks nothing rather than a test that fails.  Both are
        bound here to the documents on disk: the versioned canonical family by
        name, and the superseded set by the `deprecated` flag the documents
        themselves carry.  The Compound v3 Phase 0 documents are not part of
        the versioned canonical family and stay out.
        """
        versioned = {
            path.name
            for path in SCHEMA_DIRECTORY.iterdir()
            if re.fullmatch(r"(canonical-event|coverage-manifest)-v\d+\.json", path.name)
        }
        self.assertTrue(ALL_SCHEMAS, "no document would be checked at all")
        self.assertEqual(set(ALL_SCHEMAS), versioned)
        superseded = {
            name for name in versioned if load_schema(name).get("deprecated") is True
        }
        self.assertTrue(DEPRECATED, "no supersession would be checked at all")
        self.assertEqual(set(DEPRECATED), superseded)
        for name, successor in DEPRECATED.items():
            with self.subTest(schema=name):
                self.assertIn(successor, versioned)
                self.assertIsNot(load_schema(successor).get("deprecated"), True)

    def test_every_versioned_document_parses_and_checks_as_a_schema(self):
        for name in ALL_SCHEMAS:
            with self.subTest(schema=name):
                schema = load_schema(name)
                self.assertEqual(schema["$schema"], DRAFT, name)
                self.assertEqual(
                    schema["$id"],
                    "https://wildcat.finance/schemas/tabularium/" + name,
                )
                if jsonschema is not None:
                    validator = jsonschema.validators.validator_for(schema)
                    validator.check_schema(schema)
                else:
                    self.assertEqual(schema["type"], "object", name)
                    self.assertIsInstance(schema["properties"], dict, name)
                    self.assertIsInstance(schema["required"], list, name)
                    self.assertFalse(schema["additionalProperties"], name)


class TupleTableChecks(unittest.TestCase):
    """Shared assertions naming the schema file, the field and the value."""

    maxDiff = None

    def assert_enum_equals(self, name, pointer, schema, expected):
        try:
            node = walk(schema, pointer)
        except KeyError:
            self.fail("%s: %s is missing" % (name, pointer))
        self.assertIn("enum", node, "%s: %s has no enum" % (name, pointer))
        actual = node["enum"]
        self.assertEqual(
            len(actual),
            len(set(actual)),
            "%s: %s/enum repeats a value: %s" % (name, pointer, actual),
        )
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        if missing or extra:
            self.fail(
                "%s: %s/enum disagrees with the adapter tuple table; "
                "missing from schema: %s; not emitted by any adapter: %s"
                % (name, pointer, missing, extra)
            )

    def assert_const_equals(self, name, pointer, schema, expected):
        try:
            node = walk(schema, pointer)
        except KeyError:
            self.fail("%s: %s is missing" % (name, pointer))
        self.assertIn("const", node, "%s: %s has no const" % (name, pointer))
        self.assertEqual(
            node["const"],
            expected,
            "%s: %s/const is %r, the adapter tuple table says %r"
            % (name, pointer, node["const"], expected),
        )

    def assert_closed(self, name, pointer, schema):
        node = walk(schema, pointer)
        self.assertIs(
            node.get("additionalProperties"),
            False,
            "%s: %s does not set additionalProperties false" % (name, pointer),
        )

    def branch_for(self, name, schema, key_pointer, expected):
        """The single oneOf branch whose pinned key equals one row's value."""
        branches = schema.get("oneOf")
        self.assertIsInstance(branches, list, "%s: oneOf is missing" % name)
        matches = []
        for index, branch in enumerate(branches):
            try:
                pinned = walk(branch, key_pointer)
            except KeyError:
                self.fail("%s: oneOf[%d] does not pin %s" % (name, index, key_pointer))
            if pinned.get("const") == expected:
                matches.append(branch)
        self.assertEqual(
            len(matches),
            1,
            "%s: oneOf has %d branches pinning %s/const to %r, the adapter tuple "
            "table has exactly one row" % (name, len(matches), key_pointer, expected),
        )
        return matches[0]

    def check_event_v3(self, name, schema):
        rows = tuple_table()
        self.assertIs(schema.get("additionalProperties"), False, name)
        self.assert_closed(name, "properties/provenance", schema)
        self.assert_const_equals(name, "properties/schema_version", schema, 3)
        provenance = "properties/provenance/properties"
        self.assert_enum_equals(name, "properties/venue", schema, column(rows, "venue"))
        self.assert_enum_equals(name, provenance + "/adapter", schema, column(rows, "adapter"))
        self.assert_enum_equals(
            name, provenance + "/adapter_version", schema, column(rows, "adapter_version")
        )
        self.assert_enum_equals(
            name, provenance + "/protocol_generation", schema, column(rows, "protocol_generation")
        )
        self.assert_enum_equals(name, provenance + "/source_api", schema, column(rows, "source_api"))
        every_rule = sorted(rule for row in rows for rule in row["mapping_rules"])
        self.assert_enum_equals(name, provenance + "/mapping_rule", schema, every_rule)
        self.assertEqual(
            len(schema.get("oneOf", ())),
            len(rows),
            "%s: oneOf has %d branches, the adapter tuple table has %d rows"
            % (name, len(schema.get("oneOf", ())), len(rows)),
        )
        for row in rows:
            branch = self.branch_for(name, schema, "properties/venue", row["venue"])
            label = "%s: oneOf[venue=%s]" % (name, row["venue"])
            for field in ("adapter", "adapter_version", "protocol_generation", "source_api"):
                self.assert_const_equals(label, provenance + "/" + field, branch, row[field])
            self.assert_enum_equals(label, provenance + "/mapping_rule", branch, row["mapping_rules"])

    def check_coverage_v3(self, name, schema):
        rows = tuple_table()
        self.assertIs(schema.get("additionalProperties"), False, name)
        self.assert_closed(name, "properties/source", schema)
        self.assert_closed(name, "properties/versions", schema)
        self.assert_closed(name, "properties/versions/properties/adapter", schema)
        self.assert_const_equals(name, "properties/schema_version", schema, 3)
        self.assert_const_equals(name, "properties/versions/properties/event_schema", schema, 3)
        source = "properties/source/properties"
        adapter = "properties/versions/properties/adapter/properties"
        self.assert_enum_equals(name, source + "/evidence_class", schema, column(rows, "evidence_class"))
        self.assert_enum_equals(
            name, source + "/protocol_generation", schema, column(rows, "protocol_generation")
        )
        self.assert_enum_equals(name, source + "/source_api", schema, column(rows, "source_api"))
        self.assert_enum_equals(name, adapter + "/name", schema, column(rows, "adapter"))
        self.assert_enum_equals(name, adapter + "/version", schema, column(rows, "adapter_version"))
        every_rule = sorted(rule for row in rows for rule in row["mapping_rules"])
        self.assert_enum_equals(
            name, "properties/versions/properties/mapping_rules/items", schema, every_rule
        )
        gaps = walk(schema, "properties/known_gaps")
        self.assertEqual(gaps["minItems"], 4, "%s: known_gaps/minItems" % name)
        for module in ADAPTER_MODULES:
            self.assertGreaterEqual(
                len(KNOWN_GAPS[module.ADAPTER]),
                gaps["minItems"],
                "%s: known_gaps/minItems exceeds the %s gap count" % (name, module.ADAPTER),
            )
        self.assertEqual(
            len(schema.get("oneOf", ())),
            len(rows),
            "%s: oneOf has %d branches, the adapter tuple table has %d rows"
            % (name, len(schema.get("oneOf", ())), len(rows)),
        )
        for row in rows:
            branch = self.branch_for(name, schema, adapter + "/name", row["adapter"])
            label = "%s: oneOf[adapter=%s]" % (name, row["adapter"])
            self.assert_const_equals(label, adapter + "/version", branch, row["adapter_version"])
            for field in ("evidence_class", "protocol_generation", "source_api"):
                self.assert_const_equals(label, source + "/" + field, branch, row[field])
            self.assert_enum_equals(
                label, "properties/versions/properties/mapping_rules/items", branch, row["mapping_rules"]
            )


class V3SchemaTupleTableTests(TupleTableChecks):
    def test_tuple_table_has_one_row_per_adapter_and_eleven_rules(self):
        rows = tuple_table()
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({row["venue"] for row in rows}), 3)
        self.assertEqual(sum(len(row["mapping_rules"]) for row in rows), 11)

    def test_every_registered_adapter_reaches_the_tuple_table_and_the_v3_schemas(self):
        """A registered adapter the v3 documents do not name is the drift."""
        registered = sorted(release_v2.ADAPTERS)
        self.assertEqual(
            column(tuple_table(), "venue"),
            registered,
            "the tuple table does not cover every adapter in release_v2.ADAPTERS",
        )
        for name, pointer in (
            (EVENT_V3, "properties/venue"),
            (EVENT_V3, "properties/provenance/properties/adapter"),
            (COVERAGE_V3, "properties/versions/properties/adapter/properties/name"),
        ):
            with self.subTest(schema=name, field=pointer):
                self.assert_enum_equals(name, pointer, load_schema(name), registered)

    def test_event_v3_enums_consts_and_branches_equal_the_tuple_table(self):
        self.check_event_v3(EVENT_V3, load_schema(EVENT_V3))

    def test_coverage_v3_enums_consts_and_branches_equal_the_tuple_table(self):
        self.check_coverage_v3(COVERAGE_V3, load_schema(COVERAGE_V3))

    def test_event_v3_keeps_the_v2_envelope_outside_the_tuple_fields(self):
        v2 = load_schema(EVENT_V2)
        v3 = load_schema(EVENT_V3)
        self.assertEqual(v3["required"], v2["required"])
        self.assertEqual(
            v3["properties"]["provenance"]["required"],
            v2["properties"]["provenance"]["required"],
        )
        tuple_fields = {"schema_version", "venue", "provenance"}
        for key in v2["properties"]:
            if key not in tuple_fields:
                self.assertEqual(v3["properties"][key], v2["properties"][key], key)
        provenance_tuple = {
            "adapter", "adapter_version", "protocol_generation", "source_api", "mapping_rule",
        }
        for key in v2["properties"]["provenance"]["properties"]:
            if key not in provenance_tuple:
                self.assertEqual(
                    v3["properties"]["provenance"]["properties"][key],
                    v2["properties"]["provenance"]["properties"][key],
                    key,
                )

    def test_coverage_v3_keeps_the_v2_envelope_outside_the_tuple_fields(self):
        v2 = load_schema(COVERAGE_V2)
        v3 = load_schema(COVERAGE_V3)
        self.assertEqual(v3["required"], v2["required"])
        self.assertEqual(v3["$defs"], v2["$defs"])
        for key in ("release", "capture_manifest", "canonical", "coverage", "known_gaps"):
            self.assertEqual(v3["properties"][key], v2["properties"][key], key)
        source_tuple = {"evidence_class", "protocol_generation", "source_api"}
        for key in v2["properties"]["source"]["properties"]:
            if key not in source_tuple:
                self.assertEqual(
                    v3["properties"]["source"]["properties"][key],
                    v2["properties"]["source"]["properties"][key],
                    key,
                )

    def test_dropping_one_tuple_value_is_caught_with_file_field_and_value_named(self):
        event = load_schema(EVENT_V3)
        coverage = load_schema(COVERAGE_V3)
        cases = (
            (EVENT_V3, event, self.check_event_v3, "properties/venue", aave_v4.ADAPTER),
            (
                EVENT_V3,
                event,
                self.check_event_v3,
                "properties/provenance/properties/adapter_version",
                aave_v4.ADAPTER_VERSION,
            ),
            (
                EVENT_V3,
                event,
                self.check_event_v3,
                "properties/provenance/properties/mapping_rule",
                euler_v2.MAPPINGS["pull_debt"][2],
            ),
            (
                COVERAGE_V3,
                coverage,
                self.check_coverage_v3,
                "properties/source/properties/evidence_class",
                release_v2.EVIDENCE_CLASSES[euler_v1.ADAPTER],
            ),
            (
                COVERAGE_V3,
                coverage,
                self.check_coverage_v3,
                "properties/source/properties/source_api",
                euler_v2.SOURCE_API,
            ),
        )
        for name, schema, check, pointer, value in cases:
            with self.subTest(schema=name, field=pointer, value=value):
                edited = copy.deepcopy(schema)
                walk(edited, pointer)["enum"].remove(value)
                with self.assertRaises(AssertionError) as caught:
                    check(name, edited)
                message = str(caught.exception)
                self.assertIn(name, message)
                self.assertIn(pointer, message)
                self.assertIn(value, message)

    def test_dropping_one_one_of_branch_is_caught(self):
        for name, check in ((EVENT_V3, self.check_event_v3), (COVERAGE_V3, self.check_coverage_v3)):
            with self.subTest(schema=name):
                edited = load_schema(name)
                edited["oneOf"].pop()
                with self.assertRaises(AssertionError) as caught:
                    check(name, edited)
                self.assertIn(name, str(caught.exception))
                self.assertIn("oneOf", str(caught.exception))

    def test_repointing_one_branch_const_to_another_row_is_caught(self):
        edited = load_schema(EVENT_V3)
        branch = self.branch_for(EVENT_V3, edited, "properties/venue", euler_v1.ADAPTER)
        pointer = "properties/provenance/properties/source_api"
        walk(branch, pointer)["const"] = euler_v2.SOURCE_API
        with self.assertRaises(AssertionError) as caught:
            self.check_event_v3(EVENT_V3, edited)
        message = str(caught.exception)
        self.assertIn(EVENT_V3, message)
        self.assertIn(pointer, message)
        self.assertIn(euler_v2.SOURCE_API, message)


class V2SchemaDeprecationTests(unittest.TestCase):
    def test_v2_documents_keep_their_id_and_are_marked_superseded(self):
        for name, successor in DEPRECATED.items():
            with self.subTest(schema=name):
                schema = load_schema(name)
                self.assertEqual(
                    schema["$id"], "https://wildcat.finance/schemas/tabularium/" + name
                )
                self.assertIs(schema["deprecated"], True, name)
                self.assertIn(successor, schema["description"], name)
                self.assertRegex(schema["description"], r"20\d\d-\d\d-\d\d", name)
                self.assertEqual(schema["properties"]["schema_version"]["const"], 2, name)

    def test_v2_event_document_admits_every_value_the_python_validator_admits(self):
        schema = load_schema(EVENT_V2)
        provenance = schema["properties"]["provenance"]["properties"]
        for row in tuple_table():
            with self.subTest(adapter=row["adapter"]):
                for field, node in (
                    ("venue", schema["properties"]["venue"]),
                    ("adapter", provenance["adapter"]),
                    ("adapter_version", provenance["adapter_version"]),
                    ("protocol_generation", provenance["protocol_generation"]),
                    ("source_api", provenance["source_api"]),
                ):
                    self.assertTrue(
                        admits(node, row[field]),
                        "%s: %s refuses %r, which %s emits"
                        % (EVENT_V2, field, row[field], row["adapter"]),
                    )
                for rule in row["mapping_rules"]:
                    self.assertTrue(
                        admits(provenance["mapping_rule"], rule),
                        "%s: mapping_rule refuses %r" % (EVENT_V2, rule),
                    )

    def test_v2_coverage_document_admits_every_value_the_python_validator_admits(self):
        schema = load_schema(COVERAGE_V2)
        source = schema["properties"]["source"]["properties"]
        adapter = schema["properties"]["versions"]["properties"]["adapter"]["properties"]
        rules = schema["properties"]["versions"]["properties"]["mapping_rules"]["items"]
        for row in tuple_table():
            with self.subTest(adapter=row["adapter"]):
                for field, node, value in (
                    ("source.evidence_class", source["evidence_class"], row["evidence_class"]),
                    ("source.protocol_generation", source["protocol_generation"], row["protocol_generation"]),
                    ("source.source_api", source["source_api"], row["source_api"]),
                    ("versions.adapter.name", adapter["name"], row["adapter"]),
                    ("versions.adapter.version", adapter["version"], row["adapter_version"]),
                ):
                    self.assertTrue(
                        admits(node, value),
                        "%s: %s refuses %r, which %s emits"
                        % (COVERAGE_V2, field, value, row["adapter"]),
                    )
                for rule in row["mapping_rules"]:
                    self.assertTrue(
                        admits(rules, rule),
                        "%s: versions.mapping_rules refuses %r" % (COVERAGE_V2, rule),
                    )
                self.assertGreaterEqual(
                    len(KNOWN_GAPS[row["adapter"]]),
                    schema["properties"]["known_gaps"]["minItems"],
                )


@REQUIRES_JSONSCHEMA
class ShippedDocumentParityTests(unittest.TestCase):
    """Every shipped document validates against the schema its version names.

    A release says which envelope it was written to in `schema_version`, so the
    document is validated against that version's schema file, not against the
    current one.  The three v0 releases say 2, which is what the corrected and
    superseded v2 files describe.
    """

    maxDiff = None

    def check_release(self, name):
        manifest, rows = support.release_documents(name)
        version = manifest["schema_version"]
        self.assertIn(version, SUPPORTED_EVENT_SCHEMAS, name)
        self.assertEqual(manifest["versions"]["event_schema"], version, name)
        self.assertEqual(
            support.schema_refusal_fields(support.coverage_schema(version), manifest),
            [],
            "%s: coverage.json is refused by coverage-manifest-v%d.json"
            % (name, version),
        )
        schema = support.event_schema(version)
        adapter_module = release_v2.ADAPTERS[manifest["versions"]["adapter"]["name"]]
        self.assertTrue(rows, "%s: events.jsonl is empty" % name)
        for index, row in enumerate(rows, start=1):
            with self.subTest(row=index):
                self.assertEqual(row["schema_version"], version)
                self.assertEqual(
                    support.schema_refusal_fields(schema, row),
                    [],
                    "%s: row %d is refused by canonical-event-v%d.json"
                    % (name, index, version),
                )
                self.assertIsNone(
                    support.library_refusal_field(
                        row, adapter_module, version, index
                    ),
                    "%s: row %d is refused by validate_event_row" % (name, index),
                )

    def test_every_shipped_release_directory_carries_a_parity_case(self):
        """The declared release list matches the tree and the cases above.

        `Exit` asks for every shipped `events.jsonl` row and `coverage.json`,
        and the cases below name their releases one at a time.  A fourth
        canonical release would be covered by nothing and fail nothing, so the
        declared list is bound here to what is on disk and to the case names,
        and it is this test rather than a silent gap that reports the drift.
        A directory with no `coverage.json` is not a canonical release: the
        Compound v3 Phase 0 witness is a different artefact and stays out.
        """
        on_disk = {
            directory.name
            for directory in support.EXAMPLES.iterdir()
            if (directory / "coverage.json").is_file()
        }
        self.assertEqual(set(support.SHIPPED_RELEASES), on_disk)
        cases = [name for name in dir(self) if name.startswith("test_")]
        for release in support.SHIPPED_RELEASES:
            with self.subTest(release=release):
                self.assertTrue(
                    any(release.replace("-", "_") in case for case in cases),
                    "%s has no parity case of its own" % release,
                )

    def test_aave_v4_v0_documents_validate_against_their_named_schema(self):
        self.check_release("aave-v4-v0")

    def test_euler_v1_v0_documents_validate_against_their_named_schema(self):
        self.check_release("euler-v1-v0")

    def test_euler_v2_v0_documents_validate_against_their_named_schema(self):
        self.check_release("euler-v2-v0")


@REQUIRES_JSONSCHEMA
class RejectionParityTests(unittest.TestCase):
    """Both validators refuse each committed fixture, naming the same field."""

    maxDiff = None

    def assert_parity(self, row, expected_field):
        observation = support.parity_observation(row, expected_field)
        self.assertTrue(observation["agreed"], support.parity_disagreement(observation))
        return observation

    def check_fixture(self, name, expected_field):
        row = support.load_rejection_fixture(name)
        observation = self.assert_parity(row, expected_field)
        self.assertEqual(observation["schema_fields"], [expected_field], name)
        self.assertEqual(observation["library_field"], expected_field, name)

    def test_every_declared_rejection_fixture_carries_a_case(self):
        """The reporter's evidence set matches the tree and the cases below.

        `prove_schema_v3.py` computes the value it attests by walking
        `support.REJECTION_FIXTURES`, and nothing else reads that tuple.
        Emptied, it left the suite green while the reporter wrote
        `"value": true` over no fixtures at all, because `all(())` is true and
        the closed `protasis-design-report/v1` key set has nowhere to record a
        count.  The declared set is bound here to the committed fixture files
        and to the case names, so the evidence set cannot shrink in silence.
        """
        declared = [name for name, _ in support.REJECTION_FIXTURES]
        self.assertTrue(declared, "the reporter would attest a vacuous pass")
        on_disk = {
            path.stem
            for path in support.SCHEMA_V3_FIXTURES.iterdir()
            if path.suffix == ".json"
        }
        self.assertEqual(set(declared), on_disk)
        cases = [name for name in dir(self) if name.startswith("test_")]
        for fixture in declared:
            with self.subTest(fixture=fixture):
                self.assertTrue(
                    any(fixture.replace("-", "_") in case for case in cases),
                    "%s has no rejection case of its own" % fixture,
                )

    def test_unknown_value_is_refused_by_both_validators(self):
        self.check_fixture("unknown-value", "provenance.mapping_rule")

    def test_wrong_version_is_refused_by_both_validators(self):
        self.check_fixture("wrong-version", "schema_version")

    def test_malformed_provenance_is_refused_by_both_validators(self):
        self.check_fixture("malformed-provenance", "provenance.source_selector")

    def test_a_row_only_one_validator_refuses_fails_the_parity_check(self):
        """A one-sided refusal is a disagreement, never a pass.

        The row carries one provenance key the closed v3 key set does not name.
        `jsonschema` refuses it by name through `additionalProperties`;
        `validate_event_row` checks the tuple table and the presence of the
        eleven named provenance fields and does not police the key set, so it
        admits the row.  The parity assertion has to fail on that, which is what
        keeps a fixture either validator accepts out of a passing report.
        """
        row = support.load_rejection_fixture("unknown-value")
        row["provenance"]["mapping_rule"] = "aave-v4.borrow.v2"
        row["provenance"]["operator_note"] = "not a field of the closed key set"
        observation = support.parity_observation(row, "provenance.operator_note")
        self.assertEqual(observation["schema_fields"], ["provenance.operator_note"])
        self.assertIsNone(observation["library_field"])
        with self.assertRaises(self.failureException):
            self.assert_parity(row, "provenance.operator_note")


class ReporterCommandTests(unittest.TestCase):
    """The report's `command` names the arguments that produced its value."""

    @REQUIRES_JSONSCHEMA
    def test_the_report_command_names_the_arguments_it_was_given(self):
        """Read from `sys.argv`, the field would name a command that never ran.

        `design_evidence.py` compares this string against the resolver the
        design record binds, so it is evidence.  Calling `main` in process is
        what the suite does, and under the host's own `sys.argv` the report
        would carry the runner's arguments instead of the reporter's.
        """
        with scratch_directory() as directory:
            report = Path(directory) / "rejection-parity.json"
            with contextlib.redirect_stdout(io.StringIO()):
                code = prove_schema_v3.main(
                    [
                        "--candidate", "superseding-releases",
                        "--criterion", "rejection-parity",
                        "--report", str(report),
                    ]
                )
            self.assertEqual(code, 0)
            written = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(
            written["command"],
            "python3 plugins/tabularium/tests/prove_schema_v3.py "
            "--candidate superseding-releases --criterion rejection-parity "
            "--report %s" % report,
        )


    @REQUIRES_JSONSCHEMA
    def test_a_report_path_with_a_space_is_recorded_as_one_argument(self):
        """Joined with plain spaces, such a path read as two arguments.

        The field names the command that produced the value, and a reader
        splitting it on whitespace would have recovered a `--report` nobody
        passed.  Quoting only where quoting is needed keeps every resolver
        string the design record declares byte-identical.
        """
        with scratch_directory() as directory:
            report = Path(directory) / "rejection parity.json"
            with contextlib.redirect_stdout(io.StringIO()):
                code = prove_schema_v3.main(
                    [
                        "--candidate", "superseding-releases",
                        "--criterion", "rejection-parity",
                        "--report", str(report),
                    ]
                )
            self.assertEqual(code, 0)
            recorded = json.loads(report.read_text(encoding="utf-8"))["command"]
        self.assertEqual(shlex.split(recorded)[-1], str(report))
        self.assertIn("'%s'" % report, recorded)


class ReporterAtomicWriteTests(unittest.TestCase):
    """A failed write leaves the report that was already there untouched."""

    def test_a_failure_between_staging_and_renaming_keeps_the_old_report(self):
        """The rename is the only moment the report changes.

        Staging removed the truncation window; this covers the other half.  A
        failure after the staged bytes are written and before they replace the
        report leaves the earlier report whole and no staged file behind.
        """
        with scratch_directory() as directory:
            report = Path(directory) / "rejection-parity.json"
            prior = json.dumps({"schema": "protasis-design-report/v1"}) + "\n"
            report.write_text(prior, encoding="utf-8")
            replaced = os.replace

            def refuse(source, target):
                raise OSError(errno.EIO, "Input/output error")

            os.replace = refuse
            try:
                with self.assertRaises(prove_schema_v3.ReportRefused):
                    prove_schema_v3.write_report(report, {"value": True})
            finally:
                os.replace = replaced
            self.assertEqual(report.read_text(encoding="utf-8"), prior)
            self.assertEqual(
                [path.name for path in Path(directory).iterdir()], [report.name]
            )

    def test_a_failed_write_does_not_destroy_the_previous_report(self):
        """Opened with `O_TRUNC`, the report was emptied before any byte landed.

        The risk register's `partial-write` entry is the convention this
        follows: a killed run leaves no half-written artefact.  The reporter
        was the one writer in the tree that did not, so a failure after the
        open left zero bytes where a valid report had been.
        """
        with scratch_directory() as directory:
            report = Path(directory) / "rejection-parity.json"
            prior = json.dumps({"schema": "protasis-design-report/v1"}) + "\n"
            report.write_text(prior, encoding="utf-8")
            written = os.write

            def refuse(handle, payload):
                raise OSError(errno.ENOSPC, "No space left on device")

            os.write = refuse
            try:
                # The refusal's type is not what is under test and the parent
                # let the OSError escape unwrapped, so the file state below is
                # reached either way and is the assertion that matters.
                with self.assertRaises(Exception):
                    prove_schema_v3.write_report(report, {"value": True})
            finally:
                os.write = written
            self.assertEqual(report.read_text(encoding="utf-8"), prior)
            self.assertEqual(
                [path.name for path in Path(directory).iterdir()],
                [report.name],
                "a staged file was left behind",
            )


class ReporterRefusalTests(unittest.TestCase):
    """The design reporter's two refusals, both of which write nothing."""

    def report_argv(self, path):
        return [
            "--candidate", "superseding-releases",
            "--criterion", "rejection-parity",
            "--report", str(path),
        ]

    def test_the_reporter_refuses_to_write_when_jsonschema_is_absent(self):
        with scratch_directory() as directory:
            report = Path(directory) / "rejection-parity.json"
            stderr = io.StringIO()
            with mock.patch.dict(sys.modules, {"jsonschema": None}):
                with contextlib.redirect_stderr(stderr):
                    code = prove_schema_v3.main(self.report_argv(report))
            self.assertEqual(code, 1)
            self.assertEqual(stderr.getvalue().strip(), support.JSONSCHEMA_ABSENT)
            self.assertFalse(report.exists(), "a skip left a report behind")

    @REQUIRES_JSONSCHEMA
    def test_the_reporter_refuses_a_symlinked_report_component(self):
        with scratch_directory() as directory:
            root = Path(directory)
            (root / "real").mkdir()
            os.symlink(root / "real", root / "link")
            report = root / "link" / "rejection-parity.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = prove_schema_v3.main(self.report_argv(report))
            self.assertEqual(code, 2)
            self.assertIn("symlink", stderr.getvalue())
            self.assertFalse((root / "real" / "rejection-parity.json").exists())


if __name__ == "__main__":
    unittest.main()
