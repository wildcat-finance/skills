"""Native checkpoint verification retains both SSH and OpenPGP support."""

import hashlib
from contextlib import redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from fixture_tools import native_signing_tools
from test_hexctl_checkpoint_archive import (
    HEXCTL, ORIGIN_URL, HexctlCase, SignedRunFixture, hexctl_module,
)


class SshSignedRunFixture(SignedRunFixture):
    @classmethod
    def setUpClass(cls):
        context = native_signing_tools(("ssh-keygen",))
        try:
            cls.tool_paths = context.__enter__()
        except FileNotFoundError as error:
            raise unittest.SkipTest(str(error)) from error
        cls.addClassCleanup(context.__exit__, None, None, None)
        cls.key_root = tempfile.mkdtemp(prefix="fiat-ssh-")
        cls.addClassCleanup(shutil.rmtree, cls.key_root, ignore_errors=True)
        cls.signing_key = str(Path(cls.key_root) / "signer")
        subprocess.run(
            [cls.tool_paths["ssh-keygen"], "-q", "-t", "ed25519", "-N", "",
             "-f", cls.signing_key],
            check=True, capture_output=True, timeout=30,
        )
        result = subprocess.run(
            [cls.tool_paths["ssh-keygen"], "-lf", cls.signing_key + ".pub", "-E", "sha256"],
            check=True, capture_output=True, text=True, timeout=10,
        )
        cls.fingerprint = result.stdout.split()[1]

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        HexctlCase.setUp(self)
        self.git("remote", "add", "origin", ORIGIN_URL)
        self.git("config", "gpg.format", "ssh")
        self.git("config", "user.signingkey", self.signing_key)
        self.git("config", "gpg.ssh.program", self.tool_paths["ssh-keygen"])
        # The normal operator setup keeps public trust material outside Git.
        self.allowed_signers = Path(self.dir) / "allowed-signers"
        self.allowed_signers.write_text(
            "fixture@example.invalid " + Path(self.signing_key + ".pub").read_text(),
            encoding="utf-8",
        )
        self.git("config", "gpg.ssh.allowedSignersFile", str(self.allowed_signers))
        self.fake_refs["main"] = self.head_sha()

    def commit_signed(self, message, *, amend=False):
        result = subprocess.run(
            ["git", "-c", "commit.gpgsign=true", "commit", "-q",
             *(("--amend",) if amend else ()), "-m", message],
            cwd=self.target, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return self.head_sha()


class ArchiveSigningCases:
    def native_checkpoint(self, *args, expect=0):
        result = subprocess.run(
            [sys.executable, HEXCTL, *map(str, args)],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(expect, result.returncode, result.stderr)
        return result

    def portable_round_trip(self, portable, digest, scratch, proof):
        # Hide the producer's keys as well as its checkout. Only the archive's
        # public material can verify the restored history.
        keys = Path(self.key_root)
        hidden = keys.with_name(keys.name + "-hidden")
        if self.signature_format == "openpgp":
            # Stop the fixture agent before moving its socket directory;
            # otherwise the next signer can connect while the old agent exits.
            subprocess.run(
                [self.tool_paths["gpgconf"], "--homedir", self.key_home,
                 "--kill", "gpg-agent"],
                check=True, capture_output=True, timeout=10,
            )
        keys.rename(hidden)
        try:
            inspected = json.loads(self.native_checkpoint(
                "checkpoint", "inspect", "--archive", portable, "--sha256", digest,
            ).stdout)
            self.assertEqual(len(proof["commits"]), len(inspected["signatures"]))
            for record in inspected["signatures"]:
                self.assertEqual("G", record["status"])
                self.assertEqual(self.fingerprint, record["fingerprint"])
            restored = json.loads(self.native_checkpoint(
                "--dir", Path(scratch) / "restored", "checkpoint", "restore",
                "--archive", portable, "--sha256", digest,
            ).stdout)
            self.assertEqual("ok", restored["verify"])
        finally:
            hidden.rename(keys)

    def test_export_inspect_restore_without_producer_keys(self):
        archive = self.good_archive()
        members = self.good_members(archive)
        proof = json.loads(members["proof/signatures.json"])
        self.assertEqual(self.signature_format, proof["signer"]["format"])
        self.assertEqual([self.fingerprint], proof["signer"]["fingerprints"])
        self.assertTrue(proof["commits"])
        for record in proof["commits"]:
            self.assertEqual("G", record["status"])
            self.assertEqual(self.fingerprint, record["fingerprint"])

        with tempfile.TemporaryDirectory(prefix="fiat-portable-") as scratch:
            portable = Path(scratch) / "checkpoint.zip"
            portable.write_bytes(archive.read_bytes())
            digest = hashlib.sha256(portable.read_bytes()).hexdigest()
            shutil.rmtree(self.target)
            self.portable_round_trip(portable, digest, scratch, proof)

    def test_directory_export_inspect_restore_without_producer_keys(self):
        self.to_post_push()
        exported = json.loads(self.run_ctl("checkpoint", "archive", "--format", "directory").stdout)
        archive = Path(exported["archive"])
        proof = json.loads((archive / "proof/signatures.json").read_bytes())
        with tempfile.TemporaryDirectory(prefix="fiat-portable-") as scratch:
            portable = Path(scratch) / "checkpoint.directory"
            shutil.copytree(archive, portable)
            shutil.rmtree(self.target)
            self.portable_round_trip(portable, exported["outer_sha256"], scratch, proof)

    def assert_invalid_archive(self, members):
        specimen = self.write_specimen(members)
        digest = self.outer_sha256(specimen)
        for command in ("inspect", "restore"):
            with self.subTest(command=command):
                destination = Path(self.dir) / "refused-restore"
                result = self.native_checkpoint(
                    "--dir", destination, "checkpoint", command,
                    "--archive", specimen, "--sha256", digest, expect=1,
                )
                self.assertEqual("signature-unverified\n", result.stderr)
                self.assertEqual("", result.stdout)
                self.assertFalse(destination.exists())

    def test_inspect_and_restore_reject_substituted_or_malformed_fingerprints(self):
        archive = self.good_archive()
        other = ("SHA256:" + "A" * 43) if self.signature_format == "ssh" else "A" * 40
        self.assertNotEqual(self.fingerprint, other)
        foreign_format = "A" * 40 if self.signature_format == "ssh" else "SHA256:" + "A" * 43
        for candidate in (other, foreign_format, self.fingerprint + "=", "invalid"):
            with self.subTest(fingerprint=candidate):
                members = self.good_members(archive)
                manifest = self.manifest(members)
                proof = json.loads(members["proof/signatures.json"])
                proof["signer"]["fingerprints"] = [candidate]
                for record in proof["commits"]:
                    record["fingerprint"] = candidate
                manifest["signer"]["fingerprints"] = [candidate]
                payload = hexctl_module().canonical(proof).encode() + b"\n"
                self.retarget(members, manifest, "proof/signatures.json", payload)
                manifest["proof"]["sha256"] = hashlib.sha256(payload).hexdigest()
                self.set_manifest(members, manifest)
                self.assert_invalid_archive(members)

    def test_inspect_and_restore_reject_invalid_public_key_material(self):
        members = self.good_members()
        manifest = self.manifest(members)
        self.retarget(members, manifest, manifest["signer"]["key_path"], b"not a public key\n")
        self.set_manifest(members, manifest)
        self.assert_invalid_archive(members)

    def test_native_signature_verification_rejects_changed_commit_bytes(self):
        members = self.good_members()
        manifest = self.manifest(members)
        proof = json.loads(members["proof/signatures.json"])
        commit = self.git("cat-file", "commit", proof["commits"][0]["sha"]).stdout
        forged = subprocess.run(
            ["git", "hash-object", "-t", "commit", "-w", "--stdin"],
            input=commit + "changed after signing\n", cwd=self.target,
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        proof["commits"][0]["sha"] = forged
        payload = hexctl_module().canonical(proof).encode() + b"\n"
        members["proof/signatures.json"] = payload
        manifest["proof"]["sha256"] = hashlib.sha256(payload).hexdigest()
        error = StringIO()
        with tempfile.TemporaryDirectory() as scratch, redirect_stderr(error):
            with self.assertRaises(SystemExit) as refused:
                hexctl_module()._checkpoint_inspect_signatures(self.target, manifest, members, scratch)
        self.assertEqual(1, refused.exception.code)
        self.assertEqual("signature-unverified\n", error.getvalue())


class CheckpointOpenPgpSigningTests(ArchiveSigningCases, SignedRunFixture):
    signature_format = "openpgp"

    def test_signing_survives_producer_key_hiding(self):
        archive = self.good_archive()
        proof = json.loads(self.good_members(archive)["proof/signatures.json"])
        keys = Path(self.key_root)
        rename = Path.rename
        observed = []

        def checked_rename(source, destination):
            if source == keys:
                result = subprocess.run(
                    [self.tool_paths["gpg"], "--batch", "--no-autostart",
                     "--local-user", self.fingerprint, "--output", "-", "--detach-sign"],
                    input=b"agent must stop before its home moves\n",
                    env={**os.environ, "GNUPGHOME": self.key_home, "LC_ALL": "C"},
                    capture_output=True, timeout=10,
                )
                self.assertNotEqual(0, result.returncode,
                                    "producer agent is still signing when its home moves")
                self.assertIn(b"no gpg-agent running", result.stderr)
                observed.append(source)
            return rename(source, destination)

        with tempfile.TemporaryDirectory(prefix="fiat-portable-") as scratch:
            portable = Path(scratch) / "checkpoint.zip"
            portable.write_bytes(archive.read_bytes())
            digest = hashlib.sha256(portable.read_bytes()).hexdigest()
            with mock.patch.object(Path, "rename", checked_rename):
                self.portable_round_trip(portable, digest, scratch, proof)
        self.assertEqual([keys], observed)
        commit = self.signed_commit(self.trailers("after key hiding"))
        verified = subprocess.run(
            ["git", "verify-commit", commit], cwd=self.target,
            env={**os.environ, "GNUPGHOME": self.key_home},
            capture_output=True, timeout=10,
        )
        self.assertEqual(0, verified.returncode, verified.stderr)


class CheckpointSshSigningTests(ArchiveSigningCases, SshSignedRunFixture):
    signature_format = "ssh"

    def test_export_with_allowed_signers_inside_worktree(self):
        self.to_post_push()
        local = Path(self.target) / ".hexaemeron" / "allowed-signers"
        shutil.copyfile(self.allowed_signers, local)
        self.git("config", "gpg.ssh.allowedSignersFile", ".hexaemeron/allowed-signers")
        self.archive()

    def test_export_with_home_relative_allowed_signers(self):
        self.to_post_push()
        self.git("config", "gpg.ssh.allowedSignersFile", "~/allowed-signers")
        # HOME is private to this fixture command; no operator file is used.
        self.env["HOME"] = self.dir
        self.archive()

    def test_export_rejects_another_allowed_key(self):
        self.to_post_push()
        wrong_key = str(Path(self.dir) / "wrong-key")
        subprocess.run(
            [self.tool_paths["ssh-keygen"], "-q", "-t", "ed25519", "-N", "", "-f", wrong_key],
            check=True, capture_output=True, timeout=30,
        )
        self.allowed_signers.write_text(
            "fixture@example.invalid " + Path(wrong_key + ".pub").read_text(), encoding="utf-8",
        )
        result, _ = self.archive(expect=1)
        self.assertEqual("signature-unverified\n", result.stderr)
        self.assertFalse(list(self.store_root().glob("*/*")))


class CheckpointSignerInputTests(unittest.TestCase):
    def test_allowed_signers_capture_refuses_a_symlink_before_dotdot(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "actual" / "child").mkdir(parents=True)
            (root / "alias").symlink_to(root / "actual" / "child", target_is_directory=True)
            (root / "actual" / "allowed").write_bytes(b"configured public material\n")
            (root / "allowed").write_bytes(b"different public material\n")
            source = root / "alias" / ".." / "allowed"
            with mock.patch.object(module, "bounded_run", return_value=(0, os.fsencode(source) + b"\0")):
                with redirect_stderr(StringIO()) as error, self.assertRaises(SystemExit) as refused:
                    module._checkpoint_archive_ssh_material(str(root), str(root / "members"))
            self.assertEqual(1, refused.exception.code)
            self.assertEqual("signature-unverified\n", error.getvalue())
            self.assertFalse((root / "members").exists())

    def test_allowed_signers_capture_accepts_parent_components_without_links(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "child").mkdir()
            payload = b"configured public material\n"
            (root / "allowed").write_bytes(payload)
            source = root / "child" / ".." / "allowed"
            with mock.patch.object(module, "bounded_run", return_value=(0, os.fsencode(source) + b"\0")):
                member = module._checkpoint_archive_ssh_material(str(root), str(root / "members"))
            self.assertEqual(payload, (root / "members" / member).read_bytes())

    def test_fingerprints_are_canonical_and_format_specific(self):
        valid = hexctl_module()._checkpoint_archive_fingerprint_valid
        for fingerprint in ("A" * 40, "F" * 64):
            self.assertTrue(valid("openpgp", fingerprint))
            self.assertFalse(valid("ssh", fingerprint))
        ssh = "SHA256:" + "A" * 43
        self.assertTrue(valid("ssh", ssh))
        self.assertFalse(valid("openpgp", ssh))
        for fingerprint in (ssh + "=", ssh[:-1], ssh + "A", ssh[:-1] + "B", "MD5:" + "a" * 32):
            self.assertFalse(valid("ssh", fingerprint), fingerprint)
        for fingerprint in ("a" * 40, "A" * 41, "A" * 63):
            self.assertFalse(valid("openpgp", fingerprint), fingerprint)
        self.assertFalse(valid("x509", "A" * 40))

    def test_allowed_signers_capture_refuses_unsafe_files(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real = root / "real"
            real.write_bytes(b"public material\n")
            symlink = root / "symlink"
            symlink.symlink_to(real)
            fifo = root / "fifo"
            os.mkfifo(fifo)
            empty = root / "empty"
            empty.touch()
            linked = root / "linked"
            linked.hardlink_to(real)
            directory_link = root / "directory-link"
            directory_link.symlink_to(root, target_is_directory=True)
            for source in (symlink, fifo, empty, linked, directory_link / "empty", root / "absent"):
                with self.subTest(source=source.name), redirect_stderr(StringIO()) as error:
                    with mock.patch.object(module, "bounded_run", return_value=(0, os.fsencode(source) + b"\0")):
                        with self.assertRaises(SystemExit) as refused:
                            module._checkpoint_archive_ssh_material(str(root), str(root / "members"))
                    self.assertEqual(1, refused.exception.code)
                    self.assertEqual("signature-unverified\n", error.getvalue())
            linked.unlink()
            with mock.patch.object(module, "CHECKPOINT_ARCHIVE_ENTRY_BYTES_MAX", 4):
                with mock.patch.object(module, "bounded_run", return_value=(0, os.fsencode(real) + b"\0")):
                    with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                        module._checkpoint_archive_ssh_material(str(root), str(root / "members"))
            self.assertFalse((root / "members").exists())
