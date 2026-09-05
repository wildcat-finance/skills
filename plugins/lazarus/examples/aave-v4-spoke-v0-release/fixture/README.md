# Aave v4 spoke v0 Lazarus fixture

This checked-in fixture preserves one finite Ethereum mainnet view of the Aave
v4 hub-and-spoke deployment at block `0x18ac22c` (`25870892`), tied to block
hash `0x11e9be2ff9ff6a04319af0b04c24b95f3f1117c2df79f44f94d208857d01af07`.

Two contracts are proved: the spoke
`0x973a023a77420ba610f06b3858ad991df6d85a08` and the Core hub
`0xcca852bc40e560adc3b1cc58ca5b55638ce826c9`.

The block and the two contracts were selected from the Aave v4 Ethereum
mainnet capture v1.0.0 held outside this repository, release id
`sha256:20d0f2e8c42bce8bea8dcac04e15d9df7d5a05274fee68c16b1be0a467e2af15`:
the hub addresses from its `hubs` collection, and the block from the newest
row in its `useractivities` collection, a `REPAY` at block `25870892` in
transaction
`0xdaa7ebd15335bf809ee414876846df98d40736e7d29e3eeaca8b434653b9313e`. That
capture reads a hosted indexer, so it selected the target but proves nothing
here; the receipt names the same block in its Ethereum mainnet response, and
every evidence claim below rests on this fixture's own recorded bytes.

The capture was made on 2026-09-02 through dRPC's public archive endpoint.
Block identity was independently cross-checked against Ethereum mainnet
PublicNode, which returned the same hash. Provider URLs and headers are not
fixture components.

The EIP-1186 account proofs bind each contract's code hash and storage root to
the captured header `stateRoot`. On the spoke, slots `0x0` (`0xb`) and `0x1` (a
packed word) are included and the code is checked against the proved
`codeHash`; on the hub, slot `0x0` (`0x11`) is included. The receipt and the
single-log block query remain recorded RPC evidence; the fixture does not
describe them as state-proof-backed.

Run the complete offline demonstration from the repository root:

```bash
python3 plugins/lazarus/examples/aave-v4-spoke-v0/demo.py
```

The script verifies the fixture before starting loopback replay, reads the
code, both proved slots, the named receipt and the one block log through
ordinary JSON-RPC, observes a Lazarus `-32070` miss for uncaptured slot `0x2`,
rejects a one-nibble proof mutation and rebuilds the identical manifest bytes.
It needs no provider and does not alter the checked-in fixture.

`manifest.json` binds the plan, header, RPC and proof records, this README, the
demo and the copied v1 schemas. Its header check proves internal consistency
with the named hash; the transaction receipt and the capture notes above are
the external provenance record, not an independently proved canonical-chain
claim.
