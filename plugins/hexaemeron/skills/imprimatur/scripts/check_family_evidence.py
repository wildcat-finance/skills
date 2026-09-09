#!/usr/bin/env python3
"""Check the structural-family-evidence-v1 fixture.

The checker reads only files below ``--fixture``. It refuses a symlink, an
oversized file, an unreadable JSONL row and any path that resolves outside
that directory, and it opens no socket unless ``--verify-sources`` is given.
Specimen text is treated as bytes: it is never executed, evaluated or passed
to a shell.

Exit codes: 0 on a clean fixture, 1 on findings, 2 on a bad invocation or an
unsafe read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

FIXTURE_SEED = "imprimatur-structural-family-evidence-v1"
MAX_FILE_BYTES = 1_048_576
GH_TIMEOUT_SECONDS = 30
MAX_FETCH_BYTES = 4_194_304
# The endpoint is a path, and a path names an object only once a host is fixed.
# `gh`'s own documentation gives `GH_HOST` as "the GitHub hostname for commands
# where a hostname has not been provided, or cannot be inferred from the context
# of a local Git repository", and this command provided neither, so an operator
# environment or the working directory's remote decided where a specimen's text
# was sent and compared. Both halves close that: the argv pins the host, where a
# reader and a test can see it, and the two variables that could still name one
# are dropped from the child.
GH_HOSTNAME = "github.com"
GH_HOST_ENVIRONMENT = ("GH_HOST", "GH_REPO")
TIER_MINIMUMS = {
    "high-value": (2, 2),
    "signal": (2, 1),
    "boundary": (0, 0),
    "existing-family": (0, 0),
    "future": (0, 0),
}
# One tier set, declared once. TIERS was a second literal naming the same five
# tiers: collect_findings refused a tier outside TIERS and then indexed
# TIER_MINIMUMS with it, so a name in one list and not the other raised an
# uncaught KeyError, printed a traceback and exited 1 -- the code the amended
# Exit reserves for a content finding, not the 2 it reserves for an unsafe
# read. Reproduced by adding a sixth tier to TIERS and to the family schema's
# enum. Deriving the tuple makes that divergence unwritable rather than
# guarded, which is what the rest of this file's tier joins assume.
TIERS = tuple(TIER_MINIMUMS)
# Every value that becomes part of a gh endpoint passes endpoint_segment, which
# fullmatches one pattern named here. The schema is not that boundary: it
# validates with re.search, its `^wildcat-finance/` pattern admits
# `wildcat-finance/../other-org/repo`, its `^[0-9a-f]{40}$` admits a trailing
# newline, and `source_path` carries no pattern at all. Adding a field to an
# endpoint means adding its row below; a field with no row cannot reach gh.
ENDPOINT_SEGMENTS = {
    "repository": (
        re.compile(r"wildcat-finance/[A-Za-z0-9][A-Za-z0-9._-]*"),
        "repository is not one pinned wildcat-finance repository",
    ),
    "source_path": (
        re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*"),
        "unusable source_path",
    ),
    "source_commit": (re.compile(r"[0-9a-f]{40}"), "unusable source_commit"),
    "object_number": (re.compile(r"[0-9]{1,20}"), "cannot read an object number"),
    "comment_id": (re.compile(r"[0-9]{1,20}"), "cannot read a comment id"),
}
# A comment's own id is in the URL fragment. The number before it is the issue
# or pull request the comment sits under, which is a different object. The
# fragment ends at \Z rather than $, because $ also matches before a trailing
# newline and would carry that newline's row into the endpoint.
COMMENT_FRAGMENT = re.compile(r"#(issuecomment-|discussion_r)([0-9]+)\Z")
# The path before a comment's fragment is the thread the comment sits under.
# Nothing read it, so the fragment alone decided the endpoint and a citation
# whose path was a blob, a commit or a release replayed a comment anyway. This
# is that missing half. The number group is `[^/]+` rather than `[0-9]+` so a
# non-ASCII digit still reaches endpoint_segment, which owns that refusal and
# names the field it came from.
THREAD_PATH = re.compile(r"(issues|pull|pulls)/([^/]+)")
# The endpoint is built from `repository`, `source_commit` and `source_path`,
# while `source_url` is the citation a reader follows to the same object.
# Anchoring each segment's shape says the endpoint is one wildcat-finance
# object; it does not say it is the object this specimen cites. Nothing
# compared the two, so a row citing one object and replaying another passed
# every check. cited_path and require_cited are that comparison.
GITHUB_PREFIX = "https://github.com/"
FAMILIES_NAME = "families.jsonl"
SPECIMENS_NAME = "specimens.jsonl"
REJECTIONS_NAME = "selection-rejections.jsonl"
FAMILY_SCHEMA_NAME = "family.schema.json"
SPECIMEN_SCHEMA_NAME = "specimen.schema.json"

# A schema states what a row must carry. This file states what is checked. They
# were two lists with nothing between them, so a field could be required and
# enforced by nothing, and that fact was visible in neither: not in the schema,
# which states requirements, and not here, which states checks. Ten required
# fields were in that position, and finding them one at a time is what four
# audit rounds did. Every required field now names its enforcement, and
# `schema-contract` refuses a schema whose `required` list is not exactly these
# keys, so a field added or dropped without a decision is a finding rather than
# a silence. An `OWNED_ELSEWHERE` owner is a field this step deliberately does
# not enforce, with the runbook step that writes it; `--report` carries those
# under `unenforced_fields` so a later step reads them rather than re-deriving
# them from grep. Adding a field to a schema means adding its row below.
OWNED_ELSEWHERE = "step-3"
FIELD_ENFORCEMENT = {
    FAMILIES_NAME: {
        "family_id": (
            "checker",
            "family-duplicate refuses a second row, and specimen-unknown-family joins every specimen to one of these ids",
        ),
        "group": ("tests", "compared with the issue's five section headings"),
        "evidence_tier": (
            "checker",
            "family-tier refuses a tier TIER_MINIMUMS does not enforce, and family-minimum compares the declared pair with it",
        ),
        "form": ("tests", "compared with the issue's Form line"),
        "reader_cost": ("tests", "compared with the issue's Reader cost line"),
        "direct_rewrite": ("tests", "compared with the issue's Direct rewrite line"),
        "boundary": ("tests", "compared with the issue's Boundary line"),
        "disposition": ("tests", "compared with the issue's Disposition line"),
        "overlaps": ("checker", "family-overlaps refuses an entry naming no row in this catalogue"),
        "discovery_phrases": (
            OWNED_ELSEWHERE,
            "step 3's Exit finds candidate paragraphs by each family's discovery_phrases; nothing reads them here and 29 rows carry none",
        ),
        "minimum_positive": ("checker", "family-minimum compares it with TIER_MINIMUMS"),
        "minimum_negative": ("checker", "family-minimum compares it with TIER_MINIMUMS"),
        "source_issue": ("schema", "a const, so its schema clause is the whole check"),
    },
    SPECIMENS_NAME: {
        "specimen_id": ("checker", "specimen-duplicate refuses one id on two rows"),
        "family_id": ("checker", "specimen-unknown-family refuses an id no family row carries"),
        "tier": ("schema", "a const, so its schema clause is the whole check"),
        "family": ("checker", "specimen-family-mismatch compares it with family_id"),
        "polarity": ("checker", "specimen-independence and the tier-minimum count read it"),
        "decision": (
            OWNED_ELSEWHERE,
            "step 3's Exit records decision with the annotation; nothing compares it with polarity or rewrite here",
        ),
        "text": ("checker", "specimen-span, specimen-digest and the --verify-sources comparison read it"),
        "text_sha256": ("checker", "specimen-digest compares it with the row's own text"),
        "start_byte": ("checker", "specimen-span"),
        "end_byte": ("checker", "specimen-span"),
        "reason": (OWNED_ELSEWHERE, "step 3's Exit records reason with the annotation; nothing reads it here"),
        "rewrite": (
            OWNED_ELSEWHERE,
            "step 3's Exit records rewrite with the annotation; nothing requires one on an actionable positive here",
        ),
        "repository": (
            "checker",
            "endpoint_segment gates it, and cited_path refuses a citation naming another repository",
        ),
        "source_url": ("checker", "cited_path, cited_thread and require_cited compare the citation with the replayed object"),
        "source_commit": ("checker", "endpoint_segment gates it on every kind"),
        "source_path": ("checker", "endpoint_segment gates it and require_cited compares it with the citation"),
        "source_start_line": (
            OWNED_ELSEWHERE,
            "S2-R4-05: step 3's collector writes it and no line contract is in this step's Exit refusal list",
        ),
        "source_end_line": (
            OWNED_ELSEWHERE,
            "S2-R4-05: step 3's collector writes it and no line contract is in this step's Exit refusal list",
        ),
        "source_object": ("checker", "fetch_source_object chooses the endpoint from it"),
        "source_group_id": ("checker", "group_id_problem and specimen-independence"),
        "origin": (OWNED_ELSEWHERE, "step 3's collector records it; nothing reads it here"),
        "annotated_before_lint": ("checker", "specimen-annotation-order refuses a row that is not true"),
        "selection_seed": ("checker", "schema-contract compares its schema const with FIXTURE_SEED"),
        "selection_rank_within_group": (
            OWNED_ELSEWHERE,
            "step 3's Exit orders candidates by the seed digest and this records the rank; nothing reads it here",
        ),
    },
}
ROW_SCHEMA_NAMES = {FAMILIES_NAME: FAMILY_SCHEMA_NAME, SPECIMENS_NAME: SPECIMEN_SCHEMA_NAME}

FINDING_CLASSES = (
    "schema-contract",
    "family-tier",
    "family-schema",
    "family-duplicate",
    "family-minimum",
    "family-overlaps",
    "specimen-annotation-order",
    "specimen-schema",
    "specimen-duplicate",
    "specimen-unknown-family",
    "specimen-family-mismatch",
    "specimen-span",
    "specimen-digest",
    "specimen-group-id",
    "specimen-independence",
    "tier-minimum",
    "source-mismatch",
)


class RefusalError(Exception):
    """An unsafe read or a bad invocation. The caller exits 2."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_below(fixture: Path, name: str) -> Path:
    """Resolve ``name`` below ``fixture`` and refuse anything outside it."""
    if Path(name).is_absolute() or ".." in Path(name).parts:
        raise RefusalError(f"path escapes the fixture: {name}")
    candidate = fixture / name
    for part in (candidate, *candidate.parents):
        if part == fixture:
            break
        if part.is_symlink():
            raise RefusalError(f"symlink refused: {part}")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(fixture):
        raise RefusalError(f"path escapes the fixture: {name}")
    return candidate


