"""The Wildcat V2 venue: pinned registry, per-subject epochs and declared gaps.

`validate_registry` is the unedited function `wildcat_registry.py` defines,
re-exported rather than wrapped, so the registry's pinned digest is written in
one module only.

The epoch model is `immutable-code`. No Wildcat V2 subject is an upgradeable
proxy, so each declared subject has exactly one epoch: it names no upgrade,
its implementation is the subject's own address, and its code digest is the
SHA-256 of the runtime code read at the epoch's first block. That block is
the later of the interval start and the subject's own deployment block, which
the registry carries. This module therefore issues no storage read and
compares no log topic against an upgrade announcement: it passes
`upgrade_topic=None` to the shared log walk and never names the EIP-1967 slot
or the ERC-1967 topic.

`PRESERVED_DEPLOYMENTS` is the reviewed set of plan `deployment` names whose
staging this venue admits as collected from a chain. It is a constant here,
not a plan field, so no operator document can widen it. Every other
deployment name carries the constructed-staging gap on every evidence scope.
"""

from __future__ import annotations

import hashlib

from ..errors import AlexandriaError
from ..interval import (
    HASH_RE,
    MAX_BLOCK,
    OpeningRefusal,
    attribute_logs,
    proxy_log_positions,
    runtime_code,
    validate_epochs,
)
from ..wildcat_registry import NO_CREATION_BLOCK, subject_entries, validate_registry

VENUE = "wildcat-v2"
EPOCH_MODEL = "immutable-code"
# Empty until a collected interval is checked in under its own deployment name.
PRESERVED_DEPLOYMENTS = frozenset()
# `MarketDeployed(address,address,...)` as the HooksFactory emits it: the first
# topic of each of the 80 `MarketDeployed` events the merged estate record
# `docs/kickoff/1359/evidence/ethereum-mainnet-1590.json` preserves under
# `factory_events`. Topic two is the hooks template and topic three the market.
MARKET_DEPLOYED_TOPIC = "0x6f8c7c94fc16393d1ebec38de9899ba8c6bd860a025aa60063b7cf4c40a16c09"
FIRST_BLOCK_HEADER = "first-block-header"
SUBJECT_HEADER = "subject-first-block-header"
SUBJECT_CODE = "implementation-code"
CONSTRUCTED_STAGING_GAP = (
    "the {venue} venue does not admit deployment {deployment} as preserved, so these staging "
    "bytes are declared constructed rather than collected from a chain and this release is "
    "not preserved chain evidence"
)


def _declared(plan, registry) -> list:
    """The plan's subjects, each one a subject the validated registry lists."""
    if "subjects" not in plan:
        raise AlexandriaError(
            f"the {VENUE} venue captures a declared subject set; a single-proxy plan names none"
        )
    if registry is None:
        raise AlexandriaError(
            f"the {VENUE} venue derives each subject's first block from its deployment "
            "registry, and none was supplied"
        )
    validate_registry(registry)
    if plan["chain"] != f"eip155:{registry['chain_id']}":
        raise AlexandriaError(f"the plan's chain is not the chain the {VENUE} registry describes")
    entries = subject_entries(registry)
    for subject in plan["subjects"]:
        if subject not in entries:
            raise AlexandriaError(
                f"the plan declares subject {subject}, which the {VENUE} registry does not list"
            )
    return list(plan["subjects"])


def first_blocks(plan, registry) -> dict:
    """Each declared subject's first in-interval block, in the plan's subject order.

    The later of the interval start and the subject's deployment block. A
    subject with no recorded deployment block starts at the interval start. A
    subject deployed after the interval end has no in-interval extent and
    carries no key.
    """
    subjects = _declared(plan, registry)
    entries = subject_entries(registry)
    start = int(plan["interval"]["start"])
    end = int(plan["interval"]["end"])
    blocks = {}
    for subject in subjects:
        deployed = entries[subject]["deployment_block"]
        first = start if deployed is None else max(start, deployed)
        if first <= end:
            blocks[subject] = first
    return blocks


