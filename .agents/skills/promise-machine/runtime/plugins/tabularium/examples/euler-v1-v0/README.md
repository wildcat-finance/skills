# Euler v1 borrower block v0

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

This release preserves the canonical Euler v1 proxy response for borrower
`0x1ec0dde402dae69021492e7a9c4cbfdf72ffd84a` in Ethereum block
14,531,589. The response contains one `Borrow` log. Tabularium maps it to one
canonical event v2 row and keeps the complete log beside that interpretation.

The scope is exactly one borrower, one block and the three requested Euler v1
credit-event topics. It is not the borrower's complete history. The public RPC
reported the block hash and log; this release does not independently prove the
chain boundary. It is unsigned, so offline verification proves internal
consistency, not publisher identity or authenticity.

| File | SHA-256 |
| --- | --- |
| `source.json` | `1241cbed85189e79f9b0f8418e6838b297b4b661ad3e9f2d8a86903e22a6e790` |
| `capture.json` | `59cd57ad5d8c54e1fd97cd4e62d37e31ac0d157ee5fa8f396c00be042c25041a` |
| `events.jsonl` | `4034622f8b34147dead8a87d7c16b2a7c7197ed6417809fec41716a8028552aa` |
| `coverage.json` | `ba4c5c127449b9be257069d302b442484fbd5d83023798eb9247aa893a45d301` |

Verify or rebuild from the repository root:

```bash
python3 plugins/tabularium/scripts/tabularium.py verify \
  plugins/tabularium/examples/euler-v1-v0/coverage.json
python3 plugins/tabularium/examples/euler-v1-v0/rebuild.py
```

See [DATA-DICTIONARY.md](DATA-DICTIONARY.md) for field meanings and limits.
