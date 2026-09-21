#!/usr/bin/env python3
"""Collect a bounded Ethereum USDC Comet block interval, resumably.

The network path is explicit and lives in two places: the hosted
`HttpsTransport`, built from an environment variable that is never written
anywhere, and the bounded, explicit opt-in local `LoopbackHttpTransport`,
reached only over a literal loopback address. `transport_from_environment`
chooses between them from the environment alone. Every other path in this
module takes a transport it was handed, so the whole collector is exercised
offline against a fixture provider and no test but the loopback wiring proof
itself opens a socket.

The loop is the one `docs/compound-v3-harvest.md` specifies. It binds the end
boundary under a named finality policy before it asks for a shard, walks the
plan in bounded shards requesting only the evidence classes the plan declares,
checkpoints only after the bytes are fsynced, and rewinds to the last
remembered boundary that still matches when a hash has changed under it. After
the last shard it reads the interval's opening evidence, the first block's
header, the implementation slot and header at each epoch boundary and each
implementation's runtime code, into a fourth journal that is checkpointed and
resumed like a shard and reconciled like one. `build` discovers the epochs
from that journal alone, ships each implementation's runtime bytes as a
component the epoch table names by digest, and binds every evidence scope to
the first block's hash and the last shard's; `check` re-hashes the bytes.

A plan that declares `shards_per_component` ships each shard-class journal as
one release component per plan-derived shard range, named `<class>.<k>`, so a
journal larger than the component ceiling is released in parts. `check`
re-derives those ranges from the plan alone, refuses components that do not
tile the shard range exactly, and compares every component's byte count with
the ceiling.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))

from alexandria_lib.canonical import MAX_CONTROL_BYTES, canonical_bytes, load_bytes, load_raw_json
from alexandria_lib.errors import AlexandriaError
import re
import shutil
import tempfile

from alexandria_lib.interval import (
    ADDRESS_RE,
    CODE_DIGEST_RE,
    EVIDENCE_CLASSES,
    JOURNAL_CLASSES,
    MAX_DISPUTES,
    OPENING_CLASS,
    RECEIPT_FORMAT,
    SUBJECT_RECEIPT_FORMAT,
    UPGRADED_TOPIC,
    LEGACY_RECEIPT_FORMAT,
    OpeningRefusal,
    discover_block_epochs,
    validate_block_epochs,
    proxy_log_positions,
    attribute_logs,
    validate_attributions,
    Staging,
    ZERO_ADDRESS,
    component_name,
    discover_epochs,
    log_identity,
    FINALITY_POLICIES,
    HASH_RE,
    opening_boundaries,
    opening_code_reads,
    opening_prefix,
    plan_digest,
    plan_partition,
    read_regular,
    runtime_code,
    slot_word_address,
    upgrade_logs,
    validate_epochs,
    validate_epoch_subjects,
    subject_epoch_rows,
    subject_epoch_table,
    validate_first_code,
    validate_plan,
    validate_reconciliation,
    validate_shard_coverage,
)
from alexandria_lib.venues import VENUES
from alexandria_lib.paths import read_confined_file
from alexandria_lib.release import MAX_COMPONENTS, MAX_RAW_COMPONENT_BYTES, ingest, verify


ENDPOINT_ENV = "ALEXANDRIA_COMPOUND_RPC_URL"
BEARER_ENV = "ALEXANDRIA_RPC_BEARER"  # phylax: allow the environment variable's name, never a credential value
LOOPBACK_ALLOW_ENV = "ALEXANDRIA_RPC_ALLOW_LOOPBACK_HTTP"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1"})
MAX_COLLECT_SECONDS = 3_600
MAX_COLLECT_BYTES = 512 * 1024 * 1024
# A bounded worker pool fetches this many shards' data concurrently; commits
# still land strictly in ascending shard order (see `Collector._collect_shards`).
# Conservative by default -- tune with `collect --concurrency`, never past the
# ceiling, which exists so a plan cannot turn concurrency into an unbounded
# thread count.
DEFAULT_COLLECT_CONCURRENCY = 4
MAX_COLLECT_CONCURRENCY = 8
MAX_RESPONSE_NODES = 2_000_000
RECEIPTS_DIRECTORY = "receipts"
ERROR_RECEIPTS = "errors.jsonl"
RECONCILIATION_DIRECTORY = "reconciliation"
RECONCILIATION_RECORD = "reconciliation.json"
DISPUTED_RESPONSES = "disputed.jsonl"
# Reconciliation's own progress marker, separate from `Staging`'s: a shard's
# comparison work against the second provider, not the collected bytes
# themselves. See `Reconciler._save_reconcile_checkpoint`.
RECONCILE_CHECKPOINT_NAME = "checkpoint.json"
RECONCILE_CHECKPOINT_FORMAT = "alexandria-interval-reconcile-checkpoint/v1"
JOURNAL_FORMAT = "alexandria-interval-journal/v1"
RECONCILIATION_FORMAT = "alexandria-interval-reconciliation/v1"
BOUNDARY_CLASS = "boundary-blocks"
ENTRY_BLOCK_CLASSES = ("logs", "traces")
CODE_COMPONENT = "implementation-code"
CODE_FORMAT = "alexandria-interval-implementation-code/v1"
RELEASE_NAME = "usdc-interval-v0"
# The components every interval release carries beside its journals: one per
# declared evidence class, the opening-read journal, and these six.
FIXED_COMPONENTS = (
    "epoch-table", "error-receipts", CODE_COMPONENT, "interval-plan",
    "reconciliation", "registry",
)
# What a plan's omitted class would have preserved, named on every evidence
# scope of a release that omits it.
OMISSION_REASONS = {
    "boundary-blocks": "no shard boundary header was preserved",
    "logs": (
        "no proxy event log was preserved, so an Upgraded(address) inside the interval is "
        "undetectable from these bytes and the epoch table cannot name a boundary the "
        "interval's first block did not open"
    ),
    "traces": "no internal call to the proxy was preserved",
}



def journal_components(plan, classes) -> dict:
    """The release's journal components, derived from the plan alone.

    Maps each component name to `{"class", "index", "first", "last"}`: the
    class whose records it holds, its position among that class's components
    (None where the class is one component), and the inclusive shard range it
    covers. A plan that declares no `shards_per_component` yields one component
    per class under the class's own name, so every existing release keeps the
    names it was built with. A split plan yields `<class>.<k>` for each
    contiguous shard range the plan derives, in shard order. The opening
    journal is one component either way, under the virtual shard index.

    Refuses a plan whose components would exceed the release limit, so a
    collection cannot run to its end and then have no release to build.
    """
    shard_count = len(plan["shards"])
    ranges = plan_partition(plan)
    components = {}
    for name in classes:
        if ranges is None:
            components[name] = {"class": name, "index": None, "first": 0, "last": shard_count - 1}
            continue
        for index, (first, last) in enumerate(ranges):
            components[component_name(name, index)] = {
                "class": name, "index": index, "first": first, "last": last,
            }
    components[OPENING_CLASS] = {
        "class": OPENING_CLASS, "index": None, "first": shard_count, "last": shard_count,
    }
    total = len(FIXED_COMPONENTS) + len(components)
    if total > MAX_COMPONENTS:
        raise AlexandriaError(
            f"the plan derives {len(components)} journal components, so its release would carry "
            f"{total} components, above the {MAX_COMPONENTS}-component limit"
        )
    return components


def component_gap(plan, part) -> str:
    """What one split component does not hold, named on its own coverage.

    A split component's scope binds the whole interval's two boundary hashes,
    because those are the hashes the collector read and the journal as a whole
    covers the interval. This sentence says which shards the component itself
    carries, so a reader of one component alone does not take it for the
    journal. `check` derives the same sentence from the plan and requires it.
    """
    shards = plan["shards"]
    return (
        f"component {part['index']} of the {part['class']} journal holds shards "
        f"{part['first']} to {part['last']}, blocks {shards[part['first']]['start']} to "
        f"{shards[part['last']]['end']}; the journal's other components hold the interval's "
        "other shards"
    )


FINALITY_TAGS = {"finalized": "finalized", "safe": "safe"}
TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
PLUGIN_MANIFEST = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"


def package_version(manifest=PLUGIN_MANIFEST) -> str:
    """The delivery package version, read from the plugin manifest and nowhere else."""
    document = load_bytes(
        read_regular(Path(manifest), "plugin manifest", MAX_CONTROL_BYTES), "plugin manifest"
    )
    version = document.get("version") if isinstance(document, dict) else None
    if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
        raise AlexandriaError("the plugin manifest carries no package version")
    return version


# The headers every request carries, fixed at import. Two of the five providers
# the study probed answer HTTP 403 to Python's default User-Agent. The value is
# built from the package version and from nothing in the environment, so no
# header can carry a credential and a provider that requires one is out of
# scope.
PACKAGE_VERSION = package_version()
USER_AGENT = f"alexandria-usdc-interval/{PACKAGE_VERSION}"
REQUEST_HEADERS = {"Content-Type": "application/json", "User-Agent": USER_AGENT}


class TransportError(AlexandriaError):
    """The provider could not be reached, or answered outside the contract."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TransportError("the Compound RPC endpoint redirected")


def _close_transport_error(error: urllib.error.URLError) -> None:
    """Release the socket a raised `URLError` may still be holding open.

    `urlopen`'s default error handling turns any non-2xx response into an
    `HTTPError`, a `URLError` subclass that is itself the file-like response
    object -- it never closes on its own, unlike the `with` block's own
    response on the success path. Neither transport reads its body, so
    closing it here costs nothing and the label-only message stays exactly
    what it was; leaving it open instead keeps the socket alive until an
    unpredictable later garbage-collection pass reclaims it, printing a
    `ResourceWarning` wherever `sys.stderr` happens to point at that moment,
    in this process or a caller's.
    """
    close = getattr(error, "close", None)
    if callable(close):
        close()


