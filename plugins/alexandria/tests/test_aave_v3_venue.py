"""Per-subject Aave V3 epochs and the upgrade-transaction order rule scoped to this venue.

`AaveEpochConformanceTests`, `AaveUpgradeRefusalTests` and
`OtherVenueCompatibilityTests` are loaded by name: the Aave conformance harness
resolves `per-subject-proxy-epochs-derived`, `unsupported-upgrade-shapes-refuse`
and `other-venues-keep-upgrade-transaction-refusal` against them.

Every subject, role, creation block and recorded implementation below is read
from the committed registry. The logs, slot words, block hashes and runtime
code are constructed: the tree holds no Aave log, and it records the seven
reviewed proxy codes only by keccak-256, not their bytes. So a case that needs
a proxy to pass the reviewed-code check substitutes the keccak-256 of one
constructed code for the reviewed table; the cases that check the table itself
and its refusal use the table as the module holds it.
"""

import ast
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib import aave_registry, interval  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.venues import aave_v3, compound_v3, wildcat_v1, wildcat_v2  # noqa: E402
from tests import test_interval as epoch_fixture  # noqa: E402

REGISTRY_PATH = PLUGIN / "examples" / "aave-v3-interval-v0" / "registry.json"
SPECIMEN_PATH = PLUGIN / "docs" / "aave-v3-interval" / "design" / "upgrade-transaction-specimen.json"
SCRIPTS = PLUGIN / "scripts"
POOL = aave_registry.MARKET["pool"]
PROVIDER = aave_registry.MARKET["addresses_provider"]
START = 16291071
END = 26022093
# A token proxy the registry records as created inside the interval, at block
# 17,699,249, and upgraded in the specimen transaction.
TOKEN_PROXY = "0x00907f9921424583e7ffbfedf84f92b7b2be4977"
# A constructed proxy runtime code, standing in for the reviewed bytes the
# tree does not hold.
PROXY_CODE = "0x" + "608060405236601057600e6013565b005b" * 4
ORDINARY_TOPIC = "0x" + "aa" * 32


def registry():
    return json.loads(REGISTRY_PATH.read_bytes())


REGISTRY = registry()
ENTRIES = aave_registry.subject_entries(REGISTRY)


def block_hash(block):
    return "0x" + hashlib.sha256(f"block {block}".encode()).hexdigest()


def transaction_hash(block, tx):
    return "0x" + hashlib.sha256(f"transaction {block} {tx}".encode()).hexdigest()


def word(address):
    return "0x" + "0" * 24 + address[2:]


def code_of(address):
    """A distinct constructed runtime code for one address."""
    return "0x5f" + address[2:]


def log(subject, block, tx, index, topics=None):
    return {
        "address": subject,
        "blockHash": block_hash(block),
        "blockNumber": hex(block),
        "data": "0x",
        "logIndex": hex(index),
        "topics": list(topics or [ORDINARY_TOPIC]),
        "transactionHash": transaction_hash(block, tx),
        "transactionIndex": hex(tx),
    }


def upgraded(subject, block, tx, index, implementation):
    return log(subject, block, tx, index, [interval.UPGRADED_TOPIC, word(implementation)])


def active(subject, block):
    """The implementation the registry records for a proxy at one block."""
    for item in ENTRIES[subject]["implementations"]:
        if item["from_block"] <= block and (item["to_block"] is None or block <= item["to_block"]):
            return item["implementation"]
    raise AssertionError(f"the registry records no implementation of {subject} at {block}")


def plan(subjects, start=START, end=END):
    return {
        "chain": "eip155:1",
        "deployment": "aave-v3-constructed",
        "interval": {"end": str(end), "start": str(start)},
        "subjects": list(subjects),
        "venue": aave_v3.VENUE,
    }


def coordinate(record):
    return tuple(int(record[key], 16) for key in ("blockNumber", "transactionIndex", "logIndex"))


def evidence(document, logs, *, slots=None):
    """The opening reads a plan's logs need, derived from the registry and the logs.

    Each proxy's slot is read at its opening block, where the registry says
    which implementation it held, and at every block it announces an upgrade
    in, where the slot holds what the announcement names. `slots` overrides
    individual reads as `{(subject, block): address}`.
    """
    start, end = int(document["interval"]["start"]), int(document["interval"]["end"])
    logs = sorted(logs, key=coordinate)
    slot_reads, code_reads, hashes = {}, {}, {end: block_hash(end)}
    for subject in document["subjects"]:
        entry = ENTRIES[subject]
        opening = max(start, entry["creation_block"])
        if opening > end:
            continue
        hashes[opening] = block_hash(opening)
        if entry["role"] in aave_registry.PROXY_ROLES:
            code_reads[subject] = PROXY_CODE
            slot_reads.setdefault(subject, {})[opening] = word(active(subject, opening))
            for item in entry["implementations"]:
                code_reads[item["implementation"]] = code_of(item["implementation"])
        else:
            code_reads[subject] = code_of(subject)
    for record in logs:
        block = int(record["blockNumber"], 16)
        hashes[block] = block_hash(block)
        if record["topics"][0] == interval.UPGRADED_TOPIC and len(record["topics"]) == 2:
            slot_reads.setdefault(record["address"], {})[block] = record["topics"][1]
    for (subject, block), implementation in (slots or {}).items():
        slot_reads.setdefault(subject, {})[block] = word(implementation)
        code_reads.setdefault(implementation, code_of(implementation))
    return {"block_hashes": hashes, "code_reads": code_reads, "logs": logs, "slot_reads": slot_reads}


