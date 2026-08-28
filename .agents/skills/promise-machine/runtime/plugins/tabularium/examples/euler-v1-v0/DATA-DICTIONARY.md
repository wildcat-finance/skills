# Euler v1 v0 data dictionary

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

`events.jsonl` contains canonical event v2 rows. Exact amounts remain decimal
strings in base units.

| Field | Meaning |
| --- | --- |
| `schema_version` | Canonical event revision; `2` here. |
| `id` | Deterministic identifier derived from chain, adapter, transaction, log and mapping rule. |
| `event_family` | Venue-qualified common family such as `borrowing`, `repayment` or `debt-resolution`. |
| `action` | Exact Euler v1 action. |
| `venue` | `euler-v1`. |
| `chain` | `ethereum-mainnet`. |
| `transaction` | Transaction and block hash, block/transaction/log indexes, and a null timestamp because the response did not include one. |
| `parties` | Borrower and, for liquidation, liquidator addresses. |
| `instrument` | Canonical Euler v1 proxy. |
| `amounts` | Exact debt or collateral legs; liquidation legs stay separate. |
| `provenance` | RPC source kind, contract, selector, mapping rule, adapter, protocol generation and source API. |
| `native_record` | Complete source log retained beside its interpretation. |

`source_selector` is the transaction hash plus log index in the preserved
`eth_getLogs` response. A `repayment` or liquidation debt leg would describe
the venue event only; it would not prove that every obligation was settled.
