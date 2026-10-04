"""Signed specimens for the first-receipt OpenPGP email guard."""

from contextlib import redirect_stderr
from copy import deepcopy
from io import StringIO
import os
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture_tools import native_signing_tools
from fiat_commit_supersession_proof import live_platform_readback
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


class EffectiveCommitTests(unittest.TestCase):
    """A legacy signed three-receipt chain and its rewritten sibling chain."""

    @classmethod
    def setUpClass(cls):
        cls.tools_context = native_signing_tools()
        cls.tools = cls.tools_context.__enter__()
        # The agent creates several sockets, including S.gpg-agent.browser.
        # Keep the canonical home short enough for macOS AF_UNIX sun_path.
        cls.temporary = tempfile.TemporaryDirectory(prefix="fs-")
        cls.root = Path(cls.temporary.name)
        cls.home = cls.root / "h"
        cls.home.mkdir(mode=0o700)
        socket_path = os.path.realpath(cls.home / "S.gpg-agent.browser")
        if len(os.fsencode(socket_path)) >= 104:
            raise AssertionError(f"fixture GPG agent socket path is too long: {socket_path}")
        cls.env = {**os.environ, "GNUPGHOME": str(cls.home)}
        generated = subprocess.run(
            [cls.tools["gpg"], "--batch", "--pinentry-mode", "loopback", "--passphrase", "",
             "--quick-generate-key", "Fixture <fixture@example.invalid>", "ed25519", "sign", "0"],
            env=cls.env, capture_output=True, timeout=30,
        )
        if generated.returncode:
            raise AssertionError(
                f"fixture GPG key generation exited {generated.returncode}: "
                f"{generated.stderr.decode('utf-8', 'replace')[:2048]}"
            )
        cls.module = hexctl_module()

    @classmethod
    def tearDownClass(cls):
        subprocess.run([cls.tools["gpgconf"], "--homedir", str(cls.home), "--kill", "gpg-agent"],
                       check=False, capture_output=True, timeout=10)
        cls.temporary.cleanup()
        cls.tools_context.__exit__(None, None, None)

    def setUp(self):
        self.temporary_repo = tempfile.TemporaryDirectory(prefix="history-")
        self.repo = Path(self.temporary_repo.name)
        self.git("init", "-q", "-b", "main")
        for key, value in (("user.name", "Fixture"), ("user.email", "fixture@example.invalid"),
                           ("commit.gpgsign", "true"), ("user.signingkey", "fixture@example.invalid"),
                           ("gpg.format", "openpgp")):
            self.git("config", key, value)
        self.base = self.make_commit("base", "fixture@example.invalid")
        self.old = [self.make_commit(f"old-{number}", "wrong@example.invalid") for number in range(1, 4)]
        self.git("switch", "-q", "-c", "repair", self.base)
        self.new = [self.make_commit(f"new-{number}", "fixture@example.invalid") for number in range(1, 4)]
        self.write_run(self.old[0])

    def write_run(self, implement_commit, round_commits=None):
        """Write the run state and ledger, holding the receipted `commit` and round `fixes_commit` values."""
        round_commits = round_commits or [self.old[1], self.old[2]]
        self.controller = self.repo / ".hexaemeron"
        self.controller.mkdir(exist_ok=True)
        self.state = {
            "phase": "steps", "current_step": 1, "base": self.base,
            "config": {"skills": {}, "audit": {}, "git": {}}, "receipts": {},
            "steps": [{"n": 1, "phase": "audit", "status": "open",
                       "receipts": {"implement": {"branch": "repair", "commit": implement_commit,
                                                  "verified_commits": [self.old[0]]}},
                       "audit": {"rounds": [
                           {"round": 1, "fixes_commit": round_commits[0], "verified_commits": [self.old[1]]},
                           {"round": 2, "fixes_commit": round_commits[1], "verified_commits": [self.old[2]]},
                       ]}}],
        }
        (self.controller / "state.json").write_text(json.dumps(self.state), encoding="utf-8")
        previous = "genesis"
        rows = []
        for event, data in (
            ("done:implement", {"step": 1, "branch": "repair", "commit": implement_commit,
                                "verified_commits": [self.old[0]]}),
            ("audit-round", {"step": 1, "round": 1, "fixes_commit": round_commits[0],
                             "verified_commits": [self.old[1]]}),
            ("audit-round", {"step": 1, "round": 2, "fixes_commit": round_commits[1],
                             "verified_commits": [self.old[2]]}),
        ):
            state_digest = (
                self.module.state_fingerprint(self.state)
                if event == "audit-round" and data["round"] == 2 else "fixture"
            )
            row = {"ts": "fixture", "event": event, "data": data, "prev": previous,
                   "state": state_digest}
            row["hash"] = hashlib.sha256(self.module.canonical(row).encode()).hexdigest()
            previous = row["hash"]
            rows.append(json.dumps(row, sort_keys=True) + "\n")
        self.ledger = self.controller / "ledger.jsonl"
        self.ledger.write_text("".join(rows), encoding="utf-8")
        self.original_ledger = self.ledger.read_bytes()

    def tearDown(self):
        self.temporary_repo.cleanup()

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.repo, env=self.env,
                                check=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()

    def make_commit(self, label, email):
        env = {**self.env, "GIT_AUTHOR_NAME": "Author", "GIT_AUTHOR_EMAIL": email,
               "GIT_COMMITTER_NAME": "Committer", "GIT_COMMITTER_EMAIL": email}
        if label in {f"{prefix}-{number}" for prefix in ("old", "new") for number in range(1, 4)}:
            number = int(label.rsplit("-", 1)[1])
            (self.repo / f"step-{number}.txt").write_text(
                f"tree content for receipt {number}\n", encoding="utf-8"
            )
            self.git("add", f"step-{number}.txt")
        subprocess.run(["git", "commit", "--allow-empty", "-S", "-q", "-m", label],
                       cwd=self.repo, env=env, check=True, capture_output=True, timeout=30)
        return self.git("rev-parse", "HEAD")

    def supersede(self, index):
        args = SimpleNamespace(dir=str(self.repo), old=self.old[index], new=self.new[index])
        with mock.patch.dict(os.environ, self.env), \
             mock.patch.object(self.module, "verify_run"), \
             mock.patch.object(self.module, "verify_github_commits", return_value=[self.new[index]]):
            self.module.cmd_supersede_commit(args)

    def test_order_and_raw_ledger(self):
        for number in range(3):
            self.supersede(number)
        state = self.module.load_state(str(self.repo))
        self.assertEqual(self.module.last_local_commit(state["steps"][0]), self.new[-1])
        self.assertEqual([row["old"] for row in state["steps"][0]["supersessions"]], self.old)
        self.assertTrue(self.ledger.read_bytes().startswith(self.original_ledger))
        with mock.patch.dict(os.environ, self.env):
            self.module.verify_supersessions(str(self.repo), state, self.module.ledger_entries(str(self.repo)))

    def test_joined_disposable_verify_checkpoint_and_push(self):
        """Exercise the actual controller readers around one simulated host."""
        self.git("remote", "add", "origin", "https://github.com/wildcat-finance/skills.git")
        self.git("branch", "demo", self.base)
        self.git("branch", "demo-step-1-repair", self.new[-1])
        self.state["run_branch"] = "demo"
        self.state["config"]["git"]["base"] = "main"
        self.state["steps"][0]["title"] = "repair"
        self.module.commit(str(self.repo), self.state, "fixture:stack", {"step": 1})
        calls = []
        verified = True

        def github_rest(_base_dir, path, _label):
            calls.append(path)
            if path == "repos/wildcat-finance/skills":
                return {"full_name": "wildcat-finance/skills"}
            prefix = "repos/wildcat-finance/skills/commits/"
            self.assertTrue(path.startswith(prefix), path)
            sha = path[len(prefix):]
            self.assertIn(sha, self.new)
            identity = {"name": "Fixture", "email": "fixture@example.invalid"}
            return {
                "sha": sha,
                "author": {"login": "fixture"},
                "committer": {"login": "fixture"},
                "commit": {
                    "author": identity, "committer": identity,
                    "message": "signed fixture",
                    "verification": {
                        "verified": verified,
                        "reason": "valid" if verified else "no_user",
                    },
                },
            }

        with mock.patch.dict(os.environ, self.env), \
             mock.patch.object(self.module, "github_rest", side_effect=github_rest):
            # A matching local UID does not decide the host's account/email gate.
            self.module.require_openpgp_uid_commit(str(self.repo), self.new[0], "fixture")
            original = self.ledger.read_bytes()
            verified = False
            with self.assertRaises(SystemExit):
                self.module.cmd_supersede_commit(SimpleNamespace(
                    dir=str(self.repo), old=self.old[0], new=self.new[0]))
            self.assertEqual(self.ledger.read_bytes(), original)
            verified = True
            for old, new in zip(self.old, self.new):
                self.module.cmd_supersede_commit(SimpleNamespace(
                    dir=str(self.repo), old=old, new=new))
            self.assertEqual(self.module.verify_run(str(self.repo)), 7)
            state = self.module.load_state(str(self.repo))
            refs = self.module._checkpoint_refs(str(self.repo), state)
            self.assertTrue(all(refs[sha] == sha for sha in self.old))
            self.assertEqual(
                self.module.verify_local_range(str(self.repo), "demo", self.new[-1], "fixture"),
                self.new,
            )
            state["steps"][0]["phase"] = "push"
            self.module.commit(str(self.repo), state, "fixture:prose", {"step": 1})
            args = SimpleNamespace(
                dir=str(self.repo), pr_url="https://github.com/wildcat-finance/skills/pull/1",
                head_commit=self.new[-1], pr_base="demo", merge_commit=None,
                closed_issue_url=None,
            )
            with mock.patch.object(self.module, "require_final_green_admission"), \
                 mock.patch.object(self.module, "inspect_pull_request", return_value={
                     "author_login": "fixture", "early_merge": False,
                 }):
                self.module.done_push(args, state)
            receipt = state["steps"][0]["receipts"]["push"]
            self.assertEqual(receipt["verified_commits"], self.new)
            self.assertEqual(receipt["github_verified"], self.new)
            self.assertTrue(all(sha not in receipt["verified_commits"] for sha in self.old))
            self.assertEqual(self.module.verify_run(str(self.repo)), 9)
            verified = False
            with self.assertRaises(SystemExit):
                live_platform_readback(self.module, self.repo)
            verified = True
            self.assertEqual(live_platform_readback(self.module, self.repo), self.new)
        for sha in self.new:
            self.assertIn(f"repos/wildcat-finance/skills/commits/{sha}", calls)

    def test_audit_and_push_effective_heads(self):
        for number in range(3):
            self.supersede(number)
        state = self.module.load_state(str(self.repo))
        step = state["steps"][0]
        entries = self.module.ledger_entries(str(self.repo))
        self.module.require_effective_push_range(str(self.repo), step, entries, self.new)
        for live in ([*self.old], [self.new[0], self.old[1], self.new[2]],
                     [self.new[1], self.new[0], self.new[2]]):
            with self.subTest(live=live), self.assertRaises(SystemExit):
                self.module.require_effective_push_range(str(self.repo), step, entries, live)
        state["receipts"]["security_suite"] = "waived: test fixture"
        for index, round_entry in enumerate(step["audit"]["rounds"]):
            round_entry["findings"] = 1 if index == 0 else 0
            round_entry["log"] = "audit/rounds/fixture.md"
        args = SimpleNamespace(dir=str(self.repo), no_further_leads=False,
                               reason=None, log=None, fixes_ref=None)
        with mock.patch.object(self.module, "require_final_green_admission"), \
             mock.patch.object(self.module, "commit"):
            self.module.done_audit(args, state)
        self.assertEqual(step["receipts"]["audit"]["fixes_ref"], self.new[-1])
        self.assertEqual(step["receipts"]["audit"]["verified_fixes"], [])

    def test_moved_step_ref_refuses(self):
        self.supersede(0)
        state = self.module.load_state(str(self.repo))
        with mock.patch.dict(os.environ, self.env):
            self.module.verify_supersessions(
                str(self.repo), state, self.module.ledger_entries(str(self.repo)))
        self.git("switch", "-q", "--detach", self.new[-1])
        self.git("branch", "-f", "repair", self.old[-1])
        with mock.patch.dict(os.environ, self.env), self.assertRaises(SystemExit):
            self.module.verify_supersessions(
                str(self.repo), state, self.module.ledger_entries(str(self.repo)))

    def test_checkpoint_bundle_restore(self):
        for number in range(3):
            self.supersede(number)
        state = self.module.load_state(str(self.repo))
        refs = self.module._checkpoint_refs(str(self.repo), state)
        self.assertEqual({refs[sha] for sha in self.old}, set(self.old))
        bundle = self.root / f"{self.repo.name}.bundle"
        self.module._checkpoint_archive_bundle(str(self.repo), refs, str(bundle))
        restored = self.root / f"{self.repo.name}-restored"
        restored.mkdir()
        subprocess.run(["git", "init", "-q", str(restored)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(restored), "fetch", "--no-tags", str(bundle),
                        "+refs/heads/*:refs/heads/*"], check=True, capture_output=True)
        for sha in [*self.old, *self.new]:
            subprocess.run(["git", "-C", str(restored), "cat-file", "-e", sha + "^{commit}"],
                           check=True, capture_output=True)

        scripts = Path(__file__).resolve().parents[1] / "skills" / "fiat" / "scripts"
        sys.path.insert(0, str(scripts))
        from checkpoint_authority.coverage import derive
        self.git("branch", "-f", "main", self.base)
        candidate = deepcopy(state)
        candidate["run_branch"] = "main"
        anchor = {"initial_base_sha": self.base, "run_branch": "main"}
        candidate["receipts"]["run_anchor"] = anchor
        entries = deepcopy(self.module.ledger_entries(str(self.repo)))
        for row in entries:
            if row["event"] == "done:implement":
                row["data"].update({"branch": "repair", "commit": self.old[0]})
            if row["event"] == "audit-round":
                row["data"].update(candidate["steps"][0]["audit"]["rounds"][row["data"]["round"] - 1])
        anchor_digest = hashlib.sha256(self.module.canonical(anchor).encode()).hexdigest()
        entries.insert(0, {"event": "init", "data": {"run_anchor_sha256": anchor_digest}})
        metadata = SimpleNamespace(state=candidate, entries=entries,
                                   manifest={"boundary": {"refs": {**refs, "main": self.base}}})
        identity = {"identity": {"run": anchor, "boundary": {
            "step": 1, "kind": "audit-verdict", "working_commit_sha": self.new[-1]}}}
        approval = SimpleNamespace(anchor_sha256=anchor_digest,
                                   initial_base=self.base, start_commit=self.base)
        def native_git(argv):
            result = subprocess.run(["git", "--no-replace-objects", *argv], cwd=self.repo,
                                    env=self.env, check=True, capture_output=True, timeout=10)
            return result.stdout
        denominator = derive(metadata, identity, approval, native_git)
        self.assertEqual(denominator["required"], sorted(self.new))
        self.assertEqual(denominator["native_expected"], [self.new[-1]])
        self.assertTrue(all(sha not in denominator["required"] for sha in self.old))

    def test_refusals_do_not_append(self):
        before = self.ledger.read_bytes()
        with mock.patch.dict(os.environ, self.env), \
             mock.patch.object(self.module, "verify_run"), \
             mock.patch.object(self.module, "verify_github_commits", side_effect=SystemExit(1)):
            with self.assertRaises(SystemExit):
                self.module.cmd_supersede_commit(SimpleNamespace(
                    dir=str(self.repo), old=self.old[0], new=self.new[0]))
        self.assertEqual(self.ledger.read_bytes(), before)
        self.supersede(0)
        before = self.ledger.read_bytes()
        with mock.patch.dict(os.environ, self.env), mock.patch.object(self.module, "verify_run"):
            for old, new in ((self.old[0], self.new[0]), (self.old[2], self.new[1]),
                             ("f" * 40, self.new[1]), (self.new[0], self.old[0])):
                with self.subTest(old=old, new=new), self.assertRaises(SystemExit):
                    self.module.cmd_supersede_commit(SimpleNamespace(dir=str(self.repo), old=old, new=new))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_changed_tree_or_old_in_branch_refuse(self):
        self.git("switch", "-q", "--detach", self.base)
        (self.repo / "changed.txt").write_text("different tree\n", encoding="utf-8")
        self.git("add", "changed.txt")
        changed = self.make_commit("changed-tree", "fixture@example.invalid")
        self.git("branch", "-f", "repair", changed)
        self.git("switch", "-q", "repair")
        before = self.ledger.read_bytes()
        with mock.patch.dict(os.environ, self.env), \
             mock.patch.object(self.module, "verify_run"), \
             mock.patch.object(self.module, "verify_github_commits") as platform:
            with self.assertRaises(SystemExit):
                self.module.cmd_supersede_commit(SimpleNamespace(
                    dir=str(self.repo), old=self.old[0], new=changed))
        platform.assert_not_called()
        self.assertEqual(self.ledger.read_bytes(), before)
        self.git("switch", "-q", "--detach", self.old[0])
        self.git("branch", "-f", "repair", self.old[0])
        self.git("switch", "-q", "repair")
        descendant = self.make_commit("old-still-ancestor", "fixture@example.invalid")
        with mock.patch.dict(os.environ, self.env), mock.patch.object(self.module, "verify_run"):
            with self.assertRaises(SystemExit):
                self.module.cmd_supersede_commit(SimpleNamespace(
                    dir=str(self.repo), old=self.old[0], new=descendant))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_wrong_step_or_platform_no_receipt(self):
        altered = json.loads((self.controller / "state.json").read_text(encoding="utf-8"))
        altered["current_step"] = altered["steps"][0]["n"] = 2
        (self.controller / "state.json").write_text(json.dumps(altered), encoding="utf-8")
        before = self.ledger.read_bytes()
        with mock.patch.dict(os.environ, self.env), mock.patch.object(self.module, "verify_run"):
            with self.assertRaises(SystemExit):
                self.module.cmd_supersede_commit(SimpleNamespace(
                    dir=str(self.repo), old=self.old[0], new=self.new[0]))
        self.assertEqual(self.ledger.read_bytes(), before)
        (self.controller / "state.json").write_text(json.dumps(self.state), encoding="utf-8")
        with mock.patch.dict(os.environ, self.env), \
             mock.patch.object(self.module, "verify_run"), \
             mock.patch.object(self.module, "verify_github_commits", side_effect=SystemExit(2)):
            with self.assertRaises(SystemExit):
                self.module.cmd_supersede_commit(SimpleNamespace(
                    dir=str(self.repo), old=self.old[0], new=self.new[0]))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_append_interruptions_resume_once(self):
        for boundary in ("before", "after"):
            with self.subTest(boundary=boundary):
                # Each subtest starts from the fixture's first untouched source.
                if boundary == "after":
                    self.tearDown(); self.setUp()
                with mock.patch.dict(os.environ, self.env), \
                     mock.patch.object(self.module, "verify_run"), \
                     mock.patch.object(self.module, "verify_github_commits", return_value=[self.new[0]]):
                    # The ledger stage is complete, but interruption before
                    # its atomic rename must leave the original bytes intact.
                    target = "_guard_atomic_replace" if boundary == "before" else "save_state"
                    with mock.patch.object(self.module, target, side_effect=RuntimeError("injected interrupt")):
                        with self.assertRaisesRegex(RuntimeError, "injected interrupt"):
                            self.module.cmd_supersede_commit(SimpleNamespace(
                                dir=str(self.repo), old=self.old[0], new=self.new[0]))
                    self.assertTrue(Path(self.module.supersession_pending_path(str(self.repo))).exists())
                    if boundary == "before":
                        self.assertEqual(self.ledger.read_bytes(), self.original_ledger)
                    self.module.cmd_supersede_commit(SimpleNamespace(
                        dir=str(self.repo), old=self.old[0], new=self.new[0]))
                state = self.module.load_state(str(self.repo))
                self.assertEqual(len(state["steps"][0]["supersessions"]), 1)
                self.assertEqual(self.ledger.read_bytes().count(b'"event": "commit:supersede"'), 1)
                self.assertTrue(self.ledger.read_bytes().startswith(self.original_ledger))

    def test_short_implement_commit_is_accepted_through_supersession(self):
        """Older controllers stored the receipted `commit` as given; 9 characters is real."""
        self.write_run(self.old[0][:9])
        for number in range(3):
            self.supersede(number)
        state = self.module.load_state(str(self.repo))
        step = state["steps"][0]
        entries = self.module.ledger_entries(str(self.repo))
        self.assertEqual(step["receipts"]["implement"]["commit"], self.old[0][:9])
        self.assertEqual(entries[0]["data"]["commit"], self.old[0][:9])
        self.assertEqual([row["old"] for row in step["supersessions"]], self.old)
        with mock.patch.dict(os.environ, self.env):
            self.module.verify_supersessions(str(self.repo), state, entries)
        self.module.require_effective_push_range(str(self.repo), step, entries, self.new)
        self.assertTrue(self.ledger.read_bytes().startswith(self.original_ledger))

    def test_implement_commit_forms_that_do_not_name_the_endpoint_refuse(self):
        for label, recorded in (
            ("another receipt's prefix", self.old[1][:9]),
            ("full-length other commit", self.old[1]),
            ("below the seven-character floor", self.old[0][:6]),
            ("uppercase prefix", self.old[0][:9].upper()),
            ("no commit", None),
        ):
            with self.subTest(label):
                self.write_run(recorded)
                before = self.ledger.read_bytes()
                output = StringIO()
                with redirect_stderr(output), self.assertRaises(SystemExit):
                    self.supersede(0)
                self.assertIn("supersession implementation endpoint disagrees with its receipt",
                              output.getvalue())
                self.assertEqual(self.ledger.read_bytes(), before)

    def test_short_commit_must_resolve_to_the_endpoint_in_the_run_worktree(self):
        endpoint = self.old[0]
        names = self.module.receipt_names_commit
        for recorded in (endpoint, endpoint[:39], endpoint[:9], endpoint[:7]):
            with self.subTest(recorded=recorded):
                self.assertTrue(names(str(self.repo), recorded, endpoint))
        self.assertFalse(names(str(self.repo), endpoint[:6], endpoint))
        with mock.patch.object(self.module, "bounded_run", return_value=(128, b"")):
            self.assertFalse(names(str(self.repo), endpoint[:9], endpoint))
        with tempfile.TemporaryDirectory(prefix="empty-") as other:
            subprocess.run(["git", "init", "-q", other], check=True)
            self.assertFalse(names(other, endpoint[:9], endpoint))

    def test_short_audit_round_fixes_commits_are_accepted_through_supersession(self):
        """Issue 2059: round receipts held `fixes_commit` as given, beside a short implement commit."""
        short = [self.old[1][:9], self.old[2][:9]]
        self.write_run(self.old[0][:9], short)
        for number in range(3):
            self.supersede(number)
        state = self.module.load_state(str(self.repo))
        step = state["steps"][0]
        entries = self.module.ledger_entries(str(self.repo))
        self.assertEqual([row["fixes_commit"] for row in step["audit"]["rounds"]], short)
        self.assertEqual([row["data"]["fixes_commit"] for row in entries
                          if row["event"] == "audit-round"], short)
        self.assertEqual([row["old"] for row in step["supersessions"]], self.old)
        with mock.patch.dict(os.environ, self.env):
            self.module.verify_supersessions(str(self.repo), state, entries)
        self.module.require_effective_push_range(str(self.repo), step, entries, self.new)
        self.assertTrue(self.ledger.read_bytes().startswith(self.original_ledger))

    def test_audit_round_fixes_forms_that_do_not_name_the_endpoint_refuse(self):
        for label, recorded in (
            ("another receipt's prefix", self.old[1][:9]),
            ("full-length other commit", self.old[1]),
            ("below the seven-character floor", self.old[2][:6]),
            ("uppercase prefix", self.old[2][:9].upper()),
            ("no commit", None),
        ):
            with self.subTest(label):
                self.write_run(self.old[0], [self.old[1], recorded])
                before = self.ledger.read_bytes()
                output = StringIO()
                with redirect_stderr(output), self.assertRaises(SystemExit):
                    self.supersede(0)
                self.assertIn("supersession audit-round endpoint disagrees with its receipt",
                              output.getvalue())
                self.assertEqual(self.ledger.read_bytes(), before)

    def audit_close(self, fixes_ref, verified_fixes):
        """The run's step and ledger rows with one `done:audit` closure appended in memory."""
        step = self.module.load_state(str(self.repo))["steps"][0]
        entries = self.module.ledger_entries(str(self.repo))
        receipt = {"rounds": 2, "clean": True, "no_further_leads": False, "reason": None,
                   "fixes_ref": fixes_ref, "log": "audit/fixture.md", "verified_fixes": verified_fixes}
        step["receipts"]["audit"] = receipt
        entries.append({"event": "done:audit", "data": {"step": 1, **receipt}, "hash": "f" * 64})
        return step, entries

    def test_audit_close_fixes_ref_names_its_endpoint_by_prefix(self):
        endpoint = self.new[0]  # a commit outside the earlier receipts
        sources_of = lambda ref, verified: self.module.receipted_local_commits(
            str(self.repo), *self.audit_close(ref, verified))
        for ref in (endpoint, endpoint[:9]):
            with self.subTest(ref=ref):
                last = sources_of(ref, [endpoint])[-1]
                self.assertEqual((last["old"], last["source_event"]), (endpoint, "done:audit"))
        for label, ref in (
            ("another commit's prefix", self.new[1][:9]),
            ("full-length other commit", self.new[1]),
            ("below the seven-character floor", endpoint[:6]),
            ("uppercase prefix", endpoint[:9].upper()),
            ("no commit", None),
        ):
            with self.subTest(label):
                output = StringIO()
                with redirect_stderr(output), self.assertRaises(SystemExit):
                    sources_of(ref, [endpoint])
                self.assertIn("supersession done:audit endpoint disagrees with its receipt",
                              output.getvalue())
        # A closure with no verified fixes names no endpoint, so its short ref is not compared.
        self.assertEqual(len(sources_of(self.old[2][:9], [])), 3)


if __name__ == "__main__":
    unittest.main()
