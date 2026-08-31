"""Shard planning and resumable staging for a bounded chain interval.

The staging shape is the one the study's design record selected: one
append-only journal per evidence class, and a checkpoint that records each
journal's committed byte offset after those bytes are fsynced.  A process
killed between a record and its checkpoint leaves bytes no resumed run keeps,
because resume truncates every journal back to its recorded offset before it
returns the next shard.

Nothing here reaches a network.  The collector that does is built on top of
this module and supplies its own transport.
"""

from __future__ import annotations

import errno
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile

from .canonical import MAX_CONTROL_BYTES, canonical_bytes, load_bytes
from .errors import AlexandriaError


PLAN_FORMAT = "alexandria-interval-plan/v1"
CHECKPOINT_FORMAT = "alexandria-interval-checkpoint/v1"
RECEIPT_FORMAT = "alexandria-interval-receipt/v1"

EVIDENCE_CLASSES = ("boundary-blocks", "logs", "traces")
FINALITY_POLICIES = ("confirmations", "finalized", "safe")

# Operator bounds.  A shard is a request's block range, so its width is what a
# provider's result limit and this collector's byte ceiling have to survive; the
# shard count is what the release's 128-component ceiling and the checkpoint's
# rewrite cost have to survive.
MIN_SHARD_WIDTH = 1
MAX_SHARD_WIDTH = 50_000
MAX_SHARDS = 4_096
MAX_BLOCK = 2 ** 63 - 1
MAX_JOURNAL_BYTES = 64 * 1024 * 1024
# How far back a reorg can be walked before the collector refuses instead of
# guessing. Bounded because the checkpoint is working state, not a chain.
MAX_HISTORY = 16
MAX_PAGE_LIMIT = 100_000
MAX_TIMEOUT_SECONDS = 600

ADDRESS_RE = re.compile(r"^0x[0-9a-f]{40}$")
HASH_RE = re.compile(r"^0x[0-9a-f]{64}$")
CHAIN_RE = re.compile(r"^eip155:(0|[1-9][0-9]*)$")
WORD_RE = re.compile(r"^0x[0-9a-f]{64}$")
CODE_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")

JOURNAL_DIRECTORY = "journals"
CHECKPOINT_NAME = "checkpoint.json"

# The EIP-1967 implementation slot, and the ERC-1967 `Upgraded(address)` topic.
# Neither is computed here, because the standard library carries no keccak.
# Both are attested by the preserved Phase 0 capture in this repository: the
# slot is the exact `eth_getStorageAt` parameter in
# `examples/compound-v3-phase0-v0/input/corpus.json`, and the topic appears in
# the proxy runtime bytecode preserved at
# `examples/compound-v3-phase0-v0/input/responses/old-proxy-code.json`.
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
UPGRADED_TOPIC = "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"
ZERO_ADDRESS = "0x" + "0" * 40
MAX_EPOCHS = 256


