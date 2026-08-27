"""Path discipline for documents that name files.

A corpus or release path is relative, forward-slashed and stays inside its
tree. Backslashes are refused rather than normalised, because a path that
means different files on different systems pins neither.
"""

import os

from . import BereanError


def usable(path, what="path"):
    if not isinstance(path, str) or not path:
        raise BereanError(f"{what} is blank or not a string")
    if "\\" in path:
        raise BereanError(f"{what} carries a backslash: {path!r}")
    if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
        raise BereanError(f"{what} is absolute: {path!r}")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise BereanError(f"{what} leaves or re-enters its tree: {path!r}")
    return path


def resolve(root, relative, what="path"):
    """Join a checked relative path onto a root, refusing symlinked parents."""
    usable(relative, what)
    current = root
    for part in relative.split("/"):
        current = os.path.join(current, part)
        if os.path.islink(current):
            raise BereanError(f"{what} crosses a symlink: {relative!r}")
    return current
