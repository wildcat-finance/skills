"""Wildcat V2 wrapper instances as capture subjects (skills#2092).

`LegacyIdentityTests` freezes what a plan without `wildcat_v2_wrappers`
builds. Every literal below was computed at Skills
`50d71a2e8c1777f8eb26db32dd8adeadb34063bd`, before any wrapper code existed,
by building the constructed V2 and V1 releases through the fake transport in
`test_wildcat_venue.py`. A later change that moves a legacy release's bytes
fails here.

The design record's conformance resolver loads these three cases by name for
`legacy-identities-hold`, so their identifiers must not change.

Step 2's classes prove the `wildcat_v2_wrappers` plan field, the pure
derivation in `alexandria_lib/wildcat_wrappers.py`, the bounded wrapper gaps
in `venues/wildcat_v2.py`, and that a plan without the field reaches none of
that code. Every `WrapperDeployed` log here is constructed; none was observed
on a chain.
"""

import ast
from copy import deepcopy
import hashlib
import json
import unittest
from unittest import mock

from tests import test_wildcat_venue as venue
from alexandria_lib import interval, release, wildcat_registry, wildcat_wrappers
from alexandria_lib.canonical import canonical_bytes
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.interval import OPENING_CLASS
from alexandria_lib.venues import wildcat_v1, wildcat_v2
import usdc_interval
from usdc_interval import Builder, Collector, Reconciler


V2_RELEASE_ID = "sha256:f2b94e967c761a871129f5889fd372e992d62de87104fb5d5a4480338f9915a1"
V1_RELEASE_ID = "sha256:cbbacc59170bdf549c56347f8a962a869a6632868606a1ce3a0e1b37c0ae3def"
# The three registry digests are written only in `wildcat_registry.py`, which
# `RegistryGeneratorTests` enforces, so the freeze pins the SHA-256 of the
# V2, pre-#1880 and V1 constants joined by newlines rather than restating them.
REGISTRY_CONSTANTS_SHA256 = "5ac269412766da57a767a0874cf1d27a5c1987c3f398ffa29c67c341712c884f"
V2_REGISTRY_BYTES = 64891
V1_REGISTRY_BYTES = 7712


class LegacyIdentityTests(venue.WildcatCase):
    """The constructed legacy releases and the registry pins, as they stood at the base."""

    def setUp(self):
        """Each case names its venue before the shared fixture loads."""

    def released_on(self, name):
        self.VENUE = name
        super().setUp()
        output, release_id = self.released()
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["release_id"], release_id)
        self.assertNotIn("wildcat_v2_wrappers", self.plan)
        return release_id

    def test_constructed_v2_release_identifier_is_frozen(self):
        self.assertEqual(self.released_on(wildcat_v2.VENUE), V2_RELEASE_ID)

    def test_constructed_v1_release_identifier_is_frozen(self):
        self.assertEqual(self.released_on(wildcat_v1.VENUE), V1_RELEASE_ID)

    def test_registry_digest_constants_are_unchanged(self):
        constants = (
            wildcat_registry.WILDCAT_V2_REGISTRY_SHA256,
            wildcat_registry.PRE_1880_WILDCAT_V2_REGISTRY_SHA256,
            wildcat_registry.WILDCAT_V1_REGISTRY_SHA256,
        )
        joined = "\n".join(constants).encode("ascii")
        self.assertEqual(hashlib.sha256(joined).hexdigest(), REGISTRY_CONSTANTS_SHA256)
        v2 = wildcat_registry.registry_bytes(venue.REPO_ROOT)
        v1 = wildcat_registry.registry_v1_bytes(venue.REPO_ROOT)
        self.assertEqual(len(v2), V2_REGISTRY_BYTES)
        self.assertEqual(hashlib.sha256(v2).hexdigest(), constants[0])
        self.assertEqual(len(v1), V1_REGISTRY_BYTES)
        self.assertEqual(hashlib.sha256(v1).hexdigest(), constants[2])


