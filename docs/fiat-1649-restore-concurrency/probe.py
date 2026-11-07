#!/usr/bin/env python3
"""Measure exclusion candidates for archive restore concurrency (skills#1649).

The selection cells run a model, not hexctl.py. The model repeats the points
of `checkpoint restore` where competing operations meet: admission of an
absent or empty destination, the inspector, `git init`, the relocation marker,
the derived worktree, the private stage and its no-replace publication, the
closed-inventory finalization check, the breadcrumb and marker retirement. It
also models the two other writers that reach the same paths: a mutating
`hexctl` command against the restored worktree, and `init` against the
restored origin, each with the run lock exactly as `held_lock` takes it at
eab25fcd.

Every competitor is a separate process. Order is fixed by file barriers: an
actor told to pause at a named point creates `<role>.<point>.ready` and waits
for `<role>.<point>.go`. The parent starts, releases and kills actors only
after observing those files, so no outcome depends on timing. A barrier left
unanswered for 30 s exits 97, which the parent reports as a probe failure.

Usage, from the target root:
  python3 .hexaemeron/design/probe.py select --candidate C --criterion K --out PATH
  python3 .hexaemeron/design/probe.py conform --candidate C --criterion K --root . --out PATH
  python3 .hexaemeron/design/probe.py platform
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import json
import os
import platform as host
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

REPORT_SCHEMA = "protasis-design-report/v1"
CANDIDATES = (
    "mutating-set",
    "destination-kernel-lock",
    "exclusive-entry",
    "admitted-fd-flock",
)
SELECTION_UNITS = {
    "uncontended-restore-completes": "boolean",
    "competing-restores-one-winner": "boolean",
    "live-resume-refused": "boolean",
    "killed-holder-resumes": "boolean",
    "killed-before-write-readmits": "boolean",
    "imported-state-excluded": "boolean",
    "origin-init-excluded": "boolean",
    "concurrent-holders-after-crash": "count",
    "lock-acquisitions-per-restore": "count",
    "entries-left-after-early-kill": "count",
}
CONFORMANCE_UNITS = {
    "restore-contention-guarded": "boolean",
    "imported-state-guarded": "boolean",
    "killed-restore-recovers": "boolean",
    "existing-restores-unchanged": "boolean",
}
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
LOCK_FLAGS = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC
STATE = ".hexaemeron"
MARKER = "checkpoint-restore.json"
BREADCRUMB = "worktree"
LOCK = "lock"
ENTRY = ".fiat-restore-lock"
WORKTREE = os.path.join("tmp", "fiat", "fiat-run")
STAGE = ".hexaemeron.restore-stage"
BARRIER_SECONDS = 30.0
LOCK_IN_ROOT = ("destination-kernel-lock", "admitted-fd-flock")


class Refused(Exception):
    """One modelled refusal: the actor exits 1 with the reason on stderr."""


def refuse(reason: str) -> None:
    raise Refused(reason)


class Actor:
    """One process's barrier and acquisition count."""

    def __init__(self, barrier: str, role: str, pauses: list[str]):
        self.barrier = barrier
        self.role = role
        self.pauses = set(pauses)
        self.visited = set()
        self.acquired = 0
        self.owned = []

    def at(self, point: str) -> None:
        if point not in self.pauses or point in self.visited:
            return
        self.visited.add(point)
        with open(os.path.join(self.barrier, f"{self.role}.{point}.ready"), "x"):
            pass
        go = os.path.join(self.barrier, f"{self.role}.{point}.go")
        deadline = time.monotonic() + BARRIER_SECONDS
        while not os.path.exists(go):
            if time.monotonic() > deadline:
                os._exit(97)
            time.sleep(0.001)

    def flock(self, descriptor: int) -> None:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            refuse("another hexctl is holding this run")
        except OSError:
            refuse("lock unsupported")
        self.acquired += 1

    def holder(self, descriptor: int) -> None:
        os.ftruncate(descriptor, 0)
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.write(descriptor, json.dumps({"pid": os.getpid()}).encode() + b"\n")


