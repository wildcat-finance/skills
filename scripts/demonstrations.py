#!/usr/bin/env python3
"""Check the per-skill demonstration ledgers, rank the demo frontier, and run
the closed public demonstration set offline."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
import platform
import re
import resource
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shoggoth_topology import (  # noqa: E402
    TopologyError,
    _file_identity,
    _open_confined_directory,
    _open_regular_at,
    _safe_relpath,
    read as discover_topology,
)


LEDGER_NAME = "DEMONSTRATION.md"
FENCE_OPEN = "```shoggoth-demonstration"
FENCE_CLOSE = "```"
SCHEMA = "shoggoth-demonstration/v1"
SCHEMA_PATH = "schemas/shoggoth-demonstration-v1.json"
MAX_LEDGER_BYTES = 262_144
MAX_SCHEMA_BYTES = 262_144
MAX_SOURCE_BYTES = 33_554_432
# Per-source caps bound one read. A whole check reads every declared source, so
# the run needs its own ceiling or a large tree can ask for gigabytes before
# anything refuses. The budget is charged after each bounded read, so a run
# reads at most this plus one source.
MAX_RUN_SOURCE_BYTES = 268_435_456
MAX_SOURCES = 32
MAX_COMMANDS = 16
MAX_ARGV = 32
MAX_OBSERVATIONS = 32
MAX_JSON_DEPTH = 32

# The runner. Selection is a checked record or the closed public set; every
# argv runs without a shell under the interpreter `.python-version` pins, in a
# private work root, with an allowlisted environment and sockets denied.
REPORT_SCHEMA = "shoggoth-demonstration-report/v1"
PUBLIC_SET = (
    "anamnesis-corpus-demo",
    "lazarus-goldfinch-replay",
    "alexandria-credit-history-v0",
    "dokimasia-wildcat-app-v2-scrutiny",
)
PUBLIC_SET_CEILING_MS = 600_000
PYTHON_VERSION_PATH = ".python-version"
MAX_PYTHON_VERSION_BYTES = 64
MAX_OUTPUT_BYTES = 1_048_576
MAX_OUTPUT_TAIL = 2048
MAX_REPEAT = 10
WORK_TOKEN = "{work}"
HOOK_DIRECTORY = "site-hook"
NETWORK_MARKER = "network-attempt"
# The child sees these ambient keys and nothing else. There is no denylist to
# keep current: a credential or Git key is stripped by never being copied.
CHILD_ENVIRONMENT_KEYS = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE")
PYTHON_LAUNCHER = "python3"
# Interpreter options that would leave the child outside the socket denial.
# `-S` and `-I` skip `site`, so `sitecustomize` never runs; `-E` and `-I`
# ignore `PYTHONPATH`, so the hook directory is never on the path. Each one
# turns the denial off while the report still reads `python-site-hook`.
HOOK_DISABLING_OPTIONS = ("-S", "-E", "-I")
# CPython bundles short options, so `-Sc`, `-Ic` and `-EsSc` disable the hook
# exactly as the separate words do. Matching whole words alone let every
# bundle through, so the letter is what this looks for. A long option is not a
# bundle, which keeps `--specimen`, `--output` and `--check` admissible.
HOOK_DISABLING_LETTERS = frozenset("SEI")


def _disables_socket_hook(word: str) -> str | None:
    """Return the disabling letter in one argv word, or None.

    A short-option bundle carries its letters in one word, so the check reads
    the characters rather than comparing the whole word. Anything that is not
    a single-dash option word carries no interpreter option at all.
    """

    if not word.startswith("-") or word.startswith("--") or word == "-":
        return None
    for letter in word[1:]:
        if letter in HOOK_DISABLING_LETTERS:
            return letter
    return None


# Which argv word is the program is decided by CPython's option grammar, not
# by position. Reading `argv[1]` alone saw a program in `python3 prog.py` and
# nothing at all in `python3 -u prog.py`, so one benign flag carried a
# committed file past the declaration gate and past the pre-execution digest
# re-read. These four constants are the closed grammar the walk needs; a word
# it cannot place is refused rather than guessed at.
FLAG_ONLY_OPTION_LETTERS = frozenset("bBdhOPqRstuvVx")
OPTIONS_TAKING_ARGUMENT = frozenset(("-W", "-X", "--check-hash-based-pycs"))
PROGRAM_CARRYING_OPTIONS = frozenset(("-c", "-m"))
STDIN_PROGRAM = "-"
END_OF_OPTIONS = "--"


def classify_program(argv: list[str]) -> tuple[str, str | None]:
    """Say what one argv puts where the interpreter's program belongs.

    ``("file", path)`` names a committed file a source can declare and a
    digest can bind. ``("uncommitted", word)`` covers `-c`, `-m`, stdin and a
    `{work}` path, none of which is a committed file. ``("absent", None)``
    means the interpreter was given no work, and ``("unrecognised", word)``
    means an option word outside this closed grammar, which is refused rather
    than walked past.
    """

    index = 1
    while index < len(argv):
        word = argv[index]
        if word == END_OF_OPTIONS:
            index += 1
            break
        if word == STDIN_PROGRAM:
            return "uncommitted", word
        if not word.startswith("-"):
            break
        if word in PROGRAM_CARRYING_OPTIONS:
            return "uncommitted", word
        if word in OPTIONS_TAKING_ARGUMENT:
            index += 2
            continue
        if word.startswith("--") or not set(word[1:]) <= FLAG_ONLY_OPTION_LETTERS:
            return "unrecognised", word
        index += 1
    if index >= len(argv):
        return "absent", None
    program = argv[index]
    if WORK_TOKEN in program:
        return "uncommitted", program
    return "file", program


def _command_program(argv: list[str]) -> str | None:
    """Return the repository-relative file program one argv runs, or None."""

    kind, value = classify_program(argv)
    return value if kind == "file" else None
OBSERVATION_RE = re.compile(
    r"^(?P<command>[a-z][a-z0-9-]{0,63}): (?P<kind>line|json) (?P<rest>.+)$"
)
JSON_PATH_RE = re.compile(r"^(?P<path>[A-Za-z0-9_.-]+) (?P<value>.+)$")
POLL_SECONDS = 0.02
TEARDOWN_SECONDS = 5.0

STATUSES = ("real-data", "mixed", "constructed", "absent", "not-applicable")
EXECUTABLE_STATUSES = ("real-data", "mixed", "constructed")
PRESERVED_CLASSES = ("chain", "protocol", "repository", "audit", "production-run")
SYNTHETIC_CLASSES = ("fixture", "model-record")
SOURCE_CLASSES = PRESERVED_CLASSES + SYNTHETIC_CLASSES
FRONTIER_STATUSES = ("open", "mature")
NETWORK_POLICIES = ("denied", "allowlisted")

EXPECTED_RECORD_KEYS = (
    "schema",
    "skill",
    "plugin",
    "status",
    "claim_id",
    "claim",
    "non_claim",
    "network",
    "timeout_seconds",
    "sources",
    "commands",
    "observations",
    "frontier",
)
FRONTIER_KEYS = ("version", "status", "revision", "sha256", "current", "next")
SOURCE_KEYS = ("id", "class", "path", "sha256", "chain", "block", "anchor")
COMMAND_KEYS = ("id", "argv", "expect_exit")

IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
VERSION_RE = re.compile(r"^(?P<skill>[a-z][a-z0-9-]{0,63})-demo-v\d+\.\d+\.\d+$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
ANCHOR_RE = re.compile(r"^0x[0-9a-f]{64}$")

# One stable name per refusal condition. The policy carries this same catalogue
# and the tests compare both sets with every code used by the checker.
REFUSALS = {
    "D001": "ledger read boundary",
    "D002": "ledger UTF-8 boundary",
    "D003": "single record fence",
    "D004": "strict record JSON",
    "D005": "closed record fields",
    "D006": "record contract identifier",
    "D007": "record owner identity",
    "D008": "closed demonstration status",
    "D009": "claim identity and text",
    "D010": "closed network policy",
    "D011": "allowlisted network declaration",
    "D012": "per-command timeout",
    "D013": "bounded record collections",
    "D014": "observation text",
    "D015": "executable record completeness",
    "D016": "non-executable record emptiness",
    "D017": "real-data source purity",
    "D018": "mixed source composition",
    "D019": "constructed source purity",
    "D020": "source object and identity",
    "D021": "closed source class",
    "D022": "chain source identity",
    "D023": "file source identity",
    "D024": "confined source path",
    "D025": "bounded source read",
    "D026": "source digest agreement",
    "D027": "unique source ids",
    "D028": "whole-run source budget",
    "D030": "command object and identity",
    "D031": "bounded argv array",
    "D032": "expected command exit",
    "D033": "unique command ids",
    "D040": "demo version identity",
    "D041": "closed frontier status",
    "D042": "frontier text",
    "D043": "frontier status and next-job agreement",
    "D044": "frontier digest agreement",
    "D045": "absent demonstration cannot be mature",
    "D050": "unique public claim ids",
    "D060": "committed schema validation",
    "D070": "non-empty executable selection",
    "D071": "registered demonstration present and real-data",
    "D072": "command program present",
    "D073": "pinned interpreter",
    "D074": "sockets denied in children",
    "D075": "expected command exit",
    "D076": "per-command timeout and process-group teardown",
    "D077": "bounded command output",
    "D078": "checkable observation grammar",
    "D079": "declared observation holds",
    "D080": "contained new report path",
    "D081": "atomic report publication",
    "D082": "aggregate public-set ceiling",
    "D083": "private work root boundary",
    "D084": "declared command program",
    "D085": "process group escape",
}


@dataclass(frozen=True)
class GovernedSkill:
    """One governed directory derived from the topology reader."""

    id: str
    plugin_id: str
    directory: str


class _SchemaMismatch(ValueError):
    """One record does not satisfy the committed schema."""

STATUS_GAP = {
    "absent": 3,
    "constructed": 2,
    "mixed": 1,
    "real-data": 0,
}


class DemonstrationError(ValueError):
    """A demonstration ledger failed its closed boundary."""


def _fail(code: str, message: str) -> None:
    if code not in REFUSALS:
        raise RuntimeError(f"undeclared demonstration refusal {code}")
    raise DemonstrationError(f"{code} {message}")


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        _fail(code, message)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _refuse_deep(value: Any, depth: int = 0) -> None:
    if depth > MAX_JSON_DEPTH:
        raise ValueError(f"JSON nests deeper than {MAX_JSON_DEPTH} containers")
    if isinstance(value, dict):
        for item in value.values():
            _refuse_deep(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _refuse_deep(item, depth + 1)


def _read_regular_file(
    root: Path, relative: str | Path, *, maximum: int, label: str
) -> bytes:
    """Read one stable regular file through a confined descriptor walk."""

    safe = _safe_relpath(Path(relative).as_posix(), label=label)
    parts = safe.split("/")
    parent_fd = _open_confined_directory(root, parts[:-1])
    fd = -1
    try:
        fd = _open_regular_at(parent_fd, parts[-1], label=label)
        opened = os.fstat(fd)
        if opened.st_size > maximum:
            raise TopologyError(
                "file-oversized", f"{label} exceeds {maximum} bytes", safe
            )
        body = bytearray()
        while len(body) <= maximum:
            chunk = os.read(fd, min(65_536, maximum - len(body) + 1))
            if not chunk:
                break
            body.extend(chunk)
        if len(body) > maximum:
            raise TopologyError(
                "file-oversized", f"{label} exceeds {maximum} bytes", safe
            )
        closed = os.fstat(fd)
        try:
            named = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        except OSError as exc:
            raise TopologyError(
                "file-changed-during-read", f"{label} changed while it was read", safe
            ) from exc
        if not (
            _file_identity(opened)
            == _file_identity(closed)
            == _file_identity(named)
        ):
            raise TopologyError(
                "file-changed-during-read", f"{label} changed while it was read", safe
            )
        return bytes(body)
    except TopologyError:
        raise
    except OSError as exc:
        raise TopologyError(
            "unreadable-file", f"cannot read {label}: {exc}", safe
        ) from exc
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent_fd)


def governed_skills(root: Path) -> tuple[GovernedSkill, ...]:
    """Project the topology reader's exact governed-directory set."""

    topology = discover_topology(root)
    return tuple(
        GovernedSkill(
            id=directory.rsplit("/", 1)[-1],
            plugin_id=directory.split("/", 2)[1],
            directory=directory,
        )
        for directory in topology.governed
    )


