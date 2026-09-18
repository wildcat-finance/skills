"""A later step's receipted commits carried into a lower step branch refuse.

Issue 1480. ``refuse_rewritten_stack`` admits any moved waiting tip whose
receipted head is still an ancestor, and a later step's branch merged into a
lower step's branch has exactly that shape. ``refuse_carried_step_commits``
reads every unmerged step, the step being merged included, enumerates the
gained range ``<recorded>..<tip>`` of a moved tip once, and refuses when that
range holds a commit another step's push receipt owns. ``refuse_rewritten_stack``
returns the waiting tips it read and the guard reads only the branches that map
lacks, so a healthy ``next`` reads each unmerged tip once. ``done merge-step``
runs the guard over the waiting steps before any GitHub read, adding no read,
and checks the step being merged over the repaired range its receipt
enumerates; ``status`` prints the same observation as ``CARRY:`` lines.
The graph cases use real Git objects, as the design record's specimens do; the
CLI cases drive ``next``, ``done merge-step`` and ``status`` through the
delivery harness and prove a refusal leaves ``.hexaemeron/state.json`` and
``.hexaemeron/ledger.jsonl`` byte-identical.

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
        # The guard owns the refusal: the range reader prints nothing of its
        # own, so stderr carries exactly one error line (S2-R1-02).
        self.assertEqual(
            message.count("hexctl: error:"), 1,
            "an unknown range must produce exactly one refusal line",
        )

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


class CarriedStackFixture(HexctlCase):
    """A pushed three-step stack whose heads are real commits.

    The native range query answers from real objects; the fake ``git`` still
    answers refs, signatures and the ``done push`` range, which
    ``FAKE_GIT_REV_LIST`` shapes so step 3's receipt owns both of its commits.
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
        self.tree = self.native("mktree", input_text="")
        parent = self.native("rev-parse", "HEAD")
        chain = []
        for name in ("s1", "s2", "s3a", "s3b"):
            parent = self.native("commit-tree", self.tree, "-p", parent, "-m", name)
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

    def refused(self, *argv):
        before = self.run_bytes()
        proc = self.run_ctl(*argv, expect=2)
        self.assertEqual(proc.stdout, "", f"a refused {argv[0]} printed to stdout")
        self.assertEqual(self.run_bytes(), before, "a refusal changed state or ledger bytes")
        return proc.stderr

    def refused_next(self):
        return self.refused("next")

    def merge_step_argv(self, number=1):
        return ("done", "merge-step", "--step", str(number), "--merge-commit", "1" * 40)

    def ls_remote_log(self):
        """Record every fake ``ls-remote`` and return the ref counts on demand."""
        path = os.path.join(self.dir, "ls-remote.log")
        self.env["FAKE_GIT_LS_REMOTE_LOG"] = path

        def counts():
            tally = {}
            with open(path, encoding="utf-8") as handle:
                for line in handle:
                    ref = json.loads(line)["args"][-1]
                    tally[ref] = tally.get(ref, 0) + 1
            return tally

        return counts

    def step_ref_counts(self, counts):
        return {
            number: counts.get(f"refs/heads/{branch}", 0)
            for number, branch in self.branches.items()
        }


class CarriedStackCliCases(CarriedStackFixture):
    """``next`` on a pushed stack whose branches carry another step's commits."""

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

    def test_next_reads_each_unmerged_tip_once_across_both_guards(self):
        """The study's one added native process on a healthy stack, measured:
        ``refuse_rewritten_stack`` reads the waiting tips, the carry guard
        reads only the current step's, and no branch is read twice."""
        self.to_carried_stack()
        counts = self.ls_remote_log()
        directive = self.next_json()
        self.assertEqual(directive["do"], "merge-step")
        self.assertEqual(
            self.step_ref_counts(counts()), {1: 1, 2: 1, 3: 1},
            "each unmerged step branch tip is read exactly once by next",
        )


