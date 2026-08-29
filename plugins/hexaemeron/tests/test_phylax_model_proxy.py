"""Cause-level guards for the version-1 model proxy policy and framing core."""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import ssl
import subprocess
import struct
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = PLUGIN_ROOT / "skills" / "phylax" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "model-proxy-v1"
CLI = SCRIPT_DIR / "model_proxy.py"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from model_proxy_lib import (  # noqa: E402
    FEATURE_NAMES,
    LIMIT_FIELDS,
    LOOPBACK_TEXT_V1,
    MAX_ACCEPTED_JOB_BYTES,
    POLICY_SCHEMA,
    PolicyError,
    canonical_json,
    compile_policy,
    compile_policy_file,
    parse_json_bytes,
    resolve_profile,
    sha256_bytes,
    verify_golden,
)
import model_proxy_lib.conformance as conformance  # noqa: E402
from model_proxy_lib.conformance import (  # noqa: E402
    CONFORMANCE_MANIFEST_SCHEMA,
    CONFORMANCE_RESULT_SCHEMA,
    DEPENDENCY_BOUNDARIES,
    EXPECTED_ROWS,
    POSITIVE_SURFACES,
    ConformanceRowResult,
    check_conformance_manifest,
    conformance_manifest_digest,
)
from model_proxy_lib.framing import (  # noqa: E402
    FRAME_EVENT_SCHEMA,
    FRAMING_MANIFEST_SCHEMA,
    REQUEST_SCHEMA,
    RESPONSE_SCHEMA,
    TEXT_OPERATION,
    FramingCore,
    TextRequest,
    check_framing_manifest,
)
from model_proxy_lib.lifecycle import (  # noqa: E402
    LIFECYCLE_MANIFEST_SCHEMA,
    NANOSECONDS_PER_SECOND,
    LifecycleController,
    ModelProxyRuntime,
    check_lifecycle_manifest,
)
from model_proxy_lib.operator import render_operator_text  # noqa: E402
from model_proxy_lib.provider import (  # noqa: E402
    PROVIDER_EVENT_SCHEMA,
    PROVIDER_MANIFEST_SCHEMA,
    ProviderEvent,
    ProviderSession,
    check_provider_manifest,
)
from model_proxy_lib.receipts import RECEIPT_SCHEMA, ReceiptSink  # noqa: E402
from model_proxy_lib.transport import (  # noqa: E402
    READ_CHUNK_BYTES,
    HTTPSConnector,
    HTTPSRequest,
)


def accepted_document() -> dict[str, object]:
    return json.loads((FIXTURES / "accepted-job.json").read_text(encoding="utf-8"))


def jobspec_document(accepted: dict[str, object] | None = None) -> dict[str, object]:
    document = accepted_document() if accepted is None else accepted
    raw = base64.b64decode(document["jobspec_b64"], validate=True)
    return json.loads(raw.decode("utf-8"))


def encode_document(document: dict[str, object]) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        + b"\n"
    )


def with_jobspec(
    mutate,
    *,
    accepted: dict[str, object] | None = None,
    update_digest: bool = True,
) -> bytes:
    evidence = deepcopy(accepted_document() if accepted is None else accepted)
    jobspec = jobspec_document(evidence)
    mutate(jobspec)
    raw = encode_document(jobspec)
    evidence["jobspec_b64"] = base64.b64encode(raw).decode("ascii")
    if update_digest:
        evidence["jobspec_sha256"] = sha256_bytes(raw)
    return encode_document(evidence)


def with_raw_jobspec(raw: bytes) -> bytes:
    evidence = accepted_document()
    evidence["jobspec_b64"] = base64.b64encode(raw).decode("ascii")
    evidence["jobspec_sha256"] = sha256_bytes(raw)
    return encode_document(evidence)


def leaf_variants(value, path=()):
    if isinstance(value, dict):
        for key in sorted(value):
            for variant, child_path in leaf_variants(value[key], path + (key,)):
                changed = deepcopy(value)
                changed[key] = variant
                yield changed, child_path
    elif isinstance(value, list):
        changed = list(reversed(value))
        if changed == value:
            changed.append("digest-variant")
        yield changed, path
    elif isinstance(value, bool):
        yield not value, path
    elif isinstance(value, int):
        yield value + 1, path
    elif isinstance(value, str):
        yield value + "-digest-variant", path