def open_lock(actor: Actor, directory: int, name: str = LOCK) -> int:
    """Open a run lock; one this actor creates is its own to unlink while held."""
    try:
        descriptor = os.open(name, LOCK_FLAGS | os.O_EXCL, 0o600, dir_fd=directory)
        actor.owned.append((directory, name))
    except FileExistsError:
        descriptor = os.open(name, LOCK_FLAGS, 0o600, dir_fd=directory)
    found = os.fstat(descriptor)
    if not stat.S_ISREG(found.st_mode) or found.st_nlink != 1:
        refuse("run lock is not a safe regular file")
    return descriptor


def release_owned(actor: Actor) -> None:
    """Unlink every lock file this actor created, while its lock is still held."""
    for directory, name in actor.owned:
        try:
            os.unlink(name, dir_fd=directory)
        except FileNotFoundError:
            pass
    actor.owned = []


def held_lock_as_today(actor: Actor, base: str, init: bool):
    """`held_lock` at eab25fcd: no state root and not init means no lock."""
    root = os.path.join(base, STATE)
    if not os.path.isdir(root):
        if not init:
            return None
        os.makedirs(root, exist_ok=True)
    descriptor = os.open(os.path.join(root, LOCK), LOCK_FLAGS, 0o600)
    actor.flock(descriptor)
    actor.holder(descriptor)
    return descriptor


