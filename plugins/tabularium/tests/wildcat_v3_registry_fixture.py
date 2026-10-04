"""Synthetic intervals; registered addresses do not establish historical relationships."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "plugins" / "tabularium" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from tabularium_lib import verifier  # noqa: E402
from tabularium_lib.core import canonical_json  # noqa: E402
from tabularium_lib.keccak import keccak256  # noqa: E402
from tabularium_lib.wildcat_release import build_wildcat_canonical  # noqa: E402
from tabularium_lib.wildcat_source import _api  # noqa: E402


CREATED_AT = "2026-10-04T00:00:00Z"
DEBTOR = "0x" + "77" * 20
PAYER = "0x" + "55" * 20
ASSET = "0x" + "33" * 20
IDENTITIES = {
    "wildcat-v1": {
        "factory": "0xfd31007613c9f671df6a8d4234901324986bfd13",
        "controller": "0xd22cc5d80529401cd3eedea4a6e8958c6da49cb8",
        "market": "0x5850afc80561932b0abb63dd13cdc129395323a3",
        "start": 18743513, "end": 18743514,
    },
    "wildcat-v2": {
        "factory": "0xdd7dd3b5076cf89440d05585ff56d246386207be",
        "market": "0x20632bd54e16fcbcd35dcb2c8882a8a8802ad38d",
        "start": 25895380, "end": 25895380,
    },
}


def _word(value):
    return int(value, 16).to_bytes(32, "big") if isinstance(value, str) else value.to_bytes(32, "big")


def _string(value):
    data = value.encode("utf-8")
    return _word(len(data)) + data + b"\0" * (-len(data) % 32)


def _hash(venue, kind, number, position=None):
    label = f"wildcat-1378-constructed:{venue}:{kind}:{number}:{position}"
    return "0x" + hashlib.sha256(label.encode()).hexdigest()


def _deployment_data(venue):
    count = 9 if venue == "wildcat-v1" else 10
    name, symbol = _string("N"), _string("S")
    words = [count * 32, count * 32 + len(name), ASSET, 1000, 100, 200, 3600, 2000, 60]
    if venue == "wildcat-v2":
        words.append(0)
    return "0x" + (b"".join(_word(value) for value in words) + name + symbol).hex()


def _deployment_call():
    """Encode the complete ABI; the owner checks only the selected binding predicates."""
    signature = "deployMarket((address,string,string,uint128,uint16,uint16,uint32,uint16,uint32,uint256),bytes,bytes32,address,uint256)"
    name, symbol = _string("N"), _string("S")
    values = [ASSET, 320, 320 + len(name), 1000, 100, 200, 3600, 2000, 60, 0]
    parameters = b"".join(_word(value) for value in values) + name + symbol
    head = b"".join(_word(value) for value in (160, 160 + len(parameters), 0, 0, 0))
    return "0x" + (keccak256(signature.encode())[:4] + head + parameters + _word(0)).hex()


def _log(venue, emitter, signature, index, indexed=(), data=None):
    number = IDENTITIES[venue]["start"]
    return {
        "address": emitter, "blockNumber": hex(number),
        "blockHash": _hash(venue, "block", number),
        "transactionHash": _hash(venue, "transaction", number, 0),
        "transactionIndex": "0x0", "logIndex": hex(index), "removed": False,
        "topics": ["0x" + keccak256(signature.encode()).hex()]
                  + ["0x" + _word(value).hex() for value in indexed],
        "data": "0x" if data is None else data,
    }


def registry_inputs(venue):
    """Return fresh synthetic transport inputs and the complete authentic registry."""
    if venue not in IDENTITIES:
        raise ValueError("registry fixture requires wildcat-v1 or wildcat-v2")
    _api()
    from alexandria_lib import wildcat_registry

    raw = (wildcat_registry.registry_v1_bytes(REPO_ROOT) if venue == "wildcat-v1"
           else wildcat_registry.registry_bytes(REPO_ROOT))
    registry = json.loads(raw)
    selected = IDENTITIES[venue]
    start, end = selected["start"], selected["end"]
    subjects = sorted(value for key, value in selected.items() if key in ("factory", "controller", "market"))
    plan = {
        "format": "alexandria-interval-plan/v2", "chain": "eip155:1", "venue": venue,
        "deployment": venue + "-1378-constructed-debtor",
        "subjects": subjects, "interval": {"start": str(start), "end": str(end)},
        "shard_width": end - start + 1,
        "shards": [{"index": 0, "start": start, "end": end}],
        "evidence_classes": ["boundary-blocks", "logs", "traces"],
        "finality": {"policy": "finalized", "block_number": str(end + 1),
                     "block_hash": _hash(venue, "block", end + 1)},
        "provider": {"class": "constructed fixture provider, no endpoint",
                     "page_limit": 10000, "timeout_seconds": 25},
    }
    logs, traces = [], []
    if venue == "wildcat-v1":
        logs.append(_log(venue, selected["factory"], "NewController(address,address)", 0,
                         data="0x" + (_word(DEBTOR) + _word(selected["controller"])).hex()))
        deployment = "MarketDeployed(address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256)"
        emitter, indexed = selected["controller"], (selected["market"],)
    else:
        deployment = "MarketDeployed(address,address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256,uint256)"
        emitter, indexed = selected["factory"], ("0x" + "66" * 20, selected["market"])
        traces.append({
            "type": "call", "action": {"callType": "call", "from": DEBTOR,
                "to": selected["factory"], "input": _deployment_call(),
                "gas": "0x100000", "value": "0x0"},
            "result": {"gasUsed": "0x1000", "output": "0x" + _word(selected["market"]).hex()},
            "traceAddress": [], "subtraces": 0, "blockNumber": start,
            "blockHash": _hash(venue, "block", start),
            "transactionHash": _hash(venue, "transaction", start, 0), "transactionPosition": 0,
        })
    logs.append(_log(venue, emitter, deployment, len(logs), indexed, _deployment_data(venue)))
    logs.append(_log(venue, selected["market"], "Borrow(uint256)", len(logs),
                     data="0x" + _word(75).hex()))
    logs.append(_log(venue, selected["market"], "DebtRepaid(address,uint256)", len(logs),
                     (PAYER,), "0x" + _word(25).hex()))
    return {"plan": plan, "logs": logs, "traces": traces,
            "code": {address: "0x6000600055" for address in subjects}}, registry


class RegistryFixtureTransport:
    """Deterministic synthetic RPC responses; no endpoint, storage read or socket."""

    def __init__(self, state):
        self.state = state
        self.calls = []

    def request(self, payload, label):
        request = json.loads(payload)
        method, params = request["method"], request["params"]
        self.calls.append((method, label))
        venue = self.state["plan"]["venue"]
        if method == "eth_syncing":
            result = False
        elif method == "eth_getBlockByNumber":
            number = (int(self.state["plan"]["finality"]["block_number"])
                      if params[0] in ("finalized", "safe") else int(params[0], 16))
            result = {"hash": _hash(venue, "block", number), "number": hex(number),
                      "transactions": [_hash(venue, "transaction", number, position) for position in range(2)]}
        elif method == "eth_getLogs":
            scope = params[0]
            start, end = int(scope["fromBlock"], 16), int(scope["toBlock"], 16)
            addresses = scope["address"]
            addresses = [addresses] if isinstance(addresses, str) else addresses
            result = [row for row in self.state["logs"]
                      if start <= int(row["blockNumber"], 16) <= end and row["address"] in addresses]
        elif method == "eth_getCode":
            result = self.state["code"][params[0]]
        elif method == "trace_transaction":
            result = [row for row in self.state["traces"] if row["transactionHash"] == params[0]]
        else:
            raise AssertionError(f"registry fixture has no response for {method}")
        return canonical_json({"jsonrpc": "2.0", "id": request["id"], "result": result})


def build_registry_release(base: Path, venue: str, release_id: str) -> Path:
    """Publish a fresh closed canonical root, then verify its copied raw inputs."""
    state, registry = registry_inputs(venue)
    interval_api, release_api, _, _ = _api()
    with tempfile.TemporaryDirectory(prefix="wildcat-registry-fixture-") as temporary:
        scratch = Path(temporary).resolve()
        staging = scratch / "staging"
        staging.mkdir()
        interval_api.Collector(state["plan"], staging, RegistryFixtureTransport(state),
                               registry=registry).collect()
        interval_api.Reconciler(state["plan"], staging, RegistryFixtureTransport(state),
                                "second constructed provider, class only", registry=registry).reconcile()
        raw = scratch / "raw"
        interval_api.Builder(state["plan"], staging, registry, created_at=CREATED_AT).build(raw)
        interval_api.check_interval(raw)
        release_api.verify_release(raw)
        build_wildcat_canonical(raw, base, release_id)
    coverage = base / "coverage.json"
    verifier.verify(coverage)
    return coverage
