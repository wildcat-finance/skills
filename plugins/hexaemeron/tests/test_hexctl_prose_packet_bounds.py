"""Issue 972: the prose packet is bounded by prose, not by the whole step diff.

`scribe_files` refused above `GIT_PATHS_MAX`, and it is reached only from
`delegation_packet`, which `next` calls. A step that removed a generated tree
therefore killed the directive rather than the phase: `next` exited non-zero,
emitted nothing, and the run could neither execute the prose phase nor receipt
it. Issue 949's step 3 hit this at 1,006 paths, 995 of them deletions.

Two halves are pinned here. The behaviour cases fail with either half of the
change reverted: drop `--diff-filter=d` and the deletion cases refuse again;
restore `GIT_PATHS_MAX` at the ceiling and the end-to-end case refuses again.
The pin cases pass either way by design, and exist so that a later reader
cannot mistake one of the three remaining `GIT_PATHS_MAX` sites for a fourth
prose surface, or re-couple the two ceilings because they happen to be equal
today.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

try:
    from .hexctl_harness import HexctlCase, LINTS_CLEAN
except ImportError:
    from hexctl_harness import HexctlCase, LINTS_CLEAN


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEXCTL = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"

# Above `GIT_PATHS_MAX`, which is what the old bound refused at, and far enough
# under the new one that the fixture stays cheap to build.
DELETED_FILE_COUNT = 600


def controller_module():
    spec = importlib.util.spec_from_file_location(
        "hexctl_prose_packet_bounds_under_test", HEXCTL
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(directory, *args):
    return subprocess.run(
        ["git", "-C", str(directory), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def init_repository(directory):
    """A repository that signs nothing and inherits no ambient identity."""
    git(directory, "init", "--quiet", "-b", "main")
    for key, value in (
        ("user.name", "Fixture"),
        ("user.email", "fixture@example.invalid"),
        ("commit.gpgsign", "false"),
        ("tag.gpgsign", "false"),
    ):
        git(directory, "config", key, value)


def commit_all(directory, message):
    git(directory, "add", "-A")
    git(directory, "commit", "--quiet", "--no-gpg-sign", "-m", message)


class ProseSelectionTests(unittest.TestCase):
    """What the packet keeps and drops, read from a real repository."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.repo = Path(cls._tmp.name)
        init_repository(cls.repo)

        generated = cls.repo / "generated"
        generated.mkdir()
        for index in range(DELETED_FILE_COUNT):
            (generated / f"payload-{index:04d}.json").write_text("{}\n")
        docs = cls.repo / "docs"
        docs.mkdir()
        (docs / "kept.md").write_text("original\n")
        (docs / "moved.md").write_text("travelling\n")
        commit_all(cls.repo, "base")
        git(cls.repo, "branch", "pr-base")

        for index in range(DELETED_FILE_COUNT):
            (generated / f"payload-{index:04d}.json").unlink()
        (docs / "kept.md").write_text("rewritten\n")
        (docs / "added.md").write_text("new\n")
        git(cls.repo, "mv", "docs/moved.md", "docs/arrived.md")
        commit_all(cls.repo, "step")
        git(cls.repo, "branch", "step-branch")

        cls.module = controller_module()

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def files(self):
        return self.module.scribe_files(str(self.repo), "pr-base", "step-branch")

    def test_a_removed_generated_tree_leaves_only_the_prose_behind(self):
        """The reported shape: 600 deletions beside one rewritten artefact."""
        self.assertGreater(DELETED_FILE_COUNT, self.module.GIT_PATHS_MAX)
        files = self.files()
        self.assertIn("docs/kept.md", files)
        self.assertFalse(
            [path for path in files if path.startswith("generated/")],
            "a deleted generated payload reached the prose packet",
        )

    def test_an_added_artefact_survives_the_filter(self):
        self.assertIn("docs/added.md", self.files())

    def test_a_rename_arrives_under_its_new_name(self):
        files = self.files()
        self.assertIn("docs/arrived.md", files)
        self.assertNotIn("docs/moved.md", files)

    def test_the_packet_is_exactly_the_authored_surface(self):
        self.assertEqual(
            self.files(),
            ["docs/added.md", "docs/arrived.md", "docs/kept.md"],
        )

    def test_an_authored_diff_above_the_prose_ceiling_still_refuses(self):
        """The bound is stated, not removed: a real prose flood still stops."""
        original = self.module.PROSE_PATHS_MAX
        self.module.PROSE_PATHS_MAX = 2
        try:
            stderr = StringIO()
            with self.assertRaises(SystemExit) as raised, redirect_stderr(stderr):
                self.files()
        finally:
            self.module.PROSE_PATHS_MAX = original
        self.assertNotEqual(raised.exception.code, 0)
        message = stderr.getvalue()
        self.assertIn("prose packet", message)
        self.assertIn("deleted paths are already excluded", message)
        self.assertIn("3", message)

    def test_the_refusal_names_what_the_ceiling_protects(self):
        """A contributor is told what the number is about, not only its value."""
        original = self.module.PROSE_PATHS_MAX
        self.module.PROSE_PATHS_MAX = 1
        try:
            stderr = StringIO()
            with self.assertRaises(SystemExit), redirect_stderr(stderr):
                self.files()
        finally:
            self.module.PROSE_PATHS_MAX = original
        message = stderr.getvalue()
        self.assertIn("a prose pass could act on", message)
        self.assertNotEqual(
            message.strip(),
            f"git diff returned more than {self.module.GIT_PATHS_MAX} paths",
        )

    def test_the_grammar_refusals_still_run_over_the_retained_set(self):
        """Filtering happens on the argv, so nothing skips these checks."""
        module = self.module
        original = module.bounded_git
        module.bounded_git = lambda *a, **k: b"/etc/passwd\0"
        try:
            stderr = StringIO()
            with self.assertRaises(SystemExit), redirect_stderr(stderr):
                self.files()
        finally:
            module.bounded_git = original
        self.assertIn("unsafe path", stderr.getvalue())

    def test_a_non_utf8_path_list_still_refuses(self):
        module = self.module
        original = module.bounded_git
        module.bounded_git = lambda *a, **k: b"\xff\xfe\0"
        try:
            stderr = StringIO()
            with self.assertRaises(SystemExit), redirect_stderr(stderr):
                self.files()
        finally:
            module.bounded_git = original
        self.assertIn("not UTF-8", stderr.getvalue())

    def test_the_deletion_filter_is_applied_on_the_read(self):
        """Recorded so a later refactor cannot move it after validation."""
        seen = {}
        module = self.module
        original = module.bounded_git

        def capture(base_dir, argv, *rest, **kwargs):
            seen["argv"] = list(argv)
            return original(base_dir, argv, *rest, **kwargs)

        module.bounded_git = capture
        try:
            self.files()
        finally:
            module.bounded_git = original
        self.assertIn("--diff-filter=d", seen["argv"])


