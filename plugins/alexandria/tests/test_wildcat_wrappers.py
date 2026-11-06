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

Step 3's classes run a constructed wrapper chain through collect, reconcile,
build and check. `WrapperReleaseTests` and `WrapperRefusalTests` are loaded by
name by the design record's resolver for `wrapper-release-builds-and-checks`
and `wrapper-refusals-fire`, so the identifiers it names must not change. A
build over a staging tree that carries a refusal's case refuses through the
CLI and writes nothing, and `check` refuses a built release edited to carry
it. Collection also refuses each case its opening phase reaches, which is
every case but a wrapper log before its epoch: collection admits that one and
the build refuses it.

Step 4's `WrapperDemonstrationTests` run `wrapper_demo.py`, the constructed
specimen helper, which drives collect, reconcile, build and check through
`usdc_interval.main` over the fake transport, then each refusal case through
the same CLI. `PortableBudgetTests` measures what Steps 1 to 3 add to the
portable payload against the run base; the design record's resolver loads
its budget case by name for `portable-payload-within-budget`.
"""

import ast
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
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
    """A malformed declaration refuses before any request; a sound one is admitted."""

    def test_a_malformed_declaration_refuses_before_any_request(self):
        no_factory = wrapper_plan(WRAPPER_A)
        no_factory["subjects"].remove(FACTORY)
        registry_entry = wrapper_plan(HOOKS_INSTANCE)
        registry_entry["subjects"].remove(HOOKS_INSTANCE)
        for index, (plan, message) in enumerate((
            (dict(wrapper_plan(WRAPPER_A), **{FIELD: {"rule": RULE, "subjects": []}}),
             "must be a non-empty list"),
            (no_factory, f"requires the wrapper factory {FACTORY}"),
            (registry_entry, f"declared wrapper {HOOKS_INSTANCE} is the registry's hooks-instance"),
        )):
            with self.subTest(message=message):
                transport = venue.WildcatTransport(self.state)
                with self.assertRaisesRegex(AlexandriaError, message):
                    Collector(plan, self.scratch(f"collect-{index}"), transport,
                              registry=self.registry)
                with self.assertRaisesRegex(AlexandriaError, message):
                    Reconciler(plan, self.scratch(f"reconcile-{index}"), transport,
                               venue.SECOND_PROVIDER, registry=self.registry)
                with self.assertRaisesRegex(AlexandriaError, message):
                    Builder(plan, self.scratch(f"build-{index}"), self.registry,
                            created_at=venue.CREATED_AT)
                self.assertEqual(transport.calls, [])

    def test_a_sound_declaration_is_admitted_without_a_request(self):
        plan = wrapper_plan(WRAPPER_A, WRAPPER_B)
        transport = venue.WildcatTransport(self.state)
        Collector(plan, self.scratch("collect"), transport, registry=self.registry)
        Reconciler(plan, self.scratch("reconcile"), transport, venue.SECOND_PROVIDER,
                   registry=self.registry)
        Builder(plan, self.scratch("build"), self.registry, created_at=venue.CREATED_AT)
        self.assertEqual(transport.calls, [])

    def test_check_replay_refuses_a_declared_wrapper_no_log_names(self):
        output, _release_id = self.released()
        documents = {
            name: venue.existing.component_document(output, name)
            for name in ("logs", "registry", OPENING_CLASS)
        }
        plan = wrapper_plan(WRAPPER_A)
        parts = usdc_interval.journal_components(plan, tuple(plan["evidence_classes"]))
        with self.assertRaisesRegex(
            AlexandriaError, f"declared wrapper {WRAPPER_A} is named by no preserved WrapperDeployed"
        ):
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

    def logs(self, undeclared, declared=(WRAPPER_A,)):
        return fixture_logs() + [
            wrapper_log(OTHER_MARKET, address, BLOCK_A, log_index=index)
            for index, address in enumerate(list(declared) + [numbered(i) for i in range(undeclared)])
        ]

    def gaps(self, undeclared, declared=(WRAPPER_A,)):
        plan = wrapper_plan(*declared)
        logs = self.logs(undeclared, declared)
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
        # Every evidence scope of a wrapper plan owes the venue's gaps and the
        # wrapper gaps together, so the two share one capture's limit.
        owed = wildcat_v2.evidence_gaps(plan, self.registry, self.logs(300))
        self.assertEqual(owed[-len(gaps):], gaps)
        self.assertLessEqual(len(owed), release.MAX_GAPS)
        self.assertTrue(all(0 < len(gap) <= 1000 for gap in owed))

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


# Step 3: a constructed wrapper chain. Every log, code and frame below is
# derived from a fixed string and was not observed on a chain.
WRAPPER_C = "0x" + "cc" * 20
EARLY_BLOCK = 25895385
INTERVAL_END = "25895419"
NATIVE_TOPIC = "0x" + hashlib.sha256(b"constructed wrapper event").hexdigest()
OTHER_TOPIC = "0x" + hashlib.sha256(b"constructed other factory event").hexdigest()
WRAPPER_COMPONENT = "wrapper-subjects"
LEGACY_CHECK_KEYS = {
    "epochs", "implementations", "interval", "receipt_semantics", "reconciliation",
    "reconciliation_binding", "release_id", "shard_statuses",
}


def wrapper_code(wrapper):
    """A constructed wrapper's runtime code, 64 bytes."""
    return "0x" + hashlib.sha256(f"wrapper-code:{wrapper}".encode()).hexdigest() * 2


def code_digest(wrapper):
    return hashlib.sha256(bytes.fromhex(wrapper_code(wrapper)[2:])).hexdigest()


