"""Check the skills#1648 design home: receipted copies, selection evidence, draft."""
import contextlib
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


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "docs/fiat-1648-archive-restore-binding"
# The receipted bytes: the study accepted on 2026-11-06, the runbook receipted
# the same day, and the design record its design-lock block names.
RECEIPTED = {
    "study.md": "9406ff57bdf3850815d86e8d72ed689cc0171b2223454dbeb00abe9f66a6ef82",
    "runbook.md": "e841266f3fb16b4703f02c1629dfcec6f70f0825b697340681a4cffad1744ce3",
    "design-evidence.json": "815abd409e5d7031407d9c4104884e47814da7798e8891917625fa7a18ab9742",
}
# The probe digest the study's section 4.3 pins, and the builder that
# assembled the receipted record from the selection reports.
PINNED_SCRIPTS = {
    "probe.py": "1a58475494dc832535497d9947dfc3a59fc28ba20043c45737e48f7207c13b57",
    "build_record.py": "dab40b01ca7f3082774b8c6089786682c18c54f7c1bacacff6104512ee425ab8",
}
DRAFT = "docs/decisions/drafts/bind-archive-restore-to-its-admitted-directory.md"
SELECTOR = "adr/" + Path(DRAFT).stem
SELECTED = "anchored-cwd"
CANDIDATES = ("path-unchanged", "identity-recheck", "anchored-cwd", "private-build-adopt")
SELECTION_UNITS = {
    "unswapped-restore-completes": "boolean",
    "directory-swap-writes-nothing": "boolean",
    "symlink-swap-writes-nothing": "boolean",
    "interrupted-cleanup-stays-bound": "boolean",
    "residue-follows-reference": "boolean",
    "transaction-race-leaked-trials": "count",
    "name-resolving-writes": "count",
    "identity-probes-per-restore": "count",
    "bytes-built-outside-destination": "bytes",
}
CONFORMANCE_UNITS = {
    "replacement-regression-guarded": "boolean",
    "nonempty-symlink-still-refuse": "boolean",
    "interrupted-restore-stays-bound": "boolean",
    "from-mode-unchanged": "boolean",
}
# The study's section 4.3 table, one value per candidate in CANDIDATES order.
MEASURED = {
    "unswapped-restore-completes": (True, True, True, True),
    "directory-swap-writes-nothing": (False, True, True, True),
    "symlink-swap-writes-nothing": (False, True, True, True),
    "interrupted-cleanup-stays-bound": (False, True, True, True),
    "residue-follows-reference": (True, True, True, False),
    "transaction-race-leaked-trials": (47, 35, 0, 0),
    "name-resolving-writes": (14, 14, 0, 0),
    "identity-probes-per-restore": (0, 38, 12, 3),
    "bytes-built-outside-destination": (0, 0, 0, 39800),
}
# The tests each conformance resolver runs, as the runbook's preamble names them.
CONFORMANCE_TESTS = {
    "replacement-regression-guarded": [
        ("test_checkpoint_restore_binding.py", "replacement"),
    ],
    "nonempty-symlink-still-refuse": [
        ("test_hexctl_checkpoint_archive.py",
         "test_restore_from_archive_refuses_non_empty_destination"),
        ("test_hexctl_checkpoint_archive.py",
         "test_archive_restore_accepts_a_symlinked_destination_parent"),
        ("test_checkpoint_restore_binding.py", "symlink_destination"),
    ],
    "interrupted-restore-stays-bound": [
        ("test_checkpoint_restore_binding.py", "interrupted"),
    ],
    "from-mode-unchanged": [
        ("test_hexctl_checkpoint.py", "restore"),
    ],
}
REFUSAL = "checkpoint restore destination no longer names the admitted directory"
# The record's report paths stay relative to .hexaemeron/, where it was built;
# the runbook publishes the same reports one directory shallower.
RECORD_REPORTS = "design/reports/selection/"
COMMITTED_REPORTS = "reports/selection/"
LOCAL_PATH_MARKERS = (b"/Users/", b"/home/", b"/private/", b"/var/folders/")


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


