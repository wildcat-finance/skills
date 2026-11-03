"""Map the MarketState a Wildcat V2 market passes to its hooks instance.

Adapter `1.5.0` reads recorded trace frames in which a registered V2 market
calls its hooks instance under one of five hooks, and keeps the `MarketState`
argument as one state observation in exact native units. The signatures follow
`src/access/IHooks.sol`, the field order and widths
`src/libraries/MarketState.sol`, and the calldata offsets the encoders in
`src/types/HooksConfig.sol`, all at v2-protocol commit
a70f297fbd1b1ab597e0e9a3458a2d13a34b4657. No target source is copied here: only
the digests of those three units and the constants they fix.

The market writes the hook calldata itself: the selector, the leading
arguments, the fourteen-word state copied from memory, the `extraData` offset
and length words, then `extraData` unpadded. A frame that departs from that
layout is refused, the way a malformed accepted log ABI is refused.
"""

from copy import deepcopy
import re

from .core import MAX_SAFE_INTEGER, TabulariumError
from .keccak import keccak256
from .wildcat_rows import context_selector, selector


PIN = "a70f297fbd1b1ab597e0e9a3458a2d13a34b4657"
SOURCE = {
    "repository": "wildcat-finance/v2-protocol",
    "commit": PIN,
    "units": {
        "src/access/IHooks.sol": "b7c2028d5670c62fbbe43805f36576b638e6cced3507e773b8d158e66dcc193c",
        "src/libraries/MarketState.sol": "1aa122075f0c45098599aff3df10fe86744d168a8bbe61a12570116739a67b8c",
        "src/types/HooksConfig.sol": "ed5734a684ca96f502294930de30885c2fa9d924948a4a1a75aa628b5b3512e2",
    },
}
RULE = "wildcat-v2.hook-market-state.v1"
EVIDENCE_CLASS = "recorded-hook-call-input"
# `struct MarketState`, in declared order with declared widths.
MARKET_STATE = (
    ("isClosed", "bool"), ("maxTotalSupply", "uint128"), ("accruedProtocolFees", "uint128"),
    ("normalizedUnclaimedWithdrawals", "uint128"), ("scaledTotalSupply", "uint104"),
    ("scaledPendingWithdrawals", "uint104"), ("pendingWithdrawalExpiry", "uint32"),
    ("isDelinquent", "bool"), ("timeDelinquent", "uint32"), ("protocolFeeBips", "uint16"),
    ("annualInterestBips", "uint16"), ("reserveRatioBips", "uint16"), ("scaleFactor", "uint112"),
    ("lastInterestAccruedTimestamp", "uint32"),
)
MARKET_STATE_TYPE = "(" + ",".join(kind for _, kind in MARKET_STATE) + ")"
# The leading `IHooks` arguments of each mapped hook, and its selector as
# `cast sig` computes it; import fails if the two ever disagree. `onBorrow`,
# `onCloseMarket` and the other hooks stay unmapped.
HOOKS = (
    ("onDeposit", ("address", "uint256"), "0x5aeb713f"),
    ("onQueueWithdrawal", ("address", "uint32", "uint256"), "0x3521cccc"),
    ("onExecuteWithdrawal", ("address", "uint128"), "0x2970403d"),
    ("onTransfer", ("address", "address", "address", "uint256"), "0xa018f90e"),
    ("onRepay", ("uint256",), "0x83d9e1eb"),
)
STATE_BYTES = 32 * len(MARKET_STATE)
MAX_CALLDATA_BYTES = 64 * 1024
GAP_REASONS = ("caller-not-registered-market", "failed-call", "failed-ancestor")
LIMITATIONS = (
    "intermediateState is the state the market passed to its hook; it does not establish the state the market stores once the action completes.",
    "Each value keeps its MarketState name and native unit; no value is converted.",
    "The call's other arguments and extraData stay undecoded in native_record.",
)
SCOPE_LIMITATIONS = (
    "Only recorded successful calls from a registered V2 market to its hooks instance under onDeposit, onQueueWithdrawal, onTransfer, onExecuteWithdrawal or onRepay are observed.",
    "A hook the market's configuration leaves disabled makes no call, and a missing frame supplies no observation; no state is guessed for either.",
)
_ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}\Z")
_HASH = re.compile(r"0x[0-9a-fA-F]{64}\Z")
_QUANTITY = re.compile(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)\Z")
_CALLDATA = re.compile(r"0x(?:[0-9a-fA-F]{2})*\Z")

