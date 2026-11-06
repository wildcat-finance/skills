# `credit-history-v0`

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
<!-- marketplace-context:end -->

This demonstration runs the complete Alexandria prototype without reaching
the network. It reads the existing Aave v4 source at
`plugins/tabularium/examples/aave-v4-v0/source.json` and the existing
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

The derived release contains 511 events and no position observations:
Aave v4 contributes 500 events and Clearpool contributes 11. The two declared
query addresses return 38 Aave v4 and 11 Clearpool events. Aave v4 coverage is
covered. Clearpool coverage is partial because its fixture covers only one of
the two addresses.

Probitas emits 49 transaction records and 15 venue coverage rows: one checked,
one error, five unconfigured and eight unimplemented. All five dossier gates
pass. The 14 gap rows remain visible; they do not establish clean histories.

The fixed inputs demonstrate reproducibility, not a production corpus. The
Aave v4 bytes contain archive logs and captured reserve and token reads, with
provider-reported finality.
The Clearpool bytes are a subject-scoped archive-log fixture whose finality is
unknown. Matching their digests does not prove publisher authenticity, source
completeness or canonical-chain finality.
