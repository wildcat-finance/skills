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
import collections
import contextlib
import hashlib
import json
import os
import re
import secrets
import stat
import sys
import tempfile
import time

POLICY_SCHEMA = "anamnesis-pilot-policy/v1"
REPORT_SCHEMA = "protasis-design-report/v1"
RELEASE_SCHEMA = "anamnesis-release/v1"
CANDIDATE = "anamnesis-member"

# Absolute ceilings. A policy may declare something smaller; it may not raise
# these. Metron owns the numbers, so they are named rather than inlined.
MAX_POLICY_BYTES = 1_000_000
MAX_SOURCE_BYTES_CEILING = 8_000_000
MAX_TOTAL_SOURCE_BYTES = 50_000_000
MAX_REPORT_BYTES = 64_000
MAX_RELEASE_BYTES = 50_000_000

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
CURATION_POLICY_KEYS = {
    "version": True,
    "mapper": True,
    "taxonomy": True,
    "disclosure": True,
    "duplicates": False,
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
            raise Refusal("A025", f"the document declares {quote(key)} twice")
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
        "producer": entry["producer"],
        "path": entry["path"],
    }


@contextlib.contextmanager
def refusals_recorded(events, version, policy_digest):
    """Emit one durable refusal event for any refusal raised inside."""
    try:
        yield
    except Refusal as refusal:
        events.emit(
            "anamnesis.source.refused",
            version,
            policy_digest,
            refusal.record,
            {"rule": refusal.code, "reason": refusal.message},
        )
        raise


def validate_records(policy, known, events, version, policy_digest):
    """Check every declared record against the admitted sources."""
    record_ids = set()
    with refusals_recorded(events, version, policy_digest):
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
    return record_ids


def seed_scope(record_count):
    """The pilot's curation scope, which the runbook fixes at 25 to 50."""
    if not 25 <= record_count <= 50:
        raise Refusal(
            "A073",
            f"the pilot declares {record_count} records; the runbook requires 25 to 50",
        )


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
        with refusals_recorded(events, version, policy_digest):
            result = admit_source(
                entry, root, cap, seen, events, version, policy_digest
            )
        total += result["bytes"]
        if total > MAX_TOTAL_SOURCE_BYTES:
            raise Refusal(
                "A060",
                f"admitted sources exceed the {MAX_TOTAL_SOURCE_BYTES}-byte total cap",
            )
        admitted.append(result)

    known = {item["id"] for item in admitted}
    record_ids = validate_records(policy, known, events, version, policy_digest)
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
    seed_scope(result["records"])
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



# ---------------------------------------------------------------------------
# The mapper.
#
# Warden writes an audit round as Markdown. The shape has changed over time:
# the rounds preserved in the pilot predate the `Audit schema`, `Covered` and
# `Elenchus verdict` fields entirely. A missing field is recorded as unknown,
# never as none, because "this round declared no verdict" and "this round
# format had no verdict to declare" are different facts and only one of them
# is about the round.

MAPPER = {"name": "warden-audit-round-markdown", "version": "1"}

ROUND_HEADING = re.compile(
    r"^## (?P<label>.+?,\s*round\s*(?P<round>\d+))\s*--\s*(?P<date>.+?)\s*$"
)
OTHER_HEADING = re.compile(r"^## (?P<label>.+?)\s*$")
FINDING_ROW = re.compile(
    r"^\|\s*`?(?P<native>[A-Z]?\d*S?\d+-R\d+-\d+)`?\s*\|"
    r"\s*(?P<severity>[a-z-]+)\s*\|"
    r"\s*(?P<file>[^|]*?)\s*\|"
    r"\s*(?P<finding>.*?)\s*\|"
    r"\s*(?P<status>.*?)\s*\|$"
)
ROUND_FIELD = re.compile(
    r"^(?P<name>Audit schema|Covered|Not checked|Elenchus verdict):\s*(?P<value>.*)$"
)

# The remediation reference a status names. "fixed in this round" points at the
# round itself; "fixed in <sha>" points at a commit that may answer several
# findings, which is where one-fix-to-many-findings actually comes from.
FIXED_IN_COMMIT = re.compile(r"^fixed in `?(?P<ref>[0-9a-f]{7,40})`?\b")
FIXED_IN_ROUND = re.compile(r"^fixed in this round\b")
REJECTED = re.compile(r"^(rejected|invalid|not a finding)\b", re.I)
ACCEPTED = re.compile(r"^accepted\b", re.I)
OPEN = re.compile(r"^(open|carried forward|deferred)\b", re.I)

REMEDIATION_STATES = {
    "applied": "the source records a change that was made",
    "rejected": "the source records the finding as not accepted",
    "accepted-risk": "the source records the risk as accepted without a change",
    "unknown": "the source records no remediation state",
}
VERIFICATION_STATES = ("guarded", "unguarded", "passed", "inconclusive", "unknown")


def _strip_code(value):
    """Take a Markdown code span down to its contents, leaving other text alone."""
    stripped = value.strip()
    if len(stripped) > 1 and stripped.startswith("`") and stripped.endswith("`"):
        return stripped[1:-1]
    return stripped


