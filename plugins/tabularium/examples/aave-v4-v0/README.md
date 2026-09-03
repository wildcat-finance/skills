# Aave v4 mainnet credit window v0

A checked-in, offline-verifiable Tabularium release built from Ethereum
consensus logs: every Aave v4 borrow and repay in blocks `25855441` through
`25870892`, mapped to canonical event schema v2.

| Field | Value |
| --- | --- |
| Release | `aave-v4-mainnet-credit-window-v0` |
| Adapter | `aave-v4` 2.0.0, protocol generation `aave-v4` |
| Source API | `ethereum-json-rpc` |
| Evidence class | `native-log` |
| Events | 500: 282 `borrowing`, 218 `repayment` |
| Spokes emitting | 9 |
| Assets | 10, each with a symbol and decimals read from its own contract |
| Canonical digest | `490d3f6399f84af8a81a5401b3cc92bf7ecfbe98a6bb02f07215b9099625ccf7` |

## What was captured

Two `eth_getLogs` topics over a fixed block range:

```
BORROW  0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd
REPAY   0xd765a0263e8a360da8dd4fdb8c0dc5553adec12a96f29a462cdb45e5bea407dd
```

The scope is the topic pair and the block range, both stated in
`capture.json`. Emitting addresses are whatever the chain reported, not a list
supplied from elsewhere, so no registry or indexer decided what is in scope.

Each log names a spoke and an asset id but not a token. `source.json`
therefore also preserves the supporting reads that resolve them, each with the
call it made and the bytes it returned:

- 35 `getReserve(uint256)` calls, one per spoke and asset id, whose first word
  is the underlying token and whose second is the owning hub
- 10 `symbol()` and 10 `decimals()` calls, one pair per underlying

The upper bound `25870892` is the block the Lazarus `aave-v4-spoke-v0` and
`aave-v4-spoke-v1` fixtures preserve, and this capture read the same block
hash `0x11e9be2ff9ff6a04319af0b04c24b95f3f1117c2df79f44f94d208857d01af07`
independently. The state and event views share one boundary.

The bounds were chosen for this release. They are not a protocol milestone,
and the window is not complete Aave v4 history.

## Verify and rebuild offline

Neither command opens a network connection:

```bash
python3 plugins/tabularium/scripts/tabularium.py verify \
  plugins/tabularium/examples/aave-v4-v0/coverage.json
python3 plugins/tabularium/examples/aave-v4-v0/rebuild.py
```

`verify` recomputes the canonical digest, the row count and every tally from
the preserved bytes, and re-derives each event from its log. `rebuild.py`
rebuilds `events.jsonl` and `coverage.json` in a temporary directory from
`source.json` and `capture.json` alone, then compares both with the committed
bytes.

The adapter checks the preserved reads against themselves: a `getReserve`
record whose convenience fields disagree with the bytes its call returned is
refused, as is a token whose stated decimals disagree with its own result.

## What this release does not establish

`coverage.json` carries the full list. The ones that matter most:

- The provider reported these logs and the block hashes they name. This
  release does not independently prove the chain boundary.
- A repay log carries five data words. Only the first two are established,
  and the last three were zero in every preserved log, so the adapter never
  names them. The raw log is retained in full.
- The share leg names no asset, because shares are the spoke's own accounting
  unit rather than a token.
- Supply, withdraw and collateral-flag activity falls outside the two captured
  topics. It is neither preserved nor counted here.
- The release is unsigned. Offline verification proves internal consistency,
  not publisher identity or authenticity.
