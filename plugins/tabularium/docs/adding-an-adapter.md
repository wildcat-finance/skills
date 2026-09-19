# Adding a venue adapter

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

An adapter translates one venue's preserved records without promoting its
terms into universal credit claims. Start with a small source fixture and keep
the native record attached to every mapped row.

1. **Validate the source.** Define the required collections, field types,
   address and transaction shapes, numeric bounds and duplicate-identifier
   rules. Reject malformed input before writing output.
2. **Define each mapping.** Give every source entity a venue-qualified action,
   canonical family and versioned mapping rule. Explain what the venue means by
   terms such as repayment, cure, default or write-down.
3. **Record provenance.** Set the source kind and contract, entity collection,
   source identifier and selector, adapter name and version, and mapping-rule
   version. Record protocol generation separately from a hosted API's version.
   One covered source entity must yield one traceable selector.
4. **Declare coverage.** Count the collections mapped as events and every
   unsupported collection present in the source. Add evidence limits and known
   semantic gaps rather than dropping them silently.
5. **Add fixtures and tests.** Include a focused valid fixture plus malformed,
   duplicate, numeric-bound, ordering and coverage-drift cases. Test a
   deterministic repeat build and an offline rebuild from preserved bytes.
6. **Publish a new release.** Add source, capture, canonical and coverage files
   under a new release directory. Do not alter an earlier interpretation.

Three version axes stay separate, and a document that means one of them names
it. The canonical event and coverage `schema_version` is the envelope a release
was written to. The protocol generation is the venue's own deployment, such as
`aave-v4` or `euler-v2`. The source API version is the service that answered
the capture, such as `euler-v3`. Every release writes all three.

`build` writes `schema_version` 3 and `verify` reads 2 and 3. The v0 Aave v4
and Euler releases were published under 2 and stay under 2; their v1
successors carry 3. Schema 3 keeps the v2 envelope -- block numbers and
nullable hashes, multiple exact amount legs, owner and sub-account context, and
distinct debt-transfer and interest-accrual families -- and closes the admitted
vocabulary against the adapter tuple table, so venue, action, event family,
mapping rule, instrument type and amount kind must be the constants of one
registered adapter module. Add a new schema version rather than widening an old
release's meaning in place.

Review the venue's economic meaning as well as its JSON shape. If a common
family would imply more than the native event establishes, narrow the action
or leave that entity unsupported until the distinction can be represented.
