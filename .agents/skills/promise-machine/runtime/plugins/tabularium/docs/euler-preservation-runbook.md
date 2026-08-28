# Euler preservation delivery runbook

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

This was one atomic Fiat step because the schema, adapters, preserved bytes,
offline verifier and marketplace claim form one review boundary.

## Step 1: Ship source-bound Euler v1 and Euler V2 releases

**Goal.** Add deterministic Euler release paths without changing an earlier
Goldfinch release byte, and keep Euler V2 protocol generation separate from
the Euler V3 source API.

**Entry.** Clean `main` at `27e930f`, with issue #57 as the issue-first record,
92 passing Tabularium tests and the four Goldfinch digests fixed by tests.

**Exit.** `euler-v1-v0` and `euler-v2-v0` build in fresh directories, verify
without network access or writes, reject source and derived-artifact tampering,
and match their committed bytes on two rebuilds. The Goldfinch digest gate and
full repository test matrix remain green. Marketplace prose names the shipped
boundary and rotates the next Fiat job to Compound III Phase 0.

**Files.** Add Euler adapters, versioned release validation, schema v2,
self-contained examples, dictionaries, rebuild scripts and focused tests under
`plugins/tabularium/`. Update the canonical skill, portable entry, agent
contract, host manifests, root catalogue, guides and landing page. Preserve
vendored prose, historical audit findings outside their current-context line,
legal attribution and the digest-bound Lazarus fixture README.

**Tests.** Cover exact v1 Borrow, Repay and Liquidation mappings; every V2
credit-event family; source/native retention; owner/sub-account checks;
selector uniqueness; deterministic order; unknown-event refusal; fixed release
digests; two fresh rebuilds; no-network verification; and source, capture,
canonical, coverage, version and count tampering. Run the complete repository
Python matrix, Pandects Foundry checks and `git diff --check`.
