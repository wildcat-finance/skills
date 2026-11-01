"""Exercise the accrual and state-update meanings on constructed logs and built releases."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "scripts"))
import support
from tabularium_lib import builder, verifier
from tabularium_lib.core import TabulariumError, canonical_json, sha256_bytes
from tabularium_lib.keccak import keccak256
from tabularium_lib.wildcat_abi import VARIANTS, abi_variant_for
from tabularium_lib.wildcat_release import build_wildcat_canonical
from tabularium_lib.wildcat_rows import map_records
from tabularium_lib.wildcat_rules import DECLARED_FIELDS, RULES
from test_wildcat_v3_release import constructed_release
from wildcat_batch_public_fixtures import build_specimen, example_directory
from wildcat_batch_public_fixtures import ROOT as BATCH_ROOT
from wildcat_v3_fixtures import (
    ACCOUNT, ACCRUAL, ACCRUAL_ACTIONS, ACCRUAL_FIELDS, ACCRUED_TO, ASSET, MARKET, RAY, STATE, V1_COMMIT,
    V2_COMMIT, ZERO, accrual_inputs, log, record, word,
)
from wildcat_v3_public_fixtures import build_pair, compare_pair

VENUES = ("wildcat-v1", "wildcat-v2")
TOPICS = {"0x" + keccak256(signature.encode()).hex(): signature for signature in (ACCRUAL, STATE)}
ACCRUAL_TOPIC, STATE_TOPIC = ("0x" + keccak256(signature.encode()).hex() for signature in (ACCRUAL, STATE))
# The study's table, stated independently of the production tuples.
ACCRUAL_AMOUNTS = (("scale-factor", "scaleFactor"), ("base-interest-ray", "baseInterestRay"),
                   ("delinquency-fee-ray", "delinquencyFeeRay"), ("protocol-fees", "protocolFees"))
RAY_KINDS = ("scale-factor", "base-interest-ray", "delinquency-fee-ray")
NATIVE_STATE = {"interest-and-fees-accrued": ("fromTimestamp", "toTimestamp"),
                "state-updated": ("isDelinquent",)}
ROW_FIELDS = {"schema_version", "id", "event_family", "action", "venue", "chain", "transaction",
              "parties", "instrument", "amounts", "provenance", "native_record"}
LIMITATIONS = {
    "interest-and-fees-accrued": [
        "The scale factor and both rates are ray values, not asset quantities; the protocol fees are accrued, not collected or paid.",
        "The interval timestamps are native state; no event in the same transaction is named as this accrual's cause."],
    "state-updated": [
        "The scale factor is a ray value, not an asset quantity; no row equates it with an accrual's scale factor.",
        "isDelinquent is native state; it does not establish when delinquency began, a penalty or current standing."],
}
ASSET_LIMITATION = "The source does not establish an asset context; missing metadata remains null."
SCHEMA_2_DIGESTS = {
    "canonical-event-v2.json": "9ea081cf1cf89a1c0c81c2189767fd9bc69f1b65f24f19e3bab829e8948d65e8",
    "coverage-manifest-v2.json": "7756a58f9da49a852a418a200254e99a96105d9f7b461862b6db51302f07582b",
}


def mapped(venue, asset=True, delinquent=1):
    contexts, records = accrual_inputs(venue, delinquent)
    if not asset:
        contexts[MARKET]["asset"] = None
    return map_records(venue, contexts, records)


def row(result, action):
    (event,) = [event for event in result["events"] if event["action"].endswith("." + action)]
    return event


def mapping_for(result, event):
    return next(item for item in result["mapping_records"]
                if item["source_selector"] == event["provenance"]["source_selector"])


def market_variant(venue):
    return abi_variant_for(venue, "market", "WildcatMarket", V1_COMMIT if venue == "wildcat-v1" else V2_COMMIT)


def moved(venue, topic, inputs):
    """Patch one pinned definition so its fields read as `inputs`; types decide the topic."""
    definition = deepcopy(VARIANTS[market_variant(venue)]["events"][topic])
    definition["abi"]["inputs"] = [{"indexed": indexed, "name": name, "type": kind} for name, kind, indexed in inputs]
    return mock.patch.dict(VARIANTS[market_variant(venue)]["events"], {topic: definition})


def accrual_release(base, venue, raws, asset=True):
    """Ingest constructed logs through the real raw-release API and build a canonical release."""
    def replace(document, journal, plan):
        response = json.loads(journal["records"][0]["response"])
        response["result"] = raws
        journal["records"][0]["response"] = canonical_json(response).decode()
        if not asset:
            for context in document["contexts"]:
                if context["role"] == "market":
                    context["asset"] = None

    raw = constructed_release(base, venue, replace)
    target = base / "canonical"
    build_wildcat_canonical(raw, target, "constructed-accrual-" + venue)
    return target


def source_raws():
    """One accrual, a deposit's mint and deposit, then the state write, in source order."""
    return [log(ACCRUAL, (), ACCRUAL_FIELDS, index=0),
            log("Transfer(address,address,uint256)", (ZERO, ACCOUNT), (100,), index=1),
            log("Deposit(address,uint256,uint256)", (ACCOUNT,), (100, 94), index=2),
            log(STATE, (), (RAY + 5 * 10 ** 22, 0), index=3)]


