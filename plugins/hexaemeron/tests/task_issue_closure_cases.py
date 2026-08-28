"""Task-issue closing-reference cases loaded by ``test_hexctl``."""


class TaskIssueClosureCases:
    def to_prose(self, task_issue=None):
        self.to_audit(task_issue=task_issue)
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")

    def test_task_issue_integrate_requires_a_recognised_pr_closing_reference(self):
        issue = "https://github.com/wildcat-finance/example/issues/74"
        self.to_prose(task_issue=issue)
        self.run_ctl(
            "done", "prose", "--files", "1",
            "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", self.fake_sha("head1"),
            "--pr-base", self.step_base(1),
        )
        self.finish_step(2)
        self.merge_stack()
        self.write_run_pr()

        directive = self.next_json()
        self.assertEqual(
            directive["task_issue_closure"],
            {
                "issue": issue,
                "required_before_merge": "Closes wildcat-finance/example#74",
                "gate": (
                    "done integrate reads the final pull request body and "
                    "refuses without a recognised closing reference to this "
                    "exact issue"
                ),
            },
        )

        url = "https://github.com/wildcat-finance/example/pull/2"
        merge = "f" * 40
        run_branch = self.run_branch()
        self.fake_prs[url] = self.fake_pr(
            url,
            run_branch,
            "main",
            self.fake_refs[run_branch],
            merge,
            body=(
                "Issue #74 is complete.\n\n"
                "No other issue-74 work remains unfinished.\n\n"
                "<!-- wildcat-origin: shoggoth -->"
            ),
        )
        proc = self.run_ctl(
            "done", "integrate", "--pr-url", url,
            "--merge-commit", merge,
            "--closed-issue-url", issue,
            expect=2,
        )
        self.assertIn("no recognised closing reference", proc.stderr)
        self.assertIn("Closes wildcat-finance/example#74", proc.stderr)
        self.assertEqual(self.next_json()["do"], "integrate")

        self.run_ctl(
            "done", "integrate", "--pr-url", url,
            "--merge-commit", merge,
            "--closed-issue-url", issue,
        )
        receipt = self.state()["receipts"]["integrate"]["pull_request"]
        self.assertEqual(receipt["closing_issue"]["issue_url"], issue)
        self.assertEqual(
            receipt["closing_issue"]["reference"],
            "wildcat-finance/example#74",
        )
        self.assertEqual(len(receipt["closing_issue"]["body_sha256"]), 64)

    def test_closing_reference_ignores_examples_and_accepts_github_syntax(self):
        module = hexctl_module()
        issue = "https://github.com/wildcat-finance/example/issues/74"
        repository = "wildcat-finance/example"
        for body in (
            "Closes #74",
            "FIXES: #74",
            "Resolved wildcat-finance/example#74",
        ):
            with self.subTest(body=body):
                self.assertIsNotNone(
                    module.pull_request_closing_reference(body, issue, repository)
                )
        for body in (
            "Issue #74 is complete.",
            "No other issue-74 work remains unfinished.",
            "Use `Closes #74` in the final pull request.",
            "```text\nCloses #74\n```",
            "> Closes #74",
            "<!-- Closes #74 -->",
        ):
            with self.subTest(body=body):
                self.assertIsNone(
                    module.pull_request_closing_reference(body, issue, repository)
                )

        other_issue = "https://github.com/wildcat-finance/skills/issues/74"
        self.assertIsNone(
            module.pull_request_closing_reference(
                "Closes #74", other_issue, repository
            )
        )
        self.assertIsNotNone(
            module.pull_request_closing_reference(
                "Closes wildcat-finance/skills#74", other_issue, repository
            )
        )


def build_task_issue_closure_tests(context):
    globals().update(
        {name: value for name, value in context.items() if not name.startswith("__")}
    )
    return type(
        "TestTaskIssueClosure",
        (TaskIssueClosureCases, context["HexctlCase"]),
        {},
    )