class CarriedStackMergeStepCases(CarriedStackFixture):
    """``done merge-step`` refuses a carry before any write.

    A carry into a waiting branch refuses through the guard, before GitHub
    is read. A carry into the step being merged moves its tip off the
    recorded head, so the receipt takes its repair path and the repaired range
    ``pr_base..remote_head`` refuses through the ownership intersection; the
    fixture marks the pull request merged so that path is reached.
    """

    def merged_pull_request(self, number, head):
        pull_request = self.fake_prs[
            f"https://github.com/wildcat-finance/example/pull/{number}"
        ]
        pull_request["head"]["sha"] = head
        pull_request["state"] = "closed"
        pull_request["merged"] = True
        pull_request["merge_commit_sha"] = "1" * 40

    def test_done_merge_step_refuses_a_whole_carry_into_a_waiting_step_before_any_github_read(self):
        self.to_carried_stack()
        self.fake_refs[self.branches[2]] = self.s3b
        gh_log = os.path.join(self.dir, "gh.log")
        self.env["FAKE_GH_LOG"] = gh_log
        stderr = self.refused(*self.merge_step_argv(1))
        self.assertIn("gained a commit another step's push receipt owns", stderr)
        self.assertIn(f"step 2 (a waiting step, '{self.branches[2]}')", stderr)
        self.assertIn(f"recorded head {self.s2} and observed tip {self.s3b}", stderr)
        self.assertIn(f"first carried commit in rev-list order is {self.s3b}", stderr)
        self.assertIn("owned by step 3's push receipt", stderr)
        self.assertFalse(
            os.path.exists(gh_log), "a refused merge-step consulted GitHub first"
        )
        self.assertEqual(self.state()["integrate"]["merged"], [])

    def test_done_merge_step_refuses_a_partial_carry_into_a_waiting_step(self):
        self.to_carried_stack()
        self.fake_refs[self.branches[2]] = self.s3a
        stderr = self.refused(*self.merge_step_argv(1))
        self.assertIn(f"step 2 (a waiting step, '{self.branches[2]}')", stderr)
        self.assertIn(f"recorded head {self.s2} and observed tip {self.s3a}", stderr)
        self.assertIn(f"first carried commit in rev-list order is {self.s3a}", stderr)
        self.assertIn("owned by step 3's push receipt", stderr)
        self.assertNotIn(self.s3b, stderr)

    def test_done_merge_step_refuses_a_whole_carry_into_the_step_being_merged(self):
        self.to_carried_stack()
        self.fake_refs[self.branches[1]] = self.s3b
        self.merged_pull_request(1, self.s3b)
        stderr = self.refused(*self.merge_step_argv(1))
        self.assertIn(f"the repaired range {self.run_branch()}..{self.s3b} for step 1", stderr)
        self.assertIn(f"holds {self.s3b}, the first commit in it owned by step 3's push receipt", stderr)
        self.assertEqual(self.state()["integrate"]["merged"], [])

    def test_done_merge_step_refuses_a_partial_carry_into_the_step_being_merged(self):
        self.to_carried_stack()
        self.fake_refs[self.branches[1]] = self.s3a
        self.merged_pull_request(1, self.s3a)
        stderr = self.refused(*self.merge_step_argv(1))
        self.assertIn(f"holds {self.s3a}, the first commit in it owned by step 3's push receipt", stderr)
        self.assertNotIn(self.s3b, stderr)

    def test_done_merge_step_with_an_equal_tip_still_receipts(self):
        self.to_carried_stack()
        proc = self.run_ctl(*self.merge_step_argv(1))
        self.assertIn("step 1 merged into", proc.stdout)
        integrate = self.state()["integrate"]
        self.assertEqual(integrate["merged"], [1])
        self.assertFalse(integrate["merges"]["1"]["effective_push"]["repaired"])

    def test_done_merge_step_adds_no_tip_read(self):
        """The guard reads nothing at merge-step: the waiting tips come from
        ``refuse_rewritten_stack`` and the receipt's own read of the current
        tip is the only one (study section 10)."""
        self.to_carried_stack()
        counts = self.ls_remote_log()
        self.run_ctl(*self.merge_step_argv(1))
        self.assertEqual(self.step_ref_counts(counts()), {1: 1, 2: 1, 3: 1})

    def test_a_repaired_range_holding_an_owned_commit_refuses_before_effective_push(self):
        """The current tip is an unowned child of the recorded head, so the
        gained range admits it; the repaired range ``pr_base..tip`` the fake
        enumerates for the receipt carries step 3's first commit and refuses."""
        self.to_carried_stack()
        extension = self.native("commit-tree", self.tree, "-p", self.s1, "-m", "s1x")
        self.fake_refs[self.branches[1]] = extension
        self.merged_pull_request(1, extension)
        run_branch = self.run_branch()
        base = self.fake_refs.get(run_branch, self.fake_sha(run_branch))
        self.env["FAKE_GIT_REV_LIST"] = json.dumps(
            {f"{base}..{extension}": [self.s3a, extension]}
        )
        stderr = self.refused(*self.merge_step_argv(1))
        # The refusal names the range as the receipt would have recorded it:
        # the pull request base by name, the remote head by SHA.
        self.assertIn(f"the repaired range {run_branch}..{extension} for step 1", stderr)
        self.assertIn(f"holds {self.s3a}, the first commit in it owned by step 3's push receipt", stderr)
        self.assertIn("do not receipt this merge", stderr)
        self.assertNotIn("gained a commit another step's push receipt owns", stderr)
        self.assertEqual(self.state()["integrate"]["merged"], [])


