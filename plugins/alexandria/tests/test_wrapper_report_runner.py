"""The #2092 Step reporter and the public run record under `docs/kickoff/2092/`.

`WrapperReportRunnerTests` drives `wrapper_reports.execute_report` in process
over constructed specimen classes. They are attached to this module only for
the length of one case, so suite discovery never runs them.
`RunRecordBundleTests` holds the committed copies to the receipted digests.
"""

import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from tests import emit_wrapper_report, wrapper_reports


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
BUNDLE = REPO_ROOT / "docs" / "kickoff" / "2092"
REPORT = ".hexaemeron/steps/1/focused.json"
MODULE = "test_wrapper_report_runner"
# Elenchus's `unittest-json-v1` key set; any other key fails its parser.
REPORT_KEYS = {
    "schema", "complete", "testsRun", "failures", "errors", "skipped",
    "expectedFailures", "unexpectedSuccesses",
}
# SHA-256 of each receipted artefact, from the run's study and runbook receipts
# and the design record those receipts bind.
RECEIPTED = {
    "study.md": "35ee6b0f2816d49d4cf2fd775c413ba47d0f76054c169e423ee5d4d1056c5e88",
    "runbook.md": "406f7b923eb18806ad1bf277d4bcc84de220a3dfc303fd5aca1566eada54307a",
    "design-evidence.json": "fef4c019110a7146d94eff005b4d20cac8a39caa1d31d3fa3b036e60fe6a8f25",
    "design/model.json": "6489b55dd369cc03856731ff109a6b63348a66e2a223415370182676c995b624",
    "design/build_design_evidence.py": "0b816392edbab5c854ab167ca43d8f236554988ffa8dc666ae7dde2014a8eca7",
    "design/conformance.py": "1bfa66b88f72f281a765dea250ca1caa37981f091e7a05f28520269dd3ca1fed",
}
RAN = []


def specimens():
    """Fresh constructed classes, one per outcome the reporter must keep apart."""

    class Passing(unittest.TestCase):
        def test_passes(self):
            RAN.append("Passing")

    class Failing(unittest.TestCase):
        def test_fails(self):
            RAN.append("Failing")
            self.fail("constructed failure")

    class Erroring(unittest.TestCase):
        def test_errors(self):
            RAN.append("Erroring")
            raise RuntimeError("constructed error")

    class Skipping(unittest.TestCase):
        def test_skips(self):
            RAN.append("Skipping")
            self.skipTest("constructed skip")

    class Unselected(unittest.TestCase):
        def test_is_never_selected(self):
            RAN.append("Unselected")

    return {cls.__name__: cls for cls in (Passing, Failing, Erroring, Skipping, Unselected)}


class WrapperReportRunnerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        module = importlib.import_module(wrapper_reports.PACKAGE + "." + MODULE)
        for name, cls in specimens().items():
            patcher = mock.patch.object(module, name, cls, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)
        RAN.clear()
        self.environ = {}

    def run_step(self, *classes, argv=None, retained=None):
        """Run the reporter in process; return its exit status and report, or None."""
        cases = tuple((MODULE, name) for name in classes)
        patches = [mock.patch.object(wrapper_reports, "STEP_CASES", {1: cases})]
        if retained is not None:
            retained_cases = tuple((MODULE, name) for name in retained)
            patches.append(mock.patch.object(wrapper_reports, "RETAINED_CASES", retained_cases))
        arguments = argv or ["--step", "1", "--report", REPORT]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        try:
            with mock.patch("sys.stderr"):
                status = wrapper_reports.execute_report(
                    emit_wrapper_report.build_parser(), arguments, root=self.root,
                    environ=self.environ)
        except SystemExit as exc:
            status = exc.code
        path = self.root / REPORT
        report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        return status, report

    def test_the_parser_accepts_steps_one_to_four_and_refuses_any_other(self):
        parser = emit_wrapper_report.build_parser()
        for step in (1, 2, 3, 4):
            with self.subTest(step=step):
                args = parser.parse_args(["--step", str(step), "--report", REPORT])
                self.assertEqual((args.step, args.report, args.retained), (step, REPORT, False))
        for value in ("0", "5", "one"):
            with self.subTest(value=value), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit) as raised:
                    parser.parse_args(["--step", value, "--report", REPORT])
                self.assertEqual(raised.exception.code, 2)
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            parser.parse_args(["--step", "1"])

    def test_step_selection_runs_only_the_named_classes(self):
        status, report = self.run_step("Passing")
        self.assertEqual(status, 0)
        self.assertEqual(RAN, ["Passing"])
        self.assertEqual(set(report), REPORT_KEYS)
        self.assertEqual(report["schema"], "elenchus.unittest.v1")
        self.assertEqual((report["testsRun"], report["failures"], report["errors"]), (1, 0, 0))

    def test_step_one_names_only_its_own_classes(self):
        self.assertEqual(
            wrapper_reports.STEP_CASES[1],
            (("test_wildcat_wrappers", "LegacyIdentityTests"),
             ("test_wrapper_report_runner", "WrapperReportRunnerTests"),
             ("test_wrapper_report_runner", "RunRecordBundleTests")),
        )

    def test_a_failure_exits_one_and_an_error_exits_two_with_both_counted(self):
        status, report = self.run_step("Passing", "Failing")
        self.assertEqual(status, 1)
        self.assertEqual((report["testsRun"], report["failures"], report["errors"]), (2, 1, 0))
        (self.root / REPORT).unlink()
        status, report = self.run_step("Failing", "Erroring")
        self.assertEqual(status, 2)
        self.assertEqual((report["testsRun"], report["failures"], report["errors"]), (2, 1, 1))

    def test_a_missing_class_or_undeclared_step_refuses_without_a_report(self):
        self.assertEqual(self.run_step("Absent"), (2, None))
        with mock.patch.object(wrapper_reports, "STEP_CASES", {}), mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit) as raised:
                wrapper_reports.execute_report(
                    emit_wrapper_report.build_parser(), ["--step", "1", "--report", REPORT],
                    root=self.root, environ=self.environ)
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse((self.root / ".hexaemeron").exists())

    def test_a_report_path_that_exists_refuses_and_is_left_unchanged(self):
        path = self.root / REPORT
        path.parent.mkdir(parents=True)
        path.write_bytes(b'{"earlier": true}\n')
        status, _report = self.run_step("Passing")
        self.assertEqual(status, 2)
        self.assertEqual(path.read_bytes(), b'{"earlier": true}\n')
        self.assertEqual(RAN, [])

    def test_a_symlinked_parent_refuses_and_writes_nothing_through_it(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        (self.root / ".hexaemeron").symlink_to(elsewhere, target_is_directory=True)
        self.assertEqual(self.run_step("Passing"), (2, None))
        self.assertEqual(list(elsewhere.iterdir()), [])
        self.assertEqual(RAN, [])

    def test_a_report_outside_the_two_evidence_directories_refuses(self):
        for report in ("focused.json", "docs/focused.json", ".hexaemeron/focused.txt",
                       ".hexaemeron/../focused.json"):
            with self.subTest(report=report):
                status, _ = self.run_step("Passing", argv=["--step", "1", "--report", report])
                self.assertEqual(status, 2)
        self.assertEqual(RAN, [])

    def test_retained_without_both_staging_variables_exits_two_and_writes_no_report(self):
        argv = ["--step", "4", "--retained", "--report", REPORT]
        for present in ((), wrapper_reports.STAGING_VARIABLES[:1], wrapper_reports.STAGING_VARIABLES[1:]):
            with self.subTest(present=present):
                self.environ = {name: "/constructed/staging" for name in present}
                self.assertEqual(self.run_step(argv=argv, retained=("Passing",)), (2, None))
        self.assertEqual(RAN, [])

    def test_a_skipped_retained_test_exits_non_zero(self):
        self.environ = {name: "/constructed/staging" for name in wrapper_reports.STAGING_VARIABLES}
        argv = ["--step", "4", "--retained", "--report", REPORT]
        status, report = self.run_step(argv=argv, retained=("Passing", "Skipping"))
        self.assertEqual(status, 1)
        self.assertEqual((report["testsRun"], report["skipped"], report["failures"]), (2, 1, 0))
        self.assertEqual(RAN, ["Passing", "Skipping"])

    def test_the_registered_main_delegates_an_unstaged_retained_run_to_its_refusal(self):
        previous = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        with mock.patch.dict(sys.modules, {"wrapper_reports": wrapper_reports}), \
                mock.patch.dict(os.environ), mock.patch("sys.stderr") as stderr:
            for name in wrapper_reports.STAGING_VARIABLES:
                os.environ.pop(name, None)
            with self.assertRaises(SystemExit) as raised:
                emit_wrapper_report.main(["--step", "4", "--retained", "--report", REPORT])
        self.assertEqual(raised.exception.code, 2)
        written = "".join(call.args[0] for call in stderr.write.call_args_list)
        self.assertIn("ALEXANDRIA_WILDCAT_V1_STAGING", written)
        self.assertFalse((self.root / ".hexaemeron").exists())


class RunRecordBundleTests(unittest.TestCase):
    def digest(self, relative):
        return hashlib.sha256((BUNDLE / relative).read_bytes()).hexdigest()

    def test_the_receipted_artefacts_are_copied_byte_for_byte(self):
        for relative, sha256 in RECEIPTED.items():
            with self.subTest(relative=relative):
                self.assertEqual(self.digest(relative), sha256)
        runbook = (BUNDLE / "runbook.md").read_text(encoding="utf-8")
        self.assertIn("SHA-256 `" + RECEIPTED["study.md"] + "`", runbook)
        self.assertIn("sha256 | " + RECEIPTED["design-evidence.json"], runbook)

    def test_every_selection_report_matches_the_design_record(self):
        record = json.loads((BUNDLE / "design-evidence.json").read_text(encoding="utf-8"))
        declared = {result["report"]["path"]: result["report"]["sha256"]
                    for result in record["results"] if isinstance(result.get("report"), dict)}
        self.assertEqual(len(declared), 24)
        selection = BUNDLE / "design" / "reports" / "selection"
        self.assertEqual(
            sorted("design/reports/selection/" + path.name for path in selection.iterdir()),
            sorted(declared),
        )
        for relative, sha256 in declared.items():
            with self.subTest(relative=relative):
                self.assertEqual(self.digest(relative), sha256)

    def test_the_readme_states_what_step_one_does_not_implement(self):
        readme = (BUNDLE / "README.md").read_text(encoding="utf-8")
        self.assertIn("wildcat_v2_wrappers", readme)
        self.assertIn("emit_wrapper_report.py", readme)


if __name__ == "__main__":
    unittest.main()