PROBE = load(PACKAGE + "/probe.py", "fiat_1648_restore_binding_probe")
BUILDER = load(PACKAGE + "/build_record.py", "fiat_1648_restore_binding_builder")
DESIGN = load("plugins/hexaemeron/skills/protasis/scripts/design_evidence.py",
              "fiat_1648_restore_binding_design_checker")
BRIDGE = load("plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py",
              "fiat_1648_restore_binding_bridge_checker")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record():
    return json.loads((ROOT / PACKAGE / "design-evidence.json").read_bytes())


def selection_rows():
    return [row for row in record()["results"] if isinstance(row["report"], dict)]


def draft_text():
    raw, home, error = BRIDGE._read_stable_adr(ROOT, SELECTOR)
    if error is not None or raw is None:
        raise AssertionError("decision record unresolved: " + str(error))
    return raw.decode("utf-8"), home


def git_environment():
    """Remove inherited Git routing so the query stays in this repository."""
    environment = dict(os.environ)
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE",
                 "GIT_PREFIX", "GIT_INTERNAL_SUPER_PREFIX"):
        environment.pop(name, None)
    return environment


def tracked(*prefixes):
    """Index entries below each prefix, as repository-relative POSIX paths."""
    listed = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
        ["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--", *prefixes],
        capture_output=True, check=True, env=git_environment(),
    ).stdout
    return sorted(os.fsdecode(raw) for raw in listed.split(b"\0") if raw)


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


def scratch(test):
    directory = tempfile.TemporaryDirectory(prefix="fiat-1648-scaffold-")
    test.addCleanup(directory.cleanup)
    return Path(directory.name).resolve()


def rebuilt_layout(test):
    """The committed reports placed where the record's own paths name them."""
    base = scratch(test)
    reports = base / RECORD_REPORTS
    reports.mkdir(parents=True)
    for path in sorted((ROOT / PACKAGE / COMMITTED_REPORTS).iterdir()):
        shutil.copyfile(path, reports / path.name)
    return base


def run_script(name, cwd, *argv):
    environment = dict(os.environ)
    environment.pop("FORCE_COLOR", None)
    return subprocess.run(  # phylax: allow subprocess: fixed argv interpreter, no shell
        [sys.executable, "-I", "-B", str(ROOT / PACKAGE / name), *argv],
        cwd=cwd, env=environment, capture_output=True, text=True, timeout=120, check=False)


def table_row(criterion):
    cells = []
    for value in MEASURED[criterion]:
        if isinstance(value, bool):
            cells.append("pass" if value else "fail")
        else:
            cells.append(str(value))
    return "| `" + criterion + "` | " + " | ".join(cells) + " |"


class ReceiptedCopyTests(unittest.TestCase):
    def test_copies_equal_their_receipted_bytes(self):
        for name, expected in {**RECEIPTED, **PINNED_SCRIPTS}.items():
            with self.subTest(name=name):
                self.assertEqual(digest(ROOT / PACKAGE / name), expected)

    def test_study_pins_the_probe_and_record_it_selected_with(self):
        text = (ROOT / PACKAGE / "study.md").read_text(encoding="utf-8")
        self.assertIn("(probe SHA-256 `" + PINNED_SCRIPTS["probe.py"] + "`)", text)
        self.assertIn("`.hexaemeron/design-evidence.json`, SHA-256\n`"
                      + RECEIPTED["design-evidence.json"] + "`", text)

    def test_runbook_copy_locks_the_committed_record(self):
        text = (ROOT / PACKAGE / "runbook.md").read_text(encoding="utf-8")
        self.assertIn("```design-lock\nschema | protasis-design-evidence/v1\nsha256 | "
                      + RECEIPTED["design-evidence.json"] + "\ncandidate | " + SELECTED
                      + "\n```", text)
        self.assertIn("SHA-256 `" + RECEIPTED["study.md"] + "`", text)