class BoundIndependenceTests(unittest.TestCase):
    """The two ceilings are separate, and the three shared sites are unchanged."""

    @classmethod
    def setUpClass(cls):
        cls.module = controller_module()
        cls.source = HEXCTL.read_text(encoding="utf-8")

    def test_the_shared_constant_keeps_its_value(self):
        self.assertEqual(self.module.GIT_PATHS_MAX, 500)

    def test_the_prose_ceiling_is_its_own_constant(self):
        self.assertTrue(hasattr(self.module, "PROSE_PATHS_MAX"))
        self.assertGreater(self.module.PROSE_PATHS_MAX, self.module.GIT_PATHS_MAX)

    def test_the_commit_range_still_reads_the_shared_constant(self):
        self.assertIn(
            'die(f"{label} commit range exceeds {GIT_PATHS_MAX} commits")',
            self.source,
        )

    def test_the_checkpoint_ref_set_still_reads_the_shared_constant(self):
        self.assertIn(
            "if len(unique) != len(names) or len(unique) > GIT_PATHS_MAX:",
            self.source,
        )

    def test_the_packet_builder_no_longer_reads_the_shared_constant(self):
        import inspect

        body = inspect.getsource(self.module.scribe_files)
        self.assertIn("PROSE_PATHS_MAX", body)
        self.assertNotIn("GIT_PATHS_MAX", body)

    def test_the_selection_does_not_depend_on_the_generator_registry(self):
        """Issue 971 will remove or repoint the registry's only entry."""
        import inspect

        body = inspect.getsource(self.module.scribe_files)
        self.assertNotIn("GENERATOR_AGGREGATE_REGISTRY", body)

    def test_the_constant_comment_no_longer_denies_that_the_prose_diff_grows(self):
        self.assertNotIn(
            "prose diff and the checkpoint ref set, none of which grow that way",
            self.source,
        )


