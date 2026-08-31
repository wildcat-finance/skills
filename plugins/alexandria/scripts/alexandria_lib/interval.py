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
        "interval", "proxy", "shard_width", "shards", "venue",
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
    required = {"format", "last_accepted", "next_shard", "offsets", "plan_sha256", "records"}
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
    accepted = checkpoint["last_accepted"]
    if accepted is None:
        if checkpoint["next_shard"] != 0:
            raise AlexandriaError("interval checkpoint past shard zero must name its accepted block")
        return
    if not isinstance(accepted, dict) or set(accepted) != {"block_hash", "block_number"}:
        raise AlexandriaError("interval checkpoint accepted block has an unknown shape")
    _decimal(accepted["block_number"], "interval checkpoint accepted block")
    if (
        not isinstance(accepted["block_hash"], str)
        or HASH_RE.fullmatch(accepted["block_hash"]) is None
    ):
        raise AlexandriaError("interval checkpoint accepted block hash is not a 32-byte hash")


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
        checkpoint = {
            "format": CHECKPOINT_FORMAT,
            "last_accepted": {
                "block_hash": block_hash,
                "block_number": str(_decimal(block_number, "committed block")),
            },
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
            self._resumed = True
            return {"last_accepted": None, "next_shard": 0, "records": 0}
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
        self._resumed = True
        return {
            "last_accepted": checkpoint["last_accepted"],
            "next_shard": checkpoint["next_shard"],
            "records": checkpoint["records"],
        }

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
    previous = None
    if not isinstance(upgrade_logs, (list, tuple)):
        raise AlexandriaError("upgrade logs are not a list")
    if len(upgrade_logs) > MAX_EPOCHS:
        raise AlexandriaError(f"more than {MAX_EPOCHS} upgrade logs were supplied")
    for position, log in enumerate(upgrade_logs):
        block, opening = _upgrade_log(log, proxy, position)
        if previous is not None and block <= previous:
            raise AlexandriaError("upgrade logs are not in ascending block order")
        previous = block
        if not start <= block <= end:
            raise AlexandriaError(
                f"upgrade log at block {block} falls outside the declared interval"
            )
        if block == start:
            openings[start] = opening
            continue
        boundaries.append(block)
        openings[block] = opening

    epochs = []
    for position, boundary in enumerate(boundaries):
        closing = boundaries[position + 1] - 1 if position + 1 < len(boundaries) else end
        implementation = _implementation(slot_reads, boundary)
        code = _runtime_code(code_reads, implementation)
        epochs.append({
            "chain": chain,
            "deployment": deployment,
            "end_block": str(closing),
            "end_hash": _block_hash(block_hashes, closing),
            "implementation": implementation,
            "implementation_code_sha256": hashlib.sha256(code).hexdigest(),
            "proxy": proxy,
            "start_block": str(boundary),
            "start_hash": _block_hash(block_hashes, boundary),
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
    for field in ("address", "blockNumber", "logIndex", "topics", "transactionHash"):
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
    block = _quantity(log["blockNumber"], f"upgrade log {position} block number")
    return block, {
        "block_number": str(block),
        "log_index": _quantity(log["logIndex"], f"upgrade log {position} log index"),
        "transaction_hash": _hash(log["transactionHash"], f"upgrade log {position} transaction"),
    }


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
    "validate_checkpoint",
    "validate_epochs",
    "validate_plan",
]
