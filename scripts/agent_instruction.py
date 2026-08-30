#!/usr/bin/env python3
"""Bounded canonical model and compact codec for agent instructions v1."""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Mapping, Sequence
import copy
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
from typing import Any, NoReturn


SCHEMA_ID = "wildcat-agent-instruction/v1"
MAGIC = "WAI1"
CONTRACT_PATH = "docs/agent-instruction-language-v1.md"
SCHEMA_PATH = "schemas/agent-instruction-v1.schema.json"
RESULT_SCHEMA = "wildcat-agent-instruction-result/v1"
CHECK_RECORD_SCHEMA = "wildcat-agent-instruction-check-record/v1"
MANIFEST_ID = "wildcat-agent-instruction-manifest/v1"
MANIFEST_SCHEMA_ID = "https://wildcat.finance/schemas/agent-instruction-manifest-v1.schema.json"
MANIFEST_SCHEMA_PATH = "tests/fixtures/agent-instruction-v1/manifest.schema.json"
MANIFEST_SCHEMA_SHA256 = "1bedb95cc1a7b1a179371b2ceee528f5930ef1861346059b6a178ee86efc15d2"
FIXTURE_ROOT = "tests/fixtures/agent-instruction-v1"
FIXTURE_IDS = (
    "fiat-study-runbook-phase",
    "horos-boundary-check",
    "promise-machine-router-selection",
)
FIXTURE_REVIEWER = "shoggoth"
FIXTURE_CONTRACT = {
    "fiat-study-runbook-phase": {
        "source_id": "fiat",
        "source_path": "plugins/hexaemeron/skills/fiat/SKILL.md",
        "binding_count": 7,
        "question_count": 3,
        "mutation_count": 4,
    },
    "horos-boundary-check": {
        "source_id": "horos",
        "source_path": "plugins/horos/skills/horos/SKILL.md",
        "binding_count": 4,
        "question_count": 3,
        "mutation_count": 4,
    },
    "promise-machine-router-selection": {
        "source_id": "promise-machine",
        "source_path": "PROMISE_MACHINE.md",
        "binding_count": 4,
        "question_count": 3,
        "mutation_count": 6,
    },
}
FIXTURE_BINDING_COUNT = sum(item["binding_count"] for item in FIXTURE_CONTRACT.values())
FIXTURE_QUESTION_COUNT = sum(item["question_count"] for item in FIXTURE_CONTRACT.values())
FIXTURE_MUTATION_COUNT = sum(item["mutation_count"] for item in FIXTURE_CONTRACT.values())
FIXTURE_ARTIFACTS = {
    "compact": "compact.wai",
    "model": "model.json",
    "mutations": "mutations.json",
    "questions": "questions.json",
    "source_spans": "source-spans.json",
}
RISK_CLASSES = (
    "negation",
    "precedence",
    "scope",
    "evidence-class",
    "authorisation",
    "recovery",
    "exact-literal",
)
REQUIRED_LITERAL_MUTATION_CLASSES = (
    "identifier",
    "path",
    "sha256",
    "command",
    "number",
    "text",
)
MAX_FIXTURE_FILES = 5
MAX_QUESTIONS = 64
MAX_MUTATIONS = 128
MAX_RECORD_DEPTH = 24
MAX_RECORD_ARRAY = 256

MAX_FILE_BYTES = 1_048_576
MAX_LINES = 16_384
MAX_LINE_BYTES = 65_536
MAX_DEPTH = 32
MAX_OBJECT_MEMBERS = 32
MAX_ID_BYTES = 128
MAX_PATH_BYTES = 512
MAX_LITERAL_BYTES = 65_000
MAX_TOTAL_LITERAL_BYTES = 786_432
MAX_SOURCES = 64
MAX_SECTIONS = 128
MAX_DIRECTIVES = 4_096
MAX_EXPRESSIONS = 8_192
MAX_RELATIONS = 8_192
MAX_BINDINGS = 8_192
MAX_PROMISE_EXCEPTIONS = 1_024

ID_RE = re.compile(r"[a-z][a-z0-9.-]*\Z", re.ASCII)
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
DECIMAL_RE = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
LITERAL_KINDS = (
    "identifier",
    "path",
    "sha256",
    "command",
    "number",
    "date",
    "link",
    "quotation",
    "text",
)
LITERAL_TAGS = {
    "identifier": "i",
    "path": "p",
    "sha256": "h",
    "command": "c",
    "number": "n",
    "date": "d",
    "link": "u",
    "quotation": "q",
    "text": "t",
}
TAG_KINDS = {tag: kind for kind, tag in LITERAL_TAGS.items()}
DIRECTIVE_OPCODES = {
    "require": "R",
    "forbid": "F",
    "permit": "P",
    "refuse": "X",
    "recover": "Y",
    "unknown": "U",
}
OPCODE_DIRECTIVES = {opcode: kind for kind, opcode in DIRECTIVE_OPCODES.items()}
EXPRESSION_OPCODES = {"when": "W", "unless": "N", "scope": "C", "exception": "E"}
OPCODE_EXPRESSIONS = {opcode: kind for kind, opcode in EXPRESSION_OPCODES.items()}
RELATION_OPCODES = {"before": "<", "after": ">", "overrides": "^"}
OPCODE_RELATIONS = {opcode: kind for kind, opcode in RELATION_OPCODES.items()}
EVIDENCE_CLASSES = (
    "checked",
    "recomputed",
    "proved",
    "measured",
    "recorded",
    "attested",
    "inferred",
    "unknown",
)


class CodecError(ValueError):
    """A bounded refusal carrying a stable code and model-node path."""

    def __init__(self, code: str, node_path: str = "$") -> None:
        super().__init__(code)
        self.code = code
        self.node_path = node_path[:512]


def refuse(code: str, path: str = "$") -> NoReturn:
    raise CodecError(code, path)


def _scalar(value: str, path: str) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        refuse("WAI-E-UTF8.SCALAR", path)


def _object(value: Any, required: Sequence[str], path: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        refuse("WAI-E-SHAPE.OBJECT", path)
    if len(value) > MAX_OBJECT_MEMBERS:
        refuse("WAI-E-BOUNDS.MEMBERS", path)
    expected = set(required)
    if set(value) != expected:
        refuse("WAI-E-SHAPE.FIELDS", path)
    return value


def _array(value: Any, path: str, maximum: int, *, minimum: int = 0) -> list[Any]:
    if not isinstance(value, list):
        refuse("WAI-E-SHAPE.ARRAY", path)
    if not minimum <= len(value) <= maximum:
        refuse("WAI-E-BOUNDS.COUNT", path)
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str):
        refuse("WAI-E-SHAPE.STRING", path)
    _scalar(value, path)
    return value


def _identifier(value: Any, path: str) -> str:
    text = _string(value, path)
    if len(text.encode("utf-8")) > MAX_ID_BYTES:
        refuse("WAI-E-BOUNDS.IDENTIFIER", path)
    if ID_RE.fullmatch(text) is None:
        refuse("WAI-E-SHAPE.IDENTIFIER", path)
    return text


def _decimal(value: Any, path: str) -> str:
    text = _string(value, path)
    if DECIMAL_RE.fullmatch(text) is None:
        refuse("WAI-E-SHAPE.DECIMAL", path)
    return text


def _decimal_key(text: str) -> tuple[int, str]:
    """Return the numeric order of a canonical, non-negative decimal string."""

    return len(text), text


def _safe_relative_path(value: Any, path: str) -> str:
    text = _string(value, path)
    try:
        raw = text.encode("ascii")
    except UnicodeEncodeError:
        refuse("WAI-E-PATH.ASCII", path)
    if not raw or len(raw) > MAX_PATH_BYTES:
        refuse("WAI-E-BOUNDS.PATH", path)
    if text.startswith("/") or "\\" in text:
        refuse("WAI-E-PATH.UNSAFE", path)
    components = text.split("/")
    if any(part in ("", ".", "..") for part in components):
        refuse("WAI-E-PATH.UNSAFE", path)
    if any(ord(character) <= 0x20 or ord(character) == 0x7F for character in text):
        refuse("WAI-E-PATH.UNSAFE", path)
    return text


class ValidationState:
    def __init__(self) -> None:
        self.ids: set[str] = set()
        self.sources: set[str] = set()
        self.directives: set[str] = set()
        self.governed: set[str] = set()
        self.parents: dict[str, str] = {}
        self.total_literal_bytes = 0
        self.directive_count = 0
        self.expression_count = 0
        self.promise_exception_count = 0

    def compact_literal(self, text: str, path: str) -> None:
        """Count one value that the compact form carries as a literal field."""

        _scalar(text, path)
        size = len(text.encode("utf-8"))
        if size > MAX_LITERAL_BYTES:
            refuse("WAI-E-BOUNDS.LITERAL", path)
        self.total_literal_bytes += size
        if self.total_literal_bytes > MAX_TOTAL_LITERAL_BYTES:
            refuse("WAI-E-BOUNDS.LITERALS", path)

    def declare(self, value: Any, path: str, *, governed: bool = False, parent: str | None = None) -> str:
        identifier = _identifier(value, path)
        if identifier in self.ids:
            refuse("WAI-E-REFERENCE.DUPLICATE_ID", path)
        self.compact_literal(identifier, path)
        self.ids.add(identifier)
        if governed:
            self.governed.add(identifier)
        if parent is not None:
            self.parents[identifier] = parent
        return identifier

    def literal(self, value: Any, path: str, expected: str | None = None) -> dict[str, str]:
        item = _object(value, ("kind", "value"), path)
        kind = _string(item["kind"], f"{path}.kind")
        if kind not in LITERAL_KINDS or (expected is not None and kind != expected):
            refuse("WAI-E-SHAPE.LITERAL_KIND", f"{path}.kind")
        text = _string(item["value"], f"{path}.value")
        size = len(text.encode("utf-8"))
        if size > MAX_LITERAL_BYTES:
            refuse("WAI-E-BOUNDS.LITERAL", f"{path}.value")
        self.compact_literal(text, path)
        if kind == "identifier":
            _identifier(text, f"{path}.value")
        elif kind == "path":
            _safe_relative_path(text, f"{path}.value")
        elif kind == "sha256" and SHA256_RE.fullmatch(text) is None:
            refuse("WAI-E-SHAPE.SHA256", f"{path}.value")
        elif kind == "number":
            _decimal(text, f"{path}.value")
        elif kind == "date":
            try:
                parsed = date.fromisoformat(text)
            except ValueError:
                refuse("WAI-E-SHAPE.DATE", f"{path}.value")
            if parsed.isoformat() != text:
                refuse("WAI-E-SHAPE.DATE", f"{path}.value")
        return {"kind": kind, "value": text}


