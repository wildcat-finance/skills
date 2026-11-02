"""Hold the Python tuples, the JSON Schema branches and the parity oracle to the four accrual-state contexts."""

import copy
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "scripts"))
import support
from tabularium_lib import release_v2
from tabularium_lib.core import TabulariumError
from tabularium_lib.wildcat_rows import map_records
from tabularium_lib.wildcat_rules import RULES
from tabularium_lib.wildcat_validation import tuples
from test_wildcat_v3_schema_parity import ADDRESS, ASSET, HASH, OTHER, locked_oracle, specimen_manifest
from wildcat_v3_fixtures import MARKET, accrual_inputs

VENUES = ("wildcat-v1", "wildcat-v2")
# The study's table, stated independently of the production tuple tables:
# None marks an assetless ray kind and ASSET the underlying-unit fee.
ACCRUAL_SPECIMENS = (
    ("interest-and-fees-accrued", "interest-accrual",
     (("scale-factor", None), ("base-interest-ray", None), ("delinquency-fee-ray", None), ("protocol-fees", ASSET)),
     "InterestAndFeesAccrued(uint256,uint256,uint256,uint256,uint256,uint256)"),
    ("state-updated", "pool-state", (("scale-factor", None),), "StateUpdated(uint256,bool)"),
)
NATIVE_STATE_NAMES = ("fromTimestamp", "toTimestamp", "isDelinquent", "from-timestamp", "to-timestamp",
                      "is-delinquent", "from_timestamp", "to_timestamp", "is_delinquent")


def accrual_specimen_rows():
    rows = []
    for venue in VENUES:
        for action, family, amounts, signature in ACCRUAL_SPECIMENS:
            index = 60 + len(rows)
            rows.append({
                "schema_version": 3,
                "id": "tabularium:%s:%s:%d" % (venue, HASH, index),
                "event_family": family,
                "action": "%s.%s" % (venue, action),
                "venue": venue,
                "chain": "ethereum-mainnet",
                "transaction": {"hash": HASH, "block_number": 20, "block_hash": HASH, "transaction_index": 1, "log_index": index, "timestamp": None},
                "parties": [{"role": "pool", "address": ADDRESS}],
                "instrument": {"type": venue + "-market", "id": ADDRESS},
                "amounts": [{"kind": kind, "base_units": "7", "asset": asset} for kind, asset in amounts],
                "provenance": {
                    "adapter": venue, "adapter_version": "1.0.0", "protocol_generation": venue,
                    "source_api": "ethereum-json-rpc", "mapping_rule": "%s.%s.v1" % (venue, action),
                    "source_kind": "ethereum-log", "source_contract": ADDRESS,
                    "source_entity": signature, "source_id": "%s:%d" % (HASH, index),
                    "source_selector": "wildcat-journal:" + ("%064x" % index),
                    "supporting_selectors": ["wildcat-context:" + "ab" * 32],
                },
                "native_record": {"address": ADDRESS, "blockNumber": "0x14", "blockHash": HASH, "transactionHash": HASH, "transactionIndex": "0x1", "logIndex": hex(index), "topics": [], "data": "0x", "removed": False},
            })
    return rows


def branch_for(schema, venue, action):
    branches = [b for b in schema["oneOf"] if b["properties"].get("venue", {}).get("const") == venue
                and b["properties"].get("action", {}).get("const") == venue + "." + action]
    if len(branches) != 1:
        raise AssertionError("expected one branch for %s.%s, found %d" % (venue, action, len(branches)))
    return branches[0]


class AccrualSchemaParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        oracle = locked_oracle()
        cls.event_document = support.event_schema(3)
        cls.coverage_document = support.coverage_schema(3)
        oracle.Draft202012Validator.check_schema(cls.event_document)
        oracle.Draft202012Validator.check_schema(cls.coverage_document)
        cls.event = oracle.Draft202012Validator(cls.event_document)
        cls.coverage = oracle.Draft202012Validator(cls.coverage_document)

    def assert_event_parity(self, row, accepted):
        errors = list(self.event.iter_errors(row))
        try:
            release_v2.validate_event_row(row, release_v2.ADAPTERS[row["venue"]], 3)
        except TabulariumError as error:
            refusal = str(error)
        else:
            refusal = None
        self.assertEqual(not errors, accepted, "schema: " + "; ".join(error.message for error in errors))
        self.assertEqual(refusal is None, accepted, "Python: %s" % refusal)

    def assert_manifest_parity(self, manifest, accepted):
        errors = list(self.coverage.iter_errors(manifest))
        try:
            release_v2.validate_manifest(manifest, 3)
        except TabulariumError as error:
            refusal = str(error)
        else:
            refusal = None
        self.assertEqual(not errors, accepted, "schema: " + "; ".join(error.message for error in errors))
        self.assertEqual(refusal is None, accepted, "Python: %s" % refusal)

    def test_four_accrual_state_contexts_validate_under_schema_and_python(self):
        rows = accrual_specimen_rows()
        self.assertEqual(len(rows), 4)
        self.assertEqual(len({(row["venue"], row["action"]) for row in rows}), 4)
        for row in rows:
            with self.subTest(action=row["action"]):
                self.assert_event_parity(row, True)
        for row in accrual_specimen_rows():
            if row["action"].endswith(".interest-and-fees-accrued"):
                row["amounts"][3]["asset"] = None
                self.assert_event_parity(row, True)

    def test_actual_accrual_mappings_validate_with_and_without_an_asset(self):
        for venue in VENUES:
            for asset in (ASSET, None):
                contexts, records = accrual_inputs(venue)
                contexts[MARKET]["asset"] = asset
                result = map_records(venue, contexts, records)
                self.assertEqual(len(result["events"]), 2)
                for row in result["events"]:
                    with self.subTest(venue=venue, asset=asset, action=row["action"]):
                        self.assert_event_parity(row, True)

    def test_python_tuples_schema_branches_and_enums_name_the_same_two_actions_per_generation(self):
        rule_enum = self.event_document["properties"]["provenance"]["properties"]["mapping_rule"]["enum"]
        coverage_enum = self.coverage_document["properties"]["versions"]["properties"]["mapping_rules"]["items"]["enum"]
        self.assertEqual(rule_enum, sorted(rule_enum))
        self.assertEqual(coverage_enum, sorted(coverage_enum))
        self.assertEqual(len(rule_enum), 40)
        self.assertEqual(len(coverage_enum), 40)
        for venue in VENUES:
            coverage_branch = next(b for b in self.coverage_document["oneOf"]
                                   if b["properties"]["versions"]["properties"]["adapter"]["properties"]["name"]["const"] == venue)
            venue_rules = coverage_branch["properties"]["versions"]["properties"]["mapping_rules"]["items"]["enum"]
            table = tuples(venue)
            for action, family, amounts, signature in ACCRUAL_SPECIMENS:
                rule = "%s.%s.v1" % (venue, action)
                specification = RULES[(venue, action)]
                self.assertEqual((specification["family"], specification["party_roles"], specification["signature"]),
                                 (family, ("pool",), signature))
                self.assertEqual(specification["amount_kinds"], tuple(kind for kind, _ in amounts))
                table_family, roles, units = table[action]
                self.assertEqual((table_family, roles), (family, ("pool",)))
                self.assertEqual([(kind, has_asset) for kind, has_asset in units],
                                 [(kind, None if asset else False) for kind, asset in amounts])
                branch = branch_for(self.event_document, venue, action)
                self.assertEqual(branch["properties"]["event_family"], {"const": family})
                self.assertEqual(branch["properties"]["instrument"]["properties"]["type"], {"const": venue + "-market"})
                provenance = branch["properties"]["provenance"]["properties"]
                self.assertEqual(provenance["mapping_rule"], {"const": rule})
                self.assertEqual(provenance["source_entity"], {"const": signature})
                parties = branch["properties"]["parties"]
                self.assertEqual((parties["minItems"], parties["maxItems"], parties["items"]), (1, 1, False))
                self.assertEqual(parties["prefixItems"][0]["properties"]["role"], {"const": "pool"})
                schema_amounts = branch["properties"]["amounts"]
                self.assertEqual((schema_amounts["minItems"], schema_amounts["maxItems"], schema_amounts["items"]),
                                 (len(amounts), len(amounts), False))
                self.assertEqual([item["properties"]["kind"]["const"] for item in schema_amounts["prefixItems"]],
                                 [kind for kind, _ in amounts])
                for item, (kind, asset) in zip(schema_amounts["prefixItems"], amounts):
                    if asset is None:
                        self.assertEqual(item["properties"]["asset"], {"type": "null"}, kind)
                    else:
                        self.assertIn("oneOf", item["properties"]["asset"], kind)
                for enum in (rule_enum, coverage_enum, venue_rules):
                    self.assertIn(rule, enum)

    def test_amount_order_kind_asset_and_lexical_form_are_closed(self):
        for original in accrual_specimen_rows():
            if len(original["amounts"]) > 1:
                row = copy.deepcopy(original)
                row["amounts"].reverse()
                self.assert_event_parity(row, False)
            for mutate in (lambda r: r["amounts"].pop(), lambda r: r.update(amounts=[]),
                           lambda r: r["amounts"].append({"kind": "scale-factor", "base_units": "7", "asset": None})):
                row = copy.deepcopy(original)
                mutate(row)
                self.assert_event_parity(row, False)
            for position, amount in enumerate(original["amounts"]):
                for kind in ("ray", "assets", "scaled-claims", "scaleFactor"):
                    row = copy.deepcopy(original)
                    row["amounts"][position]["kind"] = kind
                    self.assert_event_parity(row, False)
                row = copy.deepcopy(original)
                row["amounts"][position]["asset"] = ADDRESS if amount["asset"] is None else None
                self.assert_event_parity(row, amount["kind"] == "protocol-fees")
                for value in ("07", "-1", "1.0", str(1 << 256)):
                    row = copy.deepcopy(original)
                    row["amounts"][position]["base_units"] = value
                    self.assert_event_parity(row, False)

    def test_unit_named_amounts_from_the_rejected_candidate_refuse(self):
        for original in accrual_specimen_rows():
            row = copy.deepcopy(original)
            for amount in row["amounts"]:
                amount["kind"] = "assets" if amount["kind"] == "protocol-fees" else "ray"
            self.assert_event_parity(row, False)

    def test_timestamps_and_is_delinquent_cannot_become_a_party_amount_or_row_field(self):
        for original in accrual_specimen_rows():
            for name in NATIVE_STATE_NAMES:
                with self.subTest(action=original["action"], name=name):
                    row = copy.deepcopy(original)
                    row["parties"].append({"role": name, "address": OTHER})
                    self.assert_event_parity(row, False)
                    row = copy.deepcopy(original)
                    row["parties"][0]["role"] = name
                    self.assert_event_parity(row, False)
                    row = copy.deepcopy(original)
                    row["amounts"].append({"kind": name, "base_units": "1700000000", "asset": None})
                    self.assert_event_parity(row, False)
                    row = copy.deepcopy(original)
                    row[name] = "1700000000"
                    self.assert_event_parity(row, False)
                    row = copy.deepcopy(original)
                    row["provenance"][name] = True
                    self.assert_event_parity(row, False)

    def test_rows_refuse_wrong_family_rule_signature_instrument_and_venue(self):
        swapped = {"interest-and-fees-accrued": ("pool-state", "StateUpdated(uint256,bool)"),
                   "state-updated": ("interest-accrual",
                                     "InterestAndFeesAccrued(uint256,uint256,uint256,uint256,uint256,uint256)")}
        for original in accrual_specimen_rows():
            other_venue = "wildcat-v1" if original["venue"] == "wildcat-v2" else "wildcat-v2"
            action = original["action"].split(".", 1)[1]
            family, signature = swapped[action]
            for mutate in (
                    lambda r: r.update(event_family=family),
                    lambda r: r.update(event_family="interest-accrued"),
                    lambda r: r.update(action=other_venue + "." + action),
                    lambda r: r["provenance"].update(mapping_rule=other_venue + "." + action + ".v1"),
                    lambda r: r["provenance"].update(mapping_rule=original["venue"] + "." + action + ".v2"),
                    lambda r: r["provenance"].update(source_entity=signature),
                    lambda r: r["provenance"].update(source_entity="MarketClosed(uint256)"),
                    lambda r: r["instrument"].update(type="wildcat-v2-wrapper"),
                    lambda r: r["instrument"].update(type=other_venue + "-market"),
                    lambda r: r["parties"].append({"role": "pool", "address": ADDRESS}),
                    lambda r: r.update(parties=[])):
                row = copy.deepcopy(original)
                mutate(row)
                with self.subTest(action=original["action"]):
                    self.assert_event_parity(row, False)

    def test_coverage_manifest_admits_the_accrual_rules_and_gaps_and_refuses_an_unknown_rule(self):
        for venue in VENUES:
            manifest = specimen_manifest(venue)
            rules = sorted(rule["rule"] for key, rule in RULES.items() if key[0] == venue)
            self.assertIn(venue + ".interest-and-fees-accrued.v1", rules)
            self.assertIn(venue + ".state-updated.v1", rules)
            manifest["versions"]["mapping_rules"] = rules
            self.assert_manifest_parity(manifest, True)
            for gap in ("attribution:interest-and-fees-accrued:actor", "attribution:interest-and-fees-accrued:asset",
                        "attribution:state-updated:actor"):
                manifest["coverage"]["unsupported_events"][gap] = 1
            self.assert_manifest_parity(manifest, True)
            for unknown in (venue + ".interest-accrued.v1", venue + ".state-updated.v2",
                            venue + ".interest-and-fees-accrued.v2"):
                with self.subTest(venue=venue, rule=unknown):
                    manifest["versions"]["mapping_rules"] = sorted(rules + [unknown])
                    self.assert_manifest_parity(manifest, False)


if __name__ == "__main__":
    unittest.main()
