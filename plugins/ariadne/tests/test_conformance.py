"""The conformance fixtures, run as the test suite that keeps them honest.

The fixture directory is the artefact another implementation checks itself
against, and the suite reads the names of the files: `pass-*` verifies clean and
`fail-gate<n>-*` fails that gate and no other. A gate added without a fixture
fails the completeness test below rather than shipping unexercised.
"""

import json
import os
import re
import unittest
from unittest import mock

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, gates, registry, verify  # noqa: E402
import ariadne_lib.predicates  # noqa: F401,E402  (registers the shipped predicates)
from ariadne_lib.predicates import grounded_agent  # noqa: E402

FIXTURES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "conformance"
)
BREACH = re.compile(r"^fail-gate(\d+)-")
CHECK_BREACH = "fail-check-"
COMPOUND_CHECKS = frozenset(
    {"predicate-fields", "components", "optional-evidence"}
)
GROUNDED_AGENT_PASSING = (
    "pass-grounded-agent-complete.json",
    "pass-grounded-agent-null-evidence.json",
)
GROUNDED_AGENT_BREACHES = {
    "fail-gate2-grounded-agent-adapter-digest.json": (
        "pass-grounded-agent-complete.json",
        ((2, "environment"),),
        ("predicate.adapter.parameters_digest.sha256",),
    ),
    "fail-gate5-grounded-agent-first-capture-without-reason.json": (
        "pass-grounded-agent-complete.json",
        ((5, "comparison"),),
        ("predicate.comparison.first_capture_reason",),
    ),
    "fail-gate4-grounded-agent-promotion-verdict.json": (
        "pass-grounded-agent-complete.json",
        ((4, "no-conclusions"),),
        ("subject[9].annotations.verdict",),
    ),
    "fail-check-predicate-fields-grounded-agent-unknown-field.json": (
        "pass-grounded-agent-complete.json",
        ((2, "environment"), (None, "predicate-fields")),
        ("predicate.undeclared",),
    ),
    "fail-check-components-grounded-agent-component-not-a-subject.json": (
        "pass-grounded-agent-complete.json",
        ((2, "environment"), (None, "components")),
        ("predicate.given.corpus.components[0].sha256",),
    ),
    "fail-check-components-grounded-agent-unsafe-path.json": (
        "pass-grounded-agent-complete.json",
        ((2, "environment"), (None, "components")),
        ("predicate.given.corpus.components[0].path",),
    ),
    "fail-check-release-digest-grounded-agent-stale-semantic-digest.json": (
        "pass-grounded-agent-complete.json",
        ((None, "release-digest"),),
        ("predicate.policy.refusal_conditions[0]",),
    ),
    "fail-check-optional-evidence-grounded-agent-null-reads-without-reason.json": (
        "pass-grounded-agent-null-evidence.json",
        ((2, "environment"), (None, "optional-evidence")),
        ("predicate.given.reads_absence_reason",),
    ),
    "fail-check-subject-names-grounded-agent-nonportable-name.json": (
        "pass-grounded-agent-complete.json",
        ((None, "subject-names"),),
        ("subject[0].name",),
    ),
    "fail-check-evidence-boundary-grounded-agent-promotion-result.json": (
        "pass-grounded-agent-complete.json",
        ((None, "evidence-boundary"),),
        ("subject[9].annotations.passed",),
    ),
}
"""The exact parent, ordered failures and changed leaves for each new vector.

Gate 2 deliberately reuses field-shape, component and optional-evidence
validation.  Those counterexamples therefore have two honest failures; this
table keeps that observable without weakening the singleton contract for the
older fixtures.
"""
"""A check with no gate number gets a fixture too.

Gates 2 and 5 are numbered and belong to a predicate. The other checks a
predicate adds -- coverage, inputs, audits, deployments, the field-shape check --
carry no number, so they cannot use the `fail-gate<n>-` name. Without a fixture
they ship unexercised, which is the gap this convention closes.

The check name is recovered by longest match against the names the registered
predicates actually return, because a name like `predicate-fields` contains the
separator.
"""


