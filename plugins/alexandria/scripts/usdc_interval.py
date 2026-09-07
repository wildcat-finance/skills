#!/usr/bin/env python3
"""Collect a bounded Ethereum USDC Comet block interval, resumably.

The network path is explicit and lives in one place: `HttpsTransport`, built
from an environment variable that is never written anywhere. Every other path
in this module takes a transport it was handed, so the whole collector is
exercised offline against a fixture provider and no test opens a socket.

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
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
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
    Staging,
    ZERO_ADDRESS,
    discover_epochs,
    log_identity,
    FINALITY_POLICIES,
    HASH_RE,
    opening_boundaries,
    opening_code_reads,
    opening_prefix,
    plan_digest,
    read_regular,
    runtime_code,
    slot_word_address,
    upgrade_logs,
    validate_epochs,
    validate_plan,
    validate_reconciliation,
    validate_shard_coverage,
)
from alexandria_lib.compound_registry import validate_registry
from alexandria_lib.paths import read_confined_file
from alexandria_lib.release import MAX_RAW_COMPONENT_BYTES, ingest, verify


ENDPOINT_ENV = "ALEXANDRIA_COMPOUND_RPC_URL"
MAX_COLLECT_SECONDS = 3_600
MAX_COLLECT_BYTES = 512 * 1024 * 1024
MAX_RESPONSE_NODES = 2_000_000
RECEIPTS_DIRECTORY = "receipts"
ERROR_RECEIPTS = "errors.jsonl"
RECONCILIATION_DIRECTORY = "reconciliation"
RECONCILIATION_RECORD = "reconciliation.json"
DISPUTED_RESPONSES = "disputed.jsonl"
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


class HttpsTransport:
    """The one network path. The endpoint reaches no file, receipt or message."""

    def __init__(self, endpoint: str, timeout: int) -> None:
        if not endpoint.startswith("https://") or any(c.isspace() for c in endpoint):
            raise AlexandriaError(f"{ENDPOINT_ENV} must name an HTTPS endpoint")
        self._endpoint = endpoint
        self._timeout = timeout
        self._opener = urllib.request.build_opener(_NoRedirect)

    @classmethod
    def from_environment(cls, timeout: int, environ=None) -> "HttpsTransport":
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
            raise TransportError(f"{label} transport failed") from error


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


class OpeningRefusal(AlexandriaError):
    """An opening read the collector will not believe, named by its receipt code."""

    def __init__(self, code: str, block: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.block = block


class OpeningPhase:
    """The opening reads one plan owes, in the order they are made.

    Built from the staged logs, so a fresh run, a resumed run and a reconciler
    all derive the same reads and the same request bytes. `reads()` yields the
    prefix first; the code reads follow only after every slot word has been
    accepted, because they name the implementations the slots revealed.
    Nothing here touches a transport or a file.
    """

    def __init__(self, plan, staged_logs) -> None:
        self.plan = plan
        self.virtual = len(plan["shards"])
        self.start = int(plan["interval"]["start"])
        self.end = int(plan["interval"]["end"])
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
    for name in staging.classes:
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


def replay_opening(plan, staging: Staging, classes) -> tuple[OpeningPhase, list]:
    """Replay the committed opening reads against the plan they were made from.

    Returns the phase, holding every accepted value, and one
    `(position, read, value, payload)` per read in plan order. Refuses a
    journal that stops short of the plan, runs past it, or holds a record the
    plan does not name at that position. Reads no network and changes no file.
    """
    phase = OpeningPhase(plan, staged_log_records(staging, classes))
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
        payload = phase.request(position, read)
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
        envelope = load_bytes(
            entry["response"].encode(), f"staged opening read {position}",
            max_bytes=MAX_RAW_COMPONENT_BYTES,
        )
        result = envelope.get("result") if isinstance(envelope, dict) else None
        value = phase.accept(read, result)
        replayed.append((position, read, value, payload))
        position += 1
    if len(entries) > position:
        raise AlexandriaError(
            "the epoch-evidence journal holds more committed reads than the plan names"
        )
    return phase, replayed


def epochs_from_opening(plan, phase: OpeningPhase, end_hash: str) -> list:
    """The epoch table the preserved opening reads derive, and nothing else.

    Every input is a value `OpeningPhase.accept` took from a journaled read:
    the upgrade logs the shards preserved, the slot word at each boundary, the
    code each implementation answered, and the header hashes at the first
    block and around each upgrade. The interval's last block is bound by the
    last shard's boundary read, which is the one hash the opening phase does
    not make itself.
    """
    interval = plan["interval"]
    block_hashes = {str(block): value for block, value in phase.hashes.items()}
    block_hashes[str(int(interval["end"]))] = end_hash
    return discover_epochs(
        chain=plan["chain"],
        deployment=plan["deployment"],
        proxy=plan["proxy"],
        interval=dict(interval),
        upgrade_logs=[upgrade["record"] for upgrade in phase.upgrades],
        slot_reads={str(block): word for block, word in phase.slot_words.items()},
        code_reads=dict(phase.codes),
        block_hashes=block_hashes,
    )


def shard_requests(plan, shard) -> list[tuple[str, str, list]]:
    """The requests one shard makes: one per declared class, in the plan's order."""
    proxy = plan["proxy"]
    start = hex(shard["start"])
    end = hex(shard["end"])
    requests = {
        "boundary-blocks": ("eth_getBlockByNumber", [end, False]),
        "logs": ("eth_getLogs", [{"address": proxy, "fromBlock": start, "toBlock": end}]),
        "traces": ("trace_filter", [{"fromBlock": start, "toAddress": [proxy], "toBlock": end}]),
    }
    return [(name, *requests[name]) for name in plan["evidence_classes"]]


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
    return classes


