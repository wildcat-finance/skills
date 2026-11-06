from common import *
from lazarus_lib.header import verify_header, header_fields
EMPTY_WD="0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
def doc(b):
    return {"schema_version":1,"chain_id":"0x1","number":b["number"],"hash":b["hash"],"parent_hash":b["parentHash"],"state_root":b["stateRoot"],"rpc_result":b}
def run(label,fetch,n):
    b=fetch("eth_getBlockByNumber",[hex(n),False])
    optional=[k for k in ("baseFeePerGas","withdrawalsRoot","blobGasUsed","excessBlobGas","parentBeaconBlockRoot","requestsHash") if k in b]
    wd=b.get("withdrawalsRoot")
    try:
        r=verify_header(doc(b)); res="PASS"
    except Exception as e: res="FAIL "+type(e).__name__+": "+str(e)[:90]
    print(f"{label:9s} {n:>9,} {res:5s} fields={len(header_fields(doc(b))) if res=='PASS' else '-'} extraData={(len(b['extraData'])-2)//2}B withdrawalsRoot={'absent' if wd is None else ('empty-trie' if wd==EMPTY_WD else 'non-empty')} optional={','.join(o for o in optional if o not in ('baseFeePerGas',))}")
if __name__=="__main__":
    run("ethereum",eth,26022093)
    for n in (2356365,2357105,3_000_000,5_000_000,8_000_000,10_000_000,12_000_000,15_000_000,18_000_000,20_000_000,25_000_000,30_000_000,35_000_000,38_000_000,41_000_000,44_000_000,46_000_000,47_500_000,49_000_000,51_579_258):
        run("base",rpc,n)