def parse_source(text, source_id):
    """Read one Warden Markdown record into its native rounds and findings.

    Nothing here normalises: the round label, date and every finding field are
    the producer's own bytes. Curation reads this, and never the file again.
    """
    rounds = []
    current = None
    for number, line in enumerate(text.splitlines(), start=1):
        heading = ROUND_HEADING.match(line)
        if heading:
            current = {
                "id": f"round:{source_id}:{len(rounds) + 1}",
                "label": heading.group("label").strip(),
                "date": heading.group("date").strip(),
                "line": number,
                "fields": {},
                "findings": [],
            }
            rounds.append(current)
            continue
        if OTHER_HEADING.match(line):
            # A heading that is not a round closes the current one. The pilot
            # carries "## Leads closed since", which owns no findings.
            current = None
            continue
        if current is None:
            continue
        field = ROUND_FIELD.match(line)
        if field:
            current["fields"][field.group("name")] = field.group("value").strip()
            continue
        row = FINDING_ROW.match(line)
        if row and row.group("severity") not in {"---"}:
            current["findings"].append({
                "native_id": row.group("native"),
                "severity": row.group("severity"),
                "file": _strip_code(row.group("file")),
                "finding": row.group("finding").strip(),
                "status": row.group("status").strip(),
                "line": number,
            })
    return rounds


def read_status(status):
    """Classify a status line without discarding what it said.

    Returns the finding's own adjudication, the remediation state if the line
    records one, the reference that remediation is keyed by, and the verbatim
    basis.

    Two different facts live in this one column and they belong on different
    records. "fixed in 2429718" is a statement about a change, and several
    findings may name the same one. "rejected" and "accepted" are statements
    about the finding, and neither produces a remediation at all. Keying both
    off the round would collapse a rejection and a fix recorded in the same
    round into one record, which is exactly the loss the graph exists to
    prevent.

    `applied` is as far as any of these strings reach. A round saying it fixed
    something records a change, not a verification.
    """
    if FIXED_IN_ROUND.match(status):
        return "unknown", "applied", "this-round", status
    commit = FIXED_IN_COMMIT.match(status)
    if commit:
        return "unknown", "applied", commit.group("ref"), status
    if REJECTED.match(status):
        return "rejected", None, None, status
    if ACCEPTED.match(status):
        return "accepted-risk", None, None, status
    return "unknown", None, None, status


def check_duplicates(duplicates):
    """A duplicate cluster resolves to exactly one canonical finding."""
    if not isinstance(duplicates, dict):
        raise Refusal("A113", "policy duplicates is not a mapping")
    for reported, canonical_id in duplicates.items():
        if not isinstance(canonical_id, str) or not canonical_id:
            raise Refusal("A114", f"duplicate {quote(reported)} names no canonical finding")
        if canonical_id == reported:
            raise Refusal("A115", f"duplicate {quote(reported)} names itself")
        if canonical_id in duplicates:
            raise Refusal(
                "A116",
                f"duplicate {quote(reported)} points at {quote(canonical_id)}, which is "
                "itself a duplicate; a cluster resolves to one canonical finding",
            )
    return duplicates


def _assertion(kind, ident, source, line, native, state, basis, mapper):
    return {
        "id": ident,
        "kind": kind,
        "source": source,
        "locator": {"line": line},
        "native": native,
        "mapper": dict(mapper),
        "state": {"value": state, "basis": basis},
    }


