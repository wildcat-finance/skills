"""The twenty-five generation and emitter-role qualified Wildcat tuples."""

from .wildcat_abi import VARIANTS, abi_variant_for

from .wildcat_parameters import ADAPTER_VERSION, LEGACY_VERSION, NATIVE_RULES, checked_version

CHAIN = "ethereum-mainnet"
SOURCE_API = "ethereum-json-rpc"
EVIDENCE_CLASS = "hosted-rpc-reported-log-scope"

# Amount kinds name native units; none performs an accounting conversion.
# The four withdrawal-batch tuples follow the seventeen released ones so the
# released rule identifiers and their order stay as published under 1.0.0.
_MARKET = (
    ("deposit", "deposit", "Deposit(address,uint256,uint256)",
     ("depositor", "minted-token-account"), ("assets", "scaled-claims")),
    ("withdrawal-queued", "exit-queue", "WithdrawalQueued(uint256,address,uint256,uint256)",
     ("withdrawing-account",), ("normalized-claims", "scaled-claims")),
    ("withdrawal-executed", "exit-execute", "WithdrawalExecuted(uint256,address,uint256)",
     ("beneficiary",), ("assets",)),
    ("transfer", "transfer", "Transfer(address,address,uint256)",
     ("from", "to"), ("market-token-claims",)),
    ("borrow", "borrowing", "Borrow(uint256)", ("pool",), ("assets",)),
    ("debt-repaid", "repayment", "DebtRepaid(address,uint256)",
     ("payer", "pool"), ("assets",)),
    ("market-closed", "pool-state", "MarketClosed(uint256)", ("pool",), ()),
    ("withdrawal-batch-created", "exit-queue", "WithdrawalBatchCreated(uint256)", ("pool",), ()),
    ("withdrawal-batch-payment", "exit-queue", "WithdrawalBatchPayment(uint256,uint256,uint256)",
     ("pool",), ("burned-scaled-claims", "reserved-assets")),
    ("withdrawal-batch-expired", "exit-queue", "WithdrawalBatchExpired(uint256,uint256,uint256,uint256)",
     ("pool",), ("scaled-claims", "burned-scaled-claims", "reserved-assets")),
    ("withdrawal-batch-closed", "exit-queue", "WithdrawalBatchClosed(uint256)", ("pool",), ()),
)
_WRAPPER = (
    ("wrapper-deposit", "deposit", "Deposit(address,address,uint256,uint256)",
     ("caller", "owner"), ("market-token-assets", "wrapper-shares")),
    ("wrapper-withdrawal", "exit-execute", "Withdraw(address,address,address,uint256,uint256)",
     ("caller", "receiver", "owner"), ("market-token-assets", "wrapper-shares")),
    ("wrapper-transfer", "transfer", "Transfer(address,address,uint256)",
     ("from", "to"), ("wrapper-shares",)),
)
RULES = {}
for _venue in ("wildcat-v1", "wildcat-v2"):
    for _role, _declarations in (("market", _MARKET), ("wrapper", _WRAPPER if _venue == "wildcat-v2" else ())):
        for _action, _family, _signature, _parties, _amounts in _declarations:
            RULES[(_venue, _action)] = {
                "venue": _venue, "role": _role, "action": _venue + "." + _action,
                "family": _family, "signature": _signature,
                "rule": _venue + "." + _action + ".v1",
                "party_roles": _parties, "amount_kinds": _amounts,
                "instrument_type": _venue + "-" + _role,
            }

PRIMARY_CONTEXTS = tuple(sorted((v["venue"], v["role"], v["signature"]) for v in RULES.values()))
BY_SIGNATURE = {(v["venue"], v["role"], v["signature"]): v for v in RULES.values()}
ROUTING_SIGNATURE = "SanctionedAccountWithdrawalSentToEscrow(address,address,uint32,uint256)"
DISPOSITIONS = ("primary", "supporting-routing", "unsupported-canonical-meaning", "unsupported-decode")
# The market burn a batch payment claims: Transfer(market, 0x0, normalizedAmountPaid)
# emitted at the log index before the payment, by the same market, in the same
# transaction. The six conditions are the emission order of
# _applyWithdrawalBatchPayment in both deployed generations.
BURN_SIGNATURE = "Transfer(address,address,uint256)"
BATCH_PAYMENT_SIGNATURE = "WithdrawalBatchPayment(uint256,uint256,uint256)"
BURN_JOIN_RULE = "adjacent-market-burn"
ZERO_ADDRESS = "0x" + "00" * 20


def rules(version=ADAPTER_VERSION):
    """Return the exact meanings admitted by one supported interpretation."""
    checked_version(version)
    return RULES if version == LEGACY_VERSION else {**RULES, **NATIVE_RULES}


def by_signature(version=ADAPTER_VERSION):
    return {(v["venue"], v["role"], v["signature"]): v for v in rules(version).values()}
