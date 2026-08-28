"""The scan's universe: tracked by default, widened on request, walked
when git cannot answer."""

from pathlib import Path
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402

GIT = shutil.which("git")


def write(root, relpath, content):
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        content = content.encode("utf-8")
    path.write_bytes(content)
    return path


def git(root, *args):
    subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        ["git", "-C", root, *args],
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


def is_ignored(root, relpath):
    """Whether git excludes a path, by any of the mechanisms it consults."""
    completed = subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        ["git", "-C", root, "check-ignore", "-q", relpath],
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


@unittest.skipIf(GIT is None, "git unavailable")
class UniverseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        git(self.root, "init", "-q")
        # Fixture history is not signing evidence, so inherited signing must
        # not decide whether the repository can be built.
        git(self.root, "config", "--local", "commit.gpgsign", "false")
        write(self.root, ".gitignore", "ignored.wasm\n")
        write(self.root, "src/app.py", "x = 1\n")
        write(self.root, "tracked.wasm", b"\x00asm\x01\x00\x00\x00")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "seed")
        # Local products that never entered git.
        write(self.root, "untracked.wasm", b"\x00asm\x01\x00\x00\x00")
        write(self.root, "ignored.wasm", b"\x00asm\x01\x00\x00\x00")

    def paths(self, include_untracked=False):
        result = horos.scan_tree(self.root, include_untracked=include_untracked)
        listed = [entry["path"] for entry in result["entries"]]
        return result, listed

    def test_the_default_universe_is_tracked_only(self):
        result, listed = self.paths()
        self.assertEqual(result["universe"], "tracked")
        self.assertIn("tracked.wasm", listed)
        self.assertNotIn("untracked.wasm", listed)
        self.assertNotIn("ignored.wasm", listed)

    def test_include_untracked_widens_but_never_to_ignored(self):
        result, listed = self.paths(include_untracked=True)
        self.assertEqual(result["universe"], "tracked+untracked")
        self.assertIn("tracked.wasm", listed)
        self.assertIn("untracked.wasm", listed)
        self.assertNotIn("ignored.wasm", listed)

    def test_a_non_git_tree_walks_the_filesystem(self):
        with tempfile.TemporaryDirectory() as plain:
            write(plain, "loose.wasm", b"\x00asm\x01\x00\x00\x00")
            result = horos.scan_tree(plain)
            self.assertEqual(result["universe"], "filesystem")
            self.assertIn(
                "loose.wasm", [entry["path"] for entry in result["entries"]]
            )

    def test_the_boundary_document_records_its_universe(self):
        document = horos.boundary_document(horos.scan_tree(self.root))
        self.assertEqual(document["universe"], "tracked")

    def test_check_reproduces_the_committed_universe(self):
        result = horos.scan_tree(self.root, include_untracked=True)
        horos.write_boundary(self.root, horos.boundary_document(result))
        out = io.StringIO()
        code = horos.check_tree(self.root, out=out)
        self.assertEqual(code, 0)
        self.assertIn("boundary matches the tree", out.getvalue())

    def test_an_aggregated_directory_counts_only_universe_files(self):
        write(self.root, "node_modules/dep/package.json", '{"name": "dep"}\n')
        write(self.root, "node_modules/dep/index.js", "module.exports = 1\n")
        git(self.root, "add", "-f", "node_modules")
        git(self.root, "commit", "-q", "-m", "vendor")
        write(self.root, "node_modules/dep/local-cache.js", "cache\n" * 10)
        result = horos.scan_tree(self.root)
        entry = {e["path"]: e for e in result["entries"]}["node_modules/"]
        self.assertEqual(entry["files"], 2)


MINIFIED = "var a=1;" * 400 + "\n"


