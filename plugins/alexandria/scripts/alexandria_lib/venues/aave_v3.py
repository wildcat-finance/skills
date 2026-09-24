"""The Aave V3 Ethereum main-market venue: pinned registry, plan scope and epochs.

`validate_registry` is the unedited function `aave_registry.py` defines,
re-exported rather than wrapped, so the registry's pinned digest,
`AAVE_V3_REGISTRY_SHA256`, and the pinned canonical bytes of the merged
`aave-v3` row, `ROW_PINS`, are each written in one module only. Both are
re-exported here by name. No plan field supplies either.

`validate_plan_scope` refuses a plan whose chain is not `eip155:1`, whose
registry is not the pinned one, which declares a subject the registry does
not list, or which does not declare the main market's Pool proxy and
AddressesProvider. The market addresses are the constant
`aave_registry.MARKET`, which `validate_registry` also holds the registry to.

The epoch model is keyed by registry role. A subject whose role is one of
`aave_registry.PROXY_ROLES` is an `InitializableImmutableAdminUpgradeabilityProxy`
and follows the EIP-1967 slot and its `Upgraded` positions; a subject whose
role is one of `IMMUTABLE_ROLES` has one epoch whose implementation is the
subject itself. `derive_epochs` builds that table from preserved reads alone,
under the rules `docs/usdc-interval-collector.md` states beside their pinned
source lines. `attribute_positions` passes `order_upgrade_transactions=True`
to the shared position walk, and `ORDER_UPGRADE_TRANSACTIONS` is what the
collector's reconcile, build and check paths read from this module to pass
the same value; no other venue module sets it.

`opening_phase` returns `SubjectProxyOpening`, the reads those epochs are
derived from, in a fixed order the staged logs determine: the plan's first
block header, a header at every later opening or upgrade block, the
implementation slot of every proxy at its opening block and at each block it
announces an upgrade in, then the runtime code of each subject and of each
implementation those slots hold, once per address at the first block an epoch
needs it.

`gaps` names the one subject #1591 lists both as a subject and as periphery,
so the release says so rather than resolving it silently. `evidence_gaps`
names, on every evidence scope, a constructed staging tree, the subjects
created before the plan's start and those created after its end, sixteen of
each kind by name and the rest in one counted sentence.
`POSITIONAL_VERIFICATION_LIMIT` is the sentence the collector adds to every
evidence scope of this venue and `check` refuses a release without: provider
agreement over logs excludes `transactionIndex`.

`PRESERVED_DEPLOYMENTS` is the reviewed set of plan `deployment` names whose
staging this venue admits as collected from a chain. It is empty: every
deployment name carries the constructed-staging gap until a production
collection admits its own.

`PRODUCTION_DEPLOYMENT` names the production capture, and
`SEGMENT_PLAN_SHA256` pins, in segment order, the SHA-256 of each plan in
`examples/aave-v3-interval-v0/segments.json`, taken over the plan's canonical
bytes as `plan_digest` computes them. `validate_plan_scope` refuses a plan
under that name whose digest is not pinned, so collect, reconcile, build and
check each refuse an edited or unlisted segment plan before any read. The pin
decides which plans may use the name; it admits nothing as preserved.
"""

from __future__ import annotations

import hashlib
import re

from ..aave_registry import (  # noqa: F401 -- re-exported pins, see the docstring
    AAVE_V3_REGISTRY_SHA256,
    EXPECTED_ROLE_COUNTS,
    MARKET,
    PROXY_ROLES,
    ROW_PINS,
    subject_entries,
    validate_registry,
)
from ..errors import AlexandriaError
from ..interval import (
    ADDRESS_RE,
    HASH_RE,
    IMPLEMENTATION_SLOT,
    MAX_BLOCK,
    MAX_EPOCHS,
    MAX_JOURNAL_BYTES,
    UPGRADED_TOPIC,
    WORD_RE,
    OpeningRefusal,
    attribute_logs,
    implementation_from_word,
    plan_digest,
    proxy_log_positions,
    runtime_code,
    slot_word_address,
    validate_epochs,
)

