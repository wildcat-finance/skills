# ADR-072: Fence external Fiat transitions on signed checkpoint acceptance

## Status

Accepted, 2026-09-02. This record is the standing successor to
[ADR-031](ADR-031-fence-external-fiat-transitions-on-signed-checkpoint-acceptance.md),
which [ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
retired on 2026-08-27 and which keeps its Retired status and its body.
[ADR-069](ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md)
reopened the distributed layer and asked for one standing successor per retired
record; this is the third of four. It carries ADR-031's decision forward,
rebased on what `fiat-v5.49.1` already ships.

## Context

ADR-031 made one promise: a completed transition by an outside contributor
stays useful to whoever picks the work up next. It proposed to keep that promise
by refusing to advance an external run until a service had validated, locked,
replicated and signed the checkpoint.

Half of that fence now exists, and it is the local half. ADR-028's mandatory
local hand-off amendment makes a checkpoint compulsory at every accepted
boundary, and the controller enforces it: a save failure blocks the next
directive, the destination is derived from controller state rather than chosen,
and the agent may not ask whether to skip it. The boundaries themselves are
specified and checked rather than described. `hexctl checkpoint export` accepts
exactly two controller states, the ledger tail at `done:push` with no later
mutating action, and the exhausted audit loop where `next` returns
`audit-verdict`. Every other phase refuses before an output directory appears,
and so does a pending amendment or an interrupted transaction. Restore is
equally checked: the capsule is treated as hostile, the manifest digest arrives
out of band, and the relocation appends one `checkpoint:restore` entry to the
same ledger.

What is missing is the external half. Nothing uploads, nothing validates
independently, nothing signs, and a run's transitions are not frozen pending
anyone else's decision. The checkpoint sits on the contributor's disk, which is
where ADR-031 said it must not be allowed to stay.

## What this carries from ADR-031

**Carried verbatim.** The promise and its shape. A run records an explicit
execution class at creation. Version 1 makes checkpoint publication compulsory
for `external` runs, and the class is persisted, printed by status, checked on
restore, and never inferred from a username, an email address, a commit author,
a machine or a branch name. Changing the class after creation is an ask-first,
append-only amendment and receipt, and an external run cannot downgrade itself
to mark an unpublished transition complete. Publication uses a persisted
idempotency key, so a client that dies after service acceptance retrieves the
stored statement, verifies the same exact bytes and appends once. An
unavailable or ambiguous service leaves the run in its waiting state: local work
stays recoverable and retryable, and there is no offline bypass. A rejection
preserves a bounded refusal and the archive identity, leaves the transition
unadvanced, and requires a new checked state once the cause is fixed. A
revocation after acceptance blocks resume and descendants until the salvage
rules in ADR-073 are satisfied. The acceptance statement stays outside the
archive it signs, because a statement inside would sign a digest that included
itself. The controller does not sign its own acceptance, because producer and
validator would then be one authority.

**Rebased on `fiat-v5.49.1`.** Three changes. First, ADR-031's step 1 and step 2
have shipped. The gates it listed run today, the accepted boundary is one of two
exact controller states rather than a phrase, and the deterministic export over
the receipt prefix is `hexctl checkpoint export` with a canonical manifest and a
closed inventory. A fence built now starts from a checked boundary rather than
defining one. Second, what the controller would verify in a signed statement
grows by one field. ADR-071 binds three identities to an acceptance, the outer
archive digest, the capsule manifest digest and the semantic checkpoint
identity, so a statement names all three and the controller checks the one that
matches the bytes it holds. Third, the fence is now explicitly the external half
of a local rule that already exists. The controller already refuses to advance
past a boundary whose checkpoint was not saved; this record extends that refusal
to a boundary whose checkpoint nobody else has accepted.

**Dropped.** ADR-031's `checkpoint_ready` and `checkpoint_accepted` state names
are carried as the shape of the boundary rather than as reserved literals. The
controller's ledger has grown its own vocabulary since, `done:push`,
`audit-round`, `checkpoint:restore` and the rest, and a delivery that adds these
two states names them against that vocabulary rather than against a record
written before it existed. Also dropped: the assumption that an external run's
only unpublished state is a service outage. A run can now sit at an accepted
boundary with a verified local checkpoint and no service in existence at all,
which is the ordinary case today and not a failure.

## Decision

Keep ADR-031's fence, and state it as the external half of a local rule that
already ships. Once a checkpoint service is authorised and running, an external
run's selected transition is complete when the existing gates pass, the local
checkpoint is saved and verified, and an independent validator has locked,
replicated and signed an acceptance naming the three identities ADR-071 binds.
Until then the transition is not complete and the run does not advance. Before
that, with no service to accept anything, an external run completes its
transition on the existing gates and the mandatory local checkpoint, exactly as
every run does today; this record does not strand work behind a service that
does not exist.

The execution class is recorded at run creation, never inferred, and changed
only by an ask-first append-only amendment.

This record authorises no service, no upload path and no deployment. Until one
is authorised, the mandatory local checkpoint is the whole of the fence, and
every run behaves as ADR-028 already requires.

## Alternatives

- **Treat the local checkpoint as sufficient.** It ships, it is verified, and it
  blocks the next directive when it fails. Rejected as a general answer because
  a local archive helps nobody but the machine holding it, which is the gap the
  reopened layer exists to close.
- **Publish in the background after advancing.** Lower latency for the
  contributor. Rejected for ADR-031's reason, unchanged: a crash or a forgotten
  retry breaks the handover promise the class is meant to make.
- **Make publication optional with a warning.** Keeps a service from blocking
  work. Rejected because an optional transport gives no dependable portable
  frontier and leaves any discovery surface advisory.
- **Let the controller sign its own acceptance.** Works offline and needs no
  service signer. Rejected because the producer would then be the validator, and
  no locked or replicated object versions would be established.
- **Fence every run, not only external ones.** One behaviour, simpler to
  explain. Not chosen for version 1, again: the contribution promise is the
  established need, and no service has yet earned the right to block a local
  maintainer.

## Consequences

An external transition will wait on someone else. That is the point, and it is
also the cost: the wait is bounded by a service that does not exist yet, so this
record's clauses have no effect until one is authorised.

Stating the fence as the external half of an existing local rule makes the gap
small and concrete. What a delivery has to add is an execution class, two
boundary states, a client with an idempotency key, and statement verification
over three identities. Everything under those is already checked.

Nothing executable changes. The mandatory local checkpoint remains the only
thing standing between a boundary and the next directive.
