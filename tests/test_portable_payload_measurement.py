"""Tests for the standing `measure` action and its headroom refusal wording.

`measure` and `package`/`check` read one code path (`_package_bytes`, which
calls `expected_files`), so these tests build a real package once and compare
it to `measure --json`'s figures rather than asserting fixed numbers.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "portable_promise_machine.py"
SCHEMA = "portable-payload-measurement/v1"


def load_generator():
    spec = importlib.util.spec_from_file_location("portable_measurement_test", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(*argv, cwd=None):
    return subprocess.run(  # phylax: allow subprocess: fixed local generator argv
        [sys.executable, str(GENERATOR), *argv],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )


class MeasureAgreesWithPackageTests(unittest.TestCase):
    """The measurement is a walk of the same tree `package --out` writes."""

    @classmethod
    def setUpClass(cls):
        cls.module = load_generator()
        cls.commit = cls.module.source_commit(ROOT)
        cls.measurement = cls.module.measure_tree(ROOT, 25)
        cls.tmp = tempfile.TemporaryDirectory(prefix="measure-agrees.")
        cls.out = Path(cls.tmp.name) / "package"
        cls.module.package(ROOT, str(cls.out), cls.commit)
        cls.walked = [p for p in cls.out.rglob("*") if p.is_file()]
        cls.runtime = cls.out / cls.module.PACKAGE_ROOT / "runtime"
        cls.manifest = json.loads((cls.runtime / "MANIFEST.json").read_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_package_figures_equal_a_walk_of_package_out(self):
        total_bytes = sum(p.stat().st_size for p in self.walked)
        self.assertEqual(self.measurement["package"]["bytes"], total_bytes)
        self.assertEqual(self.measurement["package"]["files"], len(self.walked))

    def test_runtime_figures_equal_the_manifest(self):
        self.assertEqual(self.measurement["runtime"]["bytes"], self.manifest["total_bytes"])
        self.assertEqual(self.measurement["runtime"]["files"], self.manifest["file_count"])
        manifest_path = self.runtime / "MANIFEST.json"
        self.assertEqual(self.measurement["manifest_bytes"], manifest_path.stat().st_size)

    def test_line_equals_cap_minus_reserve_and_margins_equal_line_minus_bytes(self):
        m = self.measurement
        self.assertEqual(m["line"], m["cap"] - m["reserve"])
        self.assertEqual(m["package"]["margin"], m["line"] - m["package"]["bytes"])
        self.assertEqual(m["runtime"]["margin"], m["line"] - m["runtime"]["bytes"])

    def test_exact_schema_and_key_set(self):
        m = self.measurement
        self.assertEqual(m["schema"], SCHEMA)
        self.assertEqual(set(m), {
            "schema", "source_commit", "tree_clean", "cap", "reserve", "line",
            "file_tripwire", "package", "runtime", "manifest_bytes",
            "outer_bytes", "omission_classes", "largest_default_included",
            "kept_by_link",
        })
        self.assertEqual(set(m["package"]), {"bytes", "files", "margin"})
        self.assertEqual(set(m["runtime"]), {"bytes", "files", "margin"})
        for row in m["largest_default_included"]:
            self.assertEqual(set(row), {"path", "bytes"})
        self.assertTrue(m["kept_by_link"])
        for row in m["kept_by_link"]:
            self.assertEqual(set(row), {"path", "bytes"})
        self.assertEqual(
            [row["path"] for row in m["kept_by_link"]],
            sorted(row["path"] for row in m["kept_by_link"]),
        )
        self.assertEqual(m["kept_by_link"], self.manifest["kept_by_link"])

    def test_file_tripwire_matches_the_module_constant(self):
        self.assertEqual(self.measurement["file_tripwire"], self.module.FILE_TRIPWIRE)


class MeasureCliTests(unittest.TestCase):
    def test_text_form_has_five_parts_and_respects_the_top_bound(self):
        result = run_cli("measure", "--top", "2")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = result.stdout
        for keyword in ("bytes", "line", "margin", "files", "tripwire"):
            self.assertIn(keyword, text)
        path_rows = [line for line in text.splitlines() if line.strip()[:1].isdigit()]
        self.assertLessEqual(len(path_rows), 2)

    def test_top_zero_lists_no_default_included_paths(self):
        result = run_cli("measure", "--json", "--top", "0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["largest_default_included"], [])

    def test_require_margin_met_exits_zero(self):
        result = run_cli("measure", "--require-margin", "1000")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_require_margin_unmet_exits_one_and_names_the_margin(self):
        result = run_cli("measure", "--require-margin", "999999999999")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        output = result.stdout + result.stderr
        self.assertIn("999999999999", output)
        self.assertIn("margin", output)

    def test_bad_top_value_exits_two(self):
        for bad in ("-1", "abc"):
            with self.subTest(value=bad):
                result = run_cli("measure", "--top", bad)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_bad_require_margin_value_exits_two(self):
        for bad in ("-1", "abc"):
            with self.subTest(value=bad):
                result = run_cli("measure", "--require-margin", bad)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_non_git_checkout_exits_one(self):
        with tempfile.TemporaryDirectory() as raw:
            result = run_cli("measure", "--root", raw, cwd=Path(raw))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_working_tree_status_is_unchanged_by_measure(self):
        def status():
            return subprocess.run(  # phylax: allow subprocess: fixed local git argv
                ["git", "-C", str(ROOT), "status", "--porcelain"],
                capture_output=True, text=True, check=True,
            ).stdout
        before = status()
        result = run_cli("measure", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = status()
        self.assertEqual(before, after)


class OverLineMeasurementTests(unittest.TestCase):
    """A tree over the line is measured, not refused; `package` still refuses.

    Each test here stands up an over-the-line tree the same cheap way
    tests/test_skills_sh_package.py's headroom test does: `expected_files` is
    mocked to return one oversized in-memory payload, one byte past the line,
    rather than materialising a real ~20 MiB tree.
    """

    def setUp(self):
        self.module = load_generator()
        self.line = self.module.MAX_RUNTIME_BYTES - self.module.MIN_BYTE_HEADROOM
        self.oversized_payload = {"probe.txt": b"x" * (self.line + 1)}
        self.commit = self.module.source_commit(ROOT)

    def test_measure_exits_clean_with_a_negative_margin_over_the_line(self):
        with mock.patch.object(
            self.module, "expected_files",
            return_value=(self.oversized_payload, b'{"kept_by_link": []}\n'),
        ):
            measurement = self.module.measure_tree(ROOT, 5)
        self.assertLess(measurement["package"]["margin"], 0)
        self.assertLess(measurement["runtime"]["margin"], 0)
        self.assertEqual(measurement["kept_by_link"], [])

    def test_package_still_refuses_naming_bytes_line_margin_and_measure(self):
        with mock.patch.object(
            self.module, "expected_files", return_value=(self.oversized_payload, b"{}\n"),
        ):
            with tempfile.TemporaryDirectory() as raw:
                out = Path(raw) / "package"
                with self.assertRaises(self.module.PackageError) as caught:
                    self.module.package(ROOT, str(out), self.commit)
        message = str(caught.exception)
        self.assertIn(str(self.line), message)
        self.assertRegex(message, r"\d+ bytes")
        self.assertIn("margin", message)
        self.assertIn("measure", message)


class HeadroomBoundaryTests(unittest.TestCase):
    def test_boundary_byte_passes_and_the_first_byte_past_refuses(self):
        module = load_generator()
        line = module.MAX_RUNTIME_BYTES - module.MIN_BYTE_HEADROOM
        module.require_byte_headroom(line)
        with self.assertRaises(module.PackageError):
            module.require_byte_headroom(line + 1)


class LinkKeptSafetyTests(unittest.TestCase):
    """The link-kept exception is validated the same way every other selected
    file is: a missing or symlinked target refuses generation instead of
    being silently skipped, and a target that would escape the tree is never
    even recognised as an example-class link in the first place (study
    section 9; docs/decisions/drafts/omit-example-payloads-from-the-portable-runtime.md).
    """

    def setUp(self):
        self.module = load_generator()
        self.scratch = ROOT / "plugins/lazarus/examples/_zzz_link_kept_probe.md"
        self.addCleanup(lambda: self.scratch.unlink(missing_ok=True))

    def _tracked_with(self, *extra):
        real = self.module._tracked_plugin_files(ROOT)
        return real + [self.scratch.relative_to(ROOT), *extra]

    def test_missing_link_kept_target_refuses_generation(self):
        self.scratch.write_text(
            "[probe](./_zzz-link-kept-probe-missing.json)\n", encoding="utf-8",
        )
        tracked = self._tracked_with()
        with mock.patch.object(self.module, "_tracked_plugin_files", return_value=tracked):
            with self.assertRaises(self.module.PackageError) as caught:
                self.module._source_candidates(ROOT)
        message = str(caught.exception)
        self.assertIn("absent or not a regular file", message)
        self.assertIn("_zzz-link-kept-probe-missing.json", message)

    def test_symlinked_link_kept_target_refuses_generation(self):
        target = ROOT / "plugins/lazarus/examples/_zzz_link_kept_probe_target.json"
        link = ROOT / "plugins/lazarus/examples/_zzz_link_kept_probe_link.json"
        target.write_text("{}", encoding="utf-8")
        link.symlink_to(target)
        self.addCleanup(lambda: link.unlink(missing_ok=True))
        self.addCleanup(lambda: target.unlink(missing_ok=True))
        self.scratch.write_text(
            "[probe](./_zzz_link_kept_probe_link.json)\n", encoding="utf-8",
        )
        # Neither the symlink nor its target is added to `tracked`: the only
        # route by which either could reach `_source_candidates`'s selection
        # is the link itself, so a refusal here is proof the scan found it.
        tracked = self._tracked_with()
        with mock.patch.object(self.module, "_tracked_plugin_files", return_value=tracked):
            with self.assertRaises(self.module.PackageError) as caught:
                self.module._source_candidates(ROOT)
        message = str(caught.exception)
        self.assertIn("absent or not a regular file", message)
        self.assertIn("_zzz_link_kept_probe_link.json", message)

    def test_intermediate_symlinked_directory_target_refuses_generation(self):
        """A tracked git path can never sit under a symlinked directory --
        git records a symlink as one blob, never a tree with children -- but
        the link scan reads the live filesystem, so `examples/` itself being
        a symlink to an external directory would let an ordinary link name a
        file the leaf-only `is_symlink` check never inspects. `_source_candidates`
        must still refuse it as a target that resolves outside the checkout.
        """
        outside_dir = tempfile.TemporaryDirectory()
        self.addCleanup(outside_dir.cleanup)
        leak = Path(outside_dir.name) / "_zzz_leak.json"
        leak.write_text("{}", encoding="utf-8")
        symlinked_examples = ROOT / "plugins/lazarus/examples/_zzz_symlinked_dir"
        symlinked_examples.symlink_to(Path(outside_dir.name), target_is_directory=True)
        self.addCleanup(lambda: symlinked_examples.unlink(missing_ok=True))
        self.scratch.write_text(
            "[probe](./_zzz_symlinked_dir/_zzz_leak.json)\n", encoding="utf-8",
        )
        tracked = self._tracked_with()
        with mock.patch.object(self.module, "_tracked_plugin_files", return_value=tracked):
            with self.assertRaises(self.module.PackageError) as caught:
                self.module._source_candidates(ROOT)
        message = str(caught.exception)
        self.assertIn("resolves outside the checkout", message)
        self.assertIn("_zzz_leak.json", message)

    def test_oversized_packaged_markdown_refuses_generation(self):
        """The per-file read is capped, not just the regex's own match groups.

        `MARKDOWN_LINK_SCAN_MAX_BYTES` bounds bytes read before they ever
        reach the regex; confirm a file one byte over that cap refuses
        outright instead of being scanned with no ceiling.
        """
        module = load_generator()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            document = Path("plugins/x/examples/DOC.md")
            (root / document).parent.mkdir(parents=True)
            oversized = b"a" * (module.MARKDOWN_LINK_SCAN_MAX_BYTES + 1)
            (root / document).write_bytes(oversized)
            with self.assertRaises(module.PackageError) as caught:
                module._link_kept_examples(root, {document})
        message = str(caught.exception)
        self.assertIn(str(module.MARKDOWN_LINK_SCAN_MAX_BYTES), message)
        self.assertIn("DOC.md", message)

    def test_file_at_exactly_the_cap_is_still_scanned(self):
        """The boundary byte itself must not be refused -- only the first byte past it."""
        module = load_generator()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            document = Path("plugins/x/examples/DOC.md")
            (root / document).parent.mkdir(parents=True)
            link = "[ok](target.json)"
            padding = b"a" * (module.MARKDOWN_LINK_SCAN_MAX_BYTES - len(link))
            (root / document).write_bytes(padding + link.encode("ascii"))
            self.assertEqual(
                (root / document).stat().st_size, module.MARKDOWN_LINK_SCAN_MAX_BYTES,
            )
            found = module._link_kept_examples(root, {document})
        self.assertEqual(found, {Path("plugins/x/examples/target.json")})

    def test_link_targets_that_escape_the_tree_are_never_treated_as_example_links(self):
        module = load_generator()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            document = Path("plugins/x/examples/deep/nested/DOC.md")
            (root / document).parent.mkdir(parents=True)
            (root / document).write_text(
                "[escape](../../../../../../../../etc/passwd)\n"
                "[also-escapes](../../../../../../outside.json)\n",
                encoding="utf-8",
            )
            found = module._link_kept_examples(root, {document})
        self.assertEqual(found, set())


if __name__ == "__main__":
    unittest.main()