VENUE = "aave-v3"
EPOCH_MODEL = "aave-v3-role-keyed"
CHAIN = "eip155:1"
# Read by the collector's reconcile, build and check paths, which pass it to
# the shared position walk as `order_upgrade_transactions`.
ORDER_UPGRADE_TRANSACTIONS = True
PRESERVED_DEPLOYMENTS = frozenset()
PRODUCTION_DEPLOYMENT = "aave-v3-ethereum-main"
# One digest per segment plan, in segment order; see the module docstring.
SEGMENT_PLAN_SHA256 = (
    "6c98ac986f0d0aa6241b058ddb00a9adb43d08fc8bcbc1b6963d1f1d74c78951",
    "c08fa6d7636d3e89ce54e04dc0765efc66e5398e6b268fa82ba868a2f2d841a2",
    "581aae5d1732a43c5f60e6bb3837d791e07937832d421482cc7ce47d565f7d00",
    "b821fd6598bca42a2cc89e7d60f9c2eb8c1cae503b0d713a8ba451be4f4c58fd",
    "54877122df496d2161f21237b272c048c2f14d283994844f1b54bb25311d0f25",
    "77a41a2fa7badd98a8a92a975e53f8a848cb33317d86b07ad19e4bd409e71da4",
    "2d4e262cb61469ed8e4ebace212aac051325c53b7b2bd1ae39ff66922dcadd2e",
    "701090ecc2f23f908062c1c9dad54bca7b7ec3b5dd35c56949cc30dd071e13b7",
    "069e22e3e87b11ac95df3a46b511b90373e73e12a1cf27be90834c0bf6e981ee",
    "b46ee7ff3c9cafda06494c9bb95b2f52c8aaf5a96e143eaaff13d6f694ba6828",
    "2f264cfceb1255b741233dac3d3845684cec46ccd6594f622fe4ec15f953015b",
    "0739a6fdc2d1231aa122619767550d79c0db6d28a4aefacabc59af7b8703882c",
)
CONSTRUCTED_STAGING_GAP = (
    "the {venue} venue does not admit deployment {deployment} as preserved, so these staging "
    "bytes are declared constructed rather than collected from a chain and this release is "
    "not preserved chain evidence"
)
# Reconciliation compares each log by the tuple `log_identity` in
# `alexandria_lib/interval.py` builds, which leaves out `transactionIndex`.
POSITIONAL_VERIFICATION_LIMIT = (
    "provider agreement over logs excludes transactionIndex: reconciliation compares each "
    "log's blockHash, transactionHash, logIndex, address, topics and data, so an agreed "
    "reconciliation is not a claim that both providers placed a log at the same transaction "
    "position; the held transaction-index-reconciliation job owns that comparison"
)
# Each gap kind that grows with the subject set names this many subjects and
# counts the rest in one sentence, as the Wildcat V2 venue does.
LISTED_GAPS = 16
# What one journaled opening read adds beyond a code answer's own hexadecimal
# digits: the request, the envelope and the entry around them. The Wildcat V2
# venue measured the same figure for its `eth_getCode` entries.
OPENING_ENTRY_OVERHEAD = 512
# EIP-170's runtime code limit, the budget for an implementation the registry
# records no code length for.
MAX_RUNTIME_CODE_BYTES = 24_576
FIRST_BLOCK_HEADER = "first-block-header"
SUBJECT_HEADER = "subject-first-block-header"
BOUNDARY_HEADER = "epoch-boundary-header"
SLOT_READ = "implementation-slot"
CODE_READ = "implementation-code"

# The roles with one immutable epoch: every role the registry counts that is
# not a proxy role.
IMMUTABLE_ROLES = frozenset(EXPECTED_ROLE_COUNTS) - frozenset(PROXY_ROLES)

# The seven proxy runtime codes, keyed by keccak-256, with the code length and
# source set the registry records for them. Each is a distinct
# `code_keccak256` among the registry's 172 proxy entries, which the generator
# copied from the pinned full observations record's `code` array read at block
# 26,022,093; `test_aave_v3_venue.py` recomputes this table from the committed
# registry. The pinned full source record names
# `InitializableImmutableAdminUpgradeabilityProxy` as the compilation target of
# each of these six source sets. `set-003` carries two of the seven: the Pool
# and PoolConfigurator proxies share one, and 99 token proxies the other.
REVIEWED_PROXY_CODES = {
    "0x3935a620a6917734e2ab10f7d244650670b6d1af1e269359de8cc2aa62f583c8": (1841, "set-081"),
    "0x4bb89014a681591fe927f26347409b23055c418060f77bd980015e8eb06d1df1": (1853, "set-080"),
    "0x67ef5f2e51f31cf415360b09b2af46b4a1a5f879dfabc2d4f3edee5ced7ea65f": (1863, "set-078"),
    "0x6bf1b53de06bf7435f4fb5626b52088fafe8730798d3c46b6468a39ec021e073": (1853, "set-079"),
    "0x82c6d153799b3226525e3b7ec27b843ef44c5f6bca21fcf8b3c80db61ba64881": (2400, "set-003"),
    "0x96107dc4006b4c7fecd1827cfb275ffeef31e6194cd50466f85f8eb24ccf2679": (2400, "set-003"),
    "0xb4697df084c5a3cabfdd7b00c0d106a042c68e9f25eb2d5fd183ca77ec82bb2a": (1909, "set-121"),
}

# The rule each epoch refusal names, so a refusal can be matched to one
# transaction and one rule without re-reading the journals.
RULE_UPGRADE_IN_OPENING_BLOCK = "upgrade-in-opening-block"
RULE_UPGRADE_BEFORE_OPENING_BLOCK = "upgrade-before-opening-block"
RULE_TWO_UPGRADES_IN_ONE_BLOCK = "two-upgrades-in-one-block"
RULE_SLOT_DISAGREES = "slot-disagrees-with-announcement"
RULE_UNRECORDED_IMPLEMENTATION = "unrecorded-implementation"
RULE_UNRECOGNISED_ROLE = "unrecognised-role"
RULE_UNREVIEWED_PROXY_CODE = "unreviewed-proxy-code"
RULE_UPGRADE_FROM_IMMUTABLE = "upgrade-from-immutable-subject"
RULE_EPOCH_LIMIT = "epoch-limit"
RULE_MALFORMED_UPGRADE = "malformed-upgrade-log"