def plan_shards(start: int, end: int, width: int) -> list[dict]:
    """Tile an inclusive block interval with ordered, non-overlapping shards."""
    for label, value in (("start", start), ("end", end), ("width", width)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise AlexandriaError(f"interval {label} must be an integer")
    if start < 0:
        raise AlexandriaError("interval start must not be negative")
    if end > MAX_BLOCK:
        raise AlexandriaError(f"interval end must not exceed {MAX_BLOCK}")
    if end < start:
        raise AlexandriaError("interval end must not precede its start")
    if width < MIN_SHARD_WIDTH:
        raise AlexandriaError(f"shard width must be at least {MIN_SHARD_WIDTH}")
    if width > MAX_SHARD_WIDTH:
        raise AlexandriaError(f"shard width must not exceed {MAX_SHARD_WIDTH}")
    total = end - start + 1
    count = (total + width - 1) // width
    if count > MAX_SHARDS:
        raise AlexandriaError(
            f"interval needs {count} shards, above the {MAX_SHARDS}-shard limit"
        )
    shards = []
    for index in range(count):
        shard_start = start + index * width
        shards.append({
            "end": min(shard_start + width - 1, end),
            "index": index,
            "start": shard_start,
        })
    return shards


def validate_plan(plan) -> None:
    """Check one closed `alexandria-interval-plan/v1` document."""
    required = {
        "chain", "deployment", "evidence_classes", "finality", "format",
        "interval", "provider", "proxy", "shard_width", "shards", "venue",
    }
    if not isinstance(plan, dict) or set(plan) != required:
        raise AlexandriaError("interval plan has an unknown shape")
    if plan["format"] != PLAN_FORMAT:
        raise AlexandriaError("interval plan format is not recognised")
    if not isinstance(plan["chain"], str) or CHAIN_RE.fullmatch(plan["chain"]) is None:
        raise AlexandriaError("interval plan chain is not an eip155 identifier")
    for field in ("deployment", "venue"):
        if not isinstance(plan[field], str) or NAME_RE.fullmatch(plan[field]) is None:
            raise AlexandriaError(f"interval plan {field} is not a name")
    if not isinstance(plan["proxy"], str) or ADDRESS_RE.fullmatch(plan["proxy"]) is None:
        raise AlexandriaError("interval plan proxy is not a lowercase address")
    if list(plan["evidence_classes"]) != list(EVIDENCE_CLASSES):
        raise AlexandriaError("interval plan evidence classes do not match this collector")

    interval = plan["interval"]
    if not isinstance(interval, dict) or set(interval) != {"end", "start"}:
        raise AlexandriaError("interval plan interval has an unknown shape")
    start = _decimal(interval["start"], "interval start")
    end = _decimal(interval["end"], "interval end")
    width = plan["shard_width"]
    expected = plan_shards(start, end, width if isinstance(width, int) else 0)
    if plan["shards"] != expected:
        raise AlexandriaError("interval plan shards do not tile its declared interval")

    finality = plan["finality"]
    if not isinstance(finality, dict):
        raise AlexandriaError("interval plan finality has an unknown shape")
    policy = finality.get("policy")
    if policy not in FINALITY_POLICIES:
        raise AlexandriaError("interval plan finality policy is not recognised")
    fields = {"block_hash", "block_number", "policy"}
    if policy == "confirmations":
        fields = fields | {"confirmations"}
    if set(finality) != fields:
        raise AlexandriaError("interval plan finality has an unknown shape")
    if policy == "confirmations":
        depth = finality["confirmations"]
        if not isinstance(depth, int) or isinstance(depth, bool) or depth < 1:
            raise AlexandriaError("interval plan confirmation depth must be a positive integer")
    provider = plan["provider"]
    if not isinstance(provider, dict) or set(provider) != {
        "class", "page_limit", "timeout_seconds",
    }:
        raise AlexandriaError("interval plan provider has an unknown shape")
    if not isinstance(provider["class"], str) or not 1 <= len(provider["class"]) <= 256:
        raise AlexandriaError("interval plan provider class is not a bounded name")
    if any(character in provider["class"] for character in ("://", "@")):
        raise AlexandriaError("interval plan provider class must not carry an endpoint")
    for field, ceiling in (("page_limit", MAX_PAGE_LIMIT), ("timeout_seconds", MAX_TIMEOUT_SECONDS)):
        value = provider[field]
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= ceiling:
            raise AlexandriaError(f"interval plan provider {field} is out of range")

    boundary = _decimal(finality["block_number"], "interval plan finality block")
    if boundary < end:
        raise AlexandriaError("interval plan end block is above its finality boundary")
    if (
        not isinstance(finality["block_hash"], str)
        or HASH_RE.fullmatch(finality["block_hash"]) is None
    ):
        raise AlexandriaError("interval plan finality block hash is not a 32-byte hash")


def validate_checkpoint(checkpoint, expected_digest: str, shard_count: int) -> None:
    """Check one closed `alexandria-interval-checkpoint/v1` document."""
    required = {
        "format", "history", "last_accepted", "next_shard", "offsets",
        "plan_sha256", "records",
    }
    if not isinstance(checkpoint, dict) or set(checkpoint) != required:
        raise AlexandriaError("interval checkpoint has an unknown shape")
    if checkpoint["format"] != CHECKPOINT_FORMAT:
        raise AlexandriaError("interval checkpoint format is not recognised")
    if checkpoint["plan_sha256"] != expected_digest:
        raise AlexandriaError("interval checkpoint belongs to a different plan")
    for field in ("next_shard", "records"):
        value = checkpoint[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise AlexandriaError(f"interval checkpoint {field} must be a non-negative integer")
    if checkpoint["next_shard"] > shard_count:
        raise AlexandriaError("interval checkpoint names a shard outside its plan")
    offsets = checkpoint["offsets"]
    if not isinstance(offsets, dict) or set(offsets) != set(EVIDENCE_CLASSES):
        raise AlexandriaError("interval checkpoint offsets do not cover every evidence class")
    for name, value in offsets.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise AlexandriaError(f"interval checkpoint offset for {name} is not a byte count")
    history = checkpoint["history"]
    if not isinstance(history, list) or len(history) > MAX_HISTORY:
        raise AlexandriaError(
            f"interval checkpoint history holds more than {MAX_HISTORY} entries"
        )
    previous = None
    for entry in history:
        if not isinstance(entry, dict) or set(entry) != {
            "block_hash", "block_number", "offsets", "records", "shard",
        }:
            raise AlexandriaError("interval checkpoint history entry has an unknown shape")
        shard = entry["shard"]
        if not isinstance(shard, int) or isinstance(shard, bool) or not 0 <= shard < shard_count:
            raise AlexandriaError("interval checkpoint history names a shard outside its plan")
        if previous is not None and shard <= previous:
            raise AlexandriaError("interval checkpoint history is not in ascending shard order")
        previous = shard
        _decimal(entry["block_number"], "interval checkpoint history block")
        if (
            not isinstance(entry["block_hash"], str)
            or HASH_RE.fullmatch(entry["block_hash"]) is None
        ):
            raise AlexandriaError("interval checkpoint history block hash is not a 32-byte hash")
        if not isinstance(entry["records"], int) or isinstance(entry["records"], bool) or entry["records"] < 0:
            raise AlexandriaError("interval checkpoint history record count is not a count")
        entry_offsets = entry["offsets"]
        if not isinstance(entry_offsets, dict) or set(entry_offsets) != set(EVIDENCE_CLASSES):
            raise AlexandriaError(
                "interval checkpoint history offsets do not cover every evidence class"
            )
        for name, value in entry_offsets.items():
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise AlexandriaError(
                    f"interval checkpoint history offset for {name} is not a byte count"
                )

    accepted = checkpoint["last_accepted"]
    if accepted is None:
        if checkpoint["next_shard"] != 0:
            raise AlexandriaError("interval checkpoint past shard zero must name its accepted block")
        if history:
            raise AlexandriaError("interval checkpoint at shard zero must carry no history")
        return
    if not isinstance(accepted, dict) or set(accepted) != {"block_hash", "block_number"}:
        raise AlexandriaError("interval checkpoint accepted block has an unknown shape")
    _decimal(accepted["block_number"], "interval checkpoint accepted block")
    if (
        not isinstance(accepted["block_hash"], str)
        or HASH_RE.fullmatch(accepted["block_hash"]) is None
    ):
        raise AlexandriaError("interval checkpoint accepted block hash is not a 32-byte hash")
    if not history or history[-1]["shard"] != checkpoint["next_shard"] - 1:
        raise AlexandriaError("interval checkpoint history does not end at its own boundary")
    if (
        history[-1]["block_hash"] != accepted["block_hash"]
        or history[-1]["offsets"] != checkpoint["offsets"]
        or history[-1]["records"] != checkpoint["records"]
    ):
        raise AlexandriaError("interval checkpoint history disagrees with its own boundary")


def plan_digest(plan) -> str:
    return hashlib.sha256(canonical_bytes(plan)).hexdigest()


def resolve_root(value) -> Path:
    """Resolve a staging root before anything is compared against it.

    A macOS temporary directory is reached through `/var/folders`, a symbolic
    link to `/private/var/folders`.  Comparing an unresolved path against a
    resolved root refuses a contained path, which is the fault the release
    statement's audit found in a sibling runner.
    """
    if not isinstance(value, (str, Path)) or not str(value):
        raise AlexandriaError("staging root must be a path")
    root = Path(value).absolute()
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise AlexandriaError(f"cannot resolve the staging root: {exc}") from exc
    if not resolved.is_dir():
        raise AlexandriaError("staging root must be a directory")
    return resolved


def contained(root: Path, candidate) -> Path:
    """Return the resolved candidate, refusing anything outside the resolved root."""
    resolved_root = resolve_root(root)
    path = Path(candidate)
    if not path.is_absolute():
        path = resolved_root / path
    try:
        resolved = path.resolve(strict=False)
    except OSError as exc:
        raise AlexandriaError(f"cannot resolve {candidate}: {exc}") from exc
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise AlexandriaError("path escapes the staging root") from exc
    return resolved


class Staging:
    """One append-only journal per evidence class, checkpointed by byte offset."""

    def __init__(self, root, plan) -> None:
        validate_plan(plan)
        self.plan = plan
        self.digest = plan_digest(plan)
        self.shard_count = len(plan["shards"])
        self.root = resolve_root(root)
        self.journals = self.root / JOURNAL_DIRECTORY
        try:
            self.journals.mkdir(exist_ok=True)
        except OSError as exc:
            raise AlexandriaError(f"cannot open the staging journal directory: {exc}") from exc
        if self.journals.is_symlink() or not self.journals.is_dir():
            raise AlexandriaError("staging journal directory is not a directory")
        self.checkpoint_path = self.root / CHECKPOINT_NAME
        self._handles: dict[str, object] = {}
        self._records = 0
        self._sizes: dict[str, int] = {}
        self._resumed = False
        self._history: list[dict] = []

    # -- journals ---------------------------------------------------------

    def _journal_path(self, name: str) -> Path:
        if name not in EVIDENCE_CLASSES:
            raise AlexandriaError(f"unknown evidence class {name!r}")
        return self.journals / f"{name}.jsonl"

    def _handle(self, name: str):
        if name not in self._handles:
            path = self._journal_path(name)
            flags = (
                os.O_WRONLY | os.O_CREAT | os.O_APPEND
                | getattr(os, "O_NOFOLLOW", 0)
            )
            try:
                descriptor = os.open(path, flags, 0o600)
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.EMLINK):
                    raise AlexandriaError(f"journal {name} must not be a symlink") from exc
                raise AlexandriaError(f"cannot open journal {name}: {exc}") from exc
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode):
                os.close(descriptor)
                raise AlexandriaError(f"journal {name} is not a regular file")
            self._handles[name] = os.fdopen(descriptor, "ab")
            self._sizes[name] = info.st_size
        return self._handles[name]

    def record(self, shard: int, name: str, request: bytes, response: bytes) -> None:
        """Append one preserved exchange to its class journal."""
        if not isinstance(shard, int) or isinstance(shard, bool) or not 0 <= shard < self.shard_count:
            raise AlexandriaError("staged shard index is outside the plan")
        if name not in EVIDENCE_CLASSES:
            raise AlexandriaError(f"unknown evidence class {name!r}")
        for label, data in (("request", request), ("response", response)):
            if not isinstance(data, bytes):
                raise AlexandriaError(f"staged {label} must be bytes")
        entry = {
            "class": name,
            "request": _text(request, "staged request"),
            "response": _text(response, "staged response"),
            "shard": shard,
        }
        data = canonical_bytes(entry)
        handle = self._handle(name)
        if self._sizes[name] + len(data) > MAX_JOURNAL_BYTES:
            raise AlexandriaError(
                f"journal {name} would exceed the {MAX_JOURNAL_BYTES}-byte limit"
            )
        handle.write(data)
        self._sizes[name] += len(data)
        self._records += 1

    def commit(self, shard: int, block_number: int, block_hash: str) -> dict:
        """Fsync every open journal, then replace the checkpoint atomically."""
        if not self._resumed:
            raise AlexandriaError("resume must establish the record baseline before a commit")
        if not isinstance(shard, int) or isinstance(shard, bool) or not 0 <= shard < self.shard_count:
            raise AlexandriaError("committed shard index is outside the plan")
        if not isinstance(block_hash, str) or HASH_RE.fullmatch(block_hash) is None:
            raise AlexandriaError("committed block hash is not a 32-byte hash")
        offsets = {}
        for name in EVIDENCE_CLASSES:
            handle = self._handles.get(name)
            if handle is None:
                path = self._journal_path(name)
                offsets[name] = path.stat().st_size if path.is_file() else 0
                continue
            handle.flush()
            os.fsync(handle.fileno())
            offsets[name] = handle.tell()
        number = str(_decimal(block_number, "committed block"))
        history = [entry for entry in self._history if entry["shard"] < shard]
        history.append({
            "block_hash": block_hash,
            "block_number": number,
            "offsets": offsets,
            "records": self._records,
            "shard": shard,
        })
        self._history = history[-MAX_HISTORY:]
        checkpoint = {
            "format": CHECKPOINT_FORMAT,
            "history": list(self._history),
            "last_accepted": {"block_hash": block_hash, "block_number": number},
            "next_shard": shard + 1,
            "offsets": offsets,
            "plan_sha256": self.digest,
            "records": self._records,
        }
        validate_checkpoint(checkpoint, self.digest, self.shard_count)
        _atomic_write(self.checkpoint_path, canonical_bytes(checkpoint))
        return checkpoint

    def resume(self) -> dict:
        """Truncate every journal to its committed offset and report where to continue."""
        self.close()
        if self.checkpoint_path.is_symlink():
            raise AlexandriaError("interval checkpoint must not be a symlink")
        if not self.checkpoint_path.exists():
            for name in EVIDENCE_CLASSES:
                path = self._journal_path(name)
                if path.is_file():
                    _truncate(path, 0)
            self._records = 0
            self._history = []
            self._resumed = True
            return {"history": [], "last_accepted": None, "next_shard": 0, "records": 0}
        if not self.checkpoint_path.is_file():
            raise AlexandriaError("interval checkpoint is not a regular file")
        data = _read_control(self.checkpoint_path, "interval checkpoint")
        checkpoint = load_bytes(data, "interval checkpoint")
        validate_checkpoint(checkpoint, self.digest, self.shard_count)
        for name in EVIDENCE_CLASSES:
            path = self._journal_path(name)
            offset = checkpoint["offsets"][name]
            size = path.stat().st_size if path.is_file() else 0
            if size < offset:
                raise AlexandriaError(f"journal {name} is shorter than its committed offset")
            if size != offset:
                _truncate(path, offset)
        self._records = checkpoint["records"]
        self._history = list(checkpoint["history"])
        self._resumed = True
        return {
            "history": list(checkpoint["history"]),
            "last_accepted": checkpoint["last_accepted"],
            "next_shard": checkpoint["next_shard"],
            "records": checkpoint["records"],
        }

    def rewind_to(self, shard: int) -> dict:
        """Drop every record above one remembered boundary and continue from it.

        The trail is bounded, so a reorg deeper than `MAX_HISTORY` accepted
        shards refuses here rather than being papered over: the collector would
        otherwise have to guess which of its journals is still on the chain it
        started from.
        """
        if not self._resumed:
            raise AlexandriaError("resume must establish the record baseline before a rewind")
        matches = [entry for entry in self._history if entry["shard"] == shard]
        if not matches:
            raise AlexandriaError(
                f"shard {shard} is not in the checkpoint's rewind history"
            )
        entry = matches[0]
        self.close()
        for name in EVIDENCE_CLASSES:
            path = self._journal_path(name)
            offset = entry["offsets"][name]
            size = path.stat().st_size if path.is_file() else 0
            if size < offset:
                raise AlexandriaError(f"journal {name} is shorter than its rewind offset")
            if size != offset:
                _truncate(path, offset)
        self._records = entry["records"]
        self._history = [item for item in self._history if item["shard"] <= shard]
        checkpoint = {
            "format": CHECKPOINT_FORMAT,
            "history": list(self._history),
            "last_accepted": {
                "block_hash": entry["block_hash"],
                "block_number": entry["block_number"],
            },
            "next_shard": shard + 1,
            "offsets": entry["offsets"],
            "plan_sha256": self.digest,
            "records": entry["records"],
        }
        validate_checkpoint(checkpoint, self.digest, self.shard_count)
        _atomic_write(self.checkpoint_path, canonical_bytes(checkpoint))
        return checkpoint

    def discard(self) -> dict:
        """Drop every record and every remembered boundary, back to shard zero."""
        if self.checkpoint_path.is_symlink():
            raise AlexandriaError("interval checkpoint must not be a symlink")
        self.close()
        for name in EVIDENCE_CLASSES:
            path = self._journal_path(name)
            if path.is_file():
                _truncate(path, 0)
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
        self._records = 0
        self._history = []
        self._resumed = True
        return {"history": [], "last_accepted": None, "next_shard": 0, "records": 0}

    def entries(self, name: str):
        """Yield the staged entries of one class, in the order they were kept."""
        path = self._journal_path(name)
        if not path.is_file():
            return
        for line in _read_journal(path).splitlines():
            if line:
                yield load_bytes(line + b"\n", f"journal {name} entry")

    def close(self) -> None:
        for handle in self._handles.values():
            handle.flush()
            handle.close()
        self._handles = {}
        self._sizes = {}

    def __enter__(self) -> "Staging":
        return self

    def __exit__(self, *_exception) -> bool:
        self.close()
        return False