FIELD = interval.WRAPPERS_FIELD
RULE = interval.WRAPPERS_RULE
TOPIC = wildcat_wrappers.WRAPPER_DEPLOYED_TOPIC
FACTORY = "0xea6de11f8f3f83c79bd9d8db5517fcfdf2bb148a"
WRAPPER_A = "0x" + "aa" * 20
WRAPPER_B = "0x" + "bb" * 20
OTHER_MARKET = "0x02e0415e828a5f97309f93f001885b5db8a87d71"
HOOKS_INSTANCE = "0x0004da6611b3c4f557ba88105ebd85e5bd214dcd"
STRANGER = "0x" + "12" * 20
BLOCK_A = 25895390
BLOCK_B = 25895400
PLAN_SCHEMA = venue.PLUGIN / "schemas" / "interval-plan-v2.schema.json"
COMPONENT_SCHEMA = venue.PLUGIN / "schemas" / "wildcat-v2-wrapper-subjects-v1.schema.json"
ABI_TABLE = venue.REPO_ROOT / "plugins" / "tabularium" / "scripts" / "tabularium_lib" / "wildcat_abi.py"


def word(address):
    """An address as the zero-padded 32-byte topic a log carries."""
    return "0x" + "0" * 24 + address[2:]


def wrapper_log(market, wrapper, block, *, transaction_index=2, log_index=5, emitter=FACTORY):
    """One constructed `WrapperDeployed` log, shaped as a provider returns it."""
    seed = hashlib.sha256(f"{wrapper}:{block}:{log_index}".encode()).hexdigest()
    return {
        "address": emitter,
        "blockHash": "0x" + hashlib.sha256(str(block).encode()).hexdigest(),
        "blockNumber": hex(block),
        "data": "0x",
        "logIndex": hex(log_index),
        "removed": False,
        "topics": [TOPIC, word(market), word(wrapper)],
        "transactionHash": "0x" + seed,
        "transactionIndex": hex(transaction_index),
    }


def fixture_logs():
    """Every constructed log the V2 fixture holds, in shard order."""
    return [record for shard in venue.fixture()["logs"].values() for record in shard]


def wrapper_plan(*wrappers):
    plan = deepcopy(venue.fixture()["plan"])
    plan[FIELD] = {"rule": RULE, "subjects": sorted(wrappers) or [WRAPPER_A]}
    return plan


def two_wrapper_logs():
    return [
        wrapper_log(venue.NEW_MARKET, WRAPPER_B, BLOCK_B, transaction_index=4, log_index=9),
        wrapper_log(OTHER_MARKET, WRAPPER_A, BLOCK_A),
    ]


def numbered(index):
    """The `index`th constructed wrapper address, ascending with `index`."""
    return "0x" + "f0" + format(index, "038x")


