"""Gates 2 and 5, and the two checks that come with them."""

import hashlib
import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import statement  # noqa: E402
from ariadne_lib.predicates import solidity_release as release  # noqa: E402

CREATION = {"sha256": hashlib.sha256(b"creation").hexdigest()}
RUNTIME = {"sha256": hashlib.sha256(b"runtime").hexdigest()}
PREVIOUS = {"sha256": hashlib.sha256(b"previous runtime").hexdigest()}
TREE = {"sha256": hashlib.sha256(b"tree").hexdigest()}
LOCK = {"sha256": hashlib.sha256(b"lock").hexdigest()}
REPORT = {"sha256": hashlib.sha256(b"report").hexdigest()}
COMMIT = "9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a"


def predicate(**overrides):
    out = {
        "source": {
            "repository": "https://github.com/wildcat-finance/example",
            "commit": COMMIT,
            "tree_digest": TREE,
        },
        "build": {
            "compiler": "solc",
            "compiler_version": "0.8.28",
            "optimizer": {"enabled": True, "runs": 200},
            "evm_version": "cancun",
            "dependency_lock_digest": LOCK,
            "command": ["forge", "build"],
        },
        "release_subjects": [
            {
                "name": "Escrow",
                "source_path": "src/Escrow.sol",
                "creation_digest": CREATION,
                "runtime_digest": RUNTIME,
            }
        ],
        "deltas": {
            "baseline": {"name": "v1.0.0", "digest": PREVIOUS},
            "current": {"name": "v1.1.0", "digest": RUNTIME},
            "abi": {"added": ["sweep(address)"], "removed": [], "changed": []},
        },
        "claims": [],
        "commands": [],
    }
    out.update(overrides)
    return out


def built(predicate_body, subject=None):
    return statement.Statement.from_dict(
        {
            "_type": statement.STATEMENT_TYPE,
            "subject": subject
            or [
                {"name": "Escrow (creation)", "digest": CREATION},
                {"name": "Escrow (runtime)", "digest": RUNTIME},
            ],
            "predicateType": release.TYPE,
            "predicate": predicate_body,
        }
    )


def gate(number, predicate_body, subject=None):
    for found in release.check(built(predicate_body, subject)):
        if found.number == number:
            return found
    raise AssertionError("no gate %r" % number)


def named(name, predicate_body, subject=None):
    for found in release.check(built(predicate_body, subject)):
        if found.name == name:
            return found
    raise AssertionError("no check named %r" % name)


