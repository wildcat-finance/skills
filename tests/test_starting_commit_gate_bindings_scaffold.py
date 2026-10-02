"""Check the skills#2042 design home: receipted copies, selection evidence, draft."""
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


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "docs/starting-commit-gate-bindings"
# The receipted bytes: the study accepted on 2026-09-30, the runbook receipted
# the same day, and the design record locked before the runbook.
RECEIPTED = {
    "study.md": "6a72a1fa4a3e0912f6cd4e10eac8edd1c76cc5e0d4535b0e81a163279da3799c",
    "runbook.md": "909e4b946b1ee45890a2467583d519023dda271800d2025be519dc0c5f6eef38",
    "design-evidence.json": "dba6eeaf5b5de4585edd2cc9e33a663599b6ec65a030d8379ada57421055cb8b",
}
# Observed when Step 1 copied .hexaemeron/design/resolve.py; no receipt binds it.
RESOLVER_SHA256 = "66f27615a251b84b50f4a3c90f527f0a52db09a74138e9db4e74add104d2474c"
DRAFT = "docs/decisions/drafts/admit-starting-commit-gate-bindings.md"
SELECTED = "base-commit-bindings"
CANDIDATES = ("base-commit-bindings", "reviewed-prior-pins",
              "runbook-scoped-pins", "recorded-controller-fork")
SELECTION_UNITS = {
    "main-controller-replays-1872": "boolean",
    "edited-module-refuses": "boolean",
    "unknown-adapter-refuses": "boolean",
    "verify-writes-no-state": "bytes",
    "verify-wall-ms": "milliseconds",
    "reviewed-rows-per-release": "count",
}
# Each pending conformance cell and the script the runbook has a later step create.
CONFORMANCE_RESOLVERS = {
    "older-controller-supersession-fixture":
        "plugins/hexaemeron/tests/fiat_starting_commit_bindings_proof.py",
    "base-commit-controller-demonstration": PACKAGE + "/demonstrate.py",
    "released-adapter-tests-green":
        "plugins/hexaemeron/tests/fiat_starting_commit_bindings_proof.py",
}
# The snapshot the resolver reads holds local paths and another run's state, so
# it stays untracked; these path parts must never appear in the index.
UNTRACKED_PARTS = {"fixtures", "evidence", "run-1872", "__pycache__"}


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


RESOLVER = load(PACKAGE + "/resolve.py", "starting_commit_bindings_resolver")
DESIGN = load("plugins/hexaemeron/skills/protasis/scripts/design_evidence.py",
              "starting_commit_bindings_design_checker")
BRIDGE = load("plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py",
              "starting_commit_bindings_bridge_checker")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record():
    return json.loads((ROOT / PACKAGE / "design-evidence.json").read_bytes())


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


