"""The log walk against the whole-list derivation it replaces.

The design record's `walk-matches-whole-list-derivation` cell loads four
classes by name:

- `WalkEquivalenceTests` compares the walk's rows, and the rows of the
  `proxy_log_positions` and `attribute_logs` wrappers, with the base commit's
  own functions. Those are read from a `git show` of the base into a
  temporary module, never from the working tree. The logs are the
  constructed Compound, Wildcat V1 and Wildcat V2 releases this module builds
  in process, and the preserved V1 and V2 releases when
  `ALEXANDRIA_WILDCAT_V1_RELEASE` and `ALEXANDRIA_WILDCAT_V2_RELEASE` name
  them.
- `WalkRefusalTests` holds every refusal the base raises, and the order it
  raises them in, to the base's own text.
- `TransactionKeyTests` covers the one rule a single pass cannot settle: a
  transaction hash repeated at a second position, and keys that collide
  without one.
- `OpeningLogTests` covers each venue's opening-log declaration, the epochs
  and gaps derived from those logs alone, and the 1,048,576-log limit.

No case opens a socket. Only the base read starts a child process: `git`,
with a fixed argv and no shell.
"""

from contextlib import redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import types
import unittest
from unittest import mock

from tests import test_epoch_positions as positions
from tests import test_interval as epoch_fixture
from tests import test_usdc_interval as existing
from tests import test_wildcat_venue as wildcat
from alexandria_lib import interval, log_walk, venues, wildcat_registry
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.interval import OPENING_CLASS, UPGRADED_TOPIC
from alexandria_lib.log_walk import LogWalk
from alexandria_lib.venues import compound_v3, wildcat_v1, wildcat_v2
import usdc_interval
from usdc_interval import Builder, Collector, Reconciler

BASE = "150943da240837040478a76c3611d150fa04f2b6"
BASE_INTERVAL = "plugins/alexandria/scripts/alexandria_lib/interval.py"
PRESERVED = {
    "wildcat-v1": "ALEXANDRIA_WILDCAT_V1_RELEASE",
    "wildcat-v2": "ALEXANDRIA_WILDCAT_V2_RELEASE",
}


def repository_root() -> Path:
    """The checkout holding this module, found by its marketplace manifest rather than by depth."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (
            (candidate / ".claude-plugin" / "marketplace.json").is_file()
            and (candidate / "plugins" / "alexandria" / "tests" / here.name).is_file()
        ):
            return candidate
    raise AssertionError(
        f"no directory above {here} holds both .claude-plugin/marketplace.json and this module"
    )


_BASE_MODULE = []


def base_interval():
    """The base commit's `interval.py`, run as a module of this package, read once."""
    if _BASE_MODULE:
        return _BASE_MODULE[0]
    home = tempfile.mkdtemp(prefix="alexandria-log-walk-git-")
    try:
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith("GIT_")}
        environment.update(HOME=home, XDG_CONFIG_HOME=home, GIT_CONFIG_NOSYSTEM="1",
                           GIT_CONFIG_GLOBAL=os.devnull, LC_ALL="C")
        result = subprocess.run(  # phylax: allow subprocess: fixed git argv reading the base commit's file, no shell
            ["git", "-c", "color.ui=never", "-C", str(repository_root()), "show",
             "--no-textconv", f"{BASE}:{BASE_INTERVAL}"],
            capture_output=True, timeout=120, env=environment, check=False,
        )
    finally:
        shutil.rmtree(home, ignore_errors=True)
    if result.returncode != 0:
        raise AssertionError(
            f"git could not read {BASE_INTERVAL} at the base commit {BASE}: "
            + result.stderr.decode("utf-8", "replace").strip()[:300]
        )
    module = types.ModuleType("alexandria_lib._interval_at_base")
    module.__package__ = "alexandria_lib"
    module.__file__ = f"{BASE}:{BASE_INTERVAL}"
    exec(compile(result.stdout, module.__file__, "exec"), module.__dict__)  # phylax: allow exec: the base commit's own interval.py, read from git, compared as the reference derivation
    _BASE_MODULE.append(module)
    return module


# -- releases ------------------------------------------------------------------

class Release:
    """What a built release gives the walk: its plan, logs by shard, epochs and opening reads."""

    def __init__(self, root: Path) -> None:
        manifest = json.loads((root / "manifest.json").read_bytes())
        paths = {item["name"]: root / item["object_path"] for item in manifest["components"]}

        def load(name):
            return json.loads(paths[name].read_bytes())

        self.release_id = manifest["release_id"]
        self.plan = load("interval-plan")
        self.receipt = load("epoch-table")
        self.registry = load("registry")
        self.entries = load(OPENING_CLASS)["records"]
        classes = usdc_interval.declared_classes(self.plan)
        self.batches = []
        for name, part in usdc_interval.journal_components(self.plan, classes).items():
            if part["class"] != "logs":
                continue
            for record in load(name)["records"]:
                result = json.loads(record["response"]).get("result")
                self.batches.append(result if isinstance(result, list) else [])
        self.logs = [record for batch in self.batches for record in batch]
        self.subjects = usdc_interval._plan_subjects(self.plan)
        self.interval = self.plan["interval"]
        self.epochs = (
            interval.subject_epoch_table(self.receipt["epochs"]) if "subjects" in self.plan
            else self.receipt["epochs"]
        )
        self.venue = usdc_interval.plan_venue(self.plan)
        self.upgrade_topic = (
            UPGRADED_TOPIC if self.venue.EPOCH_MODEL == usdc_interval.EIP1967_MODEL else None
        )
        self.end_hash = self.receipt["shards"][-1]["end_hash"]


