"""Constructed fee logs and raw releases; none is a historical observation."""

import json
from pathlib import Path
import tempfile

from wildcat_v3_fixtures import ACCOUNT, MARKET, PAYER, constructed_inputs, log, record
from test_wildcat_v3_release import constructed_release
from tabularium_lib.core import canonical_json

FEES = "FeesCollected(uint256)"
BIPS = "ProtocolFeeBipsUpdated(uint256)"
VENUES = ("wildcat-v1", "wildcat-v2")


def fee_raws(venue):
    raws = [log(FEES, (), (73,), MARKET, 0),
            log("DebtRepaid(address,uint256)", (PAYER,), (73,), MARKET, 1),
            log("WithdrawalExecuted(uint256,address,uint256)", (100, ACCOUNT), (73,), MARKET, 2)]
    if venue == "wildcat-v2":
        raws.append(log(BIPS, (), (125,), MARKET, 3))
    return raws


def fee_records(venue, missing_asset=False):
    contexts, _ = constructed_inputs(venue)
    if missing_asset:
        contexts[MARKET]["asset"] = None
    return contexts, [record(raw) for raw in fee_raws(venue)]


def fee_raw_release(base, venue, missing_asset=False):
    def mutate(document, journal, plan):
        response = json.loads(journal["records"][0]["response"])
        response["result"] = fee_raws(venue)
        journal["records"][0]["response"] = canonical_json(response).decode()
        plan["release"]["name"] = venue + "-constructed-fees"
        if missing_asset:
            for context in document["contexts"]:
                if context["address"] == MARKET:
                    context["asset"] = None
    return constructed_release(Path(base), venue, mutate)
