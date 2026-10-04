"""Verify the preserved Base pin responses offline, with Lazarus's own verifiers. Reads files only; opens no connection.

    python3 verify_base_pin.py base-pin-51579258
"""
import hashlib, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[4]          # the Skills checkout that holds this file
sys.path.insert(0, str(ROOT / "plugins/lazarus/scripts"))
from lazarus_lib.header import verify_header
from lazarus_lib.proofs import verify_proof_record
from lazarus_lib.hexvalue import hex_bytes, quantity_bytes
from lazarus_lib.rlp import encode, encode_uint
from lazarus_lib.trieproof import trie_root

d = pathlib.Path(sys.argv[1])
m = json.loads((d / "manifest.json").read_text())
by = {e["name"]: e for e in m["entries"]}
result = lambda name: json.loads((d / f"{by[name]['index']:02d}-{name}.response.json").read_bytes())["result"]
for e in m["entries"]:                                        # 1. every stored byte matches its recorded digest
    stem = f"{e['index']:02d}-{e['name']}"
    assert hashlib.sha256((d / f"{stem}.request.json").read_bytes()).hexdigest() == e["request_sha256"], stem
    assert hashlib.sha256((d / f"{stem}.response.json").read_bytes()).hexdigest() == e["response_sha256"], stem
print(f"digests: {len(m['entries'])} request/response pairs match the manifest")
assert result("chainid") == m["chain_id"]
hdr = result("header")                                        # 2. header hash, with chain_id carried in memory as 0x1
doc = {"schema_version": 1, "chain_id": "0x1", "number": hdr["number"], "hash": hdr["hash"], "parent_hash": hdr["parentHash"],
       "state_root": hdr["stateRoot"], "rpc_result": hdr}
info = verify_header(doc)
assert info["hash"] == m["expected_block_hash"], "header hash is not the pinned hash"
print("header: hash recomputes to the pin, fields", info["field_count"])
other = result("header-same-number-as-ethereum-pin")          # 3. the same-number request names a different block
assert other["hash"] != hdr["hash"] and other["number"] == "0x18d10cd"
print("same-number request: block", int(other["number"], 16), "has hash", other["hash"][:14] + "…, not the pin")
root = hex_bytes(hdr["stateRoot"], label="root", length=32)
for acct in ("multicall3", "permit2", "usdc"):                # 4. state proofs and code
    p, code = result(f"proof-{acct}"), result(f"code-{acct}")
    rec = {"schema_version": 1, "evidence": "proof-backed", "block_hash": hdr["hash"], "address": p["address"].lower(), "balance": p["balance"],
           "nonce": p["nonce"], "code_hash": p["codeHash"], "storage_hash": p["storageHash"], "code": code, "account_proof": p["accountProof"],
           "storage_proof": [{"key": x["key"], "value": x["value"], "proof": x["proof"]} for x in p["storageProof"]]}
    out = verify_proof_record(rec, state_root=root, expected_block_hash=hdr["hash"], expected_slots=[x["key"] for x in p["storageProof"]])
    print(f"proof {acct}: account_included={out['account_included']} storage_included={out['storage_included']}")
rs = result("receipts")                                       # 5. receipts root, deposit receipts with six payload fields
qb = lambda x: quantity_bytes(x, label="q")
def val(r):
    t = int(r.get("type", "0x0"), 16)
    body = [qb(r["status"]), qb(r["cumulativeGasUsed"]), hex_bytes(r["logsBloom"], label="b", length=256),
            [[hex_bytes(l["address"], label="a", length=20), [hex_bytes(x, label="t", length=32) for x in l["topics"]], hex_bytes(l["data"], label="d")] for l in r["logs"]]]
    if t == 0x7E:
        body += [qb(r["depositNonce"]), qb(r["depositReceiptVersion"])]
    payload = encode(body)
    return payload if t == 0 else bytes([t]) + payload
built = "0x" + trie_root([(encode_uint(i), val(r)) for i, r in enumerate(rs)]).hex()
assert built == hdr["receiptsRoot"], "receipts root mismatch"
print("receipts:", len(rs), "receipts rebuild the header's receiptsRoot")
print("ALL PASS")
