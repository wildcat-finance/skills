"""Check the skills#1944 design home and its refusing conformance resolver."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "docs/deferred-runner-binding"
# The current receipted bytes: the study and runbook as amended on 2026-09-27,
# the runbook's second amendment of that date included, and the design record
# locked before the runbook.
RECEIPTED = {
    "study.md": "31fb433b8b45040727d86e3db758d4cc0e165c948a297f93c6f1acd0aa442aee",
    "runbook.md": "3867af5da8d690e53216d0f29a9a49faca4ca9286457ba0df318b7834749db9a",
    "design-evidence.json": "2ee92a4119378e5cfd8e7a6455ceebe850cd222f821fd6c75fd98d194c3aba22",
}
# Observed when Step 1 copied .hexaemeron/design/probe.py; no receipt binds it.
PROBE_SHA256 = "21ee9bc04878a651734f58891e08930d8a34bbdbd654a663b31c0e278ae22368"
DRAFT = "docs/decisions/drafts/bind-a-step-created-runner-at-its-push.md"
HANDLER_STEPS = {
    "validator-deferred-contract": 2,
    "released-adapter-replay": 2,
    "successor-replay-milliseconds": 2,
    "controller-binding-custody": 3,
    "joined-demonstration": 4,
}
IMPLEMENTED = {name for name, step in HANDLER_STEPS.items() if step <= 3}
PENDING = {name: step for name, step in HANDLER_STEPS.items() if name not in IMPLEMENTED}


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


PROOF = load(PACKAGE + "/proof.py", "deferred_runner_proof")
DESIGN = load("plugins/hexaemeron/skills/protasis/scripts/design_evidence.py",
              "deferred_runner_design_checker")
BRIDGE = load("plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py",
              "deferred_runner_bridge_checker")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_report(criterion, candidate="creating-step-binding"):
    return ".hexaemeron/reports/" + candidate + "-" + criterion + ".json"


def snapshot(root):
    """Every entry below root with its type and, for a file, its bytes."""
    entries = {}
    for directory, names, files in os.walk(root, followlinks=False):
        for name in names + files:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                entries[relative] = ("link", os.readlink(path))
            elif path.is_dir():
                entries[relative] = ("directory", None)
            else:
                entries[relative] = ("file", path.read_bytes())
    return entries


class PublishedDesignHomeTests(unittest.TestCase):
    def test_copies_equal_their_receipted_bytes(self):
        for name, expected in RECEIPTED.items():
            with self.subTest(name=name):
                self.assertEqual(digest(ROOT / PACKAGE / name), expected)
        self.assertEqual(digest(ROOT / PACKAGE / "probe.py"), PROBE_SHA256)
        self.assertEqual(PROOF.RECORD_SHA256, RECEIPTED["design-evidence.json"])

    def test_each_selection_report_equals_its_recorded_digest(self):
        record = json.loads((ROOT / PACKAGE / "design-evidence.json").read_bytes())
        resolved = [row["report"] for row in record["results"] if isinstance(row["report"], dict)]
        self.assertEqual(len(resolved), 28)
        for reference in resolved:
            with self.subTest(path=reference["path"]):
                self.assertEqual(digest(ROOT / PACKAGE / reference["path"]), reference["sha256"])
        committed = {path.name for path in (ROOT / PACKAGE / "reports").iterdir()}
        self.assertEqual(committed, {Path(reference["path"]).name for reference in resolved})

    def test_committed_record_locks_the_selected_design(self):
        findings, record, _ = DESIGN.evaluate(ROOT / PACKAGE / "design-evidence.json", "design-lock")
        self.assertEqual(findings, [])
        self.assertEqual(record["selection"]["candidate"], PROOF.SELECTED)
        self.assertEqual(tuple(item["id"] for item in record["candidates"]), PROOF.CANDIDATES)

    def test_resolver_table_matches_every_pending_cell_of_the_selection(self):
        record = json.loads((ROOT / PACKAGE / "design-evidence.json").read_bytes())
        conformance = {item["id"] for item in record["criteria"] if item["stage"] == "conformance"}
        self.assertEqual(set(PROOF.CRITERIA), conformance)
        self.assertEqual(PROOF.CRITERIA, HANDLER_STEPS)
        cells = {row["criterion"]: row for row in record["results"]
                 if row["candidate"] == PROOF.SELECTED and row["state"] == "pending"}
        self.assertEqual(set(cells), conformance)
        for criterion, row in cells.items():
            with self.subTest(criterion=criterion):
                self.assertEqual(row["resolver"], PROOF.resolver(PROOF.SELECTED, criterion))
                self.assertEqual(".hexaemeron/" + row["report"], cell_report(criterion))

    def test_decision_draft_resolves_through_the_study_bridge(self):
        study = PACKAGE + "/study.md"
        self.assertEqual(BRIDGE.check_design_bridge(study, PACKAGE + "/design-evidence.json", ROOT), [])
        bridge, _, error = BRIDGE._design_bridge_block(
            (ROOT / study).read_text(encoding="utf-8").splitlines())
        self.assertIsNone(error)
        self.assertEqual(bridge["decision"], PROOF.SELECTED)
        self.assertEqual(bridge["record"], DRAFT)
        text = (ROOT / DRAFT).read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Decision: "))
        self.assertIn("`creating-step-binding`", text)
        _, home, error = BRIDGE._read_stable_adr(ROOT, "adr/" + Path(DRAFT).stem)
        self.assertIsNone(error)
        self.assertEqual(home.as_posix(), DRAFT)


class ScratchRoot(unittest.TestCase):
    """A disposable root holding only the resolver and the design record."""

    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix="deferred-runner-scaffold-")
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name).resolve()
        for name in ("proof.py", "design-evidence.json"):
            destination = self.root / PACKAGE / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / PACKAGE / name, destination)

    def call(self, *argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = PROOF.main(list(argv), root=self.root)
        return code, json.loads(stdout.getvalue())

    def resolve(self, criterion, candidate="creating-step-binding", report=None):
        return self.call("--candidate", candidate, "--criterion", criterion,
                         "--report", cell_report(criterion, candidate) if report is None else report)


class RefusingResolverTests(ScratchRoot):
    def test_each_exact_resolver_refuses_by_name_and_writes_nothing(self):
        before = snapshot(self.root)
        self.assertEqual(set(PROOF.HANDLERS), IMPLEMENTED)
        for criterion, step in PENDING.items():
            with self.subTest(criterion=criterion):
                completed = subprocess.run(
                    [sys.executable, "-I", "-B", PACKAGE + "/proof.py", "--candidate",
                     "creating-step-binding", "--criterion", criterion, "--report",
                     cell_report(criterion)],
                    cwd=self.root, capture_output=True, text=True, timeout=60, check=False)
                self.assertEqual(completed.returncode, 1, completed.stderr)
                self.assertEqual(json.loads(completed.stdout), {
                    "event": "deferred-runner-proof-refused",
                    "reason": "operation-not-implemented:" + criterion + ":step-" + str(step),
                    "candidate": "creating-step-binding", "criterion": criterion})
                self.assertEqual(snapshot(self.root), before)
        self.assertFalse((self.root / ".hexaemeron").exists())

    def test_refusal_adds_nothing_to_an_existing_report_directory(self):
        (self.root / ".hexaemeron/reports").mkdir(parents=True)
        before = snapshot(self.root)
        for criterion in PENDING:
            with self.subTest(criterion=criterion):
                code, event = self.resolve(criterion)
                self.assertEqual(code, 1)
                self.assertTrue(event["reason"].startswith("operation-not-implemented:" + criterion))
        self.assertEqual(snapshot(self.root), before)

    def test_existing_report_or_link_is_refused_and_preserved(self):
        target = self.root / "keep.json"
        target.write_bytes(b"keep\n")
        for criterion in HANDLER_STEPS:
            with self.subTest(criterion=criterion):
                output = self.root / cell_report(criterion)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"previous report\n")
                before = snapshot(self.root)
                self.assertEqual(self.resolve(criterion)[1]["reason"], "report-already-exists")
                self.assertEqual(snapshot(self.root), before)
                output.unlink()
                output.symlink_to(target)
                self.assertEqual(self.resolve(criterion)[1]["reason"], "report-already-exists")
                self.assertEqual(target.read_bytes(), b"keep\n")

    def test_linked_report_directory_is_refused(self):
        (self.root / "elsewhere").mkdir()
        (self.root / ".hexaemeron").mkdir()
        (self.root / ".hexaemeron/reports").symlink_to(self.root / "elsewhere")
        before = snapshot(self.root)
        code, event = self.resolve("joined-demonstration")
        self.assertEqual((code, event["reason"]), (1, "report-directory-unsafe"))
        self.assertEqual(snapshot(self.root), before)

    def test_arguments_outside_the_closed_set_refuse(self):
        base = ["--candidate", "creating-step-binding", "--criterion", "joined-demonstration",
                "--report", cell_report("joined-demonstration")]
        for argv in ([], base[:4], base + ["--extra", "x"], base[:2] + base[:2] + base[4:],
                     ["--cand"] + base[1:], ["--candidate=" + base[1]] + base[1:],
                     ["--help"] + base[1:]):
            with self.subTest(argv=argv):
                stdout, stderr = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code = PROOF.main(argv, root=self.root)
                self.assertEqual(code, 2)
                self.assertEqual(json.loads(stdout.getvalue())["reason"], "argument-not-closed")
                self.assertIn("usage:", stderr.getvalue())
        cases = [
            (self.resolve("joined-demonstration", candidate="no-such-candidate",
                          report=cell_report("joined-demonstration")), "unknown-candidate"),
            (self.resolve("replay-milliseconds"), "unknown-criterion"),
            (self.resolve("joined-demonstration", report=cell_report("released-adapter-replay")),
             "report-not-cell-path"),
            (self.resolve("joined-demonstration", report="/tmp/report.json"), "report-not-cell-path"),
        ]
        for candidate in PROOF.CANDIDATES[1:]:
            cases.append((self.resolve("joined-demonstration", candidate=candidate),
                          "candidate-not-selected"))
        for (code, event), reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual((code, event["reason"]), (1, reason))
        unknown = cases[0][0][1]
        self.assertEqual((unknown["candidate"], unknown["criterion"]), (None, "joined-demonstration"))
        self.assertFalse((self.root / ".hexaemeron").exists())


class ReportCustodyTests(ScratchRoot):
    """Later handlers inherit this custody; a test double stands in for one."""

    def test_handler_value_becomes_one_exclusive_admissible_report(self):
        criterion = "validator-deferred-contract"
        with mock.patch.dict(PROOF.HANDLERS, {criterion: lambda root: True}):
            code, report = self.resolve(criterion)
            output = self.root / cell_report(criterion)
            written = output.read_bytes()
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(written), report)
            self.assertEqual(report, {
                "schema": "protasis-design-report/v1", "candidate": "creating-step-binding",
                "criterion": criterion, "value": True, "unit": "boolean",
                "command": PROOF.resolver("creating-step-binding", criterion), "exit": 0})
            self.assertEqual(self.resolve(criterion)[1]["reason"], "report-already-exists")
            self.assertEqual(output.read_bytes(), written)
        # Lay the record out as a run holds it and ask Protasis to admit the report.
        shutil.copyfile(ROOT / PACKAGE / "design-evidence.json",
                        self.root / ".hexaemeron/design-evidence.json")
        for selection in (ROOT / PACKAGE / "reports").iterdir():
            shutil.copyfile(selection, self.root / ".hexaemeron/reports" / selection.name)
        findings, _, consumed = DESIGN.evaluate(self.root / ".hexaemeron/design-evidence.json",
                                                "step:3")
        self.assertIn(criterion, {row["criterion"] for row in consumed})
        self.assertEqual({finding.code for finding in findings}, {"D008"})
        self.assertEqual({name for name in HANDLER_STEPS
                          if any("/" + name + " " in finding.message for finding in findings)},
                         {"released-adapter-replay", "successor-replay-milliseconds"})

    def test_report_appearing_after_the_check_is_not_replaced(self):
        criterion = "joined-demonstration"
        output = self.root / cell_report(criterion)

        def racing(root):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"concurrent\n")
            return True

        with mock.patch.dict(PROOF.HANDLERS, {criterion: racing}):
            self.assertEqual(self.resolve(criterion)[1]["reason"], "report-already-exists")
        self.assertEqual(output.read_bytes(), b"concurrent\n")

    def test_value_outside_the_unit_or_changed_record_writes_nothing(self):
        calls = []
        for criterion, value in (("successor-replay-milliseconds", True),
                                 ("successor-replay-milliseconds", -1),
                                 ("controller-binding-custody", 1)):
            with self.subTest(criterion=criterion, value=value):
                with mock.patch.dict(PROOF.HANDLERS, {criterion: lambda root, v=value: v}):
                    self.assertEqual(self.resolve(criterion)[1]["reason"],
                                     "handler-value-outside-unit")
        record = self.root / PACKAGE / "design-evidence.json"
        original = record.read_bytes()
        record.write_bytes(original.replace(b'"threshold": 1000', b'"threshold": 9000', 1))
        self.assertNotEqual(record.read_bytes(), original)
        with mock.patch.dict(PROOF.HANDLERS, {"released-adapter-replay": calls.append}):
            self.assertEqual(self.resolve("released-adapter-replay")[1]["reason"],
                             "design-record-digest-mismatch")
        self.assertEqual(calls, [])
        self.assertFalse((self.root / ".hexaemeron").exists())


class StepTwoHandlerTests(unittest.TestCase):
    """The step:3 handlers, checked without the Git history hosted CI omits."""

    def scratch(self):
        directory = tempfile.TemporaryDirectory(prefix="deferred-runner-handlers-")
        self.addCleanup(directory.cleanup)
        return Path(directory.name).resolve()

    def contract_module(self, root, *, drop=None, extra=""):
        classes = {}
        for name in PROOF.CONTRACT_TESTS:
            if name != drop:
                owner, method = name.split(".")
                classes.setdefault(owner, []).append(method)
        text = "import unittest\n\n"
        for owner, methods in classes.items():
            text += "class " + owner + "(unittest.TestCase):\n"
            text += "".join("    def " + method + "(self):\n        self.assertTrue(True)\n"
                            for method in methods) + "\n"
        path = root / PROOF.VALIDATOR_TESTS
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + extra)
        return path

    def test_validator_needs_every_test_and_each_contract_test_to_pass(self):
        root = self.scratch()
        self.contract_module(root)
        self.assertIs(PROOF.validator_deferred_contract(root), True)
        failing = ("class Other(unittest.TestCase):\n"
                   "    def test_other(self):\n        self.fail('observed')\n")
        skipped = ("class Other(unittest.TestCase):\n"
                   "    def test_other(self):\n        self.skipTest('observed')\n")
        for kwargs in ({"extra": failing}, {"extra": skipped},
                       {"drop": PROOF.CONTRACT_TESTS[0]}):
            with self.subTest(kwargs=kwargs):
                self.contract_module(root, **kwargs)
                self.assertIs(PROOF.validator_deferred_contract(root), False)
        path = self.contract_module(root)
        path.rename(root / "moved.py")
        path.symlink_to(root / "moved.py")
        with self.assertRaisesRegex(PROOF.Refusal, "^source-unavailable$"):
            PROOF.validator_deferred_contract(root)

    def test_released_adapter_is_read_by_fixed_argv_and_checked_by_digest(self):
        commit, expected = PROOF.RELEASED_ADAPTERS[0]
        argv = ["git", "-C", str(ROOT), "cat-file", "blob", commit + ":" + PROOF.ADAPTER]
        outcomes = (
            (subprocess.CompletedProcess(argv, 128, b"", None), "released-adapter-unavailable"),
            (OSError("no git"), "released-adapter-unavailable"),
            (subprocess.TimeoutExpired(argv, 60), "released-adapter-unavailable"),
            (subprocess.CompletedProcess(argv, 0, b"other bytes", None),
             "released-adapter-digest-mismatch"),
        )
        for outcome, reason in outcomes:
            with self.subTest(reason=reason, outcome=type(outcome).__name__):
                with mock.patch.object(PROOF.subprocess, "run", side_effect=[outcome]) as run:
                    with self.assertRaisesRegex(PROOF.Refusal, "^" + reason + "$"):
                        PROOF.released_adapter(ROOT, self.scratch(), commit, expected)
                self.assertEqual(run.call_args.args, (argv,))
                self.assertNotIn("shell", run.call_args.kwargs)
                self.assertEqual(run.call_args.kwargs["timeout"], PROOF.GIT_SECONDS)

    def test_replay_handler_passes_only_when_every_observation_holds(self):
        current = (ROOT / PROOF.ADAPTER).read_bytes()
        # An extra invocation member stands in for a released adapter that disagrees.
        diverged = current.replace(b"'interface-valid'})", b"'interface-valid', 'extra': 1})")
        self.assertNotEqual(diverged, current)
        for source, expected in ((current, True), (diverged, False)):
            with self.subTest(expected=expected):
                released = ((PROOF.STARTING_COMMIT, hashlib.sha256(source).hexdigest()),)
                with mock.patch.object(PROOF, "RELEASED_ADAPTERS", released), \
                        mock.patch.object(PROOF, "git_blob", return_value=source):
                    self.assertIs(PROOF.released_adapter_replay(ROOT), expected)

    def test_timing_handler_measures_the_successor_on_the_committed_runbook(self):
        value = PROOF.successor_replay_milliseconds(ROOT)
        self.assertIs(type(value), int)
        self.assertGreater(value, 0)
        with mock.patch.object(PROOF, "read_tree_file", return_value=b"# No command\n"):
            with self.assertRaisesRegex(PROOF.Refusal, "^timed-validation-refused$"):
                PROOF.successor_replay_milliseconds(ROOT)

    def test_timing_handler_reports_the_median_of_five_samples_rounded_up(self):
        # S2-R1-02. Samples of 5, 3.000001, 1, 9 and 2 ms: the median rounds up
        # to 4, where a mean or the first sample gives 5, the unsorted middle or
        # least sample 1, and plain rounding 3.
        ticks = []
        for start, sample in zip(range(0, 50_000_000, 10_000_000),
                                 (5_000_000, 3_000_001, 1_000_000, 9_000_000, 2_000_000)):
            ticks += [start, start + sample]
        with mock.patch.object(PROOF.time, "perf_counter_ns", side_effect=ticks):
            self.assertEqual(PROOF.successor_replay_milliseconds(ROOT), 4)


class StepThreeHandlerTests(unittest.TestCase):
    """The step:4 handler's pass rule, checked on a stand-in controller module."""

    def custody_module(self, *, drop=None, extra=""):
        directory = tempfile.TemporaryDirectory(prefix="deferred-runner-custody-")
        self.addCleanup(directory.cleanup)
        root = Path(directory.name).resolve()
        classes = {}
        for name in PROOF.CUSTODY_TESTS:
            if name != drop:
                owner, method = name.split(".")
                classes.setdefault(owner, []).append(method)
        # The real module imports its sibling harness from its own directory.
        text = "import unittest\n\nimport custody_sibling\n\n"
        for owner, methods in classes.items():
            text += "class " + owner + "(unittest.TestCase):\n"
            text += "".join("    def " + method + "(self):\n"
                            "        self.assertTrue(custody_sibling.READY)\n"
                            for method in methods) + "\n"
        path = root / PROOF.CONTROLLER_TESTS
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + extra)
        path.with_name("custody_sibling.py").write_text("READY = True\n")
        return root, path

    def test_custody_needs_every_test_and_each_custody_test_to_pass(self):
        before = list(sys.path)
        try:
            root, _ = self.custody_module()
            self.assertIs(PROOF.controller_binding_custody(root), True)
            self.assertEqual(sys.path, before)
            failing = ("class Other(unittest.TestCase):\n"
                       "    def test_other(self):\n        self.fail('observed')\n")
            skipped = ("class Other(unittest.TestCase):\n"
                       "    def test_other(self):\n        self.skipTest('observed')\n")
            for kwargs in ({"extra": failing}, {"extra": skipped},
                           {"drop": PROOF.CUSTODY_TESTS[0]}):
                with self.subTest(kwargs=kwargs):
                    root, _ = self.custody_module(**kwargs)
                    self.assertIs(PROOF.controller_binding_custody(root), False)
                    self.assertEqual(sys.path, before)
            root, path = self.custody_module()
            path.rename(root / "moved.py")
            path.symlink_to(root / "moved.py")
            with self.assertRaisesRegex(PROOF.Refusal, "^source-unavailable$"):
                PROOF.controller_binding_custody(root)
            self.assertEqual(sys.path, before)
        finally:
            sys.modules.pop("custody_sibling", None)

    def test_custody_tests_name_tests_the_controller_module_defines(self):
        text = (ROOT / PROOF.CONTROLLER_TESTS).read_text(encoding="utf-8")
        for name in PROOF.CUSTODY_TESTS:
            owner, method = name.split(".")
            with self.subTest(name=name):
                self.assertIn("class " + owner + "(", text)
                self.assertIn("    def " + method + "(self", text)


if __name__ == "__main__":
    unittest.main()
