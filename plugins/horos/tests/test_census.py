"""The census shares the boundary's walk and its numbers add up."""

from pathlib import Path
from unittest import mock
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN / "examples" / "fixture"


def write(root, relpath, content):
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        content = content.encode("utf-8")
    path.write_bytes(content)
    return path


class CensusTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def census(self):
        return horos.census_document(horos.scan_tree(self.root, census=True))

    def rows(self):
        return {row["suffix"]: row for row in self.census()["rows"]}

    def test_files_bucket_by_lowercased_last_suffix(self):
        write(self.root, "a.PY", "x = 1\n")
        write(self.root, "b.py", "y = 2\n")
        write(self.root, "notes.txt", "words\n")
        rows = self.rows()
        self.assertEqual(rows[".py"]["files"], 2)
        self.assertEqual(rows[".txt"]["files"], 1)

    def test_a_dotless_or_dotfile_name_is_no_suffix(self):
        write(self.root, "Makefile", "all:\n")
        write(self.root, ".gitignore", "dist\n")
        rows = self.rows()
        self.assertEqual(rows["(no suffix)"]["files"], 2)

    def test_a_vendored_file_lands_in_its_suffix_row_as_boundary_bytes(self):
        write(self.root, "node_modules/dep/package.json", '{"name": "dep"}\n')
        write(self.root, "node_modules/dep/index.js", "module.exports = 1\n")
        write(self.root, "src/app.js", "const a = 1\n")
        rows = self.rows()
        self.assertEqual(rows[".js"]["files"], 2)
        self.assertEqual(rows[".js"]["boundary_bytes"], 19)
        self.assertEqual(rows[".js"]["bytes"], 19 + 12)

    def test_rows_sum_to_the_totals_and_boundary_never_exceeds_bytes(self):
        write(self.root, "yarn.lock", "lock\n")
        write(self.root, "src/app.py", "x = 1\n")
        write(self.root, "assets/logo.bin", b"\x00" * 9)
        document = self.census()
        self.assertEqual(
            sum(row["bytes"] for row in document["rows"]), document["total_bytes"]
        )
        self.assertEqual(
            sum(row["files"] for row in document["rows"]), document["total_files"]
        )
        for row in document["rows"]:
            self.assertLessEqual(row["boundary_bytes"], row["bytes"])

    def test_symlinks_and_skipped_directories_are_in_neither_walk(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        write(outside.name, "big.dat", b"z" * 100)
        os.symlink(os.path.join(outside.name, "big.dat"), os.path.join(self.root, "alias.dat"))
        write(self.root, ".horos/census.json", "{}")
        write(self.root, "__pycache__/x.pyc", b"\x00")
        write(self.root, "kept.py", "x = 1\n")
        rows = self.rows()
        self.assertEqual(set(rows), {".py"})

    def test_the_census_is_deterministic_and_sorted(self):
        write(self.root, "b.ts", "const b = 2\n")
        write(self.root, "a.ts", "const a = 1\n")
        write(self.root, "big.bin", b"\x00" * 500)
        first = horos.render(self.census())
        second = horos.render(self.census())
        self.assertEqual(first, second)
        rows = self.census()["rows"]
        self.assertEqual(rows[0]["suffix"], ".bin")

    def test_the_committed_fixture_census_matches_a_fresh_run(self):
        committed = (FIXTURE / horos.CENSUS_RELPATH).read_text(encoding="utf-8")
        fresh = horos.render(
            horos.census_document(horos.scan_tree(str(FIXTURE), census=True))
        )
        self.assertEqual(committed, fresh)

    def test_census_write_commits_the_artefact_atomically(self):
        write(self.root, "app.py", "x = 1\n")
        with mock.patch.object(sys, "stdout", new=io.StringIO()):
            code = horos.main(["scan", self.root, "--census", "--write"])
        self.assertEqual(code, 0)
        path = Path(self.root) / horos.CENSUS_RELPATH
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(document["schema"], horos.CENSUS_SCHEMA)
        self.assertEqual(list(path.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