def read_bytes_below(fixture: Path, name: str) -> bytes:
    path = resolve_below(fixture, name)
    if not path.is_file():
        raise RefusalError(f"missing file: {name}")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise RefusalError(f"file over {MAX_FILE_BYTES} bytes: {name} ({size})")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RefusalError(f"cannot read {name}: {exc}") from exc


def object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    """Build the object, refusing a key JSON's last-wins rule would hide.

    A row carrying `evidence_tier` twice reads to a person as its first value
    and is checked as its second, so the frozen bytes and the enforced meaning
    disagree with nothing on screen to show it.
    """
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(f"duplicate JSON key {key!r}")
        seen.add(key)
    return dict(pairs)


def read_json_below(fixture: Path, name: str):
    blob = read_bytes_below(fixture, name)
    try:
        return json.loads(blob.decode("utf-8"), object_pairs_hook=object_without_duplicate_keys)
    except (UnicodeDecodeError, ValueError) as exc:
        raise RefusalError(f"cannot parse {name}: {exc}") from exc


def jsonl_rows(text: str) -> list[str]:
    """Split a JSON Lines file on the newline, and on nothing else.

    ``str.splitlines`` also splits on U+000B, U+000C, U+0085, U+2028 and
    U+2029, and each of those is legal inside a JSON string. That cut both
    ways. A file that ``wc -l``, a diff and every other JSON Lines reader see
    as 42 rows could carry a further row this checker admitted and counted,
    which is a frozen file whose bytes and whose meaning here disagree with
    nothing on screen to show it. A specimen whose ``text`` carried one of
    them raw -- the form ``json.dumps(..., ensure_ascii=False)`` emits -- was
    split into fragments and refused as unreadable JSON. JSON Lines is
    newline-delimited, so the newline is the whole separator.
    """
    if not text:
        return []
    if text.endswith("\n"):
        text = text[:-1]
    return text.split("\n")


