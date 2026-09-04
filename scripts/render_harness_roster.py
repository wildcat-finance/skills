#!/usr/bin/env python3
"""Write the roster's three wording surfaces from one probed manifest.

`docs/harness-classification.json` is the roster's single source, written by
`scripts/probe_harnesses.py` and pinned by
`docs/decisions/ADR-077-generate-the-harness-roster-from-one-probed-manifest.md`.
This module is the renderer. It turns that manifest into the three surfaces the
decision record names: the roster block in `README.md`, the harness table in
`docs/how-to-help-shoggoth.md`, and the harness page
`scripts/build_contributor_guide.py` draws into
`docs/pdf/how-to-help-shoggoth.pdf`.

Three properties are load-bearing, and each has a case in
`tests/test_harness_manifest.py` that fails without it.

**The surfaces are derived, never authored.** Every harness name, class and
blocker in a surface comes out of the manifest. The two Markdown surfaces carry
their generated text between `<!-- harness-roster:begin -->` and
`<!-- harness-roster:end -->`, and nothing outside those markers names a
harness. The builder holds no harness name at all: it calls the four
`pdf_*` functions below at draw time, so the PDF cannot drift from the manifest
without the manifest moving first.

**Rendering is deterministic.** Nothing here reads a clock, a random source, an
environment variable or the surfaces it is about to overwrite. Two renders of
one manifest produce identical bytes, which is what makes `--check` a drift
test rather than a diff of two build times.

**The PDF is compared as text, not as bytes.** A PDF carries a creation
timestamp, so two builds of the same page never match byte for byte.
`harness_page_text` decompresses the page's own content stream and reads the
strings it shows, so `--check` answers whether the page says what the manifest
says and stays silent about when it was built.

`--check` needs no PDF library: it reads the finished file with `zlib` from the
standard library. `--write` rebuilds the PDF by running
`scripts/build_contributor_guide.py`, which does need `reportlab`, and reports
the failure rather than leaving a stale page behind.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PROBE_PATH = ROOT / "scripts/probe_harnesses.py"
BUILDER_PATH = ROOT / "scripts/build_contributor_guide.py"
MANIFEST_PATH = ROOT / "docs/harness-classification.json"
README_PATH = ROOT / "README.md"
GUIDE_PATH = ROOT / "docs/how-to-help-shoggoth.md"
PDF_PATH = ROOT / "docs/pdf/how-to-help-shoggoth.pdf"

BEGIN_MARKER = "<!-- harness-roster:begin -->"
END_MARKER = "<!-- harness-roster:end -->"

MANUAL_ROUTE = "manual route"
UNSUPPORTED = "unsupported"

# The heading the harness page draws, and the only page whose text this module
# reads. A PDF that does not carry it is not the guide.
PDF_PAGE_MARKER = "THE ATLAS AND FIAT ROUTE"

MAX_PDF_BYTES = 64 * 1024 * 1024
MAX_SURFACE_BYTES = 4 * 1024 * 1024
MAX_STREAM_BYTES = 32 * 1024 * 1024

PDF_STREAM = re.compile(rb"stream\r?\n")
PDF_STRING = re.compile(rb"\((?:\\.|[^\\()])*\)", re.DOTALL)
PDF_ESCAPE = re.compile(rb"\\([nrtbf()\\]|[0-7]{1,3})")
PDF_ESCAPES = {
    b"n": b"\n",
    b"r": b"\r",
    b"t": b"\t",
    b"b": b"\b",
    b"f": b"\f",
    b"(": b"(",
    b")": b")",
    b"\\": b"\\",
}

PDF_DETAIL = "Read AGENTS.md, then paste job.prompt. No checked Atlas launcher here."


class RenderError(Exception):
    """A surface could not be read, derived or written."""


def _probe():
    """`scripts/probe_harnesses.py`, loaded once by path.

    The manifest reader lives there, and reusing it keeps one refusal contract
    for a torn, oversized or foreign document rather than growing a second.
    """
    existing = sys.modules.get("probe_harnesses")
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location("probe_harnesses", PROBE_PATH)
    if spec is None or spec.loader is None:
        raise RenderError(f"{PROBE_PATH} could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_manifest(path=None):
    """The manifest as a document, or a `RenderError` naming why not."""
    probe = _probe()
    try:
        return probe.read_manifest(MANIFEST_PATH if path is None else path)
    except probe.ProbeError as error:
        raise RenderError(f"manifest refused: {error}") from error


def harnesses(document):
    """Every entry in the manifest's own order."""
    return tuple(document["harnesses"])


