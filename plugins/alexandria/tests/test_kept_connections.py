"""The transports keep one connection per worker slot between requests.

Each case drives `LoopbackHttpTransport` against a real HTTP/1.1 keep-alive
server on a loopback socket and counts the connections that server accepted.
A connection is reused only after its whole body was read, one the server
closed while idle is replaced, and the HTTPS opener keeps the environment's
proxy handling and its own TLS context.
"""

import http.server
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest import mock
import urllib.request

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

import usdc_interval  # noqa: E402
from usdc_interval import ENDPOINT_ENV, HttpsTransport, LoopbackHttpTransport, TransportError  # noqa: E402


class _KeepAliveHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format, *_args):
        return

    def setup(self):
        super().setup()
        with self.server.lock:
            self.server.connections += 1

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        with self.server.lock:
            self.server.requests += 1
            number = self.server.requests
        status, reply, close = self.server.answer(number, body)
        if reply is None:
            # Close without answering, the way a server drops a stale connection.
            self.close_connection = True
            return
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)
        # Closing here sends no `Connection: close`, so the client keeps the
        # connection it believes is still open.
        self.close_connection = close


def _echo(_number, body):
    return 200, b'{"echo": ' + body + b"}", False


class KeptConnectionTests(unittest.TestCase):
    def serve(self, answer=_echo):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _KeepAliveHandler)
        server.lock = threading.Lock()
        server.connections = 0
        server.requests = 0
        server.answer = answer
        # A client that closes with a body unread resets the server's socket;
        # that is the behaviour under test, not a failure to print.
        server.handle_error = lambda _request, _address: None
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.shutdown)
        transport = LoopbackHttpTransport(f"http://127.0.0.1:{server.server_address[1]}/rpc", 5)
        self.addCleanup(transport._connections.close)
        return server, transport

    def test_sequential_requests_share_one_connection(self):
        server, transport = self.serve()
        for number in range(5):
            with self.subTest(number=number):
                self.assertEqual(transport.request(str(number).encode(), "probe"), b'{"echo": %d}' % number)
        self.assertEqual((server.requests, server.connections), (5, 1))

    def test_concurrent_requests_open_at_most_one_connection_per_slot(self):
        server, transport = self.serve()
        slots = threading.BoundedSemaphore(2)
        failures = []

        def run(worker):
            for number in range(5):
                payload = str(worker * 10 + number).encode()
                try:
                    if transport.request(payload, "probe", slots=slots) != b'{"echo": ' + payload + b"}":
                        failures.append(payload)
                except TransportError as error:
                    failures.append(error)

        workers = [threading.Thread(target=run, args=(worker,)) for worker in range(4)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(10)
        self.assertEqual(failures, [])
        self.assertEqual(server.requests, 20)
        self.assertLessEqual(server.connections, 2)

    def test_a_body_left_unread_past_the_ceiling_closes_its_connection(self):
        server, transport = self.serve()
        with mock.patch.object(usdc_interval, "MAX_RAW_COMPONENT_BYTES", 4):
            self.assertEqual(transport.request(b"12345678", "probe"), b'{"ech')
        # Reusing that connection would read the rest of the first body as
        # the second response's status line.
        self.assertEqual(transport.request(b"2", "probe"), b'{"echo": 2}')
        self.assertEqual(server.connections, 2)

    def test_an_error_status_closes_its_connection(self):
        def fail_first(number, body):
            return (500, b'{"error": "first"}', False) if number == 1 else _echo(number, body)

        server, transport = self.serve(fail_first)
        with self.assertRaisesRegex(TransportError, "^probe transport failed$"):
            transport.request(b"1", "probe")
        self.assertEqual(transport.request(b"2", "probe"), b'{"echo": 2}')
        self.assertEqual(server.connections, 2)

    def test_a_connection_the_server_closed_while_idle_is_replaced(self):
        def close_each(number, body):
            status, reply, _close = _echo(number, body)
            return status, reply, True

        server, transport = self.serve(close_each)
        for number in range(3):
            self.assertEqual(transport.request(str(number).encode(), "probe"), b'{"echo": %d}' % number)
        self.assertEqual((server.requests, server.connections), (3, 3))

    def test_a_stale_kept_connection_is_retried_once_on_a_new_one(self):
        def close_each(number, body):
            status, reply, _close = _echo(number, body)
            return status, reply, True

        server, transport = self.serve(close_each)
        self.assertEqual(transport.request(b"1", "probe"), b'{"echo": 1}')
        # Skip the idle check, so the closed connection is really reused and
        # fails before any response byte arrives.
        with mock.patch.object(usdc_interval, "_idle_socket_is_readable", return_value=False):
            self.assertEqual(transport.request(b"2", "probe"), b'{"echo": 2}')
        self.assertEqual((server.requests, server.connections), (2, 2))

    def test_a_new_connection_that_fails_is_not_retried(self):
        def drop_first(number, body):
            return (200, None, True) if number == 1 else _echo(number, body)

        server, transport = self.serve(drop_first)
        with self.assertRaisesRegex(TransportError, "^probe transport failed$"):
            transport.request(b"1", "probe")
        self.assertEqual((server.requests, server.connections), (1, 1))


class HttpsOpenerTests(unittest.TestCase):
    def test_the_https_opener_keeps_connections_and_honours_the_environment_proxy(self):
        proxy = "http://proxy.invalid:3128"
        with mock.patch.dict(os.environ, {"HTTPS_PROXY": proxy, "https_proxy": proxy}):
            transport = HttpsTransport.from_environment(5, {ENDPOINT_ENV: "https://example.invalid/rpc"})
            default = urllib.request.build_opener()
        self.addCleanup(transport._connections.close)
        handlers = transport._opener.handle_open["https"]
        self.assertEqual(
            [type(handler) for handler in handlers if isinstance(handler, urllib.request.HTTPSHandler)],
            [usdc_interval._KeptHTTPSHandler],
        )
        proxies = [handler.proxies for handler in transport._opener.handlers
                   if isinstance(handler, urllib.request.ProxyHandler)]
        defaults = [handler.proxies for handler in default.handlers
                    if isinstance(handler, urllib.request.ProxyHandler)]
        self.assertEqual(proxies, defaults)
        self.assertEqual(proxies[0]["https"], proxy)

    def test_a_proxied_request_tunnels_and_keeps_proxy_credentials_off_the_origin(self):
        calls = []

        class Stop(Exception):
            pass

        class Recording:
            def __init__(self, host, timeout=None, **kwargs):
                calls.append(("connect", host, sorted(kwargs)))

            def set_tunnel(self, host, headers=None):
                calls.append(("tunnel", host, headers))

            def set_debuglevel(self, _level):
                return

            def request(self, method, selector, body, headers, encode_chunked=False):
                calls.append(("request", method, selector, headers))
                raise Stop()

            def close(self):
                calls.append(("close",))

        request = urllib.request.Request(
            "https://example.invalid/rpc", data=b"{}", headers={"Content-Type": "application/json"},
        )
        request.add_header("Proxy-authorization", "Basic c2VjcmV0")
        request.set_proxy("proxy.invalid:3128", "https")
        request.timeout = 5  # `OpenerDirector.open` sets it before any handler runs.
        handler = usdc_interval._KeptHTTPSHandler(usdc_interval._KeptConnections(1))
        with self.assertRaises(Stop):
            usdc_interval._open_kept(handler, Recording, request, handler._connections, context=handler._context)
        self.assertEqual(calls[0], ("connect", "proxy.invalid:3128", ["context"]))
        self.assertEqual(calls[1], ("tunnel", "example.invalid", {"Proxy-Authorization": "Basic c2VjcmV0"}))
        self.assertEqual(calls[2][:3], ("request", "POST", "/rpc"))
        self.assertNotIn("Proxy-Authorization", calls[2][3])
        self.assertNotIn("Connection", calls[2][3])
        self.assertEqual(calls[3], ("close",))


if __name__ == "__main__":
    unittest.main()