def group_id_problem(value: str) -> str | None:
    """Return why a ``source_group_id`` cannot key the independence rule.

    Independence is decided by comparing this value between two positives, so
    the comparison is worth exactly what the value's visibility is worth. Two
    ids differing by a space, a no-break space or a zero-width character read
    as one group on screen and as two here, which is enough to carry a
    high-value family's two independent positives out of a single document.

    Refusing whitespace and non-printing characters left the same hole open
    one composition down. A combining mark is neither, so the NFC and NFD
    spellings of one path render identically and compare unequal, and two
    positives from that one document counted as two independent groups. NFC
    is required rather than applied, so the value a reader sees and the value
    this compares are the same string.
    """
    for character in value:
        if character.isspace():
            return f"carries whitespace ({character!r})"
        if unicodedata.category(character) in ("Cc", "Cf", "Cn", "Co", "Cs"):
            return f"carries a non-printing character ({character!r})"
    if value != unicodedata.normalize("NFC", value):
        return "is not in Unicode normal form NFC"
    return None


def read_jsonl_below(fixture: Path, name: str) -> list[dict]:
    blob = read_bytes_below(fixture, name)
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RefusalError(f"{name} is not UTF-8: {exc}") from exc
    rows: list[dict] = []
    for number, line in enumerate(jsonl_rows(text), 1):
        if not line.strip():
            raise RefusalError(f"blank JSONL row at {name}:{number}")
        try:
            value = json.loads(line, object_pairs_hook=object_without_duplicate_keys)
        except ValueError as exc:
            raise RefusalError(f"unreadable JSON at {name}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise RefusalError(f"row at {name}:{number} is not an object")
        rows.append(value)
    return rows


def validate_schema(value, schema: dict, context: str) -> None:
    """Validate the JSON Schema subset the sibling v1 evaluator validates."""
    allowed_types = schema.get("type")
    if allowed_types is not None:
        if not isinstance(allowed_types, list):
            allowed_types = [allowed_types]
        predicates = {
            "object": lambda item: isinstance(item, dict),
            "array": lambda item: isinstance(item, list),
            "string": lambda item: isinstance(item, str),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
            "boolean": lambda item: isinstance(item, bool),
            "null": lambda item: item is None,
        }
        if not any(predicates[name](value) for name in allowed_types):
            raise ValueError(f"schema type mismatch at {context}: expected {allowed_types}")
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"schema const mismatch at {context}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"schema enum mismatch at {context}: {value!r}")
    if isinstance(value, dict):
        missing = set(schema.get("required", [])) - set(value)
        if missing:
            raise ValueError(f"schema missing keys at {context}: {sorted(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise ValueError(f"schema extra keys at {context}: {sorted(extra)}")
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], f"{context}/{key}")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValueError(f"schema array too short at {context}")
        if schema.get("uniqueItems"):
            rendered = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(rendered) != len(set(rendered)):
                raise ValueError(f"schema duplicate array item at {context}")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema["items"], f"{context}/{index}")
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ValueError(f"schema string too short at {context}")
        pattern = schema.get("pattern")
        if pattern is not None:
            if re.search(pattern, value) is None:
                raise ValueError(f"schema pattern mismatch at {context}: {value!r}")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"schema number below minimum at {context}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError(f"schema number above maximum at {context}")


