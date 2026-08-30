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
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
    # The manifest is written last, and the ordering is load-bearing rather
    # than incidental. A run killed part-way through the prompts leaves a
    # directory with no manifest in it, and a packet with no manifest is one
    # `tally` refuses to read. Write it first and a half-emitted packet becomes
    # one that looks complete enough to grade against.
    (out / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def load_manifest(packet: Path) -> dict:
    """The packet's manifest, or a refusal naming the packet.

    Read first, because everything else in a tally is checked against it. A
    packet with no manifest is a packet `emit` did not finish, and grading
    against one would score a run over a corpus nobody can name.
    """
    raw = _read(packet / MANIFEST_NAME, f"{packet / MANIFEST_NAME}")
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DriverError(f"{packet / MANIFEST_NAME} is not readable JSON: {error}") from error
    if not isinstance(manifest, dict):
        raise DriverError(f"{packet / MANIFEST_NAME} is not an object")
    if manifest.get("contract") != CONTRACT:
        raise DriverError(
            f"{packet / MANIFEST_NAME} declares {manifest.get('contract')!r}, not {CONTRACT}"
        )
    ids = manifest.get("cases")
    if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
        raise DriverError(f"{packet / MANIFEST_NAME} carries no case id list")
    if len(set(ids)) != len(ids):
        raise DriverError(f"{packet / MANIFEST_NAME} repeats a case id")
    for field in ("corpus_sha256", "prompt_template_sha256"):
        value = manifest.get(field)
        if not isinstance(value, str) or len(value) != 64:
            raise DriverError(f"{packet / MANIFEST_NAME} carries no {field}")
    return manifest


def read_answers(path: Path) -> dict:
    """One answer per case id, bounded and closed.

    The answers file is the only untrusted input the driver takes: it comes
    back from wherever the contexts ran. Every shape it can be wrong in is a
    refusal, because a tally that guesses records a score about nothing.
    """
    raw = _read(path, str(path))
    if len(raw) > MAX_ANSWERS_BYTES:
        raise DriverError(f"{path} is larger than {MAX_ANSWERS_BYTES} bytes")
    try:
        answers = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DriverError(f"{path} is not readable JSON: {error}") from error
    if not isinstance(answers, dict) or not answers:
        raise DriverError(f"{path} is not a non-empty object of case id to answer")
    for cid, answer in answers.items():
        if not isinstance(cid, str) or not CASE_ID.match(cid):
            raise DriverError(f"{path}: {cid!r} is not a case id")
        if not isinstance(answer, str) or not answer.strip():
            raise DriverError(f"{path}: {cid} carries no answer")
    return {cid: answer.strip() for cid, answer in answers.items()}


def check_answer_vocabulary(answers: dict, path: Path) -> None:
    """Every answer is a declared canonical name or one of the two refusals.

    Open text here would let a graded context's prose become a recorded score,
    which is the closed-set rule the corpus checker already holds run blocks to.
    """
    allowed = canonical_skill_names() | set(REFUSAL_ANSWERS)
    for cid in sorted(answers):
        if answers[cid] not in allowed:
            raise DriverError(
                f"{path}: {cid} answered {answers[cid]!r}, which is neither a "
                f"canonical skill name nor one of {sorted(REFUSAL_ANSWERS)}"
            )


def score(cases: list, answers: dict) -> dict:
    """Compare each answer with what the corpus expects, and name every miss."""
    passed, failures = 0, []
    for case in cases:
        cid = case["id"]
        given = answers[cid]
        expect = case.get("expect") or {}
        if expect.get("outcome") == "select":
            ok = given == expect.get("canonical")
        else:
            ok = given in REFUSAL_ANSWERS
        if ok:
            passed += 1
        else:
            failures.append({"case": cid, "selected": given})
    return {"passed": passed, "failed": len(failures), "failures": failures}


def corpus_without_runs(raw: bytes) -> bytes:
    """The corpus canonicalised with `runs` removed.

    A tally rewrites one key. Comparing this before and after is how a test
    says every other byte survived, without asserting on a formatter.
    """
    document = json.loads(raw.decode("utf-8"))
    document.pop("runs", None)
    return json.dumps(document, indent=2, sort_keys=True).encode("utf-8")


def tally(packet: Path, answers_path: Path, model: str, date: str) -> dict:
    """Score a packet's answers and write the run block, or refuse."""
    if not ISO_DATE.match(date):
        raise DriverError(f"{date!r} is not a YYYY-MM-DD date")
    if not model.strip():
        raise DriverError("the grading model must be named")

    manifest = load_manifest(packet)
    document = load_corpus()
    cases = document["cases"]

    current = corpus_digest(cases)
    if current != manifest["corpus_sha256"]:
        raise DriverError(
            f"{CORPUS_PATH} now digests {current}, but the packet was emitted "
            f"from {manifest['corpus_sha256']}; emit a fresh packet"
        )
    template_now = prompt_template_digest()
    if template_now != manifest["prompt_template_sha256"]:
        raise DriverError(
            f"{PROMPT_TEMPLATE_PATH} now digests {template_now}, but the packet "
            f"was emitted under {manifest['prompt_template_sha256']}"
        )

    answers = read_answers(answers_path)
    expected_ids = set(manifest["cases"])
    given_ids = set(answers)
    missing = sorted(expected_ids - given_ids)
    extra = sorted(given_ids - expected_ids)
    if missing:
        raise DriverError(
            f"{answers_path} answers no case {missing}; the schema has no field "
            f"for an unanswered case, so a tally cannot record one"
        )
    if extra:
        raise DriverError(f"{answers_path} answers {extra}, which the packet did not ask")
    check_answer_vocabulary(answers, answers_path)

    result = score(cases, answers)
    block = {
        "model": model,
        "date": date,
        "prompt_template_sha256": manifest["prompt_template_sha256"],
        "corpus_sha256": manifest["corpus_sha256"],
        "cases": len(cases),
        "passed": result["passed"],
        "failed": result["failed"],
        "failures": result["failures"],
    }
    document["runs"] = [block]
    (REPOSITORY_ROOT / CORPUS_PATH).write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )
    return block


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    emitter = sub.add_parser("emit", help="write a grading packet")
    emitter.add_argument("--out", required=True)
    scorer = sub.add_parser("tally", help="score a packet's answers into a run block")
    scorer.add_argument("--packet", required=True)
    scorer.add_argument("--answers", required=True)
    scorer.add_argument("--model", required=True)
    scorer.add_argument("--date", required=True)
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
        elif args.command == "tally":
            block = tally(Path(args.packet), Path(args.answers), args.model, args.date)
            print(
                "router-selection run model=%s date=%s cases=%d passed=%d failed=%d"
                % (block["model"], block["date"], block["cases"], block["passed"], block["failed"])
            )
    except DriverError as error:
        print(f"router_selection_driver: error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
