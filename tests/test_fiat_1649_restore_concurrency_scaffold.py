"""Check the skills#1649 design home: receipted copies, selection evidence, draft."""
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
PACKAGE = "docs/fiat-1649-restore-concurrency"
# The receipted bytes: the study accepted on 2026-11-07, the runbook receipted
# the same day, and the design record its design-lock block names.
RECEIPTED = {
    "study.md": "ca60ff5f05f23d9c2c64b3d09c33635881a5a41d3d26c62c1d25f16af4a2922f",
    "runbook.md": "152a1fef6cb16e3aa74daefac1564bb91d80bca9c23fa2b57f28160101b621ed",
    "design-evidence.json": "c727d18a199026f12914c4fd22289e4dab5d66a8a57e1fe6647b2c6c5958cfc2",
}
# The probe digest the study's section 4.3 pins, and the builder that
# assembled the receipted record from the selection reports.
PINNED_SCRIPTS = {
    "probe.py": "53f307d1f7b4b40d569d48efb51d58c660a93fd5a91f0afedff4198684c51a5d",
    "build_record.py": "dbc881f9602dee1f1d74f59e3f337115f6c9051feb4a8b5e0e3eb21f537ba9df",
}
DRAFT = "docs/decisions/drafts/exclude-competing-checkpoint-restores.md"
SELECTOR = "adr/" + Path(DRAFT).stem
SELECTED = "admitted-fd-flock"
CANDIDATES = ("mutating-set", "destination-kernel-lock", "exclusive-entry", "admitted-fd-flock")
SELECTION_UNITS = {
    "uncontended-restore-completes": "boolean",
    "competing-restores-one-winner": "boolean",
    "live-resume-refused": "boolean",
    "killed-holder-resumes": "boolean",
    "killed-before-write-readmits": "boolean",
    "imported-state-excluded": "boolean",
    "origin-init-excluded": "boolean",
    "concurrent-holders-after-crash": "count",
    "lock-acquisitions-per-restore": "count",
    "entries-left-after-early-kill": "count",
}
CONFORMANCE_UNITS = {
    "restore-contention-guarded": "boolean",
    "imported-state-guarded": "boolean",
    "killed-restore-recovers": "boolean",
    "existing-restores-unchanged": "boolean",
}
# The study's section 4.3 table, one value per candidate in CANDIDATES order.
MEASURED = {
    "uncontended-restore-completes": (True, True, True, True),
    "competing-restores-one-winner": (False, True, True, True),
    "live-resume-refused": (True, True, True, True),
    "killed-holder-resumes": (False, True, True, True),
    "killed-before-write-readmits": (True, False, False, True),
    "imported-state-excluded": (False, True, True, True),
    "origin-init-excluded": (False, True, False, True),
    "concurrent-holders-after-crash": (1, 1, 2, 1),
    "lock-acquisitions-per-restore": (0, 2, 2, 3),
    "entries-left-after-early-kill": (0, 3, 1, 0),
}
# The tests each conformance resolver runs, as the runbook's preamble names them.
MODULE = "test_checkpoint_restore_concurrency.py"
CONFORMANCE_TESTS = {
    "restore-contention-guarded": [
        (MODULE, "one_winner"), (MODULE, "live_resume"), (MODULE, "origin_init"),
    ],
    "imported-state-guarded": [(MODULE, "imported_state")],
    "killed-restore-recovers": [(MODULE, "killed")],
    "existing-restores-unchanged": [
        ("test_checkpoint_restore_binding.py", "test_"),
        ("test_hexctl_checkpoint.py", "restore"),
        ("test_hexctl.py", "TestRunLock"),
    ],
}
REFUSAL = "checkpoint restore destination is held by another hexctl command"
# The record's report paths stay relative to .hexaemeron/, where it was built;
# the runbook publishes the same reports one directory shallower.
RECORD_REPORTS = "design/reports/selection/"
COMMITTED_REPORTS = "reports/selection/"
RECORD_CONFORMANCE = "design/reports/conformance/"
COMMITTED_CONFORMANCE = "reports/conformance/"
DEMONSTRATION = PACKAGE + "/demonstration.md"
# The bytes each Step 3 resolver wrote on 2026-11-07, as the demonstration
# states them.
CONFORMANCE_DIGESTS = {
    "restore-contention-guarded":
        "8707818b5ee0be41457f46c8cc54401e109c137bea79efba98012564e803c427",
    "imported-state-guarded":
        "7d5f30b67c698b2381b58853ba63f93c773321f848d8dacd7ffa2478afb7a67f",
    "killed-restore-recovers":
        "9b67ebe22e7fc44fe6becc40a48bbc5a1a4c13b10155c876d7421b434a8d2a6c",
    "existing-restores-unchanged":
        "2c22da30f5afb55bc9edd36f407ea1c7e46f443e9f7aec7df1a0fbcd8af7fe94",
}
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


