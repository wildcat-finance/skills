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
import selectors
import signal
import stat
import subprocess
import sys
import time
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
MANIFEST_SCHEMA_SHA256 = "b09b2d38f0c491977e121b2a38f0bc39185d09aa98f110419fdbf37e4e0419e1"
FIXTURE_ROOT = "tests/fixtures/agent-instruction-v1"
EVIDENCE_ROOT = f"{FIXTURE_ROOT}/evidence"
EVIDENCE_ARTIFACTS = {
    "decoder_bootstrap": "decoder-bootstrap.txt",
    "family_profiles": "family-profiles.json",
    "measurement_record": "measurement.json",
    "parity_prompt": "parity-prompt.txt",
    "parity_record": "parity.json",
    "tokenizer_profile": "tokenizer-profile.json",
}
TRUSTED_PROFILE_SHA256 = {
    "family_profiles": "5fd5875cc9b745bd3b88a542cd5e405ada90fc36eed35b0942a2d952619ff363",
    "tokenizer_profile": "99e4c3b013b9bcc9770e434143c84b671ad57124d59affc13caf809607c3a0bd",
}
TOKENIZER_PROFILE_SCHEMA = "wildcat-agent-instruction-tokenizer-profile/v1"
FAMILY_PROFILES_SCHEMA = "wildcat-agent-instruction-family-profiles/v1"
MEASUREMENT_SCHEMA = "wildcat-agent-instruction-measurement/v1"
PARITY_SCHEMA = "wildcat-agent-instruction-parity/v1"
TOKENIZER_ADAPTER_SCHEMA = "ollama-loopback-generate/v1"
FAMILY_ADAPTER_SCHEMA = "ollama-loopback-chat/v1"
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
MAX_ADAPTER_ARGV = 32
MAX_ADAPTER_ENV = 16
MAX_ADAPTER_INPUT_BYTES = 262_144
MAX_ADAPTER_OUTPUT_BYTES = 65_536
MAX_EXECUTABLE_BYTES = 268_435_456
MAX_PARITY_RESPONSE_BYTES = 512

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
ENV_NAME_RE = re.compile(r"[A-Z][A-Z0-9_]*\Z", re.ASCII)
MODEL_BLOB_RE = re.compile(rb"sha256-([0-9a-f]{64})(?:\s|\Z)")
SECRET_NAME_RE = re.compile(r"(?:AUTH|BEARER|CREDENTIAL|KEY|PASSWORD|SECRET|TOKEN)", re.ASCII)
SECRET_ARG_RE = re.compile(
    r"(?i)(?:authorization|bearer|credential|api[_-]?key|password|secret|token)(?:[\s:=]|\Z)"
)
AUTHORIZATION_TEXT_RE = re.compile(
    r"(?i)(authorization\s*:\s*)(?:bearer\s+)?[^\s,;\"'}]+"
)
BEARER_TEXT_RE = re.compile(r"(?i)(bearer\s+)[^\s,;\"'}]+")
SECRET_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    (["']?(?:credential|api[_-]?key|password|secret|token)["']?\s*[:=]\s*)
    (?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;}]+)
    """
)
# The one marker `digest_neutral_projection` writes over every digest the
# manifest binds a path by: each fixture's whole-file source digest and all five
# of its artefact digests. It was named for the source digests alone while step
# 2's projection reached only those; step 3 widened the projection to the whole
# bound set, so the name follows.
#
# It is `f` sixty-four times for two reasons. It is well-formed lowercase
# hexadecimal, so it satisfies `SHA256_RE` above and a projected artefact keeps
# every digest field's declared shape; a legible marker such as `PROJECTED`
# would force that shape check to be relaxed wherever a projected record is
# read. And it is the largest value the space holds, never observed as a
# SHA-256 output: a bound document that collided with it would be a preimage
# for one specific 2**-256 target, so no real source can be mistaken for the
# marker. All zeros was the other well-formed candidate and is rejected because
# a zero digest already reads as "not set" in too many registers, which is a
# different claim from "deliberately not measured here".
#
# One marker for all eighteen, not one per binding. The corpus digest is meant
# to stop distinguishing revisions that differ only in a bound digest, and a
# per-binding marker would keep distinguishing them by which slot moved. The
# subject still carries every artefact's *path*, so an artefact appearing,
# vanishing or being renamed still moves the corpus digest; what the shared
# marker collapses is only the value in a slot whose identity is recorded
# beside it.
CORPUS_BOUND_DIGEST_PLACEHOLDER = "f" * 64

# What a measurement or parity record says it counted. Every recorded count
# names the exact bytes measured, so a reader who finds a `compact.sha256` that
# does not match `compact.wai` on disk can find out why from the record itself
# rather than by reading this file.
#
# `none` means the bytes on disk, unchanged: the reviewed spans are measured
# raw, because a span's recorded digest is `span_sha256` and that equality is
# the review boundary. `digest-neutral-bound-sha256/v1` means the stream was
# passed through `digest_neutral_projection` first, which is how the canonical
# models and compact documents are measured -- each embeds its source's
# whole-file digest, and counting the raw bytes would make an edit outside a
# reviewed span stale a count of bytes that did not change.
#
# The name is versioned because it identifies a rule, not a value: widening or
# narrowing what the projection substitutes changes what a recorded count is a
# count of, and a record written under the old rule must not read as though it
# were written under the new one.
MEASURED_PROJECTION_NONE = "none"
MEASURED_PROJECTION_DIGEST_NEUTRAL = "digest-neutral-bound-sha256/v1"
MEASURED_PROJECTIONS = (MEASURED_PROJECTION_NONE, MEASURED_PROJECTION_DIGEST_NEUTRAL)

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

    def __init__(
        self, code: str, node_path: str = "$", detail: str | None = None
    ) -> None:
        super().__init__(code)
        self.code = code
        self.node_path = node_path[:512]
        # Operator guidance for a refusal whose code and node path do not
        # tell a reader what to do. It never enters an emitted record: the
        # record stays byte-identical and `main` writes this to stderr,
        # which these commands otherwise leave empty.
        self.detail = detail[:1024] if detail is not None else None


def refuse(code: str, path: str = "$", detail: str | None = None) -> NoReturn:
    raise CodecError(code, path, detail)


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
            binding["start"],
            binding["end"],
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

    def decimal(self, token: str, path: str = "$") -> str:
        value = _decimal(token, path)
        size = len(value.encode("utf-8"))
        if size > MAX_LITERAL_BYTES:
            refuse("WAI-E-BOUNDS.LITERAL", path)
        self.total_literal_bytes += size
        if self.total_literal_bytes > MAX_TOTAL_LITERAL_BYTES:
            refuse("WAI-E-BOUNDS.LITERALS", path)
        return value

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
            path = f"$record[{self.index - 1}]"
            model["bindings"].append(
                {
                    "source": self.literal(values[0], "identifier")["value"],
                    "node": self.literal(values[1], "identifier")["value"],
                    "start": self.decimal(values[2], path),
                    "end": self.decimal(values[3], path),
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


def _hash_executable(path: str, node_path: str, detail: str | None = None) -> str:
    """Digest one pinned executable, or refuse.

    `detail` is the operator guidance every refusal here carries. It is passed
    in rather than built, because this helper is given a path and a node path
    and never the profile those came from, and widening it to take the profile
    would make a digest function depend on a record shape. See skills#1098.
    """
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_EXECUTABLE_BYTES:
            refuse("WAI-E-ADAPTER.EXECUTABLE", node_path, detail)
        if metadata.st_mode & 0o111 == 0:
            refuse("WAI-E-ADAPTER.EXECUTABLE", node_path, detail)
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, min(1_048_576, MAX_EXECUTABLE_BYTES + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_EXECUTABLE_BYTES:
                refuse("WAI-E-ADAPTER.EXECUTABLE", node_path, detail)
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            refuse("WAI-E-ADAPTER.EXECUTABLE_CHANGED", node_path, detail)
        return digest.hexdigest()
    except CodecError:
        raise
    except OSError:
        refuse("WAI-E-ADAPTER.EXECUTABLE", node_path, detail)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _adapter_environment(profile: Mapping[str, Any], path: str) -> dict[str, str]:
    environment: dict[str, str] = {}
    for name in _environment_allowlist(profile["environment_allowlist"], f"{path}.environment_allowlist"):
        if name not in os.environ:
            refuse("WAI-E-ADAPTER.ENVIRONMENT_MISSING", f"{path}.environment_allowlist")
        environment[name] = os.environ[name]
    for name, value in _fixed_environment(profile["fixed_environment"], f"{path}.fixed_environment").items():
        if name in environment and environment[name] != value:
            refuse("WAI-E-ADAPTER.ENVIRONMENT", f"{path}.fixed_environment.{name}")
        environment[name] = value
    return environment


def _kill_process(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except OSError:
        if process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass
    try:
        process.wait(timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        pass


def _run_bounded(
    executable: str,
    argv: Sequence[str],
    input_bytes: bytes,
    environment: Mapping[str, str],
    timeout_seconds: int,
    stdout_cap: int,
    stderr_cap: int,
    path: str,
    detail: str | None = None,
) -> tuple[bytes, bytes]:
    """Run one pinned executable under a timeout and output caps, or refuse.

    `detail` is carried by the two `WAI-E-ADAPTER.UNAVAILABLE` refusals and by
    no other refusal here: those are the two a contributor reaches by being on
    a machine the profile does not pin. A timeout, an output cap or an IO error
    is the adapter answering out of contract, which is a different situation
    and is left with its code and node path.

    It is passed in rather than built, for the reason `_hash_executable` gives:
    this helper is given an argument list, not the profile behind it. See
    skills#1098.
    """
    if len(input_bytes) > MAX_ADAPTER_INPUT_BYTES:
        refuse("WAI-E-ADAPTER.INPUT_CAP", path)
    if timeout_seconds <= 0 or stdout_cap <= 0 or stderr_cap <= 0:
        refuse("WAI-E-ADAPTER.BOUNDS", path)
    try:
        process = subprocess.Popen(
            [executable, *argv],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(environment),
            shell=False,
            start_new_session=True,
        )
    except (OSError, ValueError):
        refuse("WAI-E-ADAPTER.UNAVAILABLE", path, detail)
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    streams = {process.stdout.fileno(): ("stdout", stdout_cap), process.stderr.fileno(): ("stderr", stderr_cap)}
    for descriptor in streams:
        os.set_blocking(descriptor, False)
        selector.register(descriptor, selectors.EVENT_READ)
    stdin_descriptor = process.stdin.fileno()
    os.set_blocking(stdin_descriptor, False)
    input_offset = 0
    if input_bytes:
        selector.register(stdin_descriptor, selectors.EVENT_WRITE)
    else:
        process.stdin.close()
    deadline = time.monotonic() + timeout_seconds
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _kill_process(process)
                refuse("WAI-E-ADAPTER.TIMEOUT", path)
            events = selector.select(min(remaining, 0.25))
            if not events and process.poll() is not None:
                events = [(key, selectors.EVENT_READ) for key in selector.get_map().values() if key.fd != stdin_descriptor]
            for key, mask in events:
                descriptor = key.fd
                if descriptor == stdin_descriptor and mask & selectors.EVENT_WRITE:
                    try:
                        written = os.write(descriptor, input_bytes[input_offset : input_offset + 65_536])
                    except BrokenPipeError:
                        written = 0
                    input_offset += written
                    if written == 0 or input_offset == len(input_bytes):
                        selector.unregister(descriptor)
                        process.stdin.close()
                    continue
                if mask & selectors.EVENT_READ:
                    name, cap = streams[descriptor]
                    try:
                        chunk = os.read(descriptor, min(65_536, cap + 1 - len(buffers[name])))
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(descriptor)
                        continue
                    buffers[name].extend(chunk)
                    if len(buffers[name]) > cap:
                        _kill_process(process)
                        refuse("WAI-E-ADAPTER.OUTPUT_CAP", f"{path}.{name}")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _kill_process(process)
            refuse("WAI-E-ADAPTER.TIMEOUT", path)
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            _kill_process(process)
            refuse("WAI-E-ADAPTER.TIMEOUT", path)
        if returncode != 0:
            refuse("WAI-E-ADAPTER.UNAVAILABLE", path, detail)
        return bytes(buffers["stdout"]), bytes(buffers["stderr"])
    except CodecError:
        _kill_process(process)
        raise
    except (OSError, ValueError):
        _kill_process(process)
        refuse("WAI-E-ADAPTER.IO", path)
    finally:
        selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()


def _adapter_machine_detail(profile: Mapping[str, Any], opening: str) -> str:
    """One opening sentence, then the tokenizer and the machine it needs.

    Every in-scope adapter refusal ends in the same place -- this profile is
    bound to one machine's build, and `measure` and `parity` cannot run
    anywhere that build is absent -- and differs only in how it got there. The
    tail is written once here so a contributor reads the same instruction from
    a missing client, a client that will not run, a version that moved and an
    identity that moved, rather than four descriptions of one situation.

    Only the profile's own recorded fields are named. Nothing is read from the
    environment, so the sentence cannot carry a path or an account name the
    profile does not already record in plain sight.
    """
    return (
        f"{opening} "
        f"This profile pins tokenizer {profile.get('id', 'unrecorded')}, run as "
        f"{profile.get('runtime_executable', 'an unrecorded runtime')} "
        f"through {profile.get('executable', 'an unrecorded client')}. "
        "measure and parity regenerate token counts through that exact build, "
        "so they cannot run anywhere it is absent, including CI. Run them on "
        "the machine that recorded the profile, or re-record the profile where "
        "you are."
    )


def _adapter_identity_detail(profile: Mapping[str, Any], which: str) -> str:
    """Name the tokenizer and the machine a pinned adapter needs.

    `WAI-E-ADAPTER.EXECUTABLE_CHANGED` at a digest node tells a reader that a
    hash differed, not that this profile is bound to one machine's build. The
    codes stay bounded, so the sentence a contributor can act on rides on
    stderr instead. See skills#1098.

    For a recorded value that is present and different: an executable digest,
    the runtime's version output, its identity output, or the model blobs that
    output names.
    """
    return _adapter_machine_detail(
        profile,
        f"adapter refused: the recorded {which} is not the one on this machine.",
    )


def _adapter_executable_detail(profile: Mapping[str, Any], which: str) -> str:
    """The same guidance, for an executable that could not be read at all.

    `_hash_executable` refuses `WAI-E-ADAPTER.EXECUTABLE` when the path is
    absent, is not a regular file, is not executable, or is larger than the
    cap, and `WAI-E-ADAPTER.EXECUTABLE_CHANGED` when the file moves under the
    read. One sentence covers all five, because what a contributor does about
    them is the same and the distinction is already in the code and node path.

    The helper is not given the profile, so this is built by its caller and
    passed in. See skills#1098.
    """
    return _adapter_machine_detail(
        profile,
        f"adapter refused: the recorded {which} could not be read as a stable "
        "executable file on this machine.",
    )


def _adapter_run_detail(profile: Mapping[str, Any], which: str) -> str:
    """The same guidance, for a pinned executable that would not run.

    `WAI-E-ADAPTER.UNAVAILABLE` covers both halves of that: the process would
    not start, and the process started and exited non-zero. On a machine that
    is not the one the profile pins, the first is the usual way a contributor
    meets this code, and the node path alone does not say that the profile is
    machine-bound.

    `_run_bounded` is not given the profile, so this is built by its caller and
    passed in. See skills#1098.
    """
    return _adapter_machine_detail(
        profile,
        f"adapter refused: {which} did not run to completion on this machine.",
    )


def _verify_profile_identity(profile: Mapping[str, Any], path: str = "$.profile") -> None:
    executable = _absolute_executable(profile["executable"], f"{path}.executable")
    if (
        _hash_executable(
            executable,
            f"{path}.executable",
            _adapter_executable_detail(profile, "client executable"),
        )
        != profile["executable_sha256"]
    ):
        refuse(
            "WAI-E-ADAPTER.EXECUTABLE_CHANGED",
            f"{path}.executable_sha256",
            _adapter_identity_detail(profile, "client executable"),
        )
    runtime = _absolute_executable(profile["runtime_executable"], f"{path}.runtime_executable")
    if (
        _hash_executable(
            runtime,
            f"{path}.runtime_executable",
            _adapter_executable_detail(profile, "runtime executable"),
        )
        != profile["runtime_executable_sha256"]
    ):
        refuse(
            "WAI-E-ADAPTER.EXECUTABLE_CHANGED",
            f"{path}.runtime_executable_sha256",
            _adapter_identity_detail(profile, "runtime executable"),
        )
    environment = _adapter_environment(profile, path)
    timeout = _small_decimal(profile["timeout_seconds"], f"{path}.timeout_seconds", 600)
    stdout_cap = _small_decimal(profile["max_stdout_bytes"], f"{path}.max_stdout_bytes", MAX_ADAPTER_OUTPUT_BYTES)
    stderr_cap = _small_decimal(profile["max_stderr_bytes"], f"{path}.max_stderr_bytes", MAX_ADAPTER_OUTPUT_BYTES)
    version_bytes, _ = _run_bounded(
        runtime,
        _argv(profile["version_argv"], f"{path}.version_argv"),
        b"",
        environment,
        timeout,
        stdout_cap,
        stderr_cap,
        f"{path}.version",
        _adapter_run_detail(profile, "the pinned runtime's version call"),
    )
    if _digest(version_bytes) != profile["version_sha256"]:
        refuse(
            "WAI-E-ADAPTER.VERSION_CHANGED",
            f"{path}.version_sha256",
            _adapter_identity_detail(profile, "runtime version output"),
        )
    identity_bytes, _ = _run_bounded(
        runtime,
        _argv(profile["identity_argv"], f"{path}.identity_argv"),
        b"",
        environment,
        timeout,
        stdout_cap,
        stderr_cap,
        f"{path}.identity",
        _adapter_run_detail(profile, "the pinned runtime's identity call"),
    )
    if _digest(identity_bytes) != profile["acquisition_sha256"]:
        refuse(
            "WAI-E-ADAPTER.IDENTITY_CHANGED",
            f"{path}.acquisition_sha256",
            _adapter_identity_detail(profile, "runtime identity output"),
        )
    observed_blobs = tuple(item.decode("ascii") for item in MODEL_BLOB_RE.findall(identity_bytes))
    if observed_blobs != tuple(profile["model_blobs_sha256"]):
        refuse(
            "WAI-E-TOKENIZER.MISMATCH",
            f"{path}.model_blobs_sha256",
            _adapter_identity_detail(profile, "model blob set"),
        )
    if profile["vocabulary_sha256"] not in observed_blobs:
        refuse(
            "WAI-E-TOKENIZER.MISMATCH",
            f"{path}.vocabulary_sha256",
            _adapter_identity_detail(profile, "tokenizer vocabulary blob"),
        )


def _duplicate_checked_external_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            refuse("WAI-E-ADAPTER.JSON", "$.adapter_output")
        result[key] = value
    return result


def _ollama_response(data: bytes, expected_model: str, path: str) -> dict[str, Any]:
    if len(data) > MAX_ADAPTER_OUTPUT_BYTES:
        refuse("WAI-E-ADAPTER.OUTPUT_CAP", path)
    try:
        text = data.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_duplicate_checked_external_object)
    except CodecError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        refuse("WAI-E-ADAPTER.JSON", path)
    if not isinstance(value, dict):
        refuse("WAI-E-ADAPTER.JSON", path)
    allowed = {
        "model",
        "created_at",
        "response",
        "done",
        "done_reason",
        "context",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
    }
    if not set(value) <= allowed:
        refuse("WAI-E-ADAPTER.JSON", path)
    if value.get("model") != expected_model or value.get("done") is not True:
        refuse("WAI-E-TOKENIZER.MISMATCH", path)
    response = value.get("response")
    if not isinstance(response, str):
        refuse("WAI-E-ADAPTER.RESPONSE", path)
    _scalar(response, f"{path}.response")
    if len(response.encode("utf-8")) > MAX_PARITY_RESPONSE_BYTES:
        refuse("WAI-E-ADAPTER.RESPONSE", path)
    count = value.get("prompt_eval_count")
    if not isinstance(count, int) or isinstance(count, bool):
        refuse("WAI-E-TOKENIZER.COUNT", path)
    if count < 0:
        refuse("WAI-E-TOKENIZER.COUNT", path)
    return value


def _ollama_chat_response(data: bytes, expected_model: str, path: str) -> dict[str, Any]:
    if len(data) > MAX_ADAPTER_OUTPUT_BYTES:
        refuse("WAI-E-ADAPTER.OUTPUT_CAP", path)
    try:
        text = data.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_duplicate_checked_external_object)
    except CodecError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        refuse("WAI-E-ADAPTER.JSON", path)
    if not isinstance(value, dict):
        refuse("WAI-E-ADAPTER.JSON", path)
    allowed = {
        "model",
        "created_at",
        "message",
        "done",
        "done_reason",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
    }
    if not set(value) <= allowed or value.get("model") != expected_model or value.get("done") is not True:
        refuse("WAI-E-ADAPTER.RESPONSE", path)
    message = value.get("message")
    if not isinstance(message, dict) or not {"role", "content"} <= set(message) <= {
        "role",
        "content",
        "thinking",
    }:
        refuse("WAI-E-ADAPTER.RESPONSE", path)
    response = message.get("content")
    if message.get("role") != "assistant" or not isinstance(response, str):
        refuse("WAI-E-ADAPTER.RESPONSE", path)
    _scalar(response, f"{path}.message.content")
    if len(response.encode("utf-8")) > MAX_PARITY_RESPONSE_BYTES:
        refuse("WAI-E-ADAPTER.RESPONSE", path)
    thinking = message.get("thinking")
    if thinking is not None and not isinstance(thinking, str):
        refuse("WAI-E-ADAPTER.RESPONSE", path)
    if thinking is not None:
        _scalar(thinking, f"{path}.message.thinking")
    count = value.get("prompt_eval_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        refuse("WAI-E-TOKENIZER.COUNT", path)
    return {"prompt_eval_count": count, "response": response}


def _ollama_generate(
    profile: Mapping[str, Any],
    prompt: bytes,
    *,
    parity: bool,
    path: str,
    answer_ids: Sequence[str] = (),
) -> tuple[int, str]:
    if len(prompt) > MAX_ADAPTER_INPUT_BYTES:
        refuse("WAI-E-ADAPTER.INPUT_CAP", path)
    try:
        prompt_text = prompt.decode("utf-8")
    except UnicodeDecodeError:
        refuse("WAI-E-UTF8.DECODE", path)
    output_tokens = _small_decimal(profile["output_tokens"], f"{path}.output_tokens", 512)
    options = {
        "num_ctx": _small_decimal(profile["context_window"], f"{path}.context_window", 1_048_576),
        "num_predict": output_tokens,
        "seed": _small_decimal(profile["seed"], f"{path}.seed", 2_147_483_647),
        "temperature": 0,
    }
    if parity:
        if profile["adapter"] != FAMILY_ADAPTER_SCHEMA or not answer_ids:
            refuse("WAI-E-ADAPTER.SCHEMA", path)
        request: dict[str, Any] = {
            "model": profile["model"],
            "messages": [{"role": "user", "content": prompt_text}],
            "stream": False,
            "think": False if profile["thinking"] == "disabled" else profile["thinking"],
            "options": options,
        }
        request["format"] = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                # Keep the transport schema open to an unlisted string so the
                # local parser can preserve and refuse what the model actually
                # returned instead of asking the runtime to coerce it.
                "answer_id": {"type": "string"}
            },
            "required": ["answer_id"],
        }
    else:
        if profile["adapter"] != TOKENIZER_ADAPTER_SCHEMA:
            refuse("WAI-E-ADAPTER.SCHEMA", path)
        request = {
            "model": profile["model"],
            "prompt": prompt_text,
            "raw": True,
            "stream": False,
            "options": options,
        }
        request["format"] = {"type": "object", "additionalProperties": False}
    body = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    executable = _absolute_executable(profile["executable"], f"{path}.executable")
    if (
        _hash_executable(
            executable,
            f"{path}.executable",
            _adapter_executable_detail(profile, "client executable"),
        )
        != profile["executable_sha256"]
    ):
        refuse(
            "WAI-E-ADAPTER.EXECUTABLE_CHANGED",
            f"{path}.executable_sha256",
            _adapter_identity_detail(profile, "client executable"),
        )
    stdout, _ = _run_bounded(
        executable,
        _adapter_argv(
            profile["argv"],
            f"{path}.argv",
            profile["adapter"],
            profile["executable"],
        ),
        body,
        _adapter_environment(profile, path),
        _small_decimal(profile["timeout_seconds"], f"{path}.timeout_seconds", 600),
        _small_decimal(profile["max_stdout_bytes"], f"{path}.max_stdout_bytes", MAX_ADAPTER_OUTPUT_BYTES),
        _small_decimal(profile["max_stderr_bytes"], f"{path}.max_stderr_bytes", MAX_ADAPTER_OUTPUT_BYTES),
        path,
        _adapter_run_detail(profile, "the pinned client's model call"),
    )
    response = (
        _ollama_chat_response(stdout, profile["model"], path)
        if parity
        else _ollama_response(stdout, profile["model"], path)
    )
    return response["prompt_eval_count"], response["response"]


def _redact_text(value: str) -> str:
    redacted = AUTHORIZATION_TEXT_RE.sub(lambda match: f"{match.group(1)}[REDACTED]", value)
    redacted = BEARER_TEXT_RE.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
    return SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)


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
        _scalar(value, path)
        if len(value.encode("utf-8")) > MAX_LITERAL_BYTES:
            refuse("WAI-E-BOUNDS.LITERAL", path)
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


def _absolute_executable(value: Any, path: str) -> str:
    text = _string(value, path)
    try:
        raw = text.encode("ascii")
    except UnicodeEncodeError:
        refuse("WAI-E-ADAPTER.EXECUTABLE", path)
    if not raw or len(raw) > 1_024 or not text.startswith("/"):
        refuse("WAI-E-ADAPTER.EXECUTABLE", path)
    if any(part in ("", ".", "..") for part in text.split("/")[1:]):
        refuse("WAI-E-ADAPTER.EXECUTABLE", path)
    if any(byte <= 0x20 or byte == 0x7F for byte in raw):
        refuse("WAI-E-ADAPTER.EXECUTABLE", path)
    return text


def _argv(value: Any, path: str) -> list[str]:
    raw = _array(value, path, MAX_ADAPTER_ARGV, minimum=1)
    result: list[str] = []
    for index, item in enumerate(raw):
        argument = _string(item, f"{path}[{index}]")
        encoded = argument.encode("utf-8")
        if not encoded or len(encoded) > 2_048 or b"\x00" in encoded:
            refuse("WAI-E-ADAPTER.ARGV", f"{path}[{index}]")
        if SECRET_ARG_RE.search(argument):
            refuse("WAI-E-ADAPTER.SECRET", f"{path}[{index}]")
        result.append(argument)
    return result


def _adapter_argv(value: Any, path: str, adapter: str, executable: str) -> list[str]:
    arguments = _argv(value, path)
    endpoint = (
        "http://127.0.0.1:11434/api/chat"
        if adapter == FAMILY_ADAPTER_SCHEMA
        else "http://127.0.0.1:11434/api/generate"
    )
    urls = [argument for argument in arguments if "://" in argument]
    if urls != [endpoint] or arguments[-1] != endpoint:
        refuse("WAI-E-ADAPTER.ENDPOINT", path)
    if os.path.basename(executable) == "curl":
        expected = [
            "--disable",
            "--fail",
            "--silent",
            "--show-error",
            "--max-time",
            arguments[5] if len(arguments) > 5 else "",
            "--header",
            "Content-Type: application/json",
            "--data-binary",
            "@-",
            endpoint,
        ]
        if (
            arguments != expected
            or len(arguments[5]) > 9
            or DECIMAL_RE.fullmatch(arguments[5]) is None
            or int(arguments[5]) == 0
        ):
            refuse("WAI-E-ADAPTER.ARGV", path)
    return arguments


def _environment_allowlist(value: Any, path: str) -> list[str]:
    raw = _array(value, path, MAX_ADAPTER_ENV)
    result: list[str] = []
    for index, item in enumerate(raw):
        name = _string(item, f"{path}[{index}]")
        if ENV_NAME_RE.fullmatch(name) is None or SECRET_NAME_RE.search(name):
            refuse("WAI-E-ADAPTER.ENVIRONMENT", f"{path}[{index}]")
        if name in result:
            refuse("WAI-E-ADAPTER.ENVIRONMENT", f"{path}[{index}]")
        result.append(name)
    if result != sorted(result):
        refuse("WAI-E-ADAPTER.ENVIRONMENT", path)
    return result


def _fixed_environment(value: Any, path: str) -> dict[str, str]:
    if not isinstance(value, dict) or len(value) > MAX_ADAPTER_ENV:
        refuse("WAI-E-ADAPTER.ENVIRONMENT", path)
    result: dict[str, str] = {}
    for name, raw_value in value.items():
        if not isinstance(name, str) or ENV_NAME_RE.fullmatch(name) is None or SECRET_NAME_RE.search(name):
            refuse("WAI-E-ADAPTER.ENVIRONMENT", path)
        item = _string(raw_value, f"{path}.{name}")
        if not item or len(item.encode("utf-8")) > 512 or "\x00" in item:
            refuse("WAI-E-ADAPTER.ENVIRONMENT", f"{path}.{name}")
        result[name] = item
    return result


def _profile_context(value: Any, path: str, expected_mode: str) -> dict[str, Any]:
    context = _object(
        value,
        (
            "mode",
            "prior_messages",
            "examples",
            "repository_instruction_paths",
            "tool_definition_ids",
        ),
        path,
    )
    if _string(context["mode"], f"{path}.mode") != expected_mode:
        refuse("WAI-E-PARITY.CONTEXT", f"{path}.mode")
    for name in ("prior_messages", "examples", "repository_instruction_paths", "tool_definition_ids"):
        if _array(context[name], f"{path}.{name}", MAX_RECORD_ARRAY):
            refuse("WAI-E-PARITY.CONTEXT", f"{path}.{name}")
    return context


def _validate_adapter_profile(
    raw_profile: Any, path: str, *, schema: str, context_mode: str, family: bool
) -> dict[str, Any]:
    common = (
        "schema",
        "id",
        "adapter",
        "model",
        "model_blobs_sha256",
        "vocabulary_sha256",
        "version",
        "executable",
        "executable_sha256",
        "runtime_executable",
        "runtime_executable_sha256",
        "version_argv",
        "version_sha256",
        "identity_argv",
        "acquisition_sha256",
        "argv",
        "environment_allowlist",
        "fixed_environment",
        "input_encoding",
        "context",
        "timeout_seconds",
        "max_stdout_bytes",
        "max_stderr_bytes",
        "context_window",
        "output_tokens",
        "seed",
        "observed_on",
    )
    extra = ("family", "thinking") if family else ("tokenizer",)
    profile = _object(raw_profile, common + extra, path)
    if _string(profile["schema"], f"{path}.schema") != schema:
        refuse("WAI-E-VERSION.PROFILE", f"{path}.schema")
    _identifier(profile["id"], f"{path}.id")
    expected_adapter = FAMILY_ADAPTER_SCHEMA if family else TOKENIZER_ADAPTER_SCHEMA
    if _string(profile["adapter"], f"{path}.adapter") != expected_adapter:
        refuse("WAI-E-ADAPTER.SCHEMA", f"{path}.adapter")
    model = _string(profile["model"], f"{path}.model")
    if not model or len(model.encode("utf-8")) > 256 or any(ord(char) < 0x20 for char in model):
        refuse("WAI-E-ADAPTER.MODEL", f"{path}.model")
    blobs_raw = _array(profile["model_blobs_sha256"], f"{path}.model_blobs_sha256", 4, minimum=1)
    blobs = [_sha256(item, f"{path}.model_blobs_sha256[{index}]") for index, item in enumerate(blobs_raw)]
    if len(set(blobs)) != len(blobs):
        refuse("WAI-E-ADAPTER.IDENTITY", f"{path}.model_blobs_sha256")
    if _sha256(profile["vocabulary_sha256"], f"{path}.vocabulary_sha256") not in blobs:
        refuse("WAI-E-TOKENIZER.MISMATCH", f"{path}.vocabulary_sha256")
    version = _string(profile["version"], f"{path}.version")
    if not version or len(version.encode("utf-8")) > 128:
        refuse("WAI-E-ADAPTER.VERSION", f"{path}.version")
    _absolute_executable(profile["executable"], f"{path}.executable")
    _sha256(profile["executable_sha256"], f"{path}.executable_sha256")
    _absolute_executable(profile["runtime_executable"], f"{path}.runtime_executable")
    _sha256(profile["runtime_executable_sha256"], f"{path}.runtime_executable_sha256")
    _argv(profile["version_argv"], f"{path}.version_argv")
    _sha256(profile["version_sha256"], f"{path}.version_sha256")
    _argv(profile["identity_argv"], f"{path}.identity_argv")
    _sha256(profile["acquisition_sha256"], f"{path}.acquisition_sha256")
    _adapter_argv(
        profile["argv"],
        f"{path}.argv",
        expected_adapter,
        profile["executable"],
    )
    _environment_allowlist(profile["environment_allowlist"], f"{path}.environment_allowlist")
    _fixed_environment(profile["fixed_environment"], f"{path}.fixed_environment")
    if _string(profile["input_encoding"], f"{path}.input_encoding") != "utf-8":
        refuse("WAI-E-ADAPTER.ENCODING", f"{path}.input_encoding")
    _profile_context(profile["context"], f"{path}.context", context_mode)
    _small_decimal(profile["timeout_seconds"], f"{path}.timeout_seconds", 600)
    stdout_cap = _small_decimal(profile["max_stdout_bytes"], f"{path}.max_stdout_bytes", MAX_ADAPTER_OUTPUT_BYTES)
    stderr_cap = _small_decimal(profile["max_stderr_bytes"], f"{path}.max_stderr_bytes", MAX_ADAPTER_OUTPUT_BYTES)
    if stdout_cap == 0 or stderr_cap == 0:
        refuse("WAI-E-ADAPTER.OUTPUT_CAP", path)
    if _small_decimal(profile["context_window"], f"{path}.context_window", 1_048_576) == 0:
        refuse("WAI-E-ADAPTER.CONTEXT_WINDOW", f"{path}.context_window")
    if _small_decimal(profile["output_tokens"], f"{path}.output_tokens", 512) == 0:
        refuse("WAI-E-ADAPTER.OUTPUT_TOKENS", f"{path}.output_tokens")
    _small_decimal(profile["seed"], f"{path}.seed", 2_147_483_647)
    observed_on = _string(profile["observed_on"], f"{path}.observed_on")
    try:
        date.fromisoformat(observed_on)
    except ValueError:
        refuse("WAI-E-ADAPTER.DATE", f"{path}.observed_on")
    if family:
        _identifier(profile["family"], f"{path}.family")
        if _string(profile["thinking"], f"{path}.thinking") not in ("disabled", "low"):
            refuse("WAI-E-ADAPTER.THINKING", f"{path}.thinking")
    else:
        _identifier(profile["tokenizer"], f"{path}.tokenizer")
    return profile


def validate_tokenizer_profile(value: Any) -> dict[str, Any]:
    return _validate_adapter_profile(
        value,
        "$",
        schema=TOKENIZER_PROFILE_SCHEMA,
        context_mode="raw-prompt-count",
        family=False,
    )


def validate_family_profiles(value: Any) -> dict[str, Any]:
    root = _object(value, ("schema", "profiles"), "$")
    if _string(root["schema"], "$.schema") != FAMILY_PROFILES_SCHEMA:
        refuse("WAI-E-VERSION.PROFILE", "$.schema")
    raw_profiles = _array(root["profiles"], "$.profiles", 2, minimum=2)
    profiles = [
        _validate_adapter_profile(
            item,
            f"$.profiles[{index}]",
            schema="wildcat-agent-instruction-family-profile/v1",
            context_mode="fresh-process",
            family=True,
        )
        for index, item in enumerate(raw_profiles)
    ]
    if len({profile["id"] for profile in profiles}) != 2:
        refuse("WAI-E-PARITY.IDENTITY", "$.profiles")
    if len({profile["family"] for profile in profiles}) != 2:
        refuse("WAI-E-PARITY.ALIAS", "$.profiles")
    if len({tuple(profile["model_blobs_sha256"]) for profile in profiles}) != 2:
        refuse("WAI-E-PARITY.ALIAS", "$.profiles")
    if len({profile["acquisition_sha256"] for profile in profiles}) != 2:
        refuse("WAI-E-PARITY.ALIAS", "$.profiles")
    return root


def _confined_directory_entries(
    root: str | os.PathLike[str], relative: str, maximum: int = MAX_FIXTURE_FILES
) -> set[str]:
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
                    if len(entries) >= maximum:
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
            "evidence",
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
        if _string(review["date"], f"{path}.review.date") != "2026-08-31":
            refuse("WAI-E-MANIFEST.REVIEW", f"{path}.review.date")
        if _string(review["source_ref"], f"{path}.review.source_ref") != "1c1137898bce9086c34310bd29b5cf8a889f800c":
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
    evidence = _object(root["evidence"], tuple(EVIDENCE_ARTIFACTS), "$.evidence")
    for name, filename in EVIDENCE_ARTIFACTS.items():
        path = f"$.evidence.{name}"
        artifact = _object(evidence[name], ("path", "sha256"), path)
        expected = f"{EVIDENCE_ROOT}/{filename}"
        if _safe_relative_path(artifact["path"], f"{path}.path") != expected:
            refuse("WAI-E-MANIFEST.EVIDENCE_PATH", f"{path}.path")
        _sha256(artifact["sha256"], f"{path}.sha256")
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


def _check_manifest_bytes(
    root: str | os.PathLike[str],
    manifest_bytes: bytes,
    *,
    validate_evidence_reports: bool = True,
) -> list[dict[str, Any]]:
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
        _load_evidence_artifacts(
            root,
            manifest,
            validate_reports=validate_evidence_reports,
        )
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


def _record_nonnegative_integer(value: Any, path: str) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        or value > MAX_FILE_BYTES
    ):
        refuse("WAI-E-BOUNDS.NUMBER", path)
    return value


def _measurement_material(
    value: Any,
    expected_bytes: bytes,
    path: str,
    projection: str,
) -> tuple[dict[str, Any], int]:
    """One recorded count, checked against the bytes it says it counted.

    `expected_bytes` is the measured stream itself, already projected by the
    caller when `projection` says so, and `projection` is recorded beside the
    count. Both halves are compared, so a record cannot carry a digest computed
    one way and a `projection` claiming the other: the digest is of the stream
    the caller measured, and the name says which stream that was.

    `tokens` is carried over from the supplied record rather than recomputed,
    because recomputing it means consulting a model. That is the one field here
    the checker takes on trust, and it is why the digest beside it has to be
    exact.
    """
    material = _object(value, ("sha256", "bytes", "projection", "tokens"), path)
    token_count = _record_nonnegative_integer(material["tokens"], f"{path}.tokens")
    _record_nonnegative_integer(material["bytes"], f"{path}.bytes")
    _sha256(material["sha256"], f"{path}.sha256")
    if material["projection"] not in MEASURED_PROJECTIONS:
        refuse("WAI-E-MEASURE.PROJECTION", f"{path}.projection")
    expected = {
        "sha256": _digest(expected_bytes),
        "bytes": len(expected_bytes),
        "projection": projection,
        "tokens": token_count,
    }
    if canonical_record_bytes(material, allow_integers=True) != canonical_record_bytes(
        expected, allow_integers=True
    ):
        refuse("WAI-E-MEASURE.RECORD", path)
    return expected, token_count


def _validate_measurement_record(
    root: str | os.PathLike[str],
    value: Any,
    manifest: Mapping[str, Any],
    evidence: Mapping[str, bytes],
    profile: Mapping[str, Any],
) -> None:
    path = "$.evidence.measurement_record"
    record = _object(
        value,
        (
            "schema",
            "correlation_id",
            "corpus_sha256",
            "tokenizer_profile_sha256",
            "tokenizer_id",
            "model",
            "vocabulary_sha256",
            "observed_on",
            "bootstrap_sha256",
            "bootstrap",
            "documents",
            "amortised",
            "totals",
            "events",
            "summary",
        ),
        path,
    )
    bootstrap = evidence["decoder_bootstrap"]
    bootstrap_record = _object(record["bootstrap"], ("bytes", "tokens"), f"{path}.bootstrap")
    bootstrap_tokens = _record_nonnegative_integer(
        bootstrap_record["tokens"], f"{path}.bootstrap.tokens"
    )
    _record_nonnegative_integer(bootstrap_record["bytes"], f"{path}.bootstrap.bytes")
    expected_bootstrap = {"bytes": len(bootstrap), "tokens": bootstrap_tokens}
    if canonical_record_bytes(bootstrap_record, allow_integers=True) != canonical_record_bytes(
        expected_bootstrap, allow_integers=True
    ):
        refuse("WAI-E-MEASURE.RECORD", f"{path}.bootstrap")

    raw_documents = _array(
        record["documents"],
        f"{path}.documents",
        len(manifest["fixtures"]),
        minimum=len(manifest["fixtures"]),
    )
    documents: list[dict[str, Any]] = []
    for index, fixture in enumerate(manifest["fixtures"]):
        fixture_id = fixture["id"]
        document_path = f"{path}.documents[{index}]"
        supplied = _object(
            raw_documents[index],
            ("fixture_id", "source", "canonical_model", "compact", "one_document"),
            document_path,
        )
        source_file = read_confined(root, fixture["source"]["path"])
        start = _small_decimal(fixture["source"]["start"], "$.source.start", MAX_FILE_BYTES)
        end = _small_decimal(fixture["source"]["end"], "$.source.end", MAX_FILE_BYTES)
        # The reviewed span is measured raw. Its recorded digest is
        # `span_sha256`, and that equality is what ties a count to the bytes a
        # reviewer signed off, so it must not be substituted away.
        # `test_no_reviewed_span_carries_a_bound_digest` checks that no span
        # would be changed by the projection anyway, so measuring it raw is an
        # observation rather than an exception carved out here.
        source_bytes = source_file[start:end]
        # The canonical model and the compact document each embed the source's
        # whole-file digest, so these are the two streams the projection exists
        # for: measured through it, they are byte-identical across an edit that
        # moved nothing inside a reviewed span.
        model_bytes = digest_neutral_projection(
            manifest,
            _load_bound_artifact(
                root,
                fixture["artifacts"]["model"],
                f"$.fixtures.{fixture_id}.model",
            ),
        )
        compact_bytes = digest_neutral_projection(
            manifest,
            _load_bound_artifact(
                root,
                fixture["artifacts"]["compact"],
                f"$.fixtures.{fixture_id}.compact",
            ),
        )
        source, source_tokens = _measurement_material(
            supplied["source"],
            source_bytes,
            f"{document_path}.source",
            MEASURED_PROJECTION_NONE,
        )
        model, model_tokens = _measurement_material(
            supplied["canonical_model"],
            model_bytes,
            f"{document_path}.canonical_model",
            MEASURED_PROJECTION_DIGEST_NEUTRAL,
        )
        compact, compact_tokens = _measurement_material(
            supplied["compact"],
            compact_bytes,
            f"{document_path}.compact",
            MEASURED_PROJECTION_DIGEST_NEUTRAL,
        )
        one_document = _object(
            supplied["one_document"],
            ("bytes", "tokens", "delta_bytes", "delta_tokens"),
            f"{document_path}.one_document",
        )
        _record_nonnegative_integer(one_document["bytes"], f"{document_path}.one_document.bytes")
        _record_nonnegative_integer(one_document["tokens"], f"{document_path}.one_document.tokens")
        expected_document = {
            "fixture_id": fixture_id,
            "source": source,
            "canonical_model": model,
            "compact": compact,
            "one_document": {
                "bytes": len(compact_bytes) + len(bootstrap),
                "tokens": compact_tokens + bootstrap_tokens,
                "delta_bytes": _signed_decimal(len(compact_bytes) + len(bootstrap) - len(source_bytes)),
                "delta_tokens": _signed_decimal(compact_tokens + bootstrap_tokens - source_tokens),
            },
        }
        if canonical_record_bytes(supplied, allow_integers=True) != canonical_record_bytes(
            expected_document, allow_integers=True
        ):
            refuse("WAI-E-MEASURE.RECORD", document_path)
        documents.append(expected_document)

    amortised: list[dict[str, Any]] = []
    for count in range(1, len(documents) + 1):
        selected = documents[:count]
        source_bytes = sum(item["source"]["bytes"] for item in selected)
        source_tokens = sum(item["source"]["tokens"] for item in selected)
        compact_bytes = sum(item["compact"]["bytes"] for item in selected)
        compact_tokens = sum(item["compact"]["tokens"] for item in selected)
        amortised.append(
            {
                "document_count": count,
                "source_bytes": source_bytes,
                "source_tokens": source_tokens,
                "compact_plus_bootstrap_bytes": compact_bytes + len(bootstrap),
                "compact_plus_bootstrap_tokens": compact_tokens + bootstrap_tokens,
                "bootstrap_bytes_per_document": {"numerator": len(bootstrap), "denominator": count},
                "bootstrap_tokens_per_document": {"numerator": bootstrap_tokens, "denominator": count},
                "delta_bytes": _signed_decimal(compact_bytes + len(bootstrap) - source_bytes),
                "delta_tokens": _signed_decimal(compact_tokens + bootstrap_tokens - source_tokens),
            }
        )
    source_bytes_total = sum(item["source"]["bytes"] for item in documents)
    source_tokens_total = sum(item["source"]["tokens"] for item in documents)
    model_bytes_total = sum(item["canonical_model"]["bytes"] for item in documents)
    model_tokens_total = sum(item["canonical_model"]["tokens"] for item in documents)
    compact_bytes_total = sum(item["compact"]["bytes"] for item in documents)
    compact_tokens_total = sum(item["compact"]["tokens"] for item in documents)
    delta_tokens = compact_tokens_total + bootstrap_tokens - source_tokens_total
    correlation_id = _digest(
        (
            _corpus_sha256(manifest)
            + _digest(evidence["tokenizer_profile"])
            + _digest(bootstrap)
        ).encode("ascii")
    )
    events: list[dict[str, Any]] = [
        {
            "event": "measurement.baseline",
            "correlation_id": correlation_id,
            "fixture_id": item["fixture_id"],
            "bytes": item["source"]["bytes"],
            "tokens": item["source"]["tokens"],
            "verdict": "recorded",
            "unknowns": [],
            "refusal_codes": [],
        }
        for item in documents
    ]
    events.extend(
        {
            "event": "measurement.result",
            "correlation_id": correlation_id,
            "fixture_id": item["fixture_id"],
            "bytes": item["compact"]["bytes"],
            "tokens": item["compact"]["tokens"],
            "bootstrap_bytes": len(bootstrap),
            "bootstrap_tokens": bootstrap_tokens,
            "verdict": "recorded",
            "unknowns": [],
            "refusal_codes": [],
        }
        for item in documents
    )
    success = delta_tokens < 0
    refusal_codes = [] if success else ["WAI-E-MEASURE.NON_NEGATIVE_DELTA"]
    summary = {
        "event": "run.summary",
        "correlation_id": correlation_id,
        "case_count": 1 + 3 * len(documents),
        "passed": 1 if success else 0,
        "failed": 0 if success else 1,
        "refused": 0 if success else 1,
        "unknown": 0,
        "verdict": "accepted" if success else "refused",
        "unknowns": [],
        "refusal_codes": refusal_codes,
    }
    events.append(summary)
    expected = {
        "schema": MEASUREMENT_SCHEMA,
        "correlation_id": correlation_id,
        "corpus_sha256": _corpus_sha256(manifest),
        "tokenizer_profile_sha256": _digest(evidence["tokenizer_profile"]),
        "tokenizer_id": profile["id"],
        "model": profile["model"],
        "vocabulary_sha256": profile["vocabulary_sha256"],
        "observed_on": profile["observed_on"],
        "bootstrap_sha256": _digest(bootstrap),
        "bootstrap": expected_bootstrap,
        "documents": documents,
        "amortised": amortised,
        "totals": {
            "source_bytes": source_bytes_total,
            "source_tokens": source_tokens_total,
            "canonical_model_bytes": model_bytes_total,
            "canonical_model_tokens": model_tokens_total,
            "compact_bytes": compact_bytes_total,
            "compact_tokens": compact_tokens_total,
            "compact_plus_bootstrap_bytes": compact_bytes_total + len(bootstrap),
            "compact_plus_bootstrap_tokens": compact_tokens_total + bootstrap_tokens,
            "delta_bytes": _signed_decimal(compact_bytes_total + len(bootstrap) - source_bytes_total),
            "delta_tokens": _signed_decimal(delta_tokens),
        },
        "events": events,
        "summary": summary,
    }
    if canonical_record_bytes(record, allow_integers=True) != canonical_record_bytes(
        expected, allow_integers=True
    ):
        refuse("WAI-E-MEASURE.RECORD", path)
    if not success:
        refuse("WAI-E-MEASURE.NON_NEGATIVE_DELTA", f"{path}.totals.delta_tokens")


def _validate_parity_mode_record(
    value: Any,
    *,
    profile: Mapping[str, Any],
    fixture_id: str,
    question: Mapping[str, Any],
    mode: str,
    document: bytes,
    prompt: bytes,
    projection: str,
    correlation_id: str,
    path: str,
) -> dict[str, Any]:
    supplied = _object(
        value,
        (
            "job_id",
            "input_sha256",
            "projection",
            "prompt_sha256",
            "prompt_tokens",
            "answer_id",
            "response",
            "outcome",
            "code",
        ),
        path,
    )
    if supplied["projection"] not in MEASURED_PROJECTIONS:
        refuse("WAI-E-PARITY.PROJECTION", f"{path}.projection")
    prompt_tokens = _record_nonnegative_integer(supplied["prompt_tokens"], f"{path}.prompt_tokens")
    response = _string(supplied["response"], f"{path}.response")
    if len(response.encode("utf-8")) > MAX_PARITY_RESPONSE_BYTES:
        refuse("WAI-E-PARITY.RECORD", f"{path}.response")
    answer = _answer_record(response, question)
    if answer["answer_id"] != question["required_answer"] or answer["outcome"] != "accepted":
        refuse("WAI-E-PARITY.RECORD", f"{path}.answer_id")
    expected = {
        "job_id": _digest(
            (correlation_id + profile["id"] + fixture_id + question["id"] + mode).encode("utf-8")
        ),
        "input_sha256": _digest(document),
        "projection": projection,
        "prompt_sha256": _digest(prompt),
        "prompt_tokens": prompt_tokens,
        **answer,
    }
    if canonical_record_bytes(supplied, allow_integers=True) != canonical_record_bytes(
        expected, allow_integers=True
    ):
        refuse("WAI-E-PARITY.RECORD", path)
    return expected


def _validate_parity_record(
    root: str | os.PathLike[str],
    value: Any,
    manifest: Mapping[str, Any],
    evidence: Mapping[str, bytes],
    families: Mapping[str, Any],
) -> None:
    path = "$.evidence.parity_record"
    record = _object(
        value,
        (
            "schema",
            "correlation_id",
            "corpus_sha256",
            "family_profiles_sha256",
            "family_ids",
            "prompt_template_sha256",
            "bootstrap_sha256",
            "observed_on",
            "results",
            "summary",
        ),
        path,
    )
    profiles = families["profiles"]
    bootstrap = evidence["decoder_bootstrap"]
    template = evidence["parity_prompt"]
    corpus_digest = _corpus_sha256(manifest)
    correlation_id = _digest(
        (
            corpus_digest
            + _digest(evidence["family_profiles"])
            + _digest(template)
            + _digest(bootstrap)
        ).encode("ascii")
    )
    expected_result_count = len(profiles) * FIXTURE_QUESTION_COUNT
    raw_results = _array(
        record["results"],
        f"{path}.results",
        expected_result_count,
        minimum=expected_result_count,
    )
    results: list[dict[str, Any]] = []
    result_index = 0
    for profile in profiles:
        for fixture in manifest["fixtures"]:
            fixture_id = fixture["id"]
            source_file = read_confined(root, fixture["source"]["path"])
            start = _small_decimal(fixture["source"]["start"], "$.source.start", MAX_FILE_BYTES)
            end = _small_decimal(fixture["source"]["end"], "$.source.end", MAX_FILE_BYTES)
            source = source_file[start:end]
            # The compact document is put to the model through the projection,
            # so the prompt a parity result records is the prompt that was
            # actually sent and both survive an out-of-span edit. The reviewed
            # span goes raw, for the same reason it does in the measurement.
            compact = digest_neutral_projection(
                manifest,
                _load_bound_artifact(
                    root,
                    fixture["artifacts"]["compact"],
                    f"$.fixtures.{fixture_id}.compact",
                ),
            )
            questions_record = load_canonical_record(
                _load_bound_artifact(
                    root,
                    fixture["artifacts"]["questions"],
                    f"$.fixtures.{fixture_id}.questions",
                )
            )
            _validate_questions(questions_record, fixture_id)
            for question in questions_record["questions"]:
                result_path = f"{path}.results[{result_index}]"
                supplied = _object(
                    raw_results[result_index],
                    (
                        "event",
                        "correlation_id",
                        "family_id",
                        "family",
                        "model",
                        "fixture_id",
                        "question_id",
                        "required_answer",
                        "context_sha256",
                        "source",
                        "compact",
                        "verdict",
                        "unknowns",
                        "refusal_codes",
                    ),
                    result_path,
                )
                source_prompt = _render_parity_prompt(template, "source", bootstrap, source, question)
                compact_prompt = _render_parity_prompt(template, "compact", bootstrap, compact, question)
                source_record = _validate_parity_mode_record(
                    supplied["source"],
                    profile=profile,
                    fixture_id=fixture_id,
                    question=question,
                    mode="source",
                    document=source,
                    prompt=source_prompt,
                    projection=MEASURED_PROJECTION_NONE,
                    correlation_id=correlation_id,
                    path=f"{result_path}.source",
                )
                compact_record = _validate_parity_mode_record(
                    supplied["compact"],
                    profile=profile,
                    fixture_id=fixture_id,
                    question=question,
                    mode="compact",
                    document=compact,
                    prompt=compact_prompt,
                    projection=MEASURED_PROJECTION_DIGEST_NEUTRAL,
                    correlation_id=correlation_id,
                    path=f"{result_path}.compact",
                )
                expected_result = {
                    "event": "parity.result",
                    "correlation_id": correlation_id,
                    "family_id": profile["id"],
                    "family": profile["family"],
                    "model": profile["model"],
                    "fixture_id": fixture_id,
                    "question_id": question["id"],
                    "required_answer": question["required_answer"],
                    "context_sha256": _digest(canonical_record_bytes(question["context"])),
                    "source": source_record,
                    "compact": compact_record,
                    "verdict": "accepted",
                    "unknowns": [],
                    "refusal_codes": [],
                }
                if canonical_record_bytes(supplied, allow_integers=True) != canonical_record_bytes(
                    expected_result, allow_integers=True
                ):
                    refuse("WAI-E-PARITY.RECORD", result_path)
                results.append(expected_result)
                result_index += 1
    summary = {
        "event": "run.summary",
        "correlation_id": correlation_id,
        "case_count": len(results) * 2,
        "question_pair_count": len(results),
        "passed": len(results),
        "failed": 0,
        "refused": 0,
        "unknown": 0,
        "verdict": "accepted",
        "unknowns": [],
        "refusal_codes": [],
    }
    expected = {
        "schema": PARITY_SCHEMA,
        "correlation_id": correlation_id,
        "corpus_sha256": corpus_digest,
        "family_profiles_sha256": _digest(evidence["family_profiles"]),
        "family_ids": [profile["id"] for profile in profiles],
        "prompt_template_sha256": _digest(template),
        "bootstrap_sha256": _digest(bootstrap),
        "observed_on": profiles[0]["observed_on"],
        "results": results,
        "summary": summary,
    }
    if canonical_record_bytes(record, allow_integers=True) != canonical_record_bytes(
        expected, allow_integers=True
    ):
        refuse("WAI-E-PARITY.RECORD", path)


def _load_evidence_artifacts(
    root: str | os.PathLike[str],
    manifest: Mapping[str, Any],
    *,
    validate_reports: bool = True,
) -> dict[str, bytes]:
    if _confined_directory_entries(root, EVIDENCE_ROOT, len(EVIDENCE_ARTIFACTS)) != set(EVIDENCE_ARTIFACTS.values()):
        refuse("WAI-E-MANIFEST.CLOSURE", "$.evidence")
    evidence: dict[str, bytes] = {}
    for name in EVIDENCE_ARTIFACTS:
        evidence[name] = _load_bound_artifact(root, manifest["evidence"][name], f"$.evidence.{name}")
    for name, expected_sha256 in TRUSTED_PROFILE_SHA256.items():
        if _digest(evidence[name]) != expected_sha256:
            refuse("WAI-E-DIGEST.PROFILE", f"$.evidence.{name}")
    bootstrap = evidence["decoder_bootstrap"]
    if not bootstrap or len(bootstrap) > 4_096 or not bootstrap.endswith(b"\n"):
        refuse("WAI-E-MEASURE.BOOTSTRAP", "$.evidence.decoder_bootstrap")
    try:
        bootstrap.decode("utf-8")
    except UnicodeDecodeError:
        refuse("WAI-E-UTF8.DECODE", "$.evidence.decoder_bootstrap")
    prompt = evidence["parity_prompt"]
    if not prompt or len(prompt) > 16_384 or not prompt.endswith(b"\n"):
        refuse("WAI-E-PARITY.PROMPT", "$.evidence.parity_prompt")
    try:
        prompt_text = prompt.decode("utf-8")
    except UnicodeDecodeError:
        refuse("WAI-E-UTF8.DECODE", "$.evidence.parity_prompt")
    for placeholder in (
        "{mode}",
        "{decoder_bootstrap}",
        "{document}",
        "{question}",
        "{answer_ids}",
    ):
        if prompt_text.count(placeholder) != 1:
            refuse("WAI-E-PARITY.PROMPT", "$.evidence.parity_prompt")
    tokenizer = validate_tokenizer_profile(load_canonical_record(evidence["tokenizer_profile"]))
    families = validate_family_profiles(load_canonical_record(evidence["family_profiles"]))
    if not validate_reports:
        return evidence
    measurement = load_canonical_record(evidence["measurement_record"], allow_integers=True)
    parity = load_canonical_record(evidence["parity_record"], allow_integers=True)
    if measurement.get("schema") != MEASUREMENT_SCHEMA:
        refuse("WAI-E-VERSION.MEASUREMENT", "$.evidence.measurement_record")
    if parity.get("schema") != PARITY_SCHEMA:
        refuse("WAI-E-VERSION.PARITY", "$.evidence.parity_record")
    if measurement.get("tokenizer_profile_sha256") != _digest(evidence["tokenizer_profile"]):
        refuse("WAI-E-DIGEST.PROFILE", "$.evidence.measurement_record")
    if parity.get("family_profiles_sha256") != _digest(evidence["family_profiles"]):
        refuse("WAI-E-DIGEST.PROFILE", "$.evidence.parity_record")
    if parity.get("prompt_template_sha256") != _digest(prompt):
        refuse("WAI-E-DIGEST.PROMPT", "$.evidence.parity_record")
    if measurement.get("bootstrap_sha256") != _digest(bootstrap) or parity.get("bootstrap_sha256") != _digest(bootstrap):
        refuse("WAI-E-DIGEST.BOOTSTRAP", "$.evidence")
    if measurement.get("tokenizer_id") != tokenizer["id"]:
        refuse("WAI-E-TOKENIZER.MISMATCH", "$.evidence.measurement_record")
    corpus_digest = _corpus_sha256(manifest)
    if measurement.get("corpus_sha256") != corpus_digest:
        refuse("WAI-E-DIGEST.CORPUS", "$.evidence.measurement_record")
    if parity.get("corpus_sha256") != corpus_digest:
        refuse("WAI-E-DIGEST.CORPUS", "$.evidence.parity_record")
    if (
        measurement.get("model") != tokenizer["model"]
        or measurement.get("vocabulary_sha256") != tokenizer["vocabulary_sha256"]
        or measurement.get("observed_on") != tokenizer["observed_on"]
    ):
        refuse("WAI-E-TOKENIZER.MISMATCH", "$.evidence.measurement_record")
    family_ids = [profile["id"] for profile in families["profiles"]]
    if parity.get("family_ids") != family_ids:
        refuse("WAI-E-PARITY.IDENTITY", "$.evidence.parity_record")
    _validate_measurement_record(root, measurement, manifest, evidence, tokenizer)
    _validate_parity_record(root, parity, manifest, evidence, families)
    return evidence


def _bound_digest_values(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    """Every digest value the manifest binds a path by, sorted and deduplicated.

    Deliberately the same enumeration as `bound_digests` in
    `scripts/prove_agent_instruction_reconciliation.py`: each fixture's
    whole-file `source.sha256` and all five of its `artifacts.*.sha256`, six per
    fixture and eighteen across the three committed fixtures. The prover walks
    `(path, digest)` pairs because its constructor and its `--report` guard both
    need the path; the projection needs only the digest, so this returns the
    values.

    The two are held together by
    `test_the_projection_covers_every_path_the_prover_binds`, which asks the
    prover for its list rather than restating one, so a path the manifest starts
    binding cannot be protected by the prover and passed over by the projection.
    """
    values: set[str] = set()
    for fixture in manifest["fixtures"]:
        values.add(fixture["source"]["sha256"])
        for artifact in fixture["artifacts"].values():
            values.add(artifact["sha256"])
    return tuple(sorted(values))


def digest_neutral_projection(manifest: Mapping[str, Any], data: bytes) -> bytes:
    """`data` with every digest the manifest binds a path by neutralised.

    A bound instruction document is bound four times over: the manifest records
    its whole-file SHA-256, the artefacts derived from it -- `model.json`,
    `source-spans.json` and the compact document's `h64:` literal -- each embed
    that same digest, and the manifest then binds each of those artefacts by a
    digest *of* the bytes that embedding sits inside. Editing the document
    anywhere, including outside its reviewed span, moves all four, even though
    not one reviewed byte changed. That is the whole cost skills#1098 reports.

    This is the projection the `digest-neutral-corpus` design measures instead
    of the raw bytes. It substitutes one fixed marker for every digest in
    `_bound_digest_values` and leaves every other byte where it was, so
    `model.json`, `source-spans.json`, the compact document and the manifest all
    project to identical bytes across two revisions of the document they derive
    from.

    Step 2 substituted the source digests alone and pinned the resulting gap in
    `test_the_projection_does_not_yet_neutralise_the_bound_artefact_digests`:
    the `artifacts.*.sha256` entries are 64-hex runs but not bound *source*
    digests, so a substitution keyed on the source digests passed over them, and
    the `_corpus_sha256` subject -- which carries `fixtures` whole -- still
    differed across an out-of-span edit. Step 3 closes it here by keying the
    substitution on everything the manifest binds rather than on the source
    quarter of it, which is what lets the switch below actually hold.

    Two of the five artefact digests per fixture, `mutations` and `questions`,
    belong to artefacts that embed no source digest and never move under an
    out-of-span edit. Neutralising them is unnecessary for that edit and is done
    anyway, because the rule the projection can defend is "every path the
    manifest binds", not "the subset that happens to move today": a rule with a
    hand-picked exception drifts the moment a new artefact kind is added.

    The reviewed span digest is untouched and stays the review boundary: an edit
    that moves reviewed bytes still moves it, and `_corpus_sha256` below still
    digests it, so `in-span-edit-refusal` is unaffected by the widening. That
    holds because no `span_sha256` carries the bytes of any digest this
    substitutes -- neither a `source.sha256`, which would need a reviewed span
    covering a whole file, nor an `artifacts.*.sha256`, which would need a
    reviewed span whose digest collided with a derived artefact's.
    `test_the_reviewed_span_digest_is_distinct_from_the_projected_digest` checks
    both rather than leaving either to the fixtures' good behaviour.

    Substitution is by byte, not by field path, because one of the embeddings
    has no addressable path: the compact document carries the digest as an
    `h64:` literal inside a codec's byte stream, not as JSON. Matching each
    bound digest's own 64-byte literal reaches every embedding under one rule
    rather than a schema-aware walker per artefact kind, and it reaches only
    those: every other 64-hex run -- `span_sha256`, an evidence record's
    digests, a digest quoted in prose -- is left exactly where it was.

    Nothing is read from disk and nothing is written.
    """
    projected = data
    for bound_digest in _bound_digest_values(manifest):
        projected = projected.replace(
            bound_digest.encode("ascii"),
            CORPUS_BOUND_DIGEST_PLACEHOLDER.encode("ascii"),
        )
    return projected


CORPUS_OMITTED_SOURCE_KEYS = ("start", "end")


def _corpus_subject_fixtures(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    """`fixtures`, with each `source` record's recorded offsets left out.

    `start` and `end` say where a reviewed span sits in a file, not what it
    says. An edit before a span start moves both and moves no reviewed byte, so
    while they are in the digested subject the corpus digest moves for a change
    the measurement is not evidence about. Removing them is what makes both
    out-of-span placements neutral rather than only the one that appends.

    They are *removed* rather than substituted. `digest_neutral_projection`
    replaces byte sequences, which is sound for a 64-hex digest literal and
    unsound for a decimal: `18445` is a substring of `184450` and of any offset
    that extends it, so substituting one offset could rewrite part of another
    number anywhere in the subject. The subject is canonicalised from a mapping,
    so dropping the two keys reaches exactly the values named and nothing else.

    `span_sha256` stays. It is what ties the corpus digest to the reviewed bytes
    themselves, and removing or substituting it would make an in-span edit
    invisible here -- which is the failure
    `test_the_corpus_subject_still_moves_on_an_in_span_edit` exists to catch.

    This is necessary for a before-span edit to reconcile and it is not
    sufficient, which is recorded here rather than left to be found. The
    measurement record measures `canonical_model` and `compact` through
    `digest_neutral_projection`, and both documents carry the reviewed span's
    offsets inside them -- `model.json` as every binding's `start` and `end`.
    Re-deriving those after an edit before a span start moves both measured
    streams, so `_measurement_material` still refuses `WAI-E-MEASURE.RECORD`
    for them. That second cause is not closed here and cannot be closed the
    same way: those streams are what the recorded counts are counts of.
    `test_a_before_span_edit_still_moves_the_measured_artefact_streams` pins it.

    Nothing is mutated: each fixture and its `source` record are copied.
    """
    subjects: list[dict[str, Any]] = []
    for fixture in manifest["fixtures"]:
        subject = dict(fixture)
        subject["source"] = {
            key: value
            for key, value in fixture["source"].items()
            if key not in CORPUS_OMITTED_SOURCE_KEYS
        }
        subjects.append(subject)
    return subjects


def _corpus_sha256(manifest: Mapping[str, Any]) -> str:
    """The measured corpus's identity: the same subject, seen through the projection.

    The subject's shape is unchanged -- schema, the three counts, the risk
    classes and `fixtures` -- and so is everything in it that describes what was
    reviewed: each fixture's id, its source path, its `span_sha256`, and every
    artefact path. Two things change. The bytes are digested after
    `digest_neutral_projection` has run over them, so each fixture's whole-file
    `source.sha256` and all five of its `artifacts.*.sha256` read as the marker
    instead of as themselves; and each `source` record's `start` and `end` are
    left out of the subject entirely, by `_corpus_subject_fixtures`.

    The effect is that the corpus's identity is the reviewed span digest and the
    projected digests rather than the whole-file digest, the raw artefact
    digests and the positions the spans happen to sit at. An edit outside a
    reviewed span moves the whole-file digest and the three artefact digests
    that embed it; all four are substituted. An edit before a span start moves
    the recorded offsets as well; those are not in the subject. Either way the
    subject is byte-identical before and after and the corpus digest does not
    move. An edit inside a reviewed span moves `span_sha256`, which is never
    substituted and never removed, so the subject differs and the corpus digest
    does move.

    A neutral corpus digest is not on its own a reconciliation. For the
    before-span placement `_corpus_subject_fixtures` records what still
    refuses behind it.

    This narrows what the corpus digest is evidence *of*, and only that. The
    manifest still binds every whole-file and artefact digest, and `check` still
    verifies each one against the bytes on disk -- `WAI-E-DIGEST.SOURCE` and
    `WAI-E-DIGEST.ARTIFACT` are untouched -- so a tampered bound document is
    caught exactly where it was before. What stops happening is a *measurement*
    being declared stale by a change that moved no measured byte. ADR-076
    records the choice and the alternatives that were rejected for it, including
    what it deliberately leaves alone: `measure` still records each document's
    `canonical_model` and `compact` as digests of the *raw* artefact bytes, so
    the measurement record is still staled by an out-of-span edit at a node this
    switch does not reach.

    What the offsets' removal costs is stated rather than deferred: the corpus
    digest stops distinguishing a moved offset whose span digest is unchanged.
    `check` still catches that against the bytes on disk, at
    `WAI-E-DIGEST.SOURCE_SPAN` and `WAI-E-DIGEST.ARTIFACT`, and
    `WAI-E-REFERENCE.SPAN`, `WAI-E-DIGEST.SPAN` and `WAI-E-MANIFEST.BINDINGS` in
    `_validate_source_spans` are what make a moved offset onto a byte-identical
    window unreachable.

    The subject is projected through `manifest` itself, so a caller holding an
    edited manifest gets that manifest's own bound set. That is what makes the
    two sides of the comparison above line up: the digests substituted after the
    edit are the post-edit values, which is precisely why the two projections
    agree.
    """
    subject = {
        "schema": manifest["schema"],
        "risk_classes": manifest["risk_classes"],
        "binding_count": manifest["binding_count"],
        "question_count": manifest["question_count"],
        "mutation_count": manifest["mutation_count"],
        "fixtures": _corpus_subject_fixtures(manifest),
    }
    return _digest(digest_neutral_projection(manifest, canonical_record_bytes(subject)))


def _signed_decimal(value: int) -> str:
    return str(value)


def measure_manifest(root: str | os.PathLike[str], manifest_path: str) -> tuple[dict[str, Any], bool]:
    manifest_bytes = read_confined(root, manifest_path)
    manifest = validate_manifest(load_canonical_record(manifest_bytes))
    checked = _check_manifest_bytes(root, manifest_bytes, validate_evidence_reports=False)
    if checked[-1]["outcome"] != "accepted":
        refuse("WAI-E-MEASURE.MUTATIONS", "$.manifest")
    evidence = _load_evidence_artifacts(root, manifest, validate_reports=False)
    profile = validate_tokenizer_profile(load_canonical_record(evidence["tokenizer_profile"]))
    _verify_profile_identity(profile)
    bootstrap = evidence["decoder_bootstrap"]
    corpus_digest = _corpus_sha256(manifest)
    correlation_id = _digest(
        (corpus_digest + _digest(evidence["tokenizer_profile"]) + _digest(bootstrap)).encode("ascii")
    )
    raw_documents: list[dict[str, Any]] = []
    for fixture in manifest["fixtures"]:
        fixture_id = fixture["id"]
        source_file = read_confined(root, fixture["source"]["path"])
        start = _small_decimal(fixture["source"]["start"], "$.source.start", MAX_FILE_BYTES)
        end = _small_decimal(fixture["source"]["end"], "$.source.end", MAX_FILE_BYTES)
        # The reviewed span raw, the two derived artefacts through the
        # projection. `_validate_measurement_record` reads the same three
        # streams the same way, so what the tokenizer is handed here is exactly
        # what `check` recomputes the digests of later.
        source = source_file[start:end]
        model = digest_neutral_projection(
            manifest,
            _load_bound_artifact(root, fixture["artifacts"]["model"], f"$.fixtures.{fixture_id}.model"),
        )
        compact = digest_neutral_projection(
            manifest,
            _load_bound_artifact(root, fixture["artifacts"]["compact"], f"$.fixtures.{fixture_id}.compact"),
        )
        raw_documents.append(
            {"fixture_id": fixture_id, "source": source, "model": model, "compact": compact}
        )

    events: list[dict[str, Any]] = []
    for document in raw_documents:
        fixture_id = document["fixture_id"]
        source_tokens, _ = _ollama_generate(
            profile,
            document["source"],
            parity=False,
            path=f"$.documents.{fixture_id}.source",
        )
        document["source_tokens"] = source_tokens
        events.append(
            {
                "event": "measurement.baseline",
                "correlation_id": correlation_id,
                "fixture_id": fixture_id,
                "bytes": len(document["source"]),
                "tokens": source_tokens,
                "verdict": "recorded",
                "unknowns": [],
                "refusal_codes": [],
            }
        )

    bootstrap_tokens, _ = _ollama_generate(profile, bootstrap, parity=False, path="$.bootstrap")
    documents: list[dict[str, Any]] = []
    for document in raw_documents:
        fixture_id = document["fixture_id"]
        source = document["source"]
        model = document["model"]
        compact = document["compact"]
        source_tokens = document["source_tokens"]
        model_tokens, _ = _ollama_generate(
            profile,
            model,
            parity=False,
            path=f"$.documents.{fixture_id}.model",
        )
        compact_tokens, _ = _ollama_generate(
            profile,
            compact,
            parity=False,
            path=f"$.documents.{fixture_id}.compact",
        )
        documents.append(
            {
                "fixture_id": fixture_id,
                "source": {
                    "sha256": _digest(source),
                    "bytes": len(source),
                    "projection": MEASURED_PROJECTION_NONE,
                    "tokens": source_tokens,
                },
                "canonical_model": {
                    "sha256": _digest(model),
                    "bytes": len(model),
                    "projection": MEASURED_PROJECTION_DIGEST_NEUTRAL,
                    "tokens": model_tokens,
                },
                "compact": {
                    "sha256": _digest(compact),
                    "bytes": len(compact),
                    "projection": MEASURED_PROJECTION_DIGEST_NEUTRAL,
                    "tokens": compact_tokens,
                },
                "one_document": {
                    "bytes": len(compact) + len(bootstrap),
                    "tokens": compact_tokens + bootstrap_tokens,
                    "delta_bytes": _signed_decimal(len(compact) + len(bootstrap) - len(source)),
                    "delta_tokens": _signed_decimal(compact_tokens + bootstrap_tokens - source_tokens),
                },
            }
        )
        events.append(
            {
                "event": "measurement.result",
                "correlation_id": correlation_id,
                "fixture_id": fixture_id,
                "bytes": len(compact),
                "tokens": compact_tokens,
                "bootstrap_bytes": len(bootstrap),
                "bootstrap_tokens": bootstrap_tokens,
                "verdict": "recorded",
                "unknowns": [],
                "refusal_codes": [],
            }
        )
    _verify_profile_identity(profile)
    amortised: list[dict[str, Any]] = []
    for count in range(1, len(documents) + 1):
        selected = documents[:count]
        source_bytes = sum(item["source"]["bytes"] for item in selected)
        source_tokens = sum(item["source"]["tokens"] for item in selected)
        compact_bytes = sum(item["compact"]["bytes"] for item in selected)
        compact_tokens = sum(item["compact"]["tokens"] for item in selected)
        amortised.append(
            {
                "document_count": count,
                "source_bytes": source_bytes,
                "source_tokens": source_tokens,
                "compact_plus_bootstrap_bytes": compact_bytes + len(bootstrap),
                "compact_plus_bootstrap_tokens": compact_tokens + bootstrap_tokens,
                "bootstrap_bytes_per_document": {"numerator": len(bootstrap), "denominator": count},
                "bootstrap_tokens_per_document": {"numerator": bootstrap_tokens, "denominator": count},
                "delta_bytes": _signed_decimal(compact_bytes + len(bootstrap) - source_bytes),
                "delta_tokens": _signed_decimal(compact_tokens + bootstrap_tokens - source_tokens),
            }
        )
    source_bytes_total = sum(item["source"]["bytes"] for item in documents)
    source_tokens_total = sum(item["source"]["tokens"] for item in documents)
    model_bytes_total = sum(item["canonical_model"]["bytes"] for item in documents)
    model_tokens_total = sum(item["canonical_model"]["tokens"] for item in documents)
    compact_bytes_total = sum(item["compact"]["bytes"] for item in documents)
    compact_tokens_total = sum(item["compact"]["tokens"] for item in documents)
    delta_tokens = compact_tokens_total + bootstrap_tokens - source_tokens_total
    success = delta_tokens < 0
    refusal_codes = [] if success else ["WAI-E-MEASURE.NON_NEGATIVE_DELTA"]
    events.append(
        {
            "event": "run.summary",
            "correlation_id": correlation_id,
            "case_count": 1 + 3 * len(documents),
            "passed": 1 if success else 0,
            "failed": 0 if success else 1,
            "refused": 0 if success else 1,
            "unknown": 0,
            "verdict": "accepted" if success else "refused",
            "unknowns": [],
            "refusal_codes": refusal_codes,
        }
    )
    report = {
        "schema": MEASUREMENT_SCHEMA,
        "correlation_id": correlation_id,
        "corpus_sha256": corpus_digest,
        "tokenizer_profile_sha256": _digest(evidence["tokenizer_profile"]),
        "tokenizer_id": profile["id"],
        "model": profile["model"],
        "vocabulary_sha256": profile["vocabulary_sha256"],
        "observed_on": profile["observed_on"],
        "bootstrap_sha256": _digest(bootstrap),
        "bootstrap": {"bytes": len(bootstrap), "tokens": bootstrap_tokens},
        "documents": documents,
        "amortised": amortised,
        "totals": {
            "source_bytes": source_bytes_total,
            "source_tokens": source_tokens_total,
            "canonical_model_bytes": model_bytes_total,
            "canonical_model_tokens": model_tokens_total,
            "compact_bytes": compact_bytes_total,
            "compact_tokens": compact_tokens_total,
            "compact_plus_bootstrap_bytes": compact_bytes_total + len(bootstrap),
            "compact_plus_bootstrap_tokens": compact_tokens_total + bootstrap_tokens,
            "delta_bytes": _signed_decimal(compact_bytes_total + len(bootstrap) - source_bytes_total),
            "delta_tokens": _signed_decimal(delta_tokens),
        },
        "events": events,
        "summary": events[-1],
    }
    return report, success


def _render_parity_prompt(
    template: bytes,
    mode: str,
    bootstrap: bytes,
    document: bytes,
    question: Mapping[str, Any],
) -> bytes:
    try:
        template_text = template.decode("utf-8")
        bootstrap_text = bootstrap.decode("utf-8")
        document_text = document.decode("utf-8")
    except UnicodeDecodeError:
        refuse("WAI-E-UTF8.DECODE", "$.parity.prompt")
    rendered = template_text
    replacements = {
        "{mode}": mode,
        "{decoder_bootstrap}": bootstrap_text if mode == "compact" else "not-applicable\n",
        "{document}": document_text,
        "{question}": question["prompt"],
        "{answer_ids}": ",".join(sorted([*question["accepted_answers"], *question["refusal_answers"]])),
    }
    for placeholder, value in replacements.items():
        if rendered.count(placeholder) != 1:
            refuse("WAI-E-PARITY.PROMPT", "$.parity.prompt")
        rendered = rendered.replace(placeholder, value)
    output = rendered.encode("utf-8")
    if len(output) > MAX_ADAPTER_INPUT_BYTES:
        refuse("WAI-E-ADAPTER.INPUT_CAP", "$.parity.prompt")
    return output


def _answer_record(response: str, question: Mapping[str, Any]) -> dict[str, Any]:
    safe_response = _redact_text(response)
    _scalar(safe_response, "$.adapter_output.response")
    if len(safe_response.encode("utf-8")) > MAX_PARITY_RESPONSE_BYTES:
        safe_response = "[REDACTED: response exceeded stored bound]"
    try:
        value = json.loads(response, object_pairs_hook=_duplicate_checked_external_object)
    except (CodecError, json.JSONDecodeError, RecursionError):
        return {
            "answer_id": None,
            "response": safe_response,
            "outcome": "refused",
            "code": "WAI-E-PARITY.ANSWER",
        }
    if not isinstance(value, dict) or set(value) != {"answer_id"} or not isinstance(value["answer_id"], str):
        return {
            "answer_id": None,
            "response": safe_response,
            "outcome": "refused",
            "code": "WAI-E-PARITY.ANSWER",
        }
    answer_id = value["answer_id"]
    try:
        _scalar(answer_id, "$.adapter_output.answer_id")
    except CodecError:
        return {
            "answer_id": None,
            "response": safe_response,
            "outcome": "refused",
            "code": "WAI-E-PARITY.ANSWER",
        }
    safe_answer_id = _redact_text(answer_id)
    if len(safe_answer_id.encode("utf-8")) > MAX_PARITY_RESPONSE_BYTES:
        safe_answer_id = "[REDACTED: answer id exceeded stored bound]"
    if answer_id in question["accepted_answers"]:
        outcome, code = "accepted", "WAI-OK"
    elif answer_id in question["refusal_answers"]:
        outcome, code = "refused", "WAI-E-PARITY.MODEL_REFUSAL"
    else:
        outcome, code = "refused", "WAI-E-PARITY.UNLISTED"
    return {"answer_id": safe_answer_id, "response": safe_response, "outcome": outcome, "code": code}


def parity_manifest(root: str | os.PathLike[str], manifest_path: str) -> tuple[dict[str, Any], bool]:
    manifest_bytes = read_confined(root, manifest_path)
    manifest = validate_manifest(load_canonical_record(manifest_bytes))
    checked = _check_manifest_bytes(root, manifest_bytes, validate_evidence_reports=False)
    if checked[-1]["outcome"] != "accepted":
        refuse("WAI-E-PARITY.MUTATIONS", "$.manifest")
    evidence = _load_evidence_artifacts(root, manifest, validate_reports=False)
    families_record = validate_family_profiles(load_canonical_record(evidence["family_profiles"]))
    profiles = families_record["profiles"]
    for index, profile in enumerate(profiles):
        _verify_profile_identity(profile, f"$.profiles[{index}]")
    bootstrap = evidence["decoder_bootstrap"]
    template = evidence["parity_prompt"]
    corpus_digest = _corpus_sha256(manifest)
    correlation_id = _digest(
        (corpus_digest + _digest(evidence["family_profiles"]) + _digest(template) + _digest(bootstrap)).encode("ascii")
    )
    results: list[dict[str, Any]] = []
    refusal_codes: set[str] = set()
    passed_pairs = 0
    for profile_index, profile in enumerate(profiles):
        for fixture in manifest["fixtures"]:
            fixture_id = fixture["id"]
            source_file = read_confined(root, fixture["source"]["path"])
            start = _small_decimal(fixture["source"]["start"], "$.source.start", MAX_FILE_BYTES)
            end = _small_decimal(fixture["source"]["end"], "$.source.end", MAX_FILE_BYTES)
            source = source_file[start:end]
            # Projected, exactly as `_validate_parity_record` reads it back.
            compact = digest_neutral_projection(
                manifest,
                _load_bound_artifact(root, fixture["artifacts"]["compact"], f"$.fixtures.{fixture_id}.compact"),
            )
            questions_record = load_canonical_record(
                _load_bound_artifact(root, fixture["artifacts"]["questions"], f"$.fixtures.{fixture_id}.questions")
            )
            _validate_questions(questions_record, fixture_id)
            questions = questions_record["questions"]
            for question in questions:
                mode_records: dict[str, dict[str, Any]] = {}
                for mode, document, projection in (
                    ("source", source, MEASURED_PROJECTION_NONE),
                    ("compact", compact, MEASURED_PROJECTION_DIGEST_NEUTRAL),
                ):
                    prompt = _render_parity_prompt(template, mode, bootstrap, document, question)
                    job_id = _digest(
                        (correlation_id + profile["id"] + fixture_id + question["id"] + mode).encode("utf-8")
                    )
                    try:
                        prompt_tokens, response = _ollama_generate(
                            profile,
                            prompt,
                            parity=True,
                            path=f"$.profiles[{profile_index}].{fixture_id}.{question['id']}.{mode}",
                            answer_ids=[*question["accepted_answers"], *question["refusal_answers"]],
                        )
                        answer = _answer_record(response, question)
                    except CodecError as error:
                        answer = {"answer_id": None, "response": "", "outcome": "refused", "code": error.code}
                        prompt_tokens = 0
                    mode_records[mode] = {
                        "job_id": job_id,
                        "input_sha256": _digest(document),
                        "projection": projection,
                        "prompt_sha256": _digest(prompt),
                        "prompt_tokens": prompt_tokens,
                        **answer,
                    }
                source_answer = mode_records["source"]["answer_id"]
                compact_answer = mode_records["compact"]["answer_id"]
                required = question["required_answer"]
                pair_codes = {
                    item["code"] for item in mode_records.values() if item["code"] != "WAI-OK"
                }
                if source_answer != required or compact_answer != required:
                    pair_codes.add("WAI-E-PARITY.REQUIRED")
                if source_answer != compact_answer:
                    pair_codes.add("WAI-E-PARITY.MISMATCH")
                verdict = "accepted" if not pair_codes else "refused"
                if verdict == "accepted":
                    passed_pairs += 1
                refusal_codes.update(pair_codes)
                results.append(
                    {
                        "event": "parity.result",
                        "correlation_id": correlation_id,
                        "family_id": profile["id"],
                        "family": profile["family"],
                        "model": profile["model"],
                        "fixture_id": fixture_id,
                        "question_id": question["id"],
                        "required_answer": required,
                        "context_sha256": _digest(canonical_record_bytes(question["context"])),
                        "source": mode_records["source"],
                        "compact": mode_records["compact"],
                        "verdict": verdict,
                        "unknowns": [],
                        "refusal_codes": sorted(pair_codes),
                    }
                )
    for index, profile in enumerate(profiles):
        _verify_profile_identity(profile, f"$.profiles[{index}]")
    question_pairs = len(profiles) * FIXTURE_QUESTION_COUNT
    success = passed_pairs == question_pairs and not refusal_codes
    summary = {
        "event": "run.summary",
        "correlation_id": correlation_id,
        "case_count": len(results) * 2,
        "question_pair_count": len(results),
        "passed": passed_pairs,
        "failed": len(results) - passed_pairs,
        "refused": len(results) - passed_pairs,
        "unknown": 0,
        "verdict": "accepted" if success else "refused",
        "unknowns": [],
        "refusal_codes": sorted(refusal_codes),
    }
    report = {
        "schema": PARITY_SCHEMA,
        "correlation_id": correlation_id,
        "corpus_sha256": corpus_digest,
        "family_profiles_sha256": _digest(evidence["family_profiles"]),
        "family_ids": [profile["id"] for profile in profiles],
        "prompt_template_sha256": _digest(template),
        "bootstrap_sha256": _digest(bootstrap),
        "observed_on": profiles[0]["observed_on"],
        "results": results,
        "summary": summary,
    }
    return report, success


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
    for command in ("measure", "parity"):
        evidence_parser = subparsers.add_parser(command)
        evidence_parser.add_argument("--root", default=".")
        evidence_parser.add_argument("--manifest", required=True)
        evidence_parser.add_argument("--output", required=True)
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
        if arguments.command in ("measure", "parity"):
            input_bytes = read_confined(arguments.root, arguments.manifest)
            manifest_digest = _digest(input_bytes)
            if arguments.command == "measure":
                report, accepted = measure_manifest(arguments.root, arguments.manifest)
            else:
                report, accepted = parity_manifest(arguments.root, arguments.manifest)
            write_confined_atomic(
                arguments.root,
                arguments.output,
                canonical_record_bytes(report, allow_integers=True),
            )
            _emit(report["summary"])
            return 0 if accepted else 2
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
        # The record on stdout is the contract and does not change. A
        # refusal a reader cannot act on from its code alone also says so
        # here, where nothing parses.
        if error.detail is not None:
            print(f"agent_instruction: {error.detail}", file=sys.stderr)
        if arguments.command in ("check", "measure", "parity"):
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
