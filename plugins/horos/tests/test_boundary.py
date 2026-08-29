"""The boundary artefact is deterministic, atomic, and drift names every path."""

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


def write(root, relpath, content):
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        content = content.encode("utf-8")
    path.write_bytes(content)
    return path


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        write(self.root, "yarn.lock", "lock\n")
        write(self.root, "src/app.py", "x = 1\n")

    def document(self):
        return horos.boundary_document(horos.scan_tree(self.root))

    def check(self):
        out = io.StringIO()
        code = horos.check_tree(self.root, out=out)
        return code, out.getvalue()

    def test_two_scans_render_byte_identical_documents(self):
        self.assertEqual(horos.render(self.document()), horos.render(self.document()))

    def test_the_document_carries_no_absolute_paths(self):
        self.assertNotIn(self.root, horos.render(self.document()))

    def test_write_creates_the_boundary_and_leaves_no_temporary(self):
        horos.write_boundary(self.root, self.document())
        boundary = Path(self.root) / horos.BOUNDARY_RELPATH
        self.assertEqual(boundary.read_text(encoding="utf-8"), horos.render(self.document()))
        self.assertEqual(list(boundary.parent.glob("*.tmp")), [])

    def test_a_failed_replace_leaves_the_old_boundary_intact(self):
        horos.write_boundary(self.root, self.document())
        before = (Path(self.root) / horos.BOUNDARY_RELPATH).read_text(encoding="utf-8")
        with mock.patch.object(horos.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                horos.write_boundary(self.root, {"schema": 1, "entries": [], "counts": {}})
        after = (Path(self.root) / horos.BOUNDARY_RELPATH).read_text(encoding="utf-8")
        self.assertEqual(before, after)
        boundary = Path(self.root) / horos.BOUNDARY_RELPATH
        self.assertEqual(list(boundary.parent.glob("*.tmp")), [])

    def test_check_passes_on_a_fresh_boundary(self):
        horos.write_boundary(self.root, self.document())
        code, output = self.check()
        self.assertEqual(code, 0)
        self.assertIn("matches", output)

    def test_a_new_sink_drifts_and_is_named(self):
        horos.write_boundary(self.root, self.document())
        write(self.root, "data.wasm", b"\x00asm\x01\x00\x00\x00")
        code, output = self.check()
        self.assertEqual(code, 1)
        self.assertIn("drift: data.wasm: evidenced by the tree", output)

    def test_candidate_classification_drift_at_the_same_file_count_is_advisory(self):
        write(self.root, "notes.svg", "hand-written notes\n")
        horos.write_boundary(self.root, self.document())
        horos.write_candidates(
            self.root, horos.candidates_document(horos.scan_tree(self.root))
        )
        write(self.root, "notes.svg", '<svg xmlns="x"></svg>')
        code, output = self.check()
        self.assertEqual(code, 0)
        self.assertIn("candidate drift: notes.svg", output)

    def test_a_removed_sink_drifts_and_is_named(self):
        horos.write_boundary(self.root, self.document())
        os.unlink(os.path.join(self.root, "yarn.lock"))
        code, output = self.check()
        self.assertEqual(code, 1)
        self.assertIn("drift: yarn.lock: in the boundary", output)

    def test_a_poisoned_entry_fails_the_check_by_name(self):
        document = self.document()
        document["entries"].append(
            {
                "path": "src/app.py",
                "category": "generated",
                "bytes": 6,
                "evidence": "forged",
            }
        )
        horos.write_boundary(self.root, document)
        code, output = self.check()
        self.assertEqual(code, 1)
        self.assertIn("drift: src/app.py: in the boundary but no longer evidenced", output)

    def test_a_changed_entry_drifts_and_is_named(self):
        horos.write_boundary(self.root, self.document())
        write(self.root, "yarn.lock", "lock grew longer\n")
        code, output = self.check()
        self.assertEqual(code, 1)
        self.assertIn("drift: yarn.lock: entry changed", output)

    def test_count_only_drift_fails_the_check(self):
        document = self.document()
        document["counts"]["files_walked"] += 1
        horos.write_boundary(self.root, document)
        code, output = self.check()
        self.assertEqual(code, 1)
        self.assertIn("drift: .horos/boundary.json#counts", output)

    def test_a_missing_boundary_is_a_distinct_failure(self):
        code, output = self.check()
        self.assertEqual(code, 2)
        self.assertIn("no boundary", output)

    def test_an_unparseable_boundary_is_a_distinct_failure(self):
        write(self.root, horos.BOUNDARY_RELPATH, "{not json")
        code, output = self.check()
        self.assertEqual(code, 2)
        self.assertIn("unreadable boundary", output)

    def test_the_boundary_file_never_classifies_itself(self):
        horos.write_boundary(self.root, self.document())
        code, _ = self.check()
        self.assertEqual(code, 0)
        paths = [entry["path"] for entry in self.document()["entries"]]
        self.assertNotIn(horos.BOUNDARY_RELPATH, paths)

    def test_a_write_prints_the_adoption_stanza(self):
        with mock.patch.object(sys, "stdout", new=io.StringIO()) as stdout:
            code = horos.main(["scan", self.root, "--write"])
        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("## Reading boundary", output)
        self.assertIn("never\napplies during security review", output)
        self.assertIn("AGENTS.md or CLAUDE.md", output)

    def test_json_output_stays_pure_even_with_write(self):
        with mock.patch.object(sys, "stdout", new=io.StringIO()) as stdout:
            code = horos.main(["scan", self.root, "--json", "--write"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), horos.render(self.document()))

    def test_the_cli_json_output_is_the_rendered_document(self):
        with mock.patch.object(sys, "stdout", new=io.StringIO()) as stdout:
            code = horos.main(["scan", self.root, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), horos.render(self.document()))
        parsed = json.loads(stdout.getvalue())
        self.assertEqual(parsed["schema"], horos.BOUNDARY_SCHEMA)


if __name__ == "__main__":
    unittest.main()