def derive_epochs(*, chain, deployment, interval, first_blocks, code_reads, block_hashes) -> dict:
    """One epoch per subject from preserved reads alone, keyed by subject.

    Nothing here reads a chain and nothing is inferred: a subject whose
    runtime code was not read, or whose first block's header was not, refuses
    rather than borrowing another subject's or another block's.
    """
    start = int(interval["start"])
    end = int(interval["end"])
    if not isinstance(first_blocks, dict) or not first_blocks:
        raise AlexandriaError("no declared subject has an extent inside the interval")
    if not isinstance(code_reads, dict) or not isinstance(block_hashes, dict):
        raise AlexandriaError("the preserved opening reads are not mappings")
    end_hash = block_hashes.get(end)
    if not isinstance(end_hash, str) or HASH_RE.fullmatch(end_hash) is None:
        raise AlexandriaError(f"block {end} has no preserved block hash")
    epochs = {}
    for subject, first in first_blocks.items():
        if isinstance(first, bool) or not isinstance(first, int) or not start <= first <= end:
            raise AlexandriaError(f"subject {subject} has a first block outside the interval")
        code = code_reads.get(subject)
        if code is None:
            raise AlexandriaError(
                f"subject {subject} opens an epoch at block {first} but its runtime code was "
                "not read, and no implementation is inferred for it"
            )
        start_hash = block_hashes.get(first)
        if not isinstance(start_hash, str) or HASH_RE.fullmatch(start_hash) is None:
            raise AlexandriaError(f"block {first} has no preserved block hash")
        epochs[subject] = [{
            "chain": chain,
            "deployment": deployment,
            "end_block": str(end),
            "end_hash": end_hash,
            "end_position": {
                "block_number": str(end + 1), "log_index": None, "transaction_index": None,
            },
            "implementation": subject,
            "implementation_code_sha256": hashlib.sha256(runtime_code(code, subject)).hexdigest(),
            "proxy": subject,
            "start_block": str(first),
            "start_hash": start_hash,
            "start_position": {
                "block_number": str(first), "log_index": None, "transaction_index": None,
            },
            "upgrade": None,
        }]
    validate_epochs(epochs, start, end)
    return epochs


