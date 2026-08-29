"""What the controller does when the run branch moves outside the loop.

Issues 594 and 555. Every legitimate change to the run branch during integration
is one the run recorded: a merge-step receipt, or a sync. A tip that is neither
means something merged into it the controller was never asked for, and because a
stack chains, that is unrecoverable rather than untidy.

A new module rather than more of `test_hexctl.py`, which is close enough to the
Promise Machine's 262144-byte bounded-read ceiling that issue 576's tests had to
move out of it.
"""

import json
import os
import unittest

import sys

# `run_tests.py` discovers from this directory and puts it on the path; a reader
# running this module on its own does not get that, and the shared harness lives
# next door rather than in a package.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_hexctl import SUITE, HexctlCase


class StackCase(HexctlCase):
    """A pushed stack and the helpers both classes below drive it with."""

    def to_stack(self, titles=("Scaffold", "Core", "Ship")):
        """A pushed stack of `titles`, parked at the first merge-step."""
        self.to_steps(titles)
        for number, _ in enumerate(titles, 1):
            self.run_ctl(
                "done", "implement", "--branch", self.step_branch(number),
                "--commit", f"abc{number}",
            )
            if number == 1:
                self.run_ctl("record", "security_suite", SUITE)
            self.run_ctl("audit-round", "--findings", "0")
            self.run_ctl("done", "audit")
            self.run_ctl(
                "done", "prose", "--files", "1", "--skills",
                "hexaemeron:imprimatur,hexaemeron:vulgate",
            )
            self.run_ctl(
                "done", "push",
                "--pr-url", f"https://github.com/wildcat-finance/example/pull/{number}",
                "--head-commit", format(number, "x") * 40,
                "--pr-base", self.step_base(number),
            )

    def state_bytes(self):
        with open(os.path.join(self.target, ".hexaemeron", "state.json"), "rb") as fh:
            return fh.read()

    def merge(self, number, sha=None, expect=0):
        return self.run_ctl(
            "done", "merge-step", "--step", str(number),
            "--merge-commit", sha or format(number, "x") * 40, expect=expect,
        )

    def move_run_branch(self, sha):
        """Something merged into the run branch that this run did not receipt.

        The branch is read into a name first. `self.fake_refs[self.state()[...]]`
        binds the dict before `state()` runs, and `state()` replaces it, so the
        write lands in the copy nothing reads afterwards.
        """
        branch = self.state()["run_branch"]
        self.fake_refs[branch] = sha


