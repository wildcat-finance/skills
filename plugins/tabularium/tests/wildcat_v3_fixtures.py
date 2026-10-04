"""Labelled constructed native logs; these are not historical capture evidence."""

from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from tabularium_lib.core import canonical_json, sha256_bytes
from tabularium_lib.keccak import keccak256
from tabularium_lib.wildcat_abi import abi_variant_for
from tabularium_lib.wildcat_rows import map_records


MARKET = "0x" + "11" * 20
WRAPPER = "0x" + "22" * 20
ASSET = "0x" + "33" * 20
ACCOUNT = "0x" + "44" * 20
PAYER = "0x" + "55" * 20
OTHER = "0x" + "66" * 20
DEBTOR = "0x" + "77" * 20
ESCROW = "0x" + "88" * 20
ZERO = "0x" + "00" * 20
V1_COMMIT = "da74452aa7d1a0f024d99efd22cc6d950a8116b7"
V2_COMMIT = "a70f297fbd1b1ab597e0e9a3458a2d13a34b4657"
WRAPPER_COMMIT = "c7be4039f8f383a9dda4e45f63331c17d63f9ed9"


def word(value):
    if isinstance(value, str) and value.startswith("0x"):
        value = int(value, 16)
    return int(value).to_bytes(32, "big").hex()


def log(signature, indexed=(), data=(), emitter=MARKET, index=0):
    return {
        "address": emitter, "blockNumber": "0x64", "blockHash": "0x" + "aa" * 32,
        "transactionHash": "0x" + "bb" * 32, "transactionIndex": "0x2", "logIndex": hex(index),
        "removed": False, "topics": ["0x" + keccak256(signature.encode()).hex()] + ["0x" + word(v) for v in indexed],
        "data": "0x" + "".join(word(v) for v in data),
    }


def reference(raw, index):
    return {"component": "native-logs", "component_sha256": "sha256:" + "a" * 64,
            "capture_id": "sha256:" + "b" * 64,
            "evidence_class": "recorded:constructed-fixture",
            "journal_selector": "/records/0/response",
            "response_sha256": "sha256:" + sha256_bytes(canonical_json(raw)),
            "selector": "/result/%d" % index}


def record(raw, index=None):
    index = int(raw["logIndex"], 16) if index is None else index
    return raw, reference(raw, index)


def constructed_inputs(venue="wildcat-v2", routing=False):
    """Return declared fixture contexts and independent ABI-encoded primary logs."""
    commit = V1_COMMIT if venue == "wildcat-v1" else V2_COMMIT
    market_variant = abi_variant_for(venue, "market", "WildcatMarket", commit)
    contexts = {MARKET: {"role": "market", "asset": ASSET, "market": None,
                         "concrete_contract": "WildcatMarket", "abi_variant": market_variant,
                         "source": [{"class": "declared-constructed-context", "fixture": venue,
                                     "native": {"address": MARKET, "source_commit": commit}}],
                         "borrower_context": {"class": "registry-inferred", "borrower": DEBTOR}}}
    raws = [
        log("Deposit(address,uint256,uint256)", (ACCOUNT,), (100, 90), index=0),
        log("WithdrawalQueued(uint256,address,uint256,uint256)", (123, ACCOUNT), (70, 80), index=1),
        log("WithdrawalExecuted(uint256,address,uint256)", (123, ACCOUNT), (50,), index=2),
        log("Transfer(address,address,uint256)", (ACCOUNT, OTHER), (30,), index=3),
        log("Borrow(uint256)", (), (75,), index=4),
        log("DebtRepaid(address,uint256)", (PAYER,), (25,), index=5),
        log("MarketClosed(uint256)", (), (1730000000,), index=6),
    ]
    if venue == "wildcat-v2":
        contexts[WRAPPER] = {"role": "wrapper", "asset": MARKET, "market": MARKET,
                             "concrete_contract": "Wildcat4626Wrapper",
                             "abi_variant": abi_variant_for(venue, "wrapper", "Wildcat4626Wrapper", WRAPPER_COMMIT),
                             "source": [{"class": "declared-constructed-context", "fixture": venue,
                                         "native": {"address": WRAPPER, "source_commit": WRAPPER_COMMIT}}]}
        raws.extend((
            log("Deposit(address,address,uint256,uint256)", (PAYER, ACCOUNT), (100, 80), WRAPPER, 7),
            log("Withdraw(address,address,address,uint256,uint256)", (PAYER, OTHER, ACCOUNT), (60, 45), WRAPPER, 8),
            log("Transfer(address,address,uint256)", (ACCOUNT, OTHER), (5,), WRAPPER, 9),
        ))
    if routing:
        raws.append(log("SanctionedAccountWithdrawalSentToEscrow(address,address,uint32,uint256)",
                        (ACCOUNT,), (ESCROW, 123, 50), index=len(raws)))
    return contexts, [record(raw) for raw in raws]


def all_primary_events():
    return tuple(event for venue in ("wildcat-v1", "wildcat-v2")
                 for event in map_records(venue, *constructed_inputs(venue))["events"])


def copy_inputs(venue="wildcat-v2", routing=False):
    return deepcopy(constructed_inputs(venue, routing))
