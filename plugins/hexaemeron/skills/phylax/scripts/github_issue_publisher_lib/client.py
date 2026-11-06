"""Credential-free client for the single issue-publication operation."""

from __future__ import annotations

from collections.abc import Callable
import os
import socket
from typing import Protocol

from .canonical import MAX_REQUEST_BYTES
from .errors import PublisherError, refuse
from .framing import (
    MAX_RESULT_BYTES,
    SOCKET_PATH,
    read_closed_frame,
    validate_socket_path,
    write_frame,
)
from .receipts import parse_closed_result


CLIENT_TIMEOUT_SECONDS = 60.0


class ClientConnection(Protocol):
    def recv(self, size: int) -> bytes: ...

    def sendall(self, data: bytes) -> None: ...

    def shutdown(self, how: int) -> None: ...

    def close(self) -> None: ...


Connector = Callable[[str, float], ClientConnection]


def _connect(path: str, timeout_seconds: float) -> ClientConnection:
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        connection.settimeout(timeout_seconds)
        connection.connect(path)
        return connection
    except Exception:
        connection.close()
        raise


class PublisherClient:
    """Expose one fixed-socket publish call and no credential or HTTP surface."""

    def __init__(
        self,
        *,
        service_uid: int,
        service_gid: int,
        connector: Connector = _connect,
        lstat: Callable[[str], os.stat_result] = os.lstat,
    ):
        if not callable(connector) or not callable(lstat):
            refuse("GIP220", "client.components")
        self._service_uid = service_uid
        self._service_gid = service_gid
        self._connector = connector
        self._lstat = lstat

    def publish(self, request: bytes) -> dict[str, object]:
        if not isinstance(request, bytes):
            refuse("GIP200", "frame.request")
        validate_socket_path(
            SOCKET_PATH,
            service_uid=self._service_uid,
            service_gid=self._service_gid,
            lstat=self._lstat,
        )
        connection: ClientConnection | None = None
        try:
            connection = self._connector(SOCKET_PATH, CLIENT_TIMEOUT_SECONDS)
            write_frame(connection, request, max_bytes=MAX_REQUEST_BYTES)
            connection.shutdown(socket.SHUT_WR)
            response = read_closed_frame(connection, max_bytes=MAX_RESULT_BYTES)
            return parse_closed_result(response)
        except PublisherError:
            raise
        except (OSError, TimeoutError) as exc:
            raise PublisherError("GIP220", "client.connection") from exc
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass
