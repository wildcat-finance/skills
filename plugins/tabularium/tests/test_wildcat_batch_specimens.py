"""Hold the constructed batch specimens to source order, rebuilt bytes and named gaps."""

from collections import Counter
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "scripts"))
from tabularium_lib import verifier
from tabularium_lib.core import TabulariumError
from tabularium_lib.keccak import keccak256
from tabularium_lib.wildcat_rules import BURN_JOIN_RULE
from tabularium_lib.wildcat_source import CONSTRUCTION_GAP
from wildcat_batch_fixtures import (
    BATCH_SIGNATURES, CLOSED, CREATED, EXPIRED, MARKET_CLOSED, PAYMENT, QUEUED, REPAID, TRANSFER,
)
from wildcat_batch_public_fixtures import (
    HOSTILE_ORDER, ROOT, VENUES, build_specimen, example_directory, rebuild_example, release_id,
    specimen_names, specimen_raws,
)
from wildcat_v3_fixtures import ACCOUNT, BATCH_ACTIONS, MARKET, OTHER, PAYER, ZERO, word

BURN_GAP = "attribution:withdrawal-batch-payment:burn"
UNCLAIMED_GAP = "attribution:transfer:unclaimed-burn"
BATCH_RULES = tuple("withdrawal-batch-" + name for name in ("created", "payment", "expired", "closed"))
SYNTHETIC_ADDRESSES = {MARKET, ACCOUNT, PAYER, OTHER, ZERO}
# Indexed topic positions that carry an address; the others carry an expiry.
ADDRESS_TOPICS = {TRANSFER: (1, 2), QUEUED: (2,), REPAID: (1,)}
SIGNATURES = {"0x" + keccak256(signature.encode()).hex(): signature
              for signature in (CREATED, PAYMENT, EXPIRED, CLOSED, TRANSFER, QUEUED, REPAID, MARKET_CLOSED)}
# Named gaps each hostile transaction leaves; a source-order transaction leaves none.
HOSTILE_GAPS = {
    "burn-after-payment": {BURN_GAP: 1, UNCLAIMED_GAP: 1},
    "burn-value-changed": {BURN_GAP: 1, UNCLAIMED_GAP: 1},
    "burn-without-payment": {UNCLAIMED_GAP: 1},
    "two-burns-one-payment": {UNCLAIMED_GAP: 1},
    "payment-without-burn": {BURN_GAP: 1},
}
EXPECTED = {
    "wildcat-v1": {"rows": 33, "transactions": 9, "payments": 10, "joined": 7},
    "wildcat-v2": {"rows": 39, "transactions": 10, "payments": 11, "joined": 8},
}


def _public(venue):
    return example_directory(venue) / ROOT


def _document(root, name):
    return json.loads((root / name).read_bytes())


def _rows(root):
    return [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]


def _file_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def _committed_logs(root):
    """The raw logs as the copied Alexandria journal holds them, in journal order."""
    raw = root / "source/raw-release"
    manifest = _document(raw, "manifest.json")
    component = next(item for item in manifest["components"] if item["name"] == "native-logs")
    journal = _document(raw, component["object_path"])
    (entry,) = journal["records"]
    return json.loads(entry["response"])["result"]


def _transaction_hash(venue, name):
    position = specimen_names(venue).index(name)
    return "0x" + ("%02x" % (0xb0 + position)) * 32


def _transaction_logs(venue, name):
    return [raw for raw in _committed_logs(_public(venue)) if raw["transactionHash"] == _transaction_hash(venue, name)]


def _signatures(logs):
    return [SIGNATURES[raw["topics"][0]] for raw in logs]


def _mappings(root):
    return {m["source_selector"]: m for m in _document(root, "source.json")["mapping_records"]}


def _dispositions(root):
    return {d["source_selector"]: d for d in _document(root, "source.json")["dispositions"]}


def _payments(root):
    return [row for row in _rows(root) if row["action"].endswith(".withdrawal-batch-payment")]


def _by_selector(root):
    return {row["provenance"]["source_selector"]: row for row in _rows(root)}


