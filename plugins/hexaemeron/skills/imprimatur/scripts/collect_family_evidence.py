#!/usr/bin/env python3
"""Collect and annotate specimens for the structural-family-evidence-v1 fixture.

This is the executable form of the study's selection rule. It takes the pinned
default-branch heads and the merged ``wildcat-finance/skills`` pull request and
issue set as arguments, reads the six source kinds the specimen schema names
(Markdown paragraphs and commit messages reachable from each pinned head, and
the bodies and comments of the named repository's issues and merged pull
requests), excludes the 16 labelled-prose-v1 source groups, Imprimatur's own
files, vendored and mirrored trees and issue #1298, finds candidate paragraphs
by each family's ``discovery_phrases``, orders them by

    sha256("imprimatur-structural-family-evidence-v1" || source_url || text)

and takes them in that order until each family's tier minimum is met. Every
rejected candidate is written to ``selection-rejections.jsonl`` with its
reason, and the rejection counts are printed to standard output.

Text is fetched only through ``gh api`` at the pinned commits, with a fixed
argument list and no shell, and every fetched byte is treated as data: it is
never executed, evaluated or interpolated into a command. The annotator's
records are supplied by ``--annotations`` and are written before any lint
runs, which is what ``annotated_before_lint`` records on every shipped row.

Exit codes: 0 on a completed collection, 1 when a family cannot reach its tier
minimum from the universe given, 2 on a bad invocation or an unsafe read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

FIXTURE_SEED = "imprimatur-structural-family-evidence-v1"
FAMILIES_NAME = "families.jsonl"
SPECIMENS_NAME = "specimens.jsonl"
REJECTIONS_NAME = "selection-rejections.jsonl"
ISSUE_NAME = "issue-1298.md"

# The same host pin the checker's replay carries, and for the same reason:
# every endpoint below is a relative API path, and `gh` resolves a relative
# path against --hostname, then GH_HOST, then the working directory's own
# remote. Only the first of those is this collector's to state.
GH_HOSTNAME = "github.com"
GH_HOST_ENVIRONMENT = ("GH_HOST", "GH_REPO")
GH_TIMEOUT_SECONDS = 60
# One universe pass is a few thousand calls, so a transient answer is retried
# a bounded number of times rather than ending the pass. Only the statuses
# below are transient; every other non-zero exit is still a refusal.
GH_ATTEMPTS = 4
GH_RETRY_SECONDS = 5
GH_TRANSIENT_STATUS = ("HTTP 429", "HTTP 500", "HTTP 502", "HTTP 503", "HTTP 504")
MAX_FETCH_BYTES = 4_194_304
GITHUB_PREFIX = "https://github.com/"

# Word band and duplicate threshold are labelled-prose-v1's, quoted from its
# README: paragraphs carry 18 to 180 words, and a candidate is rejected when
# its word five-gram Jaccard similarity reaches 0.80 against a selected one.
MIN_WORDS = 18
MAX_WORDS = 180
JACCARD_LIMIT = 0.80
FIVEGRAM = 5

# Every value that becomes part of a gh endpoint fullmatches one pattern named
# here, before the endpoint is built. An argument with no row cannot reach gh.
ENDPOINT_SEGMENTS = {
    "repository": (
        re.compile(r"wildcat-finance/[A-Za-z0-9][A-Za-z0-9._-]*"),
        "repository is not one wildcat-finance repository",
    ),
    "source_path": (
        re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*"),
        "unusable source_path",
    ),
    "commit": (re.compile(r"[0-9a-f]{40}"), "unusable pinned commit"),
    "number": (re.compile(r"[0-9]{1,20}"), "unusable object number"),
}

# A paragraph is a run of consecutive non-blank lines. These first-line shapes
# are not prose: a heading, a table row, a quotation of other work, a rule, an
# indented code block and raw HTML. A list marker is prose with a marker, so
# the marker is dropped from the first line and the remainder stays an exact
# substring of the document.
NOT_PROSE_START = re.compile(r"^(?:#{1,6} |\||>|-{3,}\s*$|={3,}\s*$|    |\t|<)")
LIST_MARKER = re.compile(r"^(?:[-*+] |[0-9]+[.)] )")
FENCE = re.compile(r"^\s*(?:```|~~~)")
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’_-]*")
MARKDOWN_MARKER = re.compile(r"[*_`#\[\]()~>]")
HEX_LITERAL = re.compile(r"\b[0-9a-f]{40}\b|\b[0-9a-f]{64}\b")

# Directory names whose prose is vendored, generated or mirrored rather than
# written here. labelled-prose-v1 excludes vendored material and copied skill
# mirrors, and a mirror otherwise supplies a second "independent" source group
# for one document. A whole repository that mirrors another (skills-runtime
# carries the skills payload byte for byte) is left out of --head instead, and
# the fixture README records which ones and why.
VENDORED_SEGMENTS = frozenset(
    {"node_modules", "vendor", "third_party", "third-party", ".github", "lib", "build"}
)
IMPRIMATUR_OWN = "skills/imprimatur/"

# A tree whose own README says its prose is invented is not shipped prose, and
# a specimen taken there would be evidence of writing nobody published.
# `plugins/lemma/baseline/` in `skills` says of itself: "A small invented
# corpus", "Everything here is fabricated for the purpose", "None of it
# corresponds to a deployed system, and the prose is written to be chunked
# rather than to be read." It is the one tree in the universe that declares
# this, and it is named by repository and prefix rather than by a path segment
# so an unrelated directory called `baseline` is unaffected.
INVENTED_PROSE = (("wildcat-finance/skills", "plugins/lemma/baseline/"),)

REJECTION_REASONS = (
    "not-prose",
    "path-carries-whitespace",
    "vendored-or-mirrored-path",
    "invented-corpus",
    "imprimatur-own-prose",
    "excluded-issue",
    "unknown-thread",
    "v1-source-group",
    "outside-word-band",
    "table-row",
    "code-heavy",
    "generated-data",
    "quotes-the-issue",
    "duplicate-normalised",
    "duplicate-fivegram-jaccard",
    "group-already-used",
    "minimum-already-met",
    "annotator-rejected",
)

# Model-assistance evidence in a commit trailer, and labelled-prose-v1's
# maintainer rule for the human class. A trailer wins over the date, because
# affirmative evidence outranks the absence of it.
MODEL_TRAILERS = ("wildcat-origin:", "co-authored-by: shoggoth", "co-authored-by: claude")
HUMAN_CUTOFF = "2025-08-01T00:00:00Z"

TIER_MINIMUMS = {
    "high-value": (2, 2),
    "signal": (2, 1),
    "boundary": (0, 0),
    "existing-family": (0, 0),
    "future": (0, 0),
}
TARGET_TIERS = tuple(name for name, pair in TIER_MINIMUMS.items() if pair != (0, 0))

DECISION_FOR = {
    ("positive", "high-value"): "actionable",
    ("positive", "signal"): "signal_only",
}


class RefusalError(Exception):
    """A bad invocation or an unsafe read. The caller exits 2."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def candidate_digest(source_url: str, text: str) -> str:
    """The study's ordering key, and this collector's candidate identity.

    Ordering and identity are the same digest on purpose: an annotation names
    the candidate it was written against, so a candidate whose text or
    citation moved cannot silently inherit an annotation written for another.
    """
    return sha256_text(FIXTURE_SEED + source_url + text)


