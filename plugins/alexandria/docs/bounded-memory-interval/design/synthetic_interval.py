#!/usr/bin/env python3
"""Generate a deterministic Wildcat V2 split-plan staging tree, and optionally build it.

Run from anywhere; the repository is found from this file's location:

    python3 synthetic_interval.py --output <fresh directory> --shards <n> \
        --logs-per-shard <n> [--build] [--package <plugins/alexandria tree>]

Everything is derived from the arguments: the plan, every block hash, every
transaction hash, every log and trace frame and every subject's runtime code
comes from the seed and a position, and the subjects are the first
`--subjects` entries of the pinned V2 registry with a recorded deployment block
before the interval start. The staging tree is written by the real `Collector`
and `Reconciler` over a generating transport that answers from those
functions and never opens a socket, so its bytes are what a collection of such
a chain would stage. The deployment name is not one the venue admits as
preserved, so every release built from it declares the constructed-staging
gap.

`--package` names the `plugins/alexandria` tree whose collector and builder
run, for instance a `git archive` of the base commit; the repository's own
tree is the default. The registry always comes from the repository, whose
pinned digest both trees check.

Before any file is written, the planned release bytes are estimated from the
parameters and the free disk under the output's parent must be at least 2.5
times that, or the run refuses by name. The output directory must not exist;
the script creates it, writes only inside it, and removes it if the run fails.
On success it prints one JSON object naming the plan, the staging tree, the
release identifier (with `--build`) and the release's bytes; removing the tree
afterwards is the caller's job.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import threading

HERE = Path(__file__).resolve().parent
DEPLOYMENT = "wildcat-v2-synthetic-generator"
PROVIDER_CLASS = "synthetic generating transport, no endpoint"
SECOND_PROVIDER_CLASS = "second synthetic generating transport, no endpoint"
CREATED_AT = "2026-09-30T00:00:00Z"
DEFAULT_SEED = "fiat-1891"
DEFAULT_START = 26_000_000
DEFAULT_WIDTH = 1_000
DEFAULT_SUBJECTS = 32
DEFAULT_LOGS_PER_TRANSACTION = 4
FINALITY_DEPTH = 64
PAGE_LIMIT = 100_000
# A staged logs response is read back under the canonical reader's
# 200,000-node default, and a generated log is 13 nodes, so a shard holds at
# most this many logs.
MAX_LOGS_PER_SHARD = 15_000
# One generated log, as a logs journal, a logs component and an attribution
# row carry it, and one trace frame per transaction; measured on the
# generator's own output and rounded up, so the disk check errs towards
# refusing.
ESTIMATED_BYTES_PER_LOG = 1_050
ESTIMATED_BYTES_PER_TRANSACTION = 700
ESTIMATED_FIXED_BYTES = 8 * 1024 * 1024
DISK_HEADROOM = 2.5
EVENT_TOPIC = "0x" + hashlib.sha256(b"synthetic-interval-event").hexdigest()


class Refusal(Exception):
    pass


def repository_root() -> Path:
    """The checkout holding this script: the nearest ancestor carrying the Alexandria plugin."""
    for candidate in (HERE, *HERE.parents):
        if (candidate / "plugins/alexandria/scripts/usdc_interval.py").is_file():
            return candidate
    raise Refusal("no repository holding plugins/alexandria encloses this script")


def free_disk(path: Path) -> int:
    """Free bytes on the file system holding `path`."""
    return shutil.disk_usage(path).free


def digest(*parts) -> str:
    return "0x" + hashlib.sha256(":".join(str(part) for part in parts).encode()).hexdigest()


class Parameters:
    def __init__(self, *, shards, logs_per_shard, shard_width=DEFAULT_WIDTH,
                 logs_per_transaction=DEFAULT_LOGS_PER_TRANSACTION, subjects=DEFAULT_SUBJECTS,
                 seed=DEFAULT_SEED, start=DEFAULT_START):
        for name, value, low, high in (
            ("shards", shards, 1, 4_094), ("logs_per_shard", logs_per_shard, 1, MAX_LOGS_PER_SHARD),
            ("shard_width", shard_width, 1, 50_000),
            ("logs_per_transaction", logs_per_transaction, 1, 1_000),
            ("subjects", subjects, 1, 4_096), ("start", start, 1, 2 ** 40),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise Refusal(f"{name} must be a whole number from {low} to {high}")
        if not isinstance(seed, str) or not 1 <= len(seed) <= 64:
            raise Refusal("seed must be a name of 1 to 64 characters")
        self.shards = shards
        self.logs_per_shard = logs_per_shard
        self.shard_width = shard_width
        self.logs_per_transaction = logs_per_transaction
        self.subjects = subjects
        self.seed = seed
        self.start = start

    @property
    def end(self) -> int:
        return self.start + self.shards * self.shard_width - 1

    @property
    def transactions_per_shard(self) -> int:
        return -(-self.logs_per_shard // self.logs_per_transaction)

    def as_dict(self) -> dict:
        return {"logs_per_shard": self.logs_per_shard,
                "logs_per_transaction": self.logs_per_transaction, "seed": self.seed,
                "shard_width": self.shard_width, "shards": self.shards, "start": self.start,
                "subjects": self.subjects}

    def planned_bytes(self) -> int:
        """An upper estimate of the release's bytes, for the disk check."""
        return (ESTIMATED_FIXED_BYTES + self.shards * (
            self.logs_per_shard * ESTIMATED_BYTES_PER_LOG
            + self.transactions_per_shard * ESTIMATED_BYTES_PER_TRANSACTION))


