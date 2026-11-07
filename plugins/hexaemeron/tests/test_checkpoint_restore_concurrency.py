"""Competing `hexctl` processes against one checkpoint restore (#1649).

Each competitor is a real `hexctl` process started through a short wrapper.
The wrapper loads `hexctl.py` by path, wraps one named function so that the
first call to it creates a ready file and waits for a go file, then calls
`main()` with the competitor's arguments. A test starts, releases or kills a
process only once its ready file exists, and a bounded wait fails the test
instead of reordering it. No sleep decides an order.

The seams are the inspector (`_checkpoint_inspect_carrier_verified`),
admission before its lock (`_checkpoint_restore_flock`), the emptiness scan's
return (`_checkpoint_restore_archive_destination`), the marker transaction
(`_checkpoint_restore_marker`), the atomic publish
(`_checkpoint_atomic_publish`) and the missing-state check inside
`held_lock` (`refuse_missing_state`).

Every restore uses the signed archive fixture the #861 and #1648 suites build.
The conformance resolvers in the run's design record select these cases by
the words `one_winner`, `live_resume`, `origin_init`, `imported_state` and
`killed` in their names.
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from test_hexctl_checkpoint_archive import HEXCTL, SignedRunFixture, hexctl_module

BOUND = 120
"""Seconds a competitor may take to reach its seam or to finish."""

HELD = (
    "hexctl: error: checkpoint restore destination is held by another hexctl "
    "command\n"
)
OCCUPIED = "destination-occupied\n"
MARKER = os.path.join(".hexaemeron", "checkpoint-restore.json")

WRAPPER = r"""
import importlib.util
import os
import sys
import time

