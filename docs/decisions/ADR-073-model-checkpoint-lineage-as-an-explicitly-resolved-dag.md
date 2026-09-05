# ADR-073: Model checkpoint lineage as an explicitly resolved DAG

## Status

Accepted, 2026-09-02. This record is the standing successor to
[ADR-032](ADR-032-model-checkpoint-lineage-as-an-explicitly-resolved-dag.md),
which [ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
retired on 2026-08-27 and which keeps its Retired status and its body.
[ADR-069](ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md)
reopened the distributed layer and asked for one standing successor per retired
record; this is the last of four, and it closes the successor set. It carries
ADR-032's decision forward, rebased on what `fiat-v5.49.1` already ships.

## Context

ADR-032 answered a question that only arises once checkpoints are shared: two
contributors restore the same accepted parent, each finishes real work, and
neither sees the other before publishing. Its answer was to record both and let
a named resolver decide, rather than let a pointer, a clock or an upload order
decide silently.

ADR-028 retired it in favour of literal continuation of one controller ledger,
and that is what ships. `hexctl checkpoint restore` appends one
`checkpoint:restore` entry to the exact imported ledger prefix, so a restored
run is the same run rather than a new one, and the manifest binds the base, the
run branch and every receipted step branch to exact commits before the relocated
state is published.

Literal continuation removes the fork question without answering it. Nothing
stops two people restoring the same capsule: each gets a controller that
believes it continues the original ledger, and the two histories diverge from a
shared prefix with no record that the split happened. Today that costs nothing,
because no service accepts either result and no one can discover the other. It
becomes the ADR-032 problem on the day one does.

The scope keys that graph would need are also no longer hypothetical. Upstream
`482172e7` binds a run to one immutable starting commit through an init-owned
`fiat-run-anchor/v1` receipt, and `hexctl checkpoint identity` derives a
semantic identity from that anchor and the accepted boundary, separately from
capsule and archive bytes. A node in the graph now has a name the controller
already computes.

## What this carries from ADR-032

**Carried verbatim.** The graph and its refusals. Accepted checkpoints form a
directed acyclic graph scoped to one repository, issue, run, immutable starting
commit and protocol domain. The root has no checkpoint parent and stage zero; an
ordinary continuation names exactly one accepted unrevoked parent; a
reconciliation names at least two and the signed resolution that authorised
combining them; every non-root stage is one plus the highest verified parent
stage. Parent edges are immutable, and a missing, duplicate, cyclic,
cross-scope, wrong-base, revoked or poisoned parent refuses acceptance. Server
time, contributor time, upload order, stage ties, actor identity and branch
names carry no preference authority. All accepted siblings stay visible before
and after a resolution, and a frontier is an accepted unrevoked node with no
accepted unrevoked child in the same scope. A claim is a bounded advisory lease
that can flag duplicate effort and cannot invalidate a valid checkpoint.
Preference is a separate typed resolution record naming the frontier
considered, the scope, the exact selected, combined, superseded and clean
ancestor nodes, the action, the reason and evidence, the resolver identity and
signature, and any expiry. A reconciliation is new checked work rather than a
pointer update: its own transition restores the named parents, resolves the
conflicts, runs the union of required gates and proves both lines through Git
ancestry. Revocation is an append-only signed record naming exact object
versions and a reason; the bytes stay, the node and its descendants become
non-resumable, and salvage needs a signed resolution naming the last clean
ancestor plus a new checked checkpoint rather than a cleared flag. Every part of
the graph is rebuildable from immutable manifests and signed records.

**Rebased on `fiat-v5.49.1`.** Three changes. First, the scope tuple and the
node name exist. The immutable starting commit is bound by
`fiat-run-anchor/v1`, and `hexctl checkpoint identity` computes the semantic
identity that names a node, so a graph delivery consumes both rather than
defining them. Second, the fork this graph exists to handle now has a concrete
local cause worth naming: two restores of one capsule each continue the same
imported ledger prefix, so divergence begins at a shared prefix that both sides
can prove and neither side records. A graph built on these records treats that
pair as siblings of their shared parent, which is exactly the case ADR-032
described from the other end. Third, revocation and salvage inherit ADR-071's
three identities, so a revocation names which of the outer archive digest, the
capsule manifest digest and the semantic identity it revokes.

**Dropped.** The database sentence. ADR-032 named PostgreSQL as the index that
stores neither the edges nor the decisions; the principle survives here without
the product, for the same reason ADR-071 dropped its substrate: no deployment
exists, and naming one would state a decision nobody has taken. The rule that
matters is that the index is derived and rebuildable, and that no worker may
infer a resolution from stored order.

## Decision

Keep ADR-032's graph, its refusals and its separation between validating bytes
and choosing which valid branch the project carries. A checkpoint node is named
by the semantic identity the controller already computes, and scoped by the run
anchor's immutable starting commit.

Until a service accepts checkpoints, the graph has one shape everywhere: a
single chain per run, continued literally by restore. A delivery that adds
acceptance adds the sibling case, the resolution record and revocation with it,
in that order, because a sibling with no resolver is a question nobody can
answer.

This record authorises no service, no index and no deployment.

## Alternatives

- **Leave literal continuation as the whole answer.** It ships and it is
  checked. Rejected as a general answer because it is silent about two restores
  of one capsule, which is the fork case rather than an edge case once
  checkpoints are shared.
- **One mutable latest pointer.** Easy discovery and restore. Rejected for
  ADR-032's reason: a valid concurrent child disappears from ordinary view and
  whoever writes the pointer quietly becomes the resolver.
- **First-writer lease as a hard lock.** Reduces duplicate work. Rejected
  because a partition or an expired lease discards valid progress, against the
  promise that one checkpoint stays useful.
- **Newest upload or timestamp wins.** Always produces an answer. Rejected
  because arrival order is not checked progress and can be manipulated.
- **Deepest chain wins.** Familiar from consensus systems. Rejected because
  stage counts depth rather than quality, and this programme has no consensus
  mechanism and needs none.
- **Automatic merge of divergent checkpoints.** Would preserve both lines
  without a human. Rejected because a checkpoint carries controller, receipt,
  audit and Git provenance state whose conflicts a generic merge cannot settle
  safely.

## Consequences

Discovery will be more complex than returning one answer, and a caller may hold
several frontiers and have to wait for a resolution. That cost buys the property
the programme is for: concurrent work is not discarded by timing.

Resolver identity becomes a security boundary of its own, and conflicting or
forged resolutions hold a scope rather than letting service code choose. Key
custody and superseding decisions need durable records.

Nothing executable changes, and nothing here binds a run today: a single chain
per run is what literal continuation produces, and this record describes what
happens when that stops being true.

With this record the four retired decisions each have exactly one standing
successor. A reader who arrives at ADR-029, ADR-030, ADR-031 or ADR-032 finds
one place to go next, and the retirement stays in the history where it happened.
