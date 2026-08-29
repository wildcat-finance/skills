#!/usr/bin/env python3
"""Build a report-only dead-code inventory for one clean Git tree.

The command discovers tracked paths, applies hard Horos classifications and
renders one deterministic model as text or JSON. Step 1 registers no analyser,
so the report says that no reachability result was established. It never
deletes source and a finding count is never an exit gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import selectors
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable

SCHEMA_ID = "dead-code-report/v1"
TOOL_ID = "dead-code"
TOOL_VERSION = "1"
STATUS_ID = "analysis"
BOUNDARY_PATH = Path(".horos") / "boundary.json"
BOUNDARY_SCHEMA = 2
BOUNDARY_TOOL = "horos"
EXCLUDING_GRADE = "hard"
UNIVERSE_FLOOR = 1
TEMP_PREFIX = ".dead-code-tmp-"
OWNED_OUTPUT_DIRECTORY = ".dead-code"
GIT_TIMEOUT_SECONDS = 60
MAX_GIT_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_BOUNDARY_BYTES = 4 * 1024 * 1024
MAX_REPORT_BYTES = 32 * 1024 * 1024
MAX_TRACKED_PATHS = 100_000
MAX_PATH_BYTES = 4096
ANALYSER_STATES = frozenset({"ran", "not-available", "degraded", "failed"})
CONFIDENCE_LEVELS = frozenset({"high", "medium", "low"})

Analyser = Callable[
    [Path, "Universe"],
    tuple["AnalyserStatus", tuple["Finding", ...]],
]
ANALYSERS: dict[str, Analyser] = {}


class Refusal(Exception):
    """A named condition that stops the command before it reports."""


class DuplicateKey(ValueError):
    """A duplicate JSON member that would otherwise overwrite evidence."""


@dataclass(frozen=True)
class ClassifiedPath:
    path: str
    category: str
    evidence: str
    grade: str

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "category": self.category,
            "evidence": self.evidence,
            "grade": self.grade,
        }


@dataclass(frozen=True)
class Classification:
    files: dict[str, ClassifiedPath]
    directories: tuple[ClassifiedPath, ...]

    def match(self, path: str) -> ClassifiedPath | None:
        exact = self.files.get(path)
        if exact is not None:
            return exact
        for tree in self.directories:
            if path.startswith(tree.path):
                return ClassifiedPath(
                    path=path,
                    category=tree.category,
                    evidence=(
                        f"{tree.evidence}, inherited from the classified tree "
                        f"{tree.path}"
                    ),
                    grade=tree.grade,
                )
        return None


@dataclass(frozen=True)
class Universe:
    commit: str
    tree: str
    identity: str
    tracked_count: int
    analysed: tuple[str, ...]
    excluded: tuple[ClassifiedPath, ...]

    def excluded_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.excluded:
            counts[entry.category] = counts.get(entry.category, 0) + 1
        return {name: counts[name] for name in sorted(counts)}

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.identity,
            "tracked_count": self.tracked_count,
            "analysed_count": len(self.analysed),
            "analysed": list(self.analysed),
            "excluded_count": len(self.excluded),
            "excluded_by_category": self.excluded_by_category(),
            "excluded": [entry.as_dict() for entry in self.excluded],
        }


@dataclass(frozen=True)
class AnalyserStatus:
    analyser_id: str
    state: str
    version: str | None
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.analyser_id,
            "state": self.state,
            "version": self.version,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class Finding:
    analyser_id: str
    path: str
    symbol: str | None
    evidence: str
    confidence: str
    false_positive_boundary: str

    @property
    def identity(self) -> str:
        payload = {
            "analyser_id": self.analyser_id,
            "path": self.path,
            "symbol": self.symbol,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "false_positive_boundary": self.false_positive_boundary,
        }
        return digest_json(payload)

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.identity,
            "analyser_id": self.analyser_id,
            "path": self.path,
            "symbol": self.symbol,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "false_positive_boundary": self.false_positive_boundary,
        }


@dataclass(frozen=True)
class Report:
    universe: Universe
    statuses: tuple[AnalyserStatus, ...]
    findings: tuple[Finding, ...]

    def analysis_status(self) -> dict[str, str]:
        if not self.statuses:
            return {
                "id": STATUS_ID,
                "state": "not-run",
                "detail": (
                    "no analyser registered; this report establishes no "
                    "reachability result"
                ),
            }
        if any(item.state == "failed" for item in self.statuses):
            state = "failed"
            detail = "at least one analyser failed; no clean result is established"
        elif any(item.state in {"degraded", "not-available"} for item in self.statuses):
            state = "degraded"
            detail = "one or more analyser signals are incomplete"
        else:
            state = "ran"
            detail = "every registered analyser completed"
        return {"id": STATUS_ID, "state": state, "detail": detail}

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": SCHEMA_ID,
            "tool": {"id": TOOL_ID, "version": TOOL_VERSION},
            "tree": {
                "commit": self.universe.commit,
                "git_tree": self.universe.tree,
            },
            "universe": self.universe.as_dict(),
            "status": self.analysis_status(),
            "analysers": [status.as_dict() for status in self.statuses],
            "findings": [finding.as_dict() for finding in self.findings],
        }


def digest_json(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.kill()
    process.wait()


def run_process(
    argv: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    output_limit: int,
) -> tuple[bytes, bytes, int]:
    """Run fixed argv while bounding time and combined captured output."""
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    except FileNotFoundError as error:
        raise Refusal(f"{argv[0]} is not available on PATH") from error
    except OSError as error:
        raise Refusal(f"{argv[0]} could not start: {error}") from error

    assert process.stdout is not None
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    total = 0
    deadline = time.monotonic() + timeout_seconds
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _stop_process(process)
                raise Refusal(f"{argv[0]} timed out after {timeout_seconds}s")
            events = selector.select(min(remaining, 0.25))
            if not events:
                continue
            for key, _ in events:
                chunk = os.read(
                    key.fileobj.fileno(),
                    min(65_536, output_limit - total + 1),
                )
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffers[key.data].extend(chunk)
                total += len(chunk)
                if total > output_limit:
                    _stop_process(process)
                    raise Refusal(
                        f"{argv[0]} output exceeded {output_limit} bytes"
                    )
        returncode = process.wait()
    finally:
        selector.close()
        if process.poll() is None:
            _stop_process(process)
        process.stdout.close()
        process.stderr.close()
    return bytes(buffers["stdout"]), bytes(buffers["stderr"]), returncode


def decode_output(payload: bytes, label: str) -> str:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Refusal(f"{label} output is not UTF-8") from error


def run_git(root: Path, *arguments: str) -> str:
    stdout, stderr, returncode = run_process(
        ["git", "-C", str(root), *arguments],
        cwd=root,
        timeout_seconds=GIT_TIMEOUT_SECONDS,
        output_limit=MAX_GIT_OUTPUT_BYTES,
    )
    if returncode != 0:
        detail = decode_output(stderr, "git stderr").strip()
        if not detail:
            detail = f"exit {returncode}"
        raise Refusal(f"git {arguments[0]} failed: {detail}")
    return decode_output(stdout, "git stdout")


def repository_root(start: Path) -> Path:
    output = run_git(start, "rev-parse", "--show-toplevel").strip()
    if not output:
        raise Refusal(f"{start} is not inside a Git worktree")
    root = Path(output).resolve(strict=True)
    if not root.is_dir():
        raise Refusal("Git returned a root that is not a directory")
    return root


def _require_oid(value: str, label: str) -> str:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise Refusal(f"{label} is not a lowercase 40-byte Git object identity")
    return value


def resolve_commit(root: Path) -> str:
    return _require_oid(run_git(root, "rev-parse", "HEAD").strip(), "HEAD")


def resolve_tree(root: Path, commit: str) -> str:
    return _require_oid(
        run_git(root, "rev-parse", f"{commit}^{{tree}}").strip(),
        "HEAD tree",
    )


def require_clean_tree(root: Path) -> None:
    porcelain = run_git(
        root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=no",
    )
    changed = [entry for entry in porcelain.split(chr(0)) if entry]
    if changed:
        names = sorted(entry[3:] if len(entry) > 3 else entry for entry in changed)
        listed = ", ".join(names[:5])
        more = "" if len(names) <= 5 else f" and {len(names) - 5} more"
        raise Refusal(
            f"the checkout has {len(names)} modified tracked file(s): "
            f"{listed}{more}; commit or stash before analysing"
        )


def validate_repository_path(value: str, label: str) -> str:
    if not value:
        raise Refusal(f"{label} is empty")
    if len(value.encode("utf-8")) > MAX_PATH_BYTES:
        raise Refusal(f"{label} exceeds {MAX_PATH_BYTES} bytes")
    if value.startswith("/") or chr(92) in value or chr(0) in value:
        raise Refusal(f"{label} is not a safe repository-relative POSIX path")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise Refusal(f"{label} contains a control character")
    without_tree_suffix = value[:-1] if value.endswith("/") else value
    parts = PurePosixPath(without_tree_suffix).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise Refusal(f"{label} is not a safe repository-relative POSIX path")
    return value


def tracked_paths(root: Path, commit: str) -> tuple[str, ...]:
    listing = run_git(root, "ls-tree", "-r", "--name-only", "-z", commit)
    paths = tuple(
        sorted(
            validate_repository_path(entry, "tracked path")
            for entry in listing.split(chr(0))
            if entry
        )
    )
    if len(paths) > MAX_TRACKED_PATHS:
        raise Refusal(f"tracked discovery exceeded {MAX_TRACKED_PATHS} paths")
    if len(paths) != len(set(paths)):
        raise Refusal("tracked discovery returned duplicate paths")
    return paths


def read_bounded_regular(path: Path, *, limit: int, label: str) -> str:
    try:
        before = path.lstat()
    except FileNotFoundError as error:
        raise Refusal(f"{label} is absent") from error
    except OSError as error:
        raise Refusal(f"{label} cannot be inspected: {error}") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise Refusal(f"{label} is not a regular file")
    if before.st_size > limit:
        raise Refusal(f"{label} exceeds {limit} bytes")
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise Refusal(f"{label} changed before it was opened")
            payload = handle.read(limit + 1)
            after_handle = os.fstat(handle.fileno())
        after = path.lstat()
    except OSError as error:
        raise Refusal(f"{label} cannot be read: {error}") from error
    if len(payload) > limit:
        raise Refusal(f"{label} exceeds {limit} bytes")
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    handle_identity = (
        after_handle.st_dev,
        after_handle.st_ino,
        after_handle.st_size,
        after_handle.st_mtime_ns,
    )
    if before_identity != after_identity or before_identity != handle_identity:
        raise Refusal(f"{label} changed while it was read")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Refusal(f"{label} is not UTF-8") from error


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document: dict[str, object] = {}
    for key, value in pairs:
        if key in document:
            raise DuplicateKey(key)
        document[key] = value
    return document


def load_boundary(root: Path) -> Classification:
    label = BOUNDARY_PATH.as_posix()
    raw = read_bounded_regular(
        root / BOUNDARY_PATH,
        limit=MAX_BOUNDARY_BYTES,
        label=label,
    )
    try:
        document = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except DuplicateKey as error:
        raise Refusal(f"{label} repeats JSON key {error.args[0]}") from error
    except json.JSONDecodeError as error:
        raise Refusal(f"{label} is not valid JSON: {error}") from error
    if not isinstance(document, dict):
        raise Refusal(f"{label} is not a JSON object")
    if document.get("schema") != BOUNDARY_SCHEMA:
        raise Refusal(f"{label} does not declare schema {BOUNDARY_SCHEMA}")
    if document.get("tool") != BOUNDARY_TOOL:
        raise Refusal(f"{label} does not declare tool {BOUNDARY_TOOL}")
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise Refusal(f"{label} has no entries list")

    files: dict[str, ClassifiedPath] = {}
    directories: list[ClassifiedPath] = []
    seen_paths: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise Refusal(f"{label} entry {index} is not an object")
        fields: dict[str, str] = {}
        for name in ("path", "category", "evidence", "grade"):
            value = entry.get(name)
            if not isinstance(value, str) or not value:
                raise Refusal(f"{label} entry {index} has no usable {name}")
            fields[name] = value
        path = validate_repository_path(fields["path"], f"{label} entry {index} path")
        if path in seen_paths:
            raise Refusal(f"{label} repeats classified path {path}")
        seen_paths.add(path)
        if fields["grade"] != EXCLUDING_GRADE:
            continue
        classified = ClassifiedPath(**fields)
        if path.endswith("/"):
            directories.append(classified)
        else:
            files[path] = classified

    directories.sort(key=lambda item: (-len(item.path), item.path))
    return Classification(files=files, directories=tuple(directories))


def universe_identity(
    tree: str,
    analysed: tuple[str, ...],
    excluded: tuple[ClassifiedPath, ...],
) -> str:
    return digest_json(
        {
            "git_tree": tree,
            "analysed": list(analysed),
            "excluded": [entry.as_dict() for entry in excluded],
        }
    )


def discover(root: Path) -> Universe:
    require_clean_tree(root)
    commit = resolve_commit(root)
    tree = resolve_tree(root, commit)
    tracked = tracked_paths(root, commit)
    classified = load_boundary(root)

    analysed: list[str] = []
    excluded: list[ClassifiedPath] = []
    for path in tracked:
        match = classified.match(path)
        if match is None:
            analysed.append(path)
        else:
            excluded.append(match)
    if len(analysed) < UNIVERSE_FLOOR:
        raise Refusal(
            f"discovery returned {len(analysed)} analysable paths from "
            f"{len(tracked)} tracked; this is a collapsed walk"
        )
    analysed_tuple = tuple(analysed)
    excluded_tuple = tuple(excluded)
    return Universe(
        commit=commit,
        tree=tree,
        identity=universe_identity(tree, analysed_tuple, excluded_tuple),
        tracked_count=len(tracked),
        analysed=analysed_tuple,
        excluded=excluded_tuple,
    )


def collect(
    root: Path,
    universe: Universe,
) -> tuple[tuple[AnalyserStatus, ...], tuple[Finding, ...]]:
    statuses: list[AnalyserStatus] = []
    findings: list[Finding] = []
    for analyser_id in sorted(ANALYSERS):
        status, produced = ANALYSERS[analyser_id](root, universe)
        if status.analyser_id != analyser_id:
            raise Refusal(
                f"analyser {analyser_id} returned status for {status.analyser_id}"
            )
        statuses.append(status)
        findings.extend(produced)
    statuses.sort(key=lambda item: item.analyser_id)
    findings.sort(
        key=lambda item: (
            item.analyser_id,
            item.path,
            item.symbol or "",
            item.evidence,
        )
    )
    return tuple(statuses), tuple(findings)


def validate_report(report: Report) -> None:
    universe = report.universe
    _require_oid(universe.commit, "report commit")
    _require_oid(universe.tree, "report tree")
    if not universe.analysed:
        raise Refusal("report universe has no analysed paths")
    if universe.analysed != tuple(sorted(set(universe.analysed))):
        raise Refusal("report analysed paths are not sorted and unique")
    excluded_paths = tuple(item.path for item in universe.excluded)
    if excluded_paths != tuple(sorted(set(excluded_paths))):
        raise Refusal("report excluded paths are not sorted and unique")
    if any(item.grade != EXCLUDING_GRADE for item in universe.excluded):
        raise Refusal("report carries a non-hard exclusion")
    if universe.tracked_count != len(universe.analysed) + len(universe.excluded):
        raise Refusal("report universe counts do not partition the tracked tree")
    expected_universe_id = universe_identity(
        universe.tree,
        universe.analysed,
        universe.excluded,
    )
    if universe.identity != expected_universe_id:
        raise Refusal("report universe identity does not match its paths")

    status_ids: set[str] = set()
    for item in report.statuses:
        if not item.analyser_id or item.analyser_id in status_ids:
            raise Refusal("analyser status identities are empty or repeated")
        if item.state not in ANALYSER_STATES:
            raise Refusal(
                f"analyser {item.analyser_id} has unknown state {item.state}"
            )
        if not item.detail:
            raise Refusal(f"analyser {item.analyser_id} has no detail")
        status_ids.add(item.analyser_id)
    if tuple(item.analyser_id for item in report.statuses) != tuple(sorted(status_ids)):
        raise Refusal("analyser statuses are not sorted by identity")

    finding_ids: set[str] = set()
    analysed = set(report.universe.analysed)
    for finding in report.findings:
        if finding.analyser_id not in status_ids:
            raise Refusal(
                f"finding {finding.identity} names unreported analyser "
                f"{finding.analyser_id}"
            )
        if finding.path not in analysed:
            raise Refusal(f"finding {finding.identity} names path outside the universe")
        if finding.confidence not in CONFIDENCE_LEVELS:
            raise Refusal(
                f"finding {finding.identity} has unknown confidence "
                f"{finding.confidence}"
            )
        if finding.identity in finding_ids:
            raise Refusal(f"finding identity repeats: {finding.identity}")
        finding_ids.add(finding.identity)
    if not report.statuses and report.findings:
        raise Refusal("findings exist although no analyser ran")
    expected_finding_order = tuple(
        sorted(
            report.findings,
            key=lambda item: (
                item.analyser_id,
                item.path,
                item.symbol or "",
                item.evidence,
            ),
        )
    )
    if report.findings != expected_finding_order:
        raise Refusal("findings are not sorted by stable report identity")


def build_report(root: Path) -> Report:
    universe = discover(root)
    statuses, findings = collect(root, universe)
    report = Report(universe=universe, statuses=statuses, findings=findings)
    validate_report(report)
    return report


def render_json(report: Report) -> str:
    return json.dumps(
        report.as_dict(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + chr(10)


def render_text(report: Report) -> str:
    document = report.as_dict()
    tree = document["tree"]
    universe = document["universe"]
    status = document["status"]
    lines = [
        f"{TOOL_ID} {TOOL_VERSION} report  schema {document['schema']}",
        f"commit    {tree['commit']}",
        f"tree      {tree['git_tree']}",
        f"universe  {universe['id']}",
        (
            f"paths     {universe['tracked_count']} tracked, "
            f"{universe['analysed_count']} analysed, "
            f"{universe['excluded_count']} excluded"
        ),
        f"status    {status['state']}  {status['detail']}",
    ]
    by_category = universe["excluded_by_category"]
    if by_category:
        summary = ", ".join(
            f"{name} {by_category[name]}" for name in sorted(by_category)
        )
        lines.append(f"excluded  {summary}")
    lines.extend(["", "analysers"])
    if not document["analysers"]:
        lines.append("  none ran; no reachability result was established")
    for analyser in document["analysers"]:
        version = f" {analyser['version']}" if analyser["version"] else ""
        lines.append(
            f"  {analyser['id']}{version}  {analyser['state']}  "
            f"{analyser['detail']}"
        )

    findings = document["findings"]
    lines.extend(["", f"findings  {len(findings)} candidate(s); report-only"])
    if not findings:
        lines.append("  none reported")
    for finding in findings:
        symbol = f" {finding['symbol']}" if finding["symbol"] else ""
        lines.append(
            f"  [{finding['confidence']}] {finding['id']}  "
            f"{finding['analyser_id']}  {finding['path']}{symbol}"
        )
        lines.append(f"      saw     {finding['evidence']}")
        lines.append(f"      but     {finding['false_positive_boundary']}")
    return chr(10).join(lines) + chr(10)


def confine(root: Path, candidate: str) -> Path:
    if not isinstance(candidate, str) or not candidate:
        raise Refusal("the output path is empty")
    if chr(0) in candidate:
        raise Refusal("the output path contains a null byte")
    if chr(92) in candidate or any(
        ord(character) < 32 or ord(character) == 127 for character in candidate
    ):
        raise Refusal("the output path is not a safe repository-relative POSIX path")
    supplied = Path(candidate)
    if supplied.is_absolute():
        raise Refusal("the output path must be repository-relative")
    parts = supplied.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise Refusal(f"the output path {candidate} escapes the repository root")
    if len(candidate.encode("utf-8")) > MAX_PATH_BYTES:
        raise Refusal(f"the output path exceeds {MAX_PATH_BYTES} bytes")
    if len(parts) < 2 or parts[0] != OWNED_OUTPUT_DIRECTORY:
        raise Refusal(
            f"the output path must be beneath the owned {OWNED_OUTPUT_DIRECTORY}/ sink"
        )
    target = root.resolve(strict=True).joinpath(*parts)
    if target == root.resolve(strict=True):
        raise Refusal("the repository root is not an output file")
    return target


def output_parts(root: Path, target: Path) -> tuple[str, ...]:
    root = root.resolve(strict=True)
    try:
        relative = target.relative_to(root)
    except ValueError as error:
        raise Refusal("the output path escapes the repository root") from error
    parts = relative.parts
    if (
        not parts
        or any(part in {"", ".", ".."} for part in parts)
        or chr(92) in relative.as_posix()
        or any(
            ord(character) < 32 or ord(character) == 127
            for character in relative.as_posix()
        )
        or len(relative.as_posix().encode("utf-8")) > MAX_PATH_BYTES
    ):
        raise Refusal("the output path is not a safe repository-relative POSIX path")
    if len(parts) < 2 or parts[0] != OWNED_OUTPUT_DIRECTORY:
        raise Refusal(
            f"the output path must be beneath the owned {OWNED_OUTPUT_DIRECTORY}/ sink"
        )
    return parts


def open_output_directory(root: Path, parts: tuple[str, ...]) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory_flag is None:
        raise Refusal("this platform cannot open output directories without following links")
    flags = os.O_RDONLY | nofollow | directory_flag | getattr(os, "O_CLOEXEC", 0)
    try:
        current_fd = os.open(root.resolve(strict=True), flags)
    except OSError as error:
        raise Refusal(f"the repository root cannot be opened safely: {error}") from error
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, mode=0o755, dir_fd=current_fd)
            except FileExistsError:
                pass
            except OSError as error:
                raise Refusal(
                    f"the output directory {part} cannot be created: {error}"
                ) from error
            try:
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except OSError as error:
                raise Refusal(
                    f"the output ancestor {part} is not a real directory: {error}"
                ) from error
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except BaseException:
        os.close(current_fd)
        raise


def require_regular_target(directory_fd: int, name: str) -> None:
    try:
        target_stat = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as error:
        raise Refusal(f"the output target cannot be inspected: {error}") from error
    if stat.S_ISLNK(target_stat.st_mode) or not stat.S_ISREG(target_stat.st_mode):
        raise Refusal("the output target is not a regular file")


def create_temporary(directory_fd: int) -> tuple[int, str]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise Refusal("this platform cannot create output files without following links")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | nofollow
        | getattr(os, "O_CLOEXEC", 0)
    )
    for _ in range(128):
        name = TEMP_PREFIX + os.urandom(16).hex()
        try:
            return os.open(name, flags, 0o600, dir_fd=directory_fd), name
        except FileExistsError:
            continue
        except OSError as error:
            raise Refusal(f"report temporary cannot be created: {error}") from error
    raise Refusal("report temporary name allocation was exhausted")


def atomic_write(root: Path, target: Path, payload: str) -> None:
    encoded = payload.encode("utf-8")
    if len(encoded) > MAX_REPORT_BYTES:
        raise Refusal(f"report exceeds {MAX_REPORT_BYTES} bytes")
    parts = output_parts(root, target)
    directory_fd = open_output_directory(root, parts)
    temporary_name: str | None = None
    try:
        require_regular_target(directory_fd, parts[-1])
        temporary_fd, temporary_name = create_temporary(directory_fd)
        with os.fdopen(temporary_fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temporary_name,
            parts[-1],
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        temporary_name = None
        os.fsync(directory_fd)
    except Refusal:
        raise
    except OSError as error:
        raise Refusal(f"report write failed: {error}") from error
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except OSError:
                pass
        os.close(directory_fd)


def command_report(arguments: argparse.Namespace) -> int:
    root = repository_root(Path(arguments.directory).resolve())
    report = build_report(root)
    rendered = render_json(report) if arguments.json else render_text(report)
    if arguments.output is None:
        sys.stdout.write(rendered)
    else:
        target = confine(root, arguments.output)
        atomic_write(root, target, rendered)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dead_code.py",
        description=__doc__,
    )
    parser.add_argument(
        "--directory",
        default=".",
        help="a path inside the repository to analyse",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    report = subparsers.add_parser(
        "report",
        help="report the universe and its candidates",
    )
    report.add_argument(
        "--json",
        action="store_true",
        help="emit canonical JSON",
    )
    report.add_argument(
        "--output",
        help="write inside the repository instead of stdout",
    )
    report.set_defaults(handler=command_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return arguments.handler(arguments)
    except Refusal as refusal:
        print(f"dead_code.py: {refusal}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
