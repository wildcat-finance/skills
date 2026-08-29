"""Whether a statement describes this fixture, and whether it claims more.

The evidence tests carry the weight. Everything else here keeps a statement from
being bound to the wrong capture; those keep it from being bound to the right one
while saying something the records do not support.
"""

import copy
import traceback
import unicodedata
import unittest
from unittest import mock

from lazarus_lib import binding as binding_module
from lazarus_lib.binding import (
    CHECKS,
    EVIDENCE_CLASSES,
    IN_TOTO_STATEMENT_TYPE,
    MAX_FIXTURE_SUBJECTS,
    MAX_SUBJECTS,
    REPLAY_CLAIMS,
    STATE_FIXTURE_TYPE,
    STATE_FIXTURE_TYPE_V2,
    bind,
)
from lazarus_lib.errors import (
    FormatError,
    IntegrityError,
    ResourceLimitError,
)

BLOCK_HASH = "0x" + "41" * 32
BLOCK_NUMBER = 13097494
STATE_ROOT = "0x" + "0f" * 32
RECEIPTS_ROOT = "0x" + "22" * 32
CHAIN_ID = 1


def sample_manifest():
    return {
        "schema_version": 1,
        "chain_id": hex(CHAIN_ID),
        "block": {"number": hex(BLOCK_NUMBER), "hash": BLOCK_HASH},
        "components": [
            {"path": "header.json", "bytes": 17204, "sha256": "a" * 64},
            {"path": "plan.json", "bytes": 1418, "sha256": "b" * 64},
            {"path": "proofs.jsonl", "bytes": 8688, "sha256": "c" * 64},
        ],
    }


def sample_report():
    """What `verify_fixture` returns, in the shape it returns it."""
    return {
        "fixture_digest": "d" * 64,
        "block_hash": BLOCK_HASH,
        "block_number": hex(BLOCK_NUMBER),
        "state_root": STATE_ROOT,
        "evidence_counts": {"proof_backed": 2, "header_bound": 1, "recorded_rpc": 4},
        "proof_backed": {
            "accounts_included": 1,
            "accounts_absent": 0,
            "storage_included": 1,
            "storage_absent": 0,
        },
        "header_bound": {"headers": 1, "canonical_chain_claim": False},
        "recorded_rpc": {"records": 4, "optional_failures": 0},
    }


def sample_statement():
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": STATE_FIXTURE_TYPE,
        "predicate": {
            "chain": {
                "chain_id": CHAIN_ID,
                "block_number": BLOCK_NUMBER,
                "block_hash": BLOCK_HASH,
                "state_root": STATE_ROOT,
            },
            "evidence": {
                "proof_backed": 2,
                "header_bound": 1,
                "recorded_rpc": 4,
            },
            "replay": {"reaches_network": False, "canonical_chain_claim": False},
            "fixture_subjects": [
                {
                    "name": "header.json",
                    "path": "header.json",
                    "digest": {"sha256": "a" * 64},
                    "bytes": 17204,
                },
                {
                    "name": "plan.json",
                    "path": "plan.json",
                    "digest": {"sha256": "b" * 64},
                    "bytes": 1418,
                },
                {
                    "name": "proofs.jsonl",
                    "path": "proofs.jsonl",
                    "digest": {"sha256": "c" * 64},
                    "bytes": 8688,
                },
            ],
        },
        "subject": [
            {"name": "header.json", "digest": {"sha256": "a" * 64}},
            {"name": "plan.json", "digest": {"sha256": "b" * 64}},
            {"name": "proofs.jsonl", "digest": {"sha256": "c" * 64}},
            {"name": "goldfinch-block-13097494", "digest": {"sha256": "d" * 64}},
        ],
    }


def sample_manifest_v2():
    manifest = copy.deepcopy(sample_manifest())
    manifest["schema_version"] = 2
    manifest["receipts_root"] = RECEIPTS_ROOT
    manifest["components"].append(
        {
            "path": "receipt-witness.json",
            "bytes": 4096,
            "sha256": "e" * 64,
        }
    )
    return manifest


def sample_report_v2():
    report = copy.deepcopy(sample_report())
    report["receipts_root"] = RECEIPTS_ROOT
    report["evidence_counts"]["receipt_trie_proved"] = 2
    report["receipt_trie_proved"] = {
        "relations": 2,
        "transaction_hash_attribution": "recorded_rpc",
    }
    report["chain_anchors"] = {
        "records": 0,
        "canonical_chain_claim": False,
        "provider_independence_claim": False,
    }
    return report


def sample_statement_v2():
    document = copy.deepcopy(sample_statement())
    document["predicateType"] = STATE_FIXTURE_TYPE_V2
    document["predicate"]["chain"]["receipts_root"] = RECEIPTS_ROOT
    document["predicate"]["evidence"]["receipt_trie_proved"] = 2
    document["predicate"]["replay"]["provider_independence_claim"] = False
    component = {
        "name": "receipt-witness.json",
        "path": "receipt-witness.json",
        "digest": {"sha256": "e" * 64},
        "bytes": 4096,
    }
    document["predicate"]["fixture_subjects"].append(component)
    document["subject"].append(
        {"name": component["name"], "digest": component["digest"]}
    )
    document["predicate"].update(
        {
            "capture": {
                "tool": "lazarus",
                "tool_version": "0.1.0",
                "command": ["lazarus", "capture", "fixture-v2"],
                "parameters_digest": {"sha256": "f" * 64},
            },
            "deltas": {
                "baseline": None,
                "current": {
                    "name": "fixture-v2",
                    "digest": {"sha256": "d" * 64},
                },
                "reason": "first receipt-aware fixture",
            },
            "claims": [],
            "commands": [],
        }
    )
    return document


def bound(statement=None, manifest=None, report=None):
    return bind(
        statement if statement is not None else sample_statement(),
        manifest if manifest is not None else sample_manifest(),
        report if report is not None else sample_report(),
    )


