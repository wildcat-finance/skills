"""Offline demonstration of the released protocol as one closed machine-readable outcome.

Every input is a file the caller names. Nothing here fetches, signs, writes
outside the caller's report, or follows a locator carried in a record. The
outcome reports historical validity, current eligibility and copy availability
as separate fields and never infers one from another: a successful history with
no fresh external evidence keeps `current_eligibility_established` false.
"""
from __future__ import annotations

import json
from pathlib import Path
import platform
import resource
import sys
import tempfile
import time
import tracemalloc

from . import native_io as io, release, signatures, verifier
from .canonical import Refusal, canonical, decode, digest
from .schema import HASH, PREDICATE, enum, obj, validate

SCHEMA = "checkpoint-authority-demonstration/v1"
STAGE = "demonstration"
BUNDLE = release.CORPUS + "fixtures/"
HISTORY = BUNDLE + "demo-history.jsonl"
BOOTSTRAP = BUNDLE + "demo-bootstrap.json"
NATIVE = BUNDLE + "demo-native.json"
FRESHNESS = BUNDLE + "demo-freshness.json"
PRESENCE = BUNDLE + "demo-presence.json"
EXPECTED = BUNDLE + "demo-expected.json"
HOSTILE = BUNDLE + "release-hostile.json"
COSIGN_BLOB = BUNDLE + "semantic-specimen"
COSIGN_ENVELOPE = BUNDLE + "cosign-envelope.json"
COSIGN_DOUBLE = BUNDLE + "cosign-double-hashed-envelope.json"
TRUSTED_KEY = BUNDLE + "root-public.pem"
WRONG_KEY = BUNDLE + "wrong-public.pem"
EXPECTED_MAX = 16384
HOSTILE_MAX = 65536
COSIGN_TIMEOUT = 60
EXPECTED_SHAPE = obj(
    schema=enum("checkpoint-authority-demonstration-expected/v1"),
    history_sha256=HASH, records={"type": "integer", "minimum": 1, "maximum": 65536},
    bytes={"type": "integer", "minimum": 1, "maximum": 268435456},
    head_sha256=HASH, accepted={"type": "integer", "minimum": 1, "maximum": 65536},
    eligible={"type": "integer", "minimum": 1, "maximum": 65536},
    historical_permits={"type": "integer", "minimum": 0, "maximum": 65536},
    result_sha256=HASH)
COSIGN_CASES = (
    ("valid", "envelope", "trusted", None, 0),
    ("altered-payload", "envelope", "trusted", "payload", 1),
    ("untrusted-key", "envelope", "wrong", None, 1),
    ("wrong-payload-type", "envelope", "trusted", "type", 1),
    ("double-hashed", "double", "trusted", None, 1),
)
"""Each released case names its envelope, trusted key, one mutation and its exit."""


def _rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def _json(root, relative, maximum):
    try:
        return decode(io.read(root / relative, maximum), limit=maximum)
    except (Refusal, OSError):
        raise Refusal("demonstration-input-unavailable", STAGE) from None


def _bytes(root, relative, maximum):
    try:
        return io.read(root / relative, maximum)
    except (Refusal, OSError):
        raise Refusal("demonstration-input-unavailable", STAGE) from None


def inputs(root, tools_bytes):
    """Read every released consumer input through the public API, never a carried path."""
    limits = verifier.LIMITS
    return {
        "bootstrap": verifier.bootstrap_from(_bytes(root, BOOTSTRAP, limits["bootstrap_file_bytes"])),
        "tools": verifier.tools_from(tools_bytes),
        "native": verifier.native_from(_bytes(root, NATIVE, limits["native_file_bytes"])),
        "freshness": verifier.freshness_from(_bytes(root, FRESHNESS, limits["freshness_file_bytes"])),
        "presence": verifier.presence_from(_bytes(root, PRESENCE, limits["presence_file_bytes"])),
    }


def reconstruct(root, supplied, *, freshness=True, presence=True):
    """Replay the released history from files alone; no database or index is consulted."""
    stream = verifier.History(root / HISTORY)
    result = verifier.verify(stream, supplied["bootstrap"], supplied["tools"],
                             native=supplied["native"],
                             freshness=supplied["freshness"] if freshness else None,
                             presence=supplied["presence"] if presence else None)
    return result, stream.sha256


def _expected(root):
    value = _json(root, EXPECTED, EXPECTED_MAX)
    validate(value, EXPECTED_SHAPE)
    return value


