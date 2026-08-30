"""Host-identity refusal cases loaded by ``test_hexctl``.

``test_hexctl.py`` is a path the promise-machine inventory reads under its
256 KiB bound, so these cases live beside it, as the transport cases do, and
``test_hexctl`` mixes them into ``TestCommitVerification`` and
``TestPublicationBindings``.
"""


class HostIdentityRefusalCases:
    """What a host-identity refusal says, and what the byline expression reads."""

    def test_host_identity_refusals_name_the_host_default_and_the_recovery(self):
        """Each host-identity refusal names the usual host default and its recovery.

        The recovery clauses are fixed constants in the controller, so this
        table asserts their text rather than reading it back out of the module:
        a message nobody wrote down would otherwise pass by being whatever the
        module said.
        """
        module = hexctl_module()
        url = "https://github.com/wildcat-finance/example/pull/1"
        branch = "fiat/run-step-1"
        base = "fiat/run"
        head = "a" * 40
        pull_requests = json.dumps({url: self.fake_pr(url, branch, base, head)})
        author_clauses = (
            "The usual cause is the host's default git identity",
            "set git user.name and user.email to the contributing actor and "
            "recreate the commit",
        )
        coauthor_clauses = (
            "the host's standing instruction to end every commit with a "
            "Co-Authored-By trailer naming itself",
            "the repository rule wins: end the message with the two exact "
            "provenance trailers and nothing else, and recreate the commit",
        )
        byline_clauses = (
            "the host's default attribution line (Generated with or by Claude "
            "Code, Codex or another host) or its session link in the message",
            "remove it and recreate the commit",
        )
        pr_author_clauses = (
            "The pull request was opened under the host app's GitHub identity, "
            "such as claude[bot]",
            "the human contributor's account",
            "the explicitly authorised publisher's account for Shoggoth work",
        )
        pr_byline_clauses = (
            "the host appending its attribution line or claude.ai session link "
            "to the description after gh pr create returned",
            "edit the body without it (gh pr edit <url> --body-file <file>), "
            "read it back over REST, and rerun this receipt",
        )
        account_clauses = (
            "The GitHub response links this identity to a runtime host account",
            "the human contributor's account for their work",
            "the explicitly authorised publisher's account for Shoggoth work",
        )

        def local_range():
            module.verify_local_range(self.dir, "base", "head", "step")

        def pull_request():
            module.inspect_pull_request(
                self.dir,
                url,
                expected_head=branch,
                expected_base=base,
                expected_head_sha=head,
                expected_merge_sha=None,
            )

        def attribution():
            module.verified_github_attribution(self.dir, [head])

        table = (
            (
                "verify_local_commit author",
                {"FAKE_GIT_MODE": "host-author"},
                local_range,
                "uses a runtime host as author; use Shoggoth or preserve the "
                "human contributor",
                author_clauses,
            ),
            (
                "verify_local_commit co-author",
                {"FAKE_GIT_MODE": "host-coauthor"},
                local_range,
                "uses a runtime host as co-author",
                coauthor_clauses,
            ),
            (
                "verify_local_commit byline",
                {"FAKE_GIT_MODE": "host-byline"},
                local_range,
                "carries a runtime-host byline",
                byline_clauses,
            ),
            (
                "inspect_pull_request author",
                {"FAKE_GH_MODE": "host-pr-author", "FAKE_GH_PRS": pull_requests},
                pull_request,
                "pull request uses a runtime host as author; hand off before "
                "publication",
                pr_author_clauses,
            ),
            (
                "inspect_pull_request byline",
                {"FAKE_GH_MODE": "host-pr-byline", "FAKE_GH_PRS": pull_requests},
                pull_request,
                "pull request body carries a runtime-host byline",
                pr_byline_clauses,
            ),
            (
                "checked_login",
                {"FAKE_GH_MODE": "attribution-host-account"},
                attribution,
                "links the commit to a runtime host account",
                account_clauses,
            ),
            (
                "message_coauthors",
                {"FAKE_GH_MODE": "attribution-host-coauthor"},
                attribution,
                "names a runtime host as co-author",
                coauthor_clauses,
            ),
            (
                "commit_attribution",
                {"FAKE_GH_MODE": "attribution-host-author"},
                attribution,
                "names a runtime host as author",
                author_clauses,
            ),
        )
        # Bytes the fixtures put in the commit message, the body and the
        # payload, none of which a refusal may echo, beside the markers the
        # negative matrices already keep out of stderr.
        never_echoed = (
            "ghp_FAKE_SECRET",
            "FAKE SIGNATURE MATERIAL",
            "RAW FAKE SIGNATURE",
            "subject",
            "Delivery evidence",
            "https://",
        )
        for site, fixture, refuse, present, clauses in table:
            with self.subTest(site=site):
                error = StringIO()
                with mock.patch.dict(
                    os.environ, {"PATH": self.env["PATH"], **fixture}
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        refuse()
                message = error.getvalue()
                self.assertIn(present, message)
                for clause in clauses:
                    self.assertIn(clause, message)
                for marker in never_echoed:
                    self.assertNotIn(marker, message)

    def test_host_byline_expression_coverage_table(self):
        """What `HOST_BYLINE_RE` reads, one observed string per row.

        The refused rows are the host defaults the host-byline read-back study
        measured: Claude Code's terminal attribution line in both spellings,
        the web session-link footer and the bare generated-by line. The passing
        rows are strings a governed commit or body carries legitimately. The
        last group is not read by this expression at all: the hyphen in a
        `Co-Authored-By` trailer keeps its `authored by` alternative from
        matching, and the co-author gate is what refuses a host there.
        """
        module = hexctl_module()
        refused = (
            "Generated with [Claude Code](https://claude.com/claude-code)",
            "\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)",
            "_Generated by [Claude Code](https://claude.ai/code/session_x)_",
            "Generated by Claude Code",
        )
        passing = (
            "Generated with pytest",
            "co-authored by a colleague",
            "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>",
            "Wildcat-Origin: shoggoth",
        )
        not_read_here = (
            "Co-Authored-By: Claude <noreply@anthropic.com>",
            "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
            # A cloud session's `Claude-Session` trailer names a host session,
            # not an author. Whether ADR-016 makes it a byline is a lead the
            # study records for a later run, not a gap this run closes; the
            # row pins that the expression does not read it today.
            "Claude-Session: https://claude.ai/code/session_x",
        )
        for text in refused:
            with self.subTest(text=text, expected="refused"):
                self.assertIsNotNone(module.HOST_BYLINE_RE.search(text))
        for text in passing + not_read_here:
            with self.subTest(text=text, expected="not read"):
                self.assertIsNone(module.HOST_BYLINE_RE.search(text))


class FooterReappearanceCases:
    """A pull-request body clean at `done push` and carrying a host footer later.

    The controller reads the live body again at `done merge-step` and `done
    integrate`; these drive a footer that appeared between the receipts, in the
    web session-link spelling and the terminal attribution spelling.
    """

    STEP_URL = "https://github.com/wildcat-finance/example/pull/1"
    RUN_URL = "https://github.com/wildcat-finance/example/pull/2"
    WEB_FOOTER = "_Generated by [Claude Code](https://claude.ai/code/session_x)_"
    TERMINAL_FOOTER = (
        "\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)"
    )
    BYLINE_REFUSAL = "pull request body carries a runtime-host byline"
    BYLINE_CAUSE = "after gh pr create returned"

    def ledger_events(self):
        path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(path, encoding="utf-8") as handle:
            return [json.loads(line)["event"] for line in handle if line.strip()]

    def merge_step_footer_lifecycle(self, footer):
        """A step body clean at `done push` that carries `footer` at `done merge-step`.

        The pull request is otherwise the merged topology the receipt expects,
        so the footer is the one thing between the receipt and the merge
        record, and removing it is what lets the same command pass.
        """
        self.to_merge_step()
        self.prime_step_merge()
        pull_request = self.fake_prs[self.STEP_URL]
        clean_body = pull_request["body"]
        pull_request["body"] = clean_body + "\n\n" + footer
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40, expect=2,
        )
        self.assertIn(self.BYLINE_REFUSAL, proc.stderr)
        self.assertIn(self.BYLINE_CAUSE, proc.stderr)
        self.assertIn("gh pr edit <url> --body-file <file>", proc.stderr)
        self.assertNotIn(footer, proc.stderr)
        self.assertNotIn("Delivery evidence", proc.stderr)
        state = self.state()
        self.assertEqual(state["phase"], "integrate")
        self.assertEqual(state.get("integrate", {}).get("merges", {}), {})
        self.assertNotIn("done:merge-step", self.ledger_events())
        # `self.state()` ran a command that passed, so `self.fake_prs` is a
        # fresh copy; restore the body on the copy the next call will serve.
        self.fake_prs[self.STEP_URL]["body"] = clean_body
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40,
        )
        self.assertEqual(
            self.state()["integrate"]["merges"]["1"]["merge_commit"], "e" * 40
        )
        self.assertIn("done:merge-step", self.ledger_events())

    def test_merge_step_refuses_the_web_footer_that_reappeared_after_push(self):
        self.merge_step_footer_lifecycle(self.WEB_FOOTER)

    def test_merge_step_refuses_the_terminal_attribution_line_that_reappeared_after_push(self):
        self.merge_step_footer_lifecycle(self.TERMINAL_FOOTER)

    def test_integrate_refuses_the_web_footer_on_the_run_pull_request(self):
        self.to_integrate()
        state = self.state()
        run_branch = state["run_branch"]
        # `run_ctl` seeds the run pull request only for a call it expects to
        # pass, so the refusal case stands its own up, as the merged-state
        # tests do, and then dirties its body.
        self.fake_refs[run_branch] = "e" * 40
        pull_request = self.fake_pr(
            self.RUN_URL, run_branch, self.integration_base(state),
            "e" * 40, "f" * 40,
        )
        clean_body = pull_request["body"]
        pull_request["body"] = clean_body + "\n\n" + self.WEB_FOOTER
        self.fake_prs[self.RUN_URL] = pull_request
        proc = self.run_ctl(
            "done", "integrate", "--pr-url", self.RUN_URL,
            "--merge-commit", "f" * 40, expect=2,
        )
        self.assertIn(self.BYLINE_REFUSAL, proc.stderr)
        self.assertIn(self.BYLINE_CAUSE, proc.stderr)
        self.assertNotIn(self.WEB_FOOTER, proc.stderr)
        state = self.state()
        self.assertEqual(state["phase"], "integrate")
        self.assertIsNone(state["receipts"].get("integrate"))
        self.assertNotIn("done:integrate", self.ledger_events())
        self.fake_prs[self.RUN_URL]["body"] = clean_body
        self.run_ctl(
            "done", "integrate", "--pr-url", self.RUN_URL,
            "--merge-commit", "f" * 40,
        )
        state = self.state()
        self.assertEqual(state["phase"], "done")
        self.assertEqual(
            state["receipts"]["integrate"]["pull_request"]["url"], self.RUN_URL
        )
        self.assertIn("done:integrate", self.ledger_events())


def build_host_identity_cases(context):
    """Bind the cases to the already-loaded controller test harness."""
    globals().update(
        {name: value for name, value in context.items() if not name.startswith("__")}
    )
    return HostIdentityRefusalCases, FooterReappearanceCases