def segment(field: str, value: object) -> str:
    pattern, message = ENDPOINT_SEGMENTS[field]
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise RefusalError(f"{message}: {value!r}")
    return value


def gh_call(argv: list[str], allow_missing: bool) -> bytes | None:
    """Run one fixed-argv ``gh api`` call, retrying only a transient failure.

    The whole universe is one pass of a few thousand calls, and a single
    transient answer used to end it and discard everything already fetched: an
    HTTP 504 at document 900 of 1370 refused the run and wrote no corpus. A
    transient answer is retried a bounded number of times with a fixed wait,
    and every other non-zero exit stays the refusal it was. ``allow_missing``
    turns an HTTP 404 into ``None`` for the thread enumeration, which counts a
    number GitHub does not answer for as a hole in the sequence.

    Nothing here is retried on the strength of the reply's content: the
    decision reads only GitHub's own status line in ``gh``'s stderr, and the
    stderr text is never interpolated into a command.
    """
    if not argv or argv[0] != "api":
        raise RefusalError(f"refusing a gh call that is not `gh api`: {argv!r}")
    for value in argv:
        if value.startswith("-") and value not in ("-H",):
            raise RefusalError(f"refusing an option-shaped gh argument: {value!r}")
    environment = {
        name: value for name, value in os.environ.items() if name not in GH_HOST_ENVIRONMENT
    }
    last = ""
    for attempt in range(1, GH_ATTEMPTS + 1):
        try:
            completed = subprocess.run(  # noqa: S603 - fixed argv, shell=False
                ["gh", "api", "--hostname", GH_HOSTNAME, *argv[1:]],
                capture_output=True,
                shell=False,
                timeout=GH_TIMEOUT_SECONDS,
                check=False,
                env=environment,
            )
        except subprocess.TimeoutExpired as exc:
            last = f"gh call timed out after {GH_TIMEOUT_SECONDS}s"
            if attempt == GH_ATTEMPTS:
                raise RefusalError(f"{last} on {GH_ATTEMPTS} attempts") from exc
            time.sleep(GH_RETRY_SECONDS)
            continue
        except (OSError, subprocess.SubprocessError) as exc:
            raise RefusalError(f"gh call failed: {exc}") from exc
        if completed.returncode == 0:
            if len(completed.stdout) > MAX_FETCH_BYTES:
                raise RefusalError("gh returned more than the fetch cap allows")
            return completed.stdout
        detail = completed.stderr.decode("utf-8", "replace").strip()
        if allow_missing and "HTTP 404" in detail:
            return None
        last = f"gh exited {completed.returncode}: {detail[:200]}"
        if not any(status in detail for status in GH_TRANSIENT_STATUS):
            raise RefusalError(last)
        if attempt == GH_ATTEMPTS:
            raise RefusalError(f"{last} on {GH_ATTEMPTS} attempts")
        print(
            f"gh: transient answer on attempt {attempt} of {GH_ATTEMPTS}, retrying",
            file=sys.stderr,
        )
        time.sleep(GH_RETRY_SECONDS)
    raise RefusalError(last or "gh call made no attempt")


def gh_fetch(argv: list[str]) -> bytes:
    """Run one fixed-argv ``gh api`` call with no shell and a bounded result."""
    blob = gh_call(argv, allow_missing=False)
    if blob is None:  # pragma: no cover - allow_missing is False here
        raise RefusalError("gh returned no body")
    return blob


def gh_fetch_optional(argv: list[str]) -> bytes | None:
    """Like ``gh_fetch``, but an HTTP 404 is None rather than a refusal.

    Only the thread enumeration uses it: a number GitHub does not answer for
    is a hole in the sequence, and the enumeration records it and moves on.
    Every other failure stays a refusal.
    """
    return gh_call(argv, allow_missing=True)


def gh_json(argv: list[str]):
    blob = gh_fetch(argv)
    try:
        return json.loads(blob)
    except ValueError as exc:
        raise RefusalError(f"gh reply is not JSON: {exc}") from exc


def paragraphs(text: str) -> list[tuple[int, int, str]]:
    """Return every prose paragraph as ``(start_line, end_line, text)``.

    Lines are joined with the newline they already carry, and a list marker is
    dropped only from the first line, so the returned text stays an exact
    substring of ``text``. ``--verify-sources`` compares by substring, so a
    paragraph this function reshaped would be a row the checker cannot replay.
    """
    lines = text.split("\n")
    fenced = False
    block: list[str] = []
    start = 0
    out: list[tuple[int, int, str]] = []

    def flush(end: int) -> None:
        nonlocal block
        if block:
            out.append((start, end, "\n".join(block)))
            block = []

    for number, line in enumerate(lines, 1):
        if FENCE.match(line):
            fenced = not fenced
            flush(number - 1)
            continue
        if fenced:
            continue
        if not line.strip():
            flush(number - 1)
            continue
        if not block:
            if NOT_PROSE_START.match(line):
                continue
            start = number
            line = LIST_MARKER.sub("", line, count=1)
        block.append(line)
    flush(len(lines))
    return out


def words(text: str) -> list[str]:
    return WORD.findall(text)


def normalise(text: str) -> str:
    """labelled-prose-v1's duplicate normalisation: NFKC, lower, markers out."""
    folded = unicodedata.normalize("NFKC", text).lower()
    return " ".join(MARKDOWN_MARKER.sub(" ", folded).split())


