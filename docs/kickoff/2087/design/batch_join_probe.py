"""Selection probe for the Wildcat withdrawal-batch burn join (issue #2087).

An executable bounded proposal model, not product conformance. Each candidate
is a pairing rule between a market's ``Transfer(market, 0x0, value)`` burn and
a batch event in the same transaction. The specimens below are constructed from
the pinned V1/V2 market source emission order; none comes from a retained
capture. One report per candidate and criterion is written to ``--report``,
which must not exist.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins" / "tabularium" / "tests"))
sys.path.insert(0, str(ROOT / "plugins" / "tabularium" / "scripts"))

CANDIDATES = ("adjacent-burn", "unique-value-burn", "all-batch-events", "envelope-batch-field")
CRITERIA = {
    "source-pairing-determinism": ("boolean", "determinism"),
    "single-claim": ("boolean", "single_claim"),
    "missing-or-ambiguous-stays-gap": ("boolean", "recovery"),
    "schema-envelope-unchanged": ("boolean", "envelope"),
    "existing-rows-unchanged": ("boolean", "existing_rows"),
    "pair-comparisons": ("count", "comparisons"),
    "retained-candidates": ("count", "retained"),
}
ZERO = "0x" + "00" * 20
MARKET = "0x" + "11" * 20


# Specimen transactions: ordered (kind, expiry, value) tuples. ``burn`` value is
# the normalized amount; ``payment`` value is normalizedAmountPaid.
# Source order: V1 queueWithdrawal emits Transfer, Created, Queued, then the
# batch payment pair; V2 emits Created first. Both emit the burn immediately
# before WithdrawalBatchPayment inside _applyWithdrawalBatchPayment.
SOURCE_SPECIMENS = {
    "v1-queue-first-batch": [("transfer", None, 70), ("created", 100, None), ("queued", 100, 70),
                             ("burn", None, 40), ("payment", 100, 40)],
    "v2-queue-first-batch": [("created", 100, None), ("transfer", None, 70), ("queued", 100, 70),
                             ("burn", None, 40), ("payment", 100, 40)],
    # repayAndProcessUnpaidWithdrawalBatches paying two batches owed equal amounts
    "repay-two-unpaid-equal-amounts": [("repaid", None, 80), ("burn", None, 40), ("payment", 100, 40),
                                       ("closed", 100, None), ("burn", None, 40), ("payment", 200, 40),
                                       ("closed", 200, None)],
    # queueWithdrawal: _getUpdatedState pays the pending batch, the queue adds to it and pays again
    "queue-double-payment-same-expiry": [("burn", None, 10), ("payment", 300, 10), ("transfer", None, 20),
                                         ("queued", 300, 20), ("burn", None, 10), ("payment", 300, 10)],
    # expiry processing then V1 closure of a fully paid batch
    "expired-paid-closed": [("burn", None, 25), ("payment", 400, 25), ("expired", 400, 25), ("closed", 400, None)],
    # V2 closeMarket: pending batch paid, expired, closed, new one-second batch created
    "v2-close-market": [("burn", None, 15), ("payment", 500, 15), ("expired", 500, 15), ("closed", 500, None),
                        ("created", 501, None)],
}
HOSTILE_SPECIMENS = {
    "burn-after-payment": [("payment", 100, 40), ("burn", None, 40)],
    "burn-value-changed": [("burn", None, 41), ("payment", 100, 40)],
    "burn-without-payment": [("transfer", None, 5), ("burn", None, 40)],
    "two-burns-one-payment": [("burn", None, 40), ("burn", None, 40), ("payment", 100, 40)],
    "payment-without-burn": [("queued", 100, 40), ("payment", 100, 40)],
}
BATCH_KINDS = ("created", "payment", "expired", "closed")


class Ambiguous(Exception):
    pass


def pair(candidate, sequence):
    """Return (joins, comparisons, retained, claims) for one transaction.

    joins: {payment index: burn index}; claims: Counter of burn index claims.
    """
    items = list(enumerate(sequence))
    burns = [(i, v) for i, (k, _, v) in items if k == "burn"]
    joins, claims, comparisons = {}, {}, 0
    if candidate in ("adjacent-burn", "envelope-batch-field"):
        retained = 1
        for i, (k, _, v) in items:
            if k != "payment":
                continue
            comparisons += 1
            prev = sequence[i - 1] if i > 0 else None
            if prev is not None and prev[0] == "burn" and prev[2] == v:
                joins[i] = i - 1
                claims[i - 1] = claims.get(i - 1, 0) + 1
    elif candidate == "unique-value-burn":
        retained = len(burns) + sum(1 for k, _, _ in sequence if k == "payment")
        payments = [(i, v) for i, (k, _, v) in items if k == "payment"]
        for i, v in payments:
            matches = [b for b, bv in burns if bv == v]
            comparisons += len(burns)
            same_value_payments = [p for p, pv in payments if pv == v]
            if len(matches) == 1 and len(same_value_payments) == 1:
                joins[i] = matches[0]
                claims[matches[0]] = claims.get(matches[0], 0) + 1
    elif candidate == "all-batch-events":
        retained = len(sequence)
        for i, (k, _, v) in items:
            if k not in BATCH_KINDS:
                continue
            comparisons += len(burns)
            # the issue-literal reading: every batch event claims the nearest earlier burn
            earlier = [b for b, _ in burns if b < i]
            if earlier:
                joins[i] = earlier[-1]
                claims[earlier[-1]] = claims.get(earlier[-1], 0) + 1
    else:
        raise ValueError(candidate)
    return joins, comparisons, retained, claims


def determinism(candidate):
    for sequence in SOURCE_SPECIMENS.values():
        joins, _, _, claims = pair(candidate, sequence)
        payments = [i for i, (k, _, _) in enumerate(sequence) if k == "payment"]
        burns = [i for i, (k, _, _) in enumerate(sequence) if k == "burn"]
        if any(i not in joins for i in payments):
            return False
        if any(claims.get(b, 0) != 1 for b in burns):
            return False
    return True


def single_claim(candidate):
    for sequence in list(SOURCE_SPECIMENS.values()) + list(HOSTILE_SPECIMENS.values()):
        _, _, _, claims = pair(candidate, sequence)
        if any(count > 1 for count in claims.values()):
            return False
    return True


def recovery(candidate):
    """Hostile pairs must end as a recorded gap: no join, no exception."""
    expectations = {
        "burn-after-payment": set(),
        "burn-value-changed": set(),
        "burn-without-payment": set(),
        "two-burns-one-payment": {(2, 1)},
        "payment-without-burn": set(),
    }
    for name, sequence in HOSTILE_SPECIMENS.items():
        try:
            joins, _, _, _ = pair(candidate, sequence)
        except Exception:
            return False
        if candidate == "all-batch-events":
            joins = {p: b for p, b in joins.items() if sequence[p][0] == "payment"}
        if set(joins.items()) != expectations[name]:
            return False
    return True


def envelope(candidate):
    return candidate != "envelope-batch-field"


def existing_rows(candidate):
    """The current seventeen-rule rows are byte-identical after the candidate's pass."""
    from tabularium_lib.core import canonical_json
    from tabularium_lib.wildcat_rows import map_records
    from wildcat_v3_fixtures import constructed_inputs

    for venue in ("wildcat-v1", "wildcat-v2"):
        before = map_records(venue, *constructed_inputs(venue, routing=True))["events"]
        after = []
        for row in before:
            row = json.loads(canonical_json(row))
            if candidate == "envelope-batch-field":
                row["schema_version"] = 4
                row["batch"] = None
            after.append(row)
        if [canonical_json(r) for r in before] != [canonical_json(r) for r in after]:
            return False
    return True


def comparisons(candidate):
    return sum(pair(candidate, s)[1] for s in SOURCE_SPECIMENS.values())


def retained(candidate):
    return max(pair(candidate, s)[2] for s in SOURCE_SPECIMENS.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if os.path.lexists(args.report):
        parser.exit(2, "report path already exists: " + args.report + "\n")
    unit, function = CRITERIA[args.criterion]
    value = globals()[function](args.candidate)
    command = "python3 .hexaemeron/design/batch_join_probe.py --candidate %s --criterion %s --report %s" % (
        args.candidate, args.criterion, args.report)
    payload = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
               "criterion": args.criterion, "value": value, "unit": unit, "command": command, "exit": 0}
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    print(json.dumps({"report": args.report, "value": value, "sha256": hashlib.sha256(data).hexdigest()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
