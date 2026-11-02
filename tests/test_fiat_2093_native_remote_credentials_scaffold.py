"""Check the skills#2093 design home: receipted copies, selection evidence, draft."""
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
PACKAGE = "docs/fiat-2093-native-remote-credentials"
# The receipted bytes: the study accepted on 2026-11-02, the runbook receipted
# the same day, and the design record its design-lock block names.
RECEIPTED = {
    "study.md": "340e034f92da6ebe8339542b8667b8f0161e82a804ca715c43af1ada31700014",
    "runbook.md": "19f8c82c793a9254ea6197f9e9db4e57e93ad7f3e86cb0e74e9326d00944cff7",
    "design-evidence.json": "2dc559a0b230d436e16f215a47b612a0b03b5d0fc1d832aa2c7f0bc8b6709184",
}
# The probe and record builder digests the study's Sources section pins.
PINNED_SCRIPTS = {
    "probe.py": "0e9dbe397faa4ec3ef92d33a0d8c417a9875c0a015fd401d72e6d2c78a4816df",
    "build_record.py": "74f70a666ce268c4e625cdb324b5e74ebc83c61a6f3ffb8ea5a5862f21f390db",
}
DRAFT = "docs/decisions/drafts/admit-caller-credentials-to-native-remote-reads.md"
SELECTOR = "adr/" + Path(DRAFT).stem
SELECTED = "credential-scope-projection"
CANDIDATES = ("credential-scope-projection", "github-rest-tip",
              "credential-fill-relay", "native-unchanged")
SELECTION_UNITS = {
    "global-credential-read": "boolean",
    "moved-tip-detected": "boolean",
    "global-insteadof-inert": "boolean",
    "ambient-substitution-inert": "boolean",
    "controller-holds-no-credential": "boolean",
    "authentication-refusal-named": "boolean",
    "child-processes-per-read": "count",
    "buffered-bytes-per-read": "bytes",
    "helper-shapes-authenticated": "count",
}
CONFORMANCE_UNITS = {
    "seam-reads-credentialed-remote": "boolean",
    "sync-run-module-passes": "boolean",
    "local-reads-stay-native": "boolean",
    "projection-cap-refuses": "boolean",
    "authentication-refusal-fixed": "boolean",
    "remote-read-children": "count",
}
# The study's section 4.3 table, one value per candidate in CANDIDATES order.
MEASURED = {
    "global-credential-read": (True, False, True, False),
    "moved-tip-detected": (True, False, True, False),
    "global-insteadof-inert": (True, False, True, False),
    "ambient-substitution-inert": (True, False, True, True),
    "controller-holds-no-credential": (True, True, False, True),
    "authentication-refusal-named": (True, True, True, False),
    "child-processes-per-read": (2, 2, 3, 1),
    "buffered-bytes-per-read": (263, 73, 192, 87),
    "helper-shapes-authenticated": (4, 0, 6, 0),
}
# The record's report paths stay relative to .hexaemeron/, where it was built;
# the runbook publishes the same reports one directory shallower.
RECORD_REPORTS = "design/reports/selection/"
COMMITTED_REPORTS = "reports/selection/"
# Names the conformance resolvers bind in the controller and its tests.
PROBE_BINDINGS = ("remote_branch_tip", "_native_relation_environment", "_native_relation_commit",
                  '"test_native_remote_credentials.py"', "sync_run", "authentication",
                  "credential configuration")
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


PROBE = load(PACKAGE + "/probe.py", "fiat_2093_native_remote_credentials_probe")
BUILDER = load(PACKAGE + "/build_record.py", "fiat_2093_native_remote_credentials_builder")
DESIGN = load("plugins/hexaemeron/skills/protasis/scripts/design_evidence.py",
              "fiat_2093_native_remote_credentials_design_checker")
BRIDGE = load("plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py",
              "fiat_2093_native_remote_credentials_bridge_checker")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record():
    return json.loads((ROOT / PACKAGE / "design-evidence.json").read_bytes())


