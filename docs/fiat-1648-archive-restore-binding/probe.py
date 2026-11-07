#!/usr/bin/env python3
"""Design probe for Fiat run #1648: keep archive restore on its admitted directory.

Three modes. ``select`` and ``conform`` each write one closed
``protasis-design-report/v1`` object to an ``--out`` path that must not
already exist, and print the same bytes. ``platform`` prints facts only.

``select``   runs one candidate model of the archive restore's destination
             writes against a fresh disposable fixture and measures one
             selection criterion.
``conform``  runs the built controller's named tests under ``--root`` and
             checks one conformance criterion for the selected candidate only.
``platform`` prints which descriptor primitives this interpreter and kernel
             offer, with a swap observed through an inherited working
             directory. It writes no report.

The model is not ``hexctl.py``. It repeats the shape of the writes
``checkpoint restore --archive`` makes after admission, in order: ``git init``,
a bundle fetch, a base checkout, an origin URL, capsule members under
``.git/``, a relocation marker under ``.hexaemeron/``, the worktree home, ``git
worktree add``, a private stage published by rename, a breadcrumb, marker
retirement and removal of the capsule root. Each candidate performs those
writes under its own binding rule. Every fixture lives in a private
``mkdtemp`` tree that is removed before exit, Git runs with no global or system
configuration, commits are unsigned, and nothing touches the network.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


REPORT_SCHEMA = "protasis-design-report/v1"
SELECTED = "anchored-cwd"
CANDIDATES = ("path-unchanged", "identity-recheck", "anchored-cwd", "private-build-adopt")
SELECTION_UNITS = {
    "unswapped-restore-completes": "boolean",
    "directory-swap-writes-nothing": "boolean",
    "symlink-swap-writes-nothing": "boolean",
    "interrupted-cleanup-stays-bound": "boolean",
    "residue-follows-reference": "boolean",
    "transaction-race-leaked-trials": "count",
    "name-resolving-writes": "count",
    "identity-probes-per-restore": "count",
    "bytes-built-outside-destination": "bytes",
}
CONFORMANCE_UNITS = {
    "replacement-regression-guarded": "boolean",
    "nonempty-symlink-still-refuse": "boolean",
    "interrupted-restore-stays-bound": "boolean",
    "from-mode-unchanged": "boolean",
}
RACE_TRIALS = 100
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
RUN_BRANCH = "fiat/run"
WORKTREE = os.path.join("tmp", "fiat", "fiat-run")
WORKTREE_ADMIN = os.path.join(".git", "worktrees", "fiat-run")
RESTORE_ROOT = os.path.join(".git", "fiat-checkpoint-restore", "0" * 64)
MARKER = os.path.join(".hexaemeron", "restore-marker.json")
CAPSULE = {
    "MANIFEST.json": b"{}\n",
    "controller/state.json": b"{}\n",
    "controller/ledger.jsonl": b"\n",
}

RACER = r"""
import os, random, sys, time
parent, stop = sys.argv[1], sys.argv[2]
dest, away = os.path.join(parent, "dest"), os.path.join(parent, "away")
n = 0
while not os.path.exists(stop):
    try:
        os.rename(dest, away)
    except OSError:
        time.sleep(0.0005)
        continue
    parked = os.path.join(parent, "replacement-%d" % n)
    n += 1
    try:
        os.mkdir(dest)
        time.sleep(random.uniform(0.0002, 0.002))
        os.rename(dest, parked)
    except OSError:
        pass
    try:
        os.rename(away, dest)
    except OSError:
        pass
    time.sleep(random.uniform(0.0002, 0.002))
