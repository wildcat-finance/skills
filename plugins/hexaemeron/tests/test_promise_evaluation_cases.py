import json
from pathlib import Path
import unittest


CASES = (
    Path(__file__).parent
    / "fixtures"
    / "promise-machine"
    / "evaluation-cases.json"
)
EXPECTED = {
    "hypomnema-record-placement",
    "kronos-fiat-dispatch",
    "vulgate-register-rewrite",
    "hexaemeron-fizz-harness-campaign",
    "hexaemeron-fizz-convert-properties",
    "hexaemeron-fizz-sync-drift",
    "hexaemeron-x-ray-preaudit",
    "hexaemeron-solidity-audit-report",
}


class PromptAndVendoredCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        document = json.loads(CASES.read_text(encoding="utf-8"))
        if document["schema"] != "promise-machine-evaluation-cases/v1":
            raise AssertionError("unsupported evaluation-case schema")
        cls.cases = document["cases"]
        if set(cls.cases) != EXPECTED:
            raise AssertionError("labelled-case promise set does not match the held set")

    def assert_category(self, code, disposition):
        for promise_id, record in self.cases.items():
            with self.subTest(promise_id=promise_id, code=code):
                self.assertEqual(set(record), {"request", "P", "M", "S", "O", "R"})
                self.assertTrue(record["request"].strip())
                case = record[code]
                self.assertEqual(case["disposition"], disposition)
                self.assertTrue(case["scenario"].strip())
                self.assertTrue(case["boundary"].strip())

    def test_labelled_positive_cases(self):
        self.assert_category("P", "accept")

    def test_labelled_missing_evidence_cases(self):
        self.assert_category("M", "refuse")

    def test_labelled_subject_mismatch_cases(self):
        self.assert_category("S", "refuse")

    def test_labelled_overclaim_cases(self):
        self.assert_category("O", "refuse")

    def test_labelled_recovery_cases(self):
        self.assert_category("R", "recover")


if __name__ == "__main__":
    unittest.main()
