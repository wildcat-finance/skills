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


class DigestRebindEmitterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parents[1] / 'skills/elenchus/scripts/fixed_and_guarded.py'
        spec = importlib.util.spec_from_file_location('rebind_record_emitter', path)
        cls.emitter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.emitter)

    def result(self):
        return {
            'ref': 'a' * 40, 'status': 'guarded',
            'tests': ['tests/pins.json', 'test_behavior.py'], 'detail': 'qualified guard',
            'report': {'complete': True, 'executed': 1, 'assertion_failures': 1,
                       'errors': 0, 'skipped': 0},
            'digest_rebinds': [{'register': 'tests/pins.json', 'path': 'source.py',
                               'parent_sha256': 'a' * 64, 'rebound_sha256': 'b' * 64,
                               'target_overlaid': False}],
        }

    def test_emitter_accepts_the_optional_diagnostic(self):
        self.assertEqual([], self.emitter.result_findings(self.result()))

    def test_emitter_refuses_malformed_or_inconsistent_diagnostics(self):
        for key, value in [('target_overlaid', 0), ('target_overlaid', True),
                           ('path', '../source.py'), ('parent_sha256', 'not-a-digest'),
                           ('register', 'other.json'), ('unexpected', 'field')]:
            with self.subTest(key=key, value=value):
                result = self.result()
                result['digest_rebinds'][0][key] = value
                findings = self.emitter.result_findings(result)
                self.assertTrue(any(f.code == 'F006' for f in findings))
