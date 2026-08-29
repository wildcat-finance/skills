"""Gates 2 and 5, and the two checks that come with them.

The evidence check gets the most attention here, because it is the one carrying a
rule no other predicate has: a count of proved records is refused when there was
nothing to prove them against.
"""

import copy
import hashlib
import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import statement  # noqa: E402
from ariadne_lib.predicates import state_fixture as fixture  # noqa: E402

HEADER = {"sha256": hashlib.sha256(b"header").hexdigest()}
PROOFS = {"sha256": hashlib.sha256(b"proofs").hexdigest()}
RPC = {"sha256": hashlib.sha256(b"rpc").hexdigest()}
ELSEWHERE = {"sha256": hashlib.sha256(b"some other fixture").hexdigest()}
PARAMETERS = {"sha256": hashlib.sha256(b"parameters").hexdigest()}
BLOCK_HASH = "0x" + hashlib.sha256(b"block").hexdigest()
STATE_ROOT = "0x" + hashlib.sha256(b"root").hexdigest()
RECEIPTS_ROOT = "0x" + hashlib.sha256(b"receipts").hexdigest()

LAZARUS_MANIFEST_SCHEMA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))),
    "plugins", "lazarus", "schemas", "manifest-v1.json",
)
"""Lazarus's published manifest schema, read by one test below.

A path out of this plugin, which nothing else here does. It resolves only inside
the marketplace checkout; an installed copy of Ariadne alone skips that test
rather than failing it.
"""


def predicate(**overrides):
    out = {
        "chain": {
            "chain_id": 1,
            "block_number": 13097494,
            "block_hash": BLOCK_HASH,
            "state_root": STATE_ROOT,
        },
        "capture": {
            "tool": "lazarus",
            "tool_version": "0.1.0",
            "command": ["python3", "scripts/lazarus.py", "capture"],
            "parameters_digest": PARAMETERS,
        },
        "fixture_subjects": [
            {
                "name": "the captured block header",
                "path": "header.json",
                "digest": HEADER,
                "bytes": 17204,
            },
            {
                "name": "the state proofs",
                "path": "proofs.jsonl",
                "digest": PROOFS,
                "bytes": 8688,
            },
        ],
        "evidence": {"proof_backed": 2, "header_bound": 1, "recorded_rpc": 4},
        "replay": {"reaches_network": False, "canonical_chain_claim": False},
        "deltas": {
            "baseline": None,
            "reason": "first capture of this block; nothing earlier to compare",
        },
        "claims": [],
        "commands": [],
    }
    out.update(overrides)
    return out


def built(body, subject=None):
    return statement.Statement.from_dict(
        {
            "_type": statement.STATEMENT_TYPE,
            "subject": subject
            or [
                {"name": "header.json", "digest": HEADER},
                {"name": "proofs.jsonl", "digest": PROOFS},
            ],
            "predicateType": fixture.TYPE,
            "predicate": body,
        }
    )


def predicate_v2(**overrides):
    out = copy.deepcopy(predicate())
    out["chain"]["receipts_root"] = RECEIPTS_ROOT
    out["evidence"]["receipt_trie_proved"] = 2
    out["replay"]["provider_independence_claim"] = False
    out["deltas"]["current"] = {"name": "fixture-v2", "digest": HEADER}
    out.update(overrides)
    return out


def built_v2(body, subject=None):
    return statement.Statement.from_dict(
        {
            "_type": statement.STATEMENT_TYPE,
            "subject": subject
            or [
                {"name": "header.json", "digest": HEADER},
                {"name": "proofs.jsonl", "digest": PROOFS},
            ],
            "predicateType": fixture.V2.TYPE,
            "predicate": body,
        }
    )


def gate_v2(number, body, subject=None):
    for found in fixture.V2.check(built_v2(body, subject)):
        if found.number == number:
            return found
    raise AssertionError("no gate %r" % number)


def named_v2(name, body, subject=None):
    for found in fixture.V2.check(built_v2(body, subject)):
        if found.name == name:
            return found
    raise AssertionError("no check named %r" % name)


def gate(number, body, subject=None):
    for found in fixture.check(built(body, subject)):
        if found.number == number:
            return found
    raise AssertionError("no gate %r" % number)


def named(name, body, subject=None):
    for found in fixture.check(built(body, subject)):
        if found.name == name:
            return found
    raise AssertionError("no check named %r" % name)


