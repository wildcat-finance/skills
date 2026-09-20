"""The Wildcat V2 venue: pinned registry, per-subject epochs and declared gaps.

`validate_registry` is the unedited function `wildcat_registry.py` defines,
re-exported rather than wrapped, so the registry's pinned digest is written in
one module only.

The epoch model is `immutable-code`. No Wildcat V2 subject is an upgradeable
proxy, so each declared subject has exactly one epoch: it names no upgrade,
its implementation is the subject's own address, and its code digest is the
SHA-256 of the runtime code read at the epoch's first block. That block is
the later of the interval start and the subject's own deployment block, which
the registry carries.

A subject with no recorded creation block opens at the interval start when it
has runtime code there. Otherwise the interval end has to answer with code,
and a bisection finds an adjacent pair of blocks this collection read, empty
at one and with code at the next; the epoch opens at the second. That is an
observed boundary, not a recorded block and not the first creation: code
destroyed before the interval, or between two unread blocks, is not seen.
These reads come first, so the collector makes them before any shard.

This module therefore issues no storage read and
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
    MAX_JOURNAL_BYTES,
    OpeningRefusal,
    attribute_logs,
    proxy_log_positions,
    runtime_code,
    validate_epochs,
)
from ..wildcat_registry import subject_entries, validate_registry

VENUE = "wildcat-v2"
EPOCH_MODEL = "immutable-code"
# Empty until a collected interval is checked in under its own deployment name.
PRESERVED_DEPLOYMENTS = frozenset()
# `MarketDeployed(address,address,...)` as the HooksFactory emits it: the first
# topic of each of the 80 `MarketDeployed` events the merged estate record
# `docs/kickoff/1359/evidence/ethereum-mainnet-1590.json` preserves under
# `factory_events`. Topic two is the hooks template and topic three the market.
MARKET_DEPLOYED_TOPIC = "0x6f8c7c94fc16393d1ebec38de9899ba8c6bd860a025aa60063b7cf4c40a16c09"
# A capture's coverage holds at most 256 gap sentences, and four kinds of gap
# here grow with the subject set or with what the logs hold. Each kind lists
# this many by name and states the rest as one counted sentence, so the gaps
# this venue owes stay bounded whatever the plan declares.
LISTED_GAPS = 16
# What one journaled `eth_getCode` exchange adds beyond the code's own
# hexadecimal digits: the request, the envelope and the entry around them.
OPENING_ENTRY_OVERHEAD = 512
FIRST_CODE_PROBE = "first-code-probe"
OPENED_AT_START = "interval-start"
OPENED_AT_OBSERVED = "observed-block"
EMPTY_CODE = "empty"
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


def unrecorded_subjects(plan, registry) -> list:
    """The declared subjects whose registry entry records no creation block, in plan order."""
    subjects = _declared(plan, registry)
    entries = subject_entries(registry)
    return [subject for subject in subjects if entries[subject]["deployment_block"] is None]


def first_blocks(plan, registry, observed=None) -> dict:
    """Each declared subject's first in-interval block, in the plan's subject order.

    The later of the interval start and the recorded deployment block; a
    subject deployed after the interval end carries no key. A subject with no
    recorded block takes the block `observed` gives it, and no key without one.
    """
    subjects = _declared(plan, registry)
    entries = subject_entries(registry)
    start = int(plan["interval"]["start"])
    end = int(plan["interval"]["end"])
    observed = observed or {}
    blocks = {}
    for subject in subjects:
        deployed = entries[subject]["deployment_block"]
        if deployed is None:
            if subject in observed:
                blocks[subject] = observed[subject]
            continue
        first = max(start, deployed)
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

    First the probes that locate each unrecorded subject's first block
    (`preliminary_reads`), which need no shard. Then the interval's first
    header, one header per distinct later first block in ascending order, and
    each recorded subject's code at its first block in plan order. A probe's
    successor depends on its answer, so `accept` takes each read before the
    next is drawn. Nothing here touches a transport or a file.
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
        self.unrecorded = unrecorded_subjects(plan, registry)
        # Complete once every unrecorded subject's probes have been accepted.
        self.first_blocks = first_blocks(plan, registry)
        if not self.first_blocks and not self.unrecorded:
            raise AlexandriaError("no declared subject has an extent inside the interval")
        # Every code read lands in the one epoch-evidence journal, so a set
        # whose recorded code lengths cannot fit is refused at plan validation,
        # not after every shard. A probe may answer with the whole code.
        entries = subject_entries(registry)
        self.max_probes = max_probes(self.start, self.end)
        owed = sum(
            2 * entries[subject]["code_length"] + OPENING_ENTRY_OVERHEAD
            for subject in self.first_blocks
        ) + self.max_probes * sum(
            2 * entries[subject]["code_length"] + OPENING_ENTRY_OVERHEAD
            for subject in self.unrecorded
        )
        if owed > MAX_JOURNAL_BYTES:
            raise AlexandriaError(
                f"the {len(self.first_blocks) + len(self.unrecorded)} in-interval subjects' "
                f"runtime code needs about {owed} bytes of epoch-evidence journal, above the "
                f"{MAX_JOURNAL_BYTES}-byte journal limit; declare fewer subjects per plan"
            )
        self.logs = staged_logs
        proxy_log_positions(staged_logs, plan["subjects"], plan["interval"], upgrade_topic=None)
        self.hashes: dict[int, str] = {}
        self.codes: dict[str, str] = {}
        self.code_digests: dict[tuple[str, int], str] = {}
        # What each probe answered: "" for empty code, else the code as read.
        self.probes: dict[tuple[str, int], str] = {}
        self.first_code: dict[str, dict] = {}

    def _probe(self, subject: str, block: int) -> dict:
        return {
            "address": subject,
            "block": block,
            "kind": FIRST_CODE_PROBE,
            "method": "eth_getCode",
            "params": [subject, hex(block)],
        }

    def _has_code(self, subject: str, block: int) -> bool:
        if (subject, block) not in self.probes:
            raise AlexandriaError(
                f"the probe of subject {subject} at block {block} was not answered before the "
                "next opening read was drawn"
            )
        return bool(self.probes[(subject, block)])

    def _open(self, subject: str, empty_block, code_block: int) -> None:
        """Open one unrecorded subject's epoch at a block whose code this phase read."""
        code = self.probes[(subject, code_block)]
        self.first_blocks[subject] = code_block
        self.codes[subject] = code
        self.code_digests[(subject, code_block)] = hashlib.sha256(
            runtime_code(code, subject)
        ).hexdigest()
        self.first_code[subject] = {
            "code_block": str(code_block),
            "empty_block": None if empty_block is None else str(empty_block),
            "opening": OPENED_AT_START if empty_block is None else OPENED_AT_OBSERVED,
            "subject": subject,
        }

    def _locate(self, subject: str):
        """One unrecorded subject's probes, each drawn after the last is accepted.

        Code at the start opens the epoch there. Otherwise the end is read,
        `accept` refusing an empty one, and the range between a block read
        empty and a block read with code is halved until they are adjacent:
        both ends of the reported boundary are reads this phase accepted.
        """
        yield self._probe(subject, self.start)
        if self._has_code(subject, self.start):
            self._open(subject, None, self.start)
            return
        yield self._probe(subject, self.end)
        low, high = self.start, self.end
        if not self._has_code(subject, high):
            raise AlexandriaError(f"subject {subject} has no runtime code at the interval end")
        while high - low > 1:
            middle = (low + high) // 2
            yield self._probe(subject, middle)
            if self._has_code(subject, middle):
                high = middle
            else:
                low = middle
        self._open(subject, low, high)

    def preliminary_reads(self):
        """The reads that need no shard: the probes of every unrecorded subject, in plan order."""
        for subject in self.unrecorded:
            if subject not in self.first_code:
                yield from self._locate(subject)

    def reads(self):
        yield from self.preliminary_reads()
        yield _header_read(FIRST_BLOCK_HEADER, self.start)
        later = sorted({block for block in self.first_blocks.values() if block != self.start})
        for block in later:
            yield _header_read(SUBJECT_HEADER, block)
        for subject, block in self.first_blocks.items():
            if subject in self.first_code:
                # Its code was read by the probe that opened it.
                continue
            yield {
                "address": subject,
                "block": block,
                "kind": SUBJECT_CODE,
                "method": "eth_getCode",
                "params": [subject, hex(block)],
            }

    def first_code_rows(self) -> list:
        """How each unrecorded subject's epoch was opened, in ascending subject order."""
        missing = [subject for subject in self.unrecorded if subject not in self.first_code]
        if missing:
            raise AlexandriaError(
                f"subject {missing[0]} has no recorded creation block and its first block was "
                "not observed by the opening reads"
            )
        return [dict(self.first_code[subject]) for subject in sorted(self.first_code)]

    def accept(self, read, result) -> str:
        """Shape-check one answer and keep what it binds; returns the comparable value."""
        kind = read["kind"]
        block = read["block"]
        if kind == FIRST_CODE_PROBE:
            subject = read["address"]
            value = _probe_value(result, subject)
            if value is None:
                raise OpeningRefusal(
                    "code-not-hex", block,
                    f"the code read of subject {subject} at block {block} is not hexadecimal",
                )
            if value == EMPTY_CODE and block == self.end:
                raise OpeningRefusal(
                    "no-code-at-interval-end", block,
                    f"subject {subject} has no recorded creation block and no runtime code at "
                    f"the interval end, block {block}, so it has no extent inside the interval",
                )
            self.probes[(subject, block)] = "" if value == EMPTY_CODE else result.lower()
            return value
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
            if result == "0x":
                # A recorded block with no code is a wrong registry, never bisected.
                raise OpeningRefusal(
                    "no-code-at-recorded-block", block,
                    f"subject {read['address']} has no runtime code at block {block}, the first "
                    "block its recorded deployment gives it; the registry is wrong about it",
                )
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
        if kind == FIRST_CODE_PROBE:
            # Empty against code, or two differing codes, is a dispute.
            agreed = _probe_value(second, read["address"]) == value
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


