"""Hold the Python tuples, the JSON Schema branches and the parity oracle to the eight batch contexts."""

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
from test_wildcat_v3_schema_parity import ADDRESS, ASSET, HASH, OTHER, locked_oracle, specimen_manifest, specimen_rows
from wildcat_batch_fixtures import SOURCE_SPECIMENS, specimen
from wildcat_v3_fixtures import BATCH_ACTIONS

VENUES = ("wildcat-v1", "wildcat-v2")
# The study's table, stated independently of the production tuple tables.
BATCH_SPECIMENS = (
    ("withdrawal-batch-created", (), "WithdrawalBatchCreated(uint256)"),
    ("withdrawal-batch-payment", (("burned-scaled-claims", None), ("reserved-assets", ASSET)),
     "WithdrawalBatchPayment(uint256,uint256,uint256)"),
    ("withdrawal-batch-expired", (("scaled-claims", None), ("burned-scaled-claims", None), ("reserved-assets", ASSET)),
     "WithdrawalBatchExpired(uint256,uint256,uint256,uint256)"),
    ("withdrawal-batch-closed", (), "WithdrawalBatchClosed(uint256)"),
)
# The seventeen released declarations, frozen here so a changed table cannot pass its own oracle.
RELEASED = {
    "deposit": ("deposit", ("depositor", "minted-token-account"), ("assets", "scaled-claims"), "Deposit(address,uint256,uint256)"),
    "withdrawal-queued": ("exit-queue", ("withdrawing-account",), ("normalized-claims", "scaled-claims"), "WithdrawalQueued(uint256,address,uint256,uint256)"),
    "withdrawal-executed": ("exit-execute", ("beneficiary",), ("assets",), "WithdrawalExecuted(uint256,address,uint256)"),
    "transfer": ("transfer", ("from", "to"), ("market-token-claims",), "Transfer(address,address,uint256)"),
    "borrow": ("borrowing", ("pool",), ("assets",), "Borrow(uint256)"),
    "debt-repaid": ("repayment", ("payer", "pool"), ("assets",), "DebtRepaid(address,uint256)"),
    "market-closed": ("pool-state", ("pool",), (), "MarketClosed(uint256)"),
    "wrapper-deposit": ("deposit", ("caller", "owner"), ("market-token-assets", "wrapper-shares"), "Deposit(address,address,uint256,uint256)"),
    "wrapper-withdrawal": ("exit-execute", ("caller", "receiver", "owner"), ("market-token-assets", "wrapper-shares"), "Withdraw(address,address,address,uint256,uint256)"),
    "wrapper-transfer": ("transfer", ("from", "to"), ("wrapper-shares",), "Transfer(address,address,uint256)"),
}
EMPTY_AMOUNT_ACTIONS = ("market-closed", "withdrawal-batch-created", "withdrawal-batch-closed")