class CarriedStackStatusCases(CarriedStackFixture):
    """``status`` reports a carry as ``CARRY:`` lines and refuses nothing."""

    def carry_lines(self):
        before = self.run_bytes()
        proc = self.run_ctl("status")
        self.assertEqual(self.run_bytes(), before, "status changed state or ledger bytes")
        return proc, [line for line in proc.stdout.splitlines() if line.startswith("CARRY: ")]

    def test_status_prints_one_carry_line_per_carried_step_and_exits_0(self):
        self.to_carried_stack()
        self.fake_refs[self.branches[1]] = self.s3b
        self.fake_refs[self.branches[2]] = self.s3a
        proc, lines = self.carry_lines()
        self.assertEqual(len(lines), 2, proc.stdout)
        self.assertIn(f"step 1 (the step being merged, '{self.branches[1]}')", lines[0])
        self.assertIn(f"recorded head {self.s1} and observed tip {self.s3b}", lines[0])
        self.assertIn(f"first carried commit in rev-list order is {self.s3b}", lines[0])
        self.assertIn(f"step 2 (a waiting step, '{self.branches[2]}')", lines[1])
        self.assertIn(f"first carried commit in rev-list order is {self.s3a}", lines[1])
        for line in lines:
            self.assertIn("owned by step 3's push receipt", line)
        self.assertIn("phase: integrate (0/3 steps merged", proc.stdout)

    def test_status_prints_an_unknown_range_as_unknown_and_refuses_nothing(self):
        self.to_carried_stack()
        self.fake_refs[self.branches[1]] = MISSING_OBJECT
        proc, lines = self.carry_lines()
        self.assertEqual(len(lines), 1, proc.stdout)
        self.assertIn(f"step 1 (the step being merged, '{self.branches[1]}')", lines[0])
        self.assertIn(f"the range {self.s1}..{MISSING_OBJECT} is unknown", lines[0])
        self.assertNotIn("owned by", lines[0])
        self.assertEqual(proc.stderr, "")

    def test_status_prints_an_unreadable_tip_as_unknown(self):
        self.to_carried_stack()
        self.env["FAKE_GIT_MODE"] = "remote-absent"
        proc, lines = self.carry_lines()
        self.assertEqual(len(lines), 3, proc.stdout)
        for number, line in zip((1, 2, 3), lines):
            self.assertIn(f"step {number} (", line)
            self.assertIn(f"'{self.branches[number]}'", line)
            self.assertIn("its tip could not be read", line)
            self.assertIn("is unknown", line)

    def test_status_prints_no_carry_line_on_a_healthy_stack(self):
        self.to_carried_stack()
        proc, lines = self.carry_lines()
        self.assertEqual(lines, [], proc.stdout)


class SharedTipMap(unittest.TestCase):
    """``refuse_rewritten_stack`` hands its reads to the guard (S2-R1-01)."""

    def setUp(self):
        self.hexctl = hexctl_module()

    def _state(self, merged):
        heads = {1: "a" * 40, 2: "b" * 40, 3: "c" * 40}
        return {
            "integrate": {"merged": merged},
            "steps": [
                {"n": number, "title": f"step {number}", "receipts": {"push": {
                    "head_commit": heads[number],
                    "verified_commits": [heads[number]],
                    "early_merge": None,
                }}}
                for number in (1, 2, 3)
            ],
        }

    def _patched(self, tips, queried):
        module = self.hexctl

        def tip(_dir, branch, label="remote run branch tip"):
            queried.append(branch)
            return tips[branch]

        return mock.patch.object(
            module, "step_branch_name", side_effect=lambda _s, step: f"branch-{step['n']}"
        ), mock.patch.object(module, "remote_branch_tip", side_effect=tip)

    def test_refuse_rewritten_stack_returns_the_waiting_tips_it_read(self):
        queried = []
        names, reads = self._patched({"branch-3": "c" * 40}, queried)
        with names, reads:
            returned = self.hexctl.refuse_rewritten_stack(".", self._state([1]), 2)
        self.assertEqual(returned, {"branch-3": "c" * 40})
        self.assertEqual(queried, ["branch-3"], "the current step is never read")

    def test_the_guard_reads_only_the_tips_the_map_lacks(self):
        queried = []
        names, reads = self._patched({"branch-1": "a" * 40}, queried)
        given = {"branch-2": "b" * 40, "branch-3": "c" * 40}
        with names, reads:
            returned = self.hexctl.refuse_carried_step_commits(
                ".", self._state([]), 1, given
            )
        self.assertEqual(queried, ["branch-1"], "a tip the map holds was read again")
        self.assertEqual(returned, {**given, "branch-1": "a" * 40})
        self.assertEqual(given, {"branch-2": "b" * 40, "branch-3": "c" * 40}, "the caller's map was mutated")

    def test_the_merge_step_guard_reads_no_tip_and_skips_the_step_being_merged(self):
        queried = []
        names, reads = self._patched({}, queried)
        given = {"branch-2": "b" * 40, "branch-3": "c" * 40}
        with names, reads:
            returned = self.hexctl.refuse_carried_step_commits(
                ".", self._state([]), 1, given, waiting_only=True
            )
        self.assertEqual(queried, [], "done merge-step read a tip the map already held")
        self.assertEqual(returned, given)


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
