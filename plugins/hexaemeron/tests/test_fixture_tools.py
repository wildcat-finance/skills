"""Signing fixtures use real tools and retain their failure observations."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import fixture_tools


class NativeSigningFixtureTests(unittest.TestCase):
    def test_tool_selection_ignores_an_untrusted_path(self):
        with tempfile.TemporaryDirectory(prefix="fake-tools-") as temporary:
            fake = Path(temporary) / "gpg"
            fake.write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
            fake.chmod(0o755)
            with mock.patch.dict(os.environ, {"PATH": temporary}):
                actual = Path(fixture_tools.signing_tool("gpg"))
                self.assertTrue(actual.is_absolute())
                self.assertFalse(actual.samefile(fake))
                result = subprocess.run([str(actual), "--version"], check=True,
                                        capture_output=True, text=True, timeout=10)
                self.assertIn("GnuPG", result.stdout)

    def test_required_tool_absence_fails_without_changing_environment(self):
        before = dict(os.environ)
        with mock.patch.object(fixture_tools, "TOOL_DIRECTORIES", ()):
            with self.assertRaisesRegex(FileNotFoundError, "required fixture signing tool unavailable"):
                with fixture_tools.native_signing_tools():
                    self.fail("missing tools admitted a fixture")
        self.assertEqual(dict(os.environ), before)

    def test_success_restores_environment_and_removes_launchers(self):
        with mock.patch.dict(os.environ, {"PATH": os.defpath, "GIT_NO_REPLACE_OBJECTS": "1"}):
            before = dict(os.environ)
            with fixture_tools.native_signing_tools() as tools:
                directory = Path(os.environ["PATH"].split(os.pathsep)[0])
                self.assertEqual(set(tools), {"gpg", "gpgconf"})
                for name, executable in tools.items():
                    self.assertTrue((directory / name).samefile(executable))
                self.assertEqual(os.environ["GIT_NO_REPLACE_OBJECTS"], "1")
            self.assertEqual(dict(os.environ), before)
            self.assertFalse(directory.exists())

    def test_exception_restores_absent_path_and_removes_launchers(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("PATH", None)
            before = dict(os.environ)
            with self.assertRaisesRegex(RuntimeError, "fixture failed"):
                with fixture_tools.native_signing_tools():
                    directory = Path(os.environ["PATH"].split(os.pathsep)[0])
                    self.assertEqual(os.environ["PATH"], str(directory) + os.pathsep + os.defpath)
                    raise RuntimeError("fixture failed")
            self.assertEqual(dict(os.environ), before)
            self.assertFalse(directory.exists())

    def test_empty_path_exposes_only_the_selected_tool_launchers(self):
        with mock.patch.dict(os.environ, {"PATH": ""}):
            with fixture_tools.native_signing_tools():
                directory = Path(os.environ["PATH"])
                self.assertTrue(directory.is_dir())
                result = subprocess.run(["gpg", "--version"], check=True,
                                        capture_output=True, text=True, timeout=10)
                self.assertIn("GnuPG", result.stdout)
            self.assertEqual(os.environ["PATH"], "")
            self.assertFalse(directory.exists())

    def test_real_signature_verifies_and_changed_bytes_refuse(self):
        with mock.patch.dict(os.environ, {"PATH": os.defpath}):
            with fixture_tools.native_signing_tools() as tools:
                with tempfile.TemporaryDirectory(prefix="ft-") as temporary:
                    root = Path(temporary).resolve()
                    keyhome = root / "h"
                    keyhome.mkdir(mode=0o700)
                    environment = {**os.environ, "GNUPGHOME": str(keyhome)}
                    try:
                        subprocess.run([tools["gpg"], "--batch", "--pinentry-mode", "loopback",
                                        "--passphrase", "", "--quick-generate-key",
                                        "Tool Fixture <fixture@example.invalid>", "ed25519", "sign", "0"],
                                       env=environment, check=True, capture_output=True, timeout=30)
                        message = root / "message"
                        message.write_bytes(b"observed bytes\n")
                        subprocess.run([tools["gpg"], "--batch", "--detach-sign", str(message)],
                                       env=environment, check=True, capture_output=True, timeout=30)
                        command = ["gpg", "--batch", "--verify", str(message) + ".sig", str(message)]
                        valid = subprocess.run(command, env=environment, capture_output=True, timeout=30)
                        self.assertEqual(valid.returncode, 0, valid.stderr)
                        message.write_bytes(b"changed bytes\n")
                        changed = subprocess.run(command, env=environment, capture_output=True, timeout=30)
                        self.assertNotEqual(changed.returncode, 0)
                        self.assertIn(b"BAD signature", changed.stderr)
                    finally:
                        subprocess.run([tools["gpgconf"], "--homedir", str(keyhome), "--kill", "gpg-agent"],
                                       check=False, capture_output=True, timeout=10)
