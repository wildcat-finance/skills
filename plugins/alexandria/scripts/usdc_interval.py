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

A subject-set plan that also declares `log_attribution_parts` moves the
attribution rows out of the epoch table into one `log-attributions.<k>` part
per journal range, under receipt `alexandria-interval-receipt/v4`. `check`
derives the parts from the plan and compares each one with the rows
`attribute_logs` derives from the preserved logs of its own shards.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import functools
import hashlib
import http.client
import itertools
import json
import os
from pathlib import Path
import queue
import selectors
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import weakref

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
    MAX_JOURNAL_BYTES,
    OPENING_CLASS,
    PARTS_FIELD,
    PARTS_RECEIPT_FORMAT,
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
    journal_entries,
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
from alexandria_lib.release import (
    MAX_COMPONENTS,
    MAX_MANIFEST_NODES,
    MAX_RAW_COMPONENT_BYTES,
    encode_manifest,
    ingest,
    load_manifest,
    read_manifest_bytes,
    verify,
)


ENDPOINT_ENV = "ALEXANDRIA_COMPOUND_RPC_URL"
BEARER_ENV = "ALEXANDRIA_RPC_BEARER"  # phylax: allow the environment variable's name, never a credential value
LOOPBACK_ALLOW_ENV = "ALEXANDRIA_RPC_ALLOW_LOOPBACK_HTTP"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1"})
MAX_COLLECT_SECONDS = 3_600
# Past MAX_COLLECT_BYTES a collection starts no new shard, but the shards
# already running finish and commit, so a restart refetches none of them.
# MAX_COLLECT_DRAIN_BYTES is the hard stop for that finishing work.
MAX_COLLECT_BYTES = 512 * 1024 * 1024
MAX_COLLECT_DRAIN_BYTES = 2 * MAX_COLLECT_BYTES
# A bounded worker pool fetches this many shards' data concurrently; commits
# still land strictly in ascending shard order (see `Collector._collect_shards`).
# Conservative by default -- tune with `collect --concurrency`, never past the
# ceiling, which exists so a plan cannot turn concurrency into an unbounded
# thread count.
DEFAULT_COLLECT_CONCURRENCY = 4
MAX_COLLECT_CONCURRENCY = 8
DEFAULT_TRACE_CONCURRENCY = 4
MAX_TRACE_CONCURRENCY = 16
DEFAULT_RPC_CONCURRENCY = 8
MAX_RPC_CONCURRENCY = 8
MAX_RESPONSE_NODES = 2_000_000
# _bounded_request's own real deadline for one request, independent of a
# plan's own declared provider.timeout_seconds (bounded separately, much
# more loosely, by alexandria_lib.interval.MAX_TIMEOUT_SECONDS). Every real
# shard reconciled against the live hosted endpoint so far (1,539 of them,
# 2026-09-21) took at most 34 seconds, and every already-committed example
# already declares 25; a hung request -- most plausibly a stalled DNS
# resolution, which no socket-level timeout reaches, see _bounded_request --
# should not need up to an hour, or whatever larger ceiling a plan happens
# to declare, to reveal itself.
MAX_REQUEST_SECONDS = 60
RECEIPTS_DIRECTORY = "receipts"
ERROR_RECEIPTS = "errors.jsonl"
RECONCILIATION_DIRECTORY = "reconciliation"
RECONCILIATION_RECORD = "reconciliation.json"
DISPUTED_RESPONSES = "disputed.jsonl"
# Reconciliation's own progress marker, separate from `Staging`'s: a shard's
# comparison work against the second provider, not the collected bytes
# themselves. See `Reconciler._save_reconcile_checkpoint`.
RECONCILE_CHECKPOINT_NAME = "checkpoint.json"
# v2 binds the checkpoint to the staging tree's committed boundary hash as well
# as to the plan and the second provider; a v1 checkpoint is not trusted.
RECONCILE_CHECKPOINT_FORMAT = "alexandria-interval-reconcile-checkpoint/v2"
JOURNAL_FORMAT = "alexandria-interval-journal/v1"
RECONCILIATION_FORMAT = "alexandria-interval-reconciliation/v1"
RECONCILIATION_BINDING_GAP = "the reconciliation record has no journal digest binding"
TARGETED_TRACE_GAP = (
    "traces cover only transactions named by the subjects' preserved logs; "
    "transactions with no matching log were not traced"
)
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
# A split plan's attribution parts: one component per journal range, named
# `log-attributions.<k>` beside `logs.<k>`. A part is written and read under the
# byte and node bounds every other component has, and `MAX_PART_BYTES` and
# `MAX_PART_NODES` name those bounds where the part rule applies them.
PART_CLASS = "log-attributions"
PART_FORMAT = "alexandria-interval-log-attributions/v1"
MAX_PART_BYTES = MAX_RAW_COMPONENT_BYTES
MAX_PART_NODES = MAX_RESPONSE_NODES



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
    collection cannot run to its end and then have no release to build. The
    count is the fixed components, these journals and, under
    `log_attribution_parts`, one attribution part per journal range.
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
    parts = attribution_parts(plan)
    total = len(FIXED_COMPONENTS) + len(components) + len(parts)
    if total > MAX_COMPONENTS:
        derived = f"{len(components)} journal components"
        if parts:
            derived += f" and {len(parts)} {PART_CLASS} parts"
        raise AlexandriaError(
            f"the plan derives {derived}, so its release would carry "
            f"{total} components, above the {MAX_COMPONENTS}-component limit"
        )
    return components


def attribution_parts(plan) -> dict:
    """The release's attribution parts, derived from the plan alone.

    Empty unless the plan declares `log_attribution_parts`. Otherwise maps
    `log-attributions.<k>` to `{"class", "index", "first", "last"}` for the
    plan's `k`th journal range, the shards `logs.<k>` covers, in shard order.
    A part holds the attribution rows of every preserved log in those shards,
    so a range with no preserved log gives an empty part.
    """
    if PARTS_FIELD not in plan:
        return {}
    ranges = plan_partition(plan)
    if ranges is None:
        raise AlexandriaError(
            f"a plan that declares {PARTS_FIELD} derives its parts from its journal ranges, "
            "and this one declares none"
        )
    return {
        component_name(PART_CLASS, index): {
            "class": PART_CLASS, "index": index, "first": first, "last": last,
        }
        for index, (first, last) in enumerate(ranges)
    }


def part_label(name: str, part) -> str:
    """How a refusal names one attribution part: its component and its shard range."""
    return f"{name} (shards {part['first']} to {part['last']})"


def part_blocks(plan, part) -> tuple:
    """The inclusive block range one attribution part's shards cover."""
    shards = plan["shards"]
    return shards[part["first"]]["start"], shards[part["last"]]["end"]


def attribution_part_rows(plan, parts, rows) -> dict:
    """Slice the list `attribute_logs` returns into the plan's parts, keeping its order.

    The list's blocks never decrease, so one pass hands each row to the part
    whose blocks hold its block. Each part then holds the rows of every
    preserved log in its own shards, in `attribute_logs` order. A row outside
    every part, or one that runs back across a part boundary, refuses by name.
    """
    ordered = [(name, part, *part_blocks(plan, part)) for name, part in parts.items()]
    sliced = {name: [] for name, *_rest in ordered}
    position = 0
    for row in rows:
        block = int(row["block_number"])
        while position < len(ordered) and block > ordered[position][3]:
            position += 1
        if position == len(ordered) or block < ordered[position][2]:
            raise AlexandriaError(
                f"the attribution row at block {block} lies outside every {PART_CLASS} part "
                "or out of block order"
            )
        sliced[ordered[position][0]].append(row)
    return sliced


def attribution_part(part, rows) -> dict:
    """One `alexandria-interval-log-attributions/v1` document: a part's index, range and rows."""
    return {
        "first_shard": part["first"],
        "format": PART_FORMAT,
        "last_shard": part["last"],
        "part": part["index"],
        "rows": rows,
    }


def part_bytes(name: str, part, document) -> bytes:
    """One part's canonical bytes, refused by name above the part bounds."""
    try:
        data = canonical_bytes(document, max_nodes=MAX_PART_NODES)
    except AlexandriaError as error:
        raise AlexandriaError(f"{part_label(name, part)} cannot be written: {error}") from error
    if len(data) > MAX_PART_BYTES:
        raise AlexandriaError(
            f"{part_label(name, part)} encodes to {len(data)} bytes, above the "
            f"{MAX_PART_BYTES}-byte component ceiling"
        )
    return data


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


