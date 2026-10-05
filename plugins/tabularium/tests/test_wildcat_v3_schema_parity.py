"""Execute the locked schema oracle over Wildcat native-role row tuples.

Parity compares strict JSON rows with integer metadata. JSON Schema defines
integral floats as integers; Python refuses them at the metadata input gate.
That lexical input gate is tested separately and is not a schema claim.
"""

import copy
import importlib.metadata
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
if __package__:
    from . import support
else:
    import support
from tabularium_lib import builder, release_v2, verifier
from tabularium_lib.core import TabulariumError


LOCKED_ORACLE = {
    "attrs": "26.1.0",
    "jsonschema": "4.25.1",
    "jsonschema-specifications": "2025.9.1",
    "referencing": "0.37.0",
    "rpds-py": "2026.6.3",
    "typing-extensions": "4.16.0",
}
ADDRESS = "0x" + "11" * 20
OTHER = "0x" + "22" * 20
ASSET = "0x" + "33" * 20
HASH = "0x" + "44" * 32
MAX_SAFE = 9_007_199_254_740_991
MAX_UINT256 = (1 << 256) - 1

# These specimens state the study's roles and units independently of the
# production tuple table; a changed table cannot make its own oracle pass.
MARKET_SPECIMENS = (
    ("deposit", "deposit", ("depositor", "minted-token-account"), (("assets", ASSET), ("scaled-claims", None)), "Deposit(address,uint256,uint256)"),
    ("withdrawal-queued", "exit-queue", ("withdrawing-account",), (("normalized-claims", ADDRESS), ("scaled-claims", None)), "WithdrawalQueued(uint256,address,uint256,uint256)"),
    ("withdrawal-executed", "exit-execute", ("beneficiary",), (("assets", ASSET),), "WithdrawalExecuted(uint256,address,uint256)"),
    ("transfer", "transfer", ("from", "to"), (("market-token-claims", ADDRESS),), "Transfer(address,address,uint256)"),
    ("borrow", "borrowing", ("pool",), (("assets", ASSET),), "Borrow(uint256)"),
    ("debt-repaid", "repayment", ("payer", "pool"), (("assets", ASSET),), "DebtRepaid(address,uint256)"),
    ("market-closed", "pool-state", ("pool",), (), "MarketClosed(uint256)"),
)
WRAPPER_SPECIMENS = (
    ("wrapper-deposit", "deposit", ("caller", "owner"), (("market-token-assets", ASSET), ("wrapper-shares", ADDRESS)), "Deposit(address,address,uint256,uint256)"),
    ("wrapper-withdrawal", "exit-execute", ("caller", "receiver", "owner"), (("market-token-assets", ASSET), ("wrapper-shares", ADDRESS)), "Withdraw(address,address,address,uint256,uint256)"),
    ("wrapper-transfer", "transfer", ("from", "to"), (("wrapper-shares", ADDRESS),), "Transfer(address,address,uint256)"),
)


def locked_oracle():
    oracle = support.import_jsonschema()
    for distribution, expected in LOCKED_ORACLE.items():
        actual = importlib.metadata.version(distribution)
        if actual != expected:
            raise RuntimeError("schema parity requires %s==%s; found %s" % (distribution, expected, actual))
    return oracle


