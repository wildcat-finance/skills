#!/usr/bin/env python3
"""Capture a bounded, redacted run observation before durable emission.

This module deliberately accepts a small candidate shape.  It never serializes
the candidate itself: the only durable object is an ``accepted`` result made
from directly allowed descriptors.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Mapping


CONTRACT_ID = "promise-machine-run-observation-capture/v1"
MAX_INPUT_BYTES = 32_768
MAX_STRING_BYTES = 1_024
MAX_COLLECTION = 32
MAX_REDACTIONS = 16
MAX_PATH_BYTES = 4_096
MAX_FINGERPRINT_BYTES = 512
MAX_COUNTER = 1_000_000
ALLOWED_EVENT_FIELDS = {
    "run_id", "event_id", "event_type", "time", "status", "name",
    "format", "selector", "reference", "count", "size", "length",
}
REDACTION_FIELD_CLASSES = {
    "content", "credential", "environment", "execution", "path", "trace", "unknown",
}
REDACTION_REASON_CODES = {
    "forbidden_content", "ineligible_fingerprint", "invalid_path", "over_limit",
    "unknown_field", "unsafe_shape",
}
REDACTION_METHODS = {"omitted", "fingerprinted", "path_dehosted"}
FORBIDDEN_NAMES = {
    "prompt", "completion", "message", "messages", "instruction", "instructions",
    "directive", "directives", "reasoning", "analysis", "tool_output", "command",
    "arguments", "argv", "source", "trace", "headers", "cookies", "environment",
    "env", "credential", "credentials", "token", "api_key", "password", "payload",
    "request", "response", "exception", "url", "body", "signed_payload",
}
IDENTITY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/ -]{0,255}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class CaptureResult:
    outcome: str
    code: str
    event: dict[str, Any] | None = None
    redactions: tuple[dict[str, str], ...] = ()
    _issued_capture: object | None = field(default=None, init=False, repr=False, compare=False)

    def public(self) -> dict[str, Any]:
        result: dict[str, Any] = {"schema_id": CONTRACT_ID, "outcome": self.outcome, "code": self.code}
        if self.event is not None:
            result["event"] = self.event
        if self.redactions:
            result["redactions"] = list(self.redactions)
        return result


def _redaction(field_class: str, reason_code: str, method: str = "omitted") -> dict[str, str]:
    return {"field_class": field_class, "reason_code": reason_code, "method": method}


def _gap(field_class: str, reason_code: str) -> CaptureResult:
    return CaptureResult("gap", reason_code, redactions=(_redaction(field_class, reason_code),))


def _refused(code: str) -> CaptureResult:
    return CaptureResult("refused", code)


def _capture_issuer() -> tuple[Any, Any]:
    """Keep issuance out of the public result constructor."""
    issued = object()

    def issue(event: dict[str, Any], redactions: tuple[dict[str, str], ...]) -> CaptureResult:
        result = CaptureResult("accepted", "accepted", event=event, redactions=redactions)
        object.__setattr__(result, "_issued_capture", issued)
        return result

    def issued_by_runtime(result: CaptureResult) -> bool:
        return result._issued_capture is issued

    return issue, issued_by_runtime


_issue_accepted, _is_runtime_issued = _capture_issuer()


def _bounded_json(value: Any) -> bool:
    try:
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        return False
    return len(encoded) <= MAX_INPUT_BYTES


def _safe_scalar(value: Any) -> bool:
    if isinstance(value, bool) or isinstance(value, int):
        return True
    if not isinstance(value, str):
        return False
    return bool(value) and len(value.encode("utf-8")) <= MAX_STRING_BYTES and bool(SAFE_TEXT_RE.fullmatch(value))


def _confined_path(value: Any, repository_root: Path) -> str | None:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > MAX_PATH_BYTES:
        return None
    if unicodedata.normalize("NFC", value) != value or "\\" in value or "\x00" in value:
        return None
    supplied = Path(value)
    try:
        root = repository_root.resolve(strict=True)
        target = (root / supplied).resolve(strict=True) if not supplied.is_absolute() else supplied.resolve(strict=True)
        relative = target.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return None
    if not relative.parts or any(part in {".", ".."} for part in relative.parts):
        return None
    return relative.as_posix()


def _fingerprint(value: Mapping[str, Any]) -> tuple[dict[str, str] | None, str | None]:
    if set(value) != {"scope", "value_b64", "entropy_bits"}:
        return None, "unsafe_shape"
    scope, encoded, entropy = value["scope"], value["value_b64"], value["entropy_bits"]
    if not isinstance(scope, str) or not SAFE_TEXT_RE.fullmatch(scope) or not isinstance(entropy, int) or entropy < 128:
        return None, "ineligible_fingerprint"
    if not isinstance(encoded, str) or len(encoded) > (MAX_FINGERPRINT_BYTES * 2):
        return None, "unsafe_shape"
    try:
        source = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        return None, "unsafe_shape"
    if not source or len(source) > MAX_FINGERPRINT_BYTES:
        return None, "over_limit"
    observed_entropy_bits = -sum(
        (count / len(source)) * math.log2(count / len(source))
        for count in (source.count(byte) for byte in set(source))
    ) * len(source)
    if observed_entropy_bits < 128 or entropy > observed_entropy_bits:
        return None, "ineligible_fingerprint"
    digest = hashlib.sha256(b"promise-machine/capture/v1\x00" + scope.encode("utf-8") + b"\x00" + source).hexdigest()
    return {"algorithm": "sha256", "scope": scope, "fingerprint": digest}, None


def capture_candidate(candidate: Any, repository_root: str | os.PathLike[str]) -> CaptureResult:
    """Return an accepted result, visible gap, or refusal without retaining candidate bytes."""
    if not isinstance(candidate, Mapping) or not _bounded_json(candidate):
        return _refused("unsafe_shape")
    allowed = {"event", "repository_path", "redactions", "fingerprint"}
    unknown = set(candidate) - allowed
    if unknown:
        if any(str(key).lower() in FORBIDDEN_NAMES for key in unknown):
            return _gap("content", "forbidden_content")
        return _gap("unknown", "unknown_field")
    event = candidate.get("event")
    if not isinstance(event, Mapping) or not event or len(event) > MAX_COLLECTION:
        return _refused("unsafe_shape")
    if set(event) - ALLOWED_EVENT_FIELDS:
        return _gap("unknown", "unknown_field")
    stored_event: dict[str, Any] = {}
    for key, value in event.items():
        if key in {"run_id", "event_id"}:
            if not isinstance(value, str) or not IDENTITY_RE.fullmatch(value):
                return _refused("unsafe_shape")
        elif key in {"count", "size", "length"}:
            if type(value) is not int or not 0 <= value <= MAX_COUNTER:
                return _refused("unsafe_shape")
        elif not _safe_scalar(value):
            return _refused("unsafe_shape")
        stored_event[str(key)] = value
    if "repository_path" in candidate:
        path = _confined_path(candidate["repository_path"], Path(repository_root))
        if path is None:
            return _gap("path", "invalid_path")
        stored_event["repository_path"] = path
    redactions = candidate.get("redactions", [])
    if not isinstance(redactions, list) or len(redactions) > MAX_REDACTIONS:
        return _refused("unsafe_shape")
    stored_redactions: list[dict[str, str]] = []
    for item in redactions:
        if not isinstance(item, Mapping) or set(item) != {"field_class", "reason_code", "method"}:
            return _refused("unsafe_shape")
        field_class = item["field_class"]
        reason = item["reason_code"]
        method = item["method"]
        if field_class not in REDACTION_FIELD_CLASSES or reason not in REDACTION_REASON_CODES or method not in REDACTION_METHODS:
            return _refused("unsafe_shape")
        stored_redactions.append(_redaction(field_class, reason, method))
    if "fingerprint" in candidate:
        if not isinstance(candidate["fingerprint"], Mapping):
            return _refused("unsafe_shape")
        fingerprint, error = _fingerprint(candidate["fingerprint"])
        if error:
            return _gap("credential", error)
        assert fingerprint is not None
        stored_event["correlation"] = fingerprint
        stored_redactions.append(_redaction("content", "forbidden_content", "fingerprinted"))
    event_out: dict[str, Any] = {"schema_id": CONTRACT_ID, "descriptors": stored_event}
    if stored_redactions:
        event_out["redactions"] = stored_redactions
    return _issue_accepted(event_out, tuple(stored_redactions))


def _validated_accepted_event(result: CaptureResult, repository_root: Path) -> dict[str, Any]:
    """Rebuild a durable event from the narrow result contract, not mutable input."""
    if not _is_runtime_issued(result) or result.outcome != "accepted" or result.code != "accepted":
        raise ValueError("only a runtime-issued accepted capture result may be emitted")
    if not isinstance(result.event, Mapping) or set(result.event) - {"schema_id", "descriptors", "redactions"}:
        raise ValueError("accepted capture event is unsafe")
    if result.event.get("schema_id") != CONTRACT_ID or not isinstance(result.event.get("descriptors"), Mapping):
        raise ValueError("accepted capture event is unsafe")
    descriptors = result.event["descriptors"]
    if not descriptors or len(descriptors) > MAX_COLLECTION + 2 or set(descriptors) - (ALLOWED_EVENT_FIELDS | {"repository_path", "correlation"}):
        raise ValueError("accepted capture event is unsafe")
    rebuilt: dict[str, Any] = {}
    for key, value in descriptors.items():
        if key in {"run_id", "event_id"}:
            valid = isinstance(value, str) and bool(IDENTITY_RE.fullmatch(value))
        elif key in {"count", "size", "length"}:
            valid = type(value) is int and 0 <= value <= MAX_COUNTER
        elif key == "repository_path":
            confined = _confined_path(value, repository_root)
            valid = confined is not None
            value = confined
        elif key == "correlation":
            valid = (
                isinstance(value, Mapping)
                and set(value) == {"algorithm", "scope", "fingerprint"}
                and value.get("algorithm") == "sha256"
                and isinstance(value.get("scope"), str)
                and bool(SAFE_TEXT_RE.fullmatch(value["scope"]))
                and isinstance(value.get("fingerprint"), str)
                and bool(SHA256_RE.fullmatch(value["fingerprint"]))
            )
            value = dict(value) if valid else value
        else:
            valid = _safe_scalar(value)
        if not valid:
            raise ValueError("accepted capture event is unsafe")
        rebuilt[key] = value
    redactions = result.redactions
    if not isinstance(redactions, tuple) or len(redactions) > MAX_REDACTIONS:
        raise ValueError("accepted capture event is unsafe")
    rebuilt_redactions: list[dict[str, str]] = []
    for item in redactions:
        if not isinstance(item, Mapping) or set(item) != {"field_class", "reason_code", "method"}:
            raise ValueError("accepted capture event is unsafe")
        field_class, reason, method = item["field_class"], item["reason_code"], item["method"]
        if field_class not in REDACTION_FIELD_CLASSES or reason not in REDACTION_REASON_CODES or method not in REDACTION_METHODS:
            raise ValueError("accepted capture event is unsafe")
        rebuilt_redactions.append(_redaction(field_class, reason, method))
    event_redactions = result.event.get("redactions")
    if bool(event_redactions) != bool(rebuilt_redactions) or (event_redactions and list(event_redactions) != rebuilt_redactions):
        raise ValueError("accepted capture event is unsafe")
    event: dict[str, Any] = {"schema_id": CONTRACT_ID, "descriptors": rebuilt}
    if rebuilt_redactions:
        event["redactions"] = rebuilt_redactions
    return event


def _new_confined_target(path: str | os.PathLike[str], repository_root: Path) -> tuple[Path, tuple[str, ...]]:
    supplied = Path(path)
    root = repository_root.resolve(strict=True)
    if not supplied.is_absolute() or ".." in supplied.parts:
        raise ValueError("output target must be an absolute descendant of the repository root")
    try:
        resolved = supplied.resolve(strict=False)
        relative = resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as error:
        raise ValueError("output target must stay inside the repository root") from error
    if len(relative.parts) < 2 or resolved.exists() or resolved.is_symlink():
        raise ValueError("output target must be a new repository descendant")
    return root, relative.parts


def write_accepted(
    path: str | os.PathLike[str], result: CaptureResult, repository_root: str | os.PathLike[str] | None = None,
) -> None:
    """Emit one revalidated accepted result below the supplied or current repository root."""
    if (
        not isinstance(result, CaptureResult)
        or result.outcome != "accepted"
        or result.event is None
    ):
        raise ValueError("only an accepted capture result may be emitted")
    root, parts = _new_confined_target(path, Path.cwd() if repository_root is None else Path(repository_root))
    event = _validated_accepted_event(result, root)
    public: dict[str, Any] = {"schema_id": CONTRACT_ID, "outcome": "accepted", "code": "accepted", "event": event}
    if result.redactions:
        public["redactions"] = list(result.redactions)
    payload = json.dumps(public, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    directory = os.open(root, directory_flags)
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, mode=0o700, dir_fd=directory)
            except FileExistsError:
                pass
            next_directory = os.open(part, directory_flags, dir_fd=directory)
            os.close(directory)
            directory = next_directory
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(parts[-1], flags, 0o600, dir_fd=directory)
    except OSError as error:
        raise ValueError("output target must be new beneath real repository directories") from error
    finally:
        os.close(directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n", closefd=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)


def _read_candidate(path: str) -> Any:
    candidate_path = Path(path)
    if not candidate_path.is_file() or candidate_path.is_symlink() or candidate_path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("unsafe_shape")
    return json.loads(candidate_path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check",))
    parser.add_argument("candidate")
    arguments = parser.parse_args(argv)
    try:
        candidate = _read_candidate(arguments.candidate)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        result = _refused("unsafe_shape")
    else:
        result = capture_candidate(candidate, Path.cwd())
    print(json.dumps(result.public(), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
