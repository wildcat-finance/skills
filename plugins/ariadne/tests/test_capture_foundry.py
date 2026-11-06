"""Capture over the committed Foundry fixture.

No test here runs `forge`. The fixture's build output is committed, which is
what lets the suite check a real compiler's numbers without a Solidity
toolchain on the machine.
"""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

import ariadne  # noqa: E402
from ariadne_lib import envelope, registry, verify  # noqa: E402
from ariadne_lib.capture import foundry  # noqa: E402

FIXTURES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "forge-project"
)
V1 = os.path.join(FIXTURES, "v1")
V2 = os.path.join(FIXTURES, "v2")
REPOSITORY = "https://github.com/wildcat-finance/example-escrow"
COMMIT = "9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a"


def captured(**overrides):
    arguments = {
        "repository": REPOSITORY,
        "commit": COMMIT,
        "previous": V1,
        "previous_name": "v1.0.0",
    }
    arguments.update(overrides)
    project = arguments.pop("project", V2)
    return foundry.capture(project, **arguments)


def report_for(statement):
    document = envelope.read(json.dumps(statement).encode("utf-8"))
    return verify.report(document, registry.DEFAULT)


def run(argv):
    """Run the CLI as a shell would see it.

    argparse raises SystemExit for a bad argument rather than returning, and a
    caller in a terminal sees that as an exit code like any other, so the
    helper reports it the same way.
    """
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = ariadne.main(argv)
        except SystemExit as exit:
            code = exit.code
    return code, out.getvalue(), err.getvalue()


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.statement = captured()
        self.predicate = self.statement["predicate"]

    def test_what_capture_writes_passes_every_gate(self):
        report = report_for(self.statement)
        self.assertTrue(
            report.ok, "\n".join(g.line() for g in report.gates if not g.passed)
        )
        self.assertEqual(report.unchecked, [])

    def test_the_build_record_matches_the_fixtures_foundry_toml(self):
        build = self.predicate["build"]
        self.assertEqual(build["compiler"], "solc")
        self.assertTrue(build["compiler_version"].startswith("0.8.28"))
        self.assertEqual(build["optimizer"], {"enabled": True, "runs": 200})
        self.assertEqual(build["evm_version"], "cancun")
        self.assertFalse(build["via_ir"])

    def test_every_release_subject_is_a_subject_of_the_statement(self):
        digests = [entry["digest"] for entry in self.statement["subject"]]
        for entry in self.predicate["release_subjects"]:
            self.assertIn(entry["creation_digest"], digests)
            self.assertIn(entry["runtime_digest"], digests)

    def test_the_added_function_shows_up_in_the_abi_delta(self):
        self.assertIn("sweep(address)", self.predicate["deltas"]["abi"]["added"])

    def test_the_added_function_shows_up_as_a_selector(self):
        self.assertIn(
            "sweep(address)",
            self.predicate["deltas"]["method_identifiers"]["added"],
        )

    def test_the_moved_storage_variable_names_both_slots(self):
        moved = self.predicate["deltas"]["storage"]["moved"]
        balance = [entry for entry in moved if entry["variable"].endswith("balance")]
        self.assertEqual(len(balance), 1)
        self.assertEqual(balance[0]["baseline"]["slot"], "1")
        self.assertEqual(balance[0]["current"]["slot"], "2")

    def test_the_new_storage_variable_shows_up_as_added(self):
        added = self.predicate["deltas"]["storage"]["added"]
        self.assertTrue(any(entry.endswith("deadline") for entry in added))

    def test_the_delta_names_both_sides_as_whole_builds(self):
        """Both sides name the build rather than one contract inside it."""
        deltas = self.predicate["deltas"]
        self.assertEqual(deltas["baseline"]["name"], "v1.0.0")
        self.assertIn("sha256", deltas["baseline"]["digest"])
        bundle = [
            entry["digest"]
            for entry in self.statement["subject"]
            if entry["name"].startswith("release bundle")
        ]
        self.assertEqual(deltas["current"]["digest"], bundle[0])

    def test_the_release_bundle_is_a_subject_of_the_statement(self):
        names = [entry["name"] for entry in self.statement["subject"]]
        self.assertTrue(any(name.startswith("release bundle") for name in names))

    def test_a_contract_present_in_neither_build_is_reported_in_its_own_section(self):
        """An ABI diff cannot show a contract that is gone; there is no ABI."""
        contracts = self.predicate["deltas"]["contracts"]
        self.assertEqual(contracts["added"], [])
        self.assertEqual(contracts["removed"], [])

    def test_a_test_result_nobody_supplied_is_recorded_as_skipped(self):
        claims = {entry["name"]: entry for entry in self.predicate["claims"]}
        for name in ("unit tests", "fuzz campaign"):
            self.assertEqual(claims[name]["disposition"], "skipped")
            self.assertIn("supplied to capture", claims[name]["reason"])

    def test_a_stated_test_result_is_carried_with_its_reason(self):
        statement = captured(tests="failed:two assertions broke in EscrowTest")
        claims = {c["name"]: c for c in statement["predicate"]["claims"]}
        self.assertEqual(claims["unit tests"]["disposition"], "failed")
        self.assertIn("two assertions broke", claims["unit tests"]["reason"])

    def test_a_stated_failure_still_verifies_because_absence_is_the_record(self):
        statement = captured(tests="failed:two assertions broke")
        self.assertTrue(report_for(statement).ok)

    def test_the_build_command_is_recorded_as_exact_with_an_output_digest(self):
        command = self.predicate["commands"][0]
        self.assertEqual(command["determinism"], "exact")
        self.assertIn("sha256", command["output_digest"])

    def test_capture_without_a_previous_build_records_a_null_baseline(self):
        statement = captured(previous=None, previous_name=None)
        deltas = statement["predicate"]["deltas"]
        self.assertIsNone(deltas["baseline"])
        self.assertIn("no previous build", deltas["reason"])
        self.assertTrue(report_for(statement).ok)

    def test_capture_carries_an_audit_and_a_deployment_when_given_them(self):
        statement = captured(
            audits=[
                {
                    "report_digest": {"sha256": "ab" * 32},
                    "covered_revision": COMMIT,
                    "scope": "src/Escrow.sol",
                }
            ],
            deployments=[
                {
                    "chain_id": 1,
                    "address": "0x" + "e5" * 20,
                    "creation_tx": "0x" + "ab" * 32,
                }
            ],
        )
        self.assertFalse(
            statement["predicate"]["deployments"][0]["confirmed_against_chain"]
        )
        self.assertTrue(report_for(statement).ok)

    def test_the_build_says_what_its_lock_digest_is_over(self):
        """A digest whose subject is unnamed tells a reader nothing."""
        self.assertEqual(self.predicate["build"]["dependency_lock_source"], "src/")

    def test_an_invented_disposition_is_refused_at_capture(self):
        """Better than writing a statement this tool's own verifier rejects."""
        with self.assertRaises(foundry.CaptureError) as caught:
            captured(tests="probably fine")
        self.assertIn("is not a disposition", str(caught.exception))

    def test_selecting_a_contract_that_does_not_exist_is_refused(self):
        with self.assertRaises(foundry.CaptureError) as caught:
            captured(contracts=["Vault"])
        self.assertIn("no compiled contract named Vault", str(caught.exception))


class RefusalTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_a_project_with_no_out_directory_is_refused(self):
        with self.assertRaises(foundry.CaptureError) as caught:
            captured(project=self.root)
        self.assertIn("run forge build first", str(caught.exception))

    def test_a_project_with_no_build_info_says_what_to_turn_on(self):
        project = os.path.join(self.root, "project")
        os.makedirs(os.path.join(project, "out", "Escrow.sol"))
        shutil.copy(
            os.path.join(V2, "out", "Escrow.sol", "Escrow.json"),
            os.path.join(project, "out", "Escrow.sol", "Escrow.json"),
        )
        with self.assertRaises(foundry.CaptureError) as caught:
            captured(project=project)
        self.assertIn("build_info = true", str(caught.exception))

    def test_a_missing_project_is_refused(self):
        with self.assertRaises(foundry.CaptureError):
            captured(project=os.path.join(self.root, "absent"))


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_the_subcommand_writes_a_statement_that_verifies(self):
        out = os.path.join(self.root, "release.json")
        code, _, err = run(
            [
                "capture",
                "solidity-release",
                "--project",
                V2,
                "--previous",
                V1,
                "--previous-name",
                "v1.0.0",
                "--repository",
                REPOSITORY,
                "--commit",
                COMMIT,
                "--out",
                out,
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(run(["verify", out])[0], 0)

    def test_a_refusal_exits_two_with_the_reason(self):
        code, _, err = run(
            [
                "capture",
                "solidity-release",
                "--project",
                self.root,
                "--repository",
                REPOSITORY,
                "--commit",
                COMMIT,
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("capture failed", err)

    def test_a_deployment_missing_a_field_is_refused_by_the_parser(self):
        code, _, err = run(
            [
                "capture",
                "solidity-release",
                "--project",
                V2,
                "--repository",
                REPOSITORY,
                "--commit",
                COMMIT,
                "--deployment",
                "chain_id=1",
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("--deployment needs", err)

    def test_a_deployment_naming_a_key_twice_is_refused_by_the_parser(self):
        code, _, err = run(
            [
                "capture",
                "solidity-release",
                "--project",
                V2,
                "--repository",
                REPOSITORY,
                "--commit",
                COMMIT,
                "--deployment",
                "chain_id=1,address=0x01,creation_tx=0x02,address=0x03",
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("--deployment repeats address", err)


class FixtureHygieneTests(unittest.TestCase):
    def test_no_committed_fixture_carries_a_local_path(self):
        """A fixture built on somebody's laptop should not ship their home
        directory. The build-info paths are normalised; this keeps them so."""
        for directory, _, names in os.walk(FIXTURES):
            for name in names:
                path = os.path.join(directory, name)
                with open(path, "rb") as handle:
                    body = handle.read()
                for marker in (b"/Users/", b"/home/", b"C:\\\\Users"):
                    self.assertNotIn(marker, body, "%s carries %r" % (path, marker))

    def test_the_fixture_holds_no_build_cache(self):
        for version in ("v1", "v2"):
            self.assertFalse(
                os.path.exists(os.path.join(FIXTURES, version, "cache")),
                "the forge cache records absolute paths and is not committed",
            )


if __name__ == "__main__":
    unittest.main()