class SelectionEvidenceTests(unittest.TestCase):
    def test_each_selection_report_equals_its_recorded_digest(self):
        rows = selection_rows()
        self.assertEqual(len(rows), len(CANDIDATES) * len(SELECTION_UNITS))
        for row in rows:
            reference = row["report"]
            with self.subTest(path=reference["path"]):
                name = row["candidate"] + "-" + row["criterion"] + ".json"
                self.assertEqual(reference["path"], RECORD_REPORTS + name)
                path = ROOT / PACKAGE / COMMITTED_REPORTS / name
                data = path.read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), reference["sha256"])
                report = json.loads(data)
                self.assertEqual(report, {
                    "schema": "protasis-design-report/v1", "candidate": row["candidate"],
                    "criterion": row["criterion"], "value": report["value"],
                    "unit": SELECTION_UNITS[row["criterion"]], "exit": 0,
                    "command": "python3 .hexaemeron/design/probe.py select --candidate "
                               + row["candidate"] + " --criterion " + row["criterion"]
                               + " --out .hexaemeron/" + RECORD_REPORTS + name})
                for marker in LOCAL_PATH_MARKERS:
                    self.assertNotIn(marker, data)
        committed = {path.name for path in (ROOT / PACKAGE / COMMITTED_REPORTS).iterdir()}
        self.assertEqual(committed, {Path(row["report"]["path"]).name for row in rows})

    def test_report_values_match_the_study_and_draft_tables(self):
        values = {}
        for row in selection_rows():
            report = json.loads((ROOT / PACKAGE / COMMITTED_REPORTS
                                 / Path(row["report"]["path"]).name).read_bytes())
            values[(row["candidate"], row["criterion"])] = report["value"]
        study = (ROOT / PACKAGE / "study.md").read_text(encoding="utf-8")
        draft, _ = draft_text()
        for criterion, expected in MEASURED.items():
            with self.subTest(criterion=criterion):
                measured = tuple(values[(candidate, criterion)] for candidate in CANDIDATES)
                self.assertEqual(measured, expected)
                self.assertEqual([type(value) for value in measured],
                                 [type(value) for value in expected])
                self.assertIn(table_row(criterion), study)
                self.assertIn(table_row(criterion), draft)

    def test_builder_rebuilds_the_record_from_the_committed_reports(self):
        base = rebuilt_layout(self)
        out = base / "design-evidence.json"
        completed = run_script("build_record.py", base, "--out", str(out))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(digest(out), RECEIPTED["design-evidence.json"])
        self.assertEqual(out.read_bytes(), (ROOT / PACKAGE / "design-evidence.json").read_bytes())

    def test_rebuilt_layout_locks_the_selected_design(self):
        base = rebuilt_layout(self)
        path = base / "design-evidence.json"
        shutil.copyfile(ROOT / PACKAGE / "design-evidence.json", path)
        for transition in ("design-lock", "step:1", "step:2", "step:3"):
            with self.subTest(transition=transition):
                findings, admitted, _ = DESIGN.evaluate(path, transition)
                self.assertEqual([finding.as_dict() for finding in findings], [])
        self.assertEqual(admitted["selection"], {"candidate": SELECTED, "policy_ref": None,
                                                 "rule": "unique-frontier"})
        self.assertEqual(tuple(item["id"] for item in admitted["candidates"]), CANDIDATES)
        units = {stage: {item["id"]: item["unit"] for item in admitted["criteria"]
                         if item["stage"] == stage} for stage in ("selection", "conformance")}
        self.assertEqual(units, {"selection": SELECTION_UNITS, "conformance": CONFORMANCE_UNITS})
        findings, _, _ = DESIGN.evaluate(path, "integration")
        self.assertEqual({finding.code for finding in findings}, {"D008"})
        self.assertEqual(len(findings), len(CONFORMANCE_UNITS))
        for finding in findings:
            self.assertTrue(finding.message.startswith(SELECTED + "/"), finding.message)

    def test_pending_conformance_cells_name_the_probe(self):
        rows = [row for row in record()["results"] if row["state"] == "pending"]
        self.assertEqual(len(rows), len(CANDIDATES) * len(CONFORMANCE_UNITS))
        for candidate in CANDIDATES:
            cells = {row["criterion"]: row for row in rows if row["candidate"] == candidate}
            self.assertEqual(set(cells), set(CONFORMANCE_UNITS))
            for criterion, row in cells.items():
                with self.subTest(candidate=candidate, criterion=criterion):
                    report = "design/reports/conformance/" + candidate + "-" + criterion + ".json"
                    self.assertEqual(row["blocks"], "integration")
                    self.assertEqual(row["report"], report)
                    self.assertEqual(row["resolver"],
                                     "python3 .hexaemeron/design/probe.py conform --candidate "
                                     + candidate + " --criterion " + criterion
                                     + " --root . --out .hexaemeron/" + report)


