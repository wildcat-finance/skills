#!/usr/bin/env python3
"""Run the complete run-observation surface and emit one fresh Elenchus report."""

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

REQUIRED_SURFACE = (
    Path("schemas/promise-machine-run-observation-v1.schema.json"),
    Path("scripts/run_observation.py"),
    Path("tests/test_promise_machine_contract.py"),
    Path("tests/test_run_observation.py"),
    Path("tests/test_run_observation_inoculation.py"),
    Path("tests/fixtures/run-observation/434-carryover-v1.json"),
)
MODULES = (
    "tests.test_promise_machine_contract",
    "tests.test_run_observation",
    "tests.test_run_observation_inoculation",
)


def report_target(argv):
    """Parse one fresh confined report path and bind the worktree identity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", metavar="REPORT")
    arguments = parser.parse_args(argv)
    raw = arguments.report
    if not raw or "\x00" in raw:
        parser.error("REPORT requires a non-empty path")
    supplied = Path(raw)
    if ".." in supplied.parts:
        parser.error("REPORT must stay inside the current worktree")
    try:
        root = Path.cwd().resolve(strict=True)
        lexical_target = supplied if supplied.is_absolute() else root / supplied
        if lexical_target.is_symlink():
            parser.error("REPORT target must not already exist")
        target = lexical_target.resolve(strict=False)
        relative = target.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        parser.error("REPORT must stay inside the current worktree")

    current = root
    for part in relative.parts[:-1]:
        current /= part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            break
        except OSError:
            parser.error("REPORT cannot be inspected")
        if not stat.S_ISDIR(current_stat.st_mode):
            parser.error("REPORT parent is not a directory")
    try:
        existing = target.lstat()
    except FileNotFoundError:
        existing = None
    except (OSError, ValueError):
        parser.error("REPORT cannot be inspected")
    if existing is not None:
        parser.error("REPORT target must not already exist")

    missing = []
    for name in ("O_DIRECTORY", "O_NOFOLLOW"):
        if not hasattr(os, name):
            missing.append(f"os.{name}")
    supports_dir_fd = getattr(os, "supports_dir_fd", ())
    for operation, name in (
        (os.open, "os.open(dir_fd)"),
        (os.mkdir, "os.mkdir(dir_fd)"),
        (os.stat, "os.stat(dir_fd)"),
        (os.unlink, "os.unlink(dir_fd)"),
    ):
        if operation not in supports_dir_fd:
            missing.append(name)
    supports_follow_symlinks = getattr(os, "supports_follow_symlinks", ())
    if os.stat not in supports_follow_symlinks:
        missing.append("os.stat(follow_symlinks)")
    if missing:
        parser.error("REPORT requires secure directory operations: " + ", ".join(missing))

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        root_stat = root.stat()
        root_fd = os.open(root, directory_flags)
        try:
            opened_stat = os.fstat(root_fd)
        finally:
            os.close(root_fd)
    except OSError:
        parser.error("REPORT worktree cannot be opened and inspected")
    identity = (opened_stat.st_dev, opened_stat.st_ino)
    if identity != (root_stat.st_dev, root_stat.st_ino):
        parser.error("REPORT worktree changed during inspection")
    return root, identity, relative.parts


def result_payload(result):
    return {
        "schema": "elenchus.unittest.v1",
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }


def report_root(root, identity):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(root, flags)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != identity:
            raise OSError("report worktree identity changed")
        return descriptor
    except OSError:
        os.close(descriptor)
        raise


def report_parent(root_fd, parts):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current_fd = os.dup(root_fd)
    try:
        for part in parts:
            try:
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except FileNotFoundError:
                try:
                    os.mkdir(part, 0o700, dir_fd=current_fd)
                except FileExistsError:
                    pass
                next_fd = os.open(part, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except OSError:
        os.close(current_fd)
        raise


def existing_report_parent(root_fd, parts):
    """Open an existing parent chain without creating or following aliases."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current_fd = os.dup(root_fd)
    try:
        for part in parts:
            next_fd = os.open(part, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except OSError:
        os.close(current_fd)
        raise


def remove_created_report(parent_fd, name, created):
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return
    if (current.st_dev, current.st_ino) != (created.st_dev, created.st_ino):
        return
    try:
        os.unlink(name, dir_fd=parent_fd)
    except OSError:
        pass


def write_report(target, payload):
    root, identity, parts = target
    if not parts:
        raise OSError("report path has no filename")
    root_fd = report_root(root, identity)
    try:
        parent_fd = report_parent(root_fd, parts[:-1])
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        descriptor = None
        created = None
        try:
            descriptor = os.open(parts[-1], flags, 0o600, dir_fd=parent_fd)
            created = os.fstat(descriptor)
            if not stat.S_ISREG(created.st_mode):
                raise OSError("report target is not a regular file")
            body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
            remaining = memoryview(body)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError("report write made no progress")
                remaining = remaining[written:]
            os.fsync(descriptor)
            written_state = os.fstat(descriptor)
            os.close(descriptor)
            descriptor = None
            verify_root_fd = report_root(root, identity)
            try:
                verify_parent_fd = existing_report_parent(verify_root_fd, parts[:-1])
                try:
                    original_parent = os.fstat(parent_fd)
                    reopened_parent = os.fstat(verify_parent_fd)
                    read_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
                    verify_fd = os.open(parts[-1], read_flags, dir_fd=verify_parent_fd)
                    try:
                        reopened = os.fstat(verify_fd)
                        readback = bytearray()
                        remaining_bytes = len(body) + 1
                        while remaining_bytes:
                            chunk = os.read(verify_fd, min(65_536, remaining_bytes))
                            if not chunk:
                                break
                            readback.extend(chunk)
                            remaining_bytes -= len(chunk)
                        reread = os.fstat(verify_fd)
                    finally:
                        os.close(verify_fd)
                    named = os.stat(
                        parts[-1],
                        dir_fd=verify_parent_fd,
                        follow_symlinks=False,
                    )
                    if (
                        (original_parent.st_dev, original_parent.st_ino)
                        != (reopened_parent.st_dev, reopened_parent.st_ino)
                        or not stat.S_ISREG(named.st_mode)
                        or (named.st_dev, named.st_ino)
                        != (created.st_dev, created.st_ino)
                        or not stat.S_ISREG(reopened.st_mode)
                        or (reopened.st_dev, reopened.st_ino)
                        != (created.st_dev, created.st_ino)
                        or (reread.st_dev, reread.st_ino)
                        != (created.st_dev, created.st_ino)
                        or len(readback) != len(body)
                        or bytes(readback) != body
                        or reopened.st_size != len(body)
                        or reread.st_size != len(body)
                        or named.st_size != len(body)
                        or written_state.st_size != len(body)
                        or reread.st_mtime_ns != reopened.st_mtime_ns
                        or reread.st_ctime_ns != reopened.st_ctime_ns
                        or named.st_mtime_ns != reread.st_mtime_ns
                        or named.st_ctime_ns != reread.st_ctime_ns
                    ):
                        raise OSError("report target identity or bytes changed during write")
                finally:
                    os.close(verify_parent_fd)
            finally:
                os.close(verify_root_fd)
        except OSError:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if created is not None:
                remove_created_report(parent_fd, parts[-1], created)
            raise
        finally:
            os.close(parent_fd)
    finally:
        os.close(root_fd)


def missing_surface_suite(root):
    missing = [path.as_posix() for path in REQUIRED_SURFACE if not (root / path).is_file()]
    if not missing:
        return None

    def required_surface_is_present():
        raise FileNotFoundError("required run-observation test surface absent: " + ", ".join(missing))

    return unittest.TestSuite([unittest.FunctionTestCase(required_surface_is_present)])


def main(argv=None):
    target = report_target(sys.argv[1:] if argv is None else argv)
    root = Path.cwd().resolve(strict=True)
    suite = missing_surface_suite(root)
    if suite is None:
        suite = unittest.defaultTestLoader.loadTestsFromNames(MODULES)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("emit_run_observation_report.py: report write failed", file=sys.stderr)
        return 2
    failed = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failed}/{result.testsRun} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