class HttpsTransport:
    """The hosted network path: HTTPS only, with an optional per-instance bearer.

    The endpoint reaches no file, receipt or message. Neither does the bearer:
    it lives on this instance alone, reaches one `Authorization` header on a
    copy of the request headers, and never touches the module-level
    `REQUEST_HEADERS` constant, which stays exactly what a transport built
    without a bearer still sends.
    """

    def __init__(self, endpoint: str, timeout: int, bearer: str | None = None) -> None:
        if not endpoint.startswith("https://") or any(c.isspace() for c in endpoint):
            raise AlexandriaError(f"{ENDPOINT_ENV} must name an HTTPS endpoint")
        if bearer is not None and (
            any(character.isspace() for character in bearer) or not bearer.isprintable()
        ):
            raise AlexandriaError(f"{BEARER_ENV} must carry no whitespace and only printable bytes")
        self._endpoint = endpoint
        self._timeout = timeout
        self._bearer = bearer
        self._opener = urllib.request.build_opener(_NoRedirect)

    @classmethod
    def from_environment(cls, timeout: int, environ=None) -> "HttpsTransport":
        values = os.environ if environ is None else environ
        raw_bearer = values.get(BEARER_ENV)
        return cls(values.get(ENDPOINT_ENV, ""), timeout, raw_bearer if raw_bearer else None)

    def request(self, payload: bytes, label: str) -> bytes:
        headers = dict(REQUEST_HEADERS)
        if self._bearer is not None:
            headers["Authorization"] = f"Bearer {self._bearer}"
        message = urllib.request.Request(
            self._endpoint,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with self._opener.open(message, timeout=self._timeout) as response:
                if response.status != 200:
                    raise TransportError(f"{label} returned HTTP {response.status}")
                return response.read(MAX_RAW_COMPONENT_BYTES + 1)
        except urllib.error.URLError as error:
            _close_transport_error(error)
            raise TransportError(f"{label} transport failed") from error


def _validate_loopback_endpoint(endpoint: str) -> None:
    """Refuse anything but a literal-loopback HTTP endpoint, before any connection.

    A hostname that merely resolves to loopback is refused by its spelling
    alone -- this never resolves DNS, so a moved or spoofed record cannot
    change the answer. Malformed authority, URL user information and every
    other scheme or host are refused the same way, and none of these messages
    repeats the endpoint the caller supplied.
    """
    if not endpoint or any(character.isspace() for character in endpoint):
        raise AlexandriaError("the local loopback endpoint must name a literal loopback address")
    try:
        parts = urllib.parse.urlsplit(endpoint)
        username = parts.username
        password = parts.password
        hostname = parts.hostname
        _ = parts.port
    except ValueError as exc:
        raise AlexandriaError("the local loopback endpoint has a malformed authority") from exc
    if parts.scheme != "http":
        raise AlexandriaError("the local loopback endpoint must use plain HTTP")
    if username is not None or password is not None or "@" in parts.netloc:
        raise AlexandriaError("the local loopback endpoint must carry no user information")
    if hostname not in LOOPBACK_HOSTS:
        raise AlexandriaError("the local loopback endpoint must literally name 127.0.0.1 or ::1")


class LoopbackHttpTransport:
    """The bounded, explicit opt-in local path: literal loopback HTTP, never a bearer.

    Reached only through `transport_from_environment`, when the operator opts
    in with `ALEXANDRIA_RPC_ALLOW_LOOPBACK_HTTP=1` and the endpoint is a
    literal `127.0.0.1` or `::1` HTTP address. Environment proxy settings are
    never honored here and no redirect is ever followed, and it applies the
    same request, response and timeout bounds `HttpsTransport` does.
    """

    def __init__(self, endpoint: str, timeout: int) -> None:
        _validate_loopback_endpoint(endpoint)
        self._endpoint = endpoint
        self._timeout = timeout
        # An explicit empty proxy mapping overrides whatever HTTP_PROXY/
        # http_proxy (and friends) the environment carries; build_opener adds
        # no default ProxyHandler once one is supplied explicitly.
        self._opener = urllib.request.build_opener(_NoRedirect, urllib.request.ProxyHandler({}))

    @classmethod
    def from_environment(cls, timeout: int, environ=None) -> "LoopbackHttpTransport":
        values = os.environ if environ is None else environ
        return cls(values.get(ENDPOINT_ENV, ""), timeout)

    def request(self, payload: bytes, label: str) -> bytes:
        message = urllib.request.Request(
            self._endpoint,
            data=payload,
            headers=dict(REQUEST_HEADERS),
            method="POST",
        )
        try:
            with self._opener.open(message, timeout=self._timeout) as response:
                if response.status != 200:
                    raise TransportError(f"{label} returned HTTP {response.status}")
                return response.read(MAX_RAW_COMPONENT_BYTES + 1)
        except urllib.error.URLError as error:
            _close_transport_error(error)
            raise TransportError(f"{label} transport failed") from error


def transport_from_environment(timeout: int, environ=None):
    """The collector's one network path, chosen from the environment alone.

    The hosted `HttpsTransport` is the default. The bounded local path opens
    only when `ALEXANDRIA_RPC_ALLOW_LOOPBACK_HTTP=1` accompanies a literal
    loopback HTTP endpoint; any other endpoint under that opt-in refuses here,
    before any connection opens, rather than falling through to the hosted
    path's own HTTPS-only refusal. A bearer is never accepted alongside the
    opt-in.
    """
    values = os.environ if environ is None else environ
    if values.get(LOOPBACK_ALLOW_ENV) == "1":
        endpoint = values.get(ENDPOINT_ENV, "")
        _validate_loopback_endpoint(endpoint)
        if values.get(BEARER_ENV):
            raise AlexandriaError("the local loopback endpoint accepts no bearer credential")
        return LoopbackHttpTransport(endpoint, timeout)
    return HttpsTransport.from_environment(timeout, environ)


def request_bytes(identifier: int, method: str, params) -> bytes:
    return canonical_bytes({"id": identifier, "jsonrpc": "2.0", "method": method, "params": params})


def request_identifier(shard: int, name: str) -> int:
    """Derive an id from the plan, so a resumed run asks for the same bytes."""
    return shard * len(EVIDENCE_CLASSES) + EVIDENCE_CLASSES.index(name) + 1


def opening_identifier(virtual: int, position: int) -> int:
    """The id of one opening read: past every shard id, in the reads' plan order."""
    return request_identifier(virtual, EVIDENCE_CLASSES[0]) + position


def opening_label(position: int, read) -> str:
    return f"opening read {position} {read['kind']} block {read['block']}"


def preserved_result(response: str, identifier: int, page_limit, subject: str, result_subject: str, parse_label: str):
    """The result of one preserved envelope, held to the rules `_ask` applied to the same bytes.

    Every record in a staging tree or a release is an answer `_ask` accepted,
    and `_ask` refuses an envelope that is not JSON-RPC 2.0, one answering
    another request's id, one carrying an error, one carrying no result, one
    marked truncated and one whose result stands at the provider's page limit.
    A reader that takes `result` off the envelope and nothing else believes an
    answer the collector would have stopped for.

    That rule was written into the shard journals' reader alone, so the
    opening journal -- the evidence that binds the interval's start hash and
    derives the epoch table -- was read with `envelope.get("result")` by the
    collector's resume path, the builder's replay and the release check alike.
    This is the one reader all four sites use, so a rule added here reaches
    every preserved read rather than the journal whose loop it was written in.
    """
    envelope = load_bytes(response.encode(), parse_label, max_bytes=MAX_RAW_COMPONENT_BYTES)
    if (
        not isinstance(envelope, dict)
        or envelope.get("jsonrpc") != "2.0"
        or envelope.get("id") != identifier
        or "error" in envelope
        or "result" not in envelope
    ):
        raise AlexandriaError(f"the {subject} is not the answer its preserved request names")
    if envelope.get("truncated") is True:
        raise AlexandriaError(f"the {subject} is marked truncated")
    result = envelope["result"]
    if isinstance(result, list) and len(result) >= page_limit:
        raise AlexandriaError(
            f"the {result_subject} stands at the provider's page limit, so it is not a "
            "complete read"
        )
    return result


def opening_result(plan, position: int, response: str, parse_label: str):
    """One preserved opening read's result, held to the same rules as a shard read."""
    virtual = len(plan["shards"])
    subject = f"epoch-evidence response for opening read {position}"
    return preserved_result(
        response,
        opening_identifier(virtual, position),
        plan["provider"]["page_limit"],
        subject,
        f"epoch-evidence result for opening read {position}",
        parse_label,
    )


# The epoch model this module's own `OpeningPhase` implements. A venue naming
# any other model owns its opening reads and epoch derivation.
EIP1967_MODEL = "eip1967-proxy"


def plan_venue(plan):
    """The registered venue module a plan names, or a refusal naming the venue."""
    venue = plan["venue"]
    if venue not in VENUES:
        raise AlexandriaError(f"the interval plan names an unregistered venue {venue!r}")
    return VENUES[venue]


def opening_phase(plan, staged_logs, *, registry=None, legacy=False):
    """The opening reads one plan owes, from the venue that owns its epoch model.

    Every path that plans, replays or re-derives opening reads comes through
    here, so a subject-set plan never reaches the single-proxy phase's
    `plan["proxy"]` and a single-proxy plan never reaches a venue's
    subject-keyed one. Either mismatch refuses by name.
    """
    venue = plan_venue(plan)
    if venue.EPOCH_MODEL == EIP1967_MODEL:
        if "subjects" in plan:
            raise AlexandriaError(
                f"the {venue.VENUE} venue derives its epochs from one proxy's implementation "
                "slot, so a subject-set plan has no opening reads under it"
            )
        return OpeningPhase(plan, staged_logs, legacy=legacy)
    if legacy:
        raise AlexandriaError(
            f"the {venue.VENUE} venue has no block-only receipt; its epochs are positional"
        )
    return venue.opening_phase(plan, registry, staged_logs)


class OpeningPhase:
    """The opening reads one plan owes, in the order they are made.

    Built from the staged logs, so a fresh run, a resumed run and a reconciler
    all derive the same reads and the same request bytes. `reads()` yields the
    prefix first; the code reads follow only after every slot word has been
    accepted, because they name the implementations the slots revealed.
    Nothing here touches a transport or a file.
    """

    # The first topic this epoch model reads as an epoch boundary.
    upgrade_topic = UPGRADED_TOPIC

    def __init__(self, plan, staged_logs, *, legacy=False) -> None:
        self.plan = plan
        self.virtual = len(plan["shards"])
        self.start = int(plan["interval"]["start"])
        self.end = int(plan["interval"]["end"])
        self.logs = staged_logs
        if not legacy:
            proxy_log_positions(staged_logs, plan["proxy"], plan["interval"])
        self.upgrades = upgrade_logs(staged_logs, plan["proxy"])
        self.announced = {upgrade["block"]: upgrade for upgrade in self.upgrades}
        self.boundaries = opening_boundaries(self.start, self.end, self.upgrades)
        self.prefix = opening_prefix(plan, self.upgrades)
        self.implementations: dict[int, str] = {}
        self.slot_words: dict[int, str] = {}
        self.hashes: dict[int, str] = {}
        self.code_digests: dict[tuple[str, int], str] = {}
        self.codes: dict[str, str] = {}

    @property
    def total(self) -> int:
        return len(self.prefix) + len(self.boundaries)

    def reads(self):
        for read in self.prefix:
            yield read
        for read in opening_code_reads(self.boundaries, self.implementations):
            yield read

    def request(self, position: int, read) -> bytes:
        return request_bytes(opening_identifier(self.virtual, position), read["method"], read["params"])

    def accept(self, read, result) -> str:
        """Shape-check one answer, cross-check it against the logs, and keep what it binds.

        Returns the comparable value: the block hash, the implementation
        address, or the code digest.
        """
        kind = read["kind"]
        block = read["block"]
        if kind in ("first-block-header", "epoch-boundary-header"):
            if (
                not isinstance(result, dict)
                or not isinstance(result.get("hash"), str)
                or HASH_RE.fullmatch(result["hash"]) is None
            ):
                raise OpeningRefusal(
                    "malformed-header", block, f"the header read for block {block} carries no hash"
                )
            if _hex(result.get("number"), f"block {block} header number") != block:
                raise OpeningRefusal(
                    "malformed-header", block,
                    f"the header returned for block {block} carries another block number",
                )
            upgrade = self.announced.get(block)
            if upgrade is not None and upgrade["block_hash"] != result["hash"]:
                raise OpeningRefusal(
                    "upgrade-log-mismatch", block,
                    f"the upgrade log at block {block} names a different block hash than "
                    "the preserved block",
                )
            self.hashes[block] = result["hash"]
            return result["hash"]
        if kind == "implementation-slot":
            try:
                implementation = slot_word_address(result, block)
            except AlexandriaError as error:
                raise OpeningRefusal("slot-not-an-address", block, str(error)) from error
            if implementation == ZERO_ADDRESS:
                raise OpeningRefusal(
                    "slot-zero-address", block,
                    f"the implementation slot read at block {block} is the zero address",
                )
            upgrade = self.announced.get(block)
            if upgrade is not None and upgrade["announced"] != implementation:
                raise OpeningRefusal(
                    "upgrade-log-mismatch", block,
                    f"the upgrade log at block {block} announces {upgrade['announced']} while "
                    f"the implementation slot read there holds {implementation}",
                )
            self.implementations[block] = implementation
            self.slot_words[block] = result
            return implementation
        if kind == "implementation-code":
            try:
                code = runtime_code(result, read["address"])
            except AlexandriaError as error:
                raise OpeningRefusal("code-not-hex", block, str(error)) from error
            digest = hashlib.sha256(code).hexdigest()
            self.code_digests[(read["address"], block)] = digest
            self.codes[read["address"]] = result.lower()
            return digest
        raise AlexandriaError(f"unknown opening read kind {kind!r}")

    def compare(self, read, value, second):
        """Whether the second provider's answer binds the same thing, and the kind it is."""
        kind = read["kind"]
        block = read["block"]
        if kind == "first-block-header":
            # The header has to be the first block's own: the right hash under
            # another number is a provider describing some other block.
            agreed = isinstance(second, dict) and second.get("hash") == value
            if agreed:
                try:
                    agreed = _hex(second.get("number"), "first block number") == block
                except AlexandriaError:
                    agreed = False
            return agreed, "first-block-hash", f"block {block}"
        if kind == "implementation-slot":
            try:
                agreed = slot_word_address(second, block) == value
            except AlexandriaError:
                agreed = False
            return agreed, "slot-word", f"implementation slot at block {block}"
        if kind == "implementation-code":
            try:
                agreed = hashlib.sha256(runtime_code(second, read["address"])).hexdigest() == value
            except AlexandriaError:
                agreed = False
            return agreed, "code-digest", f"code of {read['address']} at block {block}"
        raise AlexandriaError(f"opening read kind {kind!r} is not compared")


def staged_results(staging: Staging, name: str) -> list:
    """The `result` of every staged response of one class, in journal order."""
    results = []
    for entry in staging.entries(name):
        envelope = load_bytes(
            entry["response"].encode(), f"staged {name} response",
            max_bytes=MAX_RAW_COMPONENT_BYTES,
        )
        results.append(envelope.get("result") if isinstance(envelope, dict) else None)
    return results


def staged_log_records(staging: Staging, declared) -> list:
    """Every log record the shards preserved, or none when the plan omits logs."""
    if "logs" not in declared:
        return []
    records = []
    for result in staged_results(staging, "logs"):
        if isinstance(result, list):
            records.extend(result)
    return records


def require_committed_journals(staging: Staging, state: dict, purpose: str) -> None:
    """Refuse a tree whose journals hold bytes the checkpoint has not committed.

    Once the last shard commits, `next_shard` stays one past the plan while the
    opening reads are still being made, so it no longer says that every staged
    byte is committed. The checkpoint's offsets do: a journal longer than its
    offset holds a read the collector would truncate and re-issue on resume,
    and a release or a reconciliation built over it would carry bytes the
    collector does not stand behind. A journal shorter than its offset is a
    tree something else has cut.
    """
    for name in staging.journal_names:
        size = staging.journal_bytes(name)
        offset = state["offsets"].get(name, 0)
        if size > offset:
            raise AlexandriaError(
                f"the {name} journal holds bytes the checkpoint has not committed "
                f"({size} bytes on disk, {offset} committed), so there is nothing to {purpose}"
            )
        if size < offset:
            raise AlexandriaError(
                f"the {name} journal is shorter than its committed offset "
                f"({size} bytes on disk, {offset} committed), so there is nothing to {purpose}"
            )


def replay_opening(plan, staging: Staging, classes, registry=None) -> tuple[OpeningPhase, list]:
    """Replay the committed opening reads against the plan they were made from.

    Returns the phase, holding every accepted value, and one
    `(position, read, value, payload)` per read in plan order. Refuses a
    journal that stops short of the plan, runs past it, or holds a record the
    plan does not name at that position. Reads no network and changes no file.
    """
    phase = opening_phase(plan, staged_log_records(staging, classes), registry=registry)
    entries = list(staging.entries(OPENING_CLASS))
    virtual = len(plan["shards"])
    replayed = []
    position = 0
    for read in phase.reads():
        if position >= len(entries):
            raise AlexandriaError(
                "the interval's opening reads are not completely collected, so the "
                "epoch-evidence journal cannot be believed"
            )
        entry = entries[position]
        payload = opening_request(plan, position, read)
        if (
            not isinstance(entry, dict)
            or set(entry) != {"class", "request", "response", "shard"}
            or entry["class"] != OPENING_CLASS
            or entry["shard"] != virtual
            or entry["request"].encode() != payload
        ):
            raise AlexandriaError(
                f"committed opening read {position} is not the read the plan names there"
            )
        result = opening_result(
            plan, position, entry["response"], f"staged opening read {position}"
        )
        value = phase.accept(read, result)
        replayed.append((position, read, value, payload))
        position += 1
    if len(entries) > position:
        raise AlexandriaError(
            "the epoch-evidence journal holds more committed reads than the plan names"
        )
    return phase, replayed


def opening_request(plan, position: int, read) -> bytes:
    """The request bytes of one opening read, whichever venue planned it."""
    return request_bytes(
        opening_identifier(len(plan["shards"]), position), read["method"], read["params"]
    )


def epochs_from_opening(plan, phase, end_hash: str, *, legacy=False):
    """The epoch table the preserved opening reads derive, and nothing else.

    A venue-owned phase derives its own table, keyed by subject; what follows
    describes the single-proxy phase.

    Every input is a value `OpeningPhase.accept` took from a journaled read:
    the upgrade logs the shards preserved, the slot word at each boundary, the
    code each implementation answered, and the header hashes at the first
    block and around each upgrade. The interval's last block is bound by the
    last shard's boundary read, which is the one hash the opening phase does
    not make itself.
    """
    if not isinstance(phase, OpeningPhase):
        if legacy:
            raise AlexandriaError("a venue-owned opening phase derives no block-only epoch table")
        return phase.epochs(end_hash)
    interval = plan["interval"]
    block_hashes = {str(block): value for block, value in phase.hashes.items()}
    block_hashes[str(int(interval["end"]))] = end_hash
    discover = discover_block_epochs if legacy else discover_epochs
    return discover(
        chain=plan["chain"],
        deployment=plan["deployment"],
        proxy=plan["proxy"],
        interval=dict(interval),
        upgrade_logs=[upgrade["record"] for upgrade in phase.upgrades] if legacy else phase.logs,
        slot_reads={str(block): word for block, word in phase.slot_words.items()},
        code_reads=dict(phase.codes),
        block_hashes=block_hashes,
    )


def shard_requests(plan, shard) -> list[tuple[str, str, list]]:
    """The requests one shard makes: one per declared class, in the plan's order.

    A v1 plan's single `proxy` filters `eth_getLogs` by one address and
    `trace_filter` by a one-element `toAddress`, exactly as before. A v2
    plan's declared `subjects` filters both by the whole array instead.
    """
    start = hex(shard["start"])
    end = hex(shard["end"])
    if "subjects" in plan:
        address_filter = list(plan["subjects"])
        to_address = list(plan["subjects"])
    else:
        address_filter = plan["proxy"]
        to_address = [plan["proxy"]]
    requests = {
        "boundary-blocks": ("eth_getBlockByNumber", [end, False]),
        "logs": ("eth_getLogs", [{"address": address_filter, "fromBlock": start, "toBlock": end}]),
        "traces": ("trace_filter", [{"fromBlock": start, "toAddress": to_address, "toBlock": end}]),
    }
    return [(name, *requests[name]) for name in plan["evidence_classes"]]


def _plan_subjects(plan):
    """The plan's declared subject or subjects, whichever field it carries."""
    return plan["subjects"] if "subjects" in plan else plan["proxy"]


def declared_classes(plan) -> tuple:
    """The plan's evidence classes, which must include the shard boundary class.

    Every shard is checkpointed and rewound by its boundary block's hash, and
    every release names that hash, so a plan that omits `boundary-blocks` is one
    this collector cannot walk; it refuses by name rather than reading a class
    the plan did not declare.
    """
    classes = tuple(plan["evidence_classes"])
    if BOUNDARY_CLASS not in classes:
        raise AlexandriaError(
            "the plan must declare the boundary-blocks evidence class; every shard "
            "is bound by its boundary block"
        )
    # The targeted-trace derivation reads a shard's own `logs` result instead of
    # calling `trace_filter`; a subject-set plan that declares `traces` without
    # `logs` gives it nothing to derive transaction hashes from.
    if "subjects" in plan and "traces" in classes and "logs" not in classes:
        raise AlexandriaError(
            "a subject-set plan declaring traces must also declare logs; the targeted "
            "trace derivation reads a shard's own logs result"
        )
    return classes


class _FetchedShard:
    """One shard's whole set of request/response entries, not yet staged.

    `entries` is `[(name, payload, data, result), ...]` in the plan's
    declared-class order -- the order a strictly sequential collection would
    have written them in. Building this holds nothing the caller must not
    also hold: it carries no file handle and no lock. `fetch_seconds` is wall
    time spent inside `_fetch_shard` alone (network only), reported by the
    per-shard heartbeat once this shard is written.
    """

    __slots__ = ("index", "shard", "entries", "boundary", "fetch_seconds")

    def __init__(self, index, shard, entries, boundary, fetch_seconds) -> None:
        self.index = index
        self.shard = shard
        self.entries = entries
        self.boundary = boundary
        self.fetch_seconds = fetch_seconds


class Collector:
    """One bounded collection over one plan, against one transport."""

    def __init__(
        self, plan, staging_root, transport, *, receipts_root=None, registry=None,
        concurrency=1,
    ) -> None:
        validate_plan(plan)
        self.plan = plan
        self.registry = registry
        self._held = {}
        # The opening reads come after the last shard. A plan whose venue
        # cannot plan them -- an unregistered venue, a subject set under a
        # single-proxy venue, a registry the venue refuses -- is refused here,
        # before a shard is requested, rather than after every shard is paid for.
        opening_phase(plan, [], registry=registry)
        self.digest = plan_digest(plan)
        self.classes = declared_classes(plan)
        # The release this collection is for has to be buildable: a split that
        # derives more components than a release may carry refuses here.
        journal_components(plan, self.classes)
        self.transport = transport
        self.provider = plan["provider"]
        self.staging = Staging(staging_root, plan)
        root = Path(receipts_root) if receipts_root else self.staging.root
        self.receipts = root / RECEIPTS_DIRECTORY
        try:
            self.receipts.mkdir(exist_ok=True)
        except OSError as exc:
            raise AlexandriaError(f"cannot open the receipts directory: {exc}") from exc
        if self.receipts.is_symlink() or not self.receipts.is_dir():
            raise AlexandriaError("the receipts directory is not a directory")
        self._started = None
        self._bytes = 0
        self._bytes_lock = threading.Lock()
        if not isinstance(concurrency, int) or isinstance(concurrency, bool) or not 1 <= concurrency <= MAX_COLLECT_CONCURRENCY:
            raise AlexandriaError(
                f"collect concurrency must be a whole number from 1 to {MAX_COLLECT_CONCURRENCY}"
            )
        self.concurrency = concurrency
        # The multi-subject path's targeted trace derivation matches against
        # this lowercase set; a single-proxy plan never reaches it, so it is
        # None there.
        self._subjects = frozenset(address.lower() for address in plan["subjects"]) if "subjects" in plan else None

    # -- bounds -----------------------------------------------------------

    def _spend(self, count: int) -> None:
        with self._bytes_lock:
            self._bytes += count
            over_bytes = self._bytes > MAX_COLLECT_BYTES
            over_time = (
                self._started is not None
                and time.monotonic() - self._started > MAX_COLLECT_SECONDS
            )
        if over_bytes:
            raise AlexandriaError("collection exceeded its total byte ceiling")
        if over_time:
            raise AlexandriaError("collection exceeded its elapsed-time ceiling")

    # -- one request ------------------------------------------------------

    def _ask(
        self, shard_index: int, name: str, method: str, params, *, identifier=None, label=None,
    ) -> tuple[bytes, bytes, object]:
        if identifier is None:
            identifier = request_identifier(shard_index, name)
        payload = request_bytes(identifier, method, params)
        self._spend(len(payload))
        if label is None:
            label = f"shard {shard_index} {name}"
        try:
            data = self.transport.request(payload, label)
        except AlexandriaError:
            self.record_error(shard_index, name, "transport")
            raise
        if len(data) > MAX_RAW_COMPONENT_BYTES:
            self.record_error(shard_index, name, "oversized-response", len(data))
            raise AlexandriaError(f"{label} exceeded the component byte ceiling")
        self._spend(len(data))
        try:
            envelope = load_raw_json(
                data, label, max_bytes=MAX_RAW_COMPONENT_BYTES, max_nodes=MAX_RESPONSE_NODES,
                preserve_integers=True,
            )
        except AlexandriaError:
            self.record_error(shard_index, name, "malformed-response")
            raise
        if not isinstance(envelope, dict) or envelope.get("jsonrpc") != "2.0" or envelope.get("id") != identifier:
            self.record_error(shard_index, name, "envelope-mismatch")
            raise AlexandriaError(f"{label} envelope does not match its request")
        if "error" in envelope:
            code = envelope["error"].get("code") if isinstance(envelope["error"], dict) else None
            self.record_error(
                shard_index, name, "json-rpc-error",
                code if isinstance(code, int) and not isinstance(code, bool) else None,
            )
            raise AlexandriaError(f"{label} returned a JSON-RPC error")
        if "result" not in envelope:
            self.record_error(shard_index, name, "no-result")
            raise AlexandriaError(f"{label} carried neither result nor error")
        result = envelope["result"]
        if isinstance(envelope.get("truncated"), bool) and envelope["truncated"]:
            self.record_error(shard_index, name, "truncated-response")
            raise AlexandriaError(f"{label} was marked truncated")
        if isinstance(result, list) and len(result) >= self.provider["page_limit"]:
            self.record_error(shard_index, name, "page-limit", len(result))
            raise AlexandriaError(
                f"{label} returned a page at the provider's limit, so it may be short"
            )
        return payload, data, result

    def record_error(self, shard_index: int, name: str, code: str, status=None, *, block=None) -> None:
        """Append one receipt built here, not copied from anything the provider said.

        A receipt is a durable file, and the only text a transport can reach is
        its own exception message. A caller-supplied transport that puts its
        endpoint in that message would otherwise write the endpoint, and any
        credential inside it, straight to disk. So nothing from an exception is
        copied: the receipt carries the code this module chose, the class, the
        shard, the unresolved range, the provider class the plan declared, and
        one bounded status this module computed. The exception text still
        reaches the operator on stderr, which is not a file this writes.

        An opening read is filed under the virtual shard index with the one
        block it did not resolve as its range.
        """
        shard = self.plan["shards"][shard_index] if 0 <= shard_index < len(self.plan["shards"]) else None
        if status is not None and not isinstance(status, (int, str)):
            raise AlexandriaError("an error receipt status must be a number or a short string")
        if isinstance(status, str) and (len(status) > 64 or not status.replace("-", "").isalnum()):
            raise AlexandriaError("an error receipt status string must be short and plain")
        unresolved = {"end": shard["end"], "start": shard["start"]} if shard else None
        if block is not None:
            if not isinstance(block, int) or isinstance(block, bool) or block < 0:
                raise AlexandriaError("an error receipt block must be a block number")
            unresolved = {"end": block, "start": block}
        receipt = {
            "class": name if name in JOURNAL_CLASSES else "boundary",
            "code": code,
            "provider_class": self.provider["class"],
            "shard": shard_index,
            "status": status,
            "unresolved": unresolved,
        }
        path = self.receipts / ERROR_RECEIPTS
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags, 0o600)
        except OSError as exc:
            raise AlexandriaError(f"cannot open the error receipt file: {exc}") from exc
        try:
            with os.fdopen(descriptor, "ab", closefd=False) as handle:
                handle.write(canonical_bytes(receipt))
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            os.close(descriptor)

    # -- the loop ---------------------------------------------------------

    def _finality_header(self, block, label: str) -> dict:
        """One bounded header read on the finality path, with its own receipt on refusal."""
        payload = request_bytes(0, "eth_getBlockByNumber", [block, False])
        self._spend(len(payload))
        try:
            data = self.transport.request(payload, label)
        except AlexandriaError:
            self.record_error(-1, "finality", "transport")
            raise
        self._spend(len(data))
        try:
            envelope = load_raw_json(
                data, label, max_bytes=MAX_RAW_COMPONENT_BYTES,
                max_nodes=MAX_RESPONSE_NODES, preserve_integers=True,
            )
        except AlexandriaError:
            self.record_error(-1, "finality", "malformed-response")
            raise
        header = envelope.get("result") if isinstance(envelope, dict) else None
        if not isinstance(header, dict):
            self.record_error(-1, "finality", "no-result")
            raise AlexandriaError(f"the {label} response carries no header")
        return header

    def bind_finality(self) -> dict:
        """Bind the plan's boundary block before any shard, surviving a moved tag.

        The plan's boundary block is read by number and its hash must equal the
        plan's: that is the claim the release makes. Under `finalized` or
        `safe`, the tag is then read and its number must be at or above the
        boundary. The tag itself moves every epoch, so a plan written before
        the run, or resumed after a pause, stays valid for as long as its
        boundary block stays on the chain, which is what the policy promises.
        A boundary that left the chain refuses by name with a receipt.
        """
        declared = self.plan["finality"]
        policy = declared["policy"]
        number = _number(declared["block_number"])
        header = self._finality_header(hex(number), f"finality boundary block {number}")
        if header.get("hash") != declared["block_hash"]:
            self.record_error(-1, "finality", "boundary-hash-mismatch", number)
            raise AlexandriaError(
                f"block {number} does not match the plan's {policy} boundary hash; "
                "the boundary block is no longer on the chain the plan was written against"
            )
        if _hex(header.get("number"), "finality boundary number") != number:
            self.record_error(-1, "finality", "boundary-number-mismatch", number)
            raise AlexandriaError(
                f"the header returned for block {number} carries another block number"
            )
        if policy in FINALITY_TAGS:
            tag = FINALITY_TAGS[policy]
            current = self._finality_header(tag, f"finality boundary under {policy}")
            current_number = _hex(current.get("number"), f"{policy} tag block number")
            if current_number < number:
                self.record_error(-1, "finality", "boundary-not-yet-final", current_number)
                raise AlexandriaError(
                    f"the {policy} tag stands at block {current_number}, below the plan's "
                    f"boundary block {number}"
                )
            if current_number == number and current.get("hash") != declared["block_hash"]:
                # The tag stands exactly on the boundary and names it by another
                # hash: the provider contradicts its own by-number read, or the
                # plan was written against a block the chain did not finalize.
                self.record_error(-1, "finality", "tag-hash-mismatch", number)
                raise AlexandriaError(
                    f"the {policy} tag stands at block {number} under a hash other than "
                    "the plan's boundary hash"
                )
        return header

    def _boundary_hash(self, shard_index: int) -> str:
        """Re-read one already accepted shard's boundary block."""
        shard = self.plan["shards"][shard_index]
        payload = request_bytes(
            request_identifier(shard_index, "boundary-blocks"),
            "eth_getBlockByNumber", [hex(shard["end"]), False],
        )
        self._spend(len(payload))
        try:
            data = self.transport.request(payload, f"shard {shard_index} boundary re-read")
        except AlexandriaError:
            self.record_error(shard_index, "boundary-re-read", "transport")
            raise
        self._spend(len(data))
        envelope = load_raw_json(
            data, f"shard {shard_index} boundary re-read", max_bytes=MAX_RAW_COMPONENT_BYTES,
            max_nodes=MAX_RESPONSE_NODES, preserve_integers=True,
        )
        header = envelope.get("result") if isinstance(envelope, dict) else None
        if not isinstance(header, dict) or not isinstance(header.get("hash"), str):
            self.record_error(shard_index, "boundary-re-read", "no-result")
            raise AlexandriaError(f"shard {shard_index} boundary re-read carries no block hash")
        return header["hash"]

    def _settle_start(self) -> int:
        """Resume, then rewind past any boundary whose hash has changed under us."""
        state = self.staging.resume()
        if state["next_shard"] == 0:
            return 0
        for entry in reversed(state["history"]):
            if self._boundary_hash(entry["shard"]) == entry["block_hash"]:
                if entry["shard"] == state["next_shard"] - 1:
                    return state["next_shard"]
                self.staging.rewind_to(entry["shard"])
                return entry["shard"] + 1
        if state["history"] and state["history"][0]["shard"] == 0:
            self.staging.discard()
            return 0
        raise AlexandriaError(
            "the chain moved under every remembered boundary; the reorg is deeper "
            "than the checkpoint's rewind history"
        )

    def collect(self) -> dict:
        """Collect, and release every journal handle this run opened however it ends.

        `Staging` keeps one handle per physical journal until `close`, and a
        split plan owns one per component, so the refusal path closes them.
        """
        try:
            summary = self._collect()
        except BaseException:
            # The refusal is what the operator reads; a close that fails too
            # still releases every handle and does not replace it.
            try:
                self.staging.close()
            except AlexandriaError:
                pass
            raise
        self.staging.close()
        return summary

    def _collect(self) -> dict:
        self._started = time.monotonic()
        self.bind_finality()
        start = self._settle_start()
        # A venue's preliminary reads, and any refusal, precede the first shard.
        self._preliminary_reads()
        shards = self.plan["shards"]
        counts = {name: 0 for name in self.classes}
        total = len(shards)
        if start < total:
            if self.concurrency == 1:
                self._collect_sequential(start, total, counts)
            else:
                self._collect_shards(start, total, counts)
        opening = self._open_interval()
        return {
            "collected_shards": total - start,
            "opening_reads": opening,
            "record_counts": counts,
            "resumed_from": start,
            "shards": total,
        }

    def _collect_sequential(self, start: int, total: int, counts: dict) -> None:
        """The original one-shard-at-a-time loop: request, then stage, per class.

        Reached whenever `self.concurrency == 1` -- the default for any
        caller that never asks for concurrency, which is every existing call
        site and test. Each request's bytes are staged the moment they are
        read, before the shard's next request is even made, exactly as
        collection has always worked; a kill mid-shard leaves whatever
        prefix of that shard's classes were already staged; `resume` decides
        what survives that, unchanged by anything below.
        """
        shards = self.plan["shards"]
        for index in range(start, total):
            shard = shards[index]
            boundary = None
            logs_result = None
            shard_counts = {}
            started = time.monotonic()
            for name, method, params in shard_requests(self.plan, shard):
                if name == "traces" and self._subjects is not None:
                    payload, data, result = self._targeted_traces(index, logs_result)
                else:
                    payload, data, result = self._ask(index, name, method, params)
                    if name == "logs":
                        logs_result = result
                if name == "boundary-blocks":
                    if not isinstance(result, dict) or not isinstance(result.get("hash"), str):
                        raise AlexandriaError(f"shard {index} boundary block carries no hash")
                    boundary = result["hash"]
                count = len(result) if isinstance(result, list) else 1
                counts[name] += count
                shard_counts[name] = count
                self.staging.record(index, name, payload, data)
            self.staging.commit(index, shard["end"], boundary)
            self._heartbeat(index, shard, shard_counts, time.monotonic() - started)

    def _fetch_shard(self, index: int) -> "_FetchedShard":
        """Every request one shard makes, without writing anything to the staging tree.

        Safe to call from a worker thread: nothing here touches `self.staging`,
        only `self.transport` (a fresh call per request) and `_spend`'s locked
        counters. The multi-subject path's `traces` class is derived here too
        -- through `_targeted_traces`, from this same call's own `logs`
        result -- rather than left for the writer to redo.
        """
        shard = self.plan["shards"][index]
        entries = []
        boundary = None
        logs_result = None
        started = time.monotonic()
        for name, method, params in shard_requests(self.plan, shard):
            if name == "traces" and self._subjects is not None:
                payload, data, result = self._targeted_traces(index, logs_result)
            else:
                payload, data, result = self._ask(index, name, method, params)
                if name == "logs":
                    logs_result = result
            if name == "boundary-blocks":
                if not isinstance(result, dict) or not isinstance(result.get("hash"), str):
                    raise AlexandriaError(f"shard {index} boundary block carries no hash")
                boundary = result["hash"]
            entries.append((name, payload, data, result))
        return _FetchedShard(
            index=index, shard=shard, entries=entries, boundary=boundary,
            fetch_seconds=time.monotonic() - started,
        )

    def _write_shard(self, fetched: "_FetchedShard", counts: dict) -> None:
        """Stage and commit one already-fetched shard, in its fetched (plan) order."""
        shard_counts = {}
        for name, payload, data, result in fetched.entries:
            count = len(result) if isinstance(result, list) else 1
            counts[name] += count
            shard_counts[name] = count
            self.staging.record(fetched.index, name, payload, data)
        self.staging.commit(fetched.index, fetched.shard["end"], fetched.boundary)
        self._heartbeat(fetched.index, fetched.shard, shard_counts, fetched.fetch_seconds)

    def _heartbeat(self, index: int, shard: dict, shard_counts: dict, fetch_seconds: float) -> None:
        """One flushed progress line to stderr, right after a shard commits.

        A console line only: it is never staged, never journaled, and reading
        it establishes nothing `check` or `reconcile` reads -- only a human
        watching the run. Printed to stderr, not stdout, so a caller that
        parses `collect`'s stdout (the final JSON summary, written once at
        exit) never sees it mixed in; `collect ... > collect.log 2>&1 &` then
        `tail -f collect.log` still shows both together, live, per shard.
        """
        total = len(self.plan["shards"])
        elapsed = time.monotonic() - self._started
        counted = " ".join(
            f"{name} {shard_counts.get(name, 0)}" for name in self.classes if name != BOUNDARY_CLASS
        )
        print(
            f"[collect] shard {index + 1}/{total} done | blocks {shard['start']}-{shard['end']} | "
            f"this shard {fetch_seconds:.1f}s | elapsed {elapsed:.1f}s | {counted}",
            file=sys.stderr, flush=True,
        )

    def _collect_shards(self, start: int, total: int, counts: dict) -> None:
        """Fetch shards `start` to `total - 1` with a bounded worker pool, ordered commits.

        Fetches may finish out of arrival order; `Staging.commit` never does.
        `index` only ever advances by one and each advance blocks on that
        exact shard's future, so a killed run's checkpoint always names a
        contiguous committed prefix with no gap -- the same resumability a
        strictly sequential loop gives, just fetched with real concurrency. A
        shard whose fetch finishes early still waits, uncommitted and only
        held in memory, until every lower-indexed shard is committed first.
        """
        concurrency = min(self.concurrency, total - start)
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=concurrency)
        pending = {}
        next_to_submit = start

        def _submit_up_to(limit):
            nonlocal next_to_submit
            while next_to_submit < total and len(pending) < limit:
                pending[next_to_submit] = pool.submit(self._fetch_shard, next_to_submit)
                next_to_submit += 1

        try:
            _submit_up_to(concurrency)
            for index in range(start, total):
                fetched = pending.pop(index).result()
                self._write_shard(fetched, counts)
                _submit_up_to(concurrency)
        finally:
            # `cancel_futures` drops anything still queued rather than paying
            # for it after a refusal; a fetch already running finishes on its
            # own and its result is simply never written.
            pool.shutdown(wait=True, cancel_futures=True)

    def _targeted_traces(self, shard_index: int, logs_result) -> tuple[bytes, bytes, list]:
        """One shard's whole `traces` result, without ever calling `trace_filter`.

        Only reached on the multi-subject path (`self._subjects` is not
        `None`). Derives the distinct transaction hashes this shard's own
        `logs` result touched (`subject_transaction_hashes`; no new
        `eth_getLogs` call), asks `trace_transaction` once per hash, and
        filters each transaction's frames down to the ones a blanket
        `trace_filter` call's `toAddress` parameter would have kept
        (`_matches_subjects`). The concatenation, in hash order, is the whole
        shard's `traces` result; the caller records it exactly once, the same
        as every other class -- see `Staging.record`'s one-record-per-shard
        contract, which this method must never call more than the one time
        its return value is written.
        """
        if logs_result is None:
            raise AlexandriaError(
                f"shard {shard_index}: the targeted trace derivation needs this shard's "
                "logs result, which was not read before traces this shard"
            )
        hashes = subject_transaction_hashes(logs_result)
        combined = []
        for tx_hash in hashes:
            _, _, trace_result = self._ask(
                shard_index, "traces", "trace_transaction", [tx_hash],
                label=f"shard {shard_index} traces {tx_hash}",
            )
            if not isinstance(trace_result, list):
                raise AlexandriaError(
                    f"shard {shard_index} trace_transaction {tx_hash} did not return a list"
                )
            combined.extend(frame for frame in trace_result if _matches_subjects(frame, self._subjects))
        identifier = request_identifier(shard_index, "traces")
        payload = request_bytes(identifier, "trace_transaction", hashes)
        response = canonical_bytes({"id": identifier, "jsonrpc": "2.0", "result": combined})
        if len(response) > MAX_RAW_COMPONENT_BYTES:
            raise AlexandriaError(
                f"shard {shard_index} traces combined record exceeded the component byte ceiling"
            )
        return payload, response, combined

    # -- the opening phase --------------------------------------------------

    def _committed_opening(self, entry, position: int, read, payload: bytes, label: str):
        """The result of one committed opening read, or a refusal naming its position."""
        virtual = len(self.plan["shards"])
        if (
            set(entry) != {"class", "request", "response", "shard"}
            or entry["class"] != OPENING_CLASS
            or entry["shard"] != virtual
            or entry["request"].encode() != payload
        ):
            self.record_error(virtual, OPENING_CLASS, "opening-journal-mismatch", position, block=read["block"])
            raise AlexandriaError(
                f"committed opening read {position} is not the read the plan names there"
            )
        try:
            return opening_result(self.plan, position, entry["response"], f"staged {label}")
        except AlexandriaError:
            self.record_error(
                virtual, OPENING_CLASS, "opening-journal-mismatch", position, block=read["block"],
            )
            raise

    def _preliminary_reads(self) -> None:
        """Make a venue's preliminary opening reads before any shard is requested.

        They need no shard and can refuse the collection. Each is asked with
        the request bytes of the opening-journal position it will take, and
        its answer is held: a checkpoint cannot commit an opening read while a
        shard is uncollected, so `_open_interval` journals the held bytes after
        the last shard. A run stopped before then asks again; a journal that
        already holds them is replayed.
        """
        self._held = {}
        phase = opening_phase(self.plan, [], registry=self.registry)
        preliminary = getattr(phase, "preliminary_reads", None)
        if preliminary is None:
            return
        virtual = len(self.plan["shards"])
        committed = list(self.staging.entries(OPENING_CLASS))
        for position, read in enumerate(preliminary()):
            payload = opening_request(self.plan, position, read)
            label = opening_label(position, read)
            if position < len(committed):
                result = self._committed_opening(committed[position], position, read, payload, label)
            else:
                _payload, data, result = self._ask(
                    virtual, OPENING_CLASS, read["method"], read["params"],
                    identifier=opening_identifier(virtual, position), label=label,
                )
                self._held[position] = (payload, data, result)
            try:
                phase.accept(read, result)
            except OpeningRefusal as refusal:
                self.record_error(virtual, OPENING_CLASS, refusal.code, refusal.block, block=refusal.block)
                raise

    def _open_interval(self) -> dict:
        """Read what binds the interval's start and its epochs, after the last shard.

        Every read is one `epoch-evidence` record under the virtual shard index
        and is checkpointed on its own, by committing the last shard's boundary
        again with the journal's new offset. A resumed run replays the
        committed records against the same plan, re-checks each one, and
        issues only the reads past them; a committed record that is not the
        read the plan names there refuses rather than being read around. The
        checkpoint after the last shard therefore answers two questions
        without the process: `next_shard` one past the plan says the shards
        are done, and the `epoch-evidence` offset says how many opening reads
        are committed.
        """
        accepted = self.staging.last_accepted()
        if accepted is None or accepted["shard"] != len(self.plan["shards"]) - 1:
            raise AlexandriaError("the opening phase needs every shard committed first")
        virtual = len(self.plan["shards"])
        try:
            phase = opening_phase(
                self.plan, staged_log_records(self.staging, self.classes), registry=self.registry
            )
        except AlexandriaError:
            code = (
                "malformed-upgrade-log" if plan_venue(self.plan).EPOCH_MODEL == EIP1967_MODEL
                else "malformed-staged-log"
            )
            self.record_error(virtual, OPENING_CLASS, code)
            raise
        committed = list(self.staging.entries(OPENING_CLASS))
        issued = 0
        position = 0
        for read in phase.reads():
            payload = opening_request(self.plan, position, read)
            label = opening_label(position, read)
            held = self._held.get(position)
            if position < len(committed):
                result = self._committed_opening(committed[position], position, read, payload, label)
                data = None
            elif held is not None and held[0] == payload:
                # Asked before the first shard; these are the bytes it answered.
                _payload, data, result = held
            else:
                _payload, data, result = self._ask(
                    virtual, OPENING_CLASS, read["method"], read["params"],
                    identifier=opening_identifier(virtual, position), label=label,
                )
            try:
                phase.accept(read, result)
            except OpeningRefusal as refusal:
                self.record_error(virtual, OPENING_CLASS, refusal.code, refusal.block, block=refusal.block)
                raise
            if data is not None:
                self.staging.record(virtual, OPENING_CLASS, payload, data)
                self.staging.commit(
                    accepted["shard"], accepted["block_number"], accepted["block_hash"]
                )
                issued += 1
            position += 1
        if len(committed) > position:
            self.record_error(virtual, OPENING_CLASS, "opening-journal-mismatch", len(committed))
            raise AlexandriaError(
                "the epoch-evidence journal holds more committed reads than the plan names"
            )
        return {"issued": issued, "resumed_from": position - issued, "total": position}



