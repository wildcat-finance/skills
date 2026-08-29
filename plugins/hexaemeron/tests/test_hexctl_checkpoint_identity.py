"""Focused guards for immutable Fiat run and checkpoint identities."""

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


HERE = Path(__file__).resolve().parent
HEXCTL = HERE.parent / "skills" / "fiat" / "scripts" / "hexctl.py"
IDENTITY_FIXTURE = HERE / "fixtures" / "checkpoint-identity-v1.json"
OBSERVATION_FIXTURE = (
    HERE.parents[2]
    / "tests"
    / "fixtures"
    / "run-observation"
    / "valid"
    / "success.jsonl"
)

sys.path.insert(0, str(HERE))
from test_hexctl import HexctlCase, hexctl_module  # noqa: E402


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

    def test_checkpoint_identity_command_is_registered(self):
        result = self.run_ctl("checkpoint", "identity", expected=2)
        self.assertNotIn("invalid choice", result.stderr)

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

    def test_full_tag_object_sha_refuses_before_recording(self):
        git(
            self.repo,
            "-c",
            "tag.gpgSign=false",
            "tag",
            "-a",
            "pinned",
            "-m",
            "pinned",
        )
        tag_object = git(self.repo, "rev-parse", "refs/tags/pinned")
        result = self.run_ctl(
            "init",
            "--topic",
            "immutable anchor",
            "--base",
            tag_object,
            expected=2,
        )
        self.assertIn("commit object", result.stderr)
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


