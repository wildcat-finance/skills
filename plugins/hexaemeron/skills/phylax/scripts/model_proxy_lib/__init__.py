"""Public library surface for the Phylax model proxy policy compiler."""

from .canonical import (
    MAX_ACCEPTED_JOB_BYTES,
    MAX_JOBSPEC_BYTES,
    canonical_json,
    parse_json_bytes,
    read_bounded_file,
    sha256_bytes,
)
from .errors import DIAGNOSTIC_SCHEMA, PolicyError
from .policy import (
    ACCEPTED_JOB_SCHEMA,
    JOBSPEC_SCHEMA,
    LIMIT_FIELDS,
    MODEL_PROXY_REQUEST_SCHEMA,
    POLICY_COMPILER,
    POLICY_SCHEMA,
    CompiledPolicy,
    compile_policy,
    compile_policy_file,
    verify_golden,
)
from .profiles import FEATURE_NAMES, LOOPBACK_TEXT_V1, ProviderProfile, resolve_profile
from .lifecycle import (
    LIFECYCLE_MANIFEST_SCHEMA,
    LifecycleController,
    LifecycleManifestResult,
    ModelProxyRuntime,
    Reservation,
    TerminalSnapshot,
    check_lifecycle_manifest,
)
from .operator import render_operator_text
from .receipts import MAX_RECEIPT_BYTES, RECEIPT_SCHEMA, ReceiptSink

__all__ = (
    "ACCEPTED_JOB_SCHEMA",
    "CompiledPolicy",
    "DIAGNOSTIC_SCHEMA",
    "FEATURE_NAMES",
    "JOBSPEC_SCHEMA",
    "LIMIT_FIELDS",
    "LIFECYCLE_MANIFEST_SCHEMA",
    "LifecycleController",
    "LifecycleManifestResult",
    "LOOPBACK_TEXT_V1",
    "MAX_ACCEPTED_JOB_BYTES",
    "MAX_JOBSPEC_BYTES",
    "MODEL_PROXY_REQUEST_SCHEMA",
    "MAX_RECEIPT_BYTES",
    "ModelProxyRuntime",
    "POLICY_COMPILER",
    "POLICY_SCHEMA",
    "PolicyError",
    "ProviderProfile",
    "RECEIPT_SCHEMA",
    "ReceiptSink",
    "Reservation",
    "TerminalSnapshot",
    "canonical_json",
    "check_lifecycle_manifest",
    "compile_policy",
    "compile_policy_file",
    "parse_json_bytes",
    "read_bounded_file",
    "resolve_profile",
    "render_operator_text",
    "sha256_bytes",
    "verify_golden",
)
