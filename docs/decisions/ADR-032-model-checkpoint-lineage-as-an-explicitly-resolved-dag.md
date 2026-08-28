# ADR-032: Model checkpoint lineage as an explicitly resolved DAG

## Status

Retired, 2026-08-27. The proposal below was never accepted and no longer
governs. [ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
replaces DAG resolution with literal continuation of one controller ledger.
The remaining body is preserved as historical rationale.

PR #569 published this record as ADR-027. It moved to ADR-032 so the five
Wave Delta records stay contiguous and in reading order once the collisions on
ADR-023 and ADR-024 were resolved. The decision is unchanged.

## Context

Two contributors can restore the same accepted parent and each finish useful
work before either sees the other's publication. A mutable `latest` pointer,
first-writer lock, upload timestamp, or deepest-chain rule would hide that
concurrency and let network timing decide which contribution counts.

Claims can reduce duplicate effort but cannot prevent network partitions,
offline work, expired leases, or a valid late upload. A service process that
can validate bytes must not acquire the separate authority to decide which
valid branch the organisation wants.

Revocation has the same distinction. An accepted archive can later be found
poisoned. Object Lock keeps the evidence, so the graph needs a way to make the
node and affected descendants non-resumable and to salvage work from the last
clean ancestor.

## Decision

Accepted checkpoints form a directed acyclic graph scoped to one repository,
issue, run id, immutable starting commit, and protocol/policy domain.

- The run-anchor/root record has no checkpoint parent and stage zero.
- An ordinary continuation names exactly one accepted, unrevoked parent.
- A reconciliation checkpoint names at least two accepted parents and the
  signed resolution that authorised their combination.
- Every non-root stage is one plus the maximum verified parent stage.
- Parent edges are immutable. Missing, duplicate, cyclic, cross-scope,
  wrong-base, revoked, or poisoned parents refuse acceptance.
- Server time, contributor time, upload order, stage ties, actor identity, and
  branch names carry no preference authority.

All accepted siblings remain visible before and after resolution. A frontier
is an accepted, unrevoked node with no accepted unrevoked child in the same
scope. The service may offer an advisory claim on one exact parent and next
runbook transition under a bounded lease. A stale, absent, or lost claim can
flag duplicate effort but cannot invalidate an otherwise valid checkpoint.

Preference and policy action use a separate typed resolution record. It names
the complete frontier considered, repository/issue/run/base/policy, exact
selected/combined/superseded/clean-ancestor nodes, action (`continue`,
`reconcile`, `supersede`, `salvage`, or `hold`), reason/evidence, resolver
identity/role/signature, and any expiry/review condition. The service validates
the resolver signature and stores the record immutably; its KMS key signs the
service's acceptance of that record. A worker cannot invent a resolution from
database order.

A reconciliation is new checked work, not a pointer update. Its own Fiat
transition restores the named parents, resolves conflicts, runs the union of
required gates, and publishes a checkpoint that proves both contribution lines
through literal Git ancestry or the original-to-rewritten provenance required
by ADR-021.

Revocation is an append-only signed record naming exact primary/replica object
versions and reason. The object remains. The revoked node and its descendants
are non-resumable. Salvage requires a signed resolution naming the last clean
ancestor and a new checked checkpoint; it cannot simply clear a database flag.

The graph, claims needed for current coordination, accepted resolutions,
revocations, and derived frontiers can be rebuilt from immutable manifests and
signed records. PostgreSQL stores the index, not the only edges or decisions.

## Alternatives

- **One mutable latest pointer.** Easy discovery and restore. Rejected because
  a concurrent valid child disappears from ordinary view and the pointer writer
  silently becomes resolver.
- **First-writer lease as a hard lock.** Reduces duplicate work. Rejected
  because a network partition or expired lease can discard valid progress, and
  the external-contributor promise says even one checkpoint should remain
  useful.
- **Newest timestamp or upload wins.** Always produces one answer. Rejected
  because clocks and network arrival do not establish checked progress and can
  be manipulated.
- **Deepest/longest chain wins.** Familiar from consensus systems. Rejected
  because stage counts parent depth, not quality or organisational intent, and
  this programme has no economic consensus mechanism.
- **Automatic file-level or CRDT merge.** Could preserve both branches without
  a human decision. Rejected because Fiat checkpoints include controller,
  receipt, audit, policy, and Git-provenance state whose conflicts cannot be
  settled safely by generic text merge.

## Consequences

Discovery is more complex than returning `latest`. A caller can receive several
frontiers and may need to wait for or request a resolution. Atlas must display
that honestly and redraw a bound choice when the graph changes.

Useful concurrent work is not discarded. Claims remain coordination aids rather
than authority, so a contributor whose lease expires can still publish a valid
sibling and let the resolver decide what happens next.

Resolver identity and key custody become their own security boundary. Conflicting
or forged resolutions hold the affected scope rather than letting service code
pick one. Key rotation and superseding decisions need durable records.

Revocation preserves poisoned evidence and can block a large descendant set.
Salvage costs a new checked transition from a clean ancestor, which is slower
than clearing a flag and makes the recovery claim inspectable.

This is a coordination and evidence graph, not a distributed consensus
protocol. It does not make every accepted branch correct, automatically
integrate it into current `main`, or remove the maintainer decision about which
work the project should carry forward.