def statement_of(name):
    with open(os.path.join(FIXTURES, name), "rb") as handle:
        return envelope.read(handle.read()).statement


def passing_by_type():
    """One passing fixture per predicate type, for asking a module what it checks."""
    found = {}
    for name in fixtures():
        if not name.startswith("pass-"):
            continue
        found.setdefault(statement_of(name).predicate_type, name)
    return found


def checks_of(type_uri, fixture):
    """Every gate a predicate module returns, as (number, name) pairs."""
    module = registry.DEFAULT.get(type_uri)
    if module is None or not callable(getattr(module, "check", None)):
        return []
    return [(g.number, g.name) for g in module.check(statement_of(fixture))]


def named_checks():
    """The unnumbered check names every registered predicate exposes."""
    names = set()
    for type_uri, fixture in passing_by_type().items():
        for number, name in checks_of(type_uri, fixture):
            if number is None:
                names.add(name)
    return names


def check_name_of(fixture):
    """The check a `fail-check-` fixture is named for, or None."""
    if not fixture.startswith(CHECK_BREACH):
        return None
    rest = fixture[len(CHECK_BREACH):]
    matches = [name for name in named_checks() if rest.startswith(name + "-")]
    return max(matches, key=len) if matches else None


def fixtures():
    return sorted(name for name in os.listdir(FIXTURES) if name.endswith(".json"))


def report_for(name):
    with open(os.path.join(FIXTURES, name), "rb") as handle:
        document = envelope.read(handle.read())
    return verify.report(document, registry.DEFAULT)


def failed_vector(report):
    return tuple(
        (gate.number, gate.name) for gate in report.gates if not gate.passed
    )


def failure_vector_obeys_name(name, failures):
    """Whether a complete ordered failure vector obeys its fixture name."""
    match = BREACH.match(name)
    if match:
        return len(failures) == 1 and failures[0][0] == int(match.group(1))
    check = check_name_of(name)
    if check is None:
        return False
    if failures == ((None, check),):
        return True
    return check in COMPOUND_CHECKS and failures == (
        (2, "environment"),
        (None, check),
    )


