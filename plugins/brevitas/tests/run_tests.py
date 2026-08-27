#!/usr/bin/env python3
"""Run the Brevitas suite and emit one fresh Elenchus report."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import stat
import sys
import unittest


MAX_REPORT_BYTES = 64 * 1024


def worktree_root() -> Path:
    """Return the checkout that owns this source-owned runner."""
    return Path(__file__).resolve(strict=True).parents[3]


def report_target(argv: list[str]) -> tuple[Path, tuple[int, int], tuple[str, ...]]:
    """Bind one fresh report path below the owning worktree."""
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
        root = worktree_root().resolve(strict=True)
        relative = supplied.relative_to(root) if supplied.is_absolute() else supplied
    except (OSError, RuntimeError, ValueError):
        parser.error("REPORT must stay inside the current worktree")
    if not relative.parts:
        parser.error("REPORT must name a file below the current worktree")

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

    target = root.joinpath(*relative.parts)
    try:
        existing = target.lstat()
    except FileNotFoundError:
        existing = None
    except OSError:
        parser.error("REPORT cannot be inspected")
    if existing is not None:
        parser.error("REPORT target must not already exist")

    missing = [
        name for name in ("O_DIRECTORY", "O_NOFOLLOW") if not hasattr(os, name)
    ]
    for operation, name in (
        (os.open, "os.open(dir_fd)"),
        (os.mkdir, "os.mkdir(dir_fd)"),
        (os.stat, "os.stat(dir_fd)"),
        (os.link, "os.link(dir_fd)"),
        (os.unlink, "os.unlink(dir_fd)"),
    ):
        if operation not in os.supports_dir_fd:
            missing.append(name)
    if os.stat not in os.supports_follow_symlinks:
        missing.append("os.stat(follow_symlinks)")
    if os.link not in os.supports_follow_symlinks:
        missing.append("os.link(follow_symlinks)")
    if not hasattr(os, "fchmod"):
        missing.append("os.fchmod")
    if missing:
        parser.error("REPORT requires secure directory operations: " + ", ".join(missing))

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        root_stat = root.stat()
        root_fd = os.open(root, flags)
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


def result_payload(result: unittest.TestResult) -> dict[str, object]:
    """Return the complete ``unittest-json-v1`` counter schema."""
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


def report_root(root: Path, identity: tuple[int, int]) -> int:
    """Reopen the bound worktree without accepting a replacement."""
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


def report_parent(root_fd: int, parts: tuple[str, ...]) -> int:
    """Open or privately create a parent chain without following aliases."""
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


def _unlink_own(parent_fd: int, name: str, identity: tuple[int, int]) -> None:
    """Remove a failed write only while the name still identifies our file."""
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return
    if (current.st_dev, current.st_ino) != identity:
        return
    try:
        os.unlink(name, dir_fd=parent_fd)
    except OSError:
        pass


def _private_report(parent_fd: int) -> tuple[str, int, tuple[int, int]]:
    """Create one mode-0600 temporary report in the destination directory."""
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    for _ in range(16):
        name = f".brevitas-report-{secrets.token_hex(12)}.tmp"
        try:
            descriptor = os.open(name, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError:
            continue
        created = os.fstat(descriptor)
        try:
            os.fchmod(descriptor, 0o600)
        except OSError:
            os.close(descriptor)
            _unlink_own(parent_fd, name, (created.st_dev, created.st_ino))
            raise
        secured = os.fstat(descriptor)
        if not stat.S_ISREG(secured.st_mode) or stat.S_IMODE(secured.st_mode) != 0o600:
            os.close(descriptor)
            _unlink_own(parent_fd, name, (created.st_dev, created.st_ino))
            raise OSError("report temporary is not a private regular file")
        return name, descriptor, (secured.st_dev, secured.st_ino)
    raise OSError("could not create a private report temporary")


def _write_all(descriptor: int, body: bytes) -> None:
    remaining = memoryview(body)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("report write made no progress")
        remaining = remaining[written:]


def write_report(
    target: tuple[Path, tuple[int, int], tuple[str, ...]],
    payload: dict[str, object],
) -> None:
    """Write bounded bytes privately, then atomically publish the report."""
    body = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    if len(body) > MAX_REPORT_BYTES:
        raise OSError("report exceeds the size limit")

    root, root_identity, parts = target
    root_fd = report_root(root, root_identity)
    try:
        parent_fd = report_parent(root_fd, parts[:-1])
        try:
            temporary, descriptor, temporary_identity = _private_report(parent_fd)
            try:
                _write_all(descriptor, body)
                os.fsync(descriptor)
                written = os.fstat(descriptor)
                os.lseek(descriptor, 0, os.SEEK_SET)
                readback = os.read(descriptor, len(body) + 1)
                if written.st_size != len(body) or readback != body:
                    raise OSError("report temporary bytes changed during write")

                try:
                    os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise OSError("report target already exists")

                temporary_entry = os.stat(
                    temporary,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                if (temporary_entry.st_dev, temporary_entry.st_ino) != temporary_identity:
                    raise OSError("report temporary identity changed")
                os.link(
                    temporary,
                    parts[-1],
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                final = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
                if (
                    not stat.S_ISREG(final.st_mode)
                    or (final.st_dev, final.st_ino) != temporary_identity
                    or final.st_size != len(body)
                    or final.st_size > MAX_REPORT_BYTES
                    or stat.S_IMODE(final.st_mode) != 0o600
                ):
                    raise OSError("published report identity or size changed")
                _unlink_own(parent_fd, temporary, temporary_identity)
                try:
                    os.stat(temporary, dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise OSError("report temporary could not be removed")

                os.lseek(descriptor, 0, os.SEEK_SET)
                published_readback = os.read(descriptor, len(body) + 1)
                published_descriptor = os.fstat(descriptor)
                published_entry = os.stat(
                    parts[-1], dir_fd=parent_fd, follow_symlinks=False
                )
                if (
                    published_readback != body
                    or (published_descriptor.st_dev, published_descriptor.st_ino)
                    != temporary_identity
                    or (published_entry.st_dev, published_entry.st_ino)
                    != temporary_identity
                    or published_descriptor.st_size != len(body)
                    or published_entry.st_size != len(body)
                    or stat.S_IMODE(published_entry.st_mode) != 0o600
                ):
                    raise OSError("published report identity or bytes changed")
                os.fsync(parent_fd)
                os.close(descriptor)
                descriptor = -1
            except BaseException:
                if descriptor >= 0:
                    try:
                        os.close(descriptor)
                    except OSError:
                        pass
                _unlink_own(parent_fd, parts[-1], temporary_identity)
                _unlink_own(parent_fd, temporary, temporary_identity)
                raise
        finally:
            os.close(parent_fd)
    finally:
        os.close(root_fd)


def main(argv: list[str] | None = None) -> int:
    """Run every Brevitas unit test and preserve its suite exit."""
    target = report_target(sys.argv[1:] if argv is None else argv)
    here = Path(__file__).resolve(strict=True).parent
    plugin_root = here.parent
    suite = unittest.defaultTestLoader.discover(
        str(here), pattern="test_*.py", top_level_dir=str(plugin_root)
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("run_tests.py: report write failed", file=sys.stderr)
        return 2

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
    print(f"{result.testsRun - not_passed}/{result.testsRun} tests passed")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
