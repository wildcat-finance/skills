from common import *
import datetime
MP="0x4200000000000000000000000000000000000016"
for n in (51_579_258,51_500_000,51_000_000):
    p=rpc("eth_getProof",[MP,[],hex(n)]); b=rpc("eth_getBlockByNumber",[hex(n),False])
    print(f"withdrawalsRoot == L2ToL1MessagePasser storageHash at {n:,}:",p["storageHash"]==b["withdrawalsRoot"],b["withdrawalsRoot"])
head=int(rpc("eth_blockNumber",[]),16)
def ok(n):
    p=rpc("eth_getProof",[MP,[],hex(n)]); return isinstance(p,dict) and "storageHash" in p
lo,hi=47_500_000,51_000_000
assert not ok(lo) and ok(hi)
while hi-lo>1:
    mid=(lo+hi)//2
    if ok(mid): hi=mid
    else: lo=mid
hb=rpc("eth_getBlockByNumber",[hex(head),False]); b=rpc("eth_getBlockByNumber",[hex(hi),False])
print(f"head {head:,} at {datetime.datetime.fromtimestamp(int(hb['timestamp'],16),datetime.UTC).isoformat()}; oldest block with a served eth_getProof {hi:,} ({head-hi:,} blocks, {(int(hb['timestamp'],16)-int(b['timestamp'],16))/86400:.2f} days back)")
pin_out_head=51_579_258+(head-hi)
print(f"the route stops serving proofs for the pin when head reaches about {pin_out_head:,}, {(pin_out_head-head)*2/86400:.1f} days after this run")
