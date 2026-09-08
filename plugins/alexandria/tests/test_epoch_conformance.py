"""Guard pending production conformance and the accepted selection evidence."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1] / "docs/usdc-interval-epochs"
SPEC = importlib.util.spec_from_file_location("epoch_conformance", ROOT / "design/conformance.py")
conformance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(conformance)


class Loader:
    errors = []

    def __init__(self, suite):
        self.suite = suite

    def loadTestsFromNames(self, names):
        return self.suite


class MissingLoader(unittest.TestLoader):
    def loadTestsFromNames(self, names):
        return super().loadTestsFromNames(["tests.missing_epoch_specimen.test"] * len(names))


class EpochConformanceTests(unittest.TestCase):
    def test_missing_production_assertions_refuse_each_criterion(self):
        for name in conformance.CASES:
            with self.subTest(criterion=name):
                passed, result, detail = conformance.execute(name, MissingLoader())
                self.assertFalse(passed)
                self.assertGreater(result["errors"], 0)
                self.assertIn("missing_epoch_specimen", detail)

    def test_zero_tests_cannot_pass(self):
        for name in conformance.CASES:
            passed, result, _ = conformance.execute(name, Loader(unittest.TestSuite()))
            self.assertFalse(passed)
            self.assertEqual(result["tests_run"], 0)

    def test_skipped_assertions_cannot_pass(self):
        class Skipped(unittest.TestCase):
            @unittest.skip("specimen")
            def runTest(self):
                self.fail("unreachable")
        name = "resume-and-refusal"
        suite = unittest.TestSuite(Skipped() for _ in conformance.CASES[name])
        passed, result, _ = conformance.execute(name, Loader(suite))
        self.assertFalse(passed)
        self.assertEqual(result["skipped"], len(conformance.CASES[name]))

    def test_failed_assertions_cannot_pass(self):
        class Failed(unittest.TestCase):
            def runTest(self):
                self.assertEqual("old", "new")
        name = "resume-and-refusal"
        suite = unittest.TestSuite(Failed() for _ in conformance.CASES[name])
        passed, result, _ = conformance.execute(name, Loader(suite))
        self.assertFalse(passed)
        self.assertEqual(result["failures"], len(conformance.CASES[name]))

    def test_refusal_emits_no_report(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                with mock.patch.object(conformance.unittest, "TestLoader", MissingLoader):
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        for name in conformance.CASES:
                            self.assertEqual(conformance.main([name]), 1)
            self.assertFalse((Path(directory) / ".hexaemeron/reports").exists())

    def test_report_follows_complete_successful_execution(self):
        observed = []
        class Passed(unittest.TestCase):
            def runTest(self):
                self.assertEqual(2 + 2, 4)
                observed.append("executed")
        name = "resume-and-refusal"
        suite = unittest.TestSuite(Passed() for _ in conformance.CASES[name])
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                with mock.patch.object(conformance.unittest, "TestLoader", return_value=Loader(suite)):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(conformance.main([name]), 0)
            path = Path(directory) / ".hexaemeron/reports/conformance/position-boundary-resume-and-refusal.json"
            report = json.loads(path.read_text())
            self.assertEqual(len(observed), len(conformance.CASES[name]))
            self.assertIs(report["value"], True)
            self.assertEqual(report["criterion"], name)

    def test_selection_reports_recompute_byte_identically(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            shutil.copytree(ROOT, dest, dirs_exist_ok=True)
            spec = importlib.util.spec_from_file_location("epoch_model", dest / "design/build_design_evidence.py")
            model = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(model)
            with contextlib.redirect_stdout(io.StringIO()):
                model.main()
            paths = ["design-evidence.json", "design/model-observations.json"]
            paths += [str(p.relative_to(ROOT)) for p in (ROOT / "reports/selection").glob("*.json")]
            self.assertEqual(len(paths), 12)
            for relative in paths:
                with self.subTest(path=relative):
                    self.assertEqual((ROOT / relative).read_bytes(), (dest / relative).read_bytes())
            record = json.loads((dest / "design-evidence.json").read_text())
            self.assertEqual(sum(row["state"] == "pending" for row in record["results"]), 8)

    def test_rerun_executes_fresh_and_accepts_only_identical_report(self):
        name = 'resume-and-refusal'
        observed = []
        class Passed(unittest.TestCase):
            def runTest(self):
                self.assertEqual(2 + 2, 4)
                observed.append('executed')
        def loader():
            return Loader(unittest.TestSuite(Passed() for _ in conformance.CASES[name]))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(conformance.Path, 'cwd', return_value=root), mock.patch.object(conformance.unittest, 'TestLoader', side_effect=loader):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(conformance.main([name]), 0)
                    path = root / '.hexaemeron/reports/conformance/position-boundary-resume-and-refusal.json'
                    original = path.read_bytes()
                    self.assertEqual(conformance.main([name]), 0)
                    self.assertEqual(path.read_bytes(), original)
                    self.assertEqual(len(observed), 4)
                    drifted = original.replace(b'"value": true', b'"value":false')
                    path.write_bytes(drifted)
                    with self.assertRaises(SystemExit):
                        conformance.main([name])
                    self.assertEqual(len(observed), 6)
                    self.assertEqual(path.read_bytes(), drifted)
