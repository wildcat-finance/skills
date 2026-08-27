# Goldfinch v0 Lazarus fixture

This checked-in fixture preserves one finite Ethereum mainnet view of the
Goldfinch market `0x8bbd80f88e662e56b918c353da635e210ece93c6` at block
`0xc7da16` (`13097494`). It is tied to block hash
`0x41119192a8acdaae5ab06ca8f1d5943fd7ca2fb0a14323642dd6daf74eed2cfc`.

The market and transaction were selected from the first row of Tabularium's
checked-in Goldfinch release. Transaction
`0xa46a744d6d52528a660c1d99a4edde403504fe7a308118c7cc947819583ce699`
names that block in its Ethereum mainnet receipt. The capture was made on
2026-08-16 through dRPC's public archive endpoint and independently
cross-checked against PublicNode for the receipt and block identity. Provider
URLs and headers are not fixture components.

The EIP-1186 account proof binds the contract's code hash and storage root to
the captured header `stateRoot`. Slot `0x0` is included with value `0x1`, and
the code is checked against the proved `codeHash`. The receipt and five-log
query remain recorded RPC evidence; the fixture does not describe them as
state-proof-backed.

Run the complete offline demonstration from the repository root:

```bash
python3 plugins/lazarus/examples/goldfinch-v0/demo.py
```

The script verifies the fixture before starting loopback replay, reads the
code, slot, named receipt and five logs through ordinary JSON-RPC, observes a
Lazarus `-32070` miss for uncaptured slot `0x1`, rejects a one-nibble proof
mutation and rebuilds the identical manifest bytes. It needs no provider and
does not alter the checked-in fixture.

`manifest.json` binds the plan, header, RPC and proof records, this README,
the demo and the copied v1 schemas. Its header check proves internal
consistency with the named hash; the transaction receipt and capture notes are
the external provenance record, not an independently proved canonical-chain
claim.
