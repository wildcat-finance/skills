"""The window: a filing decision too young for a run to start on.

`init` refuses when GraphQL shows the body changed inside
`FILING_DECISION_WINDOW_SECONDS` and the `Fiat-Required` line moved, or its
prior value could not be read. A body edit that left the decision alone is
cleared, a stamp older than the window clears on REST alone, and a recent
`updated_at` that nothing can attribute to the body proceeds as
undiscriminated, which the maintainer decided on 6 September 2026.

The gate has no clock override, because a variable that moved "now" would be a
variable that clears the refusal. So every timestamp here is built from the
real clock at the moment a case runs, and the cases hold the absence of an
override directly rather than trusting the author not to have added one.

Its own module because `test_hexctl.py` is bounded at 262144 bytes and has
under three kilobytes left.
"""

import datetime
import inspect
import json
import os
import re
import unittest

try:
    from .hexctl_harness import HexctlCase, hexctl_module
except ImportError:
    from hexctl_harness import HexctlCase, hexctl_module


def stamp(seconds_ago: float) -> str:
    """An ISO timestamp this many seconds before the real clock reads now."""
    moment = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        seconds=seconds_ago
    )
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


class FilingDecisionWindowTests(HexctlCase):
    """What `init` does with a decision that moved moments before it ran."""

    ISSUE = "https://github.com/wildcat-finance/example/issues/74"
    RECENT = 120
    OLD = 7200

    def body(self, value):
        return (
            "A filing.\n"
            "\n"
            f"Fiat-Required: {value}\n"
            "\n"
            "```carryover\n"
            "none | none | nothing is carried\n"
            "```\n"
        )

    def seed(self, current=1, created=OLD, updated=RECENT, nodes=None,
             mode=None):
        self.env["FAKE_GH_ISSUES"] = json.dumps({self.ISSUE: self.body(current)})
        self.env["FAKE_GH_ISSUE_STAMPS"] = json.dumps(
            {"default": {"created_at": stamp(created),
                         "updated_at": stamp(updated)}}
        )
        if nodes is not None:
            self.env["FAKE_GH_EDITS"] = json.dumps(
                {"totalCount": len(nodes), "nodes": nodes}
            )
        if mode is not None:
            self.env["FAKE_GH_MODE"] = mode

    def init(self, expect=0):
        return self.run_ctl(
            "init", "--topic", "Window topic", "--task-issue", self.ISSUE,
            expect=expect,
        )

    def window(self):
        contract = self.state()["receipts"]["task_issue_contract"]
        return contract["filing_window"]

    def test_a_decision_that_moved_inside_the_window_is_refused(self):
        self.seed(current=1, nodes=[
            {"editedAt": stamp(self.RECENT), "diff": self.body(1)},
            {"editedAt": stamp(self.OLD), "diff": self.body(0)},
        ])
        proc = self.init(expect=1)
        self.assertIn("moved from 0 to 1", proc.stderr)
        self.assertIn("inside the 15-minute window", proc.stderr)
        self.assertFalse(
            os.path.exists(os.path.join(self.target, ".hexaemeron", "state.json")),
            "a refused init wrote run state",
        )

    def test_a_decision_that_moved_before_the_window_is_accepted(self):
        self.seed(current=1, updated=self.OLD, nodes=[
            {"editedAt": stamp(self.OLD), "diff": self.body(1)},
            {"editedAt": stamp(self.OLD + 600), "diff": self.body(0)},
        ])
        self.init()
        window = self.window()
        self.assertEqual(window["verdict"], "clear")
        self.assertIn("outside the window", window["observed"])

    def test_a_recent_body_edit_that_left_the_decision_alone_is_accepted(self):
        """The refinement exists to remove this false positive."""
        self.seed(current=1, nodes=[
            {"editedAt": stamp(self.RECENT), "diff": self.body(1)},
            {"editedAt": stamp(self.OLD), "diff": self.body(1)},
        ])
        self.init()
        window = self.window()
        self.assertEqual(window["verdict"], "clear")
        self.assertIn("stayed 1", window["observed"])

    def test_an_unreadable_prior_decision_inside_the_window_is_refused(self):
        self.seed(current=1, nodes=[
            {"editedAt": stamp(self.RECENT), "diff": self.body(1)},
            {"editedAt": stamp(self.OLD), "diff": None},
        ])
        proc = self.init(expect=1)
        self.assertIn("could not be read", proc.stderr)

    def test_an_undiscriminated_rest_read_proceeds_and_says_so(self):
        self.seed(current=1, updated=self.RECENT, mode="graphql-unreachable")
        self.init()
        window = self.window()
        self.assertEqual(window["verdict"], "undiscriminated")
        self.assertIn("cannot say whether the body changed", window["observed"])
        for claim in ("enforced", "clear", "refused"):
            self.assertNotIn(claim, window["observed"])

    def test_an_old_updated_at_clears_on_rest_alone(self):
        """`updated_at` bounds the last body change from above."""
        self.seed(current=1, updated=self.OLD, mode="graphql-unreachable")
        self.init()
        self.assertEqual(self.window()["verdict"], "clear")

    def test_an_unreadable_prior_body_is_recorded_as_observed(self):
        """The receipt says what was read, not why GitHub withheld it.

        The reason attributed a null `diff` to write access on the repository.
        Measured on 2026-09-13, `diff` was readable on a public repository with
        read access alone, so the sentence named a cause the reader never
        observed (S4-R1-03). The last edit sits outside the window so the run
        proceeds and the receipt is written.
        """
        self.seed(current=1, updated=self.OLD, nodes=[
            {"editedAt": stamp(self.OLD), "diff": self.body(1)},
            {"editedAt": stamp(self.OLD + 600), "diff": None},
        ])
        self.init()
        provenance = self.state()["receipts"]["task_issue_contract"]["provenance"]
        self.assertEqual(provenance["prior_fiat_required"], "unknown")
        self.assertIn("`diff` was absent or not text", provenance["reason"])
        self.assertNotIn("write access", provenance["reason"])

    def test_the_refusal_names_no_way_to_get_this_run(self):
        self.seed(current=1, nodes=[
            {"editedAt": stamp(self.RECENT), "diff": self.body(1)},
            {"editedAt": stamp(self.OLD), "diff": self.body(0)},
        ])
        emitted = self.init(expect=1)
        text = (emitted.stdout + emitted.stderr).lower()
        for grant in ("override", "--force", "wait", "retry", "try again",
                      "change the issue", "fiat-required: 0", "bypass",
                      "environment", "flag"):
            self.assertNotIn(grant, text, f"the refusal names {grant!r}")