class DecisionDraftTests(unittest.TestCase):
    def test_decision_draft_resolves_through_the_study_bridge(self):
        study = PACKAGE + "/study.md"
        evidence = PACKAGE + "/design-evidence.json"
        self.assertEqual([finding.code for finding in
                          BRIDGE.check_design_bridge(study, evidence, ROOT)], [])
        bridge, _, error = BRIDGE._design_bridge_block(
            (ROOT / study).read_text(encoding="utf-8").splitlines())
        self.assertIsNone(error)
        self.assertEqual(bridge["decision"], SELECTED)
        self.assertEqual(bridge["record"], DRAFT)
        text, home = draft_text()
        if home.as_posix() == DRAFT:
            self.assertTrue(text.startswith("# Decision: "))
        else:
            self.assertEqual(home.parent.as_posix(), "docs/decisions")
            self.assertRegex(home.name, r"^ADR-[0-9]{3}-" + re.escape(Path(DRAFT).stem) + r"\.md$")
            self.assertTrue(text.startswith("# ADR-" + home.name[4:7] + ": "))
        for heading in ("Status", "Context", "Decision", "Alternatives", "Consequences"):
            self.assertIn("\n## " + heading + "\n", text)
        for candidate in CANDIDATES:
            self.assertIn("`" + candidate + "`", text)
        # The study-mode command the runbook's Step 1 Exit names, run in process.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = BRIDGE.main(["--study", study, "--design-evidence", evidence,
                                "--repo-root", str(ROOT)])
        self.assertEqual(code, 0)

    def test_draft_records_both_study_decisions(self):
        """Section 12 puts the binding and the fixed refusal in one record."""
        text, _ = draft_text()
        decision = text.split("\n## Decision\n", 1)[1].split("\n## Alternatives\n", 1)[0]
        self.assertIn("`fchdir`", decision)
        self.assertIn("`dir_fd`", decision)
        self.assertIn("`" + REFUSAL + "` through `die(..., 1)`", decision)
        self.assertIn("not a class in `CHECKPOINT_ARCHIVE_REFUSALS`", decision)

    def test_draft_states_the_git_window_it_leaves_open(self):
        """The study's git-absolute-paths row owes its residual window a home."""
        study = (ROOT / PACKAGE / "study.md").read_text(encoding="utf-8")
        fence = study.split("```risk-register\n", 1)[1].split("\n```", 1)[0]
        rows = {line.split(" | ")[0]: line.split(" | ") for line in fence.splitlines()}
        self.assertIn("the residual window is stated, not claimed closed",
                      rows["git-absolute-paths"][2])
        text, _ = draft_text()
        consequences = text.split("\n## Consequences\n", 1)[1]
        self.assertIn("Git's absolute-path window stays open and is stated, not claimed closed",
                      consequences)
        self.assertIn("Linux Git behaviour is unmeasured", consequences)

    def test_draft_keeps_the_study_race_qualifications(self):
        """The study qualifies the selected candidate's race figures; the draft keeps both."""
        study = (ROOT / PACKAGE / "study.md").read_text(encoding="utf-8")
        flat = " ".join(study.split())
        self.assertIn("while the probe was being written, gave 1, 1 and 0", flat)
        self.assertIn("gave `path-unchanged` 10, `identity-recheck` 13, `anchored-cwd` 11 and "
                      "`private-build-adopt` 0 of 100", flat)
        text, _ = draft_text()
        alternatives = text.split("\n## Alternatives\n", 1)[1].split("\n## Consequences\n", 1)[0]
        self.assertIn("gave 1, 1 and 0, and the one leak inspected held directories only, "
                      "from `git worktree add`", alternatives)
        consequences = text.split("\n## Consequences\n", 1)[1]
        self.assertIn("leaked in 11 of 100 trials for `anchored-cwd`, against 10 for "
                      "`path-unchanged`, 13 for `identity-recheck` and 0 for "
                      "`private-build-adopt`", consequences)


