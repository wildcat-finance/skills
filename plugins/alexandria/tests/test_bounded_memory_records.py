"""Hold the committed issue 1891 design records to the record the run locked.

`docs/bounded-memory-interval/` carries byte copies of the controller's study,
runbook, design record and design folder. Git ignores their `.hexaemeron/`
originals, so these tests read only committed bytes: the digest the runbook's
design-lock fence names, the selection reports the record binds, the
conformance harness's refusal of every candidate the record rejected, and the
synthetic generator's determinism and its disk refusal.
"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


DOCS = Path(__file__).resolve().parents[1] / "docs" / "bounded-memory-interval"
RECORD = DOCS / "design-evidence.json"
RUNBOOK = DOCS / "runbook.md"
CONFORMANCE = DOCS / "design" / "conformance.py"
GENERATOR = DOCS / "design" / "synthetic_interval.py"
VERSION_FLOOR = DOCS / "design" / "version_floor.py"
SELECTION = PurePosixPath("design/reports/selection")
DESIGN_LOCK = (
    ("schema", "protasis-design-evidence/v1"),
    ("sha256", "b495f9819f62fa7380434db6bc14c29b47812927492288c92bf51e4301666a47"),
    ("candidate", "range-streamed-logs"),
)
SELECTED = "range-streamed-logs"
REJECTED = ("plan-sized-releases", "stream-bytes-hold-logs", "compact-log-index")
# Two shards of 40 logs, 20 blocks each: a release built in well under a second.
SMALL = ("--shards", "2", "--logs-per-shard", "40", "--shard-width", "20")


def design_lock_rows():
    """Return the rows of the runbook's one design-lock fence, in order."""
    lines = RUNBOOK.read_text(encoding="utf-8").splitlines()
    openings = [index for index, line in enumerate(lines) if line == "```design-lock"]
    if len(openings) != 1:
        raise AssertionError(f"the runbook carries {len(openings)} design-lock fences, not one")
    rows = []
    for line in lines[openings[0] + 1:]:
        if line == "```":
            return tuple(rows)
        key, separator, value = line.partition(" | ")
        if not separator:
            raise AssertionError(f"design-lock row {line!r} is not `key | value`")
        rows.append((key, value))
    raise AssertionError("the runbook's design-lock fence is not closed")


def locked_record():
    return json.loads(RECORD.read_bytes())


def child_environment():
    """PATH and HOME for the interpreter, and nothing else this process carries."""
    environment = {
        "PATH": os.environ.get("PATH", os.defpath),
        "NO_COLOR": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if "HOME" in os.environ:
        environment["HOME"] = os.environ["HOME"]
    return environment


def tree_below(root):
    """Every path under root, relative and in POSIX form."""
    return sorted(
        (Path(parent) / name).relative_to(root).as_posix()
        for parent, directories, files in os.walk(root)
        for name in directories + files
    )


def load_committed_generator():
    """The committed generator as a module, loaded without writing bytecode beside it."""
    spec = importlib.util.spec_from_file_location("committed_synthetic_interval", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    writes_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = writes_bytecode
    return module


class DesignRecordCopyTests(unittest.TestCase):
    def test_the_record_copy_is_the_locked_design_record(self):
        self.assertEqual(design_lock_rows(), DESIGN_LOCK)
        data = RECORD.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), dict(DESIGN_LOCK)["sha256"])
        record = json.loads(data)
        self.assertEqual(record["schema"], dict(DESIGN_LOCK)["schema"])
        self.assertEqual(record["selection"]["candidate"], SELECTED)

    def test_every_selection_report_the_record_binds_is_committed(self):
        resolved = [row for row in locked_record()["results"] if row["state"] != "pending"]
        self.assertEqual(len(resolved), 24)
        bound = set()
        for row in resolved:
            with self.subTest(candidate=row["candidate"], criterion=row["criterion"]):
                self.assertIn(row["state"], ("pass", "fail"))
                relative = PurePosixPath(row["report"]["path"])
                self.assertEqual(relative.parent, SELECTION)
                self.assertEqual(relative.name, f"{row['candidate']}-{row['criterion']}.json")
                path = DOCS.joinpath(*relative.parts)
                self.assertFalse(path.is_symlink(), str(relative))
                self.assertTrue(path.is_file(), str(relative))
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), row["report"]["sha256"]
                )
                bound.add(relative.name)
        committed = {entry.name for entry in DOCS.joinpath(*SELECTION.parts).iterdir()}
        self.assertEqual(committed, bound)

    def test_the_conformance_harness_refuses_every_other_candidate(self):
        record = locked_record()
        others = tuple(
            item["id"] for item in record["candidates"]
            if item["id"] != record["selection"]["candidate"]
        )
        self.assertEqual(others, REJECTED)
        criteria = [item["id"] for item in record["criteria"] if item["stage"] == "conformance"]
        self.assertEqual(len(criteria), 10)
        for candidate in REJECTED:
            for criterion in criteria:
                with self.subTest(candidate=candidate, criterion=criterion):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        # The harness also exits 2 from a directory without
                        # plugins/alexandria; creating it leaves the candidate
                        # check as the only refusal that exits 2.
                        (root / "plugins" / "alexandria").mkdir(parents=True)
                        result = subprocess.run(
                            [sys.executable, str(CONFORMANCE), criterion,
                             "--candidate", candidate],
                            capture_output=True, text=True, check=False,
                            cwd=root, env=child_environment(), timeout=120,
                        )
                        after = tree_below(root)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn(
                        f"only the selected candidate {SELECTED} carries conformance cases; "
                        f"refusing {candidate}",
                        result.stderr,
                    )
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(after, ["plugins", "plugins/alexandria"])


