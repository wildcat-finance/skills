# `credit-history-v0`

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented.
<!-- marketplace-context:end -->

This demonstration runs the complete Alexandria prototype without reaching
the network. It reads the existing Goldfinch source at
`plugins/tabularium/examples/goldfinch-v0/source.json` and the existing
Clearpool source stored with this example at
`plugins/alexandria/examples/credit-history-v0/sources/clearpool.json`. The
plan pins both SHA-256 values and materializes them only in the temporary demo
output.

From the repository root:

```bash
output="$(mktemp -d)/credit-history-v0"
python3 plugins/alexandria/examples/credit-history-v0/demo.py build --output "$output"
python3 plugins/alexandria/examples/credit-history-v0/demo.py verify "$output"
```

The output contains materialized inputs, raw and derived releases, a disposable
SQLite index, stable query JSON, Probitas evidence and dossier files, and a
summary binding their digests. Build refuses an existing output directory.
Verify opens the index and releases read-only and uses a temporary directory
outside the output for Probitas's render-and-verify handoff.

The derived release contains 522 events and 31 position observations:
Goldfinch contributes 511 events and all 31 observations; Clearpool contributes
11 events. The example query address has 11 Clearpool events and no Goldfinch
rows. Clearpool coverage is covered. Goldfinch coverage remains partial because
25 native callable-loan and tranched-pool records are deliberately unsupported
by the narrow mapping.

Probitas emits 11 Clearpool transaction records and 15 venue coverage rows:
one checked, one error, two unconfigured and nine unimplemented. All five
dossier gates pass. The other 12 coverage rows remain visible as gaps; this is
not evidence that those venues were clean.

The fixed inputs demonstrate reproducibility, not a production corpus. The
Goldfinch bytes came from a hosted indexer and carry provider-reported finality.
The Clearpool bytes are a subject-scoped archive-log fixture whose finality is
unknown. Matching their digests does not prove publisher authenticity, source
completeness or canonical-chain finality.