def transaction(block, index):
    return "0x" + hashlib.sha256(f"wrapper-fixture-tx:{block}:{index}".encode()).hexdigest()


def chain_log(state, emitter, block, tx_index, log_index, topics):
    """One log on the constructed chain, under the block hash the transport answers."""
    return {
        "address": emitter,
        "blockHash": venue.WildcatTransport(state)._hash(block),
        "blockNumber": hex(block),
        "data": "0x",
        "logIndex": hex(log_index),
        "removed": False,
        "topics": topics,
        "transactionHash": transaction(block, tx_index),
        "transactionIndex": hex(tx_index),
    }


def deployed(state, market, wrapper, block, tx_index, log_index):
    return chain_log(state, FACTORY, block, tx_index, log_index, [TOPIC, word(market), word(wrapper)])


def native(state, wrapper, block, tx_index, log_index):
    return chain_log(state, wrapper, block, tx_index, log_index, [NATIVE_TOPIC])


def wrapper_state(*, undeclared=(), extra=(), drop=()):
    """The V2 fixture with wrappers A and B declared, deployed and emitting.

    A is deployed at `BLOCK_A` for a registry market, and emits one log in its
    own deployment transaction before the factory's `WrapperDeployed`, then
    one in shard 2 and one in shard 3. B is deployed at `BLOCK_B` for the
    market the fixture deploys inside the interval and emits one log, whose
    transaction also calls an address outside the capture set. `undeclared`
    adds a `WrapperDeployed` for each address with no native log, as the
    provider's address filter would leave it; `drop` names the
    `(block, log_index)` pairs of those six logs to leave out, and `extra`
    adds logs after that.
    """
    state = deepcopy(venue.fixture())
    plan = state["plan"]
    plan[FIELD] = {"rule": RULE, "subjects": [WRAPPER_A, WRAPPER_B]}
    records = [
        record for record in (
            native(state, WRAPPER_A, BLOCK_A, 2, 4),
            deployed(state, OTHER_MARKET, WRAPPER_A, BLOCK_A, 2, 5),
            native(state, WRAPPER_A, 25895395, 0, 0),
            deployed(state, venue.NEW_MARKET, WRAPPER_B, BLOCK_B, 4, 9),
            native(state, WRAPPER_B, 25895405, 0, 1),
            native(state, WRAPPER_A, 25895410, 1, 2),
        )
        if (int(record["blockNumber"], 16), int(record["logIndex"], 16)) not in drop
    ]
    records += [
        deployed(state, OTHER_MARKET, wrapper, 25895415, 0, 3 + index)
        for index, wrapper in enumerate(undeclared)
    ]
    records += list(extra)
    for record in records:
        block = int(record["blockNumber"], 16)
        shard = next(s for s in plan["shards"] if s["start"] <= block <= s["end"])
        state["logs"][str(shard["index"])].append(record)
    for shard_logs in state["logs"].values():
        shard_logs.sort(key=lambda r: (int(r["blockNumber"], 16), int(r["logIndex"], 16)))
    for wrapper in (WRAPPER_A, WRAPPER_B):
        state["code"][wrapper] = wrapper_code(wrapper)
    frame = {
        "action": {"from": "0x" + "11" * 20, "input": "0x01", "to": WRAPPER_B},
        "blockNumber": 25895405, "traceAddress": [0],
        "transactionHash": transaction(25895405, 0),
    }
    outside = dict(frame, action=dict(frame["action"], to=STRANGER), traceAddress=[0, 0])
    state["traces"]["3"] += [frame, outside]
    return state


def cli(*arguments):
    """Run `usdc_interval.py` in this process: exit code, stdout and stderr."""
    out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    err = io.StringIO()
    with mock.patch.object(sys, "stdout", out), mock.patch.object(sys, "stderr", err):
        code = usdc_interval.main([str(argument) for argument in arguments])
        out.flush()
    return code, out.buffer.getvalue().decode("utf-8"), err.getvalue()


def release_logs(output):
    """Every log record the release's `logs` journal preserves, in shard order."""
    records = []
    for record in venue.existing.component_document(output, "logs")["records"]:
        records.extend(json.loads(record["response"])["result"])
    return records


def edit_journal(change):
    """An edit that applies `change(envelope, request)` to each record of one journal.

    `change` returns whether it changed the envelope; the edit re-encodes only
    those, and fails the case when none changed, so a refusal is never
    asserted over an edit that did not happen.
    """
    def edit(document):
        changed = 0
        for record in document["records"]:
            envelope = json.loads(record["response"])
            if change(envelope, json.loads(record["request"])):
                record["response"] = canonical_bytes(envelope).decode("utf-8")
                changed += 1
        if not changed:
            raise AssertionError("the journal edit changed no record")
    return edit


class WrapperCase(venue.WildcatCase):
    """Collect, reconcile, build and check over the constructed wrapper chain."""

    def setUp(self):
        super().setUp()
        self.state = wrapper_state()
        self.plan = self.state["plan"]

    def stage(self, name, state, *, transport=None, second=None):
        staging = self.scratch(f"{name}-staging")
        self.transport = transport or venue.WildcatTransport(state)
        Collector(state["plan"], staging, self.transport, registry=self.registry).collect()
        Reconciler(
            state["plan"], staging, second or venue.WildcatTransport(state),
            venue.SECOND_PROVIDER, registry=self.registry,
        ).reconcile()
        return staging

    def cli_build(self, name, plan, staging):
        """`usdc_interval.py build` over one staging tree; its result and output path."""
        plan_path = self.root / f"{name}-plan.json"
        registry_path = self.root / f"{name}-registry.json"
        plan_path.write_bytes(canonical_bytes(plan))
        registry_path.write_bytes(canonical_bytes(self.registry))
        output = self.root / f"{name}-release"
        result = cli(
            "build", "--plan", plan_path, "--staging", staging, "--registry", registry_path,
            "--created-at", venue.CREATED_AT, "--output", output,
        )
        return result, output

    def refused_build(self, name, plan, staging, message):
        """The CLI build refuses with `message` on stderr and writes no release."""
        (code, out, err), output = self.cli_build(name, plan, staging)
        self.assertEqual(code, 1, out)
        self.assertRegex(err, "usdc-interval: .*" + message)
        self.assertFalse(output.exists())

    def refused_check(self, output, edit_name, edit, message):
        """`check` refuses a built release once one component is edited to carry a case."""
        self.rewrite(output, edit_name, edit)
        with self.assertRaisesRegex(AlexandriaError, message):
            self.check_without_verify(output)


