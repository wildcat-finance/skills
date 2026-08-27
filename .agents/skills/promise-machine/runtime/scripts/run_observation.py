#!/usr/bin/env python3
"""Validate promise-machine-run-observation/v1 JSON Lines records."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import re
import stat
import sys
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, DecimalException
from pathlib import Path
from typing import Any


CONTRACT_ID = "promise-machine-run-observation/v1"
SCHEMA_PATH = Path("schemas/promise-machine-run-observation-v1.schema.json")
MAX_TOTAL_BYTES = 1_048_576
MAX_LINE_BYTES = 65_536
MAX_EVENTS = 512
MAX_DEPTH = 12
MAX_STRING = 4_096
MAX_COLLECTION = 128
MAX_FINDINGS = 100
MAX_DISPLAY_PATH = 512
MAX_REPOSITORY_SEGMENT_BYTES = 255
MAX_REPOSITORY_PATH_BYTES = 4_096
MAX_FINITE_NUMBER = Decimal(str(sys.float_info.max))
REPOSITORY_PATH_NORMALIZATION = "NFC"

EVENT_TYPES = {
    "run.started",
    "capability.started",
    "capability.finished",
    "transition.refused",
    "retry.scheduled",
    "handoff.recorded",
    "run.finished",
}
EVIDENCE_CLASSES = {
    "checked",
    "recomputed",
    "proved",
    "measured",
    "recorded",
    "attested",
    "inferred",
}
RUN_STATUSES = {"success", "refused", "handoff", "failed"}
CAPABILITY_STATUSES = {"success", "refused", "failed"}

PLACEHOLDER_PATTERN = (
    r"(?:[Uu][Nn][Kk][Nn][Oo][Ww][Nn]|[Uu][Nn][Ss][Ee][Tt]|"
    r"[Nn][Oo][Nn][Ee]|[Nn]/[Aa]|[Nn][Aa]|[Tt][Bb][Dd]|"
    r"[Pp][Ll][Aa][Cc][Ee][Hh][Oo][Ll][Dd][Ee][Rr])"
)
ID_RE = re.compile(
    rf"^(?!{PLACEHOLDER_PATTERN}$)[A-Za-z0-9][A-Za-z0-9._:-]{{0,127}}$"
)
OBSERVED_STRING_RE = re.compile(
    rf"^(?!\s*{PLACEHOLDER_PATTERN}\s*$)(?=[\s\S]*\S)[\s\S]+$"
)
UNKNOWN_FIELD_RE = re.compile(r"^(?=[\x20-\x7E]*[A-Za-z0-9])[\x20-\x7E]+$")
REPOSITORY_PATH_RE = re.compile(
    rf"^(?!{PLACEHOLDER_PATTERN}$)"
    r"(?!/)(?!.*//)"
    r"(?!.*(?:^|/)\.(?:/|$))(?!.*(?:^|/)\.\.(?:/|$))"
    r'(?!.*[<>:"\\|?*\u0000-\u001F\u007F-\u009F])'
    r"(?!.*[\u00AD\u0600-\u0605\u061C\u06DD\u070F\u0890-\u0891\u08E2"
    r"\u180E\u200B-\u200F\u202A-\u202E\u2060-\u2064\u2066-\u206F"
    r"\uD800-\uDFFF\uFEFF\uFFF9-\uFFFB])"
    r"(?!.*(?:^|/)(?:[Cc][Oo][Nn]|[Pp][Rr][Nn]|[Aa][Uu][Xx]|"
    r"[Nn][Uu][Ll]|[Cc][Oo][Mm](?:[1-9]|\u00B9|\u00B2|\u00B3)|"
    r"[Ll][Pp][Tt](?:[1-9]|\u00B9|\u00B2|\u00B3)|"
    r"[Cc][Oo][Nn][Ii][Nn]\$|[Cc][Oo][Nn][Oo][Uu][Tt]\$|"
    r"[Cc][Ll][Oo][Cc][Kk]\$)"
    r"(?:\.[^/]*)?(?:/|$))"
    r"(?!.*[. ](?:/|$))[^/]{1,255}(?:/[^/]{1,255})*$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_RE = re.compile(r"^[0-9a-f]{40}$")
TIME_RE = re.compile(
    r"^(?:(?:(?!0000)\d{4})-(?:(?:0[13578]|1[02])-(?:0[1-9]|[12]\d|3[01])|"
    r"(?:0[469]|11)-(?:0[1-9]|[12]\d|30)|02-(?:0[1-9]|1\d|2[0-8]))|"
    r"(?:[0-9]{2}(?:0[48]|[2468][048]|[13579][26])|"
    r"(?:[13579][26]|[2468][048]|0[48])00)-02-29)"
    r"T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d"
    r"(?:\.\d{1,9})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$"
)
ESTIMATE_RE = re.compile(
    r"(?:estimate|estimation|approximat|guess(?:ed|ing)?|heuristic|"
    r"project(?:ed|ion)|predict(?:ed|ion)|forecast(?:ed|ing)?|ballpark|"
    r"assum(?:e|ed|ing|ption)|extrapolat(?:e|ed|ing|ion)|"
    r"modell?ed|modell?ing|rough|approx(?:\.|imate|imation)?|"
    r"deriv(?:e|ed|ing|ation)|infer(?:red|ring|ence)|"
    r"calculat(?:e|ed|ing|ion)|round(?:ed|ing)?|circa|about|"
    r"unmeasured|synthetic|speculat(?:e|ed|ing|ion|ive)|"
    r"best[\s_-]*effort|rule[\s_-]*of[\s_-]*thumb|likely|maybe)",
    re.IGNORECASE,
)
HIDDEN_NAMES = {
    "analysis",
    "chain-of-thought",
    "chain_of_thought",
    "hidden-reasoning",
    "hidden_reasoning",
    "internal-reasoning",
    "internal_reasoning",
    "internal_monologue",
    "inner_monologue",
    "deliberation",
    "rationale",
    "reasoning",
    "scratchpad",
    "thought",
    "thoughts",
}
RAW_NAMES = {
    "access_token",
    "answer",
    "api_key",
    "argument",
    "arguments",
    "args",
    "argv",
    "auth_token",
    "api_token",
    "assistant_message",
    "bearer",
    "chat_messages",
    "chat",
    "command",
    "completion",
    "content",
    "contents",
    "conversation_messages",
    "conversation",
    "credential",
    "credentials",
    "environment",
    "dialogue",
    "env",
    "env_vars",
    "function_arguments",
    "function_call_arguments",
    "headers",
    "input",
    "input_text",
    "instruction",
    "instructions",
    "history",
    "jwt",
    "messages",
    "message",
    "model_output",
    "mnemonic",
    "output",
    "password",
    "payload",
    "private_key",
    "prompt",
    "request",
    "request_body",
    "query",
    "response_body",
    "response",
    "reply",
    "return",
    "result",
    "raw_args",
    "raw_arguments",
    "secret",
    "secret_key",
    "signed_payload",
    "session_token",
    "stderr",
    "stdout",
    "tool_output",
    "cookies",
    "system_message",
    "transcript",
    "user_message",
}

SAFE_DESCRIPTOR_SUFFIXES = {
    "count",
    "digest",
    "format",
    "hash",
    "id",
    "identifier",
    "length",
    "name",
    "names",
    "present",
    "ref",
    "reference",
    "selector",
    "size",
    "status",
    "type",
}
BIDI_FORMATTING = {
    "\u061c",
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
}

COMMON_REQUIRED = {
    "schema_id",
    "run_id",
    "sequence",
    "event_id",
    "time",
    "type",
    "correlation_id",
}
COMMON_OPTIONAL = {"parent_event_id", "metadata", "unknowns"}
EVENT_REQUIRED = {
    "run.started": {"subject", "scope", "context"},
    "capability.started": {"capability_id", "capability"},
    "capability.finished": {
        "capability_id",
        "started_event_id",
        "status",
        "duration_ms",
    },
    "transition.refused": {
        "promise_id",
        "blocked_transition",
        "reason_code",
        "recovery",
        "caused_by",
    },
    "retry.scheduled": {"retry_of", "attempt", "reason_code", "after_ms"},
    "handoff.recorded": {
        "producer",
        "consumer",
        "source_event_id",
        "subject",
        "scope",
        "time_domain",
        "evidence_refs",
    },
    "run.finished": {"started_event_id", "status", "outcome"},
}
EVENT_OPTIONAL = {
    "run.started": {"host", "model", "repository"},
    "capability.started": set(),
    "capability.finished": {"evidence", "token_usage"},
    "transition.refused": {"evidence", "evidence_refs"},
    "retry.scheduled": set(),
    "handoff.recorded": set(),
    "run.finished": {"duration_ms", "token_usage", "repository"},
}


@dataclass(frozen=True)
class Finding:
    code: str
    fault: str
    path: str
    message: str
    recovery: str
    line: int | None = None
    run_id: str | None = None
    event_id: str | None = None
    correlation_id: str | None = None


class DuplicateKey(ValueError):
    pass


def _pairs_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(key)
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError("non-finite number")


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except DecimalException as error:
        raise ValueError("number is outside the supported decimal syntax") from error


def _normalise_field_name(name: str) -> str:
    separated = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", separated)
    return re.sub(r"[^a-z0-9]+", "_", separated.lower()).strip("_")


def _pointer_segment(name: str) -> str:
    escaped = name.replace("~", "~0").replace("/", "~1")
    return json.dumps(escaped, ensure_ascii=True)[1:-1]


def _safe_identity(value: Any) -> str | None:
    if isinstance(value, str) and ID_RE.fullmatch(value) is not None:
        return value
    return None


def _observed_string(value: Any) -> bool:
    return isinstance(value, str) and OBSERVED_STRING_RE.fullmatch(value) is not None


def _exposed_fact_string(value: Any) -> bool:
    return _observed_string(value) and ESTIMATE_RE.search(value) is None


def _json_integer(value: Any, *, minimum: int) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return False
    if isinstance(value, int):
        return abs(value) <= MAX_FINITE_NUMBER and value >= minimum
    if isinstance(value, float):
        return math.isfinite(value) and value.is_integer() and value >= minimum
    return (
        value.is_finite()
        and abs(value) <= MAX_FINITE_NUMBER
        and value == value.to_integral_value()
        and value >= minimum
    )


def _safe_descriptor_value(suffix: str, value: Any) -> bool:
    if suffix in {"count", "length", "size"}:
        return _json_integer(value, minimum=0)
    if suffix == "present":
        return isinstance(value, bool)
    if suffix in {"digest", "hash"}:
        return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None
    return _safe_identity(value) is not None


def _descriptor_suffix(parts: list[str], compact: str) -> str | None:
    if len(parts) > 1 and parts[-1] in SAFE_DESCRIPTOR_SUFFIXES:
        return parts[-1]
    for suffix in sorted(SAFE_DESCRIPTOR_SUFFIXES, key=len, reverse=True):
        if compact.endswith(suffix) and len(compact) > len(suffix):
            return suffix
    return None


def _forbidden_name(name: str, forbidden: set[str], value: Any) -> bool:
    normal = _normalise_field_name(name)
    compact = normal.replace("_", "")
    normalised = {_normalise_field_name(item) for item in forbidden}
    if normal in normalised or compact in {
        item.replace("_", "") for item in normalised
    }:
        return True
    parts = list(filter(None, normal.split("_")))
    tokens = set(parts)
    descriptor_suffix = _descriptor_suffix(parts, compact)
    if forbidden is HIDDEN_NAMES:
        if (
            descriptor_suffix is not None
            and _safe_descriptor_value(descriptor_suffix, value)
        ):
            return False
        if tokens & {
            "analysis",
            "cot",
            "deliberation",
            "monologue",
            "rationale",
            "reasoning",
            "reflection",
            "scratchpad",
            "thinking",
            "thought",
            "thoughts",
            "cognition",
            "cognitive",
            "mental",
        }:
            return True
        hidden_payload_parts = {"body", "buffer", "content", "data", "notes", "text", "value"}
        if (
            compact.startswith("cot")
            and compact[3:] in hidden_payload_parts
        ) or (
            compact.endswith("cot")
            and compact[:-3] in hidden_payload_parts
        ):
            return True
        return any(
            marker in compact
            for marker in (
                "analysis",
                "chainofthought",
                "deliberation",
                "innermonologue",
                "internalmonologue",
                "rationale",
                "reasoning",
                "reflection",
                "scratchpad",
                "thinking",
                "thought",
                "cognition",
                "cognitive",
                "mental",
            )
        )
    if forbidden is RAW_NAMES:
        if (
            descriptor_suffix is not None
            and _safe_descriptor_value(descriptor_suffix, value)
        ):
            return False
        if tokens & {
            "authorization",
            "bearer",
            "completion",
            "cookie",
            "credential",
            "credentials",
            "directive",
            "directives",
            "environment",
            "mnemonic",
            "password",
            "payload",
            "prompt",
            "instruction",
            "instructions",
            "secret",
            "secrets",
            "stderr",
            "stdout",
            "transcript",
        }:
            return True
        if any(
            pair.issubset(tokens)
            for pair in (
                {"access", "token"},
                {"api", "key"},
                {"api", "token"},
                {"auth", "header"},
                {"auth", "token"},
                {"env", "vars"},
                {"function", "arguments"},
                {"id", "token"},
                {"model", "output"},
                {"oauth", "token"},
                {"private", "key"},
                {"raw", "args"},
                {"raw", "arguments"},
                {"refresh", "token"},
                {"session", "token"},
                {"signed", "payload"},
                {"tool", "result"},
                {"tool", "response"},
                {"tool", "output"},
            )
        ):
            return True
        actor_tokens = {
            "agent",
            "ai",
            "assistant",
            "bot",
            "chat",
            "conversation",
            "developer",
            "dialogue",
            "human",
            "llm",
            "message",
            "system",
            "user",
            "cli",
            "command",
            "http",
            "shell",
            "subprocess",
        }
        if tokens & {"message", "messages"} and tokens & actor_tokens:
            return True
        if tokens & {"content", "contents"}:
            return True
        payload_tokens = {
            "answer",
            "argument",
            "arguments",
            "args",
            "body",
            "call",
            "command",
            "content",
            "data",
            "code",
            "directive",
            "directives",
            "execution",
            "generation",
            "history",
            "input",
            "instruction",
            "instructions",
            "invocation",
            "log",
            "message",
            "messages",
            "observation",
            "output",
            "parameters",
            "params",
            "query",
            "reply",
            "request",
            "response",
            "result",
            "return",
            "rule",
            "rules",
            "text",
            "trace",
            "turn",
            "turns",
            "utterance",
            "utterances",
            "value",
            "artifact",
            "artifacts",
        }
        if "raw" in tokens and tokens & (payload_tokens | {"env", "environment"}):
            return True
        payload_actors = actor_tokens | {
            "function",
            "model",
            "request",
            "response",
            "tool",
        }
        if tokens & payload_actors and tokens & payload_tokens:
            return True
        if tokens & {"request", "response"} and tokens & {
            "argument",
            "arguments",
            "args",
            "parameters",
            "params",
            "query",
        }:
            return True
        if tokens & {"header", "headers"} and not tokens & {
            "count",
            "name",
            "names",
        }:
            return True
        if tokens & {"input", "request", "response"} and tokens & {
            "body",
            "content",
            "data",
            "text",
            "value",
        }:
            return True
        if "raw" in tokens and tokens & {"body", "content", "data", "text", "value"}:
            return True
        if tokens & {"argument", "arguments"} and tokens & {
            "body",
            "content",
            "data",
            "text",
            "value",
        }:
            return True
        if any(
            pair.issubset(tokens)
            for pair in (
                {"command", "line"},
                {"command", "script"},
                {"source", "code"},
                {"stack", "trace"},
                {"execution", "trace"},
                {"trace", "data"},
            )
        ):
            return True
        if compact.startswith(
            (
                "argumentbody",
                "argumentcontent",
                "argumentdata",
                "argumentsbody",
                "argumentscontent",
                "argumentsdata",
                "argumentstext",
                "argumentsvalue",
                "argumenttext",
                "argumentvalue",
                "authheader",
                "idtoken",
                "refreshtoken",
                "toolresponse",
                "toolresult",
            )
        ):
            return True
        compact_actor_payload = any(
            actor + payload in compact or payload + actor in compact
            for actor in payload_actors
            for payload in payload_tokens
        )
        return compact_actor_payload or any(
            marker in compact
            for marker in (
                "accesstoken",
                "apikey",
                "authorization",
                "authtoken",
                "completion",
                "commandline",
                "shellcommand",
                "subprocesscommand",
                "shellscript",
                "credential",
                "directive",
                "environment",
                "mnemonic",
                "modeloutput",
                "password",
                "payload",
                "privatekey",
                "prompt",
                "rawargs",
                "rawarguments",
                "rawinput",
                "inputraw",
                "instruction",
                "userinput",
                "assistantoutput",
                "assistantresponse",
                "functionresult",
                "toolcallarguments",
                "requestarguments",
                "sessiontoken",
                "signedpayload",
                "sourcecode",
                "stacktrace",
                "executiontrace",
                "tracedata",
                "tooloutput",
                "transcript",
            )
        )
    return False


def _safe_repository_path(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs"}
        for character in value
    ):
        return False
    if any(character in BIDI_FORMATTING for character in value):
        return False
    if unicodedata.normalize(REPOSITORY_PATH_NORMALIZATION, value) != value:
        return False
    if REPOSITORY_PATH_RE.fullmatch(value) is None:
        return False
    try:
        encoded = value.encode("utf-8")
        return len(encoded) <= MAX_REPOSITORY_PATH_BYTES and all(
            len(segment.encode("utf-8")) <= MAX_REPOSITORY_SEGMENT_BYTES
            for segment in value.split("/")
        )
    except UnicodeEncodeError:
        return False


def _unknown_fact_family(name: str) -> str | None:
    normal = _normalise_field_name(name)
    if not normal:
        return None
    tokens = set(normal.split("_"))
    compact = normal.replace("_", "")
    if "host" in tokens or compact in {
        "host",
        "hostid",
        "hostidentity",
        "hostname",
        "hostsource",
    }:
        return "host"
    if "model" in tokens or compact in {
        "model",
        "modelid",
        "modelidentity",
        "modelname",
        "modelsource",
        "modelversion",
    }:
        return "model"
    if (
        "token" in tokens
        or "tokens" in tokens
        or compact.startswith(("inputtoken", "outputtoken", "tokenusage"))
        or compact == "accountingid"
    ):
        return "token_usage"
    return normal


class Validator:
    def __init__(self, display_path: str):
        self.display_path = display_path
        self.findings: list[Finding] = []
        self.events: list[tuple[int, dict[str, Any]]] = []
        self.snapshot: tuple[int, int, int, str] | None = None

    def add(
        self,
        code: str,
        fault: str,
        message: str,
        recovery: str,
        *,
        line: int | None = None,
        pointer: str = "",
        event: dict[str, Any] | None = None,
    ) -> None:
        if len(self.findings) >= MAX_FINDINGS:
            return
        run_id = _safe_identity(event.get("run_id")) if isinstance(event, dict) else None
        event_id = _safe_identity(event.get("event_id")) if isinstance(event, dict) else None
        correlation_id = (
            _safe_identity(event.get("correlation_id"))
            if isinstance(event, dict)
            else None
        )
        self.findings.append(
            Finding(
                code,
                fault,
                self.display_path + pointer,
                message,
                recovery,
                line,
                run_id,
                event_id,
                correlation_id,
            )
        )

    def read(self, path: Path, root: Path) -> None:
        try:
            info = path.lstat()
        except (OSError, ValueError):
            self.add(
                "RO001",
                "input",
                "input is absent or unreadable",
                "name one readable regular JSONL file inside the repository",
            )
            return
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            self.add(
                "RO001",
                "input",
                "input is not a regular non-symlink file",
                "copy the record to a confined regular file and retry",
            )
            return
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root.resolve(strict=True))
        except (OSError, ValueError):
            self.add(
                "RO001",
                "input",
                "input does not resolve inside the repository",
                "name a repository-confined regular file",
            )
            return
        if info.st_size > MAX_TOTAL_BYTES:
            self.add(
                "RO002",
                "limit",
                f"input exceeds the {MAX_TOTAL_BYTES}-byte limit",
                "split or reduce the record without omitting required lifecycle events",
            )
            return
        try:
            descriptor = os.open(
                path,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0),
            )
            with os.fdopen(descriptor, "rb") as handle:
                opened = os.fstat(handle.fileno())
                snapshot_digest = hashlib.sha256()
                if (
                    not stat.S_ISREG(opened.st_mode)
                    or opened.st_dev != info.st_dev
                    or opened.st_ino != info.st_ino
                ):
                    self.add(
                        "RO001",
                        "input",
                        "input identity changed before it could be read",
                        "retry with one stable confined regular file",
                    )
                    return
                number = 0
                total_read = 0
                while True:
                    raw = handle.readline(MAX_LINE_BYTES + 2)
                    if not raw:
                        break
                    snapshot_digest.update(raw)
                    total_read += len(raw)
                    if total_read > MAX_TOTAL_BYTES:
                        self.add(
                            "RO002",
                            "limit",
                            f"input exceeds the {MAX_TOTAL_BYTES}-byte limit",
                            "split or reduce the record without omitting required lifecycle events",
                        )
                        break
                    number += 1
                    if number > MAX_EVENTS:
                        self.add(
                            "RO002",
                            "limit",
                            f"record exceeds the {MAX_EVENTS}-event limit",
                            "split the record at a run boundary",
                            line=number,
                        )
                        break
                    if len(raw) > MAX_LINE_BYTES or not raw.endswith(b"\n"):
                        code = "RO003" if len(raw) > MAX_LINE_BYTES else "RO004"
                        message = (
                            f"line exceeds the {MAX_LINE_BYTES}-byte limit"
                            if code == "RO003"
                            else "record is truncated or lacks a final newline"
                        )
                        self.add(
                            code,
                            "limit" if code == "RO003" else "syntax",
                            message,
                            "write one complete bounded JSON object followed by a newline",
                            line=number,
                        )
                        if len(raw) > MAX_LINE_BYTES:
                            while raw and not raw.endswith(b"\n"):
                                raw = handle.readline(MAX_LINE_BYTES + 2)
                                snapshot_digest.update(raw)
                                total_read += len(raw)
                                if total_read > MAX_TOTAL_BYTES:
                                    self.add(
                                        "RO002",
                                        "limit",
                                        f"input exceeds the {MAX_TOTAL_BYTES}-byte limit",
                                        "split or reduce the record without omitting required lifecycle events",
                                    )
                                    return
                        continue
                    try:
                        text = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        self.add(
                            "RO004",
                            "syntax",
                            "line is not valid UTF-8",
                            "encode the complete JSON object as UTF-8",
                            line=number,
                        )
                        continue
                    try:
                        value = json.loads(
                            text,
                            object_pairs_hook=_pairs_object,
                            parse_constant=_reject_constant,
                            parse_float=_parse_decimal,
                            parse_int=_parse_decimal,
                        )
                    except DuplicateKey:
                        self.add(
                            "RO005",
                            "syntax",
                            "line contains a duplicate object key",
                            "retain one value for every object key at every depth",
                            line=number,
                        )
                        continue
                    except (json.JSONDecodeError, ValueError):
                        self.add(
                            "RO004",
                            "syntax",
                            "line is not one complete JSON object",
                            "write one complete JSON object on the line",
                            line=number,
                        )
                        continue
                    except RecursionError:
                        self.add(
                            "RO006",
                            "limit",
                            "line exceeds the safe parser nesting boundary",
                            f"reduce nesting to at most {MAX_DEPTH} levels",
                            line=number,
                        )
                        continue
                    if not isinstance(value, dict):
                        self.add(
                            "RO007",
                            "shape",
                            "event is not an object",
                            "write a closed event object",
                            line=number,
                        )
                        continue
                    self.events.append((number, value))
                after = os.fstat(handle.fileno())
                if (
                    after.st_size != opened.st_size
                    or after.st_mtime_ns != opened.st_mtime_ns
                    or after.st_ctime_ns != opened.st_ctime_ns
                ):
                    self.add(
                        "RO001",
                        "input",
                        "input changed while it was being read",
                        "retry with one stable confined regular file",
                    )
                try:
                    named_after = path.lstat()
                except (OSError, ValueError):
                    named_after = None
                try:
                    resolved_after = path.resolve(strict=True)
                    resolved_after.relative_to(root.resolve(strict=True))
                    confined_after = True
                except (OSError, ValueError):
                    confined_after = False
                if (
                    named_after is None
                    or stat.S_ISLNK(named_after.st_mode)
                    or not stat.S_ISREG(named_after.st_mode)
                    or named_after.st_dev != opened.st_dev
                    or named_after.st_ino != opened.st_ino
                    or not confined_after
                ):
                    self.add(
                        "RO001",
                        "input",
                        "input path changed while it was being read",
                        "retry with one stable confined regular file",
                    )
                self.snapshot = (
                    opened.st_dev,
                    opened.st_ino,
                    total_read,
                    snapshot_digest.hexdigest(),
                )
        except (OSError, ValueError):
            self.add(
                "RO001",
                "input",
                "input could not be read as a stable regular file",
                "restore a readable regular file and retry",
            )

    def read_captured(self, data: bytes) -> None:
        """Parse one already-confined immutable byte snapshot."""
        if not isinstance(data, bytes):
            self.add(
                "RO001",
                "input",
                "captured input is not a byte snapshot",
                "capture one stable bounded byte sequence and retry",
            )
            return
        if len(data) > MAX_TOTAL_BYTES:
            self.add(
                "RO002",
                "limit",
                f"input exceeds the {MAX_TOTAL_BYTES}-byte limit",
                "split or reduce the record without omitting required lifecycle events",
            )
            return

        handle = io.BytesIO(data)
        number = 0
        while True:
            raw = handle.readline(MAX_LINE_BYTES + 2)
            if not raw:
                break
            number += 1
            if number > MAX_EVENTS:
                self.add(
                    "RO002",
                    "limit",
                    f"record exceeds the {MAX_EVENTS}-event limit",
                    "split the record at a run boundary",
                    line=number,
                )
                break
            if len(raw) > MAX_LINE_BYTES or not raw.endswith(b"\n"):
                code = "RO003" if len(raw) > MAX_LINE_BYTES else "RO004"
                message = (
                    f"line exceeds the {MAX_LINE_BYTES}-byte limit"
                    if code == "RO003"
                    else "record is truncated or lacks a final newline"
                )
                self.add(
                    code,
                    "limit" if code == "RO003" else "syntax",
                    message,
                    "write one complete bounded JSON object followed by a newline",
                    line=number,
                )
                if len(raw) > MAX_LINE_BYTES:
                    while raw and not raw.endswith(b"\n"):
                        raw = handle.readline(MAX_LINE_BYTES + 2)
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                self.add(
                    "RO004",
                    "syntax",
                    "line is not valid UTF-8",
                    "encode the complete JSON object as UTF-8",
                    line=number,
                )
                continue
            try:
                value = json.loads(
                    text,
                    object_pairs_hook=_pairs_object,
                    parse_constant=_reject_constant,
                    parse_float=_parse_decimal,
                    parse_int=_parse_decimal,
                )
            except DuplicateKey:
                self.add(
                    "RO005",
                    "syntax",
                    "line contains a duplicate object key",
                    "retain one value for every object key at every depth",
                    line=number,
                )
                continue
            except (json.JSONDecodeError, ValueError):
                self.add(
                    "RO004",
                    "syntax",
                    "line is not one complete JSON object",
                    "write one complete JSON object on the line",
                    line=number,
                )
                continue
            except RecursionError:
                self.add(
                    "RO006",
                    "limit",
                    "line exceeds the safe parser nesting boundary",
                    f"reduce nesting to at most {MAX_DEPTH} levels",
                    line=number,
                )
                continue
            if not isinstance(value, dict):
                self.add(
                    "RO007",
                    "shape",
                    "event is not an object",
                    "write a closed event object",
                    line=number,
                )
                continue
            self.events.append((number, value))

    def finalise_input(self, path: Path, root: Path) -> None:
        """Bind a clean result to one bounded final reread of the named path."""
        if self.snapshot is None:
            self.add(
                "RO001",
                "input",
                "validated input snapshot is unavailable",
                "retry with one stable confined regular file",
            )
            return
        expected_dev, expected_ino, expected_size, expected_digest = self.snapshot
        descriptor = None
        try:
            named_before = path.lstat()
            resolved = path.resolve(strict=True)
            resolved.relative_to(root.resolve(strict=True))
            if (
                stat.S_ISLNK(named_before.st_mode)
                or not stat.S_ISREG(named_before.st_mode)
                or named_before.st_dev != expected_dev
                or named_before.st_ino != expected_ino
                or named_before.st_size > MAX_TOTAL_BYTES
            ):
                raise OSError("input identity changed before final reread")
            descriptor = os.open(
                path,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0),
            )
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_dev != expected_dev
                or opened.st_ino != expected_ino
            ):
                raise OSError("input identity changed during final reread")
            remaining = MAX_TOTAL_BYTES + 1
            final_bytes = bytearray()
            while remaining:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    break
                final_bytes.extend(chunk)
                remaining -= len(chunk)
            after = os.fstat(descriptor)
            named_after = path.lstat()
            resolved_after = path.resolve(strict=True)
            resolved_after.relative_to(root.resolve(strict=True))
            final_digest = hashlib.sha256(final_bytes).hexdigest()
            if (
                len(final_bytes) > MAX_TOTAL_BYTES
                or len(final_bytes) != expected_size
                or final_digest != expected_digest
                or after.st_dev != expected_dev
                or after.st_ino != expected_ino
                or after.st_size != expected_size
                or after.st_mtime_ns != opened.st_mtime_ns
                or after.st_ctime_ns != opened.st_ctime_ns
                or stat.S_ISLNK(named_after.st_mode)
                or not stat.S_ISREG(named_after.st_mode)
                or named_after.st_dev != expected_dev
                or named_after.st_ino != expected_ino
                or named_after.st_size != expected_size
                or named_after.st_mtime_ns != after.st_mtime_ns
                or named_after.st_ctime_ns != after.st_ctime_ns
            ):
                raise OSError("input bytes changed during final reread")
        except (OSError, ValueError):
            self.add(
                "RO001",
                "input",
                "input changed after validation and before final observation",
                "retry with one stable confined regular file",
            )
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

    def check_limits_and_names(
        self,
        value: Any,
        *,
        line: int,
        event: dict[str, Any],
        pointer: str = "",
        depth: int = 0,
    ) -> None:
        if depth > MAX_DEPTH:
            self.add(
                "RO006",
                "limit",
                f"value exceeds the nesting limit of {MAX_DEPTH}",
                "flatten the bounded metadata",
                line=line,
                pointer=pointer,
                event=event,
            )
            return
        if isinstance(value, str) and len(value) > MAX_STRING:
            self.add(
                "RO006",
                "limit",
                f"string exceeds the {MAX_STRING}-character limit",
                "replace raw content with a bounded identifier, selector, or digest",
                line=line,
                pointer=pointer,
                event=event,
            )
        if (
            isinstance(value, float)
            and (not math.isfinite(value) or abs(value) > float(MAX_FINITE_NUMBER))
        ) or (
            isinstance(value, Decimal)
            and (not value.is_finite() or abs(value) > MAX_FINITE_NUMBER)
        ) or (
            isinstance(value, int)
            and not isinstance(value, bool)
            and abs(value) > MAX_FINITE_NUMBER
        ):
            self.add(
                "RO007",
                "shape",
                "number is outside the bounded finite JSON range",
                f"record a finite number whose absolute value is at most {MAX_FINITE_NUMBER}",
                line=line,
                pointer=pointer,
                event=event,
            )
        if isinstance(value, dict):
            if len(value) > MAX_COLLECTION:
                self.add(
                    "RO006",
                    "limit",
                    f"object exceeds the {MAX_COLLECTION}-member limit",
                    "reduce the metadata to bounded observable facts",
                    line=line,
                    pointer=pointer,
                    event=event,
                )
            for key, child in value.items():
                if len(key) > MAX_STRING:
                    self.add(
                        "RO006",
                        "limit",
                        f"object key exceeds the {MAX_STRING}-character limit",
                        "replace the key with one bounded observable name",
                        line=line,
                        pointer=pointer,
                        event=event,
                    )
                    continue
                valid_name = UNKNOWN_FIELD_RE.fullmatch(key) is not None
                hidden_name = _forbidden_name(key, HIDDEN_NAMES, child)
                raw_name = _forbidden_name(key, RAW_NAMES, child)
                if not valid_name:
                    child_pointer = f"{pointer}/[invalid-field]"
                    self.add(
                        "RO007",
                        "shape",
                        "object key does not identify an observable field",
                        "replace the key with a bounded name containing an ASCII letter or digit",
                        line=line,
                        pointer=child_pointer,
                        event=event,
                    )
                elif hidden_name or raw_name:
                    child_pointer = f"{pointer}/[forbidden-field]"
                else:
                    child_pointer = f"{pointer}/{_pointer_segment(key)}"
                if hidden_name:
                    self.add(
                        "RO013",
                        "reasoning",
                        "hidden or internal reasoning is not observable record data",
                        "remove the field and record only an observable outcome or refusal",
                        line=line,
                        pointer=child_pointer,
                        event=event,
                    )
                if raw_name:
                    self.add(
                        "RO014",
                        "payload",
                        "raw or sensitive payload fields are forbidden",
                        "replace content with bounded metadata, a selector, or a digest",
                        line=line,
                        pointer=child_pointer,
                        event=event,
                    )
                self.check_limits_and_names(
                    child,
                    line=line,
                    event=event,
                    pointer=child_pointer,
                    depth=depth + 1,
                )
        elif isinstance(value, list):
            if len(value) > MAX_COLLECTION:
                self.add(
                    "RO006",
                    "limit",
                    f"array exceeds the {MAX_COLLECTION}-item limit",
                    "reduce the collection or split at a run boundary",
                    line=line,
                    pointer=pointer,
                    event=event,
                )
            for index, child in enumerate(value):
                self.check_limits_and_names(
                    child,
                    line=line,
                    event=event,
                    pointer=f"{pointer}/{index}",
                    depth=depth + 1,
                )

    def shape(self, line: int, event: dict[str, Any]) -> bool:
        self.check_limits_and_names(event, line=line, event=event)
        event_type = event.get("type")
        if not isinstance(event_type, str) or event_type not in EVENT_TYPES:
            self.add(
                "RO007",
                "shape",
                "event type is absent or unsupported",
                "use one event type from the v1 closed union",
                line=line,
                pointer="/type",
                event=event,
            )
            return False
        required = COMMON_REQUIRED | EVENT_REQUIRED[event_type]
        allowed = required | COMMON_OPTIONAL | EVENT_OPTIONAL[event_type]
        missing = sorted(required - set(event))
        unknown = sorted(set(event) - allowed)
        if missing:
            code = "RO008" if "run_id" in missing else "RO007"
            self.add(
                code,
                "identity" if code == "RO008" else "shape",
                f"event omits required fields: {', '.join(missing)}",
                "supply every required v1 field without placeholders",
                line=line,
                event=event,
            )
        if unknown:
            self.add(
                "RO007",
                "shape",
                f"event contains {len(unknown)} field(s) outside its closed shape",
                "remove fields outside the selected v1 event shape",
                line=line,
                event=event,
            )
        self.scalar_fields(line, event)
        self.nested_fields(line, event)
        return not missing and not unknown

    def scalar_fields(self, line: int, event: dict[str, Any]) -> None:
        for key in ("run_id", "event_id", "correlation_id"):
            value = event.get(key)
            if not isinstance(value, str) or ID_RE.fullmatch(value) is None:
                self.add(
                    "RO008",
                    "identity",
                    f"{key} is not a bounded stable identity",
                    "supply a non-placeholder v1 identity",
                    line=line,
                    pointer=f"/{key}",
                    event=event,
                )
        if event.get("schema_id") != CONTRACT_ID:
            self.add(
                "RO008",
                "identity",
                "schema_id does not identify the v1 observation contract",
                f"set schema_id to {CONTRACT_ID}",
                line=line,
                pointer="/schema_id",
                event=event,
            )
        sequence = event.get("sequence")
        if not _json_integer(sequence, minimum=1):
            self.add(
                "RO009",
                "order",
                "sequence is not a positive integer",
                "number events contiguously from one",
                line=line,
                pointer="/sequence",
                event=event,
            )
        timestamp = event.get("time")
        if not isinstance(timestamp, str) or TIME_RE.fullmatch(timestamp) is None:
            self.add(
                "RO007",
                "shape",
                "time is not an RFC-3339 timestamp",
                "record an exposed RFC-3339 timestamp with an offset",
                line=line,
                pointer="/time",
                event=event,
            )
        elif timestamp:
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                self.add(
                    "RO007",
                    "shape",
                    "time is not a real RFC-3339 date and time",
                    "record a valid exposed timestamp",
                    line=line,
                    pointer="/time",
                    event=event,
                )
        for key in ("capability_id", "capability", "promise_id", "reason_code", "producer", "consumer"):
            if key in event and _safe_identity(event[key]) is None:
                self.add(
                    "RO007",
                    "shape",
                    f"{key} is not a bounded stable name",
                    "supply a bounded non-placeholder name",
                    line=line,
                    pointer=f"/{key}",
                    event=event,
                )
        for key in ("duration_ms", "after_ms", "attempt"):
            if key in event and not _json_integer(
                event[key], minimum=1 if key == "attempt" else 0
            ):
                self.add(
                    "RO007",
                    "shape",
                    f"{key} is not a non-negative integer",
                    "record a host-exposed non-negative integer",
                    line=line,
                    pointer=f"/{key}",
                    event=event,
                )

    def nested_fields(self, line: int, event: dict[str, Any]) -> None:
        for key in ("subject", "scope", "time_domain", "blocked_transition", "recovery"):
            if key in event and not _observed_string(event[key]):
                self.add(
                    "RO007",
                    "shape",
                    f"{key} is not a non-empty string",
                    "record one bounded observable value",
                    line=line,
                    pointer=f"/{key}",
                    event=event,
                )
        if "status" in event:
            accepted = RUN_STATUSES if event.get("type") == "run.finished" else CAPABILITY_STATUSES
            if not isinstance(event["status"], str) or event["status"] not in accepted:
                self.add(
                    "RO007",
                    "shape",
                    "status is outside the closed status set",
                    "use one status allowed for the event type",
                    line=line,
                    pointer="/status",
                    event=event,
                )
        if "parent_event_id" in event:
            self.require_id(line, event, "parent_event_id")
        if "started_event_id" in event:
            self.require_id(line, event, "started_event_id")
        if "source_event_id" in event:
            self.require_id(line, event, "source_event_id")
        if "caused_by" in event:
            self.require_id(line, event, "caused_by")
        if "metadata" in event:
            metadata = event["metadata"]
            if not isinstance(metadata, dict) or any(
                isinstance(value, (dict, list)) for value in metadata.values()
            ):
                self.add(
                    "RO007",
                    "shape",
                    "metadata is not a flat object of scalar observable facts",
                    "replace nested or raw content with bounded scalar metadata",
                    line=line,
                    pointer="/metadata",
                    event=event,
                )
        if "unknowns" in event:
            self.check_unknowns(line, event)
        for key in ("host", "model"):
            if key in event:
                self.check_host_fact(line, event, key)
        if "repository" in event:
            self.check_repository(line, event)
        if "context" in event:
            self.check_context(line, event)
        if "token_usage" in event:
            self.check_tokens(line, event)
        if "retry_of" in event:
            value = event["retry_of"]
            if (
                not isinstance(value, dict)
                or set(value) != {"run_id", "event_id"}
                or any(_safe_identity(value.get(name)) is None for name in value)
            ):
                self.add(
                    "RO007",
                    "shape",
                    "retry_of is not a closed run and event reference",
                    "name the current run and one earlier event",
                    line=line,
                    pointer="/retry_of",
                    event=event,
                )
        if "outcome" in event:
            value = event["outcome"]
            if not isinstance(value, dict) or set(value) != {"subject", "summary", "evidence_refs"}:
                self.add(
                    "RO007",
                    "shape",
                    "outcome is not a closed observed-outcome object",
                    "record subject, bounded summary, and evidence_refs",
                    line=line,
                    pointer="/outcome",
                    event=event,
                )
            elif not all(_observed_string(value[key]) for key in ("subject", "summary")):
                self.add(
                    "RO007",
                    "shape",
                    "outcome subject or summary is absent",
                    "record a bounded observed subject and summary",
                    line=line,
                    pointer="/outcome",
                    event=event,
                )
        if "evidence" in event:
            self.check_evidence_list(line, event)
        if "evidence_refs" in event:
            self.check_evidence_refs_shape(line, event, event["evidence_refs"], "/evidence_refs")
        if isinstance(event.get("outcome"), dict) and "evidence_refs" in event["outcome"]:
            self.check_evidence_refs_shape(
                line, event, event["outcome"]["evidence_refs"], "/outcome/evidence_refs"
            )

    def require_id(self, line: int, event: dict[str, Any], key: str) -> None:
        value = event.get(key)
        if _safe_identity(value) is None:
            self.add(
                "RO010",
                "reference",
                f"{key} is not a bounded event identity",
                "name one earlier event in this run",
                line=line,
                pointer=f"/{key}",
                event=event,
            )

    def check_unknowns(self, line: int, event: dict[str, Any]) -> None:
        unknowns = event["unknowns"]
        if not isinstance(unknowns, list) or not unknowns:
            self.add(
                "RO007",
                "shape",
                "unknowns is not a non-empty array",
                "omit unknowns or name each unavailable fact and reason",
                line=line,
                pointer="/unknowns",
                event=event,
            )
            return
        seen_fields: set[str] = set()
        for index, item in enumerate(unknowns):
            if (
                not isinstance(item, dict)
                or set(item) != {"field", "reason"}
                or not all(_observed_string(item.get(key)) for key in ("field", "reason"))
                or UNKNOWN_FIELD_RE.fullmatch(item.get("field", "")) is None
            ):
                self.add(
                    "RO007",
                    "shape",
                    "unknown fact is not a closed field-and-reason object",
                    "name the unavailable field and observable reason",
                    line=line,
                    pointer=f"/unknowns/{index}",
                    event=event,
                )
                continue
            field = _normalise_field_name(item["field"])
            family = _unknown_fact_family(item["field"])
            conflicts = (
                ("host" in event and family == "host")
                or ("model" in event and family == "model")
                or ("token_usage" in event and family == "token_usage")
            )
            if not field or field in seen_fields or conflicts:
                self.add(
                    "RO007",
                    "shape",
                    "unknown fact is repeated or contradicts a supplied fact",
                    "retain one unknown only when the named fact is unavailable",
                    line=line,
                    pointer=f"/unknowns/{index}",
                    event=event,
                )
            seen_fields.add(field)

    def check_host_fact(self, line: int, event: dict[str, Any], key: str) -> None:
        value = event[key]
        if (
            not isinstance(value, dict)
            or set(value) != {"source", "identity"}
            or not all(_exposed_fact_string(value.get(name)) for name in value)
        ):
            self.add(
                "RO015",
                "host-fact",
                f"optional {key} fact is absent, placeholder, or unbound",
                f"omit {key} and record an unknown, or name its exposed source and identity",
                line=line,
                pointer=f"/{key}",
                event=event,
            )

    def check_repository(self, line: int, event: dict[str, Any]) -> None:
        value = event["repository"]
        required = (
            {"path", "before_commit"}
            if event.get("type") == "run.started"
            else {"path", "before_commit", "after_commit"}
        )
        valid = isinstance(value, dict) and set(value) == required
        if valid:
            path = value["path"]
            valid = (
                _safe_repository_path(path)
                and all(
                    isinstance(value[key], str)
                    and GIT_RE.fullmatch(value[key]) is not None
                    for key in required - {"path"}
                )
            )
        if not valid:
            self.add(
                "RO017",
                "path",
                "repository identity contains an unsafe path or invalid commit",
                "use a slash-separated relative path and full lowercase Git commit",
                line=line,
                pointer="/repository",
                event=event,
            )

    def check_context(self, line: int, event: dict[str, Any]) -> None:
        value = event["context"]
        required = {"issue_or_topic", "step", "role", "selected_skill", "promise_id"}
        valid = isinstance(value, dict) and set(value) == required
        if valid:
            valid = all(
                _observed_string(value[key])
                for key in ("issue_or_topic", "step")
            ) and all(
                _safe_identity(value[key]) is not None
                for key in ("role", "selected_skill", "promise_id")
            )
        if not valid:
            self.add(
                "RO007",
                "shape",
                "run context is not a closed issue-or-topic, step, role, skill, and promise binding",
                "record the bounded work context selected before the run",
                line=line,
                pointer="/context",
                event=event,
            )

    def check_tokens(self, line: int, event: dict[str, Any]) -> None:
        value = event["token_usage"]
        required = {"source", "scope", "accounting_id"}
        allowed = required | {"input_tokens", "output_tokens"}
        valid = (
            isinstance(value, dict)
            and set(value).issubset(allowed)
            and required.issubset(value)
            and bool({"input_tokens", "output_tokens"} & set(value))
        )
        if valid:
            valid = all(_exposed_fact_string(value[name]) for name in required)
        if valid:
            for key in ("input_tokens", "output_tokens"):
                if key in value and not _json_integer(value[key], minimum=0):
                    valid = False
        if not valid:
            self.add(
                "RO016",
                "token",
                "token usage is not non-negative and source-bound",
                "omit unavailable counts or record exposed integer counts with source, scope, and accounting identity",
                line=line,
                pointer="/token_usage",
                event=event,
            )

    def check_evidence_list(self, line: int, event: dict[str, Any]) -> None:
        value = event["evidence"]
        if not isinstance(value, list) or not value:
            self.add(
                "RO007",
                "shape",
                "evidence is not a non-empty array",
                "omit evidence or add closed source-bound evidence definitions",
                line=line,
                pointer="/evidence",
                event=event,
            )
            return
        required = {"evidence_id", "subject", "scope", "time_domain", "evidence_class", "source"}
        allowed = required | {"selector", "digest"}
        for index, item in enumerate(value):
            valid = (
                isinstance(item, dict)
                and required.issubset(item)
                and set(item).issubset(allowed)
                and len({"selector", "digest"} & set(item)) == 1
                and all(_observed_string(item.get(key)) for key in required)
                and item.get("evidence_class") in EVIDENCE_CLASSES
            )
            if valid and "digest" in item:
                valid = (
                    isinstance(item["digest"], str)
                    and SHA256_RE.fullmatch(item["digest"]) is not None
                )
            if valid and "selector" in item:
                valid = _observed_string(item["selector"])
            if valid:
                valid = _safe_identity(item["evidence_id"]) is not None
            if not valid:
                self.add(
                    "RO007",
                    "shape",
                    "evidence definition is not closed, source-bound, or classed",
                    "name one id, subject, scope, time domain, class, source, and selector or digest",
                    line=line,
                    pointer=f"/evidence/{index}",
                    event=event,
                )

    def check_evidence_refs_shape(
        self, line: int, event: dict[str, Any], value: Any, pointer: str
    ) -> None:
        required = {"evidence_id", "subject", "scope", "time_domain", "evidence_class"}
        if not isinstance(value, list):
            self.add(
                "RO007",
                "shape",
                "evidence_refs is not an array",
                "record closed references to earlier evidence",
                line=line,
                pointer=pointer,
                event=event,
            )
            return
        for index, item in enumerate(value):
            if (
                not isinstance(item, dict)
                or set(item) != required
                or not all(_observed_string(item.get(key)) for key in required)
                or item.get("evidence_class") not in EVIDENCE_CLASSES
                or _safe_identity(item.get("evidence_id")) is None
            ):
                self.add(
                    "RO007",
                    "shape",
                    "evidence reference is not a closed exact binding",
                    "repeat the earlier evidence id, subject, scope, time domain, and class exactly",
                    line=line,
                    pointer=f"{pointer}/{index}",
                    event=event,
                )

    def relations(self, *, allow_prefix: bool = False) -> None:
        seen_events: dict[str, tuple[int, dict[str, Any]]] = {}
        evidence: dict[str, tuple[int, dict[str, Any]]] = {}
        capabilities: dict[str, tuple[int, dict[str, Any]]] = {}
        finished_capabilities: set[str] = set()
        run_id: str | None = None
        started: tuple[int, dict[str, Any]] | None = None
        finished: tuple[int, dict[str, Any]] | None = None
        refusal_events: list[dict[str, Any]] = []
        handoff_events: list[dict[str, Any]] = []
        for expected_sequence, (line, event) in enumerate(self.events, start=1):
            self.shape(line, event)
            event_id = event.get("event_id")
            current_run = event.get("run_id")
            if run_id is None and isinstance(current_run, str):
                run_id = current_run
            elif current_run != run_id:
                self.add(
                    "RO008",
                    "identity",
                    "event run_id differs from the record run",
                    "use one exact run identity throughout the file",
                    line=line,
                    pointer="/run_id",
                    event=event,
                )
            if event.get("sequence") != expected_sequence:
                self.add(
                    "RO009",
                    "order",
                    "sequence does not match contiguous file order",
                    "number events contiguously from one in file order",
                    line=line,
                    pointer="/sequence",
                    event=event,
                )
            self.backward_event_refs(line, event, seen_events)
            if isinstance(event_id, str):
                if event_id in seen_events:
                    self.add(
                        "RO008",
                        "identity",
                        "event_id is repeated",
                        "mint a unique event identity within the run",
                        line=line,
                        pointer="/event_id",
                        event=event,
                    )
                else:
                    seen_events[event_id] = (line, event)
            event_type = event.get("type")
            if finished is not None:
                self.add(
                    "RO009",
                    "lifecycle",
                    "event appears after run.finished",
                    "remove trailing events or start a distinct run record",
                    line=line,
                    event=event,
                )
            if event_type == "run.started":
                if started is not None or expected_sequence != 1:
                    self.add(
                        "RO009",
                        "lifecycle",
                        "run.started is repeated or not first",
                        "place exactly one run.started event first",
                        line=line,
                        event=event,
                    )
                else:
                    started = (line, event)
            elif started is None:
                self.add(
                    "RO009",
                    "lifecycle",
                    "event appears before run.started",
                    "place exactly one run.started event first",
                    line=line,
                    event=event,
                )
            if event_type == "run.finished":
                if finished is not None:
                    self.add(
                        "RO009",
                        "lifecycle",
                        "run.finished is repeated",
                        "retain exactly one closing run.finished event",
                        line=line,
                        event=event,
                    )
                else:
                    finished = (line, event)
            elif event_type == "transition.refused":
                refusal_events.append(event)
            elif event_type == "handoff.recorded":
                handoff_events.append(event)
            if event_type == "capability.started":
                capability_id = event.get("capability_id")
                if isinstance(capability_id, str):
                    if capability_id in capabilities:
                        self.add(
                            "RO009",
                            "lifecycle",
                            "capability_id is already active or used",
                            "mint one capability identity per start and finish pair",
                            line=line,
                            event=event,
                        )
                    else:
                        capabilities[capability_id] = (line, event)
            if event_type == "capability.finished":
                capability_id = event.get("capability_id")
                start_ref = event.get("started_event_id")
                start = capabilities.get(capability_id) if isinstance(capability_id, str) else None
                if (
                    start is None
                    or start[1].get("event_id") != start_ref
                    or capability_id in finished_capabilities
                ):
                    self.add(
                        "RO009",
                        "lifecycle",
                        "capability finish does not close one matching earlier start",
                        "reference one unfinished matching capability start",
                        line=line,
                        event=event,
                    )
                elif isinstance(capability_id, str):
                    finished_capabilities.add(capability_id)
            self.evidence_relations(line, event, evidence)
            if "evidence" in event and isinstance(event["evidence"], list):
                for item in event["evidence"]:
                    if not isinstance(item, dict):
                        continue
                    evidence_id = item.get("evidence_id")
                    if isinstance(evidence_id, str):
                        if item.get("evidence_class") == "inferred":
                            selector = item.get("selector")
                            selected_event = (
                                seen_events.get(selector)
                                if isinstance(selector, str)
                                else None
                            )
                            if (
                                _safe_identity(selector) is None
                                or selected_event is None
                                or selected_event[0] >= line
                            ):
                                self.add(
                                    "RO010",
                                    "reference",
                                    "inferred evidence does not name a prior event selector",
                                    "name the deterministic rule in source and one earlier event id in selector",
                                    line=line,
                                    pointer="/evidence",
                                    event=event,
                                )
                        if evidence_id in evidence:
                            self.add(
                                "RO011",
                                "evidence",
                                "evidence_id is repeated",
                                "mint one evidence identity per definition",
                                line=line,
                                event=event,
                            )
                        else:
                            evidence[evidence_id] = (line, item)
            if event_type == "retry.scheduled":
                retry = event.get("retry_of")
                if isinstance(retry, dict):
                    if retry.get("run_id") != run_id:
                        self.add(
                            "RO010",
                            "reference",
                            "retry crosses the current run boundary",
                            "reference a failed or refused capability finish in this run",
                            line=line,
                            pointer="/retry_of/run_id",
                            event=event,
                        )
                    attempt = event.get("attempt")
                    if (
                        _json_integer(attempt, minimum=1)
                        and attempt < 2
                    ):
                        self.add(
                            "RO009",
                            "lifecycle",
                            "retry attempt does not advance beyond the first attempt",
                            "record a retry attempt of two or greater",
                            line=line,
                            pointer="/attempt",
                            event=event,
                        )
                    retry_event_id = retry.get("event_id")
                    target = (
                        seen_events.get(retry_event_id)
                        if isinstance(retry_event_id, str)
                        else None
                    )
                    target_status = target[1].get("status") if target is not None else None
                    if (
                        target is None
                        or target[1].get("type") != "capability.finished"
                        or not isinstance(target_status, str)
                        or target_status not in {"failed", "refused"}
                    ):
                        self.add(
                            "RO010",
                            "reference",
                            "retry does not reference an earlier failed or refused capability finish",
                            "reference one earlier failed or refused capability.finished event",
                            line=line,
                            pointer="/retry_of/event_id",
                            event=event,
                        )
            if event_type == "handoff.recorded":
                producer = event.get("producer")
                consumer = event.get("consumer")
                if (
                    isinstance(producer, str)
                    and isinstance(consumer, str)
                    and producer == consumer
                ):
                    self.add(
                        "RO008",
                        "identity",
                        "handoff producer and consumer are the same skill",
                        "name the distinct skill that receives the handoff",
                        line=line,
                        pointer="/consumer",
                        event=event,
                    )
                source_event_id = event.get("source_event_id")
                target = (
                    seen_events.get(source_event_id)
                    if isinstance(source_event_id, str)
                    else None
                )
                target_type = target[1].get("type") if target is not None else None
                if (
                    target is None
                    or not isinstance(target_type, str)
                    or target_type not in {"capability.finished", "transition.refused"}
                ):
                    self.add(
                        "RO010",
                        "reference",
                        "handoff source is not an earlier outcome or refusal",
                        "reference one earlier capability finish or transition refusal",
                        line=line,
                        pointer="/source_event_id",
                        event=event,
                    )
                elif isinstance(event.get("evidence_refs"), list):
                    source_ids: set[str] = set()
                    for key in ("evidence", "evidence_refs"):
                        group = target[1].get(key)
                        if isinstance(group, list):
                            source_ids.update(
                                item.get("evidence_id")
                                for item in group
                                if isinstance(item, dict)
                                and isinstance(item.get("evidence_id"), str)
                            )
                    referenced_ids = {
                        item.get("evidence_id")
                        for item in event["evidence_refs"]
                        if isinstance(item, dict)
                        and isinstance(item.get("evidence_id"), str)
                    }
                    if not referenced_ids.issubset(source_ids):
                        self.add(
                            "RO011",
                            "evidence",
                            "handoff evidence is not carried by its source event",
                            "reference evidence defined or consumed by the named source event",
                            line=line,
                            pointer="/evidence_refs",
                            event=event,
                        )
                if not event.get("evidence_refs"):
                    self.add(
                        "RO011",
                        "evidence",
                        "handoff carries no earlier evidence binding",
                        "bind at least one earlier evidence definition",
                        line=line,
                        pointer="/evidence_refs",
                        event=event,
                    )
            if event_type == "run.finished" and started is not None:
                if event.get("started_event_id") != started[1].get("event_id"):
                    self.add(
                        "RO009",
                        "lifecycle",
                        "run finish does not reference the opening event",
                        "reference the one run.started event",
                        line=line,
                        pointer="/started_event_id",
                        event=event,
                    )
                outcome = event.get("outcome")
                status = event.get("status")
                opening_repository = started[1].get("repository")
                closing_repository = event.get("repository")
                if ("repository" in started[1]) != ("repository" in event):
                    self.add(
                        "RO017",
                        "path",
                        "opening and closing repository identities are not paired",
                        "record both before and after repository identities, or omit both",
                        line=line,
                        pointer="/repository",
                        event=event,
                    )
                if isinstance(closing_repository, dict):
                    if (
                        not isinstance(opening_repository, dict)
                        or closing_repository.get("path") != opening_repository.get("path")
                        or closing_repository.get("before_commit")
                        != opening_repository.get("before_commit")
                    ):
                        self.add(
                            "RO017",
                            "path",
                            "closing repository identity does not preserve the opening path and commit",
                            "repeat the opening path and before_commit beside the observed after_commit",
                            line=line,
                            pointer="/repository",
                            event=event,
                        )
                if (
                    isinstance(status, str)
                    and status in {"success", "handoff"}
                    and isinstance(outcome, dict)
                    and not outcome.get("evidence_refs")
                ):
                    self.add(
                        "RO011",
                        "evidence",
                        "authorising run outcome carries no earlier evidence binding",
                        "bind at least one earlier evidence definition or record a non-authorising status",
                        line=line,
                        pointer="/outcome/evidence_refs",
                        event=event,
                    )
                if status == "refused" and not refusal_events:
                    self.add(
                        "RO009",
                        "lifecycle",
                        "refused run finish has no earlier transition refusal",
                        "record the observable transition.refused event before finishing the run",
                        line=line,
                        pointer="/status",
                        event=event,
                    )
                if status == "handoff" and not handoff_events:
                    self.add(
                        "RO009",
                        "lifecycle",
                        "handoff run finish has no earlier handoff event",
                        "record the observable handoff.recorded event before finishing the run",
                        line=line,
                        pointer="/status",
                        event=event,
                    )
                if status == "handoff" and isinstance(outcome, dict):
                    handed_off_ids: set[str] = set()
                    for handoff in handoff_events:
                        group = handoff.get("evidence_refs")
                        if isinstance(group, list):
                            handed_off_ids.update(
                                item.get("evidence_id")
                                for item in group
                                if isinstance(item, dict)
                                and isinstance(item.get("evidence_id"), str)
                            )
                    outcome_group = outcome.get("evidence_refs")
                    outcome_ids = (
                        {
                            item.get("evidence_id")
                            for item in outcome_group
                            if isinstance(item, dict)
                            and isinstance(item.get("evidence_id"), str)
                        }
                        if isinstance(outcome_group, list)
                        else set()
                    )
                    if not outcome_ids.issubset(handed_off_ids):
                        self.add(
                            "RO011",
                            "evidence",
                            "handoff outcome cites evidence absent from every earlier handoff",
                            "cite only evidence carried by an earlier handoff event",
                            line=line,
                            pointer="/outcome/evidence_refs",
                            event=event,
                        )
            if started is not None:
                context = started[1].get("context")
                if isinstance(context, dict):
                    if (
                        event_type == "transition.refused"
                        and event.get("promise_id") != context.get("promise_id")
                    ):
                        self.add(
                            "RO008",
                            "identity",
                            "refusal promise differs from the selected run promise",
                            "preserve the selected promise identity in the refusal",
                            line=line,
                            pointer="/promise_id",
                            event=event,
                        )
                    if (
                        event_type == "handoff.recorded"
                        and event.get("producer") != context.get("selected_skill")
                    ):
                        self.add(
                            "RO008",
                            "identity",
                            "handoff producer differs from the selected run skill",
                            "preserve the selected skill identity as the handoff producer",
                            line=line,
                            pointer="/producer",
                            event=event,
                        )
        if started is None:
            self.add(
                "RO009",
                "lifecycle",
                "record has no run.started event",
                "place exactly one run.started event first",
            )
        if finished is None and not allow_prefix:
            self.add(
                "RO009",
                "lifecycle",
                "record has no run.finished event",
                "place exactly one run.finished event last",
            )
        for capability_id, (line, event) in capabilities.items():
            if capability_id not in finished_capabilities:
                self.add(
                    "RO009",
                    "lifecycle",
                    "capability start has no matching finish",
                    "close every capability before run.finished",
                    line=line,
                    event=event,
                )

    def backward_event_refs(
        self,
        line: int,
        event: dict[str, Any],
        seen: dict[str, tuple[int, dict[str, Any]]],
    ) -> None:
        for key in ("parent_event_id", "started_event_id", "source_event_id", "caused_by"):
            if key in event and (
                not isinstance(event[key], str) or event[key] not in seen
            ):
                self.add(
                    "RO010",
                    "reference",
                    f"{key} does not resolve backward within this run",
                    "reference one earlier event id in the same record",
                    line=line,
                    pointer=f"/{key}",
                    event=event,
                )

    def evidence_relations(
        self,
        line: int,
        event: dict[str, Any],
        evidence: dict[str, tuple[int, dict[str, Any]]],
    ) -> None:
        groups: list[Any] = []
        if "evidence_refs" in event:
            groups.append(event["evidence_refs"])
        outcome = event.get("outcome")
        if isinstance(outcome, dict) and "evidence_refs" in outcome:
            groups.append(outcome["evidence_refs"])
        for group in groups:
            if not isinstance(group, list):
                continue
            for ref in group:
                if not isinstance(ref, dict):
                    continue
                evidence_id = ref.get("evidence_id")
                source = evidence.get(evidence_id) if isinstance(evidence_id, str) else None
                if source is None:
                    self.add(
                        "RO011",
                        "evidence",
                        "evidence reference is unbound",
                        "reference one earlier evidence definition in this run",
                        line=line,
                        event=event,
                    )
                    continue
                definition = source[1]
                fields = ("subject", "scope", "time_domain", "evidence_class")
                if any(ref.get(key) != definition.get(key) for key in fields):
                    self.add(
                        "RO012",
                        "evidence",
                        "evidence subject, scope, time domain, or class was strengthened or changed",
                        "repeat the earlier evidence binding exactly or add separately identified evidence",
                        line=line,
                        event=event,
                    )
                    continue
                if event.get("type") == "handoff.recorded" and any(
                    event.get(key) != definition.get(key)
                    for key in ("subject", "scope", "time_domain")
                ):
                    self.add(
                        "RO012",
                        "evidence",
                        "handoff subject, scope, or time domain differs from its evidence",
                        "preserve the evidence binding exactly across the handoff",
                        line=line,
                        event=event,
                    )
                outcome = event.get("outcome")
                if (
                    event.get("type") == "run.finished"
                    and isinstance(outcome, dict)
                    and outcome.get("subject") != definition.get("subject")
                ):
                    self.add(
                        "RO012",
                        "evidence",
                        "outcome subject differs from its evidence",
                        "preserve the evidence subject exactly in the observed outcome",
                        line=line,
                        pointer="/outcome/subject",
                        event=event,
                    )

    def result(self) -> list[Finding]:
        unique = {finding: None for finding in self.findings}
        return sorted(
            unique,
            key=lambda item: (
                item.line if item.line is not None else 0,
                item.code,
                item.path,
                item.message,
            ),
        )


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def display_path(path: Path, root: Path) -> str:
    try:
        relative = os.path.relpath(path, root)
    except ValueError:
        relative = str(path)
    relative = relative.replace(os.sep, "/")
    escaped = json.dumps(relative, ensure_ascii=True)[1:-1]
    if len(escaped) <= MAX_DISPLAY_PATH:
        return escaped
    digest = hashlib.sha256(relative.encode("utf-8", errors="surrogatepass")).hexdigest()
    suffix = f"...[sha256={digest}]"
    return escaped[: MAX_DISPLAY_PATH - len(suffix)] + suffix


def validate_path(
    path: Path,
    *,
    root: Path | None = None,
    allow_prefix: bool = False,
) -> list[Finding]:
    root = repository_root() if root is None else root
    display = display_path(path, root)
    validator = Validator(display)
    validator.read(path, root)
    if validator.events:
        validator.relations(allow_prefix=allow_prefix)
    elif not validator.findings:
        validator.add(
            "RO009",
            "lifecycle",
            "record contains no events",
            "write one run.started and one run.finished event",
        )
    if not validator.findings:
        validator.finalise_input(path, root)
    return validator.result()


def validate_bytes(
    data: bytes,
    *,
    display_path: str = "captured-observation.jsonl",
    allow_prefix: bool = False,
) -> list[Finding]:
    """Validate the exact immutable bytes already admitted by a caller."""
    validator = Validator(display_path)
    validator.read_captured(data)
    if validator.events:
        validator.relations(allow_prefix=allow_prefix)
    elif not validator.findings:
        validator.add(
            "RO009",
            "lifecycle",
            "record contains no events",
            "write one run.started and one run.finished event",
        )
    return validator.result()


def finding_objects(findings: list[Finding]) -> list[dict[str, Any]]:
    return [{key: value for key, value in asdict(item).items() if value is not None} for item in findings]


def text_lines(findings: list[Finding]) -> list[str]:
    lines = []
    for finding in findings:
        location = finding.path
        if finding.line is not None:
            location += f":{finding.line}"
        context = [f"contract={CONTRACT_ID}"]
        if finding.run_id is not None:
            context.append(f"run={finding.run_id}")
        if finding.event_id is not None:
            context.append(f"event={finding.event_id}")
        if finding.correlation_id is not None:
            context.append(f"correlation={finding.correlation_id}")
        suffix = f" [{' '.join(context)}]" if context else ""
        lines.append(
            f"{finding.code} {finding.fault} {location}{suffix}: "
            f"{finding.message}; recovery: {finding.recovery}"
        )
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check one bounded promise-machine-run-observation/v1 JSONL record or prefix."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="validate one confined JSONL record")
    check.add_argument("path")
    check.add_argument("--json", action="store_true", help="emit canonical JSON")
    prefix = subparsers.add_parser(
        "check-prefix",
        help="validate one confined JSONL prefix without requiring run.finished",
    )
    prefix.add_argument("path")
    prefix.add_argument("--json", action="store_true", help="emit canonical JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.path)
    findings = validate_path(path, allow_prefix=args.command == "check-prefix")
    if args.json:
        report = {
            "contract": CONTRACT_ID,
            "findings": finding_objects(findings),
            "ok": not findings,
            "path": display_path(path, repository_root()),
        }
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    elif findings:
        for line in text_lines(findings):
            print(line)
    else:
        print(f"clean: {display_path(path, repository_root())} satisfies {CONTRACT_ID}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
