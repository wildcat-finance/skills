"""The four evidence families stay readable, and the maintainer still decides.

Each guard here is written to fail by assertion against the classifier this
step started from, so the module names only what that classifier already
exports. A family file is checked in the three placements that hid it: a
served generated directory, a maintainer's broad set pattern with an explicit
readable line, and plain geometry beside an archive part the maintainer
excludes. In every placement the part and the siblings stay excluded, and the
eight near misses get nothing.

The representatives are 64 MiB because that is the size at which geometry
alone decides; they are written sparse, so the size is real and the cost is
not. Every git subprocess runs in a throwaway repository with every `GIT_*`
variable dropped, so an index a hook exported cannot reach the outer tree.
"""

from pathlib import Path
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402

GIT = shutil.which("git")

# The four names, and the eight names that look like them and are not.
FAMILIES = ("manifest.json", "statement.json", "SHA256SUMS", "events.jsonl")
NEAR_MISSES = {
    "manifest.json": ("manifest.jsonl", "Manifest.json"),
    "statement.json": ("statements.json", "Statement.json"),
    "SHA256SUMS": ("SHA256SUMS.txt", "sha256sums"),
    "events.jsonl": ("events.json", "Events.jsonl"),
}

# Large enough that geometry, not content, decides.
REPRESENTATIVE_BYTES = 64 * 1024 * 1024
PART = "ledger.tar.part-aa"
PART_RULE = "*.part-* linguist-generated\n"
BUNDLES = ("bundle-a.js", "bundle-b.js", "bundle-c.js")


def write(root, relpath, content):
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        content = content.encode("utf-8")
    path.write_bytes(content)
    return path


def write_representative(root, relpath, size=REPRESENTATIVE_BYTES):
    """A single-line file of `size` bytes, written sparse.

    The first 4,096 bytes carry no newline, which is the whole of what the
    classifier reads, and the rest of the length is a hole.
    """
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(b"{" + b"x" * 8191)
        handle.truncate(size)
    return path


def single_line(marker):
    """Minified-looking bytes: one line, no newline, comfortably over the
    blob threshold."""
    return (marker + "=").encode("utf-8") + b"9" * 20000


def git_env():
    """The outer repository, removed rather than overridden.

    Git exports GIT_DIR, GIT_INDEX_FILE and the rest into anything it spawns,
    so a test run from a hook or a `bisect run` line would otherwise stage
    against the outer index. Every GIT_* name goes, then the identity the
    throwaway repository needs comes back.
    """
    env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    env.update(
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@t",
    )
    return env


def git(root, *args):
    subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        ["git", "-c", "commit.gpgsign=false", "-C", root, *args],
        capture_output=True,
        check=True,
        env=git_env(),
    )


def check_attr_set(root, relpath, env=None):
    """True when `git check-attr` reports either linguist attribute set.

    Dropping every `GIT_*` name leaves `HOME` and `XDG_CONFIG_HOME` behind, and
    the per-user attributes file under either one still decides a path the
    throwaway repository's own `.gitattributes` leaves unspecified. Two case
    bodies below hold such paths, so without this pin the comparison would
    answer one way here and another on a maintainer whose
    `~/.config/git/attributes` names one of them. A `core.attributesFile` given
    on the command line outranks that default, and the path it names is never
    written.
    """
    completed = subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        [
            "git",
            "-c",
            "core.attributesFile=" + os.path.join(root, ".absent-attributes"),
            "-C",
            root,
            "check-attr",
            "linguist-generated",
            "linguist-vendored",
            "--",
            relpath,
        ],
        capture_output=True,
        check=True,
        env=env or git_env(),
    )
    states = []
    for line in completed.stdout.decode("utf-8", errors="replace").splitlines():
        if line.endswith(": set"):
            states.append(True)
    return any(states)


def covering_entry(result, relpath):
    """The hard entry that excludes a path: its own, or a directory above it."""
    for entry in result["entries"]:
        path = entry["path"]
        if path == relpath:
            return entry
        if path.endswith("/") and relpath.startswith(path):
            return entry
    return None


