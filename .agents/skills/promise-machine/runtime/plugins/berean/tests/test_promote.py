"""Promotion is evidence, rollback is a record, the chain replays whole."""

from pathlib import Path

import json
import os
import shutil
import tempfile
import unittest

from tests.support import SCRIPTS, SCHEMAS, FIXTURES  # noqa: F401

from berean_lib import BereanError, canonical, digests, promote, release
from tests.test_corpus import failures

PASS_RELEASE = FIXTURES / "conformance" / "pass-release"
OTHER_DIGEST = "f" * 64


class PromoteFixture(unittest.TestCase):
    def setUp(self):
        self.holder = tempfile.TemporaryDirectory()
        self.directory = os.path.join(self.holder.name, "release")
        shutil.copytree(PASS_RELEASE, self.directory)
        self.document = release.load(self.directory)
        self.chain_path = os.path.join(self.directory, release.PROMOTIONS_FILE)

    def tearDown(self):
        self.holder.cleanup()

    def rewrite_report(self, mutate):
        report_path = os.path.join(self.directory, "evals", "report.json")
        with open(report_path, encoding="utf-8") as handle:
            report = json.loads(handle.read())
        mutate(report)
        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(report) + "\n")
        with open(os.path.join(self.directory, "release.json"), encoding="utf-8") as handle:
            document = json.loads(handle.read())
        document["evals"]["report_sha256"] = digests.of_file(report_path)
        document["release_digest"] = release.release_digest(document)
        with open(os.path.join(self.directory, "release.json"), "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(document) + "\n")
        self.document = release.load(self.directory)


class PromoteTests(PromoteFixture):
    def test_a_clean_report_promotes_and_the_release_is_active(self):
        record = promote.promote(self.directory, "first promotion")
        self.assertEqual(record["sequence"], 1)
        chain = promote.load_chain(self.chain_path)
        self.assertEqual(promote.state(chain, self.document), "active")
        self.assertEqual(failures(release.verify(self.directory)), [])

    def test_a_failed_report_does_not_promote(self):
        def mutate(report):
            report["passed"] = 1
            report["failed"] = 1
            report["failures"] = ["case-1"]

        self.rewrite_report(mutate)
        with self.assertRaises(BereanError):
            promote.promote(self.directory, "hopeful")
        self.assertFalse(os.path.exists(self.chain_path))

    def test_a_report_for_another_corpus_does_not_promote(self):
        def mutate(report):
            report["corpus_digest"] = OTHER_DIGEST

        self.rewrite_report(mutate)
        with self.assertRaises(BereanError):
            promote.promote(self.directory, "wrong corpus")

    def test_a_report_for_other_answers_does_not_promote(self):
        def mutate(report):
            report["answers_digest"] = OTHER_DIGEST

        self.rewrite_report(mutate)
        with self.assertRaises(BereanError):
            promote.promote(self.directory, "wrong answers")

    def test_the_report_is_parsed_from_the_digested_bytes(self):
        source = (Path(__file__).parents[1] / "scripts" / "berean_lib" / "promote.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("jsonio.load(report_path", source)
        self.assertIn("jsonio.loads(report_text", source)

    def test_a_pinned_pass_over_a_failing_case_does_not_promote(self):
        cases_path = os.path.join(self.directory, "evals", "cases.json")
        with open(cases_path, encoding="utf-8") as handle:
            cases_document = json.loads(handle.read())
        for case in cases_document["cases"]:
            if case["id"] == "c-stale":
                case["answer"]["discrepancies"] = []
        with open(cases_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(cases_document) + "\n")
        release_path = os.path.join(self.directory, "release.json")
        with open(release_path, encoding="utf-8") as handle:
            document = json.loads(handle.read())
        document["evals"]["cases_sha256"] = digests.of_file(cases_path)
        document["release_digest"] = release.release_digest(document)
        with open(release_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(document) + "\n")
        with open(os.path.join(self.directory, "evals", "report.json"), encoding="utf-8") as handle:
            pinned = json.loads(handle.read())
        pinned["cases_sha256"] = document["evals"]["cases_sha256"]
        with open(os.path.join(self.directory, "evals", "report.json"), "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(pinned) + "\n")
        document["evals"]["report_sha256"] = digests.of_file(
            os.path.join(self.directory, "evals", "report.json")
        )
        document["release_digest"] = release.release_digest(document)
        with open(release_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(document) + "\n")
        with self.assertRaises(BereanError) as caught:
            promote.promote(self.directory, "hopeful")
        self.assertIn("refusing to promote", str(caught.exception))

    def test_a_tampered_report_does_not_promote(self):
        report_path = os.path.join(self.directory, "evals", "report.json")
        with open(report_path, "ab") as handle:
            handle.write(b"\n")
        with self.assertRaises(BereanError):
            promote.promote(self.directory, "tampered")


class RollbackTests(PromoteFixture):
    def test_an_active_release_rolls_back_by_record(self):
        promote.promote(self.directory, "first promotion")
        record = promote.rollback(
            self.directory, OTHER_DIGEST, "grader gap found after promotion", "standing down"
        )
        self.assertEqual(record["sequence"], 2)
        chain = promote.load_chain(self.chain_path)
        self.assertEqual(
            promote.state(chain, self.document), f"rolled back to {OTHER_DIGEST}"
        )
        self.assertEqual(failures(release.verify(self.directory)), [])

    def test_an_unpromoted_release_does_not_roll_back(self):
        with self.assertRaises(BereanError):
            promote.rollback(self.directory, OTHER_DIGEST, "reason", "note")

    def test_a_rollback_restoring_itself_is_refused(self):
        promote.promote(self.directory, "first promotion")
        with self.assertRaises(BereanError):
            promote.rollback(
                self.directory, self.document["release_digest"], "reason", "note"
            )


class ChainTests(PromoteFixture):
    def test_a_reordered_chain_is_refused(self):
        promote.promote(self.directory, "first promotion")
        promote.rollback(self.directory, OTHER_DIGEST, "reason", "note")
        with open(self.chain_path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        with open(self.chain_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(reversed(lines)) + "\n")
        with self.assertRaises(BereanError):
            promote.load_chain(self.chain_path)

    def test_a_forged_count_in_the_chain_is_refused(self):
        promote.promote(self.directory, "first promotion")
        with open(self.chain_path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        record = json.loads(lines[0])
        record["evals"]["failed"] = 3
        record["evals"]["cases"] = 5
        with open(self.chain_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(record) + "\n")
        with self.assertRaises(BereanError):
            promote.load_chain(self.chain_path)

    def test_a_chain_naming_another_release_fails_verification(self):
        promote.promote(self.directory, "first promotion")
        with open(self.chain_path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        record = json.loads(lines[0])
        record["release_digest"] = OTHER_DIGEST
        with open(self.chain_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(record) + "\n")
        self.assertEqual(
            failures(release.verify(self.directory)), ["release-promotions"]
        )

    def test_the_staged_append_leaves_no_partial_file(self):
        promote.promote(self.directory, "first promotion")
        staging = [
            name for name in os.listdir(self.directory) if name.endswith(".staging")
        ]
        self.assertEqual(staging, [])


class ReportTests(unittest.TestCase):
    def test_report_counts_must_agree(self):
        report = {
            "format": promote.REPORT_FORMAT,
            "corpus_digest": "a" * 64,
            "cases_sha256": "b" * 64,
            "answers_digest": "c" * 64,
            "cases": 3,
            "passed": 1,
            "failed": 1,
            "failures": ["x"],
        }
        with self.assertRaises(BereanError):
            promote.validate_report(report)

    def test_a_zero_case_report_proves_nothing(self):
        report = {
            "format": promote.REPORT_FORMAT,
            "corpus_digest": "a" * 64,
            "cases_sha256": "b" * 64,
            "answers_digest": "c" * 64,
            "cases": 0,
            "passed": 0,
            "failed": 0,
            "failures": [],
        }
        with self.assertRaises(BereanError):
            promote.validate_report(report)


class SchemaAgreementTests(unittest.TestCase):
    def test_the_shipped_schema_matches_the_module(self):
        with open(SCHEMAS / "promotion-record-v1.json", encoding="utf-8") as handle:
            schema = json.load(handle)
        promote_shape, rollback_shape = schema["oneOf"]
        self.assertEqual(promote_shape["properties"]["format"]["const"], promote.FORMAT)
        self.assertEqual(tuple(promote_shape["required"]), promote.PROMOTE_FIELDS)
        self.assertEqual(tuple(rollback_shape["required"]), promote.ROLLBACK_FIELDS)
        self.assertEqual(
            tuple(promote_shape["properties"]["evals"]["required"]), promote.EVALS_FIELDS
        )


class CliTests(PromoteFixture):
    def test_the_cli_promotes_rolls_back_and_prints_the_chain(self):
        import importlib

        berean = importlib.import_module("berean")
        self.assertEqual(
            berean.main(["promote", self.directory, "--note", "first promotion"]), 0
        )
        self.assertEqual(berean.main(["promotion-chain", self.directory]), 0)
        self.assertEqual(
            berean.main(
                [
                    "rollback",
                    self.directory,
                    "--to",
                    OTHER_DIGEST,
                    "--reason",
                    "grader gap",
                    "--note",
                    "standing down",
                ]
            ),
            0,
        )
        self.assertEqual(
            berean.main(["promote", self.directory, "--note", "again"]), 0
        )


if __name__ == "__main__":
    unittest.main()