"""


class Refused(Exception):
    """The candidate refused; the trial records it and inspects the residue."""


class Interrupted(Exception):
    """An injected stop standing in for a killed restore."""


def git_environment(home: str) -> dict[str, str]:
    return {
        "PATH": os.defpath + ":/usr/bin:/usr/local/bin:/opt/homebrew/bin",
        "HOME": home,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "probe",
        "GIT_AUTHOR_EMAIL": "probe@invalid",
        "GIT_COMMITTER_NAME": "probe",
        "GIT_COMMITTER_EMAIL": "probe@invalid",
        "LC_ALL": "C",
    }


def build_source(root: str, env: dict[str, str]) -> tuple[str, str]:
    """One two-branch repository and its bundle, both private to this probe."""
    source = os.path.join(root, "source")
    os.mkdir(source)
    for argv in (
        ["init", "--quiet", "--initial-branch", "main"],
        ["commit", "--quiet", "--allow-empty", "--no-gpg-sign", "-m", "base"],
    ):
        subprocess.run(["git", *argv], cwd=source, env=env, check=True)
    for index in range(20):
        Path(source, f"file-{index}.txt").write_text(f"{index}\n" * 50)
    subprocess.run(["git", "add", "."], cwd=source, env=env, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "--no-gpg-sign", "-m", "files"],
        cwd=source, env=env, check=True,
    )
    subprocess.run(["git", "branch", RUN_BRANCH], cwd=source, env=env, check=True)
    bundle = os.path.join(root, "repository.bundle")
    subprocess.run(
        ["git", "bundle", "create", "--quiet", bundle, "--all"],
        cwd=source, env=env, check=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "main"], cwd=source, env=env, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    return bundle, commit


def identity(fd: int) -> tuple[int, int]:
    value = os.fstat(fd)
    return value.st_dev, value.st_ino


def tree_bytes(path: str) -> int:
    total = 0
    for root, directories, files in os.walk(path, followlinks=False):
        for name in files:
            with contextlib.suppress(OSError):
                total += os.lstat(os.path.join(root, name)).st_size
    return total


def tree_entries(path: str) -> int:
    count = 0
    for _root, directories, files in os.walk(path, followlinks=False):
        count += len(directories) + len(files)
    return count


class Model:
    """One candidate's binding rule over the shared write sequence."""

    def __init__(self, candidate, destination, descriptor, env, bundle, commit, private_root):
        self.candidate = candidate
        self.destination = destination
        self.descriptor = descriptor
        self.admitted = identity(descriptor)
        self.env = env
        self.bundle = bundle
        self.commit = commit
        self.private_root = private_root
        self.saved = None
        self.build = None
        self.build_descriptor = None
        self.probes = 0
        self.built_outside = 0
        self.name_writes = 0
        self.after_repository = None

    # -- the identity probe every bound candidate shares -------------------

    def names_admitted(self) -> bool:
        self.probes += 1
        try:
            fd = os.open(self.destination, DIRECTORY_FLAGS)
        except OSError:
            return False
        try:
            return (
                identity(fd) == self.admitted
                and os.path.realpath(self.destination) == self.destination
            )
        finally:
            os.close(fd)

    def seal(self) -> None:
        if self.candidate != "path-unchanged" and not self.names_admitted():
            raise Refused("destination no longer names the admitted directory")

    def check(self) -> None:
        """Before and after every write: only identity-recheck probes here."""
        if self.candidate == "identity-recheck" and not self.names_admitted():
            raise Refused("destination no longer names the admitted directory")

    # -- binding rule ------------------------------------------------------

    def begin(self) -> None:
        if self.candidate == "anchored-cwd":
            self.saved = os.open(".", os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0))
            os.fchdir(self.descriptor)
        elif self.candidate == "private-build-adopt":
            self.build = os.path.realpath(tempfile.mkdtemp(prefix="build-", dir=self.private_root))
            self.build_descriptor = os.open(self.build, DIRECTORY_FLAGS)

    def end(self) -> None:
        if self.saved is not None:
            os.fchdir(self.saved)
            os.close(self.saved)
            self.saved = None
        if self.build_descriptor is not None:
            os.close(self.build_descriptor)
            self.build_descriptor = None

    def path(self, relative: str) -> str:
        if self.candidate == "anchored-cwd":
            return relative
        root = self.build if self.candidate == "private-build-adopt" else self.destination
        return root if relative == "." else os.path.join(root, relative)

    def target(self, relative: str) -> str:
        """The path one controller write opens, counted when it crosses the name."""
        resolved = self.path(relative)
        if resolved == self.destination or resolved.startswith(self.destination + os.sep):
            self.name_writes += 1
        return resolved

    def git(self, *argv: str) -> None:
        self.check()
        if self.candidate == "anchored-cwd":
            self.seal()
            completed = subprocess.run(["git", *argv], env=self.env, capture_output=True)
            self.seal()
        else:
            completed = subprocess.run(
                ["git", *argv], cwd=os.path.realpath(self.path(".")), env=self.env,
                capture_output=True,
            )
        self.check()
        if completed.returncode != 0:
            raise Refused("git " + argv[0] + " failed")

    def write(self, relative: str, data: bytes) -> None:
        self.check()
        target = self.target(relative)
        os.makedirs(os.path.dirname(target) or ".", 0o700, exist_ok=True)
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
        self.check()

    def mkdir(self, relative: str) -> None:
        self.check()
        os.makedirs(self.target(relative), 0o700, exist_ok=True)
        self.check()

    def rename(self, source: str, target: str) -> None:
        self.check()
        os.rename(self.target(source), self.target(target))
        self.check()

    def unlink(self, relative: str) -> None:
        self.check()
        os.unlink(self.target(relative))
        self.check()

    def rmtree(self, relative: str) -> None:
        self.check()
        shutil.rmtree(self.target(relative), ignore_errors=True)
        self.check()

    def recorded_worktree_is_destination(self) -> None:
        """Git's own record of the worktree must name the admitted path."""
        if self.candidate == "path-unchanged":
            return
        with open(os.path.join(self.path(WORKTREE), ".git"), "rb") as handle:
            recorded = handle.read()
        expected = os.path.join(self.path("."), WORKTREE_ADMIN)
        if self.candidate == "anchored-cwd":
            expected = os.path.join(self.destination, WORKTREE_ADMIN)
        if recorded != ("gitdir: " + expected + "\n").encode():
            raise Refused("git recorded a worktree path outside the admitted name")

    def adopt(self) -> None:
        """private-build-adopt only: move the finished build in by descriptor."""
        self.seal()
        self.built_outside = tree_bytes(self.build)
        for name in sorted(os.listdir(self.build_descriptor)):
            os.rename(name, name, src_dir_fd=self.build_descriptor, dst_dir_fd=self.descriptor)
        for relative, payload in (
            (os.path.join(WORKTREE, ".git"), "gitdir: " + os.path.join(self.destination, WORKTREE_ADMIN) + "\n"),
            (os.path.join(WORKTREE_ADMIN, "gitdir"), os.path.join(self.destination, WORKTREE, ".git") + "\n"),
        ):
            fd = os.open(relative, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW, dir_fd=self.descriptor)
            try:
                os.write(fd, payload.encode())
            finally:
                os.close(fd)
        os.rmdir(self.build)
        self.build = None

    # -- the restore's write sequence ------------------------------------

    def restore(self, *, interrupt_after_worktree: bool = False) -> None:
        self.begin()
        try:
            self.git("init", "--quiet")
            self.git("fetch", "--quiet", self.bundle, "+refs/heads/*:refs/heads/*", "--no-tags")
            self.git("checkout", "--quiet", "-b", "base", self.commit)
            self.git("config", "remote.origin.url", "https://github.com/example/example.git")
            if self.after_repository is not None:
                self.after_repository()
            for name, data in CAPSULE.items():
                self.write(os.path.join(RESTORE_ROOT, name), data)
            self.write(os.path.join(".hexaemeron", ".gitignore"), b"*\n")
            self.write(MARKER, b"{}\n")
            self.write(os.path.join("tmp", "fiat", ".gitignore"), b"*\n")
            worktree_argument = WORKTREE if self.candidate == "anchored-cwd" else self.path(WORKTREE)
            self.git("worktree", "add", "--quiet", worktree_argument, RUN_BRANCH)
            self.recorded_worktree_is_destination()
            if interrupt_after_worktree:
                swap_now(os.path.dirname(self.destination))
                raise Interrupted()
            stage = os.path.join(WORKTREE, ".hexaemeron.restore-stage")
            self.mkdir(stage)
            for name, data in CAPSULE.items():
                if name.startswith("controller/"):
                    self.write(os.path.join(stage, os.path.basename(name)), data)
            self.rename(stage, os.path.join(WORKTREE, ".hexaemeron"))
            self.write(os.path.join(".hexaemeron", "worktree"), (self.destination + "\n").encode())
            if self.candidate == "private-build-adopt":
                self.adopt()
            self.seal()
            if self.candidate == "private-build-adopt":
                os.unlink(MARKER, dir_fd=self.descriptor)
                shutil.rmtree(RESTORE_ROOT, dir_fd=self.descriptor, ignore_errors=True)
            else:
                self.unlink(MARKER)
                self.rmtree(RESTORE_ROOT)
            self.seal()
        finally:
            self.end()

    def cleanup_created(self) -> None:
        """The restore created the destination; remove it only while empty."""
        if self.candidate == "path-unchanged":
            with contextlib.suppress(OSError):
                os.rmdir(self.destination)
            return
        if self.names_admitted():
            with contextlib.suppress(OSError):
                os.rmdir(self.destination)


