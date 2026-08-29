"""The scoped-entry example does what its README says it does.

The example is copied into a temporary repository first, so the demonstration
runs against a real tracked tree without the test mutating the checkout it
ships in.
"""

from pathlib import Path
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402

GIT = shutil.which("git")
EXAMPLE = PLUGIN / "examples" / "scoped-entry"

SCOPED_TAIL = [
    "scope: packages/one",
    "hard boundary: matches",
    "candidates: 0 findings, advisory",
    "outside-scope drift: not evaluated",
    "counters: classified 2, listed outside scope 1, attribute files above scope 0",
]

APPENDED = "example.com/other v0.1.0 h1:2222222222222222222222222222222222222222=\n"


def git(root, *args):
    subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        ["git", "-c", "commit.gpgsign=false", "-C", root, *args],
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


@unittest.skipIf(GIT is None, "git unavailable")
class DemonstrationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(os.path.realpath(self._tmp.name), "scoped-entry")
        self.addCleanup(self._tmp.cleanup)
        shutil.copytree(EXAMPLE, self.root)
        git(self.root, "init", "-q")
        git(self.root, "config", "--local", "commit.gpgsign", "false")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "example")

    def check(self, *parts):
        out = io.StringIO()
        code = horos.check_scope_or_tree(os.path.join(self.root, *parts), out=out)
        return code, out.getvalue()

    def test_entering_the_repository_matches_the_documented_wording(self):
        code, text = self.check()
        self.assertEqual(code, 0, text)
        self.assertEqual(text.strip(), "boundary matches the tree")

    def test_entering_one_directory_prints_the_documented_block(self):
        code, text = self.check("packages", "one")
        self.assertEqual(code, 0, text)
        lines = text.strip().splitlines()
        self.assertEqual(lines[0], f"boundary root: {self.root}")
        self.assertEqual(lines[1:], SCOPED_TAIL)

    def test_sibling_drift_refuses_the_tree_and_admits_the_scope(self):
        target = Path(self.root) / "packages" / "two" / "go.sum"
        with target.open("a", encoding="utf-8") as handle:
            handle.write(APPENDED)
        git(self.root, "commit", "-qam", "append to the sibling lockfile")

        whole, whole_text = self.check()
        self.assertEqual(whole, 1, whole_text)
        self.assertIn("packages/two/go.sum", whole_text)

        scoped, scoped_text = self.check("packages", "one")
        self.assertEqual(scoped, 0, scoped_text)
        self.assertIn("hard boundary: matches", scoped_text)
        self.assertIn("outside-scope drift: not evaluated", scoped_text)

    def test_the_documented_refusals_exit_two(self):
        missing = os.path.join(os.path.dirname(self.root), "elsewhere")
        os.makedirs(missing)
        code, text = self.check("..", "elsewhere")
        self.assertEqual(code, 2, text)

        boundary = Path(self.root) / horos.BOUNDARY_RELPATH
        boundary.write_text("{not json", encoding="utf-8")
        code, text = self.check("packages", "one")
        self.assertEqual(code, 2, text)
        self.assertIn("unreadable boundary", text)

    def test_the_readme_quotes_the_output_it_produces(self):
        text = (EXAMPLE / "README.md").read_text(encoding="utf-8")
        for line in SCOPED_TAIL:
            with self.subTest(line=line):
                self.assertIn(line, text)
        self.assertIn(APPENDED.strip(), text)


if __name__ == "__main__":
    unittest.main()
