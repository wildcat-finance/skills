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
import re
import subprocess
import sys
from pathlib import Path

FIXTURE_SEED = "imprimatur-structural-family-evidence-v1"
MAX_FILE_BYTES = 1_048_576
GH_TIMEOUT_SECONDS = 30
MAX_FETCH_BYTES = 4_194_304
TIERS = ("high-value", "signal", "boundary", "existing-family", "future")
TIER_MINIMUMS = {
    "high-value": (2, 2),
    "signal": (2, 1),
    "boundary": (0, 0),
    "existing-family": (0, 0),
    "future": (0, 0),
}
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
FAMILIES_NAME = "families.jsonl"
SPECIMENS_NAME = "specimens.jsonl"
REJECTIONS_NAME = "selection-rejections.jsonl"
FAMILY_SCHEMA_NAME = "family.schema.json"
SPECIMEN_SCHEMA_NAME = "specimen.schema.json"

FINDING_CLASSES = (
    "family-tier",
    "family-schema",
    "family-duplicate",
    "specimen-annotation-order",
    "specimen-schema",
    "specimen-unknown-family",
    "specimen-span",
    "specimen-digest",
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


def read_jsonl_below(fixture: Path, name: str) -> list[dict]:
    blob = read_bytes_below(fixture, name)
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RefusalError(f"{name} is not UTF-8: {exc}") from exc
    rows: list[dict] = []
    for number, line in enumerate(text.splitlines(), 1):
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
    """Run one fixed-argv gh call with no shell and a bounded result."""
    for value in argv:
        if value.startswith("-") and value not in ("-H",):
            raise RefusalError(f"refusing an option-shaped gh argument: {value!r}")
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, shell=False
            ["gh", *argv],
            capture_output=True,
            shell=False,
            timeout=GH_TIMEOUT_SECONDS,
            check=False,
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


def fetch_source_object(row: dict) -> str:
    """Replay one specimen's immutable GitHub object. Opens a socket."""
    specimen_id = row.get("specimen_id")
    repository = endpoint_segment("repository", row["repository"], specimen_id)
    # Checked on every kind, not only the two that read it, so the pinned ref a
    # replay claims to be immutable is one this checker validated.
    commit = endpoint_segment("source_commit", row["source_commit"], specimen_id)
    source_object = row["source_object"]
    if source_object == "markdown_paragraph":
        path = endpoint_segment("source_path", row["source_path"], specimen_id)
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
        blob = gh_fetch(["api", f"repos/{repository}/commits/{commit}"])
        return reply_value(blob, ("commit", "message"), specimen_id)
    if source_object in ("issue_body", "pull_request_body"):
        tail = row["source_url"].rstrip("/").rsplit("/", 1)[-1].split("#")[0]
        number = endpoint_segment("object_number", tail, specimen_id)
        blob = gh_fetch(["api", f"repos/{repository}/issues/{number}"])
        return reply_value(blob, ("body",), specimen_id)
    fragment = COMMENT_FRAGMENT.search(row["source_url"])
    if fragment is None:
        raise RefusalError(f"cannot read a comment id from {row['source_url']}")
    collection = "issues" if fragment.group(1) == "issuecomment-" else "pulls"
    comment = endpoint_segment("comment_id", fragment.group(2), specimen_id)
    blob = gh_fetch(["api", f"repos/{repository}/{collection}/comments/{comment}"])
    return reply_value(blob, ("body",), specimen_id)


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
    seen: set[str] = set()
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
        if row["family_id"] not in seen:
            findings["specimen-unknown-family"].append(
                f"{SPECIMENS_NAME}:{index}: {label} names unknown family {row['family_id']}"
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
        for index, row in verifiable:
            body = fetch_source_object(row)
            if row["text"] not in body:
                findings["source-mismatch"].append(
                    f"{SPECIMENS_NAME}:{index}: {row['specimen_id']}: text is absent from the replayed object"
                )
            elif sha256_text(row["text"]) != row["text_sha256"]:
                findings["source-mismatch"].append(
                    f"{SPECIMENS_NAME}:{index}: {row['specimen_id']}: replayed text_sha256 does not match"
                )
    return findings


def measure_below_minimum(
    families: list[dict],
    specimens: list[dict],
    tier_filter: str | None,
    min_independent_positive: int | None,
) -> list[dict]:
    counted: dict[str, dict] = {}
    for row in specimens:
        family_id = row.get("family_id")
        polarity = row.get("polarity")
        if not isinstance(family_id, str) or polarity not in ("positive", "negative"):
            continue
        entry = counted.setdefault(family_id, {"positive": [], "negative": 0})
        if polarity == "positive":
            entry["positive"].append(row.get("source_group_id"))
        else:
            entry["negative"] += 1
    below = []
    for row in families:
        family_id = row.get("family_id")
        tier = row.get("evidence_tier")
        if tier not in TIER_MINIMUMS or not isinstance(family_id, str):
            continue
        if tier_filter is not None and tier != tier_filter:
            continue
        minimum_positive, minimum_negative = TIER_MINIMUMS[tier]
        if min_independent_positive is not None:
            minimum_positive = min_independent_positive
        if minimum_positive == 0 and minimum_negative == 0:
            continue
        entry = counted.get(family_id, {"positive": [], "negative": 0})
        independent = len({group for group in entry["positive"] if group is not None})
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
        help="override the independent-positive minimum for the checked tier",
    )
    parser.add_argument("--tier", help="restrict the tier-minimum check to one evidence tier")
    parser.add_argument(
        "--verify-sources",
        action="store_true",
        help="replay every specimen against its immutable GitHub object; this is the only path that opens a socket",
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