def advisory_entry(result, relpath):
    for entry in result["candidates"]:
        path = entry["path"]
        if path == relpath:
            return entry
        if path.endswith("/") and relpath.startswith(path):
            return entry
    return None


class PlacementMixin:
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def assert_readable(self, result, relpath):
        entry = covering_entry(result, relpath)
        self.assertIsNone(
            entry, f"{relpath} is excluded by {entry['path'] if entry else None}"
        )
        advisory = advisory_entry(result, relpath)
        self.assertIsNone(
            advisory, f"{relpath} is still advised against as {advisory}"
        )

    def assert_unprotected(self, result, relpath):
        """A near miss keeps whatever the classifier already said about it."""
        self.assertTrue(
            covering_entry(result, relpath) is not None
            or advisory_entry(result, relpath) is not None,
            f"{relpath} gained protection it has no name for",
        )

    def assert_excluded(self, result, relpath):
        self.assertIsNotNone(
            covering_entry(result, relpath), f"{relpath} lost its hard entry"
        )


class GeometryPlacementTests(PlacementMixin, unittest.TestCase):
    """A 64 MiB family file beside an archive part the maintainer excludes."""

    def build(self, family):
        write(self.root, ".gitattributes", PART_RULE)
        write(self.root, PART, single_line("part"))
        write_representative(self.root, family)
        suffix_miss, case_miss = NEAR_MISSES[family]
        write_representative(self.root, suffix_miss)
        write_representative(self.root, f"variants/{case_miss}")
        return horos.scan_tree(self.root)

    def test_each_family_stays_readable_beside_an_excluded_archive_part(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                self.setUp()
                result = self.build(family)
                self.assert_readable(result, family)
                self.assert_excluded(result, PART)
                suffix_miss, case_miss = NEAR_MISSES[family]
                self.assert_unprotected(result, suffix_miss)
                self.assert_unprotected(result, f"variants/{case_miss}")


class ServedDirectoryPlacementTests(PlacementMixin, unittest.TestCase):
    """A corroborated `out/` splits around the family file it holds."""

    def build(self, family):
        write(self.root, ".gitattributes", PART_RULE)
        for bundle in BUNDLES:
            write(self.root, f"out/{bundle}", single_line(bundle))
        write(self.root, f"out/{PART}", single_line("part"))
        write_representative(self.root, f"out/{family}")
        suffix_miss, case_miss = NEAR_MISSES[family]
        write_representative(self.root, f"out/{suffix_miss}")
        write_representative(self.root, f"out/variants/{case_miss}")
        return horos.scan_tree(self.root)

    def test_each_family_survives_a_corroborated_served_directory(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                self.setUp()
                result = self.build(family)
                self.assert_readable(result, f"out/{family}")
                self.assert_excluded(result, f"out/{PART}")
                for bundle in BUNDLES:
                    self.assert_excluded(result, f"out/{bundle}")
                suffix_miss, case_miss = NEAR_MISSES[family]
                self.assert_unprotected(result, f"out/{suffix_miss}")
                self.assert_unprotected(result, f"out/variants/{case_miss}")

    def test_the_split_evidence_names_the_readable_file(self):
        result = self.build("manifest.json")
        entry = covering_entry(result, "out/bundle-a.js")
        self.assertIsNotNone(entry)
        self.assertIn("directory name out corroborated by", entry["evidence"])
        self.assertIn(
            "; split around readable out/manifest.json", entry["evidence"]
        )

    def test_a_split_keeps_an_attribute_set_file_on_its_own_evidence(self):
        result = self.build("manifest.json")
        entry = covering_entry(result, f"out/{PART}")
        self.assertEqual(entry["path"], f"out/{PART}")
        self.assertIn("linguist-generated for '*.part-*'", entry["evidence"])

    def test_a_served_directory_with_no_readable_file_stays_one_entry(self):
        write(self.root, ".gitattributes", PART_RULE)
        for bundle in BUNDLES:
            write(self.root, f"out/{bundle}", single_line(bundle))
        result = horos.scan_tree(self.root)
        self.assertIsNotNone(covering_entry(result, f"out/{BUNDLES[0]}"))
        self.assertEqual(
            covering_entry(result, f"out/{BUNDLES[0]}")["path"], "out/"
        )


class MaintainerPatternPlacementTests(PlacementMixin, unittest.TestCase):
    """A broad set pattern, with one explicit readable line inside it."""

    def build(self, family, readable_line=True):
        rules = PART_RULE + "releases/** linguist-generated\n"
        if readable_line:
            rules += f"releases/**/{family} -linguist-generated\n"
        write(self.root, ".gitattributes", rules)
        write(self.root, f"releases/v1/{PART}", single_line("part"))
        write_representative(self.root, f"releases/v1/{family}")
        suffix_miss, case_miss = NEAR_MISSES[family]
        write_representative(self.root, f"releases/v1/{suffix_miss}")
        write_representative(self.root, f"releases/v1/variants/{case_miss}")
        return horos.scan_tree(self.root)

    def test_each_family_follows_an_explicit_readable_line(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                self.setUp()
                result = self.build(family)
                self.assert_readable(result, f"releases/v1/{family}")
                self.assert_excluded(result, f"releases/v1/{PART}")
                suffix_miss, case_miss = NEAR_MISSES[family]
                self.assert_unprotected(result, f"releases/v1/{suffix_miss}")
                self.assert_unprotected(
                    result, f"releases/v1/variants/{case_miss}"
                )

    def test_a_maintainers_set_attribute_still_excludes_each_family_name(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                self.setUp()
                result = self.build(family, readable_line=False)
                entry = covering_entry(result, f"releases/v1/{family}")
                self.assertIsNotNone(
                    entry, f"the maintainer's set line lost {family}"
                )
                self.assertIn("linguist-generated", entry["evidence"])


class DirectCallTests(PlacementMixin, unittest.TestCase):
    """`classify_file` answers a direct caller the way the walk does."""

    def test_classify_file_leaves_each_family_name_unclassified(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                self.setUp()
                write_representative(self.root, f"release/{family}")
                self.assertIsNone(horos.classify_file(self.root, f"release/{family}"))

    def test_classify_file_still_classifies_every_near_miss(self):
        for family in FAMILIES:
            for miss in NEAR_MISSES[family]:
                with self.subTest(near_miss=miss):
                    self.setUp()
                    write_representative(self.root, f"release/{miss}")
                    self.assertIsNotNone(
                        horos.classify_file(self.root, f"release/{miss}")
                    )


# Each case is (name, .gitattributes body, {relpath: contents}). The probe
# files are ordinary source no heuristic touches, so any hard coverage they
# carry came from an attribute and can be compared with what Git reports.
ATTRIBUTE_CASES = (
    (
        "unset",
        "assets/** linguist-generated\nassets/keep.js -linguist-generated\n",
        {"assets/keep.js": "module.exports = 1\n", "assets/other.js": "module.exports = 2\n"},
    ),
    (
        "false",
        "assets/** linguist-generated\nassets/keep.js linguist-generated=false\n",
        {"assets/keep.js": "module.exports = 1\n", "assets/other.js": "module.exports = 2\n"},
    ),
    (
        "bang",
        "assets/** linguist-generated\nassets/keep.js !linguist-generated\n",
        {"assets/keep.js": "module.exports = 1\n", "assets/other.js": "module.exports = 2\n"},
    ),
    (
        "nested-unset",
        "assets/** linguist-generated\n",
        {
            "assets/.gitattributes": "keep.js -linguist-generated\n",
            "assets/keep.js": "module.exports = 1\n",
            "assets/other.js": "module.exports = 2\n",
        },
    ),
    (
        "unset-before-set",
        "assets/keep.js -linguist-generated\nassets/** linguist-generated\n",
        {"assets/keep.js": "module.exports = 1\n", "assets/other.js": "module.exports = 2\n"},
    ),
    (
        "macro-definition",
        "[attr]generated-blob linguist-generated\nassets/** linguist-vendored\n",
        {"agenerated-blob": "notes\n", "assets/lib.js": "module.exports = 3\n"},
    ),
    (
        "family-under-a-set-line",
        "releases/** linguist-generated\n",
        {
            "releases/manifest.json": '{"release": 1}\n',
            "docs/manifest.json": '{"doc": 1}\n',
            "docs/notes.md": "notes\n",
        },
    ),
)


@unittest.skipIf(GIT is None, "git unavailable")
class GitParityTests(unittest.TestCase):
    """Hard coverage equals the set state `git check-attr` reports."""

    def build(self, body, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = os.path.realpath(tmp.name)
        git(root, "init", "-q")
        git(root, "config", "--local", "commit.gpgsign", "false")
        write(root, ".gitattributes", body)
        for relpath, content in files.items():
            write(root, relpath, content)
        git(root, "add", ".")
        git(root, "commit", "-q", "-m", "case")
        return root

    def test_every_attribute_case_matches_git(self):
        for name, body, files in ATTRIBUTE_CASES:
            with self.subTest(case=name):
                root = self.build(body, files)
                result = horos.scan_tree(root)
                for relpath in sorted(files):
                    if relpath.endswith(".gitattributes"):
                        continue
                    expected = check_attr_set(root, relpath)
                    covered = covering_entry(result, relpath) is not None
                    self.assertEqual(
                        covered,
                        expected,
                        f"{name}: {relpath} covered={covered}, git set={expected}",
                    )

    def test_a_per_user_attributes_file_does_not_move_the_comparison(self):
        """The comparison answers the same on every host.

        `family-under-a-set-line` leaves `docs/manifest.json` unspecified in
        the tree, which is exactly where git falls back to the per-user file.
        Horos reads no such file, so an unpinned comparison would report the
        family excluded on a maintainer carrying this rule and readable here.
        """
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        write(home.name, ".config/git/attributes", "docs/** linguist-generated\n")
        env = git_env()
        env["HOME"] = home.name
        env["XDG_CONFIG_HOME"] = os.path.join(home.name, ".config")
        body = dict(
            (name, (body, files)) for name, body, files in ATTRIBUTE_CASES
        )["family-under-a-set-line"]
        root = self.build(*body)
        result = horos.scan_tree(root)
        for relpath in ("docs/manifest.json", "docs/notes.md"):
            with self.subTest(path=relpath):
                self.assertFalse(
                    check_attr_set(root, relpath, env=env),
                    f"{relpath}: a per-user attributes file reached check-attr",
                )
                self.assertIsNone(covering_entry(result, relpath))


@unittest.skipIf(GIT is None, "git unavailable")
class ScopedSplitCheckTests(unittest.TestCase):
    """A scoped check over a directory the family file split."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        git(self.root, "init", "-q")
        git(self.root, "config", "--local", "commit.gpgsign", "false")
        write(self.root, ".gitattributes", PART_RULE)
        write(self.root, "src/app.py", "value = 1\n")
        for bundle in BUNDLES:
            write(self.root, f"out/{bundle}", single_line(bundle))
        write(self.root, f"out/{PART}", single_line("part"))
        write(self.root, "out/manifest.json", single_line("manifest"))
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "tree")
        result = horos.scan_tree(self.root)
        horos.write_boundary(self.root, horos.boundary_document(result))
        horos.write_candidates(self.root, horos.candidates_document(result))

    def test_the_split_directory_is_per_file_entries(self):
        result = horos.scan_tree(self.root)
        paths = [entry["path"] for entry in result["entries"]]
        self.assertNotIn("out/", paths)
        self.assertIn(f"out/{BUNDLES[0]}", paths)
        self.assertNotIn("out/manifest.json", paths)

    def test_a_scoped_check_over_the_split_directory_passes(self):
        out = io.StringIO()
        code = horos.check_scope_or_tree(os.path.join(self.root, "out"), out=out)
        text = out.getvalue()
        self.assertEqual(code, 0, text)
        self.assertIn("scope: out", text)
        self.assertIn("hard boundary: matches", text)


if __name__ == "__main__":
    unittest.main()
