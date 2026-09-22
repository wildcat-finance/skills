"""The bearer-credential hosted transport and the bounded local loopback path.

Step 8 gives `HttpsTransport` an optional per-instance bearer, read by
`from_environment` from `ALEXANDRIA_RPC_BEARER`, and adds a separate,
explicit opt-in local path -- `LoopbackHttpTransport`, reached only through
`transport_from_environment` -- for the literal-loopback Reth listener Step 9
selects as primary. Every case here proves what this step promises: the
credential and the endpoint never reach a file the collector, reconciler or
builder produces; the local path opens only for a precisely-spelled loopback
address and carries no bearer; and a refusal on either path never names what
it refused.
"""

from copy import deepcopy
import http.server
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest import mock
import urllib.request

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import validate_plan  # noqa: E402
import usdc_interval  # noqa: E402
from usdc_interval import (  # noqa: E402
    BEARER_ENV,
    ENDPOINT_ENV,
    LOOPBACK_ALLOW_ENV,
    Collector,
    HttpsTransport,
    LoopbackHttpTransport,
    Reconciler,
    TransportError,
    transport_from_environment,
)

from tests import test_usdc_interval as existing  # noqa: E402


TOKEN = "wildcat-test-bearer-3f8a9c7e1b2d4560"


class _FakeResponse:
    status = 200

    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self, limit):
        return self._body[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *_exception):
        return False


def _mock_open(captured, body=b'{"id": 0, "jsonrpc": "2.0", "result": null}'):
    def capture(_opener, request, timeout=None):
        captured.append((request, timeout))
        return _FakeResponse(body)
    return capture


class RequestHeaderIdentityTests(unittest.TestCase):
    """`REQUEST_HEADERS` never mutates; the bearer reaches one header or none."""

    def test_request_headers_constant_never_mutates_for_a_bearer_transport(self):
        reference = usdc_interval.REQUEST_HEADERS
        before = canonical_bytes(dict(usdc_interval.REQUEST_HEADERS))
        captured = []
        with mock.patch.object(
            urllib.request.OpenerDirector, "open", _mock_open(captured),
        ), mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used"),
        ):
            transport = HttpsTransport.from_environment(
                25, {ENDPOINT_ENV: existing.ENDPOINT, BEARER_ENV: TOKEN},
            )
            transport.request(b'{"id": 0}', "shard 0 logs")
        self.assertIs(usdc_interval.REQUEST_HEADERS, reference)
        self.assertEqual(canonical_bytes(dict(usdc_interval.REQUEST_HEADERS)), before)
        # The identity/equality proof above is only meaningful if the header
        # really was added to the copy the request actually carried.
        sent = dict(captured[0][0].header_items())
        self.assertEqual(sent.get("Authorization"), f"Bearer {TOKEN}")

    def test_no_authorization_header_without_the_bearer_variable(self):
        captured = []
        with mock.patch.object(
            urllib.request.OpenerDirector, "open", _mock_open(captured),
        ), mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used"),
        ):
            transport = HttpsTransport.from_environment(25, {ENDPOINT_ENV: existing.ENDPOINT})
            transport.request(b'{"id": 0}', "shard 0 logs")
        self.assertNotIn("Authorization", dict(captured[0][0].header_items()))

    def test_the_bearer_is_read_only_from_the_injected_mapping(self):
        """A real-process bearer must never leak in when the mapping omits it."""
        captured = []
        with mock.patch.dict(
            os.environ, {BEARER_ENV: "process-environment-bearer-must-not-be-used"},
        ), mock.patch.object(
            urllib.request.OpenerDirector, "open", _mock_open(captured),
        ), mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used"),
        ):
            transport = HttpsTransport.from_environment(25, {ENDPOINT_ENV: existing.ENDPOINT})
            transport.request(b'{"id": 0}', "shard 0 logs")
        self.assertNotIn("Authorization", dict(captured[0][0].header_items()))

    def test_a_clean_bearer_constructs(self):
        HttpsTransport(existing.ENDPOINT, 25, "clean-token-9182")

    def test_a_bearer_with_whitespace_or_a_non_printable_byte_refuses_construction(self):
        bad_bearers = (
            "has space", "tab\ttab", "new\nline", "carriage\rreturn",
            "bell\x07byte", "nbsp space", "  leading-and-trailing  ",
        )
        for bad in bad_bearers:
            with self.subTest(bearer=repr(bad)):
                try:
                    HttpsTransport(existing.ENDPOINT, 25, bad)
                except AlexandriaError as error:
                    message = str(error)
                    self.assertIn("whitespace", message)
                    self.assertNotIn(bad, message)
                    self.assertNotIn(existing.ENDPOINT, message)
                else:
                    self.fail(f"{bad!r} should have refused construction")

    def test_a_plans_provider_class_still_refuses_a_scheme_separator_or_at_sign(self):
        plan = deepcopy(existing.fixture()["plan"])
        for bad in ("https://evil.invalid", "user@host", "http://user@evil.invalid"):
            plan["provider"]["class"] = bad
            with self.subTest(value=bad):
                with self.assertRaisesRegex(AlexandriaError, "must not carry an endpoint"):
                    validate_plan(plan)

    def test_a_reconciliation_records_provider_class_still_refuses_a_scheme_separator_or_at_sign(self):
        state = existing.fixture()
        for bad in ("https://evil.invalid", "user@host"):
            with self.subTest(value=bad):
                with tempfile.TemporaryDirectory() as root:
                    with self.assertRaisesRegex(AlexandriaError, "must not carry an endpoint"):
                        Reconciler(state["plan"], root, existing.FixtureTransport(state), bad)