class WrapperPlanFieldTests(unittest.TestCase):
    """The plan field's one closed shape, in the schema and in `validate_plan`."""

    def setUp(self):
        self.schema = json.loads(PLAN_SCHEMA.read_text(encoding="utf-8"))
        self.registry = venue.registry()

    def test_schema_and_runtime_admit_the_one_closed_shape(self):
        legacy = venue.fixture()["plan"]
        self.assertEqual(venue.schema_errors(self.schema, legacy), [])
        interval.validate_plan(legacy)
        plan = wrapper_plan(WRAPPER_A, WRAPPER_B)
        self.assertEqual(venue.schema_errors(self.schema, plan), [])
        interval.validate_plan(plan)
        self.assertEqual(
            wildcat_wrappers.validate_wrapper_plan(plan, self.registry), [WRAPPER_A, WRAPPER_B]
        )
        self.assertNotIn(FIELD, self.schema["required"])

    def test_every_other_shape_refuses_in_schema_and_runtime(self):
        plan = wrapper_plan(WRAPPER_A)
        cases = {
            "null": None,
            "string": RULE,
            "another rule": {"rule": "wrapper-deployed/v2", "subjects": [WRAPPER_A]},
            "extra key": {"rule": RULE, "subjects": [WRAPPER_A], "factory": FACTORY},
            "no subjects": {"rule": RULE},
            "empty list": {"rule": RULE, "subjects": []},
            "uppercase": {"rule": RULE, "subjects": [WRAPPER_A.upper().replace("0X", "0x")]},
            "short": {"rule": RULE, "subjects": [WRAPPER_A[:-2]]},
            "not a string": {"rule": RULE, "subjects": [7]},
        }
        for name, value in cases.items():
            bad = dict(plan, **{FIELD: value})
            with self.subTest(case=name):
                self.assertTrue(venue.schema_errors(self.schema, bad))
                with self.assertRaisesRegex(AlexandriaError, FIELD):
                    interval.validate_plan(bad)
        for key, value, message in (
            ("venue", "wildcat-v1", "only for venue wildcat-v2"),
            ("evidence_classes", ["boundary-blocks", "traces"], "requires the logs evidence class"),
        ):
            bad = dict(plan, **{key: value})
            with self.subTest(key=key):
                self.assertTrue(venue.schema_errors(self.schema, bad))
                with self.assertRaisesRegex(AlexandriaError, message):
                    interval.validate_plan(bad)

    def test_order_duplicates_and_overlap_refuse_by_name_at_runtime(self):
        plan = wrapper_plan(WRAPPER_A)
        for subjects, message in (
            ([WRAPPER_B, WRAPPER_A], f"{WRAPPER_A} is duplicated or out of ascending order"),
            ([WRAPPER_A, WRAPPER_A], f"{WRAPPER_A} is duplicated or out of ascending order"),
            ([FACTORY], f"{FACTORY} is also a declared subject"),
        ):
            bad = dict(plan, **{FIELD: {"rule": RULE, "subjects": subjects}})
            with self.subTest(subjects=subjects):
                with self.assertRaisesRegex(AlexandriaError, message):
                    interval.validate_plan(bad)

    def test_a_single_proxy_plan_carrying_the_field_refuses_by_name(self):
        plan = wrapper_plan(WRAPPER_A)
        plan["proxy"] = plan.pop("subjects")[0]
        plan["format"] = interval.PLAN_FORMAT
        with self.assertRaisesRegex(AlexandriaError, "admitted only on an alexandria-interval-plan/v2"):
            interval.validate_plan(plan)

    def test_wrappers_count_against_the_subject_limit(self):
        plan = venue.fixture()["plan"]
        room = interval.MAX_SUBJECTS - len(plan["subjects"])
        fits = wrapper_plan(*(numbered(index) for index in range(room)))
        interval.validate_plan(fits)
        over = wrapper_plan(*(numbered(index) for index in range(room + 1)))
        with self.assertRaisesRegex(AlexandriaError, "together exceed the 4096-subject limit"):
            interval.validate_plan(over)

    def test_the_registry_checks_refuse_by_name(self):
        plan = wrapper_plan(WRAPPER_A)
        plan["subjects"].remove(FACTORY)
        with self.assertRaisesRegex(AlexandriaError, f"requires the wrapper factory {FACTORY}"):
            wildcat_wrappers.validate_wrapper_plan(plan, self.registry)
        plan = wrapper_plan(HOOKS_INSTANCE)
        plan["subjects"].remove(HOOKS_INSTANCE)
        with self.assertRaisesRegex(
            AlexandriaError, f"declared wrapper {HOOKS_INSTANCE} is the registry's hooks-instance entry"
        ):
            wildcat_wrappers.validate_wrapper_plan(plan, self.registry)
        edited = venue.registry()
        edited["entries"][0]["deployment_block"] = 1
        with self.assertRaisesRegex(AlexandriaError, "do not match the pinned registry"):
            wildcat_wrappers.validate_wrapper_plan(wrapper_plan(WRAPPER_A), edited)
        with self.assertRaisesRegex(AlexandriaError, f"declares no {FIELD}"):
            wildcat_wrappers.validate_wrapper_plan(venue.fixture()["plan"], self.registry)

    def test_the_field_names_the_venue_and_the_registry_names_one_factory(self):
        self.assertEqual(interval.WRAPPERS_VENUE, wildcat_v2.VENUE)
        self.assertEqual(wildcat_wrappers.factory(self.registry), FACTORY)
        dependent = self.schema["dependentSchemas"][FIELD]["properties"]
        self.assertEqual(dependent["venue"], {"const": wildcat_v2.VENUE})
        self.assertEqual(self.schema["properties"][FIELD]["properties"]["rule"], {"const": RULE})