def attribution_part_gap(plan, part) -> str:
    """What one attribution part does not hold, named on its own coverage.

    A part's scope names the whole interval, like the epoch table's. This
    sentence says which shards and blocks the part's rows come from, so a
    reader of one part does not take it for every row. `check` derives the
    same sentence from the plan and requires it.
    """
    low, high = part_blocks(plan, part)
    return (
        f"part {part['index']} of the log attributions holds the rows of shards "
        f"{part['first']} to {part['last']}, blocks {low} to {high}; the log "
        "attributions' other parts hold the interval's other rows"
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


class _KeptResponse(http.client.HTTPResponse):
    """A response that returns its connection for reuse once its body is read.

    `_open_kept` sets `_release`. `fp` is already `None` at `close` only when
    a read reached the end of the body, so a response closed early -- an
    error status, or a body past the component ceiling -- closes its
    connection rather than leave unread bytes on it for the next request.
    """

    _release = None

    def close(self):
        consumed = self.fp is None
        try:
            super().close()
        finally:
            release, self._release = self._release, None
            if release is not None:
                release(consumed and not self.will_close)


class _KeptHTTPConnection(http.client.HTTPConnection):
    response_class = _KeptResponse


class _KeptHTTPSConnection(http.client.HTTPSConnection):
    response_class = _KeptResponse


def _idle_socket_is_readable(sock) -> bool:
    """Whether the server closed, or wrote to, a connection while it sat idle.

    A selector, not `select.select`: a split plan holds one journal handle per
    component, so a socket's descriptor can pass `select`'s 1,024 limit.
    """
    if getattr(sock, "pending", lambda: 0)():
        return True
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(sock, selectors.EVENT_READ)
            return bool(selector.select(0))
    except (OSError, ValueError):
        return True


class _KeptConnections:
    """The idle connections one transport keeps open between requests.

    At most `limit` wait idle, one per worker slot. A connection comes back
    only after its whole response body was read, and one whose socket is
    readable while idle is closed rather than reused.
    """

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._lock = threading.Lock()
        self._idle = []

    def take(self, key):
        while True:
            with self._lock:
                found = next((position for position, (held, _) in enumerate(self._idle) if held == key), None)
                if found is None:
                    return None
                _, connection = self._idle.pop(found)
            if connection.sock is not None and not _idle_socket_is_readable(connection.sock):
                return connection
            connection.close()

    def release(self, key, connection, reusable: bool) -> None:
        if reusable and connection.sock is not None:
            with self._lock:
                if len(self._idle) < self._limit:
                    self._idle.append((key, connection))
                    return
        connection.close()

    def close(self) -> None:
        with self._lock:
            idle, self._idle = self._idle, []
        for _, connection in idle:
            connection.close()


# A kept connection the server closed while it sat idle fails with one of
# these before any response byte arrives.
_STALE_CONNECTION_ERRORS = (
    http.client.RemoteDisconnected, BrokenPipeError, ConnectionResetError, ConnectionAbortedError,
    ssl.SSLEOFError,
)


def _open_kept(handler, http_class, req, connections, **http_conn_args):
    """`AbstractHTTPHandler.do_open`, keeping the connection for the next request.

    urllib sends `Connection: close` and shuts the socket after each
    response, so every call paid a new TCP connect and, over HTTPS, a new TLS
    handshake. This sends neither. A kept connection that fails with
    `_STALE_CONNECTION_ERRORS` is closed and the request is sent once more
    on a new connection; a new connection's failure is never retried. Proxy
    tunnelling, redirect refusal and error statuses stay with the opener's
    other handlers, exactly as `do_open` leaves them.
    """
    host = req.host
    if not host:
        raise urllib.error.URLError("no host given")
    headers = dict(req.unredirected_hdrs)
    headers.update({name: value for name, value in req.headers.items() if name not in headers})
    headers = {name.title(): value for name, value in headers.items()}
    tunnel_headers = {}
    if req._tunnel_host and "Proxy-Authorization" in headers:
        # Proxy-Authorization should not be sent to the origin server.
        tunnel_headers["Proxy-Authorization"] = headers.pop("Proxy-Authorization")
    key = (host, req._tunnel_host, tuple(sorted(tunnel_headers.items())))
    connection = connections.take(key)
    reused = connection is not None
    while True:
        if connection is None:
            connection = http_class(host, timeout=req.timeout, **http_conn_args)
            if req._tunnel_host:
                connection.set_tunnel(req._tunnel_host, headers=tunnel_headers)
        else:
            connection.timeout = req.timeout
            connection.sock.settimeout(req.timeout)
        connection.set_debuglevel(handler._debuglevel)
        try:
            try:
                connection.request(
                    req.get_method(), req.selector, req.data, headers,
                    encode_chunked=req.has_header("Transfer-encoding"),
                )
            except _STALE_CONNECTION_ERRORS:
                raise
            except OSError as error:
                raise urllib.error.URLError(error)
            response = connection.getresponse()
        except _STALE_CONNECTION_ERRORS:
            connection.close()
            if not reused:
                raise
            connection, reused = None, False
            continue
        except BaseException:
            connection.close()
            raise
        break
    response._release = functools.partial(connections.release, key, connection)
    response.url = req.get_full_url()
    response.msg = response.reason
    return response


class _KeptHTTPHandler(urllib.request.HTTPHandler):
    def __init__(self, connections: _KeptConnections) -> None:
        super().__init__()
        self._connections = connections

    def http_open(self, req):
        return _open_kept(self, _KeptHTTPConnection, req, self._connections)


class _KeptHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, connections: _KeptConnections) -> None:
        super().__init__()
        self._connections = connections

    def https_open(self, req):
        return _open_kept(self, _KeptHTTPSConnection, req, self._connections, context=self._context)


class _RequestTask:
    """One request queued for `_RequestWorkers`, which a caller may cancel until it starts."""

    __slots__ = ("_call", "_lock", "_state", "done")

    def __init__(self, call) -> None:
        self._call = call
        self._lock = threading.Lock()
        self._state = "queued"
        self.done = threading.Event()

    def run(self) -> None:
        with self._lock:
            if self._state != "queued":
                return
            self._state = "running"
        try:
            self._call()
        finally:
            self.done.set()

    def cancel(self) -> bool:
        with self._lock:
            if self._state != "queued":
                return False
            self._state = "cancelled"
            return True


class _RequestWorkers:
    """The threads that run one transport's requests, at most `limit` of them.

    Started as they are first needed and kept, where `_bounded_request` used
    to start one thread per call. They are daemons, as that one was, so a
    call abandoned in a hang never blocks process exit; a
    `ThreadPoolExecutor` joins its workers at exit, so it is not used here.
    """

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._tasks = queue.SimpleQueue()
        self._lock = threading.Lock()
        self._started = 0

    def submit(self, call) -> _RequestTask:
        task = _RequestTask(call)
        self._tasks.put(task)
        with self._lock:
            if self._started < self._limit:
                self._started += 1
                threading.Thread(target=self._work, name="alexandria-request", daemon=True).start()
        return task

    def _work(self) -> None:
        while (task := self._tasks.get()) is not None:
            task.run()

    def close(self) -> None:
        """Let every started thread exit once the queue ahead of it drains."""
        with self._lock:
            started, self._started = self._started, self._limit
        for _ in range(started):
            self._tasks.put(None)