class Reconciler:
    """Run a completed staging tree past a second provider.

    A disagreement is never settled here. Neither provider wins by answering
    first or by being in a majority of two, so the record says which identities
    disagreed and both sets of bytes are kept.
    """

    def __init__(self, plan, staging_root, transport, provider_class, *, registry=None) -> None:
        validate_plan(plan)
        self.plan = plan
        self.registry = registry
        opening_phase(plan, [], registry=registry)
        self.transport = transport
        if not isinstance(provider_class, str) or not 1 <= len(provider_class) <= 256:
            raise AlexandriaError("the second provider class is not a bounded name")
        if any(character in provider_class for character in ("://", "@")):
            raise AlexandriaError("the second provider class must not carry an endpoint")
        self.provider_class = provider_class
        self.classes = declared_classes(plan)
        journal_components(plan, self.classes)
        self.staging = Staging(staging_root, plan)
        self.root = self.staging.root
        # The multi-subject path's targeted trace derivation matches against
        # this lowercase set; a single-proxy plan never reaches it, so it is
        # None there.
        self._subjects = frozenset(address.lower() for address in plan["subjects"]) if "subjects" in plan else None
        directory = self.root / RECONCILIATION_DIRECTORY
        try:
            directory.mkdir(exist_ok=True)
        except OSError as exc:
            raise AlexandriaError(f"cannot open the reconciliation directory: {exc}") from exc
        if directory.is_symlink() or not directory.is_dir():
            raise AlexandriaError("the reconciliation directory is not a directory")
        self.directory = directory

    def _staged(self) -> dict:
        """The primary's responses, keyed by shard and class."""
        staged = {}
        for name in self.classes:
            for entry in self.staging.entries(name):
                envelope = load_bytes(
                    entry["response"].encode(), f"staged {name} response",
                    max_bytes=MAX_RAW_COMPONENT_BYTES,
                )
                staged[(entry["shard"], name)] = envelope.get("result")
        return staged

    def _second(self, shard_index: int, name: str, method: str, params):
        identifier = request_identifier(shard_index, name)
        payload = request_bytes(identifier, method, params)
        return self._second_raw(payload, identifier, f"shard {shard_index} {name}")

    def _second_raw(self, payload: bytes, identifier: int, label: str):
        """Ask the second provider the exact bytes the primary was asked."""
        data = self.transport.request(payload, f"{label} second provider")
        if len(data) > MAX_RAW_COMPONENT_BYTES:
            raise AlexandriaError(
                f"{label} second-provider response exceeded the byte ceiling"
            )
        envelope = load_raw_json(
            data, f"{label} second provider",
            max_bytes=MAX_RAW_COMPONENT_BYTES, max_nodes=MAX_RESPONSE_NODES,
            preserve_integers=True,
        )
        if (
            not isinstance(envelope, dict)
            or envelope.get("jsonrpc") != "2.0"
            or envelope.get("id") != identifier
            or "result" not in envelope
        ):
            raise AlexandriaError(
                f"{label} second-provider envelope does not match its request"
            )
        return envelope["result"], data

    def _second_traces(self, shard_index: int, hashes) -> tuple:
        """Ask the second provider `trace_transaction` for each hash, filtered and combined.

        Mirrors `Collector._targeted_traces`, against `self.transport`
        instead of the primary's: one `trace_transaction` call per hash, each
        frame kept only if `_matches_subjects` would have kept it, all
        concatenated in hash order. Never staged and never journaled, only
        compared -- and kept via `_keep` when the comparison disagrees.
        """
        combined = []
        for tx_hash in hashes:
            identifier = request_identifier(shard_index, "traces")
            payload = request_bytes(identifier, "trace_transaction", [tx_hash])
            result, _data = self._second_raw(
                payload, identifier, f"shard {shard_index} traces {tx_hash}",
            )
            if not isinstance(result, list):
                raise AlexandriaError(
                    f"shard {shard_index} second-provider trace_transaction {tx_hash} did not "
                    "return a list"
                )
            combined.extend(frame for frame in result if _matches_subjects(frame, self._subjects))
        identifier = request_identifier(shard_index, "traces")
        combined_bytes = canonical_bytes({"id": identifier, "jsonrpc": "2.0", "result": combined})
        return combined, combined_bytes

    def _opening(self) -> tuple:
        """The opening phase and its committed reads, replayed; see `replay_opening`."""
        return replay_opening(self.plan, self.staging, self.classes, self.registry)

    def _keep(self, shard_index: int, name: str, data: bytes) -> None:
        """Preserve the second provider's bytes for a shard that disagreed."""
        record = canonical_bytes({
            "class": name,
            "provider_class": self.provider_class,
            "response": data.decode("utf-8"),
            "shard": shard_index,
        })
        path = self.directory / DISPUTED_RESPONSES
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags, 0o600)
        except OSError as exc:
            raise AlexandriaError(f"cannot open the disputed-response file: {exc}") from exc
        try:
            with os.fdopen(descriptor, "ab", closefd=False) as handle:
                handle.write(record)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            os.close(descriptor)

    # -- this run's own progress, separate from the collected bytes ---------

    def _checkpoint_path(self) -> Path:
        return self.directory / RECONCILE_CHECKPOINT_NAME

    def _load_reconcile_checkpoint(self):
        """This exact plan and second provider's last saved reconcile progress, or `None`.

        A checkpoint recorded for another plan or another `provider_class`
        proves nothing about this run -- comparisons already counted under a
        different second opinion cannot be carried into this one -- so it is
        treated as absent rather than trusted.
        """
        path = self._checkpoint_path()
        if not path.is_file():
            return None
        document = load_bytes(
            read_confined_file(
                self.directory, RECONCILE_CHECKPOINT_NAME, "reconcile checkpoint",
                max_bytes=MAX_CONTROL_BYTES,
            ),
            "reconcile checkpoint",
        )
        if (
            not isinstance(document, dict)
            or document.get("format") != RECONCILE_CHECKPOINT_FORMAT
            or document.get("plan_sha256") != plan_digest(self.plan)
            or document.get("provider_class") != self.provider_class
        ):
            return None
        required = {"compared", "matched", "disputed", "statuses", "next_shard"}
        if set(document) != required | {"format", "plan_sha256", "provider_class"}:
            raise AlexandriaError("the reconcile checkpoint has an unknown shape")
        if (
            not isinstance(document["next_shard"], int) or isinstance(document["next_shard"], bool)
            or not 0 <= document["next_shard"] <= len(self.plan["shards"])
            or not isinstance(document["compared"], int) or isinstance(document["compared"], bool)
            or not isinstance(document["matched"], int) or isinstance(document["matched"], bool)
            or not isinstance(document["disputed"], list)
            or not isinstance(document["statuses"], dict)
        ):
            raise AlexandriaError("the reconcile checkpoint has an unknown shape")
        return document

    def _save_reconcile_checkpoint(self, compared, matched, disputed, statuses, next_shard) -> None:
        """Checkpoint reconciliation's own progress, one shard's comparisons at a time.

        Not a batch: each shard already costs several real requests to the
        second provider, which dominates a local `fsync` by one to two
        orders of magnitude, so checkpointing every shard keeps that cost
        negligible while guaranteeing a failure never loses more than the
        one shard it happened on.
        """
        document = {
            "compared": compared,
            "disputed": disputed,
            "format": RECONCILE_CHECKPOINT_FORMAT,
            "matched": matched,
            "next_shard": next_shard,
            "plan_sha256": plan_digest(self.plan),
            "provider_class": self.provider_class,
            "statuses": {str(index): status for index, status in statuses.items()},
        }
        _atomic_json(self._checkpoint_path(), document)

    def _record_error(self, shard_index, name: str, exc: Exception) -> None:
        """Append one receipt naming what failed, where, and why -- never silently discarded.

        `shard_index` is a real shard index, or `len(self.plan["shards"])`
        for the opening-reads segment, matching the virtual index shard
        records use. `str(exc)` is bounded and, for every exception this
        actually catches (`TransportError` and the other `AlexandriaError`s
        raised on this path), already carries only a request label, never an
        endpoint or a credential -- see `_close_transport_error` -- but it is
        still truncated here rather than trusted to stay that way forever.
        """
        receipt = {
            "class": name,
            "exception": type(exc).__name__,
            "message": str(exc)[:200],
            "provider_class": self.provider_class,
            "shard": shard_index,
        }
        path = self.directory / ERROR_RECEIPTS
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags, 0o600)
        except OSError as inner:
            raise AlexandriaError(f"cannot open the reconcile error receipt file: {inner}") from inner
        try:
            with os.fdopen(descriptor, "ab", closefd=False) as handle:
                handle.write(canonical_bytes(receipt))
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            os.close(descriptor)

    def _heartbeat(self, label: str, status: str, shard_compared: int, shard_matched: int,
                    shard_disputed: int, started: float) -> None:
        """One flushed progress line to stderr, the same shape `collect` already prints.

        A console line only -- nothing here is staged, journaled or part of
        `reconciliation.json`.
        """
        elapsed = time.monotonic() - started
        print(
            f"[reconcile] {label} | {status} | compared {shard_compared} matched {shard_matched} "
            f"disputed {shard_disputed} | elapsed {elapsed:.1f}s",
            file=sys.stderr, flush=True,
        )

    def reconcile(self) -> dict:
        """Read the staging tree without changing it, then compare.

        Reconciliation never resumes the COLLECTION, because `resume`
        truncates every journal back to its checkpoint, and reading an
        interval must not be able to destroy part of it, least of all on the
        path that then refuses -- that invariant is unchanged. Reconciliation
        now resumes ITS OWN progress instead: `_load_reconcile_checkpoint`
        restores whatever shard-by-shard comparison work an earlier, failed
        attempt against this exact second provider already finished, so a
        transport failure at shard 3,000 does not force shards 0-2,999 to be
        asked again.
        """
        shards = self.plan["shards"]
        state = self.staging.committed()
        if state["next_shard"] != len(shards):
            raise AlexandriaError(
                "the interval is not completely collected, so there is nothing to reconcile"
            )
        require_committed_journals(self.staging, state, "reconcile")
        staged = self._staged()
        for index in range(len(shards)):
            for name in self.classes:
                if (index, name) not in staged:
                    raise AlexandriaError(
                        f"shard {index} has no staged {name} response to reconcile"
                    )
        phase, opening = self._opening()
        # The address every shard read filters on, in the form the plan
        # declares it: one proxy, or the whole subject set.
        subjects = _plan_subjects(self.plan)
        upgrade_topic = phase.upgrade_topic

        checkpoint = self._load_reconcile_checkpoint()
        if checkpoint is None:
            compared, matched, disputed, statuses, start = 0, 0, [], {}, 0
        else:
            compared = checkpoint["compared"]
            matched = checkpoint["matched"]
            disputed = list(checkpoint["disputed"])
            statuses = {int(index): value for index, value in checkpoint["statuses"].items()}
            start = checkpoint["next_shard"]

        counts = {}
        # Shards a checkpoint already covers still need their counts for the
        # final table below; this reads only the already-staged primary
        # bytes, so it is redone rather than checkpointed alongside them.
        for index in range(start):
            counts[index] = self._counts(index, staged)

        started = time.monotonic()
        for shard in shards[start:]:
            index = shard["index"]
            boundary = staged[(index, "boundary-blocks")]
            logs = staged.get((index, "logs"))
            counts[index] = self._counts(index, staged)
            status = "complete"
            compared_before, matched_before, disputed_before = compared, matched, len(disputed)
            try:
                second_boundary, boundary_bytes = self._second(
                    index, "boundary-blocks", "eth_getBlockByNumber", [hex(shard["end"]), False]
                )
                second_logs, logs_bytes = None, b""
                if "logs" in self.classes:
                    second_logs, logs_bytes = self._second(
                        index, "logs", "eth_getLogs",
                        # The primary's own filter, derived from the plan as
                        # the collector derived it: one proxy or every subject.
                        dict(
                            (name, params) for name, _method, params in shard_requests(self.plan, shard)
                        )["logs"],
                    )
                if isinstance(logs, list):
                    proxy_log_positions(
                        logs, subjects, self.plan["interval"], upgrade_topic=upgrade_topic
                    )
                if isinstance(second_logs, list):
                    proxy_log_positions(
                        second_logs, subjects, self.plan["interval"], upgrade_topic=upgrade_topic
                    )
                second_traces, traces_bytes = None, b""
                if "traces" in self.classes and self._subjects is not None:
                    # The primary's own committed hash set, derived from its
                    # own logs -- not a fresh derivation from the second
                    # provider's. A differing hash set is already a
                    # log-identity disagreement, settled above on its own
                    # terms; nothing new is invented for it here.
                    second_traces, traces_bytes = self._second_traces(
                        index, subject_transaction_hashes(logs) if isinstance(logs, list) else []
                    )
            except AlexandriaError as exc:
                self._record_error(index, "second-provider", exc)
                self._save_reconcile_checkpoint(compared, matched, disputed, statuses, index)
                return self._unreconciled(
                    shards, counts, staged, compared, matched, disputed
                )

            compared += 1
            if not isinstance(second_boundary, dict) or second_boundary.get("hash") != boundary.get("hash"):
                status = "failed"
                disputed.append({
                    "identity": f"block {shard['end']}",
                    "kind": "boundary-hash",
                    "shard": index,
                })
                self._keep(index, "boundary-blocks", boundary_bytes)
            else:
                matched += 1
                first_transactions = _transaction_order(boundary)
                second_transactions = _transaction_order(second_boundary)
                compared += 1
                if first_transactions != second_transactions:
                    status = "partial" if status == "complete" else status
                    disputed.append({
                        "identity": f"block {shard['end']} transaction order",
                        "kind": "transaction-order",
                        "shard": index,
                    })
                    self._keep(index, "boundary-blocks", boundary_bytes)
                else:
                    matched += 1

            first_identities = [log_identity(record) for record in logs] if isinstance(logs, list) else []
            second_identities = (
                [log_identity(record) for record in second_logs] if isinstance(second_logs, list) else []
            )
            agreed, disagreements = _identity_comparison(first_identities, second_identities)
            compared += agreed + len(disagreements)
            matched += agreed
            if disagreements:
                if status != "failed":
                    status = "partial"
                self._keep(index, "logs", logs_bytes)
                for identity in disagreements:
                    if len(disputed) < MAX_DISPUTES:
                        disputed.append({"identity": identity, "kind": "log-identity", "shard": index})

            if "traces" in self.classes and self._subjects is not None:
                traces = staged.get((index, "traces"))
                first_trace_identities = (
                    [trace_identity(record) for record in traces] if isinstance(traces, list) else []
                )
                second_trace_identities = (
                    [trace_identity(record) for record in second_traces]
                    if isinstance(second_traces, list) else []
                )
                trace_agreed, trace_disagreements = _identity_comparison(
                    first_trace_identities, second_trace_identities
                )
                compared += trace_agreed + len(trace_disagreements)
                matched += trace_agreed
                if trace_disagreements:
                    if status != "failed":
                        status = "partial"
                    self._keep(index, "traces", traces_bytes)
                    for identity in trace_disagreements:
                        if len(disputed) < MAX_DISPUTES:
                            disputed.append(
                                {"identity": identity, "kind": "trace-identity", "shard": index}
                            )
            statuses[index] = status
            self._save_reconcile_checkpoint(compared, matched, disputed, statuses, index + 1)
            self._heartbeat(
                f"shard {index + 1}/{len(shards)} done", status,
                compared - compared_before, matched - matched_before, len(disputed) - disputed_before,
                started,
            )

        # The opening reads: the first block's hash, each slot word and each
        # code digest, asked of the second provider with the primary's exact
        # request bytes. A disagreement keeps both byte sets and settles
        # nothing; the epoch boundary headers are bound by the upgrade logs
        # the primary preserved and are not asked again. Not checkpointed
        # shard by shard like the loop above -- there are a few hundred of
        # these at most, not thousands, so a failure here just redoes this
        # much smaller segment; the shard loop's own checkpoint still stands.
        virtual = len(shards)
        opening_started = time.monotonic()
        opening_position = 0
        for position, read, value, payload in opening:
            if read["kind"] == "epoch-boundary-header":
                continue
            opening_position += 1
            try:
                second, data = self._second_raw(
                    payload, opening_identifier(virtual, position), opening_label(position, read),
                )
            except AlexandriaError as exc:
                self._record_error(virtual, OPENING_CLASS, exc)
                return self._unreconciled(shards, counts, staged, compared, matched, disputed)
            compared += 1
            agreed, kind, identity = phase.compare(read, value, second)
            if agreed:
                matched += 1
            else:
                if len(disputed) < MAX_DISPUTES:
                    disputed.append({"identity": identity, "kind": kind, "shard": virtual})
                self._keep(virtual, OPENING_CLASS, data)
            self._heartbeat(
                f"opening read {opening_position}", "agreed" if agreed else "disputed",
                1, 1 if agreed else 0, 0 if agreed else 1, opening_started,
            )

        record = {
            "compared": compared,
            "disputed": disputed,
            "matched": matched,
            "provider_class": self.provider_class,
            "status": "disputed" if disputed else "agreed",
        }
        return self._write(shards, counts, statuses, record, staged)

    def _counts(self, index: int, staged) -> dict:
        """One record count per declared class, derived from the staged bytes."""
        counts = {}
        for name in self.classes:
            result = staged[(index, name)]
            counts[name] = len(result) if isinstance(result, list) else 1
        return counts

    def _unreconciled(self, shards, counts, staged, compared=0, matched=0, disputed=None) -> dict:
        for shard in shards:
            counts.setdefault(shard["index"], self._counts(shard["index"], staged))
        record = {
            "compared": compared,
            "disputed": list(disputed or []),
            "matched": matched,
            "provider_class": self.provider_class,
            "status": "unreconciled",
        }
        statuses = {shard["index"]: "complete" for shard in shards}
        return self._write(shards, counts, statuses, record, staged)

    def _write(self, shards, counts, statuses, record, staged) -> dict:
        table = [
            {
                "end": shard["end"],
                "end_hash": staged[(shard["index"], "boundary-blocks")]["hash"],
                "index": shard["index"],
                "record_counts": counts[shard["index"]],
                "start": shard["start"],
                "status": statuses[shard["index"]],
            }
            for shard in shards
        ]
        validate_shard_coverage(table, shards, self.classes)
        validate_reconciliation(record)
        document = {
            "format": RECONCILIATION_FORMAT,
            "plan_sha256": plan_digest(self.plan),
            "reconciliation": record,
            "shards": table,
        }
        _atomic_json(self.directory / RECONCILIATION_RECORD, document)
        self.staging.close()
        return document



