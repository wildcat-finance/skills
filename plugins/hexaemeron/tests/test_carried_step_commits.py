"""A later step's receipted commits carried into a lower step branch refuse.

Issue 1480. ``refuse_rewritten_stack`` admits any moved waiting tip whose
receipted head is still an ancestor, and a later step's branch merged into a
lower step's branch has exactly that shape. ``refuse_carried_step_commits``
reads every unmerged step, the step being merged included, enumerates the
gained range ``<recorded>..<tip>`` of a moved tip once, and refuses when that
range holds a commit another step's push receipt owns. The graph cases use
real Git objects, as the design record's specimens do; the CLI cases drive
``next`` through the delivery harness and prove a refusal leaves
``.hexaemeron/state.json`` and ``.hexaemeron/ledger.jsonl`` byte-identical.

A new module rather than more of ``test_hexctl.py``, which sits at the Promise
Machine's 262144-byte bounded-read ceiling.
"""

from __future__ import annotations

import importlib.util
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

HERE = Path(__file__).resolve().parent
HEXCTL = HERE.parent / "skills" / "fiat" / "scripts" / "hexctl.py"

# ``run_tests.py`` discovers from this directory and already exposes the
# harness. Direct execution needs the same explicit import path.
sys.path.insert(0, str(HERE))
from hexctl_harness import LINTS_CLEAN, SUITE, HexctlCase  # noqa: E402

RUN_BRANCH = "run"
STEP_BRANCHES = ("run-step-1", "run-step-2", "run-step-3")
MISSING_OBJECT = "f" * 40