def curate(admitted, policy, texts):
    """Build the graph from admitted sources.

    Submissions, findings, occurrences, remediations and verifications stay
    separate records joined by edges. A remediation named by several findings
    is one record with several edges, which is the whole point of keeping the
    edge many-to-many.
    """
    severities = set(policy["taxonomy"]["severities"])
    duplicates = check_duplicates(policy.get("duplicates", {}))
    derived_text = set(policy["disclosure"]["derived_text"])
    version = policy["version"]
    mapper = policy["mapper"]

    engagements, assertions, relations, quarantine, unknowns = [], [], [], [], {}

    def note_unknown(name):
        unknowns[name] = unknowns.get(name, 0) + 1

    for source in admitted:
        source_id = source["id"]
        speaks = source["disclosure"] in derived_text
        rounds = parse_source(texts[source_id], source_id)
        engagement = {
            "id": f"eng:{source_id}",
            "source": source_id,
            "producer": source["producer"],
            "rounds": [],
        }
        for entry in rounds:
            native_schema = entry["fields"].get("Audit schema")
            verdict = entry["fields"].get("Elenchus verdict")
            if native_schema is None:
                note_unknown("round.native_schema")
            if verdict is None:
                note_unknown("round.verdict")
            engagement["rounds"].append({
                "id": entry["id"],
                "label": entry["label"] if speaks else "",
                "date": entry["date"] if speaks else "",
                "findings": len(entry["findings"]),
                "native_schema": native_schema,
                "verdict": verdict,
            })
            verification_state = verdict if verdict in VERIFICATION_STATES else "unknown"
            if verdict is None:
                verification_basis = ""
            else:
                verification_basis = verdict
            verification_id = f"ver:{entry['id']}"
            assertions.append(_assertion(
                "verification", verification_id, source_id, entry["line"],
                {"round": entry["label"] if speaks else "", "declared": verdict},
                verification_state, verification_basis, mapper,
            ))

            for finding in entry["findings"]:
                native_id = finding["native_id"]
                if finding["severity"] not in severities:
                    quarantine.append({
                        "rule": "taxonomy-drift",
                        "subject": f"{source_id}:{native_id}",
                        "reason": (
                            f"severity {quote(finding['severity'])} is outside taxonomy "
                            f"{policy['taxonomy']['name']} {policy['taxonomy']['version']}"
                        ),
                    })
                    continue

                native = {
                    "native_id": native_id,
                    "severity": finding["severity"],
                    "file": finding["file"] if speaks else "",
                    "finding": finding["finding"] if speaks else "",
                    "status": finding["status"] if speaks else "",
                }
                if not speaks:
                    quarantine.append({
                        "rule": "restricted-derived-text",
                        "subject": f"{source_id}:{native_id}",
                        "reason": (
                            f"source disclosure {source['disclosure']} is not in the "
                            "policy's derived-text classes; identifiers and digests only"
                        ),
                    })

                submission_id = f"sub:{source_id}:{native_id}"
                reported_key = f"{source_id}:{native_id}"
                canonical_key = duplicates.get(reported_key, reported_key)
                finding_id = f"find:{canonical_key}"
                is_duplicate = canonical_key != reported_key
                assertions.append(_assertion(
                    "submission", submission_id, source_id, finding["line"],
                    dict(native), "unknown",
                    "the source records no adjudication of the submission", mapper,
                ))
                note_unknown("submission.adjudication")
                adjudication, remediation_state, ref, basis = read_status(
                    finding["status"] if speaks else "")
                if not is_duplicate:
                    assertions.append(_assertion(
                        "finding", finding_id, source_id, finding["line"],
                        dict(native), adjudication,
                        basis or "the source records no acceptance or rejection",
                        mapper,
                    ))
                    if adjudication == "unknown":
                        note_unknown("finding.adjudication")
                relations.append({
                    "id": f"rel:reported-as:{submission_id}",
                    "kind": "reported-as", "from": submission_id, "to": finding_id,
                    "policy_version": version,
                    "rationale": (
                        "the policy joined this submission to another submission's "
                        "canonical finding" if is_duplicate else
                        "one submission, adjudicated to itself"
                    ),
                })
                if is_duplicate:
                    note_unknown("submission.duplicate-of")
                    relations.append({
                        "id": f"rel:duplicate-of:{submission_id}",
                        "kind": "duplicate-of", "from": submission_id,
                        "to": f"sub:{canonical_key}",
                        "policy_version": version,
                        "rationale": (
                            "the duplicate keeps its own submission record; only the "
                            "canonical finding is shared"
                        ),
                    })

                if finding["file"] and speaks:
                    occurrence_id = f"occ:{source_id}:{native_id}"
                    assertions.append(_assertion(
                        "occurrence", occurrence_id, source_id, finding["line"],
                        {"file": finding["file"]}, "not-applicable",
                        "an occurrence has no lifecycle state of its own", mapper,
                    ))
                    relations.append({
                        "id": f"rel:occurs-at:{occurrence_id}",
                        "kind": "occurs-at", "from": finding_id, "to": occurrence_id,
                        "policy_version": version,
                    })

                if remediation_state is None:
                    note_unknown("finding.remediation")
                    continue
                key = ref if ref and ref != "this-round" else entry["id"]
                remediation_id = f"rem:{source_id}:{key}"
                assertions.append(_assertion(
                    "remediation", remediation_id, source_id, finding["line"],
                    {"reference": ref, "round": entry["id"]},
                    remediation_state, basis, mapper,
                ))
                relations.append({
                    "id": f"rel:addressed-by:{finding_id}:{remediation_id}",
                    "kind": "addressed-by", "from": finding_id, "to": remediation_id,
                    "policy_version": version,
                    "rationale": (
                        "the finding's status names this remediation; several findings "
                        "may name the same one"
                    ),
                })
                relations.append({
                    "id": f"rel:verified-by:{remediation_id}:{verification_id}",
                    "kind": "verified-by", "from": remediation_id, "to": verification_id,
                    "policy_version": version,
                    "rationale": (
                        "the round that recorded the remediation; its verdict is the "
                        "only verification evidence, and unknown when it declared none"
                    ),
                })
        engagements.append(engagement)

    seen_assertions = set()
    unique_assertions = []
    for assertion in assertions:
        if assertion["id"] in seen_assertions:
            continue
        seen_assertions.add(assertion["id"])
        unique_assertions.append(assertion)
    assertions = unique_assertions

    seen_relations = set()
    unique_relations = []
    for relation in relations:
        if relation["id"] in seen_relations:
            continue
        seen_relations.add(relation["id"])
        unique_relations.append(relation)

    return {
        "engagements": sorted(engagements, key=lambda e: e["id"]),
        "assertions": sorted(assertions, key=lambda a: (a["kind"], a["id"])),
        "relations": sorted(unique_relations, key=lambda r: (r["kind"], r["id"])),
        "quarantine": sorted(quarantine, key=lambda q: (q["rule"], q["subject"])),
        "unknowns": dict(sorted(unknowns.items())),
    }


def canonical(payload):
    """One byte form for a component, so two builds of the same graph agree."""
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def release_id(policy, admitted, graph):
    """Derived from the inputs and the policy, never from a clock."""
    digest = hashlib.sha256()
    digest.update(canonical(policy))
    for source in sorted(admitted, key=lambda s: s["id"]):
        digest.update(f"{source['id']}:{source['sha256']}:{source['bytes']}".encode("utf-8"))
    for key in ("engagements", "assertions", "relations", "quarantine", "unknowns"):
        digest.update(canonical(graph[key]))
    return digest.hexdigest()


def _counts(graph):
    """The denominators, computed one way so the build and verify agree."""
    kinds = collections.Counter(a["kind"] for a in graph["assertions"])
    rounds = [r for e in graph["engagements"] for r in e["rounds"]]
    return {
        "engagements": len(graph["engagements"]),
        "rounds": len(rounds),
        "rounds_with_no_findings": sum(1 for r in rounds if r["findings"] == 0),
        "submissions": kinds.get("submission", 0),
        "findings": kinds.get("finding", 0),
        "occurrences": kinds.get("occurrence", 0),
        "remediations": kinds.get("remediation", 0),
        "verifications": kinds.get("verification", 0),
        "relations": len(graph["relations"]),
    }