class HarnessRefusalTests(unittest.TestCase):
    """The harness names every refusal it can reach from a bare checkout."""

    def run_harness(self, root, *argv):
        result = subprocess.run(
            [sys.executable, str(CONFORMANCE), *argv],
            capture_output=True, text=True, check=False, cwd=root,
            env=child_environment(), timeout=120,
        )
        return result, tree_below(root)

    def test_a_cell_whose_test_module_is_absent_refuses_by_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "plugins" / "alexandria").mkdir(parents=True)
            result, after = self.run_harness(
                root, "walk-matches-whole-list-derivation")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(
            "conformance: walk-matches-whole-list-derivation loads "
            "plugins/alexandria/tests/test_log_walk.py, which does not exist yet",
            result.stderr,
        )
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(after, ["plugins", "plugins/alexandria"])

    def test_an_unusable_scratch_directory_refuses_by_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "plugins" / "alexandria").mkdir(parents=True)
            missing = root / "no-such-scratch"
            result, after = self.run_harness(
                root, "v2-check-peak-halved", "--scratch", str(missing), "--no-report")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(result.stderr.startswith("conformance: "), result.stderr)
        self.assertIn("no-such-scratch", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(after, ["plugins", "plugins/alexandria"])


class VersionFloorTests(unittest.TestCase):
    """The floor script in a throwaway repository: main below, one step branch at HEAD."""

    def git(self, root, *argv):
        environment = {
            "PATH": os.environ.get("PATH", os.defpath),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
        }
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
             "-c", "commit.gpgsign=false", "-C", str(root), *argv],
            capture_output=True, check=True, env=environment, timeout=60,
        )

    def write_surfaces(self, root, version):
        for name, text in (
            ("plugins/alexandria/.claude-plugin/plugin.json", '{"version": "%s"}\n'),
            ("plugins/alexandria/.codex-plugin/plugin.json", '{"version": "%s"}\n'),
            (".claude-plugin/marketplace.json",
             '{"plugins": [{"name": "alexandria", "version": "%s"}]}\n'),
            ("tests/test_version_propagation.py", 'PINS = {\n    "alexandria": "%s",\n}\n'),
        ):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text % version, encoding="utf-8")

    def build_repository(self, root):
        self.git(root, "init", "-q", "-b", "main")
        self.write_surfaces(root, "0.7.30")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "main")
        self.git(root, "checkout", "-q", "-b", "step")
        self.write_surfaces(root, "0.7.37")
        self.git(root, "commit", "-q", "-a", "-m", "step")
        script = root / ".hexaemeron" / "design" / "version_floor.py"
        script.parent.mkdir(parents=True)
        script.write_bytes(VERSION_FLOOR.read_bytes())
        return script

    def run_floor(self, script, root):
        return subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True, check=False,
            cwd=root, env=child_environment(), timeout=120,
        )

    def test_a_branch_stacked_on_head_does_not_raise_its_own_floor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = self.build_repository(root)
            self.git(root, "branch", "step--audit")
            self.git(root, "checkout", "-q", "step--audit")
            self.git(root, "commit", "-q", "--allow-empty", "-m", "record")
            self.git(root, "checkout", "-q", "step")
            result = self.run_floor(script, root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("floor 0.7.30 claimed by refs/heads/main", result.stdout)
        self.assertIn("above the floor: 0.7.37", result.stdout)

    def test_another_branch_at_the_same_version_still_raises_the_floor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = self.build_repository(root)
            self.git(root, "checkout", "-q", "-b", "sibling", "main")
            self.write_surfaces(root, "0.7.37")
            self.git(root, "commit", "-q", "-a", "-m", "sibling")
            self.git(root, "checkout", "-q", "step")
            result = self.run_floor(script, root)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("floor 0.7.37 claimed by refs/heads/sibling", result.stdout)
        self.assertIn("does not sit above the floor 0.7.37", result.stderr)


class GeneratorTests(unittest.TestCase):
    def generate(self, root, name):
        output = Path(root) / name
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--output", str(output), *SMALL, "--build"],
            capture_output=True, text=True, check=False, cwd=root,
            env=child_environment(), timeout=300,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return json.loads(result.stdout)

    def test_the_generator_is_deterministic_at_a_small_size(self):
        with tempfile.TemporaryDirectory() as directory:
            first = self.generate(directory, "first")
            second = self.generate(directory, "second")
            manifests = [
                (Path(run["release"]) / "manifest.json").read_bytes() for run in (first, second)
            ]
        self.assertRegex(first["release_id"], r"\Asha256:[0-9a-f]{64}\Z")
        self.assertEqual(first["release_id"], second["release_id"])
        self.assertEqual(manifests[0], manifests[1])
        self.assertEqual(first["release_bytes"], second["release_bytes"])
        self.assertLessEqual(first["release_bytes"], first["planned_bytes"])
        self.assertEqual(first["parameters"]["shards"], 2)

    def test_the_generator_refuses_without_disk_headroom(self):
        generator = load_committed_generator()
        parameters = generator.Parameters(shards=2, logs_per_shard=40, shard_width=20)
        planned = parameters.planned_bytes()
        short = int(generator.DISK_HEADROOM * planned) - 1
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "release-tree"
            with mock.patch.object(generator, "free_disk", return_value=short) as reading, \
                    mock.patch.object(generator, "Package",
                                      side_effect=AssertionError("a package was imported")):
                with self.assertRaisesRegex(
                    generator.Refusal,
                    rf"needs 2\.5 times its planned {planned} release bytes free, "
                    rf"\d+ bytes, and .* has {short}; refusing before any file is written\Z",
                ):
                    generator.generate(output, parameters, build=True)
            reading.assert_called_once_with(Path(directory))
            self.assertEqual(tree_below(Path(directory)), [])


if __name__ == "__main__":
    unittest.main()
