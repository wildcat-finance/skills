"""Single-request Unix-socket service boundary for issue publication."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from .canonical import MAX_REQUEST_BYTES, canonical_json
from .errors import PublisherError, refuse
from .framing import MAX_RESULT_BYTES, SOCKET_PATH, read_closed_frame, write_frame
from .receipts import result_bytes
from .runtime import PublisherRuntime


SOCKET_TIMEOUT_SECONDS = 60.0


class Connection(Protocol):
    def recv(self, size: int) -> bytes: ...

    def sendall(self, data: bytes) -> None: ...

    def close(self) -> None: ...


class Listener(Protocol):
    def accept(self) -> tuple[Connection, object]: ...


@dataclass(frozen=True, slots=True)
class PeerIdentity:
    uid: int
    gid: int


PeerReader = Callable[[Connection], PeerIdentity]


def default_peer_reader(connection: Connection) -> PeerIdentity:
    """Read the kernel-authenticated effective identity on macOS."""

    getter = getattr(connection, "getpeereid", None)
    if not callable(getter):
        refuse("GIP221", "peer.identity")
    try:
        uid, gid = getter()
    except (OSError, TypeError, ValueError) as exc:
        raise PublisherError("GIP221", "peer.identity") from exc
    return PeerIdentity(uid=uid, gid=gid)


def admit_peer(peer: PeerIdentity, *, service_uid: int) -> None:
    """Trust filesystem group admission, while excluding root and the service UID."""

    if (
        not isinstance(peer, PeerIdentity)
        or isinstance(service_uid, bool)
        or not isinstance(service_uid, int)
        or service_uid < 1
        or isinstance(peer.uid, bool)
        or isinstance(peer.gid, bool)
        or not isinstance(peer.uid, int)
        or not isinstance(peer.gid, int)
        or peer.uid < 1
        or peer.gid < 1
        or peer.uid == service_uid
    ):
        refuse("GIP221", "peer.policy")


class PublisherServer:
    """Serve one already-accepted socket connection, then close it."""

    def __init__(
        self,
        *,
        runtime: PublisherRuntime,
        service_uid: int,
        peer_reader: PeerReader = default_peer_reader,
    ):
        if not callable(peer_reader):
            refuse("GIP221", "peer.reader")
        self._runtime = runtime
        self._service_uid = service_uid
        self._peer_reader = peer_reader

    def serve_connection(self, connection: Connection) -> None:
        payload: bytes
        try:
            admit_peer(
                self._peer_reader(connection),
                service_uid=self._service_uid,
            )
            request = read_closed_frame(connection, max_bytes=MAX_REQUEST_BYTES)
            payload = result_bytes(self._runtime.publish(request))
        except PublisherError as exc:
            payload = canonical_json(exc.diagnostic())
        except Exception:
            payload = canonical_json(PublisherError("GIP500", "server.internal").diagnostic())
        try:
            write_frame(connection, payload, max_bytes=MAX_RESULT_BYTES)
        finally:
            try:
                connection.close()
            except Exception:
                pass

    def serve_once(self, listener: Listener) -> None:
        try:
            connection, _address = listener.accept()
        except (OSError, TimeoutError) as exc:
            raise PublisherError("GIP220", "socket.accept") from exc
        self.serve_connection(connection)
