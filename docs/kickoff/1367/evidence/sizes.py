from common import *
IMPL="0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3"; ADMIN="0x10d6a54a4754c8869d6886b5f5d7fbfa5b4522237ea5c60d11bc4e7a1ff9390b"
C={"ethereum":(eth,26022093,"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",lambda m,p:eth(m,p)),"base":(rpc,51579258,"0x833589fCD6eDb6E08f4C7C32D4f71b54bDA02913",lambda m,p:rpc(m,p,RECEIPTS_URL))}
j=lambda o:len(json.dumps(o,separators=(",",":")))
for k,(f,n,usdc,fr) in C.items():
    n_=hex(n); h=f("eth_getBlockByNumber",[n_,False]); hf=f("eth_getBlockByNumber",[n_,True]); rs=fr("eth_getBlockReceipts",[n_])
    acc={}
    for name,a,s in (("Multicall3","0xcA11bde05977b3631167028862bE2a173976CA11",[]),("Permit2","0x000000000022D473030F116dDEE9F6B43aC78BA3",[]),("USDC",usdc,[ADMIN,IMPL])):
        acc[name]=j(f("eth_getProof",[a,s,n_]))+j(f("eth_getCode",[a,n_]))
    print(k,"header",j(h),"B | block with txs",j(hf),"B | receipts",len(rs),"=",j(rs),"B | per-account proof+code",acc,"| total planned ~",j(h)+j(rs)+sum(acc.values()),"B")
