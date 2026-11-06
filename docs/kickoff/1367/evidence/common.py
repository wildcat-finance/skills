import os, sys, json, time, pathlib, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[4]   # the Skills checkout that holds this file
sys.path.insert(0,str(ROOT/"plugins/lazarus/scripts"))
# Two Base routes, read from the environment and never recorded: LAZARUS_BASE_RPC answers headers, state and proofs;
# LAZARUS_BASE_RPC_RECEIPTS answers eth_getBlockReceipts. Ethereum comes from ALEXANDRIA_COMPOUND_RPC_URL and ALEXANDRIA_RPC_BEARER.
BASE=os.environ["LAZARUS_BASE_RPC"]
RECEIPTS_URL=os.environ["LAZARUS_BASE_RPC_RECEIPTS"]
def rpc(method,params,url=BASE,bearer=None):
    err=None
    for a in range(8):
        try:
            time.sleep(0.25)
            h={"content-type":"application/json","user-agent":"curl/8.7.1"}
            if bearer: h["authorization"]="Bearer "+bearer
            r=json.load(urllib.request.urlopen(urllib.request.Request(url,json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),h),timeout=90))
            if "error" in r:
                if r["error"].get("code") in (-32016,15,30): raise RuntimeError("rate")
                return {"__error__":r["error"]}
            return r["result"]
        except Exception as e: err=e; time.sleep(min(20,2**a))
    raise err
def eth(method,params):
    return rpc(method,params,os.environ["ALEXANDRIA_COMPOUND_RPC_URL"],os.environ["ALEXANDRIA_RPC_BEARER"])