def _schema_type(value: Any, declared: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
    }.get(declared, False)


def _schema_ref(schema: dict, reference: str) -> dict:
    prefix = "#/$defs/"
    if not reference.startswith(prefix) or "/" in reference[len(prefix):]:
        raise _SchemaMismatch(f"unsupported schema reference {reference!r}")
    target = schema.get("$defs", {}).get(reference[len(prefix):])
    if not isinstance(target, dict):
        raise _SchemaMismatch(f"unresolved schema reference {reference!r}")
    return target


def _validate_schema(
    value: Any, rule: dict, schema: dict, *, where: str, depth: int = 0
) -> None:
    """Validate the deliberately small JSON-Schema subset this contract uses."""

    if depth > MAX_JSON_DEPTH:
        raise _SchemaMismatch(f"{where} exceeds the schema depth cap")
    if "$ref" in rule:
        reference = rule["$ref"]
        if not isinstance(reference, str):
            raise _SchemaMismatch(f"{where} has a non-string schema reference")
        _validate_schema(value, _schema_ref(schema, reference), schema, where=where, depth=depth + 1)
        return
    if "oneOf" in rule:
        choices = rule["oneOf"]
        if not isinstance(choices, list) or not choices:
            raise _SchemaMismatch(f"{where} has an invalid oneOf rule")
        matches = 0
        for choice in choices:
            try:
                _validate_schema(value, choice, schema, where=where, depth=depth + 1)
            except _SchemaMismatch:
                continue
            matches += 1
        if matches != 1:
            raise _SchemaMismatch(f"{where} matches {matches} oneOf branches")
        return
    if "const" in rule and value != rule["const"]:
        raise _SchemaMismatch(f"{where} does not equal the schema constant")
    if "enum" in rule:
        choices = rule["enum"]
        if not isinstance(choices, list) or value not in choices:
            raise _SchemaMismatch(f"{where} is outside the schema enum")
    declared = rule.get("type")
    if declared is not None:
        if not isinstance(declared, str) or not _schema_type(value, declared):
            raise _SchemaMismatch(f"{where} is not schema type {declared!r}")
    if isinstance(value, dict):
        required = rule.get("required", [])
        properties = rule.get("properties", {})
        if not isinstance(required, list) or not isinstance(properties, dict):
            raise _SchemaMismatch(f"{where} has an invalid object schema")
        missing = sorted(set(required) - set(value))
        if missing:
            raise _SchemaMismatch(f"{where} is missing {missing}")
        unknown = sorted(set(value) - set(properties))
        if rule.get("additionalProperties") is False and unknown:
            raise _SchemaMismatch(f"{where} has unknown keys {unknown}")
        for key in sorted(set(value) & set(properties)):
            child = properties[key]
            if not isinstance(child, dict):
                raise _SchemaMismatch(f"{where}.{key} has an invalid schema")
            _validate_schema(value[key], child, schema, where=f"{where}.{key}", depth=depth + 1)
    if isinstance(value, list):
        minimum = rule.get("minItems")
        maximum = rule.get("maxItems")
        if isinstance(minimum, int) and len(value) < minimum:
            raise _SchemaMismatch(f"{where} has fewer than {minimum} items")
        if isinstance(maximum, int) and len(value) > maximum:
            raise _SchemaMismatch(f"{where} has more than {maximum} items")
        child = rule.get("items")
        if child is not None:
            if not isinstance(child, dict):
                raise _SchemaMismatch(f"{where} has an invalid items schema")
            for index, item in enumerate(value):
                _validate_schema(item, child, schema, where=f"{where}[{index}]", depth=depth + 1)
    if isinstance(value, str):
        minimum = rule.get("minLength")
        maximum = rule.get("maxLength")
        if isinstance(minimum, int) and len(value) < minimum:
            raise _SchemaMismatch(f"{where} is shorter than {minimum}")
        if isinstance(maximum, int) and len(value) > maximum:
            raise _SchemaMismatch(f"{where} is longer than {maximum}")
        pattern = rule.get("pattern")
        if pattern is not None:
            if not isinstance(pattern, str) or re.search(pattern, value) is None:
                raise _SchemaMismatch(f"{where} does not match {pattern!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        minimum = rule.get("minimum")
        maximum = rule.get("maximum")
        if isinstance(minimum, int) and value < minimum:
            raise _SchemaMismatch(f"{where} is below {minimum}")
        if isinstance(maximum, int) and value > maximum:
            raise _SchemaMismatch(f"{where} is above {maximum}")


def load_schema(root: Path) -> dict:
    """Read and pin the closed schema profile used by the checker."""

    try:
        raw = _read_regular_file(
            root, SCHEMA_PATH, maximum=MAX_SCHEMA_BYTES, label="demonstration schema"
        )
        schema = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        _refuse_deep(schema)
    except (OSError, UnicodeDecodeError, ValueError, TopologyError) as exc:
        _fail("D060", f"cannot read the committed schema: {exc}")
    _require(isinstance(schema, dict), "D060", "the committed schema is not an object")
    _require(schema.get("type") == "object", "D060", "the schema root is not an object")
    _require(
        schema.get("additionalProperties") is False,
        "D060",
        "the schema root is not closed",
    )
    properties = schema.get("properties")
    required = schema.get("required")
    _require(isinstance(properties, dict), "D060", "the schema has no property map")
    _require(isinstance(required, list), "D060", "the schema has no required list")
    expected = set(EXPECTED_RECORD_KEYS)
    _require(
        set(properties) == expected and set(required) == expected,
        "D060",
        "the schema does not carry the exact record field set",
    )
    definitions = schema.get("$defs")
    _require(isinstance(definitions, dict), "D060", "the schema has no definitions")
    for name in ("network", "fileSource", "chainSource", "command", "frontier"):
        entry = definitions.get(name)
        _require(
            isinstance(entry, dict) and entry.get("additionalProperties") is False,
            "D060",
            f"schema definition {name!r} is absent or open",
        )
    return schema


def _closed_object(value: Any, keys: tuple[str, ...], *, code: str, where: str) -> dict:
    _require(isinstance(value, dict), code, f"{where} is not an object")
    unknown = sorted(set(value) - set(keys))
    _require(not unknown, code, f"{where} has unknown key(s) {unknown}")
    return value


def _text(value: Any, *, code: str, where: str, maximum: int = 4096) -> str:
    _require(isinstance(value, str), code, f"{where} is not a string")
    _require(bool(value.strip()), code, f"{where} is empty")
    _require(len(value) <= maximum, code, f"{where} is over {maximum} characters")
    _require(value == value.strip(), code, f"{where} is not canonically trimmed")
    return value


def read_ledger(root: Path, directory: str) -> str:
    """Return one bounded ledger's text through no-follow descriptors."""

    relative = Path(directory) / LEDGER_NAME
    try:
        payload = _read_regular_file(
            root, relative, maximum=MAX_LEDGER_BYTES, label=str(relative)
        )
    except TopologyError as exc:
        _fail("D001", f"cannot read {relative}: {exc}")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail("D002", f"{relative} is not UTF-8: {exc}")
    raise AssertionError("unreachable")


def extract_record(text: str, *, where: str) -> dict:
    """Return the one fenced record object from a ledger's text."""

    lines = text.split("\n")
    opens = [index for index, line in enumerate(lines) if line == FENCE_OPEN]
    _require(len(opens) == 1, "D003", f"{where} must hold exactly one {FENCE_OPEN} fence")
    start = opens[0]
    closes = [
        index
        for index in range(start + 1, len(lines))
        if lines[index] == FENCE_CLOSE
    ]
    _require(bool(closes), "D003", f"{where} has an unterminated record fence")
    body = "\n".join(lines[start + 1:closes[0]])
    try:
        document = json.loads(body, object_pairs_hook=_reject_duplicate_keys)
        _refuse_deep(document)
    except ValueError as exc:
        _fail("D004", f"{where} has an invalid record: {exc}")
    _require(isinstance(document, dict), "D004", f"{where} record is not an object")
    return document


def _check_network(value: Any, *, where: str) -> None:
    network = _closed_object(
        value, ("policy", "endpoints", "secret_env"), code="D010", where=f"{where} network"
    )
    policy = _text(network.get("policy"), code="D010", where=f"{where} network.policy")
    _require(policy in NETWORK_POLICIES, "D010", f"{where} network.policy is {policy!r}")
    if policy == "denied":
        _require(
            "endpoints" not in network and "secret_env" not in network,
            "D010",
            f"{where} denies network yet names endpoints or secrets",
        )
        return
    endpoints = network.get("endpoints")
    _require(
        isinstance(endpoints, list) and bool(endpoints),
        "D011",
        f"{where} allowlists the network without naming endpoints",
    )
    for index, endpoint in enumerate(endpoints):
        target = _text(endpoint, code="D011", where=f"{where} network.endpoints[{index}]")
        _require(
            target.startswith("https://"),
            "D011",
            f"{where} network endpoint {target!r} is not https",
        )
    secrets = network.get("secret_env", [])
    _require(isinstance(secrets, list), "D011", f"{where} network.secret_env is not a list")
    for index, secret in enumerate(secrets):
        name = _text(secret, code="D011", where=f"{where} network.secret_env[{index}]")
        _require(
            re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", name) is not None,
            "D011",
            f"{where} network.secret_env[{index}] is not an environment name",
        )


class _Budget:
    """A mutable byte budget shared by every source read in one check."""

    def __init__(self, maximum: int = MAX_RUN_SOURCE_BYTES) -> None:
        self.remaining = maximum
        self.maximum = maximum

    def spend(self, size: int, *, where: str) -> None:
        self.remaining -= size
        if self.remaining < 0:
            _fail(
                "D028",
                f"{where} takes the run past its {self.maximum}-byte source budget",
            )


def _check_source(
    root: Path | None, source: Any, *, where: str, budget: "_Budget | None" = None
) -> str:
    entry = _closed_object(source, SOURCE_KEYS, code="D020", where=where)
    identifier = _text(entry.get("id"), code="D020", where=f"{where}.id")
    _require(
        IDENTIFIER_RE.fullmatch(identifier) is not None,
        "D020",
        f"{where}.id {identifier!r} is not an identifier",
    )
    source_class = _text(entry.get("class"), code="D021", where=f"{where}.class")
    _require(
        source_class in SOURCE_CLASSES,
        "D021",
        f"{where}.class is {source_class!r}, not one of {', '.join(SOURCE_CLASSES)}",
    )
    if source_class == "chain":
        chain = _text(entry.get("chain"), code="D022", where=f"{where}.chain")
        _require(
            IDENTIFIER_RE.fullmatch(chain) is not None,
            "D022",
            f"{where}.chain {chain!r} is not an identifier",
        )
        block = entry.get("block")
        _require(
            isinstance(block, int) and not isinstance(block, bool) and block >= 0,
            "D022",
            f"{where}.block is not a block height",
        )
        anchor = _text(entry.get("anchor"), code="D022", where=f"{where}.anchor")
        _require(
            ANCHOR_RE.fullmatch(anchor) is not None,
            "D022",
            f"{where}.anchor is not a 32-byte hex anchor",
        )
        _require(
            "path" not in entry and "sha256" not in entry,
            "D022",
            f"{where} is a chain source yet names a path",
        )
        return source_class
    _require(
        "chain" not in entry and "block" not in entry and "anchor" not in entry,
        "D023",
        f"{where} is a file source yet names a chain anchor",
    )
    path = _text(entry.get("path"), code="D023", where=f"{where}.path")
    digest = _text(entry.get("sha256"), code="D023", where=f"{where}.sha256")
    _require(
        DIGEST_RE.fullmatch(digest) is not None,
        "D023",
        f"{where}.sha256 is not a lowercase SHA-256",
    )
    relative = Path(path)
    _require(
        not relative.is_absolute() and ".." not in relative.parts,
        "D024",
        f"{where}.path {path!r} escapes the repository",
    )
    if root is None:
        return source_class
    try:
        payload = _read_regular_file(
            root, relative, maximum=MAX_SOURCE_BYTES, label=f"{where}.path"
        )
    except TopologyError as exc:
        _fail("D025", f"{where}.path cannot be read: {exc}")
    # Charge the budget with the bytes the no-follow read actually returned. A
    # size taken beforehand would have to follow the path, so a symlinked source
    # could spend the run's budget on a file this reader then refuses, and the
    # refusal would land on whichever honest record came next. The per-source cap
    # bounds the overrun to one source.
    if budget is not None:
        budget.spend(len(payload), where=where)
    observed = hashlib.sha256(payload).hexdigest()
    _require(
        observed == digest,
        "D026",
        f"{where}.path digest is {observed}, declared {digest}",
    )
    return source_class


def _check_command(command: Any, *, where: str) -> None:
    entry = _closed_object(command, COMMAND_KEYS, code="D030", where=where)
    identifier = _text(entry.get("id"), code="D030", where=f"{where}.id")
    _require(
        IDENTIFIER_RE.fullmatch(identifier) is not None,
        "D030",
        f"{where}.id {identifier!r} is not an identifier",
    )
    argv = entry.get("argv")
    _require(isinstance(argv, list) and bool(argv), "D031", f"{where}.argv is not a non-empty list")
    _require(len(argv) <= MAX_ARGV, "D031", f"{where}.argv holds over {MAX_ARGV} words")
    for index, word in enumerate(argv):
        value = _text(word, code="D031", where=f"{where}.argv[{index}]", maximum=512)
        _require(
            "\n" not in value and "\x00" not in value,
            "D031",
            f"{where}.argv[{index}] holds a control character",
        )
    exit_code = entry.get("expect_exit")
    _require(
        isinstance(exit_code, int)
        and not isinstance(exit_code, bool)
        and 0 <= exit_code <= 255,
        "D032",
        f"{where}.expect_exit is not an exit status",
    )


def frontier_digest(status: str, revision: str, current: str, following: str) -> str:
    """Return the digest over the exact demo frontier line, newline included."""

    line = f"{status}|{revision}|{current}|{following}\n"
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def _check_frontier(record: dict, *, where: str) -> dict:
    frontier = _closed_object(
        record.get("frontier"), FRONTIER_KEYS, code="D040", where=f"{where} frontier"
    )
    version = _text(frontier.get("version"), code="D040", where=f"{where} frontier.version")
    match = VERSION_RE.fullmatch(version)
    _require(match is not None, "D040", f"{where} frontier.version {version!r} is malformed")
    _require(
        match.group("skill") == record["skill"],
        "D040",
        f"{where} frontier.version names {match.group('skill')!r}, not {record['skill']!r}",
    )
    status = _text(frontier.get("status"), code="D041", where=f"{where} frontier.status")
    _require(status in FRONTIER_STATUSES, "D041", f"{where} frontier.status is {status!r}")
    revision = _text(frontier.get("revision"), code="D042", where=f"{where} frontier.revision")
    current = _text(frontier.get("current"), code="D042", where=f"{where} frontier.current")
    following = _text(frontier.get("next"), code="D042", where=f"{where} frontier.next")
    if status == "mature":
        _require(
            following == "None -- mature",
            "D043",
            f"{where} is mature yet holds a next demo job",
        )
    else:
        _require(
            following != "None -- mature",
            "D043",
            f"{where} is open yet holds no next demo job",
        )
    declared = _text(frontier.get("sha256"), code="D044", where=f"{where} frontier.sha256")
    computed = frontier_digest(status, revision, current, following)
    _require(
        declared == computed,
        "D044",
        f"{where} frontier.sha256 is {declared}, recomputed {computed}",
    )
    return frontier


def check_record(
    root: Path | None,
    skill: GovernedSkill,
    record: dict,
    *,
    verify_bytes: bool = True,
    budget: "_Budget | None" = None,
    schema: dict | None = None,
) -> dict:
    """Validate one record against the closed contract and return it.

    ``verify_bytes`` false checks structure alone and reads no declared source.
    """

    where = f"{skill.directory}/{LEDGER_NAME}"
    if schema is None:
        schema = load_schema(Path(__file__).resolve().parents[1])
    record_keys = tuple(schema["properties"])
    _closed_object(record, record_keys, code="D005", where=where)
    missing = sorted(set(schema["required"]) - set(record))
    _require(not missing, "D005", f"{where} is missing key(s) {missing}")
    _require(record.get("schema") == SCHEMA, "D006", f"{where} schema is not {SCHEMA}")
    _require(
        record.get("skill") == skill.id,
        "D007",
        f"{where} names skill {record.get('skill')!r}, not {skill.id!r}",
    )
    _require(
        record.get("plugin") == skill.plugin_id,
        "D007",
        f"{where} names plugin {record.get('plugin')!r}, not {skill.plugin_id!r}",
    )
    status = _text(record.get("status"), code="D008", where=f"{where} status")
    _require(status in STATUSES, "D008", f"{where} status is {status!r}")
    claim_id = _text(record.get("claim_id"), code="D009", where=f"{where} claim_id")
    _require(
        IDENTIFIER_RE.fullmatch(claim_id) is not None,
        "D009",
        f"{where} claim_id {claim_id!r} is not an identifier",
    )
    _text(record.get("claim"), code="D009", where=f"{where} claim")
    _text(record.get("non_claim"), code="D009", where=f"{where} non_claim")
    _check_network(record.get("network"), where=where)

    timeout = record.get("timeout_seconds")
    _require(
        isinstance(timeout, int) and not isinstance(timeout, bool) and 1 <= timeout <= 3600,
        "D012",
        f"{where} timeout_seconds is not between 1 and 3600",
    )

    sources = record.get("sources")
    commands = record.get("commands")
    observations = record.get("observations")
    _require(isinstance(sources, list), "D013", f"{where} sources is not a list")
    _require(isinstance(commands, list), "D013", f"{where} commands is not a list")
    _require(isinstance(observations, list), "D013", f"{where} observations is not a list")
    _require(len(sources) <= MAX_SOURCES, "D013", f"{where} holds over {MAX_SOURCES} sources")
    _require(len(commands) <= MAX_COMMANDS, "D013", f"{where} holds over {MAX_COMMANDS} commands")
    _require(
        len(observations) <= MAX_OBSERVATIONS,
        "D013",
        f"{where} holds over {MAX_OBSERVATIONS} observations",
    )

    seen_sources: set[str] = set()
    classes: list[str] = []
    for index, source in enumerate(sources):
        source_class = _check_source(
            root if verify_bytes else None,
            source,
            where=f"{where} sources[{index}]",
            budget=budget,
        )
        identifier = source["id"]
        _require(
            identifier not in seen_sources,
            "D027",
            f"{where} repeats source id {identifier!r}",
        )
        seen_sources.add(identifier)
        classes.append(source_class)

    seen_commands: set[str] = set()
    for index, command in enumerate(commands):
        _check_command(command, where=f"{where} commands[{index}]")
        identifier = command["id"]
        _require(
            identifier not in seen_commands,
            "D033",
            f"{where} repeats command id {identifier!r}",
        )
        seen_commands.add(identifier)

    for index, observation in enumerate(observations):
        _text(observation, code="D014", where=f"{where} observations[{index}]")

    if status in EXECUTABLE_STATUSES:
        _require(bool(sources), "D015", f"{where} is {status} yet names no source")
        _require(bool(commands), "D015", f"{where} is {status} yet names no command")
        _require(bool(observations), "D015", f"{where} is {status} yet names no observation")
    else:
        _require(not sources, "D016", f"{where} is {status} yet names a source")
        _require(not commands, "D016", f"{where} is {status} yet names a command")
        _require(not observations, "D016", f"{where} is {status} yet names an observation")

    synthetic = [name for name in classes if name in SYNTHETIC_CLASSES]
    preserved = [name for name in classes if name in PRESERVED_CLASSES]
    if status == "real-data":
        _require(
            not synthetic,
            "D017",
            f"{where} claims real-data with material {sorted(set(synthetic))} source(s)",
        )
    if status == "mixed":
        _require(
            bool(synthetic) and bool(preserved),
            "D018",
            f"{where} claims mixed without both a preserved and a constructed source",
        )
    if status == "constructed":
        _require(
            not preserved,
            "D019",
            f"{where} claims constructed with preserved {sorted(set(preserved))} source(s)",
        )

    # A registered public demonstration verifies the program it runs. Proving
    # the file exists says nothing about its bytes, so a report that recorded
    # `evidence: verified` for every input while the executable half went
    # undigested was source-drift over exactly the half that produced the
    # result. Declaring the program as a source is what puts it under the same
    # digest check as every other input, and this refusal is what keeps it
    # declared. The rule reads the record's own claim id, so it holds whether
    # the record is reached through `--public-set` or run singly.
    if claim_id in PUBLIC_SET:
        declared = {
            source["path"]
            for source in sources
            if isinstance(source, dict) and isinstance(source.get("path"), str)
        }
        for index, command in enumerate(commands):
            kind, word = classify_program(command["argv"])
            if kind == "unrecognised":
                _fail(
                    "D084",
                    f"{where} commands[{index}] puts {word!r} where its program belongs; "
                    "the digest binding cannot place that option word",
                )
            # `-c`, `-m`, stdin and a `{work}` path are not committed files, and
            # treating that as the end of it left the gate open: the runner's
            # working directory is the repository root, so `-m package.module`
            # and `-c "import module"` both put the repository on `sys.path` and
            # execute tracked files. The declaration gate saw an option word,
            # bound nothing, and the report carried an empty `programs` array
            # while a committed file ran. A registered public demonstration
            # therefore runs a committed file a source declares, and nothing
            # else reaches the interpreter's program position.
            if kind != "file":
                reached = word if word is not None else "no program"
                _fail(
                    "D084",
                    f"{where} commands[{index}] reaches its program through {reached!r}; "
                    "a registered public demonstration runs a committed file a source declares",
                )
            if word not in declared:
                _fail(
                    "D084",
                    f"{where} commands[{index}] runs {word!r}, which no source declares; "
                    "a registered public demonstration digests the program it runs",
                )

    frontier = _check_frontier(record, where=where)
    # A mature demo frontier says nothing worth doing remains. An absent record
    # says nothing exists yet. Together they retire a demonstration that was
    # never built, which is the one combination the status set must not admit.
    if status == "absent" and frontier["status"] == "mature":
        _fail("D045", f"{where} has no demonstration yet holds a mature demo frontier")
    try:
        _validate_schema(record, schema, schema, where=where)
    except _SchemaMismatch as exc:
        _fail("D060", f"{where} does not satisfy {SCHEMA_PATH}: {exc}")
    return record


def load_records(root: str | os.PathLike[str] = ".") -> dict[str, dict]:
    """Return every governed skill's validated record, keyed by directory."""

    repository = Path(os.path.abspath(os.fspath(root)))
    skills = governed_skills(repository)
    schema = load_schema(repository)
    records: dict[str, dict] = {}
    claim_ids: dict[str, str] = {}
    budget = _Budget()
    for skill in skills:
        text = read_ledger(repository, skill.directory)
        record = extract_record(text, where=f"{skill.directory}/{LEDGER_NAME}")
        checked = check_record(repository, skill, record, budget=budget, schema=schema)
        claim_id = checked["claim_id"]
        owner = claim_ids.get(claim_id)
        _require(
            owner is None,
            "D050",
            f"claim id {claim_id!r} is claimed by {owner} and {skill.directory}",
        )
        claim_ids[claim_id] = skill.directory
        records[skill.directory] = checked
    return records


def rank_demo_frontier(records: dict[str, dict]) -> list[dict]:
    """Return the eligible demo-frontier candidates in deterministic order."""

    eligible = [
        record
        for record in records.values()
        if record["frontier"]["status"] == "open" and record["status"] in STATUS_GAP
    ]
    return sorted(
        eligible,
        key=lambda record: (-STATUS_GAP[record["status"]], record["skill"]),
    )


def _emit_event(event: str, **fields: Any) -> None:
    """Emit one bounded, stable event as canonical JSON."""

    print(json.dumps({"event": event, **fields}, sort_keys=True, separators=(",", ":")))


def command_check(args: argparse.Namespace) -> int:
    records = load_records(args.root)
    counts = {status: 0 for status in STATUSES}
    for directory, record in sorted(records.items()):
        counts[record["status"]] += 1
        _emit_event(
            "demonstration.public_claim.checked",
            claim_id=record["claim_id"],
            directory=directory,
            skill=record["skill"],
            status=record["status"],
        )
    print(f"demonstrations {len(records)} record(s) under {SCHEMA}")
    for status in STATUSES:
        print(f"  {status:<15} {counts[status]}")
    return 0


def command_frontier(args: argparse.Namespace) -> int:
    records = load_records(args.root)
    ranked = rank_demo_frontier(records)
    print(f"lane      {args.lane}")
    print(f"read      {LEDGER_NAME} only")
    print(f"records   {len(records)}")
    print(f"eligible  {len(ranked)}")
    if not ranked:
        _emit_event(
            "demonstration.frontier.selection",
            eligible=0,
            lane=args.lane,
            outcome="none",
            records=len(records),
        )
        print("selected  none; every demo frontier is mature")
        return 0
    selected = ranked[0]
    _emit_event(
        "demonstration.frontier.selection",
        claim_id=selected["claim_id"],
        eligible=len(ranked),
        lane=args.lane,
        outcome="selected",
        plugin=selected["plugin"],
        skill=selected["skill"],
        status=selected["status"],
    )
    print(f"selected  {selected['plugin']}:{selected['skill']}")
    print(f"status    {selected['status']}")
    print(f"digest    {selected['frontier']['sha256']}")
    print(f"job       {selected['frontier']['next']}")
    print("result    read-only; nothing was filed, dispatched or written")
    return 0


# --- The runner -------------------------------------------------------------


@dataclass(frozen=True)
class Observation:
    """One parsed, checkable observation from a record."""

    text: str
    command: str
    kind: str
    line: str | None
    path: tuple[str, ...]
    value: Any


@dataclass
class CommandOutcome:
    """What one executed argv produced, bounded."""

    exit_code: int | None
    duration_ms: int
    stdout: bytes
    stderr: bytes
    stdout_truncated: bool
    stderr_truncated: bool
    timed_out: bool
    network_attempt: bool
    escaped_group: bool


class RunRefusal(DemonstrationError):
    """A refusal raised while running one demonstration."""

    def __init__(self, code: str, message: str) -> None:
        if code not in REFUSALS:
            raise RuntimeError(f"undeclared demonstration refusal {code}")
        super().__init__(f"{code} {message}")
        self.code = code
        self.message = message


def _refuse(code: str, message: str) -> None:
    raise RunRefusal(code, message)


def parse_observation(text: str, *, where: str) -> Observation:
    """Parse one observation into its command, channel, and expected value.

    Two forms are checkable: ``<command>: line <json-string>`` holds when that
    exact line appears on the command's stdout, and ``<command>: json <path>
    <json-value>`` holds when the command's last stdout line parses as JSON and
    the dotted path equals the value. Anything else is prose, not evidence.
    """

    match = OBSERVATION_RE.fullmatch(text)
    if match is None:
        _refuse("D078", f"{where} is not a checkable observation: {text!r}")
    command = match.group("command")
    kind = match.group("kind")
    rest = match.group("rest")
    if kind == "line":
        try:
            expected = json.loads(rest)
        except ValueError:
            expected = None
        if not isinstance(expected, str) or not expected or "\n" in expected:
            _refuse("D078", f"{where} line observation needs one JSON string")
        return Observation(text, command, kind, expected, (), None)
    inner = JSON_PATH_RE.fullmatch(rest)
    if inner is None:
        _refuse("D078", f"{where} json observation needs a path and a value")
    try:
        value = json.loads(inner.group("value"))
    except ValueError:
        _refuse("D078", f"{where} json observation value is not JSON")
    return Observation(
        text, command, kind, None, tuple(inner.group("path").split(".")), value
    )


def _json_lookup(document: Any, path: tuple[str, ...]) -> tuple[bool, Any]:
    current = document
    for part in path:
        if isinstance(current, dict):
            if part not in current:
                return False, None
            current = current[part]
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return False, None
            current = current[index]
        else:
            return False, None
    return True, current


def observation_holds(observation: Observation, stdout: bytes) -> bool:
    """Decide one observation against the bytes a command actually wrote."""

    text = stdout.decode("utf-8", errors="replace")
    lines = [line for line in text.split("\n") if line.strip()]
    if observation.kind == "line":
        return observation.line in lines
    if not lines:
        return False
    try:
        document = json.loads(lines[-1], object_pairs_hook=_reject_duplicate_keys)
        _refuse_deep(document)
    except ValueError:
        return False
    found, actual = _json_lookup(document, observation.path)
    return found and actual == observation.value


def pinned_python_version(root: Path) -> str:
    """Return the version `.python-version` pins, refusing an absent pin."""

    try:
        raw = _read_regular_file(
            root, PYTHON_VERSION_PATH, maximum=MAX_PYTHON_VERSION_BYTES,
            label="interpreter pin",
        )
        pinned = raw.decode("utf-8").strip()
    except (TopologyError, UnicodeDecodeError) as exc:
        _refuse("D073", f"cannot read {PYTHON_VERSION_PATH}: {exc}")
    if re.fullmatch(r"\d+\.\d+\.\d+", pinned) is None:
        _refuse("D073", f"{PYTHON_VERSION_PATH} does not pin one interpreter version")
    return pinned


def require_pinned_interpreter(root: Path) -> dict[str, str]:
    pinned = pinned_python_version(root)
    running = platform.python_version()
    if running != pinned:
        _refuse(
            "D073",
            f"interpreter {sys.executable} is {running}, not the pinned {pinned}",
        )
    return {"executable": sys.executable, "version": running, "pinned": pinned}


def resolve_report_target(report: str, output_root: Path) -> Path:
    """Resolve one new report path and prove it sits below the output root."""

    if not isinstance(report, str) or not report or "\x00" in report:
        _refuse("D080", "--report needs a non-empty path")
    supplied = Path(report)
    if ".." in supplied.parts:
        _refuse("D080", f"--report {report!r} traverses with '..'")
    try:
        root = output_root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        _refuse("D080", f"output root cannot be resolved: {exc}")
    lexical = supplied if supplied.is_absolute() else Path.cwd() / supplied
    try:
        target = lexical.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        _refuse("D080", f"--report cannot be resolved: {exc}")
    if target == root or root not in target.parents:
        _refuse("D080", f"--report {report!r} resolves outside the output root {root}")
    try:
        lexical.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        _refuse("D080", f"--report cannot be inspected: {exc}")
    else:
        _refuse("D080", f"--report {report!r} already exists")
    try:
        target.lstat()
    except FileNotFoundError:
        return target
    except OSError as exc:
        _refuse("D080", f"--report cannot be inspected: {exc}")
    _refuse("D080", f"--report {report!r} already exists")
    raise AssertionError("unreachable")


def _open_report_parent(output_root: Path, target: Path) -> int:
    """Open the report's parent through a no-follow walk from the output root.

    ``resolve_report_target`` proves containment against the path as it stood
    then; the run that follows takes seconds to minutes, and every byte written
    afterwards travels the path again by name. Walking down from the output
    root with each component opened without following a symlink is what binds
    the write to the directory that was actually checked, so a component
    replaced in that window refuses instead of publishing outside the root.
    """

    try:
        # `resolve_report_target` hands back a fully resolved path, so the root
        # is resolved the same way before the two are compared.
        root = output_root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        _refuse("D081", f"output root cannot be resolved: {exc}")
    try:
        parts = target.relative_to(root).parts[:-1]
    except ValueError:
        _refuse("D081", f"report {target} is not below the output root {root}")
    for depth in range(len(parts) + 1):
        try:
            fd = _open_confined_directory(root, parts[:depth])
        except TopologyError as exc:
            _refuse("D081", f"report parent is not confined below the output root: {exc}")
        if depth == len(parts):
            return fd
        try:
            os.mkdir(parts[depth], dir_fd=fd, mode=0o755)
        except FileExistsError:
            pass
        except OSError as exc:
            os.close(fd)
            _refuse("D081", f"report parent cannot be created: {exc}")
        os.close(fd)
    raise AssertionError("unreachable")


def publish_report(target: Path, payload: dict, output_root: Path) -> str:
    """Write the report beside its target and link it in without replacing.

    The body lands in a sibling ``.partial`` file first. ``os.link`` then
    publishes it under the final name and fails on an existing entry, so the
    target is either the complete object or absent; the partial is unlinked on
    every path, and a partial that survives an unlink failure keeps its
    visible ``.partial`` suffix. Both operations run against the parent
    descriptor ``_open_report_parent`` proved, never against the pathname.
    """

    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    parent_fd = _open_report_parent(output_root, target)
    partial = f".{target.name}.partial-{secrets.token_hex(8)}"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = -1
    try:
        try:
            fd = os.open(partial, flags, 0o600, dir_fd=parent_fd)
            remaining = memoryview(body)
            while remaining:
                written = os.write(fd, remaining)
                if written <= 0:
                    raise OSError("report write made no progress")
                remaining = remaining[written:]
            os.fsync(fd)
            os.close(fd)
            fd = -1
            # link() never follows the final component of its destination, so
            # an entry already standing there fails with EEXIST rather than
            # being replaced or followed out of the directory.
            os.link(partial, target.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        except OSError as exc:
            if fd >= 0:
                os.close(fd)
            try:
                os.unlink(partial, dir_fd=parent_fd)
            except OSError:
                pass
            _refuse("D081", f"report {target} was not published: {exc}")
        try:
            os.unlink(partial, dir_fd=parent_fd)
        except OSError:
            pass
    finally:
        os.close(parent_fd)
    return hashlib.sha256(body).hexdigest()


# The audit events the hook denies. `socket.__new__` fires inside the socket
# constructor itself, whichever name reached it, so it covers the type as well
# as the module attribute; the resolver events cover name lookup.
HOOK_AUDIT_PREFIX = "socket."


def _hook_source(marker: Path) -> str:
    """Return the `sitecustomize.py` one demonstration child loads.

    Rebinding `socket.socket` binds one name, and the type it displaced stays
    reachable from ordinary Python: `socket.socket.__mro__[2]` and
    `[c for c in object.__subclasses__() if c.__module__ == '_socket']` both
    hand back `_socket.socket`, which constructs a live kernel socket with
    nothing recorded and nothing raised. A CPython audit hook fires inside the
    constructor instead of at a name, so no handle on the type avoids it, and
    the interpreter exposes no way to remove a registered hook.

    The recorder is a closure local rather than a module global for the same
    reason: `_deny` looked `_record` up in this module's namespace, so a child
    that assigned `sitecustomize._record = lambda: None` opened a socket, was
    denied, exited 0 and was recorded as having attempted nothing. Every handle
    the denial needs is now bound by value and the names are deleted, so
    nothing the hook uses is left standing in the module for a child to
    reassign.
    """

    return (
        '"""Deny sockets in one demonstration child; written by demonstrations.py."""\n'
        "import os\n"
        "import sys\n"
        "import socket\n"
        "import _socket\n"
        f"MARKER = {str(marker)!r}\n"
        f"AUDIT_PREFIX = {HOOK_AUDIT_PREFIX!r}\n"
        "\n"
        "def _install(marker, prefix, base):\n"
        "    width = len(prefix)\n"
        "    # `record` must write the marker without allocating a descriptor at\n"
        "    # denial time. A child that exhausts its descriptor table before it\n"
        "    # trips the hook would make an `os.open` there fail, the write would\n"
        "    # be suppressed, and a denied socket would record nothing while the\n"
        "    # hook still raised. So the marker descriptor is opened once here,\n"
        "    # before the child runs any of its own code, and held; the write\n"
        "    # reuses it and needs no free slot, closing the exhaustion route and\n"
        "    # the descriptor-slot race a reopen-with-a-spare retry would leave.\n"
        "    # The parent arms a fresh marker before each command and each command\n"
        "    # is its own child, so the held descriptor names the armed file. A\n"
        "    # reopen fallback still covers a child that manages to close the held\n"
        "    # descriptor, since closing frees a slot rather than exhausting one.\n"
        "    held = [None]\n"
        "    try:\n"
        "        held[0] = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)\n"
        "    except OSError:\n"
        "        held[0] = None\n"
        "    def record():\n"
        "        if held[0] is not None:\n"
        "            try:\n"
        "                os.write(held[0], b'socket\\n')\n"
        "                return\n"
        "            except OSError:\n"
        "                pass\n"
        "        try:\n"
        "            fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)\n"
        "        except OSError:\n"
        "            return\n"
        "        try:\n"
        "            os.write(fd, b'socket\\n')\n"
        "        finally:\n"
        "            os.close(fd)\n"
        "    def deny(*args, **kwargs):\n"
        "        record()\n"
        "        raise PermissionError('demonstration network policy: sockets are denied')\n"
        "    def audit(event, args):\n"
        "        if event[:width] == prefix:\n"
        "            record()\n"
        "            raise PermissionError(\n"
        "                'demonstration network policy: sockets are denied (' + event + ')'\n"
        "            )\n"
        "    class DeniedSocket(base):\n"
        "        def __init__(self, *args, **kwargs):\n"
        "            deny()\n"
        "    sys.addaudithook(audit)\n"
        "    return deny, DeniedSocket\n"
        "\n"
        "_deny, _DeniedSocket = _install(MARKER, AUDIT_PREFIX, socket.socket)\n"
        "\n"
        "socket.socket = _DeniedSocket\n"
        "socket.SocketType = _DeniedSocket\n"
        "_socket.socket = _DeniedSocket\n"
        "for _name in ('create_connection', 'create_server', 'socketpair', 'fromfd',\n"
        "              'getaddrinfo', 'gethostbyname', 'gethostbyname_ex',\n"
        "              'gethostbyaddr', 'getnameinfo'):\n"
        "    setattr(socket, _name, _deny)\n"
        "    if hasattr(_socket, _name):\n"
        "        setattr(_socket, _name, _deny)\n"
        "# Every handle the denial needs is bound by value: the resolvers hold the\n"
        "# closure and `DeniedSocket.__init__` closes over it. Nothing is left in\n"
        "# this module for a child to reassign into the path of a denial.\n"
        "del _install, _deny, _name\n"
    )


class WorkRoot:
    """A private 0700 temporary root holding the hook, the marker, and {work}."""

    def __init__(self) -> None:
        try:
            self.path = Path(tempfile.mkdtemp(prefix="shoggoth-demonstration-"))
        except OSError as exc:
            _refuse("D083", f"private work root cannot be created: {exc}")
        self.work = self.path / "work"
        self.hook = self.path / HOOK_DIRECTORY
        self.marker = self.path / NETWORK_MARKER
        self.marker_identity: tuple | None = None
        try:
            self.work.mkdir(mode=0o700)
            self.hook.mkdir(mode=0o700)
            (self.hook / "sitecustomize.py").write_text(
                _hook_source(self.marker), encoding="utf-8"
            )
        except OSError as exc:
            self.remove()
            _refuse("D083", f"private work root cannot be prepared: {exc}")

    def network_attempted(self) -> bool:
        """Read the armed marker, treating its removal as the attempt it hides.

        The child runs as this user and knows the marker's directory, so it can
        unlink the evidence after the hook writes it. An armed marker that is
        gone, or that is a different file from the one that was armed, is
        therefore read as an attempt rather than as silence.
        """

        try:
            observed = self.marker.lstat()
        except FileNotFoundError:
            return self.marker_identity is not None
        except OSError:
            return True
        if self.marker_identity is not None:
            if _file_identity(observed) != self.marker_identity:
                return True
        return observed.st_size > 0

    def arm_marker(self) -> None:
        """Replace the marker with a fresh empty file and pin its identity."""

        self.marker_identity = None
        try:
            self.marker.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            return
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(self.marker, flags, 0o600)
        except OSError:
            return
        try:
            self.marker_identity = _file_identity(os.fstat(fd))
        finally:
            os.close(fd)

    def environment(self) -> dict[str, str]:
        env = {
            key: os.environ[key]
            for key in CHILD_ENVIRONMENT_KEYS
            if key in os.environ
        }
        # PYTHONPATH is the hook alone; the interpreter's own site, including
        # the pinned dependencies Lazarus installs there, stays reachable.
        env["PYTHONPATH"] = str(self.hook)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        return env

    def expand(self, argv: list[str]) -> list[str]:
        """Expand only the reserved {work} token; every other brace is literal."""

        return [word.replace(WORK_TOKEN, str(self.work)) for word in argv]

    def redact(self, text: str) -> str:
        return text.replace(str(self.work), WORK_TOKEN)

    def remove(self) -> bool:
        removed = True

        def _failed(*_args: object) -> None:
            nonlocal removed
            removed = False

        shutil.rmtree(self.path, onexc=_failed)
        return removed


def _drain(stream: Any, sink: bytearray, overflow: threading.Event) -> None:
    try:
        while True:
            chunk = os.read(stream.fileno(), 65_536)
            if not chunk:
                return
            room = MAX_OUTPUT_BYTES - len(sink)
            if len(chunk) > room:
                sink.extend(chunk[:room])
                overflow.set()
                return
            sink.extend(chunk)
    except (OSError, ValueError):
        return


def _kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        try:
            proc.kill()
        except OSError:
            pass


def execute_command(
    argv: list[str], *, cwd: Path, env: dict[str, str], timeout_ms: int,
    work: WorkRoot,
) -> CommandOutcome:
    """Run one argv without a shell, bounded by time and output, in its own group."""

    work.arm_marker()
    started = time.monotonic_ns()
    try:
        proc = subprocess.Popen(
            argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=True, close_fds=True,
        )
    except OSError as exc:
        _refuse("D072", f"command {argv[0]!r} could not start: {exc}")
    out, err = bytearray(), bytearray()
    out_over, err_over = threading.Event(), threading.Event()
    readers = (
        threading.Thread(target=_drain, args=(proc.stdout, out, out_over), daemon=True),
        threading.Thread(target=_drain, args=(proc.stderr, err, err_over), daemon=True),
    )
    for reader in readers:
        reader.start()
    deadline = started + timeout_ms * 1_000_000
    timed_out = False
    finished_ns: int | None = None
    escaped_group = False
    try:
        while proc.poll() is None:
            if out_over.is_set() or err_over.is_set():
                _kill_group(proc)
                break
            if time.monotonic_ns() > deadline:
                timed_out = True
                _kill_group(proc)
                break
            time.sleep(POLL_SECONDS)
        try:
            proc.wait(timeout=TEARDOWN_SECONDS)
        except subprocess.TimeoutExpired:
            _kill_group(proc)
            proc.wait()
        finished_ns = time.monotonic_ns()
    finally:
        # The command ends when its own process is reaped. Everything below is
        # teardown, and timing it as part of the command made a grandchild's
        # grip on the pipes the number the report recorded.
        if finished_ns is None:
            finished_ns = time.monotonic_ns()
        # Tear the group down on every path, not only on a timeout or an
        # overflow. A command that exits 0 after forking leaves the grandchild
        # holding the pipes and outliving the run that started it.
        _kill_group(proc)
        # The group is down, so nothing inside it holds the pipes. A reader
        # still blocked after the join is therefore held by a process that
        # left the group -- `setsid` in a grandchild is enough -- which is
        # outside the teardown this runner performs and is refused rather than
        # recorded as a clean command.
        for reader in readers:
            reader.join(timeout=TEARDOWN_SECONDS)
        escaped_group = any(reader.is_alive() for reader in readers)
        for stream in (proc.stdout, proc.stderr):
            try:
                stream.close()
            except OSError:
                pass
    duration_ms = (finished_ns - started) // 1_000_000
    return CommandOutcome(
        exit_code=proc.returncode,
        duration_ms=duration_ms,
        stdout=bytes(out),
        stderr=bytes(err),
        stdout_truncated=out_over.is_set(),
        stderr_truncated=err_over.is_set(),
        timed_out=timed_out,
        network_attempt=work.network_attempted(),
        escaped_group=escaped_group,
    )


def _children_max_rss_bytes() -> int:
    usage = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return usage if sys.platform == "darwin" else usage * 1024


def record_digest(record: dict) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _tail(payload: bytes, work: WorkRoot) -> str:
    text = payload[-MAX_OUTPUT_TAIL:].decode("utf-8", errors="replace")
    return work.redact(text)


def _source_evidence(source: dict) -> dict:
    if source["class"] == "chain":
        # A chain anchor is what the record declared. The runner has no chain
        # and proves nothing about it; the report says so rather than implying
        # a verification it never performed.
        return {
            "id": source["id"], "class": "chain", "chain": source["chain"],
            "block": source["block"], "anchor": source["anchor"],
            "evidence": "recorded",
        }
    return {
        "id": source["id"], "class": source["class"], "path": source["path"],
        "sha256": source["sha256"], "evidence": "verified",
    }


def preflight_record(
    root: Path, skill: GovernedSkill, record: dict
) -> tuple[list[Observation], dict[str, dict]]:
    """Refuse a record whose commands or observations cannot be executed as declared.

    Returns the parsed observations and, per command, what was established
    about the program it runs: `verified` when the bytes matched the digest a
    source declared, `found` when the record declares no source for them.
    """

    where = f"{skill.directory}/{LEDGER_NAME}"
    command_ids = {command["id"] for command in record["commands"]}
    declared_digests = {
        source["path"]: source["sha256"]
        for source in record["sources"]
        if isinstance(source, dict) and isinstance(source.get("path"), str)
    }
    programs: dict[str, dict] = {}
    for index, command in enumerate(record["commands"]):
        argv = command["argv"]
        # The execution boundary is the pinned interpreter, not whatever the
        # record names first. Anything else is resolved through PATH and runs
        # outside every control this runner claims: a shell interprets the rest
        # of the argv, and no non-Python child ever loads the socket hook.
        if argv[0] != PYTHON_LAUNCHER:
            _refuse(
                "D072",
                f"{where} commands[{index}] runs {argv[0]!r}; only {PYTHON_LAUNCHER} is admitted",
            )
        if len(argv) < 2:
            _refuse("D072", f"{where} commands[{index}] gives the interpreter no work")
        disabling = [
            (word, letter)
            for word, letter in ((word, _disables_socket_hook(word)) for word in argv[1:])
            if letter is not None
        ]
        if disabling:
            word, letter = disabling[0]
            _refuse(
                "D074",
                f"{where} commands[{index}] passes {word!r}, whose {letter!r} turns off "
                "the site hook that denies sockets",
            )
        kind, word = classify_program(argv)
        if kind == "absent":
            _refuse("D072", f"{where} commands[{index}] gives the interpreter no work")
        if kind == "unrecognised":
            _refuse(
                "D084",
                f"{where} commands[{index}] puts {word!r} where its program belongs; "
                "the digest binding cannot place that option word",
            )
        # The same closed rule the declaration gate applies, applied again on
        # the path that actually executes. `-m` and `-c` reach committed files
        # through the repository root this runner uses as its working
        # directory, so neither is a program a registered public demonstration
        # may run. The declaration half belongs here too: without it this
        # second layer refused the program's form and not its provenance, so an
        # undeclared committed file reached execution with its entry reading
        # `found` and `verify_command_program` returning without a comparison.
        # Nothing reaches this without `check_record`, which refuses first;
        # the two layers now apply the same rule rather than half of it.
        public = record.get("claim_id") in PUBLIC_SET
        if public and kind != "file":
            reached = word if word is not None else "no program"
            _refuse(
                "D084",
                f"{where} commands[{index}] reaches its program through {reached!r}; "
                "a registered public demonstration runs a committed file a source declares",
            )
        if public and word not in declared_digests:
            _refuse(
                "D084",
                f"{where} commands[{index}] runs {word!r}, which no source declares; "
                "a registered public demonstration digests the program it runs",
            )
        program = word if kind == "file" else None
        if program is not None:
            try:
                payload = _read_regular_file(
                    root, program, maximum=MAX_SOURCE_BYTES,
                    label=f"{where} commands[{index}] program",
                )
            except TopologyError as exc:
                _refuse(
                    "D072",
                    f"{where} commands[{index}] program {program!r} is absent: {exc}",
                )
            # The declaration is checked when the record is loaded; the digest
            # is compared again here, against the bytes this run is about to
            # execute. Loading and executing are separated by every other
            # record's read, so re-reading is what makes "verified before
            # execution" name this execution rather than the earlier check.
            observed = hashlib.sha256(payload).hexdigest()
            declared = declared_digests.get(program)
            if declared is None:
                programs[command["id"]] = {
                    "path": program, "sha256": observed, "evidence": "found",
                }
            elif observed != declared:
                _refuse(
                    "D084",
                    f"{where} commands[{index}] program {program!r} is {observed}, "
                    f"declared {declared}",
                )
            else:
                programs[command["id"]] = {
                    "path": program, "sha256": observed, "evidence": "verified",
                }
    observations = []
    for index, text in enumerate(record["observations"]):
        observation = parse_observation(text, where=f"{where} observations[{index}]")
        if observation.command not in command_ids:
            _refuse(
                "D078",
                f"{where} observations[{index}] names unknown command {observation.command!r}",
            )
        observations.append(observation)
    return observations, programs


def verify_command_program(root: Path, entry: dict | None, *, where: str) -> None:
    """Re-read one command's declared program in the moment before it runs.

    `preflight_record` reads every command's program once, before the record's
    first command executes. For a record carrying more than one command that
    leaves the later programs verified against a tree that the earlier commands
    have already had their turn with, so "verified before execution" named the
    record's execution rather than this command's. Reading again here is what
    makes the digest describe the bytes this command is about to run.

    What it does not do is close the window. The child reaches its program by
    pathname, so a writer that replaces the file between this read and the
    child's `execvp` runs undigested bytes while the entry still reads
    `verified`: a probe that swapped the bytes inside exactly that window ran
    the substituted program, and the run was refused by `D079` for the
    observation that then failed rather than by any digest check. Closing it
    needs the child to execute the descriptor this read holds, which changes
    what the program sees as its own path. The residual window is stated in
    `DEMONSTRATIONS.md` beside the other boundaries this runner does not hold.
    """

    if entry is None or entry["evidence"] != "verified":
        return
    try:
        payload = _read_regular_file(
            root, entry["path"], maximum=MAX_SOURCE_BYTES,
            label=f"{where} program",
        )
    except TopologyError as exc:
        _refuse(
            "D084",
            f"{where} program {entry['path']!r} could not be read as it ran: {exc}",
        )
    observed = hashlib.sha256(payload).hexdigest()
    if observed != entry["sha256"]:
        _refuse(
            "D084",
            f"{where} program {entry['path']!r} is {observed} as it runs, "
            f"verified {entry['sha256']}",
        )


class Runner:
    """Execute selected records and build one closed report."""

    def __init__(
        self, root: Path, *, correlation_id: str, repeat: int,
        ceiling_ms: int | None, work: WorkRoot,
    ) -> None:
        self.root = root
        self.correlation_id = correlation_id
        self.repeat = repeat
        self.ceiling_ms = ceiling_ms
        self.work = work
        self.aggregate_ms = 0
        self.started_ns = time.monotonic_ns()

    def _elapsed_ms(self) -> int:
        return (time.monotonic_ns() - self.started_ns) // 1_000_000

    def _budget_ms(self, timeout_seconds: int) -> int:
        timeout_ms = timeout_seconds * 1000
        if self.ceiling_ms is None:
            return timeout_ms
        remaining = self.ceiling_ms - self._elapsed_ms()
        if remaining <= 0:
            _refuse(
                "D082",
                f"the public set passed its {self.ceiling_ms} ms ceiling before every command ran",
            )
        return min(timeout_ms, remaining)

    def _run_command(
        self, skill: GovernedSkill, record: dict, command: dict,
        observations: list[Observation], repetition: int,
        program: dict | None = None,
    ) -> tuple[dict, tuple[str, str] | None]:
        where = f"{skill.directory}/{LEDGER_NAME} commands[{command['id']}]"
        argv = self.work.expand(command["argv"])
        if argv[0] == PYTHON_LAUNCHER:
            argv[0] = sys.executable
        verify_command_program(self.root, program, where=where)
        budget_ms = self._budget_ms(record["timeout_seconds"])
        _emit_event(
            "demonstration.started",
            claim_id=record["claim_id"],
            command=command["id"],
            correlation_id=self.correlation_id,
            repetition=repetition,
            skill=record["skill"],
            timeout_ms=budget_ms,
        )
        outcome = execute_command(
            argv, cwd=self.root, env=self.work.environment(), timeout_ms=budget_ms,
            work=self.work,
        )
        entry = {
            "id": command["id"],
            "argv": command["argv"],
            "exit": outcome.exit_code,
            "expect_exit": command["expect_exit"],
            "duration_ms": outcome.duration_ms,
            "timeout_ms": budget_ms,
            "stdout_bytes": len(outcome.stdout),
            "stderr_bytes": len(outcome.stderr),
            "stdout_sha256": hashlib.sha256(outcome.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(outcome.stderr).hexdigest(),
            "stdout_tail": _tail(outcome.stdout, self.work),
            "stderr_tail": _tail(outcome.stderr, self.work),
            "truncated": outcome.stdout_truncated or outcome.stderr_truncated,
            "timed_out": outcome.timed_out,
            "network_attempt": outcome.network_attempt,
            "escaped_group": outcome.escaped_group,
            "children_max_rss_bytes": _children_max_rss_bytes(),
        }
        refusal = None
        if outcome.network_attempt:
            refusal = ("D074", f"{where} opened or resolved a socket; the record denies the network")
        elif outcome.timed_out:
            refusal = (
                "D076",
                f"{where} exceeded its {budget_ms} ms budget; its process group was killed",
            )
        elif outcome.stdout_truncated or outcome.stderr_truncated:
            refusal = (
                "D077",
                f"{where} wrote past the {MAX_OUTPUT_BYTES}-byte output cap; output truncated",
            )
        elif outcome.escaped_group:
            refusal = (
                "D085",
                f"{where} left a process holding its pipes after its process group was "
                "killed, so something it started is outside this runner's teardown",
            )
        elif outcome.exit_code != command["expect_exit"]:
            refusal = (
                "D075",
                f"{where} exited {outcome.exit_code}, expected {command['expect_exit']}",
            )
        held = []
        for observation in observations:
            if refusal is not None or observation.command != command["id"]:
                continue
            if observation_holds(observation, outcome.stdout):
                held.append(observation.text)
            else:
                refusal = ("D079", f"{where} did not show {observation.text!r}")
        entry["observations"] = held
        entry["refusal"] = None if refusal is None else refusal[0]
        return entry, refusal

    def run_record(self, skill: GovernedSkill, record: dict) -> dict:
        report = {
            "directory": skill.directory,
            "skill": record["skill"],
            "plugin": record["plugin"],
            "claim_id": record["claim_id"],
            "status": record["status"],
            "claim": record["claim"],
            "non_claim": record["non_claim"],
            "demo_version": record["frontier"]["version"],
            "record_sha256": record_digest(record),
            "network": {
                "policy": record["network"]["policy"],
                "enforcement": "python-site-hook",
            },
            "timeout_seconds": record["timeout_seconds"],
            "sources": [_source_evidence(source) for source in record["sources"]],
            # What the run established about each command's own program, which
            # `sources` alone never covered: `verified` against a declared
            # digest, or `found` where the record declares none.
            "programs": [],
            "repetitions": [],
            "slowest_ms": 0,
            "result": "refused",
            "refusal": None,
        }
        try:
            if record["status"] not in EXECUTABLE_STATUSES:
                _refuse("D070", f"{skill.directory} is {record['status']} and runs nothing")
            if record["network"]["policy"] != "denied":
                _refuse(
                    "D074",
                    f"{skill.directory} allowlists the network; this run declares no capture exception",
                )
            observations, programs = preflight_record(self.root, skill, record)
            report["programs"] = [
                programs[command["id"]]
                for command in record["commands"]
                if command["id"] in programs
            ]
            for repetition in range(1, self.repeat + 1):
                commands: list[dict] = []
                run = {"index": repetition, "commands": commands, "duration_ms": 0}
                report["repetitions"].append(run)
                for command in record["commands"]:
                    entry, refusal = self._run_command(
                        skill, record, command, observations, repetition,
                        programs.get(command["id"]),
                    )
                    commands.append(entry)
                    run["duration_ms"] += entry["duration_ms"]
                    self.aggregate_ms += entry["duration_ms"]
                    report["slowest_ms"] = max(report["slowest_ms"], run["duration_ms"])
                    if refusal is not None:
                        _refuse(*refusal)
        except RunRefusal as exc:
            report["refusal"] = {"code": exc.code, "message": self.work.redact(exc.message)}
            _emit_event(
                "demonstration.refused",
                claim_id=record["claim_id"],
                code=exc.code,
                correlation_id=self.correlation_id,
                message=report["refusal"]["message"],
                skill=record["skill"],
            )
            return report
        report["result"] = "verified"
        _emit_event(
            "demonstration.verified",
            claim_id=record["claim_id"],
            correlation_id=self.correlation_id,
            repetitions=self.repeat,
            skill=record["skill"],
            slowest_ms=report["slowest_ms"],
        )
        return report


def select_records(
    records: dict[str, dict], skills: dict[str, GovernedSkill], *,
    public_set: bool, record_directory: str | None,
) -> list[tuple[GovernedSkill, dict]]:
    """Resolve the closed public set or one named record; nothing else."""

    if public_set:
        by_claim = {record["claim_id"]: directory for directory, record in records.items()}
        selected = []
        for claim_id in PUBLIC_SET:
            directory = by_claim.get(claim_id)
            if directory is None:
                _refuse("D071", f"registered public demonstration {claim_id!r} has no ledger")
            record = records[directory]
            if record["status"] != "real-data":
                _refuse(
                    "D071",
                    f"registered public demonstration {claim_id!r} is {record['status']}, not real-data",
                )
            selected.append((skills[directory], record))
        return selected
    directory = record_directory or ""
    if directory not in records:
        _refuse("D071", f"{directory!r} is not a governed demonstration ledger")
    return [(skills[directory], records[directory])]


def run_demonstrations(
    root: Path, selected: list[tuple[GovernedSkill, dict]], *, report: str,
    output_root: Path, repeat: int, ceiling_ms: int | None,
    correlation_id: str, interpreter: dict[str, str], mode: str,
) -> tuple[int, dict]:
    """Execute the selection, publish the report, and return the exit status."""

    target = resolve_report_target(report, output_root)
    executable = [
        (skill, record)
        for skill, record in selected
        if record["status"] in EXECUTABLE_STATUSES
    ]
    _emit_event(
        "demonstration.selected",
        claim_ids=[record["claim_id"] for _skill, record in executable],
        correlation_id=correlation_id,
        count=len(executable),
        mode=mode,
    )
    if not executable:
        _refuse("D070", f"the {mode} selection resolved to zero executable records")
    work = WorkRoot()
    try:
        runner = Runner(
            root, correlation_id=correlation_id, repeat=repeat,
            ceiling_ms=ceiling_ms, work=work,
        )
        demonstrations = []
        ceiling_refusal = None
        for skill, record in executable:
            demonstrations.append(runner.run_record(skill, record))
            if ceiling_ms is not None and runner.aggregate_ms > ceiling_ms:
                ceiling_refusal = {
                    "code": "D082",
                    "message": f"aggregate {runner.aggregate_ms} ms passed the {ceiling_ms} ms ceiling",
                }
                _emit_event(
                    "demonstration.refused",
                    code="D082",
                    correlation_id=correlation_id,
                    message=ceiling_refusal["message"],
                )
                break
        work_removed = work.remove()
    except BaseException:
        work.remove()
        raise
    refusals = [
        {"claim_id": entry["claim_id"], **entry["refusal"]}
        for entry in demonstrations
        if entry["refusal"] is not None
    ]
    if ceiling_refusal is not None:
        refusals.append(ceiling_refusal)
    complete = ceiling_refusal is None and len(demonstrations) == len(executable)
    status = "verified" if complete and not refusals else "refused"
    payload = {
        "schema": REPORT_SCHEMA,
        "correlation_id": correlation_id,
        "status": status,
        "selection": {
            "mode": mode,
            "count": len(executable),
            "claim_ids": [record["claim_id"] for _skill, record in executable],
        },
        "interpreter": interpreter,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "repeat": repeat,
        "ceiling_ms": ceiling_ms,
        "aggregate_ms": runner.aggregate_ms,
        "slowest_ms": max((entry["slowest_ms"] for entry in demonstrations), default=0),
        "work_root_removed": work_removed,
        "demonstrations": demonstrations,
        "refusals": refusals,
    }
    digest = publish_report(target, payload, output_root)
    _emit_event(
        "demonstration.report",
        correlation_id=correlation_id,
        path=str(target),
        sha256=digest,
        status=status,
    )
    return (0 if status == "verified" else 2), payload


def command_run(args: argparse.Namespace) -> int:
    root = Path(os.path.abspath(args.root))
    output_root = Path(os.path.abspath(args.output_root or args.root))
    correlation_id = secrets.token_hex(8)
    try:
        interpreter = require_pinned_interpreter(root)
        resolve_report_target(args.report, output_root)
        records = load_records(root)
        skills = {skill.directory: skill for skill in governed_skills(root)}
        selected = select_records(
            records, skills, public_set=args.public_set, record_directory=args.record
        )
        code, payload = run_demonstrations(
            root, selected, report=args.report, output_root=output_root,
            repeat=args.repeat,
            ceiling_ms=PUBLIC_SET_CEILING_MS if args.public_set else None,
            correlation_id=correlation_id, interpreter=interpreter,
            mode="public-set" if args.public_set else "record",
        )
    except RunRefusal as exc:
        _emit_event(
            "demonstration.refused",
            code=exc.code,
            correlation_id=correlation_id,
            message=exc.message,
        )
        raise
    except (DemonstrationError, TopologyError) as exc:
        # A ledger, schema or topology refusal reached during a run ends the
        # run as much as a RunRefusal does. Without this the correlation id is
        # minted, the operator sees no event at all, and the only trace of a
        # failed run is a line of stderr prose.
        _emit_event(
            "demonstration.refused",
            code=getattr(exc, "code", None) or str(exc).split(" ", 1)[0],
            correlation_id=correlation_id,
            message=str(exc),
        )
        raise
    print(f"demonstrations {payload['status']}: {payload['selection']['count']} record(s), "
          f"{payload['aggregate_ms']} ms aggregate over {args.repeat} repetition(s)")
    for entry in payload["demonstrations"]:
        line = f"  {entry['claim_id']:<36} {entry['result']:<9} slowest {entry['slowest_ms']} ms"
        if entry["refusal"] is not None:
            line += f"  {entry['refusal']['code']} {entry['refusal']['message']}"
        print(line)
    print(f"report    {args.report}")
    return code


def _repeat_count(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError("--repeat needs an integer") from None
    if not 1 <= value <= MAX_REPEAT:
        raise argparse.ArgumentTypeError(f"--repeat must be between 1 and {MAX_REPEAT}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demonstrations.py",
        description="check the governed demonstration ledgers and rank the demo frontier",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    checker = sub.add_parser("check", help="validate every governed ledger")
    checker.add_argument("--root", default=".", help="repository root")
    checker.set_defaults(handler=command_check)

    frontier = sub.add_parser("frontier", help="rank the demo frontier, read-only")
    frontier.add_argument("--root", default=".", help="repository root")
    frontier.add_argument("--lane", required=True, choices=("demo",))
    frontier.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="the only supported mode in this generation",
    )
    frontier.set_defaults(handler=command_frontier)

    runner = sub.add_parser("run", help="execute a checked record or the public set offline")
    runner.add_argument("--root", default=".", help="repository root")
    selection = runner.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--public-set", action="store_true", help="run the closed public demonstration set"
    )
    selection.add_argument(
        "--record", metavar="DIRECTORY", help="run one governed skill directory's record"
    )
    runner.add_argument(
        "--report", required=True, help="new report path below the output root"
    )
    runner.add_argument(
        "--output-root", default=None, help="declared output root; defaults to --root"
    )
    runner.add_argument(
        "--repeat", type=_repeat_count, default=1,
        help=f"repetitions per record, 1 to {MAX_REPEAT}; durations are observations",
    )
    runner.set_defaults(handler=command_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (DemonstrationError, TopologyError) as exc:
        print(f"demonstrations.py: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("demonstrations.py: interrupted; no report was published", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
