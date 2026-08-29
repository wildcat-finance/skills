"""Compile accepted-job evidence into one deterministic model proxy policy."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Any

from .canonical import (
    MAX_ACCEPTED_JOB_BYTES,
    MAX_JOBSPEC_BYTES,
    canonical_json,
    parse_json_bytes,
    read_bounded_file,
    sha256_bytes,
)
from .errors import PolicyError, refuse
from .profiles import FEATURE_NAMES, ProviderProfile, resolve_profile


ACCEPTED_JOB_SCHEMA = "accepted-job/v1"
ACCEPTANCE_SCHEMA = "jobspec-acceptance/v1"
JOBSPEC_SCHEMA = "jobspec/v1"
MODEL_PROXY_REQUEST_SCHEMA = "model-proxy-request/v1"
POLICY_SCHEMA = "model-proxy-policy/v1"
POLICY_COMPILER = "phylax-model-proxy-compiler/v1"

MAX_ABSOLUTE_LIFETIME_SECONDS = 3_600
MAX_RECEIPT_RETENTION_SECONDS = 86_400

_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_JOB_ID = re.compile(r"[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?\Z")
_SCHEMA_VERSION = re.compile(r"(?P<family>[a-z0-9-]+)/v[0-9]+\Z")

_ACCEPTED_FIELDS = frozenset(
    {"schema", "jobspec_b64", "jobspec_sha256", "verified"}
)
_VERIFIED_FIELDS = frozenset(
    {"schema", "job_id", "accepted_at", "expires_at"}
)
_JOBSPEC_FIELDS = frozenset({"schema", "job_id", "expires_at", "model_proxy"})
_MODEL_PROXY_FIELDS = frozenset(
    {
        "schema",
        "provider_profile",
        "model",
        "operation",
        "request_schema",
        "response_schema",
        "data_class",
        "features",
        "content_logging",
        "diagnostic_consent",
        "receipt_retention_seconds",
        "limits",
    }
)
LIMIT_FIELDS = (
    "max_requests",
    "max_request_bytes",
    "max_response_bytes",
    "max_input_tokens",
    "max_output_tokens",
    "max_total_request_bytes",
    "max_total_response_bytes",
    "max_total_input_tokens",
    "max_total_output_tokens",
    "max_concurrency",
    "max_json_depth",
    "max_json_members",
    "max_string_bytes",
    "max_receipt_bytes",
    "max_receipts",
    "total_wall_seconds",
)


@dataclass(frozen=True, slots=True)
class CompiledPolicy:
    """The checked policy document and the exact bytes bound by its digest."""

    document: dict[str, Any]
    policy_bytes: bytes
    policy_sha256: str
    jobspec_sha256: str
    profile: str


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        refuse("MP107", field)
    return value


def _exact_fields(value: dict[str, Any], expected: frozenset[str], field: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        if expected - actual:
            refuse("MP108", f"{field}.missing")
        refuse("MP108", f"{field}.extra")


def _schema(value: Any, supported: str, field: str) -> None:
    if value == supported:
        return
    if isinstance(value, str):
        match = _SCHEMA_VERSION.fullmatch(value)
        if match is not None and match.group("family") == supported.rsplit("/", 1)[0]:
            refuse("MP121", field)
    refuse("MP111", field)


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value
    ):
        refuse("MP118", field)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        refuse("MP118", field)
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        refuse("MP118", field)
    return parsed


def _positive_integer(value: Any, field: str, ceiling: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        refuse("MP109", field)
    if value > ceiling:
        refuse("MP119", field)
    return value


def _equal(value: Any, expected: str, field: str, code: str = "MP113") -> str:
    if not isinstance(value, str) or value != expected:
        refuse(code, field)
    return value


def _decode_jobspec(value: Any) -> bytes:
    if not isinstance(value, str):
        refuse("MP107", "accepted_job.jobspec_b64")
    if len(value) > ((MAX_JOBSPEC_BYTES + 2) // 3) * 4:
        refuse("MP101", "accepted_job.jobspec_b64")
    try:
        encoded = value.encode("ascii")
        decoded = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, ValueError):
        refuse("MP109", "accepted_job.jobspec_b64")
    if len(decoded) > MAX_JOBSPEC_BYTES:
        refuse("MP101", "jobspec.bytes")
    if base64.b64encode(decoded) != encoded:
        refuse("MP109", "accepted_job.jobspec_b64")
    return decoded


def _limits(value: Any, profile: ProviderProfile) -> dict[str, int]:
    document = _object(value, "model_proxy.limits")
    _exact_fields(document, frozenset(LIMIT_FIELDS), "model_proxy.limits")
    result = {
        name: _positive_integer(
            document[name], f"model_proxy.limits.{name}", profile.limit_ceilings[name]
        )
        for name in LIMIT_FIELDS
    }
    relationships = (
        ("max_total_request_bytes", "max_request_bytes"),
        ("max_total_response_bytes", "max_response_bytes"),
        ("max_total_input_tokens", "max_input_tokens"),
        ("max_total_output_tokens", "max_output_tokens"),
        ("max_requests", "max_concurrency"),
    )
    for aggregate, per_request in relationships:
        if result[aggregate] < result[per_request]:
            refuse("MP119", f"model_proxy.limits.{aggregate}")
    if result["max_receipts"] > result["max_requests"] + 2:
        refuse("MP119", "model_proxy.limits.max_receipts")
    return result


def _features(value: Any) -> dict[str, bool]:
    document = _object(value, "model_proxy.features")
    _exact_fields(document, frozenset(FEATURE_NAMES), "model_proxy.features")
    for name in FEATURE_NAMES:
        if document[name] is not False:
            refuse("MP114", f"model_proxy.features.{name}")
    return {name: False for name in FEATURE_NAMES}


def _project(accepted: dict[str, Any], jobspec: dict[str, Any]) -> dict[str, Any]:
    verified = _object(accepted["verified"], "accepted_job.verified")
    _exact_fields(verified, _VERIFIED_FIELDS, "accepted_job.verified")
    _schema(verified["schema"], ACCEPTANCE_SCHEMA, "accepted_job.verified.schema")

    _exact_fields(jobspec, _JOBSPEC_FIELDS, "jobspec")
    _schema(jobspec["schema"], JOBSPEC_SCHEMA, "jobspec.schema")
    job_id = jobspec["job_id"]
    if not isinstance(job_id, str) or _JOB_ID.fullmatch(job_id) is None:
        refuse("MP109", "jobspec.job_id")
    if verified["job_id"] != job_id:
        refuse("MP110", "accepted_job.verified.job_id")
    accepted_at = _timestamp(verified["accepted_at"], "accepted_job.verified.accepted_at")
    verified_expires = _timestamp(
        verified["expires_at"], "accepted_job.verified.expires_at"
    )
    jobspec_expires = _timestamp(jobspec["expires_at"], "jobspec.expires_at")
    if verified_expires != jobspec_expires:
        refuse("MP110", "accepted_job.verified.expires_at")
    lifetime = int((verified_expires - accepted_at).total_seconds())
    if lifetime <= 0 or lifetime > MAX_ABSOLUTE_LIFETIME_SECONDS:
        refuse("MP118", "accepted_job.verified.lifetime")

    request = _object(jobspec["model_proxy"], "jobspec.model_proxy")
    _exact_fields(request, _MODEL_PROXY_FIELDS, "jobspec.model_proxy")
    _schema(request["schema"], MODEL_PROXY_REQUEST_SCHEMA, "model_proxy.schema")
    profile = resolve_profile(request["provider_profile"])
    _equal(request["model"], profile.model, "model_proxy.model")
    _equal(request["operation"], profile.operation, "model_proxy.operation")
    _equal(
        request["request_schema"], profile.request_schema, "model_proxy.request_schema"
    )
    _equal(
        request["response_schema"],
        profile.response_schema,
        "model_proxy.response_schema",
    )
    if request["data_class"] not in profile.allowed_data_classes:
        refuse("MP117", "model_proxy.data_class")
    features = _features(request["features"])
    if request["content_logging"] is not False:
        refuse("MP115", "model_proxy.content_logging")
    if request["diagnostic_consent"] is not False:
        refuse("MP116", "model_proxy.diagnostic_consent")
    retention = _positive_integer(
        request["receipt_retention_seconds"],
        "model_proxy.receipt_retention_seconds",
        MAX_RECEIPT_RETENTION_SECONDS,
    )
    limits = _limits(request["limits"], profile)

    return {
        "schema": POLICY_SCHEMA,
        "compiler": POLICY_COMPILER,
        "job": {
            "id": job_id,
            "jobspec_sha256": accepted["jobspec_sha256"],
            "activated_at": verified["accepted_at"],
            "expires_at": verified["expires_at"],
            "absolute_lifetime_seconds": lifetime,
        },
        "provider": profile.policy_fields(),
        "disclosure": {
            "data_class": request["data_class"],
            "content_logging": False,
            "diagnostic_consent": False,
            "disabled_features": list(FEATURE_NAMES),
        },
        "limits": limits,
        "receipt": {
            "content": "none",
            "retention_seconds": retention,
        },
    }


def compile_policy(data: bytes) -> CompiledPolicy:
    """Compile exact accepted-job bytes into one canonical policy."""

    accepted = _object(
        parse_json_bytes(data, max_bytes=MAX_ACCEPTED_JOB_BYTES), "accepted_job"
    )
    _exact_fields(accepted, _ACCEPTED_FIELDS, "accepted_job")
    _schema(accepted["schema"], ACCEPTED_JOB_SCHEMA, "accepted_job.schema")
    digest = accepted["jobspec_sha256"]
    if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
        refuse("MP110", "accepted_job.jobspec_sha256")
    jobspec_bytes = _decode_jobspec(accepted["jobspec_b64"])
    if sha256_bytes(jobspec_bytes) != digest:
        refuse("MP110", "accepted_job.jobspec_sha256")
    jobspec = _object(
        parse_json_bytes(jobspec_bytes, max_bytes=MAX_JOBSPEC_BYTES), "jobspec"
    )
    document = _project(accepted, jobspec)
    policy_bytes = canonical_json(document)
    profile = document["provider"]["id"]
    return CompiledPolicy(
        document=document,
        policy_bytes=policy_bytes,
        policy_sha256=sha256_bytes(policy_bytes),
        jobspec_sha256=digest,
        profile=profile,
    )


def compile_policy_file(path: str) -> CompiledPolicy:
    """Read and compile one bounded accepted-job evidence file."""

    return compile_policy(read_bounded_file(path, MAX_ACCEPTED_JOB_BYTES))


def verify_golden(result: CompiledPolicy, path: str) -> None:
    """Require exact policy bytes and their sibling digest vector."""

    raw = read_bounded_file(path, MAX_ACCEPTED_JOB_BYTES)
    if raw != result.policy_bytes + b"\n":
        refuse("MP120", "policy_golden.bytes")
    digest_path = str(path).removesuffix(".json") + ".sha256"
    digest_raw = read_bounded_file(digest_path, 128)
    if digest_raw != (result.policy_sha256 + "\n").encode("ascii"):
        refuse("MP120", "policy_golden.sha256")
