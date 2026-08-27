"""Corpus manifests: the digest-pinned inventory of a document tree.

`build` walks the tree and writes `berean-corpus/v1`; `verify` re-reads the
tree and requires exact agreement in both directions, so a drifted byte, a
missing file and an unpinned extra file are all refusals. A citation can
only be as strong as this pin, which is why verification is set equality
rather than a subset check.
"""

import os

from . import BereanError
from . import canonical
from . import digests
from . import jsonio
from . import paths

FORMAT = "berean-corpus/v1"
FIELDS = ("format", "corpus_version", "files", "corpus_digest")
FILE_FIELDS = ("path", "bytes", "sha256")


class Check:
    """One named verification result."""

    def __init__(self, name, passed, detail=""):
        self.name = name
        self.passed = passed
        self.detail = detail

    def line(self):
        state = "pass" if self.passed else "fail"
        detail = f": {self.detail}" if self.detail else ""
        return f"{state}  {self.name}{detail}"


def _walk(root):
    """Sorted relative paths of every regular file under root, refusing links."""
    if os.path.islink(root) or not os.path.isdir(root):
        raise BereanError(f"corpus root is not a plain directory: {root}")
    found = []
    for current, directories, files in os.walk(root):
        directories.sort()
        for name in directories:
            if os.path.islink(os.path.join(current, name)):
                raise BereanError(f"refusing symlink: {os.path.join(current, name)}")
        for name in sorted(files):
            full = os.path.join(current, name)
            relative = os.path.relpath(full, root).replace(os.sep, "/")
            if name.startswith(".") and name.endswith(".staging"):
                raise BereanError(f"staging file inside the corpus: {relative}")
            found.append(relative)
    if len(found) > digests.MAX_FILES:
        raise BereanError(f"corpus over the {digests.MAX_FILES} file ceiling")
    if not found:
        raise BereanError(f"corpus tree is empty: {root}")
    return sorted(found)


def build(root, corpus_version):
    """Pin a tree into a corpus manifest document."""
    entries = []
    for relative in _walk(root):
        paths.usable(relative, "corpus path")
        full = paths.resolve(root, relative, "corpus path")
        data = digests.read_file(full)
        entries.append({"path": relative, "bytes": len(data), "sha256": digests.of_bytes(data)})
    document = {
        "format": FORMAT,
        "corpus_version": jsonio.stated(corpus_version, "corpus_version"),
        "files": entries,
        "corpus_digest": digests.of_listing((e["path"], e["sha256"]) for e in entries),
    }
    validate(document)
    return document


def validate(document):
    """Hold a corpus manifest to its closed field table."""
    jsonio.require(document, FIELDS, "corpus manifest")
    if document["format"] != FORMAT:
        raise BereanError(f"corpus manifest format is {document['format']!r}, not {FORMAT!r}")
    jsonio.stated(document["corpus_version"], "corpus_version")
    files = document["files"]
    if not isinstance(files, list) or not files:
        raise BereanError("corpus manifest carries no files")
    seen = set()
    for entry in files:
        jsonio.require(entry, FILE_FIELDS, "corpus file entry")
        paths.usable(entry["path"], "corpus path")
        jsonio.whole_number(entry["bytes"], f"bytes for {entry['path']}")
        digests.check_hex(entry["sha256"], f"digest for {entry['path']}")
        if entry["path"] in seen:
            raise BereanError(f"corpus path pinned twice: {entry['path']}")
        seen.add(entry["path"])
    listed = [entry["path"] for entry in files]
    if listed != sorted(listed):
        raise BereanError("corpus files are not in sorted order")
    expected = digests.of_listing((e["path"], e["sha256"]) for e in files)
    if document["corpus_digest"] != expected:
        raise BereanError("corpus_digest does not match the file listing")
    return document


def write(document, out):
    validate(document)
    jsonio.write_canonical(out, document, canonical.dumps)


def verify(document, root):
    """Re-read the tree and report named checks; no repair, no subsets."""
    checks = []
    try:
        validate(document)
        checks.append(Check("manifest-shape", True))
    except BereanError as error:
        return [Check("manifest-shape", False, str(error))]

    try:
        on_disk = set(_walk(root))
    except BereanError as error:
        return checks + [Check("corpus-tree", False, str(error))]
    checks.append(Check("corpus-tree", True))

    pinned = {entry["path"]: entry for entry in document["files"]}
    missing = sorted(set(pinned) - on_disk)
    extra = sorted(on_disk - set(pinned))
    if missing:
        checks.append(Check("corpus-complete", False, f"pinned but absent: {', '.join(missing)}"))
    elif extra:
        checks.append(Check("corpus-complete", False, f"present but unpinned: {', '.join(extra)}"))
    else:
        checks.append(Check("corpus-complete", True))

    drifted = []
    for relative in sorted(set(pinned) & on_disk):
        entry = pinned[relative]
        try:
            data = digests.read_file(paths.resolve(root, relative, "corpus path"))
        except BereanError as error:
            drifted.append(f"{relative} ({error})")
            continue
        if len(data) != entry["bytes"] or digests.of_bytes(data) != entry["sha256"]:
            drifted.append(relative)
    if drifted:
        checks.append(Check("corpus-bytes", False, f"drifted: {', '.join(drifted)}"))
    else:
        checks.append(Check("corpus-bytes", True))
    return checks
