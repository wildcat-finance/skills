"""The filing contract: one decision, and every outstanding item disposed of.

Two mechanical questions are asked of an issue before work starts against it,
and the second is asked again of the run's own pull request body before its
delivery merges.

1. `Fiat-Required` is 1 when the work needs a Fiat run and 0 when one
   independent pull request will do. `init` reads it and refuses to create any
   state, worktree or branch on a 0, so the run does not get a chance to start.
2. The `carryover` block gives every outstanding, carried-forward or
   unaddressed item an issue of its own, a pointer at the issue that already
   carries it, or a stated reason it earns neither.

Both are shape checks, deliberately. A row that files a real concern against
the wrong issue passes, and so does a `none` reason nobody should have
accepted; whether the disposition was right stays with the reviewer. What
cannot happen any more is a filing that never answered, or a run that reached
integration with its leftovers named in prose and disposed of nowhere.
"""

import json
import os
import subprocess
import unittest

try:
    from .hexctl_harness import HexctlCase, hexctl_module, SUITE
except ImportError:
    from hexctl_harness import HexctlCase, hexctl_module, SUITE


ISSUE = "https://github.com/wildcat-finance/example/issues/74"
FILED = "https://github.com/wildcat-finance/skills/issues/1041"
EXISTING = "https://github.com/wildcat-finance/skills/issues/842"


def body(decision="Fiat-Required: 1", rows="none | none | nothing is carried\n",
         block=True):
    """One candidate issue body, with either part removable."""
    text = "An issue.\n"
    if decision is not None:
        text += f"\n{decision}\n"
    if block:
        text += "\n```carryover\n" + rows + "```\n"
    return text


def with_status(block, rest="An issue.\n\nFiat-Required: 1\n"):
    """One candidate body carrying the given status-block text above its prose."""
    return block + "\n" + rest


class StatusBlockTests(unittest.TestCase):
    """The status block ADR-014's amendment authorises, read directly.

    The block records an open issue's current status where a census reads it.
    Its shape is checked and its content is not: a block claiming the issue is
    superseded when it is not passes here, exactly as a `none` carryover row
    nobody should have accepted passes. What cannot happen is a body that opens
    a block and never closes it, opens two, or is judged to carry one because it
    quoted the markers as an example.
    """

    @classmethod
    def setUpClass(cls):
        cls.hexctl = hexctl_module()

    def span(self, text):
        return self.hexctl.status_block_span(text, "candidate")

    def test_a_well_formed_block_reports_its_span(self):
        span, faults = self.span(with_status(
            "<!-- status:start -->\nSuperseded in part by #1030.\n<!-- status:end -->\n"))
        self.assertEqual(faults, [], faults)
        self.assertEqual(span, (1, 3))

    def test_a_body_with_no_block_is_not_a_fault(self):
        """Most bodies carry none, so absence is ordinary rather than a refusal."""
        span, faults = self.span("An issue.\n\nFiat-Required: 1\n")
        self.assertEqual(faults, [])
        self.assertIsNone(span)

    def test_markers_inside_a_fence_carry_no_block(self):
        """A body quoting the delimiters as an example decides nothing."""
        span, faults = self.span(
            "An issue.\n\n```text\n<!-- status:start -->\n<!-- status:end -->\n```\n")
        self.assertEqual(faults, [])
        self.assertIsNone(span)

    def test_an_unterminated_block_is_refused(self):
        """It must not consume the rest of the body in silence."""
        span, faults = self.span(with_status("<!-- status:start -->\nStill open.\n"))
        self.assertIsNone(span)
        self.assertTrue(any("never closed" in fault for fault in faults), faults)

    def test_two_opened_blocks_are_no_statement(self):
        span, faults = self.span(with_status(
            "<!-- status:start -->\nOne.\n<!-- status:end -->\n"
            "<!-- status:start -->\nTwo.\n<!-- status:end -->\n"))
        self.assertIsNone(span)
        self.assertTrue(any("more than one" in fault for fault in faults), faults)

    def test_a_closer_without_an_opener_is_refused(self):
        span, faults = self.span(with_status("<!-- status:end -->\n"))
        self.assertIsNone(span)
        self.assertTrue(any("closed before it opened" in fault for fault in faults), faults)

    def test_a_stray_closer_after_a_closed_block_is_refused(self):
        """The rule holds past the first block, not only before it.

        An unmatched delimiter left in a body is the shape a half-finished edit
        leaves behind, and reporting it clean tells the editor the opposite.
        """
        span, faults = self.span(with_status(
            "<!-- status:start -->\nOne.\n<!-- status:end -->\n\nProse.\n"
            "<!-- status:end -->\n"))
        self.assertIsNone(span)
        self.assertTrue(any("closed before it opened" in fault for fault in faults), faults)

    def test_a_control_character_in_the_block_is_refused(self):
        """Matching the carryover row reader, which refuses them by name."""
        span, faults = self.span(with_status(
            "<!-- status:start -->\nSuperseded\x07 by #1030.\n<!-- status:end -->\n"))
        self.assertIsNone(span)
        self.assertTrue(any("control character" in fault for fault in faults), faults)

    def test_the_block_reaches_the_contract_record(self):
        record, faults = self.hexctl.issue_contract_faults(with_status(
            "<!-- status:start -->\nSuperseded in part by #1030.\n<!-- status:end -->\n",
            rest=body(),
        ), "candidate")
        self.assertEqual(faults, [], faults)
        self.assertEqual(record["status_block"], [1, 3])