class Builder:
    """Turn a reconciled staging tree into an Alexandria release, offline.

    Every count, every epoch and every declared interval is derived from the
    preserved bytes rather than asserted, so `ingest` can refuse an inflated
    coverage figure against the component it describes and `check` can
    re-derive the epoch table and re-hash the implementation code from the
    release alone. Nothing is taken from an operator: the epochs come from the
    `epoch-evidence` journal the collector committed.
    """

    def __init__(self, plan, staging_root, registry, *, created_at) -> None:
        validate_plan(plan)
        self.plan = plan
        self.classes = declared_classes(plan)
        # One release component per plan-derived journal component, named
        # from the plan and nothing else.
        self.components = journal_components(plan, self.classes)
        self.staging = Staging(staging_root, plan)
        self.root = self.staging.root
        self.venue = plan_venue(plan)
        self.venue.validate_registry(registry)
        self.registry = registry
        # The plan's subject form and the venue's epoch model have to agree
        # before any staged byte is read; see `opening_phase`.
        opening_phase(plan, [], registry=registry)
        if not isinstance(created_at, str) or TIMESTAMP_RE.fullmatch(created_at) is None:
            raise AlexandriaError("the release creation time is not a UTC timestamp")
        self.created_at = created_at
        self.logs = []
        self.first_code = None

    def _reconciliation(self) -> dict:
        path = self.root / RECONCILIATION_DIRECTORY / RECONCILIATION_RECORD
        if not path.is_file() or path.is_symlink():
            raise AlexandriaError(
                "the interval has not been reconciled, so there is no release to build"
            )
        document = load_bytes(
            read_regular(path, "reconciliation record", MAX_CONTROL_BYTES), "reconciliation record"
        )
        if not isinstance(document, dict) or set(document) != {
            "format", "plan_sha256", "reconciliation", "shards",
        }:
            raise AlexandriaError("the reconciliation record has an unknown shape")
        if document["plan_sha256"] != plan_digest(self.plan):
            raise AlexandriaError("the reconciliation record belongs to a different plan")
        validate_reconciliation(document["reconciliation"])
        validate_shard_coverage(document["shards"], self.plan["shards"], self.classes)
        return document

    def _errors(self) -> list:
        path = self.root / RECEIPTS_DIRECTORY / ERROR_RECEIPTS
        if not path.is_file():
            return []
        if path.is_symlink():
            raise AlexandriaError("the error receipt file must not be a symlink")
        return [
            load_bytes(line + b"\n", "error receipt", max_bytes=MAX_CONTROL_BYTES)
            for line in read_regular(path, "error receipts", MAX_CONTROL_BYTES).splitlines()
            if line
        ]

    def _journal(self, name: str, component=None) -> dict:
        """One journal document: a whole class, or one plan-derived component of it.

        A component reads its own staging file alone, so a split journal is
        released without ever being joined into one oversized document.
        """
        records = list(self.staging.entries(name, component))
        for record in records:
            if set(record) != {"class", "request", "response", "shard"}:
                raise AlexandriaError(f"a staged {name} record has an unknown shape")
        return {
            "class": name,
            "format": JOURNAL_FORMAT,
            "interval": dict(self.plan["interval"]),
            "records": records,
        }

    def _opening(self, state: dict):
        """The opening phase the journal committed, or a refusal naming what is missing."""
        if state["offsets"].get(OPENING_CLASS, 0) == 0:
            raise AlexandriaError(
                "the staging tree has no committed epoch-evidence journal; the opening "
                "phase has not been collected, so there is no release to build"
            )
        return replay_opening(self.plan, self.staging, self.classes, self.registry)[0]

    def _epochs(self, phase, end_hash: str):
        """The epoch table, derived from the opening reads; see `epochs_from_opening`."""
        return epochs_from_opening(self.plan, phase, end_hash)

    def _code_component(self, epochs, phase) -> dict:
        """Each implementation's runtime bytes as the collector read them, keyed by address."""
        records = []
        # A subject-keyed table is read through its entries, never iterated
        # as though its keys were epochs.
        entries = (
            validate_epoch_subjects(epochs, _plan_subjects(self.plan))
            if isinstance(epochs, dict) else epochs
        )
        for address in sorted({epoch["implementation"] for epoch in entries}):
            code = phase.codes.get(address)
            if code is None:
                raise AlexandriaError(
                    f"implementation {address} opens an epoch but its runtime code was not read"
                )
            records.append({"address": address, "code": code})
        return {"format": CODE_FORMAT, "records": records}

    def build(self, output: Path) -> str:
        state = self.staging.committed()
        if state["next_shard"] != len(self.plan["shards"]):
            raise AlexandriaError(
                "the interval is not completely collected, so there is no release to build"
            )
        require_committed_journals(self.staging, state, "build")
        phase = self._opening(state)
        reconciliation = self._reconciliation()
        shards = _receipt_shards(reconciliation["shards"])
        end_hash = shards[-1]["end_hash"]
        start_hash = phase.hashes[phase.start]
        epochs = self._epochs(phase, end_hash)
        self._validate_epoch_table(epochs, phase.start, phase.end)
        code = self._code_component(epochs, phase)
        code_bytes = canonical_bytes(code)
        documents = {
            "epoch-table": self._epoch_receipt(phase, epochs, code_bytes, reconciliation, shards),
            "error-receipts": {"format": "alexandria-interval-errors/v1", "records": self._errors()},
            CODE_COMPONENT: code,
            "interval-plan": self.plan,
            "reconciliation": reconciliation,
            "registry": self.registry,
        }
        for component, part in self.components.items():
            documents[component] = self._journal(part["class"], part["index"])
        boundaries = {"end_hash": end_hash, "start_hash": start_hash}
        # The preserved logs, and how each unrecorded subject was opened, for
        # the venue's own gap contribution.
        self.logs = phase.logs
        self.first_code = phase.first_code_rows() if "subjects" in self.plan else None

        parent = output.absolute().parent
        parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.plan-", dir=parent))
        try:
            components = []
            captures = []
            for component, document in sorted(documents.items()):
                relative = f"{component}.json"
                (staging / relative).write_bytes(canonical_bytes(document))
                part = self.components.get(component)
                components.append({
                    "access": "public",
                    "media_type": "application/json",
                    "name": component,
                    "path": relative,
                    "redistribution": "permitted",
                    "role": _role(component if part is None else part["class"]),
                })
                captures.append(self._capture(component, document, reconciliation, boundaries))
            plan_document = {
                "captures": captures,
                "components": components,
                "format": "alexandria-capture-plan/v1",
                "release": {"created_at": self.created_at, "name": RELEASE_NAME},
            }
            (staging / "capture-plan.json").write_bytes(canonical_bytes(plan_document))
            return ingest(staging / "capture-plan.json", output)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def _validate_epoch_table(self, epochs, start, end):
        validate_epochs(epochs, start, end)

    def _epoch_receipt(self, phase, epochs, code_bytes, reconciliation, shards):
        subjects = _plan_subjects(self.plan)
        attributions = attribute_logs(
            phase.logs, subjects, self.plan["interval"], epochs,
            upgrade_topic=phase.upgrade_topic,
        )
        # Every retained row passes the runtime validator before it is
        # written, under the plan's own subject form.
        validate_attributions(attributions, subjects=subjects)
        # A subject-keyed table is written as one list of subject rows, so its
        # coverage is one collection however many subjects the plan declares.
        receipt = {"epochs": subject_epoch_rows(epochs) if isinstance(epochs, dict) else epochs,
                   "format": SUBJECT_RECEIPT_FORMAT if "subjects" in self.plan else RECEIPT_FORMAT,
                   "log_attributions": attributions,
                   "implementation_code": {"component": CODE_COMPONENT,
                                           "sha256": hashlib.sha256(code_bytes).hexdigest()},
                   "reconciliation": reconciliation["reconciliation"], "shards": shards}
        if "subjects" in self.plan:
            # How each unrecorded subject was opened; `check` re-derives the rows.
            receipt["first_code"] = phase.first_code_rows()
            validate_first_code(
                receipt["first_code"], epochs, int(self.plan["interval"]["start"])
            )
        return receipt

    def _capture(self, component: str, document, reconciliation, boundaries) -> dict:
        interval = self.plan["interval"]
        # A journal component is named `<class>` or `<class>.<k>`; its class
        # decides its role, its scope and its gaps, and its own name is the
        # capture it is filed under.
        part = self.components.get(component)
        journal = component if part is None else part["class"]
        evidence = journal in JOURNAL_CLASSES
        collections = []
        record_count = 0
        if evidence or component in ("error-receipts", CODE_COMPONENT):
            record_count = len(document["records"])
            collections = [{
                "name": "implementations" if component == CODE_COMPONENT else component,
                "record_count": record_count,
                "selector": "/records",
            }]
        elif component == "epoch-table":
            # One list under either receipt: a single proxy's epochs, or one
            # row per in-interval subject. The count is the length of `/epochs`
            # and never grows the collection list with the subject set.
            record_count = len(document["epochs"])
            collections = [{
                "name": "epochs",
                "record_count": record_count,
                "selector": "/epochs",
            }]
        elif component == "registry":
            record_count = len(document["entries"])
            collections = [{
                "name": "registry-entries",
                "record_count": record_count,
                "selector": "/entries",
            }]
        else:
            # The plan and the reconciliation record are single documents, but
            # Alexandria will not call a coverage complete without a counted
            # collection, and each of them does carry one: its shard table.
            record_count = len(document["shards"])
            collections = [{
                "name": f"{component}-shards",
                "record_count": record_count,
                "selector": "/shards",
            }]
        gaps = _gaps(
            journal, self.plan, self.registry, reconciliation, self.venue, part,
            logs=self.logs, first_code=self.first_code,
        )
        unsupported = _unsupported(journal)
        scope_interval = {
            "end": interval["end"],
            "kind": "block-range",
            "start": interval["start"],
        }
        if evidence:
            # Both boundary hashes, from the collector's own reads: the start
            # from the first-block header the opening phase preserved, the end
            # from the last shard's boundary read. Neither is copied from the
            # epoch table or supplied by an operator, so the scope's finality
            # is the policy the plan bound rather than a provider's word.
            scope_interval["end_hash"] = boundaries["end_hash"]
            scope_interval["start_hash"] = boundaries["start_hash"]
        return {
            "chain": self.plan["chain"],
            "component": component,
            "coverage": {
                "collections": collections,
                "gaps": gaps,
                "record_count": record_count,
                "status": _status(gaps, unsupported, reconciliation),
                "unsupported_collections": unsupported,
            },
            "evidence_class": "recorded-rpc" if evidence else "header-bound",
            "id": component,
            "source": {
                "kind": "json-rpc" if evidence else "local-fixture",
                "locator_class": "provider-endpoint" if evidence else "local-fixture",
                "reference": self.plan["provider"]["class"] if evidence
                else f"derived offline from the collected interval, {component}",
            },
            "scope": {
                "deployment": self.plan["deployment"],
                "finality": scope_finality(self.plan) if evidence else "provider-reported",
                "interval": scope_interval,
                "kind": "full-dataset",
            },
            "venue": self.plan["venue"],
        }


