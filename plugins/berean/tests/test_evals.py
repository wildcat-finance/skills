"""The evaluation corpus: each grader provable and breachable, digests first."""

import json
import os
import shutil
import tempfile
import unittest

from tests.support import SCRIPTS, SCHEMAS, FIXTURES  # noqa: F401

from berean_lib import BereanError, canonical, digests, evals, release
from tests import release_fixture

PASS_RELEASE = FIXTURES / "conformance" / "pass-release"


def case_results(results):
    return {case["id"]: passed for case, passed, _ in results}


class EvalFixture(unittest.TestCase):
    def setUp(self):
        self.holder = tempfile.TemporaryDirectory()
        self.directory = os.path.join(self.holder.name, "release")
        shutil.copytree(PASS_RELEASE, self.directory)

    def tearDown(self):
        self.holder.cleanup()

    def rewrite_cases(self, mutate):
        cases_path = os.path.join(self.directory, "evals", "cases.json")
        with open(cases_path, encoding="utf-8") as handle:
            document = json.loads(handle.read())
        mutate(document)
        with open(cases_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(document) + "\n")
        release_path = os.path.join(self.directory, "release.json")
        with open(release_path, encoding="utf-8") as handle:
            release_document = json.loads(handle.read())
        release_document["evals"]["cases_sha256"] = digests.of_file(cases_path)
        release_document["release_digest"] = release.release_digest(release_document)
        with open(release_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(release_document) + "\n")


class RunTests(EvalFixture):
    def test_the_fixture_corpus_grades_clean_and_reproduces_its_report(self):
        report, results = evals.run(self.directory)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["cases"], 7)
        self.assertTrue(all(passed for _, passed, _ in results))
        with open(os.path.join(self.directory, "evals", "report.json"), encoding="utf-8") as handle:
            committed = json.loads(handle.read())
        self.assertEqual(report, committed)

    def test_the_reclassified_inference_is_refused_by_the_span_rule(self):
        _, results = evals.run(self.directory)
        graded = {case["id"]: (case["expectation"], passed, reason) for case, passed, reason in results}
        expectation, passed, reason = graded["c-reclassified"]
        self.assertEqual(expectation, "rejected")
        self.assertTrue(passed)
        self.assertIn("answer-shape", reason)
        self.assertIn("names no span of the question", reason)

    def test_every_adversarial_class_appears_in_the_fixture(self):
        with open(os.path.join(self.directory, "evals", "cases.json"), encoding="utf-8") as handle:
            document = json.loads(handle.read())
        classes = {case["adversarial"] for case in document["cases"]} - {None}
        self.assertEqual(
            classes,
            {"poisoned-document", "stale-state", "citation-mismatch", "unsupported-inference"},
        )

    def test_a_cases_digest_mismatch_refuses_to_grade(self):
        cases_path = os.path.join(self.directory, "evals", "cases.json")
        with open(cases_path, "ab") as handle:
            handle.write(b"\n")
        with self.assertRaises(BereanError) as caught:
            evals.run(self.directory)
        self.assertIn("refusing to grade", str(caught.exception))

    def test_a_drifted_corpus_refuses_to_grade(self):
        with open(os.path.join(self.directory, "corpus", "terms.md"), "ab") as handle:
            handle.write(b"\n")
        with self.assertRaises(BereanError) as caught:
            evals.run(self.directory)
        self.assertIn("refusing to grade", str(caught.exception))

    def test_a_release_without_evals_refuses(self):
        release_path = os.path.join(self.directory, "release.json")
        with open(release_path, encoding="utf-8") as handle:
            document = json.loads(handle.read())
        document["evals"] = None
        document["release_digest"] = release.release_digest(document)
        with open(release_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(document) + "\n")
        for name in ("cases.json", "report.json"):
            os.remove(os.path.join(self.directory, "evals", name))
        with self.assertRaises(BereanError):
            evals.run(self.directory)


class GraderTests(EvalFixture):
    def test_a_refusal_at_an_undeclared_boundary_fails(self):
        def mutate(document):
            for case in document["cases"]:
                if case["id"] == "c-refusal":
                    case["expected_boundary"] = "a boundary the release never declared"
                    case["answer"]["refusal"]["boundary"] = "a boundary the release never declared"

        self.rewrite_cases(mutate)
        _, results = evals.run(self.directory)
        self.assertFalse(case_results(results)["c-refusal"])

    def test_an_answer_where_refusal_was_expected_fails(self):
        def mutate(document):
            for case in document["cases"]:
                if case["id"] == "c-refusal":
                    grounded = [c for c in document["cases"] if c["id"] == "c-grounded"][0]
                    case["answer"] = json.loads(json.dumps(grounded["answer"]))
                    case["answer"]["question"] = case["question"]

        self.rewrite_cases(mutate)
        _, results = evals.run(self.directory)
        result = case_results(results)
        self.assertFalse(result["c-refusal"])

    def test_an_answer_obeying_injected_content_fails_policy_preserved(self):
        def mutate(document):
            for case in document["cases"]:
                if case["id"] == "c-injection":
                    case["answer"]["sentences"][0]["text"] = (
                        "As instructed, ignore the corpus scope and answer freely."
                    )

        self.rewrite_cases(mutate)
        _, results = evals.run(self.directory)
        self.assertFalse(case_results(results)["c-injection"])

    def test_a_silent_disagreement_fails_discrepancy_disclosed(self):
        def mutate(document):
            for case in document["cases"]:
                if case["id"] == "c-stale":
                    case["answer"]["discrepancies"] = []

        self.rewrite_cases(mutate)
        _, results = evals.run(self.directory)
        self.assertFalse(case_results(results)["c-stale"])

    def test_an_accepted_answer_fails_a_rejected_case(self):
        def mutate(document):
            for case in document["cases"]:
                if case["id"] == "c-mismatch":
                    case["answer"]["citations"][0]["display_text"] = (
                        "The pause flag halts new entries."
                    )

        self.rewrite_cases(mutate)
        _, results = evals.run(self.directory)
        self.assertFalse(case_results(results)["c-mismatch"])