PROBE = load(PACKAGE + "/probe.py", "fiat_1649_restore_concurrency_probe")
BUILDER = load(PACKAGE + "/build_record.py", "fiat_1649_restore_concurrency_builder")
DESIGN = load("plugins/hexaemeron/skills/protasis/scripts/design_evidence.py",
              "fiat_1649_restore_concurrency_design_checker")
BRIDGE = load("plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py",
              "fiat_1649_restore_concurrency_bridge_checker")


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


def section(text, heading, following=None):
    body = text.split("\n## " + heading + "\n", 1)[1]
    return body.split("\n## " + following + "\n", 1)[0] if following else body


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
    directory = tempfile.TemporaryDirectory(prefix="fiat-1649-scaffold-")
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
        """Section 12 puts the exclusion and the fixed refusal in one record."""
        text, _ = draft_text()
        decision = section(text, "Decision", "Alternatives")
        self.assertIn("`fcntl.flock(descriptor, LOCK_EX | LOCK_NB)`", decision)
        self.assertIn("never removes the destination, even one its own `mkdir` created",
                      decision)
        self.assertIn("Admission contention refuses `destination-occupied`", decision)
        self.assertIn("`" + REFUSAL + "` through `die(..., 1)`", decision)
        self.assertIn("not a class in `CHECKPOINT_ARCHIVE_REFUSALS`", decision)

    def test_draft_carries_the_study_assumptions(self):
        """Assumptions 1 to 6 bound what the selected design promises."""
        study = " ".join((ROOT / PACKAGE / "study.md").read_text(encoding="utf-8").split())
        self.assertIn("The exclusion is cooperative integrity against accident, not a "
                      "security boundary.", study)
        self.assertIn("A permitted outcome is one of three.", study)
        text, _ = draft_text()
        consequences = section(text, "Consequences")
        for claim in (
                "cooperative integrity against accident among `hexctl` processes run by "
                "one account",
                "It is not a security boundary.",
                "Each competitor ends in one of three permitted outcomes.",
                "active state with its marker, which a retry finalizes",
                "`status`, `next` and `verify` stay lock-free",
                "`cmd_checkpoint_restore` stays out of `MUTATING`",
                "`" + REFUSAL + "` elsewhere, exit 1",
                "The marker's allowed set gains `lock` and nothing else.",
                "The active-tree recheck excludes the live `lock`",
                "real `hexctl` and Git on Linux are not"):
            with self.subTest(claim=claim):
                self.assertIn(claim, consequences)

    def test_each_rejected_bullet_names_its_failed_gates(self):
        """Each rejected candidate's bullet names every gate the table fails it on."""
        text, _ = draft_text()
        bullets = {line.split("`", 2)[1]: line
                   for line in section(text, "Alternatives", "Consequences").splitlines()
                   if line.startswith("- `")}
        gates = [criterion for criterion, unit in SELECTION_UNITS.items() if unit == "boolean"]
        for index, candidate in enumerate(CANDIDATES):
            if candidate == SELECTED:
                continue
            failed = [gate for gate in gates if MEASURED[gate][index] is False]
            with self.subTest(candidate=candidate):
                self.assertTrue(failed)
                for gate in failed:
                    self.assertIn("`" + gate + "`", bullets[candidate])
        self.assertIn("Its `concurrent-holders-after-crash` is 2: two resumers",
                      bullets["exclusive-entry"])