def _compound(root: Path, name: str, edit=None) -> Path:
    state = existing.fixture()
    if edit is not None:
        edit(state)
    staging, output = root / f"{name}-staging", root / name
    staging.mkdir()
    Collector(state["plan"], staging, existing.FixtureTransport(state)).collect()
    Reconciler(
        state["plan"], staging, existing.FixtureTransport(state),
        "second archive endpoint, class only",
    ).reconcile()
    Builder(state["plan"], staging, existing.registry(), created_at=existing.CREATED_AT).build(output)
    return output


def _around_the_upgrade(state) -> None:
    """Ordinary logs before and after the upgrade in its own block, as `test_epoch_positions` builds."""
    upgrade = state["logs"]["2"][0]
    upgrade["transactionIndex"], upgrade["logIndex"] = "0x2", "0x4"
    before = deepcopy(upgrade)
    before.update(topics=["0x" + "aa" * 32], transactionIndex="0x1", logIndex="0x3",
                  transactionHash="0x" + "01" * 32)
    after = deepcopy(before)
    after.update(transactionIndex="0x3", logIndex="0x5", transactionHash="0x" + "02" * 32)
    state["logs"]["2"][0:1] = [before, upgrade, after]


def _wildcat(root: Path, venue: str) -> Path:
    state = wildcat.fixture(venue)
    registry = wildcat.registry() if venue == wildcat_v2.VENUE else wildcat.v1_registry()
    staging, output = root / f"{venue}-staging", root / venue
    staging.mkdir()
    Collector(state["plan"], staging, wildcat.WildcatTransport(state), registry=registry).collect()
    Reconciler(
        state["plan"], staging, wildcat.WildcatTransport(state), wildcat.SECOND_PROVIDER,
        registry=registry,
    ).reconcile()
    Builder(state["plan"], staging, registry, created_at=wildcat.CREATED_AT).build(output)
    return output


_CONSTRUCTED = {}


def constructed() -> dict:
    """The four constructed releases, built once per module run."""
    if not _CONSTRUCTED:
        directory = tempfile.TemporaryDirectory(prefix="alexandria-log-walk-")
        unittest.addModuleCleanup(directory.cleanup)
        root = Path(directory.name)
        with redirect_stderr(io.StringIO()):
            _CONSTRUCTED.update({
                "compound": Release(_compound(root, "compound")),
                "compound-around-upgrade": Release(_compound(root, "around", _around_the_upgrade)),
                "wildcat-v1": Release(_wildcat(root, wildcat_v1.VENUE)),
                "wildcat-v2": Release(_wildcat(root, wildcat_v2.VENUE)),
            })
    return _CONSTRUCTED


def preserved(case: unittest.TestCase, venue: str) -> Release:
    variable = PRESERVED[venue]
    value = os.environ.get(variable)
    if not value:
        case.skipTest(f"{variable} is not set; it names the preserved {venue} release")
    return Release(Path(value))


def walked(release, *, epochs=None, opening_topics=()):
    """Feed a release's logs one shard at a time; return the walk and its rows."""
    walk = LogWalk(release.subjects, release.interval, upgrade_topic=release.upgrade_topic,
                   epochs=epochs, opening_topics=opening_topics)
    rows = []
    for batch in release.batches:
        rows.extend(walk.feed(batch))
    walk.finish(lambda: release.batches)
    return walk, rows


# -- WalkEquivalenceTests ------------------------------------------------------