def scope_finality(plan) -> str:
    """The finality class an evidence scope carries: the plan's policy where Alexandria names it.

    `finalized` and `safe` are Alexandria finality classes and the collector
    bound the boundary under them, so the scope says so. A `confirmations`
    policy is a depth this collector chose, not a class the chain reports, so
    its scope stays `provider-reported` while still carrying both hashes.
    """
    policy = plan["finality"]["policy"]
    return policy if policy in FINALITY_TAGS else "provider-reported"


def _role(component: str) -> str:
    return {
        "boundary-blocks": "json-rpc-response",
        OPENING_CLASS: "json-rpc-response",
        "epoch-table": "interval-receipt",
        "error-receipts": "error-receipt",
        CODE_COMPONENT: "implementation-code",
        "interval-plan": "capture-contract",
        "logs": "json-rpc-response",
        "reconciliation": "provider-reconciliation",
        "registry": "deployment-registry",
        "traces": "json-rpc-response",
    }[component]


def _status(gaps, unsupported, reconciliation) -> str:
    """`complete` only when nothing is missing, which Alexandria also enforces.

    A coverage status of `complete` may name no gap and no unsupported
    collection, so the status is derived from what the gaps say rather than
    asserted beside them. Every component of this release names at least one
    gap today, so every status is `partial`: that is the shape of a first
    collector, not a defect to code around.
    """
    if gaps or unsupported:
        return "partial"
    if {shard["status"] for shard in reconciliation["shards"]} != {"complete"}:
        return "partial"
    if reconciliation["reconciliation"]["status"] != "agreed":
        return "partial"
    return "complete"


