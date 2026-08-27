#!/usr/bin/env python3
"""Run the checked-in Goldfinch fixture without an archive provider."""

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


ADDRESS = "0x8bbd80f88e662e56b918c353da635e210ece93c6"
BLOCK_NUMBER = "0xc7da16"
BLOCK_HASH = "0x41119192a8acdaae5ab06ca8f1d5943fd7ca2fb0a14323642dd6daf74eed2cfc"
TRANSACTION = "0xa46a744d6d52528a660c1d99a4edde403504fe7a308118c7cc947819583ce699"
SLOT_ZERO = "0x" + "00" * 32
SLOT_ZERO_WORD = "0x" + "00" * 31 + "01"
MISS_ERROR = -32070


def rpc_call(address: tuple[str, int], identifier: int, method: str, params: list[Any]) -> dict[str, Any]:
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


def reject_mutated_proof(manifest: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as directory:
        changed = Path(directory) / "fixture"
        shutil.copytree(FIXTURE, changed)
        records = read_proof_records(changed / "proofs.jsonl")
        node = records[0]["account_proof"][0]
        records[0]["account_proof"][0] = node[:-1] + (
            "0" if node[-1] != "0" else "1"
        )
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
                raise AssertionError("proof mutation failed outside trie verification") from exc
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
    if rebuilt != manifest or dumps(rebuilt) + b"\n" != (FIXTURE / "manifest.json").read_bytes():
        raise AssertionError("manifest rebuild changed bytes or digests")


def run_demo() -> dict[str, Any]:
    report = verify_fixture(FIXTURE)
    manifest = load(FIXTURE / "manifest.json")
    proof = read_proof_records(FIXTURE / "proofs.jsonl")[0]
    server = make_server(FIXTURE, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        code = rpc_call(server.server_address, 1, "eth_getCode", [ADDRESS, BLOCK_NUMBER])
        slot = rpc_call(
            server.server_address,
            2,
            "eth_getStorageAt",
            [ADDRESS, "0x0", BLOCK_NUMBER],
        )
        receipt = rpc_call(
            server.server_address,
            3,
            "eth_getTransactionReceipt",
            [TRANSACTION],
        )
        logs = rpc_call(
            server.server_address,
            4,
            "eth_getLogs",
            [{"address": ADDRESS, "blockHash": BLOCK_HASH}],
        )
        miss = rpc_call(
            server.server_address,
            5,
            "eth_getStorageAt",
            [ADDRESS, "0x1", BLOCK_NUMBER],
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    if code.get("result") != proof["code"] or not proof["code"].startswith("0x36"):
        raise AssertionError("replayed code differs from the proved fixture code")
    if (
        proof["storage_proof"][0]["key"] != SLOT_ZERO
        or proof["storage_proof"][0]["value"] != "0x1"
        or slot.get("result") != SLOT_ZERO_WORD
    ):
        raise AssertionError("replayed slot 0x0 differs from the committed word")
    receipt_result = receipt.get("result")
    if not isinstance(receipt_result, dict) or (
        receipt_result.get("transactionHash") != TRANSACTION
        or receipt_result.get("blockHash") != BLOCK_HASH
    ):
        raise AssertionError("replayed receipt names another transaction or block")
    log_result = logs.get("result")
    if not isinstance(log_result, list) or len(log_result) != 5:
        raise AssertionError("replayed Goldfinch log query changed")
    if any(item.get("address") != ADDRESS or item.get("blockHash") != BLOCK_HASH for item in log_result):
        raise AssertionError("replayed logs escape the Goldfinch block query")
    if miss.get("error", {}).get("code") != MISS_ERROR:
        raise AssertionError("uncaptured slot 0x1 did not fail closed")

    reject_mutated_proof(manifest)
    rebuild_manifest_bytes(manifest)
    return {
        "fixture_digest": report["fixture_digest"],
        "code_bytes": (len(code["result"]) - 2) // 2,
        "slot_zero": slot["result"],
        "receipt": receipt_result["transactionHash"],
        "logs": len(log_result),
        "miss": miss["error"]["code"],
    }


def main() -> int:
    report = run_demo()
    print(f"verified fixture: {report['fixture_digest']}")
    print(f"replayed code bytes: {report['code_bytes']}")
    print(f"replayed slot 0x0: {report['slot_zero']}")
    print(f"replayed receipt: {report['receipt']}")
    print(f"replayed logs: {report['logs']}")
    print(f"slot 0x1 miss: {report['miss']}")
    print("one-nibble proof mutation: rejected")
    print("manifest rebuild: identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
