"""Runtime request, time and byte limits for capture."""

from __future__ import annotations

import time
from typing import Any, Callable

from .errors import ResourceLimitError


DEFAULT_MAX_ELAPSED_SECONDS = 300
MAX_RECEIPT_FIELDS = 64
MAX_RECEIPT_LOG_FIELDS = 32


class CaptureLimits:
    def __init__(
        self,
        values: dict[str, Any],
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_requests = values["max_requests"]
        self.max_component_bytes = values["max_component_bytes"]
        self.max_total_bytes = values["max_total_bytes"]
        self.max_elapsed_seconds = values.get(
            "max_elapsed_seconds", DEFAULT_MAX_ELAPSED_SECONDS
        )
        self._clock = clock
        self._started = clock()
        self.requests = 0
        self.response_bytes = 0

    def before_request(self, count: int = 1) -> None:
        self.check_time()
        if count < 1:
            raise ResourceLimitError("RPC request count must be positive")
        if self.requests + count > self.max_requests:
            raise ResourceLimitError(
                f"capture exceeds the plan limit of {self.max_requests} RPC requests"
            )
        self.requests += count

    def response_read_limit(self) -> int:
        self.check_time()
        remaining = self.max_total_bytes - self.response_bytes
        if remaining <= 0:
            raise ResourceLimitError(
                f"capture exceeds the plan limit of {self.max_total_bytes} response bytes"
            )
        return min(self.max_component_bytes, remaining)

    def after_response(self, size: int) -> None:
        if size > self.max_component_bytes:
            raise ResourceLimitError(
                f"RPC response exceeds the plan limit of {self.max_component_bytes} bytes"
            )
        if self.response_bytes + size > self.max_total_bytes:
            raise ResourceLimitError(
                f"capture exceeds the plan limit of {self.max_total_bytes} response bytes"
            )
        self.response_bytes += size
        self.check_time()

    def remaining_seconds(self) -> float:
        remaining = self.max_elapsed_seconds - (self._clock() - self._started)
        if remaining <= 0:
            raise ResourceLimitError(
                f"capture exceeds the plan limit of {self.max_elapsed_seconds} seconds"
            )
        return remaining

    def check_time(self) -> None:
        self.remaining_seconds()

    def check_allocation(self, count: int, *, maximum: int, label: str) -> None:
        """Refuse a hostile collection before deriving another collection from it."""

        self.check_time()
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ResourceLimitError(f"{label} is not a valid count")
        if count > maximum:
            raise ResourceLimitError(f"{label} exceeds {maximum}")

    def check_component_bytes(self, size: int, *, label: str) -> None:
        self.check_time()
        if size > self.max_component_bytes:
            raise ResourceLimitError(
                f"{label} exceeds the plan limit of {self.max_component_bytes} bytes"
            )

    def check_fixture_bytes(self, size: int) -> None:
        self.check_time()
        if size > self.max_total_bytes:
            raise ResourceLimitError(
                f"fixture exceeds the plan limit of {self.max_total_bytes} bytes"
            )
