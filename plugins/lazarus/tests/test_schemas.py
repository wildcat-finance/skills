"""Versioned formats validate before they reach fixture logic."""

import copy
import traceback
import unittest
from unittest import mock

from lazarus_lib.errors import FormatError, IntegrityError, PathError
from lazarus_lib.records import make_rpc_record
from lazarus_lib.schemas import SCHEMAS, validate_builtin_schemas, validate_document

from . import support


class SchemaTests(unittest.TestCase):
    def test_every_registered_schema_is_valid_and_digest_pinned(self):
        validate_builtin_schemas()
        self.assertEqual(
            {kind for kind, version in SCHEMAS if version == 1},
            {
                "plan",
                "header",
                "rpc-record",
                "proof-record",
                "anchor-record",
                "receipt-witness",
                "manifest",
                "release",
            },
        )
        self.assertIn(("plan", 2), SCHEMAS)
        self.assertIn(("plan", 3), SCHEMAS)
        self.assertIn(("manifest", 2), SCHEMAS)
        self.assertIn(("release", 2), SCHEMAS)

    def test_a_well_formed_release_document_passes(self):
        validate_document("release", support.sample_release())
        validate_document("release", support.sample_release_v2())

    def test_release_versions_keep_their_predicate_and_evidence_vocabularies(self):
        v1 = support.sample_release()
        v1["verified"]["evidence_counts"]["receipt_trie_proved"] = 2
        v2 = support.sample_release_v2()
        v2["statement"]["predicate_type"] = (
            "https://ariadne.wildcat.finance/state-fixture/v1"
        )
        for document in (v1, v2):
            with self.subTest(version=document["schema_version"]):
                with self.assertRaises(FormatError):
                    validate_document("release", document)

    def test_release_v2_requires_a_nonzero_receipts_root_and_four_counts(self):
        for field, value in (
            ("receipts_root", None),
            ("receipts_root", "0x" + "0" * 64),
            ("receipts_root", "0x1234"),
            ("receipt_trie_proved", None),
            ("receipt_trie_proved", True),
            ("receipt_trie_proved", 0),
        ):
            document = support.sample_release_v2()
            target = document["verified"]
            if field == "receipt_trie_proved":
                target = target["evidence_counts"]
            if value is None:
                del target[field]
            else:
                target[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(FormatError):
                    validate_document("release", document)

    def test_release_v2_has_no_transaction_hash_proof_field(self):
        document = support.sample_release_v2()
        document["verified"]["transaction_hash_attribution"] = True
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_release_missing_any_required_field_fails(self):
        for field in (
            "schema_version",
            "tool_version",
            "fixture",
            "statement",
            "verified",
            "binding",
            "release_digest",
        ):
            document = support.sample_release()
            del document[field]
            with self.subTest(field=field), self.assertRaises(FormatError):
                validate_document("release", document)

    def test_a_release_carrying_an_undefined_field_fails(self):
        document = support.sample_release()
        document["signed_by"] = "somebody"
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_release_claiming_the_canonical_chain_fails(self):
        """A self-consistent header is not proof that it belongs to Ethereum's
        canonical chain, and nothing in a release establishes that it does. The
        field is pinned to false rather than merely required."""
        document = support.sample_release()
        document["verified"]["canonical_chain_claim"] = True
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_release_missing_a_verified_count_fails(self):
        for name in ("proof_backed", "header_bound", "recorded_rpc"):
            document = support.sample_release()
            del document["verified"]["evidence_counts"][name]
            with self.subTest(evidence_class=name), self.assertRaises(FormatError):
                validate_document("release", document)

    def test_a_release_with_a_boolean_count_fails(self):
        """`True` is an integer in Python and JSON Schema separates the two, so
        this is the schema being asked rather than assumed."""
        document = support.sample_release()
        document["verified"]["evidence_counts"]["proof_backed"] = True
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_release_with_no_named_binding_check_fails(self):
        """A release that establishes nothing should not be able to say so by
        omission."""
        document = support.sample_release()
        document["binding"]["checks"] = []
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_release_with_a_malformed_digest_fails(self):
        for value in ("", "beef", "0x" + "a" * 64, "A" * 64, 12345):
            document = support.sample_release()
            document["release_digest"] = value
            with self.subTest(release_digest=value), self.assertRaises(FormatError):
                validate_document("release", document)

    def test_a_release_path_that_leaves_the_release_fails(self):
        for value in ("../elsewhere", "/etc/passwd", "a\\b", "a/../b", "", "./a"):
            document = support.sample_release()
            document["statement"]["path"] = value
            with self.subTest(path=value), self.assertRaises(
                (FormatError, PathError)
            ):
                validate_document("release", document)

    def test_a_release_string_that_renders_as_nothing_fails(self):
        """Every string field in a release is read by somebody. A value that
        satisfies a length check and displays as empty is the shape this
        marketplace keeps meeting, so the schema asks for one visible
        character rather than one character."""
        BLANK = ("   ", " ", "\t", "\u200b")
        for value in BLANK:
            for dotted in (
                ("fixture", "path"),
                ("statement", "path"),
                ("statement", "predicate_type"),
            ):
                document = support.sample_release()
                document[dotted[0]][dotted[1]] = value
                with self.subTest(field="/".join(dotted), value=value):
                    with self.assertRaises((FormatError, PathError)):
                        validate_document("release", document)
            document = support.sample_release()
            document["binding"]["checks"] = [value]
            with self.subTest(field="binding/checks", value=value):
                with self.assertRaises(FormatError):
                    validate_document("release", document)

    def test_a_predicate_type_that_is_not_a_uri_fails(self):
        for value in ("state-fixture", "   ", "//x", "1https://x", "https:"):
            document = support.sample_release()
            document["statement"]["predicate_type"] = value
            with self.subTest(predicate_type=value), self.assertRaises(FormatError):
                validate_document("release", document)

    def test_a_path_with_a_space_inside_it_is_still_a_path(self):
        """Refusing every space would refuse a legitimate filename."""
        document = support.sample_release()
        document["statement"]["path"] = "a statement.json"
        validate_document("release", document)

    def test_a_release_whose_statement_is_its_fixture_fails(self):
        document = support.sample_release()
        document["statement"]["path"] = document["fixture"]["path"]
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_statement_inside_the_fixture_fails(self):
        """The fixture digest would otherwise cover the statement made about
        it, which makes the statement part of its own subject."""
        for fixture, statement in (
            ("fixture", "fixture/statement.json"),
            ("inner/fixture", "inner/fixture/statement.json"),
        ):
            document = support.sample_release()
            document["fixture"]["path"] = fixture
            document["statement"]["path"] = statement
            with self.subTest(fixture=fixture), self.assertRaises(FormatError):
                validate_document("release", document)

    def test_valid_plan_header_rpc_and_proof_documents_pass(self):
        validate_document("plan", support.sample_plan())
        validate_document("plan", support.sample_plan_v2())
        validate_document("plan", support.sample_plan_v3())
        validate_document("header", support.sample_header())
        validate_document(
            "rpc-record",
            make_rpc_record(
                "eth_chainId", [], required=True, evidence="recorded-rpc", result="0x1"
            ),
        )
        validate_document("proof-record", support.sample_proof_record())
        validate_document("anchor-record", support.sample_anchor_record())
        validate_document("receipt-witness", support.sample_receipt_witness())

    def test_unknown_schema_versions_fail_closed(self):
        for kind, document in (
            ("plan", support.sample_plan_v2()),
            ("header", support.sample_header()),
            ("proof-record", support.sample_proof_record()),
            ("anchor-record", support.sample_anchor_record()),
            ("receipt-witness", support.sample_receipt_witness()),
        ):
            document["schema_version"] = 4 if kind == "plan" else 2
            with self.subTest(kind=kind), self.assertRaisesRegex(FormatError, "unsupported"):
                validate_document(kind, document)

    def test_unknown_schema_versions_are_value_free_and_bounded(self):
        for digits in ("3141592653589793", "314159" + "2" * 4000):
            document = support.sample_receipt_witness()
            document["schema_version"] = int(digits)
            with self.subTest(digits=len(digits)), self.assertRaises(
                FormatError
            ) as raised:
                validate_document("receipt-witness", document)
            error = raised.exception
            surfaces = {
                "message": str(error),
                "args": repr(error.args),
                "repr": repr(error),
                "cause": repr(error.__cause__),
                "context": repr(error.__context__),
                "traceback": "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                ),
            }
            self.assertIsNone(error.__cause__)
            self.assertIsNone(error.__context__)
            for name, rendered in surfaces.items():
                with self.subTest(surface=name):
                    self.assertNotIn("314159", rendered)
                    self.assertLessEqual(len(rendered.encode("utf-8")), 4096)

    def test_plan_v3_surrogates_fail_as_canonical_format_errors(self):
        plan = support.sample_plan_v3()
        plan["block"]["hash_source"] = "\ud800"
        caught = None
        try:
            validate_document("plan", plan)
        except Exception as error:  # The assertion below classifies the boundary.
            caught = error
        self.assertIsNotNone(caught)
        self.assertIsInstance(caught, FormatError)
        self.assertIn("surrogate code point", str(caught))
        self.assertIsNone(caught.__cause__)
        self.assertIsNone(caught.__context__)

    def test_plan_v2_requires_closed_bounded_source_declarations(self):
        validate_document("plan", support.sample_plan_v2(("a",)))
        validate_document(
            "plan",
            support.sample_plan_v2(tuple(f"source-{index:02d}" for index in range(32))),
        )
        for source_ids in ((), tuple(f"source-{index:02d}" for index in range(33))):
            with self.subTest(count=len(source_ids)), self.assertRaisesRegex(
                FormatError, "anchor_sources"
            ):
                validate_document("plan", support.sample_plan_v2(source_ids))

        plan = support.sample_plan_v2()
        plan["anchor_sources"][0]["url"] = "https://must-not-enter-a-plan.example"
        with self.assertRaisesRegex(FormatError, "anchor_sources"):
            validate_document("plan", plan)

        legacy = support.sample_plan()
        legacy["anchor_sources"] = [{"source_id": "a"}]
        with self.assertRaisesRegex(FormatError, "additionalProperties"):
            validate_document("plan", legacy)

    def test_plan_v2_copies_every_plan_v1_contract_field(self):
        plan_v1 = support.load_json("schemas/plan-v1.json")
        plan_v2 = support.load_json("schemas/plan-v2.json")
        plan_v2["$id"] = plan_v1["$id"]
        plan_v2["title"] = plan_v1["title"]
        plan_v2["required"].remove("anchor_sources")
        plan_v2["properties"].pop("anchor_sources")
        plan_v2["properties"]["schema_version"] = {"const": 1}
        self.assertEqual(plan_v2, plan_v1)

    def test_plan_v3_copies_every_plan_v2_contract_field(self):
        plan_v2 = support.load_json("schemas/plan-v2.json")
        plan_v3 = support.load_json("schemas/plan-v3.json")
        plan_v3["$id"] = plan_v2["$id"]
        plan_v3["title"] = plan_v2["title"]
        plan_v3["required"].remove("receipt_witness")
        plan_v3["properties"].pop("receipt_witness")
        plan_v3["properties"]["schema_version"] = {"const": 2}
        self.assertEqual(plan_v3, plan_v2)

    def test_manifest_v2_is_additive_over_manifest_v1(self):
        manifest_v1 = support.load_json("schemas/manifest-v1.json")
        manifest_v2 = support.load_json("schemas/manifest-v2.json")
        manifest_v2["$id"] = manifest_v1["$id"]
        manifest_v2["title"] = manifest_v1["title"]
        manifest_v2["required"].remove("receipts_root")
        manifest_v2["properties"].pop("receipts_root")
        manifest_v2["properties"]["schema_version"] = {"const": 1}
        counts = manifest_v2["properties"]["evidence_counts"]
        counts["required"].remove("receipt_trie_proved")
        counts["properties"].pop("receipt_trie_proved")
        self.assertEqual(manifest_v2, manifest_v1)

    def test_manifest_v2_requires_a_bound_witness_and_nonzero_proved_root(self):
        manifest = support.sample_manifest_v2()
        validate_document("manifest", manifest)

        without_witness = copy.deepcopy(manifest)
        without_witness["components"].pop()
        with self.assertRaisesRegex(FormatError, "requires receipt-witness"):
            validate_document("manifest", without_witness)

        zero_root = copy.deepcopy(manifest)
        zero_root["receipts_root"] = support.hash32("00")
        with self.assertRaisesRegex(FormatError, "nonzero receipts root"):
            validate_document("manifest", zero_root)

        zero_count = copy.deepcopy(zero_root)
        zero_count["evidence_counts"]["receipt_trie_proved"] = 0
        validate_document("manifest", zero_count)

        boolean_count = copy.deepcopy(manifest)
        boolean_count["evidence_counts"]["receipt_trie_proved"] = True
        with self.assertRaises(FormatError):
            validate_document("manifest", boolean_count)

    def test_manifest_v1_refuses_a_receipt_witness_or_new_evidence_class(self):
        manifest = support.sample_manifest_v2()
        manifest["schema_version"] = 1
        manifest.pop("receipts_root")
        with self.assertRaisesRegex(FormatError, "evidence_counts"):
            validate_document("manifest", manifest)
        manifest["evidence_counts"].pop("receipt_trie_proved")
        with self.assertRaisesRegex(FormatError, "manifest-v1 refuses"):
            validate_document("manifest", manifest)

    def test_plan_v3_relations_bind_exact_standard_requests(self):
        validate_document("plan", support.sample_plan_v3())
        mutations = (
            (
                "block method",
                lambda plan: plan["requests"][1].__setitem__(
                    "method", "debug_getRawReceipts"
                ),
                "eth_getBlockReceipts",
            ),
            (
                "block params",
                lambda plan: plan["requests"][1].__setitem__(
                    "params", [plan["block"]["number"]]
                ),
                "fixed block hash",
            ),
            (
                "optional source",
                lambda plan: plan["requests"][1].__setitem__("required", False),
                "required recorded-rpc",
            ),
            (
                "target identity",
                lambda plan: plan["requests"][2].__setitem__("params", ["0x1"]),
                "transaction hash",
            ),
            (
                "log range",
                lambda plan: plan["requests"][3]["params"][0].__setitem__(
                    "fromBlock", plan["block"]["number"]
                ),
                "unsupported fields",
            ),
            (
                "log block",
                lambda plan: plan["requests"][3]["params"][0].__setitem__(
                    "blockHash", support.hash32("ff")
                ),
                "fixed block hash",
            ),
        )
        for name, mutate, message in mutations:
            plan = support.sample_plan_v3()
            mutate(plan)
            with self.subTest(name=name), self.assertRaisesRegex(
                FormatError, message
            ):
                validate_document("plan", plan)

    def test_plan_v3_relation_is_closed_complete_and_canonical(self):
        for field in (
            "block_receipts_request",
            "target_receipt_lookup_request",
            "target_transaction_index",
            "filtered_logs_request",
        ):
            plan = support.sample_plan_v3()
            del plan["receipt_witness"][field]
            with self.subTest(missing=field), self.assertRaises(FormatError):
                validate_document("plan", plan)
        plan = support.sample_plan_v3()
        plan["receipt_witness"]["fallback"] = "debug_getRawReceipts"
        with self.assertRaises(FormatError):
            validate_document("plan", plan)
        for value in (True, 1, "0x00"):
            plan = support.sample_plan_v3()
            plan["receipt_witness"]["target_transaction_index"] = value
            with self.subTest(index=value), self.assertRaises(FormatError):
                validate_document("plan", plan)

    def test_plan_target_hash_is_only_a_recorded_lookup_label(self):
        plan = support.sample_plan_v3()
        lookup_name = plan["receipt_witness"]["target_receipt_lookup_request"]
        lookup = next(item for item in plan["requests"] if item["name"] == lookup_name)
        self.assertEqual(lookup["method"], "eth_getTransactionReceipt")
        self.assertEqual(lookup["evidence"], "recorded-rpc")
        self.assertRegex(lookup["params"][0], r"^0x[0-9a-fA-F]{64}$")

        promoted = copy.deepcopy(plan)
        promoted["requests"][2]["evidence"] = "proof-backed"
        with self.assertRaisesRegex(FormatError, "required recorded-rpc"):
            validate_document("plan", promoted)

        witness_before = support.sample_receipt_witness()
        plan["requests"][2]["params"] = [support.hash32("ff")]
        validate_document("plan", plan)
        self.assertEqual(support.sample_receipt_witness(), witness_before)

    def test_receipt_witness_is_closed_complete_and_supports_named_types(self):
        witness = support.sample_receipt_witness()
        validate_document("receipt-witness", witness)
        legacy = copy.deepcopy(witness)
        legacy["receipts"][0].pop("status")
        legacy["receipts"][0]["root"] = support.hash32("77")
        validate_document("receipt-witness", legacy)

        for field in (
            "schema_version",
            "header",
            "receipts",
            "target_receipt",
            "filtered_logs",
        ):
            changed = copy.deepcopy(witness)
            del changed[field]
            with self.subTest(missing=field), self.assertRaises(FormatError):
                validate_document("receipt-witness", changed)
        changed = copy.deepcopy(witness)
        changed["provider"] = "unbound"
        with self.assertRaises(FormatError):
            validate_document("receipt-witness", changed)

    def test_receipt_witness_rejects_ambiguous_or_unsupported_payloads(self):
        mutations = (
            (
                "both status and root",
                lambda witness: witness["receipts"][0].__setitem__(
                    "root", support.hash32("77")
                ),
                FormatError,
                "receipt-witness",
            ),
            (
                "neither status nor root",
                lambda witness: witness["receipts"][0].pop("status"),
                FormatError,
                "receipt-witness",
            ),
            (
                "typed root",
                lambda witness: (
                    witness["receipts"][1].pop("status"),
                    witness["receipts"][1].__setitem__(
                        "root", support.hash32("77")
                    ),
                ),
                FormatError,
                "typed receipt",
            ),
            (
                "unsupported type",
                lambda witness: witness["receipts"][1].__setitem__(
                    "receipt_type", "0x3"
                ),
                FormatError,
                "receipt_type",
            ),
            (
                "noncanonical quantity",
                lambda witness: witness["receipts"][1].__setitem__(
                    "cumulative_gas_used", "0x02"
                ),
                FormatError,
                "cumulative_gas_used",
            ),
            (
                "odd data byte",
                lambda witness: witness["receipts"][1]["logs"][0].__setitem__(
                    "data", "0x1"
                ),
                FormatError,
                "data",
            ),
            (
                "topic count",
                lambda witness: witness["receipts"][1]["logs"][0].__setitem__(
                    "topics", [support.hash32(str(index)[-1] * 2) for index in range(5)]
                ),
                FormatError,
                "topics",
            ),
        )
        for name, mutate, error, message in mutations:
            witness = support.sample_receipt_witness()
            mutate(witness)
            with self.subTest(name=name), self.assertRaisesRegex(error, message):
                validate_document("receipt-witness", witness)

    def test_schema_refusals_do_not_echo_hostile_keys_or_values(self):
        prefix = "PRIVATE_PROVIDER_VALUE_"
        marker = prefix + "x" * 200_000

        def assert_safe(error: FormatError) -> None:
            surfaces = {
                "message": str(error),
                "args": repr(error.args),
                "repr": repr(error),
                "cause": repr(error.__cause__),
                "context": repr(error.__context__),
                "traceback": "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                ),
            }
            self.assertIsNone(error.__cause__)
            self.assertIsNone(error.__context__)
            for name, rendered in surfaces.items():
                with self.subTest(surface=name):
                    self.assertNotIn(prefix, rendered)
                    self.assertLessEqual(len(rendered.encode("utf-8")), 4096)

        for hostile_key in (prefix + "SECRET", marker):
            witness = support.sample_receipt_witness()
            witness[hostile_key] = True
            with self.subTest(hostile_key=len(hostile_key)), self.assertRaises(
                FormatError
            ) as raised:
                validate_document("receipt-witness", witness)
            assert_safe(raised.exception)

        for hostile_value in (prefix + "SECRET", marker):
            witness = support.sample_receipt_witness()
            witness["receipts"][0]["receipt_type"] = hostile_value
            with self.subTest(hostile_value=len(hostile_value)), self.assertRaises(
                FormatError
            ) as raised:
                validate_document("receipt-witness", witness)
            assert_safe(raised.exception)

    def test_receipt_witness_rejects_index_target_and_filter_disagreement(self):
        mutations = (
            (
                "index",
                lambda witness: witness["receipts"][1].__setitem__(
                    "transaction_index", "0x2"
                ),
                "not contiguous",
            ),
            (
                "target",
                lambda witness: witness["target_receipt"].__setitem__(
                    "transaction_index", "0x2"
                ),
                "target index",
            ),
            (
                "filter block",
                lambda witness: witness["filtered_logs"]["filter"].__setitem__(
                    "blockHash", support.hash32("ff")
                ),
                "fixed block hash",
            ),
        )
        for name, mutate, message in mutations:
            witness = support.sample_receipt_witness()
            mutate(witness)
            with self.subTest(name=name), self.assertRaisesRegex(
                FormatError, message
            ):
                validate_document("receipt-witness", witness)

    def test_receipt_witness_refuses_transaction_hashes_and_rpc_decorations(self):
        witness = support.sample_receipt_witness()
        self.assertNotIn("transaction_hash", str(witness))
        mutations = (
            (lambda value: value["header"].__setitem__("chain_id", "0x1")),
            (lambda value: value["header"].__setitem__("transactions", [support.hash32()])),
            (lambda value: value["receipts"][0].__setitem__("transaction_hash", support.hash32())),
            (lambda value: value["receipts"][0].__setitem__("block_hash", support.hash32())),
            (lambda value: value["receipts"][0].__setitem__("block_number", "0x10")),
            (lambda value: value["receipts"][1]["logs"][0].__setitem__("transaction_hash", support.hash32())),
            (lambda value: value["receipts"][1]["logs"][0].__setitem__("transaction_index", "0x1")),
            (lambda value: value["receipts"][1]["logs"][0].__setitem__("log_index", "0x0")),
            (lambda value: value["target_receipt"].__setitem__("transaction_hash", support.hash32())),
        )
        for mutate in mutations:
            changed = copy.deepcopy(witness)
            mutate(changed)
            with self.subTest(changed=changed), self.assertRaises(FormatError):
                validate_document("receipt-witness", changed)

    def test_source_ids_keep_the_public_grammar(self):
        invalid = ("", "A", "-source", "source/name", "a" * 129)
        for value in invalid:
            with self.subTest(value=value):
                plan = support.sample_plan_v2((value,))
                with self.assertRaisesRegex(FormatError, "source_id"):
                    validate_document("plan", plan)
                record = support.sample_anchor_record(value)
                with self.assertRaisesRegex(FormatError, "source_id"):
                    validate_document("anchor-record", record)

    def test_plan_anchor_sources_must_be_sorted_and_unique(self):
        for source_ids in (("z", "a"), ("a", "a")):
            with self.subTest(source_ids=source_ids), self.assertRaisesRegex(
                FormatError, "anchor sources must be sorted and unique"
            ):
                validate_document("plan", support.sample_plan_v2(source_ids))

    def test_anchor_record_is_closed_and_complete(self):
        for field in (
            "schema_version",
            "source_id",
            "observed_at",
            "method",
            "params",
            "returned",
        ):
            record = support.sample_anchor_record()
            del record[field]
            with self.subTest(field=field), self.assertRaises(FormatError):
                validate_document("anchor-record", record)
        record = support.sample_anchor_record()
        record["provider_url"] = "https://must-not-enter-a-record.example"
        with self.assertRaises(FormatError):
            validate_document("anchor-record", record)

    def test_anchor_timestamp_must_be_a_real_utc_instant(self):
        invalid = (
            "2026-08-25T08:30:45+00:00",
            "2026-08-25T01:30:45-07:00",
            "2026-08-25T08:30:45",
            "2026-02-30T08:30:45Z",
            "not-a-time",
        )
        for value in invalid:
            record = support.sample_anchor_record()
            record["observed_at"] = value
            with self.subTest(value=value), self.assertRaisesRegex(FormatError, "UTC"):
                validate_document("anchor-record", record)

    def test_anchor_method_and_parameters_are_exact(self):
        mutations = (
            ("method", "eth_getBlockByHash"),
            ("params", ["0x10"]),
            ("params", ["0x10", True]),
            ("params", ["0x00", False]),
        )
        for field, value in mutations:
            record = support.sample_anchor_record()
            record[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(FormatError):
                validate_document("anchor-record", record)

    def test_anchor_returned_fields_are_mainnet_block_identity(self):
        mutations = (
            ("chain_id", "0x2"),
            ("number", "0x11"),
            ("number", "0x00"),
            ("hash", "0x1234"),
        )
        for field, value in mutations:
            record = support.sample_anchor_record()
            record["returned"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(FormatError):
                validate_document("anchor-record", record)
        for field in ("chain_id", "number", "hash"):
            record = support.sample_anchor_record()
            del record["returned"][field]
            with self.subTest(missing=field), self.assertRaises(FormatError):
                validate_document("anchor-record", record)
        record = support.sample_anchor_record()
        record["returned"]["provider"] = "extra"
        with self.assertRaises(FormatError):
            validate_document("anchor-record", record)

    def test_quantities_and_addresses_keep_exact_ethereum_shapes(self):
        plan = support.sample_plan()
        plan["block"]["number"] = "0x00"
        with self.assertRaisesRegex(FormatError, "number"):
            validate_document("plan", plan)
        plan = support.sample_plan()
        plan["proof_targets"][0]["address"] = "0x1234"
        with self.assertRaisesRegex(FormatError, "address"):
            validate_document("plan", plan)
        proof = support.sample_proof_record()
        proof["balance"] = "1"
        with self.assertRaisesRegex(FormatError, "balance"):
            validate_document("proof-record", proof)
        proof = support.sample_proof_record()
        proof["balance"] = "0x1" + "0" * 64
        with self.assertRaisesRegex(FormatError, "balance"):
            validate_document("proof-record", proof)

    def test_plan_rejects_duplicate_requests_targets_and_unsorted_slots(self):
        plan = support.sample_plan()
        plan["requests"].append(copy.deepcopy(plan["requests"][0]))
        plan["requests"][1]["name"] = "same-request"
        with self.assertRaisesRegex(FormatError, "duplicate exact request"):
            validate_document("plan", plan)
        plan = support.sample_plan()
        plan["proof_targets"].append(copy.deepcopy(plan["proof_targets"][0]))
        with self.assertRaisesRegex(FormatError, "proof target address"):
            validate_document("plan", plan)
        plan = support.sample_plan()
        plan["proof_targets"][0]["slots"] = [support.slot("02"), support.slot("01")]
        with self.assertRaisesRegex(FormatError, "sorted and unique"):
            validate_document("plan", plan)

    def test_plan_enforces_its_request_limit(self):
        plan = support.sample_plan()
        plan["limits"]["max_requests"] = 1
        second = copy.deepcopy(plan["requests"][0])
        second.update({"name": "block", "method": "eth_blockNumber"})
        plan["requests"].append(second)
        with self.assertRaisesRegex(FormatError, "max_requests"):
            validate_document("plan", plan)

    def test_plan_accepts_only_bounded_integer_capture_time(self):
        plan = support.sample_plan()
        plan["limits"]["max_elapsed_seconds"] = 60
        validate_document("plan", plan)
        for value in (0, 86401, 1.5):
            changed = copy.deepcopy(plan)
            changed["limits"]["max_elapsed_seconds"] = value
            with self.subTest(value=value), self.assertRaisesRegex(
                FormatError, "max_elapsed_seconds"
            ):
                validate_document("plan", changed)

    def test_header_identity_must_match_raw_rpc_result(self):
        header = support.sample_header()
        header["rpc_result"]["hash"] = support.hash32("ff")
        with self.assertRaisesRegex(FormatError, "disagrees"):
            validate_document("header", header)
        header = support.sample_header()
        del header["rpc_result"]["stateRoot"]
        with self.assertRaisesRegex(FormatError, "stateRoot"):
            validate_document("header", header)

    def test_storage_proof_keys_are_sorted_and_unique(self):
        proof = support.sample_proof_record()
        proof["storage_proof"] = [
            {"key": support.slot("02"), "value": "0x0", "proof": ["0xc0"]},
            {"key": support.slot("01"), "value": "0x0", "proof": ["0xc0"]},
        ]
        with self.assertRaisesRegex(FormatError, "sorted and unique"):
            validate_document("proof-record", proof)

    def test_registry_digest_detects_schema_substitution(self):
        for key, document in (
            (("plan", 1), support.sample_plan()),
            (("plan", 2), support.sample_plan_v2()),
            (("plan", 3), support.sample_plan_v3()),
            (("anchor-record", 1), support.sample_anchor_record()),
            (("receipt-witness", 1), support.sample_receipt_witness()),
        ):
            filename, _ = SCHEMAS[key]
            with self.subTest(key=key), mock.patch.dict(
                SCHEMAS, {key: (filename, "0" * 64)}
            ):
                with self.assertRaisesRegex(IntegrityError, "digest mismatch"):
                    validate_document(key[0], document)


if __name__ == "__main__":
    unittest.main()