def _bounded_request(
    opener, message: urllib.request.Request, timeout: int, label: str, *, workers: _RequestWorkers, slots=None,
) -> bytes:
    """Run one HTTP request under a real deadline that covers the whole call.

    `urlopen(..., timeout=timeout)` only reaches a socket that already
    exists: `socket.create_connection` calls `getaddrinfo` *before* creating
    one, with no timeout parameter of its own -- read its source. A stalled
    DNS resolution can hang there past any configured timeout, with the CPU
    idle and no exception ever raised, which is indistinguishable from a
    process that is simply still working unless something outside urllib
    bounds the whole call. Running it on one of the transport's `workers`
    and bounding the wait for it covers every stage -- resolution, connect,
    and read -- not only the ones a socket timeout already reaches. The
    deadline also covers any wait for a free worker: a call still queued when
    it passes is cancelled and never sent.

    The deadline is `min(timeout, MAX_REQUEST_SECONDS)`, never the bare
    plan-declared `timeout`: a plan's own ceiling is validated much more
    loosely (`alexandria_lib.interval.MAX_TIMEOUT_SECONDS`) than what a
    single request should realistically ever need, precisely so that an
    already-authored plan's declared value never has to change -- and
    changing it would change `plan_digest` and invalidate every checkpoint
    already bound to that plan. Capping the real wait here, separately,
    gets a fast, bounded failure without touching the plan at all.

    Python cannot forcibly cancel a running thread. A genuine hang leaves
    its thread abandoned rather than making this call wait on it; the thread
    is daemonized so an abandoned one never blocks process exit. Until the
    call returns, that thread holds its worker and its slot.
    """
    bounded = min(timeout, MAX_REQUEST_SECONDS)
    outcome: dict = {}

    def _run() -> None:
        acquired = False
        try:
            if slots is not None:
                acquired = slots.acquire(timeout=bounded)
                if not acquired:
                    raise TransportError("request capacity timed out")
            with opener.open(message, timeout=bounded) as response:
                if response.status != 200:
                    outcome["error"] = TransportError(f"{label} returned HTTP {response.status}")
                    return
                outcome["data"] = response.read(MAX_RAW_COMPONENT_BYTES + 1)
        except urllib.error.URLError as error:
            _close_transport_error(error)
            outcome["error"] = TransportError(f"{label} transport failed")
        except Exception as error:  # noqa: BLE001
            # Not every failure below urlopen's own retry logic arrives as a
            # URLError: a read that times out after the connection is already
            # open can raise a bare TimeoutError straight out of the socket
            # layer instead (observed for real: a live loopback query timed
            # out this way and the narrower except above let it escape
            # uncaught, leaving `outcome` with neither "data" nor "error" and
            # the caller crashing on a KeyError instead of seeing a refusal).
            # Caught broadly here so this thread can never finish without
            # setting one or the other -- label-only, exactly like every
            # other refusal on this path; see _close_transport_error.
            _close_transport_error(error)
            outcome["error"] = TransportError(f"{label} transport failed")
        finally:
            if acquired:
                slots.release()

    task = workers.submit(_run)
    if not task.done.wait(bounded):
        task.cancel()
        raise TransportError(
            f"{label} did not finish within {bounded} seconds -- possibly stalled in DNS "
            "resolution, which no socket-level timeout reaches"
        )
    if "error" in outcome:
        raise outcome["error"]
    return outcome["data"]


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
        # One kept connection per worker slot; the default ProxyHandler still
        # reads the environment, as the default opener's does.
        self._connections = _KeptConnections(MAX_RPC_CONCURRENCY)
        weakref.finalize(self, self._connections.close)
        self._workers = _RequestWorkers(MAX_RPC_CONCURRENCY)
        weakref.finalize(self, self._workers.close)
        self._opener = urllib.request.build_opener(_NoRedirect, _KeptHTTPSHandler(self._connections))

    @classmethod
    def from_environment(cls, timeout: int, environ=None) -> "HttpsTransport":
        values = os.environ if environ is None else environ
        raw_bearer = values.get(BEARER_ENV)
        return cls(values.get(ENDPOINT_ENV, ""), timeout, raw_bearer if raw_bearer else None)

    def request(self, payload: bytes, label: str, *, slots=None) -> bytes:
        headers = dict(REQUEST_HEADERS)
        if self._bearer is not None:
            headers["Authorization"] = f"Bearer {self._bearer}"
        message = urllib.request.Request(
            self._endpoint,
            data=payload,
            headers=headers,
            method="POST",
        )
        return _bounded_request(self._opener, message, self._timeout, label, workers=self._workers, slots=slots)


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
        self._connections = _KeptConnections(MAX_RPC_CONCURRENCY)
        weakref.finalize(self, self._connections.close)
        self._workers = _RequestWorkers(MAX_RPC_CONCURRENCY)
        weakref.finalize(self, self._workers.close)
        self._opener = urllib.request.build_opener(
            _NoRedirect, urllib.request.ProxyHandler({}), _KeptHTTPHandler(self._connections),
        )

    @classmethod
    def from_environment(cls, timeout: int, environ=None) -> "LoopbackHttpTransport":
        values = os.environ if environ is None else environ
        return cls(values.get(ENDPOINT_ENV, ""), timeout)

    def request(self, payload: bytes, label: str, *, slots=None) -> bytes:
        message = urllib.request.Request(
            self._endpoint,
            data=payload,
            headers=dict(REQUEST_HEADERS),
            method="POST",
        )
        return _bounded_request(self._opener, message, self._timeout, label, workers=self._workers, slots=slots)


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


def replay_opening(
    plan, staging: Staging, classes, registry=None, *, log_records=None, entries=None,
) -> tuple[OpeningPhase, list]:
    """Replay the committed opening reads against the plan they were made from.

    Returns the phase, holding every accepted value, and one
    `(position, read, value, payload)` per read in plan order. Refuses a
    journal that stops short of the plan, runs past it, or holds a record the
    plan does not name at that position. Reads no network and changes no file.
    A caller that has already read the journals passes `log_records` and the
    opening `entries`, and the staging tree is not read again.
    """
    if log_records is None:
        log_records = staged_log_records(staging, classes)
    phase = opening_phase(plan, log_records, registry=registry)
    if entries is None:
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


class _ReadOutcome:
    """Carry a worker result or refusal back to the ordered coordinator."""

    def __init__(self, call):
        try:
            self.value, self.error = call(), None
        except Exception as error:
            self.value, self.error = None, error

    def result(self):
        if self.error is not None:
            raise self.error
        return self.value


def _read_batches(items, read, limit):
    """Bound submitted work and retained responses, preserving input order.

    At most `limit` reads run at once, and at most `limit` more wait settled
    for the caller. A settled read frees its slot for the next item at once,
    so a slow read no longer idles the others. A caller that stops early
    leaves the running reads to settle when the generator closes.
    """
    iterator = iter(items)
    if limit == 1:
        for item in iterator:
            yield item, _ReadOutcome(lambda: read(item))
        return
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=limit)
    window = []
    exhausted = False
    try:
        while True:
            running = [future for _item, future in window if not future.done()]
            if not exhausted and len(running) < limit and len(window) < 2 * limit:
                pulled = list(itertools.islice(iterator, 1))
                exhausted = not pulled
                window.extend((item, pool.submit(_ReadOutcome, lambda item=item: read(item))) for item in pulled)
            elif not window:
                return
            elif window[0][1].done():
                item, future = window.pop(0)
                yield item, future.result()
            else:
                concurrent.futures.wait(running, return_when=concurrent.futures.FIRST_COMPLETED)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)


def _rpc_concurrency(value):
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_RPC_CONCURRENCY:
        raise AlexandriaError(f"RPC concurrency must be a whole number from 1 to {MAX_RPC_CONCURRENCY}")
    return value


def _rpc_request(owner, payload, label):
    # Real transports retain the slot inside the HTTP worker even if its
    # caller's deadline expires during DNS or response reading.
    if isinstance(owner.transport, (HttpsTransport, LoopbackHttpTransport)):
        return owner.transport.request(payload, label, slots=owner._rpc_slots)
    with owner._rpc_slots:
        return owner.transport.request(payload, label)


def _trace_concurrency(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_TRACE_CONCURRENCY:
        raise AlexandriaError(
            f"trace concurrency must be a whole number from 1 to {MAX_TRACE_CONCURRENCY}"
        )
    return value


def _ordered_trace_results(hashes, ask, concurrency, slots):
    """Overlap a bounded request window, yielding only in transaction order.

    The window refills a slot as soon as any call settles, so one slow call
    does not idle the others. A settled result waits until every earlier hash
    has yielded, so `ask` returns only what its caller keeps. The owner's
    slots also bound calls across concurrent collector shards. A failure
    stops window refill; already running calls settle before the exception
    escapes. Workers never write a shard or advance a checkpoint.
    """
    if concurrency == 1:
        for tx_hash in hashes:
            with slots:
                yield ask(tx_hash)
        return
    if not hashes:
        return
    def fetch(tx_hash):
        with slots:
            return ask(tx_hash)

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=min(concurrency, len(hashes)))
    window = []
    submitted = 0
    try:
        while window or submitted < len(hashes):
            failed = any(future.done() and future.exception() is not None for future in window)
            running = [future for future in window if not future.done()]
            if not failed and len(running) < concurrency and submitted < len(hashes):
                window.append(pool.submit(fetch, hashes[submitted]))
                submitted += 1
            elif window[0].done():
                yield window.pop(0).result()
            else:
                concurrent.futures.wait(running, return_when=concurrent.futures.FIRST_COMPLETED)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)