def alive(pid) -> bool:
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def acquire_entry(actor: Actor, directory: int) -> None:
    """Exclusive-create entry; a dead holder's entry is reclaimed once."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        descriptor = os.open(ENTRY, flags, 0o600, dir_fd=directory)
    except FileExistsError:
        try:
            with open(os.open(ENTRY, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory), "rb") as handle:
                pid = json.loads(handle.read() or b"{}").get("pid")
        except (OSError, ValueError):
            pid = None
        if alive(pid):
            refuse("another restore holds the destination")
        actor.at("prelock")
        try:
            os.unlink(ENTRY, dir_fd=directory)
        except FileNotFoundError:
            pass
        try:
            descriptor = os.open(ENTRY, flags, 0o600, dir_fd=directory)
        except FileExistsError:
            refuse("another restore holds the destination")
    else:
        actor.at("prelock")
    os.write(descriptor, json.dumps({"pid": os.getpid()}).encode() + b"\n")
    os.close(descriptor)
    actor.acquired += 1
    actor.at("acquired")


def write_file(path: str, data: bytes, exclusive: bool = False) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC
    flags |= os.O_EXCL if exclusive else os.O_TRUNC
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, data)
    finally:
        os.close(descriptor)


def read(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def restore(actor: Actor, candidate: str, destination: str, digest: str, resume: bool) -> None:
    """One archive restore (or a `--from` style resume of an existing origin)."""
    try:
        transaction(actor, candidate, destination, digest, resume)
    finally:
        release_owned(actor)


def transaction(actor: Actor, candidate: str, destination: str, digest: str, resume: bool) -> None:
    held = []
    if not resume:
        if candidate == "mutating-set":
            descriptor = held_lock_as_today(actor, destination, init=False)
            if descriptor is not None:
                held.append(descriptor)
        created = False
        try:
            found = os.lstat(destination)
        except FileNotFoundError:
            try:
                os.mkdir(destination, 0o700)
            except OSError:
                refuse("destination-occupied")
            created = True
        else:
            if stat.S_ISLNK(found.st_mode) or not stat.S_ISDIR(found.st_mode):
                refuse("destination-occupied")
        anchor = os.open(destination, DIRECTORY_FLAGS)
        actor.at("prelock")
        excluded = candidate == "mutating-set"
        try:
            if candidate == "admitted-fd-flock":
                actor.flock(anchor)
                excluded = True
                actor.at("acquired")
            if os.listdir(anchor):
                refuse("destination-occupied")
            actor.at("scanned")
            if candidate == "destination-kernel-lock":
                try:
                    os.mkdir(STATE, 0o700, dir_fd=anchor)
                except FileExistsError:
                    pass
                root = os.open(STATE, DIRECTORY_FLAGS, dir_fd=anchor)
                lock = open_lock(actor, root)
                actor.flock(lock)
                actor.holder(lock)
                held.append(lock)
                excluded = True
                actor.at("acquired")
                if set(os.listdir(anchor)) != {STATE} or not set(os.listdir(root)) <= {LOCK, ".gitignore"}:
                    refuse("destination-occupied")
                write_file(os.path.join(destination, STATE, ".gitignore"), b"*\n")
            if candidate == "exclusive-entry":
                acquire_entry(actor, anchor)
                excluded = True
                if set(os.listdir(anchor)) != {ENTRY}:
                    refuse("destination-occupied")
        except Refused:
            # An entry this restore created is its own to remove. A created
            # destination is removed only by the restore that holds the
            # exclusion; a loser leaves the directory the winner admitted.
            if candidate == "exclusive-entry" and actor.acquired:
                os.unlink(ENTRY, dir_fd=anchor)
            if created and excluded and not os.listdir(anchor):
                os.rmdir(destination)
            raise
        os.fchdir(anchor)
        actor.at("admitted")
        os.makedirs(".git", exist_ok=True)
        write_file(os.path.join(".git", "HEAD"), digest.encode())
        write_file(os.path.join(".git", "config"), digest.encode())
        actor.at("initialised")
    else:
        anchor = os.open(destination, DIRECTORY_FLAGS)
        os.fchdir(anchor)
        if candidate != "exclusive-entry":
            # The entry's seam sits inside `acquire_entry`, after it has read
            # a dead holder and before it reclaims: the acquisition step.
            actor.at("prelock")
        if candidate == "mutating-set":
            descriptor = held_lock_as_today(actor, destination, init=False)
            if descriptor is not None:
                held.append(descriptor)
                actor.at("acquired")
        elif candidate == "admitted-fd-flock":
            actor.flock(anchor)
            actor.at("acquired")
        elif candidate == "destination-kernel-lock":
            root = os.open(STATE, DIRECTORY_FLAGS)
            lock = open_lock(actor, root)
            actor.flock(lock)
            actor.holder(lock)
            held.append(lock)
            actor.at("acquired")
        else:
            acquire_entry(actor, anchor)

    # The relocation marker.
    allowed = {".gitignore", MARKER, BREADCRUMB}
    if candidate in LOCK_IN_ROOT:
        allowed.add(LOCK)
    if candidate == "admitted-fd-flock":
        try:
            os.mkdir(STATE, 0o700)
        except FileExistsError:
            pass
        root = os.open(STATE, DIRECTORY_FLAGS)
        lock = open_lock(actor, root)
        actor.flock(lock)
        actor.holder(lock)
        held.append(lock)
    resumed = False
    if os.path.lexists(STATE):
        names = set(os.listdir(STATE))
        if MARKER in names:
            if not names <= allowed:
                refuse("checkpoint restore requires an empty fresh origin")
            if read(os.path.join(STATE, MARKER)) != digest.encode():
                refuse("checkpoint restore marker belongs to another transaction")
            resumed = True
        elif not (candidate in LOCK_IN_ROOT and names <= {LOCK, ".gitignore"}):
            refuse("checkpoint restore requires an empty fresh origin")
    else:
        try:
            os.mkdir(STATE, 0o700)
        except OSError:
            refuse("checkpoint restore marker could not be published")
    if not resumed:
        if not os.path.exists(os.path.join(STATE, ".gitignore")):
            write_file(os.path.join(STATE, ".gitignore"), b"*\n")
        try:
            write_file(os.path.join(STATE, MARKER), digest.encode(), exclusive=True)
        except FileExistsError:
            refuse("checkpoint restore marker could not be published")
    actor.at("marker")

    worktree_state = os.path.join(WORKTREE, STATE)
    carries = candidate != "mutating-set"
    if not (resumed and os.path.exists(os.path.join(worktree_state, "state.json"))):
        stage = os.path.join(WORKTREE, STAGE)
        if resumed and (os.path.lexists(WORKTREE) or os.path.lexists(stage)):
            refuse("checkpoint restore transaction was interrupted before active state")
        if os.path.lexists(WORKTREE):
            refuse("checkpoint restore derived worktree is occupied")
        os.makedirs(os.path.dirname(WORKTREE), exist_ok=True)
        try:
            os.mkdir(WORKTREE)
        except FileExistsError:
            refuse("checkpoint restore could not create its derived worktree")
        actor.at("worktree")
        os.mkdir(stage, 0o700)
        write_file(os.path.join(stage, "state.json"), digest.encode())
        write_file(os.path.join(stage, "ledger.jsonl"), f"restore {digest}\n".encode())
        if carries:
            stage_fd = os.open(stage, DIRECTORY_FLAGS)
            lock = open_lock(actor, stage_fd)
            actor.flock(lock)
            actor.holder(lock)
            held.append(lock)
        if os.path.lexists(worktree_state):
            refuse("checkpoint restore derived worktree is occupied")
        os.rename(stage, worktree_state)
        actor.at("published")
    elif carries:
        lock = open_lock(actor, os.open(worktree_state, DIRECTORY_FLAGS))
        actor.flock(lock)
        actor.holder(lock)
        held.append(lock)

    # Finalization: the closed inventory, then breadcrumb and retirement.
    names = set(os.listdir(worktree_state))
    if carries:
        names.discard(LOCK)
    if names != {"state.json", "ledger.jsonl"}:
        refuse("checkpoint restore changed opaque controller evidence")
    if read(os.path.join(worktree_state, "ledger.jsonl")) != f"restore {digest}\n".encode():
        refuse("checkpoint restored ledger changed")
    payload = (os.path.join(destination, WORKTREE) + "\n").encode()
    try:
        write_file(os.path.join(STATE, BREADCRUMB), payload, exclusive=True)
    except FileExistsError:
        if read(os.path.join(STATE, BREADCRUMB)) != payload:
            refuse("checkpoint restore breadcrumb is not transaction-owned")
    actor.at("finalising")
    try:
        if read(os.path.join(STATE, MARKER)) != digest.encode():
            refuse("checkpoint restore marker changed before retirement")
        os.unlink(os.path.join(STATE, MARKER))
    except FileNotFoundError:
        refuse("checkpoint restore marker changed before retirement")
    if candidate == "exclusive-entry":
        os.unlink(ENTRY)
    actor.at("done")
    release_owned(actor)
    for descriptor in held:
        os.close(descriptor)


def mutate(actor: Actor, candidate: str, destination: str) -> None:
    """A mutating hexctl command against the restored worktree (`done`, `record`)."""
    base = os.path.join(destination, WORKTREE)
    root = os.path.join(base, STATE)
    state = os.path.join(root, "state.json")
    if not os.path.isdir(root):
        actor.at("unlocked")
        if not os.path.exists(state):
            refuse("no state")
        if candidate != "mutating-set":
            refuse("the run state directory appeared while this command was starting")
    else:
        descriptor = os.open(os.path.join(root, LOCK), LOCK_FLAGS, 0o600)
        actor.flock(descriptor)
        actor.holder(descriptor)
    if not os.path.exists(state):
        refuse("no state")
    with open(os.path.join(root, "ledger.jsonl"), "ab") as handle:
        handle.write(b"mutation\n")


def init(actor: Actor, candidate: str, destination: str) -> None:
    """`init` from the restored origin: run lock, then the breadcrumb rewrite."""
    held_lock_as_today(actor, destination, init=True)
    root = os.path.join(destination, STATE)
    breadcrumb = os.path.join(root, BREADCRUMB)
    try:
        recorded = [line for line in read(breadcrumb).decode().splitlines() if line]
    except FileNotFoundError:
        recorded = []
    live = {entry for entry in recorded if os.path.exists(os.path.join(entry, STATE, "state.json"))}
    live.add(os.path.join(destination, "tmp", "fiat", "fiat-other"))
    if not os.path.exists(os.path.join(root, ".gitignore")):
        write_file(os.path.join(root, ".gitignore"), b"*\n")
    write_file(breadcrumb, "".join(f"{entry}\n" for entry in sorted(live)).encode())


def actor_main(args) -> int:
    actor = Actor(args.barrier, args.role, args.pause or [])
    try:
        if args.kind == "restore":
            restore(actor, args.candidate, args.destination, args.digest, False)
        elif args.kind == "resume":
            restore(actor, args.candidate, args.destination, args.digest, True)
        elif args.kind == "mutate":
            mutate(actor, args.candidate, args.destination)
        else:
            init(actor, args.candidate, args.destination)
    except Refused as refusal:
        sys.stderr.write(f"refused: {refusal}\n")
        return 1
    sys.stdout.write(json.dumps({"acquired": actor.acquired}) + "\n")
    return 0


# -------------------------------------------------------------- scenarios


class Scene:
    """One scenario's scratch parent, barrier directory and actors."""

    def __init__(self, candidate: str):
        self.candidate = candidate
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="fiat1649-"))
        self.barrier = os.path.join(self.root, "barrier")
        os.mkdir(self.barrier)
        self.destination = os.path.join(self.root, "dest")
        self.processes = []

    def close(self) -> None:
        for process in self.processes:
            if process.poll() is None:
                process.kill()
                process.wait()
        shutil.rmtree(self.root, ignore_errors=True)

    def spawn(self, role: str, kind: str, digest: str = "", pauses=()):
        argv = [sys.executable, os.path.abspath(__file__), "actor", "--kind", kind,
                "--role", role, "--candidate", self.candidate, "--destination",
                self.destination, "--digest", digest or "none", "--barrier", self.barrier]
        for point in pauses:
            argv += ["--pause", point]
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(process)
        return process

    def ready(self, role: str, point: str, process) -> bool:
        """Wait until `role` reaches `point`; False when it exited first."""
        path = os.path.join(self.barrier, f"{role}.{point}.ready")
        deadline = time.monotonic() + BARRIER_SECONDS
        while not os.path.exists(path):
            if process.poll() is not None:
                return os.path.exists(path)
            if time.monotonic() > deadline:
                raise SystemExit(f"probe barrier timed out at {role}.{point}")
            time.sleep(0.001)
        return True

    def go(self, role: str, point: str) -> None:
        with open(os.path.join(self.barrier, f"{role}.{point}.go"), "x"):
            pass

    @staticmethod
    def finish(process) -> int:
        process.communicate(timeout=60)
        if process.returncode == 97:
            raise SystemExit("probe actor barrier timed out")
        return process.returncode

    def kill(self, process) -> None:
        process.send_signal(signal.SIGKILL)
        process.communicate(timeout=60)

    def complete(self, digest: str) -> bool:
        """The destination holds exactly one complete restore of `digest`."""
        d = self.destination
        try:
            if set(os.listdir(d)) != {".git", STATE, "tmp"}:
                return False
            if read(os.path.join(d, ".git", "HEAD")) != digest.encode():
                return False
            if read(os.path.join(d, ".git", "config")) != digest.encode():
                return False
            if set(os.listdir(os.path.join(d, STATE))) - {LOCK} != {".gitignore", BREADCRUMB}:
                return False
            if read(os.path.join(d, STATE, BREADCRUMB)) != (os.path.join(d, WORKTREE) + "\n").encode():
                return False
            if set(os.listdir(os.path.join(d, WORKTREE))) != {STATE}:
                return False
            active = os.path.join(d, WORKTREE, STATE)
            if set(os.listdir(active)) - {LOCK} != {"state.json", "ledger.jsonl"}:
                return False
            return (read(os.path.join(active, "state.json")) == digest.encode()
                    and read(os.path.join(active, "ledger.jsonl")) == f"restore {digest}\n".encode())
        except OSError:
            return False

    def one_winner(self, first, second, digests) -> bool:
        codes = [self.finish(first), self.finish(second)]
        if sorted(codes) != [0, 1]:
            return False
        return self.complete(digests[codes.index(0)])


