# Release and supersession policy

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

A Tabularium release is immutable once published. Keep its `source.json`,
`capture.json`, `events.jsonl` and `coverage.json` bytes at their original
paths and digests. Documentation may point readers to a newer interpretation,
but it must not replace the historical files.

When an adapter, schema or mapping rule changes:

1. give the changed interpretation a new version;
2. build it in a new release directory with a new release identifier;
3. preserve the earlier source, canonical and coverage bytes;
4. state which release is superseded and why;
5. describe changed rows, coverage and semantic assumptions; and
6. let downstream users choose a version rather than silently mixing them.

A correction can reuse source bytes only when their digest is unchanged. A new
capture boundary or corrected raw record is new source evidence and must be
published separately. Offline verification establishes internal consistency,
not publisher identity, authenticity or an independent chain proof.

A schema change is one of those changes, and it is met the same way. A
published release keeps the `schema_version` it was built under, and its
documents keep saying so. The newer envelope arrives as a superseding release
directory built from the same `source.json` bytes, with a new release
identifier, its own `capture.json` differing only in `release`, and its own
canonical and coverage bytes. The superseded release stays on disk, stays
verifiable, and gains a note naming its successor. `verify` therefore reads
every schema version the tree still ships, not only the one `build` writes: at
present `build` writes 3 and `verify` reads 2 and 3. Dropping a version from
the read path would strand the releases published under it, so a version leaves
the read path only when no release names it.

`aave-v4-v1`, `euler-v1-v1` and `euler-v2-v1` are that pattern applied to the
three v0 releases. Their `source.json` digests equal the v0 digests, and the
only difference in a canonical row is `schema_version`.

Protocol generations and data-service versions are separate release fields.
For example, the current Euler V2 protocol activity source is the Euler V3 API.
Changing either field requires a new release; an API name alone does not prove
that a new protocol generation exists.
