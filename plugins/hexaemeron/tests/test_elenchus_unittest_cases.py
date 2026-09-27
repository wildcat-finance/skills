"""Keep native subtest events while classifying complete test methods."""

import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "elenchus" / "scripts"
SPEC = importlib.util.spec_from_file_location("elenchus_cases", SCRIPTS / "elenchus.py")
elenchus = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = elenchus
SPEC.loader.exec_module(elenchus)


class CaseReportTests(unittest.TestCase):
    def emitter(self):
        path = SCRIPTS / "unittest_report_v3.py"
        self.assertTrue(path.is_file(), "a subtest-aware reporter must exist")
        spec = importlib.util.spec_from_file_location("unittest_cases", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def run_case(self, case):
        emitter = self.emitter()
        result = unittest.TextTestRunner(
            stream=io.StringIO(), resultclass=emitter.CaseResult
        ).run(unittest.defaultTestLoader.loadTestsFromTestCase(case))
        return emitter.payload(result)

    def parse(self, value):
        self.assertIn("unittest-json-v3", elenchus.CHECK_REPORT_FORMATS)
        return elenchus.parse_unittest_v3_report(json.dumps(value).encode())

    def test_multiple_subtest_failures_remain_a_guard(self):
        class TwoFailures(unittest.TestCase):
            def test_vectors(self):
                for value in (1, 2):
                    with self.subTest(value=value):
                        self.assertEqual(value, 0)

        value = self.run_case(TwoFailures)
        self.assertEqual((value["testsRun"], value["failures"]), (1, 2))
        parsed = self.parse(value)
        self.assertEqual((parsed.executed, parsed.assertion_failures), (1, 1))
        self.assertEqual(elenchus.classify(parsed)[0], "guarded")

    def test_error_after_subtest_failure_stays_inconclusive(self):
        class Mixed(unittest.TestCase):
            def test_vectors(self):
                with self.subTest(kind="assertion"):
                    self.fail("guard")
                with self.subTest(kind="infrastructure"):
                    raise PermissionError("fixture")

        value = self.run_case(Mixed)
        self.assertEqual((value["failures"], value["errors"]), (1, 1))
        parsed = self.parse(value)
        self.assertEqual((parsed.assertion_failures, parsed.errors), (0, 1))
        self.assertEqual(elenchus.classify(parsed)[0], "inconclusive")

    def test_later_assertions_and_skips_cannot_hide_an_error(self):
        class Mixed(unittest.TestCase):
            def test_vectors(self):
                with self.subTest(kind="infrastructure"):
                    raise PermissionError("fixture")
                with self.subTest(kind="assertion"):
                    self.fail("guard")
                self.skipTest("remaining vectors unavailable")

        value = self.run_case(Mixed)
        self.assertEqual((value["failures"], value["errors"], value["skipped"]), (1, 1, 1))
        parsed = self.parse(value)
        self.assertEqual((parsed.executed, parsed.assertion_failures, parsed.errors), (1, 0, 1))
        self.assertEqual(elenchus.classify(parsed)[0], "inconclusive")

    def test_class_fixture_errors_cannot_be_mistaken_for_assertion_guards(self):
        class BrokenFixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise PermissionError("fixture")

            def test_guard(self):
                self.fail("never reached")

        value = self.run_case(BrokenFixture)
        self.assertEqual((value["testsRun"], value["errors"], value["cases"]), (0, 1, []))
        with self.assertRaises(elenchus.ReportError):
            self.parse(value)

    def test_subtest_skips_do_not_subtract_executed_methods(self):
        class SkippedVectors(unittest.TestCase):
            def test_vectors(self):
                for value in (1, 2):
                    with self.subTest(value=value):
                        self.skipTest("vector unavailable")

        value = self.run_case(SkippedVectors)
        self.assertEqual((value["testsRun"], value["skipped"]), (1, 2))
        parsed = self.parse(value)
        self.assertEqual((parsed.executed, parsed.skipped), (1, 0))

    def test_method_skips_and_expected_failures_are_not_execution(self):
        class Skips(unittest.TestCase):
            @unittest.skip("unavailable")
            def test_skip(self):
                self.fail()

            @unittest.expectedFailure
            def test_expected(self):
                self.fail()

        parsed = self.parse(self.run_case(Skips))
        self.assertEqual((parsed.executed, parsed.skipped), (0, 2))
        self.assertEqual(elenchus.classify(parsed)[0], "inconclusive")

    def test_unexpected_success_is_an_error(self):
        class Unexpected(unittest.TestCase):
            @unittest.expectedFailure
            def test_unexpected(self):
                pass

        parsed = self.parse(self.run_case(Unexpected))
        self.assertEqual((parsed.executed, parsed.errors), (1, 1))
        self.assertEqual(elenchus.classify(parsed)[0], "inconclusive")

    def test_an_empty_suite_is_inconclusive(self):
        class Empty(unittest.TestCase):
            pass

        self.assertEqual(elenchus.classify(self.parse(self.run_case(Empty)))[0], "inconclusive")

    def test_repeated_method_invocations_each_count_once(self):
        class Repeated(unittest.TestCase):
            def test_guard(self):
                self.fail("guard")

        emitter = self.emitter()
        result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=emitter.CaseResult).run(
            unittest.TestSuite([Repeated("test_guard"), Repeated("test_guard")])
        )
        parsed = self.parse(emitter.payload(result))
        self.assertEqual((parsed.executed, parsed.assertion_failures), (2, 2))

    def test_counter_and_case_contradictions_refuse(self):
        class Passing(unittest.TestCase):
            def test_ok(self):
                pass

        value = self.run_case(Passing)
        mutations = (
            lambda data: data.update(testsRun=2),
            lambda data: data.update(failures=1),
            lambda data: data["cases"][0].update(outcome="failed"),
            lambda data: data["cases"][0].update(outcome="error"),
            lambda data: data["cases"][0].update(errors=True),
            lambda data: data["cases"][0].update(test=""),
            lambda data: data["cases"][0].update(extra=0),
            lambda data: data.update(extra=0),
            lambda data: data.update(complete=False),
            lambda data: data.update(cases=[]),
            lambda data: data.update(cases=[data["cases"][0]] * 10_001, testsRun=10_001),
            lambda data: data["cases"][0].update(test="x" * 10_000),
            lambda data: data["cases"][0].update(outcome=[]),
        )
        for mutate in mutations:
            candidate = copy.deepcopy(value)
            mutate(candidate)
            with self.subTest(mutation=mutate), self.assertRaises(elenchus.ReportError):
                self.parse(candidate)

    def test_legacy_counts_and_caller_bound_formats_stay_closed(self):
        self.assertNotIn("unittest-json-v3", elenchus.REPORT_FORMATS)
        value = {"schema": "elenchus.unittest.v1", "complete": True,
                 "testsRun": 1, "failures": 2, "errors": 0, "skipped": 0,
                 "expectedFailures": 0, "unexpectedSuccesses": 0}
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(json.dumps(value).encode())


class ParentCheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="elenchus-subtests-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "--quiet", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.org")
        self.git("config", "commit.gpgsign", "false")
        (self.root / "feature.py").write_text("def value(n):\n    return 0\n")
        self.commit()
        (self.root / "feature.py").write_text("def value(n):\n    return n\n")
        self.guard = (
            "import unittest\nfrom feature import value\n"
            "class Guard(unittest.TestCase):\n"
            "    def test_vectors(self):\n"
            "        for n in (1, 2):\n"
            "            with self.subTest(n=n):\n"
            "                self.assertEqual(value(n), n)\n"
        )

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args],
                              capture_output=True, text=True, check=True).stdout.strip()

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", "fixture")
        return self.git("rev-parse", "HEAD")

    def outcome(self, source):
        (self.root / "test_feature.py").write_text(source)
        ref = self.commit()
        before = (self.git("status", "--short"), self.git("worktree", "list", "--porcelain"))
        result = elenchus.check(
            self.root, ref,
            [sys.executable, str(SCRIPTS / "unittest_report_v3.py"),
             "--report", "{report}", "test_feature.py"],
            timeout=120, report_format="unittest-json-v3", report_file=".elenchus/report",
        )
        self.assertEqual(before, (self.git("status", "--short"), self.git("worktree", "list", "--porcelain")))
        return result

    def test_native_report_guards_parent_and_passes_on_fixed_tree(self):
        result = self.outcome(self.guard)
        self.assertEqual(result["status"], "guarded", result)
        self.assertEqual(result["report"]["count_unit"], "test-method")
        self.assertEqual(result["report"]["assertion_failures"], 1)
        self.assertEqual(result["report"]["native_counts"]["failures"], 2)
        report = self.root / "fixed-report.json"
        fixed = subprocess.run(
            [sys.executable, str(SCRIPTS / "unittest_report_v3.py"),
             "--report", str(report), "test_feature.py"],
            cwd=self.root, capture_output=True,
        )
        self.assertEqual(fixed.returncode, 0, fixed.stderr.decode())
        parsed = elenchus.parse_unittest_v3_report(report.read_bytes())
        self.assertEqual((parsed.executed, parsed.assertion_failures, parsed.errors), (1, 0, 0))

    def test_contained_runner_error_still_prevents_a_guard(self):
        result = self.outcome(self.guard + "        raise PermissionError('fixture')\n")
        self.assertEqual(result["status"], "inconclusive", result)
        self.assertEqual(result["report"]["native_counts"]["failures"], 2)
        self.assertEqual(result["report"]["errors"], 1)


if __name__ == "__main__":
    unittest.main()
