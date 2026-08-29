# Goldfinch borrower record v0

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

This directory is a complete, offline-verifiable Tabularium release made from
the preserved Goldfinch borrower snapshot. It maps 34 `borrows` and 477
`repays` into 511 canonical rows. A Goldfinch repayment row records the venue's
reported repayment event; it does not by itself prove that the borrower's full
debt was settled.

## Release files

| File | Purpose | SHA-256 |
| --- | --- | --- |
| `source.json` | Unchanged hosted-indexer snapshot | `644b706804b6e28d69b1028b87937e0e36c882f703419d0e2bf568b056892bc9` |
| `capture.json` | Capture boundary, source digest and entity counts | `b8b8e46d7d688accd32826b3c228758f8fb84ed678e4c36edf228d67ce65da50` |
| `events.jsonl` | Canonical event v1 rows | `751754a2f913691cf95f3e9f859b156f9ccd7963b1d72d4fc3379348924469b1` |
| `coverage.json` | Release binding, coverage, versions and known gaps | `58184a75d8eca6ae8d9b44653c36ce8c482549c5d3cecd1a2a991b0936561f6d` |
| `DATA-DICTIONARY.md` | Field meanings and semantic limits | n/a |
| `rebuild.py` | Safe temporary rebuild and comparison | n/a |

The coverage manifest declares `_meta` (1), `callableLoans` (1), `creditLines`
(31) and `tranchedPools` (24) as unsupported source entities rather than
silently treating them as events.

## Verify or rebuild

From the repository root, verify the committed release without a network
connection:

```bash
python3 plugins/tabularium/scripts/tabularium.py verify \
  plugins/tabularium/examples/goldfinch-v0/coverage.json
```

Run the complete demonstration with:

```bash
python3 plugins/tabularium/examples/goldfinch-v0/rebuild.py
```

The demonstration copies the preserved inputs to a fresh temporary directory,
builds there, makes all four release files read-only, verifies them offline and
compares the rebuilt canonical and coverage bytes with this directory. It does
not write to the committed release.

## Evidence boundary

`capture.json` is preserved byte-for-byte. Its `status` field describes the
snapshot when it first entered staging, before this canonical release existed;
the field remains unchanged as part of that evidence.

The source boundary is the block reported by a hosted indexer. This release
does not independently prove that block or provide a verified block number and
hash for each event. It is also unsigned: offline verification proves internal
consistency, not publisher identity or authenticity.

See the [data dictionary](DATA-DICTIONARY.md), the
[adapter guide](../../docs/adding-an-adapter.md) and the
[release policy](../../docs/release-policy.md) for the interpretation contract.
