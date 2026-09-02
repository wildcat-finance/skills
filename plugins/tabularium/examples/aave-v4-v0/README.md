# Aave v4 mainnet credit window v0

A checked-in, offline-verifiable Tabularium release: every Aave v4 user
activity on Ethereum mainnet in blocks `25855441` through `25870892`, with the
borrow and repay rows mapped to canonical event schema v2 and everything else
preserved and counted but left unmapped.

- **Release:** `aave-v4-mainnet-credit-window-v0`
- **Adapter:** `aave-v4` 1.0.0, protocol generation `aave-v4`
- **Source API:** The Graph, subgraph `2Gu5HCAnWrNk2pXidscdhNEQhrwLgMKmssuCe9JhZhAe`
- **Evidence class:** `hosted-indexer-reported-block-window`
- **Events:** 500 — 282 `borrowing`, 218 `repayment`
- **Preserved and unmapped:** 376 `SUPPLY`, 264 `WITHDRAW`, 111 `SET_COLLATERAL`
- **Canonical digest:** `a54a7ff15cfe9aa43639b00bb07036f0ebc2e832ac37f44fcee2b0dd0684daa4`

## Where the rows came from

The window is a slice of the Aave v4 Ethereum mainnet capture v1.0.0 held
outside this repository, release id
`sha256:20d0f2e8c42bce8bea8dcac04e15d9df7d5a05274fee68c16b1be0a467e2af15`,
which pins subgraph state at block `25870926`. The upper bound `25870892` is
the newest credit event in that capture, and it is also the block preserved by
the Lazarus `aave-v4-spoke-v0` and `aave-v4-spoke-v1` fixtures, so the state
and event views share one boundary.

The bounds were chosen for this release. They are not a protocol milestone,
and the window is not complete Aave v4 history.

## Verify and rebuild offline

Neither command opens a network connection:

```bash
python3 plugins/tabularium/scripts/tabularium.py verify \
  plugins/tabularium/examples/aave-v4-v0/coverage.json
python3 plugins/tabularium/examples/aave-v4-v0/rebuild.py
```

`verify` recomputes the canonical digest, the row count and every mapped and
unmapped tally from the preserved bytes. `rebuild.py` re-derives
`events.jsonl` and `coverage.json` in a temporary directory from
`source.json` and `capture.json` alone, then compares both with the committed
bytes.

## What this release does not establish

`coverage.json` carries the full list. The load-bearing ones:

- The hosted indexer reported the block window. This release does not
  independently prove the chain boundary.
- Activity rows report no block hash, transaction index or underlying token
  address, so every amount leg names a `null` asset. The reserve identifier
  stays in `native_record`.
- A `REPAY` row reports no drawn amount. Its asset leg reads
  `totalAmountRepaid` and no drawn value is reconstructed.
- The release is unsigned. Offline verification proves internal consistency,
  not publisher identity or authenticity.
