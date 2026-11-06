#!/usr/bin/env python3
"""Study-time probe for the #1384 boundary fixtures.

Reads one generation's value-map inputs under ``docs/kickoff/1384/``, derives
every storage slot behind a mapped number from the compiled WildcatMarket
layout, checks each derived word against the deployed getter at the boundary
block, sizes the proofs a plan-v3 capture would fetch, and records which RPC
route answers which read. It writes one JSON summary to a caller-named path
that must not exist yet and prints the same summary. Provider URLs and bearer
values are read from the named environment variables and never written, and a
refused route is recorded as its integer code with a fixed message, never the
provider's own text.

This is measurement, not capture: nothing it fetches is a fixture, and no value
it reports is proved. Lazarus ``capture`` and ``verify`` establish proof.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from Crypto.Hash import keccak  # eth-hash[pycryptodome] pin in plugins/lazarus

KICKOFF = Path("docs/kickoff/1384")
ZERO32 = "0x" + "00" * 32
EIP1967_IMPLEMENTATION_SLOT = (
    "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
)
EIP1967_BEACON_SLOT = (
    "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
)
ZEPPELINOS_IMPLEMENTATION_SLOT = (
    "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3"
)
POINTER_SLOTS = {
    "eip1967-implementation": EIP1967_IMPLEMENTATION_SLOT,
    "eip1967-beacon": EIP1967_BEACON_SLOT,
    "zeppelinos-implementation": ZEPPELINOS_IMPLEMENTATION_SLOT,
}
SOLADY_BALANCE_SEED = bytes.fromhex("87a211a2")
ERC7201_NAMESPACES = ("openzeppelin.storage.ERC20",)
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
HOLDER_SEARCH_BLOCKS = 3000
SELECTOR_BALANCE_OF = "0x70a08231"
SELECTOR_UNPAID_EXPIRIES = "0x878eb921"  # getUnpaidBatchExpiries()
SELECTOR_ASSET = "0x38d52e0f"  # asset()
SELECTOR_PREVIOUS_STATE = "0x0c1e3fea"  # previousState()
SELECTOR_SCALED_BALANCE_OF = "0x1da24f3e"  # scaledBalanceOf(address)
SELECTOR_GET_WITHDRAWAL_BATCH = "0xdbcd50b4"  # getWithdrawalBatch(uint32)
SELECTOR_GET_ACCOUNT_WITHDRAWAL_STATUS = "0x02372c4f"  # getAccountWithdrawalStatus(address,uint32)

# Compiled with Foundry 1.7.1 from the pinned public sources named in
# docs/kickoff/1384/evidence/sources.json: `forge inspect
# src/market/WildcatMarket.sol:WildcatMarket storageLayout`.
LAYOUTS = {
    "v1": {
        "state": [3, 4, 5, 6],
        "accounts": 7,
        "fifo_head": 8,
        "fifo_data": 9,
        "batches": 10,
        "statuses": 11,
        "account_scaled_offset": 1,  # AuthRole approval occupies byte 0
        "state_words": 13,
        "word3": [("timeDelinquent", 0, 4), ("annualInterestBips", 4, 2),
                  ("reserveRatioBips", 6, 2), ("scaleFactor", 8, 14),
                  ("lastInterestAccruedTimestamp", 22, 4)],
    },
    "v2": {
        "state": [0, 1, 2, 3],
        "accounts": 4,
        "fifo_head": 5,
        "fifo_data": 6,
        "batches": 7,
        "statuses": 8,
        "account_scaled_offset": 0,
        "state_words": 14,
        "word3": [("timeDelinquent", 0, 4), ("protocolFeeBips", 4, 2),
                  ("annualInterestBips", 6, 2), ("reserveRatioBips", 8, 2),
                  ("scaleFactor", 10, 14), ("lastInterestAccruedTimestamp", 24, 4)],
    },
}
WORD0 = [("isClosed", 0, 1), ("maxTotalSupply", 1, 16)]
WORD1 = [("accruedProtocolFees", 0, 16), ("normalizedUnclaimedWithdrawals", 16, 16)]
WORD2 = [("scaledTotalSupply", 0, 13), ("scaledPendingWithdrawals", 13, 13),
         ("pendingWithdrawalExpiry", 26, 4), ("isDelinquent", 30, 1)]


def kec(data: bytes) -> bytes:
    return keccak.new(digest_bits=256, data=data).digest()


def pad(value: int | str) -> bytes:
    if isinstance(value, str):
        value = int(value, 16)
    return value.to_bytes(32, "big")


def slot_hex(value: bytes | int) -> str:
    if isinstance(value, int):
        value = value.to_bytes(32, "big")
    return "0x" + value.hex()


def mapping_slot(key: int | str, base: int | bytes) -> bytes:
    base_bytes = base if isinstance(base, bytes) else pad(base)
    return kec(pad(key) + base_bytes)


def erc7201_base(namespace: str) -> int:
    seed = int.from_bytes(kec(namespace.encode()), "big") - 1
    return int.from_bytes(kec(pad(seed)), "big") & ~0xFF


def balance_slot_candidates(holder: str) -> list[tuple[str, int | str, bytes]]:
    """Every balance-mapping layout this study knows how to name."""
    out: list[tuple[str, int | str, bytes]] = []
    for base in range(64):
        out.append(("solidity", base, kec(pad(holder) + pad(base))))
        out.append(("vyper", base, kec(pad(base) + pad(holder))))
    for namespace in ERC7201_NAMESPACES:
        out.append((f"erc7201:{namespace}", 0, kec(pad(holder) + pad(erc7201_base(namespace)))))
    out.append(("solady", "0x87a211a2", kec(bytes.fromhex(holder[2:]) + bytes(8) + SOLADY_BALANCE_SEED)))
    return out


def balance_slot(holder: str, layout: dict) -> bytes:
    order = layout["order"]
    base = layout["base"]
    if order == "solidity":
        return kec(pad(holder) + pad(base))
    if order == "vyper":
        return kec(pad(base) + pad(holder))
    if order.startswith("erc7201:"):
        return kec(pad(holder) + pad(erc7201_base(order.split(":", 1)[1])))
    if order == "solady":
        return kec(bytes.fromhex(holder[2:]) + bytes(8) + SOLADY_BALANCE_SEED)
    raise ValueError(order)


def unpack(word: int, fields: list[tuple[str, int, int]]) -> dict[str, int]:
    out = {}
    for name, offset, size in fields:
        out[name] = (word >> (8 * offset)) & ((1 << (8 * size)) - 1)
    return out


class Route:
    """One JSON-RPC route; the URL and bearer never leave this object."""

    def __init__(self, name: str, url: str, bearer: str | None, batch: int):
        self.name = name
        self._url = url
        self._bearer = bearer
        self.batch = batch
        self.bytes = 0
        self.requests = 0
        self.seconds = 0.0

    def _post(self, payload, timeout=300):
        headers = {"content-type": "application/json", "user-agent": "curl/8.7.1"}
        if self._bearer:
            headers["authorization"] = "Bearer " + self._bearer
        request = urllib.request.Request(
            self._url, data=json.dumps(payload).encode(), headers=headers
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            body = error.read()
            self.seconds += time.monotonic() - started
            try:
                return json.loads(body), len(body), error.code
            except ValueError:
                return {"error": {"code": error.code, "message": "http error"}}, len(body), error.code
        self.seconds += time.monotonic() - started
        self.bytes += len(body)
        return json.loads(body), len(body), 200

    def call(self, method, params, timeout=300):
        self.requests += 1
        parsed, size, _ = self._post(
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout
        )
        if isinstance(parsed, list):
            parsed = parsed[0]
        return parsed, size

    def many(self, calls, timeout=300):
        """Batched calls; returns results in order, with None for an error."""
        results = []
        for start in range(0, len(calls), self.batch):
            chunk = calls[start:start + self.batch]
            payload = [
                {"jsonrpc": "2.0", "id": index, "method": method, "params": params}
                for index, (method, params) in enumerate(chunk)
            ]
            self.requests += len(chunk)
            parsed, _, _ = self._post(payload, timeout)
            if not isinstance(parsed, list):
                raise RuntimeError(f"{self.name}: batch answer is not an array")
            by_id = {item.get("id"): item for item in parsed}
            for index in range(len(chunk)):
                item = by_id.get(index, {})
                results.append(item.get("result") if "result" in item else None)
        return results


REFUSAL_MESSAGE = "provider request failed"


def sanitised_outcome(parsed: dict, size: int) -> dict:
    """Record one route answer with no provider text in it.

    A provider's error message can quote its own URL or echo the request, so
    a refusal keeps only the integer code and a fixed message. The study-time
    copy wrote the message truncated to 120 characters, which is how a URL
    reached two route entries in each committed summary.
    """
    if isinstance(parsed, dict) and parsed.get("result") is not None:
        return {"outcome": "served", "bytes": size}
    error = parsed.get("error") if isinstance(parsed, dict) else None
    code = error.get("code") if isinstance(error, dict) else None
    if isinstance(code, bool) or not isinstance(code, int):
        code = None
    return {"outcome": "refused", "code": code, "message": REFUSAL_MESSAGE}


def load_inventory(generation: str) -> list[dict]:
    sys.path.insert(0, str(KICKOFF.resolve()))
    import capture_requests  # noqa: E402  (offline generator from the value map)

    return capture_requests.requests(generation)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation", choices=("v1", "v2"), required=True)
    parser.add_argument("--reth-env", default="RETH_RPC_URL")
    parser.add_argument("--proof-env", default="ALEXANDRIA_COMPOUND_RPC_URL")
    parser.add_argument("--bearer-env", default="ALEXANDRIA_RPC_BEARER")
    parser.add_argument("--keyless", action="append", default=[],
                        help="NAME=URL of a keyless route to probe for proofs")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if os.path.lexists(args.out):
        print(f"refusing to overwrite {args.out}", file=sys.stderr)
        return 2
    reth_url = os.environ.get(args.reth_env, "")
    proof_url = os.environ.get(args.proof_env, "")
    if not reth_url or not proof_url:
        print("named environment variables are unset", file=sys.stderr)
        return 2
    reth = Route("local-archive", reth_url, None, batch=200)
    gateway = Route("gateway", proof_url, os.environ.get(args.bearer_env) or None, batch=10)
    keyless = []
    for spec in args.keyless:
        name, _, url = spec.partition("=")
        keyless.append(Route(name, url, None, batch=3))

    generation = args.generation
    layout = LAYOUTS[generation]
    scope = json.loads((KICKOFF / "scope.json").read_text())
    population = json.loads((KICKOFF / "population.json").read_text())[generation]
    anchor = scope["anchors"][generation]
    number = anchor["number"]
    block_hex = hex(number)
    block_hash = anchor["hash"].lower()
    selector = {"blockHash": block_hash, "requireCanonical": True}
    subjects = scope["subjects"][generation]
    markets = [s["address"].lower() for s in subjects if s["role"] == "market"]
    summary: dict = {
        "schema": "fiat-1384-probe/v1",
        "generation": generation,
        "block_number": number,
        "block_hash": block_hash,
        "layout": {k: v for k, v in layout.items() if k not in ("word3",)},
        "subjects": len(subjects),
        "markets": len(markets),
    }

    # 1. Header and receipts on the local archive.
    header, header_bytes = reth.call("eth_getBlockByNumber", [block_hex, False])
    block = header["result"]
    if block["hash"].lower() != block_hash:
        raise SystemExit("local archive header hash disagrees with the value map anchor")
    summary["header"] = {
        "state_root": block["stateRoot"],
        "receipts_root": block["receiptsRoot"],
        "timestamp": int(block["timestamp"], 16),
        "transactions": len(block["transactions"]),
        "json_bytes": len(json.dumps(block)),
    }
    receipts_answer, receipts_bytes = reth.call("eth_getBlockReceipts", [block_hash])
    receipts = receipts_answer["result"]
    market_set = set(markets)
    asset_set: set[str] = set()
    consensus_bytes = 0
    log_count = 0
    for receipt in receipts:
        consensus_bytes += len(json.dumps({
            "status": receipt["status"],
            "cumulativeGasUsed": receipt["cumulativeGasUsed"],
            "logsBloom": receipt["logsBloom"],
            "logs": [{"address": l["address"], "topics": l["topics"], "data": l["data"]} for l in receipt["logs"]],
        }))
        log_count += len(receipt["logs"])
    summary["receipts"] = {
        "count": len(receipts),
        "logs": log_count,
        "rpc_json_bytes": receipts_bytes,
        "consensus_json_bytes": consensus_bytes,
    }

    # 2. Inventory calls on the local archive, kept for the slot comparison.
    inventory = load_inventory(generation)
    call_rows = [row for row in inventory if row["method"] == "eth_call"]
    call_results = reth.many([(row["method"], row["params"]) for row in call_rows])
    by_request: dict[tuple[str, str], str | None] = {}
    reverted = 0
    record_bytes = 0
    for row, result in zip(call_rows, call_results):
        by_request[(row["params"][0]["to"].lower(), row["params"][0]["data"])] = result
        if result is None:
            reverted += 1
        record_bytes += len(json.dumps({
            "evidence": row["evidence"], "method": row["method"], "name": row["name"],
            "outcome": {"result": result} if result is not None else {"error": {"code": 3, "message": "execution reverted"}},
            "params": row["params"], "request_key": "0x" + "00" * 32, "required": row["required"],
            "schema_version": 1,
        })) + 1
    code_rows = [row for row in inventory if row["method"] == "eth_getCode"]
    code_results = reth.many([(row["method"], row["params"]) for row in code_rows])
    code_bytes = {}
    for row, result in zip(code_rows, code_results):
        code_bytes[row["params"][0].lower()] = len(result or "0x") - 2
        record_bytes += len(json.dumps(row)) + len(result or "0x") + 80
    proof_rows = [row for row in inventory if row["method"] == "eth_getProof"]
    summary["inventory"] = {
        "rows": len(inventory),
        "eth_call": len(call_rows),
        "eth_getCode": len(code_rows),
        "eth_getProof_recorded": len(proof_rows),
        "eth_call_reverted_at_boundary": reverted,
        "estimated_rpc_record_bytes_without_recorded_proofs": record_bytes,
    }

    def word_of(address: str, data: str, index: int) -> int | None:
        result = by_request.get((address, data))
        if result is None or len(result) < 2 + 64 * (index + 1):
            return None
        return int(result[2 + 64 * index: 2 + 64 * (index + 1)], 16)

    # 3. Derive slots per market and read them on the local archive.
    market_slots: dict[str, dict[str, list[str]]] = {}
    reads: list[tuple[str, list]] = []
    read_index: dict[tuple[str, str], int] = {}

    def want(address: str, slot: str) -> None:
        key = (address, slot)
        if key not in read_index:
            read_index[key] = len(reads)
            reads.append(("eth_getStorageAt", [address, slot, selector]))

    for market in markets:
        members = population[market]
        slots = {
            "state": [slot_hex(s) for s in layout["state"]],
            "fifo_head": [slot_hex(layout["fifo_head"])],
            "accounts": [slot_hex(mapping_slot(a, layout["accounts"])) for a in members["accounts"]],
            "batches": [],
            "statuses": [],
        }
        for expiry in members["batch_expiries"]:
            base = mapping_slot(expiry, layout["batches"])
            slots["batches"].append(slot_hex(base))
            slots["batches"].append(slot_hex(int.from_bytes(base, "big") + 1))
        for pair in members["account_batches"]:
            inner = mapping_slot(pair["expiry"], layout["statuses"])
            slots["statuses"].append(slot_hex(mapping_slot(pair["account"], inner)))
        market_slots[market] = slots
        for group in slots.values():
            for slot in group:
                want(market, slot)
    read_results = reth.many(reads)

    def stored(address: str, slot: str) -> int:
        value = read_results[read_index[(address, slot)]]
        return int(value, 16) if value else 0

    # FIFO data entries depend on the head word, so they are a second pass.
    fifo_reads: list[tuple[str, list]] = []
    fifo_index: dict[tuple[str, str], int] = {}
    fifo_meta: dict[str, dict] = {}
    for market in markets:
        head = stored(market, slot_hex(layout["fifo_head"]))
        start = head & ((1 << 128) - 1)
        nxt = head >> 128
        entries = [slot_hex(mapping_slot(i, layout["fifo_data"])) for i in range(start, nxt)]
        fifo_meta[market] = {"start_index": start, "next_index": nxt, "entries": len(entries)}
        market_slots[market]["fifo_data"] = entries
        for slot in entries:
            fifo_index[(market, slot)] = len(fifo_reads)
            fifo_reads.append(("eth_getStorageAt", [market, slot, selector]))
    fifo_results = reth.many(fifo_reads)

    # 4. Compare every derived word with the deployed getter.
    decoded_states: dict[str, dict[str, int]] = {}
    agreement = {"state_markets": 0, "state_fields": 0, "state_mismatch": [],
                 "accounts": 0, "accounts_mismatch": [], "batches": 0, "batches_mismatch": [],
                 "statuses": 0, "statuses_mismatch": [], "fifo_markets": 0, "fifo_mismatch": []}
    for market in markets:
        words = [stored(market, s) for s in market_slots[market]["state"]]
        decoded = {}
        decoded.update(unpack(words[0], WORD0))
        decoded.update(unpack(words[1], WORD1))
        decoded.update(unpack(words[2], WORD2))
        decoded.update(unpack(words[3], layout["word3"]))
        decoded_states[market] = decoded
        names = ["isClosed", "maxTotalSupply", "accruedProtocolFees", "normalizedUnclaimedWithdrawals",
                 "scaledTotalSupply", "scaledPendingWithdrawals", "pendingWithdrawalExpiry",
                 "isDelinquent", "timeDelinquent"]
        if generation == "v2":
            names.append("protocolFeeBips")
        names += ["annualInterestBips", "reserveRatioBips", "scaleFactor", "lastInterestAccruedTimestamp"]
        ok = True
        for index, name in enumerate(names):
            view = word_of(market, SELECTOR_PREVIOUS_STATE, index)
            if view is None or view != decoded[name]:
                ok = False
                agreement["state_mismatch"].append({"market": market, "field": name, "stored": decoded[name], "view": view})
            else:
                agreement["state_fields"] += 1
        agreement["state_markets"] += int(ok)
        members = population[market]
        for account, slot in zip(members["accounts"], market_slots[market]["accounts"]):
            view = word_of(market, SELECTOR_SCALED_BALANCE_OF + pad(account).hex(), 0)
            value = (stored(market, slot) >> (8 * layout["account_scaled_offset"])) & ((1 << 104) - 1)
            if view == value:
                agreement["accounts"] += 1
            else:
                agreement["accounts_mismatch"].append({"market": market, "account": account, "stored": value, "view": view})
        batch_slots = market_slots[market]["batches"]
        for position, expiry in enumerate(members["batch_expiries"]):
            first = stored(market, batch_slots[2 * position])
            second = stored(market, batch_slots[2 * position + 1])
            values = (first & ((1 << 104) - 1), (first >> 104) & ((1 << 104) - 1), second & ((1 << 128) - 1))
            data = SELECTOR_GET_WITHDRAWAL_BATCH + pad(expiry).hex()
            views = tuple(word_of(market, data, i) for i in range(3))
            if views == values:
                agreement["batches"] += 1
            else:
                agreement["batches_mismatch"].append({"market": market, "expiry": expiry, "stored": values, "view": views})
        for pair, slot in zip(members["account_batches"], market_slots[market]["statuses"]):
            word = stored(market, slot)
            values = (word & ((1 << 104) - 1), (word >> 104) & ((1 << 128) - 1))
            data = SELECTOR_GET_ACCOUNT_WITHDRAWAL_STATUS + pad(pair["account"]).hex() + pad(pair["expiry"]).hex()
            views = tuple(word_of(market, data, i) for i in range(2))
            if views == values:
                agreement["statuses"] += 1
            else:
                agreement["statuses_mismatch"].append({"market": market, "account": pair["account"], "expiry": pair["expiry"], "stored": values, "view": views})
        unpaid = [fifo_results[fifo_index[(market, s)]] for s in market_slots[market]["fifo_data"]]
        unpaid_values = [int(v, 16) & 0xFFFFFFFF if v else 0 for v in unpaid]
        view_raw = by_request.get((market, SELECTOR_UNPAID_EXPIRIES))
        view_list = None
        if view_raw and len(view_raw) >= 130:
            count = int(view_raw[66:130], 16)
            view_list = [int(view_raw[130 + 64 * i: 194 + 64 * i], 16) for i in range(count)]
        if view_list == unpaid_values:
            agreement["fifo_markets"] += 1
        else:
            agreement["fifo_mismatch"].append({"market": market, "stored": unpaid_values, "view": view_list})
    summary["agreement"] = agreement
    summary["fifo"] = fifo_meta
    summary["state_decoded"] = decoded_states

    # 5. Underlying asset tokens: discover the balance mapping slot empirically.
    asset_of: dict[str, str] = {}
    for market in markets:
        raw = by_request.get((market, SELECTOR_ASSET))
        asset_of[market] = ("0x" + raw[-40:]).lower() if raw else None
    tokens: dict[str, dict] = {}
    token_codes = reth.many([("eth_getCode", [t, selector]) for t in sorted(set(a for a in asset_of.values() if a))])
    token_code_bytes = {t: len(c or "0x") // 2 - 1 for t, c in zip(sorted(set(a for a in asset_of.values() if a)), token_codes)}
    for token in sorted(set(a for a in asset_of.values() if a)):
        holders = [m for m in markets if asset_of[m] == token]
        balances = reth.many([("eth_call", [{"to": token, "data": SELECTOR_BALANCE_OF + pad(m).hex()}, selector]) for m in holders])
        balance_of = {m: int(b, 16) if b else None for m, b in zip(holders, balances)}
        probe_holder = next((m for m in holders if balance_of[m]), None)
        holder_source = "market"
        if probe_holder is None:
            # No market holds this asset at the boundary; a recent transfer
            # recipient supplies a nonzero word to recognise the layout by.
            logs = reth.call("eth_getLogs", [{
                "address": token, "topics": [TRANSFER_TOPIC],
                "fromBlock": hex(number - HOLDER_SEARCH_BLOCKS), "toBlock": block_hex,
            }])[0].get("result") or []
            for log in reversed(logs):
                candidate = "0x" + log["topics"][2][-40:]
                if int(candidate, 16) == 0:
                    continue
                raw = reth.many([("eth_call", [{"to": token, "data": SELECTOR_BALANCE_OF + pad(candidate).hex()}, selector])])[0]
                if raw and int(raw, 16):
                    probe_holder = candidate
                    balance_of[candidate] = int(raw, 16)
                    holder_source = "recent-transfer-recipient"
                    break
        found = None
        if probe_holder is not None:
            target = balance_of[probe_holder]
            candidates = balance_slot_candidates(probe_holder)
            values = reth.many([("eth_getStorageAt", [token, slot_hex(slot), selector]) for _, _, slot in candidates])
            for (order, base, _), value in zip(candidates, values):
                if value and int(value, 16) == target:
                    found = {"order": order, "base": base}
                    break
        pointer_values = reth.many([("eth_getStorageAt", [token, slot, selector]) for slot in POINTER_SLOTS.values()])
        pointers = {}
        for (name, slot), raw in zip(POINTER_SLOTS.items(), pointer_values):
            if raw and int(raw, 16):
                pointers[name] = {"slot": slot, "address": "0x" + raw[-40:]}
        tokens[token] = {
            "markets": len(holders),
            "code_bytes": token_code_bytes.get(token),
            "probe_holder": probe_holder,
            "probe_holder_source": holder_source if probe_holder else None,
            "balance_slot": found,
            "pointers": pointers,
            "holders_with_zero_balance": sum(1 for m in holders if not balance_of[m]),
        }
        if found:
            for market in holders:
                market_slots.setdefault(token, {"balances": []}).setdefault("balances", []).append(slot_hex(balance_slot(market, found)))
            for pointer in pointers.values():
                market_slots[token].setdefault("implementation_pointer", []).append(pointer["slot"])
    summary["tokens"] = tokens
    summary["assets_per_market"] = asset_of

    # 6. Size the proof set on the proof route.
    proof_targets: list[tuple[str, list[str]]] = []
    for subject in subjects:
        address = subject["address"].lower()
        groups = market_slots.get(address, {})
        slots = sorted({s for group in groups.values() for s in group})
        proof_targets.append((address, slots))
    for token, groups in market_slots.items():
        if token in market_set:
            continue
        slots = sorted({s for group in groups.values() for s in group})
        proof_targets.append((token, slots))
        for pointer in tokens[token]["pointers"].values():
            proof_targets.append((pointer["address"], []))
    proof_bytes = 0
    proof_calls = 0
    max_slots = 0
    chunked_targets = 0
    over_1024 = 0
    for address, slots in proof_targets:
        max_slots = max(max_slots, len(slots))
        if len(slots) > 1024:
            over_1024 += 1
        # Capture sends a target's whole slot list in one request, so the probe
        # does the same; a route that caps the list per call refuses here.
        chunks = [slots]
        if len(slots) > 2048:
            chunked_targets += 1
        for chunk in chunks:
            answer, size = gateway.call("eth_getProof", [address, chunk, selector])
            if not answer.get("result"):
                raise SystemExit(f"proof route refused {address} with {len(chunk)} slots")
            proof_bytes += size
            proof_calls += 1
    pointer_codes = reth.many([("eth_getCode", [a, selector]) for a, _ in proof_targets if a not in code_bytes and a not in token_code_bytes])
    for (a, _), c in zip([t for t in proof_targets if t[0] not in code_bytes and t[0] not in token_code_bytes], pointer_codes):
        token_code_bytes[a] = len(c or "0x") // 2 - 1
    code_total = sum(code_bytes.get(a, token_code_bytes.get(a, 0)) for a, _ in proof_targets)
    summary["proof_set"] = {
        "targets": len(proof_targets),
        "slots": sum(len(s) for _, s in proof_targets),
        "max_slots_per_target": max_slots,
        "targets_over_1024_slots": over_1024,
        "targets_over_2048_slots_single_call": chunked_targets,
        "proof_calls": proof_calls,
        "proof_response_bytes": proof_bytes,
        "code_bytes_raw": code_total,
        "estimated_proofs_jsonl_bytes": proof_bytes + 2 * code_total + 400 * len(proof_targets),
        "proof_route_seconds": round(gateway.seconds, 2),
    }
    summary["estimated_fixture_bytes"] = (
        summary["proof_set"]["estimated_proofs_jsonl_bytes"]
        + record_bytes
        + sum(len(json.dumps(r)) + 8_000 for r in proof_rows)
        + receipts_bytes + consensus_bytes + summary["header"]["json_bytes"]
        + len(json.dumps(inventory)) + 70 * summary["proof_set"]["slots"] + 4_096
    )

    # 7. Route probes for one subject and one slot.
    probe_subject = markets[0]
    route_report = {}
    for route in [reth, gateway, *keyless]:
        answer, size = route.call("eth_getProof", [probe_subject, [ZERO32], block_hex])
        route_report[route.name] = {"eth_getProof": sanitised_outcome(answer, size)}
        answer, size = route.call("eth_getBlockReceipts", [block_hash])
        route_report[route.name]["eth_getBlockReceipts"] = sanitised_outcome(answer, size)
        answer, size = route.call("eth_getCode", [probe_subject, block_hex])
        route_report[route.name]["eth_getCode"] = sanitised_outcome(answer, size)
    summary["routes"] = route_report

    # 8. Throughput on the proof route at the Lazarus batch size of three.
    sample = [("eth_call", [{"to": markets[0], "data": SELECTOR_ASSET}, selector])] * 30
    started = time.monotonic()
    gateway.batch = 3
    gateway.many(sample)
    elapsed = time.monotonic() - started
    per_request_ms = 1000 * elapsed / len(sample)
    summary["throughput"] = {
        "sample_requests": len(sample),
        "batch_size": 3,
        "milliseconds_per_request": round(per_request_ms, 2),
        "projected_capture_seconds": round(
            (len(inventory) + 3) * per_request_ms / 1000 + gateway.seconds, 1
        ),
    }
    summary["local_archive"] = {"requests": reth.requests, "seconds": round(reth.seconds, 2)}

    # 9. Receipt witness target selection.
    target = None
    for receipt in receipts:
        if any(l["address"].lower() in market_set for l in receipt["logs"]):
            target = receipt
            break
    rule = "lowest-index receipt with a generation market log"
    if target is None:
        asset_set = set(a for a in asset_of.values() if a)
        for receipt in receipts:
            if any(l["address"].lower() in asset_set for l in receipt["logs"]):
                target = receipt
                break
        rule = "no market log in the block; lowest-index receipt with a generation underlying-asset log"
    if target is None:
        target = receipts[0]
        rule = "no market or asset log in the block; transaction index 0"
    projection = [
        l for r in receipts for l in r["logs"] if l["address"].lower() in market_set
    ]
    summary["receipt_witness"] = {
        "target_transaction_index": int(target["transactionIndex"], 16),
        "target_transaction_hash": target["transactionHash"],
        "target_log_count": len(target["logs"]),
        "selection_rule": rule,
        "market_filter_addresses": len(markets),
        "projected_market_logs": len(projection),
    }
    summary["market_slots"] = {
        address: {group: len(slots) for group, slots in groups.items()}
        for address, groups in market_slots.items()
    }

    encoded = json.dumps(summary, indent=1, sort_keys=True) + "\n"
    with open(args.out, "x", encoding="utf-8") as handle:
        handle.write(encoded)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("market_slots", "assets_per_market", "agreement")}, indent=1, sort_keys=True))
    print(json.dumps({k: (v if not isinstance(v, list) else v[:8]) for k, v in summary["agreement"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