class WrapperPlanRefusalTests(venue.WildcatCase):
    """A plan carrying the field refuses at the venue before any request."""

    def test_a_wrapper_plan_refuses_before_any_request(self):
        for plan, message in (
            (wrapper_plan(WRAPPER_A), "checked but not collected"),
            (dict(wrapper_plan(WRAPPER_A), **{FIELD: {"rule": RULE, "subjects": []}}),
             "must be a non-empty list"),
        ):
            with self.subTest(message=message):
                transport = venue.WildcatTransport(self.state)
                with self.assertRaisesRegex(AlexandriaError, message):
                    Collector(plan, self.scratch(f"collect-{len(message)}"), transport,
                              registry=self.registry)
                with self.assertRaisesRegex(AlexandriaError, message):
                    Reconciler(plan, self.scratch(f"reconcile-{len(message)}"), transport,
                               venue.SECOND_PROVIDER, registry=self.registry)
                with self.assertRaisesRegex(AlexandriaError, message):
                    Builder(plan, self.scratch(f"build-{len(message)}"), self.registry,
                            created_at=venue.CREATED_AT)
                self.assertEqual(transport.calls, [])
        plan = wrapper_plan(WRAPPER_A)
        plan["subjects"].remove(FACTORY)
        transport = venue.WildcatTransport(self.state)
        with self.assertRaisesRegex(AlexandriaError, f"requires the wrapper factory {FACTORY}"):
            Collector(plan, self.scratch("no-factory"), transport, registry=self.registry)
        self.assertEqual(transport.calls, [])

    def test_check_replays_no_opening_for_a_wrapper_plan(self):
        output, _release_id = self.released()
        documents = {
            name: venue.existing.component_document(output, name)
            for name in ("logs", "registry", OPENING_CLASS)
        }
        plan = wrapper_plan(WRAPPER_A)
        parts = usdc_interval.journal_components(plan, tuple(plan["evidence_classes"]))
        with self.assertRaisesRegex(AlexandriaError, "checked but not collected"):
            usdc_interval._replay_release_opening(plan, documents, plan["evidence_classes"], parts)