def request_frame(
    input_text: object = "hello",
    *,
    schema: object = REQUEST_SCHEMA,
    operation: object = TEXT_OPERATION,
    extra: dict[str, object] | None = None,
) -> bytes:
    document: dict[str, object] = {
        "schema": schema,
        "operation": operation,
        "input": input_text,
    }
    if extra:
        document.update(extra)
    payload = json.dumps(
        document,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return struct.pack(">I", len(payload)) + payload


def raw_frame(payload: bytes, *, declared: int | None = None) -> bytes:
    length = len(payload) if declared is None else declared
    return struct.pack(">I", length) + payload


def synthetic_provider_response(
    input_text: str,
    output: object,
    *,
    schema: object = "synthetic-provider-response/v1",
    usage: object | None = None,
    extra: dict[str, object] | None = None,
) -> bytes:
    if usage is None:
        usage = {
            "input_tokens": len(input_text),
            "output_tokens": len(output) if isinstance(output, str) else 0,
        }
    document: dict[str, object] = {
        "schema": schema,
        "output": output,
        "usage": usage,
    }
    if extra:
        document.update(extra)
    return canonical_json(document)


class BufferedHTTPSResponse:
    def __init__(
        self,
        body: bytes,
        *,
        status: object = 200,
        headers: tuple[tuple[str, str], ...] | None = None,
        peer_address: object = "8.8.8.8",
        oversized_read: bool = False,
    ):
        self.status = status
        self.headers = (
            (
                ("Content-Length", str(len(body))),
                ("Content-Type", "application/json"),
            )
            if headers is None
            else headers
        )
        self.peer_address = peer_address
        self.body = body
        self.position = 0
        self.closed = False
        self.reads = 0
        self.read_sizes: list[int] = []
        self.oversized_read = oversized_read

    def read(self, size: int) -> bytes:
        self.reads += 1
        self.read_sizes.append(size)
        take = size + 1 if self.oversized_read else size
        chunk = self.body[self.position : self.position + take]
        self.position += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


class HTTPSExchangeFixture:
    def __init__(self, response=None, *, error: Exception | None = None):
        self.response = response
        self.error = error
        self.requests: list[HTTPSRequest] = []

    def __call__(self, request: HTTPSRequest, _context, _timeout):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.response


class PolicyCompilerTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.accepted_bytes = (FIXTURES / "accepted-job.json").read_bytes()
        self.expected_bytes = (FIXTURES / "policy.json").read_bytes()
        self.expected_digest = (FIXTURES / "policy.sha256").read_text(
            encoding="ascii"
        ).strip()

    def assert_refused(self, data: bytes, code: str) -> PolicyError:
        with self.assertRaises(PolicyError) as caught:
            compile_policy(data)
        self.assertEqual(code, caught.exception.code)
        self.assertEqual(
            set(caught.exception.diagnostic()),
            {"schema", "outcome", "code", "field"},
        )
        return caught.exception

    def mutate_jobspec(self, path: tuple[str, ...], value) -> bytes:
        def mutate(document):
            target = document
            for name in path[:-1]:
                target = target[name]
            target[path[-1]] = value

        return with_jobspec(mutate)

    def test_golden_accepted_job_compiles_to_exact_policy_and_digest(self):
        result = compile_policy(self.accepted_bytes)
        self.assertEqual(self.expected_bytes, result.policy_bytes + b"\n")
        self.assertEqual(self.expected_digest, result.policy_sha256)
        self.assertEqual(POLICY_SCHEMA, result.document["schema"])
        self.assertEqual(
            accepted_document()["jobspec_sha256"], result.jobspec_sha256
        )

    def test_golden_jobspec_bytes_are_the_digest_bound_payload(self):
        evidence = accepted_document()
        raw = base64.b64decode(evidence["jobspec_b64"], validate=True)
        self.assertEqual((FIXTURES / "jobspec.json").read_bytes(), raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence["jobspec_sha256"])

    def test_cli_emits_exact_policy_and_credential_free_success_diagnostic(self):
        result = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
            [
                sys.executable,
                str(CLI),
                "compile-policy",
                "--accepted-job",
                str(FIXTURES / "accepted-job.json"),
                "--expect",
                str(FIXTURES / "policy.json"),
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(self.expected_bytes, result.stdout)
        diagnostic = json.loads(result.stderr)
        self.assertEqual(
            {
                "schema",
                "outcome",
                "policy_schema",
                "profile",
                "jobspec_sha256",
                "policy_sha256",
            },
            set(diagnostic),
        )
        self.assertNotIn("fiat-700-policy-golden", result.stderr.decode("utf-8"))

    def test_cli_argument_refusal_is_value_free_and_does_not_abbreviate(self):
        sentinel = "fiat-700-cli-secret-canary"
        cases = (
            ("--credential", sentinel),
            ("--accepted", str(FIXTURES / "accepted-job.json")),
        )
        for option, value in cases:
            with self.subTest(option=option):
                result = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
                    [
                        sys.executable,
                        str(CLI),
                        "compile-policy",
                        option,
                        value,
                    ],
                    check=False,
                    capture_output=True,
                )
                self.assertEqual(2, result.returncode)
                self.assertEqual(b"", result.stdout)
                self.assertNotIn(value.encode("utf-8"), result.stderr)
                try:
                    diagnostic = json.loads(result.stderr)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    diagnostic = None
                self.assertEqual(
                    {
                        "schema": "model-proxy-diagnostic/v1",
                        "outcome": "refused",
                        "code": "MP122",
                        "field": "cli.arguments",
                    },
                    diagnostic,
                )

    def test_root_key_order_does_not_change_compiled_policy_bytes(self):
        evidence = accepted_document()
        reversed_evidence = dict(reversed(list(evidence.items())))
        raw = json.dumps(
            reversed_evidence,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("ascii") + b"\n"
        result = compile_policy(raw)
        self.assertEqual(self.expected_bytes, result.policy_bytes + b"\n")

    def test_policy_key_order_does_not_change_canonical_bytes(self):
        policy = compile_policy(self.accepted_bytes).document
        reordered = dict(reversed(list(policy.items())))
        self.assertEqual(canonical_json(policy), canonical_json(reordered))

    def test_canonical_json_refuses_non_string_object_names(self):
        try:
            canonical_json({1: "value"})
        except Exception as error:  # parent evidence may be the wrong exception class
            caught = error
        else:
            caught = None
        self.assertIsInstance(caught, PolicyError)
        self.assertEqual("MP109", caught.code)
        self.assertEqual("json.key", caught.field)

    def test_every_declared_policy_leaf_changes_its_digest(self):
        policy = compile_policy(self.accepted_bytes).document
        original = sha256_bytes(canonical_json(policy))
        paths = []
        for variant, path in leaf_variants(policy):
            paths.append(path)
            self.assertNotEqual(original, sha256_bytes(canonical_json(variant)), path)
        self.assertGreaterEqual(len(paths), 40)

    def test_policy_has_no_credential_field(self):
        policy = compile_policy(self.accepted_bytes).document
        pending = [policy]
        keys = set()
        while pending:
            current = pending.pop()
            if isinstance(current, dict):
                keys.update(current)
                pending.extend(current.values())
            elif isinstance(current, list):
                pending.extend(current)
        self.assertTrue(
            {"credential", "authorization", "api_key", "headers"}.isdisjoint(keys)
        )

    def test_required_root_and_nested_fields_have_no_defaults(self):
        evidence = accepted_document()
        for name in tuple(evidence):
            with self.subTest(root=name):
                candidate = deepcopy(evidence)
                del candidate[name]
                self.assert_refused(encode_document(candidate), "MP108")
        for name in LIMIT_FIELDS:
            with self.subTest(limit=name):
                self.assert_refused(
                    with_jobspec(
                        lambda document, key=name: document["model_proxy"][
                            "limits"
                        ].pop(key)
                    ),
                    "MP108",
                )

    def test_extra_fields_refuse_at_every_authority_layer(self):
        evidence = accepted_document()
        evidence["api_key"] = "canary-never-diagnostic"
        error = self.assert_refused(encode_document(evidence), "MP108")
        self.assertNotIn("canary-never-diagnostic", str(error))
        self.assert_refused(
            with_jobspec(
                lambda document: document["model_proxy"].update(
                    {"authorization": "canary-never-diagnostic"}
                )
            ),
            "MP108",
        )

    def test_duplicate_fields_refuse_at_root_and_inside_jobspec(self):
        self.assert_refused((FIXTURES / "duplicate-field.json").read_bytes(), "MP105")
        raw = (FIXTURES / "jobspec.json").read_text(encoding="utf-8")
        duplicate = raw.replace(
            '"model":"fixture-text-1"',
            '"model":"fixture-text-1","model":"fixture-text-1"',
        ).encode("utf-8")
        self.assert_refused(with_raw_jobspec(duplicate), "MP105")

    def test_null_boolean_float_negative_and_zero_limits_refuse(self):
        cases = (
            (None, "null"),
            (True, "boolean"),
            (1.5, "floating"),
            (-1, "negative"),
            (0, "zero"),
        )
        for value, label in cases:
            with self.subTest(label=label):
                self.assert_refused(
                    self.mutate_jobspec(
                        ("model_proxy", "limits", "max_requests"), value
                    ),
                    "MP109",
                )

    def test_oversized_evidence_refuses_before_parsing(self):
        self.assert_refused(b" " * (MAX_ACCEPTED_JOB_BYTES + 1), "MP101")

    def test_excessive_depth_refuses_before_parsing(self):
        self.assert_refused((FIXTURES / "excessive-depth.json").read_bytes(), "MP104")

    def test_invalid_utf8_and_invalid_unicode_refuse(self):
        self.assert_refused(b'{"schema":"\xff"}', "MP102")
        self.assert_refused((FIXTURES / "invalid-unicode.json").read_bytes(), "MP106")

    def test_non_nfc_and_format_control_strings_refuse(self):
        decomposed = "synthetic-pu\u0301blic"
        self.assert_refused(
            self.mutate_jobspec(("model_proxy", "data_class"), decomposed), "MP106"
        )
        self.assert_refused(
            self.mutate_jobspec(("model_proxy", "data_class"), "synthetic\u202epublic"),
            "MP106",
        )

    def test_stale_jobspec_digest_refuses(self):
        evidence = accepted_document()
        evidence["jobspec_sha256"] = "0" * 64
        self.assert_refused(encode_document(evidence), "MP110")

    def test_verified_identity_and_expiry_must_match_jobspec(self):
        evidence = accepted_document()
        evidence["verified"]["job_id"] = "different-job"
        self.assert_refused(encode_document(evidence), "MP110")
        evidence = accepted_document()
        evidence["verified"]["expires_at"] = "2026-08-28T12:09:59Z"
        self.assert_refused(encode_document(evidence), "MP110")

    def test_unknown_schema_refuses(self):
        evidence = accepted_document()
        evidence["schema"] = "unknown-policy-input/v1"
        self.assert_refused(encode_document(evidence), "MP111")

    def test_old_and_future_schema_versions_refuse_explicitly(self):
        for version in ("accepted-job/v0", "accepted-job/v2"):
            with self.subTest(schema=version):
                evidence = accepted_document()
                evidence["schema"] = version
                self.assert_refused(encode_document(evidence), "MP121")
        for version in ("jobspec/v0", "jobspec/v2"):
            with self.subTest(schema=version):
                self.assert_refused(
                    self.mutate_jobspec(("schema",), version), "MP121"
                )
        for version in ("model-proxy-request/v0", "model-proxy-request/v2"):
            with self.subTest(schema=version):
                self.assert_refused(
                    self.mutate_jobspec(("model_proxy", "schema"), version),
                    "MP121",
                )

    def test_unknown_old_and_future_profiles_refuse(self):
        self.assert_refused(
            self.mutate_jobspec(
                ("model_proxy", "provider_profile"), "another-provider/v1"
            ),
            "MP112",
        )
        for version in ("loopback-text/v0", "loopback-text/v2"):
            with self.subTest(profile=version):
                self.assert_refused(
                    self.mutate_jobspec(
                        ("model_proxy", "provider_profile"), version
                    ),
                    "MP121",
                )

    def test_model_and_profile_must_agree(self):
        self.assert_refused(
            self.mutate_jobspec(("model_proxy", "model"), "fixture-text-2"),
            "MP113",
        )

    def test_profile_owned_operation_and_schemas_must_agree(self):
        cases = {
            "operation": "text.stream",
            "request_schema": "provider-request/v1",
            "response_schema": "provider-response/v1",
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                self.assert_refused(
                    self.mutate_jobspec(("model_proxy", field), value), "MP113"
                )

    def test_every_provider_feature_must_be_present_and_disabled(self):
        for feature in FEATURE_NAMES:
            with self.subTest(feature=feature):
                self.assert_refused(
                    self.mutate_jobspec(
                        ("model_proxy", "features", feature), True
                    ),
                    "MP114",
                )

    def test_content_logging_and_diagnostic_consent_refuse(self):
        self.assert_refused(
            self.mutate_jobspec(("model_proxy", "content_logging"), True), "MP115"
        )
        self.assert_refused(
            self.mutate_jobspec(("model_proxy", "diagnostic_consent"), True),
            "MP116",
        )

    def test_unapproved_data_class_refuses(self):
        self.assert_refused(
            self.mutate_jobspec(("model_proxy", "data_class"), "private"),
            "MP117",
        )

    def test_invalid_and_overlong_lifetimes_refuse(self):
        evidence = accepted_document()
        evidence["verified"]["accepted_at"] = "2026-08-28T12:10:00Z"
        self.assert_refused(encode_document(evidence), "MP118")
        evidence = accepted_document()
        evidence["verified"]["expires_at"] = "2026-08-28T13:01:00Z"
        self.assert_refused(
            with_jobspec(
                lambda document: document.update(
                    {"expires_at": "2026-08-28T13:01:00Z"}
                ),
                accepted=evidence,
            ),
            "MP118",
        )
        evidence = accepted_document()
        evidence["verified"]["accepted_at"] = "not-a-time"
        self.assert_refused(encode_document(evidence), "MP118")

    def test_every_hard_limit_ceiling_refuses_excess(self):
        for name, ceiling in LOOPBACK_TEXT_V1.limit_ceilings.items():
            with self.subTest(limit=name):
                self.assert_refused(
                    self.mutate_jobspec(
                        ("model_proxy", "limits", name), ceiling + 1
                    ),
                    "MP119",
                )
        self.assert_refused(
            self.mutate_jobspec(
                ("model_proxy", "receipt_retention_seconds"), 86_401
            ),
            "MP119",
        )

    def test_aggregate_limits_cannot_be_smaller_than_one_request(self):
        pairs = (
            ("max_total_request_bytes", "max_request_bytes"),
            ("max_total_response_bytes", "max_response_bytes"),
            ("max_total_input_tokens", "max_input_tokens"),
            ("max_total_output_tokens", "max_output_tokens"),
        )
        jobspec = jobspec_document()
        for aggregate, single in pairs:
            with self.subTest(aggregate=aggregate):
                value = jobspec["model_proxy"]["limits"][single] - 1
                self.assert_refused(
                    self.mutate_jobspec(
                        ("model_proxy", "limits", aggregate), value
                    ),
                    "MP119",
                )

    def test_receipt_count_is_bounded_by_requests_plus_two(self):
        self.assert_refused(
            self.mutate_jobspec(
                ("model_proxy", "limits", "max_receipts"), 11
            ),
            "MP119",
        )

    def test_noncanonical_base64_refuses(self):
        evidence = accepted_document()
        evidence["jobspec_b64"] = evidence["jobspec_b64"] + "="
        self.assert_refused(encode_document(evidence), "MP109")

    def test_rejection_fixture_inventory_names_every_required_family(self):
        manifest = json.loads((FIXTURES / "rejections.json").read_text("utf-8"))
        self.assertEqual("model-proxy-policy-rejections/v1", manifest["schema"])
        identifiers = [case["id"] for case in manifest["cases"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(
            {
                "missing-field",
                "extra-field",
                "duplicate-field",
                "null-limit",
                "boolean-limit",
                "floating-limit",
                "negative-limit",
                "zero-limit",
                "oversized-evidence",
                "excessive-depth",
                "invalid-unicode",
                "stale-digest",
                "unknown-schema",
                "unknown-profile",
                "model-profile-disagreement",
                "feature-enabled",
                "content-log",
                "diagnostic-consent",
                "data-class",
                "lifetime",
                "hard-ceiling",
                "old-version",
                "future-version",
                "cli-arguments",
            },
            set(identifiers),
        )

    def test_profile_registry_is_closed_and_immutable(self):
        self.assertIs(LOOPBACK_TEXT_V1, resolve_profile("loopback-text/v1"))
        with self.assertRaises(FrozenInstanceError):
            LOOPBACK_TEXT_V1.model = "changed"
        with self.assertRaises(TypeError):
            LOOPBACK_TEXT_V1.limit_ceilings["max_requests"] = 1

    def test_golden_verification_refuses_byte_or_digest_drift(self):
        result = compile_policy(self.accepted_bytes)
        verify_golden(result, str(FIXTURES / "policy.json"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = root / "policy.json"
            digest = root / "policy.sha256"
            policy.write_bytes(self.expected_bytes.replace(b"fixture-text-1", b"fixture-text-2"))
            digest.write_text(self.expected_digest + "\n", encoding="ascii")
            with self.assertRaisesRegex(PolicyError, "MP120"):
                verify_golden(result, str(policy))
            policy.write_bytes(self.expected_bytes)
            digest.write_text("0" * 64 + "\n", encoding="ascii")
            with self.assertRaisesRegex(PolicyError, "MP120"):
                verify_golden(result, str(policy))

    def test_bounded_file_reader_refuses_symlink_and_oversize(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "accepted.json"
            target.write_bytes(self.accepted_bytes)
            link = root / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(PolicyError, "MP100"):
                compile_policy_file(str(link))
            target.write_bytes(b" " * (MAX_ACCEPTED_JOB_BYTES + 1))
            with self.assertRaisesRegex(PolicyError, "MP101"):
                compile_policy_file(str(target))

    def test_bounded_file_reader_refuses_fifo_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "accepted-job.fifo"
            os.mkfifo(fifo)
            try:
                result = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
                    [
                        sys.executable,
                        str(CLI),
                        "compile-policy",
                        "--accepted-job",
                        str(fifo),
                    ],
                    check=False,
                    capture_output=True,
                    timeout=2,
                )
            except subprocess.TimeoutExpired:
                result = None
            self.assertIsNotNone(
                result,
                "accepted-job FIFO blocked before the regular-file refusal",
            )
            self.assertEqual(2, result.returncode)
            self.assertEqual(b"", result.stdout)
            try:
                diagnostic = json.loads(result.stderr)
            except (UnicodeDecodeError, json.JSONDecodeError):
                diagnostic = None
            self.assertIsInstance(diagnostic, dict)
            self.assertEqual("MP100", diagnostic.get("code"))

    def test_refusal_diagnostic_never_echoes_credential_shaped_input(self):
        sentinel = "fiat-700-super-secret-canary"
        evidence = accepted_document()
        evidence["api_key"] = sentinel
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "accepted.json"
            path.write_bytes(encode_document(evidence))
            result = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
                [
                    sys.executable,
                    str(CLI),
                    "compile-policy",
                    "--accepted-job",
                    str(path),
                ],
                check=False,
                capture_output=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual(b"", result.stdout)
        self.assertNotIn(sentinel.encode("ascii"), result.stderr)
        self.assertEqual("MP108", json.loads(result.stderr)["code"])

    def test_unexpected_exception_becomes_fixed_internal_refusal(self):
        specification = importlib.util.spec_from_file_location("model_proxy_cli", CLI)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        with mock.patch.object(
            module, "compile_policy_file", side_effect=RuntimeError("secret value")
        ), mock.patch.object(module, "_write_diagnostic") as write:
            result = module.main(
                ["compile-policy", "--accepted-job", "credential-in-path"]
            )
        self.assertEqual(3, result)
        self.assertEqual(
            {
                "schema": "model-proxy-diagnostic/v1",
                "outcome": "refused",
                "code": "MP199",
                "field": "compiler.internal",
            },
            write.call_args.args[0],
        )

    def test_parser_rejects_member_and_scalar_floods(self):
        members = {f"k{index}": index for index in range(513)}
        with self.assertRaisesRegex(PolicyError, "MP101"):
            parse_json_bytes(
                encode_document(members), max_bytes=MAX_ACCEPTED_JOB_BYTES
            )
        scalars = [0] * 1_025
        with self.assertRaisesRegex(PolicyError, "MP101"):
            parse_json_bytes(
                json.dumps(scalars).encode("ascii"),
                max_bytes=MAX_ACCEPTED_JOB_BYTES,
                max_members=2_000,
            )


class FramingTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.policy = compile_policy((FIXTURES / "accepted-job.json").read_bytes())

    def assert_frame_refused(
        self, core: FramingCore, data: bytes, code: str
    ) -> PolicyError:
        with self.assertRaises(PolicyError) as caught:
            core.feed(data)
        self.assertEqual(code, caught.exception.code)
        self.assertEqual(
            {"schema", "outcome", "code", "field"},
            set(caught.exception.diagnostic()),
        )
        return caught.exception

    def test_one_byte_fragmentation_and_every_prefix_split(self):
        frame = request_frame("fragmented")
        core = FramingCore(self.policy)
        requests = []
        for byte in frame:
            requests.extend(core.feed(bytes((byte,))))
        core.finish()
        self.assertEqual(
            [(1, "fragmented")],
            [(request.sequence, request.input_text) for request in requests],
        )

        for split in range(1, 4):
            with self.subTest(prefix_split=split):
                core = FramingCore(self.policy)
                first = core.feed(frame[:split])
                second = core.feed(frame[split:])
                core.finish()
                self.assertEqual((), first)
                self.assertEqual(
                    [(1, "fragmented")],
                    [(request.sequence, request.input_text) for request in second],
                )

    def test_concatenated_frames_preserve_order_and_assign_sequence(self):
        core = FramingCore(self.policy)
        requests = core.feed(request_frame("first") + request_frame("second"))
        core.finish()
        self.assertEqual(
            [(1, "first"), (2, "second")],
            [(request.sequence, request.input_text) for request in requests],
        )

    def test_incomplete_prefix_payload_and_trailing_bytes_refuse(self):
        core = FramingCore(self.policy)
        core.feed(b"\x00\x00\x00")
        with self.assertRaisesRegex(PolicyError, "MP202"):
            core.finish()

        payload = canonical_json(
            {"schema": REQUEST_SCHEMA, "operation": TEXT_OPERATION, "input": "x"}
        )
        core = FramingCore(self.policy)
        core.feed(raw_frame(payload, declared=len(payload) + 1))
        with self.assertRaisesRegex(PolicyError, "MP203"):
            core.finish()

        core = FramingCore(self.policy)
        self.assertEqual(1, len(core.feed(request_frame("complete") + b"\x01")))
        with self.assertRaisesRegex(PolicyError, "MP202"):
            core.finish()

    def test_declared_and_actual_payload_length_must_agree(self):
        payload = canonical_json(
            {"schema": REQUEST_SCHEMA, "operation": TEXT_OPERATION, "input": "x"}
        )
        self.assert_frame_refused(
            FramingCore(self.policy),
            raw_frame(payload, declared=len(payload) - 1),
            "MP103",
        )
        core = FramingCore(self.policy)
        core.feed(raw_frame(payload, declared=len(payload) + 1))
        with self.assertRaisesRegex(PolicyError, "MP203"):
            core.finish()

    def test_zero_and_over_cap_lengths_refuse_before_payload_buffering(self):
        core = FramingCore(self.policy)
        self.assert_frame_refused(core, b"\x00\x00\x00\x00", "MP200")
        self.assertEqual(0, core.buffered_bytes)

        maximum = self.policy.document["limits"]["max_request_bytes"]
        core = FramingCore(self.policy)
        self.assert_frame_refused(core, struct.pack(">I", maximum + 1), "MP201")
        self.assertEqual(0, core.buffered_bytes)

    def test_invalid_utf8_lone_surrogate_and_duplicate_names_refuse(self):
        invalid_utf8 = (
            b'{"schema":"model-request/v1","operation":"text.generate",'
            b'"input":"\xff"}'
        )
        lone_surrogate = (
            b'{"schema":"model-request/v1","operation":"text.generate",'
            b'"input":"\\ud800"}'
        )
        duplicate = (
            b'{"schema":"model-request/v1","operation":"text.generate",'
            b'"input":"one","input":"two"}'
        )
        cases = (
            (invalid_utf8, "MP102"),
            (lone_surrogate, "MP106"),
            (duplicate, "MP105"),
        )
        for payload, code in cases:
            with self.subTest(code=code):
                self.assert_frame_refused(
                    FramingCore(self.policy), raw_frame(payload), code
                )

    def test_depth_collection_string_and_scalar_caps_refuse(self):
        excessive_depth = (
            b'{"schema":"model-request/v1","operation":"text.generate",'
            b'"input":"x","unknown":'
            + b"[" * 9
            + b"0"
            + b"]" * 9
            + b"}"
        )
        collection_flood = canonical_json(
            {
                "schema": REQUEST_SCHEMA,
                "operation": TEXT_OPERATION,
                "input": "x",
                "unknown": [[] for _ in range(61)],
            }
        )
        scalar_flood = canonical_json(
            {
                "schema": REQUEST_SCHEMA,
                "operation": TEXT_OPERATION,
                "input": "x",
                "unknown": [0 for _ in range(61)],
            }
        )
        long_string = request_frame("x" * 8_193)
        cases = (
            (raw_frame(excessive_depth), "MP104"),
            (raw_frame(collection_flood), "MP101"),
            (raw_frame(scalar_flood), "MP101"),
            (long_string, "MP101"),
        )
        for frame, code in cases:
            with self.subTest(code=code, size=len(frame)):
                self.assert_frame_refused(FramingCore(self.policy), frame, code)

    def test_closed_request_schema_refuses_missing_unknown_and_coercion(self):
        for missing in ("schema", "operation", "input"):
            with self.subTest(missing=missing):
                document = {
                    "schema": REQUEST_SCHEMA,
                    "operation": TEXT_OPERATION,
                    "input": "x",
                }
                del document[missing]
                payload = canonical_json(document)
                self.assert_frame_refused(
                    FramingCore(self.policy), raw_frame(payload), "MP206"
                )

        self.assert_frame_refused(
            FramingCore(self.policy),
            request_frame(extra={"temperature": 0}),
            "MP208",
        )
        wrong_inputs = (
            (1, "MP209"),
            (True, "MP209"),
            (None, "MP209"),
            (1.5, "MP109"),
        )
        for value, code in wrong_inputs:
            with self.subTest(input_value=value):
                self.assert_frame_refused(
                    FramingCore(self.policy), request_frame(value), code
                )

    def test_alternate_schema_versions_and_operations_refuse(self):
        schemas = (
            "model-request/v0",
            "model-request/v2",
            "provider-request/v1",
        )
        for schema in schemas:
            with self.subTest(schema=schema):
                self.assert_frame_refused(
                    FramingCore(self.policy), request_frame(schema=schema), "MP210"
                )
        for operation in ("text.stream", "chat.completions", "text.generate.batch"):
            with self.subTest(operation=operation):
                self.assert_frame_refused(
                    FramingCore(self.policy),
                    request_frame(operation=operation),
                    "MP211",
                )

    def test_guest_authority_and_every_provider_feature_refuse(self):
        forbidden = {
            "job_id",
            "sequence",
            "url",
            "method",
            "model",
            "headers",
            "remote_reference",
            "image",
            "lifecycle",
            "stream",
            "channel",
            *FEATURE_NAMES,
        }
        sentinel = "fiat-700-frame-secret-canary"
        for field in sorted(forbidden):
            with self.subTest(field=field):
                error = self.assert_frame_refused(
                    FramingCore(self.policy),
                    request_frame(extra={field: sentinel}),
                    "MP207",
                )
                self.assertNotIn(field, str(error))
                self.assertNotIn(sentinel, str(error))

    def test_input_tokens_and_request_count_are_bounded(self):
        self.assert_frame_refused(
            FramingCore(self.policy), request_frame("x" * 2_049), "MP212"
        )
        maximum = self.policy.document["limits"]["max_requests"]
        core = FramingCore(self.policy)
        combined = request_frame("x") * (maximum + 1)
        self.assert_frame_refused(core, combined, "MP217")

    def test_response_bytes_are_deterministic_and_closed(self):
        core = FramingCore(self.policy)
        request = core.feed(request_frame("ping"))[0]
        response = core.encode_response(request, "pong")
        payload = canonical_json(
            {"schema": RESPONSE_SCHEMA, "sequence": 1, "output": "pong"}
        )
        self.assertEqual(struct.pack(">I", len(payload)) + payload, response)
        self.assertEqual(len(payload), struct.unpack(">I", response[:4])[0])
        self.assertEqual(
            {"schema", "sequence", "output"},
            set(json.loads(response[4:])),
        )

        other = FramingCore(self.policy)
        other_request = other.feed(request_frame("ping"))[0]
        self.assertEqual(response, other.encode_response(other_request, "pong"))

    def test_response_type_token_unicode_and_sequence_refusals_are_bounded(self):
        core = FramingCore(self.policy)
        request = core.feed(request_frame("ping"))[0]
        with self.assertRaisesRegex(PolicyError, "MP214"):
            core.encode_response(request, 1)

        core = FramingCore(self.policy)
        request = core.feed(request_frame("ping"))[0]
        with self.assertRaisesRegex(PolicyError, "MP215"):
            core.encode_response(request, "x" * 1_025)

        core = FramingCore(self.policy)
        request = core.feed(request_frame("ping"))[0]
        with self.assertRaisesRegex(PolicyError, "MP106"):
            core.encode_response(request, "line\nbreak")

        core = FramingCore(self.policy)
        with self.assertRaisesRegex(PolicyError, "MP213"):
            core.encode_response(object(), "pong")

        first = FramingCore(self.policy)
        second = FramingCore(self.policy)
        foreign_request = first.feed(request_frame("ping"))[0]
        second.feed(request_frame("ping"))
        with self.assertRaisesRegex(PolicyError, "MP213"):
            second.encode_response(foreign_request, "pong")

    def test_response_requires_the_exact_unconsumed_issued_request(self):
        core = FramingCore(self.policy)
        request = core.feed(request_frame("ping"))[0]
        forged = replace(request, input_text="forged")
        with self.assertRaisesRegex(PolicyError, "MP213"):
            core.encode_response(forged, "pong")

        core = FramingCore(self.policy)
        request = core.feed(request_frame("ping"))[0]
        core.encode_response(request, "pong")
        with self.assertRaisesRegex(PolicyError, "MP213"):
            core.encode_response(request, "again")

    def test_responses_remain_in_admission_order_without_multiplexing(self):
        core = FramingCore(self.policy)
        first, second = core.feed(request_frame("first") + request_frame("second"))
        with self.assertRaisesRegex(PolicyError, "MP213"):
            core.encode_response(second, "SECOND")

        core = FramingCore(self.policy)
        first, second = core.feed(request_frame("first") + request_frame("second"))
        core.encode_response(first, "FIRST")
        core.encode_response(second, "SECOND")

    def test_frame_events_are_fixed_content_free_and_bounded(self):
        sentinel = "fiat-700-event-secret-canary"
        core = FramingCore(self.policy)
        core.feed(request_frame("ordinary-content"))
        with self.assertRaisesRegex(PolicyError, "MP207"):
            core.feed(request_frame(extra={"authorization": sentinel}))
        events = [event.document() for event in core.events]
        self.assertEqual("MP000", events[0]["code"])
        self.assertEqual("MP207", events[-1]["code"])
        for event in events:
            self.assertEqual(
                {"schema", "stage", "outcome", "code"}, set(event)
            )
            self.assertEqual(FRAME_EVENT_SCHEMA, event["schema"])
        rendered = canonical_json(events)
        self.assertNotIn(sentinel.encode("ascii"), rendered)
        self.assertNotIn(b"ordinary-content", rendered)
        self.assertEqual(0, core.buffered_bytes)

    def test_compiled_policy_identity_and_hard_caps_are_rechecked(self):
        document = deepcopy(self.policy.document)
        document["limits"]["max_request_bytes"] = 65_537
        policy_bytes = canonical_json(document)
        broken = replace(
            self.policy,
            document=document,
            policy_bytes=policy_bytes,
            policy_sha256=sha256_bytes(policy_bytes),
        )
        with self.assertRaisesRegex(PolicyError, "MP204"):
            FramingCore(broken)

        forged = replace(self.policy, policy_sha256="0" * 64)
        with self.assertRaisesRegex(PolicyError, "MP204"):
            FramingCore(forged)

    def test_framing_replays_compiler_input_before_accepting_policy(self):
        document = deepcopy(self.policy.document)
        forged_digest = "f" * 64
        document["job"]["jobspec_sha256"] = forged_digest
        policy_bytes = canonical_json(document)
        forged = replace(
            self.policy,
            document=document,
            policy_bytes=policy_bytes,
            policy_sha256=sha256_bytes(policy_bytes),
            jobspec_sha256=forged_digest,
        )
        with self.assertRaisesRegex(PolicyError, "MP204"):
            FramingCore(forged)

    def test_framing_manifest_vectors_and_cli_are_exact(self):
        manifest = FIXTURES / "framing-cases.json"
        result = check_framing_manifest(manifest)
        self.assertEqual(FRAMING_MANIFEST_SCHEMA, "model-proxy-framing-cases/v1")
        self.assertEqual((2, 3), (result.cases, result.requests))
        self.assertEqual(
            (FIXTURES / "policy.sha256").read_text("ascii").strip(),
            result.policy_sha256,
        )
        process = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
            [
                sys.executable,
                str(CLI),
                "check-frames",
                "--manifest",
                str(manifest),
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual(b"", process.stderr)
        self.assertEqual(
            {
                "schema": "model-proxy-diagnostic/v1",
                "outcome": "frames_checked",
                "manifest_schema": FRAMING_MANIFEST_SCHEMA,
                "cases": 2,
                "requests": 3,
                "policy_sha256": result.policy_sha256,
            },
            json.loads(process.stdout),
        )

    def test_manifest_refusal_does_not_echo_free_form_bytes(self):
        sentinel = "fiat-700-manifest-secret-canary"
        document = json.loads((FIXTURES / "framing-cases.json").read_text("utf-8"))
        document["credential"] = sentinel
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "framing-cases.json"
            manifest.write_bytes(encode_document(document))
            (root / "accepted-job.json").write_bytes(
                (FIXTURES / "accepted-job.json").read_bytes()
            )
            process = subprocess.run(  # phylax: allow fixed local Python argv
                [
                    sys.executable,
                    str(CLI),
                    "check-frames",
                    "--manifest",
                    str(manifest),
                ],
                check=False,
                capture_output=True,
            )
        self.assertEqual(2, process.returncode)
        self.assertEqual(b"", process.stdout)
        self.assertNotIn(sentinel.encode("ascii"), process.stderr)
        self.assertEqual("MP218", json.loads(process.stderr)["code"])

    def test_manifest_path_type_refuses_with_a_bounded_error(self):
        try:
            check_framing_manifest(None)
        except Exception as error:  # The assertion keeps the parent report causal.
            self.assertIsInstance(error, PolicyError)
            self.assertEqual("MP218", error.code)
            self.assertEqual(
                {"schema", "outcome", "code", "field"},
                set(error.diagnostic()),
            )
        else:
            self.fail("an invalid manifest path was accepted")


class ProviderBoundaryTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.policy = compile_policy((FIXTURES / "accepted-job.json").read_bytes())
        self.profile = resolve_profile(self.policy.profile)
        self.credential = secrets.token_urlsafe(32)

    def response(
        self,
        input_text: str = "hello",
        output: str = "HELLO",
        **kwargs,
    ) -> BufferedHTTPSResponse:
        return BufferedHTTPSResponse(
            synthetic_provider_response(input_text, output), **kwargs
        )

    def session(
        self,
        response: BufferedHTTPSResponse | None = None,
        *,
        resolver=None,
        exchange=None,
        source=None,
        context_factory=None,
        input_text: str = "hello",
    ):
        if response is None:
            response = self.response(input_text)
        if exchange is None:
            exchange = HTTPSExchangeFixture(response)
        arguments = {
            "resolver": (
                (lambda _hostname, _port: ("8.8.8.8",))
                if resolver is None
                else resolver
            ),
            "exchange": exchange,
            "clock": iter((10_000, 20_000)).__next__,
        }
        if context_factory is not None:
            arguments["context_factory"] = context_factory
        connector = HTTPSConnector(self.profile, **arguments)
        provider = ProviderSession(
            self.policy,
            connector,
            credential_source=(
                (lambda _name: self.credential) if source is None else source
            ),
        )
        admitted = provider.feed(request_frame(input_text))
        provider.finish()
        self.assertEqual(1, len(admitted))
        return provider, admitted[0], exchange, response

    def assert_generate_refused(
        self,
        code: str,
        *,
        response: BufferedHTTPSResponse | None = None,
        resolver=None,
        exchange=None,
        source=None,
        input_text: str = "hello",
    ) -> tuple[PolicyError, object, BufferedHTTPSResponse]:
        provider, request, actual_exchange, actual_response = self.session(
            response,
            resolver=resolver,
            exchange=exchange,
            source=source,
            input_text=input_text,
        )
        with self.assertRaises(PolicyError) as caught:
            provider.generate(request)
        self.assertEqual(code, caught.exception.code)
        self.assertEqual(
            {"schema", "outcome", "code", "field"},
            set(caught.exception.diagnostic()),
        )
        return caught.exception, actual_exchange, actual_response

    def test_exact_mapping_injects_credential_only_after_admission(self):
        reads = []

        def source(name):
            reads.append(name)
            return self.credential

        provider, request, exchange, response = self.session(source=source)
        self.assertEqual([], reads)
        guest_response = provider.generate(request)
        self.assertEqual([self.profile.credential_environment], reads)
        self.assertEqual(1, len(exchange.requests))
        outbound = exchange.requests[0]
        self.assertEqual("https", outbound.scheme)
        self.assertEqual("model-proxy.loopback.invalid", outbound.hostname)
        self.assertEqual(443, outbound.port)
        self.assertEqual("8.8.8.8", outbound.address)
        self.assertEqual("POST", outbound.method)
        self.assertEqual("/v1/responses", outbound.path)
        self.assertEqual(
            canonical_json(
                {
                    "schema": "synthetic-provider-request/v1",
                    "model": "fixture-text-1",
                    "input": "hello",
                }
            ),
            outbound.body,
        )
        self.assertEqual(
            f"Bearer {self.credential}", outbound.header("Authorization")
        )
        self.assertEqual("application/json", outbound.header("Accept"))
        self.assertEqual("identity", outbound.header("Content-Encoding"))
        self.assertEqual("application/json", outbound.header("Content-Type"))
        expected = canonical_json(
            {"schema": RESPONSE_SCHEMA, "sequence": 1, "output": "HELLO"}
        )
        self.assertEqual(struct.pack(">I", len(expected)) + expected, guest_response)
        self.assertTrue(response.closed)

        events = [event.document() for event in provider.events]
        self.assertEqual(1, len(events))
        self.assertEqual(
            {
                "schema",
                "profile",
                "disclosure_state",
                "outcome_family",
                "code",
                "request_bytes",
                "response_bytes",
                "input_tokens",
                "output_tokens",
                "duration_ns",
            },
            set(events[0]),
        )
        self.assertEqual(PROVIDER_EVENT_SCHEMA, events[0]["schema"])
        self.assertEqual("provider-only", events[0]["disclosure_state"])
        self.assertEqual("accepted", events[0]["outcome_family"])
        self.assertEqual(5, events[0]["input_tokens"])
        self.assertEqual(5, events[0]["output_tokens"])
        self.assertEqual(10_000, events[0]["duration_ns"])
        self.assertNotIn(self.credential, repr(outbound))
        self.assertNotIn(
            self.credential.encode("ascii"), canonical_json(events)
        )

    def test_provider_session_pins_limits_against_post_activation_mutation(self):
        maximum = self.policy.document["limits"]["max_response_bytes"]
        body = synthetic_provider_response("hello", "HELLO")
        body += b" " * (maximum - len(body) + 1)
        response = BufferedHTTPSResponse(body)
        provider, request, _exchange, _response = self.session(response=response)

        self.policy.document["limits"]["max_response_bytes"] = (
            self.profile.limit_ceilings["max_response_bytes"]
        )

        with self.assertRaisesRegex(PolicyError, "MP310"):
            provider.generate(request)
        self.assertEqual(0, response.reads)
        self.assertTrue(response.closed)

    def test_foreign_or_unadmitted_request_never_reads_credential(self):
        reads = []
        response = self.response()
        exchange = HTTPSExchangeFixture(response)
        connector = HTTPSConnector(
            self.profile,
            resolver=lambda _hostname, _port: ("8.8.8.8",),
            exchange=exchange,
        )
        provider = ProviderSession(
            self.policy,
            connector,
            credential_source=lambda name: reads.append(name) or self.credential,
        )
        foreign = FramingCore(self.policy).feed(request_frame("hello"))[0]
        with self.assertRaisesRegex(PolicyError, "MP320"):
            provider.generate(foreign)
        self.assertEqual([], reads)
        self.assertEqual([], exchange.requests)
        self.assertEqual("not-read", provider.events[0].disclosure_state)

    def test_framing_refusal_poisoned_pending_provider_requests(self):
        reads = []
        response = self.response(input_text="safe", output="SAFE")
        exchange = HTTPSExchangeFixture(response)
        connector = HTTPSConnector(
            self.profile,
            resolver=lambda _hostname, _port: ("8.8.8.8",),
            exchange=exchange,
        )
        provider = ProviderSession(
            self.policy,
            connector,
            credential_source=lambda name: reads.append(name) or self.credential,
        )
        request = provider.feed(request_frame("safe"))[0]
        provider.feed(b"\x00")
        with self.assertRaisesRegex(PolicyError, "MP202"):
            provider.finish()

        with self.assertRaises(PolicyError) as caught:
            provider.generate(request)
        self.assertEqual("MP320", caught.exception.code)
        self.assertEqual([], reads)
        self.assertEqual([], exchange.requests)
        self.assertFalse(response.closed)

    def test_out_of_order_request_refuses_before_provider_disclosure(self):
        reads = []
        response = self.response(input_text="two", output="TWO")
        exchange = HTTPSExchangeFixture(response)
        connector = HTTPSConnector(
            self.profile,
            resolver=lambda _hostname, _port: ("8.8.8.8",),
            exchange=exchange,
        )
        provider = ProviderSession(
            self.policy,
            connector,
            credential_source=lambda name: reads.append(name) or self.credential,
        )
        requests = provider.feed(request_frame("one") + request_frame("two"))
        provider.finish()

        with self.assertRaises(PolicyError) as caught:
            provider.generate(requests[1])

        self.assertEqual("MP320", caught.exception.code)
        self.assertEqual([], reads)
        self.assertEqual([], exchange.requests)
        self.assertEqual("not-read", provider.events[-1].disclosure_state)
        self.assertFalse(response.closed)

    def test_credential_source_failure_is_fixed_and_value_free(self):
        def source(_name):
            raise RuntimeError(self.credential)

        error, exchange, response = self.assert_generate_refused(
            "MP321", source=source
        )
        self.assertNotIn(self.credential, str(error))
        self.assertEqual([], exchange.requests)
        self.assertFalse(response.closed)

    def test_guest_authority_and_connect_attempts_refuse_before_disclosure(self):
        attempts = {
            "scheme": "http",
            "host": "attacker.invalid",
            "hostname": "attacker.invalid",
            "port": 80,
            "path": "/other",
            "method": "CONNECT",
            "model": "attacker-model",
            "headers": {"Authorization": self.credential},
            "authorization": self.credential,
        }
        for field, value in attempts.items():
            with self.subTest(field=field):
                reads = []
                response = self.response()
                exchange = HTTPSExchangeFixture(response)
                connector = HTTPSConnector(
                    self.profile,
                    resolver=lambda _hostname, _port: ("8.8.8.8",),
                    exchange=exchange,
                )
                provider = ProviderSession(
                    self.policy,
                    connector,
                    credential_source=lambda name: reads.append(name)
                    or self.credential,
                )
                with self.assertRaises(PolicyError) as caught:
                    provider.feed(request_frame(extra={field: value}))
                self.assertIn(caught.exception.code, {"MP207", "MP208"})
                self.assertEqual([], reads)
                self.assertEqual([], exchange.requests)

        reads = []
        connector = HTTPSConnector(
            self.profile,
            resolver=lambda _hostname, _port: ("8.8.8.8",),
            exchange=HTTPSExchangeFixture(self.response()),
        )
        provider = ProviderSession(
            self.policy,
            connector,
            credential_source=lambda name: reads.append(name) or self.credential,
        )
        with self.assertRaisesRegex(PolicyError, "MP211"):
            provider.feed(request_frame(operation="CONNECT"))
        self.assertEqual([], reads)

    def test_profile_endpoint_method_and_auth_are_not_runtime_selectable(self):
        variants = (
            replace(self.profile, scheme="http"),
            replace(self.profile, hostname="attacker.invalid"),
            replace(self.profile, port=444),
            replace(self.profile, path_family="/other"),
            replace(self.profile, method="CONNECT"),
            replace(self.profile, authorization_scheme="Basic"),
        )
        for profile in variants:
            with self.subTest(profile=profile):
                with self.assertRaisesRegex(PolicyError, "MP300"):
                    HTTPSConnector(profile)

    def test_resolution_refuses_empty_multiple_and_special_addresses(self):
        cases = {
            "empty": ("MP301", ()),
            "multiple": ("MP303", ("8.8.8.8", "1.1.1.1")),
            "private": ("MP302", ("10.0.0.1",)),
            "loopback": ("MP302", ("127.0.0.1",)),
            "link-local": ("MP302", ("169.254.1.1",)),
            "multicast": ("MP302", ("224.0.0.1",)),
            "unspecified": ("MP302", ("0.0.0.0",)),
            "documentation": ("MP302", ("192.0.2.1",)),
            "reserved-v6": ("MP302", ("2001:db8::1",)),
        }
        for label, (code, answers) in cases.items():
            with self.subTest(label=label):
                error, exchange, _response = self.assert_generate_refused(
                    code,
                    resolver=lambda _hostname, _port, value=answers: value,
                )
                self.assertNotIn(self.credential, str(error))
                self.assertEqual([], exchange.requests)

        error, exchange, _response = self.assert_generate_refused(
            "MP301",
            resolver=lambda _hostname, _port: (_ for _ in ()).throw(
                RuntimeError(self.credential)
            ),
        )
        self.assertNotIn(self.credential, str(error))
        self.assertEqual([], exchange.requests)

    def test_resolution_is_single_use_and_peer_must_match_the_pin(self):
        calls = []

        def changing_resolver(_hostname, _port):
            calls.append(len(calls))
            return ("8.8.8.8" if len(calls) == 1 else "1.1.1.1",)

        provider, request, exchange, response = self.session(
            resolver=changing_resolver
        )
        provider.generate(request)
        self.assertEqual([0], calls)
        self.assertEqual("8.8.8.8", exchange.requests[0].address)
        self.assertTrue(response.closed)

        mismatched = self.response(peer_address="1.1.1.1")
        error, _exchange, actual = self.assert_generate_refused(
            "MP304", response=mismatched
        )
        self.assertNotIn(self.credential, str(error))
        self.assertTrue(actual.closed)

    def test_resolution_pin_is_reused_for_every_request_in_the_session(self):
        answers = iter((("8.8.8.8",), ("1.1.1.1",)))
        resolver_calls = []
        exchange_addresses = []
        responses = []

        def changing_resolver(_hostname, _port):
            answer = next(answers)
            resolver_calls.append(answer)
            return answer

        def exchange(request, _context, _timeout):
            exchange_addresses.append(request.address)
            mapped = json.loads(request.body)
            output = mapped["input"].upper()
            response = BufferedHTTPSResponse(
                synthetic_provider_response(mapped["input"], output),
                peer_address=request.address,
            )
            responses.append(response)
            return response

        connector = HTTPSConnector(
            self.profile,
            resolver=changing_resolver,
            exchange=exchange,
            clock=iter((10_000, 20_000, 30_000, 40_000)).__next__,
        )
        provider = ProviderSession(
            self.policy,
            connector,
            credential_source=lambda _name: self.credential,
        )
        requests = provider.feed(request_frame("one") + request_frame("two"))
        provider.finish()
        provider.generate(requests[0])
        provider.generate(requests[1])

        self.assertEqual([("8.8.8.8",)], resolver_calls)
        self.assertEqual(["8.8.8.8", "8.8.8.8"], exchange_addresses)
        self.assertTrue(all(response.closed for response in responses))

    def test_tls_context_certificate_and_hostname_fail_closed(self):
        insecure = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        insecure.check_hostname = False
        insecure.verify_mode = ssl.CERT_NONE
        with self.assertRaisesRegex(PolicyError, "MP305"):
            HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(self.response()),
                context_factory=lambda: insecure,
            )

        failures = (
            ssl.SSLCertVerificationError(1, self.credential),
            ssl.CertificateError(self.credential),
        )
        for failure in failures:
            with self.subTest(kind=type(failure).__name__):
                exchange = HTTPSExchangeFixture(error=failure)
                error, actual_exchange, _response = self.assert_generate_refused(
                    "MP305", exchange=exchange
                )
                self.assertNotIn(self.credential, str(error))
                self.assertEqual(1, len(actual_exchange.requests))
                self.assertEqual(
                    "model-proxy.loopback.invalid",
                    actual_exchange.requests[0].hostname,
                )

    def test_default_tls_context_does_not_honor_ambient_keylog_path(self):
        with tempfile.TemporaryDirectory() as directory:
            keylog = Path(directory) / "tls-secrets.log"
            with mock.patch.dict(
                os.environ, {"SSLKEYLOGFILE": str(keylog)}, clear=False
            ):
                HTTPSConnector(self.profile)

            self.assertFalse(keylog.exists())

    def test_every_redirect_status_is_terminal_and_response_is_closed(self):
        for status in range(300, 400):
            with self.subTest(status=status):
                response = self.response(status=status)
                self.assert_generate_refused("MP307", response=response)
                self.assertTrue(response.closed)
                self.assertEqual(0, response.reads)

    def test_response_refusal_records_confirmed_provider_disclosure(self):
        cases = (
            (self.response(status=302), "MP307", 0),
            (
                BufferedHTTPSResponse(
                    b"x" * 8193,
                    headers=(
                        ("Content-Type", "application/json"),
                        ("Transfer-Encoding", "chunked"),
                    ),
                    oversized_read=True,
                ),
                "MP310",
                8193,
            ),
        )
        for response, code, expected_response_bytes in cases:
            with self.subTest(code=code):
                provider, request, exchange, _response = self.session(
                    response=response
                )
                with self.assertRaisesRegex(PolicyError, code):
                    provider.generate(request)

                self.assertEqual(1, len(exchange.requests))
                event = provider.events[-1]
                self.assertEqual(
                    len(exchange.requests[0].body), event.request_bytes
                )
                self.assertEqual(expected_response_bytes, event.response_bytes)
                self.assertEqual("provider-only", event.disclosure_state)
                self.assertEqual(code, event.code)
                self.assertTrue(response.closed)

    def test_pre_response_transport_refusal_records_mapped_request(self):
        exchange = HTTPSExchangeFixture(error=TimeoutError(self.credential))
        provider, request, actual_exchange, _response = self.session(
            exchange=exchange
        )

        with self.assertRaisesRegex(PolicyError, "MP306") as caught:
            provider.generate(request)

        self.assertNotIn(self.credential, str(caught.exception))
        self.assertEqual(1, len(actual_exchange.requests))
        event = provider.events[-1]
        self.assertEqual(len(actual_exchange.requests[0].body), event.request_bytes)
        self.assertEqual(0, event.response_bytes)
        self.assertEqual(10_000, event.duration_ns)
        self.assertEqual("provider-only", event.disclosure_state)

    def test_unexpected_status_type_encoding_and_headers_refuse(self):
        status_cases = (True, "200", 201, 204, 299, 400, 500)
        for status in status_cases:
            with self.subTest(status=status):
                response = self.response(status=status)
                self.assert_generate_refused("MP308", response=response)
                self.assertTrue(response.closed)

        header_cases = (
            (
                "MP311",
                (("Content-Type", "text/plain"), ("Content-Length", "2")),
            ),
            (
                "MP311",
                (
                    ("Content-Type", "application/json"),
                    ("Content-Encoding", "gzip"),
                ),
            ),
            (
                "MP311",
                (
                    ("Content-Type", "application/json"),
                    ("Transfer-Encoding", "gzip"),
                ),
            ),
            (
                "MP309",
                (
                    ("Content-Type", "application/json"),
                    ("content-type", "application/json"),
                ),
            ),
            (
                "MP309",
                (
                    ("Content-Type", "application/json"),
                    ("X-Request-Id", "opaque"),
                ),
            ),
            (
                "MP309",
                (("Bad\nName", "value"), ("Content-Type", "application/json")),
            ),
            (
                "MP309",
                (
                    ("Content-Type", "application/json"),
                    ("Content-Length", "1"),
                    ("Transfer-Encoding", "chunked"),
                ),
            ),
        )
        for code, headers in header_cases:
            with self.subTest(code=code, headers=headers):
                response = self.response(headers=headers)
                self.assert_generate_refused(code, response=response)
                self.assertTrue(response.closed)

    def test_content_length_chunked_and_read_floods_refuse_and_close(self):
        maximum = self.policy.document["limits"]["max_response_bytes"]
        declared = BufferedHTTPSResponse(
            b"",
            headers=(
                ("Content-Type", "application/json"),
                ("Content-Length", str(maximum + 1)),
            ),
        )
        self.assert_generate_refused("MP310", response=declared)
        self.assertTrue(declared.closed)
        self.assertEqual(0, declared.reads)

        chunked = BufferedHTTPSResponse(
            b"x" * (maximum + 1),
            headers=(
                ("Content-Type", "application/json"),
                ("Transfer-Encoding", "chunked"),
            ),
        )
        self.assert_generate_refused("MP310", response=chunked)
        self.assertTrue(chunked.closed)

        oversized_read = BufferedHTTPSResponse(
            b"x" * 8193,
            headers=(
                ("Content-Type", "application/json"),
                ("Transfer-Encoding", "chunked"),
            ),
            oversized_read=True,
        )
        self.assert_generate_refused("MP310", response=oversized_read)
        self.assertTrue(oversized_read.closed)

        mismatch = BufferedHTTPSResponse(
            synthetic_provider_response("hello", "HELLO"),
            headers=(
                ("Content-Type", "application/json"),
                ("Content-Length", "1"),
            ),
        )
        self.assert_generate_refused("MP310", response=mismatch)
        self.assertTrue(mismatch.closed)

    def test_response_flood_reads_only_one_sentinel_beyond_the_cap(self):
        maximum = self.policy.document["limits"]["max_response_bytes"]
        response = BufferedHTTPSResponse(
            b"x" * (maximum + 1),
            headers=(
                ("Content-Type", "application/json"),
                ("Transfer-Encoding", "chunked"),
            ),
        )
        self.assert_generate_refused("MP310", response=response)
        self.assertEqual(1, response.read_sizes[-1])
        self.assertTrue(response.closed)

    def test_provider_response_schema_fields_values_and_usage_are_closed(self):
        duplicate = (
            b'{"schema":"synthetic-provider-response/v1","output":"HELLO",'
            b'"output":"HELLO","usage":{"input_tokens":5,"output_tokens":5}}'
        )
        cases = (
            ("malformed", "MP323", b"{"),
            ("duplicate", "MP323", duplicate),
            (
                "missing",
                "MP323",
                canonical_json(
                    {
                        "schema": "synthetic-provider-response/v1",
                        "output": "HELLO",
                    }
                ),
            ),
            (
                "unknown",
                "MP323",
                synthetic_provider_response(
                    "hello", "HELLO", extra={"request_id": "opaque"}
                ),
            ),
            (
                "schema",
                "MP324",
                synthetic_provider_response(
                    "hello", "HELLO", schema="synthetic-provider-response/v2"
                ),
            ),
            (
                "output-type",
                "MP325",
                synthetic_provider_response("hello", 5),
            ),
            (
                "usage-fields",
                "MP323",
                synthetic_provider_response(
                    "hello", "HELLO", usage={"input_tokens": 5}
                ),
            ),
            (
                "usage-type",
                "MP325",
                synthetic_provider_response(
                    "hello",
                    "HELLO",
                    usage={"input_tokens": True, "output_tokens": 5},
                ),
            ),
            (
                "usage-input-disagreement",
                "MP326",
                synthetic_provider_response(
                    "hello",
                    "HELLO",
                    usage={"input_tokens": 4, "output_tokens": 5},
                ),
            ),
            (
                "usage-output-disagreement",
                "MP326",
                synthetic_provider_response(
                    "hello",
                    "HELLO",
                    usage={"input_tokens": 5, "output_tokens": 4},
                ),
            ),
        )
        for label, code, body in cases:
            with self.subTest(label=label):
                response = BufferedHTTPSResponse(body)
                error, _exchange, actual = self.assert_generate_refused(
                    code, response=response
                )
                self.assertNotIn(self.credential, str(error))
                self.assertTrue(actual.closed)

        output = "x" * (
            self.policy.document["limits"]["max_output_tokens"] + 1
        )
        response = BufferedHTTPSResponse(
            synthetic_provider_response("hello", output)
        )
        self.assert_generate_refused("MP325", response=response)
        self.assertTrue(response.closed)

    def test_secret_echo_and_raw_transport_error_are_sanitised(self):
        echo = BufferedHTTPSResponse(
            synthetic_provider_response("hello", self.credential)
        )
        error, _exchange, actual = self.assert_generate_refused(
            "MP327", response=echo
        )
        self.assertNotIn(self.credential, str(error))
        self.assertTrue(actual.closed)

        exchange = HTTPSExchangeFixture(error=RuntimeError(self.credential))
        error, _exchange, _response = self.assert_generate_refused(
            "MP306", exchange=exchange
        )
        self.assertNotIn(self.credential, str(error))

    def test_canary_is_absent_from_every_retained_and_guest_surface(self):
        environment = {self.profile.credential_environment: self.credential}
        provider, request, exchange, _response = self.session(
            source=lambda name: environment[name]
        )
        guest_frame = request_frame("ordinary prompt")
        guest_response = provider.generate(request)
        self.assertIn(self.credential, exchange.requests[0].header("Authorization"))

        provider_events = [event.document() for event in provider.events]
        frame_events = [event.document() for event in provider.framing_events]
        receipt = {
            "outcome": provider_events[-1]["outcome_family"],
            "request_bytes": provider_events[-1]["request_bytes"],
            "response_bytes": provider_events[-1]["response_bytes"],
        }
        argv = [
            sys.executable,
            str(CLI),
            "provider-demo",
            "--manifest",
            str(FIXTURES / "provider-cases.json"),
        ]
        environment_snapshot = {"names": sorted(environment)}
        surfaces = (
            guest_frame,
            guest_response,
            canonical_json(provider_events),
            canonical_json(frame_events),
            canonical_json(receipt),
            canonical_json(argv),
            canonical_json(environment_snapshot),
        )
        for surface in surfaces:
            self.assertNotIn(self.credential.encode("ascii"), surface)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, surface in enumerate(surfaces):
                (root / f"surface-{index}.bin").write_bytes(surface)
            for path in root.iterdir():
                self.assertNotIn(self.credential.encode("ascii"), path.read_bytes())

    def test_provider_manifest_and_cli_use_only_injected_transport(self):
        manifest = FIXTURES / "provider-cases.json"
        with mock.patch(
            "model_proxy_lib.transport.socket.create_connection",
            side_effect=AssertionError("live connection attempted"),
        ):
            result = check_provider_manifest(manifest)
        self.assertEqual(PROVIDER_MANIFEST_SCHEMA, "model-proxy-provider-cases/v1")
        self.assertEqual((2, 2), (result.cases, result.requests))
        self.assertEqual(self.policy.policy_sha256, result.policy_sha256)

        process = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
            [
                sys.executable,
                str(CLI),
                "provider-demo",
                "--manifest",
                str(manifest),
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual(b"", process.stderr)
        self.assertEqual(
            {
                "schema": "model-proxy-diagnostic/v1",
                "outcome": "provider_checked",
                "manifest_schema": PROVIDER_MANIFEST_SCHEMA,
                "cases": 2,
                "requests": 2,
                "policy_sha256": self.policy.policy_sha256,
            },
            json.loads(process.stdout),
        )

    def test_provider_manifest_refusal_is_closed_and_value_free(self):
        document = json.loads(
            (FIXTURES / "provider-cases.json").read_text(encoding="utf-8")
        )
        document["credential"] = self.credential
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "provider-cases.json"
            manifest.write_bytes(encode_document(document))
            (root / "accepted-job.json").write_bytes(
                (FIXTURES / "accepted-job.json").read_bytes()
            )
            process = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
                [
                    sys.executable,
                    str(CLI),
                    "provider-demo",
                    "--manifest",
                    str(manifest),
                ],
                check=False,
                capture_output=True,
            )
        self.assertEqual(2, process.returncode)
        self.assertEqual(b"", process.stdout)
        self.assertNotIn(self.credential.encode("ascii"), process.stderr)
        self.assertEqual("MP328", json.loads(process.stderr)["code"])


class MutableClock:
    def __init__(self, value: int):
        self.value = value
        self.lock = threading.Lock()

    def __call__(self) -> int:
        with self.lock:
            return self.value

    def set(self, value: int) -> None:
        with self.lock:
            self.value = value


class LifecycleTests(unittest.TestCase):
    maxDiff = None

    START_MONOTONIC_NS = 1_000_000_000
    START_WALL_NS = 1_787_918_401 * NANOSECONDS_PER_SECOND

    def setUp(self):
        self.policy = compile_policy((FIXTURES / "accepted-job.json").read_bytes())
        self.profile = resolve_profile(self.policy.profile)
        self.credential = secrets.token_urlsafe(32)

    def policy_with_limits(self, **values: int):
        return compile_policy(
            with_jobspec(
                lambda document: document["model_proxy"]["limits"].update(values)
            )
        )

    def controller(self, policy=None, *, monotonic=None, wall=None):
        return LifecycleController(
            self.policy if policy is None else policy,
            monotonic_clock=(
                MutableClock(self.START_MONOTONIC_NS)
                if monotonic is None
                else monotonic
            ),
            wall_clock=(
                MutableClock(self.START_WALL_NS) if wall is None else wall
            ),
        )

    def mapped_bytes(self, input_text: str) -> int:
        return len(
            canonical_json(
                {
                    "schema": self.profile.provider_request_schema,
                    "model": self.profile.model,
                    "input": input_text,
                }
            )
        )

    def event(
        self,
        reservation,
        *,
        output_tokens: int = 0,
        response_bytes: int = 0,
    ) -> ProviderEvent:
        return ProviderEvent(
            profile=self.profile.identifier,
            disclosure_state="provider-only",
            outcome_family="accepted",
            code="MP000",
            request_bytes=reservation.request_bytes,
            response_bytes=response_bytes,
            input_tokens=reservation.input_tokens,
            output_tokens=output_tokens,
            duration_ns=1_000,
        )

    def reserve(self, controller, sequence: int, input_text: str = "x"):
        return controller.reserve(
            sequence=sequence,
            request_bytes=self.mapped_bytes(input_text),
            input_text=input_text,
            job_id=controller.job_id,
            jobspec_sha256=controller.jobspec_sha256,
        )

    def runtime_request(
        self,
        root: Path,
        *,
        response: BufferedHTTPSResponse | None = None,
        exchange=None,
        input_text: str = "lifecycle prompt",
        closer=lambda: None,
    ):
        if response is None:
            response = BufferedHTTPSResponse(
                synthetic_provider_response(input_text, "LIFECYCLE RESPONSE")
            )
        if exchange is None:
            exchange = HTTPSExchangeFixture(response)
        connector = HTTPSConnector(
            self.profile,
            resolver=lambda _hostname, _port: ("8.8.8.8",),
            exchange=exchange,
            clock=iter((10_000, 20_000, 30_000, 40_000)).__next__,
        )
        runtime = ModelProxyRuntime(
            self.policy,
            connector,
            root / "receipts.jsonl",
            credential_source=lambda _name: self.credential,
            monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
            wall_clock=MutableClock(self.START_WALL_NS),
            io_closer=closer,
        )
        request = runtime.feed(request_frame(input_text))[0]
        runtime.finish_input()
        return runtime, request, exchange, response

    def receipt_versions(self):
        return {
            "policy_schema": self.policy.document["schema"],
            "compiler": self.policy.document["compiler"],
            "token_counter": self.profile.token_counter,
            "receipt_schema": RECEIPT_SCHEMA,
        }

    def write_activation(self, sink: ReceiptSink) -> None:
        sink.write_activation(
            job_id=self.policy.document["job"]["id"],
            jobspec_sha256=self.policy.jobspec_sha256,
            policy_sha256=self.policy.policy_sha256,
            profile=self.profile.identifier,
            versions=self.receipt_versions(),
            activated_monotonic_ns=self.START_MONOTONIC_NS,
            absolute_expiry_unix_ns=1_787_918_999 * NANOSECONDS_PER_SECOND,
            elapsed_deadline_ns=self.START_MONOTONIC_NS
            + 300 * NANOSECONDS_PER_SECOND,
        )

    def test_lifecycle_manifest_and_cli_are_exact(self):
        manifest = FIXTURES / "lifecycle-cases.json"
        result = check_lifecycle_manifest(manifest)
        self.assertEqual(
            "model-proxy-lifecycle-cases/v1", LIFECYCLE_MANIFEST_SCHEMA
        )
        self.assertEqual((2, 2, 6), (result.cases, result.requests, result.receipts))
        self.assertEqual(self.policy.policy_sha256, result.policy_sha256)
        process = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
            [
                sys.executable,
                str(CLI),
                "lifecycle-demo",
                "--manifest",
                str(manifest),
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual(b"", process.stderr)
        self.assertEqual(
            {
                "schema": "model-proxy-diagnostic/v1",
                "outcome": "lifecycle_checked",
                "manifest_schema": LIFECYCLE_MANIFEST_SCHEMA,
                "cases": 2,
                "requests": 2,
                "receipts": 6,
                "policy_sha256": self.policy.policy_sha256,
            },
            json.loads(process.stdout),
        )

    def test_sequential_reservations_hit_every_exact_and_over_limit(self):
        controller = self.controller()
        for sequence in range(1, 9):
            reservation = self.reserve(controller, sequence)
            controller.mark_disclosed(reservation)
            controller.complete(reservation, self.event(reservation))
        with self.assertRaisesRegex(PolicyError, "MP402"):
            self.reserve(controller, 9)
        self.assertEqual(8, controller.terminal.counts["requests"])

        text = "x"
        mapped = self.mapped_bytes(text)
        byte_policy = self.policy_with_limits(
            max_request_bytes=mapped, max_total_request_bytes=mapped
        )
        byte_controller = self.controller(byte_policy)
        byte_reservation = byte_controller.reserve(
            sequence=1, request_bytes=mapped, input_text=text
        )
        byte_controller.mark_disclosed(byte_reservation)
        byte_controller.complete(
            byte_reservation, self.event(byte_reservation)
        )
        with self.assertRaisesRegex(PolicyError, "MP402"):
            byte_controller.reserve(
                sequence=2, request_bytes=mapped, input_text=text
            )
        with self.assertRaisesRegex(PolicyError, "MP402"):
            self.controller(byte_policy).reserve(
                sequence=1, request_bytes=mapped + 1, input_text=text
            )

        token_policy = self.policy_with_limits(
            max_input_tokens=3, max_total_input_tokens=3
        )
        token_controller = self.controller(token_policy)
        token_reservation = token_controller.reserve(
            sequence=1,
            request_bytes=self.mapped_bytes("abc"),
            input_text="abc",
        )
        token_controller.mark_disclosed(token_reservation)
        token_controller.complete(
            token_reservation, self.event(token_reservation)
        )
        with self.assertRaisesRegex(PolicyError, "MP402"):
            token_controller.reserve(
                sequence=2,
                request_bytes=self.mapped_bytes("a"),
                input_text="a",
            )
        with self.assertRaisesRegex(PolicyError, "MP402"):
            self.controller(token_policy).reserve(
                sequence=1,
                request_bytes=self.mapped_bytes("abcd"),
                input_text="abcd",
            )

        output_controller = self.controller()
        for sequence in range(1, 5):
            reservation = self.reserve(output_controller, sequence)
            output_controller.mark_disclosed(reservation)
            output_controller.complete(
                reservation,
                self.event(
                    reservation,
                    output_tokens=reservation.reserved_output_tokens,
                ),
            )
        with self.assertRaisesRegex(PolicyError, "MP403"):
            self.reserve(output_controller, 5)

        response_controller = self.controller()
        for sequence in range(1, 5):
            reservation = self.reserve(response_controller, sequence)
            response_controller.mark_disclosed(reservation)
            response_controller.complete(
                reservation,
                self.event(
                    reservation,
                    response_bytes=reservation.reserved_response_bytes,
                ),
            )
        with self.assertRaisesRegex(PolicyError, "MP403"):
            self.reserve(response_controller, 5)

        concurrency = self.controller()
        first = self.reserve(concurrency, 1)
        second = self.reserve(concurrency, 2)
        self.assertEqual((1, 2), (first.concurrency, second.concurrency))
        with self.assertRaisesRegex(PolicyError, "MP403"):
            self.reserve(concurrency, 3)

    def test_concurrent_reservations_are_atomic_and_never_overshoot(self):
        policy = self.policy_with_limits(
            max_requests=4, max_concurrency=4, max_receipts=6
        )
        controller = self.controller(policy)
        barrier = threading.Barrier(8)

        def attempt(sequence):
            barrier.wait()
            try:
                return self.reserve(controller, sequence)
            except PolicyError as error:
                return error.code

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(1, 9)))
        reservations = [result for result in results if not isinstance(result, str)]
        refusals = [result for result in results if isinstance(result, str)]
        self.assertEqual(4, len(reservations))
        self.assertEqual(["MP402"] * 4, sorted(refusals))
        self.assertEqual(4, controller.terminal.counts["requests"])
        self.assertLessEqual(
            controller.terminal.counts["request_bytes"],
            policy.document["limits"]["max_total_request_bytes"],
        )
        self.assertLessEqual(
            controller.terminal.counts["input_tokens"],
            policy.document["limits"]["max_total_input_tokens"],
        )

    def test_each_concurrent_reservation_dimension_is_atomic(self):
        mapped = self.mapped_bytes("x")
        limits = self.policy.document["limits"]
        shared = {
            "max_requests": 4,
            "max_concurrency": 4,
            "max_receipts": 6,
        }
        cases = (
            (
                "request-count",
                self.policy_with_limits(
                    max_requests=2, max_concurrency=2, max_receipts=4
                ),
                "MP402",
            ),
            (
                "request-bytes",
                self.policy_with_limits(
                    **shared,
                    max_request_bytes=mapped,
                    max_total_request_bytes=mapped * 2,
                ),
                "MP402",
            ),
            (
                "input-tokens",
                self.policy_with_limits(
                    **shared,
                    max_input_tokens=1,
                    max_total_input_tokens=2,
                ),
                "MP402",
            ),
            (
                "output-tokens",
                self.policy_with_limits(
                    **shared,
                    max_total_output_tokens=limits["max_output_tokens"] * 2,
                ),
                "MP403",
            ),
            (
                "response-bytes",
                self.policy_with_limits(
                    **shared,
                    max_total_response_bytes=limits["max_response_bytes"] * 2,
                ),
                "MP403",
            ),
            (
                "concurrency",
                self.policy_with_limits(
                    **{**shared, "max_concurrency": 2},
                ),
                "MP403",
            ),
        )
        for label, policy, expected_code in cases:
            with self.subTest(label=label):
                controller = self.controller(policy)
                barrier = threading.Barrier(4)

                def attempt(sequence):
                    barrier.wait()
                    try:
                        return self.reserve(controller, sequence)
                    except PolicyError as error:
                        return error.code

                with ThreadPoolExecutor(max_workers=4) as pool:
                    results = list(pool.map(attempt, range(1, 5)))
                reservations = [
                    result for result in results if not isinstance(result, str)
                ]
                refusals = [
                    result for result in results if isinstance(result, str)
                ]
                self.assertEqual(2, len(reservations))
                self.assertEqual([expected_code] * 2, sorted(refusals))
                self.assertEqual(expected_code, controller.terminal.code)
                self.assertEqual(2, controller.terminal.counts["requests"])

    def test_rollback_request_flood_cross_job_and_terminal_paths(self):
        controller = self.controller()
        reservation = self.reserve(controller, 1, "rollback")
        controller.rollback(reservation)
        self.assertEqual(1, self.reserve(controller, 1, "rollback").sequence)
        controller.cancel()
        with self.assertRaisesRegex(PolicyError, "MP406"):
            self.reserve(controller, 2)

        foreign = self.controller()
        with self.assertRaisesRegex(PolicyError, "MP401"):
            foreign.reserve(
                sequence=1,
                request_bytes=self.mapped_bytes("x"),
                input_text="x",
                job_id="another-job",
                jobspec_sha256=foreign.jobspec_sha256,
            )
        wrong_digest = self.controller()
        with self.assertRaisesRegex(PolicyError, "MP401"):
            wrong_digest.reserve(
                sequence=1,
                request_bytes=self.mapped_bytes("x"),
                input_text="x",
                job_id=wrong_digest.job_id,
                jobspec_sha256="f" * 64,
            )
        with self.assertRaisesRegex(PolicyError, "MP401"):
            self.controller().activate()

        flood = self.controller()
        for sequence in range(1, 9):
            current = self.reserve(flood, sequence)
            flood.mark_disclosed(current)
            flood.complete(current, self.event(current))
        with self.assertRaisesRegex(PolicyError, "MP402"):
            self.reserve(flood, 9)

    def test_absolute_and_monotonic_expiry_are_distinct_terminal_paths(self):
        monotonic = MutableClock(self.START_MONOTONIC_NS)
        wall = MutableClock(1_787_918_999 * NANOSECONDS_PER_SECOND)
        absolute = self.controller(monotonic=monotonic, wall=wall)
        wall.set(1_787_919_000 * NANOSECONDS_PER_SECOND)
        self.assertEqual("MP404", absolute.poll().code)
        with self.assertRaisesRegex(PolicyError, "MP404"):
            self.reserve(absolute, 1)

        monotonic = MutableClock(self.START_MONOTONIC_NS)
        elapsed = self.controller(monotonic=monotonic)
        monotonic.set(elapsed.elapsed_deadline_ns)
        self.assertEqual("MP405", elapsed.poll().code)
        with self.assertRaisesRegex(PolicyError, "MP405"):
            self.reserve(elapsed, 1)

    def test_wall_clock_rollback_cannot_extend_absolute_expiry(self):
        expiry_ns = 1_787_919_000 * NANOSECONDS_PER_SECOND
        monotonic = MutableClock(self.START_MONOTONIC_NS)
        wall = MutableClock(expiry_ns - NANOSECONDS_PER_SECOND)
        controller = self.controller(monotonic=monotonic, wall=wall)

        wall.set(expiry_ns - 101 * NANOSECONDS_PER_SECOND)
        monotonic.set(self.START_MONOTONIC_NS + 2 * NANOSECONDS_PER_SECOND)
        snapshot = controller.poll()

        self.assertIsNotNone(snapshot)
        if snapshot is not None:
            self.assertEqual("MP404", snapshot.code)
        with self.assertRaisesRegex(PolicyError, "MP404"):
            self.reserve(controller, 1)

    def test_activation_wall_rollback_cannot_stretch_signed_absolute_lifetime(self):
        policy = self.policy_with_limits(total_wall_seconds=900)
        signed_lifetime_ns = (
            policy.document["job"]["absolute_lifetime_seconds"]
            * NANOSECONDS_PER_SECOND
        )
        monotonic = MutableClock(self.START_MONOTONIC_NS)
        wall = MutableClock(self.START_WALL_NS - signed_lifetime_ns)
        controller = self.controller(policy, monotonic=monotonic, wall=wall)

        monotonic.set(self.START_MONOTONIC_NS + signed_lifetime_ns)
        snapshot = controller.poll()

        self.assertIsNotNone(snapshot)
        if snapshot is not None:
            self.assertEqual("MP404", snapshot.code)
        with self.assertRaisesRegex(PolicyError, "MP404"):
            self.reserve(controller, 1)

    def test_clock_failure_is_terminal_and_writes_terminal_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime, _request, exchange, _response = self.runtime_request(
                Path(directory), input_text="clock failure prompt"
            )
            runtime._controller._monotonic_clock = lambda: (_ for _ in ()).throw(
                RuntimeError("clock unavailable")
            )

            try:
                code = runtime.poll()
            except PolicyError:
                code = None

            self.assertEqual("MP405", code)
            self.assertIsNotNone(runtime.terminal)
            self.assertEqual([], exchange.requests)
            records = [
                json.loads(line)
                for line in (Path(directory) / "receipts.jsonl")
                .read_text("utf-8")
                .splitlines()
            ]
            self.assertEqual(
                ["activation", "terminal"],
                [record["event"] for record in records],
            )
            self.assertEqual("MP405", records[-1]["outcome_code"])

    def test_cancellation_before_admission_marks_terminal_before_close(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            order = []
            runtime_box = {}

            def closer():
                order.append(runtime_box["runtime"].terminal.code)

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response("unused", "UNUSED")
                    )
                ),
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
                io_closer=closer,
            )
            runtime_box["runtime"] = runtime
            runtime.cancel()
            self.assertEqual(["MP406"], order)
            with self.assertRaisesRegex(PolicyError, "MP406"):
                runtime.feed(request_frame("late"))
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual(
                ["activation", "terminal"], [record["event"] for record in records]
            )

    def test_cancellation_observes_elapsed_expiry_before_terminalizing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monotonic = MutableClock(self.START_MONOTONIC_NS)
            closer_codes = []
            runtime_box = {}

            def closer():
                closer_codes.append(runtime_box["runtime"].terminal.code)

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response("unused", "UNUSED")
                    )
                ),
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=monotonic,
                wall_clock=MutableClock(self.START_WALL_NS),
                io_closer=closer,
            )
            runtime_box["runtime"] = runtime
            monotonic.set(runtime._controller.elapsed_deadline_ns)

            runtime.cancel()

            self.assertEqual("MP405", runtime.terminal.code)
            self.assertEqual(["MP405"], closer_codes)
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual("MP405", records[-1]["outcome_code"])

    def test_cancellation_observes_absolute_expiry_before_terminalizing(self):
        wall = MutableClock(self.START_WALL_NS)
        controller = self.controller(wall=wall)
        wall.set(controller.absolute_expiry_ns)

        snapshot = controller.cancel()

        self.assertEqual("MP404", snapshot.code)
        self.assertEqual("MP404", controller.terminal.code)

    def test_terminal_cleanup_discards_framing_content_references(self):
        prompt = "framing cleanup prompt"
        suffixes = (
            ("partial-prefix", b"\x00\x00"),
            ("partial-payload", struct.pack(">I", 16) + b'{"schema"'),
        )
        for label, suffix in suffixes:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                connector = HTTPSConnector(
                    self.profile,
                    resolver=lambda _hostname, _port: ("8.8.8.8",),
                    exchange=HTTPSExchangeFixture(
                        BufferedHTTPSResponse(
                            synthetic_provider_response(prompt, "UNUSED")
                        )
                    ),
                )
                runtime = ModelProxyRuntime(
                    self.policy,
                    connector,
                    root / "receipts.jsonl",
                    credential_source=lambda _name: self.credential,
                    monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                    wall_clock=MutableClock(self.START_WALL_NS),
                )
                runtime.feed(request_frame(prompt) + suffix)
                framing = runtime._provider._framing
                self.assertEqual(1, len(framing._issued))
                self.assertGreater(framing.buffered_bytes, 0)

                runtime.cancel()

                self.assertEqual(
                    ({}, {}, 0),
                    (
                        runtime._provider._admitted,
                        framing._issued,
                        framing.buffered_bytes,
                    ),
                )

    def test_cancellation_during_transport_closes_and_discards_late_response(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entered = threading.Event()
            released = threading.Event()
            responses = []
            runtime_box = {}

            def exchange(_request, _context, _timeout):
                entered.set()
                self.assertTrue(released.wait(5))
                response = BufferedHTTPSResponse(
                    synthetic_provider_response("late prompt", "LATE RESPONSE")
                )
                responses.append(response)
                return response

            def closer():
                self.assertEqual(
                    "MP406", runtime_box["runtime"].terminal.code
                )
                released.set()

            runtime, request, actual_exchange, _response = self.runtime_request(
                root,
                exchange=exchange,
                input_text="late prompt",
                closer=closer,
            )
            runtime_box["runtime"] = runtime
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(runtime.generate, request)
                self.assertTrue(entered.wait(5))
                runtime.cancel()
                with self.assertRaisesRegex(PolicyError, "MP406"):
                    future.result(timeout=5)
            self.assertIs(exchange, actual_exchange)
            self.assertTrue(responses[0].closed)
            receipt_bytes = (root / "receipts.jsonl").read_bytes()
            self.assertNotIn(b"LATE RESPONSE", receipt_bytes)
            self.assertEqual(
                "provider-only",
                json.loads(receipt_bytes.splitlines()[-1])["disclosure_state"],
            )

    def test_pre_exchange_refusal_is_not_provider_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exchange = HTTPSExchangeFixture(
                BufferedHTTPSResponse(
                    synthetic_provider_response("resolution prompt", "UNUSED")
                )
            )
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: (),
                exchange=exchange,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            request = runtime.feed(request_frame("resolution prompt"))[0]
            runtime.finish_input()

            with self.assertRaisesRegex(PolicyError, "MP301"):
                runtime.generate(request)

            self.assertEqual([], exchange.requests)
            self.assertEqual("not-read", runtime.provider_events[-1].disclosure_state)
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual("not-read", records[-1]["disclosure_state"])

    def test_expiry_during_resolution_prevents_provider_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monotonic = MutableClock(self.START_MONOTONIC_NS)
            exchange = HTTPSExchangeFixture(
                BufferedHTTPSResponse(
                    synthetic_provider_response("resolution expiry", "UNUSED")
                )
            )

            def delayed_resolver(_hostname, _port):
                monotonic.set(
                    self.START_MONOTONIC_NS
                    + self.policy.document["limits"]["total_wall_seconds"]
                    * NANOSECONDS_PER_SECOND
                )
                return ("8.8.8.8",)

            connector = HTTPSConnector(
                self.profile,
                resolver=delayed_resolver,
                exchange=exchange,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=monotonic,
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            request = runtime.feed(request_frame("resolution expiry"))[0]
            runtime.finish_input()

            with self.assertRaisesRegex(PolicyError, "MP405"):
                runtime.generate(request)

            self.assertEqual([], exchange.requests)
            self.assertEqual("not-read", runtime.provider_events[-1].disclosure_state)
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual("MP405", records[-1]["outcome_code"])
            self.assertEqual("not-read", records[-1]["disclosure_state"])

    def test_resolution_delay_shrinks_the_exchange_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monotonic = MutableClock(self.START_MONOTONIC_NS)
            timeouts = []

            def delayed_resolver(_hostname, _port):
                monotonic.set(
                    self.START_MONOTONIC_NS + 295 * NANOSECONDS_PER_SECOND
                )
                return ("8.8.8.8",)

            def exchange(_request, _context, timeout):
                timeouts.append(timeout)
                return BufferedHTTPSResponse(
                    synthetic_provider_response(
                        "resolution timeout", "LIFECYCLE RESPONSE"
                    )
                )

            connector = HTTPSConnector(
                self.profile,
                resolver=delayed_resolver,
                exchange=exchange,
                clock=iter((10_000, 20_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=monotonic,
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            request = runtime.feed(request_frame("resolution timeout"))[0]
            runtime.finish_input()

            runtime.generate(request)

            self.assertEqual([5.0], timeouts)
            runtime.cancel()

    def test_cancellation_before_provider_handoff_is_not_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            credential_started = threading.Event()
            release_credential = threading.Event()
            exchange = HTTPSExchangeFixture(
                BufferedHTTPSResponse(
                    synthetic_provider_response("cancel prompt", "UNUSED")
                )
            )

            def credential_source(_name):
                credential_started.set()
                self.assertTrue(release_credential.wait(5))
                return self.credential

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=credential_source,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
                io_closer=release_credential.set,
            )
            request = runtime.feed(request_frame("cancel prompt"))[0]
            runtime.finish_input()

            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(runtime.generate, request)
                self.assertTrue(credential_started.wait(5))
                runtime.cancel()
                with self.assertRaisesRegex(PolicyError, "MP406"):
                    future.result(timeout=5)

            self.assertEqual([], exchange.requests)
            self.assertEqual("not-read", runtime.provider_events[-1].disclosure_state)
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual("not-read", records[-1]["disclosure_state"])

    def test_cancelled_final_waiter_reports_the_terminal_winner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_started = threading.Event()
            release_first = threading.Event()
            second_receipted = threading.Event()

            def exchange(request, _context, _timeout):
                mapped = json.loads(request.body)
                if mapped["input"] == "first cancelled prompt":
                    first_started.set()
                    self.assertTrue(release_first.wait(5))
                return BufferedHTTPSResponse(
                    synthetic_provider_response(
                        mapped["input"], mapped["input"].upper()
                    )
                )

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000, 30_000, 40_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
                io_closer=release_first.set,
            )
            requests = runtime.feed(
                request_frame("first cancelled prompt")
                + request_frame("second cancelled prompt")
            )
            runtime.finish_input()
            original_write = runtime._sink.write_request

            def observed_write(**arguments):
                original_write(**arguments)
                if arguments["sequence"] == 2:
                    second_receipted.set()

            with mock.patch.object(
                runtime._sink, "write_request", side_effect=observed_write
            ), ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(runtime.generate, requests[0])
                self.assertTrue(first_started.wait(5))
                second = pool.submit(runtime.generate, requests[1], final=True)
                self.assertTrue(second_receipted.wait(5))
                runtime.cancel()
                try:
                    first.result(timeout=5)
                except PolicyError as error:
                    first_code = error.code
                else:
                    first_code = None
                try:
                    second.result(timeout=5)
                except PolicyError as error:
                    second_code = error.code
                else:
                    second_code = None

            self.assertEqual(("MP406", "MP406"), (first_code, second_code))

    def test_completion_after_cancellation_reports_the_terminal_winner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, _request, _exchange, _response = self.runtime_request(
                root, input_text="cancelled completion"
            )
            runtime.cancel()

            try:
                runtime.complete_job()
            except PolicyError as error:
                code = error.code
            else:
                code = None

            self.assertEqual("MP406", code)

    def test_concurrent_runtime_generation_keeps_provider_order_and_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_started = threading.Event()
            release_first = threading.Event()
            second_receipted = threading.Event()
            provider_inputs = []

            def exchange(request, _context, _timeout):
                mapped = json.loads(request.body)
                input_text = mapped["input"]
                provider_inputs.append(input_text)
                if input_text == "first concurrent prompt":
                    first_started.set()
                    self.assertTrue(release_first.wait(5))
                return BufferedHTTPSResponse(
                    synthetic_provider_response(input_text, input_text.upper())
                )

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000, 30_000, 40_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
                io_closer=lambda: None,
            )
            requests = runtime.feed(
                request_frame("first concurrent prompt")
                + request_frame("second concurrent prompt")
            )
            runtime.finish_input()
            original_write = runtime._sink.write_request

            def observed_write(**arguments):
                original_write(**arguments)
                if arguments["sequence"] == 2:
                    second_receipted.set()

            with mock.patch.object(
                runtime._sink, "write_request", side_effect=observed_write
            ), ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(runtime.generate, requests[0])
                self.assertTrue(first_started.wait(5))
                second = pool.submit(runtime.generate, requests[1], final=True)
                self.assertTrue(second_receipted.wait(5))
                release_first.set()
                try:
                    first_response = first.result(timeout=5)
                    second_response = second.result(timeout=5)
                except Exception as error:
                    self.fail(
                        "concurrent provider turn raised "
                        f"{type(error).__name__} instead of returning a response"
                    )

            self.assertEqual(
                ["first concurrent prompt", "second concurrent prompt"],
                provider_inputs,
            )
            self.assertEqual(
                [
                    "FIRST CONCURRENT PROMPT",
                    "SECOND CONCURRENT PROMPT",
                ],
                [
                    json.loads(first_response[4:])["output"],
                    json.loads(second_response[4:])["output"],
                ],
            )
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual(
                ["activation", "request", "request", "terminal"],
                [record["event"] for record in records],
            )
            self.assertEqual("MP000", runtime.terminal.code)

    def test_concurrent_turn_order_does_not_depend_on_lock_waiter_fairness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            provider_inputs = []
            second_receipted = threading.Event()

            def exchange(request, _context, _timeout):
                input_text = json.loads(request.body)["input"]
                provider_inputs.append(input_text)
                return BufferedHTTPSResponse(
                    synthetic_provider_response(input_text, input_text.upper())
                )

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000, 30_000, 40_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            requests = runtime.feed(
                request_frame("first scheduled prompt")
                + request_frame("second scheduled prompt")
            )
            runtime.finish_input()

            class ScheduledPublicationLock:
                def __init__(self):
                    self.lock = threading.Lock()
                    self.first_released = threading.Event()
                    self.resume_first = threading.Event()
                    self.schedule_once = True

                def __enter__(self):
                    self.lock.acquire()
                    return self

                def __exit__(self, _type, _value, _traceback):
                    self.lock.release()
                    if (
                        threading.current_thread().name == "sequence-1"
                        and self.schedule_once
                    ):
                        self.schedule_once = False
                        self.first_released.set()
                        self.resume_first.wait(5)

            scheduled = ScheduledPublicationLock()
            runtime._publication_lock = scheduled
            original_write = runtime._sink.write_request

            def observed_write(**arguments):
                original_write(**arguments)
                if arguments["sequence"] == 2:
                    second_receipted.set()

            results = {}

            def generate(label, request, final):
                try:
                    results[label] = runtime.generate(request, final=final)
                except PolicyError as error:
                    results[label] = error.code

            with mock.patch.object(
                runtime._sink, "write_request", side_effect=observed_write
            ):
                first = threading.Thread(
                    target=generate,
                    args=("first", requests[0], False),
                    name="sequence-1",
                )
                second = threading.Thread(
                    target=generate,
                    args=("second", requests[1], True),
                    name="sequence-2",
                )
                first.start()
                self.assertTrue(scheduled.first_released.wait(5))
                second.start()
                self.assertTrue(second_receipted.wait(5))
                scheduled.resume_first.set()
                first.join(5)
                second.join(5)

            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(
                ["first scheduled prompt", "second scheduled prompt"],
                provider_inputs,
            )
            self.assertTrue(
                all(isinstance(value, bytes) for value in results.values())
            )
            self.assertEqual("MP000", runtime.terminal.code)

    def test_concurrent_turn_order_survives_reverse_first_lock_acquisition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            provider_inputs = []
            second_receipted = threading.Event()

            def exchange(request, _context, _timeout):
                input_text = json.loads(request.body)["input"]
                provider_inputs.append(input_text)
                return BufferedHTTPSResponse(
                    synthetic_provider_response(input_text, input_text.upper())
                )

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000, 30_000, 40_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            requests = runtime.feed(
                request_frame("first reverse prompt")
                + request_frame("second reverse prompt")
            )
            runtime.finish_input()

            class ReverseFirstPublicationLock:
                def __init__(self):
                    self.lock = threading.Lock()
                    self.first_waiting = threading.Event()
                    self.resume_first = threading.Event()
                    self.schedule_once = True

                def __enter__(self):
                    if (
                        threading.current_thread().name == "sequence-1"
                        and self.schedule_once
                    ):
                        self.schedule_once = False
                        self.first_waiting.set()
                        self.resume_first.wait(5)
                    self.lock.acquire()
                    return self

                def __exit__(self, _type, _value, _traceback):
                    self.lock.release()

            scheduled = ReverseFirstPublicationLock()
            runtime._publication_lock = scheduled
            original_write = runtime._sink.write_request

            def observed_write(**arguments):
                original_write(**arguments)
                if arguments["sequence"] == 2:
                    second_receipted.set()

            results = {}

            def generate(label, request, final):
                try:
                    results[label] = runtime.generate(request, final=final)
                except PolicyError as error:
                    results[label] = error.code

            with mock.patch.object(
                runtime._sink, "write_request", side_effect=observed_write
            ):
                first = threading.Thread(
                    target=generate,
                    args=("first", requests[0], False),
                    name="sequence-1",
                )
                second = threading.Thread(
                    target=generate,
                    args=("second", requests[1], True),
                    name="sequence-2",
                )
                first.start()
                self.assertTrue(scheduled.first_waiting.wait(5))
                second.start()
                self.assertTrue(second_receipted.wait(5))
                self.assertTrue(second.is_alive())
                scheduled.resume_first.set()
                first.join(5)
                second.join(5)

            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(
                ["first reverse prompt", "second reverse prompt"],
                provider_inputs,
            )
            self.assertTrue(
                all(isinstance(value, bytes) for value in results.values())
            )
            self.assertEqual("MP000", runtime.terminal.code)

    def test_pending_higher_turn_observes_expiry_without_lower_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monotonic = MutableClock(self.START_MONOTONIC_NS)
            provider_called = threading.Event()
            second_receipted = threading.Event()

            def exchange(request, _context, _timeout):
                provider_called.set()
                input_text = json.loads(request.body)["input"]
                return BufferedHTTPSResponse(
                    synthetic_provider_response(input_text, input_text.upper())
                )

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=monotonic,
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            requests = runtime.feed(
                request_frame("unstarted first prompt")
                + request_frame("waiting second prompt")
            )
            runtime.finish_input()
            original_write = runtime._sink.write_request

            def observed_write(**arguments):
                original_write(**arguments)
                if arguments["sequence"] == 2:
                    second_receipted.set()

            result = {}

            def generate_second():
                try:
                    result["value"] = runtime.generate(requests[1])
                except PolicyError as error:
                    result["value"] = error.code

            with mock.patch.object(
                runtime._sink, "write_request", side_effect=observed_write
            ):
                worker = threading.Thread(target=generate_second)
                worker.start()
                self.assertTrue(second_receipted.wait(5))
                monotonic.set(runtime._controller.elapsed_deadline_ns)
                worker.join(1)
                finished_at_deadline = not worker.is_alive()
                if worker.is_alive():
                    runtime.cancel()
                    worker.join(5)

            self.assertTrue(finished_at_deadline)
            self.assertFalse(worker.is_alive())
            self.assertEqual("MP405", result["value"])
            self.assertEqual("MP405", runtime.terminal.code)
            self.assertFalse(provider_called.is_set())
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual(
                ["activation", "request", "terminal"],
                [record["event"] for record in records],
            )
            self.assertEqual("MP405", records[-1]["outcome_code"])

    def test_pending_higher_turn_wakes_after_cancellation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            second_receipted = threading.Event()
            provider_called = threading.Event()

            def exchange(request, _context, _timeout):
                provider_called.set()
                input_text = json.loads(request.body)["input"]
                return BufferedHTTPSResponse(
                    synthetic_provider_response(input_text, input_text.upper())
                )

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            requests = runtime.feed(
                request_frame("unstarted first prompt")
                + request_frame("waiting second prompt")
            )
            runtime.finish_input()
            original_write = runtime._sink.write_request

            def observed_write(**arguments):
                original_write(**arguments)
                if arguments["sequence"] == 2:
                    second_receipted.set()

            result = {}

            def generate_second():
                try:
                    result["value"] = runtime.generate(requests[1])
                except PolicyError as error:
                    result["value"] = error.code

            with mock.patch.object(
                runtime._sink, "write_request", side_effect=observed_write
            ):
                worker = threading.Thread(target=generate_second)
                worker.start()
                self.assertTrue(second_receipted.wait(5))
                runtime.cancel()
                worker.join(1)
                woke_after_cancellation = not worker.is_alive()
                if worker.is_alive():
                    with runtime._provider_turn_condition:
                        runtime._next_provider_turn = 2
                        runtime._provider_turn_condition.notify_all()
                    worker.join(5)

            self.assertTrue(woke_after_cancellation)
            self.assertFalse(worker.is_alive())
            self.assertEqual("MP406", result["value"])
            self.assertEqual("MP406", runtime.terminal.code)
            self.assertFalse(provider_called.is_set())
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual(
                ["activation", "request", "terminal"],
                [record["event"] for record in records],
            )
            self.assertEqual("MP406", records[-1]["outcome_code"])

    def test_late_transport_failure_keeps_the_cancellation_winner(self):
        with tempfile.TemporaryDirectory() as directory:
            entered = threading.Event()
            released = threading.Event()

            def exchange(_request, _context, _timeout):
                entered.set()
                self.assertTrue(released.wait(5))
                raise RuntimeError("transport closed after cancellation")

            runtime, request, _exchange, _response = self.runtime_request(
                Path(directory),
                exchange=exchange,
                input_text="cancelled transport",
                closer=released.set,
            )
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(runtime.generate, request)
                self.assertTrue(entered.wait(5))
                runtime.cancel()
                with self.assertRaisesRegex(PolicyError, "MP406"):
                    future.result(timeout=5)
            self.assertEqual("MP406", runtime.terminal.code)

    def test_successful_terminal_state_refuses_later_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response("unused", "UNUSED")
                    )
                ),
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                Path(directory) / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            runtime.complete_job()
            self.assertEqual("MP000", runtime.terminal.code)
            with self.assertRaisesRegex(PolicyError, "MP401"):
                runtime.feed(request_frame("too late"))

    def test_completion_cancel_and_expiry_races_have_one_winner(self):
        completion_first = self.controller()
        reservation = self.reserve(completion_first, 1)
        completion_first.mark_disclosed(reservation)
        completion_first.complete(reservation, self.event(reservation))
        self.assertEqual("MP000", completion_first.finish().code)
        self.assertEqual("MP000", completion_first.cancel().code)

        cancellation_first = self.controller()
        reservation = self.reserve(cancellation_first, 1)
        cancellation_first.mark_disclosed(reservation)
        cancellation_first.cancel()
        with self.assertRaisesRegex(PolicyError, "MP406"):
            cancellation_first.complete(reservation, self.event(reservation))

        monotonic = MutableClock(self.START_MONOTONIC_NS)
        expiry_first = self.controller(monotonic=monotonic)
        reservation = self.reserve(expiry_first, 1)
        expiry_first.mark_disclosed(reservation)
        monotonic.set(expiry_first.elapsed_deadline_ns)
        self.assertEqual("MP405", expiry_first.poll().code)
        with self.assertRaisesRegex(PolicyError, "MP405"):
            expiry_first.complete(reservation, self.event(reservation))

    def test_runtime_finalizes_quota_and_active_completion_terminal_paths(self):
        input_text = "x"
        mapped = self.mapped_bytes(input_text)
        quota_policy = self.policy_with_limits(
            max_requests=2,
            max_concurrency=1,
            max_receipts=4,
            max_request_bytes=mapped,
            max_total_request_bytes=mapped,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            closer_codes = []
            runtime_box = {}

            def quota_closer():
                closer_codes.append(runtime_box["runtime"].terminal.code)

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response(input_text, "Y")
                    )
                ),
                clock=iter((10_000, 20_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                quota_policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
                io_closer=quota_closer,
            )
            runtime_box["runtime"] = runtime
            requests = runtime.feed(request_frame(input_text) * 2)
            runtime.finish_input()
            runtime.generate(requests[0])
            with self.assertRaisesRegex(PolicyError, "MP402"):
                runtime.generate(requests[1])
            was_finalized = runtime._terminal_finalized
            records_before_cleanup = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            if not was_finalized:
                runtime.cancel()
            self.assertTrue(was_finalized)
            self.assertEqual(["MP402"], closer_codes)
            self.assertEqual(
                ["activation", "request", "terminal"],
                [record["event"] for record in records_before_cleanup],
            )
            self.assertEqual("MP402", records_before_cleanup[-1]["outcome_code"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entered = threading.Event()
            released = threading.Event()

            def exchange(_request, _context, _timeout):
                entered.set()
                self.assertTrue(released.wait(5))
                return BufferedHTTPSResponse(
                    synthetic_provider_response("active completion", "TOO LATE")
                )

            runtime, request, _actual_exchange, _response = self.runtime_request(
                root,
                exchange=exchange,
                input_text="active completion",
                closer=released.set,
            )
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(runtime.generate, request)
                self.assertTrue(entered.wait(5))
                with self.assertRaisesRegex(PolicyError, "MP401"):
                    runtime.complete_job()
                finalized_before_manual_release = runtime._terminal_finalized
                closer_ran = released.is_set()
                if not closer_ran:
                    released.set()
                with self.assertRaisesRegex(PolicyError, "MP401"):
                    future.result(timeout=5)
            self.assertTrue(finalized_before_manual_release)
            self.assertTrue(closer_ran)
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual("terminal", records[-1]["event"])
            self.assertEqual("MP401", records[-1]["outcome_code"])

    def test_final_response_refusal_finalizes_before_another_caller_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_started = threading.Event()
            release_first = threading.Event()
            second_receipted = threading.Event()
            second_mark_started = threading.Event()
            release_second_mark = threading.Event()

            def exchange(request, _context, _timeout):
                input_text = json.loads(request.body)["input"]
                if input_text == "first final prompt":
                    first_started.set()
                    self.assertTrue(release_first.wait(5))
                return BufferedHTTPSResponse(
                    synthetic_provider_response(input_text, input_text.upper())
                )

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000, 30_000, 40_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            requests = runtime.feed(
                request_frame("first final prompt")
                + request_frame("second active prompt")
            )
            runtime.finish_input()
            original_write = runtime._sink.write_request
            original_mark = runtime._controller.mark_disclosed

            def observed_write(**arguments):
                original_write(**arguments)
                if arguments["sequence"] == 2:
                    second_receipted.set()

            def delayed_second_mark(reservation):
                if reservation.sequence == 2:
                    second_mark_started.set()
                    self.assertTrue(release_second_mark.wait(5))
                return original_mark(reservation)

            with mock.patch.object(
                runtime._sink, "write_request", side_effect=observed_write
            ), mock.patch.object(
                runtime._controller,
                "mark_disclosed",
                side_effect=delayed_second_mark,
            ), ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(runtime.generate, requests[0], final=True)
                self.assertTrue(first_started.wait(5))
                second = pool.submit(runtime.generate, requests[1])
                self.assertTrue(second_receipted.wait(5))
                release_first.set()
                with self.assertRaisesRegex(PolicyError, "MP401"):
                    first.result(timeout=5)
                self.assertTrue(second_mark_started.wait(5))
                finalized_before_second = runtime._terminal_finalized
                records_before_second = [
                    json.loads(line)
                    for line in (root / "receipts.jsonl")
                    .read_text("utf-8")
                    .splitlines()
                ]
                release_second_mark.set()
                with self.assertRaisesRegex(PolicyError, "MP401"):
                    second.result(timeout=5)

            self.assertTrue(finalized_before_second)
            self.assertEqual(
                ["activation", "request", "request", "terminal"],
                [record["event"] for record in records_before_second],
            )

    def test_unknown_token_counter_refuses_before_activation(self):
        unknown = replace(self.profile, token_counter="unknown-counter/v1")
        with mock.patch(
            "model_proxy_lib.lifecycle.resolve_profile", return_value=unknown
        ):
            with self.assertRaisesRegex(PolicyError, "MP409"):
                self.controller()

    def test_non_finite_transport_deadlines_refuse_before_resolution(self):
        resolutions = []
        connector = HTTPSConnector(
            self.profile,
            resolver=lambda _hostname, _port: resolutions.append(True)
            or ("8.8.8.8",),
            exchange=HTTPSExchangeFixture(
                BufferedHTTPSResponse(
                    synthetic_provider_response("unused", "UNUSED")
                )
            ),
        )
        for value in (
            float("nan"),
            float("inf"),
            float("-inf"),
            10**10_000,
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                PolicyError, "MP300"
            ):
                connector.send(
                    b"{}",
                    self.credential,
                    max_response_bytes=1,
                    timeout_seconds=value,
                )
        self.assertEqual([], resolutions)

    def test_non_finite_connector_timeout_refuses_before_context_or_resolution(self):
        contexts = []
        resolutions = []
        for value in (float("nan"), float("inf")):
            with self.subTest(value=value):
                try:
                    HTTPSConnector(
                        self.profile,
                        resolver=lambda _hostname, _port: resolutions.append(True)
                        or ("8.8.8.8",),
                        context_factory=lambda: contexts.append(True),
                        timeout=value,
                    )
                except PolicyError as error:
                    code = error.code
                else:
                    code = None
                self.assertEqual("MP300", code)
        self.assertEqual([], contexts)
        self.assertEqual([], resolutions)

    def test_connector_timeout_cannot_widen_global_transport_ceiling(self):
        seen_timeouts = []

        def exchange(_request, _context, timeout):
            seen_timeouts.append(timeout)
            return BufferedHTTPSResponse(b"{}")

        connector = HTTPSConnector(
            self.profile,
            resolver=lambda _hostname, _port: ("8.8.8.8",),
            exchange=exchange,
            clock=iter((10_000, 20_000)).__next__,
            timeout=60.0,
        )
        connector.send(
            b"{}",
            self.credential,
            max_response_bytes=16,
            timeout_seconds=120.0,
        )

        self.assertEqual([30.0], seen_timeouts)

    def test_invalid_credential_is_not_recorded_as_provider_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response = BufferedHTTPSResponse(
                synthetic_provider_response("credential prompt", "UNUSED")
            )
            exchange = HTTPSExchangeFixture(response)
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: "invalid",
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            request = runtime.feed(request_frame("credential prompt"))[0]
            runtime.finish_input()

            with self.assertRaisesRegex(PolicyError, "MP321"):
                runtime.generate(request)

            self.assertEqual([], exchange.requests)
            self.assertEqual("not-read", runtime.provider_events[-1].disclosure_state)
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual("not-read", records[-1]["disclosure_state"])

    def test_invalid_later_credential_preserves_prior_provider_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response = BufferedHTTPSResponse(
                synthetic_provider_response("first prompt", "FIRST")
            )
            exchange = HTTPSExchangeFixture(response)
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000, 30_000, 40_000)).__next__,
            )
            credentials = iter((self.credential, "invalid"))
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: next(credentials),
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            first, second = runtime.feed(
                request_frame("first prompt") + request_frame("second prompt")
            )
            runtime.finish_input()

            runtime.generate(first)
            with self.assertRaisesRegex(PolicyError, "MP321"):
                runtime.generate(second)

            self.assertEqual(1, len(exchange.requests))
            self.assertEqual(
                [("MP000", "provider-only"), ("MP321", "not-read")],
                [
                    (event.code, event.disclosure_state)
                    for event in runtime.provider_events
                ],
            )
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual("provider-only", records[-1]["disclosure_state"])

    def test_provider_usage_under_and_over_reporting_are_terminal(self):
        cases = (
            {"input_tokens": len("usage prompt") - 1, "output_tokens": 5},
            {"input_tokens": len("usage prompt") + 1, "output_tokens": 5},
            {"input_tokens": len("usage prompt"), "output_tokens": 4},
            {"input_tokens": len("usage prompt"), "output_tokens": 6},
        )
        for usage in cases:
            with self.subTest(usage=usage), tempfile.TemporaryDirectory() as directory:
                response = BufferedHTTPSResponse(
                    synthetic_provider_response("usage prompt", "USAGE", usage=usage)
                )
                runtime, request, _exchange, _response = self.runtime_request(
                    Path(directory), response=response, input_text="usage prompt"
                )
                with self.assertRaisesRegex(PolicyError, "MP326"):
                    runtime.generate(request, final=True)
                self.assertEqual("MP326", runtime.terminal.code)

    def test_terminal_receipt_keeps_confirmed_refusal_response_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, request, _exchange, _response = self.runtime_request(
                root,
                response=BufferedHTTPSResponse(b"{"),
                input_text="refusing response progress",
            )
            with self.assertRaisesRegex(PolicyError, "MP323"):
                runtime.generate(request)
            provider_event = runtime.provider_events[-1]
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual(1, provider_event.response_bytes)
            self.assertEqual(
                provider_event.response_bytes,
                records[-1]["counts"]["response_bytes"],
            )

    def test_receipt_schema_count_size_mode_and_duplicate_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipts.jsonl"
            sink = ReceiptSink(path, max_record_bytes=4_096, max_records=3)
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            self.write_activation(sink)
            sink.write_request(
                job_id=self.policy.document["job"]["id"],
                jobspec_sha256=self.policy.jobspec_sha256,
                policy_sha256=self.policy.policy_sha256,
                profile=self.profile.identifier,
                versions=self.receipt_versions(),
                sequence=1,
                counts={
                    "request_bytes": 1,
                    "input_tokens": 1,
                    "reserved_output_tokens": 1,
                    "reserved_response_bytes": 1,
                    "concurrency": 1,
                },
                admitted_monotonic_ns=self.START_MONOTONIC_NS,
                remaining_wall_ns=1,
            )
            terminal_counts = {
                "requests": 1,
                "request_bytes": 1,
                "response_bytes": 1,
                "input_tokens": 1,
                "output_tokens": 1,
                "concurrency": 0,
            }
            sink.write_terminal(
                job_id=self.policy.document["job"]["id"],
                jobspec_sha256=self.policy.jobspec_sha256,
                policy_sha256=self.policy.policy_sha256,
                profile=self.profile.identifier,
                versions=self.receipt_versions(),
                counts=terminal_counts,
                terminal_monotonic_ns=self.START_MONOTONIC_NS + 1,
                duration_ns=1,
                disclosure_state="provider-only",
                outcome_code="MP000",
            )
            before = path.read_bytes()
            with self.assertRaisesRegex(PolicyError, "MP407"):
                sink.write_terminal(
                    job_id=self.policy.document["job"]["id"],
                    jobspec_sha256=self.policy.jobspec_sha256,
                    policy_sha256=self.policy.policy_sha256,
                    profile=self.profile.identifier,
                    versions=self.receipt_versions(),
                    counts=terminal_counts,
                    terminal_monotonic_ns=self.START_MONOTONIC_NS + 2,
                    duration_ns=2,
                    disclosure_state="provider-only",
                    outcome_code="MP000",
                )
            self.assertEqual(before, path.read_bytes())
            sink.close()
            lines = before.splitlines()
            self.assertEqual(3, len(lines))
            self.assertTrue(all(len(line) <= 4_096 for line in lines))
            records = [json.loads(line) for line in lines]
            self.assertTrue(
                all(record["schema"] == RECEIPT_SCHEMA for record in records)
            )
            self.assertEqual(
                ["activation", "request", "terminal"],
                [record["event"] for record in records],
            )

        with tempfile.TemporaryDirectory() as directory:
            sink = ReceiptSink(
                Path(directory) / "small.jsonl",
                max_record_bytes=128,
                max_records=3,
            )
            with self.assertRaisesRegex(PolicyError, "MP408"):
                self.write_activation(sink)
            sink.close()

        with tempfile.TemporaryDirectory() as directory:
            sink = ReceiptSink(
                Path(directory) / "count.jsonl",
                max_record_bytes=4_096,
                max_records=1,
            )
            self.write_activation(sink)
            with self.assertRaisesRegex(PolicyError, "MP407"):
                sink.write_request(
                    job_id=self.policy.document["job"]["id"],
                    jobspec_sha256=self.policy.jobspec_sha256,
                    policy_sha256=self.policy.policy_sha256,
                    profile=self.profile.identifier,
                    versions=self.receipt_versions(),
                    sequence=1,
                    counts={
                        "request_bytes": 1,
                        "input_tokens": 1,
                        "reserved_output_tokens": 1,
                        "reserved_response_bytes": 1,
                        "concurrency": 1,
                    },
                    admitted_monotonic_ns=1,
                    remaining_wall_ns=1,
                )
            sink.close()

    def test_receipt_activation_and_sequence_guards_are_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "concurrent.jsonl"
            sink = ReceiptSink(path, max_record_bytes=4_096, max_records=3)
            activation_barrier = threading.Barrier(8)

            def activate(_index):
                activation_barrier.wait()
                try:
                    self.write_activation(sink)
                    return "written"
                except PolicyError as error:
                    return error.code

            with ThreadPoolExecutor(max_workers=8) as pool:
                activation_results = list(pool.map(activate, range(8)))
            self.assertEqual(1, activation_results.count("written"))
            self.assertEqual(7, activation_results.count("MP407"))

            request_barrier = threading.Barrier(8)

            def write_request(_index):
                request_barrier.wait()
                try:
                    sink.write_request(
                        job_id=self.policy.document["job"]["id"],
                        jobspec_sha256=self.policy.jobspec_sha256,
                        policy_sha256=self.policy.policy_sha256,
                        profile=self.profile.identifier,
                        versions=self.receipt_versions(),
                        sequence=1,
                        counts={
                            "request_bytes": 1,
                            "input_tokens": 1,
                            "reserved_output_tokens": 1,
                            "reserved_response_bytes": 1,
                            "concurrency": 1,
                        },
                        admitted_monotonic_ns=self.START_MONOTONIC_NS,
                        remaining_wall_ns=1,
                    )
                    return "written"
                except PolicyError as error:
                    return error.code

            with ThreadPoolExecutor(max_workers=8) as pool:
                request_results = list(pool.map(write_request, range(8)))
            self.assertEqual(1, request_results.count("written"))
            self.assertEqual(7, request_results.count("MP407"))
            self.assertEqual(
                ["activation", "request"],
                [
                    json.loads(line)["event"]
                    for line in path.read_text("utf-8").splitlines()
                ],
            )
            sink.close()

    def test_receipt_identifiers_versions_counts_and_timings_are_closed(self):
        base = {
            "job_id": self.policy.document["job"]["id"],
            "jobspec_sha256": self.policy.jobspec_sha256,
            "policy_sha256": self.policy.policy_sha256,
            "profile": self.profile.identifier,
            "versions": self.receipt_versions(),
            "activated_monotonic_ns": self.START_MONOTONIC_NS,
            "absolute_expiry_unix_ns": 1_787_918_999
            * NANOSECONDS_PER_SECOND,
            "elapsed_deadline_ns": self.START_MONOTONIC_NS
            + 300 * NANOSECONDS_PER_SECOND,
        }
        cases = (
            {"job_id": "prompt contains spaces"},
            {"jobspec_sha256": "f" * 63 + "g"},
            {"profile": "raw-provider-name"},
            {
                "versions": {
                    **self.receipt_versions(),
                    "token_counter": "unknown/v1",
                }
            },
            {"activated_monotonic_ns": 10**30},
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, change in enumerate(cases):
                with self.subTest(change=change):
                    path = root / f"invalid-{index}.jsonl"
                    sink = ReceiptSink(
                        path, max_record_bytes=4_096, max_records=3
                    )
                    arguments = {**base, **change}
                    with self.assertRaisesRegex(PolicyError, "MP408"):
                        sink.write_activation(**arguments)
                    self.assertEqual(b"", path.read_bytes())
                    sink.close()

            path = root / "invalid-count.jsonl"
            sink = ReceiptSink(path, max_record_bytes=4_096, max_records=3)
            self.write_activation(sink)
            before = path.read_bytes()
            with self.assertRaisesRegex(PolicyError, "MP408"):
                sink.write_request(
                    job_id=self.policy.document["job"]["id"],
                    jobspec_sha256=self.policy.jobspec_sha256,
                    policy_sha256=self.policy.policy_sha256,
                    profile=self.profile.identifier,
                    versions=self.receipt_versions(),
                    sequence=1,
                    counts={
                        "request_bytes": 1,
                        "input_tokens": True,
                        "reserved_output_tokens": 1,
                        "reserved_response_bytes": 1,
                        "concurrency": 1,
                    },
                    admitted_monotonic_ns=self.START_MONOTONIC_NS,
                    remaining_wall_ns=1,
                )
            self.assertEqual(before, path.read_bytes())
            sink.close()

    def test_receipt_target_refuses_symlink_directory_preexisting_and_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_text("existing", encoding="utf-8")
            symlink = root / "link"
            symlink.symlink_to(target)
            folder = root / "folder"
            folder.mkdir()
            paths = (target, symlink, folder, root / "missing" / "receipt")
            for path in paths:
                with self.subTest(path=path), self.assertRaisesRegex(
                    PolicyError, "MP407"
                ):
                    ReceiptSink(path, max_record_bytes=4_096, max_records=3)

            parent_link = root / "parent-link"
            parent_link.symlink_to(folder, target_is_directory=True)
            with self.assertRaisesRegex(PolicyError, "MP407"):
                ReceiptSink(
                    parent_link / "receipt",
                    max_record_bytes=4_096,
                    max_records=3,
                )

    def test_receipt_parent_walk_close_failure_runs_runtime_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_parent = root / "nested"
            receipt_parent.mkdir()
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response("unused", "UNUSED")
                    )
                ),
            )
            closer = mock.Mock()
            closed_sessions = []
            original_provider_close = ProviderSession.close
            original_close = os.close
            close_failed = False

            def observed_provider_close(session):
                closed_sessions.append(session)
                original_provider_close(session)

            def failed_close(descriptor):
                nonlocal close_failed
                original_close(descriptor)
                if not close_failed:
                    close_failed = True
                    raise OSError("simulated parent-walk close failure")

            with mock.patch.object(
                ProviderSession,
                "close",
                autospec=True,
                side_effect=observed_provider_close,
            ), mock.patch(
                "model_proxy_lib.receipts.os.close", side_effect=failed_close
            ):
                try:
                    ModelProxyRuntime(
                        self.policy,
                        connector,
                        receipt_parent / "receipts.jsonl",
                        credential_source=lambda _name: self.credential,
                        monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                        wall_clock=MutableClock(self.START_WALL_NS),
                        io_closer=closer,
                    )
                    code = None
                except Exception as error:  # Keep parent replay assertion-only.
                    code = getattr(error, "code", None)

            self.assertEqual("MP407", code)
            self.assertEqual(1, len(closed_sessions))
            self.assertIsNone(closed_sessions[0]._credential_source)
            self.assertIsNone(closed_sessions[0]._connector)
            closer.assert_called_once_with()

    def test_receipt_target_setup_close_failure_runs_runtime_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response("unused", "UNUSED")
                    )
                ),
            )
            closer = mock.Mock()
            closed_sessions = []
            original_provider_close = ProviderSession.close
            original_close = os.close
            close_failed = False

            def observed_provider_close(session):
                closed_sessions.append(session)
                original_provider_close(session)

            def failed_close(descriptor):
                nonlocal close_failed
                original_close(descriptor)
                if not close_failed:
                    close_failed = True
                    raise OSError("simulated target-setup close failure")

            with mock.patch.object(
                ProviderSession,
                "close",
                autospec=True,
                side_effect=observed_provider_close,
            ), mock.patch(
                "model_proxy_lib.receipts.os.fchmod",
                side_effect=OSError("simulated target setup failure"),
            ), mock.patch(
                "model_proxy_lib.receipts.os.close", side_effect=failed_close
            ):
                try:
                    ModelProxyRuntime(
                        self.policy,
                        connector,
                        root / "receipts.jsonl",
                        credential_source=lambda _name: self.credential,
                        monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                        wall_clock=MutableClock(self.START_WALL_NS),
                        io_closer=closer,
                    )
                    code = None
                except Exception as error:  # Keep parent replay assertion-only.
                    code = getattr(error, "code", None)

            self.assertEqual("MP407", code)
            self.assertEqual(1, len(closed_sessions))
            self.assertIsNone(closed_sessions[0]._credential_source)
            self.assertIsNone(closed_sessions[0]._connector)
            closer.assert_called_once_with()

    def test_receipt_path_encoding_failure_runs_runtime_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response("unused", "UNUSED")
                    )
                ),
            )
            closer = mock.Mock()
            closed_sessions = []
            original_provider_close = ProviderSession.close

            def observed_provider_close(session):
                closed_sessions.append(session)
                original_provider_close(session)

            invalid_path = os.fspath(root) + os.sep + chr(0xD800)
            with mock.patch.object(
                ProviderSession,
                "close",
                autospec=True,
                side_effect=observed_provider_close,
            ):
                try:
                    ModelProxyRuntime(
                        self.policy,
                        connector,
                        invalid_path,
                        credential_source=lambda _name: self.credential,
                        monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                        wall_clock=MutableClock(self.START_WALL_NS),
                        io_closer=closer,
                    )
                    code = None
                except Exception as error:  # Keep parent replay assertion-only.
                    code = getattr(error, "code", None)

            self.assertEqual("MP407", code)
            self.assertEqual(1, len(closed_sessions))
            self.assertIsNone(closed_sessions[0]._credential_source)
            self.assertIsNone(closed_sessions[0]._connector)
            closer.assert_called_once_with()

    def test_receipt_restrictive_umask_short_partial_and_replacement_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "umask.jsonl"
            previous = os.umask(0o777)
            try:
                sink = ReceiptSink(path, max_record_bytes=4_096, max_records=3)
            finally:
                os.umask(previous)
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            sink.close()

        with tempfile.TemporaryDirectory() as directory:
            sink = ReceiptSink(
                Path(directory) / "short.jsonl",
                max_record_bytes=4_096,
                max_records=3,
            )
            with mock.patch("model_proxy_lib.receipts.os.write", return_value=0):
                with self.assertRaisesRegex(PolicyError, "MP407"):
                    self.write_activation(sink)
            sink.close()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.jsonl"
            sink = ReceiptSink(path, max_record_bytes=4_096, max_records=3)
            original_write = os.write

            def partial_write(descriptor, data):
                partial = data[: max(1, len(data) // 2)]
                return original_write(descriptor, partial)

            with mock.patch(
                "model_proxy_lib.receipts.os.write", side_effect=partial_write
            ):
                with self.assertRaisesRegex(PolicyError, "MP407"):
                    self.write_activation(sink)
            self.assertGreater(path.stat().st_size, 0)
            sink.close()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "receipts"
            parent.mkdir()
            path = parent / "job.jsonl"
            sink = ReceiptSink(path, max_record_bytes=4_096, max_records=3)
            self.write_activation(sink)
            before = path.read_bytes()
            moved = root / "moved-receipts"
            parent.rename(moved)
            parent.mkdir()
            with self.assertRaisesRegex(PolicyError, "MP407"):
                sink.write_request(
                    job_id=self.policy.document["job"]["id"],
                    jobspec_sha256=self.policy.jobspec_sha256,
                    policy_sha256=self.policy.policy_sha256,
                    profile=self.profile.identifier,
                    versions=self.receipt_versions(),
                    sequence=1,
                    counts={
                        "request_bytes": 1,
                        "input_tokens": 1,
                        "reserved_output_tokens": 1,
                        "reserved_response_bytes": 1,
                        "concurrency": 1,
                    },
                    admitted_monotonic_ns=self.START_MONOTONIC_NS,
                    remaining_wall_ns=1,
                )
            self.assertEqual(before, (moved / "job.jsonl").read_bytes())
            sink.close()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "durable.jsonl"
            sink = ReceiptSink(path, max_record_bytes=4_096, max_records=3)
            synced = []
            original_fsync = os.fsync

            def observed_fsync(descriptor):
                synced.append(descriptor)
                original_fsync(descriptor)

            with mock.patch(
                "model_proxy_lib.receipts.os.fsync", side_effect=observed_fsync
            ):
                self.write_activation(sink)
            self.assertIn(sink._descriptor, synced)
            self.assertIn(sink._parent_descriptor, synced)
            sink.close()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "replacement.jsonl"
            sink = ReceiptSink(path, max_record_bytes=4_096, max_records=3)
            replacement = root / "other"
            replacement.write_text("replacement", encoding="utf-8")
            os.replace(replacement, path)
            with self.assertRaisesRegex(PolicyError, "MP407"):
                self.write_activation(sink)
            sink.close()

        with tempfile.TemporaryDirectory() as directory:
            sink = ReceiptSink(
                Path(directory) / "close.jsonl",
                max_record_bytes=4_096,
                max_records=3,
            )
            receipt_descriptor = sink._descriptor
            original_close = os.close
            failed = False

            def failed_close(descriptor):
                nonlocal failed
                if descriptor == receipt_descriptor and not failed:
                    failed = True
                    original_close(descriptor)
                    raise OSError("simulated close failure")
                original_close(descriptor)

            with mock.patch(
                "model_proxy_lib.receipts.os.close", side_effect=failed_close
            ):
                with self.assertRaisesRegex(PolicyError, "MP407"):
                    sink.close()

    def test_pre_disclosure_receipt_failure_prevents_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reads = []
            response = BufferedHTTPSResponse(
                synthetic_provider_response("blocked prompt", "BLOCKED")
            )
            exchange = HTTPSExchangeFixture(response)
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda name: reads.append(name) or self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            request = runtime.feed(request_frame("blocked prompt"))[0]
            runtime.finish_input()
            with mock.patch.object(
                runtime._sink,
                "write_request",
                side_effect=PolicyError("MP407", "receipt.write"),
            ):
                with self.assertRaisesRegex(PolicyError, "MP407"):
                    runtime.generate(request)
            self.assertEqual([], reads)
            self.assertEqual([], exchange.requests)

    def test_expiry_during_request_receipt_prevents_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monotonic = MutableClock(self.START_MONOTONIC_NS)
            reads = []
            exchange = HTTPSExchangeFixture(
                BufferedHTTPSResponse(
                    synthetic_provider_response("receipt delay", "TOO LATE")
                )
            )
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda name: reads.append(name) or self.credential,
                monotonic_clock=monotonic,
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            request = runtime.feed(request_frame("receipt delay"))[0]
            runtime.finish_input()
            original_write = runtime._sink.write_request

            def delayed_write(**arguments):
                original_write(**arguments)
                monotonic.set(
                    self.START_MONOTONIC_NS
                    + self.policy.document["limits"]["total_wall_seconds"]
                    * NANOSECONDS_PER_SECOND
                )

            with mock.patch.object(
                runtime._sink, "write_request", side_effect=delayed_write
            ):
                with self.assertRaisesRegex(PolicyError, "MP405"):
                    runtime.generate(request)
            self.assertEqual([], reads)
            self.assertEqual([], exchange.requests)
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual(
                ["activation", "request", "terminal"],
                [record["event"] for record in records],
            )
            self.assertEqual("not-read", records[-1]["disclosure_state"])
            self.assertEqual("MP405", records[-1]["outcome_code"])

    def test_expiry_after_provider_completion_withholds_final_response(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monotonic = MutableClock(self.START_MONOTONIC_NS)
            exchange = HTTPSExchangeFixture(
                BufferedHTTPSResponse(
                    synthetic_provider_response("completion expiry", "TOO LATE")
                )
            )
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=monotonic,
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            request = runtime.feed(request_frame("completion expiry"))[0]
            runtime.finish_input()
            original_ready = runtime._provider.require_completion_ready

            def expire_before_finish():
                original_ready()
                monotonic.set(runtime._controller.elapsed_deadline_ns)

            with mock.patch.object(
                runtime._provider,
                "require_completion_ready",
                side_effect=expire_before_finish,
            ):
                with self.assertRaisesRegex(PolicyError, "MP405"):
                    runtime.generate(request, final=True)

            self.assertEqual("MP405", runtime.terminal.code)
            self.assertEqual(1, len(exchange.requests))
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual(
                ["activation", "request", "terminal"],
                [record["event"] for record in records],
            )
            self.assertEqual("MP405", records[-1]["outcome_code"])

    def test_post_provider_expiry_keeps_confirmed_success_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monotonic = MutableClock(self.START_MONOTONIC_NS)
            input_text = "late successful response"
            response = BufferedHTTPSResponse(
                synthetic_provider_response(input_text, "LATE")
            )
            runtime_box = {}

            def exchange(_request, _context, _timeout):
                monotonic.set(runtime_box["runtime"]._controller.elapsed_deadline_ns)
                return response

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=monotonic,
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            runtime_box["runtime"] = runtime
            request = runtime.feed(request_frame(input_text))[0]
            runtime.finish_input()

            try:
                guest_response = runtime.generate(request)
                code = None
            except PolicyError as error:
                guest_response = None
                code = error.code

            event = runtime.provider_events[-1]
            self.assertEqual(("MP405", None), (code, guest_response))
            self.assertEqual("MP000", event.code)
            self.assertGreater(event.response_bytes, 0)
            self.assertGreater(event.output_tokens, 0)
            self.assertEqual("MP405", runtime.terminal.code)
            self.assertEqual(
                (event.response_bytes, event.output_tokens),
                (
                    runtime.terminal.counts["response_bytes"],
                    runtime.terminal.counts["output_tokens"],
                ),
            )
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual("MP405", records[-1]["outcome_code"])
            self.assertEqual(
                (event.response_bytes, event.output_tokens),
                (
                    records[-1]["counts"]["response_bytes"],
                    records[-1]["counts"]["output_tokens"],
                ),
            )

    def test_post_provider_refusal_reports_the_expiry_winner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monotonic = MutableClock(self.START_MONOTONIC_NS)
            input_text = "late refusing response"
            response = BufferedHTTPSResponse(b"{")
            runtime_box = {}

            def exchange(_request, _context, _timeout):
                monotonic.set(runtime_box["runtime"]._controller.elapsed_deadline_ns)
                return response

            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
                clock=iter((10_000, 20_000)).__next__,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=monotonic,
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            runtime_box["runtime"] = runtime
            request = runtime.feed(request_frame(input_text))[0]
            runtime.finish_input()

            try:
                guest_response = runtime.generate(request)
                code = None
            except PolicyError as error:
                guest_response = None
                code = error.code

            event = runtime.provider_events[-1]
            self.assertEqual(("MP405", None), (code, guest_response))
            self.assertEqual("MP323", event.code)
            self.assertEqual(1, event.response_bytes)
            self.assertEqual("MP405", runtime.terminal.code)
            self.assertEqual(1, runtime.terminal.counts["response_bytes"])
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual("MP405", records[-1]["outcome_code"])
            self.assertEqual(1, records[-1]["counts"]["response_bytes"])

    def test_clock_failure_after_request_receipt_prevents_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reads = []
            exchange = HTTPSExchangeFixture(
                BufferedHTTPSResponse(
                    synthetic_provider_response("clock receipt", "TOO LATE")
                )
            )
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "receipts.jsonl",
                credential_source=lambda name: reads.append(name) or self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            request = runtime.feed(request_frame("clock receipt"))[0]
            runtime.finish_input()
            original_write = runtime._sink.write_request

            def fail_clock_after_write(**arguments):
                original_write(**arguments)
                runtime._controller._monotonic_clock = lambda: (
                    _ for _ in ()
                ).throw(RuntimeError("clock unavailable"))

            with mock.patch.object(
                runtime._sink,
                "write_request",
                side_effect=fail_clock_after_write,
            ):
                with self.assertRaisesRegex(PolicyError, "MP405"):
                    runtime.generate(request)

            self.assertIsNotNone(runtime.terminal)
            self.assertEqual([], reads)
            self.assertEqual([], exchange.requests)
            records = [
                json.loads(line)
                for line in (root / "receipts.jsonl").read_text("utf-8").splitlines()
            ]
            self.assertEqual(
                ["activation", "request", "terminal"],
                [record["event"] for record in records],
            )
            self.assertEqual("MP405", records[-1]["outcome_code"])

    def test_terminal_receipt_failure_withholds_provider_response(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime, request, exchange, _response = self.runtime_request(
                Path(directory), input_text="terminal receipt prompt"
            )
            with mock.patch.object(
                runtime._sink,
                "write_terminal",
                side_effect=PolicyError("MP407", "receipt.write"),
            ):
                with self.assertRaisesRegex(PolicyError, "MP407"):
                    runtime.generate(request, final=True)
            self.assertEqual(1, len(exchange.requests))
            self.assertTrue(runtime._terminal_receipt_failed)

    def test_io_cleanup_failure_withholds_terminal_response(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime, request, exchange, _response = self.runtime_request(
                Path(directory),
                input_text="cleanup failure prompt",
                closer=mock.Mock(side_effect=RuntimeError("close failed")),
            )
            with self.assertRaisesRegex(PolicyError, "MP407"):
                runtime.generate(request, final=True)
            self.assertEqual(1, len(exchange.requests))
            self.assertTrue(runtime._terminal_receipt_failed)
            self.assertIsNone(runtime._provider._credential_source)
            self.assertIsNone(runtime._provider._connector)
            self.assertEqual({}, runtime._provider._admitted)
            records = [
                json.loads(line)
                for line in (Path(directory) / "receipts.jsonl")
                .read_text("utf-8")
                .splitlines()
            ]
            self.assertEqual(["activation", "request"], [r["event"] for r in records])

    def test_provider_cleanup_failure_erases_authority_and_runs_io_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            closer = mock.Mock()
            runtime, _request, _exchange, _response = self.runtime_request(
                Path(directory),
                input_text="provider cleanup failure prompt",
                closer=closer,
            )
            provider = runtime._provider

            with mock.patch.object(
                provider._framing,
                "close",
                side_effect=OSError("simulated framing cleanup failure"),
            ):
                with self.assertRaisesRegex(PolicyError, "MP407"):
                    runtime.cancel()

            self.assertIsNone(provider._credential_source)
            self.assertIsNone(provider._connector)
            closer.assert_called_once_with()

    def test_response_close_failure_withholds_guest_output(self):
        class CloseFailureResponse(BufferedHTTPSResponse):
            def close(self):
                self.closed = True
                raise OSError("simulated response close failure")

        with tempfile.TemporaryDirectory() as directory:
            prompt = "response close prompt"
            response = CloseFailureResponse(
                synthetic_provider_response(prompt, "MUST NOT ESCAPE")
            )
            runtime, request, exchange, _response = self.runtime_request(
                Path(directory), response=response, input_text=prompt
            )

            try:
                guest_response = runtime.generate(request, final=True)
                code = None
            except PolicyError as error:
                guest_response = None
                code = error.code

            self.assertEqual(("MP306", None), (code, guest_response))
            self.assertEqual("MP306", runtime.terminal.code)
            self.assertEqual(1, len(exchange.requests))
            self.assertTrue(response.closed)
            records = [
                json.loads(line)
                for line in (Path(directory) / "receipts.jsonl")
                .read_text("utf-8")
                .splitlines()
            ]
            self.assertEqual("MP306", records[-1]["outcome_code"])

    def test_receipt_target_refusal_closes_constructor_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "receipts.jsonl"
            target.write_text("pre-existing", encoding="utf-8")
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response("unused", "UNUSED")
                    )
                ),
            )
            closed_sessions = []
            closer = mock.Mock()
            original_close = ProviderSession.close

            def observed_close(session):
                closed_sessions.append(session)
                with mock.patch.object(
                    session._framing,
                    "close",
                    side_effect=OSError("simulated framing cleanup failure"),
                ):
                    original_close(session)

            with mock.patch.object(
                ProviderSession,
                "close",
                autospec=True,
                side_effect=observed_close,
            ):
                try:
                    ModelProxyRuntime(
                        self.policy,
                        connector,
                        target,
                        credential_source=lambda _name: self.credential,
                        monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                        wall_clock=MutableClock(self.START_WALL_NS),
                        io_closer=closer,
                    )
                    code = None
                except Exception as error:  # Keep the parent replay assertion-only.
                    code = getattr(error, "code", None)

            self.assertEqual("MP407", code)
            self.assertEqual(1, len(closed_sessions))
            self.assertIsNone(closed_sessions[0]._credential_source)
            self.assertIsNone(closed_sessions[0]._connector)
            closer.assert_called_once_with()

    def test_activation_refusal_runs_all_cleanup_after_provider_close_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response("unused", "UNUSED")
                    )
                ),
            )
            closed_sessions = []
            closed_sinks = []
            closer = mock.Mock()
            original_provider_close = ProviderSession.close
            original_sink_close = ReceiptSink.close

            def observed_provider_close(session):
                closed_sessions.append(session)
                with mock.patch.object(
                    session._framing,
                    "close",
                    side_effect=OSError("simulated framing cleanup failure"),
                ):
                    original_provider_close(session)

            def observed_sink_close(sink):
                closed_sinks.append(sink)
                original_sink_close(sink)

            with mock.patch.object(
                ReceiptSink,
                "write_activation",
                autospec=True,
                side_effect=PolicyError("MP407", "receipt.activation"),
            ), mock.patch.object(
                ProviderSession,
                "close",
                autospec=True,
                side_effect=observed_provider_close,
            ), mock.patch.object(
                ReceiptSink,
                "close",
                autospec=True,
                side_effect=observed_sink_close,
            ):
                try:
                    ModelProxyRuntime(
                        self.policy,
                        connector,
                        root / "receipts.jsonl",
                        credential_source=lambda _name: self.credential,
                        monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                        wall_clock=MutableClock(self.START_WALL_NS),
                        io_closer=closer,
                    )
                    code = None
                except Exception as error:  # Keep the parent replay assertion-only.
                    code = getattr(error, "code", None)

            self.assertEqual("MP407", code)
            self.assertEqual(1, len(closed_sessions))
            self.assertIsNone(closed_sessions[0]._credential_source)
            self.assertIsNone(closed_sessions[0]._connector)
            self.assertEqual(1, len(closed_sinks))
            closer.assert_called_once_with()

    def test_terminal_paths_refuse_truncated_and_unserved_guest_frames(self):
        def connector_for(input_text):
            return HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response(input_text, "MUST NOT ESCAPE")
                    )
                ),
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exchange = HTTPSExchangeFixture(
                BufferedHTTPSResponse(
                    synthetic_provider_response("truncated", "MUST NOT ESCAPE")
                )
            )
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=exchange,
            )
            runtime = ModelProxyRuntime(
                self.policy,
                connector,
                root / "partial.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            request = runtime.feed(request_frame("truncated") + b"\x00\x00")[0]
            try:
                guest_response = runtime.generate(request, final=True)
                code = None
            except PolicyError as error:
                guest_response = None
                code = error.code
            self.assertEqual(("MP202", None), (code, guest_response))
            self.assertEqual("MP202", runtime.terminal.code)
            self.assertEqual([], exchange.requests)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exchange = HTTPSExchangeFixture(
                BufferedHTTPSResponse(
                    synthetic_provider_response("first", "MUST NOT ESCAPE")
                )
            )
            runtime = ModelProxyRuntime(
                self.policy,
                HTTPSConnector(
                    self.profile,
                    resolver=lambda _hostname, _port: ("8.8.8.8",),
                    exchange=exchange,
                ),
                root / "pending-final.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            requests = runtime.feed(
                request_frame("first") + request_frame("unserved second")
            )
            runtime.finish_input()
            try:
                guest_response = runtime.generate(requests[0], final=True)
                code = None
            except PolicyError as error:
                guest_response = None
                code = error.code
            self.assertEqual(("MP401", None), (code, guest_response))
            self.assertEqual("MP401", runtime.terminal.code)
            self.assertEqual(1, len(exchange.requests))

        with tempfile.TemporaryDirectory() as directory:
            runtime = ModelProxyRuntime(
                self.policy,
                connector_for("pending completion"),
                Path(directory) / "pending-complete.jsonl",
                credential_source=lambda _name: self.credential,
                monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                wall_clock=MutableClock(self.START_WALL_NS),
            )
            runtime.feed(request_frame("pending completion"))
            runtime.finish_input()
            try:
                runtime.complete_job()
                code = None
            except PolicyError as error:
                code = error.code
            self.assertEqual("MP401", code)
            self.assertEqual("MP401", runtime.terminal.code)

    def test_restart_cannot_resume_an_existing_receipt_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, request, _exchange, _response = self.runtime_request(root)
            runtime.generate(request, final=True)
            connector = HTTPSConnector(
                self.profile,
                resolver=lambda _hostname, _port: ("8.8.8.8",),
                exchange=HTTPSExchangeFixture(
                    BufferedHTTPSResponse(
                        synthetic_provider_response("unused", "UNUSED")
                    )
                ),
            )
            with self.assertRaisesRegex(PolicyError, "MP407"):
                ModelProxyRuntime(
                    self.policy,
                    connector,
                    root / "receipts.jsonl",
                    credential_source=lambda _name: self.credential,
                    monotonic_clock=MutableClock(self.START_MONOTONIC_NS),
                    wall_clock=MutableClock(self.START_WALL_NS),
                )

    def test_receipts_exclude_content_authority_secrets_and_raw_errors(self):
        prompt = "fiat-700-sensitive-prompt"
        output = "fiat-700-sensitive-response"
        raw_error = "fiat-700-raw-provider-error"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response = BufferedHTTPSResponse(
                synthetic_provider_response(prompt, output)
            )
            runtime, request, _exchange, _response = self.runtime_request(
                root, response=response, input_text=prompt
            )
            runtime.generate(request, final=True)
            receipt = (root / "receipts.jsonl").read_bytes()
            forbidden = (
                self.credential.encode("ascii"),
                prompt.encode("ascii"),
                output.encode("ascii"),
                hashlib.sha256(prompt.encode("ascii")).hexdigest().encode("ascii"),
                b"https://",
                b"Authorization",
                raw_error.encode("ascii"),
                b"synthetic-loopback",
                b"provider_id",
                b"request_id",
            )
            for value in forbidden:
                self.assertNotIn(value, receipt)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exchange = HTTPSExchangeFixture(error=RuntimeError(raw_error))
            runtime, request, _exchange, _response = self.runtime_request(
                root, exchange=exchange, input_text=prompt
            )
            with self.assertRaisesRegex(PolicyError, "MP306"):
                runtime.generate(request)
            receipt = (root / "receipts.jsonl").read_bytes()
            self.assertNotIn(raw_error.encode("ascii"), receipt)
            self.assertNotIn(prompt.encode("ascii"), receipt)

    def test_operator_text_is_an_exact_policy_projection_with_qualification(self):
        text = render_operator_text(self.policy)
        provider = self.policy.document["provider"]
        receipt = self.policy.document["receipt"]
        self.assertIn(provider["provider"], text)
        self.assertIn(provider["origin_family"] + provider["path_family"], text)
        self.assertIn(provider["id"], text)
        self.assertIn(provider["model"], text)
        self.assertIn(provider["retention"], text)
        self.assertIn(f"storage={str(provider['storage']).lower()}", text)
        self.assertIn(
            f"{receipt['content']} model content for {receipt['retention_seconds']} seconds",
            text,
        )
        for feature in self.policy.document["disclosure"]["disabled_features"]:
            self.assertIn(feature, text)
        for name, value in self.policy.document["limits"].items():
            self.assertIn(f"{name}={value}", text)
        self.assertIn("do not prove", text)
        self.assertIn("retain or exfiltrate", text)


class ConformanceTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.manifest_path = FIXTURES / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.policy = compile_policy_file(FIXTURES / "accepted-job.json")

    def _write_manifest(
        self,
        root: Path,
        document: dict[str, object],
        *,
        update_digest: bool = True,
    ) -> Path:
        value = deepcopy(document)
        if update_digest:
            value["manifest_sha256"] = conformance_manifest_digest(value)
        path = root / "manifest.json"
        path.write_text(
            json.dumps(value, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        (root / "accepted-job.json").write_bytes(
            (FIXTURES / "accepted-job.json").read_bytes()
        )
        return path

    def _assert_manifest_refuses(self, mutate, *, update_digest: bool = True):
        with tempfile.TemporaryDirectory() as directory:
            document = deepcopy(self.manifest)
            mutate(document)
            path = self._write_manifest(
                Path(directory), document, update_digest=update_digest
            )
            with self.assertRaisesRegex(PolicyError, "MP500"):
                check_conformance_manifest(path)

    def _check_valid_manifest(self, path):
        try:
            result = check_conformance_manifest(path)
            code = None
        except PolicyError as error:
            result = None
            code = error.code
        self.assertIsNone(code)  # Keep parent replay assertion-only.
        return result

    def test_manifest_digest_order_and_complete_row_contract_are_exact(self):
        self.assertEqual(CONFORMANCE_MANIFEST_SCHEMA, self.manifest["schema"])
        self.assertEqual(
            self.manifest["manifest_sha256"],
            conformance_manifest_digest(self.manifest),
        )
        self.assertEqual(
            [(identifier, outcome) for identifier, outcome, _state in EXPECTED_ROWS],
            [
                (row["id"], row["expected_outcome"])
                for row in self.manifest["rows"]
            ],
        )
        self.assertEqual(14, len(self.manifest["rows"]))
        self.assertEqual(14, len({row["id"] for row in self.manifest["rows"]}))
        self.assertEqual(self.policy.jobspec_sha256, self.manifest["jobspec_sha256"])
        self.assertEqual(self.policy.policy_sha256, self.manifest["policy_sha256"])

    def test_manifest_refuses_schema_shape_digest_and_every_row_drift(self):
        cases = (
            ("unknown-root", lambda value: value.__setitem__("extra", True), True),
            (
                "schema",
                lambda value: value.__setitem__("schema", "model-proxy-conformance-manifest/v2"),
                True,
            ),
            (
                "accepted-job",
                lambda value: value.__setitem__("accepted_job", "other.json"),
                True,
            ),
            ("stale-digest", lambda value: value["rows"].reverse(), False),
            ("omitted", lambda value: value["rows"].pop(), True),
            (
                "duplicate",
                lambda value: value["rows"].__setitem__(1, deepcopy(value["rows"][0])),
                True,
            ),
            (
                "order",
                lambda value: value["rows"].__setitem__(
                    slice(0, 2), [value["rows"][1], value["rows"][0]]
                ),
                True,
            ),
            (
                "unknown-row",
                lambda value: value["rows"][3].__setitem__("id", "unknown"),
                True,
            ),
            (
                "expected-outcome",
                lambda value: value["rows"][3].__setitem__(
                    "expected_outcome", "MP000"
                ),
                True,
            ),
            (
                "row-shape",
                lambda value: value["rows"][3].__setitem__("skip", True),
                True,
            ),
        )
        for name, mutate, update_digest in cases:
            with self.subTest(name=name):
                self._assert_manifest_refuses(
                    mutate, update_digest=update_digest
                )

    def test_manifest_pins_jobspec_and_policy_before_any_row_executes(self):
        digest_mutations = (
            ("jobspec", "jobspec_sha256"),
            ("policy", "policy_sha256"),
        )
        for name, field in digest_mutations:
            with self.subTest(name=name):
                document = deepcopy(self.manifest)
                document[field] = "0" * 64
                with tempfile.TemporaryDirectory() as directory:
                    path = self._write_manifest(Path(directory), document)
                    with mock.patch.object(
                        conformance, "_execute_case"
                    ) as execute:
                        with self.assertRaisesRegex(PolicyError, "MP500"):
                            check_conformance_manifest(path)
                        execute.assert_not_called()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self._write_manifest(root, self.manifest)
            accepted = accepted_document()
            jobspec = jobspec_document(accepted)
            jobspec["job_id"] = "fiat-700-substituted-job"
            accepted["verified"]["job_id"] = jobspec["job_id"]
            raw_jobspec = encode_document(jobspec)
            accepted["jobspec_b64"] = base64.b64encode(raw_jobspec).decode("ascii")
            accepted["jobspec_sha256"] = sha256_bytes(raw_jobspec)
            (root / "accepted-job.json").write_bytes(encode_document(accepted))
            with mock.patch.object(conformance, "_execute_case") as execute:
                with self.assertRaisesRegex(PolicyError, "MP500"):
                    check_conformance_manifest(path)
                execute.assert_not_called()

    def test_unexecuted_or_missing_result_cannot_pass(self):
        unexecuted = ConformanceRowResult(
            identifier="positive",
            outcome="MP000",
            disclosure_state="provider-only",
            requests=0,
            request_bytes=0,
            response_bytes=0,
            guest_bytes=0,
            receipts=0,
            duration_ns=0,
            executed=False,
        )
        for value in (unexecuted, None):
            with self.subTest(result=value):
                with mock.patch.object(conformance, "_execute_case", return_value=value):
                    try:
                        check_conformance_manifest(self.manifest_path)
                        code = None
                    except PolicyError as error:
                        code = error.code
                    self.assertEqual("MP501", code)

    def test_every_hostile_case_executes_independently_with_its_fixed_outcome(self):
        for identifier, outcome, disclosure_state in EXPECTED_ROWS[1:]:
            with self.subTest(identifier=identifier):
                result = conformance._execute_case(identifier, self.policy)
                self.assertEqual(identifier, result.identifier)
                self.assertEqual(outcome, result.outcome)
                self.assertEqual(disclosure_state, result.disclosure_state)
                self.assertTrue(result.executed)
                self.assertEqual("complete", result.cleanup_state)
                if identifier == "replay-after-expiry":
                    self.assertEqual(1, result.requests)
                    self.assertEqual(1, result.request_bytes)
                    self.assertEqual("not-read", result.disclosure_state)

    def test_unsupported_method_row_attempts_http_method_authority(self):
        sentinel = object()
        with mock.patch.object(
            conformance, "_framing_refusal", return_value=sentinel
        ) as framing_refusal:
            self.assertIs(
                sentinel,
                conformance._execute_case("unsupported-method", self.policy),
            )
        identifier, outcome, policy, frame = framing_refusal.call_args.args
        declared = struct.unpack(">I", frame[:4])[0]
        request = json.loads(frame[4:])
        self.assertEqual("unsupported-method", identifier)
        self.assertEqual("MP207", outcome)
        self.assertIs(self.policy, policy)
        self.assertEqual(declared, len(frame) - 4)
        self.assertEqual(TEXT_OPERATION, request["operation"])
        self.assertEqual("GET", request["method"])

    def test_dns_rebinding_row_attempts_pinned_peer_substitution(self):
        sentinel = object()
        with mock.patch.object(
            conformance, "_provider_refusal", return_value=sentinel
        ) as provider_refusal:
            self.assertIs(
                sentinel,
                conformance._execute_case("dns-rebinding", self.policy),
            )
        self.assertEqual(
            ("dns-rebinding", "MP304", self.policy),
            provider_refusal.call_args.args,
        )
        self.assertEqual(
            ("8.8.8.8",),
            provider_refusal.call_args.kwargs["resolver"]("hostname", 443),
        )
        response = provider_refusal.call_args.kwargs["response"]
        self.assertIsInstance(response, conformance._Response)
        self.assertEqual("1.1.1.1", response.peer_address)

    def test_response_flood_row_streams_one_sentinel_beyond_the_cap(self):
        maximum = self.policy.document["limits"]["max_response_bytes"]
        responses = []

        def response(body, **kwargs):
            value = BufferedHTTPSResponse(body, **kwargs)
            responses.append(value)
            return value

        with mock.patch.object(conformance, "_Response", side_effect=response):
            result = conformance._execute_case("response-flood", self.policy)
        self.assertEqual("MP310", result.outcome)
        self.assertEqual("provider-only", result.disclosure_state)
        self.assertEqual(1, len(responses))
        self.assertEqual(maximum + 1, len(responses[0].body))
        self.assertEqual(
            (
                ("Content-Type", "application/json"),
                ("Transfer-Encoding", "chunked"),
            ),
            responses[0].headers,
        )
        remaining = maximum + 1
        expected_reads = []
        while remaining:
            size = min(READ_CHUNK_BYTES, remaining)
            expected_reads.append(size)
            remaining -= size
        self.assertEqual(expected_reads, responses[0].read_sizes)
        self.assertEqual(maximum + 1, sum(responses[0].read_sizes))
        self.assertEqual(maximum + 1, responses[0].position)
        self.assertTrue(responses[0].closed)

    def test_positive_surface_inventory_is_closed_and_each_scan_fails_shut(self):
        credential = b"credential-canary"
        input_content = b"input-content-canary"
        output_content = b"output-content-canary"
        empty = {name: b"" for name in POSITIVE_SURFACES}
        conformance._scan_positive_surfaces(
            empty,
            credential=credential,
            input_content=input_content,
            output_content=output_content,
        )
        poison = {
            "guest_frames": credential,
            "receipts": input_content,
            "events": output_content,
            "diagnostics": credential,
            "argv": input_content,
            "environment_fixture": output_content,
            "produced_tree": credential,
        }
        self.assertEqual(
            {
                "argv",
                "diagnostics",
                "environment_fixture",
                "events",
                "guest_frames",
                "produced_tree",
                "receipts",
            },
            set(poison),
        )
        for name, value in poison.items():
            with self.subTest(surface=name):
                surfaces = dict(empty)
                surfaces[name] = value
                with self.assertRaisesRegex(PolicyError, "MP501"):
                    conformance._scan_positive_surfaces(
                        surfaces,
                        credential=credential,
                        input_content=input_content,
                        output_content=output_content,
                    )
        missing = dict(empty)
        missing.pop("argv")
        with self.assertRaisesRegex(PolicyError, "MP501"):
            conformance._scan_positive_surfaces(
                missing,
                credential=credential,
                input_content=input_content,
                output_content=output_content,
            )

    def test_positive_row_proves_component_path_and_keeps_dependencies_open(self):
        result = self._check_valid_manifest(self.manifest_path)
        document = result.document()
        self.assertEqual(
            {
                "policy_jobspec_binding": "established",
                "loopback_credential_injection": "established",
                "normalised_response": "established",
                "bounded_receipts": "established",
                "operator_disclosure": "established",
                "canary_content_absence": "established",
            },
            document["proofs"],
        )
        self.assertEqual(DEPENDENCY_BOUNDARIES, document["dependencies"])
        self.assertEqual(
            {
                "issue_698_acceptance_receipt",
                "issue_699_launch_receipt",
                "live_provider",
                "public_pilot",
                "end_to_end_digest_join",
            },
            set(document["dependencies"]),
        )
        self.assertTrue(
            all(
                status == "not-established"
                for status in document["dependencies"].values()
            )
        )
        with self.assertRaises(TypeError):
            DEPENDENCY_BOUNDARIES["live_provider"] = "established"

    def test_cli_summary_is_exact_safe_and_content_free(self):
        result = self._check_valid_manifest(self.manifest_path)
        expected = result.document()
        completed = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
            [
                sys.executable,
                str(CLI),
                "conformance",
                "--manifest",
                str(self.manifest_path),
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(b"", completed.stderr)
        self.assertEqual(expected, json.loads(completed.stdout))
        self.assertEqual(CONFORMANCE_RESULT_SCHEMA, expected["schema"])
        self.assertEqual(
            {
                "rows": 14,
                "positive": 1,
                "hostile": 13,
                "executed": 14,
                "requests": 13,
                "receipts": 3,
            },
            expected["counts"],
        )
        self.assertEqual(
            {"request_bytes": 415, "response_bytes": 32902, "guest_bytes": 90},
            expected["sizes"],
        )
        self.assertEqual({"duration_ns": "4000000"}, expected["timings"])
        self.assertEqual("complete", expected["cleanup_state"])
        self.assertEqual(
            [(identifier, outcome) for identifier, outcome, _state in EXPECTED_ROWS],
            [(row["id"], row["outcome"]) for row in expected["rows"]],
        )
        encoded = completed.stdout
        for marker in (
            b"input-",
            b"output-",
            b"hostile-input",
            b"Authorization",
            b"Bearer ",
            b"WILDCAT_MODEL_PROXY_CREDENTIAL",
        ):
            self.assertNotIn(marker, encoded)

    def test_cli_refusal_is_fixed_and_does_not_echo_manifest_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = deepcopy(self.manifest)
            document["manifest_sha256"] = "0" * 64
            path = self._write_manifest(root, document, update_digest=False)
            marker = b"positive"
            completed = subprocess.run(  # phylax: allow subprocess: fixed local Python argv
                [sys.executable, str(CLI), "conformance", "--manifest", str(path)],
                check=False,
                capture_output=True,
            )
        self.assertEqual(2, completed.returncode)
        self.assertEqual(b"", completed.stdout)
        self.assertNotIn(marker, completed.stderr)
        self.assertNotIn(str(path).encode("utf-8"), completed.stderr)
        self.assertEqual(
            {
                "schema": "model-proxy-diagnostic/v1",
                "outcome": "refused",
                "code": "MP500",
                "field": "conformance.manifest",
            },
            json.loads(completed.stderr),
        )

    def test_skill_package_marketplace_coverage_and_portable_versions_are_exact(self):
        repository = PLUGIN_ROOT.parents[1]
        skill_root = PLUGIN_ROOT / "skills" / "phylax"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        evolution = (skill_root / "EVOLUTION.md").read_text(encoding="utf-8")
        self.assertIn('metadata:\n  version: "1.4.0"', skill)
        self.assertIn("- Current version: `phylax-v1.4.0`", evolution)
        for unchanged in (
            "- Frontier status: `mature`",
            "- Frontier revision: `off-chain-boundary-controls`",
            "- Current frontier: Phylax mechanically checks its established Python boundaries and source-local TypeScript controls for raw HTML ordering, persisted session credentials and runtime-selected absolute fetch hosts.",
            "- Next Fiat job: None -- mature",
            "| `phylax-v1.4.0` | generation | `off-chain-boundary-controls` | `3d0057bb195f303c0e40b5782bf59ab0cba53e3172478c6a331d5990236ac604` |",
        ):
            self.assertIn(unchanged, evolution)
        self.assertIn("#702 Fiat integration/end-to-end", skill)
        self.assertIn("#702 Fiat integration/end-to-end", evolution)
        self.assertIn(
            "#702 Fiat integration/end-to-end",
            (skill_root / "references" / "model-proxy-v1.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertIn(
            "#702 Fiat integration/end-to-end",
            (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8"),
        )

        package_versions = {
            "claude_manifest": json.loads(
                (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(
                    encoding="utf-8"
                )
            )["version"],
            "codex_manifest": json.loads(
                (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(
                    encoding="utf-8"
                )
            )["version"],
        }
        claude_marketplace = json.loads(
            (repository / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        agents_marketplace = json.loads(
            (repository / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        package_versions["claude_marketplace"] = next(
            entry["version"]
            for entry in claude_marketplace["plugins"]
            if entry["name"] == "hexaemeron"
        )
        package_versions["agents_marketplace"] = next(
            entry["version"]
            for entry in agents_marketplace["plugins"]
            if entry["name"] == "hexaemeron"
        )
        self.assertEqual({"1.6.7"}, set(package_versions.values()))
        self.assertNotEqual("1.4.0", package_versions["claude_manifest"])

        coverage = json.loads(
            (repository / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            hashlib.sha256((skill_root / "SKILL.md").read_bytes()).hexdigest(),
            coverage["runtime"]["phylax-boundary-review"]["sha256"],
        )

        portable_root = (
            repository
            / ".agents"
            / "skills"
            / "promise-machine"
            / "runtime"
            / "plugins"
            / "hexaemeron"
        )
        copied = (
            "README.md",
            "skills/phylax/SKILL.md",
            "skills/phylax/EVOLUTION.md",
            "skills/phylax/agents/openai.yaml",
            "skills/phylax/references/model-proxy-v1.md",
            "skills/phylax/scripts/model_proxy.py",
            "skills/phylax/scripts/model_proxy_lib/__init__.py",
            "skills/phylax/scripts/model_proxy_lib/conformance.py",
            "tests/fixtures/model-proxy-v1/accepted-job.json",
            "tests/fixtures/model-proxy-v1/duplicate-field.json",
            "tests/fixtures/model-proxy-v1/excessive-depth.json",
            "tests/fixtures/model-proxy-v1/framing-cases.json",
            "tests/fixtures/model-proxy-v1/invalid-unicode.json",
            "tests/fixtures/model-proxy-v1/jobspec.json",
            "tests/fixtures/model-proxy-v1/lifecycle-cases.json",
            "tests/fixtures/model-proxy-v1/manifest.json",
            "tests/fixtures/model-proxy-v1/policy.json",
            "tests/fixtures/model-proxy-v1/policy.sha256",
            "tests/fixtures/model-proxy-v1/provider-cases.json",
            "tests/fixtures/model-proxy-v1/rejections.json",
        )
        portable_manifest = json.loads(
            (
                repository
                / ".agents/skills/promise-machine/runtime/MANIFEST.json"
            ).read_text(encoding="utf-8")
        )
        manifested = {row["path"]: row for row in portable_manifest["files"]}
        for relative in copied:
            with self.subTest(portable=relative):
                canonical = (PLUGIN_ROOT / relative).read_bytes()
                self.assertEqual(canonical, (portable_root / relative).read_bytes())
                path = f"plugins/hexaemeron/{relative}"
                self.assertEqual(path, manifested[path]["source"])
                self.assertEqual(
                    hashlib.sha256(canonical).hexdigest(),
                    manifested[path]["sha256"],
                )


if __name__ == "__main__":
    unittest.main()