def _unsupported(component: str) -> list:
    if component == "traces":
        return ["internal-call-replay"]
    if component in ("boundary-blocks", "logs"):
        return ["credit-event-mapping"]
    return []


def _gaps(
    component: str, plan, registry, reconciliation, venue, part=None, *, logs=(), first_code=None,
) -> list:
    gaps = []
    if component == "registry":
        return venue.gaps(registry, plan)
    for shard in reconciliation["shards"]:
        if shard["status"] != "complete":
            gaps.append(
                f"shard {shard['index']}, blocks {shard['start']} to {shard['end']}, is "
                f"{shard['status']} after provider reconciliation"
            )
    if reconciliation["reconciliation"]["status"] == "unreconciled":
        gaps.append("the interval was not reconciled against a second provider")
    if component in JOURNAL_CLASSES:
        # Every class the plan omitted is a gap on every evidence scope, with
        # what its absence leaves unpreserved, so a release that never asked
        # for logs says so where a reader of the logs scope would look.
        declared = set(plan["evidence_classes"])
        for name in EVIDENCE_CLASSES:
            if name not in declared:
                gaps.append(
                    f"the {name} evidence class was not declared by the plan, so it was "
                    f"never requested or preserved; {OMISSION_REASONS[name]}"
                )
        if part is not None and part["index"] is not None:
            gaps.append(component_gap(plan, part))
        # What the venue itself says these bytes do not establish: whether
        # they were collected at all, and what its registry could not supply.
        gaps.extend(venue.evidence_gaps(plan, registry, logs, first_code))
        gaps.append(
            "no credit event, position observation or repayment conclusion is derived here"
        )
    return gaps


def _receipt_shards(shards) -> list:
    return [
        {
            "end": shard["end"],
            "end_hash": shard["end_hash"],
            "index": shard["index"],
            "record_counts": shard["record_counts"],
            "start": shard["start"],
            "status": shard["status"],
        }
        for shard in shards
    ]


def _transaction_order(header) -> list:
    transactions = header.get("transactions") if isinstance(header, dict) else None
    if transactions is None:
        return []
    if not isinstance(transactions, list):
        raise AlexandriaError("a block header's transaction list is not a list")
    order = []
    for item in transactions:
        if isinstance(item, str):
            order.append(item.lower())
        elif isinstance(item, dict) and isinstance(item.get("hash"), str):
            order.append(item["hash"].lower())
        else:
            raise AlexandriaError("a block header transaction carries no hash")
    return order


def _identity_comparison(first, second):
    """How many identities both providers hold, and every one only one of them does."""
    remaining = list(second)
    agreed = 0
    disagreements = []
    for identity in first:
        if identity in remaining:
            remaining.remove(identity)
            agreed += 1
        else:
            disagreements.append(identity)
    disagreements.extend(remaining)
    return agreed, disagreements


def _atomic_json(path: Path, value) -> None:
    data = canonical_bytes(value)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)



