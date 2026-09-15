"""Digest rebind context survives the commit-based parent overlay."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location(
    "elenchus_rebind_test_helpers", Path(__file__).with_name("test_elenchus_checker.py")
)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
RunnerCase = helpers.RunnerCase
Fixture = helpers.Fixture
UNITTEST_EMITTER = helpers.UNITTEST_EMITTER
elenchus = helpers.elenchus
REPORT_FILE = helpers.REPORT_FILE


class DigestRebindReports(RunnerCase):
    @classmethod
    def setUpClass(cls):
        cls.command = [sys.executable, "emit_unittest.py", "{report}"]
        cls.report_format = "unittest-json-v1"
        cls.fixture = Fixture({"emit_unittest.py": UNITTEST_EMITTER})

    def rebind(self, path, behaviour=False):
        old = "VALUE = 1\n"
        new = "VALUE = 2\n" if behaviour else "VALUE = 1  # wording only\n"
        register = "tests/pins.json"
        def pin(raw):
            return json.dumps({"checker": {"path": path,
                "sha256": hashlib.sha256(raw.encode()).hexdigest()}})
        test = (
            "import hashlib, json, unittest\nfrom pathlib import Path\n"
            "class T(unittest.TestCase):\n"
            "    def test_digest(self):\n"
            "        pin = json.loads(Path('tests/pins.json').read_text())['checker']\n"
            "        self.assertEqual(hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest(), pin['sha256'])\n"
        )
        f = self.fixture
        f.run("checkout", "--quiet", "--detach", f.base)
        f.commit("before rebind", {path: old, register: pin(old)})
        files = {path: new, register: pin(new), "test_digest.py": test}
        if behaviour:
            files["test_behaviour.py"] = (
                "import unittest\nfrom source import VALUE\nclass T(unittest.TestCase):\n"
                "    def test_regression(self):\n        self.assertEqual(VALUE, 2)\n"
            )
        return f.commit("rebind", files)

    def test_non_test_rebind_records_the_manufactured_digest_mismatch(self):
        result = self.outcome(self.rebind("source.py"))
        self.assertEqual("guarded", result["status"])
        row, = result["digest_rebinds"]
        self.assertEqual("source.py", row["path"])
        self.assertEqual("tests/pins.json", row["register"])
        self.assertFalse(row["target_overlaid"])
        self.assertIn("digest rebind", result["detail"])

    def test_test_rebind_records_that_the_bound_bytes_were_overlaid(self):
        result = self.outcome(self.rebind("tests/data.py"))
        self.assertEqual("passed", result["status"])
        row, = result["digest_rebinds"]
        self.assertTrue(row["target_overlaid"])

    def test_real_assertion_remains_guarded_beside_a_rebind(self):
        result = self.outcome(self.rebind("source.py", behaviour=True))
        self.assertEqual("guarded", result["status"])
        self.assertEqual(2, result["report"]["assertion_failures"])
        self.assertEqual(1, len(result["digest_rebinds"]))

    def test_unbound_digest_text_is_not_reported_as_a_verified_rebind(self):
        ref = self.rebind("source.py")
        ref = self.fixture.commit("wrong pin", {"tests/pins.json": json.dumps({
            "checker": {"path": "source.py", "sha256": "0" * 64}})})
        self.assertEqual([], self.outcome(ref)["digest_rebinds"])

    def test_digest_inspection_refuses_an_exhausted_byte_budget(self):
        ref = self.rebind("source.py")
        with mock.patch.object(elenchus, "MAX_GUARD_BLOBS_BYTES", 1):
            result = self.outcome(ref)
        self.assertEqual("inconclusive", result["status"])
        self.assertIn("byte limit", result["detail"])
