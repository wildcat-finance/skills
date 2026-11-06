from common import *
from lazarus_lib.proofs import verify_proof_record
from lazarus_lib.hexvalue import hex_bytes
from lazarus_lib.errors import IntegrityError, FormatError
IMPL="0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3"
ADMIN="0x10d6a54a4754c8869d6886b5f5d7fbfa5b4522237ea5c60d11bc4e7a1ff9390b"
CHAINS={"ethereum":{"fetch":eth,"n":26022093,"usdc":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"},
        "base":{"fetch":rpc,"n":51579258,"usdc":"0x833589fCD6eDb6E08f4C7C32D4f71b54bDA02913"}}
ACCTS=lambda c:[("Multicall3","0xcA11bde05977b3631167028862bE2a173976CA11",[]),("Permit2","0x000000000022D473030F116dDEE9F6B43aC78BA3",[]),("USDC",c["usdc"],[ADMIN,IMPL])]
def record(c,addr,slots,hdr):
    f=c["fetch"]; n=hex(c["n"])
    p=f("eth_getProof",[addr,slots,n]); code=f("eth_getCode",[addr,n])
    return {"schema_version":1,"evidence":"proof-backed","block_hash":hdr["hash"],"address":addr.lower(),"balance":p["balance"],"nonce":p["nonce"],
            "code_hash":p["codeHash"],"storage_hash":p["storageHash"],"code":code,"account_proof":p["accountProof"],
            "storage_proof":[{"key":x["key"],"value":x["value"],"proof":x["proof"]} for x in p["storageProof"]]}
hdrs={k:c["fetch"]("eth_getBlockByNumber",[hex(c["n"]),False]) for k,c in CHAINS.items()}
recs={}
for k,c in CHAINS.items():
    for name,addr,slots in ACCTS(c):
        recs[(k,name)]=(record(c,addr,slots,hdrs[k]),slots)
for (k,name),(r,slots) in recs.items():
    root=hex_bytes(hdrs[k]["stateRoot"],label="r",length=32)
    try: out=verify_proof_record(r,state_root=root,expected_block_hash=hdrs[k]["hash"],expected_slots=slots); res=f"PASS account_included={out['account_included']} storage_included={out['storage_included']}"
    except (IntegrityError,FormatError) as e: res="FAIL "+type(e).__name__+": "+str(e)[:80]
    print(f"{k:8s} {name:10s} code_hash={r['code_hash'][:14]}… slots={len(slots)} -> {res}")
# negative: a proof from one chain against the other chain's header
for name in ("Multicall3","Permit2","USDC"):
    r,slots=recs[("base",name)]
    root=hex_bytes(hdrs["ethereum"]["stateRoot"],label="r",length=32)
    try: verify_proof_record(r,state_root=root,expected_block_hash=hdrs["base"]["hash"],expected_slots=slots); print("NEG base",name,"vs ethereum stateRoot: ACCEPTED (bad)")
    except (IntegrityError,FormatError) as e: print("NEG base",name,"proof vs Ethereum stateRoot ->",type(e).__name__+": "+str(e)[:70])
    try: verify_proof_record(r,state_root=hex_bytes(hdrs["base"]["stateRoot"],label="r",length=32),expected_block_hash=hdrs["ethereum"]["hash"],expected_slots=slots); print("NEG base",name,"vs ethereum block hash: ACCEPTED (bad)")
    except (IntegrityError,FormatError) as e: print("NEG base",name,"proof vs Ethereum block hash ->",type(e).__name__+": "+str(e)[:70])
