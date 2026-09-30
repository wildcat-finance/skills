from common import *
MP="0x4200000000000000000000000000000000000016"   # L2ToL1MessagePasser
L1B="0x4200000000000000000000000000000000000015"  # L1Block predeploy
def check(n):
    b=rpc("eth_getBlockByNumber",[hex(n),False])
    proof=rpc("eth_getProof",[MP,[],hex(n)])
    sh=proof.get("storageHash") if isinstance(proof,dict) else None
    wd=b.get("withdrawalsRoot")
    num=rpc("eth_call",[{"to":L1B,"data":"0x8381f58a"},hex(n)])   # L1Block.number()
    origin=int(num,16)
    l1=eth("eth_getBlockByNumber",[hex(origin),False])
    pbr=b.get("parentBeaconBlockRoot"); l1pbr=l1.get("parentBeaconBlockRoot")
    print(f"base {n:>10,} | withdrawalsRoot==MessagePasser storageHash: {wd==sh} ({(wd or 'absent')[:12]}…/{(sh or '?')[:12]}…) | L1 origin {origin:,} | header parentBeaconBlockRoot == origin's parentBeaconBlockRoot: {pbr==l1pbr} ({(pbr or 'absent')[:12]}… / {(l1pbr or 'absent')[:12]}…) | == L1 origin's own parent? n/a")
for n in (12_000_000,30_000_000,35_000_000,41_000_000,47_500_000,51_579_258): check(n)