def fivegrams(normalised: str) -> set[tuple[str, ...]]:
    tokens = normalised.split()
    return {tuple(tokens[index : index + FIVEGRAM]) for index in range(len(tokens) - FIVEGRAM + 1)}


def jaccard(left: set, right: set) -> float:
    if not left or not right:
        return 0.0
    union = len(left | right)
    return 0.0 if union == 0 else len(left & right) / union


def is_table(text: str) -> bool:
    return any(line.lstrip().startswith("|") or line.count("|") >= 2 for line in text.split("\n"))


def vendored(path: str) -> bool:
    """True when any directory on ``path`` is a vendored, generated or mirrored tree."""
    return any(segment in VENDORED_SEGMENTS for segment in path.split("/")[:-1])


def origin_from(message: str | None, date: str | None) -> str:
    """Classify one object's origin by labelled-prose-v1's rule.

    A model-assistance trailer in the message wins; otherwise a committer date
    before the cutoff is the maintainer rule for the human class; otherwise
    the origin is unknown. Thread bodies and comments carry no trailer and no
    committer date, so they are always unknown.
    """
    if isinstance(message, str):
        lowered = message.lower()
        if any(trailer in lowered for trailer in MODEL_TRAILERS):
            return "model_assisted"
    if isinstance(date, str) and date < HUMAN_CUTOFF:
        return "human"
    return "unknown"


def commit_detail(entry: object) -> tuple[str | None, str | None]:
    """The message and committer date of one commits-API reply.

    Three callers read a commit this way -- the commit half of the universe,
    a Markdown document's origin, and a shipped commit specimen's replay --
    and none of them defined it, so every one of the three raised
    ``NameError`` as soon as it reached a commit. The collector left in the
    tree therefore could not fetch the commit half of its own universe at all.

    Both the listing and the single-commit endpoint nest the two values under
    ``commit``, and the reply is data from outside: a field of the wrong type
    reads as absent here rather than reaching ``origin_from`` or a caller that
    expects a string.
    """
    if not isinstance(entry, dict):
        return None, None
    commit = entry.get("commit")
    if not isinstance(commit, dict):
        return None, None
    message = commit.get("message")
    committer = commit.get("committer")
    date = committer.get("date") if isinstance(committer, dict) else None
    return (
        message if isinstance(message, str) else None,
        date if isinstance(date, str) else None,
    )


def code_ratio(text: str) -> float:
    """The share of characters inside inline code spans."""
    inside = sum(len(span) for span in re.findall(r"`([^`]*)`", text))
    return inside / len(text) if text else 0.0


