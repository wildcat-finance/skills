"""A portable checkpoint must not move a fixture's live signing agent home."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from test_checkpoint_signing_formats import ArchiveSigningCases
from test_hexctl_checkpoint_archive import SignedRunFixture


class SigningAgentLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.keys = Path(self.temporary.name) / "producer"
        self.home = self.keys / "h"
        self.home.mkdir(parents=True)
        (self.home / "fixture-key").write_bytes(b"disposable fixture material")
        self.hidden = self.keys.with_name(self.keys.name + "-hidden")
        self.case = unittest.TestCase()
        self.case.key_root = str(self.keys)
        self.case.key_home = str(self.home)
        self.case.signature_format = "openpgp"
        self.case.fingerprint = "fixture-fingerprint"
        self.case.tool_paths = {"gpgconf": "/fixture/gpgconf"}
        self.case.native_checkpoint = mock.Mock(side_effect=lambda *argv: subprocess.CompletedProcess(
            [], 0, json.dumps({"signatures": []} if argv[0] == "checkpoint" else {"verify": "ok"}),
        ))

    def round_trip(self):
        ArchiveSigningCases.portable_round_trip(
            self.case, Path(self.temporary.name) / "checkpoint.zip", "digest",
            self.temporary.name, {"commits": []},
        )

    def test_a_live_agent_is_stopped_before_its_key_home_is_hidden(self):
        live = True
        original_rename = Path.rename

        def stop(argv, **kwargs):
            nonlocal live
            self.assertEqual(argv, ["/fixture/gpgconf", "--homedir", str(self.home),
                                    "--kill", "gpg-agent"])
            self.assertTrue(self.home.is_dir())
            self.assertFalse(self.hidden.exists())
            live = False
            return subprocess.CompletedProcess(argv, 0, "", "")

        def rename(path, destination):
            if path == self.keys:
                self.assertFalse(live, "moving a live agent home races later signing")
            return original_rename(path, destination)

        with mock.patch("subprocess.run", side_effect=stop) as stopped, \
                mock.patch.object(Path, "rename", rename):
            self.round_trip()
        stopped.assert_called_once()
        self.assertTrue(self.home.is_dir())
        self.assertFalse(self.hidden.exists())
        self.assertEqual(self.case.native_checkpoint.call_count, 2)

    def test_failed_agent_shutdown_leaves_keys_in_place_and_refuses_verification(self):
        with mock.patch("subprocess.run", return_value=subprocess.CompletedProcess(
                [], 1, "", "fixture agent shutdown refused")):
            with self.assertRaisesRegex(AssertionError, "fixture agent shutdown refused"):
                self.round_trip()
        self.assertTrue(self.home.is_dir())
        self.assertFalse(self.hidden.exists())
        self.case.native_checkpoint.assert_not_called()

    def test_unavailable_or_timed_out_shutdown_never_moves_the_keys(self):
        for error in (OSError("unavailable"), subprocess.TimeoutExpired("gpgconf", 10)):
            with self.subTest(error=type(error).__name__):
                with mock.patch("subprocess.run", side_effect=error):
                    with self.assertRaises(type(error)):
                        self.round_trip()
                self.assertTrue(self.home.is_dir())
                self.assertFalse(self.hidden.exists())
                self.case.native_checkpoint.assert_not_called()

    def test_ssh_portability_does_not_stop_an_openpgp_agent(self):
        self.case.signature_format = "ssh"
        del self.case.key_home
        self.case.tool_paths = {"ssh-keygen": "/fixture/ssh-keygen"}
        with mock.patch("subprocess.run") as stopped:
            self.round_trip()
        stopped.assert_not_called()
        self.assertTrue(self.home.is_dir())
        self.assertEqual(self.case.native_checkpoint.call_count, 2)

    def test_verification_failure_still_restores_the_hidden_keys(self):
        self.case.native_checkpoint.side_effect = AssertionError("verification refused")
        with mock.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")):
            with self.assertRaisesRegex(AssertionError, "verification refused"):
                self.round_trip()
        self.assertTrue(self.home.is_dir())
        self.assertFalse(self.hidden.exists())

    def test_failed_fixture_signing_retains_the_native_error(self):
        from test_checkpoint_signing_formats import CheckpointOpenPgpSigningTests
        case = CheckpointOpenPgpSigningTests("test_export_inspect_restore_without_producer_keys")
        diagnostic = "gpg: can't connect to the agent: End of file"
        caught = None
        with mock.patch.object(SignedRunFixture, "commit_signed", side_effect=
                               subprocess.CalledProcessError(128, ["git"], b"", diagnostic.encode())):
            try:
                case.commit_signed("fixture commit")
            except Exception as error:
                caught = error
        self.assertIsInstance(caught, AssertionError)
        self.assertIn(diagnostic, str(caught))


if __name__ == "__main__":
    unittest.main()