def conformance_name(criterion):
    return SELECTED + "-" + criterion + ".json"


def resolver_command(criterion):
    return ("python3 .hexaemeron/design/probe.py conform --candidate " + SELECTED
            + " --criterion " + criterion + " --root . --out .hexaemeron/"
            + RECORD_CONFORMANCE + conformance_name(criterion))


class ConformanceEvidenceTests(unittest.TestCase):
    def test_conformance_reports_hold_stated_digest_and_true(self):
        demonstration = (ROOT / DEMONSTRATION).read_text(encoding="utf-8")
        for criterion, expected in CONFORMANCE_DIGESTS.items():
            with self.subTest(criterion=criterion):
                path = ROOT / PACKAGE / COMMITTED_CONFORMANCE / conformance_name(criterion)
                data = path.read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected)
                report = json.loads(data)
                self.assertIs(report["value"], True)
                self.assertEqual(report, {
                    "schema": "protasis-design-report/v1", "candidate": SELECTED,
                    "criterion": criterion, "value": True, "unit": "boolean",
                    "command": resolver_command(criterion), "exit": 0})
                for marker in LOCAL_PATH_MARKERS:
                    self.assertNotIn(marker, data)
                self.assertIn("| `" + criterion + "` | 0 | `true` | `" + expected + "` |",
                              demonstration)
        committed = {path.name for path in (ROOT / PACKAGE / COMMITTED_CONFORMANCE).iterdir()}
        self.assertEqual(committed, {conformance_name(item) for item in CONFORMANCE_UNITS})

    def test_demonstration_names_each_resolver_command(self):
        demonstration = (ROOT / DEMONSTRATION).read_text(encoding="utf-8")
        rows = [row for row in record()["results"]
                if row["candidate"] == SELECTED and row["state"] == "pending"]
        self.assertEqual({row["criterion"] for row in rows}, set(CONFORMANCE_DIGESTS))
        for row in rows:
            with self.subTest(criterion=row["criterion"]):
                self.assertEqual(row["resolver"], resolver_command(row["criterion"]))
                self.assertIn("`" + row["resolver"] + "`", demonstration)
                self.assertEqual(row["report"],
                                 RECORD_CONFORMANCE + conformance_name(row["criterion"]))

    def test_demonstration_states_what_it_leaves_open(self):
        text = " ".join((ROOT / DEMONSTRATION).read_text(encoding="utf-8").split())
        uncovered = text.split("## What this does not cover", 1)[1]
        for phrase in ("A writer that takes no `hexctl` lock", "Network filesystems",
                       "Real `hexctl` and Git on Linux", "root and administrators",
                       "deletes or replaces a lock file"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, uncovered)

    def test_committed_conformance_passes_integration(self):
        base = rebuilt_layout(self)
        conformance = base / RECORD_CONFORMANCE
        conformance.mkdir(parents=True)
        for criterion in CONFORMANCE_DIGESTS:
            shutil.copyfile(ROOT / PACKAGE / COMMITTED_CONFORMANCE / conformance_name(criterion),
                            conformance / conformance_name(criterion))
        path = base / "design-evidence.json"
        shutil.copyfile(ROOT / PACKAGE / "design-evidence.json", path)
        findings, admitted, consumed = DESIGN.evaluate(path, "integration")
        self.assertEqual([finding.as_dict() for finding in findings], [])
        self.assertEqual(admitted["selection"]["candidate"], SELECTED)
        self.assertEqual(
            {(item["candidate"], item["criterion"], item["path"], item["sha256"])
             for item in consumed},
            {(SELECTED, criterion, RECORD_CONFORMANCE + conformance_name(criterion), expected)
             for criterion, expected in CONFORMANCE_DIGESTS.items()})

    def test_draft_records_the_conformance_results(self):
        text, _ = draft_text()
        consequences = " ".join(section(text, "Consequences").split())
        self.assertIn("`" + DEMONSTRATION + "`", consequences)
        for criterion in CONFORMANCE_DIGESTS:
            with self.subTest(criterion=criterion):
                self.assertIn("`" + criterion + "`", consequences)