class WrapperDiscoveryTests(unittest.TestCase):
    """Only the factory's `WrapperDeployed` logs are read, each checked field by field."""

    def setUp(self):
        self.registry = venue.registry()
        self.plan = wrapper_plan(WRAPPER_A, WRAPPER_B)

    def discover(self, extra, plan=None):
        return wildcat_wrappers.discover(plan or self.plan, self.registry, fixture_logs() + extra)

    def test_discovery_reads_only_the_factorys_wrapper_deployed_logs(self):
        self.assertEqual(self.discover([]), [])
        ignored = [
            wrapper_log(OTHER_MARKET, STRANGER, BLOCK_A, emitter=venue.NEW_MARKET),
            dict(wrapper_log(OTHER_MARKET, STRANGER, BLOCK_A, log_index=6),
                 topics=["0x" + "ab" * 32, word(OTHER_MARKET), word(STRANGER)]),
        ]
        rows = self.discover(two_wrapper_logs() + ignored)
        self.assertEqual([row["wrapper"] for row in rows], [WRAPPER_A, WRAPPER_B])
        self.assertEqual([row["market"] for row in rows], [OTHER_MARKET, venue.NEW_MARKET])
        self.assertEqual(rows[1]["deployment"], {
            "block_number": str(BLOCK_B), "log_index": 9,
            "transaction_hash": two_wrapper_logs()[0]["transactionHash"], "transaction_index": 4,
        })

    def test_a_market_the_registry_does_not_list_refuses_naming_wrapper_market_and_block(self):
        with self.assertRaisesRegex(
            AlexandriaError,
            f"block {BLOCK_A} names market {STRANGER}, which is not one of the 80 markets the "
            f"registry declares, for wrapper {WRAPPER_A}",
        ):
            self.discover([wrapper_log(STRANGER, WRAPPER_A, BLOCK_A)])

    def test_a_wrapper_equal_to_a_registry_entry_refuses_naming_it_and_its_block(self):
        with self.assertRaisesRegex(
            AlexandriaError,
            f"block {BLOCK_A} names wrapper {HOOKS_INSTANCE}, which the registry lists as its "
            "hooks-instance entry",
        ):
            self.discover([wrapper_log(OTHER_MARKET, HOOKS_INSTANCE, BLOCK_A)])

    def test_a_wrapper_named_by_two_logs_refuses_naming_both_blocks(self):
        with self.assertRaisesRegex(
            AlexandriaError,
            f"wrapper {WRAPPER_A} is named by two preserved WrapperDeployed logs, at block "
            f"{BLOCK_A} and block {BLOCK_B}",
        ):
            self.discover([
                wrapper_log(OTHER_MARKET, WRAPPER_A, BLOCK_A),
                wrapper_log(venue.NEW_MARKET, WRAPPER_A, BLOCK_B),
            ])

    def test_a_declared_wrapper_no_log_names_refuses_by_name(self):
        logs = fixture_logs() + [wrapper_log(OTHER_MARKET, WRAPPER_A, BLOCK_A)]
        with self.assertRaisesRegex(
            AlexandriaError,
            f"declared wrapper {WRAPPER_B} is named by no preserved WrapperDeployed log from the "
            f"wrapper factory {FACTORY} inside the interval, blocks 25895340 to 25895419",
        ):
            wildcat_wrappers.wrapper_subjects(self.plan, self.registry, logs)

    def test_malformed_wrapper_deployed_records_refuse_by_name(self):
        good = wrapper_log(OTHER_MARKET, WRAPPER_A, BLOCK_A)
        cases = {
            "two topics": (dict(good, topics=good["topics"][:2]), "carries 2 topics, not the three"),
            "four topics": (dict(good, topics=good["topics"] + [word(STRANGER)]),
                            "carries 4 topics, not the three"),
            "unpadded market": (dict(good, topics=[TOPIC, "0x" + "11" * 32, word(WRAPPER_A)]),
                                "zero-padded market address in topic 2"),
            "unpadded wrapper": (dict(good, topics=[TOPIC, word(OTHER_MARKET), "0x" + "11" * 32]),
                                 "zero-padded wrapper address in topic 3"),
            "uppercase topic": (dict(good, topics=[TOPIC.upper().replace("0X", "0x")] + good["topics"][1:]),
                                "topic that is not a lowercase 32-byte word"),
            "padded block": (dict(good, blockNumber="0x0" + hex(BLOCK_A)[2:]),
                             "carries no canonical blockNumber"),
            "block after the interval": (dict(good, blockNumber=hex(25895420)),
                                         "block 25895420 is outside the interval"),
            "transaction hash": (dict(good, transactionHash="0x12"),
                                 f"block {BLOCK_A} for wrapper {WRAPPER_A} carries no lowercase"),
            "log index": (dict(good, logIndex=5), f"for wrapper {WRAPPER_A} carries no canonical logIndex"),
            "transaction index": (dict(good, transactionIndex="0x"),
                                  "carries no canonical transactionIndex"),
        }
        for name, (record, message) in cases.items():
            with self.subTest(case=name):
                with self.assertRaisesRegex(AlexandriaError, message):
                    self.discover([record])
        with self.assertRaisesRegex(AlexandriaError, "is not an object"):
            self.discover(["not a log"])
        with self.assertRaisesRegex(AlexandriaError, "are not a list"):
            wildcat_wrappers.discover(self.plan, self.registry, {"0": []})

    def test_a_factory_log_with_unreadable_topics_refuses_rather_than_passing_over(self):
        plan = wrapper_plan(WRAPPER_A)
        good = wrapper_log(venue.NEW_MARKET, WRAPPER_B, BLOCK_B, log_index=9)
        for name, topics in (
            ("string", " ".join(good["topics"])),
            ("null", None),
            ("integer first word", [7] + good["topics"][1:]),
        ):
            with self.subTest(case=name):
                with self.assertRaisesRegex(
                    AlexandriaError,
                    f"log from the wrapper factory {FACTORY} at block {BLOCK_B} carries topics "
                    "that are not a list of words",
                ):
                    self.discover(
                        [wrapper_log(OTHER_MARKET, WRAPPER_A, BLOCK_A), dict(good, topics=topics)],
                        plan,
                    )

    def test_a_factory_log_with_a_malformed_first_topic_refuses_rather_than_passing_over(self):
        plan = wrapper_plan(WRAPPER_A)
        good = wrapper_log(venue.NEW_MARKET, WRAPPER_B, BLOCK_B, log_index=9)
        for name, first in (
            ("truncated", TOPIC[:-2]),
            ("no prefix", TOPIC[2:]),
            ("trailing space", TOPIC + " "),
            ("empty", ""),
        ):
            with self.subTest(case=name):
                with self.assertRaisesRegex(
                    AlexandriaError,
                    f"log from the wrapper factory {FACTORY} at block {BLOCK_B} carries topics "
                    "that are not a list of words",
                ):
                    self.discover(
                        [wrapper_log(OTHER_MARKET, WRAPPER_A, BLOCK_A),
                         dict(good, topics=[first] + good["topics"][1:])],
                        plan,
                    )

    def test_a_log_with_no_readable_emitter_refuses_rather_than_passing_over(self):
        plan = wrapper_plan(WRAPPER_A)
        declared = wrapper_log(OTHER_MARKET, WRAPPER_A, BLOCK_A)
        good = wrapper_log(venue.NEW_MARKET, WRAPPER_B, BLOCK_B, log_index=9)
        missing = dict(good)
        del missing["address"]
        for name, record in (
            ("missing", missing),
            ("null", dict(good, address=None)),
            ("integer", dict(good, address=7)),
            ("padded word", dict(good, address=word(FACTORY))),
            ("no prefix", dict(good, address=FACTORY[2:])),
        ):
            with self.subTest(case=name):
                with self.assertRaisesRegex(
                    AlexandriaError,
                    f"a preserved log at block {BLOCK_B} carries no 20-byte emitting address",
                ):
                    self.discover([declared, record], plan)
        rows = self.discover([declared, dict(good, address=FACTORY.upper().replace("0X", "0x"))], plan)
        self.assertEqual([row["wrapper"] for row in rows], [WRAPPER_A, WRAPPER_B])

    def test_more_wrappers_than_the_cap_refuse_by_name(self):
        logs = [wrapper_log(OTHER_MARKET, numbered(index), BLOCK_A, log_index=index)
                for index in range(3)]
        with mock.patch.object(wildcat_wrappers, "MAX_WRAPPERS", 2):
            with self.assertRaisesRegex(AlexandriaError, f"factory {FACTORY} deployed more than 2"):
                self.discover(logs)

    def test_the_topic_and_field_order_are_the_ones_tabulariums_abi_table_records(self):
        line = next(
            line for line in ABI_TABLE.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(repr(TOPIC))
        )
        entry = ast.literal_eval("{" + line.strip().rstrip(",") + "}")[TOPIC]
        self.assertEqual(entry["signature"], "WrapperDeployed(address,address)")
        self.assertEqual(
            [(item["name"], item["indexed"]) for item in entry["abi"]["inputs"]],
            [("market", True), ("wrapper", True)],
        )