def scene(candidate: str, body) -> object:
    current = Scene(candidate)
    try:
        return body(current)
    finally:
        current.close()


def uncontended(s: Scene) -> bool:
    lone = s.spawn("a", "restore", "aaaa")
    if s.finish(lone) != 0 or not s.complete("aaaa"):
        return False
    shutil.rmtree(s.destination)
    os.mkdir(s.destination, 0o700)
    again = s.spawn("b", "restore", "bbbb")
    if s.finish(again) != 0 or not s.complete("bbbb"):
        return False
    occupied = s.spawn("c", "restore", "cccc")
    return s.finish(occupied) == 1 and s.complete("bbbb")


def held_during_inspector(s: Scene) -> bool:
    os.mkdir(s.destination, 0o700)
    first = s.spawn("a", "restore", "aaaa", ["admitted"])
    s.ready("a", "admitted", first)
    second = s.spawn("b", "restore", "bbbb")
    second.wait(timeout=60)
    s.go("a", "admitted")
    return s.one_winner(first, second, ["aaaa", "bbbb"])


def creator_loses_lock(s: Scene) -> bool:
    second = s.spawn("b", "restore", "bbbb", ["prelock"])
    s.ready("b", "prelock", second)
    first = s.spawn("a", "restore", "aaaa", ["admitted"])
    s.ready("a", "admitted", first)
    s.go("b", "prelock")
    second.wait(timeout=60)
    s.go("a", "admitted")
    return s.one_winner(first, second, ["aaaa", "bbbb"])