class ContractParserTests(unittest.TestCase):
    """The grammar, read directly. No network, no state, no run."""

    @classmethod
    def setUpClass(cls):
        cls.hexctl = hexctl_module()

    def faults(self, text):
        _, faults = self.hexctl.issue_contract_faults(text, "candidate")
        return faults

    def record(self, text):
        record, faults = self.hexctl.issue_contract_faults(text, "candidate")
        self.assertEqual(faults, [], faults)
        return record

    def test_a_complete_body_parses_into_the_decision_and_its_rows(self):
        record = self.record(body(
            rows=f"plugin-ci | filed | {FILED}\n"
                 f"xray-drift | duplicate | {EXISTING}\n"
                 "nit | none | fixed in the same commit\n"
        ))
        self.assertEqual(record["fiat_required"], 1)
        self.assertEqual(
            [(row["id"], row["disposition"]) for row in record["carryover"]],
            [("plugin-ci", "filed"),
             ("xray-drift", "duplicate"),
             ("nit", "none")],
        )
        self.assertEqual(len(record["sha256"]), 64)

    def test_both_questions_are_reported_together(self):
        """A filer fixing one does not discover the other on the next attempt."""
        faults = self.faults("An issue with neither answer.\n")
        self.assertEqual(len(faults), 2, faults)
        self.assertIn("Fiat-Required", faults[0])
        self.assertIn("carryover", faults[1])

    def test_a_missing_decision_names_both_values(self):
        fault = self.faults(body(decision=None))[0]
        self.assertIn("Fiat-Required: 1", fault)
        self.assertIn("Fiat-Required: 0", fault)

    def test_two_decisions_are_no_decision(self):
        text = body(decision="Fiat-Required: 1\nFiat-Required: 0")
        self.assertIn("made no decision", self.faults(text)[0])

    def test_a_value_that_is_neither_zero_nor_one_is_refused(self):
        for value in ("2", "yes", "true", "", "01", "1.0", "-1", "0 1"):
            with self.subTest(value=value):
                faults = self.faults(body(decision=f"Fiat-Required: {value}"))
                self.assertTrue(faults, value)

    def test_invisible_whitespace_around_the_value_decides_nothing_by_itself(self):
        """A trailing space is not a third answer."""
        record = self.record(body(decision="Fiat-Required: 1   "))
        self.assertEqual(record["fiat_required"], 1)

    def test_zero_and_one_both_parse(self):
        self.assertEqual(self.record(body("Fiat-Required: 0"))["fiat_required"], 0)
        self.assertEqual(self.record(body("Fiat-Required: 1"))["fiat_required"], 1)

    def test_the_decision_survives_the_shapes_a_filer_writes_it_in(self):
        for spelling in ("Fiat-Required: 1",
                         "- Fiat-Required: 1",
                         "**Fiat-Required**: 1",
                         "Fiat-Required:1"):
            with self.subTest(spelling=spelling):
                record = self.record(body(decision=spelling))
                self.assertEqual(record["fiat_required"], 1)

    def test_a_quoted_specimen_decides_nothing(self):
        """The line inside a fence is evidence about syntax, not a decision."""
        text = ("An issue.\n\n```text\nFiat-Required: 0\n```\n"
                "\n```carryover\nnone | none | nothing\n```\n")
        self.assertIn("declares no `Fiat-Required` line", self.faults(text)[0])

    def test_an_absent_block_is_not_an_empty_one(self):
        absent = self.faults(body(block=False))
        self.assertIn("carries no `carryover` block", absent[0])
        empty = self.faults(body(rows=""))
        self.assertIn("holds no rows", empty[0])
        self.assertIn("none | none |", empty[0])

    def test_a_row_must_carry_exactly_three_fields(self):
        for row in ("just-an-id\n", f"an-id | filed\n",
                    f"an-id | filed | {FILED} | extra\n"):
            with self.subTest(row=row):
                self.assertIn("field(s), not the three",
                              self.faults(body(rows=row))[0])

    def test_an_id_must_be_kebab_case_and_used_once(self):
        self.assertIn("not kebab-case",
                      self.faults(body(rows=f"Not_Kebab | filed | {FILED}\n"))[0])
        repeated = self.faults(body(
            rows=f"same-id | filed | {FILED}\nsame-id | duplicate | {EXISTING}\n"))
        self.assertIn("repeats the id", repeated[0])

    def test_an_unknown_disposition_is_refused_by_name(self):
        fault = self.faults(body(rows=f"an-id | maybe | {FILED}\n"))[0]
        self.assertIn("`filed`", fault)
        self.assertIn("`duplicate`", fault)
        self.assertIn("`none`", fault)

    def test_filed_and_duplicate_must_point_at_a_real_issue_url(self):
        for disposition in ("filed", "duplicate"):
            for reference in ("", "soon", "#1041", "wildcat-finance/skills#1041",
                              "https://github.com/wildcat-finance/skills/pull/1041"):
                with self.subTest(disposition=disposition, reference=reference):
                    faults = self.faults(
                        body(rows=f"an-id | {disposition} | {reference}\n"))
                    self.assertIn("canonical GitHub issue URL", faults[0])

    def test_a_none_row_must_say_why(self):
        self.assertIn("must say why",
                      self.faults(body(rows="an-id | none |\n"))[0])
        long_reason = "x" * (self.hexctl.CARRYOVER_REASON_BYTES_MAX + 1)
        self.assertIn("longer than",
                      self.faults(body(rows=f"an-id | none | {long_reason}\n"))[0])

    def test_the_reserved_none_id_is_only_valid_alone(self):
        self.assertEqual(
            self.record(body(rows="none | none | nothing is carried\n"))["carryover"],
            [{"id": "none", "disposition": "none",
              "reference": "nothing is carried"}],
        )
        beside = self.faults(
            body(rows=f"none | none | nothing\nan-id | filed | {FILED}\n"))
        self.assertIn("only valid as the sole row", beside[0])
        wrong = self.faults(body(rows=f"none | filed | {FILED}\n"))
        self.assertIn("only valid as the sole row", wrong[0])

    def test_more_than_one_block_is_no_authoritative_block(self):
        text = (body(rows=f"an-id | filed | {FILED}\n")
                + "\n```carryover\nother-id | none | why\n```\n")
        self.assertIn("more than one `carryover` block", self.faults(text)[0])

    def test_an_unclosed_block_is_refused(self):
        text = "An issue.\n\nFiat-Required: 1\n\n```carryover\nan-id | none | why\n"
        self.assertIn("is not closed", self.faults(text)[0])

    def test_a_fence_carrying_more_than_the_info_string_is_refused(self):
        text = ("An issue.\n\nFiat-Required: 1\n\n"
                "```carryover extra\nan-id | none | why\n```\n")
        self.assertIn("that exact info string", self.faults(text)[0])

    def test_the_row_count_is_capped_rather_than_truncated(self):
        rows = "".join(
            f"item-{index} | none | why\n"
            for index in range(self.hexctl.CARRYOVER_ROWS_MAX + 1)
        )
        self.assertIn("went unchecked", self.faults(body(rows=rows))[0])


