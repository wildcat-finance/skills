"""One admitted, non-retried GitHub issue publication lifecycle."""

from __future__ import annotations

from collections.abc import Callable
import math
import time

from .canonical import sha256_bytes
from .errors import PublisherError, refuse
from .policy import ImprimaturRunner, admit_request
from .receipts import ReceiptSink, RetainedEvents, result_bytes, result_document
from .signer import SIGN_TIMEOUT_SECONDS, Signer, build_app_jwt
from .transport import (
    CREATE_TIMEOUT_SECONDS,
    READBACK_TIMEOUT_SECONDS,
    TOKEN_TIMEOUT_SECONDS,
    IssueRecord,
    PinnedGitHubTransport,
    create_issue,
    exchange_installation_token,
    read_issue,
)


TOTAL_TIMEOUT_SECONDS = 60.0


class _Budget:
    def __init__(self, clock: Callable[[], float]):
        self._clock = clock
        self._started = self._now()

    def _now(self) -> float:
        try:
            raw = self._clock()
            if isinstance(raw, bool):
                refuse("GIP330", "deadline.clock")
            value = float(raw)
        except PublisherError:
            raise
        except Exception as exc:
            raise PublisherError("GIP330", "deadline.clock") from exc
        if value < 0 or value != value or value in (float("inf"), float("-inf")):
            refuse("GIP330", "deadline.clock")
        return value

    def begin(self, ceiling: float) -> tuple[float, float]:
        now = self._now()
        remaining = TOTAL_TIMEOUT_SECONDS - (now - self._started)
        if remaining <= 0:
            refuse("GIP330", "deadline.total")
        return now, min(ceiling, remaining)

    def finish(self, started: float, ceiling: float) -> None:
        now = self._now()
        if now - started > ceiling or now - self._started > TOTAL_TIMEOUT_SECONDS:
            refuse("GIP330", "deadline.stage")

    def elapsed_ms(self) -> int:
        elapsed = max(0.0, self._now() - self._started)
        if elapsed > TOTAL_TIMEOUT_SECONDS:
            refuse("GIP330", "deadline.total")
        return int(elapsed * 1_000)


def _empty_counts() -> dict[str, int]:
    return {
        "signer_attempts": 0,
        "token_attempts": 0,
        "post_attempts": 0,
        "authenticated_readbacks": 0,
        "anonymous_readbacks": 0,
    }


def _error_with_attempts(
    error: PublisherError,
    counts: dict[str, int],
) -> PublisherError:
    """Retain mutation-relevant counts when a result cannot be built."""

    return PublisherError(
        error.code,
        error.field,
        mint_attempts=counts["token_attempts"],
        post_attempts=counts["post_attempts"],
    )