class Chain:
    """The generated chain: every answer a pure function of the parameters and a position.

    A transaction hash ends with its shard and its number inside the shard, so
    a trace request finds its transaction without an index of every hash; its
    first eight bytes, the part a transaction key keeps, stay a digest.
    """

    def __init__(self, parameters: Parameters, subjects: list, plan: dict) -> None:
        self.p = parameters
        self.subjects = subjects
        self.plan = plan
        self._lock = threading.Lock()
        self._cache = {}

    def block_hash(self, number: int) -> str:
        return digest("synthetic-block", self.p.seed, number)

    def transaction_hash(self, shard: int, number: int) -> str:
        return digest("synthetic-tx", self.p.seed, shard, number)[:50] + f"{shard:08x}{number:08x}"

    def code(self, address: str) -> str:
        return "0x60806040" + digest("synthetic-code", self.p.seed, address)[2:]

    def shard_of(self, number: int):
        if not self.p.start <= number <= self.p.end:
            return None
        return (number - self.p.start) // self.p.shard_width

    def shard(self, index: int):
        """One shard's logs in position order, and each block's transaction hashes."""
        with self._lock:
            if index in self._cache:
                return self._cache[index]
        p = self.p
        first = p.start + index * p.shard_width
        count = p.transactions_per_shard
        logs, by_block, log_indexes = [], {}, {}
        emitted = index * p.logs_per_shard
        for tx in range(count):
            block = first + (tx * p.shard_width) // count
            hashes = by_block.setdefault(block, [])
            tx_hash = self.transaction_hash(index, tx)
            position = len(hashes)
            hashes.append(tx_hash)
            block_hash = self.block_hash(block)
            for offset in range(min(p.logs_per_transaction,
                                    p.logs_per_shard - tx * p.logs_per_transaction)):
                subject = self.subjects[emitted % len(self.subjects)]
                emitted += 1
                log_index = log_indexes.get(block, 0)
                log_indexes[block] = log_index + 1
                logs.append({
                    "address": subject,
                    "blockHash": block_hash,
                    "blockNumber": hex(block),
                    "data": digest("synthetic-data", p.seed, index, tx, offset)
                    + digest("synthetic-amount", p.seed, index, tx, offset)[2:],
                    "logIndex": hex(log_index),
                    "removed": False,
                    "topics": [EVENT_TOPIC, digest("synthetic-topic", p.seed, subject)],
                    "transactionHash": tx_hash,
                    "transactionIndex": hex(position),
                })
        value = (logs, by_block)
        with self._lock:
            if len(self._cache) >= 4:
                self._cache.pop(next(iter(self._cache)))
            self._cache[index] = value
        return value

    def header(self, number: int) -> dict:
        shard = self.shard_of(number)
        transactions = [] if shard is None else self.shard(shard)[1].get(number, [])
        return {"hash": self.block_hash(number), "number": hex(number),
                "transactions": list(transactions)}

    def trace(self, tx_hash: str) -> list:
        """One call frame into the subject that emitted the transaction's first log."""
        try:
            index, number = int(tx_hash[-16:-8], 16), int(tx_hash[-8:], 16)
        except ValueError:
            return []
        if not 0 <= index < self.p.shards or self.transaction_hash(index, number) != tx_hash:
            return []
        logs, _ = self.shard(index)
        position = number * self.p.logs_per_transaction
        if position >= len(logs):
            return []
        log = logs[position]
        return [{
            "action": {"callType": "call", "from": digest("synthetic-sender", self.p.seed)[:42],
                       "gas": "0x5208", "input": "0x90323177", "to": log["address"],
                       "value": "0x0"},
            "blockHash": log["blockHash"],
            "blockNumber": int(log["blockNumber"], 16),
            "result": {"gasUsed": "0x5208", "output": "0x"},
            "subtraces": 0,
            "traceAddress": [],
            "transactionHash": tx_hash,
            "transactionPosition": int(log["transactionIndex"], 16),
            "type": "call",
        }]