class IssueCheckCommandTests(HexctlCase):
    """`issue-check`, the command run before anything is filed."""

    def candidate(self, text, name="candidate.md"):
        return self.write(name, text)

    def test_a_complete_candidate_reports_its_decision_and_dispositions(self):
        self.candidate(body(rows=f"plugin-ci | filed | {FILED}\n"
                                 f"xray-drift | duplicate | {EXISTING}\n"))
        proc = self.run_ctl("issue-check", "--body", "candidate.md")
        self.assertIn("clean", proc.stdout)
        self.assertIn("Fiat-Required: 1 (a Fiat run)", proc.stdout)
        self.assertIn("2 row(s), 1 filed, 1 pointing at an existing issue",
                      proc.stdout)
        self.assertIn(f"plugin-ci | filed | {FILED}", proc.stdout)

    def test_a_zero_candidate_is_clean_because_zero_is_an_answer(self):
        self.candidate(body("Fiat-Required: 0"))
        proc = self.run_ctl("issue-check", "--body", "candidate.md")
        self.assertIn("Fiat-Required: 0 (one independent pull request)",
                      proc.stdout)

    def test_findings_exit_one_and_are_all_reported(self):
        self.candidate("An issue with neither answer.\n")
        proc = self.run_ctl("issue-check", "--body", "candidate.md", expect=1)
        self.assertIn("Fiat-Required", proc.stderr)
        self.assertIn("carryover", proc.stderr)
        self.assertIn("2 finding(s)", proc.stderr)

    def test_exactly_one_source_is_required(self):
        proc = self.run_ctl("issue-check", expect=2)
        self.assertIn("exactly one", proc.stderr)
        proc = self.run_ctl("issue-check", "--body", "candidate.md",
                            "--issue", ISSUE, expect=2)
        self.assertIn("exactly one", proc.stderr)

    def test_an_unreadable_or_non_utf8_candidate_refuses(self):
        proc = self.run_ctl("issue-check", "--body", "absent.md", expect=2)
        self.assertIn("cannot be read", proc.stderr)
        path = os.path.join(self.target, "binary.md")
        with open(path, "wb") as handle:
            handle.write(b"Fiat-Required: 1\n\xff\xfe\n")
        proc = self.run_ctl("issue-check", "--body", "binary.md", expect=2)
        self.assertIn("not UTF-8", proc.stderr)

    def test_a_filed_issue_can_be_read_over_rest(self):
        self.env["FAKE_GH_ISSUES"] = json.dumps({
            ISSUE: body(rows=f"an-id | duplicate | {EXISTING}\n")
        })
        proc = self.run_ctl("issue-check", "--issue", ISSUE)
        self.assertIn("wildcat-finance/example#74: clean", proc.stdout)
        self.assertIn("1 pointing at an existing issue", proc.stdout)

    def test_a_url_that_is_not_a_github_issue_refuses(self):
        proc = self.run_ctl("issue-check", "--issue", "https://x/issues/74",
                            expect=2)
        self.assertIn("not a canonical GitHub issue URL", proc.stderr)


