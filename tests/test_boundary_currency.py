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
    """Every path where the committed boundary and a fresh scan disagree."""
    committed = horos.load_boundary(str(root))
    fresh = fresh_boundary(root, committed)
    return [path for path, _ in horos.diff_documents(committed, fresh)]


def fresh_boundary(root, committed=None):
    """The canonical boundary document for the committed universe."""
    committed = committed or horos.load_boundary(str(root))
    return horos.boundary_document(
        horos.scan_tree(
            str(root),
            include_untracked=committed.get("universe") == "tracked+untracked",
        )
    )


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


class BoundaryCurrencyTests(unittest.TestCase):
    def test_the_committed_boundary_matches_a_fresh_scan(self):
        self.assertEqual(drifted_paths(ROOT), [], REFRESH)

    def test_the_committed_boundary_metadata_matches_a_fresh_scan(self):
        committed = horos.load_boundary(str(ROOT))
        self.assertEqual(committed, fresh_boundary(ROOT, committed), REFRESH)


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
        self.assertEqual(drifted_paths(self.root), ["src/schema.py"])

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
