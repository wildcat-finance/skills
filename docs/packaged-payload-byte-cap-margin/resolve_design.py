#!/usr/bin/env python3
"""Resolve one cell of the issue #1467 design matrix from a measurement.

Prints one `protasis-design-report/v1` object.  With `--out` it also writes
those exact bytes to the named path and to nothing else.  It writes no
controller state, and every scan it performs excludes the run's own
`.hexaemeron/` directory, because that directory is not repository content and
its contents change as the run proceeds.

Usage:
  resolve_design.py --candidate <id> --criterion <id> [--out <path>]

Candidates
  omission-class     the package omits the character-portrait class
  omission-class-with-reference-repair
                     the same omission, and the packaged copies of the
                     documents that referenced a portrait have that `<img>`
                     tag rewritten so nothing dangles
  second-package     the runtime is split into two published packages
  route-restriction  payload unchanged; `github` documented as the only route
  warning-gate       payload unchanged; the byte assertion moves off the cap

The repository root is the nearest ancestor directory holding
`scripts/portable_promise_machine.py`, so this file runs from any depth.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import sys
import tempfile

from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
ROOT = next(
    p for p in HERE.parents if (p / "scripts" / "portable_promise_machine.py").is_file()
)
GENERATOR = ROOT / "scripts" / "portable_promise_machine.py"
# The report's `command` names the path this file occupies, relative to the
# repository root, so a report written from the committed location does not
# claim the controller copy under `.hexaemeron/` ran. The same source placed
# at `.hexaemeron/` yields the exact string the 35 receipted reports carry.
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()
EXTRACT_CAP = 25 * 1024 * 1024

CANDIDATES = (
    "omission-class",
    "omission-class-with-reference-repair",
    "second-package",
    "route-restriction",
    "warning-gate",
)

# The candidates whose published file set drops the portrait class.  The
# repair candidate differs from `omission-class` only in the bytes of the
# documents that referenced one, never in which files ship.
OMITS_PORTRAITS = ("omission-class", "omission-class-with-reference-repair")

# The greedy longest-processing-time partition of the manifest's top-level
# groups, recomputed here rather than hard-coded, so the split a reader
# reproduces is the split that was measured.
CORE = "<core>"

LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")

# One `<img>` tag with a `src` attribute.  Written to span the whole tag
# rather than the attribute alone, because the repair replaces the tag.
IMAGE = re.compile(
    r"""<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["'][^>]*>""", re.IGNORECASE
)


def _is_portrait(path: str) -> bool:
    parts = PurePosixPath(path).parts
    if parts[:2] == ("assets", "characters"):
        return True
    return len(parts) >= 4 and parts[0] == "plugins" and parts[2:4] == ("assets", "characters")


def _group(path: str) -> str:
    parts = PurePosixPath(path).parts
    return "plugins/" + parts[1] if parts[0] == "plugins" and len(parts) > 1 else CORE


