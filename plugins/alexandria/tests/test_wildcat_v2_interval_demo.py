"""The preserved Wildcat V2 mainnet interval: rebuilt from an external archive.

Unlike `usdc-interval-live-v0`, whose tiny staging tree ships inside this
repository, this interval's staging tree -- 3,463 shards, 124 files, over
200MB -- is preserved outside this repository and reached only through the
`ALEXANDRIA_WILDCAT_V2_STAGING` environment variable. A test that needs that
tree and does not find it must report exactly that reason and never silently
pass; `demo.py` refuses by name when the variable is unset, and the tests
here that need it do the same, loudly, via `skipTest` with the same reason,
never a bare skip and never a pass.

A separate group needs no staging tree at all: `staging-manifest.json` binds
the preserved archive's own byte count and SHA-256 to the byte count and
SHA-256 of every file inside it, and `rebuild-record.json` is what this
collecting host got when it actually rebuilt the release from that tree. Those
two files are checked into this repository, and the tests in
`PreservedArtefactsTests` fail -- they do not skip -- if either one is
missing, malformed, or disagrees with `expected.json` or with each other.
"""

import copy
import hashlib
import json
from pathlib import Path
import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
EXAMPLE = PLUGIN / "examples" / "wildcat-v2-interval-v0"
MODULE_NAME = "wildcat_v2_interval_demo"
STAGING_ENV_VAR = "ALEXANDRIA_WILDCAT_V2_STAGING"
REQUIRED = (
    "demo.py",
    "plan.json",
    "registry.json",
    "expected.json",
    "README.md",
    "staging-manifest.json",
    "rebuild-record.json",
)

sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import MAX_SHARDS, MAX_SHARD_WIDTH, validate_plan  # noqa: E402