class JournalContentTests(existing.CollectorTestCase):
    """What a journal actually holds, and what survives a mid-collection refusal."""

    def test_every_journalled_request_decodes_to_exactly_id_jsonrpc_method_and_params(self):
        Collector(self.plan, self.root, existing.FixtureTransport(self.state)).collect()
        seen = 0
        for _name, data in existing.journal_files(self.root).items():
            for line in data.splitlines():
                if not line:
                    continue
                entry = json.loads(line)
                request = json.loads(entry["request"])
                self.assertEqual(set(request), {"id", "jsonrpc", "method", "params"})
                seen += 1
        self.assertGreater(seen, 0)

    def test_a_transport_refusal_mid_collection_closes_every_journal_handle_opened(self):
        """The boundary issue 1679 names: a refusal this step's transport work can
        raise (a status or transport failure) must not leave a journal handle
        open, exactly the guarantee `Collector.collect` already gives an
        opening-phase refusal.
        """
        def _fail(_envelope):
            raise TransportError("shard 2 boundary-blocks returned HTTP 500")

        transport = existing.FixtureTransport(
            self.state, faults={"shard 2 boundary-blocks": _fail},
        )
        collector = Collector(self.plan, self.root, transport)
        opened = []
        handle = collector.staging._handle

        def watched(name):
            value = handle(name)
            if value not in opened:
                opened.append(value)
            return value

        with mock.patch.object(collector.staging, "_handle", side_effect=watched):
            with self.assertRaises(TransportError):
                collector.collect()
        self.assertTrue(opened, "the refusal must land after at least one handle opened")
        self.assertTrue(all(value.closed for value in opened))
        self.assertEqual(collector.staging._handles, {})