class GateTwoTests(unittest.TestCase):
    def test_a_complete_pin_and_capture_record_passes(self):
        found = gate(2, predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("chain 1 block 13097494", found.detail)
        self.assertIn("lazarus 0.1.0", found.detail)

    def test_each_pin_field_absent_fails(self):
        for field in fixture.CHAIN_REQUIRED:
            body = predicate()
            del body["chain"][field]
            with self.subTest(field=field):
                found = gate(2, body)
                self.assertFalse(found.passed)
                self.assertIn(field, found.detail)

    def test_a_hex_block_number_fails(self):
        """The wire form. `"0xc7da16" < "0x2"` is true, because that orders text."""
        body = predicate()
        body["chain"]["block_number"] = "0xc7da16"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("whole number", found.detail)

    def test_a_hex_chain_id_fails(self):
        body = predicate()
        body["chain"]["chain_id"] = "0x1"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("chain_id", found.detail)

    def test_a_boolean_block_number_fails(self):
        """`True` is an integer in Python and would read as block one."""
        body = predicate()
        body["chain"]["block_number"] = True
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("whole number", found.detail)

    def test_genesis_is_a_block(self):
        """`0` lands in `missing()` as though the field were absent."""
        body = predicate()
        body["chain"]["block_number"] = 0
        found = gate(2, body)
        self.assertTrue(found.passed, found.detail)

    def test_an_uppercased_block_hash_fails(self):
        body = predicate()
        body["chain"]["block_hash"] = BLOCK_HASH.upper().replace("0X", "0x")
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("block_hash", found.detail)

    def test_an_all_zero_block_hash_fails(self):
        """It matches the pattern and identifies nothing."""
        body = predicate()
        body["chain"]["block_hash"] = fixture.ZERO_HASH
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("block_hash", found.detail)

    def test_a_block_hash_of_the_wrong_length_fails(self):
        body = predicate()
        body["chain"]["block_hash"] = "0xdeadbeef"
        found = gate(2, body)
        self.assertFalse(found.passed)

    def test_hash_fields_with_a_terminal_line_feed_fail(self):
        for field, value in (
            ("block_hash", BLOCK_HASH),
            ("state_root", STATE_ROOT),
        ):
            body = predicate()
            body["chain"][field] = value + "\n"
            found = gate(2, body)
            with self.subTest(field=field):
                self.assertFalse(found.passed)
                self.assertIn(field, found.detail)

    def test_an_all_zero_hash_cannot_evade_the_sentinel_with_a_line_feed(self):
        body = predicate()
        body["chain"]["block_hash"] = fixture.ZERO_HASH + "\n"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("block_hash", found.detail)

    def test_a_state_root_that_is_present_and_malformed_fails(self):
        body = predicate()
        body["chain"]["state_root"] = "0xnope"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("state_root", found.detail)

    def test_a_pin_with_no_state_root_passes_the_gate(self):
        """Whether a fixture needs one depends on what it claims, which is the
        evidence check's rule rather than this gate's."""
        body = predicate()
        del body["chain"]["state_root"]
        body["evidence"] = {"proof_backed": 0, "header_bound": 1, "recorded_rpc": 4}
        found = gate(2, body)
        self.assertTrue(found.passed, found.detail)

    def test_a_pin_carrying_an_undefined_field_fails(self):
        body = predicate()
        body["chain"]["difficulty"] = "0x0"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("difficulty", found.detail)

    def test_each_capture_field_absent_fails(self):
        for field in fixture.CAPTURE_REQUIRED:
            body = predicate()
            del body["capture"][field]
            with self.subTest(field=field):
                found = gate(2, body)
                self.assertFalse(found.passed)
                self.assertIn(field, found.detail)

    def test_a_capture_command_that_is_a_string_fails(self):
        body = predicate()
        body["capture"]["command"] = "python3 scripts/lazarus.py capture"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("argv", found.detail)

    def test_a_component_digest_the_statement_does_not_cover_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["digest"] = ELSEWHERE
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_no_components_fails(self):
        body = predicate()
        body["fixture_subjects"] = []
        found = gate(2, body)
        self.assertFalse(found.passed)

    def test_an_empty_component_is_a_component(self):
        body = predicate()
        body["fixture_subjects"][1]["bytes"] = 0
        found = gate(2, body)
        self.assertTrue(found.passed, found.detail)

    def test_a_negative_byte_count_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["bytes"] = -1
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("bytes", found.detail)

    def test_a_byte_count_over_the_ceiling_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["bytes"] = fixture.MAX_BYTES + 1
        found = gate(2, body)
        self.assertFalse(found.passed)

    def test_a_component_path_leaving_the_fixture_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["path"] = "../outside.jsonl"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("fixture-relative", found.detail)

    def test_a_backslash_traversal_is_refused(self):
        """A single backslash separates segments on Windows. An earlier version
        normalised only a doubled backslash, so `a\\..\\..\\b` reached a POSIX
        consumer as one odd filename and a Windows consumer as a traversal. Found
        by sweeping `usable_path` in round 5, and the same defect was live in the
        dataset predicate, which this function was copied from."""
        for value in ("a\\..\\..\\b", "..\\outside", "a\\b\\..\\..\\..\\c"):
            with self.subTest(path=value):
                self.assertFalse(fixture.usable_path(value))

    def test_a_backslash_inside_a_name_is_not_a_traversal(self):
        """Refusing every backslash would refuse a legitimate POSIX filename that
        happens to contain one."""
        self.assertTrue(fixture.usable_path("a\\b"))

    def test_a_unc_prefix_is_refused(self):
        self.assertFalse(fixture.usable_path("\\\\server\\share\\x"))

    def test_a_trailing_separator_is_refused(self):
        """It names a directory, and a component is a file."""
        self.assertFalse(fixture.usable_path("a/"))

    def test_one_path_listed_twice_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["path"] = "header.json"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("listed twice", found.detail)


class EvidenceTests(unittest.TestCase):
    def test_the_three_counts_are_reported(self):
        found = named("evidence", predicate())
        self.assertTrue(found.passed, found.detail)
        for name in fixture.EVIDENCE_CLASSES:
            self.assertIn(name, found.detail)

    def test_each_class_key_absent_fails(self):
        for name in fixture.EVIDENCE_CLASSES:
            body = predicate()
            del body["evidence"][name]
            with self.subTest(evidence_class=name):
                found = named("evidence", body)
                self.assertFalse(found.passed)
                self.assertIn(name, found.detail)

    def test_no_evidence_block_fails(self):
        body = predicate()
        del body["evidence"]
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("records a zero in each class", found.detail)

    def test_a_fixture_that_proved_nothing_records_zeroes(self):
        body = predicate()
        body["evidence"] = {"proof_backed": 0, "header_bound": 0, "recorded_rpc": 0}
        found = named("evidence", body)
        self.assertTrue(found.passed, found.detail)

    def test_a_negative_count_fails(self):
        body = predicate()
        body["evidence"]["recorded_rpc"] = -1
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("from 0 to", found.detail)

    def test_a_boolean_count_fails(self):
        """`True` is an integer in Python, so a check that only asked whether the
        value was a number would read a producer's mistake as one record."""
        for name in fixture.EVIDENCE_CLASSES:
            for value in (True, False):
                body = predicate()
                body["evidence"][name] = value
                with self.subTest(evidence_class=name, value=value):
                    found = named("evidence", body)
                    self.assertFalse(found.passed)
                    self.assertIn(name, found.detail)

    def test_a_count_over_the_ceiling_fails(self):
        """The ceiling comes from Lazarus's manifest schema, and it was in this
        type's published schema before it was in the module. A sweep found the
        gap: a count of 10**30 verified clean and the schema refused it."""
        body = predicate()
        body["evidence"]["recorded_rpc"] = fixture.MAX_COUNT + 1
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("recorded_rpc", found.detail)

    def test_a_count_at_the_ceiling_passes(self):
        body = predicate()
        body["evidence"]["recorded_rpc"] = fixture.MAX_COUNT
        found = named("evidence", body)
        self.assertTrue(found.passed, found.detail)

    def test_a_float_count_fails(self):
        body = predicate()
        body["evidence"]["proof_backed"] = 2.0
        found = named("evidence", body)
        self.assertFalse(found.passed)

    def test_an_undefined_evidence_class_fails(self):
        body = predicate()
        body["evidence"]["trusted_oracle"] = 3
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("trusted_oracle", found.detail)

    def test_proved_records_with_no_state_root_fails(self):
        """The rule this predicate exists for."""
        body = predicate()
        del body["chain"]["state_root"]
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("no state root", found.detail)

    def test_the_rule_reaches_statements_gate_two_accepts(self):
        """Gate 2 used to require the root, which made this rule unreachable: a
        statement it would refuse had already failed the gate. The split is what
        gives the rule something to decide."""
        body = predicate()
        del body["chain"]["state_root"]
        self.assertTrue(gate(2, body).passed, "gate 2 should accept a rootless pin")
        self.assertFalse(named("evidence", body).passed)

    def test_exactly_one_proved_record_needs_a_state_root(self):
        """The boundary, and the smallest claim a fixture can make. A mutation
        probe changed the rule from `> 0` to `> 1` and the suite stayed green,
        because every other test here counts two."""
        body = predicate()
        del body["chain"]["state_root"]
        body["evidence"]["proof_backed"] = 1
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("1 proof_backed record(s)", found.detail)

    def test_the_rule_holds_at_each_count_from_zero_upward(self):
        """Swept rather than sampled, because the rule is a threshold and a
        threshold is where an off-by-one lives."""
        for count in (0, 1, 2, 3, 100, fixture.MAX_COUNT):
            body = predicate()
            del body["chain"]["state_root"]
            body["evidence"]["proof_backed"] = count
            with self.subTest(proof_backed=count):
                found = named("evidence", body)
                self.assertEqual(found.passed, count == 0, found.detail)

    def test_no_proved_records_needs_no_state_root(self):
        body = predicate()
        del body["chain"]["state_root"]
        body["evidence"]["proof_backed"] = 0
        found = named("evidence", body)
        self.assertTrue(found.passed, found.detail)

    def test_proved_records_against_an_all_zero_state_root_fails(self):
        """The unset value. It matches the hash pattern, so a check that only
        asked about the shape would let a proof-backed count sit beside a root
        nobody filled in -- the same shape as an emitted-but-empty field."""
        body = predicate()
        body["chain"]["state_root"] = fixture.ZERO_HASH
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("no state root", found.detail)

    def test_an_all_zero_state_root_with_no_proofs_still_fails_the_gate(self):
        """Gate 2 checks a state root that is present, so the unset value is
        refused there whether or not anything claims a proof."""
        body = predicate()
        body["chain"]["state_root"] = fixture.ZERO_HASH
        body["evidence"]["proof_backed"] = 0
        self.assertFalse(gate(2, body).passed)

    def test_proved_records_against_a_malformed_state_root_fails(self):
        """A root that does not parse is not a root to have proved anything
        against, even though gate 2 reports that fault separately."""
        body = predicate()
        body["chain"]["state_root"] = "0xnope"
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("no state root", found.detail)

    def test_a_chain_block_that_is_not_an_object_does_not_raise(self):
        body = predicate()
        body["chain"] = "block 13097494"
        found = named("evidence", body)
        self.assertFalse(found.passed)


class ReplayTests(unittest.TestCase):
    def test_a_closed_boundary_with_no_chain_claim_passes(self):
        found = named("replay", predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("reaches no network", found.detail)

    def test_each_field_absent_fails(self):
        for field in fixture.REPLAY_REQUIRED:
            body = predicate()
            del body["replay"][field]
            with self.subTest(field=field):
                found = named("replay", body)
                self.assertFalse(found.passed)
                self.assertIn(field, found.detail)

    def test_no_replay_block_fails(self):
        body = predicate()
        del body["replay"]
        found = named("replay", body)
        self.assertFalse(found.passed)
        self.assertIn("recorded rather than assumed", found.detail)

    def test_either_field_true_fails_with_the_reason(self):
        for field in fixture.REPLAY_REQUIRED:
            body = predicate()
            body["replay"][field] = True
            with self.subTest(field=field):
                found = named("replay", body)
                self.assertFalse(found.passed)
                self.assertIn(fixture.REFUSALS[field], found.detail)

    def test_a_zero_is_not_a_recorded_decision(self):
        """`0` is falsey and is not in the field's vocabulary. A producer writing
        it has not made the decision the field records."""
        body = predicate()
        body["replay"]["reaches_network"] = 0
        found = named("replay", body)
        self.assertFalse(found.passed)
        self.assertIn("must be false", found.detail)

    def test_a_string_false_fails(self):
        body = predicate()
        body["replay"]["canonical_chain_claim"] = "false"
        found = named("replay", body)
        self.assertFalse(found.passed)

    def test_an_undefined_replay_field_fails(self):
        body = predicate()
        body["replay"]["verified_against_chain"] = False
        found = named("replay", body)
        self.assertFalse(found.passed)
        self.assertIn("verified_against_chain", found.detail)


class GateFiveTests(unittest.TestCase):
    def test_a_first_capture_with_a_null_baseline_passes(self):
        found = gate(5, predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("no baseline", found.detail)

    def test_a_comparison_naming_both_sides_passes(self):
        body = predicate()
        body["deltas"] = {
            "baseline": {"name": "goldfinch-v0", "digest": ELSEWHERE},
            "current": {"name": "goldfinch-v1", "digest": PROOFS},
            "components": {"added": ["traces.jsonl"], "removed": [], "changed": []},
        }
        found = gate(5, body)
        self.assertTrue(found.passed, found.detail)
        self.assertIn("goldfinch-v1 against goldfinch-v0", found.detail)

    def test_an_unnamed_current_side_on_a_null_baseline_fails(self):
        """The branch step 1 of this run closed on the Solidity predicate. This
        type was written over the fixed shape, and the test is here so it stays
        fixed for both."""
        body = predicate()
        body["deltas"]["current"] = {"name": "", "digest": PROOFS}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("current side has no name", found.detail)

    def test_a_side_named_only_whitespace_fails(self):
        """`"   "` is truthy, so a bare presence test let a side identify nothing.
        Found in round 3 of the fixture step: the schema and the verifier agreed
        with each other and both were wrong."""
        for value in (" ", "   ", "\t", "\n"):
            body = predicate()
            body["deltas"]["current"] = {
                "name": value,
                "digest": body["fixture_subjects"][0]["digest"],
            }
            with self.subTest(name=value):
                found = gate(5, body)
                self.assertFalse(found.passed)
                self.assertIn("has no name", found.detail)

    def test_a_current_side_outside_the_statement_fails(self):
        body = predicate()
        body["deltas"]["current"] = {"name": "goldfinch-v1", "digest": ELSEWHERE}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_component_changes_against_a_null_baseline_fail(self):
        body = predicate()
        body["deltas"]["components"] = {"added": ["traces.jsonl"]}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("against a null baseline", found.detail)

    def test_a_changed_entry_naming_one_side_fails(self):
        body = predicate()
        body["deltas"] = {
            "baseline": {"name": "goldfinch-v0", "digest": ELSEWHERE},
            "current": {"name": "goldfinch-v1", "digest": PROOFS},
            "components": {"changed": [{"baseline": "rpc.jsonl"}]},
        }
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("names no current", found.detail)

    def test_an_unknown_delta_section_fails(self):
        body = predicate()
        body["deltas"]["storage"] = {"added": []}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("storage", found.detail)


class ShapeTests(unittest.TestCase):
    def test_a_field_outside_the_shape_fails(self):
        body = predicate()
        body["archive_endpoint"] = "https://example.invalid/rpc"
        found = named("predicate-fields", body)
        self.assertFalse(found.passed)
        self.assertIn("archive_endpoint", found.detail)

    def test_check_returns_a_gate_for_each_thing_it_looks_at(self):
        found = fixture.check(built(predicate()))
        self.assertEqual(
            [(g.number, g.name) for g in found],
            [
                (2, "environment"),
                (5, "deltas"),
                (None, "predicate-fields"),
                (None, "evidence"),
                (None, "replay"),
            ],
        )


class SchemaAgreementTests(unittest.TestCase):
    """The schema and the verifier reach the same verdict on the same document.

    A schema that accepts what the verifier refuses sends a producer straight into
    a refusal, and one that refuses what the verifier accepts refuses honest work.
    Two disagreements were found by hand in round 2 of this step: the conditional
    state-root rule, which the schema had a comment saying it could not express and
    draft 2020-12 can, and a component path leaving the fixture, which had no
    pattern at all.

    `jsonschema` is not a dependency of this plugin, so the test skips when it is
    absent rather than adding one.
    """

    CASES = {
        "the passing shape": lambda p: None,
        "a count at the ceiling": lambda p: p["evidence"].update(
            recorded_rpc=fixture.MAX_COUNT
        ),
        "a count over the ceiling": lambda p: p["evidence"].update(
            recorded_rpc=fixture.MAX_COUNT + 1
        ),
        "bytes over the ceiling": lambda p: p["fixture_subjects"][1].update(
            bytes=fixture.MAX_BYTES + 1
        ),
        "no state root and no proofs": lambda p: (
            p["chain"].pop("state_root"),
            p["evidence"].update(proof_backed=0),
        ),
        "no state root with proofs claimed": lambda p: p["chain"].pop("state_root"),
        "an all-zero state root": lambda p: p["chain"].update(
            state_root=fixture.ZERO_HASH
        ),
        "replay reaching a network": lambda p: p["replay"].update(
            reaches_network=True
        ),
        "a hex block number": lambda p: p["chain"].update(block_number="0xc7da16"),
        "a boolean count": lambda p: p["evidence"].update(proof_backed=True),
        "an uppercased block hash": lambda p: p["chain"].update(
            block_hash="0x" + "A" * 64
        ),
        "an undefined chain field": lambda p: p["chain"].update(difficulty="0x0"),
        "an undefined evidence class": lambda p: p["evidence"].update(
            trusted_oracle=1
        ),
        "a path leaving the fixture": lambda p: p["fixture_subjects"][1].update(
            path="../outside.jsonl"
        ),
        "an absolute path": lambda p: p["fixture_subjects"][1].update(
            path="/etc/passwd"
        ),
    }

    def schema(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "schemas",
            "state-fixture-v1.json",
        )
        with open(path, "rb") as handle:
            return json.loads(handle.read().decode("utf-8"))

    def test_the_schema_carries_the_two_rules_it_used_to_leave_out(self):
        """Always-on evidence, because the test below needs `jsonschema` and this
        plugin does not depend on it. Structural rather than behavioural: it checks
        that the rules are in the document, not that a validator applies them the
        way the verifier does."""
        schema = self.schema()
        conditional = schema["allOf"][0]
        claimed = conditional["if"]["properties"]["evidence"]["properties"]
        self.assertEqual(claimed["proof_backed"]["minimum"], 1)
        self.assertIn(
            "state_root", conditional["then"]["properties"]["chain"]["required"]
        )
        self.assertNotIn(
            "state_root", schema["properties"]["chain"]["required"]
        )
        path_shape = schema["properties"]["fixture_subjects"]["items"][
            "properties"
        ]["path"]
        self.assertIn("pattern", path_shape)
        chain = schema["properties"]["chain"]["properties"]
        for field in ("block_hash", "state_root"):
            with self.subTest(field=field):
                self.assertEqual(chain[field].get("minLength"), 66)
                self.assertEqual(chain[field].get("maxLength"), 66)

    INEXPRESSIBLE = {
        # A schema describes the predicate body. Whether a component digest also
        # appears in the statement's `subject` array is a fact about the document
        # around the predicate, and no keyword reaches it.
        "fail-gate2-state-fixture-component-not-a-subject.json",
    }

    def test_the_schema_and_the_verifier_agree(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        schema = self.schema()
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema)
        for label, mutate in self.CASES.items():
            body = predicate()
            mutate(body)
            with self.subTest(case=label):
                verifier_ok = all(g.passed for g in fixture.check(built(body)))
                schema_ok = not list(validator.iter_errors(body))
                self.assertEqual(
                    verifier_ok,
                    schema_ok,
                    "%s: verifier %s, schema %s"
                    % (label, verifier_ok, schema_ok),
                )

    def test_they_agree_on_the_shipped_fixtures_too(self):
        """The case list above is hand written, so it only covers what somebody
        thought of. The fixtures are the artefact another implementation reads, and
        running the pair over those found a disagreement the list had missed: the
        schema accepted an empty delta side name that every verifier here refuses.
        """
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        from ariadne_lib import envelope, registry, verify

        validator = jsonschema.Draft202012Validator(self.schema())
        directory = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures", "conformance"
        )
        found = 0
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(directory, name), "rb") as handle:
                document = envelope.read(handle.read())
            if document.statement.predicate_type != fixture.TYPE:
                continue
            found += 1
            verifier_ok = verify.report(document, registry.DEFAULT).ok
            errors = list(validator.iter_errors(document.statement.predicate))
            expected = verifier_ok or name in self.INEXPRESSIBLE
            with self.subTest(fixture=name):
                self.assertEqual(
                    not errors,
                    expected,
                    "%s: verifier %s, schema %s, %s"
                    % (name, verifier_ok, not errors,
                       [e.message for e in errors[:2]]),
                )
        self.assertTrue(found)


class ShippedFixtureTests(unittest.TestCase):
    """The two passing fixtures cover both branches, and go on covering them.

    The completeness tests in `test_conformance.py` check that every gate and
    check has a breaching fixture. Nothing there checks that a passing fixture
    still exercises the branch it was written for, so adding a state root to the
    proved-nothing fixture would leave the suite green while the fixture stopped
    testing anything. That is the shape this step keeps meeting: something that
    reads as cover and holds nothing.
    """

    FIXTURES = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "fixtures", "conformance"
    )

    def read(self, name):
        with open(os.path.join(self.FIXTURES, name), "rb") as handle:
            return json.loads(handle.read().decode("utf-8"))["predicate"]

    def test_one_passing_fixture_proves_something_and_carries_a_root(self):
        body = self.read("pass-state-fixture.json")
        self.assertGreater(body["evidence"][fixture.PROVED], 0)
        self.assertTrue(fixture.hash32(body["chain"]["state_root"]))

    def test_the_other_proves_nothing_and_carries_no_root(self):
        body = self.read("pass-state-fixture-proved-nothing.json")
        self.assertEqual(body["evidence"][fixture.PROVED], 0)
        self.assertNotIn("state_root", body["chain"])

    def test_the_proved_nothing_fixture_records_the_absence_rather_than_omitting_it(
        self,
    ):
        """A zero count and a skipped claim. A capture that proved nothing has
        said so; one that left the evidence block out has not."""
        body = self.read("pass-state-fixture-proved-nothing.json")
        self.assertEqual(sorted(body["evidence"]), sorted(fixture.EVIDENCE_CLASSES))
        skipped = [c for c in body["claims"] if c["disposition"] == "skipped"]
        self.assertTrue(skipped, "the absence of proofs is not recorded as a claim")
        self.assertTrue(all(c.get("reason", "").strip() for c in skipped))

    def test_the_proved_nothing_fixture_lists_no_proofs_component(self):
        """It would otherwise describe a file the capture does not hold."""
        body = self.read("pass-state-fixture-proved-nothing.json")
        paths = [entry["path"] for entry in body["fixture_subjects"]]
        self.assertNotIn("proofs.jsonl", paths)