def scan_then_lock(s: Scene) -> bool:
    os.mkdir(s.destination, 0o700)
    second = s.spawn("b", "restore", "bbbb", ["scanned"])
    s.ready("b", "scanned", second)
    first = s.spawn("a", "restore", "aaaa")
    first.wait(timeout=60)
    s.go("b", "scanned")
    return s.one_winner(first, second, ["aaaa", "bbbb"])


def live_resume(s: Scene) -> bool:
    first = s.spawn("a", "restore", "aaaa", ["marker"])
    s.ready("a", "marker", first)
    resumer = s.spawn("r", "resume", "aaaa")
    code = s.finish(resumer)
    s.go("a", "marker")
    return code == 1 and s.finish(first) == 0 and s.complete("aaaa")


def killed_resumes(s: Scene) -> bool:
    first = s.spawn("a", "restore", "aaaa", ["marker"])
    s.ready("a", "marker", first)
    s.kill(first)
    resumer = s.spawn("r", "resume", "aaaa")
    return s.finish(resumer) == 0 and s.complete("aaaa")


def killed_readmits(s: Scene) -> bool:
    first = s.spawn("a", "restore", "aaaa", ["admitted"])
    s.ready("a", "admitted", first)
    s.kill(first)
    again = s.spawn("b", "restore", "bbbb")
    return s.finish(again) == 0 and s.complete("bbbb")


