#!/usr/bin/env python3
"""Run the checked-in Aave v4 fixture without an archive provider."""

from __future__ import annotations

import http.client
from pathlib import Path
import shutil
import sys
import tempfile
from threading import Thread
from typing import Any


FIXTURE = Path(__file__).resolve().parent
PLUGIN_ROOT = FIXTURE.parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lazarus_lib.canonical import dumps, load, loads
from lazarus_lib.errors import IntegrityError
from lazarus_lib.manifest import build_manifest, write_manifest
from lazarus_lib.records import read_proof_records, write_proof_records
from lazarus_lib.server import make_server
from lazarus_lib.verifier import verify_fixture


SPOKE = "0x973a023a77420ba610f06b3858ad991df6d85a08"
HUB = "0xcca852bc40e560adc3b1cc58ca5b55638ce826c9"
BLOCK_NUMBER = "0x18ac22c"
BLOCK_HASH = "0x11e9be2ff9ff6a04319af0b04c24b95f3f1117c2df79f44f94d208857d01af07"
TRANSACTION = "0xdaa7ebd15335bf809ee414876846df98d40736e7d29e3eeaca8b434653b9313e"
SLOT_ZERO = "0x" + "00" * 32
SLOT_ONE = "0x" + "00" * 31 + "01"
SPOKE_SLOT_ZERO_WORD = "0x" + "00" * 31 + "0b"
SPOKE_SLOT_ONE_VALUE = "0x23280c7d713b49da00000000000000000000104ae2c7a64f0000"
HUB_SLOT_ZERO_WORD = "0x" + "00" * 31 + "11"
MISS_ERROR = -32070