class CredentialAbsenceWalkTests(existing.ReleaseTestCase):
    """The credential-in-artefact risk: neither string reaches a written file."""

    def _bearer_pipeline(self):
        backing = existing.FixtureTransport(self.state)

        def capture(_opener, request, timeout=None):
            body = backing.request(request.data, "credential-walk")
            return _FakeResponse(body)

        staging = self.scratch("credential-staging")
        with mock.patch.object(
            urllib.request.OpenerDirector, "open", capture,
        ), mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used"),
        ):
            transport = HttpsTransport.from_environment(
                self.plan["provider"]["timeout_seconds"],
                {ENDPOINT_ENV: existing.ENDPOINT, BEARER_ENV: TOKEN},
            )
            Collector(self.plan, staging, transport).collect()
            Reconciler(
                self.plan, staging, transport, "second archive endpoint, class only",
            ).reconcile()
        output = self.root / "credential-release"
        self.build(staging, output)
        return staging, output

    def test_the_token_and_the_endpoint_reach_no_file_in_staging_or_the_built_release(self):
        staging, output = self._bearer_pipeline()
        checked = 0
        for root in (staging, output):
            for path in sorted(Path(root).rglob("*")):
                if not path.is_file():
                    continue
                content = path.read_bytes()
                self.assertNotIn(TOKEN.encode(), content, f"{path} carries the bearer token")
                self.assertNotIn(
                    existing.ENDPOINT.encode(), content, f"{path} carries the endpoint",
                )
                checked += 1
        self.assertGreater(checked, 0)


