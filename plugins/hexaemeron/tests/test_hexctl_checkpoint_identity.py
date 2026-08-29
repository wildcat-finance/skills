"""Focused guards for immutable Fiat run and checkpoint identities."""

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
HEXCTL = HERE.parent / "skills" / "fiat" / "scripts" / "hexctl.py"


def load_hexctl():
    spec = importlib.util.spec_from_file_location("hexctl_checkpoint_identity", HEXCTL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "commit.gpgsign=false", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class HexctlCheckpointIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "initial")

    def tearDown(self):
        self.temporary.cleanup()

    def run_ctl(self, *args: str, expected: int = 0):
        result = subprocess.run(
            [os.sys.executable, str(HEXCTL), "--dir", str(self.repo), *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, expected, (result.stdout, result.stderr))
        return result

    def add_origin(self, repository: str = "wildcat-finance/skills"):
        git(
            self.repo,
            "remote",
            "add",
            "origin",
            f"https://github.com/{repository}.git",
        )

    def init(self, *extra: str):
        self.run_ctl("init", "--topic", "immutable anchor", *extra)
        breadcrumb = self.repo / ".hexaemeron" / "worktree"
        return Path(breadcrumb.read_text(encoding="utf-8").strip())

    @staticmethod
    def state(worktree: Path):
        return json.loads(
            (worktree / ".hexaemeron" / "state.json").read_text(encoding="utf-8")
        )

    @staticmethod
    def ledger(worktree: Path):
        return [
            json.loads(line)
            for line in (worktree / ".hexaemeron" / "ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line
        ]

    def assert_no_partial_run(self):
        state_root = self.repo / ".hexaemeron"
        for name in ("state.json", "ledger.jsonl", "worktree"):
            self.assertFalse((state_root / name).exists(), name)
        self.assertFalse((self.repo / "tmp" / "fiat" / "fiat-immutable-anchor").exists())

    def test_init_named_base_is_resolved_once_before_worktree_add(self):
        module = load_hexctl()
        starting_commit = git(self.repo, "rev-parse", "main")
        original_bounded_git = module.bounded_git
        moved = False

        def move_base_before_add(base_dir, argv, refusal=None):
            nonlocal moved
            if argv[:2] == ["worktree", "add"] and not moved:
                moved = True
                git(self.repo, "commit", "-q", "--allow-empty", "-m", "move main")
            return original_bounded_git(base_dir, argv, refusal)

        args = argparse.Namespace(
            dir=str(self.repo),
            topic="immutable anchor",
            base="main",
            task_issue=None,
            run_branch=None,
            frontier=None,
            controller_currency_waiver=None,
        )
        current = {
            "ledger_version": "fiat-v5.35.1",
            "route": "in-repo-source",
            "pin": None,
            "observed_head": None,
            "verdict": "current",
            "warning": None,
        }
        with mock.patch.object(module, "bounded_git", move_base_before_add), mock.patch.object(
            module, "observe_controller_currency", return_value=current
        ):
            module.cmd_init(args)

        self.assertTrue(moved)
        breadcrumb = self.repo / ".hexaemeron" / "worktree"
        worktree = Path(breadcrumb.read_text(encoding="utf-8").strip())
        state = json.loads(
            (worktree / ".hexaemeron" / "state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(state["base"], starting_commit)
        self.assertEqual(state["config"]["git"]["base"], "main")
        self.assertEqual(git(worktree, "rev-parse", "HEAD"), starting_commit)
        self.assertEqual(
            state["receipts"]["run_anchor"]["initial_base_sha"],
            starting_commit,
        )

    def test_init_records_closed_anchor_and_initial_ledger_digest(self):
        self.add_origin()
        issue = "https://github.com/wildcat-finance/skills/issues/560"
        worktree = self.init("--task-issue", issue)
        state = self.state(worktree)
        anchor = state["receipts"]["run_anchor"]
        self.assertEqual(
            set(anchor),
            {
                "schema",
                "controller",
                "initial_base_sha",
                "integration_branch",
                "repository",
                "run_branch",
                "run_id",
                "task",
            },
        )
        self.assertEqual(anchor["schema"], "fiat-run-anchor/v1")
        self.assertEqual(anchor["repository"], "wildcat-finance/skills")
        self.assertEqual(anchor["task"], {"kind": "github-issue", "number": 560})
        self.assertEqual(anchor["initial_base_sha"], state["base"])
        self.assertEqual(anchor["integration_branch"], state["config"]["git"]["base"])
        self.assertEqual(anchor["run_branch"], state["run_branch"])
        self.assertEqual(anchor["run_id"], load_hexctl().controller_run_id(state))
        self.assertEqual(
            anchor["controller"],
            {
                "name": state["controller"],
                "state_version": state["version"],
                "version": state["receipts"]["controller_currency"]["ledger_version"],
            },
        )
        expected_digest = hashlib.sha256(
            load_hexctl().canonical(anchor).encode("utf-8")
        ).hexdigest()
        self.assertEqual(
            self.ledger(worktree)[0]["data"]["run_anchor_sha256"], expected_digest
        )
        verified = subprocess.run(
            [os.sys.executable, str(HEXCTL), "--dir", str(worktree), "verify"],
            cwd=worktree,
            capture_output=True,
            text=True,
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)

    def test_commit_input_keeps_the_configured_integration_branch(self):
        starting_commit = git(self.repo, "rev-parse", "HEAD")
        worktree = self.init("--base", starting_commit)
        state = self.state(worktree)
        self.assertEqual(state["base"], starting_commit)
        self.assertEqual(state["config"]["git"]["base"], "main")
        self.assertEqual(
            state["receipts"]["run_anchor"]["integration_branch"], "main"
        )

    def test_status_keeps_the_named_integration_branch_visible(self):
        worktree = self.init()
        state = self.state(worktree)
        result = subprocess.run(
            [os.sys.executable, str(HEXCTL), "--dir", str(worktree), "status"],
            cwd=worktree,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"base:  {state['base']}", result.stdout)
        self.assertIn(
            f"run:   {state['run_branch']} -> {state['config']['git']['base']}",
            result.stdout,
        )
        self.assertNotIn(
            f"run:   {state['run_branch']} -> {state['base']}",
            result.stdout,
        )

    def test_malformed_and_unsafe_starting_refs_leave_no_partial_run(self):
        for starting_ref in ("../main", "missing"):
            with self.subTest(starting_ref=starting_ref):
                result = self.run_ctl(
                    "init",
                    "--topic",
                    "immutable anchor",
                    "--base",
                    starting_ref,
                    expected=2,
                )
                self.assertIn("starting base" if starting_ref == "missing" else "branch", result.stderr)
                self.assert_no_partial_run()

    def test_task_repository_substitution_refuses_before_recording(self):
        self.add_origin("wildcat-finance/skills")
        result = self.run_ctl(
            "init",
            "--topic",
            "immutable anchor",
            "--task-issue",
            "https://github.com/elsewhere/skills/issues/560",
            expected=2,
        )
        self.assertIn("task issue repository", result.stderr)
        self.assert_no_partial_run()

    def test_ambiguous_origin_refuses_before_recording(self):
        self.add_origin()
        git(
            self.repo,
            "config",
            "--add",
            "remote.origin.url",
            "https://github.com/elsewhere/skills.git",
        )
        result = self.run_ctl(
            "init",
            "--topic",
            "immutable anchor",
            expected=2,
        )
        self.assertIn("one repository", result.stderr)
        self.assert_no_partial_run()

    def test_origin_substitution_and_anchor_mismatch_refuse_verification(self):
        self.add_origin()
        worktree = self.init(
            "--task-issue", "https://github.com/wildcat-finance/skills/issues/560"
        )
        git(self.repo, "remote", "set-url", "origin", "https://github.com/elsewhere/skills.git")
        origin_changed = subprocess.run(
            [os.sys.executable, str(HEXCTL), "--dir", str(worktree), "verify"],
            cwd=worktree,
            capture_output=True,
            text=True,
        )
        self.assertEqual(origin_changed.returncode, 1)
        self.assertIn("target origin", origin_changed.stderr)

        git(self.repo, "remote", "set-url", "origin", "https://github.com/wildcat-finance/skills.git")
        module = load_hexctl()
        state = self.state(worktree)
        state["receipts"]["run_anchor"]["initial_base_sha"] = "f" * 40
        module.commit(worktree, state, "fixture:anchor-mismatch", {})
        anchor_changed = subprocess.run(
            [os.sys.executable, str(HEXCTL), "--dir", str(worktree), "verify"],
            cwd=worktree,
            capture_output=True,
            text=True,
        )
        self.assertEqual(anchor_changed.returncode, 1)
        self.assertIn("run anchor", anchor_changed.stderr)

    def test_malformed_pull_request_head_refuses_after_integration_branch_split(self):
        module = load_hexctl()
        url = "https://github.com/wildcat-finance/skills/pull/1"
        payload = {
            "user": {"login": "dave"},
            "body": "",
            "html_url": url,
            "head": None,
            "base": {"ref": "main"},
            "merged": False,
            "merge_commit_sha": None,
        }
        error = StringIO()
        with mock.patch.object(
            module, "github_repository", return_value="wildcat-finance/skills"
        ), mock.patch.object(
            module, "github_rest", return_value=payload
        ), redirect_stderr(error):
            with self.assertRaises(SystemExit) as raised:
                module.inspect_pull_request(
                    str(self.repo),
                    url,
                    expected_head="fiat/run",
                    expected_base="main",
                    expected_head_sha="a" * 40,
                    expected_merge_sha=None,
                )
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("no full head SHA", error.getvalue())

    def test_legacy_anchor_absence_is_accepted_but_new_anchor_cannot_be_rebound(self):
        worktree = self.init()
        module = load_hexctl()
        state_path = worktree / ".hexaemeron" / "state.json"
        ledger_path = worktree / ".hexaemeron" / "ledger.jsonl"
        state = self.state(worktree)
        state["receipts"].pop("run_anchor")
        entry = self.ledger(worktree)[0]
        entry["data"].pop("run_anchor_sha256")
        entry["state"] = module.state_fingerprint(state)
        entry["hash"] = hashlib.sha256(
            module.canonical(
                {
                    "ts": entry["ts"],
                    "event": entry["event"],
                    "data": entry["data"],
                    "prev": entry["prev"],
                    "state": entry["state"],
                }
            ).encode("utf-8")
        ).hexdigest()
        state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
        ledger_path.write_text(json.dumps(entry, sort_keys=True) + "\n", encoding="utf-8")
        legacy = subprocess.run(
            [os.sys.executable, str(HEXCTL), "--dir", str(worktree), "verify"],
            cwd=worktree,
            capture_output=True,
            text=True,
        )
        self.assertEqual(legacy.returncode, 0, legacy.stderr)

        fresh_repo = Path(self.temporary.name) / "fresh"
        fresh_repo.mkdir()
        git(fresh_repo, "init", "-q", "-b", "main")
        git(fresh_repo, "config", "user.name", "Fixture")
        git(fresh_repo, "config", "user.email", "fixture@example.invalid")
        git(fresh_repo, "commit", "-q", "--allow-empty", "-m", "initial")
        fresh = subprocess.run(
            [
                os.sys.executable,
                str(HEXCTL),
                "--dir",
                str(fresh_repo),
                "init",
                "--topic",
                "fresh anchor",
            ],
            cwd=fresh_repo,
            capture_output=True,
            text=True,
        )
        self.assertEqual(fresh.returncode, 0, fresh.stderr)
        fresh_worktree = Path(
            (fresh_repo / ".hexaemeron" / "worktree").read_text(encoding="utf-8").strip()
        )
        state_before = (fresh_worktree / ".hexaemeron" / "state.json").read_bytes()
        ledger_before = (fresh_worktree / ".hexaemeron" / "ledger.jsonl").read_bytes()
        for command in (
            ("record", "run_anchor", "{}"),
            ("config", "set", "git.base", "release"),
        ):
            with self.subTest(command=command):
                refused = subprocess.run(
                    [os.sys.executable, str(HEXCTL), "--dir", str(fresh_worktree), *command],
                    cwd=fresh_worktree,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(refused.returncode, 2)
                self.assertEqual(
                    (fresh_worktree / ".hexaemeron" / "state.json").read_bytes(),
                    state_before,
                )
                self.assertEqual(
                    (fresh_worktree / ".hexaemeron" / "ledger.jsonl").read_bytes(),
                    ledger_before,
                )


if __name__ == "__main__":
    unittest.main()