def bound_v2(statement=None, manifest=None, report=None):
    return bind(
        statement if statement is not None else sample_statement_v2(),
        manifest if manifest is not None else sample_manifest_v2(),
        report if report is not None else sample_report_v2(),
    )


class CleanBindingTests(unittest.TestCase):
    def test_a_statement_over_this_fixture_binds(self):
        self.assertEqual(bound(), list(CHECKS))

    def test_a_v2_statement_binds_only_to_a_v2_fixture(self):
        self.assertEqual(bound_v2(), list(CHECKS))
        with self.assertRaisesRegex(IntegrityError, "v1"):
            bound(statement=sample_statement_v2())
        with self.assertRaisesRegex(IntegrityError, "v2"):
            bound_v2(statement=sample_statement())

    def test_the_checks_it_returns_are_the_ones_it_names(self):
        """The names go into the release document, so a reader learns which
        questions were asked rather than inferring them from the release."""
        made = bound()
        self.assertEqual(made, list(CHECKS))
        self.assertEqual(len(set(made)), len(made))
        for name in made:
            self.assertTrue(name and name.strip())

    def test_anchor_inventory_binds_without_changing_the_ariadne_contract(self):
        manifest = sample_manifest()
        report = sample_report()
        statement = sample_statement()
        anchor = {
            "path": "anchors.jsonl",
            "bytes": 512,
            "sha256": "e" * 64,
        }
        manifest["components"].append(anchor)
        report["chain_anchors"] = {
            "records": 2,
            "canonical_chain_claim": False,
            "provider_independence_claim": False,
        }
        statement["predicate"]["fixture_subjects"].append(
            {
                "name": anchor["path"],
                "path": anchor["path"],
                "digest": {"sha256": anchor["sha256"]},
                "bytes": anchor["bytes"],
            }
        )
        statement["subject"].append(
            {"name": anchor["path"], "digest": {"sha256": anchor["sha256"]}}
        )
        original_evidence = copy.deepcopy(statement["predicate"]["evidence"])
        self.assertEqual(bound(statement, manifest, report), list(CHECKS))
        self.assertEqual(statement["predicate"]["evidence"], original_evidence)
        self.assertNotIn("chain_anchors", statement["predicate"])

    def test_a_block_hash_in_the_other_case_still_binds(self):
        """Two spellings of one value. Lazarus writes lowercase and a producer
        may not."""
        statement = sample_statement()
        statement["predicate"]["chain"]["block_hash"] = BLOCK_HASH.upper().replace(
            "0X", "0x"
        )
        self.assertEqual(bound(statement), list(CHECKS))


class EvidenceTests(unittest.TestCase):
    """The rule this module exists for."""

    def test_state_fixture_v1_refuses_the_new_receipt_evidence_class(self):
        report = sample_report()
        report["evidence_counts"]["receipt_trie_proved"] = 2
        report["receipt_trie_proved"] = {
            "relations": 2,
            "transaction_hash_attribution": "recorded_rpc",
        }
        with self.assertRaisesRegex(
            IntegrityError, "outside its vocabulary"
        ):
            bound(report=report)

    def test_v2_receipt_count_is_the_scoped_relation_count(self):
        for value in (None, True, 0, 3):
            statement = sample_statement_v2()
            if value is None:
                del statement["predicate"]["evidence"]["receipt_trie_proved"]
            else:
                statement["predicate"]["evidence"]["receipt_trie_proved"] = value
            with self.subTest(value=value), self.assertRaises(
                (FormatError, IntegrityError)
            ):
                bound_v2(statement=statement)

    def test_v2_report_relation_count_must_match_its_evidence_count(self):
        report = sample_report_v2()
        report["receipt_trie_proved"]["relations"] = 3
        with self.assertRaisesRegex(IntegrityError, "relation count"):
            bound_v2(report=report)

    def test_a_statement_claiming_more_proved_records_is_refused(self):
        """The study's case, and the one the held job names. Four recorded RPC
        responses moved into the proved column."""
        statement = sample_statement()
        statement["predicate"]["evidence"] = {
            "proof_backed": 6,
            "header_bound": 1,
            "recorded_rpc": 0,
        }
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        message = str(caught.exception)
        self.assertIn("proof_backed", message)
        self.assertIn("6", message)
        self.assertIn("2", message)
        self.assertIn("more than the records support", message)

    def test_each_class_disagreeing_upward_is_refused(self):
        for name in EVIDENCE_CLASSES:
            statement = sample_statement()
            statement["predicate"]["evidence"][name] += 1
            with self.subTest(evidence_class=name), self.assertRaises(IntegrityError):
                bound(statement)

    def test_each_class_disagreeing_downward_is_refused(self):
        """Understating is wrong too. It describes a fixture nobody has, and the
        next reader cannot tell which of the two documents is the mistake."""
        for name in EVIDENCE_CLASSES:
            statement = sample_statement()
            statement["predicate"]["evidence"][name] -= 1
            with self.subTest(evidence_class=name), self.assertRaises(
                IntegrityError
            ) as caught:
                bound(statement)
            self.assertIn("fewer than the records support", str(caught.exception))

    def test_a_class_left_out_is_refused(self):
        for name in EVIDENCE_CLASSES:
            statement = sample_statement()
            del statement["predicate"]["evidence"][name]
            with self.subTest(evidence_class=name), self.assertRaises(
                IntegrityError
            ) as caught:
                bound(statement)
            self.assertIn(name, str(caught.exception))

    def test_a_class_the_fixture_does_not_have_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["evidence"]["trusted_oracle"] = 3
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("trusted_oracle", str(caught.exception))

    def test_a_boolean_count_is_refused(self):
        """`True` is an integer in Python and equals 1, so a header-bound count
        of `true` would compare equal to the verified 1 and bind."""
        statement = sample_statement()
        statement["predicate"]["evidence"]["header_bound"] = True
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("whole number", str(caught.exception))

    def test_a_float_count_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["evidence"]["proof_backed"] = 2.0
        with self.assertRaises(IntegrityError):
            bound(statement)

    def test_zero_everywhere_binds_when_the_fixture_proved_nothing(self):
        statement = sample_statement()
        report = sample_report()
        for name in EVIDENCE_CLASSES:
            statement["predicate"]["evidence"][name] = 0
            report["evidence_counts"][name] = 0
        self.assertEqual(bound(statement, report=report), list(CHECKS))

    def test_the_counts_come_from_the_report_and_not_the_manifest(self):
        """The whole point. A manifest carrying inflated counts changes nothing,
        because the binding never reads them."""
        manifest = sample_manifest()
        manifest["evidence_counts"] = {
            "proof_backed": 6,
            "header_bound": 1,
            "recorded_rpc": 0,
        }
        self.assertEqual(bound(manifest=manifest), list(CHECKS))

    def test_an_evidence_block_that_is_not_an_object_is_refused(self):
        for value in (None, [], "2", 2, True):
            statement = sample_statement()
            statement["predicate"]["evidence"] = value
            with self.subTest(evidence=value), self.assertRaises(FormatError):
                bound(statement)