def _expression(
    value: Any,
    path: str,
    state: ValidationState,
    directive_id: str,
    ancestor_scopes: tuple[str, ...],
    depth: int,
) -> None:
    if depth > MAX_DEPTH:
        refuse("WAI-E-BOUNDS.DEPTH", path)
    state.expression_count += 1
    if state.expression_count > MAX_EXPRESSIONS:
        refuse("WAI-E-BOUNDS.EXPRESSIONS", path)
    if not isinstance(value, dict):
        refuse("WAI-E-SHAPE.OBJECT", path)
    kind = value.get("kind")
    if kind in ("when", "unless"):
        item = _object(value, ("kind", "predicate", "expressions"), path)
        state.literal(item["predicate"], f"{path}.predicate")
        scopes = ancestor_scopes
    elif kind == "scope":
        item = _object(value, ("kind", "scope", "expressions"), path)
        parent = ancestor_scopes[-1] if ancestor_scopes else directive_id
        scope_id = state.declare(item["scope"], f"{path}.scope", governed=True, parent=parent)
        scopes = ancestor_scopes + (scope_id,)
    elif kind == "exception":
        item = _object(value, ("kind", "target", "predicate", "expressions"), path)
        target = _identifier(item["target"], f"{path}.target")
        state.compact_literal(target, f"{path}.target")
        if target != directive_id and target not in ancestor_scopes:
            refuse("WAI-E-REFERENCE.EXCEPTION_TARGET", f"{path}.target")
        state.literal(item["predicate"], f"{path}.predicate")
        scopes = ancestor_scopes
    else:
        refuse("WAI-E-SHAPE.EXPRESSION_KIND", f"{path}.kind")
    children = _array(item["expressions"], f"{path}.expressions", MAX_EXPRESSIONS)
    for index, child in enumerate(children):
        _expression(child, f"{path}.expressions[{index}]", state, directive_id, scopes, depth + 1)


def _promise(value: Any, path: str, state: ValidationState, directive_id: str) -> None:
    item = _object(
        value,
        (
            "id",
            "claim",
            "evidence",
            "evidence_classes",
            "boundary",
            "authorises",
            "consequence",
            "refuses",
            "recovery",
            "exceptions",
        ),
        path,
    )
    promise_id = state.declare(item["id"], f"{path}.id", governed=True, parent=directive_id)
    state.literal(item["claim"], f"{path}.claim")
    for field in ("evidence", "authorises", "refuses", "recovery"):
        values = _array(item[field], f"{path}.{field}", MAX_EXPRESSIONS, minimum=1)
        for index, literal in enumerate(values):
            state.literal(literal, f"{path}.{field}[{index}]")
    classes = _array(item["evidence_classes"], f"{path}.evidence_classes", len(EVIDENCE_CLASSES), minimum=1)
    parsed_classes = [_string(entry, f"{path}.evidence_classes[{index}]") for index, entry in enumerate(classes)]
    if any(entry not in EVIDENCE_CLASSES for entry in parsed_classes):
        refuse("WAI-E-SHAPE.EVIDENCE_CLASS", f"{path}.evidence_classes")
    canonical_classes = [entry for entry in EVIDENCE_CLASSES if entry in parsed_classes]
    if parsed_classes != canonical_classes:
        refuse("WAI-E-CANONICAL.EVIDENCE_CLASSES", f"{path}.evidence_classes")
    state.literal(item["boundary"], f"{path}.boundary")
    consequence = _string(item["consequence"], f"{path}.consequence")
    if consequence not in ("0", "1", "2", "3"):
        refuse("WAI-E-SHAPE.CONSEQUENCE", f"{path}.consequence")
    exceptions = _array(item["exceptions"], f"{path}.exceptions", MAX_PROMISE_EXCEPTIONS)
    state.promise_exception_count += len(exceptions)
    if state.promise_exception_count > MAX_PROMISE_EXCEPTIONS:
        refuse("WAI-E-BOUNDS.PROMISE_EXCEPTIONS", f"{path}.exceptions")
    for index, raw_exception in enumerate(exceptions):
        exception_path = f"{path}.exceptions[{index}]"
        exception = _object(
            raw_exception,
            ("id", "authority", "gate", "subject", "scope", "record", "expiry", "recovery"),
            exception_path,
        )
        state.declare(exception["id"], f"{exception_path}.id", governed=True, parent=promise_id)
        for field in ("authority", "gate", "subject", "scope", "record", "expiry", "recovery"):
            state.literal(exception[field], f"{exception_path}.{field}")


def _is_ancestor(ancestor: str, descendant: str, parents: Mapping[str, str]) -> bool:
    cursor = descendant
    seen: set[str] = set()
    while cursor in parents and cursor not in seen:
        seen.add(cursor)
        cursor = parents[cursor]
        if cursor == ancestor:
            return True
    return False


def _check_precedence(relations: Sequence[Mapping[str, Any]], directives: set[str]) -> None:
    edges: dict[str, set[str]] = {identifier: set() for identifier in directives}
    for relation in relations:
        source = relation["source"]
        target = relation["target"]
        if relation["kind"] == "after":
            source, target = target, source
        edges[source].add(target)
    indegree = {identifier: 0 for identifier in directives}
    for targets in edges.values():
        for target in targets:
            indegree[target] += 1
    ready = [identifier for identifier in sorted(indegree, reverse=True) if indegree[identifier] == 0]
    visited = 0
    while ready:
        node = ready.pop()
        visited += 1
        for target in sorted(edges[node], reverse=True):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    if visited != len(directives):
        refuse("WAI-E-CYCLE.PRECEDENCE", "$.relations")


def validate_model(model: Any) -> dict[str, Any]:
    """Validate the closed v1 model and return it unchanged on success."""

    root = _object(model, ("schema", "document", "sources", "sections", "relations", "bindings"), "$")
    if _string(root["schema"], "$.schema") != SCHEMA_ID:
        refuse("WAI-E-VERSION.SCHEMA", "$.schema")
    state = ValidationState()
    document = _object(root["document"], ("id", "title"), "$.document")
    document_id = state.declare(document["id"], "$.document.id", governed=True)
    state.literal(document["title"], "$.document.title")

    sources = _array(root["sources"], "$.sources", MAX_SOURCES, minimum=1)
    source_ids: list[str] = []
    source_paths: set[str] = set()
    for index, raw_source in enumerate(sources):
        path = f"$.sources[{index}]"
        source = _object(raw_source, ("id", "path", "sha256"), path)
        source_id = state.declare(source["id"], f"{path}.id")
        state.sources.add(source_id)
        source_ids.append(source_id)
        source_path = _safe_relative_path(source["path"], f"{path}.path")
        if source_path in source_paths:
            refuse("WAI-E-REFERENCE.DUPLICATE_SOURCE_PATH", f"{path}.path")
        source_paths.add(source_path)
        state.compact_literal(source_path, f"{path}.path")
        digest = _string(source["sha256"], f"{path}.sha256")
        if SHA256_RE.fullmatch(digest) is None:
            refuse("WAI-E-SHAPE.SHA256", f"{path}.sha256")
        state.compact_literal(digest, f"{path}.sha256")
    if source_ids != sorted(source_ids):
        refuse("WAI-E-CANONICAL.SOURCES", "$.sources")

    sections = _array(root["sections"], "$.sections", MAX_SECTIONS, minimum=1)
    for section_index, raw_section in enumerate(sections):
        section_path = f"$.sections[{section_index}]"
        section = _object(raw_section, ("id", "title", "directives"), section_path)
        section_id = state.declare(section["id"], f"{section_path}.id", governed=True, parent=document_id)
        state.literal(section["title"], f"{section_path}.title")
        directives = _array(section["directives"], f"{section_path}.directives", MAX_DIRECTIVES, minimum=1)
        state.directive_count += len(directives)
        if state.directive_count > MAX_DIRECTIVES:
            refuse("WAI-E-BOUNDS.DIRECTIVES", f"{section_path}.directives")
        for directive_index, raw_directive in enumerate(directives):
            directive_path = f"{section_path}.directives[{directive_index}]"
            directive = _object(raw_directive, ("id", "kind", "statement", "expressions", "promise"), directive_path)
            directive_id = state.declare(
                directive["id"], f"{directive_path}.id", governed=True, parent=section_id
            )
            state.directives.add(directive_id)
            kind = _string(directive["kind"], f"{directive_path}.kind")
            if kind not in DIRECTIVE_OPCODES:
                refuse("WAI-E-SHAPE.DIRECTIVE_KIND", f"{directive_path}.kind")
            state.literal(directive["statement"], f"{directive_path}.statement")
            expressions = _array(directive["expressions"], f"{directive_path}.expressions", MAX_EXPRESSIONS)
            for expression_index, expression in enumerate(expressions):
                _expression(
                    expression,
                    f"{directive_path}.expressions[{expression_index}]",
                    state,
                    directive_id,
                    (),
                    3,
                )
            if directive["promise"] is not None:
                _promise(directive["promise"], f"{directive_path}.promise", state, directive_id)

    relations = _array(root["relations"], "$.relations", MAX_RELATIONS)
    relation_keys: list[tuple[str, str, str]] = []
    for index, raw_relation in enumerate(relations):
        path = f"$.relations[{index}]"
        relation = _object(raw_relation, ("kind", "source", "target"), path)
        kind = _string(relation["kind"], f"{path}.kind")
        if kind not in RELATION_OPCODES:
            refuse("WAI-E-SHAPE.RELATION_KIND", f"{path}.kind")
        source = _identifier(relation["source"], f"{path}.source")
        target = _identifier(relation["target"], f"{path}.target")
        state.compact_literal(source, f"{path}.source")
        state.compact_literal(target, f"{path}.target")
        if source not in state.directives or target not in state.directives:
            refuse("WAI-E-REFERENCE.RELATION", path)
        if source == target:
            refuse("WAI-E-REFERENCE.SELF_RELATION", path)
        relation_keys.append((kind, source, target))
    if len(set(relation_keys)) != len(relation_keys):
        refuse("WAI-E-REFERENCE.DUPLICATE_RELATION", "$.relations")
    if relation_keys != sorted(relation_keys):
        refuse("WAI-E-CANONICAL.RELATIONS", "$.relations")
    _check_precedence(relations, state.directives)

    bindings = _array(root["bindings"], "$.bindings", MAX_BINDINGS, minimum=1)
    binding_keys: list[tuple[str, tuple[int, str], tuple[int, str], str, str]] = []
    intervals: dict[str, list[tuple[tuple[int, str], tuple[int, str], str, str]]] = defaultdict(list)
    covered: set[str] = set()
    for index, raw_binding in enumerate(bindings):
        path = f"$.bindings[{index}]"
        binding = _object(raw_binding, ("source", "node", "start", "end", "reviewer"), path)
        source = _identifier(binding["source"], f"{path}.source")
        node = _identifier(binding["node"], f"{path}.node")
        state.compact_literal(source, f"{path}.source")
        state.compact_literal(node, f"{path}.node")
        if source not in state.sources or node not in state.governed:
            refuse("WAI-E-REFERENCE.BINDING", path)
        start_text = _decimal(binding["start"], f"{path}.start")
        end_text = _decimal(binding["end"], f"{path}.end")
        state.compact_literal(start_text, f"{path}.start")
        state.compact_literal(end_text, f"{path}.end")
        start, end = _decimal_key(start_text), _decimal_key(end_text)
        if end <= start:
            refuse("WAI-E-REFERENCE.SPAN", path)
        reviewer = state.literal(binding["reviewer"], f"{path}.reviewer", "identifier")["value"]
        key = (source, start, end, node, reviewer)
        binding_keys.append(key)
        intervals[source].append((start, end, node, path))
        covered.add(node)
    if len(set(binding_keys)) != len(binding_keys):
        refuse("WAI-E-REFERENCE.DUPLICATE_BINDING", "$.bindings")
    if binding_keys != sorted(binding_keys):
        refuse("WAI-E-CANONICAL.BINDINGS", "$.bindings")
    missing = state.governed - covered
    if missing:
        refuse("WAI-E-REFERENCE.UNCOVERED", "$.bindings")
    for source_intervals in intervals.values():
        by_node: dict[str, list[tuple[tuple[int, str], tuple[int, str], str]]] = defaultdict(list)
        for start, end, node, path in source_intervals:
            by_node[node].append((start, end, path))
        nodes = sorted(by_node)
        for left_index, left_node in enumerate(nodes):
            for right_node in nodes[left_index + 1 :]:
                left_ancestor = _is_ancestor(left_node, right_node, state.parents)
                right_ancestor = _is_ancestor(right_node, left_node, state.parents)
                for left_start, left_end, left_path in by_node[left_node]:
                    for right_start, right_end, _ in by_node[right_node]:
                        if max(left_start, right_start) >= min(left_end, right_end):
                            continue
                        nested = (
                            left_ancestor and left_start <= right_start and right_end <= left_end
                        ) or (
                            right_ancestor and right_start <= left_start and left_end <= right_end
                        )
                        if not nested:
                            refuse("WAI-E-REFERENCE.OVERLAP", left_path)
    return model