def swap_now(parent: str, *, symlink_to: str | None = None) -> None:
    """Move the admitted directory aside and put a replacement at its name."""
    destination = os.path.join(parent, "dest")
    os.rename(destination, os.path.join(parent, "away"))
    if symlink_to is None:
        os.mkdir(destination, 0o700)
    else:
        os.symlink(symlink_to, destination)


def admit(parent: str) -> tuple[str, int]:
    destination = os.path.join(os.path.realpath(parent), "dest")
    os.mkdir(destination, 0o700)
    return destination, os.open(destination, DIRECTORY_FLAGS)


def expected_layout(destination: str, env: dict[str, str]) -> bool:
    worktree = os.path.join(destination, WORKTREE)
    if not (
        os.path.isdir(os.path.join(destination, ".git"))
        and os.path.isfile(os.path.join(worktree, ".hexaemeron", "state.json"))
        and os.path.isfile(os.path.join(destination, ".hexaemeron", "worktree"))
        and not os.path.lexists(os.path.join(destination, MARKER))
        and not os.path.lexists(os.path.join(destination, RESTORE_ROOT))
        and os.path.isfile(os.path.join(destination, "file-0.txt"))
    ):
        return False
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=worktree, env=env,
        capture_output=True, text=True,
    )
    listed = subprocess.run(
        ["git", "worktree", "list", "--porcelain"], cwd=destination, env=env,
        capture_output=True, text=True,
    )
    return (
        top.returncode == 0
        and top.stdout.strip() == worktree
        and f"worktree {worktree}\n" in listed.stdout
        and "prunable" not in listed.stdout
    )