class WalkEquivalenceTests(unittest.TestCase):
    """The walk and both wrappers derive the base commit's rows, in its order."""

    def assert_equivalent(self, release):
        base = base_interval()
        expected = base.proxy_log_positions(
            release.logs, release.subjects, release.interval, upgrade_topic=release.upgrade_topic,
        )
        self.assertEqual(interval.proxy_log_positions(
            release.logs, release.subjects, release.interval, upgrade_topic=release.upgrade_topic,
        ), expected)
        self.assertEqual(walked(release)[1], expected)
        attributed = base.attribute_logs(
            release.logs, release.subjects, release.interval, release.epochs,
            upgrade_topic=release.upgrade_topic,
        )
        self.assertEqual(interval.attribute_logs(
            release.logs, release.subjects, release.interval, release.epochs,
            upgrade_topic=release.upgrade_topic,
        ), attributed)
        self.assertEqual(walked(release, epochs=release.epochs)[1], attributed)
        # Byte for byte, as a receipt or part would carry the rows.
        self.assertEqual(json.dumps(walked(release, epochs=release.epochs)[1]),
                         json.dumps(attributed))
        return attributed

    def test_the_base_module_is_the_base_commits_file_and_not_the_working_one(self):
        base = base_interval()
        self.assertEqual(base.__file__, f"{BASE}:{BASE_INTERVAL}")
        self.assertNotEqual(base.proxy_log_positions.__code__.co_code,
                            interval.proxy_log_positions.__code__.co_code)
        self.assertIs(base.AlexandriaError, AlexandriaError)

    def test_the_constructed_compound_release(self):
        release = constructed()["compound"]
        rows = self.assert_equivalent(release)
        self.assertIn("upgrade-boundary", {row["kind"] for row in rows})

    def test_the_constructed_compound_release_with_logs_around_its_upgrade(self):
        release = constructed()["compound-around-upgrade"]
        rows = self.assert_equivalent(release)
        indexes = {row["transaction_hash"]: row["epoch_index"] for row in rows}
        self.assertEqual((indexes["0x" + "01" * 32], indexes["0x" + "02" * 32]), (0, 1))

    def test_the_constructed_wildcat_v1_release(self):
        self.assert_equivalent(constructed()["wildcat-v1"])

    def test_the_constructed_wildcat_v2_release(self):
        rows = self.assert_equivalent(constructed()["wildcat-v2"])
        self.assertGreater(len({row["subject"] for row in rows}), 1)

    def test_the_rows_match_the_receipt_the_build_wrote(self):
        for name in ("compound", "wildcat-v2"):
            with self.subTest(release=name):
                release = constructed()[name]
                self.assertEqual(walked(release, epochs=release.epochs)[1],
                                 release.receipt["log_attributions"])

    def test_the_epoch_fixture_logs(self):
        value, _block = positions.evidence()
        epochs = interval.discover_epochs(**value)
        base = base_interval()
        for function in ("proxy_log_positions", "attribute_logs"):
            with self.subTest(function=function):
                arguments = (value["upgrade_logs"], value["proxy"], value["interval"])
                if function == "attribute_logs":
                    arguments += (epochs,)
                self.assertEqual(getattr(interval, function)(*arguments),
                                 getattr(base, function)(*arguments))

    def test_the_preserved_wildcat_v1_release(self):
        release = preserved(self, "wildcat-v1")
        self.assertGreater(len(self.assert_equivalent(release)), 0)

    def test_the_preserved_wildcat_v2_release(self):
        release = preserved(self, "wildcat-v2")
        self.assertGreater(len(self.assert_equivalent(release)), 0)


# -- synthetic logs ------------------------------------------------------------

PROXY = "0x" + "11" * 20
OTHER = "0x" + "22" * 20
THIRD = "0x" + "33" * 20
ORDINARY = "0x" + "aa" * 32
INTERVAL = {"start": "100", "end": "200"}


def digest(*parts) -> str:
    return "0x" + hashlib.sha256(repr(parts).encode()).hexdigest()


def log(block, tx, index, *, address=PROXY, topics=None, tx_hash=None, block_hash=None):
    return {
        "address": address,
        "blockHash": block_hash or digest("block", block),
        "blockNumber": hex(block),
        "data": "0x",
        "logIndex": hex(index),
        "removed": False,
        "topics": [ORDINARY] if topics is None else topics,
        "transactionHash": tx_hash or digest("transaction", block, tx),
        "transactionIndex": hex(tx),
    }


def upgrade(block, tx, index, *, address=PROXY, implementation="44"):
    return log(block, tx, index, address=address,
               topics=[UPGRADED_TOPIC, "0x" + "00" * 12 + implementation * 20])


def refusal(function, *arguments, **keywords):
    try:
        function(*arguments, **keywords)
    except AlexandriaError as error:
        return str(error)
    return None


def streamed(records, subjects, interval_=INTERVAL, *, upgrade_topic=UPGRADED_TOPIC, epochs=None):
    """The walk's refusal with each log fed as its own shard, or None."""
    batches = [[record] for record in records]
    try:
        walk = LogWalk(subjects, interval_, upgrade_topic=upgrade_topic, epochs=epochs)
        for batch in batches:
            walk.feed(batch)
        walk.finish(lambda: batches)
    except AlexandriaError as error:
        return str(error)
    return None