def history(root, supplied):
    """The complete accepted history, its declared agreement and its measurements."""
    expected = _expected(root)
    decodes = {"count": 0}
    original = json.loads

    def observe(raw, *args, **kwargs):
        decodes["count"] += 1
        return original(raw, *args, **kwargs)

    json.loads = observe
    try:
        tracemalloc.start()
        started = time.perf_counter_ns()
        result, history_sha256 = reconstruct(root, supplied)
        elapsed_ns = time.perf_counter_ns() - started
        _, traced = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    finally:
        json.loads = original
    replay = result["result"]
    observed = {"history_sha256": history_sha256, "records": replay["records"], "bytes": replay["bytes"],
                "head_sha256": replay["head_sha256"], "accepted": len(replay["accepted"]),
                "eligible": result["eligibility_summary"]["eligible"],
                "historical_permits": replay["historical_permits"],
                "result_sha256": digest(canonical(replay, limit=verifier.LIMITS["output_bytes"]))}
    if any(observed[key] != expected[key] for key in observed):
        raise Refusal("demonstration-history-disagreement", STAGE)
    return {"complete": result["complete"], "historical": result["historical"],
            "reconstruction": "files-only", "database_consulted": False,
            "current_eligibility_established": result["current_eligibility_established"],
            **observed, "measured": {
                "wall_ms": round(elapsed_ns / 1_000_000, 3), "json_decodes": decodes["count"],
                "tracemalloc_peak_bytes": traced, "peak_rss_bytes": _rss_bytes(),
                "repetitions": 1}}


def withheld(root, supplied):
    """A valid history with no fresh external evidence must not invent current permission."""
    without_freshness, _ = reconstruct(root, supplied, freshness=False)
    without_presence, _ = reconstruct(root, supplied, presence=False)
    states = {row["current_eligibility"] for row in without_freshness["result"]["accepted"]}
    absent = {row["current_eligibility"] for row in without_presence["result"]["accepted"]}
    if (without_freshness["current_eligibility_established"] or states != {"unknown"}
            or without_freshness["historical"] != "valid" or absent != {"unavailable"}
            or not without_presence["current_eligibility_established"]):
        raise Refusal("demonstration-eligibility-upgrade", STAGE)
    return {"without_freshness": {"historical": "valid", "current_eligibility": "unknown",
                                  "current_eligibility_established": False},
            "without_copy_observations": {"historical": "valid", "current_eligibility": "unavailable",
                                          "current_eligibility_established": True}}


def _mutate(lock, case):
    value = json.loads(json.dumps(lock))
    section, field, replacement = case["section"], case["field"], case.get("value")
    if case["kind"] == "remove":
        del (value if section is None else value[section])[field]
    elif case["kind"] in ("add", "replace"):
        (value if section is None else value[section])[field] = replacement
    elif case["kind"] == "pad" and type(replacement) is int and 0 < replacement <= 32768:
        value[field] = "x" * replacement
    else:
        raise Refusal("demonstration-hostile-case", STAGE)
    return value


def hostile(root, lock_bytes):
    """Run every declared hostile release case and require its recorded refusal code."""
    declared = _json(root, HOSTILE, HOSTILE_MAX)
    if (type(declared) is not dict or set(declared) != {"schema", "cases"}
            or declared["schema"] != "checkpoint-authority-release-hostile/v1"
            or type(declared["cases"]) is not list or not 1 <= len(declared["cases"]) <= 64):
        raise Refusal("demonstration-hostile-case", STAGE)
    lock = decode(lock_bytes, limit=release.LOCK_MAX)
    rows = []
    for case in declared["cases"]:
        if (type(case) is not dict or set(case) != {"id", "kind", "section", "field", "value", "code"}
                or type(case["id"]) is not str or type(case["code"]) is not str):
            raise Refusal("demonstration-hostile-case", STAGE)
        if case["kind"] == "bytes":
            payload = case["value"].encode() if type(case["value"]) is str else b""
        else:
            payload = canonical(_mutate(lock, case), limit=release.LOCK_MAX * 2)
        try:
            release.lock_check(payload, root, source_commit=lock["authority"]["source_commit"])
        except Refusal as refusal:
            if refusal.code != case["code"]:
                raise Refusal("demonstration-hostile-code", STAGE) from None
            rows.append({"id": case["id"], "code": refusal.code, "refused": True})
            continue
        raise Refusal("demonstration-hostile-admitted", STAGE)
    return rows