def discover_epochs(
    *,
    chain: str,
    deployment: str,
    proxy: str,
    interval,
    upgrade_logs,
    slot_reads,
    code_reads,
    block_hashes,
) -> list[dict]:
    """Tile a declared interval with code-hash-bound implementation epochs.

    Every input is bytes somebody already preserved.  Nothing here reads a
    chain, and nothing infers an implementation it was not given: a boundary
    without its own slot read is refused rather than inheriting the epoch
    before or after it, because the pinned `CometExt.version()` returns the
    constant string `0` and cannot tell two implementations apart.
    """
    if not isinstance(chain, str) or CHAIN_RE.fullmatch(chain) is None:
        raise AlexandriaError("epoch chain is not an eip155 identifier")
    if not isinstance(deployment, str) or NAME_RE.fullmatch(deployment) is None:
        raise AlexandriaError("epoch deployment is not a name")
    proxy = _address(proxy, "epoch proxy")
    if not isinstance(interval, dict) or set(interval) != {"end", "start"}:
        raise AlexandriaError("epoch interval has an unknown shape")
    start = _decimal(interval["start"], "epoch interval start")
    end = _decimal(interval["end"], "epoch interval end")
    if end < start:
        raise AlexandriaError("epoch interval end must not precede its start")

    boundaries = [start]
    openings = {start: None}
    declared = {}
    previous = None
    if not isinstance(upgrade_logs, (list, tuple)):
        raise AlexandriaError("upgrade logs are not a list")
    if len(upgrade_logs) > MAX_EPOCHS:
        raise AlexandriaError(f"more than {MAX_EPOCHS} upgrade logs were supplied")
    for position, log in enumerate(upgrade_logs):
        block, opening, announced, announced_hash = _upgrade_log(log, proxy, position)
        if previous is not None and block <= previous:
            raise AlexandriaError("upgrade logs are not in ascending block order")
        previous = block
        if not start <= block <= end:
            raise AlexandriaError(
                f"upgrade log at block {block} falls outside the declared interval"
            )
        declared[block] = (announced, announced_hash)
        if block == start:
            openings[start] = opening
            continue
        boundaries.append(block)
        openings[block] = opening

    code_by_address = _normalised_code_reads(code_reads)
    epochs = []
    for position, boundary in enumerate(boundaries):
        closing = boundaries[position + 1] - 1 if position + 1 < len(boundaries) else end
        implementation = _implementation(slot_reads, boundary)
        opening_hash = _block_hash(block_hashes, boundary)
        if boundary in declared:
            announced, announced_hash = declared[boundary]
            if announced != implementation:
                raise AlexandriaError(
                    f"upgrade log at block {boundary} announces {announced} while the "
                    f"implementation slot read there holds {implementation}"
                )
            if announced_hash != opening_hash:
                raise AlexandriaError(
                    f"upgrade log at block {boundary} names a different block hash "
                    "than the preserved block"
                )
        code = _runtime_code(code_by_address, implementation)
        epochs.append({
            "chain": chain,
            "deployment": deployment,
            "end_block": str(closing),
            "end_hash": _block_hash(block_hashes, closing),
            "implementation": implementation,
            "implementation_code_sha256": hashlib.sha256(code).hexdigest(),
            "proxy": proxy,
            "start_block": str(boundary),
            "start_hash": opening_hash,
            "upgrade": openings[boundary],
        })

    validate_epochs(epochs, start, end)
    return epochs