def _write_component(directory, name, payload, components):
    body = canonical(payload)
    target = os.path.join(directory, name)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(target, flags, 0o600)
    try:
        os.write(descriptor, body)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    components.append({
        "path": name,
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
    })


def build_release(out, policy, admitted, graph):
    """Stage a complete release, then promote it. A partial build never verifies.

    The staging directory is built beside the destination and moved into place
    only once every component is written, so a killed run leaves nothing that
    could be mistaken for a release.
    """
    if os.path.exists(out):
        raise Refusal("A100", f"release destination already exists: {quote(out)}")
    staging = f"{out}.{os.getpid()}.{secrets.token_hex(8)}.staging"
    os.makedirs(staging, exist_ok=False)
    try:
        components = []
        for name, payload in (
            ("engagements.json", graph["engagements"]),
            ("assertions.json", graph["assertions"]),
            ("relations.json", graph["relations"]),
            ("quarantine.json", graph["quarantine"]),
            ("unknowns.json", graph["unknowns"]),
            ("policy.json", policy),
        ):
            _write_component(staging, name, payload, components)

        manifest = {
            "schema": RELEASE_SCHEMA,
            "release_id": release_id(policy, admitted, graph),
            "policy": policy,
            "sources": [
                {"id": s["id"], "sha256": s["sha256"], "bytes": s["bytes"],
                 "disclosure": s["disclosure"]}
                for s in sorted(admitted, key=lambda s: s["id"])
            ],
            "components": sorted(components, key=lambda c: c["path"]),
            "counts": _counts(graph),
            "exclusions": graph["quarantine"],
            "unknowns": graph["unknowns"],
        }
        body = canonical(manifest)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(os.path.join(staging, "manifest.json"), flags, 0o600)
        try:
            os.write(descriptor, body)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.rename(staging, out)
        return manifest
    except BaseException:
        for name in sorted(os.listdir(staging)) if os.path.isdir(staging) else []:
            os.unlink(os.path.join(staging, name))
        if os.path.isdir(staging):
            os.rmdir(staging)
        raise


MANIFEST_KEYS = {
    "schema": True,
    "release_id": True,
    "policy": True,
    "sources": True,
    "components": True,
    "counts": True,
    "exclusions": True,
    "unknowns": True,
}
COMPONENT_KEYS = {"path": True, "sha256": True, "bytes": True}
MANIFEST_SOURCE_KEYS = {"id": True, "sha256": True, "bytes": True, "disclosure": True}


def check_manifest_shape(manifest):
    """Hold a release manifest to its closed shape before reading it.

    When a release arrives from somewhere else, its manifest is untrusted input
    like any other. Reading a field that is not there is a traceback, and a
    traceback is not a refusal: it names no rule and leaves the caller nothing
    to repair.
    """
    closed_object(manifest, MANIFEST_KEYS, "release manifest")
    if not isinstance(manifest["release_id"], str) or len(manifest["release_id"]) != 64:
        raise Refusal("A130", "release manifest id is malformed")
    for name, keys in (("components", COMPONENT_KEYS), ("sources", MANIFEST_SOURCE_KEYS)):
        entries = manifest[name]
        if not isinstance(entries, list) or not entries:
            raise Refusal("A131", f"release manifest {name} is not a non-empty list")
        seen = set()
        for entry in entries:
            closed_object(entry, keys, f"release manifest {name} entry")
            key = entry["path"] if name == "components" else entry["id"]
            if not isinstance(key, str) or not key:
                raise Refusal("A132", f"release manifest {name} entry has no name")
            if key in seen:
                raise Refusal("A133", f"release manifest {name} names {quote(key)} twice")
            seen.add(key)
            if not isinstance(entry["sha256"], str) or len(entry["sha256"]) != 64:
                raise Refusal("A134", f"release manifest {name} digest is malformed")
            size = entry["bytes"]
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                raise Refusal("A135", f"release manifest {name} byte count is not a count")
    for name in ("policy", "counts", "unknowns"):
        if not isinstance(manifest[name], dict):
            raise Refusal("A136", f"release manifest {name} is not an object")
    if not isinstance(manifest["exclusions"], list):
        raise Refusal("A137", "release manifest exclusions is not a list")
    return manifest