class TrackedContentTests(unittest.TestCase):
    def test_only_the_named_copies_are_tracked(self):
        reports = [COMMITTED_REPORTS + candidate + "-" + criterion + ".json"
                   for candidate in CANDIDATES for criterion in SELECTION_UNITS]
        expected = sorted(PACKAGE + "/" + name for name in
                          ["build_record.py", "design-evidence.json", "probe.py",
                           "runbook.md", "study.md", *reports])
        self.assertEqual(tracked(PACKAGE), expected)
        self.assertEqual(tracked(".hexaemeron"), [])
        _, home = draft_text()
        self.assertEqual(tracked(home.as_posix()), [home.as_posix()])
        if home.as_posix() != DRAFT:
            self.assertEqual(tracked(DRAFT), [])


class ScriptCopyTests(unittest.TestCase):
    """The copied probe and builder keep their closed arguments and write exclusively."""

    def test_script_constants_match_the_record(self):
        self.assertEqual(PROBE.CANDIDATES, CANDIDATES)
        self.assertEqual(PROBE.SELECTED, SELECTED)
        self.assertEqual(PROBE.SELECTION_UNITS, SELECTION_UNITS)
        self.assertEqual(PROBE.CONFORMANCE_UNITS, CONFORMANCE_UNITS)
        self.assertEqual(PROBE.REPORT_SCHEMA, "protasis-design-report/v1")
        self.assertEqual(tuple(item[0] for item in BUILDER.CANDIDATES), CANDIDATES)
        self.assertEqual({item[0]: item[4] for item in BUILDER.SELECTION}, SELECTION_UNITS)
        self.assertEqual({item[0]: "boolean" for item in BUILDER.CONFORMANCE},
                         CONFORMANCE_UNITS)

    def test_probe_binds_the_tests_the_runbook_names(self):
        self.assertEqual(PROBE.CONFORMANCE_TESTS, CONFORMANCE_TESTS)

    def test_scripts_hold_no_local_path(self):
        for name in PINNED_SCRIPTS:
            data = (ROOT / PACKAGE / name).read_bytes()
            for marker in LOCAL_PATH_MARKERS:
                with self.subTest(name=name, marker=marker):
                    self.assertNotIn(marker, data)

    def test_existing_out_is_refused_and_preserved(self):
        base = scratch(self)
        report = base / "report.json"
        report.write_bytes(b"previous report\n")
        target = base / "keep.json"
        target.write_bytes(b"keep\n")
        link = base / "link.json"
        link.symlink_to(target)
        for path in (report, link):
            for name, argv, refusal in (
                    ("probe.py", ["conform", "--candidate", SELECTED, "--criterion",
                                  "from-mode-unchanged", "--root", str(base), "--out", str(path)],
                     "refusing to replace an existing report"),
                    ("build_record.py", ["--out", str(path)],
                     "refusing to replace an existing record")):
                with self.subTest(path=path.name, script=name):
                    before = snapshot(base)
                    completed = run_script(name, base, *argv)
                    self.assertEqual(completed.returncode, 1)
                    self.assertIn(refusal, completed.stderr)
                    self.assertEqual(completed.stdout, "")
                    self.assertEqual(snapshot(base), before)
        self.assertEqual(report.read_bytes(), b"previous report\n")
        self.assertEqual(target.read_bytes(), b"keep\n")

    def test_probe_report_write_is_create_only(self):
        base = scratch(self)
        out = base / "nested" / "report.json"
        arguments = (str(out), SELECTED, "from-mode-unchanged", True, "boolean",
                     "python3 .hexaemeron/design/probe.py conform")
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            PROBE.write_report(*arguments)
        data = out.read_bytes()
        self.assertEqual(json.loads(data), {
            "schema": "protasis-design-report/v1", "candidate": SELECTED,
            "criterion": "from-mode-unchanged", "value": True, "unit": "boolean",
            "command": "python3 .hexaemeron/design/probe.py conform", "exit": 0})
        self.assertEqual(printed.getvalue(), data.decode("utf-8"))
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            PROBE.write_report(str(out), SELECTED, "from-mode-unchanged", False, "boolean",
                               "python3 .hexaemeron/design/probe.py conform")
        self.assertEqual(out.read_bytes(), data)

    def test_conform_without_the_built_module_reports_false(self):
        base = scratch(self)
        out = base / "report.json"
        completed = run_script("probe.py", base, "conform", "--candidate", SELECTED,
                               "--criterion", "replacement-regression-guarded",
                               "--root", str(base), "--out", str(out))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(out.read_bytes())
        self.assertIs(report["value"], False)
        self.assertEqual(completed.stdout, out.read_text(encoding="utf-8"))
        self.assertEqual(set(snapshot(base)), {"report.json"})

    def test_probe_arguments_outside_the_closed_set_refuse(self):
        base = scratch(self)
        out = str(base / "report.json")
        for argv in ([], ["measure"],
                     ["select", "--candidate", SELECTED, "--criterion", "name-resolving-writes"],
                     ["select", "--candidate", "no-such-candidate", "--criterion",
                      "name-resolving-writes", "--out", out],
                     ["select", "--candidate", SELECTED, "--criterion",
                      "from-mode-unchanged", "--out", out],
                     ["conform", "--candidate", SELECTED, "--criterion",
                      "name-resolving-writes", "--root", str(base), "--out", out],
                     ["conform", "--candidate", SELECTED, "--criterion",
                      "from-mode-unchanged", "--out", out]):
            with self.subTest(argv=argv):
                completed = run_script("probe.py", base, *argv)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("usage:", completed.stderr)
                self.assertEqual(snapshot(base), {})

    def test_probe_conform_refuses_an_unselected_candidate(self):
        base = scratch(self)
        for candidate in CANDIDATES:
            if candidate == SELECTED:
                continue
            with self.subTest(candidate=candidate):
                completed = run_script("probe.py", base, "conform", "--candidate", candidate,
                                       "--criterion", "from-mode-unchanged", "--root",
                                       str(base), "--out", str(base / "report.json"))
                self.assertEqual(completed.returncode, 1)
                self.assertIn("conformance applies to the selected candidate only",
                              completed.stderr)
                self.assertEqual(snapshot(base), {})

    def test_builder_without_reports_writes_nothing(self):
        base = scratch(self)
        completed = run_script("build_record.py", base, "--out", str(base / "design-evidence.json"))
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(snapshot(base), {})


if __name__ == "__main__":
    unittest.main()