def reviewed_constructed_code():
    """The reviewed table with the constructed proxy code's keccak-256 in it."""
    digest = "0x" + aave_v3.keccak256(bytes.fromhex(PROXY_CODE[2:])).hex()
    return mock.patch.dict(aave_v3.REVIEWED_PROXY_CODES, {digest: (len(PROXY_CODE) // 2 - 1, "constructed")})


def derive(document, staged, **overrides):
    reads = evidence(document, staged, slots=overrides.pop("slots", None))
    reads.update(overrides)
    with reviewed_constructed_code():
        epochs = aave_v3.derive_epochs(document, REGISTRY, **reads)
        rows = aave_v3.attribute_positions(reads["logs"], document["subjects"], document["interval"], epochs)
    return epochs, rows


def pool_revision_logs():
    """For each of the Pool's recorded upgrades: an ordinary log, `Upgraded`, an ordinary log.

    All three sit in one transaction, so the order rule is what owns the two
    ordinary logs.
    """
    logs = []
    for item in ENTRIES[POOL]["implementations"][1:]:
        block = item["from_block"]
        logs.append(log(POOL, block, 5, 9))
        logs.append(upgraded(POOL, block, 5, 10, item["implementation"]))
        logs.append(log(POOL, block, 5, 11))
    return logs


class AaveEpochConformanceTests(unittest.TestCase):
    """Proxy epochs follow the slot and its announcements; immutable subjects have one."""

    def test_proxy_epochs_follow_upgrade_positions(self):
        document = plan([POOL, PROVIDER])
        logs = pool_revision_logs()
        epochs, rows = derive(document, logs)
        table = epochs[POOL]
        recorded = ENTRIES[POOL]["implementations"]
        self.assertEqual([epoch["implementation"] for epoch in table],
                         [item["implementation"] for item in recorded])
        for epoch, item in zip(table[1:], recorded[1:]):
            expected = {"block_number": str(item["from_block"]), "log_index": 10, "transaction_index": 5}
            self.assertEqual(epoch["start_position"], expected)
            self.assertEqual(epoch["upgrade"], dict(expected, transaction_hash=transaction_hash(item["from_block"], 5)))
        by_position = {(row["block_number"], row["log_index"]): row for row in rows}
        for index, item in enumerate(recorded[1:], start=1):
            block = str(item["from_block"])
            # Before the announcement, the old implementation; it and after, the new.
            self.assertEqual(by_position[(block, 9)]["epoch_index"], index - 1)
            self.assertEqual(by_position[(block, 10)]["epoch_index"], index)
            self.assertEqual(by_position[(block, 10)]["kind"], "upgrade-boundary")
            self.assertEqual(by_position[(block, 11)]["epoch_index"], index)
        code = hashlib.sha256(bytes.fromhex(code_of(recorded[3]["implementation"])[2:])).hexdigest()
        self.assertEqual(table[3]["implementation_code_sha256"], code)

    def test_pre_interval_subject_opens_at_interval_start(self):
        library = min(
            (entry for entry in ENTRIES.values() if entry["role"] == "library"),
            key=lambda entry: entry["creation_block"],
        )
        self.assertLess(library["creation_block"], START)
        epochs, _ = derive(plan([POOL, PROVIDER, library["address"]]), [])
        (epoch,) = epochs[library["address"]]
        self.assertEqual(epoch["start_position"], {"block_number": str(START), "log_index": None, "transaction_index": None})
        self.assertEqual(epoch["implementation"], library["address"])
        self.assertIsNone(epoch["upgrade"])
        self.assertEqual(
            epoch["implementation_code_sha256"],
            hashlib.sha256(bytes.fromhex(code_of(library["address"])[2:])).hexdigest(),
        )
        # A proxy created before a later segment's start opens at that start
        # with the implementation its slot holds there.
        segment = 20_000_000
        epochs, _ = derive(plan([POOL, PROVIDER], start=segment), [])
        (epoch,) = epochs[POOL]
        self.assertEqual(epoch["start_block"], str(segment))
        self.assertEqual(epoch["implementation"], active(POOL, segment))
        self.assertEqual(epochs[PROVIDER][0]["start_block"], str(segment))

    def test_proxy_created_in_interval_opens_at_its_creation_block(self):
        creation = ENTRIES[TOKEN_PROXY]["creation_block"]
        self.assertGreater(creation, START)
        epochs, _ = derive(plan([POOL, PROVIDER, TOKEN_PROXY], end=creation + 10), [log(TOKEN_PROXY, creation, 2, 4)])
        (epoch,) = epochs[TOKEN_PROXY]
        self.assertEqual(epoch["start_position"], {"block_number": str(creation), "log_index": None, "transaction_index": None})
        self.assertEqual(epoch["implementation"], ENTRIES[TOKEN_PROXY]["implementations"][0]["implementation"])
        self.assertEqual(epoch["end_position"]["block_number"], str(creation + 11))
        self.assertNotIn(TOKEN_PROXY, derive(plan([POOL, PROVIDER, TOKEN_PROXY], end=creation - 1), [])[0])


class AaveTablesTests(unittest.TestCase):
    """The Pool's recorded revisions, the reviewed codes and the epoch bound."""

    def test_pools_eleven_recorded_revisions_tile_its_extent(self):
        epochs, _ = derive(plan([POOL, PROVIDER]), pool_revision_logs())
        table = epochs[POOL]
        self.assertEqual(len(table), len(ENTRIES[POOL]["implementations"]))
        self.assertEqual(len(table), 11)
        self.assertEqual(table[0]["start_block"], str(ENTRIES[POOL]["creation_block"]))
        for earlier, later in zip(table, table[1:]):
            self.assertEqual(earlier["end_position"], later["start_position"])
            self.assertEqual(earlier["end_block"], later["start_block"])
            self.assertEqual(earlier["end_hash"], later["start_hash"])
        self.assertEqual(table[-1]["end_position"], {"block_number": str(END + 1), "log_index": None, "transaction_index": None})
        interval.validate_epochs(epochs, START, END)

    def test_reviewed_proxy_codes_are_the_registrys_seven(self):
        derived = {}
        for entry in ENTRIES.values():
            if entry["role"] in aave_registry.PROXY_ROLES:
                derived.setdefault(entry["code_keccak256"], set()).add((entry["code_length"], entry["source_set"]))
        self.assertEqual(len(derived), 7)
        self.assertEqual(
            {key: next(iter(value)) for key, value in derived.items()}, aave_v3.REVIEWED_PROXY_CODES
        )
        self.assertTrue(all(len(value) == 1 for value in derived.values()))
        proxies = [entry for entry in ENTRIES.values() if entry["role"] in aave_registry.PROXY_ROLES]
        self.assertEqual(len(proxies), 172)
        self.assertEqual(len(ENTRIES) - len(proxies), 184)
        self.assertEqual(
            {entry["role"] for entry in ENTRIES.values()} - set(aave_registry.PROXY_ROLES),
            aave_v3.IMMUTABLE_ROLES,
        )

    def test_keccak_matches_the_constants_it_can_derive(self):
        self.assertEqual(
            aave_v3.keccak256(b"").hex(),
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        )
        self.assertEqual("0x" + aave_v3.keccak256(b"Upgraded(address)").hex(), interval.UPGRADED_TOPIC)
        slot = int.from_bytes(aave_v3.keccak256(b"eip1967.proxy.implementation"), "big") - 1
        self.assertEqual(f"0x{slot:064x}", interval.IMPLEMENTATION_SLOT)
        # The same permutation and padding with SHA3's domain byte is
        # SHA3-256, which the standard library does carry, at every length
        # across two rate blocks and at a proxy code's length.
        for length in list(range(0, 300)) + [2400]:
            data = bytes((index * 7 + 3) % 256 for index in range(length))
            self.assertEqual(aave_v3._sponge(data, 0x06), hashlib.sha3_256(data).digest(), length)
        with self.assertRaisesRegex(AlexandriaError, "keccak-256 input must be bytes"):
            aave_v3.keccak256("text")

    def test_epoch_limit_is_read_from_the_interval_module(self):
        limit = interval.MAX_EPOCHS
        recorded = [item["implementation"] for item in ENTRIES[POOL]["implementations"]]
        first = ENTRIES[POOL]["creation_block"] + 1

        def announcements(count):
            return [upgraded(POOL, first + number, 0, 0, recorded[number % 2]) for number in range(count)]

        epochs, _ = derive(plan([POOL, PROVIDER]), announcements(limit - 1))
        self.assertEqual(len(epochs[POOL]), limit)
        with self.assertRaises(aave_v3.EpochRefusal) as raised:
            derive(plan([POOL, PROVIDER]), announcements(limit))
        self.assertEqual(raised.exception.rule, aave_v3.RULE_EPOCH_LIMIT)
        self.assertEqual(raised.exception.block, first + limit - 1)
        self.assertIn(f"above the {limit}-epoch limit", str(raised.exception))


class AaveUpgradeTransactionSpecimenTests(unittest.TestCase):
    """The committed specimen: 98 subjects upgraded in one transaction at block 22,839,362.

    The specimen records counts and one subject's log indexes, not every
    subject's. The upgraded subjects are the registry's own: every proxy with
    a recorded epoch opened by that transaction. The example subject's log
    indexes are the specimen's; every other subject's are constructed, and one
    of them also logs before its own `Upgraded`, so two do, as the specimen
    counts.
    """

    def setUp(self):
        self.specimen = json.loads(SPECIMEN_PATH.read_bytes())
        self.block = self.specimen["block_number"]
        self.tx = self.specimen["transaction_index"]
        self.upgraded = sorted(
            address for address, entry in ENTRIES.items()
            if entry["implementations"]
            and any(item["transaction"] == self.specimen["transaction"] for item in entry["implementations"])
        )

    def test_the_registry_names_the_specimens_upgraded_subjects(self):
        self.assertEqual(self.block, 22_839_362)
        self.assertEqual(self.specimen["transaction"], "0x6f45f51fa5dd0246298f2e6284c43e0c57ef5e6b646ee1dfcd67f3f4f11dacd9")
        self.assertEqual(len(self.upgraded), self.specimen["subjects_upgraded"])
        self.assertEqual(len(self.upgraded), 98)
        self.assertIn(self.specimen["example"]["subject"], self.upgraded)
        for subject in self.upgraded:
            item = next(i for i in ENTRIES[subject]["implementations"] if i["transaction"] == self.specimen["transaction"])
            self.assertEqual(item["from_block"], self.block)

    def test_each_upgraded_subjects_ordinary_logs_follow_their_log_index(self):
        example = self.specimen["example"]
        before_subjects = {example["subject"], next(s for s in self.upgraded if s != example["subject"])}
        self.assertEqual(len(before_subjects), self.specimen["upgraded_subjects_with_an_ordinary_log_before_their_upgrade"])
        logs, expected = [], {}
        # The example's own indexes, then 3 constructed indexes per other subject above them.
        cursor = max(index for index, _kind in example["log_indexes"]) + 1
        for subject in self.upgraded:
            new = next(i["implementation"] for i in ENTRIES[subject]["implementations"] if i["from_block"] == self.block)
            if subject == example["subject"]:
                shape = [(index, kind) for index, kind in example["log_indexes"]]
            else:
                shape = ([(cursor, "ordinary")] if subject in before_subjects else []) + [
                    (cursor + 1, "Upgraded"), (cursor + 2, "ordinary"),
                ]
                cursor += 3
            announced = next(index for index, kind in shape if kind == "Upgraded")
            for index, kind in shape:
                if kind == "Upgraded":
                    logs.append(upgraded(subject, self.block, self.tx, index, new))
                else:
                    logs.append(log(subject, self.block, self.tx, index))
                expected[(subject, index)] = 0 if index < announced else 1
        document = plan([POOL, PROVIDER] + [s for s in self.upgraded if s != POOL], start=self.block - 100, end=self.block + 100)
        epochs, rows = derive(document, logs)
        owners = {(row["subject"], row["log_index"]): row["epoch_index"] for row in rows}
        self.assertEqual(owners, expected)
        # Exactly the two subjects that log before their own `Upgraded` have a
        # log in the old epoch; every one of the 98 has one in the new.
        self.assertEqual({subject for (subject, _index), owner in owners.items() if owner == 0}, before_subjects)
        self.assertEqual({subject for (subject, _index), owner in owners.items() if owner == 1}, set(self.upgraded))
        example_owners = [owners[(example["subject"], index)] for index, _kind in example["log_indexes"]]
        self.assertEqual(example_owners, [0, 0, 1, 1, 1, 1, 1, 1])
        for subject in self.upgraded:
            with self.subTest(subject=subject):
                old, new = epochs[subject]
                self.assertEqual(old["implementation"], active(subject, self.block - 1))
                self.assertEqual(new["implementation"], active(subject, self.block))
                self.assertEqual(new["start_position"]["transaction_index"], self.tx)
        # The same logs under the shared default refuse, as every other venue does.
        with self.assertRaisesRegex(AlexandriaError, "in an upgrade transaction is unsupported"):
            interval.attribute_logs(sorted(logs, key=coordinate), document["subjects"], document["interval"], epochs)


def refusal(test, rule, document, logs, **overrides):
    with test.assertRaises(aave_v3.EpochRefusal) as raised:
        derive(document, logs, **overrides)
    test.assertEqual(raised.exception.rule, rule)
    return raised.exception


class AaveUpgradeRefusalTests(unittest.TestCase):
    """Each unsupported upgrade shape refuses by name, naming where it is and which rule."""

    def assertNames(self, error, subject, block, tx, index, rule):
        message = str(error)
        for part in (f"rule {rule}", f"subject {subject}", f"block {block}",
                     f"transaction index {tx}", f"log index {index}"):
            self.assertIn(part, message)
        self.assertEqual((error.subject, error.block, error.transaction_index, error.log_index),
                         (subject, block, None if tx == "none" else tx, None if index == "none" else index))

    def test_upgrade_in_opening_block_refuses(self):
        creation = ENTRIES[TOKEN_PROXY]["creation_block"]
        recorded = ENTRIES[TOKEN_PROXY]["implementations"][1]["implementation"]
        error = refusal(self, aave_v3.RULE_UPGRADE_IN_OPENING_BLOCK, plan([POOL, PROVIDER, TOKEN_PROXY]),
                        [upgraded(TOKEN_PROXY, creation, 3, 7, recorded)])
        self.assertNames(error, TOKEN_PROXY, creation, 3, 7, aave_v3.RULE_UPGRADE_IN_OPENING_BLOCK)
        # At the interval start, the rule is the same one.
        pool = ENTRIES[POOL]["implementations"][1]["implementation"]
        error = refusal(self, aave_v3.RULE_UPGRADE_IN_OPENING_BLOCK, plan([POOL, PROVIDER], start=20_000_000),
                        [upgraded(POOL, 20_000_000, 0, 1, pool)])
        self.assertNames(error, POOL, 20_000_000, 0, 1, aave_v3.RULE_UPGRADE_IN_OPENING_BLOCK)

    def test_upgrade_before_opening_block_refuses(self):
        creation = ENTRIES[TOKEN_PROXY]["creation_block"]
        recorded = ENTRIES[TOKEN_PROXY]["implementations"][0]["implementation"]
        error = refusal(self, aave_v3.RULE_UPGRADE_BEFORE_OPENING_BLOCK, plan([POOL, PROVIDER, TOKEN_PROXY]),
                        [upgraded(TOKEN_PROXY, creation - 1, 0, 2, recorded)])
        self.assertNames(error, TOKEN_PROXY, creation - 1, 0, 2, aave_v3.RULE_UPGRADE_BEFORE_OPENING_BLOCK)

    def test_two_upgrades_of_one_subject_in_one_block_refuse(self):
        first, second = (item["implementation"] for item in ENTRIES[POOL]["implementations"][1:3])
        block = ENTRIES[POOL]["implementations"][1]["from_block"]
        for tx in (4, 3):
            with self.subTest(second_transaction=tx):
                logs = [upgraded(POOL, block, 3, 5, first), upgraded(POOL, block, tx, 8, second)]
                error = refusal(self, aave_v3.RULE_TWO_UPGRADES_IN_ONE_BLOCK, plan([POOL, PROVIDER]), logs,
                                slots={(POOL, block): second})
                self.assertNames(error, POOL, block, tx, 8, aave_v3.RULE_TWO_UPGRADES_IN_ONE_BLOCK)
        # Two subjects each upgraded once in one block are not this shape.
        creation = ENTRIES[TOKEN_PROXY]["creation_block"]
        token_new = ENTRIES[TOKEN_PROXY]["implementations"][1]["implementation"]
        pool_new = ENTRIES[POOL]["implementations"][6]["implementation"]
        derive(plan([POOL, PROVIDER, TOKEN_PROXY]), [
            upgraded(POOL, creation + 5, 1, 1, pool_new), upgraded(TOKEN_PROXY, creation + 5, 1, 2, token_new),
        ])

    def test_slot_disagreeing_with_announcement_refuses(self):
        item = ENTRIES[POOL]["implementations"][1]
        previous = ENTRIES[POOL]["implementations"][0]["implementation"]
        error = refusal(self, aave_v3.RULE_SLOT_DISAGREES, plan([POOL, PROVIDER]),
                        [upgraded(POOL, item["from_block"], 2, 6, item["implementation"])],
                        slots={(POOL, item["from_block"]): previous})
        self.assertNames(error, POOL, item["from_block"], 2, 6, aave_v3.RULE_SLOT_DISAGREES)
        self.assertIn(previous, str(error))

    def test_unrecorded_implementation_refuses(self):
        stranger = "0x" + "d0" * 20
        block = ENTRIES[POOL]["creation_block"] + 50
        error = refusal(self, aave_v3.RULE_UNRECORDED_IMPLEMENTATION, plan([POOL, PROVIDER]),
                        [upgraded(POOL, block, 1, 3, stranger)])
        self.assertNames(error, POOL, block, 1, 3, aave_v3.RULE_UNRECORDED_IMPLEMENTATION)
        # Another subject's recorded implementation is not this subject's.
        token = ENTRIES[TOKEN_PROXY]["implementations"][0]["implementation"]
        refusal(self, aave_v3.RULE_UNRECORDED_IMPLEMENTATION, plan([POOL, PROVIDER]),
                [upgraded(POOL, block, 1, 3, token)])
        # An opening slot holding an unrecorded implementation refuses the same way.
        opening = ENTRIES[POOL]["creation_block"]
        error = refusal(self, aave_v3.RULE_UNRECORDED_IMPLEMENTATION, plan([POOL, PROVIDER]), [],
                        slots={(POOL, opening): stranger})
        self.assertNames(error, POOL, opening, "none", "none", aave_v3.RULE_UNRECORDED_IMPLEMENTATION)

    def test_unreviewed_proxy_code_refuses(self):
        document = plan([POOL, PROVIDER])
        reads = evidence(document, [])
        with self.assertRaises(aave_v3.EpochRefusal) as raised:
            aave_v3.derive_epochs(document, REGISTRY, **reads)
        error = raised.exception
        self.assertEqual(error.rule, aave_v3.RULE_UNREVIEWED_PROXY_CODE)
        self.assertNames(error, POOL, ENTRIES[POOL]["creation_block"], "none", "none",
                         aave_v3.RULE_UNREVIEWED_PROXY_CODE)
        self.assertIn("0x" + aave_v3.keccak256(bytes.fromhex(PROXY_CODE[2:])).hex(), str(error))

    def test_unrecognised_role_refuses(self):
        document = plan([POOL, PROVIDER])
        reads = evidence(document, [])
        entries = deepcopy(ENTRIES)
        entries[PROVIDER]["role"] = "price-oracle"
        with reviewed_constructed_code(), self.assertRaises(aave_v3.EpochRefusal) as raised:
            aave_v3.derive_subject_epochs(
                chain=document["chain"], deployment=document["deployment"], interval=document["interval"],
                subjects=document["subjects"], entries=entries, **reads,
            )
        self.assertNames(raised.exception, PROVIDER, START, "none", "none", aave_v3.RULE_UNRECOGNISED_ROLE)
        self.assertIn("'price-oracle'", str(raised.exception))

    def test_announcement_from_an_immutable_subject_refuses(self):
        error = refusal(self, aave_v3.RULE_UPGRADE_FROM_IMMUTABLE, plan([POOL, PROVIDER]),
                        [upgraded(PROVIDER, START + 3, 0, 1, POOL)])
        self.assertNames(error, PROVIDER, START + 3, 0, 1, aave_v3.RULE_UPGRADE_FROM_IMMUTABLE)

    def test_malformed_announcement_refuses(self):
        block = ENTRIES[POOL]["creation_block"] + 9
        recorded = ENTRIES[POOL]["implementations"][1]["implementation"]
        for label, topics in (
            ("one topic", [interval.UPGRADED_TOPIC]),
            ("three topics", [interval.UPGRADED_TOPIC, word(recorded), word(recorded)]),
            ("not left-padded", [interval.UPGRADED_TOPIC, "0x" + "11" * 32]),
            ("zero address", [interval.UPGRADED_TOPIC, word("0x" + "00" * 20)]),
        ):
            with self.subTest(shape=label):
                error = refusal(self, aave_v3.RULE_MALFORMED_UPGRADE, plan([POOL, PROVIDER]),
                                [log(POOL, block, 0, 4, topics)])
                self.assertNames(error, POOL, block, 0, 4, aave_v3.RULE_MALFORMED_UPGRADE)


class AaveInputShapeTests(unittest.TestCase):
    """Malformed or missing reads refuse with a message naming what is missing."""

    def refuses(self, message, **overrides):
        with self.assertRaisesRegex(AlexandriaError, message):
            derive(plan([POOL, PROVIDER]), [], **overrides)

    def test_container_types_refuse_by_field(self):
        for field in ("slot_reads", "code_reads", "block_hashes"):
            for bad in (None, [], "text", 3):
                with self.subTest(field=field, bad=bad):
                    self.refuses(f"opening reads' {field} is not a mapping", **{field: bad})
        self.refuses("preserved subject logs are not a list", logs={"a": 1})

    def test_missing_reads_refuse_by_what_they_needed(self):
        document = plan([POOL, PROVIDER])
        reads = evidence(document, [])
        opening = ENTRIES[POOL]["creation_block"]
        self.refuses(f"proxy subject {POOL} has no preserved implementation slot reads", slot_reads={})
        self.refuses("slot reads of proxy subject .* are not a mapping", slot_reads={POOL: [1]})
        self.refuses(f"no implementation slot read at block {opening}", slot_reads={POOL: {}})
        self.refuses(f"proxy subject {POOL}: implementation slot read at block {opening} is the zero address",
                     slot_reads={POOL: {opening: word("0x" + "00" * 20)}})
        self.refuses(f"proxy subject {POOL}: implementation slot read at block {opening} is not a 32-byte word",
                     slot_reads={POOL: {opening: 7}})
        codes = dict(reads["code_reads"])
        del codes[PROVIDER]
        self.refuses(f"needs the runtime code of {PROVIDER}", code_reads=codes)
        codes = dict(reads["code_reads"])
        del codes[active(POOL, opening)]
        self.refuses(f"needs the runtime code of {active(POOL, opening)}", code_reads=codes)
        self.refuses("runtime code is not hexadecimal", code_reads={**reads["code_reads"], PROVIDER: 12})
        hashes = dict(reads["block_hashes"])
        del hashes[END]
        self.refuses(f"epoch boundary at block {END}, which has no preserved block hash", block_hashes=hashes)
        self.refuses("which has no preserved block hash", block_hashes={**reads["block_hashes"], END: None})

    def test_decimal_text_block_keys_are_read(self):
        document = plan([POOL, PROVIDER])
        reads = evidence(document, [])
        reads["slot_reads"] = {POOL: {str(block): value for block, value in reads["slot_reads"][POOL].items()}}
        reads["block_hashes"] = {str(block): value for block, value in reads["block_hashes"].items()}
        with reviewed_constructed_code():
            epochs = aave_v3.derive_epochs(document, REGISTRY, **reads)
        self.assertEqual(epochs[POOL][0]["implementation"], active(POOL, ENTRIES[POOL]["creation_block"]))

    def test_interval_shapes_refuse_by_name(self):
        for label, value, message in (
            ("absent", None, "plan interval has an unknown shape"),
            ("extra key", {"start": "1", "end": "2", "width": "3"}, "plan interval has an unknown shape"),
            ("integer start", {"start": START, "end": str(END)}, "interval start is not a bounded decimal"),
            ("padded end", {"start": str(START), "end": "026022093"}, "interval end is not a bounded decimal"),
            ("huge end", {"start": str(START), "end": "9" * 30}, "interval end is not a bounded decimal"),
            ("reversed", {"start": str(END), "end": str(START)}, "interval end precedes its start"),
        ):
            with self.subTest(shape=label):
                document = plan([POOL, PROVIDER])
                document["interval"] = value
                with self.assertRaisesRegex(AlexandriaError, message):
                    aave_v3.derive_epochs(document, REGISTRY, logs=[], slot_reads={}, code_reads={}, block_hashes={})

    def test_registry_entry_shapes_refuse_by_field(self):
        document = plan([POOL, PROVIDER])
        reads = evidence(document, [])

        def entries_with(subject, **changes):
            entries = deepcopy(ENTRIES)
            entries[subject].update(changes)
            return entries

        for label, entries, message in (
            ("not a mapping", [], "registry entries are not a mapping"),
            ("missing subject", {POOL: ENTRIES[POOL]}, f"no entry for declared subject {PROVIDER}"),
            ("text creation", entries_with(PROVIDER, creation_block="16291071"), f"entry for {PROVIDER} has no integer creation_block"),
            ("bool creation", entries_with(PROVIDER, creation_block=True), f"entry for {PROVIDER} has no integer creation_block"),
            ("no implementations", entries_with(POOL, implementations=None), f"proxy {POOL} records no implementations"),
            ("unaddressed implementation", entries_with(POOL, implementations=[{"implementation": None}]),
             f"proxy {POOL} implementation 0 is not a lowercase address"),
        ):
            with self.subTest(shape=label), reviewed_constructed_code():
                with self.assertRaisesRegex(AlexandriaError, message):
                    aave_v3.derive_subject_epochs(
                        chain=document["chain"], deployment=document["deployment"],
                        interval=document["interval"], subjects=document["subjects"],
                        entries=entries, **reads,
                    )

    def test_derivation_checks_the_plan_scope_first(self):
        document = plan([POOL])
        with self.assertRaisesRegex(AlexandriaError, "main market's AddressesProvider"):
            aave_v3.derive_epochs(document, REGISTRY, logs=[], slot_reads={}, code_reads={}, block_hashes={})
        with self.assertRaisesRegex(AlexandriaError, "no declared subject has an extent inside the interval"):
            derive(plan([POOL, PROVIDER], start=100, end=200), [])
        self.assertEqual(aave_v3.opening_blocks(plan([POOL, PROVIDER, TOKEN_PROXY], end=17_000_000), REGISTRY),
                         {POOL: ENTRIES[POOL]["creation_block"], PROVIDER: START})

    def test_opening_phase_still_refuses_by_name(self):
        with self.assertRaisesRegex(AlexandriaError, "does not yet plan the opening reads"):
            aave_v3.opening_phase(plan([POOL, PROVIDER]), REGISTRY, [])


def keyword_callers(name):
    """Every module under scripts/ that passes `name` as a call keyword, by relative path."""
    found = set()
    for path in sorted(SCRIPTS.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and any(keyword.arg == name for keyword in node.keywords):
                found.add(path.relative_to(SCRIPTS).as_posix())
    return found


class OtherVenueCompatibilityTests(unittest.TestCase):
    """The order rule is off by default, and only the Aave module turns it on."""

    def test_compound_still_refuses_an_ordinary_log_in_its_upgrade_transaction(self):
        # The Compound path: the collector's own EIP-1967 discovery over the
        # preserved epoch fixture, with an ordinary log in the upgrade's own
        # transaction on each side of it.
        self.assertEqual(compound_v3.EPOCH_MODEL, "eip1967-proxy")
        self.assertFalse(hasattr(compound_v3, "opening_phase"))
        for offset, index in ((0, "0x3"), (2, "0x5")):
            with self.subTest(side="before" if offset == 0 else "after"):
                value = epoch_fixture.epoch_evidence()
                upgrade = value["upgrade_logs"][0]
                upgrade["transactionIndex"], upgrade["logIndex"] = "0x2", "0x4"
                ordinary = deepcopy(upgrade)
                ordinary.update(topics=[ORDINARY_TOPIC], logIndex=index)
                value["upgrade_logs"] = [ordinary, upgrade] if offset == 0 else [upgrade, ordinary]
                with self.assertRaisesRegex(AlexandriaError, "in an upgrade transaction is unsupported"):
                    interval.discover_epochs(**value)
                scope = value["interval"]
                for passed in ({}, {"order_upgrade_transactions": False}):
                    with self.assertRaisesRegex(AlexandriaError, "in an upgrade transaction is unsupported"):
                        interval.proxy_log_positions(value["upgrade_logs"], value["proxy"], scope, **passed)
                rows = interval.proxy_log_positions(
                    value["upgrade_logs"], value["proxy"], scope, order_upgrade_transactions=True
                )
                self.assertEqual(len(rows), 2)
        signature = inspect.signature(interval.proxy_log_positions).parameters["order_upgrade_transactions"]
        self.assertIs(signature.default, False)
        self.assertIs(
            inspect.signature(interval.attribute_logs).parameters["order_upgrade_transactions"].default, False
        )
        # Only the Aave module turns it on; the shared module only forwards it.
        self.assertEqual(
            keyword_callers("order_upgrade_transactions"),
            {"alexandria_lib/interval.py", "alexandria_lib/venues/aave_v3.py"},
        )
        forwarded = [
            keyword.value for node in ast.walk(ast.parse((SCRIPTS / "alexandria_lib/interval.py").read_text()))
            if isinstance(node, ast.Call) for keyword in node.keywords
            if keyword.arg == "order_upgrade_transactions"
        ]
        self.assertEqual([ast.unparse(value) for value in forwarded], ["order_upgrade_transactions"])
        for bad in (None, 1, "yes"):
            with self.subTest(flag=bad), self.assertRaisesRegex(AlexandriaError, "must be True or False"):
                interval.proxy_log_positions([], "0x" + "11" * 20, {"start": "1", "end": "2"},
                                             order_upgrade_transactions=bad)

    def test_wildcat_venues_still_read_no_upgrade_topic(self):
        for module in (wildcat_v1, wildcat_v2):
            with self.subTest(venue=module.VENUE):
                self.assertEqual(module.EPOCH_MODEL, "immutable-code")
                self.assertIsNone(module.ImmutableCodeOpening.upgrade_topic)
                source = Path(module.__file__).read_text(encoding="utf-8")
                self.assertNotIn("order_upgrade_transactions", source)
                self.assertNotIn(interval.UPGRADED_TOPIC, source)
                self.assertNotIn("UPGRADED_TOPIC", source)
        # Under `upgrade_topic=None` an `Upgraded` topic is an ordinary log,
        # so no upgrade transaction exists for the order rule to govern.
        subject = "0x" + "12" * 20
        records = [
            log(subject, 1000, 0, 0, [interval.UPGRADED_TOPIC, word("0x" + "34" * 20)]),
            log(subject, 1000, 0, 1),
        ]
        rows = interval.proxy_log_positions(records, [subject], {"start": "999", "end": "1001"}, upgrade_topic=None)
        self.assertEqual([row["kind"] for row in rows], ["proxy-log", "proxy-log"])


if __name__ == "__main__":
    unittest.main()
