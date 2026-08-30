#!/usr/bin/env python3
"""hexctl - deterministic, receipt-backed controller for the one-shot loop.

The model does the work; this script decides what comes next and refuses to
advance without a receipt. State lives in `.hexaemeron/state.json` beside an
append-only, hash-chained ledger (`.hexaemeron/ledger.jsonl`). Every mutating
command appends a ledger entry, so `verify` can prove the run history was not
edited after the fact.

Phase order is fixed. Globally: study -> runbook -> steps -> integrate -> done.
Within each step: implement -> audit -> prose -> push. Step branches chain off
one another and their pull requests stack; nothing merges while the steps run.
The integrate phase merges the stack into the run branch in step order, then
merges the run branch into the recorded base exactly once and closes any
recorded task issue.

Exit codes: 0 success, 2 validation/usage error, 1 unexpected failure.
Stdout from `next` and `status --json` is a single JSON object; everything
human-facing goes to plain text or stderr.
"""

import argparse
import contextlib
import ctypes
import datetime
import errno
import fcntl
import glob
import hashlib
import importlib.util
import io
import json
import os
import re
import selectors
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

STATE_DIR_NAME = ".hexaemeron"
STATE_FILE = "state.json"
LEDGER_FILE = "ledger.jsonl"
STUDY_AMENDMENT_PENDING_FILE = "study-amendment-pending.json"
RUNBOOK_AMENDMENT_PENDING_FILE = "runbook-amendment-pending.json"
VERSION_RESOLUTION_PENDING_FILE = "version-resolution.pending.json"
AMENDMENT_PENDING_FILES = {
    "study": STUDY_AMENDMENT_PENDING_FILE,
    "runbook": RUNBOOK_AMENDMENT_PENDING_FILE,
}

# The run-level pull request body the prose phase writes and the integrate
# phase opens the integration pull request from. It is the last thing a run
# writes into the repository, so it is where the work a run gave up on has to
# be named: the next study over the same target reads it as prior art.
RUN_PR_FILE = "run-pr.md"
WORKTREE_FILE = "worktree"
"""The one line the origin checkout keeps, naming the tree the run works in."""
CARRIED_FORWARD_HEADING = "## Carried forward"

# ``issue`` remains accepted only so runs created by older controllers can
# advance directly into implementation without losing their ledger history.
STEP_PHASES = ["issue", "implement", "audit", "prose", "push"]
GLOBAL_PHASES = ["study", "runbook", "steps", "integrate", "done"]

# Decorative only: the day each phase maps to in the plugin's naming conceit.
DAY = {
    "study": 1,
    "runbook": 2,
    "issue": 3,
    "implement": 4,
    "audit": 5,
    "prose": 6,
    "push": 7,
}

DEFAULT_CONFIG = {
    "skills": {
        "prose_lint": "hexaemeron:imprimatur",
        "voice": "hexaemeron:vulgate",
        # The Pashov suite is vendored in this plugin. Preflight records
        # these ids via `record security_suite ...` -- the controller gates
        # the audit phase on that receipt, not on this list.
        "security": [
            "hexaemeron:x-ray",
            "hexaemeron:solidity-auditor",
            "hexaemeron:fizz",
        ],
    },
    "audit": {
        "max_rounds": 8,
        "stacked_suffix": "--audit",
        "fold": False,
        # No `log_path` here. A literal put every run's rounds in one file, so
        # that file entered `sync-run`'s overlap set on every integration where
        # anything else had merged. `init` derives the run's own path instead.
    },
    "git": {
        "base": "main",
        "run_branch_prefix": "fiat/",
        "draft_pr": False,
    },
    "solidity": "auto",
}

CONFIG_SET_EXACT_PATHS = frozenset({"audit.log_path", "git"})
CONFIG_SET_PREFIXES = ("git.",)
"""The complete mutable Fiat configuration surface.

Audit policy, skill identity and Solidity classification are controller gates, not
operator tuning knobs.  A run may move its own audit record and may change Git
settings, but no other stored config path can be rewritten after ``init``.
"""


def config_path_is_mutable(path: str) -> bool:
    """Return whether ``config set`` may write this exact path."""
    return path in CONFIG_SET_EXACT_PATHS or path.startswith(CONFIG_SET_PREFIXES)

LINTS = ("phylax", "ephoros", "hypomnema")
"""The three bundled lints a non-Solidity audit round runs.

Named here so the flags, the refusal message and the stored round all read from one
list. `references/audit-loop.md` is the contract they satisfy.
"""

ELENCHUS_VERDICTS = ("guarded", "unguarded", "passed", "inconclusive")
"""The complete Elenchus result vocabulary accepted on an audit fix receipt."""

AUDIT_FILTER = "sapheneia:sapheneia"
"""The exact bounded audit-record pass every new round declares."""

AUDIT_RECORD_SCHEMAS = (
    "fiat-audit-round/v1",
    "fiat-audit-round/v2",
)
AUDIT_RECORD_SCHEMA = AUDIT_RECORD_SCHEMAS[-1]
AUDIT_COVERAGE_VALUES = ("reviewed", "not-applicable")
AUDIT_FINDINGS_HEADER = "| id | severity | file | finding | status |"
AUDIT_FINDINGS_SEPARATOR = "| --- | --- | --- | --- | --- |"
AUDIT_ZERO_FINDING_ROW = "| -- | -- | -- | none | -- |"
AUDIT_TIMESTAMP_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", re.ASCII
)
AUDIT_OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd
AUDIT_PHYSICAL_LINE_BYTES_MAX = 1024 * 1024
AUDIT_RENDERER_DIAGNOSTIC_BYTES_MAX = 4096


def elenchus_verdict_obligation() -> dict:
    """Describe the conditional audit-round input without claiming it was run."""
    return {
        "flag": "--elenchus-verdict",
        "required_with": "--fixes-commit",
        "choices": list(ELENCHUS_VERDICTS),
    }


def audit_filter_obligation() -> dict:
    """Describe the exact checked declaration without claiming semantic proof."""
    return {
        "flag": "--audit-filter",
        "value": AUDIT_FILTER,
    }


SOLIDITY_MODES = ("auto", True, False)
"""What a stored legacy ``config.solidity`` value may contain.

`auto` reads the answer off the `security_suite` receipt, which is where the run
already recorded whether the Pashov pair applies. `true` and `false` force it, for a
legacy run that recorded an override before the config write gate existed.
"""


def solidity_mode(value) -> bool:
    """True when a value is one of the three modes.

    Checked by identity rather than by `in SOLIDITY_MODES`, because Python makes
    `1 == True` and `0 == False`, so membership would accept an integer as a mode and
    store it. An integer in an older state is not a way to spell ``true``.
    """
    if isinstance(value, bool):
        return True
    return value == "auto"

WAIVER_PREFIX = "waived"
"""How a `security_suite` receipt says the Pashov pair did not run.

One rule, so the classifier never guesses: the receipt is a waiver when it is a string
whose first word is this, ignoring case and surrounding space. Preflight writes
`"waived: <reason>"`, and a reason is the point of the string.
"""

SYNC_BASE_HEAD_KEY = "base_head"
"""Where the sync receipt records the exact base tip the run merged.

Two consumers, one name: `done_sync_run` writes the verified remote base tip
under this key, and `done_integrate` reads it back to subtract the ledger rows
that base had already published. The sites named different keys once -- the
writer stored `base_head` while the reader asked for `base_commit` -- so the
published set was always empty and the fiat-v5.16.1 subtraction never engaged
(skills#608). A receipt without the key still reads as the empty set, which is
the older and stricter arithmetic.
"""

def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


SOURCE_BYTES_MAX = 2 * 1024 * 1024
AMENDMENT_HISTORY_MAX = 500
GIT_OUTPUT_MAX = 2 * 1024 * 1024
GIT_PATHS_MAX = 500
# Integration revalidation reads a surface that grows with the base, so it
# carries its own ceiling. GIT_PATHS_MAX still bounds the commit range, the
# prose diff and the checkpoint ref set, none of which grow that way.
INTEGRATION_PATHS_MAX = 4096
GIT_TIMEOUT = 30
INTEGRATION_REVALIDATION_SCHEMA = "fiat-integration-revalidation/v1"
INTEGRATION_REVALIDATION_SCHEMA_V2 = "fiat-integration-revalidation/v2"
INTEGRATION_REVALIDATION_FILE = os.path.join(
    STATE_DIR_NAME, "integration-revalidation.json"
)
INTEGRATION_CHECKS_MAX = 64
INTEGRATION_COMMAND_BYTES_MAX = 2048
INTEGRATION_CHECK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
INTEGRATION_SYNC_SUPERSESSIONS_MAX = 8
INTEGRATION_SYNC_REASON_BYTES_MAX = 1024
SYNC_RESOLUTION_GUARD_SCHEMA = "fiat-sync-resolution-guard/v1"
SYNC_RESOLUTION_GUARD_KEYS = frozenset(
    {
        "schema",
        "side_selected_paths",
        "superseded_intersection_paths",
        "acknowledged_paths",
    }
)
SYNC_TREE_PATH_BATCH_MAX = 64
SYNC_TREE_ARG_BYTES_MAX = 64 * 1024
GENERATOR_AGGREGATE_FILE_DIGEST_DOMAIN = b"fiat-generator-file/v1\0"
GENERATOR_AGGREGATE_TREE_DIGEST_DOMAIN = b"fiat-generator-tree/v1\0"
GENERATOR_AGGREGATE_REGISTRY = {
    "promise-machine-portable-runtime-v1": {
        "prefix": ".agents/skills/promise-machine/runtime/",
        "generator": "scripts/portable_promise_machine.py",
        "manifest": "MANIFEST.json",
        "manifest_schema": "promise-machine-portable-runtime/v1",
        "manifest_contract": "promise-machine/v1",
        "command": "python3 scripts/portable_promise_machine.py check",
        "max_files": 1024,
        "max_bytes": 32 * 1024 * 1024,
    },
}
RESOLUTION_SYNC_KEYS = frozenset(
    {
        "commit",
        "base",
        "starting_base",
        "base_head",
        "parents",
        "github_verified",
        "product_evidence",
        "revalidation",
        "resolution_guard",
    }
)
RESOLUTION_REVALIDATION_KEYS = frozenset(
    {
        "schema",
        "artifact",
        "sha256",
        "base_before",
        "base_after",
        "product_paths",
        "upstream_paths",
        "overlap_paths",
        "composition_paths",
        "affected_paths",
        "checks",
    }
)
RESOLUTION_REVALIDATION_CHECK_KEYS = frozenset(
    {"id", "command", "paths", "exit"}
)
OBSERVATION_BINDING_CONTRACT = "fiat-run-observation-binding/v1"
OBSERVATION_CONTRACT = "promise-machine-run-observation/v1"
OBSERVATION_BYTES_MAX = 1_048_576
OBSERVATION_BINDINGS_MAX = 64
OBSERVATION_PATH_BYTES_MAX = 1024
OBSERVATION_CAPTURE_STATUSES = (
    "accepted",
    "gap",
    "refused",
    "unknown",
    "unavailable",
)
OBSERVATION_REDACTION_STATUSES = ("passed", "failed", "unknown")
OBSERVATION_REASON_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_OBSERVATION_VALIDATOR = None

CHECKPOINT_SCHEMA = "fiat-controller-checkpoint/v1"
CHECKPOINT_RESULT_SCHEMA = "fiat-controller-checkpoint-export/v1"
CHECKPOINT_RESTORE_RESULT_SCHEMA = "fiat-controller-checkpoint-restore/v1"
CHECKPOINT_MANIFEST_FILE = "MANIFEST.json"
CHECKPOINT_CONTROLLER_DIR = "controller"
CHECKPOINT_RESTORE_MARKER_FILE = "checkpoint-restore.json"
CHECKPOINT_RESTORE_MARKER_SCHEMA = "fiat-controller-checkpoint-restore-marker/v1"
CHECKPOINT_FILES_MAX = 4096
CHECKPOINT_DIRECTORIES_MAX = 4096
CHECKPOINT_TOTAL_BYTES_MAX = 256 * 1024 * 1024
CHECKPOINT_FILE_BYTES_MAX = 64 * 1024 * 1024
CHECKPOINT_MANIFEST_BYTES_MAX = 1024 * 1024
CHECKPOINT_PATH_BYTES_MAX = 1024
CHECKPOINT_JSON_DEPTH_MAX = 128
CHECKPOINT_IO_CHUNK = 64 * 1024
CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS = frozenset(
    {
        "fiat-v5.35.1",
        "fiat-v5.36.1",
        "fiat-v5.37.1",
        "fiat-v5.38.1",
        "fiat-v5.39.1",
        "fiat-v5.40.1",
        "fiat-v5.41.1",
        "fiat-v5.42.1",
        "fiat-v5.43.1",
        "fiat-v5.44.1",
    }
)
VERSION_RELATIONS_SCHEMA = "fiat-version-relations/v1"
VERSION_RELATIONS_INFO = "version-relations"
VERSION_RELATION = "next-generation-after-integration-base"
VERSION_RELATIONS_MAX = 32
VERSION_RELATION_PATH_BYTES_MAX = 1024
VERSION_RELATION_COUNTER_DIGITS_MAX = 128
VERSION_RELATION_COUNTER_MAX = (10 ** VERSION_RELATION_COUNTER_DIGITS_MAX) - 1
VERSION_RELATION_SKILL_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RELATION_FENCE_RE = re.compile(
    r"^ {0,3}(?P<mark>`{3,}|~{3,})(?P<info>.*)$"
)
VERSION_RELATION_TARGET_KEYS = frozenset(
    {
        "skill",
        "ledger",
        "relation",
        "anchor_version",
        "evolution",
        "generation",
        "epoch",
        "frontier_status",
        "frontier_revision",
        "frontier_sha256",
        "current_frontier_sha256",
        "next_job_sha256",
        "ledger_sha256",
        "skill_sha256",
        "skill_metadata_version",
    }
)
VERSION_RELATION_KEYS = frozenset(
    {"schema", "source_sha256", "anchor_commit", "targets"}
)
VERSION_RESOLUTION_SCHEMA = "fiat-version-resolution/v1"
VERSION_RESOLUTION_PENDING_SCHEMA = "fiat-version-resolution-pending/v1"
VERSION_RESOLUTIONS_MAX = 8
VERSION_RESOLUTION_PENDING_BYTES_MAX = 256 * 1024
VERSION_RESOLUTION_TARGET_KEYS = frozenset(
    {
        "skill",
        "ledger",
        "relation",
        "anchor_version",
        "base_version",
        "resolved_version",
        "base_ledger_sha256",
        "head_ledger_sha256",
        "row_sha256",
        "skill_sha256",
        "skill_metadata_version",
    }
)
VERSION_RESOLUTION_KEYS = frozenset(
    {
        "schema",
        "runbook_sha256",
        "relations_sha256",
        "base_ref",
        "base_commit",
        "head_commit",
        "targets",
        "ts",
    }
)


def scoped_path(base_dir: str, supplied: str, label: str) -> str:
    """Resolve one path and refuse anything outside the target directory."""
    try:
        root = os.path.realpath(base_dir)
        candidate = (
            supplied if os.path.isabs(supplied) else os.path.join(root, supplied)
        )
        resolved = os.path.realpath(candidate)
    except (OSError, TypeError, ValueError):
        die(f"{label} is not a valid filesystem path")
    try:
        inside = os.path.commonpath((root, resolved)) == root
    except ValueError:
        inside = False
    if not inside:
        die(f"{label} escapes target directory: {supplied}")
    return resolved


def read_bounded_source(base_dir: str, supplied: str, label: str) -> tuple[str, bytes]:
    """Read a source artefact once, with containment and a hard byte ceiling."""
    path = scoped_path(base_dir, supplied, label)
    if not os.path.isfile(path):
        die(f"{label} is not a regular file: {supplied}")
    try:
        with open(path, "rb") as handle:
            data = handle.read(SOURCE_BYTES_MAX + 1)
    except OSError as exc:
        die(f"{label} cannot be read: {exc}")
    if len(data) > SOURCE_BYTES_MAX:
        die(f"{label} exceeds {SOURCE_BYTES_MAX}-byte cap")
    return path, data


def controller_run_id(state: dict) -> str:
    """Return the stable observation identity for one controller run."""
    identity = {
        "base": state.get("base"),
        "controller": state.get("controller", "hexctl"),
        "created_at": state.get("created_at"),
        "run_branch": state.get("run_branch"),
        "topic": state.get("topic"),
        "version": state.get("version", 1),
    }
    return "fiat-" + hashlib.sha256(canonical(identity).encode()).hexdigest()


def observation_error(code: str, message: str, recovery: str, exit_code: int = 2):
    die(f"{code} {message}; recovery: {recovery}", exit_code)


def observation_relative_path(base_dir: str, supplied: str, *, exit_code: int = 2) -> str:
    """Admit one canonical run-local observation path without following links."""
    if not isinstance(supplied, str) or not supplied or os.path.isabs(supplied):
        observation_error(
            "FOB002",
            "the companion path is not a canonical run-local relative path",
            "name a regular file beneath .hexaemeron/observations",
            exit_code,
        )
    if supplied != os.path.normpath(supplied):
        observation_error(
            "FOB002",
            "the companion path is not lexically canonical",
            "remove dot segments and name a file beneath .hexaemeron/observations",
            exit_code,
        )
    try:
        encoded = supplied.encode("utf-8")
    except UnicodeEncodeError:
        encoded = b""
    parts = supplied.split(os.sep)
    if (
        not encoded
        or len(encoded) > OBSERVATION_PATH_BYTES_MAX
        or len(parts) < 3
        or parts[:2] != [STATE_DIR_NAME, "observations"]
        or any(
            not part
            or part in {".", ".."}
            or any(ord(character) < 32 or ord(character) == 127 for character in part)
            for part in parts
        )
    ):
        observation_error(
            "FOB002",
            "the companion path is outside the bounded observation namespace",
            "name a canonical regular file beneath .hexaemeron/observations",
            exit_code,
        )
    return os.sep.join(parts)


def _read_observation_once(
    base_dir: str, relative: str, *, exit_code: int = 2
) -> tuple[bytes, tuple]:
    """Read through no-follow directory descriptors and retain one identity."""
    root_fd = None
    directory_fds = []
    file_fd = None
    try:
        root_path = os.path.realpath(base_dir)
        root_fd = os.open(
            root_path,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
        )
        directory_fds = [root_fd]
        directory_fd = root_fd
        parts = relative.split(os.sep)
        for part in parts[:-1]:
            next_fd = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=directory_fd,
            )
            directory_fd = next_fd
            directory_fds.append(next_fd)
        file_fd = os.open(
            parts[-1],
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            dir_fd=directory_fd,
        )
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            raise OSError("not regular")
        chunks = []
        remaining = OBSERVATION_BYTES_MAX + 1
        while remaining:
            chunk = os.read(file_fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > OBSERVATION_BYTES_MAX:
            raise OSError("too large")
        after = os.fstat(file_fd)
        named = os.stat(parts[-1], dir_fd=directory_fd, follow_symlinks=False)
        identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        final_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        named_identity = (
            named.st_dev,
            named.st_ino,
            named.st_size,
            named.st_mtime_ns,
            named.st_ctime_ns,
        )
        if identity != final_identity or identity != named_identity or len(data) != after.st_size:
            raise OSError("changed during read")
        root_named = os.stat(root_path, follow_symlinks=False)
        root_identity = os.fstat(root_fd)
        if (root_named.st_dev, root_named.st_ino) != (
            root_identity.st_dev,
            root_identity.st_ino,
        ):
            raise OSError("root changed during read")
        for index, part in enumerate(parts[:-1]):
            named_directory = os.stat(
                part,
                dir_fd=directory_fds[index],
                follow_symlinks=False,
            )
            opened_directory = os.fstat(directory_fds[index + 1])
            if (named_directory.st_dev, named_directory.st_ino) != (
                opened_directory.st_dev,
                opened_directory.st_ino,
            ):
                raise OSError("directory changed during read")
        return data, identity
    except OSError:
        observation_error(
            "FOB002",
            "the companion path is missing, unsafe, unstable, or outside its byte ceiling",
            "write one stable regular file beneath .hexaemeron/observations and retry",
            exit_code,
        )
    finally:
        if file_fd is not None:
            os.close(file_fd)
        for descriptor in reversed(directory_fds):
            os.close(descriptor)


def read_observation_bytes(
    base_dir: str, supplied: str, *, exit_code: int = 2
) -> tuple[str, bytes]:
    """Read the same named bytes twice so a clean receipt has one stable subject."""
    relative = observation_relative_path(base_dir, supplied, exit_code=exit_code)
    first, first_identity = _read_observation_once(
        base_dir, relative, exit_code=exit_code
    )
    second, second_identity = _read_observation_once(
        base_dir, relative, exit_code=exit_code
    )
    if first_identity != second_identity or first != second:
        observation_error(
            "FOB002",
            "the companion bytes changed while they were selected",
            "stop the writer, publish one stable prefix, and retry",
            exit_code,
        )
    return relative, second


def recheck_observation_bytes(
    base_dir: str,
    relative: str,
    expected: bytes,
    *,
    exit_code: int = 2,
) -> None:
    """Re-establish the named subject after validation has completed."""
    final_relative, final = read_observation_bytes(
        base_dir,
        relative,
        exit_code=exit_code,
    )
    if final_relative != relative or final != expected:
        observation_error(
            "FOB002",
            "the companion bytes changed before the claim completed",
            "stop the writer, publish one stable prefix, and retry",
            exit_code,
        )


def _strict_observation_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate member")
        value[key] = item
    return value


def observation_summary(data: bytes, *, exit_code: int = 2) -> dict:
    """Extract the exact closed identity and interval from accepted JSONL bytes."""
    try:
        text = data.decode("utf-8")
        lines = text.splitlines()
        events = [
            json.loads(
                line,
                object_pairs_hook=_strict_observation_object,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite")),
            )
            for line in lines
        ]
    except (UnicodeDecodeError, ValueError, TypeError):
        observation_error(
            "FOB003",
            "the selected prefix is not closed UTF-8 JSONL",
            "validate and republish the prefix before binding it",
            exit_code,
        )
    if not events or any(not isinstance(event, dict) for event in events):
        observation_error(
            "FOB003",
            "the selected prefix has no closed event sequence",
            "record one run.started event and a valid closed prefix",
            exit_code,
        )
    run_values = [event.get("run_id") for event in events]
    contract_values = [event.get("schema_id") for event in events]
    sequences = [event.get("sequence") for event in events]
    event_ids = [event.get("event_id") for event in events]
    if (
        any(not isinstance(value, str) or not value for value in run_values)
        or any(not isinstance(value, str) or not value for value in contract_values)
        or len(set(run_values)) != 1
        or len(set(contract_values)) != 1
        or sequences != list(range(1, len(events) + 1))
        or any(not isinstance(value, str) or not value for value in event_ids)
    ):
        observation_error(
            "FOB003",
            "the selected prefix identity or interval is inconsistent",
            "emit one contract, run identity, and contiguous event interval",
            exit_code,
        )
    return {
        "contract": contract_values[0],
        "run_id": run_values[0],
        "event_count": len(events),
        "first_sequence": sequences[0],
        "last_sequence": sequences[-1],
        "first_event_id": event_ids[0],
        "last_event_id": event_ids[-1],
    }


def observation_validator_module(*, exit_code: int = 2):
    global _OBSERVATION_VALIDATOR
    if _OBSERVATION_VALIDATOR is not None:
        return _OBSERVATION_VALIDATOR
    repository = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
    )
    source = os.path.join(repository, "scripts", "run_observation.py")
    try:
        spec = importlib.util.spec_from_file_location(
            "fiat_run_observation_validator", source
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    except (AttributeError, ImportError, OSError):
        observation_error(
            "FOB003",
            "the bound observation validator is unavailable",
            "restore the receipted validator surface before selecting a prefix",
            exit_code,
        )
    _OBSERVATION_VALIDATOR = module
    return module


def validated_observation_prefix(base_dir: str, supplied: str, state: dict):
    relative, data = read_observation_bytes(base_dir, supplied)
    validator = observation_validator_module()
    findings = validator.validate_bytes(
        data,
        display_path=relative,
        allow_prefix=True,
    )
    if findings:
        observation_error(
            "FOB003",
            "the selected observation prefix failed its bound validator",
            "repair the prefix and rerun check-prefix before binding it",
        )
    summary = observation_summary(data)
    if (
        summary["contract"] != OBSERVATION_CONTRACT
        or summary["run_id"] != controller_run_id(state)
    ):
        observation_error(
            "FOB003",
            "the selected prefix names the wrong contract or controller run",
            "emit the current contract and observation_run_id, then retry",
        )
    recheck_observation_bytes(base_dir, relative, data)
    return relative, data, summary


def decoded_source(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        die(f"{label} is not UTF-8 text")


def read_configured_audit_log(
    base_dir: str, configured: str, supplied: str | None
) -> tuple[str, bytes]:
    """Read the one configured log without following aliases or symlinks."""
    if not isinstance(configured, str) or not configured:
        die("audit config has no log_path")
    root = os.path.realpath(base_dir)
    configured_path = scoped_path(root, configured, "audit log path")
    lexical = os.path.abspath(
        configured if os.path.isabs(configured) else os.path.join(root, configured)
    )
    if supplied is not None:
        supplied_lexical = os.path.abspath(
            supplied if os.path.isabs(supplied) else os.path.join(root, supplied)
        )
        supplied_path = scoped_path(root, supplied, "supplied audit log path")
        if supplied_lexical != lexical:
            die("--log must name the configured audit log path")
        if supplied_path != supplied_lexical:
            die("supplied audit log path traverses a symlink")
    if lexical != configured_path:
        die("audit log path traverses a symlink")
    try:
        info = os.lstat(lexical)
    except OSError:
        die("audit log path is not a regular file")
    if stat.S_ISLNK(info.st_mode):
        die("audit log path is a symlink")
    if not stat.S_ISREG(info.st_mode):
        die("audit log path is not a regular file")

    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_only = getattr(os, "O_DIRECTORY", 0)
    non_blocking = getattr(os, "O_NONBLOCK", 0)
    if (
        not no_follow
        or not directory_only
        or not non_blocking
        or not AUDIT_OPEN_SUPPORTS_DIR_FD
    ):
        die("platform cannot safely read the configured audit log")
    close_exec = getattr(os, "O_CLOEXEC", 0)
    directory_flags = (
        os.O_RDONLY | close_exec | no_follow | directory_only
    )
    file_flags = os.O_RDONLY | close_exec | no_follow | non_blocking
    relative = os.path.relpath(lexical, root)
    components = relative.split(os.sep)
    directory_descriptor = None
    file_descriptor = None
    try:
        directory_descriptor = os.open(root, directory_flags)
        if not stat.S_ISDIR(os.fstat(directory_descriptor).st_mode):
            die("target directory is not a regular directory")
        for component in components[:-1]:
            next_descriptor = None
            try:
                next_descriptor = os.open(
                    component, directory_flags, dir_fd=directory_descriptor
                )
                if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                    die("audit log path has a non-directory component")
                os.close(directory_descriptor)
                directory_descriptor = next_descriptor
                next_descriptor = None
            finally:
                if next_descriptor is not None:
                    with contextlib.suppress(OSError):
                        os.close(next_descriptor)
        file_descriptor = os.open(
            components[-1], file_flags, dir_fd=directory_descriptor
        )
        handle = os.fdopen(file_descriptor, "rb")
        file_descriptor = None
        with handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode):
                die("audit log path is not a regular file")
            if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                die("audit log path changed during access")
            data = handle.read(SOURCE_BYTES_MAX + 1)
            finished = os.fstat(handle.fileno())
            opened_identity = (
                opened.st_dev,
                opened.st_ino,
                opened.st_size,
                opened.st_mtime_ns,
                opened.st_ctime_ns,
            )
            finished_identity = (
                finished.st_dev,
                finished.st_ino,
                finished.st_size,
                finished.st_mtime_ns,
                finished.st_ctime_ns,
            )
            current_directory_descriptor = None
            current_file_descriptor = None
            try:
                current_directory_descriptor = os.open(root, directory_flags)
                for component in components[:-1]:
                    next_descriptor = None
                    try:
                        next_descriptor = os.open(
                            component,
                            directory_flags,
                            dir_fd=current_directory_descriptor,
                        )
                        os.close(current_directory_descriptor)
                        current_directory_descriptor = next_descriptor
                        next_descriptor = None
                    finally:
                        if next_descriptor is not None:
                            with contextlib.suppress(OSError):
                                os.close(next_descriptor)
                current_file_descriptor = os.open(
                    components[-1],
                    file_flags,
                    dir_fd=current_directory_descriptor,
                )
                current_directory = os.fstat(current_directory_descriptor)
                current_file = os.fstat(current_file_descriptor)
            except OSError:
                die("audit log path changed during read")
            finally:
                if current_file_descriptor is not None:
                    with contextlib.suppress(OSError):
                        os.close(current_file_descriptor)
                if current_directory_descriptor is not None:
                    with contextlib.suppress(OSError):
                        os.close(current_directory_descriptor)
            if opened_identity != finished_identity or (
                len(data) <= SOURCE_BYTES_MAX and len(data) != finished.st_size
            ) or (
                (current_directory.st_dev, current_directory.st_ino)
                != (
                    os.fstat(directory_descriptor).st_dev,
                    os.fstat(directory_descriptor).st_ino,
                )
            ) or (
                finished_identity
                != (
                    current_file.st_dev,
                    current_file.st_ino,
                    current_file.st_size,
                    current_file.st_mtime_ns,
                    current_file.st_ctime_ns,
                )
            ):
                die("audit log path changed during read")
    except OSError:
        die("audit log path cannot be read")
    finally:
        if file_descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(file_descriptor)
        if directory_descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(directory_descriptor)
    if len(data) > SOURCE_BYTES_MAX:
        die(f"audit log path exceeds {SOURCE_BYTES_MAX}-byte cap")
    return relative.replace(os.sep, "/"), data


def plugin_root() -> str:
    return os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def die(msg: str, code: int = 2) -> None:
    print(f"hexctl: error: {msg}", file=sys.stderr)
    sys.exit(code)


def refuse_audit_renderer(message) -> None:
    """Emit one bounded ASCII renderer refusal, then return code 2.

    The renderer is executable input to this controller. Its declared errors and
    the diagnostic stream can both fail while a receipt is being refused, so this
    boundary cannot delegate formatting or the final exit status to either one.
    KeyboardInterrupt and GeneratorExit remain process-level interrupts.
    """
    prefix = b"hexctl: error: "
    fallback = "audit synopsis renderer validation failed"
    payload_bytes_max = AUDIT_RENDERER_DIAGNOSTIC_BYTES_MAX - len(prefix) - 1
    try:
        rendered = str(message)
        if not rendered or len(rendered) > AUDIT_RENDERER_DIAGNOSTIC_BYTES_MAX:
            escaped = fallback
        else:
            escaped = rendered.encode("unicode_escape").decode("ascii")
            if len(escaped) > payload_bytes_max:
                escaped = fallback
    except (Exception, SystemExit):
        escaped = fallback
    frame = prefix + escaped.encode("ascii") + b"\n"
    try:
        binary_stderr = getattr(sys.stderr, "buffer", None)
    except (Exception, SystemExit):
        binary_stderr = None
    try:
        if binary_stderr is None:
            sys.stderr.write(frame.decode("ascii"))
        else:
            remaining = frame
            while remaining:
                written = binary_stderr.write(remaining)
                if (
                    isinstance(written, bool)
                    or not isinstance(written, int)
                    or written <= 0
                    or written > len(remaining)
                ):
                    break
                remaining = remaining[written:]
            if not remaining:
                flush = getattr(binary_stderr, "flush", None)
                if callable(flush):
                    flush()
    except (Exception, SystemExit):
        pass
    raise SystemExit(2)


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def as_dict(value) -> dict:
    """A mapping, or an empty one.

    `d.get(key, {})` returns the stored value when the key exists, so a state holding
    `"integrate": null` defeats the default and the next `.get` raises. The load
    boundary rejects required containers; this remains defensive for optional leaves
    and isolated callers.
    """
    return value if isinstance(value, dict) else {}


def is_waiver(value) -> bool:
    """True when a `security_suite` receipt says the Pashov pair did not run.

    The first word has to be the prefix, not merely start with it: `startswith` alone
    read `waivedX` and `waived-ish` as waivers, which the rule beside `WAIVER_PREFIX`
    does not say. Both currently land on the same answer by another route, so the
    mismatch was invisible; it would stop being invisible the moment a message
    explained which branch it took.
    """
    if not isinstance(value, str):
        return False
    first = value.strip().lower().replace(":", " ").split()
    return bool(first) and first[0] == WAIVER_PREFIX


def solidity_round(state: dict) -> bool:
    """Whether this run's audit rounds are Solidity rounds.

    False means the round's mechanical part is the three bundled lints, so
    `audit-round` requires their exit statuses.

    Under `auto` the answer comes from the `security_suite` receipt: a waiver means no
    Solidity, a non-empty list of suite ids means Solidity. Anything else -- an empty
    list, a number, an object -- is not a suite that ran, so it is treated as a
    non-Solidity round and the lints are required. Demanding more evidence is the safe
    direction when the receipt cannot be read.

    A missing receipt reads as Solidity, because nothing can be inferred from it.
    `cmd_audit_round` refuses a missing receipt before ever asking this.

    Direct callers whose `config` or `receipts` is not an object read it as absent
    rather than raising. State-backed commands cannot reach this fallback because the
    load boundary rejects those wrong-kind containers first.
    """
    mode = as_dict(state.get("config")).get("solidity", "auto")
    if mode is True or mode is False:
        return mode
    receipts = as_dict(state.get("receipts"))
    if "security_suite" not in receipts:
        return True
    suite = receipts["security_suite"]
    if is_waiver(suite):
        return False
    return isinstance(suite, list) and bool(suite)


# ------------------------------------------------------------------ branches

SLUG_RE = re.compile(r"[^a-z0-9]+")
TASK_ISSUE_PATH_RE = re.compile(r".*/issues/([1-9][0-9]*)\Z")

# Conservative subset of git's refname rules: no whitespace, no traversal, no
# leading or trailing separator, nothing that needs quoting in a shell.
BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*[A-Za-z0-9]$")


def slug(text: str, limit: int = 48) -> str:
    return SLUG_RE.sub("-", text.lower()).strip("-")[:limit].strip("-")


def task_issue_number(value: str) -> str:
    parsed = None
    if isinstance(value, str) and not any(
        character.isspace() or ord(character) < 32 or ord(character) == 127
        for character in value
    ):
        try:
            parsed = urllib.parse.urlsplit(value)
            hostname = parsed.hostname
        except ValueError:
            parsed = None
            hostname = None
    else:
        hostname = None
    path = parsed.path if parsed is not None else ""
    match = TASK_ISSUE_PATH_RE.fullmatch(path)
    if (
        match is None
        or parsed is None
        or parsed.scheme not in ("http", "https")
        or hostname is None
    ):
        die(
            "--task-issue must be an absolute HTTP(S) URL with a path ending in "
            "/issues/<positive-number>"
        )
    return match.group(1)


def branch_name_ok(name: str) -> bool:
    """Whether one string satisfies the conservative refname subset above."""
    if not BRANCH_RE.match(name) or ".." in name or "//" in name:
        return False
    return not name.endswith(".lock")


def check_branch_name(name: str) -> None:
    if not branch_name_ok(name):
        die(f"'{name}' is not a usable branch name")


def run_branch_of(state: dict):
    """The run's integration branch, or None for a run started before 3.4."""
    return state.get("run_branch")


def integration_base_of(state: dict) -> str:
    """The named branch a completed run integrates into.

    Older runs may record the exact starting commit in ``state.base`` while
    retaining the named delivery branch in ``config.git.base``.  The commit is
    immutable starting-point evidence; it is not a remote branch name.
    """
    starting_base = state.get("base")
    if not isinstance(starting_base, str) or not starting_base:
        die("the recorded starting base must be a non-empty string")
    if not COMMIT_RE.fullmatch(starting_base):
        check_branch_name(starting_base)
        return starting_base

    configured = as_dict(as_dict(state.get("config")).get("git")).get("base")
    if not isinstance(configured, str) or not configured:
        die(
            "a run started from a commit needs config.git.base to name its "
            "integration branch"
        )
    if COMMIT_RE.fullmatch(configured):
        die("config.git.base must name an integration branch, not a commit")
    check_branch_name(configured)
    return configured


def step_branch_name(state: dict, step: dict) -> str:
    """Descriptive chained step branch: run slug, step number, step title.

    A sibling of the run branch rather than a child of it, because git cannot
    hold `fiat/x` and `fiat/x/step-1-y` as refs at the same time.
    """
    tail = slug(step["title"], 32) or "untitled"
    return f"{run_branch_of(state)}-step-{step['n']}-{tail}"


def step_pr_base(state: dict, step: dict) -> str:
    """A step stacks on the step below it; step 1 stacks on the run branch."""
    if step["n"] <= 1:
        return run_branch_of(state)
    return step_branch_name(state, state["steps"][step["n"] - 2])


def branch_plan(state: dict, step: dict) -> dict:
    """Branch to cut and pull request base for a step, when the run has a run
    branch. A pre-3.4 run gets nothing here and keeps its old freedom."""
    if not run_branch_of(state):
        return {}
    parent = step_pr_base(state, step)
    return {
        "run_branch": run_branch_of(state),
        "branch": step_branch_name(state, step),
        "branch_from": parent,
        "pr_base": parent,
        "merge_now": False,
    }


def expected_task_issue(state: dict):
    task_issue = state["receipts"].get("task_issue")
    if isinstance(task_issue, str):
        return task_issue
    if isinstance(task_issue, dict):
        return task_issue.get("url")
    return None


# ---------------------------------------------------------------- state io

def state_root(base_dir: str) -> str:
    return os.path.join(base_dir, STATE_DIR_NAME)


def state_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), STATE_FILE)


def ledger_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), LEDGER_FILE)


def run_pr_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), RUN_PR_FILE)


def require_state_container(value, path: str, expected_type: type):
    """Return one required state container or stop with a value-free fault."""
    if not isinstance(value, expected_type):
        kind = "object" if expected_type is dict else "array"
        die(f"state key '{path}' must be an {kind}", 1)
    return value


def _state_relation_fault(path: str, reason: str) -> None:
    """Refuse one malformed optional relation container without echoing values."""
    die(f"state version relations key '{path}' {reason}", 1)


def validate_version_relations_shape(value, path: str) -> dict:
    """Validate the closed additive v1 runbook-anchor receipt."""
    if not isinstance(value, dict):
        _state_relation_fault(path, "must be an object")
    if set(value) != VERSION_RELATION_KEYS:
        _state_relation_fault(path, "has an unsupported field set")
    if value.get("schema") != VERSION_RELATIONS_SCHEMA:
        _state_relation_fault(f"{path}.schema", "is not supported")
    for name in ("source_sha256", "anchor_commit"):
        candidate = value.get(name)
        valid = isinstance(candidate, str) and (
            re.fullmatch(r"[0-9a-f]{64}", candidate) is not None
            if name == "source_sha256"
            else COMMIT_RE.fullmatch(candidate) is not None
        )
        if not valid:
            _state_relation_fault(f"{path}.{name}", "is malformed")
    targets = value.get("targets")
    if not isinstance(targets, list) or not targets:
        _state_relation_fault(f"{path}.targets", "must be a non-empty array")
    if len(targets) > VERSION_RELATIONS_MAX:
        _state_relation_fault(f"{path}.targets", "exceeds its item cap")

    prior_skill = None
    seen_paths = set()
    for index, target in enumerate(targets):
        target_path = f"{path}.targets[{index}]"
        if not isinstance(target, dict) or set(target) != VERSION_RELATION_TARGET_KEYS:
            _state_relation_fault(target_path, "has an unsupported field set")
        skill = target.get("skill")
        ledger = target.get("ledger")
        if not isinstance(skill, str) or not VERSION_RELATION_SKILL_RE.fullmatch(skill):
            _state_relation_fault(f"{target_path}.skill", "is malformed")
        if not isinstance(ledger, str) or _version_relation_path_fault(ledger, skill):
            _state_relation_fault(f"{target_path}.ledger", "is malformed")
        if prior_skill is not None and skill <= prior_skill:
            _state_relation_fault(f"{path}.targets", "is not uniquely skill-sorted")
        if ledger in seen_paths:
            _state_relation_fault(f"{path}.targets", "repeats a ledger path")
        prior_skill = skill
        seen_paths.add(ledger)
        if target.get("relation") != VERSION_RELATION:
            _state_relation_fault(f"{target_path}.relation", "is not supported")

        counters = []
        for name in ("evolution", "generation", "epoch"):
            counter = target.get(name)
            if (
                not isinstance(counter, int)
                or isinstance(counter, bool)
                or counter < 0
                or counter > VERSION_RELATION_COUNTER_MAX
            ):
                _state_relation_fault(f"{target_path}.{name}", "is malformed")
            if name == "generation" and counter == VERSION_RELATION_COUNTER_MAX:
                _state_relation_fault(
                    f"{target_path}.generation",
                    "cannot be projected within its counter bound",
                )
            counters.append(counter)
        expected_label = f"{skill}-v{counters[0]}.{counters[1]}.{counters[2]}"
        if target.get("anchor_version") != expected_label:
            _state_relation_fault(f"{target_path}.anchor_version", "is inconsistent")
        expected_metadata = ".".join(str(counter) for counter in counters)
        if target.get("skill_metadata_version") != expected_metadata:
            _state_relation_fault(
                f"{target_path}.skill_metadata_version", "is inconsistent"
            )
        if target.get("frontier_status") not in ("open", "mature"):
            _state_relation_fault(f"{target_path}.frontier_status", "is malformed")
        revision = target.get("frontier_revision")
        try:
            revision_bytes = (
                revision.encode("utf-8") if isinstance(revision, str) else b""
            )
        except UnicodeEncodeError:
            revision_bytes = b""
        if (
            not isinstance(revision, str)
            or not revision_bytes
            or len(revision_bytes) > VERSION_RELATION_PATH_BYTES_MAX
            or _contains_nonprinting_character(revision)
        ):
            _state_relation_fault(f"{target_path}.frontier_revision", "is malformed")
        for name in (
            "frontier_sha256",
            "current_frontier_sha256",
            "next_job_sha256",
            "ledger_sha256",
            "skill_sha256",
        ):
            digest = target.get(name)
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                _state_relation_fault(f"{target_path}.{name}", "is malformed")
    return value


def _state_resolution_fault(path: str, reason: str) -> None:
    """Refuse one malformed optional resolution without echoing its value."""
    die(f"state version resolution key '{path}' {reason}", 1)


def validate_version_resolution_shape(value, path: str) -> dict:
    """Validate one closed append-only integrate-time resolution receipt."""
    if not isinstance(value, dict):
        _state_resolution_fault(path, "must be an object")
    if set(value) != VERSION_RESOLUTION_KEYS:
        _state_resolution_fault(path, "has an unsupported field set")
    if value.get("schema") != VERSION_RESOLUTION_SCHEMA:
        _state_resolution_fault(f"{path}.schema", "is not supported")
    for name in ("runbook_sha256", "relations_sha256"):
        digest = value.get(name)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            _state_resolution_fault(f"{path}.{name}", "is malformed")
    base_ref = value.get("base_ref")
    if (
        not isinstance(base_ref, str)
        or not BRANCH_RE.fullmatch(base_ref)
        or ".." in base_ref
        or "//" in base_ref
        or base_ref.endswith(".lock")
    ):
        _state_resolution_fault(f"{path}.base_ref", "is malformed")
    for name in ("base_commit", "head_commit"):
        commit_sha = value.get(name)
        if not isinstance(commit_sha, str) or COMMIT_RE.fullmatch(commit_sha) is None:
            _state_resolution_fault(f"{path}.{name}", "is malformed")
    timestamp = value.get("ts")
    try:
        parsed_timestamp = (
            datetime.datetime.fromisoformat(timestamp)
            if isinstance(timestamp, str)
            else None
        )
    except ValueError:
        parsed_timestamp = None
    if parsed_timestamp is None or parsed_timestamp.tzinfo is None:
        _state_resolution_fault(f"{path}.ts", "is malformed")

    targets = value.get("targets")
    if not isinstance(targets, list) or not targets:
        _state_resolution_fault(f"{path}.targets", "must be a non-empty array")
    if len(targets) > VERSION_RELATIONS_MAX:
        _state_resolution_fault(f"{path}.targets", "exceeds its item cap")
    prior_skill = None
    seen_paths = set()
    for index, target in enumerate(targets):
        target_path = f"{path}.targets[{index}]"
        if not isinstance(target, dict) or set(target) != VERSION_RESOLUTION_TARGET_KEYS:
            _state_resolution_fault(target_path, "has an unsupported field set")
        skill = target.get("skill")
        ledger = target.get("ledger")
        if not isinstance(skill, str) or VERSION_RELATION_SKILL_RE.fullmatch(skill) is None:
            _state_resolution_fault(f"{target_path}.skill", "is malformed")
        if not isinstance(ledger, str) or _version_relation_path_fault(ledger, skill):
            _state_resolution_fault(f"{target_path}.ledger", "is malformed")
        if prior_skill is not None and skill <= prior_skill:
            _state_resolution_fault(f"{path}.targets", "is not uniquely skill-sorted")
        if ledger in seen_paths:
            _state_resolution_fault(f"{path}.targets", "repeats a ledger path")
        prior_skill = skill
        seen_paths.add(ledger)
        if target.get("relation") != VERSION_RELATION:
            _state_resolution_fault(f"{target_path}.relation", "is not supported")
        labels = {}
        for name in ("anchor_version", "base_version", "resolved_version"):
            label = target.get(name)
            parts = _label_parts(label, skill) if isinstance(label, str) else None
            if parts is None or label != f"{skill}-v{parts[0]}.{parts[1]}.{parts[2]}":
                _state_resolution_fault(f"{target_path}.{name}", "is malformed")
            labels[name] = parts
        anchor, base, resolved = (
            labels["anchor_version"],
            labels["base_version"],
            labels["resolved_version"],
        )
        if (
            base[0] != anchor[0]
            or base[2] != anchor[2]
            or base[1] < anchor[1]
            or resolved != (base[0], base[1] + 1, base[2])
        ):
            _state_resolution_fault(f"{target_path}.resolved_version", "is inconsistent")
        if target.get("skill_metadata_version") != ".".join(
            str(part) for part in resolved
        ):
            _state_resolution_fault(
                f"{target_path}.skill_metadata_version", "is inconsistent"
            )
        for name in (
            "base_ledger_sha256",
            "head_ledger_sha256",
            "row_sha256",
            "skill_sha256",
        ):
            digest = target.get(name)
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                _state_resolution_fault(f"{target_path}.{name}", "is malformed")
    return value


def validate_version_resolution_history(value, path: str) -> list[dict]:
    if not isinstance(value, list):
        _state_resolution_fault(path, "must be an array")
    if len(value) > VERSION_RESOLUTIONS_MAX:
        _state_resolution_fault(path, "exceeds its item cap")
    for index, receipt in enumerate(value):
        validate_version_resolution_shape(receipt, f"{path}[{index}]")
    return value


def validate_state_shape(state) -> dict:
    """Validate the version-1 container spine in one deterministic order.

    Leaves heterogeneous receipt and field payloads to their existing semantic
    checks. This boundary establishes only the containers every reader traverses.
    """
    root = require_state_container(state, "$", dict)
    config = require_state_container(root.get("config"), "config", dict)
    for section in ("skills", "audit", "git"):
        require_state_container(
            config.get(section), f"config.{section}", dict
        )
    receipts = require_state_container(root.get("receipts"), "receipts", dict)
    runbook = receipts.get("runbook")
    if isinstance(runbook, dict) and "version_relations" in runbook:
        validate_version_relations_shape(
            runbook["version_relations"], "receipts.runbook.version_relations"
        )
    integrate = root.get("integrate")
    if isinstance(integrate, dict) and "version_resolutions" in integrate:
        validate_version_resolution_history(
            integrate["version_resolutions"], "integrate.version_resolutions"
        )
    terminal = receipts.get("integrate")
    if isinstance(terminal, dict) and "version_resolution" in terminal:
        validate_version_resolution_shape(
            terminal["version_resolution"], "receipts.integrate.version_resolution"
        )
    steps = require_state_container(root.get("steps"), "steps", list)

    for step_index, step in enumerate(steps):
        require_state_container(step, f"steps[{step_index}]", dict)

    for step_index, step in enumerate(steps):
        prefix = f"steps[{step_index}]"
        require_state_container(step.get("receipts"), f"{prefix}.receipts", dict)
        audit = require_state_container(step.get("audit"), f"{prefix}.audit", dict)
        rounds = require_state_container(
            audit.get("rounds"), f"{prefix}.audit.rounds", list
        )
        for round_index, round_entry in enumerate(rounds):
            require_state_container(
                round_entry,
                f"{prefix}.audit.rounds[{round_index}]",
                dict,
            )
    return root


def amendment_pending_path(base_dir: str, subject: str) -> str:
    try:
        filename = AMENDMENT_PENDING_FILES[subject]
    except KeyError:
        die(f"unknown amendment subject: {subject}", 1)
    return os.path.join(state_root(base_dir), filename)


def study_amendment_pending_path(base_dir: str) -> str:
    """Compatibility name for callers that know the version-1 study marker."""
    return amendment_pending_path(base_dir, "study")


def load_amendment_pending(base_dir: str, subject: str) -> dict | None:
    """Read one bounded, subject-labelled interrupted amendment record."""
    path = amendment_pending_path(base_dir, subject)
    if not os.path.exists(path):
        return None
    if os.path.islink(path) or not os.path.isfile(path):
        die(f"{subject} amendment pending record is not a regular file", 1)
    try:
        with open(path, "rb") as handle:
            raw = handle.read(65537)
    except OSError as exc:
        die(f"{subject} amendment pending record cannot be read: {exc}", 1)
    if len(raw) > 65536:
        die(f"{subject} amendment pending record exceeds 65536-byte cap", 1)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        die(f"{subject} amendment pending record is malformed", 1)
    if not isinstance(value, dict) or value.get("version") != 1:
        die(f"{subject} amendment pending record has an unsupported shape", 1)
    recorded_subject = value.get("subject")
    # Study markers written by fiat-v5.20.1 and earlier had no subject field.
    if recorded_subject is None and subject == "study":
        recorded_subject = "study"
    if recorded_subject != subject:
        die(
            f"{subject} amendment pending record names subject "
            f"{recorded_subject!r}",
            1,
        )
    if not isinstance(value.get("artifact"), str) or not value["artifact"]:
        die(f"{subject} amendment pending record has no artefact path", 1)
    before = value.get("state_before_sha256")
    if not isinstance(before, str) or not re.fullmatch(r"[0-9a-f]{64}", before):
        die(f"{subject} amendment pending record has an invalid state digest", 1)
    amendment = value.get("amendment")
    if not isinstance(amendment, dict):
        die(f"{subject} amendment pending record has no amendment object", 1)
    value["subject"] = subject
    return value


def load_study_amendment_pending(base_dir: str) -> dict | None:
    """Compatibility reader for the existing study-amendment tests."""
    return load_amendment_pending(base_dir, "study")


def pending_amendments(base_dir: str) -> dict[str, dict]:
    """Return the one pending subject, refusing an ambiguous collision."""
    found = {
        subject: pending
        for subject in AMENDMENT_PENDING_FILES
        if (pending := load_amendment_pending(base_dir, subject)) is not None
    }
    if len(found) > 1:
        subjects = ", ".join(sorted(found))
        die(
            "multiple amendment transactions are pending for subjects "
            f"{subjects}; restore exactly one recorded subject before recovery",
            1,
        )
    return found


def write_amendment_pending(base_dir: str, subject: str, value: dict) -> None:
    """Publish a durable marker before replacing one receipted artefact."""
    root = state_root(base_dir)
    path = amendment_pending_path(base_dir, subject)
    value = {**value, "subject": subject}
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{subject}-amendment-pending-", dir=root
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as exc:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        die(
            f"{subject} amendment pending record could not be written: {exc}",
            1,
        )


def write_study_amendment_pending(base_dir: str, value: dict) -> None:
    """Compatibility writer; new study markers carry their subject."""
    write_amendment_pending(base_dir, "study", value)


def clear_amendment_pending(base_dir: str, subject: str) -> None:
    """Remove the write-ahead marker only after the receipt commit is durable."""
    path = amendment_pending_path(base_dir, subject)
    try:
        os.unlink(path)
        directory = os.open(state_root(base_dir), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except FileNotFoundError:
        return
    except OSError as exc:
        die(
            f"{subject} amendment pending record could not be cleared: {exc}",
            1,
        )


def clear_study_amendment_pending(base_dir: str) -> None:
    """Compatibility clearer for the existing study transition."""
    clear_amendment_pending(base_dir, "study")


def version_resolution_pending_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), VERSION_RESOLUTION_PENDING_FILE)


def load_version_resolution_pending(base_dir: str) -> dict | None:
    """Read one closed, subject-labelled interrupted resolution marker."""
    path = version_resolution_pending_path(base_dir)
    try:
        file_state = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError:
        die("version resolution pending record cannot be inspected", 1)
    if not stat.S_ISREG(file_state.st_mode) or stat.S_ISLNK(file_state.st_mode):
        die("version resolution pending record is not a regular file", 1)
    if file_state.st_size > VERSION_RESOLUTION_PENDING_BYTES_MAX:
        die(
            "version resolution pending record exceeds "
            f"{VERSION_RESOLUTION_PENDING_BYTES_MAX}-byte cap",
            1,
        )
    try:
        with open(path, "rb") as handle:
            raw = handle.read(VERSION_RESOLUTION_PENDING_BYTES_MAX + 1)
    except OSError:
        die("version resolution pending record cannot be read", 1)
    if len(raw) > VERSION_RESOLUTION_PENDING_BYTES_MAX:
        die(
            "version resolution pending record exceeds "
            f"{VERSION_RESOLUTION_PENDING_BYTES_MAX}-byte cap",
            1,
        )
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        die("version resolution pending record is malformed", 1)
    expected_keys = {
        "schema",
        "subject",
        "state_before_sha256",
        "state_after_sha256",
        "ledger_head",
        "receipt_sha256",
        "receipt",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        die("version resolution pending record has an unsupported shape", 1)
    if (
        value.get("schema") != VERSION_RESOLUTION_PENDING_SCHEMA
        or value.get("subject") != "version-resolution"
    ):
        die("version resolution pending record has an unsupported subject", 1)
    for name in (
        "state_before_sha256",
        "state_after_sha256",
        "ledger_head",
        "receipt_sha256",
    ):
        digest = value.get(name)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            die("version resolution pending record has an invalid digest", 1)
    receipt = validate_version_resolution_shape(
        value.get("receipt"), "pending.version_resolution.receipt"
    )
    if hashlib.sha256(canonical(receipt).encode()).hexdigest() != value["receipt_sha256"]:
        die("version resolution pending record receipt digest does not match", 1)
    return value


def write_version_resolution_pending(base_dir: str, value: dict) -> None:
    """Publish the resolution marker before its ledger/state write windows."""
    try:
        raw = (
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        die("version resolution pending record has an unsupported shape", 1)
    if len(raw) > VERSION_RESOLUTION_PENDING_BYTES_MAX:
        die(
            "version resolution pending record exceeds "
            f"{VERSION_RESOLUTION_PENDING_BYTES_MAX}-byte cap",
            1,
        )
    root = state_root(base_dir)
    path = version_resolution_pending_path(base_dir)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".version-resolution-pending-", dir=root
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        die("version resolution pending record could not be written", 1)


def clear_version_resolution_pending(base_dir: str) -> None:
    path = version_resolution_pending_path(base_dir)
    try:
        os.unlink(path)
        directory = os.open(state_root(base_dir), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except FileNotFoundError:
        return
    except OSError:
        die("version resolution pending record could not be cleared", 1)


def make_version_resolution_write_durable(
    base_dir: str, path: str, label: str, *, replaced: bool = False
) -> None:
    """Fsync one transaction write before crossing its next recovery window."""
    try:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if replaced:
            directory = os.open(state_root(base_dir), os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    except OSError:
        die(f"version resolution {label} could not be made durable", 1)


def load_state(
    base_dir: str,
    *,
    allow_pending_amendment: bool = False,
    allow_pending_resolution: bool = False,
) -> dict:
    path = state_path(base_dir)
    if not os.path.exists(path):
        # A checkout that started a run has no state of its own: the run's state
        # is in its worktree. Say which one and how to reach it, rather than
        # reporting the absence and letting somebody start a second run over the
        # top of the first.
        live = read_breadcrumbs(base_dir)
        if live:
            named = "\n".join(f"  hexctl --dir {entry} next" for entry in live)
            die(
                f"no state here; this checkout's {'run works' if len(live) == 1 else 'runs work'} "
                f"in {'its own worktree' if len(live) == 1 else 'their own worktrees'}:\n{named}"
            )
        recorded = raw_breadcrumbs(base_dir)
        if recorded:
            named = ", ".join(recorded)
            die(
                f"this checkout recorded a run worktree that is no longer "
                f"there: {named}. Restore it or clear the breadcrumb at "
                f"{breadcrumb_path(base_dir)}; a second run is not started for you"
            )
        die(f"no state at {path}; run `hexctl init --topic ...` first")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except (ValueError, OSError) as exc:
        die(f"state file unreadable at {path}: {exc}", 1)
    state = validate_state_shape(state)
    amendments = pending_amendments(base_dir)
    resolution = load_version_resolution_pending(base_dir)
    if amendments and resolution is not None:
        die(
            "amendment and version-resolution transactions are both pending; "
            "inspect both markers without removing either",
            1,
        )
    if amendments and not allow_pending_amendment:
        subject = next(iter(amendments))
        die(
            f"{subject} amendment transaction is pending; rerun `hexctl "
            f"amend {subject} --artifact <canonical-{subject}>` to recover "
            "before continuing"
        )
    if resolution is not None and not allow_pending_resolution:
        die(
            "version-resolution transaction is pending; rerun `hexctl done "
            "resolve-versions` to recover before continuing"
        )
    return state


MUTATING = frozenset(
    {
        "cmd_init",
        "cmd_observe",
        "cmd_record",
        "cmd_config",
        "cmd_amend_study",
        "cmd_amend_runbook",
        "cmd_done",
        "cmd_audit_round",
        "cmd_halt",
        "cmd_resume",
        "cmd_reset",
        "cmd_checkpoint_export",
    }
)
"""Commands that write. `status`, `next` and `verify` only read, and blocking
them would stop a second agent from finding out why it is blocked."""


def lock_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), "lock")


def read_holder(descriptor: int) -> dict:
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        data = os.read(descriptor, 4096)
        return json.loads(data.decode("utf-8")) if data else {}
    except (UnicodeDecodeError, ValueError, OSError):
        return {}


def holder_is_alive(pid) -> bool:
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def read_live_holder(descriptor: int) -> dict:
    """Wait briefly for a new owner to replace metadata left by a crash."""
    holder = {}
    for _ in range(50):
        holder = read_holder(descriptor)
        if holder_is_alive(holder.get("pid")):
            break
        time.sleep(0.002)
    return holder


@contextlib.contextmanager
def held_lock(base_dir: str, command: str):
    """Hold the run for the length of one mutating command.

    The ledger is a read-modify-write: an entry takes the previous entry's
    hash as its parent. Two commands interleaving there produce two entries
    claiming the same parent, and `verify` reports the chain as broken
    afterwards. This turns that into a refusal beforehand.

    The kernel owns the exclusion. It releases the lock when a process exits,
    including after a crash, so stale metadata never needs to be unlinked and
    two contenders cannot both reclaim it. The file remains as an ignored
    place to publish holder details for a refused writer.
    """
    root = state_root(base_dir)
    if not os.path.isdir(root):
        # Only `init` legitimately runs without a state directory, and it
        # creates one. Anything else is about to fail with a better message
        # than a lock could give, so do not litter the directory to say so.
        if command != "cmd_init":
            yield
            return
        os.makedirs(root, exist_ok=True)

    path = lock_path(base_dir)
    try:
        fd = os.open(
            path,
            os.O_CREAT
            | os.O_RDWR
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except OSError:
        die("run lock is not a safe regular file", 1)
    lock_stat = os.fstat(fd)
    if not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_nlink != 1:
        os.close(fd)
        die("run lock is not a safe regular file", 1)
    acquired = False

    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError:
            holder = read_live_holder(fd)
            die(
                "another hexctl is holding this run: pid {pid} running "
                "`{cmd}` since {since}.\n"
                "Two agents in one run's worktree share one run and one "
                "ledger. Each run gets its own tree at init, so start a "
                "separate run with `hexctl --dir <checkout> init --topic "
                "...`, or wait for this one.".format(
                    pid=holder.get("pid", "unknown"),
                    cmd=holder.get("command", "unknown"),
                    since=holder.get("ts", "unknown"),
                ),
                1,
            )
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(
            fd,
            json.dumps(
                {"pid": os.getpid(), "command": command, "ts": now()}
            ).encode()
            + b"\n",
        )
        os.fsync(fd)
        yield
    finally:
        if acquired:
            try:
                os.ftruncate(fd, 0)
                os.fsync(fd)
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        else:
            os.close(fd)


def save_state(base_dir: str, state: dict) -> None:
    path = state_path(base_dir)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def state_fingerprint(state: dict) -> str:
    return hashlib.sha256(canonical(state).encode()).hexdigest()


def append_ledger(base_dir: str, event: str, data: dict, state_hash: str) -> None:
    path = ledger_path(base_dir)
    prev = "genesis"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        if lines:
            try:
                prev = json.loads(lines[-1])["hash"]
            except (ValueError, KeyError, TypeError):
                die("ledger corrupt: last entry unreadable; run `hexctl verify`", 1)
    entry = {
        "ts": now(),
        "event": event,
        "data": data,
        "prev": prev,
        "state": state_hash,
    }
    entry["hash"] = hashlib.sha256(canonical(entry).encode()).hexdigest()
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def commit(base_dir: str, state: dict, event: str, data: dict) -> None:
    append_ledger(base_dir, event, data, state_fingerprint(state))
    save_state(base_dir, state)


# ------------------------------------------------------------- step helpers

def current_step(state: dict) -> dict:
    n = state.get("current_step")
    if n is None:
        die("no step is open")
    for step in state["steps"]:
        if step["n"] == n:
            return step
    die(f"state corrupt: current_step={n} not found; run `hexctl verify`", 1)


def last_local_commit(step: dict):
    """The last commit whose local signature and trailers were receipted."""
    for round_entry in reversed(as_dict(step.get("audit")).get("rounds") or []):
        verified = as_dict(round_entry).get("verified_commits") or []
        if verified:
            return verified[-1]
    implement = as_dict(as_dict(step.get("receipts")).get("implement"))
    verified = implement.get("verified_commits") or []
    if verified:
        return verified[-1]
    return implement.get("commit")


def require_global_phase(state: dict, phase: str) -> None:
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state["phase"] != phase:
        die(f"out of order: expected phase '{state['phase']}', got '{phase}'")


def amendment_block(state: dict) -> dict | None:
    """Return the latest un-repaired broken verdict for the current step."""
    if state.get("phase") != "steps" or state.get("current_step") is None:
        return None
    step_number = state["current_step"]

    runbook_receipt = as_dict(as_dict(state.get("receipts")).get("runbook"))
    runbook_amendments = runbook_receipt.get("amendments")
    if runbook_amendments is not None and not isinstance(runbook_amendments, list):
        die("runbook receipt amendments history must be an array", 1)
    for amendment in reversed(runbook_amendments or []):
        verdicts = as_dict(amendment).get("step_verdicts")
        if not isinstance(verdicts, list):
            continue
        for verdict in verdicts:
            item = as_dict(verdict)
            if item.get("step") != step_number:
                continue
            if item.get("entry") == "holds" and item.get("exit") == "holds":
                break
            return {
                "subject": "runbook",
                "step": step_number,
                "entry": item.get("entry"),
                "exit": item.get("exit"),
                "amendment_sha256": amendment.get("amendment_sha256"),
                "runbook_sha256": amendment.get("new_sha256"),
            }
        else:
            continue
        break

    study_receipt = as_dict(as_dict(state.get("receipts")).get("study"))
    study_amendments = study_receipt.get("amendments")
    if study_amendments is not None and not isinstance(study_amendments, list):
        die("study receipt amendments history must be an array", 1)
    broken = None
    for amendment in reversed(study_amendments or []):
        verdicts = as_dict(amendment).get("step_verdicts")
        if not isinstance(verdicts, list):
            continue
        for verdict in verdicts:
            item = as_dict(verdict)
            if item.get("step") != step_number:
                continue
            if item.get("entry") == "holds" and item.get("exit") == "holds":
                return None
            broken = {
                "subject": "study",
                "step": step_number,
                "entry": item.get("entry"),
                "exit": item.get("exit"),
                "amendment_sha256": amendment.get("amendment_sha256"),
                "study_sha256": amendment.get("new_sha256"),
            }
            break
        if broken is not None:
            break
    if broken is None:
        return None

    current_study = study_receipt.get("sha256")
    for amendment in reversed(runbook_amendments or []):
        item = as_dict(amendment)
        if item.get("study_sha256") != current_study:
            continue
        if step_number not in (item.get("steps_touched") or []):
            continue
        replacements = item.get("replacement_fields")
        if not isinstance(replacements, list) or not replacements:
            continue
        verdicts = item.get("step_verdicts")
        if not isinstance(verdicts, list):
            continue
        current_verdict = next(
            (
                as_dict(verdict)
                for verdict in verdicts
                if as_dict(verdict).get("step") == step_number
            ),
            None,
        )
        if (
            current_verdict is not None
            and current_verdict.get("entry") == "holds"
            and current_verdict.get("exit") == "holds"
        ):
            return None
        break
    return broken


def require_no_amendment_block(state: dict) -> None:
    blocked = amendment_block(state)
    if blocked is None:
        return
    die(
        "{subject} amendment blocks step {step}: entry {entry}, exit {exit}; "
        "inspect the amendment, halt the run, or use a separately specified "
        "runbook-repair transition".format(**blocked)
    )


def require_step_phase(state: dict, phase: str) -> dict:
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state["phase"] != "steps":
        die(f"out of order: run is in phase '{state['phase']}', not working steps")
    require_no_amendment_block(state)
    step = current_step(state)
    if step["phase"] != phase:
        die(
            f"out of order: step {step['n']} is in phase '{step['phase']}', "
            f"got 'done {phase}'"
        )
    return step


def configured_audit_log(state: dict) -> str:
    """The one file this run's rounds append to, as its own config records it.

    Read through here rather than off the dict, so the Warden packet, `next` and
    the two receipts all refuse the same way when a run has no path to write to.
    """
    log = as_dict(as_dict(state.get("config")).get("audit")).get("log_path")
    if not isinstance(log, str) or not log:
        die(
            "config audit.log_path is missing or is not a path; a round cannot "
            "say where it wrote without one"
        )
    return log


def same_audit_log(declared: str, configured: str) -> bool:
    """Whether two spellings name one record.

    `audit/rounds/x.md` and `./audit/rounds/x.md` are the same file, and a round
    turned away over a leading `./` would be turned away for punctuation.
    """
    def flatten(value: str) -> str:
        return os.path.normpath(value.replace("\\", "/"))

    return flatten(declared) == flatten(configured)


def check_declared_audit_log(state: dict, declared: str, label: str) -> str:
    """Hold a declared log to the one the caller was told to write.

    `--log` was a free string stored verbatim while the Warden packet named
    `config audit.log_path`, so a receipt could record a file the round never
    opened and nothing noticed. The declaration is checked here and the
    configured path is what gets recorded, so the two cannot drift apart by
    spelling either.
    """
    configured = configured_audit_log(state)
    if not same_audit_log(declared, configured):
        die(
            f"--log names '{declared}', but {label} writes '{configured}' "
            "(config audit.log_path); a receipt naming a file nothing opened "
            "is worse than a receipt naming none"
        )
    return configured


def max_rounds_of(state: dict) -> int:
    raw = state["config"]["audit"]["max_rounds"]
    try:
        val = int(raw)
    except (TypeError, ValueError):
        die(f"config audit.max_rounds must be an integer >= 1 (got {raw!r})")
    if val < 1:
        die(f"config audit.max_rounds must be >= 1 (got {val})")
    return val


def parse_value(raw: str):
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


# ------------------------------------------------------------------ commands

def cmd_init(args) -> None:
    origin_root = os.path.realpath(args.dir)
    root = state_root(args.dir)
    if os.path.exists(state_path(args.dir)):
        die(f"state already exists at {root}; resume with `hexctl next`")
    waiver = None
    if args.controller_currency_waiver is not None:
        waiver = args.controller_currency_waiver.strip()
        if not waiver:
            die(
                "--controller-currency-waiver needs a reason; an empty one "
                "records nothing"
            )
    prefix = DEFAULT_CONFIG["git"]["run_branch_prefix"]
    issue_number = (
        task_issue_number(args.task_issue) if args.task_issue is not None else None
    )
    topic_slug = slug(args.topic) or "run"
    automatic_tail = (
        topic_slug
        if issue_number is None
        else slug(f"{issue_number}-{topic_slug}", 48)
    )
    run_branch = args.run_branch or f"{prefix}{automatic_tail}"
    check_branch_name(run_branch)
    if issue_number is not None:
        required_prefix = f"{prefix}{issue_number}-"
        if not run_branch.startswith(required_prefix):
            die(
                f"--run-branch for task issue {issue_number} must start with "
                f"'{required_prefix}'"
            )
    if run_branch == args.base:
        die("--run-branch must differ from --base; the run needs its own branch")
    frontier = None
    if args.frontier:
        ledger = args.frontier if os.path.isabs(args.frontier) else \
            os.path.join(args.dir, args.frontier)
        if not os.path.isfile(ledger):
            die(f"--frontier {args.frontier} is not a file; name the target "
                f"skill's EVOLUTION.md")
        with open(ledger, encoding="utf-8") as fh:
            text = fh.read()
        if ledger_field(text, "Current version") is None:
            die(f"--frontier {args.frontier} states no `Current version`; it "
                f"does not look like a governed ledger")
        frontier = {
            "ledger": os.path.relpath(ledger, args.dir),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "rows": len(ledger_rows(text)),
            "version_at_init": ledger_field(text, "Current version"),
        }

    # Everything refusable happens before the first mutation. The path is derived
    # and validated, and the branch is checked for an existing tree, while a
    # refusal still costs nothing: no worktree, no state, no ledger, no
    # breadcrumb.
    repo_root = repository_root(args.dir)
    candidate = run_worktree_path(args.dir, run_branch)
    if os.path.exists(state_path(candidate)):
        die(
            f"this run already has a worktree at {candidate}; "
            f"resume with `hexctl --dir {candidate} next`"
        )
    worktree = check_worktree_path(repo_root, candidate)
    refuse_checked_out_branch(args.dir, run_branch)

    # The currency observation is the last pre-mutation check because it is
    # the only one that may wait on the network: every cheaper refusal has
    # already had its chance. A proven-behind controller stops the run here,
    # while a refusal still costs nothing; anything the observation could not
    # prove proceeds as `unknown` with the nulls recorded rather than guessed.
    currency = observe_controller_currency()
    if currency["verdict"] == "behind" and waiver is None:
        die(
            "controller currency: this controller's recorded pin "
            f"{currency['pin']} differs from the observed upstream head "
            f"{currency['observed_head']}. Either re-pin the plugin through "
            "this host's own installer (references/plugin-currency.md), or "
            "rerun init with --controller-currency-waiver '<reason>' to "
            "proceed with the gap recorded.",
            1,
        )
    if currency["verdict"] == "unknown":
        print(
            "hexctl: warning: controller currency is unknown "
            f"({currency['warning']}); the run starts anyway and its receipt "
            "records the nulls rather than a verdict.",
            file=sys.stderr,
        )
    provenance = {**currency, "waiver": waiver}

    home = os.path.dirname(worktree)
    os.makedirs(home, exist_ok=True)
    # Self-ignoring, the same trick the state directory uses. Without it the
    # worktree home shows as untracked in the origin checkout, which both breaks
    # the promise that a run leaves that checkout's `git status` alone and blocks
    # the next run, because preflight refuses a dirty tree. Doing it here rather
    # than leaning on the target repository's own rules means the promise holds
    # whichever repository the run was started in.
    home_gitignore = os.path.join(home, ".gitignore")
    if not os.path.exists(home_gitignore):
        with open(home_gitignore, "w", encoding="utf-8") as fh:
            fh.write("*\n")
    bounded_git(
        args.dir,
        ["worktree", "add", "-b", run_branch, worktree, args.base],
        refusal=(
            f"could not create the run worktree at {worktree} "
            f"for '{run_branch}' off '{args.base}'"
        ),
    )
    try:
        starting_commit = _native_relation_worktree_start(worktree, run_branch)
    except SystemExit:
        remove_run_worktree(args.dir, worktree)
        raise

    # From here the run's home is the worktree, so a failure has something to
    # undo. Anything that goes wrong while writing state takes the tree with it,
    # because a tree with no state is not a run anybody can resume.
    root = state_root(worktree)
    try:
        os.makedirs(root, exist_ok=True)
        # Self-ignoring: git never sees the state directory even in repos whose
        # .gitignore was not touched. Nested .gitignore with `*` covers it.
        with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("*\n")
    except OSError:
        remove_run_worktree(args.dir, worktree)
        die(f"could not write the run's state into {root}")

    receipts = {"controller_currency": provenance}
    if args.task_issue is not None:
        receipts["task_issue"] = args.task_issue

    state = {
        "version": 1,
        "controller": "hexctl",
        "topic": args.topic,
        "base": args.base,
        "run_branch": run_branch,
        "created_at": now(),
        "phase": "study",
        "current_step": None,
        "steps": [],
        "receipts": receipts,
        "config": json.loads(json.dumps(DEFAULT_CONFIG)),
        "halted": None,
        "frontier": frontier,
    }
    state["config"]["audit"]["log_path"] = run_audit_log_path(run_branch)
    state["config"]["git"]["worktree"] = worktree
    state["config"]["git"]["origin"] = origin_root
    init_data = {
        "topic": args.topic,
        "base": args.base,
        "run_branch": run_branch,
        "controller_currency": provenance,
        "starting_commit": starting_commit,
    }
    if args.task_issue is not None:
        init_data["task_issue"] = args.task_issue
    try:
        commit(worktree, state, "init", init_data)
        write_breadcrumbs(args.dir, worktree)
    except OSError:
        remove_run_worktree(args.dir, worktree)
        die(f"could not record the run at {root}")
    print(
        f"initialised {root} (topic: {args.topic}); "
        f"run branch {run_branch} off {args.base}"
    )
    print(f"run worktree {worktree}")
    print(f"work in it: hexctl --dir {worktree} next")
    if frontier is not None:
        print(
            f"frontier run: {frontier['ledger']} at {frontier['version_at_init']}, "
            f"{frontier['rows']} row(s). `done integrate` refuses until it "
            f"carries exactly one new valid row."
        )
    stale = stale_controller(args.dir)
    if stale is not None:
        running, checked_in, path = stale
        print(
            f"hexctl: warning: this controller is {running}, and {path} in the "
            f"target repository is {checked_in}. The run will use the older "
            f"one, so a receipt it cannot record is a gap in this run's "
            f"evidence rather than a rule that does not exist. Follow "
            f"references/plugin-currency.md: update the plugin through this "
            f"host's own installer, refresh, and re-resolve the paths, or "
            f"record a controller_version receipt saying why that could not "
            f"happen.",
            file=sys.stderr,
        )


def ledger_version(evolution_md: str) -> str | None:
    """The `Current version` a skill's EVOLUTION.md declares."""
    try:
        with open(evolution_md, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("- Current version:"):
                    return line.split(":", 1)[1].strip().strip("`") or None
    except OSError:
        return None
    return None


LEDGER_ROW = re.compile(
    r"^\| `(?P<version>[^`]+)` \| (?P<axis>baseline|evolution|generation|epoch) "
    r"\| `(?P<revision>[^`]+)` \| `(?P<digest>[0-9a-f]{64})` "
    r"\| (?P<evidence>.*?) \| (?P<change>.*?) \|$"
)
LEDGER_ROW_COMPACT = re.compile(
    r"^- `(?P<version>[^`]+)` \| (?P<axis>baseline|evolution|generation|epoch) "
    r"\| `(?P<revision>[^`]+)` \| `(?P<digest>[0-9a-f]{64})` "
    r"\| (?P<evidence>.*?) \| (?P<change>.*?)$"
)
"""One history row, in either spelling tests/test_evolution_contract.py
accepts, so the gate and the suite cannot disagree about what a row is.
Reading only the table shape counted a compact-list ledger as empty and
refused a real completed frontier (skills#443)."""

LEDGER_AXES = ("baseline", "evolution", "generation", "epoch")


def ledger_rows(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        match = LEDGER_ROW.fullmatch(line) or LEDGER_ROW_COMPACT.fullmatch(line)
        if match:
            rows.append(match.groupdict())
    return rows


def ledger_field(text: str, name: str) -> str | None:
    match = re.search(rf"(?m)^- {re.escape(name)}: (.+)$", text)
    return match.group(1).strip().strip("`") if match else None


def ledger_frontier_digest(text: str) -> str | None:
    """SHA-256 over the four-field canonical line, including its newline."""
    fields = [ledger_field(text, name) for name in
              ("Frontier status", "Frontier revision", "Current frontier",
               "Next Fiat job")]
    if any(f is None for f in fields):
        return None
    return hashlib.sha256(("|".join(fields) + "\n").encode("utf-8")).hexdigest()


def _label_parts(label: str, skill: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(
        rf"{re.escape(skill)}-v([0-9]+)\.([0-9]+)\.([0-9]+)", label
    )
    if match is None:
        return None
    groups = match.groups()
    if any(len(group) > VERSION_RELATION_COUNTER_DIGITS_MAX for group in groups):
        return None
    try:
        return tuple(int(group) for group in groups)
    except ValueError:
        # Python bounds decimal-to-integer conversion. Treat a label beyond that
        # bound as malformed input instead of letting its exception escape with
        # interpreter-specific diagnostic text.
        return None


def _contains_nonprinting_character(value: str) -> bool:
    """Cover control and format characters at a runbook/state boundary."""
    return any(not character.isprintable() for character in value)


def _unfenced_markdown_lines(text: str) -> list[str]:
    """Return physical Markdown lines that are not inside fenced code.

    Version evidence has to come from the live ledger, not from a quoted
    specimen that happens to use the same row or header spelling.  Keep the
    physical line endings so history-prefix receipts still bind exact bytes.
    """
    visible = []
    open_mark = None
    open_length = None
    for physical in text.splitlines(keepends=True):
        line = physical.rstrip("\r\n")
        fence = VERSION_RELATION_FENCE_RE.match(line)
        if fence is not None:
            sequence = fence.group("mark")
            mark = sequence[0]
            info = fence.group("info").strip()
            if open_mark is None:
                open_mark, open_length = mark, len(sequence)
            elif mark == open_mark and len(sequence) >= open_length and not info:
                open_mark, open_length = None, None
            continue
        if open_mark is None:
            visible.append(physical)
    return visible


def _version_relation_path_fault(value: str, skill: str) -> str | None:
    """Return the lexical fault for one governed ledger path, if any."""
    if not isinstance(value, str):
        return "relation path is not text"
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        encoded = b""
    parts = value.split("/")
    if (
        not encoded
        or len(encoded) > VERSION_RELATION_PATH_BYTES_MAX
        or value.startswith(("/", "\\"))
        or re.match(r"^[A-Za-z]:", value)
        or "\\" in value
        or any(part in ("", ".", "..") for part in parts)
        or _contains_nonprinting_character(value)
    ):
        return "relation path is not a safe repository-relative path"
    if len(parts) < 2 or parts[-1] != "EVOLUTION.md":
        return "relation path must name an EVOLUTION.md file"
    if parts[-2] != skill:
        return "relation target id must match the skill directory before EVOLUTION.md"
    return None


def _first_unfenced_step(lines: list[str]) -> int | None:
    open_mark = None
    open_length = None
    for index, physical in enumerate(lines):
        line = physical.rstrip("\r\n")
        fence = VERSION_RELATION_FENCE_RE.match(line)
        if fence is not None:
            sequence = fence.group("mark")
            mark = sequence[0]
            info = fence.group("info").strip()
            if open_mark is None:
                open_mark, open_length = mark, len(sequence)
                continue
            if mark == open_mark and len(sequence) >= open_length and not info:
                open_mark, open_length = None, None
            continue
        if open_mark is None and STEP_HEADING_RE.fullmatch(line):
            return index
    return None


def parse_version_relation_source(text: str) -> dict | None:
    """Extract one closed Protasis relation block without opening its paths."""
    lines = text.splitlines(keepends=True)
    blocks = []
    open_mark = None
    open_length = None
    relation_open = None
    for index, physical in enumerate(lines):
        line = physical.rstrip("\r\n")
        fence = VERSION_RELATION_FENCE_RE.match(line)
        if fence is None:
            continue
        sequence = fence.group("mark")
        mark = sequence[0]
        info = fence.group("info").strip()
        if open_mark is None:
            open_mark, open_length = mark, len(sequence)
            words = info.split()
            relation_open = (
                (index, info == VERSION_RELATIONS_INFO)
                if words and words[0] == VERSION_RELATIONS_INFO
                else None
            )
            continue
        if mark == open_mark and len(sequence) >= open_length and not info:
            if relation_open is not None:
                opening, exact_info = relation_open
                blocks.append((opening, index, exact_info, True))
            open_mark, open_length, relation_open = None, None, None
    if relation_open is not None:
        opening, exact_info = relation_open
        blocks.append((opening, len(lines) - 1, exact_info, False))
    if not blocks:
        return None
    if len(blocks) != 1:
        die("runbook carries more than one version-relations block")

    opening, closing, exact_info, closed = blocks[0]
    if not exact_info:
        die("version-relations fence must carry only that exact info string")
    if not closed:
        die("version-relations block is not closed")
    first_step = _first_unfenced_step(lines)
    if first_step is not None and opening >= first_step:
        die("version-relations block must occur before Step 1")

    rows = [line.rstrip("\r\n") for line in lines[opening + 1 : closing]]
    if not rows:
        die("version-relations block carries no row")
    if len(rows) > VERSION_RELATIONS_MAX:
        die(f"version-relations block exceeds {VERSION_RELATIONS_MAX} rows")

    targets = []
    seen_skills = set()
    seen_paths = set()
    for row in rows:
        if not row.strip():
            die("version-relations row must not be blank")
        if _contains_nonprinting_character(row):
            die("version-relations row contains a control character")
        fields = [field.strip() for field in row.split("|")]
        if len(fields) != 3 or any(not field for field in fields):
            die(
                "version-relations row must carry three non-empty fields "
                "(skill id | EVOLUTION.md path | relation)"
            )
        skill, ledger, relation = fields
        if not VERSION_RELATION_SKILL_RE.fullmatch(skill):
            die("version relation target id is not kebab-case")
        if skill in seen_skills:
            die("version relation target id appears more than once")
        if ledger in seen_paths:
            die("version relation path appears more than once")
        fault = _version_relation_path_fault(ledger, skill)
        if fault:
            die(fault)
        if relation != VERSION_RELATION:
            die(f"unknown version relation; expected {VERSION_RELATION!r}")
        seen_skills.add(skill)
        seen_paths.add(ledger)
        targets.append({"skill": skill, "ledger": ledger, "relation": relation})

    outside = "".join(lines[:opening] + lines[closing + 1 :])
    for skill in sorted(seen_skills):
        token = re.compile(
            rf"(?<![A-Za-z0-9-]){re.escape(skill)}-v"
            rf"[0-9]+\.[0-9]+\.[0-9]+(?![A-Za-z0-9-])"
        )
        if token.search(outside):
            die(
                "declared target has a concrete version token outside the "
                "version-relations block"
            )
    source = "".join(lines[opening : closing + 1]).encode("utf-8")
    return {
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "targets": targets,
    }


def _native_relation_environment() -> dict[str, str]:
    """A Git environment that cannot substitute for the repository relation."""
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def _native_relation_git(
    base_dir: str, argv: list[str], refusal: str
) -> bytes:
    """Read native local objects without inherited Git substitution state."""
    return bounded_tool(
        base_dir,
        "git",
        ["--no-replace-objects", *argv],
        refusal,
        environment=_native_relation_environment(),
    )


def _native_ancestry_status(
    base_dir: str, candidate: str, descendant: str
) -> int | None:
    """Return Git's native ancestry answer, or ``None`` when it gave none.

    This is topology admission only. It deliberately reads no signature,
    attribution, or GitHub evidence; ``done merge-step`` owns those checks over
    the exact current range. ``bounded_probe`` keeps startup, time, and output
    failures inside the same unknown result instead of exposing child output or
    turning an unavailable answer into a non-ancestor claim.
    """
    candidate = require_full_sha(candidate, "waiting step recorded head")
    descendant = require_full_sha(descendant, "waiting step observed tip")
    status, _output, failure = bounded_probe(
        base_dir,
        "git",
        [
            "--no-replace-objects",
            "merge-base",
            "--is-ancestor",
            candidate,
            descendant,
        ],
        environment=_native_relation_environment(),
    )
    if failure is not None or status not in (0, 1):
        return None
    return status


def _native_relation_commit(base_dir: str, ref: str, label: str) -> str:
    raw = _native_relation_git(
        base_dir,
        ["rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
        f"{label} does not resolve to a native commit",
    )
    try:
        lines = [line for line in raw.decode("ascii").splitlines() if line]
    except UnicodeDecodeError:
        lines = []
    if len(lines) != 1 or not COMMIT_RE.fullmatch(lines[0]):
        die(f"{label} did not resolve to one full native commit SHA")
    return lines[0]


def _native_relation_parents(
    base_dir: str, commit_sha: str, label: str
) -> list[str]:
    """Read exact commit parents without replacement refs or inherited Git state."""
    commit_sha = require_full_sha(commit_sha, label)
    raw = _native_relation_git(
        base_dir,
        ["show", "-s", "--no-show-signature", "--format=%P", commit_sha],
        f"{label} parents cannot be read",
    )
    try:
        parents = raw.decode("ascii").strip().split()
    except UnicodeDecodeError:
        parents = []
    if any(COMMIT_RE.fullmatch(parent) is None for parent in parents):
        die(f"{label} returned a malformed parent SHA")
    return parents


def _native_relation_merge_base(
    base_dir: str, left: str, right: str
) -> str:
    """Resolve one native common ancestor for a stored composition proof."""
    left = require_full_sha(left, "version resolution product head")
    right = require_full_sha(right, "version resolution base head")
    raw = _native_relation_git(
        base_dir,
        ["merge-base", "--all", left, right],
        "version resolution product/base merge base cannot be read",
    )
    try:
        candidates = [line for line in raw.decode("ascii").splitlines() if line]
    except UnicodeDecodeError:
        candidates = []
    if len(candidates) != 1 or COMMIT_RE.fullmatch(candidates[0]) is None:
        die("version resolution product/base merge base is ambiguous or malformed")
    return candidates[0]


def _native_diff_paths(
    base_dir: str,
    before: str,
    after: str,
    subject: str,
    refusal: str,
) -> list[str]:
    """One exact native tree delta, named by the caller that reads it.

    Replacement objects, rename detection and submodule shortcuts all let a
    delta describe something other than the two trees named, so every caller
    that turns a delta into evidence reads it through here. The subject is the
    caller's, because a refusal that named the wrong reader is what the #710
    acceptance fixture pins against.
    """
    raw = _native_relation_git(
        base_dir,
        [
            "diff",
            "--no-renames",
            "--ignore-submodules=none",
            "--name-only",
            "-z",
            f"{before}..{after}",
            "--",
        ],
        refusal,
    )
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        die(f"{subject} is not UTF-8")
    paths = [path for path in decoded.split("\0") if path]
    unique = sorted(set(paths))
    if len(unique) > INTEGRATION_PATHS_MAX:
        die(f"{subject} exceeds {INTEGRATION_PATHS_MAX} paths")
    if len(unique) != len(paths):
        die(f"{subject} contains duplicate paths")
    root = os.path.realpath(base_dir)
    for index, path in enumerate(unique):
        if (
            not isinstance(path, str)
            or not path
            or os.path.isabs(path)
            or path in (".", "..")
            or ".." in path.split("/")
            or any(ord(character) < 32 or ord(character) == 127 for character in path)
        ):
            die(f"{subject} contains an unsafe path at index {index}")
        candidate = os.path.realpath(os.path.join(root, path))
        try:
            inside = os.path.commonpath((root, candidate)) == root
        except ValueError:
            inside = False
        if not inside:
            die(f"{subject} escapes the repository at index {index}")
    return unique


def _native_relation_diff_paths(
    base_dir: str, before: str, after: str
) -> list[str]:
    """Read one exact native tree delta for target-path revalidation."""
    before = require_full_sha(before, "version resolution product head")
    after = require_full_sha(after, "version resolution sync head")
    return _native_diff_paths(
        base_dir,
        before,
        after,
        "version resolution target path delta",
        "version resolution target path delta cannot be read",
    )

def _native_relation_repository_identity(base_dir: str) -> tuple[str, str]:
    """Identify the worktree Git directory and its exact common repository."""
    raw = _native_relation_git(
        base_dir,
        [
            "rev-parse",
            "--path-format=absolute",
            "--absolute-git-dir",
            "--git-common-dir",
        ],
        "version relation repository identity cannot be read",
    )
    try:
        lines = raw.decode("utf-8").splitlines()
        encoded = [line.encode("utf-8") for line in lines]
    except (UnicodeDecodeError, UnicodeEncodeError):
        lines = []
        encoded = []
    if (
        len(lines) != 2
        or any(not os.path.isabs(line) for line in lines)
        or any(not value or len(value) > 4096 for value in encoded)
    ):
        die("version relation repository identity is malformed")
    return tuple(lines)


def _native_relation_worktree_start(base_dir: str, branch: str) -> str:
    """Capture the exact commit checked out when ``init`` made the worktree."""
    first = _native_relation_commit(base_dir, "HEAD", "run starting commit")
    symbolic = _native_relation_git(
        base_dir,
        ["symbolic-ref", "--quiet", "HEAD"],
        "run starting branch cannot be read",
    )
    current = _native_relation_git(
        base_dir,
        ["show-ref", "--verify", "--hash", f"refs/heads/{branch}"],
        "run starting commit cannot be read",
    )
    final = _native_relation_commit(base_dir, "HEAD", "run starting commit")
    try:
        symbolic_name = symbolic.decode("utf-8").strip()
        current_sha = current.decode("ascii").strip()
    except (UnicodeDecodeError, UnicodeEncodeError):
        symbolic_name = ""
        current_sha = ""
    if symbolic_name != f"refs/heads/{branch}":
        die("run worktree did not retain its named starting branch")
    if (
        first != final
        or not COMMIT_RE.fullmatch(current_sha)
        or current_sha != first
    ):
        die("run starting commit changed while init recorded it")
    return first


def _relation_init_starting_commit(base_dir: str, state: dict) -> str:
    """Read the exact run start from the intact hash-chained init receipt."""
    path = ledger_path(base_dir)
    if not os.path.exists(path):
        die("version relation init evidence is missing", 1)
    prev = "genesis"
    first_entry = None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                entry = json.loads(line)
                expected = hashlib.sha256(
                    canonical(
                        {
                            "ts": entry["ts"],
                            "event": entry["event"],
                            "data": entry["data"],
                            "prev": entry["prev"],
                            "state": entry["state"],
                        }
                    ).encode()
                ).hexdigest()
                if entry["prev"] != prev or entry["hash"] != expected:
                    die(
                        f"version relation controller ledger is not intact at "
                        f"line {line_number}",
                        1,
                    )
                if first_entry is None:
                    first_entry = entry
                prev = entry["hash"]
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError):
        die("version relation controller ledger is malformed", 1)
    data = as_dict(as_dict(first_entry).get("data"))
    starting_commit = data.get("starting_commit")
    if (
        as_dict(first_entry).get("event") != "init"
        or data.get("base") != state.get("base")
        or data.get("run_branch") != run_branch_of(state)
        or not isinstance(starting_commit, str)
        or not COMMIT_RE.fullmatch(starting_commit)
    ):
        die("version relation init starting commit is missing or malformed", 1)
    return starting_commit


def _require_native_relation_history(base_dir: str) -> None:
    """Refuse local object and ancestry substitutions before a branch point."""
    if "GIT_GRAFT_FILE" in os.environ:
        die("version relation starting history is rewritten by a graft")
    local_substitutions = (
        (
            "info/grafts",
            "graft",
            "version relation starting history is rewritten by a graft",
        ),
        (
            "objects/info/alternates",
            "alternate object store",
            "version relation repository uses an alternate object store",
        ),
    )
    for git_path, label, populated_refusal in local_substitutions:
        raw = _native_relation_git(
            base_dir,
            ["rev-parse", "--path-format=absolute", "--git-path", git_path],
            f"version relation {label} state cannot be located",
        )
        try:
            lines = raw.decode("utf-8").splitlines()
            encoded_path = lines[0].encode("utf-8") if len(lines) == 1 else b""
        except (UnicodeDecodeError, UnicodeEncodeError):
            lines = []
            encoded_path = b""
        if (
            len(lines) != 1
            or not os.path.isabs(lines[0])
            or not encoded_path
            or len(encoded_path) > 4096
        ):
            die(f"version relation {label} path is malformed")
        try:
            candidate = os.lstat(lines[0])
        except FileNotFoundError:
            continue
        except (OSError, ValueError):
            die(f"version relation {label} state cannot be read")
        if not stat.S_ISREG(candidate.st_mode) or candidate.st_size:
            die(populated_refusal)

    shallow = _native_relation_git(
        base_dir,
        ["rev-parse", "--is-shallow-repository"],
        "version relation shallow state cannot be read",
    )
    try:
        shallow_state = shallow.decode("ascii").strip()
    except UnicodeDecodeError:
        shallow_state = ""
    if shallow_state == "true":
        die("version relation starting history is shallow")
    if shallow_state != "false":
        die("version relation shallow state is malformed")


def relation_anchor_commit(base_dir: str, state: dict) -> str:
    """The immutable branch point the run started from, using native local refs."""
    init_start = _relation_init_starting_commit(base_dir, state)
    repository = _native_relation_repository_identity(base_dir)
    _require_native_relation_history(base_dir)
    starting = state.get("base")
    if isinstance(starting, str) and COMMIT_RE.fullmatch(starting):
        anchor = _native_relation_commit(
            base_dir, starting, "version relation starting commit"
        )
        _require_native_relation_history(base_dir)
        if _native_relation_repository_identity(base_dir) != repository:
            die("version relation repository changed while reading the starting commit")
        if anchor != init_start:
            die("version relation starting commit does not match the init starting commit")
        return anchor
    run_branch = run_branch_of(state)
    if not isinstance(run_branch, str) or not run_branch:
        die("version relations require the run's integration branch")
    base_branch = integration_base_of(state)
    run_head = _native_relation_commit(
        base_dir, run_branch, "version relation run branch"
    )
    base_head = _native_relation_commit(
        base_dir, base_branch, "version relation base branch"
    )
    raw = _native_relation_git(
        base_dir,
        ["merge-base", "--all", run_head, base_head],
        "version relation starting commit cannot be derived",
    )
    try:
        candidates = [line for line in raw.decode("ascii").splitlines() if line]
    except UnicodeDecodeError:
        candidates = []
    if len(candidates) != 1 or not COMMIT_RE.fullmatch(candidates[0]):
        die("version relation starting commit is ambiguous or malformed")
    final_run = _native_relation_commit(
        base_dir, run_branch, "version relation run branch"
    )
    final_base = _native_relation_commit(
        base_dir, base_branch, "version relation base branch"
    )
    if (run_head, base_head) != (final_run, final_base):
        die("version relation refs changed while deriving the starting commit")
    _require_native_relation_history(base_dir)
    if _native_relation_repository_identity(base_dir) != repository:
        die("version relation repository changed while deriving the starting commit")
    if candidates[0] != init_start:
        die("version relation branch point does not match the init starting commit")
    return candidates[0]


def read_commit_blob(
    base_dir: str, commit_sha: str, relative: str, label: str
) -> tuple[str, bytes]:
    """Read one bounded regular Git blob at an exact commit without a worktree."""
    raw = _native_relation_git(
        base_dir,
        ["ls-tree", "-z", commit_sha, "--", relative],
        f"{label} object cannot be inspected",
    )
    entries = [entry for entry in raw.split(b"\0") if entry]
    if not entries:
        die(f"{label} object is missing at the anchor commit")
    if len(entries) != 1 or b"\t" not in entries[0]:
        die(f"{label} object identity is ambiguous or malformed")
    header, raw_path = entries[0].split(b"\t", 1)
    fields = header.split()
    try:
        returned_path = raw_path.decode("utf-8")
    except UnicodeDecodeError:
        returned_path = ""
    if len(fields) != 3 or returned_path != relative:
        die(f"{label} object identity is ambiguous or malformed")
    try:
        mode, kind, object_sha = [field.decode("ascii") for field in fields]
    except UnicodeDecodeError:
        mode, kind, object_sha = "", "", ""
    if (
        mode not in ("100644", "100755")
        or kind != "blob"
        or not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", object_sha)
    ):
        die(f"{label} object is not a regular blob")
    size_raw = _native_relation_git(
        base_dir,
        ["cat-file", "-s", object_sha],
        f"{label} object size cannot be read",
    )
    try:
        size_text = size_raw.decode("ascii").strip()
        size = int(size_text) if re.fullmatch(r"\d+", size_text) else -1
    except (UnicodeDecodeError, ValueError):
        size = -1
    if size < 0:
        die(f"{label} object size is malformed")
    if size > SOURCE_BYTES_MAX:
        die(f"{label} object exceeds {SOURCE_BYTES_MAX}-byte cap")
    data = _native_relation_git(
        base_dir,
        ["cat-file", "blob", object_sha],
        f"{label} object cannot be read",
    )
    if len(data) != size:
        die(f"{label} object size changed during the bounded read")
    return object_sha, data


def _ledger_field_bytes(text: str, name: str, label: str) -> tuple[str, bytes]:
    prefix = f"- {name}: "
    values = [
        line[len(prefix) :]
        for physical in _unfenced_markdown_lines(text)
        if (line := physical.rstrip("\r\n")).startswith(prefix)
    ]
    if len(values) != 1 or not values[0]:
        die(f"{label} has a missing or ambiguous {name} field")
    return values[0].strip().strip("`"), values[0].encode("utf-8")


def _frontmatter_plain_key(
    line: str, indent: int, unsupported: str
) -> str | None:
    """Read one key from Fiat's closed block-mapping frontmatter subset."""
    prefix = " " * indent
    if not line.startswith(prefix):
        return None
    tail = line[indent:]
    if not tail or tail[0].isspace() or tail.startswith("#"):
        return None
    match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:", tail)
    if match is None:
        die(unsupported)
    return match.group(1)


def _skill_frontmatter_identity(text: str, skill: str) -> str:
    """Read one unambiguous name and numeric version from frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        die("version relation target skill frontmatter is missing")
    try:
        closing = lines.index("---", 1)
    except ValueError:
        die("version relation target skill frontmatter is not closed")
    frontmatter = lines[1:closing]
    if any("\t" in line for line in frontmatter):
        die("version relation target skill frontmatter uses unsupported key syntax")

    top_level = [
        (index, key)
        for index, line in enumerate(frontmatter)
        if (
            key := _frontmatter_plain_key(
                line,
                0,
                "version relation target skill frontmatter name or metadata "
                "identity is ambiguous",
            )
        ) is not None
    ]
    names = [(index, key) for index, key in top_level if key == "name"]
    if len(names) != 1:
        die("version relation target skill frontmatter name does not match")
    name_index = names[0][0]
    name = re.fullmatch(
        r"name:\s*([a-z0-9]+(?:-[a-z0-9]+)*)\s*",
        frontmatter[name_index],
    )
    if name is None or name.group(1) != skill:
        die("version relation target skill frontmatter name does not match")
    next_top = next(
        (index for index, _ in top_level if index > name_index),
        len(frontmatter),
    )
    if any(
        line.strip() and not line.lstrip().startswith("#")
        for line in frontmatter[name_index + 1 : next_top]
    ):
        die("version relation target skill frontmatter name does not match")

    metadata = [
        index
        for index, key in top_level
        if key == "metadata"
    ]
    if len(metadata) != 1:
        die(
            "version relation target skill frontmatter metadata version "
            "is missing or ambiguous"
        )
    if frontmatter[metadata[0]] != "metadata:":
        die(
            "version relation target skill frontmatter metadata version "
            "is missing or ambiguous"
        )
    metadata_end = next(
        (index for index, _ in top_level if index > metadata[0]),
        len(frontmatter),
    )
    metadata_body = frontmatter[metadata[0] + 1 : metadata_end]
    metadata_keys = [
        (index, key)
        for index, line in enumerate(metadata_body)
        if (
            key := _frontmatter_plain_key(
                line,
                2,
                "version relation target skill frontmatter metadata version "
                "is missing or ambiguous",
            )
        ) is not None
    ]
    versions = [(index, key) for index, key in metadata_keys if key == "version"]
    if len(versions) != 1:
        die(
            "version relation target skill frontmatter metadata version "
            "is missing or ambiguous"
        )
    version_index = versions[0][0]
    version = re.fullmatch(
        r'  version: "([0-9]+\.[0-9]+\.[0-9]+)"',
        metadata_body[version_index],
    )
    if version is None:
        die(
            "version relation target skill frontmatter metadata version "
            "is missing or ambiguous"
        )
    return version.group(1)


def capture_version_relation_target(
    base_dir: str, anchor_commit: str, declaration: dict
) -> dict:
    """Build one content-bounded anchor from two exact Git blobs."""
    skill = declaration["skill"]
    ledger_path = declaration["ledger"]
    _, ledger_bytes = read_commit_blob(
        base_dir, anchor_commit, ledger_path, "version relation target ledger"
    )
    try:
        ledger_text = ledger_bytes.decode("utf-8")
    except UnicodeDecodeError:
        die("version relation target ledger is not UTF-8 text")
    skill_path = ledger_path.rsplit("/", 1)[0] + "/SKILL.md"
    _, skill_bytes = read_commit_blob(
        base_dir, anchor_commit, skill_path, "version relation target skill"
    )
    try:
        skill_text = skill_bytes.decode("utf-8")
    except UnicodeDecodeError:
        die("version relation target skill is not UTF-8 text")

    current, _ = _ledger_field_bytes(
        ledger_text, "Current version", "version relation target ledger"
    )
    status, _ = _ledger_field_bytes(
        ledger_text, "Frontier status", "version relation target ledger"
    )
    revision, _ = _ledger_field_bytes(
        ledger_text, "Frontier revision", "version relation target ledger"
    )
    frontier, frontier_raw = _ledger_field_bytes(
        ledger_text, "Current frontier", "version relation target ledger"
    )
    next_job, next_job_raw = _ledger_field_bytes(
        ledger_text, "Next Fiat job", "version relation target ledger"
    )
    parts = _label_parts(current, skill)
    if parts is None or current != f"{skill}-v{parts[0]}.{parts[1]}.{parts[2]}":
        die("version relation target ledger has a malformed current label")
    if parts[1] == VERSION_RELATION_COUNTER_MAX:
        die(
            "version relation target generation cannot be projected within "
            "its counter bound"
        )
    if status not in ("open", "mature"):
        die("version relation target ledger has a malformed frontier status")
    if status == "mature" and next_job != "None -- mature":
        die("version relation target ledger has an inconsistent mature frontier")
    if status == "open" and next_job == "None -- mature":
        die("version relation target ledger has an inconsistent open frontier")
    frontier_digest = hashlib.sha256(
        f"{status}|{revision}|{frontier}|{next_job}\n".encode("utf-8")
    ).hexdigest()
    rows = ledger_rows(ledger_text)
    if (
        not rows
        or rows[-1]["version"] != current
        or rows[-1]["revision"] != revision
        or rows[-1]["digest"] != frontier_digest
    ):
        die("version relation target ledger history does not match its header")

    metadata = _skill_frontmatter_identity(skill_text, skill)
    expected_metadata = ".".join(str(part) for part in parts)
    if metadata != expected_metadata:
        die(
            "version relation target skill frontmatter metadata version "
            "does not match the ledger"
        )
    return {
        "skill": skill,
        "ledger": ledger_path,
        "relation": declaration["relation"],
        "anchor_version": current,
        "evolution": parts[0],
        "generation": parts[1],
        "epoch": parts[2],
        "frontier_status": status,
        "frontier_revision": revision,
        "frontier_sha256": frontier_digest,
        "current_frontier_sha256": hashlib.sha256(frontier_raw).hexdigest(),
        "next_job_sha256": hashlib.sha256(next_job_raw).hexdigest(),
        "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "skill_sha256": hashlib.sha256(skill_bytes).hexdigest(),
        "skill_metadata_version": metadata,
    }


def capture_version_relations(
    base_dir: str, source: dict, anchor_commit: str
) -> dict:
    targets = [
        capture_version_relation_target(base_dir, anchor_commit, declaration)
        for declaration in source["targets"]
    ]
    receipt = {
        "schema": VERSION_RELATIONS_SCHEMA,
        "source_sha256": source["source_sha256"],
        "anchor_commit": anchor_commit,
        "targets": sorted(targets, key=lambda target: target["skill"]),
    }
    validate_version_relations_shape(receipt, "captured.version_relations")
    return receipt


def version_relations_packet(receipt: dict, resolution: dict | None = None) -> dict:
    """Label an anchor and its provisional arithmetic without reserving it."""
    targets = []
    for target in receipt["targets"]:
        targets.append(
            {
                **target,
                "projection": (
                    f"{target['skill']}-v{target['evolution']}."
                    f"{target['generation'] + 1}.{target['epoch']}"
                ),
            }
        )
    return {
        "schema": receipt["schema"],
        "status": "resolved" if resolution is not None else "anchor",
        "resolution": resolution,
        "source_sha256": receipt["source_sha256"],
        "anchor_commit": receipt["anchor_commit"],
        "targets": targets,
    }


def _ledger_history_records(text: str, skill: str, label: str) -> list[dict]:
    """Parse and validate every governed history row, retaining exact bytes."""
    visible = _unfenced_markdown_lines(text)
    headings = [
        index
        for index, physical in enumerate(visible)
        if physical.rstrip("\r\n") == "## History"
    ]
    if not headings:
        die(f"{label} has no History section")
    if len(headings) != 1:
        die(f"{label} has an ambiguous History section")
    rows = []
    for physical in visible[headings[0] + 1 :]:
        line = physical.rstrip("\r\n")
        if re.match(r"^ {0,3}#{1,2}(?:[ \t]+|$)", line):
            break
        match = LEDGER_ROW.fullmatch(line) or LEDGER_ROW_COMPACT.fullmatch(line)
        if match is None:
            if line.startswith("| `") or line.startswith("- `"):
                die(f"{label} carries a malformed history row")
            continue
        row = match.groupdict()
        parts = _label_parts(row["version"], skill)
        if parts is None or row["version"] != (
            f"{skill}-v{parts[0]}.{parts[1]}.{parts[2]}"
        ):
            die(f"{label} carries a malformed history label")
        row["parts"] = parts
        row["raw"] = physical
        rows.append(row)
    if not rows:
        die(f"{label} carries no governed history row")
    if rows[0]["axis"] != "baseline":
        die(f"{label} history does not begin with a baseline row")
    seen_versions = set()
    for index, row in enumerate(rows):
        if row["version"] in seen_versions:
            die(f"{label} history repeats a version")
        seen_versions.add(row["version"])
        if index == 0:
            continue
        previous = rows[index - 1]
        deltas = tuple(
            row["parts"][part] - previous["parts"][part]
            for part in range(3)
        )
        expected_axis = {0: "evolution", 1: "generation", 2: "epoch"}
        changed = [part for part, delta in enumerate(deltas) if delta != 0]
        if (
            len(changed) != 1
            or deltas[changed[0]] != 1
            or row["axis"] != expected_axis[changed[0]]
            or row["axis"] == "baseline"
        ):
            die(f"{label} history does not follow the version-axis arithmetic")
        if row["axis"] == "generation" and (
            row["revision"] != previous["revision"]
            or row["digest"] != previous["digest"]
        ):
            die(f"{label} generation history changes the held frontier")
        if row["axis"] == "evolution" and row["digest"] == previous["digest"]:
            die(f"{label} evolution history does not change the held frontier")
        if (
            row["axis"] == "epoch"
            and row["digest"] != previous["digest"]
            and "reopen" not in (row["evidence"] + row["change"]).lower()
        ):
            die(f"{label} epoch history changes the frontier without reopening it")
    return rows


def _version_target_snapshot(
    base_dir: str, commit_sha: str, target: dict, label: str
) -> dict:
    """Read one exact ledger and sibling skill blob from a native commit."""
    skill = target["skill"]
    ledger_path = target["ledger"]
    ledger_object, ledger_bytes = read_commit_blob(
        base_dir, commit_sha, ledger_path, f"{label} ledger"
    )
    skill_path = ledger_path.rsplit("/", 1)[0] + "/SKILL.md"
    skill_object, skill_bytes = read_commit_blob(
        base_dir, commit_sha, skill_path, f"{label} skill"
    )
    try:
        ledger_text = ledger_bytes.decode("utf-8")
        skill_text = skill_bytes.decode("utf-8")
    except UnicodeDecodeError:
        die(f"{label} version evidence is not UTF-8 text")
    current, _ = _ledger_field_bytes(ledger_text, "Current version", label)
    status, _ = _ledger_field_bytes(ledger_text, "Frontier status", label)
    revision, _ = _ledger_field_bytes(ledger_text, "Frontier revision", label)
    frontier, frontier_raw = _ledger_field_bytes(
        ledger_text, "Current frontier", label
    )
    next_job, next_job_raw = _ledger_field_bytes(ledger_text, "Next Fiat job", label)
    parts = _label_parts(current, skill)
    if parts is None or current != f"{skill}-v{parts[0]}.{parts[1]}.{parts[2]}":
        die(f"{label} has a malformed current version")
    if status not in ("open", "mature"):
        die(f"{label} has a malformed frontier status")
    if (status == "mature") != (next_job == "None -- mature"):
        die(f"{label} has an inconsistent frontier status and next job")
    frontier_sha256 = hashlib.sha256(
        f"{status}|{revision}|{frontier}|{next_job}\n".encode("utf-8")
    ).hexdigest()
    rows = _ledger_history_records(ledger_text, skill, label)
    if (
        rows[-1]["version"] != current
        or rows[-1]["revision"] != revision
        or rows[-1]["digest"] != frontier_sha256
    ):
        die(f"{label} header does not match its final history row")
    metadata = _skill_frontmatter_identity(skill_text, skill)
    if metadata != ".".join(str(part) for part in parts):
        die(f"{label} skill metadata does not match its ledger")
    return {
        "skill": skill,
        "ledger": ledger_path,
        "skill_path": skill_path,
        "current": current,
        "parts": parts,
        "status": status,
        "revision": revision,
        "frontier_sha256": frontier_sha256,
        "current_frontier_sha256": hashlib.sha256(frontier_raw).hexdigest(),
        "next_job_sha256": hashlib.sha256(next_job_raw).hexdigest(),
        "rows": rows,
        "ledger_object": ledger_object,
        "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "skill_object": skill_object,
        "skill_sha256": hashlib.sha256(skill_bytes).hexdigest(),
        "metadata": metadata,
    }


def _require_anchor_snapshot(snapshot: dict, anchor: dict) -> None:
    expected = {
        "current": anchor["anchor_version"],
        "parts": (
            anchor["evolution"],
            anchor["generation"],
            anchor["epoch"],
        ),
        "status": anchor["frontier_status"],
        "revision": anchor["frontier_revision"],
        "frontier_sha256": anchor["frontier_sha256"],
        "current_frontier_sha256": anchor["current_frontier_sha256"],
        "next_job_sha256": anchor["next_job_sha256"],
        "ledger_sha256": anchor["ledger_sha256"],
        "skill_sha256": anchor["skill_sha256"],
        "metadata": anchor["skill_metadata_version"],
    }
    if any(snapshot[name] != value for name, value in expected.items()):
        die("version relation anchor evidence no longer matches its exact objects")


def _require_history_prefix(
    prefix: list[dict], history: list[dict], label: str
) -> None:
    if len(history) < len(prefix):
        die(f"{label} history is shorter than its required prefix")
    if any(
        expected["raw"] != actual["raw"]
        for expected, actual in zip(prefix, history)
    ):
        die(f"{label} history rewrites its required prefix")


def version_compatibility_fault(anchor: dict, snapshot: dict) -> str | None:
    """Name the first non-generation anchor field that drifted."""
    comparisons = (
        ("evolution", anchor["evolution"], snapshot["parts"][0]),
        ("epoch", anchor["epoch"], snapshot["parts"][2]),
        ("frontier_status", anchor["frontier_status"], snapshot["status"]),
        ("frontier_revision", anchor["frontier_revision"], snapshot["revision"]),
        ("frontier_sha256", anchor["frontier_sha256"], snapshot["frontier_sha256"]),
        (
            "current_frontier_sha256",
            anchor["current_frontier_sha256"],
            snapshot["current_frontier_sha256"],
        ),
        ("next_job_sha256", anchor["next_job_sha256"], snapshot["next_job_sha256"]),
    )
    return next(
        (name for name, expected, actual in comparisons if expected != actual),
        None,
    )


def resolve_version_relation_target(
    base_dir: str,
    anchor_commit: str,
    base_commit: str,
    head_commit: str,
    anchor: dict,
) -> dict:
    """Resolve and prove one target against exact base and candidate objects."""
    anchor_snapshot = _version_target_snapshot(
        base_dir, anchor_commit, anchor, "version relation anchor"
    )
    _require_anchor_snapshot(anchor_snapshot, anchor)
    base_snapshot = _version_target_snapshot(
        base_dir, base_commit, anchor, "version resolution base"
    )
    head_snapshot = _version_target_snapshot(
        base_dir, head_commit, anchor, "version resolution candidate"
    )
    _require_history_prefix(
        anchor_snapshot["rows"], base_snapshot["rows"], "version resolution base"
    )
    compatibility_fault = version_compatibility_fault(anchor, base_snapshot)
    if compatibility_fault:
        die(
            "version resolution base has incompatible drift in "
            f"{compatibility_fault}"
        )
    if base_snapshot["parts"][1] >= VERSION_RELATION_COUNTER_MAX:
        die("version resolution base generation has no representable successor")
    if base_snapshot["parts"][1] < anchor["generation"]:
        die("version resolution base generation predates the anchor")
    for row in base_snapshot["rows"][len(anchor_snapshot["rows"]) :]:
        if (
            row["axis"] != "generation"
            or row["revision"] != anchor["frontier_revision"]
            or row["digest"] != anchor["frontier_sha256"]
        ):
            die("version resolution base carries incompatible history drift")

    _require_history_prefix(
        base_snapshot["rows"], head_snapshot["rows"], "version resolution candidate"
    )
    if len(head_snapshot["rows"]) != len(base_snapshot["rows"]) + 1:
        die("version resolution candidate must add exactly one target history row")
    resolved_parts = (
        base_snapshot["parts"][0],
        base_snapshot["parts"][1] + 1,
        base_snapshot["parts"][2],
    )
    resolved_version = (
        f"{anchor['skill']}-v{resolved_parts[0]}."
        f"{resolved_parts[1]}.{resolved_parts[2]}"
    )
    final_row = head_snapshot["rows"][-1]
    if (
        head_snapshot["current"] != resolved_version
        or head_snapshot["parts"] != resolved_parts
        or head_snapshot["metadata"] != ".".join(str(part) for part in resolved_parts)
        or final_row["version"] != resolved_version
        or final_row["axis"] != "generation"
        or final_row["revision"] != anchor["frontier_revision"]
        or final_row["digest"] != anchor["frontier_sha256"]
    ):
        die("version resolution candidate row or skill metadata does not match")
    compatibility_fault = version_compatibility_fault(anchor, head_snapshot)
    if compatibility_fault:
        die(
            "version resolution candidate changes anchored field "
            f"{compatibility_fault}"
        )
    return {
        "skill": anchor["skill"],
        "ledger": anchor["ledger"],
        "relation": anchor["relation"],
        "anchor_version": anchor["anchor_version"],
        "base_version": base_snapshot["current"],
        "resolved_version": resolved_version,
        "base_ledger_sha256": base_snapshot["ledger_sha256"],
        "head_ledger_sha256": head_snapshot["ledger_sha256"],
        "row_sha256": hashlib.sha256(final_row["raw"].encode("utf-8")).hexdigest(),
        "skill_sha256": head_snapshot["skill_sha256"],
        "skill_metadata_version": head_snapshot["metadata"],
    }


def final_product_head(state: dict) -> str:
    if not state.get("steps"):
        die("version resolution requires at least one completed step")
    final_step = state["steps"][-1]["n"]
    merge_records = as_dict(as_dict(state.get("integrate")).get("merges"))
    return require_full_sha(
        as_dict(merge_records.get(str(final_step))).get("merge_commit"),
        "final recorded product head",
    )


def _require_resolution_sync(
    base_dir: str,
    state: dict,
    sync: dict,
    product_head: str,
    base_commit: str,
    head_commit: str,
    relations: dict,
) -> None:
    """Recheck the active signed composition and its target-path coverage."""
    if set(sync) != RESOLUTION_SYNC_KEYS:
        die("active version-resolution sync has an unsupported field set")
    if (
        sync.get("commit") != head_commit
        or sync.get("base") != integration_base_of(state)
        or sync.get("starting_base") != state.get("base")
        or sync.get("base_head") != base_commit
        or sync.get("parents") != [product_head, base_commit]
        or sync.get("github_verified") != [head_commit]
        or sync.get("product_evidence") != product_evidence_record(state, product_head)
    ):
        die("active version-resolution sync evidence is stale or malformed")
    if _native_relation_parents(base_dir, head_commit, "version resolution sync") != [
        product_head,
        base_commit,
    ]:
        die("version resolution sync parents do not match product and base")
    verify_local_commit(
        base_dir,
        head_commit,
        "version resolution sync",
        native_relation=True,
    )
    revalidation = sync.get("revalidation")
    if (
        not isinstance(revalidation, dict)
        or set(revalidation) != RESOLUTION_REVALIDATION_KEYS
        or revalidation.get("schema") != INTEGRATION_REVALIDATION_SCHEMA
    ):
        die("version resolution sync revalidation is missing or malformed")
    _manifest_paths(
        [revalidation.get("artifact")],
        "version resolution sync revalidation artifact",
    )
    digest = revalidation.get("sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        die("version resolution sync revalidation digest is malformed")
    base_before = _native_relation_merge_base(base_dir, product_head, base_commit)
    expected_paths = {
        "product_paths": _native_relation_diff_paths(
            base_dir, base_before, product_head
        ),
        "upstream_paths": _native_relation_diff_paths(
            base_dir, base_before, base_commit
        ),
        "composition_paths": _native_relation_diff_paths(
            base_dir, product_head, head_commit
        ),
    }
    expected_paths["overlap_paths"] = sorted(
        set(expected_paths["product_paths"]) & set(expected_paths["upstream_paths"])
    )
    expected_paths["affected_paths"] = sorted(
        set(expected_paths["composition_paths"]) | set(expected_paths["overlap_paths"])
    )
    if (
        revalidation.get("base_before") != base_before
        or revalidation.get("base_after") != base_commit
    ):
        die("version resolution sync revalidation commit pair is stale or malformed")
    stored_paths = {}
    for name in (
        "product_paths",
        "upstream_paths",
        "overlap_paths",
        "composition_paths",
        "affected_paths",
    ):
        stored_paths[name] = _manifest_paths(
            revalidation.get(name), f"version resolution sync {name}"
        )
        if stored_paths[name] != expected_paths[name]:
            die("version resolution sync revalidation path proof does not match")
    checks = revalidation.get("checks")
    if (
        not isinstance(checks, list)
        or not checks
        or len(checks) > INTEGRATION_CHECKS_MAX
    ):
        die("version resolution sync revalidation is missing or malformed")
    affected_paths = stored_paths["affected_paths"]
    changed = set(expected_paths["composition_paths"])
    overlap = set(expected_paths["overlap_paths"])
    target_paths = set()
    for target in relations["targets"]:
        target_paths.add(target["ledger"])
        target_paths.add(target["ledger"].rsplit("/", 1)[0] + "/SKILL.md")
    needed = (changed | overlap) & target_paths
    covered = set()
    seen_ids = set()
    for index, check in enumerate(checks):
        if not isinstance(check, dict) or set(check) != RESOLUTION_REVALIDATION_CHECK_KEYS:
            die("version resolution sync carries a failed or malformed check")
        check_id = check.get("id")
        if (
            not isinstance(check_id, str)
            or INTEGRATION_CHECK_ID_RE.fullmatch(check_id) is None
            or check_id in seen_ids
        ):
            die("version resolution sync carries a failed or malformed check")
        seen_ids.add(check_id)
        command = check.get("command")
        try:
            command_bytes = command.encode("utf-8") if isinstance(command, str) else b""
        except UnicodeEncodeError:
            command_bytes = b""
        if (
            not command_bytes
            or len(command_bytes) > INTEGRATION_COMMAND_BYTES_MAX
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in command
            )
            or isinstance(check.get("exit"), bool)
            or check.get("exit") != 0
        ):
            die("version resolution sync carries a failed or malformed check")
        paths = _manifest_paths(
            check.get("paths"),
            f"version resolution sync check {index} paths",
            set(affected_paths),
        )
        covered.update(paths)
    if covered != set(affected_paths):
        die("version resolution sync checks do not cover every affected path")
    if not needed.issubset(covered):
        die("version resolution sync checks do not cover each changed target path")
    previous_sync = _active_sync_predecessor(
        as_dict(state.get("integrate")), head_commit
    )
    _require_sync_resolution_guard(
        base_dir,
        sync,
        product_head,
        previous_sync=previous_sync,
    )


def _resolution_without_timestamp(receipt: dict) -> dict:
    return {key: value for key, value in receipt.items() if key != "ts"}


def build_version_resolution(
    base_dir: str,
    state: dict,
    *,
    exact_base: str | None = None,
    exact_head: str | None = None,
) -> dict:
    """Build one atomic resolution from stable refs or exact terminal parents."""
    runbook = receipted_source(base_dir, state, "runbook")
    relations = receipted_version_relations(base_dir, runbook, state=state)
    if relations is None:
        die("the receipted runbook declares no version relation")
    if state.get("phase") != "integrate":
        die("version resolution is available only after the step stack closes")
    product_head = final_product_head(state)
    integrate = as_dict(state.get("integrate"))
    sync = as_dict(integrate.get("sync"))
    expected_head = (
        require_full_sha(sync.get("commit"), "active recorded sync commit")
        if sync
        else product_head
    )
    base_ref = integration_base_of(state)
    repository = _native_relation_repository_identity(base_dir)
    _require_native_relation_history(base_dir)

    if exact_base is None or exact_head is None:
        first_base = remote_branch_tip(
            base_dir,
            base_ref,
            "version resolution base ref",
            native_relation=True,
        )
        first_head = remote_branch_tip(
            base_dir,
            run_branch_of(state),
            "version resolution run ref",
            native_relation=True,
        )
        if first_head != expected_head:
            die("version resolution run ref does not match the candidate head")
        if not sync and first_base != relations["anchor_commit"]:
            die(
                "version resolution base advanced; create the existing signed "
                "product/base sync and complete path revalidation first"
            )
        if sync and sync.get("base_head") != first_base:
            die("version resolution sync does not name the current base ref")
        base_commit, head_commit = first_base, first_head
    else:
        base_commit = require_full_sha(exact_base, "version resolution exact base")
        head_commit = require_full_sha(exact_head, "version resolution exact head")
        if head_commit != expected_head:
            die("version resolution exact head does not match the candidate head")
        if sync and sync.get("base_head") != base_commit:
            die("version resolution sync does not name the exact base parent")
        if not sync and base_commit != relations["anchor_commit"]:
            die("version resolution exact base requires a recorded signed sync")

    if _native_relation_commit(
        base_dir, base_commit, "version resolution base object"
    ) != base_commit:
        die("version resolution base object does not match")
    if _native_relation_commit(
        base_dir, head_commit, "version resolution candidate object"
    ) != head_commit:
        die("version resolution candidate object does not match")
    if sync:
        _require_resolution_sync(
            base_dir,
            state,
            sync,
            product_head,
            base_commit,
            head_commit,
            relations,
        )
    targets = [
        resolve_version_relation_target(
            base_dir,
            relations["anchor_commit"],
            base_commit,
            head_commit,
            target,
        )
        for target in relations["targets"]
    ]
    if exact_base is None:
        final_head = remote_branch_tip(
            base_dir,
            run_branch_of(state),
            "version resolution run ref reread",
            native_relation=True,
        )
        final_base = remote_branch_tip(
            base_dir,
            base_ref,
            "version resolution base ref reread",
            native_relation=True,
        )
        if (final_base, final_head) != (base_commit, head_commit):
            die("version resolution remote refs changed during evidence collection")
    _require_native_relation_history(base_dir)
    if _native_relation_repository_identity(base_dir) != repository:
        die("version resolution repository changed during evidence collection")
    receipt = {
        "schema": VERSION_RESOLUTION_SCHEMA,
        "runbook_sha256": as_dict(state["receipts"].get("runbook")).get("sha256"),
        "relations_sha256": relations["source_sha256"],
        "base_ref": base_ref,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "targets": sorted(targets, key=lambda target: target["skill"]),
        "ts": now(),
    }
    validate_version_resolution_shape(receipt, "built.version_resolution")
    return receipt


def active_version_resolution(base_dir: str, state: dict) -> dict:
    history = as_dict(state.get("integrate")).get("version_resolutions")
    if not isinstance(history, list) or not history:
        die("version relations have no recorded integration-time resolution")
    active = validate_version_resolution_shape(
        history[-1], "integrate.version_resolutions[-1]"
    )
    current = build_version_resolution(base_dir, state)
    if _resolution_without_timestamp(active) != _resolution_without_timestamp(current):
        die("the active version resolution is stale for the current base or head")
    return active


def version_resolution_status(base_dir: str, state: dict) -> dict:
    """Describe the newest receipt without mistaking recorded for current."""
    history = as_dict(state.get("integrate")).get("version_resolutions") or []
    if not history:
        return {
            "status": "absent",
            "history": 0,
            "base_commit": None,
            "head_commit": None,
            "reason": None,
        }
    newest = validate_version_resolution_shape(
        history[-1], "integrate.version_resolutions[-1]"
    )
    common = {
        "history": len(history),
        "base_commit": newest["base_commit"],
        "head_commit": newest["head_commit"],
    }
    terminal = as_dict(as_dict(state.get("receipts")).get("integrate")).get(
        "version_resolution"
    )
    if state.get("phase") == "done" and terminal == newest:
        return {"status": "terminal", **common, "reason": None}
    if state.get("phase") != "integrate":
        return {
            "status": "stale",
            **common,
            "reason": "recorded outside the integration phase",
        }
    diagnostic = io.StringIO()
    try:
        with contextlib.redirect_stderr(diagnostic):
            active_version_resolution(base_dir, state)
    except SystemExit:
        reason = diagnostic.getvalue().strip()
        prefix = "hexctl: error: "
        if reason.startswith(prefix):
            reason = reason[len(prefix) :]
        reason = re.sub(r"[\x00-\x1f\x7f]+", " ", reason).strip()[:512]
        return {
            "status": "stale",
            **common,
            "reason": reason or "current evidence does not match the newest receipt",
        }
    return {"status": "active", **common, "reason": None}


def carried_forward_lines(text: str) -> list[str] | None:
    """The lines under the carried-forward heading, or None when it is absent.

    Reading stops at the next heading, so a later section cannot stand in for
    this one.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != CARRIED_FORWARD_HEADING:
            continue
        said = []
        for candidate in lines[index + 1:]:
            if candidate.startswith("#"):
                break
            if candidate.strip():
                said.append(candidate.strip())
        return said
    return None


def carried_forward_fault(path: str) -> str | None:
    """Why this run has not said what it leaves unfinished, or None.

    A run that gives up on something records it in the body of the last pull
    request it lands, because that is what the next study reads. A run that
    finished everything still writes the section: an absent heading cannot be
    told apart from a question nobody asked.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return (f"the run-level pull request body {path} cannot be read "
                f"({exc}); the prose phase writes it and the integration pull "
                f"request is opened from it")

    said = carried_forward_lines(text)
    if said is None:
        return (f"{path} has no '{CARRIED_FORWARD_HEADING}' section; name every "
                f"lead left unpursued, finding accepted rather than fixed, "
                f"boundary refused and claim left unverified, or say plainly "
                f"that this run leaves none")
    if not said:
        return (f"{path} carries a '{CARRIED_FORWARD_HEADING}' heading with "
                f"nothing under it; say what is unfinished, or say that "
                f"nothing is")
    return None


def carried_forward_record(path: str) -> dict:
    """What the receipt keeps about the section, once it has passed."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    return {
        "path": os.path.join(STATE_DIR_NAME, RUN_PR_FILE),
        "lines": len(carried_forward_lines(text) or []),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def base_ledger_versions(base_dir: str, base_commit: str, ledger: str) -> frozenset:
    """Every row version the ledger already carried at one exact base commit.

    A run that syncs absorbs whatever other runs published meanwhile, and those
    rows are not its own. This is the only evidence that separates them, and it
    is already recorded: `done sync-run` stores the exact base commit it merged.

    An unreadable or unparsable blob returns the empty set, which leaves the
    gate on its older and stricter arithmetic. Failing the other way would let a
    broken read excuse a row nobody published.
    """
    if not COMMIT_RE.fullmatch(base_commit or ""):
        return frozenset()
    # `bounded_run` rather than `bounded_git`: a blob this reader cannot fetch is
    # an answer it handles, not a fatal error, so it must not print a refusal or
    # exit. Reading the status keeps that decision here.
    status, raw = bounded_run(
        base_dir, "git", ["show", f"{base_commit}:{ledger}"]
    )
    if status != 0:
        return frozenset()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return frozenset()
    return frozenset(row["version"] for row in ledger_rows(text))


def frontier_rows_after_anchor(rows: list[dict], before: dict) -> list[dict]:
    """The history rows a run is answerable for, in order.

    Shared by the gate and the receipt. Two copies of this slicing would drift,
    and the receipt would then name a different set from the one the refusal
    counted.
    """
    anchor = before.get("version_at_init")
    anchor_at = [i for i, entry in enumerate(rows) if entry["version"] == anchor]
    if anchor_at:
        return rows[anchor_at[-1] + 1:]
    return rows[len(rows) - max(0, len(rows) - before["rows"]):]


def frontier_subtracted_rows(
    base_dir: str, before: dict, published: frozenset
) -> list[str]:
    """Which already-published versions the gate subtracted, for the receipt."""
    if not published:
        return []
    path = os.path.join(base_dir, before["ledger"])
    try:
        with open(path, encoding="utf-8") as handle:
            rows = ledger_rows(handle.read())
    except OSError:
        return []
    after = frontier_rows_after_anchor(rows, before)
    return sorted({entry["version"] for entry in after} & published)


def frontier_close_fault(
    path: str, before: dict, published: frozenset = frozenset()
) -> str | None:
    """Why this run has not closed the frontier it declared, or None.

    The maturity gate says to update the ledger exactly once, and says it in
    prose. This repository has already had to reconstruct two broken evolutions,
    so the run proves the update instead of asserting it.

    `published` names the rows the base already carried, so a run is charged for
    its own rows and no others. Without it the second of two concurrent frontier
    runs on one skill is refused for work it did not do, which is what happened
    to the issue 466 run: it added `fiat-v5.15.1`, absorbed `fiat-v5.14.1` in
    its one permitted sync, and could not renumber either, because
    `done_integrate` freezes the run branch at that sync commit.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return f"the declared ledger {path} cannot be read ({exc})"

    if hashlib.sha256(text.encode("utf-8")).hexdigest() == before["sha256"]:
        return (f"{path} is byte-for-byte what it was at init; a completed "
                f"frontier job records one new row")

    rows = ledger_rows(text)
    # Anchor on the init-time version rather than the stored count: a snapshot
    # taken while the gate misread a ledger's row spelling counted a real
    # history as empty, and the anchor survives that (skills#443).
    anchor = before.get("version_at_init")
    anchor_at = [i for i, r in enumerate(rows) if r["version"] == anchor]
    if anchor is not None and not anchor_at:
        return (f"{path} no longer carries the init-time version row "
                f"{anchor!r}; history is append-only")
    after = frontier_rows_after_anchor(rows, before)
    foreign = [entry for entry in after if entry["version"] in published]
    gained = len(after) - len(foreign)
    if gained != 1:
        tail = ""
        if foreign:
            tail = (f", after subtracting {len(foreign)} already published in "
                    f"the recorded base")
        return (f"{path} gained {gained} history row(s){tail}; the contract "
                f"allows exactly one per completed frontier job")

    row = rows[-1]
    if row["version"] in published:
        return (f"the newest row {row['version']} was already published in the "
                f"recorded base; this run's own row has to be the newest")
    skill = os.path.basename(os.path.dirname(path))
    current = ledger_field(text, "Current version")
    if row["version"] != current:
        return (f"the new row is {row['version']} and the header says "
                f"{current}; they have to be the same row")
    if row["revision"] != ledger_field(text, "Frontier revision"):
        return (f"the new row's revision {row['revision']!r} is not the "
                f"header's {ledger_field(text, 'Frontier revision')!r}")

    expected = ledger_frontier_digest(text)
    if expected is None:
        return f"{path} is missing one of the four frontier header fields"
    if row["digest"] != expected:
        return (f"the new row's digest does not match the frontier line it "
                f"describes; recomputed {expected[:16]}...")

    parts = _label_parts(row["version"], skill)
    prior = rows[-2] if len(rows) > 1 else None
    if parts is None:
        return f"{row['version']} is not a valid label for {skill}"
    if prior is not None:
        before_parts = _label_parts(prior["version"], skill)
        if before_parts is None:
            return f"the previous row {prior['version']} is not a valid label"
        axis, bumped = row["axis"], None
        if axis == "evolution":
            bumped = (before_parts[0] + 1, before_parts[1], before_parts[2])
        elif axis == "generation":
            bumped = (before_parts[0], before_parts[1] + 1, before_parts[2])
            if row["revision"] != prior["revision"]:
                return "a generation entry must retain the prior frontier revision"
            if row["digest"] != prior["digest"]:
                return "a generation entry must retain the prior frontier digest"
        elif axis == "epoch":
            bumped = (before_parts[0], before_parts[1], before_parts[2] + 1)
            if row["digest"] != prior["digest"] and \
                    "reopen" not in (row["evidence"] + row["change"]).lower():
                return "an epoch entry that moves the frontier must record the reopening"
        if bumped is not None and parts != bumped:
            article = "an" if axis[0] in "aeiou" else "a"
            return (f"{article} {axis} entry from {prior['version']} must be "
                    f"{skill}-v{bumped[0]}.{bumped[1]}.{bumped[2]}, not "
                    f"{row['version']}")

    status = ledger_field(text, "Frontier status")
    next_job = ledger_field(text, "Next Fiat job")
    if status not in ("open", "mature"):
        return f"frontier status {status!r} is neither open nor mature"
    if status == "mature" and next_job != "None -- mature":
        return "a mature frontier's next job has to be `None -- mature`"
    if status == "open" and next_job == "None -- mature":
        return "an open frontier cannot hold `None -- mature` as its next job"
    return None


def stale_controller(target_dir: str) -> tuple[str, str, str] | None:
    """Whether the running Fiat is older than a copy checked into the target.

    A marketplace plugin is installed from a published copy, so a repository
    that also holds Fiat's source can be a whole evolution ahead of the
    controller driving the run. Every rule the newer one enforces then goes
    unenforced silently, which is the one omission a receipt cannot show:
    the missing flag looks like a rule that was never written.

    Returns (running label, checked-in label, repo-relative path), or None when
    there is nothing to compare or the two agree.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    running = ledger_version(os.path.join(here, os.pardir, "EVOLUTION.md"))
    if running is None:
        return None
    for candidate in sorted(
        glob.glob(
            os.path.join(target_dir, "plugins", "*", "skills", "fiat", "EVOLUTION.md")
        )
    ):
        if os.path.realpath(candidate) == os.path.realpath(
            os.path.join(here, os.pardir, "EVOLUTION.md")
        ):
            continue  # the run's target is the plugin's own source tree
        checked_in = ledger_version(candidate)
        if checked_in is not None and checked_in != running:
            return running, checked_in, os.path.relpath(candidate, target_dir)
    return None


CURRENCY_REGISTRY_FILE = "installed_plugins.json"
CURRENCY_REGISTRY_MAX = 1024 * 1024
CURRENCY_CACHE_DIR = "cache"
CURRENCY_MARKETPLACES_DIR = "marketplaces"
"""The host install layout the currency observation reads, never assumes.

`<plugins root>/installed_plugins.json` records every install;
`<plugins root>/cache/<marketplace>/<plugin>/<version>/` holds the running
copy; `<plugins root>/marketplaces/<marketplace>/` is the git clone whose own
configuration names the upstream. The plugins root is derived from the
controller's resolved file, so no environment or target-repository value
chooses what gets read.
"""


def currency_inside_git_worktree(start_dir: str) -> bool:
    """Whether a directory has a `.git` somewhere above it."""
    current = start_dir
    while True:
        if os.path.exists(os.path.join(current, ".git")):
            return True
        parent = os.path.dirname(current)
        if parent == current:
            return False
        current = parent


def currency_cache_split(real_file: str) -> tuple[str, str] | None:
    """The (plugins root, marketplace) a cached controller file sits under.

    The nearest ancestor named `cache` with marketplace, plugin and version
    components between it and the file decides; None means the file is not
    under an install cache and the in-repo check applies instead.
    """
    parts = real_file.split(os.sep)
    for index in range(len(parts) - 5, 0, -1):
        if parts[index] != CURRENCY_CACHE_DIR:
            continue
        if all(parts[index + 1:index + 4]):
            return os.sep.join(parts[:index]), parts[index + 1]
    return None


def currency_registry_load(plugins_root: str) -> tuple[str, dict | str]:
    """The host registry's plugins mapping, read once and bounded.

    Returns ("ok", plugins) or ("unknown", warning) when the registry cannot
    answer at all: missing, oversized, malformed, or the wrong kind. Hostile
    bytes are named by kind, never echoed.
    """
    path = os.path.join(plugins_root, CURRENCY_REGISTRY_FILE)
    try:
        with open(path, "rb") as handle:
            raw = handle.read(CURRENCY_REGISTRY_MAX + 1)
    except OSError:
        return "unknown", "registry-missing"
    if len(raw) > CURRENCY_REGISTRY_MAX:
        return "unknown", "registry-oversized"
    try:
        registry = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return "unknown", "registry-malformed"
    plugins = registry.get("plugins") if isinstance(registry, dict) else None
    if not isinstance(plugins, dict):
        return "unknown", "registry-wrong-kind"
    return "ok", plugins


def currency_record_pin(record: dict) -> tuple[str, str | None]:
    """One install record's pin answer.

    ("pin", sha) when the record carries a commit SHA, ("absent", None) when
    it carries none, and ("unknown", "registry-pin-malformed") for anything
    else, because a pin that is not a commit is hostile input, not a null.
    """
    pin = record.get("gitCommitSha")
    if pin is None:
        return "absent", None
    if isinstance(pin, str) and COMMIT_RE.fullmatch(pin):
        return "pin", pin
    return "unknown", "registry-pin-malformed"


def currency_registry_pin(plugins_root: str, real_file: str) -> tuple[str, str | None]:
    """The pin the host registry records for the install holding one file.

    Returns ("pin", sha) when the matching install records a commit SHA,
    ("absent", None) when it records none, and ("unknown", warning) when the
    registry cannot answer: missing, oversized, malformed, wrong kind, no
    install path holding the file, or a pin that is not a commit SHA.
    """
    kind, plugins = currency_registry_load(plugins_root)
    if kind != "ok":
        return "unknown", plugins
    for records in plugins.values():
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            install_path = record.get("installPath")
            if not isinstance(install_path, str) or not install_path:
                continue
            prefix = os.path.join(os.path.realpath(install_path), "")
            if not real_file.startswith(prefix):
                continue
            return currency_record_pin(record)
    return "unknown", "registry-unmatched"


def currency_clone_branch(clone_dir: str) -> str | None:
    """The branch name a marketplace clone's HEAD points at, or None."""
    try:
        with open(os.path.join(clone_dir, ".git", "HEAD"),
                  encoding="utf-8") as handle:
            head = handle.read(4096).strip()
    except (OSError, UnicodeDecodeError):
        return None
    branch = head.removeprefix("ref: refs/heads/")
    if branch == head or not branch_name_ok(branch):
        return None
    return branch


def currency_remote_head(clone_dir: str, branch: str) -> tuple[str | None, str | None]:
    """One bounded upstream observation: the clone's origin head for a branch.

    Runs inside the marketplace clone and names the remote rather than a URL,
    so only the clone's own configuration can choose where the read goes, and
    no URL passes through this controller at all. Credential prompts are
    disabled; the read is time-capped and output-capped by `bounded_probe`.
    Returns (head, None), or (None, warning) unless the response contains one
    full commit SHA and its exact ref name -- a failed read is never a verdict.
    """
    expected_ref = f"refs/heads/{branch}"
    status, output, failure = bounded_probe(
        clone_dir,
        "git",
        ["ls-remote", "--refs", "origin", expected_ref],
        extra_env={"GIT_TERMINAL_PROMPT": "0"},
    )
    if failure is not None:
        return None, f"remote-{failure}"
    if status != 0:
        return None, "remote-failed"
    try:
        text = output.decode("utf-8")
    except UnicodeDecodeError:
        return None, "remote-malformed"
    lines = [line for line in text.splitlines() if line]
    if len(lines) != 1:
        return None, "remote-malformed"
    fields = lines[0].split("\t")
    if (
        len(fields) != 2
        or not COMMIT_RE.fullmatch(fields[0])
        or fields[1] != expected_ref
    ):
        return None, "remote-malformed"
    return fields[0], None


def observe_controller_currency(
    controller_file: str | None = None,
    remote_reader=None,
) -> dict:
    """Resolve the running controller's own file to route, pin and upstream head.

    The one observation `init` gates on. Every input is observed rather than
    assumed: the plugins root and marketplace come from the controller's own
    resolved path, the pin from the host registry beside that root, and the
    upstream head from one bounded read inside the marketplace clone, on the
    git-backed route only. Whatever the observation cannot prove reads as an
    explicit null and, where it blocks a verdict, as `unknown` with a named
    warning -- never a guess toward `current` or `behind`.
    """
    if controller_file is None:
        controller_file = __file__
    if remote_reader is None:
        remote_reader = currency_remote_head
    real = os.path.realpath(controller_file)
    observation = {
        "ledger_version": ledger_version(
            os.path.join(os.path.dirname(real), os.pardir, "EVOLUTION.md")
        ),
        "route": "unknown",
        "pin": None,
        "observed_head": None,
        "verdict": "unknown",
        "warning": None,
    }
    split = currency_cache_split(real)
    if split is None:
        if currency_inside_git_worktree(os.path.dirname(real)):
            observation["route"] = "in-repo-source"
            observation["verdict"] = "no-pin"
        else:
            observation["warning"] = "route-unresolved"
        return observation
    plugins_root, marketplace = split
    kind, value = currency_registry_pin(plugins_root, real)
    observation.update(
        currency_pin_observation(plugins_root, marketplace, kind, value,
                                 remote_reader)
    )
    return observation


def currency_pin_observation(
    plugins_root: str,
    marketplace: str,
    kind: str,
    value: str | None,
    remote_reader,
) -> dict:
    """Route, pin, head, verdict and warning for one registry pin answer.

    The shared tail of the init gate and the `currency` report: `kind` and
    `value` come from the registry ("pin", "absent" or "unknown"), and
    everything past them is observed from the marketplace clone under the
    same plugins root. A recorded pin makes the install git-backed even when
    the marketplace clone is gone: claiming `managed` there would let one
    deleted directory silence the gate without a warning (S2-R1-02). The pin
    stays recorded, the head stays an explicit null, and the verdict stays
    `unknown`.
    """
    observation = {
        "route": "unknown",
        "pin": None,
        "observed_head": None,
        "verdict": "unknown",
        "warning": None,
    }
    if kind == "unknown":
        observation["warning"] = value
        return observation
    if kind == "absent":
        observation["route"] = "managed"
        observation["verdict"] = "managed"
        return observation
    observation["route"] = "git-backed"
    observation["pin"] = value
    clone = os.path.join(plugins_root, CURRENCY_MARKETPLACES_DIR, marketplace)
    if not os.path.exists(os.path.join(clone, ".git")):
        observation["warning"] = "clone-missing"
        return observation
    branch = currency_clone_branch(clone)
    if branch is None:
        observation["warning"] = "clone-head-unreadable"
        return observation
    head, warning = remote_reader(clone, branch)
    if head is None:
        observation["warning"] = warning or "remote-failed"
        return observation
    observation["observed_head"] = head
    observation["verdict"] = "current" if head == value else "behind"
    return observation


def currency_record_marketplace(plugins_root: str, record: dict) -> str | None:
    """The marketplace directory an install record sits under, or None.

    Observed from the record's install path relative to the same plugins
    root the controller derived from its own file, so a hostile registry
    entry cannot point the clone read outside that root.
    """
    install_path = record.get("installPath")
    if not isinstance(install_path, str) or not install_path:
        return None
    real = os.path.realpath(install_path)
    prefix = os.path.join(plugins_root, CURRENCY_CACHE_DIR, "")
    if not real.startswith(prefix):
        return None
    return real[len(prefix):].split(os.sep, 1)[0] or None


def currency_report(
    controller_file: str | None = None,
    remote_reader=None,
) -> tuple[list[dict], str | None]:
    """One currency row per installed plugin, or a named refusal.

    Returns (rows, None) or ([], refusal). The plugins root comes from the
    running controller's own resolved file exactly as the init gate derives
    it, the registry is one bounded read, and upstream is asked at most once
    per distinct marketplace clone rather than once per plugin. A defective
    record is a row with verdict `unknown`, so a plugin never vanishes from
    the report; a registry that cannot answer at all is a refusal, because an
    empty success would read as a fleet with nothing behind. Every install
    record in the registry gets a row: filtering by a hard-coded marketplace
    name would blind the report on a private-mirror host.
    """
    if controller_file is None:
        controller_file = __file__
    if remote_reader is None:
        remote_reader = currency_remote_head
    real = os.path.realpath(controller_file)
    split = currency_cache_split(real)
    if split is None:
        return [], (
            "currency reports the install registry, and this controller does "
            "not run from an install cache; run the installed copy instead"
        )
    plugins_root, _ = split
    kind, plugins = currency_registry_load(plugins_root)
    if kind != "ok":
        return [], f"the install registry cannot be read ({plugins})"

    memo: dict = {}

    def read_once(clone_dir: str, branch: str):
        key = (clone_dir, branch)
        if key not in memo:
            memo[key] = remote_reader(clone_dir, branch)
        return memo[key]

    unknown_row = {
        "route": "unknown",
        "pin": None,
        "observed_head": None,
        "verdict": "unknown",
    }
    rows = []
    for key in sorted(plugins):
        plugin = key.rsplit("@", 1)[0] or key
        records = plugins[key]
        if not isinstance(records, list) or not records:
            rows.append({"plugin": plugin, "version": None, **unknown_row,
                         "warning": "registry-wrong-kind"})
            continue
        for record in records:
            if not isinstance(record, dict):
                rows.append({"plugin": plugin, "version": None, **unknown_row,
                             "warning": "registry-wrong-kind"})
                continue
            version = record.get("version")
            row = {
                "plugin": plugin,
                "version": version if isinstance(version, str) else None,
            }
            marketplace = currency_record_marketplace(plugins_root, record)
            if marketplace is None:
                row.update(unknown_row)
                row["warning"] = "install-path-unrecognised"
            else:
                kind, value = currency_record_pin(record)
                row.update(currency_pin_observation(
                    plugins_root, marketplace, kind, value, read_once))
            rows.append(row)
    return rows, None


def currency_text_field(value) -> str:
    """One row value rendered for the line-per-plugin text report.

    Plugin names and versions are registry bytes, and a byte that breaks or
    reorders lines would forge row boundaries -- a newline in a key prints a
    fabricated row that the eye reads as another plugin's verdict (S3-R1-01),
    a Unicode line or paragraph separator does the same to a `splitlines`
    consumer, and a lone surrogate crashes the encoder mid-report
    (S3-R2-01). Anything not printable renders as `?`, which keeps every
    legitimate slug, semver, hex and verdict byte for byte; the exit code
    and `--json`, which escapes hostile values natively, are the machine
    surfaces either way.
    """
    if value is None:
        return "null"
    return "".join(ch if ch.isprintable() else "?" for ch in str(value))


def cmd_currency(args) -> None:
    """Report pin-versus-upstream currency for every installed plugin.

    Read-only: no state, no lock, no `.hexaemeron`. Exit 0 when nothing is
    behind, 3 while anything is, 1 on a refusal, so a loop can gate a re-pin
    on the status alone.
    """
    rows, refusal = currency_report()
    if refusal is not None:
        die(refusal, 1)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            line = " ".join(
                currency_text_field(row[field])
                for field in ("plugin", "version", "route", "pin",
                              "observed_head", "verdict")
            )
            if row["warning"] is not None:
                line += f" ({row['warning']})"
            print(line)
    if any(row["verdict"] == "behind" for row in rows):
        sys.exit(3)


RESERVED_RECEIPTS = {"study", "runbook", "run_observations"}


def cmd_record(args) -> None:
    state = load_state(args.dir)
    if args.key in RESERVED_RECEIPTS:
        die(f"'{args.key}' is a phase receipt; only `hexctl done {args.key}` writes it")
    if args.key == "controller_currency":
        # Init's own observation, protected like `task_issue`: a later
        # rewrite would replace the recorded verdict and waiver with a
        # value nothing observed (S2-R1-01).
        die("controller_currency is init's observation; only `hexctl init` writes it")
    if state.get("halted") and args.key != "halt_note":
        # Recording context while halted is allowed; progress commands are not.
        pass
    value = parse_value(args.value)
    if args.key == "task_issue":
        if args.key not in state["receipts"]:
            die(
                "task_issue must be supplied by `init --task-issue`; "
                "the stored run branch cannot be renamed"
            )
        if value != state["receipts"][args.key]:
            die("task_issue is already recorded and cannot be changed")
        print("task_issue already recorded")
        return
    state["receipts"][args.key] = value
    commit(args.dir, state, "record", {"key": args.key, "value": value})
    print(f"recorded {args.key}")


def ledger_entries(base_dir: str) -> list[dict]:
    entries = []
    try:
        with open(ledger_path(base_dir), encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                entry = json.loads(line)
                entry = dict(entry)
                entry["_line"] = line_number
                entries.append(entry)
    except (OSError, ValueError, TypeError):
        die("ledger unreadable; run `hexctl verify`", 1)
    return entries


def selected_observation_receipt(base_dir: str) -> dict:
    entries = ledger_entries(base_dir)
    if not entries or entries[-1].get("event") == "record:run-observation":
        observation_error(
            "FOB003",
            "there is no new controller receipt immediately before this selection",
            "record the observation after the delivery receipt it describes",
        )
    entry = entries[-1]
    return {
        "line": entry["_line"],
        "event": entry.get("event"),
        "hash": entry.get("hash"),
        "state": entry.get("state"),
    }


def cmd_observe(args) -> None:
    """Bind one validated prefix, or one explicit unavailable observation state."""
    verify_run(args.dir)
    state = load_state(args.dir)
    receipt = selected_observation_receipt(args.dir)
    existing = state["receipts"].get("run_observations", [])
    if not isinstance(existing, list) or len(existing) >= OBSERVATION_BINDINGS_MAX:
        observation_error(
            "FOB003",
            "the observation receipt collection is malformed or full",
            "verify the run or start a fresh bounded run before recording more prefixes",
        )

    common = {
        "schema": OBSERVATION_BINDING_CONTRACT,
        "observation_contract": OBSERVATION_CONTRACT,
        "controller_run_id": controller_run_id(state),
        "recorded_at": now(),
        "capture_status": args.capture_status,
        "redaction_status": args.redaction_status,
        "receipt": receipt,
    }
    if args.capture_status == "accepted":
        if not args.artifact:
            observation_error(
                "FOB002",
                "an accepted observation has no companion artifact",
                "supply one stable path beneath .hexaemeron/observations",
            )
        if args.reason_code:
            observation_error(
                "FOB003",
                "an accepted observation cannot carry an unavailable reason",
                "remove the reason code or record a non-available capture status",
            )
        if args.redaction_status != "passed":
            observation_error(
                "FOB005",
                "the selected prefix has no passing redaction result",
                "complete redaction successfully or record a non-available status",
            )
        relative, data, summary = validated_observation_prefix(
            args.dir, args.artifact, state
        )
        prior = next(
            (
                item
                for item in reversed(existing)
                if isinstance(item, dict)
                and item.get("capture_status") == "accepted"
            ),
            None,
        )
        if prior is not None:
            prior_count = prior.get("byte_count")
            prior_events = prior.get("event_count")
            prior_interval = prior.get("interval")
            if (
                relative != prior.get("artifact")
                or isinstance(prior_count, bool)
                or not isinstance(prior_count, int)
                or prior_count < 1
                or len(data) <= prior_count
                or hashlib.sha256(data[:prior_count]).hexdigest()
                != prior.get("sha256")
                or isinstance(prior_events, bool)
                or not isinstance(prior_events, int)
                or summary["event_count"] <= prior_events
                or not isinstance(prior_interval, dict)
                or summary["first_event_id"]
                != prior_interval.get("first_event_id")
                or summary["first_sequence"]
                != prior_interval.get("first_sequence")
            ):
                observation_error(
                    "FOB004",
                    "the new selection is not a strict extension of the bound stream",
                    "preserve every earlier bound byte and append later events to the same file",
                )
        binding = {
            **common,
            "validation_status": "passed",
            "artifact": relative,
            "byte_count": len(data),
            "event_count": summary["event_count"],
            "sha256": hashlib.sha256(data).hexdigest(),
            "interval": {
                "first_sequence": summary["first_sequence"],
                "last_sequence": summary["last_sequence"],
                "first_event_id": summary["first_event_id"],
                "last_event_id": summary["last_event_id"],
            },
        }
    else:
        if args.artifact:
            observation_error(
                "FOB005",
                "a non-available observation cannot bind artifact bytes",
                "remove the artifact or record an accepted capture",
            )
        if not args.reason_code or not OBSERVATION_REASON_RE.fullmatch(args.reason_code):
            observation_error(
                "FOB005",
                "the non-available observation has no bounded reason code",
                "supply one lowercase reason code of at most 64 characters",
            )
        if args.redaction_status == "passed":
            observation_error(
                "FOB005",
                "an unavailable capture cannot claim successful redaction",
                "record redaction as failed or unknown",
            )
        binding = {
            **common,
            "validation_status": "unknown",
            "reason_code": args.reason_code,
        }

    state["receipts"]["run_observations"] = [*existing, binding]
    binding_digest = hashlib.sha256(canonical(binding).encode()).hexdigest()
    commit(
        args.dir,
        state,
        "record:run-observation",
        {
            "binding_sha256": binding_digest,
            "capture_status": binding["capture_status"],
            "receipt_hash": receipt["hash"],
        },
    )
    print(
        f"recorded {OBSERVATION_BINDING_CONTRACT}: "
        f"capture={binding['capture_status']} phase unchanged"
    )


def verify_observation_bindings(base_dir: str, state: dict) -> tuple[int, int]:
    bindings = state["receipts"].get("run_observations")
    if not isinstance(bindings, list) or not bindings:
        observation_error(
            "FOB001",
            "the requested run has no observation binding",
            "record one available or explicit non-available observation receipt",
            1,
        )
    if len(bindings) > OBSERVATION_BINDINGS_MAX:
        observation_error(
            "FOB003",
            "the observation receipt collection exceeds its bound",
            "restore the receipted state and verify again",
            1,
        )
    entries = ledger_entries(base_dir)
    by_hash = {entry.get("hash"): entry for entry in entries}
    observation_records = [
        entry
        for entry in entries
        if entry.get("event") == "record:run-observation"
    ]
    if len(observation_records) != len(bindings):
        observation_error(
            "FOB003",
            "the observation binding and ledger record counts disagree",
            "restore the bound state and every matching observation ledger record",
            1,
        )
    used_record_lines = set()
    latest_tail = 0
    previous = None
    for binding in bindings:
        if not isinstance(binding, dict):
            observation_error(
                "FOB003",
                "an observation binding is not a closed record",
                "restore the receipted state and verify again",
                1,
            )
        receipt = binding.get("receipt")
        selected = by_hash.get(receipt.get("hash")) if isinstance(receipt, dict) else None
        binding_digest = hashlib.sha256(canonical(binding).encode()).hexdigest()
        matching_records = [
            entry
            for entry in observation_records
            if isinstance(entry.get("data"), dict)
            and entry["data"].get("binding_sha256") == binding_digest
        ]
        record = matching_records[0] if len(matching_records) == 1 else None
        record_data = record.get("data") if isinstance(record, dict) else None
        if (
            binding.get("schema") != OBSERVATION_BINDING_CONTRACT
            or binding.get("observation_contract") != OBSERVATION_CONTRACT
            or binding.get("controller_run_id") != controller_run_id(state)
            or selected is None
            or selected.get("event") == "record:run-observation"
            or record is None
            or record.get("_line") in used_record_lines
            or selected.get("_line") + 1 != record.get("_line")
            or record_data.get("receipt_hash") != receipt.get("hash")
            or record_data.get("capture_status") != binding.get("capture_status")
            or receipt
            != {
                "line": selected.get("_line"),
                "event": selected.get("event"),
                "hash": selected.get("hash"),
                "state": selected.get("state"),
            }
        ):
            observation_error(
                "FOB003",
                "an observation binding disagrees with its contract, run, or receipt",
                "restore the bound state and its immediately preceding ledger receipt",
                1,
            )
        used_record_lines.add(record.get("_line"))
        if (
            binding.get("capture_status") != "accepted"
            or binding.get("validation_status") != "passed"
            or binding.get("redaction_status") != "passed"
        ):
            observation_error(
                "FOB005",
                "the requested observation claim is unavailable or failed",
                "capture, validate, and redact an accepted prefix before claiming it",
                1,
            )
        artifact = binding.get("artifact")
        byte_count = binding.get("byte_count")
        event_count = binding.get("event_count")
        digest = binding.get("sha256")
        interval = binding.get("interval")
        if (
            not isinstance(artifact, str)
            or isinstance(byte_count, bool)
            or not isinstance(byte_count, int)
            or byte_count < 1
            or isinstance(event_count, bool)
            or not isinstance(event_count, int)
            or event_count < 1
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or not isinstance(interval, dict)
        ):
            observation_error(
                "FOB003",
                "an available observation binding has an invalid closed shape",
                "restore the complete receipted binding and verify again",
                1,
            )
        _, current = read_observation_bytes(base_dir, artifact, exit_code=1)
        if len(current) < byte_count:
            observation_error(
                "FOB004",
                "the bound observation prefix was truncated",
                "restore the exact bound prefix bytes or record a later receipt",
                1,
            )
        prefix = current[:byte_count]
        if hashlib.sha256(prefix).hexdigest() != digest:
            observation_error(
                "FOB004",
                "the bound observation prefix was replaced, reordered, or changed",
                "restore the exact bound prefix bytes or record a later receipt",
                1,
            )
        findings = observation_validator_module(exit_code=1).validate_bytes(
            prefix,
            display_path=artifact,
            allow_prefix=True,
        )
        if findings:
            observation_error(
                "FOB003",
                "the bound prefix no longer passes structural validation",
                "restore the exact validated prefix and verify again",
                1,
            )
        summary = observation_summary(prefix, exit_code=1)
        expected_interval = {
            "first_sequence": summary["first_sequence"],
            "last_sequence": summary["last_sequence"],
            "first_event_id": summary["first_event_id"],
            "last_event_id": summary["last_event_id"],
        }
        if (
            summary["contract"] != OBSERVATION_CONTRACT
            or summary["run_id"] != controller_run_id(state)
            or summary["event_count"] != event_count
            or interval != expected_interval
        ):
            observation_error(
                "FOB003",
                "the bound event count or identity interval diverges",
                "restore the exact binding metadata and selected prefix",
                1,
            )
        recheck_observation_bytes(
            base_dir,
            artifact,
            current,
            exit_code=1,
        )
        if previous is not None and (
            record.get("_line") <= previous["record_line"]
            or artifact != previous["artifact"]
            or byte_count <= previous["byte_count"]
            or event_count <= previous["event_count"]
            or hashlib.sha256(prefix[: previous["byte_count"]]).hexdigest()
            != previous["sha256"]
        ):
            observation_error(
                "FOB004",
                "the recorded observation sequence is not one monotonic stream",
                "restore each earlier bound prefix and append later events to the same file",
                1,
            )
        previous = {
            "artifact": artifact,
            "byte_count": byte_count,
            "event_count": event_count,
            "record_line": record.get("_line"),
            "sha256": digest,
        }
        latest_tail = len(current) - byte_count
    return len(bindings), latest_tail


def cmd_config(args) -> None:
    state = load_state(args.dir)
    node = state["config"]
    parts = args.path.split(".")
    if args.action == "get":
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                die(f"config path not found: {args.path}")
            node = node[part]
        print(json.dumps(node))
        return
    if not config_path_is_mutable(args.path):
        die(
            f"config path is immutable: {args.path}; config set may change only "
            "audit.log_path, git, or git.*"
        )
    if not args.value:
        die("config set requires a value")
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            die(f"config path not found: {args.path}")
        node = node[part]
    leaf = parts[-1]
    if not isinstance(node, dict) or leaf not in node:
        die(f"config path not found: {args.path}")
    value = parse_value(args.value)
    if args.path == "audit.log_path":
        value = check_audit_log_path(args.dir, state, value)
    node[leaf] = value
    commit(args.dir, state, "config-set", {"path": args.path, "value": node[leaf]})
    print(f"set {args.path}")


def _require_file(path: str, label: str) -> str:
    if not path:
        die(f"--{label} is required")
    if not os.path.exists(path):
        die(f"{label} not found on disk: {path}")
    return path


def _portable_receipt_artifact(base_dir: str, path: str) -> str:
    """Store a verified source as one portable target-relative path."""
    try:
        relative = os.path.relpath(path, os.path.realpath(base_dir))
    except (OSError, TypeError, ValueError):
        die("source artefact path is not portable")
    portable = relative.replace(os.sep, "/")
    return _checkpoint_safe_relative(tuple(portable.split("/")))


def done_study(args, state: dict) -> None:
    require_global_phase(state, "study")
    artifact = _require_file(args.artifact, "artifact")
    artifact_path, artifact_bytes = read_bounded_source(
        args.dir, artifact, "study artefact"
    )
    artifact = _portable_receipt_artifact(args.dir, artifact_path)
    skills = [s for s in (args.skills or "").split(",") if s]
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    state["receipts"]["study"] = {
        "artifact": artifact,
        "sha256": digest,
        "skills": skills,
    }
    state["phase"] = "runbook"
    commit(
        args.dir,
        state,
        "done:study",
        {"artifact": artifact, "sha256": digest, "skills": skills},
    )
    print("study receipted; phase -> runbook")


def done_runbook(args, state: dict) -> None:
    require_global_phase(state, "runbook")
    artifact = _require_file(args.artifact, "artifact")
    artifact_path, artifact_bytes = read_bounded_source(
        args.dir, artifact, "runbook artefact"
    )
    artifact = _portable_receipt_artifact(args.dir, artifact_path)
    artifact_text = decoded_source(artifact_bytes, "runbook artefact")
    relation_source = parse_version_relation_source(artifact_text)
    version_relations = None
    if relation_source is not None:
        repository = _native_relation_repository_identity(args.dir)
        anchor_commit = relation_anchor_commit(args.dir, state)
        version_relations = capture_version_relations(
            args.dir, relation_source, anchor_commit
        )
        _require_native_relation_history(args.dir)
        if _native_relation_repository_identity(args.dir) != repository:
            die("version relation repository changed during anchor capture")
    steps_file = _require_file(args.steps_file, "steps-file")
    _, steps_bytes = read_bounded_source(args.dir, steps_file, "steps file")
    try:
        raw = json.loads(decoded_source(steps_bytes, "steps file"))
    except ValueError as exc:
        die(f"steps-file is not valid JSON: {exc}")
    if not isinstance(raw, list) or not raw:
        die("steps-file must be a non-empty JSON list")
    titles = []
    for item in raw:
        if isinstance(item, str):
            titles.append(item)
        elif isinstance(item, dict) and isinstance(item.get("title"), str):
            titles.append(item["title"])
        else:
            die("each step must be a string or an object with a 'title'")
    if any(not title.strip() for title in titles):
        die("step titles must be non-empty")
    state["steps"] = [
        {
            "n": i + 1,
            "title": title,
            "status": "pending",
            "phase": None,
            "receipts": {},
            "audit": {"rounds": []},
        }
        for i, title in enumerate(titles)
    ]
    state["steps"][0]["status"] = "open"
    state["steps"][0]["phase"] = "implement"
    state["current_step"] = 1
    state["phase"] = "steps"
    receipt = {"artifact": artifact, "steps": titles}
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    state["receipts"]["runbook"] = {
        "artifact": artifact,
        "sha256": digest,
        "step_count": len(titles),
    }
    if version_relations is not None:
        state["receipts"]["runbook"]["version_relations"] = version_relations
        receipt["version_relations"] = version_relations
    receipt["sha256"] = digest
    commit(args.dir, state, "done:runbook", receipt)
    print(f"runbook receipted; {len(titles)} steps registered; step 1 -> implement")


def done_implement(args, state: dict) -> None:
    # Runs created before issue-free Fiat may still be parked at ``issue``.
    # Treat that legacy phase as implementation-ready and retire it in the
    # implementation receipt rather than forcing a GitHub side effect.
    step = current_step(state)
    require_no_amendment_block(state)
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state["phase"] != "steps" or step["phase"] not in ("issue", "implement"):
        require_step_phase(state, "implement")
    legacy_phase = step["phase"] == "issue"
    if not args.branch or not args.commit:
        die("--branch and --commit are required")
    if run_branch_of(state):
        expected = step_branch_name(state, step)
        if args.branch != expected:
            die(
                f"--branch must be '{expected}', chained off "
                f"'{step_pr_base(state, step)}'; got '{args.branch}'"
            )
    range_base = step_pr_base(state, step) if run_branch_of(state) else state["base"]
    branch_tip = resolved_commit(
        args.dir, args.branch, f"step {step['n']} implementation branch"
    )
    supplied_head = resolved_commit(
        args.dir, args.commit, f"step {step['n']} implementation head"
    )
    if branch_tip != supplied_head:
        die(f"step {step['n']} implementation head is not the declared branch tip")
    verified_commits = verify_local_range(
        args.dir, range_base, args.commit, f"step {step['n']} implementation"
    )
    step["receipts"]["implement"] = {
        "branch": args.branch,
        "commit": args.commit,
        "tests": args.tests,
        "verified_commits": verified_commits,
    }
    step["phase"] = "audit"
    commit(
        args.dir,
        state,
        "done:implement",
        {
            "step": step["n"],
            "branch": args.branch,
            "commit": args.commit,
            "verified_commits": verified_commits,
            "legacy_issue_phase_skipped": legacy_phase,
        },
    )
    print(f"step {step['n']} implementation receipted; phase -> audit")


def audit_risk_ids(base_dir: str, state: dict) -> list[str]:
    """Return the exact ids from Protasis's receipted risk-register block."""
    study = receipted_source(base_dir, state, "study")
    if study is None:
        die("study receipt is unavailable for Covered validation")
    register = source_risk_register(study)["markdown"]
    risk_ids = []
    seen = set()
    for line in register.splitlines()[1:-1]:
        if not line.strip():
            continue
        risk_id = line.split("|", 1)[0].strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", risk_id):
            die("study risk register has an invalid id")
        if risk_id in seen:
            die("study risk register has a duplicate id")
        seen.add(risk_id)
        risk_ids.append(risk_id)
    if not risk_ids:
        die("study risk register has no ids")
    return risk_ids


def audit_baseline_blob(base_dir: str, step: dict, log_path: str) -> bytes:
    """Read the configured log blob at the last locally verified commit."""
    baseline_ref = last_local_commit(step)
    if not isinstance(baseline_ref, str) or not baseline_ref:
        die("audit baseline has no locally verified commit")
    baseline_commit = resolved_commit(
        base_dir, baseline_ref, "audit baseline commit"
    )
    listing = bounded_git(
        base_dir,
        ["ls-tree", "-z", "--full-tree", baseline_commit, "--", log_path],
        "audit baseline path cannot be read from its verified commit",
    )
    if not listing:
        return b""
    if not listing.endswith(b"\0"):
        die("audit baseline path returned an ambiguous Git result")
    entries = [entry for entry in listing.split(b"\0") if entry]
    if len(entries) != 1:
        die("audit baseline path returned an ambiguous Git result")
    metadata, separator, raw_path = entries[0].partition(b"\t")
    match = re.fullmatch(
        rb"(?P<mode>[0-7]{6}) (?P<kind>[a-z]+) "
        rb"(?P<object>[0-9a-f]{40}(?:[0-9a-f]{24})?)",
        metadata,
    )
    try:
        listed_path = raw_path.decode("utf-8")
    except UnicodeDecodeError:
        listed_path = None
    if separator != b"\t" or match is None or listed_path != log_path:
        die("audit baseline path returned an ambiguous Git result")
    if match.group("kind") != b"blob" or match.group("mode") not in (
        b"100644",
        b"100755",
    ):
        die("audit baseline path is not a regular Git blob")
    object_id = match.group("object").decode("ascii")
    size_text = tool_text(
        bounded_git(
            base_dir,
            ["cat-file", "-s", object_id],
            "audit baseline blob size cannot be read",
        ),
        "audit baseline blob size",
    ).strip()
    if not re.fullmatch(r"0|[1-9][0-9]*", size_text):
        die("audit baseline blob size is malformed")
    size = int(size_text)
    if size > SOURCE_BYTES_MAX:
        die(f"audit baseline blob exceeds {SOURCE_BYTES_MAX}-byte cap")
    blob = bounded_git(
        base_dir,
        ["cat-file", "blob", object_id],
        "audit baseline blob cannot be read",
    )
    if len(blob) != size:
        die("audit baseline blob length does not match Git metadata")
    return blob


def audit_delta_start(
    base_dir: str, state: dict, step: dict, log_path: str, data: bytes
) -> int:
    """Choose the durable boundary before the one unreceipted raw suffix."""
    latest_offset = None
    for prior_step in state.get("steps") or []:
        if as_dict(prior_step).get("n") > step["n"]:
            break
        rounds = as_dict(as_dict(prior_step).get("audit")).get("rounds") or []
        for round_entry in rounds:
            entry = as_dict(round_entry)
            if "log_end_offset" not in entry:
                continue
            if entry.get("log") != log_path:
                die("stored audit log path does not match the configured log")
            offset = entry["log_end_offset"]
            if isinstance(offset, bool) or not isinstance(offset, int):
                die("stored audit log end offset must be a non-boolean integer")
            if offset < 0 or offset > SOURCE_BYTES_MAX or offset >= len(data):
                die("stored audit log end offset is outside the current log")
            latest_offset = offset
    if latest_offset is not None:
        return latest_offset

    baseline = audit_baseline_blob(base_dir, step, log_path)
    if len(data) <= len(baseline):
        die("audit log does not append a new record after its Git baseline")
    if data[:len(baseline)] != baseline:
        die("audit log changed before its Git baseline boundary")
    return len(baseline)


def audit_covered(value: str, expected_ids: list[str]) -> None:
    """Check total, unique risk disposition without retaining or printing prose."""
    expected = set(expected_ids)
    dispositions = {}
    for raw in value.split(";"):
        item = raw.strip()
        if not item or item.count("=") != 1:
            die("audit record Covered has a malformed risk disposition")
        risk_id, disposition = (part.strip() for part in item.split("=", 1))
        if risk_id in dispositions:
            die("audit record Covered has a duplicate risk id")
        if risk_id not in expected:
            die("audit record Covered has an unknown risk id")
        if disposition not in AUDIT_COVERAGE_VALUES:
            die("audit record Covered has an invalid disposition")
        dispositions[risk_id] = disposition
    missing = [risk_id for risk_id in expected_ids if risk_id not in dispositions]
    if missing:
        die("audit record Covered is missing a study risk id")


def audit_table_cells(line: str) -> list[str]:
    """Split one raw row at pipes not escaped by an odd backslash run."""
    trailing_slashes = len(line) - 1 - len(line[:-1].rstrip("\\"))
    if (
        len(line) < 2
        or not line.startswith("|")
        or not line.endswith("|")
        or trailing_slashes % 2
    ):
        return []
    cells = []
    start = 1
    slashes = 0
    for index, char in enumerate(line[1:-1], 1):
        if char == "|" and slashes % 2 == 0:
            cells.append(line[start:index].strip())
            start = index + 1
        slashes = slashes + 1 if char == "\\" else 0
    cells.append(line[start:-1].strip())
    return cells


def audit_raw_field(line: str, label: str) -> str:
    """Read one exact raw field line without exposing its value."""
    prefix = f"{label}: "
    if not line.startswith(prefix):
        die(f"audit record is missing or malformed {label}")
    value = line[len(prefix):]
    if not value or not value.strip() or value != value.strip():
        die(f"audit record {label} must have a canonical non-empty value")
    return value


def audit_record_bytes(data: bytes, start: int) -> bytes:
    """Return the exact LF-only record after its boundary separator."""
    if start == 0:
        separator = b""
    elif data[start - 1:start] == b"\n":
        separator = b"\n"
    else:
        separator = b"\n\n"
    delta = data[start:]
    if not delta.startswith(separator):
        die("audit record has a non-canonical boundary separator")
    record = delta[len(separator):]
    if not record or b"\r" in delta:
        die("audit record must use LF line endings")
    if not record.endswith(b"\n"):
        die("audit record must end with one LF at EOF")
    for physical in record.split(b"\n"):
        if len(physical) > AUDIT_PHYSICAL_LINE_BYTES_MAX:
            die(
                "audit record has a physical line over "
                f"{AUDIT_PHYSICAL_LINE_BYTES_MAX}-byte cap"
            )
    return record


def audit_line(lines: list[str], index: int, expected: str, label: str) -> int:
    """Consume one exact line from the raw record grammar."""
    if index >= len(lines) or lines[index] != expected:
        die(f"audit record has a non-canonical {label}")
    return index + 1


def audit_field_line(
    lines: list[str], index: int, label: str
) -> tuple[int, str]:
    if index >= len(lines):
        die(f"audit record is missing {label}")
    return index + 1, audit_raw_field(lines[index], label)


def parse_audit_record(
    record: bytes, base_dir: str, state: dict, step: dict, args
) -> tuple[str, str]:
    """Validate the one exact raw suffix and return schema and timestamp."""
    try:
        text = record.decode("utf-8")
    except UnicodeDecodeError:
        die("audit record delta is not UTF-8 text")
    lines = text[:-1].split("\n")
    round_number = len(step["audit"]["rounds"]) + 1
    if not lines:
        die("audit record is empty")
    heading = lines[0]
    index = 1
    index = audit_line(lines, index, "", "blank line after heading")
    index, schema = audit_field_line(lines, index, "Audit schema")
    if schema not in AUDIT_RECORD_SCHEMAS:
        die("Audit schema must be " + " or ".join(AUDIT_RECORD_SCHEMAS))
    if schema == "fiat-audit-round/v1":
        heading_prefix = (
            f"## {state['topic']}, step {step['n']}, round {round_number} -- "
        )
    else:
        heading_prefix = f"## Step {step['n']}, round {round_number} -- "
    if not heading.startswith(heading_prefix):
        die("audit record heading does not match its schema, step, and round")
    timestamp = heading[len(heading_prefix):]
    if not AUDIT_TIMESTAMP_RE.fullmatch(timestamp):
        die("audit record timestamp must be YYYY-MM-DDTHH:MM:SSZ UTC")
    try:
        parsed_timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        die("audit record timestamp is not calendar-valid")
    if parsed_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") != timestamp:
        die("audit record timestamp is not canonical UTC")
    index = audit_line(lines, index, "", "blank line after Audit schema")
    index, covered = audit_field_line(lines, index, "Covered")
    audit_covered(covered, audit_risk_ids(base_dir, state))
    index = audit_line(lines, index, "", "blank line after Covered")
    index, _ = audit_field_line(lines, index, "Not checked")
    index = audit_line(lines, index, "", "blank line after Not checked")
    index, verdict = audit_field_line(lines, index, "Elenchus verdict")
    expected_verdict = args.elenchus_verdict or "null"
    if verdict != expected_verdict:
        die("audit record Elenchus verdict does not match the receipt")
    index = audit_line(lines, index, "", "blank line after Elenchus verdict")
    index = audit_line(
        lines, index, AUDIT_FINDINGS_HEADER, "findings table header"
    )
    index = audit_line(
        lines, index, AUDIT_FINDINGS_SEPARATOR, "findings table separator"
    )

    row_count = 1 if args.findings == 0 else args.findings
    rows = []
    for _ in range(row_count):
        if index >= len(lines):
            die("audit record findings table row count does not match --findings")
        row = lines[index]
        cells = audit_table_cells(row)
        if len(cells) != 5 or any(not cell for cell in cells):
            die("audit record findings table has a malformed data row")
        rows.append(row)
        index += 1
    if args.findings == 0:
        if rows != [AUDIT_ZERO_FINDING_ROW]:
            die("audit record findings table must use the exact zero-finding row")
    elif AUDIT_ZERO_FINDING_ROW in rows:
        die("audit record findings table row count does not match --findings")
    if index >= len(lines) or lines[index] != "":
        die("audit record findings table row count does not match --findings")
    index += 1
    index, _ = audit_field_line(lines, index, "Leads not pursued")
    if index != len(lines):
        die("audit record has content after Leads not pursued")
    return schema, timestamp


def validated_audit_record(
    base_dir: str, state: dict, step: dict, args
) -> dict:
    """Validate one raw Warden append and return only receipt-safe evidence."""
    audit = as_dict(as_dict(state.get("config")).get("audit"))
    log_path, data = read_configured_audit_log(
        base_dir, audit.get("log_path"), args.log
    )
    entry_start = audit_delta_start(base_dir, state, step, log_path, data)
    entry_bytes = audit_record_bytes(data, entry_start)
    schema, timestamp = parse_audit_record(
        entry_bytes, base_dir, state, step, args
    )
    synopsis_path = os.path.join(
        os.path.dirname(__file__), "audit_synopsis.py"
    )
    if not os.path.isfile(synopsis_path):
        refuse_audit_renderer("audit synopsis renderer is unavailable")
    try:
        specification = importlib.util.spec_from_file_location(
            "fiat_audit_synopsis", synopsis_path
        )
        if specification is None or specification.loader is None:
            raise ImportError("renderer has no executable module specification")
        renderer = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(renderer)
    except (Exception, SystemExit):
        refuse_audit_renderer("audit synopsis renderer cannot be loaded")
    try:
        synopsis_validator = getattr(renderer, "validate_committed_synopsis", None)
        synopsis_error = getattr(renderer, "SynopsisError", None)
    except (Exception, SystemExit):
        refuse_audit_renderer("audit synopsis renderer cannot be loaded")
    try:
        interface_valid = (
            callable(synopsis_validator)
            and isinstance(synopsis_error, type)
            and issubclass(synopsis_error, Exception)
        )
    except (Exception, SystemExit):
        refuse_audit_renderer("audit synopsis renderer cannot be loaded")
    if not interface_valid:
        refuse_audit_renderer("audit synopsis renderer cannot be loaded")
    try:
        synopsis_sha256 = synopsis_validator(base_dir, log_path, data)
    except synopsis_error as error:
        refuse_audit_renderer(error)
    except SystemExit:
        refuse_audit_renderer(
            "audit synopsis renderer validation terminated unexpectedly"
        )
    try:
        digest_valid = (
            isinstance(synopsis_sha256, str)
            and re.fullmatch(r"[0-9a-f]{64}", synopsis_sha256) is not None
        )
    except (Exception, SystemExit):
        refuse_audit_renderer("audit synopsis renderer returned an invalid digest")
    if not digest_valid:
        refuse_audit_renderer("audit synopsis renderer returned an invalid digest")
    return {
        "schema": schema,
        "log": log_path,
        "record_timestamp": timestamp,
        "entry_sha256": hashlib.sha256(entry_bytes).hexdigest(),
        "log_end_offset": len(data),
        "synopsis_sha256": synopsis_sha256,
    }


def cmd_audit_round(args) -> None:
    state = load_state(args.dir)
    step = require_step_phase(state, "audit")
    if args.audit_filter is None:
        die(
            "audit-round requires --audit-filter sapheneia:sapheneia; "
            "the declaration must precede every new round receipt"
        )
    if args.audit_filter != AUDIT_FILTER:
        die("--audit-filter must equal sapheneia:sapheneia")
    if "security_suite" not in state["receipts"]:
        die(
            "no security_suite receipt; resolve the installed suite first "
            "(`hexctl record security_suite '<ids or waived:reason>'`)"
        )
    rounds = step["audit"]["rounds"]
    max_rounds = max_rounds_of(state)
    if len(rounds) >= max_rounds:
        die(
            f"max audit rounds ({max_rounds}) reached for step {step['n']}; "
            "close with `done audit --no-further-leads --reason ...` or `halt`"
        )
    if args.findings is None or args.findings < 0:
        die("--findings must be a non-negative integer")
    if args.fixes_commit and args.elenchus_verdict is None:
        die(
            "--elenchus-verdict is required with --fixes-commit; accepted values: "
            + ", ".join(ELENCHUS_VERDICTS)
        )
    if args.elenchus_verdict is not None and not args.fixes_commit:
        die("--elenchus-verdict requires --fixes-commit")
    recorded_log = (
        check_declared_audit_log(state, args.log, "this round")
        if args.log is not None
        else configured_audit_log(state)
    )

    exits = {lint: getattr(args, f"{lint}_exit", None) for lint in LINTS}
    for lint, value in exits.items():
        if value is not None and value < 0:
            die(f"--{lint}-exit must be a non-negative exit status, got {value}")

    if not solidity_round(state):
        absent = [f"--{lint}-exit" for lint in LINTS if exits[lint] is None]
        if absent:
            one = len(absent) == 1
            die(
                "this round runs the three bundled lints, so it still needs "
                + ", ".join(absent)
                + "; a round recorded without "
                + ("that" if one else "them")
                + " cannot say whether "
                + ("it ran" if one else "they ran")
                + " (see references/audit-loop.md; the security_suite receipt must "
                "classify the run before audit because Solidity config is immutable)"
            )

    recorded = {lint: value for lint, value in exits.items() if value is not None}
    dirty = sorted(lint for lint, value in recorded.items() if value)
    if dirty and args.findings == 0:
        die(
            "round reports 0 findings while "
            + ", ".join(f"{lint} exited {recorded[lint]}" for lint in dirty)
            + "; a non-zero lint exit is a finding like any other"
        )

    record = validated_audit_record(args.dir, state, step, args)

    verified_commits = []
    if args.fixes_commit:
        base = last_local_commit(step)
        if not base:
            die(f"step {step['n']} has no verified implementation commit")
        verified_commits = verify_local_range(
            args.dir, base, args.fixes_commit, f"step {step['n']} audit fixes"
        )
    entry = {
        "round": len(rounds) + 1,
        "findings": args.findings,
        "log": recorded_log,
        "audit_filter": args.audit_filter,
        "fixes_commit": args.fixes_commit,
        "elenchus_verdict": args.elenchus_verdict,
        "verified_commits": verified_commits,
        "lints": recorded or None,
        "ts": now(),
        **record,
    }
    rounds.append(entry)
    commit(args.dir, state, "audit-round", {"step": step["n"], **entry})
    tail = ""
    if recorded:
        tail = "; lints " + ", ".join(
            f"{lint} {recorded[lint]}" for lint in LINTS if lint in recorded
        )
    tail += f"; audit filter {entry['audit_filter']}"
    tail += f"; Elenchus {entry['elenchus_verdict'] or 'null'}"
    print(
        f"step {step['n']} audit round {entry['round']} recorded "
        f"({args.findings} finding(s)){tail}"
    )


def done_audit(args, state: dict) -> None:
    step = require_step_phase(state, "audit")
    if "security_suite" not in state["receipts"]:
        die("no security_suite receipt; the audit phase never legitimately ran")
    rounds = step["audit"]["rounds"]
    if not rounds:
        die("no audit rounds recorded; run at least one round before closing")
    last = rounds[-1]
    strict_log = last.get("schema") in AUDIT_RECORD_SCHEMAS
    if strict_log and args.log is not None and args.log != last.get("log"):
        die(
            f"--log names '{args.log}', but the final round's checked audit "
            f"log is '{last.get('log')}'"
        )
    clean = last["findings"] == 0
    if not clean and not args.no_further_leads:
        die(
            f"last round left {last['findings']} finding(s) open; either run "
            "another round or close with --no-further-leads --reason ..."
        )
    if args.no_further_leads and not args.reason:
        die("--no-further-leads requires --reason")
    if args.log is not None:
        closing_log = check_declared_audit_log(
            state, args.log, "this step's audit"
        )
    else:
        # A round recorded before this check keeps the value it holds; nothing
        # rewrites a receipt that is already on the ledger. Config is read only
        # when there is nothing recorded to keep, so a closure that needs
        # nothing from it is not refused by it.
        closing_log = last.get("log") or configured_audit_log(state)
    had_findings = any(r["findings"] > 0 for r in rounds)
    fixes_ref = args.fixes_ref or next(
        (r["fixes_commit"] for r in reversed(rounds) if r.get("fixes_commit")), None
    )
    if had_findings and not fixes_ref:
        die(
            "findings were recorded but no fixes reference exists; pass "
            "--fixes-ref or record fixes commits on the rounds"
        )
    verified_fixes = []
    recorded_fix = next(
        (r.get("fixes_commit") for r in reversed(rounds) if r.get("fixes_commit")),
        None,
    )
    if fixes_ref and fixes_ref != recorded_fix:
        base = last_local_commit(step)
        if not base:
            die(f"step {step['n']} has no verified commit before its fixes reference")
        verified_fixes = verify_local_range(
            args.dir, base, fixes_ref, f"step {step['n']} audit closure fixes"
        )
    step["receipts"]["audit"] = {
        "rounds": len(rounds),
        "clean": clean,
        "no_further_leads": bool(args.no_further_leads),
        "reason": args.reason,
        "fixes_ref": fixes_ref,
        "log": closing_log,
        "verified_fixes": verified_fixes,
    }
    step["phase"] = "prose"
    commit(
        args.dir,
        state,
        "done:audit",
        {"step": step["n"], **step["receipts"]["audit"]},
    )
    print(f"step {step['n']} audit receipted; phase -> prose")


def done_prose(args, state: dict) -> None:
    step = require_step_phase(state, "prose")
    if args.files is None or args.files < 0:
        die("--files must be a non-negative integer")
    applied = {s for s in (args.skills or "").split(",") if s}
    required = {
        str(state["config"]["skills"]["prose_lint"]),
        str(state["config"]["skills"]["voice"]),
    }
    missing = sorted(required - applied)
    if missing:
        die(f"prose pass is missing required skill(s): {', '.join(missing)}")
    step["receipts"]["prose"] = {"files": args.files, "skills": sorted(applied)}
    step["phase"] = "push"
    commit(
        args.dir,
        state,
        "done:prose",
        {"step": step["n"], "files": args.files, "skills": sorted(applied)},
    )
    print(f"step {step['n']} prose pass receipted; phase -> push")


def done_push(args, state: dict) -> None:
    step = require_step_phase(state, "push")
    if not args.pr_url:
        die("--pr-url is required")
    if not args.head_commit:
        die("--head-commit is required")
    stacked = run_branch_of(state) is not None
    expected_issue = expected_task_issue(state)
    if stacked:
        expected_base = step_pr_base(state, step)
        if not args.pr_base:
            die(
                f"--pr-base is required; this step's pull request targets "
                f"'{expected_base}', never the repository default branch"
            )
        if args.pr_base != expected_base:
            die(f"--pr-base must be '{expected_base}'; got '{args.pr_base}'")
        if args.merge_commit:
            die(
                "a step pull request does not merge during the run; the stack "
                "merges in step order in the integrate phase"
            )
        if args.closed_issue_url:
            die(
                "a recorded task issue closes in the integrate phase, once the "
                "run branch lands on the base"
            )
    else:
        if not args.merge_commit:
            die(
                "--merge-commit is required; the pull request is not terminal "
                "until merged"
            )
        if state["receipts"].get("task_issue") is not None and not args.closed_issue_url:
            die("--closed-issue-url is required because a task_issue receipt exists")
        if expected_issue and args.closed_issue_url != expected_issue:
            die(
                "--closed-issue-url does not match the recorded task_issue "
                f"({expected_issue})"
            )
    range_base = args.pr_base if stacked else state["base"]
    branch = (
        step_branch_name(state, step)
        if stacked
        else as_dict(step["receipts"].get("implement")).get("branch")
    )
    if not isinstance(branch, str) or not branch:
        die("step push has no recorded implementation branch")
    branch_tip = resolved_commit(args.dir, branch, f"step {step['n']} pushed branch")
    supplied_head = resolved_commit(args.dir, args.head_commit, f"step {step['n']} push head")
    if branch_tip != supplied_head:
        die(f"step {step['n']} push head is not the pushed branch tip")
    verified_commits = verify_local_range(
        args.dir, range_base, args.head_commit, f"step {step['n']} push"
    )
    pr_record = inspect_pull_request(
        args.dir,
        args.pr_url,
        expected_head=branch,
        expected_base=(args.pr_base if stacked else state["base"]),
        expected_head_sha=verified_commits[-1],
        expected_merge_sha=args.merge_commit,
        expected_closing_issue=(expected_issue if not stacked else None),
    )
    github_verified, attribution = verified_github_attribution(
        args.dir, verified_commits
    )
    merge_verified = []
    if args.merge_commit:
        merge_verified = verify_github_commits(args.dir, [args.merge_commit])
    step["receipts"]["push"] = {
        "pr_url": args.pr_url,
        # The resolved identity, not the argument. `--head-commit` accepts any
        # ref git resolves, including an abbreviated SHA, and the merge-order
        # check at integration compares this value to a full branch tip. Storing
        # what was typed lets a short SHA read as a rewritten branch five steps
        # later, with no way back: `done push` refuses once the run has left the
        # steps phase, and the ledger is append-only.
        "head_commit": supplied_head,
        "pr_base": args.pr_base,
        "merge_commit": args.merge_commit,
        "closed_issue_url": args.closed_issue_url,
        "verified_commits": verified_commits,
        "github_verified": github_verified,
        "github_merge_verified": merge_verified,
        "pull_request": pr_record,
        "attribution": {
            "pull_request_author": pr_record.get("author_login"),
            "commits": attribution,
        },
    }
    step["status"] = "done"
    step["phase"] = "done"
    remaining = [s for s in state["steps"] if s["status"] == "pending"]
    if remaining:
        nxt = remaining[0]
        nxt["status"] = "open"
        nxt["phase"] = "implement"
        state["current_step"] = nxt["n"]
        tail = f"step {nxt['n']} -> implement"
    else:
        state["current_step"] = None
        if stacked:
            state["phase"] = "integrate"
            state["integrate"] = {"merged": [], "merges": {}}
            tail = f"stack complete; merge it into {run_branch_of(state)}"
        else:
            state["phase"] = "done"
            tail = "all steps done"
    commit(
        args.dir,
        state,
        "done:push",
        {"step": step["n"], **step["receipts"]["push"]},
    )
    if stacked:
        print(
            f"step {step['n']} pushed and stacked on '{args.pr_base}'; {tail}"
        )
    else:
        print(f"step {step['n']} published, merged, and receipted; {tail}")


def _integrate_directive(
    state: dict,
    base_dir: str | None = None,
    *,
    check_resolution: bool = True,
) -> dict:
    """Merge the stack bottom up, then the run branch into the base once."""
    run_branch = run_branch_of(state)
    integration_base = integration_base_of(state)
    merged = as_dict(state.get("integrate")).get("merged") or []
    for step in state["steps"]:
        if step["n"] in merged:
            continue
        pr_url = as_dict(step["receipts"].get("push")).get("pr_url")
        return {
            "do": "merge-step",
            "step": step["n"],
            "title": step["title"],
            "branch": step_branch_name(state, step),
            "pr_url": pr_url,
            "into": run_branch,
            "merge": step_merge_command(pr_url),
            "then": (
                f"hexctl done merge-step --step {step['n']} "
                "--merge-commit <sha>"
            ),
        }
    then = "hexctl done integrate --pr-url <url> --merge-commit <sha>"
    task_issue = expected_task_issue(state)
    if task_issue:
        then += " --closed-issue-url <url>"
    final_step = state["steps"][-1]["n"]
    merge_records = as_dict(as_dict(state.get("integrate")).get("merges"))
    final_head = require_full_sha(
        as_dict(merge_records.get(str(final_step))).get("merge_commit"),
        "final recorded product head",
    )
    sync = as_dict(as_dict(state.get("integrate")).get("sync"))
    sync_then = (
        "hexctl done sync-run --commit <signed-merge-sha> "
        "--base-commit <remote-base-sha> "
        f"--revalidation {INTEGRATION_REVALIDATION_FILE} "
        "[--acknowledge-sync-path <exact-risk-path> ...]"
    )
    sync_recovery = "sync-run-and-revalidate"
    if sync:
        active_sync = require_full_sha(
            sync.get("commit"), "active recorded sync commit"
        )
        sync_then += (
            f" --supersede-sync {active_sync} "
            "--reason <bounded-repair-reason>"
        )
        sync_recovery = "supersede-sync-and-revalidate"
    resolution = None
    relations = as_dict(as_dict(state.get("receipts")).get("runbook")).get(
        "version_relations"
    )
    if relations is not None and check_resolution:
        history = as_dict(state.get("integrate")).get("version_resolutions")
        if not isinstance(history, list) or not history:
            return {
                "do": "resolve-versions",
                "run_branch": run_branch,
                "base": integration_base,
                "starting_base": state["base"],
                "reason": "the relation-bearing run has no exact base/head resolution",
                "then": "hexctl done resolve-versions",
                "recovery": (
                    "if the base advanced, first use the existing signed "
                    "product/base sync with complete integration revalidation"
                ),
            }
        if base_dir is None:
            die("version resolution freshness needs the run worktree", 1)
        resolution = active_version_resolution(base_dir, state)
    directive = {
        "do": "integrate",
        "run_branch": run_branch,
        "base": integration_base,
        "starting_base": state["base"],
        "steps": len(state["steps"]),
        "product_evidence": product_evidence_record(state, final_head),
        "base_advance": {
            "recovery": sync_recovery,
            "artifact": INTEGRATION_REVALIDATION_FILE,
            "then": sync_then,
            "resolution_guard": {
                "schema": SYNC_RESOLUTION_GUARD_SCHEMA,
                "flag": "--acknowledge-sync-path",
                "rule": (
                    "repeat the flag for the exact sorted paths named by the "
                    "controller; acknowledgement records inspection and does "
                    "not replace revalidation"
                ),
            },
            "boundary": (
                "base advancement alone does not authorise a carryover, "
                "invalidate the exact-tree product evidence, or permit a "
                "whole-side or unreviewed rebuilt resolution"
            ),
        },
        "attribution": {
            "recorded_identities": len(recorded_run_attribution(state)),
            "preserved_by": (
                "a merge commit, which leaves every recorded commit reachable "
                "from the base; a squash or rebase merge rewrites them, and "
                "then the merge commit itself has to carry each identity as "
                "author or in a Co-authored-by trailer"
            ),
        },
        **({"version_resolution": resolution} if resolution is not None else {}),
        "then": then,
    }
    identity = github_issue_identity(task_issue)
    if identity is not None:
        issue_repository, issue_number = identity
        directive["task_issue_closure"] = {
            "issue": task_issue,
            "required_before_merge": f"Closes {issue_repository}#{issue_number}",
            "gate": (
                "done integrate reads the final pull request body and refuses "
                "without a recognised closing reference to this exact issue"
            ),
        }
    return directive


def product_evidence_record(state: dict, product_head: str) -> dict:
    """Digest the completed product receipts without reclassifying them.

    These digests establish only that the same implementation and audit records
    remain attached to the exact product head. A later sync adds composition
    evidence; it does not make the earlier audit apply to changed bytes.
    """
    records = []
    for step in state["steps"]:
        payload = {
            "implement": as_dict(step["receipts"].get("implement")),
            "audit": as_dict(step.get("audit")),
            "audit_receipt": as_dict(step["receipts"].get("audit")),
        }
        records.append(
            {
                "step": step["n"],
                "sha256": hashlib.sha256(
                    canonical(payload).encode("utf-8")
                ).hexdigest(),
            }
        )
    receipts = as_dict(state.get("receipts"))
    return {
        "status": "preserved-exact-tree",
        "head": require_full_sha(product_head, "final recorded product head"),
        "study_sha256": as_dict(receipts.get("study")).get("sha256"),
        "runbook_sha256": as_dict(receipts.get("runbook")).get("sha256"),
        "steps": records,
    }


def merge_base_commit(base_dir: str, product_head: str, base_head: str) -> str:
    """Use the same replacement-free merge base stored evidence replays."""
    return _native_relation_merge_base(base_dir, product_head, base_head)


def git_diff_paths(base_dir: str, before: str, after: str) -> list[str]:
    """The integration path delta, read free of replacement and rename drift."""
    return _native_diff_paths(
        base_dir,
        before,
        after,
        "integration path delta",
        "could not read the integration path delta",
    )

def git_diff_paths_for_aggregates(
    base_dir: str, before: str, after: str
) -> list[str]:
    """Read one complete bounded delta before aggregate classification.

    Version 1 continues through ``git_diff_paths`` and its integration refusal.
    Version 2 may cross that count only because a later exact registry join
    classifies the excess. The existing byte and time ceilings still bound the
    Git read, and this reader keeps the same path grammar and diagnostics.
    """
    raw = bounded_git(
        base_dir,
        ["diff", "--name-only", "-z", f"{before}..{after}", "--"],
        "could not read the integration path delta",
    )
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        die("integration path delta is not UTF-8")
    paths = [path for path in decoded.split("\0") if path]
    unique = sorted(set(paths))
    if len(unique) != len(paths):
        die("integration path delta contains duplicate paths")
    for index, path in enumerate(unique):
        if (
            not path
            or os.path.isabs(path)
            or path in (".", "..")
            or ".." in path.split("/")
            or any(ord(character) < 32 or ord(character) == 127 for character in path)
        ):
            die(f"integration path delta contains an unsafe path at index {index}")
    return unique


def _strict_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate object key")
        result[key] = value
    return result


def _manifest_paths(value, label: str, allowed: set[str] | None = None) -> list[str]:
    if not isinstance(value, list) or len(value) > INTEGRATION_PATHS_MAX:
        die(f"{label} must be an array of at most {INTEGRATION_PATHS_MAX} paths")
    if any(not isinstance(path, str) for path in value):
        die(f"{label} must contain only path strings")
    if value != sorted(set(value)):
        die(f"{label} must be sorted and unique")
    for index, path in enumerate(value):
        try:
            encoded = path.encode("utf-8")
        except UnicodeEncodeError:
            die(f"{label} contains a non-Unicode-scalar path at index {index}")
        if (
            not path
            or len(encoded) > 4096
            or os.path.isabs(path)
            or path in (".", "..")
            or ".." in path.split("/")
            or any(ord(character) < 32 or ord(character) == 127 for character in path)
        ):
            die(f"{label} contains an unsafe path at index {index}")
        if allowed is not None and path not in allowed:
            die(f"{label} names a path outside the computed integration delta")
    return value


def _sync_tree_path_batches(paths: list[str]) -> list[list[str]]:
    """Keep literal ls-tree argv below one explicit path and byte envelope."""
    batches = []
    current = []
    current_bytes = 0
    for path in paths:
        token_bytes = len(f":(literal){path}".encode("utf-8")) + 1
        if current and (
            len(current) >= SYNC_TREE_PATH_BATCH_MAX
            or current_bytes + token_bytes > SYNC_TREE_ARG_BYTES_MAX
        ):
            batches.append(current)
            current = []
            current_bytes = 0
        current.append(path)
        current_bytes += token_bytes
    if current:
        batches.append(current)
    return batches


def _sync_tree_entries(
    base_dir: str, commit_sha: str, paths: list[str], label: str
) -> dict[str, str | None]:
    """Read exact tree-entry identities for literal paths at one native commit."""
    commit_sha = require_full_sha(commit_sha, f"{label} commit")
    paths = _manifest_paths(paths, f"{label} paths")
    identities = {path: None for path in paths}
    for batch in _sync_tree_path_batches(paths):
        literal_pathspecs = [f":(literal){path}" for path in batch]
        raw = _native_relation_git(
            base_dir,
            ["ls-tree", "-z", "--full-tree", commit_sha, "--", *literal_pathspecs],
            f"{label} tree entries cannot be read",
        )
        batch_set = set(batch)
        seen = set()
        for record in raw.split(b"\0"):
            if not record:
                continue
            metadata, separator, path_bytes = record.partition(b"\t")
            fields = metadata.split()
            try:
                path = path_bytes.decode("utf-8")
                mode, kind, object_id = [field.decode("ascii") for field in fields]
            except (UnicodeDecodeError, ValueError):
                die(f"{label} tree entries are malformed")
            if (
                separator != b"\t"
                or path not in batch_set
                or path in seen
                or re.fullmatch(r"[0-7]{6}", mode) is None
                or kind not in {"blob", "tree", "commit"}
                or COMMIT_RE.fullmatch(object_id) is None
            ):
                die(f"{label} tree entries are malformed")
            seen.add(path)
            identities[path] = f"{mode} {kind} {object_id}"
    return identities


def _active_sync_predecessor(integrate: dict, active_commit: str) -> dict | None:
    """Return the sync immediately superseded by the active receipt."""
    history = integrate.get("superseded_syncs") or []
    if not isinstance(history, list):
        die("recorded superseded integration syncs are malformed")
    if not history:
        return None
    tail = history[-1]
    previous = tail.get("sync") if isinstance(tail, dict) else None
    if (
        not isinstance(previous, dict)
        or tail.get("superseded_by") != active_commit
    ):
        die("active integration sync is not joined to its supersession history")
    return previous


def sync_resolution_guard_record(
    base_dir: str,
    product_head: str,
    base_head: str,
    sync_head: str,
    *,
    current_sync: dict | None,
    acknowledgements: list[str],
) -> dict:
    """Expose whole-side and rebuild-loss paths before a sync is receipted."""
    product_head = require_full_sha(product_head, "sync resolution product head")
    base_head = require_full_sha(base_head, "sync resolution base head")
    sync_head = require_full_sha(sync_head, "sync resolution sync head")
    acknowledgements = _manifest_paths(
        acknowledgements, "--acknowledge-sync-path values"
    )

    base_before = merge_base_commit(base_dir, product_head, base_head)
    product_paths = git_diff_paths(base_dir, base_before, product_head)
    base_paths = git_diff_paths(base_dir, base_before, base_head)
    overlap_paths = sorted(set(product_paths) & set(base_paths))
    product_entries = _sync_tree_entries(
        base_dir, product_head, overlap_paths, "sync resolution product"
    )
    base_entries = _sync_tree_entries(
        base_dir, base_head, overlap_paths, "sync resolution base"
    )
    sync_entries = _sync_tree_entries(
        base_dir, sync_head, overlap_paths, "sync resolution result"
    )
    side_selected_paths = [
        path
        for path in overlap_paths
        if product_entries[path] != base_entries[path]
        and sync_entries[path] in {product_entries[path], base_entries[path]}
    ]

    superseded_intersection_paths = []
    if current_sync is not None:
        if not isinstance(current_sync, dict):
            die("active integration sync is malformed")
        old_sync = require_full_sha(
            current_sync.get("commit"), "active recorded sync commit"
        )
        old_base = require_full_sha(
            current_sync.get(SYNC_BASE_HEAD_KEY), "active recorded sync base"
        )
        if _native_relation_parents(
            base_dir, old_sync, "active recorded sync commit"
        ) != [product_head, old_base]:
            die("active recorded sync parents do not match product and old base")
        old_composition_paths = git_diff_paths(base_dir, product_head, old_sync)
        base_advance_paths = git_diff_paths(base_dir, old_base, base_head)
        superseded_intersection_paths = sorted(
            set(old_composition_paths) & set(base_advance_paths)
        )

    required = sorted(
        set(side_selected_paths) | set(superseded_intersection_paths)
    )
    if acknowledgements != required:
        missing = sorted(set(required) - set(acknowledgements))
        extra = sorted(set(acknowledgements) - set(required))
        die(
            "integration sync resolution acknowledgements do not match; "
            f"missing {json.dumps(missing, ensure_ascii=False)}; "
            f"extra {json.dumps(extra, ensure_ascii=False)}; repeat "
            "--acknowledge-sync-path once for each required path in this "
            f"exact order: {json.dumps(required, ensure_ascii=False)}"
        )
    return {
        "schema": SYNC_RESOLUTION_GUARD_SCHEMA,
        "side_selected_paths": side_selected_paths,
        "superseded_intersection_paths": superseded_intersection_paths,
        "acknowledged_paths": acknowledgements,
    }


def _require_sync_resolution_guard(
    base_dir: str,
    sync: dict,
    product_head: str,
    *,
    previous_sync: dict | None,
) -> dict:
    """Recompute one stored guard from its immutable Git objects."""
    guard = sync.get("resolution_guard")
    if (
        not isinstance(guard, dict)
        or set(guard) != SYNC_RESOLUTION_GUARD_KEYS
        or guard.get("schema") != SYNC_RESOLUTION_GUARD_SCHEMA
    ):
        die(
            "active integration sync has no current resolution guard; "
            "supersede it with a fresh signed and revalidated sync"
        )
    for field in (
        "side_selected_paths",
        "superseded_intersection_paths",
        "acknowledged_paths",
    ):
        _manifest_paths(guard.get(field), f"sync resolution guard {field}")
    expected = sync_resolution_guard_record(
        base_dir,
        product_head,
        sync.get(SYNC_BASE_HEAD_KEY),
        sync.get("commit"),
        current_sync=previous_sync,
        acknowledgements=guard["acknowledged_paths"],
    )
    if guard != expected:
        die("active integration sync resolution guard does not replay")
    return expected


def _sha256_value(value, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        die(f"{label} must be a lowercase SHA-256 digest")
    return value


def _aggregate_relative_path(value, label: str) -> str:
    if not isinstance(value, str):
        die(f"{label} must be a path string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        encoded = b""
    if (
        not encoded
        or len(encoded) > 4096
        or os.path.isabs(value)
        or value in (".", "..")
        or ".." in value.split("/")
        or value.startswith("./")
        or value.endswith("/")
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        die(f"{label} is unsafe")
    return value


def _git_tree_record(raw: bytes, label: str) -> tuple[str, str, str, str]:
    try:
        metadata, path_bytes = raw.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii", "strict").split(" ")
        path = path_bytes.decode("utf-8", "strict")
    except (UnicodeError, ValueError):
        die(f"{label} has malformed Git tree metadata")
    if re.fullmatch(r"[0-9a-f]{40}", object_id) is None:
        die(f"{label} has a malformed Git object id")
    return mode, kind, object_id, path


def _git_aggregate_tree(
    base_dir: str, sync_head: str, aggregate_id: str, registry: dict
) -> tuple[str, list[dict]]:
    prefix = registry["prefix"]
    tree_path = prefix.removesuffix("/")
    root_raw = bounded_git(
        base_dir,
        ["ls-tree", "-z", sync_head, "--", tree_path],
        f"generator aggregate {aggregate_id} tree could not be read",
    )
    root_rows = [row for row in root_raw.split(b"\0") if row]
    if len(root_rows) != 1:
        die(f"generator aggregate {aggregate_id} prefix is not one Git tree")
    mode, kind, tree_id, path = _git_tree_record(
        root_rows[0], f"generator aggregate {aggregate_id} prefix"
    )
    if path != tree_path or mode != "040000" or kind != "tree":
        die(f"generator aggregate {aggregate_id} prefix is not a Git tree")

    raw = bounded_git(
        base_dir,
        ["ls-tree", "-r", "-z", "--full-tree", sync_head, "--", prefix],
        f"generator aggregate {aggregate_id} contents could not be read",
    )
    rows = []
    for index, encoded in enumerate(row for row in raw.split(b"\0") if row):
        mode, kind, object_id, member = _git_tree_record(
            encoded, f"generator aggregate {aggregate_id} member {index}"
        )
        if not member.startswith(prefix):
            die(f"generator aggregate {aggregate_id} escaped its registered prefix")
        _aggregate_relative_path(
            member, f"generator aggregate {aggregate_id} member {index}"
        )
        if kind != "blob":
            die(f"generator aggregate {aggregate_id} member {member} is not a blob")
        if mode not in ("100644", "100755"):
            die(f"generator aggregate {aggregate_id} member {member} has an unsafe mode")
        rows.append(
            {"path": member, "mode": mode, "object": object_id}
        )
    paths = [row["path"] for row in rows]
    if paths != sorted(set(paths)):
        die(f"generator aggregate {aggregate_id} Git tree paths are not sorted and unique")
    if not rows:
        die(f"generator aggregate {aggregate_id} Git tree is empty")
    if len(rows) > registry["max_files"]:
        die(
            f"generator aggregate {aggregate_id} exceeds its "
            f"{registry['max_files']}-file ceiling"
        )
    return tree_id, rows


def _git_batch_blobs(
    base_dir: str, aggregate_id: str, rows: list[dict], max_bytes: int
) -> dict[str, bytes]:
    """Read every final aggregate blob through one bounded batch process."""
    requests = b"".join(row["object"].encode("ascii") + b"\n" for row in rows)
    try:
        process = subprocess.Popen(
            ["git", "cat-file", "--batch"],
            cwd=os.path.realpath(base_dir),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
        )
    except OSError:
        die(f"generator aggregate {aggregate_id} Git object batch could not start")
    assert process.stdin is not None
    assert process.stdout is not None
    try:
        process.stdin.write(requests)
        process.stdin.close()
    except (BrokenPipeError, OSError):
        process.kill()
        process.wait()
        process.stdout.close()
        die(f"generator aggregate {aggregate_id} Git object batch rejected its request")

    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    output = bytearray()
    output_max = max_bytes + GIT_OUTPUT_MAX
    deadline = time.monotonic() + GIT_TIMEOUT
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                process.wait()
                die(
                    f"generator aggregate {aggregate_id} Git object batch "
                    f"timed out after {GIT_TIMEOUT} seconds"
                )
            events = selector.select(min(remaining, 0.1))
            if not events and process.poll() is not None:
                events = [
                    (key, selectors.EVENT_READ)
                    for key in selector.get_map().values()
                ]
            for key, _ in events:
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                output.extend(chunk)
                if len(output) > output_max:
                    process.kill()
                    process.wait()
                    die(
                        f"generator aggregate {aggregate_id} Git object batch "
                        "exceeded its bounded output envelope"
                    )
        try:
            returncode = process.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            die(
                f"generator aggregate {aggregate_id} Git object batch "
                f"timed out after {GIT_TIMEOUT} seconds"
            )
    finally:
        selector.close()
        process.stdout.close()
    if returncode != 0:
        die(f"generator aggregate {aggregate_id} Git object batch failed")

    cursor = 0
    metadata_bytes = 0
    blob_bytes = 0
    blobs = {}
    for row in rows:
        header_end = output.find(b"\n", cursor)
        if header_end < 0:
            die(f"generator aggregate {aggregate_id} Git object batch is partial")
        header = bytes(output[cursor:header_end])
        metadata_bytes += len(header) + 1
        if metadata_bytes > GIT_OUTPUT_MAX:
            die(
                f"generator aggregate {aggregate_id} Git object metadata "
                f"exceeds {GIT_OUTPUT_MAX} bytes"
            )
        try:
            object_id, kind, size_text = header.decode("ascii", "strict").split(" ")
            size = int(size_text, 10)
        except (UnicodeError, ValueError):
            die(f"generator aggregate {aggregate_id} Git object batch is malformed")
        if (
            object_id != row["object"]
            or kind != "blob"
            or size < 0
            or str(size) != size_text
        ):
            die(f"generator aggregate {aggregate_id} Git object batch is malformed")
        blob_bytes += size
        if blob_bytes > max_bytes:
            die(
                f"generator aggregate {aggregate_id} exceeds its "
                f"{max_bytes}-byte ceiling"
            )
        start = header_end + 1
        end = start + size
        if end >= len(output) or output[end:end + 1] != b"\n":
            die(f"generator aggregate {aggregate_id} Git object batch is partial")
        blobs[row["path"]] = bytes(output[start:end])
        cursor = end + 1
    if cursor != len(output):
        die(f"generator aggregate {aggregate_id} Git object batch has extra output")
    return blobs


def _manifest_document(data: bytes, aggregate_id: str) -> dict:
    try:
        document = json.loads(
            data.decode("utf-8", "strict"), object_pairs_hook=_strict_json_object
        )
    except (UnicodeError, ValueError) as exc:
        die(f"generator aggregate {aggregate_id} manifest is not valid JSON: {exc}")
    if not isinstance(document, dict):
        die(f"generator aggregate {aggregate_id} manifest must be an object")
    return document


def _validate_generator_aggregate(
    base_dir: str,
    sync_head: str,
    declaration: dict,
    registry: dict,
) -> dict:
    aggregate_id = declaration["id"]
    tree_id, rows = _git_aggregate_tree(
        base_dir, sync_head, aggregate_id, registry
    )
    blobs = _git_batch_blobs(
        base_dir, aggregate_id, rows, registry["max_bytes"]
    )
    by_path = {row["path"]: row for row in rows}
    manifest_path = registry["prefix"] + registry["manifest"]
    if manifest_path not in blobs:
        die(f"generator aggregate {aggregate_id} manifest is missing")
    manifest_bytes = blobs[manifest_path]
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_digest != declaration["manifest_sha256"]:
        die(f"generator aggregate {aggregate_id} manifest digest does not match")
    document = _manifest_document(manifest_bytes, aggregate_id)
    if set(document) != {
        "schema",
        "contract",
        "generated_by",
        "file_count",
        "total_bytes",
        "omissions",
        "files",
    }:
        die(f"generator aggregate {aggregate_id} manifest has the wrong fields")
    if document.get("schema") != registry["manifest_schema"]:
        die(f"generator aggregate {aggregate_id} manifest has the wrong schema")
    if document.get("contract") != registry["manifest_contract"]:
        die(f"generator aggregate {aggregate_id} manifest has the wrong contract")
    if document.get("generated_by") != registry["generator"]:
        die(f"generator aggregate {aggregate_id} manifest has the wrong generator")
    if not isinstance(document.get("omissions"), list):
        die(f"generator aggregate {aggregate_id} manifest omissions must be an array")
    payload = document.get("files")
    if not isinstance(payload, list):
        die(f"generator aggregate {aggregate_id} manifest files must be an array")
    if len(payload) + 1 > registry["max_files"]:
        die(
            f"generator aggregate {aggregate_id} exceeds its "
            f"{registry['max_files']}-file ceiling"
        )
    normalized_rows = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict) or set(item) not in (
            {"bytes", "path", "sha256", "source"},
            {"bytes", "generated_by", "path", "sha256", "source"},
        ):
            die(
                f"generator aggregate {aggregate_id} manifest row {index} "
                "has the wrong fields"
            )
        path = _aggregate_relative_path(
            item.get("path"),
            f"generator aggregate {aggregate_id} manifest row {index} path",
        )
        if path == registry["manifest"]:
            die(f"generator aggregate {aggregate_id} manifest contains a self row")
        size = item.get("bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            die(
                f"generator aggregate {aggregate_id} manifest row {index} "
                "has an invalid byte count"
            )
        digest = _sha256_value(
            item.get("sha256"),
            f"generator aggregate {aggregate_id} manifest row {index} digest",
        )
        source = item.get("source")
        if source is not None and not isinstance(source, str):
            die(
                f"generator aggregate {aggregate_id} manifest row {index} "
                "has an invalid source"
            )
        if "generated_by" in item and not isinstance(item["generated_by"], str):
            die(
                f"generator aggregate {aggregate_id} manifest row {index} "
                "has an invalid generator"
            )
        normalized_rows.append({"path": path, "bytes": size, "sha256": digest})
    manifest_paths = [item["path"] for item in normalized_rows]
    if manifest_paths != sorted(set(manifest_paths)):
        die(f"generator aggregate {aggregate_id} manifest paths are not sorted and unique")
    manifest_file_count = document.get("file_count")
    if (
        isinstance(manifest_file_count, bool)
        or not isinstance(manifest_file_count, int)
        or manifest_file_count != len(normalized_rows)
    ):
        die(f"generator aggregate {aggregate_id} manifest file count does not match")
    payload_bytes = sum(item["bytes"] for item in normalized_rows)
    manifest_total_bytes = document.get("total_bytes")
    if (
        isinstance(manifest_total_bytes, bool)
        or not isinstance(manifest_total_bytes, int)
        or manifest_total_bytes != payload_bytes
    ):
        die(f"generator aggregate {aggregate_id} manifest byte count does not match")
    total_bytes = payload_bytes + len(manifest_bytes)
    if total_bytes > registry["max_bytes"]:
        die(
            f"generator aggregate {aggregate_id} exceeds its "
            f"{registry['max_bytes']}-byte ceiling"
        )

    expected_paths = {
        registry["prefix"] + item["path"] for item in normalized_rows
    }
    expected_paths.add(manifest_path)
    if set(by_path) != expected_paths:
        die(f"generator aggregate {aggregate_id} manifest membership does not match Git")
    if declaration["file_count"] != len(expected_paths):
        die(f"generator aggregate {aggregate_id} file count does not match")

    file_digests = []
    for item in normalized_rows:
        full_path = registry["prefix"] + item["path"]
        data = blobs[full_path]
        if len(data) != item["bytes"]:
            die(f"generator aggregate {aggregate_id} blob byte count does not match")
        digest = hashlib.sha256(data).hexdigest()
        if digest != item["sha256"]:
            die(f"generator aggregate {aggregate_id} blob digest does not match")
        mode = by_path[full_path]["mode"]
        file_digests.append(
            (
                full_path,
                hashlib.sha256(
                    GENERATOR_AGGREGATE_FILE_DIGEST_DOMAIN
                    + full_path.encode("utf-8")
                    + b"\0"
                    + mode.encode("ascii")
                    + b"\0"
                    + str(len(data)).encode("ascii")
                    + b"\0"
                    + digest.encode("ascii")
                ).digest(),
            )
        )
    manifest_mode = by_path[manifest_path]["mode"]
    file_digests.append(
        (
            manifest_path,
            hashlib.sha256(
                GENERATOR_AGGREGATE_FILE_DIGEST_DOMAIN
                + manifest_path.encode("utf-8")
                + b"\0"
                + manifest_mode.encode("ascii")
                + b"\0"
                + str(len(manifest_bytes)).encode("ascii")
                + b"\0"
                + manifest_digest.encode("ascii")
            ).digest(),
        )
    )
    file_digests.sort(key=lambda item: item[0])
    tree_digest = hashlib.sha256(
        GENERATOR_AGGREGATE_TREE_DIGEST_DOMAIN
        + b"".join(digest for _, digest in file_digests)
    ).hexdigest()
    if tree_digest != declaration["tree_sha256"]:
        die(f"generator aggregate {aggregate_id} tree digest does not match")
    return {
        **declaration,
        "git_tree": tree_id,
        "payload_file_count": len(normalized_rows),
        "total_bytes": total_bytes,
    }


def _affected_aggregates(value) -> list[dict]:
    label = "affected_aggregates"
    if not isinstance(value, list) or not value:
        die(f"{label} must be a non-empty array")
    normalized = []
    for index, aggregate in enumerate(value):
        if not isinstance(aggregate, dict) or set(aggregate) != {
            "id",
            "prefix",
            "generator",
            "manifest",
            "manifest_sha256",
            "file_count",
            "tree_sha256",
        }:
            die(f"{label} entry {index} has the wrong fields")
        aggregate_id = aggregate["id"]
        if not isinstance(aggregate_id, str):
            die(f"{label} entry {index} has an invalid id")
        registry = GENERATOR_AGGREGATE_REGISTRY.get(aggregate_id)
        if registry is None:
            die(f"{label} entry {index} names an unknown aggregate")
        for key in ("prefix", "generator", "manifest"):
            if aggregate[key] != registry[key]:
                die(
                    f"generator aggregate {aggregate_id} {key} does not match "
                    "the source registry"
                )
        _sha256_value(
            aggregate["manifest_sha256"],
            f"generator aggregate {aggregate_id} manifest digest",
        )
        _sha256_value(
            aggregate["tree_sha256"],
            f"generator aggregate {aggregate_id} tree digest",
        )
        count = aggregate["file_count"]
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or count < 1
            or count > registry["max_files"]
        ):
            die(f"generator aggregate {aggregate_id} has an invalid file count")
        normalized.append(dict(aggregate))
    ids = [aggregate["id"] for aggregate in normalized]
    if ids != sorted(set(ids)):
        die(f"{label} must be sorted and unique by id")
    prefixes = [aggregate["prefix"] for aggregate in normalized]
    for left, prefix in enumerate(prefixes):
        for other in prefixes[left + 1:]:
            if prefix.startswith(other) or other.startswith(prefix):
                die("affected_aggregates contains overlapping registered prefixes")
    return normalized


def _integration_checks_v2(
    value, affected_paths: list[str], aggregates: list[dict]
) -> list[dict]:
    if (
        not isinstance(value, list)
        or not value
        or len(value) > INTEGRATION_CHECKS_MAX
    ):
        die(
            "integration revalidation checks must be a non-empty array of at "
            f"most {INTEGRATION_CHECKS_MAX} entries"
        )
    selected_ids = {aggregate["id"] for aggregate in aggregates}
    normalized = []
    seen_ids = set()
    covered_paths = set()
    covered_aggregates = set()
    for index, check in enumerate(value):
        if not isinstance(check, dict) or set(check) != {
            "id", "command", "paths", "aggregates", "exit"
        }:
            die(
                f"integration revalidation check {index} must contain exactly "
                "id, command, paths, aggregates and exit"
            )
        check_id = check["id"]
        if (
            not isinstance(check_id, str)
            or not INTEGRATION_CHECK_ID_RE.fullmatch(check_id)
            or check_id in seen_ids
        ):
            die(f"integration revalidation check {index} has an invalid id")
        seen_ids.add(check_id)
        command = check["command"]
        try:
            command_bytes = command.encode("utf-8") if isinstance(command, str) else b""
        except UnicodeEncodeError:
            command_bytes = b""
        if (
            not command_bytes
            or len(command_bytes) > INTEGRATION_COMMAND_BYTES_MAX
            or any(ord(character) < 32 or ord(character) == 127 for character in command)
        ):
            die(f"integration revalidation check {index} has an invalid command")
        if isinstance(check["exit"], bool) or check["exit"] != 0:
            die(f"integration revalidation check {check_id} must record exit 0")
        paths = _manifest_paths(
            check["paths"],
            f"integration revalidation check {check_id} paths",
            set(affected_paths),
        )
        ids = check["aggregates"]
        if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
            die(f"integration revalidation check {check_id} aggregates must be an array")
        if ids != sorted(set(ids)):
            die(
                f"integration revalidation check {check_id} aggregates must be "
                "sorted and unique"
            )
        if not set(ids) <= selected_ids:
            die(f"integration revalidation check {check_id} names an undeclared aggregate")
        for aggregate_id in ids:
            expected = GENERATOR_AGGREGATE_REGISTRY[aggregate_id]["command"]
            if command != expected:
                die(
                    f"integration revalidation check {check_id} must use the "
                    f"registered verification command for {aggregate_id}"
                )
        covered_paths.update(paths)
        covered_aggregates.update(ids)
        normalized.append(
            {
                "id": check_id,
                "command": command,
                "paths": paths,
                "aggregates": ids,
                "exit": 0,
            }
        )
    if covered_paths != set(affected_paths):
        die("integration revalidation checks do not cover every affected path")
    if covered_aggregates != selected_ids:
        die("integration revalidation checks do not cover every affected aggregate")
    return normalized


def _integration_revalidation_record_v2(
    base_dir: str,
    artifact: str,
    data: bytes,
    raw: dict,
    product_head: str,
    base_head: str,
    sync_head: str,
) -> dict:
    if set(raw) != {"schema", "affected_paths", "affected_aggregates", "checks"}:
        die(
            "integration revalidation v2 artefact must contain exactly schema, "
            "affected_paths, affected_aggregates and checks"
        )
    declarations = _affected_aggregates(raw["affected_aggregates"])
    base_before = merge_base_commit(base_dir, product_head, base_head)
    product_paths = git_diff_paths_for_aggregates(
        base_dir, base_before, product_head
    )
    upstream_paths = git_diff_paths_for_aggregates(
        base_dir, base_before, base_head
    )
    overlap_paths = sorted(set(product_paths) & set(upstream_paths))
    composition_paths = git_diff_paths_for_aggregates(
        base_dir, product_head, sync_head
    )
    required_paths = sorted(set(composition_paths) | set(overlap_paths))
    prefixes = [aggregate["prefix"] for aggregate in declarations]
    owned_paths = [
        path for path in required_paths if any(path.startswith(prefix) for prefix in prefixes)
    ]
    if not owned_paths:
        die("affected_aggregates does not own any computed integration path")
    outside_paths = sorted(set(required_paths) - set(owned_paths))
    affected_paths = _manifest_paths(
        raw["affected_paths"], "affected_paths", set(required_paths)
    )
    if affected_paths != outside_paths:
        missing = sorted(set(outside_paths) - set(affected_paths))
        if missing:
            die(
                "affected_paths omits the computed outside integration surface: "
                + ", ".join(missing)
            )
        die("affected_paths must contain only the exact outside integration surface")

    aggregates = [
        _validate_generator_aggregate(
            base_dir,
            sync_head,
            declaration,
            GENERATOR_AGGREGATE_REGISTRY[declaration["id"]],
        )
        for declaration in declarations
    ]
    checks = _integration_checks_v2(raw["checks"], affected_paths, aggregates)
    return {
        "schema": INTEGRATION_REVALIDATION_SCHEMA_V2,
        "artifact": os.path.relpath(artifact, os.path.realpath(base_dir)),
        "sha256": hashlib.sha256(data).hexdigest(),
        "base_before": base_before,
        "base_after": base_head,
        "sync_head": sync_head,
        "product_paths": product_paths,
        "upstream_paths": upstream_paths,
        "overlap_paths": overlap_paths,
        "composition_paths": composition_paths,
        "required_path_count": len(required_paths),
        "aggregate_owned_path_count": len(owned_paths),
        "individual_path_count": len(affected_paths),
        "affected_paths": affected_paths,
        "affected_aggregates": aggregates,
        "checks": checks,
    }


def integration_revalidation_record(
    base_dir: str,
    supplied: str,
    product_head: str,
    base_head: str,
    sync_head: str,
) -> dict:
    """Bind green composition checks to the exact product/base path delta."""
    artifact, data = read_bounded_source(
        base_dir, supplied, "integration revalidation artefact"
    )
    try:
        raw = json.loads(
            decoded_source(data, "integration revalidation artefact"),
            object_pairs_hook=_strict_json_object,
        )
    except ValueError as exc:
        die(f"integration revalidation artefact is not valid JSON: {exc}")
    if (
        isinstance(raw, dict)
        and raw.get("schema") == INTEGRATION_REVALIDATION_SCHEMA_V2
    ):
        return _integration_revalidation_record_v2(
            base_dir,
            artifact,
            data,
            raw,
            product_head,
            base_head,
            sync_head,
        )
    if not isinstance(raw, dict) or set(raw) != {
        "schema", "affected_paths", "checks"
    }:
        die(
            "integration revalidation artefact must contain exactly "
            "schema, affected_paths and checks"
        )
    if raw["schema"] != INTEGRATION_REVALIDATION_SCHEMA:
        die(
            "integration revalidation artefact has the wrong schema "
            f"(expected {INTEGRATION_REVALIDATION_SCHEMA})"
        )

    base_before = merge_base_commit(base_dir, product_head, base_head)
    product_paths = git_diff_paths(base_dir, base_before, product_head)
    upstream_paths = git_diff_paths(base_dir, base_before, base_head)
    overlap_paths = sorted(set(product_paths) & set(upstream_paths))
    composition_paths = git_diff_paths(base_dir, product_head, sync_head)
    required_paths = sorted(set(composition_paths) | set(overlap_paths))
    affected_paths = _manifest_paths(
        raw["affected_paths"], "affected_paths", set(required_paths)
    )
    missing_paths = sorted(set(required_paths) - set(affected_paths))
    if missing_paths:
        die(
            "affected_paths omits the computed integration surface: "
            + ", ".join(missing_paths)
        )

    checks = raw["checks"]
    if (
        not isinstance(checks, list)
        or not checks
        or len(checks) > INTEGRATION_CHECKS_MAX
    ):
        die(
            "integration revalidation checks must be a non-empty array of at "
            f"most {INTEGRATION_CHECKS_MAX} entries"
        )
    normalized = []
    seen_ids = set()
    covered = set()
    for index, check in enumerate(checks):
        if not isinstance(check, dict) or set(check) != {
            "id", "command", "paths", "exit"
        }:
            die(
                f"integration revalidation check {index} must contain exactly "
                "id, command, paths and exit"
            )
        check_id = check["id"]
        if (
            not isinstance(check_id, str)
            or not INTEGRATION_CHECK_ID_RE.fullmatch(check_id)
            or check_id in seen_ids
        ):
            die(f"integration revalidation check {index} has an invalid id")
        seen_ids.add(check_id)
        command = check["command"]
        try:
            command_bytes = (
                command.encode("utf-8") if isinstance(command, str) else b""
            )
        except UnicodeEncodeError:
            command_bytes = b""
        if (
            not isinstance(command, str)
            or not command
            or not command_bytes
            or len(command_bytes) > INTEGRATION_COMMAND_BYTES_MAX
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in command
            )
        ):
            die(f"integration revalidation check {index} has an invalid command")
        if isinstance(check["exit"], bool) or check["exit"] != 0:
            die(f"integration revalidation check {check_id} must record exit 0")
        paths = _manifest_paths(
            check["paths"], f"integration revalidation check {check_id} paths",
            set(affected_paths),
        )
        covered.update(paths)
        normalized.append(
            {"id": check_id, "command": command, "paths": paths, "exit": 0}
        )
    if covered != set(affected_paths):
        die("integration revalidation checks do not cover every affected path")

    return {
        "schema": INTEGRATION_REVALIDATION_SCHEMA,
        "artifact": os.path.relpath(artifact, os.path.realpath(base_dir)),
        "sha256": hashlib.sha256(data).hexdigest(),
        "base_before": base_before,
        "base_after": base_head,
        "product_paths": product_paths,
        "upstream_paths": upstream_paths,
        "overlap_paths": overlap_paths,
        "composition_paths": composition_paths,
        "affected_paths": affected_paths,
        "checks": normalized,
    }


def step_merge_command(pr_url: object) -> str:
    """The exact invocation that merges the pull request the directive names.

    The directive already carried the URL and the receipt command, and left the
    merge itself to whatever the operator typed from reading them. A number
    retyped from a URL is where issue 594 went wrong, and `gh pr merge` with a
    missing argument does not fail: it falls through to the current branch's pull
    request, which on a chained stack is the one holding every commit in the run.

    Built from the URL rather than a number and a repository flag, so nothing has
    to be transcribed. Printed, never executed.
    """
    if not isinstance(pr_url, str) or GITHUB_PR_RE.fullmatch(pr_url) is None:
        die(
            "this step's push receipt holds no usable pull request URL, so the "
            "merge command cannot be built from it; repair the receipt rather "
            "than merging a pull request the directive did not name"
        )
    return f"gh pr merge {pr_url.rstrip('/')} --merge"


def expected_run_branch_tip(state: dict):
    """What the run branch's tip should be, from this run's own receipts.

    An active sync is the most recent thing the controller put there; before
    that, the last merge it receipted. Before the first merge it has recorded no
    expectation at all, and `None` says the question cannot be asked yet rather
    than that any tip will do.
    """
    integrate = as_dict(state.get("integrate"))
    sync = as_dict(integrate.get("sync"))
    candidate = sync.get("commit")
    if isinstance(candidate, str) and COMMIT_RE.fullmatch(candidate):
        return candidate
    merges = as_dict(integrate.get("merges"))
    for number in reversed(integrate.get("merged") or []):
        candidate = as_dict(merges.get(str(number))).get("merge_commit")
        if isinstance(candidate, str) and COMMIT_RE.fullmatch(candidate):
            return candidate
    return None


def unreceipted_run_branch_movement(base_dir: str, state: dict, landing=None):
    """Whether the run branch moved without a receipt naming the move.

    Every legitimate change to the run branch during integration is one this run
    recorded: a merge-step receipt, or a sync. A tip that is neither means
    something merged into it that the controller was never asked for.

    A chained stack makes that unrecoverable rather than untidy. The topmost step
    branch holds every commit in the run, so merging the wrong one lands all of
    them, and the skipped pull requests can then be neither retargeted onto the
    run branch, because GitHub reports no commits between them and a branch their
    heads already sit in, nor merged into a base they are an ancestor of. The
    issue 576 run lost three merge receipts that way. Reporting it at the first
    directive after it happens is the only point where anything can still be done.
    """
    expected = expected_run_branch_tip(state)
    branch = run_branch_of(state)
    if expected is None or not isinstance(branch, str) or not branch:
        return None
    # A receipt runs after its own merge has landed, so the merge it is about to
    # record is a legitimate tip as well as the one before it. `next` passes no
    # landing commit, which is what makes the branch have to be where the loop
    # left it.
    accepted = {expected}
    if isinstance(landing, str) and COMMIT_RE.fullmatch(landing):
        accepted.add(landing)
    try:
        tip = remote_branch_tip(base_dir, branch)
    except SystemExit:
        return {"fault": "unreadable", "branch": branch, "expected": expected}
    if tip in accepted:
        return None
    return {"fault": "moved", "branch": branch, "expected": expected, "tip": tip}


def describe_run_branch_movement(fault: dict) -> str:
    """One line saying what the run branch did, for a refusal or a report."""
    if fault["fault"] == "unreadable":
        return (
            f"the run branch '{fault['branch']}' could not be read, so whether it "
            f"still matches the receipted tip {fault['expected']} is unknown"
        )
    return (
        f"the run branch '{fault['branch']}' is at {fault['tip']} and this run's "
        f"last receipt names {fault['expected']}"
    )


def refuse_unreceipted_run_branch_movement(
    base_dir: str, state: dict, landing=None
) -> None:
    """Stop the integrate phase when the run branch moved outside the loop."""
    fault = unreceipted_run_branch_movement(base_dir, state, landing)
    if fault is None:
        return
    if fault["fault"] == "unreadable":
        die(
            describe_run_branch_movement(fault)
            + ". Integration cannot proceed without reading the branch it merges "
            "into."
        )
    die(
        describe_run_branch_movement(fault)
        + ". Something merged into the run branch that this run did not receipt. "
        "A stack chains, so the topmost step branch holds every commit in the run "
        "and merging the wrong pull request lands all of them at once. There is no "
        "repair from here: a skipped step's pull request cannot be retargeted onto "
        "a branch its head already sits in, and cannot merge into a base it is an "
        "ancestor of. Merge each step's pull request by the number the directive "
        "names, one at a time. If this has already happened, halt the run with the "
        "reason and finish by hand; do not receipt a merge the loop did not make."
    )


def refuse_rewritten_stack(base_dir: str, state: dict, current_step: int) -> None:
    """Refuse when a waiting branch no longer contains its receipted head.

    Equality is the zero-query path. A moved tip receives one bounded native
    ancestry query: status 0 admits topology only, status 1 establishes that the
    receipted head is absent, and every other outcome is unknown. Signatures,
    provenance, GitHub verification, and attribution remain mandatory over the
    exact live range at ``done merge-step``.

    A step whose branch cannot be read is reported rather than skipped: an absent
    downstream branch during integration is not a normal state.
    """
    merged = as_dict(state.get("integrate")).get("merged") or []
    nonancestors, unknown, unreadable = [], [], []
    for step in state["steps"]:
        number = step["n"]
        if number == current_step or number in merged:
            continue
        push_receipt = as_dict(step["receipts"].get("push"))
        recorded = push_receipt.get("head_commit")
        if not recorded:
            continue
        branch = step_branch_name(state, step)
        try:
            tip = remote_branch_tip(base_dir, branch)
        except SystemExit:
            unreadable.append(f"step {number} ('{branch}')")
            continue
        if tip == recorded:
            continue
        if len(recorded) < 40:
            # An abbreviated receipt is an older receipt format, not a moved
            # branch: `--head-commit` accepts any ref git resolves, and receipts
            # written before that value was stored resolved hold whatever was
            # passed. Resolve and ask again, so the check answers whether this
            # is the commit that was pushed rather than whether two strings
            # match. Only reached when they differ, so a full-length receipt
            # never shells out.
            try:
                recorded = _native_relation_commit(
                    base_dir, recorded, f"step {number} recorded push head"
                )
            except SystemExit:
                unreadable.append(f"step {number} ('{branch}', recorded {recorded})")
                continue
            if tip == recorded:
                continue
        relation = _native_ancestry_status(base_dir, recorded, tip)
        observation = (
            f"step {number} ('{branch}') recorded head {recorded} and observed "
            f"tip {tip}"
        )
        if relation == 0:
            continue
        if relation == 1:
            nonancestors.append(observation)
        else:
            unknown.append(observation)
    if unreadable:
        die(
            "a step branch still waiting to merge could not be read: "
            + "; ".join(unreadable)
            + ". Integration cannot proceed while a downstream branch is missing."
        )
    if unknown:
        die(
            "a step branch still waiting to merge has unknown ancestry: "
            + "; ".join(unknown)
            + ". Its ancestry could not be determined from bounded native local "
            "objects. Restore readable native objects and repository history, then "
            "retry; integration cannot proceed on an unanswered relation."
        )
    if nonancestors:
        die(
            "a step branch still waiting to merge no longer contains its receipted "
            "head: "
            + "; ".join(nonancestors)
            + ". Each recorded head is not an ancestor of its observed tip. The "
            "controller has not established why the history moved, and the push "
            "receipt no longer describes the current remote range. Land the run "
            "from a branch holding the original commits rather than merging this "
            "stack, and do not import GitHub's public key to make the signature "
            "check pass."
        )


def done_merge_step(args, state: dict) -> None:
    if state["phase"] != "integrate":
        die(
            "merge-step is an integrate-phase receipt; the run is in phase "
            f"'{state['phase']}'"
        )
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if args.step is None:
        die("--step is required")
    if not args.merge_commit:
        die("--merge-commit is required")
    pending = _integrate_directive(state, args.dir, check_resolution=False)
    if pending["do"] != "merge-step":
        die(f"every step already merged into '{run_branch_of(state)}'")
    if args.step != pending["step"]:
        die(
            f"the stack merges in step order; step {pending['step']} "
            f"('{pending['branch']}') is next, not step {args.step}"
        )
    refuse_unreceipted_run_branch_movement(args.dir, state, args.merge_commit)
    refuse_rewritten_stack(args.dir, state, args.step)
    step = state["steps"][args.step - 1]
    push_receipt = as_dict(step["receipts"].get("push"))
    pr_record = inspect_pull_request(
        args.dir,
        pending["pr_url"],
        expected_head=pending["branch"],
        expected_base=pending["into"],
        expected_head_sha=None,
        expected_merge_sha=args.merge_commit,
    )
    remote_head = remote_branch_tip(args.dir, pending["branch"])
    if pr_record["head_sha"] != remote_head:
        die("recorded pull request head does not match its remote branch tip")
    recorded_local = push_receipt.get("verified_commits")
    recorded_github = push_receipt.get("github_verified")
    recorded_current = (
        isinstance(recorded_local, list)
        and isinstance(recorded_github, list)
        and recorded_local == recorded_github
        and bool(recorded_local)
        and all(isinstance(sha, str) and COMMIT_RE.fullmatch(sha) for sha in recorded_local)
        and recorded_local[-1] == remote_head
    )
    if recorded_current:
        effective_push = {
            "repaired": False,
            "pr_base": push_receipt.get("pr_base"),
            "head": remote_head,
            "verified_commits": recorded_local,
            "github_verified": recorded_github,
        }
    else:
        expected_pr_base = step_pr_base(state, step)
        pr_base = push_receipt.get("pr_base")
        if not isinstance(pr_base, str) or pr_base != expected_pr_base:
            die("recorded step pull request has no exact PR base for repair")
        repaired_local = verify_local_range(
            args.dir,
            pr_base,
            remote_head,
            f"step {step['n']} merge-time push repair",
        )
        # The recorded push attribution describes the head this repair replaced,
        # so it is re-derived here rather than carried forward stale.
        repaired_github, repaired_attribution = verified_github_attribution(
            args.dir, repaired_local
        )
        effective_push = {
            "repaired": True,
            "pr_base": pr_base,
            "head": remote_head,
            "verified_commits": repaired_local,
            "github_verified": repaired_github,
            "attribution": {"commits": repaired_attribution},
        }
    github_verified = verify_github_commits(args.dir, [args.merge_commit])
    integrate = state.setdefault("integrate", {"merged": [], "merges": {}})
    integrate.setdefault("merged", []).append(args.step)
    integrate.setdefault("merges", {})[str(args.step)] = {
        "branch": pending["branch"],
        "into": pending["into"],
        "merge_commit": args.merge_commit,
        "github_verified": github_verified,
        "pull_request": pr_record,
        "effective_push": effective_push,
    }
    commit(
        args.dir,
        state,
        "done:merge-step",
        {
            "step": args.step,
            "branch": pending["branch"],
            "into": pending["into"],
            "merge_commit": args.merge_commit,
            "github_verified": github_verified,
            "pull_request": pr_record,
            "effective_push": effective_push,
        },
    )
    remaining = len(state["steps"]) - len(integrate["merged"])
    tail = f"{remaining} step(s) left in the stack" if remaining else "stack merged"
    print(f"step {args.step} merged into {pending['into']}; {tail}")


def done_sync_run(args, state: dict) -> None:
    """Receipt or supersede a signed composition of a completed run stack."""
    verify_run(args.dir)
    if state["phase"] != "integrate":
        die(
            "sync-run is an integrate-phase receipt; the run is in phase "
            f"'{state['phase']}'"
        )
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    pending = _integrate_directive(state, args.dir, check_resolution=False)
    if pending["do"] != "integrate":
        die(
            f"step {pending['step']} still has to merge into "
            f"'{run_branch_of(state)}' before the run can sync"
        )
    integrate = state.setdefault("integrate", {"merged": [], "merges": {}})
    current_sync = as_dict(integrate.get("sync"))
    superseded_sync = None
    supersession_reason = None
    if current_sync:
        if args.supersede_sync is None:
            die(
                "the run branch already has a recorded integration sync; "
                "use --supersede-sync with its exact commit after repairing "
                "and revalidating the composition"
            )
        active = require_full_sha(
            current_sync.get("commit"), "active recorded sync commit"
        )
        supplied = require_full_sha(
            args.supersede_sync, "sync commit to supersede"
        )
        if supplied != active:
            die("--supersede-sync must name the active recorded sync commit")
        if not isinstance(args.reason, str) or not args.reason:
            die("--reason is required when superseding an integration sync")
        try:
            reason_bytes = args.reason.encode("utf-8")
        except UnicodeEncodeError:
            reason_bytes = b""
        if (
            not reason_bytes
            or not args.reason.strip()
            or len(reason_bytes) > INTEGRATION_SYNC_REASON_BYTES_MAX
            or any(ord(character) < 32 or ord(character) == 127
                   for character in args.reason)
        ):
            die("integration sync supersession reason is invalid")
        supersession_reason = args.reason
        history = integrate.get("superseded_syncs") or []
        if not isinstance(history, list):
            die("recorded superseded integration syncs are malformed")
        if len(history) >= INTEGRATION_SYNC_SUPERSESSIONS_MAX:
            die("the integration sync supersession limit has been reached")
    elif args.supersede_sync is not None:
        die("--supersede-sync requires an active recorded sync")
    elif args.reason is not None:
        die("--reason requires --supersede-sync")
    if not args.commit:
        die("--commit is required for sync-run")
    if not args.base_commit:
        die("--base-commit is required for sync-run")
    if not args.revalidation:
        die("--revalidation is required for sync-run")
    sync_tip = require_full_sha(args.commit, "run sync commit")
    base_tip = require_full_sha(args.base_commit, "run sync base commit")
    if current_sync and sync_tip == current_sync.get("commit"):
        die("replacement integration sync must use a new signed commit")
    repository = _native_relation_repository_identity(args.dir)
    _require_native_relation_history(args.dir)
    integration_base = integration_base_of(state)
    remote_tip = remote_branch_tip(
        args.dir, run_branch_of(state), native_relation=True
    )
    if remote_tip != sync_tip:
        die("run sync commit does not match the remote run branch tip")
    remote_base = remote_branch_tip(
        args.dir,
        integration_base,
        "remote base branch tip",
        native_relation=True,
    )
    if remote_base != base_tip:
        die("run sync base commit does not match the remote base branch tip")
    final_step = state["steps"][-1]["n"]
    merge_records = as_dict(integrate.get("merges"))
    final_merge = as_dict(merge_records.get(str(final_step))).get("merge_commit")
    recorded_tip = require_full_sha(final_merge, "final recorded step merge")
    parents = _native_relation_parents(args.dir, sync_tip, "run sync commit")
    expected_parents = [recorded_tip, base_tip]
    if parents != expected_parents:
        die(
            "run sync merge parents do not match the final recorded step merge "
            "and the exact remote base tip"
        )
    product_evidence = product_evidence_record(state, recorded_tip)
    if (
        current_sync
        and current_sync.get("product_evidence") != product_evidence
    ):
        die("recorded product evidence changed before sync supersession")
    revalidation = integration_revalidation_record(
        args.dir, args.revalidation, recorded_tip, base_tip, sync_tip
    )
    resolution_guard = sync_resolution_guard_record(
        args.dir,
        recorded_tip,
        base_tip,
        sync_tip,
        current_sync=(current_sync if current_sync else None),
        acknowledgements=list(
            getattr(args, "acknowledge_sync_paths", None) or []
        ),
    )
    verify_local_commit(args.dir, sync_tip, "run branch integration sync")
    github_verified = verify_github_commits(args.dir, [sync_tip])
    _require_native_relation_history(args.dir)
    if _native_relation_repository_identity(args.dir) != repository:
        die("integration sync repository changed during evidence collection")
    new_sync = {
        "commit": sync_tip,
        "base": integration_base,
        "starting_base": state["base"],
        SYNC_BASE_HEAD_KEY: base_tip,
        "parents": parents,
        "github_verified": github_verified,
        "product_evidence": product_evidence,
        "revalidation": revalidation,
        "resolution_guard": resolution_guard,
    }
    if current_sync:
        superseded_sync = {
            "sync": current_sync,
            "superseded_by": sync_tip,
            "reason": supersession_reason,
            "ts": now(),
        }
        history = list(integrate.get("superseded_syncs") or [])
        history.append(superseded_sync)
        integrate["superseded_syncs"] = history
    integrate["sync"] = new_sync
    if superseded_sync:
        commit(
            args.dir,
            state,
            "done:sync-run-supersede",
            {"sync": new_sync, "superseded": superseded_sync},
        )
        print(
            f"{run_branch_of(state)} superseded integration sync "
            f"{superseded_sync['sync']['commit']} with {sync_tip}; "
            f"product evidence preserved; {len(revalidation['checks'])} "
            "integration revalidation check(s) recorded; "
            f"{len(resolution_guard['acknowledged_paths'])} sync resolution "
            "path(s) acknowledged; integration may continue"
        )
    else:
        commit(args.dir, state, "done:sync-run", new_sync)
        print(
            f"{run_branch_of(state)} synced with {integration_base} at "
            f"{base_tip}; product evidence preserved; "
            f"{len(revalidation['checks'])} integration revalidation check(s) "
            f"recorded; {len(resolution_guard['acknowledged_paths'])} sync "
            "resolution path(s) acknowledged; integration may continue"
        )


def version_resolution_event(receipt: dict) -> dict:
    """Bounded ledger projection of one full state receipt."""
    return {
        "schema": VERSION_RESOLUTION_SCHEMA,
        "sha256": hashlib.sha256(canonical(receipt).encode()).hexdigest(),
        "runbook_sha256": receipt["runbook_sha256"],
        "relations_sha256": receipt["relations_sha256"],
        "base_ref": receipt["base_ref"],
        "base_commit": receipt["base_commit"],
        "head_commit": receipt["head_commit"],
        "targets": [
            {
                "skill": target["skill"],
                "ledger": target["ledger"],
                "resolved_version": target["resolved_version"],
                "head_ledger_sha256": target["head_ledger_sha256"],
                "skill_sha256": target["skill_sha256"],
            }
            for target in receipt["targets"]
        ],
    }


def _intact_ledger_entries(base_dir: str, label: str) -> list[dict]:
    path = ledger_path(base_dir)
    entries = []
    previous = "genesis"
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                entry = json.loads(line)
                expected = hashlib.sha256(
                    canonical(
                        {
                            "ts": entry["ts"],
                            "event": entry["event"],
                            "data": entry["data"],
                            "prev": entry["prev"],
                            "state": entry["state"],
                        }
                    ).encode()
                ).hexdigest()
                if entry["prev"] != previous or entry["hash"] != expected:
                    die(
                        f"{label} controller ledger is not intact at line "
                        f"{line_number}",
                        1,
                    )
                previous = entry["hash"]
                entries.append(entry)
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError):
        die(f"{label} controller ledger is malformed", 1)
    if not entries:
        die(f"{label} controller ledger is empty", 1)
    return entries


def _state_with_resolution(state: dict, receipt: dict) -> dict:
    candidate = json.loads(json.dumps(state))
    integrate = candidate.setdefault("integrate", {"merged": [], "merges": {}})
    history = integrate.setdefault("version_resolutions", [])
    if not isinstance(history, list):
        die("recorded version resolution history is malformed", 1)
    history.append(receipt)
    validate_version_resolution_history(
        history, "candidate.integrate.version_resolutions"
    )
    return candidate


def recover_version_resolution(
    base_dir: str,
    state: dict,
    pending: dict,
    current: dict | None,
) -> tuple[dict, bool]:
    """Finish, clear, or refuse one interrupted ledger/state transition."""
    recorded = pending["receipt"]
    state_hash = state_fingerprint(state)
    before = pending["state_before_sha256"]
    after = pending["state_after_sha256"]
    event_data = version_resolution_event(recorded)
    last = _intact_ledger_entries(base_dir, "version resolution")[-1]
    event_durable = (
        last.get("event") == "done:version-resolution"
        and last.get("data") == event_data
        and last.get("state") == after
        and last.get("prev") == pending["ledger_head"]
    )
    if state_hash == after:
        if not event_durable:
            die(
                "version resolution state is durable without its matching "
                "ledger event",
                1,
            )
        clear_version_resolution_pending(base_dir)
        return state, True
    if state_hash != before:
        die("version resolution pending state fingerprint does not match", 1)
    # The first pass lets a matching durable state/event pair clear without
    # consulting refs which may legitimately have moved after the transaction.
    # Every incomplete window still rebuilds current evidence before mutation.
    if current is None:
        return state, False
    if _resolution_without_timestamp(recorded) != _resolution_without_timestamp(current):
        die(
            "pending version resolution names stale base, head, or target "
            "evidence; restore that exact evidence or inspect the marker",
            1,
        )
    if event_durable:
        candidate = _state_with_resolution(state, recorded)
        if state_fingerprint(candidate) != after:
            die("version resolution pending candidate fingerprint does not match", 1)
        save_state(base_dir, candidate)
        make_version_resolution_write_durable(
            base_dir,
            state_path(base_dir),
            "state recovery",
            replaced=True,
        )
        clear_version_resolution_pending(base_dir)
        return candidate, True
    if last.get("hash") != pending["ledger_head"] or last.get("state") != before:
        die(
            "version resolution pending ledger ends with an unrelated transition",
            1,
        )
    clear_version_resolution_pending(base_dir)
    return state, False


def done_resolve_versions(args, state: dict) -> None:
    """Receipt one exact all-target relation result without editing the product."""
    if state.get("phase") != "integrate":
        die("resolve-versions is available only in the integrate phase")
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    pending_directive = _integrate_directive(
        state, args.dir, check_resolution=False
    )
    if pending_directive["do"] != "integrate":
        die(
            f"step {pending_directive['step']} still has to merge into "
            f"'{run_branch_of(state)}' before versions can resolve"
        )
    pending = load_version_resolution_pending(args.dir)
    if pending is not None:
        state, recovered = recover_version_resolution(
            args.dir, state, pending, None
        )
        if recovered:
            verify_run(args.dir)
            recorded = pending["receipt"]
            print(
                "recovered version resolution for base "
                f"{recorded['base_commit']} and head {recorded['head_commit']}"
            )
            return
    current = build_version_resolution(args.dir, state)
    if pending is not None:
        state, recovered = recover_version_resolution(
            args.dir, state, pending, current
        )
        if recovered:
            verify_run(args.dir)
            print(
                "recovered version resolution for base "
                f"{current['base_commit']} and head {current['head_commit']}"
            )
            return
    verify_run(args.dir)
    history = as_dict(state.get("integrate")).get("version_resolutions") or []
    if not isinstance(history, list):
        die("recorded version resolution history is malformed", 1)
    if (
        history
        and _resolution_without_timestamp(history[-1])
        == _resolution_without_timestamp(current)
    ):
        print(
            "version resolution already records base "
            f"{current['base_commit']} and head {current['head_commit']}"
        )
        return
    if len(history) >= VERSION_RESOLUTIONS_MAX:
        die(
            f"version resolution history already retains {VERSION_RESOLUTIONS_MAX} "
            "entries; halt rather than evicting evidence"
        )
    candidate = _state_with_resolution(state, current)
    marker = {
        "schema": VERSION_RESOLUTION_PENDING_SCHEMA,
        "subject": "version-resolution",
        "state_before_sha256": state_fingerprint(state),
        "state_after_sha256": state_fingerprint(candidate),
        "ledger_head": _intact_ledger_entries(
            args.dir, "version resolution"
        )[-1]["hash"],
        "receipt_sha256": hashlib.sha256(canonical(current).encode()).hexdigest(),
        "receipt": current,
    }
    write_version_resolution_pending(args.dir, marker)
    append_ledger(
        args.dir,
        "done:version-resolution",
        version_resolution_event(current),
        marker["state_after_sha256"],
    )
    make_version_resolution_write_durable(
        args.dir, ledger_path(args.dir), "ledger event"
    )
    save_state(args.dir, candidate)
    make_version_resolution_write_durable(
        args.dir,
        state_path(args.dir),
        "state replacement",
        replaced=True,
    )
    clear_version_resolution_pending(args.dir)
    print(
        f"resolved {len(current['targets'])} version target(s) against "
        f"{current['base_ref']} at {current['base_commit']} and candidate "
        f"{current['head_commit']}"
    )


def terminal_version_resolution(
    base_dir: str, state: dict, merge_commit: str
) -> dict | None:
    """Replay a relation from the actual base merge's ordered parents."""
    relations = as_dict(as_dict(state.get("receipts")).get("runbook")).get(
        "version_relations"
    )
    if relations is None:
        return None
    history = as_dict(state.get("integrate")).get("version_resolutions")
    if not isinstance(history, list) or not history:
        die("relation-bearing integration has no version resolution")
    active = validate_version_resolution_shape(
        history[-1], "integrate.version_resolutions[-1]"
    )
    merge_sha = require_full_sha(merge_commit, "integration merge commit")
    parents = _native_relation_parents(
        base_dir, merge_sha, "integration merge commit"
    )
    expected_parents = [active["base_commit"], active["head_commit"]]
    if parents != expected_parents:
        die(
            "integration merge parents do not replay the resolved "
            "[base, candidate] pair"
        )
    replay = build_version_resolution(
        base_dir,
        state,
        exact_base=parents[0],
        exact_head=parents[1],
    )
    if _resolution_without_timestamp(active) != _resolution_without_timestamp(replay):
        die("integration merge parents do not replay the active resolution")
    remote_base_after = remote_branch_tip(
        base_dir,
        integration_base_of(state),
        "post-merge base branch tip",
        native_relation=True,
    )
    if remote_base_after != merge_sha:
        die("the base branch moved again after the checked integration merge")
    return active


def done_integrate(args, state: dict) -> None:
    verify_run(args.dir)
    if state["phase"] != "integrate":
        die(
            "integrate is the terminal phase; the run is in phase "
            f"'{state['phase']}'"
        )
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    pending = _integrate_directive(state, args.dir, check_resolution=False)
    integration_base = integration_base_of(state)
    if pending["do"] != "integrate":
        die(
            f"step {pending['step']} still has to merge into "
            f"'{run_branch_of(state)}' first"
        )
    if not args.pr_url:
        die("--pr-url is required")
    if not args.merge_commit:
        die(
            "--merge-commit is required; the run is not complete until the run "
            f"branch is merged into '{integration_base}'"
        )
    frontier = as_dict(state.get("frontier"))
    published = frozenset()
    if frontier:
        recorded_sync = as_dict(as_dict(state.get("integrate")).get("sync"))
        if recorded_sync:
            published = base_ledger_versions(
                args.dir, recorded_sync.get(SYNC_BASE_HEAD_KEY), frontier["ledger"]
            )
        fault = frontier_close_fault(
            os.path.join(args.dir, frontier["ledger"]), frontier, published)
        if fault:
            die(
                f"the frontier ledger has not been closed: {fault}. This run "
                f"declared {frontier['ledger']} at init; update it exactly once "
                f"per the versioning contract, or `hexctl halt` and say why not"
            )
    expected_issue = expected_task_issue(state)
    if state["receipts"].get("task_issue") is not None and not args.closed_issue_url:
        die("--closed-issue-url is required because a task_issue receipt exists")
    if expected_issue and args.closed_issue_url != expected_issue:
        die(
            "--closed-issue-url does not match the recorded task_issue "
            f"({expected_issue})"
        )
    carried = carried_forward_fault(run_pr_path(args.dir))
    if carried:
        die(carried)
    remote_tip = remote_branch_tip(args.dir, run_branch_of(state))
    final_step = state["steps"][-1]["n"]
    integrate = as_dict(state.get("integrate"))
    merge_records = as_dict(integrate.get("merges"))
    final_merge = as_dict(merge_records.get(str(final_step))).get("merge_commit")
    recorded_tip = require_full_sha(final_merge, "final recorded step merge")
    sync = as_dict(integrate.get("sync"))
    expected_tip = recorded_tip
    if sync:
        recorded_product = sync.get("product_evidence")
        if recorded_product is not None and recorded_product != product_evidence_record(
            state, recorded_tip
        ):
            die("recorded product evidence changed after the integration sync")
        previous_sync = _active_sync_predecessor(
            integrate, sync.get("commit")
        )
        _require_sync_resolution_guard(
            args.dir,
            sync,
            recorded_tip,
            previous_sync=previous_sync,
        )
        expected_tip = require_full_sha(sync.get("commit"), "recorded run sync commit")
    if remote_tip != expected_tip:
        if sync:
            die("remote run branch tip does not match the recorded run sync commit")
        die("remote run branch tip does not match the final recorded step merge")
    terminal_resolution = terminal_version_resolution(
        args.dir, state, args.merge_commit
    )
    pr_record = inspect_pull_request(
        args.dir,
        args.pr_url,
        expected_head=run_branch_of(state),
        expected_base=integration_base,
        expected_head_sha=remote_tip,
        expected_merge_sha=args.merge_commit,
        expected_head_label="remote run branch tip",
        expected_closing_issue=expected_issue,
    )
    github_verified = verify_github_commits(args.dir, [args.merge_commit])
    attribution = merged_attribution(args.dir, state, args.merge_commit)
    state["receipts"]["integrate"] = {
        "run_branch": run_branch_of(state),
        "base": integration_base,
        "starting_base": state["base"],
        "pr_url": args.pr_url,
        "merge_commit": args.merge_commit,
        "closed_issue_url": args.closed_issue_url,
        "carried_forward": carried_forward_record(run_pr_path(args.dir)),
        "github_verified": github_verified,
        "pull_request": pr_record,
        "run_head": remote_tip,
        "final_step_merge": recorded_tip,
        "attribution": attribution,
        "frontier_subtracted_rows": frontier_subtracted_rows(
            args.dir, frontier, published
        ) if frontier else [],
    }
    if terminal_resolution is not None:
        state["receipts"]["integrate"]["version_resolution"] = terminal_resolution
    if sync:
        state["receipts"]["integrate"]["sync"] = sync
        state["receipts"]["integrate"]["superseded_syncs"] = list(
            integrate.get("superseded_syncs") or []
        )
    worktree = configured_git_path(state, "worktree")
    if worktree and os.path.isdir(worktree):
        state["receipts"]["integrate"]["worktree_clean"] = worktree_is_clean(worktree)
    state["phase"] = "done"
    commit(args.dir, state, "done:integrate", state["receipts"]["integrate"])
    if worktree and os.path.isdir(worktree):
        clean = state["receipts"]["integrate"]["worktree_clean"]
        print(
            f"run worktree {worktree} "
            + ("is clean; `hexctl reset` will archive the run and remove it"
               if clean else
               "holds modifications; `hexctl reset` will archive the run and "
               "keep the tree. Nothing is ever forced")
        )
    print(
        f"{run_branch_of(state)} merged into {integration_base} "
        f"({args.merge_commit}); run complete"
    )


DONE_HANDLERS = {
    "study": done_study,
    "runbook": done_runbook,
    "implement": done_implement,
    "audit": done_audit,
    "prose": done_prose,
    "push": done_push,
    "merge-step": done_merge_step,
    "sync-run": done_sync_run,
    "resolve-versions": done_resolve_versions,
    "integrate": done_integrate,
}


def cmd_done(args) -> None:
    state = load_state(
        args.dir,
        allow_pending_resolution=args.phase == "resolve-versions",
    )
    handler = DONE_HANDLERS.get(args.phase)
    if handler is None:
        die(f"unknown phase '{args.phase}'")
    handler(args, state)


def receipted_source(base_dir: str, state: dict, name: str):
    """Return a verified source artefact, or None for a legacy receipt."""
    receipt = as_dict(as_dict(state.get("receipts")).get(name))
    expected = receipt.get("sha256")
    if expected is None:
        return None
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        die(f"{name} receipt has an invalid sha256")
    artifact = receipt.get("artifact")
    if not isinstance(artifact, str) or not artifact:
        die(f"{name} receipt has no artefact path")
    path, data = read_bounded_source(base_dir, artifact, f"{name} artefact")
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        die(
            f"{name} artefact digest changed: expected {expected}, got {actual}; "
            "restore the receipted bytes or halt the run"
        )
    return {
        "path": path,
        "sha256": expected,
        "text": decoded_source(data, f"{name} artefact"),
        "receipt": receipt,
    }


def receipted_version_relations(
    base_dir: str, runbook: dict, *, state: dict | None = None
) -> dict | None:
    """Reconstruct one optional anchor from its exact source and Git objects."""
    if state is None:
        state = load_state(base_dir)
    receipt = as_dict(runbook.get("receipt"))
    stored = receipt.get("version_relations")
    source = parse_version_relation_source(runbook["text"])
    if source is None and stored is None:
        return None
    if source is None:
        die("runbook receipt has version relations but its source block is absent", 1)
    if stored is None:
        die("runbook source has version relations but its receipt anchor is absent", 1)
    stored = validate_version_relations_shape(
        stored, "receipts.runbook.version_relations"
    )
    declarations = sorted(
        source["targets"], key=lambda declaration: declaration["skill"]
    )
    recorded = [
        {
            "skill": target["skill"],
            "ledger": target["ledger"],
            "relation": target["relation"],
        }
        for target in stored["targets"]
    ]
    if source["source_sha256"] != stored["source_sha256"] or declarations != recorded:
        die("runbook version relations source does not match its receipt", 1)
    if stored["anchor_commit"] != _relation_init_starting_commit(base_dir, state):
        die(
            "runbook version relations anchor commit does not match the "
            "init starting commit"
        )
    repository = _native_relation_repository_identity(base_dir)
    _require_native_relation_history(base_dir)
    anchor_commit = _native_relation_commit(
        base_dir,
        stored["anchor_commit"],
        "runbook version relations anchor commit",
    )
    if anchor_commit != stored["anchor_commit"]:
        die("runbook version relations anchor commit is not a direct commit object")
    reconstructed = capture_version_relations(
        base_dir, source, anchor_commit
    )
    _require_native_relation_history(base_dir)
    if _native_relation_repository_identity(base_dir) != repository:
        die("version relation repository changed during anchor replay", 1)
    if reconstructed != stored:
        die("runbook version relations anchor does not match its exact Git evidence", 1)
    return stored


# This is Protasis's accepted STEP grammar with only the number-group name
# changed for this packet shape. The selector carries bytes accepted by that
# authority; it does not impose a narrower second grammar.
STEP_HEADING_RE = re.compile(
    r"^##\s+Step\s+(?P<number>\d+)\s*:\s*(?P<title>.*?)\s*$"
)
MARKDOWN_FENCE_RE = re.compile(
    r"^ {0,3}(?P<mark>`{3,}|~{3,})(?P<remainder>.*)$"
)
RISK_REGISTER_INFO = "risk-register"
AMENDMENT_HEADING_RE = re.compile(
    r"^###\s+Amendment\s+--\s+(?P<date>\d{4}-\d{2}-\d{2})\s*$"
)
AMENDMENT_FIELDS = ("What changed", "Why", "Steps touched", "Still holding")
AMENDMENT_FIELD_RE = re.compile(
    r"^\*\*(?P<name>What changed|Why|Steps touched|Still holding)\.\*\*"
    r"(?:\s*(?P<value>.*))?$"
)
ANY_AMENDMENT_FIELD_RE = re.compile(r"^\*\*[^*\n]+\.\*\*(?:\s*.*)?$")
STEP_VERDICT_RE = re.compile(
    r"Step\s+(?P<step>[1-9]\d*)\s*:\s*"
    r"entry\s+(?P<entry>holds|broken)\s*;\s*"
    r"exit\s+(?P<exit>holds|broken)\s*\.",
    re.IGNORECASE,
)
RUNBOOK_FIELDS = ("Goal", "Entry", "Exit", "Files", "Tests", "Disciplines")
COMPLETE_REPLACEMENT_RE = re.compile(
    r"Complete replacement (?P<field>Goal|Entry|Exit|Files|Tests|Disciplines):"
    r"\s*(?P<value>.*?)"
    r"(?=(?:\s+Complete replacement "
    r"(?:Goal|Entry|Exit|Files|Tests|Disciplines):)|\Z)"
)


def markdown_fence(line: str):
    """Return one CommonMark fence marker, excluding invalid backtick info."""
    fence = MARKDOWN_FENCE_RE.match(line)
    if (
        fence is not None
        and fence.group("mark").startswith("`")
        and "`" in fence.group("remainder")
    ):
        return None
    return fence


def markdown_blank(line: str) -> bool:
    """Whether one physical line is blank under CommonMark's ASCII grammar."""
    return re.fullmatch(r"[ \t]*", line) is not None


def markdown_physical_lines(text: str):
    """Yield only CommonMark's LF, CRLF, and CR-delimited physical lines."""
    start = 0
    for ending in re.finditer(r"\r\n|\r|\n", text):
        yield text[start:ending.end()]
        start = ending.end()
    if start < len(text):
        yield text[start:]


def markdown_lines(text: str):
    """Yield source offsets and fence state without treating quoted headings as real."""
    offset = 0
    open_mark = None
    open_length = None
    for physical in markdown_physical_lines(text):
        line = physical.rstrip("\r\n")
        fence = markdown_fence(line)
        was_open = open_mark
        if fence:
            sequence = fence.group("mark")
            mark = sequence[0]
            if open_mark is None:
                open_mark = mark
                open_length = len(sequence)
            elif (
                mark == open_mark
                and len(sequence) >= open_length
                and not fence.group("remainder").strip(" \t")
            ):
                open_mark = None
                open_length = None
            yield offset, offset + len(physical), line, True, was_open
        else:
            yield offset, offset + len(physical), line, open_mark is not None, was_open
        offset += len(physical)


def _study_amendment_boundary(
    text: str,
    expected: str,
    subject: str = "study",
    *,
    shape_already_accepted: bool = False,
) -> tuple[int, int, str]:
    """Find the one real final amendment whose byte prefix has the receipt hash."""
    headings = []
    for start, _, line, in_fence, _ in markdown_lines(text):
        if in_fence:
            continue
        match = AMENDMENT_HEADING_RE.fullmatch(line)
        if match:
            headings.append((start, match.group("date")))

    matches = []
    for heading_start, date_text in headings:
        boundary = heading_start
        candidates = [boundary]
        while boundary > 0 and text[boundary - 1] in "\r\n":
            boundary -= 1
            candidates.append(boundary)
        for candidate in candidates:
            digest = hashlib.sha256(text[:candidate].encode("utf-8")).hexdigest()
            if digest == expected:
                matches.append((candidate, heading_start, date_text))

    if not matches:
        die(
            "amendment candidate does not preserve the currently receipted "
            f"{subject} bytes as its exact prefix"
        )
    if len(matches) != 1:
        die("amendment candidate has an ambiguous receipted prefix boundary")
    boundary, heading_start, date_text = matches[0]
    later = [start for start, _ in headings if start > heading_start]
    if later:
        die("amendment candidate appends more than one final amendment block")
    if not shape_already_accepted:
        try:
            datetime.date.fromisoformat(date_text)
        except ValueError:
            die(f"amendment heading has an invalid calendar date: {date_text}")
    return boundary, heading_start, date_text


def _runbook_amendment_boundary(text: str, expected: str) -> tuple[int, int, str]:
    """Use the same append boundary while naming the runbook subject."""
    return _study_amendment_boundary(text, expected, "runbook")


def _study_amendment_fields(
    text: str, heading_start: int, subject: str = "study"
) -> dict[str, str]:
    """Read the four ordered fields in the final amendment and nothing else."""
    fields = []
    headings_after = []
    for start, end, line, in_fence, _ in markdown_lines(text):
        if start <= heading_start or in_fence:
            continue
        if re.fullmatch(r"#{1,3}\s+.*", line):
            headings_after.append(line)
        match = AMENDMENT_FIELD_RE.fullmatch(line)
        if match:
            fields.append((start, end, match.group("name"), match.group("value") or ""))
            continue
        if ANY_AMENDMENT_FIELD_RE.fullmatch(line):
            die(f"amendment carries an unexpected field: {line}")
    if headings_after:
        die(f"amendment block must be the final section of the {subject}")

    names = [item[2] for item in fields]
    if names != list(AMENDMENT_FIELDS):
        for name in AMENDMENT_FIELDS:
            count = names.count(name)
            if count != 1:
                die(f"amendment field '{name}' must occur exactly once (got {count})")
        die("amendment fields must appear in the accepted four-field order")

    values = {}
    for index, (_, end, name, first_line) in enumerate(fields):
        stop = fields[index + 1][0] if index + 1 < len(fields) else len(text)
        value = " ".join((first_line + "\n" + text[end:stop]).split())
        if not value:
            die(f"amendment field '{name}' must not be empty")
        values[name] = value
    return values


def _accepted_study_amendment_fields(
    text: str, heading_start: int
) -> dict[str, str]:
    """Extract controller-owned values after Protasis accepted the shape.

    Protasis owns the dated four-field grammar. Fiat needs only the two fields
    that join the accepted suffix to controller state, so this extractor makes
    no second cardinality, ordering, name, or non-empty-value verdict.
    """
    fields = []
    for start, end, line, in_fence, _ in markdown_lines(text):
        if start <= heading_start or in_fence:
            continue
        match = ANY_AMENDMENT_FIELD_RE.fullmatch(line)
        if match:
            name, _, first_line = line[2:].partition(".**")
            fields.append((start, end, name, first_line.strip()))

    values = {}
    for index, (_, end, name, first_line) in enumerate(fields):
        stop = fields[index + 1][0] if index + 1 < len(fields) else len(text)
        value = " ".join((first_line + "\n" + text[end:stop]).split())
        if name in ("Steps touched", "Still holding"):
            values[name] = value

    missing = [name for name in ("Steps touched", "Still holding") if name not in values]
    if missing:
        die("Protasis accepted a study amendment Fiat could not consume", 1)
    return values


def _complete_replacement_fields(value: str) -> list[str]:
    """Parse an exhaustive sequence of named full-field replacements."""
    matches = list(COMPLETE_REPLACEMENT_RE.finditer(value))
    if not matches:
        die(
            "runbook amendment field 'What changed' must restate at least one "
            "complete field as 'Complete replacement Exit: <full value>'"
        )
    cursor = 0
    fields = []
    for match in matches:
        if value[cursor:match.start()].strip():
            die(
                "runbook amendment field 'What changed' must contain only "
                "complete replacement clauses"
            )
        field = match.group("field")
        if not match.group("value").strip():
            die(f"runbook amendment has an empty complete replacement {field}")
        fields.append(field)
        cursor = match.end()
    if value[cursor:].strip():
        die(
            "runbook amendment field 'What changed' must contain only "
            "complete replacement clauses"
        )
    duplicates = sorted({field for field in fields if fields.count(field) > 1})
    if duplicates:
        die(f"runbook amendment repeats complete replacement field(s): {duplicates}")
    return fields


def _runbook_topology(text: str) -> list[tuple[int, str]]:
    """Return only the original numbered steps, before the first real amendment."""
    topology = []
    amendment_started = False
    for _, _, line, in_fence, _ in markdown_lines(text):
        if in_fence:
            continue
        if AMENDMENT_HEADING_RE.fullmatch(line):
            amendment_started = True
            continue
        match = STEP_HEADING_RE.fullmatch(line)
        if match:
            if amendment_started:
                die("runbook amendment cannot append a replacement Step heading")
            topology.append((int(match.group("number")), match.group("title")))
    return topology


def _require_runbook_topology(state: dict, text: str) -> None:
    expected = [(step["n"], step["title"]) for step in state["steps"]]
    actual = _runbook_topology(text)
    if actual != expected:
        die(
            "runbook amendment cannot add, remove, reorder, renumber, rename, "
            "or duplicate steps"
        )


def _study_step_verdicts(fields: dict[str, str], state: dict) -> tuple[list[int], list[dict]]:
    """Bind touched steps and exact entry/exit verdicts to every unbuilt step."""
    touched_text = fields["Steps touched"]
    if re.search(r"\bsteps?\b", touched_text, re.IGNORECASE) is None:
        die("amendment field 'Steps touched' must name at least one step number")
    touched = sorted({int(value) for value in re.findall(r"\b\d+\b", touched_text)})
    if not touched:
        die("amendment field 'Steps touched' must name at least one step number")

    all_steps = {step["n"]: step for step in state["steps"]}
    unknown_touched = [number for number in touched if number not in all_steps]
    if unknown_touched:
        die(f"amendment names unknown touched step(s): {unknown_touched}")
    completed_touched = [
        number for number in touched if all_steps[number].get("status") == "done"
    ]
    if completed_touched:
        die(f"amendment cannot rewrite completed step(s): {completed_touched}")

    verdict_text = fields["Still holding"]
    verdicts = []
    cursor = 0
    for match in STEP_VERDICT_RE.finditer(verdict_text):
        if verdict_text[cursor:match.start()].strip():
            die(
                "amendment field 'Still holding' must contain only unambiguous "
                "'Step N: entry holds|broken; exit holds|broken.' verdicts"
            )
        verdicts.append(
            {
                "step": int(match.group("step")),
                "entry": match.group("entry").lower(),
                "exit": match.group("exit").lower(),
            }
        )
        cursor = match.end()
    if verdict_text[cursor:].strip():
        die(
            "amendment field 'Still holding' must contain only unambiguous "
            "'Step N: entry holds|broken; exit holds|broken.' verdicts"
        )

    numbers = [verdict["step"] for verdict in verdicts]
    duplicates = sorted({number for number in numbers if numbers.count(number) > 1})
    if duplicates:
        die(f"amendment has duplicate step verdict(s): {duplicates}")

    unbuilt = sorted(
        step["n"] for step in state["steps"] if step.get("status") != "done"
    )
    completed = sorted(set(numbers) - set(unbuilt))
    if completed:
        die(f"amendment cannot rewrite completed or unknown step(s): {completed}")
    missing = sorted(set(unbuilt) - set(numbers))
    if missing:
        die(f"amendment is missing verdict(s) for unbuilt step(s): {missing}")
    return touched, sorted(verdicts, key=lambda item: item["step"])


def _check_amended_study(base_dir: str, candidate: bytes) -> None:
    """Run Protasis over the exact captured bytes through a controlled file."""
    root = state_root(base_dir)
    os.makedirs(root, exist_ok=True)
    descriptor, path = tempfile.mkstemp(prefix="amended-study-", suffix=".md", dir=root)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(candidate)
            handle.flush()
            os.fsync(handle.fileno())
        checker = os.path.join(plugin_root(), "skills", "protasis", "scripts", "protasis.py")
        bounded_tool(
            base_dir,
            sys.executable,
            [checker, "--study", path],
            "Protasis rejected the amendment candidate",
        )
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def _check_amended_runbook(base_dir: str, candidate: bytes) -> None:
    """Run Protasis runbook mode over the exact captured candidate bytes."""
    root = state_root(base_dir)
    os.makedirs(root, exist_ok=True)
    descriptor, path = tempfile.mkstemp(
        prefix="amended-runbook-", suffix=".md", dir=root
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(candidate)
            handle.flush()
            os.fsync(handle.fileno())
        checker = os.path.join(
            plugin_root(), "skills", "protasis", "scripts", "protasis.py"
        )
        bounded_tool(
            base_dir,
            sys.executable,
            [checker, path],
            "Protasis rejected the runbook amendment candidate",
        )
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def _replace_study_bytes(path: str, data: bytes) -> None:
    """Replace the canonical study atomically after every validation has passed."""
    directory = os.path.dirname(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".hexctl-study-", dir=directory)
    try:
        os.fchmod(descriptor, os.stat(path).st_mode & 0o777)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        parent = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    except OSError as exc:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        die(f"study artefact could not be replaced atomically: {exc}", 1)


def _replace_runbook_bytes(path: str, data: bytes) -> None:
    """Replace the canonical runbook atomically after complete validation."""
    directory = os.path.dirname(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".hexctl-runbook-", dir=directory)
    try:
        os.fchmod(descriptor, os.stat(path).st_mode & 0o777)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        parent = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    except OSError as exc:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        die(f"runbook artefact could not be replaced atomically: {exc}", 1)


def _study_amendment_record(
    state: dict, expected: str, candidate: bytes
) -> dict:
    """Join Protasis-accepted bytes to bounded controller receipt data."""
    text = decoded_source(candidate, "study amendment candidate")
    boundary, heading_start, date_text = _study_amendment_boundary(
        text, expected, shape_already_accepted=True
    )
    fields = _accepted_study_amendment_fields(text, heading_start)
    touched, verdicts = _study_step_verdicts(fields, state)
    prefix_bytes = text[:boundary].encode("utf-8")
    amendment_bytes = candidate[len(prefix_bytes):]
    return {
        "date": date_text,
        "prior_sha256": hashlib.sha256(prefix_bytes).hexdigest(),
        "new_sha256": hashlib.sha256(candidate).hexdigest(),
        "amendment_sha256": hashlib.sha256(amendment_bytes).hexdigest(),
        "steps_touched": touched,
        "step_verdicts": verdicts,
    }


def _runbook_amendment_record(
    state: dict, expected: str, candidate: bytes
) -> dict:
    """Validate one runbook suffix and retain only bounded receipt evidence."""
    text = decoded_source(candidate, "runbook amendment candidate")
    boundary, heading_start, date_text = _runbook_amendment_boundary(text, expected)
    fields = _study_amendment_fields(text, heading_start, "runbook")
    replacement_fields = _complete_replacement_fields(fields["What changed"])
    touched, verdicts = _study_step_verdicts(fields, state)
    _require_runbook_topology(state, text)
    prefix_bytes = text[:boundary].encode("utf-8")
    amendment_bytes = candidate[len(prefix_bytes):]
    study_digest = as_dict(as_dict(state.get("receipts")).get("study")).get(
        "sha256"
    )
    if not isinstance(study_digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", study_digest
    ):
        die("runbook amendment requires a source-bound current study digest")
    return {
        "date": date_text,
        "prior_sha256": hashlib.sha256(prefix_bytes).hexdigest(),
        "new_sha256": hashlib.sha256(candidate).hexdigest(),
        "amendment_sha256": hashlib.sha256(amendment_bytes).hexdigest(),
        "amendment_start": len(prefix_bytes),
        "amendment_end": len(candidate),
        "steps_touched": touched,
        "step_verdicts": verdicts,
        "replacement_fields": replacement_fields,
        "study_sha256": study_digest,
    }


def _apply_study_amendment_receipt(receipt: dict, amendment: dict) -> None:
    history = receipt.setdefault("amendments", [])
    history.append(amendment)
    receipt["sha256"] = amendment["new_sha256"]


def _apply_runbook_amendment_receipt(receipt: dict, amendment: dict) -> None:
    history = receipt.setdefault("amendments", [])
    history.append(amendment)
    receipt["sha256"] = amendment["new_sha256"]


def _commit_or_complete_study_amendment(
    base_dir: str, state: dict, amendment: dict
) -> None:
    """Do not duplicate an event written before an interrupted state replace."""
    last = None
    path = ledger_path(base_dir)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = [line for line in handle.read().splitlines() if line.strip()]
        if lines:
            last = json.loads(lines[-1])
    except (OSError, ValueError):
        last = None
    expected_state = state_fingerprint(state)
    if (
        isinstance(last, dict)
        and last.get("event") == "amend:study"
        and last.get("data") == amendment
        and last.get("state") == expected_state
    ):
        save_state(base_dir, state)
        return
    commit(base_dir, state, "amend:study", amendment)


def _commit_or_complete_runbook_amendment(
    base_dir: str, state: dict, amendment: dict
) -> None:
    """Complete the state write without duplicating a durable ledger event."""
    last = None
    path = ledger_path(base_dir)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = [line for line in handle.read().splitlines() if line.strip()]
        if lines:
            last = json.loads(lines[-1])
    except (OSError, ValueError):
        last = None
    expected_state = state_fingerprint(state)
    if (
        isinstance(last, dict)
        and last.get("event") == "amend:runbook"
        and last.get("data") == amendment
        and last.get("state") == expected_state
    ):
        save_state(base_dir, state)
        return
    commit(base_dir, state, "amend:runbook", amendment)


def _recover_study_amendment(
    base_dir: str, state: dict, pending: dict
) -> bool:
    """Finish or roll back the labelled gap left by an interrupted command.

    Returns True after the pending amendment is committed or visibly rolled
    back. A later command may retry a rolled-back candidate as a fresh
    transaction.
    """
    receipt = as_dict(as_dict(state.get("receipts")).get("study"))
    artifact = receipt.get("artifact")
    if artifact != pending["artifact"]:
        die("pending study amendment does not match the current artefact path", 1)
    amendment = pending["amendment"]
    prior = amendment.get("prior_sha256")
    new = amendment.get("new_sha256")
    if not all(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
        for value in (prior, new)
    ):
        die("pending study amendment has invalid receipt digests", 1)

    canonical_path, canonical = read_bounded_source(
        base_dir, artifact, "study artefact"
    )
    actual = hashlib.sha256(canonical).hexdigest()
    current = receipt.get("sha256")

    if current == new:
        history = receipt.get("amendments")
        if (
            actual != new
            or not isinstance(history, list)
            or not history
            or history[-1] != amendment
        ):
            die("pending study amendment disagrees with the committed receipt", 1)
        verify_run(base_dir, allow_pending_amendment=True)
        clear_study_amendment_pending(base_dir)
        print(f"study amendment recovered: committed {new}")
        return True

    if current != prior or state_fingerprint(state) != pending["state_before_sha256"]:
        die("pending study amendment no longer matches controller state", 1)
    if actual == prior:
        verify_run(base_dir, allow_pending_amendment=True)
        clear_study_amendment_pending(base_dir)
        print(f"study amendment recovered: rolled back to {prior}")
        return True
    if actual != new:
        die(
            "pending study amendment found neither the prior nor candidate bytes; "
            "restore one recorded digest before recovery",
            1,
        )

    _check_amended_study(base_dir, canonical)
    recovered = _study_amendment_record(state, prior, canonical)
    if recovered != amendment:
        die("pending study amendment metadata does not match the candidate bytes", 1)
    existing_history = receipt.get("amendments")
    if existing_history is not None and not isinstance(existing_history, list):
        die("study receipt amendments history must be an array", 1)
    _apply_study_amendment_receipt(receipt, amendment)
    _commit_or_complete_study_amendment(base_dir, state, amendment)
    verify_run(base_dir, allow_pending_amendment=True)
    clear_study_amendment_pending(base_dir)
    print(f"study amendment recovered: recorded {new}")
    return True


def cmd_amend_study(args) -> None:
    """Receipt one append-only Protasis amendment while build steps are active."""
    state = load_state(args.dir, allow_pending_amendment=True)
    pending_by_subject = pending_amendments(args.dir)
    if pending_by_subject:
        if "study" not in pending_by_subject:
            die(
                "runbook amendment transaction is pending; recover that exact "
                "subject before amending the study"
            )
        if _recover_study_amendment(
            args.dir, state, pending_by_subject["study"]
        ):
            return
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state.get("phase") != "steps":
        die("study amendments are accepted only while build steps are active")
    require_no_amendment_block(state)

    receipt = as_dict(as_dict(state.get("receipts")).get("study"))
    expected = receipt.get("sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        die("study amendment requires a source-bound study receipt with sha256")
    artifact = receipt.get("artifact")
    if not isinstance(artifact, str) or not artifact:
        die("study receipt has no artefact path")

    candidate_arg = _require_file(args.artifact, "artifact")
    candidate_path, candidate = read_bounded_source(
        args.dir, candidate_arg, "study amendment candidate"
    )
    canonical_path, canonical_bytes = read_bounded_source(
        args.dir, artifact, "study artefact"
    )
    if candidate_path != canonical_path:
        actual = hashlib.sha256(canonical_bytes).hexdigest()
        if actual != expected and canonical_bytes != candidate:
            die(
                f"study artefact digest changed: expected {expected}, got {actual}; "
                "restore the receipted bytes or halt the run"
            )

    _check_amended_study(args.dir, candidate)
    amendment = _study_amendment_record(state, expected, candidate)
    existing_history = receipt.get("amendments")
    if existing_history is not None and not isinstance(existing_history, list):
        die("study receipt amendments history must be an array", 1)

    pending = {
        "version": 1,
        "artifact": artifact,
        "state_before_sha256": state_fingerprint(state),
        "amendment": amendment,
    }
    write_study_amendment_pending(args.dir, pending)
    # Replace from the captured bytes even when the candidate is already the
    # canonical path. An editor can change that path after the bounded read;
    # the receipt must name the bytes this command validated, not a later read.
    _replace_study_bytes(canonical_path, candidate)
    _apply_study_amendment_receipt(receipt, amendment)
    commit(args.dir, state, "amend:study", amendment)
    verify_run(args.dir, allow_pending_amendment=True)
    clear_study_amendment_pending(args.dir)

    current = state["current_step"]
    verdict = next(item for item in amendment["step_verdicts"] if item["step"] == current)
    disposition = (
        "holds" if verdict["entry"] == "holds" and verdict["exit"] == "holds"
        else "broken; dependent work is blocked"
    )
    print(
        f"study amended: prior {amendment['prior_sha256']}; "
        f"new {amendment['new_sha256']}; amendment "
        f"{amendment['amendment_sha256']}; step {current} {disposition}"
    )


def _recover_runbook_amendment(
    base_dir: str, state: dict, pending: dict
) -> bool:
    """Finish or roll back one interrupted runbook amendment exactly once."""
    receipt = as_dict(as_dict(state.get("receipts")).get("runbook"))
    artifact = receipt.get("artifact")
    if artifact != pending["artifact"]:
        die("pending runbook amendment does not match the current artefact path", 1)
    amendment = pending["amendment"]
    prior = amendment.get("prior_sha256")
    new = amendment.get("new_sha256")
    if not all(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
        for value in (prior, new)
    ):
        die("pending runbook amendment has invalid receipt digests", 1)

    canonical_path, canonical = read_bounded_source(
        base_dir, artifact, "runbook artefact"
    )
    actual = hashlib.sha256(canonical).hexdigest()
    current = receipt.get("sha256")

    if current == new:
        history = receipt.get("amendments")
        if (
            actual != new
            or not isinstance(history, list)
            or not history
            or history[-1] != amendment
        ):
            die("pending runbook amendment disagrees with the committed receipt", 1)
        verify_run(base_dir, allow_pending_amendment=True)
        clear_amendment_pending(base_dir, "runbook")
        print(f"runbook amendment recovered: committed {new}")
        return True

    if current != prior or state_fingerprint(state) != pending["state_before_sha256"]:
        die("pending runbook amendment no longer matches controller state", 1)
    if actual == prior:
        verify_run(base_dir, allow_pending_amendment=True)
        clear_amendment_pending(base_dir, "runbook")
        print(f"runbook amendment recovered: rolled back to {prior}")
        return True
    if actual != new:
        die(
            "pending runbook amendment found neither the prior nor candidate bytes; "
            "restore one recorded digest before recovery",
            1,
        )

    recovered = _runbook_amendment_record(state, prior, canonical)
    _check_amended_runbook(base_dir, canonical)
    if recovered != amendment:
        die("pending runbook amendment metadata does not match candidate bytes", 1)
    existing_history = receipt.get("amendments")
    if existing_history is not None and not isinstance(existing_history, list):
        die("runbook receipt amendments history must be an array", 1)
    if len(existing_history or []) >= AMENDMENT_HISTORY_MAX:
        die(f"runbook amendment history is capped at {AMENDMENT_HISTORY_MAX}")
    _apply_runbook_amendment_receipt(receipt, amendment)
    _commit_or_complete_runbook_amendment(base_dir, state, amendment)
    verify_run(base_dir, allow_pending_amendment=True)
    clear_amendment_pending(base_dir, "runbook")
    print(f"runbook amendment recovered: recorded {new}")
    return True


def cmd_amend_runbook(args) -> None:
    """Receipt one append-only Protasis runbook amendment during build steps."""
    state = load_state(args.dir, allow_pending_amendment=True)
    pending_by_subject = pending_amendments(args.dir)
    if pending_by_subject:
        if "runbook" not in pending_by_subject:
            die(
                "study amendment transaction is pending; recover that exact "
                "subject before amending the runbook"
            )
        if _recover_runbook_amendment(
            args.dir, state, pending_by_subject["runbook"]
        ):
            return
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state.get("phase") != "steps":
        die("runbook amendments are accepted only while build steps are active")

    receipt = as_dict(as_dict(state.get("receipts")).get("runbook"))
    expected = receipt.get("sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        die("runbook amendment requires a source-bound runbook receipt with sha256")
    artifact = receipt.get("artifact")
    if not isinstance(artifact, str) or not artifact:
        die("runbook receipt has no artefact path")

    candidate_arg = _require_file(args.artifact, "artifact")
    candidate_path, candidate = read_bounded_source(
        args.dir, candidate_arg, "runbook amendment candidate"
    )
    canonical_path, canonical_bytes = read_bounded_source(
        args.dir, artifact, "runbook artefact"
    )
    if candidate_path != canonical_path:
        actual = hashlib.sha256(canonical_bytes).hexdigest()
        if actual != expected and canonical_bytes != candidate:
            die(
                f"runbook artefact digest changed: expected {expected}, got "
                f"{actual}; restore the receipted bytes or halt the run"
            )

    amendment = _runbook_amendment_record(state, expected, candidate)
    _check_amended_runbook(args.dir, candidate)
    existing_history = receipt.get("amendments")
    if existing_history is not None and not isinstance(existing_history, list):
        die("runbook receipt amendments history must be an array", 1)
    if len(existing_history or []) >= AMENDMENT_HISTORY_MAX:
        die(f"runbook amendment history is capped at {AMENDMENT_HISTORY_MAX}")

    pending = {
        "version": 1,
        "artifact": artifact,
        "state_before_sha256": state_fingerprint(state),
        "amendment": amendment,
    }
    write_amendment_pending(args.dir, "runbook", pending)
    _replace_runbook_bytes(canonical_path, candidate)
    _apply_runbook_amendment_receipt(receipt, amendment)
    commit(args.dir, state, "amend:runbook", amendment)
    verify_run(args.dir, allow_pending_amendment=True)
    clear_amendment_pending(args.dir, "runbook")

    current = state["current_step"]
    verdict = next(
        item for item in amendment["step_verdicts"] if item["step"] == current
    )
    disposition = (
        "holds" if verdict["entry"] == "holds" and verdict["exit"] == "holds"
        else "broken; dependent work is blocked"
    )
    print(
        f"runbook amended: prior {amendment['prior_sha256']}; "
        f"new {amendment['new_sha256']}; amendment "
        f"{amendment['amendment_sha256']}; study "
        f"{amendment['study_sha256']}; step {current} {disposition}"
    )


def _receipted_runbook_amendments(source: dict) -> list[dict]:
    """Recompute each exact amendment slice from its bounded receipt offsets."""
    receipt = as_dict(source.get("receipt"))
    history = receipt.get("amendments")
    if history is None:
        return []
    if not isinstance(history, list):
        die("runbook receipt amendments history must be an array", 1)
    if len(history) > AMENDMENT_HISTORY_MAX:
        die(
            f"runbook receipt has more than {AMENDMENT_HISTORY_MAX} amendments",
            1,
        )
    data = source["text"].encode("utf-8")
    verified = []
    previous_end = None
    for index, raw in enumerate(history, 1):
        item = as_dict(raw)
        start = item.get("amendment_start")
        end = item.get("amendment_end")
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or start < 0
            or end <= start
            or end > len(data)
            or (previous_end is not None and start != previous_end)
        ):
            die(f"runbook amendment {index} has invalid source offsets", 1)
        prior = hashlib.sha256(data[:start]).hexdigest()
        new = hashlib.sha256(data[:end]).hexdigest()
        amendment_bytes = data[start:end]
        amendment_digest = hashlib.sha256(amendment_bytes).hexdigest()
        if (
            item.get("prior_sha256") != prior
            or item.get("new_sha256") != new
            or item.get("amendment_sha256") != amendment_digest
        ):
            die(f"runbook amendment {index} digest evidence does not match source", 1)
        verified.append(
            {
                **item,
                "markdown": decoded_source(
                    amendment_bytes, f"runbook amendment {index}"
                ),
            }
        )
        previous_end = end
    if verified and verified[-1].get("new_sha256") != source.get("sha256"):
        die("runbook amendment history does not reach the current receipt", 1)
    return verified


def source_runbook_step(
    source: dict,
    step: dict,
    *,
    current_study_sha256: str | None = None,
    version_relations: dict | None = None,
) -> dict:
    """Carry one exact baseline step plus its current receipted amendments."""
    text = source["text"]
    amendments = _receipted_runbook_amendments(source)
    if amendments:
        baseline_bytes = text.encode("utf-8")[: amendments[0]["amendment_start"]]
        baseline_text = decoded_source(baseline_bytes, "runbook baseline")
    else:
        baseline_text = text
    headings = []
    for start, _, line, in_fence, _ in markdown_lines(baseline_text):
        if in_fence:
            continue
        match = STEP_HEADING_RE.fullmatch(line)
        if match:
            headings.append((start, match))
    matches = []
    for index, (start, heading) in enumerate(headings):
        if int(heading.group("number")) != step["n"]:
            continue
        if heading.group("title") != step["title"]:
            continue
        end = (
            headings[index + 1][0]
            if index + 1 < len(headings)
            else len(baseline_text)
        )
        matches.append(baseline_text[start:end])
    if not matches:
        die(
            f"runbook step {step['n']} '{step['title']}' has no exact source block"
        )
    if len(matches) != 1:
        die(f"ambiguous runbook step {step['n']} '{step['title']}'")
    baseline = matches[0]
    applicable = []
    for amendment in amendments:
        if step["n"] not in (amendment.get("steps_touched") or []):
            continue
        if amendment.get("study_sha256") != current_study_sha256:
            continue
        applicable.append(
            {
                "markdown": amendment["markdown"],
                "sha256": amendment["amendment_sha256"],
                "runbook_sha256": amendment["new_sha256"],
                "study_sha256": amendment["study_sha256"],
                "date": amendment["date"],
                "steps_touched": amendment["steps_touched"],
                "replacement_fields": amendment["replacement_fields"],
            }
        )
    markdown = baseline + "".join(item["markdown"] for item in applicable)
    packet = {
        "markdown": markdown,
        "baseline_markdown": baseline,
        "baseline_sha256": hashlib.sha256(baseline.encode("utf-8")).hexdigest(),
        "amendments": applicable,
        "effective_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "path": source["path"],
        "sha256": source["sha256"],
        "number": step["n"],
        "title": step["title"],
    }
    if version_relations is not None:
        packet["version_relations"] = version_relations_packet(version_relations)
    return packet


def source_risk_register(source: dict) -> dict:
    """Carry the unique fenced register; Protasis remains its shape authority."""
    text = source["text"]
    matches = []
    start = None
    risk_mark = None
    for line_start, line_end, line, is_fence, was_open in markdown_lines(text):
        if start is None and was_open is None and is_fence:
            opened = markdown_fence(line)
            if opened:
                mark = opened.group("mark")
                info = line.strip()[len(mark):].strip()
            else:
                info = None
            if info == RISK_REGISTER_INFO:
                start = line_start
                risk_mark = mark[0]
            continue
        if start is not None and is_fence and was_open == risk_mark:
            fence = markdown_fence(line)
            if fence and fence.group("mark")[0] == risk_mark:
                matches.append(text[start:line_end])
                start = None
                risk_mark = None
    if not matches:
        die("study artefact has no fenced risk-register block")
    if len(matches) != 1:
        die("study artefact has an ambiguous fenced risk-register block")
    return {
        "markdown": matches[0],
        "path": source["path"],
        "sha256": source["sha256"],
    }


def bounded_probe(
    base_dir: str,
    program: str,
    argv: list[str],
    extra_env: dict | None = None,
    *,
    environment: dict[str, str] | None = None,
) -> tuple[int | None, bytes, str | None]:
    """Run one fixed-argv tool and report failure instead of refusing.

    The reader core `bounded_run` wraps: no shell, a hard timeout, a hard
    output cap, and nothing from the child's stream in any diagnosis. This
    surface exists for callers that must keep going when the child cannot
    answer, such as the currency observation, where a stalled read is a
    recorded `unknown` rather than a refusal. Returns (returncode, output,
    failure); failure is None, "start", "timeout" or "output-cap", and the
    returncode is None whenever the child never finished cleanly.
    """
    # `environment` replaces the child's environment outright; `extra_env`
    # layers over the parent's. The native relation readers need the first,
    # because inheriting GIT_* is exactly what they strip.
    if environment is not None:
        env = environment
    elif extra_env is not None:
        env = {**os.environ, **extra_env}
    else:
        env = None
    try:
        process = subprocess.Popen(
            [program, *argv],
            cwd=os.path.realpath(base_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            env=env,
        )
    except OSError:
        return None, b"", "start"
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    output = bytearray()
    deadline = time.monotonic() + GIT_TIMEOUT
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                process.wait()
                return None, bytes(output), "timeout"
            events = selector.select(min(remaining, 0.1))
            if not events and process.poll() is not None:
                events = [(key, selectors.EVENT_READ) for key in selector.get_map().values()]
            for key, _ in events:
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                output.extend(chunk)
                if len(output) > GIT_OUTPUT_MAX:
                    process.kill()
                    process.wait()
                    return None, bytes(output), "output-cap"
        returncode = process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return None, bytes(output), "timeout"
    finally:
        selector.close()
        process.stdout.close()
    return returncode, bytes(output), None


def bounded_run(
    base_dir: str,
    program: str,
    argv: list[str],
    *,
    environment: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    """Run one fixed-argv tool and return its status and output.

    The reader itself: no shell, a hard timeout, a hard output cap, and nothing
    from the child's stream in any diagnosis. Callers that treat a non-zero
    status as fatal go through `bounded_tool`; callers for which a refusal is a
    real answer, such as git declining to remove a tree holding modifications,
    read the status here.
    """
    operation = f"{program} {argv[0]}" if argv else program
    returncode, output, failure = bounded_probe(
        base_dir, program, argv, environment=environment
    )
    if failure == "start":
        die(f"{operation} could not start")
    if failure == "timeout":
        die(f"{operation} timed out after {GIT_TIMEOUT} seconds")
    if failure == "output-cap":
        die(f"{operation} exceeded {GIT_OUTPUT_MAX}-byte output cap")
    return returncode, output


def bounded_tool(
    base_dir: str,
    program: str,
    argv: list[str],
    refusal: str | None = None,
    *,
    environment: dict[str, str] | None = None,
) -> bytes:
    """Run one fixed-argv tool without exposing its output in failures."""
    returncode, output = bounded_run(
        base_dir, program, argv, environment=environment
    )
    if returncode != 0:
        if refusal is not None:
            die(refusal)
        operation = f"{program} {argv[0]}" if argv else program
        die(f"{operation} failed with exit {returncode}")
    return output


def bounded_tool_status(base_dir: str, program: str, argv: list[str]) -> int:
    """The exit status of one fixed-argv tool, for callers a refusal informs."""
    return bounded_run(base_dir, program, argv)[0]


def bounded_git(base_dir: str, argv: list[str], refusal: str | None = None) -> bytes:
    return bounded_tool(base_dir, "git", argv, refusal)


WORKTREE_HOME = ("tmp", "fiat")
"""Where a run's worktree goes, under the repository's already-ignored scratch root.

Ignoring the home is not what keeps a scan honest: git reports a nested worktree as
one opaque directory either way. It is what keeps the next run startable, because
preflight refuses a dirty tree and an unignored directory here would show as
untracked.
"""


def flattened_run_branch(run_branch: str) -> str:
    """A run branch as one directory name, so one run maps to one path."""
    check_branch_name(run_branch)
    return run_branch.replace("/", "-")


def repository_root(base_dir: str) -> str:
    """The worktree root git reports for `base_dir`.

    A target that is not a Git repository refuses here rather than running in
    place. That is the fail-closed fallback the study chose, and it is a breaking
    change for anyone who relied on an in-place run.
    """
    root = os.path.realpath(base_dir)
    reported = bounded_git(
        base_dir,
        ["rev-parse", "--show-toplevel"],
        refusal=f"not a git repository: {root}",
    ).decode("utf-8", "replace").strip()
    if not reported:
        die(f"not a git repository: {root}")
    return os.path.realpath(reported)


AUDIT_LOG_HOME = ("audit", "rounds")
"""Where a run's own audit record lives, relative to the target directory."""


def run_audit_log_path(run_branch: str) -> str:
    """The one audit log path a run owns, derived from its own branch.

    The branch already names the run's worktree directory, so the same
    flattening names its record. Deriving it beats holding a literal: a shared
    default puts the log on both sides of `sync-run`'s product/upstream
    intersection whenever anything else merged during the run, and the record
    then owes a green check on a file the run only appended to.

    Separators are POSIX because the value is a repository path that is read
    back out of state, printed by `config get`, and quoted in prose.
    """
    return "/".join((*AUDIT_LOG_HOME, flattened_run_branch(run_branch) + ".md"))


def check_audit_log_path(base_dir: str, state: dict, value):
    """Hold an audit log override to the one file this run owns.

    The directory may move -- three plugins here already keep their rounds under
    their own tree -- but the file name is the run's identity. Without that, an
    override can aim at another run's record or back at the shared log, which is
    the arrangement this default was changed to end.

    A run whose state records no usable branch has nothing to derive from, so it
    keeps the older unconstrained value rather than being refused for its age.
    That covers a stored branch of the wrong type as well as an absent one: the
    flattening runs a regex over it, and a state holding a number there would
    otherwise raise rather than answer.
    """
    if not isinstance(value, str) or not value:
        die("config audit.log_path takes a non-empty string")
    run_branch = run_branch_of(state)
    if not isinstance(run_branch, str) or not run_branch:
        return value
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        die("config audit.log_path must carry no control character")
    if os.path.isabs(value):
        die(
            "config audit.log_path is relative to the run's directory; "
            f"got the absolute path '{value}'"
        )
    parts = value.replace("\\", "/").split("/")
    if ".." in parts:
        die(f"config audit.log_path must carry no '..' component; got '{value}'")
    required = run_audit_log_path(run_branch).rsplit("/", 1)[-1]
    if parts[-1] != required:
        die(
            f"config audit.log_path must end in '{required}', the record this "
            f"run owns; got '{value}'. Move the directory if you need to; the "
            "name is what keeps two runs out of one file."
        )
    # Containment last, because a symlinked directory component escapes a path
    # that has already passed every textual check above.
    scoped_path(base_dir, value, "audit log path")
    return value


def run_worktree_path(base_dir: str, run_branch: str) -> str:
    """The one path this run's worktree belongs at. Creates nothing."""
    return os.path.join(
        repository_root(base_dir), *WORKTREE_HOME, flattened_run_branch(run_branch)
    )


def configured_git_path(state: dict, name: str):
    """Read a current Git path, retaining old top-level state compatibility."""
    configured = as_dict(as_dict(state.get("config")).get("git")).get(name)
    return configured if configured is not None else state.get(name)


def check_worktree_path(root: str, candidate: str, registered: str | None = None) -> str:
    """Refuse a worktree path before anything is created at it.

    Five ways a path fails: it leaves the repository once resolved, a component on
    the way to it is a symlink leaving the repository, it is the repository root
    itself, it is a symlink, or it already exists as something other than this
    run's own tree.

    Occupancy is read off the supplied path with `lexists`, not off the resolved
    one. A dangling link resolves to a path that does not exist, so reading the
    target saw a free path and then returned the target rather than the path it
    was asked about -- which would put the run's tree somewhere the deriver never
    chose. A link at the derived path is refused whether it dangles or not: the
    run's tree is a real directory there, or it is nothing.

    The walk is over the supplied components rather than the resolved path. Horos
    finding S4-R1-01 is the reason: a control that inspects only the path it was
    given refuses a final-component symlink while stepping over one mid-path, and
    `git -C` resolves symlinks before it answers, so the refusal has to happen
    before git is asked anything. Traversal is refused on the raw components for
    the same reason -- normalising `..` first is what lets a symlink be stepped
    over lexically.

    Every refusal names the path, reads nothing at it, and writes nothing.
    """
    root = os.path.realpath(root)
    supplied = candidate
    if os.path.isabs(candidate):
        try:
            relative = os.path.relpath(candidate, root)
        except ValueError:
            die(f"worktree path escapes the repository: {supplied}")
    else:
        relative = candidate
    parts = [part for part in relative.split(os.sep) if part not in ("", ".")]
    if not parts or any(part == os.pardir for part in parts):
        die(f"worktree path escapes the repository: {supplied}")
    walked = root
    for part in parts:
        walked = os.path.join(walked, part)
        if os.path.islink(walked) and not contained_in(root, os.path.realpath(walked)):
            die(f"worktree path crosses a symlink out of the repository: {walked}")
    resolved = os.path.realpath(walked)
    if not contained_in(root, resolved) or resolved == root:
        die(f"worktree path escapes the repository: {supplied}")
    if os.path.lexists(walked):
        if os.path.islink(walked):
            die(f"worktree path is a symlink: {supplied}")
        if registered is None or os.path.realpath(registered) != resolved:
            die(f"worktree path is already occupied: {supplied}")
    return resolved


def checked_out_worktrees(base_dir: str) -> dict:
    """Branch -> worktree path, for every tree git currently knows about."""
    porcelain = bounded_git(base_dir, ["worktree", "list", "--porcelain"]).decode(
        "utf-8", "replace"
    )
    trees: dict[str, str] = {}
    path = None
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):].strip()
        elif line.startswith("branch ") and path is not None:
            trees[line[len("branch "):].strip().removeprefix("refs/heads/")] = path
    return trees


def refuse_checked_out_branch(base_dir: str, run_branch: str) -> None:
    """Git holds one branch in one tree, so a second checkout cannot be created.

    Refusing by name here is what turns `git worktree add`'s own failure into a
    sentence that says which branch and which tree, before anything is written.
    """
    existing = checked_out_worktrees(base_dir).get(run_branch)
    if existing is not None:
        die(f"run branch '{run_branch}' is already checked out at {existing}")


def breadcrumb_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), WORKTREE_FILE)


def raw_breadcrumbs(base_dir: str) -> list[str]:
    """Every run this checkout recorded, live or not, as written."""
    try:
        with open(breadcrumb_path(base_dir), encoding="utf-8") as handle:
            return sorted({line.strip() for line in handle if line.strip()})
    except OSError:
        return []


def read_breadcrumbs(base_dir: str) -> list[str]:
    """Every run this checkout started that still has state, in path order.

    One line per run rather than one line per checkout. The issue asks for two
    runs against one repository that do not contend, so a second run has to be
    recordable rather than refused, and a resume has to be able to say which
    trees it found. Entries whose state has gone are dropped on the way out, so
    a finished or reset run stops being offered.
    """
    try:
        with open(breadcrumb_path(base_dir), encoding="utf-8") as handle:
            recorded = [line.strip() for line in handle if line.strip()]
    except OSError:
        return []
    return sorted({entry for entry in recorded if os.path.exists(state_path(entry))})


def write_breadcrumbs(base_dir: str, worktree: str | None = None) -> None:
    """Leave one line in the origin checkout naming the run's tree.

    This is the only thing a run writes into the checkout it was started from. A
    resume reads it so nobody has to remember the path, and it is one line rather
    than state because two state directories for one run is the confusion the
    breadcrumb exists to avoid.
    """
    root = state_root(base_dir)
    os.makedirs(root, exist_ok=True)
    gitignore = os.path.join(root, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w", encoding="utf-8") as handle:
            handle.write("*\n")
    entries = sorted(set(read_breadcrumbs(base_dir)) | ({worktree} if worktree else set()))
    with open(breadcrumb_path(base_dir), "w", encoding="utf-8") as handle:
        handle.write("".join(f"{entry}\n" for entry in entries))


def remove_run_worktree(base_dir: str, worktree: str, force: bool = False) -> bool:
    """Take the run's tree away, and say whether it went.

    Never forced by default. Git refuses to remove a tree holding modifications,
    and that refusal is the point: the worst outcome here is a directory somebody
    has to look at, never uncommitted work that vanished.
    """
    argv = ["worktree", "remove"]
    if force:
        argv.append("--force")
    argv.append(worktree)
    bounded_tool_status(base_dir, "git", argv)
    return not os.path.exists(worktree)


def archive_name(state: dict) -> str:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    topic = re.sub(r"[^a-z0-9]+", "-", state["topic"].lower()).strip("-")[:48]
    return f"{stamp}-{topic or 'completed-run'}"


def worktree_is_clean(worktree: str) -> bool:
    """True when git has nothing to lose in this tree.

    Read before anything is moved. Removal is never forced, so a tree holding
    work is kept and named instead, and the worst outcome here is a directory
    somebody has to look at.
    """
    porcelain = bounded_git(worktree, ["status", "--porcelain"])
    return not porcelain.strip()


def contained_in(root: str, resolved: str) -> bool:
    """True when `resolved` is `root` or sits underneath it."""
    try:
        return os.path.commonpath((root, resolved)) == root
    except ValueError:
        return False


def github_unreachable(label: str, path: str, detail: str) -> None:
    """Refuse a read GitHub never answered, in a shape no verdict shares.

    A verdict refusal says something is wrong with the work. This one says
    nothing was learned about the work: the request failed, or came back as
    something other than the document the check reads. Sharing one shape
    between them tells an operator holding `verified: true` commits that a
    check failed when it was never asked.
    """
    die(
        f"GitHub read for {label} was not answered: GET {path} {detail}. "
        "This is a transport failure, not a verification result; "
        "nothing here says the work is unverified."
    )


def github_rest(base_dir: str, path: str, label: str) -> dict:
    """One bounded REST read of the GitHub API, parsed as one JSON object.

    Every receipt reader goes over REST because that is the transport the
    checks need. `gh <command> --json` speaks GraphQL, and an environment
    serving one and not the other could receipt nothing at all, however the
    commits were signed. REST carries every field these readers ask for.

    The bounds are `bounded_probe`'s rather than `bounded_run`'s so that a
    reader that never started, stalled, or overran its cap refuses as the
    transport failure it is, instead of in the generic tool shape.
    """
    returncode, output, failure = bounded_probe(
        base_dir, "gh", ["api", "--method", "GET", path]
    )
    if failure == "start":
        github_unreachable(label, path, "could not start the gh client")
    if failure == "timeout":
        github_unreachable(label, path, f"timed out after {GIT_TIMEOUT} seconds")
    if failure == "output-cap":
        github_unreachable(label, path, f"exceeded the {GIT_OUTPUT_MAX}-byte output cap")
    if returncode != 0:
        github_unreachable(label, path, f"failed with exit {returncode}")
    try:
        text = output.decode("utf-8")
    except UnicodeDecodeError:
        github_unreachable(label, path, "returned output that is not UTF-8")
    try:
        payload = json.loads(text)
    except ValueError:
        github_unreachable(label, path, "returned a response that is not JSON")
    if not isinstance(payload, dict):
        github_unreachable(label, path, "returned a response that is not one object")
    return payload


COMMIT_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
COAUTHOR_TRAILER = "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>"
ORIGIN_TRAILER = "Wildcat-Origin: shoggoth"
# Long key ids GitHub signs with when it creates a commit itself: the web-flow
# key, used by the merge button, the Contents API, and the rebase performed by
# the native stacked-pull-request flow. A commit carrying one of these was
# rewritten by GitHub, not created locally, so `git verify-commit` cannot
# validate it against a local keyring and the range is not the one that was
# pushed. This set exists to explain a refusal, never to permit one.
GITHUB_SIGNING_KEYS = frozenset(
    {
        "4AEE18F83AFDEB23",
        "B5690EEEBB952194",
    }
)

# A repository may choose its signature format and trust material, but it may
# not replace the native program that decides whether a signature is valid.
# Command-scoped values outrank repository-local config while preserving the
# three formats Git supports.
SIGNATURE_VERIFIER_CONFIG = (
    "gpg.program=gpg",
    "gpg.openpgp.program=gpg",
    "gpg.x509.program=gpgsm",
    "gpg.ssh.program=ssh-keygen",
)


HOST_IDENTITY_NAMES = frozenset(
    {
        "aider",
        "anthropic",
        "chatgpt",
        "claude",
        "claude code",
        "claude[bot]",
        "codex",
        "copilot",
        "cursor",
        "devin",
        "gemini",
        "gemini code assist",
        "github copilot",
        "openai",
    }
)
HOST_IDENTITY_EMAILS = frozenset(
    {
        "noreply@anthropic.com",
        "noreply@openai.com",
    }
)
HOST_PR_LOGINS = frozenset(
    {
        "app/claude",
        "chatgpt[bot]",
        "claude[bot]",
        "codex[bot]",
        "copilot[bot]",
    }
)
"""Runtime host accounts, which ADR-016 forbids as an author.

Membership is a refusal, so this set holds runtime hosts and nothing else. A
delivery agent that opens its own pull requests under a GitHub App identity is
the contributing actor rather than a host, and belongs nowhere near this set:
adding it would refuse every pull request it opens. `GITHUB_LOGIN_RE` already
accepts a `[bot]` login for that reason.
"""
COAUTHOR_RE = re.compile(
    r"^Co-authored-by:\s*(?P<name>.+?)\s*<(?P<email>[^<>]+)>$",
    re.IGNORECASE,
)
GITHUB_LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})(?:\[bot\])?$")
"""One GitHub account login as the commits endpoint spells it.

Closed on purpose. The endpoint's `author` is the account GitHub matched the
commit to, and it is the only field here that later becomes a public claim, so
an unexpected shape refuses rather than being stored and repeated.
"""

ATTRIBUTION_NAME_MAX = 256
ATTRIBUTION_EMAIL_MAX = 320
ATTRIBUTION_COAUTHOR_MAX = 32
"""Caps on the identity fields read out of a GitHub commit payload.

The address cap is RFC 5321's maximum path length. The co-author cap exists
because the trailer count is attacker-influenceable and a receipt is not the
place to discover that.
"""

HOST_BYLINE_RE = re.compile(
    r"(?:generated\s+(?:by|with)|(?:co-)?authored\s+by)\s+"
    r"(?:\[(?:claude(?: code)?|codex|chatgpt|copilot|gemini(?: code assist)?)\]"
    r"\([^\)]+\)|claude(?: code)?|codex|chatgpt|copilot|gemini(?: code assist)?)",
    re.IGNORECASE,
)

# Why a refusal names a cause. ADR-016 makes a runtime host execution metadata,
# never an author, co-author, byline or generated-by footer, and the hosts most
# contributors run Fiat through add exactly those by default: their own git
# identity, a Co-Authored-By trailer naming themselves, an attribution line or
# a session link. A refusal that only names the gate sends the operator to
# guess; one that names the usual host default and its recovery does not. The
# clauses are module constants so that no byte of a commit message or
# pull-request body can steer what a refusal says. The evidence for each
# "usual cause" is the measurement table in the committed study,
# docs/fiat-host-byline-readback/study.md (section 1); the texts are its
# section 4 table.

# verify_local_commit author and commit_attribution (ADR-016; the study's
# section 4 table).
CAUSE_HOST_AUTHOR = (
    "The usual cause is the host's default git identity, such as "
    "Claude <noreply@anthropic.com>; set git user.name and user.email to the "
    "contributing actor and recreate the commit."
)
# verify_local_commit committer and commit_attribution (ADR-052).
CAUSE_HOST_COMMITTER = (
    "The usual cause is the runtime host's default committer identity; use the "
    "explicitly authorised publisher's own name, address and signing key, then "
    "recreate the commit without changing its author."
)
# verify_local_commit co-author and message_coauthors (ADR-016; the study's
# section 4 table).
CAUSE_HOST_COAUTHOR = (
    "The usual cause is the host's standing instruction to end every commit "
    "with a Co-Authored-By trailer naming itself; the repository rule wins: "
    "end the message with the two exact provenance trailers and nothing else, "
    "and recreate the commit."
)
# verify_local_commit byline (ADR-016; the study's section 4 table).
CAUSE_HOST_BYLINE = (
    "The usual cause is the host's default attribution line (Generated with "
    "or by Claude Code, Codex or another host) or its session link in the "
    "message; remove it and recreate the commit."
)
# inspect_pull_request author (ADR-016; the study's section 4 table).
CAUSE_HOST_PR_AUTHOR = (
    "The pull request was opened under the host app's GitHub identity, such "
    "as claude[bot]; open it from the human contributor's account, or from "
    "the explicitly authorised publisher's account for Shoggoth work."
)
# inspect_pull_request byline (ADR-016; the study's section 4 table).
CAUSE_HOST_PR_BYLINE = (
    "The usual cause is the host appending its attribution line or claude.ai "
    "session link to the description after gh pr create returned; edit the "
    "body without it (gh pr edit <url> --body-file <file>), read it back over "
    "REST, and rerun this receipt."
)
# checked_login (ADR-016; the study's section 4 table).
CAUSE_HOST_ACCOUNT = (
    "The GitHub response links this identity to a runtime host account; use "
    "the human contributor's account for their work, or the explicitly "
    "authorised publisher's account for Shoggoth work."
)


def tool_text(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        die(f"{label} returned non-UTF-8 output")


def is_host_identity(name: str, email: str) -> bool:
    """Recognise known runtime identities without reclassifying human authors."""
    return (
        name.strip().casefold() in HOST_IDENTITY_NAMES
        or email.strip().casefold() in HOST_IDENTITY_EMAILS
    )


def identity_digest(email: str) -> str:
    """SHA-256 of one normalised author address.

    The receipt has to say whether the identity on the base is the identity
    that was pushed, and it must not carry an address to do it. A digest
    answers exactly that question and nothing else, and a reviewer holding the
    public repository can recompute it.
    """
    return hashlib.sha256(email.strip().casefold().encode("utf-8")).hexdigest()


def checked_login(value: object, label: str) -> str | None:
    """The GitHub account a commit is linked to, or None when it is linked to none.

    A literal `null` is the ordinary outcome for a contributor whose commit
    address is not on their account, so it is recorded as itself. Coercing it
    to a placeholder would turn "GitHub could not match this" into a name.

    An account object without a usable login is not that outcome. It is a
    payload nobody predicted, and reading it as "unlinked" would let a shape
    the reader does not understand become a claim about a person.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        die(f"{label} account is not an object")
    login = value.get("login")
    if not isinstance(login, str):
        die(f"{label} account login is not a string")
    if login.casefold() in HOST_PR_LOGINS:
        die(f"{label} links the commit to a runtime host account. {CAUSE_HOST_ACCOUNT}")
    if not GITHUB_LOGIN_RE.fullmatch(login):
        die(f"{label} account login is malformed")
    return login


def checked_identity(value: object, label: str) -> tuple[str, str]:
    """One author name and address out of a GitHub commit payload."""
    if not isinstance(value, dict):
        die(f"{label} identity is not an object")
    name = value.get("name")
    email = value.get("email")
    if (
        not isinstance(name, str)
        or not name.strip()
        or len(name) > ATTRIBUTION_NAME_MAX
    ):
        die(f"{label} identity name is malformed")
    if (
        not isinstance(email, str)
        or not email.strip()
        or len(email) > ATTRIBUTION_EMAIL_MAX
        or any(character.isspace() for character in email)
    ):
        die(f"{label} identity address is malformed")
    return name, email


def message_coauthors(message: object, label: str) -> list[dict]:
    """Every exact co-author trailer on one commit message.

    Parsed with the same expression the local range gate uses, so the two
    cannot disagree about what a trailer is. A host identity in a trailer
    refuses here as well as locally: the two views are read from different
    places and either one seeing a host is enough.
    """
    if not isinstance(message, str):
        die(f"{label} commit message is missing")
    found: list[dict] = []
    for line in message.splitlines():
        match = COAUTHOR_RE.fullmatch(line)
        if match is None:
            continue
        name, email = match.group("name"), match.group("email")
        if is_host_identity(name, email):
            die(f"{label} names a runtime host as co-author. {CAUSE_HOST_COAUTHOR}")
        if len(name) > ATTRIBUTION_NAME_MAX or len(email) > ATTRIBUTION_EMAIL_MAX:
            die(f"{label} co-author identity is malformed")
        found.append({"name": name, "email_sha256": identity_digest(email)})
        if len(found) > ATTRIBUTION_COAUTHOR_MAX:
            die(
                f"{label} carries more than {ATTRIBUTION_COAUTHOR_MAX} "
                "co-author trailers"
            )
    return found


def _exact_commit_git(
    base_dir: str,
    argv: list[str],
    refusal: str,
    *,
    native_relation: bool = False,
) -> bytes:
    """Read one native commit object, optionally inside the relation sandbox."""
    if native_relation:
        return _native_relation_git(base_dir, argv, refusal)
    return bounded_git(base_dir, ["--no-replace-objects", *argv], refusal)


def commit_author(
    base_dir: str,
    commit_sha: str,
    label: str,
    *,
    native_relation: bool = False,
) -> tuple[str, str]:
    data = _exact_commit_git(
        base_dir,
        ["show", "-s", "--no-show-signature", "--format=%an%x00%ae", commit_sha],
        f"{label} commit {commit_sha} author cannot be read",
        native_relation=native_relation,
    )
    fields = tool_text(data, f"{label} commit author").rstrip("\n").split("\0")
    if len(fields) != 2 or not all(field.strip() for field in fields):
        die(f"{label} commit {commit_sha} author identity is malformed")
    return fields[0], fields[1]


def commit_committer(
    base_dir: str,
    commit_sha: str,
    label: str,
    *,
    native_relation: bool = False,
) -> tuple[str, str]:
    """Read the actor who created the exact commit, separately from its author."""
    data = _exact_commit_git(
        base_dir,
        ["show", "-s", "--no-show-signature", "--format=%cn%x00%ce", commit_sha],
        f"{label} commit {commit_sha} committer cannot be read",
        native_relation=native_relation,
    )
    fields = tool_text(data, f"{label} commit committer").rstrip("\n").split("\0")
    if len(fields) != 2 or not all(field.strip() for field in fields):
        die(f"{label} commit {commit_sha} committer identity is malformed")
    return fields[0], fields[1]


def resolved_commit(base_dir: str, ref: str, label: str) -> str:
    data = bounded_git(
        base_dir,
        ["rev-parse", "--verify", f"{ref}^{{commit}}"],
        f"{label} does not resolve to a commit",
    )
    lines = [line.strip() for line in tool_text(data, label).splitlines() if line.strip()]
    if len(lines) != 1 or not COMMIT_RE.fullmatch(lines[0]):
        die(f"{label} did not resolve to one full commit SHA")
    return lines[0]


def remote_branch_tip(
    base_dir: str,
    branch: str,
    label: str = "remote run branch tip",
    *,
    native_relation: bool = False,
) -> str:
    check_branch_name(branch)
    expected_ref = f"refs/heads/{branch}"
    reader = _native_relation_git if native_relation else bounded_git
    data = reader(
        base_dir,
        ["ls-remote", "--refs", "origin", expected_ref],
        f"{label} could not be read",
    )
    lines = [line for line in tool_text(data, label).splitlines() if line]
    if not lines:
        # A deleted branch and a malformed remote answer are different faults,
        # and the recovery only exists for the first. Integrate reads this
        # while the run branch still has to be there, so say which one it is.
        die(
            f"{label} names no ref: origin has no {expected_ref}. A deleted "
            "branch reads this way; restore it at its recorded commit and retry"
        )
    if len(lines) > 1:
        die(f"{label} must contain exactly one ref")
    fields = lines[0].split("\t")
    if (
        len(fields) != 2
        or not COMMIT_RE.fullmatch(fields[0])
        or fields[1] != expected_ref
    ):
        die(f"{label} is malformed")
    return fields[0]


def commit_parents(base_dir: str, commit_sha: str, label: str) -> list[str]:
    commit_sha = require_full_sha(commit_sha, label)
    data = bounded_git(
        base_dir,
        ["show", "-s", "--no-show-signature", "--format=%P", commit_sha],
        f"{label} parents cannot be read",
    )
    parents = tool_text(data, f"{label} parents").strip().split()
    if any(not COMMIT_RE.fullmatch(parent) for parent in parents):
        die(f"{label} returned a malformed parent SHA")
    return parents


def exact_commit_range(base_dir: str, base_ref: str, head_ref: str, label: str) -> list[str]:
    base = resolved_commit(base_dir, base_ref, f"{label} base")
    head = resolved_commit(base_dir, head_ref, f"{label} head")
    bounded_git(
        base_dir,
        ["merge-base", "--is-ancestor", base, head],
        f"{label} head is not descended from its declared base",
    )
    data = bounded_git(
        base_dir,
        ["rev-list", "--reverse", f"--max-count={GIT_PATHS_MAX + 1}", f"{base}..{head}"],
        f"{label} commit range cannot be enumerated",
    )
    commits = [line.strip() for line in tool_text(data, label).splitlines() if line.strip()]
    if len(commits) > GIT_PATHS_MAX:
        die(f"{label} commit range exceeds {GIT_PATHS_MAX} commits")
    if any(not COMMIT_RE.fullmatch(commit) for commit in commits):
        die(f"{label} commit range returned a malformed SHA")
    if not commits or commits[-1] != head:
        die(f"{label} commit range does not end at the declared head")
    if base in commits:
        die(f"{label} commit range includes its base")
    return commits


def commit_is_ancestor(
    base_dir: str, candidate: str, descendant: str, label: str
) -> bool:
    """Whether one exact commit is still reachable from another.

    `merge-base --is-ancestor` answers 0 for yes and 1 for no. Anything else
    means the question was not answered at all: a bad object, an unreadable
    repository, a killed process. Reading an unexpected status as "no" would
    turn a broken call into a finding about a person, so only the two
    documented statuses count as an answer.
    """
    candidate = require_full_sha(candidate, f"{label} commit")
    descendant = require_full_sha(descendant, f"{label} descendant")
    status = bounded_tool_status(
        base_dir, "git", ["merge-base", "--is-ancestor", candidate, descendant]
    )
    if status not in (0, 1):
        die(f"{label} ancestry for {candidate} could not be determined")
    return status == 0


def signing_key(base_dir: str, commit_sha: str) -> str:
    """The long key id a commit was signed with, or the empty string.

    Used only to explain a failed verification. A missing or unreadable value
    is reported as unknown rather than treated as an answer.
    """
    try:
        data = bounded_git(
            base_dir,
            ["--no-replace-objects", "log", "-n1", "--pretty=%GK", commit_sha],
            f"signing key for {commit_sha} could not be read",
        )
    except SystemExit:
        return ""
    return tool_text(data, "signing key").strip()


def verify_local_commit(
    base_dir: str,
    commit_sha: str,
    label: str,
    *,
    native_relation: bool = False,
) -> str:
    """Verify one exact locally created commit and its required trailers."""
    commit_sha = require_full_sha(commit_sha, label)
    verification_argv = [
        item
        for setting in SIGNATURE_VERIFIER_CONFIG
        for item in ("-c", setting)
    ]
    verification_argv.extend(["verify-commit", commit_sha])
    if native_relation:
        _native_relation_git(
            base_dir,
            verification_argv,
            f"{label} commit {commit_sha} has no valid native local signature",
        )
    elif bounded_tool_status(
        base_dir,
        "git",
        ["--no-replace-objects", *verification_argv],
    ) != 0:
        key = signing_key(base_dir, commit_sha).upper()
        if key in GITHUB_SIGNING_KEYS:
            die(
                f"{label} commit {commit_sha} is signed by GitHub "
                f"(key {key}), not locally. GitHub rewrote this commit: its merge "
                "button, its Contents API and the rebase its native stacked "
                "pull-request flow performs all re-sign with that key, and the "
                "author and provenance trailers survive while the local signature "
                "does not. The range being receipted is therefore not the range "
                "that was pushed. Land the run from a branch holding the original "
                "unrebased commits. Do not import GitHub's public key to make this "
                "check pass; that removes the guarantee the check exists for."
            )
        if key:
            die(
                f"{label} commit {commit_sha} has no valid local signature "
                f"(signed with key {key}, which this keyring cannot validate)"
            )
        die(f"{label} commit {commit_sha} has no valid local signature")
    author_name, author_email = commit_author(
        base_dir,
        commit_sha,
        label,
        native_relation=native_relation,
    )
    if is_host_identity(author_name, author_email):
        die(
            f"{label} commit {commit_sha} uses a runtime host as author; "
            f"use Shoggoth or preserve the human contributor. {CAUSE_HOST_AUTHOR}"
        )
    committer_name, committer_email = commit_committer(
        base_dir,
        commit_sha,
        label,
        native_relation=native_relation,
    )
    if is_host_identity(committer_name, committer_email):
        die(
            f"{label} commit {commit_sha} uses a runtime host as committer. "
            f"{CAUSE_HOST_COMMITTER}"
        )
    body = tool_text(
        _exact_commit_git(
            base_dir,
            ["show", "-s", "--no-show-signature", "--format=%B", commit_sha],
            f"{label} commit {commit_sha} message cannot be read",
            native_relation=native_relation,
        ),
        f"{label} commit message",
    )
    lines = body.splitlines()
    for line in lines:
        match = COAUTHOR_RE.fullmatch(line)
        if match and is_host_identity(match.group("name"), match.group("email")):
            die(
                f"{label} commit {commit_sha} uses a runtime host as co-author. "
                f"{CAUSE_HOST_COAUTHOR}"
            )
    if HOST_BYLINE_RE.search(body):
        die(
            f"{label} commit {commit_sha} carries a runtime-host byline. "
            f"{CAUSE_HOST_BYLINE}"
        )
    coauthors = lines.count(COAUTHOR_TRAILER)
    origins = lines.count(ORIGIN_TRAILER)
    if coauthors != 1:
        die(
            f"{label} commit {commit_sha} has {coauthors} exact Shoggoth "
            "co-author trailers; expected 1"
        )
    if origins != 1:
        die(
            f"{label} commit {commit_sha} has {origins} exact Wildcat-Origin "
            "trailers; expected 1"
        )
    return commit_sha


def verify_local_range(base_dir: str, base_ref: str, head_ref: str, label: str) -> list[str]:
    """Verify every locally created commit in one exact base-to-head range."""
    commits = exact_commit_range(base_dir, base_ref, head_ref, label)
    for commit_sha in commits:
        verify_local_commit(base_dir, commit_sha, label)
    return commits


REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GITHUB_HTTPS_RE = re.compile(
    r"^https://github\.com/(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
GITHUB_SSH_RE = re.compile(
    r"^(?:git@github\.com:|ssh://git@github\.com/)(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
GITHUB_PR_RE = re.compile(
    r"^https://github\.com/(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/(?P<number>[1-9][0-9]*)/?$"
)
GITHUB_ISSUE_RE = re.compile(
    r"^https://github\.com/(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/(?P<number>[1-9][0-9]*)/?$"
)
GITHUB_CLOSING_KEYWORD_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s+",
    re.IGNORECASE,
)


def require_full_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
        die(f"{label} must be a full commit SHA")
    return value


def target_repository(base_dir: str) -> str:
    data = bounded_git(
        base_dir,
        ["remote", "get-url", "origin"],
        "target origin could not be resolved",
    )
    lines = [line.strip() for line in tool_text(data, "target origin").splitlines() if line.strip()]
    if len(lines) != 1:
        die("target origin does not name one GitHub repository")
    match = GITHUB_HTTPS_RE.fullmatch(lines[0]) or GITHUB_SSH_RE.fullmatch(lines[0])
    if match is None:
        die("target origin does not name one GitHub repository")
    repository = match.group("repo")
    if any(segment in (".", "..") for segment in repository.split("/")):
        # The owner and name go into REST paths below, so a relative segment
        # here would address some other endpoint entirely.
        die("target origin does not name one GitHub repository")
    return repository


def github_repository(base_dir: str) -> str:
    target = target_repository(base_dir)
    payload = github_rest(base_dir, f"repos/{target}", "repository identity")
    repository = payload.get("full_name")
    if not isinstance(repository, str) or not REPOSITORY_RE.fullmatch(repository):
        die("GitHub repository identity is missing full_name")
    if repository.casefold() != target.casefold():
        die("GitHub repository identity does not match target origin")
    return target


def github_issue_identity(issue_url: object) -> tuple[str, str] | None:
    """Return the repository and number for one canonical GitHub issue URL.

    ``task_issue`` predates the GitHub delivery gate and deliberately accepts
    other HTTP issue trackers. Those keep their explicit closure receipt. A
    GitHub issue gets the stronger pull-request closing-reference rule.
    """
    if not isinstance(issue_url, str):
        return None
    match = GITHUB_ISSUE_RE.fullmatch(issue_url)
    if match is None:
        return None
    return match.group("repo"), match.group("number")


def github_issue_closing_references(
    issue_url: object, pull_request_repository: str
) -> tuple[str, ...]:
    identity = github_issue_identity(issue_url)
    if identity is None:
        return ()
    issue_repository, number = identity
    references = [f"{issue_repository}#{number}"]
    if issue_repository.casefold() == pull_request_repository.casefold():
        references.insert(0, f"#{number}")
    return tuple(references)


def markdown_prose_lines(body: str) -> list[str]:
    """Return lines where GitHub can interpret a closing keyword.

    A keyword displayed as an example in a fence, inline code, an HTML comment,
    or a quotation is evidence about syntax, not an instruction to close.
    """
    without_comments = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    lines = []
    fence = None
    for line in without_comments.splitlines():
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in ("```", "~~~"):
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence is not None or stripped.startswith(">"):
            continue
        lines.append(re.sub(r"`+[^`\n]*`+", "", line))
    return lines


def pull_request_closing_reference(
    body: str, issue_url: object, repository: str
) -> dict | None:
    references = github_issue_closing_references(issue_url, repository)
    if not references:
        return None
    alternatives = "|".join(re.escape(reference) for reference in references)
    pattern = re.compile(
        GITHUB_CLOSING_KEYWORD_RE.pattern
        + rf"(?P<reference>{alternatives})(?![A-Za-z0-9_.#/-])",
        GITHUB_CLOSING_KEYWORD_RE.flags,
    )
    for line in markdown_prose_lines(body):
        match = pattern.search(line)
        if match is not None:
            return {
                "issue_url": issue_url,
                "reference": match.group("reference"),
                "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            }
    return None


def pull_request_target(pr_url: object, repository: str) -> tuple[str, str]:
    """One recorded pull request URL and its number, bound to one repository."""
    if not isinstance(pr_url, str):
        die("pull request URL is invalid")
    match = GITHUB_PR_RE.fullmatch(pr_url)
    if match is None or match.group("repo").casefold() != repository.casefold():
        die("pull request URL does not match target repository")
    return pr_url.rstrip("/"), match.group("number")


def pull_request_repository(pr_url: object, repository: str) -> str:
    return pull_request_target(pr_url, repository)[0]


def pull_request_state(payload: dict, merged: bool) -> str:
    """The recorded state of one pull request, in the receipt's own vocabulary.

    REST reports `open` or `closed` and carries the merge separately, while a
    receipt records `MERGED`, `OPEN` or `CLOSED`. Recording the three keeps
    every receipt this loop has written readable against the same three words.
    """
    if merged:
        return "MERGED"
    state = payload.get("state")
    if state not in ("open", "closed"):
        die("pull request topology is missing its state")
    return state.upper()


def inspect_pull_request(
    base_dir: str,
    pr_url: object,
    *,
    expected_head: str,
    expected_base: str,
    expected_head_sha: str | None,
    expected_merge_sha: str | None,
    expected_head_label: str = "verified pushed branch tip",
    expected_closing_issue: str | None = None,
) -> dict:
    head_sha = (
        require_full_sha(expected_head_sha, "pull request head")
        if expected_head_sha is not None
        else None
    )
    merge_sha = (
        require_full_sha(expected_merge_sha, "pull request merge")
        if expected_merge_sha is not None
        else None
    )
    repository = github_repository(base_dir)
    url, number = pull_request_target(pr_url, repository)
    payload = github_rest(
        base_dir,
        f"repos/{repository}/pulls/{number}",
        "pull request topology",
    )
    author = payload.get("user")
    author_login = author.get("login") if isinstance(author, dict) else None
    if not isinstance(author_login, str):
        die("pull request topology is missing its author")
    if author_login.casefold() in HOST_PR_LOGINS:
        die(
            "pull request uses a runtime host as author; hand off before "
            f"publication. {CAUSE_HOST_PR_AUTHOR}"
        )
    if "body" not in payload:
        die("pull request topology is missing its body")
    # REST spells an empty body as null rather than as an empty string. There
    # is no byline in either, so the absence of text is not a missing field.
    body = payload["body"] or ""
    if not isinstance(body, str):
        die("pull request topology is missing its body")
    if HOST_BYLINE_RE.search(body):
        die(f"pull request body carries a runtime-host byline. {CAUSE_HOST_PR_BYLINE}")
    closing_issue = None
    if expected_closing_issue is not None:
        references = github_issue_closing_references(
            expected_closing_issue, repository
        )
        if references:
            closing_issue = pull_request_closing_reference(
                body, expected_closing_issue, repository
            )
            if closing_issue is None:
                canonical = f"Closes {references[-1]}"
                die(
                    "pull request body has no recognised closing reference for "
                    f"the recorded task_issue; add `{canonical}` before merge"
                )
    returned_url = payload.get("html_url")
    if not isinstance(returned_url, str):
        die("pull request topology is missing its URL")
    pull_request_repository(returned_url, repository)
    if returned_url.rstrip("/") != url:
        die("pull request topology did not name the recorded pull request")
    head, base = payload.get("head"), payload.get("base")
    head_ref = head.get("ref") if isinstance(head, dict) else None
    base_ref = base.get("ref") if isinstance(base, dict) else None
    if head_ref != expected_head or base_ref != expected_base:
        die("pull request topology does not match the expected head and base")
    returned_head = head.get("sha")
    if not isinstance(returned_head, str) or not COMMIT_RE.fullmatch(returned_head):
        die("pull request topology has no full head SHA")
    if head_sha is not None and returned_head != head_sha:
        die(f"pull request head does not match the {expected_head_label}")
    merged = payload.get("merged")
    if not isinstance(merged, bool):
        die("pull request topology is missing its merged state")
    # REST also fills `merge_commit_sha` on an open pull request, with the test
    # merge GitHub computes for it. Only a merged pull request has a merge
    # commit, so an open one records none.
    merge_commit = payload.get("merge_commit_sha")
    returned_merge = merge_commit if merged and isinstance(merge_commit, str) else None
    if merge_sha is not None:
        if not merged or returned_merge != merge_sha:
            die("pull request is not the expected merged topology")
    elif merged:
        die("step pull request was already merged before integrate")
    record = {
        "url": url,
        "head": expected_head,
        "base": expected_base,
        "head_sha": returned_head,
        "state": pull_request_state(payload, merged),
        "merge_sha": returned_merge,
        "author_login": author_login,
    }
    if closing_issue is not None:
        record["closing_issue"] = closing_issue
    return record


def github_commit_payload(base_dir: str, repository: str, commit_sha: str) -> dict:
    """One bounded GitHub commit payload, checked for the exact SHA."""
    payload = github_rest(
        base_dir,
        f"repos/{repository}/commits/{commit_sha}",
        f"commit {commit_sha}",
    )
    if payload.get("sha") != commit_sha:
        die(f"GitHub verification response did not name exact SHA {commit_sha}")
    return payload


def require_github_verified(payload: dict, commit_sha: str) -> None:
    """GitHub's own verification result for one commit, or a refusal.

    Every refusal here names an answer GitHub gave. A read that never arrived
    refuses in `github_unreachable`'s shape instead, because an operator has to
    be able to tell a commit GitHub rejected from a commit GitHub was never
    asked about.
    """
    commit = payload.get("commit")
    verification = commit.get("verification") if isinstance(commit, dict) else None
    if not isinstance(verification, dict):
        die(f"GitHub answered for {commit_sha} without a verification result")
    if verification.get("verified") is not True:
        die(f"GitHub answered for {commit_sha}: not verified:true")
    if verification.get("reason") != "valid":
        die(f"GitHub answered for {commit_sha}: verification reason is not valid")


def commit_attribution(payload: dict, commit_sha: str) -> dict:
    """Who GitHub names as author and committer, without either address.

    The linked account is the identity, because one person may hold several
    addresses and one account. The digest corroborates it, and carries the
    comparison on its own where the account is null.
    """
    label = f"GitHub attribution for {commit_sha}"
    commit = payload.get("commit")
    if not isinstance(commit, dict):
        die(f"{label} is missing its commit object")
    name, email = checked_identity(commit.get("author"), label)
    if is_host_identity(name, email):
        die(f"{label} names a runtime host as author. {CAUSE_HOST_AUTHOR}")
    committer_label = f"{label} committer"
    committer_name, committer_email = checked_identity(
        commit.get("committer"), committer_label
    )
    if is_host_identity(committer_name, committer_email):
        die(
            f"{committer_label} names a runtime host. {CAUSE_HOST_COMMITTER}"
        )
    return {
        "commit": commit_sha,
        "login": checked_login(payload.get("author"), label),
        "name": name,
        "email_sha256": identity_digest(email),
        "coauthors": message_coauthors(commit.get("message"), label),
        "committer": {
            "login": checked_login(payload.get("committer"), committer_label),
            "name": committer_name,
            "email_sha256": identity_digest(committer_email),
        },
    }


def identity_matches(recorded: object, candidate: object) -> bool:
    """Whether two recorded identities name the same contributor.

    The account wins when both sides have one, because one person may hold
    several addresses and one account. The digest decides otherwise, and it is
    the only comparison available for a co-author trailer or an unlinked
    commit.
    """
    if not isinstance(recorded, dict) or not isinstance(candidate, dict):
        return False
    left, right = recorded.get("login"), candidate.get("login")
    if isinstance(left, str) and isinstance(right, str):
        return left.casefold() == right.casefold()
    digest = recorded.get("email_sha256")
    return isinstance(digest, str) and digest == candidate.get("email_sha256")


def identity_label(identity: dict) -> str:
    """Name one identity in a refusal without printing an address."""
    login = identity.get("login")
    if isinstance(login, str):
        return login
    digest = identity.get("email_sha256")
    return f"digest {digest[:12]}" if isinstance(digest, str) else "an unnamed identity"


def recorded_run_attribution(state: dict) -> list[dict]:
    """Every primary author this run's receipts recorded, in step order.

    A step whose push evidence was repaired at merge time carries a fresher
    container on the merge record, because the recorded push attribution
    describes commits that are no longer the branch tip. The fresher one wins.
    A legacy receipt carries none, and contributes nothing rather than
    refusing. A nested committer is publication evidence, not an authorship
    identity, so it stays in the push receipt and does not enter this view.
    """
    identities = []
    merges = as_dict(as_dict(state.get("integrate")).get("merges"))
    for step in state["steps"]:
        push = as_dict(step["receipts"].get("push"))
        effective = as_dict(as_dict(merges.get(str(step["n"]))).get("effective_push"))
        source = as_dict(
            effective["attribution"]
            if "attribution" in effective
            else push.get("attribution")
        )
        commits = source.get("commits")
        if commits is None:
            continue
        if not isinstance(commits, list):
            die(f"step {step['n']} recorded a malformed attribution container")
        for record in commits:
            if not isinstance(record, dict) or not isinstance(
                record.get("commit"), str
            ):
                die(f"step {step['n']} recorded a malformed attribution entry")
            author = {key: value for key, value in record.items() if key != "committer"}
            identities.append({"step": step["n"], **author})
    return identities


def attribution_carriers(state: dict, identity: dict, merge_sha: str) -> list[str]:
    """The merges that could have carried one identity onto the base.

    A step squashed into the run branch leaves its commits unreachable while
    its identity survives on that step's own merge commit, which is itself an
    ancestor of the base merge. Looking only at the base merge would refuse an
    identity that did reach the base, so the step's recorded merge is tried
    first and the base merge second.
    """
    merges = as_dict(as_dict(state.get("integrate")).get("merges"))
    step_merge = as_dict(merges.get(str(identity.get("step")))).get("merge_commit")
    carriers = []
    for candidate in (step_merge, merge_sha):
        if (
            isinstance(candidate, str)
            and COMMIT_RE.fullmatch(candidate)
            and candidate not in carriers
        ):
            carriers.append(candidate)
    return carriers


def merged_attribution(base_dir: str, state: dict, merge_sha: str) -> dict:
    """Whether the base still carries every primary author the run recorded.

    Two mechanisms count. A merge commit leaves every recorded commit
    reachable from the base, which is the ordinary case and needs no further
    read. A squash or rebase merge does not, and then the merge commit itself
    has to carry the identity as its author or in a co-author trailer.

    The merge commit's own identity is read only once an ancestry check has
    failed. On the ordinary path no extra request happens, and an unexpected
    identity shape on a merge commit cannot refuse a run whose commits all
    reached the base intact.
    """
    identities = recorded_run_attribution(state)
    resolved = []
    unresolved = []
    for identity in identities:
        if commit_is_ancestor(
            base_dir, identity["commit"], merge_sha, "merged attribution"
        ):
            resolved.append({**identity, "mechanism": "ancestor", "carrier": None})
        else:
            unresolved.append(identity)
    read: dict[str, dict] = {}
    if unresolved:
        repository = github_repository(base_dir)
        for identity in unresolved:
            carried = None
            for candidate in attribution_carriers(state, identity, merge_sha):
                if candidate != merge_sha and not commit_is_ancestor(
                    base_dir, candidate, merge_sha, "merged attribution carrier"
                ):
                    continue
                if candidate not in read:
                    read[candidate] = commit_attribution(
                        github_commit_payload(base_dir, repository, candidate),
                        candidate,
                    )
                record = read[candidate]
                if identity_matches(identity, record):
                    carried = (candidate, "merge-author")
                    break
                if any(
                    identity_matches(identity, coauthor)
                    for coauthor in record["coauthors"]
                ):
                    carried = (candidate, "merge-coauthor")
                    break
            if carried is None:
                die(
                    f"step {identity['step']} published commit "
                    f"{identity['commit']} under {identity_label(identity)}, "
                    f"and no merge this run recorded carries that commit or "
                    "that identity; the merge discarded the authorship this "
                    "run recorded"
                )
            resolved.append(
                {**identity, "mechanism": carried[1], "carrier": carried[0]}
            )
    return {
        "identities": resolved,
        "carriers": {sha: record["login"] for sha, record in read.items()},
        "mechanisms": sorted({entry["mechanism"] for entry in resolved}),
    }


def verified_github_attribution(
    base_dir: str, commits: list[str]
) -> tuple[list[str], list[dict]]:
    """Verify each exact SHA and record who GitHub says wrote it.

    One request per SHA serves both. Splitting them would double the reads and
    let the verification and the attribution describe different responses.
    """
    commits = [require_full_sha(commit, "GitHub commit") for commit in commits]
    repository = github_repository(base_dir)
    verified = []
    attribution = []
    for commit_sha in commits:
        payload = github_commit_payload(base_dir, repository, commit_sha)
        require_github_verified(payload, commit_sha)
        attribution.append(commit_attribution(payload, commit_sha))
        verified.append(commit_sha)
    return verified, attribution


def verify_github_commits(base_dir: str, commits: list[str]) -> list[str]:
    """Require GitHub's valid verification result for each exact SHA.

    Deliberately not implemented over `verified_github_attribution`. This gate
    also covers merge commits and the run sync, and routing it through the
    attribution reader would make an unexpected identity shape on a merge
    commit refuse a receipt that has nothing to do with attribution. The two
    read the same payload for different reasons and fail for different ones.
    """
    commits = [require_full_sha(commit, "GitHub commit") for commit in commits]
    repository = github_repository(base_dir)
    verified = []
    for commit_sha in commits:
        payload = github_commit_payload(base_dir, repository, commit_sha)
        require_github_verified(payload, commit_sha)
        verified.append(commit_sha)
    return verified


def scribe_files(base_dir: str, pr_base: str, branch: str) -> list[str]:
    check_branch_name(pr_base)
    check_branch_name(branch)
    raw = bounded_git(base_dir, ["diff", "--name-only", "-z", f"{pr_base}..{branch}", "--"])
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        die("git diff path list is not UTF-8")
    paths = [path for path in decoded.split("\0") if path]
    unique = sorted(set(paths))
    if len(unique) > GIT_PATHS_MAX:
        die(f"git diff returned more than {GIT_PATHS_MAX} paths")
    for path in unique:
        if os.path.isabs(path) or path in (".", ".."):
            die(f"git diff returned an unsafe path: {path}")
        scoped_path(base_dir, path, "git diff path")
    return unique


def delegation_packet(base_dir: str, state: dict, directive: dict) -> dict:
    """Add the total packet envelope and build only the four delegated briefs."""
    packet = {
        **directive,
        "state_sha256": state_fingerprint(state),
        "agent": None,
        "brief": {},
    }
    action = directive.get("do")
    root = os.path.realpath(base_dir)
    if action == "study":
        packet["agent"] = "surveyor"
        packet["brief"] = {
            "topic": state["topic"],
            "target_dir": root,
            "base_ref": state["base"],
            "output_path": scoped_path(
                root, os.path.join(STATE_DIR_NAME, "study.md"), "study output"
            ),
        }
        return packet

    if action not in ("implement", "audit-round", "prose"):
        return packet

    if not run_branch_of(state):
        return packet

    runbook = receipted_source(root, state, "runbook")
    study = receipted_source(root, state, "study")
    if runbook is None or study is None:
        # A pre-generation state cannot establish the source claims needed by
        # the four new briefs, so it retains an explicit inline directive.
        return packet
    version_relations = receipted_version_relations(root, runbook, state=state)

    step = current_step(state)
    plan = branch_plan(state, step)
    if action == "implement":
        packet["agent"] = "mason"
        packet["brief"] = {
            "runbook_step": source_runbook_step(
                runbook,
                step,
                current_study_sha256=study["sha256"],
                version_relations=version_relations,
            ),
            "branch": plan["branch"],
            "branch_from": plan["branch_from"],
        }
        return packet

    root_plugin = plugin_root()
    if action == "audit-round":
        audit = as_dict(as_dict(state.get("config")).get("audit"))
        log = configured_audit_log(state)
        suffix = audit.get("stacked_suffix")
        if not isinstance(suffix, str) or not suffix:
            die("audit config has no stacked_suffix for the warden packet")
        stacked_branch = plan["branch"] + suffix
        bounded_git(
            root,
            ["check-ref-format", "--branch", stacked_branch],
            "stacked_branch is not a valid Git branch",
        )
        packet["agent"] = "warden"
        packet["brief"] = {
            "step_branch": plan["branch"],
            "stacked_branch": stacked_branch,
            "security_suite": as_dict(state.get("receipts")).get("security_suite"),
            "plugin_root": root_plugin,
            "audit_log_path": scoped_path(root, log, "audit log path"),
            "round": directive["round"],
            "audit_filter": directive["audit_filter"],
            "risk_register": source_risk_register(study),
            "runbook_step": source_runbook_step(
                runbook,
                step,
                current_study_sha256=study["sha256"],
                version_relations=version_relations,
            ),
        }
        return packet

    pr_base = plan["pr_base"]
    packet["agent"] = "scribe"
    packet["brief"] = {
        "files": scribe_files(root, pr_base, plan["branch"]),
        "pr_base": pr_base,
        "pr_draft_path": scoped_path(
            root,
            os.path.join(STATE_DIR_NAME, "steps", str(step["n"]), "pr.md"),
            "PR draft path",
        ),
        "plugin_root": root_plugin,
    }
    if version_relations is not None:
        packet["brief"]["version_relations"] = version_relations_packet(
            version_relations
        )
    return packet


# ------------------------------------------------ controller checkpoints

def _checkpoint_stat_identity(value: os.stat_result) -> tuple:
    """Fields that must stay fixed while one controller entry is copied."""
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _checkpoint_ref_names(state: dict) -> list[str]:
    """The bounded local ref set the controller already names."""
    names = []
    base = state.get("base")
    if not isinstance(base, str) or not base:
        die("checkpoint source has no usable base ref")
    if not COMMIT_RE.fullmatch(base) and not branch_name_ok(base):
        die("checkpoint source has an unsafe base ref")
    names.append(base)

    run_branch = run_branch_of(state)
    if run_branch is not None:
        if not isinstance(run_branch, str) or not branch_name_ok(run_branch):
            die("checkpoint source has an unsafe run ref")
        names.append(run_branch)

    for step in state["steps"]:
        branch = as_dict(step.get("receipts")).get("implement")
        branch = as_dict(branch).get("branch")
        if branch is None:
            continue
        if not isinstance(branch, str) or not branch_name_ok(branch):
            die("checkpoint source has an unsafe step ref")
        names.append(branch)

    unique = sorted(set(names))
    if len(unique) != len(names) or len(unique) > GIT_PATHS_MAX:
        die("checkpoint source ref set is duplicated or too large")
    return unique


def _checkpoint_refs(base_dir: str, state: dict) -> dict[str, str]:
    """Resolve each recorded ref through the existing bounded Git reader."""
    return {
        name: resolved_commit(base_dir, name, "checkpoint ref")
        for name in _checkpoint_ref_names(state)
    }


def _checkpoint_boundary(state: dict, ledger: list[dict]) -> tuple[str, dict]:
    """Name one of ADR-028's two accepted export boundaries."""
    if not ledger:
        die("checkpoint export requires a non-empty verified ledger")
    directive = _next_directive(state)
    event = ledger[-1].get("event")
    if event == "done:push":
        return "post-push", directive
    if event == "audit-round" and directive.get("do") == "audit-verdict":
        return "audit-verdict", directive
    die(
        "checkpoint export is allowed only immediately after done push or "
        "at an active audit-verdict"
    )


def _checkpoint_safe_relative(parts: tuple[str, ...]) -> str:
    """Return one portable controller-relative path without echoing failures."""
    for part in parts:
        try:
            encoded = part.encode("utf-8")
        except UnicodeEncodeError:
            die("checkpoint source contains an unsafe path")
        if (
            not encoded
            or part in (".", "..")
            or "/" in part
            or "\\" in part
            or any(ord(character) < 32 or ord(character) == 127 for character in part)
        ):
            die("checkpoint source contains an unsafe path")
    relative = "/".join(parts)
    if len(relative.encode("utf-8")) > CHECKPOINT_PATH_BYTES_MAX:
        die("checkpoint source path exceeds the byte ceiling")
    return relative


def _checkpoint_write_all(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("short checkpoint write")
        view = view[written:]


def _checkpoint_regular(
    source_dir: int,
    name: str,
    initial: os.stat_result,
    destination: str | None,
) -> tuple[int, str]:
    """Hash and optionally copy one no-follow, single-link stable file."""
    if not stat.S_ISREG(initial.st_mode) or initial.st_nlink != 1:
        die("checkpoint source contains a special or linked entry")
    if initial.st_size > CHECKPOINT_FILE_BYTES_MAX:
        die("checkpoint source file exceeds the byte ceiling")

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        source = os.open(name, flags, dir_fd=source_dir)
    except OSError:
        die("checkpoint source changed during capture")
    output = None
    digest = hashlib.sha256()
    copied = 0
    try:
        before = os.fstat(source)
        if (
            _checkpoint_stat_identity(before) != _checkpoint_stat_identity(initial)
            or not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
        ):
            die("checkpoint source changed during capture")
        if destination is not None:
            output = os.open(
                destination,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        while True:
            chunk = os.read(source, CHECKPOINT_IO_CHUNK)
            if not chunk:
                break
            copied += len(chunk)
            if copied > CHECKPOINT_FILE_BYTES_MAX or copied > before.st_size:
                die("checkpoint source changed during capture")
            digest.update(chunk)
            if output is not None:
                _checkpoint_write_all(output, chunk)
        after = os.fstat(source)
        if (
            copied != before.st_size
            or _checkpoint_stat_identity(after) != _checkpoint_stat_identity(before)
        ):
            die("checkpoint source changed during capture")
        try:
            fresh = os.stat(name, dir_fd=source_dir, follow_symlinks=False)
        except OSError:
            die("checkpoint source changed during capture")
        if _checkpoint_stat_identity(fresh) != _checkpoint_stat_identity(before):
            die("checkpoint source changed during capture")
        if output is not None:
            os.fsync(output)
    except OSError:
        die("checkpoint source could not be copied")
    finally:
        if output is not None:
            os.close(output)
        os.close(source)
    return copied, digest.hexdigest()


def _checkpoint_snapshot(
    source_root: str,
    destination_root: str | None,
    *,
    exclude_live_lock: bool = True,
) -> list[dict]:
    """Read one bounded recursive snapshot, optionally into a private stage."""
    root_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        root_descriptor = os.open(source_root, root_flags)
    except OSError:
        die("checkpoint source directory is not a safe directory")

    inventory = []
    totals = {"files": 0, "directories": 1, "bytes": 0}

    def walk(source_dir: int, destination_dir: str | None, parts: tuple[str, ...]):
        try:
            before_directory = os.fstat(source_dir)
            if not stat.S_ISDIR(before_directory.st_mode):
                die("checkpoint source contains a non-directory container")
            with os.scandir(source_dir) as iterator:
                entries = []
                for entry in iterator:
                    relative_parts = (*parts, entry.name)
                    relative = _checkpoint_safe_relative(relative_parts)
                    try:
                        initial = os.stat(
                            entry.name, dir_fd=source_dir, follow_symlinks=False
                        )
                    except OSError:
                        die("checkpoint source changed during capture")

                    if not parts and entry.name == "lock":
                        if not exclude_live_lock:
                            die("checkpoint capsule contains an excluded run lock")
                        if not stat.S_ISREG(initial.st_mode) or initial.st_nlink != 1:
                            die("checkpoint lock is not a safe regular file")
                        continue

                    if stat.S_ISDIR(initial.st_mode):
                        totals["directories"] += 1
                        if totals["directories"] > CHECKPOINT_DIRECTORIES_MAX:
                            die("checkpoint source has too many directories")
                    elif stat.S_ISREG(initial.st_mode):
                        totals["files"] += 1
                        if totals["files"] > CHECKPOINT_FILES_MAX:
                            die("checkpoint source has too many files")
                        if initial.st_size > CHECKPOINT_FILE_BYTES_MAX:
                            die("checkpoint source file exceeds the byte ceiling")
                        totals["bytes"] += initial.st_size
                        if totals["bytes"] > CHECKPOINT_TOTAL_BYTES_MAX:
                            die("checkpoint source exceeds the total byte ceiling")
                    else:
                        die("checkpoint source contains a special or linked entry")

                    entries.append((entry, initial, relative_parts, relative))
                entries.sort(key=lambda item: item[0].name)
        except OSError:
            die("checkpoint source directory changed during capture")

        for entry, initial, relative_parts, relative in entries:
            if stat.S_ISDIR(initial.st_mode):
                child_destination = None
                if destination_dir is not None:
                    child_destination = os.path.join(destination_dir, entry.name)
                    try:
                        os.mkdir(child_destination, 0o700)
                    except OSError:
                        die("checkpoint stage could not create a private directory")
                try:
                    child = os.open(entry.name, root_flags, dir_fd=source_dir)
                except OSError:
                    die("checkpoint source directory changed during capture")
                try:
                    opened = os.fstat(child)
                    if _checkpoint_stat_identity(opened) != _checkpoint_stat_identity(initial):
                        die("checkpoint source directory changed during capture")
                    files_before = len(inventory)
                    walk(child, child_destination, relative_parts)
                    if child_destination is not None and len(inventory) == files_before:
                        try:
                            os.rmdir(child_destination)
                        except OSError:
                            die("checkpoint private stage changed during capture")
                finally:
                    os.close(child)
                continue

            destination = (
                os.path.join(destination_dir, entry.name)
                if destination_dir is not None
                else None
            )
            byte_count, digest = _checkpoint_regular(
                source_dir, entry.name, initial, destination
            )
            inventory.append(
                {
                    "path": f"{CHECKPOINT_CONTROLLER_DIR}/{relative}",
                    "bytes": byte_count,
                    "sha256": digest,
                }
            )

        after_directory = os.fstat(source_dir)
        if _checkpoint_stat_identity(after_directory) != _checkpoint_stat_identity(
            before_directory
        ):
            die("checkpoint source directory changed during capture")

    try:
        walk(root_descriptor, destination_root, ())
    finally:
        os.close(root_descriptor)
    return sorted(inventory, key=lambda item: item["path"])


def _checkpoint_read_staged(path: str, ceiling: int) -> bytes:
    """Read one private staged file under its declared byte ceiling."""
    try:
        before = os.lstat(path)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > ceiling
        ):
            die("checkpoint stage contains an unsafe file")
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            data = bytearray()
            while True:
                chunk = os.read(descriptor, min(CHECKPOINT_IO_CHUNK, ceiling + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > ceiling:
                    die("checkpoint stage file exceeds the byte ceiling")
            after = os.fstat(descriptor)
            named = os.lstat(path)
        finally:
            os.close(descriptor)
    except OSError:
        die("checkpoint stage could not be verified")
    if (
        len(data) != before.st_size
        or _checkpoint_stat_identity(after) != _checkpoint_stat_identity(before)
        or _checkpoint_stat_identity(named) != _checkpoint_stat_identity(before)
    ):
        die("checkpoint stage changed during verification")
    return bytes(data)


def _checkpoint_json_depth_within_limit(data: bytes) -> bool:
    """Bound JSON container nesting without interpreting string punctuation."""
    depth = 0
    in_string = False
    escaped = False
    for byte in data:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:  # backslash
                escaped = True
            elif byte == 0x22:  # double quote
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):  # [ {
            depth += 1
            if depth > CHECKPOINT_JSON_DEPTH_MAX:
                return False
        elif byte in (0x5D, 0x7D) and depth:
            depth -= 1
    return True


def _checkpoint_json(data: bytes, label: str):
    if not _checkpoint_json_depth_within_limit(data):
        die(f"checkpoint {label} exceeds the JSON nesting ceiling")
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("non-finite number")
            ),
        )
    except (MemoryError, RecursionError, UnicodeDecodeError, ValueError):
        die(f"checkpoint {label} is not strict UTF-8 JSON")


def _checkpoint_ledger(data: bytes, state: dict) -> tuple[int, str]:
    """Verify the captured ledger prefix without accepting duplicate keys."""
    previous = "genesis"
    count = 0
    last_state = None
    for raw_line in io.BytesIO(data):
        if not raw_line.strip():
            continue
        entry = _checkpoint_json(raw_line, "ledger")
        if not isinstance(entry, dict):
            die("checkpoint ledger entry is not an object")
        try:
            body = {
                "ts": entry["ts"],
                "event": entry["event"],
                "data": entry["data"],
                "prev": entry["prev"],
                "state": entry["state"],
            }
            expected = hashlib.sha256(canonical(body).encode()).hexdigest()
            valid = entry["prev"] == previous and entry["hash"] == expected
        except (KeyError, TypeError):
            valid = False
        if not valid:
            die("checkpoint ledger chain is invalid")
        previous = entry["hash"]
        last_state = entry["state"]
        count += 1
    if count == 0 or last_state != state_fingerprint(state):
        die("checkpoint state does not match its ledger tail")
    return count, previous


def _checkpoint_directory_still_at_path(path: str, descriptor: int) -> bool:
    """Return whether one no-follow path still names the opened directory."""
    current = None
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        if os.path.realpath(path) != path:
            return False
        current = os.open(path, flags)
        opened = os.fstat(current)
        expected = os.fstat(descriptor)
        return (opened.st_dev, opened.st_ino) == (expected.st_dev, expected.st_ino)
    except OSError:
        return False
    finally:
        if current is not None:
            with contextlib.suppress(OSError):
                os.close(current)


def _checkpoint_directory_still_in_parent(
    parent_descriptor: int, name: str, descriptor: int
) -> bool:
    """Return whether one parent entry still names the opened directory."""
    try:
        named = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        opened = os.fstat(descriptor)
    except OSError:
        return False
    return (
        stat.S_ISDIR(named.st_mode)
        and stat.S_ISDIR(opened.st_mode)
        and (named.st_dev, named.st_ino) == (opened.st_dev, opened.st_ino)
    )


def _checkpoint_destination(base_dir: str, supplied: str) -> tuple[str, str, int]:
    """Resolve and pin one new sibling-publish target and its parent."""
    if not isinstance(supplied, str) or not supplied:
        die("checkpoint export requires --out <new-directory>")
    try:
        encoded = supplied.encode("utf-8")
    except UnicodeEncodeError:
        die("checkpoint output path is unsafe")
    if (
        not encoded
        or len(encoded) > 4096
        or any(ord(character) < 32 or ord(character) == 127 for character in supplied)
    ):
        die("checkpoint output path is unsafe")
    destination = os.path.abspath(
        supplied if os.path.isabs(supplied) else os.path.join(base_dir, supplied)
    )
    parent = os.path.dirname(destination)
    if not os.path.basename(destination) or os.path.realpath(parent) != parent:
        die("checkpoint output parent must be one existing non-symlink directory")
    source = os.path.realpath(state_root(base_dir))
    if contained_in(source, destination):
        die("checkpoint output destination cannot enter controller state")
    parent_descriptor = None
    try:
        parent_stat = os.lstat(parent)
        parent_descriptor = os.open(
            parent,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        opened = os.fstat(parent_descriptor)
        if (
            not stat.S_ISDIR(parent_stat.st_mode)
            or not stat.S_ISDIR(opened.st_mode)
            or (parent_stat.st_dev, parent_stat.st_ino)
            != (opened.st_dev, opened.st_ino)
            or not _checkpoint_directory_still_at_path(parent, parent_descriptor)
        ):
            raise OSError("checkpoint parent identity changed")
    except OSError:
        if parent_descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(parent_descriptor)
        die("checkpoint output parent must be one existing non-symlink directory")

    try:
        os.stat(
            os.path.basename(destination),
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        pass
    except OSError:
        os.close(parent_descriptor)
        die("checkpoint output destination could not be inspected")
    else:
        os.close(parent_descriptor)
        die("checkpoint output destination is occupied")
    return destination, parent, parent_descriptor


def _checkpoint_manifest(
    stage: str,
    state: dict,
    boundary: str,
    directive: dict,
    refs: dict[str, str],
    inventory: list[dict],
) -> tuple[dict, bytes, str]:
    controller_root = os.path.join(stage, CHECKPOINT_CONTROLLER_DIR)
    state_bytes = _checkpoint_read_staged(
        os.path.join(controller_root, STATE_FILE), CHECKPOINT_FILE_BYTES_MAX
    )
    ledger_bytes = _checkpoint_read_staged(
        os.path.join(controller_root, LEDGER_FILE), CHECKPOINT_FILE_BYTES_MAX
    )
    if not ledger_bytes.endswith(b"\n"):
        die("checkpoint ledger is not an appendable exact prefix")
    captured_state = _checkpoint_json(state_bytes, "state")
    captured_state = validate_state_shape(captured_state)
    if canonical(captured_state) != canonical(state):
        die("checkpoint captured another controller state")
    ledger_count, ledger_tail = _checkpoint_ledger(ledger_bytes, captured_state)
    version = ledger_version(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, "EVOLUTION.md")
    )
    if version is None:
        die("checkpoint controller version cannot be resolved")
    total_bytes = sum(item["bytes"] for item in inventory)
    manifest = {
        "schema": CHECKPOINT_SCHEMA,
        "controller": {
            "name": captured_state.get("controller"),
            "state_version": captured_state.get("version"),
            "version": version,
        },
        "boundary": {
            "kind": boundary,
            "next": directive,
            "refs": refs,
        },
        "source": {
            "state_sha256": hashlib.sha256(state_bytes).hexdigest(),
            "state_fingerprint": state_fingerprint(captured_state),
            "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "ledger_entries": ledger_count,
            "ledger_tail": ledger_tail,
        },
        "resources": {
            "files": len(inventory),
            "bytes": total_bytes,
            "limits": {
                "files": CHECKPOINT_FILES_MAX,
                "directories": CHECKPOINT_DIRECTORIES_MAX,
                "total_bytes": CHECKPOINT_TOTAL_BYTES_MAX,
                "file_bytes": CHECKPOINT_FILE_BYTES_MAX,
                "manifest_bytes": CHECKPOINT_MANIFEST_BYTES_MAX,
                "path_bytes": CHECKPOINT_PATH_BYTES_MAX,
            },
        },
        "files": inventory,
    }
    payload = canonical(manifest).encode("utf-8") + b"\n"
    if len(payload) > CHECKPOINT_MANIFEST_BYTES_MAX:
        die("checkpoint manifest exceeds the byte ceiling")
    return manifest, payload, hashlib.sha256(payload).hexdigest()


def _checkpoint_write_manifest(stage: str, payload: bytes) -> None:
    path = os.path.join(stage, CHECKPOINT_MANIFEST_FILE)
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            _checkpoint_write_all(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        die("checkpoint manifest could not be written")


def _checkpoint_fsync_directories(stage: str) -> None:
    for current, directories, _ in os.walk(stage, topdown=False, followlinks=False):
        directories.sort()
        try:
            descriptor = os.open(
                current,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError:
            die("checkpoint stage could not be made durable")


def _checkpoint_atomic_publish(stage: str, destination: str) -> None:
    """Atomically publish one complete directory without replacing a target."""
    try:
        libc = ctypes.CDLL(None, use_errno=True)
    except OSError:
        die("checkpoint platform has no atomic no-replace directory publish")
    source_bytes = os.fsencode(stage)
    destination_bytes = os.fsencode(destination)
    if hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        rename.restype = ctypes.c_int
        result = rename(-100, source_bytes, -100, destination_bytes, 1)
    elif hasattr(libc, "renamex_np"):
        rename = libc.renamex_np
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        rename.restype = ctypes.c_int
        result = rename(source_bytes, destination_bytes, 0x00000004)
    else:
        die("checkpoint platform has no atomic no-replace directory publish")
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in (errno.EEXIST, errno.ENOTEMPTY):
        die("checkpoint output destination became occupied")
    die("checkpoint stage could not be published atomically")


def cmd_checkpoint_export(args) -> None:
    """Export one deterministic controller capsule without changing the run."""
    base_dir = os.path.abspath(args.dir)
    verify_run(base_dir)
    state = load_state(base_dir)
    ledger = ledger_entries(base_dir)
    boundary, directive = _checkpoint_boundary(state, ledger)
    if os.path.lexists(state_path(base_dir) + ".tmp"):
        die("checkpoint export refuses a pending controller transaction")
    destination, parent, parent_descriptor = _checkpoint_destination(
        base_dir, args.out
    )
    working_descriptor = None
    try:
        refs = _checkpoint_refs(base_dir, state)
        state_before = _checkpoint_read_staged(
            state_path(base_dir), CHECKPOINT_FILE_BYTES_MAX
        )
        ledger_before = _checkpoint_read_staged(
            ledger_path(base_dir), CHECKPOINT_FILE_BYTES_MAX
        )

        try:
            working_descriptor = os.open(
                ".",
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0),
            )
            os.fchdir(parent_descriptor)
        except OSError:
            die("checkpoint output parent could not be pinned")
        if not _checkpoint_directory_still_at_path(parent, parent_descriptor):
            die("checkpoint output parent changed before staging")

        prefix = f".{os.path.basename(destination)}.stage-"
        try:
            stage = tempfile.mkdtemp(prefix=prefix, dir=".")
            os.chmod(stage, 0o700)
        except OSError:
            die("checkpoint private stage could not be created")
        stage_name = os.path.basename(stage)
        stage_descriptor = None
        published = False
        try:
            try:
                stage_descriptor = os.open(
                    stage_name,
                    os.O_RDONLY
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=parent_descriptor,
                )
            except OSError:
                die("checkpoint private stage changed before capture")
            if not _checkpoint_directory_still_in_parent(
                parent_descriptor, stage_name, stage_descriptor
            ):
                die("checkpoint private stage changed before capture")
            controller_stage = os.path.join(stage, CHECKPOINT_CONTROLLER_DIR)
            try:
                os.mkdir(controller_stage, 0o700)
            except OSError:
                die("checkpoint private stage changed before capture")
            inventory = _checkpoint_snapshot(state_root(base_dir), controller_stage)
            if not _checkpoint_directory_still_in_parent(
                parent_descriptor, stage_name, stage_descriptor
            ):
                die("checkpoint private stage changed during capture")
            if (
                _checkpoint_snapshot(
                    controller_stage, None, exclude_live_lock=False
                )
                != inventory
            ):
                die("checkpoint private stage changed during capture")
            manifest, manifest_bytes, manifest_digest = _checkpoint_manifest(
                stage, state, boundary, directive, refs, inventory
            )
            if _checkpoint_snapshot(state_root(base_dir), None) != inventory:
                die("checkpoint source changed before publication")
            if (
                _checkpoint_read_staged(
                    state_path(base_dir), CHECKPOINT_FILE_BYTES_MAX
                )
                != state_before
                or _checkpoint_read_staged(
                    ledger_path(base_dir), CHECKPOINT_FILE_BYTES_MAX
                )
                != ledger_before
                or _checkpoint_refs(base_dir, state) != refs
            ):
                die("checkpoint source changed before publication")
            _checkpoint_write_manifest(stage, manifest_bytes)
            if _checkpoint_read_staged(
                os.path.join(stage, CHECKPOINT_MANIFEST_FILE),
                CHECKPOINT_MANIFEST_BYTES_MAX,
            ) != manifest_bytes:
                die("checkpoint manifest changed before publication")
            _checkpoint_fsync_directories(stage)
            if not _checkpoint_directory_still_in_parent(
                parent_descriptor, stage_name, stage_descriptor
            ):
                die("checkpoint private stage changed before publication")
            if not _checkpoint_directory_still_at_path(parent, parent_descriptor):
                die("checkpoint output parent changed before publication")
            destination_name = os.path.basename(destination)
            _checkpoint_atomic_publish(stage_name, destination_name)
            if not _checkpoint_directory_still_in_parent(
                parent_descriptor, destination_name, stage_descriptor
            ):
                die("checkpoint private stage changed during publication", 1)
            if not _checkpoint_directory_still_at_path(parent, parent_descriptor):
                try:
                    shutil.rmtree(destination_name, dir_fd=parent_descriptor)
                    os.fsync(parent_descriptor)
                except OSError:
                    die(
                        "checkpoint output parent changed and publication "
                        "could not be removed",
                        1,
                    )
                die("checkpoint output parent changed during publication")
            published = True
            try:
                os.fsync(parent_descriptor)
            except OSError:
                die("checkpoint publication could not be made durable", 1)
        finally:
            if (
                not published
                and stage_descriptor is not None
                and _checkpoint_directory_still_in_parent(
                    parent_descriptor, stage_name, stage_descriptor
                )
            ):
                with contextlib.suppress(OSError):
                    shutil.rmtree(stage_name, dir_fd=parent_descriptor)
            if stage_descriptor is not None:
                with contextlib.suppress(OSError):
                    os.close(stage_descriptor)
    finally:
        if working_descriptor is not None:
            with contextlib.suppress(OSError):
                os.fchdir(working_descriptor)
            with contextlib.suppress(OSError):
                os.close(working_descriptor)
        with contextlib.suppress(OSError):
            os.close(parent_descriptor)

    source = manifest["source"]
    print(
        json.dumps(
            {
                "schema": CHECKPOINT_RESULT_SCHEMA,
                "capsule": destination,
                "boundary": boundary,
                "next": directive,
                "refs": refs,
                "files": manifest["resources"]["files"],
                "bytes": manifest["resources"]["bytes"],
                "manifest_sha256": manifest_digest,
                "state_sha256": source["state_sha256"],
                "state_fingerprint": source["state_fingerprint"],
                "ledger_sha256": source["ledger_sha256"],
                "ledger_entries": source["ledger_entries"],
                "ledger_tail": source["ledger_tail"],
            },
            sort_keys=True,
        )
    )


def _checkpoint_closed_object(value, fields: set[str], label: str) -> dict:
    """Accept one object with exactly the manifest fields its schema names."""
    if not isinstance(value, dict) or set(value) != fields:
        die(f"checkpoint {label} has an unsupported shape")
    return value


def _checkpoint_restore_source_receipt(
    state: dict, name: str
) -> tuple[str, str] | None:
    """Return one portable source path and digest from imported state."""
    receipt = as_dict(as_dict(state.get("receipts")).get(name))
    expected = receipt.get("sha256")
    if expected is None:
        return None
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        die(f"checkpoint {name} receipt has an invalid sha256")
    artifact = receipt.get("artifact")
    if not isinstance(artifact, str) or not artifact:
        die(f"checkpoint {name} artefact path is not relocatable")
    if os.path.isabs(artifact):
        old_origin = configured_git_path(state, "origin")
        old_worktree = configured_git_path(state, "worktree")
        run_branch = run_branch_of(state)
        paths = (old_origin, old_worktree, artifact)
        for path in paths:
            try:
                encoded = path.encode("utf-8") if isinstance(path, str) else b""
            except UnicodeEncodeError:
                encoded = b""
            if (
                not encoded
                or not os.path.isabs(path)
                or path.replace("\\", "/") != path
                or os.path.normpath(path) != path
                or any(
                    ord(character) < 32 or ord(character) == 127
                    for character in path
                )
            ):
                die(f"checkpoint {name} artefact path is not relocatable")
        if not isinstance(run_branch, str) or not branch_name_ok(run_branch):
            die(f"checkpoint {name} artefact path is not relocatable")
        expected_worktree = os.path.join(
            old_origin, *WORKTREE_HOME, run_branch.replace("/", "-")
        )
        if old_worktree != expected_worktree:
            die(f"checkpoint {name} artefact path is not relocatable")
        try:
            relative = os.path.relpath(artifact, old_worktree).replace(os.sep, "/")
        except (OSError, TypeError, ValueError):
            die(f"checkpoint {name} artefact path is not relocatable")
        artifact = _checkpoint_safe_relative(tuple(relative.split("/")))
        if os.path.join(old_worktree, *artifact.split("/")) != receipt["artifact"]:
            die(f"checkpoint {name} artefact path is not relocatable")
    if artifact.replace("\\", "/") != artifact:
        die(f"checkpoint {name} artefact path is unsafe")
    if _checkpoint_safe_relative(tuple(artifact.split("/"))) != artifact:
        die(f"checkpoint {name} artefact path is unsafe")
    return artifact, expected


def _checkpoint_restore_capsule(
    supplied: str, expected_digest: str
) -> tuple[str, dict, dict, bytes, bytes, list[dict]]:
    """Verify one hostile capsule completely before any restore path exists."""
    if not isinstance(expected_digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_digest
    ):
        die("checkpoint restore requires a lowercase SHA-256 manifest digest")
    if not isinstance(supplied, str) or not supplied:
        die("checkpoint restore requires --from <capsule-directory>")
    try:
        capsule = os.path.abspath(supplied)
        initial = os.lstat(capsule)
    except (OSError, TypeError, ValueError):
        die("checkpoint capsule is not a safe directory")
    if (
        os.path.realpath(capsule) != capsule
        or not stat.S_ISDIR(initial.st_mode)
        or stat.S_ISLNK(initial.st_mode)
    ):
        die("checkpoint capsule is not a safe directory")
    try:
        names = []
        with os.scandir(capsule) as iterator:
            for entry in iterator:
                entry_stat = entry.stat(follow_symlinks=False)
                expected_directory = entry.name == CHECKPOINT_CONTROLLER_DIR
                if (
                    entry.name not in (CHECKPOINT_MANIFEST_FILE, CHECKPOINT_CONTROLLER_DIR)
                    or (expected_directory and not stat.S_ISDIR(entry_stat.st_mode))
                    or (not expected_directory and not stat.S_ISREG(entry_stat.st_mode))
                    or (not expected_directory and entry_stat.st_nlink != 1)
                ):
                    die("checkpoint capsule has an unsupported top-level entry")
                names.append(entry.name)
    except OSError:
        die("checkpoint capsule changed during verification")
    if set(names) != {CHECKPOINT_CONTROLLER_DIR, CHECKPOINT_MANIFEST_FILE} or len(names) != 2:
        die("checkpoint capsule is incomplete or has extra entries")

    manifest_path = os.path.join(capsule, CHECKPOINT_MANIFEST_FILE)
    manifest_bytes = _checkpoint_read_staged(
        manifest_path, CHECKPOINT_MANIFEST_BYTES_MAX
    )
    if hashlib.sha256(manifest_bytes).hexdigest() != expected_digest:
        die("checkpoint manifest digest does not match --manifest-sha256")
    manifest = _checkpoint_json(manifest_bytes, "manifest")
    manifest = _checkpoint_closed_object(
        manifest,
        {"schema", "controller", "boundary", "source", "resources", "files"},
        "manifest",
    )
    if (
        manifest.get("schema") != CHECKPOINT_SCHEMA
        or canonical(manifest).encode("utf-8") + b"\n" != manifest_bytes
    ):
        die("checkpoint manifest is not canonical or has the wrong schema")

    controller = _checkpoint_closed_object(
        manifest["controller"], {"name", "state_version", "version"}, "controller"
    )
    boundary = _checkpoint_closed_object(
        manifest["boundary"], {"kind", "next", "refs"}, "boundary"
    )
    source = _checkpoint_closed_object(
        manifest["source"],
        {
            "state_sha256",
            "state_fingerprint",
            "ledger_sha256",
            "ledger_entries",
            "ledger_tail",
        },
        "source identity",
    )
    resources = _checkpoint_closed_object(
        manifest["resources"], {"files", "bytes", "limits"}, "resources"
    )
    limits = _checkpoint_closed_object(
        resources["limits"],
        {
            "files",
            "directories",
            "total_bytes",
            "file_bytes",
            "manifest_bytes",
            "path_bytes",
        },
        "resource limits",
    )
    if canonical(limits) != canonical(
        {
            "files": CHECKPOINT_FILES_MAX,
            "directories": CHECKPOINT_DIRECTORIES_MAX,
            "total_bytes": CHECKPOINT_TOTAL_BYTES_MAX,
            "file_bytes": CHECKPOINT_FILE_BYTES_MAX,
            "manifest_bytes": CHECKPOINT_MANIFEST_BYTES_MAX,
            "path_bytes": CHECKPOINT_PATH_BYTES_MAX,
        }
    ):
        die("checkpoint manifest resource limits do not match this controller")

    controller_root = os.path.join(capsule, CHECKPOINT_CONTROLLER_DIR)
    inventory = _checkpoint_snapshot(
        controller_root, None, exclude_live_lock=False
    )
    recorded = manifest["files"]
    if (
        not isinstance(recorded, list)
        or len(recorded) > CHECKPOINT_FILES_MAX
    ):
        die("checkpoint manifest file inventory is invalid")
    for item in recorded:
        _checkpoint_closed_object(item, {"path", "bytes", "sha256"}, "file record")
        if (
            not isinstance(item["path"], str)
            or not item["path"].startswith(CHECKPOINT_CONTROLLER_DIR + "/")
            or not isinstance(item["bytes"], int)
            or isinstance(item["bytes"], bool)
            or item["bytes"] < 0
            or not isinstance(item["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
        ):
            die("checkpoint manifest file inventory is invalid")
        relative = item["path"].removeprefix(CHECKPOINT_CONTROLLER_DIR + "/")
        if _checkpoint_safe_relative(tuple(relative.split("/"))) != relative:
            die("checkpoint manifest file inventory is invalid")
    if recorded != sorted(recorded, key=lambda item: item["path"]):
        die("checkpoint manifest file inventory is invalid")
    if recorded != inventory:
        die("checkpoint manifest inventory does not match controller bytes")
    total_bytes = sum(item["bytes"] for item in inventory)
    if (
        resources["files"] != len(inventory)
        or resources["bytes"] != total_bytes
        or not isinstance(resources["files"], int)
        or isinstance(resources["files"], bool)
        or not isinstance(resources["bytes"], int)
        or isinstance(resources["bytes"], bool)
    ):
        die("checkpoint manifest resource totals do not match controller bytes")

    state_bytes = _checkpoint_read_staged(
        os.path.join(controller_root, STATE_FILE), CHECKPOINT_FILE_BYTES_MAX
    )
    ledger_bytes = _checkpoint_read_staged(
        os.path.join(controller_root, LEDGER_FILE), CHECKPOINT_FILE_BYTES_MAX
    )
    if len(state_bytes) > SOURCE_BYTES_MAX:
        die("checkpoint state exceeds the bounded controller-source cap")
    state = validate_state_shape(_checkpoint_json(state_bytes, "state"))
    ledger_count, ledger_tail = _checkpoint_ledger(ledger_bytes, state)
    if not ledger_bytes.endswith(b"\n"):
        die("checkpoint ledger is not an appendable exact prefix")
    if canonical(source) != canonical(
        {
            "state_sha256": hashlib.sha256(state_bytes).hexdigest(),
            "state_fingerprint": state_fingerprint(state),
            "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "ledger_entries": ledger_count,
            "ledger_tail": ledger_tail,
        }
    ):
        die("checkpoint source identities do not match controller bytes")

    current_version = ledger_version(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, "EVOLUTION.md")
    )
    controller_identity = {
        "name": controller["name"],
        "state_version": controller["state_version"],
    }
    state_identity = {
        "name": state.get("controller"),
        "state_version": state.get("version"),
    }
    if (
        canonical(controller_identity) != canonical(state_identity)
        or not isinstance(controller["version"], str)
        or controller["version"] not in CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS
        or current_version not in CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS
    ):
        die("checkpoint controller identity does not match this controller")
    last_entry = None
    for line in io.BytesIO(ledger_bytes):
        if line.strip():
            last_entry = _checkpoint_json(line, "ledger")
    expected_kind, expected_next = _checkpoint_boundary(
        state, [] if last_entry is None else [last_entry]
    )
    if (
        boundary["kind"] != expected_kind
        or canonical(boundary["next"]) != canonical(expected_next)
        or not isinstance(boundary["refs"], dict)
        or sorted(boundary["refs"]) != _checkpoint_ref_names(state)
        or any(
            not isinstance(value, str) or not COMMIT_RE.fullmatch(value)
            for value in boundary["refs"].values()
        )
    ):
        die("checkpoint boundary does not match controller semantics")

    # Study and runbook bytes remain source-bound after relocation. Validate
    # every receipt path before the marker boundary, and bind controller-local
    # sources to the corresponding bytes inside the capsule.
    for name in ("study", "runbook"):
        source_receipt = _checkpoint_restore_source_receipt(state, name)
        if source_receipt is None:
            continue
        artifact, expected = source_receipt
        prefix = STATE_DIR_NAME + "/"
        if artifact.startswith(prefix):
            relative = artifact[len(prefix):]
            candidate = os.path.join(controller_root, *relative.split("/"))
            data = _checkpoint_read_staged(candidate, SOURCE_BYTES_MAX)
            if hashlib.sha256(data).hexdigest() != expected:
                die(f"checkpoint {name} artefact does not match its receipt")

    # The root and manifest identities are checked a second time so a moving
    # capsule never reaches the marker-first mutation boundary.
    if (
        _checkpoint_snapshot(controller_root, None, exclude_live_lock=False)
        != inventory
        or _checkpoint_read_staged(manifest_path, CHECKPOINT_MANIFEST_BYTES_MAX)
        != manifest_bytes
    ):
        die("checkpoint capsule changed during verification")
    return capsule, manifest, state, state_bytes, ledger_bytes, inventory


def _checkpoint_restore_origin(base_dir: str) -> str:
    """Admit one clean, top-level Git worktree as the new origin."""
    origin = os.path.abspath(base_dir)
    if os.path.realpath(origin) != origin or repository_root(origin) != origin:
        die("checkpoint restore requires a fresh top-level Git origin")
    if bounded_git(origin, ["status", "--porcelain"]).strip():
        die("checkpoint restore requires a clean fresh origin")
    return origin


def _checkpoint_restore_marker_paths(origin: str, state: dict, digest: str):
    run_branch = run_branch_of(state)
    if not isinstance(run_branch, str) or not branch_name_ok(run_branch):
        die("checkpoint state has no relocatable run branch")
    worktree = run_worktree_path(origin, run_branch)
    stage = os.path.join(worktree, f".{STATE_DIR_NAME}.restore-stage-{digest[:16]}")
    marker = os.path.join(state_root(origin), CHECKPOINT_RESTORE_MARKER_FILE)
    return worktree, stage, marker


def _checkpoint_restore_marker_record(
    state: dict, digest: str, worktree: str, stage: str
) -> dict:
    return {
        "schema": CHECKPOINT_RESTORE_MARKER_SCHEMA,
        "manifest_sha256": digest,
        "run_branch": run_branch_of(state),
        "worktree": worktree,
        "stage": stage,
    }


def _checkpoint_restore_marker(
    origin: str, state: dict, digest: str
) -> tuple[str, str, str, bool]:
    """Publish or verify the transaction marker before a restore-owned path."""
    worktree, stage, marker = _checkpoint_restore_marker_paths(origin, state, digest)
    root = state_root(origin)
    expected = _checkpoint_restore_marker_record(state, digest, worktree, stage)
    if os.path.lexists(root):
        if os.path.islink(root) or not os.path.isdir(root):
            die("checkpoint restore origin state path is occupied")
        allowed = {".gitignore", CHECKPOINT_RESTORE_MARKER_FILE, WORKTREE_FILE}
        try:
            names = set(os.listdir(root))
        except OSError:
            die("checkpoint restore marker cannot be inspected")
        if not names.issubset(allowed) or CHECKPOINT_RESTORE_MARKER_FILE not in names:
            die("checkpoint restore requires an empty fresh origin")
        raw = _checkpoint_read_staged(marker, CHECKPOINT_MANIFEST_BYTES_MAX)
        found = _checkpoint_json(raw, "restore marker")
        if found != expected or raw != canonical(found).encode("utf-8") + b"\n":
            die("checkpoint restore marker belongs to another transaction")
        return worktree, stage, marker, True

    origin_descriptor = None
    root_descriptor = None
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    create_flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        origin_descriptor = os.open(origin, directory_flags)
        if not _checkpoint_directory_still_at_path(origin, origin_descriptor):
            raise OSError("checkpoint restore origin changed")
        os.mkdir(STATE_DIR_NAME, 0o700, dir_fd=origin_descriptor)
        root_descriptor = os.open(
            STATE_DIR_NAME, directory_flags, dir_fd=origin_descriptor
        )
        if not _checkpoint_directory_still_in_parent(
            origin_descriptor, STATE_DIR_NAME, root_descriptor
        ):
            raise OSError("checkpoint restore state path changed")

        gitignore_descriptor = os.open(
            ".gitignore", create_flags, 0o600, dir_fd=root_descriptor
        )
        try:
            _checkpoint_write_all(gitignore_descriptor, b"*\n")
            os.fsync(gitignore_descriptor)
        finally:
            os.close(gitignore_descriptor)

        marker_descriptor = os.open(
            CHECKPOINT_RESTORE_MARKER_FILE,
            create_flags,
            0o600,
            dir_fd=root_descriptor,
        )
        try:
            _checkpoint_write_all(
                marker_descriptor, canonical(expected).encode("utf-8") + b"\n"
            )
            os.fsync(marker_descriptor)
        finally:
            os.close(marker_descriptor)
        if not _checkpoint_directory_still_in_parent(
            origin_descriptor, STATE_DIR_NAME, root_descriptor
        ):
            raise OSError("checkpoint restore state path changed")
        os.fsync(root_descriptor)
        os.fsync(origin_descriptor)
    except OSError:
        die("checkpoint restore marker could not be published")
    finally:
        for descriptor in (root_descriptor, origin_descriptor):
            if descriptor is not None:
                with contextlib.suppress(OSError):
                    os.close(descriptor)
    return worktree, stage, marker, False


def _checkpoint_restore_prepare_worktree_home(
    origin: str, worktree: str
) -> None:
    """Create the derived worktree home through pinned directory entries."""
    home = os.path.dirname(worktree)
    expected = os.path.join(origin, *WORKTREE_HOME)
    if home != expected:
        die("checkpoint restore derived worktree home changed")

    directory_descriptor = None
    gitignore_descriptor = None
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        directory_descriptor = os.open(origin, directory_flags)
        if not _checkpoint_directory_still_at_path(origin, directory_descriptor):
            raise OSError("checkpoint restore origin changed")
        for component in WORKTREE_HOME:
            try:
                os.mkdir(component, 0o700, dir_fd=directory_descriptor)
            except FileExistsError:
                pass
            next_descriptor = os.open(
                component, directory_flags, dir_fd=directory_descriptor
            )
            if not _checkpoint_directory_still_in_parent(
                directory_descriptor, component, next_descriptor
            ):
                os.close(next_descriptor)
                raise OSError("checkpoint restore worktree home changed")
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor

        if not _checkpoint_directory_still_at_path(home, directory_descriptor):
            raise OSError("checkpoint restore worktree home changed")
        try:
            initial = os.stat(
                ".gitignore", dir_fd=directory_descriptor, follow_symlinks=False
            )
        except FileNotFoundError:
            gitignore_descriptor = os.open(
                ".gitignore",
                os.O_RDWR
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=directory_descriptor,
            )
            _checkpoint_write_all(gitignore_descriptor, b"*\n")
            os.fsync(gitignore_descriptor)
        else:
            if (
                not stat.S_ISREG(initial.st_mode)
                or initial.st_nlink != 1
                or initial.st_size != 2
            ):
                raise OSError("checkpoint restore worktree ignore changed")
            gitignore_descriptor = os.open(
                ".gitignore",
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_descriptor,
            )
            opened = os.fstat(gitignore_descriptor)
            if (
                _checkpoint_stat_identity(opened)
                != _checkpoint_stat_identity(initial)
                or os.read(gitignore_descriptor, 3) != b"*\n"
            ):
                raise OSError("checkpoint restore worktree ignore changed")
        if not _checkpoint_directory_still_at_path(home, directory_descriptor):
            raise OSError("checkpoint restore worktree home changed")
        os.fsync(directory_descriptor)
    except OSError:
        die("checkpoint restore could not prepare its marker-owned worktree home")
    finally:
        for descriptor in (gitignore_descriptor, directory_descriptor):
            if descriptor is not None:
                with contextlib.suppress(OSError):
                    os.close(descriptor)


def _checkpoint_restore_retire_marker(
    origin: str, state: dict, digest: str, marker: str
) -> None:
    """Retire only the stable marker bytes owned by this transaction."""
    worktree, stage, expected_marker = _checkpoint_restore_marker_paths(
        origin, state, digest
    )
    if marker != expected_marker:
        die("checkpoint restore marker changed before retirement", 1)
    expected = canonical(
        _checkpoint_restore_marker_record(state, digest, worktree, stage)
    ).encode("utf-8") + b"\n"
    root = state_root(origin)
    name = os.path.basename(marker)
    root_descriptor = None
    marker_descriptor = None
    verified = False
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    root_flags = flags | getattr(os, "O_DIRECTORY", 0)
    try:
        root_descriptor = os.open(root, root_flags)
        if not _checkpoint_directory_still_at_path(root, root_descriptor):
            die("checkpoint restore marker changed before retirement", 1)
        initial = os.stat(name, dir_fd=root_descriptor, follow_symlinks=False)
        if (
            not stat.S_ISREG(initial.st_mode)
            or initial.st_nlink != 1
            or initial.st_size > CHECKPOINT_MANIFEST_BYTES_MAX
        ):
            die("checkpoint restore marker changed before retirement", 1)
        marker_descriptor = os.open(name, flags, dir_fd=root_descriptor)
        before = os.fstat(marker_descriptor)
        if _checkpoint_stat_identity(before) != _checkpoint_stat_identity(initial):
            die("checkpoint restore marker changed before retirement", 1)
        data = bytearray()
        while True:
            chunk = os.read(
                marker_descriptor,
                min(
                    CHECKPOINT_IO_CHUNK,
                    CHECKPOINT_MANIFEST_BYTES_MAX + 1 - len(data),
                ),
            )
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > CHECKPOINT_MANIFEST_BYTES_MAX:
                die("checkpoint restore marker changed before retirement", 1)
        after = os.fstat(marker_descriptor)
        named = os.stat(name, dir_fd=root_descriptor, follow_symlinks=False)
        if (
            bytes(data) != expected
            or len(data) != before.st_size
            or _checkpoint_stat_identity(after) != _checkpoint_stat_identity(before)
            or _checkpoint_stat_identity(named) != _checkpoint_stat_identity(before)
        ):
            die("checkpoint restore marker changed before retirement", 1)
        verified = True
        os.unlink(name, dir_fd=root_descriptor)
        if os.fstat(marker_descriptor).st_nlink != 0:
            die("checkpoint restore marker changed during retirement", 1)
        os.fsync(root_descriptor)
    except OSError:
        if verified:
            die("checkpoint restore completed but its marker could not be retired", 1)
        die("checkpoint restore marker changed before retirement", 1)
    finally:
        for descriptor in (marker_descriptor, root_descriptor):
            if descriptor is not None:
                with contextlib.suppress(OSError):
                    os.close(descriptor)


def _checkpoint_restore_breadcrumb(origin: str, worktree: str) -> None:
    """Publish or verify the one no-follow breadcrumb owned by restore."""
    payload = f"{worktree}\n".encode("utf-8")
    if len(payload) > SOURCE_BYTES_MAX:
        die("checkpoint restore breadcrumb exceeds the output cap", 1)
    root = state_root(origin)
    root_descriptor = None
    breadcrumb_descriptor = None
    created = False
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        root_descriptor = os.open(
            root, flags | getattr(os, "O_DIRECTORY", 0)
        )
        if not _checkpoint_directory_still_at_path(root, root_descriptor):
            die("checkpoint restore breadcrumb path changed", 1)
        try:
            initial = os.stat(
                WORKTREE_FILE, dir_fd=root_descriptor, follow_symlinks=False
            )
        except FileNotFoundError:
            breadcrumb_descriptor = os.open(
                WORKTREE_FILE,
                os.O_RDWR
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=root_descriptor,
            )
            _checkpoint_write_all(breadcrumb_descriptor, payload)
            os.fsync(breadcrumb_descriptor)
            os.lseek(breadcrumb_descriptor, 0, os.SEEK_SET)
            before = os.fstat(breadcrumb_descriptor)
            created = True
        else:
            if (
                not stat.S_ISREG(initial.st_mode)
                or initial.st_nlink != 1
                or initial.st_size != len(payload)
            ):
                die("checkpoint restore breadcrumb is not transaction-owned", 1)
            breadcrumb_descriptor = os.open(
                WORKTREE_FILE, flags, dir_fd=root_descriptor
            )
            before = os.fstat(breadcrumb_descriptor)
            if _checkpoint_stat_identity(before) != _checkpoint_stat_identity(
                initial
            ):
                die("checkpoint restore breadcrumb path changed", 1)
        data = bytearray()
        while True:
            chunk = os.read(breadcrumb_descriptor, CHECKPOINT_IO_CHUNK)
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > len(payload):
                die("checkpoint restore breadcrumb is not transaction-owned", 1)
        after = os.fstat(breadcrumb_descriptor)
        named = os.stat(
            WORKTREE_FILE, dir_fd=root_descriptor, follow_symlinks=False
        )
        if (
            bytes(data) != payload
            or _checkpoint_stat_identity(after) != _checkpoint_stat_identity(before)
            or _checkpoint_stat_identity(named) != _checkpoint_stat_identity(before)
            or not _checkpoint_directory_still_at_path(root, root_descriptor)
        ):
            die("checkpoint restore breadcrumb is not transaction-owned", 1)
        if created:
            os.fsync(root_descriptor)
    except OSError:
        die("checkpoint restore breadcrumb could not be published safely", 1)
    finally:
        for descriptor in (breadcrumb_descriptor, root_descriptor):
            if descriptor is not None:
                with contextlib.suppress(OSError):
                    os.close(descriptor)


def _checkpoint_restore_state(
    imported: dict,
    origin: str,
    worktree: str,
    manifest: dict,
    manifest_digest: str,
) -> tuple[dict, dict]:
    """Relocate controller paths and shape the same-ledger receipt."""
    state = json.loads(json.dumps(imported))
    old_origin = configured_git_path(state, "origin")
    old_worktree = configured_git_path(state, "worktree")
    for name in ("study", "runbook"):
        source_receipt = _checkpoint_restore_source_receipt(state, name)
        if source_receipt is None:
            continue
        artifact, _ = source_receipt
        receipt = as_dict(as_dict(state.get("receipts")).get(name))
        receipt["artifact"] = artifact
    state.pop("origin", None)
    state.pop("worktree", None)
    state["config"]["git"]["origin"] = origin
    state["config"]["git"]["worktree"] = worktree
    relocated = state_fingerprint(state)
    receipt = {
        "manifest_sha256": manifest_digest,
        "source_state_sha256": manifest["source"]["state_sha256"],
        "source_ledger_sha256": manifest["source"]["ledger_sha256"],
        "source_ledger_tail": manifest["source"]["ledger_tail"],
        "refs": manifest["boundary"]["refs"],
        "relocated_state_fingerprint": relocated,
        "old_origin": old_origin,
        "old_worktree": old_worktree,
        "origin": origin,
        "worktree": worktree,
    }
    return state, receipt


def _checkpoint_restore_verify_source(
    worktree: str, stage: str, state: dict, name: str
) -> None:
    """Verify a source against its fresh Git tree or staged controller copy."""
    source_receipt = _checkpoint_restore_source_receipt(state, name)
    if source_receipt is None:
        return
    artifact, expected = source_receipt
    prefix = STATE_DIR_NAME + "/"
    if not artifact.startswith(prefix):
        receipted_source(worktree, state, name)
        return
    relative = artifact[len(prefix):]
    data = _checkpoint_read_staged(
        os.path.join(stage, *relative.split("/")), SOURCE_BYTES_MAX
    )
    if hashlib.sha256(data).hexdigest() != expected:
        die(f"checkpoint {name} artefact does not match its receipt")


def _checkpoint_restore_active_state(
    worktree: str,
    imported: dict,
    origin: str,
    manifest: dict,
    manifest_digest: str,
    ledger_prefix: bytes,
) -> tuple[dict, bytes, str]:
    """Accept only the exact relocated state and one owned restore append."""
    state_bytes = _checkpoint_read_staged(state_path(worktree), SOURCE_BYTES_MAX)
    state = validate_state_shape(_checkpoint_json(state_bytes, "restored state"))
    expected_state, expected_receipt = _checkpoint_restore_state(
        imported, origin, worktree, manifest, manifest_digest
    )
    expected_state_bytes = (
        json.dumps(expected_state, indent=2, sort_keys=False).encode("utf-8") + b"\n"
    )
    ledger = _checkpoint_read_staged(
        ledger_path(worktree), CHECKPOINT_FILE_BYTES_MAX
    )
    if state != expected_state or state_bytes != expected_state_bytes:
        die("checkpoint restore found unowned active state")
    if not ledger.startswith(ledger_prefix):
        die("checkpoint restore found unowned active state")
    suffix = ledger[len(ledger_prefix):]
    if not suffix.endswith(b"\n") or suffix.count(b"\n") != 1:
        die("checkpoint restore found unowned active state")
    last = _checkpoint_json(suffix[:-1], "restore ledger entry")
    if not isinstance(last, dict):
        die("checkpoint restore found unowned active state")
    if (
        set(last) != {"ts", "event", "data", "prev", "state", "hash"}
        or last.get("event") != "checkpoint:restore"
        or last.get("data") != expected_receipt
        or last.get("prev") != manifest["source"]["ledger_tail"]
        or last.get("state") != state_fingerprint(expected_state)
        or json.dumps(last, sort_keys=True).encode("utf-8") + b"\n" != suffix
    ):
        die("checkpoint restore found unowned active state")
    count, tail = _checkpoint_ledger(ledger, state)
    if (
        count != manifest["source"]["ledger_entries"] + 1
        or tail != last.get("hash")
    ):
        die("checkpoint restore found unowned active state")
    return state, ledger, tail


def _checkpoint_restore_opaque_evidence(
    controller_root: str, inventory: list[dict]
) -> None:
    """Require every non-ledger controller file to retain its capsule bytes."""
    observed = _checkpoint_snapshot(
        controller_root, None, exclude_live_lock=False
    )
    expected_by_path = {item["path"]: item for item in inventory}
    observed_by_path = {item["path"]: item for item in observed}
    if set(observed_by_path) != set(expected_by_path):
        die("checkpoint restore changed opaque controller evidence")
    for path, expected in expected_by_path.items():
        relative = path.removeprefix(CHECKPOINT_CONTROLLER_DIR + "/")
        if relative in (STATE_FILE, LEDGER_FILE):
            continue
        if observed_by_path[path] != expected:
            die("checkpoint restore changed opaque controller evidence")


def _checkpoint_restore_worktree_branch(worktree: str, state: dict) -> None:
    """Require the restored worktree to remain attached to its recorded branch."""
    expected = run_branch_of(state)
    current = bounded_git(
        worktree,
        ["symbolic-ref", "--quiet", "--short", "HEAD"],
        refusal="checkpoint restored worktree branch changed during finalization",
    ).decode("utf-8", "replace").strip()
    if current != expected:
        die("checkpoint restored worktree branch changed during finalization")


def _checkpoint_restore_worktree_identity(
    worktree: str, expected: tuple[int, int] | None = None
) -> tuple[int, int]:
    """Pin the directory identity used by path-based restore checks."""
    descriptor = None
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        initial = os.lstat(worktree)
        descriptor = os.open(worktree, flags)
        opened = os.fstat(descriptor)
        identity = (opened.st_dev, opened.st_ino)
        if (
            not stat.S_ISDIR(initial.st_mode)
            or stat.S_ISLNK(initial.st_mode)
            or (initial.st_dev, initial.st_ino) != identity
            or not _checkpoint_directory_still_at_path(worktree, descriptor)
            or (expected is not None and identity != expected)
        ):
            raise OSError("checkpoint restored worktree changed")
        return identity
    except OSError:
        die("checkpoint restored worktree changed during finalization", 1)
    finally:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)


def _checkpoint_restore_write_files(
    stage: str, state: dict, ledger_prefix: bytes, receipt: dict
) -> tuple[bytes, str]:
    """Replace state and append exactly one receipt inside a private stage."""
    state_hash = state_fingerprint(state)
    entry = {
        "ts": now(),
        "event": "checkpoint:restore",
        "data": receipt,
        "prev": receipt["source_ledger_tail"],
        "state": state_hash,
    }
    entry["hash"] = hashlib.sha256(canonical(entry).encode()).hexdigest()
    ledger = ledger_prefix + json.dumps(entry, sort_keys=True).encode("utf-8") + b"\n"
    state_payload = json.dumps(state, indent=2, sort_keys=False).encode("utf-8") + b"\n"
    if len(state_payload) > SOURCE_BYTES_MAX:
        die("checkpoint relocated state exceeds the bounded controller-source cap")
    if len(ledger) > CHECKPOINT_FILE_BYTES_MAX:
        die("checkpoint relocated ledger exceeds the file byte ceiling")
    stage_descriptor = None
    try:
        stage_descriptor = os.open(
            stage,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        if not _checkpoint_directory_still_at_path(stage, stage_descriptor):
            raise OSError("checkpoint restore stage changed")
        for name, payload in ((STATE_FILE, state_payload), (LEDGER_FILE, ledger)):
            temporary = name + ".restore"
            descriptor = os.open(
                temporary,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=stage_descriptor,
            )
            try:
                _checkpoint_write_all(descriptor, payload)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.replace(
                temporary,
                name,
                src_dir_fd=stage_descriptor,
                dst_dir_fd=stage_descriptor,
            )
            if not _checkpoint_directory_still_at_path(stage, stage_descriptor):
                raise OSError("checkpoint restore stage changed")
        os.fsync(stage_descriptor)
    except OSError:
        die("checkpoint restore stage could not record relocated state")
    finally:
        if stage_descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(stage_descriptor)
    count, tail = _checkpoint_ledger(ledger, state)
    if count < 2 or tail != entry["hash"]:
        die("checkpoint restore receipt could not be verified")
    return ledger, tail


def _checkpoint_restore_internal_checks(
    worktree: str, manifest: dict, ledger: bytes
) -> tuple[int, dict, str]:
    """Run verify, status and semantic next without emitting their content."""
    count = verify_run(worktree)
    status_output = io.StringIO()
    with contextlib.redirect_stdout(status_output):
        cmd_status(argparse.Namespace(dir=worktree, json=False))
    status_bytes = status_output.getvalue().encode("utf-8")
    if len(status_bytes) > GIT_OUTPUT_MAX:
        die("checkpoint restored status exceeds the output cap", 1)
    state = load_state(worktree)
    directive = _next_directive(state)
    if directive != manifest["boundary"]["next"]:
        die("checkpoint restored next directive changed", 1)
    return count, directive, hashlib.sha256(status_bytes).hexdigest()


def _checkpoint_restore_result(
    *,
    manifest: dict,
    digest: str,
    worktree: str,
    ledger: bytes,
    ledger_tail: str,
    verify_count: int,
    directive: dict,
    status_sha256: str,
    state_fingerprint_value: str,
    recovery: str,
) -> dict:
    return {
        "schema": CHECKPOINT_RESTORE_RESULT_SCHEMA,
        "manifest_sha256": digest,
        "source_state_sha256": manifest["source"]["state_sha256"],
        "state_fingerprint": state_fingerprint_value,
        "source_ledger_sha256": manifest["source"]["ledger_sha256"],
        "ledger_sha256": hashlib.sha256(ledger).hexdigest(),
        "ledger_entries": verify_count,
        "ledger_tail": ledger_tail,
        "refs": len(manifest["boundary"]["refs"]),
        "worktree": worktree,
        "verify": "ok",
        "status_sha256": status_sha256,
        "next": directive,
        "recovery": recovery,
    }


def cmd_checkpoint_restore(args) -> None:
    """Restore one verified capsule into a fresh, separately restored Git tree."""
    origin = _checkpoint_restore_origin(args.dir)
    capsule, manifest, imported, _, ledger_prefix, inventory = (
        _checkpoint_restore_capsule(args.source, args.manifest_sha256)
    )
    refs = _checkpoint_refs(origin, imported)
    if refs != manifest["boundary"]["refs"]:
        die("checkpoint restored Git refs do not match the manifest")

    worktree, stage, marker = _checkpoint_restore_marker_paths(
        origin, imported, args.manifest_sha256
    )
    if os.path.realpath(os.path.dirname(worktree)) != os.path.dirname(worktree):
        die("checkpoint restore derived worktree path crosses a symlink")
    root = state_root(origin)
    marker_exists = os.path.isfile(marker)
    if not marker_exists:
        check_worktree_path(origin, worktree)
        refuse_checked_out_branch(origin, run_branch_of(imported))
    worktree, stage, marker, resumed = _checkpoint_restore_marker(
        origin, imported, args.manifest_sha256
    )

    final_root = state_root(worktree)
    final_safe = False
    if os.path.lexists(final_root):
        try:
            final_stat = os.lstat(final_root)
            final_safe = (
                stat.S_ISDIR(final_stat.st_mode)
                and not stat.S_ISLNK(final_stat.st_mode)
                and os.path.realpath(final_root) == final_root
            )
        except OSError:
            final_safe = False
    if resumed and final_safe and os.path.isfile(state_path(worktree)):
        worktree_identity = _checkpoint_restore_worktree_identity(worktree)
        state, ledger, ledger_tail = _checkpoint_restore_active_state(
            worktree,
            imported,
            origin,
            manifest,
            args.manifest_sha256,
            ledger_prefix,
        )
        _checkpoint_restore_opaque_evidence(final_root, inventory)
        _checkpoint_restore_worktree_identity(worktree, worktree_identity)
        _checkpoint_restore_worktree_branch(worktree, imported)
        verify_count, directive, status_digest = _checkpoint_restore_internal_checks(
            worktree, manifest, ledger
        )
        _checkpoint_restore_worktree_identity(worktree, worktree_identity)
        state, ledger, ledger_tail = _checkpoint_restore_active_state(
            worktree,
            imported,
            origin,
            manifest,
            args.manifest_sha256,
            ledger_prefix,
        )
        _checkpoint_restore_opaque_evidence(final_root, inventory)
        _checkpoint_restore_worktree_identity(worktree, worktree_identity)
        _checkpoint_restore_worktree_branch(worktree, imported)
        if _checkpoint_refs(origin, imported) != refs:
            die("checkpoint restored Git refs changed during finalization")
        _checkpoint_restore_breadcrumb(origin, worktree)
        _checkpoint_restore_worktree_identity(worktree, worktree_identity)
        state, ledger, ledger_tail = _checkpoint_restore_active_state(
            worktree,
            imported,
            origin,
            manifest,
            args.manifest_sha256,
            ledger_prefix,
        )
        _checkpoint_restore_opaque_evidence(final_root, inventory)
        _checkpoint_restore_worktree_identity(worktree, worktree_identity)
        _checkpoint_restore_worktree_branch(worktree, imported)
        if _checkpoint_refs(origin, imported) != refs:
            die("checkpoint restored Git refs changed during finalization")
        _checkpoint_restore_retire_marker(
            origin, imported, args.manifest_sha256, marker
        )
        print(
            json.dumps(
                _checkpoint_restore_result(
                    manifest=manifest,
                    digest=args.manifest_sha256,
                    worktree=worktree,
                    ledger=ledger,
                    ledger_tail=ledger_tail,
                    verify_count=verify_count,
                    directive=directive,
                    status_sha256=status_digest,
                    state_fingerprint_value=state_fingerprint(state),
                    recovery="finalized-interrupted-publication",
                ),
                sort_keys=True,
            )
        )
        return
    if resumed and (os.path.lexists(worktree) or os.path.lexists(stage)):
        die(
            "checkpoint restore transaction was interrupted before active state; "
            "its marker-owned paths were preserved for inspection"
        )

    _checkpoint_restore_prepare_worktree_home(origin, worktree)
    bounded_git(
        origin,
        ["worktree", "add", worktree, run_branch_of(imported)],
        refusal="checkpoint restore could not create its derived worktree",
    )
    try:
        worktree_stat = os.lstat(worktree)
    except OSError:
        die("checkpoint restore derived worktree changed after Git created it")
    if (
        not stat.S_ISDIR(worktree_stat.st_mode)
        or stat.S_ISLNK(worktree_stat.st_mode)
        or os.path.realpath(worktree) != worktree
        or repository_root(worktree) != worktree
    ):
        die("checkpoint restore derived worktree changed after Git created it")
    worktree_identity = _checkpoint_restore_worktree_identity(worktree)
    _checkpoint_restore_worktree_branch(worktree, imported)
    _checkpoint_restore_worktree_identity(worktree, worktree_identity)
    if _checkpoint_refs(origin, imported) != refs:
        die("checkpoint restored Git refs changed during relocation")
    if os.path.lexists(final_root) or os.path.lexists(stage):
        die("checkpoint restore derived worktree is occupied")
    try:
        os.mkdir(stage, 0o700)
    except OSError:
        die("checkpoint restore private stage could not be created")
    staged_inventory = _checkpoint_snapshot(
        os.path.join(capsule, CHECKPOINT_CONTROLLER_DIR),
        stage,
        exclude_live_lock=False,
    )
    if staged_inventory != inventory:
        die("checkpoint capsule changed during restore capture")
    if _checkpoint_refs(origin, imported) != refs:
        die("checkpoint restored Git refs changed during relocation")
    for name in ("study", "runbook"):
        _checkpoint_restore_verify_source(worktree, stage, imported, name)

    relocated, receipt = _checkpoint_restore_state(
        imported, origin, worktree, manifest, args.manifest_sha256
    )
    ledger, ledger_tail = _checkpoint_restore_write_files(
        stage, relocated, ledger_prefix, receipt
    )
    _checkpoint_restore_opaque_evidence(stage, inventory)
    _checkpoint_restore_worktree_branch(worktree, imported)
    if _checkpoint_refs(origin, imported) != refs:
        die("checkpoint restored Git refs changed before publication")
    _checkpoint_fsync_directories(stage)
    worktree_descriptor = None
    stage_descriptor = None
    working_descriptor = None
    try:
        worktree_descriptor = os.open(
            worktree,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        stage_descriptor = os.open(
            stage,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        working_descriptor = os.open(
            ".", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        if (
            not _checkpoint_directory_still_at_path(worktree, worktree_descriptor)
            or not _checkpoint_directory_still_in_parent(
                worktree_descriptor, os.path.basename(stage), stage_descriptor
            )
        ):
            die("checkpoint restore marker-owned paths changed before publication")
        os.fchdir(worktree_descriptor)
        _checkpoint_atomic_publish(os.path.basename(stage), STATE_DIR_NAME)
        if (
            not _checkpoint_directory_still_at_path(worktree, worktree_descriptor)
            or not _checkpoint_directory_still_in_parent(
                worktree_descriptor, STATE_DIR_NAME, stage_descriptor
            )
        ):
            die("checkpoint restore active state changed during publication", 1)
        _checkpoint_restore_worktree_branch(worktree, imported)
        if _checkpoint_refs(origin, imported) != refs:
            die("checkpoint restored Git refs changed during publication")
    except OSError:
        die("checkpoint restore marker-owned paths changed before publication")
    finally:
        if working_descriptor is not None:
            with contextlib.suppress(OSError):
                os.fchdir(working_descriptor)
        for descriptor in (working_descriptor, stage_descriptor, worktree_descriptor):
            if descriptor is not None:
                with contextlib.suppress(OSError):
                    os.close(descriptor)
    _checkpoint_restore_opaque_evidence(final_root, inventory)
    _checkpoint_restore_worktree_identity(worktree, worktree_identity)
    _checkpoint_restore_worktree_branch(worktree, imported)
    verify_count, directive, status_digest = _checkpoint_restore_internal_checks(
        worktree, manifest, ledger
    )
    _checkpoint_restore_worktree_identity(worktree, worktree_identity)
    relocated, ledger, ledger_tail = _checkpoint_restore_active_state(
        worktree,
        imported,
        origin,
        manifest,
        args.manifest_sha256,
        ledger_prefix,
    )
    _checkpoint_restore_opaque_evidence(final_root, inventory)
    _checkpoint_restore_worktree_identity(worktree, worktree_identity)
    _checkpoint_restore_worktree_branch(worktree, imported)
    if _checkpoint_refs(origin, imported) != refs:
        die("checkpoint restored Git refs changed during finalization")
    _checkpoint_restore_breadcrumb(origin, worktree)
    _checkpoint_restore_worktree_identity(worktree, worktree_identity)
    relocated, ledger, ledger_tail = _checkpoint_restore_active_state(
        worktree,
        imported,
        origin,
        manifest,
        args.manifest_sha256,
        ledger_prefix,
    )
    _checkpoint_restore_opaque_evidence(final_root, inventory)
    _checkpoint_restore_worktree_identity(worktree, worktree_identity)
    _checkpoint_restore_worktree_branch(worktree, imported)
    if _checkpoint_refs(origin, imported) != refs:
        die("checkpoint restored Git refs changed during finalization")
    _checkpoint_restore_retire_marker(
        origin, imported, args.manifest_sha256, marker
    )
    print(
        json.dumps(
            _checkpoint_restore_result(
                manifest=manifest,
                digest=args.manifest_sha256,
                worktree=worktree,
                ledger=ledger,
                ledger_tail=ledger_tail,
                verify_count=verify_count,
                directive=directive,
                status_sha256=status_digest,
                state_fingerprint_value=state_fingerprint(relocated),
                recovery="new",
            ),
            sort_keys=True,
        )
    )


def cmd_next(args) -> None:
    state = load_state(args.dir)
    directive = _next_directive(state, args.dir)
    if directive["do"] == "merge-step":
        # While the stack is still coming down the run branch has to be where the
        # loop left it, and this is the only point where a wrong merge can still
        # be worked around. Once every step has merged the branch may legitimately
        # carry a sync the controller has not receipted yet, and `done sync-run`
        # owns that topology, so the check stops when the stack does.
        refuse_unreceipted_run_branch_movement(args.dir, state)
        refuse_rewritten_stack(args.dir, state, directive.get("step") or 0)
    out = delegation_packet(args.dir, state, directive)
    print(json.dumps(out))


def _next_directive(state: dict, base_dir: str | None = None) -> dict:
    if state.get("halted"):
        return {"do": "halted", "reason": state["halted"]["reason"]}
    blocked = amendment_block(state)
    if blocked is not None:
        subject = blocked.get("subject", "study")
        return {
            "do": "blocked",
            "reason": (
                f"{subject} amendment marks step {blocked['step']} entry "
                f"{blocked['entry']} and exit {blocked['exit']}"
            ),
            "amendment_sha256": blocked["amendment_sha256"],
            f"{subject}_sha256": blocked.get(f"{subject}_sha256"),
            "recovery": (
                "inspect the amendment, halt the run, or use a separately "
                "specified runbook-repair transition"
            ),
        }
    phase = state["phase"]
    if phase == "study":
        return {
            "do": "study",
            "topic": state["topic"],
            "then": "hexctl done study --artifact <path> --skills <csv>",
        }
    if phase == "runbook":
        return {
            "do": "runbook",
            "then": "hexctl done runbook --artifact <path> --steps-file <path>",
        }
    if phase == "integrate":
        return _integrate_directive(state, base_dir)
    if phase == "done":
        return {
            "do": "done",
            "steps": len(state["steps"]),
            "finalise": {
                "status": "hexctl status",
                "verify": "hexctl verify",
                "retire": "hexctl reset",
                "archive": "local .hexaemeron/archive",
            },
        }
    step = current_step(state)
    base = {"step": step["n"], "title": step["title"]}
    if step["phase"] == "audit":
        if "security_suite" not in state["receipts"]:
            return {
                **base,
                "do": "resolve-security-suite",
                "then": "hexctl record security_suite '<ids or waived:reason>'",
            }
        rounds = step["audit"]["rounds"]
        max_rounds = max_rounds_of(state)
        lints_owed = not solidity_round(state)
        owed = {
            "audit_filter": audit_filter_obligation(),
            "elenchus_verdict": elenchus_verdict_obligation(),
            "log_path": configured_audit_log(state),
        }
        if lints_owed:
            owed["lints"] = [f"--{lint}-exit" for lint in LINTS]
        if not rounds:
            return {**base, "do": "audit-round", "round": 1, **owed}
        last = rounds[-1]
        if last["findings"] == 0:
            return {**base, "do": "close-audit", "rounds": len(rounds)}
        if len(rounds) >= max_rounds:
            return {
                **base,
                "do": "audit-verdict",
                "rounds": len(rounds),
                "open_findings": last["findings"],
            }
        return {
            **base,
            "do": "audit-round",
            "round": len(rounds) + 1,
            "prior_findings": last["findings"],
            **owed,
        }
    if step["phase"] == "issue":
        return {**base, "do": "implement", "legacy_issue_phase_skipped": True}
    if step["phase"] in ("implement", "push"):
        return {**base, "do": step["phase"], **branch_plan(state, step)}
    return {**base, "do": step["phase"]}


CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def clean(text: str) -> str:
    return CONTROL_RE.sub(" ", text)


def cmd_status(args) -> None:
    state = load_state(args.dir)
    version_relations = None
    resolution_state = None
    for name in ("study", "runbook"):
        receipt = as_dict(as_dict(state.get("receipts")).get(name))
        if receipt.get("sha256") is None:
            continue
        source = receipted_source(args.dir, state, name)
        if name == "runbook":
            _receipted_runbook_amendments(source)
            version_relations = receipted_version_relations(
                args.dir, source, state=state
            )
            if version_relations is not None:
                resolution_state = version_resolution_status(args.dir, state)
    if args.json:
        payload = dict(state)
        payload["observation_run_id"] = controller_run_id(state)
        if resolution_state is not None:
            payload["version_resolution_status"] = resolution_state
        print(json.dumps(payload, indent=2))
        return
    print(f"topic: {clean(state['topic'])}")
    print(f"base:  {state['base']}")
    if state.get("run_branch"):
        print(f"run:   {state['run_branch']} -> {state['base']}")
    if version_relations is not None:
        resolution_history = as_dict(state.get("integrate")).get(
            "version_resolutions"
        ) or []
        resolution = resolution_history[-1] if resolution_history else None
        current = (
            resolution
            if resolution_state["status"] in ("active", "terminal")
            else None
        )
        relation_packet = version_relations_packet(version_relations, current)
        resolution_text = (
            "resolution null"
            if resolution is None
            else (
                f"{resolution_state['status']} base "
                f"{resolution['base_commit']} head {resolution['head_commit']}"
            )
        )
        if resolution_state and resolution_state["reason"]:
            resolution_text += f"; reason {resolution_state['reason']}"
        print(
            "version relations: "
            f"{relation_packet['schema']}; source "
            f"{relation_packet['source_sha256']}; anchor "
            f"{relation_packet['anchor_commit']}; {resolution_text}"
        )
        resolved_targets = {
            target["skill"]: target for target in (resolution or {}).get("targets", [])
        }
        for target in relation_packet["targets"]:
            recorded = resolved_targets.get(target["skill"])
            if recorded is None:
                detail = f"projection {target['projection']}"
            else:
                detail = (
                    f"{resolution_state['status']} base {recorded['base_version']}; "
                    f"resolved {recorded['resolved_version']}"
                )
            print(
                f"version relation {target['skill']} ({target['ledger']}): anchor "
                f"{target['anchor_version']}; {detail}"
            )
    print(f"observe: {controller_run_id(state)}")
    if state.get("halted"):
        print(f"HALTED: {state['halted']['reason']}")
    blocked = amendment_block(state)
    if blocked is not None:
        print(
            f"BLOCKED: {blocked.get('subject', 'study')} amendment marks "
            f"step {blocked['step']} "
            f"entry {blocked['entry']} and exit {blocked['exit']}"
        )
    phase = state["phase"]
    if phase in ("study", "runbook"):
        print(f"phase: {phase} (day {DAY[phase]})")
    elif phase == "integrate":
        merged = len(as_dict(state.get("integrate")).get("merged") or [])
        print(
            f"phase: integrate ({merged}/{len(state['steps'])} steps merged "
            f"into {state['run_branch']})"
        )
        # Reported rather than refused. `status` is what somebody runs to find
        # out what is wrong, so an unreadable remote answers "unknown" here and
        # refuses at the receipt, where a wrong answer would be acted on.
        movement = unreceipted_run_branch_movement(args.dir, state)
        if movement is not None:
            print(f"STACK: {describe_run_branch_movement(movement)}")
        sync = as_dict(as_dict(state.get("integrate")).get("sync"))
        product = as_dict(sync.get("product_evidence"))
        revalidation = as_dict(sync.get("revalidation"))
        resolution_guard = as_dict(sync.get("resolution_guard"))
        if product:
            print(
                "evidence: product "
                f"{str(product.get('head', ''))[:12]} preserved; "
                f"{len(revalidation.get('checks') or [])} integration "
                "revalidation check(s) recorded"
            )
            if resolution_guard:
                print(
                    "evidence: sync resolution "
                    f"{len(resolution_guard.get('side_selected_paths') or [])} "
                    "whole-side path(s), "
                    f"{len(resolution_guard.get('superseded_intersection_paths') or [])} "
                    "superseded-intersection path(s), "
                    f"{len(resolution_guard.get('acknowledged_paths') or [])} "
                    "acknowledged"
                )
            else:
                print(
                    "evidence: sync resolution guard missing; supersede with "
                    "a fresh signed and revalidated sync"
                )
            superseded = as_dict(state.get("integrate")).get(
                "superseded_syncs"
            ) or []
            if superseded:
                print(f"evidence: {len(superseded)} superseded sync(s) retained")
    elif phase == "done":
        print(f"phase: done ({len(state['steps'])} steps shipped)")
    else:
        step = current_step(state)
        sp = step["phase"]
        day = "rest" if sp == "push" else f"day {DAY[sp]}"
        print(f"phase: step {step['n']}/{len(state['steps'])} '{clean(step['title'])}' -> {sp} ({day})")
        if sp == "audit":
            rounds = step["audit"]["rounds"]
            tail = rounds[-1]["findings"] if rounds else "-"
            print(f"audit: {len(rounds)} round(s), last findings: {tail}")
    for step in state["steps"]:
        mark = {"pending": " ", "open": ">", "done": "x"}[step["status"]]
        print(f"  [{mark}] {step['n']}. {clean(step['title'])}")


def cmd_halt(args) -> None:
    state = load_state(args.dir)
    if not args.reason:
        die("--reason is required")
    state["halted"] = {"reason": args.reason, "ts": now()}
    commit(args.dir, state, "halt", {"reason": args.reason})
    print(f"halted: {args.reason}")


def cmd_resume(args) -> None:
    state = load_state(args.dir)
    if not state.get("halted"):
        die("run is not halted")
    note = args.note or ""
    state["halted"] = None
    commit(args.dir, state, "resume", {"note": note})
    print("resumed")


def verify_run(
    base_dir: str,
    *,
    allow_pending_amendment: bool = False,
    allow_pending_resolution: bool = False,
) -> int:
    state = load_state(
        base_dir,
        allow_pending_amendment=allow_pending_amendment,
        allow_pending_resolution=allow_pending_resolution,
    )
    path = ledger_path(base_dir)
    if not os.path.exists(path):
        die("ledger missing", 1)
    prev = "genesis"
    count = 0
    last_state = None
    runbook_event = None
    resolution_events = []
    with open(path, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                expected = hashlib.sha256(
                    canonical(
                        {
                            "ts": entry["ts"],
                            "event": entry["event"],
                            "data": entry["data"],
                            "prev": entry["prev"],
                            "state": entry["state"],
                        }
                    ).encode()
                ).hexdigest()
                broken = entry["prev"] != prev or entry["hash"] != expected
            except (ValueError, KeyError, TypeError):
                broken = True
            if broken:
                die(f"ledger chain broken at line {i}", 1)
            if entry.get("event") == "done:runbook":
                runbook_event = entry.get("data")
            if entry.get("event") == "done:version-resolution":
                resolution_events.append(entry.get("data"))
            prev = entry["hash"]
            last_state = entry["state"]
            count += 1
    if last_state is not None and state_fingerprint(state) != last_state:
        die(
            "state file does not match the last ledger entry; "
            "state.json was edited outside hexctl", 1
        )
    study_receipt = as_dict(as_dict(state.get("receipts")).get("study"))
    if study_receipt.get("sha256") is not None:
        receipted_source(base_dir, state, "study")
    runbook_receipt = as_dict(as_dict(state.get("receipts")).get("runbook"))
    version_relations = None
    if runbook_receipt.get("sha256") is not None:
        runbook = receipted_source(base_dir, state, "runbook")
        _receipted_runbook_amendments(runbook)
        version_relations = receipted_version_relations(
            base_dir, runbook, state=state
        )
        event_relations = as_dict(runbook_event).get("version_relations")
        if version_relations is None and event_relations is not None:
            die("done:runbook ledger event has an unreceipted version anchor", 1)
        if version_relations is not None and event_relations != version_relations:
            die("done:runbook ledger event does not match the version anchor", 1)
    integrate_state = as_dict(state.get("integrate"))
    history = integrate_state.get("version_resolutions") or []
    if history:
        validate_version_resolution_history(
            history, "integrate.version_resolutions"
        )
    if version_relations is None and (history or resolution_events):
        die("literal-only run carries unreceipted version resolution evidence", 1)
    expected_resolution_events = [
        version_resolution_event(receipt) for receipt in history
    ]
    if resolution_events != expected_resolution_events:
        die(
            "version resolution state history does not match its controller "
            "ledger events",
            1,
        )
    terminal = as_dict(as_dict(state.get("receipts")).get("integrate"))
    terminal_resolution = terminal.get("version_resolution")
    if terminal_resolution is not None:
        validate_version_resolution_shape(
            terminal_resolution, "receipts.integrate.version_resolution"
        )
        if not history or terminal_resolution != history[-1]:
            die("terminal version resolution does not copy the active receipt", 1)
    if state.get("phase") == "done" and version_relations is not None:
        if not history or terminal_resolution != history[-1]:
            die("relation-bearing completed run has no terminal version resolution", 1)
    if state["phase"] == "integrate":
        merged = as_dict(state.get("integrate")).get("merged") or []
        expected = [s["n"] for s in state["steps"][: len(merged)]]
        if merged != expected:
            die(
                "integrate state is inconsistent: the stack must merge in step "
                f"order, got {merged}", 1
            )
    if state["phase"] == "steps":
        step = current_step(state)
        if step["status"] != "open" or step["phase"] not in STEP_PHASES:
            die("state inconsistent: current step is not open", 1)
    return count


def cmd_verify(args) -> None:
    count = verify_run(args.dir)
    if args.observations:
        state = load_state(args.dir)
        observation_count, tail_bytes = verify_observation_bindings(args.dir, state)
        suffix = (
            f"; unbound tail: {tail_bytes} bytes" if tail_bytes else ""
        )
        noun = "prefix" if observation_count == 1 else "prefixes"
        print(
            f"ok: {count} ledger entries, chain intact, state consistent; "
            f"{observation_count} observation {noun} verified{suffix}"
        )
        return
    print(f"ok: {count} ledger entries, chain intact, state consistent")


def cmd_reset(args) -> None:
    """Archive a completed run, and retire the worktree it ran in.

    Retirement belongs here rather than in `done integrate`, because the
    controller's own contract has the caller run `status` and `verify` after the
    run reports done. A tree removed at integrate would take the state and the
    ledger those two commands read with it, so the last thing a run did would be
    to delete its own evidence. `reset` is already the command that means the run
    is finished and can be put away.

    A run that lived in a worktree archives into the checkout it was started
    from, because archiving inside the tree and then removing the tree would
    destroy the archive in the same breath.
    """
    count = verify_run(args.dir)
    state = load_state(args.dir)
    if state["phase"] != "done":
        die(
            f"refusing to reset an incomplete run in phase '{state['phase']}'; "
            "resume it or halt it explicitly"
        )

    root = state_root(args.dir)
    origin = configured_git_path(state, "origin")
    worktree = configured_git_path(state, "worktree")
    retiring = bool(origin and worktree and os.path.isdir(worktree)
                    and os.path.realpath(worktree) == os.path.realpath(args.dir))
    archive_root = os.path.join(state_root(origin) if retiring else root, "archive")
    os.makedirs(archive_root, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    topic = re.sub(r"[^a-z0-9]+", "-", state["topic"].lower()).strip("-")[:48]
    name = f"{stamp}-{topic or 'completed-run'}"
    destination = os.path.join(archive_root, name)
    suffix = 2
    while os.path.exists(destination):
        destination = os.path.join(archive_root, f"{name}-{suffix}")
        suffix += 1
    os.makedirs(destination)

    preserved = {".gitignore", "archive", "checkpoints", "lock"}
    for entry in os.listdir(root):
        if entry in preserved:
            continue
        os.replace(os.path.join(root, entry), os.path.join(destination, entry))

    print(
        f"archived verified completed run ({count} ledger entries) locally at "
        f"{destination}; active state cleared"
    )
    if retiring:
        if worktree_is_clean(worktree) and remove_run_worktree(origin, worktree):
            print(f"run worktree removed: {worktree}")
        else:
            print(
                f"run worktree kept at {worktree}: it holds work git would not "
                f"discard. Nothing was forced.",
                file=sys.stderr,
            )
        write_breadcrumbs(origin)


# ---------------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hexctl", description=__doc__)
    p.add_argument("--dir", default=".", help="directory holding the state dir")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="start a run")
    sp.add_argument("--topic", required=True)
    sp.add_argument("--base", default="main")
    sp.add_argument(
        "--task-issue",
        dest="task_issue",
        help="task issue URL whose positive terminal issue number names the run",
    )
    sp.add_argument(
        "--run-branch",
        dest="run_branch",
        help="exact integration branch (default: topic slug, prefixed by task "
             "issue when supplied)",
    )
    sp.add_argument(
        "--frontier",
        help="EVOLUTION.md this run is meant to advance; the terminal receipt "
             "then refuses until it carries exactly one new valid row",
    )
    sp.add_argument(
        "--controller-currency-waiver",
        dest="controller_currency_waiver",
        metavar="REASON",
        help="proceed on a behind controller verdict, recording this reason "
             "in the run's evidence",
    )
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser("status", help="show run state")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser(
        "currency",
        help="report pin-versus-upstream currency for installed plugins",
    )
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_currency)

    sp = sub.add_parser("next", help="emit the single next action as JSON")
    sp.set_defaults(fn=cmd_next)

    sp = sub.add_parser("record", help="store a named receipt")
    sp.add_argument("key")
    sp.add_argument("value")
    sp.set_defaults(fn=cmd_record)

    sp = sub.add_parser(
        "observe",
        help="bind one companion observation prefix or unavailable capture state",
    )
    sp.add_argument("--artifact")
    sp.add_argument(
        "--capture-status",
        required=True,
        choices=OBSERVATION_CAPTURE_STATUSES,
    )
    sp.add_argument(
        "--redaction-status",
        required=True,
        choices=OBSERVATION_REDACTION_STATUSES,
    )
    sp.add_argument("--reason-code")
    sp.set_defaults(fn=cmd_observe)

    sp = sub.add_parser("amend", help="receipt a bounded mid-run amendment")
    amend = sp.add_subparsers(dest="amend_subject", required=True)
    study = amend.add_parser("study", help="receipt one append-only study amendment")
    study.add_argument("--artifact", required=True)
    study.set_defaults(fn=cmd_amend_study)
    runbook = amend.add_parser(
        "runbook", help="receipt one append-only runbook amendment"
    )
    runbook.add_argument("--artifact", required=True)
    runbook.set_defaults(fn=cmd_amend_runbook)

    sp = sub.add_parser("config", help="get or set a config value")
    sp.add_argument("action", choices=["get", "set"])
    sp.add_argument("path")
    sp.add_argument("value", nargs="?")
    sp.set_defaults(fn=cmd_config)

    sp = sub.add_parser("done", help="receipt a completed phase")
    sp.add_argument("phase", choices=list(DONE_HANDLERS))
    sp.add_argument("--artifact")
    sp.add_argument("--skills")
    sp.add_argument("--steps-file", dest="steps_file")
    sp.add_argument("--branch")
    sp.add_argument("--commit")
    sp.add_argument("--base-commit", dest="base_commit")
    sp.add_argument("--revalidation")
    sp.add_argument("--supersede-sync", dest="supersede_sync")
    sp.add_argument(
        "--acknowledge-sync-path",
        dest="acknowledge_sync_paths",
        action="append",
        default=[],
    )
    sp.add_argument("--tests")
    sp.add_argument("--no-further-leads", dest="no_further_leads", action="store_true")
    sp.add_argument("--reason")
    sp.add_argument("--fixes-ref", dest="fixes_ref")
    sp.add_argument("--log")
    sp.add_argument("--files", type=int)
    sp.add_argument("--pr-url", dest="pr_url")
    sp.add_argument("--pr-base", dest="pr_base")
    sp.add_argument("--step", type=int)
    sp.add_argument("--head-commit", dest="head_commit")
    sp.add_argument("--merge-commit", dest="merge_commit")
    sp.add_argument("--closed-issue-url", dest="closed_issue_url")
    sp.set_defaults(fn=cmd_done)

    sp = sub.add_parser("audit-round", help="record one security round")
    sp.add_argument("--findings", type=int, required=True)
    sp.add_argument("--log")
    sp.add_argument("--audit-filter", dest="audit_filter")
    sp.add_argument("--fixes-commit", dest="fixes_commit")
    sp.add_argument(
        "--elenchus-verdict",
        dest="elenchus_verdict",
        choices=ELENCHUS_VERDICTS,
    )
    for lint in LINTS:
        sp.add_argument(
            f"--{lint}-exit",
            dest=f"{lint}_exit",
            type=int,
            help=f"the exit status {lint} returned; 0 is clean",
        )
    sp.set_defaults(fn=cmd_audit_round)

    sp = sub.add_parser("halt", help="stop the run with a reason")
    sp.add_argument("--reason")
    sp.set_defaults(fn=cmd_halt)

    sp = sub.add_parser("resume", help="clear a halt")
    sp.add_argument("--note")
    sp.set_defaults(fn=cmd_resume)

    sp = sub.add_parser(
        "checkpoint", help="export or restore portable controller state"
    )
    checkpoint = sp.add_subparsers(dest="checkpoint_action", required=True)
    export = checkpoint.add_parser(
        "export", help="write one deterministic controller capsule"
    )
    export.add_argument("--out", required=True, metavar="DIRECTORY")
    export.set_defaults(fn=cmd_checkpoint_export)
    restore = checkpoint.add_parser(
        "restore", help="relocate one verified controller capsule"
    )
    restore.add_argument("--from", dest="source", required=True, metavar="DIRECTORY")
    restore.add_argument(
        "--manifest-sha256", required=True, metavar="SHA256"
    )
    restore.set_defaults(fn=cmd_checkpoint_restore)

    sp = sub.add_parser(
        "reset", help="archive a completed run and clear its active state"
    )
    sp.set_defaults(fn=cmd_reset)

    sp = sub.add_parser("verify", help="check ledger chain and state consistency")
    sp.add_argument(
        "--observations",
        action="store_true",
        help="also recompute every selected companion observation prefix",
    )
    sp.set_defaults(fn=cmd_verify)

    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.fn.__name__ in MUTATING:
        with held_lock(args.dir, args.fn.__name__):
            args.fn(args)
        return
    args.fn(args)


if __name__ == "__main__":
    main()