def verify_release(out):
    """Recompute every component digest from the bytes on disk."""
    manifest_path = os.path.join(out, "manifest.json")
    raw = read_bounded(manifest_path, MAX_POLICY_BYTES, "release manifest")
    try:
        manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Refusal("A101", f"release manifest is not valid JSON: {quote(error)}")
    if manifest.get("schema") != RELEASE_SCHEMA:
        raise Refusal("A102", "release manifest declares another schema")
    check_manifest_shape(manifest)

    listed = {c["path"] for c in manifest["components"]} | {"manifest.json"}
    present = set(os.listdir(out))
    if present != listed:
        missing = sorted(listed - present)
        extra = sorted(present - listed)
        raise Refusal(
            "A103",
            f"release contents differ from the manifest; missing={missing} extra={extra}",
        )
    bodies = {}
    for component in manifest["components"]:
        path = resolve_within(out, component["path"], component["path"])
        body = read_bounded(
            path, MAX_RELEASE_BYTES,
            f"release component {component['path']}",
        )
        if len(body) != component["bytes"]:
            raise Refusal(
                "A104",
                f"component {quote(component['path'])} is {len(body)} bytes, "
                f"not the manifested {component['bytes']}",
            )
        actual = hashlib.sha256(body).hexdigest()
        if actual != component["sha256"]:
            raise Refusal(
                "A105",
                f"component {quote(component['path'])} digest is {quote(actual)}, "
                f"not the manifested {quote(component['sha256'])}",
            )
        bodies[component["path"]] = body
    checked_bodies = bodies

    # The manifest is not covered by its own digest, so its claims are checked
    # against the components instead. Without this, editing a count or dropping
    # an exclusion passes verification untouched.
    try:
        graph = {
            "engagements": json.loads(bodies["engagements.json"]),
            "assertions": json.loads(bodies["assertions.json"]),
            "relations": json.loads(bodies["relations.json"]),
            "quarantine": json.loads(bodies["quarantine.json"]),
            "unknowns": json.loads(bodies["unknowns.json"]),
        }
        policy = json.loads(bodies["policy.json"])
    except (KeyError, json.JSONDecodeError) as error:
        raise Refusal("A108", f"release components are not readable: {quote(error)}")

    recomputed = release_id(policy, manifest["sources"], graph)
    if recomputed != manifest["release_id"]:
        raise Refusal(
            "A109",
            f"manifest release id is {quote(manifest['release_id'])}, but its "
            f"components and sources produce {quote(recomputed)}",
        )
    if manifest["policy"] != policy:
        raise Refusal("A117", "manifest policy differs from the released policy component")
    if manifest["exclusions"] != graph["quarantine"]:
        raise Refusal("A118", "manifest exclusions differ from the released quarantine")
    if manifest["unknowns"] != graph["unknowns"]:
        raise Refusal("A123", "manifest unknowns differ from the released unknowns")
    if manifest["counts"] != _counts(graph):
        raise Refusal("A119", "manifest counts differ from the released components")
    return manifest, checked_bodies


def measure_release(out):
    """Total the release bytes, which is what the byte cap is about."""
    total = 0
    for name in sorted(os.listdir(out)):
        info = os.lstat(os.path.join(out, name))
        if not stat.S_ISREG(info.st_mode):
            raise Refusal("A106", f"release holds a non-regular entry: {quote(name)}")
        total += info.st_size
    return total


def load_curation_policy(path):
    raw = read_bounded(path, MAX_POLICY_BYTES, "curation policy")
    try:
        policy = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Refusal("A110", f"curation policy is not valid JSON: {quote(error)}")
    closed_object(policy, CURATION_POLICY_KEYS, "curation policy")
    closed_object(policy["mapper"], {"name": True, "version": True}, "policy mapper")
    closed_object(policy["taxonomy"],
                  {"name": True, "version": True, "severities": True}, "policy taxonomy")
    closed_object(policy["disclosure"], {"derived_text": True}, "policy disclosure")
    text(policy["version"], "policy version", 100)
    if not isinstance(policy["taxonomy"]["severities"], list) or not policy["taxonomy"]["severities"]:
        raise Refusal("A111", "policy taxonomy declares no severities")
    for value in policy["disclosure"]["derived_text"]:
        if value not in DISCLOSURES:
            raise Refusal("A112", f"policy names unknown disclosure class {quote(value)}")
    check_duplicates(policy.get("duplicates", {}))
    return policy


def _admitted_texts(policy_path, admitted):
    """Read the admitted bytes again, and re-check them against admission.

    Admission verifies a digest and then returns. Curation reads the files a
    second time, so the bytes it curates are not the bytes admission checked
    unless it checks them itself. Every read here is compared against the
    digest and byte count admission recorded.
    """
    root = os.path.dirname(os.path.abspath(policy_path)) or "."
    texts = {}
    for source in admitted:
        path = resolve_within(root, source["path"], source["id"])
        payload = read_bounded(
            path, MAX_SOURCE_BYTES_CEILING, f"source {source['id']}")
        if len(payload) != source["bytes"]:
            raise Refusal(
                "A120",
                f"source {source['id']} changed between admission and curation: "
                f"{len(payload)} bytes, not the admitted {source['bytes']}",
                source["id"],
            )
        digest = hashlib.sha256(payload).hexdigest()
        if digest != source["sha256"]:
            raise Refusal(
                "A121",
                f"source {source['id']} changed between admission and curation: "
                f"digest {quote(digest)}, not the admitted {quote(source['sha256'])}",
                source["id"],
            )
        try:
            texts[source["id"]] = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise Refusal(
                "A122",
                f"source {source['id']} is not valid UTF-8: {quote(error.reason)}",
                source["id"],
            )
    return texts



# ---------------------------------------------------------------------------
# The consumer projections.
#
# Each consumer reads one closed, versioned, read-only view. The views are
# narrow on purpose: the Elenchus projection has no field a verdict could
# occupy, so a past `guarded` result cannot travel through it into a present
# case, and the Synkrisis projection carries every denominator so a count
# cannot be read as a claim about records the corpus never saw.
#
# Restricted material crosses neither. ADR-003 admits a restricted source for
# preservation under an identifier and a digest; it does not admit it onward.

ANALOGUE_SCHEMA = "anamnesis-elenchus-analogue/v1"
OBSERVATION_SCHEMA = "anamnesis-synkrisis-observation/v1"

