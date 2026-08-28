"""The five core gates, one by one."""

import hashlib
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import gates, statement  # noqa: E402

ART = {"sha256": hashlib.sha256(b"artefact").hexdigest()}
OTHER = {"sha256": hashlib.sha256(b"other").hexdigest()}
OUT = {"sha256": hashlib.sha256(b"output").hexdigest()}
TYPE = "https://ariadne.wildcat.finance/example/v1"


def built(predicate, subject=None):
    return statement.Statement.from_dict(
        {
            "_type": statement.STATEMENT_TYPE,
            "subject": subject or [{"name": "a", "digest": ART}],
            "predicateType": TYPE,
            "predicate": predicate,
        }
    )


def claim(**overrides):
    out = {"name": "unit tests", "subject": ART, "disposition": "passed"}
    out.update(overrides)
    return out


def command(**overrides):
    out = {"name": "build", "argv": ["make", "build"], "determinism": "exact"}
    out.setdefault("output_digest", OUT)
    out.update(overrides)
    return out


def only(number, predicate, subject=None):
    """Run one gate over a statement and return it."""
    found = built(predicate, subject)
    for gate_number, check in gates.CORE_GATES:
        if gate_number == number:
            return check(found)
    raise AssertionError("no gate %d" % number)


class GateOneTests(unittest.TestCase):
    def test_a_claim_naming_a_subject_of_the_statement_passes(self):
        gate = only(1, {"claims": [claim()], "commands": []})
        self.assertTrue(gate.passed, gate.detail)

    def test_a_claim_naming_a_branch_fails(self):
        gate = only(1, {"claims": [claim(subject="refs/heads/main")], "commands": []})
        self.assertFalse(gate.passed)
        self.assertIn("rather than a digest set", gate.detail)

    def test_a_claim_naming_a_digest_the_statement_does_not_cover_fails(self):
        gate = only(1, {"claims": [claim(subject=OTHER)], "commands": []})
        self.assertFalse(gate.passed)
        self.assertIn("not a subject of this statement", gate.detail)

    def test_a_claim_with_no_subject_fails(self):
        entry = claim()
        del entry["subject"]
        gate = only(1, {"claims": [entry], "commands": []})
        self.assertFalse(gate.passed)
        self.assertIn("names no subject", gate.detail)

    def test_a_malformed_digest_in_a_claim_fails(self):
        gate = only(1, {"claims": [claim(subject={"sha256": "abc"})], "commands": []})
        self.assertFalse(gate.passed)

    def test_no_claims_passes_and_says_so(self):
        gate = only(1, {"claims": [], "commands": []})
        self.assertTrue(gate.passed)
        self.assertIn("no claims", gate.detail)


class GateThreeTests(unittest.TestCase):
    def test_a_missing_claims_block_fails(self):
        gate = only(3, {"commands": []})
        self.assertFalse(gate.passed)
        self.assertIn("an absent record is not an empty one", gate.detail)

    def test_a_missing_commands_block_fails(self):
        gate = only(3, {"claims": []})
        self.assertFalse(gate.passed)
        self.assertIn("commands", gate.detail)

    def test_a_claim_with_no_disposition_fails(self):
        entry = claim()
        del entry["disposition"]
        gate = only(3, {"claims": [entry], "commands": []})
        self.assertFalse(gate.passed)
        self.assertIn("no disposition", gate.detail)

    def test_a_disposition_outside_the_vocabulary_fails(self):
        gate = only(3, {"claims": [claim(disposition="probably fine")], "commands": []})
        self.assertFalse(gate.passed)
        self.assertIn("outside", gate.detail)

    def test_skipped_without_a_reason_fails(self):
        gate = only(3, {"claims": [claim(disposition="skipped")], "commands": []})
        self.assertFalse(gate.passed)
        self.assertIn("the reason is the record", gate.detail)

    def test_skipped_with_a_reason_passes_and_is_counted(self):
        gate = only(
            3,
            {
                "claims": [claim(disposition="skipped", reason="no engine configured")],
                "commands": [],
            },
        )
        self.assertTrue(gate.passed, gate.detail)
        self.assertIn("1 skipped", gate.detail)

    def test_a_whitespace_reason_does_not_count_as_one(self):
        gate = only(
            3, {"claims": [claim(disposition="failed", reason="   ")], "commands": []}
        )
        self.assertFalse(gate.passed)

    def test_a_failed_claim_is_preserved_rather_than_refused(self):
        gate = only(
            3,
            {
                "claims": [claim(disposition="failed", reason="two assertions broke")],
                "commands": [],
            },
        )
        self.assertTrue(gate.passed, gate.detail)
        self.assertIn("1 failed", gate.detail)

    def test_an_unknown_claim_field_fails(self):
        gate = only(3, {"claims": [claim(outcome="fine")], "commands": []})
        self.assertFalse(gate.passed)
        self.assertIn("outcome", gate.detail)


