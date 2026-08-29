"""Threaded loopback HTTP transport for offline Lazarus replay."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
from pathlib import Path
from typing import Any

from .canonical import MAX_JSON_BYTES, dumps, loads
from .errors import FormatError, ResourceLimitError
from .replay import ReplayStore, invalid_request, parse_error


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8545


class ReplayHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        store: ReplayStore,
    ) -> None:
        self.store = store
        super().__init__(address, ReplayHandler)


class ReplayHandler(BaseHTTPRequestHandler):
    server: ReplayHTTPServer

    def do_POST(self) -> None:
        raw = self._read_body()
        if raw is None:
            self._write_json(parse_error())
            return
        try:
            value = loads(raw, max_bytes=MAX_JSON_BYTES)
        except (FormatError, ResourceLimitError):
            self._write_json(parse_error())
            return
        if isinstance(value, list):
            if not value:
                self._write_json(invalid_request())
                return
            responses = [self.server.store.dispatch(item) for item in value]
            body = [response for response in responses if response is not None]
            if not body:
                self._write_empty()
                return
            self._write_json(body)
            return
        response = self.server.store.dispatch(value)
        if response is None:
            self._write_empty()
            return
        self._write_json(response)

    def do_GET(self) -> None:
        self.send_response(405)
        self.send_header("Allow", "POST")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _read_body(self) -> bytes | None:
        value = self.headers.get("Content-Length")
        try:
            length = int(value) if value is not None else -1
        except ValueError:
            return None
        if length < 0 or length > MAX_JSON_BYTES:
            return None
        raw = self.rfile.read(length)
        if len(raw) != length:
            return None
        return raw

    def _write_json(self, value: Any) -> None:
        body = dumps(value) + b"\n"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_empty(self) -> None:
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        return


def make_server(
    fixture: str | Path,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> ReplayHTTPServer:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        raise FormatError("replay host must be a literal loopback address") from None
    if address.version != 4 or not address.is_loopback:
        raise FormatError("replay host must be an IPv4 loopback address")
    if not isinstance(port, int) or isinstance(port, bool) or not 0 <= port <= 65535:
        raise FormatError("replay port must be between 0 and 65535")
    store = ReplayStore.from_fixture(fixture)
    try:
        return ReplayHTTPServer((host, port), store)
    except OSError:
        raise FormatError("cannot bind the loopback replay server") from None


def serve_fixture(
    fixture: str | Path,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    server = make_server(fixture, host=host, port=port)
    try:
        bound_host, bound_port = server.server_address[:2]
        print(f"lazarus replay listening on http://{bound_host}:{bound_port}", flush=True)
        server.serve_forever()
    finally:
        server.server_close()