class LoopbackTransportRefusalTests(unittest.TestCase):
    """The accepted/refused matrix for the bounded local loopback HTTP path."""

    def _env(self, endpoint, *, allow=True, bearer=None):
        values = {ENDPOINT_ENV: endpoint}
        if allow:
            values[LOOPBACK_ALLOW_ENV] = "1"
        if bearer is not None:
            values[BEARER_ENV] = bearer
        return values

    def test_a_literal_ipv4_loopback_with_opt_in_is_accepted(self):
        transport = transport_from_environment(5, self._env("http://127.0.0.1:8545/"))
        self.assertIsInstance(transport, LoopbackHttpTransport)

    def test_a_literal_ipv6_loopback_with_opt_in_is_accepted(self):
        transport = transport_from_environment(5, self._env("http://[::1]:8545/"))
        self.assertIsInstance(transport, LoopbackHttpTransport)

    def test_the_same_endpoint_without_opt_in_refuses_as_a_plain_http_endpoint(self):
        with self.assertRaisesRegex(AlexandriaError, "HTTPS endpoint"):
            transport_from_environment(5, self._env("http://127.0.0.1:8545/", allow=False))

    def test_a_public_http_address_with_opt_in_refuses_before_connecting(self):
        with self.assertRaisesRegex(AlexandriaError, "127.0.0.1 or ::1"):
            transport_from_environment(5, self._env("http://93.184.216.34:8545/"))

    def test_a_private_non_loopback_address_with_opt_in_refuses(self):
        for host in ("10.0.0.5", "192.168.1.5", "172.16.0.5"):
            with self.subTest(host=host):
                with self.assertRaisesRegex(AlexandriaError, "127.0.0.1 or ::1"):
                    transport_from_environment(5, self._env(f"http://{host}:8545/"))

    def test_a_dns_name_that_merely_resolves_to_loopback_refuses_without_any_lookup(self):
        with mock.patch.object(
            socket, "getaddrinfo",
            side_effect=AssertionError("DNS resolved; the host must be refused lexically"),
        ):
            with self.assertRaisesRegex(AlexandriaError, "127.0.0.1 or ::1"):
                transport_from_environment(5, self._env("http://loopback.example.test:8545/"))

    def test_localhost_by_name_refuses(self):
        with self.assertRaisesRegex(AlexandriaError, "127.0.0.1 or ::1"):
            transport_from_environment(5, self._env("http://localhost:8545/"))

    def test_an_ipv6_loopback_written_differently_refuses(self):
        endpoints = (
            "http://[0:0:0:0:0:0:0:1]:8545/",
            "http://[0000:0000:0000:0000:0000:0000:0000:0001]:8545/",
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                with self.assertRaisesRegex(AlexandriaError, "127.0.0.1 or ::1"):
                    transport_from_environment(5, self._env(endpoint))

    def test_url_user_information_refuses(self):
        endpoints = (
            "http://user:pass@127.0.0.1:8545/",
            "http://user@127.0.0.1@evil.test/",
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                with self.assertRaisesRegex(AlexandriaError, "no user information"):
                    transport_from_environment(5, self._env(endpoint))

    def test_a_malformed_authority_refuses(self):
        endpoints = (
            "http://127.0.0.1:not-a-port/",
            "http://127.0.0.1:999999/",
            "http://[::1/",
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                with self.assertRaisesRegex(AlexandriaError, "malformed authority"):
                    transport_from_environment(5, self._env(endpoint))

    def test_a_bearer_on_the_loopback_path_refuses(self):
        with self.assertRaisesRegex(AlexandriaError, "no bearer credential"):
            transport_from_environment(
                5, self._env("http://127.0.0.1:8545/", bearer="should-not-be-here"),
            )

    def test_no_refusal_in_this_matrix_names_the_endpoint(self):
        hostile = (
            self._env("http://93.184.216.34:8545/"),
            self._env("http://user:pass@127.0.0.1:8545/"),
            self._env("http://127.0.0.1:not-a-port/"),
            self._env("http://localhost:8545/"),
        )
        for values in hostile:
            try:
                transport_from_environment(5, values)
            except AlexandriaError as error:
                self.assertNotIn(values[ENDPOINT_ENV], str(error))
            else:
                self.fail("expected a refusal")

    def test_environment_proxy_settings_are_never_honored(self):
        proxy_env = {
            "HTTP_PROXY": "http://proxy.invalid:9999", "http_proxy": "http://proxy.invalid:9999",
        }
        with mock.patch.dict(os.environ, proxy_env):
            # Control: an opener built the ordinary way, under the same
            # environment, really does pick up the hostile proxy -- so the
            # absence checked below is this transport's own doing.
            default_opener = urllib.request.build_opener()
            default_proxies = [
                handler for handler in default_opener.handlers
                if isinstance(handler, urllib.request.ProxyHandler)
            ]
            self.assertEqual(len(default_proxies), 1)
            self.assertEqual(default_proxies[0].proxies.get("http"), proxy_env["http_proxy"])

            transport = LoopbackHttpTransport("http://127.0.0.1:8545/", 5)
        proxy_handlers = [
            handler for handler in transport._opener.handlers
            if isinstance(handler, urllib.request.ProxyHandler)
        ]
        # An empty-mapping ProxyHandler contributes no `<scheme>_open` method,
        # so `OpenerDirector.add_handler` never registers it at all: no
        # ProxyHandler is present, and "http" resolves only to `HTTPHandler`.
        self.assertEqual(proxy_handlers, [])
        self.assertTrue(
            all(
                not isinstance(handler, urllib.request.ProxyHandler)
                for handler in transport._opener.handle_open.get("http", [])
            )
        )

    def test_no_redirect_is_followed_on_the_loopback_path(self):
        transport = LoopbackHttpTransport("http://127.0.0.1:8545/", 5)
        redirect_handlers = [
            handler for handler in transport._opener.handlers
            if isinstance(handler, usdc_interval._NoRedirect)
        ]
        self.assertEqual(len(redirect_handlers), 1)
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                with self.assertRaisesRegex(TransportError, "redirected"):
                    redirect_handlers[0].redirect_request(
                        None, None, code, "Moved", {}, "http://elsewhere.invalid/",
                    )


class _LoopbackRPCHandler(http.server.BaseHTTPRequestHandler):
    """Answers a real POST from preserved chain state, over a real socket."""

    backing = None

    def log_message(self, _format, *_args):
        return

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            data = self.backing.request(body, "loopback-http-server")
        except Exception:
            self.send_response(500)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _bound_handler(backing):
    return type("_BoundLoopbackRPCHandler", (_LoopbackRPCHandler,), {"backing": backing})


class LoopbackCliCollectionTests(existing.CollectorTestCase):
    """A real local HTTP server proves the CLI reaches collection through the
    loopback path itself: the wiring, not a private replacement transport.
    """

    def _serve(self):
        backing = existing.FixtureTransport(self.state)
        server = http.server.HTTPServer(("127.0.0.1", 0), _bound_handler(backing))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.shutdown)
        return server.server_address[1]

    def test_a_cli_constructed_collect_reaches_the_local_transport_through_a_real_socket(self):
        port = self._serve()
        plan_path = self.root / "plan.json"
        plan_path.write_bytes(canonical_bytes(self.plan))
        staging = self.root / "staging"
        env = {
            ENDPOINT_ENV: f"http://127.0.0.1:{port}/rpc",
            LOOPBACK_ALLOW_ENV: "1",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            exit_code = usdc_interval.main(
                ["collect", "--plan", str(plan_path), "--staging", str(staging)],
            )
        self.assertEqual(exit_code, 0)
        checkpoint = existing.checkpoint(staging)
        self.assertEqual(len(checkpoint["history"]), len(self.plan["shards"]))
        self.assertEqual(checkpoint["history"][-1]["shard"], len(self.plan["shards"]) - 1)
        journals = existing.journal_files(staging)
        self.assertTrue(journals)

    def test_the_same_server_without_opt_in_refuses_before_any_collection(self):
        port = self._serve()
        plan_path = self.root / "plan.json"
        plan_path.write_bytes(canonical_bytes(self.plan))
        staging = self.root / "staging"
        env = {ENDPOINT_ENV: f"http://127.0.0.1:{port}/rpc"}
        with mock.patch.dict(os.environ, env, clear=False):
            exit_code = usdc_interval.main(
                ["collect", "--plan", str(plan_path), "--staging", str(staging)],
            )
        self.assertEqual(exit_code, 1)
        self.assertFalse((staging / "checkpoint.json").exists())

    def test_a_genuine_non_2xx_response_from_a_real_server_names_neither_endpoint_nor_bearer(self):
        """Every other HTTP-status assertion in this module (and in
        `test_usdc_interval.py`) drives `.request()` through a hand-built
        response object whose `.status` a mock sets directly, which never
        goes near `urllib`'s own error handling. A real connection behaves
        differently: `urllib.request`'s default `HTTPErrorProcessor` (never
        overridden here -- only `HTTPRedirectHandler` and `ProxyHandler` are)
        turns any non-2xx response into an `urllib.error.HTTPError`, a
        `URLError` subclass, before `LoopbackHttpTransport.request`'s own
        `if response.status != 200` line ever runs; that line is therefore
        unreachable over a real socket, and a genuine non-2xx response is
        instead caught by the generic `except urllib.error.URLError` branch,
        producing the transport-failure message rather than the
        HTTP-status one. Both messages carry only the caller's label, never
        the endpoint or a bearer, so the credential-absence guarantee this
        step's Tests names holds either way -- but only this test proves it
        against what a live server actually returns, rather than a stand-in
        that cannot occur outside a test.
        """
        def _fail(_envelope):
            raise usdc_interval.TransportError("fixture-forced failure for a live non-2xx probe")

        backing = existing.FixtureTransport(self.state, faults={"probe read": _fail})
        server = http.server.HTTPServer(("127.0.0.1", 0), _bound_handler(backing))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.shutdown)
        port = server.server_address[1]
        endpoint = f"http://127.0.0.1:{port}/rpc"

        transport = LoopbackHttpTransport(endpoint, 5)
        with self.assertRaises(TransportError) as caught:
            transport.request(b'{"id": 0}', "probe read")
        message = str(caught.exception)
        # This is the actual, observed behavior: the dead branch never fires,
        # so the message is the generic one, not "returned HTTP 500".
        self.assertEqual(message, "probe read transport failed")
        self.assertNotIn(endpoint, message)
        self.assertNotIn(str(port), message)


if __name__ == "__main__":
    unittest.main()