class ImmutableCodeOpening:
    """The opening reads a Wildcat V2 plan owes, in the order they are made.

    The interval's first header, then one header per distinct later first
    block in ascending order, then each in-interval subject's runtime code at
    its own first block in the plan's subject order. Every read is known
    before any answer arrives. Nothing here touches a transport or a file.
    """

    upgrade_topic = None

    def __init__(self, plan, registry, staged_logs) -> None:
        self.plan = plan
        self.registry = registry
        self.virtual = len(plan["shards"])
        self.start = int(plan["interval"]["start"])
        self.end = int(plan["interval"]["end"])
        if self.end > MAX_BLOCK:
            raise AlexandriaError("the interval end is outside the supported range")
        self.first_blocks = first_blocks(plan, registry)
        if not self.first_blocks:
            raise AlexandriaError("no declared subject has an extent inside the interval")
        self.logs = staged_logs
        proxy_log_positions(staged_logs, plan["subjects"], plan["interval"], upgrade_topic=None)
        self.hashes: dict[int, str] = {}
        self.codes: dict[str, str] = {}
        self.code_digests: dict[tuple[str, int], str] = {}
        later = sorted({block for block in self.first_blocks.values() if block != self.start})
        self._reads = [_header_read(FIRST_BLOCK_HEADER, self.start)]
        self._reads.extend(_header_read(SUBJECT_HEADER, block) for block in later)
        self._reads.extend(
            {
                "address": subject,
                "block": block,
                "kind": SUBJECT_CODE,
                "method": "eth_getCode",
                "params": [subject, hex(block)],
            }
            for subject, block in self.first_blocks.items()
        )

    @property
    def total(self) -> int:
        return len(self._reads)

    def reads(self):
        yield from self._reads

    def accept(self, read, result) -> str:
        """Shape-check one answer and keep what it binds; returns the comparable value."""
        kind = read["kind"]
        block = read["block"]
        if kind in (FIRST_BLOCK_HEADER, SUBJECT_HEADER):
            if (
                not isinstance(result, dict)
                or not isinstance(result.get("hash"), str)
                or HASH_RE.fullmatch(result["hash"]) is None
            ):
                raise OpeningRefusal(
                    "malformed-header", block, f"the header read for block {block} carries no hash"
                )
            if _quantity(result.get("number")) != block:
                raise OpeningRefusal(
                    "malformed-header", block,
                    f"the header returned for block {block} carries another block number",
                )
            self.hashes[block] = result["hash"]
            return result["hash"]
        if kind == SUBJECT_CODE:
            try:
                code = runtime_code(result, read["address"])
            except AlexandriaError as error:
                raise OpeningRefusal("code-not-hex", block, str(error)) from error
            digest = hashlib.sha256(code).hexdigest()
            self.code_digests[(read["address"], block)] = digest
            self.codes[read["address"]] = result.lower()
            return digest
        raise AlexandriaError(f"unknown opening read kind {str(kind)[:64]!r}")

    def compare(self, read, value, second):
        """Whether a second provider's answer binds the same thing, its dispute kind and identity."""
        kind = read["kind"]
        block = read["block"]
        if kind in (FIRST_BLOCK_HEADER, SUBJECT_HEADER):
            agreed = (
                isinstance(second, dict)
                and second.get("hash") == value
                and _quantity(second.get("number")) == block
            )
            return agreed, "first-block-hash", f"block {block}"
        if kind == SUBJECT_CODE:
            try:
                agreed = hashlib.sha256(runtime_code(second, read["address"])).hexdigest() == value
            except AlexandriaError:
                agreed = False
            return agreed, "code-digest", f"code of {read['address']} at block {block}"
        raise AlexandriaError(f"opening read kind {str(kind)[:64]!r} is not compared")

    def epochs(self, end_hash: str) -> dict:
        """The subject-keyed epoch table the accepted reads derive, and nothing else."""
        hashes = dict(self.hashes)
        hashes[self.end] = end_hash
        epochs = derive_epochs(
            chain=self.plan["chain"],
            deployment=self.plan["deployment"],
            interval=self.plan["interval"],
            first_blocks=self.first_blocks,
            code_reads=self.codes,
            block_hashes=hashes,
        )
        attribute_logs(
            self.logs, self.plan["subjects"], self.plan["interval"], epochs, upgrade_topic=None
        )
        return epochs


def opening_phase(plan, registry, staged_logs) -> ImmutableCodeOpening:
    return ImmutableCodeOpening(plan, registry, staged_logs)


def _header_read(kind: str, block: int) -> dict:
    return {
        "block": block,
        "kind": kind,
        "method": "eth_getBlockByNumber",
        "params": [hex(block), False],
    }


def _quantity(value):
    """A hexadecimal quantity as an integer, or None when it is not one."""
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    try:
        return int(value, 16)
    except ValueError:
        return None


