# ADR-069: Reinstate the distributed checkpoint layer above the local store

## Status

Accepted, 2026-09-02, at the maintainer's direction. This record reopens the
distributed checkpoint programme that
[ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
retired on 2026-08-27. ADR-028 stays Accepted and keeps every clause it holds
today. ADR-029 through ADR-032 stay Retired and gain standing successors rather
than edits.

## Context

The maintainer reinstated milestone 64 on 2026-09-02 and the repository does not
say so anywhere. Four decision records that describe the distributed layer are
marked Retired. The record that retired them is Accepted. The programme study and
the programme runbook each open with a banner disclaiming themselves. The
`wave-atlas-review` block on the nine estate issues reads defer or blocked.

An engineer handed one of those issues today reads a retired protocol decision, a
study that says it no longer governs, and a review that says do not start.
Nothing on disk records that the position changed, so the build either stops or
proceeds against records contradicting it.

ADR-028 does not have to be overturned to fix that. Its mandatory local hand-off
amendment calls the local checkpoint store an interim transport rule and says
that adopting a remote or distributed transport later requires another accepted
change. This record is that change. It is the thing ADR-028 asked for rather
than a reversal of it.

What the reopened layer still owes depends on what shipped meanwhile. `hexctl
checkpoint export` and `hexctl checkpoint restore` are live in `fiat-v5.49.1`
and already supply controller-state capture, ref binding, ledger prefix
verification and relocation under the `fiat-controller-checkpoint/v1` capsule
contract. The distributed layer sits above that capsule and adds a semantic
checkpoint identity distinct from archive bytes, the outer archive assembly
ADR-028 leaves to a manual procedure, an intake and publication state machine,
an independent signer and locked storage, a publication fence on external runs,
and a lineage graph with explicit resolution.

Four records describe that layer. All four are Retired, their bodies preserved
as historical rationale, and none of them has a successor to follow.

## Decision

Reopen the distributed checkpoint layer above the local checkpoint store, by
addition. Three clauses.

**The local store keeps everything it holds.** ADR-028 stays Accepted. Its
Status line, its amendments and the mandatory local hand-off it records are
unchanged. `<origin>/.hexaemeron/checkpoints/` remains the current transport and
the only one, and no checkpoint operation uploads, posts, commits or pushes
until a later delivery accepts a transport that does. This record authorises the
layer and changes no shipped behaviour.

**Each retired decision gains one standing successor.** ADR-029 through ADR-032
keep their Retired status and their preserved bodies. Four new records carry
their decisions forward, rebased on what `fiat-v5.49.1` already ships, and each
names the record it carries and states which clauses it takes verbatim, which it
rebases and which it drops. A reader who arrives at a retired record finds one
successor to follow rather than a dead end, and each reopened decision stays
independently supersedable.

**ADR-028 gains one dated amendment naming the layer above it.** The amendment
is appended after that record's `## Consequences` section and changes no
operative clause.

The successors are ADR-070 from ADR-029, ADR-071 from ADR-030, ADR-072 from
ADR-031 and ADR-073 from ADR-032. They land in the two steps after this one.

Reopening the layer authorises records, not deployment. Creating
`wildcat-finance/fiat-checkpoints`, standing up any service, and touching any
cloud account, key, region or spend each stay separately authorised deliveries.

## Alternatives

**Reopen in place.** Flip the Status line of ADR-029 through ADR-032 from
Retired back to Accepted and rewrite the ADR-028 Status paragraph that says it
retires them. Rejected. It writes no new file and rewrites five durable records.
It erases the retirement rather than recording that it was undone, so a reader
six months out would find no evidence the decisions were ever retired.

**One composite record.** Reinstate the whole programme here and reference the
four retired bodies without carrying any forward. Rejected. It collapses four
independent decisions into one. The protocol and authority split, the storage
substrate, the publication fence and the lineage model could then only be
superseded together, and each retired record would still end with no successor
to follow.

**Overturn ADR-028.** Mark that record Superseded and write this one as its
replacement, covering the local store and the distributed layer together.
Rejected. `hexctl checkpoint export`, `hexctl checkpoint restore`, the mandatory
local store and the capsule contract are all live in `fiat-v5.49.1` and all rest
on ADR-028 alone. Overturning it leaves four shipped behaviours governed by a
record that no longer stands.

## Consequences

This is the most expensive of the four routes to review. It writes five records
where the cheapest alternative writes none, holds five ADR numbers free against a
default branch other deliveries land on, and carries 24,550 bytes of retired body
forward into four successors. The design evidence records both figures. The cost
is accepted because each cheaper route fails a gate: a retired decision left
without a successor, a durable record rewritten, or a shipped behaviour left
governed by a record that was overturned.

Nothing executable changes. The controller keeps the bytes it has and every
later packet of the programme remains a delivery somebody has to authorise
separately.

The reopened layer is authorised, not specified. The four successors state what
each decision still owes on top of the shipped capsule. None of them deploys
anything, and the infrastructure their sources name is carried forward as the
shape to test rather than as a standing authorisation.

A reader asking whether the distributed programme is on or off now has one place
to look. That question was previously answerable only by reading five records
that contradict each other, and the contradiction is what this delivery exists
to remove.
