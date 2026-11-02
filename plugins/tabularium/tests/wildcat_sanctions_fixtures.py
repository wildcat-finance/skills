"""Constructed sanctions companions; no historical emission is claimed."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wildcat_v3_fixtures import (ACCOUNT, ESCROW, MARKET, ZERO, constructed_inputs,
                                 log, record)

QUEUED = "SanctionedAccountAssetsQueuedForWithdrawal(address,uint256,uint256,uint256)"
ESCROWED = "SanctionedAccountAssetsSentToEscrow(address,address,uint256)"
QUEUE = "WithdrawalQueued(uint256,address,uint256,uint256)"
TRANSFER = "Transfer(address,address,uint256)"


def raws(venue, *, overlap=False):
    if overlap:
        return [log(TRANSFER, (MARKET, ZERO), (40,), index=0),
                log("WithdrawalBatchPayment(uint256,uint256,uint256)", (123,), (35, 40), index=1),
                log(ESCROWED, (MARKET,), (ZERO, 40), index=2)]
    result = [log(TRANSFER, (ACCOUNT, ESCROW), (40,), index=0),
              log(ESCROWED, (ACCOUNT,), (ESCROW, 40), index=2)]
    if venue == "wildcat-v2":
        result.extend([log(QUEUE, (123, ACCOUNT), (70, 80), index=3),
                       log("WithdrawalBatchCreated(uint256)", (123,), (), index=4),
                       log(QUEUED, (ACCOUNT,), (123, 70, 80), index=6)])
    return result


def inputs(venue="wildcat-v2", *, overlap=False):
    contexts, _ = constructed_inputs(venue)
    return contexts, [record(raw) for raw in raws(venue, overlap=overlap)]


def raw_release(base, venue="wildcat-v2"):
    from test_wildcat_v3_release import constructed_release
    from tabularium_lib.core import canonical_json

    def replace(document, journal, plan):
        response = json.loads(journal["records"][0]["response"])
        response["result"] = raws(venue)
        journal["records"][0]["response"] = canonical_json(response).decode()
        plan["release"]["name"] = venue + "-constructed-sanctions"
    return constructed_release(base, venue, replace)
