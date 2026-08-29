# Euler data-source discovery

Captured on 2026-08-16 for
[wildcat-finance/skills#57](https://github.com/wildcat-finance/skills/issues/57).
This records why Euler v2 uses the V3 Data API rather than Goldsky, and why
Euler v1 uses the canonical proxy log rather than any surviving Euler API.

## Result

Euler v2 has a live public Goldsky subgraph, but it is deliberately a
current-state index rather than a borrowing-history source. Probitas instead
uses Euler's keyless V3 event API and ships a v2 adapter.

Euler v1's Messari subgraph, legacy EulerScan websocket and legacy Data API
routes are unusable. The canonical proxy still carries borrower-indexed
`Borrow`, `Repay` and `Liquidation` events. A keyless archival RPC serves those
logs, so Probitas ships a separate v1 adapter against the chain itself.

## Euler v2

The first-party endpoint for Ethereum mainnet is:

```text
https://api.goldsky.com/api/public/project_cm4iagnemt1wp01xn4gh1agft/subgraphs/euler-simple-mainnet/latest/gn
```

The checked-in source schema at Euler commit
`025c787a834699b7d22ebc1fe869f72c3eeb6065` is preserved byte for byte in
[`euler-v2-goldsky-schema.graphql`](euler-v2-goldsky-schema.graphql). The live
endpoint accepted introspection and exposed the same three entity families:

- `Vault`: vault address and creating factory;
- `TrackingActiveAccount`: one 19-byte address prefix grouping the main EVC
  account and all 256 sub-accounts; and
- `TrackingVaultBalance`: the latest observed balance and debt for one
  account-vault pair.

The representative response in
[`euler-v2-goldsky-sample.json`](euler-v2-goldsky-sample.json) came from this
query:

```graphql
query($prefix: Bytes!) {
  trackingVaultBalances(
    first: 100
    orderBy: id
    orderDirection: asc
    where: { addressPrefix: $prefix, debt_gt: 0 }
  ) {
    id
    vault
    addressPrefix
    account
    balance
    debt
    blockNumber
    blockTimestamp
    transactionHash
  }
  _meta { block { number hash } deployment hasIndexingErrors }
}
```

The variable was the public on-chain prefix
`0xa47b8a0f97f4f666a99d672b2aa2481e8d0180`. The capture boundary was block
25770110, deployment `QmarAreSkQbcWfUbKJW2EJ1N3XyAGxzHVnzG85F8B3ZmSe`, with
`hasIndexingErrors: false`.

The subgraph handler calls `debtOf(account)` after a vault `Transfer`, `Borrow`
or `Repay` and overwrites the same `TrackingVaultBalance`. Its
`transactionHash` is therefore the last indexed vault interaction, not
necessarily the transaction that created the outstanding debt. Repaid
positions are removed from `TrackingActiveAccount.borrows`. These properties
make the source useful for discovering active positions but insufficient for
answering what an address borrowed and repaid over time. In particular, an
empty result cannot distinguish never borrowed from fully repaid.

The older full Euler v2 branch defines immutable `Borrow`, `Repay`,
`Liquidate`, `PullDebt` and `DebtSocialized` entities. Its last deployment file
named `euler-v2-mainnet/1.0.11`, but that pinned URL and the corresponding
`latest` URL both returned HTTP 404 during this capture. The shipped adapter
does not depend on either endpoint.

## Euler v2 history source

The adapter reads the first-party keyless service at
`https://v3.euler.finance`:

- `/v3/activity/accounts/<EVC owner>/events` for borrow, repayment,
  liquidation, debt socialisation, debt transfer and interest-accrual events;
- `/v3/liquidations` for the debt and collateral legs of each liquidation; and
- `/v3/evk/vaults/batch` for vault assets, symbols and decimals.

Every account response reports `source: v3-ponder` and a per-chain coverage
object. The adapter accepts Ethereum mainnet only and refuses any response
whose coverage is partial, syncing or missing a category. Pagination must end
without a repeated cursor. Each event must belong to the requested EVC owner,
and its account must satisfy the EVC subaccount relation.

`interest_accrued` is deliberately omitted because it is not a new draw. It is
still part of the requested event vocabulary, so its presence cannot cause a
borrow beside it to be dropped. Liquidations are matched between the activity
ledger and `/v3/liquidations`, then checked against cached vault metadata.
Only exact integer amounts enter evidence; the API's floating-point USD fields
are not used.

## Euler v1

Euler v1 does not use the current Euler Goldsky project. Graph Explorer names
the source `Euler Finance Ethereum` and links to
`https://github.com/messari/subgraphs`. The current identifiers are:

```text
Subgraph ID: 95nyAWFFaiz6gykko3HtBCyhRuP5vZzuKYsZiLxHxLhr
Version: 1.3.0_1.4.0
Deployment ID: QmfTzwSoE3krDFMfYT9XTdwLcdMYBmMwyPqA1FHTMkmsVs
Schema ID: QmVPZNPakG2WBJ9AaTi3gcMp6uG538vGJMYcTCUW7m8S74
Endpoint: https://gateway.thegraph.com/api/<API_KEY>/subgraphs/id/95nyAWFFaiz6gykko3HtBCyhRuP5vZzuKYsZiLxHxLhr
```

The supplied `QmVRgUkhh7L46fH7A2XFvC3L8uR2YjCH8bT97M6XGk6nKx` deployment ID
does not match the current Graph Explorer version. The current schema is
preserved byte for byte in `euler-v1-thegraph-schema.graphql`, with its SHA-256
and source identifiers in `euler-v1-thegraph-capture.json`.

The schema can support borrower queries without account snapshots:

- `Borrow.to` is the borrower and `Borrow.amount` is the exact native token
  amount;
- `Repay.from` is the repaying account and `Repay.amount` is exact;
- `Liquidate.liquidatee` is the liquidated account; its `amount` is seized
  collateral, while the exact debt amount repaid is not stored; and
- every event carries transaction hash, log index, block and timestamp.

The authenticated gateway accepted the credential but returned no data for
`_meta`, accounts, markets or borrows. It reported one indexer returning 400,
one too far behind and one unavailable. Probitas cannot turn that response
into either history or an `empty` finding.

### The migration guide does not expose protocol v1

Euler's Data migration guide covers API versions v1 and v2, not Euler protocol
v1 and v2. The live V3 OpenAPI document had 102 paths during this capture. It
named EVK, EVC and Euler Earn resources and had no Euler protocol v1 resource
or protocol-version selector.

The account event ledger reported an indexed lower bound of block 20529207.
The first v1 `Borrow` found below was at block 14531589, so the V3 ledger starts
5,997,618 blocks after that v1 activity. The old `/v1/account/balances`,
`/v1/vault/totals` and `/v2/account/positions` routes each returned HTTP 404
with `All API endpoints are under /v3/*`. They did not return the guide's stated
`410 Gone`, but neither response contained protocol data.

### The old history service is gone

Euler's archived
[`euler-history-api`](https://github.com/euler-legacy-xyz/euler-history-api)
client points to `wss://escan-mainnet.euler.finance`. That hostname no longer
resolves. Its code establishes that Euler once served a dedicated log history,
but it cannot support a current coverage claim.

### Canonical log source

The archived contract source defines:

```solidity
event Borrow(address indexed underlying, address indexed account, uint amount);
event Repay(address indexed underlying, address indexed account, uint amount);
event Liquidation(
    address indexed liquidator,
    address indexed violator,
    address indexed underlying,
    address collateral,
    uint repay,
    uint yield,
    uint healthScore,
    uint baseDiscount,
    uint discount
);
```

The mainnet address manifest binds those events to the canonical proxy:

```text
0x27182842E098f60e3D576794A5bFFb0777E025d3
```

`https://mainnet.gateway.tenderly.co` accepted a keyless `eth_getLogs` query
from block 0 through `latest`, filtered by that proxy and the indexed borrower.
For the public account
`0x1ec0dde402dae69021492e7a9c4cbfdf72ffd84a`, the response contained 16
events: 10 borrows and 6 repayments. The first was block 14531589, transaction
`0xc84b736abd7f5414bdcd66c3b1b33c21041bf3ea1b8f4c4cb67e1c104d1bfa26`.

The adapter queries through the RPC's `finalized` block, requires every log to
come from the proxy and requested borrower topic, and rejects removed logs.
It fetches each event block again and requires the block hash to match before
using its timestamp. Token symbol and decimals come from `eth_call` at the same
finalized boundary. Unlike the Messari schema, the canonical `Liquidation`
event contains both the debt repaid and collateral seized as exact integers.

## Safe next sources

Euler v2 is covered by the V3 adapter and offline fixtures. Euler v1 is covered
by the canonical proxy-log adapter and its own fixtures. The preserved Graph
schema and failed API probes explain why neither adapter depends on the older
services.
