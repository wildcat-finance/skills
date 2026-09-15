"""Continuity cases shared with the bounded controller test module."""

import os


class WardenContinuityCases:
    """The audit-round brief says which Warden a round belongs to."""

    PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    WARDEN_DOC = os.path.join(PLUGIN, "agents", "warden.md")
    LOOP_DOC = os.path.join(
        PLUGIN, "skills", "fiat", "references", "audit-loop.md"
    )

    WAIVED = '"waived: prose-only repo"'

    def to_ready_audit(self, titles=("Scaffold", "Core")):
        self.to_steps(titles=titles)
        self.run_ctl("record", "security_suite", self.WAIVED)

    def audit_brief(self):
        directive = self.next_json()
        self.assertEqual(directive["do"], "audit-round")
        return directive["brief"]

    def another_round(self):
        self.run_ctl("audit-round", "--findings", "1", *LINTS_CLEAN)

    def close_step(self, number):
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.run_ctl("done", "audit", "--fixes-ref", "deadbeef")
        self.run_ctl(
            "done", "prose", "--files", "3",
            "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.run_ctl(
            "done", "push",
            "--pr-url",
            f"https://github.com/wildcat-finance/example/pull/{number}",
            "--head-commit", self.fake_sha(f"head{number}"),
            "--pr-base", self.step_base(number),
        )

    def test_a_steps_first_round_starts_a_new_warden(self):
        self.to_ready_audit()
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc1",
        )
        brief = self.audit_brief()
        self.assertEqual(brief["warden_continuity"], "new")
        self.assertEqual(brief["step"], 1)
        self.assertEqual(brief["round"], 1)

    def test_later_rounds_of_one_step_continue_the_same_warden(self):
        self.to_ready_audit()
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc1",
        )
        self.another_round()
        second = self.audit_brief()
        self.assertEqual(second["round"], 2)
        self.assertEqual(second["warden_continuity"], "same-agent")
        self.another_round()
        third = self.audit_brief()
        self.assertEqual(third["round"], 3)
        self.assertEqual(third["warden_continuity"], "same-agent")
        self.assertEqual(third["step"], 1)

    def test_a_new_step_starts_its_own_warden(self):
        self.to_ready_audit()
        self.finish_step(1)
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(2),
            "--commit", "abc2",
        )
        brief = self.audit_brief()
        self.assertEqual(brief["step"], 2)
        self.assertEqual(brief["round"], 1)
        self.assertEqual(brief["warden_continuity"], "new")

    def test_four_steps_of_three_rounds_start_exactly_four_wardens(self):
        titles = ("Scaffold", "Core", "Wire", "Polish")
        self.to_ready_audit(titles=titles)
        observed = []
        for number in range(1, len(titles) + 1):
            self.run_ctl(
                "done", "implement", "--branch", self.step_branch(number),
                "--commit", f"abc{number}",
            )
            observed.append(self.audit_brief())
            self.another_round()
            observed.append(self.audit_brief())
            self.another_round()
            observed.append(self.audit_brief())
            self.close_step(number)
        self.assertEqual(len(observed), 3 * len(titles))
        fresh = [item for item in observed if item["warden_continuity"] == "new"]
        self.assertEqual(len(fresh), len(titles))
        self.assertEqual(
            [item["step"] for item in fresh], list(range(1, len(titles) + 1))
        )
        self.assertEqual([item["round"] for item in fresh], [1] * len(titles))
        for item in observed:
            if item["round"] > 1:
                self.assertEqual(item["warden_continuity"], "same-agent")

    def test_the_field_never_claims_a_document_was_read(self):
        self.to_ready_audit()
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc1",
        )
        self.another_round()
        brief = self.audit_brief()
        self.assertEqual(brief["warden_continuity"], "same-agent")
        self.assertNotIn("read", json.dumps(brief).lower())

    @staticmethod
    def flowed(path):
        """The document as one line, so a wrapped sentence still matches."""
        with open(path, encoding="utf-8") as handle:
            return " ".join(handle.read().split())

    def test_the_controller_reads_only_its_own_declared_check_ids(self):
        """A check id from anywhere but a controller constant is not a name."""
        controller = hexctl_module()
        self.write(
            "tests/check-map-v1.json",
            json.dumps(
                {
                    "schema": "wildcat.check-map.v1",
                    "checks": {
                        "root-suite": {"argv": ["python3", "-m", "unittest"]},
                        "hexaemeron-suite": {"argv": ["python3", "runner.py"]},
                        "dead-code-suite": {"argv": ["python3", "dead.py"]},
                    },
                },
                indent=2,
            )
            + "\n",
        )
        for check in controller.CHECK_MAP_KNOWN_CHECKS:
            with self.subTest(check=check):
                declared = controller.repository_check_command(
                    self.target, check=check
                )
                self.assertEqual(check, declared["check"])
                self.assertEqual("tests/check-map-v1.json", declared["source"])
                self.assertEqual(".", declared["cwd"])
        self.assertNotIn("dead-code-suite", controller.CHECK_MAP_KNOWN_CHECKS)
        self.assertIsNone(
            controller.repository_check_command(
                self.target, check="dead-code-suite"
            )
        )

    def test_both_documents_keep_the_unreadable_host_fallback(self):
        warden = self.flowed(self.WARDEN_DOC)
        loop = self.flowed(self.LOOP_DOC)
        self.assertIn("warden_continuity", warden)
        self.assertIn("does not mean the suite documents are", warden)
        self.assertIn("cannot keep an agent", loop)
        self.assertIn("reads the suite documents in full", loop)
        self.assertIn("still pays for the full read", loop)


