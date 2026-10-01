"""Check the skills#1944 design home and its conformance resolver."""
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
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
    "runbook.md": "b671bccae0cac1b3f29073a45111ef2779688ae11ddd9ad8b3a18a3460a9a646",
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
# Step 4 added the last handler, so every criterion has one.
IMPLEMENTED = {name for name, step in HANDLER_STEPS.items() if step <= 4}


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


def cell_evidence(criterion, candidate="creating-step-binding"):
    return ".hexaemeron/reports/" + candidate + "-" + criterion + ".evidence.json"


def without_handler(criterion):
    """The handler table as it stood before the criterion's step added its handler."""
    return {name: handler for name, handler in PROOF.HANDLERS.items() if name != criterion}


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
    def test_every_criterion_has_its_handler(self):
        self.assertEqual(set(PROOF.HANDLERS), IMPLEMENTED)
        self.assertEqual(IMPLEMENTED, set(HANDLER_STEPS))

    def test_a_criterion_without_its_handler_refuses_by_name_and_writes_nothing(self):
        before = snapshot(self.root)
        for criterion, step in HANDLER_STEPS.items():
            with self.subTest(criterion=criterion), \
                    mock.patch.dict(PROOF.HANDLERS, without_handler(criterion), clear=True):
                self.assertEqual(self.resolve(criterion), (1, {
                    "event": "deferred-runner-proof-refused",
                    "reason": "operation-not-implemented:" + criterion + ":step-" + str(step),
                    "candidate": "creating-step-binding", "criterion": criterion}))
                self.assertEqual(snapshot(self.root), before)
        self.assertFalse((self.root / ".hexaemeron").exists())

    def test_script_entry_refuses_by_name_before_any_handler_runs(self):
        output = self.root / cell_report("joined-demonstration")
        output.parent.mkdir(parents=True)
        output.write_bytes(b"previous report\n")
        before = snapshot(self.root)
        completed = subprocess.run(
            [sys.executable, "-I", "-B", PACKAGE + "/proof.py", "--candidate",
             "creating-step-binding", "--criterion", "joined-demonstration", "--report",
             cell_report("joined-demonstration")],
            cwd=self.root, capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), {
            "event": "deferred-runner-proof-refused", "reason": "report-already-exists",
            "candidate": "creating-step-binding", "criterion": "joined-demonstration"})
        self.assertEqual(snapshot(self.root), before)

    def test_refusal_adds_nothing_to_an_existing_report_directory(self):
        (self.root / ".hexaemeron/reports").mkdir(parents=True)
        before = snapshot(self.root)
        for criterion in HANDLER_STEPS:
            with self.subTest(criterion=criterion), \
                    mock.patch.dict(PROOF.HANDLERS, without_handler(criterion), clear=True):
                code, event = self.resolve(criterion)
                self.assertEqual(code, 1)
                self.assertTrue(event["reason"].startswith("operation-not-implemented:" + criterion))
        self.assertEqual(snapshot(self.root), before)

    def test_existing_report_or_link_is_refused_and_preserved(self):
        target = self.root / "keep.json"
        target.write_bytes(b"keep\n")
        paths = [cell_report(criterion) for criterion in HANDLER_STEPS]
        paths.append(cell_evidence("joined-demonstration"))
        for path in paths:
            criterion = next(name for name in HANDLER_STEPS if "-" + name + "." in path)
            with self.subTest(path=path):
                output = self.root / path
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"previous report\n")
                before = snapshot(self.root)
                self.assertEqual(self.resolve(criterion)[1]["reason"], "report-already-exists")
                self.assertEqual(snapshot(self.root), before)
                output.unlink()
                output.symlink_to(target)
                self.assertEqual(self.resolve(criterion)[1]["reason"], "report-already-exists")
                self.assertEqual(target.read_bytes(), b"keep\n")
                output.unlink()

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
        for path in (cell_report(criterion), cell_evidence(criterion)):
            with self.subTest(path=path):
                output = self.root / path

                def racing(root):
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(b"concurrent\n")
                    return PROOF.Observed(True, {"value": True})

                with mock.patch.dict(PROOF.HANDLERS, {criterion: racing}):
                    self.assertEqual(self.resolve(criterion)[1]["reason"], "report-already-exists")
                # The concurrent entry stays and this call leaves nothing of its own.
                self.assertEqual(sorted(entry.name for entry in output.parent.iterdir()),
                                 [output.name])
                self.assertEqual(output.read_bytes(), b"concurrent\n")
                output.unlink()

    def test_evidenced_handler_must_return_its_matching_evidence(self):
        criterion = "joined-demonstration"
        for outcome, reason in ((True, "handler-evidence-missing"),
                                (PROOF.Observed(True, None), "handler-evidence-missing"),
                                (PROOF.Observed(True, {"value": False}), "handler-evidence-mismatch"),
                                (PROOF.Observed(1, {"value": 1}), "handler-value-outside-unit")):
            with self.subTest(reason=reason, outcome=outcome):
                with mock.patch.dict(PROOF.HANDLERS, {criterion: lambda root, o=outcome: o}):
                    self.assertEqual(self.resolve(criterion)[1]["reason"], reason)
        self.assertFalse((self.root / ".hexaemeron").exists())

    def test_evidence_names_the_report_it_precedes(self):
        criterion = "joined-demonstration"
        evidence = {"schema": PROOF.EVIDENCE_SCHEMA, "value": False}
        with mock.patch.dict(PROOF.HANDLERS,
                             {criterion: lambda root: PROOF.Observed(False, evidence)}):
            code, report = self.resolve(criterion)
        self.assertEqual((code, report["value"]), (0, False))
        written = (self.root / cell_report(criterion)).read_bytes()
        bound = json.loads((self.root / cell_evidence(criterion)).read_bytes())
        self.assertEqual(bound, {**evidence, "report": {
            "path": cell_report(criterion), "sha256": hashlib.sha256(written).hexdigest()}})

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
        # This handler test supplies both sources; hosted root checks use a
        # shallow checkout and do not carry the historical Git objects.
        current = (ROOT / PROOF.ADAPTER).read_bytes() + b'\n# recorded test adapter\n'
        previous_runner = (ROOT / PROOF.RUNNER).read_bytes()
        # An extra invocation member stands in for a released adapter that disagrees.
        diverged = current.replace(b"'interface-valid'})", b"'interface-valid', 'extra': 1})")
        self.assertNotEqual(diverged, current)
        for source, expected in ((current, True), (diverged, False)):
            with self.subTest(expected=expected):
                released = ((PROOF.STARTING_COMMIT, hashlib.sha256(source).hexdigest()),)
                def recorded_blob(_root, _commit, relative):
                    return source if relative == PROOF.ADAPTER else previous_runner
                original_load = PROOF.load_tree_module
                def loaded_module(root, relative, name):
                    module = original_load(root, relative, name)
                    if name == "deferred_runner_successor_replay":
                        runner, _, new_source, _, new_decl = module.RUNNER_SINGLE_PROCESS_TRANSITION
                        module.RUNNER_SINGLE_PROCESS_TRANSITION = (
                            runner, (new_source,), new_source, new_decl, new_decl,
                        )
                        module.RUNNER_SINGLE_PROCESS_ADAPTERS |= {
                            hashlib.sha256(source).hexdigest()
                        }
                    return module
                with mock.patch.object(PROOF, "RELEASED_ADAPTERS", released), \
                        mock.patch.object(PROOF, "git_blob", side_effect=recorded_blob), \
                        mock.patch.object(PROOF, "load_tree_module", side_effect=loaded_module), \
                        mock.patch.object(PROOF, "PREVIOUS_RUNNER_SHA256",
                                          hashlib.sha256(previous_runner).hexdigest()):
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


