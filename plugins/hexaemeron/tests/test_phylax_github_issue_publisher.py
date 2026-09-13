"""Cause-level guards for GitHub issue publication admission."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import stat
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = PLUGIN_ROOT / "skills" / "phylax" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "github-issue-publisher-v1"
CLI = SCRIPT_DIR / "github_issue_publisher.py"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from github_issue_publisher_lib import (  # noqa: E402
    AUTHORITY_SCHEMA,
    CANDIDATE_SCHEMA,
    FRAMEWORK_OPENING,
    FROZEN_SCHEMA,
    IMPRIMATUR_VERSION,
    MAX_JSON_MEMBERS,
    MAX_REQUEST_BYTES,
    MAX_STRING_BYTES,
    OPERATION,
    PublisherError,
    REPOSITORY,
    REQUEST_SCHEMA,
    SAPHENEIA_CHECKS,
    SAPHENEIA_VERSION,
    VULGATE_CHECKS,
    VULGATE_VERSION,
    admit_request,
    candidate_sha256,
    canonical_json,
    frozen_sha256,
    parse_json_bytes,
    read_bounded_file,
)
import github_issue_publisher_lib.policy as publisher_policy  # noqa: E402
from github_issue_publisher_lib.policy import default_imprimatur  # noqa: E402
import github_issue_publisher as publisher_cli  # noqa: E402
from github_issue_publisher_lib.client import PublisherClient  # noqa: E402
from github_issue_publisher_lib.framing import (  # noqa: E402
    MAX_RESULT_BYTES,
    SOCKET_PATH,
    FrameDecoder,
    encode_frame,
    read_closed_frame,
    validate_socket_path,
)
from github_issue_publisher_lib.receipts import (  # noqa: E402
    MemoryReceiptSink,
    RetainedEvents,
    parse_closed_result,
    result_bytes,
    result_document,
)
from github_issue_publisher_lib.runtime import PublisherRuntime  # noqa: E402
import github_issue_publisher_lib.runtime as publisher_runtime  # noqa: E402
from github_issue_publisher_lib.server import (  # noqa: E402
    PeerIdentity,
    PublisherServer,
    admit_peer,
    default_peer_reader,
)
from github_issue_publisher_lib.signer import (  # noqa: E402
    MAX_SIGNATURE_BYTES,
    OPENSSL_ARGUMENTS,
    PEM_PATH,
    RSA_SIGNATURE_BYTES,
    SIGN_TIMEOUT_SECONDS,
    OpenSSLSigner,
)
import github_issue_publisher_lib.signer as publisher_signer  # noqa: E402
from github_issue_publisher_lib.transport import (  # noqa: E402
    API_VERSION,
    GITHUB_REPOSITORY,
    ISSUES_ROUTE,
    TOKEN_ROUTE,
    HTTPSRequest,
    PinnedGitHubTransport,
    create_issue,
    exchange_installation_token,
)
import github_issue_publisher_lib.transport as publisher_transport  # noqa: E402


ROOT_FRAMEWORK_OPENING = (
    "Protasis decides which skill or skills this observation upgrades. "
    "The filer is the wrong party to guess."
)
CARRYOVER_ROW = "none | none | This publication carries no work into another issue."


def issue_body(opening: str, prose: str) -> str:
    sections = [prose, "Fiat-Required: 1", f"```carryover\n{CARRYOVER_ROW}\n```"]
    if opening:
        sections.insert(0, opening)
    return "\n\n".join(sections)


def candidate(title: str, body: str) -> dict[str, str]:
    return {"schema": CANDIDATE_SCHEMA, "title": title, "body": body}


def valid_document(
    *,
    title: str = "framework-56: checked publication boundary",
    body: str | None = None,
    queue: str = "observation",
    labels: list[str] | None = None,
    title_prefix: str = "framework-56",
    body_opening: str = FRAMEWORK_OPENING,
    host_structure: list[str] | None = None,
    protected_inventory: list[str] | None = None,
) -> dict[str, object]:
    if body is None:
        body = issue_body(
            FRAMEWORK_OPENING,
            "## Status\n\nThe publisher checks exact bytes before it asks for a credential.",
        )
    labels = (
        ["fiat-run-needed", "observation", "origin:ai"]
        if labels is None
        else labels
    )
    host_structure = ["## Status"] if host_structure is None else host_structure
    protected_inventory = (
        [
            "framework-56",
            FRAMEWORK_OPENING,
            "## Status",
            "exact bytes",
            "credential",
            "Fiat-Required: 1",
            CARRYOVER_ROW,
        ]
        if protected_inventory is None
        else protected_inventory
    )
    source = candidate(title, body)
    shaped = candidate(title, body)
    final = candidate(title, body)
    source_digest = candidate_sha256(title, body)
    shaped_digest = candidate_sha256(title, body)
    final_digest = candidate_sha256(title, body)
    frozen = {
        "schema": FROZEN_SCHEMA,
        "title_prefix": title_prefix,
        "body_opening": body_opening,
        "host_structure": host_structure,
        "protected_inventory": protected_inventory,
    }
    frozen_digest = frozen_sha256(frozen)
    gates = [
        {
            "stage": "sapheneia",
            "tool": "sapheneia:sapheneia",
            "version": SAPHENEIA_VERSION,
            "outcome": "passed",
            "source_sha256": source_digest,
            "candidate_sha256": shaped_digest,
            "subject_sha256": shaped_digest,
            "frozen_sha256": frozen_digest,
            "checks": list(SAPHENEIA_CHECKS),
        },
        {
            "stage": "imprimatur",
            "tool": "hexaemeron:imprimatur",
            "version": IMPRIMATUR_VERSION,
            "outcome": "clean",
            "subject_sha256": shaped_digest,
            "defects": 0,
        },
        {
            "stage": "vulgate",
            "tool": "hexaemeron:vulgate",
            "version": VULGATE_VERSION,
            "outcome": "parity",
            "source_sha256": shaped_digest,
            "candidate_sha256": final_digest,
            "subject_sha256": final_digest,
            "frozen_sha256": frozen_digest,
            "checks": list(VULGATE_CHECKS),
        },
        {
            "stage": "imprimatur-final",
            "tool": "hexaemeron:imprimatur",
            "version": IMPRIMATUR_VERSION,
            "outcome": "clean",
            "subject_sha256": final_digest,
            "defects": 0,
        },
    ]
    return {
        "schema": REQUEST_SCHEMA,
        "operation": OPERATION,
        "repository": REPOSITORY,
        "queue": queue,
        "labels": labels,
        "frozen": frozen,
        "source": source,
        "sapheneia_candidate": shaped,
        "final_candidate": final,
        "authority": {
            "schema": AUTHORITY_SCHEMA,
            "kind": "explicit-user-request",
            "outcome": "recorded",
            "reference": "skills#925",
            "subject_sha256": final_digest,
        },
        "gates": gates,
    }


def encoded(document: dict[str, object]) -> bytes:
    return canonical_json(document)


class FakeSigner:
    def __init__(
        self,
        *,
        signature: bytes = b"s" * RSA_SIGNATURE_BYTES,
        error: Exception | None = None,
        close_error: Exception | None = None,
        on_sign=None,
    ):
        self.signature = signature
        self.error = error
        self.close_error = close_error
        self.on_sign = on_sign
        self.calls: list[tuple[bytes, float]] = []
        self.closed = False

    def sign(self, signing_input: bytes, *, timeout_seconds: float) -> bytes:
        self.calls.append((bytes(signing_input), timeout_seconds))
        if self.on_sign is not None:
            self.on_sign()
        if self.error is not None:
            raise self.error
        return self.signature

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeResponse:
    def __init__(
        self,
        status: int,
        document: dict[str, object] | None = None,
        *,
        raw: bytes | None = None,
        headers: tuple[tuple[str, str], ...] = (("Content-Type", "application/json"),),
        chunk_bytes: int = 11,
        close_error: Exception | None = None,
    ):
        self.status = status
        self.headers = headers
        self.raw = canonical_json(document) if raw is None else raw
        self.chunk_bytes = chunk_bytes
        self.close_error = close_error
        self.offset = 0
        self.closed = False

    def read(self, size: int) -> bytes:
        take = min(size, self.chunk_bytes)
        chunk = self.raw[self.offset : self.offset + take]
        self.offset += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class QueueExchange:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests: list[HTTPSRequest] = []
        self.contexts: list[object] = []
        self.delivered: list[FakeResponse] = []

    def __call__(self, request: HTTPSRequest, context):
        self.requests.append(request)
        self.contexts.append(context)
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        self.delivered.append(response)
        return response


class FailingReceiptSink(MemoryReceiptSink):
    def __init__(self, *, write_error: bool = False, close_error: bool = False):
        super().__init__()
        self.write_error = write_error
        self.close_error = close_error

    def write(self, payload: bytes) -> None:
        if self.write_error:
            raise OSError("receipt canary must stay private")
        super().write(payload)

    def close(self) -> None:
        self.closed = True
        if self.close_error:
            raise OSError("receipt close canary must stay private")


def token_document(token: str = "t" * 32) -> dict[str, object]:
    return {
        "token": token,
        "expires_at": "2033-05-18T04:33:20Z",
        "permissions": {"issues": "write"},
        "repository_selection": "selected",
        "repositories": [{"full_name": GITHUB_REPOSITORY}],
    }


def issue_document(
    document: dict[str, object],
    *,
    number: int = 9250,
    title: str | None = None,
    body: str | None = None,
    url: str | None = None,
) -> dict[str, object]:
    final = document["final_candidate"]
    return {
        "number": number,
        "html_url": (
            f"https://github.com/wildcat-finance/skills/issues/{number}"
            if url is None
            else url
        ),
        "title": final["title"] if title is None else title,
        "body": final["body"] if body is None else body,
    }


def runtime_fixture(
    *,
    signer: FakeSigner | None = None,
    sink: MemoryReceiptSink | None = None,
    responses: list[object] | None = None,
    document: dict[str, object] | None = None,
    monotonic=lambda: 100.0,
):
    document = valid_document() if document is None else document
    signer = FakeSigner() if signer is None else signer
    sink = MemoryReceiptSink() if sink is None else sink
    if responses is None:
        issue = issue_document(document)
        responses = [
            FakeResponse(201, token_document()),
            FakeResponse(201, issue),
            FakeResponse(200, issue),
            FakeResponse(200, issue),
        ]
    exchange = QueueExchange(*responses)
    runtime = PublisherRuntime(
        signer=signer,
        transport=PinnedGitHubTransport(exchange),
        receipt_sink=sink,
        events=RetainedEvents(),
        wall_clock=lambda: 2_000_000_000.0,
        monotonic=monotonic,
        imprimatur_runner=lambda _text: {"defects": 0},
    )
    return document, runtime, signer, sink, exchange


class ChunkConnection:
    def __init__(self, *chunks: bytes):
        self.chunks = list(chunks)
        self.sent = bytearray()
        self.shutdowns: list[int] = []
        self.timeouts: list[float] = []
        self.closed = False

    def recv(self, size: int) -> bytes:
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if len(chunk) > size:
            self.chunks.insert(0, chunk[size:])
            return chunk[:size]
        return chunk

    def sendall(self, data: bytes) -> None:
        self.sent.extend(data)

    def shutdown(self, how: int) -> None:
        self.shutdowns.append(how)

    def settimeout(self, timeout_seconds: float) -> None:
        self.timeouts.append(timeout_seconds)

    def close(self) -> None:
        self.closed = True


def socket_status(
    *,
    mode: int = stat.S_IFSOCK | 0o660,
    uid: int = 501,
    gid: int = 502,
    links: int = 1,
):
    return SimpleNamespace(st_mode=mode, st_uid=uid, st_gid=gid, st_nlink=links)


class BoundaryTestCase(unittest.TestCase):
    def assert_publisher_error(
        self,
        code: str,
        field: str,
        operation,
    ) -> PublisherError:
        with self.assertRaises(PublisherError) as caught:
            operation()
        self.assertEqual(code, caught.exception.code)
        self.assertEqual(field, caught.exception.field)
        return caught.exception


def sample_result() -> dict[str, object]:
    return result_document(
        outcome="published",
        request_sha256="1" * 64,
        final_sha256="2" * 64,
        correlation_sha256="3" * 64,
        issue_number=9250,
        issue_url="https://github.com/wildcat-finance/skills/issues/9250",
        counts={
            "signer_attempts": 1,
            "token_attempts": 1,
            "post_attempts": 1,
            "authenticated_readbacks": 1,
            "anonymous_readbacks": 1,
        },
        readback="matched",
        cleanup_complete=True,
        code="GIP000",
    )


class FramingTests(BoundaryTestCase):
    def test_fragmented_frame_round_trips(self):
        payload = b"bounded-request"
        framed = encode_frame(payload, max_bytes=64)
        decoder = FrameDecoder(max_bytes=64)
        for byte in framed:
            decoder.feed(bytes([byte]))
        self.assertEqual(payload, decoder.finish())

        connection = ChunkConnection(*[bytes([byte]) for byte in framed], b"")
        self.assertEqual(payload, read_closed_frame(connection, max_bytes=64))

    def test_concatenated_and_trailing_frames_refuse(self):
        first = encode_frame(b"first", max_bytes=32)
        second = encode_frame(b"second", max_bytes=32)
        for raw in (first + second, first + b"x"):
            with self.subTest(raw=raw):
                decoder = FrameDecoder(max_bytes=32)
                self.assert_publisher_error(
                    "GIP203", "frame.trailing", lambda: decoder.feed(raw)
                )

    def test_short_prefix_and_payload_refuse(self):
        for raw in (b"\x00\x00", struct.pack(">I", 4) + b"abc"):
            with self.subTest(raw=raw):
                connection = ChunkConnection(raw, b"")
                self.assert_publisher_error(
                    "GIP202",
                    "frame.short",
                    lambda: read_closed_frame(connection, max_bytes=32),
                )

    def test_empty_and_oversized_frames_refuse(self):
        for raw in (struct.pack(">I", 0), struct.pack(">I", 33)):
            with self.subTest(raw=raw):
                decoder = FrameDecoder(max_bytes=32)
                self.assert_publisher_error(
                    "GIP200", "frame.length", lambda: decoder.feed(raw)
                )
        self.assert_publisher_error(
            "GIP200", "frame.length", lambda: encode_frame(b"", max_bytes=32)
        )
        self.assert_publisher_error(
            "GIP200",
            "frame.limit",
            lambda: encode_frame(b"x", max_bytes=MAX_REQUEST_BYTES + 1),
        )


class SocketBoundaryTests(BoundaryTestCase):
    def test_socket_path_type_owner_group_link_and_mode_are_fixed(self):
        validate_socket_path(
            SOCKET_PATH,
            service_uid=501,
            service_gid=502,
            lstat=lambda _path: socket_status(),
        )
        self.assert_publisher_error(
            "GIP220",
            "socket.path",
            lambda: validate_socket_path(
                "/tmp/publisher.sock",
                service_uid=501,
                service_gid=502,
                lstat=lambda _path: socket_status(),
            ),
        )
        invalid = (
            socket_status(mode=stat.S_IFREG | 0o660),
            socket_status(uid=503),
            socket_status(gid=503),
            socket_status(mode=stat.S_IFSOCK | 0o666),
            socket_status(links=2),
        )
        for status_value in invalid:
            with self.subTest(status=status_value):
                self.assert_publisher_error(
                    "GIP220",
                    "socket.identity",
                    lambda status_value=status_value: validate_socket_path(
                        SOCKET_PATH,
                        service_uid=501,
                        service_gid=502,
                        lstat=lambda _path: status_value,
                    ),
                )
        self.assert_publisher_error(
            "GIP220",
            "socket.identity",
            lambda: validate_socket_path(
                SOCKET_PATH,
                service_uid=501,
                service_gid=502,
                lstat=lambda _path: SimpleNamespace(),
            ),
        )

    def test_peer_policy_refuses_root_and_service_identity(self):
        admit_peer(PeerIdentity(uid=501, gid=502), service_uid=600)
        for peer in (
            PeerIdentity(uid=0, gid=502),
            PeerIdentity(uid=600, gid=502),
            PeerIdentity(uid=501, gid=0),
        ):
            with self.subTest(peer=peer):
                self.assert_publisher_error(
                    "GIP221",
                    "peer.policy",
                    lambda peer=peer: admit_peer(peer, service_uid=600),
                )

    def test_default_peer_reader_uses_macos_local_peer_credentials(self):
        class Connection:
            calls: list[tuple[int, int, int]] = []

            def getsockopt(self, level: int, option: int, size: int) -> bytes:
                self.calls.append((level, option, size))
                return struct.pack(
                    "@IIh2x16I",
                    0,
                    501,
                    2,
                    502,
                    503,
                    *([0] * 14),
                )

        connection = Connection()
        try:
            observed: object = default_peer_reader(connection)
        except PublisherError as exc:
            observed = (exc.code, exc.field)
        self.assertEqual(PeerIdentity(uid=501, gid=502), observed)
        self.assertEqual([(0, 1, 76)], connection.calls)

    @unittest.skipUnless(sys.platform == "darwin", "macOS LOCAL_PEERCRED only")
    def test_default_peer_reader_matches_a_live_macos_socketpair(self):
        left, right = socket.socketpair()
        try:
            try:
                observed: object = default_peer_reader(left)
            except PublisherError as exc:
                observed = (exc.code, exc.field)
            self.assertEqual(
                PeerIdentity(uid=os.geteuid(), gid=os.getegid()),
                observed,
            )
        finally:
            left.close()
            right.close()

    def test_client_uses_one_fixed_socket_operation(self):
        result = sample_result()
        connection = ChunkConnection(
            encode_frame(result_bytes(result), max_bytes=MAX_RESULT_BYTES),
            b"",
        )
        connects: list[tuple[str, float]] = []

        def connector(path: str, timeout_seconds: float):
            connects.append((path, timeout_seconds))
            return connection

        client = PublisherClient(
            service_uid=501,
            service_gid=502,
            connector=connector,
            lstat=lambda _path: socket_status(),
        )
        request = b'{"schema":"test"}'
        self.assertEqual(result, client.publish(request))
        self.assertEqual([(SOCKET_PATH, 60.0)], connects)
        self.assertEqual(
            encode_frame(request, max_bytes=MAX_REQUEST_BYTES), bytes(connection.sent)
        )
        self.assertEqual([socket.SHUT_WR], connection.shutdowns)
        self.assertTrue(connection.closed)

    def test_client_imports_no_signer_transport_or_service_runtime(self):
        source = (SCRIPT_DIR / "github_issue_publisher_lib/client.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        imported = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertFalse(imported & {"signer", "transport", "runtime", "server"})
        client_class = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "PublisherClient"
        )
        public_methods = [
            node.name
            for node in client_class.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ]
        self.assertEqual(["publish"], public_methods)
        for forbidden in ("PEM_PATH", "TOKEN_ROUTE", "ISSUES_ROUTE", "http.client"):
            self.assertNotIn(forbidden, source)

    def test_server_refuses_peer_before_runtime_and_closes_connection(self):
        class Runtime:
            called = False

            def publish(self, _request):
                self.called = True
                return sample_result()

        runtime = Runtime()
        connection = ChunkConnection(encode_frame(b"{}", max_bytes=32), b"")
        server = PublisherServer(
            runtime=runtime,
            service_uid=600,
            peer_reader=lambda _connection: PeerIdentity(uid=0, gid=502),
        )
        server.serve_connection(connection)
        self.assertFalse(runtime.called)
        self.assertTrue(connection.closed)
        length = struct.unpack(">I", bytes(connection.sent[:4]))[0]
        diagnostic = json.loads(bytes(connection.sent[4 : 4 + length]))
        self.assertEqual("GIP221", diagnostic["code"])
        self.assertEqual(0, diagnostic["post_attempts"])

    def test_server_reads_one_closed_request_and_returns_one_closed_result(self):
        result = sample_result()

        class Runtime:
            requests: list[bytes] = []

            def publish(self, request):
                self.requests.append(bytes(request))
                return result

        runtime = Runtime()
        request = b'{"schema":"test"}'
        framed = encode_frame(request, max_bytes=MAX_REQUEST_BYTES)
        connection = ChunkConnection(framed[:2], framed[2:9], framed[9:], b"")
        server = PublisherServer(
            runtime=runtime,
            service_uid=600,
            peer_reader=lambda _connection: PeerIdentity(uid=501, gid=502),
        )
        server.serve_connection(connection)
        self.assertEqual([request], runtime.requests)
        self.assertTrue(connection.closed)
        length = struct.unpack(">I", bytes(connection.sent[:4]))[0]
        self.assertEqual(
            result,
            parse_closed_result(bytes(connection.sent[4 : 4 + length])),
        )
        self.assertEqual(4 + length, len(connection.sent))
        self.assertEqual([60.0], connection.timeouts)


class SignerBoundaryTests(BoundaryTestCase):
    @classmethod
    def _is_production_signer_command(cls, arguments: object) -> bool:
        if not isinstance(arguments, (list, tuple)):
            return False
        return tuple(arguments) == OPENSSL_ARGUMENTS or PEM_PATH in arguments

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._real_popen = subprocess.Popen
        cls._spawn_calls: list[
            tuple[tuple[object, ...], dict[str, object]]
        ] = []

        def guarded_popen(*popen_args, **popen_kwargs):
            arguments = (
                popen_kwargs.get("args")
                if "args" in popen_kwargs
                else popen_args[0] if popen_args else None
            )
            if cls._is_production_signer_command(arguments):
                raise AssertionError("test attempted the production signer command")
            cls._spawn_calls.append((popen_args, popen_kwargs))
            return cls._real_popen(*popen_args, **popen_kwargs)

        cls._popen_guard = mock.patch.object(
            publisher_signer.subprocess,
            "Popen",
            side_effect=guarded_popen,
        )
        cls._popen_guard.start()

    @classmethod
    def tearDownClass(cls):
        cls._popen_guard.stop()
        super().tearDownClass()

    def setUp(self):
        self._spawn_calls.clear()

    def test_production_signer_spawn_guard_covers_executable_and_key(self):
        self.assertTrue(self._is_production_signer_command(OPENSSL_ARGUMENTS))
        self.assertTrue(
            self._is_production_signer_command((sys.executable, PEM_PATH))
        )
        self.assertFalse(
            self._is_production_signer_command((sys.executable, "-c", "pass"))
        )

    def test_signer_uses_fixed_arguments_stdin_timeout_and_output_limit(self):
        observed: list[tuple[tuple[str, ...], bytes, float, int]] = []

        def runner(arguments, signing_input, timeout_seconds, output_limit):
            observed.append((arguments, signing_input, timeout_seconds, output_limit))
            return b"s" * RSA_SIGNATURE_BYTES

        signer = OpenSSLSigner(runner)
        self.assertEqual(
            b"s" * RSA_SIGNATURE_BYTES,
            signer.sign(b"header.payload", timeout_seconds=SIGN_TIMEOUT_SECONDS),
        )
        self.assertEqual(
            [
                (
                    OPENSSL_ARGUMENTS,
                    b"header.payload",
                    SIGN_TIMEOUT_SECONDS,
                    MAX_SIGNATURE_BYTES,
                )
            ],
            observed,
        )
        self.assertEqual("/usr/bin/openssl", OPENSSL_ARGUMENTS[0])
        self.assertIn(PEM_PATH, OPENSSL_ARGUMENTS)

    def test_default_signer_inherits_no_environment_and_hides_stderr(self):
        canary = "STEP2_CREDENTIAL_CANARY"
        program = (
            "import os,sys;"
            f"sys.exit(7) if {canary!r} in os.environ else "
            f"sys.stdout.buffer.write(b's'*{RSA_SIGNATURE_BYTES})"
        )
        arguments = (sys.executable, "-c", program)
        with (
            mock.patch.dict(os.environ, {canary: "must-not-cross"}),
            mock.patch.object(publisher_signer, "OPENSSL_ARGUMENTS", arguments),
        ):
            self.assertEqual(
                b"s" * RSA_SIGNATURE_BYTES,
                OpenSSLSigner().sign(b"header.payload", timeout_seconds=5.0),
            )
        self.assertEqual(1, len(self._spawn_calls))
        popen_args, kwargs = self._spawn_calls[0]
        self.assertEqual((list(arguments),), popen_args)
        self.assertEqual({}, kwargs["env"])
        self.assertEqual(subprocess.DEVNULL, kwargs["stderr"])
        self.assertEqual(subprocess.PIPE, kwargs["stdout"])
        self.assertEqual(subprocess.PIPE, kwargs["stdin"])
        self.assertTrue(kwargs["close_fds"])
        self.assertNotIn("shell", kwargs)
        self.assertNotIn("must-not-cross", repr(self._spawn_calls))

    def test_default_signer_stops_child_at_output_ceiling(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / "crossed-output-limit"
            program = (
                "import os,pathlib,sys;"
                "[os.write(1,b'x'*65536) for _ in range(16)];"
                "pathlib.Path(sys.argv[1]).write_text('crossed')"
            )
            arguments = (sys.executable, "-c", program, str(sentinel))
            with mock.patch.object(
                publisher_signer,
                "OPENSSL_ARGUMENTS",
                arguments,
            ):
                self.assert_publisher_error(
                    "GIP211",
                    "signer.output",
                    lambda: OpenSSLSigner().sign(
                        b"header.payload", timeout_seconds=5.0
                    ),
                )
            self.assertFalse(sentinel.exists())

    def test_default_signer_kills_child_at_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / "crossed-timeout"
            program = (
                "import pathlib,sys,time;"
                "time.sleep(1);"
                "pathlib.Path(sys.argv[1]).write_text('crossed')"
            )
            arguments = (sys.executable, "-c", program, str(sentinel))
            with mock.patch.object(
                publisher_signer,
                "OPENSSL_ARGUMENTS",
                arguments,
            ):
                self.assert_publisher_error(
                    "GIP211",
                    "signer.unavailable",
                    lambda: OpenSSLSigner().sign(
                        b"header.payload", timeout_seconds=0.05
                    ),
                )
            self.assertFalse(sentinel.exists())

    def test_signer_refuses_timeout_overflow_nonzero_and_bad_signature(self):
        self.assert_publisher_error(
            "GIP210",
            "signer.timeout",
            lambda: OpenSSLSigner(lambda *_args: b"s" * RSA_SIGNATURE_BYTES).sign(
                b"header.payload", timeout_seconds=SIGN_TIMEOUT_SECONDS + 0.001
            ),
        )
        self.assert_publisher_error(
            "GIP211",
            "signer.output",
            lambda: OpenSSLSigner(lambda *_args: b"s" * (MAX_SIGNATURE_BYTES + 1)).sign(
                b"header.payload", timeout_seconds=5.0
            ),
        )
        self.assert_publisher_error(
            "GIP213",
            "signer.signature",
            lambda: OpenSSLSigner(lambda *_args: b"s" * (RSA_SIGNATURE_BYTES - 1)).sign(
                b"header.payload", timeout_seconds=5.0
            ),
        )
        arguments = (
            sys.executable,
            "-c",
            "import os;os.write(1,b'private');raise SystemExit(7)",
        )
        with mock.patch.object(publisher_signer, "OPENSSL_ARGUMENTS", arguments):
            self.assert_publisher_error(
                "GIP212",
                "signer.exit",
                lambda: OpenSSLSigner().sign(b"header.payload", timeout_seconds=5.0),
            )

    def test_signer_refuses_nonfinite_timeout_before_the_runner(self):
        calls: list[tuple[object, ...]] = []

        def runner(*arguments):
            calls.append(arguments)
            return b"s" * RSA_SIGNATURE_BYTES

        self.assert_publisher_error(
            "GIP210",
            "signer.timeout",
            lambda: OpenSSLSigner(runner).sign(
                b"header.payload", timeout_seconds=float("nan")
            ),
        )
        self.assertEqual([], calls)

    def test_signer_errors_are_sanitised(self):
        canary = "signer-secret-canary"

        def failed(*_args):
            raise OSError(canary)

        error = self.assert_publisher_error(
            "GIP211",
            "signer.unavailable",
            lambda: OpenSSLSigner(failed).sign(
                b"header.payload", timeout_seconds=5.0
            ),
        )
        retained = str(error) + json.dumps(error.diagnostic(), sort_keys=True)
        self.assertNotIn(canary, retained)


class TransportBoundaryTests(BoundaryTestCase):
    def token(self, response: FakeResponse):
        exchange = QueueExchange(response)
        transport = PinnedGitHubTransport(exchange)
        return (
            exchange_installation_token(
                "header.payload.signature",
                transport,
                now=2_000_000_000,
                timeout_seconds=15.0,
            ),
            exchange,
        )

    def test_token_exchange_is_exactly_narrowed(self):
        response = FakeResponse(201, token_document())
        grant, exchange = self.token(response)
        self.assertEqual("t" * 32, grant.token)
        self.assertEqual(2_000_003_600, grant.expires_at)
        self.assertTrue(response.closed)
        self.assertEqual(1, len(exchange.contexts))
        self.assertIsInstance(exchange.contexts[0], ssl.SSLContext)
        request = exchange.requests[0]
        self.assertEqual("POST", request.method)
        self.assertEqual(TOKEN_ROUTE, request.path)
        self.assertEqual(
            canonical_json(
                {"permissions": {"issues": "write"}, "repositories": ["skills"]}
            ),
            request.body,
        )
        self.assertIn(("X-GitHub-Api-Version", API_VERSION), request.headers)
        self.assertIn(("Authorization", "Bearer header.payload.signature"), request.headers)
        self.assertNotIn("header.payload.signature", repr(request))

    def test_token_response_refuses_missing_malformed_expired_or_wide_grants(self):
        cases = []
        missing = token_document()
        del missing["token"]
        cases.append((missing, "GIP310", "token.value"))
        malformed = token_document(token="short")
        cases.append((malformed, "GIP310", "token.value"))
        malformed_expiry = token_document()
        malformed_expiry["expires_at"] = "2033-05-18 04:33:20"
        cases.append((malformed_expiry, "GIP310", "token.expiry"))
        expired = token_document()
        expired["expires_at"] = "2033-05-18T03:33:50Z"
        cases.append((expired, "GIP310", "token.expiry"))
        wide = token_document()
        wide["permissions"] = {"issues": "write", "contents": "read"}
        cases.append((wide, "GIP311", "token.scope"))
        wrong_repository = token_document()
        wrong_repository["repositories"] = [{"full_name": "wildcat-finance/other"}]
        cases.append((wrong_repository, "GIP311", "token.repository"))
        for document, code, field in cases:
            with self.subTest(field=field):
                response = FakeResponse(201, document)
                self.assert_publisher_error(
                    code, field, lambda response=response: self.token(response)
                )
                self.assertTrue(response.closed)

    def test_transport_refuses_redirect_status_duplicate_and_oversized_response(self):
        cases = (
            (FakeResponse(302, {"message": "moved"}), "GIP304", "transport.redirect"),
            (FakeResponse(403, {"message": "denied"}), "GIP305", "transport.status"),
            (
                FakeResponse(201, raw=b'{"token":"a","token":"b"}'),
                "GIP303",
                "transport.response.duplicate",
            ),
            (
                FakeResponse(201, raw=b"not-json"),
                "GIP307",
                "transport.response",
            ),
            (
                FakeResponse(201, raw=b"x" * (8_192 + 1), chunk_bytes=8_193),
                "GIP306",
                "transport.response.bytes",
            ),
        )
        for response, code, field in cases:
            with self.subTest(field=field):
                exchange = QueueExchange(response)
                transport = PinnedGitHubTransport(exchange)
                self.assert_publisher_error(
                    code,
                    field,
                    lambda transport=transport: transport.request(
                        method="POST",
                        path=TOKEN_ROUTE,
                        headers=(("Accept", "application/json"),),
                        body=b"{}",
                        timeout_seconds=15.0,
                    ),
                )
                self.assertTrue(response.closed)

    def test_transport_refuses_bad_headers_and_closing_failure(self):
        bad_header = FakeResponse(
            201,
            {"ok": True},
            headers=(("X-Canary", "snowman-\N{SNOWMAN}"),),
        )
        transport = PinnedGitHubTransport(QueueExchange(bad_header))
        self.assert_publisher_error(
            "GIP302",
            "transport.headers",
            lambda: transport.request(
                method="POST",
                path=TOKEN_ROUTE,
                headers=(("Accept", "application/json"),),
                body=b"{}",
                timeout_seconds=15.0,
            ),
        )

        status_and_close_failure = FakeResponse(
            403,
            {"message": "denied"},
            close_error=OSError("close canary"),
        )
        transport = PinnedGitHubTransport(QueueExchange(status_and_close_failure))
        self.assert_publisher_error(
            "GIP309",
            "transport.response.close",
            lambda: transport.request(
                method="POST",
                path=TOKEN_ROUTE,
                headers=(("Accept", "application/json"),),
                body=b"{}",
                timeout_seconds=15.0,
            ),
        )
        self.assertTrue(bad_header.closed)

        close_failure = FakeResponse(
            201, {"ok": True}, close_error=OSError("close canary")
        )
        transport = PinnedGitHubTransport(QueueExchange(close_failure))
        self.assert_publisher_error(
            "GIP309",
            "transport.response.close",
            lambda: transport.request(
                method="POST",
                path=TOKEN_ROUTE,
                headers=(("Accept", "application/json"),),
                body=b"{}",
                timeout_seconds=15.0,
            ),
        )

    def test_live_transport_caps_headers_while_the_socket_is_read(self):
        read_sizes: list[int] = []
        response_head = (
            b"HTTP/1.1 201 Created\r\nX-Oversized: "
            + b"x" * publisher_transport.MAX_REMOTE_HEADER_BYTES
            + b"\r\n\r\n{}"
        )

        class Stream(io.BytesIO):
            def readline(self, size: int = -1) -> bytes:
                read_sizes.append(size)
                if size > publisher_transport.MAX_REMOTE_HEADER_BYTES + 1:
                    raise OSError("header read crossed the declared ceiling")
                return super().readline(size)

        class Socket:
            def makefile(self, _mode: str) -> Stream:
                return Stream(response_head)

        class Connection:
            response_class = publisher_transport.http.client.HTTPResponse
            closed = False

            def request(self, *_args, **_kwargs) -> None:
                return None

            def getresponse(self):
                response = self.response_class(Socket(), method="POST")
                response.begin()
                return response

            def close(self) -> None:
                self.closed = True

        connection = Connection()
        with mock.patch.object(
            publisher_transport.http.client,
            "HTTPSConnection",
            return_value=connection,
        ):
            self.assert_publisher_error(
                "GIP302",
                "transport.headers",
                lambda: PinnedGitHubTransport().request(
                    method="POST",
                    path=TOKEN_ROUTE,
                    headers=(("Accept", "application/json"),),
                    body=b"{}",
                    timeout_seconds=15.0,
                ),
            )
        self.assertTrue(connection.closed)
        self.assertLessEqual(
            max(read_sizes),
            publisher_transport.MAX_REMOTE_HEADER_BYTES + 1,
        )

    def test_transport_refuses_every_caller_selected_destination(self):
        exchange = QueueExchange(FakeResponse(200, {"ok": True}))
        transport = PinnedGitHubTransport(exchange)
        self.assert_publisher_error(
            "GIP300",
            "transport.destination",
            lambda: transport.request(
                method="POST",
                path="/repos/wildcat-finance/other/issues",
                headers=(("Accept", "application/json"),),
                body=b"{}",
                timeout_seconds=15.0,
            ),
        )
        self.assertEqual([], exchange.requests)

    def test_transport_refuses_nonfinite_timeout(self):
        exchange = QueueExchange(FakeResponse(201, {"ok": True}))
        transport = PinnedGitHubTransport(exchange)
        self.assert_publisher_error(
            "GIP300",
            "transport.timeout",
            lambda: transport.request(
                method="POST",
                path=TOKEN_ROUTE,
                headers=(("Accept", "application/json"),),
                body=b"{}",
                timeout_seconds=float("nan"),
            ),
        )
        self.assertEqual([], exchange.requests)

    def test_issue_post_mapping_and_returned_origin_are_exact(self):
        document = valid_document()
        response = FakeResponse(201, issue_document(document))
        exchange = QueueExchange(response)
        transport = PinnedGitHubTransport(exchange)
        final = document["final_candidate"]
        issue = create_issue(
            "t" * 32,
            title=final["title"],
            body=final["body"],
            labels=tuple(document["labels"]),
            transport=transport,
            timeout_seconds=20.0,
        )
        self.assertEqual(9250, issue.number)
        request = exchange.requests[0]
        self.assertEqual("POST", request.method)
        self.assertEqual(ISSUES_ROUTE, request.path)
        self.assertEqual(
            canonical_json(
                {
                    "body": final["body"],
                    "labels": document["labels"],
                    "title": final["title"],
                }
            ),
            request.body,
        )
        self.assertIn(("Authorization", "token " + "t" * 32), request.headers)
        self.assertTrue(response.closed)

        wrong = FakeResponse(
            201,
            issue_document(document, url="https://example.invalid/issues/9250"),
        )
        self.assert_publisher_error(
            "GIP320",
            "issue.origin",
            lambda: create_issue(
                "t" * 32,
                title=final["title"],
                body=final["body"],
                labels=tuple(document["labels"]),
                transport=PinnedGitHubTransport(QueueExchange(wrong)),
                timeout_seconds=20.0,
            ),
        )


class RuntimeBoundaryTests(BoundaryTestCase):
    def test_admission_refuses_before_signer_or_transport(self):
        _document, runtime, signer, sink, exchange = runtime_fixture()
        self.assert_publisher_error(
            "GIP120", "request", lambda: runtime.publish(b"{}")
        )
        self.assertEqual([], signer.calls)
        self.assertEqual([], exchange.requests)
        self.assertTrue(signer.closed)
        self.assertTrue(sink.closed)

    def test_published_result_has_one_attempt_and_exact_correlated_events(self):
        document, runtime, signer, sink, exchange = runtime_fixture()
        result = runtime.publish(encoded(document))
        self.assertEqual("published", result["outcome"])
        self.assertEqual("matched", result["readback"])
        self.assertEqual(
            {
                "signer_attempts": 1,
                "token_attempts": 1,
                "post_attempts": 1,
                "authenticated_readbacks": 1,
                "anonymous_readbacks": 1,
            },
            result["counts"],
        )
        self.assertEqual(1, len(signer.calls))
        self.assertEqual(4, len(exchange.requests))
        self.assertTrue(signer.closed)
        self.assertTrue(sink.closed)
        self.assertEqual(result_bytes(result), sink.payload)
        self.assertEqual(4, len(exchange.delivered))
        self.assertTrue(all(response.closed for response in exchange.delivered))
        self.assertEqual(
            [
                "admission",
                "signer",
                "token",
                "create",
                "readback-authenticated",
                "readback-anonymous",
                "cleanup",
                "receipt",
            ],
            [event["stage"] for event in runtime.events],
        )
        self.assertEqual(
            {result["correlation_sha256"]},
            {event["correlation_sha256"] for event in runtime.events},
        )

    def test_final_bytes_cannot_be_mutated_after_admission(self):
        document = valid_document()
        original = deepcopy(document["final_candidate"])

        def mutate_source_document():
            document["final_candidate"]["title"] = "framework-56: changed later"
            document["final_candidate"]["body"] = "changed later"

        signer = FakeSigner(on_sign=mutate_source_document)
        _document, runtime, _signer, _sink, exchange = runtime_fixture(
            signer=signer, document=document
        )
        result = runtime.publish(encoded(document))
        self.assertEqual("published", result["outcome"])
        posted = json.loads(exchange.requests[1].body)
        self.assertEqual(original["title"], posted["title"])
        self.assertEqual(original["body"], posted["body"])

    def test_create_transport_failure_is_indeterminate_and_never_retried(self):
        document = valid_document()
        token_response = FakeResponse(201, token_document())
        _document, runtime, _signer, sink, exchange = runtime_fixture(
            document=document,
            responses=[token_response, OSError("create outcome canary")],
        )
        result = runtime.publish(encoded(document))
        self.assertEqual("create-indeterminate", result["outcome"])
        self.assertEqual("GIP301", result["code"])
        self.assertEqual(1, result["counts"]["post_attempts"])
        self.assertEqual(2, len(exchange.requests))
        self.assertIsNone(result["issue_number"])
        self.assertIsNone(result["issue_url"])
        self.assertEqual(result_bytes(result), sink.payload)
        self.assertTrue(token_response.closed)
        retained = result_bytes(result) + canonical_json(list(runtime.events))
        self.assertNotIn(b"create outcome canary", retained)

    def test_indeterminate_create_survives_cleanup_and_receipt_failure(self):
        document = valid_document()
        signer = FakeSigner(close_error=OSError("cleanup canary"))
        token_response = FakeResponse(201, token_document())
        _document, runtime, _signer, _sink, _exchange = runtime_fixture(
            signer=signer,
            sink=FailingReceiptSink(write_error=True),
            document=document,
            responses=[token_response, OSError("create canary")],
        )
        result = runtime.publish(encoded(document))
        self.assertEqual("create-indeterminate", result["outcome"])
        self.assertEqual("GIP402", result["code"])
        self.assertFalse(result["cleanup_complete"])
        self.assertEqual(1, result["counts"]["post_attempts"])

    def test_unexpected_component_failure_is_sanitised_and_cleaned_up(self):
        document = valid_document()
        signer = FakeSigner(error=RuntimeError("component canary"))
        _document, runtime, _signer, sink, exchange = runtime_fixture(
            signer=signer, document=document
        )
        result = runtime.publish(encoded(document))
        self.assertEqual("refused", result["outcome"])
        self.assertEqual("GIP500", result["code"])
        self.assertEqual(0, result["counts"]["post_attempts"])
        self.assertEqual([], exchange.requests)
        self.assertTrue(signer.closed)
        self.assertTrue(sink.closed)

    def test_token_refusal_happens_before_issue_post(self):
        document = valid_document()
        wide = token_document()
        wide["permissions"] = {"issues": "write", "contents": "read"}
        response = FakeResponse(201, wide)
        _document, runtime, _signer, sink, exchange = runtime_fixture(
            document=document, responses=[response]
        )
        result = runtime.publish(encoded(document))
        self.assertEqual("refused", result["outcome"])
        self.assertEqual("GIP311", result["code"])
        self.assertEqual(1, result["counts"]["signer_attempts"])
        self.assertEqual(1, result["counts"]["token_attempts"])
        self.assertEqual(0, result["counts"]["post_attempts"])
        self.assertEqual(1, len(exchange.requests))
        self.assertTrue(response.closed)
        self.assertEqual(result_bytes(result), sink.payload)

    def test_authenticated_and_anonymous_mismatch_never_publish(self):
        document = valid_document()
        issue = issue_document(document)
        cases = (
            (
                [
                    FakeResponse(201, token_document()),
                    FakeResponse(201, issue),
                    FakeResponse(200, issue_document(document, title="wrong")),
                ],
                1,
                0,
                "readback-authenticated",
            ),
            (
                [
                    FakeResponse(201, token_document()),
                    FakeResponse(201, issue),
                    FakeResponse(200, issue),
                    FakeResponse(200, issue_document(document, body="wrong")),
                ],
                1,
                1,
                "readback-anonymous",
            ),
        )
        for responses, authenticated, anonymous, failed_stage in cases:
            with self.subTest(stage=failed_stage):
                _document, runtime, _signer, _sink, exchange = runtime_fixture(
                    document=document, responses=responses
                )
                result = runtime.publish(encoded(document))
                self.assertEqual("created-but-unverified", result["outcome"])
                self.assertEqual("failed", result["readback"])
                self.assertEqual(
                    authenticated, result["counts"]["authenticated_readbacks"]
                )
                self.assertEqual(anonymous, result["counts"]["anonymous_readbacks"])
                self.assertEqual(failed_stage, runtime.events[-3]["stage"])
                self.assertTrue(all(response.closed for response in responses))
                self.assertEqual(len(responses), len(exchange.requests))

    def test_receipt_and_cleanup_failures_are_terminal(self):
        for sink in (
            FailingReceiptSink(write_error=True),
            FailingReceiptSink(close_error=True),
        ):
            with self.subTest(sink=sink):
                document, runtime, signer, _sink, _exchange = runtime_fixture(sink=sink)
                result = runtime.publish(encoded(document))
                self.assertEqual("receipt-failed", result["outcome"])
                self.assertEqual("GIP402", result["code"])
                self.assertFalse(result["cleanup_complete"])
                self.assertTrue(signer.closed)
                self.assertEqual("receipt", runtime.events[-1]["stage"])
                self.assertEqual("refused", runtime.events[-1]["outcome"])

        signer = FakeSigner(close_error=OSError("cleanup canary"))
        document, runtime, _signer, sink, _exchange = runtime_fixture(signer=signer)
        result = runtime.publish(encoded(document))
        self.assertEqual("cleanup-failed", result["outcome"])
        self.assertEqual("GIP501", result["code"])
        self.assertFalse(result["cleanup_complete"])
        self.assertEqual(result_bytes(result), sink.payload)

    def test_deadline_exact_boundaries_pass_and_overruns_refuse(self):
        exact_stage = iter((0.0, 0.0, 5.0))
        budget = publisher_runtime._Budget(lambda: next(exact_stage))
        started, timeout = budget.begin(5.0)
        self.assertEqual(5.0, timeout)
        budget.finish(started, 5.0)

        over_stage = iter((0.0, 0.0, 5.001))
        budget = publisher_runtime._Budget(lambda: next(over_stage))
        started, _timeout = budget.begin(5.0)
        self.assert_publisher_error(
            "GIP330", "deadline.stage", lambda: budget.finish(started, 5.0)
        )

        exact_total = iter((0.0, 50.0, 60.0))
        budget = publisher_runtime._Budget(lambda: next(exact_total))
        started, timeout = budget.begin(20.0)
        self.assertEqual(10.0, timeout)
        budget.finish(started, 20.0)

        over_total = iter((0.0, 50.0, 60.001))
        budget = publisher_runtime._Budget(lambda: next(over_total))
        started, _timeout = budget.begin(20.0)
        self.assert_publisher_error(
            "GIP330", "deadline.stage", lambda: budget.finish(started, 20.0)
        )

    def test_nonfinite_clocks_refuse_without_reaching_the_signer(self):
        document, runtime, signer, sink, exchange = runtime_fixture(
            monotonic=lambda: float("nan")
        )
        self.assert_publisher_error(
            "GIP330",
            "deadline.clock",
            lambda: runtime.publish(encoded(document)),
        )
        self.assertEqual([], signer.calls)
        self.assertEqual([], exchange.requests)
        self.assertTrue(signer.closed)
        self.assertTrue(sink.closed)

        ticks = iter((100.0, float("nan")))
        document, runtime, signer, sink, exchange = runtime_fixture(
            monotonic=lambda: next(ticks)
        )
        self.assert_publisher_error(
            "GIP330",
            "deadline.clock",
            lambda: runtime.publish(encoded(document)),
        )
        self.assertEqual([], signer.calls)
        self.assertEqual([], exchange.requests)
        self.assertTrue(signer.closed)
        self.assertTrue(sink.closed)

        document, runtime, signer, sink, exchange = runtime_fixture()
        runtime._wall_clock = lambda: float("nan")
        result = runtime.publish(encoded(document))
        self.assertEqual("refused", result["outcome"])
        self.assertEqual("GIP330", result["code"])
        self.assertEqual(0, result["counts"]["signer_attempts"])
        self.assertEqual([], signer.calls)
        self.assertEqual([], exchange.requests)
        self.assertTrue(signer.closed)
        self.assertTrue(sink.closed)

    def test_late_clock_failure_still_closes_every_component(self):
        ticks = iter((100.0, 100.0, 100.0, float("nan"), float("nan")))
        document, runtime, signer, sink, exchange = runtime_fixture(
            monotonic=lambda: next(ticks)
        )
        self.assert_publisher_error(
            "GIP330",
            "deadline.clock",
            lambda: runtime.publish(encoded(document)),
        )
        self.assertEqual(1, len(signer.calls))
        self.assertEqual([], exchange.requests)
        self.assertTrue(signer.closed)
        self.assertTrue(sink.closed)

    def test_server_diagnostic_retains_attempts_after_terminal_event_failure(self):
        class CleanupFailureEvents(RetainedEvents):
            def emit(self, **values) -> None:
                if values.get("stage") == "cleanup":
                    raise PublisherError("GIP401", "events.value")
                super().emit(**values)

        document, runtime, signer, sink, exchange = runtime_fixture()
        runtime._events = CleanupFailureEvents()
        request = encoded(document)
        connection = ChunkConnection(
            encode_frame(request, max_bytes=MAX_REQUEST_BYTES),
            b"",
        )
        server = PublisherServer(
            runtime=runtime,
            service_uid=600,
            peer_reader=lambda _connection: PeerIdentity(uid=501, gid=502),
        )
        server.serve_connection(connection)

        length = struct.unpack(">I", bytes(connection.sent[:4]))[0]
        diagnostic = json.loads(bytes(connection.sent[4 : 4 + length]))
        self.assertEqual("GIP401", diagnostic["code"])
        self.assertEqual(1, diagnostic["mint_attempts"])
        self.assertEqual(1, diagnostic["post_attempts"])
        self.assertEqual(4, len(exchange.requests))
        self.assertTrue(all(response.closed for response in exchange.delivered))
        self.assertTrue(signer.closed)
        self.assertTrue(sink.closed)
        self.assertTrue(connection.closed)

    def test_credential_canary_stays_out_of_public_surfaces_and_file_receipt(self):
        canary = "ghs_STEP2_CANARY_0123456789abcdef"
        document = valid_document()
        issue = issue_document(document)
        responses = [
            FakeResponse(201, token_document(canary)),
            FakeResponse(201, issue),
            FakeResponse(200, issue),
            FakeResponse(200, issue),
        ]
        _document, runtime, signer, sink, exchange = runtime_fixture(
            document=document, responses=responses
        )
        result = runtime.publish(encoded(document))
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipt.json"
            receipt_path.write_bytes(sink.payload or b"")
            retained = b"\n".join(
                (
                    result_bytes(result),
                    canonical_json(list(runtime.events)),
                    repr(signer.calls).encode("utf-8"),
                    repr(exchange.requests).encode("utf-8"),
                    receipt_path.read_bytes(),
                )
            )
        self.assertNotIn(canary.encode("ascii"), retained)
        self.assertTrue(all(response.closed for response in responses))


class ReceiptBoundaryTests(BoundaryTestCase):
    def test_client_refuses_request_controlled_diagnostic_field(self):
        diagnostic = PublisherError(
            "GIP220", "credential canary copied from request"
        ).diagnostic()
        self.assert_publisher_error(
            "GIP400",
            "receipt.diagnostic",
            lambda: parse_closed_result(canonical_json(diagnostic)),
        )

    def test_client_refuses_non_integer_diagnostic_attempt_counts(self):
        for field, value in (
            ("mint_attempts", "REQUEST_CONTROLLED_CANARY"),
            ("post_attempts", {"value": "REQUEST_CONTROLLED_CANARY"}),
            ("mint_attempts", True),
            ("post_attempts", 2),
        ):
            with self.subTest(field=field, value=value):
                diagnostic = PublisherError("GIP220", "socket.path").diagnostic()
                diagnostic[field] = value
                self.assert_publisher_error(
                    "GIP400",
                    "receipt.diagnostic",
                    lambda diagnostic=diagnostic: parse_closed_result(
                        canonical_json(diagnostic)
                    ),
                )

        diagnostic = PublisherError("GIP220", "socket.path").diagnostic()
        diagnostic["code"] = "GIP000"
        self.assert_publisher_error(
            "GIP400",
            "receipt.diagnostic",
            lambda: parse_closed_result(canonical_json(diagnostic)),
        )

    def test_client_refuses_semantically_impossible_results(self):
        cases: list[dict[str, object]] = []

        published_without_publication = sample_result()
        published_without_publication.update(
            issue_number=None,
            issue_url=None,
            counts={
                "signer_attempts": 0,
                "token_attempts": 0,
                "post_attempts": 0,
                "authenticated_readbacks": 0,
                "anonymous_readbacks": 0,
            },
            readback="not-run",
            cleanup_complete=False,
            code="GIP999",
        )
        cases.append(published_without_publication)

        non_monotone_attempts = sample_result()
        non_monotone_attempts["counts"]["token_attempts"] = 0
        cases.append(non_monotone_attempts)

        indeterminate_with_issue = sample_result()
        indeterminate_with_issue.update(
            outcome="create-indeterminate",
            readback="not-run",
            code="GIP301",
        )
        cases.append(indeterminate_with_issue)

        matched_without_anonymous_readback = sample_result()
        matched_without_anonymous_readback["counts"]["anonymous_readbacks"] = 0
        cases.append(matched_without_anonymous_readback)

        refused_with_cleanup_code = sample_result()
        refused_with_cleanup_code.update(
            outcome="refused",
            issue_number=None,
            issue_url=None,
            counts={
                "signer_attempts": 1,
                "token_attempts": 0,
                "post_attempts": 0,
                "authenticated_readbacks": 0,
                "anonymous_readbacks": 0,
            },
            readback="not-run",
            code="GIP501",
        )
        cases.append(refused_with_cleanup_code)

        for document in cases:
            with self.subTest(outcome=document["outcome"]):
                self.assert_publisher_error(
                    "GIP400",
                    "receipt.value",
                    lambda document=document: parse_closed_result(
                        canonical_json(document)
                    ),
                )

    def test_returned_event_documents_cannot_mutate_retained_counts(self):
        events = RetainedEvents()
        counts = {
            "signer_attempts": 1,
            "token_attempts": 0,
            "post_attempts": 0,
            "authenticated_readbacks": 0,
            "anonymous_readbacks": 0,
        }
        events.emit(
            correlation_sha256="a" * 64,
            stage="signer",
            outcome="accepted",
            code="GIP000",
            counts=counts,
            elapsed_ms=1,
        )
        exposed = events.documents[0]
        exposed["counts"]["post_attempts"] = 1
        self.assertEqual(0, events.documents[0]["counts"]["post_attempts"])


class AdmissionTests(unittest.TestCase):
    def assert_refused(
        self,
        value: dict[str, object] | bytes,
        code: str,
        field: str | None = None,
        *,
        runner=None,
    ) -> PublisherError:
        raw = value if isinstance(value, bytes) else encoded(value)
        with self.assertRaises(PublisherError) as caught:
            admit_request(raw, imprimatur_runner=runner or (lambda _text: {"defects": 0}))
        self.assertEqual(code, caught.exception.code)
        if field is not None:
            self.assertEqual(field, caught.exception.field)
        self.assertEqual(0, caught.exception.mint_attempts)
        self.assertEqual(0, caught.exception.post_attempts)
        self.assertEqual(0, caught.exception.diagnostic()["mint_attempts"])
        self.assertEqual(0, caught.exception.diagnostic()["post_attempts"])
        return caught.exception

    def test_valid_request_runs_both_imprimatur_passes(self):
        observed: list[str] = []

        def runner(text: str) -> dict[str, int]:
            observed.append(text)
            return {"defects": 0}

        document = valid_document()
        result = admit_request(encoded(document), imprimatur_runner=runner)
        self.assertEqual("observation", result.queue)
        self.assertEqual(
            ("fiat-run-needed", "observation", "origin:ai"), result.labels
        )
        self.assertEqual(2, len(observed))
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(0, result.mint_attempts)
        self.assertEqual(0, result.post_attempts)
        self.assertEqual(result.final_sha256, result.document()["final_sha256"])
        self.assertNotIn("title", result.document())
        self.assertNotIn("body", result.document())

    def test_root_publication_contract_is_enforced_before_imprimatur(self):
        self.assertEqual(ROOT_FRAMEWORK_OPENING, FRAMEWORK_OPENING)
        document = valid_document(
            body=(
                f"{ROOT_FRAMEWORK_OPENING}\n\n"
                "## Status\n\n"
                "The publisher checks exact bytes before it asks for a credential."
            ),
            protected_inventory=[
                "framework-56",
                ROOT_FRAMEWORK_OPENING,
                "## Status",
                "exact bytes",
                "credential",
            ],
        )
        self.assert_refused(document, "GIP132", "publication.fiat-required")
        document = valid_document(
            body=(
                f"{ROOT_FRAMEWORK_OPENING}\n\n"
                "## Status\n\n"
                "The publisher checks exact bytes before it asks for a credential.\n\n"
                "Fiat-Required: 1"
            ),
            protected_inventory=[
                "framework-56",
                ROOT_FRAMEWORK_OPENING,
                "## Status",
                "exact bytes",
                "credential",
                "Fiat-Required: 1",
            ],
        )
        self.assert_refused(document, "GIP132", "publication.carryover")
        document = valid_document(labels=["observation", "only-pr-needed", "origin:ai"])
        self.assert_refused(document, "GIP131", "publication.decision-label")

    def test_golden_candidate_passes_the_root_publication_contract(self):
        controller = PLUGIN_ROOT / "skills" / "fiat" / "scripts" / "hexctl.py"
        specification = importlib.util.spec_from_file_location(
            "hexctl_publisher_contract", controller
        )
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        document = valid_document()
        final = document["final_candidate"]
        record, faults = module.issue_publication_contract_faults(
            final["title"], document["labels"], final["body"], "golden request"
        )
        self.assertEqual([], faults)
        self.assertEqual("framework-N", record["queue"])
        self.assertEqual(1, record["fiat_required"])
        self.assertEqual("none", record["carryover"][0]["id"])

    def test_root_valid_top_status_block_is_admitted(self):
        controller = PLUGIN_ROOT / "skills" / "fiat" / "scripts" / "hexctl.py"
        specification = importlib.util.spec_from_file_location(
            "hexctl_status_block_contract", controller
        )
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        body = (
            "<!-- status:start -->\n"
            "Publication is pending a current admission record.\n"
            "<!-- status:end -->\n\n"
            + issue_body(
                ROOT_FRAMEWORK_OPENING,
                "## Status\n\n"
                "The publisher checks exact bytes before it asks for a credential.",
            )
        )
        document = valid_document(body=body)
        record, faults = module.issue_publication_contract_faults(
            document["final_candidate"]["title"],
            document["labels"],
            body,
            "status-block request",
        )
        self.assertEqual([], faults)
        self.assertEqual([1, 3], record["status_block"])
        result = admit_request(encoded(document))
        self.assertEqual("observation", result.queue)
        self.assertEqual(0, result.mint_attempts)
        self.assertEqual(0, result.post_attempts)

    def test_root_valid_leading_metadata_comment_is_admitted(self):
        controller = PLUGIN_ROOT / "skills" / "fiat" / "scripts" / "hexctl.py"
        specification = importlib.util.spec_from_file_location(
            "hexctl_metadata_comment_contract", controller
        )
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        body = (
            "<!-- wildcat-origin: shoggoth -->\n\n"
            + issue_body(
                ROOT_FRAMEWORK_OPENING,
                "## Status\n\n"
                "The publisher checks exact bytes before it asks for a credential.",
            )
        )
        document = valid_document(body=body)
        record, faults = module.issue_publication_contract_faults(
            document["final_candidate"]["title"],
            document["labels"],
            body,
            "metadata-comment request",
        )
        self.assertEqual([], faults)
        self.assertEqual("framework-N", record["queue"])
        refusal = None
        try:
            result = admit_request(encoded(document))
        except PublisherError as error:
            refusal = (
                error.code,
                error.field,
                error.mint_attempts,
                error.post_attempts,
            )
        if refusal is not None:
            self.assertEqual(("GIP141", "frozen.body_opening", 0, 0), refusal)
            self.fail(
                "root-valid leading metadata comment was refused at "
                f"{refusal[0]}:{refusal[1]}"
            )
        self.assertEqual("observation", result.queue)
        self.assertEqual(0, result.mint_attempts)
        self.assertEqual(0, result.post_attempts)

    def test_root_queue_number_and_summary_grammar_is_enforced(self):
        for prefix in ("framework-0", "framework-01"):
            with self.subTest(prefix=prefix):
                document = valid_document(
                    title=f"{prefix}: checked publication boundary",
                    title_prefix=prefix,
                    protected_inventory=[
                        prefix,
                        FRAMEWORK_OPENING,
                        "## Status",
                        "exact bytes",
                        "credential",
                        "Fiat-Required: 1",
                        CARRYOVER_ROW,
                    ],
                )
                self.assert_refused(document, "GIP130", "queue.title_prefix")
        document = valid_document(title="framework-56:  checked publication boundary")
        self.assert_refused(document, "GIP130", "queue.title")

    def test_valid_fixture_is_the_canonical_golden_request(self):
        fixture = (FIXTURES / "valid-request.json").read_bytes().removesuffix(b"\n")
        self.assertEqual(encoded(valid_document()), fixture)
        result = admit_request(fixture, imprimatur_runner=lambda _text: {"defects": 0})
        self.assertEqual(
            "b7e467f4923807aa4dd70cdaeccd8f2c6dd418f09535dd230dc2c92daeebb2bb",
            result.final_sha256,
        )

    def test_default_imprimatur_accepts_clean_fixture(self):
        result = admit_request(encoded(valid_document()))
        self.assertEqual("observation", result.queue)

        class ExitingLoader:
            @staticmethod
            def create_module(_spec):
                return None

            @staticmethod
            def exec_module(_module):
                raise SystemExit("import aborted")

        specification = importlib.util.spec_from_loader(
            "github_issue_publisher_imprimatur", ExitingLoader()
        )
        with (
            mock.patch.object(publisher_policy, "_IMPRIMATUR_MODULE", None),
            mock.patch.object(
                publisher_policy.importlib.util,
                "spec_from_file_location",
                return_value=specification,
            ),
            self.assertRaises(PublisherError) as caught,
        ):
            admit_request(encoded(valid_document()))
        self.assertEqual("GIP152", caught.exception.code)
        self.assertEqual("gates.imprimatur.load", caught.exception.field)
        self.assertEqual(0, caught.exception.mint_attempts)
        self.assertEqual(0, caught.exception.post_attempts)

    def test_imprimatur_runner_failure_refuses(self):
        for failure in (RuntimeError("raw candidate"), SystemExit("runner aborted")):
            with self.subTest(failure=type(failure).__name__):
                self.assert_refused(
                    valid_document(),
                    "GIP152",
                    "gates.imprimatur.run",
                    runner=lambda _text, failure=failure: (_ for _ in ()).throw(failure),
                )

    def test_imprimatur_defect_refuses(self):
        self.assert_refused(
            valid_document(),
            "GIP151",
            "gates.imprimatur.defects",
            runner=lambda _text: {"defects": 1},
        )

    def test_exact_issue_855_is_digest_pinned_and_refused_before_authority(self):
        title = (FIXTURES / "issue-855-title.txt").read_text(encoding="utf-8").removesuffix("\n")
        body = (FIXTURES / "issue-855-body.txt").read_text(encoding="utf-8")
        source = json.loads((FIXTURES / "issue-855-source.json").read_text(encoding="utf-8"))
        self.assertEqual(source["title_sha256"], hashlib.sha256(title.encode()).hexdigest())
        self.assertEqual(source["body_sha256"], hashlib.sha256(body.encode()).hexdigest())
        self.assertEqual(source["candidate_sha256"], candidate_sha256(title, body))
        document = valid_document(
            title=title,
            body=body,
            title_prefix="framework-51",
            body_opening="",
            host_structure=["## What it looks like", "## Why it matters beyond one PR"],
            protected_inventory=[
                "framework-51",
                "shoggoth-wildcat-labs",
                "## What it looks like",
                "wildcat-finance/skills#853",
                "## Why it matters beyond one PR",
                "HOST_PR_LOGINS",
            ],
        )
        document["gates"] = []
        self.assert_refused(document, "GIP130", "queue.body_opening")

    def test_issue_855_prose_is_rejected_by_in_service_imprimatur(self):
        title = (FIXTURES / "issue-855-title.txt").read_text(encoding="utf-8").removesuffix("\n")
        original = (FIXTURES / "issue-855-body.txt").read_text(encoding="utf-8")
        body = issue_body(FRAMEWORK_OPENING, original)
        document = valid_document(
            title=title,
            body=body,
            title_prefix="framework-51",
            host_structure=["## What it looks like", "## Why it matters beyond one PR"],
            protected_inventory=[
                "framework-51",
                FRAMEWORK_OPENING,
                "shoggoth-wildcat-labs",
                "## What it looks like",
                "## Why it matters beyond one PR",
                "HOST_PR_LOGINS",
            ],
        )
        lint = default_imprimatur(f"{title}\n\n{body}")
        self.assertIn(
            ("structural_metaphor", "load-bearing"),
            {(hit["family"], hit["term"]) for hit in lint["hits"]},
        )
        with self.assertRaises(PublisherError) as caught:
            admit_request(encoded(document))
        self.assertEqual("GIP151", caught.exception.code)
        self.assertEqual("gates.imprimatur.defects", caught.exception.field)
        self.assertEqual(0, caught.exception.mint_attempts)
        self.assertEqual(0, caught.exception.post_attempts)

    def test_gate_order_is_closed(self):
        document = valid_document()
        document["gates"][0], document["gates"][1] = document["gates"][1], document["gates"][0]
        self.assert_refused(document, "GIP120", "gates.sapheneia")

    def test_gate_count_is_closed(self):
        for gates in ([], valid_document()["gates"][:3], valid_document()["gates"] * 2):
            with self.subTest(count=len(gates)):
                document = valid_document()
                document["gates"] = gates
                self.assert_refused(document, "GIP150", "gates")

    def test_gate_fields_are_closed(self):
        for index in range(4):
            with self.subTest(index=index, mutation="missing"):
                document = valid_document()
                document["gates"][index].pop("outcome")
                self.assert_refused(document, "GIP120")
            with self.subTest(index=index, mutation="extra"):
                document = valid_document()
                document["gates"][index]["note"] = "unchecked"
                self.assert_refused(document, "GIP120")

    def test_gate_versions_are_pinned(self):
        for index in range(4):
            with self.subTest(index=index):
                document = valid_document()
                document["gates"][index]["version"] = "99.0.0"
                self.assert_refused(document, "GIP150")

    def test_sapheneia_source_and_candidate_are_bound(self):
        for key in ("source_sha256", "candidate_sha256", "frozen_sha256"):
            with self.subTest(key=key):
                document = valid_document()
                document["gates"][0][key] = "0" * 64
                self.assert_refused(document, "GIP150", "gates.sapheneia")

    def test_vulgate_source_candidate_and_frozen_are_bound(self):
        for key in ("source_sha256", "candidate_sha256", "frozen_sha256"):
            with self.subTest(key=key):
                document = valid_document()
                document["gates"][2][key] = "0" * 64
                self.assert_refused(document, "GIP150", "gates.vulgate")

    def test_judgement_check_lists_are_exact_and_ordered(self):
        for index in (0, 2):
            with self.subTest(index=index):
                document = valid_document()
                document["gates"][index]["checks"] = list(reversed(document["gates"][index]["checks"]))
                self.assert_refused(document, "GIP150")

    def test_each_gate_subject_is_bound(self):
        for index, key in ((0, "subject_sha256"), (1, "subject_sha256"), (2, "subject_sha256"), (3, "subject_sha256")):
            with self.subTest(index=index):
                document = valid_document()
                document["gates"][index][key] = "0" * 64
                self.assert_refused(document, "GIP150")

    def test_gate_outcomes_fail_closed(self):
        for index in range(4):
            with self.subTest(index=index):
                document = valid_document()
                document["gates"][index]["outcome"] = "failed"
                self.assert_refused(document, "GIP150")

    def test_candidate_mutation_breaks_digest_chain(self):
        document = valid_document()
        document["final_candidate"]["body"] += "\nChanged after the record."
        document["authority"]["subject_sha256"] = candidate_sha256(
            document["final_candidate"]["title"], document["final_candidate"]["body"]
        )
        self.assert_refused(document, "GIP150", "gates.vulgate")

    def test_authority_is_bound_to_final_candidate(self):
        document = valid_document()
        document["authority"]["subject_sha256"] = "0" * 64
        self.assert_refused(document, "GIP160", "authority")

    def test_recorded_authority_is_not_promoted_to_proof(self):
        document = valid_document()
        document["authority"]["outcome"] = "proved"
        self.assert_refused(document, "GIP160", "authority")

    def test_queue_forms(self):
        fixture = json.loads((FIXTURES / "queue-cases.json").read_text(encoding="utf-8"))
        self.assertEqual("github-issue-publisher-queue-cases/v1", fixture["schema"])
        self.assertEqual(4, len(fixture["cases"]))
        for case in fixture["cases"]:
            queue = case["queue"]
            prefix = case["prefix"]
            labels = case["labels"]
            with self.subTest(queue=queue):
                title = f"{prefix}: checked publication boundary"
                opening = case["body_opening"]
                body = issue_body(
                    opening,
                    "## Status\n\nThe publisher preserves exact bytes and credential evidence.",
                )
                document = valid_document(
                    title=title,
                    body=body,
                    queue=queue,
                    labels=labels,
                    title_prefix=prefix,
                    body_opening=opening,
                    protected_inventory=(
                        [
                            prefix,
                            opening,
                            "## Status",
                            "exact bytes",
                            "credential",
                            "Fiat-Required: 1",
                            CARRYOVER_ROW,
                        ]
                        if opening
                        else [
                            prefix,
                            "## Status",
                            "exact bytes",
                            "credential",
                            "Fiat-Required: 1",
                            CARRYOVER_ROW,
                        ]
                    ),
                )
                result = admit_request(encoded(document), imprimatur_runner=lambda _text: {"defects": 0})
                self.assertEqual(queue, result.queue)

        glued = valid_document(body=f"{FRAMEWORK_OPENING}continued without a line boundary")
        self.assert_refused(glued, "GIP141", "frozen.body_opening")
        blank_title = valid_document(title="framework-56:   ")
        self.assert_refused(blank_title, "GIP141", "frozen.title_prefix")

    def test_framework_cannot_pose_as_skill_queue(self):
        document = valid_document(
            title="framework-7: wrong queue",
            body="## Status\n\nExact bytes remain present.",
            queue="wish",
            labels=["wish"],
            title_prefix="framework-7",
            body_opening="",
            protected_inventory=["framework-7", "## Status", "Exact bytes"],
        )
        self.assert_refused(document, "GIP130", "queue.skill")

    def test_labels_are_sorted_unique_and_queue_bound(self):
        cases = (
            (["origin:ai", "observation"], "GIP131"),
            (["observation", "observation"], "GIP131"),
            (["origin:ai"], "GIP130"),
            (["held-job", "observation", "origin:ai"], "GIP130"),
        )
        for labels, code in cases:
            with self.subTest(labels=labels):
                self.assert_refused(valid_document(labels=labels), code)

    def test_frozen_inventory_must_survive_every_stage(self):
        document = valid_document()
        document["sapheneia_candidate"]["body"] = document["sapheneia_candidate"]["body"].replace(
            "exact bytes", "the candidate"
        )
        self.assert_refused(document, "GIP141", "frozen.protected_inventory")

    def test_request_rejects_unknown_top_level_field(self):
        document = valid_document()
        document["endpoint"] = "https://example.invalid"
        self.assert_refused(document, "GIP120", "request")

    def test_request_requires_every_top_level_field(self):
        for key in valid_document():
            with self.subTest(key=key):
                document = valid_document()
                document.pop(key)
                self.assert_refused(document, "GIP120", "request")

    def test_request_pins_schema_operation_and_repository(self):
        for key in ("schema", "operation", "repository"):
            with self.subTest(key=key):
                document = valid_document()
                document[key] = "future-value"
                self.assert_refused(document, "GIP120", f"request.{key}")

    def test_candidate_shape_is_closed(self):
        for name in ("source", "sapheneia_candidate", "final_candidate"):
            with self.subTest(name=name, mutation="missing"):
                document = valid_document()
                document[name].pop("body")
                self.assert_refused(document, "GIP120", name)
            with self.subTest(name=name, mutation="extra"):
                document = valid_document()
                document[name]["path"] = "fw51.md"
                self.assert_refused(document, "GIP120", name)
            with self.subTest(name=name, mutation="schema"):
                document = valid_document()
                document[name]["schema"] = "github-issue-candidate/v2"
                self.assert_refused(document, "GIP120", f"{name}.schema")

    def test_request_rejects_duplicate_json_name(self):
        self.assert_refused(b'{"schema":"a","schema":"b"}', "GIP102", "request.duplicate")

    def test_request_rejects_invalid_utf8(self):
        self.assert_refused(b"\xff", "GIP101", "request.utf8")
        for surrogate in ("\ud800", "\udfff"):
            with self.subTest(surrogate=ascii(surrogate)):
                document = valid_document()
                document["source"]["body"] += surrogate
                self.assert_refused(document, "GIP103", "request.string")

    def test_request_requires_canonical_json(self):
        raw = json.dumps(valid_document(), indent=2).encode("utf-8")
        self.assert_refused(raw, "GIP104", "request.canonical")

    def test_request_rejects_float_and_boolean_as_defect_count(self):
        raw = encoded(valid_document()).replace(b'"defects":0', b'"defects":0.0', 1)
        self.assert_refused(raw, "GIP103", "request.number")
        document = valid_document()
        document["gates"][1]["defects"] = False
        self.assert_refused(document, "GIP150", "gates.imprimatur")
        document = valid_document()
        document["gates"][1]["defects"] = -1
        self.assert_refused(document, "GIP150", "gates.imprimatur")

    def test_request_rejects_null_and_excessive_depth(self):
        document = valid_document()
        document["source"] = None
        self.assert_refused(document, "GIP120", "source")
        nested: object = "leaf"
        for _ in range(10):
            nested = [nested]
        raw_document = valid_document()
        raw_document["extra"] = nested
        self.assert_refused(encoded(raw_document), "GIP103", "request.depth")

    def test_request_rejects_member_and_byte_caps(self):
        raw_document = {f"field-{index}": index for index in range(257)}
        self.assert_refused(encoded(raw_document), "GIP103", "request.members")
        at_string_limit = {"x" * MAX_STRING_BYTES: 0}
        self.assertEqual(at_string_limit, parse_json_bytes(encoded(at_string_limit)))
        above_string_limit = {"x" * (MAX_STRING_BYTES + 1): 0}
        self.assert_refused(
            encoded(above_string_limit), "GIP103", "request.string"
        )
        self.assert_refused(b"{" + b" " * (1 << 20), "GIP100", "request.bytes")

    def test_text_must_be_nfc_and_control_free(self):
        document = valid_document()
        document["source"]["title"] = "framework-56: cafe\u0301"
        self.assert_refused(document, "GIP110", "source.title")
        document = valid_document()
        document["source"]["body"] += "\u202e"
        self.assert_refused(document, "GIP110", "source.body")

    def test_title_rejects_nonprinting_unicode_before_imprimatur(self):
        controller = PLUGIN_ROOT / "skills" / "fiat" / "scripts" / "hexctl.py"
        specification = importlib.util.spec_from_file_location(
            "hexctl_nonprinting_title_contract", controller
        )
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        for character in ("\u00a0", "\u2028", "\u2029"):
            with self.subTest(codepoint=f"U+{ord(character):04X}"):
                title = f"framework-56: checked{character}publication boundary"
                document = valid_document(title=title)
                _, faults = module.issue_publication_contract_faults(
                    title,
                    document["labels"],
                    document["final_candidate"]["body"],
                    "nonprinting-title request",
                )
                self.assertTrue(
                    any("title contains a control character" in fault for fault in faults)
                )
                calls: list[str] = []
                self.assert_refused(
                    document,
                    "GIP110",
                    "source.title",
                    runner=lambda text: calls.append(text) or {"defects": 0},
                )
                self.assertEqual([], calls)

    def test_frozen_shape_is_closed_and_nonempty(self):
        document = valid_document()
        document["frozen"]["path"] = "fw51.md"
        self.assert_refused(document, "GIP120", "frozen")
        for key in ("host_structure", "protected_inventory"):
            with self.subTest(key=key):
                document = valid_document()
                document["frozen"][key] = []
                self.assert_refused(document, "GIP140", "frozen.items")

    def test_frozen_items_are_unique(self):
        document = valid_document()
        document["frozen"]["host_structure"] *= 2
        self.assert_refused(document, "GIP140", "frozen.duplicate")

    def test_authority_shape_is_closed(self):
        document = valid_document()
        document["authority"]["proven"] = True
        self.assert_refused(document, "GIP120", "authority")

    def test_rejection_fixture_names_the_required_regressions(self):
        fixture = json.loads((FIXTURES / "rejection-cases.json").read_text(encoding="utf-8"))
        self.assertEqual("github-issue-publisher-rejection-cases/v1", fixture["schema"])
        self.assertEqual(
            {
                "issue-855-missing-framework-opening",
                "missing-gate",
                "failed-gate",
                "reordered-gate",
                "gate-subject-mismatch",
                "imprimatur-defect",
                "authority-subject-mismatch",
                "missing-fiat-required",
                "missing-carryover",
                "noncanonical-title",
                "decision-label-mismatch",
            },
            {case["id"] for case in fixture["cases"]},
        )

    def test_bounded_file_refuses_symlink_and_hardlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular = root / "request.json"
            regular.write_bytes(encoded(valid_document()))
            link = root / "link.json"
            link.symlink_to(regular)
            with self.assertRaises(PublisherError) as caught:
                read_bounded_file(link)
            self.assertEqual("GIP105", caught.exception.code)
            hard = root / "hard.json"
            os.link(regular, hard)
            with self.assertRaises(PublisherError) as caught:
                read_bounded_file(regular)
            self.assertEqual("GIP105", caught.exception.code)

    def test_bounded_file_refuses_non_regular_input(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PublisherError) as caught:
                read_bounded_file(directory)
            self.assertEqual("GIP105", caught.exception.code)

    def test_cli_has_no_partial_publication_operation(self):
        completed = subprocess.run(
            [sys.executable, str(CLI)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertEqual(b"", completed.stdout)
        diagnostic = json.loads(completed.stderr)
        self.assertEqual("GIP199", diagnostic["code"])
        self.assertEqual(0, diagnostic["mint_attempts"])
        self.assertEqual(0, diagnostic["post_attempts"])

    def test_selected_conformance_resolvers_emit_closed_reports(self):
        values = {
            "ordered-admission-chain": (True, "boolean"),
            "request-work-bound": (MAX_JSON_MEMBERS, "count"),
            "request-byte-bound": (MAX_REQUEST_BYTES, "bytes"),
            "signer-and-post-boundary": (True, "boolean"),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture_root = (
                root
                / "plugins/hexaemeron/tests/fixtures/github-issue-publisher-v1"
            )
            shutil.copytree(FIXTURES, fixture_root)
            report_root = root / ".hexaemeron/design-reports"
            report_root.mkdir(parents=True)
            for criterion, (value, unit) in values.items():
                with self.subTest(criterion=criterion):
                    report_path = (
                        ".hexaemeron/design-reports/"
                        f"isolated-publisher-{criterion}.json"
                    )
                    arguments = [
                        sys.executable,
                        str(CLI),
                        "conformance",
                        "--manifest",
                        "plugins/hexaemeron/tests/fixtures/"
                        "github-issue-publisher-v1/manifest.json",
                        "--design-candidate",
                        "isolated-publisher",
                        "--design-criterion",
                        criterion,
                        "--design-report",
                        report_path,
                    ]
                    completed = subprocess.run(
                        arguments,
                        cwd=root,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=10,
                        check=False,
                    )
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    self.assertEqual(b"", completed.stderr)
                    report_bytes = (root / report_path).read_bytes()
                    self.assertEqual(completed.stdout, report_bytes)
                    report = json.loads(report_bytes)
                    self.assertEqual(
                        {
                            "schema",
                            "candidate",
                            "criterion",
                            "value",
                            "unit",
                            "command",
                            "exit",
                        },
                        set(report),
                    )
                    self.assertEqual("protasis-design-report/v1", report["schema"])
                    self.assertEqual("isolated-publisher", report["candidate"])
                    self.assertEqual(criterion, report["criterion"])
                    self.assertEqual(value, report["value"])
                    self.assertEqual(unit, report["unit"])
                    self.assertEqual(0, report["exit"])
                    self.assertEqual(
                        "python3 plugins/hexaemeron/skills/phylax/scripts/"
                        "github_issue_publisher.py conformance --manifest "
                        "plugins/hexaemeron/tests/fixtures/"
                        "github-issue-publisher-v1/manifest.json "
                        "--design-candidate isolated-publisher "
                        f"--design-criterion {criterion} "
                        f"--design-report {report_path}",
                        report["command"],
                    )
                    self.assertEqual(canonical_json(report) + b"\n", report_bytes)

    def test_conformance_refuses_changed_fixture_without_a_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture_root = (
                root
                / "plugins/hexaemeron/tests/fixtures/github-issue-publisher-v1"
            )
            shutil.copytree(FIXTURES, fixture_root)
            changed = fixture_root / "valid-request.json"
            changed.write_bytes(changed.read_bytes() + b" ")
            report = (
                root
                / ".hexaemeron/design-reports/"
                "isolated-publisher-ordered-admission-chain.json"
            )
            report.parent.mkdir(parents=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "conformance",
                    "--manifest",
                    "plugins/hexaemeron/tests/fixtures/"
                    "github-issue-publisher-v1/manifest.json",
                    "--design-candidate",
                    "isolated-publisher",
                    "--design-criterion",
                    "ordered-admission-chain",
                    "--design-report",
                    ".hexaemeron/design-reports/"
                    "isolated-publisher-ordered-admission-chain.json",
                ],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertEqual(b"", completed.stdout)
            diagnostic = json.loads(completed.stderr)
            self.assertEqual("GIP199", diagnostic["code"])
            self.assertEqual("conformance.fixture", diagnostic["field"])
            self.assertEqual(0, diagnostic["mint_attempts"])
            self.assertEqual(0, diagnostic["post_attempts"])
            self.assertFalse(report.exists())

    def test_conformance_report_refuses_an_intermediate_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "work"
            outside = Path(directory) / "outside"
            fixture_root = (
                root
                / "plugins/hexaemeron/tests/fixtures/github-issue-publisher-v1"
            )
            shutil.copytree(FIXTURES, fixture_root)
            (outside / "design-reports").mkdir(parents=True)
            (root / ".hexaemeron").symlink_to(outside, target_is_directory=True)
            report = (
                outside
                / "design-reports/isolated-publisher-ordered-admission-chain.json"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "conformance",
                    "--manifest",
                    "plugins/hexaemeron/tests/fixtures/"
                    "github-issue-publisher-v1/manifest.json",
                    "--design-candidate",
                    "isolated-publisher",
                    "--design-criterion",
                    "ordered-admission-chain",
                    "--design-report",
                    ".hexaemeron/design-reports/"
                    "isolated-publisher-ordered-admission-chain.json",
                ],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertEqual(b"", completed.stdout)
            diagnostic = json.loads(completed.stderr)
            self.assertEqual("GIP199", diagnostic["code"])
            self.assertEqual("conformance.report", diagnostic["field"])
            self.assertEqual(0, diagnostic["mint_attempts"])
            self.assertEqual(0, diagnostic["post_attempts"])
            self.assertFalse(report.exists())

    def test_conformance_checks_policy_refusals_instead_of_only_fixture_names(self):
        manifest = publisher_cli.read_bounded_file(publisher_cli.MANIFEST_PATH)
        files = publisher_cli._closed_manifest(manifest)
        fixtures = publisher_cli._fixture_bytes(Path(publisher_cli.MANIFEST_PATH).parent, files)

        class Bypass:
            mint_attempts = 0
            post_attempts = 0
            gate_versions = ("0.3.0", "2.3.0", "1.1.0", "2.3.0")

        with (
            mock.patch.object(publisher_cli, "admit_request", return_value=Bypass()),
            self.assertRaises(PublisherError) as caught,
        ):
            publisher_cli._verify_fixture_contract(fixtures)
        self.assertEqual("GIP199", caught.exception.code)
        self.assertEqual("conformance.rejection-cases", caught.exception.field)

    def test_step_two_surface_is_closed_and_cli_stays_conformance_only(self):
        package = SCRIPT_DIR / "github_issue_publisher_lib"
        self.assertEqual(
            {
                "__init__.py",
                "canonical.py",
                "client.py",
                "errors.py",
                "framing.py",
                "policy.py",
                "receipts.py",
                "runtime.py",
                "server.py",
                "signer.py",
                "transport.py",
            },
            {path.name for path in package.glob("*.py")},
        )
        cli_source = CLI.read_text(encoding="utf-8")
        self.assertNotIn("urllib", cli_source)
        self.assertNotIn("http.client", cli_source)
        self.assertNotIn("subprocess", cli_source)
        self.assertNotIn("BEGIN PRIVATE KEY", cli_source)

    def test_runtime_conformance_keeps_issue_fixture_check_in_admission(self):
        manifest = publisher_cli.read_bounded_file(str(FIXTURES / "manifest.json"))
        files = publisher_cli._closed_manifest(manifest)
        fixtures = publisher_cli._fixture_bytes(FIXTURES, files)
        publisher_cli._verify_runtime_contract(fixtures)

    def test_runtime_conformance_crosses_the_production_signer_adapter(self):
        manifest = publisher_cli.read_bounded_file(str(FIXTURES / "manifest.json"))
        files = publisher_cli._closed_manifest(manifest)
        fixtures = publisher_cli._fixture_bytes(FIXTURES, files)
        original = publisher_signer.OpenSSLSigner.sign
        calls: list[bytes] = []

        def observed(signer, signing_input, *, timeout_seconds):
            calls.append(bytes(signing_input))
            return original(
                signer,
                signing_input,
                timeout_seconds=timeout_seconds,
            )

        with mock.patch.object(
            publisher_signer.OpenSSLSigner,
            "sign",
            new=observed,
        ):
            publisher_cli._verify_runtime_contract(fixtures)
        self.assertEqual(1, len(calls))

    def test_runtime_conformance_pins_the_production_destination(self):
        manifest = publisher_cli.read_bounded_file(str(FIXTURES / "manifest.json"))
        files = publisher_cli._closed_manifest(manifest)
        fixtures = publisher_cli._fixture_bytes(FIXTURES, files)
        with (
            mock.patch.object(publisher_cli, "GITHUB_API_HOST", "example.invalid"),
            self.assertRaises(PublisherError) as caught,
        ):
            publisher_cli._verify_runtime_contract(fixtures)
        self.assertEqual("GIP199", caught.exception.code)
        self.assertEqual("conformance.runtime.constants", caught.exception.field)


class ContractTests(unittest.TestCase):
    def test_tracked_specifications_match_receipted_sources(self):
        root = PLUGIN_ROOT.parents[1]
        durable = root / "docs/phylax-github-issue-publisher"
        expected = {
            "study.md": "45981759eb011b4c82515127b3124d792342ab03903e7a0a8c8f53fc50f78706",
            "runbook.md": "0e6a4fc2cdc805cfded6f3a8dac88ad8563c0319d397a6cff4ace998acf5d583",
            "design-evidence.json": "d74fd663f1ec76d8169fe3bfa536749d3440127b3e00ec3bd2c6894ae0280587",
            "design-topology.json": "bf373194c7c1dae82bfbe5e6ccdfeca612677b0d59d02c268bb675542fa66716",
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(
                    digest,
                    hashlib.sha256((durable / name).read_bytes()).hexdigest(),
                )

        evidence = json.loads((durable / "design-evidence.json").read_text())
        resolved = [
            result for result in evidence["results"]
            if isinstance(result["report"], dict)
        ]
        self.assertEqual(20, len(resolved))
        for result in resolved:
            report = result["report"]
            with self.subTest(report=report["path"]):
                self.assertEqual(
                    report["sha256"],
                    hashlib.sha256((durable / report["path"]).read_bytes()).hexdigest(),
                )

    def test_reference_names_judgement_and_live_deployment_limits(self):
        reference = (
            PLUGIN_ROOT / "skills/phylax/references/github-issue-publisher-v1.md"
        ).read_text(encoding="utf-8")
        self.assertIn("They do not establish factual truth", reference)
        self.assertIn("live_isolation: not-established", reference)
        self.assertIn("Admission is a necessary input", reference)
        self.assertIn("github-issue-publisher-admission-manifest/v1", reference)
        self.assertIn("signer-and-post-boundary", reference)
        self.assertIn("retains at most 4,097 stdout bytes", reference)
        self.assertIn("create-indeterminate", reference)
        self.assertIn("cannot appear as a zero-attempt refusal", reference)
        self.assertIn("repository suite makes no live network call", reference)
        self.assertIn("version `0.3.0`", reference)
        self.assertNotIn("ADR-054", reference)

    def test_adr_rejects_same_identity_and_file_watcher_routes(self):
        adr = (
            PLUGIN_ROOT.parents[1]
            / "docs/decisions/drafts/use-a-credential-owning-github-issue-publisher.md"
        ).read_text(encoding="utf-8")
        self.assertIn("adr/use-a-credential-owning-github-issue-publisher", adr)
        self.assertIn("selected `isolated-publisher` design", adr)
        self.assertIn("### Add checks to the shell helper", adr)
        self.assertIn("### Watch `fw51.md`", adr)
        self.assertIn("### Run a same-UID broker", adr)
        self.assertIn("dedicated non-login account", adr)
        self.assertIn(
            "Step 1 establishes neither live deployment nor live isolation",
            adr,
        )
        self.assertIn("Step 2 establishes those component paths with injected", adr)
        self.assertIn("macOS peer-credential ABI", adr)
        self.assertNotIn("ADR-054", adr)


if __name__ == "__main__":
    unittest.main()