def specimen_rows():
    rows = []
    for venue in ("wildcat-v1", "wildcat-v2"):
        specifications = MARKET_SPECIMENS + (WRAPPER_SPECIMENS if venue == "wildcat-v2" else ())
        for action, family, roles, amounts, signature in specifications:
            index = len(rows)
            rule = "%s.%s.v1" % (venue, action)
            rows.append({
                "schema_version": 3,
                "id": "tabularium:%s:%s:%d" % (venue, HASH, index),
                "event_family": family,
                "action": "%s.%s" % (venue, action),
                "venue": venue,
                "chain": "ethereum-mainnet",
                "transaction": {"hash": HASH, "block_number": 20, "block_hash": HASH, "transaction_index": 1, "log_index": index, "timestamp": None},
                "parties": [{"role": role, "address": ADDRESS if role in ("pool", "depositor", "minted-token-account") else OTHER} for role in roles],
                "instrument": {"type": venue + ("-wrapper" if action.startswith("wrapper-") else "-market"), "id": ADDRESS},
                "amounts": [{"kind": kind, "base_units": "7", "asset": asset} for kind, asset in amounts],
                "provenance": {
                    "adapter": venue, "adapter_version": "1.0.0", "protocol_generation": venue,
                    "source_api": "ethereum-json-rpc", "mapping_rule": rule,
                    "source_kind": "ethereum-log", "source_contract": ADDRESS,
                    "source_entity": signature, "source_id": "%s:%d" % (HASH, index),
                    "source_selector": "wildcat-journal:" + ("%064x" % index),
                    "supporting_selectors": ["wildcat-context:" + "ab" * 32],
                },
                "native_record": {"address": ADDRESS, "blockNumber": "0x14", "blockHash": HASH, "transactionHash": HASH, "transactionIndex": "0x1", "logIndex": hex(index), "topics": [], "data": "0x", "removed": False},
            })
    return rows


def specimen_manifest(venue):
    rows = [row for row in specimen_rows() if row["venue"] == venue]
    capture = {"scope": {"chain": "ethereum-mainnet", "deployment": venue + "-constructed-specimen"}}
    class Mapping:
        events = rows
        mapped_counts = {row["action"]: 1 for row in rows}
        unmapped_counts = {"attribution:borrow:borrower": 1}
    return release_v2.make_manifest(
        venue + "-constructed-schema-specimen", venue,
        "source.json", b"{}", "capture.json", b"{}", "events.jsonl", b"{}\n",
        capture, Mapping(), 3,
    )