ANALOGUE_NOT_ESTABLISHED = (
    "An analogue is a past case that looks similar. It does not establish a "
    "cause for the present failure, that the present failure is the same "
    "defect, or that any remedy recorded here would work again. Elenchus must "
    "still reproduce the present failure and still earn its own guard."
)
OBSERVATION_NOT_ESTABLISHED = (
    "Every count here is a count of the records this release holds. It does not "
    "establish how common anything is outside them, that the corpus is "
    "complete, or that an excluded record was rightly excluded."
)
PUBLIC_ONLY = "public"


def _release_graph(out):
    """Take a verified release's components from the bytes verification read.

    Reading them again would mean projecting bytes nobody checked: verification
    would pass on one read and the adapter would speak from another. The checked
    bodies are returned instead, so there is no second read to go stale.
    """
    manifest, bodies = verify_release(out)
    return manifest, {name: json.loads(body) for name, body in bodies.items()}


def _public_sources(manifest):
    """The sources a projection may speak about at all."""
    return {s["id"] for s in manifest["sources"] if s["disclosure"] == PUBLIC_ONLY}


def analogues(out, kind, value):
    """The Elenchus view: source-linked analogues and no verdict."""
    if kind not in ("file", "severity", "native-id"):
        raise Refusal("A140", f"unknown analogue query kind {quote(kind)}")
    if not value:
        raise Refusal("A141", "an analogue query needs a value")
    manifest, parts = _release_graph(out)
    speakable = _public_sources(manifest)
    assertions = parts["assertions.json"]
    relations = parts["relations.json"]

    remediation_by_id = {
        a["id"]: a for a in assertions if a["kind"] == "remediation"}
    addressed = {}
    for relation in relations:
        if relation["kind"] == "addressed-by":
            addressed.setdefault(relation["from"], []).append(relation["to"])

    found = []
    for assertion in assertions:
        if assertion["kind"] != "finding":
            continue
        if assertion["source"] not in speakable:
            continue
        native = assertion["native"]
        if kind == "file" and native.get("file") != value:
            continue
        if kind == "severity" and native.get("severity") != value:
            continue
        if kind == "native-id" and native.get("native_id") != value:
            continue
        remediations = []
        for remediation_id in sorted(addressed.get(assertion["id"], [])):
            record = remediation_by_id.get(remediation_id)
            if record is None:
                continue
            state = record["state"]["value"]
            # A verification state has no route into this view. If one ever
            # reached a remediation record, refuse rather than pass it on.
            if state not in ("proposed", "applied", "released", "deployed",
                             "reverted", "unknown"):
                raise Refusal(
                    "A142",
                    f"remediation {quote(remediation_id)} carries state "
                    f"{quote(state)}, which an analogue may not report",
                )
            remediations.append({
                "id": remediation_id,
                "state": state,
                "basis": record["state"]["basis"],
            })
        found.append({
            "finding": assertion["id"],
            "source": assertion["source"],
            "native_id": native.get("native_id", ""),
            "severity": native.get("severity", ""),
            "locator": dict(assertion["locator"]),
            "remediations": remediations,
            "adjudication": assertion["state"]["value"],
        })

    return {
        "schema": ANALOGUE_SCHEMA,
        "release_id": manifest["release_id"],
        "query": {"kind": kind, "value": value},
        "analogues": sorted(found, key=lambda a: a["finding"]),
        "verdict": None,
        "not_established": ANALOGUE_NOT_ESTABLISHED,
    }


def observations(out, cohort_rule):
    """The Synkrisis view: one cohort, with every denominator it needs."""
    if not cohort_rule:
        raise Refusal("A143", "an observation needs a stated cohort rule")
    manifest, parts = _release_graph(out)
    speakable = _public_sources(manifest)
    assertions = parts["assertions.json"]

    members = sorted(
        a["id"] for a in assertions
        if a["kind"] == "finding" and a["source"] in speakable
    )
    withheld = sum(
        1 for a in assertions
        if a["kind"] == "finding" and a["source"] not in speakable
    )
    denominators = dict(manifest["counts"])
    denominators["findings_withheld_by_disclosure"] = withheld
    return {
        "schema": OBSERVATION_SCHEMA,
        "producer": OBSERVATION_SCHEMA,
        "release_id": manifest["release_id"],
        "cohort": {
            "id": f"cohort:{manifest['release_id'][:16]}",
            "included": len(members),
            "members": members,
        },
        "denominators": dict(sorted(denominators.items())),
        "policy": {
            "curation_version": manifest["policy"]["version"],
            "taxonomy": (
                f"{manifest['policy']['taxonomy']['name']} "
                f"{manifest['policy']['taxonomy']['version']}"
            ),
            "cohort_rule": cohort_rule,
        },
        "exclusions": manifest["exclusions"],
        "unknowns": manifest["unknowns"],
        "not_established": OBSERVATION_NOT_ESTABLISHED,
    }


def check_projection(payload, schema, required):
    """Hold a projection to its own closed shape before it leaves."""
    if payload.get("schema") != schema:
        raise Refusal("A144", f"projection does not declare {schema}")
    missing = sorted(required - set(payload))
    extra = sorted(set(payload) - required)
    if missing or extra:
        raise Refusal(
            "A145",
            f"projection shape differs from {schema}: missing={missing} extra={extra}",
        )
    return payload


SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schemas")