class Collector:
    """One bounded collection over one plan, against one transport."""

    def __init__(
        self, plan, staging_root, transport, *, receipts_root=None, registry=None,
        concurrency=1, trace_concurrency=DEFAULT_TRACE_CONCURRENCY,
        rpc_concurrency=DEFAULT_RPC_CONCURRENCY,
    ) -> None:
        validate_plan(plan)
        self.trace_concurrency = _trace_concurrency(trace_concurrency)
        self._trace_slots = threading.BoundedSemaphore(self.trace_concurrency)
        self.rpc_concurrency = _rpc_concurrency(rpc_concurrency)
        self._rpc_slots = threading.BoundedSemaphore(self.rpc_concurrency)
        self._coordinator = threading.get_ident()
        self._worker_errors = threading.local()
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

    def _spend(self, count: int, *, draining: bool = False) -> None:
        """Count one request's or response's bytes against the run's ceilings.

        A read for a shard that has already started passes `draining`, and
        refuses only past `MAX_COLLECT_DRAIN_BYTES`: the loops start no new
        shard once `_spent` holds, so that shard can finish and commit.
        """
        with self._bytes_lock:
            self._bytes += count
            over_bytes = self._bytes > (MAX_COLLECT_DRAIN_BYTES if draining else MAX_COLLECT_BYTES)
            over_time = (
                self._started is not None
                and time.monotonic() - self._started > MAX_COLLECT_SECONDS
            )
        if over_bytes and draining:
            raise AlexandriaError("collection exceeded its hard byte ceiling while finishing started shards")
        if over_bytes:
            raise AlexandriaError("collection exceeded its total byte ceiling")
        if over_time:
            raise AlexandriaError("collection exceeded its elapsed-time ceiling")

    def _spent(self) -> bool:
        """Whether the run has passed `MAX_COLLECT_BYTES`, so no new shard may start."""
        with self._bytes_lock:
            return self._bytes > MAX_COLLECT_BYTES

    # -- one request ------------------------------------------------------

    def _ask(self, *args, **kwargs):
        self._worker_errors.receipts = []
        try:
            return self._ask_read(*args, **kwargs)
        except AlexandriaError as error:
            if self._worker_errors.receipts:
                error._collector_receipts = self._worker_errors.receipts
            raise
        finally:
            self._worker_errors.receipts = []

    def _flush_error(self, error):
        for args, kwargs in getattr(error, "_collector_receipts", []):
            self.record_error(*args, **kwargs)
        if hasattr(error, "_collector_receipts"):
            del error._collector_receipts

    def _ask_read(
        self, shard_index: int, name: str, method: str, params, *, identifier=None, label=None,
    ) -> tuple[bytes, bytes, object]:
        if identifier is None:
            identifier = request_identifier(shard_index, name)
        payload = request_bytes(identifier, method, params)
        # Opening reads use a virtual shard index past the last real one.
        draining = 0 <= shard_index < len(self.plan["shards"])
        self._spend(len(payload), draining=draining)
        if label is None:
            label = f"shard {shard_index} {name}"
        try:
            data = _rpc_request(self, payload, label)
        except AlexandriaError:
            self.record_error(shard_index, name, "transport")
            raise
        if len(data) > MAX_RAW_COMPONENT_BYTES:
            self.record_error(shard_index, name, "oversized-response", len(data))
            raise AlexandriaError(f"{label} exceeded the component byte ceiling")
        self._spend(len(data), draining=draining)
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
        if threading.get_ident() != self._coordinator:
            self._worker_errors.receipts.append(((shard_index, name, code, status), {"block": block}))
            return
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
            data = _rpc_request(self, payload, label)
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
            data = _rpc_request(self, payload, f"shard {shard_index} boundary re-read")
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
        self._coordinator = threading.get_ident()
        try:
            summary = self._collect()
        except BaseException as error:
            try:
                self._flush_error(error)
            finally:
                # A receipt-write refusal must also release every journal;
                # a close failure must not replace either refusal.
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
            if self._spent():
                raise AlexandriaError("collection exceeded its total byte ceiling")
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
        requests = list(shard_requests(self.plan, shard))
        independent = [request for request in requests if request[0] != "traces" or self._subjects is None]

        def fetch(request):
            name, method, params = request
            payload, data, result = self._ask(index, name, method, params)
            values = {name: (payload, data, result)}
            if name == "logs" and self._subjects is not None and "traces" in self.classes:
                values["traces"] = self._targeted_traces(index, result)
            return values

        answers = {}
        for _request, outcome in _read_batches(independent, fetch, self.rpc_concurrency):
            answers.update(outcome.result())
        for name, _method, _params in requests:
            payload, data, result = answers[name]
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
        `index` only ever advances by one and each advance waits on that
        exact shard's future, so a killed run's checkpoint always names a
        contiguous committed prefix with no gap -- the same resumability a
        strictly sequential loop gives, just fetched with real concurrency. A
        shard whose fetch finishes early still waits, uncommitted and only
        held in memory, until every lower-indexed shard is committed first.

        The window refills a slot as soon as any fetch settles, so a slow
        lowest shard no longer idles the others. At most `concurrency`
        fetches run at once and at most `concurrency` more wait settled, so
        held shards stay bounded at twice the concurrency. A failure stops
        refill; every shard below it still commits before it escapes. Past
        the byte ceiling no new shard starts, and the byte ceiling refuses
        only after every started shard has committed.
        """
        concurrency = min(self.concurrency, total - start)
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=concurrency)
        window = {}
        next_to_submit = start
        index = start
        try:
            while index < total:
                running = [future for future in window.values() if not future.done()]
                failed = any(future.done() and future.exception() is not None for future in window.values())
                if (
                    not failed and next_to_submit < total and len(running) < concurrency
                    and len(window) < 2 * concurrency and not self._spent()
                ):
                    window[next_to_submit] = pool.submit(self._fetch_shard, next_to_submit)
                    next_to_submit += 1
                elif not window:
                    raise AlexandriaError("collection exceeded its total byte ceiling")
                elif window[index].done():
                    self._write_shard(window.pop(index).result(), counts)
                    index += 1
                else:
                    concurrent.futures.wait(running, return_when=concurrent.futures.FIRST_COMPLETED)
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
        def ask(tx_hash):
            _, _, trace_result = self._ask(
                shard_index, "traces", "trace_transaction", [tx_hash],
                label=f"shard {shard_index} traces {tx_hash}",
            )
            if not isinstance(trace_result, list):
                raise AlexandriaError(
                    f"shard {shard_index} trace_transaction {tx_hash} did not return a list"
                )
            return [frame for frame in trace_result if _matches_subjects(frame, self._subjects)]

        for frames in _ordered_trace_results(
            hashes, ask, self.trace_concurrency, self._trace_slots,
        ):
            combined.extend(frames)
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
        def fetch_opening(item):
            item_position, read = item
            payload = opening_request(self.plan, item_position, read)
            held = self._held.get(item_position)
            if item_position < len(committed):
                return payload, None, None
            if held is not None and held[0] == payload:
                return held
            return self._ask(
                virtual, OPENING_CLASS, read["method"], read["params"],
                identifier=opening_identifier(virtual, item_position), label=opening_label(item_position, read),
            )

        def batches():
            reads = enumerate(phase.reads())
            for item in reads:
                batch = [item]
                # Immutable venues have independent header/code reads after
                # their dependent first-code probes have all been accepted.
                if plan_venue(self.plan).EPOCH_MODEL == "immutable-code" and item[1]["kind"] != "first-code-probe":
                    batch.extend(itertools.islice(reads, self.rpc_concurrency - 1))
                yield batch

        for batch in batches():
            for item, outcome in _read_batches(batch, fetch_opening, self.rpc_concurrency):
                position, read = item
                payload, data, result = outcome.result()
                if position < len(committed):
                    result = self._committed_opening(
                        committed[position], position, read, payload, opening_label(position, read)
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

    def __init__(
        self, plan, staging_root, transport, provider_class, *, registry=None,
        trace_concurrency=DEFAULT_TRACE_CONCURRENCY, concurrency=DEFAULT_COLLECT_CONCURRENCY,
        rpc_concurrency=DEFAULT_RPC_CONCURRENCY,
    ) -> None:
        validate_plan(plan)
        self.trace_concurrency = _trace_concurrency(trace_concurrency)
        self._trace_slots = threading.BoundedSemaphore(self.trace_concurrency)
        self.rpc_concurrency = _rpc_concurrency(rpc_concurrency)
        self._rpc_slots = threading.BoundedSemaphore(self.rpc_concurrency)
        if not isinstance(concurrency, int) or isinstance(concurrency, bool) or not 1 <= concurrency <= MAX_COLLECT_CONCURRENCY:
            raise AlexandriaError(f"reconcile concurrency must be a whole number from 1 to {MAX_COLLECT_CONCURRENCY}")
        self.concurrency = concurrency
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

    def _read_journals(self) -> tuple:
        """Read every physical journal once, for its digest and for what it staged.

        Returns the digest binding `_staged_journal_bindings` gives, the
        primary's responses keyed by shard and class, every staged log record
        in journal order, and the opening reads' entries. Each journal used to
        be read once for its digest and again for its entries, and the log
        journals a third time for the opening replay; one read now serves all
        of them, so the entries compared are the bytes the digest binds.
        """
        journals, staged, log_records, opening = {}, {}, [], []
        for name in self.staging.classes:
            for journal in self.staging.physical_journals(name):
                data = read_confined_file(
                    self.staging.journals, f"{journal}.jsonl", f"committed journal {journal}",
                    max_bytes=MAX_JOURNAL_BYTES,
                )
                journals[journal] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                for entry in journal_entries(journal, data):
                    if name == OPENING_CLASS:
                        opening.append(entry)
                        continue
                    envelope = load_bytes(
                        entry["response"].encode(), f"staged {name} response",
                        max_bytes=MAX_RAW_COMPONENT_BYTES,
                    )
                    staged[(entry["shard"], name)] = envelope.get("result")
                    if name == "logs" and isinstance(envelope.get("result"), list):
                        log_records.extend(envelope["result"])
        return dict(sorted(journals.items())), staged, log_records, opening

    def _second(self, shard_index: int, name: str, method: str, params):
        identifier = request_identifier(shard_index, name)
        payload = request_bytes(identifier, method, params)
        return self._second_raw(payload, identifier, f"shard {shard_index} {name}")

    def _second_raw(self, payload: bytes, identifier: int, label: str):
        """Ask the second provider the exact bytes the primary was asked."""
        data = _rpc_request(self, payload, f"{label} second provider")
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
        def ask(tx_hash):
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
            return [frame for frame in result if _matches_subjects(frame, self._subjects)]

        for frames in _ordered_trace_results(
            hashes, ask, self.trace_concurrency, self._trace_slots,
        ):
            combined.extend(frames)
        identifier = request_identifier(shard_index, "traces")
        combined_bytes = canonical_bytes({"id": identifier, "jsonrpc": "2.0", "result": combined})
        return combined, combined_bytes

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

    def _committed_input_digest(self, state: dict, *, journals=None) -> str:
        """Bind resumed comparisons to exact checkpoint and journal bytes."""
        if journals is None:
            journals = _staged_journal_bindings(self.staging)
        digest = hashlib.sha256(canonical_bytes(state))
        for name in sorted(journals):
            digest.update(canonical_bytes({"name": name, **journals[name]}))
        return digest.hexdigest()

    def _load_reconcile_checkpoint(self, boundary: str, input_digest: str):
        """This plan, second provider and committed tree's saved reconcile progress, or `None`.

        A checkpoint recorded for another plan, another `provider_class` or a
        staging tree whose committed boundary hash differs -- one rewound and
        collected again since the checkpoint was written -- proves nothing
        about this run: comparisons already counted under a different second
        opinion, or over bytes no longer in the tree, cannot be carried into
        this one, so it is treated as absent rather than trusted. So is a
        checkpoint in an earlier format.
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
            or document.get("staging_last_accepted") != boundary
            or document.get("staging_sha256") != input_digest
        ):
            return None
        required = {"compared", "matched", "disputed", "statuses", "next_shard"}
        if set(document) != required | {
            "format", "plan_sha256", "provider_class", "staging_last_accepted", "staging_sha256",
        }:
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

    def _save_reconcile_checkpoint(
        self, compared, matched, disputed, statuses, next_shard, boundary: str, input_digest: str,
    ) -> None:
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
            "staging_last_accepted": boundary,
            "staging_sha256": input_digest,
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

    def _fetch_shard(self, shard, staged):
        """Fetch independent second-provider classes without any durable write."""
        index = shard["index"]
        requests = {name: (method, params) for name, method, params in shard_requests(self.plan, shard)}
        names = ["boundary-blocks"]
        if "logs" in self.classes:
            names.append("logs")
        if "traces" in self.classes and self._subjects is not None:
            names.append("traces")

        def read(name):
            if name == "traces":
                logs = staged.get((index, "logs"))
                return self._second_traces(index, subject_transaction_hashes(logs) if isinstance(logs, list) else [])
            method, params = requests[name]
            return self._second(index, name, method, params)

        answers = {name: outcome for name, outcome in _read_batches(names, read, self.rpc_concurrency)}
        boundary, boundary_bytes = answers["boundary-blocks"].result()
        logs, logs_bytes = answers["logs"].result() if "logs" in answers else (None, b"")
        traces, traces_bytes = answers["traces"].result() if "traces" in answers else (None, b"")
        return boundary, boundary_bytes, logs, logs_bytes, traces, traces_bytes

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
        # The committed boundary this run reads. A reconcile checkpoint written
        # over a tree that was rewound and collected again names another one,
        # and its comparisons say nothing about the bytes now in the tree.
        last_accepted = state["last_accepted"]
        if not isinstance(last_accepted, dict) or not isinstance(last_accepted.get("block_hash"), str):
            raise AlexandriaError("the collected interval's checkpoint names no accepted boundary")
        staging_boundary = last_accepted["block_hash"]
        journals, staged, log_records, opening_entries = self._read_journals()
        self.journal_sha256 = {name: entry["sha256"] for name, entry in journals.items()}
        staging_digest = self._committed_input_digest(state, journals=journals)
        for index in range(len(shards)):
            for name in self.classes:
                if (index, name) not in staged:
                    raise AlexandriaError(
                        f"shard {index} has no staged {name} response to reconcile"
                    )
        phase, opening = replay_opening(
            self.plan, self.staging, self.classes, self.registry,
            log_records=log_records, entries=opening_entries,
        )
        # The address every shard read filters on, in the form the plan
        # declares it: one proxy, or the whole subject set.
        subjects = _plan_subjects(self.plan)
        upgrade_topic = phase.upgrade_topic

        checkpoint = self._load_reconcile_checkpoint(staging_boundary, staging_digest)
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
        fetched_shards = _read_batches(
            shards[start:], lambda shard: self._fetch_shard(shard, staged), self.concurrency,
        )
        for shard, fetched in fetched_shards:
            index = shard["index"]
            boundary = staged[(index, "boundary-blocks")]
            logs = staged.get((index, "logs"))
            counts[index] = self._counts(index, staged)
            status = "complete"
            compared_before, matched_before, disputed_before = compared, matched, len(disputed)
            try:
                (second_boundary, boundary_bytes, second_logs, logs_bytes,
                 second_traces, traces_bytes) = fetched.result()
                if isinstance(logs, list):
                    proxy_log_positions(logs, subjects, self.plan["interval"], upgrade_topic=upgrade_topic)
                if isinstance(second_logs, list):
                    proxy_log_positions(second_logs, subjects, self.plan["interval"], upgrade_topic=upgrade_topic)
            except AlexandriaError as exc:
                self._record_error(index, "second-provider", exc)
                self._save_reconcile_checkpoint(
                    compared, matched, disputed, statuses, index, staging_boundary, staging_digest,
                )
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
            self._save_reconcile_checkpoint(
                compared, matched, disputed, statuses, index + 1, staging_boundary, staging_digest,
            )
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
        opening_reads = (row for row in opening if row[1]["kind"] != "epoch-boundary-header")
        def fetch_opening(row):
            position, read, _value, payload = row
            return self._second_raw(payload, opening_identifier(virtual, position), opening_label(position, read))

        for row, outcome in _read_batches(opening_reads, fetch_opening, self.rpc_concurrency):
            position, read, value, payload = row
            opening_position += 1
            try:
                second, data = outcome.result()
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
        _check_staged_journal_bindings(self.staging, self.journal_sha256)
        document = {
            "format": RECONCILIATION_FORMAT,
            "journal_sha256": self.journal_sha256,
            "plan_sha256": plan_digest(self.plan),
            "reconciliation": record,
            "shards": table,
        }
        _atomic_json(self.directory / RECONCILIATION_RECORD, document)
        self.staging.close()
        return document



