"""Retained-conformance resolver for the Wildcat accrual and state-update meaning (#2088).

The custody, staging-manifest and private-scratch helpers are #2087's, imported
from `wildcat_batch_retained.py` rather than copied. Each staging tree is named
by its variable and read without following a link, checked against its public
Alexandria example's staging manifest and rebuilt into a raw release through
that example's builder, inside a private temporary directory outside the
repository. This module builds and verifies a canonical release from each raw
release and answers one boolean per generation: do the `InterestAndFeesAccrued`
and `StateUpdated` rows carry the selected `abi-named-amounts` meaning, and
does `verify` pass. Each decoded value is read again from the preserved log's
own data words, and each party from the log's emitter, so the answer does not
rest on the adapter's decoder agreeing with itself.

A generation that maps no row of either event refuses by generation name
instead of passing, so a `true` report says both events were exercised in both
generations. The observations carry raw release identifiers, canonical and
coverage digests and the generations that passed: no path, count, address,
transaction, block or amount from the retained releases. The temporary
directory is removed on success, on a false result and on refusal.

`wildcat_accrual_reports.py` may not import `os`, so the environment read
lives here and that module imports only `retained_resolver`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
if sys.path[:1] != [str(HERE)]:
    sys.path.insert(0, str(HERE))

# The batch module puts the plugin's scripts directory on sys.path as it loads.
from wildcat_batch_retained import (DIGEST_FILES, GENERATIONS, MAX_DOCUMENT_BYTES, RELEASE_SUFFIX,
                                    document, private_scratch, sha256_file, verified)
from tabularium_lib.keccak import keccak256
from tabularium_lib.wildcat_release import build_wildcat_canonical
from wildcat_v3_reports import EvidenceUnavailable

ACCRUAL = "InterestAndFeesAccrued(uint256,uint256,uint256,uint256,uint256,uint256)"
STATE = "StateUpdated(uint256,bool)"
# The selected design's meaning, stated apart from the production rule tuples:
# action to (family, signature, amount kinds with the ABI field each carries in
# order, and the native-state fields that stay in the decoded record).
MEANING = {
    "interest-and-fees-accrued": (
        "interest-accrual", ACCRUAL,
        (("scale-factor", "scaleFactor"), ("base-interest-ray", "baseInterestRay"),
         ("delinquency-fee-ray", "delinquencyFeeRay"), ("protocol-fees", "protocolFees")),
        ("fromTimestamp", "toTimestamp")),
    "state-updated": ("pool-state", STATE, (("scale-factor", "scaleFactor"),), ("isDelinquent",)),
}
SIGNATURES = frozenset(signature for _family, signature, _amounts, _native in MEANING.values())
# Each event's fields in the pinned declaration's order, none indexed, so the
# log carries one topic and one data word per field.
DECLARED = {
    "interest-and-fees-accrued": (("fromTimestamp", "uint256"), ("toTimestamp", "uint256"),
                                  ("scaleFactor", "uint256"), ("baseInterestRay", "uint256"),
                                  ("delinquencyFeeRay", "uint256"), ("protocolFees", "uint256")),
    "state-updated": (("scaleFactor", "uint256"), ("isDelinquent", "bool")),
}
HEX_WORDS = re.compile(r"0x(?:[0-9a-fA-F]{64})*")
TOPICS = frozenset("0x" + keccak256(signature.encode()).hex() for signature in SIGNATURES)
# The one kind that names the market's asset; the three ray kinds stay assetless.
ASSET_KIND = "protocol-fees"
ROW_FIELDS = frozenset(("schema_version", "id", "event_family", "action", "venue", "chain", "transaction",
                        "parties", "instrument", "amounts", "provenance", "native_record"))
CONTEXT_SELECTOR = "wildcat-context:"


def event_rows(path: Path) -> list:
    """The canonical rows, read under the release owner's byte cap without following a link."""
    if path.is_symlink() or not path.is_file():
        raise EvidenceUnavailable("canonical release rows unavailable")
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise EvidenceUnavailable("canonical release rows exceed the byte cap")
    with path.open("rb") as handle:
        return [json.loads(line) for line in handle.read().splitlines()]


def native_values(action: str, native_record: dict):
    """Each declared field as the preserved log's own word reads, or None for any other log shape.

    The topic list must be the signature's topic alone and the data exactly one
    word per declared field. A `uint256` reads as its decimal string and a
    `bool` word must be zero or one.
    """
    fields = DECLARED[action]
    data = native_record.get("data")
    if native_record.get("topics") != ["0x" + keccak256(MEANING[action][1].encode()).hex()]:
        return None
    if not isinstance(data, str) or len(data) != 2 + 64 * len(fields) or not HEX_WORDS.fullmatch(data):
        return None
    values = {}
    for index, (field, kind) in enumerate(fields):
        word = int(data[2 + 64 * index:66 + 64 * index], 16)
        if kind == "bool":
            if word not in (0, 1):
                return None
            values[field] = word == 1
        else:
            values[field] = str(word)
    return values


def expected_gaps(action: str, asset) -> list:
    """The actor gap, and the asset gap only on an accrual whose market asset is unknown."""
    gaps = ["attribution:%s:actor" % action]
    if asset is None and any(kind == ASSET_KIND for kind, _field in MEANING[action][2]):
        gaps.append("attribution:%s:asset" % action)
    return gaps