class FixtureTests(unittest.TestCase):
    def test_every_passing_fixture_verifies_clean(self):
        found = 0
        for name in fixtures():
            if not name.startswith("pass-"):
                continue
            with self.subTest(fixture=name):
                report = report_for(name)
                self.assertTrue(
                    report.ok,
                    "\n".join(g.line() for g in report.gates if not g.passed),
                )
            found += 1
        self.assertTrue(found)

    def test_every_breaching_fixture_fails_the_gate_it_is_named_for(self):
        found = 0
        for name in fixtures():
            match = BREACH.match(name)
            if not match:
                continue
            expected = int(match.group(1))
            with self.subTest(fixture=name):
                report = report_for(name)
                failed = failed_vector(report)
                self.assertTrue(
                    failure_vector_obeys_name(name, failed),
                    "%s should breach gate %d alone, breached %s"
                    % (name, expected, failed),
                )
                self.assertFalse(report.ok)
            found += 1
        self.assertTrue(found)

    def test_every_core_gate_has_a_breaching_fixture(self):
        """A gate with no fixture is a gate nobody else can test against."""
        covered = set()
        for name in fixtures():
            match = BREACH.match(name)
            if match:
                covered.add(int(match.group(1)))
        expected = {number for number, _ in gates.CORE_GATES}
        self.assertEqual(
            expected - covered,
            set(),
            "core gates with no breaching fixture: %s" % sorted(expected - covered),
        )

    def test_every_fixture_follows_the_naming_convention(self):
        for name in fixtures():
            with self.subTest(fixture=name):
                self.assertTrue(
                    name.startswith("pass-")
                    or BREACH.match(name)
                    or check_name_of(name) is not None,
                    "%s is not a pass-, fail-gate<n>- or fail-check-<name>- fixture"
                    % name,
                )

    def test_every_check_breaching_fixture_fails_the_check_it_is_named_for(self):
        found = 0
        for name in fixtures():
            expected = check_name_of(name)
            if expected is None:
                continue
            with self.subTest(fixture=name):
                report = report_for(name)
                failed = failed_vector(report)
                self.assertTrue(
                    failure_vector_obeys_name(name, failed),
                    "%s should breach %s under the naming contract, breached %s"
                    % (name, expected, failed),
                )
                self.assertFalse(report.ok)
            found += 1
        self.assertTrue(found)

    def test_every_registered_predicate_has_a_passing_fixture(self):
        registered = {type_uri for type_uri, _ in registry.DEFAULT.entries()}
        self.assertEqual(registered - set(passing_by_type()), set())

    def test_every_predicate_gate_has_a_breaching_fixture_of_its_own_type(self):
        """Gates 2 and 5 mean different things per predicate, so one type's
        fixture does not exercise another's."""
        for type_uri, fixture in passing_by_type().items():
            owned = {n for n, _ in checks_of(type_uri, fixture) if n is not None}
            if not owned:
                continue
            covered = set()
            for name in fixtures():
                match = BREACH.match(name)
                if match and statement_of(name).predicate_type == type_uri:
                    covered.add(int(match.group(1)))
            with self.subTest(predicate=type_uri):
                self.assertEqual(
                    owned - covered,
                    set(),
                    "%s gates with no breaching fixture of that type: %s"
                    % (type_uri, sorted(owned - covered)),
                )

    def test_every_named_check_has_a_breaching_fixture(self):
        """An unnumbered check with no fixture is one nobody else can test
        against, which is how `audits` and `deployments` shipped unexercised."""
        covered = {check_name_of(name) for name in fixtures()}
        covered.discard(None)
        self.assertEqual(
            named_checks() - covered,
            set(),
            "named checks with no breaching fixture: %s"
            % sorted(named_checks() - covered),
        )

    def test_the_envelope_fixture_reads_through_its_envelope(self):
        with open(
            os.path.join(FIXTURES, "pass-in-an-unsigned-envelope.json"), "rb"
        ) as handle:
            document = envelope.read(handle.read())
        self.assertIsNotNone(document.envelope)
        self.assertIn("unsigned", document.signature_state)

    def test_the_fixtures_are_formatted_as_committed_json(self):
        """They are read by other people's tools; keep them parseable and tidy."""
        for name in fixtures():
            path = os.path.join(FIXTURES, name)
            with open(path, "rb") as handle:
                raw = handle.read()
            with self.subTest(fixture=name):
                json.loads(raw.decode("utf-8"))
                self.assertTrue(raw.endswith(b"\n"), "%s has no trailing newline" % name)

    def test_state_fixture_v2_has_paired_release_proof_vectors(self):
        expected = {
            "pass-state-fixture-v2.json",
            "fail-gate2-state-fixture-v2-malformed-receipts-root.json",
            "fail-gate2-state-fixture-v2-backslash-path.json",
            "fail-gate2-state-fixture-v2-dot-segment-path.json",
            "fail-gate2-state-fixture-v2-invisible-segment-path.json",
            "fail-gate2-state-fixture-v2-whitespace-segment-path.json",
            "fail-gate5-state-fixture-v2-unnamed-current.json",
            "fail-gate5-state-fixture-v2-missing-baseline.json",
            "fail-gate5-state-fixture-v2-missing-current.json",
            "fail-gate5-state-fixture-v2-empty-components-without-baseline.json",
            "fail-check-evidence-state-fixture-v2-receipts-without-root.json",
            "fail-check-subject-names-state-fixture-v2-duplicate-name.json",
        }
        self.assertTrue(expected.issubset(set(fixtures())))
        for name in expected:
            with self.subTest(fixture=name):
                self.assertEqual(
                    statement_of(name).predicate_type,
                    "https://ariadne.wildcat.finance/state-fixture/v2",
                )