def selection_rows():
    return [row for row in record()["results"] if isinstance(row["report"], dict)]


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
    directory = tempfile.TemporaryDirectory(prefix="fiat-2093-scaffold-")
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
    return subprocess.run(  # phylax: allow subprocess: fixed argv interpreter, no shell
        [sys.executable, "-I", "-B", str(ROOT / PACKAGE / name), *argv],
        cwd=cwd, capture_output=True, text=True, timeout=120, check=False)


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

    def test_study_pins_the_probe_and_builder_it_was_measured_with(self):
        text = (ROOT / PACKAGE / "study.md").read_text(encoding="utf-8")
        for name, expected in PINNED_SCRIPTS.items():
            with self.subTest(name=name):
                self.assertIn("`.hexaemeron/design/" + name + "` (SHA-256\n  `" + expected + "`)",
                              text)

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
                self.assertEqual(digest(path), reference["sha256"])
                report = json.loads(path.read_bytes())
                self.assertEqual(report, {
                    "schema": "protasis-design-report/v1", "candidate": row["candidate"],
                    "criterion": row["criterion"], "value": report["value"],
                    "unit": SELECTION_UNITS[row["criterion"]], "exit": 0,
                    "command": "python3 .hexaemeron/design/probe.py select --candidate "
                               + row["candidate"] + " --criterion " + row["criterion"]
                               + " --out .hexaemeron/" + RECORD_REPORTS + name})
        committed = {path.name for path in (ROOT / PACKAGE / COMMITTED_REPORTS).iterdir()}
        self.assertEqual(committed, {Path(row["report"]["path"]).name for row in rows})

    def test_report_values_match_the_study_and_draft_tables(self):
        values = {}
        for row in selection_rows():
            report = json.loads((ROOT / PACKAGE / COMMITTED_REPORTS
                                 / Path(row["report"]["path"]).name).read_bytes())
            values[(row["candidate"], row["criterion"])] = report["value"]
        study = (ROOT / PACKAGE / "study.md").read_text(encoding="utf-8")
        _, home, error = BRIDGE._read_stable_adr(ROOT, SELECTOR)
        self.assertIsNone(error)
        draft = (ROOT / home).read_text(encoding="utf-8")
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
        self.assertEqual(bridge["record"], SELECTOR)
        raw, home, error = BRIDGE._read_stable_adr(ROOT, SELECTOR)
        self.assertIsNone(error)
        self.assertIsNotNone(raw)
        self.assertIsNotNone(home)
        text = raw.decode("utf-8")
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

    def test_draft_writes_down_the_secret_exposure_limit(self):
        """The study's secret-exposure row owes its inline-secret limit a home."""
        study = (ROOT / PACKAGE / "study.md").read_text(encoding="utf-8")
        fence = study.split("```risk-register\n", 1)[1].split("\n```", 1)[0]
        rows = {line.split(" | ")[0]: line.split(" | ") for line in fence.splitlines()}
        self.assertIn("embeds a secret inline", rows["secret-exposure"][2])
        _, home, error = BRIDGE._read_stable_adr(ROOT, SELECTOR)
        self.assertIsNone(error)
        draft = (ROOT / home).read_text(encoding="utf-8")
        consequences = draft.split("\n## Consequences\n", 1)[1]
        self.assertIn("embeds a secret inline", consequences)
        # Every projected credential.* entry is replayed, not only helpers.
        self.assertNotIn("only helper strings travel", draft)