def validate_epochs(epochs, start: int, end: int) -> None:
    """Check that an epoch table tiles its interval exactly, with no gap or overlap."""
    if not isinstance(epochs, list) or not epochs:
        raise AlexandriaError("epoch table is empty")
    if len(epochs) > MAX_EPOCHS:
        raise AlexandriaError(f"epoch table holds more than {MAX_EPOCHS} epochs")
    required = {
        "chain", "deployment", "end_block", "end_hash", "implementation",
        "implementation_code_sha256", "proxy", "start_block", "start_hash",
        "upgrade",
    }
    expected = start
    for epoch in epochs:
        if not isinstance(epoch, dict) or set(epoch) != required:
            raise AlexandriaError("epoch has an unknown shape")
        first = _decimal(epoch["start_block"], "epoch start block")
        last = _decimal(epoch["end_block"], "epoch end block")
        if last < first:
            raise AlexandriaError("epoch end block precedes its start block")
        if first != expected:
            raise AlexandriaError(
                f"epoch table leaves block {expected} uncovered"
                if first > expected
                else f"epoch table overlaps at block {first}"
            )
        for field in ("end_hash", "start_hash"):
            if not isinstance(epoch[field], str) or HASH_RE.fullmatch(epoch[field]) is None:
                raise AlexandriaError(f"epoch {field} is not a 32-byte hash")
        _address(epoch["implementation"], "epoch implementation")
        if (
            not isinstance(epoch["implementation_code_sha256"], str)
            or CODE_DIGEST_RE.fullmatch(epoch["implementation_code_sha256"]) is None
        ):
            raise AlexandriaError("epoch implementation code digest is not a SHA-256")
        upgrade = epoch["upgrade"]
        if upgrade is not None:
            if not isinstance(upgrade, dict) or set(upgrade) != {
                "block_number", "log_index", "transaction_hash",
            }:
                raise AlexandriaError("epoch upgrade coordinates have an unknown shape")
            if _decimal(upgrade["block_number"], "epoch upgrade block") != first:
                raise AlexandriaError("epoch upgrade block does not open its epoch")
        expected = last + 1
    if expected != end + 1:
        raise AlexandriaError(f"epoch table leaves block {expected} uncovered")