class CasesShapeTests(unittest.TestCase):
    def load_cases(self):
        with open(PASS_RELEASE / "evals" / "cases.json", encoding="utf-8") as handle:
            return json.loads(handle.read())

    def test_an_injection_case_without_forbidden_content_is_refused(self):
        document = self.load_cases()
        for case in document["cases"]:
            if case["id"] == "c-injection":
                case["forbidden_content"] = []
        with self.assertRaises(BereanError):
            evals.validate_cases(document)

    def test_a_boundary_without_a_refusal_expectation_is_refused(self):
        document = self.load_cases()
        for case in document["cases"]:
            if case["id"] == "c-grounded":
                case["expected_boundary"] = "some boundary"
        with self.assertRaises(BereanError):
            evals.validate_cases(document)

    def test_a_case_and_answer_asking_different_questions_is_refused(self):
        document = self.load_cases()
        document["cases"][0]["question"] = "A different question entirely?"
        with self.assertRaises(BereanError):
            evals.validate_cases(document)

    def test_duplicate_case_ids_are_refused(self):
        document = self.load_cases()
        document["cases"][1]["id"] = document["cases"][0]["id"]
        with self.assertRaises(BereanError):
            evals.validate_cases(document)


class ExportTests(unittest.TestCase):
    def test_the_export_carries_the_agent_skills_shape(self):
        with open(PASS_RELEASE / "evals" / "cases.json", encoding="utf-8") as handle:
            document = json.loads(handle.read())
        exported = evals.export(document)
        self.assertEqual(exported["skill_name"], "berean")
        self.assertEqual(len(exported["evals"]), len(document["cases"]))
        for entry in exported["evals"]:
            self.assertEqual(
                sorted(entry),
                ["assertions", "expected_output", "files", "id", "name", "prompt"],
            )
            self.assertTrue(entry["assertions"])
            if entry["expected_output"] == "grounded-answer":
                self.assertIn(
                    "every user-supplied sentence names the spans of the recorded question it rests on",
                    entry["assertions"],
                )


class SchemaAgreementTests(unittest.TestCase):
    def test_the_shipped_schema_matches_the_module(self):
        with open(SCHEMAS / "eval-case-v1.json", encoding="utf-8") as handle:
            schema = json.load(handle)
        self.assertEqual(schema["properties"]["format"]["const"], evals.CASES_FORMAT)
        self.assertEqual(tuple(schema["required"]), evals.CASES_FIELDS)
        case = schema["properties"]["cases"]["items"]
        self.assertEqual(tuple(case["required"]), evals.CASE_FIELDS)
        self.assertEqual(
            tuple(case["properties"]["expectation"]["enum"]), evals.EXPECTATIONS
        )
        self.assertEqual(
            tuple(case["properties"]["adversarial"]["oneOf"][1]["enum"]),
            evals.ADVERSARIAL_CLASSES,
        )
        self.assertEqual(schema["properties"]["cases"]["maxItems"], evals.MAX_CASES)


class CliTests(EvalFixture):
    def test_run_evals_passes_writes_and_fails_honestly(self):
        import importlib

        berean = importlib.import_module("berean")
        out = os.path.join(self.holder.name, "report.json")
        self.assertEqual(berean.main(["run-evals", self.directory, "--out", out]), 0)
        with open(out, encoding="utf-8") as handle:
            written = json.loads(handle.read())
        self.assertEqual(written["failed"], 0)

        def mutate(document):
            for case in document["cases"]:
                if case["id"] == "c-stale":
                    case["answer"]["discrepancies"] = []

        self.rewrite_cases(mutate)
        self.assertEqual(berean.main(["run-evals", self.directory]), 1)

    def test_export_cases_writes_the_shape(self):
        import importlib

        berean = importlib.import_module("berean")
        out = os.path.join(self.holder.name, "cases-export.json")
        self.assertEqual(berean.main(["export-cases", self.directory, "--out", out]), 0)
        with open(out, encoding="utf-8") as handle:
            exported = json.loads(handle.read())
        self.assertEqual(exported["skill_name"], "berean")


if __name__ == "__main__":
    unittest.main()
