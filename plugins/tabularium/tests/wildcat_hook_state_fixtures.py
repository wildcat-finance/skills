"""A constructed Wildcat V2 interval whose market calls its hooks instance (skills#2144).

The registry-context fixture gains one registered hooks instance as a subject,
a deployment hooks word naming it, and a second transaction in which the market
emits a borrow log and calls that instance. The calls cover the five mapped
hooks, one failed call, one call under a failed parent, one call from an
unregistered address and one `onBorrow` call that stays unmapped.

The calldata is encoded here from the literal `HooksConfig.sol` offsets and the
`MarketState` field order at v2-protocol commit
a70f297fbd1b1ab597e0e9a3458a2d13a34b4657, not from the mapper's own tables, so
the two agree only if both follow the pinned source. Every record is
constructed; none was observed on a chain.
"""

from pathlib import Path
import tempfile

if __package__:
    from .wildcat_v3_registry_fixture import (
        CREATED_AT, DEBTOR, IDENTITIES, RegistryFixtureTransport, _hash, _word, registry_inputs,
    )
else:
    from wildcat_v3_registry_fixture import (
        CREATED_AT, DEBTOR, IDENTITIES, RegistryFixtureTransport, _hash, _word, registry_inputs,
    )

from tabularium_lib import verifier  # noqa: E402
from tabularium_lib.keccak import keccak256  # noqa: E402
from tabularium_lib.wildcat_release import build_wildcat_canonical  # noqa: E402
from tabularium_lib.wildcat_source import _api  # noqa: E402


VENUE = "wildcat-v2"
MARKET = IDENTITIES[VENUE]["market"]
START = IDENTITIES[VENUE]["start"]
# A registered OpenTermHooks instance at the V2 pin. The registry does not
# bind it to this market; the constructed deployment hooks word does.
HOOKS = "0x0d7a820f97714f879454790d8b3887b1c50b4dad"
LENDER = "0x" + "44" * 20
OTHER = "0x" + "66" * 20
STRANGER = "0x" + "99" * 20
# useOnDeposit through useOnRepay: bits 95 to 90 of the hooks configuration.
HOOKS_WORD = (int(HOOKS, 16) << 96) | sum(1 << bit for bit in range(90, 96))
ACTIVITY = _hash(VENUE, "transaction", START, 1)
STATE_TYPE = "(bool,uint128,uint128,uint128,uint104,uint104,uint32,bool,uint32,uint16,uint16,uint16,uint112,uint32)"
FIELDS = (
    "isClosed", "maxTotalSupply", "accruedProtocolFees", "normalizedUnclaimedWithdrawals",
    "scaledTotalSupply", "scaledPendingWithdrawals", "pendingWithdrawalExpiry", "isDelinquent",
    "timeDelinquent", "protocolFeeBips", "annualInterestBips", "reserveRatioBips", "scaleFactor",
    "lastInterestAccruedTimestamp",
)
# hook -> (signature, state offset, extraData head offset, base size), from
# the `<Hook>Hook_*` constants in HooksConfig.sol.
LAYOUT = {
    "onDeposit": ("onDeposit(address,uint256,%s,bytes)" % STATE_TYPE, 0x40, 0x200, 0x0244),
    "onQueueWithdrawal": ("onQueueWithdrawal(address,uint32,uint256,%s,bytes)" % STATE_TYPE, 0x60, 0x220, 0x0264),
    "onExecuteWithdrawal": ("onExecuteWithdrawal(address,uint128,%s,bytes)" % STATE_TYPE, 0x40, 0x200, 0x0244),
    "onTransfer": ("onTransfer(address,address,address,uint256,%s,bytes)" % STATE_TYPE, 0x80, 0x240, 0x0284),
    "onRepay": ("onRepay(uint256,%s,bytes)" % STATE_TYPE, 0x20, 0x1e0, 0x0224),
    "onBorrow": ("onBorrow(uint256,%s,bytes)" % STATE_TYPE, 0x20, 0x1e0, 0x0224),
}


def state(seed):
    """Distinct values per call, several at their declared maximum width."""
    return {
        "isClosed": seed == 4, "maxTotalSupply": (1 << 128) - 1 - seed,
        "accruedProtocolFees": 1000 + seed, "normalizedUnclaimedWithdrawals": 2000 + seed,
        "scaledTotalSupply": (1 << 104) - 1 - seed, "scaledPendingWithdrawals": 3000 + seed,
        "pendingWithdrawalExpiry": 1_760_000_000 + seed, "isDelinquent": seed % 2 == 1,
        "timeDelinquent": 60 * seed, "protocolFeeBips": 1000 + seed,
        "annualInterestBips": 1200 + seed, "reserveRatioBips": 2000 + seed,
        "scaleFactor": (1 << 112) - 1 - seed, "lastInterestAccruedTimestamp": 1_759_999_000 + seed,
    }


