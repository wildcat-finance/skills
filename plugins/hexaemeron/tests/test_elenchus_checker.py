"""Elenchus classifies guards from real runner-owned reports."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "elenchus" / "scripts" / "elenchus.py"
RUN_TESTS = ROOT / "tests" / "run_tests.py"

spec = importlib.util.spec_from_file_location("elenchus_guard", SCRIPT)
elenchus = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = elenchus
spec.loader.exec_module(elenchus)

runner_spec = importlib.util.spec_from_file_location(
    "hexaemeron_test_runner", RUN_TESTS
)
hexaemeron_runner = importlib.util.module_from_spec(runner_spec)
runner_spec.loader.exec_module(hexaemeron_runner)

REPORT_FILE = ".elenchus/report"

UNITTEST_EMITTER = '''\
import json
import os
from pathlib import Path
import sys
import unittest

suite = unittest.defaultTestLoader.discover(".", pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=1).run(suite)
payload = {
    "schema": "elenchus.unittest.v1",
    "complete": True,
    "testsRun": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "skipped": len(result.skipped),
    "expectedFailures": len(result.expectedFailures),
    "unexpectedSuccesses": len(result.unexpectedSuccesses),
}
target = Path(sys.argv[1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(payload), encoding="utf-8")
if "--exit-zero" not in sys.argv:
    raise SystemExit(not result.wasSuccessful())
'''

FORGE_EMITTER = '''\
import os
from pathlib import Path
import sys

target = Path(sys.argv[1])
target.parent.mkdir(parents=True, exist_ok=True)
descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
os.dup2(descriptor, sys.stdout.fileno())
os.close(descriptor)
os.execv(sys.argv[2], [sys.argv[2], "test", "--junit"])
'''

NODE_EMITTER = '''\
import { run } from "node:test";
import { writeFile } from "node:fs/promises";

console.error("ModuleNotFoundError AssertionError");
const counts = { executed: 0, assertionFailures: 0, errors: 0, skipped: 0 };
const stream = run({ files: ["test_adder.mjs"], isolation: "none" });
stream.on("test:pass", (data) => {
  if (data.skip || data.todo) counts.skipped += 1;
  else counts.executed += 1;
});
stream.on("test:fail", (data) => {
  counts.executed += 1;
  const wrapped = data.details?.error;
  const cause = wrapped?.cause ?? wrapped;
  if (cause?.code === "ERR_ASSERTION" || cause?.name === "AssertionError") {
    counts.assertionFailures += 1;
  } else {
    counts.errors += 1;
  }
});
const finished = new Promise((resolve, reject) => {
  stream.on("end", resolve);
  stream.on("error", reject);
});
stream.resume();
await finished;
await writeFile(process.argv[2], JSON.stringify({
  schema: "elenchus.node-test.v1",
  complete: true,
  ...counts,
}));
process.exitCode = counts.assertionFailures + counts.errors > 0 ? 1 : 0;
'''


def replace_runner_ancestor(real_run, ancestor, malicious_source):
    """Keep a replacement ancestor installed for the complete guarded run."""
    held = ancestor.with_name(f"{ancestor.name}-held")

    def run_with_replacement(command, *args, **kwargs):
        ancestor.rename(held)
        ancestor.mkdir()
        replacement = ancestor / "runner"
        replacement.write_text(malicious_source, encoding="utf-8")
        replacement.chmod(0o755)
        try:
            return real_run(command, *args, **kwargs)
        finally:
            shutil.rmtree(ancestor)
            held.rename(ancestor)

    return run_with_replacement


class Fixture:
    """A real temporary git history with independent children of one base."""

    def __init__(self, base_files):
        self.path = Path(tempfile.mkdtemp(prefix="elenchus-fixture-"))
        self.run("init", "--quiet", "-b", "main")
        self.run("config", "--local", "commit.gpgsign", "false")
        self.run("config", "user.email", "fixture@example.org")
        self.run("config", "user.name", "Fixture")
        self.base = self.commit("base", base_files)

    def run(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def commit(self, message, files):
        for name, body in files.items():
            target = self.path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(body, bytes):
                target.write_bytes(body)
            else:
                target.write_text(body, encoding="utf-8")
        self.run("add", "-A")
        self.run("-c", "commit.gpgsign=false", "commit", "--quiet", "-m", message)
        return self.run("rev-parse", "HEAD").strip()

    def child(self, message, files):
        self.run("checkout", "--quiet", "--detach", self.base)
        return self.commit(message, files)

    def status(self):
        return self.run("status", "--short")

    def worktrees(self):
        return self.run("worktree", "list", "--porcelain")

    def destroy(self):
        shutil.rmtree(self.path, ignore_errors=True)


class RunnerCase(unittest.TestCase):
    fixture = None
    command = None
    report_format = None

    @classmethod
    def tearDownClass(cls):
        if cls.fixture is not None:
            cls.fixture.destroy()

    def outcome(self, ref, command=None, **kwargs):
        before = self.fixture.status()
        result = elenchus.check(
            self.fixture.path,
            ref,
            command or self.command,
            timeout=kwargs.pop("timeout", 120),
            report_format=kwargs.pop("report_format", self.report_format),
            report_file=kwargs.pop("report_file", REPORT_FILE),
            **kwargs,
        )
        self.assertEqual(before, self.fixture.status())
        return result


class UnittestReports(RunnerCase):
    @classmethod
    def setUpClass(cls):
        cls.command = [sys.executable, "emit_unittest.py", "{report}"]
        cls.report_format = "unittest-json-v1"
        cls.fixture = Fixture({
            "adder.py": "def add(a, b):\n    return a - b\n",
            "emit_unittest.py": UNITTEST_EMITTER,
        })
        f = cls.fixture
        cls.guarded = f.child("guarded", {
            "test_adder.py": (
                "import unittest\nfrom adder import add\n\n"
                "class T(unittest.TestCase):\n"
                "    def test_it_adds(self):\n"
                "        self.assertEqual(add(2, 2), 4, 'ModuleNotFoundError')\n"
            ),
        })
        cls.passed = f.child("passed", {
            "test_arithmetic.py": (
                "import unittest\n\nclass T(unittest.TestCase):\n"
                "    def test_arithmetic(self):\n        self.assertEqual(1 + 1, 2)\n"
            ),
        })
        cls.broken = f.child("broken", {
            "test_broken.py": "raise RuntimeError('AssertionError')\n",
        })
        cls.unguarded = f.child("unguarded", {"adder.py": "def add(a, b):\n    return a + b\n"})

    def test_runner_categories_distinguish_all_three_outcomes(self):
        self.assertEqual("guarded", self.outcome(self.guarded)["status"])
        self.assertEqual("passed", self.outcome(self.passed)["status"])
        self.assertEqual("inconclusive", self.outcome(self.broken)["status"])

    def test_diagnostic_poisoning_and_exit_code_do_not_change_the_report(self):
        ordinary = self.outcome(self.guarded)
        forced_zero = self.outcome(
            self.guarded,
            [sys.executable, "emit_unittest.py", "{report}", "--exit-zero"],
        )
        self.assertEqual("guarded", ordinary["status"])
        self.assertEqual("guarded", forced_zero["status"])
        self.assertNotEqual(ordinary["exit_code"], forced_zero["exit_code"])
        self.assertIn("ModuleNotFoundError", ordinary["output"])
        self.assertIn("AssertionError", self.outcome(self.broken)["output"])

    def test_legacy_runner_output_capture_is_bounded(self):
        guarded = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        result = self.outcome(self.guarded, [
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; "
            "sys.stdout.write('o'*2000000); sys.stderr.write('e'*2000000); "
            "p=Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True); "
            f"p.write_text({guarded!r}, encoding='utf-8')",
            "{report}",
        ])
        self.assertEqual("guarded", result["status"])
        self.assertLessEqual(len(result["output"]), elenchus.MAX_DIAGNOSTIC_CHARS)

    def test_legacy_runner_uses_the_closed_environment(self):
        guarded = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        script = (
            "from pathlib import Path; import os,sys; "
            "assert 'ELENCHUS_CALLER_VALUE' not in os.environ; "
            "p=Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True); "
            f"p.write_text({guarded!r}, encoding='utf-8')"
        )
        with mock.patch.dict(
            os.environ, {"ELENCHUS_CALLER_VALUE": "must-not-cross"}, clear=False
        ):
            result = self.outcome(
                self.guarded, [sys.executable, "-c", script, "{report}"]
            )
        self.assertEqual("guarded", result["status"])

    def test_legacy_runner_cannot_leave_an_escaped_descendant(self):
        with tempfile.TemporaryDirectory(prefix="elenchus-legacy-descendant-") as directory:
            marker = Path(directory) / "survived"
            child = (
                "from pathlib import Path; import signal,time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "time.sleep(2); "
                f"Path({str(marker)!r}).write_text('survived', encoding='utf-8')"
            )
            parent = (
                "import subprocess,sys; "
                f"subprocess.Popen([sys.executable, '-c', {child!r}], "
                "start_new_session=True)"
            )
            result = self.outcome(
                self.guarded,
                [sys.executable, "-c", parent, "{report}"],
                timeout=3,
            )
            self.assertEqual("inconclusive", result["status"])
            self.assertRegex(
                result["output"],
                "PermissionError|BlockingIOError|Operation not permitted|"
                "Resource temporarily unavailable",
            )
            time.sleep(2.25)
            self.assertFalse(marker.exists())

    def test_legacy_runner_rejects_an_executable_changed_during_the_run(self):
        guarded = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        with tempfile.TemporaryDirectory(prefix="elenchus-mutating-runner-") as directory:
            runner = Path(directory) / "runner"
            runner.write_text(
                f"#!{sys.executable}\n"
                "from pathlib import Path\n"
                "import sys\n"
                "source = Path(sys.argv[0])\n"
                "source.write_text(source.read_text(encoding='utf-8') + "
                "'# changed\\n', encoding='utf-8')\n"
                "target = Path(sys.argv[1])\n"
                "target.parent.mkdir(parents=True, exist_ok=True)\n"
                f"target.write_text({guarded!r}, encoding='utf-8')\n",
                encoding="utf-8",
            )
            runner.chmod(0o755)
            result = self.outcome(self.guarded, [str(runner), "{report}"])
        self.assertEqual("inconclusive", result["status"])
        self.assertIn("executable changed", result["detail"])

    def test_legacy_runner_ancestor_substitution_cannot_execute_replacement(self):
        guarded = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        with tempfile.TemporaryDirectory(prefix="elenchus-runner-parent-") as directory:
            ancestor = Path(directory) / "bin"
            ancestor.mkdir()
            runner = ancestor / "runner"
            runner.write_text(
                f"#!{sys.executable}\n"
                "from pathlib import Path\n"
                "import sys\n"
                "target = Path(sys.argv[1])\n"
                "target.parent.mkdir(parents=True, exist_ok=True)\n"
                f"target.write_text({guarded!r}, encoding='utf-8')\n",
                encoding="utf-8",
            )
            runner.chmod(0o755)
            marker = Path(directory) / "replacement-ran"
            malicious = (
                f"#!{sys.executable}\n"
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('ran', encoding='utf-8')\n"
            )
            real_run = elenchus._run_guard_command
            with mock.patch.object(
                elenchus,
                "_run_guard_command",
                side_effect=replace_runner_ancestor(
                    real_run, ancestor, malicious
                ),
            ):
                result = self.outcome(
                    self.guarded, [str(runner), "{report}"]
                )
            replacement_ran = marker.exists()
        if sys.platform == "linux":
            self.assertEqual("guarded", result["status"])
        else:
            self.assertEqual("inconclusive", result["status"])
        self.assertFalse(replacement_ran)

    def test_legacy_no_report_is_inconclusive(self):
        result = elenchus.check(
            self.fixture.path, self.guarded, self.command, timeout=120
        )
        self.assertEqual("inconclusive", result["status"])

    def test_legacy_cli_is_nonfatal_by_default_and_fails_when_required(self):
        argv = [
            "--repo", str(self.fixture.path), "--ref", self.guarded,
            "--test-command", f"{sys.executable} emit_unittest.py {{report}}",
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, elenchus.main(argv))
            self.assertEqual(1, elenchus.main(argv + ["--require-guard"]))

    def test_unsafe_and_tracked_report_paths_fail_closed(self):
        traversal = self.outcome(self.guarded, report_file="../report")
        tracked = self.outcome(self.guarded, report_file="adder.py")
        self.assertEqual("inconclusive", traversal["status"])
        self.assertEqual("inconclusive", tracked["status"])

    def test_report_ownership_is_an_explicit_command_argument(self):
        no_placeholder = self.outcome(
            self.guarded, [sys.executable, "emit_unittest.py"]
        )
        payload = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        inherited_writer = (
            "import os; from pathlib import Path; "
            f"value={payload!r}; target=os.environ.get('ELENCHUS_REPORT_FILE'); "
            "target and Path(target).write_text(value, encoding='utf-8')"
        )
        with mock.patch.dict(os.environ, {"ELENCHUS_REPORT_FILE": "inherited"}):
            inherited = self.outcome(
                self.guarded,
                [sys.executable, "-c", inherited_writer, "{report}"],
            )
        self.assertEqual("inconclusive", no_placeholder["status"])
        self.assertEqual("inconclusive", inherited["status"])

    def test_no_changed_test_is_still_unguarded(self):
        self.assertEqual("unguarded", self.outcome(self.unguarded)["status"])


class ParentGuardEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Fixture({"emit_unittest.py": UNITTEST_EMITTER})
        cls.payload = b"raw-guard-\xff\x00\r\n"
        cls.guard = cls.fixture.child("raw guard", {
            "payload.bin": cls.payload,
            "test_raw_guard.py": (
                "from pathlib import Path\n"
                "import os\n"
                "import unittest\n\n"
                "class RawGuard(unittest.TestCase):\n"
                "    def test_parent_fails(self):\n"
                f"        self.assertEqual(Path('payload.bin').read_bytes(), {cls.payload!r})\n"
                "        self.assertTrue(os.stat('payload.bin').st_mode & 0o100)\n"
                "        self.fail('known parent failure')\n"
            ),
        })
        os.chmod(cls.fixture.path / "payload.bin", 0o755)
        cls.fixture.run("add", "payload.bin")
        cls.fixture.run(
            "-c", "commit.gpgsign=false", "commit", "--quiet", "--amend", "--no-edit"
        )
        cls.guard = cls.fixture.run("rev-parse", "HEAD").strip()
        cls.rows = cls._rows(cls.guard)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.destroy()

    @classmethod
    def _rows(cls, ref):
        names = cls.fixture.run(
            "diff-tree", "--no-commit-id", "--name-status", "-r", ref
        ).splitlines()
        rows = []
        for line in names:
            status, path = line.split("\t")
            entry = cls.fixture.run("ls-tree", ref, "--", path).strip()
            mode, kind, oid, actual = entry.replace("\t", " ").split(" ", 3)
            assert kind == "blob" and actual == path
            raw = subprocess.run(
                ["git", "-C", str(cls.fixture.path), "cat-file", "blob", oid],
                capture_output=True,
                check=True,
            ).stdout
            rows.append({
                "path": path,
                "status": status,
                "mode": mode,
                "oid": oid,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "raw": raw,
            })
        return sorted(rows, key=lambda row: row["path"].encode("utf-8"))

    def run_evidence(self, command=None, **changes):
        rows = [dict(row) for row in changes.pop("rows", self.rows)]
        return elenchus.parent_guard_evidence(
            self.fixture.path,
            changes.pop("parent", self.fixture.base),
            rows,
            command or [sys.executable, "emit_unittest.py", "{report}"],
            changes.pop("report_format", "unittest-json-v1"),
            changes.pop("report_file", REPORT_FILE),
            changes.pop("timeout", 120),
            **changes,
        )

    def test_report_path_pathspec_magic_cannot_hide_a_tracked_file(self):
        fixture = Fixture({":(literal)sentinel": "tracked bytes\n"})
        self.addCleanup(fixture.destroy)
        target = fixture.path / ":(literal)sentinel"
        before = target.read_bytes()

        with self.assertRaisesRegex(elenchus.ReportError, "tracked file"):
            elenchus.prepare_report_path(fixture.path, ":(literal)sentinel")

        self.assertEqual(before, target.read_bytes())

    def test_report_path_tracking_errors_refuse_without_unlinking(self):
        fixture = Fixture({"ordinary.txt": "tracked bytes\n"})
        self.addCleanup(fixture.destroy)
        target = fixture.path / "ordinary.txt"
        before = target.read_bytes()
        failed = subprocess.CompletedProcess([], 2, stdout="", stderr="broken")

        with mock.patch.object(elenchus.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(elenchus.ReportError, "tracked state"):
                elenchus.prepare_report_path(fixture.path, "ordinary.txt")

        self.assertEqual(before, target.read_bytes())

    def test_missing_submodule_object_materializes_as_a_bound_empty_directory(self):
        fixture = Fixture({"emit_unittest.py": UNITTEST_EMITTER})
        self.addCleanup(fixture.destroy)
        missing = "1" * 40
        fixture.run(
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{missing},vendor/sub",
        )
        fixture.run(
            "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "gitlink parent"
        )
        fixture.base = fixture.run("rev-parse", "HEAD").strip()
        absent = subprocess.run(
            ["git", "-C", str(fixture.path), "cat-file", "-e", missing],
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, absent.returncode)
        guard_path = "test_gitlink_parent.py"
        guard = fixture.child(
            "gitlink guard",
            {
                guard_path: (
                    "from pathlib import Path\n"
                    "import unittest\n\n"
                    "class GitlinkParent(unittest.TestCase):\n"
                    "    def test_gitlink_is_an_empty_directory(self):\n"
                    "        self.assertTrue(Path('vendor/sub').is_dir())\n"
                    "        self.assertEqual([], list(Path('vendor/sub').iterdir()))\n"
                    "        self.fail('known parent failure')\n"
                )
            },
        )
        entry = fixture.run("ls-tree", guard, "--", guard_path).strip()
        mode, kind, oid, actual = entry.replace("\t", " ").split(" ", 3)
        raw = subprocess.run(
            ["git", "-C", str(fixture.path), "cat-file", "blob", oid],
            capture_output=True,
            check=True,
        ).stdout
        result = elenchus.parent_guard_evidence(
            fixture.path,
            fixture.base,
            [
                {
                    "path": actual,
                    "status": "A",
                    "mode": mode,
                    "oid": oid,
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "raw": raw,
                }
            ],
            [sys.executable, "emit_unittest.py", "{report}"],
            "unittest-json-v1",
            REPORT_FILE,
            timeout=120,
        )

        self.assertEqual("blob", kind)
        self.assertEqual("guarded", result["status"])

    def test_parent_tree_and_blob_materialization_limits_are_exact(self):
        listing = elenchus._native_git(
            self.fixture.path,
            "ls-tree",
            "-r",
            "-z",
            "--full-tree",
            self.fixture.base,
        )
        entries = elenchus._parent_tree_entries(self.fixture.path, self.fixture.base)
        sizes = [
            int(elenchus._native_git(self.fixture.path, "cat-file", "-s", oid))
            for _path, _mode, kind, oid in entries
            if kind == "blob"
        ]
        cases = (
            ("tree-bytes", "MAX_PARENT_TREE_BYTES", len(listing)),
            ("entry-count", "MAX_PARENT_ENTRIES", len(entries)),
            ("one-blob", "MAX_PARENT_BLOB_BYTES", max(sizes)),
            ("aggregate", "MAX_PARENT_BLOBS_BYTES", sum(sizes)),
        )
        for name, limit, exact in cases:
            with self.subTest(name=f"{name}-exact"), mock.patch.object(
                elenchus, limit, exact
            ):
                self.assertEqual("guarded", self.run_evidence()["status"])
            with self.subTest(name=f"{name}-over"), mock.patch.object(
                elenchus, limit, exact - 1
            ), mock.patch.object(elenchus, "_run_guard_command") as runner:
                with self.assertRaisesRegex(elenchus.ReportError, "size limit|too many"):
                    self.run_evidence()
                runner.assert_not_called()

    def test_parent_blob_reader_refuses_an_expired_deadline(self):
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        reader = elenchus._BatchBlobReader(process, time.monotonic() - 1)
        try:
            with self.assertRaisesRegex(elenchus.ReportError, "timed out"):
                reader.line(129)
        finally:
            process.kill()
            process.wait()
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
            reader.close()

    def test_parent_tree_listing_refuses_an_expired_deadline(self):
        real_popen = subprocess.Popen
        processes = []

        def capture(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            processes.append(process)
            return process

        try:
            with (
                mock.patch.object(elenchus, "MAX_PARENT_GIT_SECONDS", 0),
                mock.patch.object(
                    elenchus.subprocess, "Popen", side_effect=capture
                ),
            ):
                with self.assertRaisesRegex(elenchus.ReportError, "listing timed out"):
                    elenchus._parent_tree_entries(self.fixture.path, self.fixture.base)
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=1)

    def test_stuck_parent_git_cleanup_shares_deadline_and_reaps_process(self):
        real_popen = subprocess.Popen

        def stuck_process(*_args, **kwargs):
            process = real_popen(
                [sys.executable, "-c", "import time; time.sleep(60)"],
                stdin=kwargs.get("stdin"),
                stdout=kwargs.get("stdout"),
                stderr=kwargs.get("stderr"),
            )
            processes.append(process)
            return process

        for operation in ("listing", "blobs"):
            with self.subTest(operation=operation):
                processes = []
                started = time.monotonic()
                try:
                    with (
                        mock.patch.object(elenchus, "MAX_PARENT_GIT_SECONDS", 0.25),
                        mock.patch.object(
                            elenchus, "MAX_PARENT_GIT_REAP_SECONDS", 0.05
                        ),
                        mock.patch.object(
                            elenchus.subprocess,
                            "Popen",
                            side_effect=stuck_process,
                        ),
                    ):
                        if operation == "listing":
                            with self.assertRaisesRegex(
                                elenchus.ReportError, "listing timed out"
                            ):
                                elenchus._parent_tree_entries(
                                    self.fixture.path, self.fixture.base
                                )
                        else:
                            with (
                                mock.patch.object(
                                    elenchus, "_parent_tree_entries", return_value=[]
                                ),
                                mock.patch.object(
                                    elenchus, "_native_git", return_value=b""
                                ),
                                tempfile.TemporaryDirectory(
                                    prefix="elenchus-stuck-parent-git-"
                                ) as directory,
                            ):
                                with self.assertRaisesRegex(
                                    elenchus.ReportError, "materialization timed out"
                                ):
                                    elenchus._materialize_parent_tree(
                                        self.fixture.path,
                                        Path(directory),
                                        self.fixture.base,
                                    )
                    self.assertLess(time.monotonic() - started, 0.75)
                    self.assertEqual(1, len(processes))
                    self.assertIsNotNone(processes[0].poll())
                    self.assertEqual(-signal.SIGKILL, processes[0].returncode)
                finally:
                    for process in processes:
                        if process.poll() is None:
                            process.kill()
                            process.wait(timeout=1)
                        for stream in (
                            process.stdin,
                            process.stdout,
                            process.stderr,
                        ):
                            if stream is not None:
                                stream.close()

    def transformed_parent_result(
        self, attributes, configurations, *, global_configurations=False
    ):
        fixture = Fixture({
            "parent.txt": "raw-parent\n",
            "emit_unittest.py": UNITTEST_EMITTER,
        })
        self.addCleanup(fixture.destroy)
        tool = fixture.path / "parent-tool"
        tool.write_bytes(b"#!/bin/sh\nexit 0\n")
        tool.chmod(0o755)
        (fixture.path / "parent-link").symlink_to("parent.txt")
        fixture.run("add", "parent-tool", "parent-link")
        fixture.run(
            "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "parent modes"
        )
        (fixture.path / ".gitattributes").write_text(attributes, encoding="utf-8")
        fixture.run("add", ".gitattributes")
        fixture.run(
            "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "attributes"
        )
        fixture.base = fixture.run("rev-parse", "HEAD").strip()
        test_path = fixture.path / "test_parent_bytes.py"
        test_path.write_text(
            "from pathlib import Path\n"
            "import os\n"
            "import unittest\n\n"
            "class ParentBytes(unittest.TestCase):\n"
            "    def test_parent_bytes_are_native_git_bytes(self):\n"
            "        self.assertEqual(Path('parent.txt').read_bytes(), "
            "b'raw-parent\\n')\n"
            "        self.assertEqual('parent.txt', os.readlink('parent-link'))\n"
            "        self.assertTrue(Path('parent-link').is_symlink())\n"
            "        self.assertEqual(0o111, os.stat('parent-tool').st_mode & 0o111)\n",
            encoding="utf-8",
        )
        fixture.run("add", "test_parent_bytes.py")
        fixture.run(
            "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "parent bytes guard"
        )
        guard = fixture.run("rev-parse", "HEAD").strip()
        environment = contextlib.nullcontext()
        if global_configurations:
            global_config = fixture.path / "attack-global-config"
            for name, value in configurations:
                subprocess.run(
                    ["git", "config", "--file", str(global_config), name, value],
                    capture_output=True,
                    check=True,
                )
            environment = mock.patch.dict(
                os.environ, {"GIT_CONFIG_GLOBAL": str(global_config)}, clear=False
            )
        else:
            for name, value in configurations:
                fixture.run("config", name, value)
        checkout_home = Path(tempfile.mkdtemp(prefix="elenchus-filter-checkout-"))
        self.addCleanup(shutil.rmtree, checkout_home, True)
        checkout_tree = checkout_home / "tree"
        with environment:
            checkout = subprocess.run(
                [
                    "git", "-C", str(fixture.path), "worktree", "add", "--quiet",
                    "--detach", str(checkout_tree), fixture.base,
                ],
                capture_output=True,
                check=False,
            )
            checkout_bytes = (
                (checkout_tree / "parent.txt").read_bytes()
                if checkout.returncode == 0
                else None
            )
            subprocess.run(
                [
                    "git", "-C", str(fixture.path), "worktree", "remove", "--force",
                    str(checkout_tree),
                ],
                capture_output=True,
                check=False,
            )
            rows = []
            for line in fixture.run(
                "diff-tree", "--no-commit-id", "--name-status", "-r", guard
            ).splitlines():
                status, path = line.split("\t")
                entry = fixture.run("ls-tree", guard, "--", path).strip()
                mode, kind, oid, actual = entry.replace("\t", " ").split(" ", 3)
                self.assertEqual(("blob", path), (kind, actual))
                raw = subprocess.run(
                    ["git", "-C", str(fixture.path), "cat-file", "blob", oid],
                    capture_output=True,
                    check=True,
                ).stdout
                rows.append({
                    "path": path,
                    "status": status,
                    "mode": mode,
                    "oid": oid,
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "raw": raw,
                })
            rows.sort(key=lambda row: row["path"].encode("utf-8"))
            result = elenchus.parent_guard_evidence(
                fixture.path,
                fixture.base,
                rows,
                [sys.executable, "emit_unittest.py", "{report}"],
                "unittest-json-v1",
                REPORT_FILE,
                timeout=120,
            )
        return result, checkout.returncode, checkout_bytes

    def test_raw_blobs_modes_and_exact_report_are_returned_before_cleanup(self):
        before = self.fixture.worktrees()
        result = self.run_evidence()
        self.assertEqual("guarded", result["status"])
        self.assertEqual({
            "complete": True,
            "executed": 1,
            "assertion_failures": 1,
            "errors": 0,
            "skipped": 0,
        }, result["report"])
        self.assertEqual(
            "elenchus.unittest.v1",
            json.loads(result["raw_report"].decode("utf-8"))["schema"],
        )
        self.assertEqual(before, self.fixture.worktrees())

    def test_git_replacement_objects_do_not_change_supplied_blob_evidence(self):
        target = next(row for row in self.rows if row["path"] == "payload.bin")
        replacement = subprocess.run(
            ["git", "-C", str(self.fixture.path), "hash-object", "-w", "--stdin"],
            input=b"replacement bytes",
            capture_output=True,
            check=True,
        ).stdout.decode().strip()
        self.fixture.run("replace", target["oid"], replacement)
        self.addCleanup(
            subprocess.run,
            ["git", "-C", str(self.fixture.path), "replace", "-d", target["oid"]],
            capture_output=True,
            check=False,
        )

        result = self.run_evidence()

        self.assertEqual("guarded", result["status"])

    def test_checkout_transformations_cannot_change_parent_evidence(self):
        cases = (
            (
                "smudge-and-clean-filter",
                "parent.txt filter=attack\n",
                (
                    ("filter.attack.smudge", "sed s/raw-parent/smudged-parent/"),
                    ("filter.attack.clean", "sed s/smudged-parent/raw-parent/"),
                    ("filter.attack.required", "true"),
                ),
                b"smudged-parent\n",
            ),
            (
                "process-filter",
                "parent.txt filter=attack\n",
                (
                    ("filter.attack.process", "/definitely/missing/filter-process"),
                    ("filter.attack.required", "true"),
                ),
                None,
            ),
            (
                "autocrlf",
                "parent.txt text\n",
                (("core.autocrlf", "true"),),
                b"raw-parent\r\n",
            ),
            (
                "working-tree-encoding",
                "parent.txt working-tree-encoding=UTF-16LE\n",
                (("core.checkRoundtripEncoding", "UTF-16LE"),),
                "raw-parent\n".encode("utf-16le"),
                False,
            ),
            (
                "global-smudge-filter",
                "parent.txt filter=attack\n",
                (
                    ("filter.attack.smudge", "sed s/raw-parent/global-parent/"),
                    ("filter.attack.clean", "cat"),
                    ("filter.attack.required", "true"),
                ),
                b"global-parent\n",
                True,
            ),
        )
        normalized_cases = (
            case if len(case) == 5 else (*case, False)
            for case in cases
        )
        for name, attributes, configurations, transformed, is_global in normalized_cases:
            with self.subTest(name=name):
                result, checkout_exit, checkout_bytes = self.transformed_parent_result(
                    attributes,
                    configurations,
                    global_configurations=is_global,
                )
                if transformed is None:
                    self.assertNotEqual(0, checkout_exit)
                else:
                    self.assertEqual(0, checkout_exit)
                    self.assertEqual(transformed, checkout_bytes)
                self.assertEqual("passed", result["status"])
                self.assertEqual(1, result["report"]["executed"])
                self.assertEqual(0, result["report"]["assertion_failures"])

    def test_caller_path_and_pythonpath_cannot_forge_guard_evidence(self):
        passed = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        forged = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        command = [
            "python3",
            "-c",
            "from pathlib import Path; import sys; "
            f"p=Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True); "
            f"p.write_text({passed!r}, encoding='utf-8')",
            "{report}",
        ]

        with tempfile.TemporaryDirectory(prefix="elenchus-fake-path-") as directory:
            attack = Path(directory)
            marker = attack / "path-ran"
            git_marker = attack / "git-path-ran"
            fake = attack / "python3"
            fake.write_text(
                "#!/bin/sh\n"
                f": > {shlex.quote(str(marker))}\n"
                "mkdir -p \"$(dirname \"$3\")\"\n"
                f"printf %s {shlex.quote(forged)} > \"$3\"\n"
                "exit 1\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            fake_git = attack / "git"
            fake_git.write_text(
                "#!/bin/sh\n"
                f": > {shlex.quote(str(git_marker))}\n"
                "exit 1\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            with mock.patch.dict(
                os.environ,
                {"PATH": f"{attack}{os.pathsep}{os.environ.get('PATH', '')}"},
                clear=False,
            ):
                result = self.run_evidence(command)
            self.assertEqual("passed", result["status"])
            self.assertFalse(marker.exists())
            self.assertFalse(git_marker.exists())

        with tempfile.TemporaryDirectory(prefix="elenchus-pythonpath-") as directory:
            attack = Path(directory)
            marker = attack / "pythonpath-ran"
            (attack / "sitecustomize.py").write_text(
                "from pathlib import Path\n"
                "import os\n"
                "import sys\n"
                f"Path({str(marker)!r}).write_text('ran', encoding='utf-8')\n"
                "target = Path(sys.argv[-1])\n"
                "target.parent.mkdir(parents=True, exist_ok=True)\n"
                f"target.write_text({forged!r}, encoding='utf-8')\n"
                "os._exit(1)\n",
                encoding="utf-8",
            )
            with mock.patch.dict(
                os.environ, {"PYTHONPATH": str(attack)}, clear=False
            ):
                result = self.run_evidence(command)
            self.assertEqual("passed", result["status"])
            self.assertFalse(marker.exists())

    def test_blob_shape_mode_digest_object_parent_and_order_fail_closed(self):
        cases = []
        bad_mode = [dict(row) for row in self.rows]
        bad_mode[0]["mode"] = "120000"
        cases.append(bad_mode)
        bad_digest = [dict(row) for row in self.rows]
        bad_digest[0]["sha256"] = "0" * 64
        cases.append(bad_digest)
        bad_object = [dict(row) for row in self.rows]
        bad_object[0]["raw"] += b"x"
        bad_object[0]["bytes"] += 1
        bad_object[0]["sha256"] = hashlib.sha256(bad_object[0]["raw"]).hexdigest()
        cases.append(bad_object)
        cases.append(list(reversed(self.rows)))
        unknown = [dict(row) for row in self.rows]
        unknown[0]["extra"] = None
        cases.append(unknown)
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(elenchus.ReportError):
                self.run_evidence(rows=rows)
        with self.assertRaises(elenchus.ReportError):
            self.run_evidence(parent="HEAD")

    def test_report_symlink_hardlink_and_cap_are_inconclusive(self):
        valid = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        scripts = (
            (
                "symlink",
                "from pathlib import Path; import sys; "
                f"p=Path(sys.argv[1]); q=p.parent/'other'; q.write_text({valid!r}); "
                "p.symlink_to(q)",
            ),
            (
                "hardlink",
                "from pathlib import Path; import os,sys; "
                f"p=Path(sys.argv[1]); p.write_text({valid!r}); "
                "os.link(p,p.parent/'other')",
            ),
            (
                "oversized",
                "from pathlib import Path; import sys; "
                f"Path(sys.argv[1]).write_bytes(b'x'*{elenchus.MAX_REPORT_BYTES + 1})",
            ),
            (
                "ancestor-symlink",
                "from pathlib import Path; import os,sys; "
                "p=Path(sys.argv[1]); old=p.parent.with_name('.elenchus-old'); "
                "p.parent.rename(old); p.parent.symlink_to(old, target_is_directory=True); "
                f"(old/p.name).write_text({valid!r})",
            ),
            (
                "fifo",
                "from pathlib import Path; import os,sys; "
                "p=Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True); "
                "os.mkfifo(p)",
            ),
        )
        for name, script in scripts:
            with self.subTest(name=name):
                result = self.run_evidence([sys.executable, "-c", script, "{report}"])
                self.assertEqual("inconclusive", result["status"])

    def test_output_is_bounded_and_escaped_descendants_are_contained(self):
        guarded = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        output = self.run_evidence([
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; "
            "sys.stdout.write('o'*2000000); sys.stderr.write('e'*2000000); "
            "p=Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True); "
            f"p.write_text({guarded!r}, encoding='utf-8')",
            "{report}",
        ])
        self.assertEqual("guarded", output["status"])
        self.assertLessEqual(len(output["output"]), elenchus.MAX_DIAGNOSTIC_CHARS)

        with tempfile.TemporaryDirectory(prefix="elenchus-descendant-") as directory:
            marker = Path(directory) / "survived"
            child = (
                "from pathlib import Path; import signal,time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "time.sleep(2); "
                f"Path({str(marker)!r}).write_text('survived', encoding='utf-8')"
            )
            parent = (
                "import subprocess,sys; "
                f"subprocess.Popen([sys.executable, '-c', {child!r}], "
                "start_new_session=True)"
            )
            started = time.monotonic()
            result = self.run_evidence(
                [sys.executable, "-c", parent, "{report}"], timeout=3
            )
            elapsed = time.monotonic() - started
            self.assertEqual("inconclusive", result["status"])
            self.assertNotIn("raw_report", result)
            self.assertRegex(
                result["output"],
                "PermissionError|BlockingIOError|Operation not permitted|"
                "Resource temporarily unavailable",
            )
            self.assertLess(elapsed, 3)
            time.sleep(2.25)
            self.assertFalse(marker.exists())

    def test_parent_guard_rejects_an_executable_changed_during_the_run(self):
        guarded = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        with tempfile.TemporaryDirectory(prefix="elenchus-mutating-runner-") as directory:
            runner = Path(directory) / "runner"
            runner.write_text(
                f"#!{sys.executable}\n"
                "from pathlib import Path\n"
                "import sys\n"
                "source = Path(sys.argv[0])\n"
                "source.write_text(source.read_text(encoding='utf-8') + "
                "'# changed\\n', encoding='utf-8')\n"
                "target = Path(sys.argv[1])\n"
                "target.parent.mkdir(parents=True, exist_ok=True)\n"
                f"target.write_text({guarded!r}, encoding='utf-8')\n",
                encoding="utf-8",
            )
            runner.chmod(0o755)
            result = self.run_evidence([str(runner), "{report}"])
        self.assertEqual("inconclusive", result["status"])
        self.assertIn("executable changed", result["detail"])

    def test_parent_runner_ancestor_substitution_cannot_execute_replacement(self):
        guarded = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        with tempfile.TemporaryDirectory(prefix="elenchus-runner-parent-") as directory:
            ancestor = Path(directory) / "bin"
            ancestor.mkdir()
            runner = ancestor / "runner"
            runner.write_text(
                f"#!{sys.executable}\n"
                "from pathlib import Path\n"
                "import sys\n"
                "target = Path(sys.argv[1])\n"
                "target.parent.mkdir(parents=True, exist_ok=True)\n"
                f"target.write_text({guarded!r}, encoding='utf-8')\n",
                encoding="utf-8",
            )
            runner.chmod(0o755)
            marker = Path(directory) / "replacement-ran"
            malicious = (
                f"#!{sys.executable}\n"
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('ran', encoding='utf-8')\n"
            )
            real_run = elenchus._run_guard_command
            with mock.patch.object(
                elenchus,
                "_run_guard_command",
                side_effect=replace_runner_ancestor(
                    real_run, ancestor, malicious
                ),
            ):
                result = self.run_evidence([str(runner), "{report}"])
            replacement_ran = marker.exists()
        if sys.platform == "linux":
            self.assertEqual("guarded", result["status"])
        else:
            self.assertEqual("inconclusive", result["status"])
        self.assertFalse(replacement_ran)

    def test_incomplete_escaped_pipes_prevent_report_admission(self):
        guarded = json.dumps({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        })
        with tempfile.TemporaryDirectory(prefix="elenchus-open-pipe-") as directory:
            pid_file = Path(directory) / "pid"
            child = "import time; time.sleep(30)"
            parent = (
                "from pathlib import Path; import subprocess,sys; "
                f"child=subprocess.Popen([sys.executable, '-c', {child!r}], "
                "start_new_session=True); "
                f"Path({str(pid_file)!r}).write_text(str(child.pid)); "
                "p=Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True); "
                f"p.write_text({guarded!r}, encoding='utf-8')"
            )

            def without_containment(command, target):
                return elenchus.GuardCommand(command, (), (target,))

            with mock.patch.object(
                elenchus,
                "_contained_guard_command",
                side_effect=without_containment,
            ):
                result = self.run_evidence(
                    [sys.executable, "-c", parent, "{report}"], timeout=3
                )
            child_pid = int(pid_file.read_text(encoding="ascii"))
            with contextlib.suppress(ProcessLookupError):
                os.kill(child_pid, signal.SIGKILL)
            self.assertEqual("inconclusive", result["status"])
            self.assertIn("output streams open", result["detail"])
            self.assertNotIn("raw_report", result)

    def test_overlay_status_and_physical_path_boundaries_fail_closed(self):
        target = next(row for row in self.rows if row["path"] == "payload.bin")
        for path in (
            ".git/test_guard.py",
            "tests/.GiT/test_guard.py",
            "tests/test_bad\npath.py",
        ):
            row = dict(target, path=path, status="A")
            with self.subTest(path=path), self.assertRaises(elenchus.ReportError):
                self.run_evidence(rows=[row])

        aliases = [
            dict(target, path="tests/Test_alias.py", status="A"),
            dict(target, path="tests/test_alias.py", status="A"),
        ]
        aliases.sort(key=lambda row: row["path"].encode("utf-8"))
        with self.assertRaises(elenchus.ReportError):
            self.run_evidence(rows=aliases)

        with tempfile.TemporaryDirectory(prefix="elenchus-overlay-") as directory:
            tree = Path(directory)
            existing = tree / "existing.py"
            existing.write_bytes(b"parent")
            added = dict(target, path="existing.py", status="A")
            with self.assertRaises(elenchus.ReportError):
                elenchus._overlay_guard_blob(tree, added)
            self.assertEqual(b"parent", existing.read_bytes())

            missing = dict(target, path="missing.py", status="M")
            with self.assertRaises(elenchus.ReportError):
                elenchus._overlay_guard_blob(tree, missing)
            self.assertFalse((tree / "missing.py").exists())

    def test_report_path_cannot_overlap_or_alias_a_guard_blob(self):
        target = next(row for row in self.rows if row["path"] == "test_raw_guard.py")
        nested = dict(target, path="tests/test_overlap.py", status="A")
        unicode_path = dict(target, path="tests/t\u00e9st.py", status="A")
        cases = (
            ([target], "test_raw_guard.py"),
            ([target], "test_raw_guard.py/report.json"),
            ([target], "TEST_RAW_GUARD.PY"),
            ([nested], "tests"),
            ([nested], "TESTS"),
            ([unicode_path], "tests/te\u0301st.py"),
        )
        for rows, report_file in cases:
            with self.subTest(report_file=report_file):
                with self.assertRaises(elenchus.ReportError):
                    self.run_evidence(rows=rows, report_file=report_file)

    def test_report_change_while_reading_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory)
            report = tree / "report"
            report.write_bytes(b"x" * 70000)
            real_read = os.read
            changed = False

            def read_then_change(descriptor, count):
                nonlocal changed
                chunk = real_read(descriptor, count)
                if chunk and not changed:
                    changed = True
                    with report.open("ab") as target:
                        target.write(b"y")
                return chunk

            with mock.patch.object(elenchus.os, "read", side_effect=read_then_change):
                with self.assertRaises(elenchus.ReportError):
                    elenchus._stable_report_bytes(report, 0, tree)

    def test_report_ancestor_replacement_while_reading_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory)
            reports = tree / "reports"
            reports.mkdir()
            report = reports / "report"
            body = b"x" * 70000
            report.write_bytes(body)
            real_read = os.read
            replaced = False

            def read_then_replace(descriptor, count):
                nonlocal replaced
                chunk = real_read(descriptor, count)
                if chunk and not replaced:
                    replaced = True
                    reports.rename(tree / "reports-old")
                    reports.mkdir()
                    (reports / "report").write_bytes(body)
                return chunk

            with mock.patch.object(elenchus.os, "read", side_effect=read_then_replace):
                with self.assertRaises(elenchus.ReportError):
                    elenchus._stable_report_bytes(report, 0, tree)

    def test_complete_command_has_one_4096_byte_ceiling(self):
        with self.assertRaises(elenchus.ReportError):
            self.run_evidence([
                sys.executable,
                "x" * elenchus.MAX_COMMAND_BYTES,
                "{report}",
            ])

    def test_timeout_start_failure_and_signal_are_distinct_inconclusive_results(self):
        timeout = self.run_evidence(
            [sys.executable, "-c", "import time; time.sleep(2)", "{report}"],
            timeout=1,
        )
        missing = self.run_evidence(["/definitely/missing/elenchus-runner", "{report}"])
        interrupted = self.run_evidence([
            sys.executable, "-c", "import os,signal; os.kill(os.getpid(),signal.SIGTERM)",
            "{report}",
        ])
        self.assertIn("did not finish", timeout["detail"])
        self.assertIn("could not be started", missing["detail"])
        self.assertIn("interrupted", interrupted["detail"])
        self.assertEqual(
            ["inconclusive", "inconclusive", "inconclusive"],
            [timeout["status"], missing["status"], interrupted["status"]],
        )


class ForgeReports(RunnerCase):
    @classmethod
    def setUpClass(cls):
        forge = shutil.which("forge")
        if forge is None:
            raise unittest.SkipTest("forge is unavailable")
        cls.runner_version = subprocess.run(
            [forge, "--version"], capture_output=True, text=True, check=True
        ).stdout.splitlines()[0]
        cls.command = [sys.executable, "emit_forge.py", "{report}", forge]
        cls.report_format = "forge-junit-v1"
        cls.fixture = Fixture({
            "foundry.toml": (
                "[profile.default]\nsrc = 'src'\ntest = 'test'\n"
                "solc_version = '0.8.28'\n"
            ),
            "src/Adder.sol": (
                "// SPDX-License-Identifier: UNLICENSED\npragma solidity 0.8.28;\n"
                "contract Adder { function add(uint a, uint b) external pure returns (uint) "
                "{ return a - b; } }\n"
            ),
            "emit_forge.py": FORGE_EMITTER,
        })
        f = cls.fixture
        cls.guarded = f.child("guarded", {
            "test/Adder.t.sol": (
                "// SPDX-License-Identifier: UNLICENSED\npragma solidity 0.8.28;\n"
                "import {Adder} from '../src/Adder.sol';\n"
                "contract AdderTest { function testModuleNotFoundError() public { "
                "assert(new Adder().add(2, 2) == 4); } }\n"
            ),
        })
        cls.passed = f.child("passed", {
            "test/Arithmetic.t.sol": (
                "// SPDX-License-Identifier: UNLICENSED\npragma solidity 0.8.28;\n"
                "contract ArithmeticTest { function testArithmetic() public pure { "
                "assert(uint(1) + 1 == 2); } }\n"
            ),
        })
        cls.broken = f.child("broken", {
            "test/Broken.t.sol": (
                "// SPDX-License-Identifier: UNLICENSED\npragma solidity 0.8.28;\n"
                "import {Missing} from '../src/AssertionError.sol';\n"
                "contract BrokenTest {}\n"
            ),
        })

    def test_cold_native_forge_fails_closed_when_it_needs_a_solc_child(self):
        result = self.outcome(self.guarded)
        self.assertEqual("inconclusive", result["status"])
        self.assertNotIn("report", result)
        self.assertRegex(
            result["output"],
            "Operation not permitted|Resource temporarily unavailable",
        )

    def test_fixture_exercised_the_declared_forge_version(self):
        self.assertIn("1.7.1", self.runner_version)


class NodeReports(RunnerCase):
    @classmethod
    def setUpClass(cls):
        node = shutil.which("node")
        if node is None:
            raise unittest.SkipTest("node is unavailable")
        cls.runner_version = subprocess.run(
            [node, "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
        cls.command = [node, "emit_node.mjs", "{report}"]
        cls.report_format = "node-test-json-v1"
        cls.fixture = Fixture({
            "adder.mjs": "export const add = (a, b) => a - b;\n",
            "emit_node.mjs": NODE_EMITTER,
        })
        f = cls.fixture
        cls.guarded = f.child("guarded", {
            "test_adder.mjs": (
                "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
                "import { add } from './adder.mjs';\n"
                "test('ModuleNotFoundError', () => assert.equal(add(2, 2), 4));\n"
            ),
        })
        cls.passed = f.child("passed", {
            "test_adder.mjs": (
                "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
                "test('arithmetic', () => assert.equal(1 + 1, 2));\n"
            ),
        })
        cls.broken = f.child("broken", {
            "test_adder.mjs": (
                "import test from 'node:test';\n"
                "import './AssertionError.mjs';\n"
                "test('unreachable', () => {});\n"
            ),
        })

    def test_testsstream_distinguishes_all_three_outcomes(self):
        self.assertEqual("guarded", self.outcome(self.guarded)["status"])
        self.assertEqual("passed", self.outcome(self.passed)["status"])
        self.assertEqual("inconclusive", self.outcome(self.broken)["status"])

    def test_fixture_exercised_the_declared_node_version(self):
        self.assertEqual("v26.6.0", self.runner_version)


class ReportValidation(unittest.TestCase):
    def payload(self, **changes):
        value = {
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }
        value.update(changes)
        return json.dumps(value).encode()

    def test_malformed_incomplete_zero_and_contradictory_reports_fail_closed(self):
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(b"{")
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(self.payload(complete=False))
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(self.payload(testsRun=1, failures=2))

    def test_json_reports_reject_duplicate_object_keys(self):
        unittest_report = self.payload().replace(
            b'{', b'{"schema":"elenchus.unittest.v1",', 1
        )
        node_report = (
            b'{"schema":"elenchus.node-test.v1","complete":true,'
            b'"executed":1,"executed":1,"assertionFailures":0,'
            b'"errors":0,"skipped":0}'
        )
        for parser, raw in (
            (elenchus.parse_unittest_report, unittest_report),
            (elenchus.parse_node_report, node_report),
        ):
            with self.subTest(parser=parser.__name__):
                with self.assertRaisesRegex(
                    elenchus.ReportError, "duplicate object key"
                ):
                    parser(raw)

    def test_forge_junit_parser_preserves_all_three_verdicts(self):
        reports = (
            b'<testsuites tests="1" failures="1" errors="0">'
            b'<testcase><failure/></testcase></testsuites>',
            b'<testsuites tests="1" failures="0" errors="0">'
            b'<testcase/></testsuites>',
            b'<testsuites tests="1" failures="0" errors="1">'
            b'<testcase><error/></testcase></testsuites>',
        )
        self.assertEqual(
            ["guarded", "passed", "inconclusive"],
            [
                elenchus.classify(elenchus.parse_forge_report(raw))[0]
                for raw in reports
            ],
        )

    def test_platform_no_child_boundaries_are_explicit_or_refused(self):
        identity = (1, 2, 3, 4, 5, 6, 7)
        command = ["/runner", "{report}"]
        target = mock.Mock(spec=elenchus.ExecutableBinding)
        target.path = "/runner"
        target.leaf = "runner"
        target.descriptor = 40
        target.parent_descriptor = 39
        target.identity = identity
        python = mock.Mock(spec=elenchus.ExecutableBinding)
        python.path = "/usr/bin/python3"
        python.descriptor = 41
        with (
            mock.patch.object(elenchus.os, "geteuid", return_value=501),
            mock.patch.object(elenchus.os, "getuid", return_value=501),
            mock.patch.object(elenchus.sys, "platform", "linux"),
            mock.patch.object(
                elenchus.os, "uname", return_value=mock.Mock(machine="x86_64")
            ),
            mock.patch.object(
                elenchus, "_trusted_executable",
                return_value=python,
            ),
        ):
            wrapped = elenchus._contained_guard_command(command, target)
        self.assertEqual(["/proc/self/fd/41", "-I", "-c"], wrapped.argv[:3])
        self.assertIn("PR_SET_SECCOMP", wrapped.argv[3])
        self.assertIn("CLONE_THREAD", wrapped.argv[3])
        self.assertIn("os.execve(target_fd", wrapped.argv[3])
        self.assertEqual((41, 40), wrapped.pass_fds)

        sandbox = mock.Mock(spec=elenchus.ExecutableBinding)
        sandbox.path = "/usr/bin/sandbox-exec"
        sandbox.descriptor = 42
        system_python = mock.Mock(spec=elenchus.ExecutableBinding)
        system_python.path = "/usr/bin/python3"
        system_python.descriptor = 43
        with (
            mock.patch.object(elenchus.os, "geteuid", return_value=501),
            mock.patch.object(elenchus.os, "getuid", return_value=501),
            mock.patch.object(elenchus.sys, "platform", "darwin"),
            mock.patch.object(
                elenchus, "_trusted_executable",
                side_effect=(sandbox, system_python),
            ),
            mock.patch.object(
                elenchus, "_binding_path_is_immutable", return_value=True
            ),
        ):
            wrapped = elenchus._contained_guard_command(command, target)
        self.assertEqual("/usr/bin/sandbox-exec", wrapped.argv[0])
        self.assertIn("deny process-fork", wrapped.argv[2])
        self.assertEqual("/usr/bin/python3", wrapped.argv[3])
        self.assertIn("dir_fd=parent_fd", wrapped.argv[6])
        self.assertIn("follow_symlinks=False", wrapped.argv[6])
        self.assertEqual((39, 40), wrapped.pass_fds)

        with (
            mock.patch.object(elenchus.os, "geteuid", return_value=501),
            mock.patch.object(elenchus.os, "getuid", return_value=501),
            mock.patch.object(elenchus.sys, "platform", "freebsd"),
        ):
            with self.assertRaises(OSError):
                elenchus._contained_guard_command(command, target)
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(self.payload(testsRun=True))
        zero = elenchus.parse_unittest_report(self.payload(testsRun=0))
        self.assertEqual("inconclusive", elenchus.classify(zero)[0])

    def test_mixed_assertion_and_infrastructure_errors_are_inconclusive(self):
        report = elenchus.RunnerReport(True, 2, 1, 1, 0)
        self.assertEqual("inconclusive", elenchus.classify(report)[0])

    def test_oversized_and_stale_reports_are_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report"
            path.write_bytes(b"x" * (elenchus.MAX_REPORT_BYTES + 1))
            with self.assertRaises(elenchus.ReportError):
                elenchus.read_report(path, "unittest-json-v1", 0)
            path.write_bytes(self.payload())
            os.utime(path, (1, 1))
            with self.assertRaises(elenchus.ReportError):
                elenchus.read_report(path, "unittest-json-v1", time.time_ns())

    def test_xml_entities_and_contradictory_cases_are_rejected(self):
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_forge_report(
                b'<!DOCTYPE x [<!ENTITY y "z">]><testsuites />'
            )
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_forge_report(
                b'<testsuites><testcase><failure/><error/></testcase></testsuites>'
            )
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_forge_report(b'<testsuites tests="1">')

    def test_absolute_traversal_and_symlink_report_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory)
            (tree / "real").mkdir()
            (tree / "link").symlink_to(tree / "real", target_is_directory=True)
            for path in ("/tmp/report", "../report", "link/report"):
                with self.subTest(path=path), self.assertRaises(elenchus.ReportError):
                    elenchus.prepare_report_path(tree, path)


class HexaemeronUnittestReport(unittest.TestCase):
    def fixture(self, source):
        temporary = tempfile.TemporaryDirectory(prefix="hexaemeron-runner-")
        root = Path(temporary.name)
        shutil.copy2(RUN_TESTS, root / "run_tests.py")
        (root / "test_fixture.py").write_text(source, encoding="utf-8")
        return temporary, root

    def run_runner(self, root, *arguments):
        return subprocess.run(
            [sys.executable, str(root / "run_tests.py"), *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_report_has_the_exact_schema_and_every_unittest_counter(self):
        temporary, root = self.fixture(
            "import unittest\n\n"
            "class Outcomes(unittest.TestCase):\n"
            "    def test_pass(self): self.assertTrue(True)\n"
            "    def test_failure(self): self.fail('failure')\n"
            "    def test_error(self): raise RuntimeError('error')\n"
            "    @unittest.skip('skip')\n"
            "    def test_skip(self): pass\n"
            "    @unittest.expectedFailure\n"
            "    def test_expected_failure(self): self.fail('expected')\n"
            "    @unittest.expectedFailure\n"
            "    def test_unexpected_success(self): pass\n"
        )
        self.addCleanup(temporary.cleanup)
        report = root / "reports" / "nested" / "result.json"

        result = self.run_runner(root, "--elenchus-report", str(report))

        self.assertEqual(1, result.returncode)
        self.assertEqual({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 6,
            "failures": 1,
            "errors": 1,
            "skipped": 1,
            "expectedFailures": 1,
            "unexpectedSuccesses": 1,
        }, json.loads(report.read_text(encoding="utf-8")))

    def test_report_mode_preserves_pass_and_failure_exit_codes(self):
        passing, pass_root = self.fixture(
            "import unittest\n"
            "class Pass(unittest.TestCase):\n"
            "    def test_pass(self): self.assertTrue(True)\n"
        )
        failing, fail_root = self.fixture(
            "import unittest\n"
            "class Fail(unittest.TestCase):\n"
            "    def test_fail(self): self.fail('failure')\n"
        )
        self.addCleanup(passing.cleanup)
        self.addCleanup(failing.cleanup)
        pass_report = pass_root / "pass.json"
        fail_report = fail_root / "fail.json"

        self.assertEqual(0, self.run_runner(pass_root).returncode)
        self.assertEqual(
            0,
            self.run_runner(
                pass_root, "--elenchus-report", str(pass_report)
            ).returncode,
        )
        self.assertEqual(
            1,
            self.run_runner(
                fail_root, "--elenchus-report", str(fail_report)
            ).returncode,
        )
        self.assertTrue(pass_report.is_file())
        self.assertTrue(fail_report.is_file())

    def test_bad_arguments_are_refused_before_tests_or_report_writes(self):
        temporary, root = self.fixture(
            "from pathlib import Path\n"
            "raise AssertionError('the suite must not run on bad CLI input')\n"
        )
        self.addCleanup(temporary.cleanup)
        first = root / "first.json"
        second = root / "second.json"
        malformed = root / "malformed.json"
        outside = root.parent / f"{root.name}-outside.json"

        cases = (
            ("missing", ("--elenchus-report",)),
            (
                "repeated",
                (
                    "--elenchus-report", str(first),
                    "--elenchus-report", str(second),
                ),
            ),
            (
                "unknown",
                ("--elenchus-report", str(malformed), "--unknown"),
            ),
            ("empty", ("--elenchus-report", "")),
            ("outside-worktree", ("--elenchus-report", str(outside))),
        )
        for name, arguments in cases:
            with self.subTest(name=name):
                result = self.run_runner(root, *arguments)
                self.assertEqual(2, result.returncode)

        self.assertFalse(first.exists())
        self.assertFalse(second.exists())
        self.assertFalse(malformed.exists())
        self.assertFalse(outside.exists())

    def test_existing_report_targets_are_refused_without_overwrite(self):
        temporary, root = self.fixture(
            "import unittest\n"
            "class Pass(unittest.TestCase):\n"
            "    def test_pass(self): self.assertTrue(True)\n"
        )
        self.addCleanup(temporary.cleanup)
        directory = root / "directory"
        directory.mkdir()
        original = root / "original"
        original.write_text("keep\n", encoding="utf-8")
        symlink = root / "report-link"
        symlink.symlink_to(original)
        dangling = root / "dangling-link"
        dangling.symlink_to(root / "missing")

        for name, target in (
            ("directory", directory),
            ("regular", original),
            ("symlink", symlink),
            ("dangling-symlink", dangling),
        ):
            with self.subTest(name=name):
                result = self.run_runner(
                    root, "--elenchus-report", str(target)
                )
                self.assertEqual(2, result.returncode)

        self.assertEqual("keep\n", original.read_text(encoding="utf-8"))

    def test_suite_cannot_redirect_report_through_replaced_parent(self):
        outside = tempfile.TemporaryDirectory(prefix="hexaemeron-report-outside-")
        outside_root = Path(outside.name)
        temporary, root = self.fixture("import unittest\n")
        self.addCleanup(temporary.cleanup)
        self.addCleanup(outside.cleanup)
        fixture = root / "test_fixture.py"
        fixture.write_text(
            "from pathlib import Path\n"
            "import unittest\n\n"
            f"report_parent = Path({str(root / 'reports')!r})\n"
            f"report_parent.symlink_to(Path({str(outside_root)!r}), "
            "target_is_directory=True)\n\n"
            "class Pass(unittest.TestCase):\n"
            "    def test_pass(self): self.assertTrue(True)\n",
            encoding="utf-8",
        )
        report = root / "reports" / "result.json"

        result = self.run_runner(root, "--elenchus-report", str(report))

        self.assertEqual(2, result.returncode)
        self.assertFalse((outside_root / "result.json").exists())

    def test_relative_report_stays_anchored_when_suite_changes_cwd(self):
        outside = tempfile.TemporaryDirectory(prefix="hexaemeron-cwd-outside-")
        outside_root = Path(outside.name)
        temporary, root = self.fixture(
            "import os\n"
            "import unittest\n\n"
            f"os.chdir({str(outside_root)!r})\n\n"
            "class Pass(unittest.TestCase):\n"
            "    def test_pass(self): self.assertTrue(True)\n"
        )
        self.addCleanup(temporary.cleanup)
        self.addCleanup(outside.cleanup)

        result = self.run_runner(root, "--elenchus-report", "result.json")

        self.assertEqual(0, result.returncode)
        self.assertTrue((root / "result.json").is_file())
        self.assertFalse((outside_root / "result.json").exists())

    def test_suite_cannot_rebind_a_saved_report_root_descriptor(self):
        outside = tempfile.TemporaryDirectory(prefix="hexaemeron-fd-outside-")
        outside_root = Path(outside.name)
        temporary, root = self.fixture("import unittest\n")
        self.addCleanup(temporary.cleanup)
        self.addCleanup(outside.cleanup)
        fixture = root / "test_fixture.py"
        fixture.write_text(
            "import os\n"
            "from pathlib import Path\n"
            "import unittest\n\n"
            f"worktree = Path({str(root)!r})\n"
            f"outside = Path({str(outside_root)!r})\n"
            "identity = worktree.stat()\n"
            "for candidate in range(3, 256):\n"
            "    try:\n"
            "        opened = os.fstat(candidate)\n"
            "    except OSError:\n"
            "        continue\n"
            "    if (opened.st_dev, opened.st_ino) == "
            "(identity.st_dev, identity.st_ino):\n"
            "        os.close(candidate)\n"
            "        replacement = os.open(\n"
            "            outside, os.O_RDONLY | os.O_DIRECTORY\n"
            "        )\n"
            "        if replacement != candidate:\n"
            "            raise AssertionError('descriptor slot was not reused')\n"
            "        break\n\n"
            "class Pass(unittest.TestCase):\n"
            "    def test_pass(self): self.assertTrue(True)\n",
            encoding="utf-8",
        )
        report = root / "nested" / "result.json"

        result = self.run_runner(root, "--elenchus-report", str(report))

        self.assertEqual(0, result.returncode)
        self.assertTrue(report.is_file())
        self.assertFalse((outside_root / "nested" / "result.json").exists())

    def test_unsupported_directory_operations_are_named_before_tests(self):
        temporary, root = self.fixture(
            "raise AssertionError('the suite must not run')\n"
        )
        self.addCleanup(temporary.cleanup)
        stderr = io.StringIO()
        with (
            mock.patch.object(hexaemeron_runner.Path, "cwd", return_value=root),
            mock.patch.object(
                hexaemeron_runner.os, "supports_dir_fd", set()
            ),
            mock.patch.object(
                hexaemeron_runner.os, "supports_follow_symlinks", set()
            ),
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            hexaemeron_runner.main(
                ["--elenchus-report", str(root / "result.json")]
            )

        self.assertEqual(2, raised.exception.code)
        for name in (
            "os.open(dir_fd)",
            "os.mkdir(dir_fd)",
            "os.stat(dir_fd)",
            "os.unlink(dir_fd)",
            "os.stat(follow_symlinks)",
        ):
            self.assertIn(name, stderr.getvalue())

    def test_report_write_failure_has_a_distinct_exit_and_no_report(self):
        with tempfile.TemporaryDirectory(prefix="hexaemeron-write-failure-") as root:
            report = Path(root) / "report.json"
            suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
            stderr = io.StringIO()
            with (
                mock.patch.object(
                    hexaemeron_runner.unittest.defaultTestLoader,
                    "discover",
                    return_value=suite,
                ),
                mock.patch.object(
                    hexaemeron_runner,
                    "write_report",
                    side_effect=OSError("write blocked"),
                ),
                mock.patch.object(
                    hexaemeron_runner.Path,
                    "cwd",
                    return_value=Path(root),
                ),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = hexaemeron_runner.main(
                    ["--elenchus-report", str(report)]
                )

            self.assertEqual(2, exit_code)
            self.assertFalse(report.exists())
            self.assertIn("report write failed", stderr.getvalue())

    def test_partial_report_write_is_removed_before_failure_returns(self):
        with tempfile.TemporaryDirectory(prefix="hexaemeron-partial-write-") as root:
            report = Path(root) / "report.json"
            suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
            real_write = os.write
            real_write_report = hexaemeron_runner.write_report
            writes = 0

            def short_then_fail(descriptor, body):
                nonlocal writes
                writes += 1
                if writes == 1:
                    return real_write(descriptor, body[: max(1, len(body) // 2)])
                raise OSError("write blocked")

            def partially_write_report(target, payload):
                with mock.patch.object(
                    hexaemeron_runner.os,
                    "write",
                    side_effect=short_then_fail,
                ):
                    return real_write_report(target, payload)

            with (
                mock.patch.object(
                    hexaemeron_runner.unittest.defaultTestLoader,
                    "discover",
                    return_value=suite,
                ),
                mock.patch.object(
                    hexaemeron_runner,
                    "write_report",
                    side_effect=partially_write_report,
                ),
                mock.patch.object(
                    hexaemeron_runner.Path,
                    "cwd",
                    return_value=Path(root),
                ),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                exit_code = hexaemeron_runner.main(
                    ["--elenchus-report", str(report)]
                )

            self.assertEqual(2, exit_code)
            self.assertEqual(2, writes)
            self.assertFalse(report.exists())


class LaunchFailures(RunnerCase):
    @classmethod
    def setUpClass(cls):
        cls.report_format = "unittest-json-v1"
        cls.fixture = Fixture({"value.py": "VALUE = 1\n"})
        cls.changed = cls.fixture.child("test", {
            "test_value.py": "import unittest\nclass T(unittest.TestCase):\n    pass\n"
        })

    def test_missing_report_timeout_and_executable_failure_are_inconclusive_and_clean(self):
        before = self.fixture.worktrees()
        missing = self.outcome(
            self.changed, [sys.executable, "-c", "pass", "{report}"]
        )
        timeout = self.outcome(
            self.changed,
            [sys.executable, "-c", "import time; time.sleep(3)", "{report}"],
            timeout=1,
        )
        absent = self.outcome(
            self.changed, ["elenchus-command-does-not-exist", "{report}"]
        )
        interrupted = self.outcome(
            self.changed,
            [
                sys.executable,
                "-c",
                "import os, signal; os.kill(os.getpid(), signal.SIGTERM)",
                "{report}",
            ],
        )
        self.assertEqual(["inconclusive"] * 4, [
            missing["status"], timeout["status"], absent["status"], interrupted["status"],
        ])
        self.assertEqual(before, self.fixture.worktrees())


class Severity(unittest.TestCase):
    def test_unguarded_passes_by_default_and_fails_when_required(self):
        fixture = Fixture({"thing.py": "value = 1\n"})
        try:
            ref = fixture.child("second", {"thing.py": "value = 2\n"})
            argv = ["--repo", str(fixture.path), "--ref", ref,
                    "--test-command", "python3 -c pass"]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, elenchus.main(argv))
                self.assertEqual(1, elenchus.main(argv + ["--require-guard"]))
        finally:
            fixture.destroy()


class TestFileDetection(unittest.TestCase):
    def test_it_recognises_the_conventions_this_marketplace_meets(self):
        for path in (
            "tests/test_index.py", "src/thing_test.py", "app/Button.test.ts",
            "app/Button.spec.ts", "test/Market.t.sol", "__tests__/route.ts",
        ):
            self.assertTrue(elenchus.is_test(path), path)

    def test_it_leaves_ordinary_source_alone(self):
        for path in ("src/adder.py", "scripts/hexctl.py", "app/Button.tsx", "src/Market.sol"):
            self.assertFalse(elenchus.is_test(path), path)


if __name__ == "__main__":
    unittest.main()
