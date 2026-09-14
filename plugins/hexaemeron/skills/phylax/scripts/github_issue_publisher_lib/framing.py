"""One bounded, length-prefixed request or response frame."""

from __future__ import annotations

import os
import stat
import struct
from collections.abc import Callable
from typing import Protocol

from .canonical import MAX_REQUEST_BYTES
from .errors import PublisherError, refuse


FRAME_PREFIX_BYTES = 4
MAX_RESULT_BYTES = 4_096
SOCKET_PATH = "/var/run/wildcat-github-issue-publisher.sock"
SOCKET_MODE = 0o660


class SocketLike(Protocol):
    def recv(self, size: int) -> bytes: ...

    def sendall(self, data: bytes) -> None: ...


def encode_frame(payload: bytes, *, max_bytes: int) -> bytes:
    """Encode one non-empty payload below a code-owned ceiling."""

    if (
        isinstance(max_bytes, bool)
        or not isinstance(max_bytes, int)
        or max_bytes < 1
        or max_bytes > MAX_REQUEST_BYTES
    ):
        refuse("GIP200", "frame.limit")
    if (
        not isinstance(payload, bytes)
        or not payload
        or len(payload) > max_bytes
    ):
        refuse("GIP200", "frame.length")
    return struct.pack(">I", len(payload)) + payload


class FrameDecoder:
    """Incrementally accept exactly one frame and reject every trailing byte."""

    def __init__(self, *, max_bytes: int):
        if (
            isinstance(max_bytes, bool)
            or not isinstance(max_bytes, int)
            or max_bytes < 1
            or max_bytes > MAX_REQUEST_BYTES
        ):
            refuse("GIP200", "frame.limit")
        self._max_bytes = max_bytes
        self._prefix = bytearray()
        self._payload = bytearray()
        self._expected: int | None = None
        self._complete = False
        self._closed = False

    @property
    def buffered_bytes(self) -> int:
        return len(self._prefix) + len(self._payload)

    def feed(self, chunk: bytes) -> None:
        if self._closed or not isinstance(chunk, bytes):
            refuse("GIP203", "frame.state")
        if not chunk:
            return
        position = 0
        while position < len(chunk):
            if self._complete:
                refuse("GIP203", "frame.trailing")
            if self._expected is None:
                take = min(FRAME_PREFIX_BYTES - len(self._prefix), len(chunk) - position)
                self._prefix.extend(chunk[position : position + take])
                position += take
                if len(self._prefix) < FRAME_PREFIX_BYTES:
                    continue
                declared = struct.unpack(">I", self._prefix)[0]
                self._prefix.clear()
                if declared < 1 or declared > self._max_bytes:
                    refuse("GIP200", "frame.length")
                self._expected = declared
            remaining = self._expected - len(self._payload)
            take = min(remaining, len(chunk) - position)
            self._payload.extend(chunk[position : position + take])
            position += take
            if len(self._payload) == self._expected:
                self._complete = True

    def finish(self) -> bytes:
        if self._closed:
            refuse("GIP203", "frame.state")
        self._closed = True
        if not self._complete or self._expected is None:
            self._prefix.clear()
            self._payload.clear()
            refuse("GIP202", "frame.short")
        payload = bytes(self._payload)
        self._payload.clear()
        self._expected = None
        return payload

    def close(self) -> None:
        self._prefix.clear()
        self._payload.clear()
        self._expected = None
        self._complete = False
        self._closed = True


def read_closed_frame(connection: SocketLike, *, max_bytes: int) -> bytes:
    """Read through EOF so concatenated and trailing frames cannot hide."""

    decoder = FrameDecoder(max_bytes=max_bytes)
    try:
        while True:
            chunk = connection.recv(min(65_536, max_bytes + FRAME_PREFIX_BYTES))
            if not isinstance(chunk, bytes):
                refuse("GIP201", "frame.read")
            if not chunk:
                return decoder.finish()
            decoder.feed(chunk)
    except PublisherError:
        raise
    except (OSError, TimeoutError) as exc:
        raise PublisherError("GIP201", "frame.read") from exc
    finally:
        decoder.close()


def write_frame(connection: SocketLike, payload: bytes, *, max_bytes: int) -> None:
    """Write one complete bounded frame without exposing partial state."""

    frame = encode_frame(payload, max_bytes=max_bytes)
    try:
        connection.sendall(frame)
    except (OSError, TimeoutError) as exc:
        raise PublisherError("GIP201", "frame.write") from exc


def validate_socket_path(
    path: str,
    *,
    service_uid: int,
    service_gid: int,
    lstat: Callable[[str], os.stat_result] = os.lstat,
) -> None:
    """Require the one code-owned socket, owner, group, and mode."""

    if path != SOCKET_PATH:
        refuse("GIP220", "socket.path")
    try:
        status = lstat(path)
    except (OSError, TypeError, ValueError) as exc:
        raise PublisherError("GIP220", "socket.path") from exc
    if (
        isinstance(service_uid, bool)
        or not isinstance(service_uid, int)
        or service_uid < 1
        or isinstance(service_gid, bool)
        or not isinstance(service_gid, int)
        or service_gid < 1
    ):
        refuse("GIP220", "socket.identity")
    try:
        matches = (
            stat.S_ISSOCK(status.st_mode)
            and status.st_nlink == 1
            and status.st_uid == service_uid
            and status.st_gid == service_gid
            and stat.S_IMODE(status.st_mode) == SOCKET_MODE
        )
    except (AttributeError, TypeError, ValueError):
        matches = False
    if not matches:
        refuse("GIP220", "socket.identity")
