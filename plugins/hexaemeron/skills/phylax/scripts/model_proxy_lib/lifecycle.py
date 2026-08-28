"""Atomic quotas, lifecycle, and durable receipts for one model proxy job."""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
import secrets
import struct
import tempfile
import threading
import time
from types import MappingProxyType
from typing import Callable, Mapping

from .canonical import (
    MAX_JSON_MEMBERS,
    canonical_json,
    parse_json_bytes,
    read_bounded_file,
)
from .errors import PolicyError, refuse
from .framing import REQUEST_SCHEMA, RESPONSE_SCHEMA, TEXT_OPERATION, TextRequest
from .operator import render_operator_text
from .policy import CompiledPolicy, compile_policy, compile_policy_file
from .profiles import ProviderProfile, resolve_profile
from .provider import ProviderEvent, ProviderSession, provider_request_bytes
from .receipts import RECEIPT_SCHEMA, ReceiptSink
from .transport import HTTPSConnector, HTTPSRequest, HTTPSResponse


LIFECYCLE_MANIFEST_SCHEMA = "model-proxy-lifecycle-cases/v1"
MAX_LIFECYCLE_MANIFEST_BYTES = 128 * 1024
NANOSECONDS_PER_SECOND = 1_000_000_000

_CASE_ID = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\Z")
_OUTCOME_CODE = re.compile(r"MP[0-9]{3}\Z")
_MANIFEST_FIELDS = frozenset({"schema", "accepted_job", "cases"})
_CASE_FIELDS = frozenset(
    {"id", "input", "output", "monotonic_start_ns", "wall_start_unix_seconds"}
)

Clock = Callable[[], int]


def _terminal_refusal_code(snapshot: TerminalSnapshot) -> str:
    return "MP401" if snapshot.code == "MP000" else snapshot.code


@dataclass(frozen=True, slots=True)
class Reservation:
    """One content-free atomic reservation bound to its owning job."""

    job_id: str
    jobspec_sha256: str
    sequence: int
    request_bytes: int
    input_tokens: int
    reserved_output_tokens: int
    reserved_response_bytes: int
    concurrency: int
    admitted_monotonic_ns: int
    remaining_wall_ns: int
    _owner: object = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class TerminalSnapshot:
    """The first terminal transition and its bounded counters."""

    code: str
    disclosure_state: str
    terminal_monotonic_ns: int
    duration_ns: int
    counts: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class LifecycleManifestResult:
    """Safe summary of deterministic lifecycle component vectors."""

    cases: int
    requests: int
    receipts: int
    policy_sha256: str


