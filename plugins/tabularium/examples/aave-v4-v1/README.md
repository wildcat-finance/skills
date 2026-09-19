# Aave v4 mainnet credit window v1

A checked-in, offline-verifiable Tabularium release built from Ethereum
consensus logs: every Aave v4 borrow and repay in blocks `25855441` through
`25870892`, mapped to canonical event schema v3.

This release supersedes
[`aave-v4-v0`](../aave-v4-v0/README.md), which carries release
`aave-v4-mainnet-credit-window-v0` under schema v2. Both were built from the
same `source.json`, byte for byte, and the only difference in a canonical row
is `schema_version`. The v0 release stays on disk and stays verifiable; it is
not migrated in place.

| Field | Value |
| --- | --- |
| Release | `aave-v4-mainnet-credit-window-v1` |
| Supersedes | `aave-v4-mainnet-credit-window-v0` |
| Adapter | `aave-v4` 2.0.0, protocol generation `aave-v4` |
| Source API | `ethereum-json-rpc` |
| Evidence class | `native-log` |
| Events | 500: 282 `borrowing`, 218 `repayment` |
| Spokes emitting | 9 |
| Assets | 10, each with a symbol and decimals read from its own contract |
| Canonical digest | `81d416a10b70ab0f3d9a3bd41c0680e235b3b64f4f06cc36b4f4292c81136492` |

## What was captured

Two `eth_getLogs` topics over a fixed block range:

```
BORROW  0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd
REPAY   0xd765a0263e8a360da8dd4fdb8c0dc5553adec12a96f29a462cdb45e5bea407dd
```

The scope is the topic pair and the block range, both stated in
`capture.json`. Emitting addresses are whatever the chain reported, not a list
supplied from elsewhere, so no registry or indexer decided what is in scope.

`capture.json` differs from the v0 capture in one field, `release`. The
request it records, the scope and the source digest are unchanged.

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

| File | SHA-256 |
| --- | --- |
| `source.json` | `1d88fdb5bca293995fd02e5a59f060d74541c80405e7bf1987544e5f334a8744` |
| `capture.json` | `c5ea81d7c065792498f9b7359f30a8a6a9d0c5a587bc7bfdf81cee60365ca89a` |
| `events.jsonl` | `81d416a10b70ab0f3d9a3bd41c0680e235b3b64f4f06cc36b4f4292c81136492` |
| `coverage.json` | `fb2d96db06d1ebf9b1e89529ddaa7dfbf7931960dd57745dde166dc73089d49b` |

## Verify and rebuild offline

Neither command opens a network connection:

```bash
python3 plugins/tabularium/scripts/tabularium.py verify \
  plugins/tabularium/examples/aave-v4-v1/coverage.json
python3 plugins/tabularium/examples/aave-v4-v1/rebuild.py
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

See [DATA-DICTIONARY.md](DATA-DICTIONARY.md) for field meanings and limits.
