#!/usr/bin/env python3
"""Select repository checks from one declared graph and run them under one budget.

The planner unions the requested scopes with every actual changed path, closes
that set over the declared dependency edges, and refuses before execution when
ownership is unknown, a command is stale, a key is duplicated, a path is unsafe,
an edge forms a cycle or the base cannot be resolved.  The executor freezes an
immutable snapshot of the relevant working tree, starts fixed argv without a
shell, and holds one global slot budget that nested suite runners draw their
allocation from rather than deriving a second budget of their own.

``wildcat.check-plan.v1`` and ``wildcat.check-run.v1`` are the versioned records.
Neither one caches a pass verdict: timing history may balance work, and nothing
else.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

MAP_SCHEMA = "wildcat.check-map.v1"
PLAN_SCHEMA = "wildcat.check-plan.v1"
RUN_SCHEMA = "wildcat.check-run.v1"
DEFAULT_MAP_PATH = "tests/check-map-v1.json"
RUNNER_PARENT = "tmp/check-runner"
SENTINEL_NAME = ".check-runner-owned"
MAX_MAP_BYTES = 1_048_576
MAX_GIT_OUTPUT_BYTES = 8_388_608
MAX_CAPTURE_HEAD_BYTES = 65_536
MAX_CAPTURE_TAIL_BYTES = 65_536
MAX_UNTRACKED_BYTES = 33_554_432
MAX_WORKTREE_ENTRIES = 100_000
DEFAULT_TIMEOUT_SECONDS = 1_800
SAFETY_CAP = 32
DRAIN_SECONDS = 5.0
MAX_ATTEMPTS = 2
CHECK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SCOPE_ID_RE = CHECK_ID_RE
FAILURE_CLASSES = (
    "test-failure",
    "command-failure",
    "scheduler-error",
    "invalid-plan",
    "snapshot-error",
    "superseded",
    "unstable-source",
)
GIT_ENV_PREFIXES = ("GIT_",)
GIT_ENV_KEEP = {"GIT_EXEC_PATH"}


class PlanError(Exception):
    """A refusal raised before any check is started."""

    def __init__(self, code: str, message: str, detail: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


class SnapshotError(Exception):
    """The attempt snapshot could not be created or stayed unstable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Check:
    id: str
    title: str
    argv: tuple[str, ...]
    cwd: str
    kind: str
    script: str | None
    jobs_flag: str | None
    requires_executable: str | None
    group: str | None
    order: int
    timeout_seconds: int


@dataclass(frozen=True)
class Scope:
    id: str
    title: str
    checks: tuple[str, ...]


@dataclass(frozen=True)
class CheckMap:
    checks: Mapping[str, Check]
    scopes: Mapping[str, Scope]
    groups: Mapping[str, tuple[str, ...]]
    dependencies: Mapping[str, tuple[str, ...]]
    owners: tuple[tuple[str, str], ...]
    digest: str


@dataclass
class Selection:
    scopes: dict[str, list[str]] = field(default_factory=dict)
    changed_paths: list[str] = field(default_factory=list)
    unowned_paths: list[str] = field(default_factory=list)
    requested: list[str] = field(default_factory=list)
    base: str | None = None
    full: bool = False

    def add_reason(self, scope: str, reason: str) -> None:
        self.scopes.setdefault(scope, [])
        if reason not in self.scopes[scope]:
            self.scopes[scope].append(reason)


@dataclass
class CaptureBuffer:
    """Bounded head and tail retention with an exact byte count."""

    head: bytearray = field(default_factory=bytearray)
    tail: bytearray = field(default_factory=bytearray)
    total: int = 0

    def feed(self, chunk: bytes) -> None:
        self.total += len(chunk)
        room = MAX_CAPTURE_HEAD_BYTES - len(self.head)
        if room > 0:
            self.head.extend(chunk[:room])
            chunk = chunk[room:]
        if not chunk:
            return
        self.tail.extend(chunk)
        if len(self.tail) > MAX_CAPTURE_TAIL_BYTES:
            del self.tail[: len(self.tail) - MAX_CAPTURE_TAIL_BYTES]

    def record(self) -> dict[str, Any]:
        return {
            "bytes": self.total,
            "truncated": self.total > len(self.head) + len(self.tail),
            "head": self.head.decode("utf-8", "replace"),
            "tail": self.tail.decode("utf-8", "replace") if self.tail else "",
        }


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise PlanError("duplicate-key", f"duplicate key in check map: {key}")
        seen[key] = value
    return seen