def max_probes(start: int, end: int) -> int:
    """The most `eth_getCode` probes one unrecorded subject can need over an interval."""
    if end <= start:
        return 1
    # The two ends, then ceil(log2(n)) halvings between blocks n apart.
    return 2 + (end - start - 1).bit_length()


def _probe_value(result, subject: str):
    """`EMPTY_CODE`, the SHA-256 of the code a probe answered, or None when it is neither."""
    if result == "0x":
        return EMPTY_CODE
    try:
        return hashlib.sha256(runtime_code(result, subject)).hexdigest()
    except AlexandriaError:
        return None


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
    declared = None if plan is None or "subjects" not in plan else set(plan["subjects"])
    for entry in entries:
        if entry["deployment_block"] is None:
            # A subject the plan does not declare has no epoch to speak of.
            result.append(_missing_block_gap(
                entry["address"], opens=declared is None or entry["address"] in declared
            ))
    if plan is not None and "subjects" in plan:
        undeclared = len(entries) - len(set(plan["subjects"]) & set(subject_entries(registry)))
        if undeclared:
            result.append(
                f"{undeclared} of the {len(entries)} registry subjects were not declared by the "
                "plan, so nothing was requested for them"
            )
    return result


def _missing_block_gap(address: str, row=None, *, opens=True) -> str:
    """One unrecorded subject's gap; with `row`, which opening applied.

    The registry capture holds no opening read, so it owes the first clause
    and, for a subject the plan declares, the rule its epoch opens by; for one
    the plan does not declare it owes the first clause alone. An evidence
    scope says which opening applied, so an observed block is never read as a
    recorded one.
    """
    missing = (
        f"the merged records carry no creation block for subject {address}, so its deployment "
        "block is not established"
    )
    if not opens:
        return missing
    if row is None:
        return (
            f"{missing}; its epoch opens at the interval start when it has runtime code there "
            "and otherwise at the first block this collection observes code at"
        )
    if row["opening"] == OPENED_AT_START:
        return (
            f"{missing}; it has runtime code at the interval start, block {row['code_block']}, "
            "and its epoch opens there"
        )
    return (
        f"{missing}; this collection read no code for it at block {row['empty_block']} and "
        f"runtime code at block {row['code_block']}, and its epoch opens at that observed "
        "block, which is not a recorded deployment block"
    )