_DECIMAL_RE = re.compile(r"0|[1-9][0-9]{0,18}")


class EpochRefusal(AlexandriaError):
    """An Aave epoch the preserved evidence does not support, named by its rule.

    The message and the attributes carry the subject, block, transaction
    index, log index and rule. An index is None where the refusal is about a
    subject's opening block rather than one log.
    """

    def __init__(self, rule, subject, block, transaction_index, log_index, detail) -> None:
        def shown(value):
            return "none" if value is None else str(value)

        super().__init__(
            f"{VENUE} epoch rule {rule} refuses subject {subject} at block {block}, "
            f"transaction index {shown(transaction_index)}, log index {shown(log_index)}: {detail}"
        )
        self.rule = rule
        self.subject = subject
        self.block = block
        self.transaction_index = transaction_index
        self.log_index = log_index


def validate_plan_scope(plan, registry) -> list:
    """The plan's declared subjects, after its chain, registry and market are checked."""
    if plan.get("chain") != CHAIN:
        raise AlexandriaError(
            f"the {VENUE} venue captures the Ethereum main market on {CHAIN}; the plan names "
            f"chain {str(plan.get('chain'))[:64]!r}"
        )
    if "subjects" not in plan:
        raise AlexandriaError(
            f"the {VENUE} venue captures a declared subject set; a single-proxy plan names none"
        )
    if plan.get("deployment") == PRODUCTION_DEPLOYMENT and plan_digest(plan) not in SEGMENT_PLAN_SHA256:
        raise AlexandriaError(
            f"the plan names the production deployment {PRODUCTION_DEPLOYMENT}, but its SHA-256 "
            f"{plan_digest(plan)} is not one of the {len(SEGMENT_PLAN_SHA256)} pinned segment plan "
            "digests in SEGMENT_PLAN_SHA256"
        )
    if registry is None:
        raise AlexandriaError(
            f"the {VENUE} venue checks every subject against its pinned registry, and none was supplied"
        )
    validate_registry(registry)
    entries = subject_entries(registry)
    subjects = list(plan["subjects"])
    # The market is checked before membership, so a plan built around another
    # market's Pool is refused as the wrong market rather than as one stray subject.
    for key, label in (("pool", "Pool proxy"), ("addresses_provider", "AddressesProvider")):
        if MARKET[key] not in subjects:
            raise AlexandriaError(
                f"the plan does not declare the main market's {label} {MARKET[key]}, so it "
                f"is not a plan over the {VENUE} main market"
            )
    for subject in subjects:
        if subject not in entries:
            raise AlexandriaError(
                f"the plan declares subject {subject}, which the {VENUE} registry does not list"
            )
    return subjects


def opening_phase(plan, registry, staged_logs) -> "SubjectProxyOpening":
    """The opening reads a plan owes, after its chain, registry and market are checked."""
    return SubjectProxyOpening(plan, registry, staged_logs)


