"""Guard pending production conformance and the accepted selection evidence for
the venue-agnostic interval capture design record (eight resolvers, two venues,
three rejected candidates)."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1] / "docs/wildcat-interval"
SPEC = importlib.util.spec_from_file_location("wildcat_conformance", ROOT / "design/conformance.py")
conformance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(conformance)

REJECTED_CANDIDATES = (
    "registry-format-dispatch",
    "venue-parameter-table",
    "separate-wildcat-collector",
)


class Loader:
    errors = []

    def __init__(self, suite):
        self.suite = suite

    def loadTestsFromNames(self, names):
        return self.suite


class MissingLoader(unittest.TestLoader):
    def loadTestsFromNames(self, names):
        return super().loadTestsFromNames(["tests.missing_wildcat_specimen.test"] * len(names))


class WildcatConformanceHarnessTests(unittest.TestCase):
    """While venue code is absent, all eight resolvers must refuse."""

    def test_eight_resolver_names_are_declared(self):
        self.assertEqual(
            set(conformance.CASES),
            {
                "compound-path-still-builds",
                "wildcat-v2-plan-builds-and-checks",
                "wildcat-v1-plan-builds-and-checks",
                "shared-subject-attributed-per-venue",
                "v1-source-gap-declared",
                "constructed-staging-declared-in-coverage",
                "undeclared-venue-refuses",
                "component-budget-respected",
            },
        )

    def test_missing_venue_code_refuses_each_criterion_with_named_counts(self):
        for name in conformance.CASES:
            with self.subTest(criterion=name):
                passed, observed, detail = conformance.execute(name, MissingLoader())
                self.assertFalse(passed)
                self.assertEqual(observed["criterion"], name)
                self.assertGreater(observed["loader_errors"], 0)
                self.assertTrue(observed["unresolved"])
                self.assertIsNotNone(observed["reason"])
                self.assertIn("missing_wildcat_specimen", detail)

    def test_zero_tests_cannot_pass(self):
        for name in conformance.CASES:
            passed, observed, _ = conformance.execute(name, Loader(unittest.TestSuite()))
            self.assertFalse(passed)
            self.assertEqual(observed["tests_run"], 0)
            self.assertEqual(observed["reason"], "no-assertions-executed")

    def test_failed_assertions_cannot_pass(self):
        class Failed(unittest.TestCase):
            def runTest(self):
                self.assertEqual("old", "new")

        name = "undeclared-venue-refuses"
        suite = unittest.TestSuite(Failed() for _ in conformance.CASES[name])
        passed, observed, _ = conformance.execute(name, Loader(suite))
        self.assertFalse(passed)
        self.assertEqual(observed["failures"], len(conformance.CASES[name]))
        self.assertEqual(observed["reason"], "assertions-failed")

    def test_skipped_assertions_cannot_pass(self):
        class Skipped(unittest.TestCase):
            @unittest.skip("specimen")
            def runTest(self):
                self.fail("unreachable")

        name = "undeclared-venue-refuses"
        suite = unittest.TestSuite(Skipped() for _ in conformance.CASES[name])
        passed, observed, _ = conformance.execute(name, Loader(suite))
        self.assertFalse(passed)
        self.assertEqual(observed["skipped"], len(conformance.CASES[name]))
        self.assertEqual(observed["reason"], "assertions-skipped")

    def test_refusal_emits_no_report_for_every_resolver_name(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                with mock.patch.object(conformance.unittest, "TestLoader", MissingLoader):
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        for name in conformance.CASES:
                            self.assertEqual(conformance.main([name]), 1)
            self.assertFalse((Path(directory) / ".hexaemeron/reports").exists())

    def test_report_follows_complete_successful_execution(self):
        executed = []

        class Passed(unittest.TestCase):
            def runTest(self):
                self.assertEqual(2 + 2, 4)
                executed.append("executed")

        name = "component-budget-respected"
        suite = unittest.TestSuite(Passed() for _ in conformance.CASES[name])
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                with mock.patch.object(conformance.unittest, "TestLoader", return_value=Loader(suite)):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(conformance.main([name]), 0)
            path = Path(directory) / f".hexaemeron/reports/conformance/{conformance.CANDIDATE}-{name}.json"
            report = json.loads(path.read_text())
            self.assertEqual(len(executed), len(conformance.CASES[name]))
            self.assertIs(report["value"], True)
            self.assertEqual(report["criterion"], name)
            self.assertEqual(report["candidate"], conformance.CANDIDATE)

    def test_rejected_candidate_refuses_by_name_before_loading_anything(self):
        for candidate in REJECTED_CANDIDATES:
            with self.subTest(candidate=candidate):
                blocked_loader = mock.Mock(side_effect=AssertionError("loaded before the candidate check"))
                with mock.patch.object(conformance.unittest, "TestLoader", blocked_loader):
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaises(SystemExit):
                            conformance.main(["compound-path-still-builds", "--candidate", candidate])
                    blocked_loader.assert_not_called()
                    self.assertIn(candidate, stderr.getvalue())

    def test_every_resolver_name_refuses_the_same_rejected_candidate(self):
        for name in conformance.CASES:
            with self.subTest(criterion=name):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        conformance.main([name, "--candidate", "registry-format-dispatch"])
                self.assertIn("registry-format-dispatch", stderr.getvalue())

    def test_rejected_candidate_refusal_cannot_write_a_report(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        conformance.main(["compound-path-still-builds", "--candidate", "venue-parameter-table"])
            self.assertFalse((Path(directory) / ".hexaemeron/reports").exists())

    def test_selection_reports_recompute_byte_identically(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            shutil.copytree(ROOT, dest, dirs_exist_ok=True)
            spec = importlib.util.spec_from_file_location(
                "wildcat_model", dest / "design/build_design_evidence.py"
            )
            model = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(model)
            with contextlib.redirect_stdout(io.StringIO()):
                model.main()
            paths = ["design-evidence.json", "design/model-observations.json"]
            paths += [str(p.relative_to(ROOT)) for p in (ROOT / "reports/selection").glob("*.json")]
            self.assertEqual(len(paths), 26)
            for relative in paths:
                with self.subTest(path=relative):
                    self.assertEqual((ROOT / relative).read_bytes(), (dest / relative).read_bytes())
            record = json.loads((dest / "design-evidence.json").read_text())
            self.assertEqual(len(record["results"]), 56)
            self.assertEqual(sum(row["state"] == "pending" for row in record["results"]), 32)
            self.assertEqual(sum(row["state"] == "pass" for row in record["results"]), 20)
            self.assertEqual(sum(row["state"] == "fail" for row in record["results"]), 4)

    def test_rerun_executes_fresh_and_accepts_only_identical_report(self):
        name = "component-budget-respected"
        executed = []

        class Passed(unittest.TestCase):
            def runTest(self):
                self.assertEqual(2 + 2, 4)
                executed.append("executed")

        def loader():
            return Loader(unittest.TestSuite(Passed() for _ in conformance.CASES[name]))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(conformance.Path, "cwd", return_value=root), mock.patch.object(
                conformance.unittest, "TestLoader", side_effect=loader
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(conformance.main([name]), 0)
                    path = root / f".hexaemeron/reports/conformance/{conformance.CANDIDATE}-{name}.json"
                    original = path.read_bytes()
                    # A second, identical rerun is a byte-for-byte no-op success.
                    self.assertEqual(conformance.main([name]), 0)
                    self.assertEqual(path.read_bytes(), original)
                    self.assertEqual(len(executed), 4)
                    # A drifted report is refused rather than overwritten.
                    drifted = original.replace(b'"value": true', b'"value":false')
                    self.assertNotEqual(drifted, original)
                    path.write_bytes(drifted)
                    with self.assertRaises(SystemExit):
                        conformance.main([name])
                    self.assertEqual(len(executed), 6)
                    self.assertEqual(path.read_bytes(), drifted)


if __name__ == "__main__":
    unittest.main()
