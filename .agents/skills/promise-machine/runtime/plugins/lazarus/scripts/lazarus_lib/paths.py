"""Fixture-root confinement without symlink or traversal shortcuts."""

from __future__ import annotations

import errno
import os
from pathlib import Path, PurePosixPath
import secrets
import stat

from .errors import PathError, ResourceLimitError
from .text import visible

MAX_FIXTURE_ENTRIES = 8192
FixtureRoot = str | os.PathLike[str] | int


def _require_secure_directory_capabilities() -> None:
    """Refuse before using a partial descriptor-confinement surface.

    Falling back to zero for either no-follow flag would turn the same source
    into a symlink-following implementation on another host. Python exposes
    the descriptor forms separately, so require the complete subset used by
    reads, writes, and inventory before opening the fixture root.
    """

    missing = [
        name for name in ("O_DIRECTORY", "O_NOFOLLOW") if not hasattr(os, name)
    ]
    supports_dir_fd = getattr(os, "supports_dir_fd", ())
    for operation, name in (
        (os.open, "open-dir-fd"),
        (os.stat, "stat-dir-fd"),
        # os.replace uses the same renameat support but is not itself listed in
        # supports_dir_fd on every POSIX Python build.
        (os.rename, "replace-dir-fd"),
        (os.unlink, "unlink-dir-fd"),
    ):
        if operation not in supports_dir_fd:
            missing.append(name)
    if os.stat not in getattr(os, "supports_follow_symlinks", ()):
        missing.append("stat-no-follow")
    if os.scandir not in getattr(os, "supports_fd", ()):
        missing.append("scandir-fd")
    if missing:
        raise PathError("platform lacks secure fixture directory operations")


def validate_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise PathError("component path must be a non-empty string")
    if "\x00" in value or "\\" in value:
        raise PathError(f"unsafe component path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/"):
        raise PathError(f"absolute component path is forbidden: {value}")
    if not path.parts:
        # "." has no parts at all, so every part-based check below passes
        # vacuously and it comes back unchanged as though it named a file. It
        # names the directory itself.
        raise PathError(f"component path names no file: {value!r}")
    if any(part in ("", ".", "..") for part in path.parts):
        raise PathError(f"component path is not normalised: {value}")
    if any(not visible(part) for part in path.parts):
        # A segment with nothing visible in it names a file whose name renders as
        # nothing. Whitespace is the obvious case and a legal POSIX filename;
        # U+200B and its neighbours are the quieter one, because `str.strip` does
        # not treat them as whitespace, so `a` and `a\u200b` are two files that
        # look identical in any listing. A space inside a name is untouched:
        # "a b" stays valid.
        raise PathError(f"component path segment names nothing: {value!r}")
    normalised = path.as_posix()
    if normalised != value:
        raise PathError(f"component path is not slash-normalised: {value}")
    return normalised


