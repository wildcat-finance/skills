"""Signed specimens for the first-receipt OpenPGP email guard."""

from contextlib import redirect_stderr
from copy import deepcopy
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture_tools import native_signing_tools
from hexctl_harness import hexctl_module


class CommitEmailReadinessTests(unittest.TestCase):
    def assert_refused(self, expected, action):
        output = StringIO()
        with redirect_stderr(output), self.assertRaises(SystemExit):
            action()
        self.assertIn(expected, output.getvalue())

    @classmethod
    def setUpClass(cls):
        cls.tools_context = native_signing_tools()
        cls.tools = cls.tools_context.__enter__()
        cls.temporary = tempfile.TemporaryDirectory(prefix="fiat-uid-")
        cls.root = Path(cls.temporary.name)
        cls.home = cls.root / "keys"
        cls.home.mkdir(mode=0o700)
        cls.env = {**os.environ, "GNUPGHOME": str(cls.home)}
        cls.repo = cls.root / "repo"
        cls.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(cls.repo)], check=True)
        for key, value in (("user.name", "Fixture"),
                           ("user.email", "fixture@example.invalid"),
                           ("commit.gpgsign", "true"),
                           ("user.signingkey", "fixture@example.invalid"),
                           ("gpg.format", "openpgp")):
            subprocess.run(["git", "-C", str(cls.repo), "config", key, value], check=True)
        subprocess.run(
            [cls.tools["gpg"], "--batch", "--pinentry-mode", "loopback", "--passphrase", "",
             "--quick-generate-key", "Fixture <fixture@example.invalid>", "ed25519", "sign", "0"],
            env=cls.env, check=True, capture_output=True, timeout=30,
        )
        cls.module = hexctl_module()
        cls.commits = {}
        for label, author, committer in (
            ("matching", "other@example.invalid", "fixture@example.invalid"),
            ("mismatch", "fixture@example.invalid", "wrong@example.invalid"),
        ):
            environment = {**cls.env, "GIT_AUTHOR_NAME": "Author",
                           "GIT_AUTHOR_EMAIL": author,
                           "GIT_COMMITTER_NAME": "Committer",
                           "GIT_COMMITTER_EMAIL": committer}
            subprocess.run(["git", "-C", str(cls.repo), "commit", "--allow-empty", "-S",
                            "-q", "-m", label], env=environment, check=True,
                           capture_output=True, timeout=30)
            cls.commits[label] = subprocess.run(
                ["git", "-C", str(cls.repo), "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()

    @classmethod
    def tearDownClass(cls):
        subprocess.run([cls.tools["gpgconf"], "--homedir", str(cls.home),
                        "--kill", "gpg-agent"], check=False, capture_output=True,
                       timeout=10)
        cls.temporary.cleanup()
        cls.tools_context.__exit__(None, None, None)

    def test_real_signed_mismatch_is_refused_at_first_receipt(self):
        with mock.patch.dict(os.environ, self.env):
            commit = self.commits["mismatch"]
            self.assertEqual(self.module.verify_local_commit(str(self.repo), commit, "fixture"), commit)
            self.assert_refused(
                "committer email 'wrong@example.invalid' is absent",
                lambda: self.module.require_openpgp_uid_commit(str(self.repo), commit, "fixture"),
            )

    def test_author_difference_does_not_refuse_matching_committer(self):
        with mock.patch.dict(os.environ, self.env):
            commit = self.commits["matching"]
            self.module.verify_local_commit(str(self.repo), commit, "fixture")
            self.module.require_openpgp_uid_commit(str(self.repo), commit, "fixture")

    def test_missing_or_malformed_key_output_refuses(self):
        with mock.patch.dict(os.environ, self.env):
            commit = self.commits["matching"]
            original = self.module.bounded_tool
            def malformed(base_dir, program, argv, *args, **kwargs):
                return b"bad" if program == "gpg" else original(base_dir, program, argv, *args, **kwargs)
            with mock.patch.object(self.module, "bounded_tool", side_effect=malformed):
                self.assert_refused("listing does not bind signer",
                    lambda: self.module.require_openpgp_uid_commit(str(self.repo), commit, "fixture"))
            def unavailable(base_dir, program, argv, *args, **kwargs):
                if program == "gpg":
                    raise SystemExit(2)
                return original(base_dir, program, argv, *args, **kwargs)
            with mock.patch.object(self.module, "bounded_tool", side_effect=unavailable):
                with self.assertRaises(SystemExit):
                    self.module.require_openpgp_uid_commit(str(self.repo), commit, "fixture")

    def test_subkey_fingerprint_and_duplicate_uids_are_accepted(self):
        with mock.patch.dict(os.environ, self.env):
            commit = self.commits["matching"]
            metadata = subprocess.run(
                ["git", "-C", str(self.repo), "show", "-s", "--format=%GF%x00%GP", commit],
                check=True, capture_output=True,
            ).stdout.strip().split(b"\0")
            primary = metadata[1].decode()
            subkey = "A" * len(primary)
            uid = ":".join(["uid", "u", "", "", "", "", "", "", "",
                            "Fixture <fixture@example.invalid>", ""])
            listing = (f"pub:u:::::::::\n"
                       f"fpr:::::::::{primary}:\n"
                       f"{uid}\n{uid}\n"
                       f"sub:u:::::::::\n"
                       f"fpr:::::::::{subkey}:\n").encode()
            original = self.module.bounded_git
            original_tool = self.module.bounded_tool
            with mock.patch.object(self.module, "bounded_git") as git_read:
                def substitute(base_dir, argv, *args, **kwargs):
                    if "--format=%GF%x00%GP" in argv:
                        return f"{subkey}\0{primary}\n".encode()
                    return original(base_dir, argv, *args, **kwargs)
                git_read.side_effect = substitute
                def key_listing(base_dir, program, argv, *args, **kwargs):
                    return listing if program == "gpg" else original_tool(base_dir, program, argv, *args, **kwargs)
                with mock.patch.object(self.module, "bounded_tool", side_effect=key_listing):
                    self.module.require_openpgp_uid_commit(str(self.repo), commit, "fixture")

    def test_unrelated_primary_uid_cannot_supply_committer_email(self):
        with mock.patch.dict(os.environ, self.env):
            commit = self.commits["matching"]
            original = self.module.bounded_tool
            wrong = "A" * 40
            uid = ":".join(["uid", "u", "", "", "", "", "", "", "",
                            "Other <fixture@example.invalid>", ""])
            listing = (f"pub:u:::::::::\n"
                       f"fpr:::::::::{wrong}:\n"
                       f"{uid}\n").encode()
            def key_listing(base_dir, program, argv, *args, **kwargs):
                return listing if program == "gpg" else original(base_dir, program, argv, *args, **kwargs)
            with mock.patch.object(self.module, "bounded_tool", side_effect=key_listing):
                self.assert_refused("listing has another primary key",
                    lambda: self.module.require_openpgp_uid_commit(str(self.repo), commit, "fixture"))

    def test_unknown_signature_marker_cannot_skip_openpgp_readiness(self):
        with mock.patch.dict(os.environ, self.env):
            commit = self.commits["mismatch"]
            original = self.module.bounded_git
            def unknown_marker(base_dir, argv, *args, **kwargs):
                data = original(base_dir, argv, *args, **kwargs)
                if "cat-file" in argv and "commit" in argv:
                    return data.replace(b"gpgsig -----BEGIN PGP SIGNATURE-----",
                                        b"gpgsig -----BEGIN UNKNOWN SIGNATURE-----", 1)
                return data
            with mock.patch.object(self.module, "bounded_git", side_effect=unknown_marker):
                self.assert_refused("unrecognized signature metadata",
                    lambda: self.module.require_openpgp_uid_commit(str(self.repo), commit, "fixture"))

    def test_implementation_receipt_refuses_real_mismatch_without_mutation(self):
        controller = self.module
        step = {"n": 1, "phase": "implement", "receipts": {}}
        state = {"phase": "steps", "current_step": 1, "steps": [step],
                 "base": self.commits["matching"], "receipts": {}}
        before = deepcopy(state)
        args = SimpleNamespace(dir=str(self.repo), branch="HEAD",
                               commit=self.commits["mismatch"], tests="fixture")
        ledger = self.repo / ".hexaemeron" / "ledger.jsonl"
        ledger.parent.mkdir(exist_ok=True)
        ledger.write_bytes(b"prior receipt\n")
        with mock.patch.dict(os.environ, self.env), \
             mock.patch.object(controller, "receipted_known_failure_inventory", return_value=None), \
             mock.patch.object(controller, "_criteria_success_for_step"), \
             mock.patch.object(controller, "commit") as record:
            self.assert_refused(
                "committer email 'wrong@example.invalid' is absent",
                lambda: controller.done_implement(args, state),
            )
        record.assert_not_called()
        self.assertEqual(state, before)
        self.assertEqual(ledger.read_bytes(), b"prior receipt\n")

    def test_empty_range_does_not_invent_a_commit(self):
        self.module.require_openpgp_uid_range(str(self.repo), [], "prose")

    def test_prose_checks_the_audit_closure_fixes_head(self):
        controller = self.module
        closure_head = self.commits["matching"]
        earlier_head = self.commits["mismatch"]
        step = {
            "n": 1,
            "phase": "prose",
            "receipts": {
                "implement": {"verified_commits": [earlier_head]},
                "audit": {"verified_fixes": [closure_head]},
            },
            "audit": {"rounds": []},
        }
        state = {
            "phase": "steps",
            "current_step": 1,
            "steps": [step],
            "config": {"skills": {"prose_lint": "lint", "voice": "voice"}},
        }
        args = SimpleNamespace(dir=str(self.repo), files=0, skills="lint,voice")
        with mock.patch.object(controller, "require_final_green_admission"), \
             mock.patch.object(controller, "require_openpgp_uid_commit") as readiness, \
             mock.patch.object(controller, "commit"):
            controller.done_prose(args, state)
        readiness.assert_called_once_with(str(self.repo), closure_head, "step 1 prose head")


if __name__ == "__main__":
    unittest.main()
