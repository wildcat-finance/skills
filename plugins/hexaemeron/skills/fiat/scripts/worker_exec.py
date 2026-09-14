#!/usr/bin/env python3
"""Run one declared native worker and capture bounded, private output.

The supervisor owns launch metadata and snapshots. Every launch gets fresh
scratch which is retired permanently: a process-group signal cannot prove
that no descendant detached. Only private captured files may be consumed.
This module records observations; it writes no Fiat receipt or Git metadata.
"""

import argparse
import base64
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

SCHEMA = "fiat-worker-capture/v1"
MAX_CAP = 16 * 1024 * 1024
DEFAULT_CAP = 1024 * 1024
MAX_FILES = 32
MAX_ENTRIES = 128
MAX_DEPTH = 8
MAX_RECEIPT = MAX_CAP * 2 + 262144
CHUNK = 65536
TOOLS = ("patch", "python", "shell")
SANDBOX = Path("/usr/bin/sandbox-exec")


class Refusal(ValueError):
    """A named launch or capture failure; no artifact admission is implied."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Capture:
    """Bounded streams and immutable file identities, with a diagnostic record."""

    record: dict
    stdout: bytes
    stderr: bytes


def _absolute_directory(value):
    try:
        path = Path(value)
        resolved = path.resolve(strict=True)
    except (TypeError, ValueError, OSError) as exc:
        raise Refusal("unsafe-target-root") from exc
    if (not path.is_absolute() or str(path) != str(resolved)
            or not path.is_dir() or path == Path("/")
            or any(ord(c) < 32 or ord(c) > 126 or c == "\\" for c in str(path))
            or len(os.fsencode(path)) > 2048):
        raise Refusal("unsafe-target-root")
    return path


def _relative(value):
    if type(value) is not str or not value or len(value.encode()) > 256:
        raise Refusal("invalid-output-path")
    path = PurePosixPath(value)
    if (str(path) != value or path.is_absolute() or len(path.parts) > MAX_DEPTH
            or any(p in (".", "..", ".git", ".hexaemeron") for p in path.parts)
            or any(ord(c) < 32 or ord(c) > 126 or c == "\\" for c in value)):
        raise Refusal("invalid-output-path")
    return path


def _identity(path):
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 64 * 1024 * 1024:
            raise Refusal("unsupported-executable")
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if _stamp(before) != _stamp(os.fstat(handle.fileno())):
            raise Refusal("executable-drift")
    return {"path": str(path), "sha256": digest}


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def tool_inventory():
    """Return the finite Python, shell and patch executables on this host."""
    if (platform.system() != "Darwin" or not SANDBOX.is_file()
            or not hasattr(os, "waitid") or not hasattr(os, "WNOWAIT")):
        raise Refusal("unsupported-native-host")
    python = Path(sys.executable).resolve(strict=True)
    runtime = Path(sys.base_prefix).resolve(strict=True)
    paths = {"python": python, "shell": Path("/bin/sh"), "patch": Path("/usr/bin/patch")}
    app = runtime / "Resources/Python.app/Contents/MacOS/Python"
    executables = [*paths.values(), Path("/bin/bash")]
    if app.is_file():
        executables.append(app)
    if any(not os.access(p, os.X_OK) or p.is_symlink() for p in executables):
        raise Refusal("unsupported-executable")
    return paths, runtime, [_identity(p) for p in executables]


def runtime_dependencies(runtime):
    """Declare resolved non-system dylibs of the installed standard library.

    Only the supervisor runs otool. An unresolved or unusually large runtime
    refuses; no worker-provided path extends the read policy.
    """
    modules = sorted((runtime / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
                      / "lib-dynload").glob("*.so"))
    if not modules or len(modules) > 128:
        raise Refusal("unsupported-runtime")
    pending = [*modules, Path(sys.executable).resolve()]
    checked = set()
    libraries = {}
    while pending:
        if len(checked) + len(pending) > 192:
            raise Refusal("runtime-dependency-cap")
        result = subprocess.run(["/usr/bin/otool", "-L", *map(str, pending)],
                                capture_output=True, timeout=2, check=False,
                                env={"PATH": "/bin:/usr/bin", "LC_ALL": "C"},
                                stdin=subprocess.DEVNULL, close_fds=True)
        if result.returncode or len(result.stdout) > 1024 * 1024:
            raise Refusal("unsupported-runtime")
        checked.update(map(str, pending))
        pending = []
        for line in result.stdout.decode("utf-8", "strict").splitlines():
            if not line.startswith("\t"):
                continue
            reference = line.strip().split(" (", 1)[0]
            if reference.startswith(("/usr/lib/", "/System/Library/")):
                continue
            path = Path(reference)
            if not path.is_absolute():
                raise Refusal("unresolved-runtime-dependency")
            path = path.resolve(strict=True)
            _absolute_directory(path.parent)
            if str(path) not in libraries:
                libraries[str(path)] = _identity(path)
            if str(path) not in checked and path not in pending:
                pending.append(path)
    return list(libraries.values())


def policy_text(scratch, runtime, inventory, dependencies=()):
    """Build the native policy; no caller can append a rule or deputy."""
    literal = lambda path: "(literal " + json.dumps(str(path)) + ")"
    subtree = lambda path: "(subpath " + json.dumps(str(path)) + ")"
    reads = [subtree(scratch), subtree(runtime), subtree("/System/Library"),
             subtree("/usr/lib"), literal("/dev/null"),
             literal("/dev/random"), literal("/dev/urandom")]
    reads.extend(literal(item["path"]) for item in (*inventory, *dependencies))
    return "\n".join([
        "(version 1)", "(deny default)", "(deny process-info*)", "(allow process-fork)",
        "(allow process-exec " + " ".join(literal(i["path"]) for i in inventory) + ")",
        "(allow signal (target self))",
        # Broad sysctl reads expose process environments even with process-info denied.
        # These five names keep os.uname (and ctypes startup) available.
        '(allow sysctl-read (sysctl-name "kern.ostype" "kern.osrelease" '
        '"kern.version" "kern.hostname" "hw.machine"))',
        "(allow file-read-metadata)", "(allow file-read-data (literal \"/\"))", "(allow file-read* " + " ".join(reads) + ")",
        "(allow file-write* " + subtree(scratch) + ")",
        '(allow file-write-data (literal "/dev/null"))', "",
    ])


def _environment(scratch, output):
    return {"PATH": "/bin:/usr/bin", "HOME": str(scratch),
            "TMPDIR": str(scratch / "tmp"), "LANG": "C", "LC_ALL": "C",
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
            "PYTHONSAFEPATH": "1", "FIAT_SCRATCH_ROOT": str(scratch),
            "FIAT_OUTPUT_DIR": str(output)}


def _probe(policy, python, scratch, private, env, deadline):
    sentinel = private / "policy-sentinel"
    sentinel.write_bytes(b"preserve")
    code = ("import os\n"
            "open('policy-control','wb').write(b'control')\n"
            "try:\n"
            f" open({str(sentinel)!r},'wb').write(b'changed')\n"
            "except PermissionError:\n print('ready')\n"
            "else:\n raise SystemExit(9)\n")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise Refusal("deadline")
    try:
        result = subprocess.run(
            [str(SANDBOX), "-f", str(policy), str(python), "-I", "-c", code],
            cwd=scratch, env=env, stdin=subprocess.DEVNULL, close_fds=True,
            capture_output=True, timeout=min(remaining, 2), check=False)
    except subprocess.TimeoutExpired as exc:
        raise Refusal("native-preflight-timeout") from exc
    if (result.returncode != 0 or result.stdout != b"ready\n"
            or sentinel.read_bytes() != b"preserve"):
        raise Refusal("native-policy-preflight")


def _open_dir(name, parent=None):
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                   dir_fd=parent)


def _inventory(output_fd, declared, remaining, complete=False):
    found = {}
    entries = 0
    total = 0

    def walk(directory, prefix, depth):
        nonlocal entries, total
        if depth > MAX_DEPTH:
            raise Refusal("artifact-depth-cap")
        with os.scandir(directory) as iterator:
            for item in iterator:
                entries += 1
                if entries > MAX_ENTRIES:
                    raise Refusal("artifact-entry-cap")
                name = (prefix + "/" if prefix else "") + item.name
                _relative(name)
                info = os.stat(item.name, dir_fd=directory, follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    if not any(path.startswith(name + "/") for path in declared):
                        raise Refusal("undeclared-artifact-directory")
                    child = _open_dir(item.name, directory)
                    try:
                        walk(child, name, depth + 1)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                    if name not in declared:
                        raise Refusal("undeclared-artifact")
                    found[name] = _stamp(info)
                    if len(found) > MAX_FILES:
                        raise Refusal("artifact-file-cap")
                    total += info.st_size
                    if total > remaining:
                        raise Refusal("output-cap")
                else:
                    raise Refusal("unsafe-artifact-kind")
    walk(output_fd, "", 0)
    if complete and set(found) != set(declared):
        raise Refusal("missing-artifact")
    return found, total


def _snapshot(output_fd, private, inventory, remaining, deadline):
    """Copy through held no-follow descriptors; never return mutable scratch."""
    snapshot = private / "snapshot"
    snapshot.mkdir(mode=0o700)
    records = []
    retained = 0
    for relative, expected in sorted(inventory.items()):
        held = [os.dup(output_fd)]
        links = []
        source = None
        try:
            parts = PurePosixPath(relative).parts
            for name in parts[:-1]:
                child = _open_dir(name, held[-1])
                links.append((held[-1], name, child))
                held.append(child)
            source = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=held[-1])
            before = os.fstat(source)
            if (_stamp(before) != expected or not stat.S_ISREG(before.st_mode)
                    or before.st_nlink != 1):
                raise Refusal("artifact-drift")
            destination = snapshot / relative
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            digest = hashlib.sha256()
            with destination.open("xb") as handle:
                while True:
                    if time.monotonic() >= deadline:
                        raise Refusal("deadline")
                    data = os.read(source, min(CHUNK, remaining - retained + 1))
                    if not data:
                        break
                    if len(data) > remaining - retained:
                        raise Refusal("output-cap")
                    handle.write(data)
                    digest.update(data)
                    retained += len(data)
                handle.flush()
                os.fsync(handle.fileno())
            if (_stamp(os.fstat(source)) != expected
                    or _stamp(os.stat(parts[-1], dir_fd=held[-1], follow_symlinks=False)) != expected):
                raise Refusal("artifact-drift")
            for parent, name, child in links:
                linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
                actual = os.fstat(child)
                if (linked.st_dev, linked.st_ino) != (actual.st_dev, actual.st_ino):
                    raise Refusal("artifact-directory-drift")
            destination.chmod(0o400)
            records.append({"path": relative, "sha256": digest.hexdigest(),
                            "bytes": before.st_size})
        finally:
            if source is not None:
                os.close(source)
            for descriptor in reversed(held):
                os.close(descriptor)
    return str(snapshot), records, retained


def _exited_unreaped(proc):
    # WNOWAIT preserves ownership of the numeric PID/PGID until final signals.
    return os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None


def _terminate(proc):
    """Signal the owned group before reaping; detached lifetime stays unknown."""
    denied = False
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            denied = True
        if sig == signal.SIGTERM:
            time.sleep(0.05)
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        return "unreaped-retired"
    return "signal-denied-retired" if denied else "unverified-retired"


def _capture(proc, output_fd, declared, cap, deadline):
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    retained = 0
    code = None
    with selectors.DefaultSelector() as selector:
        for name, stream in (("stdout", proc.stdout), ("stderr", proc.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map() or not _exited_unreaped(proc):
            if time.monotonic() >= deadline:
                code = "deadline"
                break
            try:
                _inventory(output_fd, declared, cap - retained)
            except (Refusal, OSError) as exc:
                code = exc.code if isinstance(exc, Refusal) else "artifact-race"
                break
            for key, _ in selector.select(timeout=min(0.02, max(0, deadline - time.monotonic()))):
                data = os.read(key.fileobj.fileno(), min(CHUNK, cap - retained + 1))
                if not data:
                    selector.unregister(key.fileobj)
                elif len(data) > cap - retained:
                    code = "output-cap"
                    break
                else:
                    buffers[key.data].extend(data)
                    retained += len(data)
            if code:
                break
    return bytes(buffers["stdout"]), bytes(buffers["stderr"]), code


def run_worker(target_root, argv, *, outputs=(), deadline_seconds=30,
               output_cap_bytes=DEFAULT_CAP, tools=TOOLS, report_operands=()):
    """Run the finite native backend, returning captured files or a refusal.

    Inputs are literal argv, declared output paths and a shared stream/artifact
    byte cap. Unsupported preflight raises Refusal before worker launch.
    Runtime refusals return a record with no snapshot or admitted artifacts.
    """
    started = time.monotonic()
    if (type(deadline_seconds) not in (int, float) or not math.isfinite(deadline_seconds)
            or not 0.1 <= deadline_seconds <= 300):
        raise Refusal("invalid-deadline")
    if type(output_cap_bytes) is not int or not 1 <= output_cap_bytes <= MAX_CAP:
        raise Refusal("invalid-output-cap")
    if type(tools) not in (list, tuple) or tuple(tools) != TOOLS:
        raise Refusal("unsupported-tool-inventory")
    paths, runtime, inventory = tool_inventory()
    target = _absolute_directory(target_root)
    if (type(argv) not in (list, tuple) or not argv or len(argv) > 128
            or any(type(a) is not str or "\0" in a for a in argv)
            or sum(len(a.encode()) for a in argv) > 16384
            or argv[0] not in {str(p) for p in paths.values()}):
        raise Refusal("invalid-worker-argv")
    if (type(outputs) not in (list, tuple) or len(outputs) > MAX_FILES
            or any(type(item) is not str for item in outputs)
            or len(set(outputs)) != len(outputs)):
        raise Refusal("invalid-artifact-inventory")
    declared = tuple(str(_relative(p)) for p in outputs)
    if (type(report_operands) not in (list, tuple) or len(report_operands) > MAX_FILES
            or any(type(item) is not dict or set(item) != {"index", "source", "output"}
                   or type(item["index"]) is not int or not 0 < item["index"] < len(argv)
                   or item["source"] != argv[item["index"]] or item["output"] not in declared
                   for item in report_operands)
            or len({item["index"] for item in report_operands}) != len(report_operands)):
        raise Refusal("invalid-report-operands")
    try:
        dependencies = runtime_dependencies(runtime)
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        raise Refusal("unsupported-runtime") from exc
    staging_parent = target / "tmp"
    staging_parent.mkdir(exist_ok=True, mode=0o700)
    if staging_parent.is_symlink() or not staging_parent.is_dir():
        raise Refusal("unsafe-staging-parent")
    launch = Path(tempfile.mkdtemp(prefix="fiat-worker-", dir=staging_parent))
    scratch = launch / "scratch"
    private = launch / "private"
    scratch.mkdir(mode=0o700)
    private.mkdir(mode=0o700)
    (scratch / "tmp").mkdir(mode=0o700)
    output = scratch / "output"
    output.mkdir(mode=0o700)
    output_fd = _open_dir(output)
    scratch_fd = _open_dir(scratch)
    policy = policy_text(scratch, runtime, inventory, dependencies)
    policy_path = private / "policy.sb"
    policy_path.write_text(policy)
    policy_path.chmod(0o400)
    source_argv = list(argv)
    argv = list(argv)
    for operand in report_operands:
        argv[operand["index"]] = str(output / operand["output"])
    env = _environment(scratch, output)
    deadline = started + deadline_seconds
    record = {"schema": SCHEMA, "event": "fiat_worker_capture", "launch": launch.name,
              "target_root": str(target), "scratch_root": str(scratch),
              "scratch_reusable": False, "cleanup": "not-started-retired",
              "tool_inventory": list(tools), "executables": inventory,
              "runtime_dependencies": dependencies,
              "native_backend": _identity(SANDBOX),
              "supervisor": _identity(Path(__file__).resolve()),
              "policy_sha256": hashlib.sha256(policy.encode()).hexdigest(),
              "deadline_seconds": deadline_seconds, "output_cap_bytes": output_cap_bytes,
              "argv": list(argv), "source_argv": source_argv,
              "report_operands": list(report_operands),
              "outputs": list(declared), "snapshot": None,
              "artifacts": [], "artifact_bytes": 0, "stream_bytes": 0,
              "status": "refused", "code": None, "returncode": None}
    stdout = stderr = b""
    proc = None
    try:
        _probe(policy_path, paths["python"], scratch, private, env, deadline)
        proc = subprocess.Popen(
            [str(paths["python"]), "-I", str(Path(__file__).resolve()), "--_start",
             str(output_cap_bytes), str(max(1, math.ceil(deadline_seconds))),
             str(policy_path), *argv], cwd=scratch, env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            close_fds=True, start_new_session=True)
        stdout, stderr, code = _capture(proc, output_fd, declared, output_cap_bytes, deadline)
        record["cleanup"] = _terminate(proc)
        record["returncode"] = proc.returncode
        if code:
            raise Refusal(code)
        if record["cleanup"] == "unreaped-retired":
            raise Refusal("worker-unreaped")
        if proc.returncode != 0:
            raise Refusal("worker-exit")
        root_info = os.stat("output", dir_fd=scratch_fd, follow_symlinks=False)
        held_info = os.fstat(output_fd)
        if (root_info.st_dev, root_info.st_ino) != (held_info.st_dev, held_info.st_ino):
            raise Refusal("artifact-directory-drift")
        remaining = output_cap_bytes - len(stdout) - len(stderr)
        found, _ = _inventory(output_fd, declared, remaining, complete=True)
        snapshot, artifacts, artifact_bytes = _snapshot(output_fd, private, found, remaining, deadline)
        after, _ = _inventory(output_fd, declared, remaining, complete=True)
        linked = os.stat("output", dir_fd=scratch_fd, follow_symlinks=False)
        if (after != found or (linked.st_dev, linked.st_ino) !=
                (held_info.st_dev, held_info.st_ino)):
            raise Refusal("artifact-drift")
        record.update(status="captured", code="captured", snapshot=snapshot,
                      artifacts=artifacts, artifact_bytes=artifact_bytes)
    except (Refusal, OSError, subprocess.SubprocessError) as exc:
        record["code"] = exc.code if isinstance(exc, Refusal) else "native-io-failure"
        if proc is not None and record["cleanup"] == "not-started-retired":
            record["cleanup"] = _terminate(proc)
        partial = private / "snapshot"
        if partial.exists():
            try:
                shutil.rmtree(partial)
            except OSError:
                record["partial_snapshot_cleanup"] = "failed-private-not-admitted"
    finally:
        if proc is not None:
            proc.stdout.close()
            proc.stderr.close()
        os.close(output_fd)
        os.close(scratch_fd)
    record["stream_bytes"] = len(stdout) + len(stderr)
    record["elapsed_seconds"] = time.monotonic() - started
    record["recovery"] = "Inspect this retired scratch; start a fresh launch after repair."
    return Capture(record, stdout, stderr)


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _read_regular(directory, name, cap):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > cap:
            raise Refusal("unsafe-controller-input")
        data = bytearray()
        while len(data) <= cap:
            part = os.read(fd, min(CHUNK, cap + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        if len(data) > cap or _stamp(before) != _stamp(os.fstat(fd)):
            raise Refusal("controller-input-drift")
        return bytes(data), _stamp(before)
    finally:
        os.close(fd)


def _directory_at(root_fd, parts, create=False):
    directory = os.dup(root_fd)
    try:
        for part in parts:
            if create:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=directory)
                except FileExistsError:
                    pass
            child = _open_dir(part, directory)
            os.close(directory)
            directory = child
        return directory
    except BaseException:
        os.close(directory)
        raise


def _exclusive(directory, name, data):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o400, dir_fd=directory)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def _controller_directories(root, root_fd, metadata, receipts, reports):
    """Check namespace links against held descriptors; record all parent inodes.

    Rechecks detect observed renames, not atomic namespace stability. Writes
    use the held directories; a rename after a pre-check can leave partial
    output there, so callers recheck before reporting successful admission.
    """
    def identity(info):
        return [info.st_dev, info.st_ino]
    try:
        links = ((None, root, root_fd), (root_fd, ".hexaemeron", metadata),
                 (metadata, "worker-launches", receipts), (metadata, "reports", reports))
        identities = []
        for parent, name, held in links:
            linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
            actual = os.fstat(held)
            if not stat.S_ISDIR(linked.st_mode) or identity(linked) != identity(actual):
                raise Refusal("controller-directory-drift")
            identities.append(identity(actual))
        return identities
    except OSError as exc:
        raise Refusal("controller-directory-drift") from exc


def _origin_snapshot(origin):
    """Hash only the explicitly declared regular files; never write origin."""
    root = _absolute_directory(origin["root"])
    fd = _open_dir(root)
    try:
        info = os.fstat(fd)
        records = []
        remaining = MAX_CAP
        for name in origin["paths"]:
            parts = _relative(name).parts
            parent = _directory_at(fd, parts[:-1])
            try:
                try:
                    data, stamp = _read_regular(parent, parts[-1], remaining)
                    remaining -= len(data)
                    records.append({"path": name, "sha256": _digest(data),
                                    "bytes": len(data), "identity": list(stamp)})
                except FileNotFoundError:
                    records.append({"path": name, "missing": True})
            finally:
                os.close(parent)
        return {"root": str(root), "identity": [info.st_dev, info.st_ino], "files": records}
    finally:
        os.close(fd)


def _launch_request(root, request):
    fields = {"schema", "root", "argv", "tools", "deadline_seconds",
              "output_cap_bytes", "reports", "origin"}
    if type(request) is not dict or set(request) != fields or request["schema"] != "fiat-worker-request/v1":
        raise Refusal("invalid-launch-request")
    if request["root"] != str(root):
        raise Refusal("request-root-mismatch")
    reports = request["reports"]
    if type(reports) is not list or not 1 <= len(reports) <= MAX_FILES:
        raise Refusal("invalid-report-inventory")
    outputs, operands, destinations = [], [], []
    for report in reports:
        if type(report) is not dict or set(report) != {"index", "source", "output"}:
            raise Refusal("invalid-report-declaration")
        source = report["source"]
        if type(source) is not str:
            raise Refusal("invalid-report-destination")
        path = PurePosixPath(source)
        if (path.is_absolute() or str(path) != source or
                path.parts[:2] != (".hexaemeron", "reports") or len(path.parts) != 3):
            raise Refusal("invalid-report-destination")
        _relative(path.name)
        outputs.append(str(_relative(report["output"])))
        operands.append(dict(report))
        destinations.append(str(root / source))
    if len(set(destinations)) != len(destinations):
        raise Refusal("duplicate-report-destination")
    origin = request["origin"]
    if (type(origin) is not dict or set(origin) != {"root", "paths"}
            or type(origin["paths"]) is not list or len(origin["paths"]) > 128
            or any(type(p) is not str for p in origin["paths"])
            or len(set(origin["paths"])) != len(origin["paths"])):
        raise Refusal("invalid-origin-inventory")
    _absolute_directory(origin["root"])
    for name in origin["paths"]:
        _relative(name)
    return outputs, operands, destinations


def controller_launch(root, request, controller_source):
    """Capture one native launch and retain a controller-owned admission record.

    This is a separate execution path, not a Fiat phase receipt. A caller must
    retain the returned receipt digest before asking to promote its files.
    Origin changes are observed without attribution and never rolled back.
    """
    root = _absolute_directory(root)
    outputs, operands, destinations = _launch_request(root, request)
    request = json.loads(_json_bytes(request))
    controller_identity = _identity(Path(controller_source).resolve())
    before = _origin_snapshot(request["origin"])
    root_fd = _open_dir(root)
    metadata = receipts = reports_fd = None
    try:
        metadata = _directory_at(root_fd, (".hexaemeron",), create=True)
        receipts = _directory_at(metadata, ("worker-launches",), create=True)
        reports_fd = _directory_at(metadata, ("reports",), create=True)
        directories = _controller_directories(root, root_fd, metadata, receipts, reports_fd)
        for destination in destinations:
            try:
                os.stat(Path(destination).name, dir_fd=reports_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise Refusal("report-destination-exists")
        capture = run_worker(root, request["argv"], outputs=outputs, tools=request["tools"],
                             deadline_seconds=request["deadline_seconds"],
                             output_cap_bytes=request["output_cap_bytes"], report_operands=operands)
        try:
            after = _origin_snapshot(request["origin"])
            origin_status = "unchanged" if before == after else "changed-unattributed"
        except (OSError, Refusal):
            after = None
            origin_status = "unreadable-unattributed"
        record = {"schema": "fiat-worker-launch/v1", "request": request,
                  "request_sha256": _digest(_json_bytes(request)),
                  "controller": controller_identity,
                  "controller_directories": directories,
                  "root_identity": [os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino],
                  "capture": capture.record, "destinations": destinations,
                  "streams": {name: {"base64": base64.b64encode(data).decode("ascii"),
                                     "bytes": len(data), "sha256": _digest(data)}
                              for name, data in (("stdout", capture.stdout), ("stderr", capture.stderr))},
                  "stream_evidence": "Untrusted worker output; no inferred syscall attribution.",
                  "origin_before": before, "origin_after": after,
                  "origin_status": origin_status, "attribution": "unknown",
                  "status": "ready" if origin_status == "unchanged" and
                  capture.record["status"] == "captured" and controller_identity ==
                  _identity(Path(controller_source).resolve()) else "refused",
                  "recovery": "Preserve origin changes; start a fresh launch to resnapshot."}
        data = _json_bytes(record)
        name = uuid.uuid4().hex + ".json"
        if _controller_directories(root, root_fd, metadata, receipts, reports_fd) != directories:
            raise Refusal("controller-directory-drift")
        _exclusive(receipts, name, data)
        os.fsync(receipts)
        _controller_directories(root, root_fd, metadata, receipts, reports_fd)
        return {"receipt": str(root / ".hexaemeron/worker-launches" / name),
                "sha256": _digest(data), "record": record}
    finally:
        if receipts is not None:
            os.close(receipts)
        if reports_fd is not None:
            os.close(reports_fd)
        if metadata is not None:
            os.close(metadata)
        os.close(root_fd)


def controller_admit(root, receipt, digest, controller_source):
    """Verify a pinned private capture, then exclusively publish its reports."""
    root = _absolute_directory(root)
    path = Path(receipt)
    if (path.parent != root / ".hexaemeron/worker-launches" or
            len(path.stem) != 32 or any(c not in "0123456789abcdef" for c in path.stem)
            or path.suffix != ".json"):
        raise Refusal("invalid-launch-receipt-path")
    root_fd = _open_dir(root)
    metadata = receipts = reports = snapshot_fd = None
    try:
        metadata = _directory_at(root_fd, (".hexaemeron",))
        receipts = _directory_at(metadata, ("worker-launches",))
        reports = _directory_at(metadata, ("reports",))
        data, _ = _read_regular(receipts, path.name, MAX_RECEIPT)
        if _digest(data) != digest:
            raise Refusal("launch-receipt-mismatch")
        record = json.loads(data)
        if _controller_directories(root, root_fd, metadata, receipts, reports) != record["controller_directories"]:
            raise Refusal("controller-directory-drift")
        request = record["request"]
        outputs, operands, destinations = _launch_request(root, request)
        if (record["schema"] != "fiat-worker-launch/v1" or record["status"] != "ready"
                or record["request_sha256"] != _digest(_json_bytes(request))
                or record["controller"] != _identity(Path(controller_source).resolve())
                or record["root_identity"] != [os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino]
                or record["destinations"] != destinations):
            raise Refusal("stale-launch-receipt")
        current_origin = _origin_snapshot(request["origin"])
        if current_origin != record["origin_before"]:
            _exclusive(receipts, path.stem + ".drift-" + uuid.uuid4().hex + ".json",
                       _json_bytes({"event": "worker_admission_refused", "receipt_sha256": digest,
                                    "code": "origin-drift", "attribution": "unknown",
                                    "origin_before": record["origin_before"],
                                    "origin_observed": current_origin,
                                    "recovery": "Preserve origin changes; launch again to resnapshot."}))
            os.fsync(receipts)
            raise Refusal("origin-drift-preserved-resnapshot-required")
        capture = record["capture"]
        tools, runtime, inventory = tool_inventory()
        dependencies = runtime_dependencies(runtime)
        if (capture["supervisor"] != _identity(Path(__file__).resolve())
                or capture["executables"] != inventory or capture["runtime_dependencies"] != dependencies
                or capture["native_backend"] != _identity(SANDBOX)
                or capture["tool_inventory"] != request["tools"]
                or capture["deadline_seconds"] != request["deadline_seconds"]
                or capture["output_cap_bytes"] != request["output_cap_bytes"]
                or capture["source_argv"] != request["argv"] or capture["report_operands"] != operands
                or capture["outputs"] != outputs or capture["status"] != "captured"):
            raise Refusal("launch-binding-mismatch")
        scratch = Path(capture["scratch_root"])
        launch = scratch.parent
        if (launch.parent != root / "tmp" or not launch.name.startswith("fiat-worker-")
                or scratch.name != "scratch" or capture["snapshot"] != str(launch / "private/snapshot")
                or capture["target_root"] != str(root)
                or capture["policy_sha256"] != _digest(policy_text(scratch, runtime, inventory, dependencies).encode())):
            raise Refusal("snapshot-binding-mismatch")
        resolved_argv = list(request["argv"])
        for operand in operands:
            resolved_argv[operand["index"]] = str(scratch / "output" / operand["output"])
        if capture["argv"] != resolved_argv:
            raise Refusal("launch-argv-mismatch")
        snapshot_fd = _directory_at(root_fd, ("tmp", launch.name, "private", "snapshot"))
        remaining = request["output_cap_bytes"] - capture["stream_bytes"]
        contents = []
        if [a["path"] for a in capture["artifacts"]] != sorted(outputs):
            raise Refusal("artifact-manifest-mismatch")
        by_output = {item["output"]: destination for item, destination in zip(request["reports"], destinations)}
        for artifact in capture["artifacts"]:
            parts = _relative(artifact["path"]).parts
            parent = _directory_at(snapshot_fd, parts[:-1])
            try:
                content, _ = _read_regular(parent, parts[-1], remaining)
            finally:
                os.close(parent)
            if _digest(content) != artifact["sha256"] or len(content) != artifact["bytes"]:
                raise Refusal("private-snapshot-mismatch")
            remaining -= len(content)
            contents.append((Path(by_output[artifact["path"]]).name, content))
        # Claim once before publication. Any partial publication remains visible
        # and requires operator inspection; retry never overwrites its files.
        _controller_directories(root, root_fd, metadata, receipts, reports)
        _exclusive(receipts, path.stem + ".admission.json", _json_bytes({"receipt_sha256": digest,
                   "status": "promotion-started", "destinations": destinations}))
        for name, content in contents:
            _controller_directories(root, root_fd, metadata, receipts, reports)
            _exclusive(reports, name, content)
            _controller_directories(root, root_fd, metadata, receipts, reports)
        os.fsync(reports)
        _exclusive(receipts, path.stem + ".complete.json", _json_bytes({"receipt_sha256": digest,
                   "status": "reports-written", "destinations": destinations}))
        os.fsync(receipts)
        _controller_directories(root, root_fd, metadata, receipts, reports)
        return {"status": "admitted", "receipt_sha256": digest, "destinations": destinations}
    finally:
        for fd in (receipts, reports, snapshot_fd, metadata, root_fd):
            if fd is not None:
                os.close(fd)


def _start(arguments):
    import resource
    # Limits run in a fresh isolated interpreter, avoiding preexec_fn in threads.
    cap, cpu, policy, *argv = arguments
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (int(cap) + 1, int(cap) + 1))
    resource.setrlimit(resource.RLIMIT_CPU, (int(cpu) + 1, int(cpu) + 1))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    os.execve(str(SANDBOX), [str(SANDBOX), "-f", policy, *argv], dict(os.environ))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", action="append", default=[])
    parser.add_argument("--deadline", type=float, default=30)
    parser.add_argument("--output-cap", type=int, default=DEFAULT_CAP)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        capture = run_worker(args.root, command, outputs=args.output,
                             deadline_seconds=args.deadline, output_cap_bytes=args.output_cap)
    except (Refusal, OSError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "refused",
                          "code": exc.code if isinstance(exc, Refusal) else "invalid-root"}))
        return 1
    print(json.dumps(capture.record, sort_keys=True))
    return 0 if capture.record["status"] == "captured" else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["--_start"]:
        _start(sys.argv[2:])
    else:
        raise SystemExit(main())