def v1_exclusions(samples: Path) -> tuple[set[str], set[tuple[str, str]], set[tuple[str, str]]]:
    """Read the 16 v1 source groups from the v1 sample file, and nothing else.

    Only ``samples.jsonl`` is opened, and only its provenance fields are read.
    The v1 label, adjudication and split files are never opened by this
    collector: reading them while choosing specimens is the ``holdout-leak``
    item in the study's register, so the path is refused by name rather than
    left to whoever passes the argument.
    """
    if samples.name != "samples.jsonl":
        raise RefusalError(
            f"--v1-samples must name the v1 sample file, not {samples.name!r}; "
            "no v1 label, adjudication or split file may be opened here"
        )
    if samples.is_symlink():
        raise RefusalError(f"symlink refused: {samples}")
    groups: set[str] = set()
    documents: set[tuple[str, str]] = set()
    commits: set[tuple[str, str]] = set()
    for number, line in enumerate(samples.read_text(encoding="utf-8").split("\n"), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            raise RefusalError(f"unreadable JSON at {samples.name}:{number}: {exc}") from exc
        if not isinstance(row, dict):
            raise RefusalError(f"row at {samples.name}:{number} is not an object")
        group = row.get("source_group_id")
        repository = row.get("repository")
        if isinstance(group, str):
            groups.add(group)
        if not isinstance(repository, str):
            continue
        path = row.get("source_path")
        if isinstance(path, str):
            documents.add((repository, path))
        commit = row.get("source_commit")
        if isinstance(commit, str):
            commits.add((repository, commit))
    return groups, documents, commits


def parse_head(value: str) -> tuple[str, str]:
    if value.count("=") != 1:
        raise RefusalError(f"--head wants one repository=commit pair: {value!r}")
    repository, commit = value.split("=", 1)
    return segment("repository", repository), segment("commit", commit)


def fetch_tree(repository: str, commit: str) -> list[str]:
    reply = gh_json(["api", f"repos/{repository}/git/trees/{commit}?recursive=1"])
    if not isinstance(reply, dict) or not isinstance(reply.get("tree"), list):
        raise RefusalError(f"tree reply for {repository}@{commit} carries no tree")
    if reply.get("truncated") is True:
        raise RefusalError(
            f"tree for {repository}@{commit} came back truncated, so the document "
            "set would be partial and the selection unreproducible"
        )
    paths = []
    for entry in reply["tree"]:
        if not isinstance(entry, dict) or entry.get("type") != "blob":
            continue
        path = entry.get("path")
        if isinstance(path, str) and path.endswith(".md"):
            paths.append(path)
    return sorted(paths)


def fetch_document(repository: str, commit: str, path: str) -> str:
    blob = gh_fetch(
        [
            "api",
            "-H",
            "Accept: application/vnd.github.raw",
            f"repos/{repository}/contents/{path}?ref={commit}",
        ]
    )
    return blob.decode("utf-8", "replace")


def thread_ceiling(repository: str) -> int:
    """The highest issue or pull request number GitHub answers for.

    The listing's first page, newest first, names a candidate; the numbers
    above it are then probed one by one until GitHub returns 404, so a thread
    the listing omitted at the top cannot lower the ceiling.
    """
    reply = gh_json(
        ["api", f"repos/{repository}/issues?state=all&per_page=1&sort=created&direction=desc"]
    )
    if not isinstance(reply, list) or not reply or not isinstance(reply[0], dict):
        raise RefusalError(f"issue listing for {repository} names no newest thread")
    highest = reply[0].get("number")
    if not isinstance(highest, int) or isinstance(highest, bool):
        raise RefusalError(f"issue listing for {repository} carries no number")
    while gh_fetch_optional(["api", f"repos/{repository}/issues/{highest + 1}"]) is not None:
        highest += 1
    return highest


def fetch_threads(repository: str) -> list[dict]:
    """Every issue and merged pull request in ``repository``, with its body.

    Threads are read one number at a time from 1 to the ceiling above, not
    from the listing endpoint. On 2026-09-09 that listing returned 692 of the
    repository's 1,181 threads, its first page held 53 items on one call and
    100 on the next, and the numbers it dropped included the newest pull
    requests; a universe read from it would differ between two runs minutes
    apart. A number GitHub answers 404 for is counted and skipped, and the
    count is printed so the record says how many holes the sequence had.
    Enumerating the whole sequence also keeps the universe the repository's
    own set rather than a list somebody chose after seeing which items
    carried a family.
    """
    out: list[dict] = []
    ceiling = thread_ceiling(repository)
    missing = 0
    for number in range(1, ceiling + 1):
        blob = gh_fetch_optional(["api", f"repos/{repository}/issues/{number}"])
        if blob is None:
            missing += 1
            continue
        try:
            item = json.loads(blob)
        except ValueError as exc:
            raise RefusalError(f"thread {number} reply is not JSON: {exc}") from exc
        if not isinstance(item, dict) or item.get("number") != number:
            raise RefusalError(f"thread {number} reply does not name itself")
        body = item.get("body")
        if not isinstance(body, str):
            body = ""
        pull = item.get("pull_request")
        if isinstance(pull, dict):
            if not pull.get("merged_at"):
                continue
            out.append({"kind": "pull", "number": number, "body": body})
        else:
            out.append({"kind": "issue", "number": number, "body": body})
        if number % 200 == 0 or number == ceiling:
            print(f"threads: read {number} of {ceiling}", file=sys.stderr)
    print(
        f"threads: {len(out)} admitted from {ceiling} numbers, {missing} returned 404",
        file=sys.stderr,
    )
    return sorted(out, key=lambda row: row["number"])


def fetch_origin(repository: str, commit: str, path: str) -> str:
    """Classify one document's origin from the commit that last touched it."""
    reply = gh_json(
        ["api", f"repos/{repository}/commits?sha={commit}&path={path}&per_page=1"]
    )
    if not isinstance(reply, list) or not reply or not isinstance(reply[0], dict):
        return "unknown"
    return origin_from(*commit_detail(reply[0]))


def fetch_commits(repository: str, commit: str) -> list[dict]:
    """Every commit reachable from the pinned head, with its message and date.

    The listing walks history from the pinned commit, so the set is fixed by
    the head and not by whatever the default branch points at later. A merge
    commit is kept: its message is usually one line and falls outside the word
    band on its own.
    """
    out: list[dict] = []
    page = 1
    while True:
        reply = gh_json(
            ["api", f"repos/{repository}/commits?sha={commit}&per_page=100&page={page}"]
        )
        if not isinstance(reply, list):
            raise RefusalError(f"commit listing for {repository}@{commit} is not a list")
        if not reply:
            break
        for entry in reply:
            if not isinstance(entry, dict):
                continue
            sha = entry.get("sha")
            message, date = commit_detail(entry)
            if not isinstance(sha, str) or message is None:
                continue
            out.append({"sha": sha, "message": message, "date": date})
        page += 1
    return out


def fetch_comments(repository: str, threads: dict[int, str]) -> list[dict]:
    """Every comment on a thread in ``threads``: conversation and review comments.

    ``threads`` maps a number to ``issue`` or ``pull`` for the threads already
    admitted to the universe, so a comment on an unmerged pull request or an
    excluded issue is dropped here with the thread it belongs to.
    """
    out: list[dict] = []
    for collection, key, fragment in (
        ("issues", "issue_url", "issuecomment-"),
        ("pulls", "pull_request_url", "discussion_r"),
    ):
        page = 1
        while True:
            reply = gh_json(
                ["api", f"repos/{repository}/{collection}/comments?per_page=100&page={page}"]
            )
            if not isinstance(reply, list):
                raise RefusalError(f"{collection} comment listing for {repository} is not a list")
            if not reply:
                break
            for item in reply:
                if not isinstance(item, dict):
                    continue
                identifier = item.get("id")
                body = item.get("body")
                thread_url = item.get(key)
                if (not isinstance(identifier, int) or isinstance(identifier, bool)
                        or not isinstance(body, str) or not isinstance(thread_url, str)):
                    continue
                tail = thread_url.rstrip("/").rsplit("/", 1)[-1]
                if not tail.isdigit():
                    continue
                number = int(tail)
                kind = threads.get(number)
                out.append(
                    {
                        "number": number,
                        "thread": kind,
                        "comment": identifier,
                        "fragment": f"{fragment}{identifier}",
                        "body": body,
                    }
                )
            page += 1
    return sorted(out, key=lambda row: (row["number"], row["comment"]))


def corpus_from_network(args: argparse.Namespace) -> list[dict]:
    """Fetch every document and thread body in the universe, through gh api."""
    documents: list[dict] = []
    for repository, commit in args.head:
        for path in fetch_tree(repository, commit):
            documents.append(
                {
                    "kind": "markdown_paragraph",
                    "repository": repository,
                    "commit": commit,
                    "path": path,
                    "number": None,
                    "comment": None,
                    "fragment": None,
                    "date": None,
                    "text": "",
                }
            )
    total = len(documents)
    for index, document in enumerate(documents, 1):
        document["text"] = fetch_document(
            document["repository"], document["commit"], document["path"]
        )
        if index % 100 == 0 or index == total:
            print(f"corpus: fetched {index} of {total} documents", file=sys.stderr)
    for repository, commit in args.head:
        for entry in fetch_commits(repository, commit):
            documents.append(
                {
                    "kind": "commit_message",
                    "repository": repository,
                    "commit": entry["sha"],
                    "path": None,
                    "number": None,
                    "comment": None,
                    "fragment": None,
                    "date": entry["date"],
                    "text": entry["message"],
                }
            )
    for repository, commit in args.head:
        if repository not in args.threads:
            continue
        listed = fetch_threads(repository)
        threads = {row["number"]: row["kind"] for row in listed}
        bodies = {repository: {row["number"]: row["body"] for row in listed}}
        for number in sorted(threads):
            kind = threads[number]
            documents.append(
                {
                    "kind": "issue_body" if kind == "issue" else "pull_request_body",
                    "repository": repository,
                    "commit": commit,
                    "path": None,
                    "number": number,
                    "comment": None,
                    "fragment": None,
                    "date": None,
                    "text": bodies[repository][number],
                }
            )
        for row in fetch_comments(repository, threads):
            documents.append(
                {
                    "kind": "issue_comment" if row["thread"] == "issue" else "pull_request_comment",
                    "repository": repository,
                    "commit": commit,
                    "path": None,
                    "number": row["number"],
                    "comment": row["comment"],
                    "fragment": row["fragment"],
                    "date": None,
                    # A comment whose thread is not in the universe is carried
                    # with thread None and rejected below as unknown-thread,
                    # so the rejection record says it was seen and dropped.
                    "thread": row["thread"],
                    "text": row["body"],
                }
            )
    return documents


def read_corpus(path: Path) -> list[dict]:
    """Read a corpus this collector wrote, checking each record's own digest.

    A corpus file is the recorded result of the one network pass, so it is
    read back the way any other outside input is: shape first, then the digest
    the writer stored beside the text. Every specimen that is actually shipped
    is re-fetched from its endpoint before the row is written, so a corpus can
    shorten a rerun but cannot decide a shipped row's provenance.
    """
    if path.is_symlink():
        raise RefusalError(f"symlink refused: {path}")
    documents: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            raise RefusalError(f"unreadable JSON at {path.name}:{number}: {exc}") from exc
        if not isinstance(row, dict):
            raise RefusalError(f"row at {path.name}:{number} is not an object")
        text = row.get("text")
        digest = row.get("text_sha256")
        if not isinstance(text, str) or not isinstance(digest, str):
            raise RefusalError(f"corpus row at {path.name}:{number} carries no text and digest")
        if sha256_text(text) != digest:
            raise RefusalError(f"corpus row at {path.name}:{number} does not match its digest")
        documents.append(row)
    return documents


def write_corpus(path: Path, documents: list[dict]) -> None:
    rows = [
        {**document, "text_sha256": sha256_text(document["text"])}
        for document in documents
    ]
    write_jsonl_atomic(path, rows)


def write_jsonl_atomic(path: Path, rows: list[dict]) -> None:
    """Write JSON Lines through a temporary file in the same directory.

    A collection that dies half way through otherwise leaves a file whose rows
    are valid and whose content is partial, which is the ``partial-write`` item
    in the study's register. The rename is atomic on one filesystem, so a
    reader sees either the previous file or the whole new one.
    """
    body = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    temporary = path.with_name(path.name + ".partial")
    temporary.write_text(body, encoding="utf-8")
    os.replace(temporary, path)


def source_of(document: dict, first: int, last: int) -> dict:
    """Return the citation and group a candidate inherits from its document."""
    repository = document["repository"]
    if document["kind"] == "markdown_paragraph":
        path = document["path"]
        return {
            "source_object": "markdown_paragraph",
            "source_path": path,
            "source_url": f"{GITHUB_PREFIX}{repository}/blob/{document['commit']}/{path}#L{first}-L{last}",
            "source_group_id": f"{repository}:{path}",
        }
    if document["kind"] == "commit_message":
        return {
            "source_object": "commit_message",
            "source_path": None,
            "source_url": f"{GITHUB_PREFIX}{repository}/commit/{document['commit']}",
            "source_group_id": f"{repository}:commit/{document['commit']}",
        }
    collection = "issues" if document["kind"] in ("issue_body", "issue_comment") else "pull"
    number = document["number"]
    url = f"{GITHUB_PREFIX}{repository}/{collection}/{number}"
    if document["kind"] in ("issue_comment", "pull_request_comment"):
        url = f"{url}#{document['fragment']}"
    # A comment and the body of its thread are one document: the thread is
    # the unit a reader follows, so it is the unit independence counts.
    return {
        "source_object": document["kind"],
        "source_path": None,
        "source_url": url,
        "source_group_id": f"{repository}:{collection}/{number}",
    }


def document_rejection(document: dict, excluded_issues: set[int],
                       v1_documents: set[tuple[str, str]],
                       v1_commits: set[tuple[str, str]]) -> str | None:
    """Return why a whole document is outside the universe, or None."""
    repository = document["repository"]
    path = document["path"]
    if document["kind"] == "commit_message":
        if (repository, document["commit"]) in v1_commits:
            return "v1-source-group"
        return None
    if document["kind"] != "markdown_paragraph":
        if document.get("number") in excluded_issues:
            return "excluded-issue"
        if document["kind"] in ("issue_comment", "pull_request_comment") and \
                document.get("thread") not in ("issue", "pull"):
            return "unknown-thread"
        return None
    if not isinstance(path, str):
        return "not-prose"
    if IMPRIMATUR_OWN in path:
        return "imprimatur-own-prose"
    if vendored(path):
        return "vendored-or-mirrored-path"
    if any(repository == owner and path.startswith(prefix)
           for owner, prefix in INVENTED_PROSE):
        return "invented-corpus"
    if (repository, path) in v1_documents:
        return "v1-source-group"
    if (repository, document["commit"]) in v1_commits:
        return "v1-source-group"
    # A source group is repository plus document, and a group id carrying
    # whitespace is refused by the checker, because two ids differing by a
    # space read as one group on screen and as two in the independence count.
    if any(character.isspace() for character in path):
        return "path-carries-whitespace"
    try:
        segment("source_path", path)
    except RefusalError:
        return "path-carries-whitespace"
    return None


def paragraph_rejection(text: str, issue_body: str) -> str | None:
    """Return why one paragraph cannot be a specimen, or None."""
    count = len(words(text))
    if not MIN_WORDS <= count <= MAX_WORDS:
        return "outside-word-band"
    if is_table(text):
        return "table-row"
    if code_ratio(text) > 0.30:
        return "code-heavy"
    if HEX_LITERAL.search(text):
        return "generated-data"
    if normalise(text) and normalise(text) in normalise(issue_body):
        return "quotes-the-issue"
    return None


def build_candidates(families: list[dict], documents: list[dict], issue_body: str,
                     excluded_issues: set[int], v1_documents: set[tuple[str, str]],
                     v1_commits: set[tuple[str, str]]) -> tuple[list[dict], list[dict]]:
    """Return the ordered candidates per family and every rejection so far."""
    rejections: list[dict] = []
    candidates: list[dict] = []
    phrases = {
        row["family_id"]: tuple(row["discovery_phrases"])
        for row in families
        if row["discovery_phrases"]
    }
    for document in documents:
        reason = document_rejection(document, excluded_issues, v1_documents, v1_commits)
        if reason is not None:
            rejections.append(
                {
                    "candidate_id": None,
                    "family_id": None,
                    "repository": document["repository"],
                    "source_path": document["path"],
                    "source_object": document["kind"],
                    "source_start_line": None,
                    "source_end_line": None,
                    "words": None,
                    "reason": reason,
                    "detail": "whole document excluded from the universe",
                }
            )
            continue
        for first, last, text in paragraphs(document["text"]):
            matched = [
                family_id
                for family_id, family_phrases in phrases.items()
                if any(phrase in text for phrase in family_phrases)
            ]
            if not matched:
                continue
            citation = source_of(document, first, last)
            reason = paragraph_rejection(text, issue_body)
            # A commit's origin is read from its whole message and committer
            # date here, where the whole message is still to hand; the
            # candidate carries only its own paragraph.
            origin = "unknown"
            if document["kind"] == "commit_message":
                origin = origin_from(document["text"], document.get("date"))
            row = {
                "candidate_id": candidate_digest(citation["source_url"], text),
                "repository": document["repository"],
                "source_commit": document["commit"],
                "date": document.get("date"),
                "origin": origin,
                "source_start_line": first,
                "source_end_line": last,
                "words": len(words(text)),
                "text": text,
                **citation,
            }
            for family_id in sorted(matched):
                if reason is not None:
                    rejections.append(
                        {
                            "candidate_id": row["candidate_id"],
                            "family_id": family_id,
                            "repository": row["repository"],
                            "source_path": row["source_path"],
                            "source_object": row["source_object"],
                            "source_start_line": first,
                            "source_end_line": last,
                            "words": row["words"],
                            "reason": reason,
                            "detail": "paragraph outside the selection rule",
                        }
                    )
                    continue
                candidates.append({**row, "family_id": family_id})
    candidates.sort(key=lambda row: (row["family_id"], row["candidate_id"]))
    return candidates, rejections


def rejection_row(candidate: dict, reason: str, detail: str) -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "family_id": candidate["family_id"],
        "repository": candidate["repository"],
        "source_path": candidate["source_path"],
        "source_object": candidate["source_object"],
        "source_start_line": candidate["source_start_line"],
        "source_end_line": candidate["source_end_line"],
        "words": candidate["words"],
        "reason": reason,
        "detail": detail,
    }