class InitFilingGateTests(HexctlCase):
    """What `init` does with the decision the issue filed."""

    def set_issue(self, text):
        self.env["FAKE_GH_ISSUES"] = json.dumps({ISSUE: text})

    def test_a_one_starts_the_run_and_the_receipt_records_the_read(self):
        self.set_issue(body(rows=f"plugin-ci | filed | {FILED}\n"))
        self.init("Gated topic", task_issue=ISSUE)
        contract = self.state()["receipts"]["task_issue_contract"]
        self.assertEqual(contract["issue"], ISSUE)
        self.assertEqual(contract["repository"], "wildcat-finance/example")
        self.assertEqual(contract["number"], "74")
        self.assertEqual(contract["fiat_required"], 1)
        self.assertEqual(contract["carryover"],
                         [{"id": "plugin-ci", "disposition": "filed",
                           "reference": FILED}])
        self.assertEqual(len(contract["sha256"]), 64)

    def test_a_zero_refuses_before_any_state_worktree_or_branch_exists(self):
        self.set_issue(body("Fiat-Required: 0"))
        proc = self.run_ctl("init", "--topic", "Not a run", "--task-issue",
                            ISSUE, expect=1)
        self.assertIn("Fiat-Required: 0", proc.stderr)
        self.assertIn("one independent pull request", proc.stderr)
        self.assertIn("No run state, worktree or branch was created",
                      proc.stderr)
        self.assertFalse(
            os.path.exists(os.path.join(self.dir, ".hexaemeron", "state.json")))
        self.assertFalse(
            os.path.exists(os.path.join(self.dir, ".hexaemeron", "worktree")))
        branches = subprocess.run(
            ["git", "branch", "--format=%(refname:short)"],
            cwd=self.dir, capture_output=True, text=True, check=True).stdout
        self.assertNotIn("fiat/74-not-a-run", branches.split())

    def test_an_issue_that_declares_nothing_refuses_and_says_what_to_add(self):
        self.set_issue("An issue filed before the contract existed.\n")
        proc = self.run_ctl("init", "--topic", "t", "--task-issue", ISSUE,
                            expect=2)
        self.assertIn("the filing contract is not satisfied", proc.stderr)
        self.assertIn("Fiat-Required", proc.stderr)
        self.assertIn("carryover", proc.stderr)
        self.assertIn(ISSUE, proc.stderr)
        self.assertFalse(
            os.path.exists(os.path.join(self.dir, ".hexaemeron", "state.json")))

    def test_a_malformed_triage_block_refuses_even_when_the_decision_is_one(self):
        self.set_issue(body(rows="an-id | duplicate | soon\n"))
        proc = self.run_ctl("init", "--topic", "t", "--task-issue", ISSUE,
                            expect=2)
        self.assertIn("canonical GitHub issue URL", proc.stderr)

    def test_a_run_naming_no_issue_records_the_nulls_and_says_so(self):
        proc = self.run_ctl("init", "--topic", "Ungated topic")
        self.assertIn("names no task issue", proc.stderr)
        self.write_design_evidence()
        contract = self.state()["receipts"]["task_issue_contract"]
        self.assertIsNone(contract["issue"])
        self.assertIsNone(contract["fiat_required"])
        self.assertEqual(contract["carryover"], [])
        self.assertIn("no task issue", contract["reason"])

    def test_a_tracker_that_is_not_github_records_the_gap_rather_than_a_one(self):
        proc = self.run_ctl("init", "--topic", "Elsewhere", "--task-issue",
                            "https://x/issues/74")
        self.assertIn("is not a GitHub issue", proc.stderr)
        self.write_design_evidence()
        contract = self.state()["receipts"]["task_issue_contract"]
        self.assertEqual(contract["issue"], "https://x/issues/74")
        self.assertIsNone(contract["fiat_required"])
        self.assertIn("not a GitHub issue", contract["reason"])

    def test_a_read_github_never_answered_is_a_transport_failure(self):
        self.env["FAKE_GH_MODE"] = "issue-missing"
        proc = self.run_ctl("init", "--topic", "t", "--task-issue", ISSUE,
                            expect=2)
        self.assertIn("was not answered", proc.stderr)
        self.assertIn("transport failure", proc.stderr)
        self.assertFalse(
            os.path.exists(os.path.join(self.dir, ".hexaemeron", "state.json")))

    def test_a_body_that_is_not_text_refuses_in_the_transport_shape(self):
        self.env["FAKE_GH_MODE"] = "issue-body-not-text"
        proc = self.run_ctl("init", "--topic", "t", "--task-issue", ISSUE,
                            expect=2)
        self.assertIn("body that is not text", proc.stderr)

    def test_the_recorded_read_cannot_be_rewritten_afterwards(self):
        self.set_issue(body("Fiat-Required: 1"))
        self.init("Gated topic", task_issue=ISSUE)
        proc = self.run_ctl(
            "record", "task_issue_contract",
            json.dumps({"fiat_required": 1, "carryover": []}), expect=2)
        self.assertIn("only `hexctl init` writes it", proc.stderr)
        self.assertEqual(
            self.state()["receipts"]["task_issue_contract"]["fiat_required"], 1)

    def test_the_decision_reaches_the_ledger_as_well_as_the_receipt(self):
        self.set_issue(body("Fiat-Required: 1"))
        self.init("Gated topic", task_issue=ISSUE)
        path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(path, encoding="utf-8") as handle:
            first = json.loads(handle.readline())
        self.assertEqual(first["event"], "init")
        self.assertEqual(first["data"]["task_issue_contract"]["fiat_required"], 1)