class NoOverrideExistsTests(unittest.TestCase):
    """Absence, held by reading the code rather than by trusting its author.

    The decision record says no flag, environment variable or argument clears
    the refusal. A test that only drove the documented interface would pass
    whether or not someone had added a door, so these read the parser and the
    gate's own source.
    """

    def test_init_takes_no_argument_that_touches_the_window(self):
        module = hexctl_module()
        # A skip here would pass without enumerating anything, which is the
        # vacuous green this run filed against the checked runner as
        # skills#1429. An absence test has to fail when it cannot look.
        self.assertTrue(
            hasattr(module, "build_parser"),
            "hexctl exposes no parser builder, so no option can be enumerated",
        )
        parser = module.build_parser()
        init = next(
            action.choices["init"]
            for action in parser._actions
            if getattr(action, "choices", None) and "init" in action.choices
        )
        for action in init._actions:
            # Whole words: a substring test reads "age" inside "message".
            words = set(re.findall(r"[a-z]+", " ".join(
                [*action.option_strings, str(action.dest), str(action.help or "")]
            ).lower()))
            for door in ("window", "override", "age", "force", "skip", "clock"):
                self.assertNotIn(
                    door, words,
                    f"init option {action.option_strings} mentions {door!r}",
                )

    def test_the_gate_reads_no_environment_and_no_clock_seam(self):
        module = hexctl_module()
        source = inspect.getsource(module.filing_decision_window)
        for door in ("environ", "getenv", "HEXCTL_", "FAKE_"):
            self.assertNotIn(door, source, f"the window gate reads {door!r}")
        self.assertIn("datetime.datetime.now", source)

    def test_the_call_site_consults_nothing_between_the_verdict_and_the_refusal(self):
        """The door would be at the call site, not inside the gate.

        The gate is a function of the provenance block alone, so an option or
        a variable that cleared the refusal would be read in `cmd_init` between
        the verdict and `die`, where `args` is in scope. The parser case above
        is a six-word denylist, and it cannot hold `waiver`, the one door-shaped
        word `init` already uses in `--controller-currency-waiver`, so it trips
        on some names and proves nothing about the rest. This reads the segment
        itself (S4-R1-01).
        """
        module = hexctl_module()
        source = inspect.getsource(module.cmd_init)
        start = source.index('provenance = task_issue_contract.get("provenance")')
        end = source.index('task_issue_contract["filing_window"] = window')
        segment = source[start:end]
        self.assertIn('window["verdict"] == "refuse"', segment)
        self.assertIn("die(", segment)
        for door in ("args.", "environ", "getenv", "config", "input(", "open("):
            self.assertNotIn(door, segment, f"the call site reads {door!r}")


if __name__ == "__main__":
    unittest.main()