def writer_after_publication(s: Scene) -> bool:
    first = s.spawn("a", "restore", "aaaa", ["published"])
    s.ready("a", "published", first)
    writer = s.spawn("m", "mutate")
    code = s.finish(writer)
    s.go("a", "published")
    return code == 1 and s.finish(first) == 0 and s.complete("aaaa")


def writer_in_absent_root_window(s: Scene) -> bool:
    first = s.spawn("a", "restore", "aaaa", ["worktree", "published"])
    s.ready("a", "worktree", first)
    writer = s.spawn("m", "mutate", pauses=["unlocked"])
    s.ready("m", "unlocked", writer)
    s.go("a", "worktree")
    s.ready("a", "published", first)
    s.go("m", "unlocked")
    code = s.finish(writer)
    s.go("a", "published")
    return code == 1 and s.finish(first) == 0 and s.complete("aaaa")


def init_after_marker(s: Scene) -> bool:
    first = s.spawn("a", "restore", "aaaa", ["marker"])
    s.ready("a", "marker", first)
    starter = s.spawn("i", "init")
    code = s.finish(starter)
    s.go("a", "marker")
    return code == 1 and s.finish(first) == 0 and s.complete("aaaa")


def init_before_marker(s: Scene) -> bool:
    first = s.spawn("a", "restore", "aaaa", ["initialised"])
    s.ready("a", "initialised", first)
    starter = s.spawn("i", "init")
    code = s.finish(starter)
    s.go("a", "initialised")
    restored = s.finish(first)
    if sorted([code, restored]) != [0, 1]:
        return False
    if restored == 0:
        return s.complete("aaaa")
    return not os.path.lexists(os.path.join(s.destination, WORKTREE))


