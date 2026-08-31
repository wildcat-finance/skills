"""The read boundary: what it accepts, and every way it refuses by name."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from dokimasia_lib import paths  # noqa: E402


class DeclaredRootTests(unittest.TestCase):
    def test_a_directory_resolves(self):
        with tempfile.TemporaryDirectory() as raw:
            self.assertEqual(paths.declared_root(raw), Path(raw).resolve())

    def test_a_symlinked_root_refuses_by_name(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            (base / "real").mkdir()
            (base / "link").symlink_to(base / "real", target_is_directory=True)
            with self.assertRaises(paths.PathRefusal) as caught:
                paths.declared_root(base / "link")
        self.assertIn("is a symlink", str(caught.exception))

    def test_a_file_is_not_a_root(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "f.txt"
            target.write_text("x", encoding="utf-8")
            with self.assertRaises(paths.PathRefusal) as caught:
                paths.declared_root(target)
        self.assertIn("is not a directory", str(caught.exception))


class RelativeWithinTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = paths.declared_root(self.tmp.name)

    def test_an_ordinary_relative_path_is_accepted(self):
        self.assertEqual(
            paths.relative_within(self.root, "src/app/page.tsx"),
            PurePosixPath("src/app/page.tsx"),
        )

    def test_an_absolute_path_refuses_by_name(self):
        with self.assertRaises(paths.PathRefusal) as caught:
            paths.relative_within(self.root, "/etc/passwd")
        self.assertIn("absolute path", str(caught.exception))

    def test_a_parent_directory_segment_refuses_by_name(self):
        with self.assertRaises(paths.PathRefusal) as caught:
            paths.relative_within(self.root, "src/../../outside.ts")
        self.assertIn("parent-directory segment", str(caught.exception))


class WalkAndReadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / "src").mkdir()
        (self.base / "src" / "a.tsx").write_text("export default function A() {}", encoding="utf-8")
        self.root = paths.declared_root(self.base)

    def test_the_walk_is_sorted_so_a_digest_can_be_reproducible(self):
        for name in ("z.tsx", "m.tsx", "b.tsx"):
            (self.base / "src" / name).write_text("export default function X() {}", encoding="utf-8")
        found = paths.source_files(self.root, frozenset({".tsx"}))
        self.assertEqual(found, sorted(found))

    def test_a_symlinked_file_is_not_walked(self):
        (self.base / "src" / "link.tsx").symlink_to(self.base / "src" / "a.tsx")
        found = paths.source_files(self.root, frozenset({".tsx"}))
        self.assertNotIn(PurePosixPath("src/link.tsx"), found)

    def test_a_nested_checkout_is_pruned(self):
        nested = self.base / "vendored"
        (nested / ".git").mkdir(parents=True)
        (nested / "b.tsx").write_text("export default function B() {}", encoding="utf-8")
        found = paths.source_files(self.root, frozenset({".tsx"}))
        self.assertNotIn(PurePosixPath("vendored/b.tsx"), found)

    def test_an_over_deep_tree_refuses_by_name(self):
        deep = self.base
        for level in range(paths.MAX_DEPTH + 2):
            deep = deep / f"d{level}"
        deep.mkdir(parents=True)
        (deep / "p.tsx").write_text("export default function D() {}", encoding="utf-8")
        with self.assertRaises(paths.PathRefusal) as caught:
            paths.source_files(self.root, frozenset({".tsx"}))
        self.assertIn("deeper than", str(caught.exception))

    def test_an_over_large_file_count_refuses_by_name(self):
        for index in range(4):
            (self.base / "src" / f"p{index}.tsx").write_text("export default function P() {}", encoding="utf-8")
        with self.assertRaises(paths.PathRefusal) as caught:
            paths.source_files(self.root, frozenset({".tsx"}), max_files=2)
        self.assertIn("2-file cap", str(caught.exception))

    def test_the_file_count_cap_is_a_parameter_and_never_a_mutated_global(self):
        # A cap that a library function lowers in place is a cap another caller
        # can observe lowered. Passing it keeps the declared value fixed.
        before = paths.MAX_FILES
        with self.assertRaises(paths.PathRefusal):
            paths.source_files(self.root, frozenset({".tsx"}), max_files=0)
        self.assertEqual(paths.MAX_FILES, before)

    def test_an_oversized_file_refuses_by_name(self):
        big = self.base / "src" / "big.tsx"
        big.write_bytes(b"x" * (paths.MAX_FILE_BYTES + 1))
        with self.assertRaises(paths.PathRefusal) as caught:
            paths.read_source(self.root, PurePosixPath("src/big.tsx"))
        self.assertIn("over the", str(caught.exception))

    def test_reading_a_symlink_refuses_by_name(self):
        (self.base / "src" / "link.tsx").symlink_to(self.base / "src" / "a.tsx")
        with self.assertRaises(paths.PathRefusal) as caught:
            paths.read_source(self.root, PurePosixPath("src/link.tsx"))
        self.assertIn("is a symlink", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
