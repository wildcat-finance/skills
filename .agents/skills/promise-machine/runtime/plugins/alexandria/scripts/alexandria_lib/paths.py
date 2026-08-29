"""Confined path handling for source and release objects."""

from __future__ import annotations

import errno
import os
from pathlib import Path, PurePosixPath
import stat

from .errors import AlexandriaError


SAFE_OPEN_SUPPORTED = (
    hasattr(os, "O_NOFOLLOW")
    and hasattr(os, "O_NONBLOCK")
    and os.open in os.supports_dir_fd
    and os.scandir in os.supports_fd
)


def validate_relative_path(value: str, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise AlexandriaError(f"{label} must be a non-empty relative POSIX path")
    if "\\" in value or "\x00" in value:
        raise AlexandriaError(f"{label} is not a safe POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise AlexandriaError(f"{label} must stay below its declared root")
    if str(path) != value:
        raise AlexandriaError(f"{label} is not in normal form")
    return path


def read_confined_file(root: Path, value: str, label: str, *, max_bytes: int) -> bytes:
    """Read through no-follow directory descriptors below one fixed root."""
    if not SAFE_OPEN_SUPPORTED:
        raise AlexandriaError("this platform cannot perform safe confined reads")
    parent, name = _open_parent(root, value, label)
    descriptor = None
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(name, flags, dir_fd=parent)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise AlexandriaError(f"{label} must name a regular file")
        if before.st_size > max_bytes:
            raise AlexandriaError(f"{label} exceeds the {max_bytes}-byte limit")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise AlexandriaError(f"{label} exceeds the {max_bytes}-byte limit")
        after = os.fstat(descriptor)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise AlexandriaError(f"{label} changed while it was read")
        return data
    except AlexandriaError:
        raise
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise AlexandriaError(f"{label} must not pass through a symlink") from exc
        raise AlexandriaError(f"cannot read {label}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)


def validate_closed_tree(root: Path, allowed_files) -> None:
    """Refuse release entries that are not bound by the manifest."""
    if not SAFE_OPEN_SUPPORTED:
        raise AlexandriaError("this platform cannot perform safe confined reads")
    files = {str(validate_relative_path(value, "release file")) for value in allowed_files}
    directories = set()
    for value in files:
        path = PurePosixPath(value)
        directories.update(str(parent) for parent in path.parents if str(parent) != ".")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    root_descriptor = None
    stack = []
    seen = set()
    try:
        root_descriptor = os.open(root, flags | getattr(os, "O_DIRECTORY", 0))
        stack.append((root_descriptor, PurePosixPath()))
        root_descriptor = None
        while stack:
            descriptor, relative = stack.pop()
            try:
                with os.scandir(descriptor) as entries:
                    for entry in entries:
                        child = relative / entry.name
                        child_name = str(child)
                        if child_name not in files and child_name not in directories:
                            raise AlexandriaError(
                                f"release contains undeclared entry {child_name}"
                            )
                        child_descriptor = os.open(entry.name, flags, dir_fd=descriptor)
                        try:
                            info = os.fstat(child_descriptor)
                            if child_name in directories:
                                if not stat.S_ISDIR(info.st_mode):
                                    raise AlexandriaError(
                                        f"release directory {child_name} is not a directory"
                                    )
                                stack.append((child_descriptor, child))
                                child_descriptor = None
                            else:
                                if not stat.S_ISREG(info.st_mode):
                                    raise AlexandriaError(
                                        f"release file {child_name} is not a regular file"
                                    )
                                seen.add(child_name)
                        finally:
                            if child_descriptor is not None:
                                os.close(child_descriptor)
            finally:
                os.close(descriptor)
        if seen != files:
            missing = sorted(files - seen)[0]
            raise AlexandriaError(f"release is missing declared file {missing}")
    except AlexandriaError:
        raise
    except OSError as exc:
        raise AlexandriaError(f"cannot inspect the release tree: {exc}") from exc
    finally:
        if root_descriptor is not None:
            os.close(root_descriptor)
        for descriptor, _relative in stack:
            os.close(descriptor)


def _open_parent(root: Path, value: str, label: str):
    relative = validate_relative_path(value, label)
    parts = relative.parts
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        current = os.open(root, flags)
    except OSError as exc:
        raise AlexandriaError(f"cannot open the declared root for {label}: {exc}") from exc
    try:
        if not stat.S_ISDIR(os.fstat(current).st_mode):
            raise AlexandriaError(f"the declared root for {label} is not a directory")
        for part in parts[:-1]:
            following = os.open(part, flags, dir_fd=current)
            os.close(current)
            current = following
        return current, parts[-1]
    except OSError as exc:
        os.close(current)
        raise AlexandriaError(f"{label} must not pass through a symlink or missing directory") from exc
    except Exception:
        os.close(current)
        raise
