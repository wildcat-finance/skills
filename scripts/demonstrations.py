#!/usr/bin/env python3
"""Check the per-skill demonstration ledgers and rank the demo frontier."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
import re
import sys
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (DemonstrationError, TopologyError) as exc:
        print(f"demonstrations.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