class PublisherRuntime:
    """Keep credential authority inside one admitted service operation."""

    def __init__(
        self,
        *,
        signer: Signer,
        transport: PinnedGitHubTransport,
        receipt_sink: ReceiptSink,
        events: RetainedEvents | None = None,
        wall_clock: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
        imprimatur_runner: ImprimaturRunner | None = None,
    ):
        if not all(
            callable(value)
            for value in (
                getattr(signer, "sign", None),
                getattr(signer, "close", None),
                getattr(transport, "request", None),
                getattr(transport, "close", None),
                getattr(receipt_sink, "write", None),
                getattr(receipt_sink, "close", None),
                wall_clock,
                monotonic,
            )
        ):
            refuse("GIP500", "runtime.components")
        self._signer = signer
        self._transport = transport
        self._receipt_sink = receipt_sink
        self._events = RetainedEvents() if events is None else events
        self._wall_clock = wall_clock
        self._monotonic = monotonic
        self._imprimatur_runner = imprimatur_runner

    @property
    def events(self) -> tuple[dict[str, object], ...]:
        return self._events.documents

    def _close_components(self) -> bool:
        complete = True
        for component in (self._signer, self._transport):
            try:
                component.close()
            except Exception:
                complete = False
        return complete

    def _close_before_result(self) -> None:
        self._close_components()
        try:
            self._receipt_sink.close()
        except Exception:
            pass

    def _wall_seconds(self) -> int:
        try:
            raw = self._wall_clock()
            if isinstance(raw, bool):
                refuse("GIP330", "deadline.clock")
            value = float(raw)
        except PublisherError:
            raise
        except Exception as exc:
            raise PublisherError("GIP330", "deadline.clock") from exc
        if not math.isfinite(value) or value < 1:
            refuse("GIP330", "deadline.clock")
        return int(value)

    def _emit(
        self,
        budget: _Budget,
        correlation: str,
        stage: str,
        outcome: str,
        code: str,
        counts: dict[str, int],
    ) -> None:
        self._events.emit(
            correlation_sha256=correlation,
            stage=stage,
            outcome=outcome,
            code=code,
            counts=counts,
            elapsed_ms=budget.elapsed_ms(),
        )

    def _emit_or_close(
        self,
        budget: _Budget,
        correlation: str,
        stage: str,
        outcome: str,
        code: str,
        counts: dict[str, int],
    ) -> None:
        """Close every component if a terminal event cannot be retained."""

        try:
            self._emit(budget, correlation, stage, outcome, code, counts)
        except BaseException as exc:
            self._close_before_result()
            if isinstance(exc, PublisherError):
                raise _error_with_attempts(exc, counts) from exc
            if isinstance(exc, Exception):
                error = PublisherError("GIP500", "runtime.events")
                raise _error_with_attempts(error, counts) from exc
            raise

    def publish(self, raw: bytes) -> dict[str, object]:
        """Attempt one admitted create and return one content-free result."""

        if not isinstance(raw, bytes):
            refuse("GIP500", "runtime.request")
        accepted_raw = bytes(raw)
        counts = _empty_counts()
        try:
            budget = _Budget(self._monotonic)
        except PublisherError:
            self._close_before_result()
            raise
        try:
            admission = admit_request(
                accepted_raw,
                imprimatur_runner=self._imprimatur_runner,
            )
        except PublisherError:
            self._close_before_result()
            raise

        correlation = sha256_bytes(
            b"github-issue-publisher/v1\x00" + admission.request_sha256.encode("ascii")
        )
        try:
            self._emit(
                budget,
                correlation,
                "admission",
                "accepted",
                "GIP000",
                counts,
            )
        except PublisherError:
            self._close_before_result()
            raise
        except Exception as exc:
            self._close_before_result()
            raise PublisherError("GIP500", "runtime.events") from exc
        title = admission.final_title
        body = admission.final_body
        labels = admission.labels
        jwt: str | None = None
        token: str | None = None
        issue: IssueRecord | None = None
        outcome = "published"
        code = "GIP000"
        readback = "not-run"
        active_stage = "signer"

        try:
            started, timeout = budget.begin(SIGN_TIMEOUT_SECONDS)
            now = self._wall_seconds()
            counts["signer_attempts"] += 1
            jwt = build_app_jwt(
                now,
                self._signer,
                timeout_seconds=timeout,
            )
            budget.finish(started, SIGN_TIMEOUT_SECONDS)
            self._emit(budget, correlation, "signer", "accepted", "GIP000", counts)

            active_stage = "token"
            started, timeout = budget.begin(TOKEN_TIMEOUT_SECONDS)
            now = self._wall_seconds()
            counts["token_attempts"] += 1
            grant = exchange_installation_token(
                jwt,
                self._transport,
                now=now,
                timeout_seconds=timeout,
            )
            token = grant.token
            budget.finish(started, TOKEN_TIMEOUT_SECONDS)
            self._emit(budget, correlation, "token", "accepted", "GIP000", counts)

            active_stage = "create"
            started, timeout = budget.begin(CREATE_TIMEOUT_SECONDS)
            counts["post_attempts"] += 1
            try:
                issue = create_issue(
                    token,
                    title=title,
                    body=body,
                    labels=labels,
                    transport=self._transport,
                    timeout_seconds=timeout,
                )
            except PublisherError as exc:
                outcome = "create-indeterminate"
                code = exc.code
                self._emit(
                    budget,
                    correlation,
                    "create",
                    "indeterminate",
                    exc.code,
                    counts,
                )
            else:
                budget.finish(started, CREATE_TIMEOUT_SECONDS)
                self._emit(budget, correlation, "create", "confirmed", "GIP000", counts)

            if issue is not None:
                try:
                    active_stage = "readback-authenticated"
                    started, timeout = budget.begin(READBACK_TIMEOUT_SECONDS)
                    counts["authenticated_readbacks"] += 1
                    read_issue(
                        issue,
                        title=title,
                        body=body,
                        token=token,
                        transport=self._transport,
                        timeout_seconds=timeout,
                    )
                    budget.finish(started, READBACK_TIMEOUT_SECONDS)
                    self._emit(
                        budget,
                        correlation,
                        "readback-authenticated",
                        "confirmed",
                        "GIP000",
                        counts,
                    )

                    active_stage = "readback-anonymous"
                    started, timeout = budget.begin(READBACK_TIMEOUT_SECONDS)
                    counts["anonymous_readbacks"] += 1
                    read_issue(
                        issue,
                        title=title,
                        body=body,
                        token=None,
                        transport=self._transport,
                        timeout_seconds=timeout,
                    )
                    budget.finish(started, READBACK_TIMEOUT_SECONDS)
                    self._emit(
                        budget,
                        correlation,
                        "readback-anonymous",
                        "confirmed",
                        "GIP000",
                        counts,
                    )
                    readback = "matched"
                except PublisherError as exc:
                    outcome = "created-but-unverified"
                    code = exc.code
                    readback = "failed"
                    stage = (
                        "readback-authenticated"
                        if counts["anonymous_readbacks"] == 0
                        else "readback-anonymous"
                    )
                    self._emit(budget, correlation, stage, "refused", exc.code, counts)
        except PublisherError as exc:
            if issue is not None:
                outcome = "created-but-unverified"
                readback = "failed"
            elif counts["post_attempts"]:
                outcome = "create-indeterminate"
            else:
                outcome = "refused"
            code = exc.code
            self._emit_or_close(
                budget,
                correlation,
                active_stage,
                "indeterminate" if outcome == "create-indeterminate" else "refused",
                exc.code,
                counts,
            )
        except Exception:
            if issue is not None:
                outcome = "created-but-unverified"
                readback = "failed"
            elif counts["post_attempts"]:
                outcome = "create-indeterminate"
            else:
                outcome = "refused"
            code = "GIP500"
            self._emit_or_close(
                budget,
                correlation,
                active_stage,
                "indeterminate" if outcome == "create-indeterminate" else "refused",
                code,
                counts,
            )

        jwt = None
        token = None
        grant = None
        cleanup_complete = self._close_components()
        if not cleanup_complete:
            if outcome not in {"create-indeterminate", "created-but-unverified"}:
                outcome = "cleanup-failed"
            code = "GIP501"
        self._emit_or_close(
            budget,
            correlation,
            "cleanup",
            "accepted" if cleanup_complete else "refused",
            "GIP000" if cleanup_complete else "GIP501",
            counts,
        )
        document = result_document(
            outcome=outcome,
            request_sha256=admission.request_sha256,
            final_sha256=admission.final_sha256,
            correlation_sha256=correlation,
            issue_number=None if issue is None else issue.number,
            issue_url=None if issue is None else issue.url,
            counts=counts,
            readback=readback,
            cleanup_complete=cleanup_complete,
            code=code,
        )
        payload = result_bytes(document)
        try:
            self._receipt_sink.write(payload)
            self._receipt_sink.close()
            self._emit(budget, correlation, "receipt", "accepted", "GIP000", counts)
        except Exception:
            try:
                self._receipt_sink.close()
            except Exception:
                pass
            self._emit_or_close(
                budget,
                correlation,
                "receipt",
                "refused",
                "GIP402",
                counts,
            )
            document = result_document(
                outcome=(
                    outcome
                    if outcome in {"create-indeterminate", "created-but-unverified"}
                    else "receipt-failed"
                ),
                request_sha256=admission.request_sha256,
                final_sha256=admission.final_sha256,
                correlation_sha256=correlation,
                issue_number=None if issue is None else issue.number,
                issue_url=None if issue is None else issue.url,
                counts=counts,
                readback=readback,
                cleanup_complete=False,
                code="GIP402",
            )
        return document