class PredicateTypeTests(unittest.TestCase):
    def test_another_type_is_refused(self):
        statement = sample_statement()
        statement["predicateType"] = "https://ariadne.wildcat.finance/dataset/v1"
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("has not read", str(caught.exception))

    def test_versions_are_not_implicitly_upgraded(self):
        with self.assertRaises(IntegrityError):
            bound(statement=sample_statement_v2())
        with self.assertRaises(IntegrityError):
            bound_v2(statement=sample_statement())

    def test_a_type_that_names_nothing_is_refused(self):
        for value in (None, "", "   ", 12345, [], "​"):
            statement = sample_statement()
            statement["predicateType"] = value
            with self.subTest(predicate_type=repr(value)), self.assertRaises(
                FormatError
            ):
                bound(statement)

    def test_a_statement_with_no_type_is_refused(self):
        statement = sample_statement()
        del statement["predicateType"]
        with self.assertRaises(FormatError):
            bound(statement)


class BlockTests(unittest.TestCase):
    def test_a_different_block_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["chain"]["block_hash"] = "0x" + "99" * 32
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("different capture", str(caught.exception))

    def test_a_block_hash_that_is_not_a_string_is_refused(self):
        for value in (None, 12345, [], {}, True):
            statement = sample_statement()
            statement["predicate"]["chain"]["block_hash"] = value
            with self.subTest(block_hash=value), self.assertRaises(IntegrityError):
                bound(statement)

    def test_a_statement_with_no_chain_is_refused(self):
        statement = sample_statement()
        del statement["predicate"]["chain"]
        with self.assertRaises(FormatError):
            bound(statement)


class ReplayClaimTests(unittest.TestCase):
    def test_a_statement_claiming_the_canonical_chain_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["replay"]["canonical_chain_claim"] = True
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("canonical", str(caught.exception))

    def test_a_claim_that_is_not_a_boolean_is_refused(self):
        """`0` is falsey and is not the recorded decision the field carries."""
        for value in (0, 1, "false", None, [], "no"):
            statement = sample_statement()
            statement["predicate"]["replay"]["canonical_chain_claim"] = value
            with self.subTest(claim=value), self.assertRaises(IntegrityError):
                bound(statement)

    def test_a_report_claiming_the_canonical_chain_is_refused(self):
        """No Lazarus build establishes it, so a report saying otherwise is not
        one this binding will build a release on."""
        report = sample_report()
        report["header_bound"]["canonical_chain_claim"] = True
        with self.assertRaises(IntegrityError):
            bound(report=report)

    def test_a_statement_with_no_replay_block_is_refused(self):
        statement = sample_statement()
        del statement["predicate"]["replay"]
        with self.assertRaises(FormatError):
            bound(statement)

    def test_v2_refuses_provider_independence_on_either_side(self):
        statement = sample_statement_v2()
        statement["predicate"]["replay"]["provider_independence_claim"] = True
        with self.assertRaisesRegex(IntegrityError, "provider_independence"):
            bound_v2(statement=statement)

        report = sample_report_v2()
        report["chain_anchors"]["provider_independence_claim"] = True
        with self.assertRaisesRegex(IntegrityError, "provider independence"):
            bound_v2(report=report)


