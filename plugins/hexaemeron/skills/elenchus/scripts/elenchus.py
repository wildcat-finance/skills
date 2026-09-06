#!/usr/bin/env python3
"""Elenchus guard check.

A fix is guarded when its changed test records an assertion failure against
the parent tree. The runner writes a declared structured report; process text
and ordinary exit codes remain diagnostic evidence and never decide whether a
test asserted, passed, or broke before assertion.

Exit 0 unless ``--require-guard`` is set and the result is not ``guarded``.
"""

from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
import errno
import hashlib
import json
import os
import re
import selectors
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

TEST_NAMES = ("test_", "_test.", ".test.", ".spec.", ".t.sol")
TEST_DIRS = ("test", "tests", "spec", "__tests__")
REPORT_FORMATS = ("unittest-json-v1", "forge-junit-v1", "node-test-json-v1")
REPORT_PLACEHOLDER = "{report}"
MAX_REPORT_BYTES = 1024 * 1024
MAX_DIAGNOSTIC_CHARS = 4000
MAX_DIAGNOSTIC_BYTES = 16_000
MAX_GUARD_BLOB_BYTES = 2 * 1024 * 1024
MAX_GUARD_BLOBS_BYTES = 16 * 1024 * 1024
MAX_GUARD_BLOBS = 4096
MAX_GUARD_PATH_BYTES = 1024
MAX_COMMAND_ARGUMENTS = 16
MAX_COMMAND_BYTES = 4096
MAX_PARENT_ENTRIES = 100_000
MAX_PARENT_PATH_BYTES = 4096
MAX_PARENT_TREE_BYTES = 32 * 1024 * 1024
MAX_PARENT_BLOB_BYTES = 32 * 1024 * 1024
MAX_PARENT_BLOBS_BYTES = 256 * 1024 * 1024
MAX_PARENT_GIT_SECONDS = 30
MAX_PARENT_GIT_REAP_SECONDS = 0.25
GUARD_BLOB_KEYS = {"path", "status", "mode", "oid", "bytes", "sha256", "raw"}
OBJECT_ID_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
LINUX_NO_DESCENDANT_WRAPPER = """\
import ctypes
import errno
import os
import sys

class SockFilter(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("jt", ctypes.c_ubyte),
        ("jf", ctypes.c_ubyte),
        ("k", ctypes.c_uint32),
    ]

class SockFprog(ctypes.Structure):
    _fields_ = [
        ("len", ctypes.c_ushort),
        ("filter", ctypes.POINTER(SockFilter)),
    ]

machine = os.uname().machine
if machine in ("x86_64", "amd64"):
    audit_arch = 0xC000003E
    clone_nr = 56
    process_syscalls = (57, 58)
elif machine in ("aarch64", "arm64"):
    audit_arch = 0xC00000B7
    clone_nr = 220
    process_syscalls = ()
else:
    raise OSError(errno.ENOTSUP, "unsupported seccomp architecture")

# Classic BPF over struct seccomp_data. Threads retain CLONE_THREAD and are
# allowed; every operation that can create another process is refused. clone3
# receives ENOSYS so runtimes can fall back to clone for their worker threads.
BPF_LD_W_ABS = 0x20
BPF_JMP_JEQ_K = 0x15
BPF_JMP_JSET_K = 0x45
BPF_ALU_AND_K = 0x54
BPF_RET_K = 0x06
SECCOMP_RET_KILL_PROCESS = 0x80000000
SECCOMP_RET_ERRNO = 0x00050000
SECCOMP_RET_ALLOW = 0x7FFF0000
CLONE_THREAD = 0x00010000
X32_SYSCALL_BIT = 0x40000000
CLONE3_NR = 435

instructions = [
    (BPF_LD_W_ABS, 0, 0, 4),
    (BPF_JMP_JEQ_K, 1, 0, audit_arch),
    (BPF_RET_K, 0, 0, SECCOMP_RET_KILL_PROCESS),
    (BPF_LD_W_ABS, 0, 0, 0),
]
if audit_arch == 0xC000003E:
    instructions.extend([
        (BPF_JMP_JSET_K, 0, 1, X32_SYSCALL_BIT),
        (BPF_RET_K, 0, 0, SECCOMP_RET_KILL_PROCESS),
    ])
for syscall_nr in process_syscalls:
    instructions.extend([
        (BPF_JMP_JEQ_K, 0, 1, syscall_nr),
        (BPF_RET_K, 0, 0, SECCOMP_RET_ERRNO | errno.EPERM),
    ])
instructions.extend([
    (BPF_JMP_JEQ_K, 0, 1, CLONE3_NR),
    (BPF_RET_K, 0, 0, SECCOMP_RET_ERRNO | errno.ENOSYS),
    (BPF_JMP_JEQ_K, 1, 0, clone_nr),
    (BPF_RET_K, 0, 0, SECCOMP_RET_ALLOW),
    (BPF_LD_W_ABS, 0, 0, 16),
    (BPF_ALU_AND_K, 0, 0, CLONE_THREAD),
    (BPF_JMP_JEQ_K, 1, 0, CLONE_THREAD),
    (BPF_RET_K, 0, 0, SECCOMP_RET_ERRNO | errno.EPERM),
    (BPF_RET_K, 0, 0, SECCOMP_RET_ALLOW),
])
filters = (SockFilter * len(instructions))(
    *(SockFilter(*instruction) for instruction in instructions)
)
program = SockFprog(len(filters), filters)
libc = ctypes.CDLL(None, use_errno=True)
if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
    raise OSError(ctypes.get_errno(), "cannot lock process privileges")
if libc.prctl(22, 2, ctypes.byref(program)) != 0:  # PR_SET_SECCOMP, filter
    raise OSError(ctypes.get_errno(), "cannot install process-creation filter")
target_fd = int(sys.argv[1])
if os.execve not in os.supports_fd:
    raise OSError(errno.ENOTSUP, "descriptor execution is unavailable")
os.execve(target_fd, [sys.argv[2], *sys.argv[3:]], os.environ)
"""
DARWIN_NO_DESCENDANT_PROFILE = (
    "(version 1) (allow default) (deny process-fork)"
)
DARWIN_BOUND_EXEC_WRAPPER = """\
import errno
import os
import stat
import sys

parent_fd = int(sys.argv[1])
target_fd = int(sys.argv[2])
leaf = sys.argv[3]
expected = tuple(int(part) for part in sys.argv[4].split(","))

def identity(observed):
    return (
        observed.st_dev, observed.st_ino, observed.st_mode, observed.st_nlink,
        observed.st_size, observed.st_mtime_ns, observed.st_ctime_ns,
    )

opened = os.fstat(target_fd)
named = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
named_path = os.stat(sys.argv[5], follow_symlinks=False)
if (
    identity(opened) != expected
    or identity(named) != expected
    or identity(named_path) != expected
    or not stat.S_ISREG(opened.st_mode)
):
    raise OSError(errno.ESTALE, "the executable binding changed")
os.execv(sys.argv[5], [sys.argv[5], *sys.argv[6:]])
"""


class ReportError(ValueError):
    """A runner report failed the declared structural contract."""


@dataclass(frozen=True)
class RunnerReport:
    complete: bool
    executed: int
    assertion_failures: int
    errors: int
    skipped: int


@dataclass(frozen=True)
class GuardRun:
    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool
    streams_complete: bool


@dataclass
class ExecutableBinding:
    """One executable held through a stable no-follow descriptor chain."""

    path: str
    leaf: str
    descriptor: int
    directories: tuple[tuple[int | None, str | None, int, tuple[int, ...]], ...]
    identity: tuple[int, ...]

    @property
    def parent_descriptor(self) -> int:
        return self.directories[-1][2]

    def stable(self) -> bool:
        try:
            for containing, name, descriptor, expected in self.directories:
                if _file_identity(os.fstat(descriptor)) != expected:
                    return False
                named = (
                    os.lstat(os.path.sep)
                    if containing is None
                    else os.stat(name, dir_fd=containing, follow_symlinks=False)
                )
                if _file_identity(named) != expected or not stat.S_ISDIR(named.st_mode):
                    return False
            opened = os.fstat(self.descriptor)
            named = os.stat(
                self.leaf,
                dir_fd=self.parent_descriptor,
                follow_symlinks=False,
            )
            return (
                _file_identity(opened) == self.identity
                and _file_identity(named) == self.identity
                and stat.S_ISREG(opened.st_mode)
            )
        except OSError:
            return False

    def close(self) -> None:
        if self.descriptor < 0:
            return
        with contextlib.suppress(OSError):
            os.close(self.descriptor)
        for _, _, descriptor, _ in reversed(self.directories):
            with contextlib.suppress(OSError):
                os.close(descriptor)
        self.descriptor = -1
        self.directories = ()