class ProseDirectiveTests(HexctlCase):
    """The acceptance check, driven through `next` on real branches."""

    def reach_prose_with_a_removed_tree(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.run_ctl("done", "audit")

        state = self.state()
        run_branch = state["run_branch"]
        step_branch = self.step_branch(1, state)

        generated = os.path.join(self.target, "generated")
        os.makedirs(generated, exist_ok=True)
        for index in range(DELETED_FILE_COUNT):
            with open(
                os.path.join(generated, f"payload-{index:04d}.json"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("{}\n")
        docs = os.path.join(self.target, "docs")
        os.makedirs(docs, exist_ok=True)
        with open(os.path.join(docs, "record.md"), "w", encoding="utf-8") as handle:
            handle.write("original\n")
        self.git("add", "-A")
        self.git("commit", "--no-gpg-sign", "-m", "seed the generated payload")

        self.git("branch", "-f", step_branch, run_branch)
        stage = os.path.join(self.dir, "step-stage")
        subprocess.run(
            ["git", "-C", self.target, "worktree", "add", "--quiet", stage, step_branch],
            check=True,
            capture_output=True,
        )
        try:
            for index in range(DELETED_FILE_COUNT):
                os.unlink(os.path.join(stage, "generated", f"payload-{index:04d}.json"))
            with open(
                os.path.join(stage, "docs", "record.md"), "w", encoding="utf-8"
            ) as handle:
                handle.write("rewritten by the step\n")
            git(stage, "add", "-A")
            git(stage, "commit", "--no-gpg-sign", "-m", "stop carrying the payload")
        finally:
            subprocess.run(
                ["git", "-C", self.target, "worktree", "remove", "--force", stage],
                check=True,
                capture_output=True,
            )

        changed = git(
            self.target, "diff", "--name-only", f"{run_branch}..{step_branch}"
        ).splitlines()
        self.assertGreater(len(changed), self.module_git_paths_max())
        return self.next_json()

    @staticmethod
    def module_git_paths_max():
        return controller_module().GIT_PATHS_MAX

    def test_a_step_that_removes_a_generated_tree_reaches_prose(self):
        directive = self.reach_prose_with_a_removed_tree()
        self.assertEqual(directive["do"], "prose")
        self.assertEqual(directive["agent"], "scribe")

    def test_the_packet_carries_the_prose_artefact_and_not_the_payload(self):
        directive = self.reach_prose_with_a_removed_tree()
        files = directive["brief"]["files"]
        self.assertIn("docs/record.md", files)
        self.assertFalse([path for path in files if path.startswith("generated/")])

    def test_the_prose_phase_can_then_be_receipted(self):
        self.reach_prose_with_a_removed_tree()
        self.run_ctl(
            "done",
            "prose",
            "--files",
            "1",
            "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.assertEqual(self.state()["steps"][0]["phase"], "push")


if __name__ == "__main__":
    unittest.main()
