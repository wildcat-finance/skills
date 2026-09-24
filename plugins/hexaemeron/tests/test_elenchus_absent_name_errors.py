"""An error on a name the fix introduces no longer hides a guard (skills#1576)."""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "elenchus" / "scripts"
EMITTER = SCRIPTS / "unittest_report_v2.py"

spec = importlib.util.spec_from_file_location(
    "elenchus_absent_name", SCRIPTS / "elenchus.py"
)
elenchus = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = elenchus
spec.loader.exec_module(elenchus)

REPORT_FILE = ".elenchus/report"

BASE_FEATURE = (
    "# provenance is recorded by the caller\n"
    "def check(value):\n    return 0\n\n"
    "def config():\n    return {}\n"
)

FIXED_FEATURE = (
    "# provenance is recorded by the caller\n"
    "def check(value):\n    return value\n\n"
    "def window():\n    return 1\n\n"
    "def config():\n    return {'filing_window': 1, 'provenance': 'fix'}\n"
)

GUARD_TEST = (
    "import unittest\nimport feature\n\n"
    "class T(unittest.TestCase):\n"
    "    def test_refusal(self):\n        self.assertEqual(feature.check(1), 1)\n\n"
    "    def test_window(self):\n        self.assertEqual(feature.window(), 1)\n\n"
    "    def test_filing_window(self):\n"
    "        self.assertEqual(feature.config()['filing_window'], 1)\n\n"
    "    def test_provenance(self):\n"
    "        self.assertEqual(feature.config()['provenance'], 'fix')\n"
)


def unittest_v2(errors, failures=1, details=None, **extra):
    payload = {
        "schema": "elenchus.unittest.v2",
        "complete": True,
        "testsRun": 4,
        "failures": failures,
        "errors": errors,
        "skipped": 0,
        "expectedFailures": 0,
        "unexpectedSuccesses": 0,
        "errorDetails": details if details is not None else [
            {"test": f"t.T.test_{index}", "module": "test_feature.py",
             "exception": "KeyError", "name": "filing_window"}
            for index in range(errors)
        ],
    }
    payload.update(extra)
    return json.dumps(payload).encode("utf-8")


class Fixture:
    def __init__(self, base_files):
        self.path = Path(tempfile.mkdtemp(prefix="elenchus-absent-name-"))
        self.run("init", "--quiet", "-b", "main")
        self.run("config", "--local", "commit.gpgsign", "false")
        self.run("config", "user.email", "fixture@example.org")
        self.run("config", "user.name", "Fixture")
        self.base = self.commit("base", base_files)

    def run(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True, text=True, check=True,
        ).stdout

    def commit(self, message, files):
        for name, body in files.items():
            target = self.path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        self.run("add", "-A")
        self.run("-c", "commit.gpgsign=false", "commit", "--quiet", "-m", message)
        return self.run("rev-parse", "HEAD").strip()

    def child(self, message, files):
        self.run("checkout", "--quiet", "--detach", self.base)
        return self.commit(message, files)


class ReportShape(unittest.TestCase):
    def test_v2_report_carries_one_detail_per_error(self):
        report = elenchus.parse_unittest_v2_report(unittest_v2(2))
        self.assertEqual(2, report.errors)
        self.assertEqual(
            ("KeyError", "filing_window"),
            (report.error_details[0].exception, report.error_details[0].name),
        )

    def test_malformed_v2_reports_are_refused(self):
        cases = {
            "count": unittest_v2(2, details=[]),
            "extra key": unittest_v2(1, details=[{
                "test": "t", "module": None, "exception": "KeyError",
                "name": None, "extra": 1,
            }]),
            "unsafe module": unittest_v2(1, details=[{
                "test": "t", "module": "../escape.py", "exception": "KeyError",
                "name": "x",
            }]),
            "exception": unittest_v2(1, details=[{
                "test": "t", "module": None, "exception": "not an id",
                "name": "x",
            }]),
            "name type": unittest_v2(1, details=[{
                "test": "t", "module": None, "exception": "KeyError", "name": 3,
            }]),
            "schema": unittest_v2(0, schema="elenchus.unittest.v1"),
        }
        for label, raw in cases.items():
            with self.subTest(label), self.assertRaises(elenchus.ReportError):
                elenchus.parse_unittest_v2_report(raw)

    def test_v1_stays_closed_and_parent_guard_keeps_its_formats(self):
        raw = json.loads(unittest_v2(0))
        raw["schema"] = "elenchus.unittest.v1"
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(json.dumps(raw).encode("utf-8"))
        self.assertNotIn("unittest-json-v2", elenchus.REPORT_FORMATS)
        self.assertIn("unittest-json-v2", elenchus.CHECK_REPORT_FORMATS)