@dataclass
class GuardCommand:
    """A contained argv and every descriptor that makes it immutable."""

    argv: list[str]
    pass_fds: tuple[int, ...]
    bindings: tuple[ExecutableBinding, ...]

    def stable(self) -> bool:
        return all(binding.stable() for binding in self.bindings)

    def close(self) -> None:
        for binding in reversed(self.bindings):
            binding.close()


def _trusted_search_path() -> str:
    """Return a caller-independent executable search path."""
    candidates = [
        str(Path(sys.executable).resolve().parent),
        *os.defpath.split(os.pathsep),
    ]
    return os.pathsep.join(dict.fromkeys(path for path in candidates if path))


def _effective_execute_bit(observed: os.stat_result) -> int:
    if not hasattr(os, "geteuid") or not hasattr(os, "getegid"):
        return 0
    if os.geteuid() == observed.st_uid:
        return stat.S_IXUSR
    groups = {os.getegid(), *getattr(os, "getgroups", lambda: [])()}
    if observed.st_gid in groups:
        return stat.S_IXGRP
    return stat.S_IXOTH


def _trusted_executable(raw: str) -> ExecutableBinding:
    """Resolve and retain one executable through a no-follow descriptor walk."""
    if os.sep in raw or (os.altsep and os.altsep in raw):
        if not os.path.isabs(raw):
            raise ReportError("the test command executable path must be absolute")
        candidate = raw
    else:
        candidate = shutil.which(raw, path=_trusted_search_path())
        if candidate is None:
            raise FileNotFoundError(raw)
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise OSError("safe executable descriptor access is unavailable")
    resolved = Path(candidate).resolve(strict=True)
    if not resolved.is_absolute() or resolved.anchor != os.path.sep:
        raise OSError("the test command executable could not be resolved safely")
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    file_flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | os.O_NONBLOCK
        | getattr(os, "O_CLOEXEC", 0)
    )
    directories: list[
        tuple[int | None, str | None, int, tuple[int, ...]]
    ] = []
    descriptor: int | None = None
    try:
        root_named = os.lstat(os.path.sep)
        root_fd = os.open(os.path.sep, directory_flags)
        root_identity = _file_identity(os.fstat(root_fd))
        if (
            root_identity != _file_identity(root_named)
            or not stat.S_ISDIR(root_named.st_mode)
        ):
            os.close(root_fd)
            raise OSError("the executable root was replaced")
        directories.append((None, None, root_fd, root_identity))
        parent_fd = root_fd
        for component in resolved.parts[1:-1]:
            named = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            child_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            identity = _file_identity(os.fstat(child_fd))
            if identity != _file_identity(named) or not stat.S_ISDIR(named.st_mode):
                os.close(child_fd)
                raise OSError("an executable directory was replaced")
            directories.append((parent_fd, component, child_fd, identity))
            parent_fd = child_fd

        leaf = resolved.parts[-1]
        named = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        descriptor = os.open(leaf, file_flags, dir_fd=parent_fd)
        opened = os.fstat(descriptor)
        identity = _file_identity(opened)
        execute_bit = _effective_execute_bit(opened)
        if (
            identity != _file_identity(named)
            or not stat.S_ISREG(opened.st_mode)
            or opened.st_mode & (stat.S_ISUID | stat.S_ISGID)
            or not opened.st_mode & execute_bit
        ):
            raise OSError("the test command executable is not a safe regular executable")
        if sys.platform == "linux":
            if not hasattr(os, "getxattr"):
                raise OSError("executable capability inspection is unavailable")
            try:
                capability = os.getxattr(descriptor, "security.capability")
            except (TypeError, ValueError) as err:
                raise OSError("executable capability inspection is unavailable") from err
            except OSError as err:
                if err.errno != errno.ENODATA:
                    raise
                capability = b""
            if capability:
                raise OSError("the test command executable carries file capabilities")
        binding = ExecutableBinding(
            str(resolved), leaf, descriptor, tuple(directories), identity
        )
        descriptor = None
        directories = []
        if not binding.stable():
            binding.close()
            raise OSError("the test command executable changed while it was bound")
        return binding
    finally:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        for _, _, directory_fd, _ in reversed(directories):
            with contextlib.suppress(OSError):
                os.close(directory_fd)


def _binding_path_is_immutable(binding: ExecutableBinding) -> bool:
    """Return true when this process cannot rewrite any pathname component."""
    try:
        for _, _, descriptor, _ in binding.directories:
            if os.access(
                ".", os.W_OK, dir_fd=descriptor, effective_ids=True
            ):
                return False
        if os.access(
            binding.leaf,
            os.W_OK,
            dir_fd=binding.parent_descriptor,
            effective_ids=True,
            follow_symlinks=False,
        ):
            return False
        return binding.stable()
    except (OSError, NotImplementedError, TypeError):
        return False


def _contained_guard_command(
    command: list[str],
    target: ExecutableBinding,
) -> GuardCommand:
    """Wrap argv in a hard no-descendant resource boundary or refuse."""
    if (
        not hasattr(os, "geteuid")
        or not hasattr(os, "getuid")
        or os.geteuid() == 0
        or os.getuid() == 0
    ):
        raise OSError("the host cannot enforce the no-descendant boundary")
    if sys.platform == "linux":
        if os.uname().machine not in ("x86_64", "amd64", "aarch64", "arm64"):
            raise OSError("the host has no proven no-descendant boundary")
        python = _trusted_executable(sys.executable)
        return GuardCommand(
            [
                f"/proc/self/fd/{python.descriptor}",
                "-I",
                "-c",
                LINUX_NO_DESCENDANT_WRAPPER,
                str(target.descriptor),
                target.path,
                *command[1:],
            ],
            (python.descriptor, target.descriptor),
            (target, python),
        )
    if sys.platform == "darwin":
        sandbox = _trusted_executable("/usr/bin/sandbox-exec")
        python: ExecutableBinding | None = None
        try:
            python = _trusted_executable("/usr/bin/python3")
            if not _binding_path_is_immutable(sandbox) or not _binding_path_is_immutable(
                python
            ):
                raise OSError("the containment wrapper path is mutable")
            expected = ",".join(str(part) for part in target.identity)
            return GuardCommand(
                [
                    sandbox.path,
                    "-p",
                    DARWIN_NO_DESCENDANT_PROFILE,
                    python.path,
                    "-I",
                    "-c",
                    DARWIN_BOUND_EXEC_WRAPPER,
                    str(target.parent_descriptor),
                    str(target.descriptor),
                    target.leaf,
                    expected,
                    target.path,
                    *command[1:],
                ],
                (target.parent_descriptor, target.descriptor),
                (target, sandbox, python),
            )
        except BaseException:
            if python is not None:
                python.close()
            sandbox.close()
            raise
    raise OSError("the host has no proven no-descendant boundary")


def _native_git_environment() -> dict[str, str]:
    """Return a closed environment for replacement-free native Git reads."""
    return {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": _trusted_search_path(),
    }


def _guard_environment(runtime: Path) -> dict[str, str]:
    """Return a closed runner environment with no caller injection channels."""
    runtime.mkdir(mode=0o700)
    home = runtime / "home"
    temporary = runtime / "tmp"
    configuration = runtime / "config"
    for directory in (home, temporary, configuration):
        directory.mkdir(mode=0o700)
    return {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": str(home),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": _trusted_search_path(),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1",
        "PYTHONUTF8": "1",
        "TMPDIR": str(temporary),
        "TZ": "UTC",
        "XDG_CONFIG_HOME": str(configuration),
    }


