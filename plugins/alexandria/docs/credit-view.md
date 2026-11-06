# Tabularium credit view

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
<!-- marketplace-context:end -->

Alexandria derives a narrow credit view from a verified raw release. The raw
release stays unchanged. Derivation writes a new release containing the same
digest-keyed objects, two deterministic JSONL files and a new manifest.

```bash
python3 plugins/alexandria/scripts/alexandria.py derive raw-release \
  --output derived-release
python3 plugins/alexandria/scripts/alexandria.py verify derived-release
```

Rows name the input `source_release_id`, raw component digest, capture,
primary JSON Pointer, any context pointers, source identity, mapping rule,
adapter version and evidence class. The derived manifest names that same raw
release and binds the JSONL digests, registered mapping revisions, source
coverage and row counts. The output release ID covers the whole manifest.
Keeping the input release ID in the rows avoids a digest cycle: a row cannot
contain the digest of a manifest that contains the row's own digest.

An event ID covers its row kind, mapping rule, chain and native record
identity. A position-observation ID also covers its snapshot boundary. The
capture name, release ID and component digest remain in provenance but do not
rename the economic record. This lets a corrected release retain stable row
IDs while changing the sourced content. If one release repeats the same
record under two capture names, derivation refuses the duplicate.

## Registered mappings

`aave-v4.credit.v1` reads the archive-log capture shipped by Tabularium. It
maps 500 native Borrow and Repay logs to events. Captured reserve and token
reads supply asset context; their selectors remain in row provenance. The
mapping emits no position observations and declares no unsupported records in
this fixture. Its finality is provider-reported, and the captured interval
does not establish a current balance, default or full repayment.

`clearpool.credit.v1` reads the subject-scoped archive-log fixture already
shipped by Probitas. It maps five `Borrowed` and six `Repaid` logs. The pool
factory record supplies the manager, pool and currency; the captured currency
record supplies symbol and decimals; and the captured block-time record
supplies the timestamp. Those joins appear as context selectors on every row.
Clearpool's fixture has no position-state reading, so the mapping emits no
observation.

The Clearpool fixture omits log indices. Its native identity therefore covers
the emitter, topics, data and transaction hash. Extra provider metadata does
not rename a log. Two logs that remain indistinguishable on those captured
fields are refused rather than assigned guessed identities.

The checked-in source declaration at
`../tests/fixtures/credit-view-sources.json` points to the existing repository
files instead of copying either source into the Alexandria plugin.

## Row boundary

Credit events carry a chain-qualified subject, original venue and deployment,
venue-qualified action, event family, facility, one or more exact amount legs,
available transaction coordinates and complete provenance. Multiple amount
legs allow later liquidation mappings to retain debt and collateral without
forcing them into one number.

The current Aave v4 and Clearpool mappings emit one `source-amount` leg.
Their repayment records do not split that amount into principal and interest,
so the derived row does not add such a split.

Position observations carry the same subject, venue, facility and provenance,
plus a venue-qualified property, exact value and unit, observation boundary,
method and evidence class. Optional maturity is a sourced term, not an
Alexandria verdict.

Verification re-runs every registered mapping from the raw bytes, resolves all
primary and context selectors, rejects duplicate native or derived identities,
reconciles mapped, context and unsupported source counts, rebuilds both JSONL
files and compares their exact bytes. It does not use the network or write to
the release. Derivation reads raw components without an aggregate byte cache.
It stops above 100,000 rows or 64 MiB for either JSONL output. Derived access
and redistribution classes inherit the most restrictive input; an unknown
redistribution right stays unknown unless an input is explicitly prohibited.
