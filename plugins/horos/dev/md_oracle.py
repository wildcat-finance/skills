"""Dev-time oracle and differential driver for the Horos Markdown
outliner. Never imported or executed by the shipped plugin or its test
suite: the differential corpus run drives it by hand inside a scratchpad
virtualenv holding markdown-it-py 4.2.0 in its `commonmark` preset, and
only the recorded results are committed.

Usage, from the target repository root, under the virtualenv's interpreter:

    <venv-python> plugins/horos/dev/md_oracle.py --commit <sha> \
        --out plugins/horos/docs/evidence/skills-markdown-outline.results.json

The corpus is `git ls-files '*.md'` at that commit, read from the working
tree; the run refuses to start when the tree's head is not that commit.
`--oracle <path>` additionally writes the raw per-file oracle reading.

Declared altitudes, what the run compares and nothing else:

- Headings by `(level, line)`, at every container depth, ATX and setext
  alike. The heading's text is not compared: the outliner slices the
  verbatim line and markdown-it reports parsed inline content.
- Fenced code blocks by `(first line, last line)`. The info string is not
  compared, for the same reason.

Everything else either side sees is outside the comparison: inline
structure, link reference definitions, indented code, thematic breaks,
paragraphs, lists and tables.

Two exclusions, declared on both sides:

- Front matter. A `---` line at line 1 through the next `---` or `...`
  line is stripped before markdown-it parses, and the remaining line
  numbers are shifted back by the stripped count, because CommonMark has no
  front matter and would read `title: x` under `---` as a setext heading.
  The outliner names the same block by line range and outlines nothing
  inside it, so the block is outlined on one side and compared on neither.
- An unterminated fence. markdown-it reads a fence that never closes as a
  fence running to the end of the file; the outliner refuses to invent the
  closing line, confesses the remainder as an unparsed region and exits 1.
  Such a fence is therefore recorded as `fence_missed_confessed`, never as
  a match and never as a miss.

A miss whose line falls inside a confessed region is `missed_confessed`,
counted and reported separately: the outliner said it had not read there.
A miss outside every confessed region is a silent miss and fails the
acceptance. A crash on any file fails it too.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "plugins/horos/skills/horos/scripts"))

from languages.markdown import markdown as shipped  # noqa: E402

PARSER = MarkdownIt("commonmark")


def split_front_matter(text):
    """Return (stripped line count, body). Mirrors the outliner's rule."""
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        return 0, text
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r") in ("---", "..."):
            return i + 1, "\n".join(lines[i + 1:])
    return 0, text


def oracle_reading(text):
    """markdown-it's headings and fences at the declared altitudes."""
    skipped, body = split_front_matter(text)
    headings = []
    fences = []
    for token in PARSER.parse(body):
        if token.type == "heading_open":
            headings.append([int(token.tag[1]), token.map[0] + 1 + skipped])
        elif token.type == "fence":
            fences.append([token.map[0] + 1 + skipped, token.map[1] + skipped])
    return {"front_matter_lines": skipped, "headings": headings, "fences": fences}