def _clock_value(clock: Clock, field_name: str) -> int:
    try:
        value = clock()
    except Exception:
        refuse("MP405", field_name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        refuse("MP405", field_name)
    return value


def _unix_ns(timestamp: str) -> int:
    try:
        parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        refuse("MP400", "lifecycle.expiry")
    return calendar.timegm(parsed.timetuple()) * NANOSECONDS_PER_SECOND


def _replay_policy(policy: CompiledPolicy) -> tuple[CompiledPolicy, ProviderProfile]:
    if type(policy) is not CompiledPolicy:
        refuse("MP400", "lifecycle.policy")
    try:
        replayed = compile_policy(policy.accepted_job_bytes)
    except (PolicyError, TypeError):
        refuse("MP400", "lifecycle.policy")
    if (
        replayed.policy_bytes != policy.policy_bytes
        or replayed.policy_sha256 != policy.policy_sha256
        or replayed.jobspec_sha256 != policy.jobspec_sha256
        or replayed.profile != policy.profile
    ):
        refuse("MP400", "lifecycle.policy")
    return replayed, resolve_profile(replayed.profile)


def _count_input(profile: ProviderProfile, input_text: str) -> int:
    if profile.token_counter != "unicode-codepoint-fixture/v1":
        refuse("MP409", "lifecycle.token_counter")
    if not isinstance(input_text, str):
        refuse("MP409", "lifecycle.input")
    return len(input_text)


class LifecycleController:
    """Linearise one job's reservations and terminal transition under a lock."""

    def __init__(
        self,
        policy: CompiledPolicy,
        *,
        monotonic_clock: Clock = time.monotonic_ns,
        wall_clock: Clock = time.time_ns,
    ):
        replayed, profile = _replay_policy(policy)
        if not callable(monotonic_clock) or not callable(wall_clock):
            refuse("MP405", "lifecycle.clock")
        _count_input(profile, "")
        self._policy = replayed
        self._profile = profile
        self._limits = MappingProxyType(dict(replayed.document["limits"]))
        self._job_id = replayed.document["job"]["id"]
        self._jobspec_sha256 = replayed.jobspec_sha256
        self._monotonic_clock = monotonic_clock
        self._wall_clock = wall_clock
        self._started_monotonic_ns = _clock_value(
            monotonic_clock, "lifecycle.monotonic_clock"
        )
        self._last_monotonic_ns = self._started_monotonic_ns
        self._started_wall_ns = _clock_value(wall_clock, "lifecycle.wall_clock")
        self._absolute_expiry_ns = _unix_ns(
            replayed.document["job"]["expires_at"]
        )
        if self._started_wall_ns >= self._absolute_expiry_ns:
            refuse("MP404", "lifecycle.absolute_expiry")
        elapsed_ns = self._limits["total_wall_seconds"] * NANOSECONDS_PER_SECOND
        self._elapsed_deadline_ns = self._started_monotonic_ns + elapsed_ns
        signed_absolute_lifetime_ns = (
            replayed.document["job"]["absolute_lifetime_seconds"]
            * NANOSECONDS_PER_SECOND
        )
        self._absolute_window_ns = min(
            self._absolute_expiry_ns - self._started_wall_ns,
            signed_absolute_lifetime_ns,
        )
        self._absolute_deadline_monotonic_ns = (
            self._started_monotonic_ns + self._absolute_window_ns
        )
        self._lock = threading.Lock()
        self._owner = object()
        self._active: dict[int, Reservation] = {}
        self._disclosed: set[int] = set()
        self._provider_disclosed = False
        self._seen: set[int] = set()
        self._requests = 0
        self._request_bytes = 0
        self._response_bytes = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._reserved_response_bytes = 0
        self._reserved_output_tokens = 0
        self._terminal: TerminalSnapshot | None = None

    @property
    def job_id(self) -> str:
        return self._job_id

    @property
    def jobspec_sha256(self) -> str:
        return self._jobspec_sha256

    @property
    def policy_sha256(self) -> str:
        return self._policy.policy_sha256

    @property
    def policy(self) -> CompiledPolicy:
        return self._policy

    @property
    def profile(self) -> ProviderProfile:
        return self._profile

    @property
    def limits(self) -> Mapping[str, int]:
        return self._limits

    @property
    def started_monotonic_ns(self) -> int:
        return self._started_monotonic_ns

    @property
    def absolute_expiry_ns(self) -> int:
        return self._absolute_expiry_ns

    @property
    def elapsed_deadline_ns(self) -> int:
        return self._elapsed_deadline_ns

    @property
    def terminal(self) -> TerminalSnapshot | None:
        with self._lock:
            return self._terminal

    def activate(self) -> None:
        """Make a second activation an explicit refusal."""

        refuse("MP401", "lifecycle.activation")

    def _counts_locked(self) -> Mapping[str, int]:
        return MappingProxyType(
            {
                "requests": self._requests,
                "request_bytes": self._request_bytes,
                "response_bytes": self._response_bytes,
                "input_tokens": self._input_tokens,
                "output_tokens": self._output_tokens,
                "concurrency": len(self._active),
            }
        )

    def _disclosure_state_locked(self) -> str:
        return "provider-only" if self._provider_disclosed else "not-read"

    def _monotonic_locked(self) -> int:
        value = _clock_value(
            self._monotonic_clock, "lifecycle.monotonic_clock"
        )
        if value < self._last_monotonic_ns:
            refuse("MP405", "lifecycle.monotonic_clock")
        self._last_monotonic_ns = value
        return value

    def _wall_locked(self) -> int:
        return _clock_value(self._wall_clock, "lifecycle.wall_clock")

    def _terminal_locked(
        self,
        code: str,
        disclosure_state: str,
        now_monotonic_ns: int | None = None,
    ) -> TerminalSnapshot:
        if self._terminal is not None:
            return self._terminal
        if now_monotonic_ns is None:
            try:
                now = self._monotonic_locked()
            except PolicyError:
                now = self._last_monotonic_ns
        else:
            now = now_monotonic_ns
        snapshot = TerminalSnapshot(
            code=code,
            disclosure_state=disclosure_state,
            terminal_monotonic_ns=now,
            duration_ns=max(0, now - self._started_monotonic_ns),
            counts=self._counts_locked(),
        )
        self._terminal = snapshot
        return snapshot

    def _expiry_code_locked(self, now_monotonic: int, now_wall: int) -> str | None:
        absolute_expired = (
            now_wall >= self._absolute_expiry_ns
            or now_monotonic >= self._absolute_deadline_monotonic_ns
        )
        elapsed_expired = now_monotonic >= self._elapsed_deadline_ns
        if not absolute_expired and not elapsed_expired:
            return None
        if absolute_expired and elapsed_expired:
            return (
                "MP404"
                if self._absolute_window_ns
                <= self._limits["total_wall_seconds"] * NANOSECONDS_PER_SECOND
                else "MP405"
            )
        return "MP404" if absolute_expired else "MP405"

    def _expiry_locked(self) -> TerminalSnapshot | None:
        if self._terminal is not None:
            return None
        try:
            now_monotonic = self._monotonic_locked()
            now_wall = self._wall_locked()
        except PolicyError:
            state = self._disclosure_state_locked()
            return self._terminal_locked(
                "MP405", state, self._last_monotonic_ns
            )
        code = self._expiry_code_locked(now_monotonic, now_wall)
        if code is None:
            return None
        state = self._disclosure_state_locked()
        return self._terminal_locked(code, state, now_monotonic)

    def poll(self) -> TerminalSnapshot | None:
        """Apply an expiry transition once; the caller closes I/O afterwards."""

        with self._lock:
            return self._expiry_locked()

    def _remaining_locked(self) -> tuple[int, int]:
        try:
            now_monotonic = self._monotonic_locked()
            now_wall = self._wall_locked()
        except PolicyError:
            state = self._disclosure_state_locked()
            self._terminal_locked("MP405", state, self._last_monotonic_ns)
            refuse("MP405", "lifecycle.deadline")
        code = self._expiry_code_locked(now_monotonic, now_wall)
        if code is not None:
            state = self._disclosure_state_locked()
            self._terminal_locked(code, state, now_monotonic)
            refuse(code, "lifecycle.deadline")
        remaining = min(
            self._elapsed_deadline_ns - now_monotonic,
            self._absolute_deadline_monotonic_ns - now_monotonic,
            self._absolute_expiry_ns - now_wall,
        )
        if remaining <= 0:
            state = self._disclosure_state_locked()
            self._terminal_locked("MP405", state, now_monotonic)
            refuse("MP405", "lifecycle.deadline")
        return now_monotonic, remaining

    def _stop_and_refuse_locked(self, code: str, field_name: str) -> None:
        state = self._disclosure_state_locked()
        self._terminal_locked(code, state)
        refuse(code, field_name)

    def reserve(
        self,
        *,
        sequence: int,
        request_bytes: int,
        input_text: str,
        job_id: str | None = None,
        jobspec_sha256: str | None = None,
    ) -> Reservation:
        """Atomically reserve all seven disclosure resources."""

        with self._lock:
            if self._terminal is not None:
                refuse(_terminal_refusal_code(self._terminal), "lifecycle.state")
            self._expiry_locked()
            if self._terminal is not None:
                refuse(_terminal_refusal_code(self._terminal), "lifecycle.state")
            if (
                (job_id is not None and job_id != self._job_id)
                or (
                    jobspec_sha256 is not None
                    and jobspec_sha256 != self._jobspec_sha256
                )
                or isinstance(sequence, bool)
                or not isinstance(sequence, int)
                or sequence < 1
                or sequence in self._seen
            ):
                self._stop_and_refuse_locked("MP401", "lifecycle.identity")
            if (
                isinstance(request_bytes, bool)
                or not isinstance(request_bytes, int)
                or request_bytes < 1
            ):
                self._stop_and_refuse_locked("MP402", "lifecycle.request_bytes")
            input_tokens = _count_input(self._profile, input_text)
            now_monotonic, remaining = self._remaining_locked()
            request_limit_failed = (
                self._requests + 1 > self._limits["max_requests"]
                or request_bytes > self._limits["max_request_bytes"]
                or self._request_bytes + request_bytes
                > self._limits["max_total_request_bytes"]
                or input_tokens > self._limits["max_input_tokens"]
                or self._input_tokens + input_tokens
                > self._limits["max_total_input_tokens"]
            )
            if request_limit_failed:
                self._stop_and_refuse_locked("MP402", "lifecycle.request_quota")
            output_reservation = self._limits["max_output_tokens"]
            response_reservation = self._limits["max_response_bytes"]
            response_limit_failed = (
                len(self._active) + 1 > self._limits["max_concurrency"]
                or self._output_tokens
                + self._reserved_output_tokens
                + output_reservation
                > self._limits["max_total_output_tokens"]
                or self._response_bytes
                + self._reserved_response_bytes
                + response_reservation
                > self._limits["max_total_response_bytes"]
            )
            if response_limit_failed:
                self._stop_and_refuse_locked("MP403", "lifecycle.response_quota")
            reservation = Reservation(
                job_id=self._job_id,
                jobspec_sha256=self._jobspec_sha256,
                sequence=sequence,
                request_bytes=request_bytes,
                input_tokens=input_tokens,
                reserved_output_tokens=output_reservation,
                reserved_response_bytes=response_reservation,
                concurrency=len(self._active) + 1,
                admitted_monotonic_ns=now_monotonic,
                remaining_wall_ns=remaining,
                _owner=self._owner,
            )
            self._active[sequence] = reservation
            self._seen.add(sequence)
            self._requests += 1
            self._request_bytes += request_bytes
            self._input_tokens += input_tokens
            self._reserved_output_tokens += output_reservation
            self._reserved_response_bytes += response_reservation
            return reservation

    def _owned_locked(self, reservation: Reservation) -> bool:
        return (
            isinstance(reservation, Reservation)
            and reservation._owner is self._owner
            and self._active.get(reservation.sequence) is reservation
        )

    def mark_disclosed(self, reservation: Reservation) -> int:
        """Recheck expiry at publication and return the current timeout."""

        with self._lock:
            if not self._owned_locked(reservation):
                refuse("MP401", "lifecycle.reservation")
            if self._terminal is not None:
                code = _terminal_refusal_code(self._terminal)
                self._release_locked(reservation, rollback=False)
                refuse(code, "lifecycle.reservation")
            self._expiry_locked()
            if self._terminal is not None:
                code = self._terminal.code
                self._release_locked(reservation, rollback=False)
                refuse(code, "lifecycle.deadline")
            try:
                _now, remaining = self._remaining_locked()
            except PolicyError:
                if self._owned_locked(reservation):
                    self._release_locked(reservation, rollback=False)
                raise
            self._disclosed.add(reservation.sequence)
            return min(reservation.remaining_wall_ns, remaining)

    def provider_handoff(self, reservation: Reservation) -> int:
        """Recheck expiry at the actual exchange handoff and return its timeout."""

        with self._lock:
            if (
                not self._owned_locked(reservation)
                or reservation.sequence not in self._disclosed
            ):
                refuse("MP401", "lifecycle.reservation")
            if self._terminal is not None:
                refuse(
                    _terminal_refusal_code(self._terminal),
                    "lifecycle.provider_handoff",
                )
            _now, remaining = self._remaining_locked()
            self._provider_disclosed = True
            return min(reservation.remaining_wall_ns, remaining)

    def _release_locked(self, reservation: Reservation, *, rollback: bool) -> None:
        del self._active[reservation.sequence]
        self._reserved_output_tokens -= reservation.reserved_output_tokens
        self._reserved_response_bytes -= reservation.reserved_response_bytes
        if rollback:
            self._seen.remove(reservation.sequence)
            self._requests -= 1
            self._request_bytes -= reservation.request_bytes
            self._input_tokens -= reservation.input_tokens

    def rollback(self, reservation: Reservation) -> None:
        """Release a reservation only while no provider disclosure occurred."""

        with self._lock:
            if (
                not self._owned_locked(reservation)
                or reservation.sequence in self._disclosed
            ):
                refuse("MP401", "lifecycle.rollback")
            self._release_locked(reservation, rollback=True)

    def complete(self, reservation: Reservation, event: ProviderEvent) -> None:
        """Commit exact provider usage or discard it after a terminal race."""

        with self._lock:
            if not self._owned_locked(reservation):
                refuse("MP401", "lifecycle.reservation")
            if self._terminal is not None:
                code = self._terminal.code
                self._release_locked(reservation, rollback=False)
                refuse(code, "lifecycle.late_response")
            if (
                not isinstance(event, ProviderEvent)
                or event.request_bytes != reservation.request_bytes
                or event.input_tokens != reservation.input_tokens
                or isinstance(event.output_tokens, bool)
                or not isinstance(event.output_tokens, int)
                or event.output_tokens < 0
                or event.output_tokens > reservation.reserved_output_tokens
                or isinstance(event.response_bytes, bool)
                or not isinstance(event.response_bytes, int)
                or event.response_bytes < 0
                or event.response_bytes > reservation.reserved_response_bytes
                or event.code != "MP000"
                or event.disclosure_state != "provider-only"
            ):
                self._terminal_locked("MP409", "provider-only")
                self._release_locked(reservation, rollback=False)
                refuse("MP409", "lifecycle.provider_usage")
            self._provider_disclosed = True
            self._output_tokens += event.output_tokens
            self._response_bytes += event.response_bytes
            self._expiry_locked()
            if self._terminal is not None:
                code = self._terminal.code
                self._release_locked(reservation, rollback=False)
                refuse(code, "lifecycle.late_response")
            self._release_locked(reservation, rollback=False)

    def fail(
        self,
        reservation: Reservation,
        code: str,
        event: ProviderEvent | None = None,
    ) -> TerminalSnapshot:
        with self._lock:
            if not self._owned_locked(reservation):
                refuse("MP401", "lifecycle.reservation")
            disclosure_state = "provider-only"
            if event is not None:
                if (
                    not isinstance(event, ProviderEvent)
                    or event.profile != self._profile.identifier
                    or event.code != code
                    or event.disclosure_state not in {"not-read", "provider-only"}
                    or isinstance(event.request_bytes, bool)
                    or not isinstance(event.request_bytes, int)
                    or event.request_bytes not in {0, reservation.request_bytes}
                    or isinstance(event.response_bytes, bool)
                    or not isinstance(event.response_bytes, int)
                    or event.response_bytes < 0
                    or event.response_bytes > reservation.reserved_response_bytes + 1
                    or isinstance(event.input_tokens, bool)
                    or not isinstance(event.input_tokens, int)
                    or event.input_tokens not in {0, reservation.input_tokens}
                    or isinstance(event.output_tokens, bool)
                    or not isinstance(event.output_tokens, int)
                    or event.output_tokens < 0
                    or event.output_tokens > reservation.reserved_output_tokens
                    or isinstance(event.duration_ns, bool)
                    or not isinstance(event.duration_ns, int)
                    or event.duration_ns < 0
                ):
                    snapshot = self._terminal_locked("MP409", "provider-only")
                    self._release_locked(reservation, rollback=False)
                    return snapshot
                if event.disclosure_state == "provider-only":
                    self._provider_disclosed = True
                disclosure_state = (
                    "provider-only"
                    if self._provider_disclosed
                    else event.disclosure_state
                )
                if (
                    self._terminal is None
                    and event.disclosure_state == "provider-only"
                ):
                    self._response_bytes += event.response_bytes
            if self._terminal is None:
                snapshot = self._expiry_locked()
                if snapshot is None:
                    snapshot = self._terminal_locked(code, disclosure_state)
            else:
                snapshot = self._terminal
            self._release_locked(reservation, rollback=False)
            return snapshot

    def stop(self, code: str) -> TerminalSnapshot:
        with self._lock:
            if not isinstance(code, str) or _OUTCOME_CODE.fullmatch(code) is None:
                refuse("MP401", "lifecycle.outcome")
            state = self._disclosure_state_locked()
            return self._terminal_locked(code, state)

    def cancel(self) -> TerminalSnapshot:
        with self._lock:
            expired = self._expiry_locked()
            if expired is not None:
                return expired
            state = self._disclosure_state_locked()
            return self._terminal_locked("MP406", state)

    def finish(self) -> TerminalSnapshot:
        with self._lock:
            if self._terminal is not None:
                return self._terminal
            self._expiry_locked()
            if self._terminal is not None:
                return self._terminal
            if self._active:
                self._stop_and_refuse_locked("MP401", "lifecycle.concurrency")
            state = self._disclosure_state_locked()
            return self._terminal_locked("MP000", state)


class ModelProxyRuntime:
    """Bind provider I/O, lifecycle state, and one exclusive receipt sink."""

    def __init__(
        self,
        policy: CompiledPolicy,
        connector: HTTPSConnector,
        receipt_path: str | Path,
        *,
        credential_source=None,
        monotonic_clock: Clock = time.monotonic_ns,
        wall_clock: Clock = time.time_ns,
        io_closer: Callable[[], None] = lambda: None,
    ):
        if not callable(io_closer):
            refuse("MP400", "lifecycle.io_closer")
        self._controller = LifecycleController(
            policy,
            monotonic_clock=monotonic_clock,
            wall_clock=wall_clock,
        )
        effective_policy = self._controller.policy
        self._provider = ProviderSession(
            effective_policy,
            connector,
            **(
                {}
                if credential_source is None
                else {"credential_source": credential_source}
            ),
        )
        self._io_closer = io_closer
        try:
            self._sink = ReceiptSink(
                receipt_path,
                max_record_bytes=self._controller.limits["max_receipt_bytes"],
                max_records=self._controller.limits["max_receipts"],
            )
        except PolicyError:
            self._controller.stop("MP407")
            try:
                self._provider.close()
            except Exception:
                pass
            try:
                self._io_closer()
            except Exception:
                pass
            raise
        self._publication_lock = threading.Lock()
        self._provider_lock = threading.Lock()
        self._provider_turn_condition = threading.Condition()
        self._pending_provider_turns: set[int] = set()
        self._terminal_lock = threading.Lock()
        self._terminal_finalized = False
        self._terminal_receipt_failed = False
        provider_fields = effective_policy.document["provider"]
        self._versions = MappingProxyType(
            {
                "policy_schema": effective_policy.document["schema"],
                "compiler": effective_policy.document["compiler"],
                "token_counter": provider_fields["token_counter"],
                "receipt_schema": RECEIPT_SCHEMA,
            }
        )
        try:
            self._sink.write_activation(
                job_id=self._controller.job_id,
                jobspec_sha256=self._controller.jobspec_sha256,
                policy_sha256=self._controller.policy_sha256,
                profile=self._controller.profile.identifier,
                versions=self._versions,
                activated_monotonic_ns=self._controller.started_monotonic_ns,
                absolute_expiry_unix_ns=self._controller.absolute_expiry_ns,
                elapsed_deadline_ns=self._controller.elapsed_deadline_ns,
            )
        except PolicyError:
            self._controller.stop("MP407")
            try:
                self._provider.close()
            except Exception:
                pass
            try:
                self._sink.close()
            except (OSError, PolicyError):
                pass
            try:
                self._io_closer()
            except Exception:
                pass
            raise

    @property
    def terminal(self) -> TerminalSnapshot | None:
        return self._controller.terminal

    @property
    def provider_events(self) -> tuple[ProviderEvent, ...]:
        return self._provider.events

    @property
    def framing_events(self):
        return self._provider.framing_events

    @property
    def receipt_count(self) -> int:
        return self._sink.records

    def activate(self) -> None:
        with self._publication_lock:
            try:
                self._controller.activate()
            except PolicyError as error:
                snapshot = self._controller.stop(error.code)
                self._finalize_terminal(snapshot)
                raise

    def operator_text(self) -> str:
        return render_operator_text(self._controller.policy)

    def _finalize_terminal(self, snapshot: TerminalSnapshot) -> None:
        with self._provider_turn_condition:
            self._provider_turn_condition.notify_all()
        with self._terminal_lock:
            if self._terminal_finalized:
                if self._terminal_receipt_failed:
                    refuse("MP407", "receipt.terminal")
                return
            cleanup_failed = False
            try:
                self._provider.close()
            except Exception:
                cleanup_failed = True
            try:
                self._io_closer()
            except Exception:
                cleanup_failed = True
            receipt_failed = self._terminal_receipt_failed or cleanup_failed
            if not cleanup_failed:
                try:
                    self._sink.write_terminal(
                        job_id=self._controller.job_id,
                        jobspec_sha256=self._controller.jobspec_sha256,
                        policy_sha256=self._controller.policy_sha256,
                        profile=self._controller.profile.identifier,
                        versions=self._versions,
                        counts=snapshot.counts,
                        terminal_monotonic_ns=snapshot.terminal_monotonic_ns,
                        duration_ns=snapshot.duration_ns,
                        disclosure_state=snapshot.disclosure_state,
                        outcome_code=snapshot.code,
                    )
                except PolicyError:
                    receipt_failed = True
            try:
                self._sink.close()
            except (OSError, PolicyError):
                receipt_failed = True
            self._terminal_receipt_failed = receipt_failed
            self._terminal_finalized = True
            if receipt_failed:
                refuse("MP407", "receipt.terminal")

    def _register_provider_turn(self, reservation: Reservation) -> None:
        with self._provider_turn_condition:
            if reservation.sequence in self._pending_provider_turns:
                refuse("MP401", "lifecycle.provider_turn")
            self._pending_provider_turns.add(reservation.sequence)
            self._provider_turn_condition.notify_all()

    def _await_provider_turn(self, reservation: Reservation) -> None:
        with self._provider_turn_condition:
            while reservation.sequence in self._pending_provider_turns:
                if self._controller.terminal is not None:
                    return
                if reservation.sequence == min(self._pending_provider_turns):
                    return
                self._provider_turn_condition.wait()
            refuse("MP401", "lifecycle.provider_turn")

    def _release_provider_turn(self, reservation: Reservation) -> None:
        with self._provider_turn_condition:
            self._pending_provider_turns.discard(reservation.sequence)
            self._provider_turn_condition.notify_all()

    def _active_locked(self) -> None:
        snapshot = self._controller.poll()
        if snapshot is not None:
            self._finalize_terminal(snapshot)
        terminal = self._controller.terminal
        if terminal is not None:
            if self._terminal_receipt_failed:
                refuse("MP407", "receipt.terminal")
            refuse(_terminal_refusal_code(terminal), "lifecycle.state")

    def poll(self) -> str | None:
        with self._publication_lock:
            snapshot = self._controller.poll()
            if snapshot is not None:
                self._finalize_terminal(snapshot)
                return snapshot.code
            terminal = self._controller.terminal
            if terminal is not None and self._terminal_receipt_failed:
                refuse("MP407", "receipt.terminal")
            return None if terminal is None else terminal.code

    def feed(self, data: bytes) -> tuple[TextRequest, ...]:
        with self._provider_lock:
            with self._publication_lock:
                self._active_locked()
                try:
                    return self._provider.feed(data)
                except PolicyError as error:
                    snapshot = self._controller.stop(error.code)
                    self._finalize_terminal(snapshot)
                    raise

    def finish_input(self) -> None:
        with self._provider_lock:
            with self._publication_lock:
                self._active_locked()
                try:
                    self._provider.finish()
                except PolicyError as error:
                    snapshot = self._controller.stop(error.code)
                    self._finalize_terminal(snapshot)
                    raise

    def generate(self, request: TextRequest, *, final: bool = False) -> bytes:
        """Reserve, receipt, disclose, and publish one admitted response."""

        with self._publication_lock:
            self._active_locked()
            try:
                body = provider_request_bytes(self._controller.profile, request)
                reservation = self._controller.reserve(
                    sequence=request.sequence,
                    request_bytes=len(body),
                    input_text=request.input_text,
                    job_id=self._controller.job_id,
                    jobspec_sha256=self._controller.jobspec_sha256,
                )
            except PolicyError as error:
                snapshot = self._controller.terminal
                if snapshot is None:
                    snapshot = self._controller.stop(error.code)
                self._finalize_terminal(snapshot)
                raise
            try:
                self._sink.write_request(
                    job_id=self._controller.job_id,
                    jobspec_sha256=self._controller.jobspec_sha256,
                    policy_sha256=self._controller.policy_sha256,
                    profile=self._controller.profile.identifier,
                    versions=self._versions,
                    sequence=reservation.sequence,
                    counts={
                        "request_bytes": reservation.request_bytes,
                        "input_tokens": reservation.input_tokens,
                        "reserved_output_tokens": reservation.reserved_output_tokens,
                        "reserved_response_bytes": reservation.reserved_response_bytes,
                        "concurrency": reservation.concurrency,
                    },
                    admitted_monotonic_ns=reservation.admitted_monotonic_ns,
                    remaining_wall_ns=reservation.remaining_wall_ns,
                )
            except PolicyError:
                self._controller.rollback(reservation)
                snapshot = self._controller.stop("MP407")
                self._finalize_terminal(snapshot)
                refuse("MP407", "receipt.request")
            self._register_provider_turn(reservation)
        try:
            self._await_provider_turn(reservation)
            with self._provider_lock:
                with self._publication_lock:
                    if final:
                        try:
                            self._provider.prepare_terminal_input(request)
                        except PolicyError as error:
                            events = self._provider.events
                            event = events[-1] if events else None
                            snapshot = self._controller.fail(
                                reservation, error.code, event
                            )
                            self._finalize_terminal(snapshot)
                            if snapshot.code != error.code:
                                refuse(snapshot.code, "lifecycle.state")
                            raise
                    try:
                        disclosure_timeout_ns = self._controller.mark_disclosed(
                            reservation
                        )
                    except PolicyError:
                        terminal = self._controller.terminal
                        if terminal is not None:
                            self._finalize_terminal(terminal)
                        raise

                try:
                    guest_response = self._provider.generate(
                        request,
                        timeout_ns=disclosure_timeout_ns,
                        on_provider_handoff=lambda: (
                            self._controller.provider_handoff(reservation)
                            / NANOSECONDS_PER_SECOND
                        ),
                    )
                except PolicyError as error:
                    with self._publication_lock:
                        events = self._provider.events
                        event = events[-1] if events else None
                        snapshot = self._controller.fail(
                            reservation, error.code, event
                        )
                        self._finalize_terminal(snapshot)
                        if snapshot.code != error.code:
                            refuse(snapshot.code, "lifecycle.late_response")
                    raise

                event = self._provider.events[-1]
                with self._publication_lock:
                    try:
                        self._controller.complete(reservation, event)
                    except PolicyError:
                        terminal = self._controller.terminal
                        if terminal is not None:
                            self._finalize_terminal(terminal)
                        raise
                    if final:
                        try:
                            self._provider.require_completion_ready()
                        except PolicyError as error:
                            snapshot = self._controller.stop(error.code)
                            self._finalize_terminal(snapshot)
                            raise
                        try:
                            snapshot = self._controller.finish()
                        except PolicyError:
                            terminal = self._controller.terminal
                            if terminal is not None:
                                self._finalize_terminal(terminal)
                            raise
                        self._finalize_terminal(snapshot)
                        if snapshot.code != "MP000":
                            refuse(snapshot.code, "lifecycle.late_response")
                    else:
                        self._active_locked()
                    return guest_response
        finally:
            self._release_provider_turn(reservation)

    def cancel(self) -> None:
        with self._publication_lock:
            snapshot = self._controller.cancel()
            self._finalize_terminal(snapshot)

    def complete_job(self) -> None:
        with self._publication_lock:
            self._active_locked()
            try:
                self._provider.prepare_terminal_input()
                self._provider.require_completion_ready()
                snapshot = self._controller.finish()
            except PolicyError as error:
                terminal = self._controller.terminal
                if terminal is None:
                    terminal = self._controller.stop(error.code)
                self._finalize_terminal(terminal)
                raise
            self._finalize_terminal(snapshot)


class _StaticClock:
    def __init__(self, value: int):
        self.value = value

    def __call__(self) -> int:
        return self.value


class _DemoResponse:
    def __init__(self, body: bytes, address: str):
        self.status = 200
        self.headers = (
            ("Content-Length", str(len(body))),
            ("Content-Type", "application/json"),
        )
        self.peer_address = address
        self._body = body
        self._position = 0
        self.closed = False

    def read(self, size: int) -> bytes:
        chunk = self._body[self._position : self._position + size]
        self._position += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


def _request_frame(input_text: str) -> bytes:
    payload = canonical_json(
        {"schema": REQUEST_SCHEMA, "operation": TEXT_OPERATION, "input": input_text}
    )
    return struct.pack(">I", len(payload)) + payload


def _manifest_object(
    value: object, fields: frozenset[str], field_name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or frozenset(value) != fields:
        refuse("MP410", field_name)
    return value


def check_lifecycle_manifest(path: str | Path) -> LifecycleManifestResult:
    """Exercise lifecycle vectors with injected clocks, transport, and credentials."""

    try:
        manifest_path = Path(path)
        parsed = parse_json_bytes(
            read_bounded_file(manifest_path, MAX_LIFECYCLE_MANIFEST_BYTES),
            max_bytes=MAX_LIFECYCLE_MANIFEST_BYTES,
            max_members=MAX_JSON_MEMBERS,
        )
    except PolicyError:
        refuse("MP410", "lifecycle.manifest")
    except (OSError, TypeError, ValueError):
        refuse("MP410", "lifecycle.manifest.path")
    manifest = _manifest_object(parsed, _MANIFEST_FIELDS, "lifecycle.manifest")
    if (
        manifest["schema"] != LIFECYCLE_MANIFEST_SCHEMA
        or manifest["accepted_job"] != "accepted-job.json"
    ):
        refuse("MP410", "lifecycle.manifest")
    cases = manifest["cases"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= 16:
        refuse("MP410", "lifecycle.manifest.cases")
    policy = compile_policy_file(manifest_path.parent / "accepted-job.json")
    profile = resolve_profile(policy.profile)
    seen: set[str] = set()
    request_count = 0
    receipt_count = 0
    for raw_case in cases:
        case = _manifest_object(raw_case, _CASE_FIELDS, "lifecycle.manifest.case")
        identifier = case["id"]
        input_text = case["input"]
        output_text = case["output"]
        monotonic_start = case["monotonic_start_ns"]
        wall_start_seconds = case["wall_start_unix_seconds"]
        if (
            not isinstance(identifier, str)
            or _CASE_ID.fullmatch(identifier) is None
            or identifier in seen
            or not isinstance(input_text, str)
            or not input_text
            or not isinstance(output_text, str)
            or not output_text
            or isinstance(monotonic_start, bool)
            or not isinstance(monotonic_start, int)
            or monotonic_start < 0
            or isinstance(wall_start_seconds, bool)
            or not isinstance(wall_start_seconds, int)
            or wall_start_seconds < 0
        ):
            refuse("MP410", "lifecycle.manifest.case")
        wall_start = wall_start_seconds * NANOSECONDS_PER_SECOND
        seen.add(identifier)
        credential = secrets.token_urlsafe(32)
        address = "8.8.8.8"
        response_body = canonical_json(
            {
                "schema": profile.provider_response_schema,
                "output": output_text,
                "usage": {
                    "input_tokens": len(input_text),
                    "output_tokens": len(output_text),
                },
            }
        )
        responses: list[_DemoResponse] = []

        def exchange(
            request: HTTPSRequest, _context, _timeout: float
        ) -> HTTPSResponse:
            mapped = parse_json_bytes(request.body, max_bytes=65_536)
            if (
                not isinstance(mapped, dict)
                or mapped.get("input") != input_text
                or request.header("Authorization") != f"Bearer {credential}"
            ):
                refuse("MP410", "lifecycle.manifest.exchange")
            response = _DemoResponse(response_body, address)
            responses.append(response)
            return response

        lifecycle_clock = _StaticClock(monotonic_start)
        wall_clock = _StaticClock(wall_start)
        connector = HTTPSConnector(
            profile,
            resolver=lambda _hostname, _port: (address,),
            exchange=exchange,
            clock=iter((monotonic_start, monotonic_start + 1_000_000)).__next__,
        )
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "job-receipts.jsonl"
            runtime = ModelProxyRuntime(
                policy,
                connector,
                receipt_path,
                credential_source=lambda _name: credential,
                monotonic_clock=lifecycle_clock,
                wall_clock=wall_clock,
            )
            admitted = runtime.feed(_request_frame(input_text))
            runtime.finish_input()
            if len(admitted) != 1:
                refuse("MP410", "lifecycle.manifest.admission")
            guest = runtime.generate(admitted[0], final=True)
            expected_payload = canonical_json(
                {
                    "schema": RESPONSE_SCHEMA,
                    "sequence": 1,
                    "output": output_text,
                }
            )
            expected_guest = struct.pack(">I", len(expected_payload)) + expected_payload
            receipt_bytes = read_bounded_file(
                receipt_path,
                policy.document["limits"]["max_receipts"] * 4_097,
            )
            lines = receipt_bytes.splitlines()
            if (
                guest != expected_guest
                or len(lines) != 3
                or any(len(line) > 4_096 for line in lines)
                or any(not response.closed for response in responses)
                or credential.encode("ascii") in receipt_bytes
                or input_text.encode("utf-8") in receipt_bytes
                or output_text.encode("utf-8") in receipt_bytes
            ):
                refuse("MP410", "lifecycle.manifest.result")
            records = [parse_json_bytes(line, max_bytes=4_096) for line in lines]
            if [record.get("event") for record in records] != [
                "activation",
                "request",
                "terminal",
            ]:
                refuse("MP410", "lifecycle.manifest.receipts")
            operator_text = runtime.operator_text()
            if (
                profile.identifier not in operator_text
                or profile.origin_family not in operator_text
                or "do not prove" not in operator_text
            ):
                refuse("MP410", "lifecycle.manifest.operator")
            receipt_count += len(lines)
        request_count += 1
    return LifecycleManifestResult(
        cases=len(cases),
        requests=request_count,
        receipts=receipt_count,
        policy_sha256=policy.policy_sha256,
    )