def _bounded(sentences: list, rest: str) -> list:
    """At most `LISTED_GAPS` named sentences, then one that counts the others."""
    if len(sentences) <= LISTED_GAPS:
        return sentences
    return sentences[:LISTED_GAPS] + [
        rest.format(rest=len(sentences) - LISTED_GAPS, total=len(sentences))
    ]


def evidence_gaps(plan, registry, logs, first_code=None) -> list[str]:
    """The venue's contribution to every evidence scope's declared gaps.

    `first_code` is the phase's `first_code_rows()`; a release always supplies
    it, and then every unrecorded declared subject has to have a row. Without
    it the sentence names neither opening.

    Bounded: a fixed number of sentences plus, for each of the four kinds that
    scale, `LISTED_GAPS` named ones and one count. `market_deploy_report` still
    names every member from the release's own components.
    """
    blocks = first_blocks(plan, registry)
    result = []
    if plan["deployment"] not in PRESERVED_DEPLOYMENTS:
        result.append(CONSTRUCTED_STAGING_GAP.format(deployment=plan["deployment"], venue=VENUE))
    rows = None if first_code is None else {row["subject"]: row for row in first_code}
    for address in unrecorded_subjects(plan, registry):
        if rows is None:
            result.append(_missing_block_gap(address))
        elif address not in rows:
            raise AlexandriaError(
                f"subject {address} has no recorded creation block and no opening read says "
                "where its epoch opened"
            )
        else:
            result.append(_missing_block_gap(address, rows[address]))
    entries = subject_entries(registry)
    result.extend(_bounded(
        [
            f"subject {subject} was deployed at block {entries[subject]['deployment_block']}, "
            "after the interval end, so it has no epoch and is outside the interval"
            for subject in plan["subjects"]
            if subject not in blocks and entries[subject]["deployment_block"] is not None
        ],
        "{rest} further declared subjects, {total} in all, were deployed after the interval end, "
        "have no epoch and are outside the interval; the plan and registry components name each",
    ))
    report = market_deploy_report(plan, registry, logs)
    if not report["compared"]:
        result.append(
            f"the HooksFactory {report['factory']} is not a declared subject, so no "
            "MarketDeployed log was requested and the declared markets were not compared"
        )
    result.extend(_bounded(
        [
            f"the registry declares market {address} deployed at block "
            f"{entries[address]['deployment_block']} inside the interval, but no preserved "
            "MarketDeployed log names it"
            for address in report["missing"]
        ],
        "{rest} further declared markets, {total} in all, were deployed inside the interval with "
        "no preserved MarketDeployed log; the registry and logs components name each",
    ))
    result.extend(_bounded(
        [
            f"a preserved MarketDeployed log at block {block} names market {address}, which the "
            f"registry declares deployed at block {declared}; its epoch start follows the registry"
            for address, block, declared in report["misplaced"]
        ],
        "{rest} further preserved MarketDeployed logs, {total} in all, name a declared market at "
        "another block than the registry records; the registry and logs components name each",
    ))
    result.extend(_bounded(
        [
            f"a preserved MarketDeployed log at block {block} names market {address}, which is "
            f"not one of the {report['declared']} markets the registry declares"
            for address, block in report["undeclared"]
        ],
        "{rest} further preserved MarketDeployed logs, {total} in all, name a market the registry "
        "does not declare; the logs components name each",
    ))
    return result