def interoperability(root, cosign):
    """Agree with one independent pinned verifier offline; no transparency log is consulted."""
    if cosign is None:
        return {"verifier": None, "network": "denied", "cases": [], "agreed": False,
                "code": "independent-verifier-not-supplied"}
    validate(cosign.name, enum("cosign"))
    cosign.check()
    envelopes = {"envelope": decode(_bytes(root, COSIGN_ENVELOPE, release.LOCK_MAX * 8)),
                 "double": decode(_bytes(root, COSIGN_DOUBLE, release.LOCK_MAX * 8))}
    keys = {"trusted": _bytes(root, TRUSTED_KEY, 16384), "wrong": _bytes(root, WRONG_KEY, 16384)}
    blob = _bytes(root, COSIGN_BLOB, verifier.LIMITS["record_bytes"])
    rows = []
    with tempfile.TemporaryDirectory(prefix="checkpoint-release-demo-") as temporary:
        directory = Path(temporary)
        (directory / "blob").write_bytes(blob)
        for name, data in keys.items():
            (directory / (name + ".pem")).write_bytes(data)
        for case, source, key, mutation, expected_exit in COSIGN_CASES:
            envelope = json.loads(json.dumps(envelopes[source]))
            if mutation == "payload":
                envelope["payload"] = signatures.b64(
                    signatures.b64decode(envelope["payload"]).replace(b"test-service", b"other-service"))
            elif mutation == "type":
                envelope["payloadType"] = "application/wrong"
            bundle = {"mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json",
                      "verificationMaterial": {"publicKey": {"hint": ""}}, "dsseEnvelope": envelope}
            (directory / "bundle.json").write_bytes(canonical(bundle, limit=131072))
            exit_code = signatures._run(cosign, [
                "verify-blob-attestation", "--offline", "--insecure-ignore-tlog",
                "--key", key + ".pem", "--bundle", "bundle.json", "--type", PREDICATE, "blob",
            ], directory, timeout=COSIGN_TIMEOUT)[0]
            if exit_code != expected_exit:
                raise Refusal("demonstration-interoperability-disagreement", STAGE)
            rows.append({"id": case, "expected_exit": expected_exit, "exit": exit_code, "agreed": True})
    return {"verifier": {"name": cosign.name, "sha256": cosign.sha256}, "network": "denied",
            "transparency_log": "not-consulted", "cases": rows, "agreed": True, "code": "verifiers-agree"}


def run(root, *, tools_bytes, cosign=None):
    """Return one closed demonstration outcome; a refusal reaches the caller unchanged."""
    supplied = inputs(root, tools_bytes)
    first, second = release.build(root), release.build(root)
    if release.encode(first) != release.encode(second):
        raise Refusal("release-not-reproducible", STAGE)
    manifest_bytes, _ = release.committed(root)
    lock_bytes = _bytes(root, release.LOCK_EXAMPLE, release.LOCK_MAX)
    lock = decode(lock_bytes, limit=release.LOCK_MAX)
    verified = release.lock_check(lock_bytes, root, source_commit=lock["authority"]["source_commit"])
    return {"schema": SCHEMA, "event": "checkpoint_authority_demonstrated", "stage": STAGE,
            "code": "demonstration-complete", "complete": True,
            "release": {"manifest_sha256": digest(manifest_bytes), "reproducible_rebuilds": 2,
                        "pins": verified["pins"], "native": verified["native"], "tools": verified["tools"],
                        "source_commit_asserted": verified["source_commit_asserted"]},
            "history": history(root, supplied), "withheld_evidence": withheld(root, supplied),
            "hostile": hostile(root, lock_bytes), "interoperability": interoperability(root, cosign),
            "limits": {**verifier.LIMITS, "supported_resource_limits": release.RESOURCE_LIMITS},
            "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                            "machine": platform.machine()},
            "boundary": "One machine, one committed synthetic history signed with ephemeral test keys and "
                        "unexecuted synthetic native attestations. No production latency, throughput, "
                        "issuer root, cloud retention or live storage independence is established."}


def refusal(error):
    """One closed refusal event; no input value or child diagnostic leaves the process."""
    stage = error.stage if isinstance(error, Refusal) else STAGE
    code = error.code if isinstance(error, Refusal) else "unsafe-or-unavailable-file"
    return {"schema": SCHEMA, "event": "checkpoint_authority_demonstration_refused", "stage": stage,
            "code": code, "complete": False, "historical": None,
            "current_eligibility_established": False}


def encode(outcome):
    return canonical(outcome, limit=verifier.LIMITS["output_bytes"])