def _native_git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        _native_git_argv(repo, *args),
        input=input_bytes,
        capture_output=True,
        check=False,
        env=_native_git_environment(),
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ReportError(detail or f"native git {' '.join(args)} failed")
    return result.stdout


def _native_git_argv(repo: Path, *args: str) -> list[str]:
    candidate = shutil.which("git", path=os.defpath)
    if candidate is None:
        raise ReportError("native git is unavailable")
    binding = _trusted_executable(candidate)
    try:
        if not _binding_path_is_immutable(binding):
            raise ReportError("native git has a mutable executable path")
        return [
            binding.path, "--no-replace-objects", "-c", "core.useReplaceRefs=false",
            "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args,
        ]
    finally:
        binding.close()


def _parent_git_reap_reserve() -> float:
    """Keep bounded reap time inside the one parent-Git phase deadline."""
    return min(
        MAX_PARENT_GIT_REAP_SECONDS,
        max(0.0, MAX_PARENT_GIT_SECONDS / 10),
    )


def _parent_git_io_remaining(deadline: float) -> float:
    return deadline - time.monotonic() - _parent_git_reap_reserve()


def _reap_parent_git(
    process: subprocess.Popen,
    deadline: float,
    *,
    kill: bool = False,
) -> tuple[int | None, bool]:
    """Stop and reap native Git without extending its absolute deadline."""
    timed_out = False
    if not kill:
        natural_wait = max(0.0, _parent_git_io_remaining(deadline))
        try:
            return process.wait(timeout=natural_wait), False
        except subprocess.TimeoutExpired:
            kill = True
            timed_out = True
    if kill:
        with contextlib.suppress(OSError):
            process.kill()
    try:
        return (
            process.wait(timeout=max(0.0, deadline - time.monotonic())),
            timed_out,
        )
    except subprocess.TimeoutExpired:
        return None, timed_out


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def is_test(path: str) -> bool:
    name = Path(path).name
    if any(marker in name for marker in TEST_NAMES):
        return True
    return any(part in TEST_DIRS for part in Path(path).parts[:-1])


def changed_tests(repo: Path, ref: str) -> list[str]:
    out = git(
        repo,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "--diff-filter=AM",
        "-r",
        ref,
    )
    return sorted(path for path in out.splitlines() if path and is_test(path))


def parent_of(repo: Path, ref: str) -> str | None:
    try:
        return git(repo, "rev-parse", f"{ref}^").strip()
    except RuntimeError:
        return None


def _integer(value, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ReportError(f"{name} must be a non-negative integer")
    return value


def _normalised(complete, executed, failures, errors, skipped) -> RunnerReport:
    if complete is not True:
        raise ReportError("the report is incomplete")
    report = RunnerReport(
        complete=True,
        executed=_integer(executed, "executed"),
        assertion_failures=_integer(failures, "assertion_failures"),
        errors=_integer(errors, "errors"),
        skipped=_integer(skipped, "skipped"),
    )
    if report.assertion_failures + report.errors > report.executed:
        raise ReportError("outcome counts exceed executed tests")
    return report


def _json_object(raw: bytes) -> dict:
    def unique_object(pairs: list[tuple[str, object]]) -> dict:
        value = {}
        for key, item in pairs:
            if key in value:
                raise ReportError("the report contains a duplicate object key")
            value[key] = item
        return value

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique_object,
        )
    except ReportError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ReportError("the report is not valid UTF-8 JSON") from err
    if type(value) is not dict:
        raise ReportError("the report root must be an object")
    return value


def parse_unittest_report(raw: bytes) -> RunnerReport:
    value = _json_object(raw)
    required = {
        "schema", "complete", "testsRun", "failures", "errors", "skipped",
        "expectedFailures", "unexpectedSuccesses",
    }
    if set(value) != required or value.get("schema") != "elenchus.unittest.v1":
        raise ReportError("the unittest report schema is not supported")
    tests_run = _integer(value["testsRun"], "testsRun")
    failures = _integer(value["failures"], "failures")
    errors = _integer(value["errors"], "errors")
    skipped = _integer(value["skipped"], "skipped")
    expected = _integer(value["expectedFailures"], "expectedFailures")
    unexpected = _integer(value["unexpectedSuccesses"], "unexpectedSuccesses")
    if failures + errors + skipped + expected + unexpected > tests_run:
        raise ReportError("unittest categories exceed testsRun")
    executed = tests_run - skipped - expected
    return _normalised(
        value["complete"], executed, failures, errors + unexpected, skipped + expected
    )


