"""The verify report and the `verify` subcommand.

Includes the one case the shipped registry cannot show: a predicate type that
is registered. The module below registers itself into a throwaway registry, so
the report's `unchecked` line disappears without the plugin shipping a
predicate it has not built yet.
"""

import contextlib
import hashlib
import io
import json
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

import ariadne  # noqa: E402
from ariadne_lib import envelope, gates, registry, statement, verify  # noqa: E402

ART = {"sha256": hashlib.sha256(b"artefact").hexdigest()}
TYPE = "https://ariadne.wildcat.finance/test-only/v1"


class TestOnlyPredicate(object):
    TYPE = TYPE
    SUMMARY = "a predicate that exists only inside this test module"


def document(predicate=None, predicate_type=TYPE, wrap=False):
    body = json.dumps(
        {
            "_type": statement.STATEMENT_TYPE,
            "subject": [{"name": "a", "digest": ART}],
            "predicateType": predicate_type,
            "predicate": predicate
            if predicate is not None
            else {
                "claims": [
                    {"name": "unit tests", "subject": ART, "disposition": "passed"}
                ],
                "commands": [],
            },
        }
    ).encode("utf-8")
    if wrap:
        body = envelope.wrap(body).to_json().encode("utf-8")
    return envelope.read(body)


def run(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ariadne.main(argv)
    return code, out.getvalue(), err.getvalue()


class ReportTests(unittest.TestCase):
    def test_a_clean_statement_reports_every_core_gate(self):
        report = verify.report(document(), registry.Registry())
        self.assertTrue(report.ok)
        self.assertEqual([gate.number for gate in report.gates], [1, 3, 4, 6, 7])

    def test_an_unregistered_type_says_which_gates_went_unchecked(self):
        report = verify.report(document(), registry.Registry())
        joined = "\n".join(report.unchecked)
        self.assertIn("gates 2 and 5", joined)
        self.assertIn("not registered here", joined)

    def test_a_registered_type_with_no_checks_says_so_rather_than_passing(self):
        """Registered is not checked. Silence here would be the shape of thing
        gate 3 exists to refuse."""
        known = registry.Registry()
        known.register(TestOnlyPredicate)
        report = verify.report(document(), known)
        self.assertIn("registered but exposes no checks", "\n".join(report.unchecked))
        self.assertIn("(registered)", "\n".join(report.lines()))

    def test_a_predicate_that_exposes_checks_has_them_run_and_reported(self):
        class Checking(object):
            TYPE = TYPE
            SUMMARY = "a predicate with a check of its own"

            @staticmethod
            def check(statement):
                return [gates.Gate(2, "environment", False, "no compiler recorded")]

        known = registry.Registry()
        known.register(Checking)
        report = verify.report(document(), known)
        self.assertIn("gate 5 was not checked", "\n".join(report.unchecked))
        self.assertFalse(report.predicate_gates_checked)
        self.assertIs(
            report.to_dict().get("predicateGatesChecked"),
            False,
        )
        self.assertFalse(report.ok)
        self.assertIn("gate 2 environment: FAIL", "\n".join(report.lines()))

    def test_a_predicate_that_reports_both_owned_gates_is_complete(self):
        class Checking(object):
            TYPE = TYPE
            SUMMARY = "a predicate with both owned gates"

            @staticmethod
            def check(statement):
                return [
                    gates.Gate(2, "environment", True, "recorded"),
                    gates.Gate(5, "comparison", True, "recorded"),
                ]

        known = registry.Registry()
        known.register(Checking)
        report = verify.report(document(), known)
        self.assertTrue(report.predicate_gates_checked)
        self.assertEqual(report.unchecked, [])
        self.assertIs(
            report.to_dict().get("predicateGatesChecked"),
            True,
        )

    def test_a_declared_result_contract_refuses_missing_duplicate_or_reordered_checks(self):
        expected = (
            (2, "environment"),
            (5, "comparison"),
            (None, "binding"),
        )
        cases = (
            (
                "missing",
                [
                    gates.Gate(2, "environment", True, "recorded"),
                    gates.Gate(5, "comparison", True, "recorded"),
                ],
            ),
            (
                "duplicate",
                [
                    gates.Gate(2, "environment", True, "recorded"),
                    gates.Gate(2, "environment", True, "recorded again"),
                    gates.Gate(5, "comparison", True, "recorded"),
                    gates.Gate(None, "binding", True, "recorded"),
                ],
            ),
            (
                "reordered",
                [
                    gates.Gate(5, "comparison", True, "recorded"),
                    gates.Gate(2, "environment", True, "recorded"),
                    gates.Gate(None, "binding", True, "recorded"),
                ],
            ),
        )
        for label, returned in cases:
            class Regressed(object):
                TYPE = TYPE
                SUMMARY = "a predicate whose declared result set regressed"
                EXPECTED_RESULTS = expected

                @staticmethod
                def check(statement):
                    return returned

            known = registry.Registry()
            known.register(Regressed)
            with self.subTest(label=label):
                report = verify.report(document(), known)
                self.assertFalse(report.ok)
                self.assertFalse(report.predicate_gates_checked)
                self.assertEqual(report.missing_predicate_gates, (2, 5))
                self.assertIn(
                    "does not match its declared result contract",
                    "\n".join(report.lines()),
                )

    def test_a_malformed_declared_result_contract_fails_closed(self):
        malformed = (
            [(2, "environment"), (5, "comparison")],
            ((2, "environment"),),
            ((2, "environment"), (2, "again"), (5, "comparison")),
            ((1, "core-owned"), (2, "environment"), (5, "comparison")),
            ((True, "environment"), (5, "comparison")),
            ((2, "same"), (5, "same")),
        )
        for declared in malformed:
            class BrokenContract(object):
                TYPE = TYPE
                SUMMARY = "a predicate with a malformed result contract"
                EXPECTED_RESULTS = declared

                @staticmethod
                def check(statement):
                    return [
                        gates.Gate(2, "environment", True, "recorded"),
                        gates.Gate(5, "comparison", True, "recorded"),
                    ]

            known = registry.Registry()
            known.register(BrokenContract)
            with self.subTest(declared=declared):
                report = verify.report(document(), known)
                self.assertFalse(report.ok)
                self.assertFalse(report.predicate_gates_checked)
                self.assertEqual(report.missing_predicate_gates, (2, 5))
                self.assertIn(
                    "malformed declared result contract",
                    "\n".join(report.lines()),
                )

    def test_a_predicate_that_raises_fails_its_own_gate_rather_than_the_run(self):
        class Broken(object):
            TYPE = TYPE
            SUMMARY = "a predicate whose check falls over"

            @staticmethod
            def check(statement):
                raise KeyError("compiler")

        known = registry.Registry()
        known.register(Broken)
        report = verify.report(document(), known)
        self.assertFalse(report.ok)
        joined = "\n".join(report.lines())
        self.assertIn("raised while checking", joined)
        self.assertIn("gate 1 subject-naming: pass", joined)

    def test_a_predicate_returning_something_other_than_gates_fails(self):
        class Odd(object):
            TYPE = TYPE
            SUMMARY = "a predicate returning the wrong shape"

            @staticmethod
            def check(statement):
                return ["gate 2 is fine, trust me"]

        known = registry.Registry()
        known.register(Odd)
        report = verify.report(document(), known)
        self.assertFalse(report.ok)
        self.assertIn("not a gate", "\n".join(report.lines()))

    def test_predicate_gate_fields_are_validated_before_the_report_trusts_them(self):
        cases = (
            ("number", "2"),
            ("number", 2.0),
            ("number", 1),
            ("name", 17),
            ("passed", "false"),
            ("detail", {"unexpected": "shape"}),
        )
        observed = []
        for field, value in cases:
            first = gates.Gate(2, "environment", True, "recorded")
            setattr(first, field, value)
            returned = [first, gates.Gate(5, "comparison", True, "recorded")]

            class Malformed(object):
                TYPE = TYPE
                SUMMARY = "a predicate returning a malformed gate"

                @staticmethod
                def check(statement):
                    return returned

            known = registry.Registry()
            known.register(Malformed)
            try:
                report = verify.report(document(), known)
                rendered = report.to_dict()
                lines = "\n".join(report.lines())
                outcome = (
                    report.ok,
                    report.predicate_gates_checked,
                    report.missing_predicate_gates,
                    "malformed gate" in lines,
                    all(type(gate.get("passed")) is bool for gate in rendered["gates"]),
                )
            except Exception as error:  # noqa: BLE001 -- a crash is the observed result
                outcome = ("raised", type(error).__name__)
            observed.append((field, type(value).__name__, outcome))

        expected = [
            (field, type(value).__name__, (False, False, (2, 5), True, True))
            for field, value in cases
        ]
        self.assertEqual(observed, expected)

    def test_an_exception_with_an_unprintable_message_still_becomes_a_gate(self):
        class Unprintable(Exception):
            def __str__(self):
                raise RuntimeError("message rendering broke")

        class Broken(object):
            TYPE = TYPE
            SUMMARY = "a predicate whose exception cannot be rendered"

            @staticmethod
            def check(statement):
                raise Unprintable()

        known = registry.Registry()
        known.register(Broken)
        try:
            report = verify.report(document(), known)
            outcome = (report.ok, "raised while checking" in "\n".join(report.lines()))
        except Exception as error:  # noqa: BLE001 -- a crash is the observed result
            outcome = ("raised", type(error).__name__)
        self.assertEqual(outcome, (False, True))

    def test_a_signed_document_reports_that_signatures_went_unchecked(self):
        payload = json.dumps(
            {
                "_type": statement.STATEMENT_TYPE,
                "subject": [{"name": "a", "digest": ART}],
                "predicateType": TYPE,
                "predicate": {"claims": [], "commands": []},
            }
        ).encode("utf-8")
        found = envelope.Envelope(
            payload, signatures=[envelope.Signature("AA==", "key-1")]
        )
        report = verify.report(envelope.read(found.to_json()), registry.Registry())
        self.assertIn(
            "signatures were not checked", "\n".join(report.unchecked)
        )

    def test_a_breach_shows_in_the_report_and_in_ok(self):
        report = verify.report(
            document({"claims": [], "commands": [{"name": "b", "argv": ["x"]}]}),
            registry.Registry(),
        )
        self.assertFalse(report.ok)
        self.assertIn("FAIL", "\n".join(report.lines()))

    def test_the_json_report_carries_the_same_verdict(self):
        found = verify.report(document(), registry.Registry()).to_dict()
        self.assertTrue(found["ok"])
        self.assertEqual(len(found["gates"]), 5)
        self.assertFalse(found["predicateTypeKnown"])
        self.assertIs(found.get("predicateGatesChecked"), False)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, name, content):
        path = os.path.join(self.root, name)
        with open(path, "wb") as handle:
            handle.write(content if isinstance(content, bytes) else content.encode())
        return path

    def fixture(self, name):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fixtures",
            "conformance",
            name,
        )

    def test_a_clean_fixture_exits_zero_with_five_gate_lines(self):
        code, out, _ = run(["verify", self.fixture("pass-absence-recorded.json")])
        self.assertEqual(code, 0)
        self.assertEqual(len([line for line in out.splitlines() if ": pass -- " in line]), 5)

    def test_a_breaching_fixture_exits_one_and_names_the_gate(self):
        code, out, _ = run(
            ["verify", self.fixture("fail-gate3-skipped-without-reason.json")]
        )
        self.assertEqual(code, 1)
        self.assertIn("gate 3 absence: FAIL", out)

    def test_an_envelope_verifies_through_its_wrapper(self):
        code, out, _ = run(["verify", self.fixture("pass-in-an-unsigned-envelope.json")])
        self.assertEqual(code, 0)
        self.assertIn("unsigned", out)

    def test_a_file_over_the_size_cap_exits_two(self):
        path = self.write("big.json", "{" + " " * 5000 + "}")
        code, _, err = run(["verify", path, "--max-bytes", "128"])
        self.assertEqual(code, 2)
        self.assertIn("byte cap", err)

    def test_a_file_nested_past_the_depth_cap_exits_two(self):
        path = self.write("deep.json", "[" * 100 + "]" * 100)
        code, _, err = run(["verify", path, "--max-depth", "16"])
        self.assertEqual(code, 2)
        self.assertIn("nested deeper", err)

    def test_a_file_with_duplicate_keys_exits_two(self):
        path = self.write("dup.json", '{"_type":"a","_type":"b"}')
        code, _, err = run(["verify", path])
        self.assertEqual(code, 2)
        self.assertIn("duplicate key", err)

    def test_a_missing_file_exits_two(self):
        code, _, err = run(["verify", os.path.join(self.root, "absent.json")])
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)

    def test_a_fifo_is_refused_rather_than_blocking_the_read(self):
        """A fifo reports a size of zero and then blocks until somebody writes."""
        path = os.path.join(self.root, "pipe.json")
        os.mkfifo(path)
        code, _, err = run(["verify", path])
        self.assertEqual(code, 2)
        self.assertIn("not a regular file", err)

    def test_the_json_output_is_machine_readable(self):
        code, out, _ = run(
            ["verify", self.fixture("pass-minimal.json"), "--json"]
        )
        self.assertEqual(code, 0)
        found = json.loads(out)
        self.assertTrue(found["ok"])
        self.assertEqual(len(found["gates"]), 5)

    def test_inspect_takes_the_same_bounds(self):
        path = self.write("deep.json", "[" * 100 + "]" * 100)
        code, _, err = run(["inspect", path, "--max-depth", "16"])
        self.assertEqual(code, 2)
        self.assertIn("nested deeper", err)


if __name__ == "__main__":
    unittest.main()