def _upgrade_log(log, proxy: str, position: int):
    if not isinstance(log, dict):
        raise AlexandriaError(f"upgrade log {position} is not an object")
    for field in ("address", "blockHash", "blockNumber", "logIndex", "topics", "transactionHash"):
        if field not in log:
            raise AlexandriaError(f"upgrade log {position} has no {field}")
    # ephoros: allow no telemetry here: `log` is a JSON-RPC event log a provider returned, and `address` is its emitting-contract field
    if _address(log["address"], f"upgrade log {position} emitting contract") != proxy:
        raise AlexandriaError(f"upgrade log {position} was not emitted by the proxy")
    topics = log["topics"]
    if not isinstance(topics, list) or len(topics) != 2:
        raise AlexandriaError(f"upgrade log {position} does not carry two topics")
    if not isinstance(topics[0], str) or topics[0].lower() != UPGRADED_TOPIC:
        raise AlexandriaError(f"upgrade log {position} is not an Upgraded(address) log")
    announced = _topic_address(topics[1], f"upgrade log {position} implementation topic")
    block = _quantity(log["blockNumber"], f"upgrade log {position} block number")
    opening = {
        "block_number": str(block),
        "log_index": _quantity(log["logIndex"], f"upgrade log {position} log index"),
        "transaction_hash": _hash(log["transactionHash"], f"upgrade log {position} transaction"),
    }
    return block, opening, announced, _hash(log["blockHash"], f"upgrade log {position} block hash")