LAYOUTS = {}
for _name, _leading, _selector in HOOKS:
    _signature = "%s(%s)" % (_name, ",".join((*_leading, MARKET_STATE_TYPE, "bytes")))
    if "0x" + keccak256(_signature.encode()).hex()[:8] != _selector:
        raise TabulariumError("Wildcat hook selector does not match its signature")
    _state = 32 * len(_leading)
    # Offsets are within the argument head, after the four selector bytes.
    LAYOUTS[_selector] = {
        "hook": _name, "signature": _signature, "selector": _selector, "leading": _leading,
        "state_offset": _state, "extra_head": _state + STATE_BYTES,
        "base_size": 4 + _state + STATE_BYTES + 64,
    }


def _address(value, where):
    if not isinstance(value, str) or not _ADDRESS.fullmatch(value):
        raise TabulariumError("Wildcat hook call %s is not an address" % where)
    return value.lower()


def _quantity(value, where):
    if type(value) is int:
        number = value
    elif isinstance(value, str) and _QUANTITY.fullmatch(value) and len(value) <= 16:
        number = int(value, 16)
    else:
        raise TabulariumError("Wildcat hook call %s is not a bounded quantity" % where)
    if not 0 <= number <= MAX_SAFE_INTEGER:
        raise TabulariumError("Wildcat hook call %s exceeds the safe integer range" % where)
    return number


def _path(value):
    if (not isinstance(value, list) or len(value) > 1024
            or any(type(part) is not int or not 0 <= part <= MAX_SAFE_INTEGER for part in value)):
        raise TabulariumError("Wildcat hook call trace address is malformed")
    return list(value)


def candidate_selector(trace):
    """Return the mapped hook selector a frame's input starts with, never raising."""
    action = trace.get("action") if isinstance(trace, dict) else None
    value = action.get("input") if isinstance(action, dict) else None
    if not isinstance(value, str) or len(value) < 10:
        return None
    prefix = value[:10].lower()
    return prefix if prefix in LAYOUTS else None


def _identity(trace):
    if not isinstance(trace, dict) or not isinstance(trace.get("action"), dict):
        raise TabulariumError("Wildcat hook call frame is not an object with an action")
    values = {}
    for key, name in (("transactionHash", "hash"), ("blockHash", "block_hash")):
        value = trace.get(key)
        if not isinstance(value, str) or not _HASH.fullmatch(value):
            raise TabulariumError("Wildcat hook call frame has an invalid %s" % key)
        values[name] = value.lower()
    values["block_number"] = _quantity(trace.get("blockNumber"), "block number")
    values["transaction_index"] = _quantity(trace.get("transactionPosition"), "transaction position")
    values["trace_address"] = _path(trace.get("traceAddress"))
    return values


def _word(data, offset):
    return int.from_bytes(data[offset:offset + 32], "big")


def _check(number, kind, where):
    if kind == "bool":
        if number not in (0, 1):
            raise TabulariumError("Wildcat hook %s boolean is neither zero nor one" % where)
        return bool(number)
    if kind == "address":
        if number >> 160:
            raise TabulariumError("Wildcat hook %s address has nonzero padding" % where)
        return None
    if number >> int(kind[4:]):
        raise TabulariumError("Wildcat hook %s exceeds its declared width" % where)
    return str(number)


def market_state(layout, value):
    """Decode one hook frame's complete calldata; refuse anything off its layout."""
    if not isinstance(value, str) or not _CALLDATA.fullmatch(value):
        raise TabulariumError("Wildcat hook calldata is not hexadecimal bytes")
    if len(value) > 2 + 2 * MAX_CALLDATA_BYTES:
        raise TabulariumError("Wildcat hook calldata exceeds its byte budget")
    data = bytes.fromhex(value[2:])
    if data[:4].hex() != layout["selector"][2:]:
        raise TabulariumError("Wildcat hook calldata selector does not match its layout")
    if len(data) < layout["base_size"]:
        raise TabulariumError("Wildcat hook calldata is truncated before its MarketState and extraData head")
    head = data[4:]
    for position, kind in enumerate(layout["leading"]):
        _check(_word(head, 32 * position), kind, "%s argument %d" % (layout["hook"], position))
    state = {}
    for index, (name, kind) in enumerate(MARKET_STATE):
        state[name] = _check(_word(head, layout["state_offset"] + 32 * index), kind,
                             "%s MarketState.%s" % (layout["hook"], name))
    if _word(head, layout["extra_head"]) != layout["extra_head"] + 32:
        raise TabulariumError("Wildcat hook extraData offset does not match its layout")
    if _word(head, layout["extra_head"] + 32) != len(data) - layout["base_size"]:
        raise TabulariumError("Wildcat hook extraData length does not match the calldata")
    return state


def _supports(contexts, *addresses):
    result = []
    for address in addresses:
        for item in contexts[address].get("source", ()):
            value = context_selector(item)
            if value not in result:
                result.append(value)
    return result


def _hooks_word(context):
    """The hooks address the market's own deployment log names, when retained."""
    words = [item["values"]["hooks"] for item in context.get("source", ())
             if isinstance(item, dict) and item.get("class") == "inferred-deployment-asset"
             and isinstance(item.get("values"), dict) and "hooks" in item["values"]]
    if len(words) > 1:
        raise TabulariumError("Wildcat market has more than one deployment hooks word")
    if not words:
        return None
    word = words[0]
    if not isinstance(word, str) or not re.fullmatch(r"0x[0-9a-f]{64}", word):
        raise TabulariumError("Wildcat market deployment hooks word is malformed")
    return "0x" + word[2:42]


def _order(item):
    transaction = item["transaction"]
    return (transaction["block_number"], transaction["transaction_index"],
            transaction["trace_address"], item["source_selector"])


def _failed_ancestor(path, frames):
    for parent, _ in frames:
        if not isinstance(parent, dict) or "error" not in parent:
            continue
        prefix = parent.get("traceAddress")
        if isinstance(prefix, list) and len(prefix) < len(path) and path[:len(prefix)] == prefix:
            return True
    return False


def map_hook_calls(venue, contexts, transactions):
    """Return the state-observation section for V2, or None for V1.

    `transactions` maps a transaction hash to every recorded frame of that
    transaction, each with its journal reference, or is None where the release
    holds no trace journal. Each frame starting with a mapped selector becomes
    exactly one record or one gap; a malformed frame refuses.
    """
    if venue == "wildcat-v1":
        return None
    if venue != "wildcat-v2":
        raise TabulariumError("Wildcat hook-state generation is unsupported")
    section = {"source": SOURCE, "limitations": list(SCOPE_LIMITATIONS),
               "coverage": "not-established" if transactions is None else "recorded-trace-frames",
               "records": [], "gaps": []}
    if transactions is None:
        return section
    if not isinstance(transactions, dict):
        raise TabulariumError("Wildcat hook-call transactions are not a mapping")
    seen, selectors, metadata = set(), set(), {}
    for tx_hash, frames in transactions.items():
        if not isinstance(frames, list):
            raise TabulariumError("Wildcat hook-call transaction frames are not a list")
        for frame, reference in frames:
            hook_selector = candidate_selector(frame)
            if hook_selector is None:
                continue
            layout = LAYOUTS[hook_selector]
            identity = _identity(frame)
            if frame["transactionHash"] != tx_hash:
                raise TabulariumError("Wildcat hook call frame is filed under another transaction")
            source_selector = selector(reference)
            key = (identity["hash"], tuple(identity["trace_address"]))
            if key in seen or source_selector in selectors:
                raise TabulariumError("Wildcat hook call repeats a trace identity or selector")
            seen.add(key)
            selectors.add(source_selector)
            position = (identity["block_hash"], identity["block_number"], identity["transaction_index"])
            if metadata.setdefault(identity["hash"], position) != position:
                raise TabulariumError("Wildcat hook calls give one transaction conflicting positions")
            action = frame["action"]
            caller = _address(action.get("from"), "caller")
            reason = None
            if contexts.get(caller, {}).get("role") != "market":
                reason = "caller-not-registered-market"
            elif "error" in frame:
                reason = "failed-call"
            elif _failed_ancestor(identity["trace_address"], frames):
                reason = "failed-ancestor"
            if reason is not None:
                section["gaps"].append({
                    "gap": "hook-state:%s:%s" % (layout["hook"], reason), "hook": layout["hook"],
                    "reason": reason, "caller": caller, "transaction": identity,
                    "source_selector": source_selector, "reference": deepcopy(reference),
                    "native_record": deepcopy(frame),
                })
                continue
            target = _address(action.get("to"), "target")
            if frame.get("type") != "call" or action.get("callType") != "call":
                raise TabulariumError("Wildcat hook call is not a plain call frame")
            if contexts.get(target, {}).get("role") != "hooks-instance":
                raise TabulariumError("Wildcat hook call target is not a registered hooks instance")
            bound = _hooks_word(contexts[caller])
            if bound is not None and bound != target:
                raise TabulariumError("Wildcat hook call target conflicts with the market's deployment hooks")
            section["records"].append({
                "evidence_class": EVIDENCE_CLASS, "rule": RULE, "hook": layout["hook"],
                "signature": layout["signature"], "selector": layout["selector"],
                "market": caller, "hooks_instance": target, "transaction": identity,
                "market_state": market_state(layout, action.get("input")),
                "source_selector": source_selector, "reference": deepcopy(reference),
                "supporting_selectors": _supports(contexts, caller, target),
                "limitations": list(LIMITATIONS), "native_record": deepcopy(frame),
            })
    section["records"].sort(key=_order)
    section["gaps"].sort(key=_order)
    return section