class ComponentTests(unittest.TestCase):
    def test_a_component_the_fixture_does_not_hold_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"].append(
            {
                "name": "extra.json",
                "path": "extra.json",
                "digest": {"sha256": "e" * 64},
                "bytes": 10,
            }
        )
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("extra.json", str(caught.exception))
        self.assertIn("does not hold", str(caught.exception))

    def test_a_component_the_statement_omits_is_refused(self):
        """The silent absence this plugin refuses everywhere else."""
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"] = [
            entry
            for entry in statement["predicate"]["fixture_subjects"]
            if entry["path"] != "plan.json"
        ]
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("plan.json", str(caught.exception))
        self.assertIn("does not name", str(caught.exception))

    def test_a_digest_that_disagrees_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"][1]["digest"]["sha256"] = "f" * 64
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("plan.json", str(caught.exception))

    def test_a_byte_count_that_disagrees_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"][1]["bytes"] += 1
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("bytes", str(caught.exception))

    def test_a_boolean_byte_count_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"][1]["bytes"] = True
        with self.assertRaises(IntegrityError):
            bound(statement)

    def test_a_component_named_twice_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"].append(
            copy.deepcopy(statement["predicate"]["fixture_subjects"][0])
        )
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("twice", str(caught.exception))

    def test_one_path_under_two_names_is_refused(self):
        """The duplicate-name rule fires first when a whole entry is repeated,
        so the path rule needs an entry that differs everywhere else."""
        statement = sample_statement()
        entry = copy.deepcopy(statement["predicate"]["fixture_subjects"][0])
        entry["name"] = "the same file again"
        entry["digest"] = {"sha256": "e" * 64}
        statement["predicate"]["fixture_subjects"].append(entry)
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("header.json twice", str(caught.exception))
        self.assertIn("two digests", str(caught.exception))

    def test_a_path_that_names_nothing_is_refused(self):
        for value in ("", "   ", None, 12345, "​"):
            statement = sample_statement()
            statement["predicate"]["fixture_subjects"][0]["path"] = value
            with self.subTest(path=repr(value)), self.assertRaises(FormatError):
                bound(statement)

    def test_no_components_at_all_is_refused(self):
        for value in ([], None, {}, "header.json"):
            statement = sample_statement()
            statement["predicate"]["fixture_subjects"] = value
            with self.subTest(subjects=value), self.assertRaises(FormatError):
                bound(statement)

    def test_a_digest_block_that_is_not_an_object_is_refused(self):
        for value in (None, "a" * 64, [], 12345):
            statement = sample_statement()
            statement["predicate"]["fixture_subjects"][0]["digest"] = value
            with self.subTest(digest=value), self.assertRaises(FormatError):
                bound(statement)


class ShapeTests(unittest.TestCase):
    def test_a_statement_that_is_not_an_object_is_refused(self):
        """`bind` is called directly here. The helper above substitutes the
        sample when it is handed `None`, so going through it would have tested
        the helper rather than the rule."""
        for value in (None, [], "statement", 12345, True):
            with self.subTest(statement=value), self.assertRaises(FormatError):
                bind(value, sample_manifest(), sample_report())

    def test_a_predicate_that_is_not_an_object_is_refused(self):
        for value in (None, [], "predicate", 12345):
            statement = sample_statement()
            statement["predicate"] = value
            with self.subTest(predicate=value), self.assertRaises(FormatError):
                bound(statement)

    def test_a_statement_with_no_predicate_is_refused(self):
        statement = sample_statement()
        del statement["predicate"]
        with self.assertRaises(FormatError):
            bound(statement)

    def test_it_refuses_at_the_first_disagreement(self):
        """A statement that disagrees about the block it pins is not a document
        whose component list is worth reading."""
        statement = sample_statement()
        statement["predicate"]["chain"]["block_hash"] = "0x" + "99" * 32
        statement["predicate"]["fixture_subjects"] = []
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("different capture", str(caught.exception))


