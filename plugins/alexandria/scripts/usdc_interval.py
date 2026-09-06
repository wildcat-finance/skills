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
resumed like a shard and reconciled like one.
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
    EVIDENCE_CLASSES,
    JOURNAL_CLASSES,
    MAX_DISPUTES,
    OPENING_CLASS,
    RECEIPT_FORMAT,
    Staging,
    ZERO_ADDRESS,
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
RELEASE_NAME = "usdc-interval-v0"

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
        self.hashes: dict[int, str] = {}
        self.code_digests: dict[tuple[str, int], str] = {}

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
            return implementation
        if kind == "implementation-code":
            try:
                code = runtime_code(result, read["address"])
            except AlexandriaError as error:
                raise OpeningRefusal("code-not-hex", block, str(error)) from error
            digest = hashlib.sha256(code).hexdigest()
            self.code_digests[(read["address"], block)] = digest
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
    if "boundary-blocks" not in classes:
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
        """Replay the committed opening reads against the plan they were made from.

        Returns one `(position, read, value, payload)` per read, in plan
        order, and refuses a journal that stops short of the plan, runs past
        it, or holds a record the plan does not name at that position.
        """
        phase = OpeningPhase(self.plan, staged_log_records(self.staging, self.classes))
        entries = list(self.staging.entries(OPENING_CLASS))
        virtual = len(self.plan["shards"])
        replayed = []
        position = 0
        for read in phase.reads():
            if position >= len(entries):
                raise AlexandriaError(
                    "the interval's opening reads are not completely collected, so there "
                    "is nothing to reconcile"
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
        return replayed

    def _compare_opening(self, read, value, second) -> tuple[bool, str, str]:
        """Whether the second provider's answer binds the same thing, and the kind it is."""
        kind = read["kind"]
        block = read["block"]
        if kind == "first-block-header":
            agreed = isinstance(second, dict) and second.get("hash") == value
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
            "format": "alexandria-interval-reconciliation/v1",
            "plan_sha256": plan_digest(self.plan),
            "reconciliation": record,
            "shards": table,
        }
        _atomic_json(self.directory / RECONCILIATION_RECORD, document)
        self.staging.close()
        return document



