"""Routed filing-decision cases loaded by ``test_hexctl``.

``test_hexctl.py`` is a path the promise-machine inventory reads under its
256 KiB bound, so these cases live beside it, as the host-identity,
replacement-object and study-amendment-rebind cases do, and ``test_hexctl``
binds them into ``RoutedFilingDecisionTests``.
"""


class RoutedFilingDecisionCases:
    """What `init` does when the issue already decided against a run.

    A filed `Fiat-Required: 0` used to exit 1 with a refusal whose last
    sentence named the edit that turned it off. An agent told to start a run
    read that as the instruction for doing so, edited the issue, and the run
    began. These cases hold the replacement to two promises: the answer is
    reported rather than refused, and nothing emitted names a way to get the
    run anyway. `adr/route-a-filed-zero-as-an-answer` records the decision.
    """

    ISSUE = "https://github.com/wildcat-finance/skills/issues/1337"

    def zero_body(self, reference="this fixture carries nothing forward"):
        return (
            "A filing that decided one pull request answers it.\n"
            "\n"
            "Fiat-Required: 0\n"
            "\n"
            "```carryover\n"
            f"none | none | {reference}\n"
            "```\n"
        )

    def route(self, body=None, expect=0):
        """Run `init` against an issue declaring `0` and return the process.

        The fake `gh` reads its bodies from the environment `run_ctl` hands the
        subprocess, which is `self.env` rather than this process's own, so the
        body is set there.
        """
        self.env["FAKE_GH_ISSUES"] = json.dumps(
            {self.ISSUE: body if body is not None else self.zero_body()}
        )
        try:
            return self.run_ctl(
                "init", "--topic", "routing probe", "--task-issue", self.ISSUE,
                expect=expect,
            )
        finally:
            self.env.pop("FAKE_GH_ISSUES", None)

    def test_a_filed_zero_exits_zero_and_prints_one_directive(self):
        proc = self.route()
        self.assertEqual(proc.returncode, 0)
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, f"expected one object, got: {proc.stdout!r}")
        directive = json.loads(lines[0])
        self.assertEqual(directive["do"], "pull-request")
        self.assertEqual(directive["fiat_required"], 0)

    def test_a_routed_zero_names_the_route_the_issue_and_what_closing_needs(self):
        directive = json.loads(self.route().stdout)
        self.assertEqual(directive["task_issue"], self.ISSUE)
        self.assertEqual(directive["repository"], "wildcat-finance/skills")
        self.assertEqual(directive["number"], "1337")
        self.assertIn("one independent pull request", directive["route"])
        self.assertEqual(
            directive["task_issue_closure"]["required_before_merge"],
            "Closes wildcat-finance/skills#1337",
        )
        self.assertEqual(
            directive["carryover"],
            [{"id": "none", "disposition": "none",
              "reference": "this fixture carries nothing forward"}],
        )

    def status(self):
        return subprocess.run(
            ["git", "status", "--short"],
            cwd=self.target, capture_output=True, text=True, env=self.env,
        ).stdout

    def test_a_routed_zero_leaves_no_state_worktree_or_branch(self):
        # The fixture's own scaffolding is untracked before anything runs, so
        # the claim under test is that `init` added nothing, not that the tree
        # was ever empty.
        before = self.status()
        self.route()
        self.assertEqual(self.status(), before, "a routed zero changed the worktree")
        self.assertFalse(
            os.path.exists(os.path.join(self.target, ".hexaemeron")),
            "a routed zero left a state directory behind",
        )
        self.assertEqual(
            subprocess.run(
                ["git", "branch", "--list", "fiat/*"],
                cwd=self.target, capture_output=True, text=True, env=self.env,
            ).stdout.strip(),
            "",
            "a routed zero cut a branch",
        )

    def test_nothing_emitted_names_a_mechanism_that_grants_this_run(self):
        proc = self.route()
        emitted = (proc.stdout + proc.stderr).lower()
        for grant in (
            "if that decision was wrong",
            "fiat-required: 1",
            "override",
            "--force",
            "change the issue",
        ):
            self.assertNotIn(
                grant, emitted,
                f"the routed directive names {grant!r}, which is a way back in",
            )

    def test_an_issue_body_carrying_a_control_character_never_reaches_a_run(self):
        """The parser refuses it, which is why the stripping is a second line."""
        proc = self.route(
            body=self.zero_body(reference="a reference carrying \x07 a bell"),
            expect=2,
        )
        self.assertIn("contains a control character", proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_the_directive_strips_a_control_character_from_every_field(self):
        """The builder strips whatever reaches it, parser or no parser.

        No body that gets this far can carry one, because
        `issue_contract_faults` refuses it first and the case above holds that
        refusal. This exercises the builder directly, so the stripping is
        proved by the code that would have to fail for a control character to
        reach an agent, rather than by an input the parser already rejects.
        """
        module = hexctl_module()
        directive = module.routed_filing_directive({
            "issue": "https://github.com/wildcat-finance/skills/issues/1337",
            "repository": "wildcat-finance/sk\x07ills",
            "number": "1337",
            "fiat_required": 0,
            "carryover": [
                {"id": "none", "disposition": "none",
                 "reference": "a reference carrying \x07 a bell"},
            ],
        })
        rendered = json.dumps(directive)
        for control in ("\x07", "\x00", "\x1b"):
            self.assertNotIn(control, rendered)
        self.assertEqual(directive["repository"], "wildcat-finance/sk ills")
        self.assertEqual(
            directive["carryover"][0]["reference"],
            "a reference carrying   a bell",
        )

    def test_the_directive_strips_control_characters_from_keys_and_nesting(self):
        """A row shape the parser does not currently produce is still clean.

        Today `carryover_row_faults` emits three fixed string keys and refuses
        a row carrying a control character first, so nothing dirty reaches the
        builder. This holds the builder to the claim its docstring makes rather
        than to the coupling that happens to make the claim true (S2-R1-04).
        """
        module = hexctl_module()
        directive = module.routed_filing_directive({
            "issue": "https://github.com/wildcat-finance/skills/issues/1337",
            "repository": "wildcat-finance/skills",
            "number": "1337",
            "fiat_required": 0,
            "carryover": [
                {"i\x00d": "none",
                 "nested": {"deep\x1b": ["a \x07 bell", 7, None, True]},
                 "count": 3},
            ],
        })
        rendered = json.dumps(directive)
        for control in ("\x00", "\x07", "\x1b"):
            self.assertNotIn(control, rendered)
        row = directive["carryover"][0]
        self.assertIn("i d", row)
        self.assertEqual(row["nested"]["deep "], ["a   bell", 7, None, True])
        self.assertEqual(row["count"], 3)


def build_routed_filing_decision_cases(context):
    """Bind the cases to the already-loaded controller test harness."""
    globals().update(
        {name: value for name, value in context.items() if not name.startswith("__")}
    )
    return (RoutedFilingDecisionCases,)