class WalkRefusalTests(unittest.TestCase):
    """Every refusal the base raises, with the base's text, whole-list and streamed."""

    def assert_refuses_as_base(self, records, subjects=PROXY, *, contains, epochs=None,
                               upgrade_topic=UPGRADED_TOPIC, interval_=INTERVAL):
        base = base_interval()
        if epochs is None:
            expected = refusal(base.proxy_log_positions, records, subjects, interval_,
                               upgrade_topic=upgrade_topic)
            wrapped = refusal(interval.proxy_log_positions, records, subjects, interval_,
                              upgrade_topic=upgrade_topic)
        else:
            expected = refusal(base.attribute_logs, records, subjects, interval_, epochs,
                               upgrade_topic=upgrade_topic)
            wrapped = refusal(interval.attribute_logs, records, subjects, interval_, epochs,
                              upgrade_topic=upgrade_topic)
        self.assertIsNotNone(expected, "the base accepted a case meant to refuse")
        self.assertIn(contains, expected)
        self.assertEqual(wrapped, expected)
        self.assertEqual(streamed(records, subjects, interval_, upgrade_topic=upgrade_topic,
                                  epochs=epochs), expected)
        return expected

    def test_unordered_positions(self):
        self.assert_refuses_as_base([log(101, 0, 1), log(101, 0, 0)],
                                    contains="(101, 0, 0) is duplicated or unordered")
        self.assert_refuses_as_base([log(102, 0, 0), log(101, 5, 9)],
                                    contains="is duplicated or unordered")
        # A later transaction in the same block cannot restart the log index.
        self.assert_refuses_as_base([log(101, 0, 3), log(101, 1, 2)],
                                    contains="(101, 1, 2) is duplicated or unordered")

    def test_duplicated_positions(self):
        self.assert_refuses_as_base([log(101, 0, 0), log(101, 0, 0)],
                                    contains="(101, 0, 0) is duplicated or unordered")

    def test_contradictory_block_hash(self):
        self.assert_refuses_as_base(
            [log(101, 0, 0), log(101, 1, 1, block_hash=digest("another block"))],
            contains="proxy log block 101 has contradictory hashes",
        )

    def test_contradictory_transaction_pair_inside_one_position(self):
        self.assert_refuses_as_base(
            [log(101, 0, 0), log(101, 0, 1, tx_hash=digest("another transaction"))],
            contains="(101, 0, 1) has contradictory transaction hash/index pairs",
        )

    def test_one_transaction_hash_at_two_positions(self):
        shared = digest("shared")
        self.assert_refuses_as_base(
            [log(101, 0, 0, tx_hash=shared), log(102, 3, 0, tx_hash=shared)],
            contains="(102, 3, 0) has contradictory transaction hash/index pairs",
        )
        self.assert_refuses_as_base(
            [log(101, 0, 0, tx_hash=shared), log(101, 1, 1, tx_hash=shared)],
            contains="(101, 1, 1) has contradictory transaction hash/index pairs",
        )

    def test_ordinary_log_in_an_upgrade_transaction(self):
        self.assert_refuses_as_base(
            [upgrade(101, 0, 0), log(101, 0, 1)],
            contains="ordinary proxy log at (101, 0, 1) in an upgrade transaction is unsupported",
        )
        self.assert_refuses_as_base(
            [log(101, 0, 0), upgrade(101, 0, 1)],
            contains="ordinary proxy log at (101, 0, 0) in an upgrade transaction is unsupported",
        )
        # The first such log in the list, across two upgrade transactions.
        self.assert_refuses_as_base(
            [upgrade(101, 0, 0), log(101, 0, 1), log(101, 0, 2), upgrade(150, 0, 0), log(150, 0, 1)],
            contains="ordinary proxy log at (101, 0, 1)",
        )

    def test_another_subjects_log_beside_an_upgrade_is_its_own(self):
        records = [upgrade(101, 0, 0), log(101, 0, 1, address=OTHER)]
        self.assertEqual(interval.proxy_log_positions(records, [PROXY, OTHER], INTERVAL),
                         base_interval().proxy_log_positions(records, [PROXY, OTHER], INTERVAL))

    def test_upgrade_rules(self):
        self.assert_refuses_as_base([upgrade(100, 0, 0)],
                                    contains="first-block upgrade at (100, 0, 0)")
        self.assert_refuses_as_base([upgrade(101, 0, 0), upgrade(101, 1, 1)],
                                    contains="multiple upgrades in block 101 are unsupported")
        malformed = upgrade(101, 0, 0)
        malformed["topics"] = [UPGRADED_TOPIC]
        self.assert_refuses_as_base([log(100, 0, 0), malformed],
                                    contains="upgrade log 1 does not carry two topics")

    def test_log_outside_the_interval(self):
        self.assert_refuses_as_base([log(99, 0, 0)], contains="proxy log block 99 is outside the interval")
        self.assert_refuses_as_base([log(150, 0, 0), log(201, 0, 0)],
                                    contains="proxy log block 201 is outside the interval")

    def test_undeclared_emitter(self):
        self.assert_refuses_as_base([log(101, 0, 0, address=OTHER)],
                                    contains="a preserved log was not emitted by the proxy")
        self.assert_refuses_as_base([log(101, 0, 0, address=THIRD)], [PROXY, OTHER],
                                    contains="a preserved log was not emitted by a declared subject")
        self.assert_refuses_as_base([log(101, 0, 0), "not a log"],
                                    contains="a preserved log was not emitted by the proxy")
        self.assert_refuses_as_base([log(101, 0, 0, address="0x12")],
                                    contains="log emitting contract is not a 20-byte address")

    def test_malformed_topics(self):
        for topics in ("0x" + "aa" * 32, [ORDINARY.upper().replace("0X", "0x")], [1], ["0x12"]):
            with self.subTest(topics=topics):
                self.assert_refuses_as_base([log(101, 0, 0, topics=topics)],
                                            contains="(101, 0, 0) has malformed topics")

    def test_malformed_positions_and_hashes(self):
        cases = (
            ({"blockNumber": "0x065"}, "blockNumber is not a canonical non-negative quantity"),
            ({"transactionIndex": 1}, "transactionIndex is not a canonical non-negative quantity"),
            ({"logIndex": "0x" + "f" * interval.MAX_POSITION_QUANTITY_LENGTH},
             "logIndex exceeds the canonical integer limit"),
            ({"blockHash": "0x12"}, "proxy log block hash is not a 32-byte hash"),
            ({"transactionHash": None}, "proxy log transaction hash is not a 32-byte hash"),
        )
        for change, text in cases:
            with self.subTest(change=change):
                record = log(101, 0, 0)
                record.update(change)
                self.assert_refuses_as_base([record], contains=text)

    def test_inputs_refuse_before_any_log(self):
        self.assert_refuses_as_base([log(101, 0, 0)], [], contains="non-empty collection")
        self.assert_refuses_as_base([log(101, 0, 0)], [PROXY, PROXY], contains="is duplicated")
        self.assert_refuses_as_base([log(101, 0, 0)], interval_={"start": "100"},
                                    contains="position interval has an unknown shape")
        self.assert_refuses_as_base([log(101, 0, 0)], interval_={"start": "0100", "end": "200"},
                                    contains="position interval start is not a decimal block number")
        base = base_interval()
        self.assertEqual(refusal(interval.proxy_log_positions, {"not": "a list"}, PROXY, INTERVAL),
                         refusal(base.proxy_log_positions, {"not": "a list"}, PROXY, INTERVAL))
        # Logs that are not a list are refused before the interval's values are read.
        unbounded = {"start": "1" * 20, "end": "200"}
        expected = refusal(base.proxy_log_positions, {"not": "a list"}, PROXY, unbounded)
        self.assertEqual(expected, "proxy logs are not a list")
        self.assertEqual(refusal(interval.proxy_log_positions, {"not": "a list"}, PROXY, unbounded),
                         expected)

    def test_the_first_refusal_in_list_order_wins(self):
        shared = digest("shared")
        # A hash repeated at a second position, before a later malformed log.
        self.assert_refuses_as_base(
            [log(101, 0, 0, tx_hash=shared), log(102, 0, 0, tx_hash=shared), log(103, 0, 0, topics="x")],
            contains="(102, 0, 0) has contradictory transaction hash/index pairs",
        )
        # The same log repeats the hash and carries malformed topics: the hash rule comes first.
        self.assert_refuses_as_base(
            [log(101, 0, 0, tx_hash=shared), log(102, 0, 0, tx_hash=shared, topics="x")],
            contains="(102, 0, 0) has contradictory transaction hash/index pairs",
        )
        # A malformed log before the repeat stops the list there.
        self.assert_refuses_as_base(
            [log(101, 0, 0, tx_hash=shared), log(101, 1, 1, topics="x"), log(102, 0, 0, tx_hash=shared)],
            contains="(101, 1, 1) has malformed topics",
        )
        # An ordering refusal at the repeating log itself comes before the hash rule.
        self.assert_refuses_as_base(
            [log(102, 0, 0, tx_hash=shared), log(101, 0, 0, tx_hash=shared)],
            contains="(101, 0, 0) is duplicated or unordered",
        )
        # An ordinary log in an upgrade transaction yields to any later in-list refusal.
        self.assert_refuses_as_base(
            [upgrade(101, 0, 0), log(101, 0, 1), log(150, 0, 0), log(149, 0, 0)],
            contains="(149, 0, 0) is duplicated or unordered",
        )

    def subject_epochs(self):
        return wildcat_v2.derive_epochs(
            chain="eip155:1", deployment="constructed", interval=INTERVAL,
            first_blocks={PROXY: 100, OTHER: 150},
            code_reads={PROXY: "0x6001", OTHER: "0x6002"},
            block_hashes={100: digest("block", 100), 150: digest("block", 150),
                          200: digest("block", 200)},
        )

    def test_attribution_refusals(self):
        epochs = self.subject_epochs()
        subjects = [PROXY, OTHER, THIRD]
        self.assert_refuses_as_base([log(140, 0, 0, address=OTHER)], subjects, epochs=epochs,
                                    upgrade_topic=None, contains="has no positional epoch owner")
        self.assert_refuses_as_base([log(140, 0, 0, address=THIRD)], subjects, epochs=epochs,
                                    upgrade_topic=None, contains="has no positional epoch owner")
        self.assert_refuses_as_base(
            [log(200, 0, 0, block_hash=digest("not the end"))], subjects, epochs=epochs,
            upgrade_topic=None, contains="proxy log hash contradicts its epoch boundary",
        )
        single = interval.discover_epochs(**epoch_fixture.epoch_evidence())
        start = int(single[0]["start_block"])
        record = log(start, 0, 0, address=epoch_fixture.epoch_evidence()["proxy"],
                     block_hash=digest("not the first block"))
        self.assert_refuses_as_base(
            [record], epoch_fixture.epoch_evidence()["proxy"], epochs=single,
            interval_=epoch_fixture.epoch_evidence()["interval"],
            contains="proxy log hash contradicts its epoch boundary",
        )

    def test_the_subject_whose_logs_appear_first_refuses_first(self):
        epochs = self.subject_epochs()
        subjects = [PROXY, OTHER]
        late_contradiction = log(200, 0, 0, block_hash=digest("not the end"))
        early_orphan = log(140, 0, 0, address=OTHER)
        # PROXY appears first, so its late contradiction wins over OTHER's earlier orphan.
        self.assert_refuses_as_base(
            [log(101, 0, 0), early_orphan, late_contradiction], subjects, epochs=epochs,
            upgrade_topic=None, contains="hash contradicts its epoch boundary",
        )
        # OTHER appears first, so its orphan wins.
        self.assert_refuses_as_base(
            [early_orphan, late_contradiction], subjects, epochs=epochs,
            upgrade_topic=None, contains="has no positional epoch owner",
        )
        # A position refusal anywhere comes before any ownership refusal.
        self.assert_refuses_as_base(
            [early_orphan, log(160, 0, 0, topics="x")], subjects, epochs=epochs,
            upgrade_topic=None, contains="(160, 0, 0) has malformed topics",
        )

    def test_epoch_tables_refuse_before_any_log(self):
        epochs = self.subject_epochs()
        self.assert_refuses_as_base([log(101, 0, 0)], PROXY, epochs=epochs,
                                    contains="a single subject requires a flat epoch list")
        self.assert_refuses_as_base([log(101, 0, 0)], [PROXY], epochs=epochs, upgrade_topic=None,
                                    contains="epoch table names an undeclared subject")
        self.assert_refuses_as_base([log(101, 0, 0)], [PROXY, OTHER], epochs={}, upgrade_topic=None,
                                    contains="epoch table names no subject")

    def test_rows_from_a_refused_walk_are_never_returned(self):
        records = [log(101, 0, 0), log(101, 0, 0)]
        walk = LogWalk(PROXY, INTERVAL)
        self.assertEqual(len(walk.feed(records)), 1)
        # Once a refusal is held, later shards are not read.
        self.assertEqual(walk.feed([log(150, 0, 0)]), [])
        with self.assertRaisesRegex(AlexandriaError, "duplicated or unordered"):
            walk.finish(lambda: [records])
        with self.assertRaisesRegex(AlexandriaError, "already finished"):
            walk.feed([log(160, 0, 0)])