def market_deploy_report(plan, registry, logs) -> dict:
    """Compare the collected `MarketDeployed` logs with the registry's declared markets.

    `expected` is every declared market whose deployment block is inside the
    interval, `observed` every market a preserved HooksFactory
    `MarketDeployed` log names. `missing` and `undeclared` are the two ways
    the lists can disagree. `misplaced` is the third disagreement: a declared
    market that a preserved log deploys at another block than the registry
    records, whichever side of the interval the registry's block is on. Its
    epoch start came from the registry's block, so the release says so.
    `compared` is false when the factory is not a declared subject, because
    its logs were then never requested.
    """
    _declared(plan, registry)
    start = int(plan["interval"]["start"])
    end = int(plan["interval"]["end"])
    factory = next(e["address"] for e in registry["entries"] if e["role"] == "factory")
    markets = {e["address"]: e for e in registry["entries"] if e["role"] == "market"}
    expected = sorted(
        address for address, entry in markets.items()
        if start <= entry["deployment_block"] <= end
    )
    compared = factory in plan["subjects"]
    observed = {}
    blocks = {}
    if compared:
        # Each record is a JSON-RPC event log a provider returned; its
        # `address` field is the emitting contract, not telemetry.
        for record in logs:
            topics = record.get("topics") if isinstance(record, dict) else None
            emitter = record.get("address") if isinstance(record, dict) else None
            if (
                not isinstance(topics, list) or not topics
                or not isinstance(emitter, str)
                or emitter.lower() != factory
                or topics[0] != MARKET_DEPLOYED_TOPIC
            ):
                continue
            if len(topics) != 3 or not topics[2].startswith("0x" + "0" * 24):
                raise AlexandriaError(
                    "a preserved MarketDeployed log does not name its market in topic three"
                )
            market = "0x" + topics[2][26:]
            block = _quantity(record.get("blockNumber"))
            if block is None:
                raise AlexandriaError("a preserved MarketDeployed log carries no block number")
            observed.setdefault(market, block)
            blocks.setdefault(market, set()).add(block)
    return {
        "compared": compared,
        "declared": len(markets),
        "expected": expected,
        "factory": factory,
        "misplaced": sorted(
            (address, block, markets[address]["deployment_block"])
            for address, seen in blocks.items() if address in markets
            for block in seen if block != markets[address]["deployment_block"]
        ),
        "missing": sorted(set(expected) - set(observed)) if compared else [],
        "observed": sorted(observed),
        "undeclared": sorted(
            (address, block) for address, block in observed.items() if address not in markets
        ),
    }


def gaps(registry, plan=None) -> list[str]:
    """What the registry component does not establish."""
    entries = registry["entries"]
    private = sum(1 for entry in entries if entry["source_repository_private"])
    result = [
        f"the registry pins no source bytes; every one of its {len(entries)} subjects names a "
        f"source commit, {private} of them in a repository private to the organisation",
    ]
    for address in NO_CREATION_BLOCK:
        result.append(_missing_block_gap(address))
    if plan is not None and "subjects" in plan:
        undeclared = len(entries) - len(set(plan["subjects"]) & set(subject_entries(registry)))
        if undeclared:
            result.append(
                f"{undeclared} of the {len(entries)} registry subjects were not declared by the "
                "plan, so nothing was requested for them"
            )
    return result


def _missing_block_gap(address: str) -> str:
    return (
        f"the merged records carry no creation block for subject {address}; its epoch starts at "
        "the interval start and its deployment block is not established"
    )


def evidence_gaps(plan, registry, logs) -> list[str]:
    """The venue's contribution to every evidence scope's declared gaps."""
    blocks = first_blocks(plan, registry)
    result = []
    if plan["deployment"] not in PRESERVED_DEPLOYMENTS:
        result.append(CONSTRUCTED_STAGING_GAP.format(deployment=plan["deployment"], venue=VENUE))
    for address in NO_CREATION_BLOCK:
        if address in blocks:
            result.append(_missing_block_gap(address))
    entries = subject_entries(registry)
    for subject in plan["subjects"]:
        if subject not in blocks:
            result.append(
                f"subject {subject} was deployed at block {entries[subject]['deployment_block']}, "
                "after the interval end, so it has no epoch and is outside the interval"
            )
    report = market_deploy_report(plan, registry, logs)
    if not report["compared"]:
        result.append(
            f"the HooksFactory {report['factory']} is not a declared subject, so no "
            "MarketDeployed log was requested and the declared markets were not compared"
        )
    for address in report["missing"]:
        result.append(
            f"the registry declares market {address} deployed at block "
            f"{entries[address]['deployment_block']} inside the interval, but no preserved "
            "MarketDeployed log names it"
        )
    for address, block, declared in report["misplaced"]:
        result.append(
            f"a preserved MarketDeployed log at block {block} names market {address}, which the "
            f"registry declares deployed at block {declared}; its epoch start follows the registry"
        )
    for address, block in report["undeclared"]:
        result.append(
            f"a preserved MarketDeployed log at block {block} names market {address}, which is "
            f"not one of the {report['declared']} markets the registry declares"
        )
    return result
