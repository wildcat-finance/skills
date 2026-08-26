"""Versioned formats validate before they reach fixture logic."""

import copy
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
                "manifest",
                "release",
            },
        )
        self.assertIn(("plan", 2), SCHEMAS)

    def test_a_well_formed_release_document_passes(self):
        validate_document("release", support.sample_release())

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
        document = support.sample_release()
        document["statement"]["path"] = "fixture/statement.json"
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_valid_plan_header_rpc_and_proof_documents_pass(self):
        validate_document("plan", support.sample_plan())
        validate_document("plan", support.sample_plan_v2())
        validate_document("header", support.sample_header())
        validate_document(
            "rpc-record",
            make_rpc_record(
                "eth_chainId", [], required=True, evidence="recorded-rpc", result="0x1"
            ),
        )
        validate_document("proof-record", support.sample_proof_record())
        validate_document("anchor-record", support.sample_anchor_record())

    def test_unknown_schema_versions_fail_closed(self):
        for kind, document in (
            ("plan", support.sample_plan_v2()),
            ("header", support.sample_header()),
            ("proof-record", support.sample_proof_record()),
            ("anchor-record", support.sample_anchor_record()),
        ):
            document["schema_version"] = 3 if kind == "plan" else 2
            with self.subTest(kind=kind), self.assertRaisesRegex(FormatError, "unsupported"):
                validate_document(kind, document)

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
        with self.assertRaisesRegex(FormatError, "anchor_sources"):
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
            (("anchor-record", 1), support.sample_anchor_record()),
        ):
            filename, _ = SCHEMAS[key]
            with self.subTest(key=key), mock.patch.dict(
                SCHEMAS, {key: (filename, "0" * 64)}
            ):
                with self.assertRaisesRegex(IntegrityError, "digest mismatch"):
                    validate_document(key[0], document)


if __name__ == "__main__":
    unittest.main()
