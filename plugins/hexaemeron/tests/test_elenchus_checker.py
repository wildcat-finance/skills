"""Elenchus classifies guards from real runner-owned reports."""

import contextlib
import importlib.util
import io
import json
import os
import shutil
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
from pathlib import Path
import subprocess
import sys

run = subprocess.run(["forge", "test", "--junit"], capture_output=True, check=False)
target = Path(sys.argv[1])
if run.stdout:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(run.stdout)
raise SystemExit(run.returncode)
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
            target.write_text(body, encoding="utf-8")
        self.run("add", "-A")
        self.run("commit", "--quiet", "-m", message)
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


class ForgeReports(RunnerCase):
    @classmethod
    def setUpClass(cls):
        cls.runner_version = subprocess.run(
            ["forge", "--version"], capture_output=True, text=True, check=True
        ).stdout.splitlines()[0]
        cls.command = [sys.executable, "emit_forge.py", "{report}"]
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

    def test_native_junit_distinguishes_all_three_outcomes(self):
        self.assertEqual("guarded", self.outcome(self.guarded)["status"])
        self.assertEqual("passed", self.outcome(self.passed)["status"])
        self.assertEqual("inconclusive", self.outcome(self.broken)["status"])

    def test_fixture_exercised_the_declared_forge_version(self):
        self.assertIn("1.7.1", self.runner_version)


class NodeReports(RunnerCase):
    @classmethod
    def setUpClass(cls):
        cls.runner_version = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
        cls.command = ["node", "emit_node.mjs", "{report}"]
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
            writes = 0

            def short_then_fail(descriptor, body):
                nonlocal writes
                writes += 1
                if writes == 1:
                    return real_write(descriptor, body[: max(1, len(body) // 2)])
                raise OSError("write blocked")

            with (
                mock.patch.object(
                    hexaemeron_runner.unittest.defaultTestLoader,
                    "discover",
                    return_value=suite,
                ),
                mock.patch.object(
                    hexaemeron_runner.os,
                    "write",
                    side_effect=short_then_fail,
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