def span_problem(row: dict) -> str | None:
    """Return why the span is unusable, or None when it is sound."""
    text = row.get("text")
    start = row.get("start_byte")
    end = row.get("end_byte")
    if not isinstance(text, str):
        return "text is not a string"
    if not isinstance(start, int) or isinstance(start, bool):
        return "start_byte is not an integer"
    if not isinstance(end, int) or isinstance(end, bool):
        return "end_byte is not an integer"
    blob = text.encode("utf-8")
    if start < 0 or end > len(blob):
        return f"span {start}:{end} lies outside the {len(blob)}-byte text"
    if start >= end:
        return f"span {start}:{end} is empty"
    try:
        blob[start:end].decode("utf-8")
    except UnicodeDecodeError:
        return f"span {start}:{end} splits a UTF-8 codepoint"
    return None


def gh_fetch(argv: list[str]) -> bytes:
    """Run one fixed-argv ``gh api`` call with no shell and a bounded result.

    The host is pinned here rather than left to the environment. Every endpoint
    below is a relative API path, and ``gh`` resolves a relative path against
    ``--hostname``, then ``GH_HOST``, then the working directory's own remote.
    Only the first of those is this checker's to state, so it states it, and
    ``GH_HOST`` and ``GH_REPO`` are removed from the child so neither can name
    a host or a repository the specimen never cited.
    """
    if not argv or argv[0] != "api":
        raise RefusalError(f"refusing a gh call that is not `gh api`: {argv!r}")
    for value in argv:
        if value.startswith("-") and value not in ("-H",):
            raise RefusalError(f"refusing an option-shaped gh argument: {value!r}")
    environment = {
        name: value
        for name, value in os.environ.items()
        if name not in GH_HOST_ENVIRONMENT
    }
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, shell=False
            ["gh", "api", "--hostname", GH_HOSTNAME, *argv[1:]],
            capture_output=True,
            shell=False,
            timeout=GH_TIMEOUT_SECONDS,
            check=False,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RefusalError(f"gh call failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()[:200]
        raise RefusalError(f"gh exited {completed.returncode}: {detail}")
    if len(completed.stdout) > MAX_FETCH_BYTES:
        raise RefusalError("gh returned more than the fetch cap allows")
    return completed.stdout


def reply_value(blob: bytes, path: tuple[str, ...], specimen_id) -> str:
    """Read one string out of a gh reply, refusing every other shape.

    The reply is data from outside the process like the row is. Round 1 stopped
    an unchecked row reaching the endpoint; this stops an unchecked reply
    reaching a field access, where a KeyError exits 1 -- the code reserved for a
    content finding -- and prints a traceback.
    """
    try:
        value = json.loads(blob)
    except ValueError as exc:
        raise RefusalError(f"gh reply for {specimen_id} is not JSON: {exc}") from exc
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise RefusalError(f"gh reply for {specimen_id} carries no {'.'.join(path)}")
        value = value[key]
    if value is None:
        return ""
    if not isinstance(value, str):
        raise RefusalError(f"gh reply {'.'.join(path)} for {specimen_id} is not a string")
    return value


def endpoint_segment(field: str, value, specimen_id) -> str:
    """Return ``value`` only when it fullmatches the pattern pinned for ``field``.

    This is the one gate between a specimen row and a gh endpoint. Fullmatch,
    not search: a pattern anchored only at its start admits a suffix, which is
    how `^wildcat-finance/` once admitted `wildcat-finance/../evil-org/repo`.
    """
    pattern, message = ENDPOINT_SEGMENTS[field]
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise RefusalError(f"{message} for {specimen_id}: {value!r}")
    return value


def cited_path(row: dict, repository: str, specimen_id) -> str:
    """Return the ``source_url`` path below the repository being replayed.

    A citation naming another repository is refused here rather than compared
    later, because every endpoint below is built from ``repository`` and would
    otherwise read an object in a repository the specimen never cited.

    A query string is dropped with the fragment. Neither is part of the path,
    and GitHub's own permalink for a Markdown file carries ``?plain=1``, which
    was compared against the path and refused a citation that agreed.
    """
    url = row["source_url"]
    prefix = f"{GITHUB_PREFIX}{repository}/"
    if not isinstance(url, str) or not url.startswith(prefix):
        raise RefusalError(f"source_url for {specimen_id} does not cite {repository}: {url!r}")
    return url[len(prefix):].split("#", 1)[0].split("?", 1)[0].rstrip("/")


def cited_thread(row: dict, repository: str, specimen_id) -> tuple[str, str, str]:
    """Return the cited path, its collection and its number for a thread citation.

    Both body kinds and both comment kinds cite an issue or pull request
    thread. Reading the number here rather than off the raw URL removes the
    second parse: ``rsplit`` before the fragment split and ``rstrip`` after it
    could disagree with this one about where the path ended.
    """
    cited = cited_path(row, repository, specimen_id)
    thread = THREAD_PATH.fullmatch(cited)
    if thread is None:
        raise RefusalError(
            f"source_url for {specimen_id} cites {cited!r}, which is not an "
            "issue or pull request thread"
        )
    return cited, thread.group(1), thread.group(2)


def require_cited(specimen_id, cited: str, allowed: tuple[str, ...]) -> None:
    """Refuse a replay of an object the specimen's own citation does not name."""
    if cited not in allowed:
        raise RefusalError(
            f"source_url for {specimen_id} cites {cited!r}, which is not the "
            f"replayed object ({' or '.join(allowed)})"
        )


def fetch_source_object(row: dict) -> str:
    """Replay one specimen's cited GitHub object. Opens a socket.

    Two of the six kinds replay an object GitHub cannot change under the
    reference sent: a file at ``?ref=<sha>`` and a commit read by its sha. The
    four body and comment kinds have no such reference, so their replay
    compares the current body and is a live read rather than an immutable one.
    ``source_commit`` is still checked on every kind, because a row carrying an
    unusable commit is an unusable row whether this endpoint sends it or not.
    """
    specimen_id = row.get("specimen_id")
    repository = endpoint_segment("repository", row["repository"], specimen_id)
    commit = endpoint_segment("source_commit", row["source_commit"], specimen_id)
    source_object = row["source_object"]
    if source_object == "markdown_paragraph":
        path = endpoint_segment("source_path", row["source_path"], specimen_id)
        cited = cited_path(row, repository, specimen_id)
        require_cited(specimen_id, cited, (f"blob/{commit}/{path}", f"raw/{commit}/{path}"))
        blob = gh_fetch(
            [
                "api",
                "-H",
                "Accept: application/vnd.github.raw",
                f"repos/{repository}/contents/{path}?ref={commit}",
            ]
        )
        return blob.decode("utf-8", "replace")
    if source_object == "commit_message":
        cited = cited_path(row, repository, specimen_id)
        require_cited(specimen_id, cited, (f"commit/{commit}", f"commits/{commit}"))
        blob = gh_fetch(["api", f"repos/{repository}/commits/{commit}"])
        return reply_value(blob, ("commit", "message"), specimen_id)
    if source_object in ("issue_body", "pull_request_body"):
        cited, _, tail = cited_thread(row, repository, specimen_id)
        number = endpoint_segment("object_number", tail, specimen_id)
        collections = ("issues",) if source_object == "issue_body" else ("pull", "pulls")
        require_cited(specimen_id, cited, tuple(f"{name}/{number}" for name in collections))
        blob = gh_fetch(["api", f"repos/{repository}/issues/{number}"])
        return reply_value(blob, ("body",), specimen_id)
    cited, cited_collection, _ = cited_thread(row, repository, specimen_id)
    # The fragment, not source_object, decides the collection: a pull request's
    # conversation comment is an issue comment on GitHub and legitimately
    # carries #issuecomment-, so the two are not cross-checked here. The cited
    # path is checked, because a fragment on a blob, a commit or a release
    # named a comment the citation does not lead a reader to.
    fragment = COMMENT_FRAGMENT.search(row["source_url"])
    if fragment is None:
        raise RefusalError(f"cannot read a comment id from {row['source_url']}")
    if fragment.group(1) == "discussion_r" and cited_collection == "issues":
        raise RefusalError(
            f"source_url for {specimen_id} cites a review comment under {cited!r}, "
            "which is an issue thread"
        )
    collection = "issues" if fragment.group(1) == "issuecomment-" else "pulls"
    comment = endpoint_segment("comment_id", fragment.group(2), specimen_id)
    blob = gh_fetch(["api", f"repos/{repository}/{collection}/comments/{comment}"])
    return reply_value(blob, ("body",), specimen_id)


def unenforced_fields() -> list[dict]:
    """Return every required field this step declares and does not enforce.

    A deferral that lives only in a source comment is found by whoever greps
    for it. This is the same fact as a report key, so the step that owns each
    field reads it instead of re-deriving it.
    """
    return [
        {"row": row_name, "field": field, "owner": owner, "note": note}
        for row_name in sorted(FIELD_ENFORCEMENT)
        for field, (owner, note) in sorted(FIELD_ENFORCEMENT[row_name].items())
        if owner == OWNED_ELSEWHERE
    ]


def schema_contract_problems(schemas: dict[str, dict]) -> list[str]:
    """Return where a schema's declarations and this file's checks disagree.

    Three joins, each of which was two unjoined copies of one contract. The
    `required` list against FIELD_ENFORCEMENT: dropping `origin` from the
    specimen schema's `required` list left all 54 tests green, so the
    declaration itself could shrink unnoticed. The family schema's
    `evidence_tier` enum against the enforced tier set: adding a sixth tier
    left all 54 green while the checker would refuse every row carrying it.
    The specimen schema's `selection_seed` const against FIXTURE_SEED:
    changing the constant left all 54 green, and the report's `seed` then
    names a seed no specimen may declare.
    """
    problems: list[str] = []
    for row_name in sorted(FIELD_ENFORCEMENT):
        schema_name = ROW_SCHEMA_NAMES[row_name]
        register = FIELD_ENFORCEMENT[row_name]
        required = schemas[row_name].get("required")
        if not isinstance(required, list):
            problems.append(f"{schema_name}: required is not a list")
            continue
        declared = set(required)
        if len(declared) != len(required):
            problems.append(f"{schema_name}: required names a field twice")
        unaccounted = sorted(declared - set(register))
        if unaccounted:
            problems.append(
                f"{schema_name}: required names {unaccounted}, which no field enforcement accounts for"
            )
        absent = sorted(set(register) - declared)
        if absent:
            problems.append(
                f"{schema_name}: field enforcement names {absent}, which required does not declare"
            )
    properties = schemas[FAMILIES_NAME].get("properties", {})
    enum = properties.get("evidence_tier", {}).get("enum")
    if not isinstance(enum, list) or sorted(set(enum)) != sorted(TIERS) or len(enum) != len(TIERS):
        problems.append(
            f"{FAMILY_SCHEMA_NAME}: evidence_tier declares {enum!r}, and {sorted(TIERS)} is enforced"
        )
    seed = schemas[SPECIMENS_NAME].get("properties", {}).get("selection_seed", {}).get("const")
    if seed != FIXTURE_SEED:
        problems.append(
            f"{SPECIMEN_SCHEMA_NAME}: selection_seed declares {seed!r}, and {FIXTURE_SEED!r} is the fixture seed"
        )
    return problems


def collect_findings(
    families: list[dict],
    specimens: list[dict],
    family_schema: dict,
    specimen_schema: dict,
    below_minimum: list[dict],
    allow_below_minimum: bool,
    verify_sources: bool,
) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {name: [] for name in FINDING_CLASSES}
    findings["schema-contract"].extend(
        schema_contract_problems({FAMILIES_NAME: family_schema, SPECIMENS_NAME: specimen_schema})
    )
    seen: set[str] = set()
    seen_specimens: set[str] = set()
    # Only rows that cleared every local check reach the network. A row that
    # failed its schema has an unchecked repository, path and commit, and
    # fetch_source_object reads those fields straight into the gh endpoint.
    verifiable: list[tuple[int, dict]] = []
    for index, row in enumerate(families, 1):
        label = row.get("family_id", f"row {index}")
        tier = row.get("evidence_tier")
        if tier not in TIERS:
            findings["family-tier"].append(f"{FAMILIES_NAME}:{index}: unknown evidence_tier {tier!r} for {label}")
            continue
        try:
            validate_schema(row, family_schema, f"{FAMILIES_NAME}:{index}")
        except ValueError as exc:
            findings["family-schema"].append(f"{exc}")
            continue
        if row["family_id"] in seen:
            findings["family-duplicate"].append(
                f"{FAMILIES_NAME}:{index}: duplicate family_id {row['family_id']}"
            )
        seen.add(row["family_id"])
        # The row declares its minimums and TIER_MINIMUMS enforces them, and
        # nothing joined the two. Every measurement reads the table, so the
        # declared pair could say one thing while the checked pair said
        # another: dropping `signal` to (1, 0) in the table left the catalogue
        # still declaring (2, 1), the report printing 1 and 0 beside that
        # family, `below_minimum` still 13 so the step's own proof command
        # held, and the whole suite green, because the only other copy of the
        # table is a literal in the test module and no test reads this one.
        # The amended Exit already states that these two fields are set from
        # the tier; this is that sentence as a comparison.
        declared = (row["minimum_positive"], row["minimum_negative"])
        if declared != TIER_MINIMUMS[tier]:
            findings["family-minimum"].append(
                f"{FAMILIES_NAME}:{index}: {row['family_id']} declares minimum_positive "
                f"{declared[0]} and minimum_negative {declared[1]}, but tier {tier} "
                f"is enforced as {TIER_MINIMUMS[tier][0]} and {TIER_MINIMUMS[tier][1]}"
            )

    # `overlaps` declares a link to another family and nothing resolved it, so
    # a row could name a family that does not exist and exit 0; round 6 read
    # the shipped list by hand instead. This is `specimen-unknown-family`'s
    # check on the catalogue's own referential field. It runs after the loop
    # above because it needs every id the catalogue carries.
    for index, row in enumerate(families, 1):
        overlaps = row.get("overlaps")
        if not isinstance(overlaps, list):
            continue
        for name in overlaps:
            if name not in seen:
                findings["family-overlaps"].append(
                    f"{FAMILIES_NAME}:{index}: {row.get('family_id')} overlaps {name!r}, "
                    "which is not a family in this catalogue"
                )

    positives: dict[str, list[dict]] = {}
    for index, row in enumerate(specimens, 1):
        label = row.get("specimen_id", f"row {index}")
        if row.get("annotated_before_lint") is not True:
            findings["specimen-annotation-order"].append(
                f"{SPECIMENS_NAME}:{index}: annotated_before_lint is not true for {label}"
            )
            continue
        try:
            validate_schema(row, specimen_schema, f"{SPECIMENS_NAME}:{index}")
        except ValueError as exc:
            findings["specimen-schema"].append(f"{exc}")
            continue
        # One specimen id on two rows. A duplicate family_id was refused and
        # this was not, so two byte-identical negative rows counted as two
        # negatives and carried a high-value family's whole negative minimum
        # out of one document. Independence stays a positives-only rule, which
        # is what the register asks for; this refuses one row counted twice.
        if row["specimen_id"] in seen_specimens:
            findings["specimen-duplicate"].append(
                f"{SPECIMENS_NAME}:{index}: duplicate specimen_id {row['specimen_id']}"
            )
            continue
        seen_specimens.add(row["specimen_id"])
        if row["family_id"] not in seen:
            findings["specimen-unknown-family"].append(
                f"{SPECIMENS_NAME}:{index}: {label} names unknown family {row['family_id']}"
            )
            continue
        # One family named twice, in the two spellings the v1 and v2 schemas
        # use. Nothing but this compared them, so a row could be counted under
        # family_id while a v2 evaluator reading `family` saw another family.
        if row["family"] != row["family_id"]:
            findings["specimen-family-mismatch"].append(
                f"{SPECIMENS_NAME}:{index}: {label}: family {row['family']!r} "
                f"is not its family_id {row['family_id']!r}"
            )
            continue
        problem = span_problem(row)
        if problem is not None:
            findings["specimen-span"].append(f"{SPECIMENS_NAME}:{index}: {label}: {problem}")
            continue
        if sha256_text(row["text"]) != row["text_sha256"]:
            findings["specimen-digest"].append(
                f"{SPECIMENS_NAME}:{index}: {label}: text_sha256 does not match the text"
            )
            continue
        group_problem = group_id_problem(row["source_group_id"])
        if group_problem is not None:
            findings["specimen-group-id"].append(
                f"{SPECIMENS_NAME}:{index}: {label}: source_group_id {group_problem}"
            )
            continue
        verifiable.append((index, row))
        if row["polarity"] == "positive":
            positives.setdefault(row["family_id"], []).append(row)

    for family_id, rows in sorted(positives.items()):
        groups: dict[str, str] = {}
        for row in rows:
            group = row["source_group_id"]
            if group in groups:
                findings["specimen-independence"].append(
                    f"{family_id}: {groups[group]} and {row['specimen_id']} share source_group_id {group}"
                )
            else:
                groups[group] = row["specimen_id"]

    if not allow_below_minimum:
        for entry in below_minimum:
            findings["tier-minimum"].append(
                f"{entry['family_id']} ({entry['evidence_tier']}) has "
                f"{entry['independent_positives']} independent positive and "
                f"{entry['negatives']} negative specimens, below the "
                f"{entry['minimum_positive']} and {entry['minimum_negative']} its tier requires"
            )

    if verify_sources:
        # The digest was compared against this row's own text above, and a row
        # that failed it never reached here, so comparing it again after the
        # replay could not fail. What the replay establishes is that the text
        # is present in the object the specimen cites.
        for index, row in verifiable:
            body = fetch_source_object(row)
            if row["text"] not in body:
                findings["source-mismatch"].append(
                    f"{SPECIMENS_NAME}:{index}: {row['specimen_id']}: text is absent from the replayed object"
                )
    return findings


def measure_below_minimum(
    families: list[dict],
    specimens: list[dict],
    tier_filter: str | None,
    min_independent_positive: int | None,
) -> list[dict]:
    # This runs before anything is validated, so every field it reads is raw.
    # Two of them reached a hash: `source_group_id` a set element and
    # `evidence_tier` a dict key. A row carrying either as a list or an object
    # raised an uncaught TypeError, which printed a traceback and exited 1 --
    # the code reserved for a content finding, not the 2 reserved for an
    # unsafe read. Both are now skipped here and reported by collect_findings,
    # which is the same shape the family_id and polarity guards already had.
    counted: dict[str, dict] = {}
    for row in specimens:
        family_id = row.get("family_id")
        polarity = row.get("polarity")
        group = row.get("source_group_id")
        if not isinstance(family_id, str) or polarity not in ("positive", "negative"):
            continue
        if polarity == "positive" and not isinstance(group, str):
            continue
        entry = counted.setdefault(family_id, {"positive": [], "negative": 0})
        if polarity == "positive":
            entry["positive"].append(group)
        else:
            entry["negative"] += 1
    below = []
    for row in families:
        family_id = row.get("family_id")
        tier = row.get("evidence_tier")
        if not isinstance(tier, str) or tier not in TIER_MINIMUMS:
            continue
        if not isinstance(family_id, str):
            continue
        if tier_filter is not None and tier != tier_filter:
            continue
        minimum_positive, minimum_negative = TIER_MINIMUMS[tier]
        if min_independent_positive is not None:
            minimum_positive = min_independent_positive
        if minimum_positive == 0 and minimum_negative == 0:
            continue
        entry = counted.get(family_id, {"positive": [], "negative": 0})
        independent = len(set(entry["positive"]))
        if independent >= minimum_positive and entry["negative"] >= minimum_negative:
            continue
        below.append(
            {
                "family_id": family_id,
                "evidence_tier": tier,
                "minimum_positive": minimum_positive,
                "minimum_negative": minimum_negative,
                "positives": len(entry["positive"]),
                "independent_positives": independent,
                "negatives": entry["negative"],
            }
        )
    return below


def build_report(fixture: Path, families: list[dict], specimens: list[dict], below_minimum: list[dict]) -> dict:
    tiers: dict[str, int] = {}
    for row in families:
        tier = row.get("evidence_tier")
        if isinstance(tier, str):
            tiers[tier] = tiers.get(tier, 0) + 1
    return {
        "schema_version": 1,
        "seed": FIXTURE_SEED,
        "fixture": fixture.name,
        "families": len(families),
        "specimens": len(specimens),
        "tiers": tiers,
        "below_minimum": below_minimum,
        "unenforced_fields": unenforced_fields(),
        "rejections_path": REJECTIONS_NAME,
    }


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the structural-family-evidence-v1 fixture.")
    parser.add_argument("--fixture", type=Path, required=True, help="fixture directory; no file outside it is read")
    parser.add_argument("--report", type=Path, help="write one JSON report to this path")
    parser.add_argument(
        "--allow-below-minimum",
        action="store_true",
        help=(
            "record a tier-minimum shortfall in the report instead of reporting it as a finding. "
            "This flag exists for the build phase only, while specimens are still being collected; "
            "a released fixture must pass without it."
        ),
    )
    parser.add_argument(
        "--min-independent-positive",
        type=int,
        help="override the independent-positive minimum for the tier --tier names; requires --tier",
    )
    parser.add_argument("--tier", help="restrict the tier-minimum check to one evidence tier")
    parser.add_argument(
        "--verify-sources",
        action="store_true",
        help=(
            "replay every specimen against the GitHub object it cites, at the pinned host. "
            "Two of the six kinds send a reference GitHub cannot change under, a file at "
            "?ref=<sha> and a commit read by its sha; the four body and comment kinds have "
            "no such reference and compare the current body. This is the only path that "
            "opens a socket."
        ),
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    fixture = args.fixture.resolve()
    if args.fixture.is_symlink():
        raise RefusalError(f"symlink refused: {args.fixture}")
    if not fixture.is_dir():
        raise RefusalError(f"not a fixture directory: {args.fixture}")
    if args.tier is not None and args.tier not in TIERS:
        raise RefusalError(f"unknown tier: {args.tier}")
    if args.min_independent_positive is not None and args.min_independent_positive < 0:
        raise RefusalError("--min-independent-positive cannot be negative")
    # The override reaches every tier the run measures, so without --tier it
    # reached all five. `boundary`, `existing-family` and `future` require
    # nothing, and the flag alone put all 42 families in `below_minimum` with a
    # minimum_positive their tier does not require, in the field the README
    # documents as "the minimums its tier requires". The flag overrides one
    # tier's minimum, so it now names the tier it overrides.
    if args.min_independent_positive is not None and args.tier is None:
        raise RefusalError("--min-independent-positive overrides one tier and needs --tier")

    family_schema = read_json_below(fixture, f"schemas/{FAMILY_SCHEMA_NAME}")
    specimen_schema = read_json_below(fixture, f"schemas/{SPECIMEN_SCHEMA_NAME}")
    families = read_jsonl_below(fixture, FAMILIES_NAME)
    specimens = read_jsonl_below(fixture, SPECIMENS_NAME)

    below_minimum = measure_below_minimum(families, specimens, args.tier, args.min_independent_positive)
    report = build_report(fixture, families, specimens, below_minimum)
    if args.report is not None:
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    findings = collect_findings(
        families,
        specimens,
        family_schema,
        specimen_schema,
        below_minimum,
        args.allow_below_minimum,
        args.verify_sources,
    )
    for name in FINDING_CLASSES:
        if findings[name]:
            for line in findings[name]:
                sys.stderr.write(f"check-family-evidence: {name}: {line}\n")
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run(args)
    except RefusalError as exc:
        sys.stderr.write(f"check-family-evidence: {exc}\n")
        return 2
    except OSError as exc:
        sys.stderr.write(f"check-family-evidence: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