class VersionTwoVocabularyTests(unittest.TestCase):
    def test_v2_release_uses_ariadnes_portable_identifier_contract(self):
        invisible = ("\u200b", "\x00", "\ue000", "\u2060", "\u96ea")
        for value in invisible:
            cases = []

            capture = sample_statement_v2()
            capture["predicate"]["capture"]["tool"] = value
            cases.append(("capture tool", capture))

            command = sample_statement_v2()
            command["predicate"]["capture"]["command"][0] = value
            cases.append(("capture command", command))

            component = sample_statement_v2()
            component["predicate"]["fixture_subjects"][0]["name"] = value
            cases.append(("component name", component))

            current = sample_statement_v2()
            current["predicate"]["deltas"]["current"]["name"] = value
            cases.append(("current name", current))

            subject = sample_statement_v2()
            subject["subject"][0]["name"] = value
            cases.append(("statement subject", subject))

            claim = sample_statement_v2()
            claim["predicate"]["claims"] = [
                {
                    "name": value,
                    "subject": {"sha256": "a" * 64},
                    "disposition": "passed",
                }
            ]
            cases.append(("claim name", claim))

            for field, statement in cases:
                with self.subTest(field=field, value=repr(value)), self.assertRaises(
                    (FormatError, IntegrityError)
                ):
                    bound_v2(statement=statement)

        for path in (
            "a/\u200b",
            "a/\x00",
            "a/\ue000",
            "a/\u2060",
            "a/\u96ea",
            "1:header.json",
            "\u96ea:header.json",
        ):
            statement = sample_statement_v2()
            manifest = sample_manifest_v2()
            statement["predicate"]["fixture_subjects"][0]["path"] = path
            manifest["components"][0]["path"] = path
            with self.subTest(path=repr(path)), self.assertRaises(
                (FormatError, IntegrityError)
            ):
                bound_v2(statement=statement, manifest=manifest)

    def test_a_structured_transaction_hash_proof_claim_is_refused(self):
        statement = sample_statement_v2()
        statement["predicate"]["transaction_hash_proved"] = True
        with self.assertRaisesRegex(IntegrityError, "outside its vocabulary"):
            bound_v2(statement=statement)

    def test_each_required_v2_block_must_be_present(self):
        for field in ("capture", "deltas", "claims", "commands"):
            statement = sample_statement_v2()
            del statement["predicate"][field]
            with self.subTest(field=field), self.assertRaises(FormatError):
                bound_v2(statement=statement)

    def test_v2_subject_references_use_ariadnes_digest_identity(self):
        def uncover_current(document):
            document["predicate"]["deltas"]["current"]["digest"] = {
                "sha256": "9" * 64
            }

        def uncover_claim(document):
            document["predicate"]["claims"] = [
                {
                    "name": "receipt membership",
                    "subject": {"sha256": "9" * 64},
                    "disposition": "passed",
                }
            ]

        def disagree_on_a_shared_algorithm(document):
            document["predicate"]["fixture_subjects"][0]["digest"]["sha512"] = (
                "1" * 128
            )
            document["subject"][0]["digest"]["sha512"] = "2" * 128

        for name, mutate in (
            ("current delta", uncover_current),
            ("claim", uncover_claim),
            ("fixture subject", disagree_on_a_shared_algorithm),
        ):
            statement = sample_statement_v2()
            mutate(statement)
            with self.subTest(reference=name), self.assertRaisesRegex(
                IntegrityError, "subject"
            ):
                bound_v2(statement=statement)

    def test_v2_capture_delta_claim_and_command_shapes_are_closed(self):
        mutations = (
            lambda document: document.__setitem__("unchecked", True),
            lambda document: document["subject"][0].__setitem__(
                "unchecked", True
            ),
            lambda document: document["predicate"]["capture"].__setitem__(
                "unchecked", True
            ),
            lambda document: document["predicate"]["fixture_subjects"][0].__setitem__(
                "unchecked", True
            ),
            lambda document: document["predicate"]["deltas"]["current"].__setitem__(
                "unchecked", True
            ),
            lambda document: document["predicate"]["deltas"].__setitem__(
                "unchecked", True
            ),
            lambda document: document["predicate"].__setitem__(
                "claims",
                [
                    {
                        "name": "unchecked",
                        "subject": {"sha256": "d" * 64},
                        "disposition": "passed",
                        "unchecked": True,
                    }
                ],
            ),
            lambda document: document["predicate"].__setitem__(
                "claims",
                [
                    {
                        "name": "unchecked",
                        "subject": {"sha256": "d" * 64},
                        "disposition": {"unexpected": True},
                    }
                ],
            ),
            lambda document: document["predicate"].__setitem__(
                "commands",
                [
                    {
                        "name": "network",
                        "argv": ["curl", "https://example.invalid"],
                        "determinism": "exact",
                    }
                ],
            ),
        )
        for mutate in mutations:
            statement = sample_statement_v2()
            mutate(statement)
            with self.subTest(mutate=mutate), self.assertRaises(
                (FormatError, IntegrityError)
            ):
                bound_v2(statement=statement)

    def test_unknown_v2_fields_do_not_cross_exception_surfaces(self):
        prefix = "PRIVATE_PROVIDER_VALUE_"
        keys = (prefix + "SECRET", prefix + "x" * 200_000)
        locations = (
            lambda body, key: body.__setitem__(key, True),
            lambda body, key: body["chain"].__setitem__(key, True),
            lambda body, key: body["evidence"].__setitem__(key, True),
            lambda body, key: body["replay"].__setitem__(key, True),
        )
        for key in keys:
            for locate in locations:
                statement = sample_statement_v2()
                locate(statement["predicate"], key)
                with self.subTest(key_bytes=len(key), locate=locate):
                    with self.assertRaises(IntegrityError) as raised:
                        bound_v2(statement=statement)
                    error = raised.exception
                    surfaces = {
                        "message": str(error),
                        "args": repr(error.args),
                        "repr": repr(error),
                        "cause": repr(error.__cause__),
                        "context": repr(error.__context__),
                        "traceback": "".join(
                            traceback.format_exception(
                                type(error), error, error.__traceback__
                            )
                        ),
                    }
                    self.assertIsNone(error.__cause__)
                    self.assertIsNone(error.__context__)
                    for name, rendered in surfaces.items():
                        with self.subTest(surface=name):
                            self.assertNotIn(prefix, rendered)
                            self.assertLessEqual(len(rendered.encode("utf-8")), 4096)

    def test_rejected_v2_values_do_not_cross_exception_surfaces(self):
        prefix = "PRIVATE_PROVIDER_VALUE_"
        values = (prefix + "SECRET", prefix + "x" * 200_000)

        def duplicate_fixture_name(document, value):
            document["predicate"]["fixture_subjects"][0]["name"] = value
            document["predicate"]["fixture_subjects"][1]["name"] = value

        def duplicate_subject_name(document, value):
            document["subject"][0]["name"] = value
            document["subject"][1]["name"] = value

        locations = (
            lambda document, value: document.__setitem__("_type", value),
            lambda document, value: document.__setitem__("predicateType", value),
            lambda document, value: document["predicate"]["chain"].__setitem__(
                "state_root", value
            ),
            lambda document, value: document["predicate"]["evidence"].__setitem__(
                "proof_backed", value
            ),
            lambda document, value: document["predicate"]["replay"].__setitem__(
                "reaches_network", value
            ),
            lambda document, value: document["predicate"]["fixture_subjects"][
                0
            ].__setitem__("path", value),
            duplicate_fixture_name,
            duplicate_subject_name,
        )
        for value in values:
            for locate in locations:
                statement = sample_statement_v2()
                locate(statement, value)
                with self.subTest(value_bytes=len(value), locate=locate):
                    with self.assertRaises(IntegrityError) as raised:
                        bound_v2(statement=statement)
                    error = raised.exception
                    surfaces = {
                        "message": str(error),
                        "args": repr(error.args),
                        "repr": repr(error),
                        "cause": repr(error.__cause__),
                        "context": repr(error.__context__),
                        "traceback": "".join(
                            traceback.format_exception(
                                type(error), error, error.__traceback__
                            )
                        ),
                    }
                    self.assertIsNone(error.__cause__)
                    self.assertIsNone(error.__context__)
                    for name, rendered in surfaces.items():
                        with self.subTest(surface=name):
                            self.assertNotIn(prefix, rendered)
                            self.assertLessEqual(len(rendered.encode("utf-8")), 4096)