def projection_fields(filename):
    """The field set a projection schema declares, read from the schema.

    Holding this as a constant beside the schema let the two drift: an adapter
    could gain a field the schema never declared, or lose one it requires, and
    nothing compared them. The schema is the single statement of the shape.
    """
    path = os.path.normpath(os.path.join(SCHEMA_DIR, filename))
    raw = read_bounded(path, MAX_POLICY_BYTES, f"schema {filename}")
    document = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    declared = set(document["properties"])
    required = set(document["required"])
    if declared != required:
        raise Refusal(
            "A160",
            f"schema {quote(filename)} declares optional fields {sorted(declared - required)}; "
            "a projection's shape is closed and every field is required",
        )
    return declared


ANALOGUE_FIELDS = projection_fields("elenchus-analogue-v1.json")
OBSERVATION_FIELDS = projection_fields("synkrisis-observation-v1.json")


def _rebuild_once(specimen, destination):
    """Build the specimen's release into a fresh directory."""
    policy_path = os.path.join(specimen, "policy.json")
    curation_path = os.path.join(specimen, "curation-policy.json")
    result = admit(policy_path, Events())
    policy = load_curation_policy(curation_path)
    texts = _admitted_texts(policy_path, result["sources"])
    graph = curate(result["sources"], policy, texts)
    return build_release(destination, policy, result["sources"], graph)


def verify_rebuild(specimen):
    """Build twice into fresh directories and compare every byte.

    Two builds of the same inputs under the same policy must agree on the
    release id and on every component. Comparing only the id would pass a build
    whose components drifted while their digests stayed in the manifest.
    """
    with tempfile.TemporaryDirectory() as first_root, \
            tempfile.TemporaryDirectory() as second_root:
        first = os.path.join(first_root, "release")
        second = os.path.join(second_root, "release")
        left = _rebuild_once(specimen, first)
        right = _rebuild_once(specimen, second)
        if left["release_id"] != right["release_id"]:
            raise Refusal(
                "A150",
                f"two builds disagree: {quote(left['release_id'])} and "
                f"{quote(right['release_id'])}",
            )
        verify_release(first)
        verify_release(second)
        names = sorted(os.listdir(first))
        if names != sorted(os.listdir(second)):
            raise Refusal("A151", "two builds wrote different file sets")
        for name in names:
            a = read_bounded(os.path.join(first, name), MAX_RELEASE_BYTES, name)
            b = read_bounded(os.path.join(second, name), MAX_RELEASE_BYTES, name)
            if a != b:
                raise Refusal(
                    "A152", f"two builds disagree on component {quote(name)}")
        return left["release_id"], len(names)


def cmd_ingest(args):
    events = Events(args.events)
    result = admit(args.policy, events)
    texts = _admitted_texts(args.policy, result["sources"])
    total = 0
    for source in result["sources"]:
        rounds = parse_source(texts[source["id"]], source["id"])
        found = sum(len(r["findings"]) for r in rounds)
        total += found
        print(f"{source['id']}: {len(rounds)} round(s), {found} finding(s)")
    print(f"ingested {len(result['sources'])} source(s) and {total} finding(s)")
    return 0


def cmd_curate(args):
    events = Events(args.events)
    result = admit(args.policy, events)
    policy = load_curation_policy(args.curation_policy)
    texts = _admitted_texts(args.policy, result["sources"])
    graph = curate(result["sources"], policy, texts)
    print(
        f"curated {len(graph['engagements'])} engagement(s), "
        f"{len(graph['assertions'])} assertion(s), {len(graph['relations'])} relation(s), "
        f"{len(graph['quarantine'])} quarantined"
    )
    return 0


def cmd_release(args):
    events = Events(args.events)
    result = admit(args.policy, events)
    policy = load_curation_policy(args.curation_policy)
    texts = _admitted_texts(args.policy, result["sources"])
    graph = curate(result["sources"], policy, texts)
    manifest = build_release(args.out, policy, result["sources"], graph)
    print(f"released {manifest['release_id']} to {args.out}")
    return 0


def cmd_verify(args):
    manifest, _ = verify_release(args.release)
    print(
        f"verified {manifest['release_id']}: "
        f"{len(manifest['components'])} component(s), "
        f"{manifest['counts']['findings']} finding(s), "
        f"{len(manifest['exclusions'])} exclusion(s)"
    )
    return 0


def cmd_measure_release(args):
    verify_release(args.release)  # refuses before anything is measured
    total = measure_release(args.release)
    if total > MAX_RELEASE_BYTES:
        raise Refusal(
            "A107",
            f"release is {total} bytes, above the {MAX_RELEASE_BYTES}-byte cap",
        )
    command = (
        "python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py measure-release "
        f"--release {args.release} --report {args.report}"
    )
    report = {
        "schema": REPORT_SCHEMA,
        "candidate": CANDIDATE,
        "criterion": "seed-release-byte-cap",
        "value": total,
        "unit": "bytes",
        "command": command,
        "exit": 0,
    }
    payload = json.dumps(report, indent=2) + "\n"
    encoded = payload.encode("utf-8")
    if len(encoded) > MAX_REPORT_BYTES:
        raise Refusal("A080", f"report exceeds the {MAX_REPORT_BYTES}-byte cap")
    parent = os.path.dirname(os.path.abspath(args.report))
    os.makedirs(parent, exist_ok=True)
    staging = f"{args.report}.{os.getpid()}.{secrets.token_hex(8)}.partial"
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
    os.replace(staging, args.report)
    print(f"release is {total} bytes, within the {MAX_RELEASE_BYTES}-byte cap; "
          f"wrote {args.report}")
    return 0