def rpc_call(
    address: tuple[str, int], identifier: int, method: str, params: list[Any]
) -> dict[str, Any]:
    connection = http.client.HTTPConnection(*address, timeout=5)
    try:
        connection.request(
            "POST",
            "/",
            body=dumps(
                {
                    "jsonrpc": "2.0",
                    "id": identifier,
                    "method": method,
                    "params": params,
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = response.read()
    finally:
        connection.close()
    if response.status != 200:
        raise AssertionError(f"replay returned HTTP {response.status}")
    parsed = loads(body)
    if not isinstance(parsed, dict):
        raise AssertionError("replay response is not a JSON-RPC object")
    return parsed


def proof_for(records: list[dict[str, Any]], address: str) -> dict[str, Any]:
    for record in records:
        if record["address"] == address:
            return record
    raise AssertionError(f"fixture carries no proof for {address}")


def reject_mutated_proof(manifest: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as directory:
        changed = Path(directory) / "fixture"
        shutil.copytree(FIXTURE, changed)
        records = read_proof_records(changed / "proofs.jsonl")
        node = records[0]["account_proof"][0]
        records[0]["account_proof"][0] = node[:-1] + ("0" if node[-1] != "0" else "1")
        write_proof_records(changed / "proofs.jsonl", records)
        rebuilt = build_manifest(
            changed,
            [item["path"] for item in manifest["components"]],
            chain_id=manifest["chain_id"],
            block_number=manifest["block"]["number"],
            block_hash=manifest["block"]["hash"],
            evidence_counts=manifest["evidence_counts"],
            optional_failures=manifest["optional_failures"],
        )
        write_manifest(changed, rebuilt)
        try:
            verify_fixture(changed)
        except IntegrityError as exc:
            if "root" not in str(exc):
                raise AssertionError(
                    "proof mutation failed outside trie verification"
                ) from exc
            return
    raise AssertionError("one-nibble proof mutation was accepted")


def rebuild_manifest_bytes(manifest: dict[str, Any]) -> None:
    rebuilt = build_manifest(
        FIXTURE,
        [item["path"] for item in manifest["components"]],
        chain_id=manifest["chain_id"],
        block_number=manifest["block"]["number"],
        block_hash=manifest["block"]["hash"],
        evidence_counts=manifest["evidence_counts"],
        optional_failures=manifest["optional_failures"],
    )
    if (
        rebuilt != manifest
        or dumps(rebuilt) + b"\n" != (FIXTURE / "manifest.json").read_bytes()
    ):
        raise AssertionError("manifest rebuild changed bytes or digests")


def run_demo() -> dict[str, Any]:
    report = verify_fixture(FIXTURE)
    manifest = load(FIXTURE / "manifest.json")
    records = read_proof_records(FIXTURE / "proofs.jsonl")
    spoke_proof = proof_for(records, SPOKE)
    hub_proof = proof_for(records, HUB)
    server = make_server(FIXTURE, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        code = rpc_call(
            server.server_address, 1, "eth_getCode", [SPOKE, BLOCK_NUMBER]
        )
        spoke_slot = rpc_call(
            server.server_address, 2, "eth_getStorageAt", [SPOKE, "0x0", BLOCK_NUMBER]
        )
        hub_slot = rpc_call(
            server.server_address, 3, "eth_getStorageAt", [HUB, "0x0", BLOCK_NUMBER]
        )
        receipt = rpc_call(
            server.server_address, 4, "eth_getTransactionReceipt", [TRANSACTION]
        )
        logs = rpc_call(
            server.server_address,
            5,
            "eth_getLogs",
            [{"address": SPOKE, "blockHash": BLOCK_HASH}],
        )
        miss = rpc_call(
            server.server_address, 6, "eth_getStorageAt", [SPOKE, "0x2", BLOCK_NUMBER]
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    if code.get("result") != spoke_proof["code"] or not spoke_proof["code"].startswith(
        "0x6080604052"
    ):
        raise AssertionError("replayed code differs from the proved fixture code")
    spoke_slots = {item["key"]: item["value"] for item in spoke_proof["storage_proof"]}
    if (
        spoke_slots.get(SLOT_ZERO) != "0xb"
        or spoke_slots.get(SLOT_ONE) != SPOKE_SLOT_ONE_VALUE
        or spoke_slot.get("result") != SPOKE_SLOT_ZERO_WORD
    ):
        raise AssertionError("replayed spoke storage differs from the committed words")
    hub_slots = {item["key"]: item["value"] for item in hub_proof["storage_proof"]}
    if hub_slots.get(SLOT_ZERO) != "0x11" or hub_slot.get("result") != HUB_SLOT_ZERO_WORD:
        raise AssertionError("replayed hub slot 0x0 differs from the committed word")
    receipt_result = receipt.get("result")
    if not isinstance(receipt_result, dict) or (
        receipt_result.get("transactionHash") != TRANSACTION
        or receipt_result.get("blockHash") != BLOCK_HASH
    ):
        raise AssertionError("replayed receipt names another transaction or block")
    log_result = logs.get("result")
    if not isinstance(log_result, list) or len(log_result) != 1:
        raise AssertionError("replayed Aave v4 spoke log query changed")
    if any(
        item.get("address") != SPOKE or item.get("blockHash") != BLOCK_HASH
        for item in log_result
    ):
        raise AssertionError("replayed logs escape the Aave v4 spoke block query")
    if miss.get("error", {}).get("code") != MISS_ERROR:
        raise AssertionError("uncaptured slot 0x2 did not fail closed")

    reject_mutated_proof(manifest)
    rebuild_manifest_bytes(manifest)
    return {
        "fixture_digest": report["fixture_digest"],
        "code_bytes": (len(code["result"]) - 2) // 2,
        "spoke_slot_zero": spoke_slot["result"],
        "hub_slot_zero": hub_slot["result"],
        "receipt": receipt_result["transactionHash"],
        "logs": len(log_result),
        "miss": miss["error"]["code"],
    }


def main() -> int:
    report = run_demo()
    print(f"verified fixture: {report['fixture_digest']}")
    print(f"replayed code bytes: {report['code_bytes']}")
    print(f"replayed spoke slot 0x0: {report['spoke_slot_zero']}")
    print(f"replayed hub slot 0x0: {report['hub_slot_zero']}")
    print(f"replayed receipt: {report['receipt']}")
    print(f"replayed logs: {report['logs']}")
    print(f"slot 0x2 miss: {report['miss']}")
    print("one-nibble proof mutation: rejected")
    print("manifest rebuild: identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