class GateFourTests(unittest.TestCase):
    def test_a_verdict_key_anywhere_in_the_predicate_fails(self):
        gate = only(
            4,
            {
                "claims": [claim()],
                "commands": [],
                "summary": {"nested": {"verdict": "no issues"}},
            },
        )
        self.assertFalse(gate.passed)
        self.assertIn("verdict", gate.detail)

    def test_the_check_folds_case_and_separators(self):
        for key in ("risk_free", "riskFree", "RISKFREE"):
            gate = only(4, {"claims": [], "commands": [], key: True})
            self.assertFalse(gate.passed, key)

    def test_structured_conclusion_compounds_fail(self):
        for key in (
            "security_verdict",
            "riskScore",
            "safety-conclusion",
            "approval_status",
            "securityRating",
            "assurance_level",
            "audit_recommendation",
        ):
            gate = only(4, {"claims": [], "commands": [], key: "positive"})
            with self.subTest(key=key):
                self.assertFalse(gate.passed, gate.detail)
                self.assertIn(key, gate.detail)

    def test_neutral_status_and_conclusion_process_metadata_pass(self):
        for key in ("status", "identity", "approval_workflow", "score_method"):
            gate = only(4, {"claims": [], "commands": [], key: "recorded"})
            with self.subTest(key=key):
                self.assertTrue(gate.passed, gate.detail)

    def test_a_verdict_in_a_subject_annotation_fails_too(self):
        """The shorter route: a subject's annotations are producer-chosen too."""
        gate = only(
            4,
            {"claims": [], "commands": []},
            subject=[{"name": "a", "digest": ART, "annotations": {"rating": "A+"}}],
        )
        self.assertFalse(gate.passed)
        self.assertIn("rating", gate.detail)

    def test_a_measurement_is_not_a_conclusion(self):
        gate = only(
            4,
            {
                "claims": [claim(detail={"cases": 87, "properties_held": 4})],
                "commands": [],
            },
        )
        self.assertTrue(gate.passed, gate.detail)


class GateSixTests(unittest.TestCase):
    def test_a_command_with_a_class_and_an_output_digest_passes(self):
        gate = only(6, {"claims": [], "commands": [command()]})
        self.assertTrue(gate.passed, gate.detail)

    def test_a_command_with_no_determinism_class_fails(self):
        entry = command()
        del entry["determinism"]
        gate = only(6, {"claims": [], "commands": [entry]})
        self.assertFalse(gate.passed)
        self.assertIn("declares no determinism class", gate.detail)

    def test_an_exact_command_with_no_output_digest_fails(self):
        entry = command()
        del entry["output_digest"]
        gate = only(6, {"claims": [], "commands": [entry]})
        self.assertFalse(gate.passed)
        self.assertIn("nothing to compare a replay against", gate.detail)

    def test_a_nondeterministic_command_needs_no_output_digest(self):
        gate = only(
            6,
            {
                "claims": [],
                "commands": [
                    {
                        "name": "fuzz",
                        "argv": ["echidna", "."],
                        "determinism": "nondeterministic",
                    }
                ],
            },
        )
        self.assertTrue(gate.passed, gate.detail)

    def test_a_command_with_no_argv_fails(self):
        entry = command()
        del entry["argv"]
        gate = only(6, {"claims": [], "commands": [entry]})
        self.assertFalse(gate.passed)
        self.assertIn("nobody else could run it", gate.detail)

    def test_a_class_outside_the_vocabulary_fails(self):
        gate = only(6, {"claims": [], "commands": [command(determinism="mostly")]})
        self.assertFalse(gate.passed)