class PublishedDesignHomeTests(unittest.TestCase):
    def test_copies_equal_their_receipted_bytes(self):
        for name, expected in RECEIPTED.items():
            with self.subTest(name=name):
                self.assertEqual(digest(ROOT / PACKAGE / name), expected)
        self.assertEqual(digest(ROOT / PACKAGE / "resolve.py"), RESOLVER_SHA256)

    def test_runbook_copy_locks_the_committed_record(self):
        text = (ROOT / PACKAGE / "runbook.md").read_text(encoding="utf-8")
        self.assertIn("```design-lock\nschema | protasis-design-evidence/v1\nsha256 | "
                      + RECEIPTED["design-evidence.json"] + "\ncandidate | " + SELECTED
                      + "\n```", text)
        self.assertIn("SHA-256 `" + RECEIPTED["study.md"] + "`", text)

    def test_each_selection_report_equals_its_recorded_digest(self):
        resolved = [row for row in record()["results"] if isinstance(row["report"], dict)]
        self.assertEqual(len(resolved), 24)
        for row in resolved:
            reference = row["report"]
            with self.subTest(path=reference["path"]):
                path = ROOT / PACKAGE / reference["path"]
                self.assertEqual(digest(path), reference["sha256"])
                report = json.loads(path.read_bytes())
                self.assertEqual(report, {
                    "schema": "protasis-design-report/v1", "candidate": row["candidate"],
                    "criterion": row["criterion"], "value": report["value"],
                    "unit": SELECTION_UNITS[row["criterion"]], "exit": 0,
                    "command": "python3 .hexaemeron/design/resolve.py --candidate "
                               + row["candidate"] + " --criterion " + row["criterion"]
                               + " --report .hexaemeron/reports/design/" + row["candidate"]
                               + "-" + row["criterion"] + ".json"})
                self.assertEqual(path.name, row["candidate"] + "-" + row["criterion"] + ".json")
        committed = {path.name for path in (ROOT / PACKAGE / "reports/design").iterdir()}
        self.assertEqual(committed, {Path(row["report"]["path"]).name for row in resolved})

    def test_committed_record_locks_the_selected_design(self):
        findings, admitted, _ = DESIGN.evaluate(ROOT / PACKAGE / "design-evidence.json",
                                                "design-lock")
        self.assertEqual(findings, [])
        self.assertEqual(admitted["selection"], {"candidate": SELECTED, "policy_ref": None,
                                                 "rule": "unique-frontier"})
        self.assertEqual(tuple(item["id"] for item in admitted["candidates"]), CANDIDATES)
        selection = {item["id"]: item["unit"] for item in admitted["criteria"]
                     if item["stage"] == "selection"}
        self.assertEqual(selection, SELECTION_UNITS)

    def test_pending_conformance_cells_name_the_scripts_later_steps_create(self):
        admitted = record()
        conformance = {item["id"] for item in admitted["criteria"]
                       if item["stage"] == "conformance"}
        self.assertEqual(conformance, set(CONFORMANCE_RESOLVERS))
        for candidate in CANDIDATES:
            cells = {row["criterion"]: row for row in admitted["results"]
                     if row["candidate"] == candidate and row["state"] == "pending"}
            self.assertEqual(set(cells), conformance)
            for criterion, row in cells.items():
                with self.subTest(candidate=candidate, criterion=criterion):
                    report = ".hexaemeron/reports/design/" + candidate + "-" + criterion + ".json"
                    self.assertEqual(row["blocks"], "integration")
                    self.assertEqual(".hexaemeron/" + row["report"], report)
                    self.assertEqual(row["resolver"], "python3 " + CONFORMANCE_RESOLVERS[criterion]
                                     + " --candidate " + candidate + " --criterion " + criterion
                                     + " --report " + report)

    def test_decision_draft_resolves_through_the_study_bridge(self):
        study = PACKAGE + "/study.md"
        self.assertEqual(BRIDGE.check_design_bridge(study, PACKAGE + "/design-evidence.json", ROOT),
                         [])
        bridge, _, error = BRIDGE._design_bridge_block(
            (ROOT / study).read_text(encoding="utf-8").splitlines())
        self.assertIsNone(error)
        self.assertEqual(bridge["decision"], SELECTED)
        self.assertEqual(bridge["record"], DRAFT)
        text = (ROOT / DRAFT).read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Decision: "))
        self.assertIn("`" + SELECTED + "`", text)
        for alternative in CANDIDATES[1:]:
            self.assertIn("`" + alternative + "`", text)
        _, home, error = BRIDGE._read_stable_adr(ROOT, "adr/" + Path(DRAFT).stem)
        self.assertIsNone(error)
        self.assertEqual(home.as_posix(), DRAFT)
        # The command the runbook's Step 1 Exit names, run in process.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = BRIDGE.main(["--study", study, "--design-evidence",
                                PACKAGE + "/design-evidence.json", "--repo-root", str(ROOT)])
        self.assertEqual(code, 0)


