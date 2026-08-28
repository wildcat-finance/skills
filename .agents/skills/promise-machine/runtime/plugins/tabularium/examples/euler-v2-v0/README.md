# Euler V2 owner activity v0

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

This release preserves a fixed Euler V3 API response for EVC owner
`0xa47b8a0f97f4f666a99d672b2aa2481e8d018000` at Unix second
1,786,933,919. The response contains one `borrow` and one
`interest_accrued` row. Tabularium maps both without turning interest into a
fresh draw.

`Euler V2` is the protocol generation. `Euler V3` is the hosted source API
version. The two fields remain separate in every canonical row and manifest.
The response reports complete index coverage for its source categories across
blocks 20,529,207 through 25,774,728, but this release covers only the stated
owner and second. The hosted indexer does not provide a per-event block hash
or transaction index, and this release does not independently prove its chain
boundary. It is unsigned, so offline verification proves internal consistency,
not publisher identity or authenticity.

| File | SHA-256 |
| --- | --- |
| `source.json` | `10f5c8e8242ef3745fbd69c4d8aed458f31b165fc4526f638e76df59a69a18cc` |
| `capture.json` | `bcf2c85907243ccb40bc79234e30457d2e7e8b7dc3addc32d7301f804c772b9e` |
| `events.jsonl` | `f563baa00c737384a3901f1bb3a7ae977f68f52a813eae9d02071eb2f4d0a5fe` |
| `coverage.json` | `9892768315484ff05771e998f301b30daebd079a445e4226c9e55b12323c2a4b` |

Verify or rebuild from the repository root:

```bash
python3 plugins/tabularium/scripts/tabularium.py verify \
  plugins/tabularium/examples/euler-v2-v0/coverage.json
python3 plugins/tabularium/examples/euler-v2-v0/rebuild.py
```

See [DATA-DICTIONARY.md](DATA-DICTIONARY.md) for field meanings and limits.
