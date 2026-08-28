# Euler V2 v0 data dictionary

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

`events.jsonl` contains canonical event v2 rows. Exact amounts remain decimal
strings in base units.

| Field | Meaning |
| --- | --- |
| `schema_version` | Canonical event revision; `2` here. |
| `id` | Deterministic identifier derived from chain, adapter, transaction, log and mapping rule. |
| `event_family` | Common family without erasing venue meaning. Interest accrual has its own family. |
| `action` | Exact Euler V2 action. |
| `venue` | `euler-v2`. |
| `chain` | `ethereum-mainnet`. |
| `transaction` | Transaction hash, block/log indexes and source timestamp; block hash and transaction index are null because the API omitted them. |
| `parties` | EVC owner, touched sub-account and any actor or counterparty. |
| `instrument` | EVK vault address. |
| `amounts` | Every source amount leg, with an address only when the source row names one. |
| `provenance` | Hosted-index source, selector, mapping rule, adapter, `euler-v2` protocol generation and `euler-v3` source API. |
| `native_record` | Complete source activity row retained beside its interpretation. |

The owner and sub-account are separate. The adapter checks that the sub-account
shares the owner's first nineteen bytes and matches `subAccountIndex`.
`interest_accrued` is balance growth, not a draw. `pull_debt` is a debt
transfer, `debt_socialized` retains its venue term, and liquidation remains a
collateral event rather than a universal default claim.
