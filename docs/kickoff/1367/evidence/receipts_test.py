from common import *
from lazarus_lib.rlp import encode, encode_uint
from lazarus_lib.trieproof import trie_root
from lazarus_lib.hexvalue import hex_bytes, quantity_bytes
from lazarus_lib.receipts import encode_receipt
from lazarus_lib.errors import FormatError
import collections
def qb(x): return quantity_bytes(x,label="q")
def log_(l): return [hex_bytes(l["address"],label="a",length=20),[hex_bytes(t,label="t",length=32) for t in l["topics"]],hex_bytes(l["data"],label="d")]
def value(r,variant):
    t=int(r.get("type","0x0"),16)
    body=[qb(r["status"]),qb(r["cumulativeGasUsed"]),hex_bytes(r["logsBloom"],label="b",length=256),[log_(l) for l in r["logs"]]]
    if t==0x7e:
        if variant>=1: body.append(qb(r["depositNonce"]) if "depositNonce" in r else b"")
        if variant>=2 and "depositReceiptVersion" in r: body.append(qb(r["depositReceiptVersion"]))
    p=encode(body)
    return p if t==0 else bytes([t])+p
def root(rs,variant): return "0x"+trie_root([(encode_uint(i),value(r,variant)) for i,r in enumerate(rs)]).hex()
def run(label,fetch,n):
    hdr=fetch("eth_getBlockByNumber",[hex(n),False]); rs=fetch("eth_getBlockReceipts",[hex(n)])
    types=collections.Counter(r.get("type","0x0") for r in rs)
    dep=[r for r in rs if r.get("type")=="0x7e"]
    # 1. what Lazarus does today with a deposit receipt
    lz="n/a (no deposit receipt)"
    if dep:
        try: encode_receipt({"receipt_type":"0x7e","status":dep[0]["status"],"cumulative_gas_used":dep[0]["cumulativeGasUsed"],"logs_bloom":dep[0]["logsBloom"],"logs":[]}); lz="accepted?!"
        except FormatError as e: lz="refused: "+str(e)
    # 2. which encoding reproduces the header's receiptsRoot
    match=[v for v in (0,1,2) if root(rs,v)==hdr["receiptsRoot"]]
    fields=sorted({k for r in dep for k in r if k.startswith("deposit")})
    print(f"{label:8s} {n:>10,} txs={len(rs):>4} types={dict(types)} | Lazarus on 0x7e: {lz} | RPC deposit fields: {fields or '-'} | payload variants matching receiptsRoot (0=4 fields, 1=+depositNonce, 2=+depositReceiptVersion): {match or 'none'}")
if __name__=="__main__":
    run("ethereum",eth,26022093)
    via_receipts_route=lambda m,p: rpc(m,p,RECEIPTS_URL)
    for n in (2_357_105,5_000_000,10_000_000,12_000_000,30_000_000,41_000_000,51_579_258): run("base",via_receipts_route,n)