@unittest.skipIf(GIT is None, "git unavailable")
class BindingDirectoryTests(unittest.TestCase):
    """A hard directory entry must cover at least one file in the universe.

    Without this, a boundary check answers differently on two machines: an
    ignored build directory or a stray worktree is present in one checkout and
    absent from the other, so the check drifts against local state instead of
    against the tree.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        git(self.root, "init", "-q")
        git(self.root, "config", "--local", "commit.gpgsign", "false")
        write(self.root, ".gitignore", "node_modules/\nout/\nvendor-only/\n")
        write(self.root, "src/app.py", "value = 1\n")

    def paths(self, result):
        return [entry["path"] for entry in result["entries"]]

    def test_a_vendored_name_holding_nothing_tracked_earns_no_entry(self):
        write(self.root, "node_modules/dep/package.json", '{"name": "dep"}\n')
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "tracked")
        self.assertNotIn("node_modules/", self.paths(horos.scan_tree(self.root)))

    def test_a_corroborated_generated_name_holding_nothing_tracked_earns_no_entry(self):
        write(self.root, "out/bundle.min.js", MINIFIED)
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "tracked")
        self.assertNotIn("out/", self.paths(horos.scan_tree(self.root)))

    def test_one_tracked_file_is_enough_to_bind_the_directory(self):
        write(self.root, "node_modules/dep/package.json", '{"name": "dep"}\n')
        git(self.root, "add", "-f", "node_modules/dep/package.json", "src", ".gitignore")
        git(self.root, "commit", "-q", "-m", "one tracked")
        write(self.root, "node_modules/dep/local-cache.js", "cache\n" * 20)
        write(self.root, "node_modules/other/index.js", "module.exports = 2\n")
        entries = {entry["path"]: entry for entry in horos.scan_tree(self.root)["entries"]}
        self.assertIn("node_modules/", entries)
        self.assertEqual(entries["node_modules/"]["files"], 1)

    def test_an_attribute_matched_directory_holding_nothing_tracked_earns_no_entry(self):
        write(self.root, ".gitattributes", "vendor-only/** linguist-vendored\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "attributes")
        write(self.root, "vendor-only/lib.js", "module.exports = 3\n")
        self.assertNotIn("vendor-only/", self.paths(horos.scan_tree(self.root)))

    def test_the_filesystem_fallback_still_binds_an_untracked_directory(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        write(outside.name, "node_modules/dep/package.json", '{"name": "dep"}\n')
        result = horos.scan_tree(outside.name)
        self.assertEqual(result["universe"], "filesystem")
        self.assertIn("node_modules/", self.paths(result))


@unittest.skipIf(GIT is None, "git unavailable")
class CandidateBindingTests(unittest.TestCase):
    """The advisory pass answers to the universe the binding pass does.

    A candidate directory is uncorroborated by construction, so it is never
    excluded from reading. It is still written to a file a maintainer commits,
    and a finding raised by a local virtualenv or a checked-out worktree cannot
    be reproduced, promoted or even seen anywhere else: every scan on the
    machine that has it dirties the report, and no scan on any other machine
    agrees. Both outputs therefore cover the same files.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        git(self.root, "init", "-q")
        git(self.root, "config", "--local", "commit.gpgsign", "false")
        write(self.root, ".gitignore", "local/\n")
        write(self.root, "src/app.py", "value = 1\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "seed")

    def outputs(self, **kwargs):
        """Every path either output names, from one scan."""
        result = horos.scan_tree(self.root, **kwargs)
        return (
            [entry["path"] for entry in result["entries"]],
            [entry["path"] for entry in result["candidates"]],
        )

    def test_an_ignored_candidate_directory_appears_in_neither_output(self):
        # Plain prose under a candidate name: the name alone is the signal, so
        # nothing corroborates it and the directory takes the advisory path.
        write(self.root, "local/build/notes.txt", "hand-written, not generated\n")
        entries, candidates = self.outputs()
        self.assertNotIn("local/build/", entries)
        self.assertNotIn("local/build/", candidates)

    def test_include_untracked_reaches_the_untracked_but_not_the_ignored(self):
        write(self.root, "local/build/notes.txt", "hand-written, not generated\n")
        write(self.root, "scratch/build/notes.txt", "hand-written, not generated\n")
        entries, candidates = self.outputs(include_untracked=True)
        self.assertNotIn("local/build/", entries)
        self.assertNotIn("local/build/", candidates)
        self.assertIn("scratch/build/", candidates)

    def test_one_tracked_file_still_raises_the_candidate(self):
        write(self.root, "pkg/build/notes.txt", "hand-written, not generated\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "tracked build")
        _, candidates = self.outputs()
        self.assertIn("pkg/build/", candidates)

    def test_the_filesystem_fallback_still_raises_the_candidate(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        write(outside.name, "build/notes.txt", "hand-written, not generated\n")
        result = horos.scan_tree(outside.name)
        self.assertEqual(result["universe"], "filesystem")
        self.assertIn("build/", [entry["path"] for entry in result["candidates"]])

    def test_a_nested_worktree_is_invisible_even_when_nothing_ignores_it(self):
        """A worktree is checked out, not ignored, and not every repository
        excludes the directory its worktrees land in. It stays out anyway: its
        files belong to another checkout's index, never to this one's, and git
        reports the whole worktree as a single opaque directory rather than
        enumerating what is inside it. Nothing under it can enter the universe,
        so the build directory in the checkout binds nothing."""
        git(self.root, "worktree", "add", "-q", ".claude/worktrees/wt", "-b", "other")
        write(
            self.root,
            ".claude/worktrees/wt/build/notes.txt",
            "hand-written, not generated\n",
        )
        nested = ".claude/worktrees/wt/build/"
        self.assertFalse(is_ignored(self.root, ".claude/worktrees"))
        for widened in (False, True):
            with self.subTest(include_untracked=widened):
                entries, candidates = self.outputs(include_untracked=widened)
                self.assertNotIn(nested, entries)
                self.assertNotIn(nested, candidates)


if __name__ == "__main__":
    unittest.main()