def demo():
    """Import the demonstration, failing rather than skipping when it is absent.

    Every file this checks is meant to be committed to this repository (the
    preserved staging tree itself is the one exception, handled separately
    below); a missing one here is a defect in the example, not something to
    wave past.
    """
    missing = [name for name in REQUIRED if not (EXAMPLE / name).is_file()]
    if missing:
        raise AssertionError(
            f"the wildcat-v2-interval-v0 example is missing {', '.join(missing)} "
            f"at {EXAMPLE}; this suite is the proof it is complete and must fail "
            "rather than skip"
        )
    if MODULE_NAME in sys.modules:
        return sys.modules[MODULE_NAME]
    spec = importlib.util.spec_from_file_location(MODULE_NAME, EXAMPLE / "demo.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


class DemoTestCase(unittest.TestCase):
    def setUp(self):
        self.module = demo()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.expected = json.loads((EXAMPLE / "expected.json").read_text(encoding="utf-8"))
        self.manifest = json.loads((EXAMPLE / "staging-manifest.json").read_text(encoding="utf-8"))
        self.record = json.loads((EXAMPLE / "rebuild-record.json").read_text(encoding="utf-8"))


class PreservedArtefactsTests(DemoTestCase):
    """Needs no staging tree. Fails -- never skips -- on a bad manifest or record."""

    def test_verify_preserved_passes_against_the_committed_artefacts(self):
        result = self.module.verify_preserved()
        self.assertEqual(result["manifest"], self.manifest)
        self.assertEqual(result["record"], self.record)

    def test_committed_plan_fits_both_transport_and_collector_bounds(self):
        plan = json.loads((EXAMPLE / "plan.json").read_text())
        validate_plan(plan)
        self.assertLessEqual(plan["shard_width"], MAX_SHARD_WIDTH)
        self.assertLessEqual(len(plan["shards"]), MAX_SHARDS)
        self.assertTrue(all(shard["end"] - shard["start"] <= 29_999 for shard in plan["shards"]))
        self.assertGreaterEqual(int(plan["finality"]["block_number"]), int(plan["interval"]["end"]))
        self.assertEqual(len(plan["subjects"]), 137)

    def test_the_manifest_is_well_formed(self):
        self.assertEqual(self.manifest["format"], self.module.MANIFEST_FORMAT)
        archive = self.manifest["archive"]
        self.assertIn("sha256", archive)
        self.assertIn("bytes", archive)
        self.assertIsInstance(self.manifest["files"], list)
        self.assertEqual(len(self.manifest["files"]), 124)
        for entry in self.manifest["files"]:
            self.assertIn("path", entry)
            self.assertIn("bytes", entry)
            self.assertIn("sha256", entry)

    def test_the_manifest_file_sizes_sum_to_its_own_declared_total(self):
        total = sum(entry["bytes"] for entry in self.manifest["files"])
        self.assertEqual(total, self.manifest["staging_bytes_total"])
        self.assertEqual(len(self.manifest["files"]), self.manifest["staging_files_total"])

    def test_the_manifest_names_no_path_twice(self):
        paths = [entry["path"] for entry in self.manifest["files"]]
        self.assertEqual(len(paths), len(set(paths)))

    def test_the_rebuild_record_is_well_formed_and_binds_the_manifests_archive(self):
        self.assertEqual(self.record["format"], self.module.RECORD_FORMAT)
        for field in ("archive_sha256", "checked", "rebuilt_at", "rebuilt_by"):
            self.assertIn(field, self.record)
        self.assertEqual(self.record["archive_sha256"], self.manifest["archive"]["sha256"])

    def test_the_rebuild_record_agrees_with_the_pinned_expectation(self):
        checked = self.record["checked"]
        for field in ("epochs", "reconciliation", "release_id", "shard_statuses"):
            self.assertEqual(checked[field], self.expected[field], field)

    def test_a_missing_manifest_fails_not_skips(self):
        with mock.patch.object(self.module, "MANIFEST", self.root / "absent.json"):
            with self.assertRaisesRegex(AlexandriaError, "staging manifest is missing"):
                self.module.verify_preserved()

    def test_a_missing_rebuild_record_fails_not_skips(self):
        with mock.patch.object(self.module, "RECORD", self.root / "absent.json"):
            with self.assertRaisesRegex(AlexandriaError, "rebuild record is missing"):
                self.module.verify_preserved()

    def test_a_malformed_manifest_format_fails(self):
        broken = self.root / "manifest.json"
        broken.write_text(json.dumps(dict(self.manifest, format="unknown/v0")), encoding="utf-8")
        with mock.patch.object(self.module, "MANIFEST", broken):
            with self.assertRaisesRegex(AlexandriaError, "unknown format"):
                self.module.verify_preserved()

    def test_a_manifest_whose_file_sizes_do_not_sum_fails(self):
        tampered = copy.deepcopy(self.manifest)
        tampered["files"][0]["bytes"] += 1
        broken = self.root / "manifest.json"
        broken.write_text(json.dumps(tampered), encoding="utf-8")
        with mock.patch.object(self.module, "MANIFEST", broken):
            with self.assertRaisesRegex(AlexandriaError, "do not sum"):
                self.module.verify_preserved()

    def test_a_record_binding_a_different_archive_fails(self):
        tampered = dict(self.record, archive_sha256="0" * 64)
        broken = self.root / "record.json"
        broken.write_text(json.dumps(tampered), encoding="utf-8")
        with mock.patch.object(self.module, "RECORD", broken):
            with self.assertRaisesRegex(AlexandriaError, "different archive"):
                self.module.verify_preserved()

    def test_a_record_that_disagrees_with_expected_fails(self):
        tampered = copy.deepcopy(self.record)
        tampered["checked"]["epochs"] += 1
        broken = self.root / "record.json"
        broken.write_text(json.dumps(tampered), encoding="utf-8")
        with mock.patch.object(self.module, "RECORD", broken):
            with self.assertRaisesRegex(AlexandriaError, "epochs"):
                self.module.verify_preserved()

    def test_the_command_line_runs_verify_preserved(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "verify-preserved"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.expected["release_id"], result.stdout)

    def test_neither_this_group_nor_verify_preserved_opens_a_socket(self):
        with mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used")
        ):
            self.module.verify_preserved()

    def test_the_readme_never_names_the_external_repository_that_holds_the_archive(self):
        for path in sorted(p for p in EXAMPLE.iterdir() if p.is_file()):
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("secretsauce", text.lower(), path)

    def test_the_readme_documents_the_staging_environment_variable(self):
        readme = (EXAMPLE / "README.md").read_text(encoding="utf-8")
        self.assertIn(STAGING_ENV_VAR, readme)
        self.assertIn("preserved outside this repository", readme)