def _implementation(slot_reads, block: int) -> str:
    if not isinstance(slot_reads, dict):
        raise AlexandriaError("implementation slot reads are not a mapping")
    word = slot_reads.get(str(block), slot_reads.get(block))
    if word is None:
        raise AlexandriaError(
            f"block {block} opens an epoch with no implementation slot read of its own"
        )
    if not isinstance(word, str) or WORD_RE.fullmatch(word.lower()) is None:
        raise AlexandriaError(f"implementation slot read at block {block} is not a 32-byte word")
    if word[2:26].strip("0") != "":
        raise AlexandriaError(
            f"implementation slot read at block {block} is not a left-padded address"
        )
    implementation = "0x" + word[-40:].lower()
    if implementation == ZERO_ADDRESS:
        raise AlexandriaError(f"implementation slot read at block {block} is the zero address")
    return implementation


def _normalised_code_reads(code_reads) -> dict:
    """Key runtime code by lowercase address, so a checksummed key still resolves."""
    if not isinstance(code_reads, dict):
        raise AlexandriaError("runtime code reads are not a mapping")
    normalised = {}
    for key, value in code_reads.items():
        address = _address(key, "runtime code read key")
        if address in normalised and normalised[address] != value:
            raise AlexandriaError(
                f"runtime code reads hold two different bodies for {address}"
            )
        normalised[address] = value
    return normalised