class AccrualMappingTests(unittest.TestCase):
    def test_accrual_rows_carry_pool_only_interest_accrual_and_four_abi_named_amounts(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                event = row(mapped(venue), "interest-and-fees-accrued")
                self.assertEqual(event["event_family"], "interest-accrual")
                self.assertEqual(event["parties"], [{"role": "pool", "address": MARKET}])
                self.assertEqual(event["instrument"], {"type": venue + "-market", "id": MARKET})
                self.assertEqual(event["amounts"], [
                    {"kind": "scale-factor", "base_units": str(RAY + 5 * 10 ** 22), "asset": None},
                    {"kind": "base-interest-ray", "base_units": str(4 * 10 ** 22), "asset": None},
                    {"kind": "delinquency-fee-ray", "base_units": str(10 ** 22), "asset": None},
                    {"kind": "protocol-fees", "base_units": "7", "asset": ASSET}])
                self.assertEqual(event["provenance"]["mapping_rule"], venue + ".interest-and-fees-accrued.v1")
                self.assertEqual(event["provenance"]["source_entity"], ACCRUAL)

    def test_state_updated_rows_carry_pool_only_pool_state_and_one_scale_factor(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                event = row(mapped(venue), "state-updated")
                self.assertEqual(event["event_family"], "pool-state")
                self.assertEqual(event["parties"], [{"role": "pool", "address": MARKET}])
                self.assertEqual(event["instrument"], {"type": venue + "-market", "id": MARKET})
                self.assertEqual(event["amounts"], [{"kind": "scale-factor", "base_units": str(RAY + 5 * 10 ** 22),
                                                     "asset": None}])
                self.assertEqual(event["provenance"]["mapping_rule"], venue + ".state-updated.v1")
                self.assertEqual(event["provenance"]["source_entity"], STATE)

    def test_each_amount_is_its_decoded_field_in_native_units_with_no_conversion(self):
        extremes = (0, (1 << 256) - 1, (1 << 256) - 2, 10 ** 30 + 1)
        for venue in VENUES:
            contexts, _ = accrual_inputs(venue)
            raws = [log(ACCRUAL, (), (1, 2, *extremes), index=0), log(STATE, (), ((1 << 256) - 3, 0), index=1)]
            result = map_records(venue, contexts, [record(raw) for raw in raws])
            accrual = row(result, "interest-and-fees-accrued")
            decoded = mapping_for(result, accrual)["decoded"]
            self.assertEqual([(a["kind"], a["base_units"]) for a in accrual["amounts"]],
                             [(kind, decoded[field]) for kind, field in ACCRUAL_AMOUNTS])
            self.assertEqual([a["base_units"] for a in accrual["amounts"]], [str(value) for value in extremes])
            state = row(result, "state-updated")
            self.assertEqual(state["amounts"][0]["base_units"], str((1 << 256) - 3))
            self.assertEqual(mapping_for(result, state)["decoded"]["scaleFactor"], str((1 << 256) - 3))

    def test_ray_kinds_stay_assetless_whether_or_not_the_asset_is_known(self):
        for venue in VENUES:
            for asset in (True, False):
                with self.subTest(venue=venue, asset=asset):
                    result = mapped(venue, asset)
                    for event in result["events"]:
                        for amount in event["amounts"]:
                            if amount["kind"] in RAY_KINDS:
                                self.assertIsNone(amount["asset"])
                    self.assertNotIn("attribution:state-updated:asset", result["unsupported_counts"])

    def test_protocol_fees_name_the_market_asset_where_the_context_establishes_it(self):
        for venue in VENUES:
            result = mapped(venue)
            fees = row(result, "interest-and-fees-accrued")["amounts"][3]
            self.assertEqual(fees, {"kind": "protocol-fees", "base_units": "7", "asset": ASSET})
            self.assertNotIn("attribution:interest-and-fees-accrued:asset", result["unsupported_counts"])
            self.assertNotIn(ASSET_LIMITATION, mapping_for(result, row(result, "interest-and-fees-accrued"))["limitations"])

    def test_unknown_asset_leaves_protocol_fees_null_with_the_named_asset_gap(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                result = mapped(venue, asset=False)
                accrual = row(result, "interest-and-fees-accrued")
                self.assertEqual(accrual["amounts"][3], {"kind": "protocol-fees", "base_units": "7", "asset": None})
                self.assertEqual(result["unsupported_counts"]["attribution:interest-and-fees-accrued:asset"], 1)
                disposition = next(d for d in result["dispositions"]
                                   if d["source_selector"] == accrual["provenance"]["source_selector"])
                self.assertEqual(disposition["gaps"], ["attribution:interest-and-fees-accrued:actor",
                                                       "attribution:interest-and-fees-accrued:asset"])
                self.assertEqual(mapping_for(result, accrual)["limitations"],
                                 LIMITATIONS["interest-and-fees-accrued"] + [ASSET_LIMITATION])

    def test_timestamps_and_is_delinquent_stay_decoded_native_state(self):
        for venue in VENUES:
            contexts, records = accrual_inputs(venue)
            result = map_records(venue, contexts, records)
            for action, fields in NATIVE_STATE.items():
                with self.subTest(venue=venue, action=action):
                    event = row(result, action)
                    evidence = mapping_for(result, event)
                    for field in fields:
                        self.assertIn(field, evidence["decoded"])
                    self.assertEqual(set(event), ROW_FIELDS)
                    self.assertEqual([party["role"] for party in event["parties"]], ["pool"])
                    kinds = [amount["kind"] for amount in event["amounts"]]
                    self.assertFalse({"from-timestamp", "to-timestamp", "is-delinquent"} & set(kinds))
                    self.assertEqual(event["native_record"], evidence["native_record"])
            accrual = mapping_for(result, row(result, "interest-and-fees-accrued"))["decoded"]
            self.assertEqual((accrual["fromTimestamp"], accrual["toTimestamp"]),
                             (str(ACCRUED_TO - 3600), str(ACCRUED_TO)))
            self.assertEqual(row(result, "interest-and-fees-accrued")["native_record"], records[0][0])
            self.assertIs(mapping_for(result, row(result, "state-updated"))["decoded"]["isDelinquent"], True)
            self.assertEqual(row(result, "state-updated")["native_record"], records[1][0])

    def test_is_delinquent_decodes_both_words_as_booleans_without_changing_the_row(self):
        for venue in VENUES:
            true_result, false_result = mapped(venue, delinquent=1), mapped(venue, delinquent=0)
            self.assertIs(mapping_for(true_result, row(true_result, "state-updated"))["decoded"]["isDelinquent"], True)
            self.assertIs(mapping_for(false_result, row(false_result, "state-updated"))["decoded"]["isDelinquent"], False)
            true_row, false_row = row(true_result, "state-updated"), row(false_result, "state-updated")
            self.assertEqual(true_row["amounts"], false_row["amounts"])
            self.assertEqual(true_row["parties"], false_row["parties"])

    def test_both_events_are_primary_with_an_actor_gap_and_no_canonical_gap(self):
        for venue in VENUES:
            result = mapped(venue)
            self.assertEqual({d["disposition"] for d in result["dispositions"]}, {"primary"})
            self.assertEqual(result["included_counts"], {"interest-and-fees-accrued": 1, "state-updated": 1})
            self.assertEqual(result["unsupported_counts"], {"attribution:interest-and-fees-accrued:actor": 1,
                                                            "attribution:state-updated:actor": 1})
            self.assertFalse([key for key in result["unsupported_counts"] if ACCRUAL in key or STATE in key])

    def test_limitations_read_ratios_and_fees_natively_and_name_no_cause(self):
        for venue in VENUES:
            result = mapped(venue)
            for action, expected in LIMITATIONS.items():
                evidence = mapping_for(result, row(result, action))
                self.assertEqual(evidence["limitations"], expected, (venue, action))
                text = " ".join(evidence["limitations"]).lower()
                for phrase in ("caused by", "because of", "collected by", "paid to", "in default", "defaulted"):
                    self.assertNotIn(phrase, text)

    def test_rows_join_nothing_and_each_reads_only_its_own_log(self):
        for venue in VENUES:
            contexts, _ = accrual_inputs(venue)
            result = map_records(venue, contexts, [record(raw) for raw in source_raws()])
            self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))
            for action in ACCRUAL_ACTIONS:
                event = row(result, action)
                self.assertEqual(len(event["provenance"]["supporting_selectors"]), 1)
                self.assertEqual(event["provenance"]["supporting_selectors"][0][:16], "wildcat-context:")
            raws = source_raws()
            raws[3] = log(STATE, (), (RAY + 9 * 10 ** 22, 0), index=3)
            changed = map_records(venue, contexts, [record(raw) for raw in raws])
            self.assertEqual(row(changed, "interest-and-fees-accrued")["amounts"],
                             row(result, "interest-and-fees-accrued")["amounts"])
            self.assertEqual(row(changed, "state-updated")["amounts"][0]["base_units"], str(RAY + 9 * 10 ** 22))

    def test_mapping_is_independent_of_record_order(self):
        for venue in VENUES:
            contexts, _ = accrual_inputs(venue)
            records = [record(raw) for raw in source_raws()]
            self.assertEqual(map_records(venue, contexts, records), map_records(venue, contexts, list(reversed(records))))

    def test_moved_renamed_or_reindexed_field_declarations_refuse(self):
        accrual = list(DECLARED_FIELDS["interest-and-fees-accrued"])
        swapped = accrual[:2] + [accrual[3], accrual[2]] + accrual[4:]
        renamed = accrual[:5] + [("protocolFee", "uint256", False)]
        state = list(DECLARED_FIELDS["state-updated"])
        state_swapped = [("isDelinquent", "uint256", False), ("scaleFactor", "bool", False)]
        reindexed = [("scaleFactor", "uint256", True), state[1]]
        cases = (
            (ACCRUAL_TOPIC, swapped, log(ACCRUAL, (), ACCRUAL_FIELDS)),
            (ACCRUAL_TOPIC, renamed, log(ACCRUAL, (), ACCRUAL_FIELDS)),
            (STATE_TOPIC, state_swapped, log(STATE, (), (17, 1))),
            (STATE_TOPIC, reindexed, log(STATE, (17,), (1,))),
        )
        for venue in VENUES:
            contexts, _ = accrual_inputs(venue)
            for topic, inputs, raw in cases:
                with self.subTest(venue=venue, inputs=inputs), moved(venue, topic, inputs):
                    with self.assertRaisesRegex(TabulariumError, "declared field order"):
                        map_records(venue, contexts, [record(raw)])
            with self.subTest(venue=venue, case="unmoved"):
                map_records(venue, contexts, [record(log(ACCRUAL, (), ACCRUAL_FIELDS))])

    def test_retyped_field_declaration_refuses_at_the_topic_check(self):
        accrual = list(DECLARED_FIELDS["interest-and-fees-accrued"])
        retyped = accrual[:5] + [("protocolFees", "uint128", False)]
        for venue in VENUES:
            contexts, _ = accrual_inputs(venue)
            with self.subTest(venue=venue), moved(venue, ACCRUAL_TOPIC, retyped):
                with self.assertRaisesRegex(TabulariumError, "does not match its topic"):
                    map_records(venue, contexts, [record(log(ACCRUAL, (), ACCRUAL_FIELDS))])

    def test_non_boolean_is_delinquent_word_refuses(self):
        for venue in VENUES:
            contexts, _ = accrual_inputs(venue)
            for value in (2, 1 << 8, 1 << 255, (1 << 256) - 1):
                with self.subTest(venue=venue, value=value), \
                        self.assertRaisesRegex(TabulariumError, "boolean is neither zero nor one"):
                    map_records(venue, contexts, [record(log(STATE, (), (RAY, value)))])

    def test_truncated_extended_or_malformed_accrual_and_state_logs_refuse(self):
        mutations = (
            lambda r: r.update(data=r["data"][:-64]),                  # one data word short
            lambda r: r.update(data=r["data"][:-2]),                   # one byte short
            lambda r: r.update(data=r["data"] + word(9)),              # trailing word
            lambda r: r["topics"].append("0x" + word(7)),              # extra topic
            lambda r: r.update(data="0x" + "zz" * (len(r["data"]) // 2 - 1)),  # non-hex data
        )
        for venue in VENUES:
            contexts, _ = accrual_inputs(venue)
            for base in (log(ACCRUAL, (), ACCRUAL_FIELDS), log(STATE, (), (RAY, 1))):
                for position, mutate in enumerate(mutations):
                    raw = deepcopy(base)
                    mutate(raw)
                    with self.subTest(venue=venue, signature=TOPICS[base["topics"][0]], mutation=position), \
                            self.assertRaises(TabulariumError):
                        map_records(venue, contexts, [record(raw)])

    def test_unpinned_source_commit_stays_an_unsupported_decode_gap(self):
        for venue in VENUES:
            self.assertIsNone(abi_variant_for(venue, "market", "WildcatMarket", "f" * 40))
            contexts, records = accrual_inputs(venue)
            contexts[MARKET]["abi_variant"] = None
            result = map_records(venue, contexts, records)
            self.assertEqual(result["events"], ())
            self.assertEqual({d["disposition"] for d in result["dispositions"]}, {"unsupported-decode"})
            self.assertEqual(result["unsupported_counts"], {"decode:market:" + ACCRUAL_TOPIC: 1,
                                                            "decode:market:" + STATE_TOPIC: 1})

    def test_four_rules_declare_the_pinned_field_order_beside_the_released_ones(self):
        self.assertEqual(len(RULES), 29)
        for venue in VENUES:
            for action, family, signature, kinds in (
                    ("interest-and-fees-accrued", "interest-accrual", ACCRUAL, tuple(k for k, _ in ACCRUAL_AMOUNTS)),
                    ("state-updated", "pool-state", STATE, ("scale-factor",))):
                rule = RULES[(venue, action)]
                self.assertEqual(rule["rule"], "%s.%s.v1" % (venue, action))
                self.assertEqual((rule["role"], rule["family"], rule["party_roles"]), ("market", family, ("pool",)))
                self.assertEqual((rule["signature"], rule["amount_kinds"]), (signature, kinds))
                self.assertEqual(rule["instrument_type"], venue + "-market")
                pinned = VARIANTS[market_variant(venue)]["events"]["0x" + keccak256(signature.encode()).hex()]
                self.assertEqual(tuple((i["name"], i["type"], i["indexed"]) for i in pinned["abi"]["inputs"]),
                                 DECLARED_FIELDS[action])

    def test_accrual_release_builds_verifies_moves_and_counts_coverage(self):
        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                target = accrual_release(base, venue, source_raws())
                self.assertEqual(verifier.verify(target / "coverage.json").rows, 4)
                coverage = json.loads((target / "coverage.json").read_bytes())
                self.assertEqual(coverage["coverage"]["included_events"],
                                 {"deposit": 1, "interest-and-fees-accrued": 1, "state-updated": 1, "transfer": 1})
                unsupported = coverage["coverage"]["unsupported_events"]
                self.assertEqual(unsupported["attribution:interest-and-fees-accrued:actor"], 1)
                self.assertEqual(unsupported["attribution:state-updated:actor"], 1)
                self.assertFalse([key for key in unsupported if key.startswith(("canonical:", "decode:"))])
                self.assertEqual(coverage["versions"]["mapping_rules"],
                                 sorted(venue + "." + action + ".v1" for action in
                                        ("deposit", "interest-and-fees-accrued", "state-updated", "transfer")))
                source = json.loads((target / "source.json").read_bytes())
                decoded = [m["decoded"] for m in source["mapping_records"] if m["signature"] == STATE]
                self.assertEqual(decoded, [{"scaleFactor": str(RAY + 5 * 10 ** 22), "isDelinquent": False}])
                shutil.rmtree(base / "raw")
                moved_root = base / "moved"
                shutil.move(str(target), str(moved_root))
                self.assertEqual(verifier.verify(moved_root / "coverage.json").rows, 4)

    def test_coverage_counts_the_protocol_fee_asset_gap_per_release(self):
        raws = [log(ACCRUAL, (), ACCRUAL_FIELDS, index=0), log(STATE, (), (RAY, 1), index=1),
                log(ACCRUAL, (), ACCRUAL_FIELDS, index=2), log(STATE, (), (RAY, 0), index=3)]
        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                target = accrual_release(Path(temporary).resolve(), venue, raws, asset=False)
                coverage = json.loads((target / "coverage.json").read_bytes())
                unsupported = coverage["coverage"]["unsupported_events"]
                self.assertEqual(unsupported["attribution:interest-and-fees-accrued:asset"], 2)
                self.assertEqual(unsupported["attribution:interest-and-fees-accrued:actor"], 2)
                self.assertEqual(unsupported["attribution:state-updated:actor"], 2)
                self.assertNotIn("attribution:state-updated:asset", unsupported)
                self.assertEqual(coverage["coverage"]["included_events"],
                                 {"interest-and-fees-accrued": 2, "state-updated": 2})
                rows = [json.loads(line) for line in (target / "events.jsonl").read_text().splitlines()]
                self.assertEqual([r["amounts"][3]["asset"] for r in rows if r["action"].endswith(".interest-and-fees-accrued")],
                                 [None, None])
                self.assertEqual(verifier.verify(target / "coverage.json").rows, 4)

    def test_verify_refuses_edited_events_amounts_decoded_records_and_coverage(self):
        def accrual_of(rows_):
            return next(r for r in rows_ if r["action"].endswith(".interest-and-fees-accrued"))

        def state_of(rows_):
            return next(r for r in rows_ if r["action"].endswith(".state-updated"))

        def edit_fee(rows_, coverage):
            accrual_of(rows_)["amounts"][3]["base_units"] = "8"

        def edit_ray_asset(rows_, coverage):
            accrual_of(rows_)["amounts"][1]["asset"] = ASSET

        def edit_kind(rows_, coverage):
            state_of(rows_)["amounts"][0]["kind"] = "ray"

        def edit_family(rows_, coverage):
            state_of(rows_)["event_family"] = "interest-accrual"

        def edit_decoded_flag(source, coverage):
            item = next(m for m in source["mapping_records"] if m["signature"] == STATE)
            item["decoded"]["isDelinquent"] = True

        def edit_decoded_timestamp(source, coverage):
            item = next(m for m in source["mapping_records"] if m["signature"] == ACCRUAL)
            item["decoded"]["toTimestamp"] = str(ACCRUED_TO + 1)

        def edit_coverage_included(source, coverage):
            coverage["coverage"]["included_events"]["state-updated"] += 1

        def edit_coverage_gap(source, coverage):
            del coverage["coverage"]["unsupported_events"]["attribution:interest-and-fees-accrued:actor"]

        for name, edit in (("events.jsonl", edit_fee), ("events.jsonl", edit_ray_asset), ("events.jsonl", edit_kind),
                           ("events.jsonl", edit_family), ("source.json", edit_decoded_flag),
                           ("source.json", edit_decoded_timestamp), ("coverage.json", edit_coverage_included),
                           ("coverage.json", edit_coverage_gap)):
            with self.subTest(edit=edit.__name__), tempfile.TemporaryDirectory() as temporary:
                target = accrual_release(Path(temporary).resolve(), "wildcat-v2", source_raws())
                coverage_path = target / "coverage.json"
                coverage = json.loads(coverage_path.read_bytes())
                path = target / name
                if name == "events.jsonl":
                    rows_ = [json.loads(line) for line in path.read_text().splitlines()]
                    edit(rows_, coverage)
                    data = b"".join(canonical_json(r) + b"\n" for r in rows_)
                    coverage["canonical"].update(sha256=sha256_bytes(data), bytes=len(data))
                    path.write_bytes(data)
                elif name == "source.json":
                    source = json.loads(path.read_bytes())
                    edit(source, coverage)
                    data = canonical_json(source) + b"\n"
                    coverage["source"].update(sha256=sha256_bytes(data), bytes=len(data))
                    path.write_bytes(data)
                else:
                    edit(None, coverage)
                coverage_path.write_bytes(canonical_json(coverage) + b"\n")
                with self.assertRaises(TabulariumError):
                    verifier.verify(coverage_path)

    def test_published_wildcat_and_batch_specimens_rebuild_byte_identical(self):
        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                published = support.EXAMPLES / (venue + "-v0")
                expected = json.loads((published / "expected.json").read_bytes())
                rebuilt = base / "rebuilt"
                rebuilt.mkdir()
                self.assertEqual(build_pair(rebuilt, venue), expected)
                compare_pair(published, rebuilt)
                batches = base / "batches"
                batches.mkdir()
                built = build_specimen(batches, venue)
                self.assertEqual(built, json.loads((example_directory(venue) / "expected.json").read_bytes()))
                public = example_directory(venue) / BATCH_ROOT
                files = sorted(p.relative_to(public).as_posix() for p in public.rglob("*") if p.is_file())
                self.assertEqual(files, sorted(p.relative_to(batches / BATCH_ROOT).as_posix()
                                               for p in (batches / BATCH_ROOT).rglob("*") if p.is_file()))
                for relative in files:
                    self.assertEqual((batches / BATCH_ROOT / relative).read_bytes(), (public / relative).read_bytes(),
                                     relative)
                for root in (published / "release", published / "registry-context/release", public):
                    rules = json.loads((root / "coverage.json").read_bytes())["versions"]["mapping_rules"]
                    self.assertFalse([r for r in rules if r.endswith((".interest-and-fees-accrued.v1", ".state-updated.v1"))])

    def test_six_aave_and_euler_releases_and_schema_2_rebuild_byte_identical(self):
        for name, digest in SCHEMA_2_DIGESTS.items():
            self.assertEqual(hashlib.sha256((support.SCHEMAS / name).read_bytes()).hexdigest(), digest, name)
        for name in support.SHIPPED_RELEASES:
            with self.subTest(release=name), tempfile.TemporaryDirectory() as temporary:
                source = support.EXAMPLES / name
                destination = Path(temporary).resolve()
                for filename in ("source.json", "capture.json"):
                    (destination / filename).write_bytes((source / filename).read_bytes())
                manifest, rows_ = support.release_documents(name)
                builder.build(destination / "source.json", destination / "capture.json", destination / "events.jsonl",
                              destination / "coverage.json", manifest["release"],
                              adapter=manifest["versions"]["adapter"]["name"], event_schema=manifest["schema_version"])
                self.assertEqual(verifier.verify(destination / "coverage.json").rows, len(rows_))
                for filename in support.RELEASE_DATA_FILES:
                    self.assertEqual((destination / filename).read_bytes(), (source / filename).read_bytes(), filename)


if __name__ == "__main__":
    unittest.main()
