"""The published schemas and the verifier, over every fixture that ships.

Three separate drift findings came from putting one document through both and
comparing the verdicts: a delta side name the schemas accepted and every verifier
refused, a component path the state-fixture schema accepted and its verifier
rejected, and a deployment confirmation the verifier accepted and its own schema
refused. Drift runs in both directions, and each time the pair disagreed a producer
following one of them was sent into a refusal by the other.

Hand-written case lists found the first only after they were extended to the
shipped files, so this runs over the fixtures themselves. They are the artefact
another implementation reads, which makes them the set that has to agree.

`jsonschema` is not a dependency of this plugin. Without it the comparison cannot
run and the test skips, which is why `test_state_fixture.py` also holds the
structural facts a plain reader can check.
"""

import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, registry, verify  # noqa: E402
import ariadne_lib.predicates  # noqa: F401,E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures", "conformance")
SCHEMAS = os.path.join(os.path.dirname(HERE), "schemas")

FOR_TYPE = {
    "https://ariadne.wildcat.finance/solidity-release/v1": "solidity-release-v1.json",
    "https://ariadne.wildcat.finance/dataset/v1": "dataset-v1.json",
    "https://ariadne.wildcat.finance/state-fixture/v1": "state-fixture-v1.json",
    "https://ariadne.wildcat.finance/state-fixture/v2": "state-fixture-v2.json",
    "https://ariadne.wildcat.finance/grounded-agent/v1": "grounded-agent-v1.json",
}

ACCEPTED_BY_THE_SCHEMA = {
    # Beyond any schema. Whether a component digest also appears in the
    # statement's `subject` array is a fact about the document around the
    # predicate, and no keyword reaches outside the body being validated.
    "fail-gate2-state-fixture-component-not-a-subject.json": (
        "a schema validates the predicate body and cannot see the subjects"
    ),
    "fail-check-subject-names-state-fixture-v2-duplicate-name.json": (
        "the predicate schema cannot see or compare outer subject names"
    ),
    # Expressible and not yet expressed. `anyOf` over an input item would say
    # that a digest or a disposition has to be there.
    "fail-check-inputs-dataset-locator-only.json": (
        "expressible with anyOf on an input item; recorded as a lead"
    ),
    # Expressible and not yet expressed. `if`/`then` on a null baseline would
    # refuse the delta sections beside it, as the state-fixture schema does for
    # its own conditional rule.
    "fail-gate5-content-against-null-baseline.json": (
        "expressible with if/then on a null baseline; recorded as a lead"
    ),
}
"""Fixtures the verifier refuses and a schema accepts, each with its reason.

An entry here is a claim that the disagreement is understood, not that it is
fine. Two of the three name the keyword that would close them. A disagreement
with no entry fails the test rather than joining the list quietly.
"""


def validator_for(type_uri):
    import jsonschema

    with open(os.path.join(SCHEMAS, FOR_TYPE[type_uri]), "rb") as handle:
        schema = json.loads(handle.read().decode("utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


class AgreementTests(unittest.TestCase):
    def setUp(self):
        try:
            import jsonschema  # noqa: F401
        except ImportError:
            self.skipTest("jsonschema is not installed")

    def test_each_shipped_fixture_gets_the_same_verdict_from_both(self):
        validators = {uri: validator_for(uri) for uri in FOR_TYPE}
        found = 0
        for name in sorted(os.listdir(FIXTURES)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(FIXTURES, name), "rb") as handle:
                document = envelope.read(handle.read())
            type_uri = document.statement.predicate_type
            if type_uri not in validators:
                continue
            found += 1
            verifier_ok = verify.report(document, registry.DEFAULT).ok
            errors = list(
                validators[type_uri].iter_errors(document.statement.predicate)
            )
            expected = verifier_ok or name in ACCEPTED_BY_THE_SCHEMA
            with self.subTest(fixture=name):
                self.assertEqual(
                    not errors,
                    expected,
                    "%s: verifier %s, schema %s%s"
                    % (
                        name,
                        verifier_ok,
                        not errors,
                        "" if verifier_ok else " (add a reason to "
                        "ACCEPTED_BY_THE_SCHEMA only if it is understood)",
                    ),
                )
        self.assertTrue(found)

    def test_no_passing_fixture_is_refused_by_its_schema(self):
        """The other direction. A schema stricter than the verifier turns a
        statement this tool wrote into one its own published shape rejects."""
        validators = {uri: validator_for(uri) for uri in FOR_TYPE}
        for name in sorted(os.listdir(FIXTURES)):
            if not name.startswith("pass-") or not name.endswith(".json"):
                continue
            with open(os.path.join(FIXTURES, name), "rb") as handle:
                document = envelope.read(handle.read())
            type_uri = document.statement.predicate_type
            if type_uri not in validators:
                continue
            errors = list(
                validators[type_uri].iter_errors(document.statement.predicate)
            )
            with self.subTest(fixture=name):
                self.assertEqual(
                    errors, [], [error.message for error in errors[:3]]
                )

    def test_named_failures_are_refused_by_their_schema_when_expressible(self):
        validators = {uri: validator_for(uri) for uri in FOR_TYPE}
        for name in sorted(os.listdir(FIXTURES)):
            if (
                not name.startswith("fail-")
                or not name.endswith(".json")
                or name in ACCEPTED_BY_THE_SCHEMA
            ):
                continue
            with open(os.path.join(FIXTURES, name), "rb") as handle:
                document = envelope.read(handle.read())
            type_uri = document.statement.predicate_type
            if type_uri not in validators:
                continue
            errors = list(
                validators[type_uri].iter_errors(document.statement.predicate)
            )
            with self.subTest(fixture=name):
                self.assertTrue(errors, "%s passed its published schema" % name)

    def test_every_exception_names_a_fixture_that_exists(self):
        """A stale entry would hide a disagreement that came back."""
        for name in ACCEPTED_BY_THE_SCHEMA:
            with self.subTest(fixture=name):
                self.assertTrue(
                    os.path.isfile(os.path.join(FIXTURES, name)),
                    "%s is listed as an allowed disagreement and does not exist"
                    % name,
                )

    def test_every_exception_is_still_a_disagreement(self):
        """An entry that no longer disagrees has been fixed, and leaving it here
        would let a later one hide behind it."""
        validators = {uri: validator_for(uri) for uri in FOR_TYPE}
        for name in ACCEPTED_BY_THE_SCHEMA:
            with open(os.path.join(FIXTURES, name), "rb") as handle:
                document = envelope.read(handle.read())
            validator = validators[document.statement.predicate_type]
            errors = list(validator.iter_errors(document.statement.predicate))
            with self.subTest(fixture=name):
                self.assertEqual(
                    errors,
                    [],
                    "%s no longer disagrees; remove it from "
                    "ACCEPTED_BY_THE_SCHEMA" % name,
                )


if __name__ == "__main__":
    unittest.main()
