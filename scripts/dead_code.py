#!/usr/bin/env python3
"""Build a report-only dead-code inventory for one clean Git tree.

The command discovers tracked paths, applies hard Horos classifications and
renders one deterministic model as text or JSON. Step 1 registers no analyser,
so the report says that no reachability result was established. It never
deletes source and a finding count is never an exit gate.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable

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
MAX_PYTHON_FILE_BYTES = 4 * 1024 * 1024
MAX_PYTHON_TOTAL_BYTES = 96 * 1024 * 1024
MAX_COVERAGE_BYTES = 32 * 1024 * 1024
MAX_COVERAGE_PROCESS_BYTES = 16 * 1024 * 1024
MAX_COVERAGE_PROCESSES = 4096
MAX_RUNNER_OUTPUT_BYTES = 32 * 1024 * 1024
RUNNER_TIMEOUT_SECONDS = 3600
COVERAGE_DRAIN_SECONDS = 5.0
CHECK_RUNNER = Path("scripts") / "run_checks.py"
MONITOR_DIRECTORY = Path("scripts") / "dead_code_monitoring"
COVERAGE_SCHEMA_ID = "dead-code-coverage/v1"
COVERAGE_ACTIVE_ENV = "WILDCAT_DEAD_CODE_COVERAGE_ACTIVE"
COVERAGE_OUTPUT_ENV = "WILDCAT_DEAD_CODE_COVERAGE_OUTPUT"
CHECK_CONTAINMENT_ENV = "WILDCAT_CHECK_CONTAINMENT"
PYTHON_ANALYSER_VERSION = "1"
COVERAGE_ANALYSER_VERSION = "sys.monitoring/3.14"
ANALYSER_STATES = frozenset({"ran", "not-available", "degraded", "failed"})
CONFIDENCE_LEVELS = frozenset({"high", "medium", "low"})
ANALYSER_RECORD_KINDS = frozenset({"file", "check"})
ANALYSER_RECORD_STATES = frozenset(
    {"parsed", "parse-error", "skipped", "passed", "failed", "unavailable"}
)

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
class AnalyserRecord:
    record_id: str
    kind: str
    state: str
    detail: str
    bytes_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.record_id,
            "kind": self.kind,
            "state": self.state,
            "detail": self.detail,
            "bytes": self.bytes_count,
        }


@dataclass(frozen=True)
class AnalyserStatus:
    analyser_id: str
    state: str
    version: str | None
    detail: str
    records: tuple[AnalyserRecord, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.analyser_id,
            "state": self.state,
            "version": self.version,
            "detail": self.detail,
            "records": [record.as_dict() for record in self.records],
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
    cwd_fd: int | None = None,
    env: dict[str, str] | None = None,
) -> tuple[bytes, bytes, int]:
    """Run fixed argv while bounding time and combined captured output."""
    process_cwd: Path | None = cwd
    pass_fds: tuple[int, ...] = ()
    preexec_fn: Callable[[], None] | None = None
    if cwd_fd is not None:
        process_cwd = None
        pass_fds = (cwd_fd,)

        def enter_opened_directory() -> None:
            os.fchdir(cwd_fd)
            os.close(cwd_fd)

        preexec_fn = enter_opened_directory
    try:
        process = subprocess.Popen(
            argv,
            cwd=process_cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            pass_fds=pass_fds,
            preexec_fn=preexec_fn,
            env=env,
        )
    except FileNotFoundError as error:
        raise Refusal(f"{argv[0]} is not available on PATH") from error
    except (OSError, subprocess.SubprocessError) as error:
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


def run_git(root: Path, *arguments: str, root_fd: int | None = None) -> str:
    argv = ["git", "-C", str(root), *arguments]
    if root_fd is not None:
        argv = ["git", *arguments]
    stdout, stderr, returncode = run_process(
        argv,
        cwd=root,
        timeout_seconds=GIT_TIMEOUT_SECONDS,
        output_limit=MAX_GIT_OUTPUT_BYTES,
        cwd_fd=root_fd,
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


def resolve_commit(root: Path, *, root_fd: int | None = None) -> str:
    return _require_oid(
        run_git(root, "rev-parse", "HEAD", root_fd=root_fd).strip(),
        "HEAD",
    )


def resolve_tree(root: Path, commit: str, *, root_fd: int | None = None) -> str:
    return _require_oid(
        run_git(
            root,
            "rev-parse",
            f"{commit}^{{tree}}",
            root_fd=root_fd,
        ).strip(),
        "HEAD tree",
    )


def require_clean_tree(root: Path, *, root_fd: int | None = None) -> None:
    porcelain = run_git(
        root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=no",
        root_fd=root_fd,
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


def tracked_paths(
    root: Path,
    commit: str,
    *,
    root_fd: int | None = None,
) -> tuple[str, ...]:
    listing = run_git(
        root,
        "ls-tree",
        "-r",
        "--name-only",
        "-z",
        commit,
        root_fd=root_fd,
    )
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


def read_commit_regular(
    root: Path,
    commit: str,
    repository_path: str,
    *,
    limit: int,
    label: str,
    root_fd: int | None = None,
) -> str:
    """Read one bounded regular blob from the recorded Git tree."""
    listing = run_git(
        root,
        "ls-tree",
        "-z",
        commit,
        "--",
        repository_path,
        root_fd=root_fd,
    )
    records = [record for record in listing.split(chr(0)) if record]
    if not records:
        raise Refusal(f"{label} is absent from commit {commit}")
    if len(records) != 1 or chr(9) not in records[0]:
        raise Refusal(f"{label} has an ambiguous Git tree record")
    metadata, listed_path = records[0].split(chr(9), 1)
    fields = metadata.split()
    if len(fields) != 3 or listed_path != repository_path:
        raise Refusal(f"{label} has a malformed Git tree record")
    mode, object_type, object_id = fields
    if mode not in {"100644", "100755"} or object_type != "blob":
        raise Refusal(f"{label} is not a regular file in commit {commit}")
    _require_oid(object_id, f"{label} blob")
    size_text = run_git(
        root,
        "cat-file",
        "-s",
        object_id,
        root_fd=root_fd,
    ).strip()
    if not size_text.isdecimal():
        raise Refusal(f"{label} blob size is not an integer")
    size = int(size_text)
    if size > limit:
        raise Refusal(f"{label} exceeds {limit} bytes")
    stdout, stderr, returncode = run_process(
        ["git", "cat-file", "blob", object_id]
        if root_fd is not None
        else ["git", "-C", str(root), "cat-file", "blob", object_id],
        cwd=root,
        timeout_seconds=GIT_TIMEOUT_SECONDS,
        output_limit=limit,
        cwd_fd=root_fd,
    )
    if returncode != 0:
        detail = decode_output(stderr, "git stderr").strip()
        if not detail:
            detail = f"exit {returncode}"
        raise Refusal(f"{label} blob cannot be read: {detail}")
    if len(stdout) != size:
        raise Refusal(f"{label} blob size changed while it was read")
    return decode_output(stdout, label)


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document: dict[str, object] = {}
    for key, value in pairs:
        if key in document:
            raise DuplicateKey(key)
        document[key] = value
    return document


def load_boundary(
    root: Path,
    *,
    commit: str | None = None,
    root_fd: int | None = None,
) -> Classification:
    label = BOUNDARY_PATH.as_posix()
    owns_root_fd = root_fd is None
    if root_fd is None:
        root_fd = open_repository_directory(root)
    try:
        recorded_commit = (
            resolve_commit(root, root_fd=root_fd) if commit is None else commit
        )
        raw = read_commit_regular(
            root,
            recorded_commit,
            label,
            limit=MAX_BOUNDARY_BYTES,
            label=label,
            root_fd=root_fd,
        )
    finally:
        if owns_root_fd:
            os.close(root_fd)
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


def discover(root: Path, *, root_fd: int | None = None) -> Universe:
    owns_root_fd = root_fd is None
    if root_fd is None:
        root_fd = open_repository_directory(root)
    try:
        require_clean_tree(root, root_fd=root_fd)
        commit = resolve_commit(root, root_fd=root_fd)
        tree = resolve_tree(root, commit, root_fd=root_fd)
        tracked = tracked_paths(root, commit, root_fd=root_fd)
        classified = load_boundary(root, commit=commit, root_fd=root_fd)

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
        require_clean_tree(root, root_fd=root_fd)
    finally:
        if owns_root_fd:
            os.close(root_fd)

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


@dataclass(frozen=True)
class ParsedPython:
    path: str
    module: str | None
    tree: ast.Module
    bytes_count: int
    dynamic_boundaries: tuple[str, ...]
    retained_names: frozenset[str]
    imports: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class PythonSnapshot:
    files: tuple[ParsedPython, ...]
    records: tuple[AnalyserRecord, ...]
    module_paths: dict[str, str]
    reachable_paths: frozenset[str]
    entry_paths: frozenset[str]
    degraded: bool


def python_module_name(path: str) -> str | None:
    if not path.endswith(".py"):
        return None
    parts = list(PurePosixPath(path).parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = parts[-1][:-3]
    if not parts or any(not part.isidentifier() for part in parts):
        return None
    return ".".join(parts)


def _main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    if not isinstance(test.ops[0], (ast.Eq, ast.NotEq)) or len(test.comparators) != 1:
        return False
    sides = (test.left, test.comparators[0])
    return any(
        isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
        for left, right in (sides, tuple(reversed(sides)))
    )


def _call_name(node: ast.Call) -> str:
    target = node.func
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return ""


def _literal_exports(tree: ast.Module) -> set[str]:
    exports: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            continue
        value = node.value
        if not isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            continue
        exports.update(
            item.value
            for item in value.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
    return exports


def _python_dynamic_boundaries(tree: ast.Module) -> tuple[str, ...]:
    boundaries: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.decorator_list:
                boundaries.add("decorator-registration")
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        lowered = name.lower()
        if any(token in lowered for token in ("register", "callback", "fixture", "route")):
            boundaries.add("dynamic-registration")
        if name in {"__import__", "import_module"}:
            if not node.args or not (
                isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                boundaries.add("computed-import")
        if name == "getattr" and (
            len(node.args) < 2
            or not (
                isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            )
        ):
            boundaries.add("computed-getattr")
    if _literal_exports(tree):
        boundaries.add("literal-__all__")
    return tuple(sorted(boundaries))


def _retained_names(path: str, tree: ast.Module) -> frozenset[str]:
    retained = _literal_exports(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.decorator_list or node.name.startswith("test_"):
                retained.add(node.name)
        if isinstance(node, ast.Call):
            lowered = _call_name(node).lower()
            if any(token in lowered for token in ("register", "callback", "fixture", "route")):
                retained.update(
                    argument.id for argument in node.args if isinstance(argument, ast.Name)
                )
        if _main_guard(node):
            retained.update(
                child.id
                for child in ast.walk(node)
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
            )
    if path.startswith("tests/") or "/fixtures/" in f"/{path}":
        retained.update(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        )
    return frozenset(retained)


def _import_targets(
    module: str | None,
    tree: ast.Module,
    *,
    package_module: bool,
) -> tuple[tuple[str, int], ...]:
    targets: set[tuple[str, int]] = set()
    package = [] if module is None else module.split(".")
    if not package_module:
        package = package[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.update((alias.name, node.lineno) for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            remove = node.level - 1
            base = package[: max(0, len(package) - remove)]
        else:
            base = []
        if node.module:
            base.extend(node.module.split("."))
        if base:
            targets.add((".".join(base), node.lineno))
        for alias in node.names:
            if alias.name != "*" and base:
                targets.add((".".join([*base, alias.name]), node.lineno))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node) not in {"__import__", "import_module"}:
            continue
        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            targets.add((node.args[0].value, node.lineno))
    return tuple(sorted(targets))


def _check_map_entry_paths(
    root: Path,
    universe: Universe,
    module_paths: dict[str, str],
    *,
    root_fd: int,
) -> set[str]:
    path = "tests/check-map-v1.json"
    if path not in universe.analysed:
        return set()
    try:
        raw = read_commit_regular(
            root,
            universe.commit,
            path,
            limit=MAX_BOUNDARY_BYTES,
            label=path,
            root_fd=root_fd,
        )
        document = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (Refusal, DuplicateKey, json.JSONDecodeError):
        return set()
    checks = document.get("checks") if isinstance(document, dict) else None
    if not isinstance(checks, dict):
        return set()
    seeds: set[str] = set()
    for body in checks.values():
        if not isinstance(body, dict):
            continue
        script = body.get("script")
        if isinstance(script, str) and script.endswith(".py"):
            seeds.add(script)
        argv = body.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            continue
        for item in argv[1:]:
            if item.endswith(".py"):
                seeds.add(item)
            elif item in module_paths:
                seeds.add(module_paths[item])
    return seeds


def parse_python_snapshot(root: Path, universe: Universe) -> PythonSnapshot:
    parsed: list[ParsedPython] = []
    records: list[AnalyserRecord] = []
    total = 0
    degraded = False
    root_fd = open_repository_directory(root)
    try:
        for path in (item for item in universe.analysed if item.endswith(".py")):
            if total >= MAX_PYTHON_TOTAL_BYTES:
                degraded = True
                records.append(
                    AnalyserRecord(path, "file", "skipped", "aggregate Python byte limit reached", 0)
                )
                continue
            try:
                source = read_commit_regular(
                    root,
                    universe.commit,
                    path,
                    limit=MAX_PYTHON_FILE_BYTES,
                    label=path,
                    root_fd=root_fd,
                )
            except Refusal as error:
                degraded = True
                records.append(AnalyserRecord(path, "file", "parse-error", str(error), 0))
                continue
            size = len(source.encode("utf-8"))
            total += size
            if total > MAX_PYTHON_TOTAL_BYTES:
                degraded = True
                records.append(
                    AnalyserRecord(path, "file", "skipped", "aggregate Python byte limit exceeded", size)
                )
                continue
            try:
                tree = ast.parse(source, filename=path, type_comments=True)
            except (SyntaxError, ValueError, MemoryError) as error:
                degraded = True
                line = getattr(error, "lineno", None)
                suffix = f" at line {line}" if isinstance(line, int) else ""
                records.append(
                    AnalyserRecord(path, "file", "parse-error", f"{type(error).__name__}{suffix}", size)
                )
                continue
            dynamic = _python_dynamic_boundaries(tree)
            detail = "parsed"
            if dynamic:
                detail += "; dynamic boundaries: " + ", ".join(dynamic)
            records.append(AnalyserRecord(path, "file", "parsed", detail, size))
            module = python_module_name(path)
            parsed.append(
                ParsedPython(
                    path=path,
                    module=module,
                    tree=tree,
                    bytes_count=size,
                    dynamic_boundaries=dynamic,
                    retained_names=_retained_names(path, tree),
                    imports=_import_targets(
                        module,
                        tree,
                        package_module=path.endswith("/__init__.py") or path == "__init__.py",
                    ),
                )
            )

        module_paths = {
            item.module: item.path
            for item in parsed
            if item.module is not None
        }
        seeds = {
            item.path
            for item in parsed
            if item.path.startswith("tests/")
            or item.path.endswith("/__main__.py")
            or any(_main_guard(node) for node in item.tree.body)
        }
        seeds.update(_check_map_entry_paths(root, universe, module_paths, root_fd=root_fd))
    finally:
        os.close(root_fd)

    edges: dict[str, set[str]] = {item.path: set() for item in parsed}
    for item in parsed:
        for target, _line in item.imports:
            probe = target
            while probe:
                destination = module_paths.get(probe)
                if destination is not None:
                    edges[item.path].add(destination)
                    break
                probe = probe.rpartition(".")[0]
    reachable = set(path for path in seeds if path in edges)
    pending = list(reachable)
    while pending:
        source = pending.pop()
        for destination in edges[source]:
            if destination not in reachable:
                reachable.add(destination)
                pending.append(destination)
    return PythonSnapshot(
        files=tuple(parsed),
        records=tuple(sorted(records, key=lambda item: item.record_id)),
        module_paths=module_paths,
        reachable_paths=frozenset(reachable),
        entry_paths=frozenset(path for path in seeds if path in edges),
        degraded=degraded,
    )


def _candidate(
    path: str,
    symbol: str,
    evidence: str,
    confidence: str,
    boundary: str,
    *,
    analyser_id: str = "python",
) -> Finding:
    return Finding(analyser_id, path, symbol, evidence, confidence, boundary)


def _function_scope_nodes(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterable[ast.AST]:
    """Walk stores in one function scope without entering child scopes."""
    boundaries = (
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Lambda,
        ast.ClassDef,
        ast.ListComp,
        ast.SetComp,
        ast.DictComp,
        ast.GeneratorExp,
    )
    pending = list(reversed(function.body))
    while pending:
        node = pending.pop()
        yield node
        if isinstance(node, boundaries):
            continue
        pending.extend(reversed(list(ast.iter_child_nodes(node))))


def _unused_bindings(item: ParsedPython) -> Iterable[Finding]:
    loads = {
        node.id
        for node in ast.walk(item.tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    } | set(_literal_exports(item.tree))
    confidence = "low" if item.dynamic_boundaries else "high"
    boundary = (
        "computed references or registration may consume this binding"
        if item.dynamic_boundaries
        else "scope-insensitive name loading can retain a shadowed binding"
    )
    seen_imports: set[tuple[str, int]] = set()
    for node in ast.walk(item.tree):
        if isinstance(node, ast.Import):
            aliases = node.names
        elif isinstance(node, ast.ImportFrom):
            aliases = node.names
        else:
            continue
        for alias in aliases:
            if alias.name == "*":
                continue
            binding = alias.asname or alias.name.split(".")[0]
            identity = (binding, node.lineno)
            if binding in loads or binding.startswith("_") or identity in seen_imports:
                continue
            seen_imports.add(identity)
            yield _candidate(
                item.path,
                f"{binding}@{node.lineno}",
                f"import binding {binding} has no Name load in the parsed file",
                confidence,
                boundary,
            )

    for function in (
        node
        for node in ast.walk(item.tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        function_loads = {
            node.id
            for node in ast.walk(function)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        scope_nodes = tuple(_function_scope_nodes(function))
        assignments: dict[str, int] = {}
        external_bindings = {
            name
            for declaration in scope_nodes
            if isinstance(declaration, (ast.Global, ast.Nonlocal))
            for name in declaration.names
        }
        for node in scope_nodes:
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                assignments.setdefault(node.id, node.lineno)
        for name, line in sorted(assignments.items()):
            if name in function_loads or name in external_bindings or name.startswith("_"):
                continue
            yield _candidate(
                item.path,
                f"{function.name}.{name}@{line}",
                f"local binding {name} is stored but has no Name load in {function.name}",
                confidence,
                "a nested dynamic lookup or scope-insensitive shadow may consume the binding",
            )


def _block_findings(item: ParsedPython) -> Iterable[Finding]:
    confidence = "low" if item.dynamic_boundaries else "high"

    def inspect(block: list[ast.stmt]) -> Iterable[Finding]:
        terminator_line: int | None = None
        for statement in block:
            if terminator_line is not None:
                yield _candidate(
                    item.path,
                    f"line:{statement.lineno}:unreachable",
                    f"statement follows an unconditional terminator at line {terminator_line}",
                    confidence,
                    "exception handling, generated bytecode or parser limitations may alter control flow",
                )
            for field in ("body", "orelse", "finalbody"):
                child = getattr(statement, field, None)
                if isinstance(child, list):
                    yield from inspect(child)
            if isinstance(statement, ast.Try):
                for handler in statement.handlers:
                    yield from inspect(handler.body)
            if isinstance(statement, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                terminator_line = statement.lineno

    yield from inspect(item.tree.body)
    for node in ast.walk(item.tree):
        if not isinstance(node, (ast.If, ast.While)):
            continue
        truth: bool | None = None
        if isinstance(node.test, ast.Constant) and isinstance(node.test.value, (bool, type(None))):
            truth = bool(node.test.value)
        if truth is None:
            continue
        direction = "true" if truth else "false"
        yield _candidate(
            item.path,
            f"line:{node.lineno}:constant-{direction}",
            f"branch condition is the literal constant {node.test.value!r}",
            confidence,
            "the syntax may be an intentional feature flag or type-checking guard",
        )


def analyse_python(root: Path, universe: Universe) -> tuple[AnalyserStatus, tuple[Finding, ...]]:
    snapshot = parse_python_snapshot(root, universe)
    findings: list[Finding] = []
    for item in snapshot.files:
        findings.extend(_unused_bindings(item))
        findings.extend(_block_findings(item))
        if (
            item.module is not None
            and snapshot.entry_paths
            and item.path not in snapshot.reachable_paths
            and not item.path.endswith("/__init__.py")
        ):
            findings.append(
                _candidate(
                    item.path,
                    "<module>",
                    "no path from a declared check, test or __main__ seed reaches this module over static imports",
                    "low",
                    "computed imports, plugin manifests and prose entry points are outside the static import graph",
                )
            )
    state = "degraded" if snapshot.degraded else "ran"
    parsed_count = sum(record.state == "parsed" for record in snapshot.records)
    detail = (
        f"parsed {parsed_count}/{len(snapshot.records)} bounded Python files; "
        f"{len(snapshot.entry_paths)} entry seed(s)"
    )
    if snapshot.degraded:
        detail += "; one or more files did not parse"
    return (
        AnalyserStatus("python", state, PYTHON_ANALYSER_VERSION, detail, snapshot.records),
        tuple(findings),
    )


def _json_document(payload: bytes | str, label: str) -> dict[str, object]:
    try:
        document = json.loads(payload, object_pairs_hook=reject_duplicate_keys)
    except DuplicateKey as error:
        raise Refusal(f"{label} repeats JSON key {error.args[0]}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise Refusal(f"{label} is not valid UTF-8 JSON: {error}") from error
    if not isinstance(document, dict):
        raise Refusal(f"{label} is not a JSON object")
    return document


def _python_argv(argv: object) -> bool:
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
        return False
    executable = PurePosixPath(argv[0]).name
    return re.fullmatch(r"python(?:3(?:\.14)?)?", executable) is not None


def _coverage_recurses(argv: list[str]) -> bool:
    normalised = [item.replace(chr(92), "/") for item in argv]
    return any(item.endswith("scripts/dead_code.py") for item in normalised) and "coverage" in argv


def _runner_plan(root: Path, scopes: tuple[str, ...]) -> dict[str, object]:
    argv = [sys.executable, CHECK_RUNNER.as_posix()]
    for scope in scopes:
        argv.extend(["--scope", scope])
    argv.extend(["--plan", "--format", "json"])
    stdout, stderr, returncode = run_process(
        argv,
        cwd=root,
        timeout_seconds=GIT_TIMEOUT_SECONDS,
        output_limit=MAX_RUNNER_OUTPUT_BYTES,
    )
    if returncode != 0:
        detail = decode_output(stderr, "check-plan stderr").strip() or f"exit {returncode}"
        raise Refusal(f"checked runner plan failed: {detail}")
    plan = _json_document(stdout, "checked runner plan")
    if plan.get("schema") != "wildcat.check-plan.v1":
        raise Refusal("checked runner returned an unknown plan schema")
    if plan.get("requested_scopes") != list(scopes):
        raise Refusal("checked runner plan is not bound to the requested scopes")
    selected = plan.get("selected_checks")
    if not isinstance(selected, list) or not selected:
        raise Refusal("checked runner selected no checks for coverage")
    identifiers: set[str] = set()
    for index, check in enumerate(selected):
        if not isinstance(check, dict):
            raise Refusal(f"checked runner plan check {index} is not an object")
        identifier = check.get("id")
        argv_value = check.get("argv")
        if not isinstance(identifier, str) or not identifier or identifier in identifiers:
            raise Refusal("checked runner plan has empty or repeated check identities")
        identifiers.add(identifier)
        if not _python_argv(argv_value):
            raise Refusal(
                f"coverage scope includes non-Python check {identifier}; select a Python-only scope"
            )
        assert isinstance(argv_value, list)
        if _coverage_recurses(argv_value):
            raise Refusal(f"coverage check {identifier} recursively invokes dead_code.py coverage")
    return plan


def _create_process_directory(root: Path, root_fd: int, run_id: str) -> tuple[Path, int]:
    relative = f"{OWNED_OUTPUT_DIRECTORY}/coverage-processes-{run_id}/record.json"
    target = confine(root, relative)
    parts = output_parts(root, target)
    directory_fd = open_output_directory(root_fd, parts)
    return target.parent, directory_fd


def _read_process_documents(
    directory: Path,
    directory_fd: int,
    run_id: str,
) -> list[tuple[dict[str, object], int]]:
    try:
        names = sorted(os.listdir(directory_fd))
    except OSError as error:
        raise Refusal(f"coverage process directory cannot be listed: {error}") from error
    if len(names) > MAX_COVERAGE_PROCESSES:
        raise Refusal(f"coverage emitted more than {MAX_COVERAGE_PROCESSES} process records")
    documents: list[tuple[dict[str, object], int]] = []
    total_bytes = 0
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    for name in names:
        if re.fullmatch(r"process-[0-9]+-[0-9a-f]{32}\.json", name) is None:
            raise Refusal(f"coverage process directory contains foreign entry {name}")
        try:
            fd = os.open(name, flags, dir_fd=directory_fd)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise Refusal(f"coverage process record {name} is not regular")
            if info.st_size > MAX_COVERAGE_PROCESS_BYTES:
                raise Refusal(f"coverage process record {name} exceeds its byte limit")
            with os.fdopen(fd, "rb") as handle:
                payload = handle.read(MAX_COVERAGE_PROCESS_BYTES + 1)
        except Refusal:
            raise
        except OSError as error:
            raise Refusal(f"coverage process record {name} cannot be read: {error}") from error
        if len(payload) > MAX_COVERAGE_PROCESS_BYTES or len(payload) != info.st_size:
            raise Refusal(f"coverage process record {name} changed or exceeded its byte limit")
        total_bytes += len(payload)
        if total_bytes > MAX_COVERAGE_BYTES:
            raise Refusal(f"coverage process records exceed {MAX_COVERAGE_BYTES} aggregate bytes")
        document = _json_document(payload, f"coverage process record {name}")
        if document.get("schema") != "dead-code-process-coverage/v1" or document.get("run") != run_id:
            raise Refusal(f"coverage process record {name} has the wrong identity")
        documents.append((document, len(payload)))
    return documents


def _remove_process_directory(directory_fd: int, root_fd: int, name: str) -> None:
    try:
        for entry in os.listdir(directory_fd):
            if re.fullmatch(r"process-[0-9]+-[0-9a-f]{32}\.json", entry):
                try:
                    os.unlink(entry, dir_fd=directory_fd)
                except OSError:
                    pass
    finally:
        os.close(directory_fd)
    try:
        dead_code_fd = os.open(
            OWNED_OUTPUT_DIRECTORY,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=root_fd,
        )
    except OSError:
        return
    try:
        os.rmdir(name, dir_fd=dead_code_fd)
    except OSError:
        pass
    finally:
        os.close(dead_code_fd)


def _argv_matches(process_argv: object, planned_argv: object) -> bool:
    if not _python_argv(process_argv) or not _python_argv(planned_argv):
        return False
    assert isinstance(process_argv, list)
    assert isinstance(planned_argv, list)
    return process_argv[1:] == planned_argv[1:]


def _normalise_coverage_events(
    lines: list[object],
    branches: list[object],
    analysed: set[str],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    normal_lines: set[tuple[str, str, int]] = set()
    normal_branches: set[tuple[str, str, int, int, str]] = set()
    for item in lines:
        if not isinstance(item, dict):
            raise Refusal("coverage line event is not an object")
        path = item.get("path")
        function = item.get("function")
        line = item.get("line")
        if (
            not isinstance(path, str)
            or not isinstance(function, str)
            or not isinstance(line, int)
            or isinstance(line, bool)
            or line < 1
        ):
            raise Refusal("coverage line event has an invalid identity")
        validate_repository_path(path, "coverage line path")
        if path in analysed:
            normal_lines.add((path, function, line))
    for item in branches:
        if not isinstance(item, dict):
            raise Refusal("coverage branch event is not an object")
        path = item.get("path")
        function = item.get("function")
        source = item.get("from_line")
        target = item.get("to_line")
        direction = item.get("direction")
        if (
            not isinstance(path, str)
            or not isinstance(function, str)
            or not isinstance(source, int)
            or isinstance(source, bool)
            or source < 1
            or not isinstance(target, int)
            or isinstance(target, bool)
            or target < 1
            or not isinstance(direction, str)
            or direction not in {"left", "right"}
        ):
            raise Refusal("coverage branch event has an invalid identity")
        validate_repository_path(path, "coverage branch path")
        if path in analysed:
            normal_branches.add((path, function, source, target, direction))
    return (
        [
            {"path": path, "function": function, "line": line}
            for path, function, line in sorted(normal_lines)
        ],
        [
            {
                "path": path,
                "function": function,
                "from_line": source,
                "to_line": target,
                "direction": direction,
            }
            for path, function, source, target, direction in sorted(normal_branches)
        ],
    )


def _coverage_process_complete(status: object) -> bool:
    if not isinstance(status, dict):
        raise Refusal("coverage process status is not an object")
    state = status.get("state")
    truncated = status.get("truncated")
    errors = status.get("errors")
    if (
        not isinstance(state, str)
        or state not in {"ran", "degraded"}
        or not isinstance(truncated, bool)
        or not isinstance(errors, list)
        or not all(isinstance(error, str) and error for error in errors)
    ):
        raise Refusal("coverage process status is malformed")
    return state == "ran" and not truncated and not errors


def aggregate_coverage(
    plan: dict[str, object],
    run: dict[str, object],
    process_documents: list[tuple[dict[str, object], int]],
    universe: Universe,
) -> dict[str, object]:
    for field in ("map_digest", "requested_scopes", "selected_checks"):
        if run.get(field) != plan.get(field):
            raise Refusal(
                f"checked runner result does not match the preflight plan field {field}"
            )
    selected = plan.get("selected_checks")
    results = run.get("checks")
    if not isinstance(selected, list) or not isinstance(results, list):
        raise Refusal("checked runner record omits selected checks or results")
    planned: dict[str, dict[str, object]] = {}
    for item in selected:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise Refusal("checked runner selected-check record is malformed")
        identifier = item["id"]
        if not identifier or identifier in planned:
            raise Refusal("checked runner plan has an empty or repeated check identity")
        planned[identifier] = item
    terminal: dict[str, dict[str, object]] = {}
    for item in results:
        if not isinstance(item, dict) or not isinstance(item.get("check"), str):
            raise Refusal("checked runner terminal record is malformed")
        identifier = item["check"]
        if not identifier or identifier in terminal:
            raise Refusal("checked runner terminal record has an empty or repeated check identity")
        terminal[identifier] = item
    if set(terminal) != set(planned):
        raise Refusal("checked runner terminal records do not match its plan")

    marker_to_check: dict[str, str] = {}
    degraded_reasons: set[str] = set()
    for document, _size in process_documents:
        process = document.get("process")
        if not isinstance(process, dict):
            raise Refusal("coverage process record omits process identity")
        marker = process.get("containment")
        argv = process.get("argv")
        if not isinstance(marker, str) or not marker:
            raise Refusal("coverage process record omits containment identity")
        matches = [
            check_id
            for check_id, check in planned.items()
            if _argv_matches(argv, check.get("argv"))
        ]
        if len(matches) == 1:
            prior = marker_to_check.get(marker)
            if prior is not None and prior != matches[0]:
                degraded_reasons.add("one process group matched multiple checks")
            marker_to_check[marker] = matches[0]

    public_processes: list[dict[str, object]] = []
    bytes_by_check = {check_id: 0 for check_id in planned}
    process_count_by_check = {check_id: 0 for check_id in planned}
    for document, size in process_documents:
        process = document["process"]
        assert isinstance(process, dict)
        marker = process["containment"]
        assert isinstance(marker, str)
        check_id = marker_to_check.get(marker)
        if check_id is None:
            degraded_reasons.add("one monitored process group could not be attributed")
            continue
        status = document.get("status")
        lines = document.get("lines")
        branches = document.get("branches")
        if not isinstance(status, dict) or not isinstance(lines, list) or not isinstance(branches, list):
            raise Refusal("coverage process record omits status, lines or branches")
        lines, branches = _normalise_coverage_events(
            lines,
            branches,
            set(universe.analysed),
        )
        if not _coverage_process_complete(status):
            degraded_reasons.add(f"check {check_id} emitted a degraded process record")
        bytes_by_check[check_id] += size
        process_count_by_check[check_id] += 1
        group_id = digest_json({"run": document.get("run"), "containment": marker})
        process_id = digest_json(
            {
                "group": group_id,
                "pid": process.get("pid"),
                "parent_pid": process.get("parent_pid"),
                "lines": lines,
                "branches": branches,
            }
        )
        public_processes.append(
            {
                "id": process_id,
                "group": group_id,
                "check": check_id,
                "pid": process.get("pid"),
                "parent_pid": process.get("parent_pid"),
                "status": status,
                "bytes": size,
                "lines": lines,
                "branches": branches,
            }
        )

    check_records: list[dict[str, object]] = []
    for check_id in sorted(planned):
        result = terminal[check_id]
        state = result.get("status")
        if state != "passed":
            degraded_reasons.add(f"check {check_id} ended {state}")
        if process_count_by_check[check_id] == 0:
            degraded_reasons.add(f"check {check_id} emitted no process record")
        check_records.append(
            {
                "id": check_id,
                "state": state,
                "duration_seconds": result.get("duration_seconds"),
                "processes": process_count_by_check[check_id],
                "bytes": bytes_by_check[check_id],
            }
        )
    if run.get("schema") != "wildcat.check-run.v1" or run.get("outcome") != "green":
        degraded_reasons.add(f"checked runner outcome was {run.get('outcome')}")
    public_processes.sort(key=lambda item: (str(item["check"]), str(item["id"])))
    state = "degraded" if degraded_reasons else "ran"
    return {
        "schema": COVERAGE_SCHEMA_ID,
        "tool": {"id": "sys.monitoring", "python": sys.version.split()[0]},
        "tree": {"commit": universe.commit, "git_tree": universe.tree, "universe": universe.identity},
        "plan": {
            "schema": plan.get("schema"),
            "map_digest": plan.get("map_digest"),
            "requested_scopes": plan.get("requested_scopes"),
            "selected_checks": sorted(planned),
        },
        "status": {
            "state": state,
            "detail": (
                "every selected Python check completed with process coverage"
                if not degraded_reasons
                else "; ".join(sorted(degraded_reasons))
            ),
        },
        "checks": check_records,
        "processes": public_processes,
    }


def _coverage_environment(root: Path, process_directory: Path, run_id: str) -> dict[str, str]:
    environment = dict(os.environ)
    monitoring_path = str(root / MONITOR_DIRECTORY)
    inherited_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = monitoring_path + (
        os.pathsep + inherited_python_path if inherited_python_path else ""
    )
    runtime_directory = str(Path(sys.executable).parent)
    inherited_path = environment.get("PATH")
    environment["PATH"] = runtime_directory + (
        os.pathsep + inherited_path if inherited_path else ""
    )
    environment[COVERAGE_ACTIVE_ENV] = run_id
    environment[COVERAGE_OUTPUT_ENV] = str(process_directory)
    return environment


def _coverage_survivor_pids(run_id: str) -> list[int]:
    if len(run_id) != 32 or any(character not in "0123456789abcdef" for character in run_id):
        raise Refusal("coverage run identity is malformed")
    try:
        listing = subprocess.run(
            ["ps", "axeww", "-o", "pid=,command="],
            capture_output=True,
            shell=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal(f"coverage process sweep is unavailable: {error}") from error
    if listing.returncode != 0 or len(listing.stdout) > MAX_GIT_OUTPUT_BYTES:
        raise Refusal("coverage process sweep failed or exceeded its output bound")
    token = f"{COVERAGE_ACTIVE_ENV}={run_id}"
    pids: list[int] = []
    for line in listing.stdout.decode("utf-8", "replace").splitlines():
        stripped = line.strip()
        if token not in stripped:
            continue
        pid_text = stripped.split(None, 1)[0]
        if pid_text.isdigit() and int(pid_text) != os.getpid():
            pids.append(int(pid_text))
    return sorted(set(pids))


def _terminate_coverage_processes(run_id: str) -> None:
    survivors = _coverage_survivor_pids(run_id)
    for requested_signal in (signal.SIGTERM, signal.SIGKILL):
        if not survivors:
            return
        for pid in survivors:
            try:
                os.kill(pid, requested_signal)
            except OSError:
                continue
        deadline = time.monotonic() + COVERAGE_DRAIN_SECONDS
        while time.monotonic() < deadline:
            survivors = _coverage_survivor_pids(run_id)
            if not survivors:
                return
            time.sleep(0.05)
    if survivors:
        raise Refusal(
            "coverage process recovery could not drain pid(s): "
            + ", ".join(str(pid) for pid in survivors)
        )


def command_coverage(arguments: argparse.Namespace) -> int:
    if os.environ.get(COVERAGE_ACTIVE_ENV):
        raise Refusal("coverage wrapper recursion is active in this process")
    if sys.version_info[:2] != (3, 14) or not hasattr(sys, "monitoring"):
        raise Refusal("coverage requires the repository Python 3.14 sys.monitoring runtime")
    scopes = tuple(arguments.scope)
    if not scopes or len(scopes) != len(set(scopes)):
        raise Refusal("coverage requires one or more unique --scope values")
    root = repository_root(Path(arguments.directory).resolve())
    root_fd = open_repository_directory(root)
    process_fd: int | None = None
    process_name = ""
    try:
        target = confine(root, arguments.output)
        universe = discover(root, root_fd=root_fd)
        plan = _runner_plan(root, scopes)
        run_id = uuid.uuid4().hex
        process_directory, process_fd = _create_process_directory(root, root_fd, run_id)
        process_name = process_directory.name
        environment = _coverage_environment(root, process_directory, run_id)
        runner_report = f"{OWNED_OUTPUT_DIRECTORY}/checks.json"
        argv = [sys.executable, CHECK_RUNNER.as_posix()]
        for scope in scopes:
            argv.extend(["--scope", scope])
        argv.extend(["--report", runner_report])
        try:
            _stdout, _stderr, _returncode = run_process(
                argv,
                cwd=root,
                timeout_seconds=RUNNER_TIMEOUT_SECONDS,
                output_limit=MAX_RUNNER_OUTPUT_BYTES,
                env=environment,
            )
        except BaseException as error:
            try:
                _terminate_coverage_processes(run_id)
            except Refusal as cleanup_error:
                if isinstance(error, Refusal):
                    raise Refusal(f"{error}; {cleanup_error}") from error
            raise
        unexpected_survivors = _coverage_survivor_pids(run_id)
        if unexpected_survivors:
            _terminate_coverage_processes(run_id)
            raise Refusal("checked runner returned with monitored processes still active")
        run_raw = read_bounded_regular(
            root / runner_report,
            limit=MAX_COVERAGE_BYTES,
            label=runner_report,
        )
        run = _json_document(run_raw, runner_report)
        outcome = run.get("outcome")
        expected_returncode = 0 if outcome == "green" else 1 if outcome == "red" else None
        if expected_returncode is None or _returncode != expected_returncode:
            raise Refusal(
                f"checked runner exit {_returncode} does not match {outcome} outcome"
            )
        documents = _read_process_documents(process_directory, process_fd, run_id)
        coverage = aggregate_coverage(plan, run, documents, universe)
        atomic_write(root, target, json.dumps(coverage, indent=2, sort_keys=True) + chr(10), root_fd=root_fd)
        return 0
    finally:
        if process_fd is not None:
            _remove_process_directory(process_fd, root_fd, process_name)
        os.close(root_fd)


def _coverage_file(
    root: Path,
    universe: Universe,
    coverage_path: str | None,
) -> dict[str, object]:
    if coverage_path is None:
        raise Refusal("coverage analyser requires --coverage")
    target = confine(root, coverage_path)
    raw = read_bounded_regular(target, limit=MAX_COVERAGE_BYTES, label=coverage_path)
    document = _json_document(raw, coverage_path)
    if document.get("schema") != COVERAGE_SCHEMA_ID:
        raise Refusal(f"{coverage_path} does not declare {COVERAGE_SCHEMA_ID}")
    tool = document.get("tool")
    if (
        not isinstance(tool, dict)
        or tool.get("id") != "sys.monitoring"
        or not isinstance(tool.get("python"), str)
        or re.fullmatch(r"3\.14\.\d+", tool["python"]) is None
    ):
        raise Refusal(f"{coverage_path} does not declare Python 3.14 sys.monitoring")
    plan = document.get("plan")
    if not isinstance(plan, dict) or plan.get("schema") != "wildcat.check-plan.v1":
        raise Refusal(f"{coverage_path} does not declare wildcat.check-plan.v1")
    map_digest = plan.get("map_digest")
    requested_scopes = plan.get("requested_scopes")
    if (
        not isinstance(map_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", map_digest) is None
        or not isinstance(requested_scopes, list)
        or not requested_scopes
        or not all(isinstance(scope, str) and scope for scope in requested_scopes)
        or len(requested_scopes) != len(set(requested_scopes))
    ):
        raise Refusal(f"{coverage_path} carries malformed checked-runner plan identity")
    tree = document.get("tree")
    if not isinstance(tree, dict):
        raise Refusal(f"{coverage_path} omits tree identity")
    if (
        tree.get("commit") != universe.commit
        or tree.get("git_tree") != universe.tree
        or tree.get("universe") != universe.identity
    ):
        return {
            **document,
            "status": {
                "state": "degraded",
                "detail": "coverage identity does not match the report universe",
            },
        }
    return document


def _function_targets(item: ParsedPython) -> Iterable[tuple[str, int]]:
    for node in ast.walk(item.tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.body:
            continue
        if node.name in item.retained_names:
            continue
        body = node.body
        if (
            isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]
        if body:
            yield node.name, body[0].lineno


def _branch_targets(item: ParsedPython) -> Iterable[tuple[int, int, str]]:
    for node in ast.walk(item.tree):
        if not isinstance(node, ast.If) or not node.body or not node.orelse:
            continue
        if isinstance(node.test, ast.Constant):
            continue
        yield node.lineno, node.body[0].lineno, "body"
        yield node.lineno, node.orelse[0].lineno, "else"


def analyse_coverage(
    root: Path,
    universe: Universe,
    coverage_path: str | None,
) -> tuple[AnalyserStatus, tuple[Finding, ...]]:
    document = _coverage_file(root, universe, coverage_path)
    status = document.get("status")
    checks = document.get("checks")
    processes = document.get("processes")
    if not isinstance(status, dict) or not isinstance(checks, list) or not isinstance(processes, list):
        raise Refusal("coverage record omits status, checks or processes")
    records: list[AnalyserRecord] = []
    check_claims: dict[str, tuple[int, int]] = {}
    for item in checks:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise Refusal("coverage check record is malformed")
        identifier = item["id"]
        process_count = item.get("processes")
        byte_count = item.get("bytes")
        if (
            not identifier
            or identifier in check_claims
            or not isinstance(process_count, int)
            or isinstance(process_count, bool)
            or process_count < 0
            or not isinstance(byte_count, int)
            or isinstance(byte_count, bool)
            or byte_count < 0
        ):
            raise Refusal("coverage check record has an invalid identity or count")
        check_claims[identifier] = (process_count, byte_count)
        state = item.get("state")
        mapped = "passed" if state == "passed" else "unavailable" if state == "unavailable" else "failed"
        records.append(
            AnalyserRecord(
                identifier,
                "check",
                mapped,
                f"runner state {state}; {process_count} process record(s)",
                byte_count,
            )
        )
    records.sort(key=lambda item: item.record_id)
    plan = document.get("plan")
    selected_checks = plan.get("selected_checks") if isinstance(plan, dict) else None
    if (
        not isinstance(selected_checks, list)
        or not all(isinstance(item, str) and item for item in selected_checks)
        or len(selected_checks) != len(set(selected_checks))
        or set(selected_checks) != set(check_claims)
    ):
        raise Refusal("coverage plan and check records do not name the same checks")

    observed_lines: set[tuple[str, int]] = set()
    observed_branches: set[tuple[str, int, int]] = set()
    actual_counts = {identifier: [0, 0] for identifier in check_claims}
    incomplete: set[str] = set()
    analysed_paths = set(universe.analysed)
    for process in processes:
        if not isinstance(process, dict):
            raise Refusal("coverage process aggregate is malformed")
        check_id = process.get("check")
        size = process.get("bytes")
        lines = process.get("lines")
        branches = process.get("branches")
        process_status = process.get("status")
        if (
            not isinstance(check_id, str)
            or check_id not in check_claims
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or not isinstance(lines, list)
            or not isinstance(branches, list)
            or not isinstance(process_status, dict)
        ):
            raise Refusal("coverage process aggregate omits a valid check, size, status or event list")
        normal_lines, normal_branches = _normalise_coverage_events(
            lines,
            branches,
            analysed_paths,
        )
        if normal_lines != lines or normal_branches != branches:
            raise Refusal("coverage process events are not canonical for the report universe")
        actual_counts[check_id][0] += 1
        actual_counts[check_id][1] += size
        if not _coverage_process_complete(process_status):
            incomplete.add(f"process for {check_id} was degraded")
        observed_lines.update(
            (line["path"], line["line"])
            for line in normal_lines
        )
        observed_branches.update(
            (branch["path"], branch["from_line"], branch["to_line"])
            for branch in normal_branches
        )
    for check_id, claimed in check_claims.items():
        actual = tuple(actual_counts[check_id])
        if actual != claimed:
            incomplete.add(
                f"check {check_id} claimed {claimed[0]} process record(s) and {claimed[1]} bytes; "
                f"the aggregate carries {actual[0]} and {actual[1]}"
            )
        if claimed[0] == 0:
            incomplete.add(f"check {check_id} carries no process record")

    if status.get("state") != "ran":
        return (
            AnalyserStatus(
                "coverage",
                "degraded",
                COVERAGE_ANALYSER_VERSION,
                str(status.get("detail") or "coverage did not complete"),
                tuple(records),
            ),
            (),
        )
    if incomplete:
        return (
            AnalyserStatus(
                "coverage",
                "degraded",
                COVERAGE_ANALYSER_VERSION,
                "; ".join(sorted(incomplete)),
                tuple(records),
            ),
            (),
        )
    if not records or any(record.state != "passed" for record in records):
        return (
            AnalyserStatus(
                "coverage",
                "degraded",
                COVERAGE_ANALYSER_VERSION,
                "coverage claimed completion but one or more check records were not passed",
                tuple(records),
            ),
            (),
        )

    snapshot = parse_python_snapshot(root, universe)
    if snapshot.degraded:
        return (
            AnalyserStatus(
                "coverage",
                "degraded",
                COVERAGE_ANALYSER_VERSION,
                "coverage completed but the bounded Python source inventory was incomplete",
                tuple(records),
            ),
            (),
        )
    findings: list[Finding] = []
    for item in snapshot.files:
        for name, line in _function_targets(item):
            if (item.path, line) not in observed_lines:
                findings.append(
                    _candidate(
                        item.path,
                        f"{name}@{line}",
                        f"no body line for {name} was observed in the completed named checks",
                        "low",
                        "coverage names only the selected checks and cannot prove other entry points absent",
                        analyser_id="coverage",
                    )
                )
        for source, target, direction in _branch_targets(item):
            if (item.path, source, target) not in observed_branches:
                findings.append(
                    _candidate(
                        item.path,
                        f"branch:{source}->{target}:{direction}",
                        f"the {direction} branch from line {source} to line {target} was not observed",
                        "low",
                        "sys.monitoring observed only the completed named checks",
                        analyser_id="coverage",
                    )
                )
    return (
        AnalyserStatus(
            "coverage",
            "ran",
            COVERAGE_ANALYSER_VERSION,
            f"consumed {len(processes)} process record(s) from {len(checks)} completed check(s)",
            tuple(records),
        ),
        tuple(findings),
    )


ANALYSERS["python"] = analyse_python


def collect(
    root: Path,
    universe: Universe,
    analyser_ids: tuple[str, ...] | None = None,
    coverage_path: str | None = None,
) -> tuple[tuple[AnalyserStatus, ...], tuple[Finding, ...]]:
    statuses: list[AnalyserStatus] = []
    findings: list[Finding] = []
    selected = tuple(sorted(ANALYSERS)) if analyser_ids is None else tuple(sorted(analyser_ids))
    for analyser_id in selected:
        if analyser_id == "coverage":
            status, produced = analyse_coverage(root, universe, coverage_path)
        else:
            analyser = ANALYSERS.get(analyser_id)
            if analyser is None:
                raise Refusal(f"unknown analyser {analyser_id}")
            status, produced = analyser(root, universe)
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
        record_ids: set[tuple[str, str]] = set()
        for record in item.records:
            identity = (record.kind, record.record_id)
            if not record.record_id or identity in record_ids:
                raise Refusal(f"analyser {item.analyser_id} has empty or repeated records")
            if record.kind not in ANALYSER_RECORD_KINDS:
                raise Refusal(f"analyser {item.analyser_id} has unknown record kind {record.kind}")
            if record.state not in ANALYSER_RECORD_STATES:
                raise Refusal(f"analyser {item.analyser_id} has unknown record state {record.state}")
            if not record.detail or record.bytes_count < 0:
                raise Refusal(f"analyser {item.analyser_id} has an invalid record")
            record_ids.add(identity)
        if item.records != tuple(sorted(item.records, key=lambda record: (record.kind, record.record_id))):
            raise Refusal(f"analyser {item.analyser_id} records are not sorted")
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


def build_report(
    root: Path,
    *,
    root_fd: int | None = None,
    analyser_ids: tuple[str, ...] = (),
    coverage_path: str | None = None,
) -> Report:
    universe = discover(root, root_fd=root_fd)
    statuses, findings = collect(root, universe, analyser_ids, coverage_path)
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
        for record in analyser["records"]:
            lines.append(
                f"    {record['kind']} {record['id']}  {record['state']}  "
                f"{record['bytes']} byte(s)  {record['detail']}"
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
    if not root.is_absolute():
        raise Refusal("the repository root is not absolute")
    target = root.joinpath(*parts)
    if target == root:
        raise Refusal("the repository root is not an output file")
    return target


def output_parts(root: Path, target: Path) -> tuple[str, ...]:
    if not root.is_absolute():
        raise Refusal("the repository root is not absolute")
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


def open_repository_directory(root: Path) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory_flag is None:
        raise Refusal("this platform cannot open output directories without following links")
    if not root.is_absolute():
        raise Refusal("the repository root is not absolute")
    flags = os.O_RDONLY | nofollow | directory_flag | getattr(os, "O_CLOEXEC", 0)
    try:
        return os.open(root, flags)
    except OSError as error:
        raise Refusal(f"the repository root cannot be opened safely: {error}") from error


def open_output_directory(root_fd: int, parts: tuple[str, ...]) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory_flag is None:
        raise Refusal("this platform cannot open output directories without following links")
    flags = os.O_RDONLY | nofollow | directory_flag | getattr(os, "O_CLOEXEC", 0)
    try:
        current_fd = os.dup(root_fd)
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


def atomic_write(
    root: Path,
    target: Path,
    payload: str,
    *,
    root_fd: int | None = None,
) -> None:
    encoded = payload.encode("utf-8")
    if len(encoded) > MAX_REPORT_BYTES:
        raise Refusal(f"report exceeds {MAX_REPORT_BYTES} bytes")
    owns_root_fd = root_fd is None
    if root_fd is None:
        root_fd = open_repository_directory(root)
    try:
        parts = output_parts(root, target)
        directory_fd = open_output_directory(root_fd, parts)
    finally:
        if owns_root_fd:
            os.close(root_fd)
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
    root_fd = open_repository_directory(root)
    target: Path | None = None
    try:
        analyser_ids = parse_analyser_ids(getattr(arguments, "analyser", None))
        coverage_path = getattr(arguments, "coverage", None)
        if arguments.output is not None:
            target = confine(root, arguments.output)
        report = build_report(
            root,
            root_fd=root_fd,
            analyser_ids=analyser_ids,
            coverage_path=coverage_path,
        )
        rendered = render_json(report) if arguments.json else render_text(report)
        if arguments.output is None:
            sys.stdout.write(rendered)
            return 0
        assert target is not None
        atomic_write(root, target, rendered, root_fd=root_fd)
        return 0
    finally:
        if root_fd is not None:
            os.close(root_fd)


def parse_analyser_ids(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    identifiers = tuple(value.split(","))
    if not identifiers or any(not item for item in identifiers):
        raise Refusal("--analyser must be a comma-separated list of identities")
    if len(identifiers) != len(set(identifiers)):
        raise Refusal("--analyser repeats an identity")
    supported = {*ANALYSERS, "coverage"}
    unknown = sorted(set(identifiers) - supported)
    if unknown:
        raise Refusal("unknown analyser(s): " + ", ".join(unknown))
    return identifiers


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
    coverage = subparsers.add_parser(
        "coverage",
        help="run a Python-only checked scope under sys.monitoring",
    )
    coverage.add_argument(
        "--scope",
        action="append",
        default=[],
        help="a checked-runner scope; repeatable",
    )
    coverage.add_argument(
        "--output",
        required=True,
        help="write the coverage record inside the owned .dead-code sink",
    )
    coverage.set_defaults(handler=command_coverage)
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
    report.add_argument(
        "--analyser",
        help="comma-separated analyser identities to run",
    )
    report.add_argument(
        "--coverage",
        help="coverage record below the owned .dead-code sink",
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