class Builder:
    """Turn a reconciled staging tree into an Alexandria release, offline.

    Every count and every declared interval is derived from the preserved bytes
    rather than asserted, so `ingest` can refuse an inflated coverage figure
    against the component it describes.
    """

    def __init__(self, plan, staging_root, epochs, registry, *, created_at) -> None:
        validate_plan(plan)
        self.plan = plan
        self.classes = declared_classes(plan)
        self.staging = Staging(staging_root, plan)
        self.root = self.staging.root
        validate_epochs(
            epochs,
            int(plan["interval"]["start"]),
            int(plan["interval"]["end"]),
        )
        self.epochs = epochs
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

    def build(self, output: Path) -> str:
        state = self.staging.committed()
        if state["next_shard"] != len(self.plan["shards"]):
            raise AlexandriaError(
                "the interval is not completely collected, so there is no release to build"
            )
        reconciliation = self._reconciliation()
        documents = {
            "epoch-table": {
                "epochs": self.epochs,
                "format": RECEIPT_FORMAT,
                "reconciliation": reconciliation["reconciliation"],
                "shards": _receipt_shards(reconciliation["shards"]),
            },
            "error-receipts": {"format": "alexandria-interval-errors/v1", "records": self._errors()},
            "interval-plan": self.plan,
            "reconciliation": reconciliation,
            "registry": self.registry,
        }
        for name in self.classes:
            documents[name] = self._journal(name)

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
                captures.append(self._capture(component, document, reconciliation))
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

    def _capture(self, component: str, document, reconciliation) -> dict:
        interval = self.plan["interval"]
        collections = []
        record_count = 0
        if component in EVIDENCE_CLASSES:
            record_count = len(document["records"])
            collections = [{
                "name": component,
                "record_count": record_count,
                "selector": "/records",
            }]
        elif component == "error-receipts":
            record_count = len(document["records"])
            collections = [{
                "name": "error-receipts",
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
            "evidence_class": "recorded-rpc" if component in EVIDENCE_CLASSES else "header-bound",
            "id": component,
            "source": {
                "kind": "json-rpc" if component in EVIDENCE_CLASSES else "local-fixture",
                "locator_class": "provider-endpoint" if component in EVIDENCE_CLASSES else "local-fixture",
                "reference": self.plan["provider"]["class"] if component in EVIDENCE_CLASSES
                else f"derived offline from the collected interval, {component}",
            },
            "scope": {
                "deployment": self.plan["deployment"],
                # `provider-reported`, whatever the plan's policy is called. A
                # `safe` or `finalized` scope owes Alexandria both of its
                # block-range hashes, and this collector reads each shard's end
                # block, never the interval's first one, so the start hash does
                # not exist to give. The named policy and the boundary block it
                # bound are in the plan and the interval receipt; what the
                # release establishes about finality is that a provider
                # reported it, which is the class Phase 0's captures use for
                # the same reason.
                "finality": "provider-reported",
                # No scope hash. Alexandria wants a block-range's start and end
                # hashes together or not at all, and this collector never reads
                # the interval's first block: it reads each shard's end. Those
                # hashes, the epoch boundaries and the finality boundary are all
                # bound in the interval receipt, which is where they belong.
                # Borrowing the operator's epoch evidence to fill a scope field
                # would put one source's hash behind another source's claim.
                "interval": {
                    "end": interval["end"],
                    "kind": "block-range",
                    "start": interval["start"],
                },
                "kind": "full-dataset",
            },
            "venue": self.plan["venue"],
        }


def _role(component: str) -> str:
    return {
        "boundary-blocks": "json-rpc-response",
        "epoch-table": "interval-receipt",
        "error-receipts": "error-receipt",
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
    if component in EVIDENCE_CLASSES:
        gaps.append(
            f"the interval's first block, {plan['interval']['start']}, was not read, so this "
            f"scope binds no start hash and its finality class is provider-reported rather "
            f"than {plan['finality']['policy']}"
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
    settles the things only an interval release can be wrong about.
    """
    release_root = Path(release_root).absolute()
    release_id = verify(release_root)
    manifest = load_bytes(
        read_confined_file(release_root, "manifest.json", "manifest", max_bytes=MAX_CONTROL_BYTES),
        "manifest",
    )
    documents = {}
    plan = load_bytes(
        _component(release_root, manifest, "interval-plan"), "component interval-plan",
        max_bytes=MAX_RAW_COMPONENT_BYTES,
    )
    validate_plan(plan)
    classes = declared_classes(plan)
    for name in ("epoch-table", "error-receipts", "reconciliation", "registry", *classes):
        documents[name] = load_bytes(
            _component(release_root, manifest, name), f"component {name}",
            max_bytes=MAX_RAW_COMPONENT_BYTES,
        )

    interval = plan["interval"]
    start = int(interval["start"])
    end = int(interval["end"])

    receipt = documents["epoch-table"]
    if not isinstance(receipt, dict) or set(receipt) != {
        "epochs", "format", "reconciliation", "shards",
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
    # do, they came from different evidence and have to agree: the epoch hash
    # from the operator's chain reads, the shard hash from what the collector
    # itself saw at that block.
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

    reconciliation = documents["reconciliation"]
    if reconciliation["plan_sha256"] != plan_digest(plan):
        raise AlexandriaError("the reconciliation record belongs to a different plan")
    validate_reconciliation(reconciliation["reconciliation"])
    validate_shard_coverage(reconciliation["shards"], plan["shards"], classes)
    if [shard["status"] for shard in reconciliation["shards"]] != [
        shard["status"] for shard in shards
    ]:
        raise AlexandriaError("the reconciliation and the receipt disagree about a shard")

    disputed = {
        shard["index"] for shard in shards if shard["status"] != "complete"
    }
    captures = {capture["id"]: capture for capture in manifest["captures"]}
    derived = {shard["index"]: {} for shard in plan["shards"]}
    for name in classes:
        journal = documents[name]
        if journal["format"] != JOURNAL_FORMAT or journal["class"] != name:
            raise AlexandriaError(f"the {name} component is not its own journal")
        if journal["interval"] != interval:
            raise AlexandriaError(f"the {name} journal declares another interval")
        staged = {record["shard"] for record in journal["records"]}
        if staged != {shard["index"] for shard in plan["shards"]}:
            raise AlexandriaError(f"the {name} journal does not cover every shard")
        for record in journal["records"]:
            envelope = load_bytes(
                record["response"].encode(), f"{name} response for shard {record['shard']}",
                max_bytes=MAX_RAW_COMPONENT_BYTES,
            )
            result = envelope.get("result")
            derived[record["shard"]][name] = (
                len(result) if isinstance(result, list) else 1
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

    for shard in shards:
        if shard["record_counts"] != derived[shard["index"]]:
            raise AlexandriaError(
                f"shard {shard['index']} declares record counts the journals do not carry"
            )

    return {
        "epochs": len(receipt["epochs"]),
        "interval": {"end": interval["end"], "start": interval["start"]},
        "reconciliation": reconciliation["reconciliation"]["status"],
        "release_id": release_id,
        "shard_statuses": {
            status: sum(1 for shard in shards if shard["status"] == status)
            for status in sorted({shard["status"] for shard in shards})
        },
    }


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
    build.add_argument("--epochs", required=True, type=Path)
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
            epochs = load_control(args.epochs, "epoch table")
            registry = load_control(args.registry, "Compound registry")
            release_id = Builder(
                plan, args.staging, epochs, registry, created_at=args.created_at
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