def batch_specimen_rows():
    rows = []
    for venue in VENUES:
        for action, amounts, signature in BATCH_SPECIMENS:
            index = 40 + len(rows)
            rows.append({
                "schema_version": 3,
                "id": "tabularium:%s:%s:%d" % (venue, HASH, index),
                "event_family": "exit-queue",
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


class BatchSchemaParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        oracle = locked_oracle()
        cls.oracle = oracle
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

    def test_eight_batch_contexts_validate_under_schema_and_python(self):
        rows = batch_specimen_rows()
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({(row["venue"], row["action"]) for row in rows}), 8)
        for row in rows:
            with self.subTest(action=row["action"]):
                self.assert_event_parity(row, True)

    def test_actual_batch_mappings_and_burn_joins_validate(self):
        for venue in VENUES:
            for name in SOURCE_SPECIMENS:
                result = map_records(venue, *specimen(venue, name))
                self.assertTrue(result["events"])
                for row in result["events"]:
                    with self.subTest(venue=venue, specimen=name, action=row["action"]):
                        self.assert_event_parity(row, True)
                joined = [m for m in result["mapping_records"] if m["join"]]
                self.assertTrue(joined, name)
                for evidence in joined:
                    self.assertEqual(evidence["join"]["rule"], "adjacent-market-burn")

    def test_python_tuples_schema_branches_and_enums_name_the_same_four_actions_per_generation(self):
        rule_enum = self.event_document["properties"]["provenance"]["properties"]["mapping_rule"]["enum"]
        coverage_enum = self.coverage_document["properties"]["versions"]["properties"]["mapping_rules"]["items"]["enum"]
        self.assertEqual(rule_enum, sorted(rule_enum))
        self.assertEqual(coverage_enum, sorted(coverage_enum))
        for venue in VENUES:
            branches = [b for b in self.event_document["oneOf"] if b["properties"].get("venue", {}).get("const") == venue]
            self.assertEqual(len(branches), 11 if venue == "wildcat-v1" else 14)
            coverage_branch = next(b for b in self.coverage_document["oneOf"]
                                   if b["properties"]["versions"]["properties"]["adapter"]["properties"]["name"]["const"] == venue)
            venue_rules = coverage_branch["properties"]["versions"]["properties"]["mapping_rules"]["items"]["enum"]
            self.assertEqual(len(venue_rules), len(branches))
            table = tuples(venue)
            self.assertEqual(len(table), len(branches))
            for action, amounts, signature in BATCH_SPECIMENS:
                rule = "%s.%s.v1" % (venue, action)
                self.assertEqual(RULES[(venue, action)]["family"], "exit-queue")
                self.assertEqual(RULES[(venue, action)]["party_roles"], ("pool",))
                self.assertEqual(RULES[(venue, action)]["amount_kinds"], tuple(kind for kind, _ in amounts))
                self.assertEqual(RULES[(venue, action)]["signature"], signature)
                family, roles, units = table[action]
                self.assertEqual((family, roles), ("exit-queue", ("pool",)))
                self.assertEqual(tuple(kind for kind, _ in units), tuple(kind for kind, _ in amounts))
                self.assertEqual([has_asset for _, has_asset in units],
                                 [None if kind == "reserved-assets" else False for kind, _ in amounts])
                branch = branch_for(self.event_document, venue, action)
                self.assertEqual(branch["properties"]["event_family"], {"const": "exit-queue"})
                provenance = branch["properties"]["provenance"]["properties"]
                self.assertEqual(provenance["mapping_rule"], {"const": rule})
                self.assertEqual(provenance["source_entity"], {"const": signature})
                parties = branch["properties"]["parties"]
                self.assertEqual((parties["minItems"], parties["maxItems"], parties["items"]), (1, 1, False))
                self.assertEqual(parties["prefixItems"][0]["properties"]["role"], {"const": "pool"})
                schema_amounts = branch["properties"]["amounts"]
                self.assertEqual((schema_amounts["minItems"], schema_amounts["maxItems"], schema_amounts["items"]),
                                 (len(amounts), len(amounts), False))
                kinds = [item["properties"]["kind"]["const"] for item in schema_amounts.get("prefixItems", [])]
                self.assertEqual(kinds, [kind for kind, _ in amounts])
                for item, (kind, _) in zip(schema_amounts.get("prefixItems", []), amounts):
                    asset = item["properties"]["asset"]
                    if kind == "reserved-assets":
                        self.assertIn("oneOf", asset)
                    else:
                        self.assertEqual(asset, {"type": "null"})
                self.assertIn(rule, rule_enum)
                self.assertIn(rule, coverage_enum)
                self.assertIn(rule, venue_rules)
        self.assertEqual(len(rule_enum), 36)
        self.assertEqual(len(coverage_enum), 36)

    def test_only_created_closed_and_market_closed_admit_empty_amounts(self):
        for row in specimen_rows() + batch_specimen_rows():
            row["amounts"] = []
            with self.subTest(action=row["action"]):
                self.assert_event_parity(row, row["action"].split(".", 1)[1] in EMPTY_AMOUNT_ACTIONS)

    def test_batch_amount_order_kind_and_asset_nullability_are_closed(self):
        for original in batch_specimen_rows():
            if not original["amounts"]:
                row = copy.deepcopy(original)
                row["amounts"].append({"kind": "reserved-assets", "base_units": "1", "asset": ASSET})
                self.assert_event_parity(row, False)
                continue
            row = copy.deepcopy(original)
            row["amounts"].reverse()
            self.assert_event_parity(row, False)
            row = copy.deepcopy(original)
            row["amounts"].pop()
            self.assert_event_parity(row, False)
            for position, amount in enumerate(original["amounts"]):
                row = copy.deepcopy(original)
                row["amounts"][position]["kind"] = "assets"
                self.assert_event_parity(row, False)
                row = copy.deepcopy(original)
                row["amounts"][position]["asset"] = ADDRESS if amount["asset"] is None else None
                self.assert_event_parity(row, amount["kind"] == "reserved-assets")
                row = copy.deepcopy(original)
                row["amounts"][position]["base_units"] = "07"
                self.assert_event_parity(row, False)

    def test_expiry_cannot_become_a_party_amount_or_row_field(self):
        for original in batch_specimen_rows():
            row = copy.deepcopy(original)
            row["parties"].append({"role": "expiry", "address": OTHER})
            self.assert_event_parity(row, False)
            row = copy.deepcopy(original)
            row["parties"][0]["role"] = "expiry"
            self.assert_event_parity(row, False)
            row = copy.deepcopy(original)
            row["amounts"].append({"kind": "expiry", "base_units": "1700000000", "asset": None})
            self.assert_event_parity(row, False)
            for field in ("expiry", "batch"):
                row = copy.deepcopy(original)
                row[field] = "1700000000"
                self.assert_event_parity(row, False)
                row = copy.deepcopy(original)
                row["provenance"][field] = "1700000000"
                self.assert_event_parity(row, False)

    def test_batch_rows_refuse_wrong_family_rule_signature_instrument_and_venue(self):
        for original in batch_specimen_rows():
            other_venue = "wildcat-v1" if original["venue"] == "wildcat-v2" else "wildcat-v2"
            action = original["action"].split(".", 1)[1]
            swapped = {"withdrawal-batch-created": "WithdrawalBatchClosed(uint256)",
                       "withdrawal-batch-closed": "WithdrawalBatchCreated(uint256)",
                       "withdrawal-batch-payment": "WithdrawalBatchExpired(uint256,uint256,uint256,uint256)",
                       "withdrawal-batch-expired": "WithdrawalBatchPayment(uint256,uint256,uint256)"}[action]
            for mutate in (
                    lambda r: r.update(event_family="pool-state"),
                    lambda r: r.update(event_family="exit-execute"),
                    lambda r: r.update(action=other_venue + "." + action),
                    lambda r: r["provenance"].update(mapping_rule=other_venue + "." + action + ".v1"),
                    lambda r: r["provenance"].update(mapping_rule=original["venue"] + "." + action + ".v2"),
                    lambda r: r["provenance"].update(source_entity=swapped),
                    lambda r: r["instrument"].update(type="wildcat-v2-wrapper"),
                    lambda r: r["instrument"].update(type=other_venue + "-market"),
                    lambda r: r["parties"].append({"role": "pool", "address": ADDRESS}),
                    lambda r: r.update(parties=[])):
                row = copy.deepcopy(original)
                mutate(row)
                with self.subTest(action=original["action"], row=row["event_family"]):
                    self.assert_event_parity(row, False)

    def test_a_burn_selector_on_a_batch_row_stays_journal_qualified_and_unique(self):
        for original in batch_specimen_rows():
            row = copy.deepcopy(original)
            row["provenance"]["supporting_selectors"].append("wildcat-journal:" + "bc" * 32)
            self.assert_event_parity(row, True)
            row["provenance"]["supporting_selectors"].append("wildcat-journal:" + "bc" * 32)
            self.assert_event_parity(row, False)
            row = copy.deepcopy(original)
            row["provenance"]["supporting_selectors"].append("wildcat-burn:" + "bc" * 32)
            self.assert_event_parity(row, False)

    def test_the_seventeen_released_declarations_keep_their_tuples(self):
        released = {key: value for key, value in RULES.items() if key[1] not in BATCH_ACTIONS}
        self.assertEqual(len(released), 17)
        for (venue, action), rule in released.items():
            family, roles, kinds, signature = RELEASED[action]
            self.assertEqual(rule["family"], family)
            self.assertEqual(rule["party_roles"], roles)
            self.assertEqual(rule["amount_kinds"], kinds)
            self.assertEqual(rule["signature"], signature)
            self.assertEqual(rule["rule"], "%s.%s.v1" % (venue, action))
            self.assertIn(rule["rule"], self.event_document["properties"]["provenance"]["properties"]["mapping_rule"]["enum"])
        for row in specimen_rows():
            self.assert_event_parity(row, True)

    def test_coverage_manifest_admits_batch_rules_and_refuses_an_unknown_rule(self):
        for venue in VENUES:
            manifest = specimen_manifest(venue)
            rules = sorted(rule["rule"] for key, rule in RULES.items() if key[0] == venue)
            manifest["versions"]["mapping_rules"] = rules
            self.assert_manifest_parity(manifest, True)
            manifest["coverage"]["unsupported_events"]["attribution:withdrawal-batch-payment:burn"] = 1
            manifest["coverage"]["unsupported_events"]["attribution:transfer:unclaimed-burn"] = 1
            self.assert_manifest_parity(manifest, True)
            manifest["versions"]["mapping_rules"] = sorted(rules + [venue + ".withdrawal-batch-paid.v1"])
            self.assert_manifest_parity(manifest, False)
            manifest["versions"]["mapping_rules"] = sorted(rules + [venue + ".withdrawal-batch-payment.v2"])
            self.assert_manifest_parity(manifest, False)


if __name__ == "__main__":
    unittest.main()
