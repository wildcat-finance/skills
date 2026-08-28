#!/usr/bin/env python3
"""Validate the closed Brevitas held-corpus contract without network access."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SCHEMA = "brevitas-held-corpus-v1"
REQUEST_FORMAT = "prompt-source-v1"
REQUEST_MIDDLE = b"\n--- BEGIN SOURCE EXCERPT ---\n"
REQUEST_END = b"--- END SOURCE EXCERPT ---\n"
MANIFEST_LIMIT = 256 * 1024
FIXTURE_LIMIT = 32 * 1024
CASE_LIMIT = 100
SPAN_LIMIT = 32

FAMILIES = frozenset(
    {"x-ray", "solidity-auditor", "gas", "invariant", "diff-review"}
)
MODEL_IDENTITIES = frozenset(
    {"openai/gpt-5.6-sol", "openai/gpt-5.6-terra"}
)
OUTCOMES = frozenset(
    {
        "conforming",
        "expected-diagnostics",
        "compression-target",
        "evidence-retention-target",
        "unclassified",
    }
)
SPAN_KINDS = frozenset(
    {
        "file-reference",
        "numeric-claim",
        "causal-mechanism",
        "counterexample-step",
        "reproduction-step",
        "invariant",
        "establishment-limit",
    }
)

ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
CODE_RE = re.compile(r"^B[0-9]{3}$")
FORBIDDEN_METADATA_KEYS = frozenset(
    {
        "api_key",
        "access_token",
        "auth_token",
        "bearer_token",
        "chain_of_thought",
        "client_log",
        "credential",
        "credentials",
        "hidden_reasoning",
        "private_prompt",
        "raw_request",
        "reasoning",
        "session",
        "session_id",
    }
)
FORBIDDEN_BYTES = (
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    re.compile(rb"(?i)Bearer[ \t]+[A-Za-z0-9._~+/-]{16,}"),
    re.compile(
        rb"(?i)[\"']?(?:api[_-]?key|access[_-]?token|auth[_-]?token|"
        rb"session[_-]?id|hidden[_-]?reasoning|chain[_-]?of[_-]?thought)"
        rb"[\"']?[ \t]*[:=][ \t]*[\"']?[^\s\"']{8,}"
    ),
)


class CorpusError(ValueError):
    """A bounded, non-content-bearing corpus validation failure."""

    def __init__(
        self,
        code: str,
        detail: str,
        *,
        case_id: str | None = None,
        expected_digest: str | None = None,
        actual_digest: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.case_id = case_id
        self.expected_digest = expected_digest
        self.actual_digest = actual_digest


class _DuplicateField(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedCase:
    case_id: str
    family: str
    model_identity: str
    expectation: str
    expected_codes: tuple[str, ...]
    prompt_digest: str
    source_digest: str
    output_digest: str
    protected_span_count: int


@dataclass(frozen=True)
class CorpusResult:
    cases: tuple[ValidatedCase, ...]
    family_models: dict[str, tuple[str, ...]]
    unclassified: int
    stale: int


def _duplicate_aware_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for key, value in pairs:
        if key in found:
            raise _DuplicateField
        found[key] = value
    return found


def _safe_case_id(value: Any, index: int) -> str:
    if isinstance(value, str) and ID_RE.fullmatch(value):
        return value
    return f"case-{index}"


def _expect_object(value: Any, *, code: str, detail: str, case_id: str | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CorpusError(code, detail, case_id=case_id)
    return value


def _expect_fields(
    value: dict[str, Any],
    fields: set[str],
    *,
    code: str,
    detail: str,
    case_id: str | None = None,
) -> None:
    if set(value) != fields:
        raise CorpusError(code, detail, case_id=case_id)


def _reject_forbidden_metadata(value: Any, *, case_id: str | None = None) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower().replace("-", "_") in FORBIDDEN_METADATA_KEYS:
                raise CorpusError("HC013", "forbidden-capture-metadata", case_id=case_id)
            _reject_forbidden_metadata(child, case_id=case_id)
    elif isinstance(value, list):
        for child in value:
            _reject_forbidden_metadata(child, case_id=case_id)


def _checked_relative_path(value: Any, *, case_id: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise CorpusError("HC020", "unsafe-relative-path", case_id=case_id)
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise CorpusError("HC020", "unsafe-relative-path", case_id=case_id)
    return path


def _read_regular_utf8(
    root: Path,
    relative: Any,
    *,
    byte_limit: int,
    case_id: str,
) -> tuple[bytes, str]:
    path = _checked_relative_path(relative, case_id=case_id)
    try:
        root_lstat = root.lstat()
        root_resolved = root.resolve(strict=True)
    except OSError:
        raise CorpusError("HC021", "corpus-root-unavailable", case_id=case_id) from None
    if stat.S_ISLNK(root_lstat.st_mode) or not stat.S_ISDIR(root_lstat.st_mode):
        raise CorpusError("HC021", "corpus-root-not-direct-directory", case_id=case_id)

    candidate = root.joinpath(*path.parts)
    current = root
    try:
        for index, part in enumerate(path.parts):
            current = current / part
            found = current.lstat()
            if stat.S_ISLNK(found.st_mode):
                raise CorpusError("HC021", "linked-fixture-path", case_id=case_id)
            if index < len(path.parts) - 1 and not stat.S_ISDIR(found.st_mode):
                raise CorpusError("HC021", "non-directory-fixture-parent", case_id=case_id)
        before = candidate.lstat()
        resolved = candidate.resolve(strict=True)
    except CorpusError:
        raise
    except OSError:
        raise CorpusError("HC021", "fixture-unavailable", case_id=case_id) from None

    if not resolved.is_relative_to(root_resolved):
        raise CorpusError("HC020", "fixture-path-escape", case_id=case_id)
    if not stat.S_ISREG(before.st_mode):
        raise CorpusError("HC021", "fixture-not-regular", case_id=case_id)
    if before.st_size > byte_limit:
        raise CorpusError("HC022", "fixture-oversized", case_id=case_id)

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(candidate, flags)
    except OSError:
        raise CorpusError("HC021", "fixture-open-refused", case_id=case_id) from None
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise CorpusError("HC021", "fixture-not-regular", case_id=case_id)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise CorpusError("HC021", "fixture-identity-changed", case_id=case_id)
        data = os.read(descriptor, byte_limit + 1)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)

    if len(data) > byte_limit or after.st_size > byte_limit:
        raise CorpusError("HC022", "fixture-oversized", case_id=case_id)
    if len(data) != after.st_size:
        raise CorpusError("HC021", "fixture-partial-read", case_id=case_id)
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
        opened.st_mtime_ns,
    ):
        raise CorpusError("HC021", "fixture-changed-during-read", case_id=case_id)
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise CorpusError("HC023", "fixture-invalid-utf8", case_id=case_id) from None
    if "\x00" in text:
        raise CorpusError("HC023", "fixture-contains-nul", case_id=case_id)
    for pattern in FORBIDDEN_BYTES:
        if pattern.search(data):
            raise CorpusError("HC013", "forbidden-capture-material", case_id=case_id)
    return data, text


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _checked_digest(value: Any, *, case_id: str) -> str:
    if not isinstance(value, str) or not DIGEST_RE.fullmatch(value):
        raise CorpusError("HC010", "invalid-digest-field", case_id=case_id)
    return value


def _verify_digest(data: bytes, expected: Any, *, case_id: str) -> str:
    expected_digest = _checked_digest(expected, case_id=case_id)
    actual_digest = _digest(data)
    if actual_digest != expected_digest:
        raise CorpusError(
            "HC024",
            "fixture-digest-mismatch",
            case_id=case_id,
            expected_digest=expected_digest,
            actual_digest=actual_digest,
        )
    return actual_digest


def _validate_capture(value: Any, *, case_id: str) -> tuple[str, str]:
    capture = _expect_object(value, code="HC010", detail="capture-not-object", case_id=case_id)
    _expect_fields(
        capture,
        {"provider", "returned_model_id", "client", "client_version", "mode"},
        code="HC010",
        detail="capture-fields-invalid",
        case_id=case_id,
    )
    provider = capture["provider"]
    model_identity = capture["returned_model_id"]
    if (
        not isinstance(provider, str)
        or not isinstance(model_identity, str)
        or provider != "openai"
        or model_identity not in MODEL_IDENTITIES
    ):
        raise CorpusError("HC012", "capture-identity-invalid", case_id=case_id)
    if not model_identity.startswith(f"{provider}/"):
        raise CorpusError("HC012", "capture-identity-invalid", case_id=case_id)
    if (
        capture["client"] != "codex-cli"
        or capture["client_version"] != "0.150.1"
        or capture["mode"] != "one-time-ephemeral-read-only-output-only"
    ):
        raise CorpusError("HC012", "capture-client-invalid", case_id=case_id)
    return provider, model_identity


def _validate_provenance(value: Any, *, case_id: str) -> None:
    provenance = _expect_object(
        value, code="HC010", detail="provenance-not-object", case_id=case_id
    )
    _expect_fields(
        provenance,
        {"origins"},
        code="HC010",
        detail="provenance-fields-invalid",
        case_id=case_id,
    )
    origins = provenance["origins"]
    if not isinstance(origins, list) or not 1 <= len(origins) <= 4:
        raise CorpusError("HC014", "source-origin-count-invalid", case_id=case_id)
    for origin in origins:
        origin_object = _expect_object(
            origin, code="HC014", detail="source-origin-invalid", case_id=case_id
        )
        _expect_fields(
            origin_object,
            {"repository", "commit", "path", "range"},
            code="HC014",
            detail="source-origin-fields-invalid",
            case_id=case_id,
        )
        if origin_object["repository"] != "https://github.com/wildcat-finance/skills":
            raise CorpusError("HC014", "source-repository-invalid", case_id=case_id)
        if not isinstance(origin_object["commit"], str) or not COMMIT_RE.fullmatch(
            origin_object["commit"]
        ):
            raise CorpusError("HC014", "source-commit-invalid", case_id=case_id)
        _checked_relative_path(origin_object["path"], case_id=case_id)
        source_range = origin_object["range"]
        if not isinstance(source_range, str) or not 1 <= len(source_range) <= 120:
            raise CorpusError("HC014", "source-range-invalid", case_id=case_id)


def _validate_review(value: Any, *, case_id: str) -> None:
    review = _expect_object(value, code="HC010", detail="review-not-object", case_id=case_id)
    _expect_fields(
        review,
        {
            "licence_spdx",
            "licence_decision",
            "sensitivity_decision",
            "secret_review",
            "capture_review",
            "redistributable",
        },
        code="HC010",
        detail="review-fields-invalid",
        case_id=case_id,
    )
    if (
        review["licence_spdx"] != "Apache-2.0"
        or review["licence_decision"] != "redistribution-permitted"
        or review["sensitivity_decision"] != "public-no-personal-data"
        or review["secret_review"] != "prompt-source-output-reviewed-clean"
        or review["capture_review"] != "final-response-only-no-hidden-reasoning"
        or review["redistributable"] is not True
    ):
        raise CorpusError("HC014", "licence-or-sensitivity-review-invalid", case_id=case_id)


def _validate_classification(value: Any, *, case_id: str) -> tuple[str, tuple[str, ...]]:
    classification = _expect_object(
        value, code="HC010", detail="classification-not-object", case_id=case_id
    )
    _expect_fields(
        classification,
        {"reviewer", "timing", "outcome", "lint_mode", "expected_codes", "basis"},
        code="HC010",
        detail="classification-fields-invalid",
        case_id=case_id,
    )
    if classification["reviewer"] != "human-review" or classification["timing"] != "before-current-linter":
        raise CorpusError("HC015", "classification-provenance-invalid", case_id=case_id)
    outcome = classification["outcome"]
    if (
        not isinstance(outcome, str)
        or outcome not in OUTCOMES
        or classification["lint_mode"] != "report"
    ):
        raise CorpusError("HC015", "classification-outcome-invalid", case_id=case_id)
    expected_codes = classification["expected_codes"]
    if not isinstance(expected_codes, list) or any(
        not isinstance(code, str) or not CODE_RE.fullmatch(code) for code in expected_codes
    ):
        raise CorpusError("HC016", "classification-codes-invalid", case_id=case_id)
    if expected_codes != sorted(expected_codes):
        raise CorpusError("HC016", "classification-codes-unsorted", case_id=case_id)
    if outcome == "conforming" and expected_codes:
        raise CorpusError("HC016", "conforming-case-has-diagnostics", case_id=case_id)
    if outcome == "expected-diagnostics" and not expected_codes:
        raise CorpusError("HC016", "diagnostic-case-has-no-code", case_id=case_id)
    basis = classification["basis"]
    if not isinstance(basis, str) or not 1 <= len(basis.encode("utf-8")) <= 512:
        raise CorpusError("HC015", "classification-basis-invalid", case_id=case_id)
    return outcome, tuple(expected_codes)


def _validate_spans(value: Any, output: str, *, case_id: str) -> int:
    if not isinstance(value, list) or not 1 <= len(value) <= SPAN_LIMIT:
        raise CorpusError("HC030", "protected-span-count-invalid", case_id=case_id)
    spans: list[tuple[int, str]] = []
    texts: set[str] = set()
    for span_value in value:
        span = _expect_object(
            span_value, code="HC030", detail="protected-span-not-object", case_id=case_id
        )
        _expect_fields(
            span,
            {"order", "kind", "text", "sha256"},
            code="HC030",
            detail="protected-span-fields-invalid",
            case_id=case_id,
        )
        order = span["order"]
        text = span["text"]
        if isinstance(order, bool) or not isinstance(order, int):
            raise CorpusError("HC030", "protected-span-order-invalid", case_id=case_id)
        if not isinstance(span["kind"], str) or span["kind"] not in SPAN_KINDS:
            raise CorpusError("HC030", "protected-span-kind-invalid", case_id=case_id)
        if not isinstance(text, str) or not 1 <= len(text.encode("utf-8")) <= 2048:
            raise CorpusError("HC030", "protected-span-text-invalid", case_id=case_id)
        if text in texts:
            raise CorpusError("HC032", "protected-span-declared-twice", case_id=case_id)
        texts.add(text)
        expected_digest = _checked_digest(span["sha256"], case_id=case_id)
        if _digest(text.encode("utf-8")) != expected_digest:
            raise CorpusError("HC030", "protected-span-digest-mismatch", case_id=case_id)
        count = output.count(text)
        if count == 0:
            raise CorpusError("HC031", "protected-span-missing", case_id=case_id)
        if count != 1:
            raise CorpusError("HC032", "protected-span-duplicated", case_id=case_id)
        spans.append((order, text))

    expected_orders = list(range(1, len(spans) + 1))
    if sorted(order for order, _ in spans) != expected_orders:
        raise CorpusError("HC030", "protected-span-orders-invalid", case_id=case_id)
    positions = [output.index(text) for _, text in sorted(spans)]
    if positions != sorted(positions):
        raise CorpusError("HC033", "protected-spans-reordered", case_id=case_id)
    return len(spans)


def _validate_files(
    value: Any,
    root: Path,
    *,
    case_id: str,
) -> tuple[str, str, str, str]:
    files = _expect_object(value, code="HC010", detail="files-not-object", case_id=case_id)
    _expect_fields(
        files,
        {
            "prompt",
            "prompt_sha256",
            "source",
            "source_sha256",
            "output",
            "output_sha256",
            "request_sha256",
        },
        code="HC010",
        detail="file-fields-invalid",
        case_id=case_id,
    )
    prompt, _ = _read_regular_utf8(root, files["prompt"], byte_limit=FIXTURE_LIMIT, case_id=case_id)
    source, _ = _read_regular_utf8(root, files["source"], byte_limit=FIXTURE_LIMIT, case_id=case_id)
    output, output_text = _read_regular_utf8(
        root, files["output"], byte_limit=FIXTURE_LIMIT, case_id=case_id
    )
    prompt_digest = _verify_digest(prompt, files["prompt_sha256"], case_id=case_id)
    source_digest = _verify_digest(source, files["source_sha256"], case_id=case_id)
    output_digest = _verify_digest(output, files["output_sha256"], case_id=case_id)
    request_digest = _digest(prompt + REQUEST_MIDDLE + source + REQUEST_END)
    expected_request_digest = _checked_digest(files["request_sha256"], case_id=case_id)
    if request_digest != expected_request_digest:
        raise CorpusError(
            "HC025",
            "capture-request-digest-mismatch",
            case_id=case_id,
            expected_digest=expected_request_digest,
            actual_digest=request_digest,
        )
    return prompt_digest, source_digest, output_digest, output_text


def validate_corpus(root: Path) -> CorpusResult:
    """Validate one corpus root and return bounded reporting fields."""

    manifest_bytes, manifest_text = _read_regular_utf8(
        root,
        "corpus.json",
        byte_limit=MANIFEST_LIMIT,
        case_id="manifest",
    )
    del manifest_bytes
    try:
        document = json.loads(manifest_text, object_pairs_hook=_duplicate_aware_object)
    except _DuplicateField:
        raise CorpusError("HC002", "duplicate-json-field") from None
    except (json.JSONDecodeError, RecursionError, UnicodeError, ValueError):
        raise CorpusError("HC002", "invalid-json-manifest") from None

    document = _expect_object(document, code="HC003", detail="manifest-not-object")
    _reject_forbidden_metadata(document)
    _expect_fields(
        document,
        {"schema", "request_format", "cases"},
        code="HC003",
        detail="manifest-fields-invalid",
    )
    if document["schema"] != SCHEMA or document["request_format"] != REQUEST_FORMAT:
        raise CorpusError("HC003", "manifest-version-invalid")
    cases = document["cases"]
    if not isinstance(cases, list) or not cases or len(cases) > CASE_LIMIT:
        raise CorpusError("HC003", "manifest-case-count-invalid")

    validated: list[ValidatedCase] = []
    ids: set[str] = set()
    output_paths: set[str] = set()
    coverage_pairs: set[tuple[str, str]] = set()
    family_models: dict[str, set[str]] = {family: set() for family in FAMILIES}
    unclassified = 0

    for index, case_value in enumerate(cases, start=1):
        case_object = _expect_object(
            case_value, code="HC010", detail="case-not-object", case_id=f"case-{index}"
        )
        case_id = _safe_case_id(case_object.get("id"), index)
        _reject_forbidden_metadata(case_object, case_id=case_id)
        _expect_fields(
            case_object,
            {
                "id",
                "family",
                "capture",
                "files",
                "provenance",
                "review",
                "classification",
                "protected_spans",
            },
            code="HC010",
            detail="case-fields-invalid",
            case_id=case_id,
        )
        if case_object["id"] != case_id:
            raise CorpusError("HC010", "case-id-invalid", case_id=case_id)
        if case_id in ids:
            raise CorpusError("HC011", "duplicate-case-id", case_id=case_id)
        ids.add(case_id)

        family = case_object["family"]
        if not isinstance(family, str) or family not in FAMILIES:
            raise CorpusError("HC044", "engineering-family-invalid", case_id=case_id)
        _, model_identity = _validate_capture(case_object["capture"], case_id=case_id)
        pair = (family, model_identity)
        if pair in coverage_pairs:
            raise CorpusError("HC043", "duplicate-family-model-case", case_id=case_id)
        coverage_pairs.add(pair)

        _validate_provenance(case_object["provenance"], case_id=case_id)
        _validate_review(case_object["review"], case_id=case_id)
        outcome, expected_codes = _validate_classification(
            case_object["classification"], case_id=case_id
        )
        if outcome == "unclassified":
            unclassified += 1

        files = _expect_object(
            case_object["files"], code="HC010", detail="files-not-object", case_id=case_id
        )
        output_path = files.get("output")
        if isinstance(output_path, str) and output_path in output_paths:
            raise CorpusError("HC043", "duplicate-output-file", case_id=case_id)
        if isinstance(output_path, str):
            output_paths.add(output_path)
        prompt_digest, source_digest, output_digest, output_text = _validate_files(
            files, root, case_id=case_id
        )
        protected_span_count = _validate_spans(
            case_object["protected_spans"], output_text, case_id=case_id
        )
        family_models[family].add(model_identity)
        validated.append(
            ValidatedCase(
                case_id=case_id,
                family=family,
                model_identity=model_identity,
                expectation=outcome,
                expected_codes=expected_codes,
                prompt_digest=prompt_digest,
                source_digest=source_digest,
                output_digest=output_digest,
                protected_span_count=protected_span_count,
            )
        )

    missing_families = sorted(family for family, models in family_models.items() if not models)
    if missing_families:
        raise CorpusError("HC040", "required-family-missing")
    incomplete = sorted(
        family for family, models in family_models.items() if models != MODEL_IDENTITIES
    )
    if incomplete:
        raise CorpusError("HC041", "family-model-coverage-incomplete")
    if len(validated) < 10:
        raise CorpusError("HC042", "qualifying-case-count-below-ten")
    if unclassified:
        raise CorpusError("HC015", "unclassified-cases-present")

    return CorpusResult(
        cases=tuple(sorted(validated, key=lambda item: item.case_id)),
        family_models={
            family: tuple(sorted(models)) for family, models in sorted(family_models.items())
        },
        unclassified=unclassified,
        stale=0,
    )


def result_lines(result: CorpusResult) -> Iterable[str]:
    for case in result.cases:
        codes = ",".join(case.expected_codes) if case.expected_codes else "none"
        yield (
            f"CASE id={case.case_id} family={case.family} model={case.model_identity} "
            f"expectation={case.expectation} expected={codes} actual=not-run "
            f"prompt={case.prompt_digest[:12]} source={case.source_digest[:12]} "
            f"output={case.output_digest[:12]} spans={case.protected_span_count}"
        )
    for family, models in result.family_models.items():
        yield f"COVERAGE family={family} models={','.join(models)} cases={len(models)}"
    yield (
        f"CORPUS schema={SCHEMA} families={len(result.family_models)} models={len(MODEL_IDENTITIES)} "
        f"cases={len(result.cases)} qualifying={len(result.cases)} "
        f"unclassified={result.unclassified} stale={result.stale}"
    )


def failure_line(error: CorpusError) -> str:
    fields = ["FAIL", f"code={error.code}", f"detail={error.detail}"]
    if error.case_id:
        fields.append(f"case={error.case_id}")
    if error.expected_digest:
        fields.append(f"expected={error.expected_digest[:12]}")
    if error.actual_digest:
        fields.append(f"actual={error.actual_digest[:12]}")
    return " ".join(fields)
