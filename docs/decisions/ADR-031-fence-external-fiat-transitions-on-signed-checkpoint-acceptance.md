# ADR-031: Fence external Fiat transitions on signed checkpoint acceptance

## Status

Retired, 2026-08-27. The proposal below was never accepted and no longer
governs. [ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
replaces its external acceptance fence with two explicit checkpoint
boundaries and same-ledger verification. The remaining body is preserved as
historical rationale.

PR #569 published this record as ADR-026. It moved to ADR-031 so the five
Wave Delta records stay contiguous and in reading order once the collisions on
ADR-023 and ADR-024 were resolved. The decision is unchanged.

## Context

The deal with outside contributors is that one completed checkpoint remains
useful to the next person. Optional or background publication cannot make that
promise: the local run can advance or finish while the only portable state is
still on the contributor's machine. A plain upload response is also too weak.
Network failure after server acceptance can look the same as failure before
upload, and a service database row can disagree with immutable object versions.

Putting the current acceptance statement inside the archive it signs would
make archive identity self-referential. Letting the controller sign its own
acceptance would show only that the producer believed its bytes, not that an
independent validator locked and replicated them.

## Decision

Fiat run creation records an explicit `execution_class`. Version 1 makes
checkpoint publication mandatory for `external` runs. The class is persisted,
printed by status, checked on restore, and never inferred from GitHub username,
email, commit author, machine, or branch name.

Changing execution class after run creation is an ask-first, append-only study
amendment and controller receipt. An external run cannot downgrade itself to
mark an already unpublished transition complete. Other execution classes keep
current behaviour until a later accepted decision widens the fence.

For an external run, the end of every selected green transition becomes a
two-phase boundary:

1. Existing implementation, audit, prose, signature, push, and remote-
   verification gates pass.
2. The controller appends `checkpoint_ready`, freezes further transitions, and
   exports/inspects deterministic bytes covering the receipt prefix through
   that record.
3. The client announces and uploads the exact candidate through an idempotent
   service path, then waits for validation, locked primary/replica publication,
   and a signed acceptance statement.
4. The controller verifies the statement's typed domain, pinned key/policy,
   repository, issue, run, step, role, parent set, `snapshot_id`,
   `archive_sha256`, primary and replica versions, and acceptance result.
5. The controller appends `checkpoint_accepted` plus the signed sidecar and
   permits exactly the next runbook transition.

The archive contains the controller/receipt state through `checkpoint_ready`.
It does not contain its own acceptance statement. Appending
`checkpoint_accepted` records an external decision about the already named
semantic state; the next cumulative archive carries that prior statement.

Publication uses a persisted idempotency key. If the client dies after server
acceptance but before local append, it retrieves the stored statement, verifies
the same exact bytes, and appends once. If the service is unavailable or its
decision is ambiguous, the controller remains `checkpoint_ready` or
`publishing`; local work stays recoverable and retryable, but the transition is
not complete. There is no offline bypass for an external run.

A rejection preserves a bounded refusal and archive identity, leaves the
transition unadvanced, and requires a new checked state after the cause is
fixed. Revocation after acceptance blocks resume and descendants until the
lineage/salvage rules in ADR-032 are satisfied.

## Alternatives

- **Publish in the background after advancing.** Lower contributor latency.
  Rejected because a crash or forgotten retry breaks the very handover promise
  that external classification is meant to make.
- **Make publication optional and show a warning.** Keeps the service from
  blocking work. Rejected because optional transport gives no dependable
  portable frontier and makes Atlas state advisory at best.
- **Let the controller sign acceptance locally.** Works offline and removes
  the service signer. Rejected because producer and validator become the same
  authority and no locked/replicated object versions are established.
- **Place acceptance inside the same archive.** One file is convenient to
  carry. Rejected because the statement signs an archive digest that would then
  include the statement itself.
- **Require the fence for every Fiat run immediately.** One behaviour is
  simpler. Not chosen for version 1 because the external contribution promise
  is the established need and service availability has not yet earned the
  right to block every local maintainer run.

## Consequences

An external transition can wait on upload, validation, replication, or KMS and
therefore takes longer than its existing push gate. That is deliberate: the
transition is not portable until those checks finish. Idempotent retry and a
preserved local ready archive keep outage from destroying work without calling
the work complete.

The controller gains a remote dependency and new persistent states. Status,
events, alerts, and recovery must make it clear which side owns the next retry
and how long the fence has waited.

The sidecar split leaves one accepted checkpoint as two objects to carry: the
archive and its signed statement. The next archive incorporates the earlier
statement chain, while the current pair remains independently verifiable.

The rule does not say a checkpoint's work is correct beyond its existing Fiat
receipts and the service's bounded validation. It establishes portable accepted
bytes for the named transition, not correctness of the whole task or safety of
eventual integration with a newer `main`.
