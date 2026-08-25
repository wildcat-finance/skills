"""Scoped entry: one ancestor boundary, admitting one descendant scope.

The tree every case here starts from:

    repo/
      .gitattributes        vendor-only/** linguist-vendored
      src/app.py
      plugins/one/module.py
      plugins/one/yarn.lock      lockfile, a hard entry inside the scope
      plugins/two/other.py
      plugins/two/go.sum         lockfile, a hard entry in a sibling
      vendor-only/lib.js         tracked, so the attribute rule binds the dir
"""

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

MINIFIED = "var a=1;" * 400 + "\n"
BLOB = "[" + ",".join(['"row"'] * 4000) + "]\n"


def write(root, relpath, content):
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def git(root, *args):
    subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        ["git", "-C", root, *args],
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


def commit_boundary(root):
    result = horos.scan_tree(root)
    horos.write_boundary(root, horos.boundary_document(result))
    horos.write_candidates(root, horos.candidates_document(result))


@unittest.skipIf(GIT is None, "git unavailable")
class ScopedEntryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        git(self.root, "init", "-q")
        git(self.root, "config", "--local", "commit.gpgsign", "false")
        write(self.root, ".gitattributes", "vendor-only/** linguist-vendored\n")
        write(self.root, "src/app.py", "value = 1\n")
        write(self.root, "plugins/one/module.py", "value = 2\n")
        write(self.root, "plugins/one/yarn.lock", "# lockfile\n")
        write(self.root, "plugins/two/other.py", "value = 3\n")
        write(self.root, "plugins/two/go.sum", "# sums\n")
        write(self.root, "vendor-only/lib.js", "module.exports = 1\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "tree")
        commit_boundary(self.root)

    def check(self, target):
        out = io.StringIO()
        code = horos.check_scope_or_tree(target, out=out)
        return code, out.getvalue()

    def scope_of(self, target):
        resolved, reason = horos.resolve_boundary_root(target)
        self.assertIsNotNone(resolved, reason)
        return resolved

    # Resolution

    def test_the_root_check_keeps_its_whole_tree_wording(self):
        code, text = self.check(self.root)
        self.assertEqual(code, 0, text)
        self.assertIn("boundary matches the tree", text)
        self.assertNotIn("scope:", text)

    def test_a_descendant_resolves_the_ancestor_boundary(self):
        boundary_root, scope = self.scope_of(os.path.join(self.root, "plugins", "one"))
        self.assertEqual(boundary_root, self.root)
        self.assertEqual(scope, "plugins/one")

    def test_the_nearest_boundary_wins(self):
        nested = os.path.join(self.root, "plugins")
        commit_boundary(nested)
        boundary_root, scope = self.scope_of(os.path.join(nested, "one"))
        self.assertEqual(boundary_root, nested)
        self.assertEqual(scope, "one")

    def test_a_scope_equal_to_the_boundary_root_is_the_whole_tree(self):
        boundary_root, scope = self.scope_of(self.root)
        self.assertEqual((boundary_root, scope), (self.root, "."))

    def test_a_directory_outside_any_boundary_is_refused(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        resolved, reason = horos.resolve_boundary_root(outside.name)
        self.assertIsNone(resolved)
        self.assertIn("no boundary", reason)

    def test_a_symlink_leaving_the_worktree_is_refused(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        link = os.path.join(self.root, "escape")
        os.symlink(os.path.realpath(outside.name), link)
        resolved, reason = horos.resolve_boundary_root(link)
        self.assertIsNone(resolved)
        self.assertIn("leaves the worktree", reason)

    def test_a_relative_path_climbing_out_of_the_worktree_is_refused(self):
        cwd = os.getcwd()
        os.chdir(os.path.join(self.root, "plugins", "one"))
        try:
            resolved, reason = horos.resolve_boundary_root("../../..")
        finally:
            os.chdir(cwd)
        self.assertIsNone(resolved)
        self.assertIn("leaves the worktree", reason)

    def test_a_symlinked_intermediate_component_is_refused(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        os.makedirs(os.path.join(outside.name, "sub"))
        git(os.path.realpath(outside.name), "init", "-q")
        os.symlink(os.path.realpath(outside.name), os.path.join(self.root, "bridge"))
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            resolved, reason = horos.resolve_boundary_root("bridge/sub")
        finally:
            os.chdir(cwd)
        self.assertIsNone(resolved)
        self.assertIn("leaves the worktree", reason)

    def test_a_sibling_scope_reached_by_a_relative_path_is_admitted(self):
        cwd = os.getcwd()
        os.chdir(os.path.join(self.root, "plugins", "one"))
        try:
            code, text = self.check("../two")
        finally:
            os.chdir(cwd)
        self.assertEqual(code, 0, text)
        self.assertIn("scope: plugins/two", text)

    def test_a_missing_boundary_exits_two(self):
        os.remove(os.path.join(self.root, horos.BOUNDARY_RELPATH))
        resolved, reason = horos.resolve_boundary_root(
            os.path.join(self.root, "plugins", "one")
        )
        self.assertIsNone(resolved)
        self.assertIn("no boundary", reason)

    def test_a_malformed_boundary_exits_two(self):
        path = os.path.join(self.root, horos.BOUNDARY_RELPATH)
        Path(path).write_text("{not json", encoding="utf-8")
        code, text = self.check(os.path.join(self.root, "plugins", "one"))
        self.assertEqual(code, 2)
        self.assertIn("unreadable boundary", text)

    # Admission

    def test_a_clean_scope_is_admitted_and_says_what_it_did_not_evaluate(self):
        code, text = self.check(os.path.join(self.root, "plugins", "one"))
        self.assertEqual(code, 0, text)
        self.assertIn("scope: plugins/one", text)
        self.assertIn("hard boundary: matches", text)
        self.assertIn("outside-scope drift: not evaluated", text)

    def test_an_empty_scope_is_admitted(self):
        empty = os.path.join(self.root, "src", "nothing")
        os.makedirs(empty)
        code, text = self.check(empty)
        self.assertEqual(code, 0, text)
        self.assertIn("hard boundary: matches", text)

    def test_a_scope_that_is_itself_a_directory_entry_matches(self):
        committed = horos.load_boundary(self.root)
        self.assertIn("vendor-only/", [e["path"] for e in committed["entries"]])
        code, text = self.check(os.path.join(self.root, "vendor-only"))
        self.assertEqual(code, 0, text)
        self.assertIn("hard boundary: matches", text)

    def test_an_addition_inside_the_scope_refuses_it(self):
        write(self.root, "plugins/one/package-lock.json", '{"lockfileVersion": 3}\n')
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "new lockfile")
        code, text = self.check(os.path.join(self.root, "plugins", "one"))
        self.assertEqual(code, 1, text)
        self.assertIn("plugins/one/package-lock.json", text)
        self.assertIn("hard boundary: drifted", text)

    def test_a_removal_inside_the_scope_refuses_it(self):
        git(self.root, "rm", "-q", "plugins/one/yarn.lock")
        git(self.root, "commit", "-qm", "drop lockfile")
        code, text = self.check(os.path.join(self.root, "plugins", "one"))
        self.assertEqual(code, 1, text)
        self.assertIn("plugins/one/yarn.lock", text)

    def test_a_changed_entry_inside_the_scope_refuses_it(self):
        write(self.root, "plugins/one/yarn.lock", "# lockfile\n" * 40)
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "grow lockfile")
        code, text = self.check(os.path.join(self.root, "plugins", "one"))
        self.assertEqual(code, 1, text)
        self.assertIn("entry changed", text)

    def test_drift_in_a_sibling_does_not_refuse_the_scope(self):
        write(self.root, "plugins/two/pnpm-lock.yaml", "lockfileVersion: 9\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "sibling lockfile")
        code, text = self.check(os.path.join(self.root, "plugins", "one"))
        self.assertEqual(code, 0, text)
        self.assertNotIn("plugins/two", text)
        whole, _ = self.check(self.root)
        self.assertEqual(whole, 1)

    def test_candidate_drift_inside_the_scope_does_not_refuse_it(self):
        write(self.root, "plugins/one/rows.json", BLOB)
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "blob")
        result = horos.scan_tree(self.root, scope="plugins/one")
        self.assertTrue(
            any(e["path"] == "plugins/one/rows.json" for e in result["candidates"]),
            [e["path"] for e in result["candidates"]],
        )
        code, text = self.check(os.path.join(self.root, "plugins", "one"))
        self.assertEqual(code, 0, text)
        self.assertIn("hard boundary: matches", text)

    # Cost and equivalence

    def test_the_scope_classifies_nothing_outside_itself(self):
        result = horos.scan_tree(self.root, scope="plugins/one")
        for entry in result["entries"] + result["candidates"]:
            self.assertTrue(
                entry["path"].startswith("plugins/one"),
                entry["path"],
            )
        self.assertEqual(result["counts"]["files_walked"], 2)

    def test_an_attribute_file_above_the_scope_is_read_and_counted(self):
        result = horos.scan_tree(self.root, scope="vendor-only")
        self.assertEqual(result["counts"]["attribute_files_above_scope"], 1)
        self.assertIn("vendor-only/", [e["path"] for e in result["entries"]])

    def test_both_invocation_sites_print_the_same_bytes(self):
        target = os.path.join(self.root, "plugins", "one")
        _, from_above = self.check(target)
        cwd = os.getcwd()
        os.chdir(target)
        try:
            _, from_inside = self.check(".")
        finally:
            os.chdir(cwd)
        self.assertEqual(from_above, from_inside)


if __name__ == "__main__":
    unittest.main()
