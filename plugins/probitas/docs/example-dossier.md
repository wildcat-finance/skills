# Counterparty dossier: Acme Trading Ltd

<!-- marketplace-context:start -->
> **Marketplace context: Probitas.** Probitas builds a sourced record of what a counterparty did across lending venues from addresses they declared, without identifying a person or issuing a Wildcat verdict. Use Alexandria for archived lending inputs and Tabularium when the job is publishing a reusable credit-event release rather than assessing one counterparty. **Current frontier:** Morpho Midnight fixed-maturity coverage now ships API-scoped on Base; secondary-market borrow exits stay refused as unattributable and Morpho curation remains uncollected.
<!-- marketplace-context:end -->

Run `demo`.

This document was assembled by probitas from public sources. It carries no
rating and no recommendation. Every assertion below cites a transaction, a URL
or a document reference; anything that could not be sourced was dropped rather
than softened.

## Subject

**Entity.** Acme Trading Ltd

**Declared by the counterparty.**

- `0xa1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1`

## Coverage

What was checked, and what was not. A venue with no row here would be an
omission; a venue with a row saying nobody checked is a gap, and a gap is not
a clean record.

| Venue | Status | Range | Records | Note |
| --- | --- | --- | --- | --- |
| Aave v3 | unimplemented | -- | 0 | Reachable without a key after all, at api.aave.com/graphql. The \`activities\` query filtered by user returns borrows, repayments and liquidations, each with a txHash and an exact on-chain integer. Introspection is off; the schema is published in the aave-v4-sdk repository. The Graph gateway route needs a paid key; this does not. |
| Aave v4 | unimplemented | -- | 0 | Live on Ethereum mainnet since March 2026, hub and spoke rather than one pool, keyless at api.v4.aave.com/graphql. A borrower on v3 and a borrower on v4 are the same counterparty and the dossier should say so. |
| Centrifuge | unimplemented | -- | 0 | Keyless GraphQL at api.centrifuge.io, introspects cleanly, 24 pools on mainnet. Carries pools, holdings, investor transactions and debt changes. The most build-ready of the unbuilt venues. |
| Clearpool | unimplemented | -- | 0 | Live, and the API sits behind a bot challenge that returns 403 to a plain request. Working around that is not something this tool should do; an agreement with them is the way in. |
| Compound v3 | unimplemented | -- | 0 | No first-party API found. The Graph gateway rejects unauthenticated requests and the old hosted service is gone. |
| Euler v2 | empty | fixture | 0 | ethereum mainnet V3 event ledger; complete indexed coverage; no borrowing activity found for any subject EVC owner |
| Euler v1 | empty | fixture | 0 | ethereum mainnet canonical Euler v1 proxy log; Borrow, Repay and Liquidation events checked through finalized block 18000000; no borrowing activity found for any subject address |
| Goldfinch | unimplemented | -- | 0 | The protocol wound down in June 2026 after roughly 100 million dollars originated, with depositors reporting far heavier losses than the dashboard showed. The record stays on chain and is worth more to a dossier than most live venues, since it is a list of who did not repay. |
| Maple Finance | unimplemented | -- | 0 | api.maple.finance responds but disables introspection, so the query shape could not be established. Undercollateralised, so worth the work. |
| MetaMorpho vaults | unimplemented | -- | 0 | 450 vaults on mainnet, on the same keyless API. A counterparty can appear here as a curator rather than a borrower, and a curator who allocated into a market that took bad debt made a call that cost lenders money. Not collected yet. |
| Morpho Blue | checked | fixture | 3 | ethereum mainnet only; 3 record(s) across 1 address(es) |
| Morpho Midnight | checked | unpublished-50551562 | 6 | Base chain id 8453; all 1 user transaction cursor walk(s) exhausted across 1 page(s); observed\_at=1785374000; returned index through block 50551562; API history lower bound unpublished; API-scoped history only, not archive-chain completeness; 6 record(s) |
| Morpho Vaults V2 | unimplemented | -- | 0 | 474 vaults on mainnet, same API, separate surface from MetaMorpho with its own allocation transactions. Not collected yet. |
| TrueFi | unimplemented | -- | 0 | Restructured through 2025 and into a token migration completing May 2026. No public API endpoint answered. Historical undercollateralised loans are still the interesting part. |
| Wildcat | checked | fixture | 6 | mainnet only; 1 market(s) across 1 address(es) |

## What could not be established

| Subject | Status | Why |
| --- | --- | --- |
| aave-v3 borrowing history | unimplemented | Reachable without a key after all, at api.aave.com/graphql. The \`activities\` query filtered by user returns borrows, repayments and liquidations, each with a txHash and an exact on-chain integer. Introspection is off; the schema is published in the aave-v4-sdk repository. The Graph gateway route needs a paid key; this does not. |
| aave-v4 borrowing history | unimplemented | Live on Ethereum mainnet since March 2026, hub and spoke rather than one pool, keyless at api.v4.aave.com/graphql. A borrower on v3 and a borrower on v4 are the same counterparty and the dossier should say so. |
| centrifuge borrowing history | unimplemented | Keyless GraphQL at api.centrifuge.io, introspects cleanly, 24 pools on mainnet. Carries pools, holdings, investor transactions and debt changes. The most build-ready of the unbuilt venues. |
| clearpool borrowing history | unimplemented | Live, and the API sits behind a bot challenge that returns 403 to a plain request. Working around that is not something this tool should do; an agreement with them is the way in. |
| compound-v3 borrowing history | unimplemented | No first-party API found. The Graph gateway rejects unauthenticated requests and the old hosted service is gone. |
| goldfinch borrowing history | unimplemented | The protocol wound down in June 2026 after roughly 100 million dollars originated, with depositors reporting far heavier losses than the dashboard showed. The record stays on chain and is worth more to a dossier than most live venues, since it is a list of who did not repay. |
| maple borrowing history | unimplemented | api.maple.finance responds but disables introspection, so the query shape could not be established. Undercollateralised, so worth the work. |
| metamorpho borrowing history | unimplemented | 450 vaults on mainnet, on the same keyless API. A counterparty can appear here as a curator rather than a borrower, and a curator who allocated into a market that took bad debt made a call that cost lenders money. Not collected yet. |
| morpho-vaults-v2 borrowing history | unimplemented | 474 vaults on mainnet, same API, separate surface from MetaMorpho with its own allocation transactions. Not collected yet. |
| truefi borrowing history | unimplemented | Restructured through 2025 and into a token migration completing May 2026. No public API endpoint answered. Historical undercollateralised loans are still the interesting part. |

## Borrowing history

| Date | Venue | Event | Detail | Source |
| --- | --- | --- | --- | --- |
| 2025-02-20 | morpho-blue | Drew | 9,000.000000 USDC | `0x61616161...6161` |
| 2025-03-21 | morpho-blue | Bad debt left unpaid | 1,450.000000 USDC | `0x62626262...6262` |
| 2025-03-21 | morpho-blue | Liquidated | collateral sold to cover 6,000.000000 USDC; the position was collateralised, so this is a price moving rather than a borrower walking away | `0x62626262...6262` |
| 2026-07-17 | morpho-midnight | Drew | drew 100 loan-token units; debt increased by 100 debt units | `0x11111111...1111` |
| 2026-07-17 | morpho-midnight | Liquidated | liquidation reduced debt by 100 debt units (100 repaid debt units, 0 realized bad-debt units); this was liquidation, not voluntary repayment | `0x22222222...2222` |
| 2026-07-30 | morpho-midnight | Terms set | fixed maturity at Unix time 1,784,300,400 seconds; Base chain id 8453 | [source](https://api.morpho.org/v0/midnight/markets/0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738) |
| 2026-07-30 | morpho-midnight | Token metadata | Wrapped Ether (WETH), 18 decimals | [source](https://api.morpho.org/v0/tokens/8453:0x4200000000000000000000000000000000000006) |
| 2026-07-30 | morpho-midnight | Maturity outcome | Outstanding at maturity: 100 debt units; Settled late through liquidation; 0 debt units at observation | `0x22222222...2222` |
| 2026-07-30 | morpho-midnight | Position observed | current position closed; 0 debt units at observation; indexed through block 50551562 | [source](https://api.morpho.org/v0/midnight/markets/0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738/users/0xa1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1/position) |
| 2025-02-20 | wildcat | Drew | 9,000,000.000000 USDC | `0x33333333...3333` |
| 2025-03-11 | wildcat | Repaid | 500,000.000000 USDC | `0x34343434...3434` |

## Wildcat markets

Terms the counterparty set for themselves, and whether they held to them.

| Date | Venue | Event | Detail | Source |
| --- | --- | --- | --- | --- |
| 2025-02-19 | wildcat | Standing | drew 9,000,000.000000 USDC; repaid 500,000.000000 USDC; penalty interest 41,000.000000 USDC; delinquent now; past the grace period now | `0x31313131...3131` |
| 2025-02-19 | wildcat | Terms set | Cygnus USD Coin, reserve ratio 20.00% (2000 bips), rate 12.00% (1200 bips), grace period 3d, penalty 10.00% (1000 bips) | `0x31313131...3131` |
| 2025-04-20 | wildcat | Went delinquent | held 20,000.000000 USDC against a requirement of 1,800,000.000000 USDC | `0x32323232...3232` |
| 2025-04-28 | wildcat | Withdrawal expired unpaid | requested 1,500,000.000000 USDC, paid 0.000000 USDC | `0x35353535...3535` |

## Counterparty graph

Limited to relationships the counterparty declared and relationships visible on
chain between the declared addresses. No inference from off-chain association.

No relationship between the declared addresses appears on chain in the venues checked, and none was declared.

## Public incident record

Insolvencies, exploits and enforcement actions, each with a source.

_Nothing to report._

## Addresses not declared

Addresses suspected but neither declared nor provably linked on chain. Findings
here are held apart from everything above and feed no conclusion.

_Nothing to report._

## Summary

Written by whoever runs this, from the sections above and nothing else. Probitas emits no rating: the specification leaves the question open and leans toward evidence without a score, because a score invites reliance the data cannot carry.
