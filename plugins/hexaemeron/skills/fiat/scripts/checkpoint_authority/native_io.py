"""Bounded local I/O for the native adapter; the caller owns host isolation."""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import time

from .canonical import Refusal, digest

DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
STDOUT_MAX = 65536
STDERR_MAX = 16384
CARRIER_MAX = 1073741824
FILE_MAX = 67108864
MANIFEST_MAX = 1048576


def identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def same_directory(left, right):
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


@contextlib.contextmanager
def directory(path, *, private=False):
    """Hold every directory edge without following links; detect observed swaps."""
    path = Path(path)
    if not path.is_absolute() or str(path) != os.path.normpath(path):
        raise Refusal("native-path", "native")
    with contextlib.ExitStack() as stack:
        parent = os.open(path.anchor, DIRECTORY_FLAGS)
        stack.callback(os.close, parent)
        links = []
        for part in path.parts[1:]:
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=parent)
            stack.callback(os.close, child)
            links.append((parent, part, child))
            parent = child

        def check():
            for owner, name, child in links:
                named = os.stat(name, dir_fd=owner, follow_symlinks=False)
                held = os.fstat(child)
                if not stat.S_ISDIR(named.st_mode) or not same_directory(named, held):
                    raise Refusal("native-path-changed", "native")
            last = os.fstat(parent)
            if private and (last.st_uid != os.geteuid() or last.st_mode & 0o077):
                raise Refusal("native-scratch-ownership", "native")

        check()
        yield parent, check
        check()


@contextlib.contextmanager
def regular(path, maximum):
    """Keep a bounded stable single-link leaf open across its consumer."""
    path = Path(path)
    with directory(path.parent) as (parent, check_parent):
        fd = os.open(path.name, FILE_FLAGS, dir_fd=parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 <= before.st_size <= maximum:
                raise Refusal("native-file-limit-or-kind", "native")

            def check():
                named = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                if identity(before) != identity(os.fstat(fd)) or identity(before) != identity(named):
                    raise Refusal("native-file-changed", "native")
                check_parent()

            check()
            yield fd, before.st_size, check
            check()
        finally:
            os.close(fd)


def read(path, maximum=FILE_MAX):
    with regular(path, maximum) as (fd, size, check):
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(maximum + 1)
        if len(data) != size:
            raise Refusal("native-file-changed", "native")
        check()
        return data


def hash_file(path, maximum=FILE_MAX):
    with regular(path, maximum) as (fd, size, check):
        hasher = hashlib.sha256()
        count = 0
        while chunk := os.read(fd, 1024 * 1024):
            count += len(chunk)
            if count > maximum:
                raise Refusal("native-file-limit-or-kind", "native")
            hasher.update(chunk)
        check()
        if count != size:
            raise Refusal("native-file-changed", "native")
        return hasher.hexdigest(), count


def create(path, data):
    with directory(Path(path).parent, private=True) as (parent, check):
        fd = os.open(Path(path).name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        check()


def copy_archive(source, destination, expected):
    """Capture one archive once; all later commands consume this private copy."""
    with regular(source, CARRIER_MAX) as (source_fd, size, check_source):
        with directory(Path(destination).parent, private=True) as (parent, check_parent):
            target = os.open(Path(destination).name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=parent)
            hasher = hashlib.sha256()
            copied = 0
            with os.fdopen(target, "wb") as stream:
                while chunk := os.read(source_fd, 1024 * 1024):
                    copied += len(chunk)
                    if copied > size or copied > CARRIER_MAX:
                        raise Refusal("native-archive-limit", "native")
                    stream.write(chunk)
                    hasher.update(chunk)
                stream.flush()
                os.fsync(stream.fileno())
            check_source(); check_parent()
            if not size or copied != size or hasher.hexdigest() != expected:
                raise Refusal("native-input-digest", "native")
            return copied


@dataclass(frozen=True)
class NativeTool:
    """Trusted caller pin; never populated from archive or output fields."""
    name: str
    path: str
    sha256: str

    def check(self):
        if self.name not in ("python", "git", "gpg", "gpgconf", "ssh-keygen") or type(self.sha256) is not str or re.fullmatch(r"[a-f0-9]{64}", self.sha256) is None:
            raise Refusal("native-tool-pin", "native")
        if hash_file(self.path, 256 * 1024 * 1024)[0] != self.sha256:
            raise Refusal("native-tool-pin", "native")


@dataclass(frozen=True)
class Execution:
    stage: str
    attempt_id: str
    input_sha256: str
    exit: int
    stdout: bytes
    stderr: bytes
    duration_ms: int

    def summary(self):
        return {"stage": self.stage, "attempt_id": self.attempt_id,
                "input_sha256": self.input_sha256, "exit": self.exit,
                "output_sha256": digest(self.stdout), "log_sha256": digest(self.stderr),
                "output_bytes": len(self.stdout), "log_bytes": len(self.stderr),
                "duration_ms": self.duration_ms}


def execute(tool, args, cwd, environment, *, stage, attempt_id, input_sha256,
            deadline, input_bytes=b""):
    """Use fixed argv and one deadline, draining both bounded streams concurrently."""
    tool.check()
    if time.monotonic() >= deadline:
        raise Refusal("native-deadline", stage)
    import tempfile
    started = time.monotonic()
    with tempfile.TemporaryFile() as source:
        source.write(input_bytes); source.seek(0)
        process = subprocess.Popen([tool.path, *args], cwd=cwd, env=environment,
            stdin=source, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=True)
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ, "stdout")
                selector.register(process.stderr, selectors.EVENT_READ, "stderr")
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise Refusal("native-deadline", stage)
                    for key, _ in selector.select(min(remaining, 0.1)):
                        chunk = os.read(key.fileobj.fileno(), 8192)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        buffers[key.data].extend(chunk)
                        cap = STDOUT_MAX if key.data == "stdout" else STDERR_MAX
                        if len(buffers[key.data]) > cap:
                            raise Refusal("native-output-limit", stage)
                result = process.wait(timeout=max(0.001, deadline - time.monotonic()))
        finally:
            # A dead leader does not establish that descendants released their pipes.
            try:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    process.wait(timeout=max(0.0, deadline - time.monotonic()))
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                process.wait()
            finally:
                process.stdout.close(); process.stderr.close()
    tool.check()
    return Execution(stage, attempt_id, input_sha256, result, bytes(buffers["stdout"]),
                     bytes(buffers["stderr"]), int((time.monotonic() - started) * 1000))
