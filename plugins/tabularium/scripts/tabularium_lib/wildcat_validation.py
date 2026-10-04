"""Closed Wildcat row tuples, separate from reconstruction of raw evidence."""

import re

from .core import MAX_SAFE_INTEGER, TabulariumError


ADAPTER_VERSION = "1.0.0"
SOURCE_API = "ethereum-json-rpc"
CHAIN = "ethereum-mainnet"
KNOWN_GAPS = (
    "the provider reported the logs and block hashes; this release does not independently prove the chain boundary",
    "the retained interval is not complete venue, account or lifetime history",
    "emitted payer and claim account do not establish debtor, executor or ultimate cash recipient without separately sourced routing evidence",
    "market-token claims and wrapper assets or shares do not establish underlying cash flow or shareholder look-through",
    "market closure does not establish settlement; an expired unprocessed V1 withdrawal batch can remain unpaid",
    "the release is unsigned; offline verification proves internal consistency, not publisher identity or authenticity",
)

# Each tuple fixes native party roles and financial units. Addresses, decoded
# quantities and joins are reconstructed from preserved journals by the release
# verifier; this table never supplies missing actor or asset evidence.
# Asset flags are True for a required token, False for assetless scaled claims,
# and None for an underlying asset that may remain unknown with an attribution gap.
MARKET_TUPLES = {
    "deposit": ("deposit", ("depositor", "minted-token-account"), (("assets", None), ("scaled-claims", False))),
    "withdrawal-queued": ("exit-queue", ("withdrawing-account",), (("normalized-claims", True), ("scaled-claims", False))),
    "withdrawal-executed": ("exit-execute", ("beneficiary",), (("assets", None),)),
    "transfer": ("transfer", ("from", "to"), (("market-token-claims", True),)),
    "borrow": ("borrowing", ("pool",), (("assets", None),)),
    "debt-repaid": ("repayment", ("payer", "pool"), (("assets", None),)),
    "market-closed": ("pool-state", ("pool",), ()),
}
WRAPPER_TUPLES = {
    "wrapper-deposit": ("deposit", ("caller", "owner"), (("market-token-assets", True), ("wrapper-shares", True))),
    "wrapper-withdrawal": ("exit-execute", ("caller", "receiver", "owner"), (("market-token-assets", True), ("wrapper-shares", True))),
    "wrapper-transfer": ("transfer", ("from", "to"), (("wrapper-shares", True),)),
}
SIGNATURES = {
    "deposit": "Deposit(address,uint256,uint256)",
    "withdrawal-queued": "WithdrawalQueued(uint256,address,uint256,uint256)",
    "withdrawal-executed": "WithdrawalExecuted(uint256,address,uint256)",
    "transfer": "Transfer(address,address,uint256)",
    "borrow": "Borrow(uint256)",
    "debt-repaid": "DebtRepaid(address,uint256)",
    "market-closed": "MarketClosed(uint256)",
    "wrapper-deposit": "Deposit(address,address,uint256,uint256)",
    "wrapper-withdrawal": "Withdraw(address,address,address,uint256,uint256)",
    "wrapper-transfer": "Transfer(address,address,uint256)",
}
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
HASH = re.compile(r"^0x[0-9a-f]{64}$")
DECIMAL = re.compile(r"^(0|[1-9][0-9]*)$")
MAX_UINT256 = (1 << 256) - 1
JOURNAL_SELECTOR = re.compile(r"^wildcat-journal:[0-9a-f]{64}$")
SUPPORT_SELECTOR = re.compile(r"^wildcat-(?:context|journal):[0-9a-f]{64}$")


def tuples(venue):
    if venue == "wildcat-v1":
        return MARKET_TUPLES
    if venue == "wildcat-v2":
        return {**MARKET_TUPLES, **WRAPPER_TUPLES}
    raise TabulariumError("unsupported Wildcat venue %r" % venue)


def mappings(venue):
    return {
        action: (family, "%s.%s" % (venue, action), "%s.%s.v1" % (venue, action))
        for action, (family, _, _) in tuples(venue).items()
    }


def _fail(where, field, reason):
    raise TabulariumError("%s field %s %s" % (where, field, reason))


def _closed(value, names, where, field):
    if not isinstance(value, dict):
        _fail(where, field, "is not an object")
    missing = set(names) - set(value)
    extra = set(value) - set(names)
    if missing:
        _fail(where, "%s.%s" % (field, sorted(missing)[0]), "is missing")
    if extra:
        _fail(where, "%s.%s" % (field, sorted(extra, key=str)[0]), "is not admitted")


def _text(value, where, field, pattern=None):
    if not isinstance(value, str) or not value:
        _fail(where, field, "is not a non-empty string")
    if pattern is not None and not pattern.fullmatch(value):
        _fail(where, field, "has an unsupported lexical form")


