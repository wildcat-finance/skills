# Compound v3 Phase 0 method proof

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

This release pins Compound's 28 production Comet deployments at commit
`f766f51583c23acc33b2a7824654ef2029a96804` and preserves the raw JSON-RPC
requests and responses for two Ethereum USDC transactions. The 2022
transaction tests old-state and old-trace access. The 2026 transaction tests
the pinned deployment, nested calls, transaction-start storage and ordered
`SSTORE` output below a provider-reported finalized boundary.

The capture came from one public Hinterlight endpoint reporting
`reth/v1.11.3-d6324d6`. It is recorded RPC evidence, not chain proof or an
independent finality check. The release covers a fixed method-proof corpus; it
does not cover a market interval or all Compound activity. The endpoint URL,
headers and credentials are not preserved.

`source/` holds the authored corpus and generated registry. `input/` holds the
exact capture plan, pinned upstream files and RPC envelopes. `release/` is the
content-addressed Alexandria release with ID
`sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab`.

From the repository root:

```bash
python3 plugins/alexandria/examples/compound-v3-phase0-v0/rebuild.py
python3 plugins/alexandria/scripts/compound_v3_phase0.py check \
  plugins/alexandria/examples/compound-v3-phase0-v0/release
```

`rebuild.py` ingests the checked-in input twice, compares both release trees
with the committed bytes and runs the semantic check with socket connections
disabled.
