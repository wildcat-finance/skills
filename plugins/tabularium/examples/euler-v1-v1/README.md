# Euler v1 borrower block v1

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

This release preserves the canonical Euler v1 proxy response for borrower
`0x1ec0dde402dae69021492e7a9c4cbfdf72ffd84a` in Ethereum block
14,531,589. The response contains one `Borrow` log. Tabularium maps it to one
canonical event v3 row and keeps the complete log beside that interpretation.

It supersedes [`euler-v1-v0`](../euler-v1-v0/README.md), release
`euler-v1-borrow-block-14531589-v0`, which carries the same mapped event under
schema v2. Both releases were built from the same `source.json`, byte for
byte, and `capture.json` differs in one field, `release`. The only difference
in the canonical row is `schema_version`. The v0 release stays on disk and
stays verifiable.

The scope is exactly one borrower, one block and the three requested Euler v1
credit-event topics. It is not the borrower's complete history. The public RPC
reported the block hash and log; this release does not independently prove the
chain boundary. It is unsigned, so offline verification proves internal
consistency, not publisher identity or authenticity.

| File | SHA-256 |
| --- | --- |
| `source.json` | `1241cbed85189e79f9b0f8418e6838b297b4b661ad3e9f2d8a86903e22a6e790` |
| `capture.json` | `63d63a29d7d29c0f7be2f62fb4408ea7c5732b79bc0fe76b48a61527d7359aba` |
| `events.jsonl` | `5b1016a9bc143f42e9bea46de71b3d1917bf6731d93b4c49f974df3660bc8595` |
| `coverage.json` | `825c7b7ad59ed5fedd4e4f403a2f2b3bac9c60fc06fd9b49612f2f7a771b2e18` |

Verify or rebuild from the repository root:

```bash
python3 plugins/tabularium/scripts/tabularium.py verify \
  plugins/tabularium/examples/euler-v1-v1/coverage.json
python3 plugins/tabularium/examples/euler-v1-v1/rebuild.py
```

See [DATA-DICTIONARY.md](DATA-DICTIONARY.md) for field meanings and limits.