class GateSevenTests(unittest.TestCase):
    def test_a_payload_asserting_its_own_verification_fails(self):
        gate = only(7, {"claims": [claim(detail={"verified": True})], "commands": []})
        self.assertFalse(gate.passed)
        self.assertIn("verified", gate.detail)

    def test_a_payload_naming_its_own_author_fails(self):
        gate = only(7, {"claims": [], "commands": [], "author": "wildcat labs"})
        self.assertFalse(gate.passed)

    def test_a_signed_by_key_fails_however_it_is_spelled(self):
        for key in ("signed_by", "signedBy", "attested_by"):
            gate = only(7, {"claims": [], "commands": [], key: "someone"})
            self.assertFalse(gate.passed, key)

    def test_direct_authorship_identity_and_status_compounds_fail(self):
        for key in (
            "signature_status",
            "verificationStatus",
            "SIGNER-IDENTITY",
            "attestation_status",
            "authorshipIdentity",
            "notarization_status",
        ):
            gate = only(7, {"claims": [], "commands": [], key: "verified"})
            with self.subTest(key=key):
                self.assertFalse(gate.passed, gate.detail)
                self.assertIn(key, gate.detail)

    def test_direct_authorship_names_and_multitoken_status_claims_fail(self):
        for key in (
            "author_name",
            "publisherName",
            "SIGNER-NAME",
            "signature_verification_status",
            "signatureValidationStatus",
            "signatureverificationstatus",
            "attestation-verification-status",
            "is_verified",
            "signed_by_identity",
        ):
            gate = only(7, {"claims": [], "commands": [], key: "someone"})
            with self.subTest(key=key):
                self.assertFalse(gate.passed, gate.detail)
                self.assertIn(key, gate.detail)

    def test_neutral_identity_and_signature_metadata_pass(self):
        for key in (
            "identity",
            "status",
            "signature_algorithm",
            "verification_method",
            "attestation_format",
        ):
            gate = only(7, {"claims": [], "commands": [], key: "recorded"})
            with self.subTest(key=key):
                self.assertTrue(gate.passed, gate.detail)

    def test_an_author_in_a_subject_annotation_fails_too(self):
        gate = only(
            7,
            {"claims": [], "commands": []},
            subject=[{"name": "a", "digest": ART, "annotations": {"signed_by": "us"}}],
        )
        self.assertFalse(gate.passed)

    def test_an_ordinary_predicate_passes(self):
        gate = only(7, {"claims": [claim()], "commands": [command()]})
        self.assertTrue(gate.passed, gate.detail)


class RunTests(unittest.TestCase):
    def test_run_returns_every_core_gate_in_order(self):
        found = gates.run(built({"claims": [claim()], "commands": [command()]}))
        self.assertEqual([gate.number for gate in found], [1, 3, 4, 6, 7])
        self.assertTrue(all(gate.passed for gate in found))

    def test_a_gate_reports_rather_than_raises_on_a_broken_predicate(self):
        found = gates.run(built({"claims": "not a list", "commands": []}))
        self.assertFalse(all(gate.passed for gate in found))

    def test_the_line_format_names_the_gate_and_its_verdict(self):
        gate = only(1, {"claims": [claim()], "commands": []})
        self.assertTrue(gate.line().startswith("gate 1 subject-naming: pass -- "))


if __name__ == "__main__":
    unittest.main()