class SchemaParityTests(unittest.TestCase):
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

    def test_all_seventeen_exact_native_role_contexts_validate(self):
        rows = specimen_rows()
        self.assertEqual(len(rows), 17)
        self.assertEqual(len({(row["venue"], row["action"]) for row in rows}), 17)
        for row in rows:
            with self.subTest(action=row["action"]):
                self.assert_event_parity(row, True)

    def test_all_seventeen_actual_mappings_and_sanctions_join_validate(self):
        from wildcat_v3_fixtures import all_primary_events, constructed_inputs
        from tabularium_lib.wildcat_rows import map_records
        rows = all_primary_events()
        self.assertEqual(len(rows), 17)
        for row in rows:
            with self.subTest(action=row["action"]):
                self.assert_event_parity(row, True)
        for venue in ("wildcat-v1", "wildcat-v2"):
            result = map_records(venue, *constructed_inputs(venue, routing=True))
            row = next(row for row in result["events"] if row["action"].endswith(".withdrawal-executed"))
            self.assertEqual([party["role"] for party in row["parties"]], ["beneficiary", "escrow-recipient"])
            self.assert_event_parity(row, True)

    def test_missing_underlying_asset_stays_null_with_a_qualified_gap(self):
        from wildcat_v3_fixtures import MARKET, constructed_inputs
        from tabularium_lib.wildcat_rows import map_records
        for venue in ("wildcat-v1", "wildcat-v2"):
            contexts, records = constructed_inputs(venue)
            contexts[MARKET]["asset"] = None
            result = map_records(venue, contexts, records)
            for row in result["events"]:
                self.assert_event_parity(row, True)
                for amount in row["amounts"]:
                    if amount["kind"] == "assets":
                        self.assertIsNone(amount["asset"])
            self.assertTrue(any(key.startswith("attribution:") and key.endswith(":asset") for key in result["unsupported_counts"]))

    def test_party_and_amount_arrays_are_closed_ordered_native_tuples(self):
        for original in specimen_rows():
            for field in ("parties", "amounts"):
                for value in (None, {}, [], original[field] + original[field][:1]):
                    if value == original[field]:
                        continue
                    with self.subTest(action=original["action"], field=field, value=value):
                        row = copy.deepcopy(original)
                        row[field] = value
                        self.assert_event_parity(row, False)
                if len(original[field]) > 1:
                    row = copy.deepcopy(original)
                    row[field].reverse()
                    self.assert_event_parity(row, False)
            for field in ("parties", "amounts"):
                for position in range(len(original[field])):
                    row = copy.deepcopy(original)
                    row[field][position]["operator_note"] = "extra"
                    self.assert_event_parity(row, False)

    def test_no_borrower_executor_or_underlying_cash_role_is_invented(self):
        for original in specimen_rows():
            for position in range(len(original["parties"])):
                row = copy.deepcopy(original)
                row["parties"][position]["role"] = "borrower"
                self.assert_event_parity(row, False)
            for position in range(len(original["amounts"])):
                row = copy.deepcopy(original)
                row["amounts"][position]["kind"] = "assets" if original["amounts"][position]["kind"] != "assets" else "wrapper-shares"
                self.assert_event_parity(row, False)

    def test_scaled_claims_are_assetless_and_token_claims_name_an_asset(self):
        for original in specimen_rows():
            for position, amount in enumerate(original["amounts"]):
                row = copy.deepcopy(original)
                row["amounts"][position]["asset"] = ADDRESS if amount["asset"] is None else None
                self.assert_event_parity(row, amount["kind"] == "assets")

    def test_uint256_decimal_bounds_and_exact_lexical_forms_match(self):
        original = specimen_rows()[0]
        for value, accepted in (("0", True), (str(MAX_UINT256), True), (str(MAX_UINT256 + 1), False), ("9" * 78, False), ("1" * 79, False), ("07", False), ("-1", False), ("1.0", False), ("7\n", False), (7, False), (True, False), (None, False)):
            with self.subTest(value=value):
                row = copy.deepcopy(original)
                row["amounts"][0]["base_units"] = value
                self.assert_event_parity(row, accepted)

    def test_transaction_metadata_rejects_bool_float_overflow_and_null(self):
        for field in ("block_number", "transaction_index", "log_index"):
            for value, accepted in ((0, True), (MAX_SAFE, True), (MAX_SAFE + 1, False), (-1, False), (True, False), (1.5, False), ("1", False), (None, False)):
                row = copy.deepcopy(specimen_rows()[0])
                row["transaction"][field] = value
                self.assert_event_parity(row, accepted)
        row = copy.deepcopy(specimen_rows()[0])
        row["transaction"]["timestamp"] = "2026-10-04T00:00:00Z"
        self.assert_event_parity(row, False)

    def test_integral_float_metadata_refuses_at_the_python_input_gate(self):
        for field in ("block_number", "transaction_index", "log_index"):
            row = copy.deepcopy(specimen_rows()[0])
            row["transaction"][field] = 1.0
            self.assertFalse(list(self.event.iter_errors(row)))
            with self.assertRaisesRegex(TabulariumError, "safe JSON integer"):
                release_v2.validate_event_row(row, release_v2.ADAPTERS[row["venue"]], 3)

    def test_exact_generation_action_signature_and_instrument_tuple(self):
        for original in specimen_rows():
            for field, replacement in (("event_family", "interest-accrual"), ("action", original["venue"] + ".unsupported"), ("chain", "ethereum-sepolia")):
                row = copy.deepcopy(original)
                row[field] = replacement
                self.assert_event_parity(row, False)
            for field, replacement in (("adapter", "euler-v1"), ("adapter_version", "2.0.0"), ("protocol_generation", "wildcat-v2.5"), ("source_api", "euler-v3"), ("source_kind", "hosted-indexer-event"), ("source_entity", "Transfer(address,address,uint256)" if original["provenance"]["source_entity"] != "Transfer(address,address,uint256)" else "Borrow(uint256)"), ("mapping_rule", "euler-v1.borrow.v1")):
                row = copy.deepcopy(original)
                row["provenance"][field] = replacement
                self.assert_event_parity(row, False)
            row = copy.deepcopy(original)
            row["instrument"]["type"] = "wildcat-v2-wrapper" if original["instrument"]["type"] != "wildcat-v2-wrapper" else "wildcat-v2-market"
            self.assert_event_parity(row, False)

    def test_every_missing_or_unknown_row_and_provenance_field_refuses(self):
        for original in specimen_rows():
            for scope in (None, "provenance"):
                fields = original if scope is None else original[scope]
                for field in fields:
                    row = copy.deepcopy(original)
                    target = row if scope is None else row[scope]
                    del target[field]
                    if field == "venue" and scope is None:
                        self.assertTrue(list(self.event.iter_errors(row)))
                        with self.assertRaises(TabulariumError):
                            release_v2.validate_event_row(row, release_v2.ADAPTERS[original["venue"]], 3)
                    else:
                        self.assert_event_parity(row, False)
                row = copy.deepcopy(original)
                (row if scope is None else row[scope])["operator_note"] = "extra"
                self.assert_event_parity(row, False)

    def test_only_two_closure_tuples_admit_no_financial_amount(self):
        for row in specimen_rows():
            row["amounts"] = []
            self.assert_event_parity(row, row["action"].endswith(".market-closed"))
        for name in support.SHIPPED_RELEASES:
            _, rows = support.release_documents(name)
            row = rows[0]
            row["amounts"] = []
            version = row["schema_version"]
            self.assertTrue(list(self.oracle.Draft202012Validator(support.event_schema(version)).iter_errors(row)))
            with self.assertRaises(TabulariumError):
                release_v2.validate_event_row(row, release_v2.ADAPTERS[row["venue"]], version)

    def test_new_wildcat_families_cannot_widen_legacy_adapter_tuples(self):
        for name in support.SHIPPED_RELEASES:
            _, rows = support.release_documents(name)
            for family in ("deposit", "exit-queue", "exit-execute", "transfer", "pool-state"):
                row = copy.deepcopy(rows[0])
                row["event_family"] = family
                version = row["schema_version"]
                self.assertTrue(list(self.oracle.Draft202012Validator(support.event_schema(version)).iter_errors(row)))
                with self.assertRaisesRegex(TabulariumError, "legacy schema vocabulary"):
                    release_v2.validate_event_row(row, release_v2.ADAPTERS[row["venue"]], version)

    def test_zero_address_mints_burns_and_queue_endpoints_validate(self):
        for original in specimen_rows():
            if not original["action"].endswith(".transfer") and not original["action"].endswith(".wrapper-transfer"):
                continue
            for position in (0, 1):
                row = copy.deepcopy(original)
                row["parties"][position]["address"] = "0x" + "00" * 20
                self.assert_event_parity(row, True)

    def test_joined_escrow_recipient_is_limited_to_withdrawal_execution(self):
        for original in specimen_rows():
            row = copy.deepcopy(original)
            row["parties"].append({"role": "escrow-recipient", "address": OTHER})
            row["provenance"]["supporting_selectors"].append("wildcat-journal:" + "bc" * 32)
            self.assert_event_parity(row, row["action"].endswith(".withdrawal-executed"))

    def test_source_selectors_remain_class_qualified_and_unique(self):
        for field, values in (("source_selector", ("records/0", "wildcat-context:" + "ab" * 32, "wildcat-journal:" + "ab" * 32 + "\n")), ("supporting_selectors", (["plain"], ["wildcat-context:" + "ab" * 32] * 2, {}, None))):
            for value in values:
                row = copy.deepcopy(specimen_rows()[0])
                row["provenance"][field] = value
                self.assert_event_parity(row, False)

    def test_both_coverage_manifests_and_tuple_mutations_have_parity(self):
        for venue in ("wildcat-v1", "wildcat-v2"):
            original = specimen_manifest(venue)
            self.assert_manifest_parity(original, True)
            for field in ("evidence_class", "protocol_generation", "source_api", "chain"):
                manifest = copy.deepcopy(original)
                manifest["source"][field] = "unsupported"
                self.assert_manifest_parity(manifest, False)
            for scope, field, value in (("source", "bytes", True), ("canonical", "rows", -1), ("canonical", "bytes", MAX_SAFE + 1), ("versions", "event_schema", 2)):
                manifest = copy.deepcopy(original)
                manifest[scope][field] = value
                self.assert_manifest_parity(manifest, False)
            manifest = copy.deepcopy(original)
            manifest["versions"]["adapter"]["version"] = "2.0.0"
            self.assert_manifest_parity(manifest, False)
            manifest = copy.deepcopy(original)
            manifest["versions"]["mapping_rules"] = ["euler-v1.borrow.v1"]
            self.assert_manifest_parity(manifest, False)
            manifest = copy.deepcopy(original)
            manifest["known_gaps"].pop()
            self.assert_manifest_parity(manifest, False)

    def test_wildcat_schema2_and_generic_descriptor_only_routes_refuse(self):
        for venue in ("wildcat-v1", "wildcat-v2"):
            module = release_v2.ADAPTERS[venue]
            manifest = specimen_manifest(venue)
            manifest["schema_version"] = manifest["versions"]["event_schema"] = 2
            self.assertTrue(list(self.oracle.Draft202012Validator(support.coverage_schema(2)).iter_errors(manifest)))
            with self.assertRaisesRegex(TabulariumError, "schema 3"):
                release_v2.validate_manifest(manifest, 2)
            row = next(row for row in specimen_rows() if row["venue"] == venue)
            row["schema_version"] = 2
            self.assertTrue(list(self.oracle.Draft202012Validator(support.event_schema(2)).iter_errors(row)))
            with self.assertRaisesRegex(TabulariumError, "schema 3"):
                release_v2.validate_event_row(row, module, 2)
            with self.assertRaisesRegex(TabulariumError, "verified Alexandria raw release"):
                module.map_source({}, {}, 3)
            capture = {"schema_version": 2, "release": "constructed", "adapter": {"name": venue, "version": "1.0.0"}, "protocol_generation": venue, "source_api": "ethereum-json-rpc", "captured_at": "2026-10-04T00:00:00Z", "endpoint": "local", "request": {}, "scope": {}, "source": {"sha256": "0" * 64, "bytes": 0}}
            with self.assertRaisesRegex(TabulariumError, "wildcat-canonical"):
                release_v2.validate_capture(capture, {}, b"{}", 3)

    def test_all_six_historical_releases_rebuild_verify_and_validate(self):
        for name in support.SHIPPED_RELEASES:
            with self.subTest(release=name), tempfile.TemporaryDirectory() as temporary:
                source = support.EXAMPLES / name
                destination = Path(temporary).resolve()
                before = support.release_digests(name)
                for filename in ("source.json", "capture.json"):
                    (destination / filename).write_bytes((source / filename).read_bytes())
                manifest, rows = support.release_documents(name)
                version = manifest["schema_version"]
                builder.build(destination / "source.json", destination / "capture.json", destination / "events.jsonl", destination / "coverage.json", manifest["release"], adapter=manifest["versions"]["adapter"]["name"], event_schema=version)
                result = verifier.verify(destination / "coverage.json")
                self.assertEqual(result.rows, len(rows))
                for filename in support.RELEASE_DATA_FILES:
                    self.assertEqual((destination / filename).read_bytes(), (source / filename).read_bytes(), filename)
                self.assertEqual(support.release_digests(name), before)
                manifest_validator = self.oracle.Draft202012Validator(support.coverage_schema(version))
                event_validator = self.oracle.Draft202012Validator(support.event_schema(version))
                self.assertFalse(list(manifest_validator.iter_errors(manifest)))
                for row in rows:
                    self.assertFalse(list(event_validator.iter_errors(row)))

    def test_missing_or_wrong_locked_oracle_is_an_error_never_a_skip(self):
        with mock.patch.dict("sys.modules", {"jsonschema": None}):
            with self.assertRaises(support.JsonschemaAbsent):
                locked_oracle()
        with mock.patch.object(importlib.metadata, "version", return_value="0.0.0"):
            with self.assertRaisesRegex(RuntimeError, "requires attrs==26.1.0"):
                locked_oracle()