class WrapperComponentTests(unittest.TestCase):
    """The `wrapper-subjects` document: its content, its canonical bytes and its schema."""

    def setUp(self):
        self.registry = venue.registry()
        self.plan = wrapper_plan(WRAPPER_B)
        self.logs = fixture_logs() + two_wrapper_logs()
        self.schema = json.loads(COMPONENT_SCHEMA.read_text(encoding="utf-8"))

    def component(self):
        return wildcat_wrappers.wrapper_subjects(self.plan, self.registry, self.logs)

    def test_the_component_lists_factory_topic_window_and_each_wrapper(self):
        first, second = two_wrapper_logs()
        self.assertEqual(self.component(), {
            "factory": FACTORY,
            "format": "alexandria-wildcat-v2-wrapper-subjects/v1",
            "topic": TOPIC,
            "window": {"end": "25895419", "start": "25895340"},
            "wrappers": [
                {"declared": False, "market": OTHER_MARKET, "wrapper": WRAPPER_A, "deployment": {
                    "block_number": str(BLOCK_A), "log_index": 5,
                    "transaction_hash": second["transactionHash"], "transaction_index": 2,
                }},
                {"declared": True, "market": venue.NEW_MARKET, "wrapper": WRAPPER_B, "deployment": {
                    "block_number": str(BLOCK_B), "log_index": 9,
                    "transaction_hash": first["transactionHash"], "transaction_index": 4,
                }},
            ],
        })

    def test_the_component_bytes_are_canonical_and_independent_of_log_order(self):
        data = wildcat_wrappers.component_bytes(self.component())
        self.assertEqual(data, canonical_bytes(json.loads(data)))
        self.assertTrue(data.endswith(b"}\n"))
        self.assertNotIn(b" ", data)
        reordered = wildcat_wrappers.wrapper_subjects(
            self.plan, self.registry, list(reversed(self.logs))
        )
        self.assertEqual(wildcat_wrappers.component_bytes(reordered), data)

    def test_schema_and_validator_agree_on_the_component(self):
        document = self.component()
        self.assertEqual(venue.schema_errors(self.schema, document), [])

        def edited(change):
            copy = deepcopy(document)
            change(copy)
            return copy

        both = {
            "extra key": lambda d: d.update(rule=RULE),
            "format": lambda d: d.update(format="alexandria-wildcat-v2-wrapper-subjects/v2"),
            "topic": lambda d: d.update(topic="0x" + "00" * 32),
            "factory": lambda d: d.update(factory=FACTORY.upper()),
            "window": lambda d: d["window"].update(start="01"),
            "no wrappers": lambda d: d.update(wrappers=[]),
            "row key": lambda d: d["wrappers"][0].update(subject=WRAPPER_A),
            "declared": lambda d: d["wrappers"][0].update(declared="yes"),
            "market": lambda d: d["wrappers"][0].update(market="0x12"),
            "deployment key": lambda d: d["wrappers"][0]["deployment"].pop("log_index"),
            "transaction hash": lambda d: d["wrappers"][0]["deployment"].update(transaction_hash="0x"),
            "negative index": lambda d: d["wrappers"][0]["deployment"].update(log_index=-1),
            "boolean index": lambda d: d["wrappers"][0]["deployment"].update(transaction_index=True),
        }
        for name, change in both.items():
            bad = edited(change)
            with self.subTest(case=name):
                self.assertTrue(venue.schema_errors(self.schema, bad))
                with self.assertRaises(AlexandriaError):
                    wildcat_wrappers.validate_component(bad)
        runtime_only = {
            "unsorted": lambda d: d["wrappers"].reverse(),
            "block outside window": lambda d: d["wrappers"][0]["deployment"].update(
                block_number="25895420"),
            "reversed window": lambda d: d.update(window={"end": "25895340", "start": "25895419"}),
        }
        for name, change in runtime_only.items():
            with self.subTest(case=name):
                with self.assertRaises(AlexandriaError):
                    wildcat_wrappers.component_bytes(edited(change))

    def test_the_schema_catalogue_indexes_the_component_and_the_field(self):
        catalogue = (venue.PLUGIN / "schemas" / "README.md").read_text(encoding="utf-8")
        self.assertIn("`wildcat-v2-wrapper-subjects-v1.schema.json`", catalogue)
        self.assertIn("`alexandria-wildcat-v2-wrapper-subjects/v1`", catalogue)
        self.assertIn(f"`{FIELD}`", catalogue)
        self.assertEqual(self.schema["properties"]["format"]["const"], wildcat_wrappers.FORMAT)
        self.assertEqual(self.schema["properties"]["topic"]["const"], TOPIC)


