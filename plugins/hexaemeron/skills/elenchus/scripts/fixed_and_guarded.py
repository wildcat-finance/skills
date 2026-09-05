#!/usr/bin/env python3
"""Emit the Elenchus fixed-and-guarded result as one closed record.

An `elenchus-fixed-and-guarded/v1` record holds the nine evidence fields the
`elenchus-fixed-and-guarded` Promise names and nothing else.  Seven come from
an operator-written draft, `unfixed_parent` and `verdict` from an
`elenchus.py --format json` result, and the parent commit from one
`git rev-parse <ref>^{commit} <ref>^`, which returns the commit the result
names beside its parent so both can be bound to the drafted repair.

Codes:

  F000  an input cannot be read as one bounded strict JSON object
  F001  the record is not one closed elenchus-fixed-and-guarded/v1 object
  F002  a field is absent, or its value is not the shape the schema names
  F003  a text field is empty, over its byte cap, or not printable
  F004  the verdict is not guarded
  F005  the draft is not one closed draft object
  F006  the result is not one closed elenchus.py result carrying a report
  F007  the guard names a test absent from the repair's changed test files
  F008  the parent commit could not be re-derived from the result's ref
  F009  the output path is not a free symlink-free relative worktree descendant,
        or the record could not be written there
  F010  the result's ref is not the commit the draft names as the repair
  F011  the record names one commit as both the parent and the fixed tree
  F012  the verdict is guarded while the parent's own report never failed
  F013  the verdict is guarded while the parent's own report records an error
  F014  the verdict is guarded while the fixed tree's own report still fails
  F015  the fixed tree is not the commit the record names as the repair
  F016  the guard names a file absent from the repair's own changed files

Exit 0 written or clean, 1 refused, 2 bad invocation.  Every refusal names its
code and its field on stderr and writes nothing.  The record is staged in the
destination directory and renamed into place, so an interrupted emit leaves no
file `--check` accepts.  No value read from either input is executed,
interpolated into a command line or followed as a URL; the reproduction output
reaches the record as a digest and a byte count and never as bytes.

This script emits.  It does not resolve one record against another, admit
anything to a corpus, or say that two records share a cause.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "elenchus-fixed-and-guarded/v1"
GUARDED = "guarded"
STATES = ("guarded", "passed", "unguarded", "inconclusive")

MAX_INPUT_BYTES = 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_TEXT_BYTES = 4096
MAX_PATH_BYTES = 512
MAX_LIST_ITEMS = 256
MAX_EXIT_CODE = 255

RECORD_KEYS = frozenset({
    "schema", "reproduction", "causal_mechanism", "minimal_case", "repair",
    "guard", "unfixed_parent", "fixed_tree", "suites", "verdict",
})
DRAFT_KEYS = frozenset({
    "reproduction", "causal_mechanism", "minimal_case", "repair", "guard",
    "fixed_tree", "suites",
})
RESULT_REQUIRED = frozenset({"ref", "status", "tests", "detail"})
RESULT_OPTIONAL = frozenset({"report", "exit_code", "output"})

REPRODUCTION_KEYS = frozenset({"command", "output_sha256", "output_bytes"})
MECHANISM_KEYS = frozenset({"account", "site"})
MINIMAL_CASE_KEYS = frozenset({"description", "path"})
REPAIR_KEYS = frozenset({"commit", "files"})
GUARD_KEYS = frozenset({"file", "test"})
TREE_KEYS = frozenset({"commit", "report"})
REPORT_KEYS = frozenset({
    "complete", "executed", "assertion_failures", "errors", "skipped",
})
SUITE_KEYS = frozenset({"command", "exit_code"})
VERDICT_KEYS = frozenset({"status", "detail"})

COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
SITE = re.compile(r"^[A-Za-z0-9._/-]+:[1-9][0-9]{0,8}$")
TEST_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:[.:][A-Za-z_][A-Za-z0-9_]*)*$")


class DuplicateKey(ValueError):
    """A JSON object repeated a key, so its bytes name two values."""


class Finding:
    """One refusal, carrying the rule that refused and the field it read."""

    __slots__ = ("code", "field", "message")

    def __init__(self, code: str, field: str, message: str) -> None:
        self.code = code
        self.field = field
        self.message = message

    def __str__(self) -> str:
        return f"{self.code} {self.field}: {self.message}"


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _depth_within_limit(data: bytes) -> bool:
    """Bound nesting before the parser recurses over attacker-shaped bytes."""
    depth = 0
    in_string = False
    escaped = False
    for byte in data:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):
            depth += 1
            if depth > MAX_JSON_DEPTH:
                return False
        elif byte in (0x5D, 0x7D) and depth:
            depth -= 1
    return True


def read_json(path: Path) -> object | None:
    """One bounded strict JSON read, or None with nothing else attempted."""
    try:
        before = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > MAX_INPUT_BYTES
        ):
            return None
        descriptor = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            chunks = []
            total = 0
            while True:
                chunk = os.read(descriptor, min(64 * 1024, MAX_INPUT_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_INPUT_BYTES:
                    return None
        finally:
            os.close(descriptor)
        data = b"".join(chunks)
        if not _depth_within_limit(data):
            return None
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite number {token}")
            ),
        )
    except (
        DuplicateKey, MemoryError, OSError, RecursionError, UnicodeDecodeError,
        ValueError,
    ):
        return None


def _integer(value, *, maximum: int | None = None) -> bool:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return False
    return maximum is None or value <= maximum


def _text(value, *, maximum: int = MAX_TEXT_BYTES) -> bool:
    if not isinstance(value, str) or not value:
        return False
    return (
        len(value.encode("utf-8", "surrogatepass")) <= maximum
        and all(character.isprintable() for character in value)
    )


def _relative_path(value) -> bool:
    """A portable repository-relative path, with no traversal and no root."""
    if not _text(value, maximum=MAX_PATH_BYTES):
        return False
    if value.startswith("/") or "\\" in value or re.match(r"^[A-Za-z]:", value):
        return False
    return all(part not in ("", ".", "..") for part in value.split("/"))


def _closed(value, keys: frozenset[str]) -> bool:
    return isinstance(value, dict) and set(value) == set(keys)


def _text_findings(value, field: str, *, maximum: int = MAX_TEXT_BYTES) -> list[Finding]:
    if _text(value, maximum=maximum):
        return []
    return [Finding(
        "F003", field,
        f"must be printable text of 1 to {maximum} bytes",
    )]


def _report_findings(value, field: str) -> list[Finding]:
    if not _closed(value, REPORT_KEYS):
        return [Finding("F002", field, "must be one closed normalised report object")]
    findings: list[Finding] = []
    if value["complete"] is not True:
        findings.append(Finding("F002", f"{field}.complete", "must be true"))
    for name in ("executed", "assertion_failures", "errors", "skipped"):
        if not _integer(value[name]):
            findings.append(Finding(
                "F002", f"{field}.{name}", "must be a non-negative integer",
            ))
    if findings:
        return findings
    if value["assertion_failures"] + value["errors"] > value["executed"]:
        findings.append(Finding(
            "F002", field, "outcome counts exceed executed tests",
        ))
    return findings


def _tree_findings(value, field: str) -> list[Finding]:
    if not _closed(value, TREE_KEYS):
        return [Finding("F002", field, "must be one closed commit-and-report object")]
    findings: list[Finding] = []
    if not isinstance(value["commit"], str) or COMMIT.fullmatch(value["commit"]) is None:
        findings.append(Finding(
            "F002", f"{field}.commit", "must be one full hexadecimal commit identifier",
        ))
    findings.extend(_report_findings(value["report"], f"{field}.report"))
    return findings


def _reproduction_findings(value) -> list[Finding]:
    if not _closed(value, REPRODUCTION_KEYS):
        return [Finding("F002", "reproduction", "must be one closed reproduction object")]
    findings = _text_findings(value["command"], "reproduction.command")
    digest = value["output_sha256"]
    if not isinstance(digest, str) or DIGEST.fullmatch(digest) is None:
        findings.append(Finding(
            "F002", "reproduction.output_sha256",
            "must be the observed output's SHA-256, and the output's bytes never reach the record",
        ))
    if not _integer(value["output_bytes"]):
        findings.append(Finding(
            "F002", "reproduction.output_bytes", "must be a non-negative integer",
        ))
    return findings


def _mechanism_findings(value) -> list[Finding]:
    if not _closed(value, MECHANISM_KEYS):
        return [Finding("F002", "causal_mechanism", "must be one closed mechanism object")]
    findings = _text_findings(value["account"], "causal_mechanism.account")
    site = value["site"]
    if not _text(site, maximum=MAX_PATH_BYTES) or SITE.fullmatch(site) is None:
        findings.append(Finding(
            "F002", "causal_mechanism.site", "must be the `path:line` where the mechanism starts",
        ))
    return findings


def _minimal_case_findings(value) -> list[Finding]:
    if value is None:
        return []
    if not _closed(value, MINIMAL_CASE_KEYS):
        return [Finding(
            "F002", "minimal_case",
            "must be one closed reduced-case object, or null where none was useful",
        )]
    findings = _text_findings(value["description"], "minimal_case.description")
    if not _relative_path(value["path"]):
        findings.append(Finding(
            "F002", "minimal_case.path", "must be a relative path with no traversal",
        ))
    return findings


def _repair_findings(value) -> list[Finding]:
    if not _closed(value, REPAIR_KEYS):
        return [Finding("F002", "repair", "must be one closed repair object")]
    findings: list[Finding] = []
    if not isinstance(value["commit"], str) or COMMIT.fullmatch(value["commit"]) is None:
        findings.append(Finding(
            "F002", "repair.commit", "must be one full hexadecimal commit identifier",
        ))
    files = value["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_LIST_ITEMS:
        findings.append(Finding(
            "F002", "repair.files",
            f"must list 1 to {MAX_LIST_ITEMS} files the repair touched",
        ))
    else:
        for index, name in enumerate(files):
            if not _relative_path(name):
                findings.append(Finding(
                    "F002", f"repair.files[{index}]",
                    "must be a relative path with no traversal",
                ))
    return findings


def _guard_findings(value) -> list[Finding]:
    if not _closed(value, GUARD_KEYS):
        return [Finding("F002", "guard", "must be one closed guard object")]
    findings: list[Finding] = []
    if not _relative_path(value["file"]):
        findings.append(Finding(
            "F002", "guard.file", "must be a relative path with no traversal",
        ))
    name = value["test"]
    if not _text(name, maximum=MAX_PATH_BYTES) or TEST_NAME.fullmatch(name) is None:
        findings.append(Finding(
            "F002", "guard.test", "must name the regression test inside that file",
        ))
    return findings


def _suites_findings(value) -> list[Finding]:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_LIST_ITEMS:
        return [Finding(
            "F002", "suites",
            f"must record 1 to {MAX_LIST_ITEMS} suite runs, each a command and its exit code",
        )]
    findings: list[Finding] = []
    for index, suite in enumerate(value):
        if not _closed(suite, SUITE_KEYS):
            findings.append(Finding(
                "F002", f"suites[{index}]", "must be one closed suite object",
            ))
            continue
        findings.extend(_text_findings(suite["command"], f"suites[{index}].command"))
        if not _integer(suite["exit_code"], maximum=MAX_EXIT_CODE):
            findings.append(Finding(
                "F002", f"suites[{index}].exit_code",
                f"must be an exit code from 0 to {MAX_EXIT_CODE}",
            ))
    return findings


def _verdict_findings(value) -> list[Finding]:
    if not _closed(value, VERDICT_KEYS):
        return [Finding("F002", "verdict", "must be one closed verdict object")]
    findings = _text_findings(value["detail"], "verdict.detail")
    status = value["status"]
    if status not in STATES:
        findings.append(Finding(
            "F002", "verdict.status",
            "must be one of the four Elenchus states: " + ", ".join(STATES),
        ))
    elif status != GUARDED:
        findings.append(Finding(
            "F004", "verdict.status",
            f"is {status}; the Boundary does not turn an inconclusive, zero-test or "
            f"infrastructure-failed comparison into a guard",
        ))
    return findings


def _relation_findings(record) -> list[Finding]:
    """The refusals that read one field of the record against another.

    Each is decided from fields the record already carries, so `--check`
    settles them on a record alone.  They run only once every field they
    read has passed its own rule, because a relation between two values the
    schema has already refused says nothing about the record.
    """
    findings: list[Finding] = []
    if record["unfixed_parent"]["commit"] == record["fixed_tree"]["commit"]:
        findings.append(Finding(
            "F011", "unfixed_parent.commit",
            "equals fixed_tree.commit; a guard observed red and green on one "
            "commit is not the two trees the Evidence clause names",
        ))
    if record["fixed_tree"]["commit"] != record["repair"]["commit"]:
        findings.append(Finding(
            "F015", "fixed_tree.commit",
            f"is {record['fixed_tree']['commit']}, which is not the "
            f"{record['repair']['commit']} the record names as the repair; the "
            f"fixed tree the Evidence clause requires is the tree the repair "
            f"produced and no other",
        ))
    if record["guard"]["file"] not in record["repair"]["files"]:
        findings.append(Finding(
            "F016", "guard.file",
            f"{record['guard']['file']} is absent from repair.files; the "
            f"Boundary covers the named guard, and a guard the repair did not "
            f"touch is not that guard",
        ))
    if record["verdict"]["status"] != GUARDED:
        return findings
    parent = record["unfixed_parent"]["report"]
    if parent["assertion_failures"] == 0 and parent["errors"] == 0:
        findings.append(Finding(
            "F012", "verdict.status",
            "is guarded while unfixed_parent.report records 0 assertion failures "
            "and 0 errors; the Refuses clause names a guard that never failed "
            "without the fix",
        ))
    if parent["errors"] > 0:
        findings.append(Finding(
            "F013", "verdict.status",
            f"is guarded while unfixed_parent.report records {parent['errors']} "
            f"errors; a report carrying an error classifies as inconclusive, and "
            f"the Boundary does not turn an inconclusive comparison into a guard",
        ))
    fixed = record["fixed_tree"]["report"]
    if fixed["assertion_failures"] > 0 or fixed["errors"] > 0:
        findings.append(Finding(
            "F014", "verdict.status",
            f"is guarded while fixed_tree.report records "
            f"{fixed['assertion_failures']} assertion failures and "
            f"{fixed['errors']} errors; the Evidence clause requires the guard "
            f"to pass on the fixed tree",
        ))
    return findings


def record_findings(record) -> list[Finding]:
    """Everything a record establishes about itself, without its inputs."""
    if not isinstance(record, dict) or set(record) != set(RECORD_KEYS):
        return [Finding(
            "F001", "schema",
            f"must be one closed {SCHEMA} object holding exactly the nine evidence fields",
        )]
    if record["schema"] != SCHEMA:
        return [Finding("F001", "schema", f"must be {SCHEMA}")]
    findings: list[Finding] = []
    findings.extend(_reproduction_findings(record["reproduction"]))
    findings.extend(_mechanism_findings(record["causal_mechanism"]))
    findings.extend(_minimal_case_findings(record["minimal_case"]))
    findings.extend(_repair_findings(record["repair"]))
    findings.extend(_guard_findings(record["guard"]))
    findings.extend(_tree_findings(record["unfixed_parent"], "unfixed_parent"))
    findings.extend(_tree_findings(record["fixed_tree"], "fixed_tree"))
    findings.extend(_suites_findings(record["suites"]))
    findings.extend(_verdict_findings(record["verdict"]))
    if findings:
        return findings
    return _relation_findings(record)


def draft_findings(draft) -> list[Finding]:
    """The operator-supplied half, checked before anything is composed."""
    if not isinstance(draft, dict) or set(draft) != set(DRAFT_KEYS):
        return [Finding(
            "F005", "draft",
            "must be one closed object holding exactly: " + ", ".join(sorted(DRAFT_KEYS)),
        )]
    findings: list[Finding] = []
    findings.extend(_reproduction_findings(draft["reproduction"]))
    findings.extend(_mechanism_findings(draft["causal_mechanism"]))
    findings.extend(_minimal_case_findings(draft["minimal_case"]))
    findings.extend(_repair_findings(draft["repair"]))
    findings.extend(_guard_findings(draft["guard"]))
    findings.extend(_tree_findings(draft["fixed_tree"], "fixed_tree"))
    findings.extend(_suites_findings(draft["suites"]))
    return findings


def result_findings(result) -> list[Finding]:
    """The `elenchus.py --format json` half, read for four values only."""
    if (
        not isinstance(result, dict)
        or not set(RESULT_REQUIRED) <= set(result)
        or not set(result) <= set(RESULT_REQUIRED | RESULT_OPTIONAL)
    ):
        return [Finding(
            "F006", "result",
            "must be one closed elenchus.py result object; an unknown key is refused",
        )]
    findings: list[Finding] = []
    # A ref beginning with a dash is an option rather than a name, and this one
    # becomes an argument to `git rev-parse`; refuse it before it gets there.
    if not _text(result["ref"], maximum=MAX_PATH_BYTES) or result["ref"].startswith("-"):
        findings.append(Finding(
            "F006", "result.ref",
            "must name the commit carrying the fix, and must not begin with a dash",
        ))
    findings.extend(
        Finding("F006", finding.field, finding.message)
        for finding in _text_findings(result["detail"], "result.detail")
    )
    tests = result["tests"]
    if not isinstance(tests, list) or not 1 <= len(tests) <= MAX_LIST_ITEMS:
        findings.append(Finding(
            "F006", "result.tests", "must list the changed test files the comparison used",
        ))
    elif not all(_relative_path(name) for name in tests):
        findings.append(Finding(
            "F006", "result.tests", "must hold relative paths with no traversal",
        ))
    status = result["status"]
    if status not in STATES:
        findings.append(Finding(
            "F006", "result.status",
            "must be one of the four Elenchus states: " + ", ".join(STATES),
        ))
    elif status != GUARDED:
        findings.append(Finding(
            "F004", "result.status",
            f"is {status}; the Boundary does not turn an inconclusive, zero-test or "
            f"infrastructure-failed comparison into a guard",
        ))
    if "report" not in result:
        findings.append(Finding(
            "F006", "result.report",
            "is absent, so no parent comparison was recorded to carry into the record",
        ))
    else:
        findings.extend(
            Finding("F006", finding.field, finding.message)
            for finding in _report_findings(result["report"], "result.report")
        )
    return findings


def git(repo: Path, *arguments: str) -> str | None:
    """One fixed-argv git read, with no shell and no value interpolated."""
    try:
        run = subprocess.run(
            ["git", "-C", str(repo), *arguments],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return run.stdout if run.returncode == 0 else None


def commit_and_parent(repo: Path, ref: str) -> tuple[str, str] | None:
    """The commit the result names, and the parent it was compared against.

    Both come from one read, because the record is only coherent when the
    parent belongs to the commit the draft calls the repair.  The first
    argument peels, because `elenchus.py` takes any ref and echoes it
    unresolved: an annotated tag resolves to its own object rather than to
    the commit it names, and comparing that object against the drafted
    repair would refuse a record whose parent is perfectly good.
    """
    out = git(repo, "rev-parse", f"{ref}^{{commit}}", f"{ref}^")
    if out is None:
        return None
    resolved = out.split()
    if len(resolved) != 2 or any(COMMIT.fullmatch(one) is None for one in resolved):
        return None
    return resolved[0], resolved[1]


def tracked(repo: Path, relative: str) -> bool:
    return git(repo, "ls-files", "--error-unmatch", "--", relative) is not None


def prepare_output_path(repo: Path, raw: str) -> tuple[Path | None, Finding | None]:
    """A free, symlink-free relative descendant of the worktree, or a refusal."""
    def refuse(message: str) -> tuple[None, Finding]:
        return None, Finding("F009", "--out", message)

    if not _relative_path(raw):
        return refuse("must be a relative worktree descendant with no traversal")
    try:
        root = repo.resolve(strict=True)
    except OSError:
        return refuse("names a worktree that cannot be resolved")

    parts = raw.split("/")
    walked = root
    for part in parts[:-1]:
        walked = walked / part
        try:
            entry = walked.lstat()
        except FileNotFoundError:
            break
        except OSError:
            return refuse("cannot be inspected")
        if stat.S_ISLNK(entry.st_mode):
            return refuse("must not contain a symlink component")
        if not stat.S_ISDIR(entry.st_mode):
            return refuse("names a parent component that is not a directory")

    candidate = root / raw
    try:
        candidate.resolve(strict=False).relative_to(root)
    except (OSError, ValueError):
        return refuse("escapes the worktree")
    if tracked(repo, raw):
        return refuse("names a tracked file")
    try:
        candidate.lstat()
    except FileNotFoundError:
        pass
    except OSError:
        return refuse("cannot be inspected")
    else:
        return refuse("names a destination that already exists")
    try:
        candidate.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return refuse("names a parent directory that cannot be created")
    return candidate, None


def compose(draft: dict, result: dict, parent: str) -> dict:
    """The nine fields, each taken from the half that holds it."""
    return {
        "schema": SCHEMA,
        "causal_mechanism": draft["causal_mechanism"],
        "fixed_tree": draft["fixed_tree"],
        "guard": draft["guard"],
        "minimal_case": draft["minimal_case"],
        "repair": draft["repair"],
        "reproduction": draft["reproduction"],
        "suites": draft["suites"],
        "unfixed_parent": {"commit": parent, "report": result["report"]},
        "verdict": {"status": result["status"], "detail": result["detail"]},
    }


def write_staged(path: Path, record: dict) -> None:
    """Stage beside the destination and rename, so a kill leaves nothing."""
    payload = json.dumps(record, indent=2, sort_keys=True) + "\n"
    descriptor, staged = tempfile.mkstemp(
        dir=str(path.parent), prefix=".fixed-and-guarded-", suffix=".staged",
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, path)
    except BaseException:
        try:
            os.unlink(staged)
        except OSError:
            pass
        raise


def emit(repo: Path, draft_path: Path, result_path: Path, out: str) -> tuple[list[Finding], Path | None]:
    """Read both inputs, compose the record and write it, or refuse."""
    draft = read_json(draft_path)
    if draft is None:
        return [Finding(
            "F000", "--draft",
            "cannot be read as one bounded strict JSON object; a duplicate key, "
            "a symlink, a non-regular file and an oversized file are each refused",
        )], None
    result = read_json(result_path)
    if result is None:
        return [Finding(
            "F000", "--result",
            "cannot be read as one bounded strict JSON object; a duplicate key, "
            "a symlink, a non-regular file and an oversized file are each refused",
        )], None

    findings = draft_findings(draft) + result_findings(result)
    if findings:
        return findings, None

    if draft["guard"]["file"] not in result["tests"]:
        return [Finding(
            "F007", "guard.file",
            f"{draft['guard']['file']} is absent from the repair's changed test "
            f"files, so the Boundary's named guard is not the one that was compared",
        )], None

    resolved = commit_and_parent(repo, result["ref"])
    if resolved is None:
        return [Finding(
            "F008", "unfixed_parent.commit",
            f"git rev-parse {result['ref']}^{{commit}} {result['ref']}^ named "
            f"no commit and parent in {repo}",
        )], None
    fixed, parent = resolved
    if fixed != draft["repair"]["commit"]:
        return [Finding(
            "F010", "unfixed_parent.commit",
            f"{result['ref']} resolves to {fixed}, which is not the "
            f"{draft['repair']['commit']} the draft names as the repair, so the "
            f"derived parent is not the repair's parent",
        )], None

    record = compose(draft, result, parent)
    composed = record_findings(record)
    if composed:
        return composed, None

    target, refusal = prepare_output_path(repo, out)
    if refusal is not None:
        return [refusal], None
    try:
        write_staged(target, record)
    except OSError:
        return [Finding(
            "F009", "--out",
            "could not be written; the staged file was removed, so no partial "
            "record was left behind",
        )], None
    return [], target


def check(path: Path) -> list[Finding]:
    """What one record establishes on its own, with no input beside it."""
    record = read_json(path)
    if record is None:
        return [Finding(
            "F000", "--check",
            "cannot be read as one bounded strict JSON object; a duplicate key, "
            "a symlink, a non-regular file and an oversized file are each refused",
        )]
    return record_findings(record)


def report(prefix: str, findings: list[Finding]) -> None:
    """Name the rule and the field of every refusal, on stderr."""
    for finding in findings:
        print(f"{prefix}: {finding}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit or check one closed Elenchus fixed-and-guarded record.",
    )
    parser.add_argument("--repo", default=".", help="worktree the record is written inside")
    parser.add_argument("--draft", help="operator-supplied JSON holding seven of the nine fields")
    parser.add_argument("--result", help="an elenchus.py --format json result")
    parser.add_argument("--out", help="where to write the record, relative to --repo")
    parser.add_argument("--check", help="validate an existing record and write nothing")
    args = parser.parse_args(argv)

    emitting = (args.draft, args.result, args.out)
    if args.check is not None:
        if any(value is not None for value in emitting):
            parser.error("--check validates a record on its own")
        path = Path(args.check)
        findings = check(path)
        report(str(path), findings)
        if not findings:
            print(f"{path}: clean")
        return 1 if findings else 0
    if any(value is None for value in emitting):
        parser.error("emission needs --draft, --result and --out")

    repo = Path(args.repo)
    findings, target = emit(repo, Path(args.draft), Path(args.result), args.out)
    if findings:
        report(Path(__file__).name, findings)
        return 1
    print(f"{target}: written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