def corpus(commit):
    listing = subprocess.run(
        ["git", "ls-files", "--with-tree", commit, "*.md"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
    return [line for line in listing.splitlines() if line]


def compare(reading, heads, fences, regions):
    inside = lambda line: any(a <= line <= b for a, b in regions)  # noqa: E731
    oracle_heads = {tuple(h) for h in reading["headings"]}
    ours_heads = {tuple(h) for h in heads}
    oracle_fences = {tuple(f) for f in reading["fences"]}
    ours_fences = {tuple(f) for f in fences}
    missed = oracle_heads - ours_heads
    confessed = {h for h in missed if inside(h[1])}
    fence_missed = oracle_fences - ours_fences
    fence_confessed = {f for f in fence_missed if inside(f[0]) or inside(f[1])}
    return {
        "oracle": len(oracle_heads),
        "ours": len(ours_heads),
        "matched": len(oracle_heads & ours_heads),
        "missed": len(missed - confessed),
        "missed_confessed": len(confessed),
        "extra": len(ours_heads - oracle_heads),
        "fence_oracle": len(oracle_fences),
        "fence_ours": len(ours_fences),
        "fence_matched": len(oracle_fences & ours_fences),
        "fence_missed": len(fence_missed - fence_confessed),
        "fence_missed_confessed": len(fence_confessed),
        "fence_extra": len(ours_fences - oracle_fences),
        "regions": len(regions),
    }


SUMMED = (
    "oracle", "matched", "missed", "missed_confessed", "extra",
    "fence_oracle", "fence_matched", "fence_missed", "fence_missed_confessed",
    "fence_extra", "regions",
)


CLEAN_NOTE = (
    "A path under `clean` matched the oracle exactly at the declared altitudes: no miss, "
    "no extra, no confessed region and no crash. Its value is [headings, fenced blocks], "
    "the count the oracle found and the outliner matched, so `totals` remains the sum over "
    "`files` and `clean`. Only a file with something to report keeps a row in `files`."
)


def is_clean(row):
    """True when the row records a file the outliner read exactly as the oracle did.

    A clean row carries no information the totals do not already hold, and there
    are hundreds of them in a corpus this size, so the document keeps the file's
    two counts instead of its thirteen zeroes and matches.
    """
    if "crash" in row:
        return False
    return (
        row["missed"] == 0
        and row["missed_confessed"] == 0
        and row["extra"] == 0
        and row["regions"] == 0
        and row["matched"] == row["oracle"] == row["ours"]
        and row["fence_missed"] == 0
        and row["fence_missed_confessed"] == 0
        and row["fence_extra"] == 0
        and row["fence_matched"] == row["fence_oracle"] == row["fence_ours"]
    )


def results_document(totals, per_file):
    """The committed results file: totals, the rows worth reading, and the rest by count."""
    keep, clean = {}, {}
    for path, row in per_file.items():
        if is_clean(row):
            clean[path] = [row["oracle"], row["fence_oracle"]]
        else:
            keep[path] = row
    document = {"totals": totals, "files": keep, "clean": clean, "note": CLEAN_NOTE}
    text = json.dumps(document, indent=1, sort_keys=True) + "\n"
    # One line per clean path. The pair is the whole value, and three lines to
    # carry two integers is what this document is being trimmed out of.
    return re.sub(r"\[\s*\n\s*(\d+),\s*\n\s*(\d+)\s*\n\s*\]", r"[\1, \2]", text)


def run(commit, out_path, oracle_path):
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if head != commit:
        raise SystemExit(f"tree is at {head}, not the named commit {commit}")
    paths = corpus(commit)
    totals = {key: 0 for key in SUMMED}
    totals.update(files=0, bytes=0, crashes=0, files_with_regions=0)
    per_file = {}
    readings = {}
    mismatched = []
    started = time.perf_counter()
    for path in paths:
        raw = (ROOT / path).read_bytes()
        source = raw.decode("utf-8", errors="replace")
        reading = oracle_reading(source)
        if oracle_path:
            readings[path] = reading
        totals["files"] += 1
        totals["bytes"] += len(raw)
        try:
            heads, fences, regions, _ = shipped.declarations(source)
        except Exception as error:  # noqa: BLE001
            totals["crashes"] += 1
            per_file[path] = {"crash": repr(error)}
            print(f"CRASH {path}: {error!r}", file=sys.stderr)
            continue
        row = compare(reading, heads, fences, regions)
        per_file[path] = row
        for key in SUMMED:
            totals[key] += row[key]
        if row["regions"]:
            totals["files_with_regions"] += 1
        if row["missed"] or row["extra"] or row["fence_missed"] or row["fence_extra"]:
            mismatched.append((path, row))
    totals["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    Path(out_path).write_text(results_document(totals, per_file))
    if oracle_path:
        Path(oracle_path).write_text(json.dumps(readings, sort_keys=True))
    print(json.dumps(totals, indent=1, sort_keys=True))
    for path, row in mismatched[:25]:
        print(f"MISMATCH {path}: {row}", file=sys.stderr)
    print(f"mismatching files: {len(mismatched)}", file=sys.stderr)
    return 1 if (mismatched or totals["crashes"]) else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Markdown outline differential")
    parser.add_argument("--commit", required=True, help="the commit the corpus is read at")
    parser.add_argument("--out", required=True, help="results document to write")
    parser.add_argument("--oracle", default=None, help="optional raw oracle reading")
    args = parser.parse_args(argv)
    return run(args.commit, args.out, args.oracle)


if __name__ == "__main__":
    sys.exit(main())
