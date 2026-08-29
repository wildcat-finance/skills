# Compound v3 Phase 0 execution witness

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

This non-canonical witness consumes Alexandria's verified
`compound-v3-phase0-v0` raw release and rebuilds two successful nested Comet
calls, eight relevant ordered storage writes and one signed-principal
transition. It reads the checked-in Alexandria objects by their manifest-bound
digests and makes no RPC request.

The witness transaction is one Ethereum USDC interaction. It proves that the
recorded method can connect call frames, proxy storage writes and a packed
`int104` principal transition for that transaction. It is not a Compound event
release, a market-history claim or a general call-trace normalizer. Canonical
Compound events remain Phase 1 work.

From the repository root:

```bash
python3 plugins/tabularium/examples/compound-v3-phase0-v0/rebuild.py
```

See [DATA-DICTIONARY.md](DATA-DICTIONARY.md) for field meanings and refusal
boundaries.