def holders_after_crash(s: Scene) -> int:
    first = s.spawn("a", "restore", "aaaa", ["marker"])
    s.ready("a", "marker", first)
    s.kill(first)
    contenders = [s.spawn(role, "resume", "aaaa", ["prelock", "acquired"]) for role in ("r", "q")]
    for role, process in zip(("r", "q"), contenders):
        s.ready(role, "prelock", process)
    holding = 0
    for role, process in zip(("r", "q"), contenders):
        s.go(role, "prelock")
        if s.ready(role, "acquired", process):
            holding += 1
    return holding


def acquisitions(s: Scene) -> int:
    lone = s.spawn("a", "restore", "aaaa")
    out, _ = lone.communicate(timeout=60)
    if lone.returncode != 0:
        raise SystemExit("uncontended model restore failed")
    return json.loads(out)["acquired"]


def entries_after_early_kill(s: Scene) -> int:
    """Entries a restore killed during the inspector leaves in its destination."""
    first = s.spawn("a", "restore", "aaaa", ["admitted"])
    s.ready("a", "admitted", first)
    s.kill(first)
    return sum(len(directories) + len(files) for _, directories, files in os.walk(s.destination))


def measure(candidate: str, criterion: str):
    run = lambda body: scene(candidate, body)  # noqa: E731
    if criterion == "uncontended-restore-completes":
        return run(uncontended)
    if criterion == "competing-restores-one-winner":
        return all(run(body) for body in (held_during_inspector, creator_loses_lock, scan_then_lock))
    if criterion == "live-resume-refused":
        return run(live_resume)
    if criterion == "killed-holder-resumes":
        return run(killed_resumes)
    if criterion == "killed-before-write-readmits":
        return run(killed_readmits)
    if criterion == "imported-state-excluded":
        return all(run(body) for body in (writer_after_publication, writer_in_absent_root_window))
    if criterion == "origin-init-excluded":
        return all(run(body) for body in (init_after_marker, init_before_marker))
    if criterion == "concurrent-holders-after-crash":
        return run(holders_after_crash)
    if criterion == "lock-acquisitions-per-restore":
        return run(acquisitions)
    if criterion == "entries-left-after-early-kill":
        return run(entries_after_early_kill)
    raise SystemExit(f"unknown criterion {criterion}")


# --------------------------------------------------------------- platform

HOLDER = r"""
import fcntl, os, sys, time
path, ready, mode = sys.argv[1], sys.argv[2], sys.argv[3]
flags = os.O_RDONLY | (os.O_DIRECTORY if mode == "dir" else 0)
fd = os.open(path, flags | (0 if mode == "inherit" else os.O_CLOEXEC))
fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
if mode in ("inherit", "cloexec"):
    os.set_inheritable(fd, mode == "inherit")
    import subprocess
    child = subprocess.Popen(["sleep", "30"], close_fds=True,
                             pass_fds=(fd,) if mode == "inherit" else ())
    open(ready + ".child", "w").write(str(child.pid))
open(ready, "w").close()
time.sleep(30)
"""


def contended(path: str, directory: bool) -> bool:
    """True when this process cannot take the lock on `path` right now."""
    descriptor = os.open(path, os.O_RDONLY | (os.O_DIRECTORY if directory else 0))
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    finally:
        os.close(descriptor)
    return False


def hold(path: str, ready: str, mode: str):
    process = subprocess.Popen([sys.executable, "-c", HOLDER, path, ready, mode])
    deadline = time.monotonic() + BARRIER_SECONDS
    while not os.path.exists(ready):
        if process.poll() is not None or time.monotonic() > deadline:
            raise SystemExit("platform holder did not start")
        time.sleep(0.001)
    return process