def _baseline_manifest():
    """Build one package into a temporary directory and return its manifest."""
    with tempfile.TemporaryDirectory(prefix="fiat-1467-baseline.") as raw:
        out = Path(raw) / "package"
        result = subprocess.run(  # phylax: allow subprocess: fixed local generator argv
            [sys.executable, str(GENERATOR), "package", "--out", str(out)],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise SystemExit(result.stdout + result.stderr)
        manifest = out / ".agents/skills/promise-machine/runtime/MANIFEST.json"
        payload = manifest.parent
        document = json.loads(manifest.read_text(encoding="utf-8"))
        texts = {
            row["path"]: (payload / row["path"]).read_bytes()
            for row in document["files"]
            if row["path"].endswith(".md")
        }
    return document, texts


def _partition(manifest):
    sizes, counts = {}, {}
    for row in manifest["files"]:
        key = _group(row["path"])
        sizes[key] = sizes.get(key, 0) + row["bytes"]
        counts[key] = counts.get(key, 0) + 1
    left, right = set(), set()
    left_bytes = right_bytes = 0
    for key in sorted(sizes, key=lambda name: (-sizes[name], name)):
        if left_bytes <= right_bytes:
            left.add(key)
            left_bytes += sizes[key]
        else:
            right.add(key)
            right_bytes += sizes[key]
    return left, right, left_bytes, right_bytes


def _image_target(document, src):
    """The package-relative path an `<img src>` names, or None if it is remote.

    A scheme-bearing, protocol-relative or `data:` source cannot dangle inside
    the package, so it is not the repair's subject and not counted against it.
    """
    link = src.split("#", 1)[0]
    if not link or "://" in link or link.startswith(("data:", "mailto:", "//")):
        return None
    base = posixpath.dirname(document)
    return posixpath.normpath(posixpath.join(base, link))


def _repair(document, text, present):
    """Rewrite only the `<img>` tags whose target left this published set.

    The replacement is an HTML comment naming the omitted path.  Three
    properties are wanted and each follows from that choice: the pass is
    idempotent, because the replacement contains no `<img`; it is
    deterministic, because it is a pure function of the document bytes and the
    published path set; and it changes nothing else, because only the matched
    tag span is replaced and every other byte is copied through.
    """
    def substitute(match):
        target = _image_target(document, match.group(1))
        if target is None or target in present:
            return match.group(0)
        return f"<!-- image omitted from the portable package: {target} -->"

    return IMAGE.sub(substitute, text)


def _packaged_text(candidate, document, text, present):
    """The bytes of one packaged Markdown document under this candidate."""
    if candidate == "omission-class-with-reference-repair":
        return _repair(document, text, present)
    return text


def _parts(candidate, manifest, texts):
    """Published parts as (path -> packaged bytes, path -> packaged text).

    One part per published package.  Byte counts are the packaged ones, so a
    candidate that rewrites a document is measured on what it would ship
    rather than on what the baseline holds.
    """
    paths = {row["path"]: row["bytes"] for row in manifest["files"]}
    if candidate in OMITS_PORTRAITS:
        sets = [{p for p in paths if not _is_portrait(p)}]
    elif candidate == "second-package":
        left, _right, _lb, _rb = _partition(manifest)
        sets = [
            {p for p in paths if _group(p) in left},
            {p for p in paths if _group(p) not in left},
        ]
    else:
        sets = [set(paths)]

    built = []
    for present in sets:
        part_texts = {}
        sizes = {}
        for path in present:
            if path in texts:
                data = _packaged_text(
                    candidate, path, texts[path].decode("utf-8"), present
                ).encode("utf-8")
                part_texts[path] = data
                sizes[path] = len(data)
            else:
                sizes[path] = paths[path]
        built.append((sizes, part_texts))
    return built


def _file_sets(candidate, manifest, texts):
    """Return the list of published file sets this candidate produces."""
    return [sizes for sizes, _part_texts in _parts(candidate, manifest, texts)]


def _dangling_images(candidate, manifest, texts):
    """`<img src>` references in packaged documents whose target is absent.

    Counted over every packaged Markdown document, not only the authoritative
    set the shipped link-closure test reads, because the operator's constraint
    is about what a reader of any packaged document sees.  Measured for every
    candidate from its own published bytes; no candidate is assigned zero by
    reasoning that it changes nothing.
    """
    total = 0
    for sizes, part_texts in _parts(candidate, manifest, texts):
        present = set(sizes)
        for document in sorted(part_texts):
            text = part_texts[document].decode("utf-8")
            for src in IMAGE.findall(text):
                target = _image_target(document, src)
                if target is not None and target not in present:
                    total += 1
    return total


def _authoritative(present):
    for path in sorted(present):
        parts = PurePosixPath(path).parts
        if path in ("AGENTS.md", ".agents/skills/promise-machine/SKILL.md"):
            yield path
        elif parts[-1] == "AGENTS.md" and len(parts) == 3 and parts[0] == "plugins":
            yield path
        elif parts[-1] == "SKILL.md" and parts[0] == "plugins":
            yield path


def _link_escapes(candidate, manifest, texts):
    """Count `[](...)` links leaving the package, by the shipped test's rule.

    `tests/test_skills_sh_package.py` resolves each link on disk and accepts
    anything that exists, so a link naming a directory is satisfied by any file
    beneath it.  That is reproduced here against the manifest's path set.
    """
    total = 0
    for present, part_texts in _parts(candidate, manifest, texts):
        directories = set()
        for path in present:
            parent = PurePosixPath(path).parent
            while str(parent) not in (".", "/"):
                directories.add(str(parent))
                parent = parent.parent
        for document in _authoritative(present):
            text = part_texts[document].decode("utf-8")
            base = str(PurePosixPath(document).parent)
            for raw in LINK.findall(text):
                link = raw.split("#", 1)[0]
                if not link or "://" in link or link.startswith("mailto:"):
                    continue
                if PurePosixPath(document).parent.name == "x-ray" and link == "invariants.md":
                    continue
                target = posixpath.normpath(posixpath.join(base, link))
                if target in present or target in directories:
                    continue
                total += 1
    return total


def _extract_margin(candidate, manifest, texts):
    largest = max(
        sum(part.values()) for part in _file_sets(candidate, manifest, texts)
    )
    return EXTRACT_CAP - largest


def _install_commands(candidate):
    return 2 if candidate == "second-package" else 1


def _publication_files_written(candidate, manifest, texts):
    """Files the hourly publication job writes on each rebuild.

    ADR-066 records that a scheduled job regenerates and republishes the whole
    package every hour, so the files it writes per run is what that job's time
    is spent on.  This is the deterministic driver, chosen over a wall clock: a
    median build time measured on one laptop put `route-restriction` at 855 ms
    and `warning-gate` at 769 ms, an 86 ms spread between two candidates whose
    build is byte-identical, so wall clock cannot separate them as evidence.

    Each published package writes its manifested files plus its own
    `MANIFEST.json`.
    """
    return sum(len(part) + 1 for part in _file_sets(candidate, manifest, texts))


def _foreign_repositories_touched(candidate):
    """Repositories other than `wildcat-finance/skills` the candidate changes.

    ADR-066 records that `wildcat-finance/skills-runtime` holds the published
    package, that its own token cannot update its workflow, and that the
    documented install command names one address.  A candidate that changes the
    published address or the destination job cannot be made or unmade by a
    commit here alone.  This value is read from the candidate definitions and
    that record, not from executing the candidate.
    """
    return 1 if candidate == "second-package" else 0


def _tracked_files_deleted(candidate):
    """Tracked repository files the candidate removes from the source tree.

    Issue #1467 refuses a change that deletes files to buy margin.  Every
    candidate carried here keeps the source tree whole: an omission class keeps
    its files tracked and omits them from the package, which is what all eight
    omission classes already in `scripts/portable_promise_machine.py` do.  The
    refused option would score 32 against this gate.  This value is read from
    the candidate definitions, not from executing the candidate.
    """
    return 0


MEASURES = {
    "tracked-files-deleted": ("count", lambda c, m, t: _tracked_files_deleted(c)),
    "authoritative-link-closure": ("count", lambda c, m, t: _link_escapes(c, m, t)),
    "extract-margin": ("bytes", lambda c, m, t: _extract_margin(c, m, t)),
    "install-commands": ("count", lambda c, m, t: _install_commands(c)),
    "publication-files-written": (
        "count", lambda c, m, t: _publication_files_written(c, m, t)
    ),
    "foreign-repositories-touched": (
        "count", lambda c, m, t: _foreign_repositories_touched(c)
    ),
    "dangling-image-references": (
        "count", lambda c, m, t: _dangling_images(c, m, t)
    ),
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Resolve one design-matrix cell.")
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=sorted(MEASURES))
    parser.add_argument("--out", default=None, help="write the report to this path")
    args = parser.parse_args(argv)

    unit, measure = MEASURES[args.criterion]
    manifest, texts = _baseline_manifest()
    value = measure(args.candidate, manifest, texts)

    report = {
        "schema": "protasis-design-report/v1",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": value,
        "unit": unit,
        "command": (
            f"python3 {SELF} "
            f"--candidate {args.candidate} --criterion {args.criterion}"
        ),
        "exit": 0,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    sys.stdout.write(encoded)
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