class TaskIdentityCases:
    """Issue 363: `next` names the task a delegate runs as, and refuses a stale one.

    Every role, the inline directive and each refusal class are held in
    `test_task_identity`. These two are the cases the run's conformance cells
    name, on a run bound to issue 320 as the observed failure's run was.
    """

    HANDLE = "fiat-320-step-2-mason"
    ORIGIN = "https://github.com/wildcat-finance/example.git"

    def issue_run_at_step_two(self):
        self.git("remote", "add", "origin", self.ORIGIN)
        self.to_steps(task_issue=self.ORIGIN[:-4] + "/issues/320")
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.finish_step(1)
        return self.run_ctl("next").stdout

    def test_stale_handle_from_another_issue_is_refused(self):
        bare = self.issue_run_at_step_two()
        packet = json.loads(bare)
        self.assertEqual((packet["do"], packet["agent"]), ("implement", "mason"))
        self.assertEqual(packet["task_identity"]["handle"], self.HANDLE)
        stale = self.run_ctl("next", "--task-handle", "issue318_step2", expect=2)
        self.assertEqual(stale.stdout, "")
        self.assertEqual(
            stale.stderr,
            "hexctl: error: task handle refused (equality): expected "
            f"{self.HANDLE}, observed issue318_step2\n",
        )
        current = self.run_ctl("next", "--task-handle", self.HANDLE)
        self.assertEqual(current.stdout, bare)

    def test_identity_is_identical_across_processes_and_after_reload(self):
        first = self.issue_run_at_step_two()
        self.assertEqual(self.run_ctl("next").stdout, first)
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        capsule, origin = (os.path.join(os.path.realpath(home.name), name)
                           for name in ("capsule", "origin"))
        exported = self.run_ctl("checkpoint", "export", "--out", capsule).stdout
        with open(os.path.join(capsule, "MANIFEST.json"), encoding="utf-8") as handle:
            refs = json.load(handle)["boundary"]["refs"]
        commands = [["clone", "-q", self.dir, origin]]
        commands += [["-C", origin, "branch", ref, f"origin/{ref}"] for ref in refs
                     if ref != "main" and not re.fullmatch(r"[0-9a-f]{40}", ref)]
        commands.append(["-C", origin, "remote", "set-url", "origin", self.ORIGIN])
        for command in commands:
            subprocess.run(["git", *command], check=True, capture_output=True)
        env = dict(self.env, FAKE_GIT_REFS=json.dumps(self.fake_refs),
                   FAKE_GIT_PARENTS=json.dumps(self.fake_parents),
                   FAKE_GH_PRS=json.dumps(self.fake_prs))

        def control(where, *args):
            proc = subprocess.run([sys.executable, HEXCTL, "--dir", where, *args],
                                  cwd=where, capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return proc.stdout

        control(origin, "checkpoint", "restore", "--from", capsule,
                "--manifest-sha256", json.loads(exported)["manifest_sha256"])
        crumb = os.path.join(origin, ".hexaemeron", "worktree")
        with open(crumb, encoding="utf-8") as handle:
            restored = handle.read().strip()
        after = control(restored, "next")
        # The identity is compared as emitted, before anything is put back:
        # the substitution below would also rewrite a path or digest inside it.
        identity = json.loads(after)["task_identity"]
        self.assertEqual(identity, json.loads(first)["task_identity"])
        self.assertEqual(identity["handle"], self.HANDLE)
        # A restore moves the run, so its paths and state digest move with it.
        # Put both back and every other byte holds.
        was, now = (json.loads(out)["state_sha256"] for out in (first, after))
        self.assertNotEqual(was, now)
        self.assertEqual(
            after.replace(restored, os.path.realpath(self.target)).replace(now, was),
            first,
        )
        self.assertEqual(control(restored, "next", "--task-handle", self.HANDLE), after)


def build_task_continuity_cases(context):
    """Bind these cases to the existing controller fixture."""
    globals().update({name: value for name, value in context.items() if not name.startswith("__")})
    return WardenContinuityCases, TaskIdentityCases
