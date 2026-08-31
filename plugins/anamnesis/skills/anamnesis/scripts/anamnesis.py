#!/usr/bin/env python3
"""Anamnesis: custody of audit findings and the changes that answered them.

This version implements source admission. Curation and release are declared
boundaries that refuse by name and say which runbook step owes them.

The module reaches no network and imports nothing that could. Sources are read
as ordinary files, without following a symlink, under a declared byte cap, and
none of them is executed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import stat
import sys

POLICY_SCHEMA = "anamnesis-pilot-policy/v1"
REPORT_SCHEMA = "protasis-design-report/v1"
CANDIDATE = "anamnesis-member"

# Absolute ceilings. A policy may declare something smaller; it may not raise
# these. Metron owns the numbers, so they are named rather than inlined.
MAX_POLICY_BYTES = 1_000_000
MAX_SOURCE_BYTES_CEILING = 8_000_000
MAX_TOTAL_SOURCE_BYTES = 50_000_000
MAX_REPORT_BYTES = 64_000

# Bounded error output: a refusal quotes at most this much of any value it
# names, so a hostile source cannot flood an operator's terminal or a log.
MAX_QUOTED = 120

RIGHTS_BASES = ("licence", "permission", "contract", "digest-only")
DISCLOSURES = ("public", "restricted", "embargoed")
MEDIA_TYPES = ("text/markdown", "application/json", "text/plain")

POLICY_KEYS = {
    "schema": True,
    "policy_version": True,
    "engagement": True,
    "max_source_bytes": True,
    "sources": True,
    "records": True,
}
SOURCE_KEYS = {
    "id": True,
    "path": True,
    "sha256": True,
    "bytes": True,
    "media_type": True,
    "producer": True,
    "provenance": True,
    "rights": True,
}
PROVENANCE_KEYS = {
    "origin": True,
    "origin_path": True,
    "origin_commit": False,
    "retrieved": True,
}
RIGHTS_KEYS = {
    "basis": True,
    "disclosure": True,
    "holder": True,
    "statement": True,
    "expires": False,
}
RECORD_KEYS = {
    "id": True,
    "source": True,
    "native_id": True,
    "round": True,
}


class Refusal(Exception):
    """A fail-closed refusal carrying the rule that fired and what it fired on."""

    def __init__(self, code, message, record=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.record = record


def quote(value):
    """Bound any value before it reaches a message or an event."""
    text = str(value)
    if len(text) > MAX_QUOTED:
        return text[:MAX_QUOTED] + "..."
    return text


def correlation_id(policy_digest, record):
    """Deterministic correlation id.

    Derived from the policy bytes and the record it concerns, so two runs over
    the same inputs correlate identically and a release stays byte-identical.
    """
    seed = f"{policy_digest}:{record or '-'}".encode("utf-8")
    return hashlib.sha256(seed).hexdigest()[:16]


class Events:
    """A closed JSONL event stream, or a sink that keeps them in memory."""

    def __init__(self, path=None):
        self.path = path
        self.emitted = []

    def emit(self, name, policy_version, policy_digest, record, fields):
        event = {
            "event": name,
            "policy_version": policy_version,
            "record": record,
            "correlation_id": correlation_id(policy_digest, record),
        }
        event.update(fields)
        self.emitted.append(event)
        if self.path is not None:
            line = json.dumps(event, sort_keys=True, separators=(",", ":"))
            # Append without following a symlink: an operator-named stream path
            # is untrusted, and a link there would redirect every refusal we
            # write into a file we never meant to touch.
            flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(self.path, flags, 0o600)
            try:
                os.write(descriptor, (line + "\n").encode("utf-8"))
            finally:
                os.close(descriptor)


def read_bounded(path, cap, what):
    """Read a regular file without following a symlink, refusing above `cap`."""
    try:
        info = os.lstat(path)
    except OSError as error:
        raise Refusal("A001", f"{what} cannot be read: {quote(error.strerror)}")
    if stat.S_ISLNK(info.st_mode):
        raise Refusal("A002", f"{what} is a symlink: {quote(path)}")
    if not stat.S_ISREG(info.st_mode):
        raise Refusal("A003", f"{what} is not an ordinary file: {quote(path)}")
    if info.st_size > cap:
        raise Refusal(
            "A004", f"{what} is {info.st_size} bytes, above the {cap}-byte cap"
        )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        return os.read(descriptor, cap + 1)
    finally:
        os.close(descriptor)


def closed_object(value, keys, where):
    """Refuse an unknown key and a missing required one, in that order."""
    if not isinstance(value, dict):
        raise Refusal("A010", f"{where} is not an object")
    for key in value:
        if key not in keys:
            raise Refusal("A011", f"{where} has unknown key {quote(key)}")
    for key, required in keys.items():
        if required and key not in value:
            raise Refusal("A012", f"{where} is missing {quote(key)}")
    return value


def text(value, where, limit=500):
    if not isinstance(value, str) or not value or len(value) > limit:
        raise Refusal("A013", f"{where} is not a bounded non-empty string")
    return value


def _no_duplicate_keys(pairs):
    """Refuse a duplicated key rather than silently keeping the last one."""
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise Refusal("A025", f"policy declares {quote(key)} twice")
        seen[key] = value
    return seen


def parse_policy(raw, where):
    try:
        policy = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Refusal("A020", f"{where} is not valid JSON: {quote(error)}")
    closed_object(policy, POLICY_KEYS, "policy")
    if policy["schema"] != POLICY_SCHEMA:
        raise Refusal(
            "A021",
            f"policy schema is {quote(policy['schema'])}, not {POLICY_SCHEMA}",
        )
    text(policy["policy_version"], "policy_version", 100)
    text(policy["engagement"], "engagement", 200)
    cap = policy["max_source_bytes"]
    if not isinstance(cap, int) or isinstance(cap, bool) or not 0 < cap <= MAX_SOURCE_BYTES_CEILING:
        raise Refusal(
            "A022",
            f"max_source_bytes must be 1..{MAX_SOURCE_BYTES_CEILING}, got {quote(cap)}",
        )
    if not isinstance(policy["sources"], list) or not policy["sources"]:
        raise Refusal("A023", "policy declares no sources")
    if not isinstance(policy["records"], list) or not policy["records"]:
        raise Refusal("A024", "policy declares no records")
    return policy


def check_rights(rights, source_id):
    closed_object(rights, RIGHTS_KEYS, f"source {source_id} rights")
    basis = rights["basis"]
    if basis not in RIGHTS_BASES:
        raise Refusal(
            "A030",
            f"source {source_id} rights basis {quote(basis)} is not recognised; "
            "public visibility is not a rights basis",
            source_id,
        )
    disclosure = rights["disclosure"]
    if disclosure not in DISCLOSURES:
        raise Refusal(
            "A031",
            f"source {source_id} disclosure {quote(disclosure)} is not recognised",
            source_id,
        )
    if disclosure == "embargoed":
        raise Refusal(
            "A032", f"source {source_id} is embargoed and is refused at admission",
            source_id,
        )
    if basis == "digest-only" and disclosure == "public":
        raise Refusal(
            "A033",
            f"source {source_id} claims public disclosure under a digest-only basis; "
            "digest-only permits an identifier and a hash, not derived text",
            source_id,
        )
    text(rights["holder"], f"source {source_id} rights holder", 200)
    text(rights["statement"], f"source {source_id} rights statement", 500)
    return basis, disclosure


def resolve_within(root, relative, source_id):
    """Join `relative` under `root`, refusing escape and any symlink on the way."""
    if not relative or relative.startswith("/") or "\\" in relative:
        raise Refusal("A040", f"source {source_id} path is not relative", source_id)
    parts = [p for p in relative.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise Refusal("A041", f"source {source_id} path escapes the root", source_id)
    if not parts:
        raise Refusal("A040", f"source {source_id} path is empty", source_id)
    current = root
    for part in parts:
        current = os.path.join(current, part)
        try:
            info = os.lstat(current)
        except OSError:
            raise Refusal(
                "A042", f"source {source_id} path is missing: {quote(relative)}", source_id
            )
        if stat.S_ISLNK(info.st_mode):
            raise Refusal(
                "A043",
                f"source {source_id} path crosses a symlink at {quote(part)}",
                source_id,
            )
    return current


def admit_source(entry, root, cap, seen, events, policy_version, policy_digest):
    closed_object(entry, SOURCE_KEYS, "source")
    source_id = entry["id"]
    if not isinstance(source_id, str) or not source_id:
        raise Refusal("A050", "a source has no id")
    if source_id in seen:
        raise Refusal("A051", f"duplicate source id {quote(source_id)}", source_id)
    seen.add(source_id)

    if entry["media_type"] not in MEDIA_TYPES:
        raise Refusal(
            "A052",
            f"source {source_id} media type {quote(entry['media_type'])} is not recognised",
            source_id,
        )
    text(entry["producer"], f"source {source_id} producer", 200)
    closed_object(entry["provenance"], PROVENANCE_KEYS, f"source {source_id} provenance")
    basis, disclosure = check_rights(entry["rights"], source_id)

    declared = entry["bytes"]
    if not isinstance(declared, int) or isinstance(declared, bool) or declared < 0:
        raise Refusal("A053", f"source {source_id} byte count is not a count", source_id)
    if declared > cap:
        raise Refusal(
            "A054",
            f"source {source_id} declares {declared} bytes, above the {cap}-byte cap",
            source_id,
        )
    digest_declared = entry["sha256"]
    if not isinstance(digest_declared, str) or len(digest_declared) != 64:
        raise Refusal("A055", f"source {source_id} digest is malformed", source_id)

    path = resolve_within(root, entry["path"], source_id)
    payload = read_bounded(path, cap, f"source {source_id}")
    observed = len(payload)
    if observed != declared:
        raise Refusal(
            "A056",
            f"source {source_id} is {observed} bytes, not the declared {declared}",
            source_id,
        )
    digest_observed = hashlib.sha256(payload).hexdigest()
    if digest_observed != digest_declared:
        raise Refusal(
            "A057",
            f"source {source_id} digest is {quote(digest_observed)}, "
            f"not the declared {quote(digest_declared)}",
            source_id,
        )

    events.emit(
        "anamnesis.source.admitted",
        policy_version,
        policy_digest,
        source_id,
        {"bytes": observed, "sha256": digest_observed, "basis": basis,
         "disclosure": disclosure},
    )
    return {
        "id": source_id,
        "sha256": digest_observed,
        "bytes": observed,
        "basis": basis,
        "disclosure": disclosure,
    }


def admit(policy_path, events):
    """Admit every source a policy declares. Any refusal stops the whole run."""
    root = os.path.dirname(os.path.abspath(policy_path)) or "."
    raw = read_bounded(policy_path, MAX_POLICY_BYTES, "policy")
    policy_digest = hashlib.sha256(raw).hexdigest()
    policy = parse_policy(raw, "policy")
    version = policy["policy_version"]
    cap = policy["max_source_bytes"]

    seen = set()
    admitted = []
    total = 0
    for entry in policy["sources"]:
        try:
            result = admit_source(
                entry, root, cap, seen, events, version, policy_digest
            )
        except Refusal as refusal:
            events.emit(
                "anamnesis.source.refused",
                version,
                policy_digest,
                refusal.record,
                {"rule": refusal.code, "reason": refusal.message},
            )
            raise
        total += result["bytes"]
        if total > MAX_TOTAL_SOURCE_BYTES:
            raise Refusal(
                "A060",
                f"admitted sources exceed the {MAX_TOTAL_SOURCE_BYTES}-byte total cap",
            )
        admitted.append(result)

    known = {item["id"] for item in admitted}
    record_ids = set()
    for record in policy["records"]:
        closed_object(record, RECORD_KEYS, "record")
        record_id = record["id"]
        if not isinstance(record_id, str) or not record_id:
            raise Refusal("A070", "a record has no id")
        if record_id in record_ids:
            raise Refusal("A071", f"duplicate record id {quote(record_id)}", record_id)
        record_ids.add(record_id)
        if record["source"] not in known:
            raise Refusal(
                "A072",
                f"record {quote(record_id)} names unadmitted source "
                f"{quote(record['source'])}",
                record_id,
            )
        text(record["native_id"], f"record {record_id} native id", 100)
        text(record["round"], f"record {record_id} round", 200)

    if not 25 <= len(record_ids) <= 50:
        raise Refusal(
            "A073",
            f"the pilot declares {len(record_ids)} records; the runbook requires 25 to 50",
        )

    return {
        "policy_version": version,
        "policy_sha256": policy_digest,
        "sources": admitted,
        "records": len(record_ids),
        "total_bytes": total,
    }


def write_report(path, criterion, value, command):
    report = {
        "schema": REPORT_SCHEMA,
        "candidate": CANDIDATE,
        "criterion": criterion,
        "value": value,
        "unit": "boolean",
        "command": command,
        "exit": 0,
    }
    payload = json.dumps(report, indent=2) + "\n"
    encoded = payload.encode("utf-8")
    if len(encoded) > MAX_REPORT_BYTES:
        raise Refusal("A080", f"report exceeds the {MAX_REPORT_BYTES}-byte cap")
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    # Stage under a name this process alone creates, refusing to open through a
    # symlink or over an existing file, then promote atomically. A fixed
    # ".partial" suffix let a second run write into the first run's staging.
    staging = f"{path}.{os.getpid()}.{secrets.token_hex(8)}.partial"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(staging, flags, 0o600)
    try:
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    except BaseException:
        os.close(descriptor)
        os.unlink(staging)
        raise
    os.close(descriptor)
    os.replace(staging, path)
    return report


def cmd_admit(args):
    events = Events(args.events)
    result = admit(args.policy, events)
    print(
        f"admitted {len(result['sources'])} sources "
        f"({result['total_bytes']} bytes) and {result['records']} records "
        f"under policy {result['policy_version']}"
    )
    return 0


def cmd_admit_seed(args):
    events = Events(args.events)
    result = admit(args.policy, events)
    command = (
        "python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py admit-seed "
        f"--policy {args.policy} --report {args.report}"
    )
    write_report(args.report, "seed-source-rights-admitted", True, command)
    print(
        f"admitted {len(result['sources'])} sources and {result['records']} records; "
        f"wrote {args.report}"
    )
    return 0


def cmd_curate(args):
    raise Refusal(
        "A090",
        "curate is not implemented in anamnesis-v0.1.0; runbook step 2 owes the "
        "corpus graph, its closed schemas and its specimens",
    )


def cmd_release(args):
    raise Refusal(
        "A091",
        "release is not implemented in anamnesis-v0.1.0; runbook step 3 owes the "
        "deterministic release and its consumer projections",
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anamnesis",
        description=(
            "Preserve audit findings and their remedies as a source-bound corpus. "
            "This version implements source admission."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    admit_parser = sub.add_parser("admit", help="admit the sources a policy declares")
    admit_parser.add_argument("--policy", required=True)
    admit_parser.add_argument("--events", default=None)
    admit_parser.set_defaults(handler=cmd_admit)

    seed = sub.add_parser(
        "admit-seed", help="admit the pilot sources and write the conformance report"
    )
    seed.add_argument("--policy", required=True)
    seed.add_argument("--report", required=True)
    seed.add_argument("--events", default=None)
    seed.set_defaults(handler=cmd_admit_seed)

    curate = sub.add_parser("curate", help="not implemented; runbook step 2 owes it")
    curate.add_argument("--policy", default=None)
    curate.set_defaults(handler=cmd_curate)

    release = sub.add_parser("release", help="not implemented; runbook step 3 owes it")
    release.add_argument("--policy", default=None)
    release.set_defaults(handler=cmd_release)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except Refusal as refusal:
        print(f"refused [{refusal.code}] {refusal.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