def _integer(value, where, field):
    if type(value) is not int or not 0 <= value <= MAX_SAFE_INTEGER:
        _fail(where, field, "is not a non-negative safe JSON integer")


def validate_row(row, venue, schema_version, index=1):
    where = "canonical row %d" % index
    if schema_version != 3 or type(row["schema_version"]) is not int:
        _fail(where, "schema_version", "is not the Wildcat schema 3 envelope")
    _text(row["id"], where, "id")
    if row["chain"] != CHAIN:
        _fail(where, "chain", "is not Ethereum mainnet")
    options = mappings(venue)
    action = row["action"]
    selected = next((name for name, item in options.items() if item[1] == action), None)
    if selected is None:
        _fail(where, "action", "is not in the Wildcat tuple table")
    family, roles, amounts = tuples(venue)[selected]
    if row["event_family"] != family:
        _fail(where, "event_family", "does not match its Wildcat action")
    provenance = row["provenance"]
    if provenance["mapping_rule"] != options[selected][2]:
        _fail(where, "provenance.mapping_rule", "does not match its Wildcat action")
    for name in ("source_kind", "source_entity", "source_id", "source_selector"):
        _text(provenance[name], where, "provenance." + name)
    if provenance["source_kind"] != "ethereum-log":
        _fail(where, "provenance.source_kind", "is not the admitted native log kind")
    if provenance["source_entity"] != SIGNATURES[selected]:
        _fail(where, "provenance.source_entity", "does not match its concrete event signature")
    _text(provenance["source_selector"], where, "provenance.source_selector", JOURNAL_SELECTOR)
    _text(provenance["source_contract"], where, "provenance.source_contract", ADDRESS)
    selectors = provenance["supporting_selectors"]
    if not isinstance(selectors, list):
        _fail(where, "provenance.supporting_selectors", "is not an array")
    for selector in selectors:
        _text(selector, where, "provenance.supporting_selectors", SUPPORT_SELECTOR)
    if len(selectors) != len(set(selectors)):
        _fail(where, "provenance.supporting_selectors", "contains repeated selectors")
    transaction = row["transaction"]
    _closed(transaction, ("hash", "block_number", "block_hash", "transaction_index", "log_index", "timestamp"), where, "transaction")
    for name in ("hash", "block_hash"):
        _text(transaction[name], where, "transaction." + name, HASH)
    for name in ("block_number", "transaction_index", "log_index"):
        _integer(transaction[name], where, "transaction." + name)
    if transaction["timestamp"] is not None:
        _fail(where, "transaction.timestamp", "has no admitted timestamp evidence")
    parties = row["parties"]
    if not isinstance(parties, list):
        _fail(where, "parties", "is not an array")
    expected_roles = roles
    if selected == "withdrawal-executed" and len(parties) == 2:
        expected_roles = (*roles, "escrow-recipient")
    if len(parties) != len(expected_roles):
        _fail(where, "parties", "does not have the action's exact party count")
    for position, (party, role) in enumerate(zip(parties, expected_roles)):
        field = "parties.%d" % position
        _closed(party, ("role", "address"), where, field)
        if party["role"] != role:
            _fail(where, field + ".role", "does not match its native action")
        _text(party["address"], where, field + ".address", ADDRESS)
    instrument = row["instrument"]
    _closed(instrument, ("type", "id"), where, "instrument")
    expected_type = "%s-%s" % (venue, "wrapper" if selected in WRAPPER_TUPLES else "market")
    if instrument["type"] != expected_type:
        _fail(where, "instrument.type", "does not match its emitter role")
    _text(instrument["id"], where, "instrument.id", ADDRESS)
    raw_amounts = row["amounts"]
    if not isinstance(raw_amounts, list) or len(raw_amounts) != len(amounts):
        _fail(where, "amounts", "does not have the action's exact financial amount count")
    for position, (amount, (kind, has_asset)) in enumerate(zip(raw_amounts, amounts)):
        field = "amounts.%d" % position
        _closed(amount, ("kind", "base_units", "asset"), where, field)
        if amount["kind"] != kind:
            _fail(where, field + ".kind", "does not match its native financial unit")
        _text(amount["base_units"], where, field + ".base_units", DECIMAL)
        if len(amount["base_units"]) > 78 or int(amount["base_units"]) > MAX_UINT256:
            _fail(where, field + ".base_units", "exceeds uint256")
        if has_asset or (has_asset is None and amount["asset"] is not None):
            _text(amount["asset"], where, field + ".asset", ADDRESS)
        elif has_asset is False and amount["asset"] is not None:
            _fail(where, field + ".asset", "must be null for scaled accounting claims")
    if not isinstance(row["native_record"], dict):
        _fail(where, "native_record", "is not an object")
    return row
