"""Digest discipline: lowercase sha256 hex, files read without following links.

Uppercase hex is refused rather than folded because two spellings of one
digest would let the same bytes carry two identities through a comparison.
"""

import hashlib
import os
import re

from . import BereanError

HEX64 = re.compile(r"^[0-9a-f]{64}$")

# One pinned file is at most 4 MiB and one corpus at most 10000 files. These
# are correctness ceilings for a documentation corpus, not tuning knobs: a
# reader that accepts unbounded input can be parsed into a hang.
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_FILES = 10000


def check_hex(value, what):
    if not isinstance(value, str) or not HEX64.match(value):
        raise BereanError(f"{what} is not lowercase sha256 hex: {value!r}")
    return value


def of_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_file(path):
    """Read a regular file's bytes, refusing symlinks and oversize files."""
    if os.path.islink(path):
        raise BereanError(f"refusing symlink: {path}")
    if not os.path.isfile(path):
        raise BereanError(f"not a regular file: {path}")
    size = os.stat(path).st_size
    if size > MAX_FILE_BYTES:
        raise BereanError(f"file over the {MAX_FILE_BYTES} byte ceiling: {path}")
    with open(path, "rb") as handle:
        return handle.read()


def of_file(path):
    return of_bytes(read_file(path))


def of_listing(entries):
    """Digest a corpus listing: sorted `path\\0digest\\n` lines.

    The path is part of the digested line so a rename changes the corpus
    identity even when every file's bytes survive.
    """
    lines = []
    for path, digest in sorted(entries):
        check_hex(digest, f"digest for {path}")
        if "\x00" in path or "\n" in path:
            raise BereanError(f"control character in path: {path!r}")
        lines.append(f"{path}\x00{digest}\n")
    return of_bytes("".join(lines).encode("utf-8"))