def _topic_address(value, label: str) -> str:
    if not isinstance(value, str) or WORD_RE.fullmatch(value.lower()) is None:
        raise AlexandriaError(f"{label} is not a 32-byte word")
    if value[2:26].strip("0") != "":
        raise AlexandriaError(f"{label} is not a left-padded address")
    return "0x" + value[-40:].lower()


def _runtime_code(code_reads, implementation: str) -> bytes:
    if not isinstance(code_reads, dict):
        raise AlexandriaError("runtime code reads are not a mapping")
    value = code_reads.get(implementation)
    if value is None:
        raise AlexandriaError(f"implementation {implementation} has no runtime code read")
    if not isinstance(value, str) or not value.startswith("0x") or len(value) % 2:
        raise AlexandriaError(f"implementation {implementation} runtime code is not hexadecimal")
    body = value[2:]
    if not body:
        raise AlexandriaError(f"implementation {implementation} has empty runtime code")
    try:
        return bytes.fromhex(body)
    except ValueError as exc:
        raise AlexandriaError(
            f"implementation {implementation} runtime code is not hexadecimal"
        ) from exc


def _block_hash(block_hashes, block: int) -> str:
    if not isinstance(block_hashes, dict):
        raise AlexandriaError("block hashes are not a mapping")
    value = block_hashes.get(str(block), block_hashes.get(block))
    if value is None:
        raise AlexandriaError(f"block {block} has no preserved block hash")
    return _hash(value, f"block {block} hash")


def _address(value, label: str) -> str:
    if not isinstance(value, str) or ADDRESS_RE.fullmatch(value.lower()) is None:
        raise AlexandriaError(f"{label} is not a 20-byte address")
    return value.lower()


def _hash(value, label: str) -> str:
    if not isinstance(value, str) or HASH_RE.fullmatch(value.lower()) is None:
        raise AlexandriaError(f"{label} is not a 32-byte hash")
    return value.lower()


def _quantity(value, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, str) or not value.startswith("0x"):
        raise AlexandriaError(f"{label} is not a hexadecimal quantity")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise AlexandriaError(f"{label} is not a hexadecimal quantity") from exc



RECONCILIATION_STATUSES = ("agreed", "disputed", "unreconciled")
SHARD_STATUSES = ("complete", "partial", "failed")
DISPUTE_KINDS = ("boundary-hash", "log-identity", "transaction-order")
MAX_DISPUTES = 1_024


def log_identity(record) -> str:
    """The tuple the harvest specification compares, rendered as one string.

    `(blockHash, transactionHash, logIndex, address, topics, data)`. Nothing is
    normalised beyond case, because two providers disagreeing about the case of
    a hash is not a disagreement about the chain.
    """
    if not isinstance(record, dict):
        raise AlexandriaError("a log record is not an object")
    fields = []
    for name in ("blockHash", "transactionHash", "logIndex", "address"):
        value = record.get(name)
        if not isinstance(value, str) or not value:
            raise AlexandriaError(f"a log record has no {name}")
        fields.append(value.lower())
    topics = record.get("topics")
    if not isinstance(topics, list) or any(not isinstance(item, str) for item in topics):
        raise AlexandriaError("a log record has no topic list")
    fields.append(",".join(topic.lower() for topic in topics))
    data = record.get("data")
    if not isinstance(data, str):
        raise AlexandriaError("a log record has no data")
    fields.append(data.lower())
    return "|".join(fields)


def validate_shard_coverage(shards, plan_shards) -> None:
    """Check one shard-status table against the plan it claims to cover."""
    if not isinstance(shards, list) or len(shards) != len(plan_shards):
        raise AlexandriaError("the shard table does not cover every planned shard")
    for entry, planned in zip(shards, plan_shards):
        if not isinstance(entry, dict) or set(entry) != {
            "end", "end_hash", "index", "record_counts", "start", "status",
        }:
            raise AlexandriaError("a shard entry has an unknown shape")
        if (entry["index"], entry["start"], entry["end"]) != (
            planned["index"], planned["start"], planned["end"]
        ):
            raise AlexandriaError("a shard entry does not match its planned shard")
        if entry["status"] not in SHARD_STATUSES:
            raise AlexandriaError("a shard entry status is not recognised")
        if not isinstance(entry["end_hash"], str) or HASH_RE.fullmatch(entry["end_hash"]) is None:
            raise AlexandriaError("a shard entry end hash is not a 32-byte hash")
        counts = entry["record_counts"]
        if not isinstance(counts, dict) or set(counts) != set(EVIDENCE_CLASSES):
            raise AlexandriaError("a shard entry does not count every evidence class")
        for value in counts.values():
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise AlexandriaError("a shard entry record count is not a count")