def row_conforms(generation: str, action: str, row: dict, record: dict, gaps: list) -> bool:
    """True when one row and its mapping record carry the selected meaning.

    The log's emitter is the only party; each decoded field equals its word in
    the preserved log, and each amount is its decoded ABI field in native
    units, with the ray kinds assetless and `protocol-fees` naming the market's
    asset or leaving it null with the asset gap; the timestamps and
    `isDelinquent` stay in the decoded record and `native_record`; and the row
    joins nothing and is supported only by its emitter's context.
    """
    family, signature, amounts, native = MEANING[action]
    if set(row) != ROW_FIELDS or row["venue"] != generation or row["event_family"] != family:
        return False
    provenance = row["provenance"]
    emitter = provenance["source_contract"]
    if (provenance["mapping_rule"], provenance["source_entity"]) != ("%s.%s.v1" % (generation, action), signature):
        return False
    if row["parties"] != [{"role": "pool", "address": emitter}]:
        return False
    if emitter != str(record["native_record"].get("address", "")).lower():
        return False
    if row["instrument"] != {"type": generation + "-market", "id": emitter}:
        return False
    decoded = record["decoded"]
    if set(decoded) != {field for _kind, field in amounts} | set(native):
        return False
    if "isDelinquent" in native and type(decoded["isDelinquent"]) is not bool:
        return False
    if decoded != native_values(action, record["native_record"]):
        return False
    asset = record["context"]["asset"]
    if row["amounts"] != [{"kind": kind, "base_units": decoded[field],
                           "asset": asset if kind == ASSET_KIND else None} for kind, field in amounts]:
        return False
    if row["native_record"] != record["native_record"]:
        return False
    if record["disposition"] != "primary" or record["join"] is not None:
        return False
    supports = record["supporting_selectors"]
    if provenance["supporting_selectors"] != supports:
        return False
    if not supports or not all(item.startswith(CONTEXT_SELECTOR) for item in supports):
        return False
    return gaps == expected_gaps(action, asset)


def release_conforms(generation: str, source: dict, rows: list, coverage: dict) -> bool:
    """True when both signatures map and every accrual and state-update row carries the meaning.

    Neither signature or topic is left in unsupported coverage, every mapping
    record of the two signatures has exactly one conforming row, and the
    included count of each action equals its rows. No row is compared with
    another, so no event's cause and no shared scale factor is inferred.
    """
    for key in coverage["coverage"]["unsupported_events"]:
        if any(signature in key for signature in SIGNATURES):
            return False
        if key.startswith("decode:") and key.rsplit(":", 1)[-1] in TOPICS:
            return False
    gaps = {item["source_selector"]: item["gaps"] for item in source["dispositions"]}
    records = {item["source_selector"]: item for item in source["mapping_records"]
               if item["signature"] in SIGNATURES}
    seen = set()
    counts = dict.fromkeys(MEANING, 0)
    for row in rows:
        prefix, _, action = row["action"].partition(".")
        if action not in MEANING:
            continue
        selector = row["provenance"]["source_selector"]
        record = records.get(selector)
        if prefix != generation or record is None or selector in seen:
            return False
        if record["signature"] != MEANING[action][1]:
            return False
        if not row_conforms(generation, action, row, record, gaps.get(selector)):
            return False
        seen.add(selector)
        counts[action] += 1
    if seen != set(records):
        return False
    included = coverage["coverage"]["included_events"]
    return all(included.get(action, 0) == count for action, count in counts.items())


def require_both_events(generation: str, rows: list) -> None:
    """Refuse a release missing either event: its conditions would hold over an empty set."""
    for action in MEANING:
        if not any(row["action"] == generation + "." + action for row in rows):
            raise EvidenceUnavailable(generation + " maps no " + action + " row")


def retained_conformance(generations=GENERATIONS, environ=None, witness=None):
    """Resolve the criterion over every generation; return (bool, observations).

    Custody is checked for every generation before any directory is created,
    so an absent or unreadable variable refuses by name with nothing to clean
    up. `witness`, when given, receives the scratch path so a test can confirm
    it is gone afterwards.
    """
    environ = os.environ if environ is None else environ
    roots = [(spec, spec.custody(environ)) for spec in generations]
    scratch = private_scratch()
    if witness is not None:
        witness(scratch)
    inputs, passed = [], []
    try:
        value = True
        for spec, root in roots:
            raw = spec.rebuild(root, scratch / (spec.generation + "-raw"))
            canonical = scratch / (spec.generation + "-canonical")
            build_wildcat_canonical(raw, canonical, spec.generation + RELEASE_SUFFIX)
            source = document(canonical / "source.json")
            coverage = document(canonical / "coverage.json")
            rows = event_rows(canonical / "events.jsonl")
            require_both_events(spec.generation, rows)
            conformant = verified(canonical) and release_conforms(spec.generation, source, rows, coverage)
            inputs.append({"generation": spec.generation,
                           "raw_release_id": source["raw_release"]["release_id"],
                           **{field: sha256_file(canonical / name) for field, name in DIGEST_FILES}})
            if conformant:
                passed.append(spec.generation)
            value = value and conformant
    finally:
        shutil.rmtree(scratch)
    return value, {"inputs": inputs, "passed_generations": passed}


def retained_resolver(generations=GENERATIONS, witness=None):
    """A resolver the dispatch table can call with no arguments."""
    def resolve():
        return retained_conformance(generations, witness=witness)
    return resolve
