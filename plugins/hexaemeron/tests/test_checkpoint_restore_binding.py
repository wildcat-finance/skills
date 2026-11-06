"""`checkpoint restore --archive` stays on the directory it admitted (#1648).

Admission opens the destination without following a symlink and checks it is
empty. Before #1648 every later operation resolved the destination's name
again, so a writer on the parent who swapped the name after admission
received the restore. These cases restore one real signed archive in process
and swap the name at fixed points through `mock.patch` seams, so the order is
deterministic: right after the inspector, before and after `git init` (or the
directory carrier's clone), after the relocation marker, after `git worktree
add`, before publication and before the marker's retirement.

A swap puts either an empty directory (`replacement`) or a symlink to an empty
sentinel directory (`symlink_destination`) at the name. Either way the
restore must refuse with the one fixed sentence, write nothing into the
replacement or the sentinel, remove neither, and give the caller back the
working directory it started in. An `interrupted` restore must leave its
marker and disposable root in the admitted directory. The conformance
resolvers in the run's design record select these cases by those words.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from argparse import Namespace
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from test_hexctl_checkpoint_archive import HEXCTL, SignedRunFixture, hexctl_module

MOVED = (
    "hexctl: error: checkpoint restore destination no longer names the "
    "admitted directory\n"
)
MARKER = os.path.join(".hexaemeron", "checkpoint-restore.json")


class Outcome:
    """What one in-process restore did: exit code, stderr, result, exception."""

    def __init__(self, code, error, result, raised):
        self.code = code
        self.error = error
        self.result = result
        self.raised = raised


class RestoreBindingTests(SignedRunFixture):
    """Name swaps after admission never move the restore off its inode."""

    _carriers: dict = {}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._carriers = {}
        cls.module = hexctl_module()
        cls.carrier_root = tempfile.mkdtemp(prefix="fiat1648-carrier-")
        cls.addClassCleanup(shutil.rmtree, cls.carrier_root, ignore_errors=True)

    # -- fixture ------------------------------------------------------------

    def carrier(self, kind="zip"):
        """One real signed archive of each carrier, built once per class."""
        if kind not in self._carriers:
            self.to_post_push()
            arguments = ["checkpoint", "archive"]
            if kind == "directory":
                arguments += ["--format", "directory"]
            payload = json.loads(self.run_ctl(*arguments).stdout)
            source = Path(payload["archive"])
            kept = Path(self.carrier_root) / f"{kind}-{source.name}"
            if source.is_dir():
                shutil.copytree(source, kept, symlinks=True)
            else:
                shutil.copy2(source, kept)
            self._carriers[kind] = (kept, payload["outer_sha256"])
        return self._carriers[kind]

    def parent(self):
        root = os.path.realpath(tempfile.mkdtemp(prefix="fiat1648-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        sentinel = os.path.join(root, "sentinel")
        os.mkdir(sentinel)
        return root

    @staticmethod
    def swap(root, *, symlink=False):
        """Move the admitted directory aside and put a replacement at its name."""
        destination = os.path.join(root, "dest")
        os.rename(destination, os.path.join(root, "away"))
        if symlink:
            os.symlink(os.path.join(root, "sentinel"), destination)
        else:
            os.mkdir(destination, 0o700)

    def after(self, name, action):
        """Patch one module function to run `action` once after it returns."""
        original = getattr(self.module, name)
        fired = []

        def wrapper(*args, **kwargs):
            value = original(*args, **kwargs)
            if not fired:
                fired.append(True)
                action()
            return value

        return name, wrapper

    def git_seam(self, verb, action, *, when="after", tool=False):
        """Run `action` once around the first Git call whose argv starts with `verb`."""
        name = "bounded_tool" if tool else "bounded_git"
        original = getattr(self.module, name)
        fired = []

        def wrapper(base_dir, *args, **kwargs):
            argv = args[1] if tool else args[0]
            hit = not fired and list(argv[: len(verb)]) == list(verb)
            if hit and when == "before":
                fired.append(True)
                action(argv)
            value = original(base_dir, *args, **kwargs)
            if hit and when == "after":
                fired.append(True)
                action(argv)
            return value

        return name, wrapper

    def seam(self, point, action):
        """The patch that runs `action` at one named SC-1 point."""
        return {
            "inspected": lambda: self.after(
                "_checkpoint_inspect_carrier_verified", action
            ),
            "before-init": lambda: self.git_seam(
                ("init",), lambda _: action(), when="before"
            ),
            "after-init": lambda: self.git_seam(("init",), lambda _: action()),
            "after-marker": lambda: self.after("_checkpoint_restore_marker", action),
            "after-worktree-add": lambda: self.git_seam(
                ("worktree", "add"), lambda _: action()
            ),
            "before-publication": lambda: self.after(
                "_checkpoint_restore_write_files", action
            ),
            "before-retirement": lambda: self.after(
                "_checkpoint_archive_identity", action
            ),
            "before-clone": lambda: self.git_seam(
                ("clone",), lambda _: action(), when="before", tool=True
            ),
        }[point]()

    def restore(self, destination, patches=(), *, kind="zip"):
        """Run one archive restore in process; the caller's cwd must come back."""
        archive, digest = self.carrier(kind)
        before = os.stat(os.curdir)
        before_name = os.getcwd()
        error = StringIO()
        code = result = raised = None
        with ExitStack() as stack:
            for name, value in patches:
                stack.enter_context(mock.patch.object(self.module, name, value))
            stack.enter_context(redirect_stderr(error))
            stack.enter_context(redirect_stdout(StringIO()))
            try:
                result = self.module._checkpoint_restore_from_archive(
                    destination, str(archive), digest
                )
            except SystemExit as stopped:
                code = stopped.code
            except (KeyboardInterrupt, RuntimeError) as exception:
                raised = exception
        after = os.stat(os.curdir)
        self.assertEqual(
            (before.st_dev, before.st_ino),
            (after.st_dev, after.st_ino),
            "the restore did not give the caller back its working directory",
        )
        self.assertEqual(before_name, os.getcwd())
        self.assertIsNone(getattr(self.module, "_CHECKPOINT_RESTORE_ANCHOR", None))
        return Outcome(code, error.getvalue(), result, raised)

    def assert_replacement_refused(self, point, *, kind="zip"):
        root = self.parent()
        destination = os.path.join(root, "dest")
        outcome = self.restore(
            destination, [self.seam(point, lambda: self.swap(root))], kind=kind
        )
        self.assertEqual(1, outcome.code, outcome.error)
        self.assertEqual(MOVED, outcome.error)
        self.assertTrue(os.path.isdir(destination))
        self.assertFalse(os.path.islink(destination))
        self.assertEqual([], os.listdir(destination), "the restore wrote into the replacement")
        self.assertTrue(os.path.isdir(os.path.join(root, "away")))

    def assert_symlink_refused(self, point):
        root = self.parent()
        destination = os.path.join(root, "dest")
        sentinel = os.path.join(root, "sentinel")
        outcome = self.restore(
            destination, [self.seam(point, lambda: self.swap(root, symlink=True))]
        )
        self.assertEqual(1, outcome.code, outcome.error)
        self.assertEqual(MOVED, outcome.error)
        self.assertTrue(os.path.islink(destination))
        self.assertEqual(sentinel, os.readlink(destination))
        self.assertEqual([], os.listdir(sentinel), "the restore wrote through the symlink")

    def assert_residue_admitted(self, root):
        """The marker and disposable root stay in the admitted directory."""
        away = os.path.join(root, "away")
        _, digest = self.carrier()
        self.assertTrue(os.path.isfile(os.path.join(away, MARKER)))
        self.assertTrue(
            os.path.isdir(
                os.path.join(
                    away, ".git", self.module.CHECKPOINT_ARCHIVE_RESTORE_STAGE_DIR, digest
                )
            )
        )

    # -- SC-1: an empty directory swapped in at each point -------------------

    def test_replacement_after_inspection_refuses(self):
        self.assert_replacement_refused("inspected")

    def test_replacement_before_git_init_refuses(self):
        # The step's counterfactual: before #1648 the whole restore lands in
        # the replacement and the admitted directory stays empty.
        self.assert_replacement_refused("before-init")

    def test_replacement_after_git_init_refuses(self):
        self.assert_replacement_refused("after-init")

    def test_replacement_after_marker_refuses(self):
        self.assert_replacement_refused("after-marker")

    def test_replacement_after_worktree_add_refuses(self):
        self.assert_replacement_refused("after-worktree-add")

    def test_replacement_before_publication_refuses(self):
        self.assert_replacement_refused("before-publication")

    def test_replacement_before_marker_retirement_refuses(self):
        self.assert_replacement_refused("before-retirement")

    def test_directory_carrier_replacement_before_clone_refuses(self):
        self.assert_replacement_refused("before-clone", kind="directory")

    # -- SC-2: a symlink to a sentinel swapped in at each point -------------

    def test_symlink_destination_after_inspection(self):
        self.assert_symlink_refused("inspected")

    def test_symlink_destination_before_git_init(self):
        self.assert_symlink_refused("before-init")

    def test_symlink_destination_after_git_init(self):
        self.assert_symlink_refused("after-init")

    def test_symlink_destination_after_marker(self):
        self.assert_symlink_refused("after-marker")

    def test_symlink_destination_after_worktree_add(self):
        self.assert_symlink_refused("after-worktree-add")

    def test_symlink_destination_before_publication(self):
        self.assert_symlink_refused("before-publication")

    def test_symlink_destination_before_marker_retirement(self):
        self.assert_symlink_refused("before-retirement")

    # -- SC-4: an interruption after a swap ---------------------------------

    def interrupt_after_swap(self, point, *, symlink=False):
        root = self.parent()
        destination = os.path.join(root, "dest")

        def swap_then_interrupt():
            self.swap(root, symlink=symlink)
            raise KeyboardInterrupt

        outcome = self.restore(destination, [self.seam(point, swap_then_interrupt)])
        self.assertIsInstance(outcome.raised, KeyboardInterrupt)
        return root, destination

    def test_interrupted_after_marker_keeps_residue_admitted(self):
        root, destination = self.interrupt_after_swap("after-marker")
        self.assert_residue_admitted(root)
        self.assertTrue(os.path.isdir(destination), "cleanup removed the replacement")
        self.assertEqual([], os.listdir(destination))

    def test_interrupted_before_retirement_keeps_marker_admitted(self):
        root, destination = self.interrupt_after_swap("before-retirement")
        self.assert_residue_admitted(root)
        self.assertTrue(os.path.isdir(destination), "cleanup removed the replacement")
        self.assertEqual([], os.listdir(destination))

    def test_interrupted_symlink_destination_leaves_sentinel(self):
        root, destination = self.interrupt_after_swap("after-marker", symlink=True)
        self.assert_residue_admitted(root)
        self.assertTrue(os.path.islink(destination))
        self.assertEqual([], os.listdir(os.path.join(root, "sentinel")))

    def test_interrupted_before_any_write_keeps_replacement(self):
        # A created destination swapped before `git init`: the cleanup's
        # `rmdir` once removed whatever empty directory held the name.
        root, destination = self.interrupt_after_swap("before-init")
        self.assertTrue(os.path.isdir(destination), "cleanup removed the replacement")
        self.assertEqual([], os.listdir(destination))
        self.assertEqual([], os.listdir(os.path.join(root, "away")))

    # -- the working directory on every exit ----------------------------------

    def test_cwd_restored_after_another_refusal(self):
        root = self.parent()
        destination = os.path.join(root, "dest")

        def refuse(*_args, **_kwargs):
            self.module.die("fixture refusal after the anchor")

        outcome = self.restore(destination, [("_checkpoint_restore_marker", refuse)])
        self.assertEqual(2, outcome.code)
        self.assertIn("fixture refusal after the anchor", outcome.error)

    def test_cwd_restored_after_an_exception(self):
        root = self.parent()
        destination = os.path.join(root, "dest")

        def fail(*_args, **_kwargs):
            raise RuntimeError("fixture failure after the anchor")

        outcome = self.restore(
            destination, [("_checkpoint_restore_prepare_worktree_home", fail)]
        )
        self.assertIsInstance(outcome.raised, RuntimeError)
        self.assertTrue(os.path.isdir(os.path.join(destination, ".git")))

    # -- the link Git records for the derived worktree ---------------------

    def test_worktree_link_naming_another_directory_refuses(self):
        root = self.parent()
        destination = os.path.join(root, "dest")
        elsewhere = os.path.join(root, "sentinel", ".git", "worktrees", "run")

        def redirect(argv):
            with open(os.path.join(argv[2], ".git"), "w", encoding="utf-8") as handle:
                handle.write(f"gitdir: {elsewhere}\n")

        outcome = self.restore(
            destination, [self.git_seam(("worktree", "add"), redirect)]
        )
        self.assertEqual(1, outcome.code, outcome.error)
        self.assertEqual(MOVED, outcome.error)
        self.assertEqual([], os.listdir(os.path.join(root, "sentinel")))

    # -- unswapped restores complete as before -------------------------------

    def assert_restored(self, destination, outcome):
        self.assertIsNone(outcome.code, outcome.error)
        self.assertIsNone(outcome.raised)
        payload = outcome.result
        self.assertEqual("ok", payload["verify"])
        worktree = payload["restore"]["worktree"]
        self.assertEqual(os.path.join(destination, "tmp", "fiat"), os.path.dirname(worktree))
        state = json.loads(Path(worktree, ".hexaemeron", "state.json").read_bytes())
        self.assertEqual(destination, state["config"]["git"]["origin"])
        self.assertEqual(worktree, state["config"]["git"]["worktree"])
        self.assertEqual(
            f"{worktree}\n",
            Path(destination, ".hexaemeron", "worktree").read_text(encoding="utf-8"),
        )
        self.assertFalse(os.path.exists(os.path.join(destination, MARKER)))
        self.assertFalse(
            os.path.exists(
                os.path.join(
                    destination, ".git", self.module.CHECKPOINT_ARCHIVE_RESTORE_STAGE_DIR
                )
            )
        )
        for command in (["verify"], ["status", "--json"], ["next"]):
            checked = subprocess.run(
                [sys.executable, HEXCTL, "--dir", worktree, *command],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, checked.returncode, checked.stderr)
        return worktree

    def test_unswapped_restore_completes_with_relative_children(self):
        root = self.parent()
        destination = os.path.join(root, "dest")
        started = []
        real_popen = subprocess.Popen

        def recording_popen(argv, *args, **kwargs):
            started.append((list(argv), kwargs.get("cwd")))
            return real_popen(argv, *args, **kwargs)

        with mock.patch.object(self.module.subprocess, "Popen", recording_popen):
            outcome = self.restore(destination)
        self.assert_restored(destination, outcome)
        verbs = [
            cwd
            for argv, cwd in started
            if argv[:1] == ["git"]
            and (argv[1:2] in (["init"], ["fetch"], ["checkout"]) or argv[1:3] == ["worktree", "add"])
        ]
        named = [
            cwd
            for cwd in verbs
            if cwd is not None
            and os.path.isabs(cwd)
            and (cwd == destination or cwd.startswith(destination + os.sep))
        ]
        self.assertEqual([], named, "a restore Git child resolved the destination name")
        inherited = [cwd for cwd in verbs if cwd is None or not os.path.isabs(cwd)]
        self.assertGreaterEqual(len(inherited), 4)

    def test_directory_carrier_clone_restores_in_place(self):
        root = self.parent()
        destination = os.path.join(root, "dest")
        cloned = []

        def record(argv):
            cloned.append(list(argv))

        outcome = self.restore(
            destination,
            [self.git_seam(("clone",), record, tool=True)],
            kind="directory",
        )
        self.assert_restored(destination, outcome)
        self.assertEqual(1, len(cloned))
        self.assertEqual(".git", cloned[0][-1])

    # -- `--from` keeps every child at its resolved origin ----------------------

    def test_from_restore_keeps_resolved_child_cwd(self):
        self.to_post_push()
        capsule = Path(self.dir) / "capsule"
        exported = json.loads(
            self.run_ctl("checkpoint", "export", "--out", str(capsule)).stdout
        )
        home = os.path.realpath(tempfile.mkdtemp(prefix="fiat1648-from-"))
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        origin = os.path.join(home, "origin")
        subprocess.run(["git", "clone", "-q", self.dir, origin], check=True, capture_output=True)
        remote = self.git("remote", "get-url", "origin").stdout.strip()
        subprocess.run(
            ["git", "remote", "set-url", "origin", remote],
            cwd=origin, check=True, capture_output=True,
        )
        manifest = json.loads(capsule.joinpath("MANIFEST.json").read_bytes())
        for ref in manifest["boundary"]["refs"]:
            if ref == "main" or len(ref) == 40:
                continue
            subprocess.run(
                ["git", "branch", ref, f"origin/{ref}"],
                cwd=origin, check=True, capture_output=True,
            )
        started = []
        real_popen = subprocess.Popen

        def recording_popen(argv, *args, **kwargs):
            if list(argv[:1]) == ["git"]:
                started.append(kwargs.get("cwd"))
            return real_popen(argv, *args, **kwargs)

        before = os.getcwd()
        output = StringIO()
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.dict(os.environ, self.direct_environment(), clear=True)
            )
            stack.enter_context(
                mock.patch.object(self.module.subprocess, "Popen", recording_popen)
            )
            stack.enter_context(redirect_stdout(output))
            self.module.cmd_checkpoint_restore(
                Namespace(
                    dir=origin,
                    source=str(capsule),
                    manifest_sha256=exported["manifest_sha256"],
                    archive=None,
                    sha256=None,
                )
            )
        self.assertEqual(before, os.getcwd())
        self.assertEqual("new", json.loads(output.getvalue())["recovery"])
        self.assertTrue(started)
        for cwd in started:
            self.assertTrue(cwd is not None and os.path.isabs(cwd))
            self.assertEqual(os.path.realpath(cwd), cwd)
        self.assertIsNone(getattr(self.module, "_CHECKPOINT_RESTORE_ANCHOR", None))
