"""Exclusive content-free receipt sink for one model proxy job."""

from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import threading
from typing import Mapping

from .canonical import MAX_SAFE_INTEGER, canonical_json
from .errors import PolicyError, refuse
from .policy import POLICY_COMPILER, POLICY_SCHEMA
from .profiles import LOOPBACK_TEXT_V1


RECEIPT_SCHEMA = "model-proxy-receipt/v1"
MAX_RECEIPT_BYTES = 4_096
MAX_TIMING_VALUE = 10**30 - 1

_JOB_ID = re.compile(r"[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_DECIMAL_TIMING = re.compile(r"(?:0|[1-9][0-9]{0,29})\Z")
_OUTCOME_CODE = re.compile(r"MP[0-9]{3}\Z")

_ROOT_FIELDS = frozenset(
    {
        "schema",
        "event",
        "job_id",
        "jobspec_sha256",
        "policy_sha256",
        "profile",
        "sequence",
        "versions",
        "counts",
        "timings",
        "disclosure_state",
        "outcome_code",
    }
)
_VERSION_FIELDS = frozenset(
    {"policy_schema", "compiler", "token_counter", "receipt_schema"}
)
_ACTIVATION_COUNTS = frozenset()
_ACTIVATION_TIMINGS = frozenset(
    {"activated_monotonic_ns", "absolute_expiry_unix_ns", "elapsed_deadline_ns"}
)
_REQUEST_COUNTS = frozenset(
    {
        "request_bytes",
        "input_tokens",
        "reserved_output_tokens",
        "reserved_response_bytes",
        "concurrency",
    }
)
_REQUEST_TIMINGS = frozenset({"admitted_monotonic_ns", "remaining_wall_ns"})
_TERMINAL_COUNTS = frozenset(
    {
        "requests",
        "request_bytes",
        "response_bytes",
        "input_tokens",
        "output_tokens",
        "concurrency",
    }
)
_TERMINAL_TIMINGS = frozenset({"terminal_monotonic_ns", "duration_ns"})
_EXPECTED_VERSIONS = {
    "policy_schema": POLICY_SCHEMA,
    "compiler": POLICY_COMPILER,
    "token_counter": LOOPBACK_TEXT_V1.token_counter,
    "receipt_schema": RECEIPT_SCHEMA,
}


def _positive_limit(value: object, field: str, ceiling: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > ceiling
    ):
        refuse("MP408", field)
    return value


def _timing(value: int, field: str) -> str:
    """Keep nanosecond values exact without exceeding JSON's safe integer range."""

    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > MAX_TIMING_VALUE
    ):
        refuse("MP408", field)
    return str(value)


def _mapping(value: object, field: str) -> dict[str, object]:
    try:
        copied = dict(value)  # type: ignore[arg-type]
    except Exception:
        refuse("MP408", field)
    return copied


def _nonnegative_count(value: object, field: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > MAX_SAFE_INTEGER
    ):
        refuse("MP408", field)
    return value


def _close_after_refusal(descriptor: int | None) -> None:
    """Attempt one descriptor close without replacing the fixed refusal."""

    if descriptor is None:
        return
    try:
        os.close(descriptor)
    except OSError:
        pass


def _open_parent(path: str | os.PathLike[str]) -> tuple[int, str, str]:
    """Open every parent component without following a symbolic link."""

    try:
        raw = os.fspath(path)
    except Exception:
        refuse("MP407", "receipt.path")
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        refuse("MP407", "receipt.path")
    try:
        raw_parts = Path(raw).parts
        absolute_path = os.path.abspath(raw)
        parts = Path(absolute_path).parts
    except (OSError, ValueError):
        refuse("MP407", "receipt.path")
    raw_components = raw_parts[1:] if os.path.isabs(raw) else raw_parts
    if not raw_components or any(
        part in {"", ".", ".."} for part in raw_components
    ):
        refuse("MP407", "receipt.path")
    if not parts:
        refuse("MP407", "receipt.path")
    components = parts[1:]
    if not components or components[-1] in {"", ".", ".."}:
        refuse("MP407", "receipt.path")
    if any(part in {"", ".", ".."} for part in components):
        refuse("MP407", "receipt.path")

    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open("/", directory_flags)
    except (OSError, ValueError):
        refuse("MP407", "receipt.path")
    for component in components[:-1]:
        try:
            child = os.open(component, directory_flags, dir_fd=descriptor)
        except (OSError, ValueError):
            _close_after_refusal(descriptor)
            refuse("MP407", "receipt.path")
        try:
            os.close(descriptor)
        except OSError:
            _close_after_refusal(child)
            refuse("MP407", "receipt.path")
        descriptor = child
    return descriptor, components[-1], absolute_path


