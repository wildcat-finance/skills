#!/usr/bin/env python3
"""Run the repository suite and print a pass count."""

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import unittest


def report_target(argv):
    """Parse one fresh report path and bind its worktree identity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "report",
        nargs="?",
        metavar="PATH",
        help="the source-bound Elenchus report path",
    )
    parser.add_argument(
        "--elenchus-report",
        action="append",
        metavar="PATH",
        help="write an elenchus.unittest.v1 result to a fresh worktree path",
    )
    arguments = parser.parse_args(argv)
    values = list(arguments.elenchus_report or [])
    if arguments.report is not None:
        values.append(arguments.report)
    if len(values) > 1:
        parser.error("name one report path, either positionally or with --elenchus-report")
    if not values:
        return None

    raw = values[0]
    if not raw or "\x00" in raw:
        parser.error("--elenchus-report requires a non-empty path")
    supplied = Path(raw)
    if ".." in supplied.parts:
        parser.error("--elenchus-report must stay inside the current worktree")
    try:
        cwd = Path.cwd()
        root = cwd.resolve(strict=True)
        lexical_target = supplied if supplied.is_absolute() else cwd / supplied
        if lexical_target.is_symlink():
            parser.error("--elenchus-report target must not already exist")
        target = (
            supplied if supplied.is_absolute() else root / supplied
        ).resolve(strict=False)
        relative = target.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        parser.error("--elenchus-report must stay inside the current worktree")

    current = root
    for part in relative.parts[:-1]:
        current /= part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            break
        except OSError:
            parser.error("--elenchus-report cannot be inspected")
        if not stat.S_ISDIR(current_stat.st_mode):
            parser.error("--elenchus-report parent is not a directory")
    try:
        existing = target.lstat()
    except FileNotFoundError:
        existing = None
    except (OSError, ValueError):
        parser.error("--elenchus-report cannot be inspected")
    if existing is not None:
        parser.error("--elenchus-report target must not already exist")

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
        parser.error(
            "--elenchus-report requires secure directory operations: "
            + ", ".join(missing)
        )
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        root_stat = root.stat()
        root_fd = os.open(root, directory_flags)
        try:
            opened_stat = os.fstat(root_fd)
        finally:
            os.close(root_fd)
    except OSError:
        parser.error("--elenchus-report worktree cannot be opened and inspected")
    if (opened_stat.st_dev, opened_stat.st_ino) != (
        root_stat.st_dev,
        root_stat.st_ino,
    ):
        parser.error("--elenchus-report worktree changed during inspection")
    return root, (opened_stat.st_dev, opened_stat.st_ino), relative.parts


def result_payload(result):
    """Return Elenchus's complete unittest counter schema."""
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


def report_parent(root_fd, parts):
    """Open or create report directories without following a symlink."""
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


def report_root(root, identity):
    """Reopen the bound worktree and refuse a replaced directory."""
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


def remove_created_report(parent_fd, name, created):
    """Remove a failed write only while the target is still our inode."""
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
    """Create the declared report through its bound worktree identity."""
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
            os.close(descriptor)
            descriptor = None
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


def main(argv=None):
    """Run the suite, optionally emit its report, and preserve suite exits."""
    target = report_target(sys.argv[1:] if argv is None else argv)
    here = os.path.dirname(os.path.abspath(__file__))
    repository = os.path.dirname(here)
    suite = unittest.defaultTestLoader.discover(
        here, pattern="test_*.py", top_level_dir=repository
    )
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)

    if target is not None:
        try:
            write_report(target, result_payload(result))
        except OSError:
            print("run_tests.py: report write failed", file=sys.stderr)
            return 2

    print(f"{total - failed}/{total} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
