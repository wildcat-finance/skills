#!/usr/bin/env python3
"""Emit a router-selection grading packet and tally the answers it comes back with.

A recorded grading run is bound to `corpus_sha256`. Adding a case moves that
digest, so the recorded run stops describing the corpus and the suite goes red.
The documented repair is a regrade, and until this module there was nothing to
perform one with: `emit_router_selection_report.py` reports on a run that
already exists and is deliberately built never to echo a request.

This driver stops at the model boundary in both directions. `emit` writes one
prompt per case and a manifest; `tally` reads answers back, scores them and
writes the run block. The contexts in between belong to whoever runs it, one
per request. Batching them is what invalidated the first grading this surface
recorded, and a prompt that names outcome classes is what invalidated the
template before it.

Nothing here opens a socket or holds a credential, so a regrade is reproducible
by anyone holding the repository.
"""

from __future__ import annotations

import argparse
import json
import hashlib
import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = "tests/fixtures/router-selection/cases.json"
PROMPT_TEMPLATE_PATH = "tests/fixtures/router-selection/prompt-template.txt"
MANIFEST_NAME = "manifest.json"
CONTRACT = "promise-machine-router-selection-packet/v1"

# The two refusal forms the corpus records, kept identical to the checker's.
REFUSALS = ("ambiguous", "uncovered")
REFUSAL_ANSWERS = frozenset(f"refuse:{reason}" for reason in REFUSALS)

SKILL_NAME = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
CASE_ID = re.compile(r"^RS-\d{2,}$")

# The only case field an emitted prompt may carry. Everything else in a case
# object is the answer or the reasoning behind it, and a graded context that
# sees any of it is grading nothing. An allowlist rather than a denylist,
# because a later schema addition must fail closed rather than leak by default.
EMITTABLE_CASE_FIELDS = frozenset({"id", "request"})

MAX_ANSWERS_BYTES = 1 << 20


class DriverError(Exception):
    """A refusal that names the packet, the case or the field it found."""


def _read(path: Path, what: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise DriverError(f"{what} could not be read: {error}") from error


def load_corpus() -> dict:
    raw = _read(REPOSITORY_ROOT / CORPUS_PATH, CORPUS_PATH)
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DriverError(f"{CORPUS_PATH} is not readable JSON: {error}") from error
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise DriverError(f"{CORPUS_PATH} carries no cases")
    return document


def corpus_digest(cases: list) -> str:
    """Digest the cases alone, exactly as the checker does."""
    payload = json.dumps(cases, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def prompt_template() -> str:
    return _read(REPOSITORY_ROOT / PROMPT_TEMPLATE_PATH, PROMPT_TEMPLATE_PATH).decode("utf-8")


def prompt_template_digest() -> str:
    raw = _read(REPOSITORY_ROOT / PROMPT_TEMPLATE_PATH, PROMPT_TEMPLATE_PATH)
    return hashlib.sha256(raw).hexdigest()


def canonical_skill_names() -> set:
    """Every canonical skill name under `plugins/`, as the checker reads them."""
    names = set()
    for skill in sorted((REPOSITORY_ROOT / "plugins").glob("*/skills/**/SKILL.md")):
        match = SKILL_NAME.search(skill.read_text(encoding="utf-8"))
        if match:
            names.add(match.group(1).strip())
    return names


def render_prompt(request: str) -> str:
    """The pinned template with one request substituted and nothing else.

    `str.replace` rather than `format`, because a request is corpus text and a
    brace in it would otherwise be read as a field.
    """
    template = prompt_template()
    if "{request}" not in template:
        raise DriverError(f"{PROMPT_TEMPLATE_PATH} carries no {{request}} placeholder")
    return template.replace("{request}", request)


def case_request(case: dict, where: str) -> tuple:
    cid = case.get("id")
    if not isinstance(cid, str) or not CASE_ID.match(cid):
        raise DriverError(f"{where}: case id is missing or malformed")
    request = case.get("request")
    if not isinstance(request, str) or not request.strip():
        raise DriverError(f"{where}: {cid} carries no request")
    return cid, request


def emit(out: Path) -> dict:
    """Write one prompt per case plus a manifest, or refuse without writing."""
    document = load_corpus()
    cases = document["cases"]
    pairs = [case_request(c, CORPUS_PATH) for c in cases]
    ids = [cid for cid, _ in pairs]
    if len(set(ids)) != len(ids):
        raise DriverError(f"{CORPUS_PATH} repeats a case id")

    if out.exists() and any(out.iterdir()):
        raise DriverError(f"{out} already holds files; choose an empty directory")
    out.mkdir(parents=True, exist_ok=True)

    manifest = {
        "contract": CONTRACT,
        "corpus": CORPUS_PATH,
        "corpus_sha256": corpus_digest(cases),
        "prompt_template_sha256": prompt_template_digest(),
        "cases": sorted(ids),
    }
    for cid, request in pairs:
        (out / f"{cid}.txt").write_text(render_prompt(request), encoding="utf-8")
    (out / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    emitter = sub.add_parser("emit", help="write a grading packet")
    emitter.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "emit":
            manifest = emit(Path(args.out))
            print(
                "router-selection packet %s cases=%d corpus_sha256=%s "
                "prompt_template_sha256=%s"
                % (
                    args.out,
                    len(manifest["cases"]),
                    manifest["corpus_sha256"],
                    manifest["prompt_template_sha256"],
                )
            )
    except DriverError as error:
        print(f"router_selection_driver: error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