path, name, when, ready, go, bound, *argv = sys.argv[1:]
spec = importlib.util.spec_from_file_location("hexctl_under_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original = getattr(module, name, None)
if original is None:
    print(f"seam {name} is absent from this controller", file=sys.stderr)
    sys.exit(97)
fired = []


def pause():
    with open(ready, "x", encoding="utf-8") as handle:
        handle.write(f"{os.getpid()}\n")
    deadline = time.monotonic() + float(bound)
    while not os.path.exists(go):
        if time.monotonic() > deadline:
            print("seam was never released", file=sys.stderr)
            os._exit(98)
        time.sleep(0.01)


def wrapper(*args, **kwargs):
    first = not fired
    fired.append(True)
    if first and when == "before":
        pause()
    value = original(*args, **kwargs)
    if first and when == "after":
        pause()
    return value


setattr(module, name, wrapper)
sys.argv = [path, *argv]
module.main()
"""


class Competitor:
    """One wrapped `hexctl` process and the two files that order it."""

    def __init__(self, process, ready, go):
        self.process = process
        self.ready = ready
        self.go = go


class RestoreConcurrencyTests(SignedRunFixture):
    """Every competitor the study names meets a lock it honours."""

    _carrier = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._carrier = None
        cls.module = hexctl_module()
        cls.carrier_root = tempfile.mkdtemp(prefix="fiat1649-carrier-")
        cls.addClassCleanup(shutil.rmtree, cls.carrier_root, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.competitors = []
        self.scratch = os.path.realpath(tempfile.mkdtemp(prefix="fiat1649-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)

    def tearDown(self):
        """Kill every competitor still running, so no lock outlives a test."""
        try:
            for competitor in self.competitors:
                if competitor.process.poll() is None:
                    competitor.process.kill()
                competitor.process.communicate(timeout=BOUND)
        finally:
            super().tearDown()

    # -- fixture ------------------------------------------------------------

    def carrier(self):
        """One real signed zip archive, built once for the class."""
        if type(self)._carrier is None:
            self.to_post_push()
            payload = json.loads(self.run_ctl("checkpoint", "archive").stdout)
            source = Path(payload["archive"])
            kept = Path(self.carrier_root) / source.name
            shutil.copy2(source, kept)
            with zipfile.ZipFile(kept) as container:
                manifest = json.loads(container.read("checkpoint.json"))
            capsule_state = "/".join(
                (self.module.CHECKPOINT_ARCHIVE_CAPSULE_DIR, "controller", "state.json")
            )
            with zipfile.ZipFile(kept) as container:
                state = json.loads(container.read(capsule_state))
            type(self)._carrier = (
                str(kept),
                payload["outer_sha256"],
                manifest["controller_capsule"]["manifest_sha256"],
                state["run_branch"],
            )
        return type(self)._carrier[:3]

    def derived_worktree(self, destination):
        """Where a restore into `destination` puts the run's worktree."""
        self.carrier()
        branch = type(self)._carrier[3]
        return os.path.join(
            destination,
            *self.module.WORKTREE_HOME,
            self.module.flattened_run_branch(branch),
        )

    def destination(self, *, create=False):
        path = os.path.join(self.scratch, f"dest-{len(self.competitors)}")
        if create:
            os.mkdir(path, 0o700)
        return path

    def start(self, argv, seam=None, when="after", env=None):
        """Start one wrapped `hexctl`; with no seam it runs straight through."""
        index = len(self.competitors)
        ready = os.path.join(self.scratch, f"competitor-{index}.ready")
        go = os.path.join(self.scratch, f"competitor-{index}.go")
        if seam is None:
            seam, when = "main", "none"
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                WRAPPER,
                HEXCTL,
                seam,
                when,
                ready,
                go,
                str(BOUND),
                *argv,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        competitor = Competitor(process, ready, go)
        self.competitors.append(competitor)
        return competitor

    def restore(self, destination, seam=None, when="after"):
        archive, digest, _ = self.carrier()
        return self.start(
            [
                "--dir",
                destination,
                "checkpoint",
                "restore",
                "--archive",
                archive,
                "--sha256",
                digest,
            ],
            seam,
            when,
        )

    def from_origin(self):
        """A fresh clone and the `restore --from` arguments for one export."""
        self.to_post_push()
        capsule = Path(self.dir) / "capsule"
        exported = json.loads(
            self.run_ctl("checkpoint", "export", "--out", str(capsule)).stdout
        )
        origin = os.path.join(self.scratch, "origin")
        subprocess.run(
            ["git", "clone", "-q", self.dir, origin], check=True, capture_output=True
        )
        remote = self.git("remote", "get-url", "origin").stdout.strip()
        subprocess.run(
            ["git", "remote", "set-url", "origin", remote],
            cwd=origin,
            check=True,
            capture_output=True,
        )
        manifest = json.loads(capsule.joinpath("MANIFEST.json").read_bytes())
        for ref in manifest["boundary"]["refs"]:
            if ref == "main" or len(ref) == 40:
                continue
            subprocess.run(
                ["git", "branch", ref, f"origin/{ref}"],
                cwd=origin,
                check=True,
                capture_output=True,
            )
        arguments = [
            "--dir",
            origin,
            "checkpoint",
            "restore",
            "--from",
            str(capsule),
            "--manifest-sha256",
            exported["manifest_sha256"],
        ]
        return origin, arguments

    def resume(self, destination, seam=None, when="after", env=None):
        """`restore --from` over the disposable root an archive restore left."""
        _, outer, capsule_digest = self.carrier()
        capsule = os.path.join(
            destination,
            ".git",
            self.module.CHECKPOINT_ARCHIVE_RESTORE_STAGE_DIR,
            outer,
        )
        return self.start(
            [
                "--dir",
                destination,
                "checkpoint",
                "restore",
                "--from",
                capsule,
                "--manifest-sha256",
                capsule_digest,
            ],
            seam,
            when,
            env,
        )

    def wait_ready(self, competitor):
        """Wait, bounded, for a competitor to reach its seam."""
        deadline = time.monotonic() + BOUND
        while time.monotonic() < deadline:
            if os.path.exists(competitor.ready):
                return
            if competitor.process.poll() is not None:
                out, err = competitor.process.communicate(timeout=BOUND)
                self.fail(
                    f"competitor exited {competitor.process.returncode} before "
                    f"its seam\nstdout: {out}\nstderr: {err}"
                )
            time.sleep(0.01)
        self.fail("competitor did not reach its seam within the bound")

    def finish(self, competitor, *, release=True):
        """Release a paused competitor if asked, and wait for it to exit."""
        if release:
            Path(competitor.go).write_text("go\n", encoding="utf-8")
        out, err = competitor.process.communicate(timeout=BOUND)
        return competitor.process.returncode, out, err

    def kill(self, competitor):
        competitor.process.send_signal(signal.SIGKILL)
        competitor.process.communicate(timeout=BOUND)
        self.assertEqual(-signal.SIGKILL, competitor.process.returncode)

    # -- assertions -----------------------------------------------------------

    def marker(self, destination):
        return json.loads(Path(destination, MARKER).read_bytes())

    def assert_restored(self, destination, code, out, err):
        """One complete restore, with no lock file it made left behind."""
        self.assertEqual(0, code, err)
        payload = json.loads(out)
        worktree = payload["restore"]["worktree"]
        self.assertEqual(
            f"{worktree}\n",
            Path(destination, ".hexaemeron", "worktree").read_text(encoding="utf-8"),
        )
        self.assertFalse(os.path.exists(os.path.join(destination, MARKER)))
        ledger = Path(worktree, ".hexaemeron", "ledger.jsonl").read_bytes()
        events = [json.loads(line)["event"] for line in ledger.splitlines()]
        self.assertEqual(1, events.count("checkpoint:restore"))
        for command in (["verify"], ["status", "--json"], ["next"]):
            checked = subprocess.run(
                [sys.executable, HEXCTL, "--dir", worktree, *command],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, checked.returncode, checked.stderr)
        return worktree

    def assert_no_lock_files(self, destination, worktree):
        self.assertEqual(
            [".gitignore", "worktree"],
            sorted(os.listdir(os.path.join(destination, ".hexaemeron"))),
        )
        self.assertNotIn("lock", os.listdir(os.path.join(worktree, ".hexaemeron")))

    def assert_unlocked(self, path):
        """The kernel holds no lock on `path`: this process can take one."""
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(path, flags)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def assert_holder_names_restore(self, err, competitor):
        self.assertIn("another hexctl is holding this run", err)
        self.assertIn(f"pid {competitor.process.pid}", err)
        self.assertIn("`cmd_checkpoint_restore`", err)

    # -- SC-1: two archive restores into one destination ----------------------

    def test_one_winner_second_restore_during_inspector(self):
        # C1, and the step's counterfactual: on the parent controller the
        # second restore also passes admission and writes.
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_inspect_carrier_verified")
        self.wait_ready(first)
        code, out, err = self.finish(self.restore(destination))
        self.assertEqual((1, "", OCCUPIED), (code, out, err))
        self.assertEqual([], os.listdir(destination))
        self.assert_restored(destination, *self.finish(first))

    def test_one_winner_creator_paused_before_its_lock(self):
        # C2 and C3: the creator of an absent destination loses the lock to
        # a restore that admitted the directory it made, and removes nothing.
        destination = self.destination()
        creator = self.restore(destination, "_checkpoint_restore_flock", "before")
        self.wait_ready(creator)
        self.assertEqual([], os.listdir(destination))
        holder = self.restore(destination, "_checkpoint_inspect_carrier_verified")
        self.wait_ready(holder)
        code, out, err = self.finish(creator)
        self.assertEqual((1, "", OCCUPIED), (code, out, err))
        self.assertTrue(os.path.isdir(destination), "the loser removed the destination")
        self.assert_restored(destination, *self.finish(holder))

    def test_one_winner_between_scan_and_first_write(self):
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_restore_archive_destination")
        self.wait_ready(first)
        code, out, err = self.finish(self.restore(destination))
        self.assertEqual((1, "", OCCUPIED), (code, out, err))
        self.assertEqual([], os.listdir(destination))
        self.assert_restored(destination, *self.finish(first))

    def test_one_winner_second_restore_at_the_marker(self):
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_restore_marker")
        self.wait_ready(first)
        before = sorted(os.listdir(os.path.join(destination, ".hexaemeron")))
        code, out, err = self.finish(self.restore(destination))
        self.assertEqual((1, "", OCCUPIED), (code, out, err))
        self.assertEqual(
            before, sorted(os.listdir(os.path.join(destination, ".hexaemeron")))
        )
        self.assert_restored(destination, *self.finish(first))

    # -- SC-2: a resume against a live restore --------------------------------

    def test_live_resume_through_the_marker_refuses(self):
        # C5: a same-digest marker reads as a resume, so on the parent
        # controller this ran the transaction beside the live restore.
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_restore_marker")
        self.wait_ready(first)
        marker = Path(destination, MARKER).read_bytes()
        code, out, err = self.finish(self.resume(destination))
        self.assertEqual((1, "", HELD), (code, out, err))
        self.assertEqual(marker, Path(destination, MARKER).read_bytes())
        self.assertFalse(os.path.exists(self.marker(destination)["worktree"]))
        self.assert_restored(destination, *self.finish(first))

    def test_live_resume_after_publication_refuses(self):
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_atomic_publish")
        self.wait_ready(first)
        worktree = self.marker(destination)["worktree"]
        ledger = Path(worktree, ".hexaemeron", "ledger.jsonl").read_bytes()
        code, out, err = self.finish(self.resume(destination))
        self.assertEqual((1, "", HELD), (code, out, err))
        self.assertEqual(
            ledger, Path(worktree, ".hexaemeron", "ledger.jsonl").read_bytes()
        )
        self.assert_restored(destination, *self.finish(first))

    def test_live_resume_second_from_restore_refuses(self):
        # Two `--from` restores of one origin: the second meets the origin
        # lock before its clean check and writes nothing.
        origin, arguments = self.from_origin()
        environment = self.direct_environment()
        first = self.start(arguments, "_checkpoint_restore_marker", env=environment)
        self.wait_ready(first)
        marker = Path(origin, MARKER).read_bytes()
        code, out, err = self.finish(self.start(arguments, env=environment))
        self.assertEqual((1, "", HELD), (code, out, err))
        self.assertEqual(marker, Path(origin, MARKER).read_bytes())
        code, out, err = self.finish(first)
        self.assertEqual(0, code, err)
        payload = json.loads(out)
        self.assertEqual("new", payload["recovery"])
        self.assert_no_lock_files(origin, payload["worktree"])

    # -- SC-3: init on the restore's origin -----------------------------------

    def test_origin_init_after_the_marker_refuses(self):
        # C8: on the parent controller `init` took the origin's run lock and
        # rewrote the breadcrumb, and the restore refused after publication.
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_restore_marker")
        self.wait_ready(first)
        root = os.path.join(destination, ".hexaemeron")
        before = {name: Path(root, name).read_bytes() for name in os.listdir(root)}
        code, out, err = self.finish(
            self.start(["--dir", destination, "init", "--topic", "competing init"])
        )
        self.assertEqual(1, code, err)
        self.assert_holder_names_restore(err, first)
        after = {name: Path(root, name).read_bytes() for name in os.listdir(root)}
        self.assertEqual(before, after)
        self.assert_restored(destination, *self.finish(first))

    def test_origin_init_before_the_marker_one_refuses(self):
        # C9: `init` wins the origin; the restore refuses before it writes
        # any active state.
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_restore_marker", "before")
        self.wait_ready(first)
        init = self.start(["--dir", destination, "init", "--topic", "competing init"])
        init_code, _, init_err = self.finish(init)
        code, out, err = self.finish(first)
        self.assertEqual(0, init_code, init_err)
        self.assertEqual(
            (2, "", "hexctl: error: checkpoint restore requires an empty fresh origin\n"),
            (code, out, err),
        )
        worktree_home = os.path.join(destination, "tmp", "fiat")
        restored = [
            name
            for name in (os.listdir(worktree_home) if os.path.isdir(worktree_home) else [])
            if os.path.isfile(os.path.join(worktree_home, name, MARKER))
        ]
        self.assertEqual([], restored)
        self.assertFalse(os.path.exists(os.path.join(destination, MARKER)))

    # -- SC-4: a mutating command on the imported state ------------------------

    def test_imported_state_command_after_publication_refuses(self):
        # C6: on the parent controller `record` took the published root's
        # lock, appended to the ledger, and the restore refused.
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_atomic_publish")
        self.wait_ready(first)
        worktree = self.marker(destination)["worktree"]
        root = Path(worktree, ".hexaemeron")
        before = (root / "state.json").read_bytes(), (root / "ledger.jsonl").read_bytes()
        code, _, err = self.finish(
            self.start(["--dir", worktree, "record", "competing", '"write"'])
        )
        self.assertEqual(1, code, err)
        self.assert_holder_names_restore(err, first)
        after = (root / "state.json").read_bytes(), (root / "ledger.jsonl").read_bytes()
        self.assertEqual(before, after)
        self.assertEqual(worktree, self.assert_restored(destination, *self.finish(first)))

    def test_imported_state_absent_root_window_refuses(self):
        # C7: the command found no state root before the restore published
        # one, and resumes only after publication.
        destination = self.destination(create=True)
        worktree = self.derived_worktree(destination)
        command = self.start(
            ["--dir", worktree, "record", "competing", '"write"'],
            "refuse_missing_state",
            "before",
        )
        self.wait_ready(command)
        first = self.restore(destination, "_checkpoint_atomic_publish")
        self.wait_ready(first)
        self.assertEqual(worktree, self.marker(destination)["worktree"])
        root = Path(worktree, ".hexaemeron")
        before = (root / "state.json").read_bytes(), (root / "ledger.jsonl").read_bytes()
        code, _, err = self.finish(command)
        self.assertEqual(1, code, err)
        self.assert_holder_names_restore(err, first)
        after = (root / "state.json").read_bytes(), (root / "ledger.jsonl").read_bytes()
        self.assertEqual(before, after)
        self.assert_restored(destination, *self.finish(first))

    def test_absent_root_command_refuses_with_missing_state(self):
        # L4 changes no message: with no state root a non-init command refuses
        # with the words `load_state` prints, and leaves nothing behind.
        target = os.path.join(self.scratch, "no-state")
        os.mkdir(target)
        code, out, err = self.finish(
            self.start(["--dir", target, "record", "competing", '"write"'])
        )
        path = os.path.join(target, ".hexaemeron", "state.json")
        self.assertEqual(
            (2, "", f"hexctl: error: no state at {path}; run `hexctl init --topic ...` first\n"),
            (code, out, err),
        )
        self.assertEqual([], os.listdir(target))

    # -- SC-5: a killed restore ------------------------------------------------

    def test_killed_after_marker_releases_locks_and_resumes(self):
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_restore_marker")
        self.wait_ready(first)
        self.kill(first)
        root = os.path.join(destination, ".hexaemeron")
        self.assertEqual(
            [".gitignore", "checkpoint-restore.json", "lock"], sorted(os.listdir(root))
        )
        self.assert_unlocked(destination)
        self.assert_unlocked(os.path.join(root, "lock"))
        code, out, err = self.finish(self.resume(destination))
        self.assertEqual(0, code, err)
        self.assertEqual("new", json.loads(out)["recovery"])
        self.assertFalse(os.path.exists(os.path.join(destination, MARKER)))
        self.assertEqual(b"", Path(root, "lock").read_bytes())

    def test_killed_after_publication_retry_finalizes(self):
        destination = self.destination(create=True)
        first = self.restore(destination, "_checkpoint_atomic_publish")
        self.wait_ready(first)
        worktree = self.marker(destination)["worktree"]
        self.kill(first)
        lock = os.path.join(worktree, ".hexaemeron", "lock")
        self.assertTrue(os.path.isfile(lock))
        self.assert_unlocked(lock)
        self.assert_unlocked(os.path.join(destination, ".hexaemeron", "lock"))
        ledger = Path(worktree, ".hexaemeron", "ledger.jsonl").read_bytes()
        code, out, err = self.finish(self.resume(destination))
        self.assertEqual(0, code, err)
        self.assertEqual(
            "finalized-interrupted-publication", json.loads(out)["recovery"]
        )
        self.assertFalse(os.path.exists(os.path.join(destination, MARKER)))
        self.assertEqual(
            ledger, Path(worktree, ".hexaemeron", "ledger.jsonl").read_bytes()
        )
        self.assertEqual(b"", Path(lock).read_bytes())

    def test_killed_in_inspector_leaves_destination_admissible(self):
        destination = self.destination()
        first = self.restore(destination, "_checkpoint_inspect_carrier_verified")
        self.wait_ready(first)
        self.kill(first)
        self.assertEqual([], os.listdir(destination))
        self.assert_unlocked(destination)
        restored = self.restore(destination)
        worktree = self.assert_restored(destination, *self.finish(restored))
        self.assert_no_lock_files(destination, worktree)

    # -- uncontended restores --------------------------------------------------

    def test_uncontended_archive_restore_leaves_no_lock_file(self):
        destination = self.destination()
        worktree = self.assert_restored(
            destination, *self.finish(self.restore(destination))
        )
        self.assert_no_lock_files(destination, worktree)
        self.assert_unlocked(destination)

    def test_uncontended_from_restore_leaves_no_lock_file(self):
        origin, arguments = self.from_origin()
        code, out, err = self.finish(
            self.start(arguments, env=self.direct_environment())
        )
        self.assertEqual(0, code, err)
        payload = json.loads(out)
        self.assertEqual("new", payload["recovery"])
        self.assert_no_lock_files(origin, payload["worktree"])
        self.assert_unlocked(origin)