def trial(candidate: str, root: str, env, bundle, commit, scenario: str) -> dict:
    parent = tempfile.mkdtemp(prefix="trial-", dir=root)
    private_root = os.path.join(root, "private")
    os.makedirs(private_root, 0o700, exist_ok=True)
    destination, descriptor = admit(parent)
    model = Model(candidate, destination, descriptor, env, bundle, commit, private_root)
    outcome = {"refused": False, "completed": False, "interrupted": False}
    sentinel = None
    racer = None
    stop = os.path.join(parent, "stop")
    try:
        if scenario == "directory-swap":
            swap_now(parent)
        elif scenario == "symlink-swap":
            sentinel = tempfile.mkdtemp(prefix="sentinel-", dir=root)
            swap_now(parent, symlink_to=sentinel)
        elif scenario == "race":
            racer = subprocess.Popen([sys.executable, "-I", "-c", RACER, parent, stop])
            time.sleep(0.01)
        elif scenario == "late-race":
            def start() -> None:
                nonlocal racer
                racer = subprocess.Popen([sys.executable, "-I", "-c", RACER, parent, stop])
                time.sleep(0.01)
            model.after_repository = start
        try:
            model.restore(interrupt_after_worktree=(scenario == "interrupt"))
            outcome["completed"] = True
        except Interrupted:
            outcome["interrupted"] = True
        except (Refused, OSError, subprocess.SubprocessError):
            outcome["refused"] = True
        if not outcome["completed"]:
            model.cleanup_created()
    finally:
        if racer is not None:
            Path(stop).touch()
            racer.wait(timeout=30)
        os.close(descriptor)
    outcome["probes"] = model.probes
    outcome["name_writes"] = model.name_writes
    outcome["built_outside"] = model.built_outside
    if scenario in ("directory-swap", "interrupt"):
        replacement = os.path.join(parent, "dest")
        outcome["replacement_present"] = os.path.isdir(replacement) and not os.path.islink(replacement)
        outcome["replacement_entries"] = tree_entries(replacement) if outcome["replacement_present"] else 0
        outcome["marker_in_admitted"] = os.path.isfile(os.path.join(parent, "away", MARKER))
    if scenario == "symlink-swap":
        outcome["sentinel_entries"] = tree_entries(sentinel)
        outcome["symlink_intact"] = os.path.islink(os.path.join(parent, "dest"))
    if scenario in ("race", "late-race"):
        replacements = [
            os.path.join(parent, name) for name in os.listdir(parent)
            if name.startswith("replacement-")
        ]
        outcome["leaked"] = sum(1 for path in replacements if os.listdir(path))
    if scenario == "unswapped":
        outcome["layout"] = expected_layout(destination, env)
    shutil.rmtree(parent, ignore_errors=True)
    shutil.rmtree(private_root, ignore_errors=True)
    if sentinel is not None:
        shutil.rmtree(sentinel, ignore_errors=True)
    return outcome


