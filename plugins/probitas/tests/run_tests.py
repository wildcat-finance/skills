#!/usr/bin/env python3
"""Run the Probitas suite and emit one confined Elenchus report."""

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import unittest


def worktree_root():
    """Resolve the checkout that owns this runner, independent of cwd."""
    return Path(__file__).resolve(strict=True).parents[3]


def absolute_report_parts(supplied, root):
    """Bind an absolute path or outside alias to the owning checkout."""
    anchor = None
    for ancestor in supplied.parents:
        try:
            if ancestor.resolve(strict=True) == root:
                anchor = ancestor
        except (OSError, RuntimeError):
            continue
    if anchor is None:
        raise ValueError("report path is outside the worktree")
    return supplied.relative_to(anchor)


def report_target(argv):
    """Parse exactly one fresh report path and bind its worktree identity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--elenchus-report",
        action="append",
        metavar="PATH",
        help="write an elenchus.unittest.v1 result to a fresh worktree path",
    )
    arguments = parser.parse_args(argv)
    values = list(arguments.elenchus_report or [])
    if len(values) != 1:
        parser.error("name exactly one --elenchus-report path")

    raw = values[0]
    if not raw or "\x00" in raw:
        parser.error("--elenchus-report requires a non-empty path")
    supplied = Path(raw)
    if ".." in supplied.parts:
        parser.error("--elenchus-report must stay inside the current worktree")
    try:
        root = worktree_root().resolve(strict=True)
        relative = (
            absolute_report_parts(supplied, root)
            if supplied.is_absolute()
            else supplied
        )
        target = root.joinpath(*relative.parts)
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
    identity = (opened_stat.st_dev, opened_stat.st_ino)
    if identity != (root_stat.st_dev, root_stat.st_ino):
        parser.error("--elenchus-report worktree changed during inspection")
    return root, identity, relative.parts


def result_payload(result=None, *, complete=True):
    """Return the closed unittest counter schema consumed by Elenchus."""
    if result is None:
        counts = {
            "testsRun": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }
    else:
        counts = {
            "testsRun": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "expectedFailures": len(result.expectedFailures),
            "unexpectedSuccesses": len(result.unexpectedSuccesses),
        }
    return {
        "schema": "elenchus.unittest.v1",
        "complete": complete,
        **counts,
    }


def report_parent(root_fd, parts):
    """Open or create report directories without following symlinks."""
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
    """Reopen the bound checkout and refuse a replaced directory."""
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
    """Remove a failed write only while the name still identifies our inode."""
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
    """Create the declared report through its bound checkout identity."""
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
    """Run every Probitas test and preserve its structured exit evidence."""
    target = report_target(sys.argv[1:] if argv is None else argv)
    here = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.dirname(here)
    try:
        suite = unittest.defaultTestLoader.discover(
            here, pattern="test_*.py", top_level_dir=plugin_root
        )
        test_runner = unittest.TextTestRunner(verbosity=1)
        result = test_runner.run(suite)
    except BaseException:
        try:
            write_report(target, result_payload(complete=False))
        except OSError:
            pass
        raise

    try:
        write_report(target, result_payload(result))
    except OSError:
        print("run_tests.py: report write failed", file=sys.stderr)
        return 2

    total = result.testsRun
    not_passed = sum(
        len(outcomes)
        for outcomes in (
            result.failures,
            result.errors,
            result.skipped,
            result.expectedFailures,
            result.unexpectedSuccesses,
        )
    )
    print(f"{total - not_passed}/{total} tests passed")
    if total == 0:
        print("run_tests.py: no tests were discovered", file=sys.stderr)
        return 2
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
