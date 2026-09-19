# Euler V2 owner activity v1

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

This release preserves a fixed Euler V3 API response for EVC owner
`0xa47b8a0f97f4f666a99d672b2aa2481e8d018000` at Unix second
1,786,933,919. The response contains one `borrow` and one
`interest_accrued` row. Tabularium maps both without turning interest into a
fresh draw, as canonical event v3 rows.

It supersedes [`euler-v2-v0`](../euler-v2-v0/README.md), release
`euler-v2-owner-activity-1786933919-v0`, which carries the same two mapped
events under schema v2. Both releases were built from the same `source.json`,
byte for byte, and `capture.json` differs in one field, `release`. The only
difference in a canonical row is `schema_version`. The v0 release stays on
disk and stays verifiable.

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
| `capture.json` | `46b623f4c2c832f1529bb9b4fa4b992229890240db04efaaa2c8f0c40a045b9a` |
| `events.jsonl` | `f2b227058f53cd644c11359e911c8494924d6fef7da7072e8a33a4baf952d02a` |
| `coverage.json` | `cd23d3b89d949ccd9afad7ef7284b2172303af2bf8c1fb8151cd9c82c9fc22c7` |

Verify or rebuild from the repository root:

```bash
python3 plugins/tabularium/scripts/tabularium.py verify \
  plugins/tabularium/examples/euler-v2-v1/coverage.json
python3 plugins/tabularium/examples/euler-v2-v1/rebuild.py
```

See [DATA-DICTIONARY.md](DATA-DICTIONARY.md) for field meanings and limits.
