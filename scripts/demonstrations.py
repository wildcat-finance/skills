#!/usr/bin/env python3
"""Check the per-skill demonstration ledgers and rank the demo frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shoggoth_topology import (  # noqa: E402
    GovernedSkill,
    TopologyError,
    _read_regular_file,
    _reject_duplicate_keys,
    discover_topology,
)


LEDGER_NAME = "DEMONSTRATION.md"
FENCE_OPEN = "```shoggoth-demonstration"
FENCE_CLOSE = "```"
SCHEMA = "shoggoth-demonstration/v1"
MAX_LEDGER_BYTES = 262_144
MAX_SOURCE_BYTES = 33_554_432
# Per-source caps bound one read. A whole check reads every declared source in
# all 26 records, so the run needs its own ceiling or 26 records of 32 sources
# each can ask for gigabytes before anything refuses.
MAX_RUN_SOURCE_BYTES = 268_435_456
MAX_SOURCES = 32
MAX_COMMANDS = 16
MAX_ARGV = 32
MAX_OBSERVATIONS = 32

STATUSES = ("real-data", "mixed", "constructed", "absent", "not-applicable")
EXECUTABLE_STATUSES = ("real-data", "mixed", "constructed")
PRESERVED_CLASSES = ("chain", "protocol", "repository", "audit", "production-run")
SYNTHETIC_CLASSES = ("fixture", "model-record")
SOURCE_CLASSES = PRESERVED_CLASSES + SYNTHETIC_CLASSES
FRONTIER_STATUSES = ("open", "mature")
NETWORK_POLICIES = ("denied", "allowlisted")

RECORD_KEYS = (
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

STATUS_GAP = {
    "absent": 3,
    "constructed": 2,
    "mixed": 1,
    "real-data": 0,
}


class DemonstrationError(ValueError):
    """A demonstration ledger failed its closed boundary."""


def _fail(code: str, message: str) -> None:
    raise DemonstrationError(f"{code} {message}")


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        _fail(code, message)


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
        payload = _read_regular_file(root, relative, maximum=MAX_LEDGER_BYTES)
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
    if budget is not None:
        try:
            size = os.stat(os.path.join(root, relative)).st_size
        except OSError as exc:
            _fail("D025", f"{where}.path cannot be read: {exc}")
        budget.spend(size, where=where)
    try:
        payload = _read_regular_file(root, relative, maximum=MAX_SOURCE_BYTES)
    except TopologyError as exc:
        _fail("D025", f"{where}.path cannot be read: {exc}")
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
) -> dict:
    """Validate one record against the closed contract and return it.

    ``verify_bytes`` false checks structure alone and reads no declared source.
    """

    where = f"{skill.directory}/{LEDGER_NAME}"
    _closed_object(record, RECORD_KEYS, code="D005", where=where)
    missing = sorted(set(RECORD_KEYS) - set(record))
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
    return record


def load_records(root: str | os.PathLike[str] = ".") -> dict[str, dict]:
    """Return every governed skill's validated record, keyed by directory."""

    repository = Path(os.path.abspath(os.fspath(root)))
    topology = discover_topology(repository)
    records: dict[str, dict] = {}
    claim_ids: dict[str, str] = {}
    budget = _Budget()
    for skill in topology.governed_skills:
        text = read_ledger(repository, skill.directory)
        record = extract_record(text, where=f"{skill.directory}/{LEDGER_NAME}")
        checked = check_record(repository, skill, record, budget=budget)
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


def command_check(args: argparse.Namespace) -> int:
    records = load_records(args.root)
    counts = {status: 0 for status in STATUSES}
    for record in records.values():
        counts[record["status"]] += 1
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
        print("selected  none; every demo frontier is mature")
        return 0
    selected = ranked[0]
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