class NamingContractGuardTests(unittest.TestCase):
    def test_a_grounded_gate_vector_cannot_override_its_filename(self):
        """A gate-2 name wrapped around a real gate-4 report must be red.

        This drives the generic naming assertion itself.  The parent special
        case trusted the metadata vector and therefore accepted this mutation.
        """
        fake = "fail-gate2-grounded-agent-promotion-verdict.json"
        report = report_for("fail-gate4-grounded-agent-promotion-verdict.json")
        metadata = (
            "pass-grounded-agent-complete.json",
            ((4, "no-conclusions"),),
            ("subject[9].annotations.verdict",),
        )
        with (
            mock.patch(__name__ + ".fixtures", return_value=[fake]),
            mock.patch(__name__ + ".report_for", return_value=report),
            mock.patch.dict(GROUNDED_AGENT_BREACHES, {fake: metadata}),
        ):
            result = unittest.TestResult()
            FixtureTests(
                "test_every_breaching_fixture_fails_the_gate_it_is_named_for"
            ).run(result)
        self.assertFalse(
            result.wasSuccessful(),
            "a fail-gate2 filename was allowed to carry a gate-4 failure",
        )
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.errors, [])


class MinimalityTests(unittest.TestCase):
    """A breaching fixture of the state-fixture type is one change from a passing one.

    The fixtures are read as examples, so a reader diffing a breaching file against
    its passing sibling should see the rule and nothing else. `docs/conformance.md`
    states this, and a claim in a shipped document that nothing enforces is worth no
    more than the sentence.

    Scoped to one type on purpose. The older core fixtures are written against
    `pass-minimal.json`, the smallest statement that can carry the breach rather
    than a near sibling, and they differ by up to eight leaves. That is a different
    deliberate choice and not one this test is entitled to overturn.
    """

    TYPE = "https://ariadne.wildcat.finance/state-fixture/v1"
    PASSING = "pass-state-fixture.json"
    ALLOWED = {
        # A comparison against a baseline has to name a current side, so no single
        # change reaches that branch of gate 5.
        "fail-gate5-state-fixture-unnamed-current.json": 2,
        "fail-gate5-state-fixture-baseline-without-digest.json": 4,
    }

    @staticmethod
    def leaves(value, path=""):
        """Every leaf of a document, with its type beside its value.

        The type travels because `True == 1` and `0 == False` in Python. Two
        fixtures here change only a value's type, and a comparison without the type
        reports them as identical to the fixture they breach against -- which is
        the very equality those two rules exist to refuse.
        """
        if isinstance(value, dict):
            found = {}
            for key, item in value.items():
                here = "%s.%s" % (path, key) if path else key
                found.update(MinimalityTests.leaves(item, here))
            return found
        if isinstance(value, list):
            found = {}
            for index, item in enumerate(value):
                found.update(MinimalityTests.leaves(item, "%s[%d]" % (path, index)))
            return found or {path + "[]": ("empty", None)}
        return {path: (type(value).__name__, value)}

    def distance(self, left, right):
        one, two = self.leaves(left), self.leaves(right)
        changed = sorted(key for key in set(one) & set(two) if one[key] != two[key])
        return sorted(set(one) ^ set(two)) + changed

    def test_each_breaching_fixture_is_one_change_from_the_passing_one(self):
        passing = statement_of(self.PASSING).predicate
        found = 0
        for name in fixtures():
            if name.startswith("pass-"):
                continue
            if statement_of(name).predicate_type != self.TYPE:
                continue
            found += 1
            apart = self.distance(passing, statement_of(name).predicate)
            allowed = self.ALLOWED.get(name, 1)
            with self.subTest(fixture=name):
                self.assertEqual(
                    len(apart),
                    allowed,
                    "%s differs from %s in %d leaves rather than %d: %s"
                    % (name, self.PASSING, len(apart), allowed, apart),
                )
        self.assertTrue(found)

    def test_a_type_only_change_is_not_read_as_no_change(self):
        """The guard on the comparison above. Without the type, these two fixtures
        measure as identical to the passing one and the test passes for the wrong
        reason."""
        passing = statement_of(self.PASSING).predicate
        for name in (
            "fail-check-evidence-state-fixture-count-is-a-boolean.json",
            "fail-check-replay-state-fixture-zero-is-not-false.json",
        ):
            with self.subTest(fixture=name):
                self.assertEqual(
                    len(self.distance(passing, statement_of(name).predicate)), 1
                )


