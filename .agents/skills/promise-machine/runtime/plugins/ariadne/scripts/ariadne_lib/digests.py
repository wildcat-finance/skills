"""Digest sets, and the rules for when two of them mean the same artefact.

A statement's subject is a digest and nothing else, so every way of writing a
digest loosely is a way of making a subject match something it should not.
Uppercase hex, a truncated value, an empty set and a set carrying only a weak
algorithm are all rejected here rather than somewhere further in.

Matching is the other half. Two digest sets agree when they share a supported
algorithm and every algorithm they share holds the same value. Sharing nothing
is not agreement, and disagreeing anywhere is a mismatch even if something else
matches: an artefact that collides under one algorithm and differs under another
is two artefacts. Sharing only an unsupported algorithm is not agreement either,
because a match resting on sha1 alone is a match anyone can manufacture.
"""

import hashlib
import os
import re

HEX = re.compile(r"^[0-9a-f]+$")

ALGORITHMS = {
    "sha256": (hashlib.sha256, 64),
    "sha384": (hashlib.sha384, 96),
    "sha512": (hashlib.sha512, 128),
}
"""Algorithm name to constructor and hex length. sha1 is absent deliberately."""

DEFAULT_ALGORITHM = "sha256"

SKIPPED_DIRECTORIES = frozenset({".git"})
"""Skipped when digesting a tree. Named here so the exclusion is visible."""


class DigestError(ValueError):
    """A digest set that cannot stand for an artefact."""


def check(digests):
    """Validate a digest set and return it unchanged.

    Raises DigestError naming the specific fault, because a caller handed a
    rejected statement needs to know which of several near-identical mistakes
    it made.
    """
    if not isinstance(digests, dict):
        raise DigestError("digest set must be an object of algorithm to hex value")
    if not digests:
        raise DigestError("digest set is empty; a subject with no digest matches nothing")

    known = 0
    for algorithm, value in digests.items():
        if not isinstance(algorithm, str) or not algorithm:
            raise DigestError("digest algorithm must be a non-empty string")
        if not isinstance(value, str):
            raise DigestError("digest value for %s must be a string" % algorithm)
        if value != value.lower():
            raise DigestError(
                "digest value for %s is not lowercase hex; case-insensitive "
                "comparison is how two different digests come to look equal" % algorithm
            )
        if not HEX.fullmatch(value):
            raise DigestError("digest value for %s is not hex" % algorithm)
        if algorithm in ALGORITHMS:
            expected = ALGORITHMS[algorithm][1]
            if len(value) != expected:
                raise DigestError(
                    "digest value for %s is %d hex characters, expected %d"
                    % (algorithm, len(value), expected)
                )
            known += 1

    if not known:
        raise DigestError(
            "digest set carries no supported algorithm; supported: %s"
            % ", ".join(sorted(ALGORITHMS))
        )
    return digests


def agree(left, right):
    """True when two validated digest sets stand for the same artefact.

    A weak algorithm carried alongside a strong one is evidence, not proof: the
    agreement has to rest on a supported algorithm, and any shared algorithm
    that disagrees sinks the match regardless.
    """
    # Claims are compared with every statement subject.  Iterating the wider
    # set for each comparison lets one bounded JSON object multiply work by the
    # subject count, so walk only the smaller set and probe the other mapping.
    smaller, larger = (left, right) if len(left) <= len(right) else (right, left)
    supported = False
    for algorithm, value in smaller.items():
        if algorithm not in larger:
            continue
        if value != larger[algorithm]:
            return False
        if algorithm in ALGORITHMS:
            supported = True
    return supported


def of_bytes(data, algorithm=DEFAULT_ALGORITHM):
    if algorithm not in ALGORITHMS:
        raise DigestError("unsupported algorithm %r" % algorithm)
    return {algorithm: ALGORITHMS[algorithm][0](data).hexdigest()}


def of_file(path, algorithm=DEFAULT_ALGORITHM):
    if algorithm not in ALGORITHMS:
        raise DigestError("unsupported algorithm %r" % algorithm)
    if os.path.islink(path):
        raise DigestError("%s is a symlink; digest the target explicitly" % path)
    if not os.path.isfile(path):
        # A fifo opened for reading blocks until somebody writes to it, so a
        # hostile tree could hang a caller indefinitely with no output and no
        # timeout. `tree_listing` has refused this since the first build and its
        # comment names the same hazard; `of_file` did not, and both capture paths
        # call it directly rather than going through a tree digest.
        raise DigestError(
            "%s is not a regular file; a digest covers regular files only" % path
        )
    digest = ALGORITHMS[algorithm][0]()
    try:
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(65536), b""):
                digest.update(block)
    except OSError as error:
        raise DigestError("cannot read %s: %s" % (path, error))
    return {algorithm: digest.hexdigest()}


def tree_listing(root):
    """Sorted (relative posix path, file) pairs under root.

    Symlinks raise rather than being followed or skipped. Following one lets a
    tree digest cover bytes outside the tree; skipping one hides a file that
    was there.
    """
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise DigestError("%s is not a directory" % root)

    def refuse(error):
        # os.walk swallows errors by default, so an unreadable directory would
        # drop out of the listing and the digest would cover less than the
        # caller believes it does. A tree that cannot be read in full is not a
        # tree this can digest.
        raise DigestError("cannot read %s: %s" % (error.filename, error))

    found = []
    for directory, subdirectories, files in os.walk(
        root, followlinks=False, onerror=refuse
    ):
        subdirectories[:] = sorted(
            name
            for name in subdirectories
            if name not in SKIPPED_DIRECTORIES
        )
        for name in sorted(subdirectories):
            if os.path.islink(os.path.join(directory, name)):
                raise DigestError(
                    "%s is a symlinked directory; a tree digest will not follow it"
                    % os.path.relpath(os.path.join(directory, name), root)
                )
        for name in sorted(files):
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, root).replace(os.sep, "/")
            if os.path.islink(path):
                raise DigestError(
                    "%s is a symlink; a tree digest will not follow it" % relative
                )
            if not os.path.isfile(path):
                # A fifo opened for reading blocks until somebody writes to it,
                # so a hostile tree could hang a capture indefinitely. Anything
                # that is not a regular file is refused rather than read.
                raise DigestError(
                    "%s is not a regular file; a tree digest covers regular "
                    "files only" % relative
                )
            found.append((relative, path))
    return sorted(found)


def of_tree(root, algorithm=DEFAULT_ALGORITHM):
    """Digest a source tree over its sorted path-and-content listing.

    The listing is hashed rather than the concatenated contents, so a file
    renamed changes the digest and two files whose contents swap places do
    too.
    """
    if algorithm not in ALGORITHMS:
        raise DigestError("unsupported algorithm %r" % algorithm)
    digest = ALGORITHMS[algorithm][0]()
    for relative, path in tree_listing(root):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(of_file(path, algorithm)[algorithm].encode("ascii"))
        digest.update(b"\n")
    return {algorithm: digest.hexdigest()}


def short(digests):
    """A one-line rendering for human output: the strongest algorithm present."""
    for algorithm in ("sha512", "sha384", "sha256"):
        if algorithm in digests:
            return "%s:%s" % (algorithm, digests[algorithm][:16])
    algorithm = sorted(digests)[0]
    return "%s:%s" % (algorithm, digests[algorithm][:16])
