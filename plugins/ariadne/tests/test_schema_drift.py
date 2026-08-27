"""The published schemas and the validators, held to the same field tables.

Two things describe each predicate: the schema under `schemas/`, which other
producers read, and the module under `predicates/`, which decides what this tool
accepts. A field added to one and not the other is a disagreement nobody would
notice until somebody else's statement failed here for a reason their schema said
was fine.

Every shipped predicate needs a schema and a drift class. The completeness test
at the bottom fails when one ships without them.
"""

import ast
import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import core_predicate  # noqa: E402
from ariadne_lib import registry  # noqa: E402
from ariadne_lib.predicates import dataset  # noqa: E402
from ariadne_lib.predicates import grounded_agent  # noqa: E402
from ariadne_lib.predicates import solidity_release as release  # noqa: E402
from ariadne_lib.predicates import state_fixture  # noqa: E402

SCHEMAS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas"
)
SCHEMA = os.path.join(SCHEMAS, "solidity-release-v1.json")
DATASET_SCHEMA = os.path.join(SCHEMAS, "dataset-v1.json")
STATE_FIXTURE_SCHEMA = os.path.join(SCHEMAS, "state-fixture-v1.json")
STATE_FIXTURE_V2_SCHEMA = os.path.join(SCHEMAS, "state-fixture-v2.json")
GROUNDED_AGENT_SCHEMA = os.path.join(SCHEMAS, "grounded-agent-v1.json")

SHIPPED = (
    (release, SCHEMA),
    (dataset, DATASET_SCHEMA),
    (state_fixture, STATE_FIXTURE_SCHEMA),
    (state_fixture.V2, STATE_FIXTURE_V2_SCHEMA),
    (grounded_agent, GROUNDED_AGENT_SCHEMA),
)
"""Each shipped predicate and its published schema."""


