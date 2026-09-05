"""The shipped examples, including the ones that carry their gaps."""

import hashlib
import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, registry, verify  # noqa: E402
import ariadne_lib.predicates  # noqa: F401,E402  (registers the shipped predicates)
"""Imported for the side effect, as `test_conformance.py` does.

Without it this module passes only when something else has already registered the
predicates, which under `unittest discover` happens to be true and on its own is
not: every example reported gates 2 and 5 unchecked and the assertions that they
were checked failed. It was passing for a reason other than the one it states.
"""

EXAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples"
)
TAMPERED = os.path.join(EXAMPLES, "tampered")

BREACHES = {
    "escrow-v1.1.0-claim-repointed.json": 1,
    "escrow-v1.1.0-with-gaps-reason-removed.json": 3,
    "aave-v4-demo-v0-agent-policy-byte-changed.json": "release-digest",
    "aave-v4-spoke-v0-fixture-state-root-removed.json": "evidence",
}
"""What each tampered copy is meant to breach: a gate number, or the name of a
check that carries no number.

The fourth is the rule the state-fixture predicate exists for. Its state root is
gone and its proof-backed count is not, so the statement counts records with
nothing to have proved them against."""

TAMPER_PARENTS = {
    "escrow-v1.1.0-claim-repointed.json": "escrow-v1.1.0.json",
    "escrow-v1.1.0-with-gaps-reason-removed.json": (
        "escrow-v1.1.0-with-gaps.json"
    ),
    "aave-v4-demo-v0-agent-policy-byte-changed.json": (
        "aave-v4-demo-v0-agent.json"
    ),
    "aave-v4-spoke-v0-fixture-state-root-removed.json": "aave-v4-spoke-v0-fixture.json",
}

GROUNDED_STATEMENT = "aave-v4-demo-v0-agent.json"
GROUNDED_TAMPER = "aave-v4-demo-v0-agent-policy-byte-changed.json"
GROUNDED_BYTES = 7512
GROUNDED_SHA256 = (
    "3da25eb77f22c83697f28118afd140bec15bdeea87bf84c7c7b5000c2851729f"
)
GROUNDED_TAMPER_SHA256 = (
    "0bc6e5f8b94c858fe0ccb63b428b25f924964556427b893b223791d97dc2c62c"
)


def report_for(path):
    with open(path, "rb") as handle:
        document = envelope.read(handle.read())
    return verify.report(document, registry.DEFAULT)


def examples():
    return sorted(
        name for name in os.listdir(EXAMPLES) if name.endswith(".json")
    )


class ExampleTests(unittest.TestCase):
    def test_all_examples_verify_with_nothing_unchecked(self):
        found = examples()
        self.assertEqual(len(found), 4, found)
        for name in found:
            with self.subTest(example=name):
                report = report_for(os.path.join(EXAMPLES, name))
                self.assertTrue(
                    report.ok,
                    "\n".join(g.line() for g in report.gates if not g.passed),
                )
                self.assertEqual(report.unchecked, [])

    def test_grounded_agent_statement_has_frozen_bytes(self):
        with open(os.path.join(EXAMPLES, GROUNDED_STATEMENT), "rb") as handle:
            statement = handle.read()
        self.assertEqual(len(statement), GROUNDED_BYTES)
        self.assertEqual(hashlib.sha256(statement).hexdigest(), GROUNDED_SHA256)

    def test_grounded_agent_statement_exposes_its_exact_topology(self):
        with open(os.path.join(EXAMPLES, GROUNDED_STATEMENT), "rb") as handle:
            predicate = json.loads(handle.read().decode("utf-8"))["predicate"]

        self.assertEqual(len(predicate["produced"]["answers"]), 3)
        terminal = predicate["produced"]["promotion"]["terminal"]
        self.assertEqual(
            terminal,
            {
                "sequence": 1,
                "action": "promote",
                "target_release_digest": predicate["release"]["release_digest"],
            },
        )
        self.assertEqual(
            predicate["adapter"]["command"],
            [
                "python3",
                "plugins/berean/examples/aave-v4-demo-v0/rebuild.py",
            ],
        )

    def test_grounded_agent_guide_matches_topology_and_guard_scope(self):
        with open(os.path.join(EXAMPLES, "README.md"), encoding="utf-8") as handle:
            guide = handle.read()

        self.assertIn("three recorded answers", guide)
        self.assertIn("promoted the complete release", guide)
        self.assertNotIn("selected one answer", guide)
        self.assertIn("blocks sockets in its parent\nprocess", guide)
        self.assertIn("injects the same guard into each child command", guide)

    def test_the_unhappy_example_carries_its_timed_out_campaign(self):
        with open(os.path.join(EXAMPLES, "escrow-v1.1.0-with-gaps.json"), "rb") as f:
            predicate = json.loads(f.read().decode("utf-8"))["predicate"]
        claims = {entry["name"]: entry for entry in predicate["claims"]}
        campaign = claims["fuzz campaign"]
        self.assertEqual(campaign["disposition"], "timed_out")
        self.assertIn("properties outstanding", campaign["reason"])

    def test_the_unhappy_example_says_its_audit_covered_another_revision(self):
        report = report_for(
            os.path.join(EXAMPLES, "escrow-v1.1.0-with-gaps.json")
        )
        audits = [gate for gate in report.gates if gate.name == "audits"][0]
        self.assertTrue(audits.passed)
        self.assertIn("other than the released commit", audits.detail)

    def test_the_clean_example_says_its_audit_covered_the_release(self):
        report = report_for(os.path.join(EXAMPLES, "escrow-v1.1.0.json"))
        audits = [gate for gate in report.gates if gate.name == "audits"][0]
        self.assertNotIn("other than the released commit", audits.detail)

    def test_every_example_records_its_deployment_as_unconfirmed(self):
        for name in examples():
            with open(os.path.join(EXAMPLES, name), "rb") as handle:
                predicate = json.loads(handle.read().decode("utf-8"))["predicate"]
            for deployment in predicate.get("deployments", []):
                self.assertFalse(deployment["confirmed_against_chain"], name)