class HexctlSemanticCheckpointIdentityTests(HexctlCase):
    @staticmethod
    def golden_capture():
        fixture = json.loads(IDENTITY_FIXTURE.read_text(encoding="utf-8"))
        golden = fixture["golden"]
        state_bytes = bytes.fromhex("".join(golden["state_bytes_hex"]))
        ledger_bytes = bytes.fromhex("".join(golden["ledger_bytes_hex"]))
        return fixture, state_bytes, ledger_bytes, copy.deepcopy(golden["evidence"])

    @staticmethod
    def parsed_ledger(ledger_bytes):
        return [json.loads(line) for line in ledger_bytes.splitlines() if line]

    @staticmethod
    def rebuild_capture(module, state, entries):
        anchor = state["receipts"].get("run_anchor")
        if anchor is None:
            entries[0]["data"].pop("run_anchor_sha256", None)
        else:
            entries[0]["data"]["run_anchor_sha256"] = hashlib.sha256(
                module.canonical(anchor).encode("utf-8")
            ).hexdigest()
        entries[-1]["state"] = module.state_fingerprint(state)
        previous = "genesis"
        for entry in entries:
            entry["prev"] = previous
            body = {
                key: entry[key]
                for key in ("ts", "event", "data", "prev", "state")
            }
            entry["hash"] = hashlib.sha256(
                module.canonical(body).encode("utf-8")
            ).hexdigest()
            previous = entry["hash"]
        state_bytes = module.canonical(state).encode("utf-8") + b"\n"
        ledger_bytes = b"".join(
            json.dumps(entry, sort_keys=True).encode("utf-8") + b"\n"
            for entry in entries
        )
        return state_bytes, ledger_bytes

    def rewrite_live_capture(self, mutate):
        module = hexctl_module()
        state_path = Path(self.target) / ".hexaemeron" / "state.json"
        ledger_path = Path(self.target) / ".hexaemeron" / "ledger.jsonl"
        state = json.loads(state_path.read_bytes())
        entries = self.parsed_ledger(ledger_path.read_bytes())
        mutate(state, entries)
        state_bytes, ledger_bytes = self.rebuild_capture(module, state, entries)
        state_path.write_bytes(state_bytes)
        ledger_path.write_bytes(ledger_bytes)

    @staticmethod
    def assert_helper_refuses(test, module, state_bytes, ledger_bytes, evidence):
        error = StringIO()
        with redirect_stderr(error), test.assertRaises(SystemExit) as stopped:
            module.checkpoint_identity_from_captured(
                state_bytes, ledger_bytes, evidence
            )
        test.assertEqual(2, stopped.exception.code)
        return error.getvalue()

    def to_post_push(self):
        self.git(
            "remote",
            "add",
            "origin",
            "https://github.com/wildcat-finance/example.git",
        )
        self.to_steps(titles=("First", "Second"))
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.finish_step(1)

    def state_ledger_bytes(self):
        root = Path(self.target) / ".hexaemeron"
        return root.joinpath("state.json").read_bytes(), root.joinpath(
            "ledger.jsonl"
        ).read_bytes()

    def identity(self, *, expect=0, environment=None):
        result = subprocess.run(
            [
                sys.executable,
                str(HEXCTL),
                "--dir",
                self.target,
                "checkpoint",
                "identity",
            ],
            cwd=self.target,
            capture_output=True,
            text=True,
            env=environment or self.direct_environment(),
        )
        self.assertEqual(expect, result.returncode, result.stderr)
        return result

    def direct_environment(self):
        environment = dict(self.env)
        environment["FAKE_GIT_REFS"] = json.dumps(self.fake_refs)
        environment["FAKE_GIT_PARENTS"] = json.dumps(self.fake_parents)
        environment["FAKE_GH_PRS"] = json.dumps(self.fake_prs)
        return environment

    def test_identity_is_read_only_and_byte_stable(self):
        self.to_post_push()
        before = self.state_ledger_bytes()
        first = self.identity()
        second = self.identity()
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(before, self.state_ledger_bytes())
        self.assertEqual("", first.stderr)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["schema"], "fiat-checkpoint-identity-result/v1")
        self.assertEqual(payload["identity"]["boundary"]["kind"], "post-push")
        self.assertRegex(payload["snapshot_id"], r"^[0-9a-f]{64}$")

    def test_stable_branch_tip_movement_is_not_semantic_identity(self):
        self.to_post_push()
        first = json.loads(self.identity().stdout)
        state = self.state()
        self.fake_refs[state["run_branch"]] = "e" * 40
        self.fake_refs[self.step_branch(1, state)] = "d" * 40
        second = json.loads(self.identity().stdout)
        self.assertEqual(first, second)

    def test_active_audit_verdict_and_unavailable_binding_are_explicit(self):
        self.git(
            "remote",
            "add",
            "origin",
            "https://github.com/wildcat-finance/example.git",
        )
        self.to_steps(titles=("First", "Second"))
        self.run_ctl(
            "observe",
            "--capture-status",
            "unavailable",
            "--redaction-status",
            "unknown",
            "--reason-code",
            "observer-unavailable",
        )
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.run_ctl(
            "done",
            "implement",
            "--branch",
            self.step_branch(1),
            "--commit",
            "abc1",
        )
        self.record_legacy_config("audit.max_rounds", 1)
        self.run_ctl(
            "audit-round",
            "--findings",
            "1",
            "--phylax-exit",
            "0",
            "--ephoros-exit",
            "0",
            "--hypomnema-exit",
            "0",
        )
        payload = json.loads(self.identity().stdout)["identity"]
        self.assertEqual("audit-verdict", payload["boundary"]["kind"])
        self.assertEqual(1, payload["boundary"]["step"])
        self.assertEqual("bound", payload["evidence"]["observation_status"])
        self.assertEqual(1, payload["evidence"]["observation_bindings"])

    def test_accepted_observation_prefix_is_reverified_and_bound(self):
        self.git(
            "remote",
            "add",
            "origin",
            "https://github.com/wildcat-finance/example.git",
        )
        self.to_steps(titles=("First", "Second"))
        state = self.state()
        events = [
            json.loads(line)
            for line in OBSERVATION_FIXTURE.read_text(encoding="utf-8").splitlines()
        ][:-1]
        for event in events:
            event["run_id"] = hexctl_module().controller_run_id(state)
            event["schema_id"] = "promise-machine-run-observation/v1"
        relative = Path(".hexaemeron") / "observations" / "identity.jsonl"
        artifact = Path(self.target) / relative
        artifact.parent.mkdir(parents=True)
        artifact.write_text(
            "".join(
                json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
                for event in events
            ),
            encoding="utf-8",
        )
        self.run_ctl(
            "observe",
            "--artifact",
            relative.as_posix(),
            "--capture-status",
            "accepted",
            "--redaction-status",
            "passed",
        )
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.finish_step(1)
        payload = json.loads(self.identity().stdout)["identity"]["evidence"]
        self.assertEqual("bound", payload["observation_status"])
        self.assertEqual(1, payload["observation_bindings"])

    def test_source_and_ref_mutation_refuse_before_stdout(self):
        self.to_post_push()
        before = self.state_ledger_bytes()
        environment = self.direct_environment()

        for surface in ("source", "observation", "git"):
            with self.subTest(surface=surface):
                module = hexctl_module()
                output = StringIO()
                error = StringIO()
                if surface == "source":
                    original = module._checkpoint_identity_source_evidence
                    calls = 0

                    def moving(*args):
                        nonlocal calls
                        calls += 1
                        evidence, token = original(*args)
                        if calls == 2:
                            token = (*token, ("changed", "0" * 64, "changed"))
                        return evidence, token

                    patcher = mock.patch.object(
                        module, "_checkpoint_identity_source_evidence", moving
                    )
                elif surface == "observation":
                    original = module._checkpoint_identity_verify_observations
                    calls = 0

                    def moving(*args):
                        nonlocal calls
                        calls += 1
                        token = original(*args)
                        if calls == 2:
                            token = (*token, ("changed", 1, "0" * 64))
                        return token

                    patcher = mock.patch.object(
                        module,
                        "_checkpoint_identity_verify_observations",
                        moving,
                    )
                else:
                    original = module._checkpoint_identity_git_evidence
                    calls = 0

                    def moving(*args):
                        nonlocal calls
                        calls += 1
                        evidence = original(*args)
                        if calls == 2:
                            evidence = copy.deepcopy(evidence)
                            key = next(
                                name
                                for name in evidence["refs"]
                                if not re.fullmatch(r"[0-9a-f]{40}", name)
                            )
                            evidence["refs"][key] = "e" * 40
                        return evidence

                    patcher = mock.patch.object(
                        module, "_checkpoint_identity_git_evidence", moving
                    )

                with mock.patch.dict(os.environ, environment, clear=True), patcher:
                    with redirect_stdout(output), redirect_stderr(error):
                        with self.assertRaises(SystemExit) as stopped:
                            module.cmd_checkpoint_identity(
                                SimpleNamespace(dir=self.target)
                            )
                self.assertEqual(2, stopped.exception.code)
                self.assertEqual("", output.getvalue())
                self.assertIn("changed before output", error.getvalue())
                self.assertEqual(before, self.state_ledger_bytes())

    def test_golden_identity_has_exact_closed_bytes_and_domain(self):
        fixture, state_bytes, ledger_bytes, evidence = self.golden_capture()
        module = hexctl_module()
        with mock.patch(
            "builtins.open", side_effect=AssertionError("pure helper opened a path")
        ), mock.patch.object(
            module,
            "bounded_git",
            side_effect=AssertionError("pure helper invoked Git"),
        ):
            result = module.checkpoint_identity_from_captured(
                state_bytes, ledger_bytes, evidence
            )
        self.assertEqual(fixture["golden"]["result"], result)
        identity_bytes = module.canonical(result["identity"]).encode("utf-8")
        self.assertEqual(
            bytes.fromhex("".join(fixture["golden"]["identity_bytes_hex"])),
            identity_bytes,
        )
        self.assertEqual(
            hashlib.sha256(module.CHECKPOINT_IDENTITY_DOMAIN + identity_bytes).hexdigest(),
            result["snapshot_id"],
        )
        self.assertNotEqual(
            hashlib.sha256(b"another-domain\0" + identity_bytes).hexdigest(),
            result["snapshot_id"],
        )
        self.assertEqual(
            {"schema", "identity", "snapshot_id"}, set(result)
        )
        self.assertEqual(
            {"schema", "run", "boundary", "evidence"}, set(result["identity"])
        )
        self.assertEqual(
            {"kind", "step", "working_commit_sha"},
            set(result["identity"]["boundary"]),
        )
        self.assertEqual(
            {
                "ledger_entries",
                "ledger_sha256",
                "ledger_tail",
                "observation_bindings",
                "observation_sha256",
                "observation_status",
                "policy_sha256",
                "run_anchor_sha256",
                "runbook_sha256",
                "state_fingerprint",
                "study_sha256",
            },
            set(result["identity"]["evidence"]),
        )

    def test_hostile_bytes_types_caps_and_drift_refuse(self):
        fixture, state_bytes, ledger_bytes, evidence = self.golden_capture()
        module = hexctl_module()
        hostile = fixture["hostile"]

        duplicate_state = bytes.fromhex(hostile["duplicate_state_bytes_hex"])
        error = self.assert_helper_refuses(
            self, module, duplicate_state, ledger_bytes, evidence
        )
        self.assertIn("strict UTF-8 JSON", error)

        duplicate_ledger = bytes.fromhex(
            hostile["duplicate_ledger_bytes_hex"]
        )
        error = self.assert_helper_refuses(
            self, module, state_bytes, duplicate_ledger, evidence
        )
        self.assertIn("strict UTF-8 JSON", error)

        wrong_type = copy.deepcopy(evidence)
        wrong_type["observations"]["bindings"] = hostile[
            "wrong_evidence_bindings_type"
        ]
        error = self.assert_helper_refuses(
            self, module, state_bytes, ledger_bytes, wrong_type
        )
        self.assertIn("observation evidence", error)

        bool_count = copy.deepcopy(evidence)
        bool_count["observations"]["bindings"] = False
        error = self.assert_helper_refuses(
            self, module, state_bytes, ledger_bytes, bool_count
        )
        self.assertIn("observation evidence", error)

        for name, patch_name, value in (
            ("state", "CHECKPOINT_FILE_BYTES_MAX", len(state_bytes) - 1),
            ("entries", "CHECKPOINT_IDENTITY_LEDGER_ENTRIES_MAX", 1),
        ):
            with self.subTest(cap=name), mock.patch.object(module, patch_name, value):
                error = self.assert_helper_refuses(
                    self, module, state_bytes, ledger_bytes, evidence
                )
                self.assertIn("ceiling", error)

        drifted_entries = self.parsed_ledger(ledger_bytes)
        drifted_entries[-1]["hash"] = "0" * 64
        drifted = b"".join(
            json.dumps(entry, sort_keys=True).encode("utf-8") + b"\n"
            for entry in drifted_entries
        )
        error = self.assert_helper_refuses(
            self, module, state_bytes, drifted, evidence
        )
        self.assertIn("chain", error)

        no_newline = ledger_bytes.rstrip(b"\n")
        error = self.assert_helper_refuses(
            self, module, state_bytes, no_newline, evidence
        )
        self.assertIn("appendable exact prefix", error)

        state = json.loads(state_bytes)
        entries = self.parsed_ledger(ledger_bytes)
        state["config"]["skills"]["security"] = [{}]
        malformed_state, malformed_ledger = self.rebuild_capture(
            module, state, entries
        )
        error = self.assert_helper_refuses(
            self, module, malformed_state, malformed_ledger, evidence
        )
        self.assertIn("security policy", error)

        state = json.loads(state_bytes)
        entries = self.parsed_ledger(ledger_bytes)
        entries[-1]["data"]["step"] = True
        malformed_state, malformed_ledger = self.rebuild_capture(
            module, state, entries
        )
        error = self.assert_helper_refuses(
            self, module, malformed_state, malformed_ledger, evidence
        )
        self.assertIn("positive step number", error)

        state = json.loads(state_bytes)
        entries = self.parsed_ledger(ledger_bytes)
        state["receipts"].pop("run_anchor")
        missing_state, missing_ledger = self.rebuild_capture(module, state, entries)
        error = self.assert_helper_refuses(
            self, module, missing_state, missing_ledger, evidence
        )
        self.assertIn("init-owned run anchor", error)

        state = json.loads(state_bytes)
        entries = self.parsed_ledger(ledger_bytes)
        state["receipts"]["run_anchor"]["run_id"] = "fiat-" + "f" * 64
        mismatch_state, mismatch_ledger = self.rebuild_capture(
            module, state, entries
        )
        error = self.assert_helper_refuses(
            self, module, mismatch_state, mismatch_ledger, evidence
        )
        self.assertIn("does not match captured state", error)

    def test_carrier_fields_do_not_change_snapshot_id(self):
        fixture, state_bytes, ledger_bytes, evidence = self.golden_capture()
        module = hexctl_module()
        baseline = module.checkpoint_identity_from_captured(
            state_bytes, ledger_bytes, evidence
        )
        changed_refs = copy.deepcopy(evidence)
        changed_refs["git"]["refs"]["fiat/560-golden"] = "e" * 40
        moved_tip = module.checkpoint_identity_from_captured(
            state_bytes, ledger_bytes, changed_refs
        )
        self.assertEqual(baseline, moved_tip)

        identity_text = module.canonical(baseline["identity"])
        carrier_keys = set()
        for carrier in fixture["carrier_variants"]:
            carrier_keys.update(carrier)
            for key in carrier:
                self.assertNotIn(key, identity_text)
        self.assertTrue(
            carrier_keys.isdisjoint(
                baseline["identity"] | baseline["identity"]["evidence"]
            )
        )
        self.assertNotIn("/outside/", identity_text)

        state = json.loads(state_bytes)
        entries = self.parsed_ledger(ledger_bytes)
        state["config"]["git"]["origin"] = "/tmp/ghp_SUPER_SECRET/origin"
        state["config"]["git"]["worktree"] = "/tmp/ghp_SUPER_SECRET/worktree"
        state["config"]["audit"]["log_path"] = "ghp_SUPER_SECRET.md"
        secret_state, secret_ledger = self.rebuild_capture(module, state, entries)
        secret_result = module.checkpoint_identity_from_captured(
            secret_state, secret_ledger, evidence
        )
        self.assertNotIn(
            "ghp_SUPER_SECRET", module.canonical(secret_result["identity"])
        )

    def test_semantic_inputs_each_change_snapshot_id(self):
        _, state_bytes, ledger_bytes, evidence = self.golden_capture()
        module = hexctl_module()
        baseline = module.checkpoint_identity_from_captured(
            state_bytes, ledger_bytes, evidence
        )["snapshot_id"]

        def changed_snapshot(change):
            state = json.loads(state_bytes)
            entries = self.parsed_ledger(ledger_bytes)
            current_evidence = copy.deepcopy(evidence)
            change(state, entries, current_evidence)
            candidate_state, candidate_ledger = self.rebuild_capture(
                module, state, entries
            )
            return module.checkpoint_identity_from_captured(
                candidate_state, candidate_ledger, current_evidence
            )["snapshot_id"]

        def change_policy(state, _entries, _evidence):
            state["config"]["audit"]["fold"] = True

        def change_study(state, _entries, current_evidence):
            state["receipts"]["study"]["sha256"] = "b" * 64
            current_evidence["sources"]["study_sha256"] = "b" * 64

        def change_working(state, entries, current_evidence):
            working = "c" * 40
            state["steps"][0]["receipts"]["push"]["head_commit"] = working
            state["steps"][0]["receipts"]["push"]["verified_commits"] = [
                working
            ]
            entries[-1]["data"]["head_commit"] = working
            entries[-1]["data"]["verified_commits"] = [working]
            current_evidence["git"]["working_commit_sha"] = working

        def change_base(state, _entries, current_evidence):
            prior = state["base"]
            replacement = "d" * 40
            state["base"] = replacement
            controller = state["receipts"]["run_anchor"]["controller"]
            state["receipts"]["run_anchor"] = module.build_run_anchor(
                state, "wildcat-finance/skills", controller
            )
            refs = current_evidence["git"]["refs"]
            refs[replacement] = replacement
            del refs[prior]
            current_evidence["git"]["initial_base_sha"] = replacement

        def bind_unavailable(state, entries, current_evidence):
            selected = entries[0]
            binding = {
                "schema": "fiat-run-observation-binding/v1",
                "observation_contract": "promise-machine-run-observation/v1",
                "controller_run_id": module.controller_run_id(state),
                "recorded_at": "2026-08-29T00:30:00+00:00",
                "capture_status": "unavailable",
                "redaction_status": "unknown",
                "receipt": {
                    "line": 1,
                    "event": selected["event"],
                    "hash": selected["hash"],
                    "state": selected["state"],
                },
                "validation_status": "unknown",
                "reason_code": "observer-unavailable",
            }
            state["receipts"]["run_observations"] = [binding]
            digest = hashlib.sha256(
                module.canonical(binding).encode("utf-8")
            ).hexdigest()
            entries.insert(
                1,
                {
                    "ts": "2026-08-29T00:30:00+00:00",
                    "event": "record:run-observation",
                    "data": {
                        "binding_sha256": digest,
                        "capture_status": "unavailable",
                        "receipt_hash": selected["hash"],
                    },
                    "prev": selected["hash"],
                    "state": "7" * 64,
                    "hash": "0" * 64,
                },
            )
            current_evidence["observations"] = {
                "status": "bound",
                "bindings": 1,
                "sha256": hashlib.sha256(
                    module.canonical([binding]).encode("utf-8")
                ).hexdigest(),
            }

        for name, change in (
            ("policy", change_policy),
            ("study", change_study),
            ("working_commit", change_working),
            ("immutable_base", change_base),
            ("observations", bind_unavailable),
        ):
            with self.subTest(semantic=name):
                self.assertNotEqual(baseline, changed_snapshot(change))

    def test_identity_refuses_legacy_symbolic_base(self):
        self.to_post_push()

        def make_legacy(state, _entries):
            state["base"] = "main"
            state["receipts"].pop("run_anchor")

        self.rewrite_live_capture(make_legacy)
        before = self.state_ledger_bytes()
        result = self.identity(expect=2)
        self.assertEqual("", result.stdout)
        self.assertIn("immutable full-SHA run base", result.stderr)
        self.assertEqual(before, self.state_ledger_bytes())

    def test_identity_refuses_unreceipted_and_non_descendant_working_commits(self):
        self.to_post_push()
        before = self.state_ledger_bytes()
        environment = self.direct_environment()
        environment["FAKE_GIT_MODE"] = "not-ancestor"
        environment["FAKE_GIT_NOT_ANCESTOR"] = self.state()["base"]
        result = self.identity(expect=2, environment=environment)
        self.assertEqual("", result.stdout)
        self.assertIn("does not descend", result.stderr)
        self.assertEqual(before, self.state_ledger_bytes())

        def remove_receipt(state, entries):
            state["steps"][0]["receipts"]["push"]["verified_commits"] = []
            entries[-1]["data"]["verified_commits"] = []

        self.rewrite_live_capture(remove_receipt)
        before = self.state_ledger_bytes()
        result = self.identity(expect=2)
        self.assertEqual("", result.stdout)
        self.assertIn("post-push receipt is incomplete", result.stderr)
        self.assertEqual(before, self.state_ledger_bytes())

    def test_identity_refuses_a_non_checkpoint_phase_without_writes(self):
        self.git(
            "remote",
            "add",
            "origin",
            "https://github.com/wildcat-finance/example.git",
        )
        self.to_steps(titles=("First",))
        before = self.state_ledger_bytes()
        result = self.identity(expect=2)
        self.assertEqual("", result.stdout)
        self.assertIn("allowed only", result.stderr)
        self.assertEqual(before, self.state_ledger_bytes())


if __name__ == "__main__":
    unittest.main()
