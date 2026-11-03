"""Hold the constructed accrual specimens to source order, rebuilt bytes and named gaps."""

from collections import Counter
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
GUIDE = HERE.parent / "docs" / "wildcat-canonical.md"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "scripts"))
from tabularium_lib import verifier
from tabularium_lib.core import TabulariumError
from tabularium_lib.keccak import keccak256
from tabularium_lib.wildcat_source import CONSTRUCTION_GAP
from test_wildcat_accrual_mapping import ACCRUAL_AMOUNTS, ASSET_LIMITATION, LIMITATIONS, RAY_KINDS, ROW_FIELDS
from wildcat_accrual_public_fixtures import (
    BLOCK_TIME, EXPIRY, ROOT, TRANSACTIONS, VENUES, build_specimen, example_directory, rebuild_example,
    release_id, specimen_names, specimen_raws,
)
from wildcat_batch_fixtures import CLOSED, EXPIRED, PAYMENT, SECOND_MARKET, TRANSFER
from wildcat_v3_fixtures import ACCRUAL, ACCRUAL_ACTIONS, ASSET, MARKET, RAY, STATE, WRAPPER

ASSET_GAP = "attribution:interest-and-fees-accrued:asset"
ACCRUAL_RULES = ("interest-and-fees-accrued", "state-updated")
SIGNATURES = {"0x" + keccak256(signature.encode()).hex(): signature
              for signature in (ACCRUAL, STATE, TRANSFER, PAYMENT, EXPIRED, CLOSED)}
# Each transaction's signatures in emission order, stated apart from the fixture.
SOURCE_ORDER = {
    "expired-batch-update-state": [ACCRUAL, TRANSFER, PAYMENT, EXPIRED, CLOSED, ACCRUAL, STATE],
    "same-timestamp-update-state": [STATE],
    "unknown-asset-update-state": [ACCRUAL, STATE],
}
EXPECTED = {"rows": 10, "transactions": 3, "interest-and-fees-accrued": 3, "state-updated": 3}
UNSUPPORTED = {
    "attribution:interest-and-fees-accrued:actor": 3,
    ASSET_GAP: 1,
    "attribution:state-updated:actor": 3,
    "attribution:withdrawal-batch-closed:actor": 1,
    "attribution:withdrawal-batch-expired:actor": 1,
    "attribution:withdrawal-batch-payment:actor": 1,
}
CAUSE_PHRASES = ("caused by", "because of", "collected by", "paid to", "in default", "defaulted")


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
    return "0x" + ("%02x" % (0xb0 + specimen_names(venue).index(name))) * 32


def _transaction_logs(venue, name):
    return [raw for raw in _committed_logs(_public(venue)) if raw["transactionHash"] == _transaction_hash(venue, name)]


def _mappings(root):
    return {m["source_selector"]: m for m in _document(root, "source.json")["mapping_records"]}


def _dispositions(root):
    return {d["source_selector"]: d for d in _document(root, "source.json")["dispositions"]}


def _action_rows(root, action):
    return [row for row in _rows(root) if row["action"].endswith("." + action)]