def check_interval(release_root: Path) -> dict:
    """Verify one interval release offline: Alexandria's checks, then the interval's.

    Reaches no network and changes no file. The Alexandria verifier settles
    canonical bytes, digests, paths and declared coverage counts; what follows
    settles the things only an interval release can be wrong about, and
    believes nothing the release merely declares: the epoch table is
    re-derived from the preserved opening reads, each implementation's digest
    is re-hashed from the `implementation-code` component, and every evidence
    scope's start hash is compared with the collector's own first-block read.
    """
    release_root = Path(release_root).absolute()
    release_id = verify(release_root)
    manifest = load_bytes(
        read_confined_file(release_root, "manifest.json", "manifest", max_bytes=MAX_CONTROL_BYTES),
        "manifest",
    )
    # The manifest already carries every component's byte count; comparing it
    # with the ceiling here, before any component is read, makes the budget a
    # refusal by name rather than a figure left to a reader.
    for item in manifest["components"]:
        if item["bytes"] > MAX_RAW_COMPONENT_BYTES:
            raise AlexandriaError(
                f"component {item['name']} holds {item['bytes']} bytes, above the "
                f"{MAX_RAW_COMPONENT_BYTES}-byte component ceiling"
            )
    plan = load_bytes(
        _component(release_root, manifest, "interval-plan"), "component interval-plan",
        max_bytes=MAX_RAW_COMPONENT_BYTES,
    )
    validate_plan(plan)
    venue = plan_venue(plan)
    classes = declared_classes(plan)
    # The journal components, and the shard range each one holds, come from
    # the plan and nothing else; the manifest's own list is compared with them,
    # never believed.
    journal_parts = journal_components(plan, classes)
    journal_names = tuple(journal_parts)
    expected_components = set(FIXED_COMPONENTS) | set(journal_names)
    present = [item["name"] for item in manifest["components"]]
    for name in sorted(set(present) - expected_components):
        raise AlexandriaError(
            f"the release carries a {name} component the plan does not declare"
        )
    for name in sorted(expected_components - set(present)):
        raise AlexandriaError(f"the release lacks its {name} component")
    documents = {}
    component_bytes = {}
    for name in sorted(expected_components):
        component_bytes[name] = _component(release_root, manifest, name)
        documents[name] = load_bytes(
            component_bytes[name], f"component {name}", max_bytes=MAX_RAW_COMPONENT_BYTES,
        )

    interval = plan["interval"]
    start = int(interval["start"])
    end = int(interval["end"])

    receipt = documents["epoch-table"]
    legacy = isinstance(receipt, dict) and receipt.get("format") == LEGACY_RECEIPT_FORMAT
    required = {"epochs", "format", "implementation_code", "reconciliation", "shards"}
    if not legacy:
        required.add("log_attributions")
    # Keyed on the receipt's own format, so a receipt under the other kind of
    # plan still reaches the refusal below that names the mismatch.
    if isinstance(receipt, dict) and receipt.get("format") == SUBJECT_RECEIPT_FORMAT:
        required.add("first_code")
    if not isinstance(receipt, dict) or set(receipt) != required or receipt["format"] not in (
        LEGACY_RECEIPT_FORMAT, RECEIPT_FORMAT, SUBJECT_RECEIPT_FORMAT,
    ):
        raise AlexandriaError("the interval receipt has an unknown shape")
    # A subject-set plan's receipt is the subject-row format and a
    # single-proxy plan's is not; either one under the other plan is a receipt
    # some other plan's build wrote.
    if ("subjects" in plan) != (receipt["format"] == SUBJECT_RECEIPT_FORMAT):
        raise AlexandriaError(
            "the interval receipt format does not match the plan's subject form"
        )
    # A subject-set receipt writes its table as one list of subject rows; the
    # table those rows declare is what every check below reads.
    receipt_epochs = (
        subject_epoch_table(receipt["epochs"]) if "subjects" in plan else receipt["epochs"]
    )
    (validate_block_epochs if legacy else validate_epochs)(receipt_epochs, start, end)
    subjects = _plan_subjects(plan)
    epoch_entries = validate_epoch_subjects(receipt_epochs, subjects)
    if "subjects" in plan:
        validate_first_code(receipt["first_code"], receipt_epochs, start)
    if not legacy:
        validate_attributions(receipt["log_attributions"], subjects=subjects)
    for epoch in epoch_entries:
        owned = epoch["proxy"] == subjects if isinstance(subjects, str) else epoch["proxy"] in subjects
        if not owned or epoch["chain"] != plan["chain"]:
            raise AlexandriaError("an epoch does not belong to the plan's market")

    shards = receipt["shards"]
    validate_shard_coverage(shards, plan["shards"], classes)
    expected = start
    for shard in shards:
        if shard["start"] != expected:
            raise AlexandriaError(
                f"the shard table leaves block {expected} uncovered"
                if shard["start"] > expected
                else f"the shard table overlaps at block {shard['start']}"
            )
        expected = shard["end"] + 1
    if expected != end + 1:
        raise AlexandriaError(f"the shard table leaves block {expected} uncovered")

    # An epoch boundary and a shard boundary can name the same block. Where they
    # do, they came from different reads and have to agree: the epoch hash from
    # the opening phase's header reads, the shard hash from what the collector
    # saw at that block while walking the shards.
    shard_hashes = {shard["end"]: shard["end_hash"] for shard in shards}
    for epoch in epoch_entries:
        boundary = int(epoch["end_block"])
        if boundary in shard_hashes and epoch["end_hash"] != shard_hashes[boundary]:
            raise AlexandriaError(
                f"the epoch ending at block {boundary} and the shard ending there "
                "name different block hashes"
            )

    finality = plan["finality"]
    if finality["policy"] not in FINALITY_POLICIES:
        raise AlexandriaError("the release's finality policy is not recognised")
    if HASH_RE.fullmatch(finality["block_hash"]) is None:
        raise AlexandriaError("the release's finality boundary carries no block hash")
    if int(finality["block_number"]) < end:
        raise AlexandriaError("the release's interval ends above its finality boundary")

    # The reconciliation component is the last record shape this check reads,
    # and it was the only one read without a shape check: its fields were
    # indexed straight, and `validate_reconciliation` tolerates a null record
    # for a run that has not compared providers yet. So an absent field raised
    # a KeyError, a null record raised a TypeError where the status is read at
    # the return, and a wrong format was accepted. The shape is settled here,
    # once, on the same terms as the epoch table and the journals.
    reconciliation = documents["reconciliation"]
    if (
        not isinstance(reconciliation, dict)
        or set(reconciliation) != {"format", "plan_sha256", "reconciliation", "shards"}
        or reconciliation["format"] != RECONCILIATION_FORMAT
    ):
        raise AlexandriaError("the reconciliation component has an unknown shape")
    if reconciliation["reconciliation"] is None:
        raise AlexandriaError(
            "the reconciliation component records no reconciliation, so the release "
            "carries no second-provider comparison"
        )
    if reconciliation["plan_sha256"] != plan_digest(plan):
        raise AlexandriaError("the reconciliation record belongs to a different plan")
    validate_reconciliation(reconciliation["reconciliation"])
    validate_shard_coverage(reconciliation["shards"], plan["shards"], classes)
    # The two shard tables are one table written twice. Only their statuses
    # were compared, so the reconciliation copy could carry another boundary
    # hash or another record count than the receipt's -- neither of which any
    # other check reads -- and a reader of the reconciliation alone would
    # believe it. They must agree entry for entry.
    if reconciliation["shards"] != shards:
        raise AlexandriaError("the reconciliation and the receipt disagree about a shard")
    # The receipt carries its own copy of the comparison, which the builder
    # takes from this record. Only the record's copy was checked, so a receipt
    # could declare `agreed` over any number of comparisons while the record
    # said `unreconciled`, and a reader of the receipt alone would believe it.
    if receipt["reconciliation"] != reconciliation["reconciliation"]:
        raise AlexandriaError(
            "the receipt and the reconciliation record declare different comparisons"
        )

    disputed = {
        shard["index"] for shard in shards if shard["status"] != "complete"
    }
    captures = {capture["id"]: capture for capture in manifest["captures"]}
    # Every component's coverage and scope are read under the component's own
    # name below and in `_check_scopes`. The builder gives each capture the
    # name of the component it preserves; a release whose captures name
    # something else raised a KeyError there instead of refusing.
    for name in sorted(expected_components - set(captures)):
        raise AlexandriaError(f"the release carries no capture for its {name} component")
    derived = {shard["index"]: {} for shard in plan["shards"]}
    boundary_headers = {}
    # A subject-set plan's `traces` request is derived from its own shard's
    # `logs` result (see `subject_transaction_hashes`), not from a static
    # per-shard filter `shard_requests` can precompute; this is filled in as
    # each shard's `logs` record is read below, which always precedes its
    # `traces` record because `journal_components` orders components by
    # declared class, and `declared_classes` refuses a plan that declares
    # `traces` under subjects without also declaring `logs`.
    logs_by_shard = {}
    # The read each shard and class makes, derived from the plan exactly as the
    # collector derived it. A shard journal record was filed under a shard
    # index that nothing held against the request the record preserves, so a
    # `logs` read over two unrelated blocks, or a boundary record that asked
    # for something other than the shard's last block, stood for the shard's
    # coverage. The opening journal has been replayed against its own derived
    # requests since it was written; the shard journals are held to the same
    # rule here.
    planned_requests = {
        (shard["index"], name): request_bytes(
            request_identifier(shard["index"], name), method, params
        )
        for shard in plan["shards"]
        for name, method, params in shard_requests(plan, shard)
    }
    shard_bounds = {shard["index"]: (shard["start"], shard["end"]) for shard in plan["shards"]}
    # The address every shard read filters on: `eth_getLogs` by the emitting
    # contract, `trace_filter` by the recipient. An entry naming another
    # address is one its own preserved request could not have returned.
    proxy = _plan_subjects(plan)
    reads = {}
    virtual = len(plan["shards"])
    for name, part in journal_parts.items():
        journal = documents[name]
        # `name` is the component, `kind` the class whose records it holds;
        # they differ only under a split, where the plan derives `<class>.<k>`.
        kind = part["class"]
        if (
            not isinstance(journal, dict)
            or set(journal) != {"class", "format", "interval", "records"}
            or journal["format"] != JOURNAL_FORMAT
        ):
            raise AlexandriaError(f"the {name} component is not an interval journal")
        if journal["class"] != kind:
            raise AlexandriaError(
                f"the {name} component carries a {str(journal['class'])[:64]} journal, "
                "so the plan and the journals disagree about the declared classes"
            )
        if journal["interval"] != interval:
            raise AlexandriaError(f"the {name} journal declares another interval")
        if not isinstance(journal["records"], list):
            raise AlexandriaError(f"the {name} journal carries no record list")
        for record in journal["records"]:
            if not isinstance(record, dict) or set(record) != {"class", "request", "response", "shard"}:
                raise AlexandriaError(f"a {name} journal record has an unknown shape")
            # The request and the response are read as text further down, by
            # `_replay_release_opening` and by the count derivation. A release
            # is somebody else's bytes, so the type is checked here rather
            # than discovered as an attribute error on a number.
            for field in ("request", "response"):
                if not isinstance(record[field], str):
                    raise AlexandriaError(
                        f"a {name} journal record carries a {field} that is not text"
                    )
            # The shard index becomes a set element on the next line and a
            # dictionary key in the count derivation, so an unhashable value
            # raises a TypeError there and a boolean silently shares shard
            # one's key. Both are refused by name here instead.
            if not isinstance(record["shard"], int) or isinstance(record["shard"], bool):
                raise AlexandriaError(
                    f"a {name} journal record carries a shard index that is not a whole number"
                )
            if record["class"] != kind:
                raise AlexandriaError(
                    f"the {name} journal holds a {str(record['class'])[:64]} record, so the "
                    "plan and the journals disagree about the declared classes"
                )
        staged = {record["shard"] for record in journal["records"]}
        if kind == OPENING_CLASS:
            if staged and staged != {virtual}:
                raise AlexandriaError(
                    "the epoch-evidence journal holds a record outside the virtual shard index"
                )
        else:
            # The component holds exactly the shards the plan derives for it:
            # a shard from another range is an overlap or a repeated range, a
            # missing one is a gap, and either leaves a journal that does not
            # reassemble from its components.
            expected_shards = set(range(part["first"], part["last"] + 1))
            for index in sorted(staged - expected_shards):
                raise AlexandriaError(
                    f"the {name} component holds shard {index}, outside the shards "
                    f"{part['first']} to {part['last']} the plan derives for it"
                )
            for index in sorted(expected_shards - staged):
                raise AlexandriaError(
                    f"the {name} component does not cover shard {index} of the shards "
                    f"{part['first']} to {part['last']} the plan derives for it"
                )
            for record in journal["records"]:
                if kind == "traces" and "subjects" in plan:
                    # Not a static per-shard filter: the request this plan
                    # actually made is `trace_transaction` once per distinct
                    # transaction hash its own `logs` result touched.
                    expected_request = request_bytes(
                        request_identifier(record["shard"], "traces"), "trace_transaction",
                        subject_transaction_hashes(logs_by_shard.get(record["shard"], [])),
                    )
                else:
                    expected_request = planned_requests[(record["shard"], kind)]
                if record["request"].encode() != expected_request:
                    raise AlexandriaError(
                        f"the {name} record filed under shard {record['shard']} is not the "
                        "read the plan names there"
                    )
                # The envelope the collector accepted for this read, held to
                # the rules `_ask` applied to the same bytes: the answer's id,
                # its version, an absent error, a present result, no
                # truncation marker and a page below the provider's limit.
                # Those rules live in `preserved_result` now, which the
                # opening journal's three readers share, so the release's
                # shard evidence and its opening evidence are read under one
                # rule rather than two that drift apart.
                result = preserved_result(
                    record["response"],
                    request_identifier(record["shard"], kind),
                    plan["provider"]["page_limit"],
                    f"{name} response for shard {record['shard']}",
                    f"{name} result for shard {record['shard']}",
                    f"{name} response for shard {record['shard']}",
                )
                # A `logs` or `trace_filter` answer is a list of entries, and
                # the entries are read below. A result of any other shape was
                # counted as one read and never looked at.
                if kind in ENTRY_BLOCK_CLASSES and not isinstance(result, list):
                    raise AlexandriaError(
                        f"the {name} result for shard {record['shard']} is not a list of entries"
                    )
                if kind == "logs":
                    logs_by_shard[record["shard"]] = result
                reads[(record["shard"], kind)] = reads.get((record["shard"], kind), 0) + 1
                # Two records of one class for one shard are two reads, so
                # their sizes add. Assigning here declared the last record's
                # size alone, so a journal could carry a shard's evidence
                # twice while the receipt's count named one read of it.
                derived[record["shard"]][kind] = derived[record["shard"]].get(kind, 0) + (
                    len(result) if isinstance(result, list) else 1
                )
                if kind == BOUNDARY_CLASS:
                    boundary_headers[record["shard"]] = result
                if kind in ENTRY_BLOCK_CLASSES:
                    # An entry the read could not have returned: the record's
                    # own request bounds the blocks its result can carry, and
                    # an entry outside them contradicts the read it sits in.
                    # `logs` names its block as a hexadecimal quantity and
                    # `trace_filter` as a decimal number, so both are read.
                    low, high = shard_bounds[record["shard"]]
                    for entry in result:
                        label = f"a {name} entry for shard {record['shard']}"
                        block = _entry_block(
                            entry.get("blockNumber") if isinstance(entry, dict) else None,
                            f"{label} block number",
                        )
                        if not low <= block <= high:
                            raise AlexandriaError(
                                f"{label} names block {block}, outside the shard's blocks "
                                f"{low} to {high}"
                            )
                        # The other half of the record's own filter: the read
                        # names one address, so an entry naming another is one
                        # the read could not have returned. The block was
                        # bound and the address was not.
                        address = _entry_address(entry, kind, label)
                        if isinstance(proxy, str):
                            if address != proxy:
                                raise AlexandriaError(
                                    f"{label} names address {address}, not the {proxy} its "
                                    "read asked for"
                                )
                        elif address not in proxy:
                            raise AlexandriaError(
                                f"{label} names address {address}, which is not one of the "
                                "subjects its read asked for"
                            )
        gaps = captures[name]["coverage"]["gaps"]
        for index in sorted(disputed):
            if not any(f"shard {index}," in gap for gap in gaps):
                raise AlexandriaError(
                    f"shard {index} is not complete but the {name} coverage does not name it"
                )
        if disputed and captures[name]["coverage"]["status"] == "complete":
            raise AlexandriaError(
                f"the {name} coverage reports complete while a shard is not"
            )
        for omitted in EVIDENCE_CLASSES:
            if omitted not in classes and not any(
                f"the {omitted} evidence class was not declared" in gap for gap in gaps
            ):
                raise AlexandriaError(
                    f"the plan omits {omitted} but the {name} coverage does not name the gap"
                )
        # A split component's coverage names the shards it holds, in the words
        # the plan derives, so a reader of one component is not left to take
        # it for the whole journal its scope binds.
        if part["index"] is not None and component_gap(plan, part) not in gaps:
            raise AlexandriaError(
                f"the {name} coverage does not name the shards {part['first']} to "
                f"{part['last']} the plan derives for it"
            )

    for shard in shards:
        if shard["record_counts"] != derived[shard["index"]]:
            raise AlexandriaError(
                f"shard {shard['index']} declares record counts the journals do not carry"
            )

    # One read per shard and class is what the collector writes: it asks each
    # request once and a resumed run truncates its journals back to the
    # checkpoint before it continues. A second record was refused for the
    # boundary class alone, where the later copy supplanted the read the
    # shard's hash is compared with; for every other class a second record
    # stood beside the genuine one and the receipt declared their sum as reads
    # the collector never made. The rule is one rule, and it is applied after
    # the counts so a journal carrying evidence its receipt does not count is
    # still refused under that name.
    for index, class_name in sorted(key for key, count in reads.items() if count > 1):
        raise AlexandriaError(
            f"the {class_name} journal holds shard {index} twice, so two reads claim "
            f"that shard's {class_name} evidence"
        )

    # Every shard's boundary hash, re-read from the release's own
    # `boundary-blocks` journal. The collector took each one from an
    # `eth_getBlockByNumber` at that shard's last block and the journal
    # preserves that read, so the declared hash is compared with the bytes it
    # describes rather than believed. Without this the interval's own end
    # hash was pinned only to the epoch table, which the derivation takes
    # from the same declared value, so it was pinned to itself.
    for shard in shards:
        header = boundary_headers.get(shard["index"])
        if not isinstance(header, dict) or not isinstance(header.get("hash"), str):
            raise AlexandriaError(
                f"the boundary-blocks record for shard {shard['index']} preserves no block header"
            )
        label = f"the boundary-blocks header for shard {shard['index']}"
        if _hex(header.get("number"), f"{label} block number") != shard["end"]:
            raise AlexandriaError(
                f"{label} preserves block {header['number']}, not the shard's last "
                f"block {shard['end']}"
            )
        if header["hash"] != shard["end_hash"]:
            raise AlexandriaError(
                f"shard {shard['index']} declares boundary hash {shard['end_hash']}, which "
                f"its preserved boundary read does not carry; that read carries "
                f"{header['hash']}"
            )

    # The opening reads, replayed from the release's own journal: they name
    # the first block's hash and derive the epoch table the receipt has to
    # match, so nothing the receipt declares about an epoch is believed on
    # its own word.
    phase = _replay_release_opening(plan, documents, classes, journal_parts, legacy=legacy)
    first_hash = phase.hashes[start]

    # The implementation code, re-hashed from the component's bytes: the
    # receipt names the component's digest, and each epoch names the digest of
    # its implementation's runtime bytes; both are recomputed here, before the
    # table as a whole is compared, so a digest the bytes do not carry is
    # refused under its own name.
    implementations = _recheck_implementation_code(
        receipt, epoch_entries, documents[CODE_COMPONENT], component_bytes[CODE_COMPONENT],
    )
    derived_epochs = epochs_from_opening(plan, phase, shards[-1]["end_hash"], legacy=legacy)
    if derived_epochs != receipt_epochs:
        raise AlexandriaError(
            "the epoch table does not match the epochs the preserved opening reads derive"
        )

    if not legacy and receipt["log_attributions"] != attribute_logs(
        phase.logs, _plan_subjects(plan), interval, derived_epochs,
        upgrade_topic=phase.upgrade_topic,
    ):
        raise AlexandriaError("log attributions do not match ownership derived from preserved logs")

    # The gaps the venue owes every evidence scope, re-derived from the
    # release's own plan, registry and preserved logs: a release whose
    # coverage dropped one -- the constructed-staging label above all -- is
    # refused here rather than read as preserved evidence.
    # The receipt's first-code rows have to be the ones the preserved probes give.
    first_code = None
    if "subjects" in plan:
        first_code = phase.first_code_rows()
        if receipt["first_code"] != first_code:
            raise AlexandriaError(
                "the first-code rows do not match the opening reads the release preserves"
            )
    owed = venue.evidence_gaps(plan, documents["registry"], phase.logs, first_code)
    for name in journal_names:
        declared_gaps = captures[name]["coverage"]["gaps"]
        for sentence in owed:
            if sentence not in declared_gaps:
                raise AlexandriaError(
                    f"the {name} coverage does not name a gap its venue owes: {sentence[:160]}"
                )

    _check_scopes(manifest, plan, journal_names, first_hash, shards[-1]["end_hash"])

    return {
        "receipt_semantics": (
            "v1-block-only" if legacy
            else "v3-subject-positional" if receipt["format"] == SUBJECT_RECEIPT_FORMAT
            else "v2-positional"
        ),
        "epochs": len(epoch_entries),
        "implementations": implementations,
        "interval": {"end": interval["end"], "start": interval["start"]},
        "reconciliation": reconciliation["reconciliation"]["status"],
        "release_id": release_id,
        "shard_statuses": {
            status: sum(1 for shard in shards if shard["status"] == status)
            for status in sorted({shard["status"] for shard in shards})
        },
    }