class FreshnessTests(unittest.TestCase):
    """The examples quote digests from the committed fixture.

    Rebuild the fixture and forget the examples, and they would go on claiming
    bytecode that no longer exists. This catches that.
    """

    def test_the_solidity_examples_still_describe_the_committed_fixture(self):
        from ariadne_lib.capture import foundry

        fixtures = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures", "forge-project"
        )
        current = foundry.capture(
            os.path.join(fixtures, "v2"),
            repository="https://github.com/wildcat-finance/example-escrow",
            commit="9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a",
            previous=os.path.join(fixtures, "v1"),
            previous_name="v1.0.0",
        )
        expected = current["predicate"]["release_subjects"]
        found = 0
        for name in examples():
            with open(os.path.join(EXAMPLES, name), "rb") as handle:
                document = json.loads(handle.read().decode("utf-8"))
            if "release_subjects" not in document["predicate"]:
                continue
            found += 1
            with self.subTest(example=name):
                self.assertEqual(
                    document["predicate"]["release_subjects"], expected
                )
        self.assertTrue(found)

    def test_the_state_fixture_example_still_describes_the_lazarus_fixture(self):
        """The same guard for the other kind. The example is a real capture over
        `plugins/lazarus/examples/aave-v4-spoke-v0`, so a change there without a
        recapture would leave it describing components that no longer exist."""
        from ariadne_lib.capture import state_fixture

        root = os.path.abspath(__file__)
        for _ in range(4):  # tests -> ariadne -> plugins -> the checkout
            root = os.path.dirname(root)
        aave_v4 = os.path.join(
            root, "plugins", "lazarus", "examples", "aave-v4-spoke-v0"
        )
        if not os.path.isdir(aave_v4):
            self.skipTest("Lazarus is not beside this plugin in this checkout")
        with open(os.path.join(EXAMPLES, "aave-v4-spoke-v0-fixture.json"), "rb") as handle:
            shipped = json.loads(handle.read().decode("utf-8"))
        current = state_fixture.capture(
            aave_v4,
            name="aave-v4-spoke-v0",
            capture_tool="lazarus",
            capture_command=[
                "python3", "scripts/lazarus.py", "verify", "examples/aave-v4-spoke-v0",
            ],
            parameters={"fixture": "aave-v4-spoke-v0"},
            first_capture_reason=(
                "first preservation release of this fixture; there is no earlier "
                "capture of this block to compare against"
            ),
        )
        self.assertEqual(current, shipped)


class TamperTests(unittest.TestCase):
    def test_every_tampered_copy_fails_the_gate_it_is_meant_to(self):
        found = sorted(
            name for name in os.listdir(TAMPERED) if name.endswith(".json")
        )
        self.assertEqual(sorted(BREACHES), found)
        for name, expected in BREACHES.items():
            with self.subTest(tampered=name):
                report = report_for(os.path.join(TAMPERED, name))
                self.assertFalse(report.ok)
                broken = [
                    gate.number if gate.number is not None else gate.name
                    for gate in report.gates
                    if not gate.passed
                ]
                self.assertEqual(broken, [expected])
                self.assertEqual(report.unchecked, [])

    def test_each_tampered_copy_differs_from_its_example_in_one_place(self):
        """A tamper that changed several things would pass for the wrong reason."""
        self.assertEqual(set(BREACHES), set(TAMPER_PARENTS))
        for name, source in TAMPER_PARENTS.items():
            with open(os.path.join(EXAMPLES, source), "rb") as handle:
                original = json.loads(handle.read().decode("utf-8"))
            with open(os.path.join(TAMPERED, name), "rb") as handle:
                changed = json.loads(handle.read().decode("utf-8"))
            with self.subTest(tampered=name):
                self.assertNotEqual(original, changed)
                self.assertEqual(original["subject"], changed["subject"])
                # Whichever block this type carries as its build record stays
                # identical, so the tamper is the one thing the name says.
                for field in ("build", "capture"):
                    if field in original["predicate"]:
                        self.assertEqual(
                            original["predicate"][field],
                            changed["predicate"][field],
                        )

    def test_grounded_agent_tamper_is_one_exact_byte_from_its_parent(self):
        with open(os.path.join(EXAMPLES, GROUNDED_STATEMENT), "rb") as handle:
            original = handle.read()
        with open(os.path.join(TAMPERED, GROUNDED_TAMPER), "rb") as handle:
            changed = handle.read()

        self.assertEqual(len(original), GROUNDED_BYTES)
        self.assertEqual(len(changed), GROUNDED_BYTES)
        self.assertEqual(
            hashlib.sha256(changed).hexdigest(), GROUNDED_TAMPER_SHA256
        )
        differences = [
            (offset, left, right)
            for offset, (left, right) in enumerate(zip(original, changed))
            if left != right
        ]
        self.assertEqual(differences, [(6765, ord("8"), ord("0"))])


if __name__ == "__main__":
    unittest.main()
