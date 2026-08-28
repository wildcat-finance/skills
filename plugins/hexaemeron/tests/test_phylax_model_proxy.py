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
import unittest
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
from model_proxy_lib.framing import (  # noqa: E402
    FRAME_EVENT_SCHEMA,
    FRAMING_MANIFEST_SCHEMA,
    REQUEST_SCHEMA,
    RESPONSE_SCHEMA,
    TEXT_OPERATION,
    FramingCore,
    check_framing_manifest,
)
from model_proxy_lib.provider import (  # noqa: E402
    PROVIDER_EVENT_SCHEMA,
    PROVIDER_MANIFEST_SCHEMA,
    ProviderSession,
    check_provider_manifest,
)
from model_proxy_lib.transport import HTTPSConnector, HTTPSRequest  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