class ReceiptSink:
    """Write one fresh, private JSONL receipt file and never resume it."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        max_record_bytes: int,
        max_records: int,
    ):
        self._max_record_bytes = _positive_limit(
            max_record_bytes, "receipt.max_record_bytes", MAX_RECEIPT_BYTES
        )
        self._max_records = _positive_limit(
            max_records, "receipt.max_records", 1_024
        )
        self._lock = threading.Lock()
        self._descriptor: int | None = None
        self._parent_descriptor: int | None = None
        self._path = ""
        self._name = ""
        self._identity: tuple[int, int] | None = None
        self._parent_identity: tuple[int, int] | None = None
        self._records = 0
        self._activation_written = False
        self._terminal_written = False
        self._request_sequences: set[int] = set()
        self._poisoned = False

        parent, name, absolute_path = _open_parent(path)
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor: int | None = None
        try:
            descriptor = os.open(name, flags, 0o600, dir_fd=parent)
            os.fchmod(descriptor, 0o600)
            status = os.fstat(descriptor)
            parent_status = os.fstat(parent)
            if (
                not stat.S_ISREG(status.st_mode)
                or status.st_nlink != 1
                or stat.S_IMODE(status.st_mode) != 0o600
            ):
                raise OSError("unsafe receipt target")
        except (OSError, ValueError):
            _close_after_refusal(descriptor)
            _close_after_refusal(parent)
            refuse("MP407", "receipt.path")
        self._descriptor = descriptor
        self._parent_descriptor = parent
        self._path = absolute_path
        self._name = name
        self._identity = (status.st_dev, status.st_ino)
        self._parent_identity = (parent_status.st_dev, parent_status.st_ino)

    @property
    def records(self) -> int:
        with self._lock:
            return self._records

    def _same_target(self) -> bool:
        descriptor = self._descriptor
        parent = self._parent_descriptor
        identity = self._identity
        parent_identity = self._parent_identity
        if (
            descriptor is None
            or parent is None
            or identity is None
            or parent_identity is None
            or not self._path
        ):
            return False
        named_parent: int | None = None
        same = False
        try:
            opened = os.fstat(descriptor)
            retained_parent = os.fstat(parent)
            named_parent, named_name, _absolute_path = _open_parent(self._path)
            reopened_parent = os.fstat(named_parent)
            named = os.stat(
                named_name, dir_fd=named_parent, follow_symlinks=False
            )
            same = (
                named_name == self._name
                and stat.S_ISREG(opened.st_mode)
                and stat.S_ISREG(named.st_mode)
                and opened.st_nlink == 1
                and named.st_nlink == 1
                and (opened.st_dev, opened.st_ino) == identity
                and (named.st_dev, named.st_ino) == identity
                and (retained_parent.st_dev, retained_parent.st_ino)
                == parent_identity
                and (reopened_parent.st_dev, reopened_parent.st_ino)
                == parent_identity
                and stat.S_IMODE(opened.st_mode) == 0o600
            )
        except (OSError, PolicyError):
            same = False
        if named_parent is not None:
            try:
                os.close(named_parent)
            except OSError:
                same = False
        return same

    def _write(self, document: dict[str, object]) -> None:
        with self._lock:
            if self._poisoned or self._terminal_written:
                refuse("MP407", "receipt.state")
            if frozenset(document) != _ROOT_FIELDS:
                refuse("MP408", "receipt.schema")
            event = document["event"]
            if not isinstance(event, str) or event not in {
                "activation",
                "request",
                "terminal",
            }:
                refuse("MP408", "receipt.event")
            if document["schema"] != RECEIPT_SCHEMA:
                refuse("MP408", "receipt.schema")
            job_id = document["job_id"]
            if not isinstance(job_id, str) or _JOB_ID.fullmatch(job_id) is None:
                refuse("MP408", "receipt.job_id")
            if any(
                not isinstance(document[field], str)
                or _SHA256.fullmatch(document[field]) is None
                for field in ("jobspec_sha256", "policy_sha256")
            ):
                refuse("MP408", "receipt.digest")
            if document["profile"] != LOOPBACK_TEXT_V1.identifier:
                refuse("MP408", "receipt.profile")
            versions = document["versions"]
            counts = document["counts"]
            timings = document["timings"]
            if (
                not isinstance(versions, dict)
                or frozenset(versions) != _VERSION_FIELDS
                or versions != _EXPECTED_VERSIONS
            ):
                refuse("MP408", "receipt.versions")
            expected_counts = {
                "activation": _ACTIVATION_COUNTS,
                "request": _REQUEST_COUNTS,
                "terminal": _TERMINAL_COUNTS,
            }[event]
            expected_timings = {
                "activation": _ACTIVATION_TIMINGS,
                "request": _REQUEST_TIMINGS,
                "terminal": _TERMINAL_TIMINGS,
            }[event]
            if not isinstance(counts, dict) or frozenset(counts) != expected_counts:
                refuse("MP408", "receipt.counts")
            if not isinstance(timings, dict) or frozenset(timings) != expected_timings:
                refuse("MP408", "receipt.timings")
            for name, value in counts.items():
                _nonnegative_count(value, f"receipt.counts.{name}")
            if event == "request" and any(
                counts[name] < 1
                for name in (
                    "request_bytes",
                    "reserved_output_tokens",
                    "reserved_response_bytes",
                    "concurrency",
                )
            ):
                refuse("MP408", "receipt.counts")
            if any(
                not isinstance(value, str)
                or _DECIMAL_TIMING.fullmatch(value) is None
                for value in timings.values()
            ):
                refuse("MP408", "receipt.timings")
            sequence = document["sequence"]
            disclosure_state = document["disclosure_state"]
            outcome_code = document["outcome_code"]
            if (
                isinstance(sequence, bool)
                or not isinstance(sequence, int)
                or sequence < 0
                or sequence > MAX_SAFE_INTEGER
                or not isinstance(outcome_code, str)
                or _OUTCOME_CODE.fullmatch(outcome_code) is None
            ):
                refuse("MP408", "receipt.outcome")
            if event == "activation":
                if self._activation_written or self._records != 0:
                    refuse("MP407", "receipt.activation")
                if (
                    sequence != 0
                    or disclosure_state != "not-read"
                    or outcome_code != "MP000"
                ):
                    refuse("MP408", "receipt.activation")
            elif event == "request":
                if (
                    not self._activation_written
                    or sequence < 1
                    or sequence in self._request_sequences
                ):
                    refuse("MP407", "receipt.sequence")
                if disclosure_state != "not-read" or outcome_code != "MP000":
                    refuse("MP408", "receipt.request")
            else:
                if not self._activation_written or self._terminal_written:
                    refuse("MP407", "receipt.terminal")
                if (
                    sequence != 0
                    or disclosure_state not in {"not-read", "provider-only"}
                ):
                    refuse("MP408", "receipt.terminal")
            if self._records >= self._max_records:
                refuse("MP407", "receipt.count")
            encoded = canonical_json(document)
            if len(encoded) > self._max_record_bytes or len(encoded) > MAX_RECEIPT_BYTES:
                refuse("MP408", "receipt.bytes")
            if not self._same_target():
                self._poisoned = True
                refuse("MP407", "receipt.replacement")
            descriptor = self._descriptor
            if descriptor is None:
                self._poisoned = True
                refuse("MP407", "receipt.state")
            line = encoded + b"\n"
            try:
                written = os.write(descriptor, line)
                if written != len(line):
                    self._poisoned = True
                    refuse("MP407", "receipt.write")
                os.fsync(descriptor)
                if event == "activation":
                    parent = self._parent_descriptor
                    if parent is None:
                        self._poisoned = True
                        refuse("MP407", "receipt.state")
                    os.fsync(parent)
            except PolicyError:
                raise
            except OSError:
                self._poisoned = True
                refuse("MP407", "receipt.write")
            if not self._same_target():
                self._poisoned = True
                refuse("MP407", "receipt.replacement")
            self._records += 1
            if event == "activation":
                self._activation_written = True
            elif event == "request":
                self._request_sequences.add(sequence)
            else:
                self._terminal_written = True

    def write_activation(
        self,
        *,
        job_id: str,
        jobspec_sha256: str,
        policy_sha256: str,
        profile: str,
        versions: Mapping[str, str],
        activated_monotonic_ns: int,
        absolute_expiry_unix_ns: int,
        elapsed_deadline_ns: int,
    ) -> None:
        self._write(
            {
                "schema": RECEIPT_SCHEMA,
                "event": "activation",
                "job_id": job_id,
                "jobspec_sha256": jobspec_sha256,
                "policy_sha256": policy_sha256,
                "profile": profile,
                "sequence": 0,
                "versions": _mapping(versions, "receipt.versions"),
                "counts": {},
                "timings": {
                    "activated_monotonic_ns": _timing(
                        activated_monotonic_ns, "receipt.activated_monotonic_ns"
                    ),
                    "absolute_expiry_unix_ns": _timing(
                        absolute_expiry_unix_ns, "receipt.absolute_expiry_unix_ns"
                    ),
                    "elapsed_deadline_ns": _timing(
                        elapsed_deadline_ns, "receipt.elapsed_deadline_ns"
                    ),
                },
                "disclosure_state": "not-read",
                "outcome_code": "MP000",
            }
        )

    def write_request(
        self,
        *,
        job_id: str,
        jobspec_sha256: str,
        policy_sha256: str,
        profile: str,
        versions: Mapping[str, str],
        sequence: int,
        counts: Mapping[str, int],
        admitted_monotonic_ns: int,
        remaining_wall_ns: int,
    ) -> None:
        self._write(
            {
                "schema": RECEIPT_SCHEMA,
                "event": "request",
                "job_id": job_id,
                "jobspec_sha256": jobspec_sha256,
                "policy_sha256": policy_sha256,
                "profile": profile,
                "sequence": sequence,
                "versions": _mapping(versions, "receipt.versions"),
                "counts": _mapping(counts, "receipt.counts"),
                "timings": {
                    "admitted_monotonic_ns": _timing(
                        admitted_monotonic_ns, "receipt.admitted_monotonic_ns"
                    ),
                    "remaining_wall_ns": _timing(
                        remaining_wall_ns, "receipt.remaining_wall_ns"
                    ),
                },
                "disclosure_state": "not-read",
                "outcome_code": "MP000",
            }
        )

    def write_terminal(
        self,
        *,
        job_id: str,
        jobspec_sha256: str,
        policy_sha256: str,
        profile: str,
        versions: Mapping[str, str],
        counts: Mapping[str, int],
        terminal_monotonic_ns: int,
        duration_ns: int,
        disclosure_state: str,
        outcome_code: str,
    ) -> None:
        self._write(
            {
                "schema": RECEIPT_SCHEMA,
                "event": "terminal",
                "job_id": job_id,
                "jobspec_sha256": jobspec_sha256,
                "policy_sha256": policy_sha256,
                "profile": profile,
                "sequence": 0,
                "versions": _mapping(versions, "receipt.versions"),
                "counts": _mapping(counts, "receipt.counts"),
                "timings": {
                    "terminal_monotonic_ns": _timing(
                        terminal_monotonic_ns, "receipt.terminal_monotonic_ns"
                    ),
                    "duration_ns": _timing(duration_ns, "receipt.duration_ns"),
                },
                "disclosure_state": disclosure_state,
                "outcome_code": outcome_code,
            }
        )

    def close(self) -> None:
        with self._lock:
            descriptor = self._descriptor
            parent = self._parent_descriptor
            self._descriptor = None
            self._parent_descriptor = None
            failed = False
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    failed = True
            if parent is not None:
                try:
                    os.close(parent)
                except OSError:
                    failed = True
            if failed:
                self._poisoned = True
                refuse("MP407", "receipt.close")