class GateTwoTests(unittest.TestCase):
    def test_a_complete_build_record_passes(self):
        found = gate(2, predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("solc 0.8.28", found.detail)

    def test_a_compiler_version_alone_is_not_a_build_description(self):
        body = predicate()
        body["build"] = {"compiler": "solc", "compiler_version": "0.8.28"}
        found = gate(2, body)
        self.assertFalse(found.passed)
        for field in ("optimizer", "evm_version", "dependency_lock_digest", "command"):
            self.assertIn(field, found.detail)

    def test_an_optimizer_without_its_runs_fails(self):
        body = predicate()
        body["build"]["optimizer"] = {"enabled": True}
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("runs", found.detail)

    def test_an_optimizer_turned_off_is_a_setting_not_an_absence(self):
        body = predicate()
        body["build"]["optimizer"] = {"enabled": False, "runs": 0}
        found = gate(2, body)
        self.assertTrue(found.passed, found.detail)
        self.assertIn("optimiser off", found.detail)

    def test_a_source_without_a_commit_fails(self):
        body = predicate()
        del body["source"]["commit"]
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("commit", found.detail)

    def test_a_branch_name_where_a_commit_belongs_fails(self):
        """A branch points at whatever it pointed at that day."""
        body = predicate()
        body["source"]["commit"] = "main"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("something that moves", found.detail)

    def test_a_source_commit_with_a_terminal_line_feed_fails(self):
        body = predicate()
        body["source"]["commit"] += "\n"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("git object id", found.detail)

    def test_a_source_without_a_tree_digest_fails(self):
        body = predicate()
        del body["source"]["tree_digest"]
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("tree_digest", found.detail)

    def test_a_compiler_version_that_is_not_a_string_fails(self):
        body = predicate()
        body["build"]["compiler_version"] = 8
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("compiler_version must be a string", found.detail)

    def test_a_build_command_that_is_a_string_fails(self):
        body = predicate()
        body["build"]["command"] = "forge build"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("argv of strings", found.detail)

    def test_a_recorded_exact_command_must_match_the_build_command(self):
        body = predicate()
        body["commands"] = [
            {
                "name": "not the declared build",
                "argv": ["true"],
                "determinism": "exact",
                "output_digest": RUNTIME,
            }
        ]
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("do not match", found.detail)

    def test_a_release_subject_not_covered_by_the_statement_fails(self):
        body = predicate()
        found = gate(2, body, subject=[{"name": "Escrow", "digest": CREATION}])
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_no_release_subjects_fails(self):
        body = predicate()
        body["release_subjects"] = []
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("non-empty", found.detail)


class GateFiveTests(unittest.TestCase):
    def test_a_delta_naming_both_sides_passes(self):
        found = gate(5, predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("v1.1.0 against v1.0.0", found.detail)

    def test_a_baseline_without_a_digest_fails(self):
        body = predicate()
        body["deltas"]["baseline"] = {"name": "v1.0.0"}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("baseline", found.detail)

    def test_a_side_named_only_whitespace_fails(self):
        """`"   "` is truthy. `check_side` is shared by all three predicates and
        used a bare presence test, so a side could identify nothing and pass the
        check that exists to make both ends identifiable."""
        for side in ("baseline", "current"):
            for value in (" ", "   ", "\t"):
                body = predicate()
                body["deltas"][side] = dict(body["deltas"][side], name=value)
                with self.subTest(side=side, name=value):
                    found = gate(5, body)
                    self.assertFalse(found.passed)
                    self.assertIn("has no name", found.detail)

    def test_a_baseline_without_a_name_fails(self):
        body = predicate()
        body["deltas"]["baseline"] = {"digest": PREVIOUS}
        found = gate(5, body)
        self.assertFalse(found.passed)

    def test_a_missing_current_side_fails(self):
        body = predicate()
        del body["deltas"]["current"]
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("current", found.detail)

    def test_a_null_baseline_with_a_reason_passes_and_keeps_the_reason(self):
        body = predicate()
        body["deltas"] = {"baseline": None, "reason": "first tagged release"}
        found = gate(5, body)
        self.assertTrue(found.passed, found.detail)
        self.assertIn("first tagged release", found.detail)

    def test_a_null_baseline_without_a_reason_fails(self):
        body = predicate()
        body["deltas"] = {"baseline": None}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("needs a reason", found.detail)

    def test_delta_content_against_a_null_baseline_fails(self):
        body = predicate()
        body["deltas"] = {
            "baseline": None,
            "reason": "first release",
            "abi": {"added": ["sweep(address)"]},
        }
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("against a null baseline", found.detail)

    def test_a_null_current_side_against_a_baseline_fails(self):
        body = predicate()
        body["deltas"]["current"] = None
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("current side is not an object", found.detail)

    def test_a_current_side_outside_the_statement_fails(self):
        """The current side is meant to be this release, not some other pair."""
        body = predicate()
        body["deltas"]["current"] = {"name": "v1.1.0", "digest": PREVIOUS}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_empty_delta_sections_beside_a_null_baseline_are_not_content(self):
        body = predicate()
        body["deltas"] = {
            "baseline": None,
            "reason": "first tagged release",
            "abi": {"added": [], "removed": [], "changed": []},
        }
        found = gate(5, body)
        self.assertTrue(found.passed, found.detail)

    def test_a_delta_section_that_is_not_an_object_fails(self):
        body = predicate()
        body["deltas"]["abi"] = "everything changed"
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("must be an object", found.detail)

    def test_a_changed_entry_that_names_one_side_fails(self):
        body = predicate()
        body["deltas"]["abi"] = {
            "added": [],
            "removed": [],
            "changed": [{"signature": "sweep(address)", "current": {"type": "function"}}],
        }
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("names no baseline", found.detail)

    def test_a_changed_entry_naming_both_sides_passes(self):
        body = predicate()
        body["deltas"]["abi"] = {
            "added": [],
            "removed": [],
            "changed": [
                {
                    "signature": "sweep(address)",
                    "baseline": {"stateMutability": "nonpayable"},
                    "current": {"stateMutability": "payable"},
                }
            ],
        }
        found = gate(5, body)
        self.assertTrue(found.passed, found.detail)

    def test_a_delta_list_that_is_not_a_list_fails(self):
        body = predicate()
        body["deltas"]["abi"] = {"added": "sweep(address)"}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("must be an array", found.detail)

    def test_a_missing_deltas_block_fails(self):
        body = predicate()
        del body["deltas"]
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("no deltas block", found.detail)

    def test_an_unknown_delta_section_fails(self):
        body = predicate()
        body["deltas"]["gas"] = {"cheaper": 12}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("gas", found.detail)


class NullBaselineCurrentSideTests(unittest.TestCase):
    """The current side of a first release, which gate 5 used to skip entirely.

    The null-baseline branch returned before anything looked at the current
    side, so a first release could name no version, carry no digest, or point at
    bytes the statement does not cover, and gate 5 would report a pass. A first
    release that leaves the side out is the shipped convention and still passes;
    a side that is there is now checked like any other.
    """

    def first_release(self, current=None):
        body = predicate()
        body["deltas"] = {
            "baseline": None,
            "reason": "first tagged release; nothing to compare against",
        }
        if current is not None:
            body["deltas"]["current"] = current
        return body

    def test_a_first_release_with_no_current_side_passes(self):
        found = gate(5, self.first_release())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("no baseline", found.detail)

    def test_a_first_release_naming_a_covered_current_side_passes(self):
        found = gate(
            5, self.first_release({"name": "v1.0.0", "digest": RUNTIME})
        )
        self.assertTrue(found.passed, found.detail)
        self.assertIn("v1.0.0, no baseline", found.detail)

    def test_a_current_side_without_a_name_fails(self):
        found = gate(5, self.first_release({"digest": RUNTIME}))
        self.assertFalse(found.passed)
        self.assertIn("current side has no name", found.detail)

    def test_an_empty_name_on_a_current_side_fails(self):
        found = gate(5, self.first_release({"name": "", "digest": RUNTIME}))
        self.assertFalse(found.passed)
        self.assertIn("current side has no name", found.detail)

    def test_a_current_side_without_a_digest_fails(self):
        found = gate(5, self.first_release({"name": "v1.0.0"}))
        self.assertFalse(found.passed)
        self.assertIn("current side", found.detail)

    def test_a_current_side_whose_digest_is_malformed_fails(self):
        found = gate(
            5, self.first_release({"name": "v1.0.0", "digest": {"sha256": "beef"}})
        )
        self.assertFalse(found.passed)
        self.assertIn("current side", found.detail)

    def test_a_current_side_outside_the_statement_fails(self):
        found = gate(
            5, self.first_release({"name": "v1.0.0", "digest": PREVIOUS})
        )
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_a_current_side_that_is_not_an_object_fails(self):
        found = gate(5, self.first_release("v1.0.0"))
        self.assertFalse(found.passed)
        self.assertIn("current side is not an object", found.detail)

    def test_a_null_current_side_fails(self):
        """`"current": null` is a side that is there, not a side left out.

        A producer emitting the key with nothing in it has said a current side
        exists and then identified nothing, which is the shape the absent case
        is not. Membership rather than a truthiness test is what separates them,
        and a mutation probe found no test holding that line.
        """
        body = predicate()
        body["deltas"] = {
            "baseline": None,
            "reason": "first tagged release; nothing to compare against",
            "current": None,
        }
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("current side is not an object", found.detail)


class AuditTests(unittest.TestCase):
    def test_an_audit_naming_its_revision_passes(self):
        body = predicate(
            audits=[
                {
                    "report_digest": REPORT,
                    "covered_revision": COMMIT,
                    "scope": "src/Escrow.sol",
                }
            ]
        )
        found = named("audits", body)
        self.assertTrue(found.passed, found.detail)

    def test_an_audit_without_a_covered_revision_fails(self):
        body = predicate(
            audits=[{"report_digest": REPORT, "scope": "src/Escrow.sol"}]
        )
        found = named("audits", body)
        self.assertFalse(found.passed)
        self.assertIn("covered_revision", found.detail)

    def test_an_audit_covering_a_branch_fails(self):
        body = predicate(
            audits=[
                {
                    "report_digest": REPORT,
                    "covered_revision": "release/v1",
                    "scope": "src/Escrow.sol",
                }
            ]
        )
        found = named("audits", body)
        self.assertFalse(found.passed)
        self.assertIn("covered whatever it pointed at", found.detail)

    def test_an_audit_revision_with_a_terminal_line_feed_fails(self):
        body = predicate(
            audits=[
                {
                    "report_digest": REPORT,
                    "covered_revision": COMMIT + "\n",
                    "scope": "src/Escrow.sol",
                }
            ]
        )
        found = named("audits", body)
        self.assertFalse(found.passed)
        self.assertIn("git object id", found.detail)

    def test_no_audits_is_reported_rather_than_assumed(self):
        found = named("audits", predicate())
        self.assertTrue(found.passed)
        self.assertIn("no audits recorded", found.detail)


class DeploymentTests(unittest.TestCase):
    def test_an_unconfirmed_deployment_is_counted_and_named(self):
        body = predicate(
            deployments=[
                {
                    "chain_id": 1,
                    "address": "0x" + "e5" * 20,
                    "creation_tx": "0x" + "ab" * 32,
                    "confirmed_against_chain": False,
                }
            ]
        )
        found = named("deployments", body)
        self.assertTrue(found.passed, found.detail)
        self.assertIn("1 unconfirmed", found.detail)

    def test_a_confirmation_that_is_not_a_boolean_fails(self):
        """The field records a decision, so only the two booleans are in its
        vocabulary. Anything else was read for truthiness, and `"null"` and `" "`
        are truthy: a deployment carrying either verified clean and the report line
        said `0 unconfirmed against a chain`, which told a reader every deployment
        had been checked against a chain. Nothing here has ever spoken to a node.
        """
        for value in ("null", " ", "", 0, 1, "false", [], {}):
            body = predicate(
                deployments=[
                    {
                        "chain_id": 1,
                        "address": "0x" + "ab" * 20,
                        "creation_tx": "0x" + "cd" * 32,
                        "confirmed_against_chain": value,
                    }
                ]
            )
            with self.subTest(confirmed=value):
                found = named("deployments", body)
                self.assertFalse(found.passed, "%r was accepted" % (value,))

    def test_both_booleans_are_accepted_and_counted(self):
        for value, unconfirmed in ((False, 1), (True, 0)):
            body = predicate(
                deployments=[
                    {
                        "chain_id": 1,
                        "address": "0x" + "ab" * 20,
                        "creation_tx": "0x" + "cd" * 32,
                        "confirmed_against_chain": value,
                    }
                ]
            )
            with self.subTest(confirmed=value):
                found = named("deployments", body)
                self.assertTrue(found.passed, found.detail)
                self.assertIn("%d unconfirmed" % unconfirmed, found.detail)

    def test_a_chain_id_that_is_not_a_number_fails(self):
        """A chain id identifies a chain. `" "` and `"null"` and `true` all
        satisfied the presence test and named none."""
        for value in (" ", "null", True, 0, -1, 1.5, [], "1"):
            body = predicate(
                deployments=[
                    {
                        "chain_id": value,
                        "address": "0x" + "ab" * 20,
                        "creation_tx": "0x" + "cd" * 32,
                        "confirmed_against_chain": False,
                    }
                ]
            )
            with self.subTest(chain_id=value):
                found = named("deployments", body)
                self.assertFalse(found.passed, "%r was accepted" % (value,))

    def test_a_deployment_that_does_not_say_whether_it_was_confirmed_fails(self):
        body = predicate(
            deployments=[
                {
                    "chain_id": 1,
                    "address": "0x" + "e5" * 20,
                    "creation_tx": "0x" + "ab" * 32,
                }
            ]
        )
        found = named("deployments", body)
        self.assertFalse(found.passed)
        self.assertIn("confirmed_against_chain", found.detail)


class ShapeTests(unittest.TestCase):
    def test_revision_schema_carries_exact_git_oid_lengths(self):
        path = os.path.join(support.PLUGIN_ROOT, "schemas", "solidity-release-v1.json")
        with open(path, "rb") as handle:
            schema = json.loads(handle.read().decode("utf-8"))
        revisions = (
            schema["properties"]["source"]["properties"]["commit"],
            schema["properties"]["audits"]["items"]["properties"][
                "covered_revision"
            ],
        )
        expected = [
            {"minLength": 40, "maxLength": 40},
            {"minLength": 64, "maxLength": 64},
        ]
        for revision in revisions:
            self.assertEqual(revision.get("anyOf"), expected)

    def test_a_field_outside_the_shape_fails(self):
        body = predicate(summary_of_findings="all clear")
        found = named("predicate-fields", body)
        self.assertFalse(found.passed)
        self.assertIn("summary_of_findings", found.detail)

    def test_a_required_field_left_out_is_left_to_the_gate_that_owns_it(self):
        """Gate 3 already fails on a missing claims block. Failing here too
        would report one fault as two."""
        body = predicate()
        del body["claims"]
        found = named("predicate-fields", body)
        self.assertTrue(found.passed, found.detail)

    def test_check_returns_a_gate_for_each_thing_it_looks_at(self):
        found = release.check(built(predicate()))
        self.assertEqual(
            [(gate.number, gate.name) for gate in found],
            [
                (2, "environment"),
                (5, "deltas"),
                (None, "predicate-fields"),
                (None, "audits"),
                (None, "deployments"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
