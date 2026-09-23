"""Hold the committed issue 1888 design records to the record the run locked.

`docs/epoch-table-split/` carries byte copies of the controller's study,
runbook, design record and design folder. Git ignores their `.hexaemeron/`
originals, so these tests read only committed bytes: the digest the runbook's
design-lock fence names, the selection reports the record binds, the
conformance harness's refusal of every candidate the record rejected, and the
committed resolver's git-read cells rerun from where the copy is committed.
"""

import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import unittest


DOCS = Path(__file__).resolve().parents[1] / "docs" / "epoch-table-split"
RECORD = DOCS / "design-evidence.json"
RUNBOOK = DOCS / "runbook.md"
CONFORMANCE = DOCS / "design" / "conformance.py"
RESOLVE = DOCS / "design" / "resolve.py"
SELECTION = PurePosixPath("design/reports/selection")
DESIGN_LOCK = (
    ("schema", "protasis-design-evidence/v1"),
    ("sha256", "94a3d5293c5b03a73cc584a3ea2e1843c4e4659676819d4bff293e4a75850eb5"),
    ("candidate", "split-attribution-parts"),
)
SELECTED = "split-attribution-parts"
REJECTED = ("compact-attribution-rows", "raised-epoch-table-ceiling", "plan-sized-releases")
# Selection cells whose values come from git reads, with the values the record
# binds. edit-sites reads the base commit alone; sites-shared-with-1872 also
# reads the issue 1872 step heads the resolver pins in PR_STEPS.
GIT_READ_CELLS = (
    ("edit-sites", "split-attribution-parts", 31),
    ("edit-sites", "raised-epoch-table-ceiling", 24),
    ("sites-shared-with-1872", "split-attribution-parts", 3),
    ("sites-shared-with-1872", "raised-epoch-table-ceiling", 2),
)


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


def resolver_step_heads():
    """The issue 1872 commits the committed resolver diffs, from its PR_STEPS."""
    for node in ast.parse(RESOLVE.read_bytes()).body:
        if isinstance(node, ast.Assign) and [
            getattr(target, "id", None) for target in node.targets
        ] == ["PR_STEPS"]:
            return sorted({commit for pair in ast.literal_eval(node.value).values()
                           for commit in pair})
    raise AssertionError("the committed resolver declares no PR_STEPS")


def tree_below(root):
    """Every path under root, relative and in POSIX form."""
    return sorted(
        (Path(parent) / name).relative_to(root).as_posix()
        for parent, directories, files in os.walk(root)
        for name in directories + files
    )


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
        self.assertEqual(len(resolved), 36)
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
        self.assertEqual(len(criteria), 4)
        # No staging variable reaches the child, so a harness that skipped the
        # candidate check could not rebuild a demonstration from here.
        environment = {
            "PATH": os.environ.get("PATH", os.defpath),
            "NO_COLOR": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
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
                            cwd=root, env=environment, timeout=120,
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


class CommittedResolverTests(unittest.TestCase):
    def test_the_committed_resolver_reproduces_its_git_read_cells_where_it_is_committed(self):
        results = {(row["candidate"], row["criterion"]): row
                   for row in locked_record()["results"]}
        # Only what git and the interpreter need reaches the child, so an
        # inherited GIT_DIR or GIT_WORK_TREE cannot choose the tree it reads.
        environment = {
            "PATH": os.environ.get("PATH", os.defpath),
            "NO_COLOR": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        if "HOME" in os.environ:
            environment["HOME"] = os.environ["HOME"]
        absent = [
            commit for commit in resolver_step_heads()
            if subprocess.run(
                ["git", "-C", str(DOCS), "cat-file", "-e", f"{commit}^{{commit}}"],
                capture_output=True, check=False, env=environment, timeout=60,
            ).returncode != 0
        ]
        for criterion, candidate, value in GIT_READ_CELLS:
            with self.subTest(criterion=criterion, candidate=candidate):
                if criterion == "sites-shared-with-1872" and absent:
                    self.skipTest("this clone lacks the issue 1872 step heads "
                                  + ", ".join(absent))
                relative = PurePosixPath(results[(candidate, criterion)]["report"]["path"])
                bound = DOCS.joinpath(*relative.parts).read_bytes()
                self.assertEqual(json.loads(bound)["value"], value)
                with tempfile.TemporaryDirectory() as directory:
                    # A working directory outside the repository leaves the
                    # script's own location as its only route to the root.
                    result = subprocess.run(
                        [sys.executable, str(RESOLVE), criterion, "--candidate", candidate],
                        capture_output=True, check=False, cwd=directory,
                        env=environment, timeout=300,
                    )
                    after = tree_below(Path(directory))
                self.assertEqual(
                    result.returncode, 0, result.stderr.decode("utf-8", "replace"))
                self.assertEqual(result.stdout, bound)
                self.assertEqual(after, [])


if __name__ == "__main__":
    unittest.main()