class TrackedContentTests(unittest.TestCase):
    def test_only_the_named_copies_are_tracked(self):
        reports = [COMMITTED_REPORTS + candidate + "-" + criterion + ".json"
                   for candidate in CANDIDATES for criterion in SELECTION_UNITS]
        expected = sorted(PACKAGE + "/" + name for name in
                          ["build_record.py", "design-evidence.json", "probe.py", "runbook.md",
                           "study.md", *reports])
        self.assertEqual(tracked(PACKAGE), expected)
        self.assertEqual(tracked(".hexaemeron"), [])
        _, home, error = BRIDGE._read_stable_adr(ROOT, SELECTOR)
        self.assertIsNone(error)
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
        self.assertEqual(BUILDER.SELECTED, SELECTED)
        self.assertEqual(tuple(item["id"] for item in BUILDER.CANDIDATES), CANDIDATES)
        self.assertEqual({item[0]: item[4] for item in BUILDER.SELECTION}, SELECTION_UNITS)
        self.assertEqual({item[0]: item[3] for item in BUILDER.CONFORMANCE}, CONFORMANCE_UNITS)

    def test_scripts_hold_no_local_path(self):
        for name in PINNED_SCRIPTS:
            data = (ROOT / PACKAGE / name).read_bytes()
            for marker in LOCAL_PATH_MARKERS:
                with self.subTest(name=name, marker=marker):
                    self.assertNotIn(marker, data)

    def test_probe_keeps_the_bindings_the_runbook_names(self):
        text = (ROOT / PACKAGE / "probe.py").read_text(encoding="utf-8")
        for token in PROBE_BINDINGS:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_existing_out_is_refused_and_preserved(self):
        base = scratch(self)
        report = base / "report.json"
        report.write_bytes(b"previous report\n")
        target = base / "keep.json"
        target.write_bytes(b"keep\n")
        link = base / "link.json"
        link.symlink_to(target)
        for path in (report, link):
            for name, argv in (
                    ("probe.py", ["select", "--candidate", SELECTED, "--criterion",
                                  "global-credential-read", "--out", str(path)]),
                    ("probe.py", ["conform", "--candidate", SELECTED, "--criterion",
                                  "remote-read-children", "--root", str(base), "--out", str(path)]),
                    ("build_record.py", ["--out", str(path)])):
                with self.subTest(path=path.name, script=name, mode=argv[0]):
                    before = snapshot(base)
                    completed = run_script(name, base, *argv)
                    self.assertEqual(completed.returncode, 2)
                    self.assertIn("--out must not already exist", completed.stderr)
                    self.assertEqual(completed.stdout, "")
                    self.assertEqual(snapshot(base), before)
        self.assertEqual(report.read_bytes(), b"previous report\n")
        self.assertEqual(target.read_bytes(), b"keep\n")

    def test_probe_report_write_is_create_only(self):
        base = scratch(self)
        out = base / "nested" / "report.json"
        report = {"schema": "protasis-design-report/v1", "candidate": SELECTED,
                  "criterion": "remote-read-children", "value": 2, "unit": "count",
                  "command": "python3 .hexaemeron/design/probe.py conform", "exit": 0}
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            PROBE.write_report(out, report)
        data = out.read_bytes()
        self.assertEqual(json.loads(data), report)
        self.assertIn("sha256 " + hashlib.sha256(data).hexdigest() + "\n", printed.getvalue())
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(FileExistsError):
            PROBE.write_report(out, dict(report, value=3))
        self.assertEqual(out.read_bytes(), data)

    def test_probe_arguments_outside_the_closed_set_refuse(self):
        base = scratch(self)
        out = str(base / "report.json")
        for argv in ([], ["measure"],
                     ["select", "--candidate", SELECTED, "--criterion", "global-credential-read"],
                     ["select", "--candidate", "no-such-candidate", "--criterion",
                      "global-credential-read", "--out", out],
                     ["select", "--candidate", SELECTED, "--criterion",
                      "remote-read-children", "--out", out],
                     ["conform", "--candidate", SELECTED, "--criterion",
                      "global-credential-read", "--root", str(base), "--out", out],
                     ["conform", "--candidate", SELECTED, "--criterion",
                      "remote-read-children", "--out", out]):
            with self.subTest(argv=argv):
                completed = run_script("probe.py", base, *argv)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("usage:", completed.stderr)
                self.assertEqual(snapshot(base), {})

    def test_probe_conform_refuses_a_candidate_with_no_built_surface(self):
        base = scratch(self)
        for candidate in CANDIDATES[1:]:
            with self.subTest(candidate=candidate):
                completed = run_script("probe.py", base, "conform", "--candidate", candidate,
                                       "--criterion", "remote-read-children", "--root",
                                       str(base), "--out", str(base / "report.json"))
                self.assertEqual(completed.returncode, 2)
                self.assertIn("only " + SELECTED + " is built", completed.stderr)
                self.assertEqual(snapshot(base), {})

    def test_builder_without_reports_writes_nothing(self):
        base = scratch(self)
        completed = run_script("build_record.py", base, "--out", str(base / "design-evidence.json"))
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(snapshot(base), {})


if __name__ == "__main__":
    unittest.main()
