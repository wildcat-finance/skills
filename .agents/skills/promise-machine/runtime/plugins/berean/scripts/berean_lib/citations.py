"""Citations: exact bytes in a pinned corpus, or nothing.

A citation names a pinned document, a byte range, the range's digest and
its display text. It passes only when the pinned file still matches the
corpus manifest, the slice reproduces the digest, and the slice decodes to
exactly the display text. Digest and text are both checked because either
alone can lie: a digest with no text pins bytes nobody can read back, and
text with no digest is a claim about bytes nobody sliced.
"""

from . import BereanError
from . import digests
from . import jsonio
from . import paths
from .corpus import Check

FORMAT = "berean-citation/v1"
FIELDS = ("format", "doc", "byte_start", "byte_end", "sha256", "display_text")


def validate(citation):
    jsonio.require(citation, FIELDS, "citation")
    if citation["format"] != FORMAT:
        raise BereanError(f"citation format is {citation['format']!r}, not {FORMAT!r}")
    paths.usable(citation["doc"], "citation doc")
    start = jsonio.whole_number(citation["byte_start"], "byte_start")
    end = jsonio.whole_number(citation["byte_end"], "byte_end")
    if end <= start:
        raise BereanError(f"empty or inverted byte range: {start}..{end}")
    digests.check_hex(citation["sha256"], "citation digest")
    if not isinstance(citation["display_text"], str) or not citation["display_text"]:
        raise BereanError("display_text is blank or not a string")
    return citation


def check(citation, manifest, root):
    """Prove or refuse one citation against a pinned corpus; named checks out."""
    checks = []
    try:
        validate(citation)
        checks.append(Check("citation-shape", True))
    except BereanError as error:
        return [Check("citation-shape", False, str(error))]

    pinned = {entry["path"]: entry for entry in manifest["files"]}
    entry = pinned.get(citation["doc"])
    if entry is None:
        return checks + [Check("citation-doc", False, f"not in the corpus: {citation['doc']}")]
    checks.append(Check("citation-doc", True))

    try:
        data = digests.read_file(paths.resolve(root, citation["doc"], "citation doc"))
    except BereanError as error:
        return checks + [Check("citation-pin", False, str(error))]
    if len(data) != entry["bytes"] or digests.of_bytes(data) != entry["sha256"]:
        return checks + [
            Check("citation-pin", False, f"{citation['doc']} no longer matches the corpus manifest")
        ]
    checks.append(Check("citation-pin", True))

    start, end = citation["byte_start"], citation["byte_end"]
    if end > len(data):
        return checks + [Check("citation-range", False, f"range {start}..{end} leaves the {len(data)} byte file")]
    checks.append(Check("citation-range", True))

    piece = data[start:end]
    if digests.of_bytes(piece) != citation["sha256"]:
        checks.append(Check("citation-bytes", False, "the slice does not reproduce the cited digest"))
        return checks
    checks.append(Check("citation-bytes", True))

    try:
        text = piece.decode("utf-8")
    except UnicodeDecodeError:
        checks.append(Check("citation-text", False, "the slice is not whole UTF-8; the range splits a character"))
        return checks
    if text != citation["display_text"]:
        checks.append(Check("citation-text", False, "display_text is not the decoded slice"))
    else:
        checks.append(Check("citation-text", True))
    return checks
