"""Constructed withdrawal-batch transactions in the pinned source emission order.

Every sequence here is built from the V1 and V2 market source the adapter pins,
not from a retained capture. A step is one tuple naming its kind; a transaction
is a list of steps, and a specimen is one or more transactions in one block.
"""

from copy import deepcopy

from wildcat_v3_fixtures import (
    ACCOUNT, MARKET, OTHER, PAYER, WRAPPER, ZERO, constructed_inputs, log, record,
)


CREATED = "WithdrawalBatchCreated(uint256)"
PAYMENT = "WithdrawalBatchPayment(uint256,uint256,uint256)"
EXPIRED = "WithdrawalBatchExpired(uint256,uint256,uint256,uint256)"
CLOSED = "WithdrawalBatchClosed(uint256)"
TRANSFER = "Transfer(address,address,uint256)"
QUEUED = "WithdrawalQueued(uint256,address,uint256,uint256)"
REPAID = "DebtRepaid(address,uint256)"
MARKET_CLOSED = "MarketClosed(uint256)"
BATCH_SIGNATURES = (CREATED, PAYMENT, EXPIRED, CLOSED)
SECOND_MARKET = "0x" + "99" * 20

# Source order. V1 queueWithdrawal emits the queue transfer before
# WithdrawalBatchCreated; V2 emits WithdrawalBatchCreated first. Both emit the
# burn immediately before WithdrawalBatchPayment inside
# _applyWithdrawalBatchPayment, and neither gives created, expired or closed a
# burn of its own.
SOURCE_SPECIMENS = {
    "v1-queue-first-batch": [("transfer", ACCOUNT, MARKET, 70), ("created", 100), ("queued", 100, 70, 70),
                             ("burn", 40), ("payment", 100, 40, 40)],
    "v2-queue-first-batch": [("created", 100), ("transfer", ACCOUNT, MARKET, 70), ("queued", 100, 70, 70),
                             ("burn", 40), ("payment", 100, 40, 40)],
    # repayAndProcessUnpaidWithdrawalBatches paying two batches owed equal amounts
    "repay-two-unpaid-equal-amounts": [("repaid", 80), ("burn", 40), ("payment", 100, 40, 40), ("closed", 100),
                                       ("burn", 40), ("payment", 200, 40, 40), ("closed", 200)],
    # queueWithdrawal: _getUpdatedState pays the pending batch, the queue adds to it and pays again
    "queue-double-payment-same-expiry": [("burn", 10), ("payment", 300, 10, 10), ("transfer", ACCOUNT, MARKET, 20),
                                         ("queued", 300, 20, 20), ("burn", 10), ("payment", 300, 10, 10)],
    # expiry processing then closure of a fully paid batch
    "expired-paid-closed": [("burn", 25), ("payment", 400, 25, 25), ("expired", 400, 25, 25, 25), ("closed", 400)],
    # V2 closeMarket: pending batch paid, expired, closed, new one-second batch created
    "v2-close-market": [("burn", 15), ("payment", 500, 15, 15), ("expired", 500, 15, 15, 15), ("closed", 500),
                        ("created", 501)],
}
HOSTILE_SPECIMENS = {
    "burn-after-payment": [("payment", 100, 40, 40), ("burn", 40)],
    "burn-value-changed": [("burn", 41), ("payment", 100, 40, 40)],
    "burn-without-payment": [("transfer", ACCOUNT, OTHER, 5), ("burn", 40)],
    "two-burns-one-payment": [("burn", 40), ("burn", 40), ("payment", 100, 40, 40)],
    "payment-without-burn": [("queued", 100, 40, 40), ("payment", 100, 40, 40)],
}


def step_log(step, index, emitter=MARKET):
    kind = step[0]
    if kind == "created":
        return log(CREATED, (step[1],), (), emitter, index)
    if kind == "payment":
        return log(PAYMENT, (step[1],), (step[2], step[3]), emitter, index)
    if kind == "expired":
        return log(EXPIRED, (step[1],), (step[2], step[3], step[4]), emitter, index)
    if kind == "closed":
        return log(CLOSED, (step[1],), (), emitter, index)
    if kind == "burn":
        return log(TRANSFER, (emitter, ZERO), (step[1],), emitter, index)
    if kind == "transfer":
        return log(TRANSFER, (step[1], step[2]), (step[3],), emitter, index)
    if kind == "queued":
        return log(QUEUED, (step[1], ACCOUNT), (step[2], step[3]), emitter, index)
    if kind == "repaid":
        return log(REPAID, (PAYER,), (step[1],), emitter, index)
    if kind == "market-closed":
        return log(MARKET_CLOSED, (), (step[1],), emitter, index)
    raise ValueError(kind)


def raws_for(transactions, emitter=MARKET):
    """Block-wide log indices across one or more transactions, in emission order."""
    raws, index = [], 0
    for position, steps in enumerate(transactions):
        for step in steps:
            raw = step_log(step, index, emitter)
            raw["transactionHash"] = "0x" + ("%02x" % (0xb0 + position)) * 32
            raw["transactionIndex"] = hex(2 + position)
            raws.append(raw)
            index += 1
    return raws


def batch_records(venue, transactions, emitter=MARKET):
    contexts, _ = constructed_inputs(venue)
    if emitter != MARKET and emitter not in contexts:
        contexts[emitter] = deepcopy(contexts[MARKET])
    return contexts, [record(raw) for raw in raws_for(transactions, emitter)]


def specimen(venue, name):
    return batch_records(venue, [SOURCE_SPECIMENS[name]])


def hostile(venue, name):
    return batch_records(venue, [HOSTILE_SPECIMENS[name]])


def wrapper_burn_then_payment():
    """A V2 wrapper burn at the index before a market payment; the wrapper is not the market."""
    contexts, _ = constructed_inputs("wildcat-v2")
    raws = [log(TRANSFER, (WRAPPER, ZERO), (40,), WRAPPER, 0), log(PAYMENT, (100,), (40, 40), MARKET, 1)]
    return contexts, [record(raw) for raw in raws]


def rows(result, action):
    return [event for event in result["events"] if event["action"].endswith("." + action)]


def row(result, action):
    (event,) = rows(result, action)
    return event


def burn_rows(result):
    return [event for event in result["events"] if event["action"].endswith(".transfer")
            and event["parties"][0]["address"] == event["instrument"]["id"]
            and event["parties"][1]["address"] == ZERO]


def mapping_for(result, event):
    return next(item for item in result["mapping_records"]
                if item["source_selector"] == event["provenance"]["source_selector"])