def hexctl_module():
    spec = importlib.util.spec_from_file_location("hexctl_carried_step_commits", HEXCTL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_git_executable():
    return shutil.which("git", path=os.defpath)


class GainedRangeOwnershipGraphCases(unittest.TestCase):
    """The eight specimens of the design record, on real Git objects.

    A run branch and three chained step branches with two commits each. Each
    step's push receipt owns its two commits; the run's current step is 1 and
    nothing has merged.
    """

    def setUp(self):
        self.hexctl = hexctl_module()
        self.guard = getattr(self.hexctl, "refuse_carried_step_commits", None)
        self.assertIsNotNone(
            self.guard, "hexctl.py has no refuse_carried_step_commits guard"
        )
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.serial = 0
        self.tips = {}
        self._git("init", "-q", "-b", "main")
        self._git("config", "commit.gpgsign", "false")
        self._commit("base")
        self._git("checkout", "-q", "-b", RUN_BRANCH)
        self.steps = []
        below = RUN_BRANCH
        for number, branch in enumerate(STEP_BRANCHES, start=1):
            self._git("checkout", "-q", "-b", branch, below)
            commits = [self._commit(f"s{number}a"), self._commit(f"s{number}b")]
            self.steps.append({
                "n": number,
                "title": branch,
                "receipts": {"push": {
                    "head_commit": commits[-1],
                    "verified_commits": list(commits),
                    "early_merge": None,
                }},
            })
            below = branch

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *argv, input_text=None):
        executable = native_git_executable()
        self.assertIsNotNone(executable)
        self.serial += 1
        stamp = f"{1000000000 + self.serial} +0000"
        result = subprocess.run(
            [executable, "--no-replace-objects", *argv],
            cwd=self.repo,
            input=input_text,
            capture_output=True,
            text=True,
            env={
                "PATH": os.defpath,
                "LANG": "C",
                "LC_ALL": "C",
                "HOME": str(self.repo),
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_AUTHOR_NAME": "Fixture",
                "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "Fixture",
                "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
                "GIT_AUTHOR_DATE": stamp,
                "GIT_COMMITTER_DATE": stamp,
            },
        )
        if result.returncode:
            self.fail(
                f"git {' '.join(argv)} -> {result.returncode}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
        return result.stdout.strip()

    def _commit(self, name):
        (self.repo / f"{name}.txt").write_text(f"{name}\n", encoding="utf-8")
        self._git("add", f"{name}.txt")
        self._git("commit", "-q", "-m", name)
        return self._git("rev-parse", "HEAD")

    def _merge(self, into, source, message="carry"):
        self._git("checkout", "-q", into)
        self._git("merge", "-q", "--no-ff", "-m", message, source)
        return self._git("rev-parse", "HEAD")

    def _state(self):
        return {"integrate": {"merged": []}, "steps": json.loads(json.dumps(self.steps))}

    def _owned(self, number):
        return self.steps[number - 1]["receipts"]["push"]["verified_commits"]

    def _head(self, number):
        return self.steps[number - 1]["receipts"]["push"]["head_commit"]

    def _tip(self, _dir, branch, *_rest, **_kwargs):
        if branch in self.tips:
            return self.tips[branch]
        return self._git("rev-parse", "--verify", f"refs/heads/{branch}")

    def _run_guard(self, state=None, current_step=1):
        """The refusal text, or ``None`` when every unmerged tip is admitted."""
        module = self.hexctl
        captured = StringIO()
        with mock.patch.object(
            module, "step_branch_name", side_effect=lambda _state, step: step["title"]
        ), mock.patch.object(
            module, "remote_branch_tip", side_effect=self._tip
        ), redirect_stderr(captured):
            try:
                self.guard(str(self.repo), state or self._state(), current_step)
            except SystemExit:
                return captured.getvalue()
        return None

    def assertCarried(self, message, number, branch, recorded, tip, commit, owner):
        self.assertIsNotNone(message, "the carried branch was admitted")
        self.assertIn("gained a commit another step's push receipt owns", message)
        self.assertIn(f"step {number} (", message)
        self.assertIn(f"'{branch}'", message)
        self.assertIn(recorded, message)
        self.assertIn(tip, message)
        self.assertIn(f"first carried commit in rev-list order is {commit}", message)
        self.assertIn(f"owned by step {owner}'s push receipt", message)
        self.assertIn("does not claim which operation moved the branch", message)

    def test_a_whole_carry_into_the_step_being_merged_refuses(self):
        tip = self._merge(STEP_BRANCHES[0], STEP_BRANCHES[2])
        message = self._run_guard()
        self.assertCarried(
            message, 1, STEP_BRANCHES[0], self._head(1), tip, self._head(3), 3
        )
        self.assertIn("the step being merged", message)

    def test_a_whole_carry_into_a_waiting_step_refuses(self):
        tip = self._merge(STEP_BRANCHES[1], STEP_BRANCHES[2])
        message = self._run_guard()
        self.assertCarried(
            message, 2, STEP_BRANCHES[1], self._head(2), tip, self._head(3), 3
        )
        self.assertIn("a waiting step", message)

    def test_a_partial_carry_of_one_non_head_commit_refuses(self):
        first = self._owned(3)[0]
        tip = self._merge(STEP_BRANCHES[0], first, message="partial")
        message = self._run_guard()
        self.assertCarried(message, 1, STEP_BRANCHES[0], self._head(1), tip, first, 3)
        self.assertNotIn(self._head(3), message)

    def test_an_honest_extension_of_a_waiting_step_is_admitted(self):
        self._git("checkout", "-q", STEP_BRANCHES[1])
        fix = self._commit("fix")
        self.assertNotEqual(fix, self._head(2))
        self.assertIsNone(
            self._run_guard(),
            "a waiting tip that gained only a commit nobody owns was refused",
        )

    def test_a_healthy_stack_is_admitted_without_a_range_query(self):
        with mock.patch.object(
            self.hexctl,
            "bounded_probe",
            side_effect=AssertionError("an equal tip started a native child"),
        ):
            self.assertIsNone(self._run_guard())

    def test_an_adopted_early_merge_is_admitted(self):
        merge = self._merge(STEP_BRANCHES[1], STEP_BRANCHES[2], message="early")
        state = self._state()
        state["steps"][2]["receipts"]["push"]["early_merge"] = {
            "merge_commit": merge,
            "reachable_from": STEP_BRANCHES[1],
            "base_tip": merge,
            "github_verified": [merge],
        }
        self.assertIsNone(
            self._run_guard(state),
            "an adopted step's commits inside the branch its receipt names were refused",
        )

    def test_a_missing_object_refuses_as_unknown_naming_the_pair(self):
        self.tips[STEP_BRANCHES[1]] = MISSING_OBJECT
        message = self._run_guard()
        self.assertIsNotNone(message)
        self.assertIn("unknown gained range", message)
        self.assertIn(f"step 2 (a waiting step, '{STEP_BRANCHES[1]}')", message)
        self.assertIn(f"{self._head(2)}..{MISSING_OBJECT}", message)
        self.assertIn("unknown rather than clean", message)
        self.assertIn("nothing was fetched and no cause is claimed", message)
        self.assertNotIn("gained a commit another step's push receipt owns", message)

    def test_a_legacy_head_only_receipt_owns_exactly_its_head(self):
        state = self._state()
        del state["steps"][2]["receipts"]["push"]["verified_commits"]
        tip = self._merge(STEP_BRANCHES[1], STEP_BRANCHES[2])
        message = self._run_guard(state)
        self.assertCarried(
            message, 2, STEP_BRANCHES[1], self._head(2), tip, self._head(3), 3
        )
        # The same legacy receipt owns nothing but its head, so a carry of the
        # non-head commit alone reads as an unowned extension.
        self._git("checkout", "-q", STEP_BRANCHES[1])
        self._git("reset", "-q", "--hard", self._head(2))
        self._merge(STEP_BRANCHES[1], self._owned(3)[0], message="partial")
        self.assertIsNone(self._run_guard(state))

    def test_start_timeout_cap_status_overflow_and_malformed_lines_are_unknown(self):
        module = self.hexctl
        tip = self._merge(STEP_BRANCHES[1], STEP_BRANCHES[2])
        overflow = "\n".join(format(index, "040x") for index in range(module.GIT_PATHS_MAX + 1))
        outcomes = (
            (None, b"", "start"),
            (None, b"", "timeout"),
            (None, b"ignored", "output-cap"),
            (128, b"ignored", None),
            (0, (overflow + "\n").encode("ascii"), None),
            (0, b"not-a-sha\n", None),
        )
        for outcome in outcomes:
            with self.subTest(outcome=outcome[2] or outcome[0]), mock.patch.object(
                module, "bounded_probe", return_value=outcome
            ):
                message = self._run_guard()
                self.assertIsNotNone(message)
                self.assertIn("unknown gained range", message)
                self.assertIn(f"{self._head(2)}..{tip}", message)
                self.assertNotIn("gained a commit another step's push receipt owns", message)

    def test_the_range_query_is_one_scrubbed_native_child_with_fixed_argv(self):
        module = self.hexctl
        tip = self._merge(STEP_BRANCHES[1], STEP_BRANCHES[2])
        calls = []
        native_probe = module.bounded_probe

        def record_probe(*args, **kwargs):
            calls.append((args, kwargs))
            return native_probe(*args, **kwargs)

        hostile = {
            "GIT_DIR": str(self.repo / "absent-git-dir"),
            "GIT_OBJECT_DIRECTORY": str(self.repo / "absent-objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(self.repo / "absent-alts"),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.repositoryformatversion",
            "GIT_CONFIG_VALUE_0": "999",
        }
        with mock.patch.dict(os.environ, hostile, clear=False), mock.patch.object(
            module, "bounded_probe", side_effect=record_probe
        ):
            message = self._run_guard()
        self.assertIsNotNone(message)
        self.assertEqual(len(calls), 1, "one moved tip must cost exactly one native child")
        args, kwargs = calls[0]
        self.assertEqual(args[1], module._native_git_executable())
        self.assertTrue(os.path.isabs(args[1]))
        self.assertEqual(
            args[2],
            [
                "--no-replace-objects",
                "rev-list",
                f"--max-count={module.GIT_PATHS_MAX + 1}",
                f"{self._head(2)}..{tip}",
            ],
        )
        self.assertNotIn("fetch", " ".join(args[2]))
        self.assertEqual(kwargs["timeout"], module.GIT_TIMEOUT)
        self.assertEqual(kwargs["output_max"], module.GIT_OUTPUT_MAX)
        environment = kwargs["environment"]
        for name, value in hostile.items():
            self.assertNotEqual(environment.get(name), value)
        self.assertEqual(environment["PATH"], os.defpath)
        self.assertEqual(environment["GIT_CONFIG_GLOBAL"], os.devnull)
        self.assertEqual(environment["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(environment["GIT_CONFIG_SYSTEM"], os.devnull)
        self.assertEqual(environment["GIT_NO_LAZY_FETCH"], "1")
        self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")

    def test_a_refusal_names_the_observation_and_no_mechanism(self):
        self._merge(STEP_BRANCHES[1], STEP_BRANCHES[2])
        message = self._run_guard()
        self.assertIsNotNone(message)
        for absent in ("GitHub", "cherry", "re-sign", "stacked-pull-request", "rewrote"):
            self.assertNotIn(absent, message)


class CarriedStackCliCases(HexctlCase):
    """``next`` on a pushed stack whose branches carry another step's commits.

    The step heads are real commits in the fixture repository, so the native
    range query answers from real objects; the fake ``git`` still answers refs,
    signatures and the ``done push`` range, which ``FAKE_GIT_REV_LIST`` shapes
    so step 3's receipt owns both of its commits.
    """

    def native(self, *argv, input_text=None):
        executable = native_git_executable()
        self.assertIsNotNone(executable)
        result = subprocess.run(
            [executable, *argv],
            cwd=self.target,
            input=input_text,
            capture_output=True,
            text=True,
            env={
                "PATH": os.defpath,
                "GIT_AUTHOR_NAME": "Fixture",
                "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "Fixture",
                "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
                "GIT_AUTHOR_DATE": "1000000000 +0000",
                "GIT_COMMITTER_DATE": "1000000000 +0000",
            },
        )
        if result.returncode:
            self.fail(
                f"native git {' '.join(argv)} -> {result.returncode}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
        return result.stdout.strip()

    def to_carried_stack(self):
        """Three pushed steps whose heads are real commits: s1 <- s2 <- s3a <- s3b."""
        self.to_steps(("Scaffold", "Core", "Ship"))
        tree = self.native("mktree", input_text="")
        parent = self.native("rev-parse", "HEAD")
        chain = []
        for name in ("s1", "s2", "s3a", "s3b"):
            parent = self.native("commit-tree", tree, "-p", parent, "-m", name)
            chain.append(parent)
        self.s1, self.s2, self.s3a, self.s3b = chain
        self.heads = {1: self.s1, 2: self.s2, 3: self.s3b}
        for number in (1, 2, 3):
            self.run_ctl(
                "done", "implement", "--branch", self.step_branch(number),
                "--commit", f"abc{number}",
            )
            if number == 1:
                self.run_ctl("record", "security_suite", SUITE)
            self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
            self.run_ctl("done", "audit")
            self.run_ctl(
                "done", "prose", "--files", "1", "--skills",
                "hexaemeron:imprimatur,hexaemeron:vulgate",
            )
            if number == 3:
                self.env["FAKE_GIT_REV_LIST"] = json.dumps(
                    {f"{self.s2}..{self.s3b}": [self.s3a, self.s3b]}
                )
            self.run_ctl(
                "done", "push",
                "--pr-url", f"https://github.com/wildcat-finance/example/pull/{number}",
                "--head-commit", self.heads[number],
                "--pr-base", self.step_base(number),
            )
        self.env.pop("FAKE_GIT_REV_LIST", None)
        self.branches = {number: self.step_branch(number) for number in (1, 2, 3)}

    def run_bytes(self):
        out = {}
        for name in ("state.json", "ledger.jsonl"):
            with open(os.path.join(self.target, ".hexaemeron", name), "rb") as handle:
                out[name] = handle.read()
        return out

    def refused_next(self):
        before = self.run_bytes()
        proc = self.run_ctl("next", expect=2)
        self.assertEqual(proc.stdout, "", "a refused next printed a directive")
        self.assertEqual(self.run_bytes(), before, "a refusal changed state or ledger bytes")
        return proc.stderr

    def test_next_withholds_the_directive_for_a_carried_waiting_branch(self):
        self.to_carried_stack()
        self.fake_refs[self.branches[2]] = self.s3b
        stderr = self.refused_next()
        self.assertIn("gained a commit another step's push receipt owns", stderr)
        self.assertIn(f"step 2 (a waiting step, '{self.branches[2]}')", stderr)
        self.assertIn(f"recorded head {self.s2} and observed tip {self.s3b}", stderr)
        self.assertIn(f"first carried commit in rev-list order is {self.s3b}", stderr)
        self.assertIn("owned by step 3's push receipt", stderr)

    def test_next_withholds_the_directive_for_a_carried_current_step(self):
        self.to_carried_stack()
        self.fake_refs[self.branches[1]] = self.s3b
        stderr = self.refused_next()
        self.assertIn(f"step 1 (the step being merged, '{self.branches[1]}')", stderr)
        self.assertIn(f"recorded head {self.s1} and observed tip {self.s3b}", stderr)
        self.assertIn(f"first carried commit in rev-list order is {self.s3b}", stderr)
        self.assertIn("owned by step 3's push receipt", stderr)

    def test_a_partial_carry_of_a_non_head_commit_refuses_through_the_receipt(self):
        self.to_carried_stack()
        receipt = self.state()["steps"][2]["receipts"]["push"]
        self.assertEqual(receipt["verified_commits"], [self.s3a, self.s3b])
        self.fake_refs[self.branches[2]] = self.s3a
        stderr = self.refused_next()
        self.assertIn(f"first carried commit in rev-list order is {self.s3a}", stderr)
        self.assertIn("owned by step 3's push receipt", stderr)

    def test_a_healthy_stack_still_prints_the_merge_step_directive(self):
        self.to_carried_stack()
        directive = self.next_json()
        self.assertEqual(directive["do"], "merge-step")
        self.assertEqual(directive["step"], 1)

    def test_an_unanswered_range_refuses_as_unknown(self):
        self.to_carried_stack()
        self.fake_refs[self.branches[1]] = MISSING_OBJECT
        stderr = self.refused_next()
        self.assertIn("unknown gained range", stderr)
        self.assertIn(f"{self.s1}..{MISSING_OBJECT}", stderr)
        self.assertIn("nothing was fetched and no cause is claimed", stderr)
        self.assertNotIn("gained a commit another step's push receipt owns", stderr)


class FakeGitRevListMap(HexctlCase):
    """The harness answers a mapped range exactly and leaves every mode alone."""

    def fake_git(self, *argv, mode=None, ranges=None):
        env = {"PATH": os.environ.get("PATH", os.defpath)}
        if mode is not None:
            env["FAKE_GIT_MODE"] = mode
        if ranges is not None:
            env["FAKE_GIT_REV_LIST"] = json.dumps(ranges)
        result = subprocess.run(
            [sys.executable, os.path.join(self.dir, "delivery-tools", "git"), *argv],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def test_a_mapped_range_prints_exactly_its_lines(self):
        pair = f"{'1' * 40}..{'2' * 40}"
        lines = ["3" * 40, "2" * 40]
        self.assertEqual(
            self.fake_git("rev-list", "--reverse", "--max-count=501", pair, ranges={pair: lines}),
            lines,
        )
        self.assertEqual(
            self.fake_git("rev-list", "--max-count=501", pair, mode="intermediate", ranges={pair: lines}),
            lines,
            "a mapped range outranks the mode",
        )

    def test_an_unmapped_range_keeps_every_mode_answer(self):
        pair = f"{'1' * 40}..{'2' * 40}"
        other = {f"{'8' * 40}..{'9' * 40}": ["7" * 40]}
        for mode in (None, "intermediate", "malformed-range", "range-confusion"):
            with self.subTest(mode=mode):
                self.assertEqual(
                    self.fake_git("rev-list", "--max-count=501", pair, mode=mode),
                    self.fake_git("rev-list", "--max-count=501", pair, mode=mode, ranges=other),
                )


if __name__ == "__main__":
    unittest.main()