class BatchSpecimenTests(unittest.TestCase):
    """Source order, byte-exact rebuild, constructed qualification, joins and gaps."""

    def test_v1_queue_path_emits_the_queue_transfer_before_the_created_batch(self):
        logs = _transaction_logs("wildcat-v1", "v1-queue-first-batch")
        self.assertEqual(_signatures(logs), [TRANSFER, CREATED, QUEUED, TRANSFER, PAYMENT])
        self.assertEqual(logs[0]["topics"][1:], ["0x" + word(ACCOUNT), "0x" + word(MARKET)])
        self.assertEqual(logs[3]["topics"][1:], ["0x" + word(MARKET), "0x" + word(ZERO)])
        self.assertEqual([int(raw["logIndex"], 16) for raw in logs], [0, 1, 2, 3, 4])
        self.assertEqual([row["action"].split(".", 1)[1] for row in _rows(_public("wildcat-v1"))[:5]],
                         ["transfer", "withdrawal-batch-created", "withdrawal-queued", "transfer",
                          "withdrawal-batch-payment"])
        self.assertNotIn(MARKET_CLOSED, _signatures(_committed_logs(_public("wildcat-v1"))))

    def test_v2_queue_path_emits_the_created_batch_first(self):
        logs = _transaction_logs("wildcat-v2", "v2-queue-first-batch")
        self.assertEqual(_signatures(logs), [CREATED, TRANSFER, QUEUED, TRANSFER, PAYMENT])
        self.assertEqual(logs[1]["topics"][1:], ["0x" + word(ACCOUNT), "0x" + word(MARKET)])
        self.assertEqual([row["action"].split(".", 1)[1] for row in _rows(_public("wildcat-v2"))[:5]],
                         ["withdrawal-batch-created", "transfer", "withdrawal-queued", "transfer",
                          "withdrawal-batch-payment"])

    def test_v2_close_market_pays_expires_closes_then_opens_a_one_second_batch(self):
        logs = _transaction_logs("wildcat-v2", "v2-close-market")
        self.assertEqual(_signatures(logs), [TRANSFER, PAYMENT, EXPIRED, CLOSED, CREATED, MARKET_CLOSED])
        self.assertEqual([raw["topics"][1] for raw in logs[1:5]], ["0x" + word(500)] * 3 + ["0x" + word(501)])
        root = _public("wildcat-v2")
        mappings, selectors = _mappings(root), _by_selector(root)
        closed = next(row for row in _rows(root) if row["action"].endswith(".withdrawal-batch-closed")
                      and row["transaction"]["hash"] == logs[0]["transactionHash"])
        evidence = mappings[closed["provenance"]["source_selector"]]
        self.assertIsNone(evidence["join"])
        self.assertIn("does not name which path closed it", " ".join(evidence["limitations"]))
        closing = next(row for row in _rows(root) if row["action"].endswith(".market-closed"))
        self.assertEqual(closing["transaction"]["hash"], closed["transaction"]["hash"])
        self.assertEqual(len(selectors), EXPECTED["wildcat-v2"]["rows"])

    def test_every_source_order_burn_immediately_precedes_its_payment(self):
        for venue in VENUES:
            logs = _committed_logs(_public(venue))
            self.assertEqual([int(raw["logIndex"], 16) for raw in logs], list(range(len(logs))))
            self.assertEqual(logs, specimen_raws(venue))
            hostile = {_transaction_hash(venue, name) for name in HOSTILE_ORDER}
            checked = 0
            for position, raw in enumerate(logs):
                if SIGNATURES[raw["topics"][0]] != PAYMENT or raw["transactionHash"] in hostile:
                    continue
                burn = logs[position - 1]
                self.assertEqual(burn["transactionHash"], raw["transactionHash"])
                self.assertEqual(SIGNATURES[burn["topics"][0]], TRANSFER)
                self.assertEqual(burn["topics"][1:], ["0x" + word(MARKET), "0x" + word(ZERO)])
                self.assertEqual(burn["data"], "0x" + raw["data"][66:])
                checked += 1
            self.assertEqual(checked, EXPECTED[venue]["joined"] - 1)

    def test_fresh_rebuild_matches_every_committed_byte_and_expected_json(self):
        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                fresh = Path(temporary).resolve() / "fresh"
                fresh.mkdir()
                built = build_specimen(fresh, venue)
                self.assertEqual(built, _document(example_directory(venue), "expected.json"))
                self.assertEqual(_file_bytes(fresh / ROOT), _file_bytes(_public(venue)))
                report = verifier.verify(fresh / ROOT / "coverage.json")
                self.assertEqual((report.schema_version, report.rows, report.release),
                                 (3, EXPECTED[venue]["rows"], release_id(venue)))

    def test_moved_read_only_release_verifies_offline_and_the_rebuild_script_reports(self):
        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                copied = base / "copied"
                shutil.copytree(_public(venue), copied)
                moved = base / "elsewhere" / "moved"
                moved.parent.mkdir()
                copied.rename(moved)
                for path in moved.rglob("*"):
                    if path.is_file():
                        path.chmod(0o444)
                self.assertEqual(verifier.verify(moved / "coverage.json").rows, EXPECTED[venue]["rows"])
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(rebuild_example(venue), 0)
                event = json.loads(output.getvalue())
                self.assertEqual(event["event"], "wildcat.batch-specimen.reproduced")
                self.assertEqual(event["roots"][ROOT]["rows"], EXPECTED[venue]["rows"])
                self.assertEqual(set(event["roots"][ROOT]), {"release", "rows", "native_logs", "canonical_sha256"})

    def test_rebuild_refuses_a_specimen_whose_committed_bytes_or_identities_changed(self):
        for venue in VENUES:
            for change in ("expected", "events"):
                with self.subTest(venue=venue, change=change), tempfile.TemporaryDirectory() as temporary:
                    examples = Path(temporary).resolve()
                    copied = examples / (venue + "-batches-v0")
                    shutil.copytree(example_directory(venue), copied)
                    for path in copied.rglob("*"):
                        if path.is_file():
                            path.chmod(0o600)
                    if change == "expected":
                        expected = _document(copied, "expected.json")
                        expected[ROOT]["rows"] += 1
                        (copied / "expected.json").write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n")
                    else:
                        events = copied / ROOT / "events.jsonl"
                        events.write_bytes(events.read_bytes().replace(b'"base_units":"40"', b'"base_units":"41"', 1))
                    with self.assertRaises((ValueError, TabulariumError)), redirect_stdout(io.StringIO()):
                        rebuild_example(venue, examples)

    def test_every_record_keeps_its_constructed_qualification(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                source = _document(root, "source.json")
                self.assertEqual(source["scope"]["kind"], "constructed-fixture")
                self.assertEqual(source["scope"]["limitations"], [CONSTRUCTION_GAP])
                for context in source["contexts"].values():
                    self.assertEqual([item["class"] for item in context["source"]], ["declared-constructed-context"])
                for capture in source["scope"]["raw_captures"]:
                    self.assertEqual(capture["source"]["kind"], "constructed-fixture")
                    self.assertEqual(capture["source"]["locator_class"], "local-fixture")
                    self.assertEqual(capture["scope"]["finality"], "unknown")
                    self.assertEqual(capture["coverage"]["gaps"], [CONSTRUCTION_GAP])
                self.assertEqual(_document(root, "capture.json")["scope"], source["scope"])
                for mapping in source["mapping_records"]:
                    self.assertEqual(mapping["reference"]["evidence_class"], "recorded-rpc")
                    self.assertEqual(mapping["evidence_class"], "directly-observed")
                    self.assertEqual(mapping["context"]["role"], "market")
                    self.assertNotIn("borrower_context", mapping["context"])
                    self.assertTrue(mapping["supporting_selectors"][0].startswith("wildcat-context:"))
                coverage = _document(root, "coverage.json")
                self.assertEqual(coverage["release"], release_id(venue))
                self.assertIn("constructed", coverage["release"])
                raw_release_id = source["raw_release"]["release_id"]
                self.assertTrue(raw_release_id.startswith("sha256:"))
                manifest = _document(root / "source/raw-release", "manifest.json")
                self.assertEqual((manifest["release_id"], manifest["release"]["name"]),
                                 (raw_release_id, venue + "-constructed-batches"))
                self.assertEqual(_document(example_directory(venue), "expected.json")[ROOT]["raw_release_id"],
                                 raw_release_id)
                self.assertEqual(_document(example_directory(venue), "expected.json")[ROOT]["scope_kind"],
                                 "constructed-fixture")

    def test_batch_signatures_are_absent_from_unsupported_coverage(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                coverage = _document(root, "coverage.json")["coverage"]
                unsupported = coverage["unsupported_events"]
                self.assertFalse([key for key in unsupported if key.startswith(("canonical:", "decode:"))])
                self.assertFalse([key for key in unsupported if "WithdrawalBatch" in key])
                for action in BATCH_ACTIONS:
                    self.assertGreaterEqual(coverage["included_events"][action], 1)
                rules = _document(root, "coverage.json")["versions"]["mapping_rules"]
                self.assertEqual([rule for rule in rules if "batch" in rule],
                                 sorted(venue + "." + action + ".v1" for action in BATCH_RULES))
                self.assertEqual({d["disposition"] for d in _dispositions(root).values()}, {"primary"})
                self.assertEqual({SIGNATURES[raw["topics"][0]] for raw in _committed_logs(root)} & set(BATCH_SIGNATURES),
                                 set(BATCH_SIGNATURES))

    def test_each_payment_carries_its_join_or_its_burn_gap(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                mappings, dispositions, selectors = _mappings(root), _dispositions(root), _by_selector(root)
                payments = _payments(root)
                self.assertEqual(len(payments), EXPECTED[venue]["payments"])
                joined = 0
                for payment in payments:
                    selector = payment["provenance"]["source_selector"]
                    join = mappings[selector]["join"]
                    if join is None:
                        self.assertIn(BURN_GAP, dispositions[selector]["gaps"])
                        self.assertEqual(len(payment["provenance"]["supporting_selectors"]), 1)
                        continue
                    joined += 1
                    self.assertEqual(join["rule"], BURN_JOIN_RULE)
                    self.assertEqual(join["evidence_class"], "join-inference")
                    self.assertEqual(join["primary_selector"], selector)
                    burn = selectors[join["companion_selector"]]
                    self.assertEqual(burn["transaction"]["hash"], payment["transaction"]["hash"])
                    self.assertEqual(burn["transaction"]["log_index"], payment["transaction"]["log_index"] - 1)
                    self.assertEqual(burn["parties"], [{"role": "from", "address": MARKET}, {"role": "to", "address": ZERO}])
                    self.assertEqual(burn["amounts"][0]["base_units"], payment["amounts"][1]["base_units"])
                    self.assertEqual(payment["provenance"]["supporting_selectors"][-1], join["companion_selector"])
                    self.assertEqual(burn["provenance"]["supporting_selectors"][-1], selector)
                    self.assertEqual(mappings[join["companion_selector"]]["join"], join)
                    self.assertNotIn(BURN_GAP, dispositions[selector]["gaps"])
                self.assertEqual(joined, EXPECTED[venue]["joined"])

    def test_each_hostile_transaction_carries_its_named_gap_and_source_transactions_none(self):
        for venue in VENUES:
            root = _public(venue)
            by_hash = {_transaction_hash(venue, name): name for name in specimen_names(venue)}
            gaps = {name: Counter() for name in by_hash.values()}
            selectors = _by_selector(root)
            for selector, disposition in _dispositions(root).items():
                name = by_hash[selectors[selector]["transaction"]["hash"]]
                gaps[name].update(gap for gap in disposition["gaps"] if gap in (BURN_GAP, UNCLAIMED_GAP))
            for name, counted in gaps.items():
                with self.subTest(venue=venue, transaction=name):
                    self.assertEqual(dict(counted), HOSTILE_GAPS.get(name, {}))
            mappings = _mappings(root)
            adjacent = next(p for p in _payments(root)
                            if p["transaction"]["hash"] == _transaction_hash(venue, "two-burns-one-payment"))
            join = mappings[adjacent["provenance"]["source_selector"]]["join"]
            self.assertEqual(join["conditions"]["burn_log_index"], adjacent["transaction"]["log_index"] - 1)

    def test_two_payments_to_one_expiry_in_one_transaction_each_join_their_own_burn(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                mappings = _mappings(root)
                payments = [p for p in _payments(root)
                            if p["transaction"]["hash"] == _transaction_hash(venue, "queue-double-payment-same-expiry")]
                self.assertEqual(len(payments), 2)
                self.assertEqual([mappings[p["provenance"]["source_selector"]]["decoded"]["expiry"] for p in payments],
                                 ["300", "300"])
                companions = [mappings[p["provenance"]["source_selector"]]["join"]["companion_selector"] for p in payments]
                self.assertEqual(len(set(companions)), 2)
                burns = [mappings[selector] for selector in companions]
                self.assertEqual([int(b["native_record"]["logIndex"], 16) for b in burns],
                                 [p["transaction"]["log_index"] - 1 for p in payments])

    def test_coverage_counts_mapped_rows_and_gaps_separately(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                coverage = _document(root, "coverage.json")
                rows = _rows(root)
                expected = EXPECTED[venue]
                self.assertEqual(coverage["canonical"]["rows"], expected["rows"])
                self.assertEqual(len(rows), expected["rows"])
                self.assertEqual(sum(coverage["coverage"]["included_events"].values()), expected["rows"])
                self.assertEqual(coverage["coverage"]["included_events"],
                                 dict(Counter(row["action"].split(".", 1)[1] for row in rows)))
                unsupported = coverage["coverage"]["unsupported_events"]
                self.assertEqual(unsupported[BURN_GAP], expected["payments"] - expected["joined"])
                self.assertEqual(unsupported[UNCLAIMED_GAP], 4)
                self.assertEqual(unsupported["attribution:withdrawal-batch-payment:actor"], expected["payments"])
                self.assertEqual(len({row["transaction"]["hash"] for row in rows}), expected["transactions"])
                observed = _document(example_directory(venue), "expected.json")[ROOT]
                self.assertEqual((observed["rows"], observed["native_logs"]), (expected["rows"], expected["rows"]))
                self.assertEqual(observed["dispositions"], {"primary": expected["rows"]})

    def test_specimen_logs_carry_only_synthetic_identities(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                logs = _committed_logs(_public(venue))
                for raw in logs:
                    self.assertEqual(raw["address"], MARKET)
                    self.assertEqual(raw["blockHash"], "0x" + "aa" * 32)
                    self.assertEqual(raw["blockNumber"], "0x64")
                    self.assertRegex(raw["transactionHash"], r"^0x(b[0-9a-f])\1{31}$")
                    for position in ADDRESS_TOPICS.get(SIGNATURES[raw["topics"][0]], ()):
                        topic = raw["topics"][position]
                        self.assertEqual(topic[:26], "0x" + "00" * 12)
                        self.assertIn("0x" + topic[-40:], SYNTHETIC_ADDRESSES)
                source = _document(_public(venue), "source.json")
                self.assertEqual(set(source["contexts"]) - {MARKET}, set() if venue == "wildcat-v1" else {"0x" + "22" * 20})
                for capture in source["scope"]["raw_captures"]:
                    self.assertEqual(capture["source"]["reference"], venue + "-constructed-specimen")

    def test_batch_limitations_read_reserved_as_reserved_and_name_no_cause(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                mappings = _mappings(root)
                for row in _rows(root):
                    action = row["action"].split(".", 1)[1]
                    if action not in BATCH_ACTIONS:
                        continue
                    evidence = mappings[row["provenance"]["source_selector"]]
                    text = " ".join(evidence["limitations"])
                    for phrase in ("lender receipt", "spendable cash", "caused by", "because of", "executed to"):
                        self.assertNotIn(phrase, text)
                    self.assertEqual([party["role"] for party in row["parties"]], ["pool"])
                    self.assertEqual(row["event_family"], "exit-queue")
                    if action == "withdrawal-batch-payment":
                        self.assertEqual([amount["kind"] for amount in row["amounts"]],
                                         ["burned-scaled-claims", "reserved-assets"])
                        self.assertIn("not received, spendable or executed", text)


if __name__ == "__main__":
    unittest.main()
