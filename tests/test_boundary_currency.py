"""The committed reading boundary must describe the tracked tree it ships with.

Criterion 6 of `plugins/horos/docs/scoped-entry/study.md`. The audit record
carries this failure once already: Marking run, step 4, round 1 refreshed the
boundary by hand after `check` flagged the marking evidence copies as new
sinks, and no guard was written. It recurred two days later, when a commit
regenerated the boundary and added an evidence copy of it in the same change.
This is the guard.

A guard that cannot fail is worth nothing, so the mutations below drive the
same comparison over a temporary repository and require it to name a path in
both directions: an entry the tree earned and the boundary lacks, and an entry
the boundary claims and the tree no longer earns.
"""

from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "horos" / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402

GIT = shutil.which("git")

REFRESH = (
    "regenerate with: python3 "
    "plugins/horos/skills/horos/scripts/horos.py scan . --write"
)


def drifted_paths(root):
    """Every canonical item where the boundary and fresh scan disagree."""
    committed = horos.load_boundary(str(root))
    fresh = horos.boundary_document(
        horos.scan_tree(
            str(root),
            include_untracked=committed.get("universe") == "tracked+untracked",
        )
    )
    return [path for path, _ in horos.diff_boundary_documents(committed, fresh)]


def write(root, relpath, content):
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# Git exports these into any process it spawns. A hook, `git bisect run`, a
# rebase `exec` line: all of them set GIT_DIR and GIT_INDEX_FILE to the outer
# repository. Inheriting them makes `git -C <tempdir> add .` operate on the
# outer index instead, which stages a deletion for every tracked file the
# temporary tree does not contain. Measured once at 1487 phantom deletions with
# every file still on disk, which reads exactly like catastrophic data loss.
GIT_ENV_TO_DROP = (
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_WORK_TREE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_PREFIX",
    "GIT_INTERNAL_SUPER_PREFIX",
)


def git_env(base=None):
    """The environment for a git call against a throwaway tree.

    Every variable that could point git at a different repository is removed
    rather than overridden, so an unset one cannot fall through to the outer
    checkout.
    """
    env = dict(os.environ if base is None else base)
    for name in GIT_ENV_TO_DROP:
        env.pop(name, None)
    env.update(
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@t",
    )
    return env


def git(root, *args):
    subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        ["git", "-C", root, *args],
        capture_output=True,
        check=True,
        env=git_env(),
    )


class GitEnvironmentIsolation(unittest.TestCase):
    """A git call against a throwaway tree must not reach the outer repository.

    This is the guard for a defect that presented as data loss. The helper below
    used to inherit `os.environ` wholesale, so when the suite ran anywhere git
    had exported `GIT_INDEX_FILE` -- a pre-commit hook, `git bisect run`, a
    rebase `exec` -- its `git add .` in a temporary directory staged a deletion
    for every tracked file the temporary tree lacked.
    """

    def test_no_variable_that_could_repoint_git_survives(self):
        polluted = {name: "/somewhere/else" for name in GIT_ENV_TO_DROP}
        env = git_env({**polluted, "PATH": os.environ.get("PATH", "")})
        for name in GIT_ENV_TO_DROP:
            self.assertNotIn(name, env, f"{name} would repoint git at another repository")

    def test_the_identity_variables_are_still_set(self):
        env = git_env({"PATH": os.environ.get("PATH", "")})
        for name in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
                     "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
            self.assertIn(name, env)

    def test_the_helper_leaves_the_outer_index_alone(self):
        """The end-to-end form: pollute the environment and check nothing moved."""
        outer = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"],
            capture_output=True, text=True,
        )
        if outer.returncode != 0:
            self.skipTest("not inside a git work tree")
        index = Path(outer.stdout.strip()) / "index"
        before = index.stat().st_mtime_ns if index.exists() else None

        with tempfile.TemporaryDirectory() as work:
            os.environ["GIT_INDEX_FILE"] = str(index)
            try:
                git(work, "init", "-q")
                write(work, "throwaway.txt", "x\n")
                git(work, "add", ".")
            finally:
                os.environ.pop("GIT_INDEX_FILE", None)

        after = index.stat().st_mtime_ns if index.exists() else None
        self.assertEqual(
            before, after,
            "the outer index was written by a git call meant for a temporary tree",
        )


class BoundaryCurrencyTests(unittest.TestCase):
    def test_the_committed_boundary_matches_a_fresh_scan(self):
        self.assertEqual(drifted_paths(ROOT), [], REFRESH)


@unittest.skipIf(GIT is None, "git unavailable")
class GuardMutationTests(unittest.TestCase):
    """The same comparison, driven against a tree that is deliberately wrong."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        git(self.root, "init", "-q")
        write(self.root, "src/app.py", "value = 1\n")
        write(self.root, "yarn.lock", "# lockfile\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "tracked tree")
        horos.write_boundary(
            self.root, horos.boundary_document(horos.scan_tree(self.root))
        )
        self.assertEqual(drifted_paths(self.root), [])

    def test_a_new_generated_file_without_a_refresh_is_named(self):
        # Assembled rather than spelled: a file containing the marker literal
        # classifies itself as generated, which is the held frontier defect
        # (marker-self-exclusion). Spelling it here would put this guard's own
        # source inside the boundary and leave it unread by every agent that
        # honours one.
        marker = "# Do not " + "edit: generated\n"
        write(self.root, "src/schema.py", marker + "X = 1\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "generated file")
        self.assertEqual(
            drifted_paths(self.root),
            [".horos/boundary.json#counts", "src/schema.py"],
        )

    def test_an_entry_the_tree_no_longer_earns_is_named(self):
        path = os.path.join(self.root, horos.BOUNDARY_RELPATH)
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        document["entries"].append(
            {
                "path": "src/app.py",
                "category": "generated",
                "bytes": 12,
                "evidence": "invented for this test",
                "grade": "hard",
            }
        )
        Path(path).write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.assertEqual(drifted_paths(self.root), ["src/app.py"])

    def test_two_scans_render_the_same_bytes(self):
        first = horos.render(horos.boundary_document(horos.scan_tree(self.root)))
        second = horos.render(horos.boundary_document(horos.scan_tree(self.root)))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
