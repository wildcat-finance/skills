# ADR-048: Derive Midnight timeliness from debt units

## Status

Accepted, 2026-08-28.

## Context

A Morpho Midnight dossier needs to say whether a fixed-maturity obligation
was cleared when due. A current position cannot answer that question: debt
may be outstanding at maturity and later reach zero through repayment, a
secondary close or liquidation.

The pinned Midnight contract permits debt increases while
`block.timestamp <= maturity` and changes to post-maturity liquidation only
when `block.timestamp > maturity`. The public v0 API exposes immutable
maturity and second-resolution user transactions, but no intra-second event
index. It supports Base chain id 8453 and cursor pagination without publishing
an indexing start block or a chain-completeness guarantee.

Probitas evidence schema 1 gives each record one source. A maturity outcome is
derived from several transaction-cited ledger entries, so it needs a
reproducible evidence rule without inventing a source or silently widening
the schema.

The accepted design and its source boundary are recorded in the committed
[study](../../plugins/probitas/docs/morpho-midnight-fixed-maturity-study.md).

## Decision

For each address and market, Probitas groups exact integer debt-unit changes
by API timestamp and applies every group whose `created_at <= maturity`.
Zero units after the maturity-second group means `cleared_by_maturity`;
positive units mean `outstanding_at_maturity`; a future maturity means
`not_due`. Events within one second are added as a group because the reviewed
API surface supplies no narrower order.

The evidence keeps obligation state separate from settlement mode. Primary
repayment, secondary close and liquidation can each reduce debt, but none is
renamed as another. A later zero balance may establish `settled_late`; it
never rewrites an outstanding-at-maturity result.

Coverage is limited to the complete cursor walk returned by the Morpho
Midnight v0 API at the recorded observation boundary on Base. It states the
unpublished history lower bound and does not claim archive-chain completeness.

Schema 1 remains in place. Every input event keeps its transaction source,
and the outcome records the determining source and the values needed to
recompute it. If audit shows that this cannot establish the claimed outcome,
implementation stops and asks before any evidence-schema migration.

## Alternatives

- Read only the current position. This loses the maturity state whenever debt
  is settled later and can turn a late liquidation into an apparently timely
  result.
- Exclude events at the maturity timestamp. This conflicts with the pinned
  contract boundary and would misclassify an event the contract permits at
  the due second.
- Use one settlement label as the maturity verdict. This erases whether the
  obligation was still open when due and can call forced liquidation a
  voluntary repayment.
- Move to a multi-source schema 2. That would represent the derivation more
  directly, but it changes every adapter, renderer and verification gate for
  a result schema 1 can preserve through its cited event ledger.
- Reconstruct directly from Base logs or a preserved capture. That could
  support a stronger completeness claim, but it adds deployment, ABI, RPC and
  cross-skill preservation work outside this Probitas delivery.

## Consequences

The adapter must exhaust cursors, reject incomplete or ambiguous history,
group equal-second deltas, keep balances non-negative and reconcile the final
units with the returned current position. Its fixtures must retain a case
where debt is positive at maturity and zero at observation.

Dossiers can state both when the obligation was cleared and how settlement
occurred without strengthening API evidence into a chain-history claim. The
cost is an explicit API lower-bound gap and continued maintenance of pinned
response specimens while the v0 surface evolves.