def set_status(side, entries):
    def change(observations):
        observations["receipt"][side]["status"] = {"entries": entries, "count": len(entries)}
    return change


def set_in(path, value):
    """Replace one observation, addressed by its keys and list indexes."""
    def change(observations):
        node = observations
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    return change


# Each check with observations that must make it, and only it, fail.
PERTURBATIONS = {
    "controller-bytes": [set_in(("controller", "sha256_after"), "0" * 64),
                         set_in(("controller", "driven"), None),
                         set_in(("controller", "driven"), "hexctl.py")],
    "adapter-bytes": [set_in(("adapter", "sha256_after"), "0" * 64),
                      set_in(("runbook", "adapter_sha256"), "0" * 64),
                      set_in(("binding", "adapter_sha256"), "0" * 64)],
    "runbook-refuses-present-runner": [
        set_in(("present-runner", "status"), {"entries": [], "count": 0}),
        set_in(("present-runner", "tokens"), []),
        set_in(("present-runner", "after", 0), "0" * 64)],
    "runbook-receipted-without-product-files": [
        set_status("before", ["?? src/extra.py"]), set_status("after", ["?? src/extra.py"]),
        set_in(("receipt", "before", "runner_present"), True)],
    "step-one-commands-deferred": [
        set_in(("runbook", "step_one", 1, "invocations", 0, "result"), "interface-valid"),
        set_in(("runbook", "step_one"), []),
        set_in(("runbook", "interface_rows"), []),
        set_in(("runbook", "file_sha256"), "0" * 64)],
    "status-awaiting-binding": [set_in(("status", "after-runbook", "status"), "current")],
    "runner-created-by-step-one": [
        set_in(("runner", "base_entry"), "100644 blob " + "a" * 40 + "\ttests/run_tests.py\0"),
        set_in(("runner", "added_by"), [])],
    "push-binds-runner": [
        set_in(("status", "after-push", "status"), "awaiting-binding"),
        set_in(("status", "before-push", "status"), "current"),
        set_in(("binding", "ledger_sha256"), []),
        set_in(("binding", "paths", 0, "blob"), "0" * 40),
        set_in(("binding", "results"), ["interface-deferred"])],
    "push-refuses-worktree-mismatch": [set_in(("push-mismatch", "after", 1), "0" * 64),
                                       set_in(("push-mismatch", "tokens"), [])],
    "later-edit-refuses-drift": [set_in(("drift", "verify", "tokens"), []),
                                 set_in(("drift", "implement", "returncode"), 0),
                                 set_in(("drift", "verify", "after", 0), "0" * 64),
                                 set_in(("drift", "status", "status"), "current")],
    "in-step-fix-without-amendment": [set_in(("amendments", "ledger_events"), 1),
                                      set_in(("amendments", "receipt"), 1),
                                      set_in(("status", "after-fix", "status"), "current"),
                                      set_in(("commits", "fixes_ref"), "0" * 40)],
    "fix-changes-runner-behaviour": [set_in(("runs", "created", "assertion_failures"), 0),
                                     set_in(("runs", "fixed", "parsed"), False)],
}