class AccrualSpecimenTests(unittest.TestCase):
    """Source order, byte-exact rebuild, constructed qualification, native units and named gaps."""

    def test_each_transaction_follows_the_pinned_source_emission_order(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                logs = _committed_logs(_public(venue))
                self.assertEqual(logs, specimen_raws(venue))
                self.assertEqual([int(raw["logIndex"], 16) for raw in logs], list(range(EXPECTED["rows"])))
                self.assertEqual(specimen_names(venue), tuple(SOURCE_ORDER))
                for name, order in SOURCE_ORDER.items():
                    transaction = _transaction_logs(venue, name)
                    self.assertEqual([SIGNATURES[raw["topics"][0]] for raw in transaction], order, name)
                    self.assertEqual(SIGNATURES[transaction[-1]["topics"][0]], STATE, name)
                rows = _rows(_public(venue))
                self.assertEqual([row["transaction"]["log_index"] for row in rows], list(range(EXPECTED["rows"])))
                mappings = _mappings(_public(venue))
                intervals = [(mappings[row["provenance"]["source_selector"]]["decoded"]["fromTimestamp"],
                              mappings[row["provenance"]["source_selector"]]["decoded"]["toTimestamp"])
                             for row in _action_rows(_public(venue), "interest-and-fees-accrued")]
                self.assertEqual(intervals, [("1000", str(EXPIRY)), (str(EXPIRY), str(BLOCK_TIME)),
                                             ("1000", str(BLOCK_TIME))])

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
                                 (3, EXPECTED["rows"], release_id(venue)))

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
                self.assertEqual(verifier.verify(moved / "coverage.json").rows, EXPECTED["rows"])
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(rebuild_example(venue), 0)
                event = json.loads(output.getvalue())
                self.assertEqual(event["event"], "wildcat.accrual-specimen.reproduced")
                self.assertEqual(event["roots"][ROOT]["rows"], EXPECTED["rows"])
                self.assertEqual(set(event["roots"][ROOT]), {"release", "rows", "native_logs", "canonical_sha256"})

    def test_rebuild_refuses_a_specimen_whose_committed_bytes_or_identities_changed(self):
        for venue in VENUES:
            for change in ("expected", "events", "raw"):
                with self.subTest(venue=venue, change=change), tempfile.TemporaryDirectory() as temporary:
                    examples = Path(temporary).resolve()
                    copied = examples / (venue + "-accrual-v0")
                    shutil.copytree(example_directory(venue), copied)
                    for path in copied.rglob("*"):
                        if path.is_file():
                            path.chmod(0o600)
                    if change == "expected":
                        expected = _document(copied, "expected.json")
                        expected[ROOT]["rows"] += 1
                        (copied / "expected.json").write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n")
                    elif change == "events":
                        events = copied / ROOT / "events.jsonl"
                        data = events.read_bytes()
                        self.assertEqual(data.count(b'"base_units":"100"'), 1)
                        events.write_bytes(data.replace(b'"base_units":"100"', b'"base_units":"101"'))
                    else:
                        manifest = _document(copied / ROOT / "source/raw-release", "manifest.json")
                        component = next(item for item in manifest["components"] if item["name"] == "native-logs")
                        journal = copied / ROOT / "source/raw-release" / component["object_path"]
                        journal.write_bytes(journal.read_bytes().replace(b"0x64", b"0x65", 1))
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
                                 (raw_release_id, venue + "-constructed-accrual"))
                expected = _document(example_directory(venue), "expected.json")[ROOT]
                self.assertEqual((expected["raw_release_id"], expected["scope_kind"]),
                                 (raw_release_id, "constructed-fixture"))

    def test_both_signatures_are_absent_from_unsupported_coverage(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                document = _document(root, "coverage.json")
                unsupported = document["coverage"]["unsupported_events"]
                self.assertFalse([key for key in unsupported if key.startswith(("canonical:", "decode:"))])
                self.assertFalse([key for key in unsupported
                                  if "InterestAndFeesAccrued" in key or "StateUpdated" in key])
                for action in ACCRUAL_ACTIONS:
                    self.assertEqual(document["coverage"]["included_events"][action], EXPECTED[action])
                rules = document["versions"]["mapping_rules"]
                self.assertEqual([rule for rule in rules if rule.endswith(tuple("." + r + ".v1" for r in ACCRUAL_RULES))],
                                 sorted(venue + "." + action + ".v1" for action in ACCRUAL_RULES))
                self.assertEqual({d["disposition"] for d in _dispositions(root).values()}, {"primary"})
                self.assertEqual({SIGNATURES[raw["topics"][0]] for raw in _committed_logs(root)} & {ACCRUAL, STATE},
                                 {ACCRUAL, STATE})

    def test_protocol_fees_name_the_declared_asset_or_carry_the_named_asset_gap(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                contexts = _document(root, "source.json")["contexts"]
                self.assertEqual((contexts[MARKET]["asset"], contexts[SECOND_MARKET]["asset"]), (ASSET, None))
                self.assertEqual(contexts[SECOND_MARKET]["role"], "market")
                mappings, dispositions = _mappings(root), _dispositions(root)
                fees = []
                for event in _action_rows(root, "interest-and-fees-accrued"):
                    selector = event["provenance"]["source_selector"]
                    market = event["instrument"]["id"]
                    fees.append((market, event["amounts"][3]["asset"]))
                    gaps = dispositions[selector]["gaps"]
                    limitations = mappings[selector]["limitations"]
                    if market == MARKET:
                        self.assertEqual(gaps, ["attribution:interest-and-fees-accrued:actor"])
                        self.assertNotIn(ASSET_LIMITATION, limitations)
                    else:
                        self.assertEqual(gaps, ["attribution:interest-and-fees-accrued:actor", ASSET_GAP])
                        self.assertEqual(limitations, LIMITATIONS["interest-and-fees-accrued"] + [ASSET_LIMITATION])
                self.assertEqual(fees, [(MARKET, ASSET), (MARKET, ASSET), (SECOND_MARKET, None)])
                for event in _action_rows(root, "state-updated"):
                    self.assertNotIn(ASSET_GAP, dispositions[event["provenance"]["source_selector"]]["gaps"])
                self.assertEqual(_document(root, "coverage.json")["coverage"]["unsupported_events"][ASSET_GAP], 1)

    def test_prose_reads_the_unknown_asset_fee_as_a_null_asset_not_a_null_amount(self):
        # The README and guide once said the fee amount stays null; the row
        # holds the decoded amount, and only its asset is null.
        null_subject = r"`protocol-fees` (\w+) stays null"
        carrier = r"(\w+)(?: in `source\.json`)? carries `" + re.escape(ASSET_GAP) + "`"
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                (event,) = [row for row in _action_rows(root, "interest-and-fees-accrued")
                            if row["instrument"]["id"] == SECOND_MARKET]
                selector = event["provenance"]["source_selector"]
                fee = event["amounts"][3]
                self.assertEqual((fee["kind"], fee["asset"], fee["base_units"]),
                                 ("protocol-fees", None, _mappings(root)[selector]["decoded"]["protocolFees"]))
                self.assertNotIn("gaps", event)
                self.assertIn(ASSET_GAP, _dispositions(root)[selector]["gaps"])
                text = " ".join((example_directory(venue) / "README.md").read_text().split())
                self.assertEqual(re.findall(null_subject, text), ["asset"])
                self.assertEqual(re.findall(carrier, text), ["disposition"])
        guide = " ".join(GUIDE.read_text().split())
        self.assertEqual(re.findall(null_subject, guide), ["asset"])

    def test_each_amount_is_its_decoded_field_in_native_units_with_no_conversion(self):
        accruals = [step[1:] for _name, _emitter, steps in TRANSACTIONS for step in steps if step[0] == "accrual"]
        states = [step[1:] for _name, _emitter, steps in TRANSACTIONS for step in steps if step[0] == "state"]
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                mappings = _mappings(root)
                rows = _action_rows(root, "interest-and-fees-accrued")
                for event, values in zip(rows, accruals, strict=True):
                    decoded = mappings[event["provenance"]["source_selector"]]["decoded"]
                    self.assertEqual([(a["kind"], a["base_units"]) for a in event["amounts"]],
                                     [(kind, decoded[field]) for kind, field in ACCRUAL_AMOUNTS])
                    self.assertEqual([a["base_units"] for a in event["amounts"]], [str(v) for v in values[2:]])
                    self.assertEqual([a["asset"] for a in event["amounts"] if a["kind"] in RAY_KINDS], [None] * 3)
                    self.assertGreaterEqual(int(event["amounts"][0]["base_units"]), RAY)
                for event, values in zip(_action_rows(root, "state-updated"), states, strict=True):
                    decoded = mappings[event["provenance"]["source_selector"]]["decoded"]
                    self.assertEqual(event["amounts"], [{"kind": "scale-factor", "base_units": str(values[0]),
                                                         "asset": None}])
                    self.assertEqual(decoded["scaleFactor"], str(values[0]))

    def test_timestamps_and_is_delinquent_stay_decoded_native_state(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                mappings = _mappings(root)
                logs = {(raw["transactionHash"], raw["logIndex"]): raw for raw in _committed_logs(root)}
                for action, fields in (("interest-and-fees-accrued", ("fromTimestamp", "toTimestamp")),
                                       ("state-updated", ("isDelinquent",))):
                    for event in _action_rows(root, action):
                        evidence = mappings[event["provenance"]["source_selector"]]
                        self.assertEqual(set(event), ROW_FIELDS)
                        self.assertEqual(event["parties"], [{"role": "pool", "address": event["instrument"]["id"]}])
                        for field in fields:
                            self.assertIn(field, evidence["decoded"])
                        kinds = {amount["kind"] for amount in event["amounts"]}
                        self.assertFalse({"from-timestamp", "to-timestamp", "is-delinquent"} & kinds)
                        self.assertEqual(event["native_record"], evidence["native_record"])
                        self.assertEqual(event["native_record"],
                                         logs[(event["transaction"]["hash"], hex(event["transaction"]["log_index"]))])
                flags = [(event["instrument"]["id"], mappings[event["provenance"]["source_selector"]]["decoded"]["isDelinquent"])
                         for event in _action_rows(root, "state-updated")]
                self.assertEqual(flags, [(MARKET, False), (MARKET, False), (SECOND_MARKET, True)])

    def test_rows_join_nothing_and_name_no_cause(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                mappings = _mappings(root)
                selectors = set(mappings)
                for action in ACCRUAL_ACTIONS:
                    for event in _action_rows(root, action):
                        selector = event["provenance"]["source_selector"]
                        evidence = mappings[selector]
                        self.assertIsNone(evidence["join"])
                        supporting = event["provenance"]["supporting_selectors"]
                        self.assertEqual(len(supporting), 1)
                        self.assertFalse(set(supporting) & selectors)
                        if event["instrument"]["id"] == MARKET or action == "state-updated":
                            self.assertEqual(evidence["limitations"], LIMITATIONS[action])
                        text = " ".join(evidence["limitations"]).lower()
                        for phrase in CAUSE_PHRASES:
                            self.assertNotIn(phrase, text)
                alone = _transaction_logs(venue, "same-timestamp-update-state")
                self.assertEqual([SIGNATURES[raw["topics"][0]] for raw in alone], [STATE])
                # The only join is the batch payment's adjacent burn; neither side is an accrual or state write.
                joins = [mapping["join"] for mapping in mappings.values() if mapping["join"] is not None]
                self.assertEqual(len(joins), 2)
                for join in joins:
                    self.assertEqual((mappings[join["primary_selector"]]["signature"],
                                      mappings[join["companion_selector"]]["signature"]), (PAYMENT, TRANSFER))

    def test_coverage_counts_mapped_rows_and_gaps_separately(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue)
                coverage = _document(root, "coverage.json")
                rows = _rows(root)
                self.assertEqual(coverage["canonical"]["rows"], EXPECTED["rows"])
                self.assertEqual(len(rows), EXPECTED["rows"])
                self.assertEqual(sum(coverage["coverage"]["included_events"].values()), EXPECTED["rows"])
                self.assertEqual(coverage["coverage"]["included_events"],
                                 dict(Counter(row["action"].split(".", 1)[1] for row in rows)))
                self.assertEqual(coverage["coverage"]["unsupported_events"], UNSUPPORTED)
                self.assertEqual(len({row["transaction"]["hash"] for row in rows}), EXPECTED["transactions"])
                observed = _document(example_directory(venue), "expected.json")[ROOT]
                self.assertEqual((observed["rows"], observed["native_logs"]), (EXPECTED["rows"], EXPECTED["rows"]))
                self.assertEqual(observed["dispositions"], {"primary": EXPECTED["rows"]})

    def test_specimen_logs_carry_only_synthetic_identities(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                logs = _committed_logs(_public(venue))
                for raw in logs:
                    self.assertIn(raw["address"], (MARKET, SECOND_MARKET))
                    self.assertEqual(raw["blockHash"], "0x" + "aa" * 32)
                    self.assertEqual(raw["blockNumber"], "0x64")
                    self.assertRegex(raw["transactionHash"], r"^0x(b[0-2])\1{31}$")
                    if SIGNATURES[raw["topics"][0]] == TRANSFER:
                        self.assertEqual(raw["topics"][1:], ["0x" + "00" * 12 + MARKET[2:], "0x" + "00" * 32])
                self.assertEqual({raw["address"] for raw in _transaction_logs(venue, "unknown-asset-update-state")},
                                 {SECOND_MARKET})
                source = _document(_public(venue), "source.json")
                declared = {MARKET, SECOND_MARKET} | ({WRAPPER} if venue == "wildcat-v2" else set())
                self.assertEqual(set(source["contexts"]), declared)
                for capture in source["scope"]["raw_captures"]:
                    self.assertEqual(capture["source"]["reference"], venue + "-constructed-specimen")
                    self.assertEqual(capture["scope"]["subjects"], ["eip155:1:" + address for address in sorted(declared)])


if __name__ == "__main__":
    unittest.main()