def canonical_json_bytes(model: Any) -> bytes:
    validate_model(model)
    output = (
        json.dumps(model, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    if len(output) > MAX_FILE_BYTES:
        refuse("WAI-E-BOUNDS.FILE", "$")
    return output


def _duplicate_checked_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            refuse("WAI-E-JSON.DUPLICATE_KEY", "$")
        value[key] = item
    return value


def _forbidden_number(_: str) -> NoReturn:
    refuse("WAI-E-JSON.NUMBER", "$")


def _bounded_record_integer(text: str) -> int:
    if text.startswith("-") or len(text) > len(str(MAX_FILE_BYTES)):
        refuse("WAI-E-BOUNDS.NUMBER", "$")
    number = int(text)
    if number > MAX_FILE_BYTES:
        refuse("WAI-E-BOUNDS.NUMBER", "$")
    return number


def load_canonical_json(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_FILE_BYTES:
        refuse("WAI-E-BOUNDS.FILE", "$")
    if data.startswith(b"\xef\xbb\xbf"):
        refuse("WAI-E-UTF8.BOM", "$")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        refuse("WAI-E-UTF8.DECODE", "$")
    _scalar(text, "$")
    try:
        model = json.loads(
            text,
            object_pairs_hook=_duplicate_checked_object,
            parse_int=_forbidden_number,
            parse_float=_forbidden_number,
            parse_constant=_forbidden_number,
        )
    except CodecError:
        raise
    except (json.JSONDecodeError, RecursionError):
        refuse("WAI-E-JSON.SYNTAX", "$")
    if not isinstance(model, dict):
        refuse("WAI-E-SHAPE.OBJECT", "$")
    canonical = canonical_json_bytes(model)
    if data != canonical:
        refuse("WAI-E-CANONICAL.JSON", "$")
    return model


def encode_literal(literal: Mapping[str, str]) -> str:
    kind = literal["kind"]
    value = literal["value"]
    tag = LITERAL_TAGS[kind]
    escaped: list[str] = []
    for character in value:
        code = ord(character)
        if character == "\\":
            escaped.append("\\\\")
        elif character == " ":
            escaped.append("\\s")
        elif character == ":":
            escaped.append("\\:")
        elif character == "\t":
            escaped.append("\\t")
        elif character == "\n":
            escaped.append("\\n")
        elif character == "\r":
            escaped.append("\\r")
        elif code < 0x20 or code == 0x7F:
            escaped.append(f"\\x{code:02X}")
        else:
            escaped.append(character)
    return f"{tag}{len(value.encode('utf-8'))}:{''.join(escaped)}"


def decode_literal(token: str, expected: str | None = None, path: str = "$") -> dict[str, str]:
    if len(token) < 3 or token[0] not in TAG_KINDS:
        refuse("WAI-E-COMPACT.LITERAL", path)
    colon = token.find(":", 1)
    if colon < 2:
        refuse("WAI-E-COMPACT.LITERAL", path)
    count_text = token[1:colon]
    if DECIMAL_RE.fullmatch(count_text) is None:
        refuse("WAI-E-COMPACT.LENGTH", path)
    if _decimal_key(count_text) > _decimal_key(str(MAX_LITERAL_BYTES)):
        refuse("WAI-E-BOUNDS.LITERAL", path)
    expected_bytes = int(count_text)
    data = token[colon + 1 :]
    decoded: list[str] = []
    actual_bytes = 0
    index = 0
    while index < len(data):
        character = data[index]
        if character == "\\":
            if index + 1 >= len(data):
                refuse("WAI-E-COMPACT.ESCAPE", path)
            escape = data[index + 1]
            simple = {"\\": "\\", "s": " ", ":": ":", "t": "\t", "n": "\n", "r": "\r"}
            if escape in simple:
                value = simple[escape]
                index += 2
            elif escape == "x" and index + 3 < len(data):
                digits = data[index + 2 : index + 4]
                if re.fullmatch(r"[0-9A-F]{2}", digits) is None:
                    refuse("WAI-E-COMPACT.ESCAPE", path)
                code = int(digits, 16)
                if not (code < 0x20 or code == 0x7F) or code in (9, 10, 13):
                    refuse("WAI-E-CANONICAL.ESCAPE", path)
                value = chr(code)
                index += 4
            else:
                refuse("WAI-E-COMPACT.ESCAPE", path)
        else:
            code = ord(character)
            if character in (" ", ":") or code < 0x20 or code == 0x7F:
                refuse("WAI-E-CANONICAL.ESCAPE", path)
            value = character
            index += 1
        decoded.append(value)
        actual_bytes += len(value.encode("utf-8"))
        if actual_bytes > expected_bytes:
            refuse("WAI-E-COMPACT.LENGTH", path)
    if actual_bytes != expected_bytes:
        refuse("WAI-E-COMPACT.LENGTH", path)
    literal = {"kind": TAG_KINDS[token[0]], "value": "".join(decoded)}
    state = ValidationState()
    state.literal(literal, path, expected)
    if encode_literal(literal) != token:
        refuse("WAI-E-CANONICAL.LITERAL", path)
    return literal


def _record(lines: list[str], depth: int, opcode: str, *fields: str) -> None:
    line = "  " * depth + opcode
    if fields:
        line += " " + " ".join(fields)
    if len(line.encode("utf-8")) > MAX_LINE_BYTES:
        refuse("WAI-E-BOUNDS.LINE", "$")
    lines.append(line)


def _format_expression(lines: list[str], expression: Mapping[str, Any], depth: int) -> None:
    kind = expression["kind"]
    if kind in ("when", "unless"):
        _record(lines, depth, EXPRESSION_OPCODES[kind], encode_literal(expression["predicate"]))
    elif kind == "scope":
        _record(lines, depth, "C", encode_literal({"kind": "identifier", "value": expression["scope"]}))
    else:
        _record(
            lines,
            depth,
            "E",
            encode_literal({"kind": "identifier", "value": expression["target"]}),
            encode_literal(expression["predicate"]),
        )
    for child in expression["expressions"]:
        _format_expression(lines, child, depth + 1)


def _format_promise(lines: list[str], promise: Mapping[str, Any]) -> None:
    _record(
        lines,
        3,
        "M",
        encode_literal({"kind": "identifier", "value": promise["id"]}),
        encode_literal(promise["claim"]),
    )
    for literal in promise["evidence"]:
        _record(lines, 4, "V", encode_literal(literal))
    for evidence_class in promise["evidence_classes"]:
        _record(lines, 4, "K", evidence_class)
    _record(lines, 4, "G", encode_literal(promise["boundary"]))
    for literal in promise["authorises"]:
        _record(lines, 4, "A", encode_literal(literal))
    _record(lines, 4, "Q", promise["consequence"])
    for literal in promise["refuses"]:
        _record(lines, 4, "J", encode_literal(literal))
    for literal in promise["recovery"]:
        _record(lines, 4, "Z", encode_literal(literal))
    for exception in promise["exceptions"]:
        _record(
            lines,
            4,
            "I",
            encode_literal({"kind": "identifier", "value": exception["id"]}),
            *(encode_literal(exception[field]) for field in ("authority", "gate", "subject", "scope", "record", "expiry", "recovery")),
        )


def format_compact(model: Any) -> bytes:
    validate_model(model)
    lines = [MAGIC]
    document = model["document"]
    _record(
        lines,
        0,
        "D",
        encode_literal({"kind": "identifier", "value": document["id"]}),
        encode_literal(document["title"]),
    )
    for source in model["sources"]:
        _record(
            lines,
            1,
            "S",
            encode_literal({"kind": "identifier", "value": source["id"]}),
            encode_literal({"kind": "path", "value": source["path"]}),
            encode_literal({"kind": "sha256", "value": source["sha256"]}),
        )
    for section in model["sections"]:
        _record(
            lines,
            1,
            "H",
            encode_literal({"kind": "identifier", "value": section["id"]}),
            encode_literal(section["title"]),
        )
        for directive in section["directives"]:
            _record(
                lines,
                2,
                DIRECTIVE_OPCODES[directive["kind"]],
                encode_literal({"kind": "identifier", "value": directive["id"]}),
                encode_literal(directive["statement"]),
            )
            for expression in directive["expressions"]:
                _format_expression(lines, expression, 3)
            if directive["promise"] is not None:
                _format_promise(lines, directive["promise"])
    for relation in model["relations"]:
        _record(
            lines,
            1,
            RELATION_OPCODES[relation["kind"]],
            encode_literal({"kind": "identifier", "value": relation["source"]}),
            encode_literal({"kind": "identifier", "value": relation["target"]}),
        )
    for binding in model["bindings"]:
        _record(
            lines,
            1,
            "B",
            encode_literal({"kind": "identifier", "value": binding["source"]}),
            encode_literal({"kind": "identifier", "value": binding["node"]}),
            encode_literal({"kind": "number", "value": binding["start"]}),
            encode_literal({"kind": "number", "value": binding["end"]}),
            encode_literal(binding["reviewer"]),
        )
    if len(lines) > MAX_LINES:
        refuse("WAI-E-BOUNDS.LINES", "$")
    output = ("\n".join(lines) + "\n").encode("utf-8")
    if len(output) > MAX_FILE_BYTES:
        refuse("WAI-E-BOUNDS.FILE", "$")
    return output


class CompactParser:
    def __init__(self, data: bytes) -> None:
        if len(data) > MAX_FILE_BYTES:
            refuse("WAI-E-BOUNDS.FILE", "$")
        if data.startswith(b"\xef\xbb\xbf"):
            refuse("WAI-E-UTF8.BOM", "$")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            refuse("WAI-E-UTF8.DECODE", "$")
        _scalar(text, "$")
        if not text.endswith("\n") or text.endswith("\n\n") or "\r" in text:
            refuse("WAI-E-COMPACT.NEWLINE", "$")
        physical = text[:-1].split("\n")
        if len(physical) > MAX_LINES:
            refuse("WAI-E-BOUNDS.LINES", "$")
        if not physical or physical[0] != MAGIC:
            refuse("WAI-E-VERSION.MAGIC", "$")
        self.records: list[tuple[int, str, list[str]]] = []
        for line_number, line in enumerate(physical[1:], 2):
            path = f"$line[{line_number}]"
            if not line or line.endswith((" ", "\t")) or "\t" in line:
                refuse("WAI-E-COMPACT.WHITESPACE", path)
            if len(line.encode("utf-8")) > MAX_LINE_BYTES:
                refuse("WAI-E-BOUNDS.LINE", path)
            spaces = len(line) - len(line.lstrip(" "))
            if spaces % 2:
                refuse("WAI-E-COMPACT.INDENT", path)
            depth = spaces // 2
            if depth > MAX_DEPTH:
                refuse("WAI-E-BOUNDS.DEPTH", path)
            body = line[spaces:]
            fields = body.split(" ")
            if not fields[0] or len(fields[0]) != 1:
                refuse("WAI-E-COMPACT.OPCODE", path)
            self.records.append((depth, fields[0], fields[1:]))
        self.index = 0
        self.total_literal_bytes = 0

    def literal(self, token: str, expected: str | None = None, path: str = "$") -> dict[str, str]:
        literal = decode_literal(token, expected, path)
        self.total_literal_bytes += len(literal["value"].encode("utf-8"))
        if self.total_literal_bytes > MAX_TOTAL_LITERAL_BYTES:
            refuse("WAI-E-BOUNDS.LITERALS", path)
        return literal

    def peek(self) -> tuple[int, str, list[str]] | None:
        return self.records[self.index] if self.index < len(self.records) else None

    def take(self, depth: int, opcode: str, fields: int) -> list[str]:
        record = self.peek()
        path = f"$record[{self.index}]"
        if record is None:
            refuse("WAI-E-COMPACT.TRUNCATED", path)
        actual_depth, actual_opcode, values = record
        if actual_depth != depth or actual_opcode != opcode:
            refuse("WAI-E-COMPACT.ORDER", path)
        if len(values) != fields:
            refuse("WAI-E-COMPACT.FIELDS", path)
        self.index += 1
        return values

    def expression(self, depth: int) -> dict[str, Any]:
        record = self.peek()
        path = f"$record[{self.index}]"
        if record is None or record[0] != depth or record[1] not in OPCODE_EXPRESSIONS:
            refuse("WAI-E-COMPACT.ORDER", path)
        opcode = record[1]
        kind = OPCODE_EXPRESSIONS[opcode]
        if kind in ("when", "unless"):
            fields = self.take(depth, opcode, 1)
            expression: dict[str, Any] = {
                "kind": kind,
                "predicate": self.literal(fields[0], path=path),
                "expressions": [],
            }
        elif kind == "scope":
            fields = self.take(depth, opcode, 1)
            expression = {
                "kind": kind,
                "scope": self.literal(fields[0], "identifier", path)["value"],
                "expressions": [],
            }
        else:
            fields = self.take(depth, opcode, 2)
            expression = {
                "kind": kind,
                "target": self.literal(fields[0], "identifier", path)["value"],
                "predicate": self.literal(fields[1], path=path),
                "expressions": [],
            }
        while self.peek() is not None and self.peek()[0] == depth + 1 and self.peek()[1] in OPCODE_EXPRESSIONS:
            expression["expressions"].append(self.expression(depth + 1))
        return expression

    def promise(self) -> dict[str, Any]:
        path = f"$record[{self.index}]"
        fields = self.take(3, "M", 2)
        promise: dict[str, Any] = {
            "id": self.literal(fields[0], "identifier", path)["value"],
            "claim": self.literal(fields[1], path=path),
            "evidence": [],
            "evidence_classes": [],
            "boundary": None,
            "authorises": [],
            "consequence": None,
            "refuses": [],
            "recovery": [],
            "exceptions": [],
        }
        while self.peek() is not None and self.peek()[:2] == (4, "V"):
            promise["evidence"].append(self.literal(self.take(4, "V", 1)[0], path=path))
        while self.peek() is not None and self.peek()[:2] == (4, "K"):
            evidence_class = self.take(4, "K", 1)[0]
            if evidence_class not in EVIDENCE_CLASSES:
                refuse("WAI-E-COMPACT.TOKEN", path)
            promise["evidence_classes"].append(evidence_class)
        promise["boundary"] = self.literal(self.take(4, "G", 1)[0], path=path)
        while self.peek() is not None and self.peek()[:2] == (4, "A"):
            promise["authorises"].append(self.literal(self.take(4, "A", 1)[0], path=path))
        consequence = self.take(4, "Q", 1)[0]
        if consequence not in ("0", "1", "2", "3"):
            refuse("WAI-E-COMPACT.TOKEN", path)
        promise["consequence"] = consequence
        while self.peek() is not None and self.peek()[:2] == (4, "J"):
            promise["refuses"].append(self.literal(self.take(4, "J", 1)[0], path=path))
        while self.peek() is not None and self.peek()[:2] == (4, "Z"):
            promise["recovery"].append(self.literal(self.take(4, "Z", 1)[0], path=path))
        while self.peek() is not None and self.peek()[:2] == (4, "I"):
            values = self.take(4, "I", 8)
            exception = {"id": self.literal(values[0], "identifier", path)["value"]}
            for field, token in zip(
                ("authority", "gate", "subject", "scope", "record", "expiry", "recovery"),
                values[1:],
                strict=True,
            ):
                exception[field] = self.literal(token, path=path)
            promise["exceptions"].append(exception)
        return promise

    def parse(self) -> dict[str, Any]:
        fields = self.take(0, "D", 2)
        model: dict[str, Any] = {
            "schema": SCHEMA_ID,
            "document": {
                "id": self.literal(fields[0], "identifier")["value"],
                "title": self.literal(fields[1]),
            },
            "sources": [],
            "sections": [],
            "relations": [],
            "bindings": [],
        }
        while self.peek() is not None and self.peek()[:2] == (1, "S"):
            values = self.take(1, "S", 3)
            model["sources"].append(
                {
                    "id": self.literal(values[0], "identifier")["value"],
                    "path": self.literal(values[1], "path")["value"],
                    "sha256": self.literal(values[2], "sha256")["value"],
                }
            )
        while self.peek() is not None and self.peek()[:2] == (1, "H"):
            values = self.take(1, "H", 2)
            section: dict[str, Any] = {
                "id": self.literal(values[0], "identifier")["value"],
                "title": self.literal(values[1]),
                "directives": [],
            }
            while self.peek() is not None and self.peek()[0] == 2 and self.peek()[1] in OPCODE_DIRECTIVES:
                depth, opcode, _ = self.peek()
                del depth
                values = self.take(2, opcode, 2)
                directive: dict[str, Any] = {
                    "id": self.literal(values[0], "identifier")["value"],
                    "kind": OPCODE_DIRECTIVES[opcode],
                    "statement": self.literal(values[1]),
                    "expressions": [],
                    "promise": None,
                }
                while self.peek() is not None and self.peek()[0] == 3 and self.peek()[1] in OPCODE_EXPRESSIONS:
                    directive["expressions"].append(self.expression(3))
                if self.peek() is not None and self.peek()[:2] == (3, "M"):
                    directive["promise"] = self.promise()
                section["directives"].append(directive)
            model["sections"].append(section)
        while self.peek() is not None and self.peek()[0] == 1 and self.peek()[1] in OPCODE_RELATIONS:
            _, opcode, _ = self.peek()
            values = self.take(1, opcode, 2)
            model["relations"].append(
                {
                    "kind": OPCODE_RELATIONS[opcode],
                    "source": self.literal(values[0], "identifier")["value"],
                    "target": self.literal(values[1], "identifier")["value"],
                }
            )
        while self.peek() is not None and self.peek()[:2] == (1, "B"):
            values = self.take(1, "B", 5)
            model["bindings"].append(
                {
                    "source": self.literal(values[0], "identifier")["value"],
                    "node": self.literal(values[1], "identifier")["value"],
                    "start": self.literal(values[2], "number")["value"],
                    "end": self.literal(values[3], "number")["value"],
                    "reviewer": self.literal(values[4], "identifier"),
                }
            )
        if self.index != len(self.records):
            opcode = self.records[self.index][1]
            if opcode not in set("DSHRFPXYUWNCMVKGAQJZI<>^BE"):
                refuse("WAI-E-COMPACT.OPCODE", f"$record[{self.index}]")
            refuse("WAI-E-COMPACT.ORDER", f"$record[{self.index}]")
        validate_model(model)
        return model


def decode_compact(data: bytes) -> tuple[dict[str, Any], bytes]:
    parser = CompactParser(data)
    model = parser.parse()
    canonical = canonical_json_bytes(model)
    if format_compact(model) != data:
        refuse("WAI-E-CANONICAL.COMPACT", "$")
    return model, canonical


def _open_root(root: str | os.PathLike[str]) -> int:
    try:
        descriptor = os.open(os.fspath(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except (OSError, TypeError):
        refuse("WAI-E-PATH.ROOT", "$")
    if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        refuse("WAI-E-PATH.ROOT", "$")
    return descriptor


def _open_parent(root: str | os.PathLike[str], relative: str) -> tuple[int, str]:
    safe = _safe_relative_path(relative, "$.path")
    components = safe.split("/")
    descriptor = _open_root(root)
    try:
        for component in components[:-1]:
            next_descriptor = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
            if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
                refuse("WAI-E-PATH.COMPONENT", "$.path")
    except CodecError:
        os.close(descriptor)
        raise
    except OSError:
        os.close(descriptor)
        refuse("WAI-E-PATH.COMPONENT", "$.path")
    return descriptor, components[-1]


def read_confined(root: str | os.PathLike[str], relative: str) -> bytes:
    parent, leaf = _open_parent(root, relative)
    descriptor = -1
    try:
        # WAI-PATH-001: O_NONBLOCK lets fstat reject FIFOs without waiting for a writer.
        try:
            descriptor = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        except OSError:
            refuse("WAI-E-PATH.LEAF", "$.path")
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            refuse("WAI-E-PATH.SPECIAL", "$.path")
        if before.st_size > MAX_FILE_BYTES:
            refuse("WAI-E-BOUNDS.FILE", "$.path")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65_536, MAX_FILE_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_FILE_BYTES:
                refuse("WAI-E-BOUNDS.FILE", "$.path")
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            refuse("WAI-E-IO.UNSTABLE", "$.path")
        return b"".join(chunks)
    except CodecError:
        raise
    except OSError:
        refuse("WAI-E-IO.READ", "$.path")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def write_confined_atomic(root: str | os.PathLike[str], relative: str, data: bytes) -> None:
    if len(data) > MAX_FILE_BYTES:
        refuse("WAI-E-BOUNDS.FILE", "$.path")
    parent, leaf = _open_parent(root, relative)
    temporary = f".wai-{secrets.token_hex(16)}"
    descriptor = -1
    created = False
    try:
        try:
            existing = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None and not stat.S_ISREG(existing.st_mode):
            refuse("WAI-E-PATH.SPECIAL", "$.path")
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent,
        )
        created = True
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                refuse("WAI-E-IO.WRITE", "$.path")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, leaf, src_dir_fd=parent, dst_dir_fd=parent)
        created = False
        os.fsync(parent)
    except CodecError:
        raise
    except OSError:
        refuse("WAI-E-IO.WRITE", "$.path")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if created:
            try:
                os.unlink(temporary, dir_fd=parent)
            except OSError:
                pass
        os.close(parent)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _record_bounds(value: Any, path: str = "$", depth: int = 0, *, allow_integers: bool = False) -> None:
    if depth > MAX_RECORD_DEPTH:
        refuse("WAI-E-BOUNDS.DEPTH", path)
    if isinstance(value, dict):
        if len(value) > MAX_OBJECT_MEMBERS:
            refuse("WAI-E-BOUNDS.MEMBERS", path)
        for key, item in value.items():
            _string(key, f"{path}.key")
            _record_bounds(item, f"{path}.{key}", depth + 1, allow_integers=allow_integers)
        return
    if isinstance(value, list):
        if len(value) > MAX_RECORD_ARRAY:
            refuse("WAI-E-BOUNDS.COUNT", path)
        for index, item in enumerate(value):
            _record_bounds(item, f"{path}[{index}]", depth + 1, allow_integers=allow_integers)
        return
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_LITERAL_BYTES:
            refuse("WAI-E-BOUNDS.LITERAL", path)
        _scalar(value, path)
        return
    if value is None or isinstance(value, bool):
        return
    if allow_integers and isinstance(value, int) and not isinstance(value, bool):
        if value < 0 or value > MAX_FILE_BYTES:
            refuse("WAI-E-BOUNDS.NUMBER", path)
        return
    refuse("WAI-E-JSON.NUMBER", path)


def canonical_record_bytes(value: Any, *, allow_integers: bool = False) -> bytes:
    _record_bounds(value, allow_integers=allow_integers)
    output = (
        json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    if len(output) > MAX_FILE_BYTES:
        refuse("WAI-E-BOUNDS.FILE", "$")
    return output


def load_canonical_record(data: bytes, *, allow_integers: bool = False) -> dict[str, Any]:
    if len(data) > MAX_FILE_BYTES:
        refuse("WAI-E-BOUNDS.FILE", "$")
    if data.startswith(b"\xef\xbb\xbf"):
        refuse("WAI-E-UTF8.BOM", "$")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        refuse("WAI-E-UTF8.DECODE", "$")
    _scalar(text, "$")
    parse_int = _bounded_record_integer if allow_integers else _forbidden_number
    try:
        record = json.loads(
            text,
            object_pairs_hook=_duplicate_checked_object,
            parse_int=parse_int,
            parse_float=_forbidden_number,
            parse_constant=_forbidden_number,
        )
    except CodecError:
        raise
    except (json.JSONDecodeError, RecursionError):
        refuse("WAI-E-JSON.SYNTAX", "$")
    if not isinstance(record, dict):
        refuse("WAI-E-SHAPE.OBJECT", "$")
    if canonical_record_bytes(record, allow_integers=allow_integers) != data:
        refuse("WAI-E-CANONICAL.JSON", "$")
    return record


def _sha256(value: Any, path: str) -> str:
    digest = _string(value, path)
    if SHA256_RE.fullmatch(digest) is None:
        refuse("WAI-E-SHAPE.SHA256", path)
    return digest


def _small_decimal(value: Any, path: str, maximum: int) -> int:
    text = _decimal(value, path)
    if len(text) > 9:
        refuse("WAI-E-BOUNDS.COUNT", path)
    number = int(text)
    if number > maximum:
        refuse("WAI-E-BOUNDS.COUNT", path)
    return number


def _confined_directory_entries(root: str | os.PathLike[str], relative: str) -> set[str]:
    parent, leaf = _open_parent(root, relative)
    descriptor = -1
    try:
        try:
            descriptor = os.open(leaf, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        except OSError:
            refuse("WAI-E-PATH.COMPONENT", "$.fixture.root")
        entries: set[str] = set()
        try:
            with os.scandir(descriptor) as iterator:
                for entry in iterator:
                    if len(entries) >= MAX_FIXTURE_FILES:
                        refuse("WAI-E-MANIFEST.CLOSURE", "$.fixture.root")
                    name = entry.name
                    if name in (".", "..") or "/" in name or "\\" in name:
                        refuse("WAI-E-PATH.UNSAFE", "$.fixture.root")
                    try:
                        metadata = entry.stat(follow_symlinks=False)
                    except OSError:
                        refuse("WAI-E-IO.READ", "$.fixture.root")
                    if not stat.S_ISREG(metadata.st_mode):
                        refuse("WAI-E-PATH.SPECIAL", "$.fixture.root")
                    entries.add(name)
        except CodecError:
            raise
        except OSError:
            refuse("WAI-E-IO.READ", "$.fixture.root")
        return entries
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def validate_manifest(manifest: Any) -> dict[str, Any]:
    root = _object(
        manifest,
        (
            "schema",
            "schema_path",
            "schema_sha256",
            "risk_classes",
            "binding_count",
            "question_count",
            "mutation_count",
            "fixtures",
        ),
        "$",
    )
    if _string(root["schema"], "$.schema") != MANIFEST_ID:
        refuse("WAI-E-VERSION.MANIFEST", "$.schema")
    if _safe_relative_path(root["schema_path"], "$.schema_path") != MANIFEST_SCHEMA_PATH:
        refuse("WAI-E-MANIFEST.SCHEMA_PATH", "$.schema_path")
    if _sha256(root["schema_sha256"], "$.schema_sha256") != MANIFEST_SCHEMA_SHA256:
        refuse("WAI-E-DIGEST.SCHEMA", "$.schema_sha256")
    risks = _array(root["risk_classes"], "$.risk_classes", len(RISK_CLASSES), minimum=len(RISK_CLASSES))
    if tuple(_string(item, f"$.risk_classes[{index}]") for index, item in enumerate(risks)) != RISK_CLASSES:
        refuse("WAI-E-MANIFEST.RISKS", "$.risk_classes")
    declared_bindings = _small_decimal(root["binding_count"], "$.binding_count", MAX_BINDINGS)
    if declared_bindings != FIXTURE_BINDING_COUNT:
        refuse("WAI-E-MANIFEST.BINDING_COUNT", "$.binding_count")
    declared_questions = _small_decimal(root["question_count"], "$.question_count", MAX_QUESTIONS)
    if declared_questions != FIXTURE_QUESTION_COUNT:
        refuse("WAI-E-MANIFEST.QUESTION_COUNT", "$.question_count")
    declared_mutations = _small_decimal(root["mutation_count"], "$.mutation_count", MAX_MUTATIONS)
    if declared_mutations != FIXTURE_MUTATION_COUNT:
        refuse("WAI-E-MANIFEST.MUTATION_COUNT", "$.mutation_count")
    fixtures = _array(root["fixtures"], "$.fixtures", len(FIXTURE_IDS), minimum=len(FIXTURE_IDS))
    fixture_ids: list[str] = []
    artifact_paths: set[str] = set()
    fixture_mutations = 0
    for index, raw_fixture in enumerate(fixtures):
        path = f"$.fixtures[{index}]"
        fixture = _object(
            raw_fixture,
            (
                "id",
                "root",
                "source",
                "artifacts",
                "review",
                "binding_count",
                "question_count",
                "mutation_count",
            ),
            path,
        )
        fixture_id = _identifier(fixture["id"], f"{path}.id")
        fixture_ids.append(fixture_id)
        expected_contract = FIXTURE_CONTRACT.get(fixture_id)
        if expected_contract is None:
            refuse("WAI-E-MANIFEST.FIXTURES", f"{path}.id")
        expected_root = f"{FIXTURE_ROOT}/{fixture_id}"
        if _safe_relative_path(fixture["root"], f"{path}.root") != expected_root:
            refuse("WAI-E-MANIFEST.FIXTURE_ROOT", f"{path}.root")
        source = _object(
            fixture["source"],
            ("id", "path", "sha256", "start", "end", "span_sha256"),
            f"{path}.source",
        )
        source_id = _identifier(source["id"], f"{path}.source.id")
        source_path = _safe_relative_path(source["path"], f"{path}.source.path")
        if source_id != expected_contract["source_id"] or source_path != expected_contract["source_path"]:
            refuse("WAI-E-MANIFEST.SOURCE", f"{path}.source")
        _sha256(source["sha256"], f"{path}.source.sha256")
        start = _small_decimal(source["start"], f"{path}.source.start", MAX_FILE_BYTES)
        end = _small_decimal(source["end"], f"{path}.source.end", MAX_FILE_BYTES)
        if end <= start:
            refuse("WAI-E-REFERENCE.SPAN", f"{path}.source")
        _sha256(source["span_sha256"], f"{path}.source.span_sha256")
        artifacts = _object(fixture["artifacts"], tuple(FIXTURE_ARTIFACTS), f"{path}.artifacts")
        for name, filename in FIXTURE_ARTIFACTS.items():
            artifact_path = f"{path}.artifacts.{name}"
            artifact = _object(artifacts[name], ("path", "sha256"), artifact_path)
            expected = f"{expected_root}/{filename}"
            if _safe_relative_path(artifact["path"], f"{artifact_path}.path") != expected:
                refuse("WAI-E-MANIFEST.ARTIFACT_PATH", f"{artifact_path}.path")
            if expected in artifact_paths:
                refuse("WAI-E-MANIFEST.DUPLICATE_PATH", f"{artifact_path}.path")
            artifact_paths.add(expected)
            _sha256(artifact["sha256"], f"{artifact_path}.sha256")
        review = _object(fixture["review"], ("reviewer", "date", "source_ref", "statement"), f"{path}.review")
        if _identifier(review["reviewer"], f"{path}.review.reviewer") != FIXTURE_REVIEWER:
            refuse("WAI-E-MANIFEST.REVIEW", f"{path}.review.reviewer")
        if _string(review["date"], f"{path}.review.date") != "2026-08-30":
            refuse("WAI-E-MANIFEST.REVIEW", f"{path}.review.date")
        if _string(review["source_ref"], f"{path}.review.source_ref") != "d1ca7ba5af741d45d1da6492632661e688157bff":
            refuse("WAI-E-MANIFEST.REVIEW", f"{path}.review.source_ref")
        if _string(review["statement"], f"{path}.review.statement") != "reviewed-source-to-model-binding":
            refuse("WAI-E-MANIFEST.REVIEW", f"{path}.review.statement")
        binding_count = _small_decimal(fixture["binding_count"], f"{path}.binding_count", MAX_BINDINGS)
        if binding_count != expected_contract["binding_count"]:
            refuse("WAI-E-MANIFEST.BINDING_COUNT", f"{path}.binding_count")
        question_count = _small_decimal(fixture["question_count"], f"{path}.question_count", MAX_QUESTIONS)
        if question_count != expected_contract["question_count"]:
            refuse("WAI-E-MANIFEST.QUESTION_COUNT", f"{path}.question_count")
        mutation_count = _small_decimal(fixture["mutation_count"], f"{path}.mutation_count", MAX_MUTATIONS)
        if mutation_count != expected_contract["mutation_count"]:
            refuse("WAI-E-MANIFEST.MUTATION_COUNT", f"{path}.mutation_count")
        fixture_mutations += mutation_count
    if tuple(fixture_ids) != FIXTURE_IDS:
        refuse("WAI-E-MANIFEST.FIXTURES", "$.fixtures")
    if fixture_mutations != declared_mutations:
        refuse("WAI-E-MANIFEST.MUTATION_COUNT", "$.mutation_count")
    return manifest


def _load_bound_artifact(
    root: str | os.PathLike[str], artifact: Mapping[str, Any], path: str
) -> bytes:
    data = read_confined(root, artifact["path"])
    if _digest(data) != artifact["sha256"]:
        refuse("WAI-E-DIGEST.ARTIFACT", path)
    return data


def _validate_source_spans(
    record: Any,
    fixture_id: str,
    source_record: Mapping[str, Any],
    source_bytes: bytes,
    model: Mapping[str, Any],
) -> int:
    item = _object(record, ("schema", "fixture", "source", "spans"), "$.source_spans")
    if _string(item["schema"], "$.source_spans.schema") != "wildcat-agent-instruction-source-spans/v1":
        refuse("WAI-E-VERSION.SOURCE_SPANS", "$.source_spans.schema")
    if _identifier(item["fixture"], "$.source_spans.fixture") != fixture_id:
        refuse("WAI-E-MANIFEST.FIXTURE", "$.source_spans.fixture")
    source = _object(item["source"], ("id", "path", "sha256"), "$.source_spans.source")
    for field in ("id", "path", "sha256"):
        if source[field] != source_record[field]:
            refuse("WAI-E-MANIFEST.SOURCE", f"$.source_spans.source.{field}")
    governed_start = _small_decimal(source_record["start"], "$.source.start", MAX_FILE_BYTES)
    governed_end = _small_decimal(source_record["end"], "$.source.end", MAX_FILE_BYTES)
    spans = _array(item["spans"], "$.source_spans.spans", MAX_BINDINGS, minimum=1)
    expected = []
    for binding in model["bindings"]:
        expected.append((binding["node"], binding["start"], binding["end"], binding["reviewer"]["value"]))
    observed = []
    for index, raw_span in enumerate(spans):
        path = f"$.source_spans.spans[{index}]"
        span = _object(raw_span, ("node", "start", "end", "reviewer", "sha256"), path)
        node = _identifier(span["node"], f"{path}.node")
        start = _small_decimal(span["start"], f"{path}.start", MAX_FILE_BYTES)
        end = _small_decimal(span["end"], f"{path}.end", MAX_FILE_BYTES)
        reviewer = _identifier(span["reviewer"], f"{path}.reviewer")
        if reviewer != FIXTURE_REVIEWER:
            refuse("WAI-E-MANIFEST.REVIEW", f"{path}.reviewer")
        digest = _sha256(span["sha256"], f"{path}.sha256")
        if not governed_start <= start < end <= governed_end <= len(source_bytes):
            refuse("WAI-E-REFERENCE.SPAN", path)
        if _digest(source_bytes[start:end]) != digest:
            refuse("WAI-E-DIGEST.SPAN", path)
        observed.append((node, span["start"], span["end"], reviewer))
    if observed != expected:
        refuse("WAI-E-MANIFEST.BINDINGS", "$.source_spans.spans")
    return len(spans)


def _validate_questions(record: Any, fixture_id: str) -> dict[str, dict[str, Any]]:
    item = _object(record, ("schema", "fixture", "questions"), "$.questions")
    if _string(item["schema"], "$.questions.schema") != "wildcat-agent-instruction-questions/v1":
        refuse("WAI-E-VERSION.QUESTIONS", "$.questions.schema")
    if _identifier(item["fixture"], "$.questions.fixture") != fixture_id:
        refuse("WAI-E-MANIFEST.FIXTURE", "$.questions.fixture")
    questions = _array(item["questions"], "$.questions.questions", MAX_QUESTIONS, minimum=1)
    answers: dict[str, dict[str, Any]] = {}
    for index, raw_question in enumerate(questions):
        path = f"$.questions.questions[{index}]"
        question = _object(
            raw_question,
            ("id", "prompt", "accepted_answers", "refusal_answers", "required_answer", "context"),
            path,
        )
        question_id = _identifier(question["id"], f"{path}.id")
        if question_id in answers:
            refuse("WAI-E-REFERENCE.DUPLICATE_ID", f"{path}.id")
        prompt = _string(question["prompt"], f"{path}.prompt")
        if not prompt.strip():
            refuse("WAI-E-SHAPE.EMPTY", f"{path}.prompt")
        accepted_raw = _array(question["accepted_answers"], f"{path}.accepted_answers", 16, minimum=1)
        refused_raw = _array(question["refusal_answers"], f"{path}.refusal_answers", 16, minimum=1)
        accepted = [_identifier(value, f"{path}.accepted_answers") for value in accepted_raw]
        refused = [_identifier(value, f"{path}.refusal_answers") for value in refused_raw]
        if len(set(accepted)) != len(accepted) or len(set(refused)) != len(refused):
            refuse("WAI-E-REFERENCE.DUPLICATE_ANSWER", path)
        if set(accepted) & set(refused):
            refuse("WAI-E-REFERENCE.ANSWER_CLASS", path)
        required = _identifier(question["required_answer"], f"{path}.required_answer")
        if required not in accepted:
            refuse("WAI-E-REFERENCE.REQUIRED_ANSWER", f"{path}.required_answer")
        context = _object(
            question["context"],
            ("mode", "prior_messages", "examples", "repository_instruction_paths", "tool_definition_ids"),
            f"{path}.context",
        )
        if _string(context["mode"], f"{path}.context.mode") != "fresh":
            refuse("WAI-E-CONTEXT.NOT_FRESH", f"{path}.context.mode")
        prior = _array(context["prior_messages"], f"{path}.context.prior_messages", 0)
        examples = _array(context["examples"], f"{path}.context.examples", 0)
        if prior or examples:
            refuse("WAI-E-CONTEXT.CONTAMINATED", f"{path}.context")
        instructions = _array(
            context["repository_instruction_paths"], f"{path}.context.repository_instruction_paths", 32
        )
        tools = _array(context["tool_definition_ids"], f"{path}.context.tool_definition_ids", 64)
        for value in instructions:
            _safe_relative_path(value, f"{path}.context.repository_instruction_paths")
        for value in tools:
            _identifier(value, f"{path}.context.tool_definition_ids")
        answers[question_id] = {
            "answers": set(accepted) | set(refused),
            "required": required,
        }
    return answers


def _pointer_tokens(pointer: Any, path: str) -> list[str]:
    text = _string(pointer, path)
    if not text.startswith("/") or len(text.encode("utf-8")) > MAX_PATH_BYTES:
        refuse("WAI-E-MUTATION.POINTER", path)
    tokens = []
    for raw in text[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            refuse("WAI-E-MUTATION.POINTER", path)
        tokens.append(raw.replace("~1", "/").replace("~0", "~"))
    return tokens


def apply_mutation(model: Mapping[str, Any], operation: Any) -> dict[str, Any]:
    if not isinstance(operation, dict):
        refuse("WAI-E-SHAPE.OBJECT", "$.mutation.operation")
    kind = operation.get("kind")
    required = ("kind", "path") if kind == "remove" else ("kind", "path", "value")
    item = _object(operation, required, "$.mutation.operation")
    if kind not in ("remove", "replace"):
        refuse("WAI-E-MUTATION.OPERATION", "$.mutation.operation.kind")
    tokens = _pointer_tokens(item["path"], "$.mutation.operation.path")
    if not tokens:
        refuse("WAI-E-MUTATION.POINTER", "$.mutation.operation.path")
    changed = copy.deepcopy(model)
    parent: Any = changed
    for token in tokens[:-1]:
        if isinstance(parent, list):
            if DECIMAL_RE.fullmatch(token) is None or int(token) >= len(parent):
                refuse("WAI-E-MUTATION.POINTER", "$.mutation.operation.path")
            parent = parent[int(token)]
        elif isinstance(parent, dict) and token in parent:
            parent = parent[token]
        else:
            refuse("WAI-E-MUTATION.POINTER", "$.mutation.operation.path")
    token = tokens[-1]
    if isinstance(parent, list):
        if DECIMAL_RE.fullmatch(token) is None or int(token) >= len(parent):
            refuse("WAI-E-MUTATION.POINTER", "$.mutation.operation.path")
        index = int(token)
        if kind == "remove":
            parent.pop(index)
        else:
            parent[index] = copy.deepcopy(item["value"])
    elif isinstance(parent, dict) and token in parent:
        if kind == "remove":
            del parent[token]
        else:
            parent[token] = copy.deepcopy(item["value"])
    else:
        refuse("WAI-E-MUTATION.POINTER", "$.mutation.operation.path")
    return changed


def _mutation_literal_class(model: Mapping[str, Any], operation: Mapping[str, Any]) -> str:
    if not isinstance(operation, dict):
        refuse("WAI-E-SHAPE.OBJECT", "$.mutation.operation")
    if operation.get("kind") != "replace":
        refuse("WAI-E-MUTATION.LITERAL_CLASS", "$.mutation.operation.kind")
    tokens = _pointer_tokens(operation.get("path"), "$.mutation.operation.path")
    if not tokens:
        refuse("WAI-E-MUTATION.LITERAL_CLASS", "$.mutation.operation.path")
    parent: Any = model
    for token in tokens[:-1]:
        if isinstance(parent, list):
            if DECIMAL_RE.fullmatch(token) is None or int(token) >= len(parent):
                refuse("WAI-E-MUTATION.POINTER", "$.mutation.operation.path")
            parent = parent[int(token)]
        elif isinstance(parent, dict) and token in parent:
            parent = parent[token]
        else:
            refuse("WAI-E-MUTATION.POINTER", "$.mutation.operation.path")
    field = tokens[-1]
    if not isinstance(parent, dict) or field not in parent:
        refuse("WAI-E-MUTATION.POINTER", "$.mutation.operation.path")
    if field == "value" and parent.get("kind") in LITERAL_KINDS:
        return parent["kind"]
    if len(tokens) == 3 and tokens[0] == "sources" and field in ("id", "path", "sha256"):
        return {"id": "identifier", "path": "path", "sha256": "sha256"}[field]
    if field == "consequence":
        return "number"
    if field == "id":
        return "identifier"
    refuse("WAI-E-MUTATION.LITERAL_CLASS", "$.mutation.operation.path")


def _validate_mutation_risk_target(
    model: Mapping[str, Any],
    risk: str,
    operation: Any,
    expected_kind: str,
    path: str,
) -> None:
    if not isinstance(operation, dict):
        refuse("WAI-E-SHAPE.OBJECT", f"{path}.operation")
    tokens = _pointer_tokens(operation.get("path"), f"{path}.operation.path")
    directive_target = (
        len(tokens) >= 4
        and tokens[0] == "sections"
        and DECIMAL_RE.fullmatch(tokens[1]) is not None
        and tokens[2] == "directives"
        and DECIMAL_RE.fullmatch(tokens[3]) is not None
    )
    if risk == "exact-literal":
        return
    if risk == "negation":
        matches = directive_target and expected_kind == "answer-change"
    elif risk == "precedence":
        matches = (
            len(tokens) >= 2
            and tokens[0] == "relations"
            and DECIMAL_RE.fullmatch(tokens[1]) is not None
        )
    elif risk == "scope":
        matches = (
            directive_target
            and len(tokens) >= 6
            and tokens[4] == "expressions"
            and DECIMAL_RE.fullmatch(tokens[5]) is not None
        )
        if matches:
            try:
                expression = model["sections"][int(tokens[1])]["directives"][int(tokens[3])]["expressions"][
                    int(tokens[5])
                ]
            except (IndexError, KeyError, TypeError):
                matches = False
            else:
                matches = isinstance(expression, dict) and expression.get("kind") in ("scope", "exception")
    elif risk in ("evidence-class", "authorisation", "recovery"):
        field = {
            "evidence-class": "evidence_classes",
            "authorisation": "authorises",
            "recovery": "recovery",
        }[risk]
        matches = (
            directive_target
            and len(tokens) >= 6
            and tokens[4] == "promise"
            and tokens[5] == field
        )
    else:
        matches = False
    if not matches:
        refuse("WAI-E-MUTATION.RISK_TARGET", f"{path}.operation.path")


def _validate_mutations(
    record: Any,
    fixture_id: str,
    model: Mapping[str, Any],
    model_bytes: bytes,
    declared_count: int,
    question_answers: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    item = _object(record, ("schema", "fixture", "mutations"), "$.mutations")
    if _string(item["schema"], "$.mutations.schema") != "wildcat-agent-instruction-mutations/v1":
        refuse("WAI-E-VERSION.MUTATIONS", "$.mutations.schema")
    if _identifier(item["fixture"], "$.mutations.fixture") != fixture_id:
        refuse("WAI-E-MANIFEST.FIXTURE", "$.mutations.fixture")
    mutations = _array(item["mutations"], "$.mutations.mutations", MAX_MUTATIONS, minimum=1)
    if len(mutations) != declared_count:
        refuse("WAI-E-MANIFEST.MUTATION_COUNT", "$.mutations.mutations")
    records: list[dict[str, Any]] = []
    risks: set[str] = set()
    literal_classes: set[str] = set()
    mutation_ids: set[str] = set()
    answer_change_negations = 0
    for index, raw_mutation in enumerate(mutations):
        path = f"$.mutations.mutations[{index}]"
        if not isinstance(raw_mutation, dict):
            refuse("WAI-E-SHAPE.OBJECT", path)
        risk = _string(raw_mutation.get("risk"), f"{path}.risk")
        required_fields = (
            ("id", "risk", "operation", "expected", "literal_class")
            if risk == "exact-literal"
            else ("id", "risk", "operation", "expected")
        )
        mutation = _object(raw_mutation, required_fields, path)
        mutation_id = _identifier(mutation["id"], f"{path}.id")
        if mutation_id in mutation_ids:
            refuse("WAI-E-REFERENCE.DUPLICATE_ID", f"{path}.id")
        mutation_ids.add(mutation_id)
        if risk not in RISK_CLASSES:
            refuse("WAI-E-MUTATION.RISK", f"{path}.risk")
        risks.add(risk)
        raw_expected = mutation["expected"]
        if not isinstance(raw_expected, dict):
            refuse("WAI-E-SHAPE.OBJECT", f"{path}.expected")
        expected_kind = _string(raw_expected.get("kind"), f"{path}.expected.kind")
        expected_fields = ("kind", "question", "value") if expected_kind == "answer-change" else ("kind", "value")
        expected = _object(raw_expected, expected_fields, f"{path}.expected")
        expected_value = _string(expected["value"], f"{path}.expected.value")
        _validate_mutation_risk_target(model, risk, mutation["operation"], expected_kind, path)
        literal_class = None
        if risk == "exact-literal":
            literal_class = _string(mutation["literal_class"], f"{path}.literal_class")
            if literal_class not in REQUIRED_LITERAL_MUTATION_CLASSES:
                refuse("WAI-E-MUTATION.LITERAL_CLASS", f"{path}.literal_class")
            if _mutation_literal_class(model, mutation["operation"]) != literal_class:
                refuse("WAI-E-MUTATION.LITERAL_CLASS", f"{path}.literal_class")
            if literal_class in literal_classes:
                refuse("WAI-E-MUTATION.LITERAL_CLASS", f"{path}.literal_class")
            literal_classes.add(literal_class)
        mutated = apply_mutation(model, mutation["operation"])
        observed = ""
        if expected_kind == "model-digest":
            if expected_value != "different":
                refuse("WAI-E-MUTATION.EXPECTED", f"{path}.expected.value")
            mutated_bytes = canonical_json_bytes(mutated)
            if _digest(mutated_bytes) == _digest(model_bytes):
                refuse("WAI-E-MUTATION.SILENT", path)
            observed = "model-digest-changed"
        elif expected_kind == "structural-refusal":
            if not expected_value.startswith("WAI-E-"):
                refuse("WAI-E-MUTATION.EXPECTED", f"{path}.expected.value")
            try:
                canonical_json_bytes(mutated)
            except CodecError as error:
                if error.code != expected_value:
                    refuse("WAI-E-MUTATION.WRONG_REFUSAL", path)
                observed = error.code
            else:
                refuse("WAI-E-MUTATION.SILENT", path)
        elif expected_kind == "answer-change":
            if risk != "negation" or question_answers is None:
                refuse("WAI-E-MUTATION.EXPECTED", f"{path}.expected")
            question_id = _identifier(expected["question"], f"{path}.expected.question")
            changed_answer = _identifier(expected_value, f"{path}.expected.value")
            question = question_answers.get(question_id)
            if (
                question is None
                or changed_answer not in question["answers"]
                or changed_answer == question["required"]
            ):
                refuse("WAI-E-MUTATION.EXPECTED", f"{path}.expected")
            mutated_bytes = canonical_json_bytes(mutated)
            if _digest(mutated_bytes) == _digest(model_bytes):
                refuse("WAI-E-MUTATION.SILENT", path)
            answer_change_negations += 1
            observed = "declared-answer-changed"
        else:
            refuse("WAI-E-MUTATION.EXPECTED", f"{path}.expected.kind")
        result = {
            "mutation_id": mutation_id,
            "risk": risk,
            "expected": expected_kind,
            "observed": observed,
        }
        if literal_class is not None:
            result["literal_class"] = literal_class
        records.append(result)
    if answer_change_negations != 1:
        refuse("WAI-E-MUTATION.NEGATION_COVERAGE", "$.mutations.mutations")
    return records, risks, literal_classes


def _check_record(
    event: str,
    manifest_digest: str,
    *,
    outcome: str = "accepted",
    code: str = "WAI-OK",
    **fields: Any,
) -> dict[str, Any]:
    return {
        "schema": CHECK_RECORD_SCHEMA,
        "event": event,
        "manifest_sha256": manifest_digest,
        "outcome": outcome,
        "code": code,
        **fields,
    }


def _check_fixture(
    root: str | os.PathLike[str], fixture: Mapping[str, Any], manifest_digest: str
) -> tuple[list[dict[str, Any]], set[str], set[str], int, int]:
    fixture_id = fixture["id"]
    fixture_digest = _digest(canonical_record_bytes(fixture))
    if _confined_directory_entries(root, fixture["root"]) != set(FIXTURE_ARTIFACTS.values()):
        refuse("WAI-E-MANIFEST.CLOSURE", f"$.fixtures.{fixture_id}.root")
    source_bytes = read_confined(root, fixture["source"]["path"])
    if _digest(source_bytes) != fixture["source"]["sha256"]:
        refuse("WAI-E-DIGEST.SOURCE", f"$.fixtures.{fixture_id}.source.sha256")
    span_start = _small_decimal(fixture["source"]["start"], "$.source.start", MAX_FILE_BYTES)
    span_end = _small_decimal(fixture["source"]["end"], "$.source.end", MAX_FILE_BYTES)
    if span_end > len(source_bytes) or _digest(source_bytes[span_start:span_end]) != fixture["source"]["span_sha256"]:
        refuse("WAI-E-DIGEST.SOURCE_SPAN", f"$.fixtures.{fixture_id}.source.span_sha256")
    artifacts = {
        name: _load_bound_artifact(root, fixture["artifacts"][name], f"$.fixtures.{fixture_id}.artifacts.{name}")
        for name in FIXTURE_ARTIFACTS
    }
    model = load_canonical_json(artifacts["model"])
    if model["document"]["id"] != fixture_id:
        refuse("WAI-E-MANIFEST.FIXTURE", f"$.fixtures.{fixture_id}.model.document.id")
    expected_source = fixture["source"]
    if len(model["sources"]) != 1 or any(
        model["sources"][0][field] != expected_source[field] for field in ("id", "path", "sha256")
    ):
        refuse("WAI-E-MANIFEST.SOURCE", f"$.fixtures.{fixture_id}.model.sources")
    decoded_model, decoded_bytes = decode_compact(artifacts["compact"])
    if decoded_model != model or decoded_bytes != artifacts["model"] or format_compact(model) != artifacts["compact"]:
        refuse("WAI-E-CANONICAL.ROUNDTRIP", f"$.fixtures.{fixture_id}")
    spans_record = load_canonical_record(artifacts["source_spans"])
    binding_count = _validate_source_spans(spans_record, fixture_id, expected_source, source_bytes, model)
    declared_bindings = _small_decimal(fixture["binding_count"], "$.fixture.binding_count", MAX_BINDINGS)
    if binding_count != declared_bindings:
        refuse("WAI-E-MANIFEST.BINDING_COUNT", "$.fixture.binding_count")
    questions = load_canonical_record(artifacts["questions"])
    answer_sets = _validate_questions(questions, fixture_id)
    declared_questions = _small_decimal(fixture["question_count"], "$.fixture.question_count", MAX_QUESTIONS)
    if len(answer_sets) != declared_questions:
        refuse("WAI-E-MANIFEST.QUESTION_COUNT", "$.fixture.question_count")
    mutations = load_canonical_record(artifacts["mutations"])
    declared_count = _small_decimal(fixture["mutation_count"], "$.fixture.mutation_count", MAX_MUTATIONS)
    mutation_records, fixture_risks, literal_classes = _validate_mutations(
        mutations, fixture_id, model, artifacts["model"], declared_count, answer_sets
    )
    records: list[dict[str, Any]] = []
    records.append(
        _check_record(
            "binding.result",
            manifest_digest,
            fixture_id=fixture_id,
            fixture_sha256=fixture_digest,
            source_path=expected_source["path"],
            source_sha256=expected_source["sha256"],
            source_span_sha256=expected_source["span_sha256"],
            binding_count=binding_count,
            missing_count=0,
            overlapping_count=0,
        )
    )
    records.append(
        _check_record(
            "roundtrip.result",
            manifest_digest,
            fixture_id=fixture_id,
            fixture_sha256=fixture_digest,
            model_sha256=_digest(artifacts["model"]),
            compact_sha256=_digest(artifacts["compact"]),
            decoded_sha256=_digest(decoded_bytes),
            idempotent=True,
        )
    )
    for mutation in mutation_records:
        records.append(
            _check_record(
                "mutation.result",
                manifest_digest,
                fixture_id=fixture_id,
                fixture_sha256=fixture_digest,
                **mutation,
            )
        )
    return records, fixture_risks, literal_classes, len(mutation_records), len(answer_sets)


def _check_manifest_bytes(root: str | os.PathLike[str], manifest_bytes: bytes) -> list[dict[str, Any]]:
    manifest_digest = _digest(manifest_bytes)
    manifest = validate_manifest(load_canonical_record(manifest_bytes))
    schema_bytes = read_confined(root, manifest["schema_path"])
    if _digest(schema_bytes) != manifest["schema_sha256"]:
        refuse("WAI-E-DIGEST.SCHEMA", "$.schema_sha256")
    schema = load_canonical_record(schema_bytes, allow_integers=True)
    if schema.get("$id") != MANIFEST_SCHEMA_ID or schema.get("additionalProperties") is not False:
        refuse("WAI-E-MANIFEST.SCHEMA", "$.schema_path")
    records: list[dict[str, Any]] = []
    seen_risks: set[str] = set()
    seen_literal_classes: set[str] = set()
    mutation_total = 0
    question_total = 0
    failures = 0
    for fixture in manifest["fixtures"]:
        fixture_id = fixture["id"]
        try:
            fixture_records, fixture_risks, fixture_literal_classes, fixture_mutations, fixture_questions = _check_fixture(
                root, fixture, manifest_digest
            )
        except CodecError as error:
            failures += 1
            records.append(
                _check_record(
                    "fixture.result",
                    manifest_digest,
                    outcome="refused",
                    code=error.code,
                    fixture_id=fixture_id,
                    fixture_sha256=_digest(canonical_record_bytes(fixture)),
                    node_path=error.node_path,
                )
            )
            continue
        records.extend(fixture_records)
        seen_risks.update(fixture_risks)
        if seen_literal_classes & fixture_literal_classes:
            refuse("WAI-E-MUTATION.LITERAL_CLASS", "$.fixtures")
        seen_literal_classes.update(fixture_literal_classes)
        mutation_total += fixture_mutations
        question_total += fixture_questions
    if failures == 0:
        if seen_risks != set(RISK_CLASSES):
            refuse("WAI-E-MUTATION.COVERAGE", "$.risk_classes")
        if seen_literal_classes != set(REQUIRED_LITERAL_MUTATION_CLASSES):
            refuse("WAI-E-MUTATION.LITERAL_COVERAGE", "$.fixtures")
        if mutation_total != _small_decimal(manifest["mutation_count"], "$.mutation_count", MAX_MUTATIONS):
            refuse("WAI-E-MANIFEST.MUTATION_COUNT", "$.mutation_count")
    records.append(
        _check_record(
            "run.summary",
            manifest_digest,
            outcome="accepted" if failures == 0 else "refused",
            code="WAI-OK" if failures == 0 else "WAI-E-CHECK.FIXTURE",
            fixture_count=len(manifest["fixtures"]),
            binding_count=sum(record.get("binding_count", 0) for record in records),
            roundtrip_count=sum(record["event"] == "roundtrip.result" for record in records),
            mutation_count=mutation_total,
            question_count=question_total,
            passed=sum(record["outcome"] == "accepted" for record in records),
            failed=failures,
            refused=failures,
            unknown=0,
        )
    )
    return records


def check_manifest(root: str | os.PathLike[str], manifest_path: str) -> list[dict[str, Any]]:
    return _check_manifest_bytes(root, read_confined(root, manifest_path))


def _result(
    outcome: str,
    code: str,
    node_path: str,
    input_bytes: bytes = b"",
    model_bytes: bytes | None = None,
    compact_bytes: bytes | None = None,
    *,
    event: str = "validation",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "event": event,
        "outcome": outcome,
        "code": code,
        "node_path": node_path,
        "input_sha256": _digest(input_bytes),
    }
    if model_bytes is not None:
        result["model_sha256"] = _digest(model_bytes)
    if compact_bytes is not None:
        result["compact_sha256"] = _digest(compact_bytes)
    return result


def _emit(result: Mapping[str, Any]) -> None:
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _self_test_model() -> dict[str, Any]:
    reviewer = {"kind": "identifier", "value": "self-test"}
    return {
        "schema": SCHEMA_ID,
        "document": {"id": "doc", "title": {"kind": "text", "value": "self test"}},
        "sources": [{"id": "src", "path": "source.md", "sha256": "0" * 64}],
        "sections": [
            {
                "id": "section",
                "title": {"kind": "text", "value": "section"},
                "directives": [
                    {
                        "id": "rule",
                        "kind": "require",
                        "statement": {"kind": "text", "value": "round trip"},
                        "expressions": [],
                        "promise": None,
                    }
                ],
            }
        ],
        "relations": [],
        "bindings": [
            {"source": "src", "node": "doc", "start": "0", "end": "30", "reviewer": reviewer},
            {"source": "src", "node": "section", "start": "0", "end": "30", "reviewer": reviewer},
            {"source": "src", "node": "rule", "start": "5", "end": "20", "reviewer": reviewer},
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and encode Wildcat agent instruction models.",
        epilog=f"Contract: {CONTRACT_PATH}; schema: {SCHEMA_PATH}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {SCHEMA_ID} compact-magic={MAGIC}")
    subparsers = parser.add_subparsers(dest="command")
    for command in ("validate", "format", "decode", "roundtrip"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--root", default=".")
        command_parser.add_argument("--input", required=True)
        if command != "validate":
            command_parser.add_argument("--output", required=command in ("format", "decode"))
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--root", default=".")
    check_parser.add_argument("--manifest", required=True)
    subparsers.add_parser("self-test")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.command is None:
        parser.print_help()
        return 0
    input_bytes = b""
    manifest_digest: str | None = None
    try:
        if arguments.command == "self-test":
            model = _self_test_model()
            model_bytes = canonical_json_bytes(model)
            compact_bytes = format_compact(model)
            _, decoded = decode_compact(compact_bytes)
            if decoded != model_bytes:
                refuse("WAI-E-CANONICAL.ROUNDTRIP", "$")
            _emit(_result("accepted", "WAI-OK", "$", model_bytes, model_bytes, compact_bytes, event="roundtrip"))
            return 0
        if arguments.command == "check":
            input_bytes = read_confined(arguments.root, arguments.manifest)
            manifest_digest = _digest(input_bytes)
            records = _check_manifest_bytes(arguments.root, input_bytes)
            for record in records:
                _emit(record)
            return 0 if records[-1]["outcome"] == "accepted" else 2
        input_bytes = read_confined(arguments.root, arguments.input)
        if arguments.command == "validate":
            model = load_canonical_json(input_bytes)
            model_bytes = canonical_json_bytes(model)
            _emit(_result("accepted", "WAI-OK", "$", input_bytes, model_bytes))
            return 0
        if arguments.command in ("format", "roundtrip"):
            model = load_canonical_json(input_bytes)
            model_bytes = canonical_json_bytes(model)
            compact_bytes = format_compact(model)
            _, decoded = decode_compact(compact_bytes)
            if decoded != model_bytes:
                refuse("WAI-E-CANONICAL.ROUNDTRIP", "$")
            if arguments.output:
                write_confined_atomic(arguments.root, arguments.output, compact_bytes)
            _emit(_result("accepted", "WAI-OK", "$", input_bytes, model_bytes, compact_bytes, event="roundtrip"))
            return 0
        model, model_bytes = decode_compact(input_bytes)
        compact_bytes = format_compact(model)
        write_confined_atomic(arguments.root, arguments.output, model_bytes)
        _emit(_result("accepted", "WAI-OK", "$", input_bytes, model_bytes, compact_bytes, event="roundtrip"))
        return 0
    except CodecError as error:
        if arguments.command == "check":
            record = {
                "schema": CHECK_RECORD_SCHEMA,
                "event": "run.summary",
                "outcome": "refused",
                "code": error.code,
                "node_path": error.node_path,
                "passed": 0,
                "failed": 0,
                "refused": 1,
                "unknown": 0,
            }
            if manifest_digest is not None:
                record["manifest_sha256"] = manifest_digest
            _emit(record)
            return 2
        event = "validation" if arguments.command == "validate" else "roundtrip"
        _emit(_result("refused", error.code, error.node_path, input_bytes, event=event))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