class Collector:
    """One bounded collection over one plan, against one transport."""

    def __init__(self, plan, staging_root, transport, *, receipts_root=None) -> None:
        validate_plan(plan)
        self.plan = plan
        self.digest = plan_digest(plan)
        self.classes = declared_classes(plan)
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

    # -- bounds -----------------------------------------------------------

    def _spend(self, count: int) -> None:
        self._bytes += count
        if self._bytes > MAX_COLLECT_BYTES:
            raise AlexandriaError("collection exceeded its total byte ceiling")
        if self._started is not None and time.monotonic() - self._started > MAX_COLLECT_SECONDS:
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
        self._started = time.monotonic()
        self.bind_finality()
        start = self._settle_start()
        shards = self.plan["shards"]
        counts = {name: 0 for name in self.classes}
        for index in range(start, len(shards)):
            shard = shards[index]
            boundary = None
            for name, method, params in shard_requests(self.plan, shard):
                payload, data, result = self._ask(index, name, method, params)
                if name == "boundary-blocks":
                    if not isinstance(result, dict) or not isinstance(result.get("hash"), str):
                        raise AlexandriaError(f"shard {index} boundary block carries no hash")
                    boundary = result["hash"]
                if isinstance(result, list):
                    counts[name] += len(result)
                else:
                    counts[name] += 1
                self.staging.record(index, name, payload, data)
            self.staging.commit(index, shard["end"], boundary)
        opening = self._open_interval()
        self.staging.close()
        return {
            "collected_shards": len(shards) - start,
            "opening_reads": opening,
            "record_counts": counts,
            "resumed_from": start,
            "shards": len(shards),
        }

    # -- the opening phase --------------------------------------------------

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
            phase = OpeningPhase(self.plan, staged_log_records(self.staging, self.classes))
        except AlexandriaError:
            self.record_error(virtual, OPENING_CLASS, "malformed-upgrade-log")
            raise
        committed = list(self.staging.entries(OPENING_CLASS))
        issued = 0
        position = 0
        for read in phase.reads():
            payload = phase.request(position, read)
            label = opening_label(position, read)
            if position < len(committed):
                entry = committed[position]
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
                envelope = load_bytes(
                    entry["response"].encode(), f"staged {label}", max_bytes=MAX_RAW_COMPONENT_BYTES,
                )
                result = envelope.get("result") if isinstance(envelope, dict) else None
                data = None
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

    def __init__(self, plan, staging_root, transport, provider_class) -> None:
        validate_plan(plan)
        self.plan = plan
        self.transport = transport
        if not isinstance(provider_class, str) or not 1 <= len(provider_class) <= 256:
            raise AlexandriaError("the second provider class is not a bounded name")
        if any(character in provider_class for character in ("://", "@")):
            raise AlexandriaError("the second provider class must not carry an endpoint")
        self.provider_class = provider_class
        self.classes = declared_classes(plan)
        self.staging = Staging(staging_root, plan)
        self.root = self.staging.root
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

    def _opening(self) -> list:
        """The committed opening reads, replayed; see `replay_opening`."""
        return replay_opening(self.plan, self.staging, self.classes)[1]

    def _compare_opening(self, read, value, second) -> tuple[bool, str, str]:
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

    def reconcile(self) -> dict:
        """Read the staging tree without changing it, then compare.

        Reconciliation never resumes the collection, because `resume` truncates
        every journal back to its checkpoint. Reading an interval must not be
        able to destroy part of it, least of all on the path that then refuses.
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
        opening = self._opening()

        compared = 0
        matched = 0
        disputed = []
        statuses = {}
        counts = {}
        for shard in shards:
            index = shard["index"]
            boundary = staged[(index, "boundary-blocks")]
            logs = staged.get((index, "logs"))
            counts[index] = self._counts(index, staged)
            status = "complete"
            try:
                second_boundary, boundary_bytes = self._second(
                    index, "boundary-blocks", "eth_getBlockByNumber", [hex(shard["end"]), False]
                )
                second_logs, logs_bytes = None, b""
                if "logs" in self.classes:
                    second_logs, logs_bytes = self._second(
                        index, "logs", "eth_getLogs",
                        [{"address": self.plan["proxy"], "fromBlock": hex(shard["start"]), "toBlock": hex(shard["end"])}],
                    )
            except AlexandriaError:
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
            statuses[index] = status

        # The opening reads: the first block's hash, each slot word and each
        # code digest, asked of the second provider with the primary's exact
        # request bytes. A disagreement keeps both byte sets and settles
        # nothing; the epoch boundary headers are bound by the upgrade logs
        # the primary preserved and are not asked again.
        virtual = len(shards)
        for position, read, value, payload in opening:
            if read["kind"] == "epoch-boundary-header":
                continue
            try:
                second, data = self._second_raw(
                    payload, opening_identifier(virtual, position), opening_label(position, read),
                )
            except AlexandriaError:
                return self._unreconciled(shards, counts, staged, compared, matched, disputed)
            compared += 1
            agreed, kind, identity = self._compare_opening(read, value, second)
            if agreed:
                matched += 1
            else:
                if len(disputed) < MAX_DISPUTES:
                    disputed.append({"identity": identity, "kind": kind, "shard": virtual})
                self._keep(virtual, OPENING_CLASS, data)

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
        self.staging = Staging(staging_root, plan)
        self.root = self.staging.root
        validate_registry(registry)
        self.registry = registry
        if not isinstance(created_at, str) or TIMESTAMP_RE.fullmatch(created_at) is None:
            raise AlexandriaError("the release creation time is not a UTC timestamp")
        self.created_at = created_at

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

    def _journal(self, name: str) -> dict:
        records = list(self.staging.entries(name))
        for record in records:
            if set(record) != {"class", "request", "response", "shard"}:
                raise AlexandriaError(f"a staged {name} record has an unknown shape")
        return {
            "class": name,
            "format": JOURNAL_FORMAT,
            "interval": dict(self.plan["interval"]),
            "records": records,
        }

    def _opening(self, state: dict) -> OpeningPhase:
        """The opening phase the journal committed, or a refusal naming what is missing."""
        if state["offsets"].get(OPENING_CLASS, 0) == 0:
            raise AlexandriaError(
                "the staging tree has no committed epoch-evidence journal; the opening "
                "phase has not been collected, so there is no release to build"
            )
        return replay_opening(self.plan, self.staging, self.classes)[0]

    def _epochs(self, phase: OpeningPhase, end_hash: str) -> list:
        """The epoch table, derived from the opening reads; see `epochs_from_opening`."""
        return epochs_from_opening(self.plan, phase, end_hash)

    def _code_component(self, epochs, phase: OpeningPhase) -> dict:
        """Each implementation's runtime bytes as the collector read them, keyed by address."""
        records = []
        for address in sorted({epoch["implementation"] for epoch in epochs}):
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
        validate_epochs(epochs, phase.start, phase.end)
        code = self._code_component(epochs, phase)
        code_bytes = canonical_bytes(code)
        documents = {
            "epoch-table": {
                "epochs": epochs,
                "format": RECEIPT_FORMAT,
                "implementation_code": {
                    "component": CODE_COMPONENT,
                    "sha256": hashlib.sha256(code_bytes).hexdigest(),
                },
                "reconciliation": reconciliation["reconciliation"],
                "shards": shards,
            },
            "error-receipts": {"format": "alexandria-interval-errors/v1", "records": self._errors()},
            CODE_COMPONENT: code,
            "interval-plan": self.plan,
            "reconciliation": reconciliation,
            "registry": self.registry,
        }
        for name in self.staging.classes:
            documents[name] = self._journal(name)
        boundaries = {"end_hash": end_hash, "start_hash": start_hash}

        parent = output.absolute().parent
        parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.plan-", dir=parent))
        try:
            components = []
            captures = []
            for component, document in sorted(documents.items()):
                relative = f"{component}.json"
                (staging / relative).write_bytes(canonical_bytes(document))
                components.append({
                    "access": "public",
                    "media_type": "application/json",
                    "name": component,
                    "path": relative,
                    "redistribution": "permitted",
                    "role": _role(component),
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

    def _capture(self, component: str, document, reconciliation, boundaries) -> dict:
        interval = self.plan["interval"]
        evidence = component in JOURNAL_CLASSES
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
        gaps = _gaps(component, self.plan, self.registry, reconciliation)
        unsupported = _unsupported(component)
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


def _gaps(component: str, plan, registry, reconciliation) -> list:
    gaps = []
    if component == "registry":
        others = [
            f"{entry['network']}/{entry['market']}"
            for entry in registry["entries"]
            if not (entry["network"] == "mainnet" and entry["market"] == "usdc")
        ]
        gaps.append(
            f"{len(others)} of the {len(registry['entries'])} registry entries at the pin "
            "were not collected; this release covers the Ethereum USDC Comet only"
        )
        return gaps
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
    plan = load_bytes(
        _component(release_root, manifest, "interval-plan"), "component interval-plan",
        max_bytes=MAX_RAW_COMPONENT_BYTES,
    )
    validate_plan(plan)
    classes = declared_classes(plan)
    journal_names = (*classes, OPENING_CLASS)
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
    if not isinstance(receipt, dict) or set(receipt) != {
        "epochs", "format", "implementation_code", "reconciliation", "shards",
    } or receipt["format"] != RECEIPT_FORMAT:
        raise AlexandriaError("the interval receipt has an unknown shape")
    validate_epochs(receipt["epochs"], start, end)
    for epoch in receipt["epochs"]:
        if epoch["proxy"] != plan["proxy"] or epoch["chain"] != plan["chain"]:
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
    for epoch in receipt["epochs"]:
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
    proxy = plan["proxy"]
    reads = {}
    virtual = len(plan["shards"])
    for name in journal_names:
        journal = documents[name]
        if (
            not isinstance(journal, dict)
            or set(journal) != {"class", "format", "interval", "records"}
            or journal["format"] != JOURNAL_FORMAT
        ):
            raise AlexandriaError(f"the {name} component is not an interval journal")
        if journal["class"] != name:
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
            if record["class"] != name:
                raise AlexandriaError(
                    f"the {name} journal holds a {str(record['class'])[:64]} record, so the "
                    "plan and the journals disagree about the declared classes"
                )
        staged = {record["shard"] for record in journal["records"]}
        if name == OPENING_CLASS:
            if staged and staged != {virtual}:
                raise AlexandriaError(
                    "the epoch-evidence journal holds a record outside the virtual shard index"
                )
        else:
            if staged != {shard["index"] for shard in plan["shards"]}:
                raise AlexandriaError(f"the {name} journal does not cover every shard")
            for record in journal["records"]:
                if record["request"].encode() != planned_requests[(record["shard"], name)]:
                    raise AlexandriaError(
                        f"the {name} record filed under shard {record['shard']} is not the "
                        "read the plan names there"
                    )
                envelope = load_bytes(
                    record["response"].encode(), f"{name} response for shard {record['shard']}",
                    max_bytes=MAX_RAW_COMPONENT_BYTES,
                )
                # The envelope the collector accepted for this read. `_ask`
                # refuses an answer whose id is not the request's, one
                # carrying a JSON-RPC error and one carrying no result, and
                # writes an error receipt rather than a journal record for
                # each. None of that was re-read from the release, so a
                # preserved error, or another read's answer, stood as the
                # shard's evidence and counted as one record of it.
                if (
                    not isinstance(envelope, dict)
                    or envelope.get("jsonrpc") != "2.0"
                    or envelope.get("id") != request_identifier(record["shard"], name)
                    or "error" in envelope
                    or "result" not in envelope
                ):
                    raise AlexandriaError(
                        f"the {name} response for shard {record['shard']} is not the answer "
                        "its preserved request names"
                    )
                result = envelope["result"]
                # A `logs` or `trace_filter` answer is a list of entries, and
                # the entries are read below. A result of any other shape was
                # counted as one read and never looked at.
                if name in ENTRY_BLOCK_CLASSES and not isinstance(result, list):
                    raise AlexandriaError(
                        f"the {name} result for shard {record['shard']} is not a list of entries"
                    )
                # The two truncation rules `_ask` applies to the same bytes: a
                # marked envelope and a page filled to the provider's declared
                # limit are refused there rather than kept, because neither is
                # a complete answer to a bounded request. A release preserving
                # one of them declared a shard complete on a read the
                # collector would have stopped for.
                if envelope.get("truncated") is True:
                    raise AlexandriaError(
                        f"the {name} response for shard {record['shard']} is marked truncated"
                    )
                if (
                    isinstance(result, list)
                    and len(result) >= plan["provider"]["page_limit"]
                ):
                    raise AlexandriaError(
                        f"the {name} result for shard {record['shard']} stands at the "
                        "provider's page limit, so it is not a complete read"
                    )
                reads[(record["shard"], name)] = reads.get((record["shard"], name), 0) + 1
                # Two records of one class for one shard are two reads, so
                # their sizes add. Assigning here declared the last record's
                # size alone, so a journal could carry a shard's evidence
                # twice while the receipt's count named one read of it.
                derived[record["shard"]][name] = derived[record["shard"]].get(name, 0) + (
                    len(result) if isinstance(result, list) else 1
                )
                if name == BOUNDARY_CLASS:
                    boundary_headers[record["shard"]] = result
                if name in ENTRY_BLOCK_CLASSES:
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
                        address = _entry_address(entry, name, label)
                        if address != proxy:
                            raise AlexandriaError(
                                f"{label} names address {address}, not the {proxy} its "
                                "read asked for"
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
    phase = _replay_release_opening(plan, documents, classes)
    first_hash = phase.hashes[start]

    # The implementation code, re-hashed from the component's bytes: the
    # receipt names the component's digest, and each epoch names the digest of
    # its implementation's runtime bytes; both are recomputed here, before the
    # table as a whole is compared, so a digest the bytes do not carry is
    # refused under its own name.
    implementations = _recheck_implementation_code(
        receipt, documents[CODE_COMPONENT], component_bytes[CODE_COMPONENT],
    )
    derived_epochs = epochs_from_opening(plan, phase, shards[-1]["end_hash"])
    if derived_epochs != receipt["epochs"]:
        raise AlexandriaError(
            "the epoch table does not match the epochs the preserved opening reads derive"
        )

    _check_scopes(manifest, plan, journal_names, first_hash, shards[-1]["end_hash"])

    return {
        "epochs": len(receipt["epochs"]),
        "implementations": implementations,
        "interval": {"end": interval["end"], "start": interval["start"]},
        "reconciliation": reconciliation["reconciliation"]["status"],
        "release_id": release_id,
        "shard_statuses": {
            status: sum(1 for shard in shards if shard["status"] == status)
            for status in sorted({shard["status"] for shard in shards})
        },
    }


def _replay_release_opening(plan, documents, classes) -> OpeningPhase:
    """Replay the release's `epoch-evidence` records against its plan, offline."""
    logs = []
    if "logs" in classes:
        for record in documents["logs"]["records"]:
            envelope = load_bytes(
                record["response"].encode(), "logs response", max_bytes=MAX_RAW_COMPONENT_BYTES,
            )
            result = envelope.get("result") if isinstance(envelope, dict) else None
            if isinstance(result, list):
                logs.extend(result)
    phase = OpeningPhase(plan, logs)
    entries = documents[OPENING_CLASS]["records"]
    position = 0
    for read in phase.reads():
        if position >= len(entries):
            raise AlexandriaError(
                "the epoch-evidence journal stops short of the opening reads the plan names"
            )
        entry = entries[position]
        if entry["request"].encode() != phase.request(position, read):
            raise AlexandriaError(
                f"epoch-evidence record {position} is not the opening read the plan names there"
            )
        envelope = load_bytes(
            entry["response"].encode(), f"opening read {position}", max_bytes=MAX_RAW_COMPONENT_BYTES,
        )
        phase.accept(read, envelope.get("result") if isinstance(envelope, dict) else None)
        position += 1
    if len(entries) > position:
        raise AlexandriaError(
            "the epoch-evidence journal holds more records than the opening reads the plan names"
        )
    return phase


def _recheck_implementation_code(receipt, component, data: bytes) -> dict:
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
    for epoch in receipt["epochs"]:
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
        action = entry.get("action") if isinstance(entry.get("action"), dict) else {}
        created = entry.get("result") if isinstance(entry.get("result"), dict) else {}
        value = next(
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
    reconcile = commands.add_parser(
        "reconcile", help="run the collected interval past a second provider"
    )
    reconcile.add_argument("--plan", required=True, type=Path)
    reconcile.add_argument("--staging", required=True, type=Path)
    reconcile.add_argument("--provider-class", required=True)
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
            registry = load_control(args.registry, "Compound registry")
            release_id = Builder(
                plan, args.staging, registry, created_at=args.created_at
            ).build(args.output)
            print(release_id)
            return 0
        transport = HttpsTransport.from_environment(plan["provider"]["timeout_seconds"])
        if args.command == "reconcile":
            document = Reconciler(plan, args.staging, transport, args.provider_class).reconcile()
            sys.stdout.buffer.write(canonical_bytes(document))
            return 0
        args.staging.mkdir(parents=True, exist_ok=True)
        summary = Collector(plan, args.staging, transport).collect()
        sys.stdout.buffer.write(canonical_bytes(summary))
        return 0
    except (AlexandriaError, OSError) as error:
        print(f"usdc-interval: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