class WrapperGapTests(unittest.TestCase):
    """Wrapper gap sentences: bounded, named and within the capture's gap limit."""

    def setUp(self):
        self.registry = venue.registry()

    def gaps(self, undeclared, declared=(WRAPPER_A,)):
        plan = wrapper_plan(*declared)
        logs = fixture_logs() + [
            wrapper_log(OTHER_MARKET, address, BLOCK_A, log_index=index)
            for index, address in enumerate(list(declared) + [numbered(i) for i in range(undeclared)])
        ]
        component = wildcat_wrappers.wrapper_subjects(plan, self.registry, logs)
        return plan, wildcat_v2.wrapper_gaps(plan, self.registry, component)

    def test_undeclared_wrappers_are_named_up_to_sixteen_then_counted(self):
        _plan, gaps = self.gaps(16)
        named = [gap for gap in gaps if "is not declared by the plan" in gap]
        self.assertEqual(len(named), 16)
        self.assertIn(
            f"wrapper {numbered(0)} for market {OTHER_MARKET}, named by a preserved "
            f"WrapperDeployed log at block {BLOCK_A}, is not declared by the plan, so its native "
            "logs were not requested", gaps,
        )
        _plan, gaps = self.gaps(20)
        named = [gap for gap in gaps if "is not declared by the plan" in gap]
        self.assertEqual(len(named), wildcat_v2.LISTED_GAPS)
        self.assertEqual(
            [gap for gap in gaps if gap.startswith("4 further wrappers, 20 in all")],
            ["4 further wrappers, 20 in all, are named by preserved WrapperDeployed logs but not "
             "declared by the plan, so their native logs were not requested; the "
             "wrapper-subjects component names each"],
        )
        self.assertEqual(len(gaps), 16 + 1 + 3)

    def test_a_fully_declared_set_owes_the_factory_start_and_two_unknowns(self):
        _plan, gaps = self.gaps(0, declared=(WRAPPER_A, WRAPPER_B))
        self.assertEqual(gaps, [
            f"the wrapper factory {FACTORY} was deployed at block 24750455, before the interval "
            "start, block 25895340; its WrapperDeployed logs before the start were not requested, "
            "so a wrapper it deployed earlier is not listed",
            wildcat_v2.WRAPPER_IMMUTABILITY_GAP,
            wildcat_v2.WRAPPER_PROVENANCE_GAP.format(factory=FACTORY),
        ])
        self.assertIn("immutability is not established", gaps[1])
        self.assertIn("single-factory provenance is not established", gaps[2])

    def test_a_wrapper_capture_stays_within_the_gap_limit(self):
        plan, gaps = self.gaps(300)
        self.assertEqual(len(gaps), 16 + 1 + 3)
        owed = wildcat_v2.evidence_gaps(plan, self.registry, fixture_logs())
        self.assertLessEqual(len(owed) + len(gaps), release.MAX_GAPS)
        self.assertTrue(all(0 < len(gap) <= 1000 for gap in gaps))

    def test_a_plan_declared_wrapper_the_component_does_not_mark_refuses(self):
        logs = fixture_logs() + two_wrapper_logs()
        plan = wrapper_plan(WRAPPER_A, WRAPPER_B)
        full = wildcat_wrappers.wrapper_subjects(plan, self.registry, logs)
        for name, component in (
            ("marked undeclared", wildcat_wrappers.wrapper_subjects(
                wrapper_plan(WRAPPER_A), self.registry, logs)),
            ("row dropped", dict(full, wrappers=[
                row for row in full["wrappers"] if row["wrapper"] != WRAPPER_B])),
        ):
            with self.subTest(case=name):
                with self.assertRaisesRegex(
                    AlexandriaError, f"does not list plan-declared wrapper {WRAPPER_B} as declared"
                ):
                    wildcat_v2.wrapper_gaps(plan, self.registry, component)

    def test_a_component_marking_an_undeclared_wrapper_declared_refuses(self):
        logs = fixture_logs() + two_wrapper_logs()
        component = wildcat_wrappers.wrapper_subjects(
            wrapper_plan(WRAPPER_A, WRAPPER_B), self.registry, logs
        )
        with self.assertRaisesRegex(
            AlexandriaError, f"lists wrapper {WRAPPER_A} as declared, which the plan does not declare"
        ):
            wildcat_v2.wrapper_gaps(wrapper_plan(WRAPPER_B), self.registry, component)

    def test_a_component_for_another_factory_or_window_refuses(self):
        plan = wrapper_plan(WRAPPER_A)
        logs = fixture_logs() + [wrapper_log(OTHER_MARKET, WRAPPER_A, BLOCK_A)]
        component = wildcat_wrappers.wrapper_subjects(plan, self.registry, logs)
        for key, value in (("factory", STRANGER), ("window", {"end": "25895419", "start": "25895341"})):
            with self.subTest(key=key):
                with self.assertRaisesRegex(AlexandriaError, "does not name this plan's wrapper factory"):
                    wildcat_v2.wrapper_gaps(plan, self.registry, dict(component, **{key: value}))


class LegacyPlanIsolationTests(venue.WildcatCase):
    """A plan without the field builds and checks without calling any wrapper code."""

    def test_a_legacy_plan_reaches_no_wrapper_code(self):
        tripped = mock.Mock(side_effect=AssertionError("a legacy plan reached wrapper code"))
        targets = [
            (interval, "_validate_wrappers"),
            (wildcat_v2, "wrapper_gaps"),
        ] + [(wildcat_wrappers, name) for name in (
            "factory", "validate_wrapper_plan", "discover", "wrapper_subjects",
            "validate_component", "component_bytes",
        )]
        for module, name in targets:
            patcher = mock.patch.object(module, name, tripped)
            patcher.start()
            self.addCleanup(patcher.stop)
        output, release_id = self.released()
        self.assertEqual(release_id, V2_RELEASE_ID)
        self.assertEqual(usdc_interval.check_interval(output)["epochs"], 137)
        tripped.assert_not_called()