def list_fixture_files(
    root: FixtureRoot, *, max_entries: int = MAX_FIXTURE_ENTRIES
) -> set[str]:
    """Inventory one fixture beneath a path or caller-owned directory fd.

    A descriptor is duplicated on entry and remains owned by its caller. Every
    descendant is inspected and opened relative to that duplicate; no
    descriptor is converted back into a pathname.
    """

    files: set[str] = set()
    entries = 0
    root_fd = _open_root(root)

    def visit(directory_fd: int, prefix: str) -> None:
        nonlocal entries
        try:
            with os.scandir(directory_fd) as scanned:
                names: list[str] = []
                for entry in scanned:
                    entries += 1
                    if entries > max_entries:
                        raise ResourceLimitError(
                            f"fixture entry count exceeds {max_entries}"
                        )
                    names.append(entry.name)
        except OSError as exc:
            raise PathError("fixture directory cannot be inventoried") from exc

        for name in sorted(names):
            relative = validate_relative_path(f"{prefix}/{name}" if prefix else name)
            try:
                details = os.stat(
                    name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise PathError(
                    f"fixture entry is unavailable: {relative}"
                ) from exc
            if stat.S_ISLNK(details.st_mode):
                raise PathError(f"symlink component is forbidden: {relative}")
            if stat.S_ISREG(details.st_mode):
                files.add(relative)
                continue
            if not stat.S_ISDIR(details.st_mode):
                raise PathError(
                    f"non-regular fixture entry is forbidden: {relative}"
                )

            child: int | None = None
            try:
                child = os.open(name, _directory_flags(), dir_fd=directory_fd)
                opened = os.fstat(child)
                if (opened.st_dev, opened.st_ino) != (
                    details.st_dev,
                    details.st_ino,
                ):
                    raise PathError(f"fixture directory changed: {relative}")
                visit(child, relative)
                after = os.stat(
                    name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                if (after.st_dev, after.st_ino) != (
                    details.st_dev,
                    details.st_ino,
                ):
                    raise PathError(f"fixture directory changed: {relative}")
            except PathError:
                raise
            except OSError as exc:
                raise PathError(
                    f"fixture directory is unavailable: {relative}"
                ) from exc
            finally:
                if child is not None:
                    os.close(child)

    try:
        visit(root_fd, "")
        return files
    finally:
        os.close(root_fd)


def confined_directory(root: str | Path, relative: str) -> Path:
    """A directory inside another, reached without following a symlink.

    `list_fixture_files` refuses a fixture root that is itself a symlink, and
    `read_confined_bytes` refuses a symlinked component. Neither sees the
    segments in between: a fixture declared at `a/b`, where `a` is a symlink and
    `b` is a real directory, verifies against bytes that live outside the tree
    that named it. This walks every segment with no-follow descriptors and hands
    back the path only once each one has been proven a real directory.
    """
    normalised = validate_relative_path(relative)
    parts = PurePosixPath(normalised).parts
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        current = os.open(Path(root), directory_flags)
    except OSError as exc:
        raise PathError(f"directory root is unavailable: {root}") from exc
    try:
        for part in parts:
            following = os.open(part, directory_flags, dir_fd=current)
            os.close(current)
            current = following
            if not stat.S_ISDIR(os.fstat(current).st_mode):
                raise PathError(f"not a directory: {relative}")
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise PathError(
                f"a segment of {relative} is a symlink or not a directory"
            ) from exc
        raise PathError(f"directory is unavailable: {relative}") from exc
    finally:
        os.close(current)
    return Path(root) / normalised


def read_confined_bytes(
    root: FixtureRoot,
    relative: str,
    *,
    max_bytes: int,
) -> bytes:
    """Read one regular component through no-follow directory descriptors."""

    parent, name = _open_parent(root, relative)
    descriptor: int | None = None
    try:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor = os.open(name, flags, dir_fd=parent)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise PathError(f"component is not a regular file: {relative}")
        if before.st_size > max_bytes:
            raise ResourceLimitError(f"component exceeds {max_bytes} bytes: {relative}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ResourceLimitError(f"component exceeds {max_bytes} bytes: {relative}")
        after = os.fstat(descriptor)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise PathError(f"component changed while it was read: {relative}")
        return data
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise PathError(f"symlink component is forbidden: {relative}") from exc
        raise PathError(f"cannot read fixture component: {relative}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)


def atomic_write_confined(root: FixtureRoot, relative: str, data: bytes) -> None:
    """Replace one fixture file without following its previous inode."""

    parent, name = _open_parent(root, relative)
    temporary = f".{name}.{secrets.token_hex(8)}.tmp"
    created = False
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, 0o600, dir_fd=parent)
        created = True
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
        created = False
        os.fsync(parent)
    except OSError as exc:
        raise PathError(f"cannot write fixture component: {relative}") from exc
    finally:
        if created:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )


def _open_root(root: FixtureRoot) -> int:
    """Open an independent owned reference to a fixture root.

    Integer roots are caller-owned. This function duplicates them, verifies
    the duplicate is a directory, and closes only the duplicate downstream.
    No descriptor is reconstructed as a pathname.
    """

    _require_secure_directory_capabilities()
    try:
        if isinstance(root, int) and not isinstance(root, bool):
            current = os.dup(root)
        else:
            current = os.open(root, _directory_flags())
    except (OSError, TypeError, NotImplementedError) as exc:
        if getattr(exc, "errno", None) == errno.ELOOP:
            raise PathError(f"fixture root is a symlink: {root}") from exc
        raise PathError(f"fixture root is unavailable: {root}") from exc
    try:
        if not stat.S_ISDIR(os.fstat(current).st_mode):
            raise PathError(f"fixture root is not a directory: {root}")
        return current
    except Exception:
        os.close(current)
        raise


def _open_parent(root: FixtureRoot, relative: str) -> tuple[int, str]:
    normalised = validate_relative_path(relative)
    parts = PurePosixPath(normalised).parts
    current = _open_root(root)
    try:
        for part in parts[:-1]:
            following = os.open(part, _directory_flags(), dir_fd=current)
            os.close(current)
            current = following
        return current, parts[-1]
    except OSError as exc:
        os.close(current)
        raise PathError(f"component parent is unavailable: {relative}") from exc
    except Exception:
        os.close(current)
        raise
