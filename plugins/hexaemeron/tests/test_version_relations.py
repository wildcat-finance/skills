"""Focused fixtures for Fiat's runbook version-relation anchor.

The relation changes when a version becomes concrete.  These tests hold the
earlier boundary: ``done runbook`` captures exact starting-commit evidence,
does not reserve a label, and leaves a literal-only run byte-compatible.
"""

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile

try:
    from plugins.hexaemeron.tests.test_hexctl import HexctlCase, hexctl_module
except ModuleNotFoundError:  # direct discovery from this directory
    from test_hexctl import HexctlCase, hexctl_module


RELATION = "next-generation-after-integration-base"
SCHEMA = "fiat-version-relations/v1"


def field_digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class VersionRelationTests(HexctlCase):
    def setUp(self):
        super().setUp()
        # These fixtures need the real object database.  HexctlCase's delivery
        # shim is for signature and GitHub topology tests and deliberately
        # replaces ordinary ``git show`` output.
        self.env["PATH"] = os.pathsep.join(self.env["PATH"].split(os.pathsep)[1:])

    @staticmethod
    def ledger_path(skill):
        return f"plugins/hexaemeron/skills/{skill}/EVOLUTION.md"

    @staticmethod
    def skill_path(skill):
        return f"plugins/hexaemeron/skills/{skill}/SKILL.md"

    @staticmethod
    def ledger(
        skill,
        version=(1, 2, 3),
        *,
        status="open",
        revision="held-frontier",
        frontier="The held frontier remains exact.",
        job="Complete the held job.",
    ):
        label = f"{skill}-v{version[0]}.{version[1]}.{version[2]}"
        digest = hashlib.sha256(
            f"{status}|{revision}|{frontier}|{job}\n".encode("utf-8")
        ).hexdigest()
        return (
            f"# {skill} evolution ledger\n\n"
            f"- Current version: `{label}`\n"
            f"- Frontier status: `{status}`\n"
            f"- Frontier revision: `{revision}`\n"
            f"- Current frontier: {frontier}\n"
            f"- Next Fiat job: {job}\n\n"
            "## History\n\n"
            f"- `{label}` | baseline | `{revision}` | `{digest}` | "
            "fixture | Versioning starts here.\n"
        )

    @staticmethod
    def skill(skill, version=(1, 2, 3)):
        number = ".".join(str(part) for part in version)
        return (
            "---\n"
            f"name: {skill}\n"
            "description: Fixture governed skill.\n"
            "metadata:\n"
            f"  version: \"{number}\"\n"
            "---\n\n"
            f"# {skill}\n"
        )

    def install_target(self, skill, version=(1, 2, 3), **ledger_fields):
        self.write(self.ledger_path(skill), self.ledger(skill, version, **ledger_fields))
        self.write(self.skill_path(skill), self.skill(skill, version))

    def commit_seed(self):
        self.git("add", "-A")
        self.git("commit", "-m", "seed governed skills")
        return self.git("rev-parse", "HEAD").stdout.strip()

    def hash_object(self, text):
        result = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=self.target,
            input=text,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    @staticmethod
    def relation_block(*skills):
        rows = [
            f"{skill} | plugins/hexaemeron/skills/{skill}/EVOLUTION.md | {RELATION}"
            for skill in skills
        ]
        return "```version-relations\n" + "\n".join(rows) + "\n```\n"

    def receipt_runbook(self, *skills, block=None, study_text="# Study\n"):
        self.init()
        study = self.write("study.md", study_text)
        self.run_ctl("done", "study", "--artifact", study)
        if block is None:
            block = self.relation_block(*skills) if skills else ""
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + block
            + "\n## Step 1: Build\n\n**Goal.** Build the fixture.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        return result, self.state()

    def receipt(self, state):
        return state["receipts"]["runbook"]["version_relations"]

    def assert_unchanged_after_refusal(self, before_state, before_ledger):
        with open(
            os.path.join(self.target, ".hexaemeron", "state.json"),
            encoding="utf-8",
        ) as handle:
            self.assertEqual(json.load(handle), before_state)
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            self.assertEqual(handle.read(), before_ledger)

    def test_one_target_captures_every_anchor_field_without_reserving(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        _, state = self.receipt_runbook("fiat")
        relation = self.receipt(state)

        self.assertEqual(relation["schema"], SCHEMA)
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(
            relation["source_sha256"],
            hashlib.sha256(self.relation_block("fiat").encode()).hexdigest(),
        )
        self.assertNotIn("reserved", json.dumps(relation).lower())
        self.assertEqual(len(relation["targets"]), 1)
        target = relation["targets"][0]
        self.assertEqual(
            target,
            {
                "skill": "fiat",
                "ledger": self.ledger_path("fiat"),
                "relation": RELATION,
                "anchor_version": "fiat-v1.2.3",
                "evolution": 1,
                "generation": 2,
                "epoch": 3,
                "frontier_status": "open",
                "frontier_revision": "held-frontier",
                "frontier_sha256": hashlib.sha256(
                    (
                        "open|held-frontier|The held frontier remains exact.|"
                        "Complete the held job.\n"
                    ).encode()
                ).hexdigest(),
                "current_frontier_sha256": field_digest(
                    "The held frontier remains exact."
                ),
                "next_job_sha256": field_digest("Complete the held job."),
                "ledger_sha256": hashlib.sha256(
                    self.ledger("fiat").encode()
                ).hexdigest(),
                "skill_sha256": hashlib.sha256(self.skill("fiat").encode()).hexdigest(),
                "skill_metadata_version": "1.2.3",
            },
        )

    def test_two_targets_are_atomic_and_sorted_not_source_ordered(self):
        self.install_target("fiat")
        self.install_target("protasis", (4, 7, 0))
        self.commit_seed()
        _, state = self.receipt_runbook(
            block=self.relation_block("protasis", "fiat")
        )
        self.assertEqual(
            [target["skill"] for target in self.receipt(state)["targets"]],
            ["fiat", "protasis"],
        )

    def test_partial_target_coverage_captures_only_the_declared_skill(self):
        self.install_target("fiat")
        self.install_target("protasis", (4, 7, 0))
        self.commit_seed()
        _, state = self.receipt_runbook("fiat")
        self.assertEqual(
            [target["skill"] for target in self.receipt(state)["targets"]],
            ["fiat"],
        )

    def test_starting_commit_wins_over_later_worktree_and_ref_drift(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()

        self.write(self.ledger_path("fiat"), self.ledger("fiat", (1, 9, 3)))
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 9, 3)))
        self.git("add", "-A")
        self.git("commit", "-m", "move run worktree")

        with open(os.path.join(self.dir, "base-drift.txt"), "w", encoding="utf-8") as handle:
            handle.write("main moved\n")
        subprocess.run(
            ["git", "add", "base-drift.txt"], cwd=self.dir, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "move base ref"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )

        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        relation = self.receipt(self.state())
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_base_rewind_cannot_move_anchor_before_the_run_start(self):
        self.install_target("fiat", (1, 1, 3))
        older = self.commit_seed()
        self.write(self.ledger_path("fiat"), self.ledger("fiat", (1, 2, 3)))
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 2, 3)))
        self.commit_seed()
        self.init()

        subprocess.run(
            ["git", "reset", "--hard", older],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done",
            "runbook",
            "--artifact",
            runbook,
            "--steps-file",
            steps,
            expect=2,
        )
        self.assertIn("init starting commit", result.stderr)
        self.assertNotIn(older, result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_run_branch_recreation_cannot_replace_the_init_anchor(self):
        self.install_target("fiat")
        original = self.commit_seed()
        self.init()
        run_branch = self.state()["run_branch"]

        origin_ledger = os.path.join(self.dir, self.ledger_path("fiat"))
        origin_skill = os.path.join(self.dir, self.skill_path("fiat"))
        with open(origin_ledger, "w", encoding="utf-8") as handle:
            handle.write(self.ledger("fiat", (9, 9, 9)))
        with open(origin_skill, "w", encoding="utf-8") as handle:
            handle.write(self.skill("fiat", (9, 9, 9)))
        subprocess.run(
            ["git", "add", "-A"], cwd=self.dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "move the integration base"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )
        moved = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.dir,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        # Deleting and recreating the checked-out ref replaces its branch
        # reflog without touching the linked worktree's controller state.
        subprocess.run(
            ["git", "update-ref", "-d", f"refs/heads/{run_branch}"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "update-ref",
                "--create-reflog",
                f"refs/heads/{run_branch}",
                moved,
            ],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )

        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done",
            "runbook",
            "--artifact",
            runbook,
            "--steps-file",
            steps,
            expect=2,
        )
        self.assertIn("init starting commit", result.stderr)
        self.assertNotIn(original, result.stderr)
        self.assertNotIn(moved, result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_relation_anchor_does_not_require_native_reflogs(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        subprocess.run(
            ["git", "config", "core.logAllRefUpdates", "false"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )

        _, state = self.receipt_runbook("fiat")

        relation = self.receipt(state)
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_sha256_repository_anchor_replays_across_packets_and_verify(self):
        controller = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "skills",
                "fiat",
                "scripts",
                "hexctl.py",
            )
        )
        with tempfile.TemporaryDirectory() as repository:
            for argv in (
                ("init", "-q", "--object-format=sha256", "-b", "main"),
                ("config", "user.email", "fixture@example.invalid"),
                ("config", "user.name", "Fixture"),
                ("config", "commit.gpgsign", "false"),
            ):
                subprocess.run(
                    ["git", *argv],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                )
            ledger = os.path.join(repository, self.ledger_path("fiat"))
            skill = os.path.join(repository, self.skill_path("fiat"))
            os.makedirs(os.path.dirname(ledger), exist_ok=True)
            with open(ledger, "w", encoding="utf-8") as handle:
                handle.write(self.ledger("fiat"))
            with open(skill, "w", encoding="utf-8") as handle:
                handle.write(self.skill("fiat"))
            for argv in (("add", "-A"), ("commit", "-q", "-m", "seed")):
                subprocess.run(
                    ["git", *argv],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                )
            anchor = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(len(anchor), 64)

            def control(directory, *argv):
                result = subprocess.run(
                    [sys.executable, controller, "--dir", directory, *argv],
                    cwd=directory,
                    env=self.env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return result

            control(repository, "init", "--topic", "sha256 relation")
            with open(
                os.path.join(repository, ".hexaemeron", "worktree"),
                encoding="utf-8",
            ) as handle:
                worktree = handle.read().strip()
            with open(
                os.path.join(worktree, "study.md"), "w", encoding="utf-8"
            ) as handle:
                handle.write("# Study\n")
            control(worktree, "done", "study", "--artifact", "study.md")
            with open(
                os.path.join(worktree, "runbook.md"), "w", encoding="utf-8"
            ) as handle:
                handle.write(
                    "# Runbook\n\n"
                    + self.relation_block("fiat")
                    + "\n## Step 1: Build\n\n**Goal.** Build.\n"
                )
            with open(
                os.path.join(worktree, "steps.json"), "w", encoding="utf-8"
            ) as handle:
                handle.write('["Build"]')
            control(
                worktree,
                "done",
                "runbook",
                "--artifact",
                "runbook.md",
                "--steps-file",
                "steps.json",
            )
            status = json.loads(control(worktree, "status", "--json").stdout)
            relation = status["receipts"]["runbook"]["version_relations"]
            self.assertEqual(relation["anchor_commit"], anchor)
            self.assertEqual(
                relation["targets"][0]["anchor_version"], "fiat-v1.2.3"
            )
            control(worktree, "next")
            control(worktree, "verify")

    def test_commit_replacement_cannot_substitute_anchor_tree(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.write(self.ledger_path("fiat"), self.ledger("fiat", (9, 9, 9)))
        self.write(self.skill_path("fiat"), self.skill("fiat", (9, 9, 9)))
        self.git("add", "-A")
        self.git("commit", "-m", "replacement tree")
        replacement = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("reset", "--hard", anchor)

        self.init(base=anchor)
        self.git("replace", anchor, replacement)
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )

        relation = self.receipt(self.state())
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_blob_replacements_cannot_substitute_anchor_bytes(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        ledger_blob = self.git(
            "rev-parse", f"{anchor}:{self.ledger_path('fiat')}"
        ).stdout.strip()
        skill_blob = self.git(
            "rev-parse", f"{anchor}:{self.skill_path('fiat')}"
        ).stdout.strip()
        replacement_ledger = self.hash_object(self.ledger("fiat", (9, 9, 9)))
        replacement_skill = self.hash_object(self.skill("fiat", (9, 9, 9)))

        self.init(base=anchor)
        self.git("replace", ledger_blob, replacement_ledger)
        self.git("replace", skill_blob, replacement_skill)
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )

        relation = self.receipt(self.state())
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_grafted_branch_history_refuses_anchor_derivation(self):
        self.install_target("fiat")
        self.commit_seed()
        self.init()
        self.env["GIT_GRAFT_FILE"] = os.path.join(self.dir, "attacker-grafts")
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("rewritten by a graft", result.stderr)

    def test_relation_git_environment_cannot_redirect_anchor_repository(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()
        state = self.state()

        with tempfile.TemporaryDirectory() as attacker:
            for argv in (
                ("init", "-q", "-b", "main"),
                ("config", "user.email", "attacker@example.invalid"),
                ("config", "user.name", "Attacker"),
                ("config", "commit.gpgsign", "false"),
            ):
                subprocess.run(
                    ["git", *argv], cwd=attacker, check=True, capture_output=True
                )
            ledger = os.path.join(attacker, self.ledger_path("fiat"))
            skill = os.path.join(attacker, self.skill_path("fiat"))
            os.makedirs(os.path.dirname(ledger), exist_ok=True)
            with open(ledger, "w", encoding="utf-8") as handle:
                handle.write(self.ledger("fiat", (9, 9, 9)))
            with open(skill, "w", encoding="utf-8") as handle:
                handle.write(self.skill("fiat", (9, 9, 9)))
            subprocess.run(
                ["git", "add", "-A"], cwd=attacker, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-q", "-m", "substitute repository"],
                cwd=attacker,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", state["run_branch"]],
                cwd=attacker,
                check=True,
                capture_output=True,
            )

            study = self.write("study.md", "# Study\n")
            self.run_ctl("done", "study", "--artifact", study)
            runbook = self.write(
                "runbook.md",
                "# Runbook\n\n"
                + self.relation_block("fiat")
                + "\n## Step 1: Build\n\n**Goal.** Build.\n",
            )
            steps = self.write("steps.json", '["Build"]')
            self.env["GIT_DIR"] = os.path.join(attacker, ".git")
            try:
                self.run_ctl(
                    "done", "runbook", "--artifact", runbook,
                    "--steps-file", steps,
                )
            finally:
                self.env.pop("GIT_DIR", None)

        with open(
            os.path.join(self.target, ".hexaemeron", "state.json"),
            encoding="utf-8",
        ) as handle:
            relation = self.receipt(json.load(handle))
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_relation_git_ignores_alternate_object_environment(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = os.path.join(
            self.dir, "absent-object-store"
        )
        try:
            self.run_ctl(
                "done", "runbook", "--artifact", runbook, "--steps-file", steps
            )
        finally:
            self.env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)

        relation = self.receipt(self.state())
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_repository_alternate_object_store_refuses_anchor_capture(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init(base=anchor)
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        alternates = self.git(
            "rev-parse", "--path-format=absolute", "--git-path",
            "objects/info/alternates",
        ).stdout.strip()
        os.makedirs(os.path.dirname(alternates), exist_ok=True)
        with tempfile.TemporaryDirectory() as alternate:
            with open(alternates, "w", encoding="utf-8") as handle:
                handle.write(alternate + "\n")
            runbook = self.write(
                "runbook.md",
                "# Runbook\n\n"
                + self.relation_block("fiat")
                + "\n## Step 1: Build\n\n**Goal.** Build.\n",
            )
            steps = self.write("steps.json", '["Build"]')
            result = self.run_ctl(
                "done", "runbook", "--artifact", runbook,
                "--steps-file", steps, expect=2,
            )
        self.assertIn("uses an alternate object store", result.stderr)

    def test_shallow_history_refuses_anchor_derivation(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        shallow = self.git(
            "rev-parse", "--path-format=absolute", "--git-path", "shallow"
        ).stdout.strip()
        with open(shallow, "w", encoding="ascii") as handle:
            handle.write(anchor + "\n")
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("starting history is shallow", result.stderr)

    def test_anchor_derivation_refuses_history_that_turns_shallow_mid_read(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()
        state = self.state()
        shallow = self.git(
            "rev-parse", "--path-format=absolute", "--git-path", "shallow"
        ).stdout.strip()
        module = hexctl_module()
        native_git = module._native_relation_git
        changed = False

        def change_history_after_check(base_dir, argv, refusal):
            nonlocal changed
            output = native_git(base_dir, argv, refusal)
            if argv == ["rev-parse", "--is-shallow-repository"] and not changed:
                with open(shallow, "w", encoding="ascii") as handle:
                    handle.write(anchor + "\n")
                changed = True
            return output

        module._native_relation_git = change_history_after_check
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                module.relation_anchor_commit(self.target, state)
        self.assertIn("starting history is shallow", stderr.getvalue())

    def test_replay_refuses_tree_typed_anchor_commit(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.receipt_runbook("fiat")
        anchor_tree = self.git("rev-parse", f"{anchor}^{{tree}}").stdout.strip()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["runbook"]["version_relations"][
            "anchor_commit"
        ] = anchor_tree
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)

        for command in (("status",), ("next",)):
            with self.subTest(command=command):
                result = self.run_ctl(*command, expect=2)
                self.assertIn("anchor commit", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_replay_refuses_post_receipt_repository_alternate(self):
        self.install_target("fiat")
        self.commit_seed()
        self.receipt_runbook("fiat")
        alternates = self.git(
            "rev-parse", "--path-format=absolute", "--git-path",
            "objects/info/alternates",
        ).stdout.strip()
        os.makedirs(os.path.dirname(alternates), exist_ok=True)
        with tempfile.TemporaryDirectory() as alternate:
            with open(alternates, "w", encoding="utf-8") as handle:
                handle.write(alternate + "\n")
            for command in (("status",), ("next",)):
                with self.subTest(command=command):
                    result = self.run_ctl(*command, expect=2)
                    self.assertIn("uses an alternate object store", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_replay_refuses_post_receipt_shallow_history(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.receipt_runbook("fiat")
        shallow = self.git(
            "rev-parse", "--path-format=absolute", "--git-path", "shallow"
        ).stdout.strip()
        with open(shallow, "w", encoding="ascii") as handle:
            handle.write(anchor + "\n")

        for command in (("status",), ("next",)):
            with self.subTest(command=command):
                result = self.run_ctl(*command, expect=2)
                self.assertIn("starting history is shallow", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_replay_refuses_history_that_turns_shallow_mid_read(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.receipt_runbook("fiat")
        state = self.state()
        shallow = self.git(
            "rev-parse", "--path-format=absolute", "--git-path", "shallow"
        ).stdout.strip()
        module = hexctl_module()
        runbook = module.receipted_source(self.target, state, "runbook")
        native_git = module._native_relation_git
        changed = False

        def change_history_during_replay(base_dir, argv, refusal):
            nonlocal changed
            output = native_git(base_dir, argv, refusal)
            if argv[:2] == ["cat-file", "blob"] and not changed:
                with open(shallow, "w", encoding="ascii") as handle:
                    handle.write(anchor + "\n")
                changed = True
            return output

        module._native_relation_git = change_history_during_replay
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                module.receipted_version_relations(self.target, runbook)
        self.assertIn("starting history is shallow", stderr.getvalue())

    def test_no_block_preserves_the_legacy_receipt_and_packet_shape(self):
        _, state = self.receipt_runbook()
        self.assertEqual(
            set(state["receipts"]["runbook"]),
            {"artifact", "sha256", "step_count"},
        )
        raw = self.run_ctl("next").stdout
        directive = json.loads(raw)
        self.assertEqual(
            set(directive["brief"]["runbook_step"]),
            {
                "markdown",
                "baseline_markdown",
                "baseline_sha256",
                "amendments",
                "effective_sha256",
                "path",
                "sha256",
                "number",
                "title",
            },
        )
        self.assertNotIn("version_relations", json.dumps(directive))
        step_markdown = "## Step 1: Build\n\n**Goal.** Build the fixture.\n"
        step_sha256 = hashlib.sha256(step_markdown.encode()).hexdigest()
        branch = self.step_branch(1)
        expected = {
            "step": 1,
            "title": "Build",
            "do": "implement",
            "run_branch": "fiat/test-topic",
            "branch": branch,
            "branch_from": "fiat/test-topic",
            "pr_base": "fiat/test-topic",
            "merge_now": False,
            "state_sha256": hexctl_module().state_fingerprint(state),
            "agent": "mason",
            "brief": {
                "runbook_step": {
                    "markdown": step_markdown,
                    "baseline_markdown": step_markdown,
                    "baseline_sha256": step_sha256,
                    "amendments": [],
                    "effective_sha256": step_sha256,
                    "path": os.path.realpath(
                        os.path.join(
                            self.target,
                            state["receipts"]["runbook"]["artifact"],
                        )
                    ),
                    "sha256": state["receipts"]["runbook"]["sha256"],
                    "number": 1,
                    "title": "Build",
                },
                "branch": branch,
                "branch_from": "fiat/test-topic",
            },
        }
        self.assertEqual(raw, json.dumps(expected) + "\n")
        self.run_ctl("verify")

    def test_no_block_performs_no_git_version_read(self):
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md", "# Runbook\n\n## Step 1: Build\n\n**Goal.** Build.\n"
        )
        steps = self.write("steps.json", '["Build"]')
        sentinel = os.path.join(self.dir, "unexpected-git-read")
        wrapper_dir = os.path.join(self.dir, "refusing-git")
        os.makedirs(wrapper_dir)
        wrapper = os.path.join(wrapper_dir, "git")
        with open(wrapper, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env python3\n"
                "from pathlib import Path\n"
                "import os\n"
                "Path(os.environ['VERSION_GIT_SENTINEL']).write_text('called\\n')\n"
                "raise SystemExit(99)\n"
            )
        os.chmod(wrapper, 0o755)
        prior_path = self.env["PATH"]
        self.env["PATH"] = wrapper_dir + os.pathsep + prior_path
        self.env["VERSION_GIT_SENTINEL"] = sentinel
        try:
            self.run_ctl(
                "done", "runbook", "--artifact", runbook, "--steps-file", steps
            )
            self.run_ctl("status")
            self.run_ctl("next")
        finally:
            self.env["PATH"] = prior_path
            self.env.pop("VERSION_GIT_SENTINEL", None)
        self.assertFalse(os.path.exists(sentinel))

    def test_no_block_init_does_not_require_native_reflogs(self):
        subprocess.run(
            ["git", "config", "core.logAllRefUpdates", "false"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )

        _, state = self.receipt_runbook()

        self.assertEqual(
            set(state["receipts"]["runbook"]),
            {"artifact", "sha256", "step_count"},
        )
        self.assertNotIn("version_relations", self.run_ctl("next").stdout)
        self.run_ctl("verify")

    def test_relation_packet_and_status_label_anchor_and_projection(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        _, state = self.receipt_runbook("fiat")
        packet = self.next_json()["brief"]["runbook_step"]["version_relations"]
        self.assertEqual(packet["status"], "anchor")
        self.assertIsNone(packet["resolution"])
        self.assertEqual(packet["anchor_commit"], anchor)
        self.assertEqual(packet["targets"][0]["ledger"], self.ledger_path("fiat"))
        self.assertEqual(packet["targets"][0]["anchor_version"], "fiat-v1.2.3")
        self.assertEqual(packet["targets"][0]["projection"], "fiat-v1.3.3")
        self.assertNotIn("reserved", json.dumps(packet).lower())
        human = self.run_ctl("status").stdout
        self.assertIn(SCHEMA, human)
        self.assertIn(packet["source_sha256"], human)
        self.assertIn(anchor, human)
        self.assertIn(self.ledger_path("fiat"), human)
        self.assertIn("resolution null", human)
        self.assertIn("projection fiat-v1.3.3", human)
        self.run_ctl("verify")
        self.assertEqual(
            self.receipt(state), self.state()["receipts"]["runbook"]["version_relations"]
        )

    def test_projection_increments_generation_without_semver_reset(self):
        self.install_target("fiat", (7, 99, 13))
        self.commit_seed()
        self.receipt_runbook("fiat")
        packet = self.next_json()["brief"]["runbook_step"]["version_relations"]
        self.assertEqual(packet["targets"][0]["anchor_version"], "fiat-v7.99.13")
        self.assertEqual(packet["targets"][0]["projection"], "fiat-v7.100.13")

    def test_projection_refuses_an_unrepresentable_generation_successor(self):
        maximum = "9" * 128
        self.install_target("fiat", (1, maximum, 0))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook,
            "--steps-file", steps, expect=2,
        )
        self.assertIn(
            "generation cannot be projected within its counter bound",
            result.stderr,
        )
        self.assertNotIn(maximum, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_leading_zero_counters_are_not_canonical_labels(self):
        self.install_target("fiat", ("01", "02", "03"))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("malformed current label", result.stderr)

    def test_warden_and_scribe_packets_reconstruct_the_same_anchor(self):
        self.install_target("fiat")
        self.commit_seed()
        _, state = self.receipt_runbook(
            "fiat",
            study_text=(
                "# Study\n\n```risk-register\n"
                "relation-anchor | packet boundary | reconstruct\n```\n"
            ),
        )
        expected = self.next_json()["brief"]["runbook_step"]["version_relations"]
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")

        # Packet construction is the subject here.  Move the valid state fixture
        # between worker phases without exercising their unrelated Git receipts.
        state["receipts"]["security_suite"] = "waived: packet fixture"
        state["steps"][0]["phase"] = "audit"
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        warden = self.next_json()
        self.assertEqual(
            warden["brief"]["runbook_step"]["version_relations"], expected
        )

        self.git("branch", self.step_branch(1), "HEAD")
        state["steps"][0]["phase"] = "prose"
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        scribe = self.next_json()
        self.assertEqual(scribe["brief"]["version_relations"], expected)

    def test_ledger_and_skill_metadata_mismatch_refuses_without_partial_state(self):
        self.install_target("fiat")
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 2, 4)))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb") as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat") + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("metadata version", result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_body_example_cannot_stand_in_for_frontmatter_metadata(self):
        self.write(self.ledger_path("fiat"), self.ledger("fiat"))
        self.write(
            self.skill_path("fiat"),
            "---\n"
            "name: fiat\n"
            "description: Fixture with no metadata field.\n"
            "---\n\n"
            "Example only:\n\n"
            '  version: "1.2.3"\n',
        )
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("frontmatter metadata version", result.stderr)

    def test_skill_frontmatter_name_must_match_the_relation_target(self):
        self.write(self.ledger_path("fiat"), self.ledger("fiat"))
        self.write(
            self.skill_path("fiat"),
            self.skill("other").replace("# other", "# fiat"),
        )
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("frontmatter name", result.stderr)

    def test_quoted_duplicate_frontmatter_name_is_ambiguous(self):
        self.write(self.ledger_path("fiat"), self.ledger("fiat"))
        self.write(
            self.skill_path("fiat"),
            self.skill("fiat").replace(
                "name: fiat\n", 'name: fiat\n"name": other\n'
            ),
        )
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook,
            "--steps-file", steps, expect=2,
        )
        self.assertIn("frontmatter name", result.stderr)

    def test_quoted_duplicate_metadata_version_is_ambiguous(self):
        self.write(self.ledger_path("fiat"), self.ledger("fiat"))
        self.write(
            self.skill_path("fiat"),
            self.skill("fiat").replace(
                '  version: "1.2.3"\n',
                '  version: "1.2.3"\n  "version": "9.9.9"\n',
            ),
        )
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook,
            "--steps-file", steps, expect=2,
        )
        self.assertIn("frontmatter metadata version", result.stderr)

    def test_yaml_equivalent_protected_keys_are_ambiguous(self):
        canonical = self.skill("fiat")
        specimens = {
            "escaped-name": canonical.replace(
                "name: fiat\n", 'name: fiat\n"na\\u006de": other\n'
            ),
            "tagged-name": canonical.replace(
                "name: fiat\n", "name: fiat\n!!str name: other\n"
            ),
            "explicit-name": canonical.replace(
                "name: fiat\n", "name: fiat\n? name\n: other\n"
            ),
            "continued-name": canonical.replace(
                "name: fiat\n", "name: fiat\n  other\n"
            ),
            "escaped-version": canonical.replace(
                '  version: "1.2.3"\n',
                '  version: "1.2.3"\n  "ver\\u0073ion": "9.9.9"\n',
            ),
            "tagged-version": canonical.replace(
                '  version: "1.2.3"\n',
                '  version: "1.2.3"\n  !!str version: "9.9.9"\n',
            ),
        }
        for label, text in specimens.items():
            with self.subTest(label=label):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        hexctl_module()._skill_frontmatter_identity(text, "fiat")

    def test_relation_failure_does_not_echo_the_controlled_target_id(self):
        controlled = "private-relation-target-token"
        self.write(self.skill_path(controlled), self.skill(controlled))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block(controlled)
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook,
            "--steps-file", steps, expect=2,
        )
        self.assertNotIn(controlled, result.stderr)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 256)
        self.assertNotIn("Traceback", result.stderr)

    def test_unbounded_decimal_label_refuses_instead_of_raising(self):
        label = "fiat-v" + ("9" * 5000) + ".0.0"
        try:
            parsed = hexctl_module()._label_parts(label, "fiat")
        except ValueError:
            self.fail("unbounded decimal label raised instead of refusing")
        self.assertIsNone(parsed)

    def test_decimal_limit_is_independent_of_python_startup_policy(self):
        huge = "9" * 5000
        self.install_target("fiat", (huge, 0, 0))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.env["PYTHONINTMAXSTRDIGITS"] = "0"
        try:
            result = self.run_ctl(
                "done", "runbook", "--artifact", runbook,
                "--steps-file", steps, expect=2,
            )
        finally:
            self.env.pop("PYTHONINTMAXSTRDIGITS", None)
        self.assertIn("malformed current label", result.stderr)
        self.assertNotIn(huge, result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_one_bad_target_refuses_the_whole_capture(self):
        self.install_target("fiat")
        self.write(self.skill_path("protasis"), self.skill("protasis", (4, 7, 0)))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb") as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat", "protasis")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def _assert_object_refused(self, skill, needle):
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block(skill) + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn(needle, result.stderr)
        self.assertNotIn("ghp_", result.stderr)

    def test_missing_ledger_object_is_refused_content_free(self):
        self.write(self.skill_path("missing"), self.skill("missing"))
        self.commit_seed()
        self._assert_object_refused("missing", "missing")

    def test_tree_ledger_object_is_refused(self):
        self.write(self.skill_path("tree"), self.skill("tree"))
        self.write(self.ledger_path("tree") + "/child", "not a blob\n")
        self.commit_seed()
        self._assert_object_refused("tree", "regular blob")

    def test_symlink_ledger_object_is_refused(self):
        self.write(self.skill_path("linked"), self.skill("linked"))
        ledger = os.path.join(self.dir, self.ledger_path("linked"))
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        os.symlink("SKILL.md", ledger)
        self.commit_seed()
        self._assert_object_refused("linked", "regular blob")

    def test_gitlink_ledger_object_is_refused(self):
        self.write(self.skill_path("gitlink"), self.skill("gitlink"))
        self.git("add", self.skill_path("gitlink"))
        target = self.git("rev-parse", "HEAD").stdout.strip()
        self.git(
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{target},{self.ledger_path('gitlink')}",
        )
        self.git("commit", "-m", "seed gitlink")
        self._assert_object_refused("gitlink", "regular blob")

    def test_non_utf8_ledger_object_is_refused(self):
        self.write(self.skill_path("binary"), self.skill("binary"))
        ledger = os.path.join(self.dir, self.ledger_path("binary"))
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        with open(ledger, "wb") as handle:
            handle.write(b"\xff\xfe\x00")
        self.commit_seed()
        self._assert_object_refused("binary", "UTF-8")

    def test_oversized_ledger_object_is_refused_before_parsing(self):
        self.write(self.skill_path("large"), self.skill("large"))
        ledger = os.path.join(self.dir, self.ledger_path("large"))
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        with open(ledger, "wb") as handle:
            handle.write(b"x" * (2 * 1024 * 1024 + 1))
        self.commit_seed()
        self._assert_object_refused("large", "byte cap")

    def test_unsafe_relation_path_is_not_treated_as_legacy(self):
        self.install_target("fiat")
        self.commit_seed()
        block = (
            "```version-relations\n"
            f"fiat | ../fiat/EVOLUTION.md | {RELATION}\n"
            "```\n"
        )
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md", block + "\n## Step 1: Build\n\n**Goal.** Build.\n"
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("safe repository-relative", result.stderr)

    def test_malformed_stored_anchor_refuses_status_next_and_verify(self):
        self.install_target("fiat")
        self.commit_seed()
        self.receipt_runbook("fiat")
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["runbook"]["version_relations"]["targets"][0].pop(
            "ledger_sha256"
        )
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        for command in (("status",), ("next",), ("verify",)):
            with self.subTest(command=command):
                result = self.run_ctl(*command, expect=1)
                self.assertIn("version relations", result.stderr)

    def test_surrogate_revision_is_a_bounded_state_refusal(self):
        self.install_target("fiat")
        self.commit_seed()
        self.receipt_runbook("fiat")
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["runbook"]["version_relations"]["targets"][0][
            "frontier_revision"
        ] = "\ud800"
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        expected = (
            "state version relations key "
            "'receipts.runbook.version_relations.targets[0].frontier_revision' "
            "is malformed"
        )
        for command in (("status",), ("next",), ("verify",)):
            with self.subTest(command=command):
                result = self.run_ctl(*command, expect=1)
                self.assertIn(expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    import unittest

    unittest.main()