def measure(candidate: str, criterion: str) -> object:
    root = os.path.realpath(tempfile.mkdtemp(prefix="fiat-1648-probe-"))
    try:
        home = os.path.join(root, "home")
        os.mkdir(home)
        env = git_environment(home)
        bundle, commit = build_source(root, env)
        if criterion == "unswapped-restore-completes":
            outcome = trial(candidate, root, env, bundle, commit, "unswapped")
            return bool(outcome["completed"] and outcome["layout"])
        if criterion == "directory-swap-writes-nothing":
            outcome = trial(candidate, root, env, bundle, commit, "directory-swap")
            return bool(
                outcome["refused"] and outcome["replacement_present"]
                and outcome["replacement_entries"] == 0
            )
        if criterion == "symlink-swap-writes-nothing":
            outcome = trial(candidate, root, env, bundle, commit, "symlink-swap")
            return bool(outcome["refused"] and outcome["symlink_intact"] and outcome["sentinel_entries"] == 0)
        if criterion == "interrupted-cleanup-stays-bound":
            outcome = trial(candidate, root, env, bundle, commit, "interrupt")
            return bool(
                outcome["interrupted"] and outcome["replacement_present"]
                and outcome["replacement_entries"] == 0
            )
        if criterion == "residue-follows-reference":
            outcome = trial(candidate, root, env, bundle, commit, "interrupt")
            return bool(outcome["interrupted"] and outcome["marker_in_admitted"])
        if criterion in ("racing-swap-leaked-trials", "transaction-race-leaked-trials"):
            scenario = "race" if criterion == "racing-swap-leaked-trials" else "late-race"
            return sum(
                1 for _ in range(RACE_TRIALS)
                if trial(candidate, root, env, bundle, commit, scenario)["leaked"]
            )
        if criterion == "name-resolving-writes":
            return int(trial(candidate, root, env, bundle, commit, "unswapped")["name_writes"])
        if criterion == "identity-probes-per-restore":
            return int(trial(candidate, root, env, bundle, commit, "unswapped")["probes"])
        if criterion == "bytes-built-outside-destination":
            return int(trial(candidate, root, env, bundle, commit, "unswapped")["built_outside"])
        raise SystemExit(f"unknown selection criterion {criterion}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def platform_facts() -> dict:
    """Descriptor primitives, and what a child sees after a parent-side swap."""
    facts = {"platform": sys.platform, "python": sys.version.split()[0]}
    facts["dir_fd"] = sorted(function.__name__ for function in os.supports_dir_fd)
    facts["O_DIRECTORY"] = hasattr(os, "O_DIRECTORY")
    facts["O_NOFOLLOW"] = hasattr(os, "O_NOFOLLOW")
    try:
        libc = ctypes.CDLL(None, use_errno=True)
    except OSError:
        libc = None
    for name in ("renameat", "renameat2", "renamex_np", "renameatx_np", "unlinkat", "mkdirat"):
        facts[name] = bool(libc is not None and hasattr(libc, name))
    root = os.path.realpath(tempfile.mkdtemp(prefix="fiat-1648-platform-"))
    saved = os.open(".", os.O_RDONLY | os.O_DIRECTORY)
    try:
        destination, descriptor = admit(root)
        os.fchdir(descriptor)
        swap_now(root)
        subprocess.run(["sh", "-c", "echo x > child-wrote"], check=True)
        facts["child_inherits_admitted_cwd"] = (
            os.listdir(os.path.join(root, "away")) == ["child-wrote"]
            and os.listdir(destination) == []
        )
        facts["getcwd_follows_inode"] = os.getcwd() == os.path.join(root, "away")
        os.fchdir(saved)
        for prefix in ("/dev/fd", "/proc/self/fd"):
            alias = f"{prefix}/{descriptor}"
            try:
                facts["alias " + prefix] = "child-wrote" in os.listdir(alias)
            except OSError as error:
                facts["alias " + prefix] = error.strerror
        os.close(descriptor)
    finally:
        os.fchdir(saved)
        os.close(saved)
        shutil.rmtree(root, ignore_errors=True)
    return facts


CONFORMANCE_TESTS = {
    "replacement-regression-guarded": [
        ("test_checkpoint_restore_binding.py", "replacement"),
    ],
    "nonempty-symlink-still-refuse": [
        ("test_hexctl_checkpoint_archive.py", "test_restore_from_archive_refuses_non_empty_destination"),
        ("test_hexctl_checkpoint_archive.py", "test_archive_restore_accepts_a_symlinked_destination_parent"),
        ("test_checkpoint_restore_binding.py", "symlink_destination"),
    ],
    "interrupted-restore-stays-bound": [
        ("test_checkpoint_restore_binding.py", "interrupted"),
    ],
    "from-mode-unchanged": [
        ("test_hexctl_checkpoint.py", "restore"),
    ],
}
RAN = re.compile(rb"^Ran (\d+) tests? in ", re.MULTILINE)


def conform(root: str, criterion: str) -> bool:
    tests = os.path.join(root, "plugins", "hexaemeron", "tests")
    for module, pattern in CONFORMANCE_TESTS[criterion]:
        if not os.path.isfile(os.path.join(tests, module)):
            return False
        env = dict(os.environ)
        env.pop("FORCE_COLOR", None)
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", tests, "-t", tests,
             "-p", module, "-k", pattern],
            cwd=root, env=env, capture_output=True, timeout=3600,
        )
        ran = RAN.search(completed.stderr)
        if (
            completed.returncode != 0
            or ran is None
            or int(ran.group(1)) < 1
            or b"skipped=" in completed.stderr
        ):
            return False
    return True