class GroundedAgentFixtureTests(unittest.TestCase):
    def distance(self, left, right):
        one = MinimalityTests.leaves(left)
        two = MinimalityTests.leaves(right)
        changed = sorted(key for key in set(one) & set(two) if one[key] != two[key])
        return sorted(set(one) ^ set(two)) + changed

    def test_the_grounded_agent_inventory_is_complete(self):
        passing = {
            name
            for name in fixtures()
            if name.startswith("pass-")
            and statement_of(name).predicate_type == grounded_agent.TYPE
        }
        breaching = {
            name
            for name in fixtures()
            if name.startswith("fail-")
            and statement_of(name).predicate_type == grounded_agent.TYPE
        }
        self.assertEqual(passing, set(GROUNDED_AGENT_PASSING))
        self.assertEqual(breaching, set(GROUNDED_AGENT_BREACHES))

    def test_the_complete_and_null_evidence_examples_cover_both_branches(self):
        complete = statement_of("pass-grounded-agent-complete.json").predicate
        self.assertIsInstance(complete["given"]["reads"], dict)
        self.assertIsInstance(complete["produced"]["evaluations"], dict)
        self.assertIsInstance(complete["produced"]["promotion"], dict)
        self.assertTrue(complete["given"]["corpus"]["components"])
        self.assertTrue(complete["produced"]["answers"])
        self.assertTrue(complete["policy"]["question_families"])
        self.assertIsNone(complete["comparison"]["baseline"])
        self.assertTrue(complete["comparison"]["first_capture_reason"].strip())

        absent = statement_of("pass-grounded-agent-null-evidence.json").predicate
        for block, reason in (
            (absent["given"]["reads"], absent["given"]["reads_absence_reason"]),
            (
                absent["produced"]["evaluations"],
                absent["produced"]["evaluations_absence_reason"],
            ),
            (
                absent["produced"]["promotion"],
                absent["produced"]["promotion_absence_reason"],
            ),
        ):
            with self.subTest(reason=reason):
                self.assertIsNone(block)
                self.assertTrue(reason.strip())

    def test_each_breach_has_its_exact_ordered_failure_vector(self):
        for name, (_, expected, _) in GROUNDED_AGENT_BREACHES.items():
            failed = failed_vector(report_for(name))
            with self.subTest(fixture=name):
                self.assertEqual(failed, expected)

    def test_each_declared_vector_obeys_its_filename(self):
        for name, (_, declared, _) in GROUNDED_AGENT_BREACHES.items():
            with self.subTest(fixture=name):
                self.assertTrue(
                    failure_vector_obeys_name(name, declared),
                    "%s contradicts its declared failure vector %s"
                    % (name, declared),
                )

    def test_each_breach_differs_from_its_clean_parent_only_at_named_leaves(self):
        for name, (parent, _, changed) in GROUNDED_AGENT_BREACHES.items():
            parent_statement = statement_of(parent)
            with self.subTest(fixture=name, parent=parent):
                self.assertTrue(report_for(parent).ok)
                self.assertEqual(
                    self.distance(
                        parent_statement.to_dict(), statement_of(name).to_dict()
                    ),
                    list(changed),
                )

    def test_passing_bodies_carry_no_gate_four_conclusion_keys(self):
        def conclusion_paths(value, path="predicate"):
            found = []
            if isinstance(value, dict):
                for key, child in value.items():
                    here = "%s.%s" % (path, key)
                    if gates.conclusion_key(key):
                        found.append(here)
                    found.extend(conclusion_paths(child, here))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    found.extend(
                        conclusion_paths(child, "%s[%d]" % (path, index))
                    )
            return found

        for name in GROUNDED_AGENT_PASSING:
            with self.subTest(fixture=name):
                self.assertEqual(conclusion_paths(statement_of(name).predicate), [])


if __name__ == "__main__":
    unittest.main()