class LazarusAgreementTests(unittest.TestCase):
    """The class names are copied from Lazarus. This is what checks the copy.

    Ariadne imports nothing from another plugin at run time, so the names are a
    tuple in this module rather than a shared constant. A rename in Lazarus would
    otherwise go unnoticed here until somebody compared two documents by hand.
    """

    def test_the_class_names_are_the_ones_lazarus_publishes(self):
        if not os.path.isfile(LAZARUS_MANIFEST_SCHEMA):
            self.skipTest("Lazarus is not beside this plugin in this checkout")
        with open(LAZARUS_MANIFEST_SCHEMA, "rb") as handle:
            schema = json.loads(handle.read().decode("utf-8"))
        counts = schema["properties"]["evidence_counts"]
        self.assertEqual(
            sorted(counts["required"]), sorted(fixture.EVIDENCE_CLASSES)
        )
        self.assertEqual(
            sorted(counts["properties"]), sorted(fixture.EVIDENCE_CLASSES)
        )

    def test_the_proved_class_is_one_of_them(self):
        self.assertIn(fixture.PROVED, fixture.EVIDENCE_CLASSES)

    def test_the_ceilings_match_the_ones_lazarus_sets(self):
        if not os.path.isfile(LAZARUS_MANIFEST_SCHEMA):
            self.skipTest("Lazarus is not beside this plugin in this checkout")
        with open(LAZARUS_MANIFEST_SCHEMA, "rb") as handle:
            schema = json.loads(handle.read().decode("utf-8"))
        component = schema["properties"]["components"]["items"]["properties"]
        self.assertEqual(component["bytes"]["maximum"], fixture.MAX_BYTES)
        counts = schema["properties"]["evidence_counts"]["properties"]
        for name in fixture.EVIDENCE_CLASSES:
            with self.subTest(evidence_class=name):
                self.assertEqual(counts[name]["maximum"], fixture.MAX_COUNT)