def read_schema(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def schema():
    return read_schema(SCHEMA)


class SchemaDriftTests(unittest.TestCase):
    def setUp(self):
        self.schema = schema()
        self.properties = self.schema["properties"]

    def test_the_schema_names_this_predicate_type(self):
        self.assertIn(release.TYPE, self.schema["description"])

    def test_the_top_level_fields_match_the_module(self):
        self.assertEqual(sorted(self.properties), sorted(release.PREDICATE_FIELDS))
        self.assertEqual(self.schema["required"], list(release.REQUIRED_FIELDS))

    def test_the_source_fields_match(self):
        self.assertEqual(
            self.properties["source"]["required"], list(release.SOURCE_REQUIRED)
        )

    def test_the_revision_pattern_matches_the_validator(self):
        """A schema that accepted `main` would send a producer straight into a
        refusal here, which is the drift this test exists to catch."""
        self.assertEqual(
            self.properties["source"]["properties"]["commit"]["pattern"],
            release.REVISION.pattern,
        )
        self.assertEqual(
            self.properties["audits"]["items"]["properties"]["covered_revision"][
                "pattern"
            ],
            release.REVISION.pattern,
        )

    def test_the_build_fields_match(self):
        self.assertEqual(
            self.properties["build"]["required"], list(release.BUILD_REQUIRED)
        )
        self.assertEqual(
            self.properties["build"]["properties"]["optimizer"]["required"],
            list(release.OPTIMIZER_REQUIRED),
        )

    def test_the_release_subject_fields_match(self):
        self.assertEqual(
            self.properties["release_subjects"]["items"]["required"],
            list(release.RELEASE_SUBJECT_REQUIRED),
        )

    def test_the_audit_and_deployment_fields_match(self):
        self.assertEqual(
            self.properties["audits"]["items"]["required"], list(release.AUDIT_REQUIRED)
        )
        self.assertEqual(
            self.properties["deployments"]["items"]["required"],
            list(release.DEPLOYMENT_REQUIRED),
        )

    def test_the_delta_sections_match(self):
        sections = set(self.properties["deltas"]["properties"])
        self.assertEqual(
            sections, set(release.DELTA_SECTIONS) | {"baseline", "current", "reason"}
        )

    def test_the_core_vocabularies_match(self):
        claims = self.properties["claims"]["items"]["properties"]
        commands = self.properties["commands"]["items"]["properties"]
        self.assertEqual(
            claims["disposition"]["enum"], list(core_predicate.DISPOSITIONS)
        )
        self.assertEqual(
            commands["determinism"]["enum"], list(core_predicate.DETERMINISM)
        )
        self.assertEqual(
            sorted(claims), sorted(core_predicate.CLAIM_FIELDS)
        )
        self.assertEqual(
            sorted(commands), sorted(core_predicate.COMMAND_FIELDS)
        )

    def test_the_schema_is_committed_as_readable_json(self):
        with open(SCHEMA, "rb") as handle:
            raw = handle.read()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(
            json.loads(raw.decode("utf-8"))["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )


class DatasetSchemaDriftTests(unittest.TestCase):
    def setUp(self):
        self.schema = read_schema(DATASET_SCHEMA)
        self.properties = self.schema["properties"]

    def test_the_schema_names_this_predicate_type(self):
        self.assertIn(dataset.TYPE, self.schema["description"])

    def test_the_top_level_fields_match_the_module(self):
        self.assertEqual(sorted(self.properties), sorted(dataset.PREDICATE_FIELDS))
        self.assertEqual(self.schema["required"], list(dataset.REQUIRED_FIELDS))

    def test_the_producer_fields_match(self):
        self.assertEqual(
            self.properties["producer"]["required"], list(dataset.PRODUCER_REQUIRED)
        )

    def test_the_input_fields_match(self):
        self.assertEqual(
            self.properties["inputs"]["items"]["required"], list(dataset.INPUT_REQUIRED)
        )
        self.assertEqual(
            sorted(self.properties["inputs"]["items"]["properties"]),
            sorted(dataset.INPUT_FIELDS),
        )

    def test_the_released_file_fields_match(self):
        self.assertEqual(
            self.properties["dataset_subjects"]["items"]["required"],
            list(dataset.DATASET_SUBJECT_REQUIRED),
        )

    def test_the_coverage_and_gap_fields_match(self):
        self.assertEqual(
            self.properties["coverage"]["required"], list(dataset.COVERAGE_KEYS)
        )
        gap = self.properties["coverage"]["properties"]["gaps"]["items"]
        self.assertEqual(gap["required"], list(dataset.GAP_REQUIRED))
        self.assertEqual(sorted(gap["properties"]), sorted(dataset.GAP_FIELDS))

    def test_the_delta_sections_match(self):
        sections = set(self.properties["deltas"]["properties"])
        self.assertEqual(
            sections, set(dataset.DELTA_SECTIONS) | {"baseline", "current", "reason"}
        )

    def test_the_both_sided_sections_require_both_sides(self):
        records = self.properties["deltas"]["properties"]["records"]["properties"]
        for section in dataset.BOTH_SIDED:
            with self.subTest(section=section):
                self.assertEqual(
                    records[section]["items"]["required"], ["baseline", "current"]
                )

    def test_the_released_file_constraints_match_the_gate(self):
        """The gate refuses a negative count and a path that is absolute or carries
        a .. segment. A schema that allowed either would send a producer straight
        into a refusal here."""
        props = self.properties["dataset_subjects"]["items"]["properties"]
        self.assertEqual(props["record_count"]["minimum"], 0)
        self.assertEqual(props["path"]["minLength"], 1)
        self.assertFalse(dataset.usable_path("/etc/passwd"))
        self.assertFalse(dataset.usable_path("../outside.jsonl"))
        self.assertFalse(dataset.usable_path("by-pool/../../outside.jsonl"))
        self.assertTrue(dataset.usable_path("events.jsonl"))
        self.assertTrue(dataset.usable_path("by-pool/pool-a.jsonl"))

    def test_the_coverage_bounds_are_integers(self):
        """The module refuses a bound that is not a whole number, so a schema
        allowing a string would send a producer straight into a refusal here."""
        coverage = self.properties["coverage"]["properties"]
        for field in ("start", "end"):
            with self.subTest(field=field):
                self.assertEqual(coverage[field]["type"], "integer")
        gap = coverage["gaps"]["items"]["properties"]
        for field in ("start", "end"):
            with self.subTest(gap_field=field):
                self.assertEqual(gap[field]["type"], "integer")
        self.assertEqual(
            self.properties["dataset_subjects"]["items"]["properties"]["record_count"][
                "type"
            ],
            "integer",
        )

    def test_the_core_vocabularies_match(self):
        claims = self.properties["claims"]["items"]["properties"]
        commands = self.properties["commands"]["items"]["properties"]
        self.assertEqual(
            claims["disposition"]["enum"], list(core_predicate.DISPOSITIONS)
        )
        self.assertEqual(
            commands["determinism"]["enum"], list(core_predicate.DETERMINISM)
        )
        self.assertEqual(sorted(claims), sorted(core_predicate.CLAIM_FIELDS))
        self.assertEqual(sorted(commands), sorted(core_predicate.COMMAND_FIELDS))
        self.assertEqual(
            self.properties["inputs"]["items"]["properties"]["disposition"]["enum"],
            list(dataset.INPUT_DISPOSITIONS),
        )
        self.assertNotIn(
            "passed",
            self.properties["inputs"]["items"]["properties"]["disposition"]["enum"],
            "an input that was read carries a digest, not a passed disposition",
        )

    def test_the_schema_is_committed_as_readable_json(self):
        with open(DATASET_SCHEMA, "rb") as handle:
            raw = handle.read()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(
            json.loads(raw.decode("utf-8"))["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )



class StateFixtureSchemaDriftTests(unittest.TestCase):
    def setUp(self):
        self.schema = read_schema(STATE_FIXTURE_SCHEMA)
        self.properties = self.schema["properties"]

    def test_the_schema_names_this_predicate_type(self):
        self.assertIn(state_fixture.TYPE, self.schema["description"])

    def test_the_top_level_fields_match_the_module(self):
        self.assertEqual(
            sorted(self.properties), sorted(state_fixture.PREDICATE_FIELDS)
        )
        self.assertEqual(
            self.schema["required"], list(state_fixture.REQUIRED_FIELDS)
        )

    def test_the_pin_fields_match(self):
        self.assertEqual(
            self.properties["chain"]["required"],
            list(state_fixture.CHAIN_REQUIRED),
        )
        self.assertEqual(
            sorted(self.properties["chain"]["properties"]),
            sorted(state_fixture.CHAIN_FIELDS),
        )

    def test_the_state_root_is_not_required_by_the_shape(self):
        """It is required by what a statement claims, which is the evidence
        check's rule. Requiring it here would make that rule unreachable: a
        statement with no root would fail gate 2 first, and the rule refusing a
        proof-backed count without one would never decide anything."""
        self.assertNotIn("state_root", self.properties["chain"]["required"])
        self.assertNotIn("state_root", state_fixture.CHAIN_REQUIRED)
        self.assertIn("state_root", state_fixture.CHAIN_FIELDS)

    def test_the_capture_fields_match(self):
        self.assertEqual(
            self.properties["capture"]["required"],
            list(state_fixture.CAPTURE_REQUIRED),
        )

    def test_the_component_fields_match(self):
        self.assertEqual(
            self.properties["fixture_subjects"]["items"]["required"],
            list(state_fixture.FIXTURE_SUBJECT_REQUIRED),
        )

    def test_the_evidence_classes_match(self):
        self.assertEqual(
            self.properties["evidence"]["required"],
            list(state_fixture.EVIDENCE_CLASSES),
        )
        self.assertEqual(
            sorted(self.properties["evidence"]["properties"]),
            sorted(state_fixture.EVIDENCE_CLASSES),
        )

    def test_the_replay_fields_match_and_are_pinned_false(self):
        """The module accepts only `False`, so a schema allowing `true` would send
        a producer straight into a refusal here."""
        replay = self.properties["replay"]
        self.assertEqual(replay["required"], list(state_fixture.REPLAY_REQUIRED))
        for field in state_fixture.REPLAY_REQUIRED:
            with self.subTest(field=field):
                self.assertIs(replay["properties"][field]["const"], False)

    def test_the_delta_sections_match(self):
        sections = set(self.properties["deltas"]["properties"])
        self.assertEqual(
            sections,
            set(state_fixture.DELTA_SECTIONS) | {"baseline", "current", "reason"},
        )

    def test_the_both_sided_sections_require_both_sides(self):
        components = self.properties["deltas"]["properties"]["components"][
            "properties"
        ]
        for section in state_fixture.BOTH_SIDED:
            with self.subTest(section=section):
                self.assertEqual(
                    components[section]["items"]["required"], ["baseline", "current"]
                )

    def test_the_numbers_are_integers_rather_than_wire_strings(self):
        """A Lazarus manifest writes the chain id and the block number as hex
        quantity strings. The module refuses those, so a schema typing either as a
        string would publish a shape this tool will not accept."""
        chain = self.properties["chain"]["properties"]
        for field in ("chain_id", "block_number"):
            with self.subTest(field=field):
                self.assertEqual(chain[field]["type"], "integer")
        self.assertEqual(
            self.properties["fixture_subjects"]["items"]["properties"]["bytes"][
                "type"
            ],
            "integer",
        )

    def test_the_hash_patterns_accept_what_the_module_accepts(self):
        """Behaviour rather than the pattern string. The module refuses the
        all-zero hash inside `hash32` and the schema refuses it inside the
        pattern, so the two spell the same rule differently and comparing the
        text would fail on a disagreement that is not one."""
        import re

        candidates = (
            "0x" + "0f" * 32,
            "0x" + "0F" * 32,
            "0x" + "f" * 64,
            state_fixture.ZERO_HASH,
            "0x" + "f" * 63,
            "0x" + "f" * 65,
            "f" * 64,
            "0x",
            "",
        )
        chain = self.properties["chain"]["properties"]
        for field in ("block_hash", "state_root"):
            pattern = re.compile(chain[field]["pattern"])
            for value in candidates:
                with self.subTest(field=field, value=value):
                    self.assertEqual(
                        bool(pattern.match(value)),
                        state_fixture.hash32(value),
                        "%s: schema and module disagree on %r" % (field, value),
                    )

    def test_the_module_refuses_the_unset_hash(self):
        """It matches `HASH32` and identifies nothing, which is why the check is
        not the pattern alone."""
        self.assertTrue(state_fixture.HASH32.match(state_fixture.ZERO_HASH))
        self.assertFalse(state_fixture.hash32(state_fixture.ZERO_HASH))

    def test_the_published_bounds_are_the_ones_the_module_enforces(self):
        """Names matching is not enough. The schema carried a count ceiling of
        100000 before the module enforced one, so a statement with a larger count
        passed the verifier and was refused by the schema shipping beside it. Both
        ceilings come from Lazarus's manifest schema."""
        evidence = self.properties["evidence"]["properties"]
        for name in state_fixture.EVIDENCE_CLASSES:
            with self.subTest(evidence_class=name):
                self.assertEqual(evidence[name]["minimum"], 0)
                self.assertEqual(evidence[name]["maximum"], state_fixture.MAX_COUNT)
        component = self.properties["fixture_subjects"]["items"]["properties"]
        self.assertEqual(component["bytes"]["minimum"], 0)
        self.assertEqual(component["bytes"]["maximum"], state_fixture.MAX_BYTES)

    def test_the_component_constraints_match_the_gate(self):
        props = self.properties["fixture_subjects"]["items"]["properties"]
        self.assertEqual(props["bytes"]["minimum"], 0)
        self.assertEqual(props["bytes"]["maximum"], state_fixture.MAX_BYTES)
        self.assertEqual(props["path"]["minLength"], 1)
        self.assertFalse(state_fixture.usable_path("/etc/passwd"))
        self.assertFalse(state_fixture.usable_path("../outside.json"))
        self.assertFalse(state_fixture.usable_path("schemas/../../outside.json"))
        self.assertTrue(state_fixture.usable_path("manifest.json"))
        self.assertTrue(state_fixture.usable_path("schemas/header-v1.json"))


class StateFixtureV2SchemaDriftTests(unittest.TestCase):
    def setUp(self):
        self.schema = read_schema(STATE_FIXTURE_V2_SCHEMA)
        self.properties = self.schema["properties"]

    def test_the_schema_names_the_v2_predicate_type(self):
        self.assertIn(state_fixture.V2.TYPE, self.schema["$id"])

    def test_the_top_level_and_pin_fields_match_v2(self):
        self.assertEqual(
            sorted(self.properties), sorted(state_fixture.V2.PREDICATE_FIELDS)
        )
        self.assertEqual(
            self.schema["required"], list(state_fixture.V2.REQUIRED_FIELDS)
        )
        chain = self.properties["chain"]
        self.assertEqual(chain["required"], list(state_fixture.V2.CHAIN_REQUIRED))
        self.assertEqual(
            sorted(chain["properties"]), sorted(state_fixture.V2.CHAIN_FIELDS)
        )

    def test_each_proved_class_requires_only_its_own_root(self):
        found = {}
        for rule in self.schema["allOf"]:
            evidence = (
                rule.get("if", {})
                .get("properties", {})
                .get("evidence", {})
                .get("properties", {})
            )
            for evidence_class, condition in evidence.items():
                if condition.get("minimum") == 1:
                    found[evidence_class] = rule["then"]["properties"]["chain"][
                        "required"
                    ]
        self.assertEqual(
            found,
            {
                state_fixture.V2.PROVED: ["state_root"],
                state_fixture.V2.RECEIPT_PROVED: ["receipts_root"],
            },
        )

    def test_the_four_evidence_classes_and_bounds_match_v2(self):
        evidence = self.properties["evidence"]
        self.assertEqual(evidence["required"], list(state_fixture.V2.EVIDENCE_CLASSES))
        self.assertEqual(
            sorted(evidence["properties"]),
            sorted(state_fixture.V2.EVIDENCE_CLASSES),
        )
        for name in state_fixture.V2.EVIDENCE_CLASSES:
            with self.subTest(evidence_class=name):
                self.assertEqual(
                    evidence["properties"][name]["$ref"], "#/$defs/count"
                )
        count = self.schema["$defs"]["count"]
        self.assertEqual(count["minimum"], 0)
        self.assertEqual(count["maximum"], state_fixture.MAX_COUNT)

    def test_the_three_replay_claims_are_required_and_pinned_false(self):
        replay = self.properties["replay"]
        self.assertEqual(replay["required"], list(state_fixture.V2.REPLAY_REQUIRED))
        self.assertEqual(
            sorted(replay["properties"]),
            sorted(state_fixture.V2.REPLAY_REQUIRED),
        )
        for field in state_fixture.V2.REPLAY_REQUIRED:
            with self.subTest(field=field):
                self.assertIs(replay["properties"][field]["const"], False)

    def test_v2_replay_has_no_executable_commands(self):
        self.assertEqual(self.properties["commands"]["maxItems"], 0)

    def test_v2_deltas_require_the_explicit_absent_and_current_sides(self):
        self.assertEqual(
            self.properties["deltas"].get("required"), ["baseline", "current"]
        )

    def test_v2_machine_read_names_share_the_portable_graphic_shape(self):
        self.assertIn("portableText", self.schema["$defs"])
        portable = self.schema["$defs"]["portableText"]
        self.assertEqual(portable["pattern"], "[!-~]")
        self.assertEqual(
            self.properties["capture"]["properties"]["tool"],
            {"$ref": "#/$defs/portableText"},
        )
        self.assertEqual(
            self.properties["capture"]["properties"]["command"]["items"],
            {"$ref": "#/$defs/portableText"},
        )
        component = self.properties["fixture_subjects"]["items"]["properties"]
        self.assertEqual(
            component["name"], {"$ref": "#/$defs/portableText"}
        )
        self.assertEqual(
            self.schema["$defs"]["side"]["properties"]["name"],
            {"$ref": "#/$defs/portableText"},
        )
        self.assertEqual(
            self.properties["claims"]["items"]["properties"]["name"],
            {"$ref": "#/$defs/portableText"},
        )

        import re

        pattern = re.compile(portable["pattern"])
        for value, expected in (
            ("fixture", True),
            ("\u96ea.json", True),
            ("\u96ea fixture", True),
            ("\u200b", False),
            ("\x00", False),
            ("\ue000", False),
            ("\u2060", False),
        ):
            with self.subTest(value=repr(value)):
                self.assertEqual(bool(pattern.search(value)), expected)
                self.assertEqual(state_fixture.portable_name_v2(value), expected)

    def test_v2_hashes_and_component_bounds_match_the_module(self):
        import re

        chain = self.properties["chain"]["properties"]
        pattern = re.compile(self.schema["$defs"]["hash32"]["pattern"])
        candidates = (
            "0x" + "f" * 64,
            state_fixture.ZERO_HASH,
            "0x" + "f" * 63,
            "0x" + "F" * 64,
        )
        for field in ("block_hash", "state_root", "receipts_root"):
            self.assertEqual(chain[field]["$ref"], "#/$defs/hash32")
            for value in candidates:
                with self.subTest(field=field, value=value):
                    self.assertEqual(
                        bool(pattern.match(value)), state_fixture.hash32(value)
                    )
        component = self.properties["fixture_subjects"]["items"]["properties"]
        self.assertEqual(
            self.properties["fixture_subjects"]["maxItems"],
            getattr(state_fixture.V2, "MAX_FIXTURE_SUBJECTS", None),
        )
        self.assertEqual(component["bytes"]["maximum"], state_fixture.MAX_BYTES)
        self.assertEqual(component["path"]["maxLength"], 1024)
        path_check = getattr(state_fixture, "usable_path_v2", state_fixture.usable_path)
        for path in (
            "a\\b",
            ".",
            "./header.json",
            "a/./header.json",
            "a/\u200b",
            "a/\x00",
            "a/\ue000",
            "a/\u2060",
            "header.json/",
            "C:header.json",
            "1:header.json",
            "\u96ea:header.json",
            "header\x00.json",
            "x" * 1025,
        ):
            with self.subTest(path=path[:40]):
                self.assertFalse(path_check(path))

    def test_v2_digest_sets_require_one_supported_full_length_algorithm(self):
        digest = self.schema["$defs"]["digest"]
        self.assertEqual(
            {tuple(rule["required"]) for rule in digest.get("anyOf", [])},
            {("sha256",), ("sha384",), ("sha512",)},
        )
        self.assertEqual(
            {
                name: shape["pattern"]
                for name, shape in digest.get("properties", {}).items()
            },
            {
                "sha256": "^[0-9a-f]{64}$",
                "sha384": "^[0-9a-f]{96}$",
                "sha512": "^[0-9a-f]{128}$",
            },
        )


class GroundedAgentSchemaDriftTests(unittest.TestCase):
    def setUp(self):
        self.schema = read_schema(GROUNDED_AGENT_SCHEMA)
        self.properties = self.schema["properties"]

    def test_the_schema_names_the_predicate_type(self):
        self.assertIn(grounded_agent.TYPE, self.schema["$id"])
        self.assertIn(grounded_agent.BEREAN_FORMAT, self.schema["description"])

    def test_the_top_level_fields_match_the_module(self):
        self.assertEqual(
            sorted(self.properties), sorted(grounded_agent.PREDICATE_FIELDS)
        )
        self.assertEqual(
            self.schema["required"], list(grounded_agent.REQUIRED_FIELDS)
        )

    def test_every_closed_nested_field_table_matches(self):
        component = self.schema["$defs"]["component"]
        cases = (
            (self.properties["release"], grounded_agent.RELEASE_FIELDS),
            (self.properties["given"], grounded_agent.GIVEN_FIELDS),
            (
                self.properties["given"]["properties"]["corpus"],
                grounded_agent.CORPUS_FIELDS,
            ),
            (
                self.properties["given"]["properties"]["reads"]["oneOf"][1],
                grounded_agent.READS_FIELDS,
            ),
            (self.properties["produced"], grounded_agent.PRODUCED_FIELDS),
            (
                self.properties["produced"]["properties"]["evaluations"]["oneOf"][1],
                grounded_agent.EVALUATIONS_FIELDS,
            ),
            (
                self.properties["produced"]["properties"]["promotion"]["oneOf"][1],
                grounded_agent.PROMOTION_FIELDS,
            ),
            (
                self.properties["produced"]["properties"]["promotion"]["oneOf"][1]["properties"]["terminal"],
                grounded_agent.PROMOTION_TERMINAL_FIELDS,
            ),
            (self.properties["policy"], grounded_agent.POLICY_FIELDS),
            (
                self.properties["policy"]["properties"]["rules"],
                grounded_agent.RULES_FIELDS,
            ),
            (
                self.properties["policy"]["properties"]["allowlists"],
                grounded_agent.ALLOWLIST_FIELDS,
            ),
            (self.properties["adapter"], grounded_agent.ADAPTER_FIELDS),
            (self.properties["comparison"], grounded_agent.COMPARISON_FIELDS),
            (self.schema["$defs"]["comparisonSide"], grounded_agent.COMPARISON_SIDE_FIELDS),
            (component, grounded_agent.COMPONENT_FIELDS),
        )
        for shape, fields in cases:
            with self.subTest(fields=fields):
                self.assertEqual(shape["required"], list(fields))
                self.assertEqual(sorted(shape["properties"]), sorted(fields))
                self.assertIs(shape["additionalProperties"], False)

    def test_component_and_collection_bounds_match(self):
        component = self.schema["$defs"]["component"]["properties"]
        self.assertEqual(component["bytes"]["maximum"], grounded_agent.MAX_COMPONENT_BYTES)
        self.assertEqual(self.schema["$defs"]["path"]["maxLength"], grounded_agent.MAX_PATH)
        corpus = self.properties["given"]["properties"]["corpus"]["properties"]["components"]
        answers = self.properties["produced"]["properties"]["answers"]
        self.assertEqual(corpus["maxItems"], grounded_agent.MAX_COMPONENTS)
        self.assertEqual(answers["maxItems"], grounded_agent.MAX_COMPONENTS)

    def test_portable_name_and_path_patterns_match_the_module(self):
        import re

        name_pattern = re.compile(self.schema["$defs"]["portableName"]["pattern"])
        for value, expected in (
            ("release-v1", True),
            ("e\u0301 release", True),
            ("x\u200b", True),
            ("x\ue000", True),
            ("\u200b", False),
            ("\ue000", False),
            (" leading", False),
            ("trailing ", False),
            ("line\nbreak", False),
        ):
            with self.subTest(kind="name", value=repr(value)):
                self.assertEqual(bool(name_pattern.search(value)), expected)
                self.assertEqual(grounded_agent.portable_name(value), expected)

        path_pattern = re.compile(self.schema["$defs"]["path"]["pattern"])
        for value, expected in (
            ("corpus/terms.md", True),
            ("corpus/e\u0301-terms.md", True),
            ("corpus/x\u200b.json", True),
            ("corpus/x\ue000.json", True),
            ("corpus/ leading.json", False),
            ("corpus/trailing.json ", False),
            ("corpus/line\nbreak.json", False),
            ("corpus/\u200b", False),
            ("corpus//terms.md", False),
            ("corpus/terms.md\\", False),
            ("../outside.json", False),
            ("corpus\\outside.json", False),
        ):
            with self.subTest(kind="path", value=repr(value)):
                self.assertEqual(bool(path_pattern.search(value)), expected)
                self.assertEqual(grounded_agent.usable_path(value), expected)

    def test_policy_vocabularies_match_the_checked_copies(self):
        rules = self.properties["policy"]["properties"]["rules"]["properties"]
        self.assertEqual(
            rules["source_classes"]["const"], list(grounded_agent.BEREAN_SOURCE_CLASSES)
        )
        self.assertEqual(
            rules["evidence_classes"]["const"], list(grounded_agent.BEREAN_EVIDENCE_CLASSES)
        )
        self.assertEqual(
            self.properties["policy"]["properties"]["retention"]["enum"],
            list(grounded_agent.BEREAN_RETENTION),
        )

    def test_comparison_requires_explicit_absence_and_current(self):
        self.assertEqual(
            self.properties["comparison"]["required"],
            list(grounded_agent.COMPARISON_FIELDS),
        )
        self.assertEqual(
            self.schema["$defs"]["comparisonSide"]["required"],
            list(grounded_agent.COMPARISON_SIDE_FIELDS),
        )

    def test_optional_blocks_pair_null_with_a_stated_reason(self):
        given = self.properties["given"]
        produced = self.properties["produced"]
        expected = (
            (given, "reads", "reads_absence_reason"),
            (produced, "evaluations", "evaluations_absence_reason"),
            (produced, "promotion", "promotion_absence_reason"),
        )
        for shape, block, reason in expected:
            rules = shape["allOf"]
            null_rules = [
                rule
                for rule in rules
                if rule["if"]["properties"].get(block) == {"type": "null"}
            ]
            object_rules = [
                rule
                for rule in rules
                if rule["if"]["properties"].get(block) == {"type": "object"}
                and reason in rule["then"]["properties"]
            ]
            with self.subTest(block=block):
                self.assertEqual(len(null_rules), 1)
                self.assertEqual(
                    null_rules[0]["then"]["properties"][reason],
                    {"$ref": "#/$defs/stated"},
                )
                self.assertEqual(len(object_rules), 1)
                self.assertEqual(
                    object_rules[0]["then"]["properties"][reason],
                    {"type": "null"},
                )

    def test_promotion_boundaries_match_the_checked_projection(self):
        limit = getattr(grounded_agent, "BEREAN_MAX_PROMOTION_RECORDS", None)
        self.assertEqual(limit, 1000)
        produced = self.properties["produced"]
        promotion = produced["properties"]["promotion"]["oneOf"][1]
        terminal = promotion["properties"]["terminal"]
        sequence = terminal["properties"]["sequence"]
        self.assertEqual(sequence.get("minimum"), 1)
        self.assertEqual(
            sequence.get("maximum"), limit
        )
        rollback = terminal.get("allOf", [])
        self.assertIn(
            {
                "if": {"properties": {"action": {"const": "rollback"}}},
                "then": {"properties": {"sequence": {"minimum": 2}}},
            },
            rollback,
        )
        self.assertIn(
            {
                "if": {"properties": {"promotion": {"type": "object"}}},
                "then": {"properties": {"evaluations": {"type": "object"}}},
            },
            produced["allOf"],
        )

    def test_core_vocabularies_match(self):
        claims = self.properties["claims"]["items"]["properties"]
        commands = self.properties["commands"]["items"]["properties"]
        self.assertEqual(claims["disposition"]["enum"], list(core_predicate.DISPOSITIONS))
        self.assertEqual(commands["determinism"]["enum"], list(core_predicate.DETERMINISM))
        self.assertEqual(sorted(claims), sorted(core_predicate.CLAIM_FIELDS))
        self.assertEqual(sorted(commands), sorted(core_predicate.COMMAND_FIELDS))

    def test_the_schema_is_committed_as_readable_json(self):
        with open(GROUNDED_AGENT_SCHEMA, "rb") as handle:
            raw = handle.read()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(
            json.loads(raw.decode("utf-8"))["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )


def literal_assignments(path):
    """Literal public constants from a sibling module, without importing it."""
    with open(path, "rb") as handle:
        tree = ast.parse(handle.read(), filename=path)
    found = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            found[target.id] = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue
    return found


class BereanPublicConstantDriftTests(unittest.TestCase):
    def setUp(self):
        repo = os.path.dirname(os.path.dirname(os.path.dirname(SCHEMAS)))
        self.library = os.path.join(repo, "plugins", "berean", "scripts", "berean_lib")
        if not os.path.isdir(self.library):
            self.skipTest("the sibling Berean plugin is not installed")

    def test_release_constants_match_without_a_runtime_import(self):
        values = literal_assignments(os.path.join(self.library, "release.py"))
        expected = {
            "FORMAT": grounded_agent.BEREAN_FORMAT,
            "FIELDS": grounded_agent.BEREAN_RELEASE_FIELDS,
            "CORPUS_FIELDS": grounded_agent.BEREAN_CORPUS_FIELDS,
            "READS_FIELDS": grounded_agent.BEREAN_READS_FIELDS,
            "ANSWER_FIELDS": grounded_agent.BEREAN_ANSWER_FIELDS,
            "RULES_FIELDS": grounded_agent.BEREAN_RULES_FIELDS,
            "ALLOWLIST_FIELDS": grounded_agent.BEREAN_ALLOWLIST_FIELDS,
            "EVALS_FIELDS": grounded_agent.BEREAN_EVALS_FIELDS,
            "RETENTION": grounded_agent.BEREAN_RETENTION,
            "RELEASE_DOCUMENT": grounded_agent.BEREAN_RELEASE_DOCUMENT,
            "PROMOTIONS_FILE": grounded_agent.BEREAN_PROMOTIONS_FILE,
        }
        for name, copied in expected.items():
            with self.subTest(name=name):
                self.assertEqual(values[name], copied)

    def test_evidence_and_promotion_vocabularies_match(self):
        answers = literal_assignments(os.path.join(self.library, "answers.py"))
        reads = literal_assignments(os.path.join(self.library, "reads.py"))
        promotion = literal_assignments(os.path.join(self.library, "promote.py"))
        limit = getattr(grounded_agent, "BEREAN_MAX_PROMOTION_RECORDS", None)
        self.assertEqual(limit, 1000)
        self.assertEqual(answers["SOURCE_CLASSES"], grounded_agent.BEREAN_SOURCE_CLASSES)
        self.assertEqual(reads["EVIDENCE_CLASSES"], grounded_agent.BEREAN_EVIDENCE_CLASSES)
        self.assertEqual(promotion["FORMAT"], grounded_agent.BEREAN_PROMOTION_FORMAT)
        self.assertEqual(promotion["ACTIONS"], grounded_agent.BEREAN_PROMOTION_ACTIONS)
        self.assertEqual(
            promotion.get("MAX_RECORDS"), limit
        )


class CompletenessTests(unittest.TestCase):
    def test_every_registered_predicate_ships_a_schema_this_file_checks(self):
        """A predicate registered without a published schema, or with one nothing
        compares against the module, is the drift this file exists to prevent."""
        from ariadne_lib import predicates  # noqa: F401

        registered = {type_uri for type_uri, _ in registry.DEFAULT.entries()}
        covered = {module.TYPE for module, _ in SHIPPED}
        self.assertEqual(registered, covered)
        for module, path in SHIPPED:
            with self.subTest(predicate=module.TYPE):
                self.assertTrue(os.path.isfile(path), path)
                self.assertIn(module.TYPE, read_schema(path)["description"])


if __name__ == "__main__":
    unittest.main()