class JoinedDemonstrationTests(unittest.TestCase):
    """The step:integration handler, run once on this tree's controller."""

    POSITIVE = {"runbook-receipted-without-product-files", "step-one-commands-deferred",
                "status-awaiting-binding", "runner-created-by-step-one", "push-binds-runner",
                "in-step-fix-without-amendment", "fix-changes-runner-behaviour"}
    REFUSAL = {"runbook-refuses-present-runner", "push-refuses-worktree-mismatch",
               "later-edit-refuses-drift"}
    IDENTITY = {"controller-bytes", "adapter-bytes"}

    @classmethod
    def setUpClass(cls):
        # A fresh root holds the resolver, the design record and the report it
        # writes; the handler drives this tree's controller.
        scratch = tempfile.TemporaryDirectory(prefix="deferred-runner-joined-")
        cls.addClassCleanup(scratch.cleanup)
        cls.root = Path(scratch.name).resolve()
        for name in ("proof.py", "design-evidence.json"):
            destination = cls.root / PACKAGE / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / PACKAGE / name, destination)
        criterion = "joined-demonstration"
        handler = PROOF.HANDLERS[criterion]
        stdout = io.StringIO()
        with mock.patch.dict(PROOF.HANDLERS, {criterion: lambda root: handler(ROOT)}), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            cls.code = PROOF.main(["--candidate", "creating-step-binding", "--criterion", criterion,
                                   "--report", cell_report(criterion)], root=cls.root)
        cls.printed = json.loads(stdout.getvalue())
        if cls.code != 0:
            raise AssertionError("demonstration refused: " + stdout.getvalue())
        cls.report_bytes = (cls.root / cell_report(criterion)).read_bytes()
        cls.evidence = json.loads((cls.root / cell_evidence(criterion)).read_bytes())
        cls.observations = cls.evidence["observations"]

    def checks(self, kinds):
        return {row["id"]: row["holds"] for row in self.evidence["checks"] if row["kind"] in kinds}

    def test_report_is_closed_passing_and_bound_to_its_evidence(self):
        report = json.loads(self.report_bytes)
        self.assertEqual(report, {
            "schema": "protasis-design-report/v1", "candidate": "creating-step-binding",
            "criterion": "joined-demonstration", "value": True, "unit": "boolean",
            "command": PROOF.resolver("creating-step-binding", "joined-demonstration"), "exit": 0})
        self.assertEqual(self.printed, report)
        self.assertEqual(self.evidence["report"], {
            "path": cell_report("joined-demonstration"),
            "sha256": hashlib.sha256(self.report_bytes).hexdigest()})
        self.assertEqual((self.evidence["schema"], self.evidence["value"]),
                         (PROOF.EVIDENCE_SCHEMA, True))
        self.assertEqual(sorted(path.name for path in (self.root / ".hexaemeron/reports").iterdir()),
                         sorted([Path(cell_report("joined-demonstration")).name,
                                 Path(cell_evidence("joined-demonstration")).name]))
        # Protasis consumes the report at integration.
        with tempfile.TemporaryDirectory(prefix="deferred-runner-integration-") as scratch:
            run = Path(scratch) / ".hexaemeron"
            (run / "reports").mkdir(parents=True)
            shutil.copyfile(ROOT / PACKAGE / "design-evidence.json", run / "design-evidence.json")
            for selection in (ROOT / PACKAGE / "reports").iterdir():
                shutil.copyfile(selection, run / "reports" / selection.name)
            (run / cell_report("joined-demonstration").removeprefix(".hexaemeron/")).write_bytes(
                self.report_bytes)
            findings, _, consumed = DESIGN.evaluate(run / "design-evidence.json", "integration")
        self.assertIn("joined-demonstration", {row["criterion"] for row in consumed})
        self.assertFalse([finding for finding in findings
                          if "/joined-demonstration " in finding.message])

    def test_names_the_controller_and_adapter_bytes_it_drove(self):
        for key, relative in (("controller", PROOF.CONTROLLER), ("adapter", PROOF.ADAPTER)):
            data = (ROOT / relative).read_bytes()
            with self.subTest(key=key):
                self.assertEqual(self.evidence[key], {
                    "path": relative, "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data)})
                self.assertEqual(self.observations[key]["sha256_after"],
                                 hashlib.sha256(data).hexdigest())
        self.assertEqual(self.observations["controller"]["driven"], PROOF.CONTROLLER)
        # Each gate record the controller wrote names the adapter it loaded.
        adapter = self.evidence["adapter"]["sha256"]
        self.assertEqual(self.observations["runbook"]["adapter_sha256"], adapter)
        self.assertEqual(self.observations["binding"]["adapter_sha256"], adapter)
        self.assertEqual(self.evidence["sources"], [
            {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
            for path in (PROOF.SELF, PROOF.HARNESS, PROOF.ELENCHUS_PARSER)])
        self.assertEqual(self.checks({"identity"}), dict.fromkeys(self.IDENTITY, True))

    def test_positive_observations_hold(self):
        self.assertEqual(self.checks({"positive"}), dict.fromkeys(self.POSITIVE, True))
        commits = self.evidence["fixture"]["commits"]
        self.assertEqual(set(commits), {"starting", "implementation", "fix", "push_head",
                                        "later_edit", "implement_receipt", "fixes_ref"})
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", value) for value in commits.values()))
        self.assertEqual(len({commits[name] for name in
                              ("starting", "implementation", "fix", "push_head", "later_edit")}), 5)
        status = self.observations["status"]
        self.assertEqual([status[name]["status"] for name in
                          ("after-runbook", "after-fix", "before-push", "after-push")],
                         ["awaiting-binding"] * 3 + ["current"])
        self.assertEqual(self.observations["binding"]["paths"][0]["sha256"],
                         hashlib.sha256(PROOF.RUNNER_FIXED.encode()).hexdigest())
        self.assertEqual(self.observations["amendments"]["ledger_events"], 0)
        self.assertEqual((self.observations["runs"]["created"]["assertion_failures"],
                          self.observations["runs"]["fixed"]["executed"]), (1, 2))

    def test_refusal_observations_hold(self):
        self.assertEqual(self.checks({"refusal"}), dict.fromkeys(self.REFUSAL, True))
        refusals = {"present-runner": self.observations["present-runner"],
                    "push-mismatch": self.observations["push-mismatch"],
                    "drift-verify": self.observations["drift"]["verify"],
                    "drift-implement": self.observations["drift"]["implement"]}
        tokens = {"present-runner": ["deferred-source-present"],
                  "push-mismatch": ["deferred-worktree-mismatch"],
                  "drift-verify": ["registered-source-drift"],
                  "drift-implement": ["registered-source-drift"]}
        for name, refusal in refusals.items():
            with self.subTest(name=name):
                self.assertEqual(refusal["returncode"], 1)
                self.assertEqual(refusal["tokens"], tokens[name])
                self.assertEqual(refusal["before"], refusal["after"])

    def test_each_check_fails_when_its_observation_does(self):
        self.assertEqual(set(PERTURBATIONS), self.POSITIVE | self.REFUSAL | self.IDENTITY)
        self.assertEqual({row["id"] for row in PROOF.assess(self.observations)
                          if row["holds"]}, set(PERTURBATIONS))
        for identifier, changes in PERTURBATIONS.items():
            for index, change in enumerate(changes):
                with self.subTest(check=identifier, perturbation=index):
                    observations = copy.deepcopy(self.observations)
                    change(observations)
                    failing = {row["id"] for row in PROOF.assess(observations) if not row["holds"]}
                    self.assertEqual(failing, {identifier})

    def test_value_is_derived_from_the_observations(self):
        altered = copy.deepcopy(self.observations)
        PERTURBATIONS["later-edit-refuses-drift"][0](altered)
        for observations, expected in ((self.observations, True), (altered, False)):
            with self.subTest(expected=expected), \
                    mock.patch.object(PROOF, "run_demonstration", return_value=observations):
                outcome = PROOF.joined_demonstration(ROOT)
            self.assertIs(outcome.value, expected)
            self.assertIs(outcome.evidence["value"], expected)
            self.assertEqual(len(outcome.evidence["establishes"]), 5 if expected else 4)
        missing = copy.deepcopy(self.observations)
        del missing["drift"]
        self.assertFalse(dict((row["id"], row["holds"]) for row in PROOF.assess(missing))[
            "later-edit-refuses-drift"])

    def test_identity_is_read_again_after_the_run_and_from_the_harness(self):
        cached = {key: value for key, value in self.observations.items()
                  if key not in ("controller", "adapter", "sources")}

        class Stub:
            stage = "stub"

            def setUp(self):
                pass

            def tearDown(self):
                pass

            def demonstrate(self, scratch):
                return copy.deepcopy(cached)

        original_read, original_load = PROOF.read_tree_file, PROOF.load_registered
        reads = []

        def changed_after_run(root, relative, cap=PROOF.MAX_SOURCE_BYTES):
            data = original_read(root, relative, cap)
            reads.append(relative)
            if relative in (PROOF.CONTROLLER, PROOF.ADAPTER) and reads.count(relative) > 1:
                return data + b"# changed during the run\n"
            return data

        def elsewhere(path, name):
            module = original_load(path, name)
            if Path(path).name == "hexctl_harness.py":
                module.HEXCTL = str(ROOT / "hexctl.py")
            return module

        cases = (({}, set()),
                 ({"read_tree_file": changed_after_run}, {"controller-bytes", "adapter-bytes"}),
                 ({"load_registered": elsewhere}, {"controller-bytes"}))
        for patches, failing in cases:
            with self.subTest(failing=failing), \
                    mock.patch.object(PROOF, "demonstration_case", return_value=Stub()), \
                    contextlib.ExitStack() as stack:
                for name, replacement in patches.items():
                    stack.enter_context(mock.patch.object(PROOF, name, side_effect=replacement))
                observations = PROOF.run_demonstration(ROOT)
                self.assertEqual({row["id"] for row in PROOF.assess(observations)
                                  if not row["holds"]}, failing)

    def test_evidence_states_its_exclusions_and_what_it_leaves_unclaimed(self):
        self.assertEqual(self.evidence["exclusions"], list(PROOF.EXCLUSIONS))
        self.assertEqual(self.evidence["unclaimed"], list(PROOF.UNCLAIMED))
        self.assertEqual(self.evidence["establishes"], list(PROOF.CLAIMS.values()))
        text = " ".join(self.evidence["exclusions"] + self.evidence["unclaimed"])
        for boundary in ("fake delivery tools", "sufficient", "isolation", "remote GitHub"):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, text)

    def test_refusal_tokens_match_whole(self):
        self.assertEqual(PROOF.tokens_in("gate binding refused: deferred-source-present-at-base"),
                         ["deferred-source-present-at-base"])
        self.assertEqual(PROOF.tokens_in("refused: deferred-source-present: tests/run_tests.py"),
                         ["deferred-source-present"])
        self.assertEqual(PROOF.tokens_in("not-registered-source-drift-x"), [])

    def test_fixture_runner_fits_the_gate_and_starts_no_process(self):
        # The builder the gate parses, and no module that starts a process.
        for program in (PROOF.RUNNER_CREATED, PROOF.RUNNER_FIXED):
            tree = ast.parse(program)
            imported = {alias.name.split(".")[0] for node in ast.walk(tree)
                        if isinstance(node, (ast.Import, ast.ImportFrom))
                        for alias in (node.names if isinstance(node, ast.Import)
                                      else [ast.alias(node.module)])}
            self.assertEqual(imported, {"argparse", "json", "pathlib", "sys", "unittest"})
        self.assertNotEqual(PROOF.RUNNER_CREATED, PROOF.RUNNER_FIXED)
        self.assertIn('"socket.getnameinfo"', PROOF.RUNNER_FIXED)
        self.assertNotIn('"socket.getnameinfo"', PROOF.RUNNER_CREATED)


if __name__ == "__main__":
    unittest.main()