class StatementTypeTests(unittest.TestCase):
    """The envelope, not the predicate.

    A predicate type says how to read `predicate`. The statement type says the
    document is the kind of thing that has one.
    """

    def test_a_document_that_is_not_a_statement_is_refused(self):
        statement = sample_statement()
        statement["_type"] = "https://example.invalid/receipt/v1"
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("no envelope", str(caught.exception))

    def test_a_document_with_no_type_is_refused(self):
        statement = sample_statement()
        del statement["_type"]
        with self.assertRaises(FormatError):
            bound(statement)

    def test_a_type_that_names_nothing_is_refused(self):
        """Shape and disagreement are told apart here as they are for the
        predicate type: a caller catching one should not have to catch the
        other to learn a field was blank."""
        for value in (None, "", "   ", 12345, [], {}, True, "​"):
            statement = sample_statement()
            statement["_type"] = value
            with self.subTest(statement_type=repr(value)), self.assertRaises(
                FormatError
            ):
                bound(statement)

    def test_the_type_it_binds_is_the_in_toto_one(self):
        self.assertEqual(IN_TOTO_STATEMENT_TYPE, "https://in-toto.io/Statement/v1")


class ChainTests(unittest.TestCase):
    """The block hash is not the whole of which capture this is.

    A statement pinning the right hash while naming another chain, another height
    or another state root reads as though all four were corroborated.
    """

    def test_another_chain_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["chain"]["chain_id"] = 137
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("137", str(caught.exception))

    def test_another_block_number_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["chain"]["block_number"] = BLOCK_NUMBER + 1
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn(str(BLOCK_NUMBER), str(caught.exception))

    def test_another_state_root_is_refused(self):
        """Every proof in the fixture was checked against the header's root."""
        statement = sample_statement()
        statement["predicate"]["chain"]["state_root"] = "0x" + "ab" * 32
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("state root", str(caught.exception))

    def test_v2_receipts_root_is_independent_of_the_state_root(self):
        statement = sample_statement_v2()
        del statement["predicate"]["chain"]["receipts_root"]
        with self.assertRaises(FormatError):
            bound_v2(statement=statement)

        statement = sample_statement_v2()
        statement["predicate"]["chain"]["receipts_root"] = STATE_ROOT
        with self.assertRaisesRegex(IntegrityError, "receipts root"):
            bound_v2(statement=statement)

    def test_v2_chain_hashes_use_the_canonical_lowercase_spelling(self):
        fields = ("block_hash", "state_root", "receipts_root")
        for field in fields:
            statement = sample_statement_v2()
            manifest = sample_manifest_v2()
            report = sample_report_v2()
            canonical = "0x" + "ab" * 32
            statement["predicate"]["chain"][field] = canonical.upper().replace(
                "0X", "0x"
            )
            if field == "block_hash":
                report["block_hash"] = canonical
                manifest["block"]["hash"] = canonical
            elif field == "state_root":
                report["state_root"] = canonical
            else:
                report["receipts_root"] = canonical
                manifest["receipts_root"] = canonical
            with self.subTest(field=field), self.assertRaises(IntegrityError):
                bound_v2(statement=statement, manifest=manifest, report=report)

    def test_v2_chain_has_no_transaction_hash_authority(self):
        statement = sample_statement_v2()
        statement["predicate"]["chain"]["transaction_hash"] = "0x" + "99" * 32
        with self.assertRaisesRegex(IntegrityError, "outside its vocabulary"):
            bound_v2(statement=statement)

    def test_a_state_root_in_the_other_case_still_binds(self):
        statement = sample_statement()
        statement["predicate"]["chain"]["state_root"] = STATE_ROOT.upper().replace(
            "0X", "0x"
        )
        self.assertEqual(bound(statement), list(CHECKS))

    def test_a_chain_field_left_out_is_refused(self):
        for field in ("chain_id", "block_number", "block_hash", "state_root"):
            statement = sample_statement()
            del statement["predicate"]["chain"][field]
            with self.subTest(field=field), self.assertRaises(FormatError):
                bound(statement)

    def test_a_boolean_chain_id_is_refused(self):
        """`True` equals 1 and this fixture is chain 1."""
        statement = sample_statement()
        statement["predicate"]["chain"]["chain_id"] = True
        with self.assertRaises(IntegrityError):
            bound(statement)

    def test_chain_fields_of_the_wrong_shape_are_refused(self):
        for field in ("chain_id", "block_number", "block_hash", "state_root"):
            for value in (None, "", "   ", [], {}, 1.5, "​"):
                statement = sample_statement()
                statement["predicate"]["chain"][field] = value
                with self.subTest(field=field, value=repr(value)), self.assertRaises(
                    IntegrityError
                ):
                    bound(statement)

    def test_a_chain_that_is_not_an_object_is_refused(self):
        for value in (None, [], "mainnet", 1):
            statement = sample_statement()
            statement["predicate"]["chain"] = value
            with self.subTest(chain=value), self.assertRaises(FormatError):
                bound(statement)

    def test_a_manifest_chain_id_that_is_not_a_quantity_is_refused(self):
        for value in (None, "one", "", 1):
            manifest = sample_manifest()
            manifest["chain_id"] = value
            with self.subTest(chain_id=value), self.assertRaises(FormatError):
                bound(manifest=manifest)

    def test_a_hex_quantity_that_is_not_a_number_is_refused(self):
        """0x and then something that is not hex. The prefix check passes and
        the conversion is where it goes wrong."""
        for value in ("0x", "0xzz", "0x 1", "0x1.5"):
            manifest = sample_manifest()
            manifest["chain_id"] = value
            with self.subTest(chain_id=value), self.assertRaises(
                FormatError
            ) as caught:
                bound(manifest=manifest)
            self.assertIn("hex quantity", str(caught.exception))

    def test_a_report_block_number_that_is_not_a_quantity_is_refused(self):
        for value in (None, "twelve", "", 12):
            report = sample_report()
            report["block_number"] = value
            with self.subTest(block_number=value), self.assertRaises(FormatError):
                bound(report=report)