class VersionTwoTests(unittest.TestCase):
    def assertSafePass(self, found, name):
        self.assertTrue(found.passed)
        self.assertEqual(
            found.detail,
            "state-fixture/v2 %s check passed" % name,
        )

    def assertSafeFailure(self, found, name):
        self.assertFalse(found.passed)
        self.assertEqual(
            found.detail,
            "state-fixture/v2 %s check failed" % name,
        )

    def test_the_complete_v2_predicate_passes_its_checks(self):
        failed = [
            gate
            for gate in fixture.V2.check(built_v2(predicate_v2()))
            if not gate.passed
        ]
        self.assertEqual(failed, [], [gate.line() for gate in failed])

    def test_v2_hashes_with_a_terminal_line_feed_fail(self):
        for field, value in (
            ("block_hash", BLOCK_HASH),
            ("state_root", STATE_ROOT),
            ("receipts_root", RECEIPTS_ROOT),
        ):
            body = predicate_v2()
            body["chain"][field] = value + "\n"
            found = gate_v2(2, body)
            with self.subTest(field=field):
                self.assertSafeFailure(found, "environment")

    def test_v2_schema_carries_an_exact_hash_width(self):
        path = os.path.join(
            support.PLUGIN_ROOT, "schemas", "state-fixture-v2.json"
        )
        with open(path, "rb") as handle:
            schema = json.loads(handle.read().decode("utf-8"))
        shape = schema["$defs"]["hash32"]
        self.assertEqual(shape.get("minLength"), 66)
        self.assertEqual(shape.get("maxLength"), 66)

    def test_v2_requires_both_delta_endpoints_even_on_a_first_capture(self):
        for side in ("baseline", "current"):
            body = predicate_v2()
            del body["deltas"][side]
            found = gate_v2(5, body)
            with self.subTest(side=side):
                self.assertSafeFailure(found, "deltas")

    def test_v2_refuses_even_an_empty_delta_section_against_a_null_baseline(self):
        body = predicate_v2()
        body["deltas"]["components"] = {}
        found = gate_v2(5, body)
        self.assertSafeFailure(found, "deltas")

    def test_v2_component_paths_match_the_published_portable_shape(self):
        for path in (
            "a\\b",
            ".",
            "./header.json",
            "a/./header.json",
            "a/ ",
            "header.json/",
            "C:header.json",
            "1:header.json",
            "\u96ea:header.json",
            "header\x00.json",
            "x" * 1025,
        ):
            body = predicate_v2()
            body["fixture_subjects"][0]["path"] = path
            found = gate_v2(2, body)
            with self.subTest(path=path[:40]):
                self.assertSafeFailure(found, "environment")

    def test_v2_identifiers_and_path_segments_need_a_portable_graphic(self):
        self.assertTrue(
            hasattr(fixture, "portable_name_v2"),
            "state-fixture/v2 exposes its published portable-name predicate",
        )
        if not hasattr(fixture, "portable_name_v2"):
            return
        invisible = ("\u200b", "\x00", "\ue000", "\u2060")
        for value in invisible:
            cases = []

            capture_tool = predicate_v2()
            capture_tool["capture"]["tool"] = value
            cases.append(("capture tool", 2, capture_tool, "environment"))

            command = predicate_v2()
            command["capture"]["command"][0] = value
            cases.append(("capture command", 2, command, "environment"))

            component_name = predicate_v2()
            component_name["fixture_subjects"][0]["name"] = value
            cases.append(("component name", 2, component_name, "environment"))

            component_path = predicate_v2()
            component_path["fixture_subjects"][0]["path"] = "a/" + value
            cases.append(("component path", 2, component_path, "environment"))

            current_name = predicate_v2()
            current_name["deltas"]["current"]["name"] = value
            cases.append(("current name", 5, current_name, "deltas"))

            claim_name = predicate_v2()
            claim_name["claims"] = [
                {
                    "name": value,
                    "subject": HEADER,
                    "disposition": "passed",
                }
            ]
            cases.append(
                ("claim name", None, claim_name, "predicate-fields")
            )

            for field, number, body, check in cases:
                with self.subTest(value=repr(value), field=field):
                    found = (
                        gate_v2(number, body)
                        if number is not None
                        else named_v2(check, body)
                    )
                    self.assertSafeFailure(found, check)

        for value in ("fixture", "\u96ea.json", "\u96ea fixture"):
            with self.subTest(visible=value):
                self.assertTrue(fixture.portable_name_v2(value))

    def test_v2_failed_predicate_checks_do_not_echo_hostile_values(self):
        marker = "PRIVATE_PROVIDER_VALUE_" + "x" * 200000
        cases = []

        environment = predicate_v2()
        environment["chain"][marker] = 1
        cases.append((2, "environment", environment))

        deltas = predicate_v2()
        deltas["deltas"]["current"][marker] = "unchecked"
        cases.append((5, "deltas", deltas))

        fields = predicate_v2(**{marker: "unchecked"})
        cases.append((None, "predicate-fields", fields))

        evidence = predicate_v2()
        evidence["evidence"][marker] = 1
        cases.append((None, "evidence", evidence))

        replay = predicate_v2()
        replay["replay"][marker] = False
        cases.append((None, "replay", replay))

        for number, name, body in cases:
            with self.subTest(check=name):
                found = (
                    gate_v2(number, body)
                    if number is not None
                    else named_v2(name, body)
                )
                self.assertSafeFailure(found, name)
                self.assertNotIn(marker, found.line())
                self.assertLessEqual(len(found.line()), 128)

    def test_v2_passing_predicate_checks_do_not_echo_hostile_values(self):
        marker = "PRIVATE_PROVIDER_VALUE_" + "x" * 200000
        body = predicate_v2()
        body["capture"]["tool"] = marker
        found = gate_v2(2, body)
        self.assertSafePass(found, "environment")
        self.assertNotIn(marker, found.line())
        self.assertLessEqual(len(found.line()), 128)

    def test_v2_subject_names_match_release_normalisation(self):
        for location in ("fixture", "statement"):
            body = predicate_v2()
            subjects = None
            if location == "fixture":
                body["fixture_subjects"][0]["name"] = "pl\u00e1n.json"
                body["fixture_subjects"][1]["name"] = "pla\u0301n.json"
            else:
                subjects = [
                    {"name": "pl\u00e1n.json", "digest": HEADER},
                    {"name": "pla\u0301n.json", "digest": PROOFS},
                ]
            with self.subTest(location=location):
                self.assertSafeFailure(
                    named_v2("subject-names", body, subjects), "subject-names"
                )

        body = predicate_v2()
        subjects = [
            {"name": "header.json", "digest": HEADER},
            {"name": "proofs.jsonl", "digest": PROOFS},
            {"name": "header.json", "digest": ELSEWHERE},
        ]
        self.assertSafeFailure(
            named_v2("subject-names", body, subjects), "subject-names"
        )

    def test_v2_refuses_more_components_than_its_schema_publishes(self):
        maximum = 1024
        body = predicate_v2()
        body["fixture_subjects"] = [
            copy.deepcopy(body["fixture_subjects"][0])
            for _ in range(maximum + 1)
        ]
        found = gate_v2(2, body)
        self.assertSafeFailure(found, "environment")

    def test_v2_closes_the_nested_shapes_its_schema_closes(self):
        cases = []

        capture_extra = predicate_v2()
        capture_extra["capture"]["extra_note"] = "unchecked"
        cases.append((2, capture_extra, "extra_note"))

        subject_extra = predicate_v2()
        subject_extra["fixture_subjects"][0]["extra_note"] = "unchecked"
        cases.append((2, subject_extra, "extra_note"))

        delta_extra = predicate_v2()
        delta_extra["deltas"]["current"]["extra_note"] = "unchecked"
        cases.append((5, delta_extra, "extra_note"))

        changed_extra = predicate_v2()
        changed_extra["deltas"] = {
            "baseline": {"name": "old", "digest": HEADER},
            "current": {"name": "fixture-v2", "digest": HEADER},
            "components": {
                "changed": [
                    {
                        "baseline": "old-header.json",
                        "current": "header.json",
                        "extra_note": "unchecked",
                    }
                ]
            },
        }
        cases.append((5, changed_extra, "extra_note"))

        reason_type = predicate_v2()
        reason_type["deltas"]["reason"] = 17
        cases.append((5, reason_type, "reason must be a string"))

        for number, body, detail in cases:
            with self.subTest(gate=number, detail=detail):
                found = gate_v2(number, body)
                self.assertSafeFailure(
                    found, "environment" if number == 2 else "deltas"
                )

    def test_v2_claim_shape_matches_the_published_schema(self):
        for edit, detail in (
            (lambda claim: claim.pop("name"), "name"),
            (lambda claim: claim.update(detail="not an object"), "detail"),
            (lambda claim: claim.update(reason=17), "reason"),
        ):
            body = predicate_v2()
            body["claims"] = [
                {
                    "name": "component checked",
                    "subject": HEADER,
                    "disposition": "passed",
                }
            ]
            edit(body["claims"][0])
            found = named_v2("predicate-fields", body)
            with self.subTest(detail=detail):
                self.assertSafeFailure(found, "predicate-fields")

    def test_state_and_receipt_authority_are_independent(self):
        state_only = predicate_v2()
        state_only["evidence"]["receipt_trie_proved"] = 0
        del state_only["chain"]["receipts_root"]
        self.assertTrue(named_v2("evidence", state_only).passed)

        receipts_only = predicate_v2()
        receipts_only["evidence"]["proof_backed"] = 0
        del receipts_only["chain"]["state_root"]
        self.assertTrue(named_v2("evidence", receipts_only).passed)

    def test_each_positive_count_needs_its_own_root(self):
        for evidence_class, root in (
            ("proof_backed", "state_root"),
            ("receipt_trie_proved", "receipts_root"),
        ):
            body = predicate_v2()
            del body["chain"][root]
            found = named_v2("evidence", body)
            with self.subTest(evidence=evidence_class, root=root):
                self.assertSafeFailure(found, "evidence")

    def test_zero_counts_need_neither_root(self):
        body = predicate_v2()
        body["evidence"]["proof_backed"] = 0
        body["evidence"]["receipt_trie_proved"] = 0
        del body["chain"]["state_root"]
        del body["chain"]["receipts_root"]
        self.assertTrue(gate_v2(2, body).passed)
        self.assertTrue(named_v2("evidence", body).passed)

    def test_boolean_or_missing_receipt_counts_are_refused(self):
        for value in (None, True):
            body = predicate_v2()
            if value is None:
                del body["evidence"]["receipt_trie_proved"]
            else:
                body["evidence"]["receipt_trie_proved"] = value
            with self.subTest(value=value):
                self.assertFalse(named_v2("evidence", body).passed)

    def test_malformed_or_zero_roots_are_refused_when_present(self):
        for root in ("state_root", "receipts_root"):
            for value in ("0x1234", "0x" + "0" * 64):
                body = predicate_v2()
                body["chain"][root] = value
                with self.subTest(root=root, value=value):
                    self.assertFalse(gate_v2(2, body).passed)

    def test_v2_records_no_network_chain_or_provider_claim(self):
        for field in fixture.V2.REPLAY_REQUIRED:
            body = predicate_v2()
            body["replay"][field] = True
            with self.subTest(field=field):
                self.assertFalse(named_v2("replay", body).passed)

    def test_v2_replay_carries_no_executable_command(self):
        body = predicate_v2()
        body["commands"] = [
            {
                "name": "network",
                "argv": ["curl", "https://example.invalid"],
                "determinism": "exact",
            }
        ]
        found = named_v2("replay", body)
        self.assertSafeFailure(found, "replay")

    def test_transaction_hashes_are_outside_the_v2_predicate_shape(self):
        body = predicate_v2(transaction_hash="0x" + "99" * 32)
        found = named_v2("predicate-fields", body)
        self.assertSafeFailure(found, "predicate-fields")


if __name__ == "__main__":
    unittest.main()
