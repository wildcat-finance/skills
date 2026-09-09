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

import argparse
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
        # `totalCount` matches the node list because the reader refuses a
        # response whose two halves disagree about how many revisions exist
        # (S3-R4-03); this case previously declared 4 against 2 nodes.
        self.edits([
            {"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)},
            {"editedAt": "2026-09-06T09:37:54Z", "diff": self.body(0)},
        ], total=2)
        provenance = self.start(value=1)
        self.assertEqual(provenance["created_at"], "2026-09-06T09:17:50Z")
        self.assertEqual(provenance["updated_at"], "2026-09-06T10:08:38Z")
        self.assertEqual(provenance["edit_count"], 2)
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
        self.assertIn("carried 1 revision", provenance["reason"])

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

    def test_the_reason_names_the_revision_count_the_response_carried(self):
        """A count off the nodes read, not off `totalCount` (S3-R2-03).

        `totalCount` and `nodes` are validated separately, so a response where
        they disagree wrote `edit_count: 4` beside a sentence claiming one
        revision, and an empty node list claimed one revision of a body it had
        seen nothing of. Neither count was read.

        Both halves now carry counts that agree, because a response whose two
        halves disagree is refused outright (S3-R4-03). The empty list is the
        discriminating input either way: the wording this repair replaced said
        "the body has one revision" for a response carrying none.
        """
        self.edits([], total=0)
        provenance = self.start(value=1)
        self.assertEqual(provenance["edit_count"], 0)
        self.assertIn("carried 0 revisions", provenance["reason"])
        self.tearDown()
        self.setUp()
        self.edits(
            [{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}], total=1)
        provenance = self.start(value=1)
        self.assertEqual(provenance["edit_count"], 1)
        self.assertIn("carried 1 revision", provenance["reason"])
        self.assertNotIn("the body has", provenance["reason"])

    def test_an_unreadable_history_now_is_not_called_a_moved_decision(self):
        """`unknown` at the current end is a failed read, not a body edit.

        Comparing the sentinel as a value reported `edit_count: recorded 1, now
        unknown` under "the filing decision has moved since this run read it",
        which is the undiscriminated-read reading S3-R1-01 removed from
        `updated_at`, arriving through the transport instead (S3-R2-01).
        """
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        self.env["FAKE_GH_MODE"] = "graphql-unreachable"
        proc = self.run_ctl("verify", "--check-filing-decision")
        self.assertNotIn("has moved", proc.stdout)
        self.assertIn("edit_count: not compared", proc.stdout)
        self.assertIn("last_edited_at: not compared", proc.stdout)
        self.assertIn("the current read returned `unknown`", proc.stdout)

    def test_an_unreadable_history_then_is_not_called_a_moved_decision(self):
        """The same in reverse: `unknown` recorded, a value read now."""
        self.env["FAKE_GH_MODE"] = "graphql-unreachable"
        self.start(value=1)
        self.env.pop("FAKE_GH_MODE")
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        proc = self.run_ctl("verify", "--check-filing-decision")
        self.assertNotIn("has moved", proc.stdout)
        self.assertIn("edit_count: not compared", proc.stdout)
        self.assertIn("recorded it as `unknown`", proc.stdout)

    def test_two_unreadable_reads_do_not_read_as_a_history_that_stands(self):
        """The pass `graphql-transport` refuses (S3-R2-01).

        Two `unknown` sentinels compared equal, so a run that never reached
        GraphQL at either end printed "the filing decision stands as recorded"
        and exited 0 over an edit history nothing had ever read.
        """
        self.env["FAKE_GH_MODE"] = "graphql-unreachable"
        self.start(value=1)
        proc = self.run_ctl("verify", "--check-filing-decision")
        self.assertNotIn("the filing decision stands as recorded\n", proc.stdout)
        self.assertIn("could not be compared", proc.stdout)
        self.assertIn(
            "neither this run's read nor the current one could read it",
            proc.stdout,
        )

    def test_a_receipt_with_no_provenance_block_is_not_a_moved_decision(self):
        """A run started before this reader existed records no block at all.

        `as_dict` turned the absence into `{}` and every provenance field
        compared `None` against a real value, so an untouched issue read as
        three divergences and exit 1 (S3-R2-01).
        """
        module = hexctl_module()
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        recorded = dict(
            self.state()["receipts"]["task_issue_contract"])
        recorded.pop("provenance")
        saved = dict(os.environ)
        os.environ.update(
            {key: value for key, value in self.env.items()
             if key.startswith("FAKE_GH") or key == "PATH"})
        try:
            result = module.filing_decision_divergence(
                self.dir, {"receipts": {"task_issue_contract": recorded}})
        finally:
            os.environ.clear()
            os.environ.update(saved)
        # Unpacked after the length is asserted, so a reader that reports no
        # uncomparable fields fails this case rather than erroring in it and
        # costing the round its Elenchus verdict.
        self.assertEqual(len(result), 3, "no uncomparable fields are reported")
        divergences, uncomparable, skipped = result
        self.assertEqual(divergences, [], divergences)
        self.assertEqual(skipped, "")
        self.assertEqual(
            [entry["field"] for entry in uncomparable],
            ["updated_at", "edit_count", "last_edited_at"],
        )
        for entry in uncomparable:
            self.assertIn("carries no provenance block", entry["why"])

    EMPTY_BODY_SHA256 = (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )

    def test_a_body_that_is_not_text_is_not_a_moved_decision(self):
        """One response, two readers, opposite answers (S3-R3-01).

        `init` refuses a body that is not text in the transport shape. The
        divergence reader substituted `""` for it and reported the SHA-256 of
        the empty string as the issue's current body digest, under "the filing
        decision has moved since this run read it".
        """
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        self.env["FAKE_GH_MODE"] = "issue-body-not-text"
        proc = self.run_ctl("verify", "--check-filing-decision", expect=2)
        self.assertIn("body that is not text", proc.stderr)
        self.assertNotIn(self.EMPTY_BODY_SHA256, proc.stdout)
        self.assertNotIn("has moved", proc.stdout)

    def test_a_body_above_the_cap_is_refused_rather_than_hashed(self):
        """`init` dies on a body above the cap; the re-read parsed it.

        The same two-readers-one-response split as the case above, on the
        second of the two rules `init` applies to a body (S3-R3-01).
        """
        module = hexctl_module()
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        over = self.body(1) + "x" * (module.ISSUE_BODY_BYTES_MAX + 1)
        payload = json.dumps({
            "number": 74, "body": over, "title": "t", "labels": [],
            "created_at": "2026-09-06T09:17:50Z",
            "updated_at": "2026-09-06T10:08:38Z",
        }).encode("utf-8")
        original = module.bounded_probe
        module.bounded_probe = lambda *a, **k: (0, payload, None)
        try:
            with self.assertRaises(SystemExit):
                module.filing_decision_divergence(self.dir, self.state())
        finally:
            module.bounded_probe = original

    def test_an_unreadable_decision_now_is_not_reported_as_no_decision(self):
        """A body declaring the line twice is not a body declaring nothing.

        `issue_contract_faults` returns `None` for a body it cannot read one
        decision out of, and the fault saying why was dropped, so the report
        read `fiat_required: recorded 1, now None` (S3-R3-02).
        """
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.start(value=1)
        twice = self.body(1).replace(
            "Fiat-Required: 1", "Fiat-Required: 1\nFiat-Required: 0")
        self.env["FAKE_GH_ISSUES"] = json.dumps({self.ISSUE: twice})
        proc = self.run_ctl("verify", "--check-filing-decision", expect=1)
        self.assertNotIn("now None", proc.stdout)
        self.assertIn("fiat_required: not compared", proc.stdout)
        self.assertIn("2 times", proc.stdout)

    def test_an_unreadable_edit_time_is_not_called_a_moved_decision(self):
        """A node carrying no readable `editedAt` was read as no edit time.

        The sentinel closed the transport-level version of this in S3-R2-01,
        and the field-level version stayed: `last_edited_at` fell to `None`,
        which the comparison reads as a value, so an issue whose body never
        moved reported `last_edited_at: recorded None, now <time>` under "the
        filing decision has moved since this run read it" and exited 1
        (S3-R4-01). `last_edited_at` is not in
        `UNDISCRIMINATED_DIVERGENCE_FIELDS`, so it carries the strong headline
        on its own.
        """
        self.edits([{"diff": self.body(1)}, {"diff": self.body(0)}], total=2)
        provenance = self.start(value=1)
        self.edits([
            {"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)},
            {"diff": self.body(0)},
        ], total=2)
        # Exit 0 first, because the defect is an exit 1 over an unmoved body
        # and the harness reports the whole report with it.
        proc = self.run_ctl("verify", "--check-filing-decision")
        self.assertNotIn("has moved", proc.stdout)
        self.assertIn("last_edited_at: not compared", proc.stdout)
        self.assertIn("recorded it as `unknown`", proc.stdout)
        self.assertEqual(provenance["last_edited_at"], "unknown")
        self.assertIn("no readable `editedAt`", provenance["reason"])

    def test_an_unread_rest_stamp_is_not_called_a_touched_issue(self):
        """A `updated_at` the response did not carry as text is not a value.

        `rest_filing_stamps` coerced it to `None` on both sides, so the two
        builders agreed, and then the comparison read that absence as data: a
        run whose `init` got a non-string stamp reported "the issue has been
        touched since this run read it" against an issue nothing had touched
        (S3-R4-02).
        """
        self.edits([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}])
        self.env["FAKE_GH_ISSUES"] = json.dumps({self.ISSUE: self.body(1)})
        self.env["FAKE_GH_ISSUE_STAMPS"] = json.dumps(
            {"default": {"created_at": "2026-09-06T09:17:50Z", "updated_at": 17}}
        )
        self.init("Provenance topic", task_issue=self.ISSUE)
        provenance = self.state()["receipts"]["task_issue_contract"]["provenance"]
        self.stamps()
        proc = self.run_ctl("verify", "--check-filing-decision")
        self.assertNotIn("has been touched", proc.stdout)
        self.assertNotIn("has moved", proc.stdout)
        self.assertIn("updated_at: not compared", proc.stdout)
        self.assertEqual(provenance["updated_at"], "unknown")

    def test_a_count_without_its_nodes_is_not_a_history_that_was_read(self):
        """A response answering the same question twice, believed both times.

        `totalCount` and `len(nodes)` were validated separately and never
        against each other, so a response claiming 3 revisions and carrying
        none recorded `edit_count: 3` beside `last_edited_at: None` -- and
        that `None` means "read, and there is no last-edit time", which this
        response did not say. The comparison then read it as a value: against
        the same three revisions delivered, `verify --check-filing-decision`
        printed "the filing decision has moved since this run read it" on
        `last_edited_at: recorded None, now 2026-09-06T10:08:38Z` and exited 1,
        over a body whose digest, decision, `updated_at` and `edit_count` were
        all identical (S3-R4-03). This is S3-R4-01's failure reached through
        the count rather than through a node's `editedAt`.
        """
        self.edits([], total=3)
        provenance = self.start(value=1)
        self.edits([
            {"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)},
            {"editedAt": "2026-09-06T09:37:54Z", "diff": self.body(1)},
            {"editedAt": "2026-09-06T09:17:50Z", "diff": self.body(1)},
        ], total=3)
        # Exit 0 first: the defect is an exit 1 over an unmoved body, and the
        # harness prints the whole report with the returncode assertion.
        proc = self.run_ctl("verify", "--check-filing-decision")
        self.assertNotIn("has moved", proc.stdout)
        self.assertIn("last_edited_at: not compared", proc.stdout)
        self.assertIn("edit_count: not compared", proc.stdout)
        self.assertIn("recorded it as `unknown`", proc.stdout)
        for field in ("edit_count", "last_edited_at", "prior_fiat_required"):
            self.assertEqual(provenance[field], "unknown", field)
        self.assertIn("claimed 3 revisions and carried 0", provenance["reason"])

    def test_a_count_and_a_node_list_that_disagree_are_never_read_as_values(self):
        """Both directions of the disagreement, and a count below zero.

        The mirror recorded `edit_count: 0` beside a `last_edited_at` read out
        of a node, and a negative `totalCount` passed the type check and the
        ceiling and recorded `edit_count: -3`. One rule refuses all three: no
        list length can equal a negative count either (S3-R4-03).
        """
        cases = (
            ([], 3, "claimed 3 revisions and carried 0"),
            ([{"editedAt": "2026-09-06T10:08:38Z", "diff": self.body(1)}], 0,
             "claimed 0 revisions and carried 1"),
            ([], -3, "claimed -3 revisions and carried 0"),
        )
        for index, (nodes, total, expected) in enumerate(cases):
            if index:
                self.tearDown()
                self.setUp()
            with self.subTest(total=total, carried=len(nodes)):
                self.edits(nodes, total=total)
                provenance = self.start(value=1)
                for field in ("edit_count", "last_edited_at",
                              "prior_fiat_required"):
                    self.assertEqual(provenance[field], "unknown", field)
                self.assertIn(expected, provenance["reason"])
                # The REST half costs no request of its own and is unaffected.
                self.assertEqual(provenance["created_at"],
                                 "2026-09-06T09:17:50Z")

    def test_a_deeply_nested_rest_response_refuses_rather_than_crashing(self):
        """The REST sibling of the GraphQL parser S3-R1-02 repaired.

        Step 3 gave `github_rest` a second call site inside
        `filing_decision_divergence`, and its `except ValueError` does not
        reach `RecursionError` (S3-R3-03). The exception is caught rather than
        allowed to propagate, because an error rather than an assertion
        failure is what `elenchus classify` reads as inconclusive.
        """
        module = hexctl_module()
        deep = ("[" * 200_000 + "]" * 200_000).encode("utf-8")
        self.assertLess(len(deep), module.GIT_OUTPUT_MAX)
        original = module.bounded_probe
        module.bounded_probe = lambda *a, **k: (0, deep, None)
        outcome = "returned a payload"
        try:
            module.github_rest(
                self.dir, "repos/wildcat-finance/example/issues/74",
                "task issue wildcat-finance/example#74")
        except SystemExit as exc:
            outcome = f"refused with exit {exc.code}"
        except RecursionError:
            outcome = "walked off the interpreter's stack"
        finally:
            module.bounded_probe = original
        self.assertEqual(outcome, "refused with exit 2")


class VerifyFlagCompositionTests(unittest.TestCase):
    """`--observations` used to end the command before the filing check ran."""

    def test_the_observations_flag_does_not_swallow_the_filing_check(self):
        """Both flags, one comparison dropped in silence (S3-R2-02).

        The observation branch returned, so a caller passing both got an `ok:`
        line and exit 0 with the filing decision never compared. Driven at the
        command rather than through the fixture, because a passing
        `--observations` needs a bound observation prefix this module has no
        other use for.
        """
        module = hexctl_module()
        calls = []
        originals = {
            name: getattr(module, name)
            for name in ("verify_run", "load_state",
                         "verify_observation_bindings",
                         "filing_decision_divergence")
        }
        module.verify_run = lambda base_dir: 1
        module.load_state = lambda base_dir: {"receipts": {}}
        module.verify_observation_bindings = lambda base_dir, state: (1, 0)
        module.filing_decision_divergence = (
            lambda base_dir, state: (calls.append(1), ([], [], ""))[1])
        try:
            module.cmd_verify(argparse.Namespace(
                dir=".", observations=True, check_filing_decision=True))
        finally:
            for name, value in originals.items():
                setattr(module, name, value)
        self.assertEqual(len(calls), 1, "the filing decision was never compared")


if __name__ == "__main__":
    unittest.main()