class NetworkClaimTests(unittest.TestCase):
    """The other half of the replay block.

    `canonical_chain_claim` overstates what a header proves. `reaches_network`
    overstates where the bytes came from: a statement saying verification went to
    a node has a reader believe the records were corroborated live.
    """

    def test_a_statement_claiming_verification_reached_a_node_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["replay"]["reaches_network"] = True
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("reaches_network", str(caught.exception))

    def test_a_network_claim_that_is_not_a_boolean_is_refused(self):
        for value in (0, 1, "false", None, [], "no"):
            statement = sample_statement()
            statement["predicate"]["replay"]["reaches_network"] = value
            with self.subTest(claim=value), self.assertRaises(IntegrityError):
                bound(statement)

    def test_either_claim_left_out_is_refused(self):
        for field in REPLAY_CLAIMS:
            statement = sample_statement()
            del statement["predicate"]["replay"][field]
            with self.subTest(field=field), self.assertRaises(FormatError):
                bound(statement)


class SubjectTests(unittest.TestCase):
    """The list an in-toto reader actually reads."""

    def test_a_component_absent_from_the_subject_list_is_refused(self):
        statement = sample_statement()
        statement["subject"] = [
            entry for entry in statement["subject"] if entry["name"] != "plan.json"
        ]
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("plan.json", str(caught.exception))

    def test_a_subject_list_matched_by_digest_rather_than_name_binds(self):
        """The names in the subject list are labels; the digests carry it."""
        statement = sample_statement()
        for index, entry in enumerate(statement["subject"]):
            entry["name"] = "component-%d" % index
        self.assertEqual(bound(statement), list(CHECKS))

    def test_a_subject_digest_in_the_other_case_still_covers(self):
        statement = sample_statement()
        for entry in statement["subject"]:
            entry["digest"]["sha256"] = entry["digest"]["sha256"].upper()
        self.assertEqual(bound(statement), list(CHECKS))

    def test_two_subjects_under_one_name_are_refused(self):
        """A reader matching by name cannot tell which digest was meant."""
        statement = sample_statement()
        statement["subject"].append(
            {"name": "plan.json", "digest": {"sha256": "e" * 64}}
        )
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("twice", str(caught.exception))

    def test_a_subject_naming_nothing_is_refused(self):
        for value in (None, "", "   ", 12345, [], "​"):
            statement = sample_statement()
            statement["subject"][0]["name"] = value
            with self.subTest(name=repr(value)), self.assertRaises(FormatError):
                bound(statement)

    def test_a_subject_with_no_digest_is_refused(self):
        statement = sample_statement()
        del statement["subject"][0]["digest"]
        with self.assertRaises(FormatError):
            bound(statement)

    def test_a_subject_digest_that_names_nothing_is_refused(self):
        for value in (None, "", "   ", 12345, [], "​"):
            statement = sample_statement()
            statement["subject"][0]["digest"]["sha256"] = value
            with self.subTest(sha256=repr(value)), self.assertRaises(FormatError):
                bound(statement)

    def test_no_subject_list_at_all_is_refused(self):
        statement = sample_statement()
        del statement["subject"]
        with self.assertRaises(FormatError):
            bound(statement)

    def test_an_empty_subject_list_is_refused(self):
        for value in ([], None, {}, "header.json"):
            statement = sample_statement()
            statement["subject"] = value
            with self.subTest(subject=value), self.assertRaises(FormatError):
                bound(statement)

    def test_a_fixture_subject_naming_nothing_is_refused(self):
        for value in (None, "", "   ", 12345, [], "​"):
            statement = sample_statement()
            statement["predicate"]["fixture_subjects"][0]["name"] = value
            with self.subTest(name=repr(value)), self.assertRaises(FormatError):
                bound(statement)

    def test_two_fixture_subjects_under_one_name_are_refused(self):
        statement = sample_statement()
        entry = copy.deepcopy(statement["predicate"]["fixture_subjects"][0])
        entry["path"] = "other.json"
        statement["predicate"]["fixture_subjects"].append(entry)
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("twice", str(caught.exception))


class TrustedDocumentTests(unittest.TestCase):
    """The manifest and the report are the caller's, not a producer's.

    `verify_manifest` and `verify_fixture` establish what they say. These tests
    are about the difference between a refusal naming the field and a traceback
    out of the middle of a comparison, for a caller who handed over the wrong
    document.
    """

    def test_a_manifest_component_of_the_wrong_shape_is_refused(self):
        for field, value in (
            ("path", []), ("path", None), ("path", "   "), ("path", "\u200b"),
            ("sha256", {}), ("sha256", None), ("sha256", ""),
            ("bytes", None), ("bytes", "1418"), ("bytes", True), ("bytes", -1),
        ):
            manifest = sample_manifest()
            manifest["components"][1][field] = value
            with self.subTest(field=field, value=repr(value)), self.assertRaises(
                FormatError
            ):
                bound(manifest=manifest)

    def test_a_manifest_missing_what_the_binding_reads_is_refused(self):
        for field in ("chain_id", "components"):
            manifest = sample_manifest()
            del manifest[field]
            with self.subTest(field=field), self.assertRaises(FormatError):
                bound(manifest=manifest)

    def test_a_manifest_that_is_not_an_object_is_refused(self):
        for value in (None, [], "manifest", 12345):
            with self.subTest(manifest=value), self.assertRaises(FormatError):
                bind(sample_statement(), value, sample_report())

    def test_a_manifest_holding_no_components_is_refused(self):
        for value in ([], None, {}, "header.json"):
            manifest = sample_manifest()
            manifest["components"] = value
            with self.subTest(components=value), self.assertRaises(FormatError):
                bound(manifest=manifest)

    def test_a_report_missing_what_the_binding_reads_is_refused(self):
        for field in (
            "block_hash", "block_number", "state_root", "evidence_counts",
            "header_bound",
        ):
            report = sample_report()
            del report[field]
            with self.subTest(field=field), self.assertRaises(FormatError):
                bound(report=report)

    def test_a_report_count_of_the_wrong_shape_is_refused(self):
        for name in EVIDENCE_CLASSES:
            for value in (None, "", [], {}, 1.5, True, -1):
                report = sample_report()
                report["evidence_counts"][name] = value
                with self.subTest(name=name, value=repr(value)), self.assertRaises(
                    FormatError
                ):
                    bound(report=report)

    def test_a_report_count_left_out_is_refused(self):
        for name in EVIDENCE_CLASSES:
            report = sample_report()
            del report["evidence_counts"][name]
            with self.subTest(name=name), self.assertRaises(FormatError):
                bound(report=report)

    def test_a_report_block_field_that_names_nothing_is_refused(self):
        for field in ("block_hash", "block_number", "state_root"):
            for value in (None, "", "   ", 12345, [], "\u200b"):
                report = sample_report()
                report[field] = value
                with self.subTest(field=field, value=repr(value)), self.assertRaises(
                    FormatError
                ):
                    bound(report=report)

    def test_a_report_with_no_canonical_chain_claim_is_refused(self):
        report = sample_report()
        del report["header_bound"]["canonical_chain_claim"]
        with self.assertRaises(FormatError):
            bound(report=report)

    def test_a_report_that_is_not_an_object_is_refused(self):
        for value in (None, [], "report", 12345):
            with self.subTest(report=value), self.assertRaises(FormatError):
                bind(sample_statement(), sample_manifest(), value)