def write_report(out: str, candidate: str, criterion: str, value, unit: str, command: str) -> None:
    if os.path.lexists(out):
        raise SystemExit("refusing to replace an existing report")
    report = {
        "schema": REPORT_SCHEMA,
        "candidate": candidate,
        "criterion": criterion,
        "value": value,
        "unit": unit,
        "command": command,
        "exit": 0,
    }
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "xb") as handle:
        handle.write(data)
    sys.stdout.write(data.decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    select = sub.add_parser("select")
    select.add_argument("--candidate", required=True, choices=CANDIDATES)
    select.add_argument("--criterion", required=True, choices=sorted(SELECTION_UNITS))
    select.add_argument("--out", required=True)
    check = sub.add_parser("conform")
    check.add_argument("--candidate", required=True, choices=CANDIDATES)
    check.add_argument("--criterion", required=True, choices=sorted(CONFORMANCE_UNITS))
    check.add_argument("--root", required=True)
    check.add_argument("--out", required=True)
    sub.add_parser("platform")
    sub.add_parser("observe")
    args = parser.parse_args(argv)
    if args.mode == "platform":
        print(json.dumps(platform_facts(), indent=1, sort_keys=True))
        return 0
    if args.mode == "observe":
        # Whole-sequence race, Git children included: prose evidence, not a cell.
        print(json.dumps({
            candidate: measure(candidate, "racing-swap-leaked-trials")
            for candidate in CANDIDATES
        }, indent=1))
        return 0
    command = "python3 .hexaemeron/design/probe.py " + " ".join(
        argv if argv is not None else sys.argv[1:]
    )
    if args.mode == "select":
        value = measure(args.candidate, args.criterion)
        write_report(args.out, args.candidate, args.criterion, value,
                     SELECTION_UNITS[args.criterion], command)
        return 0
    if args.candidate != SELECTED:
        raise SystemExit("conformance applies to the selected candidate only")
    value = conform(os.path.realpath(args.root), args.criterion)
    write_report(args.out, args.candidate, args.criterion, value,
                 CONFORMANCE_UNITS[args.criterion], command)
    return 0


if __name__ == "__main__":
    sys.exit(main())