class Classification(unittest.TestCase):
    tests = ("test_feature.py",)

    def report(self, failures=1, **detail):
        row = {"test": "t.T.test_x", "module": "test_feature.py",
               "exception": "AttributeError", "name": "window"}
        row.update(detail)
        return elenchus.parse_unittest_v2_report(
            unittest_v2(1, failures=failures, details=[row])
        )

    def test_attributed_errors_beside_an_assertion_are_guarded(self):
        status, detail = elenchus.classify(
            self.report(), frozenset({"window"}), self.tests
        )
        self.assertEqual("guarded", status)
        self.assertIn("reads a name the fix introduces", detail)

    def test_each_unattributed_shape_stays_inconclusive(self):
        cases = {
            "no fix evidence": (self.report(), frozenset()),
            "name not introduced": (self.report(), frozenset({"other"})),
            "unchanged module": (self.report(module="test_other.py"),
                                 frozenset({"window"})),
            "no module": (self.report(module=None), frozenset({"window"})),
            "infrastructure type": (self.report(exception="ImportError"),
                                    frozenset({"window"})),
            "no name": (self.report(name=None), frozenset({"window"})),
            "errors alone": (self.report(failures=0), frozenset({"window"})),
        }
        for label, (report, introduced) in cases.items():
            with self.subTest(label):
                self.assertEqual(
                    "inconclusive",
                    elenchus.classify(report, introduced, self.tests)[0],
                )

    def test_counters_without_details_keep_the_old_verdict(self):
        report = elenchus.RunnerReport(True, 4, 1, 1, 0)
        self.assertEqual(
            "inconclusive",
            elenchus.classify(report, frozenset({"window"}), self.tests)[0],
        )


class CommitCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Fixture({"feature.py": BASE_FEATURE})
        f = cls.fixture
        cls.fix = f.child("fix", {
            "feature.py": FIXED_FEATURE, "test_feature.py": GUARD_TEST,
        })
        cls.test_only_name = f.child("test-only name", {
            "feature.py": FIXED_FEATURE.replace("'filing_window': 1, ", ""),
            "test_feature.py": GUARD_TEST,
        })
        cls.errors_only = f.child("errors only", {
            "feature.py": FIXED_FEATURE,
            "test_feature.py": GUARD_TEST.replace(
                "feature.check(1), 1", "feature.check(1), feature.check(1)"
            ),
        })
        cls.command = [
            sys.executable, str(EMITTER), "--report", "{report}", "test_feature.py",
        ]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.fixture.path, ignore_errors=True)

    def outcome(self, ref):
        return elenchus.check(
            self.fixture.path, ref, self.command, timeout=120,
            report_format="unittest-json-v2", report_file=REPORT_FILE,
        )

    def test_errors_on_names_the_fix_introduces_are_guarded(self):
        result = self.outcome(self.fix)
        self.assertEqual("guarded", result["status"], result)
        self.assertEqual(
            (1, 3), (result["report"]["assertion_failures"], result["report"]["errors"])
        )
        rows = result["report"]["error_details"]
        self.assertEqual(
            {("AttributeError", "window"), ("KeyError", "filing_window"),
             ("KeyError", "provenance")},
            {(row["exception"], row["name"]) for row in rows},
        )
        self.assertTrue(all(row["reads_introduced_name"] for row in rows))

    def test_a_name_only_the_test_uses_stays_inconclusive(self):
        result = self.outcome(self.test_only_name)
        self.assertEqual("inconclusive", result["status"], result)
        unattributed = [
            row["name"] for row in result["report"]["error_details"]
            if not row["reads_introduced_name"]
        ]
        self.assertEqual(["filing_window"], unattributed)

    def test_introduced_name_errors_without_an_assertion_stay_inconclusive(self):
        result = self.outcome(self.errors_only)
        self.assertEqual("inconclusive", result["status"], result)
        self.assertEqual(0, result["report"]["assertion_failures"])

    def test_a_v1_report_of_the_same_fix_keeps_the_old_verdict(self):
        emitter = (
            "import json, sys, unittest\nsys.path.insert(0, '.')\nimport test_feature\n"
            "r = unittest.TextTestRunner().run(\n"
            "    unittest.defaultTestLoader.loadTestsFromModule(test_feature))\n"
            "open(sys.argv[1], 'w').write(json.dumps({\n"
            "    'schema': 'elenchus.unittest.v1', 'complete': True,\n"
            "    'testsRun': r.testsRun, 'failures': len(r.failures),\n"
            "    'errors': len(r.errors), 'skipped': 0,\n"
            "    'expectedFailures': 0, 'unexpectedSuccesses': 0}))\n"
        )
        with tempfile.TemporaryDirectory() as scratch:
            script = Path(scratch) / "emit_v1.py"
            script.write_text(emitter, encoding="utf-8")
            result = elenchus.check(
                self.fixture.path, self.fix,
                [sys.executable, str(script), "{report}"], timeout=120,
                report_format="unittest-json-v1", report_file=REPORT_FILE,
            )
        self.assertEqual("inconclusive", result["status"], result)
        self.assertNotIn("error_details", result["report"])


if __name__ == "__main__":
    unittest.main()