class NameSpellingTests(unittest.TestCase):
    """Two Unicode spellings of one name are one name to a reader."""

    COMPOSED = unicodedata.normalize("NFC", "pl\u00e1n.json")
    DECOMPOSED = unicodedata.normalize("NFD", "pl\u00e1n.json")

    def test_the_two_spellings_differ_as_strings(self):
        """Without this the rest of the class would pass for the wrong reason."""
        self.assertNotEqual(self.COMPOSED, self.DECOMPOSED)

    def test_one_subject_name_in_two_spellings_is_refused(self):
        statement = sample_statement()
        statement["subject"][0]["name"] = self.COMPOSED
        statement["subject"].append(
            {"name": self.DECOMPOSED, "digest": {"sha256": "e" * 64}}
        )
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("twice", str(caught.exception))

    def test_one_fixture_subject_name_in_two_spellings_is_refused(self):
        statement = sample_statement()
        subjects = statement["predicate"]["fixture_subjects"]
        subjects[0]["name"] = self.COMPOSED
        entry = copy.deepcopy(subjects[0])
        entry["name"] = self.DECOMPOSED
        entry["path"] = "other.json"
        subjects.append(entry)
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("twice", str(caught.exception))

    def test_names_that_differ_by_more_than_spelling_still_bind(self):
        statement = sample_statement()
        statement["subject"][0]["name"] = self.COMPOSED
        statement["subject"][1]["name"] = "plan.json"
        self.assertEqual(bound(statement), list(CHECKS))


class LimitTests(unittest.TestCase):
    """A refusal that names a hundred thousand paths is a refusal nobody reads."""

    @staticmethod
    def components(count):
        return [
            {
                "name": "c%d" % index,
                "path": "c%d" % index,
                "digest": {"sha256": "%064x" % index},
                "bytes": index,
            }
            for index in range(count)
        ]

    def test_more_components_than_a_fixture_can_hold_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"] = self.components(
            MAX_FIXTURE_SUBJECTS + 1
        )
        with self.assertRaises(ResourceLimitError) as caught:
            bound(statement)
        self.assertIn(str(MAX_FIXTURE_SUBJECTS), str(caught.exception))

    def test_exactly_the_limit_is_read_rather_than_refused(self):
        """The cap is a bound on work. A fixture may hold that many, so a
        statement describing that many is read and then disagreed with."""
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"] = self.components(
            MAX_FIXTURE_SUBJECTS
        )
        with self.assertRaises(IntegrityError):
            bound(statement)

    def test_more_subjects_than_this_reads_is_refused(self):
        statement = sample_statement()
        statement["subject"] = [
            {"name": "s%d" % index, "digest": {"sha256": "%064x" % index}}
            for index in range(MAX_SUBJECTS + 1)
        ]
        with self.assertRaises(ResourceLimitError) as caught:
            bound(statement)
        self.assertIn(str(MAX_SUBJECTS), str(caught.exception))

    def test_v2_component_cap_precedes_digest_and_coverage_work(self):
        statement = sample_statement_v2()
        components = self.components(MAX_FIXTURE_SUBJECTS + 1)
        statement["predicate"]["fixture_subjects"] = components
        statement["subject"] = [
            {"name": entry["name"], "digest": entry["digest"]}
            for entry in components
        ] + [
            {"name": "fixture-v2", "digest": {"sha256": "d" * 64}}
        ]
        with mock.patch.object(
            binding_module,
            "_digest_set",
            wraps=binding_module._digest_set,
        ) as digest_check:
            with self.assertRaises(ResourceLimitError):
                bound_v2(statement=statement)
        self.assertEqual(digest_check.call_count, 0)

    def test_v2_subject_cap_precedes_digest_and_coverage_work(self):
        statement = sample_statement_v2()
        while len(statement["subject"]) <= MAX_SUBJECTS:
            index = len(statement["subject"])
            statement["subject"].append(
                {
                    "name": "s%d" % index,
                    "digest": {"sha256": "%064x" % index},
                }
            )
        with mock.patch.object(
            binding_module,
            "_digest_set",
            wraps=binding_module._digest_set,
        ) as digest_check:
            with self.assertRaises(ResourceLimitError):
                bound_v2(statement=statement)
        self.assertEqual(digest_check.call_count, 0)

    def test_a_refusal_counts_the_names_it_does_not_spell_out(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"] = self.components(200)
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        message = str(caught.exception)
        self.assertIn("more", message)
        self.assertLess(len(message), 500)


if __name__ == "__main__":
    unittest.main()