def _replay_release_opening(plan, documents, classes, journal_parts, *, legacy=False):
    """Replay the release's `epoch-evidence` records against its plan, offline.

    The staged logs are read from every `logs` component in shard order, so a
    split journal reaches the opening phase exactly as its unsplit twin would.
    """
    logs = []
    if "logs" in classes:
        for name, part in journal_parts.items():
            if part["class"] != "logs":
                continue
            for record in documents[name]["records"]:
                envelope = load_bytes(
                    record["response"].encode(), "logs response", max_bytes=MAX_RAW_COMPONENT_BYTES,
                )
                result = envelope.get("result") if isinstance(envelope, dict) else None
                if isinstance(result, list):
                    logs.extend(result)
    # A venue that owns its opening reads derives them from the release's own
    # registry component, which it validates against its pinned digest first.
    phase = opening_phase(plan, logs, registry=documents["registry"], legacy=legacy)
    entries = documents[OPENING_CLASS]["records"]
    position = 0
    for read in phase.reads():
        if position >= len(entries):
            raise AlexandriaError(
                "the epoch-evidence journal stops short of the opening reads the plan names"
            )
        entry = entries[position]
        if entry["request"].encode() != opening_request(plan, position, read):
            raise AlexandriaError(
                f"epoch-evidence record {position} is not the opening read the plan names there"
            )
        phase.accept(
            read, opening_result(plan, position, entry["response"], f"opening read {position}")
        )
        position += 1
    if len(entries) > position:
        raise AlexandriaError(
            "the epoch-evidence journal holds more records than the opening reads the plan names"
        )
    return phase


def _recheck_implementation_code(receipt, epoch_entries, component, data: bytes) -> dict:
    """Re-hash the component and every implementation's bytes; refuse by name what disagrees."""
    named = receipt["implementation_code"]
    if not isinstance(named, dict) or set(named) != {"component", "sha256"}:
        raise AlexandriaError("the epoch table names its implementation-code component in an unknown shape")
    if named["component"] != CODE_COMPONENT:
        raise AlexandriaError(
            f"the epoch table names {str(named['component'])[:64]} rather than the "
            f"{CODE_COMPONENT} component"
        )
    if not isinstance(named["sha256"], str) or CODE_DIGEST_RE.fullmatch(named["sha256"]) is None:
        raise AlexandriaError("the epoch table names no SHA-256 for the implementation-code component")
    actual = hashlib.sha256(data).hexdigest()
    if actual != named["sha256"]:
        raise AlexandriaError(
            f"the epoch table names implementation-code digest {named['sha256']} but the "
            f"component's bytes hash to {actual}"
        )
    if (
        not isinstance(component, dict)
        or set(component) != {"format", "records"}
        or component["format"] != CODE_FORMAT
        or not isinstance(component["records"], list)
    ):
        raise AlexandriaError("the implementation-code component has an unknown shape")
    codes = {}
    for record in component["records"]:
        if not isinstance(record, dict) or set(record) != {"address", "code"}:
            raise AlexandriaError("an implementation-code record has an unknown shape")
        address = record["address"]
        if not isinstance(address, str) or not re.fullmatch(r"0x[0-9a-f]{40}", address):
            raise AlexandriaError("an implementation-code record is not keyed by a lowercase address")
        if address in codes:
            raise AlexandriaError(f"the implementation-code component holds {address} twice")
        codes[address] = hashlib.sha256(runtime_code(record["code"], address)).hexdigest()
    implementations = {}
    for epoch in epoch_entries:
        address = epoch["implementation"]
        if address not in codes:
            raise AlexandriaError(
                f"implementation {address}, which opens the epoch at block "
                f"{epoch['start_block']}, is missing from the implementation-code component"
            )
        if codes[address] != epoch["implementation_code_sha256"]:
            raise AlexandriaError(
                f"the epoch at block {epoch['start_block']} names implementation code digest "
                f"{epoch['implementation_code_sha256']} for {address}, which the preserved "
                f"bytes do not carry; they hash to {codes[address]}"
            )
        implementations[address] = codes[address]
    for address in sorted(set(codes) - set(implementations)):
        raise AlexandriaError(
            f"the implementation-code component carries {address}, which no epoch names"
        )
    return implementations


def _check_scopes(manifest, plan, journal_names, first_hash: str, end_hash: str) -> None:
    """Every evidence scope carries the plan's finality class and both boundary hashes.

    The start hash is compared with the hash the collector's own first-block
    read carries, never with the epoch table; the end hash with the last
    shard's boundary read. A scope with one hash and not the other, another
    finality class, a block range other than the plan's, or a hash from
    elsewhere refuses by name.
    """
    expected_finality = scope_finality(plan)
    planned = plan["interval"]
    captures = {capture["id"]: capture for capture in manifest["captures"]}
    for name in journal_names:
        scope = captures[name]["scope"]
        interval = scope["interval"]
        # The block range beside the two hashes was declared and never
        # compared, so a scope could name a range the release does not cover
        # while carrying the hashes of the range it does.
        if (
            str(interval["start"]) != str(planned["start"])
            or str(interval["end"]) != str(planned["end"])
        ):
            raise AlexandriaError(
                f"the {name} scope declares blocks {interval['start']} to {interval['end']}, "
                f"not the plan's {planned['start']} to {planned['end']}"
            )
        has_start = "start_hash" in interval
        has_end = "end_hash" in interval
        if has_start != has_end:
            raise AlexandriaError(
                f"the {name} scope carries one boundary hash and not the other"
            )
        if not has_start:
            raise AlexandriaError(f"the {name} scope carries no boundary hashes")
        if scope["finality"] != expected_finality:
            raise AlexandriaError(
                f"the {name} scope carries finality {str(scope['finality'])[:64]} while the "
                f"plan's policy binds {expected_finality}"
            )
        if interval["start_hash"] != first_hash:
            raise AlexandriaError(
                f"the {name} scope's start hash is not the hash the collector's first-block "
                "read carries"
            )
        if interval["end_hash"] != end_hash:
            raise AlexandriaError(
                f"the {name} scope's end hash is not the last shard's boundary hash"
            )
    for name, capture in captures.items():
        if name not in journal_names and (
            "start_hash" in capture["scope"]["interval"] or "end_hash" in capture["scope"]["interval"]
        ):
            raise AlexandriaError(
                f"the {name} scope carries boundary hashes although it preserves no chain read"
            )


def _component(release_root: Path, manifest, name: str) -> bytes:
    matches = [item for item in manifest["components"] if item["name"] == name]
    if len(matches) != 1:
        raise AlexandriaError(f"release component {name} is missing or duplicated")
    return read_confined_file(
        release_root, matches[0]["object_path"], f"release component {name}",
        max_bytes=MAX_RAW_COMPONENT_BYTES,
    )


def _number(value) -> int:
    return int(value)


def _trace_filter_recipient(entry):
    """The address `trace_filter`'s own `toAddress` parameter would have matched, if any.

    A call's `to`, a creation's `result.address`, a self-destruct's
    `refundAddress`, a reward's `author`, in that priority order, whichever
    the trace's own kind carries. `None` when the trace carries none of them,
    such as a `create` whose init reverted and so has no `result`; such a
    trace can never satisfy `toAddress`, on any provider, because there is no
    address on it that filter could have matched.
    """
    if not isinstance(entry, dict):
        return None
    action = entry.get("action") if isinstance(entry.get("action"), dict) else {}
    created = entry.get("result") if isinstance(entry.get("result"), dict) else {}
    return next(
        (
            candidate
            for candidate in (
                action.get("to"),
                created.get("address"),
                action.get("refundAddress"),
                action.get("author"),
            )
            if isinstance(candidate, str)
        ),
        None,
    )


def _matches_subjects(entry, subjects) -> bool:
    """Whether `trace_filter`'s own `toAddress` parameter would have kept this frame.

    `subjects` is a lowercase-address set. Used to filter one transaction's
    `trace_transaction` frames down to the ones a blanket `trace_filter` call
    would have returned -- see `Collector._targeted_traces`.
    """
    value = _trace_filter_recipient(entry)
    return isinstance(value, str) and value.lower() in subjects


def subject_transaction_hashes(logs_result) -> list:
    """The distinct transaction hashes one shard's own `logs` result touched.

    Ordered by `(blockNumber, transactionIndex)` ascending -- the order
    `trace_filter` itself would have returned their frames in -- so a
    per-transaction `trace_transaction` walk in this order, concatenated,
    reproduces `trace_filter`'s own order. Every `logs` entry the plan's own
    address filter could return already names a subject, so no further
    address check is made here; the field this reads is `transactionHash`.
    """
    if not isinstance(logs_result, list):
        raise AlexandriaError("a shard's logs result is not a list of entries")
    seen = {}
    for entry in logs_result:
        if not isinstance(entry, dict):
            raise AlexandriaError("a log entry is not an object")
        tx_hash = entry.get("transactionHash")
        if not isinstance(tx_hash, str) or HASH_RE.fullmatch(tx_hash.lower()) is None:
            raise AlexandriaError("a log entry carries no transaction hash")
        key = tx_hash.lower()
        if key in seen:
            continue
        block = _entry_block(entry.get("blockNumber"), "a log entry block number")
        tx_index = _hex(entry.get("transactionIndex"), "a log entry transaction index")
        seen[key] = (block, tx_index, tx_hash)
    return [value[2] for value in sorted(seen.values(), key=lambda value: value[:2])]


def trace_identity(record) -> str:
    """The tuple two providers' targeted trace frames are compared by, as one string.

    `(transactionHash, traceAddress, type, recipient)`, where `recipient` is
    whatever `_trace_filter_recipient` reads off the frame. A transaction's
    hash together with its trace address already names one frame uniquely, so
    unlike `log_identity` this does not require a `blockHash`: a provider
    whose trace frames carry only the fields `_ask` itself ever reads (as the
    collector's own preserved frames do) still compares. `type` and
    `recipient` fall back to an empty string rather than refusing when
    absent, for the same reason. Nothing here is normalised beyond case,
    because two providers disagreeing about the case of a hash is not a
    disagreement about the chain.
    """
    if not isinstance(record, dict):
        raise AlexandriaError("a trace record is not an object")
    tx_hash = record.get("transactionHash")
    if not isinstance(tx_hash, str) or not tx_hash:
        raise AlexandriaError("a trace record has no transactionHash")
    trace_address = record.get("traceAddress")
    if not isinstance(trace_address, list) or any(
        not isinstance(item, int) or isinstance(item, bool) for item in trace_address
    ):
        raise AlexandriaError("a trace record has no traceAddress")
    kind = record.get("type")
    recipient = _trace_filter_recipient(record)
    fields = [
        tx_hash.lower(),
        ",".join(str(item) for item in trace_address),
        kind.lower() if isinstance(kind, str) else "",
        recipient.lower() if isinstance(recipient, str) else "",
    ]
    return "|".join(fields)


def _entry_address(entry, name: str, label: str) -> str:
    """The address one journal entry names as the party its read filtered on.

    `eth_getLogs` filters on the emitting contract, which every log carries as
    `address`. `trace_filter` filters on the recipient, which a trace names in
    the field its own action carries: a call's `to`, a creation's
    `result.address`, a self-destruct's `refundAddress`, a reward's `author`.
    """
    if not isinstance(entry, dict):
        raise AlexandriaError(f"{label} is not an object")
    if name == "logs":
        value = entry.get("address")
    else:
        value = _trace_filter_recipient(entry)
    if not isinstance(value, str) or ADDRESS_RE.fullmatch(value.lower()) is None:
        raise AlexandriaError(f"{label} names no address its read could have filtered on")
    return value.lower()


def _entry_block(value, label: str) -> int:
    """One journal entry's block, as a hexadecimal quantity or a whole number."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return _hex(value, label)


def _hex(value, label: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise AlexandriaError(f"{label} is not a hexadecimal quantity")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise AlexandriaError(f"{label} is not a hexadecimal quantity") from exc


def load_control(path: Path, label: str):
    path = path.absolute()
    return load_bytes(
        read_confined_file(path.parent, path.name, label, max_bytes=MAX_CONTROL_BYTES),
        label,
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Collect a bounded Ethereum USDC Comet interval, resumably."
    )
    commands = value.add_subparsers(dest="command", metavar="{collect,reconcile,build,check}")
    collect = commands.add_parser("collect", help="collect the plan's interval from the explicit RPC endpoint")
    collect.add_argument("--plan", required=True, type=Path)
    collect.add_argument("--staging", required=True, type=Path)
    collect.add_argument(
        "--registry", type=Path,
        help="the deployment registry, for a venue that plans its opening reads from one",
    )
    collect.add_argument(
        "--concurrency", type=int, default=DEFAULT_COLLECT_CONCURRENCY,
        help=(
            f"shards fetched at once, from 1 to {MAX_COLLECT_CONCURRENCY} "
            f"(default {DEFAULT_COLLECT_CONCURRENCY}); commits still land strictly in "
            "ascending shard order"
        ),
    )
    reconcile = commands.add_parser(
        "reconcile", help="run the collected interval past a second provider"
    )
    reconcile.add_argument("--plan", required=True, type=Path)
    reconcile.add_argument("--staging", required=True, type=Path)
    reconcile.add_argument("--provider-class", required=True)
    reconcile.add_argument(
        "--registry", type=Path,
        help="the deployment registry, for a venue that plans its opening reads from one",
    )
    build = commands.add_parser("build", help="build the Alexandria release offline")
    build.add_argument("--plan", required=True, type=Path)
    build.add_argument("--staging", required=True, type=Path)
    build.add_argument("--registry", required=True, type=Path)
    build.add_argument("--created-at", required=True)
    build.add_argument("--output", required=True, type=Path)
    check = commands.add_parser("check", help="verify an interval release offline")
    check.add_argument("release", type=Path)
    return value


def main(argv=None) -> int:
    value = parser()
    args = value.parse_args(argv)
    if args.command is None:
        value.print_help(sys.stderr)
        return 2
    try:
        if args.command == "check":
            sys.stdout.buffer.write(canonical_bytes(check_interval(args.release)))
            return 0
        plan = load_control(args.plan, "interval plan")
        validate_plan(plan)
        if args.command == "build":
            registry = load_control(args.registry, "deployment registry")
            release_id = Builder(
                plan, args.staging, registry, created_at=args.created_at
            ).build(args.output)
            print(release_id)
            return 0
        registry = (
            None if args.registry is None else load_control(args.registry, "deployment registry")
        )
        # Refused before the endpoint is read: see `opening_phase`.
        opening_phase(plan, [], registry=registry)
        transport = transport_from_environment(plan["provider"]["timeout_seconds"])
        if args.command == "reconcile":
            document = Reconciler(
                plan, args.staging, transport, args.provider_class, registry=registry
            ).reconcile()
            sys.stdout.buffer.write(canonical_bytes(document))
            return 0
        args.staging.mkdir(parents=True, exist_ok=True)
        summary = Collector(
            plan, args.staging, transport, registry=registry, concurrency=args.concurrency,
        ).collect()
        sys.stdout.buffer.write(canonical_bytes(summary))
        return 0
    except (AlexandriaError, OSError) as error:
        print(f"usdc-interval: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
