"""One pass over preserved logs, in plan order, with bounded state.

`LogWalk` applies every rule `interval.proxy_log_positions` applies and, given
epochs, attributes each log as `interval.attribute_logs` does. It is fed one
shard's `eth_getLogs` result at a time and keeps only:

1. the previous position, for the ordering rule;
2. the current block's hash and the current transaction's hash, for the two
   contradiction rules the ordering rule makes local;
3. the subjects upgraded in the current block and transaction, and the first
   ordinary log of each subject in the current transaction, for the upgrade
   rules;
4. one 8-byte key per distinct transaction (the first 8 bytes of its hash) in
   256 `array("Q")` buckets by first byte, for the rule that one transaction
   hash names one position;
5. with epochs, one cursor per subject; and
6. the logs whose first topic the caller declared as opening logs.

The key rule is the only one a single pass cannot settle. After the pass each
bucket is sorted on its own. A repeated key is a transaction hash at two
positions or two hashes sharing their first 8 bytes. Only then does the walk
read the logs a second time, collecting full hashes for the repeated keys
alone, and refuse with the base message and coordinate or continue. The second
read must reproduce the first: every transaction's position and hash, and the
log count, are bound by a SHA-256 taken during the first pass, so a key
collision costs a read and never admits a log.

A refusal found during the pass is held, and the walk stops reading. `finish`
raises whichever refusal `proxy_log_positions` and `attribute_logs` raise on
the same logs: a repeated transaction hash at or before the held position,
then the held refusal, then an ordinary log in an upgrade transaction, then
the first attribution refusal in the order the subjects first appear. Rows
`feed` returns are provisional until `finish` returns.
"""

from __future__ import annotations

from array import array
import hashlib
import re

from .errors import AlexandriaError
from .interval import (
    HASH_RE,
    MAX_EPOCHS,
    MAX_POSITION_INDEX,
    MAX_POSITION_QUANTITY_LENGTH,
    MAX_SUBJECTS,
    UPGRADED_TOPIC,
    _address,
    _decimal,
    _declared_subjects,
    _hash,
    _position_key,
    _upgrade_log,
    validate_epoch_subjects,
    validate_epochs,
)

# The width of the per-transaction key, read when a walk starts. A test may
# narrow it to force collisions; a collision only costs the second read.
KEY_BYTES = 8
BUCKETS = 256
# The opening logs a release may hold: one per subject epoch at most.
MAX_OPENING_LOGS = MAX_SUBJECTS * MAX_EPOCHS
QUANTITY_RE = re.compile(r"0x(?:0|[1-9a-f][0-9a-f]*)")
_ABSENT = object()


def checked_inputs(subjects, interval, records=_ABSENT):
    """The declared subjects and interval, refused in `proxy_log_positions`' order.

    Returns `(single, subjects, start, end)`. `records`, when given, is checked
    where `proxy_log_positions` checks it: after the interval's shape and
    before its values.
    """
    single = isinstance(subjects, str)
    allowed = _declared_subjects(subjects)
    if not isinstance(interval, dict) or set(interval) != {"start", "end"}:
        raise AlexandriaError("position interval has an unknown shape")
    if records is not _ABSENT and not isinstance(records, (list, tuple)):
        raise AlexandriaError("proxy logs are not a list")
    if any(not isinstance(interval[key], str) or len(interval[key]) > 19 for key in ("start", "end")):
        raise AlexandriaError("position interval blocks must be bounded decimal strings")
    start = _decimal(interval["start"], "position interval start")
    end = _decimal(interval["end"], "position interval end")
    return single, allowed, start, end


def checked_epochs(subjects, interval, epochs) -> None:
    """Refuse an epoch table as `attribute_logs` does, before any log is read."""
    validate_epochs(epochs, int(interval["start"]), int(interval["end"]))
    if isinstance(subjects, str):
        if not isinstance(epochs, list):
            raise AlexandriaError("a single subject requires a flat epoch list")
    else:
        validate_epoch_subjects(epochs, subjects)


def attribute_row(row, epochs, index: int) -> int:
    """Give one row its epoch in one subject's own table; returns the cursor after it.

    `index` is the cursor the previous row of the same subject left, so a
    subject's rows, taken in position order, walk its table once.
    """
    key = (int(row["block_number"]), row["transaction_index"], row["log_index"])
    while index + 1 < len(epochs) and key >= _position_key(epochs[index]["end_position"]):
        index += 1
    epoch = epochs[index]
    if not _position_key(epoch["start_position"]) <= key < _position_key(epoch["end_position"]):
        raise AlexandriaError("proxy log has no positional epoch owner")
    for boundary in ("start", "end"):
        if row["block_number"] == epoch[boundary + "_block"] and row["block_hash"] != epoch[boundary + "_hash"]:
            raise AlexandriaError("proxy log hash contradicts its epoch boundary")
    row["epoch_index"] = index
    return index


