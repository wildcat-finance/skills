"""Native directory checkpoints preserve the same signed run as ZIP carriers."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock

from test_hexctl_checkpoint_archive import HEXCTL, SignedRunFixture, hexctl_module


class CheckpointDirectoryTests(SignedRunFixture):
    def directory_archive(self):
        self.to_post_push()
        result = self.run_ctl("checkpoint", "archive", "--format", "directory")
        payload = json.loads(result.stdout)
        return Path(payload["archive"]), payload

    def test_directory_checkpoint_round_trip_without_source(self):
        archive, exported = self.directory_archive()
        self.assertTrue(archive.is_dir())
        manifest_bytes = (archive / "checkpoint.json").read_bytes()
        self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(), exported["outer_sha256"])
        manifest = json.loads(manifest_bytes)
        self.assertEqual(manifest["archive"]["format"], "directory")
        self.assertGreater(manifest["limits"]["bundle_bytes"], 70_000_000_000)
        before = self.controller_bytes()
        checked = self.run_ctl("checkpoint", "inspect", "--archive", str(archive),
                               "--sha256", exported["outer_sha256"])
        self.assertEqual(json.loads(checked.stdout)["findings"], [])
        self.assertEqual(before, self.controller_bytes())
        with tempfile.TemporaryDirectory() as temporary:
            independent = Path(temporary) / "checkpoint.directory"
            shutil.copytree(archive, independent)
            hidden = self.dir + "-hidden"
            os.rename(self.dir, hidden)
            try:
                destination = Path(temporary) / "restored-directory"
                result = subprocess.run([
                    sys.executable, HEXCTL, "--dir", str(destination), "checkpoint", "restore",
                    "--archive", str(independent), "--sha256", exported["outer_sha256"],
                ], capture_output=True, text=True, timeout=120, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                restored = json.loads(result.stdout)
                self.assertEqual(restored["snapshot_id"], exported["snapshot_id"])
                self.assertEqual(restored["next"], exported["next"])
            finally:
                os.rename(hidden, self.dir)

    def test_directory_checkpoint_rejects_changed_member(self):
        archive, exported = self.directory_archive()
        with (archive / "git/repository.bundle").open("ab") as handle:
            handle.write(b"changed")
        result = self.run_ctl("checkpoint", "inspect", "--archive", str(archive),
                              "--sha256", exported["outer_sha256"], expect=1)
        self.assertIn("manifest-mismatch", result.stderr)

    def test_directory_checkpoint_rejects_symlink_and_extra_member(self):
        archive, exported = self.directory_archive()
        (archive / "extra").write_bytes(b"not listed")
        result = self.run_ctl("checkpoint", "inspect", "--archive", str(archive),
                              "--sha256", exported["outer_sha256"], expect=1)
        self.assertIn("manifest-mismatch", result.stderr)
        (archive / "extra").unlink()
        member = archive / "README.txt"
        elsewhere = Path(self.dir) / "outside-readme"
        shutil.move(member, elsewhere)
        os.symlink(elsewhere, member)
        result = self.run_ctl("checkpoint", "inspect", "--archive", str(archive),
                              "--sha256", exported["outer_sha256"], expect=1)
        self.assertIn("entry-mode", result.stderr)

    def test_directory_checkpoint_rejects_digest_schema_and_hardlink_changes(self):
        archive, exported = self.directory_archive()
        original = (archive / "checkpoint.json").read_bytes()
        result = self.run_ctl("checkpoint", "inspect", "--archive", str(archive),
                              "--sha256", "0" * 64, expect=1)
        self.assertIn("outer-digest-mismatch", result.stderr)
        changed = json.loads(original)
        changed["unrecognised"] = True
        candidate = json.dumps(changed, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        (archive / "checkpoint.json").write_bytes(candidate)
        result = self.run_ctl("checkpoint", "inspect", "--archive", str(archive),
                              "--sha256", hashlib.sha256(candidate).hexdigest(), expect=1)
        self.assertIn("schema-unsupported", result.stderr)
        (archive / "checkpoint.json").write_bytes(original)
        os.link(archive / "README.txt", Path(self.dir) / "linked-readme")
        result = self.run_ctl("checkpoint", "inspect", "--archive", str(archive),
                              "--sha256", exported["outer_sha256"], expect=1)
        self.assertIn("entry-mode", result.stderr)

    def test_directory_checkpoint_rebuild_has_identical_manifest_and_bundle(self):
        archive, first = self.directory_archive()
        manifest = (archive / "checkpoint.json").read_bytes()
        shutil.rmtree(self.store_root())
        result = self.run_ctl("checkpoint", "archive", "--format", "directory")
        second = json.loads(result.stdout)
        self.assertEqual(first["outer_sha256"], second["outer_sha256"])
        self.assertEqual(first["bundle_sha256"], second["bundle_sha256"])
        self.assertEqual(manifest, (Path(second["archive"]) / "checkpoint.json").read_bytes())


class DirectoryCaptureTests(unittest.TestCase):
    def setUp(self):
        self.h = hexctl_module()
        self.carrier = self.h._checkpoint_directory_module()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.write_bytes(b"preserved bytes" * 10000)
        self.fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, self.fd)

    def test_clone_and_stream_captures_are_independent_of_later_source_writes(self):
        original = self.source.read_bytes()
        for fallback in (False, True):
            with self.subTest(fallback=fallback):
                self.source.write_bytes(original)
                target = self.root / ("stream" if fallback else "clone")
                context = mock.patch.object(self.carrier, "clone_file", return_value=False)
                with context if fallback else mock.patch.object(self.carrier, "IO_CHUNK", 4096):
                    size, digest, _ = self.carrier.capture(self.h, self.fd, "source", str(target),
                                                         len(original), float("inf"), clone=True)
                self.source.write_bytes(b"changed")
                self.assertEqual(target.read_bytes(), original)
                self.assertEqual(size, len(original))
                self.assertEqual(digest, hashlib.sha256(original).hexdigest())
                self.assertNotEqual(target.stat().st_ino, self.source.stat().st_ino)

    def test_capture_refuses_byte_excess_and_observed_source_mutation(self):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            self.carrier.capture(self.h, self.fd, "source", str(self.root / "over"), 1, float("inf"))
        actual_read = os.read
        changed = False

        def changing_read(descriptor, size):
            nonlocal changed
            data = actual_read(descriptor, size)
            if data and not changed:
                changed = True
                with self.source.open("ab") as handle:
                    handle.write(b"mutation")
            return data

        with mock.patch.object(self.carrier.os, "read", changing_read):
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                self.carrier.capture(self.h, self.fd, "source", str(self.root / "mutated"),
                                     1000000, float("inf"))


if __name__ == "__main__":
    unittest.main()