def names_in_class(document, classification):
    """The harnesses carrying one class, in manifest order."""
    return tuple(
        entry["name"]
        for entry in harnesses(document)
        if entry["classification"] == classification
    )


def recorded(document):
    """The host, date and base ref this manifest was written against."""
    block = document["recorded"]
    return block["host"], block["date"], block["base_ref"]


def _version(entry):
    """What to print for a version, without recognising the unread sentinel.

    `version_read` is the field ADR-077 tells a reader to consult, so this reads
    that boolean rather than comparing `client_version` against a magic string.
    """
    return entry["client_version"] if entry["version_read"] else "not read"


def _yes_no(value):
    return "yes" if value else "no"


def _provenance(document, surface):
    host, date, base_ref = recorded(document)
    return (
        f"<!-- Generated by scripts/render_harness_roster.py from "
        f"docs/harness-classification.json, recorded on {host} on {date} against "
        f"{base_ref}. Change the roster in scripts/probe_harnesses.py, re-run the "
        f"probe, then re-run the renderer. Nothing between these markers is "
        f"edited by hand, and {surface} carries no harness name outside them. -->"
    )


def readme_block(document):
    """The generated body of the README roster block."""
    host, date, _ = recorded(document)
    manual = names_in_class(document, MANUAL_ROUTE)
    unsupported = names_in_class(document, UNSUPPORTED)
    lines = [
        _provenance(document, "the README"),
        "",
        "No local harness holds a checked one-click Atlas launcher. A probe on "
        f"{host} read every client below on {date}, and the roster states what it "
        "found rather than what anybody hoped for:",
        "",
    ]
    if manual:
        lines.append(f"- Manual route: {', '.join(manual)}.")
    if unsupported:
        lines.append(f"- Unsupported: {', '.join(unsupported)}.")
    lines.extend([
        "",
        "Each harness carries the exact reason it stopped there in "
        "[the harness table](./docs/how-to-help-shoggoth.md#local-harnesses) and "
        "in [`docs/harness-classification.json`](./docs/harness-classification.json), "
        "which both surfaces are generated from.",
    ])
    return "\n".join(lines)