def calldata(hook, leading, values, extra=b""):
    """Encode one hook call the way the market's HooksConfig encoder writes it."""
    signature, state_offset, extra_head, base = LAYOUT[hook]
    head = b"".join(_word(value) for value in leading)
    assert len(head) == state_offset
    head += b"".join(_word(int(values[name])) for name in FIELDS)
    assert len(head) == extra_head
    data = keccak256(signature.encode())[:4] + head + _word(extra_head + 32) + _word(len(extra)) + extra
    assert len(data) == base + len(extra)
    return "0x" + data.hex()


# (hook, trace address, leading arguments, state seed, extraData)
MAPPED = (
    ("onDeposit", [0], (LENDER, 500), 0, b"\x01\x02\x03\x04\x05"),
    ("onQueueWithdrawal", [1], (LENDER, 1_760_086_400, 300), 1, b""),
    ("onTransfer", [2], (DEBTOR, LENDER, OTHER, 100), 2, b""),
    ("onExecuteWithdrawal", [3], (LENDER, 250), 3, b""),
    ("onRepay", [4], (700,), 4, b""),
)


def frame(trace_address, caller, target, data, failed=False):
    record = {
        "type": "call",
        "action": {"callType": "call", "from": caller, "to": target, "input": data,
                   "gas": "0x100000", "value": "0x0"},
        "traceAddress": list(trace_address), "subtraces": 0, "blockNumber": START,
        "blockHash": _hash(VENUE, "block", START), "transactionHash": ACTIVITY,
        "transactionPosition": 1,
    }
    if failed:
        record["error"] = "Reverted"
    else:
        record["result"] = {"gasUsed": "0x100", "output": "0x"}
    return record


def activity_frames():
    """The second transaction's frames: five mapped calls and four that map nothing."""
    frames = [frame([], DEBTOR, MARKET, "0xc5ebeaec" + _word(75).hex())]
    for hook, path, leading, seed, extra in MAPPED:
        frames.append(frame(path, MARKET, HOOKS, calldata(hook, leading, state(seed), extra)))
    frames += [
        frame([5], MARKET, HOOKS, calldata("onDeposit", (LENDER, 9), state(5)), failed=True),
        frame([6], MARKET, MARKET, "0x12345678", failed=True),
        frame([6, 0], MARKET, HOOKS, calldata("onRepay", (9,), state(6))),
        frame([7], STRANGER, HOOKS, calldata("onTransfer", (STRANGER, LENDER, OTHER, 9), state(7))),
        frame([8], MARKET, HOOKS, calldata("onBorrow", (75,), state(8))),
    ]
    return frames


def hook_state_inputs(frames=None):
    """The registry-context inputs with the hooks instance and the activity transaction."""
    state_, registry = registry_inputs(VENUE)
    plan, logs = state_["plan"], state_["logs"]
    plan["subjects"] = sorted(plan["subjects"] + [HOOKS])
    plan["deployment"] = VENUE + "-2144-constructed-hook-state"
    deployment = logs[0]
    data = bytes.fromhex(deployment["data"][2:])
    deployment["data"] = "0x" + (data[:9 * 32] + _word(HOOKS_WORD) + data[10 * 32:]).hex()
    logs.append({
        "address": MARKET, "blockNumber": hex(START), "blockHash": _hash(VENUE, "block", START),
        "transactionHash": ACTIVITY, "transactionIndex": "0x1", "logIndex": hex(len(logs)),
        "removed": False, "topics": ["0x" + keccak256(b"Borrow(uint256)").hex()],
        "data": "0x" + _word(75).hex(),
    })
    state_["traces"] += activity_frames() if frames is None else frames
    state_["code"][HOOKS] = "0x" + "60006000556002" * 4
    return state_, registry


def raw_release(base: Path, frames=None) -> Path:
    """Collect, build and check the interval through Alexandria; return the raw root."""
    state_, registry = hook_state_inputs(frames)
    interval_api, release_api, _, _ = _api()
    raw = base / "raw"
    with tempfile.TemporaryDirectory(prefix="wildcat-hook-state-fixture-") as temporary:
        staging = Path(temporary).resolve() / "staging"
        staging.mkdir()
        interval_api.Collector(state_["plan"], staging, RegistryFixtureTransport(state_),
                               registry=registry).collect()
        interval_api.Reconciler(state_["plan"], staging, RegistryFixtureTransport(state_),
                                "second constructed provider, class only", registry=registry).reconcile()
        interval_api.Builder(state_["plan"], staging, registry, created_at=CREATED_AT).build(raw)
    interval_api.check_interval(raw)
    release_api.verify_release(raw)
    return raw


def canonical_release(raw: Path, target: Path, version: str) -> Path:
    """Build one canonical root from the raw release and verify it offline."""
    build_wildcat_canonical(raw, target, VENUE + "-constructed-hook-state-" + version, version)
    verifier.verify(target / "coverage.json")
    return target
