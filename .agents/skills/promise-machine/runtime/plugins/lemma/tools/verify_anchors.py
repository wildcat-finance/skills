#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""
Lemma anchor verifier

Checks that the anchor algorithm in markdown.py still reproduces every heading
id the live documentation site serves. The algorithm is *fitted* to GitBook's
renderer, not derived from a spec, so a
platform change can invalidate it silently. This is the check to run when that
is suspected, and before shipping any change to `gitbook_id()`.

    python3 tools/verify_anchors.py --root docs \
        --site https://docs.example.com

For each page listed in `SUMMARY.md`, fetch the rendered HTML, extract heading
ids, and scan the local Markdown through the production code path:
`scan_structure`, `heading_text`, `gitbook_id`, and the duplicate counter used by
`chunk_file`. Pair the two lists positionally.

Pages where the heading *count* differs have drifted from the pinned sources
(the live site tracks main); they are reported and skipped, because a drifted
page verifies nothing either way. Pages where counts match but ids differ are
algorithm failures. Exit code is the number of those.

Network access required, obviously. This is a manual verification tool, not a
build step.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location(
    "md", ROOT / "chunkers" / "markdown.py")
md = importlib.util.module_from_spec(_spec)
sys.modules["md"] = md
_spec.loader.exec_module(md)

HTML_HEADING = re.compile(r'<h([1-6])\s+id="([^"]+)"')


def summary_pages(root: pathlib.Path) -> list[tuple[str, str]]:
    """(relative md path, site url path) for every SUMMARY entry."""
    pages = []
    for line in (root / "SUMMARY.md").read_text(encoding="utf-8").split("\n"):
        m = md.SUMMARY_ENTRY.match(line)
        if not m or not m.group(3).endswith(".md"):
            continue
        rel = m.group(3)
        url = rel[:-3]
        if url.endswith("README"):
            url = url[:-7]
        pages.append((rel, url.strip("/")))
    return pages


def local_ids(root: pathlib.Path, rel: str) -> list[str]:
    """Return anchor ids through the production code path used by chunk_file."""
    blob = (root / rel).read_bytes()
    _, body = md.split_frontmatter(blob)
    headings, _ = md.scan_structure(blob, body)
    anchor_of = md.assign_anchors(headings)
    return [anchor_of[off] for off, _, _ in headings
            if anchor_of[off] is not None]


def live_ids(site: str, url: str) -> list[str] | None:
    # The site 403s urllib's default User-Agent; identify as this tool.
    req = urllib.request.Request(
        f"{site}/{url}".rstrip("/"),
        headers={"User-Agent": "lemma-verify-anchors/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"  fetch failed: {url} ({e})", file=sys.stderr)
        return None
    return [i for _, i in HTML_HEADING.findall(html)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="pinned docs checkout")
    ap.add_argument("--site", required=True,
                    help="rendered site to check anchors against")
    args = ap.parse_args()
    root = pathlib.Path(args.root)

    verified = drifted = unfetched = failures = 0
    for rel, url in summary_pages(root):
        want = live_ids(args.site, url)
        if want is None:
            unfetched += 1
            continue
        got = local_ids(root, rel)
        if len(want) != len(got):
            drifted += 1
            print(f"  drift  {rel}: live serves {len(want)} heading id(s), "
                  f"pinned source has {len(got)} — page has moved on")
            continue
        bad = [(w, g) for w, g in zip(want, got) if w != g]
        for w, g in bad:
            print(f"  FAIL   {rel}: live {w!r} vs derived {g!r}")
        failures += len(bad)
        verified += len(want) - len(bad)

    print(f"\n{verified} anchor(s) verified against {args.site}, "
          f"{failures} mismatch(es), {drifted} drifted page(s) skipped, "
          f"{unfetched} unfetched")
    if failures:
        print("the algorithm no longer matches the renderer — re-fit before "
              "trusting any citation fragment", file=sys.stderr)
    return failures


if __name__ == "__main__":
    sys.exit(main())
