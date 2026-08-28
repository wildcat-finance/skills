#!/usr/bin/env python3
"""Hook entry point for the imprimatur lexicon.

Reads a Claude Code hook payload on stdin, runs the hard pass over whatever
prose the payload carries, and blocks when a banned term appears.

Only the hard pass runs here. Gated terms need the sentence read for a
referent, and structural patterns need judgement about whether the formula is
doing something the author intended. Blocking on those from a hook produces
false positives, and a hook that cries wolf gets switched off inside a week.

Exit codes follow the hook contract:
  0  allow
  2  block, stderr goes back to the model as the reason
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from imprimatur import build, strip_code_blocks  # noqa: E402

# Extensions worth gating. Source files are prose-free by definition; comments
# in them are not worth a false positive.
PROSE_EXT = {".md", ".mdx", ".txt", ".rst", ".adoc", ".tex", ".org"}

# Escape hatch for quoting slop in order to discuss it.
RE_ALLOW_BLOCK = re.compile(r"<!--\s*imprimatur:off\s*-->.*?<!--\s*imprimatur:on\s*-->", re.S | re.I)
RE_ALLOW_FILE = re.compile(r"<!--\s*imprimatur:ignore-file\s*-->", re.I)


def extract(payload: dict, stage: str) -> tuple[str, str]:
    """Return (label, text) for whatever this payload wants checked."""
    if stage == "pre-write":
        ti = payload.get("tool_input", {})
        if not isinstance(ti, dict):
            ti = {}
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        if path and Path(path).suffix.lower() not in PROSE_EXT:
            return path, ""
        parts = []
        for key in ("content", "new_string", "new_source"):
            if ti.get(key) is not None and ti.get(key) != "":
                parts.append(str(ti[key]))
        for edit in ti.get("edits", []) or []:
            if isinstance(edit, dict) and edit.get("new_string"):
                parts.append(str(edit["new_string"]))
        return path or "<write>", "\n".join(parts)

    for key in ("last_assistant_message", "assistant_message", "message", "transcript_tail"):
        if payload.get(key):
            return "<reply>", str(payload[key])
    return "<reply>", ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="pre-write", choices=["pre-write", "stop"])
    ap.add_argument("--warn-only", action="store_true", help="report without blocking")
    args = ap.parse_args()

    if os.environ.get("IMPRIMATUR_DISABLE"):
        return 0

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # never break the session over a malformed payload
    if not isinstance(payload, dict):
        return 0

    try:
        label, text = extract(payload, args.stage)
    except Exception:
        return 0  # same rule: an unexpected shape is not worth a broken session
    if not text.strip():
        return 0

    if RE_ALLOW_FILE.search(text):
        return 0
    text = RE_ALLOW_BLOCK.sub(" ", text)
    text = strip_code_blocks(text)

    report = build(text, hard_only=True, skip_code=False)
    if not report["hits"]:
        return 0

    seen: dict[str, dict] = {}
    for h in report["hits"]:
        seen.setdefault(h["term"], h)
    ordered = sorted(seen.values(), key=lambda h: -{"critical": 3, "high": 2}.get(h["severity"], 1))

    lines = [f"imprimatur: {len(seen)} banned term(s) in {label}."]
    for h in ordered[:8]:
        lines.append(f"  {h['line']}:{h['col']} [{h['family']}] {h['term']!r}")
    if len(ordered) > 8:
        lines.append(f"  ... and {len(ordered) - 8} more")
    lines.append("")
    lines.append("Rewrite the offending spans. Do not swap in a synonym from the same")
    lines.append("family; the family is what is banned. Say the thing plainly instead.")
    lines.append("To quote slop deliberately, wrap it in <!-- imprimatur:off --> ... <!-- imprimatur:on -->.")

    sys.stderr.write("\n".join(lines) + "\n")
    return 0 if args.warn_only else 2


if __name__ == "__main__":
    raise SystemExit(main())
