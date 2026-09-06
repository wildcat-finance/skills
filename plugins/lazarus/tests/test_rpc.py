"""The capture transport bounds and reorders JSON-RPC without leaking errors."""

from http.client import IncompleteRead
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import signal
from threading import Thread
import time
import traceback
import unittest
from unittest import mock

from lazarus_lib.canonical import loads
from lazarus_lib.errors import FormatError, ResourceLimitError
from lazarus_lib.limits import CaptureLimits
from lazarus_lib.rpc import JsonRpcClient, RpcTransportError

from .fake_rpc import FakeRpc, RpcError


def limits(**changes):
    values = {
        "max_requests": 20,
        "max_component_bytes": 4096,
        "max_total_bytes": 16384,
        "max_elapsed_seconds": 10,
    }
    values.update(changes)
    return CaptureLimits(values)


class RpcTests(unittest.TestCase):
    def test_out_of_order_batch_responses_return_in_request_order(self):
        def dispatch(method, params, server):
            return params[0]

        with FakeRpc(dispatch, reverse_batches=True) as server:
            client = JsonRpcClient(server.url, limits())
            outcomes = client.request_many([("one", [1]), ("two", [2]), ("three", [3])])
        self.assertEqual([item.result for item in outcomes], [1, 2, 3])

    def test_rpc_errors_keep_only_code_and_stable_message(self):
        def dispatch(method, params, server):
            return RpcError(-32602, "secret provider URL", {"token": "bearer-secret"})

        with FakeRpc(dispatch) as server:
            outcome = JsonRpcClient(server.url, limits()).request_many([("bad", [])])[0]
        self.assertEqual(
            outcome.error,
            {"code": -32602, "message": "provider request failed"},
        )

    def test_missing_or_duplicate_batch_ids_fail(self):
        raw = b'[{"jsonrpc":"2.0","id":1,"result":1},{"jsonrpc":"2.0","id":1,"result":2}]'
        with FakeRpc(lambda *args: None, raw_response=raw) as server:
            client = JsonRpcClient(server.url, limits())
            with self.assertRaisesRegex(FormatError, "duplicate"):
                client.request_many([("one", []), ("two", [])])

    def test_response_container_matches_request_cardinality(self):
        singleton_batch = b'[{"jsonrpc":"2.0","id":1,"result":"0x1"}]'
        with FakeRpc(lambda *args: None, raw_response=singleton_batch) as server:
            with self.assertRaisesRegex(FormatError, "single response"):
                JsonRpcClient(server.url, limits()).call("eth_chainId", [])

        singleton_object = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}'
        with FakeRpc(lambda *args: None, raw_response=singleton_object) as server:
            with self.assertRaisesRegex(FormatError, "batch response"):
                JsonRpcClient(server.url, limits()).request_many(
                    [("one", []), ("two", [])]
                )

    def test_batch_id_validation_is_linear(self):
        class CountingInt(int):
            comparisons = 0

            def __eq__(self, other):
                type(self).comparisons += 1
                return super().__eq__(other)

            __hash__ = int.__hash__

        count = 128
        responses = [
            {"jsonrpc": "2.0", "id": CountingInt(index), "result": index}
            for index in range(1, count + 1)
        ]
        client = JsonRpcClient(
            "https://rpc.example",
            limits(max_requests=count),
            max_batch_size=count,
        )
        with mock.patch.object(client, "_post", return_value=responses):
            outcomes = client.request_many([("read", []) for _ in range(count)])
        self.assertEqual(len(outcomes), count)
        self.assertLess(CountingInt.comparisons, count * 4)

    def test_request_many_splits_calls_into_provider_sized_batches(self):
        posted = []

        def fake_post(body):
            payload = loads(body, max_bytes=65536)
            single = isinstance(payload, dict)
            requests = [payload] if single else payload
            posted.append([request["id"] for request in requests])
            answers = [
                {"jsonrpc": "2.0", "id": request["id"], "result": request["id"]}
                for request in requests
            ]
            return answers[0] if single else answers

        client = JsonRpcClient(
            "https://rpc.example",
            limits(max_requests=7),
            max_batch_size=3,
        )
        with mock.patch.object(client, "_post", side_effect=fake_post):
            outcomes = client.request_many([("read", []) for _ in range(7)])
        self.assertEqual(posted, [[1, 2, 3], [4, 5, 6], [7]])
        self.assertEqual([outcome.result for outcome in outcomes], [1, 2, 3, 4, 5, 6, 7])

    def test_batch_size_below_one_is_refused(self):
        with self.assertRaises(ValueError):
            JsonRpcClient("https://rpc.example", limits(), max_batch_size=0)

    def test_response_body_is_bounded_before_json_parsing(self):
        with FakeRpc(lambda *args: None, raw_response=b" " * 65) as server:
            client = JsonRpcClient(server.url, limits(max_component_bytes=64))
            with self.assertRaisesRegex(ResourceLimitError, "RPC response"):
                client.call("large", [])

    def test_elapsed_budget_is_checked_during_streamed_response(self):
        body = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}'

        class Clock:
            now = 0.0

            def __call__(self):
                return self.now

        clock = Clock()

        class DripResponse:
            headers = {"Content-Length": str(len(body))}
            bytes_returned = 0
            read_calls = 0
            read1_calls = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self, size):
                self.read_calls += 1
                self.bytes_returned = len(body)
                clock.now = 3.0
                return body

            def read1(self, size):
                self.read1_calls += 1
                clock.now += 1.1
                chunk = body[self.bytes_returned : self.bytes_returned + 1]
                self.bytes_returned += len(chunk)
                return chunk

        response = DripResponse()

        class DripOpener:
            def open(self, request, timeout):
                return response

        bounded = CaptureLimits(
            {
                "max_requests": 20,
                "max_component_bytes": 4096,
                "max_total_bytes": 16384,
                "max_elapsed_seconds": 2,
            },
            clock=clock,
        )
        with self.assertRaisesRegex(ResourceLimitError, "seconds"):
            JsonRpcClient(
                "https://rpc.example",
                bounded,
                opener=DripOpener(),
            ).call("eth_chainId", [])
        self.assertEqual(response.read_calls, 0)
        self.assertEqual(response.read1_calls, 2)
        self.assertLess(response.bytes_returned, len(body))

    def test_declared_response_size_is_validated_before_reading(self):
        valid = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}'
        with FakeRpc(
            lambda *args: None,
            raw_response=valid,
            declared_length="not-a-number",
        ) as server:
            with self.assertRaisesRegex(RpcTransportError, "content length"):
                JsonRpcClient(server.url, limits()).call("invalid-length", [])
        with FakeRpc(
            lambda *args: None,
            raw_response=valid,
            declared_length="4097",
        ) as server:
            with self.assertRaisesRegex(ResourceLimitError, "RPC response"):
                JsonRpcClient(server.url, limits()).call("oversized-length", [])
        with FakeRpc(
            lambda *args: None,
            raw_response=valid,
            declared_length=str(len(valid) + 7),
        ) as server:
            with self.assertRaisesRegex(RpcTransportError, "content length"):
                JsonRpcClient(server.url, limits()).call("incomplete-length", [])

    def test_content_length_requires_ascii_decimal_digits(self):
        body = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}   '
        for value in (f"+{len(body)}", "4_2"):
            with self.subTest(content_length=value), FakeRpc(
                lambda *args: None,
                raw_response=body,
                declared_length=value,
            ) as server:
                with self.assertRaisesRegex(RpcTransportError, "content length"):
                    JsonRpcClient(server.url, limits()).call("eth_chainId", [])

    def test_absolute_deadline_interrupts_the_open_phase(self):
        class Response:
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read1(self, size):
                return b""

        class SlowOpener:
            completed = False

            def open(self, request, timeout):
                time.sleep(0.1)
                self.completed = True
                return Response()

        opener = SlowOpener()
        previous_handler = signal.getsignal(signal.SIGALRM)
        previous_timer = signal.getitimer(signal.ITIMER_REAL)
        with self.assertRaisesRegex(ResourceLimitError, "seconds") as caught:
            JsonRpcClient(
                "https://rpc.example",
                limits(max_elapsed_seconds=0.02),
                opener=opener,
            ).call("eth_chainId", [])
        self.assertFalse(opener.completed)
        self.assertIsNone(caught.exception.__cause__)
        self.assertIsNone(caught.exception.__context__)
        self.assertEqual(signal.getsignal(signal.SIGALRM), previous_handler)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), previous_timer)

    def test_absolute_deadline_interrupts_json_decode(self):
        body = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}'
        completed = False

        def slow_loads(raw, *, max_bytes):
            nonlocal completed
            time.sleep(0.1)
            completed = True
            return {"jsonrpc": "2.0", "id": 1, "result": "0x1"}

        with FakeRpc(lambda *args: None, raw_response=body) as server:
            with mock.patch("lazarus_lib.rpc.loads", side_effect=slow_loads):
                with self.assertRaisesRegex(ResourceLimitError, "seconds") as caught:
                    JsonRpcClient(
                        server.url,
                        limits(max_elapsed_seconds=0.02),
                    ).call("eth_chainId", [])
        self.assertFalse(completed)
        self.assertIsNone(caught.exception.__cause__)
        self.assertIsNone(caught.exception.__context__)

    def test_absolute_deadline_does_not_replace_an_active_process_timer(self):
        class ForbiddenOpener:
            opened = False

            def open(self, request, timeout):
                self.opened = True
                raise AssertionError("an occupied process timer was replaced")

        opener = ForbiddenOpener()
        with mock.patch.object(signal, "getitimer", return_value=(1.0, 0.0)):
            with self.assertRaisesRegex(RpcTransportError, "deadline enforcement"):
                JsonRpcClient(
                    "https://rpc.example",
                    limits(),
                    opener=opener,
                ).call("eth_chainId", [])
        self.assertFalse(opener.opened)

    def test_ambiguous_http_response_framing_is_refused(self):
        body = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}'
        cases = (
            (
                "duplicate-length",
                (("Content-Length", str(len(body))), ("Content-Length", str(len(body) + 7))),
                body,
            ),
            (
                "transfer-and-length",
                (("Transfer-Encoding", "chunked"), ("Content-Length", str(len(body)))),
                f"{len(body):x}\r\n".encode() + body + b"\r\n0\r\n\r\n",
            ),
            (
                "duplicate-transfer",
                (("Transfer-Encoding", "chunked"), ("Transfer-Encoding", "identity")),
                f"{len(body):x}\r\n".encode() + body + b"\r\n0\r\n\r\n",
            ),
        )

        for name, headers, wire_body in cases:
            with self.subTest(framing=name):
                class AmbiguousResponse(BaseHTTPRequestHandler):
                    def do_POST(self):
                        self.send_response(200)
                        for header, value in headers:
                            self.send_header(header, value)
                        self.end_headers()
                        self.wfile.write(wire_body)

                    def log_message(self, format, *args):
                        return

                server = ThreadingHTTPServer(("127.0.0.1", 0), AmbiguousResponse)
                thread = Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    url = f"http://127.0.0.1:{server.server_address[1]}"
                    with self.assertRaisesRegex(RpcTransportError, "framing"):
                        JsonRpcClient(url, limits()).call("eth_chainId", [])
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join()

    def test_chunked_response_without_content_length_is_accepted(self):
        body = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}'

        class ChunkedResponse(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(200)
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                self.wfile.write(
                    f"{len(body):x}\r\n".encode() + body + b"\r\n0\r\n\r\n"
                )

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), ChunkedResponse)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}"
            result = JsonRpcClient(url, limits()).call("eth_chainId", [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        self.assertEqual(result, "0x1")

    def test_invalid_content_length_retains_no_provider_value(self):
        marker = "PRIVATE_CONTENT_LENGTH_SECRET"
        with FakeRpc(
            lambda *args: None,
            raw_response=b'{}',
            declared_length=marker,
        ) as server:
            try:
                JsonRpcClient(server.url, limits()).call("invalid-length", [])
            except Exception as exc:
                raised = exc
            else:
                self.fail("invalid content length was accepted")
        self.assertIsInstance(raised, RpcTransportError)
        self.assertIsNone(raised.__cause__)
        self.assertIsNone(raised.__context__)
        surfaces = (str(raised), repr(raised), "".join(traceback.format_exception(raised)))
        self.assertTrue(all(marker not in surface for surface in surfaces))

    def test_invalid_json_is_a_context_free_transport_refusal(self):
        marker = "PRIVATE_MALFORMED_JSON_SECRET"
        raw = f'{{"jsonrpc":"2.0","id":1,"result":"{marker}"'.encode()
        with FakeRpc(lambda *args: None, raw_response=raw) as server:
            try:
                JsonRpcClient(server.url, limits()).call("invalid-json", [])
            except Exception as exc:
                raised = exc
            else:
                self.fail("invalid provider JSON was accepted")
        self.assertIsInstance(raised, RpcTransportError)
        self.assertIsNone(raised.__cause__)
        self.assertIsNone(raised.__context__)
        surfaces = (str(raised), repr(raised), "".join(traceback.format_exception(raised)))
        self.assertTrue(all(marker not in surface for surface in surfaces))

    def test_invalid_provider_url_is_a_cause_free_transport_refusal(self):
        marker = "PRIVATE_PROVIDER_URL_SECRET"
        try:
            JsonRpcClient(marker, limits()).call("eth_chainId", [])
        except Exception as exc:
            raised = exc
        else:
            self.fail("invalid provider URL was accepted")
        self.assertIsInstance(raised, RpcTransportError)
        self.assertIsNone(raised.__cause__)
        self.assertIsNone(raised.__context__)
        surfaces = (str(raised), repr(raised), "".join(traceback.format_exception(raised)))
        self.assertTrue(all(marker not in surface for surface in surfaces))

    def test_non_http_provider_scheme_is_refused_before_opening(self):
        class ForbiddenOpener:
            opened = False

            def open(self, request, timeout):
                self.opened = True
                raise AssertionError("a non-HTTP handler was reached")

        opener = ForbiddenOpener()
        with self.assertRaisesRegex(RpcTransportError, "HTTP or HTTPS"):
            JsonRpcClient(
                "file:///tmp/local-rpc-response.json",
                limits(),
                opener=opener,
            ).call("eth_chainId", [])
        self.assertFalse(opener.opened)

    def test_incomplete_http_body_retains_no_provider_bytes(self):
        marker = b"PRIVATE_PARTIAL_BODY_SECRET"

        class BrokenResponse:
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self, size):
                raise IncompleteRead(marker, size)

        class BrokenOpener:
            def open(self, request, timeout):
                return BrokenResponse()

        try:
            JsonRpcClient(
                "https://rpc.example",
                limits(),
                opener=BrokenOpener(),
            ).call("eth_chainId", [])
        except Exception as exc:
            raised = exc
        else:
            self.fail("incomplete HTTP body was accepted")
        self.assertIsInstance(raised, RpcTransportError)
        self.assertIsNone(raised.__cause__)
        self.assertIsNone(raised.__context__)
        surfaces = (str(raised), repr(raised), "".join(traceback.format_exception(raised)))
        self.assertTrue(
            all(marker.decode() not in surface for surface in surfaces)
        )

    def test_hostile_response_nesting_is_bounded(self):
        nested = b'{"jsonrpc":"2.0","id":1,"result":' + b'{"x":' * 65
        nested += b"0" + b"}" * 66
        with FakeRpc(lambda *args: None, raw_response=nested) as server:
            with self.assertRaisesRegex(ResourceLimitError, "nesting"):
                JsonRpcClient(
                    server.url,
                    limits(max_component_bytes=16384, max_total_bytes=32768),
                ).call("nested", [])

    def test_redirects_are_refused_before_credentials_reach_another_origin(self):
        received = []

        class Target(BaseHTTPRequestHandler):
            def do_GET(self):
                received.append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()

            def log_message(self, format, *args):
                return

        target = ThreadingHTTPServer(("127.0.0.1", 0), Target)
        target_thread = Thread(target=target.serve_forever, daemon=True)
        target_thread.start()
        target_url = f"http://127.0.0.1:{target.server_address[1]}/target"

        class Redirect(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header("Location", target_url)
                self.end_headers()

            def log_message(self, format, *args):
                return

        redirect = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        redirect_thread = Thread(target=redirect.serve_forever, daemon=True)
        redirect_thread.start()
        try:
            url = f"http://127.0.0.1:{redirect.server_address[1]}/rpc"
            client = JsonRpcClient(
                url,
                limits(),
                headers={"Authorization": "Bearer redirect-secret"},
            )
            with self.assertRaisesRegex(RpcTransportError, "transport"):
                client.call("eth_chainId", [])
            self.assertEqual(received, [])
        finally:
            redirect.shutdown()
            redirect.server_close()
            redirect_thread.join(timeout=2)
            target.shutdown()
            target.server_close()
            target_thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
