"""Euler v1 credit history from the canonical proxy event log.

The v1 data APIs and the old EulerScan websocket are gone, and the Messari
subgraph has no serving indexer.  The protocol itself is the better archive:
all borrowing passed through one proxy and emitted borrower-indexed ``Borrow``,
``Repay`` and ``Liquidation`` events with exact integer amounts.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .. import endpoints, sanitise
from ..evidence import Coverage, Record


VENUE = "euler-v1"
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_LOGS_PER_ADDRESS = 50_000
MAX_BATCH_CALLS = 2_000

BORROW_TOPIC = (
    "0x312a5e5e1079f5dda4e95dbbd0b908b291fd5b992ef22073643ab691572c5b52"
)
REPAY_TOPIC = (
    "0x05f2eeda0e08e4b437f487c8d7d29b14537d15e3488170dc3de5dbdf8dac4684"
)
LIQUIDATION_TOPIC = (
    "0xbba0f1d6fb8b9abe2bbc543b7c13d43faba91c6f78da4700381c94041ac7267d"
)
EVENT_KIND = {
    BORROW_TOPIC: "borrow",
    REPAY_TOPIC: "repayment",
    LIQUIDATION_TOPIC: "liquidation",
}
DECIMALS_SELECTOR = "0x313ce567"
SYMBOL_SELECTOR = "0x95d89b41"


class EulerV1ShapeError(ValueError):
    """The archive answered, but not with a complete shape we can cite."""


def _mapping(value, where):
    if not isinstance(value, dict):
        raise EulerV1ShapeError(f"{where} is not an object")
    return value


def _list(value, where):
    if not isinstance(value, list):
        raise EulerV1ShapeError(f"{where} is not a list")
    return value


def _require(mapping, key, where):
    if not isinstance(mapping, dict) or key not in mapping:
        raise EulerV1ShapeError(f"{where} has no {key!r}")
    return mapping[key]


def _hex_integer(value, where, *, maximum=None):
    if not isinstance(value, str) or not value.startswith("0x"):
        raise EulerV1ShapeError(f"{where} is not a JSON-RPC hex integer")
    digits = value[2:]
    if not digits:
        raise EulerV1ShapeError(f"{where} is an empty JSON-RPC hex integer")
    try:
        integer = int(digits, 16)
    except ValueError as error:
        raise EulerV1ShapeError(f"{where} is not hexadecimal") from error
    if integer < 0 or (maximum is not None and integer > maximum):
        raise EulerV1ShapeError(f"{where} is outside the accepted range")
    return integer


def _hash(value, where):
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        raise EulerV1ShapeError(f"{where} is not a transaction or block hash")
    try:
        int(value[2:], 16)
    except ValueError as error:
        raise EulerV1ShapeError(f"{where} is not hexadecimal") from error
    return value.lower()


def _address(value, where):
    try:
        return sanitise.address(value)
    except ValueError as error:
        raise EulerV1ShapeError(f"{where} is not an address: {error}") from error


def _topic_address(value, where):
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        raise EulerV1ShapeError(f"{where} is not a 32-byte address topic")
    if value[2:26] != "0" * 24:
        raise EulerV1ShapeError(f"{where} is not a zero-padded address topic")
    return _address("0x" + value[-40:], where)


def _words(value, count, where):
    expected = 2 + count * 64
    if not isinstance(value, str) or len(value) != expected or not value.startswith("0x"):
        raise EulerV1ShapeError(
            f"{where} is not exactly {count} ABI word(s)"
        )
    try:
        return [int(value[2 + i * 64 : 2 + (i + 1) * 64], 16) for i in range(count)]
    except ValueError as error:
        raise EulerV1ShapeError(f"{where} is not hexadecimal") from error


def _word_address(word, where):
    if word >> 160:
        raise EulerV1ShapeError(f"{where} is not a zero-padded address word")
    return _address(f"0x{word:040x}", where)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EulerV1ShapeError(f"Euler v1 archive redirected unexpectedly ({code})")


def _request_json(payload, timeout):
    endpoint = endpoints.EULER_V1_RPC_ENDPOINT
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "https" or parsed.query or parsed.fragment:
        raise EulerV1ShapeError("Euler v1 archive endpoint must be a plain HTTPS URL")
    raw_payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=raw_payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Probitas/1.0 (+https://github.com/wildcat-finance/skills)",
        },
        method="POST",
    )
    try:
        with urllib.request.build_opener(_NoRedirect()).open(
            request, timeout=timeout
        ) as response:
            length = response.headers.get("Content-Length")
            if length and length.isdigit() and int(length) > MAX_RESPONSE_BYTES:
                raise EulerV1ShapeError("Euler v1 archive response exceeds 16 MiB")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
        raise EulerV1ShapeError(f"Euler v1 archive request failed: {error}") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise EulerV1ShapeError("Euler v1 archive response exceeds 16 MiB")
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EulerV1ShapeError("Euler v1 archive response is not JSON") from error


def _rpc_result(response, expected_id, where):
    response = _mapping(response, where)
    if response.get("jsonrpc") != "2.0" or response.get("id") != expected_id:
        raise EulerV1ShapeError(f"{where} is not the requested JSON-RPC response")
    if "error" in response:
        error = _mapping(response["error"], f"{where}.error")
        message = sanitise.clean(error.get("message"), max_length=180)
        raise EulerV1ShapeError(f"{where} failed: {message or 'unknown RPC error'}")
    return _require(response, "result", where)


def _rpc(method, params, timeout):
    response = _request_json(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout,
    )
    return _rpc_result(response, 1, method)


def _rpc_batch(calls, timeout):
    if not calls:
        return []
    if len(calls) > MAX_BATCH_CALLS:
        raise EulerV1ShapeError(
            f"Euler v1 metadata needs {len(calls)} RPC calls; limit is {MAX_BATCH_CALLS}"
        )
    payload = [
        {"jsonrpc": "2.0", "id": index, "method": method, "params": params}
        for index, (method, params) in enumerate(calls, 1)
    ]
    rows = _list(_request_json(payload, timeout), "JSON-RPC batch")
    by_id = {}
    for row in rows:
        row = _mapping(row, "JSON-RPC batch item")
        row_id = row.get("id")
        if isinstance(row_id, bool) or not isinstance(row_id, int) or row_id in by_id:
            raise EulerV1ShapeError("JSON-RPC batch has a missing or duplicate integer id")
        by_id[row_id] = row
    expected = set(range(1, len(calls) + 1))
    if set(by_id) != expected:
        raise EulerV1ShapeError("JSON-RPC batch omitted or invented a response")
    return [
        _rpc_result(by_id[index], index, f"JSON-RPC batch item {index}")
        for index in range(1, len(calls) + 1)
    ]


def _block(raw, where, expected_number=None):
    raw = _mapping(raw, where)
    number = _hex_integer(_require(raw, "number", where), f"{where}.number")
    timestamp = _hex_integer(
        _require(raw, "timestamp", where), f"{where}.timestamp"
    )
    block_hash = _hash(_require(raw, "hash", where), f"{where}.hash")
    if expected_number is not None and number != expected_number:
        raise EulerV1ShapeError(
            f"{where} returned block {number}, expected {expected_number}"
        )
    return {"number": number, "timestamp": timestamp, "hash": block_hash}


def _event(raw, addresses, end_block, index):
    where = f"Euler v1 log {index}"
    raw = _mapping(raw, where)
    if _address(_require(raw, "address", where), f"{where}.address") != endpoints.EULER_V1_PROXY:
        raise EulerV1ShapeError(f"{where} was not emitted by the Euler v1 proxy")
    if _require(raw, "removed", where) is not False:
        raise EulerV1ShapeError(f"{where} is removed or has no canonicality flag")
    topics = _list(_require(raw, "topics", where), f"{where}.topics")
    if not topics or not isinstance(topics[0], str):
        raise EulerV1ShapeError(f"{where}.topics has no event signature")
    signature = topics[0].lower()
    kind = EVENT_KIND.get(signature)
    if kind is None:
        raise EulerV1ShapeError(f"{where} has an unrequested event signature")
    expected_topics = 4 if kind == "liquidation" else 3
    if len(topics) != expected_topics:
        raise EulerV1ShapeError(f"{where} has {len(topics)} topics, expected {expected_topics}")
    account = _topic_address(topics[2], f"{where}.topics[2]")
    if account not in addresses:
        raise EulerV1ShapeError(f"{where} belongs to unrequested account {account}")
    block_number = _hex_integer(
        _require(raw, "blockNumber", where), f"{where}.blockNumber"
    )
    if block_number > end_block:
        raise EulerV1ShapeError(f"{where} is beyond the finalized coverage boundary")
    transaction_index = _hex_integer(
        _require(raw, "transactionIndex", where), f"{where}.transactionIndex"
    )
    log_index = _hex_integer(_require(raw, "logIndex", where), f"{where}.logIndex")
    event = {
        "kind": kind,
        "account": account,
        "underlying": _topic_address(
            topics[1 if kind != "liquidation" else 3], f"{where}.underlying"
        ),
        "block": block_number,
        "transaction_index": transaction_index,
        "log_index": log_index,
        "transaction": _hash(
            _require(raw, "transactionHash", where), f"{where}.transactionHash"
        ),
        "block_hash": _hash(_require(raw, "blockHash", where), f"{where}.blockHash"),
        "where": where,
    }
    if kind == "liquidation":
        event["liquidator"] = _topic_address(topics[1], f"{where}.liquidator")
        words = _words(_require(raw, "data", where), 6, f"{where}.data")
        event.update(
            {
                "collateral": _word_address(words[0], f"{where}.collateral"),
                "repaid": words[1],
                "seized": words[2],
                "health_score": words[3],
                "base_discount": words[4],
                "discount": words[5],
            }
        )
    else:
        event["amount"] = _words(
            _require(raw, "data", where), 1, f"{where}.data"
        )[0]
    return event


def _decode_symbol(value, where):
    if not isinstance(value, str) or not value.startswith("0x"):
        raise EulerV1ShapeError(f"{where} is not ABI-encoded bytes")
    try:
        raw = bytes.fromhex(value[2:])
    except ValueError as error:
        raise EulerV1ShapeError(f"{where} is not hexadecimal") from error
    if len(raw) == 32:
        encoded = raw.rstrip(b"\0")
    elif len(raw) >= 64 and len(raw) % 32 == 0:
        offset = int.from_bytes(raw[:32], "big")
        length = int.from_bytes(raw[32:64], "big")
        if offset != 32 or length > 64 or 64 + length > len(raw):
            raise EulerV1ShapeError(f"{where} is not a bounded ABI string")
        encoded = raw[64 : 64 + length]
    else:
        raise EulerV1ShapeError(f"{where} is not a bytes32 or ABI string")
    try:
        symbol = encoded.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EulerV1ShapeError(f"{where} is not UTF-8") from error
    symbol = sanitise.clean(symbol, max_length=64)
    if not symbol:
        raise EulerV1ShapeError(f"{where} is empty")
    return symbol


def _decode_decimals(value, where):
    words = _words(value, 1, where)
    if words[0] > 255:
        raise EulerV1ShapeError(f"{where} exceeds uint8")
    return words[0]


def _fixture(path):
    filename = os.path.join(path, "euler-v1.json")
    if not os.path.exists(filename):
        raise EulerV1ShapeError(f"no Euler v1 fixture at {filename}")
    with open(filename, encoding="utf-8") as handle:
        return json.load(handle)


def _fixture_material(payload):
    payload = _mapping(payload, "Euler v1 fixture")
    final = _block(_require(payload, "finalized", "Euler v1 fixture"), "fixture.finalized")
    logs = _list(_require(payload, "logs", "Euler v1 fixture"), "fixture.logs")
    raw_blocks = _list(_require(payload, "blocks", "Euler v1 fixture"), "fixture.blocks")
    blocks = {}
    for index, raw in enumerate(raw_blocks):
        item = _block(raw, f"fixture.blocks[{index}]")
        if item["number"] in blocks:
            raise EulerV1ShapeError("fixture.blocks repeats a block")
        blocks[item["number"]] = item
    raw_tokens = _list(_require(payload, "tokens", "Euler v1 fixture"), "fixture.tokens")
    tokens = {}
    for index, raw in enumerate(raw_tokens):
        where = f"fixture.tokens[{index}]"
        raw = _mapping(raw, where)
        address = _address(_require(raw, "address", where), f"{where}.address")
        symbol = sanitise.clean(_require(raw, "symbol", where), max_length=64)
        decimals = _require(raw, "decimals", where)
        if not symbol or isinstance(decimals, bool) or not isinstance(decimals, int):
            raise EulerV1ShapeError(f"{where} has invalid token metadata")
        if decimals < 0 or decimals > 255 or address in tokens:
            raise EulerV1ShapeError(f"{where} has duplicate or invalid token metadata")
        tokens[address] = {"symbol": symbol, "decimals": decimals}
    return final, logs, blocks, tokens


def _live_material(addresses, timeout):
    final_raw = _rpc("eth_getBlockByNumber", ["finalized", False], timeout)
    final = _block(final_raw, "finalized block")
    logs = []
    for address in sorted(addresses):
        topic = "0x" + "0" * 24 + address[2:]
        rows = _list(
            _rpc(
                "eth_getLogs",
                [
                    {
                        "address": endpoints.EULER_V1_PROXY,
                        "fromBlock": "0x0",
                        "toBlock": hex(final["number"]),
                        "topics": [[BORROW_TOPIC, REPAY_TOPIC, LIQUIDATION_TOPIC], None, topic],
                    }
                ],
                timeout,
            ),
            f"eth_getLogs for {address}",
        )
        if len(rows) > MAX_LOGS_PER_ADDRESS:
            raise EulerV1ShapeError(
                f"{address} returned over {MAX_LOGS_PER_ADDRESS} Euler v1 logs"
            )
        logs.extend(rows)
    events = [_event(raw, addresses, final["number"], i) for i, raw in enumerate(logs)]
    block_numbers = sorted({event["block"] for event in events})
    tokens = sorted(
        {event["underlying"] for event in events}
        | {event["collateral"] for event in events if event["kind"] == "liquidation"}
    )
    block_results = _rpc_batch(
        [("eth_getBlockByNumber", [hex(number), False]) for number in block_numbers],
        timeout,
    )
    blocks = {
        number: _block(raw, f"event block {number}", expected_number=number)
        for number, raw in zip(block_numbers, block_results)
    }
    token_results = _rpc_batch(
        [
            ("eth_call", [{"to": token, "data": selector}, hex(final["number"])])
            for token in tokens
            for selector in (SYMBOL_SELECTOR, DECIMALS_SELECTOR)
        ],
        timeout,
    )
    metadata = {}
    for index, token in enumerate(tokens):
        metadata[token] = {
            "symbol": _decode_symbol(token_results[index * 2], f"{token}.symbol"),
            "decimals": _decode_decimals(
                token_results[index * 2 + 1], f"{token}.decimals"
            ),
        }
    return final, logs, blocks, metadata


def _records(events, blocks, tokens, addresses):
    records = []
    seen = set()
    for event in sorted(
        events,
        key=lambda item: (
            item["block"],
            item["transaction_index"],
            item["log_index"],
        ),
    ):
        identity = (event["transaction"], event["log_index"])
        if identity in seen:
            raise EulerV1ShapeError(f"duplicate Euler v1 log {identity}")
        seen.add(identity)
        block = blocks.get(event["block"])
        if block is None:
            raise EulerV1ShapeError(f"no timestamp for event block {event['block']}")
        if block["hash"] != event["block_hash"]:
            raise EulerV1ShapeError(
                f"event block hash disagrees at block {event['block']}"
            )
        debt = tokens.get(event["underlying"])
        if debt is None:
            raise EulerV1ShapeError(
                f"no token metadata for {event['underlying']}"
            )
        common = {
            "debt_token": event["underlying"],
            "debt_symbol": debt["symbol"],
            "debt_decimals": debt["decimals"],
            "collateralised": True,
        }
        if event["kind"] == "liquidation":
            collateral = tokens.get(event["collateral"])
            if collateral is None:
                raise EulerV1ShapeError(
                    f"no token metadata for {event['collateral']}"
                )
            values = {
                **common,
                "repaid": event["repaid"],
                "seized_collateral": event["seized"],
                "collateral_token": event["collateral"],
                "collateral_symbol": collateral["symbol"],
                "collateral_decimals": collateral["decimals"],
                "liquidator": event["liquidator"],
                "health_score": event["health_score"],
                "base_discount": event["base_discount"],
                "discount": event["discount"],
            }
        else:
            values = {**common, "amount": event["amount"]}
        records.append(
            Record(
                venue=VENUE,
                address=event["account"],
                provenance=addresses[event["account"]],
                claim=event["kind"],
                values=values,
                source=event["transaction"],
                observed_at=block["timestamp"],
                block=event["block"],
            )
        )
    return records


def adapter(addresses, config):
    """Run the Euler v1 mainnet event archive."""
    config = config or {}
    fixtures = config.get("fixtures")
    timeout = config.get("timeout", 30)
    if fixtures:
        final, logs, blocks, tokens = _fixture_material(_fixture(fixtures))
        endpoint = "fixture:" + sanitise.clean(
            os.path.basename(os.path.normpath(fixtures)) or "unnamed", max_length=60
        )
        block_range = "fixture"
    else:
        final, logs, blocks, tokens = _live_material(addresses, timeout)
        endpoint = endpoints.EULER_V1_RPC_ENDPOINT
        block_range = f"0-{final['number']}"
    events = [_event(raw, addresses, final["number"], i) for i, raw in enumerate(logs)]
    records = _records(events, blocks, tokens, addresses)
    return records, Coverage(
        venue=VENUE,
        status="checked" if records else "empty",
        endpoint=endpoint,
        block_range=block_range,
        note=(
            "ethereum mainnet canonical Euler v1 proxy log; Borrow, Repay and "
            f"Liquidation events checked through finalized block {final['number']}; "
            f"{len(records)} record(s) across {len(addresses)} subject address(es)"
            if records
            else "ethereum mainnet canonical Euler v1 proxy log; Borrow, Repay and "
            f"Liquidation events checked through finalized block {final['number']}; "
            "no borrowing activity found for any subject address"
        ),
    )