class GeneratingTransport:
    """Answers each JSON-RPC request from the generated chain; opens no socket."""

    def __init__(self, chain: Chain) -> None:
        self.chain = chain

    def request(self, payload, label, *, slots=None):
        envelope = json.loads(payload)
        method = envelope["method"]
        params = envelope["params"]
        chain = self.chain
        if method == "eth_syncing":
            result = False
        elif method == "eth_getBlockByNumber":
            tag = params[0]
            if tag in ("finalized", "safe"):
                number = int(chain.plan["finality"]["block_number"])
            else:
                number = int(tag, 16)
            result = chain.header(number)
        elif method == "eth_getLogs":
            shard = chain.shard_of(int(params[0]["toBlock"], 16))
            result = [] if shard is None else chain.shard(shard)[0]
        elif method == "trace_transaction":
            result = chain.trace(params[0])
        elif method == "eth_getCode":
            result = chain.code(params[0])
        else:
            raise Refusal(f"the generating transport answers no {method}")
        # A provider's bytes, sorted and compact, without the canonical
        # writer's node ceiling, which a page of logs passes.
        return json.dumps({"id": envelope["id"], "jsonrpc": "2.0", "result": result},
                          ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


class Package:
    """One `plugins/alexandria` tree's collector, reconciler and builder, imported once."""

    def __init__(self, root: Path) -> None:
        scripts = root / "scripts"
        if not (scripts / "usdc_interval.py").is_file():
            raise Refusal(f"{root} holds no scripts/usdc_interval.py")
        for name in [name for name in sys.modules
                     if name == "usdc_interval" or name.split(".")[0] == "alexandria_lib"]:
            del sys.modules[name]
        sys.path.insert(0, str(scripts))
        try:
            self.usdc_interval = importlib.import_module("usdc_interval")
            self.interval = importlib.import_module("alexandria_lib.interval")
            self.canonical = importlib.import_module("alexandria_lib.canonical")
            self.registry = importlib.import_module("alexandria_lib.wildcat_registry")
            self.errors = importlib.import_module("alexandria_lib.errors")
        finally:
            sys.path.remove(str(scripts))
        self.root = root


def subjects_for(registry: dict, parameters: Parameters) -> list:
    """The first registry subjects deployed at a recorded block before the interval."""
    chosen = [entry["address"] for entry in registry["entries"]
              if entry["deployment_block"] is not None
              and entry["deployment_block"] < parameters.start][:parameters.subjects]
    if len(chosen) < parameters.subjects:
        raise Refusal(f"the registry lists only {len(chosen)} subjects deployed before block "
                      f"{parameters.start}; asked for {parameters.subjects}")
    return chosen


def plan_for(package: Package, parameters: Parameters, subjects: list, chain_hash) -> dict:
    interval = package.interval
    boundary = parameters.end + FINALITY_DEPTH
    plan = {
        "chain": "eip155:1",
        "deployment": DEPLOYMENT,
        "evidence_classes": ["boundary-blocks", "logs", "traces"],
        "finality": {"block_hash": chain_hash(boundary), "block_number": str(boundary),
                     "policy": "finalized"},
        "format": "alexandria-interval-plan/v2",
        "interval": {"end": str(parameters.end), "start": str(parameters.start)},
        "provider": {"class": PROVIDER_CLASS, "page_limit": PAGE_LIMIT, "timeout_seconds": 25},
        "shard_width": parameters.shard_width,
        "shards": interval.plan_shards(parameters.start, parameters.end, parameters.shard_width),
        "subjects": subjects,
        "venue": "wildcat-v2",
        interval.SPLIT_FIELD: 1,
        interval.PARTS_FIELD: interval.PARTS_RULE,
    }
    interval.validate_plan(plan)
    return plan


def release_bytes(release: Path) -> int:
    return sum(path.stat().st_size for path in release.rglob("*")
               if path.is_file() and not path.is_symlink())


def generate(output: Path, parameters: Parameters, *, build: bool = False,
             package_root: Path | None = None) -> dict:
    """Write the staging tree (and, with `build`, the release) under a fresh `output`."""
    repository = repository_root()
    output = Path(output)
    if os.path.lexists(output):
        raise Refusal(f"{output} already exists; the generator writes only a fresh directory")
    parent = output.parent
    if not parent.is_dir():
        raise Refusal(f"{parent} is not a directory")
    planned = parameters.planned_bytes()
    free = free_disk(parent)
    if free < DISK_HEADROOM * planned:
        raise Refusal(
            f"the generator needs {DISK_HEADROOM} times its planned {planned} release bytes free, "
            f"{int(DISK_HEADROOM * planned)} bytes, and {parent} has {free}; refusing before any "
            "file is written")
    package = Package(Path(package_root) if package_root else repository / "plugins/alexandria")
    registry = json.loads(package.registry.registry_bytes(repository))
    subjects = subjects_for(registry, parameters)
    probe = Chain(parameters, subjects, {})
    plan = plan_for(package, parameters, subjects, probe.block_hash)
    chain = Chain(parameters, subjects, plan)
    usdc = package.usdc_interval
    output.mkdir()
    try:
        (output / "plan.json").write_bytes(package.canonical.canonical_bytes(plan))
        (output / "registry.json").write_bytes(package.canonical.canonical_bytes(registry))
        staging = output / "staging"
        staging.mkdir()
        with contextlib.redirect_stderr(open(os.devnull, "w")):
            while True:
                try:
                    usdc.Collector(plan, staging, GeneratingTransport(chain),
                                   registry=registry).collect()
                    break
                except package.errors.AlexandriaError as error:
                    # A run stops starting shards past its byte ceiling; a
                    # fresh run resumes from the checkpoint.
                    if "exceeded its total byte ceiling" not in str(error):
                        raise
            usdc.Reconciler(plan, staging, GeneratingTransport(Chain(parameters, subjects, plan)),
                            SECOND_PROVIDER_CLASS, registry=registry).reconcile()
        result = {"created_at": CREATED_AT, "parameters": parameters.as_dict(),
                  "planned_bytes": planned,
                  "plan": str(output / "plan.json"), "registry": str(output / "registry.json"),
                  "staging": str(staging)}
        if build:
            release = output / "release"
            result["release_id"] = usdc.Builder(plan, staging, registry,
                                                created_at=CREATED_AT).build(release)
            result["release"] = str(release)
            result["release_bytes"] = release_bytes(release)
        return result
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    value.add_argument("--output", required=True, type=Path)
    value.add_argument("--shards", required=True, type=int)
    value.add_argument("--logs-per-shard", required=True, type=int)
    value.add_argument("--shard-width", type=int, default=DEFAULT_WIDTH)
    value.add_argument("--logs-per-transaction", type=int, default=DEFAULT_LOGS_PER_TRANSACTION)
    value.add_argument("--subjects", type=int, default=DEFAULT_SUBJECTS)
    value.add_argument("--seed", default=DEFAULT_SEED)
    value.add_argument("--start", type=int, default=DEFAULT_START)
    value.add_argument("--package", type=Path,
                       help="the plugins/alexandria tree to collect and build with")
    value.add_argument("--build", action="store_true", help="also build the release")
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        parameters = Parameters(
            shards=args.shards, logs_per_shard=args.logs_per_shard, shard_width=args.shard_width,
            logs_per_transaction=args.logs_per_transaction, subjects=args.subjects,
            seed=args.seed, start=args.start)
        result = generate(args.output, parameters, build=args.build, package_root=args.package)
    except (Refusal, OSError) as refusal:
        print(f"synthetic-interval: {refusal}", file=sys.stderr)
        return 1
    except Exception as error:
        # The package's own refusals are AlexandriaError, from whichever tree
        # --package named; they are reported by name the same way.
        if type(error).__name__ != "AlexandriaError":
            raise
        print(f"synthetic-interval: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