def platform_facts() -> dict:
    root = tempfile.mkdtemp(prefix="fiat1649-platform-")
    facts = {"system": host.system(), "release": host.release(), "python": host.python_version()}
    try:
        directory = os.path.join(root, "dest")
        os.mkdir(directory)
        mine = os.open(directory, DIRECTORY_FLAGS)
        try:
            fcntl.flock(mine, fcntl.LOCK_EX | fcntl.LOCK_NB)
            facts["flock_on_directory_fd"] = True
        except OSError as error:
            facts["flock_on_directory_fd"] = errno.errorcode.get(error.errno, str(error.errno))
        other = os.open(directory, DIRECTORY_FLAGS)
        try:
            fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
            facts["second_open_blocks"] = False
        except BlockingIOError as error:
            facts["second_open_blocks"] = True
            facts["contended_errno"] = errno.errorcode[error.errno]
        try:
            fcntl.lockf(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
            facts["posix_write_lock_on_directory_fd"] = "acquired"
        except OSError as error:
            facts["posix_write_lock_on_directory_fd"] = errno.errorcode.get(error.errno, str(error.errno))
        os.close(other)
        os.close(mine)

        holder = hold(directory, os.path.join(root, "r1"), "dir")
        facts["other_process_blocked"] = contended(directory, True)
        os.rename(directory, os.path.join(root, "moved"))
        os.mkdir(directory)
        facts["lock_follows_renamed_directory"] = contended(os.path.join(root, "moved"), True)
        facts["new_directory_at_old_name_is_free"] = not contended(directory, True)
        holder.send_signal(signal.SIGKILL)
        holder.wait()
        facts["released_on_sigkill"] = not contended(os.path.join(root, "moved"), True)

        stage = os.path.join(root, "stage")
        os.mkdir(stage)
        lock = os.path.join(stage, "lock")
        open(lock, "w").close()
        holder = hold(lock, os.path.join(root, "r2"), "file")
        os.rename(stage, os.path.join(root, "published"))
        facts["file_lock_follows_renamed_parent"] = contended(os.path.join(root, "published", "lock"), False)
        holder.send_signal(signal.SIGKILL)
        holder.wait()

        for mode in ("inherit", "cloexec"):
            target = os.path.join(root, f"{mode}.lock")
            open(target, "w").close()
            ready = os.path.join(root, f"r-{mode}")
            holder = hold(target, ready, mode)
            child = int(open(ready + ".child").read())
            holder.send_signal(signal.SIGKILL)
            holder.wait()
            facts[f"{mode}_fd_held_by_live_child_after_kill"] = contended(target, False)
            os.kill(child, signal.SIGKILL)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return facts


# ------------------------------------------------------------ conformance

CONFORMANCE_MODULE = "test_checkpoint_restore_concurrency.py"
CONFORMANCE_TESTS = {
    "restore-contention-guarded": [
        (CONFORMANCE_MODULE, "one_winner"),
        (CONFORMANCE_MODULE, "live_resume"),
        (CONFORMANCE_MODULE, "origin_init"),
    ],
    "imported-state-guarded": [(CONFORMANCE_MODULE, "imported_state")],
    "killed-restore-recovers": [(CONFORMANCE_MODULE, "killed")],
    "existing-restores-unchanged": [
        ("test_checkpoint_restore_binding.py", "test_"),
        ("test_hexctl_checkpoint.py", "restore"),
        ("test_hexctl.py", "TestRunLock"),
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
    actor = sub.add_parser("actor")
    actor.add_argument("--kind", required=True, choices=("restore", "resume", "mutate", "init"))
    actor.add_argument("--role", required=True)
    actor.add_argument("--candidate", required=True, choices=CANDIDATES)
    actor.add_argument("--destination", required=True)
    actor.add_argument("--digest", required=True)
    actor.add_argument("--barrier", required=True)
    actor.add_argument("--pause", action="append")
    args = parser.parse_args(argv)
    if args.mode == "actor":
        return actor_main(args)
    if args.mode == "platform":
        print(json.dumps(platform_facts(), indent=1, sort_keys=True))
        return 0
    if args.mode == "select":
        value = measure(args.candidate, args.criterion)
        command = (f"python3 .hexaemeron/design/probe.py select --candidate {args.candidate} "
                   f"--criterion {args.criterion} --out {args.out}")
        write_report(args.out, args.candidate, args.criterion, value,
                     SELECTION_UNITS[args.criterion], command)
        return 0
    value = conform(os.path.abspath(args.root), args.criterion)
    command = (f"python3 .hexaemeron/design/probe.py conform --candidate {args.candidate} "
               f"--criterion {args.criterion} --root {args.root} --out {args.out}")
    write_report(args.out, args.candidate, args.criterion, value, "boolean", command)
    return 0


if __name__ == "__main__":
    sys.exit(main())