class TrackedContentTests(unittest.TestCase):
    def test_only_the_named_copies_are_tracked_and_no_snapshot_is(self):
        reports = ["reports/design/" + candidate + "-" + criterion + ".json"
                   for candidate in CANDIDATES for criterion in SELECTION_UNITS]
        expected = sorted(PACKAGE + "/" + name for name in
                          ["design-evidence.json", "resolve.py", "runbook.md", "study.md", *reports])
        self.assertEqual(tracked(PACKAGE), expected)
        self.assertEqual(tracked(".hexaemeron"), [])
        self.assertEqual(tracked(DRAFT), [DRAFT])
        offending = [path for path in tracked()
                     if "run-1872" in Path(path).parts
                     or (path.startswith(PACKAGE + "/")
                         and (UNTRACKED_PARTS & set(Path(path).parts)
                              or Path(path).name in ("state.json", "ledger.jsonl")))]
        self.assertEqual(offending, [])
        for name in ("fixtures", "evidence"):
            with self.subTest(name=name):
                self.assertFalse((ROOT / PACKAGE / name).exists())


class ResolverCopyTests(unittest.TestCase):
    """The copied resolver keeps its closed arguments and creates reports exclusively."""

    def scratch(self):
        directory = tempfile.TemporaryDirectory(prefix="starting-commit-bindings-scaffold-")
        self.addCleanup(directory.cleanup)
        return Path(directory.name).resolve()

    def run_resolver(self, cwd, *argv):
        return subprocess.run(  # phylax: allow subprocess: fixed argv interpreter, no shell
            [sys.executable, "-I", "-B", str(ROOT / PACKAGE / "resolve.py"), *argv],
            cwd=cwd, capture_output=True, text=True, timeout=120, check=False)

    def test_resolver_constants_match_the_record(self):
        self.assertEqual(RESOLVER.CANDIDATES, CANDIDATES)
        self.assertEqual(RESOLVER.CRITERIA, SELECTION_UNITS)
        self.assertEqual(RESOLVER.ROOT, ROOT)
        self.assertEqual(RESOLVER.FIXTURE, ROOT / PACKAGE / "fixtures" / "run-1872")
        self.assertEqual(RESOLVER.BASE_CONTROLLER[RESOLVER.ADAPTER],
                         "ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119")
        self.assertEqual(RESOLVER.LITERAL_ADAPTER, RESOLVER.BASE_CONTROLLER[RESOLVER.ADAPTER])
        self.assertEqual(RESOLVER.RUN_HEAD, "5d5ec5e142d83140a0967fe13ad3498df3df2015")

    def test_absent_snapshot_refuses_before_any_write(self):
        self.assertFalse(RESOLVER.FIXTURE.exists())
        scratch = self.scratch()
        before = snapshot(ROOT / PACKAGE)
        completed = self.run_resolver(scratch, "--candidate", SELECTED, "--criterion",
                                      "verify-wall-ms", "--report", str(scratch / "report.json"))
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(completed.stderr.startswith("refused: "), completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(snapshot(ROOT / PACKAGE), before)
        self.assertEqual(snapshot(scratch), {})

    def test_existing_report_is_refused_and_preserved(self):
        scratch = self.scratch()
        report = scratch / "report.json"
        report.write_bytes(b"previous report\n")
        target = scratch / "keep.json"
        target.write_bytes(b"keep\n")
        link = scratch / "link.json"
        link.symlink_to(target)
        for path in (report, link):
            with self.subTest(path=path.name):
                before = snapshot(scratch)
                completed = self.run_resolver(scratch, "--candidate", SELECTED, "--criterion",
                                              "verify-wall-ms", "--report", str(path))
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(completed.stderr, "report-already-exists\n")
                self.assertEqual(snapshot(scratch), before)
        self.assertEqual(target.read_bytes(), b"keep\n")

    def test_arguments_outside_the_closed_set_refuse(self):
        scratch = self.scratch()
        base = ["--candidate", SELECTED, "--criterion", "verify-wall-ms",
                "--report", str(scratch / "report.json")]
        for argv in ([], base[:4], base + ["--extra", "x"],
                     ["--candidate", "no-such-candidate"] + base[2:],
                     base[:2] + ["--criterion", "replay-milliseconds"] + base[4:]):
            with self.subTest(argv=argv):
                completed = self.run_resolver(scratch, *argv)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("usage:", completed.stderr)
                self.assertEqual(snapshot(scratch), {})


if __name__ == "__main__":
    unittest.main()