def parse_node_report(raw: bytes) -> RunnerReport:
    value = _json_object(raw)
    required = {
        "schema", "complete", "executed", "assertionFailures", "errors", "skipped",
    }
    if set(value) != required or value.get("schema") != "elenchus.node-test.v1":
        raise ReportError("the Node report schema is not supported")
    return _normalised(
        value["complete"], value["executed"], value["assertionFailures"],
        value["errors"], value["skipped"],
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_forge_report(raw: bytes) -> RunnerReport:
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ReportError("XML declarations with entities are not accepted")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as err:
        raise ReportError("the report is not valid XML") from err
    if _local_name(root.tag) != "testsuites":
        raise ReportError("the Forge JUnit root must be testsuites")
    cases = [node for node in root.iter() if _local_name(node.tag) == "testcase"]
    failures = errors = skipped = 0
    for case in cases:
        children = {_local_name(child.tag) for child in case}
        failures += "failure" in children
        errors += "error" in children
        skipped += "skipped" in children
        if len(children & {"failure", "error", "skipped"}) > 1:
            raise ReportError("a Forge testcase has contradictory outcomes")
    for attribute, observed in (
        ("tests", len(cases)), ("failures", failures), ("errors", errors)
    ):
        declared = root.attrib.get(attribute)
        if declared is None or not declared.isascii() or not declared.isdecimal():
            raise ReportError(f"the Forge report lacks a valid {attribute} total")
        if int(declared) != observed:
            raise ReportError(f"the Forge {attribute} total contradicts its cases")
    return _normalised(True, len(cases) - skipped, failures, errors, skipped)


def _verify_report_location(tree: Path, candidate: Path) -> None:
    root = tree.resolve()
    current = candidate
    while current != tree:
        if current.is_symlink():
            raise ReportError("the report path cannot contain a symlink")
        current = current.parent
    try:
        candidate.resolve(strict=False).relative_to(root)
    except (OSError, ValueError) as err:
        raise ReportError("the report path escapes the worktree") from err


def read_report(
    path: Path, report_format: str, started_ns: int, tree: Path | None = None
) -> RunnerReport:
    if tree is not None:
        raw = _stable_report_bytes(path, started_ns, tree)
    else:
        try:
            observed = path.stat()
        except OSError as err:
            raise ReportError("the runner did not create its report") from err
        if not path.is_file() or path.is_symlink():
            raise ReportError("the runner report is not a regular file")
        if observed.st_mtime_ns < started_ns:
            raise ReportError("the runner report is stale")
        try:
            with path.open("rb") as source:
                raw = source.read(MAX_REPORT_BYTES + 1)
        except OSError as err:
            raise ReportError("the runner report could not be read") from err
        if len(raw) > MAX_REPORT_BYTES:
            raise ReportError("the runner report exceeds the size limit")
    parsers = {
        "unittest-json-v1": parse_unittest_report,
        "forge-junit-v1": parse_forge_report,
        "node-test-json-v1": parse_node_report,
    }
    parser = parsers.get(report_format)
    if parser is None:
        raise ReportError("the declared report format is not supported")
    return parser(raw)


def classify(report: RunnerReport) -> tuple[str, str]:
    if report.executed == 0:
        return "inconclusive", "the runner report records no executed tests"
    if report.errors > 0:
        return "inconclusive", "the runner report records an infrastructure error"
    if report.assertion_failures > 0:
        return "guarded", "the runner report records a parent assertion failure"
    return "passed", "the runner report records that the guard passed on the parent"


def _tracked(tree: Path, relative: Path) -> bool:
    result = subprocess.run(
        _native_git_argv(
            tree,
            "ls-files",
            "--error-unmatch",
            "--",
            f":(literal){relative.as_posix()}",
        ),
        capture_output=True,
        text=True,
        check=False,
        env=_native_git_environment(),
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise ReportError("the report path's tracked state could not be read")


def prepare_report_path(tree: Path, raw_path: str) -> Path:
    relative = Path(raw_path)
    if not raw_path or relative.is_absolute() or ".." in relative.parts:
        raise ReportError("the report path must be a relative worktree descendant")
    candidate = tree / relative
    _verify_report_location(tree, candidate)
    if _tracked(tree, relative):
        raise ReportError("the report path names a tracked file")
    if candidate.exists():
        if not candidate.is_file() or candidate.is_symlink():
            raise ReportError("the stale report path is not a regular file")
        candidate.unlink()
    candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate


def _guard_path(raw_path: object) -> str:
    if type(raw_path) is not str or not raw_path:
        raise ReportError("a guard blob path must be a nonempty string")
    try:
        encoded = raw_path.encode("utf-8")
    except UnicodeEncodeError as err:
        raise ReportError("a guard blob path must be UTF-8") from err
    if len(encoded) > MAX_GUARD_PATH_BYTES:
        raise ReportError("a guard blob path exceeds the size limit")
    path = PurePosixPath(raw_path)
    if (
        path.is_absolute()
        or path.parts in ((), (".",))
        or any(part in ("", ".", "..") for part in path.parts)
        or str(path) != raw_path
        or any(
            unicodedata.normalize("NFC", part).casefold() == ".git"
            for part in path.parts
        )
        or any(
            ord(character) < 32
            or ord(character) == 127
            or (character != " " and character.isspace())
            for character in raw_path
        )
    ):
        raise ReportError("a guard blob path is not a canonical repository path")
    return raw_path


def _physical_path_key(path: str) -> tuple[str, ...]:
    """Return the conservative cross-filesystem alias key for a Git path."""
    return tuple(
        unicodedata.normalize("NFC", part).casefold()
        for part in PurePosixPath(path).parts
    )


def _guard_report_path(raw_path: object) -> str:
    if type(raw_path) is not str or not raw_path:
        raise ReportError("the report path must be a nonempty string")
    try:
        encoded = raw_path.encode("utf-8")
    except UnicodeEncodeError as err:
        raise ReportError("the report path must be UTF-8") from err
    path = PurePosixPath(raw_path)
    if (
        len(encoded) > MAX_GUARD_PATH_BYTES
        or path.is_absolute()
        or path.parts in ((), (".",))
        or any(part in ("", ".", "..") for part in path.parts)
        or str(path) != raw_path
        or any(
            unicodedata.normalize("NFC", part).casefold() == ".git"
            for part in path.parts
        )
        or any(
            ord(character) < 32
            or ord(character) == 127
            or (character != " " and character.isspace())
            for character in raw_path
        )
    ):
        raise ReportError("the report path is not a canonical repository path")
    return raw_path


def _paths_overlap(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    common = min(len(left), len(right))
    return left[:common] == right[:common]


def _validate_report_guard_disjoint(report_file: str, blobs: list[dict]) -> str:
    report = _guard_report_path(report_file)
    report_key = _physical_path_key(report)
    for row in blobs:
        if _paths_overlap(report_key, _physical_path_key(row["path"])):
            raise ReportError("the report path overlaps a guard blob path")
    return report


def _parent_path(raw_path: bytes) -> str:
    try:
        path = raw_path.decode("utf-8", "strict")
    except UnicodeDecodeError as err:
        raise ReportError("the parent tree contains a non-UTF-8 path") from err
    if len(raw_path) > MAX_PARENT_PATH_BYTES:
        raise ReportError("a parent tree path exceeds the size limit")
    parsed = PurePosixPath(path)
    if (
        not path
        or parsed.is_absolute()
        or any(part in ("", ".", "..") for part in parsed.parts)
        or str(parsed) != path
        or parsed.parts[0] == ".git"
    ):
        raise ReportError("the parent tree contains an unsafe path")
    return path


def _parent_tree_entries(repo: Path, parent: str) -> list[tuple[str, str, str, str]]:
    deadline = time.monotonic() + MAX_PARENT_GIT_SECONDS
    process = subprocess.Popen(
        _native_git_argv(repo, "ls-tree", "-r", "-z", "--full-tree", parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_native_git_environment(),
    )
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    entries: list[tuple[str, str, str, str]] = []
    seen: set[bytes] = set()
    pending = bytearray()
    stderr = bytearray()
    observed_bytes = 0

    def accept(record: bytes) -> None:
        if not record:
            raise ReportError("the parent tree contains an empty entry")
        if len(entries) >= MAX_PARENT_ENTRIES:
            raise ReportError("the parent tree has too many entries")
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, kind, raw_oid = metadata.split(b" ")
            mode_text = mode.decode("ascii")
            kind_text = kind.decode("ascii")
            oid = raw_oid.decode("ascii")
        except (UnicodeDecodeError, ValueError) as err:
            raise ReportError("the parent tree contains a malformed entry") from err
        path = _parent_path(raw_path)
        if raw_path in seen:
            raise ReportError("the parent tree paths are duplicated")
        seen.add(raw_path)
        if OBJECT_ID_RE.fullmatch(oid) is None:
            raise ReportError("the parent tree contains an invalid object id")
        if (mode_text, kind_text) not in {
            ("100644", "blob"),
            ("100755", "blob"),
            ("120000", "blob"),
            ("160000", "commit"),
        }:
            raise ReportError("the parent tree contains an unsupported entry")
        entries.append((path, mode_text, kind_text, oid))

    failure: BaseException | None = None
    returncode: int | None = None
    try:
        while selector.get_map():
            remaining = _parent_git_io_remaining(deadline)
            if remaining <= 0:
                raise ReportError("the parent tree listing timed out")
            events = selector.select(min(remaining, 0.1))
            if not events and process.poll() is not None:
                events = [
                    (key, selectors.EVENT_READ)
                    for key in selector.get_map().values()
                ]
            for key, _ in events:
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                if key.data == "stderr":
                    available = max(0, MAX_DIAGNOSTIC_BYTES - len(stderr))
                    stderr.extend(chunk[:available])
                    continue
                observed_bytes += len(chunk)
                if observed_bytes > MAX_PARENT_TREE_BYTES:
                    raise ReportError("the parent tree listing exceeds the size limit")
                pending.extend(chunk)
                while True:
                    separator = pending.find(0)
                    if separator < 0:
                        break
                    record = bytes(pending[:separator])
                    del pending[: separator + 1]
                    accept(record)
        returncode, timed_out = _reap_parent_git(process, deadline)
        if timed_out or returncode is None:
            raise ReportError("the parent tree listing timed out")
    except BaseException as err:
        failure = err
        _reap_parent_git(process, deadline, kill=True)
    finally:
        selector.close()
        with contextlib.suppress(OSError):
            process.stdout.close()
        with contextlib.suppress(OSError):
            process.stderr.close()
    if failure is not None:
        raise failure
    if returncode != 0:
        detail = stderr.decode("utf-8", errors="replace").strip()
        raise ReportError(detail or "native Git parent tree listing failed")
    if pending:
        raise ReportError("the parent tree listing is incomplete")
    return entries


def _tree_entry(repo: Path, parent: str, path: str) -> tuple[str, str, str] | None:
    raw = _native_git(repo, "ls-tree", "-z", parent, "--", f":(literal){path}")
    if not raw:
        return None
    rows = raw.split(b"\0")
    if rows[-1] != b"" or len(rows) != 2:
        raise ReportError("a guard blob parent entry is ambiguous")
    try:
        metadata, actual_path = rows[0].split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split(" ")
        decoded_path = actual_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as err:
        raise ReportError("a guard blob parent entry is malformed") from err
    if decoded_path != path:
        raise ReportError("a guard blob parent entry does not match its path")
    return mode, kind, oid


def _validate_guard_blobs(
    repo: Path, parent: str, blobs: list[dict]
) -> list[dict]:
    if type(blobs) is not list or len(blobs) > MAX_GUARD_BLOBS:
        raise ReportError("guard blobs must be a bounded list")
    validated: list[dict] = []
    total = 0
    previous: bytes | None = None
    physical_paths: set[tuple[str, ...]] = set()
    for row in blobs:
        if type(row) is not dict or set(row) != GUARD_BLOB_KEYS:
            raise ReportError("a guard blob row has unknown or missing fields")
        path = _guard_path(row["path"])
        path_bytes = path.encode("utf-8")
        if previous is not None and path_bytes <= previous:
            raise ReportError("guard blob rows must have unique UTF-8-byte order")
        previous = path_bytes
        physical_path = _physical_path_key(path)
        if physical_path in physical_paths:
            raise ReportError("guard blob paths have a physical alias collision")
        physical_paths.add(physical_path)
        if row["status"] not in ("A", "M"):
            raise ReportError("a guard blob status must be A or M")
        if row["mode"] not in ("100644", "100755"):
            raise ReportError("a guard blob mode must be 100644 or 100755")
        raw = row["raw"]
        if type(raw) is not bytes:
            raise ReportError("a guard blob raw value must be bytes")
        if type(row["bytes"]) is not int or row["bytes"] != len(raw):
            raise ReportError("a guard blob byte count does not match its raw bytes")
        if len(raw) > MAX_GUARD_BLOB_BYTES:
            raise ReportError("a guard blob exceeds the size limit")
        total += len(raw)
        if total > MAX_GUARD_BLOBS_BYTES:
            raise ReportError("the guard blob set exceeds the size limit")
        digest = hashlib.sha256(raw).hexdigest()
        if type(row["sha256"]) is not str or row["sha256"] != digest:
            raise ReportError("a guard blob SHA-256 does not match its raw bytes")
        oid = row["oid"]
        if type(oid) is not str or OBJECT_ID_RE.fullmatch(oid) is None:
            raise ReportError("a guard blob object id is not canonical")
        if _native_git(repo, "hash-object", "--stdin", input_bytes=raw).strip() != oid.encode():
            raise ReportError("a guard blob object id does not match its raw bytes")
        if _native_git(repo, "cat-file", "blob", oid) != raw:
            raise ReportError("a guard blob differs from its native Git object")
        parent_entry = _tree_entry(repo, parent, path)
        if row["status"] == "A" and parent_entry is not None:
            raise ReportError("an added guard blob already exists in the parent")
        if row["status"] == "M":
            if parent_entry is None:
                raise ReportError("a modified guard blob is absent from the parent")
            parent_mode, parent_kind, _ = parent_entry
            if parent_kind != "blob" or parent_mode not in ("100644", "100755"):
                raise ReportError("a modified guard blob parent is not a regular blob")
        validated.append(row)
    return validated


def _require_exact_entry(parent_fd: int, name: str) -> None:
    if name not in os.listdir(parent_fd):
        raise ReportError("a path component has a physical alias collision")


def _open_directory(parent_fd: int, name: str, create: bool) -> int:
    if not hasattr(os, "O_NOFOLLOW"):
        raise ReportError("safe no-follow directory access is unavailable")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        if not create:
            raise
        os.mkdir(name, 0o755, dir_fd=parent_fd)
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    try:
        _require_exact_entry(parent_fd, name)
        named = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(named.st_mode)
            or _file_identity(named) != _file_identity(opened)
        ):
            raise ReportError("a path directory was replaced")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _parent_leaf_directory(tree: Path, path: str) -> tuple[int, str]:
    parts = PurePosixPath(path).parts
    directory_fd = os.open(
        tree, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    )
    try:
        for part in parts[:-1]:
            child_fd = _open_directory(directory_fd, part, create=True)
            os.close(directory_fd)
            directory_fd = child_fd
        return directory_fd, parts[-1]
    except BaseException:
        os.close(directory_fd)
        raise


def _git_blob_digest(raw: bytes, oid_length: int) -> str:
    digest = hashlib.sha1() if oid_length == 40 else hashlib.sha256()
    digest.update(f"blob {len(raw)}\0".encode("ascii"))
    digest.update(raw)
    return digest.hexdigest()


def _materialize_regular(tree: Path, path: str, mode: str, oid: str, raw: bytes) -> None:
    directory_fd, leaf = _parent_leaf_directory(tree, path)
    descriptor = None
    try:
        descriptor = os.open(
            leaf,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        view = memoryview(raw)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short parent blob write")
            view = view[written:]
        os.fchmod(descriptor, int(mode, 8))
        before = os.fstat(descriptor)
        _require_exact_entry(directory_fd, leaf)
        named = os.stat(leaf, dir_fd=directory_fd, follow_symlinks=False)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size != len(raw)
            or stat.S_IMODE(before.st_mode) != int(mode[-3:], 8)
            or _file_identity(before) != _file_identity(named)
        ):
            raise OSError("parent blob identity or mode mismatch")
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest = hashlib.sha1() if len(oid) == 40 else hashlib.sha256()
        digest.update(f"blob {len(raw)}\0".encode("ascii"))
        remaining = len(raw)
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                raise OSError("short parent blob read")
            digest.update(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1) or digest.hexdigest() != oid:
            raise OSError("materialized parent blob differs from its Git object")
        after = os.fstat(descriptor)
        named_after = os.stat(leaf, dir_fd=directory_fd, follow_symlinks=False)
        if (
            _file_identity(before) != _file_identity(after)
            or _file_identity(after) != _file_identity(named_after)
        ):
            raise OSError("materialized parent blob changed during verification")
    except OSError as err:
        raise ReportError("a parent blob could not be materialized exactly") from err
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory_fd)


def _materialize_symlink(tree: Path, path: str, oid: str, raw: bytes) -> None:
    if b"\0" in raw:
        raise ReportError("a parent symlink target contains a null byte")
    directory_fd, leaf = _parent_leaf_directory(tree, path)
    leaf_bytes = os.fsencode(leaf)
    try:
        os.symlink(raw, leaf_bytes, dir_fd=directory_fd)
        _require_exact_entry(directory_fd, leaf)
        named = os.stat(leaf_bytes, dir_fd=directory_fd, follow_symlinks=False)
        if (
            not stat.S_ISLNK(named.st_mode)
            or os.readlink(leaf_bytes, dir_fd=directory_fd) != raw
            or _git_blob_digest(raw, len(oid)) != oid
        ):
            raise OSError("materialized parent symlink mismatch")
    except OSError as err:
        raise ReportError("a parent symlink could not be materialized exactly") from err
    finally:
        os.close(directory_fd)


def _materialize_gitlink(tree: Path, path: str) -> None:
    directory_fd, leaf = _parent_leaf_directory(tree, path)
    try:
        os.mkdir(leaf, 0o755, dir_fd=directory_fd)
        _require_exact_entry(directory_fd, leaf)
        named = os.stat(leaf, dir_fd=directory_fd, follow_symlinks=False)
        if not stat.S_ISDIR(named.st_mode):
            raise OSError("materialized gitlink is not a directory")
    except OSError as err:
        raise ReportError("a parent gitlink could not be materialized exactly") from err
    finally:
        os.close(directory_fd)


class _BatchBlobReader:
    """Deadline-bound stdout framing for one native ``cat-file --batch``."""

    def __init__(self, process: subprocess.Popen, deadline: float):
        assert process.stdout is not None and process.stderr is not None
        self.process = process
        self.deadline = deadline
        self.buffer = bytearray()
        self.stderr = bytearray()
        self.selector = selectors.DefaultSelector()
        self.selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        self.selector.register(process.stderr, selectors.EVENT_READ, "stderr")

    def _fill(self) -> None:
        remaining = _parent_git_io_remaining(self.deadline)
        if remaining <= 0:
            raise ReportError("native Git parent blob materialization timed out")
        events = self.selector.select(min(remaining, 0.1))
        if not events and self.process.poll() is not None:
            events = [
                (key, selectors.EVENT_READ)
                for key in self.selector.get_map().values()
            ]
        if not events:
            return
        for key, _ in events:
            chunk = os.read(key.fd, 65536)
            if not chunk:
                self.selector.unregister(key.fileobj)
                continue
            if key.data == "stderr":
                available = max(0, MAX_DIAGNOSTIC_BYTES - len(self.stderr))
                self.stderr.extend(chunk[:available])
            else:
                self.buffer.extend(chunk)

    def line(self, maximum: int) -> bytes:
        while True:
            separator = self.buffer.find(b"\n")
            if separator >= 0:
                if separator + 1 > maximum:
                    raise ReportError("native Git returned an oversized parent blob header")
                line = bytes(self.buffer[: separator + 1])
                del self.buffer[: separator + 1]
                return line
            if len(self.buffer) >= maximum:
                raise ReportError("native Git returned an oversized parent blob header")
            if not self.selector.get_map():
                raise ReportError("native Git returned an incomplete parent blob header")
            self._fill()

    def exact(self, size: int) -> bytes:
        while len(self.buffer) < size:
            if not self.selector.get_map():
                raise ReportError("native Git returned an incomplete parent blob")
            self._fill()
        raw = bytes(self.buffer[:size])
        del self.buffer[:size]
        return raw

    def close(self) -> None:
        self.selector.close()


def _batch_blob(reader: _BatchBlobReader, oid: str, remaining: int) -> bytes:
    process = reader.process
    assert process.stdin is not None
    process.stdin.write(oid.encode("ascii") + b"\n")
    process.stdin.flush()
    header = reader.line(129)
    match = re.fullmatch(
        rb"([0-9a-f]{40}(?:[0-9a-f]{24})?) blob (0|[1-9][0-9]*)\n",
        header,
    )
    if match is None or match.group(1).decode("ascii") != oid:
        raise ReportError("native Git returned an invalid parent blob header")
    size = int(match.group(2))
    if size > MAX_PARENT_BLOB_BYTES:
        raise ReportError("a parent blob exceeds the per-blob size limit")
    if size > remaining:
        raise ReportError("parent blobs exceed the aggregate size limit")
    raw = reader.exact(size)
    trailer = reader.exact(1)
    if len(raw) != size or trailer != b"\n" or _git_blob_digest(raw, len(oid)) != oid:
        raise ReportError("native Git returned an incomplete or mismatched parent blob")
    return raw


def _materialize_parent_tree(repo: Path, tree: Path, parent: str) -> None:
    """Populate a no-checkout worktree from exact native Git object bytes."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise ReportError("safe no-follow parent materialization is unavailable")
    entries = _parent_tree_entries(repo, parent)
    _native_git(tree, "read-tree", parent)
    deadline = time.monotonic() + MAX_PARENT_GIT_SECONDS
    process = subprocess.Popen(
        _native_git_argv(repo, "cat-file", "--batch"),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_native_git_environment(),
    )
    reader = _BatchBlobReader(process, deadline)
    failure: BaseException | None = None
    returncode: int | None = None
    total = 0
    try:
        for path, mode, kind, oid in entries:
            if kind == "commit":
                _materialize_gitlink(tree, path)
                continue
            raw = _batch_blob(reader, oid, MAX_PARENT_BLOBS_BYTES - total)
            total += len(raw)
            if mode == "120000":
                _materialize_symlink(tree, path, oid, raw)
            else:
                _materialize_regular(tree, path, mode, oid, raw)
    except BaseException as err:
        failure = err
    finally:
        timed_out = False
        if failure is not None:
            returncode, _ = _reap_parent_git(process, deadline, kill=True)
        if process.stdin is not None:
            with contextlib.suppress(OSError):
                process.stdin.close()
        if failure is None:
            returncode, timed_out = _reap_parent_git(process, deadline)
        stderr = bytes(reader.stderr)
        reader.close()
        if process.stdout is not None:
            with contextlib.suppress(OSError):
                process.stdout.close()
        if process.stderr is not None:
            with contextlib.suppress(OSError):
                process.stderr.close()
    if failure is not None:
        raise failure
    if timed_out or returncode is None:
        raise ReportError("native Git parent blob materialization timed out")
    if returncode != 0:
        detail = stderr.decode("utf-8", errors="replace").strip()
        raise ReportError(detail or "native Git parent blob reader failed")


def _overlay_guard_blob(tree: Path, row: dict) -> None:
    if not hasattr(os, "O_NOFOLLOW"):
        raise ReportError("safe no-follow blob overlay is unavailable")
    parts = PurePosixPath(row["path"]).parts
    directory_fd = os.open(tree, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts[:-1]:
            child_fd = _open_directory(
                directory_fd, part, create=row["status"] == "A"
            )
            os.close(directory_fd)
            directory_fd = child_fd
        if row["status"] == "A":
            flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        else:
            if parts[-1] not in os.listdir(directory_fd):
                raise ReportError("a modified guard blob path is not physically exact")
            flags = os.O_RDWR | os.O_TRUNC | os.O_NOFOLLOW
        descriptor = os.open(parts[-1], flags, 0o600, dir_fd=directory_fd)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise ReportError("a guard blob target is not a single-link regular file")
            _require_exact_entry(directory_fd, parts[-1])
            view = memoryview(row["raw"])
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise ReportError("a guard blob could not be overlaid completely")
                view = view[written:]
            os.fchmod(descriptor, int(row["mode"], 8))
            os.lseek(descriptor, 0, os.SEEK_SET)
            digest = hashlib.sha256()
            remaining = len(row["raw"])
            while remaining:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    raise ReportError("a guard blob could not be read back completely")
                digest.update(chunk)
                remaining -= len(chunk)
            after = os.fstat(descriptor)
            named = os.stat(parts[-1], dir_fd=directory_fd, follow_symlinks=False)
            if (
                os.read(descriptor, 1)
                or digest.hexdigest() != row["sha256"]
                or not stat.S_ISREG(after.st_mode)
                or after.st_nlink != 1
                or after.st_size != row["bytes"]
                or stat.S_IMODE(after.st_mode) != int(row["mode"][-3:], 8)
                or (opened.st_dev, opened.st_ino) != (after.st_dev, after.st_ino)
                or (after.st_dev, after.st_ino) != (named.st_dev, named.st_ino)
            ):
                raise ReportError("a guard blob overlay did not remain exact")
        finally:
            os.close(descriptor)
    except OSError as err:
        raise ReportError("a guard blob could not be overlaid safely") from err
    finally:
        os.close(directory_fd)


def _file_identity(observed: os.stat_result) -> tuple[int, ...]:
    return (
        observed.st_dev, observed.st_ino, observed.st_mode, observed.st_nlink,
        observed.st_size, observed.st_mtime_ns, observed.st_ctime_ns,
    )


def _stable_report_bytes(path: Path, started_ns: int, tree: Path) -> bytes:
    _verify_report_location(tree, path)
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_NONBLOCK"):
        raise ReportError("safe no-follow report access is unavailable")
    try:
        relative = path.relative_to(tree)
    except ValueError as err:
        raise ReportError("the report path escapes the worktree") from err
    if not relative.parts:
        raise ReportError("the report path must name a file")

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directories: list[tuple[int | None, str | None, int, tuple[int, ...]]] = []
    descriptor: int | None = None
    try:
        root_named = tree.lstat()
        root_fd = os.open(tree, directory_flags)
        root_identity = _file_identity(os.fstat(root_fd))
        if root_identity != _file_identity(root_named) or not stat.S_ISDIR(root_named.st_mode):
            os.close(root_fd)
            raise ReportError("the report worktree root was replaced")
        directories.append((None, None, root_fd, root_identity))

        parent_fd = root_fd
        for component in relative.parts[:-1]:
            named = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            child_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            identity = _file_identity(os.fstat(child_fd))
            if identity != _file_identity(named) or not stat.S_ISDIR(named.st_mode):
                os.close(child_fd)
                raise ReportError("a runner report directory was replaced")
            directories.append((parent_fd, component, child_fd, identity))
            parent_fd = child_fd

        leaf = relative.parts[-1]
        named_before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(named_before.st_mode):
            raise ReportError("the runner report is not a regular file")
        descriptor = os.open(
            leaf,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent_fd,
        )
    except (OSError, ReportError) as err:
        for _, _, directory_fd, _ in reversed(directories):
            os.close(directory_fd)
        if isinstance(err, ReportError):
            raise
        raise ReportError("the runner did not create a safe report") from err
    try:
        opened_before = os.fstat(descriptor)
        identity = _file_identity(opened_before)
        named_identity = _file_identity(named_before)
        if identity != named_identity or not stat.S_ISREG(opened_before.st_mode):
            raise ReportError("the runner report was replaced")
        if opened_before.st_nlink != 1:
            raise ReportError("the runner report is not a single-link regular file")
        if opened_before.st_mtime_ns < started_ns:
            raise ReportError("the runner report is stale")
        if opened_before.st_size > MAX_REPORT_BYTES:
            raise ReportError("the runner report exceeds the size limit")
        chunks: list[bytes] = []
        remaining = MAX_REPORT_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > MAX_REPORT_BYTES:
            raise ReportError("the runner report exceeds the size limit")
        opened_after = os.fstat(descriptor)
        named_after = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        after_identity = _file_identity(opened_after)
        final_named_identity = _file_identity(named_after)
        if identity != after_identity or identity != final_named_identity:
            raise ReportError("the runner report was unstable or replaced")
        if len(raw) != opened_after.st_size:
            raise ReportError("the runner report size changed while reading")

        for containing_fd, name, opened_fd, expected in reversed(directories[1:]):
            opened_identity = _file_identity(os.fstat(opened_fd))
            named_identity = _file_identity(
                os.stat(name, dir_fd=containing_fd, follow_symlinks=False)
            )
            if expected != opened_identity or expected != named_identity:
                raise ReportError("a runner report directory was unstable or replaced")
        root_after = tree.lstat()
        if (
            directories[0][3] != _file_identity(os.fstat(directories[0][2]))
            or directories[0][3] != _file_identity(root_after)
        ):
            raise ReportError("the report worktree root was unstable or replaced")
        return raw
    except OSError as err:
        raise ReportError("the runner report could not be read stably") from err
    finally:
        if descriptor is not None:
            os.close(descriptor)
        for _, _, directory_fd, _ in reversed(directories):
            os.close(directory_fd)


def _parse_report(raw: bytes, report_format: str) -> RunnerReport:
    parsers = {
        "unittest-json-v1": parse_unittest_report,
        "forge-junit-v1": parse_forge_report,
        "node-test-json-v1": parse_node_report,
    }
    parser = parsers.get(report_format)
    if parser is None:
        raise ReportError("the declared report format is not supported")
    return parser(raw)


def _base_result(ref: str, status: str, tests: list[str], detail: str) -> dict:
    return {"ref": ref, "status": status, "tests": tests, "detail": detail}


def _tail(current: bytes, chunk: bytes) -> bytes:
    return (current + chunk)[-MAX_DIAGNOSTIC_BYTES:]


def _drain_guard_pipes(
    selector: selectors.BaseSelector,
    tails: dict[str, bytes],
    timeout: float,
) -> None:
    for key, _ in selector.select(timeout):
        stream = key.fileobj
        try:
            chunk = os.read(stream.fileno(), 65_536)
        except BlockingIOError:
            continue
        if chunk:
            tails[key.data] = _tail(tails[key.data], chunk)
            continue
        selector.unregister(stream)
        stream.close()


def _signal_guard_group(process: subprocess.Popen, requested: signal.Signals) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(process.pid, requested)


def _guard_leader_exited(process: subprocess.Popen) -> bool:
    """Observe the leader without reaping it, so its group id cannot be reused."""
    try:
        observed = os.waitid(
            os.P_PID,
            process.pid,
            os.WEXITED | os.WNOHANG | os.WNOWAIT,
        )
    except ChildProcessError:
        return True
    return observed is not None


def _run_guard_command(
    command: GuardCommand, tree: Path, timeout: int, environment: dict[str, str]
) -> GuardRun:
    """Run one process group while retaining only bounded stdout/stderr tails."""
    if any(
        not hasattr(os, name)
        for name in ("killpg", "waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT")
    ):
        raise OSError("process-group control is unavailable")
    selector = selectors.DefaultSelector()
    try:
        process = subprocess.Popen(
            command.argv,
            cwd=tree,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            pass_fds=command.pass_fds,
            start_new_session=True,
        )
    except BaseException:
        selector.close()
        raise
    try:
        assert process.stdout is not None and process.stderr is not None
        tails = {"stdout": b"", "stderr": b""}
        for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        deadline = time.monotonic() + timeout
        timed_out = False
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = not _guard_leader_exited(process)
                break
            _drain_guard_pipes(selector, tails, min(0.05, remaining))
            if _guard_leader_exited(process):
                break

        # A report is not stable evidence while any command descendant remains.
        _signal_guard_group(process, signal.SIGTERM)
        grace_deadline = time.monotonic() + 0.1
        while time.monotonic() < grace_deadline:
            _drain_guard_pipes(selector, tails, 0.05)
        _signal_guard_group(process, signal.SIGKILL)
        try:
            returncode = process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            returncode = process.wait(timeout=1)

        drain_deadline = time.monotonic() + 1
        while selector.get_map() and time.monotonic() < drain_deadline:
            _drain_guard_pipes(selector, tails, 0.05)
        return GuardRun(
            returncode=returncode,
            stdout=tails["stdout"],
            stderr=tails["stderr"],
            timed_out=timed_out,
            streams_complete=not selector.get_map(),
        )
    finally:
        _signal_guard_group(process, signal.SIGKILL)
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(OSError):
                process.kill()
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                process.wait(timeout=1)
        for key in list(selector.get_map().values()):
            with contextlib.suppress(OSError, KeyError):
                selector.unregister(key.fileobj)
            with contextlib.suppress(OSError):
                key.fileobj.close()
        for stream in (process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                with contextlib.suppress(OSError):
                    stream.close()
        selector.close()


def parent_guard_evidence(
    repo: Path,
    parent: str,
    blobs: list[dict],
    command: list[str],
    report_format: str,
    report_file: str,
    timeout: int = 900,
) -> dict:
    """Run caller-bound raw guard blobs on one exact native Git parent.

    The return value is deliberately in-memory.  Its ``raw_report`` member is
    the exact report byte string read before the detached worktree is removed;
    persistence and admission into controller evidence belong to Fiat.
    """
    repo = Path(repo).resolve()
    if type(parent) is not str or OBJECT_ID_RE.fullmatch(parent) is None:
        raise ReportError("the parent must be one canonical full object id")
    resolved = _native_git(repo, "rev-parse", "--verify", f"{parent}^{{commit}}").strip()
    if resolved != parent.encode("ascii"):
        raise ReportError("the parent did not resolve to its exact commit")
    validated = _validate_guard_blobs(repo, parent, blobs)
    tests = [row["path"] for row in validated if is_test(row["path"])]
    if not tests:
        return _base_result(parent, "unguarded", [], "the guard blobs contain no test files")
    if report_format not in REPORT_FORMATS:
        raise ReportError("the declared report format is not supported")
    report_file = _validate_report_guard_disjoint(report_file, validated)
    if type(command) is not list or not command or len(command) > MAX_COMMAND_ARGUMENTS:
        raise ReportError("the test command must be a bounded nonempty argv list")
    if any(
        type(argument) is not str
        or not argument
        for argument in command
    ):
        raise ReportError("a test command argument is invalid")
    encoded_command = b"\0".join(argument.encode("utf-8") for argument in command)
    if len(encoded_command) > MAX_COMMAND_BYTES:
        raise ReportError("the complete test command exceeds the size limit")
    if command.count(REPORT_PLACEHOLDER) != 1:
        raise ReportError("the test command must contain one exact {report} argument")
    if type(timeout) is not int or timeout <= 0:
        raise ReportError("the timeout must be a positive integer")

    workdir = Path(tempfile.mkdtemp(prefix="elenchus-parent-guard-"))
    tree = workdir / "tree"
    try:
        _native_git(
            repo, "worktree", "add", "--quiet", "--no-checkout", "--detach",
            str(tree), parent,
        )
        _materialize_parent_tree(repo, tree, parent)
        for row in validated:
            _overlay_guard_blob(tree, row)
        report_path = prepare_report_path(tree, report_file)
        resolved_command = [
            str(report_path) if argument == REPORT_PLACEHOLDER else argument
            for argument in command
        ]
        try:
            executable = _trusted_executable(resolved_command[0])
        except OSError:
            return _base_result(
                parent, "inconclusive", tests,
                "the test command could not be started",
            )
        resolved_command[0] = executable.path
        try:
            contained_command = _contained_guard_command(
                resolved_command, executable
            )
        except OSError:
            executable.close()
            return _base_result(
                parent, "inconclusive", tests,
                "complete descendant containment is unavailable",
            )
        environment = _guard_environment(workdir / "runtime")
        started_ns = time.time_ns()
        try:
            if not contained_command.stable():
                return _base_result(
                    parent, "inconclusive", tests,
                    "the test command executable changed during the run",
                )
            try:
                run = _run_guard_command(
                    contained_command, tree, timeout, environment
                )
            except OSError:
                return _base_result(
                    parent, "inconclusive", tests,
                    "the test command could not be started",
                )
            bindings_stable = contained_command.stable()
        finally:
            contained_command.close()

        output = (run.stdout + run.stderr).decode(
            "utf-8", errors="replace"
        )[-MAX_DIAGNOSTIC_CHARS:]
        if run.timed_out:
            return _base_result(
                parent, "inconclusive", tests,
                f"the run did not finish inside {timeout}s",
            )
        if not run.streams_complete:
            result = _base_result(
                parent, "inconclusive", tests,
                "the test command left output streams open after teardown",
            )
        elif not bindings_stable:
            result = _base_result(
                parent, "inconclusive", tests,
                "the test command executable changed during the run",
            )
        elif run.returncode < 0:
            result = _base_result(
                parent, "inconclusive", tests, "the test command was interrupted"
            )
        else:
            try:
                raw_report = _stable_report_bytes(report_path, started_ns, tree)
                report = _parse_report(raw_report, report_format)
                status, detail = classify(report)
                result = _base_result(parent, status, tests, detail)
                result["report"] = {
                    "complete": report.complete,
                    "executed": report.executed,
                    "assertion_failures": report.assertion_failures,
                    "errors": report.errors,
                    "skipped": report.skipped,
                }
                result["raw_report"] = raw_report
            except ReportError as err:
                result = _base_result(parent, "inconclusive", tests, str(err))
        result.update({"exit_code": run.returncode, "output": output})
        return result
    finally:
        with contextlib.suppress(OSError, ReportError):
            subprocess.run(
                _native_git_argv(
                    repo, "worktree", "remove", "--force", str(tree)
                ),
                capture_output=True,
                check=False,
                env=_native_git_environment(),
            )
        shutil.rmtree(workdir, ignore_errors=True)


def check(
    repo: Path,
    ref: str,
    command: list[str],
    timeout: int = 900,
    report_format: str | None = None,
    report_file: str | None = None,
) -> dict:
    tests = changed_tests(repo, ref)
    if not tests:
        return _base_result(ref, "unguarded", [], "the commit changed no test files")
    if not report_format or not report_file:
        return _base_result(
            ref, "inconclusive", tests, "declare both --report-format and --report-file"
        )
    if not command:
        return _base_result(
            ref, "inconclusive", tests, "the test command is empty"
        )
    parent = parent_of(repo, ref)
    if parent is None:
        return _base_result(
            ref, "inconclusive", tests, "the commit has no parent to compare against"
        )

    workdir = Path(tempfile.mkdtemp(prefix="elenchus-"))
    tree = workdir / "tree"
    try:
        git(repo, "worktree", "add", "--quiet", "--detach", str(tree), parent)
        for relative in tests:
            blob = git(repo, "show", f"{ref}:{relative}")
            target = tree / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(blob, encoding="utf-8")
        try:
            report_path = prepare_report_path(tree, report_file)
        except ReportError as err:
            return _base_result(ref, "inconclusive", tests, str(err))

        if command.count(REPORT_PLACEHOLDER) != 1:
            return _base_result(
                ref,
                "inconclusive",
                tests,
                "the test command must contain one exact {report} argument",
            )
        resolved_command = [
            str(report_path) if argument == REPORT_PLACEHOLDER else argument
            for argument in command
        ]
        try:
            executable = _trusted_executable(resolved_command[0])
        except OSError:
            return _base_result(
                ref, "inconclusive", tests, "the test command could not be started"
            )
        resolved_command[0] = executable.path
        try:
            contained_command = _contained_guard_command(
                resolved_command, executable
            )
        except OSError:
            executable.close()
            return _base_result(
                ref,
                "inconclusive",
                tests,
                "complete descendant containment is unavailable",
            )
        environment = _guard_environment(workdir / "runtime")
        started_ns = time.time_ns()
        try:
            if not contained_command.stable():
                return _base_result(
                    ref, "inconclusive", tests,
                    "the test command executable changed during the run",
                )
            try:
                run = _run_guard_command(
                    contained_command, tree, timeout, environment
                )
            except OSError:
                return _base_result(
                    ref, "inconclusive", tests,
                    "the test command could not be started",
                )
            bindings_stable = contained_command.stable()
        finally:
            contained_command.close()

        output = (run.stdout + run.stderr).decode(
            "utf-8", errors="replace"
        )[-MAX_DIAGNOSTIC_CHARS:]
        if run.timed_out:
            return _base_result(
                ref, "inconclusive", tests, f"the run did not finish inside {timeout}s"
            )
        if not run.streams_complete:
            result = _base_result(
                ref, "inconclusive", tests,
                "the test command left output streams open after teardown",
            )
        elif not bindings_stable:
            result = _base_result(
                ref, "inconclusive", tests,
                "the test command executable changed during the run",
            )
        elif run.returncode < 0:
            result = _base_result(
                ref, "inconclusive", tests, "the test command was interrupted"
            )
        else:
            try:
                report = read_report(report_path, report_format, started_ns, tree)
                status, detail = classify(report)
                result = _base_result(ref, status, tests, detail)
                result["report"] = {
                    "complete": report.complete,
                    "executed": report.executed,
                    "assertion_failures": report.assertion_failures,
                    "errors": report.errors,
                    "skipped": report.skipped,
                }
            except ReportError as err:
                result = _base_result(ref, "inconclusive", tests, str(err))
        result.update({"exit_code": run.returncode, "output": output})
        return result
    finally:
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "remove", "--force", str(tree)],
            capture_output=True,
            check=False,
        )
        shutil.rmtree(workdir, ignore_errors=True)


def audit_line(result: dict) -> str:
    """The line to carry into the audit file's leads-not-pursued list."""
    return (
        f"Guard check on `{result['ref'][:12]}`: {result['status']} "
        f"-- {result['detail']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Elenchus guard check.")
    parser.add_argument("--repo", default=".", help="repository to inspect")
    parser.add_argument("--ref", default="HEAD", help="commit carrying the fix")
    parser.add_argument(
        "--test-command", required=True,
        help="how to run the tests, with quoting interpreted by shlex",
    )
    parser.add_argument("--report-format", choices=REPORT_FORMATS)
    parser.add_argument("--report-file")
    parser.add_argument(
        "--require-guard", action="store_true", help="exit 1 unless the fix is guarded"
    )
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        result = check(
            Path(args.repo).resolve(), args.ref, shlex.split(args.test_command),
            args.timeout, args.report_format, args.report_file,
        )
    except (RuntimeError, ValueError) as err:
        print(f"could not inspect the repository: {err}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(audit_line(result))
        for path in result["tests"]:
            print(f"  test: {path}")
    return 1 if args.require_guard and result["status"] != "guarded" else 0


if __name__ == "__main__":
    sys.exit(main())