class IntegrationTriageGateTests(HexctlCase):
    """Integration does not proceed on leftovers nothing was decided about."""

    def reach_integrate(self):
        self.to_steps(("One",))
        self.run_ctl("record", "security_suite", SUITE)
        self.finish_step(1)
        self.merge_stack()
        return ["done", "integrate", "--pr-url",
                "https://github.com/wildcat-finance/example/pull/2",
                "--merge-commit", "f" * 40]

    def test_the_integrate_directive_states_the_shape_before_it_is_written(self):
        """The prose phase should not have to guess it from a refusal."""
        self.reach_integrate()
        required = self.next_json()["carried_forward"]
        self.assertEqual(required["path"], ".hexaemeron/run-pr.md")
        self.assertEqual(required["heading"], "## Carried forward")
        self.assertEqual(required["block"], "carryover")
        self.assertEqual(required["dispositions"], ["filed", "duplicate", "none"])
        self.assertIn("<id> | <disposition> | <reference>", required["row"])
        self.assertIn("never file an issue merely to fill a row",
                      required["rule"])

    def test_prose_that_disposes_of_nothing_stops_integration(self):
        args = self.reach_integrate()
        self.write_run_pr(carried="- the CI workflow is still missing\n")
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("carries no `carryover` block", proc.stderr)
        self.assertIn("compared against what is already filed", proc.stderr)

    def test_a_row_pointing_nowhere_stops_integration(self):
        args = self.reach_integrate()
        self.write_run_pr(rows="plugin-ci | filed | later\n")
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("canonical GitHub issue URL", proc.stderr)
        self.assertIn("Integration cannot proceed", proc.stderr)

    def test_a_block_outside_the_section_does_not_count(self):
        """A later section cannot answer this one's question."""
        args = self.reach_integrate()
        self.write(
            os.path.join(".hexaemeron", "run-pr.md"),
            "Run body.\n\n## Carried forward\n\n- the CI workflow is missing\n"
            "\n## Checks\n\n```carryover\nplugin-ci | filed | " + FILED
            + "\n```\n",
        )
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("carries no `carryover` block", proc.stderr)

    def test_a_disposed_section_integrates_and_the_receipt_keeps_the_rows(self):
        args = self.reach_integrate()
        self.write_run_pr(
            rows=f"plugin-ci | filed | {FILED}\n"
                 f"xray-drift | duplicate | {EXISTING}\n"
                 "nit | none | fixed in the same commit\n")
        self.run_ctl(*args)
        receipt = self.state()["receipts"]["integrate"]["carried_forward"]
        self.assertEqual(receipt["filed"], ["plugin-ci"])
        self.assertEqual(receipt["duplicates"], ["xray-drift"])
        self.assertEqual(
            [row["reference"] for row in receipt["carryover"]],
            [FILED, EXISTING, "fixed in the same commit"],
        )
        self.run_ctl("verify")

    def test_a_run_that_leaves_nothing_still_says_so_in_a_row(self):
        args = self.reach_integrate()
        self.write_run_pr()
        self.run_ctl(*args)
        receipt = self.state()["receipts"]["integrate"]["carried_forward"]
        self.assertEqual(receipt["filed"], [])
        self.assertEqual(receipt["duplicates"], [])
        self.assertEqual([row["id"] for row in receipt["carryover"]], ["none"])
        self.run_ctl("verify")


if __name__ == "__main__":
    unittest.main()
