"""Supporting sanctions relations over complete native keys and unique groups."""

from collections import defaultdict

QUEUED_SIGNATURE = "SanctionedAccountAssetsQueuedForWithdrawal(address,uint256,uint256,uint256)"
ESCROW_SIGNATURE = "SanctionedAccountAssetsSentToEscrow(address,address,uint256)"
QUEUE_SIGNATURE = "WithdrawalQueued(uint256,address,uint256,uint256)"
TRANSFER_SIGNATURE = "Transfer(address,address,uint256)"
QUEUE_RULE = "same-market-transaction-account-expiry-scaled-normalized"
ESCROW_RULE = "same-market-transaction-account-escrow-amount"
COMPANIONS = (QUEUED_SIGNATURE, ESCROW_SIGNATURE)


def _conditions(venue, item, queue, companion):
    values = item["values"]
    common = {"generation": venue, "market": item["emitter"],
              "transaction_hash": item["transaction"]["hash"]}
    if queue:
        return {**common, "account": values["account"], "expiry": values["expiry"],
                "scaled_amount": values["scaledAmount"],
                "normalized_amount": values["normalizedAmount"]}
    return {**common, "account": values["account"] if companion else values["from"],
            "escrow": values["escrow"] if companion else values["to"],
            "amount": values["amount"] if companion else values["value"]}


def relations(venue, decoded):
    """Return reciprocal relations and one stable gap per unmatched companion."""
    primary, companions = defaultdict(list), defaultdict(list)
    for item in decoded:
        if item["definition"] is None or item["context"]["role"] != "market":
            continue
        signature = item["definition"]["signature"]
        if signature not in (*COMPANIONS, QUEUE_SIGNATURE, TRANSFER_SIGNATURE):
            continue
        queue = signature in (QUEUED_SIGNATURE, QUEUE_SIGNATURE)
        if queue and venue != "wildcat-v2":
            continue
        companion = signature in COMPANIONS
        conditions = _conditions(venue, item, queue, companion)
        key = (queue, *conditions.values())
        (companions if companion else primary)[key].append((item, conditions))
    joined, gaps = defaultdict(list), {}
    for key, group in companions.items():
        candidates = primary[key]
        queue = key[0]
        prefix = "routing:sanctioned-assets-" + ("queued-for-withdrawal" if queue else "sent-to-escrow")
        if len(group) != 1 or len(candidates) != 1:
            reason = "ambiguous-match" if len(group) > 1 or len(candidates) > 1 else "missing-primary"
            for companion, _ in group:
                gaps[companion["selector"]] = prefix + ":" + reason
            continue
        (companion, conditions), (item, _) = group[0], candidates[0]
        relation = {"evidence_class": "join-inference",
                    "rule": QUEUE_RULE if queue else ESCROW_RULE,
                    "primary_selector": item["selector"],
                    "companion_selector": companion["selector"],
                    "conditions": conditions}
        joined[item["selector"]].append(relation)
        joined[companion["selector"]].append(relation)
    return dict(joined), gaps
