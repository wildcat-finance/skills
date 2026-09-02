"""The boundary every read crosses, and the caps that close it.

A target checkout is untrusted input. Nothing here follows a symlink, leaves
the declared root, or reads a file the caps do not allow. Every refusal names
the cap or the path that caused it, because a walk that stops without saying
why is indistinguishable from a tree that was simply small.
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

MAX_FILES = 20_000
MAX_FILE_BYTES = 1_048_576
MAX_DEPTH = 32

# Directories a source inventory never needs to enter. Skipping them is not a
# security control; the caps are. It keeps a normal checkout inside the caps.
SKIP_DIRECTORIES = frozenset({
    ".git", "node_modules", ".next", "out", "build", "dist", "coverage",
    ".turbo", ".vercel", "storybook-static", "__pycache__",
})


class PathRefusal(Exception):
    """One named refusal at the read boundary."""


def declared_root(supplied: str | os.PathLike[str]) -> Path:
    """Resolve the one directory every later path must stay under."""
    root = Path(supplied)
    if root.is_symlink():
        raise PathRefusal(f"root {supplied} is a symlink")
    if not root.is_dir():
        raise PathRefusal(f"root {supplied} is not a directory")
    return root.resolve(strict=True)


def relative_within(root: Path, supplied: str) -> PurePosixPath:
    """Accept one relative, non-escaping path and return it in posix form."""
    if supplied.startswith("/") or (len(supplied) > 1 and supplied[1] == ":"):
        raise PathRefusal(f"{supplied} is an absolute path")
    candidate = PurePosixPath(supplied)
    if any(part == ".." for part in candidate.parts):
        raise PathRefusal(f"{supplied} contains a parent-directory segment")
    resolved = (root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise PathRefusal(f"{supplied} escapes the declared root")
    return candidate


def source_files(
    root: Path,
    suffixes: frozenset[str],
    max_files: int = MAX_FILES,
) -> list[PurePosixPath]:
    """Every readable source file under the root, sorted, under every cap.

    Sorted because the inventory digest has to be reproducible, and an
    operating system's directory order is not.
    """
    found: list[PurePosixPath] = []
    for parent, directories, names in os.walk(root, followlinks=False):
        here = Path(parent)
        relative_parent = here.relative_to(root)
        depth = len(relative_parent.parts)
        if depth > MAX_DEPTH:
            raise PathRefusal(
                f"{relative_parent.as_posix()} is deeper than the {MAX_DEPTH}-level cap"
            )
        # Prune nested checkouts. A directory holding `.git` is a separate
        # repository or worktree, so its sources belong to that checkout and
        # counting them here would inventory the same application twice.
        directories[:] = sorted(
            name for name in directories
            if name not in SKIP_DIRECTORIES
            and not (here / name).is_symlink()
            and not (here / name / ".git").exists()
        )
        for name in sorted(names):
            path = here / name
            if path.is_symlink():
                continue
            if path.suffix not in suffixes:
                continue
            found.append(PurePosixPath((relative_parent / name).as_posix()))
            if len(found) > max_files:
                raise PathRefusal(f"the tree holds more than the {max_files}-file cap")
    return sorted(found)


def read_source(root: Path, relative: PurePosixPath) -> str:
    """Read one capped, non-symlink regular file as text."""
    path = root / relative
    if path.is_symlink():
        raise PathRefusal(f"{relative} is a symlink")
    if not path.is_file():
        raise PathRefusal(f"{relative} is not a regular file")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise PathRefusal(
            f"{relative} is {size} bytes, over the {MAX_FILE_BYTES}-byte cap"
        )
    return path.read_text(encoding="utf-8", errors="replace")