def _safe_relpath(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise PlanError("unsafe-path", f"{field_name} must be a non-empty string")
    if value.startswith("/") or ":" in value:
        raise PlanError("unsafe-path", f"{field_name} must be repository-relative: {value}")
    parts = [p for p in value.split("/") if p]
    if any(p in {"..", "."} for p in parts):
        raise PlanError("unsafe-path", f"{field_name} must not traverse: {value}")
    if any(p == ".git" for p in parts):
        raise PlanError("unsafe-path", f"{field_name} must not enter a Git namespace: {value}")
    return "/".join(parts)


def _optional_string(body: Mapping[str, Any], key: str, *, cid: str) -> str | None:
    value = body.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise PlanError("map-invalid", f"check {cid} {key} must be a non-empty string")
    return value


def _bounded_int(body: Mapping[str, Any], key: str, default: int, *, cid: str) -> int:
    """A malformed number must refuse by name rather than raise out of main()."""
    value = body.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise PlanError("map-invalid", f"check {cid} {key} must be an integer")
    return value


def load_map(root: Path, map_path: str = DEFAULT_MAP_PATH) -> CheckMap:
    """Read, validate and digest the declared check map."""
    target = root / map_path
    try:
        raw = target.read_bytes()
    except OSError as exc:
        raise PlanError("map-unreadable", f"cannot read {map_path}: {exc}") from exc
    if len(raw) > MAX_MAP_BYTES:
        raise PlanError("map-oversized", f"{map_path} exceeds {MAX_MAP_BYTES} bytes")
    digest = hashlib.sha256(raw).hexdigest()
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except UnicodeDecodeError as exc:
        raise PlanError("map-invalid", f"{map_path} is not UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise PlanError("map-invalid", f"{map_path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != MAP_SCHEMA:
        raise PlanError("map-invalid", f"{map_path} is not {MAP_SCHEMA}")

    groups_raw = data.get("groups") or {}
    if not isinstance(groups_raw, dict):
        raise PlanError("map-invalid", "groups must be an object")

    checks: dict[str, Check] = {}
    explicit_order: dict[str, int] = {}
    raw_checks = data.get("checks")
    if not isinstance(raw_checks, dict) or not raw_checks:
        raise PlanError("map-invalid", "checks must be a non-empty object")
    for cid, body in raw_checks.items():
        if not CHECK_ID_RE.match(cid):
            raise PlanError("map-invalid", f"check id is not well formed: {cid}")
        if not isinstance(body, dict):
            raise PlanError("map-invalid", f"check {cid} must be an object")
        argv = body.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) and a for a in argv):
            raise PlanError("map-invalid", f"check {cid} needs a non-empty string argv")
        cwd = body.get("cwd", ".")
        if cwd != ".":
            cwd = _safe_relpath(cwd, field_name=f"check {cid} cwd")
        script = body.get("script")
        if script is not None:
            script = _safe_relpath(script, field_name=f"check {cid} script")
        group = body.get("group")
        if group is not None and group not in groups_raw:
            raise PlanError("map-invalid", f"check {cid} names unknown group {group}")
        timeout_seconds = _bounded_int(
            body, "timeout_seconds", DEFAULT_TIMEOUT_SECONDS, cid=cid
        )
        if timeout_seconds < 1:
            raise PlanError("map-invalid", f"check {cid} timeout_seconds must be positive")
        if "order" in body:
            explicit_order[cid] = _bounded_int(body, "order", 0, cid=cid)
        checks[cid] = Check(
            id=cid,
            title=str(body.get("title", cid)),
            argv=tuple(argv),
            cwd=cwd,
            kind=str(body.get("kind", "suite")),
            script=script,
            jobs_flag=_optional_string(body, "jobs_flag", cid=cid),
            requires_executable=_optional_string(body, "requires_executable", cid=cid),
            group=group,
            order=_bounded_int(body, "order", 0, cid=cid),
            timeout_seconds=timeout_seconds,
        )

    groups: dict[str, tuple[str, ...]] = {}
    for gid, body in groups_raw.items():
        if not isinstance(body, dict) or not isinstance(body.get("ordered"), list):
            raise PlanError("map-invalid", f"group {gid} needs an ordered list")
        ordered = body["ordered"]
        for cid in ordered:
            if cid not in checks:
                raise PlanError("map-invalid", f"group {gid} names unknown check {cid}")
            if checks[cid].group != gid:
                raise PlanError("map-invalid", f"check {cid} does not declare group {gid}")
        if len(set(ordered)) != len(ordered):
            raise PlanError("map-invalid", f"group {gid} names a check twice in its ordered list")
        # A check may not join a group by the back reference alone: a member the
        # ordered list omits has no declared position, and would otherwise be
        # sequenced by a default the map never states.
        omitted = sorted(cid for cid, c in checks.items() if c.group == gid and cid not in ordered)
        if omitted:
            raise PlanError(
                "map-invalid", f"group {gid} omits declared member(s) from its ordered list: {omitted}"
            )
        # The ordered list is the declaration, so it is what execution follows.
        # ``order`` is an optional restatement of it and must not contradict it:
        # a member with no ``order`` would otherwise fall back to a default that
        # sequences the group by check id, silently inverting the declaration.
        restated = [cid for cid in ordered if cid in explicit_order]
        if sorted(restated, key=lambda c: (explicit_order[c], c)) != restated:
            raise PlanError(
                "ordered-conflict",
                f"group {gid} order fields contradict its declared sequence: {ordered}",
            )
        for position, cid in enumerate(ordered):
            checks[cid] = replace(checks[cid], order=position)
        groups[gid] = tuple(ordered)

    scopes: dict[str, Scope] = {}
    raw_scopes = data.get("scopes")
    if not isinstance(raw_scopes, dict) or not raw_scopes:
        raise PlanError("map-invalid", "scopes must be a non-empty object")
    for sid, body in raw_scopes.items():
        if not SCOPE_ID_RE.match(sid):
            raise PlanError("map-invalid", f"scope id is not well formed: {sid}")
        if not isinstance(body, dict) or not isinstance(body.get("checks"), list):
            raise PlanError("map-invalid", f"scope {sid} needs a checks list")
        for cid in body["checks"]:
            if cid not in checks:
                raise PlanError("map-invalid", f"scope {sid} names unknown check {cid}")
        scopes[sid] = Scope(sid, str(body.get("title", sid)), tuple(body["checks"]))

    deps_raw = data.get("dependencies") or {}
    if not isinstance(deps_raw, dict):
        raise PlanError("map-invalid", "dependencies must be an object")
    dependencies: dict[str, tuple[str, ...]] = {}
    for sid, consumers in deps_raw.items():
        if sid not in scopes:
            raise PlanError("map-invalid", f"dependency edge from unknown scope {sid}")
        if not isinstance(consumers, list):
            raise PlanError("map-invalid", f"dependencies for {sid} must be a list")
        for consumer in consumers:
            if consumer not in scopes:
                raise PlanError("map-invalid", f"dependency edge to unknown scope {consumer}")
        dependencies[sid] = tuple(consumers)

    owners_raw = data.get("owners")
    if not isinstance(owners_raw, list) or not owners_raw:
        raise PlanError("map-invalid", "owners must be a non-empty list")
    seen_paths: set[str] = set()
    owners: list[tuple[str, str]] = []
    for entry in owners_raw:
        if not isinstance(entry, dict):
            raise PlanError("map-invalid", "each owner entry must be an object")
        path = _safe_relpath(str(entry.get("path", "")), field_name="owner path")
        scope = entry.get("scope")
        if scope not in scopes:
            raise PlanError("map-invalid", f"owner {path} names unknown scope {scope}")
        if path in seen_paths:
            raise PlanError("ambiguous-ownership", f"owner path declared twice: {path}")
        seen_paths.add(path)
        owners.append((path, str(scope)))
    owners.sort(key=lambda pair: (-len(pair[0]), pair[0]))

    _refuse_cycles(dependencies)
    return CheckMap(checks, scopes, groups, dependencies, tuple(owners), digest)


def _refuse_cycles(dependencies: Mapping[str, Sequence[str]]) -> None:
    colour: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        state = colour.get(node, 0)
        if state == 1:
            cycle = stack[stack.index(node):] + [node]
            raise PlanError("dependency-cycle", "dependency cycle: " + " -> ".join(cycle))
        if state == 2:
            return
        colour[node] = 1
        stack.append(node)
        for nxt in dependencies.get(node, ()):
            visit(nxt)
        stack.pop()
        colour[node] = 2

    for node in dependencies:
        visit(node)


def refuse_stale_commands(root: Path, check_map: CheckMap) -> None:
    """Every declared script path must still exist in the checkout."""
    stale = []
    for check in check_map.checks.values():
        if check.script is None:
            continue
        if not (root / check.script).exists():
            stale.append({"check": check.id, "script": check.script})
        if check.cwd != "." and not (root / check.cwd).is_dir():
            stale.append({"check": check.id, "cwd": check.cwd})
    if stale:
        raise PlanError("stale-command", "the check map names paths that no longer exist", stale)


def owner_of(check_map: CheckMap, path: str) -> str | None:
    for prefix, scope in check_map.owners:
        if path == prefix or path.startswith(prefix + "/"):
            return scope
    return None


def is_runner_owned(path: str) -> bool:
    """True for paths under this runner's own snapshot parent.

    The runner must never observe its own snapshot as a changed path or as
    source movement, whether or not the checkout happens to ignore ``tmp/``.
    """
    return path == RUNNER_PARENT or path.startswith(RUNNER_PARENT + "/")


def _git_env() -> dict[str, str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if not (k.startswith(GIT_ENV_PREFIXES) and k not in GIT_ENV_KEEP)
    }
    env["GIT_PAGER"] = "cat"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.pop("GIT_EDITOR", None)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def git(root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(root),
        env=_git_env(),
        capture_output=True,
        shell=False,
    )
    if check and proc.returncode != 0:
        raise PlanError(
            "git-failed",
            f"git {' '.join(args)} failed: {proc.stderr.decode('utf-8', 'replace').strip()}",
        )
    if len(proc.stdout) > MAX_GIT_OUTPUT_BYTES:
        raise PlanError("git-oversized", f"git {' '.join(args)} produced too much output")
    return proc.stdout.decode("utf-8", "replace")


def resolve_base(root: Path, base: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", base + "^{commit}"],
        cwd=str(root),
        env=_git_env(),
        capture_output=True,
        shell=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise PlanError("invalid-base", f"cannot resolve base: {base}")
    return proc.stdout.decode().strip()


def changed_paths(root: Path, base: str | None) -> list[str]:
    """Committed, staged, unstaged and relevant untracked paths, rename-aware."""
    paths: set[str] = set()
    if base is not None:
        resolved = resolve_base(root, base)
        for line in git(root, "diff", "--name-only", "--no-renames", "-z", f"{resolved}..HEAD").split("\0"):
            if line:
                paths.add(line)
    for args in (
        ("diff", "--name-only", "--no-renames", "-z", "--cached"),
        ("diff", "--name-only", "--no-renames", "-z"),
    ):
        for line in git(root, *args).split("\0"):
            if line:
                paths.add(line)
    for line in git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        if line:
            paths.add(line)
    for line in git(root, "diff", "--name-only", "--no-renames", "-z", "--diff-filter=D").split("\0"):
        if line:
            paths.add(line)
    paths.update(_filesystem_special_paths(root))
    return sorted(p for p in paths if not is_runner_owned(p))


def build_selection(
    root: Path,
    check_map: CheckMap,
    requested: Sequence[str],
    base: str | None,
    full: bool,
    observed: Sequence[str] | None = None,
) -> Selection:
    """Union the requested scopes with the actual diff, then close over consumers.

    ``observed`` exists so a caller that has already captured the changed paths,
    or a test exercising one named change class, drives the same closure the
    command line does.
    """
    selection = Selection(requested=list(requested), base=base, full=full)
    for scope in requested:
        if scope not in check_map.scopes:
            raise PlanError("unknown-scope", f"unknown scope: {scope}")
        selection.add_reason(scope, "requested")
    if full:
        for scope in check_map.scopes:
            selection.add_reason(scope, "full")

    if observed is None:
        observed = changed_paths(root, base)
    selection.changed_paths = list(observed)
    for path in observed:
        scope = owner_of(check_map, path)
        if scope is None:
            selection.unowned_paths.append(path)
            continue
        selection.add_reason(scope, f"changed path {path}")
    if selection.unowned_paths:
        raise PlanError(
            "unknown-ownership",
            "changed paths have no declared owner",
            selection.unowned_paths,
        )

    frontier = list(selection.scopes)
    while frontier:
        scope = frontier.pop()
        for consumer in check_map.dependencies.get(scope, ()):
            if consumer not in selection.scopes:
                frontier.append(consumer)
            selection.add_reason(consumer, f"consumer of {scope}")
    return selection


def selected_checks(check_map: CheckMap, selection: Selection) -> list[Check]:
    chosen: dict[str, Check] = {}
    for scope in selection.scopes:
        for cid in check_map.scopes[scope].checks:
            chosen[cid] = check_map.checks[cid]
    return sorted(chosen.values(), key=lambda c: c.id)


def _positive_capacity(value: Any) -> int | None:
    """Return one positive integer capacity signal, or no signal."""
    if isinstance(value, bool):
        return None
    try:
        integer = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return integer if integer > 0 else None


def _read_small_text(path: str | Path, maximum: int = 256) -> str:
    """Read one bounded ASCII controller value."""
    with Path(path).open("rb") as handle:
        body = handle.read(maximum + 1)
    if len(body) > maximum:
        raise OSError(f"controller value exceeds {maximum} bytes: {path}")
    return body.decode("ascii").strip()


def _quota_capacity(quota: Any, period: Any) -> int | None:
    try:
        quota_value = int(quota)
        period_value = int(period)
    except (TypeError, ValueError):
        return None
    if quota_value <= 0 or period_value <= 0:
        return None
    return max(1, quota_value // period_value)


def _canonical_cgroup_member(raw: Any) -> PurePosixPath | None:
    try:
        member = PurePosixPath(raw)
    except (TypeError, ValueError):
        return None
    if (
        not isinstance(raw, str)
        or not raw.startswith("/")
        or str(member) != raw
        or any(part in {"", ".", ".."} for part in member.parts[1:])
    ):
        return None
    return member


def _decode_mountinfo_path(raw: str) -> PurePosixPath | None:
    value = raw
    for encoded, decoded in (
        (r"\040", " "),
        (r"\011", "\t"),
        (r"\012", "\n"),
        (r"\134", "\\"),
    ):
        value = value.replace(encoded, decoded)
    if "\\" in value or "\x00" in value:
        return None
    return _canonical_cgroup_member(value)


def _cgroup_v2_member() -> PurePosixPath | None:
    try:
        membership = _read_small_text("/proc/self/cgroup", maximum=4_096)
    except (OSError, UnicodeError, ValueError):
        return None
    matches = []
    for line in membership.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0" and parts[1] == "":
            matches.append(parts[2])
    if len(matches) != 1:
        return None
    return _canonical_cgroup_member(matches[0])


def _cgroup_v2_mounts() -> list[tuple[PurePosixPath, PurePosixPath]]:
    try:
        mountinfo = _read_small_text("/proc/self/mountinfo", maximum=131_072)
    except (OSError, UnicodeError, ValueError):
        return []
    mounts: list[tuple[PurePosixPath, PurePosixPath]] = []
    for line in mountinfo.splitlines():
        fields = line.split()
        try:
            separator = fields.index("-")
        except ValueError:
            continue
        if separator < 6 or len(fields) <= separator + 1:
            continue
        if fields[separator + 1] != "cgroup2":
            continue
        controller_root = _decode_mountinfo_path(fields[3])
        mount_point = _decode_mountinfo_path(fields[4])
        if controller_root is None or mount_point is None:
            continue
        pair = (controller_root, mount_point)
        if pair not in mounts:
            mounts.append(pair)
    return mounts


def _cgroup_v2_cpu_max_paths() -> list[str]:
    member = _cgroup_v2_member()
    fallback = (PurePosixPath("/"), PurePosixPath("/sys/fs/cgroup"))
    mounts = _cgroup_v2_mounts() if member is not None else []
    if fallback not in mounts:
        mounts.append(fallback)
    if member is None:
        member = PurePosixPath("/")

    result: list[str] = []
    for controller_root, mount_point in mounts:
        try:
            relative = member.relative_to(controller_root)
        except ValueError:
            continue
        base = mount_point.joinpath(*relative.parts)
        while True:
            path = str(base / "cpu.max")
            if path not in result:
                result.append(path)
            if base == mount_point or mount_point not in base.parents:
                break
            base = base.parent
    return result


def _cgroup_v2_capacity() -> int | None:
    capacities = []
    for path in _cgroup_v2_cpu_max_paths():
        try:
            values = _read_small_text(path).split()
        except (OSError, UnicodeError, ValueError):
            continue
        if len(values) != 2 or values[0] == "max":
            continue
        value = _quota_capacity(values[0], values[1])
        if value is not None:
            capacities.append(value)
    return min(capacities) if capacities else None


def _cgroup_v1_cpu_member() -> PurePosixPath | None:
    try:
        membership = _read_small_text("/proc/self/cgroup", maximum=4_096)
    except (OSError, UnicodeError, ValueError):
        return None
    matches = []
    for line in membership.splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3 or not parts[0]:
            continue
        if "cpu" in (parts[1].split(",") if parts[1] else []):
            matches.append(parts[2])
    if len(matches) != 1:
        return None
    return _canonical_cgroup_member(matches[0])


def _cgroup_v1_cpu_mounts() -> list[tuple[PurePosixPath, PurePosixPath]]:
    try:
        mountinfo = _read_small_text("/proc/self/mountinfo", maximum=131_072)
    except (OSError, UnicodeError, ValueError):
        return []
    mounts: list[tuple[PurePosixPath, PurePosixPath]] = []
    for line in mountinfo.splitlines():
        fields = line.split()
        try:
            separator = fields.index("-")
        except ValueError:
            continue
        if separator < 6 or len(fields) <= separator + 3:
            continue
        if fields[separator + 1] != "cgroup":
            continue
        if "cpu" not in set(fields[separator + 3].split(",")):
            continue
        controller_root = _decode_mountinfo_path(fields[3])
        mount_point = _decode_mountinfo_path(fields[4])
        if controller_root is None or mount_point is None:
            continue
        pair = (controller_root, mount_point)
        if pair not in mounts:
            mounts.append(pair)
    return mounts


def _cgroup_v1_cpu_quota_paths() -> list[tuple[str, str]]:
    member = _cgroup_v1_cpu_member()
    mounts = _cgroup_v1_cpu_mounts() if member is not None else []
    if member is not None:
        mounts.extend(
            (PurePosixPath("/"), PurePosixPath(root))
            for root in (
                "/sys/fs/cgroup/cpu",
                "/sys/fs/cgroup/cpu,cpuacct",
                "/sys/fs/cgroup/cpuacct,cpu",
            )
        )
    else:
        mounts.append((PurePosixPath("/"), PurePosixPath("/sys/fs/cgroup/cpu")))
        member = PurePosixPath("/")

    result: list[tuple[str, str]] = []
    for controller_root, mount_point in mounts:
        try:
            relative = member.relative_to(controller_root)
        except ValueError:
            continue
        base = mount_point.joinpath(*relative.parts)
        while True:
            pair = (str(base / "cpu.cfs_quota_us"), str(base / "cpu.cfs_period_us"))
            if pair not in result:
                result.append(pair)
            if base == mount_point or mount_point not in base.parents:
                break
            base = base.parent
    return result


def _cgroup_v1_capacity() -> int | None:
    capacities = []
    for quota_path, period_path in _cgroup_v1_cpu_quota_paths():
        try:
            quota = _read_small_text(quota_path)
            period = _read_small_text(period_path)
        except (OSError, UnicodeError, ValueError):
            continue
        value = _quota_capacity(quota, period)
        if value is not None:
            capacities.append(value)
    return min(capacities) if capacities else None


def _capacity_signals() -> dict[str, int]:
    signals: dict[str, int] = {}
    process_count = getattr(os, "process_cpu_count", None)
    if process_count is not None:
        try:
            value = _positive_capacity(process_count())
        except OSError:
            value = None
        if value is not None:
            signals["process_cpu_count"] = value
    affinity = getattr(os, "sched_getaffinity", None)
    if affinity is not None:
        try:
            value = _positive_capacity(len(affinity(0)))
        except OSError:
            value = None
        if value is not None:
            signals["affinity"] = value
    value = _cgroup_v2_capacity()
    if value is not None:
        signals["cgroup_v2"] = value
    value = _cgroup_v1_capacity()
    if value is not None:
        signals["cgroup_v1"] = value
    try:
        value = _positive_capacity(os.cpu_count())
    except OSError:
        value = None
    if value is not None:
        signals["os_cpu_count"] = value
    return signals


def capacity_plan(
    requested: int | None,
    item_count: int,
    signals: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose a conservative automatic budget or one bounded explicit override."""
    if requested is not None and (isinstance(requested, bool) or not isinstance(requested, int)):
        raise ValueError("explicit jobs must be an integer")
    if requested is not None and requested < 1:
        raise ValueError("explicit jobs must be positive")
    if isinstance(item_count, bool) or not isinstance(item_count, int) or item_count < 0:
        raise ValueError("item count must be a non-negative integer")
    observed = dict(_capacity_signals() if signals is None else signals)
    observed = {
        key: value
        for key, raw in sorted(observed.items())
        if (value := _positive_capacity(raw)) is not None
    }
    usable = min(observed.values()) if observed else 1
    if requested is None:
        reserve = max(1, (usable + 2) // 3) if usable > 1 else 0
        budget = min(SAFETY_CAP, max(1, usable - reserve))
        source = "automatic"
    else:
        reserve = 0
        budget = min(requested, SAFETY_CAP)
        source = "explicit"
    runnable_cap = max(1, item_count)
    return {
        "signals": observed,
        "usable": usable,
        "reserve": reserve,
        "safety_cap": SAFETY_CAP,
        "runnable_cap": runnable_cap,
        "effective_budget": min(budget, runnable_cap),
        "source": source,
    }


def read_capacity() -> dict[str, Any]:
    """Return the automatic host policy before a concrete plan is selected."""
    return capacity_plan(None, item_count=SAFETY_CAP)


def _runnable_slot_cap(checks: Sequence[Check]) -> int:
    """Bound outer work; nested runners cap their own rediscovered manifests."""
    groups = {check.group for check in checks if check.group is not None}
    singles = [check for check in checks if check.group is None]
    units = len(groups) + len(singles)
    if any(check.jobs_flag is not None for check in checks):
        return SAFETY_CAP
    return units


def _ignored_paths(root: Path) -> tuple[str, ...]:
    status = git(
        root,
        "status",
        "--porcelain=v1",
        "-z",
        "--ignored=matching",
        "--untracked-files=normal",
    )
    return tuple(
        record[3:].rstrip("/")
        for record in status.split("\0")
        if record.startswith("!! ") and record[3:].rstrip("/")
    )


def _filesystem_special_paths(root: Path) -> list[str]:
    """Find non-ignored objects Git omits, without following links or .git."""
    ignored = _ignored_paths(root)

    def excluded(rel: str) -> bool:
        return any(rel == item or rel.startswith(item + "/") for item in ignored)

    special = []
    stack: list[tuple[Path, str]] = [(root, "")]
    entries = 0
    while stack:
        directory, prefix = stack.pop()
        try:
            children = sorted(os.scandir(directory), key=lambda entry: entry.name, reverse=True)
        except OSError as exc:
            raise PlanError(
                "snapshot-error", f"cannot inspect working tree directory {prefix or '.'}: {exc}"
            ) from exc
        for entry in children:
            rel = f"{prefix}/{entry.name}" if prefix else entry.name
            if rel == ".git" or rel.startswith(".git/") or is_runner_owned(rel) or excluded(rel):
                continue
            entries += 1
            if entries > MAX_WORKTREE_ENTRIES:
                raise PlanError(
                    "snapshot-error",
                    f"working tree exceeds the {MAX_WORKTREE_ENTRIES}-entry inspection bound",
                )
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise PlanError("snapshot-error", f"cannot inspect working tree path {rel}: {exc}") from exc
            if stat.S_ISDIR(info.st_mode):
                stack.append((Path(entry.path), rel))
            elif not stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode):
                special.append(rel)
    if not special:
        return []
    encoded = b"\0".join(
        rel.encode("utf-8", "surrogateescape") for rel in special
    ) + b"\0"
    if len(encoded) > MAX_GIT_OUTPUT_BYTES:
        raise PlanError("git-oversized", "special-file ignore query is too large")
    proc = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin", "-z"],
        cwd=str(root),
        env=_git_env(),
        input=encoded,
        capture_output=True,
        shell=False,
    )
    if proc.returncode not in {0, 1}:
        raise PlanError(
            "git-failed",
            "git check-ignore failed: " + proc.stderr.decode("utf-8", "replace").strip(),
        )
    if len(proc.stdout) > MAX_GIT_OUTPUT_BYTES:
        raise PlanError("git-oversized", "git check-ignore produced too much output")
    ignored_special = {
        rel
        for rel in proc.stdout.decode("utf-8", "surrogateescape").split("\0")
        if rel
    }
    return sorted(set(special) - ignored_special)


def _untracked_paths(root: Path) -> list[str]:
    paths = {
        rel
        for rel in git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
        if rel and not is_runner_owned(rel)
    }
    paths.update(_filesystem_special_paths(root))
    return sorted(paths)


def _snapshot_relpath(rel: str) -> str:
    try:
        return _safe_relpath(rel, field_name="untracked path")
    except PlanError as exc:
        raise SnapshotError("snapshot-error", exc.message) from exc


def _confine_untracked_parent(root: Path, rel: str) -> None:
    base = root.resolve()
    try:
        parent = (root / rel).parent.resolve(strict=True)
    except OSError as exc:
        raise SnapshotError(
            "snapshot-error", f"cannot resolve untracked path parent {rel}: {exc}"
        ) from exc
    if parent != base and base not in parent.parents:
        raise SnapshotError("snapshot-error", f"untracked path leaves the repository: {rel}")


def _safe_symlink_target(root: Path, rel: str, raw_target: str) -> None:
    """Accept only a relative link whose resolved target stays outside Git state."""
    if not raw_target or os.path.isabs(raw_target):
        raise SnapshotError(
            "snapshot-error", f"untracked symlink has an unsafe target: {rel}"
        )
    base = root.resolve()
    try:
        resolved = ((root / rel).parent / raw_target).resolve(strict=False)
        relative = resolved.relative_to(base)
    except (OSError, ValueError) as exc:
        raise SnapshotError(
            "snapshot-error", f"untracked symlink leaves the repository: {rel}"
        ) from exc
    posix = relative.as_posix()
    if ".git" in relative.parts or is_runner_owned(posix):
        raise SnapshotError(
            "snapshot-error", f"untracked symlink enters runner or Git state: {rel}"
        )


def _read_untracked_regular(src: Path, expected: os.stat_result, maximum: int) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(src, flags)
    try:
        opened = os.fstat(fd)
        identity = (expected.st_dev, expected.st_ino, expected.st_size, expected.st_mtime_ns)
        opened_identity = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
        if identity != opened_identity or not stat.S_ISREG(opened.st_mode):
            raise SnapshotError("snapshot-error", f"untracked file moved while opening: {src}")
        body = bytearray()
        while True:
            chunk = os.read(fd, min(65_536, maximum - len(body) + 1))
            if not chunk:
                break
            body.extend(chunk)
            if len(body) > maximum:
                raise SnapshotError(
                    "snapshot-error", "untracked working files exceed the snapshot bound"
                )
        closed = os.fstat(fd)
        closed_identity = (closed.st_dev, closed.st_ino, closed.st_size, closed.st_mtime_ns)
        if opened_identity != closed_identity:
            raise SnapshotError("snapshot-error", f"untracked file moved while reading: {src}")
        return bytes(body)
    finally:
        os.close(fd)


def _untracked_entry(root: Path, rel: str, remaining: int) -> tuple[str, bytes, int]:
    safe = _snapshot_relpath(rel)
    _confine_untracked_parent(root, safe)
    src = root / safe
    try:
        info = src.lstat()
    except OSError as exc:
        raise SnapshotError("snapshot-error", f"cannot inspect untracked path {safe}: {exc}") from exc
    if stat.S_ISLNK(info.st_mode):
        try:
            raw_target = os.readlink(src)
        except OSError as exc:
            raise SnapshotError(
                "snapshot-error", f"cannot read untracked symlink {safe}: {exc}"
            ) from exc
        _safe_symlink_target(root, safe, raw_target)
        body = os.fsencode(raw_target)
        if len(body) > remaining:
            raise SnapshotError(
                "snapshot-error", "untracked working files exceed the snapshot bound"
            )
        return "symlink", body, info.st_mode
    if not stat.S_ISREG(info.st_mode):
        raise SnapshotError("snapshot-error", f"unsupported untracked special file: {safe}")
    return "regular", _read_untracked_regular(src, info, remaining), info.st_mode


def _digest_field(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def source_identity(root: Path) -> str:
    """A digest over HEAD, the full working diff and every relevant untracked entry."""
    parts = [git(root, "rev-parse", "HEAD").strip()]
    parts.append(hashlib.sha256(git(root, "diff", "HEAD").encode()).hexdigest())
    parts.append(hashlib.sha256(git(root, "diff", "--cached").encode()).hexdigest())
    digest = hashlib.sha256()
    consumed = 0
    try:
        for rel in _untracked_paths(root):
            kind, body, mode = _untracked_entry(root, rel, MAX_UNTRACKED_BYTES - consumed)
            consumed += len(body)
            _digest_field(digest, rel.encode("utf-8", "surrogateescape"))
            _digest_field(digest, kind.encode("ascii"))
            if kind == "regular":
                replayed_mode = stat.S_IMODE(mode) & 0o777
                _digest_field(digest, replayed_mode.to_bytes(4, "big"))
            _digest_field(digest, body)
    except SnapshotError as exc:
        raise PlanError(exc.code, exc.message) from exc
    parts.append(digest.hexdigest())
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()


def make_snapshot(root: Path, nonce: str) -> Path:
    """Clone the checkout, replay the working diff and copy relevant untracked files."""
    parent = root / RUNNER_PARENT / nonce
    try:
        parent.mkdir(parents=True, exist_ok=False)
        (parent / SENTINEL_NAME).write_text(nonce + "\n", encoding="utf-8")
        target = parent / "snapshot"
        proc = subprocess.run(
            ["git", "clone", "--quiet", "--no-hardlinks", "--local", str(root), str(target)],
            env=_git_env(),
            capture_output=True,
            shell=False,
        )
        if proc.returncode != 0:
            raise SnapshotError("snapshot-error", proc.stderr.decode("utf-8", "replace").strip())
        head = git(root, "rev-parse", "HEAD").strip()
        checkout = subprocess.run(
            ["git", "checkout", "--quiet", "--detach", head],
            cwd=str(target),
            env=_git_env(),
            capture_output=True,
            shell=False,
            check=False,
        )
        if checkout.returncode != 0:
            detail = checkout.stderr.decode("utf-8", "replace").strip()
            raise SnapshotError(
                "snapshot-error", f"cannot checkout the snapshot HEAD: {detail}"
            )
        if git(target, "rev-parse", "HEAD").strip() != head:
            raise SnapshotError("snapshot-error", "the snapshot checked out a different HEAD")
        patch = git(root, "diff", "HEAD")
        if patch.strip():
            applied = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", "-"],
                cwd=str(target),
                env=_git_env(),
                input=patch.encode(),
                capture_output=True,
                shell=False,
            )
            if applied.returncode != 0:
                raise SnapshotError(
                    "snapshot-error",
                    "cannot replay the working diff: "
                    + applied.stderr.decode("utf-8", "replace").strip(),
                )
        _copy_untracked(root, target)
        return target
    except OSError as exc:
        raise SnapshotError("snapshot-error", f"cannot build the snapshot: {exc}") from exc
    except PlanError as exc:
        # Git capture inside the snapshot raises PlanError -- an oversized
        # `git diff HEAD` is the reachable case.  Left as PlanError it slips past
        # the caller's `except SnapshotError`, so the parent directory and its
        # sentinel are never removed and a whole clone is leaked on disk.
        raise SnapshotError("snapshot-error", f"cannot build the snapshot: {exc.message}") from exc


def _copy_untracked(root: Path, target: Path) -> None:
    copied = 0
    for rel in _untracked_paths(root):
        kind, body, mode = _untracked_entry(root, rel, MAX_UNTRACKED_BYTES - copied)
        copied += len(body)
        dest = target / _snapshot_relpath(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if kind == "symlink":
            os.symlink(os.fsdecode(body), dest)
            continue
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(dest, flags, stat.S_IMODE(mode) & 0o777)
        try:
            view = memoryview(body)
            while view:
                written = os.write(fd, view)
                view = view[written:]
            os.fchmod(fd, stat.S_IMODE(mode) & 0o777)
        finally:
            os.close(fd)


def remove_snapshot(root: Path, nonce: str) -> str:
    """Remove only a tree this runner created and can still prove it owns."""
    parent = root / RUNNER_PARENT / nonce
    sentinel = parent / SENTINEL_NAME
    try:
        if parent.is_symlink() or not parent.is_dir():
            return "not-owned"
        if not sentinel.is_file() or sentinel.is_symlink():
            return "not-owned"
        if sentinel.read_text(encoding="utf-8").strip() != nonce:
            return "not-owned"
    except OSError:
        return "not-owned"
    try:
        shutil.rmtree(parent)
    except OSError:
        return "retained"
    return "removed"


class Scheduler:
    """One global slot budget covering commands, ordered groups and nested shards."""

    def __init__(self, budget: int) -> None:
        self.budget = budget
        self._condition = threading.Condition()
        self._in_use = 0
        self.high_water = 0
        self.queue_high_water = 0
        self._waiting = 0

    def acquire(self, slots: int) -> int:
        slots = max(1, min(slots, self.budget))
        with self._condition:
            self._waiting += 1
            self.queue_high_water = max(self.queue_high_water, self._waiting)
            while self._in_use + slots > self.budget:
                self._condition.wait()
            self._waiting -= 1
            self._in_use += slots
            self.high_water = max(self.high_water, self._in_use)
        return slots

    def release(self, slots: int) -> None:
        with self._condition:
            self._in_use -= slots
            self._condition.notify_all()


def _terminate_group(proc: subprocess.Popen[bytes]) -> str:
    """Signal the check's whole process group -- never a pid already reaped.

    Every check leads its own session, so a descendant that keeps running after
    the leader exits is still reachable through the group.  ``proc.kill()``
    alone reaches the leader and leaves that descendant holding the output
    descriptor, which is what kept a wedged check outside every bound.

    The group may only be derived from a leader the runner still owns.
    ``Popen.poll`` and ``Popen.wait`` reap the leader and hand its pid back to
    the kernel for reuse, so ``os.getpgid(proc.pid)`` after that point can
    resolve an unrelated process and ``os.killpg`` would then signal a process
    group belonging to somebody else.  Once the leader is reaped the runner has
    no safe handle at all, and saying so is the only correct action -- which is
    also what the retained-descriptor diagnostic already reports.

    Returns the disposition, so a caller can record what actually happened
    rather than imply the descendant was dealt with.
    """
    if proc.returncode is not None:
        return "not-signalled: the check leader was already reaped"
    try:
        pgid = os.getpgid(proc.pid)
    except OSError:
        return "not-signalled: the check leader is gone"
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(pgid, sig)
        except OSError:
            return "not-signalled: the process group is gone"
        try:
            proc.wait(timeout=DRAIN_SECONDS)
            return "terminated"
        except subprocess.TimeoutExpired:
            continue
    return "unresponsive"


def _capture_output(
    proc: subprocess.Popen[bytes], buffer: CaptureBuffer, deadline: float
) -> tuple[bool, bool]:
    """Read the child's output without ever blocking past its deadline.

    A blocking ``read(n)`` returns only at ``n`` bytes or at end of file, so a
    quiet check could outlive its timeout and a descendant retaining the write
    end could block completion for ever.  Polling the descriptor instead keeps
    the deadline authoritative whatever the child does or does not print.

    Returns ``(timed_out, retained)``: whether the deadline passed with the
    check still running, and whether the descriptor was still held after the
    leader exited and the bounded drain interval elapsed.
    """
    fd = proc.stdout.fileno() if proc.stdout is not None else -1
    if fd < 0:
        return False, False
    os.set_blocking(fd, False)
    selector = selectors.DefaultSelector()
    selector.register(fd, selectors.EVENT_READ)
    timed_out = False
    retained = False
    drain_deadline: float | None = None
    try:
        while True:
            now = time.monotonic()
            if not timed_out and drain_deadline is None and now > deadline:
                timed_out = True
                _terminate_group(proc)
                drain_deadline = now + DRAIN_SECONDS
            if drain_deadline is None and proc.poll() is not None:
                # The leader is gone; every reader gets one bounded interval.
                drain_deadline = now + DRAIN_SECONDS
            if drain_deadline is not None and now > drain_deadline:
                retained = True
                break
            if not selector.select(timeout=0.25):
                continue
            try:
                chunk = os.read(fd, 65_536)
            except BlockingIOError:
                continue
            if not chunk:
                break
            buffer.feed(chunk)
    finally:
        selector.close()
    return timed_out, retained


def _allocation_for(check: Check, budget: int, parallel_checks: int) -> int:
    if check.jobs_flag is None:
        return 1
    if parallel_checks <= 1:
        return budget
    return max(1, budget // 2)


def run_check(
    check: Check,
    snapshot: Path,
    scheduler: Scheduler,
    parallel_checks: int,
) -> dict[str, Any]:
    slots = _allocation_for(check, scheduler.budget, parallel_checks)
    granted = scheduler.acquire(slots)
    started = time.monotonic()
    record: dict[str, Any] = {
        "check": check.id,
        "title": check.title,
        "slots": granted,
        "argv": list(check.argv),
        "cwd": check.cwd,
    }
    try:
        argv = list(check.argv)
        if check.jobs_flag is not None:
            argv += [check.jobs_flag, str(granted)]
            record["argv"] = argv
            record["nested_allocation"] = granted
        if check.requires_executable and shutil.which(check.requires_executable) is None:
            record.update(
                status="unavailable",
                failure_class="command-failure",
                reason=f"{check.requires_executable} is not on PATH",
                duration_seconds=0.0,
            )
            return record
        workdir = snapshot if check.cwd == "." else snapshot / check.cwd
        buffer = CaptureBuffer()
        proc = subprocess.Popen(
            argv,
            cwd=str(workdir),
            env=_child_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            start_new_session=True,
        )
        capture_error: OSError | None = None
        try:
            termination = "not-required"
            try:
                timed_out, retained = _capture_output(
                    proc, buffer, started + check.timeout_seconds
                )
            except OSError as exc:
                # A pipe read fault is runner infrastructure, not the target's
                # exit status.  Keep the partial bytes, stop the owned scope and
                # leave a scheduler-error record instead of calling EIO EOF.
                capture_error = exc
                timed_out = False
                retained = False
                termination = _terminate_group(proc)
            if retained:
                termination = _terminate_group(proc)
            try:
                proc.wait(timeout=DRAIN_SECONDS)
            except subprocess.TimeoutExpired:
                _terminate_group(proc)
                try:
                    proc.wait(timeout=DRAIN_SECONDS)
                except subprocess.TimeoutExpired:
                    pass
        except BaseException:
            # A fault after the child started must not leave it running: the
            # worker guard would otherwise report a scheduler error while the
            # check kept holding resources.
            _terminate_group(proc)
            raise
        finally:
            if proc.stdout is not None:
                proc.stdout.close()
        record["output"] = buffer.record()
        record["exit_code"] = proc.returncode
        record["duration_seconds"] = round(time.monotonic() - started, 3)
        record["descriptor_retained"] = retained
        record["termination"] = termination
        if capture_error is not None:
            record.update(
                status="failed",
                failure_class="scheduler-error",
                reason=f"capture failed: {capture_error}",
            )
        elif retained:
            # ADR-038: a retained output descriptor is a bounded red result with
            # an explicit detachment diagnostic, never a pass.  The runner does
            # not claim to have terminated a descendant that left the group.
            record.update(
                status="failed",
                failure_class="scheduler-error",
                reason=(
                    "an output descriptor was retained after the check leader exited; "
                    "a detached descendant may still be running"
                ),
            )
        elif timed_out:
            record.update(status="failed", failure_class="command-failure", reason="timeout")
        elif proc.returncode == 0:
            record["status"] = "passed"
        else:
            record.update(
                status="failed",
                failure_class="test-failure" if check.kind == "suite" else "command-failure",
            )
        return record
    except OSError as exc:
        record.update(
            status="failed",
            failure_class="command-failure",
            reason=str(exc),
            duration_seconds=round(time.monotonic() - started, 3),
        )
        return record
    finally:
        scheduler.release(granted)


def _child_env() -> dict[str, str]:
    env = _git_env()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def execute(
    checks: Sequence[Check],
    snapshot: Path,
    budget: int,
) -> tuple[list[dict[str, Any]], Scheduler]:
    scheduler = Scheduler(budget)
    results: list[dict[str, Any]] = []
    lock = threading.Lock()
    grouped: dict[str, list[Check]] = {}
    singles: list[Check] = []
    for check in checks:
        if check.group is None:
            singles.append(check)
        else:
            grouped.setdefault(check.group, []).append(check)
    for members in grouped.values():
        members.sort(key=lambda c: c.order)
    units = len(singles) + len(grouped)

    def guarded(check: Check) -> dict[str, Any]:
        """Never let a worker fault remove a check from the accounting.

        An unhandled exception here used to kill the thread and drop the record
        entirely, so a selected check could vanish and the run still aggregate
        green.  A fault is a scheduler error, and it stays in the report.
        """
        try:
            return run_check(check, snapshot, scheduler, units)
        except BaseException as exc:  # noqa: BLE001 - a fault must stay visible
            return {
                "check": check.id,
                "title": check.title,
                "status": "failed",
                "failure_class": "scheduler-error",
                "reason": f"the worker faulted: {type(exc).__name__}: {exc}",
            }

    def run_single(check: Check) -> None:
        record = guarded(check)
        with lock:
            results.append(record)

    def run_group(gid: str, members: list[Check]) -> None:
        for index, check in enumerate(members):
            record = guarded(check)
            record["group"] = gid
            with lock:
                results.append(record)
            if record.get("status") != "passed":
                for skipped in members[index + 1:]:
                    with lock:
                        results.append(
                            {
                                "check": skipped.id,
                                "title": skipped.title,
                                "group": gid,
                                "status": "not-started",
                                "reason": f"ordered group stopped at {check.id}",
                            }
                        )
                return

    threads: list[threading.Thread] = []
    for check in singles:
        threads.append(threading.Thread(target=run_single, args=(check,), daemon=False))
    for gid, members in grouped.items():
        threads.append(threading.Thread(target=run_group, args=(gid, members), daemon=False))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    # Prove the disjoint union of selection and completion before any caller
    # reads an outcome: a check with no terminal record is a scheduler error,
    # not an absence that quietly aggregates green.
    recorded = {r["check"] for r in results}
    for check in checks:
        if check.id not in recorded:
            results.append(
                {
                    "check": check.id,
                    "title": check.title,
                    "status": "failed",
                    "failure_class": "scheduler-error",
                    "reason": "the scheduler returned no terminal record for this check",
                }
            )
    results.sort(key=lambda r: r["check"])
    return results, scheduler


def plan_record(
    check_map: CheckMap,
    selection: Selection,
    checks: Sequence[Check],
    capacity: Mapping[str, Any],
) -> dict[str, Any]:
    omitted = sorted(set(check_map.checks) - {c.id for c in checks})
    return {
        "schema": PLAN_SCHEMA,
        "map_digest": check_map.digest,
        "requested_scopes": selection.requested,
        "full": selection.full,
        "base": selection.base,
        "changed_paths": selection.changed_paths,
        "selected_scopes": {
            scope: reasons for scope, reasons in sorted(selection.scopes.items())
        },
        "selected_checks": [
            {
                "id": c.id,
                "title": c.title,
                "argv": list(c.argv),
                "cwd": c.cwd,
                "kind": c.kind,
                "group": c.group,
                "nested_jobs_flag": c.jobs_flag,
            }
            for c in checks
        ],
        "omitted_checks": omitted,
        "capacity": dict(capacity),
    }


def confine_report_path(root: Path, rel_path: str) -> str:
    """Refuse a report target that leaves the repository through a symlink.

    ``_safe_relpath`` is lexical, so it cannot see that an existing directory
    component is a link out of the tree.  Checking the components before
    anything is created keeps the refusal ahead of execution.
    """
    safe = _safe_relpath(rel_path, field_name="report path")
    probe = root
    for part in safe.split("/")[:-1]:
        probe = probe / part
        if probe.is_symlink():
            raise PlanError(
                "unsafe-path", f"report path traverses a symlink: {safe}"
            )
    return safe


def write_report(root: Path, rel_path: str, payload: Mapping[str, Any]) -> str:
    safe = confine_report_path(root, rel_path)
    target = root / safe
    target.parent.mkdir(parents=True, exist_ok=True)
    base = root.resolve()
    resolved = target.parent.resolve()
    if resolved != base and base not in resolved.parents:
        raise PlanError("unsafe-path", f"report path leaves the repository: {safe}")
    tmp = target.parent / f".{target.name}.{uuid.uuid4().hex}.partial"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(tmp, flags, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    os.replace(tmp, target)
    return safe


def render_human(plan: Mapping[str, Any], run: Mapping[str, Any] | None) -> str:
    captured = (run or plan).get("source_identity")
    lines = [
        f"source     {captured if captured else 'not captured (plan only)'}",
        f"map        {plan['map_digest'][:12]}",
        f"base       {plan['base'] or '(working tree only)'}",
        f"changed    {len(plan['changed_paths'])} path(s)",
        "",
        "selected scopes",
    ]
    for scope, reasons in plan["selected_scopes"].items():
        lines.append(f"  {scope:<16} {'; '.join(reasons)}")
    lines.append("")
    lines.append("selected checks")
    for check in plan["selected_checks"]:
        suffix = f"  [group {check['group']}]" if check["group"] else ""
        lines.append(f"  {check['id']:<22} {check['title']}{suffix}")
    if plan["omitted_checks"]:
        lines.append("")
        lines.append("omitted: " + ", ".join(plan["omitted_checks"]))
    capacity = plan["capacity"]
    lines.append("")
    lines.append(
        f"budget     {capacity['effective_budget']} slot(s) ({capacity['source']}, cap {capacity['safety_cap']})"
    )
    if run is not None:
        lines.append("")
        lines.append("results")
        for record in run["checks"]:
            status = record.get("status", "unknown")
            duration = record.get("duration_seconds")
            shown = f"{duration:.1f}s" if isinstance(duration, float) else "-"
            lines.append(f"  {record['check']:<22} {status:<12} {shown}")
        lines.append("")
        lines.append(f"outcome    {run['outcome']}")
        if run.get("failure_classes"):
            lines.append("failures   " + ", ".join(run["failure_classes"]))
    return "\n".join(lines)


def emit(args: argparse.Namespace, plan: Mapping[str, Any], run: Mapping[str, Any] | None) -> None:
    if args.format == "json":
        print(json.dumps(run if run is not None else plan, indent=2, sort_keys=True))
    else:
        print(render_human(plan, run))


def refusal(args: argparse.Namespace, code: str, message: str, detail: Any = None) -> int:
    payload = {
        "schema": RUN_SCHEMA,
        "outcome": "refused",
        "failure_class": "snapshot-error" if code == "snapshot-error" else "invalid-plan",
        "code": code,
        "message": message,
        "detail": detail,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"refused: {code}: {message}", file=sys.stderr)
        if detail:
            for item in detail if isinstance(detail, list) else [detail]:
                print(f"  {item}", file=sys.stderr)
    return 2


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_checks.py",
        description="Select and run the repository checks that the changed scope owns.",
    )
    parser.add_argument("--scope", action="append", default=[], help="a declared scope id; repeatable")
    parser.add_argument("--base", default=None, help="compare committed history against this ref")
    parser.add_argument("--full", action="store_true", help="select every declared scope")
    parser.add_argument("--plan", action="store_true", help="print the plan and run nothing")
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--jobs", type=positive_int, default=None, help="override the automatic budget")
    parser.add_argument("--report", default=None, help="write the run report to this repository-relative path")
    parser.add_argument("--map", default=DEFAULT_MAP_PATH, help="the check map to read")
    return parser


def repository_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        env=_git_env(),
        shell=False,
    )
    if proc.returncode != 0:
        raise PlanError("not-a-repository", "run_checks.py must run inside a Git repository")
    return Path(proc.stdout.decode().strip())


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = repository_root()
        check_map = load_map(root, args.map)
        refuse_stale_commands(root, check_map)
        # With no scope and no --full, the actual diff is the whole request:
        # selecting everything by default would defeat the point of the map.
        selection = build_selection(root, check_map, args.scope, args.base, args.full)
        checks = selected_checks(check_map, selection)
        if args.report is not None:
            confine_report_path(root, args.report)
    except PlanError as exc:
        return refusal(args, exc.code, exc.message, exc.detail)

    capacity = capacity_plan(args.jobs, item_count=_runnable_slot_cap(checks))
    plan = plan_record(check_map, selection, checks, capacity)

    if args.plan:
        emit(args, plan, None)
        return 0
    if not checks:
        run = dict(plan, schema=RUN_SCHEMA, outcome="nothing-selected", checks=[], failure_classes=[])
        emit(args, plan, run)
        return 0

    attempts: list[dict[str, Any]] = []
    try:
        return _run_attempts(args, root, check_map, selection, checks, capacity, plan, attempts)
    except PlanError as exc:
        # Every refusal leaves by the declared route.  Git capture around the
        # attempt loop -- `source_identity` before and after execution -- raises
        # PlanError, and an escape from here would exit 1 with a traceback: the
        # same code a red run uses, so a caller could not tell a failed check
        # from a runner that never ran one.
        return refusal(args, exc.code, exc.message, exc.detail)


def _run_attempts(
    args: argparse.Namespace,
    root: Path,
    check_map: CheckMap,
    selection: Selection,
    checks: Sequence[Check],
    capacity: Mapping[str, Any],
    plan: Mapping[str, Any],
    attempts: list[dict[str, Any]],
) -> int:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        nonce = uuid.uuid4().hex
        before = source_identity(root)
        if attempt > 1:
            # A superseded attempt re-derives its plan: the source that moved may
            # own checks the first plan never selected.
            try:
                selection = build_selection(root, check_map, args.scope, args.base, args.full)
                checks = selected_checks(check_map, selection)
                plan = plan_record(check_map, selection, checks, capacity)
            except PlanError as exc:
                return refusal(args, exc.code, exc.message, exc.detail)
        try:
            snapshot = make_snapshot(root, nonce)
        except SnapshotError as exc:
            remove_snapshot(root, nonce)
            return refusal(args, exc.code, exc.message)
        try:
            results, scheduler = execute(checks, snapshot, capacity["effective_budget"])
            after = source_identity(root)
        finally:
            cleanup = remove_snapshot(root, nonce)
        if after != before:
            attempts.append({"attempt": attempt, "outcome": "superseded", "source_before": before})
            if attempt == MAX_ATTEMPTS:
                run = dict(
                    plan,
                    schema=RUN_SCHEMA,
                    outcome="unstable-source",
                    failure_classes=["unstable-source"],
                    checks=[],
                    attempts=attempts,
                )
                emit(args, plan, run)
                return 3
            continue
        classes = sorted(
            {r["failure_class"] for r in results if r.get("failure_class")}
        )
        unknown = [c for c in classes if c not in FAILURE_CLASSES]
        if unknown:
            return refusal(args, "unknown-failure-class", f"undeclared failure class: {unknown}")
        not_started = [r for r in results if r.get("status") == "not-started"]
        outcome = "green" if not classes and not not_started else "red"
        run = dict(
            plan,
            schema=RUN_SCHEMA,
            source_identity=before,
            snapshot_cleanup=cleanup,
            outcome=outcome,
            failure_classes=classes,
            checks=results,
            attempts=attempts,
            scheduler={
                "budget": scheduler.budget,
                "slot_high_water": scheduler.high_water,
                "queue_high_water": scheduler.queue_high_water,
            },
            # The composed run reaches a nested runner that does keep a timing
            # cache, so a reader cannot assume the question does not arise.
            # State this runner's own disposition rather than leave it to be
            # inferred from the absence of a field.
            cache={
                "result_cache": "none",
                "selection_input": False,
                "detail": (
                    "run_checks.py holds no cache: no verdict, duration or membership is "
                    "read from or written to one, and selection derives only from the map "
                    "and the current diff.  A nested runner's own timing cache is reported "
                    "in that runner's record, inside this check's captured output."
                ),
            },
        )
        if args.report:
            try:
                run["report_path"] = write_report(root, args.report, run)
            except (PlanError, OSError) as exc:
                return refusal(args, "unsafe-report-path", str(exc))
        emit(args, plan, run)
        return 0 if outcome == "green" else 1
    return 3


if __name__ == "__main__":
    sys.exit(main())