class SubjectProxyOpening:
    """The opening reads an Aave plan owes, in the order they are made.

    Planned from the plan, the registry and the staged logs alone, so a fresh
    run, a resumed run, a reconciler and `check` derive the same reads and the
    same request bytes. The code reads come last and are drawn only after
    every slot read has been accepted, because they name the implementations
    the slots hold. Nothing here touches a transport or a file.
    """

    upgrade_topic = UPGRADED_TOPIC

    def __init__(self, plan, registry, staged_logs) -> None:
        self.plan = plan
        self.subjects = validate_plan_scope(plan, registry)
        self.entries = subject_entries(registry)
        self.start, self.end = _interval(plan.get("interval"))
        self.openings = opening_blocks(plan, registry)
        if not self.openings:
            raise AlexandriaError("no declared subject has an extent inside the interval")
        self.logs = staged_logs
        rows = proxy_log_positions(
            staged_logs, self.subjects, _plan_interval(self.start, self.end), upgrade_topic=None
        )
        announced: dict = {}
        for record, row in zip(staged_logs, rows):
            topics = record["topics"]
            if topics and topics[0] == UPGRADED_TOPIC:
                announced.setdefault(row["subject"], []).append(_announcement(record, row))
        # The upgrade shapes that need no read refuse here, before any opening
        # read is made; `derive_epochs` applies the same rules again.
        self.announced = {}
        for subject, items in announced.items():
            role = self.entries[subject]["role"]
            if role in PROXY_ROLES and subject in self.openings:
                _check_announcements(subject, self.openings[subject], items)
                self.announced[subject] = items
            elif role not in PROXY_ROLES:
                first = items[0]
                raise EpochRefusal(
                    RULE_UPGRADE_FROM_IMMUTABLE, subject, first["block"],
                    first["transaction_index"], first["log_index"],
                    "its registry role has one immutable epoch, and it emitted an "
                    "Upgraded(address) log",
                )
        self.proxies = [
            subject for subject in self.subjects
            if subject in self.openings and self.entries[subject]["role"] in PROXY_ROLES
        ]
        self.slot_blocks = {
            subject: [self.openings[subject]]
            + [item["block"] for item in self.announced.get(subject, [])]
            for subject in self.proxies
        }
        upgrade_blocks = {item["block"] for items in self.announced.values() for item in items}
        opening_set = set(self.openings.values())
        self.header_blocks = sorted((opening_set | upgrade_blocks) - {self.start})
        self._opening_set = opening_set
        self.upgrade_hashes: dict = {}
        for items in self.announced.values():
            for item in items:
                self.upgrade_hashes.setdefault(item["block"], set()).add(item["block_hash"])
        self._check_budget()
        self.hashes: dict[int, str] = {}
        self.slot_words: dict[tuple[str, int], str] = {}
        self.codes: dict[str, str] = {}
        self.code_digests: dict[tuple[str, int], str] = {}

    def _check_budget(self) -> None:
        """Refuse a plan whose opening reads cannot fit the one epoch-evidence journal.

        That journal is never split, so a plan that would overflow it is
        refused while the plan is checked, not after every shard.
        """
        owed = self._owed()
        if owed > MAX_JOURNAL_BYTES:
            raise AlexandriaError(
                f"the {len(self.openings)} in-interval subjects' opening reads need about {owed} "
                f"bytes of epoch-evidence journal, above the {MAX_JOURNAL_BYTES}-byte journal "
                "limit; declare fewer subjects per plan"
            )

    def _owed(self) -> int:
        """An upper bound on the journal bytes the opening reads write.

        Every implementation the registry records for an in-interval proxy is
        counted, whether or not its slot names it.
        """
        addresses = set(self.openings)
        for subject in self.proxies:
            addresses.update(_recorded_implementations(self.entries[subject], subject))
        owed = sum(
            2 * _code_length(self.entries.get(address)) + OPENING_ENTRY_OVERHEAD
            for address in addresses
        )
        return owed + OPENING_ENTRY_OVERHEAD * (
            1 + len(self.header_blocks) + sum(len(blocks) for blocks in self.slot_blocks.values())
        )

    def reads(self):
        yield _header_read(FIRST_BLOCK_HEADER, self.start)
        for block in self.header_blocks:
            kind = SUBJECT_HEADER if block in self._opening_set else BOUNDARY_HEADER
            yield _header_read(kind, block)
        for subject in self.proxies:
            for block in self.slot_blocks[subject]:
                yield {
                    "address": subject,
                    "block": block,
                    "kind": SLOT_READ,
                    "method": "eth_getStorageAt",
                    "params": [subject, IMPLEMENTATION_SLOT, hex(block)],
                }
        for address, block in self._code_targets():
            yield {
                "address": address,
                "block": block,
                "kind": CODE_READ,
                "method": "eth_getCode",
                "params": [address, hex(block)],
            }

    def _code_targets(self) -> list:
        """Each address whose code an epoch needs, once, at the first block it is needed.

        Walked in plan order: the subject itself at its opening block, then,
        for a proxy, the implementation its slot holds there and each one it
        announces. Every slot read has to have been accepted first.
        """
        earliest: dict = {}

        def need(address, block):
            if address not in earliest or block < earliest[address]:
                earliest[address] = block

        for subject in self.subjects:
            if subject not in self.openings:
                continue
            opening = self.openings[subject]
            need(subject, opening)
            if subject not in self.slot_blocks:
                continue
            for block in self.slot_blocks[subject]:
                word = self.slot_words.get((subject, block))
                if word is None:
                    raise AlexandriaError(
                        f"the implementation slot of proxy subject {subject} at block {block} "
                        "was not accepted before the code reads were drawn"
                    )
                need(slot_word_address(word, block), block)
        return list(earliest.items())

    def accept(self, read, result) -> str:
        """Shape-check one answer and keep what it binds; returns the comparable value."""
        kind = read["kind"]
        block = read["block"]
        if kind in (FIRST_BLOCK_HEADER, SUBJECT_HEADER, BOUNDARY_HEADER):
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
            if any(value != result["hash"] for value in self.upgrade_hashes.get(block, ())):
                raise OpeningRefusal(
                    "upgrade-log-mismatch", block,
                    f"an upgrade log at block {block} names a different block hash than the "
                    "preserved block",
                )
            self.hashes[block] = result["hash"]
            return result["hash"]
        if kind == SLOT_READ:
            try:
                implementation = implementation_from_word(result, block)
            except AlexandriaError as error:
                raise OpeningRefusal(
                    "slot-not-an-address", block, f"proxy subject {read['address']}: {error}"
                ) from error
            self.slot_words[(read["address"], block)] = result.lower()
            return implementation
        if kind == CODE_READ:
            if result == "0x":
                raise OpeningRefusal(
                    "no-code-at-recorded-block", block,
                    f"{read['address']} has no runtime code at block {block}, the first block "
                    "an epoch needs it at; the registry or the slot is wrong about it",
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
        if kind == SLOT_READ:
            try:
                agreed = slot_word_address(second, block) == value
            except AlexandriaError:
                agreed = False
            return agreed, "slot-word", f"implementation slot of {read['address']} at block {block}"
        if kind == CODE_READ:
            try:
                agreed = hashlib.sha256(runtime_code(second, read["address"])).hexdigest() == value
            except AlexandriaError:
                agreed = False
            return agreed, "code-digest", f"code of {read['address']} at block {block}"
        raise AlexandriaError(f"opening read kind {str(kind)[:64]!r} is not compared")

    def first_code_rows(self) -> list:
        """None: every Aave subject's opening block comes from its recorded creation block."""
        return []

    def epochs(self, end_hash: str) -> dict:
        """The subject-keyed epoch table the accepted reads derive, and nothing else."""
        hashes = dict(self.hashes)
        hashes[self.end] = end_hash
        slot_reads: dict = {}
        for (subject, block), word in self.slot_words.items():
            slot_reads.setdefault(subject, {})[block] = word
        return derive_subject_epochs(
            chain=self.plan["chain"],
            deployment=self.plan.get("deployment"),
            interval=self.plan.get("interval"),
            subjects=self.subjects,
            entries=self.entries,
            logs=self.logs,
            slot_reads=slot_reads,
            code_reads=dict(self.codes),
            block_hashes=hashes,
        )


def _code_length(entry) -> int:
    value = entry.get("code_length") if isinstance(entry, dict) else None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= MAX_RUNTIME_CODE_BYTES:
        return MAX_RUNTIME_CODE_BYTES
    return value


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


def opening_blocks(plan, registry) -> dict:
    """Each declared subject's opening block: the later of the plan start and its creation.

    A subject created after the plan's end carries no key, because it has no
    epoch in that plan.
    """
    subjects = validate_plan_scope(plan, registry)
    start, end = _interval(plan.get("interval"))
    entries = subject_entries(registry)
    blocks = {}
    for subject in subjects:
        first = max(start, entries[subject]["creation_block"])
        if first <= end:
            blocks[subject] = first
    return blocks


def derive_epochs(plan, registry, *, logs, slot_reads, code_reads, block_hashes) -> dict:
    """The subject-keyed epoch table the preserved reads derive, and nothing else.

    `logs` are the plan's preserved subject logs in position order.
    `slot_reads` maps each proxy subject to `{block: word}`, the EIP-1967 slot
    as read at the end of that block. `code_reads` maps an address to the
    runtime code read for it: each immutable subject and each proxy at its
    opening block, and each implementation an epoch names. `block_hashes`
    maps a block to its preserved hash. Nothing here reads a chain, and a
    read that is missing refuses rather than being inferred.
    """
    subjects = validate_plan_scope(plan, registry)
    return derive_subject_epochs(
        chain=plan["chain"],
        deployment=plan.get("deployment"),
        interval=plan.get("interval"),
        subjects=subjects,
        entries=subject_entries(registry),
        logs=logs,
        slot_reads=slot_reads,
        code_reads=code_reads,
        block_hashes=block_hashes,
    )


def derive_subject_epochs(
    *, chain, deployment, interval, subjects, entries, logs, slot_reads, code_reads, block_hashes,
) -> dict:
    """`derive_epochs` over registry entries already validated by the caller.

    Split out so the role refusal can be exercised: the pinned registry holds
    only the fourteen roles `aave_registry.EXPECTED_ROLE_COUNTS` counts, so an
    unrecognised role cannot reach this through `derive_epochs`.
    """
    start, end = _interval(interval)
    if not isinstance(logs, (list, tuple)):
        raise AlexandriaError("the preserved subject logs are not a list")
    for label, value in (
        ("slot_reads", slot_reads), ("code_reads", code_reads), ("block_hashes", block_hashes),
    ):
        if not isinstance(value, dict):
            raise AlexandriaError(f"the preserved opening reads' {label} is not a mapping")
    if not isinstance(entries, dict):
        raise AlexandriaError("the registry entries are not a mapping")
    # Shape, emitter and order first, with every log read as ordinary: the
    # announcements are found below, so each upgrade shape is refused here by
    # its own rule before the shared walk's generic refusals could fire.
    rows = proxy_log_positions(logs, subjects, _plan_interval(start, end), upgrade_topic=None)
    announcements: dict = {}
    for record, row in zip(logs, rows):
        topics = record["topics"]
        if topics and topics[0] == UPGRADED_TOPIC:
            announcements.setdefault(row["subject"], []).append(_announcement(record, row))

    epochs = {}
    for subject in subjects:
        entry = entries.get(subject)
        if not isinstance(entry, dict):
            raise AlexandriaError(f"the registry has no entry for declared subject {subject}")
        creation = entry.get("creation_block")
        if isinstance(creation, bool) or not isinstance(creation, int) or not 0 <= creation <= MAX_BLOCK:
            raise AlexandriaError(f"the registry entry for {subject} has no integer creation_block")
        opening = max(start, creation)
        role = entry.get("role")
        if opening > end:
            continue
        if role in IMMUTABLE_ROLES:
            epochs[subject] = _immutable_epochs(
                chain, deployment, subject, opening, end, code_reads, block_hashes,
                announcements.get(subject, []),
            )
        elif role in PROXY_ROLES:
            epochs[subject] = _proxy_epochs(
                chain, deployment, subject, entry, opening, end, slot_reads, code_reads,
                block_hashes, announcements.get(subject, []),
            )
        else:
            raise EpochRefusal(
                RULE_UNRECOGNISED_ROLE, subject, opening, None, None,
                f"its registry role {str(role)[:64]!r} is neither a proxy role nor an "
                "immutable role, so no epoch model applies",
            )
    if not epochs:
        raise AlexandriaError("no declared subject has an extent inside the interval")
    validate_epochs(epochs, start, end)
    attribute_positions(logs, subjects, _plan_interval(start, end), epochs)
    return epochs


def attribute_positions(logs, subjects, interval, epochs) -> list:
    """Own each preserved log by position under this venue's upgrade-transaction rule."""
    return attribute_logs(
        logs, subjects, interval, epochs,
        upgrade_topic=UPGRADED_TOPIC, order_upgrade_transactions=True,
    )


def _immutable_epochs(chain, deployment, subject, opening, end, code_reads, block_hashes, announced):
    if announced:
        first = announced[0]
        raise EpochRefusal(
            RULE_UPGRADE_FROM_IMMUTABLE, subject, first["block"], first["transaction_index"],
            first["log_index"],
            "its registry role has one immutable epoch, and it emitted an Upgraded(address) log",
        )
    code = _code(code_reads, subject, subject, opening)
    return [_epoch(
        chain, deployment, subject, subject, hashlib.sha256(code).hexdigest(),
        _block_sentinel(opening), _block_sentinel(end + 1), None, block_hashes, subject,
    )]


def _proxy_epochs(chain, deployment, subject, entry, opening, end, slot_reads, code_reads,
                  block_hashes, announced):
    proxy_code = keccak256(_code(code_reads, subject, subject, opening))
    reviewed = "0x" + proxy_code.hex()
    if reviewed not in REVIEWED_PROXY_CODES:
        raise EpochRefusal(
            RULE_UNREVIEWED_PROXY_CODE, subject, opening, None, None,
            f"its runtime code hashes to keccak-256 {reviewed}, which is not one of the "
            f"{len(REVIEWED_PROXY_CODES)} reviewed proxy codes",
        )
    recorded = _recorded_implementations(entry, subject)
    _check_epoch_limit(subject, announced)
    implementation = _slot(slot_reads, subject, opening)
    if implementation not in recorded:
        raise EpochRefusal(
            RULE_UNRECORDED_IMPLEMENTATION, subject, opening, None, None,
            f"its implementation slot holds {implementation} at the end of its opening block, "
            "an implementation the registry does not record for this subject",
        )
    # The shape of every announcement is checked before any is compared with a
    # slot read, so a block holding two is refused as that, not as whichever
    # of its two announcements the block's one slot read disagrees with.
    _check_announcement_blocks(subject, opening, announced)
    starts = [(_block_sentinel(opening), implementation, None)]
    for item in announced:
        block, tx, log = item["block"], item["transaction_index"], item["log_index"]
        held = _slot(slot_reads, subject, block)
        if held != item["implementation"]:
            raise EpochRefusal(
                RULE_SLOT_DISAGREES, subject, block, tx, log,
                f"the announcement names {item['implementation']} while the implementation "
                f"slot read at the end of the block holds {held}",
            )
        if item["implementation"] not in recorded:
            raise EpochRefusal(
                RULE_UNRECORDED_IMPLEMENTATION, subject, block, tx, log,
                f"the announcement names {item['implementation']}, an implementation the "
                "registry does not record for this subject",
            )
        position = {"block_number": str(block), "transaction_index": tx, "log_index": log}
        upgrade = dict(position, transaction_hash=item["transaction_hash"])
        starts.append((position, item["implementation"], upgrade))
    epochs = []
    for index, (position, implementation, upgrade) in enumerate(starts):
        closing = starts[index + 1][0] if index + 1 < len(starts) else _block_sentinel(end + 1)
        code = _code(code_reads, implementation, subject, int(position["block_number"]))
        epochs.append(_epoch(
            chain, deployment, subject, implementation, hashlib.sha256(code).hexdigest(),
            position, closing, upgrade, block_hashes, subject,
        ))
    return epochs


def _check_epoch_limit(subject, announced) -> None:
    if len(announced) + 1 > MAX_EPOCHS:
        extra = announced[MAX_EPOCHS - 1]
        raise EpochRefusal(
            RULE_EPOCH_LIMIT, subject, extra["block"], extra["transaction_index"], extra["log_index"],
            f"its {len(announced)} announcements would open {len(announced) + 1} epochs, above "
            f"the {MAX_EPOCHS}-epoch limit",
        )


def _check_announcement_blocks(subject, opening, announced) -> None:
    seen_blocks = set()
    for item in announced:
        block, tx, log = item["block"], item["transaction_index"], item["log_index"]
        if block < opening:
            raise EpochRefusal(
                RULE_UPGRADE_BEFORE_OPENING_BLOCK, subject, block, tx, log,
                f"the announcement precedes the subject's opening block {opening}",
            )
        if block == opening:
            raise EpochRefusal(
                RULE_UPGRADE_IN_OPENING_BLOCK, subject, block, tx, log,
                "the opening implementation is read from the slot at the end of this block, "
                "so an announcement inside it leaves the earlier logs' implementation unread",
            )
        if block in seen_blocks:
            raise EpochRefusal(
                RULE_TWO_UPGRADES_IN_ONE_BLOCK, subject, block, tx, log,
                "a second announcement in one block cannot be checked against a slot read "
                "at the block's end",
            )
        seen_blocks.add(block)


def _check_announcements(subject, opening, announced) -> None:
    """The announcement rules that need no read, in the order `_proxy_epochs` applies them."""
    _check_epoch_limit(subject, announced)
    _check_announcement_blocks(subject, opening, announced)


def _epoch(chain, deployment, subject, implementation, digest, first, last, upgrade,
           block_hashes, owner):
    start_block = int(first["block_number"])
    # A closing block sentinel ends the envelope at the block before it; a
    # closing announcement ends it at the announcement's own block.
    end_block = int(last["block_number"]) - (last["transaction_index"] is None)
    return {
        "chain": chain,
        "deployment": deployment,
        "end_block": str(end_block),
        "end_hash": _block_hash(block_hashes, end_block, owner),
        "end_position": last,
        "implementation": implementation,
        "implementation_code_sha256": digest,
        "proxy": subject,
        "start_block": str(start_block),
        "start_hash": _block_hash(block_hashes, start_block, owner),
        "start_position": first,
        "upgrade": upgrade,
    }


def _announcement(record, row) -> dict:
    """One `Upgraded(address)` log's coordinates and the implementation it names."""
    subject = row["subject"]
    block, tx, log = int(row["block_number"]), row["transaction_index"], row["log_index"]
    topics = record["topics"]
    if len(topics) != 2 or WORD_RE.fullmatch(topics[1]) is None or topics[1][2:26].strip("0"):
        raise EpochRefusal(
            RULE_MALFORMED_UPGRADE, subject, block, tx, log,
            "an Upgraded(address) log must carry two topics, the second a left-padded address",
        )
    implementation = "0x" + topics[1][-40:]
    if implementation == "0x" + "0" * 40:
        raise EpochRefusal(
            RULE_MALFORMED_UPGRADE, subject, block, tx, log,
            "the Upgraded(address) log announces the zero address",
        )
    return {
        "block": block,
        "block_hash": row["block_hash"],
        "implementation": implementation,
        "log_index": log,
        "transaction_hash": row["transaction_hash"],
        "transaction_index": tx,
    }


def _recorded_implementations(entry, subject) -> frozenset:
    table = entry.get("implementations")
    if not isinstance(table, list) or not table:
        raise AlexandriaError(f"the registry entry for proxy {subject} records no implementations")
    recorded = set()
    for position, item in enumerate(table):
        address = item.get("implementation") if isinstance(item, dict) else None
        if not isinstance(address, str) or ADDRESS_RE.fullmatch(address) is None:
            raise AlexandriaError(
                f"the registry entry for proxy {subject} implementation {position} is not a "
                "lowercase address"
            )
        recorded.add(address)
    return frozenset(recorded)


def _lookup(mapping, block):
    """A block-keyed read, whether the key is an integer or its decimal text."""
    if block in mapping:
        return mapping[block]
    return mapping.get(str(block))


def _slot(slot_reads, subject, block) -> str:
    reads = slot_reads.get(subject)
    if reads is None:
        raise AlexandriaError(f"proxy subject {subject} has no preserved implementation slot reads")
    if not isinstance(reads, dict):
        raise AlexandriaError(f"the implementation slot reads of proxy subject {subject} are not a mapping")
    word = _lookup(reads, block)
    if word is None:
        raise AlexandriaError(
            f"proxy subject {subject} has no implementation slot read at block {block}, and no "
            "implementation is inferred for it"
        )
    try:
        return implementation_from_word(word, block)
    except AlexandriaError as error:
        raise AlexandriaError(f"proxy subject {subject}: {error}") from error


def _code(code_reads, address, subject, block) -> bytes:
    value = code_reads.get(address)
    if value is None:
        raise AlexandriaError(
            f"subject {subject} needs the runtime code of {address} for its epoch at block "
            f"{block}, and it was not read"
        )
    return runtime_code(value, address)


def _block_hash(block_hashes, block, subject) -> str:
    value = _lookup(block_hashes, block)
    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
        raise AlexandriaError(
            f"subject {subject} has an epoch boundary at block {block}, which has no preserved "
            "block hash"
        )
    return value


def _block_sentinel(block) -> dict:
    return {"block_number": str(block), "log_index": None, "transaction_index": None}


def _interval(interval):
    if not isinstance(interval, dict) or set(interval) != {"end", "start"}:
        raise AlexandriaError("the plan interval has an unknown shape")
    bounds = []
    for key in ("start", "end"):
        value = interval[key]
        if not isinstance(value, str) or _DECIMAL_RE.fullmatch(value) is None or int(value) > MAX_BLOCK:
            raise AlexandriaError(f"the plan interval {key} is not a bounded decimal block number")
        bounds.append(int(value))
    if bounds[1] < bounds[0]:
        raise AlexandriaError("the plan interval end precedes its start")
    return bounds[0], bounds[1]


def _plan_interval(start, end) -> dict:
    return {"end": str(end), "start": str(start)}


def gaps(registry, plan=None) -> list[str]:
    """The periphery overlap the registry records, one sentence per address."""
    return [
        f"subject {item['address']} ({item['role']}) is also listed as periphery "
        f"({item['periphery']}) in the full record the {VENUE} row pins; it is captured as a "
        "subject because it is inside the row's digest-bound subject set"
        for item in registry["periphery"]["overlap"]
    ]


def evidence_gaps(plan, registry, logs, first_code=None) -> list[str]:
    """The venue's contribution to every evidence scope's declared gaps.

    A deployment name this venue does not admit as preserved, then the
    subjects created before the plan's start and those created after its end.
    Each of the last two kinds names `LISTED_GAPS` subjects and counts the
    rest in one sentence, so the gaps stay bounded whatever the plan declares.
    `logs` and `first_code` are accepted for the collector's shared call and
    change nothing here: every Aave subject's creation block is recorded.
    """
    subjects = validate_plan_scope(plan, registry)
    start, end = _interval(plan.get("interval"))
    entries = subject_entries(registry)
    result = []
    if plan["deployment"] not in PRESERVED_DEPLOYMENTS:
        result.append(CONSTRUCTED_STAGING_GAP.format(deployment=plan["deployment"], venue=VENUE))
    result.extend(_bounded(
        [
            f"subject {subject} was created at block {entries[subject]['creation_block']}, before "
            f"the plan's start block {start}; its epoch opens at the start, its creation block is "
            "the registry's record rather than a read this collection made, and its activity "
            "before the start is outside this capture"
            for subject in subjects if entries[subject]["creation_block"] < start
        ],
        "{rest} further declared subjects, {total} in all, were created before the plan's start; "
        "each epoch opens at the start and the registry component names each creation block",
    ))
    result.extend(_bounded(
        [
            f"subject {subject} was created at block {entries[subject]['creation_block']}, after "
            f"the plan's end block {end}, so it has no epoch and is outside the interval"
            for subject in subjects if entries[subject]["creation_block"] > end
        ],
        "{rest} further declared subjects, {total} in all, were created after the plan's end, "
        "have no epoch and are outside the interval; the plan and registry components name each",
    ))
    return result


def _bounded(sentences: list, rest: str) -> list:
    """At most `LISTED_GAPS` named sentences, then one that counts the others."""
    if len(sentences) <= LISTED_GAPS:
        return sentences
    return sentences[:LISTED_GAPS] + [
        rest.format(rest=len(sentences) - LISTED_GAPS, total=len(sentences))
    ]


# Keccak-256 as Ethereum uses it (the 0x01 domain byte, not SHA3-256's 0x06).
# The standard library carries only SHA3, and the reviewed proxy codes are
# recorded by keccak-256, so the proxy-code check needs its own.
_KECCAK_ROUNDS = (
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
)
_KECCAK_ROTATIONS = (
    0, 1, 62, 28, 27, 36, 44, 6, 55, 20, 3, 10, 43, 25, 39,
    41, 45, 15, 21, 8, 18, 2, 61, 56, 14,
)
_LANE = (1 << 64) - 1
_RATE = 136


def _rotl(value, amount):
    return ((value << amount) | (value >> (64 - amount))) & _LANE if amount else value


def _keccak_f(lanes):
    for constant in _KECCAK_ROUNDS:
        parity = [lanes[x] ^ lanes[x + 5] ^ lanes[x + 10] ^ lanes[x + 15] ^ lanes[x + 20] for x in range(5)]
        for x in range(5):
            delta = parity[(x - 1) % 5] ^ _rotl(parity[(x + 1) % 5], 1)
            for y in range(0, 25, 5):
                lanes[x + y] ^= delta
        moved = [0] * 25
        for x in range(5):
            for y in range(5):
                moved[y + 5 * ((2 * x + 3 * y) % 5)] = _rotl(lanes[x + 5 * y], _KECCAK_ROTATIONS[x + 5 * y])
        for y in range(0, 25, 5):
            row = moved[y:y + 5]
            for x in range(5):
                lanes[x + y] = row[x] ^ (~row[(x + 1) % 5] & row[(x + 2) % 5])
        lanes[0] ^= constant


def keccak256(data: bytes) -> bytes:
    """The 32-byte keccak-256 digest of `data`."""
    return _sponge(data, 0x01)


def _sponge(data, domain: int) -> bytes:
    """The 256-bit sponge over `data` with one domain byte.

    0x01 is keccak-256. 0x06 is SHA3-256, which lets a test hold this
    permutation and padding to `hashlib.sha3_256` at every length.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise AlexandriaError("keccak-256 input must be bytes")
    padded = bytearray(data) + bytes([domain])
    padded += b"\x00" * (-len(padded) % _RATE)
    padded[-1] |= 0x80
    lanes = [0] * 25
    for offset in range(0, len(padded), _RATE):
        for lane in range(_RATE // 8):
            start = offset + 8 * lane
            lanes[lane] ^= int.from_bytes(padded[start:start + 8], "little")
        _keccak_f(lanes)
    return b"".join(lane.to_bytes(8, "little") for lane in lanes[:4])
