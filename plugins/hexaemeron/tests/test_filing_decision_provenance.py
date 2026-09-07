"""What a run records about the filing decision it read, and what it discards.

A run that began seconds after its own issue was edited could not say so from
its own evidence. The provenance block answers that from what `init` already
reads, plus at most one GraphQL request that is never required.

`userContentEdits` returns whole prior bodies, not a diff, so the reader takes
the `Fiat-Required` value out of the revision before the current one and lets
every byte of the body go. These cases hold that: one plants a sentence in a
prior revision and looks for it in stdout, stderr, the state file and the
ledger, while asserting that the value from that same body survived.

Its own module because `test_hexctl.py` is bounded at 262144 bytes and this law
pushed it over, the same reason the harness moved out before it.
"""

import json
import os
import subprocess
import unittest

try:
    from .hexctl_harness import HexctlCase, hexctl_module
except ImportError:
    from hexctl_harness import HexctlCase, hexctl_module


class FilingDecisionProvenanceTests(HexctlCase):
    """What the run records about the decision it read, and what it never keeps.

    A run that started on a decision edited moments earlier could not say so
    from its own evidence. These cases hold the provenance block to three
    promises: it says what was read, it says `unknown` with a reason where it
    could not look, and it keeps no prior body text anywhere.
    """

    ISSUE = "https://github.com/wildcat-finance/example/issues/74"
    PRIOR_MARKER = "a sentence only a prior revision carries"

    def body(self, value, extra=""):
        return (
            f"A filing.{extra}\n"
            "\n"
            f"Fiat-Required: {value}\n"
            "\n"
            "```carryover\n"
            "none | none | nothing is carried\n"
            "```\n"
        )

    def stamps(self, created="2026-09-06T09:17:50Z", updated="2026-09-06T10:08:38Z"):
        self.env["FAKE_GH_ISSUE_STAMPS"] = json.dumps(
            {"default": {"created_at": created, "updated_at": updated}}
        )

    def edits(self, nodes, total=None):
        self.env["FAKE_GH_EDITS"] = json.dumps(
            {"totalCount": len(nodes) if total is None else total, "nodes": nodes}
        )

    def start(self, value=1, **kwargs):
        self.env["FAKE_GH_ISSUES"] = json.dumps({self.ISSUE: self.body(value)})
        self.stamps(**kwargs)
        self.init("Provenance topic", task_issue=self.ISSUE)
        return self.state()["receipts"]["task_issue_contract"]["provenance"]

    def test_a_readable_history_records_the_count_time_and_prior_value(self):
        self.edits([
            {"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)},
            {"editedAt": "2026-09-06T09:37:54Z", "diff": self.body(0)},
        ], total=4)
        provenance = self.start(value=1)
        self.assertEqual(provenance["created_at"], "2026-09-06T09:17:50Z")
        self.assertEqual(provenance["updated_at"], "2026-09-06T10:08:38Z")
        self.assertEqual(provenance["edit_count"], 4)
        self.assertEqual(provenance["last_edited_at"], "2026-09-06T10:08:38Z")
        self.assertEqual(provenance["prior_fiat_required"], 0)
        self.assertIsNone(provenance["reason"])

    def test_an_unreachable_graphql_records_unknown_with_its_reason(self):
        self.env["FAKE_GH_MODE"] = "graphql-unreachable"
        provenance = self.start()
        for field in ("edit_count", "last_edited_at", "prior_fiat_required"):
            self.assertEqual(provenance[field], "unknown", field)
        self.assertIn("failed with exit", provenance["reason"])
        # The REST half is unaffected: it costs no request of its own.
        self.assertEqual(provenance["created_at"], "2026-09-06T09:17:50Z")

    def test_no_readable_field_is_ever_absent_rather_than_unknown(self):
        """An absent field cannot be told apart from a question nobody asked."""
        expected = {"created_at", "updated_at", "edit_count",
                    "last_edited_at", "prior_fiat_required", "reason"}
        self.env["FAKE_GH_MODE"] = "graphql-not-json"
        self.assertEqual(set(self.start()), expected)
        self.tearDown()
        self.setUp()
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        provenance = self.start()
        self.assertEqual(set(provenance), expected)
        self.assertIsNone(provenance["prior_fiat_required"])
        self.assertIn("one revision", provenance["reason"])

    def test_prior_body_text_reaches_no_recorded_surface(self):
        self.edits([
            {"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)},
            {"editedAt": "2026-09-06T09:37:54Z",
             "diff": self.body(0, extra=" " + self.PRIOR_MARKER)},
        ])
        self.env["FAKE_GH_ISSUES"] = json.dumps({self.ISSUE: self.body(1)})
        self.stamps()
        proc = self.run_ctl("init", "--topic", "Provenance topic",
                            "--task-issue", self.ISSUE)
        self.assertNotIn(self.PRIOR_MARKER, proc.stdout)
        self.assertNotIn(self.PRIOR_MARKER, proc.stderr)
        for name in ("state.json", "ledger.jsonl"):
            with open(os.path.join(self.target, ".hexaemeron", name),
                      encoding="utf-8") as handle:
                self.assertNotIn(self.PRIOR_MARKER, handle.read(), name)
        # The value survives the body it came from.
        self.assertEqual(
            self.state()["receipts"]["task_issue_contract"]["provenance"][
                "prior_fiat_required"], 0)

    def test_verify_reports_a_filing_decision_that_moved(self):
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        self.env["FAKE_GH_ISSUES"] = json.dumps({self.ISSUE: self.body(0)})
        proc = self.run_ctl("verify", "--check-filing-decision", expect=1)
        self.assertIn("the filing decision has moved", proc.stdout)
        self.assertIn("fiat_required: recorded 1, now 0", proc.stdout)
        self.assertIn("sha256", proc.stdout)

    def test_verify_says_so_when_the_decision_stands(self):
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        proc = self.run_ctl("verify", "--check-filing-decision")
        self.assertIn("stands as recorded", proc.stdout)
        self.assertNotIn("has moved", proc.stdout)

    def test_a_moved_updated_at_alone_is_not_called_a_body_edit(self):
        """A comment moves `updated_at` and nothing that records the body.

        Reporting that as "the filing decision has moved" names an
        undiscriminated read as a body edit, which is what
        `window-undiscriminated-read` refuses at `init` (S3-R1-01).
        """
        nodes = [{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}]
        self.edits(nodes)
        self.start(value=1)
        # Same body, same edit history; only the undiscriminated field moves.
        self.stamps(updated="2026-09-07T11:00:00Z")
        self.edits(nodes)
        proc = self.run_ctl("verify", "--check-filing-decision", expect=1)
        self.assertNotIn("the filing decision has moved", proc.stdout)
        self.assertIn("nothing that records the body has moved", proc.stdout)
        self.assertIn("not a body edit", proc.stdout)

    def test_a_moved_body_still_reads_as_a_moved_decision(self):
        """The qualifier above does not soften a real body edit."""
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        self.env["FAKE_GH_ISSUES"] = json.dumps({self.ISSUE: self.body(0)})
        self.edits([
            {"editedAt": "2026-09-07T11:00:00Z", "diff": self.body(0)},
            {"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)},
        ])
        self.stamps(updated="2026-09-07T11:00:00Z")
        proc = self.run_ctl("verify", "--check-filing-decision", expect=1)
        self.assertIn("the filing decision has moved", proc.stdout)
        self.assertIn("last_edited_at: recorded 2026-09-06T10:08:38Z, now "
                      "2026-09-07T11:00:00Z", proc.stdout)

    def test_a_deeply_nested_response_records_unknown_rather_than_crashing(self):
        """`RecursionError` is not a `ValueError` (S3-R1-02).

        400000 bytes of `[` sits well inside `GIT_OUTPUT_MAX`, so the byte cap
        is not what bounds this and the parser has to catch it itself.
        """
        module = hexctl_module()
        deep = ("[" * 200_000 + "]" * 200_000).encode("utf-8")
        original = module.bounded_probe
        module.bounded_probe = lambda *a, **k: (0, deep, None)
        try:
            out = module.github_issue_edit_provenance(
                self.dir, "wildcat-finance/example", "74")
        finally:
            module.bounded_probe = original
        self.assertEqual(out["edit_count"], "unknown")
        self.assertEqual(out["prior_fiat_required"], "unknown")
        self.assertIn("not UTF-8 JSON", out["reason"])

    def test_a_boolean_edit_count_is_refused_rather_than_recorded(self):
        """`bool` subclasses `int`, so `true` passed as a count (S3-R1-03).

        It also compared equal to a real count of 1, so a moved edit count
        reported no divergence at all.
        """
        self.env["FAKE_GH_EDITS"] = json.dumps({
            "totalCount": True,
            "nodes": [{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}],
        })
        provenance = self.start(value=1)
        self.assertEqual(provenance["edit_count"], "unknown")
        self.assertIn("did not carry an edit history", provenance["reason"])
        with open(os.path.join(self.target, ".hexaemeron", "state.json"),
                  encoding="utf-8") as handle:
            self.assertNotIn('"edit_count": true', handle.read())

    def test_no_prior_body_text_reaches_the_routed_zero_directive(self):
        """The `0` route prints a directive an agent consumes (S3-R1-05).

        `read_task_issue_contract` builds the provenance block before
        `cmd_init` routes the value, so the reader has held a prior body by the
        time this directive is composed.
        """
        self.edits([
            {"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(0)},
            {"editedAt": "2026-09-06T09:37:54Z",
             "diff": self.body(1, extra=" " + self.PRIOR_MARKER)},
        ])
        self.env["FAKE_GH_ISSUES"] = json.dumps({self.ISSUE: self.body(0)})
        self.stamps()
        proc = self.run_ctl("init", "--topic", "Provenance topic",
                            "--task-issue", self.ISSUE)
        self.assertNotIn(self.PRIOR_MARKER, proc.stdout)
        self.assertNotIn(self.PRIOR_MARKER, proc.stderr)
        directive = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertNotIn("provenance", directive)
        self.assertEqual(directive["do"], "pull-request")

    def test_no_prior_body_text_reaches_the_divergence_report(self):
        """The other printer that holds a prior body (S3-R1-05)."""
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        self.env["FAKE_GH_ISSUES"] = json.dumps({self.ISSUE: self.body(0)})
        self.edits([
            {"editedAt": "2026-09-07T11:00:00Z", "diff": self.body(0)},
            {"editedAt": "2026-09-06T10:08:38Z",
             "diff": self.body(1, extra=" " + self.PRIOR_MARKER)},
        ])
        proc = self.run_ctl("verify", "--check-filing-decision", expect=1)
        self.assertIn("the filing decision has moved", proc.stdout)
        self.assertNotIn(self.PRIOR_MARKER, proc.stdout)
        self.assertNotIn(self.PRIOR_MARKER, proc.stderr)

    def test_init_makes_at_most_two_requests_and_plain_verify_makes_none(self):
        log = os.path.join(self.dir, "transport.log")
        self.env["FAKE_GH_LOG"] = log
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        with open(log, encoding="utf-8") as handle:
            during_init = [json.loads(line) for line in handle if line.strip()]
        self.assertLessEqual(len(during_init), 2, during_init)
        self.assertEqual(
            sum(1 for call in during_init if call[:2] == ["api", "graphql"]), 1)
        os.remove(log)
        self.run_ctl("verify")
        self.run_ctl("status")
        self.assertFalse(
            os.path.exists(log),
            "plain verify or status made a network request",
        )


if __name__ == "__main__":
    unittest.main()