def validate_reconciliation(reconciliation) -> None:
    """Check one closed reconciliation record."""
    if reconciliation is None:
        return
    if not isinstance(reconciliation, dict) or set(reconciliation) != {
        "compared", "disputed", "matched", "provider_class", "status",
    }:
        raise AlexandriaError("the reconciliation record has an unknown shape")
    if reconciliation["status"] not in RECONCILIATION_STATUSES:
        raise AlexandriaError("the reconciliation status is not recognised")
    provider = reconciliation["provider_class"]
    if not isinstance(provider, str) or not 1 <= len(provider) <= 256:
        raise AlexandriaError("the reconciliation provider class is not a bounded name")
    if any(character in provider for character in ("://", "@")):
        raise AlexandriaError("the reconciliation provider class must not carry an endpoint")
    for field in ("compared", "matched"):
        value = reconciliation[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise AlexandriaError(f"the reconciliation {field} count is not a count")
    if reconciliation["matched"] > reconciliation["compared"]:
        raise AlexandriaError("the reconciliation matched more identities than it compared")
    disputed = reconciliation["disputed"]
    if not isinstance(disputed, list) or len(disputed) > MAX_DISPUTES:
        raise AlexandriaError(f"the reconciliation records more than {MAX_DISPUTES} disputes")
    for entry in disputed:
        if not isinstance(entry, dict) or set(entry) != {"identity", "kind", "shard"}:
            raise AlexandriaError("a dispute entry has an unknown shape")
        if entry["kind"] not in DISPUTE_KINDS:
            raise AlexandriaError("a dispute kind is not recognised")
        if not isinstance(entry["shard"], int) or isinstance(entry["shard"], bool) or entry["shard"] < 0:
            raise AlexandriaError("a dispute entry names no shard")
        if not isinstance(entry["identity"], str) or not 1 <= len(entry["identity"]) <= 1024:
            raise AlexandriaError("a dispute identity is not a bounded string")
    if reconciliation["status"] == "agreed" and disputed:
        raise AlexandriaError("an agreed reconciliation cannot carry a dispute")
    if reconciliation["status"] == "disputed" and not disputed:
        raise AlexandriaError("a disputed reconciliation names no dispute")
    if reconciliation["status"] == "unreconciled" and reconciliation["compared"]:
        raise AlexandriaError("an unreconciled interval compared nothing")


def _text(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AlexandriaError(f"{label} is not UTF-8") from exc


def _decimal(value, label: str) -> int:
    if isinstance(value, bool):
        raise AlexandriaError(f"{label} is not a block number")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value):
        number = int(value)
    else:
        raise AlexandriaError(f"{label} is not a decimal block number")
    if not 0 <= number <= MAX_BLOCK:
        raise AlexandriaError(f"{label} is outside the supported block range")
    return number


def _atomic_write(path: Path, data: bytes) -> None:
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


def _truncate(path: Path, offset: int) -> None:
    flags = os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise AlexandriaError(f"{path.name} must not be a symlink") from exc
        raise AlexandriaError(f"cannot truncate {path.name}: {exc}") from exc
    try:
        os.ftruncate(descriptor, offset)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_control(path: Path, label: str) -> bytes:
    return _read_regular(path, label, MAX_CONTROL_BYTES)


def _read_journal(path: Path) -> bytes:
    return _read_regular(path, f"journal {path.name}", MAX_JOURNAL_BYTES)


def _read_regular(path: Path, label: str, maximum: int) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise AlexandriaError(f"{label} must not be a symlink") from exc
        raise AlexandriaError(f"cannot read {label}: {exc}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise AlexandriaError(f"{label} must name a regular file")
        if info.st_size > maximum:
            raise AlexandriaError(f"{label} exceeds the {maximum}-byte limit")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(maximum + 1)
    finally:
        os.close(descriptor)
    if len(data) > maximum:
        raise AlexandriaError(f"{label} exceeds the {maximum}-byte limit")
    return data


__all__ = [
    "CHECKPOINT_FORMAT",
    "IMPLEMENTATION_SLOT",
    "MAX_EPOCHS",
    "UPGRADED_TOPIC",
    "EVIDENCE_CLASSES",
    "FINALITY_POLICIES",
    "MAX_HISTORY",
    "MAX_SHARDS",
    "MAX_SHARD_WIDTH",
    "PLAN_FORMAT",
    "RECEIPT_FORMAT",
    "Staging",
    "contained",
    "discover_epochs",
    "plan_digest",
    "plan_shards",
    "resolve_root",
    "DISPUTE_KINDS",
    "RECONCILIATION_STATUSES",
    "SHARD_STATUSES",
    "log_identity",
    "validate_checkpoint",
    "validate_epochs",
    "validate_reconciliation",
    "validate_shard_coverage",
    "validate_plan",
]