class WrapperReleaseTests(WrapperCase):
    """A plan declaring two wrappers builds, checks and lists each wrapper."""

    def test_wrapper_release_builds_and_checks(self):
        staging = self.stage("cli", self.state)
        (code, out, err), output = self.cli_build("cli", self.plan, staging)
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"\Asha256:[0-9a-f]{64}\n\Z")
        release_id = out.strip()
        self.assertNotEqual(release_id, V2_RELEASE_ID)
        code, out, err = cli("check", output)
        self.assertEqual(code, 0, err)
        summary = json.loads(out)
        self.assertEqual(summary["release_id"], release_id)
        self.assertEqual(set(summary), LEGACY_CHECK_KEYS | {"wrappers"})
        self.assertEqual(summary["epochs"], 137 + 2)
        self.assertEqual(summary["receipt_semantics"], "v3-subject-positional")
        self.assertEqual(summary["reconciliation"], "agreed")
        self.assertEqual(summary["shard_statuses"], {"complete": 4})
        self.assertEqual(
            set(summary["implementations"]), set(self.plan["subjects"]) | {WRAPPER_A, WRAPPER_B}
        )
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {component["name"] for component in manifest["components"]},
            set(usdc_interval.FIXED_COMPONENTS) | set(venue.EVIDENCE_COMPONENTS)
            | {WRAPPER_COMPONENT},
        )
        role = next(c["role"] for c in manifest["components"] if c["name"] == WRAPPER_COMPONENT)
        self.assertEqual(role, WRAPPER_COMPONENT)

    def test_check_lists_each_wrapper_with_epoch_and_journal(self):
        output, _release_id = self.released()
        listing = usdc_interval.check_interval(output)["wrappers"]
        self.assertEqual(listing, [
            {
                "attributed_logs": 3, "declared": True, "market": OTHER_MARKET,
                "deployment": {
                    "block_number": str(BLOCK_A), "log_index": 5,
                    "transaction_hash": transaction(BLOCK_A, 2), "transaction_index": 2,
                },
                "epoch": {
                    "end_block": INTERVAL_END, "implementation_code_sha256": code_digest(WRAPPER_A),
                    "start_block": str(BLOCK_A),
                },
                "wrapper": WRAPPER_A,
            },
            {
                "attributed_logs": 1, "declared": True, "market": venue.NEW_MARKET,
                "deployment": {
                    "block_number": str(BLOCK_B), "log_index": 9,
                    "transaction_hash": transaction(BLOCK_B, 4), "transaction_index": 4,
                },
                "epoch": {
                    "end_block": INTERVAL_END, "implementation_code_sha256": code_digest(WRAPPER_B),
                    "start_block": str(BLOCK_B),
                },
                "wrapper": WRAPPER_B,
            },
        ])
        # Each count is the wrapper's own logs in the released `logs` journal.
        emitted = [record["address"] for record in release_logs(output)]
        self.assertEqual([row["attributed_logs"] for row in listing],
                         [emitted.count(WRAPPER_A), emitted.count(WRAPPER_B)])

    def test_check_rederives_the_wrapper_subjects_component(self):
        output, _release_id = self.released()
        path = venue.existing.component_path(output, WRAPPER_COMPONENT)
        released = path.read_bytes()
        derived = wildcat_wrappers.wrapper_subjects(self.plan, self.registry, release_logs(output))
        self.assertEqual(released, wildcat_wrappers.component_bytes(derived))
        for name, edit in (
            ("transaction index", lambda d: d["wrappers"][0]["deployment"].update(transaction_index=3)),
            ("market", lambda d: d["wrappers"][1].update(market=OTHER_MARKET)),
            ("declared flag", lambda d: d["wrappers"][1].update(declared=False)),
            ("dropped row", lambda d: d["wrappers"].pop()),
        ):
            with self.subTest(edit=name):
                path.write_bytes(released)
                self.refused_check(
                    output, WRAPPER_COMPONENT, edit,
                    "the wrapper-subjects component is not the wrapper set the release's "
                    "preserved WrapperDeployed logs and registry derive",
                )
        path.write_bytes(released)
        manifest_path = output / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["components"] = [
            c for c in manifest["components"] if c["name"] != WRAPPER_COMPONENT
        ]
        manifest["captures"] = [c for c in manifest["captures"] if c["id"] != WRAPPER_COMPONENT]
        manifest_path.write_bytes(canonical_bytes(manifest, max_nodes=release.MAX_MANIFEST_NODES))
        with self.assertRaisesRegex(AlexandriaError, "lacks its wrapper-subjects component"):
            self.check_without_verify(output)

    def test_wrapper_epochs_name_the_wrapper_and_own_only_its_logs(self):
        output, _release_id = self.released()
        receipt = venue.existing.component_document(output, "epoch-table")
        table = venue.epoch_table(receipt)
        for wrapper, block in ((WRAPPER_A, BLOCK_A), (WRAPPER_B, BLOCK_B)):
            with self.subTest(wrapper=wrapper):
                [epoch] = table[wrapper]
                self.assertEqual((epoch["proxy"], epoch["implementation"]), (wrapper, wrapper))
                self.assertIsNone(epoch["upgrade"])
                self.assertEqual(epoch["start_position"], {
                    "block_number": str(block), "log_index": None, "transaction_index": None,
                })
                self.assertEqual(epoch["end_block"], INTERVAL_END)
        emitters = {
            (int(r["blockNumber"], 16), int(r["logIndex"], 16)): r["address"]
            for r in release_logs(output)
        }
        rows = receipt["log_attributions"]
        self.assertEqual(len(rows), len(emitters))
        for row in rows:
            self.assertEqual(row["subject"], emitters[(int(row["block_number"]), row["log_index"])])
        owners = {(int(r["block_number"]), r["log_index"]): r["subject"] for r in rows}
        # A's own log in its deployment transaction precedes the factory's
        # WrapperDeployed there, and the block-sentinel epoch still owns it.
        self.assertEqual(owners[(BLOCK_A, 4)], WRAPPER_A)
        self.assertEqual(owners[(BLOCK_A, 5)], FACTORY)
        self.assertEqual(owners[(BLOCK_B, 9)], FACTORY)

    def test_wrapper_reads_join_the_existing_journals(self):
        staging = self.stage("journals", self.state)
        self.assertEqual(
            set(venue.existing.journals(staging)),
            {"boundary-blocks", "logs", "traces", OPENING_CLASS},
        )
        requests = [json.loads(line)["request"] for line in
                    (staging / "journals" / "logs.jsonl").read_text().splitlines()]
        for request in requests:
            self.assertEqual(
                json.loads(request)["params"][0]["address"],
                self.plan["subjects"] + [WRAPPER_A, WRAPPER_B],
            )
        opening = [json.loads(entry["request"]) for entry in
                   venue.existing.opening_entries(staging)]
        for wrapper, block in ((WRAPPER_A, BLOCK_A), (WRAPPER_B, BLOCK_B)):
            with self.subTest(wrapper=wrapper):
                codes = [r["params"] for r in opening
                         if r["method"] == "eth_getCode" and r["params"][0] == wrapper]
                self.assertEqual(codes, [[wrapper, hex(block)]])
                headers = [r for r in opening if r["method"] == "eth_getBlockByNumber"
                           and r["params"][0] == hex(block)]
                self.assertEqual(len(headers), 1)
        traces = [json.loads(json.loads(line)["response"])["result"] for line in
                  (staging / "journals" / "traces.jsonl").read_text().splitlines()]
        recipients = [frame["action"]["to"] for result in traces for frame in result]
        self.assertIn(WRAPPER_B, recipients)
        self.assertNotIn(STRANGER, recipients)

    def test_an_undeclared_wrapper_is_listed_with_no_logs_requested(self):
        state = wrapper_state(undeclared=(WRAPPER_C,))
        output, _release_id = self.released("undeclared", state)
        listing = usdc_interval.check_interval(output)["wrappers"]
        self.assertEqual([row["wrapper"] for row in listing], [WRAPPER_A, WRAPPER_B, WRAPPER_C])
        self.assertEqual(
            {key: listing[2][key] for key in ("attributed_logs", "declared", "epoch")},
            {"attributed_logs": None, "declared": False, "epoch": None},
        )
        receipt = venue.existing.component_document(output, "epoch-table")
        self.assertNotIn(WRAPPER_C, venue.epoch_table(receipt))
        captures = self.captures(output)
        component = venue.existing.component_document(output, WRAPPER_COMPONENT)
        owed = wildcat_v2.wrapper_gaps(state["plan"], self.registry, component)
        self.assertEqual(captures[WRAPPER_COMPONENT]["coverage"]["gaps"], owed)
        sentence = (
            f"wrapper {WRAPPER_C} for market {OTHER_MARKET}, named by a preserved WrapperDeployed "
            "log at block 25895415, is not declared by the plan, so its native logs were not "
            "requested"
        )
        for name in (WRAPPER_COMPONENT, "logs", "traces", OPENING_CLASS):
            with self.subTest(capture=name):
                gaps = captures[name]["coverage"]["gaps"]
                self.assertIn(sentence, gaps)
                self.assertIn(wildcat_v2.WRAPPER_IMMUTABILITY_GAP, gaps)
                self.assertIn(wildcat_v2.WRAPPER_PROVENANCE_GAP.format(factory=FACTORY), gaps)
        dropped = [gap for gap in captures["logs"]["coverage"]["gaps"] if gap != sentence]
        manifest_path = output / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        next(c for c in manifest["captures"] if c["id"] == "logs")["coverage"]["gaps"] = dropped
        manifest_path.write_bytes(canonical_bytes(manifest, max_nodes=release.MAX_MANIFEST_NODES))
        with self.assertRaisesRegex(AlexandriaError, "the logs coverage does not name a gap"):
            self.check_without_verify(output)

    def test_a_legacy_plan_builds_the_same_bytes_and_check_keys(self):
        legacy = venue.fixture()
        output, release_id = self.released("legacy", legacy)
        self.assertEqual(release_id, V2_RELEASE_ID)
        result = usdc_interval.check_interval(output)
        self.assertEqual(set(result), LEGACY_CHECK_KEYS)
        manifest_path = output / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertNotIn(WRAPPER_COMPONENT, {c["name"] for c in manifest["components"]})
        # A legacy release carrying a wrapper set is a component its plan does not declare.
        wrapped, _wrapped_id = self.released("wrapped")
        source = json.loads((wrapped / "manifest.json").read_text(encoding="utf-8"))
        item = next(c for c in source["components"] if c["name"] == WRAPPER_COMPONENT)
        target = output / item["object_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((wrapped / item["object_path"]).read_bytes())
        manifest["components"].append(item)
        manifest["captures"].append(
            next(c for c in source["captures"] if c["id"] == WRAPPER_COMPONENT)
        )
        manifest_path.write_bytes(canonical_bytes(manifest, max_nodes=release.MAX_MANIFEST_NODES))
        with self.assertRaisesRegex(
            AlexandriaError, "carries a wrapper-subjects component the plan does not declare"
        ):
            self.check_without_verify(output)


class WrapperRefusalTests(WrapperCase):
    """Build and `check` on an edited release refuse each case by name.

    Collect refuses each case but a wrapper log before its epoch, which no
    opening read reaches.
    """

    def test_unknown_market_refuses(self):
        message = (
            f"block {BLOCK_A} names market {STRANGER}, which is not one of the 80 markets the "
            f"registry declares, for wrapper {WRAPPER_A}"
        )
        state = wrapper_state(
            drop={(BLOCK_A, 5)}, extra=[deployed(self.state, STRANGER, WRAPPER_A, BLOCK_A, 2, 5)]
        )
        with self.assertRaisesRegex(AlexandriaError, message):
            self.stage("collect", state)
        real = wildcat_wrappers.subject_entries

        def widened(registry):
            entries = real(registry)
            entries[STRANGER] = dict(entries[OTHER_MARKET], address=STRANGER)
            return entries

        with mock.patch.object(wildcat_wrappers, "subject_entries", widened):
            staging = self.stage("admitted", state)
        self.refused_build("unknown", state["plan"], staging, message)
        output, _release_id = self.released()

        def change(envelope, _request):
            for record in envelope["result"]:
                if record["topics"][:3] == [TOPIC, word(OTHER_MARKET), word(WRAPPER_A)]:
                    record["topics"][1] = word(STRANGER)
                    return True
            return False

        self.refused_check(output, "logs", edit_journal(change), message)

    def test_wrapper_without_code_refuses(self):
        message = (
            f"wrapper {WRAPPER_A} has no runtime code at block {BLOCK_A}, the block of the "
            "WrapperDeployed log that names it"
        )

        class Empty(venue.WildcatTransport):
            def code(self, address, number):
                return "0x" if address == WRAPPER_A else super().code(address, number)

        with self.assertRaisesRegex(AlexandriaError, message):
            self.stage("collect", self.state, transport=Empty(self.state))
        receipts = (self.root / "collect-staging" / "receipts" / "errors.jsonl").read_text()
        self.assertIn('"code":"no-code-at-wrapper-deployment"', receipts)
        real = wildcat_v2.ImmutableCodeOpening.accept

        def tolerant(phase, read, result):
            if read["kind"] == wildcat_v2.WRAPPER_CODE and result == "0x":
                return "empty"
            return real(phase, read, result)

        with mock.patch.object(wildcat_v2.ImmutableCodeOpening, "accept", tolerant):
            staging = self.stage(
                "admitted", self.state, transport=Empty(self.state), second=Empty(self.state)
            )
        self.refused_build("empty", self.plan, staging, message)
        output, _release_id = self.released()

        def change(envelope, request):
            if request["method"] == "eth_getCode" and request["params"][0] == WRAPPER_A:
                envelope["result"] = "0x"
                return True
            return False

        self.refused_check(output, OPENING_CLASS, edit_journal(change), message)

    def test_wrapper_log_outside_its_epoch_refuses(self):
        message = (
            f"wrapper {WRAPPER_A} emitted a preserved log at block {{block}}, before block "
            f"{BLOCK_A}, where the WrapperDeployed log that names it opens its epoch"
        )
        state = wrapper_state(extra=[native(self.state, WRAPPER_A, EARLY_BLOCK, 0, 0)])
        staging = self.stage("early", state)
        self.refused_build("early", state["plan"], staging, message.format(block=EARLY_BLOCK))
        output, _release_id = self.released()
        moved = "0xfeb516d9d946dd487a9346f6fee11f40c6945ee4"

        def change(envelope, _request):
            for record in envelope["result"]:
                if record["address"] == moved:
                    record["address"] = WRAPPER_A
                    return True
            return False

        self.refused_check(
            output, "logs", edit_journal(change), message.format(block=25895370)
        )

    def test_declared_wrapper_without_deployment_refuses(self):
        message = (
            f"declared wrapper {WRAPPER_B} is named by no preserved WrapperDeployed log from the "
            f"wrapper factory {FACTORY} inside the interval, blocks 25895340 to {INTERVAL_END}"
        )
        state = wrapper_state(drop={(BLOCK_B, 9)})
        with self.assertRaisesRegex(AlexandriaError, message):
            self.stage("collect", state)
        real = wildcat_wrappers.discover
        claimed = {
            "deployment": {
                "block_number": str(BLOCK_B), "log_index": 9,
                "transaction_hash": transaction(BLOCK_B, 4), "transaction_index": 4,
            },
            "market": venue.NEW_MARKET, "wrapper": WRAPPER_B,
        }

        def asserted(plan, registry, logs):
            return sorted(real(plan, registry, logs) + [claimed], key=lambda row: row["wrapper"])

        with mock.patch.object(wildcat_wrappers, "discover", asserted):
            staging = self.stage("asserted", state)
        self.refused_build("undeployed", state["plan"], staging, message)
        output, _release_id = self.released()

        def change(envelope, _request):
            for record in envelope["result"]:
                if record["topics"][:1] == [TOPIC] and record["topics"][2] == word(WRAPPER_B):
                    record["topics"][0] = OTHER_TOPIC
                    return True
            return False

        self.refused_check(output, "logs", edit_journal(change), message)

    def test_wrapper_deployed_log_on_another_block_hash_refuses(self):
        # The log that opens a wrapper's epoch and the header read that starts
        # it must name one block, as an upgrade log and its header must under
        # the proxy epoch models. B's WrapperDeployed moves to a block holding
        # no other log, under a hash the header read there does not return.
        block = BLOCK_B + 2
        other = "0x" + hashlib.sha256(b"constructed other block").hexdigest()

        def mismatch(at):
            return (
                f"the WrapperDeployed log naming wrapper {WRAPPER_B} at block {at} carries a "
                f"different block hash than the preserved header of block {at}"
            )

        moved = deployed(self.state, venue.NEW_MARKET, WRAPPER_B, block, 0, 0)
        moved["blockHash"] = other
        state = wrapper_state(drop={(BLOCK_B, 9)}, extra=[moved])
        with self.assertRaisesRegex(AlexandriaError, mismatch(block)):
            self.stage("collect", state)
        receipts = (self.root / "collect-staging" / "receipts" / "errors.jsonl").read_text()
        self.assertIn('"code":"wrapper-deployed-log-mismatch"', receipts)
        real = wildcat_v2.ImmutableCodeOpening.accept

        def tolerant(phase, read, result):
            try:
                return real(phase, read, result)
            except interval.OpeningRefusal as refusal:
                if refusal.code != "wrapper-deployed-log-mismatch":
                    raise
                phase.hashes[read["block"]] = result["hash"]
                return result["hash"]

        with mock.patch.object(wildcat_v2.ImmutableCodeOpening, "accept", tolerant):
            staging = self.stage("admitted", state)
        self.refused_build("mismatch", state["plan"], staging, mismatch(block))
        output, _release_id = self.released()

        def change(envelope, _request):
            changed = False
            for record in envelope["result"]:
                if int(record["blockNumber"], 16) == BLOCK_B:
                    record["blockHash"] = other
                    changed = True
            return changed

        self.refused_check(output, "logs", edit_journal(change), mismatch(BLOCK_B))


# Step 4: the constructed specimen through the CLI, as `wrapper_demo.py` runs it.
WRAPPER_RELEASE_ID = "sha256:9dc8e1d1a585491e3842d5b3a4a815a1f06630dd90fe23b4fbfa09e647516962"
DEMO_SCRIPT = Path(__file__).resolve().parent / "wrapper_demo.py"
# Each case's message names the wrapper and the market, block or interval at fault.
CASE_MESSAGES = {
    "unknown-market": (
        f"a preserved WrapperDeployed log at block {BLOCK_A} names market {STRANGER}, which is "
        f"not one of the 80 markets the registry declares, for wrapper {WRAPPER_A}"
    ),
    "wrapper-without-code": (
        f"wrapper {WRAPPER_A} has no runtime code at block {BLOCK_A}, the block of the "
        "WrapperDeployed log that names it, so no epoch opens for it"
    ),
    "wrapper-log-before-its-epoch": (
        f"wrapper {WRAPPER_A} emitted a preserved log at block {{block}}, before block {BLOCK_A}, "
        "where the WrapperDeployed log that names it opens its epoch; no epoch owns that log"
    ),
    "declared-wrapper-without-deployment": (
        f"declared wrapper {WRAPPER_B} is named by no preserved WrapperDeployed log from the "
        f"wrapper factory {FACTORY} inside the interval, blocks 25895340 to {INTERVAL_END}"
    ),
}


class WrapperDemonstrationTests(unittest.TestCase):
    """The specimen and the four refusal cases through `usdc_interval.main`.

    `wrapper_demo.run` executes once for the class in a temporary root. The
    cases read that transcript and the files the run left there; one also
    runs the script under `python3 -I` and compares the transcript it prints.
    """

    @classmethod
    def setUpClass(cls):
        # `wrapper_demo` imports this module for the specimen, so it is
        # imported here, once this module has finished loading.
        from tests import wrapper_demo
        cls.demo = wrapper_demo
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.root = Path(directory.name)
        cls.transcript = wrapper_demo.run(cls.root)

    def test_the_specimen_collects_reconciles_builds_and_checks_through_the_cli(self):
        specimen = self.transcript["specimen"]
        self.assertEqual([argv[0] for argv in specimen["commands"]], list(self.demo.STAGES))
        self.assertEqual(specimen["exits"], [0, 0, 0, 0])
        self.assertEqual(specimen["release_id"], WRAPPER_RELEASE_ID)
        self.assertEqual(specimen["check_release_id"], WRAPPER_RELEASE_ID)
        self.assertEqual(release.verify(self.root / "specimen" / "release"), WRAPPER_RELEASE_ID)
        self.assertNotIn(WRAPPER_RELEASE_ID, (V2_RELEASE_ID, V1_RELEASE_ID))

    def test_check_prints_each_wrapper_with_its_epoch_and_journal(self):
        listing = self.transcript["specimen"]["wrappers"]
        self.assertEqual(
            [(row["wrapper"], row["market"], row["declared"], row["attributed_logs"])
             for row in listing],
            [(WRAPPER_A, OTHER_MARKET, True, 3), (WRAPPER_B, venue.NEW_MARKET, True, 1)],
        )
        for row, (wrapper, block, tx_index, log_index) in zip(
            listing, ((WRAPPER_A, BLOCK_A, 2, 5), (WRAPPER_B, BLOCK_B, 4, 9)),
        ):
            with self.subTest(wrapper=wrapper):
                self.assertEqual(row["deployment"], {
                    "block_number": str(block), "log_index": log_index,
                    "transaction_hash": transaction(block, tx_index), "transaction_index": tx_index,
                })
                self.assertEqual(row["epoch"], {
                    "end_block": INTERVAL_END, "implementation_code_sha256": code_digest(wrapper),
                    "start_block": str(block),
                })
        output = self.root / "specimen" / "release"
        self.assertEqual(listing, usdc_interval.check_interval(output)["wrappers"])

    def test_each_case_refuses_at_the_first_command_that_reaches_it(self):
        expected = {
            "unknown-market": ("collect", []),
            "wrapper-without-code": ("collect", ["no-code-at-wrapper-deployment"]),
            "wrapper-log-before-its-epoch": ("build", []),
            "declared-wrapper-without-deployment": ("collect", []),
        }
        rows = {row["case"]: row for row in self.transcript["refusals"]}
        self.assertEqual(list(rows), list(self.demo.CASES))
        for case, (stage, codes) in expected.items():
            with self.subTest(case=case):
                row = rows[case]
                self.assertEqual(row["refused_at"], stage)
                self.assertEqual(row["exits"], [0] * self.demo.STAGES.index(stage) + [1])
                message = CASE_MESSAGES[case].format(block=EARLY_BLOCK)
                self.assertEqual(row["message"], "usdc-interval: " + message)
                self.assertEqual(row["error_receipt_codes"], codes)
                self.assertFalse(row["release_written"])
                directory = self.root / ("refusal-" + case)
                self.assertEqual(sorted(path.name for path in directory.iterdir()),
                                 ["plan.json", "staging"])

    def test_check_refuses_each_case_on_an_edited_and_resealed_release(self):
        early = next(
            int(record["blockNumber"], 16)
            for record in release_logs(self.root / "specimen" / "release")
            if int(record["blockNumber"], 16) < BLOCK_A and record["address"] != FACTORY
        )
        rows = {row["case"]: row for row in self.transcript["check_refusals"]}
        self.assertEqual(list(rows), list(self.demo.CASES))
        for case in self.demo.CASES:
            with self.subTest(case=case):
                row = rows[case]
                self.assertEqual(row["argv"], ["check", "check-" + case])
                self.assertEqual(row["exit"], 1)
                self.assertEqual(
                    row["edited_component"],
                    OPENING_CLASS if case == "wrapper-without-code" else "logs",
                )
                message = CASE_MESSAGES[case].format(block=early)
                self.assertEqual(row["message"], "usdc-interval: " + message)
                # `verify` accepts the edited copy, so the refusal is check's own.
                resealed = release.verify(self.root / ("check-" + case))
                self.assertNotEqual(resealed, WRAPPER_RELEASE_ID)

    def test_the_script_prints_the_same_transcript_under_isolated_python(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            result = subprocess.run(  # phylax: allow subprocess: fixed local interpreter argv, no shell
                [sys.executable, "-I", str(DEMO_SCRIPT)],
                cwd=elsewhere, capture_output=True, check=False, timeout=600,
            )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        printed = result.stdout.decode("utf-8")
        self.assertEqual(printed, json.dumps(self.transcript, indent=2, sort_keys=True) + "\n")

    def test_the_exit_status_needs_every_refusal_and_no_argument(self):
        self.assertTrue(self.demo.succeeded(self.transcript))
        admitted = deepcopy(self.transcript)
        admitted["check_refusals"][2]["exit"] = 0
        self.assertFalse(self.demo.succeeded(admitted))
        unrefused = deepcopy(self.transcript)
        unrefused["refusals"][0]["refused_at"] = None
        self.assertFalse(self.demo.succeeded(unrefused))
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdout", out), mock.patch.object(sys, "stderr", err):
            self.assertEqual(self.demo.main(["--output"]), 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("takes no arguments", err.getvalue())


# Step 4: what this run adds to the portable payload, against the run base.
RUN_BASE = "50d71a2e8c1777f8eb26db32dd8adeadb34063bd"
STEP_THREE_HEAD = "1093a99b69419d9826749eaefac7c91b57052f9c"
RUN_PAYLOAD_PATHS = (
    "plugins/alexandria/README.md",
    "plugins/alexandria/docs/usdc-interval-collector.md",
    "plugins/alexandria/schemas/README.md",
    "plugins/alexandria/schemas/interval-plan-v2.schema.json",
    "plugins/alexandria/schemas/wildcat-v2-wrapper-subjects-v1.schema.json",
    "plugins/alexandria/scripts/alexandria_lib/interval.py",
    "plugins/alexandria/scripts/alexandria_lib/venues/wildcat_v2.py",
    "plugins/alexandria/scripts/alexandria_lib/wildcat_wrappers.py",
    "plugins/alexandria/scripts/usdc_interval.py",
    "plugins/alexandria/skills/alexandria/EVOLUTION.md",
    "plugins/alexandria/skills/alexandria/SKILL.md",
)
MAX_FILES_ADDED = 5
MAX_BYTES_ADDED = 100_000
PORTABLE_SCRIPT = venue.REPO_ROOT / "scripts" / "portable_promise_machine.py"


def portable_module():
    """`scripts/portable_promise_machine.py`, loaded by path under a name of its own."""
    spec = importlib.util.spec_from_file_location("portable_promise_machine_2092", PORTABLE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortableBudgetTests(unittest.TestCase):
    """The portable payload bytes and files this run adds, against `RUN_BASE`.

    `RUN_PAYLOAD_PATHS` holds every path the portable payload ships that
    `git diff` names between the run base and Step 3's head, and
    `test_the_measured_paths_are_every_shipped_path_steps_one_to_three_changed`
    re-derives that set from this tree's payload. Step 4 changes no path the
    payload ships. A path's bytes at a commit are its blob there after the
    payload's own portrait transform, the bytes `expected_files` packs. Both
    ends are commits, the run base and Step 3's head, so a later edit to one
    of these paths does not count against this run's budget. Bytes added are
    the listed paths' bytes at Step 3's head less their bytes at the base; a
    file added is a listed path Step 3's head has and the base lacks. The
    payload's `MANIFEST.json` and `.horos/boundary.json` are generated rather
    than copied from a source file, so both are outside the comparison. A
    clone without either commit cannot measure: a shallow checkout skips and
    any other clone fails, each naming the commits it lacks.
    """

    @classmethod
    def setUpClass(cls):
        cls.portable = portable_module()
        # Elenchus starts every runner with PYTHONSAFEPATH=1. The Horos scan
        # `expected_files` launches for the rendered boundary would inherit it
        # and miss its sibling imports; that boundary is outside the comparison.
        with mock.patch.dict(os.environ):
            os.environ.pop("PYTHONSAFEPATH", None)
            payload, manifest = cls.portable.expected_files(venue.REPO_ROOT)
        cls.payload = payload
        cls.omitted = {row["path"] for row in json.loads(manifest)["omitted_files"]}

    def git(self, *arguments):
        result = subprocess.run(  # phylax: allow subprocess: fixed local git argv, no shell
            ["git", "-C", str(venue.REPO_ROOT), *arguments],
            check=False, capture_output=True, env=self.portable._git_environment(),
        )
        if result.returncode:
            detail = result.stderr.decode("utf-8", "replace").strip()
            self.fail("git " + arguments[0] + " refused: " + detail)
        return result.stdout

    def is_shallow(self):
        return self.git("rev-parse", "--is-shallow-repository").strip() == b"true"

    def require_measured_commits(self):
        """Skip a shallow checkout without a measured commit; fail any other clone without one."""
        absent = [
            commit for commit in (RUN_BASE, STEP_THREE_HEAD)
            if subprocess.run(  # phylax: allow subprocess: fixed local git argv, no shell
                ["git", "-C", str(venue.REPO_ROOT), "cat-file", "-e", commit + "^{commit}"],
                check=False, capture_output=True, env=self.portable._git_environment(),
            ).returncode
        ]
        if absent:
            reason = (
                "this clone lacks " + " and ".join(absent)
                + ", the commits the run's payload budget is measured between"
            )
            if self.is_shallow():
                self.skipTest("shallow checkout: " + reason)
            self.fail(reason)

    def payload_bytes(self, commit, path):
        """The path's payload bytes at `commit`, or None where that commit has no such file."""
        if not self.git("ls-tree", "-r", "-z", "--name-only", commit, "--", path):
            return None
        data = self.git("cat-file", "blob", f"{commit}:{path}")
        return self.portable.transform_portrait_images(Path(path), data, self.omitted)[0]

    def test_run_adds_at_most_five_payload_files_and_100000_bytes(self):
        self.require_measured_commits()
        files = added = 0
        for path in RUN_PAYLOAD_PATHS:
            run = self.payload_bytes(STEP_THREE_HEAD, path)
            base = self.payload_bytes(RUN_BASE, path)
            files += run is not None and base is None
            added += len(run or b"") - len(base or b"")
        self.assertLessEqual(files, MAX_FILES_ADDED, f"{files} payload files added")
        self.assertLessEqual(added, MAX_BYTES_ADDED, f"{added} payload bytes added")

    def test_a_later_edit_to_a_measured_path_does_not_count_against_the_run(self):
        # Once the run merges, other work edits these paths. With the first
        # listed path grown past the whole budget in this tree's payload, the
        # budget case still passes, because it reads only the two commits.
        path = RUN_PAYLOAD_PATHS[0]
        grown = dict(self.payload)
        grown[path] = grown[path] + b"#" * (MAX_BYTES_ADDED + 1)
        with mock.patch.object(self, "payload", grown):
            self.test_run_adds_at_most_five_payload_files_and_100000_bytes()

    def test_a_clone_without_a_measured_commit_names_it(self):
        # A depth-2 checkout holds neither commit. The budget case must not
        # fail on git's own words there, and must name what is missing.
        missing = "f" * 40
        for shallow, outcome in ((True, unittest.SkipTest), (False, AssertionError)):
            with self.subTest(shallow=shallow):
                with mock.patch.object(sys.modules[__name__], "RUN_BASE", missing), \
                        mock.patch.object(self, "is_shallow", return_value=shallow, create=True), \
                        self.assertRaises(outcome) as raised:
                    self.test_run_adds_at_most_five_payload_files_and_100000_bytes()
                self.assertIn("this clone lacks " + missing, str(raised.exception))

    def test_the_measured_paths_are_every_shipped_path_steps_one_to_three_changed(self):
        self.require_measured_commits()
        names = self.git("diff", "--name-only", "-z", "--no-renames", RUN_BASE, STEP_THREE_HEAD)
        changed = {raw.decode("utf-8") for raw in names.split(b"\0") if raw}
        shipped = sorted(
            path for path in changed
            if path in self.payload and path != self.portable.PORTABLE_BOUNDARY
        )
        self.assertEqual(shipped, list(RUN_PAYLOAD_PATHS))