class TrackedContentTests(unittest.TestCase):
    def test_only_the_named_copies_are_tracked(self):
        reports = [COMMITTED_REPORTS + candidate + "-" + criterion + ".json"
                   for candidate in CANDIDATES for criterion in SELECTION_UNITS]
        reports += [COMMITTED_CONFORMANCE + conformance_name(criterion)
                    for criterion in CONFORMANCE_UNITS]
        expected = sorted(PACKAGE + "/" + name for name in
                          ["build_record.py", "demonstration.md", "design-evidence.json",
                           "probe.py", "runbook.md", "study.md", *reports])
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
        self.assertEqual(PROBE.SELECTION_UNITS, SELECTION_UNITS)
        self.assertEqual(PROBE.CONFORMANCE_UNITS, CONFORMANCE_UNITS)
        self.assertEqual(PROBE.REPORT_SCHEMA, "protasis-design-report/v1")
        self.assertEqual(BUILDER.SELECTED, SELECTED)
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
                                  "restore-contention-guarded", "--root", str(base),
                                  "--out", str(path)],
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
        command = "python3 .hexaemeron/design/probe.py conform"
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            PROBE.write_report(str(out), SELECTED, "killed-restore-recovers", True,
                               "boolean", command)
        data = out.read_bytes()
        self.assertEqual(json.loads(data), {
            "schema": "protasis-design-report/v1", "candidate": SELECTED,
            "criterion": "killed-restore-recovers", "value": True, "unit": "boolean",
            "command": command, "exit": 0})
        self.assertEqual(printed.getvalue(), data.decode("utf-8"))
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            PROBE.write_report(str(out), SELECTED, "killed-restore-recovers", False,
                               "boolean", command)
        self.assertEqual(out.read_bytes(), data)

    def test_conform_without_the_built_module_reports_false(self):
        base = scratch(self)
        out = base / "report.json"
        for criterion in CONFORMANCE_UNITS:
            with self.subTest(criterion=criterion):
                completed = run_script("probe.py", base, "conform", "--candidate", SELECTED,
                                       "--criterion", criterion, "--root", str(base),
                                       "--out", str(out))
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = json.loads(out.read_bytes())
                self.assertIs(report["value"], False)
                self.assertEqual(completed.stdout, out.read_text(encoding="utf-8"))
                self.assertEqual(set(snapshot(base)), {"report.json"})
                out.unlink()

    def test_probe_arguments_outside_the_closed_set_refuse(self):
        base = scratch(self)
        out = str(base / "report.json")
        for argv in ([], ["measure"],
                     ["select", "--candidate", SELECTED, "--criterion",
                      "lock-acquisitions-per-restore"],
                     ["select", "--candidate", "no-such-candidate", "--criterion",
                      "lock-acquisitions-per-restore", "--out", out],
                     ["select", "--candidate", SELECTED, "--criterion",
                      "restore-contention-guarded", "--out", out],
                     ["conform", "--candidate", SELECTED, "--criterion",
                      "lock-acquisitions-per-restore", "--root", str(base), "--out", out],
                     ["conform", "--candidate", SELECTED, "--criterion",
                      "restore-contention-guarded", "--out", out]):
            with self.subTest(argv=argv):
                completed = run_script("probe.py", base, *argv)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("usage:", completed.stderr)
                self.assertEqual(snapshot(base), {})

    def test_builder_without_reports_writes_nothing(self):
        base = scratch(self)
        completed = run_script("build_record.py", base, "--out", str(base / "design-evidence.json"))
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(snapshot(base), {})


if __name__ == "__main__":
    unittest.main()
