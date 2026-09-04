"""The build command exercised against focused and real source files."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from . import support
from tabularium_lib import builder as builder_module


COMMAND = support.PLUGIN_ROOT / "scripts" / "tabularium.py"
FIXTURE = support.FIXTURES / "minimal-snapshot.json"
CAPTURE_FIXTURE = support.FIXTURES / "minimal-capture-manifest.json"


def run(*args):
    return subprocess.run(
        [sys.executable, str(COMMAND), *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


def release_paths(directory):
    root = Path(directory)
    source = root / "source.json"
    capture = root / "capture.json"
    output = root / "events.jsonl"
    manifest = root / "coverage.json"
    source.write_bytes(FIXTURE.read_bytes())
    capture.write_bytes(CAPTURE_FIXTURE.read_bytes())
    return source, capture, output, manifest


def build_args(source, capture, output, manifest, release="fixture-v1"):
    return (
        "build", "--source", source, "--capture-manifest", capture,
        "--out", output, "--manifest", manifest, "--release", release,
    )


class BuilderCliTests(unittest.TestCase):
    def test_euler_adapter_selection_builds_schema_v2(self):
        release = support.PLUGIN_ROOT / "examples" / "euler-v1-v0"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            capture = root / "capture.json"
            output = root / "events.jsonl"
            manifest = root / "coverage.json"
            source.write_bytes((release / "source.json").read_bytes())
            capture.write_bytes((release / "capture.json").read_bytes())
            result = run(
                "build", "--adapter", "euler-v1",
                "--source", source, "--capture-manifest", capture,
                "--out", output, "--manifest", manifest,
                "--release", "euler-v1-borrow-block-14531589-v0",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(manifest.read_text())["schema_version"], 2)

    def test_wrong_euler_adapter_fails_before_outputs(self):
        release = support.PLUGIN_ROOT / "examples" / "euler-v1-v0"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            capture = root / "capture.json"
            output = root / "events.jsonl"
            manifest = root / "coverage.json"
            source.write_bytes((release / "source.json").read_bytes())
            capture.write_bytes((release / "capture.json").read_bytes())
            result = run(
                "build", "--adapter", "euler-v2",
                "--source", source, "--capture-manifest", capture,
                "--out", output, "--manifest", manifest,
                "--release", "wrong-adapter",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("capture adapter", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())

    def test_build_writes_sorted_canonical_jsonl_and_reports_unmapped_kinds(self):
        with tempfile.TemporaryDirectory() as directory:
            source, capture, output, manifest = release_paths(directory)
            result = run(*build_args(source, capture, output, manifest))
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual([row["event_family"] for row in rows], ["borrowing", "repayment"])
            self.assertIn("built 2 event(s)", result.stderr)
            self.assertIn("borrowing=1, repayment=1", result.stderr)
            self.assertIn("coverage manifest sha256", result.stderr)
            self.assertTrue(output.read_bytes().endswith(b"\n"))
            self.assertTrue(manifest.read_bytes().endswith(b"\n"))

    def test_same_release_layout_in_separate_directories_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            first_root = Path(directory) / "first"
            second_root = Path(directory) / "second"
            first_root.mkdir()
            second_root.mkdir()
            first = release_paths(first_root)
            second = release_paths(second_root)
            self.assertEqual(run(*build_args(*first)).returncode, 0)
            self.assertEqual(run(*build_args(*second)).returncode, 0)
            self.assertEqual(first[2].read_bytes(), second[2].read_bytes())
            self.assertEqual(first[3].read_bytes(), second[3].read_bytes())

    def test_bad_source_exits_two_without_an_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            output = Path(directory) / "events.jsonl"
            capture = Path(directory) / "capture.json"
            manifest = Path(directory) / "coverage.json"
            source.write_text('{"_meta": {}, "useractivities": []}')
            capture.write_bytes(CAPTURE_FIXTURE.read_bytes())
            result = run(*build_args(source, capture, output, manifest))
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())
            self.assertIn("source digest", result.stderr)

    def test_capture_byte_count_is_checked_before_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source, capture, output, manifest = release_paths(directory)
            claim = json.loads(capture.read_text())
            claim["source"]["bytes"] += 1
            capture.write_text(json.dumps(claim))
            result = run(*build_args(source, capture, output, manifest))
            self.assertEqual(result.returncode, 2)
            self.assertIn("byte count", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())

    def test_capture_window_is_checked_before_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source, capture, output, manifest = release_paths(directory)
            claim = json.loads(capture.read_text())
            claim["scope"]["to_block"] = 111
            claim["request"]["query"]["where"] = "block_gte:100,block_lte:111"
            capture.write_text(json.dumps(claim))
            result = run(*build_args(source, capture, output, manifest))
            self.assertEqual(result.returncode, 2)
            self.assertIn("window does not match", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())

    def test_output_cannot_be_the_source_path(self):
        with tempfile.TemporaryDirectory() as directory:
            source, capture, _, manifest = release_paths(directory)
            source.write_bytes(FIXTURE.read_bytes())
            before = source.read_bytes()
            result = run(*build_args(source, capture, source, manifest))
            self.assertEqual(result.returncode, 2)
            self.assertIn("aliases preserved input", result.stderr)
            self.assertEqual(source.read_bytes(), before)

    def test_output_symlink_is_refused_without_following_it(self):
        with tempfile.TemporaryDirectory() as directory:
            source, capture, _, manifest = release_paths(directory)
            output = Path(directory) / "events.jsonl"
            before = source.read_bytes()
            output.symlink_to(source)
            result = run(*build_args(source, capture, output, manifest))
            self.assertEqual(result.returncode, 2)
            self.assertIn("output path is a symlink", result.stderr)
            self.assertTrue(output.is_symlink())
            self.assertEqual(source.read_bytes(), before)

    def test_output_hardlink_to_source_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            source, capture, _, manifest = release_paths(directory)
            output = Path(directory) / "events.jsonl"
            before = source.read_bytes()
            os.link(source, output)
            result = run(*build_args(source, capture, output, manifest))
            self.assertEqual(result.returncode, 2)
            self.assertIn("aliases preserved input", result.stderr)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(output.read_bytes(), before)

    def test_a_symlink_swapped_in_after_the_alias_check_cannot_rewrite_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source, capture, _, manifest = release_paths(directory)
            output = Path(directory) / "events.jsonl"
            before = source.read_bytes()
            from tabularium_lib.adapters import aave_v4

            original_map = aave_v4.map_source

            def swap_after_check(snapshot, capture_manifest):
                mapped = original_map(snapshot, capture_manifest)
                output.symlink_to(source)
                return mapped

            with mock.patch.object(
                aave_v4, "map_source", side_effect=swap_after_check
            ):
                report = builder_module.build(
                    source, capture, output, manifest, "fixture-v1"
                )

            self.assertEqual(report.rows, 2)
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(output.is_symlink())
            self.assertNotEqual(output.read_bytes(), before)

    def test_verify_accepts_a_locally_built_release(self):
        with tempfile.TemporaryDirectory() as directory:
            source, capture, output, manifest = release_paths(directory)
            self.assertEqual(run(*build_args(source, capture, output, manifest)).returncode, 0)
            result = run("verify", manifest)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("verified fixture-v1 offline", result.stdout)
