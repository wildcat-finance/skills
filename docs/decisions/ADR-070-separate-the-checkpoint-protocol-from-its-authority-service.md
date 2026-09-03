# ADR-070: Separate the checkpoint protocol from its authority service

## Status

Accepted, 2026-09-02. This record is the standing successor to
[ADR-029](ADR-029-separate-the-checkpoint-protocol-from-its-authority-service.md),
which [ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
retired on 2026-08-27 and which keeps its Retired status and its body.
[ADR-069](ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md)
reopened the distributed layer and asked for one successor per retired record;
this is the first of four. It carries ADR-029's decision forward, rebased on
what `fiat-v5.49.1` already ships.

## Context

ADR-029 was written when nothing of the checkpoint programme had shipped. Every
schema, verifier and command in it was future work, so the record could treat
the boundary between protocol and service as a question of where code would one
day live.

That is no longer the position. `hexctl checkpoint export` and `hexctl
checkpoint restore` are live in `fiat-v5.49.1` under the
`fiat-controller-checkpoint/v1` capsule contract at
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`. That
contract already fixes the capsule's canonical manifest, its closed file
inventory and digests, the exact local ref-to-commit map, the appendable ledger
prefix and tail, a hostile-input read boundary with named refusal classes, an
atomic no-replace publication, and a relocation transaction that appends one
`checkpoint:restore` entry to the same ledger. On the default branch, `hexctl
checkpoint identity` and ADR-028's run-anchor amendment add a semantic
checkpoint identity derived from the verified run anchor, held separate from
exact capsule and archive bytes. A protocol half exists, in this repository,
with no service anywhere.

So the question ADR-029 answered in the abstract now has a concrete half
already settled. What survives is the reason for the split, and the rest of the
protocol surface the shipped commands do not cover.

## What this carries from ADR-029

**Carried verbatim.** The three-way ownership split, and the reasoning behind
it. `wildcat-finance/skills` owns the portable protocol. A separately
authorised `wildcat-finance/fiat-checkpoints` repository owns the replaceable
service implementation: contributor authentication and run authorisation,
bounded quarantine upload grants, isolated validation against a pinned protocol
release, immutable object publication and replication with signed statements,
derived indexes and lineage operations, and the infrastructure, monitoring and
runbooks around them. `wildcat-finance/shoggoth-wave-atlas` owns only redacted
discovery and hand-off: it reads versioned summaries, reports each source's
freshness, binds a contributor's resume, redraw or start choice, requests a
short-lived download grant and passes bytes to the verifier. It does not
validate archives as authority, sign decisions, select a fork or retain a
durable object URL. Also carried: no archive, observation, credential,
environment state or deployment secret belongs in either source repository; the
service pins one exact protocol release or signed commit digest and never
widens a schema locally to accept a failing upload; a protocol or public-key
change lands here first with compatibility fixtures before any deployment
adopts it; and checkpoint acceptance is an evidence-statement boundary handed
to Ariadne's in-toto and DSSE contract rather than a new attestation grammar,
with the checkpoint protocol still fixing the predicate fields and their
authorisation meaning.

**Rebased on `fiat-v5.49.1`.** ADR-029 listed the protocol surface as six items
of future work. Three of them have shipped in part. The run-anchor schema is
`fiat-run-anchor/v1`, bound by initialization. The snapshot and manifest
schemas exist for the controller capsule as `fiat-controller-checkpoint/v1`,
whose manifest digest names exact capsule bytes while the semantic identity is
derived separately. Deterministic export and restore reference commands are
`hexctl checkpoint export` and `hexctl checkpoint restore`, and their refusal
behaviour is specified rather than promised. What this repository still owes the
protocol is therefore narrower: the acceptance, revocation, resolution and
redacted-discovery schemas; canonical identity rules extended past one run's
controller state, with golden vectors; pinned receipt and resolver public keys
with typed key-transition rules; controller publication-fence behaviour; and
compatibility and refusal fixtures for all of it. The offline-inspection
guarantee is likewise no longer a promise. A capsule and its manifest digest can
be checked today with no service in existence.

**Dropped.** ADR-029's status framing goes: it described itself as a Proposed
record whose service-repository visibility would be settled at creation time,
and it pointed at issues #563 and #564 as the entry gates. Those gates belong to
a milestone that has since been re-cut, and neither number is cited here as
authority. Creating `wildcat-finance/fiat-checkpoints`, choosing its visibility
and approving any cloud account, dependency or deployment remain separately
authorised deliveries, which is the part of that clause worth keeping. Also
dropped: the implication that offline restore had to be built before it could be
relied on.

## Decision

Keep the three-repository split exactly as ADR-029 drew it, with the protocol
half in this repository, the replaceable service in its own separately
authorised repository, and Atlas confined to redacted discovery and hand-off.

The protocol surface this repository owes is the list above, not the original
six items, because the run anchor, the capsule schema and the deterministic
export and restore commands already ship. A new protocol delivery states which
of the remaining items it closes and adds its compatibility fixtures here
before any service adopts it.

This record authorises no repository, no service, no account and no deployment.
It records where each responsibility belongs when one is authorised.

## Alternatives

- **Let the shipped capsule contract stand as the whole protocol.** Cheapest,
  and it is already written. Rejected because the capsule moves one run's
  controller state between machines; it fixes no acceptance, revocation,
  resolution or discovery schema, and says so in its own words.
- **Fold the service into this repository now that a protocol half exists.**
  One tree, one review queue. Rejected for ADR-029's reason, unchanged by
  anything that shipped: cloud operations and public skill releases have
  different cadences and different write boundaries.
- **Let the service repository own the remaining schemas.** Keeps service work
  self-contained. Rejected because an accepted checkpoint would then depend on a
  live service release for its meaning, and the service could reinterpret stored
  objects without a protocol change anybody could review.
- **Write one successor covering all four retired records.** Fewer files.
  Rejected by ADR-069, which requires one standing successor per retired record
  so each stays independently supersedable.

## Consequences

A reader arriving at ADR-029 now has somewhere to go, and the successor tells
them which parts of that record still hold and which the shipped controller has
overtaken. That is the whole point of writing it.

The narrower protocol list is a commitment. Anyone closing one of those items
has to add its fixtures here, and a service that wants a schema it does not have
must wait for that landing rather than widen its own copy.

Nothing executable changes. This record adds a file and governs a programme that
has not been authorised to deploy anything.