# -- TransactionKeyTests -------------------------------------------------------

class TransactionKeyTests(unittest.TestCase):
    """One 8-byte key per transaction; a repeated key costs one read and nothing else."""

    def walk_of(self, records, batches=None):
        batches = batches or [[record] for record in records]
        reads = []

        def reread():
            reads.append(1)
            return batches

        walk = LogWalk(PROXY, INTERVAL)
        rows = []
        for batch in batches:
            rows.extend(walk.feed(batch))
        return walk, rows, reread, reads

    def test_one_key_of_eight_bytes_per_distinct_transaction(self):
        records = [log(101, 0, 0), log(101, 0, 1), log(101, 1, 2), log(102, 0, 0), log(102, 0, 1)]
        walk, _rows, reread, reads = self.walk_of(records)
        self.assertEqual(len(walk._buckets), 256)
        self.assertEqual({bucket.typecode for bucket in walk._buckets}, {"Q"})
        self.assertEqual({bucket.itemsize for bucket in walk._buckets}, {8})
        self.assertEqual(sum(len(bucket) for bucket in walk._buckets), 3)
        walk.finish(reread)
        self.assertEqual((reads, walk.rereads), ([], 0))

    def test_a_hash_repeated_across_blocks_refuses_after_one_more_read(self):
        shared = digest("shared")
        records = [log(101, 0, 0, tx_hash=shared), log(120, 0, 0), log(150, 2, 0, tx_hash=shared),
                   log(160, 0, 0)]
        walk, _rows, reread, reads = self.walk_of(records)
        expected = refusal(base_interval().proxy_log_positions, records, PROXY, INTERVAL)
        self.assertEqual(expected, "proxy log position (150, 2, 0) has contradictory "
                                   "transaction hash/index pairs")
        with self.assertRaises(AlexandriaError) as raised:
            walk.finish(reread)
        self.assertEqual(str(raised.exception), expected)
        self.assertEqual((reads, walk.rereads), ([1], 1))

    def test_a_forced_key_collision_refuses_nothing(self):
        prefix = "0x" + "ab" * 8
        records = [log(101, 0, 0, tx_hash=prefix + "01" * 24), log(102, 0, 0, tx_hash=prefix + "02" * 24),
                   log(103, 0, 0, tx_hash=prefix + "01" * 23 + "02")]
        walk, rows, reread, reads = self.walk_of(records)
        walk.finish(reread)
        self.assertEqual(rows, base_interval().proxy_log_positions(records, PROXY, INTERVAL))
        self.assertEqual((reads, walk.rereads), ([1], 1))

    def test_truncated_keys_collide_everywhere_and_refuse_nothing(self):
        records = [log(101 + index // 4, index % 4, index % 4) for index in range(400)]
        with mock.patch.object(log_walk, "KEY_BYTES", 1):
            walk, rows, reread, reads = self.walk_of(records, [records[:150], records[150:]])
            walk.finish(reread)
            self.assertEqual(rows, base_interval().proxy_log_positions(records, PROXY, INTERVAL))
            self.assertEqual((reads, walk.rereads), ([1], 1))
            for name, release in constructed().items():
                with self.subTest(release=name):
                    self.assertEqual(
                        walked(release, epochs=release.epochs)[1],
                        base_interval().attribute_logs(
                            release.logs, release.subjects, release.interval, release.epochs,
                            upgrade_topic=release.upgrade_topic,
                        ),
                    )

    def test_a_truncated_key_still_finds_the_real_repeat(self):
        shared = digest("shared")
        records = [log(101 + index, 0, 0) for index in range(40)]
        records.insert(10, log(110, 1, 1, tx_hash=shared))
        records.insert(30, log(129, 1, 1, tx_hash=shared))
        expected = refusal(base_interval().proxy_log_positions, records, PROXY, INTERVAL)
        self.assertIn("(129, 1, 1) has contradictory", expected)
        with mock.patch.object(log_walk, "KEY_BYTES", 1):
            self.assertEqual(streamed(records, PROXY), expected)

    def test_a_second_read_that_differs_from_the_first_refuses(self):
        prefix = "0x" + "cd" * 8
        records = [log(101, 0, 0, tx_hash=prefix + "01" * 24), log(102, 0, 0, tx_hash=prefix + "02" * 24)]
        changed = deepcopy(records)
        changed[1]["transactionHash"] = prefix + "03" * 24
        for second in ([changed], [records[:1]], [[records[0], "not a log"]], ["not a shard"]):
            with self.subTest(second=second):
                walk, _rows, _reread, _reads = self.walk_of(records)
                with self.assertRaisesRegex(AlexandriaError, "second read of the preserved logs does not match"):
                    walk.finish(lambda second=second: second)

    def test_a_repeated_key_with_no_second_read_refuses(self):
        prefix = "0x" + "ef" * 8
        records = [log(101, 0, 0, tx_hash=prefix + "01" * 24), log(102, 0, 0, tx_hash=prefix + "02" * 24)]
        walk, _rows, _reread, _reads = self.walk_of(records)
        with self.assertRaisesRegex(AlexandriaError, "given no second read"):
            walk.finish()

    def test_the_first_of_two_repeated_hashes_is_the_one_named(self):
        first, second = digest("first shared"), digest("second shared")
        records = [log(101, 0, 0, tx_hash=first), log(102, 0, 0, tx_hash=second),
                   log(105, 0, 0, tx_hash=first), log(110, 0, 0, tx_hash=second)]
        expected = refusal(base_interval().proxy_log_positions, records, PROXY, INTERVAL)
        self.assertEqual(expected, "proxy log position (105, 0, 0) has contradictory "
                                   "transaction hash/index pairs")
        for width in (8, 1):
            with self.subTest(key_bytes=width), mock.patch.object(log_walk, "KEY_BYTES", width):
                self.assertEqual(streamed(records, PROXY), expected)

    def several_logs_a_transaction(self):
        """Forty transactions of three logs each, so a second read meets repeated positions."""
        return [log(101 + index // 4, index % 4, 3 * (index % 4) + offset)
                for index in range(40) for offset in range(3)]

    def test_truncated_keys_over_transactions_with_several_logs(self):
        records = self.several_logs_a_transaction()
        with mock.patch.object(log_walk, "KEY_BYTES", 1):
            walk, rows, reread, reads = self.walk_of(records, [records[:50], records[50:]])
            walk.finish(reread)
        self.assertEqual(rows, base_interval().proxy_log_positions(records, PROXY, INTERVAL))
        self.assertEqual((reads, walk.rereads), ([1], 1))
        # A real repeat among them is named at the first log of the repeating transaction.
        shared = records[0]["transactionHash"]
        repeated = deepcopy(records)
        for record in repeated[60:63]:
            record["transactionHash"] = shared
        expected = refusal(base_interval().proxy_log_positions, repeated, PROXY, INTERVAL)
        self.assertEqual(expected, "proxy log position (106, 0, 0) has contradictory "
                                   "transaction hash/index pairs")
        with mock.patch.object(log_walk, "KEY_BYTES", 1):
            self.assertEqual(streamed(repeated, PROXY), expected)

    def test_a_second_read_short_of_the_last_log_refuses(self):
        records = self.several_logs_a_transaction()
        with mock.patch.object(log_walk, "KEY_BYTES", 1):
            walk, _rows, _reread, _reads = self.walk_of(records, [records])
            with self.assertRaisesRegex(AlexandriaError, "second read of the preserved logs does not match"):
                walk.finish(lambda: [records[:-1]])

    def test_the_preserved_releases_under_truncated_keys(self):
        for venue in PRESERVED:
            with self.subTest(venue=venue):
                release = preserved(self, venue)
                expected = base_interval().attribute_logs(
                    release.logs, release.subjects, release.interval, release.epochs,
                    upgrade_topic=release.upgrade_topic,
                )
                with mock.patch.object(log_walk, "KEY_BYTES", 1):
                    walk, rows = walked(release, epochs=release.epochs)
                self.assertEqual(walk.rereads, 1)
                self.assertEqual(rows, expected)


# -- OpeningLogTests -----------------------------------------------------------

def replayed(release, logs):
    """The opening phase a release's own opening reads give, built from `logs`."""
    phase = usdc_interval.opening_phase(release.plan, logs, registry=release.registry)
    for position, read in enumerate(phase.reads()):
        entry = release.entries[position]
        assert entry["request"].encode() == usdc_interval.opening_request(release.plan, position, read)
        phase.accept(read, usdc_interval.opening_result(
            release.plan, position, entry["response"], f"opening read {position}",
        ))
    return phase


class OpeningLogTests(unittest.TestCase):
    """Each venue's opening logs, and what its opening phase and gaps derive from them alone."""

    def test_each_venue_declares_its_opening_logs(self):
        self.assertEqual(venues.OPENING_TOPICS, {
            compound_v3.VENUE: (UPGRADED_TOPIC,),
            wildcat_v1.VENUE: (),
            wildcat_v2.VENUE: (wildcat_v2.MARKET_DEPLOYED_TOPIC,),
        })
        self.assertEqual(set(venues.OPENING_TOPICS), set(venues.VENUES))
        for name in venues.VENUES:
            self.assertEqual(venues.opening_topics(name), venues.OPENING_TOPICS[name])
        with self.assertRaisesRegex(AlexandriaError, "declares no opening logs"):
            venues.opening_topics("aave-v4")

    def test_the_limit_is_every_subject_epoch(self):
        self.assertEqual(log_walk.MAX_OPENING_LOGS, 1_048_576)
        self.assertEqual(log_walk.MAX_OPENING_LOGS, interval.MAX_SUBJECTS * interval.MAX_EPOCHS)

    def opening(self, release):
        walk, _rows = walked(release, epochs=release.epochs,
                             opening_topics=venues.opening_topics(release.plan["venue"]))
        return venues.opening_logs(walk)

    def test_a_walk_keeps_only_the_declared_logs(self):
        for name, release in constructed().items():
            with self.subTest(release=name):
                topics = venues.opening_topics(release.plan["venue"])
                expected = [record for record in release.logs if record["topics"]
                            and record["topics"][0] in topics]
                self.assertEqual(self.opening(release), expected)
                if name.startswith("compound"):
                    self.assertTrue(expected)
                    self.assertLess(len(expected), len(release.logs))
                if name == "wildcat-v1":
                    self.assertEqual(expected, [])
                if name == "wildcat-v2":
                    self.assertTrue(expected)

    def assert_opening_alone_gives_todays_results(self, release):
        opening = self.opening(release)
        whole, alone = replayed(release, release.logs), replayed(release, opening)
        epochs = usdc_interval.epochs_from_opening(release.plan, whole, release.end_hash)
        self.assertEqual(usdc_interval.epochs_from_opening(release.plan, alone, release.end_hash), epochs)
        self.assertEqual(epochs, release.epochs)
        first_code = None
        if "subjects" in release.plan:
            first_code = whole.first_code_rows()
            self.assertEqual(alone.first_code_rows(), first_code)
        self.assertEqual(
            release.venue.evidence_gaps(release.plan, release.registry, opening, first_code),
            release.venue.evidence_gaps(release.plan, release.registry, release.logs, first_code),
        )
        return epochs

    def test_todays_epochs_and_gaps_from_the_opening_logs_alone(self):
        for name, release in constructed().items():
            with self.subTest(release=name):
                self.assert_opening_alone_gives_todays_results(release)

    def test_the_market_deploy_report_from_the_opening_logs_alone(self):
        release = constructed()["wildcat-v2"]
        report = wildcat_v2.market_deploy_report(release.plan, release.registry, self.opening(release))
        self.assertEqual(report, wildcat_v2.market_deploy_report(
            release.plan, release.registry, release.logs))
        self.assertTrue(report["compared"])
        self.assertTrue(report["observed"])

    def test_discover_epochs_from_the_upgrade_announcements_alone(self):
        value, _block = positions.evidence()
        whole = interval.discover_epochs(**value)
        announcements = dict(value, upgrade_logs=[
            record for record in value["upgrade_logs"] if record["topics"][0] == UPGRADED_TOPIC
        ])
        self.assertLess(len(announcements["upgrade_logs"]), len(value["upgrade_logs"]))
        self.assertEqual(interval.discover_epochs(**announcements), whole)
        self.assertEqual(base_interval().discover_epochs(**value), whole)

    def test_the_preserved_releases_from_their_opening_logs_alone(self):
        for venue in PRESERVED:
            with self.subTest(venue=venue):
                release = preserved(self, venue)
                with wildcat_registry.checking_release():
                    self.assert_opening_alone_gives_todays_results(release)

    def test_a_count_above_the_limit_refuses_by_name(self):
        records = [log(101 + index, 0, 0) for index in range(3)]
        for limit, refused in ((3, False), (2, True)):
            with self.subTest(limit=limit), mock.patch.object(log_walk, "MAX_OPENING_LOGS", limit):
                walk = LogWalk(PROXY, INTERVAL, opening_topics=(ORDINARY,))
                walk.feed(records)
                walk.finish()
                self.assertLessEqual(len(walk.opening), limit)
                if refused:
                    with self.assertRaisesRegex(
                        AlexandriaError,
                        "hold 3 opening logs, above the 2-log opening-log limit",
                    ):
                        venues.opening_logs(walk)
                else:
                    self.assertEqual(venues.opening_logs(walk), records)

    def test_an_unfinished_walk_has_no_opening_logs(self):
        walk = LogWalk(PROXY, INTERVAL, opening_topics=(ORDINARY,))
        walk.feed([log(101, 0, 0)])
        with self.assertRaisesRegex(AlexandriaError, "has not finished"):
            venues.opening_logs(walk)


if __name__ == "__main__":
    unittest.main()