class PrematureStackMergeTests(StackCase):
    def test_a_healthy_stack_merges_unchanged(self):
        """The guard has to be invisible to a run that does the right thing."""
        self.to_stack()
        for number in (1, 2, 3):
            self.merge(number)
        self.assertEqual(self.state()["integrate"]["merged"], [1, 2, 3])

    def test_nothing_fires_before_the_first_merge(self):
        """With no merge recorded the controller has no expectation to compare."""
        self.to_stack()
        self.move_run_branch("9" * 40)
        self.assertEqual(self.next_json()["do"], "merge-step")
        self.merge(1)

    def test_a_run_branch_moved_outside_the_loop_refuses_at_the_receipt(self):
        self.to_stack()
        self.merge(1)
        self.move_run_branch("9" * 40)
        proc = self.merge(2, expect=2)
        self.assertIn("this run did not receipt", proc.stderr)
        self.assertIn("9" * 40, proc.stderr)
        self.assertIn("1" * 40, proc.stderr)

    def test_it_refuses_at_next_rather_than_at_the_merge_after(self):
        """The whole point: the refusal arrives while the stack can still land."""
        self.to_stack()
        self.merge(1)
        self.move_run_branch("9" * 40)
        proc = self.run_ctl("next", expect=2)
        self.assertIn("this run did not receipt", proc.stderr)

    def test_it_names_that_there_is_no_repair(self):
        self.to_stack()
        self.merge(1)
        self.move_run_branch("9" * 40)
        proc = self.merge(2, expect=2)
        self.assertIn("no repair", proc.stderr)
        self.assertIn("retargeted", proc.stderr)

    def test_status_reports_it_rather_than_refusing(self):
        """`status` is what somebody runs to find out what is wrong."""
        self.to_stack()
        self.merge(1)
        self.move_run_branch("9" * 40)
        proc = self.run_ctl("status")
        self.assertIn("STACK:", proc.stdout)
        self.assertIn("9" * 40, proc.stdout)

    def test_status_stays_quiet_on_a_healthy_stack(self):
        self.to_stack()
        self.merge(1)
        self.assertNotIn("STACK:", self.run_ctl("status").stdout)

    def test_a_refused_receipt_leaves_the_state_file_byte_identical(self):
        self.to_stack()
        self.merge(1)
        self.move_run_branch("9" * 40)
        before = self.state_bytes()
        self.merge(2, expect=2)
        self.assertEqual(self.state_bytes(), before)

    def test_an_unreadable_run_branch_refuses_at_the_receipt(self):
        self.to_stack()
        self.merge(1)
        self.env["FAKE_GIT_MODE"] = "remote-absent"
        proc = self.merge(2, expect=2)
        self.assertIn("could not be read", proc.stderr)

    def test_an_unreadable_run_branch_is_reported_as_unknown_by_status(self):
        """Reported, not refused: a wrong answer here is not acted on."""
        self.to_stack()
        self.merge(1)
        self.env["FAKE_GIT_MODE"] = "remote-absent"
        proc = self.run_ctl("status")
        self.assertIn("STACK:", proc.stdout)
        self.assertIn("unknown", proc.stdout)

    def test_the_expected_tip_follows_the_last_receipted_merge(self):
        self.to_stack()
        self.merge(1)
        self.merge(2)
        self.move_run_branch("2" * 40)
        self.assertEqual(self.next_json()["do"], "merge-step")
        self.move_run_branch("9" * 40)
        self.run_ctl("next", expect=2)

    def test_a_recorded_sync_becomes_the_expected_tip(self):
        """After a sync the run branch is the sync commit, not the last merge."""
        module = __import__("test_hexctl").hexctl_module()
        expected = module.expected_run_branch_tip
        state = {
            "integrate": {
                "merged": [1],
                "merges": {"1": {"merge_commit": "a" * 40}},
                "sync": {"commit": "b" * 40},
            }
        }
        self.assertEqual(expected(state), "b" * 40)
        del state["integrate"]["sync"]
        self.assertEqual(expected(state), "a" * 40)
        state["integrate"]["merged"] = []
        self.assertIsNone(expected(state))


class MergeCommandDirectiveTests(StackCase):
    """The directive carries the command, so no number is retyped from a URL."""

    def test_the_directive_carries_the_command_for_its_own_pull_request(self):
        self.to_stack()
        directive = self.next_json()
        self.assertEqual(
            directive["merge"], f"gh pr merge {directive['pr_url']} --merge"
        )

    def test_the_command_follows_the_stack_down(self):
        self.to_stack()
        self.merge(1)
        directive = self.next_json()
        self.assertEqual(directive["step"], 2)
        self.assertIn("/pull/2", directive["merge"])
        self.assertNotIn("/pull/1", directive["merge"])

    def test_the_receipt_command_is_unchanged(self):
        self.to_stack()
        directive = self.next_json()
        self.assertEqual(
            directive["then"],
            "hexctl done merge-step --step 1 --merge-commit <sha>",
        )

    def test_a_missing_recorded_url_refuses_rather_than_guessing(self):
        self.to_stack()
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        del state["steps"][0]["receipts"]["push"]["pr_url"]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        proc = self.run_ctl("next", expect=2)
        self.assertIn("no usable pull request URL", proc.stderr)

    def test_a_malformed_recorded_url_refuses(self):
        self.to_stack()
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        state["steps"][0]["receipts"]["push"]["pr_url"] = "not a url"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        proc = self.run_ctl("next", expect=2)
        self.assertIn("no usable pull request URL", proc.stderr)

    def test_no_other_directive_gains_a_command(self):
        self.to_steps(("Scaffold",))
        self.assertNotIn("merge", self.next_json())


if __name__ == "__main__":
    unittest.main(verbosity=2)