def _transaction_record(block: int, tx: int, log: int, tx_hash: str) -> bytes:
    return b"%d,%d,%d,%s;" % (block, tx, log, tx_hash.encode("ascii"))


def _conflict(coordinate) -> AlexandriaError:
    return AlexandriaError(
        f"proxy log position {coordinate} has contradictory transaction hash/index pairs"
    )


class LogWalk:
    """Validate, and optionally attribute, preserved logs fed in plan order.

    `subjects`, `interval` and `upgrade_topic` mean what they mean to
    `proxy_log_positions`; `epochs` what it means to `attribute_logs`.
    `opening_topics` names the first topics whose logs the walk keeps for the
    venue's opening phase and gaps; `venues.opening_logs` returns them.
    """

    def __init__(self, subjects, interval, *, upgrade_topic=UPGRADED_TOPIC, epochs=None,
                 opening_topics=()) -> None:
        if epochs is not None:
            checked_epochs(subjects, interval, epochs)
        self.single, self.subjects, self.start, self.end = checked_inputs(subjects, interval)
        self._allowed = frozenset(self.subjects)
        self.upgrade_topic = upgrade_topic
        self.epochs = epochs
        self.opening_topics = frozenset(opening_topics)
        self._not_emitted = (
            "a preserved log was not emitted by the proxy" if self.single
            else "a preserved log was not emitted by a declared subject"
        )
        self._key_hex = 2 * KEY_BYTES
        self._buckets = [array("Q") for _ in range(BUCKETS)]
        self._digest = hashlib.sha256()
        # Rows derived, and records that passed the hash rules (the ones the
        # second read has to reproduce).
        self.count = 0
        self._hashed = 0
        self._previous = None
        self._block = None
        self._block_hash = None
        self._block_upgrades: set = set()
        self._transaction = None
        self._transaction_hash = None
        self._transaction_upgrades: set = set()
        self._ordinary: dict = {}
        self._held = None
        self._upgrade_refusal = None
        # subject -> [cursor, table, refusal], in the order subjects first appear.
        self._attribution: dict = {}
        self.opening: list = []
        self.opening_count = 0
        self.rereads = 0
        self.finished = False

    # -- the first pass ------------------------------------------------------

    def feed(self, records) -> list:
        """Read one shard's logs; return the rows derived from them, provisionally."""
        if self.finished:
            raise AlexandriaError("the log walk has already finished")
        if not isinstance(records, (list, tuple)):
            raise AlexandriaError("proxy logs are not a list")
        rows = []
        if self._held is not None:
            return rows
        for record in records:
            try:
                row = self._accept(record)
            except AlexandriaError as refusal:
                self._held = refusal
                return rows
            rows.append(row)
        return rows

    def _accept(self, record) -> dict:
        if not isinstance(record, dict):
            raise AlexandriaError(self._not_emitted)
        address = _address(record.get("address"), "log emitting contract")
        if address not in self._allowed:
            raise AlexandriaError(self._not_emitted)
        values = []
        for field in ("blockNumber", "transactionIndex", "logIndex"):
            value = record.get(field)
            if not isinstance(value, str) or QUANTITY_RE.fullmatch(value) is None:
                raise AlexandriaError(f"proxy log {field} is not a canonical non-negative quantity")
            if len(value) > MAX_POSITION_QUANTITY_LENGTH or int(value, 16) > MAX_POSITION_INDEX:
                raise AlexandriaError(f"proxy log {field} exceeds the canonical integer limit")
            values.append(int(value, 16))
        block, tx, log = values
        if not self.start <= block <= self.end:
            raise AlexandriaError(f"proxy log block {block} is outside the interval")
        coordinate = (block, tx, log)
        previous = self._previous
        if previous is not None and (coordinate <= previous or
                (block == previous[0] and (tx < previous[1] or log <= previous[2]))):
            raise AlexandriaError(f"proxy log position {coordinate} is duplicated or unordered")
        self._previous = coordinate
        block_hash = _hash(record.get("blockHash"), "proxy log block hash")
        tx_hash = _hash(record.get("transactionHash"), "proxy log transaction hash")
        # Positions strictly ascend, so a block's logs and a transaction's logs
        # are contiguous: comparing with the current ones is the whole rule.
        if block != self._block:
            self._end_transaction()
            self._block, self._block_hash = block, block_hash
            self._block_upgrades = set()
        elif block_hash != self._block_hash:
            raise AlexandriaError(f"proxy log block {block} has contradictory hashes")
        if (block, tx) != self._transaction:
            self._end_transaction()
            self._transaction, self._transaction_hash = (block, tx), tx_hash
            self._buckets[int(tx_hash[2:4], 16)].append(int(tx_hash[2:2 + self._key_hex], 16))
            self._digest.update(_transaction_record(block, tx, log, tx_hash))
        elif tx_hash != self._transaction_hash:
            raise _conflict(coordinate)
        self._hashed += 1
        topics = record.get("topics")
        if not isinstance(topics, list) or any(not isinstance(topic, str) or HASH_RE.fullmatch(topic) is None for topic in topics):
            raise AlexandriaError(f"proxy log position {coordinate} has malformed topics")
        is_upgrade = bool(self.upgrade_topic is not None and topics and topics[0] == self.upgrade_topic)
        if is_upgrade:
            _upgrade_log(record, address, self.count)
            if block == self.start:
                raise AlexandriaError(f"first-block upgrade at {coordinate} has no preceding implementation evidence")
            if address in self._block_upgrades:
                raise AlexandriaError(f"multiple upgrades in block {block} are unsupported")
            self._block_upgrades.add(address)
            self._transaction_upgrades.add(address)
        else:
            self._ordinary.setdefault(address, coordinate)
        row = {"block_number": str(block), "block_hash": block_hash,
               "transaction_hash": tx_hash, "transaction_index": tx,
               "log_index": log, "kind": "upgrade-boundary" if is_upgrade else "proxy-log"}
        if not self.single:
            row["subject"] = address
        if self.epochs is not None:
            self._attribute(row, address)
        if topics and topics[0] in self.opening_topics:
            self.opening_count += 1
            if self.opening_count <= MAX_OPENING_LOGS:
                self.opening.append(record)
        self.count += 1
        return row

    def _end_transaction(self) -> None:
        """Close the current transaction: an ordinary log beside its subject's upgrade refuses."""
        if self._upgrade_refusal is None and self._transaction_upgrades:
            found = [coordinate for subject, coordinate in self._ordinary.items()
                     if subject in self._transaction_upgrades]
            if found:
                block, tx, log = min(found)
                self._upgrade_refusal = AlexandriaError(
                    f"ordinary proxy log at ({block}, {tx}, {log}) in an upgrade transaction is unsupported"
                )
        self._transaction_upgrades = set()
        self._ordinary = {}

    def _attribute(self, row, subject: str) -> None:
        state = self._attribution.get(subject)
        if state is None:
            table = self.epochs if self.single else self.epochs.get(subject)
            refusal = None if table else AlexandriaError("proxy log has no positional epoch owner")
            state = self._attribution[subject] = [0, table, refusal]
        if state[2] is not None:
            return
        try:
            state[0] = attribute_row(row, state[1], state[0])
        except AlexandriaError as refusal:
            state[2] = refusal

    # -- after the pass ------------------------------------------------------

    def finish(self, reread=None) -> None:
        """Raise the refusal the whole-list derivation raises, if any.

        `reread` returns the same logs again, as an iterable of shard results;
        it is called only when two transactions share a key.
        """
        if self.finished:
            raise AlexandriaError("the log walk has already finished")
        self.finished = True
        if self._held is None:
            self._end_transaction()
        conflict = self._settle_keys(reread)
        if conflict is not None:
            raise conflict
        if self._held is not None:
            raise self._held
        if self._upgrade_refusal is not None:
            raise self._upgrade_refusal
        for _cursor, _table, refusal in self._attribution.values():
            if refusal is not None:
                raise refusal

    def _repeated_keys(self) -> array:
        repeated = array("Q")
        for index, bucket in enumerate(self._buckets):
            ordered = sorted(bucket)
            self._buckets[index] = array("Q")
            for position in range(1, len(ordered)):
                if ordered[position] == ordered[position - 1] and (
                    not repeated or repeated[-1] != ordered[position]
                ):
                    repeated.append(ordered[position])
        return repeated

    def _settle_keys(self, reread):
        repeated = self._repeated_keys()
        if not repeated:
            return None
        if reread is None:
            raise AlexandriaError(
                "two preserved transactions share a key and the log walk was given no second read"
            )
        self.rereads += 1
        wanted = frozenset(repeated)
        del repeated
        digest = hashlib.sha256()
        seen: set = set()
        first = None
        transaction = None
        count = 0
        mismatch = AlexandriaError("the second read of the preserved logs does not match the first")
        for records in reread():
            if count == self._hashed:
                break
            if not isinstance(records, (list, tuple)):
                raise mismatch
            for record in records:
                if count == self._hashed:
                    break
                try:
                    block = int(record["blockNumber"], 16)
                    tx = int(record["transactionIndex"], 16)
                    log = int(record["logIndex"], 16)
                    tx_hash = _hash(record["transactionHash"], "proxy log transaction hash")
                except (AlexandriaError, KeyError, TypeError, ValueError) as error:
                    raise mismatch from error
                count += 1
                if (block, tx) == transaction:
                    continue
                transaction = (block, tx)
                digest.update(_transaction_record(block, tx, log, tx_hash))
                if first is None and int(tx_hash[2:2 + self._key_hex], 16) in wanted:
                    if tx_hash in seen:
                        first = (block, tx, log)
                    else:
                        seen.add(tx_hash)
        if count != self._hashed or digest.digest() != self._digest.digest():
            raise mismatch
        return None if first is None else _conflict(first)