def cmd_analogues(args):
    payload = check_projection(
        analogues(args.release, args.kind, args.value), ANALOGUE_SCHEMA,
        ANALOGUE_FIELDS)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_observations(args):
    payload = check_projection(
        observations(args.release, args.cohort_rule), OBSERVATION_SCHEMA,
        OBSERVATION_FIELDS)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _write_report(path, criterion, value, unit, command):
    report = {
        "schema": REPORT_SCHEMA,
        "candidate": CANDIDATE,
        "criterion": criterion,
        "value": value,
        "unit": unit,
        "command": command,
        "exit": 0,
    }
    encoded = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAX_REPORT_BYTES:
        raise Refusal("A080", f"report exceeds the {MAX_REPORT_BYTES}-byte cap")
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
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


def cmd_verify_rebuild(args):
    release, components = verify_rebuild(args.specimen)
    command = (
        "python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py "
        f"verify-rebuild --specimen {args.specimen} --report {args.report}"
    )
    _write_report(args.report, "deterministic-rebuild", True, "boolean", command)
    print(
        f"two fresh builds agree on {release} across {components} component(s); "
        f"wrote {args.report}"
    )
    return 0


def cmd_demo(args):
    """The whole path, from the study's problem statement."""
    started = time.monotonic()
    release, components = verify_rebuild(args.specimen)
    print(f"1. two fresh builds agree on {release} across {components} components")

    out = os.path.join(args.specimen, "release")
    manifest, _ = verify_release(out)
    print(f"2. the committed release verifies: {manifest['counts']['findings']} "
          f"finding(s), {manifest['counts']['rounds']} round(s), "
          f"{manifest['counts']['rounds_with_no_findings']} with no findings")
    if manifest["release_id"] != release:
        raise Refusal(
            "A153",
            f"the committed release is {quote(manifest['release_id'])} but a fresh "
            f"build produces {quote(release)}",
        )

    view = check_projection(
        analogues(out, "severity", "high"), ANALOGUE_SCHEMA, ANALOGUE_FIELDS)
    print(f"3. Elenchus analogues for severity high: {len(view['analogues'])}; "
          f"verdict {view['verdict']}")

    cohort = check_projection(
        observations(out, "every public finding in the release"),
        OBSERVATION_SCHEMA, OBSERVATION_FIELDS)
    print(f"4. Synkrisis cohort {cohort['cohort']['id']}: "
          f"{cohort['cohort']['included']} included against "
          f"{cohort['denominators']['findings']} findings; "
          f"{len(cohort['exclusions'])} exclusion(s), "
          f"{sum(cohort['unknowns'].values())} unknown(s)")

    elapsed = time.monotonic() - started
    # Imported here rather than at module scope: one command needs it, and a
    # platform without it should still be able to admit and release.
    import resource

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    unit = "bytes" if sys.platform == "darwin" else "kibibytes"
    print(
        f"5. baseline, not a threshold: {elapsed:.2f}s wall clock, peak resident "
        f"{peak} {unit}. No budget is declared for either, so neither gates."
    )
    if args.report:
        command = (
            "python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo "
            f"--specimen {args.specimen} --report {args.report}"
        )
        _write_report(args.report, "deterministic-rebuild", True, "boolean", command)
        print(f"6. wrote {args.report}")
    return 0


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

    ingest = sub.add_parser(
        "ingest", help="read the admitted sources into their native rounds")
    ingest.add_argument("--policy", required=True)
    ingest.add_argument("--events", default=None)
    ingest.set_defaults(handler=cmd_ingest)

    curate = sub.add_parser(
        "curate", help="build the finding-to-remedy graph from admitted sources")
    curate.add_argument("--policy", required=True)
    curate.add_argument("--curation-policy", required=True)
    curate.add_argument("--events", default=None)
    curate.set_defaults(handler=cmd_curate)

    release = sub.add_parser("release", help="write one checked release")
    release.add_argument("--policy", required=True)
    release.add_argument("--curation-policy", required=True)
    release.add_argument("--out", required=True)
    release.add_argument("--events", default=None)
    release.set_defaults(handler=cmd_release)

    verify = sub.add_parser(
        "verify", help="recompute every component digest in a release")
    verify.add_argument("--release", required=True)
    verify.set_defaults(handler=cmd_verify)

    measure = sub.add_parser(
        "measure-release", help="verify a release and write the byte-cap report")
    measure.add_argument("--release", required=True)
    measure.add_argument("--report", required=True)
    measure.set_defaults(handler=cmd_measure_release)

    analogue = sub.add_parser(
        "analogues", help="the Elenchus view: source-linked analogues, no verdict")
    analogue.add_argument("--release", required=True)
    analogue.add_argument("--kind", required=True,
                          choices=("file", "severity", "native-id"))
    analogue.add_argument("--value", required=True)
    analogue.set_defaults(handler=cmd_analogues)

    observation = sub.add_parser(
        "observations", help="the Synkrisis view: one cohort with its denominators")
    observation.add_argument("--release", required=True)
    observation.add_argument("--cohort-rule", required=True)
    observation.set_defaults(handler=cmd_observations)

    rebuild = sub.add_parser(
        "verify-rebuild", help="build twice into fresh directories and compare")
    rebuild.add_argument("--specimen", required=True)
    rebuild.add_argument("--report", required=True)
    rebuild.set_defaults(handler=cmd_verify_rebuild)

    demo = sub.add_parser("demo", help="run the whole path over one specimen")
    demo.add_argument("--specimen", required=True)
    demo.add_argument("--report", default=None)
    demo.set_defaults(handler=cmd_demo)

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
