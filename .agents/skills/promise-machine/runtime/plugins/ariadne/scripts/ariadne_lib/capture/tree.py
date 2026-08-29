"""Reading a directory of files without losing any of them quietly.

Every capture that digests a directory needs the same refusals, and the reason is
the same one the gates exist for. A generic directory walk can materialise a wide
directory before its caller enforces a bound, does not descend a symlinked
directory, and may swallow a directory it cannot read. Any of those would defeat a
capture ceiling or drop files from the statement and bundle digest without a
record. This reader refuses at the entry where the boundary is crossed instead.

Written once because it was written twice. The dataset capture and the state-fixture
capture both walk a tree, and the second copy of a path helper in this package was
where a traversal defect had already been found: `usable_path` normalised only a
doubled backslash in both predicates, because one had been copied from the other.
A third copy of a walk was not worth the same risk.

The wording is parameterised rather than shared, because a reader gets told which
kind of directory refused them: a release for the dataset capture, a fixture for the
state-fixture one.
"""

import os
import stat

MAX_FILES = 4096
"""The maximum number of filesystem entries a capture will traverse.

The name predates counting directories as well as files. A capture reads somebody's
own output directory rather than a stranger's archive, but the cap keeps a mistaken
`--release /` from walking a filesystem.
"""

REFUSED_NAMES = frozenset({".git", "__pycache__"})
"""Directories that have no business in something being digested.

Skipping them quietly would be the silent absence this whole tool refuses: the
bundle digest would cover part of the tree while the statement said nothing about
the rest. Refusing says which directory to remove, and the caller decides.
"""


class CaptureError(ValueError):
    """Something that cannot be captured, with the reason a caller can act on."""


def confined(path, what):
    """Resolve a directory, refusing anything that is not one.

    `realpath` collapses `..` and follows symlinks, so the resolved path is what
    every later containment check compares against.
    """
    if not path:
        raise CaptureError("%s is required" % what)
    resolved = os.path.realpath(path)
    if not os.path.isdir(resolved):
        raise CaptureError("%s %s is not a directory" % (what, path))
    return resolved


def inside(root, path, what, kind="release"):
    """The resolved path, or a refusal when it leaves the root.

    A symlink inside the tree pointing out of it is the case this catches: the
    file reads fine, and its digest would describe something the tree does not
    contain.
    """
    resolved = os.path.realpath(path)
    try:
        shared = os.path.commonpath([root, resolved])
    except ValueError as error:
        raise CaptureError(
            "%s %s: cannot place it inside %s (%s)" % (what, path, root, error)
        )
    if shared != root:
        raise CaptureError("%s %s resolves outside the %s" % (what, path, kind))
    return resolved


def files(root, kind="release"):
    """Every file under root, as (relative path, absolute path), sorted.

    Sorted because the statement has to come out the same way twice.

    Nothing is skipped, and the three refusals in this module's docstring are why.
    """

    def unreadable(error):
        raise CaptureError(
            "cannot read %s: %s; a %s that cannot be read whole cannot be captured"
            % (getattr(error, "filename", root), error, kind)
        )

    found = []
    seen_entries = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        child_directories = []
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    seen_entries += 1
                    if seen_entries > MAX_FILES:
                        raise CaptureError(
                            "%s holds more than %d entries; name a narrower directory"
                            % (kind, MAX_FILES)
                        )

                    absolute = os.path.join(directory, entry.name)
                    relative = os.path.relpath(absolute, root)
                    mode = entry.stat(follow_symlinks=False).st_mode
                    if stat.S_ISLNK(mode):
                        try:
                            linked_directory = entry.is_dir()
                        except OSError:
                            linked_directory = False
                        if linked_directory:
                            raise CaptureError(
                                "%s is a symlink to a directory; its contents would "
                                "be left out of the statement and out of the %s "
                                "digest without anything saying so" % (relative, kind)
                            )
                        raise CaptureError(
                            "%s is a symlink; a digest over its target would describe "
                            "something the %s does not contain" % (relative, kind)
                        )
                    if stat.S_ISDIR(mode):
                        if entry.name in REFUSED_NAMES:
                            raise CaptureError(
                                "%s holds %s; remove it or name a directory that holds "
                                "only the %s" % (kind, relative, kind)
                            )
                        child_directories.append(absolute)
                        continue
                    if not stat.S_ISREG(mode):
                        # Refused before anything opens it. A fifo opened for
                        # reading blocks until somebody writes to it, which hangs
                        # a capture with no output and no timeout.
                        raise CaptureError(
                            "%s is not a regular file; a %s holds files, and reading "
                            "a fifo would block until something wrote to it"
                            % (relative, kind)
                        )
                    inside(root, absolute, "%s file" % kind, kind)
                    found.append((relative, absolute))
        except OSError as error:
            unreadable(error)
        pending.extend(reversed(sorted(child_directories)))
    if not found:
        raise CaptureError("%s %s holds no files" % (kind, root))
    return sorted(found, key=lambda item: item[0])