def read_annotations(path: Path) -> dict[tuple[str, str], dict]:
    """Read the annotator's records, keyed by family and candidate.

    One paragraph can be a candidate for two families when it carries both
    families' phrases, and the two annotations differ: the same sentence is a
    positive for one move and a negative for the other. The key is therefore
    the pair, and a record naming no family is refused rather than guessed.
    """
    if path.is_symlink():
        raise RefusalError(f"symlink refused: {path}")
    out: dict[tuple[str, str], dict] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            raise RefusalError(f"unreadable JSON at {path.name}:{number}: {exc}") from exc
        if not isinstance(row, dict):
            raise RefusalError(f"row at {path.name}:{number} is not an object")
        identifier = row.get("candidate_id")
        family_id = row.get("family_id")
        if not isinstance(identifier, str):
            raise RefusalError(f"annotation at {path.name}:{number} names no candidate_id")
        if not isinstance(family_id, str):
            raise RefusalError(f"annotation at {path.name}:{number} names no family_id")
        if (family_id, identifier) in out:
            raise RefusalError(
                f"annotation at {path.name}:{number} repeats {identifier} for {family_id}"
            )
        out[(family_id, identifier)] = row
    return out


def check_annotation(annotation: dict, candidate: dict, tier: str) -> None:
    """Refuse an annotation whose own fields disagree with each other.

    Four row-level rules the checker declares required and leaves to this step
    are enforced here, where the row is written, because the runbook's Files
    list does not include the checker: a decision has to follow the polarity
    and the family's tier, an actionable or signal row has to carry a rewrite,
    a negative has to carry none, and the line range has to be ordered.
    """
    polarity = annotation.get("polarity")
    if polarity not in ("positive", "negative"):
        raise RefusalError(f"{candidate['candidate_id']}: polarity is not positive or negative")
    decision = annotation.get("decision")
    expected = DECISION_FOR.get((polarity, tier), "negative" if polarity == "negative" else None)
    if expected is None:
        raise RefusalError(
            f"{candidate['candidate_id']}: a positive on tier {tier} carries no decision this step writes"
        )
    if decision != expected:
        raise RefusalError(
            f"{candidate['candidate_id']}: decision {decision!r} does not follow "
            f"polarity {polarity!r} on tier {tier!r}, which is {expected!r}"
        )
    reason = annotation.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise RefusalError(f"{candidate['candidate_id']}: reason is empty")
    rewrite = annotation.get("rewrite")
    if decision == "negative":
        if rewrite is not None:
            raise RefusalError(
                f"{candidate['candidate_id']}: a negative specimen carries no rewrite"
            )
    elif not isinstance(rewrite, str) or not rewrite.strip():
        raise RefusalError(
            f"{candidate['candidate_id']}: an {decision} specimen needs a content-preserving rewrite"
        )
    start = annotation.get("start_byte")
    end = annotation.get("end_byte")
    blob = candidate["text"].encode("utf-8")
    for name, value in (("start_byte", start), ("end_byte", end)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise RefusalError(f"{candidate['candidate_id']}: {name} is not an integer")
    if not 0 <= start < end <= len(blob):
        raise RefusalError(
            f"{candidate['candidate_id']}: span {start}:{end} is not inside the {len(blob)}-byte text"
        )
    try:
        blob[start:end].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RefusalError(f"{candidate['candidate_id']}: span splits a UTF-8 codepoint") from exc
    if candidate["source_start_line"] > candidate["source_end_line"]:
        raise RefusalError(
            f"{candidate['candidate_id']}: source_start_line is after source_end_line"
        )


def select(families: list[dict], candidates: list[dict],
           annotations: dict[tuple[str, str], dict],
           verify: bool) -> tuple[list[dict], list[dict], list[dict]]:
    """Walk each family's candidates in digest order and take what is annotated."""
    specimens: list[dict] = []
    rejections: list[dict] = []
    shortfalls: list[dict] = []
    tiers = {row["family_id"]: row["evidence_tier"] for row in families}
    by_family: dict[str, list[dict]] = {}
    for candidate in candidates:
        by_family.setdefault(candidate["family_id"], []).append(candidate)

    for family in families:
        family_id = family["family_id"]
        tier = family["evidence_tier"]
        minimum_positive, minimum_negative = TIER_MINIMUMS[tier]
        if (minimum_positive, minimum_negative) == (0, 0):
            continue
        taken_positive: dict[str, str] = {}
        taken_negative = 0
        selected_fivegrams: list[set] = []
        selected_normalised: set[str] = set()
        rank = 0
        for candidate in by_family.get(family_id, []):
            met = len(taken_positive) >= minimum_positive and taken_negative >= minimum_negative
            annotation = annotations.get((family_id, candidate["candidate_id"]))
            if met:
                rejections.append(rejection_row(candidate, "minimum-already-met",
                                                "the family's tier minimum was already met"))
                continue
            if annotation is None:
                rejections.append(rejection_row(candidate, "annotator-rejected",
                                                "no annotation was written for this candidate"))
                continue
            if annotation.get("select") is False:
                detail = annotation.get("reason")
                rejections.append(rejection_row(candidate, "annotator-rejected",
                                                detail if isinstance(detail, str) else
                                                "the annotator did not take this candidate"))
                continue
            # One side of the minimum can be met while the other is still
            # open. A candidate annotated on the met side is not shipped, and
            # its annotation is kept in the rejection so the record says the
            # annotator read it and what it was.
            polarity = annotation.get("polarity")
            if polarity == "negative" and taken_negative >= minimum_negative:
                rejections.append(rejection_row(
                    candidate, "minimum-already-met",
                    "annotated negative; the family's negative minimum was already met"))
                continue
            if polarity == "positive" and len(taken_positive) >= minimum_positive:
                rejections.append(rejection_row(
                    candidate, "minimum-already-met",
                    "annotated positive; the family's independent-positive minimum was already met"))
                continue
            normalised = normalise(candidate["text"])
            if normalised in selected_normalised:
                rejections.append(rejection_row(candidate, "duplicate-normalised",
                                                "normalised text equals a selected specimen"))
                continue
            grams = fivegrams(normalised)
            nearest = max((jaccard(grams, other) for other in selected_fivegrams), default=0.0)
            if nearest >= JACCARD_LIMIT:
                rejections.append(rejection_row(
                    candidate, "duplicate-fivegram-jaccard",
                    f"five-gram Jaccard {nearest:.4f} against a selected specimen"))
                continue
            if polarity == "positive" and candidate["source_group_id"] in taken_positive:
                rejections.append(rejection_row(
                    candidate, "group-already-used",
                    f"a positive from {candidate['source_group_id']} is already taken"))
                continue
            check_annotation(annotation, candidate, tier)
            rank += 1
            specimens.append(build_specimen(candidate, annotation, family_id, rank, verify))
            selected_fivegrams.append(grams)
            selected_normalised.add(normalised)
            if polarity == "positive":
                taken_positive[candidate["source_group_id"]] = candidate["candidate_id"]
            else:
                taken_negative += 1
        if len(taken_positive) < minimum_positive or taken_negative < minimum_negative:
            shortfalls.append(
                {
                    "family_id": family_id,
                    "evidence_tier": tier,
                    "independent_positives": len(taken_positive),
                    "negatives": taken_negative,
                    "minimum_positive": minimum_positive,
                    "minimum_negative": minimum_negative,
                    "candidates": len(by_family.get(family_id, [])),
                }
            )
    del tiers
    return specimens, rejections, shortfalls


def build_specimen(candidate: dict, annotation: dict, family_id: str, rank: int,
                   verify: bool) -> dict:
    """Assemble one shipped row, re-fetching its object when asked to."""
    identifier = annotation.get("specimen_id")
    if not isinstance(identifier, str):
        raise RefusalError(f"{candidate['candidate_id']}: annotation names no specimen_id")
    origin = candidate.get("origin", "unknown")
    if verify:
        replayed, date = replay(candidate)
        if candidate["text"] not in replayed:
            raise RefusalError(
                f"{identifier}: text is absent from the replayed object "
                f"{candidate['source_url']}"
            )
        if candidate["source_object"] == "markdown_paragraph":
            origin = fetch_origin(candidate["repository"], candidate["source_commit"],
                                  candidate["source_path"])
        elif candidate["source_object"] == "commit_message":
            origin = origin_from(replayed, date)
    return {
        "specimen_id": identifier,
        "family_id": family_id,
        "tier": "structural",
        "family": family_id,
        "polarity": annotation["polarity"],
        "decision": annotation["decision"],
        "text": candidate["text"],
        "text_sha256": sha256_text(candidate["text"]),
        "start_byte": annotation["start_byte"],
        "end_byte": annotation["end_byte"],
        "reason": annotation["reason"],
        "rewrite": annotation["rewrite"],
        "repository": candidate["repository"],
        "source_url": candidate["source_url"],
        "source_commit": candidate["source_commit"],
        "source_path": candidate["source_path"],
        "source_start_line": candidate["source_start_line"],
        "source_end_line": candidate["source_end_line"],
        "source_object": candidate["source_object"],
        "source_group_id": candidate["source_group_id"],
        "origin": origin,
        "annotated_before_lint": True,
        "selection_seed": FIXTURE_SEED,
        "selection_rank_within_group": rank,
    }


def replay(candidate: dict) -> tuple[str, str | None]:
    """Re-fetch one candidate's own object, through the checker's endpoints.

    Returns the object's text and, for a commit, its committer date. The four
    thread kinds replay a live body, as the checker's own documentation says;
    a Markdown file at ``?ref=<sha>`` and a commit by its sha are immutable.
    """
    repository = segment("repository", candidate["repository"])
    commit = segment("commit", candidate["source_commit"])
    kind = candidate["source_object"]
    if kind == "markdown_paragraph":
        return fetch_document(repository, commit, segment("source_path", candidate["source_path"])), None
    if kind == "commit_message":
        reply = gh_json(["api", f"repos/{repository}/commits/{commit}"])
        message, date = commit_detail(reply) if isinstance(reply, dict) else (None, None)
        if message is None:
            raise RefusalError(f"commit {commit} carries no message")
        return message, date
    url = candidate["source_url"]
    path, _, fragment = url.partition("#")
    if kind in ("issue_comment", "pull_request_comment"):
        prefix = "issuecomment-" if fragment.startswith("issuecomment-") else "discussion_r"
        if not fragment.startswith(prefix):
            raise RefusalError(f"cannot read a comment id from {url}")
        comment = segment("number", fragment[len(prefix):])
        collection = "issues" if prefix == "issuecomment-" else "pulls"
        reply = gh_json(["api", f"repos/{repository}/{collection}/comments/{comment}"])
    else:
        number = segment("number", path.rstrip("/").rsplit("/", 1)[-1])
        reply = gh_json(["api", f"repos/{repository}/issues/{number}"])
    body = reply.get("body") if isinstance(reply, dict) else None
    if body is None:
        return "", None
    if not isinstance(body, str):
        raise RefusalError(f"body behind {url} is not a string")
    return body, None


def read_families(fixture: Path) -> list[dict]:
    rows: list[dict] = []
    text = (fixture / FAMILIES_NAME).read_text(encoding="utf-8")
    for number, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            raise RefusalError(f"unreadable JSON at {FAMILIES_NAME}:{number}: {exc}") from exc
        for key in ("family_id", "evidence_tier", "discovery_phrases"):
            if key not in row:
                raise RefusalError(f"{FAMILIES_NAME}:{number} carries no {key}")
        if row["evidence_tier"] not in TIER_MINIMUMS:
            raise RefusalError(f"{FAMILIES_NAME}:{number}: unknown evidence_tier")
        if not isinstance(row["discovery_phrases"], list):
            raise RefusalError(f"{FAMILIES_NAME}:{number}: discovery_phrases is not a list")
        # A target family with no phrase can never reach its minimum, and the
        # shortfall would read as an absent corpus rather than an absent rule.
        if row["evidence_tier"] in TARGET_TIERS and not row["discovery_phrases"]:
            raise RefusalError(
                f"{FAMILIES_NAME}:{number}: {row['family_id']} is on tier "
                f"{row['evidence_tier']} and records no discovery_phrases"
            )
        rows.append(row)
    return rows


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect specimens for the structural-family-evidence-v1 fixture."
    )
    parser.add_argument("--fixture", type=Path, required=True,
                        help="fixture directory; specimens and rejections are written here")
    parser.add_argument("--head", action="append", default=[], metavar="REPOSITORY=COMMIT",
                        help="a pinned default-branch head; repeatable and required")
    parser.add_argument("--threads", action="append", default=[], metavar="REPOSITORY",
                        help="a repository whose issues and merged pull requests join the universe")
    parser.add_argument("--v1-samples", type=Path, required=True,
                        help="labelled-prose-v1/samples.jsonl; only its provenance fields are read")
    parser.add_argument("--exclude-issue", action="append", type=int, default=[],
                        help="an issue number outside the universe; #1298 is always excluded")
    parser.add_argument("--annotations", type=Path,
                        help="the annotator's records; without it no specimens.jsonl is written")
    parser.add_argument("--candidates-out", type=Path,
                        help="write the ordered candidate list for the annotator")
    parser.add_argument("--corpus-out", type=Path,
                        help="record the fetched universe, so a rerun need not fetch it again")
    parser.add_argument("--corpus-in", type=Path,
                        help="read a recorded universe instead of fetching it")
    parser.add_argument("--no-verify", action="store_true",
                        help="skip the per-specimen replay; a shipped fixture is built without it")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    fixture = args.fixture.resolve()
    if args.fixture.is_symlink():
        raise RefusalError(f"symlink refused: {args.fixture}")
    if not fixture.is_dir():
        raise RefusalError(f"not a fixture directory: {args.fixture}")
    # The pinned heads are what makes the selection reproducible, so a run
    # without one is refused rather than defaulted to a branch name that moves.
    if not args.head:
        raise RefusalError("--head is required: this collector fetches only at pinned commits")
    if args.corpus_in is not None and args.corpus_out is not None:
        raise RefusalError("--corpus-in and --corpus-out name opposite halves of one pass")
    args.head = [parse_head(value) for value in args.head]
    args.threads = {segment("repository", value) for value in args.threads}
    pinned = {repository for repository, _ in args.head}
    unpinned = sorted(args.threads - pinned)
    if unpinned:
        raise RefusalError(f"--threads names {unpinned}, which no --head pins")

    families = read_families(fixture)
    groups, v1_documents, v1_commits = v1_exclusions(args.v1_samples)
    excluded_issues = {1298, *args.exclude_issue}
    issue_body = (fixture / ISSUE_NAME).read_text(encoding="utf-8")

    if args.corpus_in is not None:
        documents = read_corpus(args.corpus_in)
    else:
        documents = corpus_from_network(args)
        if args.corpus_out is not None:
            write_corpus(args.corpus_out, documents)

    candidates, rejections = build_candidates(
        families, documents, issue_body, excluded_issues, v1_documents, v1_commits
    )
    if args.candidates_out is not None:
        write_jsonl_atomic(args.candidates_out, candidates)

    annotations = read_annotations(args.annotations) if args.annotations is not None else {}
    specimens, more, shortfalls = select(
        families, candidates, annotations, not args.no_verify
    )
    rejections.extend(more)

    # No specimen may share a source group with any of the 16 v1 groups. The
    # exclusion above works on documents; this compares the ids themselves, so
    # a group derived another way still cannot collide with the spent holdout.
    collisions = sorted({row["source_group_id"] for row in specimens} & groups)
    if collisions:
        raise RefusalError(f"specimens share a v1 source group: {collisions}")

    write_jsonl_atomic(fixture / REJECTIONS_NAME, rejections)
    if args.annotations is not None:
        write_jsonl_atomic(fixture / SPECIMENS_NAME, specimens)

    counts: dict[str, int] = {}
    for row in rejections:
        counts[row["reason"]] = counts.get(row["reason"], 0) + 1
    print(f"candidates: {len(candidates)}")
    print(f"specimens: {len(specimens)}")
    print(f"rejections: {len(rejections)}")
    for reason in REJECTION_REASONS:
        if reason in counts:
            print(f"  {reason}: {counts[reason]}")
    for reason in sorted(set(counts) - set(REJECTION_REASONS)):
        print(f"  {reason}: {counts[reason]}")
    for entry in shortfalls:
        print(
            f"below minimum: {entry['family_id']} ({entry['evidence_tier']}) has "
            f"{entry['independent_positives']} independent positive and "
            f"{entry['negatives']} negative specimens against "
            f"{entry['minimum_positive']} and {entry['minimum_negative']}, "
            f"from {entry['candidates']} candidates",
            file=sys.stderr,
        )
    return 1 if shortfalls else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run(args)
    except RefusalError as exc:
        sys.stderr.write(f"collect-family-evidence: {exc}\n")
        return 2
    except OSError as exc:
        sys.stderr.write(f"collect-family-evidence: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