class StagingManifestGuardTests(DemoTestCase):
    """Check corrupt, missing and extra files before the builder consumes staging."""

    def setUp(self):
        super().setUp()
        self.staging = self.root / "staging"
        self.staging.mkdir()
        files = []
        for name, data in (("checkpoint.json", b"{}\n"), ("journal.jsonl", b"[]\n")):
            (self.staging / name).write_bytes(data)
            files.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        self.small_manifest = {
            "format": self.module.MANIFEST_FORMAT,
            "archive": {"bytes": 1, "sha256": "a" * 64},
            "files": files, "staging_files_total": 2, "staging_bytes_total": 6,
        }
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_text(json.dumps(self.small_manifest))

    def assert_refused_before_build(self, reason):
        with mock.patch.object(self.module, "MANIFEST", self.manifest_path), mock.patch.dict(
            os.environ, {STAGING_ENV_VAR: str(self.staging)}
        ), mock.patch.object(self.module, "Builder") as builder:
            with self.assertRaisesRegex(AlexandriaError, reason):
                self.module.build(self.root / "built")
            builder.assert_not_called()
        self.assertFalse((self.root / "built").exists())

    def test_one_changed_byte_refuses_before_build(self):
        (self.staging / "journal.jsonl").write_bytes(b"{}\n")
        self.assert_refused_before_build("journal.jsonl differs")

    def test_an_unlisted_file_refuses_before_build(self):
        (self.staging / "extra").write_bytes(b"extra")
        self.assert_refused_before_build("does not list")

    def test_a_missing_file_refuses_before_build(self):
        (self.staging / "journal.jsonl").unlink()
        self.assert_refused_before_build("lacks")

    def test_a_symlink_refuses_before_build(self):
        (self.staging / "journal.jsonl").unlink()
        (self.staging / "journal.jsonl").symlink_to(self.staging / "checkpoint.json")
        self.assert_refused_before_build("symlink")

    def test_a_matching_tree_checks_every_file(self):
        self.assertEqual(
            self.module.verify_staging_tree(self.staging, self.small_manifest),
            {"files": 2, "bytes": 6},
        )

    def test_malformed_manifest_fields_refuse(self):
        for field, value in (("sha256", "bad"), ("bytes", True), ("path", "./journal.jsonl")):
            with self.subTest(field=field):
                broken = copy.deepcopy(self.small_manifest)
                broken["files"][1][field] = value
                self.manifest_path.write_text(json.dumps(broken))
                self.assert_refused_before_build("manifest")


class StagedRebuildTests(DemoTestCase):
    """Needs the real preserved staging tree, unpacked locally.

    Every test here reports its absence by name through `skipTest`, which
    unittest renders as skipped -- distinct from a pass -- rather than a
    silent omission or a green result with nothing behind it.
    """

    def setUp(self):
        super().setUp()
        value = os.environ.get(STAGING_ENV_VAR)
        if not value or not (Path(value) / "checkpoint.json").is_file():
            self.skipTest(
                f"not run: {STAGING_ENV_VAR} is not set to an unpacked preserved "
                "staging tree"
            )

    def test_the_rebuild_reproduces_the_pinned_identifier(self):
        output = self.root / "built"
        summary = self.module.build(output)
        self.assertEqual(summary["release_id"], self.expected["release_id"])
        self.assertEqual(summary["epochs"], self.expected["epochs"])
        self.assertEqual(summary["reconciliation"], self.expected["reconciliation"])
        self.assertEqual(summary["shard_statuses"], self.expected["shard_statuses"])

    def test_verify_compares_every_pinned_identity_and_the_cli_agrees(self):
        output = self.root / "built"
        self.module.build(output)
        derived = self.module.verify(output)
        for field in self.module.COMPARED:
            self.assertEqual(derived[field], self.expected[field], field)

        cli_output = self.root / "cli"
        built = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "build", "--output", str(cli_output)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(built.returncode, 0, built.stderr)
        self.assertIn(self.expected["release_id"], built.stdout)
        verified = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "verify", str(cli_output)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)


class MissingStagingEnvironmentVariableTests(DemoTestCase):
    """`build` refuses by name; it never silently proceeds without the tree."""

    def test_an_unset_variable_refuses_by_name(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(STAGING_ENV_VAR, None)
            with self.assertRaisesRegex(AlexandriaError, STAGING_ENV_VAR):
                self.module.build(self.root / "unstaged")
        self.assertFalse((self.root / "unstaged").exists())

    def test_a_variable_naming_a_tree_with_no_checkpoint_refuses_by_name(self):
        empty = self.root / "not-a-staging-tree"
        empty.mkdir()
        with mock.patch.dict(os.environ, {STAGING_ENV_VAR: str(empty)}):
            with self.assertRaisesRegex(AlexandriaError, "no checkpoint.json"):
                self.module.build(self.root / "unstaged")

    def test_the_command_line_reports_a_controlled_usage_error(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