def guide_block(document):
    """The generated body of the guide's harness table."""
    host, date, base_ref = recorded(document)
    lines = [
        _provenance(document, "the guide"),
        "",
        "| Harness | Class | Client found here | Version | Authenticated here |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in harnesses(document):
        lines.append(
            f"| {entry['name']} | {entry['classification']} | "
            f"{_yes_no(entry['client_present'])} | {_version(entry)} | "
            f"{_yes_no(entry['auth_configured'])} |"
        )
    lines.extend([
        "",
        f"Recorded on {host} on {date}, against `{base_ref}`. A row cannot reach "
        "`Atlas launcher` or `tested local route` without a client run somebody "
        "got an answer from, so every row below carries the exact reason it "
        "stopped where it did:",
        "",
    ])
    for entry in harnesses(document):
        blocker = entry["blocker"]
        lines.append(f"- **{entry['name']}** -- {blocker if blocker else 'nothing blocked it.'}")
    return "\n".join(lines)


def pdf_label(document):
    """The harness page's roster card label, before the page uppercases it."""
    host, date, _ = recorded(document)
    return f"Manual only - probed {host}, {date}"


def pdf_roster_line(document):
    """The harness page's roster line."""
    return "  /  ".join(names_in_class(document, MANUAL_ROUTE))


def pdf_detail(document):
    """The harness page's roster card detail."""
    unsupported = names_in_class(document, UNSUPPORTED)
    if not unsupported:
        return PDF_DETAIL
    return f"{PDF_DETAIL} Unsupported: {', '.join(unsupported)}."


def pdf_expectations(document):
    """Every string the harness page has to show, in the order it shows them."""
    return (
        pdf_label(document).upper(),
        pdf_roster_line(document),
        pdf_detail(document),
    )


def _normalise(text):
    """One space between words, so a wrapped line reads as the sentence it is."""
    return " ".join(text.split())


def _unescape(raw):
    def replace(match):
        body = match.group(1)
        if body in PDF_ESCAPES:
            return PDF_ESCAPES[body]
        return bytes([int(body, 8) & 0xFF])

    return PDF_ESCAPE.sub(replace, raw)


def harness_page_text(path=None):
    """The harness page's shown text, normalised to one space between words.

    Only this page's own content stream is read, so a creation timestamp, an
    embedded image or another page cannot decide the comparison. A PDF with no
    harness page is a refusal rather than an empty string, because an empty
    string would let a check pass against a file that never carried the roster.
    """
    target = Path(PDF_PATH if path is None else path)
    try:
        size = target.stat().st_size
    except OSError as error:
        raise RenderError(f"pdf cannot be inspected ({type(error).__name__})") from error
    if size > MAX_PDF_BYTES:
        raise RenderError(f"pdf is {size} bytes, over the {MAX_PDF_BYTES} cap")
    try:
        data = target.read_bytes()
    except OSError as error:
        raise RenderError(f"pdf cannot be read ({type(error).__name__})") from error

    marker = PDF_PAGE_MARKER.encode("ascii")
    for match in PDF_STREAM.finditer(data):
        start = match.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        try:
            page = zlib.decompress(data[start:end])
        except zlib.error:
            continue
        if len(page) > MAX_STREAM_BYTES or marker not in page:
            continue
        shown = [_unescape(found.group(0)[1:-1]) for found in PDF_STRING.finditer(page)]
        return _normalise(b" ".join(shown).decode("latin-1"))
    raise RenderError(f"{target} carries no page showing {PDF_PAGE_MARKER!r}")


def _read_surface(path):
    target = Path(path)
    try:
        size = target.stat().st_size
    except OSError as error:
        raise RenderError(f"{target} cannot be inspected ({type(error).__name__})") from error
    if size > MAX_SURFACE_BYTES:
        raise RenderError(f"{target} is {size} bytes, over the {MAX_SURFACE_BYTES} cap")
    try:
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise RenderError(f"{target} cannot be read ({type(error).__name__})") from error


def split_surface(text, path):
    """The text before the markers, the generated body, and the text after.

    Exactly one marked region is admitted. Two regions would leave the renderer
    choosing which one to believe, and none means the surface was never bound.
    """
    starts = list(_positions(text, BEGIN_MARKER))
    ends = list(_positions(text, END_MARKER))
    if len(starts) != 1 or len(ends) != 1:
        raise RenderError(
            f"{path} carries {len(starts)} begin and {len(ends)} end markers; "
            "exactly one of each is required"
        )
    start, end = starts[0], ends[0]
    if end < start:
        raise RenderError(f"{path} closes the roster region before it opens it")
    head = text[: start + len(BEGIN_MARKER)]
    body = text[start + len(BEGIN_MARKER) : end]
    tail = text[end:]
    return head, body, tail


def _positions(text, marker):
    index = text.find(marker)
    while index >= 0:
        yield index
        index = text.find(marker, index + 1)


def rendered_surface(text, body, path):
    """The whole surface file as it should read, with the body regenerated."""
    head, _, tail = split_surface(text, path)
    return f"{head}\n{body}\n{tail}"


def build_pdf(builder=None, target=None, python=None):
    """Rebuild the guide PDF by running its builder as a fixed argv."""
    argv = [
        sys.executable if python is None else str(python),
        str(BUILDER_PATH if builder is None else builder),
        "--output",
        str(PDF_PATH if target is None else target),
    ]
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RenderError(f"the guide builder could not be run ({type(error).__name__})") from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        reason = detail[-1] if detail else f"exit {completed.returncode}"
        raise RenderError(f"the guide builder exited {completed.returncode}: {reason}")
    return argv


def write(
    *,
    manifest=None,
    readme=None,
    guide=None,
    pdf=None,
    builder=None,
    python=None,
):
    """Regenerate all three surfaces, and report every path written.

    The PDF is always rebuilt and so is always written. The two Markdown
    surfaces are written only where the rendered text differs from what is
    already there, so a no-op render leaves their modification times alone.
    """
    document = load_manifest(manifest)
    written = []
    for path, body in (
        (README_PATH if readme is None else Path(readme), readme_block(document)),
        (GUIDE_PATH if guide is None else Path(guide), guide_block(document)),
    ):
        text = _read_surface(path)
        rendered = rendered_surface(text, body, path)
        if rendered != text:
            path.write_text(rendered, encoding="utf-8")
            written.append(path)
    build_pdf(builder=builder, target=pdf, python=python)
    written.append(PDF_PATH if pdf is None else Path(pdf))
    return document, written


def check(*, manifest=None, readme=None, guide=None, pdf=None):
    """Every surface that has drifted from the manifest, as readable lines."""
    document = load_manifest(manifest)
    drift = []
    for path, body in (
        (README_PATH if readme is None else Path(readme), readme_block(document)),
        (GUIDE_PATH if guide is None else Path(guide), guide_block(document)),
    ):
        try:
            text = _read_surface(path)
            if rendered_surface(text, body, path) != text:
                drift.append(f"{path}: the roster region does not match the manifest")
        except RenderError as error:
            drift.append(f"{path}: {error}")
    try:
        shown = harness_page_text(pdf)
        for expected in pdf_expectations(document):
            if _normalise(expected) not in shown:
                drift.append(
                    f"{PDF_PATH if pdf is None else Path(pdf)}: the harness page does "
                    f"not show {expected!r}"
                )
    except RenderError as error:
        drift.append(f"{PDF_PATH if pdf is None else Path(pdf)}: {error}")
    return document, drift


def build_parser():
    parser = argparse.ArgumentParser(description="Render the harness roster's three surfaces.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift and exit non-zero instead of writing anything",
    )
    parser.add_argument("--manifest", metavar="PATH", help="the manifest to render from")
    parser.add_argument("--readme", metavar="PATH", help="the README surface")
    parser.add_argument("--guide", metavar="PATH", help="the contributor guide surface")
    parser.add_argument("--pdf", metavar="PATH", help="the guide PDF")
    parser.add_argument(
        "--python",
        metavar="PATH",
        help="the interpreter that runs the PDF builder, when writing",
    )
    return parser


def main(argv=None):
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.check:
            document, drift = check(
                manifest=arguments.manifest,
                readme=arguments.readme,
                guide=arguments.guide,
                pdf=arguments.pdf,
            )
            for line in drift:
                print(f"render_harness_roster: {line}", file=sys.stderr)
            if drift:
                print(
                    f"render_harness_roster: {len(drift)} surface(s) drifted from the manifest",
                    file=sys.stderr,
                )
                return 1
            print(f"three surfaces match {len(harnesses(document))} recorded harnesses")
            return 0
        document, changed = write(
            manifest=arguments.manifest,
            readme=arguments.readme,
            guide=arguments.guide,
            pdf=arguments.pdf,
            python=arguments.python,
        )
    except RenderError as error:
        print(f"render_harness_roster: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"render_harness_roster: {type(error).__name__} writing a surface", file=sys.stderr)
        return 1
    for path in changed:
        print(f"wrote {path}")
    print(f"rendered {len(harnesses(document))} harnesses into three surfaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