def _staged_journal_bindings(staging) -> dict:
    """Hash each bounded physical journal, including the opening reads."""
    result = {}
    for name in sorted(staging.journal_names):
        data = read_confined_file(
            staging.journals, f"{name}.jsonl", f"committed journal {name}",
            max_bytes=MAX_JOURNAL_BYTES,
        )
        result[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return result


def _reconciliation_bindings(document, names, label):
    """Accept the historical record or its complete journal digest map."""
    required = {"format", "plan_sha256", "reconciliation", "shards"}
    if (
        not isinstance(document, dict)
        or set(document) not in (required, required | {"journal_sha256"})
        or document["format"] != RECONCILIATION_FORMAT
    ):
        raise AlexandriaError(f"the {label} has an unknown shape")
    if "journal_sha256" not in document:
        return None
    bindings = document["journal_sha256"]
    if not isinstance(bindings, dict):
        raise AlexandriaError("the reconciliation journal digest binding is not an object")
    for name in sorted(names):
        digest = bindings.get(name)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise AlexandriaError(f"the reconciliation has no valid digest for journal {name}")
    if set(bindings) != set(names):
        raise AlexandriaError("the reconciliation binds a journal the plan does not declare")
    return bindings


def _check_staged_journal_bindings(staging, bindings) -> None:
    if bindings is not None:
        for name, entry in _staged_journal_bindings(staging).items():
            if entry["sha256"] != bindings[name]:
                raise AlexandriaError(f"the reconciliation digest differs for journal {name}")


def _check_released_journal_binding(name, records, bindings) -> None:
    if bindings is None:
        return
    digest = hashlib.sha256()
    for record in records:
        digest.update(canonical_bytes(record))
    if digest.hexdigest() != bindings[name]:
        raise AlexandriaError(f"the reconciliation digest differs for journal {name}")


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
        # A split plan's attribution parts, named from the plan the same way,
        # and the part documents `_epoch_receipt` writes for them.
        self.parts = attribution_parts(plan)
        self.part_documents = {}
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
        bindings = _reconciliation_bindings(
            document, self.staging.journal_names, "reconciliation record",
        )
        if document["plan_sha256"] != plan_digest(self.plan):
            raise AlexandriaError("the reconciliation record belongs to a different plan")
        validate_reconciliation(document["reconciliation"])
        validate_shard_coverage(document["shards"], self.plan["shards"], self.classes)
        _check_staged_journal_bindings(self.staging, bindings)
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
        record_path = self.root / RECONCILIATION_DIRECTORY / RECONCILIATION_RECORD
        reconciliation = self._reconciliation() if record_path.is_file() else None
        phase = self._opening(state)
        if reconciliation is None:
            reconciliation = self._reconciliation()
        shards = _receipt_shards(reconciliation["shards"])
        end_hash = shards[-1]["end_hash"]
        start_hash = phase.hashes[phase.start]
        epochs = self._epochs(phase, end_hash)
        self._validate_epoch_table(epochs, phase.start, phase.end)
        code = self._code_component(epochs, phase)
        code_bytes = canonical_bytes(code)
        # The parts come back here, not in the return value, because two demonstration
        # builders override `_epoch_receipt` with this signature.
        self.part_documents = {}
        receipt = self._epoch_receipt(phase, epochs, code_bytes, reconciliation, shards)
        if set(self.part_documents) != set(self.parts):
            raise AlexandriaError(
                f"the plan derives {len(self.parts)} {PART_CLASS} parts, but the interval "
                f"receipt was built with {len(self.part_documents)}"
            )
        documents = {
            "epoch-table": receipt,
            "error-receipts": {"format": "alexandria-interval-errors/v1", "records": self._errors()},
            CODE_COMPONENT: code,
            "interval-plan": self.plan,
            "reconciliation": reconciliation,
            "registry": self.registry,
        }
        # Empty unless the plan declares `log_attribution_parts`.
        documents.update(self.part_documents)
        for component, part in self.components.items():
            documents[component] = self._journal(part["class"], part["index"])
            _check_released_journal_binding(
                component, documents[component]["records"], reconciliation.get("journal_sha256"),
            )
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
                # Every journal component is already bounded by
                # MAX_JOURNAL_BYTES per physical file, and every raw
                # response any of them holds already passed load_raw_json's
                # own MAX_RESPONSE_NODES limit at collect time -- this is a
                # second, output-side bound on already-validated data, not
                # the place untrusted input gets its first check. A wide
                # real capture's epoch-table can legitimately carry one
                # log_attributions entry per preserved log (74,088 of them
                # for the full V2 interval, 2026-09-21), so this uses the
                # same larger ceiling MAX_RESPONSE_NODES already sets for
                # real provider data, not the tighter default meant for a
                # small control document like a plan or a registry.
                # A part carries its own bounds, so one above them refuses
                # under the part's name and shard range.
                attribution = self.parts.get(component)
                data = (
                    canonical_bytes(document, max_nodes=MAX_RESPONSE_NODES)
                    if attribution is None
                    else part_bytes(component, attribution, document)
                )
                (staging / relative).write_bytes(data)
                part = self.components.get(component, attribution)
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
            # Written under the manifest limits `ingest` reads it back under, so a
            # plan past either refuses here by name.
            (staging / "capture-plan.json").write_bytes(
                encode_manifest(plan_document, "capture plan")
            )
            return ingest(staging / "capture-plan.json", output)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def _validate_epoch_table(self, epochs, start, end):
        validate_epochs(epochs, start, end)

    def _epoch_receipt(self, phase, epochs, code_bytes, reconciliation, shards):
        """The interval receipt; under a split plan, also the parts that hold its rows.

        A plan without `log_attribution_parts` gets today's receipt, byte for
        byte, and no part. Under the split, the rows `attribute_logs` returned
        leave the receipt for one part per journal range, kept in
        `part_documents`, and the receipt becomes v4, listing each part's
        component, shard range and row count in order.
        """
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
        if self.parts:
            rows = attribution_part_rows(self.plan, self.parts, receipt.pop("log_attributions"))
            receipt["format"] = PARTS_RECEIPT_FORMAT
            receipt["log_attribution_parts"] = [
                {
                    "component": name, "first_shard": part["first"],
                    "last_shard": part["last"], "rows": len(rows[name]),
                }
                for name, part in self.parts.items()
            ]
            self.part_documents = {
                name: attribution_part(part, rows[name]) for name, part in self.parts.items()
            }
        return receipt

    def _capture(self, component: str, document, reconciliation, boundaries) -> dict:
        interval = self.plan["interval"]
        # A journal component is named `<class>` or `<class>.<k>`; its class
        # decides its role, its scope and its gaps, and its own name is the
        # capture it is filed under.
        part = self.components.get(component)
        journal = component if part is None else part["class"]
        # An attribution part is filed the same way under `log-attributions.<k>`.
        attribution = self.parts.get(component)
        if attribution is not None:
            journal = PART_CLASS
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
        elif attribution is not None:
            # One part's rows, counted under `/rows`. Its gap sentence below
            # says which shards and blocks they come from.
            record_count = len(document["rows"])
            collections = [{
                "name": PART_CLASS,
                "record_count": record_count,
                "selector": "/rows",
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
        if attribution is not None:
            gaps.append(attribution_part_gap(self.plan, attribution))
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
        PART_CLASS: "log-attributions",
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
        if component == "traces" and "subjects" in plan:
            gaps.append(TARGETED_TRACE_GAP)
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
    manifest = load_manifest(
        read_manifest_bytes(release_root, "manifest.json", "manifest"), "manifest",
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
    # One pass keys the manifest's components by name, so each lookup below is
    # one dictionary read rather than a scan of up to 16,384 entries.
    by_name = _components_by_name(manifest)
    plan_bytes = _component(release_root, by_name, "interval-plan")
    plan = load_bytes(plan_bytes, "component interval-plan", max_bytes=MAX_RAW_COMPONENT_BYTES)
    validate_plan(plan)
    venue = plan_venue(plan)
    classes = declared_classes(plan)
    # The journal components, and the shard range each one holds, come from
    # the plan and nothing else; the manifest's own list is compared with them,
    # never believed.
    journal_parts = journal_components(plan, classes)
    journal_names = tuple(journal_parts)
    # The attribution parts come from the plan the same way: empty unless it
    # declares `log_attribution_parts`, and never read off the manifest.
    parts = attribution_parts(plan)
    split = bool(parts)

    def named(name):
        return part_label(name, parts[name]) if name in parts else name

    recorded = None
    if split:
        # A split release is read only as the bytes `verify` accepted: the
        # manifest has to hash to the identity `verify` returned, and each
        # component below has to carry the size and digest it records. A
        # release without the split keeps today's reads.
        _require_verified_manifest(manifest, release_id)
        recorded = {item["name"]: item for item in manifest["components"]}
        _require_recorded_bytes("interval-plan", plan_bytes, recorded.get("interval-plan"))
    expected_components = set(FIXED_COMPONENTS) | set(journal_names) | set(parts)
    present = [item["name"] for item in manifest["components"]]
    for name in sorted(set(present) - expected_components):
        raise AlexandriaError(
            f"the release carries a {name} component the plan does not declare"
        )
    for name in sorted(expected_components - set(present)):
        raise AlexandriaError(f"the release lacks its {named(name)} component")
    documents = {}
    component_bytes = {}
    for name in sorted(expected_components):
        if name in parts:
            # Read once, compared with the verified manifest, then parsed
            # from those same bytes under the part bounds.
            label = named(name)
            if recorded[name]["bytes"] > MAX_PART_BYTES:
                raise AlexandriaError(
                    f"component {label} holds {recorded[name]['bytes']} bytes, above the "
                    f"{MAX_PART_BYTES}-byte component ceiling"
                )
            data = read_confined_file(
                release_root, recorded[name]["object_path"], f"release component {label}",
                max_bytes=MAX_PART_BYTES,
            )
            _require_recorded_bytes(label, data, recorded[name])
            documents[name] = load_bytes(
                data, f"component {label}", max_bytes=MAX_PART_BYTES, max_nodes=MAX_PART_NODES,
            )
            continue
        component_bytes[name] = _component(release_root, by_name, name)
        if split:
            _require_recorded_bytes(name, component_bytes[name], recorded[name])
        # max_nodes matches Builder.build's own write-side ceiling for these
        # same components: real data already built and digest-verified by
        # `verify` above, not fresh untrusted input, so the epoch-table's
        # one log_attributions entry per preserved log (74,088 of them for
        # the full V2 interval, 2026-09-21) reads back the same way it was
        # written rather than refusing under the tighter default meant for
        # a small control document.
        documents[name] = load_bytes(
            component_bytes[name], f"component {name}",
            max_bytes=MAX_RAW_COMPONENT_BYTES, max_nodes=MAX_RESPONSE_NODES,
        )

    interval = plan["interval"]
    start = int(interval["start"])
    end = int(interval["end"])

    receipt = documents["epoch-table"]
    legacy = isinstance(receipt, dict) and receipt.get("format") == LEGACY_RECEIPT_FORMAT
    divided = isinstance(receipt, dict) and receipt.get("format") == PARTS_RECEIPT_FORMAT
    required = {"epochs", "format", "implementation_code", "reconciliation", "shards"}
    if divided:
        required.add("log_attribution_parts")
    elif not legacy:
        required.add("log_attributions")
    # Keyed on the receipt's own format, so a receipt under the other kind of
    # plan still reaches the refusal below that names the mismatch.
    if isinstance(receipt, dict) and receipt.get("format") in (
        SUBJECT_RECEIPT_FORMAT, PARTS_RECEIPT_FORMAT,
    ):
        required.add("first_code")
    if not isinstance(receipt, dict) or set(receipt) != required or receipt["format"] not in (
        LEGACY_RECEIPT_FORMAT, RECEIPT_FORMAT, SUBJECT_RECEIPT_FORMAT, PARTS_RECEIPT_FORMAT,
    ):
        raise AlexandriaError("the interval receipt has an unknown shape")
    # A subject-set plan's receipt is the subject-row format and a
    # single-proxy plan's is not; either one under the other plan is a receipt
    # some other plan's build wrote.
    if ("subjects" in plan) != (receipt["format"] in (SUBJECT_RECEIPT_FORMAT, PARTS_RECEIPT_FORMAT)):
        raise AlexandriaError(
            "the interval receipt format does not match the plan's subject form"
        )
    # Receipt v4 lists the parts in place of the rows, so it belongs to a plan
    # that declares them and to no other.
    if split and not divided:
        raise AlexandriaError(
            f"the plan declares {PARTS_FIELD}, so its receipt must be {PARTS_RECEIPT_FORMAT}, "
            f"not {receipt['format']}"
        )
    if divided and not split:
        raise AlexandriaError(
            f"the interval receipt is {PARTS_RECEIPT_FORMAT}, but the plan declares no "
            f"{PARTS_FIELD}"
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
    if split:
        _check_attribution_parts(plan, parts, receipt, documents, subjects)
    elif not legacy:
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
    bindings = _reconciliation_bindings(
        reconciliation, journal_names, "reconciliation component",
    )
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
        raise AlexandriaError(f"the release carries no capture for its {named(name)} component")
    for name, part in parts.items():
        _check_part_capture(plan, name, part, captures[name], documents[name])
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
        if kind == "traces" and "subjects" in plan and TARGETED_TRACE_GAP not in gaps:
            raise AlexandriaError(f"the {name} coverage does not name the targeted trace gap")
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

    attributions = None if legacy else attribute_logs(
        phase.logs, _plan_subjects(plan), interval, derived_epochs,
        upgrade_topic=phase.upgrade_topic,
    )
    if split:
        # Each part against the rows derived for its own shards, sliced from
        # the one list the unchanged call returns.
        derived_rows = attribution_part_rows(plan, parts, attributions)
        for name, part in parts.items():
            if documents[name]["rows"] != derived_rows[name]:
                raise AlexandriaError(
                    f"component {named(name)} does not hold the rows attribute_logs derives "
                    "from the preserved logs of its shards"
                )
    elif not legacy and receipt["log_attributions"] != attributions:
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
    for name in journal_names:
        _check_released_journal_binding(name, documents[name]["records"], bindings)

    return {
        "receipt_semantics": (
            "v1-block-only" if legacy
            else "v4-subject-positional-parts" if divided
            else "v3-subject-positional" if receipt["format"] == SUBJECT_RECEIPT_FORMAT
            else "v2-positional"
        ),
        "epochs": len(epoch_entries),
        "implementations": implementations,
        "interval": {"end": interval["end"], "start": interval["start"]},
        "reconciliation": reconciliation["reconciliation"]["status"],
        "reconciliation_binding": {
            "status": "absent" if bindings is None else "verified",
            "gaps": [RECONCILIATION_BINDING_GAP] if bindings is None else [],
        },
        "release_id": release_id,
        "shard_statuses": {
            status: sum(1 for shard in shards if shard["status"] == status)
            for status in sorted({shard["status"] for shard in shards})
        },
    }


def _require_verified_manifest(manifest, release_id: str) -> None:
    """Refuse a manifest other than the one `verify` accepted.

    `verify` reads the manifest and every object, then `check` reads them
    again. The digests a split release is checked against come from this
    second read, so it has to hash to the identity `verify` returned; naming
    that identity in its own `release_id` field is not enough.
    """
    if isinstance(manifest, dict) and manifest.get("release_id") == release_id:
        identity = {key: value for key, value in manifest.items() if key != "release_id"}
        digest = hashlib.sha256(canonical_bytes(identity, max_nodes=MAX_MANIFEST_NODES))
        if "sha256:" + digest.hexdigest() == release_id:
            return
    raise AlexandriaError(
        "the manifest check read does not hash to the release identity verification "
        "accepted, so the release changed after it was verified"
    )


def _require_recorded_bytes(label: str, data: bytes, item) -> None:
    """Refuse component bytes other than the ones the verified manifest records."""
    if (
        not isinstance(item, dict)
        or len(data) != item.get("bytes")
        or "sha256:" + hashlib.sha256(data).hexdigest() != item.get("sha256")
    ):
        raise AlexandriaError(
            f"component {label} does not carry the size and SHA-256 the verified manifest "
            "records, so it changed after the release was verified"
        )


def _whole(value) -> bool:
    """A non-negative integer and not a boolean, since `True == 1` would pass for one."""
    return type(value) is int and value >= 0


def _check_attribution_parts(plan, parts, receipt, documents, subjects) -> None:
    """Hold a v4 receipt's part list and every part document to the plan's parts.

    The plan derives the parts. The receipt's list and each document are
    compared with that derivation and never believed: each has to name its
    own component, index and shard range, and hold valid rows inside its
    range's blocks, as many as the list counts. Whether the rows are the ones
    the preserved logs give is settled after the epochs are re-derived.
    """
    listing = receipt["log_attribution_parts"]
    if not isinstance(listing, list):
        raise AlexandriaError("the interval receipt's log_attribution_parts is not a list")
    ordered = list(parts.items())
    for position in range(len(ordered), len(listing)):
        entry = listing[position]
        extra = entry.get("component") if isinstance(entry, dict) else None
        raise AlexandriaError(
            f"the interval receipt lists {str(extra)[:64]} at position {position}, beyond the "
            f"{len(ordered)} {PART_CLASS} parts the plan derives"
        )
    for position, (name, part) in enumerate(ordered):
        label = part_label(name, part)
        if position >= len(listing):
            raise AlexandriaError(f"the interval receipt does not list {label}")
        entry = listing[position]
        if not isinstance(entry, dict) or set(entry) != {
            "component", "first_shard", "last_shard", "rows",
        }:
            raise AlexandriaError(f"the interval receipt's entry for {label} has an unknown shape")
        if entry["component"] != name:
            raise AlexandriaError(
                f"the interval receipt lists {str(entry['component'])[:64]} at position "
                f"{position}, where the plan derives {label}"
            )
        if (
            not _whole(entry["first_shard"]) or not _whole(entry["last_shard"])
            or (entry["first_shard"], entry["last_shard"]) != (part["first"], part["last"])
        ):
            raise AlexandriaError(
                f"the interval receipt names another shard range for {label}"
            )
        if not _whole(entry["rows"]):
            raise AlexandriaError(f"the interval receipt's row count for {label} is not a count")
        document = documents[name]
        if (
            not isinstance(document, dict)
            or set(document) != {"first_shard", "format", "last_shard", "part", "rows"}
            or document["format"] != PART_FORMAT
        ):
            raise AlexandriaError(f"component {label} is not an {PART_FORMAT} document")
        if not _whole(document["part"]) or document["part"] != part["index"]:
            raise AlexandriaError(
                f"component {label} names itself part {str(document['part'])[:64]}, not "
                f"part {part['index']}"
            )
        if (
            not _whole(document["first_shard"]) or not _whole(document["last_shard"])
            or (document["first_shard"], document["last_shard"]) != (part["first"], part["last"])
        ):
            raise AlexandriaError(
                f"component {label} declares another shard range than the plan derives for it"
            )
        rows = document["rows"]
        if not isinstance(rows, list):
            raise AlexandriaError(f"component {label} carries no row list")
        if len(rows) != entry["rows"]:
            raise AlexandriaError(
                f"component {label} holds {len(rows)} rows, but the interval receipt counts "
                f"{entry['rows']}"
            )
        try:
            validate_attributions(rows, subjects=subjects)
        except AlexandriaError as error:
            raise AlexandriaError(f"component {label}: {error}") from error
        low, high = part_blocks(plan, part)
        for row in rows:
            block = int(row["block_number"])
            if not low <= block <= high:
                raise AlexandriaError(
                    f"component {label} holds a row at block {block}, outside its blocks "
                    f"{low} to {high}"
                )


def _check_part_capture(plan, name: str, part, capture, document) -> None:
    """A part's capture is the one the builder writes: derived, header-bound, counting `/rows`.

    The fields are compared with the ones the plan gives every part, and the
    coverage has to count the part's rows under `/rows` and name its shards
    and blocks in the sentence the plan derives. Every refusal names the part.
    """
    label = part_label(name, part)
    interval = plan["interval"]
    expected = {
        "chain": plan["chain"],
        "component": name,
        "evidence_class": "header-bound",
        "scope": {
            "deployment": plan["deployment"],
            "finality": "provider-reported",
            "interval": {"end": interval["end"], "kind": "block-range", "start": interval["start"]},
            "kind": "full-dataset",
        },
        "source": {
            "kind": "local-fixture",
            "locator_class": "local-fixture",
            "reference": f"derived offline from the collected interval, {name}",
        },
        "venue": plan["venue"],
    }
    for field, value in expected.items():
        if capture.get(field) != value:
            raise AlexandriaError(
                f"the {label} capture's {field} is not the one the plan gives every part"
            )
    coverage = capture["coverage"]
    if attribution_part_gap(plan, part) not in coverage["gaps"]:
        raise AlexandriaError(
            f"the {label} coverage does not name the shards and blocks the plan derives for it"
        )
    count = len(document["rows"])
    counted = {
        "collections": [{"name": PART_CLASS, "record_count": count, "selector": "/rows"}],
        "record_count": count,
        "status": "partial",
        "unsupported_collections": [],
    }
    if any(coverage.get(field) != value for field, value in counted.items()):
        raise AlexandriaError(
            f"the {label} coverage does not count its {count} rows under /rows as a partial part"
        )


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


def _components_by_name(manifest) -> dict:
    """Every manifest component entry, keyed by its name; a repeated name keeps each entry."""
    by_name = {}
    for item in manifest["components"]:
        by_name.setdefault(item["name"], []).append(item)
    return by_name


def _component(release_root: Path, by_name, name: str) -> bytes:
    matches = by_name.get(name, [])
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
    """Identify a trace frame and bind every field of its preserved content.

    The final digest includes action, result, error and location fields.
    JSON key order is ignored; every value and omitted field stays significant.
    Two providers must return the same content to record agreement.
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
        hashlib.sha256(canonical_bytes(record)).hexdigest(),
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
    reconcile.add_argument(
        "--concurrency", type=int, default=DEFAULT_COLLECT_CONCURRENCY,
        help=f"shards prefetched at once, from 1 to {MAX_COLLECT_CONCURRENCY}; comparisons commit in order",
    )
    for command in (collect, reconcile):
        command.add_argument(
            "--trace-concurrency", type=int, default=DEFAULT_TRACE_CONCURRENCY,
            help=(
                f"targeted trace requests in flight, from 1 to {MAX_TRACE_CONCURRENCY} "
                f"(default {DEFAULT_TRACE_CONCURRENCY}); 1 requests serially"
            ),
        )
        command.add_argument(
            "--rpc-concurrency", type=int, default=DEFAULT_RPC_CONCURRENCY,
            help=f"overall active RPC limit across all categories, from 1 to {MAX_RPC_CONCURRENCY} (default 8)",
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
                plan, args.staging, transport, args.provider_class, registry=registry,
                trace_concurrency=args.trace_concurrency, concurrency=args.concurrency,
                rpc_concurrency=args.rpc_concurrency,
            ).reconcile()
            sys.stdout.buffer.write(canonical_bytes(document))
            return 0
        args.staging.mkdir(parents=True, exist_ok=True)
        summary = Collector(
            plan, args.staging, transport, registry=registry, concurrency=args.concurrency,
            trace_concurrency=args.trace_concurrency, rpc_concurrency=args.rpc_concurrency,
        ).collect()
        sys.stdout.buffer.write(canonical_bytes(summary))
        return 0
    except (AlexandriaError, OSError) as error:
        print(f"usdc-interval: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
