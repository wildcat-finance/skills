"""Cause-level guards for the version-1 model proxy policy compiler."""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
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


if __name__ == "__main__":
    unittest.main()
